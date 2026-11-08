// GET  /api/admin/media   photos déjà envoyées (les 200 plus récentes)
// POST /api/admin/media   envoi d'une photo : le corps de la requête est le fichier lui-même,
//                         son nom d'origine dans l'en-tête X-File-Name (encodé). 5 Mo au plus.
// Superadmin et éditeur.
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json } from '../../../_lib/http.js';
import { nowIso } from '../../../_lib/settings.js';
import { MAX_BYTES, NO_STORAGE, NO_TABLE, dimensions, noTable, randomKey, rowToMedia, sniff } from '../../../_lib/media.js';

const ROLES = ['superadmin', 'editor'];

export async function onRequestGet({ request, env }) {
  const { response } = await requireRole(env, request, ROLES);
  if (response) return response;
  try {
    const { results } = await env.DB.prepare('SELECT * FROM media ORDER BY id DESC LIMIT 200').all();
    return json({ ok: true, storage: !!env.MEDIA, media: results.map(rowToMedia) });
  } catch (e) {
    if (noTable(e)) return json({ ok: true, storage: !!env.MEDIA, media: [], notice: NO_TABLE });
    throw e;
  }
}

export async function onRequestPost({ request, env }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  if (!env.MEDIA) return error(503, 'no_storage', NO_STORAGE);

  const len = Number(request.headers.get('Content-Length') || 0);
  if (len > MAX_BYTES) return error(413, 'too_big', 'Cette photo dépasse 5 Mo. Réduisez-la (par exemple avec l’outil de partage du téléphone), puis réessayez.');
  const buf = new Uint8Array(await request.arrayBuffer());
  if (!buf.length) return error(400, 'empty', 'Le fichier est vide. Choisissez une autre photo.');
  if (buf.length > MAX_BYTES) return error(413, 'too_big', 'Cette photo dépasse 5 Mo. Réduisez-la, puis réessayez.');

  const mime = sniff(buf);
  if (!mime) return error(415, 'bad_type', 'Ce fichier n’est pas une photo acceptée. Formats permis : JPEG, PNG, WebP ou GIF.');
  const { width, height } = dimensions(buf, mime);

  let name = '';
  try { name = decodeURIComponent(request.headers.get('X-File-Name') || ''); } catch { name = ''; }
  name = name.replace(/[\u0000-\u001f\u007f<>"]/g, '').trim().slice(0, 120);

  const key = randomKey(mime);
  try {
    await env.DB.prepare('SELECT id FROM media LIMIT 1').first();
  } catch (e) {
    if (noTable(e)) return error(503, 'no_table', NO_TABLE);
    throw e;
  }
  await env.MEDIA.put(key, buf, { httpMetadata: { contentType: mime, cacheControl: 'public, max-age=31536000, immutable' } });
  const res = await env.DB.prepare(
    'INSERT INTO media (file_key, mime, size, width, height, name, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
  ).bind(key, mime, buf.length, width, height, name, nowIso(), admin.id).run();
  const id = res.meta.last_row_id;
  await audit(env.DB, admin.id, 'media.upload', request, `media:${id}`, { name, size: buf.length, mime });
  const row = await env.DB.prepare('SELECT * FROM media WHERE id = ?').bind(id).first();
  return json({ ok: true, media: rowToMedia(row) }, 201);
}
