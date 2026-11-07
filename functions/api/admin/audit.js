// GET /api/admin/audit?limit=20   journal des modifications (superadmin uniquement)
// Alimente « Site entier → Compte et sécurité → Journal des modifications ».
import { requireRole } from '../../_lib/guard.js';
import { json } from '../../_lib/http.js';

export async function onRequestGet({ request, env }) {
  const { response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const limit = Math.min(100, Math.max(1, parseInt(new URL(request.url).searchParams.get('limit'), 10) || 20));
  const { results } = await env.DB.prepare(
    `SELECT l.id, l.action, l.target, l.details, l.created_at AS createdAt,
            COALESCE(a.username, '—') AS username
       FROM audit_log l LEFT JOIN admins a ON a.id = l.admin_id
      ORDER BY l.id DESC LIMIT ?`
  ).bind(limit).all();
  return json({
    ok: true,
    entries: results.map((r) => {
      let details = null;
      try { details = r.details ? JSON.parse(r.details) : null; } catch { details = null; }
      return { ...r, details };
    }),
  });
}
