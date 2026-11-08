"""Branche « Créer une page » (étape 5b + correctifs Pièce 2) sur l'API /api/admin/pages.

1. SA-Pages.dc.html (« Mes pages ») : formulaire « Nouvelle page » (titre, adresse /p/<slug> avec
   compteur X / 60, visibilité avec Brouillon par défaut) et vraie liste des pages, avec Modifier,
   Voir, Copier le lien, Dupliquer, Supprimer (confirmation). L'en-tête global (« Tout est enregistré »,
   « Annuler les changements », « Enregistrer ») suit l'état réel de chargement et du formulaire.
2. SA-PageEditeur.dc.html (éditeur, ?id=<page>) : titre (compteur X / 120), blocs Texte / Bouton /
   Tableau / Photo / Vidéo / Formulaire / Widget (étapes M1 à M5) (+ Ligne, + Colonne, − Dernière ligne, − Dernière colonne, et suppression par ligne/colonne),
   lien de la page (compteur X / 60), visibilité (Brouillon / Publiée / Lien privé), mise en page,
   largeur, description (compteur X / 160), suppression de la page avec confirmation, et barre
   d'enregistrement cohérente en haut ET en bas de page.
3. SA-Panneau.dc.html (étape 5d) : les pages créées (publiées ou lien privé) sont proposées dans
   les 7 sélecteurs de liens de l'accueil ; « Lien externe… » demande l'adresse ; la page
   d'exemple « Inscriptions Ramadan 2027 » est retirée.

Dans SA-Pages et SA-PageEditeur, le composant de la maquette est remplacé par un composant minimal qui
gère l'en-tête et les messages ; le contenu attend que React ait monté #dc-root avant de s'initialiser.
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

# Styles communs ajoutés aux deux pages (bouton danger, pastilles de statut, éditeur responsive, barre de bas de page).
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
.pe-table td,.pe-table th{padding:6px;border-bottom:1px solid #F3EAD8;vertical-align:middle}
.pe-table th{background:#FAF6EC}
.pe-table .in{min-width:120px}
.pe-col-h{display:flex;align-items:center;gap:4px}
.pe-col-h .in{flex:1}
.pe-mini-del{min-width:30px;height:30px;padding:0 6px;border-radius:8px;border:1px solid #E9B4AF;background:#fff;color:#B3261E;font-weight:700;cursor:pointer;line-height:1}
.pe-mini-del:hover{background:#FBEAE8}
.pe-mini-del:disabled{opacity:.35;cursor:not-allowed}
.pe-slug{display:flex;align-items:center;gap:6px}
.pe-slug span{color:#4F5E57;font-weight:600}
.pe-slug .in{flex:1;min-width:0}
.pe-bottom-bar{grid-column:1 / -1;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px 16px;padding:14px 18px;border:1px solid #E4D9C0;border-radius:14px;background:#fff}
</style>
'''


def svg(name):
    return ('<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + ICON[name] + '</svg>')


# ---------------------------------------------------------------- composant minimal
# Ne gère que l'en-tête (statut, boutons) et les messages ; window.__saPage n'est exposé qu'une fois
# le composant réellement monté dans #dc-root (componentDidMount), pour éviter toute écriture dans <x-dc>.
BRIDGE = """
class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.state = { loaded: false, dirty: false, saving: false, vis: 'draft', toast: '' };
  }
  componentDidMount() {
    window.__saPage = this;
    window.dispatchEvent(new Event('sa-page-ready'));
  }
  componentWillUnmount() {
    clearTimeout(this.tt);
    if (window.__saPage === this) window.__saPage = null;
  }
  flash(m) {
    this.setState({ toast: m });
    clearTimeout(this.tt);
    this.tt = setTimeout(() => this.setState({ toast: '' }), 3200);
  }
  renderVals() {
    const st = this.state;
    const isList = st.vis === 'list';
    const label = !st.loaded ? 'Chargement…'
      : st.saving ? 'Enregistrement…'
      : st.dirty ? 'Changements non enregistrés'
      : isList ? 'Tout est enregistré'
      : st.vis === 'published' ? 'Publiée · tout est enregistré'
      : st.vis === 'private' ? 'Lien privé · tout est enregistré'
      : 'Brouillon · tout est enregistré';
    const pubLabel = st.saving ? 'Enregistrement…'
      : isList ? 'Enregistrer'
      : st.vis === 'draft' ? 'Enregistrer le brouillon'
      : st.vis === 'private' ? 'Mettre à jour (lien privé)'
      : 'Mettre à jour';
    const call = (name, arg) => () => { if (typeof window[name] === 'function') window[name](arg); };
    return {
      dot: !st.loaded || st.dirty || st.saving ? '#C49A4A' : '#7FB89F',
      statusTxt: label,
      clean: !st.loaded || st.saving || !st.dirty,
      save: call('saPageSave'),
      undo: call('saPageUndo'),
      saveDraft: call('saPageSave'),
      publish: call('saPageSave'),
      pubLabel: pubLabel,
      openPv: call('saPagePreview'),
      toast: st.toast
    };
  }
}
"""


# ---------------------------------------------------------------- 1. Mes pages
LIST_MAIN = '''
   <div><p class="eyebrow">Rubrique du menu</p><h1 class="serif ttl-page">Créer une page</h1>
   <p style="margin:6px 0 0;color:#4F5E57;max-width:640px">Ajoutez une page complète sans toucher au code : texte, boutons, tableaux, photos, vidéos, formulaires et widgets. Chaque page a son adresse, en brouillon par défaut tant que vous ne la publiez pas.</p></div>
   <section class="card" aria-labelledby="np-t"><div class="card-h"><span class="num" aria-hidden="true">1</span><div><h2 class="ttl" id="np-t">Nouvelle page</h2>
   <p class="dsc">Elle démarre en brouillon par défaut (invisible du public). Vous pouvez choisir son lien et sa visibilité dès maintenant, puis la remplir dans l’éditeur.</p></div></div>
   <div class="card-b"><form id="np-form" novalidate style="display:flex;flex-direction:column;gap:14px;margin-top:10px">
    <div class="g2" style="align-items:start">
     <div class="fld"><label class="lbl" for="np-title">Titre de la page</label>
      <input class="in" id="np-title" type="text" maxlength="120" placeholder="Ex. Inscriptions Ramadan 2027" aria-describedby="np-title-hint np-msg">
      <p class="hint" id="np-title-hint"><span id="np-title-n"></span> / 120 caractères.</p></div>
     <div class="fld"><label class="lbl" for="np-slug">Adresse (lien de la page)</label>
      <div class="pe-slug"><span aria-hidden="true">/p/</span><input class="in pg-mono" id="np-slug" type="text" maxlength="60" placeholder="ex. inscriptions-ramadan-2027" aria-describedby="np-slug-hint np-msg" autocomplete="off" spellcheck="false"></div>
      <p class="hint" id="np-slug-hint"><span id="np-slug-n"></span> / 60 caractères · Lettres minuscules, chiffres et tirets (généré automatiquement depuis le titre si laissé tel quel).</p></div>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:14px 24px;align-items:flex-end;justify-content:space-between">
     <div class="fld" style="flex:1 1 280px"><span class="lbl" id="np-vis-l">Visibilité au départ</span>
      <div class="seg" role="group" aria-labelledby="np-vis-l" style="flex-wrap:wrap;align-self:flex-start">
       <button type="button" data-np-vis="draft" aria-pressed="true">Brouillon</button>
       <button type="button" data-np-vis="published" aria-pressed="false">Publiée</button>
       <button type="button" data-np-vis="private" aria-pressed="false">Lien privé</button></div>
      <p class="hint" id="np-vis-hint"></p></div>
     <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
      <button type="button" class="btn btn-line" id="np-reset" disabled style="min-height:48px">Annuler</button>
      <button type="submit" class="btn btn-gold" id="np-btn" style="min-height:48px">Créer la page</button></div>
    </div>
   </form>
   <p id="np-msg" class="pg-err" role="alert" hidden style="margin-top:10px"></p></div></section>
   <section class="card" aria-labelledby="pl-t"><div class="card-h"><span class="num" aria-hidden="true">2</span><div><h2 class="ttl" id="pl-t">Pages créées</h2>
   <p class="dsc" id="pl-count"></p></div></div>
   <div class="card-b"><ul class="pg-list" id="pl-list"></ul><p id="pl-msg" role="status" aria-live="polite" class="hint" style="margin:10px 0 0"></p></div></section>
'''

LIST_SCRIPT = r"""<script id="sa-pages-list">
(function () {
  var VIS = { draft: 'Brouillon', published: 'Publiée', private: 'Lien privé' };
  var VIS_HINT = {
    draft: 'Recommandé : la nouvelle page démarre en brouillon, visible seulement dans le superadmin.',
    published: 'La page sera publiée dès sa création à son adresse /p/…',
    private: 'Accessible uniquement aux personnes qui ont le lien. Google ne l’indexe pas.'
  };
  var ICON = __ICONS__;
  var pages = [];
  var npVis = 'draft';
  var slugTouched = false;
  function $(id) { return document.getElementById(id); }
  function bridge() { return window.__saPage; }
  function setBridge(st) { var b = bridge(); if (b) b.setState(st); }
  function flash(m) { var b = bridge(); if (b) b.flash(m); else { var p = $('pl-msg'); if (p) p.textContent = m; } }
  function slugify(text) {
    return String(text || '')
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .toLowerCase().replace(/['’]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
      .slice(0, 60).replace(/-+$/g, '');
  }
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
  function setNpVis(v) {
    npVis = VIS[v] ? v : 'draft';
    document.querySelectorAll('[data-np-vis]').forEach(function (btn) {
      btn.setAttribute('aria-pressed', String(btn.getAttribute('data-np-vis') === npVis));
    });
    if ($('np-vis-hint')) $('np-vis-hint').textContent = VIS_HINT[npVis];
  }
  function syncFormUi() {
    var t = $('np-title'), s = $('np-slug'), rst = $('np-reset');
    var tLen = t ? t.value.length : 0;
    var sLen = s ? s.value.length : 0;
    if ($('np-title-n')) $('np-title-n').textContent = String(tLen);
    if ($('np-slug-n')) $('np-slug-n').textContent = String(sLen);
    var dirty = (t && t.value.trim().length > 0) || (s && s.value.trim().length > 0) || npVis !== 'draft';
    if (rst) rst.disabled = !dirty;
    setBridge({ loaded: true, vis: 'list', dirty: !!dirty });
  }
  function resetForm(notify) {
    var t = $('np-title'), s = $('np-slug'), msg = $('np-msg');
    if (t) { t.value = ''; t.removeAttribute('aria-invalid'); }
    if (s) { s.value = ''; s.removeAttribute('aria-invalid'); }
    if (msg) msg.hidden = true;
    slugTouched = false;
    setNpVis('draft');
    syncFormUi();
    if (notify) flash('Formulaire réinitialisé.');
  }
  function render() {
    var ul = $('pl-list'); if (!ul) return;
    ul.innerHTML = '';
    var n = pages.length;
    if ($('pl-count')) {
      $('pl-count').textContent = n ? n + (n > 1 ? ' pages' : ' page') + ' · le lien et la visibilité de chaque page se modifient dans son éditeur.' : 'Aucune page pour l’instant.';
    }
    if (!n) {
      var li = el('li', { class: 'pg-item' });
      li.appendChild(el('p', { class: 'hint', style: 'margin:0' },
        'Vos pages apparaîtront ici. Donnez un titre ci-dessus et cliquez sur « Créer la page » : elle démarre en brouillon par défaut, invisible du public.'));
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
    if ($('pl-count') && !pages.length) $('pl-count').textContent = 'Chargement des pages…';
    api('/api/admin/pages').then(function (r) {
      setBridge({ loaded: true, vis: 'list' });
      if (!r.ok) {
        if ($('pl-count')) $('pl-count').textContent = r.message || 'Impossible de charger les pages. Rechargez la page.';
        return;
      }
      pages = r.pages || [];
      render();
    }, function () {
      setBridge({ loaded: true, vis: 'list' });
      if ($('pl-count')) $('pl-count').textContent = 'Impossible de joindre le serveur. Rechargez la page.';
    });
  }
  function submitNewPage() {
    var t = $('np-title'), s = $('np-slug'), btn = $('np-btn'), msg = $('np-msg');
    if (!t || !btn || btn.getAttribute('aria-busy') === 'true') return;
    msg.hidden = true;
    t.removeAttribute('aria-invalid');
    if (s) s.removeAttribute('aria-invalid');
    var title = t.value.trim();
    if (title.length < 2) {
      t.setAttribute('aria-invalid', 'true');
      msg.textContent = 'Donnez un titre à la page (2 caractères minimum).';
      msg.hidden = false;
      t.focus();
      return;
    }
    var rawSlug = s ? s.value.trim().toLowerCase() : '';
    if (rawSlug && (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(rawSlug) || rawSlug.length < 2 || rawSlug.length > 60)) {
      if (s) { s.setAttribute('aria-invalid', 'true'); s.focus(); }
      msg.textContent = 'Le lien doit faire 2 à 60 caractères : lettres minuscules sans accent, chiffres et tirets (ex. ramadan-2027).';
      msg.hidden = false;
      return;
    }
    var payload = { title: title, visibility: npVis || 'draft' };
    if (rawSlug) payload.slug = rawSlug;
    btn.setAttribute('aria-busy', 'true');
    btn.textContent = 'Création…';
    setBridge({ saving: true });
    api('/api/admin/pages', { method: 'POST', body: JSON.stringify(payload) }).then(function (r) {
      setBridge({ saving: false });
      if (r.ok) { location.href = 'SA-PageEditeur.dc.html?id=' + r.page.id; return; }
      btn.removeAttribute('aria-busy');
      btn.textContent = 'Créer la page';
      if (r.code === 'slug_taken' && s) { s.setAttribute('aria-invalid', 'true'); s.focus(); }
      msg.textContent = r.message || 'La création a échoué. Réessayez.';
      msg.hidden = false;
    }, function () {
      setBridge({ saving: false });
      btn.removeAttribute('aria-busy');
      btn.textContent = 'Créer la page';
      msg.textContent = 'Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.';
      msg.hidden = false;
    });
  }
  window.saPageSave = function () { submitNewPage(); };
  window.saPageUndo = function () { resetForm(true); };
  document.addEventListener('submit', function (e) {
    if (!e.target || e.target.id !== 'np-form') return;
    e.preventDefault();
    submitNewPage();
  });
  document.addEventListener('input', function (e) {
    var t = e.target;
    if (!t) return;
    if (t.id === 'np-title') {
      t.removeAttribute('aria-invalid');
      if ($('np-msg')) $('np-msg').hidden = true;
      var s = $('np-slug');
      if (s && !slugTouched) {
        s.value = t.value.trim() ? slugify(t.value) : '';
      }
      syncFormUi();
    } else if (t.id === 'np-slug') {
      t.removeAttribute('aria-invalid');
      if ($('np-msg')) $('np-msg').hidden = true;
      slugTouched = t.value.trim().length > 0;
      syncFormUi();
    }
  });
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('[data-np-vis],#np-reset');
    if (!btn) return;
    if (btn.hasAttribute('data-np-vis')) {
      setNpVis(btn.getAttribute('data-np-vis'));
      syncFormUi();
    } else if (btn.id === 'np-reset') {
      resetForm(true);
    }
  });
  var started = false;
  function start() {
    setNpVis('draft');
    syncFormUi();
    load();
  }
  function tryStart() {
    if (started || document.querySelector('x-dc') || !window.__saPage || !$('pl-list')) return;
    started = true;
    start();
  }
  window.addEventListener('sa-page-ready', tryStart);
  tryStart();
  if (!started) {
    new MutationObserver(function (m, o) {
      if (!document.querySelector('x-dc') && window.__saPage && $('pl-list')) {
        o.disconnect();
        tryStart();
      }
    }).observe(document.documentElement, { childList: true, subtree: true });
  }
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
     <input class="in" id="pe-title" type="text" maxlength="120" aria-describedby="pe-title-hint" style="font-size:22px;font-weight:700;color:#0E4D3C;min-height:56px">
     <p class="hint" id="pe-title-hint"><span id="pe-title-n"></span> / 120 caractères.</p></div>
     <div id="pe-blocks" style="display:flex;flex-direction:column;gap:14px"></div>
     <section class="card" aria-labelledby="pe-add-t"><div class="card-b">
      <h2 class="ttl" id="pe-add-t" style="margin:0">Ajouter un bloc</h2>
      <p class="hint" style="margin:4px 0 0">Les blocs s’affichent dans cet ordre sur la page. Changez l’ordre avec les flèches.</p>
      <div class="pe-add"><button type="button" class="btn btn-line" data-pe-add="texte">+ Texte</button>
      <button type="button" class="btn btn-line" data-pe-add="bouton">+ Bouton</button>
      <button type="button" class="btn btn-line" data-pe-add="tableau">+ Tableau</button>
      <button type="button" class="btn btn-line" data-pe-add="photo">+ Photo</button>
      <button type="button" class="btn btn-line" data-pe-add="video">+ Vidéo</button>
      <button type="button" class="btn btn-line" data-pe-add="formulaire">+ Formulaire</button>
      <button type="button" class="btn btn-line" data-pe-add="widget">+ Widget</button></div>
     </div></section>
    </div>
    <aside aria-label="Réglages de la page" style="display:flex;flex-direction:column;gap:14px;min-width:0">
     <section class="card" aria-labelledby="pe-link-t"><div class="card-b">
      <h2 class="ttl" id="pe-link-t" style="margin:0 0 8px">Lien de la page</h2>
      <div class="fld"><label class="lbl" for="pe-slug">Adresse</label>
      <div class="pe-slug"><span aria-hidden="true">/p/</span><input class="in pg-mono" id="pe-slug" type="text" maxlength="60" aria-describedby="pe-slug-hint pe-slug-err" autocomplete="off" spellcheck="false"></div>
      <p class="hint" id="pe-slug-hint"><span id="pe-slug-n"></span> / 60 caractères · Lettres minuscules, chiffres et tirets. Si vous la changez, l’ancienne adresse redirige vers la nouvelle.</p>
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
      <div style="margin-top:12px;padding-top:12px;border-top:1px solid #F3EAD8;display:flex;flex-direction:column;gap:8px">
       <button type="button" class="btn btn-gold" id="pe-save-pub" disabled style="width:100%">Enregistrer le brouillon</button>
       <button type="button" class="btn btn-line" id="pe-undo-pub" disabled style="width:100%">Annuler les changements</button>
       <p class="hint" id="pe-pub-status" style="margin:0;text-align:center"></p>
      </div>
     </div></section>
     <section class="card" aria-labelledby="pe-seo-t"><div class="card-b">
      <h2 class="ttl" id="pe-seo-t" style="margin:0 0 8px">Partage et Google</h2>
      <div class="fld"><label class="lbl" for="pe-desc">Description courte</label>
      <textarea class="in" id="pe-desc" rows="3" maxlength="160" aria-describedby="pe-desc-hint" style="min-height:84px;resize:vertical"></textarea>
      <p class="hint" id="pe-desc-hint">Affichée par Google et sur Facebook. <span id="pe-desc-n"></span> / 160 caractères.</p></div>
     </div></section>
    </aside>
    <section class="pe-bottom-bar" id="pe-bottom-bar" aria-label="Actions de la page">
     <div style="display:flex;flex-wrap:wrap;align-items:center;gap:12px">
      <span id="pe-bottom-status" style="font-weight:700;color:#0E4D3C;font-size:14px"></span>
      <button type="button" class="btn btn-line" id="pe-delete" style="color:#B3261E;border-color:#E9B4AF">Supprimer cette page</button>
     </div>
     <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
      <button type="button" class="btn btn-line" id="pe-pv-bottom">Aperçu</button>
      <button type="button" class="btn btn-line" id="pe-undo-bottom" disabled>Annuler les changements</button>
      <button type="button" class="btn btn-gold" id="pe-save-bottom" disabled>Enregistrer le brouillon</button>
     </div>
    </section>
   </div>
'''

EDITOR_SCRIPT = r"""<script id="sa-page-editor">
(function () {
  var ICON = __ICONS__;
  var SITE_LINKS = __SITE_LINKS__;
  var VIS_HINT = {
    draft: 'Visible seulement dans le superadmin. Cliquez sur « Enregistrer le brouillon » pour garder la page en brouillon.',
    published: 'Visible par tous à son adresse dès l’enregistrement.',
    private: 'Accessible seulement à qui a le lien. Google ne la voit pas.'
  };
  var LAY_HINT = { site: 'La page garde le menu, le logo et le pied de page du site.', blank: 'Sans menu ni pied de page : idéal pour un outil ou un tableau.' };
  var META = { texte: 'Texte', bouton: 'Bouton', tableau: 'Tableau', photo: 'Photo', video: 'Vidéo', formulaire: 'Formulaire', widget: 'Widget' };
  var me = null, media = [], mediaNotice = '', storage = false, widgets = {}, forms = [];
  function isSuper() { return !!(me && me.role === 'superadmin'); }
  function mediaById(mid) { for (var k = 0; k < media.length; k++) if (media[k].id === mid) return media[k]; return null; }
  function widgetList() { return Object.keys(widgets).map(function (k) { return widgets[k]; }).sort(function (a, c) { return c.id - a.id; }); }
  function widgetDraft(w) {
    return w ? { title: w.title || '', lang: w.lang || 'web', html: w.html || '', css: w.css || '', js: w.js || '', net: !!w.net, height: w.height || 400 }
      : { title: '', lang: 'web', html: '', css: '', js: '', net: false, height: 300 };
  }
  function stripBlocks(list) {
    return list.map(function (b) { var c = {}; Object.keys(b).forEach(function (k) { if (k !== '_w') c[k] = b[k]; }); return c; });
  }
  // Widgets nouveaux ou modifiés : enregistrés un par un AVANT la page (la page ne garde que leur numéro).
  function saveWidgets() {
    if (!isSuper()) return Promise.resolve();
    var jobs = blocks.filter(function (b) {
      return b.type === 'widget' && b._w && (!b.widget || !widgets[b.widget] || JSON.stringify(widgetDraft(widgets[b.widget])) !== JSON.stringify(b._w));
    });
    return jobs.reduce(function (p, b) {
      return p.then(function () {
        var exists = b.widget && widgets[b.widget];
        return api(exists ? '/api/admin/widgets/' + b.widget : '/api/admin/widgets', { method: exists ? 'PUT' : 'POST', body: JSON.stringify(b._w) }).then(function (r) {
          if (!r.ok) throw new Error(r.message || 'Le widget n’a pas pu être enregistré. Réessayez.');
          widgets[r.widget.id] = r.widget;
          b.widget = r.widget.id;
        });
      });
    }, Promise.resolve());
  }
  // Même règle que le serveur (functions/_lib/video.js) : YouTube, Vimeo ou Facebook seulement.
  function parseVideo(raw) {
    var u; try { u = new URL(String(raw || '').trim()); } catch (e) { return null; }
    if (u.protocol !== 'https:' && u.protocol !== 'http:') return null;
    var host = u.hostname.replace(/^(www\.|m\.)/, '').toLowerCase();
    var yt = function (vid) { return /^[A-Za-z0-9_-]{11}$/.test(vid || '') ? { provider: 'YouTube', embed: 'https://www.youtube-nocookie.com/embed/' + vid } : null; };
    if (host === 'youtu.be') return yt(u.pathname.split('/')[1]);
    if (host === 'youtube.com' || host === 'youtube-nocookie.com' || host === 'music.youtube.com') {
      if (u.pathname === '/watch') return yt(u.searchParams.get('v'));
      var m = /^\/(?:embed|shorts|live|v)\/([^/?#]+)/.exec(u.pathname);
      return m ? yt(m[1]) : null;
    }
    if (host === 'vimeo.com' || host === 'player.vimeo.com') {
      var mv = /\/(?:video\/)?(\d{5,12})(?:\/|$)/.exec(u.pathname);
      return mv ? { provider: 'Vimeo', embed: 'https://player.vimeo.com/video/' + mv[1] + '?dnt=1' } : null;
    }
    if (host === 'facebook.com' || host === 'fb.watch') {
      if (host === 'facebook.com' && !/\/(videos|watch|reel)\b/.test(u.pathname + u.search)) return null;
      var clean = 'https://' + (host === 'fb.watch' ? 'fb.watch' : 'www.facebook.com') + u.pathname + (u.pathname === '/watch/' || u.pathname === '/watch' ? u.search : '');
      return { provider: 'Facebook', embed: 'https://www.facebook.com/plugins/video.php?href=' + encodeURIComponent(clean) + '&show_text=false' };
    }
    return null;
  }
  var id = parseInt(new URLSearchParams(location.search).get('id'), 10);
  var page = null, blocks = [], saved = '', customPages = [], vis = 'draft', lay = 'site', isSaving = false;
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

  function normTable(b) {
    if (!Array.isArray(b.colonnes) || !b.colonnes.length) b.colonnes = ['', ''];
    b.colonnes = b.colonnes.slice(0, 8).map(function (c) { return typeof c === 'string' ? c : ''; });
    var n = b.colonnes.length;
    if (!Array.isArray(b.lignes) || !b.lignes.length) {
      b.lignes = [b.colonnes.map(function () { return ''; })];
    } else {
      b.lignes = b.lignes.slice(0, 100).map(function (r) {
        var row = Array.isArray(r) ? r.slice(0, n).map(function (c) { return typeof c === 'string' ? c : ''; }) : [];
        while (row.length < n) row.push('');
        return row;
      });
    }
    return b;
  }

  // ---------- compteurs et état
  function updateCounters() {
    if ($('pe-title-n') && $('pe-title')) $('pe-title-n').textContent = String(($('pe-title').value || '').length);
    if ($('pe-slug-n') && $('pe-slug')) $('pe-slug-n').textContent = String(($('pe-slug').value || '').length);
    if ($('pe-desc-n') && $('pe-desc')) $('pe-desc-n').textContent = String(($('pe-desc').value || '').length);
  }
  function snapshot() {
    if (!$('pe-title') || !$('pe-slug') || !$('pe-width') || !$('pe-desc')) return saved;
    return JSON.stringify({
      title: $('pe-title').value.trim(),
      slug: $('pe-slug').value.trim().toLowerCase(),
      blocks: blocks,
      visibility: vis,
      layout: lay,
      width: $('pe-width').value,
      description: $('pe-desc').value.trim()
    });
  }
  function syncActionUi() {
    var dirty = page ? snapshot() !== saved : false;
    setBridge({ loaded: true, dirty: dirty, saving: isSaving, vis: vis });
    var saveLbl = isSaving ? 'Enregistrement…'
      : vis === 'draft' ? 'Enregistrer le brouillon'
      : vis === 'private' ? 'Mettre à jour (lien privé)'
      : 'Mettre à jour';
    var statusTxt = isSaving ? 'Enregistrement…'
      : dirty ? 'Changements non enregistrés'
      : vis === 'published' ? 'Publiée · tout est enregistré'
      : vis === 'private' ? 'Lien privé · tout est enregistré'
      : 'Brouillon · tout est enregistré';
    ['pe-save-bottom', 'pe-save-pub'].forEach(function (btnId) {
      var btn = $(btnId);
      if (btn) { btn.disabled = !page || isSaving || !dirty; btn.textContent = saveLbl; }
    });
    ['pe-undo-bottom', 'pe-undo-pub'].forEach(function (btnId) {
      var btn = $(btnId);
      if (btn) btn.disabled = !page || isSaving || !dirty;
    });
    if ($('pe-bottom-status')) {
      $('pe-bottom-status').textContent = statusTxt;
      $('pe-bottom-status').style.color = dirty ? '#7A5A1E' : '#0E4D3C';
    }
    if ($('pe-pub-status')) {
      $('pe-pub-status').textContent = statusTxt + ' · boutons d’enregistrement disponibles ici, en haut et en bas de page.';
    }
  }
  function dirtyCheck() {
    updateCounters();
    syncActionUi();
  }
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

    var on = function (input, fn) {
      input.addEventListener('input', function () { fn(input.value); dirtyCheck(); });
      input.addEventListener('change', function () { fn(input.value); dirtyCheck(); });
    };
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
      normTable(b);
      var dim = el('p', { class: 'hint', style: 'margin:6px 0 0' },
        b.lignes.length + (b.lignes.length > 1 ? ' lignes' : ' ligne') + ' × ' +
        b.colonnes.length + (b.colonnes.length > 1 ? ' colonnes' : ' colonne'));
      body.appendChild(dim);
      var wrap = el('div', { class: 'pe-table', tabindex: '0', 'aria-label': 'Tableau du bloc ' + (i + 1) + ', défilable horizontalement' });
      var table = el('table'); var thead = el('thead'); var hr = el('tr');
      b.colonnes.forEach(function (c, ci) {
        var th = el('th', { scope: 'col' });
        var ch = el('div', { class: 'pe-col-h' });
        var inp = el('input', { class: 'in', type: 'text', maxlength: '80', 'aria-label': 'Titre de la colonne ' + (ci + 1), placeholder: 'Colonne ' + (ci + 1) });
        inp.value = c; on(inp, function (v) { b.colonnes[ci] = v; });
        ch.appendChild(inp);
        var rmCol = el('button', {
          type: 'button',
          class: 'pe-mini-del',
          title: 'Retirer la colonne ' + (ci + 1),
          'aria-label': 'Retirer la colonne ' + (ci + 1)
        }, '−');
        rmCol.disabled = b.colonnes.length <= 1;
        rmCol.addEventListener('click', function () {
          if (b.colonnes.length <= 1) return;
          b.colonnes.splice(ci, 1);
          b.lignes.forEach(function (r) { r.splice(ci, 1); });
          render(); dirtyCheck();
        });
        ch.appendChild(rmCol);
        th.appendChild(ch); hr.appendChild(th);
      });
      var thAct = el('th', { scope: 'col', style: 'width:40px;text-align:center;color:#4F5E57;font-size:12px' }, 'Ligne');
      hr.appendChild(thAct);
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
        var tdAct = el('td', { style: 'text-align:center;width:40px' });
        var rmRow = el('button', {
          type: 'button',
          class: 'pe-mini-del',
          title: 'Retirer la ligne ' + (ri + 1),
          'aria-label': 'Retirer la ligne ' + (ri + 1)
        }, '−');
        rmRow.disabled = b.lignes.length <= 1;
        rmRow.addEventListener('click', function () {
          if (b.lignes.length <= 1) return;
          b.lignes.splice(ri, 1);
          render(); dirtyCheck();
        });
        tdAct.appendChild(rmRow);
        tr.appendChild(tdAct);
        tb.appendChild(tr);
      });
      table.appendChild(tb); wrap.appendChild(table); body.appendChild(wrap);
      var tools = el('div', { class: 'pe-add' });
      var tool = function (label, enabled, fn) {
        var x = el('button', { type: 'button', class: 'btn btn-line' }, label);
        x.disabled = !enabled;
        x.addEventListener('click', function () { fn(); render(); dirtyCheck(); });
        tools.appendChild(x);
      };
      tool('+ Ligne', b.lignes.length < 100, function () {
        b.lignes.push(b.colonnes.map(function () { return ''; }));
      });
      tool('+ Colonne', b.colonnes.length < 8, function () {
        b.colonnes.push('');
        b.lignes.forEach(function (r) { r.push(''); });
      });
      tool('− Dernière ligne', b.lignes.length > 1, function () {
        if (b.lignes.length > 1) b.lignes.pop();
      });
      tool('− Dernière colonne', b.colonnes.length > 1, function () {
        if (b.colonnes.length > 1) {
          b.colonnes.pop();
          b.lignes.forEach(function (r) { r.pop(); });
        }
      });
      body.appendChild(tools);
    } else if (b.type === 'photo') {
      if (!storage) body.appendChild(el('p', { class: 'pg-err', style: 'margin-top:8px' }, mediaNotice || 'Le stockage des photos n’est pas relié au site : créez le bucket R2 « ascil-medias » dans Cloudflare, puis redéployez.'));
      var cur = mediaById(b.media);
      if (cur) {
        var pv = el('img', { src: cur.url, alt: '', style: 'display:block;max-width:100%;max-height:220px;margin-top:10px;border-radius:12px;border:1px solid #E4D9C0' });
        body.appendChild(pv);
      }
      var ps = el('select', { class: 'in', id: nid('m') });
      ps.appendChild(el('option', { value: '' }, media.length ? 'Choisir une photo déjà envoyée…' : 'Aucune photo envoyée pour l’instant'));
      media.forEach(function (m) {
        ps.appendChild(el('option', { value: String(m.id) }, (m.name || ('Photo ' + m.id)) + (m.width ? ' · ' + m.width + ' × ' + m.height : '') + ' · ' + Math.max(1, Math.round(m.size / 1024)) + ' ko'));
      });
      ps.value = b.media ? String(b.media) : '';
      ps.addEventListener('change', function () { b.media = ps.value ? parseInt(ps.value, 10) : null; render(); dirtyCheck(); });
      body.appendChild(field('Photo', ps));
      var up = el('input', { type: 'file', id: nid('f'), accept: 'image/jpeg,image/png,image/webp,image/gif', class: 'in', style: 'padding:10px' });
      up.disabled = !storage;
      var upMsg = el('p', { class: 'hint', role: 'status', 'aria-live': 'polite' }, 'JPEG, PNG, WebP ou GIF · 5 Mo au plus.');
      up.addEventListener('change', function () {
        var file = up.files && up.files[0];
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) { upMsg.textContent = 'Cette photo dépasse 5 Mo. Réduisez-la, puis réessayez.'; up.value = ''; return; }
        upMsg.textContent = 'Envoi de la photo…';
        up.disabled = true;
        fetch('/api/admin/media', { method: 'POST', credentials: 'same-origin', body: file,
          headers: { 'Content-Type': file.type || 'application/octet-stream', 'X-File-Name': encodeURIComponent(file.name || '') } })
          .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
          .then(function (r) {
            up.disabled = false; up.value = '';
            if (!r.ok) { upMsg.textContent = r.message || 'L’envoi a échoué. Réessayez.'; return; }
            media.unshift(r.media);
            b.media = r.media.id;
            render(); dirtyCheck();
            flash('Photo envoyée. Décrivez-la dans « Texte alternatif », puis enregistrez la page.');
          }, function () { up.disabled = false; upMsg.textContent = 'Impossible de joindre le serveur. Réessayez.'; });
      });
      var upF = field('Ou envoyer une nouvelle photo', up); upF.appendChild(upMsg);
      body.appendChild(upF);
      var alt = el('input', { class: 'in', type: 'text', id: nid('a'), maxlength: '200', placeholder: 'Ex. La salle de prière pendant le Ramadan' }); alt.value = b.alt || '';
      on(alt, function (v) { b.alt = v; });
      body.appendChild(field('Texte alternatif (obligatoire)', alt, 'Décrit la photo pour les personnes aveugles et pour Google.'));
      var leg = el('input', { class: 'in', type: 'text', id: nid('c'), maxlength: '200' }); leg.value = b.legende || '';
      on(leg, function (v) { b.legende = v; });
      body.appendChild(field('Légende (facultative)', leg, 'Affichée sous la photo.'));
      var tl = el('select', { class: 'in', id: nid('z') });
      [['pleine', 'Pleine largeur'], ['moyenne', 'Moyenne'], ['petite', 'Petite']].forEach(function (x) { tl.appendChild(el('option', { value: x[0] }, x[1])); });
      tl.value = b.taille || 'pleine';
      tl.addEventListener('change', function () { b.taille = tl.value; dirtyCheck(); });
      body.appendChild(field('Taille', tl));
      if (cur) {
        var rm = el('button', { type: 'button', class: 'btn btn-line', style: 'color:#B3261E;border-color:#E9B4AF;align-self:flex-start;margin-top:8px' }, 'Supprimer cette photo du stockage');
        rm.addEventListener('click', function () {
          if (!window.confirm('Supprimer définitivement la photo « ' + (cur.name || cur.id) + ' » ?\n\nToutes les pages qui l’affichent ne la montreront plus. Cette action est irréversible.')) return;
          api('/api/admin/media/' + cur.id, { method: 'DELETE' }).then(function (r) {
            if (!r.ok) { flash(r.message || 'La suppression a échoué. Réessayez.'); return; }
            media = media.filter(function (m) { return m.id !== cur.id; });
            blocks.forEach(function (x) { if (x.type === 'photo' && x.media === cur.id) x.media = null; });
            render(); dirtyCheck();
            flash('Photo supprimée du stockage. Enregistrez la page pour garder ce changement.');
          }, function () { flash('Impossible de joindre le serveur. Réessayez.'); });
        });
        body.appendChild(rm);
      }
    } else if (b.type === 'video') {
      var vu = el('input', { class: 'in', type: 'url', id: nid('v'), maxlength: '500', placeholder: 'https://www.youtube.com/watch?v=…' }); vu.value = b.url || '';
      var vMsg = el('p', { class: 'hint', role: 'status', 'aria-live': 'polite' });
      var vBox = el('div', { style: 'margin-top:10px' });
      var syncVideo = function () {
        var v = parseVideo(vu.value);
        vBox.innerHTML = '';
        if (!vu.value.trim()) { vMsg.textContent = 'Collez le lien d’une vidéo YouTube, Vimeo ou Facebook.'; return; }
        if (!v) { vMsg.textContent = 'Lien non reconnu : collez un lien YouTube, Vimeo ou Facebook (par exemple https://youtu.be/…).'; return; }
        vMsg.textContent = 'Vidéo ' + v.provider + ' reconnue. Aperçu ci-dessous.';
        var fr = el('iframe', { src: v.embed, title: 'Aperçu de la vidéo', loading: 'lazy', allow: 'encrypted-media; picture-in-picture; fullscreen',
          style: 'display:block;width:100%;max-width:480px;aspect-ratio:16/9;border:0;border-radius:12px;background:#1E2B26' });
        vBox.appendChild(fr);
      };
      vu.addEventListener('input', function () { b.url = vu.value.trim(); vMsg.textContent = ''; dirtyCheck(); });
      vu.addEventListener('change', function () { b.url = vu.value.trim(); syncVideo(); dirtyCheck(); });
      var vf = field('Lien de la vidéo', vu); vf.appendChild(vMsg);
      body.appendChild(vf);
      var vt = el('input', { class: 'in', type: 'text', id: nid('vt'), maxlength: '120', placeholder: 'Ex. Khutba du vendredi 6 novembre' }); vt.value = b.titre || '';
      on(vt, function (v) { b.titre = v; });
      body.appendChild(field('Titre de la vidéo (facultatif)', vt, 'Affiché sous la vidéo et lu par les lecteurs d’écran.'));
      body.appendChild(vBox);
      syncVideo();
    } else if (b.type === 'formulaire') {
      var fs = el('select', { class: 'in', id: nid('fm') });
      fs.appendChild(el('option', { value: '' }, forms.length ? 'Choisir un formulaire…' : 'Aucun formulaire pour l’instant'));
      forms.forEach(function (f) {
        fs.appendChild(el('option', { value: String(f.id) }, f.title + ' · ' + f.fields.length + (f.fields.length > 1 ? ' champs' : ' champ') + (f.open ? '' : ' · fermé')));
      });
      fs.value = b.form ? String(b.form) : '';
      fs.addEventListener('change', function () { b.form = fs.value ? parseInt(fs.value, 10) : null; dirtyCheck(); });
      body.appendChild(field('Formulaire à afficher', fs, 'Les réponses arrivent dans le panneau, rubrique Formulaires → Réponses.'));
      var fl = el('p', { class: 'hint', style: 'margin:8px 0 0' });
      var fa = el('a', { href: 'SA-Formulaires.dc.html', style: 'font-weight:700' }, forms.length ? 'Gérer les formulaires et voir les réponses' : 'Créer un formulaire');
      fl.appendChild(fa);
      body.appendChild(fl);
    } else if (b.type === 'widget') {
      if (!isSuper()) {
        var ws = el('select', { class: 'in', id: nid('w') });
        ws.appendChild(el('option', { value: '' }, widgetList().length ? 'Choisir un widget…' : 'Aucun widget pour l’instant'));
        widgetList().forEach(function (w) { ws.appendChild(el('option', { value: String(w.id) }, w.title || ('Widget ' + w.id))); });
        ws.value = b.widget ? String(b.widget) : '';
        ws.addEventListener('change', function () { b.widget = ws.value ? parseInt(ws.value, 10) : null; render(); dirtyCheck(); });
        body.appendChild(field('Widget à afficher', ws, 'Le code des widgets ne peut être écrit ou modifié que par le superadmin.'));
      } else {
        if (!b._w) b._w = widgetDraft(widgets[b.widget]);
        var wd = b._w;
        var wsel = el('select', { class: 'in', id: nid('w') });
        wsel.appendChild(el('option', { value: 'new' }, 'Nouveau widget'));
        widgetList().forEach(function (w) { wsel.appendChild(el('option', { value: String(w.id) }, (w.title || ('Widget ' + w.id)) + ' (n° ' + w.id + ')')); });
        wsel.value = b.widget ? String(b.widget) : 'new';
        wsel.addEventListener('change', function () {
          b.widget = wsel.value === 'new' ? null : parseInt(wsel.value, 10);
          b._w = widgetDraft(widgets[b.widget]);
          render(); dirtyCheck();
        });
        body.appendChild(field('Widget', wsel, 'Un même widget peut servir sur plusieurs pages : le modifier change toutes ces pages.'));
        var wt = el('input', { class: 'in', type: 'text', id: nid('wt'), maxlength: '80', placeholder: 'Ex. Calculateur de zakat' }); wt.value = wd.title;
        on(wt, function (v) { wd.title = v; });
        body.appendChild(field('Nom du widget', wt, 'Lu par les lecteurs d’écran pour annoncer le widget.'));
        var lg = el('div', { class: 'seg', role: 'group', 'aria-label': 'Langage du widget', style: 'flex-wrap:wrap;align-self:flex-start;margin-top:8px' });
        [['web', 'HTML, CSS et JavaScript'], ['python', 'Python']].forEach(function (x) {
          var bb = el('button', { type: 'button', 'aria-pressed': String(wd.lang === x[0]) }, x[1]);
          bb.addEventListener('click', function () { wd.lang = x[0]; render(); dirtyCheck(); });
          lg.appendChild(bb);
        });
        body.appendChild(lg);
        var mono = 'font-family:ui-monospace,Menlo,monospace;font-size:13px;min-height:120px;resize:vertical;white-space:pre';
        var area = function (key, label, hint, rows) {
          var t = el('textarea', { class: 'in', id: nid('wc'), rows: String(rows || 6), spellcheck: 'false', autocapitalize: 'off', autocomplete: 'off', style: mono });
          t.value = wd[key] || '';
          t.addEventListener('input', function () { wd[key] = t.value; dirtyCheck(); });
          body.appendChild(field(label, t, hint));
        };
        if (wd.lang === 'python') {
          area('js', 'Code Python', 'Tourne dans le navigateur du visiteur (Pyodide). print() s’affiche sous le widget. Premier chargement : environ 10 Mo, lent sur téléphone.', 10);
          area('html', 'HTML affiché au-dessus du résultat (facultatif)', 'Le code Python peut le modifier avec « from js import document ».', 4);
          area('css', 'CSS (facultatif)', '', 4);
        } else {
          area('html', 'HTML', '', 8);
          area('css', 'CSS', '', 5);
          area('js', 'JavaScript', '', 8);
        }
        var g2 = el('div', { class: 'g2', style: 'align-items:start' });
        var wh = el('input', { class: 'in', type: 'number', id: nid('wh'), min: '80', max: '2000', step: '10' }); wh.value = String(wd.height);
        on(wh, function (v) { var n = parseInt(v, 10); wd.height = isNaN(n) ? 400 : n; });
        g2.appendChild(field('Hauteur affichée (pixels)', wh, 'Entre 80 et 2000.'));
        var nw = el('div', { class: 'fld' });
        var nl = el('label', { style: 'display:flex;gap:10px;align-items:flex-start;font-weight:600;min-height:44px;cursor:pointer' });
        var nc = el('input', { type: 'checkbox', style: 'width:22px;height:22px;flex:none;margin-top:2px' }); nc.checked = !!wd.net;
        nc.addEventListener('change', function () { wd.net = nc.checked; dirtyCheck(); });
        nl.appendChild(nc); nl.appendChild(document.createTextNode('Autoriser le widget à joindre Internet'));
        nw.appendChild(nl);
        nw.appendChild(el('p', { class: 'hint' }, 'Désactivé par défaut : le widget ne peut alors envoyer ni recevoir aucune donnée. À activer seulement pour un service que vous connaissez (formulaire de don externe, carte…).'));
        g2.appendChild(nw);
        body.appendChild(g2);
        var box = el('div', { style: 'margin-top:10px;padding:12px 14px;border-radius:12px;background:#E6EEF8;color:#1F4E86;font-size:14px' },
          'Sécurité : le widget tourne dans une boîte isolée (adresse /w/…). Il ne peut lire ni la session du panneau, ni les cookies, ni les données du site, ni toucher au reste de la page. Son code reste visible par les visiteurs : n’y mettez jamais de mot de passe ni de clé secrète.');
        body.appendChild(box);
        if (b.widget && widgets[b.widget]) {
          body.appendChild(el('p', { class: 'lbl', style: 'margin:14px 0 6px' }, 'Aperçu (dernière version enregistrée)'));
          body.appendChild(el('iframe', { src: '/w/' + b.widget + '?v=' + encodeURIComponent(widgets[b.widget].updatedAt || ''), title: 'Aperçu du widget', sandbox: 'allow-scripts',
            style: 'display:block;width:100%;height:' + Math.min(600, widgets[b.widget].height) + 'px;border:1px solid #E4D9C0;border-radius:12px;background:#fff' }));
        }
      }
    }
    sec.appendChild(body);
    return sec;
  }
  function render() {
    var box = $('pe-blocks'); if (!box) return;
    box.innerHTML = '';
    if (!blocks.length) {
      var empty = el('section', { class: 'card' }); var b = el('div', { class: 'card-b' });
      b.appendChild(el('p', { style: 'margin:0;font-weight:700;color:#0E4D3C' }, 'Cette page est encore vide.'));
      b.appendChild(el('p', { class: 'hint', style: 'margin:4px 0 0' }, 'Ajoutez un premier bloc ci-dessous : texte, bouton, tableau, photo, vidéo, formulaire ou widget.'));
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
    blocks.forEach(function (b) {
      if (b && b.type === 'tableau') normTable(b);
      if (b && b.type === 'widget' && isSuper()) b._w = widgetDraft(widgets[b.widget]);
    });
    vis = p.visibility || 'draft';
    lay = p.layout || 'site';
    $('pe-title').value = p.title || '';
    $('pe-slug').value = p.slug || '';
    $('pe-width').value = p.width || 'normal';
    $('pe-desc').value = p.description || '';
    setSeg('data-pe-vis', vis);
    setSeg('data-pe-lay', lay);
    $('pe-vis-hint').textContent = VIS_HINT[vis] || VIS_HINT.draft;
    $('pe-lay-hint').textContent = LAY_HINT[lay] || LAY_HINT.site;
    $('pe-slug-err').hidden = true;
    render();
    saved = snapshot();
    updateCounters();
    syncActionUi();
  }

  // ---------- actions d'enregistrement, d'annulation, d'aperçu et de suppression
  window.saPageSave = function (forcedVis) {
    if (!page || isSaving) return;
    var title = $('pe-title').value.trim(), slug = $('pe-slug').value.trim().toLowerCase();
    if (title.length < 2) { flash('Donnez un titre à la page (2 caractères minimum).'); $('pe-title').focus(); return; }
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length < 2 || slug.length > 60) {
      var err = $('pe-slug-err');
      err.textContent = 'Adresse invalide : 2 à 60 caractères, lettres minuscules sans accent, chiffres et tirets (ex. ramadan-2027).';
      err.hidden = false; $('pe-slug').focus(); return;
    }
    var badUrl = blocks.some(function (x) { return x.type === 'bouton' && x.lien && x.lien.type === 'url' && !/^https?:\/\/\S{3,}$/i.test(x.lien.url); });
    if (badUrl) { flash('Un bouton a un lien externe invalide : il doit commencer par https://'); return; }
    for (var bi = 0; bi < blocks.length; bi++) {
      var x = blocks[bi], bn = bi + 1, why = '';
      if (x.type === 'photo' && !x.media) why = 'Choisissez ou envoyez une photo pour le bloc ' + bn + ', ou supprimez ce bloc.';
      else if (x.type === 'photo' && !String(x.alt || '').trim()) why = 'Décrivez la photo du bloc ' + bn + ' dans « Texte alternatif » (obligatoire).';
      else if (x.type === 'video' && !parseVideo(x.url)) why = 'Le bloc ' + bn + ' n’a pas de lien vidéo reconnu : collez un lien YouTube, Vimeo ou Facebook.';
      else if (x.type === 'formulaire' && !x.form) why = 'Choisissez le formulaire à afficher dans le bloc ' + bn + ', ou supprimez ce bloc.';
      else if (x.type === 'widget' && !isSuper() && !x.widget) why = 'Choisissez le widget à afficher dans le bloc ' + bn + ', ou supprimez ce bloc.';
      else if (x.type === 'widget' && isSuper() && x._w && !(x._w.html + x._w.js).trim()) why = 'Le widget du bloc ' + bn + ' est vide : écrivez son code, ou supprimez ce bloc.';
      if (why) { flash(why); return; }
    }
    var targetVis = (typeof forcedVis === 'string' && VIS_HINT[forcedVis]) ? forcedVis : vis;
    var body = {
      title: title,
      slug: slug,
      blocks: blocks,
      visibility: targetVis,
      layout: lay,
      width: $('pe-width').value,
      description: $('pe-desc').value.trim()
    };
    isSaving = true;
    syncActionUi();
    saveWidgets().then(function () {
      body.blocks = stripBlocks(blocks);
      return api('/api/admin/pages/' + id, { method: 'PUT', body: JSON.stringify(body) });
    }, function (err) { return { ok: false, message: err && err.message }; }).then(function (r) {
      isSaving = false;
      if (!r.ok) {
        syncActionUi();
        if (r.code === 'slug_taken') { var e2 = $('pe-slug-err'); e2.textContent = r.message; e2.hidden = false; $('pe-slug').focus(); }
        flash(r.message || 'L’enregistrement a échoué. Réessayez.');
        return;
      }
      fill(r.page);
      flash(r.page.visibility === 'published' ? 'Page enregistrée et publiée à ' + r.page.url
        : r.page.visibility === 'private' ? 'Page enregistrée. Accessible à qui a le lien : ' + r.page.url
        : 'Brouillon enregistré. La page n’est pas visible du public.');
    }, function () {
      isSaving = false;
      syncActionUi();
      flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.');
    });
  };
  window.saPageUndo = function () {
    if (!page || isSaving) return;
    fill(page);
    flash('Changements annulés.');
  };
  window.saPagePreview = function () {
    if (!page) return;
    if (snapshot() !== saved) flash('L’aperçu montre la dernière version enregistrée. Enregistrez pour y voir vos changements.');
    window.open(page.url, '_blank', 'noopener');
  };
  function deleteCurrentPage() {
    if (!page || isSaving) return;
    if (!window.confirm('Supprimer définitivement « ' + page.title + ' » ?\n\nSon adresse ' + page.url + ' ne fonctionnera plus. Cette action est irréversible.')) return;
    isSaving = true;
    syncActionUi();
    api('/api/admin/pages/' + id, { method: 'DELETE' }).then(function (r) {
      isSaving = false;
      if (!r.ok) {
        syncActionUi();
        flash(r.message || 'La suppression a échoué. Réessayez.');
        return;
      }
      saved = snapshot();
      location.href = 'SA-Pages.dc.html';
    }, function () {
      isSaving = false;
      syncActionUi();
      flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.');
    });
  }

  // ---------- événements du formulaire
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-pe-add],[data-pe-vis],[data-pe-lay],#pe-copy,#pe-save-bottom,#pe-save-pub,#pe-undo-bottom,#pe-undo-pub,#pe-pv-bottom,#pe-delete');
    if (!t || !page) return;
    if (t.hasAttribute('data-pe-add')) {
      var k = t.getAttribute('data-pe-add');
      if (blocks.length >= 50) { flash('Une page compte au plus 50 blocs.'); return; }
      blocks.push(k === 'texte' ? { type: 'texte', titre: '', texte: '' }
        : k === 'bouton' ? { type: 'bouton', texte: '', lien: { type: 'none' }, style: 'or' }
        : k === 'photo' ? { type: 'photo', media: null, alt: '', legende: '', taille: 'pleine' }
        : k === 'video' ? { type: 'video', url: '', titre: '' }
        : k === 'formulaire' ? { type: 'formulaire', form: null }
        : k === 'widget' ? { type: 'widget', widget: null }
        : { type: 'tableau', colonnes: ['', ''], lignes: [['', ''], ['', '']] });
      render(); dirtyCheck();
      flash('Bloc « ' + META[k] + ' » ajouté.');
      var cards = $('pe-blocks').querySelectorAll('section.card');
      var last = cards[cards.length - 1]; var f = last && last.querySelector('input,textarea,select'); if (f) f.focus();
    } else if (t.hasAttribute('data-pe-vis')) {
      vis = t.getAttribute('data-pe-vis');
      setSeg('data-pe-vis', vis);
      $('pe-vis-hint').textContent = VIS_HINT[vis];
      dirtyCheck();
    } else if (t.hasAttribute('data-pe-lay')) {
      lay = t.getAttribute('data-pe-lay');
      setSeg('data-pe-lay', lay);
      $('pe-lay-hint').textContent = LAY_HINT[lay];
      dirtyCheck();
    } else if (t.id === 'pe-copy') {
      var full = location.origin + page.url;
      (navigator.clipboard ? navigator.clipboard.writeText(full) : Promise.reject()).then(
        function () { t.textContent = 'Lien copié'; setTimeout(function () { t.textContent = 'Copier le lien'; }, 1800); },
        function () { flash('Copie impossible ici. Le lien est : ' + full); });
    } else if (t.id === 'pe-save-bottom' || t.id === 'pe-save-pub') {
      window.saPageSave();
    } else if (t.id === 'pe-undo-bottom' || t.id === 'pe-undo-pub') {
      window.saPageUndo();
    } else if (t.id === 'pe-pv-bottom') {
      window.saPagePreview();
    } else if (t.id === 'pe-delete') {
      deleteCurrentPage();
    }
  });
  document.addEventListener('input', function (e) {
    var t = e.target; if (!t || !page) return;
    if (t.id === 'pe-slug') $('pe-slug-err').hidden = true;
    if (['pe-title', 'pe-slug', 'pe-desc'].indexOf(t.id) > -1) dirtyCheck();
  });
  document.addEventListener('change', function (e) { if (e.target && e.target.id === 'pe-width') dirtyCheck(); });

  // ---------- chargement (attend que #dc-root soit monté par React)
  var started = false;
  function start() {
    var miss = $('pe-missing');
    if (!id) {
      miss.textContent = 'Aucune page choisie. Revenez à « Créer une page » et cliquez sur « Modifier » à côté d’une page.';
      miss.hidden = false;
      setBridge({ loaded: true, dirty: false });
      return;
    }
    Promise.all([api('/api/admin/pages/' + id), api('/api/admin/pages'), api('/api/auth/me'), api('/api/admin/media'),
      api('/api/admin/widgets'), api('/api/admin/custom-forms')]).then(function (rs) {
      var r = rs[0];
      if (!r.ok) {
        miss.textContent = r.message || 'Impossible de charger cette page.';
        miss.hidden = false;
        setBridge({ loaded: true, dirty: false });
        return;
      }
      customPages = rs[1].ok ? rs[1].pages : [];
      me = rs[2].ok ? rs[2].admin : null;
      media = rs[3].ok ? rs[3].media || [] : [];
      storage = !!(rs[3].ok && rs[3].storage);
      mediaNotice = rs[3].notice || (rs[3].ok ? '' : rs[3].message || '');
      widgets = {};
      (rs[4].ok ? rs[4].widgets || [] : []).forEach(function (w) { widgets[w.id] = w; });
      forms = rs[5].ok ? rs[5].forms || [] : [];
      $('pe-root').hidden = false;
      fill(r.page);
    }, function () {
      miss.textContent = 'Impossible de joindre le serveur. Rechargez la page.';
      miss.hidden = false;
      setBridge({ loaded: true, dirty: false });
    });
  }
  function tryStart() {
    if (started || document.querySelector('x-dc') || !window.__saPage || !$('pe-root')) return;
    started = true;
    start();
  }
  window.addEventListener('sa-page-ready', tryStart);
  tryStart();
  if (!started) {
    new MutationObserver(function (m, o) {
      if (!document.querySelector('x-dc') && window.__saPage && $('pe-root')) {
        o.disconnect();
        tryStart();
      }
    }).observe(document.documentElement, { childList: true, subtree: true });
  }
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
    # En-tête : Aperçu + Annuler les changements (désactivé si clean) + Enregistrer le brouillon / Mettre à jour (désactivé si clean).
    hdr_pat = re.compile(
        r'(<button type="button" class="btn btn-onDark" sc-camel-on-click="\{\{openPv\}\}">.*?</button>)\s*<button.*?(?=</header>)',
        flags=re.S,
    )
    hdr_repl = (
        r'\1\n'
        r'  <button type="button" class="btn btn-onDark" disabled="{{clean}}" sc-camel-on-click="{{undo}}" style="gap:0">Annuler<span class="hide-t">&nbsp;les changements</span></button>\n'
        r'  <button type="button" class="btn btn-gold" disabled="{{clean}}" sc-camel-on-click="{{save}}">{{pubLabel}}</button>\n '
    )
    tpl, n_hdr = hdr_pat.subn(hdr_repl, tpl, count=1)
    assert n_hdr == 1, 'boutons d’en-tête de SA-PageEditeur introuvables'
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
# Panneau Accueil : 7 sélecteurs de liens hors cartes et annonces. La maquette y proposait une page inventée et un
# « Lien externe… » qui s'enregistrait tel quel (bouton cassé sur l'accueil public).
# Les liens des cartes et des annonces sont gérés par la logique du panneau (panneau_component.js).
HOME_LINK_FIELDS = r"""{ 'f-h1': ['hero', 'h1'], 'f-h2': ['hero', 'h2'], 'f-int': ['campagne', 'btnInterac'],
  'f-sui': ['campagne', 'btnSuivre'], 'f-tous': ['annonces', 'btnTous'], 'f-bv': ['bienvenue', 'lien'],
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
  if (!document.querySelector('x-dc') && document.getElementById('f-h1')) start();
  else new MutationObserver(function (m, o) { if (!document.querySelector('x-dc') && document.getElementById('f-h1')) { o.disconnect(); start(); } })
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
