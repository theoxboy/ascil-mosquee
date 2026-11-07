"""Branche « Créer une page » (étape 5b) sur l'API /api/admin/pages.

1. SA-Pages.dc.html (« Mes pages ») : formulaire « Nouvelle page » et vraie liste des pages,
   avec Modifier, Voir, Copier le lien, Dupliquer, Supprimer (confirmation). Les onglets
   « Widgets » et « Guide développeur » de la maquette, non fonctionnels, sont retirés.
2. SA-PageEditeur.dc.html (éditeur, ?id=<page>) : titre, blocs Texte / Bouton / Tableau,
   lien de la page, visibilité, mise en page, largeur, description. L'en-tête garde le statut,
   « Enregistrer », « Publier » / « Mettre à jour » et « Aperçu » (ouvre /p/<lien>).
   Les contenus d'exemple de la maquette (blocs, code, widgets, emplacements) sont retirés.
3. SA-Panneau.dc.html (étape 5d) : les pages créées (publiées ou lien privé) sont proposées dans
   les 9 sélecteurs de liens de l'accueil ; « Lien externe… » demande l'adresse ; la page
   d'exemple « Inscriptions Ramadan 2027 » est retirée.

Dans ces deux pages, le composant de la maquette est remplacé par un composant minimal qui ne
gère que l'en-tête et les messages ; le contenu est piloté par un script autonome.
Ordre : après install_superadmin.py, avant fix_inputs.py (voir BACKEND.md). Idempotent.
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


def replace_main(tpl, inner):
    a = tpl.index('<main')
    a = tpl.index('>', a) + 1
    b = tpl.index('</main>', a)
    return tpl[:a] + inner + tpl[b:]


def replace_component(tpl, code):
    return re.sub(r'(<script type="text/x-dc"[^>]*>).*?(</script>)', lambda m: m.group(1) + code + m.group(2), tpl, count=1, flags=re.S)


def inject_script(tpl, script_id, script):
    tpl = re.sub(r'<script id="' + script_id + r'">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    return tpl[:k] + script + tpl[k:]


def drop_side_sub(tpl):
    # Sous-menu « Mes pages / Widgets / Guide développeur » : les deux derniers n'existent plus.
    return re.sub(r'<div class="side-sub"><a href="(?:SA-Pages\.dc\.html)?#sp-0">Mes pages</a>.*?</div>', '', tpl, count=1, flags=re.S)


ICON = {
    'up': '<path d="m18 15-6-6-6 6"></path>',
    'down': '<path d="m6 9 6 6 6-6"></path>',
    'trash': '<path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>',
    'copy': '<rect width="14" height="14" x="8" y="8" rx="2"></rect><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path>',
    'dup': '<path d="M12 5v14"></path><path d="M5 12h14"></path>',
}

# Styles communs ajoutés aux deux pages (bouton danger, pastilles de statut, éditeur responsive).
STYLE = '''<style id="sa-pages-style">
.btn-danger{background:#B3261E;color:#fff;border-color:#B3261E}
.btn-danger:hover{background:#8C1D18;border-color:#8C1D18}
.ico.ico-danger{color:#B3261E;border-color:#E9B4AF}
.ico.ico-danger:hover{background:#FBEAE8}
.pg-tag{display:inline-flex;align-items:center;min-height:24px;padding:0 10px;border-radius:999px;font-size:12px;font-weight:700}
.pg-tag.draft{background:#F3EAD8;color:#7A5A1E}.pg-tag.published{background:#DCEFE6;color:#0E4D3C}.pg-tag.private{background:#E6EEF8;color:#1F4E86}
.pg-list{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:10px}
.pg-item{display:flex;flex-wrap:wrap;gap:12px 16px;align-items:center;justify-content:space-between;padding:14px 16px;border:1px solid #E4D9C0;border-radius:14px;background:#fff}
.pg-item-main{min-width:0;flex:1 1 260px}
.pg-item-title{font-weight:700;color:#0E4D3C;overflow-wrap:anywhere}
.pg-actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.pg-mono{font-family:ui-monospace,Menlo,monospace}
.pg-err{margin:0;padding:10px 14px;border-radius:12px;background:#FBEAE8;color:#8C1D18;font-size:14px}
.pe-grid{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:18px;align-items:start}
@container (max-width: 1023px){.pe-grid{grid-template-columns:minmax(0,1fr)}}
.pe-block-h{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pe-block-h .ttl{flex:1;min-width:0}
.pe-add{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.pe-table{overflow-x:auto;border:1px solid #E4D9C0;border-radius:12px;background:#fff;margin-top:10px}
.pe-table table{border-collapse:collapse;min-width:100%}
.pe-table td,.pe-table th{padding:6px;border-bottom:1px solid #F3EAD8}
.pe-table .in{min-width:120px}
.pe-slug{display:flex;align-items:center;gap:6px}
.pe-slug span{color:#4F5E57;font-weight:600}
.pe-slug .in{flex:1;min-width:0}
</style>
'''


def svg(name):
    return ('<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + ICON[name] + '</svg>')


# ---------------------------------------------------------------- composant minimal
# Ne gère que l'en-tête (statut, boutons) et les messages ; le contenu appelle window.__saPage.
BRIDGE = """
class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.state = { loaded: false, dirty: false, saving: false, vis: 'draft', toast: '' };
    window.__saPage = this;
  }
  componentDidMount() { window.dispatchEvent(new Event('sa-page-ready')); }
  componentWillUnmount() { clearTimeout(this.tt); if (window.__saPage === this) window.__saPage = null; }
  flash(m) { this.setState({ toast: m }); clearTimeout(this.tt); this.tt = setTimeout(() => this.setState({ toast: '' }), 3200); }
  renderVals() {
    const st = this.state;
    const label = !st.loaded ? 'Chargement…' : st.vis === 'list' ? 'Tout est enregistré' : st.saving ? 'Enregistrement…' : st.dirty ? 'Changements non enregistrés'
      : st.vis === 'published' ? 'Publiée · tout est enregistré' : st.vis === 'private' ? 'Lien privé · tout est enregistré' : 'Brouillon · tout est enregistré';
    const call = (name, arg) => () => { if (typeof window[name] === 'function') window[name](arg); };
    return {
      dot: st.dirty ? '#C49A4A' : '#7FB89F', statusTxt: label,
      clean: !st.loaded || st.saving || !st.dirty,
      save: call('saPageSave'), undo: call('saPageUndo'),
      saveDraft: call('saPageSave'), publish: call('saPageSave', 'published'),
      pubLabel: st.vis === 'published' ? 'Mettre à jour' : 'Publier',
      openPv: call('saPagePreview'),
      toast: st.toast
    };
  }
}
"""


# ---------------------------------------------------------------- 1. Mes pages
LIST_MAIN = '''
   <div><p class="eyebrow">Rubrique du menu</p><h1 class="serif ttl-page">Créer une page</h1>
   <p style="margin:6px 0 0;color:#4F5E57;max-width:640px">Ajoutez une page complète sans toucher au code : texte, boutons, tableaux. Chaque page a son adresse, en brouillon tant que vous ne la publiez pas.</p></div>
   <section class="card" aria-labelledby="np-t"><div class="card-h"><span class="num" aria-hidden="true">1</span><div><h2 class="ttl" id="np-t">Nouvelle page</h2>
   <p class="dsc">Elle démarre en brouillon, invisible du public. Vous la remplissez ensuite dans l’éditeur.</p></div></div>
   <div class="card-b"><form id="np-form" novalidate style="display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;margin-top:10px">
   <div class="fld" style="flex:1 1 260px;min-width:0"><label class="lbl" for="np-title">Titre de la page</label>
   <input class="in" id="np-title" type="text" maxlength="120" placeholder="Ex. Inscriptions Ramadan 2027" aria-describedby="np-msg"></div>
   <button type="submit" class="btn btn-gold" id="np-btn" style="min-height:48px">Créer la page</button></form>
   <p id="np-msg" class="pg-err" role="alert" hidden style="margin-top:10px"></p></div></section>
   <section class="card" aria-labelledby="pl-t"><div class="card-h"><span class="num" aria-hidden="true">2</span><div><h2 class="ttl" id="pl-t">Pages créées</h2>
   <p class="dsc" id="pl-count">Chargement…</p></div></div>
   <div class="card-b"><ul class="pg-list" id="pl-list"></ul><p id="pl-msg" role="status" aria-live="polite" class="hint" style="margin:10px 0 0"></p></div></section>
'''

LIST_SCRIPT = r"""<script id="sa-pages-list">
(function () {
  var VIS = { draft: 'Brouillon', published: 'Publiée', private: 'Lien privé' };
  var ICON = __ICONS__;
  var pages = [];
  function $(id) { return document.getElementById(id); }
  function bridge() { return window.__saPage; }
  function flash(m) { var b = bridge(); if (b) b.flash(m); else { var p = $('pl-msg'); if (p) p.textContent = m; } }
  function api(url, opt) {
    return fetch(url, Object.assign({ credentials: 'same-origin', headers: { 'Content-Type': 'application/json' } }, opt || {}))
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function when(iso) {
    var d = new Date(iso);
    return isNaN(d) ? '—' : d.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short', year: 'numeric' });
  }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text != null) e.textContent = text;
    return e;
  }
  function iconBtn(name, label, cls) {
    var b = el('button', { type: 'button', class: 'ico' + (cls ? ' ' + cls : ''), 'aria-label': label, title: label });
    b.innerHTML = ICON[name];
    return b;
  }
  function render() {
    var ul = $('pl-list'); if (!ul) return;
    ul.innerHTML = '';
    var n = pages.length;
    $('pl-count').textContent = n ? n + (n > 1 ? ' pages' : ' page') + ' · le lien de chaque page se modifie dans son éditeur.' : 'Aucune page pour l’instant.';
    if (!n) {
      var li = el('li', { class: 'pg-item' });
      li.appendChild(el('p', { class: 'hint', style: 'margin:0' },
        'Vos pages apparaîtront ici. Donnez un titre ci-dessus et cliquez sur « Créer la page » : elle démarre en brouillon, invisible du public.'));
      ul.appendChild(li);
      return;
    }
    pages.forEach(function (p) {
      var li = el('li', { class: 'pg-item' });
      var main = el('div', { class: 'pg-item-main' });
      var head = el('div', { style: 'display:flex;flex-wrap:wrap;gap:8px;align-items:center' });
      head.appendChild(el('span', { class: 'pg-item-title' }, p.title));
      head.appendChild(el('span', { class: 'pg-tag ' + p.visibility }, VIS[p.visibility] || p.visibility));
      main.appendChild(head);
      var meta = el('p', { class: 'hint', style: 'margin:4px 0 0' });
      meta.appendChild(el('span', { class: 'pg-mono' }, p.url));
      meta.appendChild(document.createTextNode(' · ' + p.blockCount + (p.blockCount > 1 ? ' blocs' : ' bloc') +
        ' · modifiée le ' + when(p.updatedAt) + (p.updatedBy ? ' par ' + p.updatedBy : '')));
      main.appendChild(meta);
      var act = el('div', { class: 'pg-actions' });
      act.appendChild(el('a', { class: 'btn btn-green', href: 'SA-PageEditeur.dc.html?id=' + p.id, style: 'min-height:40px' }, 'Modifier'));
      act.appendChild(el('a', { class: 'btn btn-line', href: p.url, target: '_blank', rel: 'noopener', style: 'min-height:40px' }, 'Voir'));
      var c = iconBtn('copy', 'Copier le lien de « ' + p.title + ' »');
      c.addEventListener('click', function () {
        var full = location.origin + p.url;
        (navigator.clipboard ? navigator.clipboard.writeText(full) : Promise.reject()).then(
          function () { flash('Lien copié : ' + full); },
          function () { flash('Copie impossible ici. Le lien est : ' + full); });
      });
      var d = iconBtn('dup', 'Dupliquer « ' + p.title + ' »');
      d.addEventListener('click', function () {
        d.setAttribute('aria-busy', 'true');
        api('/api/admin/pages/' + p.id + '/duplicate', { method: 'POST', body: '{}' }).then(function (r) {
          d.removeAttribute('aria-busy');
          if (!r.ok) { flash(r.message || 'La duplication a échoué. Réessayez.'); return; }
          flash('Copie créée en brouillon : « ' + r.page.title + ' ».');
          load();
        }, function () { d.removeAttribute('aria-busy'); flash('Impossible de joindre le serveur. Réessayez.'); });
      });
      var x = iconBtn('trash', 'Supprimer « ' + p.title + ' »', 'ico-danger');
      x.addEventListener('click', function () {
        if (!window.confirm('Supprimer définitivement « ' + p.title + ' » ?\n\nSon adresse ' + p.url + ' ne fonctionnera plus. Cette action est irréversible.')) return;
        api('/api/admin/pages/' + p.id, { method: 'DELETE' }).then(function (r) {
          if (!r.ok) { flash(r.message || 'La suppression a échoué. Réessayez.'); return; }
          flash('Page « ' + p.title + ' » supprimée.');
          load();
        }, function () { flash('Impossible de joindre le serveur. Réessayez.'); });
      });
      act.appendChild(c); act.appendChild(d); act.appendChild(x);
      li.appendChild(main); li.appendChild(act);
      ul.appendChild(li);
    });
  }
  function load() {
    api('/api/admin/pages').then(function (r) {
      if (!r.ok) { $('pl-count').textContent = r.message || 'Impossible de charger les pages. Rechargez la page.'; return; }
      pages = r.pages; render();
    }, function () { $('pl-count').textContent = 'Impossible de joindre le serveur. Rechargez la page.'; });
  }
  document.addEventListener('submit', function (e) {
    if (!e.target || e.target.id !== 'np-form') return;
    e.preventDefault();
    var t = $('np-title'), btn = $('np-btn'), msg = $('np-msg');
    if (btn.getAttribute('aria-busy') === 'true') return;
    msg.hidden = true; t.removeAttribute('aria-invalid');
    if (t.value.trim().length < 2) {
      t.setAttribute('aria-invalid', 'true'); msg.textContent = 'Donnez un titre à la page (2 caractères minimum).'; msg.hidden = false; t.focus(); return;
    }
    btn.setAttribute('aria-busy', 'true'); btn.textContent = 'Création…';
    api('/api/admin/pages', { method: 'POST', body: JSON.stringify({ title: t.value.trim() }) }).then(function (r) {
      if (r.ok) { location.href = 'SA-PageEditeur.dc.html?id=' + r.page.id; return; }
      btn.removeAttribute('aria-busy'); btn.textContent = 'Créer la page';
      msg.textContent = r.message || 'La création a échoué. Réessayez.'; msg.hidden = false;
    }, function () {
      btn.removeAttribute('aria-busy'); btn.textContent = 'Créer la page';
      msg.textContent = 'Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.'; msg.hidden = false;
    });
  });
  function start() { var b = bridge(); if (b) b.setState({ loaded: true, vis: 'list' }); load(); }
  if (document.getElementById('pl-list')) start();
  else new MutationObserver(function (m, o) { if (document.getElementById('pl-list')) { o.disconnect(); start(); } })
    .observe(document.documentElement, { childList: true, subtree: true });
})();
</script>
"""


def wire_list():
    path = ROOT / 'SA-Pages.dc.html'
    s, i, j, tpl = load(path)
    tpl = replace_main(tpl, LIST_MAIN)
    tpl = replace_component(tpl, BRIDGE)
    tpl = drop_side_sub(tpl)
    tpl = re.sub(r'<style id="sa-pages-style">.*?</style>\s*', '', tpl, flags=re.S)
    k = tpl.index('</head>')
    tpl = tpl[:k] + STYLE + tpl[k:]
    tpl = inject_script(tpl, 'sa-pages-list', LIST_SCRIPT.replace('__ICONS__', json.dumps({k: svg(k) for k in ICON})))
    save(path, s, i, j, tpl)
    print('SA-Pages.dc.html : « Mes pages » relié à la base')


# ---------------------------------------------------------------- 2. Éditeur
EDITOR_MAIN = '''
   <nav aria-label="Fil d’Ariane" style="font-size:14px;color:#4F5E57"><a href="SA-Pages.dc.html" style="font-weight:600">Créer une page</a> › Éditeur</nav>
   <p id="pe-missing" class="pg-err" role="alert" hidden></p>
   <div id="pe-root" class="pe-grid" hidden>
    <div style="display:flex;flex-direction:column;gap:18px;min-width:0">
     <div class="fld"><label class="lbl" for="pe-title">Titre de la page</label>
     <input class="in" id="pe-title" type="text" maxlength="120" style="font-size:22px;font-weight:700;color:#0E4D3C;min-height:56px"></div>
     <div id="pe-blocks" style="display:flex;flex-direction:column;gap:14px"></div>
     <section class="card" aria-labelledby="pe-add-t"><div class="card-b">
      <h2 class="ttl" id="pe-add-t" style="margin:0">Ajouter un bloc</h2>
      <p class="hint" style="margin:4px 0 0">Les blocs s’affichent dans cet ordre sur la page. Changez l’ordre avec les flèches.</p>
      <div class="pe-add"><button type="button" class="btn btn-line" data-pe-add="texte">+ Texte</button>
      <button type="button" class="btn btn-line" data-pe-add="bouton">+ Bouton</button>
      <button type="button" class="btn btn-line" data-pe-add="tableau">+ Tableau</button></div>
     </div></section>
    </div>
    <aside aria-label="Réglages de la page" style="display:flex;flex-direction:column;gap:14px;min-width:0">
     <section class="card" aria-labelledby="pe-link-t"><div class="card-b">
      <h2 class="ttl" id="pe-link-t" style="margin:0 0 8px">Lien de la page</h2>
      <div class="fld"><label class="lbl" for="pe-slug">Adresse</label>
      <div class="pe-slug"><span aria-hidden="true">/p/</span><input class="in pg-mono" id="pe-slug" type="text" maxlength="60" aria-describedby="pe-slug-hint pe-slug-err" autocomplete="off" spellcheck="false"></div>
      <p class="hint" id="pe-slug-hint">Lettres minuscules, chiffres et tirets. Si vous la changez, l’ancienne adresse redirige vers la nouvelle.</p>
      <p class="pg-err" id="pe-slug-err" role="alert" hidden></p></div>
      <button type="button" class="btn btn-line" id="pe-copy" style="margin-top:8px">Copier le lien</button>
     </div></section>
     <section class="card" aria-labelledby="pe-pub-t"><div class="card-b">
      <h2 class="ttl" id="pe-pub-t" style="margin:0 0 8px">Publication</h2>
      <div class="fld"><span class="lbl" id="pe-vis-l">Visibilité</span>
      <div class="seg" role="group" aria-labelledby="pe-vis-l" style="flex-wrap:wrap;align-self:flex-start">
       <button type="button" data-pe-vis="draft" aria-pressed="true">Brouillon</button>
       <button type="button" data-pe-vis="published" aria-pressed="false">Publiée</button>
       <button type="button" data-pe-vis="private" aria-pressed="false">Lien privé</button></div>
      <p class="hint" id="pe-vis-hint"></p></div>
      <div class="fld"><span class="lbl" id="pe-lay-l">Mise en page</span>
      <div class="seg" role="group" aria-labelledby="pe-lay-l" style="flex-wrap:wrap;align-self:flex-start">
       <button type="button" data-pe-lay="site" aria-pressed="true">Avec menu et pied</button>
       <button type="button" data-pe-lay="blank" aria-pressed="false">Page vierge</button></div>
      <p class="hint" id="pe-lay-hint"></p></div>
      <div class="fld"><label class="lbl" for="pe-width">Largeur du contenu</label>
      <select class="in" id="pe-width"><option value="normal">Normale (lecture)</option><option value="large">Large (tableaux)</option><option value="full">Pleine largeur</option></select></div>
     </div></section>
     <section class="card" aria-labelledby="pe-seo-t"><div class="card-b">
      <h2 class="ttl" id="pe-seo-t" style="margin:0 0 8px">Partage et Google</h2>
      <div class="fld"><label class="lbl" for="pe-desc">Description courte</label>
      <textarea class="in" id="pe-desc" rows="3" maxlength="160" aria-describedby="pe-desc-hint" style="min-height:84px;resize:vertical"></textarea>
      <p class="hint" id="pe-desc-hint">Affichée par Google et sur Facebook. <span id="pe-desc-n">0</span> / 160 caractères.</p></div>
     </div></section>
    </aside>
   </div>
'''

EDITOR_SCRIPT = r"""<script id="sa-page-editor">
(function () {
  var ICON = __ICONS__;
  var SITE_LINKS = __SITE_LINKS__;
  var VIS_HINT = { draft: 'Visible seulement dans le superadmin.', published: 'Visible par tous à son adresse.',
    private: 'Accessible seulement à qui a le lien. Google ne la voit pas.' };
  var LAY_HINT = { site: 'La page garde le menu, le logo et le pied de page du site.', blank: 'Sans menu ni pied de page : idéal pour un outil ou un tableau.' };
  var META = { texte: 'Texte', bouton: 'Bouton', tableau: 'Tableau' };
  var id = parseInt(new URLSearchParams(location.search).get('id'), 10);
  var page = null, blocks = [], saved = '', customPages = [], vis = 'draft', lay = 'site';
  function $(x) { return document.getElementById(x); }
  function bridge() { return window.__saPage; }
  function setBridge(st) { var b = bridge(); if (b) b.setState(st); }
  function flash(m) { var b = bridge(); if (b) b.flash(m); }
  function api(url, opt) {
    return fetch(url, Object.assign({ credentials: 'same-origin', headers: { 'Content-Type': 'application/json' } }, opt || {}))
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }).then(function (d) { d.status = r.status; return d; }); });
  }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text != null) e.textContent = text;
    return e;
  }
  function field(label, input, hint) {
    var f = el('div', { class: 'fld' });
    var l = el('label', { class: 'lbl', for: input.id }, label);
    f.appendChild(l); f.appendChild(input);
    if (hint) f.appendChild(el('p', { class: 'hint' }, hint));
    return f;
  }
  var uid = 0;
  function nid(p) { uid += 1; return 'pe-' + p + '-' + uid; }

  // ---------- état
  function snapshot() {
    return JSON.stringify({ title: $('pe-title').value.trim(), slug: $('pe-slug').value.trim().toLowerCase(), blocks: blocks,
      visibility: vis, layout: lay, width: $('pe-width').value, description: $('pe-desc').value.trim() });
  }
  function dirtyCheck() { setBridge({ dirty: snapshot() !== saved }); }
  window.addEventListener('beforeunload', function (e) { if (page && snapshot() !== saved) { e.preventDefault(); e.returnValue = ''; } });

  // ---------- liens des boutons
  function linkOptions(sel, current) {
    sel.innerHTML = '';
    var add = function (parent, value, label) { var o = el('option', { value: value }, label); parent.appendChild(o); return o; };
    add(sel, '', 'Aucun lien');
    var g1 = el('optgroup', { label: 'Pages du site' }); sel.appendChild(g1);
    SITE_LINKS.forEach(function (x) { add(g1, 'page:' + x[0], x[1]); });
    var mine = customPages.filter(function (p) { return p.id !== id && p.visibility !== 'draft'; });
    if (mine.length) {
      var g2 = el('optgroup', { label: 'Pages créées (publiées ou lien privé)' }); sel.appendChild(g2);
      mine.forEach(function (p) { add(g2, 'custom:' + p.slug, p.title); });
    }
    add(sel, 'url', 'Lien externe…');
    var v = !current || current.type === 'none' ? '' : current.type === 'page' ? 'page:' + current.page
      : current.type === 'custom' ? 'custom:' + current.slug : 'url';
    if (current && current.type === 'custom' && !mine.some(function (p) { return p.slug === current.slug; })) {
      add(sel, v, 'Page créée : /p/' + current.slug + ' (brouillon ou supprimée)');
    }
    sel.value = v;
  }

  // ---------- rendu des blocs
  function blockCard(b, i) {
    var n = blocks.length;
    var sec = el('section', { class: 'card', 'aria-label': 'Bloc ' + (i + 1) + ' : ' + META[b.type] });
    var body = el('div', { class: 'card-b' });
    var head = el('div', { class: 'pe-block-h' });
    head.appendChild(el('span', { class: 'num', 'aria-hidden': 'true' }, String(i + 1)));
    head.appendChild(el('h3', { class: 'ttl', style: 'margin:0' }, META[b.type]));
    [['up', 'Monter', i === 0, -1], ['down', 'Descendre', i === n - 1, 1]].forEach(function (m) {
      var btn = el('button', { type: 'button', class: 'ico', 'aria-label': m[1] + ' le bloc ' + (i + 1) });
      btn.innerHTML = ICON[m[0]]; btn.disabled = m[2];
      btn.addEventListener('click', function () { var t = blocks[i]; blocks[i] = blocks[i + m[3]]; blocks[i + m[3]] = t; render(); dirtyCheck(); });
      head.appendChild(btn);
    });
    var del = el('button', { type: 'button', class: 'ico ico-danger', 'aria-label': 'Supprimer le bloc ' + (i + 1) });
    del.innerHTML = ICON.trash;
    del.addEventListener('click', function () {
      if (!window.confirm('Supprimer le bloc ' + (i + 1) + ' (' + META[b.type] + ') ? Son contenu sera perdu à l’enregistrement.')) return;
      blocks.splice(i, 1); render(); dirtyCheck();
    });
    head.appendChild(del);
    body.appendChild(head);

    var on = function (input, fn) { input.addEventListener('input', function () { fn(input.value); dirtyCheck(); }); input.addEventListener('change', function () { fn(input.value); dirtyCheck(); }); };
    if (b.type === 'texte') {
      var t1 = el('input', { class: 'in', type: 'text', id: nid('t'), maxlength: '200' }); t1.value = b.titre || '';
      on(t1, function (v) { b.titre = v; });
      var t2 = el('textarea', { class: 'in', id: nid('x'), rows: '6', maxlength: '5000', style: 'min-height:140px;resize:vertical' }); t2.value = b.texte || '';
      on(t2, function (v) { b.texte = v; });
      body.appendChild(field('Titre de la section (facultatif)', t1));
      body.appendChild(field('Texte', t2, 'Une ligne vide sépare deux paragraphes.'));
    } else if (b.type === 'bouton') {
      var g = el('div', { class: 'g2', style: 'align-items:start' });
      var bt = el('input', { class: 'in', type: 'text', id: nid('b'), maxlength: '80', placeholder: 'Ex. Voir les horaires du Ramadan' }); bt.value = b.texte || '';
      on(bt, function (v) { b.texte = v; });
      var sel = el('select', { class: 'in', id: nid('l') }); linkOptions(sel, b.lien);
      var url = el('input', { class: 'in', type: 'url', id: nid('u'), maxlength: '500', placeholder: 'https://…' });
      url.value = b.lien && b.lien.type === 'url' ? b.lien.url : '';
      var urlField = field('Adresse du lien externe', url);
      var syncLink = function () {
        var v = sel.value;
        urlField.style.display = v === 'url' ? '' : 'none';
        b.lien = !v ? { type: 'none' } : v === 'url' ? { type: 'url', url: url.value.trim() }
          : v.indexOf('page:') === 0 ? { type: 'page', page: v.slice(5) } : { type: 'custom', slug: v.slice(7) };
      };
      sel.addEventListener('change', function () { syncLink(); dirtyCheck(); });
      on(url, function () { syncLink(); });
      syncLink();
      var st = el('select', { class: 'in', id: nid('s') });
      [['or', 'Or (principal)'], ['vert', 'Vert'], ['contour', 'Contour']].forEach(function (x) { st.appendChild(el('option', { value: x[0] }, x[1])); });
      st.value = b.style || 'or';
      st.addEventListener('change', function () { b.style = st.value; dirtyCheck(); });
      g.appendChild(field('Texte du bouton', bt)); g.appendChild(field('Lien', sel));
      body.appendChild(g); body.appendChild(urlField); body.appendChild(field('Style', st));
    } else if (b.type === 'tableau') {
      var wrap = el('div', { class: 'pe-table', tabindex: '0', 'aria-label': 'Tableau du bloc ' + (i + 1) + ', défilable horizontalement' });
      var table = el('table'); var thead = el('thead'); var hr = el('tr');
      b.colonnes.forEach(function (c, ci) {
        var th = el('th', { scope: 'col' });
        var inp = el('input', { class: 'in', type: 'text', maxlength: '80', 'aria-label': 'Titre de la colonne ' + (ci + 1), placeholder: 'Colonne ' + (ci + 1) });
        inp.value = c; on(inp, function (v) { b.colonnes[ci] = v; });
        th.appendChild(inp); hr.appendChild(th);
      });
      thead.appendChild(hr); table.appendChild(thead);
      var tb = el('tbody');
      b.lignes.forEach(function (row, ri) {
        var tr = el('tr');
        row.forEach(function (cell, ci) {
          var td = el('td');
          var inp = el('input', { class: 'in', type: 'text', maxlength: '200', 'aria-label': 'Ligne ' + (ri + 1) + ', colonne ' + (ci + 1) });
          inp.value = cell; on(inp, function (v) { b.lignes[ri][ci] = v; });
          td.appendChild(inp); tr.appendChild(td);
        });
        tb.appendChild(tr);
      });
      table.appendChild(tb); wrap.appendChild(table); body.appendChild(wrap);
      var tools = el('div', { class: 'pe-add' });
      var tool = function (label, enabled, fn) {
        var x = el('button', { type: 'button', class: 'btn btn-line' }, label); x.disabled = !enabled;
        x.addEventListener('click', function () { fn(); render(); dirtyCheck(); }); tools.appendChild(x);
      };
      tool('+ Ligne', b.lignes.length < 100, function () { b.lignes.push(b.colonnes.map(function () { return ''; })); });
      tool('+ Colonne', b.colonnes.length < 8, function () { b.colonnes.push(''); b.lignes.forEach(function (r) { r.push(''); }); });
      tool('− Dernière ligne', b.lignes.length > 0, function () { b.lignes.pop(); });
      tool('− Dernière colonne', b.colonnes.length > 1, function () { b.colonnes.pop(); b.lignes.forEach(function (r) { r.pop(); }); });
      body.appendChild(tools);
    }
    sec.appendChild(body);
    return sec;
  }
  function render() {
    var box = $('pe-blocks'); box.innerHTML = '';
    if (!blocks.length) {
      var empty = el('section', { class: 'card' }); var b = el('div', { class: 'card-b' });
      b.appendChild(el('p', { style: 'margin:0;font-weight:700;color:#0E4D3C' }, 'Cette page est encore vide.'));
      b.appendChild(el('p', { class: 'hint', style: 'margin:4px 0 0' }, 'Ajoutez un premier bloc ci-dessous : un texte, un bouton ou un tableau.'));
      empty.appendChild(b); box.appendChild(empty);
    }
    blocks.forEach(function (b, i) { box.appendChild(blockCard(b, i)); });
  }
  function setSeg(attr, value) {
    document.querySelectorAll('[' + attr + ']').forEach(function (x) { x.setAttribute('aria-pressed', String(x.getAttribute(attr) === value)); });
  }
  function fill(p) {
    page = p;
    blocks = JSON.parse(JSON.stringify(p.blocks || []));
    vis = p.visibility; lay = p.layout;
    $('pe-title').value = p.title; $('pe-slug').value = p.slug;
    $('pe-width').value = p.width; $('pe-desc').value = p.description || '';
    $('pe-desc-n').textContent = String(($('pe-desc').value || '').length);
    setSeg('data-pe-vis', vis); setSeg('data-pe-lay', lay);
    $('pe-vis-hint').textContent = VIS_HINT[vis]; $('pe-lay-hint').textContent = LAY_HINT[lay];
    $('pe-slug-err').hidden = true;
    render();
    saved = snapshot();
    setBridge({ loaded: true, dirty: false, vis: vis });
  }

  // ---------- actions de l'en-tête
  window.saPageSave = function (publish) {
    var b = bridge();
    if (!page || (b && b.state.saving)) return;
    var title = $('pe-title').value.trim(), slug = $('pe-slug').value.trim().toLowerCase();
    if (title.length < 2) { flash('Donnez un titre à la page (2 caractères minimum).'); $('pe-title').focus(); return; }
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length < 2 || slug.length > 60) {
      var err = $('pe-slug-err'); err.textContent = 'Adresse invalide : 2 à 60 caractères, lettres minuscules sans accent, chiffres et tirets (ex. ramadan-2027).';
      err.hidden = false; $('pe-slug').focus(); return;
    }
    var badUrl = blocks.some(function (x) { return x.type === 'bouton' && x.lien && x.lien.type === 'url' && !/^https?:\/\/\S{3,}$/i.test(x.lien.url); });
    if (badUrl) { flash('Un bouton a un lien externe invalide : il doit commencer par https://'); return; }
    var body = { title: title, slug: slug, blocks: blocks, visibility: publish || vis, layout: lay, width: $('pe-width').value, description: $('pe-desc').value.trim() };
    setBridge({ saving: true });
    api('/api/admin/pages/' + id, { method: 'PUT', body: JSON.stringify(body) }).then(function (r) {
      setBridge({ saving: false });
      if (!r.ok) {
        if (r.code === 'slug_taken') { var e2 = $('pe-slug-err'); e2.textContent = r.message; e2.hidden = false; $('pe-slug').focus(); }
        flash(r.message || 'L’enregistrement a échoué. Réessayez.');
        return;
      }
      fill(r.page);
      flash(r.page.visibility === 'published' ? 'Page enregistrée et publiée à ' + r.page.url
        : r.page.visibility === 'private' ? 'Page enregistrée. Accessible à qui a le lien : ' + r.page.url
        : 'Brouillon enregistré. La page n’est pas visible du public.');
    }, function () { setBridge({ saving: false }); flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.'); });
  };
  window.saPagePreview = function () {
    if (!page) return;
    if (snapshot() !== saved) flash('L’aperçu montre la dernière version enregistrée. Enregistrez pour y voir vos changements.');
    window.open(page.url, '_blank', 'noopener');
  };

  // ---------- événements du formulaire
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-pe-add],[data-pe-vis],[data-pe-lay],#pe-copy');
    if (!t || !page) return;
    if (t.hasAttribute('data-pe-add')) {
      var k = t.getAttribute('data-pe-add');
      if (blocks.length >= 50) { flash('Une page compte au plus 50 blocs.'); return; }
      blocks.push(k === 'texte' ? { type: 'texte', titre: '', texte: '' }
        : k === 'bouton' ? { type: 'bouton', texte: '', lien: { type: 'none' }, style: 'or' }
        : { type: 'tableau', colonnes: ['', ''], lignes: [['', ''], ['', '']] });
      render(); dirtyCheck();
      flash('Bloc « ' + META[k] + ' » ajouté en bas de la page.');
      var cards = $('pe-blocks').querySelectorAll('section.card');
      var last = cards[cards.length - 1]; var f = last && last.querySelector('input,textarea'); if (f) f.focus();
    } else if (t.hasAttribute('data-pe-vis')) {
      vis = t.getAttribute('data-pe-vis'); setSeg('data-pe-vis', vis); $('pe-vis-hint').textContent = VIS_HINT[vis]; dirtyCheck();
    } else if (t.hasAttribute('data-pe-lay')) {
      lay = t.getAttribute('data-pe-lay'); setSeg('data-pe-lay', lay); $('pe-lay-hint').textContent = LAY_HINT[lay]; dirtyCheck();
    } else if (t.id === 'pe-copy') {
      var full = location.origin + page.url;
      (navigator.clipboard ? navigator.clipboard.writeText(full) : Promise.reject()).then(
        function () { t.textContent = 'Lien copié'; setTimeout(function () { t.textContent = 'Copier le lien'; }, 1800); },
        function () { flash('Copie impossible ici. Le lien est : ' + full); });
    }
  });
  document.addEventListener('input', function (e) {
    var t = e.target; if (!t || !page) return;
    if (t.id === 'pe-desc') $('pe-desc-n').textContent = String(t.value.length);
    if (t.id === 'pe-slug') $('pe-slug-err').hidden = true;
    if (['pe-title', 'pe-slug', 'pe-desc'].indexOf(t.id) > -1) dirtyCheck();
  });
  document.addEventListener('change', function (e) { if (e.target && e.target.id === 'pe-width') dirtyCheck(); });

  // ---------- chargement
  function start() {
    var miss = $('pe-missing');
    if (!id) {
      miss.textContent = 'Aucune page choisie. Revenez à « Créer une page » et cliquez sur « Modifier » à côté d’une page.';
      miss.hidden = false; setBridge({ loaded: true }); return;
    }
    Promise.all([api('/api/admin/pages/' + id), api('/api/admin/pages')]).then(function (rs) {
      var r = rs[0];
      if (!r.ok) { miss.textContent = r.message || 'Impossible de charger cette page.'; miss.hidden = false; setBridge({ loaded: true }); return; }
      customPages = rs[1].ok ? rs[1].pages : [];
      $('pe-root').hidden = false;
      fill(r.page);
    }, function () { miss.textContent = 'Impossible de joindre le serveur. Rechargez la page.'; miss.hidden = false; });
  }
  if (document.getElementById('pe-root')) start();
  else new MutationObserver(function (m, o) { if (document.getElementById('pe-root')) { o.disconnect(); start(); } })
    .observe(document.documentElement, { childList: true, subtree: true });
})();
</script>
"""

SITE_LINKS = [
    ('pg_horaires', 'Page : Horaires du mois'), ('pg_evenements', 'Page : Événements'),
    ('pg_inscription', 'Page : Inscription aux événements'), ('pg_dons', 'Page : Faire un don'),
    ('pg_campagne', 'Page : Campagne en direct'), ('pg_contact', 'Page : Contact'),
    ('pg_apropos', 'Page : À propos'), ('pg_services', 'Page : Services'), ('pg_ressources', 'Page : Ressources'),
]


def wire_editor():
    path = ROOT / 'SA-PageEditeur.dc.html'
    s, i, j, tpl = load(path)
    tpl = replace_main(tpl, EDITOR_MAIN)
    tpl = replace_component(tpl, BRIDGE)
    tpl = drop_side_sub(tpl)
    # Aperçu de la maquette (fenêtre avec contenu fictif) : remplacé par l'ouverture de /p/<lien>.
    tpl = re.sub(r'\s*<sc-if value="\{\{pv\}\}"[^>]*>.*?</sc-if>\s*(?=<sc-if value="\{\{toast\}\}")', '\n ', tpl, count=1, flags=re.S)
    tpl = tpl.replace('<span class="hide-t">Enregistrer le&nbsp;</span>brouillon', 'Enregistrer')
    tpl = re.sub(r'<style id="sa-pages-style">.*?</style>\s*', '', tpl, flags=re.S)
    k = tpl.index('</head>')
    tpl = tpl[:k] + STYLE + tpl[k:]
    tpl = inject_script(tpl, 'sa-page-editor', EDITOR_SCRIPT
                        .replace('__ICONS__', json.dumps({k: svg(k) for k in ICON}))
                        .replace('__SITE_LINKS__', json.dumps([list(x) for x in SITE_LINKS], ensure_ascii=False)))
    assert '{{pv}}' not in tpl, 'fenêtre d’aperçu de la maquette encore présente'
    save(path, s, i, j, tpl)
    print('SA-PageEditeur.dc.html : éditeur relié à la base')


# ---------------------------------------------------------------- 3. Liens de l'accueil (étape 5d)
# Panneau Accueil : 9 sélecteurs de liens. La maquette y proposait une page inventée et un
# « Lien externe… » qui s'enregistrait tel quel (bouton cassé sur l'accueil public).
HOME_LINK_FIELDS = r"""{ 'f-h1': ['hero', 'h1'], 'f-h2': ['hero', 'h2'], 'k-0': ['acces', 'cartes', 0, 'lien'],
  'k-1': ['acces', 'cartes', 1, 'lien'], 'k-2': ['acces', 'cartes', 2, 'lien'], 'f-int': ['campagne', 'btnInterac'],
  'f-sui': ['campagne', 'btnSuivre'], 'f-tous': ['annonces', 'btnTous'], 'a-l-0': ['annonces', 'items', 0, 'lien'],
  'a-l-1': ['annonces', 'items', 1, 'lien'], 'a-l-2': ['annonces', 'items', 2, 'lien'], 'f-bv': ['bienvenue', 'lien'],
  'f-inv': ['invitation', 'lien'] }"""

HOME_LINKS_SCRIPT = r"""<script id="sa-home-links">
(function () {
  var FIELDS = __FIELDS__;
  var EXT = 'Lien externe…';
  var pages = [], settings = null, prev = {};
  function get(obj, path) { return path.reduce(function (o, k) { return o == null ? o : o[k]; }, obj); }
  function opt(sel, value, text) {
    for (var i = 0; i < sel.options.length; i++) if (sel.options[i].value === value) return sel.options[i];
    var o = document.createElement('option'); o.value = value; o.textContent = text;
    var ext = null;
    for (var j = 0; j < sel.options.length; j++) if (sel.options[j].text.trim() === EXT) ext = sel.options[j];
    sel.insertBefore(o, ext);
    return o;
  }
  function apply() {
    Object.keys(FIELDS).forEach(function (id) {
      var sel = document.getElementById(id);
      if (!sel || sel.tagName !== 'SELECT') return;
      pages.forEach(function (p) { opt(sel, p.url, 'Ma page : ' + p.title); });
      var v = settings ? get(settings, FIELDS[id]) : null;
      if (typeof v === 'string' && v) {
        if (/^\/p\//.test(v)) opt(sel, v, 'Ma page : ' + v + ' (non publiée ou supprimée)');
        else if (/^https?:\/\//i.test(v)) opt(sel, v, 'Lien externe : ' + v);
        sel.value = v;
      }
      prev[id] = sel.value;
    });
  }
  // « Lien externe… » : on demande l'adresse, au lieu d'enregistrer ce texte comme lien.
  document.addEventListener('change', function (e) {
    var sel = e.target;
    if (!sel || sel.tagName !== 'SELECT' || !FIELDS[sel.id]) return;
    if (sel.options[sel.selectedIndex] && sel.options[sel.selectedIndex].text.trim() === EXT) {
      var url = (window.prompt('Adresse du lien externe (doit commencer par https://)', 'https://') || '').trim();
      if (/^https?:\/\/[^\s<>"]{3,}$/i.test(url)) {
        opt(sel, url, 'Lien externe : ' + url);
        sel.value = url;
      } else {
        sel.value = prev[sel.id] || sel.options[0].value;
        if (url && url !== 'https://') window.alert('Adresse non valide : elle doit commencer par https:// . Le lien précédent est conservé.');
      }
      sel.dispatchEvent(new Event('input', { bubbles: true }));
    }
    prev[sel.id] = sel.value;
  }, true);
  var api = function (u) { return fetch(u, { credentials: 'same-origin' }).then(function (r) { return r.json().catch(function () { return { ok: false }; }); }); };
  function start() {
    Promise.all([api('/api/admin/pages'), api('/api/admin/settings/home')]).then(function (rs) {
      pages = rs[0].ok ? rs[0].pages.filter(function (p) { return p.visibility !== 'draft'; }) : [];
      settings = rs[1].ok ? rs[1].settings : null;
      apply();
      // Les cartes et annonces sont rendues par la page : on complète leurs listes si elles réapparaissent.
      new MutationObserver(function () {
        var missing = Object.keys(FIELDS).some(function (id) {
          var s = document.getElementById(id);
          return s && s.tagName === 'SELECT' && pages.some(function (p) {
            for (var i = 0; i < s.options.length; i++) if (s.options[i].value === p.url) return false;
            return true;
          });
        });
        if (missing) apply();
      }).observe(document.documentElement, { childList: true, subtree: true });
    }, function () {});
  }
  if (document.getElementById('f-h1')) start();
  else new MutationObserver(function (m, o) { if (document.getElementById('f-h1')) { o.disconnect(); start(); } })
    .observe(document.documentElement, { childList: true, subtree: true });
})();
</script>
"""


def wire_home_links():
    path = ROOT / 'SA-Panneau.dc.html'
    s, i, j, tpl = load(path)
    n = tpl.count('<option>Ma page : Inscriptions Ramadan 2027</option>')
    tpl = tpl.replace('<option>Ma page : Inscriptions Ramadan 2027</option>', '')
    tpl = inject_script(tpl, 'sa-home-links', HOME_LINKS_SCRIPT.replace('__FIELDS__', HOME_LINK_FIELDS))
    save(path, s, i, j, tpl)
    print(f'SA-Panneau.dc.html : liens de l’accueil reliés aux pages créées ({n} options d’exemple retirées)')


if __name__ == '__main__':
    wire_list()
    wire_editor()
    wire_home_links()
