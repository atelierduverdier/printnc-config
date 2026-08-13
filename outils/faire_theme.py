#!/usr/bin/env python3
# =========================================================================
# faire_theme.py — le thème « Atelier du Verdier » pour qtdragon_hd
# =========================================================================
# Le thème n'est PAS écrit à la main : il est DÉRIVÉ de `dark.qss`, celui que
# livre LinuxCNC. Raison unique : ce fichier couvre 72 sélecteurs, et un thème
# qui en oublie un laisse le widget correspondant en style Qt par défaut — une
# plage gris clair au milieu d'une interface sombre. Repartir du fichier amont
# garantit la couverture par construction ; seule la palette change.
#
# Conséquence à connaître : quand LinuxCNC enrichira `dark.qss`, relancer ce
# script fera suivre le thème. Un thème recopié, lui, se figerait.
#
# TROIS PIÈGES, TOUS RELEVÉS DANS LE FICHIER, AUCUN DEVINÉ
#
# 1. LE VERT A DEUX SENS.
#    « État machine » — `action_estop` au repos, `action_machine_on` allumée :
#    un couple rouge/vert de sécurité, lu d'un coup d'œil à trois mètres. Il ne
#    se repeint pas ; un arrêt d'urgence orange au milieu d'une interface
#    orange ne se voit plus. Ces blocs sortent INTACTS (voir EXCEPTIONS).
#    « Accent d'interaction » — survol, bouton enfoncé, onglet actif, ligne
#    sélectionnée : celui-là devient l'orange de l'atelier.
#
# 2. dark.qss N'EST SOMBRE QU'À MOITIÉ. Les onglets, les menus, les en-têtes
#    de tableau et l'éditeur de G-code sont restés CLAIRS — menus en #ABABAB,
#    onglets en dégradé #D3D3D3→#E1E1E1, zone de texte en rgb(250,250,250).
#    Or CINQ de ces règles posent un fond clair SANS fixer la couleur du
#    texte : elles comptent sur le noir par défaut de Qt. Assombrir le fond
#    sans rien d'autre donnerait du noir sur ardoise — l'éditeur de G-code
#    illisible. D'où les `color:` injectés par ENCRE_FORCEE.
#
# 3. UNE MÊME COULEUR SERT À DEUX CHOSES OPPOSÉES. `#fff` est le rail VIDE
#    d'une glissière (qui doit devenir sombre) ET sa poignée (qui doit rester
#    claire, sinon elle disparaît). Une table globale ne peut pas trancher :
#    d'où PARTICULIERS, appliqué avant elle, règle par règle.
#
# UTILISATION :
#   python3 outils/faire_theme.py
#
# Écrit qtvcp/screens/qtdragon_hd/verdier.qss. Pour l'employer, choisir
# « verdier » dans le sélecteur de thème de qtdragon (onglet Settings).
# =========================================================================

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = Path('/usr/share/qtvcp/screens/qtdragon_hd/dark.qss')
SORTIE = RACINE / 'qtvcp' / 'screens' / 'qtdragon_hd' / 'verdier.qss'

# Les jetons de la charte, version sombre — les mêmes que `kit/verdier-jetons.css`
# du dépôt `site`. Une interface d'atelier se regarde sous une lampe et à côté
# d'une machine : c'est la version sombre qui s'impose, pas la claire.
ORANGE     = '#ff9a1f'   # --orange
ORANGE_CLR = '#ffab45'   # --orange-d, pour les dégradés et le survol
FOND       = '#14171b'   # --bg
FOND_2     = '#1a1e23'   # --bg-2
FOND_3     = '#22272e'   # --bg-3
ENCRE      = '#e6e9ee'   # --fg
ENCRE_2    = '#a8b0bc'   # --fg-2
ENCRE_3    = '#7c8592'   # --fg-3
TRAIT      = '#2a3038'   # --line
TRAIT_2    = '#353c46'   # --line-2
RELIEF     = '#39414d'   # haut des dégradés de bouton
ROUGE      = '#ff4040'   # le rouge d'origine, remonté pour rester lisible
# L'encre posée SUR de l'orange. Ce n'est pas un choix refait ici : c'est la
# règle `.btn-primary{background:var(--orange); color:#20160a}` de verdier.css.
SUR_ORANGE = '#20160a'

