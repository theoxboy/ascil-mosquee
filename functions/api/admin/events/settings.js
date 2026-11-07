// GET & PUT /api/admin/events/settings
// Configuration de l'événement et de la jauge (titre, dates, places, options).
import { requireRole } from '../../../_lib/guard.js';
import { json, error, readJson } from '../../../_lib/http.js';
import { audit } from '../../../_lib/auth.js';
import { cleanEventRegistrationSettings, nowIso, readEventRegistrationSettings } from '../../../_lib/settings.js';

export async function onRequestGet({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'events', 'editor']);
  if (response) return response;

  const db = env.DB;
  if (!db) return error(503, 'no_db', 'Base de données non disponible.');

  const settings = await readEventRegistrationSettings(db);

  // Synthèse des inscriptions actuelles
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
  } catch {}

  return json({
    ok: true,
    settings,
    stats: {
      reserved_seats: reservedSeats,
      total_seats: settings.total_seats,
      remaining_seats: Math.max(0, settings.total_seats - reservedSeats),
      registrations_count: registrationsCount,
      vegetarian_count: vegetarianCount,
    },
  });
}

export async function onRequestPut({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'events']);
  if (response) return response;

  const db = env.DB;
  if (!db) return error(503, 'no_db', 'Base de données non disponible.');

  const body = await readJson(request, 8192);
  if (!body) return error(400, 'invalid_payload', 'Données JSON invalides.');

  const cleaned = cleanEventRegistrationSettings(body);
  const jsonStr = JSON.stringify(cleaned);
  try {
    await db.prepare(`
      INSERT INTO site_settings (key, value, updated_at, updated_by)
      VALUES (?, ?, ?, ?)
      ON CONFLICT(key) DO UPDATE SET
        value = excluded.value, updated_at = excluded.updated_at, updated_by = excluded.updated_by
    `).bind('event_registration', jsonStr, nowIso(), admin.id).run();

    await audit(db, admin.id, 'events.settings_update', request, 'settings:event_registration', {
      event_title: cleaned.event_title,
      total_seats: cleaned.total_seats,
      is_open: cleaned.is_open,
    });
  } catch (err) {
    console.error('save event settings error:', err);
    return error(500, 'db_error', 'Échec de la sauvegarde des paramètres.');
  }

  return json({ ok: true, settings: cleaned });
}
