// Garde d'entrée : ne s'exécute que sur les chemins listés dans _routes.json
// (API, pages superadmin, fichiers du dépôt qui ne doivent pas être servis).
import { currentAdmin } from './_lib/auth.js';
import { error, sameOrigin } from './_lib/http.js';

const PRIVATE = [/^\/functions(\/|$)/, /^\/migrations(\/|$)/, /^\/scripts(\/|$)/, /^\/wrangler\.toml$/, /^\/_routes\.json$/, /^\/\.git/];
const LOGIN_PAGES = [/^\/superadmin(\.html)?$/, /^\/SA-Connexion\.dc(\.html)?$/];
const ADMIN_PAGE = /^\/SA-[A-Za-z]+\.dc(\.html)?$/;

const PAGE_HEADERS = {
  'Cache-Control': 'no-store',
  'X-Robots-Tag': 'noindex, nofollow',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'same-origin',
  'X-Content-Type-Options': 'nosniff',
};

function withHeaders(response, headers) {
  const r = new Response(response.body, response);
  for (const [k, v] of Object.entries(headers)) r.headers.set(k, v);
  return r;
}

function redirect(location) {
  return new Response(null, { status: 302, headers: { Location: location, 'Cache-Control': 'no-store' } });
}

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const path = url.pathname;

  if (PRIVATE.some((re) => re.test(path))) return new Response('Not found', { status: 404 });

  if (path.startsWith('/api/')) {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method) && !sameOrigin(request)) {
      return error(403, 'origin', 'Requête refusée : elle ne vient pas du site de l’ASCIL.');
    }
    if (!env.DB) return error(503, 'no_db', 'La base de données n’est pas reliée au site. Ajoutez la liaison D1 « DB » dans Cloudflare Pages.');
    try {
      return withHeaders(await next(), { 'X-Content-Type-Options': 'nosniff' });
    } catch (e) {
      console.error('api error', path, e && e.stack || e);
      return error(500, 'server', 'Une erreur interne est survenue. Réessayez dans un instant.');
    }
  }

  const isLogin = LOGIN_PAGES.some((re) => re.test(path));
  if (isLogin || ADMIN_PAGE.test(path)) {
    const admin = env.DB ? await currentAdmin(env.DB, request).catch(() => null) : null;
    if (isLogin) {
      if (admin) return redirect('/SA-Panneau.dc.html');
    } else if (!admin) {
      return redirect('/superadmin.html?next=' + encodeURIComponent(path + url.search));
    }
    return withHeaders(await next(), PAGE_HEADERS);
  }

  return next();
}
