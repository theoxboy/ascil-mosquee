// DELETE /api/admin/media/:id   supprime une photo (fichier et fiche). Superadmin et éditeur.
// Les pages qui l'affichaient n'affichent plus rien à sa place (le bloc reste, vide).
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json } from '../../../_lib/http.js';
import { NO_TABLE, noTable } from '../../../_lib/media.js';

export async function onRequestDelete({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'editor']);
  if (response) return response;
  const id = Number(params.id);
  if (!Number.isInteger(id) || id < 1) return error(404, 'not_found', 'Cette photo n’existe pas.');
  let row;
  try {
    row = await env.DB.prepare('SELECT * FROM media WHERE id = ?').bind(id).first();
  } catch (e) {
    if (noTable(e)) return error(503, 'no_table', NO_TABLE);
    throw e;
  }
  if (!row) return error(404, 'not_found', 'Cette photo n’existe pas, ou a déjà été supprimée.');
  if (env.MEDIA) await env.MEDIA.delete(row.file_key);
  await env.DB.prepare('DELETE FROM media WHERE id = ?').bind(id).run();
  await audit(env.DB, admin.id, 'media.delete', request, `media:${id}`, { name: row.name });
  return json({ ok: true });
}
