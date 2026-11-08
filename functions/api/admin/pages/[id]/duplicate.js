// POST /api/admin/pages/:id/duplicate
// Copie la page (contenu et réglages) en brouillon, titre « … (copie) », lien libre suivant.
import { audit } from '../../../../_lib/auth.js';
import { requireRole } from '../../../../_lib/guard.js';
import { json } from '../../../../_lib/http.js';
import { nowIso } from '../../../../_lib/settings.js';
import { ROLES, SELECT_PAGE, loadPage, rowToPage, uniqueSlug } from '../../../../_lib/custom-pages.js';

export async function onRequestPost({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const page = await loadPage(env.DB, params.id);
  if (page.response) return page.response;
  const src = page.row;

  const slug = await uniqueSlug(env.DB, `${src.slug}-copie`.slice(0, 60).replace(/-+$/g, ''));
  const title = `${src.title} (copie)`.slice(0, 120);
  const now = nowIso();
  const res = await env.DB.batch([
    env.DB.prepare('DELETE FROM page_redirects WHERE old_slug = ?').bind(slug),
    env.DB.prepare(
      `INSERT INTO custom_pages (slug, title, blocks, visibility, layout, width, description,
                                 created_at, updated_at, created_by, updated_by)
       VALUES (?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)`
    ).bind(slug, title, src.blocks, src.layout, src.width, src.description, now, now, admin.id, admin.id),
  ]);
  const id = res[1].meta.last_row_id;
  await audit(env.DB, admin.id, 'pages.duplicate', request, `page:${id}`, {
    from: src.id,
    fromTitle: src.title,
    title,
    slug,
  });

  const row = await env.DB.prepare(`${SELECT_PAGE} WHERE p.id = ?`).bind(id).first();
  return json({ ok: true, page: rowToPage(row) }, 201);
}
