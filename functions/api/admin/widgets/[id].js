// PUT    /api/admin/widgets/:id   modifie le code d'un widget (superadmin)
// DELETE /api/admin/widgets/:id   supprime un widget (superadmin) ; les pages qui l'affichaient ne montrent plus rien
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import { nowIso } from '../../../_lib/settings.js';
import { NO_TABLE, cleanWidget, noTable, rowToWidget } from '../../../_lib/widgets.js';

async function find(env, raw) {
  const id = Number(raw);
  if (!Number.isInteger(id) || id < 1) return { response: error(404, 'not_found', 'Ce widget n’existe pas.') };
  try {
    const row = await env.DB.prepare('SELECT * FROM page_widgets WHERE id = ?').bind(id).first();
    if (!row) return { response: error(404, 'not_found', 'Ce widget n’existe pas, ou a déjà été supprimé.') };
    return { row };
  } catch (e) {
    if (noTable(e)) return { response: error(503, 'no_table', NO_TABLE) };
    throw e;
  }
}

export async function onRequestPut({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const f = await find(env, params.id);
  if (f.response) return f.response;
  const body = await readJson(request, 300 * 1024);
  if (!body || typeof body !== 'object') return error(400, 'invalid', 'Code illisible ou trop long (300 ko au plus). Réessayez.');
  const w = cleanWidget(body);
  await env.DB.prepare(
    'UPDATE page_widgets SET title = ?, lang = ?, html = ?, css = ?, js = ?, net = ?, height = ?, updated_at = ?, updated_by = ? WHERE id = ?'
  ).bind(w.title, w.lang, w.html, w.css, w.js, w.net, w.height, nowIso(), admin.id, f.row.id).run();
  await audit(env.DB, admin.id, 'widgets.update', request, `widget:${f.row.id}`, { title: w.title, lang: w.lang, net: !!w.net });
  const row = await env.DB.prepare('SELECT * FROM page_widgets WHERE id = ?').bind(f.row.id).first();
  return json({ ok: true, widget: rowToWidget(row) });
}

export async function onRequestDelete({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const f = await find(env, params.id);
  if (f.response) return f.response;
  await env.DB.prepare('DELETE FROM page_widgets WHERE id = ?').bind(f.row.id).run();
  await audit(env.DB, admin.id, 'widgets.delete', request, `widget:${f.row.id}`, { title: f.row.title });
  return json({ ok: true });
}
