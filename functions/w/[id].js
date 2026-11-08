// GET /w/<id> : un widget seul, dans sa boîte isolée (voir functions/_lib/widgets.js).
// Les pages /p/ l'affichent dans un <iframe sandbox="allow-scripts">, et cette réponse impose
// elle-même la même isolation (CSP sandbox), même si quelqu'un ouvre l'adresse directement.
import { noTable, renderWidgetDoc, widgetCsp } from '../_lib/widgets.js';

export async function onRequestGet({ env, params }) {
  const id = Number(params.id);
  const missing = () => new Response('Widget introuvable.', {
    status: 404, headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' },
  });
  if (!env.DB || !Number.isInteger(id) || id < 1) return missing();
  let row = null;
  try {
    row = await env.DB.prepare('SELECT * FROM page_widgets WHERE id = ?').bind(id).first();
  } catch (e) {
    if (noTable(e)) return missing();
    throw e;
  }
  if (!row) return missing();
  return new Response(renderWidgetDoc(row), {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Content-Security-Policy': widgetCsp(row),
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer',
      'X-Robots-Tag': 'noindex, nofollow',
      'Cache-Control': 'no-cache',
      'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
    },
  });
}
