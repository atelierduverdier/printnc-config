#!/usr/bin/env python3
# =========================================================================
# apercu_theme.py — voir un thème qtvcp sans lancer LinuxCNC
# =========================================================================
# Monte un panneau d'essai avec tous les types de widgets que la feuille de
# style habille, l'applique, et rend l'image hors écran.
#
# POURQUOI CE SCRIPT EXISTE : Qt n'annonce PAS les erreurs de syntaxe d'une
# feuille QSS. Une accolade en trop et tout ce qui suit est ignoré — sans un
# mot, sans exception, sans journal. Le seul verdict fiable est de REGARDER
# LES PIXELS. D'où le contrôle de fin : si le fond n'est pas celui de la
# charte, la feuille n'a pas pris, et le script sort avec 1.
#
# C'est aussi la boucle de travail : changer la palette, relancer, regarder,
# sans jamais démarrer la machine.
#
# UTILISATION :
#   python3 outils/apercu_theme.py [verdier]
#
# Écrit /tmp/apercu-<thème>.png
# =========================================================================

import os
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5 import QtCore, QtGui, QtWidgets   # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
ECRANS = RACINE / 'qtvcp' / 'screens' / 'qtdragon_hd'
SYSTEME = Path('/usr/share/qtvcp/screens/qtdragon_hd')

# Le fond attendu si la feuille a bien pris. Lu dans le fichier plutôt que
# recopié : une valeur écrite deux fois finit par diverger.
import re                                     # noqa: E402


def fond_attendu(qss: str):
    m = re.search(r'QMainWindow\s*\{[^}]*background:\s*(#[0-9a-fA-F]{6})', qss)
    return m.group(1) if m else None


# Un extrait qui met en jeu chaque famille de la coloration : codes G, codes M,
# lettres d'axe, valeurs, commentaire.
EXEMPLE = """(rosace — passe de finition)
G21 G90 G54
G0 Z25.000
G0 X10.000 Y10.000
M3 S18000
G1 Z-2.000 F300
G1 X90.000 F1200
G2 X100.000 Y20.000 I0.000 J10.000
G0 Z25.000
M5
M2
"""


def panneau():
    """Un échantillon de chaque famille de widgets habillée par le thème."""
    f = QtWidgets.QWidget()
    f.setObjectName('apercu')
    grille = QtWidgets.QVBoxLayout(f)

    # --- boutons : au repos, enfoncé, désactivé
    rang = QtWidgets.QHBoxLayout()
    for texte, etat in (('Cycle Start', None), ('Mode Piece', 'checked'),
                        ('Touch Off', None), ('Indisponible', 'disabled')):
        b = QtWidgets.QPushButton(texte)
        if etat == 'checked':
            b.setCheckable(True)
            b.setChecked(True)
        elif etat == 'disabled':
            b.setEnabled(False)
        b.setMinimumHeight(44)
        rang.addWidget(b)
    grille.addLayout(rang)

    # --- le DRO : c'est ce qu'on lit le plus, de loin
    dro = QtWidgets.QHBoxLayout()
    for axe, val in (('X', '  123.456'), ('Y', ' -45.000'), ('Z', '   8.250')):
        e = QtWidgets.QLabel(f'{axe} {val}')
        e.setObjectName(f'label_axis_{axe.lower()}')
        e.setFont(QtGui.QFont('monospace', 22, QtGui.QFont.Bold))
        dro.addWidget(e)
    grille.addLayout(dro)

    # --- onglets, avec le vrai visualiseur de G-code dedans
    onglets = QtWidgets.QTabWidget()

    # Le VRAI widget, pas une imitation : c'est le seul moyen d'éprouver le
    # bloc `qproperty-`, que QsciScintilla lit autrement que les autres
    # règles. Il s'instancie sans LinuxCNC, mais s'il venait à ne plus le
    # faire, l'aperçu doit continuer de servir pour tout le reste.
    # qtvcp ouvre un journal `~/default.log` dès l'import, faute de CONFIG_DIR.
    # Un outil d'aperçu n'a pas à laisser de trace dans le dossier personnel :
    # on ne l'efface que si c'est nous qui venons de le créer.
    journal = Path.home() / 'default.log'
    prealable = journal.exists()

    try:
        from qtvcp.widgets.gcode_editor import EditorBase
        editeur = EditorBase()
        editeur.setText(EXEMPLE)
        onglets.addTab(editeur, 'G-code')
    except Exception as e:                       # noqa: BLE001
        print(f"  (avertissement : EditorBase indisponible — {type(e).__name__}"
              " ; le bloc de l'editeur n'est PAS verifie par cet apercu)")

    if not prealable and journal.exists():
        journal.unlink()

    texte = QtWidgets.QTextEdit()
    texte.setPlainText("Fichier : rosace.ngc\nLignes : 2 103\n"
                       "Etendue X : 0.000 a 240.000\nOutil : 2 (3.175 mm)")
    onglets.addTab(texte, 'Proprietes')
    tableau = QtWidgets.QTableWidget(3, 3)
    tableau.setHorizontalHeaderLabels(['Outil', 'Diam.', 'Longueur'])
    for i, ligne in enumerate((('1', '6.000', '52.310'),
                               ('2', '3.175', '48.900'),
                               ('3', '12.000', '61.045'))):
        for j, v in enumerate(ligne):
            tableau.setItem(i, j, QtWidgets.QTableWidgetItem(v))
    onglets.addTab(tableau, 'Outils')
    onglets.addTab(QtWidgets.QWidget(), 'Reglages')
    grille.addWidget(onglets)

    # --- glissières et barre d'avancement : rempli contre vide
    bas = QtWidgets.QHBoxLayout()
    for orient, val in ((QtCore.Qt.Horizontal, 70), (QtCore.Qt.Horizontal, 30)):
        g = QtWidgets.QSlider(orient)
        g.setValue(val)
        g.setMinimumWidth(160)
        bas.addWidget(g)
    barre = QtWidgets.QProgressBar()
    barre.setValue(62)
    bas.addWidget(barre)
    combo = QtWidgets.QComboBox()
    combo.addItems(['G54', 'G55', 'G56'])
    bas.addWidget(combo)
    case = QtWidgets.QCheckBox('Optional stop')
    case.setChecked(True)
    bas.addWidget(case)
    grille.addLayout(bas)

    gv = QtWidgets.QSlider(QtCore.Qt.Vertical)
    gv.setValue(45)
    gv.setMinimumHeight(90)
    grille.addWidget(gv, alignment=QtCore.Qt.AlignHCenter)

    return f


