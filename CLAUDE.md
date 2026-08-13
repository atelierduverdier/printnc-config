# CLAUDE.md

Ce qui doit être vrai à **chaque** session sur ce dépôt.

Le `README.md` porte le détail : la nomenclature, les mesures au multimètre,
l'histoire des convertisseurs, les timings de pas. **Ce fichier ne le recopie
pas** — il porte les règles de travail et renvoie au README.

## Ce que c'est

La configuration **LinuxCNC** d'une fraiseuse PrintNC réelle : carte Flexi-HAL,
VFD Huanyang, tête laser LT-80W sur `spindle.1`, interface QtDragon HD, magasin
ATC ER20 en cours de pose.

**Ce dépôt ne produit pas un logiciel : il pilote une machine.** Une erreur ici
ne fait pas planter un programme, elle casse un outil, brûle du bois ou détruit
un laser. C'est la différence à garder en tête sur tout ce qu'on y touche.

## Non négociable

### 1. Deux machines, un seul dépôt

* **Raspberry Pi (production)** — pilote la vraie machine. Lance
  `remora-flexi.ini`.
* **PC (développement)** — simulation, sans matériel. Lance
  `remora-flexi-sim.ini`.

Les fichiers en `_sim` remplacent le composant Flexi-HAL (SPI) et le VFD série
par des équivalents simulés. **Une modification se fait sur PC, s'éprouve en
simulation, se pousse, puis se récupère sur le Pi.** Jamais l'inverse, et jamais
directement sur le Pi : les deux copies divergeraient.

Corollaire : toucher à un fichier de production sans toucher son jumeau `_sim`
casse la simulation, et l'on ne s'en aperçoit qu'à la session suivante.

### 2. Le jumper P6 protège le laser

**Ne jamais mettre P6 sur 12 V en mode PWM.** P6 fixe l'alimentation de
l'ampli op, donc l'amplitude du carré en sortie. Sur 12 V, le PWM enverrait
~10,5 V droit dans l'entrée TTL 5 V du LaserTree. Réglage correct : **P6 sur
5 V, P7 vertical**.

C'est du matériel, pas du logiciel — on ne peut que le vérifier et le rappeler.
Mais tout changement de la chaîne PWM doit être relu avec cette contrainte en
tête.

### 3. Une pause ne coupe pas le laser

Un feed hold ou un `M1` **ne coupe pas les broches** : un travail laser en pause
continue d'émettre au point fixe, sur du bois. Seul `M5 $1` ouvre le relais AUX3
et coupe vraiment le faisceau ; `S0 $1` met la puissance à zéro mais **laisse le
laser armé**.

Tout G-code ou toute macro écrite ici doit finir par `M5 $1`, et jamais se
contenter d'un `S0`.

### 4. Le G-code n'habite plus ici

Les programmes ont été sortis de la config machine (commit « Sortir le G-code de
la config machine »). Ce qui reste dans `subroutines/` est de
l'**infrastructure** appelée par la machine — changement d'outil, palpage, prise
de référence, `on_abort` — pas des pièces à usiner.

`SUBROUTINE_PATH` liste **les deux clones**, machine d'abord puis poste de
conception : c'est ce qui permet au visualiseur de résoudre les sous-programmes
sans rien changer au comportement de la machine.

### 5. Les paramètres d'établi ne se devinent pas

`subroutines/atc_config.ngc` porte des valeurs marquées `[ETABLI]`, à **999**
tant qu'elles n'ont pas été mesurées. Le sous-programme refuse de tourner tant
qu'il en reste une — c'est voulu. Ne jamais remplacer un 999 par une estimation
« raisonnable » : la sentinelle est le garde-fou.

## Vérifier une modification

```bash
python3 outils/verifier_ngc.py subroutines/*.ngc
```

Il ne dit pas si un sous-programme est **juste**, il dit s'il est **bien
formé** : `sub`/`endsub` appariés et nommés comme le fichier, `O<numéro>`
imbriqués et refermés du bon numéro, tout paramètre lu écrit quelque part, et
chaque `o<nom> call` visant un fichier qui existe. C'est la passe `ast.parse` du
G-code.

