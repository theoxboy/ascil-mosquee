"""Branche « Site entier → Pages publiées » (superadmin) sur la base, et l'applique au site public.

1. SA-Site.dc.html : le composant de la page
   - charge l'état réel des pages depuis GET /api/admin/settings/pages ;
   - « Enregistrer » écrit vraiment (PUT), « Annuler » revient au dernier état enregistré ;
   - « Accueil » ne peut pas être masquée.
   Seules les pages publiées sont enregistrées pour l'instant ; les autres réglages de la page
   (saison, langues, bannière) le diront honnêtement au lieu de prétendre être enregistrés.
   « Compte et sécurité » affiche les vraies données de la session (voir wire_account()).

2. Toutes les pages publiques : un petit script lit GET /api/settings/pages et retire du menu,
   du pied de page et des contenus les liens vers une page masquée. L'adresse directe d'une page
   masquée est déjà renvoyée vers l'accueil par le serveur (functions/_middleware.js).

À relancer après scripts/install_superadmin.py (qui régénère les pages SA-*). Idempotent.
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


# ---------------------------------------------------------------- 1. panneau
COMPONENT_PATCHES = [
    # État de départ = ce qui est en ligne aujourd'hui (toutes les pages publiées), en attendant la base.
    ('"pg_cours": false, "pg_mariages": false, "pg_funerailles": false, "pg_aide": false, "pg_femmes": false, '
     '"pg_khutba": false, "pg_rappel": false, "pg_campagne": false, "pg_calendrier": false, "pg_inscription": false, '
     '"pg_dua": false',
     '"pg_cours": true, "pg_mariages": true, "pg_funerailles": true, "pg_aide": true, "pg_femmes": true, '
     '"pg_khutba": true, "pg_rappel": true, "pg_campagne": true, "pg_calendrier": true, "pg_inscription": true, '
     '"pg_dua": true'),
    # Chargement depuis la base + enregistrement réel.
    ("  componentWillUnmount() { clearTimeout(this.tt); }",
     """  componentWillUnmount() { clearTimeout(this.tt); }
  componentDidMount() {
    fetch('/api/admin/settings/pages', { credentials: 'same-origin' })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((d) => {
        if (!d.ok) { this.flash(d.message || 'Impossible de charger l’état des pages. Rechargez la page.'); return; }
        this.base = Object.assign({}, this.base, d.settings);
        this.setState({ on: Object.assign({}, this.state.on, d.settings) });
      })
      .catch(() => this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et rechargez la page.'));
  }
  savePages() {
    if (this.saving) return;
    this.saving = true;
    const on = this.state.on, pages = {};
    Object.keys(on).forEach((k) => { if (k.indexOf('pg_') === 0 && k !== 'pg_accueil') pages[k] = !!on[k]; });
    this.flash('Enregistrement…');
    fetch('/api/admin/settings/pages', {
      method: 'PUT', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(pages)
    })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((d) => {
        this.saving = false;
        if (!d.ok) { this.flash(d.message || 'L’enregistrement a échoué. Réessayez.'); return; }
        this.base = Object.assign({}, this.base, d.settings);
        this.forceUpdate();
        const rest = Object.keys(this.state.on).some((k) => k.indexOf('pg_') !== 0 && this.state.on[k] !== this.base[k]);
        this.flash(rest
          ? 'Pages publiées enregistrées. Les autres réglages de cette page ne sont pas encore reliés : ils n’ont pas été enregistrés.'
          : 'Pages publiées enregistrées. Le site est à jour.');
      })
      .catch(() => { this.saving = false; this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.'); });
  }"""),
    # Accueil ne peut pas être masquée.
    ("      s[k] = { c: String(!!on[k]), t: () => this.setState(",
     "      s[k] = { c: String(!!on[k]), t: () => k === 'pg_accueil' ? null : this.setState("),
    # Le bouton « Enregistrer » enregistre vraiment.
    ("      save: () => { this.base = Object.assign({}, this.state.on); this.forceUpdate(); this.flash('Réglages enregistrés. Le site est à jour.'); },",
     "      save: () => this.savePages(),"),
]


def wire_panel():
    path = ROOT / 'SA-Site.dc.html'
    s, i, j, tpl = load(path)
    if 'savePages()' in tpl:
        print('SA-Site.dc.html : déjà branché')
        return
    for a, b in COMPONENT_PATCHES:
        assert tpl.count(a) == 1, a[:70]
        tpl = tpl.replace(a, b)
    save(path, s, i, j, tpl)
    print('SA-Site.dc.html : Pages publiées branchées sur la base')


# ---------------------------------------------------------------- 2. site public
PUBLIC_SCRIPT = r'''<script id="ascil-pages-sync">
(function () {
  var FILES = { pg_horaires: 'Horaires', pg_apropos: 'APropos', pg_services: 'Services', pg_dons: 'Dons',
    pg_evenements: 'Evenements', pg_ressources: 'Ressources', pg_contact: 'Contact', pg_cours: 'N2-Cours',
    pg_mariages: 'N2-Mariages', pg_funerailles: 'N2-Funerailles', pg_aide: 'N2-AideAlimentaire',
    pg_femmes: 'N2-EspaceFemmes', pg_khutba: 'N2-Khutba', pg_rappel: 'N3-Rappel', pg_campagne: 'N3-Campagne',
    pg_calendrier: 'N3-Calendrier', pg_inscription: 'N3-Inscription', pg_dua: 'N3-Dua' };
  var hidden = {};
  function fileOf(href) {
    var m = /^(?:\.?\/)?(?:M-|T-)?([A-Za-z0-9-]+?)\.dc(?:\.html)?(?:[?#].*)?$/.exec(href || '');
    return m ? m[1] : null;
  }
  function apply() {
    var links = document.querySelectorAll('a[href]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i], f = fileOf(a.getAttribute('href'));
      if (!f || !hidden[f] || a.getAttribute('data-ascil-hidden')) continue;
      a.setAttribute('data-ascil-hidden', '1');
      // Dans une liste (menu, pied de page), on retire la ligne entière.
      var li = a.parentElement && a.parentElement.tagName === 'LI' && a.parentElement.children.length === 1 ? a.parentElement : null;
      (li || a).style.display = 'none';
    }
  }
  fetch('/api/settings/pages', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.ok) return;
      Object.keys(FILES).forEach(function (k) { if (d.settings[k] === false) hidden[FILES[k]] = true; });
      if (!Object.keys(hidden).length) return;
      if (hidden[fileOf(location.pathname.split('/').pop())]) { location.replace('/'); return; }
      apply();
      new MutationObserver(apply).observe(document.documentElement, { childList: true, subtree: true });
    }, function () {});
})();
</script>
'''


def wire_public():
    n = 0
    for path in sorted(ROOT.glob('*.dc.html')) + [ROOT / 'index.html']:
        if path.name.startswith('SA-'):
            continue
        s, i, j, tpl = load(path)
        tpl = re.sub(r'<script id="ascil-pages-sync">.*?</script>\s*', '', tpl, flags=re.S)
        k = tpl.rindex('</body>')
        tpl = tpl[:k] + PUBLIC_SCRIPT + tpl[k:]
        save(path, s, i, j, tpl)
        n += 1
    print('pages publiques reliées :', n)


# ---------------------------------------------------------------- 3. Compte et sécurité
# La maquette affichait des valeurs inventées (nom, sessions « ce Mac / iPhone », journal fictif,
# sauvegardes) et des interrupteurs sans effet (validation en deux étapes, déconnexion auto).
# On les remplace par les vraies données de la session, et on retire ce qui n'existe pas.
ACCOUNT_HTML = (
    '<div id="sp-2" class="sp"><div class="sp-h"><div style="flex:1;min-width:220px"><p class="eyebrow">Votre accès</p>'
    '<h2 class="serif" style="margin:4px 0 0;font-size:26px;color:#0E4D3C;font-weight:700">Compte et sécurité</h2>'
    '<p class="dsc" style="margin-top:4px">Votre compte, vos appareils connectés et l’historique des changements.</p></div></div>'

    '<section class="card" aria-labelledby="acc-t1"><div class="card-h"><span class="num" aria-hidden="true">1</span>'
    '<div><h3 class="ttl" id="acc-t1">Mon compte</h3></div></div><div class="card-b">'
    '<dl id="acc-info" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px 24px;margin:10px 0 0">'
    '<div><dt class="lbl">Nom affiché</dt><dd id="acc-name" style="margin:4px 0 0;overflow-wrap:anywhere">Chargement…</dd></div>'
    '<div><dt class="lbl">Identifiant</dt><dd id="acc-user" style="margin:4px 0 0;overflow-wrap:anywhere">—</dd></div>'
    '<div><dt class="lbl">Rôle</dt><dd id="acc-role" style="margin:4px 0 0">—</dd></div>'
    '<div><dt class="lbl">Courriel</dt><dd id="acc-mail" style="margin:4px 0 0;overflow-wrap:anywhere">—</dd></div></dl>'
    '<form id="acc-pw" novalidate style="margin-top:18px;display:flex;flex-direction:column;gap:12px">'
    '<p class="lbl" style="margin:0">Changer le mot de passe</p>'
    '<div class="g2" style="align-items:start">'
    '<div class="fld"><label class="lbl" for="acc-cur">Mot de passe actuel</label><input class="in" id="acc-cur" type="password" autocomplete="current-password"></div>'
    '<div class="fld"><label class="lbl" for="acc-new">Nouveau mot de passe</label><input class="in" id="acc-new" type="password" autocomplete="new-password" aria-describedby="acc-pw-hint"><p class="hint" id="acc-pw-hint">12 caractères minimum. Une courte phrase fonctionne bien.</p></div>'
    '</div>'
    '<div class="g2" style="align-items:start"><div class="fld"><label class="lbl" for="acc-new2">Confirmez le nouveau mot de passe</label><input class="in" id="acc-new2" type="password" autocomplete="new-password"></div></div>'
    '<p id="acc-pw-msg" role="status" aria-live="polite" class="hint" style="margin:0"></p>'
    '<div><button type="submit" class="btn btn-line" id="acc-pw-btn">Changer le mot de passe</button></div>'
    '</form></div></section>'

    '<section class="card" aria-labelledby="acc-t2"><div class="card-h"><span class="num" aria-hidden="true">2</span>'
    '<div><h3 class="ttl" id="acc-t2">Appareils connectés</h3><p class="dsc">Les sessions ouvertes sur votre compte en ce moment.</p></div></div>'
    '<div class="card-b"><ul id="acc-sessions" style="list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:8px"><li class="hint">Chargement…</li></ul>'
    '<p id="acc-sess-msg" role="status" aria-live="polite" class="hint" style="margin:10px 0 0"></p>'
    '<div style="margin-top:10px"><button type="button" class="btn btn-line" id="acc-revoke">Déconnecter les autres appareils</button></div>'
    '</div></section>'

    '<section class="card" id="acc-journal" aria-labelledby="acc-t3" hidden><div class="card-h"><span class="num" aria-hidden="true">3</span>'
    '<div><h3 class="ttl" id="acc-t3">Journal des modifications</h3><p class="dsc">Les 20 dernières actions dans le panneau : qui, quoi, quand.</p></div></div>'
    '<div class="card-b"><div style="overflow-x:auto;margin-top:10px;border:1px solid #E4D9C0;border-radius:12px;background:#fff" tabindex="0" aria-label="Journal des modifications, défilable horizontalement">'
    '<table style="width:100%;border-collapse:collapse;font-size:14px;min-width:520px"><caption class="sr" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Journal des modifications</caption>'
    '<thead><tr style="background:#F6EEDF;color:#0E4D3C;text-align:left">'
    '<th scope="col" style="padding:10px 12px">Quand</th><th scope="col" style="padding:10px 12px">Action</th><th scope="col" style="padding:10px 12px">Par</th></tr></thead>'
    '<tbody id="acc-journal-rows"><tr><td colspan="3" style="padding:10px 12px" class="hint">Chargement…</td></tr></tbody></table></div>'
    '</div></section>'
    '</div>'
)

ACCOUNT_SCRIPT = r"""<script id="sa-site-account">
(function () {
  var ROLE = { superadmin: 'Superadmin', editor: 'Éditeur', events: 'Responsable événements' };
  var ACTIONS = {
    'auth.login': 'Connexion', 'auth.logout': 'Déconnexion', 'auth.login_failed': 'Échec de connexion',
    'auth.password_changed': 'Mot de passe changé', 'auth.sessions_revoked': 'Autres appareils déconnectés',
    'account.create': 'Compte créé', 'account.update': 'Compte modifié', 'account.reset_password': 'Mot de passe réinitialisé',
    'events.settings_update': 'Réglages de l’événement modifiés', 'events.registration_cancel': 'Inscription annulée'
  };
  var TARGETS = { 'settings:home': 'Accueil', 'settings:pages': 'Pages publiées', 'settings:event_registration': 'Événement' };
  function $(id) { return document.getElementById(id); }
  function text(id, v) { var e = $(id); if (e) e.textContent = v; }
  function when(iso) {
    var d = new Date(iso);
    return isNaN(d) ? '—' : d.toLocaleString('fr-CA', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  }
  function device(ua) {
    var os = /iPhone/.test(ua) ? 'iPhone' : /iPad/.test(ua) ? 'iPad' : /Android/.test(ua) ? 'Android'
      : /Macintosh|Mac OS X/.test(ua) ? 'Mac' : /Windows/.test(ua) ? 'Windows' : /Linux/.test(ua) ? 'Linux' : 'Appareil inconnu';
    var br = /Edg\//.test(ua) ? 'Edge' : /Firefox\//.test(ua) ? 'Firefox' : /Chrome\//.test(ua) ? 'Chrome' : /Safari\//.test(ua) ? 'Safari' : '';
    return br ? os + ' · ' + br : os;
  }
  function getJson(url, opt) {
    return fetch(url, Object.assign({ credentials: 'same-origin' }, opt || {}))
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }).then(function (d) { d.status = r.status; return d; }); });
  }
  function loadMe() {
    getJson('/api/auth/me').then(function (d) {
      if (!d.ok) { text('acc-name', 'Impossible de charger votre compte. Rechargez la page.'); return; }
      var a = d.admin;
      text('acc-name', a.displayName || '—');
      text('acc-user', a.username);
      text('acc-role', a.roleLabel || ROLE[a.role] || a.role);
      text('acc-mail', a.email || 'Aucun courriel enregistré');
      if (a.role === 'superadmin') loadJournal();
    }, function () { text('acc-name', 'Impossible de joindre le serveur. Rechargez la page.'); });
  }
  function loadSessions() {
    getJson('/api/auth/sessions').then(function (d) {
      var ul = $('acc-sessions'); if (!ul) return;
      ul.innerHTML = '';
      if (!d.ok) { ul.innerHTML = '<li class="hint">Impossible de charger les appareils connectés.</li>'; return; }
      d.sessions.forEach(function (s) {
        var li = document.createElement('li');
        li.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;padding:10px 12px;border:1px solid #E4D9C0;border-radius:12px;background:#fff';
        var b = document.createElement('strong'); b.textContent = device(s.userAgent) + (s.current ? ' (cet appareil)' : '');
        var span = document.createElement('span'); span.className = 'hint'; span.style.margin = '0';
        span.textContent = 'Dernière activité : ' + when(s.lastSeenAt) + ' · connecté le ' + when(s.createdAt);
        li.appendChild(b); li.appendChild(span); ul.appendChild(li);
      });
      var others = d.sessions.filter(function (s) { return !s.current; }).length;
      var btn = $('acc-revoke'); if (btn) btn.style.display = others ? '' : 'none';
      text('acc-sess-msg', others ? '' : 'Aucun autre appareil n’est connecté à votre compte.');
    });
  }
  function loadJournal() {
    getJson('/api/admin/audit?limit=20').then(function (d) {
      var card = $('acc-journal'), body = $('acc-journal-rows');
      if (!d.ok || !card || !body) return;
      card.hidden = false;
      body.innerHTML = '';
      if (!d.entries.length) { body.innerHTML = '<tr><td colspan="3" style="padding:10px 12px" class="hint">Aucune action enregistrée pour l’instant.</td></tr>'; return; }
      d.entries.forEach(function (e) {
        var tr = document.createElement('tr'); tr.style.borderTop = '1px solid #F3EAD8';
        var label = (ACTIONS[e.action] || e.action) + (e.target && TARGETS[e.target] ? ' : ' + TARGETS[e.target] : '');
        [when(e.createdAt), label, e.username].forEach(function (v) {
          var td = document.createElement('td'); td.style.padding = '10px 12px'; td.textContent = v; tr.appendChild(td);
        });
        body.appendChild(tr);
      });
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('#acc-revoke');
    if (!b || b.getAttribute('aria-busy') === 'true') return;
    b.setAttribute('aria-busy', 'true'); b.textContent = 'Déconnexion en cours…';
    getJson('/api/auth/sessions', { method: 'DELETE', headers: { 'Content-Type': 'application/json' } }).then(function (d) {
      b.removeAttribute('aria-busy'); b.textContent = 'Déconnecter les autres appareils';
      text('acc-sess-msg', d.ok ? (d.closed + ' autre(s) appareil(s) déconnecté(s).') : (d.message || 'L’opération a échoué. Réessayez.'));
      loadSessions();
    }, function () { b.removeAttribute('aria-busy'); b.textContent = 'Déconnecter les autres appareils'; text('acc-sess-msg', 'Impossible de joindre le serveur. Réessayez.'); });
  });
  document.addEventListener('submit', function (e) {
    if (!e.target || e.target.id !== 'acc-pw') return;
    e.preventDefault();
    var cur = $('acc-cur'), n1 = $('acc-new'), n2 = $('acc-new2'), btn = $('acc-pw-btn');
    if (btn.getAttribute('aria-busy') === 'true') return;
    [cur, n1, n2].forEach(function (x) { x.removeAttribute('aria-invalid'); });
    var bad = !cur.value ? [cur, 'Entrez votre mot de passe actuel.']
      : n1.value.length < 12 ? [n1, 'Le nouveau mot de passe doit contenir au moins 12 caractères.']
      : n1.value !== n2.value ? [n2, 'Les deux nouveaux mots de passe ne correspondent pas. Retapez-le.'] : null;
    if (bad) { bad[0].setAttribute('aria-invalid', 'true'); bad[0].focus(); text('acc-pw-msg', bad[1]); return; }
    btn.setAttribute('aria-busy', 'true'); btn.textContent = 'Enregistrement…';
    getJson('/api/auth/password', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current: cur.value, next: n1.value }) }).then(function (d) {
      btn.removeAttribute('aria-busy'); btn.textContent = 'Changer le mot de passe';
      if (d.ok) {
        cur.value = n1.value = n2.value = '';
        text('acc-pw-msg', 'Mot de passe changé. Vos autres appareils ont été déconnectés.');
        loadSessions();
      } else {
        if (d.code === 'wrong_current') { cur.setAttribute('aria-invalid', 'true'); cur.focus(); }
        text('acc-pw-msg', d.message || 'Le changement a échoué. Réessayez.');
      }
    }, function () { btn.removeAttribute('aria-busy'); btn.textContent = 'Changer le mot de passe'; text('acc-pw-msg', 'Impossible de joindre le serveur. Réessayez.'); });
  });
  function start() { loadMe(); loadSessions(); }
  if (document.getElementById('acc-info')) start();
  else new MutationObserver(function (m, obs) { if (document.getElementById('acc-info')) { obs.disconnect(); start(); } })
    .observe(document.documentElement, { childList: true, subtree: true });
})();
</script>
"""


def wire_account():
    path = ROOT / 'SA-Site.dc.html'
    s, i, j, tpl = load(path)
    a = tpl.index('<div id="sp-2" class="sp">')
    depth, end = 0, None
    for m in re.finditer(r'<div\b|</div>', tpl[a:]):
        depth += 1 if m.group(0) != '</div>' else -1
        if depth == 0:
            end = a + m.end()
            break
    assert end, 'section sp-2 mal fermée'
    tpl = tpl[:a] + ACCOUNT_HTML + tpl[end:]
    tpl = re.sub(r'<script id="sa-site-account">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + ACCOUNT_SCRIPT + tpl[k:]
    save(path, s, i, j, tpl)
    print('SA-Site.dc.html : Compte et sécurité relié aux vraies données')


if __name__ == '__main__':
    wire_panel()
    wire_account()
    wire_public()
