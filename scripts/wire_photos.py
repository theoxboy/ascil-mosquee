"""Étape P1 : les deux photos de l'Accueil se changent depuis le panneau Accueil (SA-Panneau).

Photos concernées (Main.dc.html, index.html, M-Accueil.dc.html, T-Accueil.dc.html) :
  - « hero »      : grande photo du haut (section Héros) ;
  - « bienvenue » : photo de « Vous venez pour la première fois ? » (section Bienvenue aux visiteurs).

Panneau (SA-Panneau.dc.html) : un bloc « Photo » dans les cartes Héros et Bienvenue aux visiteurs.
  « Choisir une photo » envoie le fichier à /api/admin/media (JPEG, PNG, WebP ou GIF, 5 Mo au plus),
  puis enregistre aussitôt le réglage « photos » (/api/admin/settings/photos) ; « Remettre la photo
  d'origine » vide le réglage ; la description (texte lu par les lecteurs d'écran) s'enregistre avec
  son propre bouton. Ce bloc s'enregistre seul : il ne dépend pas du bouton « Enregistrer » du panneau.
Pages : un petit script (#ascil-photos-live) lit /api/settings/photos et remplace la photo et sa
  description quand une photo est choisie ; sinon la photo d'origine reste. Dernière valeur gardée
  dans le navigateur pour l'afficher sans attendre à la visite suivante.
Ordre : après wire_nettoyage.py, avant wire_langues.py. Idempotent.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'
HOME = ['Main.dc.html', 'index.html', 'M-Accueil.dc.html', 'T-Accueil.dc.html']
ALT_BV = 'alt="Illustration : des membres de la communauté partagent un thé'

LIVE = r"""<script id="ascil-photos-live">
(function () {
  var KEY = 'ascil-photos', s = null;
  var ok = function (u) { return typeof u === 'string' && /^\/media\/[0-9a-f]{32}\.(jpg|png|webp|gif)$/.test(u); };
  try { s = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { s = null; }
  function apply() {
    if (!s) return;
    ['hero', 'bienvenue'].forEach(function (k) {
      var p = s[k];
      if (!p || !ok(p.src)) return;
      document.querySelectorAll('img[data-ascil-photo="' + k + '"]').forEach(function (img) {
        if (img.getAttribute('src') !== p.src) img.setAttribute('src', p.src);
        if (p.alt && img.getAttribute('data-alt-set') !== p.alt) { img.setAttribute('alt', p.alt); img.setAttribute('data-alt-set', p.alt); }
      });
    });
  }
  var timer = null;
  function later() { clearTimeout(timer); timer = setTimeout(apply, 30); }
  apply();
  new MutationObserver(later).observe(document.documentElement, { childList: true, subtree: true });
  fetch('/api/settings/photos').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d || !d.ok || !d.settings) return;
    s = d.settings;
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {}
    apply();
  }, function () {});
})();
</script>
"""

PANEL_CSS = """<style id="sa-photos-css">
.ph-slot{margin-top:18px;padding-top:16px;border-top:1px solid #E4D9C0;display:grid;gap:10px}
.ph-row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}
.ph-prev{inline-size:220px;max-inline-size:100%;aspect-ratio:4/3;border:1px solid #E4D9C0;border-radius:12px;background:#F7F2E4;overflow:hidden;display:flex;align-items:center;justify-content:center;padding:8px;text-align:center;font-size:13px;color:#4F5E57}
.ph-prev img{inline-size:100%;block-size:100%;object-fit:cover;display:block;border-radius:8px}
.ph-side{display:grid;gap:10px;flex:1;min-inline-size:min(100%,240px)}
.ph-btns{display:flex;gap:10px;flex-wrap:wrap}
.ph-btns .btn{min-block-size:44px;padding:0 16px;border-radius:10px;border:1.5px solid #E4D9C0;font-weight:700;font-size:14px;display:inline-flex;align-items:center;gap:8px;cursor:pointer}
.ph-btns .btn:focus-visible,.ph-file:focus-visible+.ph-pick{outline:3px solid #C49A4A;outline-offset:2px}
.ph-btns .btn[disabled]{opacity:.5;pointer-events:none}
.ph-file{position:absolute;inline-size:1px;block-size:1px;opacity:0;overflow:hidden}
.ph-msg{font-size:13px;margin:0;color:#4F5E57;min-block-size:1.2em}
.ph-msg.err{color:#A3261B;font-weight:600}
.ph-msg.ok{color:#0E4D3C;font-weight:600}
</style>
"""


def slot_html(k, title, hint):
    return (
        f'<div class="ph-slot" data-slot="{k}" style="position:relative">'
        f'<span class="lbl" id="ph-t-{k}">{title}</span>'
        f'<p class="hint">{hint}</p>'
        '<div class="ph-row">'
        f'<div class="ph-prev" id="ph-prev-{k}" aria-live="polite">Photo d’origine du site</div>'
        '<div class="ph-side">'
        '<div class="ph-btns">'
        f'<input class="ph-file" type="file" id="ph-file-{k}" accept="image/jpeg,image/png,image/webp,image/gif" aria-labelledby="ph-pick-{k} ph-t-{k}">'
        f'<label class="btn btn-green ph-pick" id="ph-pick-{k}" for="ph-file-{k}">'
        '<svg aria-hidden="true" width="18" height="18" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="M17 8l-5-5-5 5"></path><path d="M12 3v12"></path></svg>'
        'Choisir une photo</label>'
        f'<button type="button" class="btn btn-line" id="ph-reset-{k}">Remettre la photo d’origine</button>'
        '</div>'
        f'<div class="fld"><label class="lbl" for="ph-alt-{k}">Description de la photo</label>'
        f'<input class="in" id="ph-alt-{k}" type="text" maxlength="200" placeholder="Ex. La salle de prière un vendredi">'
        '<p class="hint">Lue à voix haute pour les personnes aveugles. Décrivez ce qu’on voit, en une phrase.</p></div>'
        f'<div class="ph-btns"><button type="button" class="btn btn-line" id="ph-save-{k}">Enregistrer la description</button></div>'
        f'<p class="ph-msg" id="ph-msg-{k}" role="status"></p>'
        '</div></div></div>'
    )


SLOTS = {
    'hero': ('Photo du haut de l’Accueil',
             'Grande photo à côté du titre. Format paysage conseillé (par exemple 1600 × 1000 pixels). JPEG, PNG, WebP ou GIF, 5 Mo au plus.'),
    'bienvenue': ('Photo « Vous venez pour la première fois ? »',
                  'Photo à côté des conseils aux visiteurs. Format paysage conseillé. JPEG, PNG, WebP ou GIF, 5 Mo au plus.'),
}

PANEL_JS = r"""<script id="sa-photos">
(function () {
  var data = { hero: { src: '', alt: '' }, bienvenue: { src: '', alt: '' } }, loaded = false;
  var $ = function (id) { return document.getElementById(id); };
  function msg(k, t, cls) { var m = $('ph-msg-' + k); if (m) { m.textContent = t; m.className = 'ph-msg' + (cls ? ' ' + cls : ''); } }
  function preview(k) {
    var box = $('ph-prev-' + k); if (!box) return;
    var src = data[k].src;
    if (src) {
      var img = box.querySelector('img');
      if (!img) { box.textContent = ''; img = document.createElement('img'); box.appendChild(img); }
      if (img.getAttribute('src') !== src) img.setAttribute('src', src);
      img.setAttribute('alt', data[k].alt || 'Photo choisie');
    } else if (box.querySelector('img') || box.textContent !== 'Photo d’origine du site') {
      box.textContent = 'Photo d’origine du site';
    }
    var reset = $('ph-reset-' + k); if (reset) reset.disabled = !src;
    var alt = $('ph-alt-' + k), save = $('ph-save-' + k);
    if (alt) { alt.disabled = !src; if (alt.getAttribute('data-k') !== k) { alt.value = data[k].alt || ''; alt.setAttribute('data-k', k); } }
    if (save) save.disabled = !src;
  }
  function api(url, opt) {
    return fetch(url, Object.assign({ credentials: 'same-origin' }, opt || {})).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { j.status = r.status; return j; });
    });
  }
  function save(k, okText) {
    return api('/api/admin/settings/photos', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(function (j) {
      if (!j.ok) { msg(k, (j.error && j.error.message) || j.message || 'Enregistrement impossible. Vérifiez votre connexion, puis réessayez.', 'err'); return false; }
      data = j.settings || data; preview(k); msg(k, okText, 'ok'); return true;
    }, function () { msg(k, 'Enregistrement impossible : pas de connexion. Réessayez dans un instant.', 'err'); return false; });
  }
  function bind(k) {
    var file = $('ph-file-' + k), reset = $('ph-reset-' + k), btn = $('ph-save-' + k), pick = $('ph-pick-' + k);
    if (!file || file.getAttribute('data-bound')) return;
    file.setAttribute('data-bound', '1');
    file.addEventListener('change', function () {
      var f = file.files && file.files[0]; file.value = '';
      if (!f) return;
      if (f.size > 5 * 1024 * 1024) { msg(k, 'Cette photo dépasse 5 Mo. Réduisez-la (par exemple avec l’outil de partage du téléphone), puis réessayez.', 'err'); return; }
      msg(k, 'Envoi de la photo…'); if (pick) pick.setAttribute('aria-busy', 'true');
      api('/api/admin/media', { method: 'POST', headers: { 'X-File-Name': encodeURIComponent(f.name || 'photo') }, body: f }).then(function (j) {
        if (pick) pick.removeAttribute('aria-busy');
        if (!j.ok || !j.media || !j.media.url) { msg(k, (j.error && j.error.message) || j.message || 'La photo n’a pas pu être envoyée. Réessayez.', 'err'); return; }
        data[k] = { src: j.media.url, alt: data[k].alt || '' };
        var alt = $('ph-alt-' + k); if (alt) alt.removeAttribute('data-k');
        save(k, 'Photo enregistrée. Elle apparaît sur l’Accueil d’ici une minute environ. Pensez à la décrire ci-dessus.');
      }, function () { if (pick) pick.removeAttribute('aria-busy'); msg(k, 'La photo n’a pas pu être envoyée : pas de connexion. Réessayez.', 'err'); });
    });
    reset.addEventListener('click', function () {
      if (!confirm('Remettre la photo d’origine du site à cet endroit ?')) return;
      data[k] = { src: '', alt: '' };
      var alt = $('ph-alt-' + k); if (alt) alt.removeAttribute('data-k');
      save(k, 'Photo d’origine remise.');
    });
    btn.addEventListener('click', function () {
      var alt = $('ph-alt-' + k); data[k].alt = alt ? alt.value.trim().slice(0, 200) : '';
      save(k, 'Description enregistrée.');
    });
  }
  function tick() { ['hero', 'bienvenue'].forEach(function (k) { bind(k); if (loaded) preview(k); }); }
  api('/api/admin/settings/photos').then(function (j) {
    if (j.ok && j.settings) data = j.settings;
    loaded = true; tick();
  }, function () { loaded = true; tick(); });
  var t = null;
  new MutationObserver(function () { clearTimeout(t); t = setTimeout(tick, 60); }).observe(document.documentElement, { childList: true, subtree: true });
  tick();
})();
</script>
"""


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def save(path, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def public():
    for name in HOME:
        path = ROOT / name
        s, i, j, tpl = load(path)
        tpl = re.sub(r'<script id="ascil-photos-live">.*?</script>\s*', '', tpl, flags=re.S)
        if 'data-ascil-photo="hero"' not in tpl:
            assert tpl.count('<img class="heroimg" ') == 1, name
            tpl = tpl.replace('<img class="heroimg" ', '<img class="heroimg" data-ascil-photo="hero" ', 1)
        if 'data-ascil-photo="bienvenue"' not in tpl:
            k = tpl.index(ALT_BV)
            a = tpl.rindex('<img ', 0, k)
            assert tpl.count(ALT_BV) == 1 and a > k - 200, name
            tpl = tpl[:a] + '<img data-ascil-photo="bienvenue" ' + tpl[a + 5:]
        k = tpl.rindex('</body>')
        tpl = tpl[:k] + LIVE + tpl[k:]
        save(path, s, i, j, tpl)
    print(f'photos de l’Accueil reliées au panneau sur {len(HOME)} pages')


def panel():
    path = ROOT / 'SA-Panneau.dc.html'
    s, i, j, tpl = load(path)
    tpl = re.sub(r'<style id="sa-photos-css">.*?</style>\s*', '', tpl, flags=re.S)
    tpl = re.sub(r'<script id="sa-photos">.*?</script>\s*', '', tpl, flags=re.S)
    tpl = re.sub(r'<div class="ph-slot" data-slot="\w+".*?role="status"></p></div></div></div>', '', tpl, flags=re.S)
    for k, sec in (('hero', 'w-hero'), ('bienvenue', 'w-bienvenue')):
        a = tpl.index(f'<section id="{sec}"')
        b = tpl.index('</section>', a)
        body = tpl[a:b]
        end = body.rindex('</div>')          # fin de .card-b
        body = body[:end] + slot_html(k, *SLOTS[k]) + body[end:]
        tpl = tpl[:a] + body + tpl[b:]
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + PANEL_CSS + PANEL_JS + tpl[k:]
    assert tpl.count('class="ph-slot"') == 2
    save(path, s, i, j, tpl)
    print('panneau Accueil : bloc Photo ajouté aux cartes Héros et Bienvenue aux visiteurs')


if __name__ == '__main__':
    public()
    panel()
