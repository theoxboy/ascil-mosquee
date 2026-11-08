// Mur « Dua et annonces » (table dua_messages, migration 0010 ; règles dans la clé dua).
import { DEFAULT_SETTINGS, cleanDuaSettings } from './settings.js';

export const DUA_TYPES = ['dua', 'ann'];
export const DUA_STATUSES = ['attente', 'publie', 'refuse'];
export const MIN_FILL_MS = 3000;
export const NO_TABLE = 'Le mur Dua et annonces n’est pas encore installé : appliquez la migration 0010 dans la console D1.';

const oneLine = (v, max) => (typeof v === 'string' ? v.replace(/[\u0000-\u001f\u007f]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max) : '');
const multiLine = (v, max) => (typeof v === 'string'
  ? v.replace(/\r\n?/g, '\n').replace(/[\u0000-\u0009\u000b-\u001f\u007f]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim().slice(0, max)
  : '');

export async function readDuaSettings(db) {
  try {
    const row = await db.prepare("SELECT value FROM site_settings WHERE key = 'dua'").first();
    if (row && row.value) return cleanDuaSettings(JSON.parse(row.value));
  } catch (e) {
    console.warn('dua settings read fallback:', e && e.message);
  }
  return cleanDuaSettings(DEFAULT_SETTINGS.dua);
}

export const categoriesOf = (rules) => rules.categories.filter((c) => c.on && c.titre).map((c) => c.titre);

// Vérifie un message envoyé depuis le mur (ou corrigé dans le panneau). Renvoie { value } ou { code, message }.
export function cleanDuaMessage(body, rules, { admin = false } = {}) {
  const type = DUA_TYPES.includes(body.type) ? body.type : '';
  if (!type || (!admin && type === 'dua' && !rules.ongletDua) || (!admin && type === 'ann' && !rules.ongletAnn)) {
    return { code: 'invalid_type', message: 'Ce type de message n’est pas accepté sur le mur. Rechargez la page et réessayez.' };
  }
  const texte = multiLine(body.texte, rules.max);
  if (texte.length < 5) return { code: 'missing_text', message: 'Écrivez votre message (5 caractères minimum).' };
  let signature = oneLine(body.signature, 60);
  if (!signature) {
    if (!rules.anonyme && !admin) return { code: 'missing_signature', message: 'Signez votre message avec votre prénom ou vos initiales.' };
    signature = 'Anonyme';
  }
  if (!admin && !rules.anonyme && /^anonyme$/i.test(signature)) {
    return { code: 'missing_signature', message: 'Le mur ne permet pas la signature « Anonyme ». Signez avec votre prénom ou vos initiales.' };
  }
  let categorie = null;
  if (type === 'ann') {
    const cats = categoriesOf(rules);
    categorie = oneLine(body.categorie, 30);
    if (!admin && cats.length && !cats.includes(categorie)) return { code: 'missing_category', message: 'Choisissez une catégorie pour votre annonce.' };
    if (!categorie) categorie = null;
  }
  return { value: { type, texte, signature, categorie } };
}

// Limite d'essais par connexion (table rate_limits, migration 0006). Renvoie true si la limite est atteinte.
export async function limited(db, bucket, ip, limit, windowMs) {
  if (!ip) return false;
  const now = Date.now();
  try {
    const row = await db.prepare('SELECT COUNT(*) AS n FROM rate_limits WHERE bucket = ? AND ip = ? AND at > ?').bind(bucket, ip, now - windowMs).first();
    if ((row?.n || 0) >= limit) return true;
    await db.batch([
      db.prepare('INSERT INTO rate_limits (bucket, ip, at) VALUES (?, ?, ?)').bind(bucket, ip, now),
      db.prepare('DELETE FROM rate_limits WHERE at < ?').bind(now - 24 * 60 * 60 * 1000),
    ]);
  } catch (err) {
    console.warn('rate_limits indisponible :', err && err.message);
  }
  return false;
}

export const noTable = (err) => /no such table/i.test(String(err && err.message));