# Les couleurs de la coloration syntaxique ne sont pas inventées ici : ce sont
# celles que le visualiseur G-code emploie déjà pour le MÊME G-code
# (`interface/theme.py`, palette SOMBRE). Même langage de couleur du
# visualiseur à la machine : le cyan est le travail, le jaune le palpage.
MOUVEMENT  = '#5cc7fa'   # vgcode « travail »
AUXILIAIRE = '#ffd94d'   # vgcode « palpage »

# Polices. « Lato Heavy », demandée SEIZE fois par dark.qss, N'EST PAS
# installée — ni ici, ni dans les dépôts Arch : les seize déclarations
# retombent en silence sur Noto Sans. La charte du site ne livre d'ailleurs
# aucune police, elle s'appuie sur la pile système ; on fait pareil, avec des
# familles présentes sur Arch comme sur le Raspberry Pi de l'atelier.
POLICE_UI = 'Noto Sans'
# Pour l'éditeur, une CHASSE FIXE — écart assumé avec l'amont, qui a choisi une
# proportionnelle. Des colonnes de coordonnées ne s'alignent qu'en chasse fixe.
POLICE_CODE = 'DejaVu Sans Mono'

# --- 1. Les blocs épargnés ------------------------------------------------
# Le vert et le rouge y sont un ÉTAT MACHINE, pas un ornement. Si dark.qss en
# ajoute un, il faudra l'inscrire ici ; le contrôle de fin ne le dira pas —
# lui ne voit que les couleurs, pas leur sens.
EXCEPTIONS = (
    'action_machine_on',
    'action_estop',
)

# --- 2. Le texte qu'il faut rendre lisible --------------------------------
# Ces règles posent un fond sans dire la couleur du texte. Sélecteur exact
# (après normalisation des espaces) -> couleur à injecter.
ENCRE_FORCEE = {
    'QTextEdit':      ENCRE,       # l'éditeur de G-code, le plus important
    'QProgressBar':   SUR_ORANGE,  # voir RAIL_CLAIR ci-dessous
    'QHeaderView':    ENCRE,
    'QMenu':          ENCRE,
    'QTabBar::tab':   ENCRE_2,     # onglets au repos ; l'actif a déjà sa couleur
}

# --- 2 bis. La barre d'avancement garde un rail CLAIR ---------------------
# Relevé sur les SIX thèmes livrés : tous gardent `rgb(250,250,250)` ou
# `#a0a0a0` comme fond de QProgressBar, même les sombres. Ce n'est pas un
# oubli, c'est leur raisonnement : Qt dessine le texte d'UNE seule couleur,
# par-dessus la partie remplie ET la partie vide. Avec un rail sombre et un
# remplissage orange, aucune encre ne se lit des deux côtés — clair sur
# orange donne 1,9:1, sombre sur ardoise 1,3:1. Un rail clair rend les deux
# lisibles avec la même encre.
# `spindle_power` écrit « POWER %p% » sur toute la largeur : le cas se
# présente vraiment, ce n'est pas une hypothèse.
RAIL_CLAIR = ENCRE_2

# --- 3. Les couleurs à sens variable --------------------------------------
# (fragment du sélecteur, couleur d'origine, remplaçant). Appliqué AVANT la
# table globale, sinon celle-ci mangerait la couleur.
#   rempli   -> orange     vide -> fond sombre
#   poignée  -> claire     désactivé -> gris moyen
PARTICULIERS = [
    ('QProgressBar',                      'rgb(250, 250, 250)', RAIL_CLAIR),
    ('QSlider::groove',                   'white', FOND_3),   # le rail
    ('QSlider::add-page:horizontal',      '#fff',  FOND_3),   # partie vide
    ('QSlider::sub-page:vertical',        'white', FOND_3),   # partie vide
    ('QSlider::add-page:horizontal:disabled', '#eee', FOND_3),
    ('QSlider::sub-page:horizontal:disabled', '#bbb', ENCRE_3),
    ('QSlider::handle:horizontal:disabled',   '#eee', ENCRE_3),
]

