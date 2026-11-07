// POST /api/auth/password  { current, next }
// Change le mot de passe et ferme toutes les autres sessions de ce compte.
import { audit, currentAdmin, hashPassword, verifyPassword } from '../../_lib/auth.js';
import { error, json, readJson } from '../../_lib/http.js';

export async function onRequestPost({ request, env }) {
  const db = env.DB;
  const admin = await currentAdmin(db, request);
  if (!admin) return error(401, 'unauthenticated', 'Votre session a expiré. Reconnectez-vous.');

  const body = await readJson(request);
  const current = typeof body?.current === 'string' ? body.current : '';
  const next = typeof body?.next === 'string' ? body.next : '';
  if (next.length < 12 || next.length > 256) {
    return error(400, 'weak', 'Le nouveau mot de passe doit contenir au moins 12 caractères. Une courte phrase fonctionne bien.');
  }

  const row = await db.prepare('SELECT password_hash FROM admins WHERE id = ?').bind(admin.id).first();
  if (!(await verifyPassword(current, row?.password_hash))) {
    return error(400, 'wrong_current', 'Le mot de passe actuel est incorrect. Vérifiez-le et réessayez.');
  }

  await db.batch([
    db.prepare('UPDATE admins SET password_hash = ?, password_changed_at = ? WHERE id = ?')
      .bind(await hashPassword(next), new Date().toISOString(), admin.id),
    db.prepare('DELETE FROM admin_sessions WHERE admin_id = ? AND id != ?').bind(admin.id, admin.sessionId),
  ]);
  await audit(db, admin.id, 'auth.password_changed', request);
  return json({ ok: true });
}
