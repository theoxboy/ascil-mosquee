// Fonctions partagées par les routes /api/admin/accounts.
import { error } from './http.js';
import { ASSIGNABLE } from './roles.js';

export const PUBLIC_COLS = `id, username, email, display_name AS displayName, role, is_active AS isActive,
  must_change_password AS mustChangePassword, created_at AS createdAt, last_login_at AS lastLoginAt`;

export function validate(body, partial = false) {
  const out = {};
  if (!partial || body?.username !== undefined) {
    const u = typeof body?.username === 'string' ? body.username.trim() : '';
    if (!/^[A-Za-z0-9._-]{3,64}$/.test(u)) {
      return { error: 'L’identifiant doit faire 3 à 64 caractères : lettres sans accent, chiffres, point, tiret ou souligné.' };
    }
    out.username = u;
  }
  if (!partial || body?.role !== undefined) {
    if (!ASSIGNABLE.includes(body?.role)) return { error: 'Choisissez un rôle : Éditeur ou Responsable événements.' };
    out.role = body.role;
  }
  if (!partial || body?.email !== undefined) {
    const e = typeof body?.email === 'string' ? body.email.trim() : '';
    if (e && (e.length > 120 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e))) {
      return { error: 'Le courriel n’est pas valide. Exemple : prenom@exemple.com' };
    }
    out.email = e || null;
  }
  if (!partial || body?.displayName !== undefined) {
    const n = typeof body?.displayName === 'string' ? body.displayName.trim() : '';
    if (n.length > 80) return { error: 'Le nom affiché ne doit pas dépasser 80 caractères.' };
    out.displayName = n || null;
  }
  return out;
}

export function fix(a) {
  return a && { ...a, isActive: a.isActive === 1, mustChangePassword: a.mustChangePassword === 1 };
}

export async function loadTarget(db, rawId) {
  const id = Number(rawId);
  if (!Number.isInteger(id) || id < 1) return { response: error(404, 'not_found', 'Ce compte n’existe pas.') };
  const row = await db.prepare('SELECT id, username, role FROM admins WHERE id = ? AND password_hash IS NOT NULL').bind(id).first();
  if (!row) return { response: error(404, 'not_found', 'Ce compte n’existe pas, ou a déjà été supprimé.') };
  if (row.role === 'superadmin') {
    return { response: error(403, 'protected', 'Le compte superadmin ne se modifie pas ici. Utilisez « Changer mon mot de passe ».') };
  }
  return { row };
}
