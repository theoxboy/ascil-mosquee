// GET /api/settings/:key
// Renvoie les réglages publics actifs pour la clé donnée (ex. "home").
import { json, error } from '../../_lib/http.js';
import { DEFAULT_SETTINGS, cleanHomeSettings } from '../../_lib/settings.js';

export async function onRequestGet({ env, params }) {
  const key = String(params.key || '').trim().toLowerCase();
  if (!key) return error(400, 'bad_key', 'Clé de réglage requise.');

  let settings = null;
  let updatedAt = null;

  if (env.DB) {
    try {
      const row = await env.DB.prepare('SELECT value, updated_at FROM site_settings WHERE key = ?').bind(key).first();
      if (row && row.value) {
        settings = JSON.parse(row.value);
        updatedAt = row.updated_at;
      }
    } catch (e) {
      console.warn('site_settings read fallback:', e && e.message);
    }
  }

  // Si non trouvé en base, fallback sur les valeurs par défaut
  if (!settings && DEFAULT_SETTINGS[key]) {
    settings = DEFAULT_SETTINGS[key];
  }

  if (!settings) {
    return error(404, 'not_found', 'Aucun réglage trouvé pour cette clé.');
  }

  if (key === 'home') {
    settings = cleanHomeSettings(settings);
  }

  return json(
    { ok: true, key, settings, updatedAt },
    200,
    { 'Cache-Control': 'public, max-age=15, stale-while-revalidate=120' }
  );
}
