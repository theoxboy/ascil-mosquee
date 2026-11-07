// GET  /api/admin/accounts   liste des comptes (superadmin)
// POST /api/admin/accounts   crée un compte à rôle limité ; renvoie son mot de passe provisoire UNE fois
import { audit, hashPassword, tempPassword } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import { PUBLIC_COLS, fix, validate } from '../../../_lib/accounts.js';

export async function onRequestGet({ request, env }) {
  const { response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;
  const { results } = await env.DB.prepare(
    `SELECT ${PUBLIC_COLS} FROM admins WHERE password_hash IS NOT NULL
      ORDER BY CASE role WHEN 'superadmin' THEN 0 ELSE 1 END, is_active DESC, username COLLATE NOCASE`
  ).all();
  return json({ ok: true, accounts: results.map(fix) });
}

export async function onRequestPost({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin']);
  if (response) return response;

  const body = await readJson(request);
  const v = validate(body);
  if (v.error) return error(400, 'invalid', v.error);

  const password = tempPassword();
  const now = new Date().toISOString();
  try {
    await env.DB.prepare(
      `INSERT INTO admins (username, email, display_name, role, password_hash, is_active,
                           must_change_password, created_at, created_by)
       VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)`
    ).bind(v.username, v.email, v.displayName, v.role, await hashPassword(password), now, admin.id).run();
  } catch (e) {
    if (/UNIQUE/i.test(String(e && e.message))) {
      return error(409, 'taken', `L’identifiant « ${v.username} » est déjà pris. Choisissez-en un autre.`);
    }
    throw e;
  }
  const created = await env.DB.prepare(`SELECT ${PUBLIC_COLS} FROM admins WHERE username = ? COLLATE NOCASE`)
    .bind(v.username).first();
  await audit(env.DB, admin.id, 'account.create', request, `admin:${created.id}`, { username: v.username, role: v.role });
  return json({ ok: true, account: fix(created), temporaryPassword: password }, 201);
}
