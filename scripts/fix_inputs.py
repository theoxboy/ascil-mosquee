"""Libère les champs de saisie figés par la maquette.

Les pages bundlées sont rendues par React. Un <input value="…"> écrit en dur devient un champ
« contrôlé » sans gestionnaire : React lui remet sa valeur après chaque frappe ou chaque choix
(on ne peut ni écrire, ni choisir une date). Idem pour une case <input checked>.

Ce script remplace, dans toutes les pages bundlées :
  value="…"   -> sc-camel-default-value="…"   (React : defaultValue, valeur de départ libre)
  checked     -> sc-camel-default-checked="true"
Les valeurs liées à l'état ({{ … }}) et les boutons, cases cachées, etc. ne sont pas touchés,
ni le contenu des balises <script>.

Dernière étape obligatoire après install_superadmin.py et les scripts wire_*.py
(qui s'appuient sur les attributs value d'origine). Idempotent.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'
TEXT_SKIP = {'checkbox', 'radio', 'hidden', 'submit', 'button', 'reset', 'image'}


def fix_tag(tag):
    m = re.search(r'\btype="([^"]*)"', tag)
    kind = m.group(1).lower() if m else 'text'
    if kind in ('checkbox', 'radio'):
        # checked seul, ou checked="" / checked="checked", sans liaison {{ }}
        return re.sub(r'(\s)checked(?:="(?:checked)?")?(?=[\s>/])', r'\1sc-camel-default-checked="true"', tag)
    if kind in TEXT_SKIP:
        return tag
    return re.sub(r'(\s)value="((?:(?!\{\{)[^"])*)"', r'\1sc-camel-default-value="\2"', tag)


# Le contenu des <script> n'est jamais touché : les panneaux y construisent des champs en HTML
# (innerHTML), où seul value="…" donne une valeur de départ (sc-camel-default-value y serait ignoré).
def fix_outside_scripts(tpl):
    parts = re.split(r'(<script\b[^>]*>.*?</script>)', tpl, flags=re.S)
    return ''.join(p if k % 2 else re.sub(r'<input\b[^>]*>', lambda m: fix_tag(m.group(0)), p)
                   for k, p in enumerate(parts))


def main():
    changed = 0
    for path in sorted(ROOT.glob('*.html')):
        s = path.read_text(encoding='utf-8')
        if OPEN not in s:
            continue
        i = s.index(OPEN) + len(OPEN)
        j = s.index('</script>', i)
        tpl = json.loads(s[i:j])
        if '<x-dc' not in tpl:
            continue
        new = fix_outside_scripts(tpl)
        if new == tpl:
            continue
        enc = json.dumps(new).replace('</', '<\\u002F')
        assert json.loads(enc) == new
        path.write_text(s[:i] + enc + s[j:], encoding='utf-8')
        changed += 1
    print('pages aux champs libérés :', changed)


if __name__ == '__main__':
    main()
