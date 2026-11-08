// GET  /api/admin/custom-forms   formulaires créés, avec le nombre de réponses (superadmin, éditeur)
// POST /api/admin/custom-forms   crée un formulaire { title, intro?, fields?, bouton?, merci?, open? } (superadmin)
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import { nowIso } from '../../../_lib/settings.js';
import { LIST_SQL, NO_TABLE, cleanForm, noTable, rowToForm } from '../../../_lib/custom-forms.js';


export async function onRequestGet({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'editor']);
  if (response) return response;
  try {
    const { results } = await env.DB.prepare(`${LIST_SQL} ORDER BY f.updated_at DESC LIMIT 200`).all();
    return json({ ok: true, canEdit: admin.role === 'superadmin', forms: results.map(rowToForm) });
  } catch (e) {
    if (noTable(e)) return json({ ok: true, canEdit: admin.role === 'superadmin', forms: [], notice: NO_TABLE });
    throw e;
  }
}

export async function onRequestPost({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const body = await readJson(request, 128 * 1024);
  if (!body || typeof body !== 'object') return error(400, 'invalid', 'Données illisibles. Rechargez la page et réessayez.');
  const { values, error: msg } = cleanForm(body);
  if (msg) return error(400, 'invalid', msg);
  const now = nowIso();
  let res;
  try {
    res = await env.DB.prepare(
      `INSERT INTO custom_forms (title, intro, fields, bouton, merci, open, created_at, updated_at, created_by, updated_by)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(values.title, values.intro || '', JSON.stringify(values.fields || []), values.bouton || 'Envoyer',
      values.merci || '', values.open === 0 ? 0 : 1, now, now, admin.id, admin.id).run();
  } catch (e) {
    if (noTable(e)) return error(503, 'no_table', NO_TABLE);
    throw e;
  }
  const id = res.meta.last_row_id;
  await audit(env.DB, admin.id, 'cforms.create', request, `form:${id}`, { title: values.title });
  const row = await env.DB.prepare(`${LIST_SQL} WHERE f.id = ?`).bind(id).first();
  return json({ ok: true, form: rowToForm(row) }, 201);
}
