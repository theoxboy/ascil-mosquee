// GET    /api/auth/sessions   sessions ouvertes du compte connecté (la session actuelle est signalée)
// DELETE /api/auth/sessions   ferme toutes les AUTRES sessions de ce compte
import { audit } from '../../_lib/auth.js';
import { requireRole } from '../../_lib/guard.js';
import { json } from '../../_lib/http.js';

export async function onRequestGet({ request, env }) {
  const { admin, response } = await requireRole(env, request, null);
  if (response) return response;
  const { results } = await env.DB.prepare(
    `SELECT id, created_at, last_seen_at, expires_at, user_agent
       FROM admin_sessions WHERE admin_id = ? AND expires_at > ?
      ORDER BY last_seen_at DESC LIMIT 20`
  ).bind(admin.id, Date.now()).all();
  return json({
    ok: true,
    sessions: results.map((s) => ({
      current: s.id === admin.sessionId,
      createdAt: new Date(s.created_at).toISOString(),
      lastSeenAt: new Date(s.last_seen_at).toISOString(),
      expiresAt: new Date(s.expires_at).toISOString(),
      userAgent: s.user_agent || '',
    })),
  });
}

export async function onRequestDelete({ request, env }) {
  const { admin, response } = await requireRole(env, request, null);
  if (response) return response;
  const res = await env.DB.prepare('DELETE FROM admin_sessions WHERE admin_id = ? AND id != ?')
    .bind(admin.id, admin.sessionId).run();
  const closed = res?.meta?.changes || 0;
  await audit(env.DB, admin.id, 'auth.sessions_revoked', request, null, { closed });
  return json({ ok: true, closed });
}
