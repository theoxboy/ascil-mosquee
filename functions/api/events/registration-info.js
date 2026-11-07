// GET /api/events/registration-info
// Données publiques pour l'affichage de l'événement et des places disponibles.
import { json, error } from '../../_lib/http.js';
import { readEventRegistrationSettings } from '../../_lib/settings.js';

export async function onRequestGet({ env }) {
  const db = env.DB;
  if (!db) return error(503, 'no_db', 'Base de données non disponible.');

  const settings = await readEventRegistrationSettings(db);

  let reservedSeats = 0;
  let registrationsCount = 0;
  let vegetarianCount = 0;

  try {
    const statRow = await db.prepare(`
      SELECT
        COALESCE(SUM(attendees_count), 0) as reserved,
        COUNT(*) as count,
        COALESCE(SUM(CASE WHEN is_vegetarian = 1 THEN attendees_count ELSE 0 END), 0) as veg
      FROM event_registrations
      WHERE event_slug = ? AND status = 'confirmed'
    `).bind(settings.event_slug).first();

    if (statRow) {
      reservedSeats = Number(statRow.reserved) || 0;
      registrationsCount = Number(statRow.count) || 0;
      vegetarianCount = Number(statRow.veg) || 0;
    }
  } catch (err) {
    console.warn('statRow error:', err && err.message);
  }

  const totalSeats = settings.total_seats || 1;
  const remainingSeats = Math.max(0, totalSeats - reservedSeats);
  const reservedPct = Math.min(100, Math.round((reservedSeats / totalSeats) * 100));

  // Vérification de la date limite
  let isExpired = false;
  if (settings.deadline) {
    const today = new Date().toISOString().slice(0, 10);
    if (today > settings.deadline) {
      isExpired = true;
    }
  }

  const isOpen = Boolean(settings.is_open && !isExpired && remainingSeats > 0);

  return json({
    ok: true,
    event: {
      slug: settings.event_slug,
      title: settings.event_title,
      date_str: settings.date_str,
      location: settings.location,
      description: settings.description,
      total_seats: settings.total_seats,
      reserved_seats: reservedSeats,
      remaining_seats: remainingSeats,
      reserved_pct: reservedPct,
      registrations_count: registrationsCount,
      vegetarian_count: vegetarianCount,
      max_per_reg: settings.max_per_reg,
      deadline: settings.deadline,
      is_open: isOpen,
      is_expired: isExpired,
      is_full: remainingSeats === 0,
      opt_vege: settings.opt_vege,
      opt_code: settings.opt_code,
      opt_agenda: settings.opt_agenda,
    },
  });
}
