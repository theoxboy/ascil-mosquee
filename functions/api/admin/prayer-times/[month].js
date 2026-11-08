// GET & PUT /api/admin/prayer-times/:month
// Lecture et écriture d'un mois entier de la table prayer_times (superadmin et éditeur seulement).
import { handleAdminGet, handleAdminPut } from './index.js';

export async function onRequestGet(ctx) {
  return handleAdminGet({ ...ctx, monthParam: ctx.params?.month });
}

export async function onRequestPut(ctx) {
  return handleAdminPut({ ...ctx, monthParam: ctx.params?.month });
}