Pour un vrai contrôle de trajectoire, le **visualiseur de parcours**
(`~/Projets/logiciels/visualiseur-gcode`) interprète le fichier avec `rs274` et montre ce
que la machine ferait — y compris les sous-programmes, grâce au
`SUBROUTINE_PATH` ci-dessus.

## L'interface : le thème maison

`qtvcp/screens/qtdragon_hd/verdier.qss` habille `qtdragon_hd` aux couleurs de
l'atelier — orange `#ff9a1f` sur ardoise `#14171b`, les jetons de
`kit/verdier-jetons.css` du dépôt `site`. **Le comportement n'est pas
touché** : une feuille de style ne peut pas l'être. Mêmes boutons, mêmes
onglets, mêmes fonctions qu'à l'origine.

Il n'est **pas écrit à la main**. `outils/faire_theme.py` le dérive du
`dark.qss` que livre LinuxCNC, parce que ce fichier couvre 72 sélecteurs et
qu'un thème qui en oublie un laisse le widget en style Qt par défaut — une
plage claire au milieu de l'ardoise. Corriger la palette **dans le script**,
jamais dans le `.qss`, et relancer.

```bash
python3 outils/faire_theme.py      # engendre verdier.qss
python3 outils/apercu_theme.py     # le rend hors ecran, dans /tmp
```

L'aperçu existe parce que **Qt n'annonce pas les erreurs de syntaxe d'une
feuille QSS** : une accolade en trop et tout ce qui suit est ignoré, sans un
mot. Le seul verdict est de compter les pixels, et c'est ce que fait le
script — il refuse aussi toute plage claire que la feuille ne demande pas.
Éprouvé dans les deux sens : muet sur `verdier`, il attrape sur `dark` un
`#c0c0c0` qui couvre **30 % de l'écran**.

Ce que la dérivation a corrigé au passage, tout mesuré :

* `dark.qss` n'est sombre qu'à moitié — menus, onglets, en-têtes et zone de
  texte étaient restés clairs, dont **cinq** avec un fond clair et **aucune**
  couleur de texte : les assombrir sans plus donnait du noir sur ardoise ;
* il n'habille **ni** le visualiseur de G-code (`EditorBase`, qui prend ses
  couleurs par `qproperty-`, pas par les règles ordinaires), **ni** les barres
  de défilement, **ni** les 99 infobulles, **ni** `gcode_list` ;
* « Lato Heavy », demandée **seize** fois, n'est installée nulle part et n'est
  pas empaquetée sur Arch : tout retombait en silence sur Noto Sans.

Deux choix à connaître, parce qu'ils ont l'air d'erreurs :

* **le rail de la barre d'avancement reste clair.** Les six thèmes livrés font
  pareil, et c'est leur raisonnement : Qt dessine le texte d'une seule couleur
  par-dessus le rempli **et** le vide. `spindle_power` écrit « POWER %p% » sur
  toute la largeur ; avec un rail sombre, aucune encre ne se lit des deux
  côtés.
* **le couple rouge/vert de l'arrêt d'urgence n'est pas repeint.** C'est un
  état machine, pas un ornement. Un arrêt d'urgence orange au milieu d'une
  interface orange ne se voit plus.

Les couleurs de la coloration syntaxique sont celles que le **visualiseur de
parcours** emploie déjà pour le même G-code — cyan le travail, jaune le
palpage. Même langage de couleur du visualiseur à la machine.

### Ce que seul le lancement RÉEL a trouvé

L'aperçu hors écran valide la feuille, pas l'écran : il ne monte qu'un
échantillon de widgets. Quatre défauts n'ont sauté aux yeux qu'en lançant
qtdragon pour de vrai, et trois étaient de mon fait.

