// GET & PUT /api/admin/settings/:key
// Gestion des réglages du site par les administrateurs (superadmin & éditeur).
import { audit } from '../../../_lib/auth.js';
import { requireRole } from '../../../_lib/guard.js';
import { json, error, readJson } from '../../../_lib/http.js';
import { DEFAULT_SETTINGS, cleanHomeSettings, cleanPagesSettings } from '../../../_lib/settings.js';

export async function onRequestGet({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'editor']);
  if (response) return response;

  const key = String(params.key || '').trim().toLowerCase();
  if (!key) return error(400, 'bad_key', 'Clé de réglage requise.');

  let settings = null;
  let row = null;

  if (env.DB) {
    row = await env.DB.prepare('SELECT value, updated_at, updated_by FROM site_settings WHERE key = ?').bind(key).first();
    if (row && row.value) {
      try {
        settings = JSON.parse(row.value);
      } catch {}
    }
  }

  if (!settings && DEFAULT_SETTINGS[key]) {
    settings = DEFAULT_SETTINGS[key];
  }

  if (!settings) {
    return error(404, 'not_found', 'Aucun réglage trouvé pour cette clé.');
  }

  if (key === 'home') {
    settings = cleanHomeSettings(settings);
  }
  if (key === 'pages') {
    settings = cleanPagesSettings(settings);
  }

  return json({
    ok: true,
    key,
    settings,
    updatedAt: row?.updated_at || null,
    updatedBy: row?.updated_by || null,
  });
}

export async function onRequestPut({ request, env, params }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'editor']);
  if (response) return response;

  const key = String(params.key || '').trim().toLowerCase();
  if (!key) return error(400, 'bad_key', 'Clé de réglage requise.');

  const body = await readJson(request);
  if (!body) return error(400, 'bad_json', 'Données JSON invalides.');

  let cleaned = body;
  if (key === 'home') {
    cleaned = cleanHomeSettings(body);
  }
  if (key === 'pages') {
    cleaned = cleanPagesSettings(body);
  }

  const now = new Date().toISOString();
  const valStr = JSON.stringify(cleaned);

  await env.DB.prepare(`
    INSERT INTO site_settings (key, value, updated_at, updated_by)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
      value = excluded.value,
      updated_at = excluded.updated_at,
      updated_by = excluded.updated_by
  `).bind(key, valStr, now, admin.id).run();

  await audit(env.DB, admin.id, 'settings.update', request, `settings:${key}`);

  return json({
    ok: true,
    key,
    settings: cleaned,
    updatedAt: now,
  });
}
