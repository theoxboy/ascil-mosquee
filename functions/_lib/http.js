// Réponses JSON et garde-fous communs à toutes les routes /api.

export function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...headers },
  });
}

// Message pensé pour la personne qui utilise le panneau : ce qui s'est passé, et quoi faire.
export const error = (status, code, message, headers) => json({ ok: false, code, message }, status, headers);

// Les requêtes qui modifient quelque chose doivent venir du site lui-même (protection CSRF,
// en plus du cookie SameSite=Strict).
export function sameOrigin(request) {
  const origin = request.headers.get('Origin');
  if (origin) return origin === new URL(request.url).origin;
  return request.headers.get('Sec-Fetch-Site') === 'same-origin';
}

export async function readJson(request, maxBytes = 64 * 1024) {
  const len = Number(request.headers.get('Content-Length') || 0);
  if (len > maxBytes) return null;
  if (!(request.headers.get('Content-Type') || '').includes('application/json')) return null;
  try {
    const text = await request.text();
    return text.length > maxBytes ? null : JSON.parse(text);
  } catch {
    return null;
  }
}
