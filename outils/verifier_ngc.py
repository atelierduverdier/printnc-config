#!/usr/bin/env python3
"""Controle structurel des sous-programmes O-word LinuxCNC.

Il n'y a pas de linter G-code ici. Ce script joue le role de la passe
`ast.parse` : il ne dit pas si le programme est JUSTE, il dit s'il est
BIEN FORME. Ce qu'il verifie :
  - sub/endsub apparies, et le nom du sub = le nom du fichier
  - chaque O<numero> if/while ferme par le meme numero, bien imbrique
  - tout parametre nomme LU quelque part est ECRIT quelque part
  - les appels o<nom> call visent un fichier qui existe
"""
import re
import sys
import os

RE_ONUM = re.compile(r'^\s*[oO](\d+)\s+(if|elseif|else|endif|while|endwhile|do|repeat|endrepeat)\b',
                     re.I)
RE_ONAME = re.compile(r'^\s*[oO]<([^>]+)>\s+(sub|endsub|call|return)\b', re.I)
RE_ECRIT = re.compile(r'#<([^>]+)>\s*=')
RE_LU = re.compile(r'#<([^>]+)>')

OUVRE = {'if': 'endif', 'while': 'endwhile', 'do': 'endwhile',
         'repeat': 'endrepeat'}


def decommenter(ligne):
    """Retire les commentaires ; ... et ( ... ) — sans casser les [ ]."""
    ligne = ligne.split(';', 1)[0]
    return re.sub(r'\([^)]*\)', ' ', ligne)


def verifier(chemin):
    nom_fichier = os.path.splitext(os.path.basename(chemin))[0]
    erreurs, avertis = [], []
    pile, subs, appels = [], [], []
    ecrits, lus = set(), {}
    with open(chemin, encoding='utf-8') as f:
        lignes = f.readlines()

    for n, brute in enumerate(lignes, 1):
        ligne = decommenter(brute)

        m = RE_ONAME.search(ligne)
        if m:
            nom, mot = m.group(1), m.group(2).lower()
            if mot == 'sub':
                subs.append(('sub', nom, n))
                if nom != nom_fichier:
                    erreurs.append("l.%d : sub <%s> dans %s.ngc — LinuxCNC "
                                   "exige le meme nom" % (n, nom, nom_fichier))
            elif mot == 'endsub':
                subs.append(('endsub', nom, n))
            elif mot == 'call':
                appels.append((nom, n))

        m = RE_ONUM.search(ligne)
        if m:
            num, mot = m.group(1), m.group(2).lower()
            if mot in OUVRE:
                pile.append((num, mot, n))
            elif mot in ('elseif', 'else'):
                if not pile or pile[-1][0] != num:
                    erreurs.append("l.%d : O%s %s sans if O%s ouvert"
                                   % (n, num, mot, num))
            elif mot in ('endif', 'endwhile', 'endrepeat'):
                if not pile:
                    erreurs.append("l.%d : O%s %s sans ouverture" % (n, num, mot))
                elif pile[-1][0] != num:
                    erreurs.append("l.%d : O%s %s ferme un O%s ouvert l.%d — "
                                   "imbrication croisee"
                                   % (n, num, mot, pile[-1][0], pile[-1][2]))
                elif OUVRE[pile[-1][1]] != mot:
                    erreurs.append("l.%d : O%s %s ferme un %s" % (n, num, mot, pile[-1][1]))
                    pile.pop()
                else:
                    pile.pop()

        for p in RE_ECRIT.findall(ligne):
            ecrits.add(p.strip())
        for p in RE_LU.findall(ligne):
            lus.setdefault(p.strip(), n)

    for num, mot, n in pile:
        erreurs.append("l.%d : O%s %s jamais ferme" % (n, num, mot))

    # Un fichier SANS sub est legitime : c'est un script MDI, appele par un
    # bouton QtDragon (reset_ref.ngc, set_mode_*.ngc). Seul un sub OUVERT et
    # non ferme est une faute.
    ouverts = [s for s in subs if s[0] == 'sub']
    fermes = [s for s in subs if s[0] == 'endsub']
    if len(ouverts) > 1:
        erreurs.append("%d 'sub' dans un meme fichier" % len(ouverts))
    if ouverts and not fermes:
        erreurs.append("sub <%s> jamais ferme par endsub" % ouverts[0][1])
    if fermes and not ouverts:
        erreurs.append("endsub sans sub")
    if not ouverts:
        avertis.append("aucun sub : lu comme script MDI, pas comme "
                       "sous-programme appelable")

    # parametres systeme et locaux d'appel : jamais ecrits, c'est normal
    systeme = {'_metric', '_imperial', '_absolute', '_incremental', '_x', '_y',
               '_z', '_a', '_b', '_c', '_current_tool', '_selected_tool',
               '_current_pocket', '_selected_pocket', '_spindle_rpm_mode',
               '_spindle_css_mode', '_ijk_absolute_mode', '_lathe_diameter_mode',
               '_lathe_radius_mode', '_coord_system', '_tool_offset',
               '_feed', '_rpm', '_vmajor', '_vminor', '_line', '_motion_mode',
               '_plane', '_call_level', '_remap_level', '_in_feed_override',
               '_task', '_value', '_value_returned'}
    orphelins = {}
    for p, n in sorted(lus.items()):
        if p in ecrits or p in systeme:
            continue
        # Les variables d'INI, #<_ini[SECTION]CLE>, sont posees par
        # LinuxCNC au chargement : elles ne sont ecrites nulle part dans
        # le G-code, et c'est normal. Sans cette exception le controle
        # criait au loup sur la position du palpeur, qui se lit
        # desormais dans [VERSA_TOOLSETTER] au lieu d'etre recopiee.
        #
        # Ce n'est PAS un trou dans le filet : une section ou une cle
        # absente de l'ini fait echouer le chargement du programme, donc
        # bruyamment. C'est le silence qui etait a craindre, et il ne
        # concerne que les parametres ordinaires.
        if p.startswith('_ini['):
            continue
        orphelins[p] = n

    return erreurs, avertis, [a[0] for a in appels], ecrits, orphelins


