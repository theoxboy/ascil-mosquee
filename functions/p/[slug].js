// GET /p/<lien> : page créée dans le superadmin, rendue côté serveur.
//  - publiée : visible par tous, indexable ;
//  - lien privé : visible à qui a le lien, jamais indexée ;
//  - brouillon : visible seulement par un compte connecté (bandeau « Brouillon »), sinon introuvable ;
//  - ancienne adresse : redirection 301 vers l'adresse actuelle.
import { currentAdmin } from '../_lib/auth.js';
import { SLUG_RE, rowToPage } from '../_lib/custom-pages.js';
import { renderNotFound, renderPage } from '../_lib/render-page.js';
import { cleanAlertSettings } from '../_lib/settings.js';

const SECURITY = {
  'Content-Type': 'text/html; charset=utf-8',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  // Aucune exécution de script : la page n'en contient pas.
  'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
    + "font-src https://fonts.gstatic.com; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
};

function html(body, status, extra = {}) {
  return new Response(body, { status, headers: { ...SECURITY, ...extra } });
}
const notFound = () => html(renderNotFound(), 404, { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' });

// Bannière d'alerte active aujourd'hui (heure du Québec), comme sur le reste du site.
async function activeAlert(db) {
  try {
    const row = await db.prepare("SELECT value FROM site_settings WHERE key = 'alert'").first();
    const a = cleanAlertSettings(row ? JSON.parse(row.value) : null);
    if (!a.on || !a.message) return null;
    const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Toronto' }).format(new Date());
    if ((a.from && today < a.from) || (a.to && today > a.to)) return null;
    return a;
  } catch {
    return null;
  }
}

export async function onRequestGet({ request, env, params }) {
  const db = env.DB;
  const slug = String(params.slug || '').toLowerCase();
  if (!db || !SLUG_RE.test(slug) || slug.length > 60) return notFound();

  let row = await db.prepare('SELECT * FROM custom_pages WHERE slug = ?').bind(slug).first();
  if (!row) {
    const r = await db.prepare(
      'SELECT p.slug FROM page_redirects r JOIN custom_pages p ON p.id = r.page_id WHERE r.old_slug = ?'
    ).bind(slug).first();
    if (r) return new Response(null, { status: 301, headers: { Location: `/p/${r.slug}`, 'Cache-Control': 'public, max-age=300' } });
    return notFound();
  }
  const page = rowToPage(row);

  let draft = false;
  if (page.visibility === 'draft') {
    const admin = await currentAdmin(db, request).catch(() => null);
    if (!admin) return notFound();
    draft = true;
  }

  const body = renderPage(page, { alert: await activeAlert(db), draft, origin: new URL(request.url).origin });
  if (page.visibility === 'published') {
    return html(body, 200, { 'Cache-Control': 'public, max-age=60' });
  }
  return html(body, 200, { 'Cache-Control': 'private, no-store', 'X-Robots-Tag': 'noindex, nofollow' });
}
