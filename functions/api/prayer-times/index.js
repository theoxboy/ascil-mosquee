// GET /api/prayer-times (?month=AAAA-MM & ?date=AAAA-MM-JJ)
// Route publique (sans authentification) du tableau mensuel et des heures du jour.
// Source unique : la table prayer_times ; les heures du jour viennent de la ligne du jour,
// avec repli sur les défauts Accueil (Fajr 06:30, Jumu'a 12:30, Icha 19:00) si une case est vide ou absente.
import { error, json } from '../../_lib/http.js';
import {
  currentMonthToronto,
  isValidDate,
  isValidMonth,
  readDay,
  readHomeDefaults,
  readMonth,
  resolveDayWithDefaults,
  todayToronto,
} from '../../_lib/prayer-times.js';

const CACHE_HEADERS = { 'Cache-Control': 'public, max-age=15, stale-while-revalidate=120' };

export async function handlePublicGet({ request, env, param }) {
  const url = new URL(request.url);
  const p = typeof param === 'string' ? param.trim() : '';

  const todayDate = todayToronto();
  let dateQuery = url.searchParams.get('date') || url.searchParams.get('day') || '';
  let monthQuery = url.searchParams.get('month') || '';

  if (p) {
    if (p.toLowerCase() === 'today' || p.toLowerCase() === 'aujourdhui') {
      dateQuery = todayDate;
    } else if (isValidDate(p)) {
      dateQuery = p;
    } else if (isValidMonth(p)) {
      monthQuery = p;
    } else {
      return error(400, 'bad_param', 'Paramètre invalide. Indiquez un mois (AAAA-MM), une date (AAAA-MM-JJ) ou « today ».');
    }
  }

  if (dateQuery) {
    dateQuery = dateQuery.trim();
    if (dateQuery.toLowerCase() === 'today' || dateQuery.toLowerCase() === 'aujourdhui') {
      dateQuery = todayDate;
    } else if (!isValidDate(dateQuery)) {
      return error(400, 'bad_date', 'Date invalide. Utilisez le format AAAA-MM-JJ (ex. 2026-11-08).');
    }
  }

  const targetDate = dateQuery || todayDate;
  const targetMonth = (monthQuery ? monthQuery.trim() : '') || targetDate.slice(0, 7) || currentMonthToronto();
  if (!isValidMonth(targetMonth)) {
    return error(400, 'bad_month', 'Mois invalide. Utilisez le format AAAA-MM (ex. 2026-11).');
  }

  // Si on demande uniquement le jour via /api/prayer-times/today ou /api/prayer-times/AAAA-MM-JJ (sans ?month)
  const dayOnly = Boolean(p && p.toLowerCase() !== targetMonth && !monthQuery);
  if (dayOnly) {
    const { day, raw, defaults } = await readDay(env.DB, targetDate);
    return json(
      {
        ok: true,
        date: targetDate,
        day,
        today: targetDate === todayDate ? day : (await readDay(env.DB, todayDate)).day,
        raw,
        defaults,
      },
      200,
      CACHE_HEADERS
    );
  }

  const [{ days, savedCount }, defaults] = await Promise.all([
    readMonth(env.DB, targetMonth),
    readHomeDefaults(env.DB),
  ]);

  const byDate = new Map(days.map((d) => [d.date, d]));

  const resolveForDate = async (dStr) => {
    if (byDate.has(dStr)) {
      const row = byDate.get(dStr);
      return resolveDayWithDefaults(row, defaults, dStr);
    }
    return (await readDay(env.DB, dStr)).day;
  };

  const [day, today] = await Promise.all([
    resolveForDate(targetDate),
    targetDate === todayDate ? null : resolveForDate(todayDate),
  ]);

  return json(
    {
      ok: true,
      month: targetMonth,
      date: targetDate,
      day,
      today: today || day,
      days,
      savedCount,
      defaults,
    },
    200,
    CACHE_HEADERS
  );
}

export async function onRequestGet(ctx) {
  return handlePublicGet(ctx);
}
