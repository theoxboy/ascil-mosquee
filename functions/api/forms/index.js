// POST /api/forms
// Envoi d'un formulaire public (Contact, et plus tard les formulaires des services) vers la boîte
// de réception du panneau. Protection anti-robot sans casse-tête :
//  - champ piège invisible (hp) : rempli → réponse « envoyé » mais rien n'est enregistré ;
//  - délai minimal entre l'affichage du formulaire et l'envoi (t, en ms) ;
//  - au plus 5 envois par connexion en 15 minutes (table rate_limits, migration 0006) ;
//  - le middleware refuse déjà les envois qui ne viennent pas du site lui-même.
import { json, error, readJson } from '../../_lib/http.js';
import { clientIp } from '../../_lib/auth.js';
import { cleanFormMessage, MIN_FILL_MS, LIMIT, WINDOW_MS } from '../../_lib/forms.js';
import { DEFAULT_SETTINGS, cleanContactSettings } from '../../_lib/settings.js';

const BUCKET = 'forms.send';

async function rateLimited(db, ip) {
  if (!ip) return false;
  const now = Date.now();
  try {
    const row = await db.prepare('SELECT COUNT(*) AS n FROM rate_limits WHERE bucket = ? AND ip = ? AND at > ?')
      .bind(BUCKET, ip, now - WINDOW_MS).first();
    if ((row?.n || 0) >= LIMIT) return true;
    await db.batch([
      db.prepare('INSERT INTO rate_limits (bucket, ip, at) VALUES (?, ?, ?)').bind(BUCKET, ip, now),
      db.prepare('DELETE FROM rate_limits WHERE at < ?').bind(now - 24 * 60 * 60 * 1000),
    ]);
  } catch (err) {
    console.warn('rate_limits indisponible :', err && err.message);
  }
  return false;
}

export async function onRequestPost({ request, env }) {
  const body = await readJson(request, 16 * 1024);
  if (!body || typeof body !== 'object') {
    return error(400, 'invalid_payload', 'Le formulaire n’a pas pu être lu. Rechargez la page et réessayez.');
  }

  // Champ piège rempli : c'est un robot. On ne lui dit rien.
  if (typeof body.hp === 'string' && body.hp.trim()) return json({ ok: true });

  const elapsed = Number(body.t);
  if (!Number.isFinite(elapsed) || elapsed < MIN_FILL_MS) {
    return error(400, 'too_fast', 'Envoi trop rapide. Relisez votre message, puis envoyez-le à nouveau.');
  }

  const checked = cleanFormMessage(body);
  if (!checked.value) return error(400, checked.code, checked.message);
  const v = checked.value;

  // Formulaire Contact : longueur maximale et sujets réglés dans le panneau (Contact → Page Contact).
  if (v.source === 'contact') {
    let co = null;
    try {
      const row = await env.DB.prepare("SELECT value FROM site_settings WHERE key = 'contact'").first();
      if (row && row.value) co = JSON.parse(row.value);
    } catch (err) {
      console.warn('contact settings read fallback:', err && err.message);
    }
    co = cleanContactSettings(co || DEFAULT_SETTINGS.contact);
    const max = co.form.max;
    if (v.message.length > max) {
      return error(400, 'too_long', `Votre message dépasse ${max} caractères. Raccourcissez-le, puis envoyez-le à nouveau.`);
    }
    const sujets = co.form.sujets.filter((x) => x.on && x.titre).map((x) => x.titre);
    if (v.sujet && sujets.length && !sujets.includes(v.sujet)) v.sujet = '';
  }

  if (await rateLimited(env.DB, clientIp(request))) {
    return error(429, 'too_many', 'Trop de messages envoyés depuis cette connexion. Réessayez dans 15 minutes.', { 'Retry-After': '900' });
  }

  try {
    await env.DB.prepare(
      'INSERT INTO form_messages (source, sujet, nom, contact, message, details) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(v.source, v.sujet || null, v.nom, v.contact, v.message, v.details ? JSON.stringify(v.details) : null).run();
  } catch (err) {
    console.error('form_messages insert error:', err && err.message);
    return error(500, 'db_error', 'Votre message n’a pas pu être enregistré. Réessayez dans un instant.');
  }
  return json({ ok: true, message: 'Votre message est bien arrivé à l’association.' });
}
