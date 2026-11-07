// Rendu HTML des pages créées dans le superadmin (/p/<lien>), côté serveur, sans aucun script.
// Tout texte venant de la base est échappé ; les liens sont recalculés à partir des blocs validés.
import { PAGE_FILES } from './settings.js';

const esc = (s) => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const WIDTHS = { normal: '760px', large: '1120px', full: '100%' };
const ALERT_TONES = {
  info: { bg: 'var(--vert)', fg: '#FFFFFF', label: 'Information' },
  attention: { bg: 'var(--or)', fg: 'var(--encre)', label: 'Attention' },
  urgent: { bg: 'var(--rouge)', fg: '#FFFFFF', label: 'Urgent' },
};

function href(lien) {
  if (!lien) return null;
  if (lien.type === 'page' && PAGE_FILES[lien.page]) return { url: `/${PAGE_FILES[lien.page]}.dc.html`, ext: false };
  if (lien.type === 'custom' && lien.slug) return { url: `/p/${encodeURIComponent(lien.slug)}`, ext: false };
  if (lien.type === 'url' && /^https?:\/\//i.test(lien.url || '')) return { url: lien.url, ext: true };
  return null;
}

function renderBlock(b) {
  if (b.type === 'texte') {
    const paras = String(b.texte || '').split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean)
      .map((p) => `<p>${esc(p).replace(/\n/g, '<br>')}</p>`).join('');
    if (!b.titre && !paras) return '';
    return `<section class="blk blk-texte">${b.titre ? `<h2>${esc(b.titre)}</h2>` : ''}${paras}</section>`;
  }
  if (b.type === 'bouton') {
    const h = href(b.lien);
    if (!h || !b.texte) return '';
    const extra = h.ext ? ' target="_blank" rel="noopener"' : '';
    return `<p class="blk blk-bouton"><a class="btn btn-${esc(b.style || 'or')}" href="${esc(h.url)}"${extra}>${esc(b.texte)}`
      + `${h.ext ? '<span class="sr"> (ouvre un autre site)</span>' : ''}</a></p>`;
  }
  if (b.type === 'tableau') {
    const cols = Array.isArray(b.colonnes) ? b.colonnes : [];
    const rows = (Array.isArray(b.lignes) ? b.lignes : []).filter((r) => r.some((c) => String(c).trim()));
    if (!rows.length && !cols.some((c) => String(c).trim())) return '';
    const head = cols.some((c) => String(c).trim())
      ? `<thead><tr>${cols.map((c) => `<th scope="col">${esc(c)}</th>`).join('')}</tr></thead>` : '';
    const body = rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join('')}</tr>`).join('');
    return `<div class="blk blk-tableau" role="region" aria-label="Tableau, défilable horizontalement si besoin" tabindex="0">`
      + `<table>${head}<tbody>${body}</tbody></table></div>`;
  }
  return '';
}

const STYLE = `
:root{--vert:#0E4D3C;--vert-fonce:#08362A;--or:#C49A4A;--sable:#F3EAD8;--sable-bord:#E4D9C0;--encre:#1E2B26;
--muted:#4F5E57;--fond:#FAF8F1;--blanc:#FFFFFF;--rouge:#B3261E;--focus:#C49A4A}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--fond);color:var(--encre);font:16px/1.6 'Noto Sans',system-ui,-apple-system,'Segoe UI',sans-serif;overflow-wrap:anywhere}
a{color:var(--vert)}
a:focus-visible,.blk-tableau:focus-visible{outline:3px solid var(--focus);outline-offset:3px;border-radius:6px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:-9999px;top:8px;background:var(--blanc);color:var(--vert);padding:10px 14px;border-radius:10px;z-index:100}
.skip:focus{left:16px}
.alert{padding:10px 16px;text-align:center;font-weight:600}
.alert a{color:inherit;text-underline-offset:3px}
.hdr{background:var(--vert);color:var(--sable)}
.hdr-in,.ftr-in{max-width:1180px;margin:0 auto;padding:0 16px}
.hdr-in{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;min-height:64px}
.logo{color:var(--blanc);font-weight:800;font-size:20px;text-decoration:none;display:inline-flex;flex-direction:column;line-height:1.15;padding:6px 0}
.logo small{font-size:12px;font-weight:600;color:var(--sable)}
.nav{display:flex;flex-wrap:wrap;gap:4px 16px;margin:0;padding:0;list-style:none}
.nav a{color:var(--sable);text-decoration:none;display:inline-flex;align-items:center;min-height:44px;font-weight:600}
.nav a:hover{color:var(--blanc);text-decoration:underline}
.nav .don{background:var(--or);color:var(--encre);padding:0 16px;border-radius:999px}
.nav .don:hover{color:var(--encre);background:#D6AE60}
main{margin:0 auto;padding:40px 16px 64px}
h1{font-family:'Noto Serif',Georgia,serif;color:var(--vert);font-size:clamp(32px,6vw,48px);line-height:1.15;margin:0 0 24px}
.blk{margin:0 0 28px}
.blk h2{font-family:'Noto Serif',Georgia,serif;color:var(--vert);font-size:clamp(22px,3.4vw,28px);line-height:1.25;margin:0 0 10px}
.blk-texte p{margin:0 0 14px;max-width:70ch}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 24px;border-radius:999px;font-weight:700;text-decoration:none;border:2px solid transparent}
.btn-or{background:var(--or);color:var(--encre)}.btn-or:hover{background:#D6AE60}
.btn-vert{background:var(--vert);color:var(--blanc)}.btn-vert:hover{background:var(--vert-fonce)}
.btn-contour{background:transparent;color:var(--vert);border-color:var(--vert)}.btn-contour:hover{background:var(--sable)}
.blk-tableau{overflow-x:auto;border:1px solid var(--sable-bord);border-radius:14px;background:var(--blanc);
  background-image:linear-gradient(to right,var(--blanc),var(--blanc)),linear-gradient(to left,var(--blanc),var(--blanc)),
  linear-gradient(to right,rgba(0,0,0,.12),transparent),linear-gradient(to left,rgba(0,0,0,.12),transparent);
  background-position:left,right,left,right;background-repeat:no-repeat;background-size:24px 100%,24px 100%,12px 100%,12px 100%;
  background-attachment:local,local,scroll,scroll}
table{border-collapse:collapse;width:100%;min-width:480px}
th,td{padding:12px 14px;text-align:start;border-bottom:1px solid var(--sable);vertical-align:top}
th{background:var(--sable);color:var(--vert)}
tr:last-child td{border-bottom:0}
.draft{background:var(--sable);color:#7A5A1E;text-align:center;padding:10px 16px;font-weight:700;border-bottom:1px solid var(--sable-bord)}
.empty{color:var(--muted)}
.ftr{background:var(--vert);color:var(--sable);padding:32px 0;font-size:15px}
.ftr a{color:var(--sable)}
.ftr p{margin:0 0 6px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
`;

function alertHtml(alert) {
  if (!alert) return '';
  const t = ALERT_TONES[alert.tone] || ALERT_TONES.attention;
  const h = href(alert.link);
  const link = h ? ` <a href="${esc(h.url)}"${h.ext ? ' target="_blank" rel="noopener"' : ''}>En savoir plus</a>` : '';
  return `<div class="alert" role="region" aria-label="Information importante" style="background:${t.bg};color:${t.fg}">`
    + `<span class="sr">${t.label} : </span>${esc(alert.message)}${link}</div>`;
}

const HEADER = `<header class="hdr"><div class="hdr-in">
<a class="logo" href="/">ASCIL<small>Mosquée de Rivière-du-Loup</small></a>
<nav aria-label="Navigation principale"><ul class="nav">
<li><a href="/Horaires.dc.html">Horaires</a></li><li><a href="/Evenements.dc.html">Événements</a></li>
<li><a href="/Services.dc.html">Services</a></li><li><a href="/Contact.dc.html">Contact</a></li>
<li><a class="don" href="/Dons.dc.html">Faire un don</a></li></ul></nav></div></header>`;

const FOOTER = `<footer class="ftr"><div class="ftr-in">
<p><strong>ASCIL</strong> · Association Socio-Culturelle Islamique Louperivoise</p>
<p>174 rue Lafontaine, Rivière-du-Loup (Québec) · <a href="mailto:associationrdl.ascil@gmail.com">associationrdl.ascil@gmail.com</a></p>
<p><a href="/">Retour à l’accueil</a></p></div></footer>`;

function shell({ title, description, body, noindex, canonical, layout, alert, draft }) {
  const site = layout !== 'blank';
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} — ASCIL</title>
${description ? `<meta name="description" content="${esc(description)}">` : ''}
${noindex ? '<meta name="robots" content="noindex, nofollow">' : ''}
${canonical ? `<link rel="canonical" href="${esc(canonical)}">` : ''}
<meta property="og:title" content="${esc(title)}">
${description ? `<meta property="og:description" content="${esc(description)}">` : ''}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700;800&family=Noto+Serif:wght@700&display=swap">
<style>${STYLE}</style></head><body>
<a class="skip" href="#contenu">Aller au contenu</a>
${draft ? '<p class="draft" role="note">Brouillon : cette page n’est visible que par les comptes connectés au superadmin.</p>' : ''}
${site ? alertHtml(alert) + HEADER : ''}
${body}
${site ? FOOTER : ''}
</body></html>`;
}

export function renderPage(page, { alert = null, draft = false, origin = '' } = {}) {
  const blocks = (page.blocks || []).map(renderBlock).join('');
  const body = `<main id="contenu" style="max-width:${WIDTHS[page.width] || WIDTHS.normal}">`
    + `<h1>${esc(page.title)}</h1>${blocks || '<p class="empty">Cette page est encore vide.</p>'}</main>`;
  return shell({
    title: page.title,
    description: page.description,
    body,
    noindex: page.visibility !== 'published',
    canonical: page.visibility === 'published' && origin ? `${origin}/p/${page.slug}` : '',
    layout: page.layout,
    alert,
    draft,
  });
}

export function renderNotFound() {
  return shell({
    title: 'Page introuvable',
    body: `<main id="contenu" style="max-width:760px"><h1>Page introuvable</h1>`
      + `<p>Cette page n’existe pas, a été retirée ou n’est pas encore publiée. Vérifiez l’adresse, ou revenez à l’accueil.</p>`
      + `<p><a class="btn btn-vert" href="/">Retour à l’accueil</a></p></main>`,
    noindex: true,
    layout: 'site',
  });
}
