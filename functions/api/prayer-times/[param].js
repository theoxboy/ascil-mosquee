// GET /api/prayer-times/:param  (:param = today | AAAA-MM-JJ | AAAA-MM)
// Route publique du jour ou du mois (sans authentification).
import { handlePublicGet } from './index.js';

export async function onRequestGet(ctx) {
  return handlePublicGet({ ...ctx, param: ctx.params?.param });
}