def main(chemins):
    # TOUS les dossiers recus, pas seulement celui du premier fichier.
    # LinuxCNC resout un o<nom> call en parcourant le SUBROUTINE_PATH, qui
    # en compte plusieurs -- dont banc/, place en tete par l'ini de
    # simulation. Ne regarder que le premier dossier faisait crier ce
    # controle sur un appel parfaitement resolu, des qu'on lancait la
    # verification sur banc/ seul.
    dossiers = []
    for c in chemins:
        d = os.path.dirname(os.path.abspath(c))
        for candidat in (d, os.path.dirname(d)):
            # Le dossier PARENT aussi : banc/ vit sous subroutines/, et
            # l'ini de simulation les enchaine dans cet ordre. Verifier
            # banc/ seul doit donc trouver les sous-programmes du dessus,
            # comme LinuxCNC les trouve.
            if candidat not in dossiers and os.path.isdir(candidat):
                dossiers.append(candidat)
    total = 0
    tous_appels = []
    resultats = {}
    globales = set()          # tout #<_xxx> ecrit dans N'IMPORTE lequel des fichiers
    for c in chemins:
        err, avert, appels, ecrits, orphelins = verifier(c)
        resultats[c] = (err, avert, orphelins)
        tous_appels += [(a, c) for a in appels]
        globales |= {e for e in ecrits if e.startswith('_')}

    # Deuxieme passe : un parametre lu nulle part ecrit est une ERREUR.
    # C'est ce controle-la qui compte — LinuxCNC ne dit rien d'un
    # #<_atc_truc> jamais pose, il le lit a zero et envoie la broche
    # a Z0 sans broncher.
    for c in chemins:
        err, avert, orphelins = resultats[c]
        for p, n in sorted(orphelins.items()):
            if p in globales:
                continue
            err.append("l.%d : #<%s> lu et pose NULLE PART — "
                       "LinuxCNC le lira a 0" % (n, p))
        etat = "OK" if not err else "%d ERREUR(S)" % len(err)
        print("%-24s %s" % (os.path.basename(c), etat))
        for e in err:
            print("   ERREUR  %s" % e)
        for a in avert:
            print("   note    %s" % a)
        total += len(err)

    for nom, depuis in tous_appels:
        trouve = next((os.path.join(d, nom + ".ngc") for d in dossiers
                       if os.path.exists(os.path.join(d, nom + ".ngc"))), None)
        if trouve is None:
            print("   ERREUR  %s appelle o<%s> : %s.ngc introuvable"
                  % (os.path.basename(depuis), nom, nom))
            total += 1
        else:
            ou = os.path.basename(os.path.dirname(trouve))
            print("appel o<%s> depuis %s -> %s.ngc present (%s/)"
                  % (nom, os.path.basename(depuis), nom, ou))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
