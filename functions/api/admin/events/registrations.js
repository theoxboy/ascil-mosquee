// GET & DELETE /api/admin/events/registrations
// Liste des inscrits, recherche, synthèse et annulation d'une inscription.
import { requireRole } from '../../../_lib/guard.js';
import { json, error, readJson } from '../../../_lib/http.js';
import { audit } from '../../../_lib/auth.js';

export async function onRequestGet({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'events', 'editor']);
  if (response) return response;

  const db = env.DB;
  if (!db) return error(503, 'no_db', 'Base de données non disponible.');

  const url = new URL(request.url);
  const status = url.searchParams.get('status') || 'all';
  const search = (url.searchParams.get('q') || '').trim();

  let query = 'SELECT id, event_slug, event_title, code, name, contact, attendees_count, is_vegetarian, status, notes, created_at FROM event_registrations WHERE 1=1';
  const params = [];

  if (status && status !== 'all') {
    query += ' AND status = ?';
    params.push(status);
  }

  if (search) {
    query += ' AND (name LIKE ? OR contact LIKE ? OR code LIKE ?)';
    const term = `%${search}%`;
    params.push(term, term, term);
  }

  query += ' ORDER BY id DESC LIMIT 500';

  let rows = [];
  try {
    let stmt = db.prepare(query);
    if (params.length > 0) stmt = stmt.bind(...params);
    const res = await stmt.all();
    rows = res?.results || [];
  } catch (err) {
    console.error('get registrations error:', err);
    return error(500, 'db_error', 'Impossible de récupérer la liste des inscrits.');
  }

  // Calcul du résumé global
  let summary = {
    total_registrations: 0,
    total_attendees: 0,
    vegetarian_count: 0,
    cancelled_count: 0,
  };

  try {
    const sumRow = await db.prepare(`
      SELECT
        COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_regs,
        COALESCE(SUM(CASE WHEN status = 'confirmed' THEN attendees_count ELSE 0 END), 0) as confirmed_att,
        COALESCE(SUM(CASE WHEN status = 'confirmed' AND is_vegetarian = 1 THEN attendees_count ELSE 0 END), 0) as veg,
        COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled
      FROM event_registrations
    `).first();

    if (sumRow) {
      summary.total_registrations = Number(sumRow.confirmed_regs) || 0;
      summary.total_attendees = Number(sumRow.confirmed_att) || 0;
      summary.vegetarian_count = Number(sumRow.veg) || 0;
      summary.cancelled_count = Number(sumRow.cancelled) || 0;
    }
  } catch {}

  return json({
    ok: true,
    summary,
    registrations: rows,
  });
}

export async function onRequestDelete({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'events']);
  if (response) return response;

  const db = env.DB;
  if (!db) return error(503, 'no_db', 'Base de données non disponible.');

  const url = new URL(request.url);
  const idStr = url.searchParams.get('id');
  const id = parseInt(idStr, 10);
  if (isNaN(id) || id <= 0) {
    return error(400, 'invalid_id', 'Identifiant d’inscription invalide.');
  }

  try {
    const existing = await db.prepare('SELECT id, code, name, attendees_count FROM event_registrations WHERE id = ?').bind(id).first();
    if (!existing) {
      return error(404, 'not_found', 'Inscription non trouvée.');
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
    return error(500, 'db_error', 'Échec de l’annulation de l’inscription.');
  }
}
