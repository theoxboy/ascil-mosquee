// GET    /api/admin/pages/:id   page complète (blocs compris)
// PUT    /api/admin/pages/:id   { title?, slug?, blocks?, visibility?, layout?, width?, description? }
//                               si le lien change, l'ancien redirige vers le nouveau
// DELETE /api/admin/pages/:id   suppression définitive (et ses anciennes adresses)
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import { nowIso } from '../../../_lib/settings.js';
import { ROLES, SELECT_PAGE, cleanPage, loadPage, rowToPage, slugTaken } from '../../../_lib/custom-pages.js';

export async function onRequestGet({ request, env, params }) {
  const { response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const page = await loadPage(env.DB, params.id);
  if (page.response) return page.response;
  return json({ ok: true, page: rowToPage(page.row) });
}

export async function onRequestPut({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const page = await loadPage(env.DB, params.id);
  if (page.response) return page.response;
  const current = page.row;

  // Une page peut contenir beaucoup de texte : jusqu'à 256 ko.
  const body = await readJson(request, 256 * 1024);
  if (!body || typeof body !== 'object') return error(400, 'invalid', 'Données illisibles ou page trop longue. Rechargez la page et réessayez.');
  const { values, error: msg } = cleanPage(body, { partial: true });
  if (msg) return error(400, 'invalid', msg);
  if (!Object.keys(values).length) return error(400, 'invalid', 'Aucune modification à enregistrer.');

  const stmts = [];
  const slugChanged = values.slug !== undefined && values.slug !== current.slug.toLowerCase();
  if (slugChanged) {
    if (await slugTaken(env.DB, values.slug, current.id)) {
      return error(409, 'slug_taken', `Le lien « ${values.slug} » est déjà utilisé par une autre page. Choisissez-en un autre.`);
    }
    const now = nowIso();
    stmts.push(
      // La nouvelle adresse ne doit plus être une redirection (d'une autre page ou de celle-ci).
      env.DB.prepare('DELETE FROM page_redirects WHERE old_slug = ?').bind(values.slug),
      // L'ancienne adresse redirige vers cette page.
      env.DB.prepare('INSERT OR REPLACE INTO page_redirects (old_slug, page_id, created_at) VALUES (?, ?, ?)')
        .bind(current.slug, current.id, now),
    );
  } else {
    delete values.slug;
  }

  const cols = Object.keys(values);
  if (cols.length) {
    const sets = cols.map((c) => `${c} = ?`).concat('updated_at = ?', 'updated_by = ?');
    const binds = cols.map((c) => (c === 'blocks' ? JSON.stringify(values[c]) : values[c]));
    stmts.push(env.DB.prepare(`UPDATE custom_pages SET ${sets.join(', ')} WHERE id = ?`).bind(...binds, nowIso(), admin.id, current.id));
  }
  await env.DB.batch(stmts);

  await audit(env.DB, admin.id, 'pages.update', request, `page:${current.id}`, {
    fields: cols, ...(slugChanged ? { oldSlug: current.slug, newSlug: values.slug } : {}),
  });
  const row = await env.DB.prepare(`${SELECT_PAGE} WHERE p.id = ?`).bind(current.id).first();
  return json({ ok: true, page: rowToPage(row) });
}

export async function onRequestDelete({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const page = await loadPage(env.DB, params.id);
  if (page.response) return page.response;

  await env.DB.batch([
    env.DB.prepare('DELETE FROM page_redirects WHERE page_id = ?').bind(page.row.id),
    env.DB.prepare('DELETE FROM custom_pages WHERE id = ?').bind(page.row.id),
  ]);
  await audit(env.DB, admin.id, 'pages.delete', request, `page:${page.row.id}`, { slug: page.row.slug, title: page.row.title });
  return json({ ok: true, deleted: page.row.id });
}
