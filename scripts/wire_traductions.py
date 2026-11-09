"""Étape L2 : nouvelle rubrique « Traductions » du panneau (SA-Traductions.dc.html).

- Textes du panneau : tous les textes saisis dans les rubriques (accueil, horaires, services, événements…),
  relus en direct depuis la base, avec un champ arabe et un champ anglais pour chacun.
- Textes fixes du site : le dictionnaire intégré (i18n/ar.json, i18n/en.json) ; une traduction saisie ici
  remplace celle du site, un champ vidé revient à la traduction du site.
- Plus utilisés : traductions enregistrées dont le texte français n'apparaît plus nulle part (à retirer).
- Filtre « À traduire », recherche, enregistrement dans la clé de réglage « traductions » (superadmin et éditeur).
- Menu : lien « Traductions » dans toutes les pages du panneau.
Les pages publiques (#ascil-i18n, wire_langues.py) appliquent ces traductions en priorité.

Page construite à partir de SA-Pages.dc.html déjà relié (même en-tête, même composant minimal).
Ordre : après wire_formulaires.py, avant wire_pied.py. Idempotent.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def save(path, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def inject_script(tpl, script_id, script):
    tpl = re.sub(r'<script id="' + script_id + r'">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    return tpl[:k] + script + tpl[k:]


TRASH = ('<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path>'
         '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>')

STYLE = '''<style id="sa-tr-style">
.tr-tools{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.tr-item{border:1px solid #E4D9C0;border-radius:14px;padding:14px;background:#fff;display:flex;flex-direction:column;gap:10px}
.tr-item.todo{border-color:#C49A4A}
.tr-head{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.tr-tag{display:inline-flex;align-items:center;min-height:24px;padding:0 10px;border-radius:999px;font-size:12px;font-weight:700;background:#F3EAD8;color:#7A5A1E}
.tr-tag.ok{background:#DCEFE6;color:#0E4D3C}.tr-tag.todo{background:#FFF1D6;color:#7A4A00}
.tr-fr{margin:0;padding:10px 12px;border-radius:10px;background:#FAF6EC;color:#1E2B26;overflow-wrap:anywhere;white-space:pre-wrap}
.tr-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:start}
@container (max-width: 760px){.tr-grid{grid-template-columns:minmax(0,1fr)}}
.tr-grid textarea{inline-size:100%;min-inline-size:0;min-height:64px;resize:vertical}
@font-face{font-family:'Cairo';src:url('/fonts/cairo/Cairo-Variable.ttf') format('truetype');font-weight:200 1000;font-style:normal;font-display:swap}
.tr-grid textarea[lang="ar"]{font-family:'Cairo','Noto Sans Arabic',system-ui,sans-serif;font-size:16px}
.tr-bar{position:sticky;bottom:0;z-index:5;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;
  padding:12px 14px;border:1px solid #E4D9C0;border-radius:14px;background:#FFFEF9;box-shadow:0 -8px 24px -18px rgba(0,0,0,.35)}
.tr-list{list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:10px}
</style>
'''

MAIN = '''
   <div><p class="eyebrow">Rubrique du menu</p><h1 class="serif ttl-page">Traductions</h1>
   <p style="margin:6px 0 0;color:#4F5E57;max-width:720px">Le site s’affiche en français, en arabe et en anglais. Les textes fixes sont déjà traduits ; les textes que vous saisissez dans le panneau (annonces, événements, services…) s’affichent en français tant qu’ils n’ont pas de traduction ici. Un champ laissé vide garde le texte français, ou la traduction du site quand elle existe.</p></div>
   <p id="tr-notice" class="pg-err" role="alert" hidden></p>
   <section class="card" aria-labelledby="tr-t"><div class="card-h"><span class="num" aria-hidden="true">1</span><div><h2 class="ttl" id="tr-t">Textes à traduire</h2>
   <p class="dsc" id="tr-count" role="status">Chargement des textes du site…</p></div></div>
   <div class="card-b">
    <div class="tr-tools" style="margin-top:10px">
     <div class="seg" role="group" aria-label="Quels textes afficher" style="flex-wrap:wrap">
      <button type="button" data-tr-view="panel" aria-pressed="true">Textes du panneau</button><button type="button" data-tr-view="fixed" aria-pressed="false">Textes fixes du site</button><button type="button" data-tr-view="old" aria-pressed="false">Plus utilisés</button></div>
     <div class="seg" role="group" aria-label="Filtrer" style="flex-wrap:wrap">
      <button type="button" data-tr-only="todo" aria-pressed="true">À traduire</button><button type="button" data-tr-only="" aria-pressed="false">Tous</button></div>
     <input class="in" id="tr-q" type="search" aria-label="Rechercher un texte, en français, en arabe ou en anglais" placeholder="Rechercher un texte…" style="flex:1 1 220px;min-width:0">
    </div>
    <p class="hint" id="tr-view-hint" style="margin:8px 0 0"></p>
    <ul class="tr-list" id="tr-list"></ul>
    <div style="display:flex;justify-content:center;margin-top:12px"><button type="button" class="btn btn-line" id="tr-more" hidden>Afficher 30 textes de plus</button></div>
   </div></section>
   <div class="tr-bar">
    <span id="tr-status" role="status" style="font-weight:700;color:#0E4D3C;font-size:14px">Tout est enregistré</span>
    <span class="tr-tools"><button type="button" class="btn btn-line" id="tr-undo" disabled>Annuler les changements</button>
    <button type="button" class="btn btn-gold" id="tr-save" disabled>Enregistrer les traductions</button></span>
   </div>
'''

SCRIPT = r"""<script id="sa-traductions">
(function () {
  var TRASH = __TRASH__;
  // Rubriques du panneau dont les textes s'affichent sur le site public.
  var KEYS = { home: 'Accueil', alert: 'Bannière d’alerte', season: 'Mode du site', horaires: 'Horaires', khutba: 'Langue de la khutba',
    rappel: 'Rappel de prière', apropos: 'À propos', campagne: 'Campagne en direct', services: 'Services', cours: 'Cours',
    mariages: 'Mariages', funerailles: 'Funérailles', aide: 'Aide alimentaire', femmes: 'Espace femmes', dons: 'Faire un don',
    merci: 'Bloc Merci', evenements: 'Événements', calendrier: 'Calendrier du mois', ressources: 'Ressources', dua: 'Mur Dua et annonces',
    contact: 'Contact', p404: 'Page 404' };
  // Champs qui ne contiennent jamais de texte affiché (liens, médias, identifiants, coordonnées).
  var SKIP_KEY = /^(lien|liens|href|url|link|mapUrl|itineraire|photo|photos|plan|image|img|src|email|courriel|telephone|tel|numero|compte|transit|institution|codePostal|lat|lng|id|slug|icone|tone|couleur|color|bg|fg|to|from|suivreLien|mapage|page)$/i;
  var VIEWS = {
    panel: 'Textes saisis dans les rubriques du panneau. Ils s’affichent en français tant qu’ils n’ont pas de traduction.',
    fixed: 'Textes fixes du site, déjà traduits. Écrivez ici pour corriger une traduction ; videz le champ pour revenir à celle du site.',
    old: 'Traductions enregistrées dont le texte français n’apparaît plus sur le site (texte modifié ou supprimé). Vous pouvez les retirer.'
  };
  var used = new Map();      // texte -> rubriques
  var builtin = { ar: {}, en: {} };
  var saved = new Map();     // texte -> { ar, en } (enregistré)
  var work = new Map();      // texte -> { ar, en } (modifié, non enregistré)
  var view = 'panel', only = 'todo', query = '', limit = 30, saving = false;
  function $(x) { return document.getElementById(x); }
  function flash(m) { var b = window.__saPage; if (b && b.flash) b.flash(m); }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text != null) e.textContent = text;
    return e;
  }
  function norm(s) { return String(s || '').replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/ /g, ' ').replace(/\s+/g, ' ').trim(); }
  function plural(n, one, many) { return n + ' ' + (n > 1 ? many : one); }
  function api(url, opt) {
    return fetch(url, Object.assign({ credentials: 'same-origin', headers: { 'Content-Type': 'application/json' } }, opt || {}))
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function isText(v) {
    if (v.length < 2 || v.length > 2000 || !/[A-Za-zÀ-ÿ]/.test(v)) return false;
    if (/^(https?:\/\/|mailto:|tel:|data:|\/)/i.test(v) || /^\S+@\S+\.\S+$/.test(v)) return false;
    if (/^#[0-9a-f]{3,8}$/i.test(v) || /^\d{4}-\d\d(-\d\d)?(T|$)/.test(v) || /^\d{1,2}:\d\d$/.test(v)) return false;
    if (/^[a-z0-9_.\-]+$/.test(v)) return false;   // valeur technique (ex. « salle », « m1 »)
    return true;
  }
  function collect(o, label, key) {
    if (o == null) return;
    if (typeof o === 'string') {
      if (key && SKIP_KEY.test(key)) return;
      var v = norm(o);
      if (!isText(v)) return;
      if (!used.has(v)) used.set(v, []);
      var l = used.get(v); if (l.indexOf(label) < 0) l.push(label);
      return;
    }
    if (Array.isArray(o)) { o.forEach(function (x) { collect(x, label, key); }); return; }
    if (typeof o === 'object') Object.keys(o).forEach(function (k) { collect(o[k], label, k); });
  }
  function value(fr, lg) {
    if (work.has(fr)) return work.get(fr)[lg] || '';
    return saved.has(fr) ? saved.get(fr)[lg] || '' : '';
  }
  function effective(fr, lg) { return value(fr, lg) || builtin[lg][fr] || ''; }
  function todo(fr) { return !effective(fr, 'ar') || !effective(fr, 'en'); }
  function dirty() {
    var n = 0;
    work.forEach(function (w, fr) {
      var s = saved.get(fr) || { ar: '', en: '' };
      if ((w.ar || '') !== (s.ar || '') || (w.en || '') !== (s.en || '')) n += 1;
    });
    return n;
  }
  function listFor(v) {
    var out = [];
    if (v === 'panel') used.forEach(function (labels, fr) { out.push(fr); });
    else if (v === 'fixed') Object.keys(builtin.ar).forEach(function (fr) { if (!used.has(fr)) out.push(fr); });
    else saved.forEach(function (x, fr) { if (!used.has(fr) && !builtin.ar[fr]) out.push(fr); });
    return out.sort(function (a, b) { return a.localeCompare(b, 'fr'); });
  }
  function matches(fr) {
    if (only === 'todo' && view !== 'old' && !todo(fr)) return false;
    if (!query) return true;
    var q = query.toLowerCase();
    return (fr + ' ' + effective(fr, 'ar') + ' ' + effective(fr, 'en')).toLowerCase().indexOf(q) > -1;
  }
  function counts() {
    var panel = listFor('panel'), missAr = 0, missEn = 0;
    panel.forEach(function (fr) { if (!effective(fr, 'ar')) missAr += 1; if (!effective(fr, 'en')) missEn += 1; });
    $('tr-count').textContent = plural(panel.length, 'texte saisi dans le panneau', 'textes saisis dans le panneau') + ' · '
      + (missAr ? missAr + ' sans arabe' : 'tous en arabe') + ' · ' + (missEn ? missEn + ' sans anglais' : 'tous en anglais')
      + ' · ' + plural(listFor('old').length, 'traduction plus utilisée', 'traductions plus utilisées');
  }
  var uid = 0;
  function area(fr, lg, label) {
    uid += 1;
    var id = 'tr-' + lg + '-' + uid;
    var f = el('div', { class: 'fld' });
    f.appendChild(el('label', { class: 'lbl', for: id }, label));
    var t = el('textarea', { class: 'in', id: id, rows: '2', maxlength: '2000', lang: lg, dir: lg === 'ar' ? 'rtl' : 'ltr' });
    t.value = value(fr, lg);
    if (builtin[lg][fr]) t.setAttribute('placeholder', builtin[lg][fr]);
    t.addEventListener('input', function () {
      var w = work.get(fr) || { ar: value(fr, 'ar'), en: value(fr, 'en') };
      w[lg] = t.value;
      work.set(fr, w);
      status();
    });
    f.appendChild(t);
    if (builtin[lg][fr]) f.appendChild(el('p', { class: 'hint' }, 'Vide : traduction du site (affichée en gris).'));
    return f;
  }
  function render() {
    var ul = $('tr-list'); if (!ul) return;
    ul.innerHTML = '';
    $('tr-view-hint').textContent = VIEWS[view];
    var all = listFor(view).filter(matches);
    if (!all.length) {
      var li = el('li', { class: 'tr-item' });
      li.appendChild(el('p', { class: 'hint', style: 'margin:0' }, query ? 'Aucun texte ne correspond à cette recherche.'
        : view === 'old' ? 'Aucune traduction inutilisée.' : only === 'todo' ? 'Tout est traduit ici. Choisissez « Tous » pour relire ou corriger.' : 'Aucun texte.'));
      ul.appendChild(li);
    }
    all.slice(0, limit).forEach(function (fr) {
      var li = el('li', { class: 'tr-item' + (view !== 'old' && todo(fr) ? ' todo' : '') });
      var head = el('div', { class: 'tr-head' });
      (used.get(fr) || [view === 'fixed' ? 'Texte fixe du site' : 'Plus utilisé']).forEach(function (l) { head.appendChild(el('span', { class: 'tr-tag' }, l)); });
      if (view !== 'old') head.appendChild(el('span', { class: 'tr-tag ' + (todo(fr) ? 'todo' : 'ok') }, todo(fr) ? 'À traduire' : 'Traduit'));
      li.appendChild(head);
      li.appendChild(el('p', { class: 'tr-fr', lang: 'fr' }, fr));
      var g = el('div', { class: 'tr-grid' });
      g.appendChild(area(fr, 'ar', 'Arabe'));
      g.appendChild(area(fr, 'en', 'Anglais'));
      li.appendChild(g);
      if (view === 'old') {
        var x = el('button', { type: 'button', class: 'btn btn-line', style: 'align-self:flex-start;display:inline-flex;gap:8px;align-items:center' });
        x.innerHTML = TRASH; x.appendChild(document.createTextNode('Retirer cette traduction'));
        x.addEventListener('click', function () { work.set(fr, { ar: '', en: '' }); status(); render(); });
        li.appendChild(x);
      }
      ul.appendChild(li);
    });
    $('tr-more').hidden = all.length <= limit;
    counts();
  }
  function status() {
    var n = dirty();
    $('tr-status').textContent = saving ? 'Enregistrement…' : n ? plural(n, 'traduction modifiée, non enregistrée', 'traductions modifiées, non enregistrées') : 'Tout est enregistré';
    $('tr-save').disabled = !n || saving;
    $('tr-undo').disabled = !n || saving;
  }
  function payload() {
    var map = new Map();
    saved.forEach(function (x, fr) { map.set(fr, { ar: x.ar || '', en: x.en || '' }); });
    work.forEach(function (w, fr) { map.set(fr, { ar: norm(w.ar), en: norm(w.en) }); });
    var items = [];
    map.forEach(function (x, fr) { if (x.ar || x.en) items.push({ fr: fr, ar: x.ar, en: x.en }); });
    return { items: items };
  }
  function setSaved(items) {
    saved = new Map();
    (items || []).forEach(function (x) { saved.set(x.fr, { ar: x.ar || '', en: x.en || '' }); });
  }
  function save() {
    if (saving || !dirty()) return;
    saving = true; status();
    api('/api/admin/settings/traductions', { method: 'PUT', body: JSON.stringify(payload()) }).then(function (r) {
      saving = false;
      if (!r.ok) { status(); flash(r.message || 'L’enregistrement a échoué. Réessayez.'); return; }
      setSaved(r.settings && r.settings.items);
      work = new Map();
      status(); render();
      flash('Traductions enregistrées. Le site les affiche d’ici une minute.');
    }, function () { saving = false; status(); flash('Impossible de joindre le serveur. Vos changements sont toujours là : réessayez.'); });
  }
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('button');
    if (!t || !document.getElementById('tr-list')) return;
    if (t.hasAttribute('data-tr-view')) {
      view = t.getAttribute('data-tr-view'); limit = 30;
      document.querySelectorAll('[data-tr-view]').forEach(function (b) { b.setAttribute('aria-pressed', String(b === t)); });
      render();
    } else if (t.hasAttribute('data-tr-only')) {
      only = t.getAttribute('data-tr-only'); limit = 30;
      document.querySelectorAll('[data-tr-only]').forEach(function (b) { b.setAttribute('aria-pressed', String(b === t)); });
      render();
    } else if (t.id === 'tr-more') { limit += 30; render(); }
    else if (t.id === 'tr-save') { save(); }
    else if (t.id === 'tr-undo') {
      if (!window.confirm('Annuler toutes les traductions modifiées depuis le dernier enregistrement ?')) return;
      work = new Map(); status(); render();
    }
  });
  document.addEventListener('input', function (e) {
    if (e.target && e.target.id === 'tr-q') { query = norm(e.target.value); limit = 30; render(); }
  });
  window.addEventListener('beforeunload', function (e) { if (dirty()) { e.preventDefault(); e.returnValue = ''; } });

  function load() {
    var keys = Object.keys(KEYS);
    var reads = keys.map(function (k) {
      return api('/api/admin/settings/' + k).then(function (r) { if (r.ok) collect(r.settings, KEYS[k], null); }, function () {});
    });
    var dicts = ['ar', 'en'].map(function (lg) {
      return fetch('/i18n/' + lg + '.json', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { if (d && d.strings) builtin[lg] = d.strings; }, function () {});
    });
    var mine = api('/api/admin/settings/traductions').then(function (r) {
      if (!r.ok) throw new Error(r.message || 'Lecture impossible.');
      setSaved(r.settings && r.settings.items);
    });
    Promise.all(reads.concat(dicts)).then(function () { return mine; }).then(function () {
      $('tr-notice').hidden = true; status(); render();
    }, function (err) {
      var n = $('tr-notice'); n.hidden = false;
      n.textContent = 'Les traductions n’ont pas pu être chargées (' + (err && err.message ? err.message : 'erreur réseau') + '). Rechargez la page.';
      $('tr-count').textContent = 'Chargement impossible.';
    });
  }

  // Démarrage : attend que la page (#dc-root) soit montée par React.
  var started = false;
  function tryStart() {
    if (started || document.querySelector('x-dc') || !window.__saPage || !$('tr-list')) return;
    started = true;
    load();
  }
  window.addEventListener('sa-page-ready', tryStart);
  tryStart();
  if (!started) {
    new MutationObserver(function (m, o) {
      if (!document.querySelector('x-dc') && window.__saPage && $('tr-list')) { o.disconnect(); tryStart(); }
    }).observe(document.documentElement, { childList: true, subtree: true });
  }
})();
</script>
"""

LINK = '<a href="SA-Traductions.dc.html">Traductions</a>'


def add_menu(tpl):
    """Lien « Traductions » juste avant « Comptes » dans le menu latéral, et dans la liste « Page à gérer »."""
    if 'href="SA-Traductions.dc.html"' not in tpl and '<a href="SA-Comptes.html">Comptes</a>' in tpl:
        tpl = tpl.replace('<a href="SA-Comptes.html">Comptes</a>', LINK + '<a href="SA-Comptes.html">Comptes</a>', 1)
    for sel in ('jump-page', 'jump'):
        m = re.search(r'<sc-raw-select class="in" id="' + sel + r'">.*?</sc-raw-select>', tpl, re.S)
        if m and '<option>Traductions</option>' not in m.group(0) and '<option>Comptes</option>' in m.group(0):
            new = m.group(0).replace('<option>Comptes</option>', '<option>Traductions</option><option>Comptes</option>', 1)
            tpl = tpl[:m.start()] + new + tpl[m.end():]
    return tpl


def wire_page():
    src = ROOT / 'SA-Pages.dc.html'
    s, i, j, tpl = load(src)
    assert 'id="sa-pages-list"' in tpl, 'lancer wire_pages.py avant wire_traductions.py'
    tpl = re.sub(r'<title>.*?</title>', '<title>Superadmin · Traductions — ASCIL</title>', tpl, count=1)
    a = tpl.index('<main')
    a = tpl.index('>', a) + 1
    b = tpl.index('</main>', a)
    tpl = tpl[:a] + MAIN + tpl[b:]
    tpl = re.sub(r'<script id="sa-pages-list">.*?</script>\s*', '', tpl, flags=re.S)
    tpl = tpl.replace('<a href="SA-Pages.dc.html" aria-current="page" class="on">Créer une page</a>', '<a href="SA-Pages.dc.html">Créer une page</a>', 1)
    tpl = add_menu(tpl)
    tpl = tpl.replace(LINK, '<a href="SA-Traductions.dc.html" aria-current="page" class="on">Traductions</a>', 1)
    assert 'aria-current="page" class="on">Traductions</a>' in tpl
    tpl = re.sub(r'<style id="sa-tr-style">.*?</style>\s*', '', tpl, flags=re.S)
    k = tpl.index('</head>')
    tpl = tpl[:k] + STYLE + tpl[k:]
    tpl = inject_script(tpl, 'sa-traductions', SCRIPT.replace('__TRASH__', json.dumps(TRASH)))
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    (ROOT / 'SA-Traductions.dc.html').write_text(s[:i] + enc + s[j:], encoding='utf-8')
    print('SA-Traductions.dc.html : rubrique Traductions créée')


def wire_menus():
    n = 0
    for path in sorted(ROOT.glob('SA-*.dc.html')):
        if path.name in ('SA-Traductions.dc.html', 'SA-Connexion.dc.html'):
            continue
        s, i, j, tpl = load(path)
        if '<nav class="side nav"' not in tpl:
            continue
        new = add_menu(tpl)
        if new != tpl:
            save(path, s, i, j, new)
            n += 1
    p = ROOT / 'SA-Comptes.html'
    if p.exists():
        c = p.read_text(encoding='utf-8')
        if 'href="SA-Traductions.dc.html"' not in c:
            c2 = c.replace('   <a href="SA-Comptes.html" aria-current="page" class="on">Comptes</a>',
                           '   <a href="SA-Traductions.dc.html">Traductions</a>\n   <a href="SA-Comptes.html" aria-current="page" class="on">Comptes</a>', 1)
            assert c2 != c, 'menu de SA-Comptes.html introuvable'
            p.write_text(c2, encoding='utf-8')
    print(f'menu « Traductions » ajouté à {n} pages du panneau (et Comptes)')


if __name__ == '__main__':
    wire_page()
    wire_menus()