* **Une couleur nommée peut survivre à une réécriture.** `brown` est tombé
  d'une table de correspondance, et les boutons ont porté une bordure marron
  jusqu'au lancement. Le contrôle d'alors ne cherchait que des `#hex`. Il
  cherche désormais **tout mot en position de couleur** : il en trouve sept
  dans `dark.qss` — `black, brown, gray, orange, red, white, yellow` — et
  aucun dans `verdier.qss`.
* **`black` et `gray` jouent trois rôles** : bordure, fond, encre. Traduits en
  bloc, ils ont donné `color: #2a3038` sur `background: #1a1e23` dans la ligne
  MDI — **1,4:1, illisible** — et auraient peint tous les dialogues en gris
  moyen. Un contrôle de contraste refuse maintenant tout couple sous 3:1.
* **`red` et `yellow` sont des états**, pas des ornements : DRO non référencé,
  correcteur d'avance hors plage. Ils gardent leur teinte.
* **La barre d'état ne vient PAS de la feuille.** `set_style_default()` du
  gestionnaire pose `rgb(252,252,252)` par `setStyleSheet` **sur le widget** —
  et un style de widget bat celui de l'application. Aucun thème ne peut
  l'atteindre : c'était une bande blanche pleine largeur au bas de l'écran.
  Corrigé dans le gestionnaire. Les états avertissement (jaune) et critique
  (orange) sont laissés tels quels, ce sont des alertes.

Reste une question ouverte : l'état **critique** de cette barre est
`rgb(255,144,0)`, à un cheveu de l'orange d'accent `#ff9a1f`. Une alerte qui a
la couleur de la décoration alerte moins.

Pour l'allumer : onglet **Settings**, sélecteur de thème, « verdier ». Le
choix s'écrit dans `style_QSS_Path`, section `[BOOK_KEEPING]` de
`qtdragon.pref` — qui n'est pas dans ce dépôt.

### Le dossier de surcharge fige l'écran — et retient un correctif

`qtvcp/screens/qtdragon_hd/` est une **copie complète** de l'écran amont, pas
un jeu de retouches. qtvcp résout chaque fichier séparément (`.ui`, `.qss`,
`_handler.py`, `.qrc`), en cherchant d'abord dans la config : n'y mettre que
ce qu'on a modifié suffirait, le reste continuerait d'arriver du système.

Relevé le 13/08/2026, copie contre `/usr/share/qtvcp/screens/qtdragon_hd/` :

| fichier | état |
|---|---|
| `qtdragon_hd.ui` | **modifié**, 263 lignes d'écart — textes, géométries, `lbl_tool_image` |
| `qtdragon_hd_handler.py` | **modifié**, 116 lignes d'écart |
| les 5 `.qss` livrés, `.qrc`, `_ABOUT` | **identiques** — poids mort |
| `resources.py`, `images/` | absents du système : à garder |

Et `version.txt` dit le prix : la copie est en **1.5**, le système livre la
**1.6**, qui corrige *« incremental keyboard jogging had to hold key down
until jog finished »*. Ce correctif n'arrive pas sur la machine, et rien ne
le signale.

Le `.ui` et le gestionnaire portent de vraies retouches : on ne les supprime
donc pas. Les remettre à niveau demande de rejouer ces retouches sur la base
1.6 — un vrai chantier, à faire sciemment, pas au détour d'autre chose.

### Le voyant LASER ARME

Panneau **INPUTS**, juste sous PROBE, rouge et non vert : un laser sous
tension est un danger, pas un état courant. Il suit `laser-arm`, la net qui
existait déjà (`spindle.1.on => flexi.output.AUX3`) — s'y greffer n'enlève
rien à l'interlock, un signal ayant une source et autant de destinations
qu'on veut.

Il comble le seul vrai trou de l'interface : **rien à l'écran ne disait que
le laser était sous tension**, alors qu'une pause ne le coupe pas et que le
jumper P6 est la seule autre protection.

**Il reste éteint en simulation, et c'est exact** : `remora-flexi-sim.ini`
déclare `SPINDLES = 1`, donc `spindle.1.on` n'y existe pas. Rien à câbler
côté banc — une entrée de LED sans source vaut faux, ce qui est la vérité.

