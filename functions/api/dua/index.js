// /api/dua : mur public « Dua et annonces » (page N3-Dua).
//  GET                                                   messages publiés (signalés exclus) et règles du mur
//  POST { action:'send', type, categorie, texte, signature, ok, hp, t }   envoi pour validation
//  POST { action:'amin', id }                            « J'ai fait une dua » (une fois par connexion et par jour)
//  POST { action:'report', id }                          signalement : le message quitte le mur jusqu'à relecture
// Anti-robot comme le formulaire Contact : champ piège, délai minimal, 5 envois par connexion en 15 minutes.
import { json, error, readJson } from '../../_lib/http.js';
import { clientIp } from '../../_lib/auth.js';
import { readDuaSettings, cleanDuaMessage, limited, noTable, MIN_FILL_MS, NO_TABLE } from '../../_lib/dua.js';

const COLS = 'id, type, categorie, texte, signature, amin, published_at';

export async function onRequestGet({ env }) {
  const rules = await readDuaSettings(env.DB);
  try {
    const [d, a] = await Promise.all([
      env.DB.prepare(`SELECT ${COLS} FROM dua_messages WHERE status = 'publie' AND signale = 0 AND type = 'dua' ORDER BY published_at DESC, id DESC LIMIT 60`).all(),
      env.DB.prepare(`SELECT ${COLS} FROM dua_messages WHERE status = 'publie' AND signale = 0 AND type = 'ann' ORDER BY published_at DESC, id DESC LIMIT 60`).all(),
    ]);
    return json({ ok: true, rules, duas: d?.results || [], anns: a?.results || [] }, 200, { 'Cache-Control': 'public, max-age=15, stale-while-revalidate=60' });
  } catch (err) {
    console.error('dua list error:', err && err.message);
    if (noTable(err)) return json({ ok: true, rules, duas: [], anns: [], installed: false });
    return error(500, 'db_error', 'Le mur n’a pas pu être chargé. Réessayez dans un instant.');
  }
}

export async function onRequestPost({ request, env }) {
  const body = await readJson(request, 8 * 1024);
  if (!body || typeof body !== 'object') return error(400, 'invalid_payload', 'La demande n’a pas pu être lue. Rechargez la page et réessayez.');
  const ip = clientIp(request);
  const id = parseInt(body.id, 10);

  if (body.action === 'amin' || body.action === 'report') {
    if (!(id > 0)) return error(400, 'invalid_id', 'Message non reconnu. Rechargez la page et réessayez.');
    const amin = body.action === 'amin';
    if (amin) {
      const rules = await readDuaSettings(env.DB);
      if (!rules.compteur) return error(400, 'off', 'Le compteur n’est pas activé sur le mur.');
    }
    const over = amin ? await limited(env.DB, 'dua.amin.' + id, ip, 1, 24 * 60 * 60 * 1000) : await limited(env.DB, 'dua.report', ip, 10, 15 * 60 * 1000);
    try {
      if (amin) {
        if (!over) await env.DB.prepare("UPDATE dua_messages SET amin = amin + 1 WHERE id = ? AND status = 'publie' AND type = 'dua'").bind(id).run();
        const row = await env.DB.prepare('SELECT amin FROM dua_messages WHERE id = ?').bind(id).first();
        if (!row) return error(404, 'not_found', 'Ce message n’est plus sur le mur.');
        return json({ ok: true, id, amin: Number(row.amin) || 0 });
      }
      if (over) return error(429, 'too_many', 'Trop de signalements depuis cette connexion. Réessayez dans 15 minutes.', { 'Retry-After': '900' });
      await env.DB.prepare("UPDATE dua_messages SET signale = 1 WHERE id = ? AND status = 'publie'").bind(id).run();
      return json({ ok: true, id, message: 'Merci. Le message est retiré du mur le temps d’être relu.' });
    } catch (err) {
      console.error('dua action error:', err && err.message);
      if (noTable(err)) return error(503, 'no_table', NO_TABLE);
      return error(500, 'db_error', 'L’action n’a pas pu être enregistrée. Réessayez dans un instant.');
    }
  }

  if (body.action !== 'send') return error(400, 'invalid_action', 'Action non reconnue. Rechargez la page et réessayez.');
  if (typeof body.hp === 'string' && body.hp.trim()) return json({ ok: true });
  const elapsed = Number(body.t);
  if (!Number.isFinite(elapsed) || elapsed < MIN_FILL_MS) return error(400, 'too_fast', 'Envoi trop rapide. Relisez votre message, puis envoyez-le à nouveau.');
  const rules = await readDuaSettings(env.DB);
  if (rules.pause) return error(403, 'paused', 'Le mur est en pause : aucun nouveau message pour le moment. Revenez bientôt.');
  if (body.ok !== true) return error(400, 'missing_consent', 'Cochez la case de relecture pour envoyer votre message.');
  const checked = cleanDuaMessage(body, rules);
  if (!checked.value) return error(400, checked.code, checked.message);
  if (await limited(env.DB, 'dua.send', ip, 5, 15 * 60 * 1000)) {
    return error(429, 'too_many', 'Trop de messages envoyés depuis cette connexion. Réessayez dans 15 minutes.', { 'Retry-After': '900' });
  }
  const v = checked.value;
  try {
    await env.DB.prepare('INSERT INTO dua_messages (type, categorie, texte, signature) VALUES (?, ?, ?, ?)').bind(v.type, v.categorie, v.texte, v.signature).run();
  } catch (err) {
    console.error('dua insert error:', err && err.message);
    if (noTable(err)) return error(503, 'no_table', 'Le mur n’accepte pas encore de messages. Réessayez plus tard.');
    return error(500, 'db_error', 'Votre message n’a pas pu être enregistré. Réessayez dans un instant.');
  }
  return json({ ok: true, message: 'Merci. Votre message apparaîtra sur le mur après relecture (sous ' + rules.delai + ').' });
}
