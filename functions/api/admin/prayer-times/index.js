// GET & PUT /api/admin/prayer-times (?month=AAAA-MM)
// Lecture et écriture d'un mois entier de la table prayer_times (superadmin et éditeur seulement).
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { error, json, readJson } from '../../../_lib/http.js';
import {
  ROLES,
  cleanMonthPayload,
  currentMonthToronto,
  isValidMonth,
  readHomeDefaults,
  readMonth,
  writeMonth,
} from '../../../_lib/prayer-times.js';

export async function handleAdminGet({ request, env, monthParam }) {
  const { response } = await requireRole(env, request, ROLES);
  if (response) return response;
  if (!env.DB) return error(503, 'no_db', 'Base de données non disponible.');

  const url = new URL(request.url);
  const rawMonth = monthParam || url.searchParams.get('month') || currentMonthToronto();
  const month = String(rawMonth).trim();
  if (!isValidMonth(month)) {
    return error(400, 'bad_month', 'Mois invalide. Utilisez le format AAAA-MM (ex. 2026-11).');
  }

  const [{ days, savedCount }, defaults] = await Promise.all([
    readMonth(env.DB, month),
    readHomeDefaults(env.DB),
  ]);

  return json({
    ok: true,
    month,
    days,
    savedCount,
    defaults,
  });
}

export async function handleAdminPut({ request, env, monthParam }) {
  const { admin, response } = await requireRole(env, request, ROLES);
  if (response) return response;
  if (!env.DB) return error(503, 'no_db', 'Base de données non disponible.');

  const body = await readJson(request, 128 * 1024);
  if (!body || typeof body !== 'object') {
    return error(400, 'bad_json', 'Données illisibles. Rechargez la page et réessayez.');
  }

  const url = new URL(request.url);
  const rawMonth = monthParam || url.searchParams.get('month') || (typeof body.month === 'string' ? body.month : '') || currentMonthToronto();
  const month = String(rawMonth).trim();

  const cleaned = cleanMonthPayload(month, body);
  if (cleaned.error) {
    return error(400, 'invalid_schedule', cleaned.error);
  }

  const { upserted, cleared } = await writeMonth(env.DB, month, cleaned.days);
  await audit(env.DB, admin.id, 'prayer_times.update', request, `prayer_times:${month}`, {
    upserted,
    cleared,
  });

  const [{ days, savedCount }, defaults] = await Promise.all([
    readMonth(env.DB, month),
    readHomeDefaults(env.DB),
  ]);

  return json({
    ok: true,
    month,
    days,
    savedCount,
    upserted,
    cleared,
    defaults,
  });
}

export async function onRequestGet(ctx) {
  return handleAdminGet(ctx);
}

export async function onRequestPut(ctx) {
  return handleAdminPut(ctx);
}
