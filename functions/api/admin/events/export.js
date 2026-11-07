// GET /api/admin/events/export
// Exporte la liste des inscriptions en CSV compatible Excel / Google Sheets avec accents UTF-8.
import { requireRole } from '../../../_lib/guard.js';
import { error } from '../../../_lib/http.js';

function escapeCsv(val) {
  if (val == null) return '""';
  const str = String(val).replace(/"/g, '""');
  return `"${str}"`;
}

export async function onRequestGet({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'events', 'editor']);
  if (response) return response;

  const db = env.DB;
  if (!db) return error(503, 'no_db', 'Base de données non disponible.');

  try {
    const res = await db.prepare(`
      SELECT id, event_title, code, name, contact, attendees_count, is_vegetarian, status, notes, created_at
      FROM event_registrations
      ORDER BY id DESC
    `).all();

    const rows = res?.results || [];

    const headers = [
      'Date d\'inscription',
      'Code',
      'Événement',
      'Nom',
      'Contact',
      'Nombre de places',
      'Repas végétarien',
      'Statut',
      'Notes'
    ];

    const lines = [headers.map(escapeCsv).join(';')];

    for (const r of rows) {
      lines.push([
        escapeCsv(r.created_at || ''),
        escapeCsv(r.code || ''),
        escapeCsv(r.event_title || ''),
        escapeCsv(r.name || ''),
        escapeCsv(r.contact || ''),
        escapeCsv(r.attendees_count || 1),
        escapeCsv(r.is_vegetarian ? 'Oui' : 'Non'),
        escapeCsv(r.status === 'confirmed' ? 'Confirmé' : 'Annulé'),
        escapeCsv(r.notes || '')
      ].join(';'));
    }

    // Préfixe BOM UTF-8 (\uFEFF) pour qu'Excel ouvre le fichier avec les bons caractères
    const csvContent = '\uFEFF' + lines.join('\r\n');
    const today = new Date().toISOString().slice(0, 10);
    const filename = `inscrits-evenements-${today}.csv`;

    return new Response(csvContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Cache-Control': 'no-store, no-cache',
      },
    });
  } catch (err) {
    console.error('export csv error:', err);
    return error(500, 'db_error', 'Échec de la génération de l’export CSV.');
  }
}
