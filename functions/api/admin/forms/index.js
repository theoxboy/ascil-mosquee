// /api/admin/forms : boîte de réception (Contact → Demandes reçues).
//  GET    ?status=nouveau|lu|traite&source=contact|…&q=texte   liste (500 au plus) et compteurs
//  PATCH  { id, status }                                          change le statut d'une demande
//  DELETE ?id=N                                                   supprime définitivement une demande
// Réservé au superadmin et à l'éditeur (comme la page SA-Contact).
import { requireRole } from '../../../_lib/guard.js';
import { json, error, readJson } from '../../../_lib/http.js';
import { audit } from '../../../_lib/auth.js';
import { FORM_SOURCES, FORM_STATUSES, parseDetails } from '../../../_lib/forms.js';

const ROLES = ['superadmin', 'editor'];
const NO_TABLE = 'La boîte de réception n’est pas encore installée : appliquez la migration 0009 dans la console D1.';

export async function onRequestGet({ request, env }) {
  const { response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const url = new URL(request.url);
  const status = url.searchParams.get('status') || '';
  const source = url.searchParams.get('source') || '';
  const q = (url.searchParams.get('q') || '').trim().slice(0, 100);

  let sql = 'SELECT id, source, sujet, nom, contact, message, details, status, created_at FROM form_messages WHERE 1 = 1';
  const params = [];
  if (FORM_STATUSES.includes(status)) { sql += ' AND status = ?'; params.push(status); }
  if (FORM_SOURCES[source]) { sql += ' AND source = ?'; params.push(source); }
  if (q) {
    sql += ' AND (nom LIKE ? OR contact LIKE ? OR sujet LIKE ? OR message LIKE ?)';
    const term = `%${q.replace(/[%_]/g, ' ')}%`;
    params.push(term, term, term, term);
  }
  sql += ' ORDER BY id DESC LIMIT 500';

  try {
    const [list, counts] = await Promise.all([
      env.DB.prepare(sql).bind(...params).all(),
      env.DB.prepare('SELECT status, COUNT(*) AS n FROM form_messages GROUP BY status').all(),
    ]);
    const c = { nouveau: 0, lu: 0, traite: 0 };
    for (const r of counts?.results || []) if (r.status in c) c[r.status] = Number(r.n) || 0;
    return json({
      ok: true,
      counts: { ...c, total: c.nouveau + c.lu + c.traite },
      sources: FORM_SOURCES,
      messages: (list?.results || []).map((r) => ({ ...r, details: parseDetails(r.details), sourceLabel: FORM_SOURCES[r.source] || r.source })),
    });
  } catch (err) {
    console.error('form_messages list error:', err && err.message);
    if (/no such table/i.test(String(err && err.message))) return error(503, 'no_table', NO_TABLE);
    return error(500, 'db_error', 'Impossible de charger les demandes reçues. Réessayez dans un instant.');
  }
}

export async function onRequestPatch({ request, env }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const body = await readJson(request, 1024);
  const id = parseInt(body && body.id, 10);
  const status = body && body.status;
  if (!(id > 0) || !FORM_STATUSES.includes(status)) {
    return error(400, 'invalid_payload', 'Demande ou statut non reconnu. Rechargez la page et réessayez.');
  }
  try {
    const res = await env.DB.prepare('UPDATE form_messages SET status = ? WHERE id = ?').bind(status, id).run();
    if (!res?.meta?.changes) return error(404, 'not_found', 'Cette demande n’existe plus. Elle a peut-être été supprimée.');
    await audit(env.DB, admin.id, 'forms.status', request, `form:${id}`, { status });
    return json({ ok: true, id, status });
  } catch (err) {
    console.error('form_messages status error:', err && err.message);
    return error(500, 'db_error', 'Le statut n’a pas pu être changé. Réessayez dans un instant.');
  }
}

export async function onRequestDelete({ request, env }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const id = parseInt(new URL(request.url).searchParams.get('id'), 10);
  if (!(id > 0)) return error(400, 'invalid_id', 'Demande non reconnue. Rechargez la page et réessayez.');
  try {
    const row = await env.DB.prepare('SELECT source FROM form_messages WHERE id = ?').bind(id).first();
    if (!row) return error(404, 'not_found', 'Cette demande n’existe plus. Elle a peut-être déjà été supprimée.');
    await env.DB.prepare('DELETE FROM form_messages WHERE id = ?').bind(id).run();
    // Le journal ne garde ni le nom ni le message : seulement le formulaire d'origine.
    await audit(env.DB, admin.id, 'forms.delete', request, `form:${id}`, { source: row.source });
    return json({ ok: true, deleted_id: id });
  } catch (err) {
    console.error('form_messages delete error:', err && err.message);
    return error(500, 'db_error', 'La demande n’a pas pu être supprimée. Réessayez dans un instant.');
  }
}