# --- 4. La table globale --------------------------------------------------
# L'ordre compte : les formes longues d'abord, sinon « #eee » mangerait le
# début de « #eeeeee », et « #fff » celui de « #fff3e2 ».
PALETTE = [
    ('rgba(120, 140, 180, 255)', RELIEF),
    ('rgba(11, 22, 33, 255)',    FOND),
    ('rgb(250, 250, 250)',       FOND_2),   # fonds clairs a moitie convertis
    ('rgb(250,250,250)',         FOND_2),   # ... ecrit des deux facons
    ('#fafafa',                  FOND_3),
    ('#ABABAB',                  FOND_2),   # fond des menus
    ('#B0B0D0',                  FOND_3),   # en-tete de tableau
    ('#D3D3D3',                  FOND_2),   # onglet au repos, degrade
    ('#D8D8D8',                  FOND_2),
    ('#DDDDDD',                  FOND_3),
    ('#E1E1E1',                  FOND_3),
    ('#e7e7e7',                  RELIEF),   # onglet actif, degrade
    ('#f4f4f4',                  FOND_3),
    ('#404040',                  FOND),
    ('#505050',                  FOND_3),
    ('#303030',                  FOND_3),
    ('#6c6c6c',                  TRAIT),
    ('#32414B',                  TRAIT),
    ('#606060',                  FOND_2),
    ('#FFFFD0',                  ENCRE),
    ('#00FF00',                  ORANGE),
    ('#00ff00',                  ORANGE),
    ('#FF0000',                  ROUGE),
    ('#ff0000',                  ROUGE),
    ('#bbf',                     ORANGE_CLR),
    ('#66e',                     ORANGE),
    ('#55f',                     ORANGE),
    ('#eee',                     ENCRE),    # poignees de glissiere : claires
    ('#ddd',                     ENCRE_2),
    ('#ccc',                     ENCRE_2),
    ('#bbb',                     ENCRE_3),
    ('#aaa',                     TRAIT_2),
    ('#999',                     ENCRE_3),
    ('#444',                     TRAIT_2),
    ('#fff',                     ENCRE),
    ('white',                    ENCRE),
    ('black',                    TRAIT),    # 13 bordures noires, invisibles
]

