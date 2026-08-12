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
(`~/Projets/visualiseur-gcode`) interprète le fichier avec `rs274` et montre ce
que la machine ferait — y compris les sous-programmes, grâce au
`SUBROUTINE_PATH` ci-dessus.

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
