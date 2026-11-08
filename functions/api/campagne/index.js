// GET /api/campagne
// Données publiques de la campagne du nouveau lieu (page Campagne en direct, page À propos).
import { json } from '../../_lib/http.js';
import { readCampagne } from '../../_lib/campagne.js';

export async function onRequestGet({ env }) {
  const campagne = await readCampagne(env.DB);
  return json({ ok: true, ...campagne }, 200, { 'Cache-Control': 'public, max-age=15, stale-while-revalidate=60' });
}
