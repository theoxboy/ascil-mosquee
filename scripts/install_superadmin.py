"""Installe le frontend superadmin dans le site ASCIL.

Source : la planche /Users/mac/Documents/mosque/superadmin.html (15 maquettes).
Chaque maquette est une page bundlée complète, au même format que les pages du site.
On garde la version PC de chaque écran (les versions mobile et tablette sont le même code,
fluide grâce aux container queries), et on écrit :
  SA-Connexion, SA-Panneau, SA-Site, SA-Pages, SA-PageEditeur, SA-Horaires, SA-APropos,
  SA-Services, SA-Dons, SA-Evenements, SA-Ressources, SA-Contact (.dc.html)
  superadmin.html = point d'entrée (copie de SA-Connexion.dc.html)
Puis on ajoute un lien discret « Espace administration » dans le pied de page du site.
"""
import base64, gzip, json, re, sys, zlib, pathlib

SRC = pathlib.Path(sys.argv[1])
ROOT = pathlib.Path(sys.argv[2])
OPEN = '<script type="__bundler/template">'
VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1">'
ROBOTS = '<meta name="robots" content="noindex, nofollow">'

SCREENS = {  # titre de la planche -> fichier
    'Connexion · PC': 'SA-Connexion.dc.html',
    'Panneau · PC': 'SA-Panneau.dc.html',
    'Superadmin · Site entier': 'SA-Site.dc.html',
    'Superadmin · Horaires': 'SA-Horaires.dc.html',
    'Superadmin · À propos': 'SA-APropos.dc.html',
    'Superadmin · Services': 'SA-Services.dc.html',
    'Superadmin · Faire un don': 'SA-Dons.dc.html',
    'Superadmin · Événements': 'SA-Evenements.dc.html',
    'Superadmin · Ressources': 'SA-Ressources.dc.html',
    'Superadmin · Contact': 'SA-Contact.dc.html',
    'Superadmin · Créer une page': 'SA-Pages.dc.html',
    'Superadmin · Éditeur de page': 'SA-PageEditeur.dc.html',
}
TITLES = {'SA-Panneau.dc.html': 'Superadmin · Accueil — ASCIL'}

# Boutons « Voir la page » vers des pages que le site n'a pas encore.
MISSING = ['Page404.dc.html', 'Merci.dc.html', 'EvenementDetail.dc.html']


def split(text):
    i = text.index(OPEN) + len(OPEN)
    j = text.index('</script>', i)
    return i, j, json.loads(text[i:j])


