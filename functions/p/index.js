// GET /p ou /p/ : pas de page sans lien ; on affiche la page « introuvable » du site.
import { renderNotFound } from '../_lib/render-page.js';

export function onRequestGet() {
  return new Response(renderNotFound(), {
    status: 404,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' },
  });
}