Deux retards corrigés en même temps, le 13/08/2026 :

* le bouton **AUX 3 a été retiré du `.ui`**. Le postgui disait lui-même que
  « le bouton QtDragon AUX3 n'a plus d'effet » depuis qu'AUX3 est dédié au
  laser. Attention : sa broche était encore nettée dans
  `custom_postgui_sim.hal`, et **laisser cette ligne aurait fait échouer le
  chargement de HAL** sur une pin disparue. Les deux vont ensemble.
* **AUX 2 s'appelle désormais VENTILATEURS**, ce qu'il pilote réellement.

Et le commentaire en tête de `custom_postgui.hal` annonçait ses trois `net`
comme « désactivées temporairement » alors qu'elles étaient actives depuis
longtemps : corrigé.

**Ce qui reste à décider** : le voyant **LIMIT** ne s'allumera jamais. Sa
broche `qtdragon.led-limits-tripped` n'est câblée nulle part et ne peut pas
l'être — les contacteurs sont en prise d'origine seule (5 `home-sw-in`,
**zéro** `lim-sw-in`). Un voyant éteint en permanence se lit « rien de
déclenché, tout va bien » : c'est l'alarme qui s'apprend à ignorer. Le
masquer serait plus honnête que le laisser.

### Le logo de la machine, et les trois murs rencontrés

`qtvcp/screens/qtdragon_hd/images/logo-verdier.png` s'affiche **au centre du
panneau de gauche tant qu'aucun programme n'est chargé**, et disparaît au
premier fichier. Règle reprise du visualiseur de parcours : une marque qui
reste par-dessus le travail devient un tampon sur le pare-brise.

C'est le **logo complet** — chapeau, « PrintNC », « Orange Mécanique » — et
non le chapeau seul : la machine EST une PrintNC, et le dessin le dit. Le
partage vient du visualiseur (`interface/marque.py`) : le chapeau seul fait
les icônes, parce qu'à seize pixels le reste n'est plus qu'une tache ; le
logo complet va là où il y a la place.

L'image est **engendrée** par `outils/faire_theme.py` depuis
`ressources/printnc.svg` du dépôt du visualiseur — pas recopiée. Son texte y
est déjà converti en courbes, sans quoi les trois polices d'origine, qui
n'existent que sur ce poste, le rendraient méconnaissable ailleurs. En PNG et
non en SVG parce que `PyQt5.QtSvg` est un paquet séparé sur Debian et n'est
pas garanti sur le Raspberry Pi.

Trois murs, tous payés :

* **Il n'est pas dans la vue 3D, et ce n'est pas un choix.** `gcodegraphics`
  est un `QGLWidget` — l'ancien widget OpenGL à fenêtre native — et la surface
  GL peint **par-dessus** ses enfants. Hors écran l'étiquette se voyait ; sur
  la vraie fenêtre elle avait disparu. L'y mettre demanderait de sous-classer
  le widget et de le promouvoir dans le `.ui`.
* **`HandlerClass` n'est pas un `QObject`.** `installEventFilter(self)` lève un
  `TypeError` qui fait surgir la boîte d'erreur de qtvcp au démarrage. D'où
  `RecentreurLogo`, un vrai `QObject`, dont il faut **garder la référence**
  sinon le ramasse-miettes l'emporte.
* **Ni `__file__` ni `paths.IMAGEDIR` ne désignent le dossier de l'écran.**
  qtvcp charge le gestionnaire autrement, et `IMAGEDIR` est
  `/usr/share/qtvcp/images`, les icônes communes. Il faut chercher comme
  qtvcp : `CONFIGPATH/qtvcp/screens/<écran>/images/` d'abord, `SCREENDIR`
  ensuite.

