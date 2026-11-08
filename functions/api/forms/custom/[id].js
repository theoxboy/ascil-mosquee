// POST /api/forms/custom/:id
// Envoi d'un formulaire créé dans le panneau, depuis une page /p/<lien>. C'est un vrai formulaire
// HTML (la page n'a aucun script) : on répond par une redirection vers la page, qui affiche le
// message de remerciement ou l'erreur. Protections, comme les autres formulaires du site :
//  - le middleware refuse les envois qui ne viennent pas du site lui-même ;
//  - champ piège invisible (_site) : rempli → on fait comme si c'était envoyé, sans rien garder ;
//  - délai minimal entre l'affichage de la page et l'envoi (_t) ;
//  - au plus 5 envois par connexion en 15 minutes (table rate_limits) ;
//  - seuls les champs connus du formulaire sont gardés, chacun vérifié selon son type.
import { clientIp } from '../../../_lib/auth.js';
import { SLUG_RE } from '../../../_lib/custom-pages.js';
import { MIN_FILL_MS, cleanEntry, noTable, rowToForm } from '../../../_lib/custom-forms.js';
import { limited } from '../../../_lib/dua.js';

const MAX_BYTES = 64 * 1024;

function back(slug, id, code) {
  const target = slug ? `/p/${slug}?f=${id}&r=${code}#form-${id}` : `/?form=${code}`;
  return new Response(null, { status: 303, headers: { Location: target, 'Cache-Control': 'no-store' } });
}

export async function onRequestPost({ request, env, params }) {
  const id = Number(params.id);
  if (!Number.isInteger(id) || id < 1) return back('', 0, 'server');
  if (Number(request.headers.get('Content-Length') || 0) > MAX_BYTES) return back('', id, 'invalid');

  let fd;
  try {
    fd = await request.formData();
  } catch {
    return back('', id, 'invalid');
  }
  const rawSlug = String(fd.get('_p') || '').toLowerCase();
  const slug = SLUG_RE.test(rawSlug) && rawSlug.length <= 60 ? rawSlug : '';

  // Robot : il croit que c'est envoyé.
  if (String(fd.get('_site') || '').trim()) return back(slug, id, 'ok');

  let row;
  try {
    row = await env.DB.prepare('SELECT * FROM custom_forms WHERE id = ?').bind(id).first();
  } catch (e) {
    if (noTable(e)) return back(slug, id, 'server');
    throw e;
  }
  if (!row) return back(slug, id, 'server');
  const form = rowToForm(row);
  if (!form.open) return back(slug, id, 'closed');

  const shown = Number(fd.get('_t'));
  if (!Number.isFinite(shown) || Date.now() - shown < MIN_FILL_MS) return back(slug, id, 'too_fast');

  const checked = cleanEntry(form, fd);
  if (!checked.value) return back(slug, id, checked.code);

  if (await limited(env.DB, 'forms.custom', clientIp(request), 5, 15 * 60 * 1000)) return back(slug, id, 'too_many');

  try {
    await env.DB.prepare('INSERT INTO form_entries (form_id, data, page_slug) VALUES (?, ?, ?)')
      .bind(form.id, JSON.stringify(checked.value), slug || null).run();
  } catch (e) {
    console.error('form_entries insert error:', e && e.message);
    return back(slug, id, 'server');
  }
  return back(slug, id, 'ok');
}