def join(text, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    return text[:i] + enc + text[j:]


def disable_missing(tpl):
    def repl(m):
        inner = m.group(2)
        return ('<span class="btn btn-line" aria-disabled="true" title="Cette page n’existe pas encore sur le site public"'
                ' style="min-height:40px;opacity:.5;cursor:not-allowed">' + inner + '</span>')
    for name in MISSING:
        pat = re.compile(r'<a class="btn btn-line" href="' + re.escape(name) + r'"( style="min-height:40px")>(.*?)</a>', re.S)
        tpl, n = pat.subn(repl, tpl)
        assert name not in tpl, name
    return tpl


# Sur tablette et mobile le menu latéral est masqué et remplacé par des listes
# « Page à gérer » / « Aller au widget » qui, dans la maquette, ne faisaient rien.
NAV_SCRIPT = r'''<script id="sa-nav">
(function () {
  var PAGES = {
    'Accueil': 'SA-Panneau.dc.html', 'Site entier': 'SA-Site.dc.html', 'Créer une page': 'SA-Pages.dc.html',
    'Horaires': 'SA-Horaires.dc.html', 'À propos': 'SA-APropos.dc.html', 'Services': 'SA-Services.dc.html',
    'Faire un don': 'SA-Dons.dc.html', 'Événements': 'SA-Evenements.dc.html', 'Ressources': 'SA-Ressources.dc.html',
    'Contact': 'SA-Contact.dc.html'
  };
  function labelOf(el) {
    var l = el.id && document.querySelector('label[for="' + el.id + '"]');
    return l ? l.textContent.trim() : '';
  }
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (!t || t.tagName !== 'SELECT' || (t.id !== 'jump' && t.id !== 'jump-page')) return;
    var v = t.value.trim();
    if (labelOf(t).indexOf('Page') === 0) {
      var href = PAGES[v];
      if (href && location.pathname.split('/').pop() !== href) location.href = href;
      return;
    }
    var links = document.querySelectorAll('nav.side a[href^="#"]');
    for (var i = 0; i < links.length; i++) {
      var first = links[i].firstChild ? links[i].firstChild.textContent.trim() : '';
      if (first === v) {
        var target = document.getElementById(links[i].getAttribute('href').slice(1));
        if (target) {
          var hdr = document.querySelector('header.top');
          var off = (hdr && getComputedStyle(hdr).position === 'sticky' ? hdr.offsetHeight : 0) + 12;
          window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - off,
            behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
          var f = target.querySelector('h2, [tabindex]');
          if (f) { f.setAttribute('tabindex', '-1'); f.focus({ preventScroll: true }); }
        }
        return;
      }
    }
  });
})();
</script>
'''


# Déconnexion : les liens « Se déconnecter » ferment la session côté serveur.
LOGOUT_SCRIPT = r'''<script id="sa-logout">
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('a[href="SA-Connexion.dc.html"]');
  if (!a) return;
  e.preventDefault();
  a.setAttribute('aria-busy', 'true');
  fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    .catch(function () {})
    .then(function () { location.href = 'superadmin.html'; });
});
</script>
'''

# Connexion : le formulaire de la maquette était un simple lien vers le panneau.
LOGIN_STYLE = '''<style id="sa-login-style">
.lg-in[aria-invalid="true"]{border-color:#B3261E}
.lg-err{margin:0;padding:10px 14px;border-radius:12px;background:#FBEAE8;color:#8C1D18;font-size:14px;line-height:1.45}
.lg-info{margin:0;padding:10px 14px;border-radius:12px;background:#F7F2E4;color:#4F5E57;font-size:14px;line-height:1.45}
.lg-btn[aria-busy="true"]{cursor:progress}
.lg-spin{width:18px;height:18px;border-radius:50%;border:2.5px solid rgba(255,255,255,.35);border-top-color:#fff;animation:lgspin .8s linear infinite}
@keyframes lgspin{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion: reduce){.lg-spin{animation-duration:2.4s}}
</style>
'''
LOGIN_SCRIPT = r'''<script id="sa-login-js">
(function () {
  function nextUrl() {
    var n = new URLSearchParams(location.search).get('next') || '';
    return /^\/SA-[A-Za-z]+\.dc(\.html)?(\?[^#]*)?$/.test(n) && !/SA-Connexion/.test(n) ? n : 'SA-Panneau.dc.html';
  }
  function show(el, msg) { if (!el) return; el.textContent = msg; el.hidden = !msg; }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('#sa-forgot');
    if (!a) return;
    e.preventDefault();
    show(document.getElementById('sa-login-info'),
      'Le mot de passe se réinitialise depuis l’ordinateur du responsable technique de l’ASCIL. Contactez-le pour en obtenir un nouveau.');
  });
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (!f || f.id !== 'sa-login') return;
    e.preventDefault();
    var id = document.getElementById('sa-id'), pw = document.getElementById('sa-pw');
    var rem = document.getElementById('sa-remember'), btn = document.getElementById('sa-login-btn');
    var err = document.getElementById('sa-login-err');
    if (btn.getAttribute('aria-busy') === 'true') return;
    id.removeAttribute('aria-invalid'); pw.removeAttribute('aria-invalid'); show(err, '');
    if (!id.value.trim() || !pw.value) {
      (!id.value.trim() ? id : pw).setAttribute('aria-invalid', 'true');
      show(err, 'Entrez votre identifiant et votre mot de passe.');
      (!id.value.trim() ? id : pw).focus();
      return;
    }
    var label = btn.innerHTML;
    btn.setAttribute('aria-busy', 'true');
    btn.innerHTML = '<span class="lg-spin" aria-hidden="true"></span>Connexion…';
    fetch('/api/auth/login', {
      method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: id.value.trim(), password: pw.value, remember: !!(rem && rem.checked) })
    }).then(function (r) {
      return r.json().catch(function () { return { ok: false, message: 'Le serveur ne répond pas correctement. Réessayez dans un instant.' }; });
    }).then(function (d) {
      if (d.ok) { location.href = nextUrl(); return; }
      btn.removeAttribute('aria-busy'); btn.innerHTML = label;
      if (d.code === 'invalid') { pw.setAttribute('aria-invalid', 'true'); pw.value = ''; pw.focus(); }
      show(err, d.message || 'La connexion a échoué. Réessayez.');
    }, function () {
      btn.removeAttribute('aria-busy'); btn.innerHTML = label;
      show(err, 'Impossible de joindre le serveur. Vérifiez votre connexion Internet et réessayez.');
    });
  });
})();
</script>
'''


def fix_login(tpl):
    rep = [
        ('<form style="display:flex;flex-direction:column;gap:16px">',
         '<form id="sa-login" novalidate style="display:flex;flex-direction:column;gap:16px">'),
        (' type="password" autocomplete="current-password" value="motdepasse">',
         ' type="password" autocomplete="current-password" aria-describedby="sa-login-err">'),
        ('<a href="#" style="font-size:14px;font-weight:600">Mot de passe oublié ?</a>',
         '<a href="#" id="sa-forgot" style="font-size:14px;font-weight:600">Mot de passe oublié ?</a>'),
        ('<input type="checkbox" style="width:20px;height:20px;accent-color:#0E4D3C;margin:0">',
         '<input type="checkbox" id="sa-remember" style="width:20px;height:20px;accent-color:#0E4D3C;margin:0">'),
    ]
    for a, b in rep:
        assert tpl.count(a) == 1, a
        tpl = tpl.replace(a, b)
    tpl, n = re.subn(r'<a class="lg-btn btn" href="SA-Panneau\.dc\.html">(Se connecter.*?)</a>',
                     lambda m: '<p id="sa-login-err" class="lg-err" role="alert" hidden></p>'
                               '<p id="sa-login-info" class="lg-info" role="status" hidden></p>'
                               '<button type="submit" class="lg-btn btn" id="sa-login-btn">' + m.group(1) + '</button>',
                     tpl, count=1, flags=re.S)
    assert n == 1
    k = tpl.index('</head>')
    tpl = tpl[:k] + LOGIN_STYLE + tpl[k:]
    k = tpl.rindex('</body>')
    return tpl[:k] + LOGIN_SCRIPT + tpl[k:]


def fix_sa(text, out_name):
    if 'name="viewport"' not in text.split(OPEN)[0]:
        text = text.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n  ' + VIEWPORT + '\n  ' + ROBOTS, 1)
    i, j, tpl = split(text)
    if 'name="viewport"' not in tpl:
        tpl = tpl.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + VIEWPORT + '\n' + ROBOTS, 1)
        assert 'name="viewport"' in tpl
    tpl = disable_missing(tpl)
    if 'id="sa-nav"' not in tpl:
        k = tpl.rindex('</body>')
        tpl = tpl[:k] + NAV_SCRIPT + tpl[k:]
    if out_name == 'SA-Connexion.dc.html':
        tpl = fix_login(tpl)
    elif 'id="sa-logout"' not in tpl:
        k = tpl.rindex('</body>')
        tpl = tpl[:k] + LOGOUT_SCRIPT + tpl[k:]
    if out_name in TITLES:
        tpl = re.sub(r'<title>.*?</title>', '<title>' + TITLES[out_name] + '</title>', tpl, count=1)
    return join(text, i, j, tpl)


