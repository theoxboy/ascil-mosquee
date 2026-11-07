// POST /api/auth/logout
import { audit, clearCookie, currentAdmin, destroySession } from '../../_lib/auth.js';
import { json } from '../../_lib/http.js';

export async function onRequestPost({ request, env }) {
  const admin = await currentAdmin(env.DB, request);
  await destroySession(env.DB, request);
  if (admin) await audit(env.DB, admin.id, 'auth.logout', request);
  return json({ ok: true }, 200, { 'Set-Cookie': clearCookie() });
}