Et pour déboguer tout ça : **`print()` ne sert à rien ici.** Le script
`/usr/bin/linuxcnc` ne redirige que stderr (`exec 2>>$DEBUG_FILE`), la sortie
standard de l'affichage se perd, et Python la tamponne de toute façon. Même
piège que la console de FreeCAD ailleurs dans l'atelier, même parade : écrire
dans un fichier. C'est ce que fait `dire_logo()`, vers
`/tmp/logo-diag.txt`, et **uniquement quand quelque chose manque**.

### Ne jamais arrêter qtvcp au signal

**`pkill qtvcp` le fait planter par segfault, à tous les coups** — quatre
tentatives, quatre `SIGSEGV` de `python3.14` dans `coredumpctl`, chacun à la
seconde du signal, jamais au démarrage. Pire, le script `/usr/bin/linuxcnc`
qui l'enveloppe **survit** au SIGTERM et reste bloqué : cinq scripts fantômes
se sont accumulés en une session, et le lancement suivant a échoué en
demandant « LinuxCNC is still running. Restart it? » — un dialogue Tk qui
ressemble à une panne du thème alors que c'est un reste. Il faut alors un
`kill -9` sur le script.

La sortie par le bouton **EXIT est propre** : aucun segfault, HAL et les
segments NML libérés, zéro script résiduel. Mesuré le 13/08/2026, référence
à 4 segfaults avant, 4 après.

Et un `kill -9` laisse pire encore : **`/tmp/linuxcnc.lock` survit**. Le
lancement suivant ouvre alors « LinuxCNC is still running. Restart it? » et
attend une réponse — ce qui ressemble à une panne de la configuration alors
qu'il suffit de `rm /tmp/linuxcnc.lock`. Vérifier aussi les segments partagés
orphelins avec `ipcs -m`.

Le bouton appelle `self.QTVCP_INSTANCE_.close()`
(`qtvcp/widgets/action_button.py:687`), donc une demande de fermeture du
gestionnaire de fenêtres passe par le même chemin — utile pour scripter un
arrêt propre :

```bash
qdbus6 org.kde.KWin /Scripting loadScript /tmp/fermer.js f && \
  qdbus6 org.kde.KWin /Scripting/Script0 org.kde.kwin.Script.run
```

où le script appelle `closeWindow()` sur la fenêtre de classe `qtvcp`. Une
confirmation « Do you want to Shutdown now? » s'ouvre ensuite : **viser
`Alt+Y`, jamais la touche Entrée** — le troisième bouton est « System
Shutdown », qui éteint l'ordinateur.

Sous Wayland, XTEST **ne peut pas** déplacer le pointeur (le compositeur le
possède, vérifié : la position ne bouge pas d'un pixel). Les événements
clavier XTEST, eux, arrivent bien à la fenêtre XWayland qui a le focus X.

## Ce qui a été payé

* **Le mot `S` par bloc arrête la machine.** Prouvé par deux fichiers jumeaux.
  `M67 E0` a remplacé le `S` : mesuré sur bois le 31/07/2026, +2 % de temps
  seulement sur 64 869 changements de puissance, et 56 minutes épargnées.
* **Piège multi-broche** : un travail laser seul gelait au premier `G1`, laser
  allumé, sans message. LinuxCNC attendait `spindle.0.at-speed` alors que seule
  `spindle.1` était commandée. Corrigé par `atspeed_or` + `s0_on_not`, **sans**
  perdre la sécurité fraisage.
* **Un `(MSG,…)` ne développe rien.** Il ne se suffit que de son texte littéral.
* **`2.9.0~pre1` de Debian multiplie par 25,4** les décalages de la table
  d'outils. La version doit correspondre à celle de la machine — 2.9.10.

## Prudence

Il y a des **worktrees Claude oubliés** dans `.claude/worktrees/` : ils ne sont
pas suivis par git, mais `git worktree list` les montre et ils gênent la
lecture du dépôt. Les nettoyer par `git worktree remove`, jamais par un `rm -rf`
qui laisserait les métadonnées derrière.

Et la règle générale de l'atelier vaut doublement ici : **demander avant tout
essai qui met la machine en mouvement**.
