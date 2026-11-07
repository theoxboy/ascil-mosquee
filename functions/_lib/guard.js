// Contrôle d'accès des routes /api : session valide + rôle autorisé.
import { currentAdmin } from './auth.js';
import { error } from './http.js';

// Renvoie { admin } si l'accès est permis, sinon { response } à renvoyer tel quel.
export async function requireRole(env, request, roles) {
  const admin = await currentAdmin(env.DB, request);
  if (!admin) return { response: error(401, 'unauthenticated', 'Votre session a expiré. Reconnectez-vous.') };
  if (admin.mustChangePassword) {
    return { response: error(403, 'must_change_password', 'Choisissez d’abord votre propre mot de passe.') };
  }
  if (roles && !roles.includes(admin.role)) {
    return { response: error(403, 'forbidden', 'Votre compte n’a pas accès à cette action. Demandez au superadmin si besoin.') };
  }
  return { admin };
}
