"""Étape G : page publique « Un site gratuit pour votre mosquée » (/site-gratuit-mosquee) et son lien
discret dans le pied de page de toutes les pages publiques.

- site-gratuit-mosquee.html est construite depuis 404.html (même en-tête, menu, pied de page, liens absolus,
  script des langues) : seul le contenu principal change. Texte en français dans la page ; l'arabe et
  l'anglais viennent du dictionnaire (scripts/i18n/lot-gratuit.tsv). La page n'est pas dans le menu
  principal : on y arrive par le lien du pied de page. Invitation sobre, sans nom mis en avant.
- Lien du pied de page : une petite ligne sous « © … · Espace administration », sur les pages publiques
  (PC, M-, T-, index.html, 404.html) et la nouvelle page.
Ordre : après wire_langues.py (la page reprend la 404 déjà complète), avant fix_inputs.py. Idempotent.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'
SLUG = 'site-gratuit-mosquee'
OUT = ROOT / f'{SLUG}.html'
TITLE = 'Un site gratuit pour votre mosquée'
EMAIL = 'elidryssi@gmail.com'

FOOT = (f'<p class="ascil-gratuit" style="margin:12px 0 0;font-size:14px">'
        f'<a href="/{SLUG}" style="color:#F3EAD8;opacity:.75;text-decoration:underline;text-underline-offset:3px;display:inline-block;padding:4px 0">'
        'Vous êtes une mosquée ou une association ? Un site gratuit pour vous</a></p>')

ITEMS = [
    'Un site complet comme celui-ci (horaires de prière, événements et inscriptions, campagne de dons, ressources, contact)',
    'L’hébergement',
    'Les mises à jour de sécurité',
    'Une aide technique rapide en cas de besoin',
]

MAIN = (
    '<section class="sand" aria-labelledby="sg-t" style="border-bottom:1px solid #E4D9C0">'
    '<div class="wrap" style="padding-top:64px;padding-bottom:56px">'
    f'<h1 id="sg-t" class="h1" style="margin:0;max-width:760px">{TITLE}</h1>'
    '<p class="lead" style="margin-top:20px;max-width:65ch">Vous êtes une mosquée ou une association islamique et vous souhaitez '
    'un site comme celui-ci ? C’est possible, et c’est 100 % gratuit.</p>'
    '</div></section>\n'
    '<section aria-label="' + TITLE + '"><div class="wrap" style="padding-top:48px;padding-bottom:56px;max-width:820px">'
    '<h2 class="h3" style="margin:0">Ce qui est offert :</h2>'
    '<ul style="margin:16px 0 0;padding-inline-start:1.25em;display:grid;gap:10px;line-height:1.6;max-width:65ch">'
    + ''.join(f'<li>{x}</li>' for x in ITEMS) +
    '</ul>'
    '<h2 class="h3" style="margin:40px 0 0">Ce qu’on vous demande :</h2>'
    '<p style="margin:12px 0 0;line-height:1.6">Rien. Vos douas suffisent.</p>'
    f'<p style="margin:40px 0 0;line-height:1.6">Contact : <a href="mailto:{EMAIL}" style="color:#0E4D3C;font-weight:700;'
    f'text-decoration:underline;text-underline-offset:3px;overflow-wrap:anywhere;display:inline-block;padding:4px 0">{EMAIL}</a></p>'
    '</div></section>\n'
)


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def enc(tpl):
    e = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(e) == tpl
    return e


def add_footer_link(tpl, name):
    if f'href="/{SLUG}"' in tpl:
        return tpl
    a = tpl.index('<footer')
    k = tpl.index('Espace administration</a></p>', a) + len('Espace administration</a></p>')
    return tpl[:k] + FOOT + tpl[k:]


def footers():
    n = 0
    pages = [p for p in sorted(ROOT.glob('*.dc.html')) if not p.name.startswith('SA-')] + [ROOT / 'index.html', ROOT / '404.html']
    for path in pages:
        if not path.exists():
            continue
        s, i, j, tpl = load(path)
        if '<footer' not in tpl:
            continue
        new = add_footer_link(tpl, path.name)
        assert new.count(f'href="/{SLUG}"') == 1, path.name
        if new != tpl:
            path.write_text(s[:i] + enc(new) + s[j:], encoding='utf-8')
        n += 1
    print(f'lien « Un site gratuit pour vous » dans le pied de page de {n} pages publiques')


def build_page():
    s, i, j, tpl = load(ROOT / '404.html')
    a = tpl.index('<section class="sand" aria-labelledby="nf-t"')
    b = tpl.index('</section>', a) + len('</section>\n')
    tpl = tpl[:a] + MAIN + tpl[b:]
    tpl = re.sub(r'<script id="ascil-404-load">.*?</script>\s*', '', tpl, flags=re.S)
    tpl = tpl.replace('\n<meta name="robots" content="noindex">', '', 1)
    tpl = tpl.replace('<title>Page introuvable — ASCIL</title>', f'<title>{TITLE} — ASCIL</title>', 1)
    assert 'nf-t' not in tpl and 'noindex' not in tpl and f'<title>{TITLE} — ASCIL</title>' in tpl
    assert tpl.count(f'href="/{SLUG}"') == 1
    out = s[:i] + enc(tpl) + s[j:]
    out = out.replace('Page introuvable — ASCIL', f'{TITLE} — ASCIL')
    OUT.write_text(out, encoding='utf-8')
    print(f'{OUT.name} : page « {TITLE} » construite depuis 404.html')


if __name__ == '__main__':
    footers()
    build_page()
