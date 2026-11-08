// GET    /api/admin/custom-forms/:id   un formulaire (superadmin, éditeur)
// PUT    /api/admin/custom-forms/:id   modifie le formulaire (superadmin)
// DELETE /api/admin/custom-forms/:id   supprime le formulaire ET toutes ses réponses (superadmin)
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import { nowIso } from '../../../_lib/settings.js';
import { LIST_SQL, cleanForm, findForm, rowToForm } from '../../../_lib/custom-forms.js';


export async function onRequestGet({ request, env, params }) {
  const { response } = await requireRole(env, request, ['superadmin', 'editor']);
  if (response) return response;
  const f = await findForm(env, params.id);
  if (f.response) return f.response;
  return json({ ok: true, form: rowToForm(f.row) });
}

export async function onRequestPut({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const f = await findForm(env, params.id);
  if (f.response) return f.response;
  const body = await readJson(request, 128 * 1024);
  if (!body || typeof body !== 'object') return error(400, 'invalid', 'Données illisibles. Rechargez la page et réessayez.');
  const { values, error: msg } = cleanForm(body, { partial: true });
  if (msg) return error(400, 'invalid', msg);
  const cols = Object.keys(values);
  if (!cols.length) return error(400, 'invalid', 'Aucune modification à enregistrer.');
  const sets = cols.map((c) => `${c} = ?`).concat('updated_at = ?', 'updated_by = ?');
  const binds = cols.map((c) => (c === 'fields' ? JSON.stringify(values[c]) : values[c]));
  await env.DB.prepare(`UPDATE custom_forms SET ${sets.join(', ')} WHERE id = ?`).bind(...binds, nowIso(), admin.id, f.row.id).run();
  await audit(env.DB, admin.id, 'cforms.update', request, `form:${f.row.id}`, { title: values.title ?? f.row.title, fields: cols });
  const row = await env.DB.prepare(`${LIST_SQL} WHERE f.id = ?`).bind(f.row.id).first();
  return json({ ok: true, form: rowToForm(row) });
}

export async function onRequestDelete({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const f = await findForm(env, params.id);
  if (f.response) return f.response;
  await env.DB.batch([
    env.DB.prepare('DELETE FROM form_entries WHERE form_id = ?').bind(f.row.id),
    env.DB.prepare('DELETE FROM custom_forms WHERE id = ?').bind(f.row.id),
  ]);
  await audit(env.DB, admin.id, 'cforms.delete', request, `form:${f.row.id}`, { title: f.row.title, entries: f.row.total || 0 });
  return json({ ok: true });
}
