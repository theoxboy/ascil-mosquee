"""Branche « Site entier → Pages publiées » (superadmin) sur la base, et l'applique au site public.

1. SA-Site.dc.html : le composant de la page
   - charge l'état réel des pages depuis GET /api/admin/settings/pages ;
   - « Enregistrer » écrit vraiment (PUT), « Annuler » revient au dernier état enregistré ;
   - « Accueil » ne peut pas être masquée.
   Seules les pages publiées sont enregistrées pour l'instant ; les autres réglages de la page
   (saison, langues, bannière) le diront honnêtement au lieu de prétendre être enregistrés.
   « Compte et sécurité » affiche les vraies données de la session (voir wire_account()).

2. Toutes les pages publiques : la bannière d'alerte (GET /api/settings/alert, si active et dans
   sa période) en haut de page, et un petit script qui lit GET /api/settings/pages et retire du menu,
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
    if 'savePages()' in tpl or 'saveAll()' in tpl:  # déjà branché (étapes suivantes incluses)
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


# ---------------------------------------------------------------- 5. Bannière d'alerte (site public)
ALERT_SCRIPT = r"""<script id="ascil-alert-banner">
(function () {
  var FILES = { pg_horaires: 'Horaires', pg_apropos: 'APropos', pg_services: 'Services', pg_dons: 'Dons',
    pg_evenements: 'Evenements', pg_ressources: 'Ressources', pg_contact: 'Contact', pg_cours: 'N2-Cours',
    pg_mariages: 'N2-Mariages', pg_funerailles: 'N2-Funerailles', pg_aide: 'N2-AideAlimentaire',
    pg_femmes: 'N2-EspaceFemmes', pg_khutba: 'N2-Khutba', pg_rappel: 'N3-Rappel', pg_campagne: 'N3-Campagne',
    pg_calendrier: 'N3-Calendrier', pg_inscription: 'N3-Inscription', pg_dua: 'N3-Dua' };
  // Couleurs du site ; contrastes texte / fond : blanc sur vert 9,6:1, encre sur or 6,9:1, blanc sur rouge 6,5:1.
  var TONES = {
    info: { bg: '#0E4D3C', fg: '#FFFFFF', label: 'Information' },
    attention: { bg: '#C49A4A', fg: '#1E2B26', label: 'Attention' },
    urgent: { bg: '#B3261E', fg: '#FFFFFF', label: 'Urgent' }
  };
  var ICON = { info: '<circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path>',
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path>' };
  var banner = null;
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function build(a) {
    var t = TONES[a.tone] || TONES.attention;
    var el = document.createElement('div');
    el.id = 'ascil-alert';
    el.setAttribute('role', 'region');
    el.setAttribute('aria-label', 'Information importante');
    el.style.cssText = 'position:relative;z-index:60;background:' + t.bg + ';color:' + t.fg +
      ';font:600 15px/1.45 "Noto Sans",system-ui,sans-serif;padding:10px 16px';
    var row = document.createElement('div');
    row.style.cssText = 'max-width:1180px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;text-align:center';
    var svg = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" style="flex:none">' + (a.tone === 'info' ? ICON.info : ICON.alert) + '</svg>';
    row.innerHTML = svg;
    var msg = document.createElement('p');
    msg.style.cssText = 'margin:0;min-width:0;overflow-wrap:anywhere';
    var sr = document.createElement('span');
    sr.textContent = t.label + ' : ';
    sr.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap';
    msg.appendChild(sr);
    msg.appendChild(document.createTextNode(a.message));
    row.appendChild(msg);
    var href = a.link && a.link.type === 'page' && FILES[a.link.page] ? FILES[a.link.page] + '.dc.html'
      : a.link && a.link.type === 'url' ? a.link.url : '';
    if (href) {
      var link = document.createElement('a');
      link.href = href;
      link.textContent = 'En savoir plus';
      link.style.cssText = 'color:inherit;text-decoration:underline;text-underline-offset:3px;display:inline-flex;align-items:center;min-height:24px;padding:2px 4px';
      if (a.link.type === 'url') { link.target = '_blank'; link.rel = 'noopener'; }
      row.appendChild(link);
    }
    el.appendChild(row);
    return el;
  }
  function place() {
    if (!banner || !document.body) return;
    if (document.body.firstChild !== banner) document.body.insertBefore(banner, document.body.firstChild);
  }
  fetch('/api/settings/alert', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.ok) return;
      var a = d.settings, now = today();
      if (!a.on || !a.message) return;
      if (a.from && now < a.from) return;
      if (a.to && now > a.to) return;
      banner = build(a);
      place();
      new MutationObserver(place).observe(document.body, { childList: true });
    }, function () {});
})();
</script>
"""


# ---------------------------------------------------------------- 7. Langues et saison (site public)
LANG_SCRIPT = r"""<script id="ascil-languages">
(function () {
  var off = {};
  function hide(el) { if (el && el.style.display !== 'none') el.style.display = 'none'; }
  function apply() {
    // Liste déroulante (PC) : « العربية », « English » ; pastilles du menu mobile : « العربية », « EN ».
    document.querySelectorAll('li[role="option"]').forEach(function (li) {
      var t = li.textContent.trim();
      if ((off.ar && t === 'العربية') || (off.en && t === 'English')) hide(li);
    });
    document.querySelectorAll('span.pill').forEach(function (p) {
      var t = p.textContent.trim();
      if ((off.ar && t === 'العربية') || (off.en && t === 'EN')) hide(p);
      // Plus aucune autre langue : on retire toute la rangée de pastilles.
      if (off.ar && off.en && t === 'FR' && p.parentElement) hide(p.parentElement);
    });
    if (off.ar && off.en) document.querySelectorAll('.lang-desk').forEach(hide);
  }
  fetch('/api/settings/languages', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.ok) return;
      off = { ar: d.settings.ar === false, en: d.settings.en === false };
      if (!off.ar && !off.en) return;
      apply();
      new MutationObserver(apply).observe(document.documentElement, { childList: true, subtree: true });
    }, function () {});
})();
</script>
"""

SEASON_SCRIPT = r"""<script id="ascil-season">
(function () {
  var TEXT = {
    ramadan: { title: 'Ramadan Moubarak', ar: 'رمضان مبارك' },
    aid_fitr: { title: 'Aïd al-Fitr Moubarak', ar: 'عيد فطر مبارك',
      sub: 'Bonne fête à toutes et à tous. L’heure de la prière de l’Aïd est indiquée dans les horaires.' },
    aid_adha: { title: 'Aïd al-Adha Moubarak', ar: 'عيد أضحى مبارك',
      sub: 'Bonne fête à toutes et à tous. L’heure de la prière de l’Aïd est indiquée dans les horaires.' }
  };
  var band = null;
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function active(s) {
    if (!s || s.mode === 'normal' || !TEXT[s.mode]) return false;
    if (!s.auto) return true;
    var now = today();
    return !!s.from && !!s.to && now >= s.from && now <= s.to;
  }
  function build(mode, priere) {
    var t = TEXT[mode];
    var el = document.createElement('section');
    el.id = 'ascil-season';
    el.setAttribute('aria-label', t.title);
    // Fond vert du site : texte crème 8,6:1 ; titre arabe en or, en grand (≥ 18,7 px gras) : 4,3:1.
    el.style.cssText = 'background:#0E4D3C;color:#F3EAD8;border-radius:20px;padding:20px 24px;margin:16px auto;' +
      'max-width:1180px;box-sizing:border-box;display:flex;flex-wrap:wrap;align-items:center;gap:12px 24px;' +
      'font-family:"Noto Sans",system-ui,sans-serif';
    var head = document.createElement('div');
    head.style.cssText = 'flex:1 1 260px;min-width:0';
    var h = document.createElement('p');
    h.style.cssText = 'margin:0;font-size:24px;font-weight:800;color:#FFFFFF;line-height:1.2';
    h.textContent = t.title;
    var ar = document.createElement('p');
    ar.lang = 'ar'; ar.dir = 'rtl';
    ar.style.cssText = 'margin:4px 0 0;font-size:22px;font-weight:700;color:#C49A4A;text-align:start';
    ar.textContent = t.ar;
    head.appendChild(h); head.appendChild(ar);
    var info = document.createElement('p');
    info.style.cssText = 'margin:0;flex:1 1 260px;min-width:0;font-size:16px;line-height:1.5';
    if (mode === 'ramadan') {
      var parts = [];
      if (priere && priere.fajr) parts.push('Suhoor jusqu’à ' + priere.fajr);
      if (priere && priere.maghreb) parts.push('Iftar à ' + priere.maghreb);
      info.textContent = parts.length ? parts.join(' · ') + ' (aujourd’hui).' : 'Les heures de Suhoor et d’Iftar sont indiquées dans les horaires du mois.';
    } else {
      info.textContent = t.sub;
    }
    var link = document.createElement('a');
    link.href = 'Horaires.dc.html';
    link.textContent = 'Horaires du mois';
    link.style.cssText = 'display:inline-flex;align-items:center;min-height:44px;padding:0 18px;border-radius:999px;' +
      'background:#C49A4A;color:#1E2B26;font-weight:700;text-decoration:none';
    el.appendChild(head); el.appendChild(info); el.appendChild(link);
    return el;
  }
  function place() {
    var main = document.querySelector('main');
    if (!band || !main) return;
    if (main.firstElementChild !== band) main.insertBefore(band, main.firstChild);
  }
  var get = function (k) { return fetch('/api/settings/' + k, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }); };
  get('season').then(function (d) {
    if (!d || !d.ok || !active(d.settings)) return;
    var mode = d.settings.mode;
    (mode === 'ramadan' ? get('home') : Promise.resolve(null)).then(function (h) {
      band = build(mode, h && h.ok ? h.settings.priere : null);
      place();
      new MutationObserver(place).observe(document.documentElement, { childList: true, subtree: true });
    }, function () {});
  }, function () {});
})();
</script>
"""
HOME_PAGES = {'Main.dc.html', 'index.html', 'M-Accueil.dc.html', 'T-Accueil.dc.html'}


def wire_public():
    n = 0
    for path in sorted(ROOT.glob('*.dc.html')) + [ROOT / 'index.html']:
        if path.name.startswith('SA-'):
            continue
        s, i, j, tpl = load(path)
        tpl = re.sub(r'<script id="ascil-(?:pages-sync|alert-banner|languages|season)">.*?</script>\s*', '', tpl, flags=re.S)
        k = tpl.rindex('</body>')
        extra = SEASON_SCRIPT if path.name in HOME_PAGES else ''
        tpl = tpl[:k] + PUBLIC_SCRIPT + ALERT_SCRIPT + LANG_SCRIPT + extra + tpl[k:]
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
    'events.settings_update': 'Réglages de l’événement modifiés', 'events.registration_cancel': 'Inscription annulée',
    'settings.update': 'Réglages modifiés', 'pages.create': 'Page créée', 'pages.update': 'Page modifiée',
    'pages.duplicate': 'Page dupliquée', 'pages.delete': 'Page supprimée'
  };
  var TARGETS = { 'settings:home': 'Accueil', 'settings:pages': 'Pages publiées', 'settings:event_registration': 'Événement',
    'settings:alert': 'Bannière d’alerte', 'settings:season': 'Mode du site', 'settings:languages': 'Langues' };
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


# ---------------------------------------------------------------- 4. Bannière d'alerte (panneau)
# Liste des liens possibles : uniquement de vraies pages du site (la maquette proposait une page
# inventée), ou une adresse externe saisie dans un champ dédié.
ALERT_LINKS = [
    ('', 'Aucun lien'),
    ('pg_horaires', 'Page : Horaires du mois'), ('pg_evenements', 'Page : Événements'),
    ('pg_inscription', 'Page : Inscription aux événements'), ('pg_dons', 'Page : Faire un don'),
    ('pg_campagne', 'Page : Campagne en direct'), ('pg_contact', 'Page : Contact'),
    ('pg_apropos', 'Page : À propos'), ('pg_services', 'Page : Services'), ('pg_ressources', 'Page : Ressources'),
    ('__url', 'Lien externe…'),
]

ALERT_CARD_PATCHES = [
    ('<input class="in" id="f4" type="text" value="La mosquée est fermée ce soir à cause de la tempête." placeholder="Message court">',
     '<input class="in" id="f4" type="text" value="" maxlength="200" placeholder="Ex. La mosquée est fermée ce soir à cause de la tempête." aria-describedby="alert-msg-hint">'
     '<p class="hint" id="alert-msg-hint">200 caractères au plus. La bannière ne s’affiche que si un message est saisi.</p>'),
    ('<sc-raw-select class="in" id="f5"><option>Page : Horaires du mois</option><option>Ma page : Inscriptions Ramadan 2027</option><option>Lien externe…</option></sc-raw-select></div>',
     '<sc-raw-select class="in" id="f5">' + ''.join('<option>' + label + '</option>' for _, label in ALERT_LINKS) + '</sc-raw-select>'
     '<div id="alert-url-wrap" style="display:none;flex-direction:column;gap:6px;margin-top:8px">'
     '<label class="lbl" for="alert-url">Adresse du lien externe</label>'
     '<input class="in" id="alert-url" type="url" placeholder="https://…" maxlength="500"></div></div>'),
    ('<input class="in tnum" id="f6" type="date" value="2026-11-10">',
     '<input class="in tnum" id="f6" type="date" value="" aria-describedby="alert-dates-hint">'),
    ('<input class="in tnum" id="f7" type="date" value="2026-11-11"></div></div>',
     '<input class="in tnum" id="f7" type="date" value=""></div></div>'
     '<p class="hint" id="alert-dates-hint" style="margin:-4px 0 0">Laissez vide pour afficher dès maintenant, ou sans date de fin.</p>'),
    ('<button type="button" aria-pressed="false">Information (vert)</button><button type="button" aria-pressed="true">Attention (or)</button><button type="button" aria-pressed="false">Urgent (rouge)</button>',
     '<button type="button" data-alert-tone="info" aria-pressed="false">Information (vert)</button>'
     '<button type="button" data-alert-tone="attention" aria-pressed="true">Attention (or)</button>'
     '<button type="button" data-alert-tone="urgent" aria-pressed="false">Urgent (rouge)</button>'),
]

ALERT_METHODS = """  alertLinks() { return __ALERT_LINKS__; }
  readAlertForm() {
    const v = (id) => { const e = document.getElementById(id); return e ? e.value : ''; };
    const sel = document.getElementById('f5');
    const label = sel && sel.selectedIndex > -1 ? sel.options[sel.selectedIndex].text.trim() : '';
    const found = this.alertLinks().find((x) => x[1] === label);
    const key = found ? found[0] : '';
    const pressed = document.querySelector('[data-alert-tone][aria-pressed="true"]');
    return {
      on: !!this.state.on.alerte,
      message: v('f4').replace(/\\s+/g, ' ').trim(),
      link: key === '__url' ? { type: 'url', url: v('alert-url').trim() } : key ? { type: 'page', page: key } : { type: 'none' },
      from: v('f6'), to: v('f7'),
      tone: pressed ? pressed.getAttribute('data-alert-tone') : 'attention'
    };
  }
  setAlertForm(a) {
    const set = (id, val) => { const e = document.getElementById(id); if (e) e.value = val || ''; };
    set('f4', a.message); set('f6', a.from); set('f7', a.to);
    const key = a.link && a.link.type === 'url' ? '__url' : a.link && a.link.type === 'page' ? a.link.page : '';
    const sel = document.getElementById('f5');
    if (sel) {
      const label = (this.alertLinks().find((x) => x[0] === key) || this.alertLinks()[0])[1];
      for (let i = 0; i < sel.options.length; i++) if (sel.options[i].text.trim() === label) sel.selectedIndex = i;
    }
    set('alert-url', a.link && a.link.type === 'url' ? a.link.url : '');
    this.showAlertUrl();
    document.querySelectorAll('[data-alert-tone]').forEach((b) => b.setAttribute('aria-pressed', String(b.getAttribute('data-alert-tone') === a.tone)));
  }
  showAlertUrl() {
    const w = document.getElementById('alert-url-wrap'), sel = document.getElementById('f5');
    if (w && sel) w.style.display = sel.selectedIndex > -1 && sel.options[sel.selectedIndex].text.trim() === 'Lien externe…' ? 'flex' : 'none';
  }
  alertDirty() {
    if (!this.alertBase) return false;
    return JSON.stringify(this.readAlertForm()) !== JSON.stringify(Object.assign({}, this.alertBase, { on: !!this.base.alerte }));
  }
  listenAlert() {
    const inCard = (t) => t && t.closest && t.closest('section[aria-label="Bannière d’alerte"]');
    const changed = (e) => { if (inCard(e.target)) { this.showAlertUrl(); this.forceUpdate(); } };
    document.addEventListener('input', changed);
    document.addEventListener('change', changed);
    document.addEventListener('click', (e) => {
      const b = e.target.closest && e.target.closest('[data-alert-tone]');
      if (!b) return;
      document.querySelectorAll('[data-alert-tone]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      this.forceUpdate();
    });
  }
  loadAlert() {
    fetch('/api/admin/settings/alert', { credentials: 'same-origin' })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((d) => {
        if (!d.ok) { this.flash(d.message || 'Impossible de charger la bannière d’alerte. Rechargez la page.'); return; }
        this.alertBase = d.settings;
        this.base = Object.assign({}, this.base, { alerte: d.settings.on });
        this.setState({ on: Object.assign({}, this.state.on, { alerte: d.settings.on }) });
        this.setAlertForm(d.settings);
      })
      .catch(() => this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et rechargez la page.'));
  }
  saveAll() {
    if (this.saving) return;
    const alert = this.readAlertForm();
    if (alert.on && !alert.message) { this.flash('Écrivez le message de la bannière, ou désactivez-la.'); document.getElementById('f4') && document.getElementById('f4').focus(); return; }
    if (alert.link.type === 'url' && !/^https?:\\/\\/\\S{3,}$/i.test(alert.link.url)) { this.flash('L’adresse du lien externe doit commencer par https://'); return; }
    this.saving = true;
    const on = this.state.on, pages = {};
    Object.keys(on).forEach((k) => { if (k.indexOf('pg_') === 0 && k !== 'pg_accueil') pages[k] = !!on[k]; });
    this.flash('Enregistrement…');
    const put = (key, body) => fetch('/api/admin/settings/' + key, {
      method: 'PUT', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    }).then((r) => r.json().catch(() => ({ ok: false })));
    Promise.all([put('pages', pages), put('alert', alert)])
      .then(([p, a]) => {
        this.saving = false;
        if (!p.ok || !a.ok) { this.flash((!p.ok ? p : a).message || 'L’enregistrement a échoué. Réessayez.'); return; }
        this.alertBase = a.settings;
        this.base = Object.assign({}, this.base, p.settings, { alerte: a.settings.on });
        this.setAlertForm(a.settings);
        this.forceUpdate();
        const rest = Object.keys(this.state.on).some((k) => (k === 'mode_auto' || k.indexOf('lang_') === 0) && this.state.on[k] !== this.base[k]);
        this.flash(rest
          ? 'Pages et bannière enregistrées. Le mode du site et les langues ne sont pas encore reliés : ils n’ont pas été enregistrés.'
          : 'Réglages enregistrés. Le site est à jour.');
      })
      .catch(() => { this.saving = false; this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.'); });
  }
"""


def wire_alert_panel():
    path = ROOT / 'SA-Site.dc.html'
    s, i, j, tpl = load(path)
    if 'saveAll()' in tpl:
        print('SA-Site.dc.html : bannière déjà branchée')
        return
    for a, b in ALERT_CARD_PATCHES:
        assert tpl.count(a) == 1, a[:70]
        tpl = tpl.replace(a, b)
    methods = ALERT_METHODS.replace('__ALERT_LINKS__', json.dumps([list(x) for x in ALERT_LINKS], ensure_ascii=False))
    # savePages() est remplacé par saveAll() (pages + bannière en un seul « Enregistrer »).
    tpl, n = re.subn(r'  savePages\(\) \{.*?\n  \}\n(?=  flash\()', lambda m: methods, tpl, count=1, flags=re.S)
    assert n == 1, 'savePages introuvable'
    patches = [
        ('  componentDidMount() {\n', '  componentDidMount() {\n    this.listenAlert();\n    this.loadAlert();\n'),
        ('const dirty = Object.keys(on).some((k) => on[k] !== this.base[k]);',
         'const dirty = Object.keys(on).some((k) => on[k] !== this.base[k]) || this.alertDirty();'),
        ('      save: () => this.savePages(),', '      save: () => this.saveAll(),'),
        ("      undo: () => { this.setState({ on: Object.assign({}, this.base) }); this.flash('Changements annulés.'); },",
         "      undo: () => { this.setState({ on: Object.assign({}, this.base) }); if (this.alertBase) this.setAlertForm(this.alertBase); this.flash('Changements annulés.'); },"),
    ]
    for a, b in patches:
        assert tpl.count(a) == 1, a[:70]
        tpl = tpl.replace(a, b)
    save(path, s, i, j, tpl)
    print('SA-Site.dc.html : bannière d’alerte branchée sur la base')


# ---------------------------------------------------------------- 6. Mode du site et langues (panneau)
SEASON_CARD_PATCHES = [
    ('<p class="dsc">Change l’accueil (bandeau, couleurs d’accent, horaires Suhoor / Iftar) pendant la période choisie.</p>',
     '<p class="dsc">Affiche un bandeau de saison en haut de l’accueil (vœux, horaires Suhoor et Iftar pour le Ramadan) pendant la période choisie.</p>'),
    ('<button type="button" aria-pressed="true">Normal</button><button type="button" aria-pressed="false">Ramadan</button>'
     '<button type="button" aria-pressed="false">Aïd al-Fitr</button><button type="button" aria-pressed="false">Aïd al-Adha</button>',
     '<button type="button" data-season-mode="normal" aria-pressed="true">Normal</button>'
     '<button type="button" data-season-mode="ramadan" aria-pressed="false">Ramadan</button>'
     '<button type="button" data-season-mode="aid_fitr" aria-pressed="false">Aïd al-Fitr</button>'
     '<button type="button" data-season-mode="aid_adha" aria-pressed="false">Aïd al-Adha</button>'),
    ('<input class="in tnum" id="f2" type="date" value="2027-02-08">', '<input class="in tnum" id="f2" type="date" value="">'),
    ('<input class="in tnum" id="f3" type="date" value="2027-03-09">', '<input class="in tnum" id="f3" type="date" value="">'),
    ('<p class="hint">Sinon, le mode reste celui choisi ci-dessus.</p>',
     '<p class="hint">Activé : le mode ne s’affiche qu’entre les deux dates. Désactivé : il s’affiche tout de suite, jusqu’à ce que vous repassiez en Normal.</p>'),
    ('<p class="hint">Une langue masquée disparaît du sélecteur. Les traductions arriveront avec la base de données.</p>',
     '<p class="hint">Une langue masquée disparaît du sélecteur de toutes les pages. Les textes ne sont pas encore traduits : '
     'choisir العربية ou EN n’affiche pas encore de traduction.</p>'),
]

SEASON_METHODS = """  readSeasonForm() {
    const v = (id) => { const e = document.getElementById(id); return e ? e.value : ''; };
    const pressed = document.querySelector('[data-season-mode][aria-pressed="true"]');
    return { mode: pressed ? pressed.getAttribute('data-season-mode') : 'normal', from: v('f2'), to: v('f3'), auto: !!this.state.on.mode_auto };
  }
  setSeasonForm(a) {
    const set = (id, val) => { const e = document.getElementById(id); if (e) e.value = val || ''; };
    set('f2', a.from); set('f3', a.to);
    document.querySelectorAll('[data-season-mode]').forEach((b) => b.setAttribute('aria-pressed', String(b.getAttribute('data-season-mode') === a.mode)));
  }
  seasonDirty() {
    if (!this.seasonBase) return false;
    return JSON.stringify(this.readSeasonForm()) !== JSON.stringify(Object.assign({}, this.seasonBase, { auto: !!this.base.mode_auto }));
  }
  listenSeason() {
    const inCard = (t) => t && t.closest && t.closest('section[aria-label="Mode du site"]');
    const changed = (e) => { if (inCard(e.target)) this.forceUpdate(); };
    document.addEventListener('input', changed);
    document.addEventListener('change', changed);
    document.addEventListener('click', (e) => {
      const b = e.target.closest && e.target.closest('[data-season-mode]');
      if (!b) return;
      document.querySelectorAll('[data-season-mode]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      this.forceUpdate();
    });
  }
  loadSeason() {
    const get = (key) => fetch('/api/admin/settings/' + key, { credentials: 'same-origin' }).then((r) => r.json().catch(() => ({ ok: false })));
    Promise.all([get('season'), get('languages')])
      .then(([s, l]) => {
        if (!s.ok || !l.ok) { this.flash((!s.ok ? s : l).message || 'Impossible de charger la saison et les langues. Rechargez la page.'); return; }
        this.seasonBase = s.settings;
        const sw = { mode_auto: s.settings.auto, lang_fr: true, lang_ar: l.settings.ar, lang_en: l.settings.en };
        this.base = Object.assign({}, this.base, sw);
        this.setState({ on: Object.assign({}, this.state.on, sw) });
        this.setSeasonForm(s.settings);
      })
      .catch(() => this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et rechargez la page.'));
  }
  saveAll() {
    if (this.saving) return;
    const alert = this.readAlertForm(), season = this.readSeasonForm();
    if (alert.on && !alert.message) { this.flash('Écrivez le message de la bannière, ou désactivez-la.'); document.getElementById('f4') && document.getElementById('f4').focus(); return; }
    if (alert.link.type === 'url' && !/^https?:\\/\\/\\S{3,}$/i.test(alert.link.url)) { this.flash('L’adresse du lien externe doit commencer par https://'); return; }
    if (season.mode !== 'normal' && season.auto && (!season.from || !season.to)) {
      this.flash('Indiquez le début et la fin de la période, ou désactivez le changement automatique aux dates.');
      document.getElementById(season.from ? 'f3' : 'f2') && document.getElementById(season.from ? 'f3' : 'f2').focus();
      return;
    }
    this.saving = true;
    const on = this.state.on, pages = {};
    Object.keys(on).forEach((k) => { if (k.indexOf('pg_') === 0 && k !== 'pg_accueil') pages[k] = !!on[k]; });
    const languages = { fr: true, ar: !!on.lang_ar, en: !!on.lang_en };
    this.flash('Enregistrement…');
    const put = (key, body) => fetch('/api/admin/settings/' + key, {
      method: 'PUT', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    }).then((r) => r.json().catch(() => ({ ok: false })));
    Promise.all([put('pages', pages), put('alert', alert), put('season', season), put('languages', languages)])
      .then(([p, a, se, la]) => {
        this.saving = false;
        const failed = [p, a, se, la].find((x) => !x.ok);
        if (failed) { this.flash(failed.message || 'L’enregistrement a échoué. Réessayez.'); return; }
        this.alertBase = a.settings;
        this.seasonBase = se.settings;
        this.base = Object.assign({}, this.base, p.settings, {
          alerte: a.settings.on, mode_auto: se.settings.auto, lang_fr: true, lang_ar: la.settings.ar, lang_en: la.settings.en
        });
        this.setState({ on: Object.assign({}, this.state.on, { mode_auto: se.settings.auto }) });
        this.setAlertForm(a.settings);
        this.setSeasonForm(se.settings);
        this.forceUpdate();
        this.flash('Réglages enregistrés. Le site est à jour.');
      })
      .catch(() => { this.saving = false; this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.'); });
  }
"""


def wire_season_panel():
    path = ROOT / 'SA-Site.dc.html'
    s, i, j, tpl = load(path)
    if 'readSeasonForm()' in tpl:
        print('SA-Site.dc.html : mode du site et langues déjà branchés')
        return
    for a, b in SEASON_CARD_PATCHES:
        assert tpl.count(a) == 1, a[:70]
        tpl = tpl.replace(a, b)
    # saveAll() est remplacé par la version qui enregistre aussi la saison et les langues.
    tpl, n = re.subn(r'  saveAll\(\) \{.*?\n  \}\n(?=  flash\()', lambda m: SEASON_METHODS, tpl, count=1, flags=re.S)
    assert n == 1, 'saveAll introuvable'
    patches = [
        ('"lang_ar": false, "lang_en": false', '"lang_ar": true, "lang_en": true'),
        ('  componentDidMount() {\n', '  componentDidMount() {\n    this.listenSeason();\n    this.loadSeason();\n'),
        ('|| this.alertDirty();', '|| this.alertDirty() || this.seasonDirty();'),
        ("t: () => k === 'pg_accueil' ? null : this.setState(", "t: () => (k === 'pg_accueil' || k === 'lang_fr') ? null : this.setState("),
        ('if (this.alertBase) this.setAlertForm(this.alertBase);',
         'if (this.alertBase) this.setAlertForm(this.alertBase); if (this.seasonBase) this.setSeasonForm(this.seasonBase);'),
    ]
    for a, b in patches:
        assert tpl.count(a) == 1, a[:70]
        tpl = tpl.replace(a, b)
    save(path, s, i, j, tpl)
    print('SA-Site.dc.html : mode du site et langues branchés sur la base')


if __name__ == '__main__':
    wire_panel()
    wire_alert_panel()
    wire_season_panel()
    wire_account()
    wire_public()
