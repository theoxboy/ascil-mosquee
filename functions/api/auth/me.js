// GET /api/auth/me : qui est connecté ?
import { currentAdmin } from '../../_lib/auth.js';
import { error, json } from '../../_lib/http.js';
import { ROLES, homeFor } from '../../_lib/roles.js';

export async function onRequestGet({ request, env }) {
  const admin = await currentAdmin(env.DB, request);
  if (!admin) return error(401, 'unauthenticated', 'Votre session a expiré. Reconnectez-vous.');
  const { sessionId, ...pub } = admin;
  return json({ ok: true, admin: { ...pub, roleLabel: (ROLES[pub.role] || {}).label || pub.role, home: homeFor(pub.role) } });
}
