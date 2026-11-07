// GET & DELETE /api/admin/events/registrations
// Inscrits de l'événement en cours (event_slug des réglages), recherche, synthèse et annulation.
// Les noms et contacts ne sont visibles que du superadmin et du responsable événements ;
// l'éditeur ne reçoit que la synthèse chiffrée.
import { requireRole } from '../../../_lib/guard.js';
import { json, error } from '../../../_lib/http.js';
import { audit } from '../../../_lib/auth.js';
import { readEventRegistrationSettings } from '../../../_lib/settings.js';

const NOMINATIVE_ROLES = ['superadmin', 'events'];

export async function onRequestGet({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'events', 'editor']);
  if (response) return response;

  const db = env.DB;
  const settings = await readEventRegistrationSettings(db);
  const slug = settings.event_slug;

  // Synthèse : uniquement l'événement en cours, comme registration-info et events/settings.
  const summary = { event_slug: slug, total_registrations: 0, total_attendees: 0, vegetarian_count: 0, cancelled_count: 0 };
  try {
    const sumRow = await db.prepare(`
      SELECT
        COUNT(CASE WHEN status = 'confirmed' THEN 1 END) AS confirmed_regs,
        COALESCE(SUM(CASE WHEN status = 'confirmed' THEN attendees_count ELSE 0 END), 0) AS confirmed_att,
        COALESCE(SUM(CASE WHEN status = 'confirmed' AND is_vegetarian = 1 THEN attendees_count ELSE 0 END), 0) AS veg,
        COUNT(CASE WHEN status = 'cancelled' THEN 1 END) AS cancelled
      FROM event_registrations
      WHERE event_slug = ?
    `).bind(slug).first();
    if (sumRow) {
      summary.total_registrations = Number(sumRow.confirmed_regs) || 0;
      summary.total_attendees = Number(sumRow.confirmed_att) || 0;
      summary.vegetarian_count = Number(sumRow.veg) || 0;
      summary.cancelled_count = Number(sumRow.cancelled) || 0;
    }
  } catch (err) {
    console.warn('registrations summary error:', err && err.message);
  }

  if (!NOMINATIVE_ROLES.includes(admin.role)) {
    return json({
      ok: true,
      summary,
      registrations: [],
      restricted: true,
      message: 'La liste nominative des inscrits est réservée au superadmin et au responsable des événements.',
    });
  }

  const url = new URL(request.url);
  const status = url.searchParams.get('status') || 'all';
  const search = (url.searchParams.get('q') || '').trim().slice(0, 100);

  let query = `SELECT id, event_slug, event_title, code, name, contact, attendees_count, is_vegetarian, status, notes, created_at
                 FROM event_registrations WHERE event_slug = ?`;
  const params = [slug];
  if (status === 'confirmed' || status === 'cancelled') {
    query += ' AND status = ?';
    params.push(status);
  }
  if (search) {
    query += ' AND (name LIKE ? OR contact LIKE ? OR code LIKE ?)';
    const term = `%${search}%`;
    params.push(term, term, term);
  }
  query += ' ORDER BY id DESC LIMIT 500';

  try {
    const res = await db.prepare(query).bind(...params).all();
    return json({ ok: true, summary, registrations: res?.results || [] });
  } catch (err) {
    console.error('get registrations error:', err);
    return error(500, 'db_error', 'Impossible de récupérer la liste des inscrits. Réessayez dans un instant.');
  }
}

export async function onRequestDelete({ request, env }) {
  const { admin, response } = await requireRole(env, request, NOMINATIVE_ROLES);
  if (response) return response;

  const db = env.DB;
  const id = parseInt(new URL(request.url).searchParams.get('id'), 10);
  if (isNaN(id) || id <= 0) {
    return error(400, 'invalid_id', 'Identifiant d’inscription invalide.');
  }

  try {
    const existing = await db.prepare('SELECT id, code, name, attendees_count FROM event_registrations WHERE id = ?').bind(id).first();
    if (!existing) {
      return error(404, 'not_found', 'Inscription non trouvée. Elle a peut-être déjà été supprimée.');
    }

    await db.prepare("UPDATE event_registrations SET status = 'cancelled' WHERE id = ?").bind(id).run();

    await audit(db, admin.id, 'events.registration_cancel', request, `registration:${id}`, {
      code: existing.code,
      name: existing.name,
      attendees_count: existing.attendees_count,
    });

    return json({ ok: true, cancelled_id: id });
  } catch (err) {
    console.error('cancel registration error:', err);
    return error(500, 'db_error', 'Échec de l’annulation de l’inscription. Réessayez dans un instant.');
  }
}
