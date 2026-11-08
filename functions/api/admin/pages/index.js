// GET  /api/admin/pages   liste des pages créées (superadmin, éditeur)
// POST /api/admin/pages   { title, slug?, visibility? } crée une page (en brouillon par défaut), vide ;
//                         le lien est tiré du titre s'il n'est pas fourni, et rendu unique (ramadan-2027, ramadan-2027-2…)
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import { nowIso } from '../../../_lib/settings.js';
import { ROLES, SELECT_PAGE, cleanPage, rowToPage, slugTaken, slugify, uniqueSlug } from '../../../_lib/custom-pages.js';

export async function onRequestGet({ request, env }) {
  const { response } = await requireRole(env, request, ROLES);
  if (response) return response;
  const { results } = await env.DB.prepare(`${SELECT_PAGE} ORDER BY p.updated_at DESC LIMIT 200`).all();
  return json({
    ok: true,
    pages: results.map((r) => {
      const p = rowToPage(r);
      // La liste n'a pas besoin du contenu : juste le nombre de blocs.
      return { ...p, blocks: undefined, blockCount: p.blocks.length };
    }),
  });
}

export async function onRequestPost({ request, env }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;

  const body = await readJson(request);
  if (!body || typeof body !== 'object') return error(400, 'invalid', 'Données illisibles. Rechargez la page et réessayez.');
  const { values, error: msg } = cleanPage({
    title: body.title,
    ...(body.slug !== undefined && String(body.slug).trim() !== '' ? { slug: body.slug } : {}),
    ...(body.visibility !== undefined ? { visibility: body.visibility } : {}),
  });
  if (msg) return error(400, 'invalid', msg);
  const visibility = values.visibility || 'draft';

  let slug = values.slug;
  if (slug) {
    if (await slugTaken(env.DB, slug)) {
      return error(409, 'slug_taken', `Le lien « ${slug} » est déjà utilisé par une autre page. Choisissez-en un autre.`);
    }
  } else {
    slug = await uniqueSlug(env.DB, slugify(values.title));
  }

  const now = nowIso();
  const res = await env.DB.batch([
    // Une ancienne adresse d'une autre page ne bloque pas : cette page la récupère.
    env.DB.prepare('DELETE FROM page_redirects WHERE old_slug = ?').bind(slug),
    env.DB.prepare(
      `INSERT INTO custom_pages (slug, title, blocks, visibility, layout, width, description,
                                 created_at, updated_at, created_by, updated_by)
       VALUES (?, ?, '[]', ?, 'site', 'normal', '', ?, ?, ?, ?)`
    ).bind(slug, values.title, visibility, now, now, admin.id, admin.id),
  ]);
  const id = res[1].meta.last_row_id;
  await audit(env.DB, admin.id, 'pages.create', request, `page:${id}`, { slug, title: values.title, visibility });

  const row = await env.DB.prepare(`${SELECT_PAGE} WHERE p.id = ?`).bind(id).first();
  return json({ ok: true, page: rowToPage(row) }, 201);
}
