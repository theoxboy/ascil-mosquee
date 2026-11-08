// GET /media/<nom> : photo envoyée depuis le panneau, lue dans le stockage R2 « MEDIA ».
// Le nom est vérifié (32 caractères aléatoires + extension) ; le type servi est celui reconnu
// à l'envoi, avec nosniff et une politique qui interdit tout script.
import { KEY_RE } from '../_lib/media.js';

const TYPES = { jpg: 'image/jpeg', png: 'image/png', webp: 'image/webp', gif: 'image/gif' };

export async function onRequestGet({ env, params }) {
  const key = String(params.key || '');
  const m = KEY_RE.exec(key);
  if (!m || !env.MEDIA) return new Response('Not found', { status: 404 });
  const obj = await env.MEDIA.get(key);
  if (!obj) return new Response('Not found', { status: 404, headers: { 'Cache-Control': 'no-store' } });
  return new Response(obj.body, {
    headers: {
      'Content-Type': TYPES[m[1]],
      'Content-Length': String(obj.size),
      'Cache-Control': 'public, max-age=31536000, immutable',
      'X-Content-Type-Options': 'nosniff',
      'Content-Security-Policy': "default-src 'none'; sandbox",
      'Content-Disposition': 'inline',
      ETag: obj.httpEtag,
    },
  });
}
