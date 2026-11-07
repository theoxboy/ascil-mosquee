// POST /api/views
// Comptabilise anonymement la consultation d'une page publique (sans cookies ni IP).
import { json, error, readJson } from '../_lib/http.js';

const PAGES = ['Main', 'Horaires', 'APropos', 'Services', 'Dons', 'Evenements', 'Ressources', 'Contact',
  'N2-Cours', 'N2-Mariages', 'N2-Funerailles', 'N2-AideAlimentaire', 'N2-EspaceFemmes', 'N2-Khutba',
  'N3-Rappel', 'N3-Campagne', 'N3-Calendrier', 'N3-Inscription', 'N3-Dua'];
// /Horaires.dc.html, /M-Horaires.dc, /T-Accueil.dc.html… (Accueil n'existe qu'en M- et T-).
const KNOWN_PAGE = new RegExp('^/((?:(?:M-|T-)?(?:' + PAGES.join('|') + '))|(?:M-|T-)Accueil)\\.dc(?:\\.html)?$');

export async function onRequestPost({ request, env }) {
  if (!env.DB) return error(503, 'no_db', 'Base de données non disponible.');

  const body = await readJson(request, 1024);
  let path = typeof body?.path === 'string' ? body.path.trim() : '';
  if (!path) path = '/';

  // Seules les pages publiques connues du site sont comptées (pas d'adresse inventée,
  // pas de pages admin) ; la forme « jolie » sans .html est ramenée à la forme du fichier.
  if (path === '/index.html' || path === '/index') path = '/';
  if (path !== '/') {
    const m = KNOWN_PAGE.exec(path);
    if (!m) return json({ ok: true, ignored: true });
    path = `/${m[1]}.dc.html`;
  }

  try {
    await env.DB.prepare(`
      INSERT INTO page_views (path, viewed_date, count)
      VALUES (?, strftime('%Y-%m-%d', 'now'), 1)
      ON CONFLICT(path, viewed_date) DO UPDATE SET count = count + 1
    `).bind(path).run();
  } catch (err) {
    console.warn('page_views insert error:', err && err.message);
  }

  return json({ ok: true });
}
