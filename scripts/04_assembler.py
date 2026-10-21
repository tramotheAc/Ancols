# -*- coding: utf-8 -*-
"""Etape 4 - assemble la page autonome app-statique/index.html.

Ordre de chargement impose par la charte : jetons, socle, composants, puis
bouton-theme et motif-rail. Le bandeau officiel est injecte dans --fond-rail.
Viennent ensuite les styles propres a la page, le balisage, les donnees
(donnees/analyse.json) et les scripts.

La page produite ne depend de rien : elle s'ouvre par double-clic, avec Live
Server, ou se publie telle quelle.

    python3 scripts/04_assembler.py                 ecrit app-statique/index.html
    python3 scripts/04_assembler.py --fragment f    ecrit aussi un fragment sans <html>/<head>
                                                    (pour un hebergeur qui fournit le squelette)
"""
import io
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RACINE, 'src')
THEME = os.path.join(SRC, 'theme')
ORDRE_CHARTE = ('jetons.css', 'socle.css', 'composants.css', 'bouton-theme.css', 'motif-rail.css', 'bandeau.css')
TITRE = 'Cartographie des trames ANCOLS'


def lit(*chemin):
    return io.open(os.path.join(*chemin), encoding='utf-8').read()


def assemble():
    styles = '\n'.join(lit(THEME, f) for f in ORDRE_CHARTE) + '\n' + lit(SRC, 'page.css')
    donnees = json.load(io.open(os.path.join(RACINE, 'donnees', 'analyse.json'), encoding='utf-8'))
    # « </ » fermerait la balise <script> qui porte les donnees.
    donnees = json.dumps(donnees, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    corps = (lit(SRC, 'page.html')
             + '\n<script id="donnees" type="application/json">' + donnees + '</script>\n'
             + '<script>\n' + lit(THEME, 'bouton-theme.js') + '\n</script>\n'
             + '<script>\n' + lit(SRC, 'page.js') + '\n</script>\n')
    return styles, corps


def main():
    styles, corps = assemble()
    page = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>' + TITRE + '</title>\n<style>\n' + styles + '\n</style>\n</head>\n<body>\n'
            + corps + '</body>\n</html>\n')
    sortie = os.path.join(RACINE, 'app-statique', 'index.html')
    io.open(sortie, 'w', encoding='utf-8').write(page)
    print('ecrit', os.path.relpath(sortie, RACINE), round(len(page.encode('utf-8')) / 1024), 'Ko')
    if '--fragment' in sys.argv:
        cible = sys.argv[sys.argv.index('--fragment') + 1]
        io.open(cible, 'w', encoding='utf-8').write('<title>' + TITRE + '</title>\n<style>\n' + styles + '\n</style>\n' + corps)
        print('ecrit', cible)


if __name__ == '__main__':
    main()
