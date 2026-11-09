"""Nettoyage des dernières mentions de brouillon (tous les services et outils du site sont confirmés).

Pages publiques (PC, M-, T-, index.html, 404.html) :
  - bouton « Revenir en haut de la page » : lien « #top » (haut de la page) au lieu de « # » ;
  - lieu de l'Aïd laissé vide : « Lieu communiqué prochainement » ;
  - Ressources, restaurants : « à vérifier auprès du restaurant » pour la certification halal non indiquée ;
  - menu mobile : ouvert sur l'écran visible (plus en haut de la page), page derrière immobile.
Panneau :
  - SA-Services : description de la rubrique sans « à confirmer ».
Les scripts d'origine (wire_prieres.py, wire_ressources.py, wire_horaires.py, wire_pages.py, wire_site.py)
écrivent déjà ces nouveaux textes ; ce script met à jour les pages déjà générées.
Ordre : après wire_pied.py, avant fix_inputs.py. Idempotent.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'

PUBLIC = [
    ('<div class="totop"><a href="#" aria-label="Revenir en haut de la page">',
     '<div class="totop"><a href="#top" aria-label="Revenir en haut de la page">'),
    ("|| 'Lieu à confirmer')", "|| 'Lieu communiqué prochainement')"),
    ("confirmer: 'Certification halal : à confirmer auprès du restaurant'",
     "confirmer: 'Certification halal : à vérifier auprès du restaurant'"),
    # Menu mobile (trois lignes) : il s'ouvre sur l'écran visible, là où l'on se trouve dans la page,
    # au lieu du haut de la page ; il défile lui-même s'il est plus long que l'écran, et la page
    # derrière ne bouge pas tant qu'il est ouvert (à la fermeture, on reste au même endroit).
    ('<div class="menu-in" role="dialog" aria-label="Menu" style="position:absolute;inset:0;z-index:60;background:#FFFEF9;display:flex;flex-direction:column">',
     '<div class="menu-in" role="dialog" aria-label="Menu" style="position:fixed;inset:0;z-index:60;background:#FFFEF9;display:flex;flex-direction:column;overflow-y:auto;overscroll-behavior:contain">'),
    ('.menu-in{animation:menuin .35s cubic-bezier(.2,.8,.2,1) both}\n.menu-in nav a{',
     '.menu-in{animation:menuin .35s cubic-bezier(.2,.8,.2,1) both}\nhtml:has(.menu-in){overflow:hidden}\n.menu-in nav a{'),
]
PANEL = {
    'SA-Services.dc.html': [
        ('La liste des services, puis chaque service à confirmer (cours, mariages, funérailles, aide alimentaire, espace femmes).',
         'La liste des services, puis chaque service (cours, mariages, funérailles, aide alimentaire, espace femmes).'),
    ],
}


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def save(path, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def main():
    n = 0
    pages = [p for p in sorted(ROOT.glob('*.dc.html')) if not p.name.startswith('SA-')] + [ROOT / 'index.html', ROOT / '404.html']
    for path in pages:
        if not path.exists():
            continue
        s, i, j, tpl = load(path)
        new = tpl
        for a, b in PUBLIC:
            new = new.replace(a, b)
        assert 'Lieu à confirmer' not in new and 'à confirmer auprès' not in new, path.name
        assert 'class="totop"><a href="#"' not in new, path.name
        assert 'aria-label="Menu" style="position:absolute' not in new, path.name
        if new != tpl:
            save(path, s, i, j, new)
            n += 1
    for name, pairs in PANEL.items():
        path = ROOT / name
        s, i, j, tpl = load(path)
        new = tpl
        for a, b in pairs:
            new = new.replace(a, b)
        assert 'à confirmer' not in new, name
        if new != tpl:
            save(path, s, i, j, new)
    print(f'nettoyage des mentions de brouillon : {n} pages publiques mises à jour, panneau Services corrigé')


if __name__ == '__main__':
    main()
