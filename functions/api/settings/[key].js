// GET /api/settings/:key
// Renvoie les réglages publics actifs pour la clé donnée (ex. "home").
import { json, error } from '../../_lib/http.js';
import { DEFAULT_SETTINGS, GENERIC_KEYS, PUBLIC_KEYS } from '../../_lib/settings.js';
import { autoTotals } from '../../_lib/campagne.js';

export async function onRequestGet({ env, params }) {
  const key = String(params.key || '').trim().toLowerCase();
  if (!key) return error(400, 'bad_key', 'Clé de réglage requise.');
  // Lecture publique limitée aux réglages affichés sur le site.
  if (!PUBLIC_KEYS.includes(key)) return error(404, 'not_found', 'Aucun réglage trouvé pour cette clé.');

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

  settings = GENERIC_KEYS[key].clean(settings);

  // Campagne en mode automatique : le montant récolté de l'accueil vient de la table donations.
  if (key === 'home') {
    const auto = await autoTotals(env.DB);
    if (auto) settings = { ...settings, campagne: { ...settings.campagne, recolte: auto.recolte } };
  }

  return json(
    { ok: true, key, settings, updatedAt },
    200,
    { 'Cache-Control': 'public, max-age=15, stale-while-revalidate=120' }
  );
}
