# Workflows laser — gravure avec le LaserTree (T100)

Guide pratique pas-a-pas pour graver au laser sur la PrintNC, seul ou
apres un usinage. Complement du README (sections Laser et Changement
d'outil), qui documente le POURQUOI ; ici c'est le COMMENT.

---

## La regle d'or des modes

Le palpage d'outil se fait toujours sur le **palpeur fixe** (G53 X-50
Y60). Le premier outil palpe de la session devient la **reference**
(`#1000`), les suivants recoivent un offset relatif a lui. Ce qui
change entre les deux modes, c'est ou vit le zero Z :

| | Mode martyre (`#1001=0`) | Mode piece (`#1001=1`) |
|---|---|---|
| Zero Z | Sur le martyre, defini AUTOMATIQUEMENT par le premier palpage (distance palpeur->martyre = 50.525 mm, mecanique) | Sur le dessus de la piece, pris MANUELLEMENT (papier a cigarette) |
| Qui peut etre la reference ? | N'importe quel outil, **y compris le laser** | UNIQUEMENT l'outil qui a physiquement pris le zero sur la piece — donc **jamais le laser** (il ne touche pas la piece) |

Consequence : `T100 M6` seul suffit en mode martyre. En mode piece, il
faut d'abord une fraise qui touche la piece.

Le laser etant monte sur glissiere a position repetable, on peut le
demonter/remonter librement : chaque `T100 M6` re-palpe son nez sur la
pastille du palpeur fixe (palpage mecanique, decalage XY automatique
gere par `toolchange.ngc`).

---

## Workflow 1 — Gravure seule, zero sur le martyre

Cas : gravure directe sur une planche posee sur le martyre, ou piece
dont l'epaisseur est connue/mesurable au pied a coulisse.

1. Poser la piece/chute sur le martyre.
2. Boutons QtDragon : **Reset Ref** puis **Mode Martyre**.
3. MDI : `T100 M6` — le laser se palpe, definit la reference ET le
   zero martyre. Le message "le LASER va definir la reference" est
   normal pour un job laser seul.
4. Zero XY (voir section "Zero XY au laser" plus bas).
5. Lancer le G-code de gravure. Le dessus de la piece est a
   Z = epaisseur, le point focal se place donc a
   Z = epaisseur + focale (a gerer dans le post CAM, ou en decalant
   le zero : `G10 L2 P1 Z[#5223 + epaisseur]` en MDI remonte le zero
   G54 du martyre au dessus de la piece).

## Workflow 2 — Gravure seule, zero sur le dessus de la piece

Cas : graver le dessus d'une piece d'epaisseur quelconque, sans
usinage prevu. Il faut une fraise (n'importe laquelle) pour toucher.

1. **Reset Ref** puis **Mode Piece**.
2. Monter une fraise, MDI : `T2 M6` (adapter le numero) — elle se
   palpe et devient la reference de session.
3. Zero Z au **papier a cigarette** entre le bas de la fraise et le
   dessus de la piece -> touch off Z0 dans QtDragon (epaisseur du
   papier ~0.03 mm, negligeable pour du laser).
4. Zero XY dans la foulee (avec la fraise, ou plus tard au laser).
5. MDI : `T100 M6` — monter la glissiere pendant la pause, RESUME.
   Le laser se palpe et herite du zero piece via son offset relatif.
6. Lancer la gravure : le point focal est a Z = focale (ex. `G1 Z7`).

## Workflow 3 — Job mixte : usinage puis gravure

Cas : fraiser une piece puis graver dessus, en reutilisant le meme
zero. C'est le flux naturel du systeme, rien de special a faire.

1. **Reset Ref**, choisir le mode (martyre ou piece) et faire les
   zeros comme pour un job d'usinage normal.
2. `T2 M6`, usiner (la fraise est la reference de session).
3. `T100 M6` — monter la glissiere, RESUME. Le laser recoit son
   offset relatif a la fraise : il connait exactement le zero utilise
   pour l'usinage.
4. Graver. L'alignement XY gravure/usinage depend des offsets X/Y de
   T100 dans tool.tbl — a valider UNE FOIS avec
   `gcode_tests/test_offset_laser_xy.ngc` (signe du Y suspect, voir
   README).

Ordre inverse (graver puis usiner) : possible en mode martyre
uniquement (le laser peut etre la reference, la fraise palpee ensuite
retrouve le bon zero). Impossible en mode piece.

---

## Zero XY au laser (tir a faible puissance)

Avec `T100 M6` fait et `G43 H100` actif (les offsets XY du laser
s'appliquent, le touch off est donc directement valable) :

1. **Lunettes laser.**
2. MDI : `M3 $1 S20` (2 %, juste visible sans marquer).
3. Jog pour amener le point sur le coin/repere de la piece.
4. MDI : `M5 $1` (coupe reellement le faisceau via AUX3).
5. Touch off X0 Y0 dans QtDragon.

## En-tete type d'un G-code de gravure

```gcode
T100 M6
G43 H100
M3 $1 S0        ; arme le laser (relais AUX3), faisceau a 0
...
S500 $1         ; puissance pendant les G1 (500 = 50%)
G1 X.. Y.. F1500
S0 $1           ; faisceau a 0 sur les deplacements G0
...
M5 $1           ; fin : coupe reellement le faisceau
```

Rappels (details au README) : le S-word est une puissance 0-1000, pas
une vitesse ; `S0` laisse le laser ARME (seul `M5 $1` ouvre le relais
AUX3) ; un feed hold / M1 ne coupe PAS le faisceau -> jamais de
gravure sans surveillance.

---

## Calibrations a faire une fois

| Quoi | Comment | Ou reporter |
|---|---|---|
| Focale (inconnue a ce jour) | `gcode_tests/test_focale_laser.ngc` : rampe de traits Z 3->10 mm, le plus fin = focale | `z_focus` du post CAM + README |
| Offsets X/Y de T100 (signe Y suspect) | `gcode_tests/test_offset_laser_xy.ngc` : croix fraisee vs croix laser, corriger `X_nouveau = X_actuel - dX` (idem Y) puis recharger la table d'outils | tool.tbl ligne T100 |

## Piste future : plaque de contact

La plaque de contact (pince crocodile) pas encore cablee permettrait,
en mode piece, de remplacer le papier a cigarette par un `G38.2` +
`G10 L20 P1 Z<epaisseur plaque>`. Et si le cone metallique du laser
est conducteur (a verifier au multimetre, l'anodisation isole), pincer
le crocodile dessus permettrait de palper la piece directement avec le
nez du laser -> plus besoin de fraise du tout en mode piece.