# --- 5. Ce que dark.qss ne couvre PAS -------------------------------------
# Deux widgets restent au style Qt par défaut — deux plages claires au milieu
# de l'ardoise. Ce n'est pas une supposition : `EditorBase` n'est habillé que
# par `dark_grey.qss` et `QPlainTextEdit` que par `argentium.qss`, sur les six
# thèmes livrés.
#
# `EditorBase` est le visualiseur de G-code, celui qu'on regarde le plus. Ses
# couleurs ne passent PAS par les règles ordinaires : QsciScintilla les prend
# par des propriétés Qt, atteignables depuis une feuille de style avec le
# préfixe `qproperty-`. La liste des noms vient de `gcode_editor.py`.
SUPPLEMENT = f"""

/* ================================================================
   AJOUTÉ PAR faire_theme.py — absent de dark.qss
   ================================================================ */

/** Le visualiseur de G-code. QsciScintilla ignore les regles QSS
    ordinaires : tout passe par des proprietes Qt. **/
EditorBase {{
    /* Le cadre du QAbstractScrollArea, distinct du fond du texte : sans
       cette ligne il reste en gris clair tout autour de l'editeur. */
    border: 1px solid {TRAIT};
    border-radius: 4px;
    qproperty-styleColorBackground: {FOND};
    qproperty-styleColorMarginBackground: {FOND_2};
    qproperty-styleColorMarginText: {ENCRE_3};        /* numeros de ligne */
    qproperty-styleColorMarkerBackground: {FOND_3};   /* ligne courante */
    qproperty-styleColorSelectionBackground: {ORANGE};
    qproperty-styleColorSelectionText: {SUR_ORANGE};
    qproperty-styleFont: "{POLICE_CODE}, 11";
    qproperty-styleFont1: "{POLICE_CODE}, 10";        /* commentaires */
    qproperty-styleFontMargin: "{POLICE_CODE}, 9";
    qproperty-styleColor0: {ENCRE};                   /* ordinaire */
    qproperty-styleColor1: {ENCRE_3};                 /* commentaires */
    qproperty-styleColor2: {MOUVEMENT};               /* codes G */
    qproperty-styleColor3: {AUXILIAIRE};              /* codes M */
    qproperty-styleColor4: {ENCRE_2};                 /* lettres d'axe */
    qproperty-styleColor5: {ENCRE_2};                 /* avance, broche... */
    qproperty-styleColor6: {ENCRE};                   /* valeurs d'axe */
    qproperty-styleColor7: {ENCRE};                   /* autres valeurs */
}}

/** `gcode_description` : une plage blanche sans cette regle. **/
QPlainTextEdit {{
    background: {FOND_2};
    color: {ENCRE};
    border: 1px solid {TRAIT};
    border-radius: 4px;
}}

/** `gcode_list` : blanche elle aussi, sans cette regle. **/
QListWidget {{
    background: {FOND_2};
    color: {ENCRE};
    border: 1px solid {TRAIT};
    border-radius: 4px;
    outline: none;
}}

QListWidget::item:selected {{
    background: {ORANGE};
    color: {SUR_ORANGE};
}}

/** Les infobulles : QUATRE-VINGT-DIX-NEUF widgets en portent une, et sans
    regle elles sortent en jaune pale sur toute l'interface. **/
QToolTip {{
    background: {FOND_3};
    color: {ENCRE};
    border: 1px solid {TRAIT_2};
    border-radius: 4px;
    padding: 4px 7px;
}}

/** Barres de defilement. dark.qss n'en a AUCUNE : celle du visualiseur de
    G-code ressort en gris clair au milieu de l'ardoise. **/
QScrollBar:vertical {{
    background: {FOND_2};
    width: 14px;
    margin: 0;
    border: none;
}}

QScrollBar:horizontal {{
    background: {FOND_2};
    height: 14px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {{
    background: {TRAIT_2};
    border-radius: 5px;
    min-height: 28px;
    min-width: 28px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {{
    background: {ORANGE};
}}

/* Les fleches d'extremite : on les efface plutot que de les peindre. Sans
   ces quatre regles Qt dessine ses fleches par defaut, en gris clair. */
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0; width: 0; border: none; background: none;
}}

QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
}}
"""

REGLE = re.compile(r'([^{}]+)\{([^}]*)\}')

# « 9 pt » avec une espace, ligne 205 de dark.qss, est une syntaxe INVALIDE que
# Qt ignore sans rien dire. Le motif l'absorbe au passage.
POLICE_LOURDE = re.compile(r'font:\s*(\d+)\s*pt\s*"Lato Heavy"')
POLICE_SIMPLE = re.compile(r'font:\s*(\d+)\s*pt\s*"Lato"')


def traduire(corps: str) -> str:
    for avant, apres in PALETTE:
        corps = corps.replace(avant, apres)
    return corps


