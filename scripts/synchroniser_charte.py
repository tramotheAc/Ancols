# -*- coding: utf-8 -*-
"""Recopie la charte visuelle dans src/theme/, avec la version d'origine en tete de chaque fichier.

La charte se consomme par un clone local, declare dans le .env du projet :

    CHARTE=C:\\Aiguillon\\charte-visuelle

A defaut, le script cherche ../charte-visuelle a cote du depot.

    python3 scripts/synchroniser_charte.py      copie, puis relancer scripts/04_assembler.py

Avant de pousser, verifier avec les outils de la charte :

    python3 <CHARTE>/outils/couverture.py app-statique/index.html
    python3 <CHARTE>/outils/contraste.py  app-statique/index.html
"""
import io
import os
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIERS = ('jetons.css', 'socle.css', 'composants.css', 'motif-rail.css', 'bouton-theme.css', 'bouton-theme.js')


def chemin_charte():
    if os.environ.get('CHARTE'):
        return os.environ['CHARTE']
    env = os.path.join(RACINE, '.env')
    if os.path.exists(env):
        for ligne in io.open(env, encoding='utf-8'):
            if ligne.strip().startswith('CHARTE='):
                return ligne.split('=', 1)[1].strip().strip('"')
    return os.path.join(os.path.dirname(RACINE), 'charte-visuelle')


def main():
    charte = chemin_charte()
    if not os.path.exists(os.path.join(charte, 'jetons.css')):
        sys.exit('Charte introuvable : ' + charte + '\nDeclarer CHARTE=<chemin du clone> dans .env')
    try:
        version = subprocess.check_output(['git', '-C', charte, 'rev-parse', '--short', 'HEAD'], text=True).strip()
    except Exception:
        version = 'version inconnue'
    cible = os.path.join(RACINE, 'src', 'theme')
    os.makedirs(cible, exist_ok=True)
    for nom in FICHIERS:
        contenu = io.open(os.path.join(charte, nom), encoding='utf-8').read()
        entete = '/* Copie de tramotheAc/charte-visuelle@%s — %s. Ne pas modifier ici : mettre à jour avec scripts/synchroniser_charte.py. */\n' % (version, nom)
        io.open(os.path.join(cible, nom), 'w', encoding='utf-8').write(entete + contenu)
        print('copie', nom)
    bandeau = io.open(os.path.join(charte, 'bandeau-gauche-bleu.png.base64'), encoding='utf-8').read().replace('\n', '').strip()
    io.open(os.path.join(cible, 'bandeau.css'), 'w', encoding='utf-8').write(
        '/* Bandeau officiel (charte-visuelle/bandeau-gauche-bleu.png.base64, @%s), injecté dans --fond-rail. */\n'
        ':root { --fond-rail: url("data:image/png;base64,%s"); }\n' % (version, bandeau))
    print('copie bandeau.css  (charte @%s)' % version)


if __name__ == '__main__':
    main()
