// POST /api/auth/login  { username, password, remember }
import { audit, clientIp, createSession, recordAttempt, tooManyAttempts, verifyPassword } from '../../_lib/auth.js';
import { error, json, readJson } from '../../_lib/http.js';

export async function onRequestPost({ request, env }) {
  const body = await readJson(request);
  const username = typeof body?.username === 'string' ? body.username.trim().slice(0, 64) : '';
  const password = typeof body?.password === 'string' ? body.password : '';
  if (!username || !password) {
    return error(400, 'missing', 'Entrez votre identifiant et votre mot de passe.');
  }
  if (password.length > 256) return error(400, 'invalid', 'Identifiant ou mot de passe incorrect.');

  const db = env.DB;
  const ip = clientIp(request);
  if (await tooManyAttempts(db, ip, username)) {
    return error(429, 'locked', 'Trop de tentatives. Pour protéger le compte, réessayez dans 15 minutes.', { 'Retry-After': '900' });
  }

  const admin = await db.prepare(
    'SELECT id, username, role, display_name, password_hash, is_active FROM admins WHERE username = ? COLLATE NOCASE AND password_hash IS NOT NULL'
  ).bind(username).first();
  const ok = await verifyPassword(password, admin?.password_hash);
  if (!ok || !admin.is_active) {
    await recordAttempt(db, ip, username, false);
    await audit(db, admin?.id ?? null, 'auth.login_failed', request, null, { username });
    return error(401, 'invalid', 'Identifiant ou mot de passe incorrect. Vérifiez les majuscules et réessayez.');
  }

  await recordAttempt(db, ip, username, true);
  const setCookie = await createSession(db, admin.id, request, body.remember === true);
  await db.prepare('UPDATE admins SET last_login_at = ? WHERE id = ?').bind(new Date().toISOString(), admin.id).run();
  await audit(db, admin.id, 'auth.login', request);

  return json({ ok: true, admin: { username: admin.username, role: admin.role, displayName: admin.display_name } }, 200,
    { 'Set-Cookie': setCookie });
}