def main() -> int:
    if not SOURCE.is_file():
        sys.exit(f"faire_theme : {SOURCE} introuvable — le paquet linuxcnc "
                 "est-il installé ?")

    texte = SOURCE.read_text(encoding='utf-8')
    compte = {'epargne': 0, 'particulier': 0, 'encre': 0}

    def refaire(m):
        entete, corps = m.group(1), m.group(2)
        # Le sélecteur nu : sans les commentaires qui le précèdent.
        sel = ' '.join(re.sub(r'/\*.*?\*/', '', entete, flags=re.S).split())

        if any(e in sel for e in EXCEPTIONS):
            compte['epargne'] += 1
            return m.group(0)

        for fragment, avant, apres in PARTICULIERS:
            if fragment in sel and avant in corps:
                corps = corps.replace(avant, apres)
                compte['particulier'] += 1

        corps = traduire(corps)

        for cible, couleur in ENCRE_FORCEE.items():
            if sel == cible and not re.search(r'(?<!-)\bcolor\s*:', corps):
                # Injecté à la fin du bloc, en gardant l'indentation d'à côté.
                marge = re.search(r'\n(\s*)\S', corps)
                corps = corps.rstrip().rstrip(';') + ';\n' \
                    + (marge.group(1) if marge else '    ') \
                    + f'color: {couleur};\n'
                compte['encre'] += 1

        return entete + '{' + corps + '}'

    resultat = REGLE.sub(refaire, texte)

    # « Lato Heavy » n'existe sur aucune des deux machines : on nomme ce qui
    # est réellement là, et le gras remplace le poids « Heavy ».
    resultat, polices = POLICE_LOURDE.subn(
        rf'font: bold \1pt "{POLICE_UI}"', resultat)
    resultat, simples = POLICE_SIMPLE.subn(
        rf'font: \1pt "{POLICE_UI}"', resultat)
    polices += simples

    resultat += SUPPLEMENT

    entete = (
        "/* Thème « Atelier du Verdier » pour qtdragon_hd.\n"
        "   ENGENDRÉ par outils/faire_theme.py depuis le dark.qss de LinuxCNC.\n"
        "   Ne pas éditer ici : corriger la palette du script et relancer.\n"
        f"   Orange {ORANGE} sur ardoise {FOND} — la charte du site.\n"
        "   Le couple rouge/vert de l'arrêt d'urgence et de la mise sous\n"
        "   tension est LAISSÉ INTACT : c'est un état machine, pas un\n"
        "   ornement. */\n\n"
    )
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(entete + resultat, encoding='utf-8')

    # --- Contrôles --------------------------------------------------------
    # Une couleur d'origine oubliée se voit à l'écran, mais pas dans un diff.
    restes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,6}|rgba?\([0-9, ]+\)',
                                   resultat)))
    connues = {c.lower() for c in (ORANGE, ORANGE_CLR, FOND, FOND_2, FOND_3,
                                   ENCRE, ENCRE_2, ENCRE_3, TRAIT, TRAIT_2,
                                   RELIEF, ROUGE, SUR_ORANGE,
                                   MOUVEMENT, AUXILIAIRE,
                                   '#00FF00', '#FF0000')}
    etrangeres = [c for c in restes if c.lower() not in connues]

    # Le nombre de règles doit se retrouver : une accolade avalée par le
    # découpage ne se verrait pas autrement.
    ajoutees = len(REGLE.findall(SUPPLEMENT))
    avant = len(REGLE.findall(texte))
    apres = len(REGLE.findall(resultat))

    print(f"  {SORTIE.relative_to(RACINE)}")
    print(f"  {avant} regles reprises, {ajoutees} ajoutees, "
          f"{compte['epargne']} epargnees")
    print(f"  {compte['particulier']} corrections particulieres, "
          f"{compte['encre']} couleurs de texte, {polices} polices nommees")

    faute = 0
    if apres != avant + ajoutees:
        print(f"  ECHEC : {avant}+{ajoutees} regles attendues, {apres} en sortie")
        faute = 1
    if re.search(r'Lato', resultat):
        print("  ECHEC : « Lato » subsiste, or la police n'est pas installee")
        faute = 1
    if etrangeres:
        print(f"  ECHEC : couleurs non traduites : {', '.join(etrangeres)}")
        faute = 1
    if not faute:
        print("  toutes les couleurs sont passees a la charte")
    return faute


sys.exit(main())
