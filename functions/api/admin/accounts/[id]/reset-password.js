// POST /api/admin/accounts/:id/reset-password   (superadmin)
// Génère un nouveau mot de passe provisoire, ferme les sessions du compte,
// et l'oblige à choisir son propre mot de passe à la prochaine connexion.
import { audit, hashPassword, tempPassword } from '../../../../_lib/auth.js';
import { requireRole } from '../../../../_lib/guard.js';
import { json } from '../../../../_lib/http.js';
import { loadTarget } from '../../../../_lib/accounts.js';

export async function onRequestPost({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const target = await loadTarget(env.DB, params.id);
  if (target.response) return target.response;

  const password = tempPassword();
  await env.DB.batch([
    env.DB.prepare('UPDATE admins SET password_hash = ?, must_change_password = 1, password_changed_at = ? WHERE id = ?')
      .bind(await hashPassword(password), new Date().toISOString(), target.row.id),
    env.DB.prepare('DELETE FROM admin_sessions WHERE admin_id = ?').bind(target.row.id),
  ]);
  await audit(env.DB, admin.id, 'account.reset_password', request, `admin:${target.row.id}`);
  return json({ ok: true, temporaryPassword: password });
}
