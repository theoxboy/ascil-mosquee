// PATCH /api/admin/accounts/:id   { role?, displayName?, email?, isActive? }   (superadmin)
// Le compte superadmin ne se modifie pas par cette route.
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import { PUBLIC_COLS, fix, loadTarget, validate } from '../../../_lib/accounts.js';

export async function onRequestPatch({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;

  const target = await loadTarget(env.DB, params.id);
  if (target.response) return target.response;

  const body = await readJson(request);
  if (!body) return error(400, 'invalid', 'Requête illisible. Rechargez la page et réessayez.');
  const v = validate({ role: body.role, email: body.email, displayName: body.displayName }, true);
  if (v.error) return error(400, 'invalid', v.error);

  const sets = [], binds = [], changes = {};
  if (v.role !== undefined) { sets.push('role = ?'); binds.push(v.role); changes.role = v.role; }
  if (v.email !== undefined) { sets.push('email = ?'); binds.push(v.email); changes.email = v.email; }
  if (v.displayName !== undefined) { sets.push('display_name = ?'); binds.push(v.displayName); changes.displayName = v.displayName; }
  if (body.isActive !== undefined) {
    if (typeof body.isActive !== 'boolean') return error(400, 'invalid', 'Valeur d’activation invalide.');
    sets.push('is_active = ?'); binds.push(body.isActive ? 1 : 0); changes.isActive = body.isActive;
  }
  if (!sets.length) return error(400, 'invalid', 'Aucune modification à enregistrer.');

  const stmts = [env.DB.prepare(`UPDATE admins SET ${sets.join(', ')} WHERE id = ?`).bind(...binds, target.row.id)];
  // Un compte désactivé est déconnecté immédiatement.
  if (changes.isActive === false) stmts.push(env.DB.prepare('DELETE FROM admin_sessions WHERE admin_id = ?').bind(target.row.id));
  await env.DB.batch(stmts);

  await audit(env.DB, admin.id, 'account.update', request, `admin:${target.row.id}`, changes);
  const row = await env.DB.prepare(
`SELECT ${PUBLIC_COLS} FROM admins WHERE id = ?`).bind(target.row.id).first();
  return json({ ok: true, account: fix(row) });
}
