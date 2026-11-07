// POST /api/views
// Comptabilise anonymement la consultation d'une page publique (sans cookies ni IP).
import { json, error, readJson } from '../_lib/http.js';

export async function onRequestPost({ request, env }) {
  if (!env.DB) return error(503, 'no_db', 'Base de données non disponible.');

  const body = await readJson(request, 1024);
  let path = typeof body?.path === 'string' ? body.path.trim() : '';
  if (!path) path = '/';

  // Ne pas comptabiliser les pages admin ni les appels API
  if (path.startsWith('/api') || path.startsWith('/SA-') || path.startsWith('/superadmin')) {
    return json({ ok: true, ignored: true });
  }

  // Normalisation du chemin
  if (path === '' || path === '/index.html') path = '/';
  if (path.length > 100) path = path.slice(0, 100);

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
