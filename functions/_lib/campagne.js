// Campagne du nouveau lieu : données publiques, lues par /api/campagne (page Campagne en direct,
// page À propos), et montant récolté de l'accueil en mode automatique.
// Mode manuel : montants saisis dans le panneau. Mode automatique : calculés depuis la table donations.
import { DEFAULT_SETTINGS, cleanHomeSettings, cleanCampagneSettings } from './settings.js';

const WEEK = 7 * 864e5;

async function readKey(db, key) {
  if (!db) return null;
  try {
    const row = await db.prepare('SELECT value FROM site_settings WHERE key = ?').bind(key).first();
    return row && row.value ? JSON.parse(row.value) : null;
  } catch {
    return null;
  }
}

// Nom affiché d'un don : jamais le nom complet.
export function maskName(name, mode) {
  const parts = String(name || '').replace(/\s+/g, ' ').trim().split(' ').filter(Boolean);
  if (mode === 'anonyme' || !parts.length || /^anonyme$/i.test(parts[0])) return 'Anonyme';
  if (mode === 'initiales') return parts.slice(0, 3).map((p) => p.charAt(0).toUpperCase() + '.').join(' ');
  return parts[0].slice(0, 40);
}

// Totaux calculés depuis la table donations, ou null en mode manuel / sans base.
export async function autoTotals(db) {
  if (!db) return null;
  const c = cleanCampagneSettings((await readKey(db, 'campagne')) || DEFAULT_SETTINGS.campagne);
  if (!c.auto) return null;
  try {
    const row = await db.prepare('SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS total FROM donations').first();
    return { recolte: Math.max(0, Math.round(Number(row?.total) || 0)), donateurs: Number(row?.n) || 0 };
  } catch {
    return null;
  }
}

export async function readCampagne(db) {
  const home = cleanHomeSettings((await readKey(db, 'home')) || DEFAULT_SETTINGS.home);
  const c = cleanCampagneSettings((await readKey(db, 'campagne')) || DEFAULT_SETTINGS.campagne);
  const nombre = c.semaines.nombre;
  const out = {
    objectif: home.campagne.objectif,
    recolte: home.campagne.recolte,
    donateurs: c.donateurs,
    auto: c.auto,
    etapes: { on: c.etapes.on, items: c.etapes.items.filter((e) => e.on && e.libelle).map((e) => ({ seuil: e.seuil, libelle: e.libelle })) },
    // Semaines saisies dans le panneau : Semaine 1 = la plus ancienne ; aucune barre si tout est vide.
    semaines: {
      on: c.semaines.on,
      items: c.semaines.valeurs.some((v) => v > 0) ? c.semaines.valeurs.slice(0, nombre).map((v, i) => ({ label: 'S' + (i + 1), montant: v })) : [],
    },
    derniers: { on: c.derniers.on && c.auto, montant: c.derniers.montant, items: [] },
  };
  if (!c.auto || !db) return out;

  try {
    const tot = await db.prepare('SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0) AS total FROM donations').first();
    out.recolte = Math.max(0, Math.round(Number(tot?.total) || 0));
    out.donateurs = Number(tot?.n) || 0;

    // Dons par semaine : la semaine en cours est la dernière barre.
    const now = Date.now();
    const sums = new Array(nombre).fill(0);
    const rows = await db.prepare(
      "SELECT amount, created_at FROM donations WHERE julianday(created_at) >= julianday('now', ?)"
    ).bind(`-${nombre * 7} days`).all();
    for (const r of rows?.results || []) {
      const t = Date.parse(String(r.created_at || '').replace(' ', 'T') + (/[zZ]|[+-]\d\d:?\d\d$/.test(String(r.created_at)) ? '' : 'Z'));
      if (!Number.isFinite(t)) continue;
      const age = Math.floor((now - t) / WEEK);
      if (age >= 0 && age < nombre) sums[nombre - 1 - age] += Number(r.amount) || 0;
    }
    out.semaines.items = sums.map((v, i) => ({ label: i === nombre - 1 ? 'Cette sem.' : 'S' + (i + 1), montant: Math.round(v) }));

    if (c.derniers.on) {
      const last = await db.prepare(
        'SELECT donor_name, amount, created_at FROM donations ORDER BY julianday(created_at) DESC, id DESC LIMIT ?'
      ).bind(c.derniers.nombre).all();
      out.derniers.items = (last?.results || []).map((r) => ({
        nom: maskName(r.donor_name, c.derniers.nom),
        montant: c.derniers.montant ? Math.round(Number(r.amount) || 0) : null,
        date: String(r.created_at || ''),
      }));
    }
  } catch (e) {
    console.warn('campagne auto fallback:', e && e.message);
  }
  return out;
}
