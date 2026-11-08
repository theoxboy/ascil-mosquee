// GET  /api/admin/widgets   liste des widgets (superadmin : avec le code ; éditeur : titres seulement)
// POST /api/admin/widgets   crée un widget { title, lang, html, css, js, net, height }   (superadmin)
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import { nowIso } from '../../../_lib/settings.js';
import { NO_TABLE, cleanWidget, noTable, rowToWidget } from '../../../_lib/widgets.js';

export async function onRequestGet({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'editor']);
  if (response) return response;
  try {
    const { results } = await env.DB.prepare('SELECT * FROM page_widgets ORDER BY updated_at DESC LIMIT 200').all();
    return json({ ok: true, widgets: results.map((r) => rowToWidget(r, admin.role === 'superadmin')) });
  } catch (e) {
    if (noTable(e)) return json({ ok: true, widgets: [], notice: NO_TABLE });
    throw e;
  }
}

export async function onRequestPost({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const body = await readJson(request, 300 * 1024);
  if (!body || typeof body !== 'object') return error(400, 'invalid', 'Code illisible ou trop long (300 ko au plus). Réessayez.');
  const w = cleanWidget(body);
  const now = nowIso();
  let res;
  try {
    res = await env.DB.prepare(
      `INSERT INTO page_widgets (title, lang, html, css, js, net, height, created_at, updated_at, created_by, updated_by)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(w.title, w.lang, w.html, w.css, w.js, w.net, w.height, now, now, admin.id, admin.id).run();
  } catch (e) {
    if (noTable(e)) return error(503, 'no_table', NO_TABLE);
    throw e;
  }
  const id = res.meta.last_row_id;
  await audit(env.DB, admin.id, 'widgets.create', request, `widget:${id}`, { title: w.title, lang: w.lang, net: !!w.net });
  const row = await env.DB.prepare('SELECT * FROM page_widgets WHERE id = ?').bind(id).first();
  return json({ ok: true, widget: rowToWidget(row) }, 201);
}
