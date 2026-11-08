// Widgets HTML / CSS / JS / Python des pages créées (étapes M3 et M4, table page_widgets).
//
// Le code d'un widget ne tourne JAMAIS dans la page du site. Il est servi seul à l'adresse /w/<id>,
// avec une politique « sandbox » qui lui donne une origine opaque : pour le navigateur, c'est un
// autre site. Il ne peut donc pas lire la session du panneau, les cookies, ni les données du site,
// ni toucher à la page qui l'affiche, ni ouvrir de fenêtre, ni rediriger le visiteur.
// Sans l'interrupteur « Internet », il ne peut joindre aucun serveur.
// Création et modification : superadmin seulement (voir les routes /api/admin/widgets).

export const LANGS = ['web', 'python'];
export const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';
export const NO_TABLE = 'La table des widgets n’existe pas encore. Appliquez la migration 0011 dans la console D1, puis réessayez.';
export const noTable = (e) => /no such table/i.test(String(e && e.message));

const txt = (v, max) => (typeof v === 'string' ? v.replace(/\r\n?/g, '\n').slice(0, max) : '');

export function cleanWidget(body) {
  const height = Math.round(Number(body.height));
  return {
    title: txt(body.title, 80).trim(),
    lang: LANGS.includes(body.lang) ? body.lang : 'web',
    html: txt(body.html, 100000),
    css: txt(body.css, 50000),
    js: txt(body.js, 100000),
    net: body.net === true || body.net === 1 ? 1 : 0,
    height: Number.isFinite(height) ? Math.min(2000, Math.max(80, height)) : 400,
  };
}

export function rowToWidget(r, withCode = true) {
  const w = {
    id: r.id, title: r.title, lang: r.lang, net: !!r.net, height: r.height,
    createdAt: r.created_at, updatedAt: r.updated_at,
  };
  if (withCode) Object.assign(w, { html: r.html, css: r.css, js: r.js });
  return w;
}

// Le contenu est le code du superadmin lui-même ; on évite seulement qu'une balise de fin
// glissée dans le CSS ou le JS ne coupe le document.
const inStyle = (s) => String(s || '').replace(/<\/(style)/gi, '<\\/$1');
const inScript = (s) => String(s || '').replace(/<\/(script)/gi, '<\\/$1');
const asJson = (s) => JSON.stringify(String(s || '')).replace(/</g, '\\u003c').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');

export function widgetCsp(w) {
  const py = w.lang === 'python';
  const net = !!w.net;
  const cdn = 'https://cdn.jsdelivr.net';
  return [
    'sandbox allow-scripts',
    "default-src 'none'",
    `script-src 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval'${py ? ' ' + cdn : ''}${net ? ' https:' : ''}`,
    `style-src 'unsafe-inline'${net ? ' https:' : ''}`,
    `img-src 'self' data: blob:${net ? ' https:' : ''}`,
    `media-src 'self' data: blob:${net ? ' https:' : ''}`,
    `font-src data:${net ? ' https:' : ''}`,
    `connect-src ${net ? 'https:' : py ? cdn : "'none'"}`,
    `frame-src ${net ? 'https:' : "'none'"}`,
    `form-action ${net ? 'https:' : "'none'"}`,
    "base-uri 'none'",
    "frame-ancestors 'self'",
  ].join('; ');
}

const BASE_CSS = 'html{-webkit-text-size-adjust:100%}body{margin:0;padding:8px;font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;color:#1E2B26;background:transparent;overflow-wrap:anywhere}*{box-sizing:border-box}';

export function renderWidgetDoc(w) {
  const head = `<!doctype html><html lang="fr"><head><meta charset="utf-8">`
    + `<meta name="viewport" content="width=device-width, initial-scale=1">`
    + `<meta name="robots" content="noindex">`
    + `<title>${String(w.title || 'Widget').replace(/[<>&"]/g, '')}</title>`
    + `<style>${BASE_CSS}</style><style>${inStyle(w.css)}</style></head><body>`;
  if (w.lang === 'python') {
    return head + w.html
      + '<pre id="py-sortie" aria-live="polite" style="white-space:pre-wrap;margin:8px 0 0;font:14px/1.5 ui-monospace,Menlo,monospace"></pre>'
      + `<script src="${PYODIDE}pyodide.js"></script>`
      + '<script>(function(){var out=document.getElementById("py-sortie");'
      + 'var CODE=' + asJson(w.js) + ';'
      + 'out.textContent="Chargement de Python…\\n";'
      + 'loadPyodide({indexURL:' + JSON.stringify(PYODIDE) + ',stdout:function(s){out.textContent+=s+"\\n";},stderr:function(s){out.textContent+=s+"\\n";}})'
      + '.then(function(py){out.textContent="";return py.loadPackagesFromImports(CODE).then(function(){return py.runPythonAsync(CODE);});})'
      + '.catch(function(e){out.textContent+="Erreur Python : "+(e&&e.message||e)+"\\n";});})();</script>'
      + '</body></html>';
  }
  return head + w.html + (w.js ? `<script>${inScript(w.js)}</script>` : '') + '</body></html>';
}
