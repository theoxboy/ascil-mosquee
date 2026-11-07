// Authentification du superadmin : mots de passe, sessions, cookies, limitation des essais.
// Aucune dépendance : tout passe par WebCrypto, disponible dans les Workers.

export const COOKIE = '__Host-ascil_sa';
const SESSION_MS = 12 * 60 * 60 * 1000;          // 12 h
const REMEMBER_MS = 30 * 24 * 60 * 60 * 1000;    // 30 jours (« Rester connecté »)
const PBKDF2_ITER = 100000;                       // maximum accepté par les Workers
const WINDOW_MS = 15 * 60 * 1000;
const MAX_FAILS = 5;

const enc = new TextEncoder();
const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)));
const unb64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');

async function pbkdf2(password, salt, iter) {
  const key = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
  return crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations: iter }, key, 256);
}

export async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const dk = await pbkdf2(password, salt, PBKDF2_ITER);
  return `pbkdf2_sha256$${PBKDF2_ITER}$${b64(salt)}$${b64(dk)}`;
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a[i] ^ b[i];
  return r === 0;
}

// Empreinte factice : un identifiant inconnu coûte le même temps qu'un vrai.
const DUMMY = 'pbkdf2_sha256$100000$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=';

export async function verifyPassword(password, stored) {
  const parts = String(stored || DUMMY).split('$');
  if (parts.length !== 4 || parts[0] !== 'pbkdf2_sha256') return false;
  const iter = Number(parts[1]);
  if (!Number.isInteger(iter) || iter < 10000 || iter > PBKDF2_ITER) return false;
  const dk = new Uint8Array(await pbkdf2(password, unb64(parts[2]), iter));
  return stored ? timingSafeEqual(dk, unb64(parts[3])) : false;
}

export async function sha256Hex(s) {
  return hex(await crypto.subtle.digest('SHA-256', enc.encode(s)));
}

export function clientIp(request) {
  return request.headers.get('CF-Connecting-IP') || request.headers.get('X-Forwarded-For') || '';
}

export function readCookie(request, name = COOKIE) {
  const raw = request.headers.get('Cookie') || '';
  for (const part of raw.split(';')) {
    const i = part.indexOf('=');
    if (i > -1 && part.slice(0, i).trim() === name) return part.slice(i + 1).trim();
  }
  return null;
}

function cookie(value, maxAgeSec) {
  const base = `${COOKIE}=${value}; Path=/; HttpOnly; Secure; SameSite=Strict`;
  return maxAgeSec === undefined ? base : `${base}; Max-Age=${maxAgeSec}`;
}
export const clearCookie = () => cookie('', 0);

export async function createSession(db, adminId, request, remember) {
  const token = b64(crypto.getRandomValues(new Uint8Array(32))).replace(/[+/=]/g, (c) => ({ '+': '-', '/': '_', '=': '' })[c]);
  const now = Date.now();
  const ttl = remember ? REMEMBER_MS : SESSION_MS;
  await db.prepare(
    'INSERT INTO admin_sessions (id, admin_id, created_at, expires_at, last_seen_at, ip, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(await sha256Hex(token), adminId, now, now + ttl, now, clientIp(request),
    (request.headers.get('User-Agent') || '').slice(0, 300)).run();
  // Sans « Rester connecté », cookie de session (effacé à la fermeture du navigateur).
  return cookie(token, remember ? Math.floor(ttl / 1000) : undefined);
}

// Renvoie l'administrateur connecté, ou null.
export async function currentAdmin(db, request) {
  const token = readCookie(request);
  if (!token || token.length > 100) return null;
  const id = await sha256Hex(token);
  const now = Date.now();
  const row = await db.prepare(
    `SELECT s.id AS sid, s.last_seen_at, a.id, a.username, a.email, a.role, a.display_name, a.must_change_password
       FROM admin_sessions s JOIN admins a ON a.id = s.admin_id
      WHERE s.id = ? AND s.expires_at > ? AND a.is_active = 1`
  ).bind(id, now).first();
  if (!row) return null;
  if (now - row.last_seen_at > 5 * 60 * 1000) {
    await db.prepare('UPDATE admin_sessions SET last_seen_at = ? WHERE id = ?').bind(now, id).run();
  }
  return { id: row.id, username: row.username, email: row.email || null, role: row.role, displayName: row.display_name,
    mustChangePassword: row.must_change_password === 1, sessionId: row.sid };
}

export async function destroySession(db, request) {
  const token = readCookie(request);
  if (token) await db.prepare('DELETE FROM admin_sessions WHERE id = ?').bind(await sha256Hex(token)).run();
}

export async function tooManyAttempts(db, ip, username) {
  const since = Date.now() - WINDOW_MS;
  const r = await db.prepare(
    `SELECT
       SUM(CASE WHEN ip = ?1 THEN 1 ELSE 0 END) AS by_ip,
       SUM(CASE WHEN username = ?2 THEN 1 ELSE 0 END) AS by_user
     FROM login_attempts WHERE success = 0 AND attempted_at > ?3 AND (ip = ?1 OR username = ?2)`
  ).bind(ip, username, since).first();
  return (r?.by_ip || 0) >= MAX_FAILS || (r?.by_user || 0) >= MAX_FAILS;
}

export async function recordAttempt(db, ip, username, success) {
  const now = Date.now();
  await db.batch([
    db.prepare('INSERT INTO login_attempts (ip, username, success, attempted_at) VALUES (?, ?, ?, ?)').bind(ip, username, success ? 1 : 0, now),
    // Ménage : on ne garde qu'une journée d'historique, et pas les sessions expirées.
    db.prepare('DELETE FROM login_attempts WHERE attempted_at < ?').bind(now - 24 * 60 * 60 * 1000),
    db.prepare('DELETE FROM admin_sessions WHERE expires_at < ?').bind(now),
  ]);
}

// Mot de passe provisoire lisible à l'oral : 4 groupes de 4, sans caractères ambigus (0/O, 1/l/I).
export function tempPassword() {
  const alphabet = 'abcdefghjkmnpqrstuvwxyz23456789';
  const limit = 256 - (256 % alphabet.length); // rejet pour éviter le biais du modulo
  const chars = [];
  while (chars.length < 16) {
    for (const b of crypto.getRandomValues(new Uint8Array(32))) {
      if (b < limit && chars.length < 16) chars.push(alphabet[b % alphabet.length]);
    }
  }
  return chars.join('').match(/.{4}/g).join('-');
}

export async function audit(db, adminId, action, request, target = null, details = null) {
  await db.prepare('INSERT INTO audit_log (admin_id, action, target, details, ip) VALUES (?, ?, ?, ?, ?)')
    .bind(adminId, action, target, details ? JSON.stringify(details) : null, clientIp(request)).run();
}
