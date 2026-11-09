// GET /media/<nom> : photo envoyée depuis le panneau, lue dans l'espace de stockage KV « MEDIA ».
// Une photo toute neuve peut manquer quelques secondes à un endroit du réseau (KV finalement
// cohérent) : la réponse 404 n'est alors jamais mise en cache, pour qu'elle apparaisse dès que possible.
// Le nom est vérifié (32 caractères aléatoires + extension) ; le type servi est celui reconnu
// à l'envoi, avec nosniff et une politique qui interdit tout script.
import { KEY_RE } from '../_lib/media.js';

const TYPES = { jpg: 'image/jpeg', png: 'image/png', webp: 'image/webp', gif: 'image/gif' };

export async function onRequestGet({ env, params }) {
  const key = String(params.key || '');
  const m = KEY_RE.exec(key);
  if (!m || !env.MEDIA) return new Response('Not found', { status: 404 });
  const value = await env.MEDIA.get(key, { type: 'arrayBuffer', cacheTtl: 3600 });
  if (!value) return new Response('Not found', { status: 404, headers: { 'Cache-Control': 'no-store' } });
  return new Response(value, {
    headers: {
      'Content-Type': TYPES[m[1]],
      'Content-Length': String(value.byteLength),
      'Cache-Control': 'public, max-age=31536000, immutable',
      'X-Content-Type-Options': 'nosniff',
      'Content-Security-Policy': "default-src 'none'; sandbox",
      'Content-Disposition': 'inline',
    },
  });
}
