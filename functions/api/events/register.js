// POST /api/events/register
// Inscription publique sans compte (< 1 min) avec génération de code unique.
import { json, error, readJson } from '../../_lib/http.js';
import { DEFAULT_SETTINGS, cleanEventRegistrationSettings } from '../../_lib/settings.js';

function generateCode() {
  // Génère un code convivial à 4 chiffres : ex. ASC-7429
  const num = Math.floor(1000 + Math.random() * 9000);
  return `ASC-${num}`;
}

export async function onRequestPost({ request, env }) {
  const db = env.DB;
  if (!db) return error(503, 'no_db', 'Base de données non disponible.');

  const body = await readJson(request, 4096);
  if (!body) return error(400, 'invalid_payload', 'Données de formulaire invalides.');

  const name = typeof body.name === 'string' ? body.name.trim() : '';
  const contact = typeof body.contact === 'string' ? body.contact.trim() : '';
  let attendeesCount = typeof body.attendees_count === 'number' ? Math.floor(body.attendees_count) : parseInt(body.attendees_count, 10);
  if (isNaN(attendeesCount) || attendeesCount < 1) attendeesCount = 1;
  const isVegetarian = Boolean(body.is_vegetarian);
  const notes = typeof body.notes === 'string' ? body.notes.trim().slice(0, 300) : '';

  if (!name || name.length < 2) {
    return error(400, 'missing_name', 'Veuillez indiquer votre nom.');
  }
  if (!contact || contact.length < 5) {
    return error(400, 'missing_contact', 'Veuillez indiquer un courriel ou un numéro de téléphone.');
  }

  // 1. Lire la configuration de l'événement
  let settings = DEFAULT_SETTINGS.event_registration;
  try {
    const row = await db.prepare('SELECT value FROM site_settings WHERE key = ?').bind('event_registration').first();
    if (row && row.value) {
      settings = cleanEventRegistrationSettings(JSON.parse(row.value));
    }
  } catch (err) {
    console.warn('read event_registration error:', err && err.message);
  }

  // 2. Vérifier si les inscriptions sont ouvertes
  if (!settings.is_open) {
    return error(400, 'registrations_closed', 'Les inscriptions pour cet événement sont actuellement fermées.');
  }

  if (settings.deadline) {
    const today = new Date().toISOString().slice(0, 10);
    if (today > settings.deadline) {
      return error(400, 'registration_deadline_passed', 'La date limite d’inscription pour cet événement est passée.');
    }
  }

  if (attendeesCount > settings.max_per_reg) {
    return error(400, 'max_attendees_exceeded', `Le nombre maximum de personnes par inscription est de ${settings.max_per_reg}.`);
  }

  // 3. Vérifier les places restantes
  let reservedSeats = 0;
  try {
    const resRow = await db.prepare(`
      SELECT COALESCE(SUM(attendees_count), 0) as reserved
      FROM event_registrations
      WHERE event_slug = ? AND status = 'confirmed'
    `).bind(settings.event_slug).first();
    if (resRow) reservedSeats = Number(resRow.reserved) || 0;
  } catch (err) {
    console.warn('reserved seats check error:', err && err.message);
  }

  const remaining = Math.max(0, settings.total_seats - reservedSeats);
  if (remaining <= 0) {
    return error(400, 'event_full', 'Désolé, toutes les places pour cet événement sont déjà réservées.');
  }
  if (attendeesCount > remaining) {
    return error(400, 'insufficient_seats', `Il ne reste que ${remaining} place(s) disponible(s).`);
  }

  // 4. Générer un code unique (avec essai anti-collision)
  let code = generateCode();
  let inserted = false;
  let attempts = 0;

  while (!inserted && attempts < 5) {
    attempts++;
    try {
      await db.prepare(`
        INSERT INTO event_registrations (
          event_slug, event_title, code, name, contact, attendees_count, is_vegetarian, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed', ?)
      `).bind(
        settings.event_slug,
        settings.event_title,
        code,
        name.slice(0, 100),
        contact.slice(0, 100),
        attendeesCount,
        isVegetarian ? 1 : 0,
        notes || null
      ).run();
      inserted = true;
    } catch (err) {
      if (String(err && err.message).includes('UNIQUE')) {
        code = generateCode();
      } else {
        console.error('insert registration error:', err);
        return error(500, 'db_error', 'Impossible d’enregistrer l’inscription.');
      }
    }
  }

  if (!inserted) {
    return error(500, 'code_error', 'Erreur lors de la génération du code de réservation. Veuillez réessayer.');
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
