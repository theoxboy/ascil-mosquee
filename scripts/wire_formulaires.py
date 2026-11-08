"""Étape M5 : nouvelle rubrique « Formulaires » du panneau (SA-Formulaires.dc.html).

- Mes formulaires : liste (titre, ouvert / fermé, nombre de champs, réponses et nouvelles réponses),
  création, modification et suppression (superadmin ; l'éditeur voit la liste et les réponses).
- Éditeur : titre, introduction, champs (texte court, texte long, courriel, téléphone, nombre, date,
  liste déroulante, choix unique, cases à cocher ; libellé, aide, obligatoire, choix proposés, ordre),
  texte du bouton, message après l'envoi, ouvert ou fermé.
- Réponses : tableau (une colonne par champ), filtre par statut, recherche, statut nouveau / lu / traité,
  suppression (superadmin) et export CSV pour Excel (protégé contre les formules piégées).
- Menu : lien « Formulaires » (avec le nombre de nouvelles réponses) dans toutes les pages du panneau.

La page est construite à partir de SA-Pages.dc.html déjà relié par wire_pages.py (même en-tête,
même composant minimal). Les formulaires se placent sur une page créée avec le bloc « + Formulaire ».
Ordre : après wire_contact.py, avant fix_inputs.py. Idempotent.
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


ICON = {
    'up': '<path d="m18 15-6-6-6 6"></path>',
    'down': '<path d="m6 9 6 6 6-6"></path>',
    'trash': '<path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>',
}


def svg(name):
    return ('<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + ICON[name] + '</svg>')


STYLE = '''<style id="sa-forms-style">
.fm-tag{display:inline-flex;align-items:center;min-height:24px;padding:0 10px;border-radius:999px;font-size:12px;font-weight:700}
.fm-tag.open{background:#DCEFE6;color:#0E4D3C}.fm-tag.closed{background:#F3EAD8;color:#7A5A1E}.fm-tag.new{background:#E6EEF8;color:#1F4E86}
.fm-field{border:1px solid #E4D9C0;border-radius:14px;padding:14px;background:#fff;display:flex;flex-direction:column;gap:10px}
.fm-field-h{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.fm-field-h .ttl{flex:1;min-width:0;margin:0;font-size:16px}
.fm-check{display:flex;gap:10px;align-items:center;font-weight:600;min-height:44px;cursor:pointer}
.fm-check input{width:22px;height:22px;flex:none}
.fm-tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.fm-table{overflow-x:auto;border:1px solid #E4D9C0;border-radius:12px;margin-top:12px;
  background:linear-gradient(to right,#fff,#fff),linear-gradient(to left,#fff,#fff),linear-gradient(to right,rgba(0,0,0,.12),transparent),linear-gradient(to left,rgba(0,0,0,.12),transparent);
  background-position:left,right,left,right;background-repeat:no-repeat;background-size:24px 100%,24px 100%,12px 100%,12px 100%;background-attachment:local,local,scroll,scroll}
.fm-table table{border-collapse:collapse;min-width:100%;font-size:14px}
.fm-table th,.fm-table td{padding:10px 12px;border-bottom:1px solid #F3EAD8;text-align:start;vertical-align:top}
.fm-table th{background:#FAF6EC;color:#0E4D3C;white-space:nowrap}
.fm-table td{max-width:320px;overflow-wrap:anywhere;white-space:pre-wrap}
.fm-table tr.is-new td{background:#F7FAFE}
.fm-table select{min-height:36px;padding:4px 8px;border:1px solid #8A9A92;border-radius:8px;font:inherit;background:#fff}
.fm-table :focus-visible{outline:3px solid #C49A4A;outline-offset:2px}
</style>
'''

MAIN = '''
   <div><p class="eyebrow">Rubrique du menu</p><h1 class="serif ttl-page">Formulaires</h1>
   <p style="margin:6px 0 0;color:#4F5E57;max-width:680px">Créez vos propres formulaires (inscriptions, sondages, demandes…), placez-les sur une page avec le bloc « + Formulaire » de « Créer une page », puis lisez ici toutes les réponses.</p></div>
   <p id="fm-notice" class="pg-err" role="alert" hidden></p>
   <section class="card" aria-labelledby="fl-t"><div class="card-h"><span class="num" aria-hidden="true">1</span><div><h2 class="ttl" id="fl-t">Mes formulaires</h2>
   <p class="dsc" id="fl-count">Chargement des formulaires…</p></div></div>
   <div class="card-b">
    <form id="fn-form" novalidate hidden style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;margin:10px 0 4px">
     <div class="fld" style="flex:1 1 280px"><label class="lbl" for="fn-title">Nouveau formulaire</label>
     <input class="in" id="fn-title" type="text" maxlength="120" placeholder="Ex. Inscription aux cours d’arabe 2027"></div>
     <button type="submit" class="btn btn-gold" id="fn-btn" style="min-height:48px">Créer le formulaire</button>
    </form>
    <ul class="pg-list" id="fl-list"></ul>
   </div></section>
   <section class="card" id="fe-card" hidden aria-labelledby="fe-t"><div class="card-h"><span class="num" aria-hidden="true">2</span><div><h2 class="ttl" id="fe-t">Modifier le formulaire</h2>
   <p class="dsc">Changer ou retirer un champ ne modifie pas les réponses déjà reçues.</p></div></div>
   <div class="card-b" style="display:flex;flex-direction:column;gap:14px;margin-top:10px">
    <div class="fld"><label class="lbl" for="fe-title">Titre (affiché au-dessus du formulaire)</label><input class="in" id="fe-title" type="text" maxlength="120"></div>
    <div class="fld"><label class="lbl" for="fe-intro">Introduction (facultative)</label><textarea class="in" id="fe-intro" rows="3" maxlength="1000" style="min-height:84px;resize:vertical"></textarea></div>
    <h3 class="ttl" style="margin:6px 0 0;font-size:17px">Champs</h3>
    <div id="fe-fields" style="display:flex;flex-direction:column;gap:10px"></div>
    <div class="fm-tools"><button type="button" class="btn btn-line" id="fe-add">+ Ajouter un champ</button><span class="hint" id="fe-nfields"></span></div>
    <div class="g2" style="align-items:start">
     <div class="fld"><label class="lbl" for="fe-bouton">Texte du bouton d’envoi</label><input class="in" id="fe-bouton" type="text" maxlength="40"></div>
     <div class="fld"><span class="lbl" id="fe-open-l">État</span>
      <div class="seg" role="group" aria-labelledby="fe-open-l" style="flex-wrap:wrap;align-self:flex-start">
       <button type="button" data-fe-open="1" aria-pressed="true">Ouvert</button><button type="button" data-fe-open="0" aria-pressed="false">Fermé</button></div>
      <p class="hint">Fermé : le formulaire reste affiché sur la page mais n’accepte plus de réponses.</p></div>
    </div>
    <div class="fld"><label class="lbl" for="fe-merci">Message affiché après l’envoi</label><textarea class="in" id="fe-merci" rows="2" maxlength="600" style="min-height:64px;resize:vertical" placeholder="Merci ! Votre réponse est bien arrivée à l’association."></textarea></div>
    <div class="fm-tools" style="justify-content:space-between;border-top:1px solid #F3EAD8;padding-top:12px">
     <span id="fe-status" style="font-weight:700;color:#0E4D3C;font-size:14px"></span>
     <span class="fm-tools"><button type="button" class="btn btn-line" id="fe-close">Fermer l’éditeur</button>
     <button type="button" class="btn btn-line" id="fe-undo" disabled>Annuler les changements</button>
     <button type="button" class="btn btn-gold" id="fe-save" disabled>Enregistrer le formulaire</button></span>
    </div>
   </div></section>
   <section class="card" id="fr-card" hidden aria-labelledby="fr-t"><div class="card-h"><span class="num" aria-hidden="true">3</span><div><h2 class="ttl" id="fr-t">Réponses</h2>
   <p class="dsc" id="fr-count"></p></div></div>
   <div class="card-b">
    <div class="fm-tools" style="margin-top:10px">
     <div class="seg" role="group" aria-label="Filtrer les réponses" style="flex-wrap:wrap">
      <button type="button" data-fr-filter="" aria-pressed="true">Toutes</button><button type="button" data-fr-filter="nouveau" aria-pressed="false">Nouvelles</button>
      <button type="button" data-fr-filter="lu" aria-pressed="false">Lues</button><button type="button" data-fr-filter="traite" aria-pressed="false">Traitées</button></div>
     <input class="in" id="fr-q" type="search" aria-label="Rechercher dans les réponses" placeholder="Rechercher un nom, un courriel…" style="flex:1 1 220px;min-width:0">
     <button type="button" class="btn btn-line" id="fr-read">Tout marquer comme lu</button>
     <button type="button" class="btn btn-green" id="fr-csv">Exporter en CSV (Excel)</button>
    </div>
    <p class="hint" id="fr-scroll" hidden style="margin:8px 0 0">Faites défiler le tableau vers la droite pour voir toutes les colonnes.</p>
    <div id="fr-box"></div>
   </div></section>
'''

SCRIPT = r"""<script id="sa-forms">
(function () {
  var ICON = __ICONS__;
  var TYPES = __TYPES__;
  var WITH_OPTIONS = ['liste', 'choix', 'cases'];
  var STATUS = { nouveau: 'Nouveau', lu: 'Lu', traite: 'Traité' };
  var forms = [], canEdit = false, cur = null, saved = '', saving = false;
  var shown = null, entries = [], filter = '', query = '';
  function $(x) { return document.getElementById(x); }
  function bridge() { return window.__saPage; }
  function setBridge(st) { var b = bridge(); if (b) b.setState(st); }
  function flash(m) { var b = bridge(); if (b) b.flash(m); }
  function api(url, opt) {
    return fetch(url, Object.assign({ credentials: 'same-origin', headers: { 'Content-Type': 'application/json' } }, opt || {}))
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text != null) e.textContent = text;
    return e;
  }
  var uid = 0;
  function nid(p) { uid += 1; return 'fm-' + p + '-' + uid; }
  function field(label, input, hint) {
    var f = el('div', { class: 'fld' });
    f.appendChild(el('label', { class: 'lbl', for: input.id }, label)); f.appendChild(input);
    if (hint) f.appendChild(el('p', { class: 'hint' }, hint));
    return f;
  }
  function iconBtn(name, label, cls) {
    var b = el('button', { type: 'button', class: 'ico' + (cls ? ' ' + cls : ''), 'aria-label': label, title: label });
    b.innerHTML = ICON[name];
    return b;
  }
  function when(iso, withTime) {
    var d = new Date(iso);
    if (isNaN(d)) return '—';
    return withTime ? d.toLocaleString('fr-CA', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
      : d.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short', year: 'numeric' });
  }
  function plural(n, one, many) { return n + ' ' + (n > 1 ? many : one); }

  // ---------- liste
  function renderList() {
    var ul = $('fl-list'); if (!ul) return;
    ul.innerHTML = '';
    $('fn-form').hidden = !canEdit;
    var n = forms.length;
    $('fl-count').textContent = n ? plural(n, 'formulaire', 'formulaires') + (canEdit ? '' : ' · seul le superadmin peut créer ou modifier un formulaire.')
      : canEdit ? 'Aucun formulaire pour l’instant.' : 'Aucun formulaire pour l’instant. Le superadmin peut en créer un.';
    if (!n) {
      var li = el('li', { class: 'pg-item' });
      li.appendChild(el('p', { class: 'hint', style: 'margin:0' }, canEdit
        ? 'Donnez un titre ci-dessus et cliquez sur « Créer le formulaire ». Ajoutez ensuite ses champs, puis placez-le sur une page avec le bloc « + Formulaire ».'
        : 'Les formulaires créés par le superadmin et leurs réponses apparaîtront ici.'));
      ul.appendChild(li);
      return;
    }
    forms.forEach(function (f) {
      var li = el('li', { class: 'pg-item' });
      var main = el('div', { class: 'pg-item-main' });
      var head = el('div', { style: 'display:flex;flex-wrap:wrap;gap:8px;align-items:center' });
      head.appendChild(el('span', { class: 'pg-item-title' }, f.title));
      head.appendChild(el('span', { class: 'fm-tag ' + (f.open ? 'open' : 'closed') }, f.open ? 'Ouvert' : 'Fermé'));
      if (f.nouveaux) head.appendChild(el('span', { class: 'fm-tag new' }, plural(f.nouveaux, 'nouvelle réponse', 'nouvelles réponses')));
      main.appendChild(head);
      main.appendChild(el('p', { class: 'hint', style: 'margin:4px 0 0' },
        plural(f.fields.length, 'champ', 'champs') + ' · ' + plural(f.total || 0, 'réponse', 'réponses') + ' · modifié le ' + when(f.updatedAt)));
      var act = el('div', { class: 'pg-actions' });
      var rb = el('button', { type: 'button', class: 'btn btn-green', style: 'min-height:40px' }, 'Réponses (' + (f.total || 0) + ')');
      rb.addEventListener('click', function () { showEntries(f.id, true); });
      act.appendChild(rb);
      if (canEdit) {
        var eb = el('button', { type: 'button', class: 'btn btn-line', style: 'min-height:40px' }, 'Modifier');
        eb.addEventListener('click', function () { openEditor(f.id); });
        act.appendChild(eb);
        var x = iconBtn('trash', 'Supprimer « ' + f.title + ' »', 'ico-danger');
        x.addEventListener('click', function () {
          if (!window.confirm('Supprimer définitivement le formulaire « ' + f.title + ' » et ses ' + plural(f.total || 0, 'réponse', 'réponses') + ' ?\n\nLes pages qui l’affichent ne le montreront plus. Cette action est irréversible.')) return;
          api('/api/admin/custom-forms/' + f.id, { method: 'DELETE' }).then(function (r) {
            if (!r.ok) { flash(r.message || 'La suppression a échoué. Réessayez.'); return; }
            if (cur && cur.id === f.id) closeEditor(true);
            if (shown === f.id) { shown = null; $('fr-card').hidden = true; }
            flash('Formulaire « ' + f.title + ' » supprimé.');
            loadList();
          }, function () { flash('Impossible de joindre le serveur. Réessayez.'); });
        });
        act.appendChild(x);
      }
      li.appendChild(main); li.appendChild(act);
      ul.appendChild(li);
    });
  }
  function loadList() {
    return api('/api/admin/custom-forms').then(function (r) {
      setBridge({ loaded: true, vis: 'list' });
      if (!r.ok) { $('fl-count').textContent = r.message || 'Impossible de charger les formulaires. Rechargez la page.'; return; }
      canEdit = !!r.canEdit;
      forms = r.forms || [];
      if (r.notice) { $('fm-notice').textContent = r.notice; $('fm-notice').hidden = false; }
      renderList();
    }, function () {
      setBridge({ loaded: true, vis: 'list' });
      $('fl-count').textContent = 'Impossible de joindre le serveur. Rechargez la page.';
    });
  }
  function byId(id) { for (var i = 0; i < forms.length; i++) if (forms[i].id === id) return forms[i]; return null; }

  // ---------- éditeur
  function snapshot() { return cur ? JSON.stringify(cur) : ''; }
  function dirty() { return !!cur && snapshot() !== saved; }
  function sync() {
    var d = dirty();
    setBridge({ loaded: true, vis: 'list', dirty: d, saving: saving });
    if (!cur) return;
    $('fe-save').disabled = !d || saving;
    $('fe-undo').disabled = !d || saving;
    $('fe-save').textContent = saving ? 'Enregistrement…' : 'Enregistrer le formulaire';
    $('fe-status').textContent = saving ? 'Enregistrement…' : d ? 'Changements non enregistrés' : 'Tout est enregistré';
    $('fe-status').style.color = d ? '#7A5A1E' : '#0E4D3C';
    $('fe-nfields').textContent = plural(cur.fields.length, 'champ', 'champs') + ' sur 30 au plus.';
    $('fe-add').disabled = cur.fields.length >= 30;
  }
  function nextId() {
    var n = 0;
    cur.fields.forEach(function (f) { var m = /^c(\d+)$/.exec(f.id); if (m) n = Math.max(n, parseInt(m[1], 10)); });
    return 'c' + (n + 1);
  }
  function renderFields() {
    var box = $('fe-fields'); box.innerHTML = '';
    if (!cur.fields.length) box.appendChild(el('p', { class: 'hint', style: 'margin:0' }, 'Ce formulaire n’a encore aucun champ. Cliquez sur « + Ajouter un champ ».'));
    cur.fields.forEach(function (f, i) {
      var n = cur.fields.length;
      var card = el('div', { class: 'fm-field', role: 'group', 'aria-label': 'Champ ' + (i + 1) });
      var h = el('div', { class: 'fm-field-h' });
      h.appendChild(el('span', { class: 'num', 'aria-hidden': 'true' }, String(i + 1)));
      h.appendChild(el('h4', { class: 'ttl' }, f.label || 'Champ sans libellé'));
      [['up', 'Monter', i === 0, -1], ['down', 'Descendre', i === n - 1, 1]].forEach(function (m) {
        var b = iconBtn(m[0], m[1] + ' le champ ' + (i + 1)); b.disabled = m[2];
        b.addEventListener('click', function () { var t = cur.fields[i]; cur.fields[i] = cur.fields[i + m[3]]; cur.fields[i + m[3]] = t; renderFields(); sync(); });
        h.appendChild(b);
      });
      var del = iconBtn('trash', 'Retirer le champ ' + (i + 1), 'ico-danger');
      del.addEventListener('click', function () { cur.fields.splice(i, 1); renderFields(); sync(); });
      h.appendChild(del);
      card.appendChild(h);
      var g = el('div', { class: 'g2', style: 'align-items:start' });
      var ts = el('select', { class: 'in', id: nid('t') });
      Object.keys(TYPES).forEach(function (k) { ts.appendChild(el('option', { value: k }, TYPES[k])); });
      ts.value = f.type;
      ts.addEventListener('change', function () {
        f.type = ts.value;
        if (WITH_OPTIONS.indexOf(f.type) > -1 && !Array.isArray(f.options)) f.options = [];
        if (WITH_OPTIONS.indexOf(f.type) === -1) delete f.options;
        renderFields(); sync();
      });
      var lb = el('input', { class: 'in', type: 'text', id: nid('l'), maxlength: '120', placeholder: 'Ex. Votre nom complet' }); lb.value = f.label || '';
      lb.addEventListener('input', function () { f.label = lb.value; card.querySelector('h4').textContent = lb.value || 'Champ sans libellé'; sync(); });
      g.appendChild(field('Type', ts)); g.appendChild(field('Libellé (la question)', lb));
      card.appendChild(g);
      var ai = el('input', { class: 'in', type: 'text', id: nid('a'), maxlength: '200', placeholder: 'Facultatif' }); ai.value = f.aide || '';
      ai.addEventListener('input', function () { f.aide = ai.value; sync(); });
      card.appendChild(field('Aide sous la question', ai));
      if (WITH_OPTIONS.indexOf(f.type) > -1) {
        var op = el('textarea', { class: 'in', id: nid('o'), rows: '4', style: 'min-height:96px;resize:vertical', placeholder: 'Un choix par ligne' });
        op.value = (f.options || []).join('\n');
        op.addEventListener('input', function () { f.options = op.value.split('\n').map(function (x) { return x.trim(); }).filter(Boolean).slice(0, 30); sync(); });
        card.appendChild(field('Choix proposés', op, 'Un choix par ligne, 30 au plus.'));
      }
      var rq = el('label', { class: 'fm-check' });
      var rc = el('input', { type: 'checkbox' }); rc.checked = !!f.requis;
      rc.addEventListener('change', function () { f.requis = rc.checked; sync(); });
      rq.appendChild(rc); rq.appendChild(document.createTextNode('Réponse obligatoire'));
      card.appendChild(rq);
      box.appendChild(card);
    });
  }
  function fillEditor(f) {
    cur = JSON.parse(JSON.stringify({ id: f.id, title: f.title, intro: f.intro || '', fields: f.fields || [], bouton: f.bouton || 'Envoyer', merci: f.merci || '', open: !!f.open }));
    $('fe-title').value = cur.title; $('fe-intro').value = cur.intro; $('fe-bouton').value = cur.bouton; $('fe-merci').value = cur.merci;
    document.querySelectorAll('[data-fe-open]').forEach(function (b) { b.setAttribute('aria-pressed', String((b.getAttribute('data-fe-open') === '1') === cur.open)); });
    renderFields();
    saved = snapshot();
    sync();
  }
  function openEditor(id) {
    if (dirty() && cur.id !== id && !window.confirm('Le formulaire en cours a des changements non enregistrés. Les abandonner ?')) return;
    api('/api/admin/custom-forms/' + id).then(function (r) {
      if (!r.ok) { flash(r.message || 'Impossible d’ouvrir ce formulaire.'); return; }
      $('fe-card').hidden = false;
      $('fe-t').textContent = 'Modifier « ' + r.form.title + ' »';
      fillEditor(r.form);
      $('fe-card').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
      $('fe-title').focus({ preventScroll: true });
    }, function () { flash('Impossible de joindre le serveur. Réessayez.'); });
  }
  function closeEditor(force) {
    if (!force && dirty() && !window.confirm('Fermer l’éditeur sans enregistrer les changements ?')) return;
    cur = null; saved = '';
    $('fe-card').hidden = true;
    sync();
  }
  function saveForm() {
    if (!cur || saving || !dirty()) return;
    cur.title = $('fe-title').value.trim();
    if (cur.title.length < 2) { flash('Donnez un titre au formulaire (2 caractères minimum).'); $('fe-title').focus(); return; }
    for (var i = 0; i < cur.fields.length; i++) {
      var f = cur.fields[i];
      if (!String(f.label || '').trim()) { flash('Le champ ' + (i + 1) + ' a besoin d’un libellé (la question posée).'); return; }
      if (WITH_OPTIONS.indexOf(f.type) > -1 && !(f.options || []).length) { flash('Le champ « ' + f.label + ' » a besoin d’au moins un choix (un par ligne).'); return; }
    }
    saving = true; sync();
    api('/api/admin/custom-forms/' + cur.id, { method: 'PUT', body: JSON.stringify(cur) }).then(function (r) {
      saving = false;
      if (!r.ok) { sync(); flash(r.message || 'L’enregistrement a échoué. Réessayez.'); return; }
      $('fe-t').textContent = 'Modifier « ' + r.form.title + ' »';
      fillEditor(r.form);
      flash('Formulaire enregistré. Les pages qui l’affichent sont à jour.');
      loadList();
      if (shown === r.form.id) showEntries(r.form.id, false);
    }, function () { saving = false; sync(); flash('Impossible de joindre le serveur. Réessayez.'); });
  }
  window.saPageSave = saveForm;
  window.saPageUndo = function () { if (cur && dirty()) { api('/api/admin/custom-forms/' + cur.id).then(function (r) { if (r.ok) { fillEditor(r.form); flash('Changements annulés.'); } }); } };
  window.addEventListener('beforeunload', function (e) { if (dirty()) { e.preventDefault(); e.returnValue = ''; } });

  // ---------- réponses
  function columns(f) {
    var cols = f.fields.map(function (x) { return { id: x.id, label: x.label }; });
    var known = {}; cols.forEach(function (c) { known[c.id] = true; });
    entries.forEach(function (e) {
      Object.keys(e.data || {}).forEach(function (k) {
        if (!known[k]) { known[k] = true; cols.push({ id: k, label: (e.data[k] && e.data[k].l ? e.data[k].l : k) + ' (champ retiré)' }); }
      });
    });
    return cols;
  }
  function val(e, id) { var d = e.data && e.data[id]; return d && d.v != null ? String(d.v) : ''; }
  function visible() {
    var q = query.trim().toLowerCase();
    return entries.filter(function (e) {
      if (filter && e.status !== filter) return false;
      if (!q) return true;
      return Object.keys(e.data || {}).some(function (k) { return val(e, k).toLowerCase().indexOf(q) > -1; });
    });
  }
  function setStatus(ids, status) {
    return api('/api/admin/custom-forms/' + shown + '/entries', { method: 'PATCH', body: JSON.stringify({ ids: ids, status: status }) }).then(function (r) {
      if (!r.ok) { flash(r.message || 'Le changement de statut a échoué. Réessayez.'); return false; }
      entries.forEach(function (e) { if (ids.indexOf(e.id) > -1) e.status = status; });
      loadList();
      return true;
    }, function () { flash('Impossible de joindre le serveur. Réessayez.'); return false; });
  }
  function renderEntries() {
    var f = byId(shown); var box = $('fr-box'); if (!f || !box) return;
    box.innerHTML = '';
    var nNew = entries.filter(function (e) { return e.status === 'nouveau'; }).length;
    $('fr-t').textContent = 'Réponses — « ' + f.title + ' »';
    $('fr-count').textContent = plural(entries.length, 'réponse', 'réponses') + (nNew ? ' · ' + plural(nNew, 'nouvelle', 'nouvelles') : '');
    $('fr-read').disabled = !nNew;
    $('fr-csv').disabled = !entries.length;
    document.querySelectorAll('[data-fr-filter]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-fr-filter') === filter)); });
    var list = visible();
    if (!entries.length) {
      var em = el('div', { style: 'margin-top:12px;padding:18px;border:1px dashed #E4D9C0;border-radius:14px' });
      em.appendChild(el('p', { style: 'margin:0;font-weight:700;color:#0E4D3C' }, 'Aucune réponse pour l’instant.'));
      em.appendChild(el('p', { class: 'hint', style: 'margin:4px 0 0' }, 'Placez ce formulaire sur une page (bloc « + Formulaire » dans « Créer une page »), publiez-la et partagez son lien. Chaque réponse arrivera ici.'));
      box.appendChild(em); $('fr-scroll').hidden = true; return;
    }
    if (!list.length) { box.appendChild(el('p', { class: 'hint', style: 'margin:12px 0 0' }, 'Aucune réponse ne correspond à ce filtre ou à cette recherche.')); $('fr-scroll').hidden = true; return; }
    var cols = columns(f);
    $('fr-scroll').hidden = cols.length < 4;
    var wrap = el('div', { class: 'fm-table', tabindex: '0', role: 'region', 'aria-label': 'Tableau des réponses, défilable horizontalement' });
    var t = el('table'); var hr = el('tr');
    ['Reçue le', 'Statut'].concat(cols.map(function (c) { return c.label; })).concat(canEdit ? ['Action'] : []).forEach(function (x) { hr.appendChild(el('th', { scope: 'col' }, x)); });
    var th = el('thead'); th.appendChild(hr); t.appendChild(th);
    var tb = el('tbody');
    list.forEach(function (e) {
      var tr = el('tr', { class: e.status === 'nouveau' ? 'is-new' : '' });
      var td0 = el('td', { style: 'white-space:nowrap' }, when(e.createdAt, true));
      if (e.status === 'nouveau') { td0.appendChild(document.createElement('br')); td0.appendChild(el('span', { class: 'fm-tag new' }, 'Nouveau')); }
      tr.appendChild(td0);
      var td1 = el('td');
      var ss = el('select', { 'aria-label': 'Statut de la réponse du ' + when(e.createdAt, true) });
      Object.keys(STATUS).forEach(function (k) { ss.appendChild(el('option', { value: k }, STATUS[k])); });
      ss.value = e.status;
      ss.addEventListener('change', function () { setStatus([e.id], ss.value).then(function (ok) { if (ok) { flash('Statut changé : ' + STATUS[ss.value] + '.'); renderEntries(); } }); });
      td1.appendChild(ss); tr.appendChild(td1);
      cols.forEach(function (c) { tr.appendChild(el('td', {}, val(e, c.id) || '—')); });
      if (canEdit) {
        var td2 = el('td');
        var x = iconBtn('trash', 'Supprimer la réponse du ' + when(e.createdAt, true), 'ico-danger');
        x.addEventListener('click', function () {
          if (!window.confirm('Supprimer définitivement cette réponse ? Cette action est irréversible.')) return;
          api('/api/admin/custom-forms/' + shown + '/entries', { method: 'DELETE', body: JSON.stringify({ ids: [e.id] }) }).then(function (r) {
            if (!r.ok) { flash(r.message || 'La suppression a échoué. Réessayez.'); return; }
            entries = entries.filter(function (y) { return y.id !== e.id; });
            renderEntries(); loadList(); flash('Réponse supprimée.');
          }, function () { flash('Impossible de joindre le serveur. Réessayez.'); });
        });
        td2.appendChild(x); tr.appendChild(td2);
      }
      tb.appendChild(tr);
    });
    t.appendChild(tb); wrap.appendChild(t); box.appendChild(wrap);
    box.appendChild(el('p', { class: 'hint', style: 'margin:8px 0 0' }, plural(list.length, 'réponse affichée', 'réponses affichées') + '.'));
  }
  function showEntries(id, scroll) {
    shown = id;
    $('fr-card').hidden = false;
    $('fr-box').innerHTML = '';
    $('fr-count').textContent = 'Chargement des réponses…';
    api('/api/admin/custom-forms/' + id + '/entries').then(function (r) {
      if (!r.ok) { $('fr-count').textContent = r.message || 'Impossible de charger les réponses.'; return; }
      entries = r.entries || [];
      renderEntries();
      if (scroll) {
        $('fr-card').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
        $('fr-t').setAttribute('tabindex', '-1'); $('fr-t').focus({ preventScroll: true });
      }
    }, function () { $('fr-count').textContent = 'Impossible de joindre le serveur. Rechargez la page.'; });
  }
  // CSV pour Excel : séparateur « ; », UTF-8 avec BOM ; une valeur qui commence par = + - @ est
  // précédée d'une apostrophe pour qu'Excel ne l'exécute jamais comme une formule.
  function csvCell(v) {
    var s = String(v == null ? '' : v);
    if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
    return '"' + s.replace(/"/g, '""') + '"';
  }
  function exportCsv() {
    var f = byId(shown); if (!f || !entries.length) return;
    var cols = columns(f);
    var rows = [['Reçue le', 'Statut'].concat(cols.map(function (c) { return c.label; }))];
    visible().forEach(function (e) { rows.push([when(e.createdAt, true), STATUS[e.status] || e.status].concat(cols.map(function (c) { return val(e, c.id); }))); });
    var text = '﻿' + rows.map(function (r) { return r.map(csvCell).join(';'); }).join('\r\n');
    var name = 'reponses-' + (f.title.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'formulaire')
      + '-' + new Date().toISOString().slice(0, 10) + '.csv';
    var a = el('a', { href: URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' })), download: name });
    document.body.appendChild(a); a.click(); a.remove();
    flash('Fichier ' + name + ' téléchargé (' + plural(rows.length - 1, 'réponse', 'réponses') + ').');
  }

  // ---------- événements
  document.addEventListener('submit', function (e) {
    if (!e.target || e.target.id !== 'fn-form') return;
    e.preventDefault();
    var t = $('fn-title'), btn = $('fn-btn');
    var title = t.value.trim();
    if (title.length < 2) { flash('Donnez un titre au formulaire (2 caractères minimum).'); t.focus(); return; }
    btn.setAttribute('aria-busy', 'true'); btn.textContent = 'Création…';
    var starter = [{ id: 'c1', type: 'texte', label: 'Nom complet', aide: '', requis: true }, { id: 'c2', type: 'courriel', label: 'Courriel', aide: '', requis: true }];
    api('/api/admin/custom-forms', { method: 'POST', body: JSON.stringify({ title: title, fields: starter, merci: 'Merci ! Votre réponse est bien arrivée à l’association.' }) }).then(function (r) {
      btn.removeAttribute('aria-busy'); btn.textContent = 'Créer le formulaire';
      if (!r.ok) { flash(r.message || 'La création a échoué. Réessayez.'); return; }
      t.value = '';
      flash('Formulaire « ' + r.form.title + ' » créé avec deux premiers champs. Complétez-le ci-dessous.');
      loadList().then(function () { openEditor(r.form.id); });
    }, function () { btn.removeAttribute('aria-busy'); btn.textContent = 'Créer le formulaire'; flash('Impossible de joindre le serveur. Réessayez.'); });
  });
  document.addEventListener('input', function (e) {
    var t = e.target; if (!t) return;
    if (cur && t.id === 'fe-title') { cur.title = t.value; sync(); }
    else if (cur && t.id === 'fe-intro') { cur.intro = t.value; sync(); }
    else if (cur && t.id === 'fe-bouton') { cur.bouton = t.value; sync(); }
    else if (cur && t.id === 'fe-merci') { cur.merci = t.value; sync(); }
    else if (t.id === 'fr-q') { query = t.value; renderEntries(); }
  });
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-fe-open],[data-fr-filter],#fe-add,#fe-save,#fe-undo,#fe-close,#fr-read,#fr-csv');
    if (!t) return;
    if (t.hasAttribute('data-fe-open') && cur) {
      cur.open = t.getAttribute('data-fe-open') === '1';
      document.querySelectorAll('[data-fe-open]').forEach(function (b) { b.setAttribute('aria-pressed', String(b === t)); });
      sync();
    } else if (t.hasAttribute('data-fr-filter')) {
      filter = t.getAttribute('data-fr-filter'); renderEntries();
    } else if (t.id === 'fe-add' && cur) {
      if (cur.fields.length >= 30) return;
      cur.fields.push({ id: nextId(), type: 'texte', label: '', aide: '', requis: false });
      renderFields(); sync();
      var cards = $('fe-fields').querySelectorAll('.fm-field');
      var last = cards[cards.length - 1]; var inp = last && last.querySelectorAll('input')[0]; if (inp) inp.focus();
    } else if (t.id === 'fe-save') { saveForm(); }
    else if (t.id === 'fe-undo') { window.saPageUndo(); }
    else if (t.id === 'fe-close') { closeEditor(false); }
    else if (t.id === 'fr-read') {
      var ids = entries.filter(function (x) { return x.status === 'nouveau'; }).map(function (x) { return x.id; });
      if (ids.length) setStatus(ids, 'lu').then(function (ok) { if (ok) { renderEntries(); flash(plural(ids.length, 'réponse marquée', 'réponses marquées') + ' comme lue' + (ids.length > 1 ? 's.' : '.')); } });
    } else if (t.id === 'fr-csv') { exportCsv(); }
  });

  // ---------- démarrage (attend que #dc-root soit monté par React)
  var started = false;
  function start() {
    var q = new URLSearchParams(location.search);
    var want = parseInt(q.get('form'), 10);
    loadList().then(function () { if (want && byId(want)) showEntries(want, true); });
  }
  function tryStart() {
    if (started || document.querySelector('x-dc') || !window.__saPage || !$('fl-list')) return;
    started = true;
    start();
  }
  window.addEventListener('sa-page-ready', tryStart);
  tryStart();
  if (!started) {
    new MutationObserver(function (m, o) {
      if (!document.querySelector('x-dc') && window.__saPage && $('fl-list')) { o.disconnect(); tryStart(); }
    }).observe(document.documentElement, { childList: true, subtree: true });
  }
})();
</script>
"""

# Nombre de nouvelles réponses à côté du lien « Formulaires » du menu, sur toutes les pages du panneau.
BADGE = r"""<script id="sa-forms-badge">
(function () {
  function apply(n) {
    document.querySelectorAll('nav.side a[href="SA-Formulaires.dc.html"]').forEach(function (a) {
      var b = a.querySelector('.fm-badge');
      if (!n) { if (b) b.remove(); return; }
      if (!b) {
        b = document.createElement('span');
        b.className = 'fm-badge';
        b.setAttribute('style', 'display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:22px;padding:0 6px;margin-left:8px;border-radius:999px;background:#C49A4A;color:#1E2B26;font-size:12px;font-weight:800');
        a.appendChild(b);
      }
      b.textContent = String(n);
      b.setAttribute('aria-label', n + (n > 1 ? ' nouvelles réponses' : ' nouvelle réponse'));
    });
  }
  var n = 0;
  fetch('/api/admin/custom-forms', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d || !d.ok) return;
    n = (d.forms || []).reduce(function (s, f) { return s + (f.nouveaux || 0); }, 0);
    apply(n);
    new MutationObserver(function () {
      var a = document.querySelector('nav.side a[href="SA-Formulaires.dc.html"]');
      if (a && n && !a.querySelector('.fm-badge')) apply(n);
    }).observe(document.documentElement, { childList: true, subtree: true });
  }, function () {});
})();
</script>
"""

LINK = '<a href="SA-Formulaires.dc.html">Formulaires</a>'


def add_menu(tpl):
    """Lien « Formulaires » juste avant « Comptes » dans le menu latéral, et dans la liste « Page à gérer »."""
    if 'href="SA-Formulaires.dc.html"' not in tpl and '<a href="SA-Comptes.html">Comptes</a>' in tpl:
        tpl = tpl.replace('<a href="SA-Comptes.html">Comptes</a>', LINK + '<a href="SA-Comptes.html">Comptes</a>', 1)
    for sel in ('jump-page', 'jump'):
        m = re.search(r'<sc-raw-select class="in" id="' + sel + r'">.*?</sc-raw-select>', tpl, re.S)
        if m and '<option>Formulaires</option>' not in m.group(0) and '<option>Comptes</option>' in m.group(0):
            new = m.group(0).replace('<option>Comptes</option>', '<option>Formulaires</option><option>Comptes</option>', 1)
            tpl = tpl[:m.start()] + new + tpl[m.end():]
    return tpl


def wire_page():
    src = ROOT / 'SA-Pages.dc.html'
    s, i, j, tpl = load(src)
    assert 'id="sa-pages-list"' in tpl, 'lancer wire_pages.py avant wire_formulaires.py'
    tpl = re.sub(r'<title>.*?</title>', '<title>Superadmin · Formulaires — ASCIL</title>', tpl, count=1)
    a = tpl.index('<main')
    a = tpl.index('>', a) + 1
    b = tpl.index('</main>', a)
    tpl = tpl[:a] + MAIN + tpl[b:]
    tpl = re.sub(r'<script id="sa-pages-list">.*?</script>\s*', '', tpl, flags=re.S)
    tpl = tpl.replace('<a href="SA-Pages.dc.html" aria-current="page" class="on">Créer une page</a>', '<a href="SA-Pages.dc.html">Créer une page</a>', 1)
    tpl = add_menu(tpl)
    tpl = tpl.replace(LINK, '<a href="SA-Formulaires.dc.html" aria-current="page" class="on">Formulaires</a>', 1)
    assert 'aria-current="page" class="on">Formulaires</a>' in tpl
    tpl = re.sub(r'<style id="sa-forms-style">.*?</style>\s*', '', tpl, flags=re.S)
    k = tpl.index('</head>')
    tpl = tpl[:k] + STYLE + tpl[k:]
    types = {'texte': 'Texte court', 'paragraphe': 'Texte long', 'courriel': 'Courriel', 'telephone': 'Téléphone', 'nombre': 'Nombre',
             'date': 'Date', 'liste': 'Liste déroulante', 'choix': 'Choix unique', 'cases': 'Cases à cocher'}
    tpl = inject_script(tpl, 'sa-forms', SCRIPT.replace('__ICONS__', json.dumps({k: svg(k) for k in ICON}))
                        .replace('__TYPES__', json.dumps(types, ensure_ascii=False)))
    tpl = inject_script(tpl, 'sa-forms-badge', BADGE)
    out = ROOT / 'SA-Formulaires.dc.html'
    save_as(src, out, s, i, j, tpl)
    print('SA-Formulaires.dc.html : rubrique Formulaires créée')


def save_as(src, out, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    out.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def wire_menus():
    n = 0
    for path in sorted(ROOT.glob('SA-*.dc.html')):
        if path.name in ('SA-Formulaires.dc.html', 'SA-Connexion.dc.html'):
            continue
        s, i, j, tpl = load(path)
        if '<nav class="side nav"' not in tpl:
            continue
        new = inject_script(add_menu(tpl), 'sa-forms-badge', BADGE)
        if new != tpl:
            save(path, s, i, j, new)
            n += 1
    # Comptes : page écrite à la main (hors maquette).
    p = ROOT / 'SA-Comptes.html'
    if p.exists():
        c = p.read_text(encoding='utf-8')
        if 'href="SA-Formulaires.dc.html"' not in c:
            c2 = c.replace('   <a href="SA-Comptes.html" aria-current="page" class="on">Comptes</a>',
                           '   <a href="SA-Formulaires.dc.html">Formulaires</a>\n   <a href="SA-Comptes.html" aria-current="page" class="on">Comptes</a>', 1)
            assert c2 != c, 'menu de SA-Comptes.html introuvable'
            c = c2
        if 'id="sa-forms-badge"' not in c:
            k = c.rindex('</body>')
            c = c[:k] + BADGE + c[k:]
        p.write_text(c, encoding='utf-8')
    print(f'menu « Formulaires » ajouté à {n} pages du panneau (et Comptes)')


if __name__ == '__main__':
    wire_page()
    wire_menus()
