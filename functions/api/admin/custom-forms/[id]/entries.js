// GET    /api/admin/custom-forms/:id/entries          réponses du formulaire, plus récentes d'abord (superadmin, éditeur)
// PATCH  /api/admin/custom-forms/:id/entries          { ids: [..], status: nouveau|lu|traite } (superadmin, éditeur)
// DELETE /api/admin/custom-forms/:id/entries          { ids: [..] } suppression définitive (superadmin)
import { audit } from '../../../../_lib/auth.js';
import { requireRole } from '../../../../_lib/guard.js';
import { error, json, readJson } from '../../../../_lib/http.js';
import { ENTRY_STATUSES, findForm, rowToEntry } from '../../../../_lib/custom-forms.js';

function cleanIds(v) {
  return Array.from(new Set((Array.isArray(v) ? v : []).map(Number).filter((n) => Number.isInteger(n) && n > 0))).slice(0, 500);
}

export async function onRequestGet({ request, env, params }) {
  const { response } = await requireRole(env, request, ['superadmin', 'editor']);
  if (response) return response;
  const f = await findForm(env, params.id);
  if (f.response) return f.response;
  const { results } = await env.DB.prepare('SELECT * FROM form_entries WHERE form_id = ? ORDER BY id DESC LIMIT 2000').bind(f.row.id).all();
  return json({ ok: true, entries: results.map(rowToEntry) });
}

export async function onRequestPatch({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'editor']);
  if (response) return response;
  const f = await findForm(env, params.id);
  if (f.response) return f.response;
  const body = await readJson(request);
  const ids = cleanIds(body && body.ids);
  if (!ids.length || !ENTRY_STATUSES.includes(body.status)) return error(400, 'invalid', 'Choisissez au moins une réponse et un statut.');
  await env.DB.prepare(`UPDATE form_entries SET status = ? WHERE form_id = ? AND id IN (${ids.map(() => '?').join(',')})`)
    .bind(body.status, f.row.id, ...ids).run();
  await audit(env.DB, admin.id, 'cforms.entries.status', request, `form:${f.row.id}`, { ids, status: body.status });
  return json({ ok: true });
}

export async function onRequestDelete({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const f = await findForm(env, params.id);
  if (f.response) return f.response;
  const body = await readJson(request);
  const ids = cleanIds(body && body.ids);
  if (!ids.length) return error(400, 'invalid', 'Choisissez au moins une réponse à supprimer.');
  await env.DB.prepare(`DELETE FROM form_entries WHERE form_id = ? AND id IN (${ids.map(() => '?').join(',')})`)
    .bind(f.row.id, ...ids).run();
  await audit(env.DB, admin.id, 'cforms.entries.delete', request, `form:${f.row.id}`, { ids });
  return json({ ok: true });
}
