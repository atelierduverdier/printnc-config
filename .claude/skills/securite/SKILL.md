---
name: securite
description: >-
  Travailler sur la configuration LinuxCNC de la PrintNC sans mettre la machine ni
  l'opérateur en danger : demander avant tout mouvement, le jumeau _sim, le flux PC →
  dépôt → Pi, sync-gcode.sh go, M5 $1 en fin de programme, jamais pkill qtvcp, P6 et
  le laser. À charger pour TOUTE modification dans ce dépôt, HAL, INI, .ngc, .ui ou thème.
---

# Ce dépôt pilote une machine, pas un logiciel

## 1. Avant tout essai qui met la machine en mouvement : demander

Une erreur de signe dans un `.ngc` ou un HAL, c'est un plongeon de broche ou un
faisceau laser allumé. On modifie sur le **PC**, on éprouve en **simulation**,
on pousse, Christophe récupère sur le **Pi** et lance. Jamais l'inverse. Aucun
essai réel sans son accord explicite dans la conversation.

## 2. Toujours toucher le jumeau `_sim`

Chaque config a son double de simulation. Une modification qui n'est pas
reportée dans le `_sim` ne sera pas éprouvée avant la machine.

## 3. Le G-code

- **Tout programme finit par `M5 $1`** : `S0` laisse le laser **armé**, et une
  pause ne le coupe pas.
- Contrôle de forme : `python3 outils/verifier_ngc.py subroutines/*.ngc`.
- Vrai contrôle de trajectoire : `~/Projets/logiciels/visualiseur-gcode`
  (`rs274`), jamais un interpréteur maison.
- Les valeurs `[ETABLI]` à **999** dans `atc_config.ngc` sont une sentinelle :
  ne jamais les remplacer par une estimation, elles se mesurent à l'établi.
- Le partage `/mnt/srv-partage/Gcode` fait foi ; `~/linuxcnc/nc_files` est un
  cache jetable, et on ne grave pas depuis le partage. Copie par
  `outils/sync-gcode.sh go` — **sans `go`, c'est un essai à blanc**, rien n'est copié.

## 4. L'électronique

**P6 jamais sur 12 V en mode PWM.** Le laser LT-80W est sur `spindle.1` et son
HAL ramène la puissance à 0 à l'arrêt : une pause faisceau allumé engrave donc
un blanc (cf. LaserAtelier, règle du `G4`). Le VFD Huanyang tient le port
série : arrêter LinuxCNC avant de le lire.

## 5. L'interface QtDragon

- **Jamais `pkill qtvcp`** : segfault systématique, scripts fantômes,
  `/tmp/linuxcnc.lock` survivant. Sortir par EXIT ; arrêt scriptable par
  KWin/qdbus6 (`loadScript /tmp/fermer.js` + `Script.run`). Viser `Alt+Y`,
  jamais Entrée, sur la confirmation.
- Un bouton se raccorde dans le `<connections>` du `.ui` ; un slot absent fait
  échouer **tout l'écran**.
- La palette se corrige dans `outils/faire_theme.py` (qui engendre le `.qss`
  sous ses deux noms), jamais dans le `.qss` ; aperçu hors écran par
  `python3 outils/apercu_theme.py`.

## 6. Le dépôt

Worktrees nettoyés par `git worktree remove`. Documents à tenir :
`WORKFLOW_ATC.md`, `WORKFLOW_LASER.md`, `AFFECTATION_AUX.md`, `CHANGELOG.md`.
Push sur `main`, puis récupération sur le Pi par Christophe.
