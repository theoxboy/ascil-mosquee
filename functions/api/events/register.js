// POST /api/events/register
// Inscription publique sans compte (< 1 min) avec code de réservation unique.
//  - limite : 5 inscriptions par IP en 15 minutes (table rate_limits, migration 0006) ;
//  - code « ASC- » + deux groupes de 4 caractères : 8 caractères tirés par crypto.getRandomValues (31^8 ≈ 850 milliards) ;
//  - places vérifiées et réservées en UNE requête SQL (INSERT … SELECT … WHERE), donc atomique :
//    deux inscriptions simultanées ne peuvent pas dépasser la jauge.
import { json, error, readJson } from '../../_lib/http.js';
import { clientIp } from '../../_lib/auth.js';
import { readEventRegistrationSettings } from '../../_lib/settings.js';

const LIMIT = 5;
const WINDOW_MS = 15 * 60 * 1000;
const ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; // sans 0/O, 1/I/L

function generateCode() {
  const limit = 256 - (256 % ALPHABET.length); // rejet : pas de biais du modulo
  const chars = [];
  while (chars.length < 8) {
    for (const b of crypto.getRandomValues(new Uint8Array(16))) {
      if (b < limit && chars.length < 8) chars.push(ALPHABET[b % ALPHABET.length]);
    }
  }
  return `ASC-${chars.slice(0, 4).join('')}-${chars.slice(4).join('')}`;
}

// Renvoie true si cette IP a déjà fait LIMIT essais dans la fenêtre. Si la table n'existe pas
// encore (migration 0006 non appliquée), on laisse passer plutôt que de bloquer les inscriptions.
async function rateLimited(db, ip) {
  if (!ip) return false;
  const now = Date.now();
  try {
    const row = await db.prepare('SELECT COUNT(*) AS n FROM rate_limits WHERE bucket = ? AND ip = ? AND at > ?')
      .bind('events.register', ip, now - WINDOW_MS).first();
    if ((row?.n || 0) >= LIMIT) return true;
    await db.batch([
      db.prepare('INSERT INTO rate_limits (bucket, ip, at) VALUES (?, ?, ?)').bind('events.register', ip, now),
      db.prepare('DELETE FROM rate_limits WHERE at < ?').bind(now - 24 * 60 * 60 * 1000),
    ]);
  } catch (err) {
    console.warn('rate_limits indisponible :', err && err.message);
  }
  return false;
}

async function reservedSeats(db, slug) {
  const row = await db.prepare(`
    SELECT COALESCE(SUM(attendees_count), 0) AS reserved
      FROM event_registrations WHERE event_slug = ? AND status = 'confirmed'
  `).bind(slug).first();
  return Number(row?.reserved) || 0;
}

export async function onRequestPost({ request, env }) {
  const db = env.DB;

  const body = await readJson(request, 4096);
  if (!body) return error(400, 'invalid_payload', 'Le formulaire n’a pas pu être lu. Rechargez la page et réessayez.');

  const name = typeof body.name === 'string' ? body.name.trim() : '';
  const contact = typeof body.contact === 'string' ? body.contact.trim() : '';
  let attendeesCount = typeof body.attendees_count === 'number' ? Math.floor(body.attendees_count) : parseInt(body.attendees_count, 10);
  if (isNaN(attendeesCount) || attendeesCount < 1) attendeesCount = 1;
  const isVegetarian = Boolean(body.is_vegetarian);
  const notes = typeof body.notes === 'string' ? body.notes.trim().slice(0, 300) : '';

  if (!name || name.length < 2) {
    return error(400, 'missing_name', 'Indiquez votre nom (2 caractères minimum).');
  }
  if (!contact || contact.length < 5) {
    return error(400, 'missing_contact', 'Indiquez un courriel ou un numéro de téléphone pour vous joindre.');
  }

  if (await rateLimited(db, clientIp(request))) {
    return error(429, 'too_many', 'Trop d’inscriptions depuis cette connexion. Réessayez dans 15 minutes.', { 'Retry-After': '900' });
  }

  const settings = await readEventRegistrationSettings(db);

  if (!settings.is_open) {
    return error(400, 'registrations_closed', 'Les inscriptions pour cet événement sont fermées.');
  }
  if (settings.deadline) {
    const today = new Date().toISOString().slice(0, 10);
    if (today > settings.deadline) {
      return error(400, 'registration_deadline_passed', 'La date limite d’inscription pour cet événement est passée.');
    }
  }
  if (attendeesCount > settings.max_per_reg) {
    return error(400, 'max_attendees_exceeded', `Une inscription compte au plus ${settings.max_per_reg} personnes. Faites une seconde inscription pour les autres.`);
  }

  // Insertion conditionnelle : la ligne n'est ajoutée que s'il reste assez de places au moment
  // même de l'écriture. Une collision de code (UNIQUE) relance avec un nouveau code.
  for (let attempt = 0; attempt < 10; attempt++) {
    const code = generateCode();
    let result;
    try {
      result = await db.prepare(`
        INSERT INTO event_registrations (
          event_slug, event_title, code, name, contact, attendees_count, is_vegetarian, status, notes
        )
        SELECT ?1, ?2, ?3, ?4, ?5, ?6, ?7, 'confirmed', ?8
         WHERE (SELECT COALESCE(SUM(attendees_count), 0) FROM event_registrations
                 WHERE event_slug = ?1 AND status = 'confirmed') + ?6 <= ?9
      `).bind(
        settings.event_slug, settings.event_title, code,
        name.slice(0, 100), contact.slice(0, 100), attendeesCount,
        isVegetarian ? 1 : 0, notes || null, settings.total_seats
      ).run();
    } catch (err) {
      if (String(err && err.message).includes('UNIQUE')) continue;
      console.error('insert registration error:', err);
      return error(500, 'db_error', 'L’inscription n’a pas pu être enregistrée. Réessayez dans un instant.');
    }

    if (!result?.meta?.changes) {
      const remaining = Math.max(0, settings.total_seats - await reservedSeats(db, settings.event_slug));
      return remaining <= 0
        ? error(400, 'event_full', 'Désolé, toutes les places pour cet événement sont réservées.')
        : error(400, 'insufficient_seats', `Il ne reste que ${remaining} place(s). Réduisez le nombre de personnes et réessayez.`);
    }

    return json({
      ok: true,
      code,
      event_title: settings.event_title,
      date_str: settings.date_str,
      location: settings.location,
      name,
      attendees_count: attendeesCount,
      is_vegetarian: isVegetarian,
      message: 'Votre réservation est confirmée.',
    });
  }

  return error(500, 'code_error', 'Le code de réservation n’a pas pu être créé. Réessayez dans un instant.');
}
