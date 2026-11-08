// GET & PUT /api/admin/settings/:key
// Réglages du site gérés depuis le panneau. Seules les clés de GENERIC_KEYS sont acceptées,
// chacune avec ses rôles et sa fonction de validation (aucune clé arbitraire ne peut être créée).
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { json, error, readJson } from '../../../_lib/http.js';
import { DEFAULT_SETTINGS, GENERIC_KEYS, nowIso } from '../../../_lib/settings.js';

function keyConfig(params) {
  const key = String(params.key || '').trim().toLowerCase();
  return { key, conf: Object.prototype.hasOwnProperty.call(GENERIC_KEYS, key) ? GENERIC_KEYS[key] : null };
}

export async function onRequestGet({ request, env, params }) {
  const { key, conf } = keyConfig(params);
  if (!conf) return error(404, 'not_found', 'Ce réglage n’existe pas.');
  const { response } = await requireRole(env, request, conf.roles);
  if (response) return response;

  // ?defaults=1 : valeurs d'origine (« Revenir aux valeurs d'origine » du panneau), sans rien enregistrer.
  if (new URL(request.url).searchParams.get('defaults') === '1') {
    return json({ ok: true, key, settings: conf.clean(DEFAULT_SETTINGS[key]), defaults: true });
  }
  const row = await env.DB.prepare('SELECT value, updated_at, updated_by FROM site_settings WHERE key = ?').bind(key).first();
  let saved = null;
  try { saved = row && row.value ? JSON.parse(row.value) : null; } catch { saved = null; }

  return json({
    ok: true,
    key,
    settings: conf.clean(saved || DEFAULT_SETTINGS[key]),
    updatedAt: row?.updated_at || null,
    updatedBy: row?.updated_by || null,
  });
}

export async function onRequestPut({ request, env, params }) {
  const { key, conf } = keyConfig(params);
  if (!conf) return error(404, 'not_found', 'Ce réglage n’existe pas.');
  const { admin, response } = await requireRole(env, request, conf.roles);
  if (response) return response;

  const body = await readJson(request);
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return error(400, 'bad_json', 'Données illisibles. Rechargez la page et réessayez.');
  }

  const cleaned = conf.clean(body);
  let details = null;
  if (key === 'pages') {
    const prevRow = await env.DB.prepare("SELECT value FROM site_settings WHERE key = 'pages'").first();
    let prev = null;
    try { prev = prevRow && prevRow.value ? JSON.parse(prevRow.value) : null; } catch { prev = null; }
    const before = conf.clean(prev || DEFAULT_SETTINGS.pages);
    const published = [], hidden = [];
    for (const k of Object.keys(cleaned)) {
      if (cleaned[k] !== before[k]) (cleaned[k] ? published : hidden).push(k);
    }
    if (published.length || hidden.length) details = { published, hidden };
  }
  const now = nowIso();
  await env.DB.prepare(`
    INSERT INTO site_settings (key, value, updated_at, updated_by)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
      value = excluded.value,
      updated_at = excluded.updated_at,
      updated_by = excluded.updated_by
  `).bind(key, JSON.stringify(cleaned), now, admin.id).run();

  await audit(env.DB, admin.id, 'settings.update', request, `settings:${key}`, details);
  return json({ ok: true, key, settings: cleaned, updatedAt: now });
}
