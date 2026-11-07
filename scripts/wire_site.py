"""Branche « Site entier → Pages publiées » (superadmin) sur la base, et l'applique au site public.

1. SA-Site.dc.html : le composant de la page
   - charge l'état réel des pages depuis GET /api/admin/settings/pages ;
   - « Enregistrer » écrit vraiment (PUT), « Annuler » revient au dernier état enregistré ;
   - « Accueil » ne peut pas être masquée.
   Seules les pages publiées sont enregistrées pour l'instant ; les autres réglages de la page
   (saison, langues, bannière, compte) le diront honnêtement au lieu de prétendre être enregistrés.

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


if __name__ == '__main__':
    wire_panel()
    wire_public()