def main() -> int:
    nom = sys.argv[1] if len(sys.argv) > 1 else 'verdier'
    chemin = ECRANS / f'{nom}.qss'
    if not chemin.is_file():
        chemin = SYSTEME / f'{nom}.qss'
    if not chemin.is_file():
        sys.exit(f"apercu_theme : ni {ECRANS}/{nom}.qss ni {SYSTEME}/{nom}.qss")

    qss = chemin.read_text(encoding='utf-8')
    # qtvcp fait ce remplacement au chargement ; sans lui les cases à cocher
    # perdent leur image et l'aperçu mentirait sur ce point.
    qss = qss.replace('url(:/newPrefix/images', f'url({SYSTEME}/images')

    app = QtWidgets.QApplication(sys.argv)

    # Les `url(:/buttons/...)` de la feuille ne sont PAS des fichiers : ce sont
    # des ressources Qt compilées, que seul l'import de `resources.py`
    # enregistre. Sans lui, les cases à cocher sortent vides et l'aperçu
    # accuserait le thème d'un défaut qui n'est pas le sien. Ce module vit
    # dans le dossier de surcharge, pas dans /usr/share.
    sys.path.insert(0, str(ECRANS))
    try:
        import resources                      # noqa: F401
    except ImportError:
        print(f"  (avertissement : {ECRANS}/resources.py absent — "
              "les cases a cocher seront vides dans l'apercu SEULEMENT)")

    fenetre = QtWidgets.QMainWindow()
    fenetre.setCentralWidget(panneau())
    fenetre.statusBar().showMessage('  Machine prete — F1 pour l\'arret d\'urgence')
    fenetre.resize(900, 560)
    fenetre.setStyleSheet(qss)
    fenetre.show()
    app.processEvents()

    image = fenetre.grab().toImage()
    sortie = Path(f'/tmp/apercu-{nom}.png')
    image.save(str(sortie))

    # --- Le verdict : les pixels, pas l'absence d'exception ---------------
    attendu = fond_attendu(qss)
    coin = QtGui.QColor(image.pixel(4, 4)).name()
    compte = {}
    for y in range(0, image.height(), 3):
        for x in range(0, image.width(), 3):
            c = QtGui.QColor(image.pixel(x, y)).name()
            compte[c] = compte.get(c, 0) + 1
    total = sum(compte.values())

    print(f"  {sortie}  ({image.width()}x{image.height()})")
    print("  couleurs dominantes :")
    for c, n in sorted(compte.items(), key=lambda kv: -kv[1])[:8]:
        print(f"      {c}  {100 * n / total:5.1f} %")

    if attendu is None:
        print("  (pas de QMainWindow dans la feuille, controle du fond impossible)")
        return 0
    if coin.lower() != attendu.lower():
        print(f"  ECHEC : fond {coin}, attendu {attendu} — "
              "la feuille n'a pas ete appliquee (syntaxe ?)")
        return 1
    print(f"  fond {coin} conforme : la feuille est bien appliquee")

    return plages_claires_etrangeres(qss, compte, total)


def plages_claires_etrangeres(qss, compte, total):
    """Les plages claires que la feuille n'a PAS demandées.

    Le défaut typique d'un thème sombre n'est pas une faute de syntaxe, c'est
    un widget oublié : Qt le peint en clair, et il crève l'écran. Trouvé à
    l'œil une première fois (le cadre gris de l'éditeur), il doit ensuite se
    trouver tout seul.

    On ne bannit pas le clair — le rail de la barre d'avancement et les
    poignées de glissière le sont VOLONTAIREMENT. On signale le clair que la
    feuille ne mentionne nulle part.
    """
    def rvb(c):
        return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)

    def clarte(c):
        r, v, b = rvb(c)
        return (0.2126 * r + 0.7152 * v + 0.0722 * b) / 255

    voulues = [c.lower() for c in
               set(re.findall(r'#[0-9a-fA-F]{6}', qss))]
    suspects = []
    for c, n in compte.items():
        part = 100 * n / total
        if clarte(c) < 0.55 or part < 0.10:
            continue
        # L'anticrénelage fabrique des teintes intermédiaires : on tolère un
        # petit écart avec la couleur déclarée la plus proche.
        proche = min((sum(abs(a - b) for a, b in zip(rvb(c), rvb(v)))
                      for v in voulues), default=999)
        if proche > 40:
            suspects.append((part, c))

    if not suspects:
        print("  aucune plage claire etrangere a la feuille")
        return 0
    for part, c in sorted(suspects, reverse=True):
        print(f"  ECHEC : {c} couvre {part:.1f} % et n'est demande "
              "nulle part dans la feuille")
    return 1


sys.exit(main())