# 1. Pages superadmin
board = SRC.read_text(encoding='utf-8')
bi, bj, btpl = split(board)
manifest = json.loads(re.search(r'<script type="__bundler/manifest"[^>]*>(.*?)</script>', board, re.S).group(1))
frames = dict(re.findall(r'<h2>(.*?)</h2><iframe src="about:blank#([0-9a-f-]+)"', btpl))
for title, out in SCREENS.items():
    raw = base64.b64decode(manifest[frames[title]]['data'])
    try:
        page = gzip.decompress(raw)
    except OSError:
        page = zlib.decompress(raw, -15)
    page = page.decode('utf-8')
    (ROOT / out).write_text(fix_sa(page, out), encoding='utf-8')
    print('écrit', out)

(ROOT / 'superadmin.html').write_text((ROOT / 'SA-Connexion.dc.html').read_text(encoding='utf-8'), encoding='utf-8')
print('superadmin.html = SA-Connexion.dc.html')

# 2. Lien depuis le site public (pied de page de toutes les pages)
ANCHOR = 'Islamique Louperivoise — Rivière-du-Loup, Québec</p>'
LINK = ('Islamique Louperivoise — Rivière-du-Loup, Québec'
        '<a href="superadmin.html" rel="nofollow" style="float:right;color:#F3EAD8;opacity:.75;'
        'text-decoration:underline;text-underline-offset:3px;display:inline-block;padding:4px 0;margin-left:16px">'
        'Espace administration</a></p>')
n = 0
for p in sorted(ROOT.glob('*.dc.html')) + [ROOT / 'index.html']:
    if p.name.startswith('SA-'):
        continue
    s = p.read_text(encoding='utf-8')
    i, j, tpl = split(s)
    if 'href="superadmin.html"' in tpl:
        continue
    assert tpl.count(ANCHOR) == 1, p.name
    tpl = tpl.replace(ANCHOR, LINK)
    p.write_text(join(s, i, j, tpl), encoding='utf-8')
    n += 1
print('pages du site reliées:', n)
