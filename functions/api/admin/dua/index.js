// /api/admin/dua : modération du mur « Dua et annonces » (Ressources → Dua et annonces).
//  GET                                                    à valider (en attente ou signalés), publiés, compteurs
//  PATCH { id, action:'publier'|'refuser'|'retirer'|'modifier', texte?, signature?, categorie? }
//  DELETE ?id=N                                           supprime définitivement un message
// Réservé au superadmin et à l'éditeur.
import { requireRole } from '../../../_lib/guard.js';
import { json, error, readJson } from '../../../_lib/http.js';
import { audit } from '../../../_lib/auth.js';
import { readDuaSettings, cleanDuaMessage, noTable, NO_TABLE } from '../../../_lib/dua.js';

const ROLES = ['superadmin', 'editor'];
const COLS = 'id, type, categorie, texte, signature, status, signale, amin, created_at, published_at';

export async function onRequestGet({ request, env }) {
  const { response } = await requireRole(env, request, ROLES);
  if (response) return response;
  try {
    const [p, q] = await Promise.all([
      env.DB.prepare(`SELECT ${COLS} FROM dua_messages WHERE status = 'attente' OR (status = 'publie' AND signale = 1) ORDER BY signale DESC, id ASC LIMIT 200`).all(),
      env.DB.prepare(`SELECT ${COLS} FROM dua_messages WHERE status = 'publie' AND signale = 0 ORDER BY published_at DESC, id DESC LIMIT 200`).all(),
    ]);
    return json({ ok: true, pending: p?.results || [], published: q?.results || [] });
  } catch (err) {
    console.error('dua admin list error:', err && err.message);
    if (noTable(err)) return error(503, 'no_table', NO_TABLE);
    return error(500, 'db_error', 'Impossible de charger les messages du mur. Réessayez dans un instant.');
  }
}

export async function onRequestPatch({ request, env }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const body = await readJson(request, 8 * 1024);
  const id = parseInt(body && body.id, 10);
  const action = body && body.action;
  if (!(id > 0) || !['publier', 'refuser', 'retirer', 'modifier'].includes(action)) {
    return error(400, 'invalid_payload', 'Message ou action non reconnus. Rechargez la page et réessayez.');
  }
  try {
    const row = await env.DB.prepare('SELECT type FROM dua_messages WHERE id = ?').bind(id).first();
    if (!row) return error(404, 'not_found', 'Ce message n’existe plus. Il a peut-être été supprimé.');
    if (action === 'modifier') {
      const rules = await readDuaSettings(env.DB);
      const checked = cleanDuaMessage({ ...body, type: row.type }, { ...rules, max: 1000 }, { admin: true });
      if (!checked.value) return error(400, checked.code, checked.message);
      const v = checked.value;
      await env.DB.prepare('UPDATE dua_messages SET texte = ?, signature = ?, categorie = ? WHERE id = ?').bind(v.texte, v.signature, v.categorie, id).run();
    } else if (action === 'publier') {
      await env.DB.prepare("UPDATE dua_messages SET status = 'publie', signale = 0, published_at = COALESCE(published_at, strftime('%Y-%m-%dT%H:%M:%fZ', 'now')) WHERE id = ?").bind(id).run();
    } else {
      // refuser : le message n'apparaît plus ; retirer : un message publié quitte le mur.
      await env.DB.prepare("UPDATE dua_messages SET status = 'refuse', signale = 0 WHERE id = ?").bind(id).run();
    }
    await audit(env.DB, admin.id, 'dua.' + action, request, `dua:${id}`, { type: row.type });
    const msg = await env.DB.prepare(`SELECT ${COLS} FROM dua_messages WHERE id = ?`).bind(id).first();
    return json({ ok: true, message: msg });
  } catch (err) {
    console.error('dua admin patch error:', err && err.message);
    if (noTable(err)) return error(503, 'no_table', NO_TABLE);
    return error(500, 'db_error', 'Le message n’a pas pu être modifié. Réessayez dans un instant.');
  }
}

export async function onRequestDelete({ request, env }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const id = parseInt(new URL(request.url).searchParams.get('id'), 10);
  if (!(id > 0)) return error(400, 'invalid_id', 'Message non reconnu. Rechargez la page et réessayez.');
  try {
    const row = await env.DB.prepare('SELECT type FROM dua_messages WHERE id = ?').bind(id).first();
    if (!row) return error(404, 'not_found', 'Ce message n’existe plus. Il a peut-être déjà été supprimé.');
    await env.DB.prepare('DELETE FROM dua_messages WHERE id = ?').bind(id).run();
    await audit(env.DB, admin.id, 'dua.delete', request, `dua:${id}`, { type: row.type });
    return json({ ok: true, deleted_id: id });
  } catch (err) {
    console.error('dua admin delete error:', err && err.message);
    return error(500, 'db_error', 'Le message n’a pas pu être supprimé. Réessayez dans un instant.');
  }
}
