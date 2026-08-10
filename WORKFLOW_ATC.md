# Workflow magasin ATC (ER20) - PrintNC Atelier du Verdier

Etat au 9 aout 2026.

---

## Ce qui change aujourd'hui : RIEN

`REMAP=M6` pointe toujours sur `toolchange.ngc`. **Ton mode semi-manuel marche
exactement comme avant** : `T3 M6` amene la broche en X150 Y0, met en pause, tu
montes l'outil a la main, il palpe, il repart.

Les fichiers ATC sont poses a cote, sans etre branches. Rien ne peut partir tout
seul.

| Fichier | Role |
|---|---|
| `subroutines/atc_config.ngc` | tous les reglages, rien d'autre |
| `subroutines/atc_toolchange.ngc` | depose / prise / palpage |
| `subroutines/palper_outil.ngc` | palpage + offsets, appele par les deux |
| `outils/verifier_ngc.py` | controle structurel des `.ngc` |

Le detail technique et les calculs sont dans `CHANGELOG.md`, entree du 9 aout.
Ce fichier-ci ne dit que **quoi faire, dans quel ordre**.

---

## 1. LA mesure qui decide de tout

Avant de percer quoi que ce soit dans la table.

Pour aller chercher un outil, la broche doit le **sortir** de son poste et
passer **au-dessus** du magasin — avec l'outil qui pend dessous. C'est
l'empilement au-dessus du martyre qui commande, et il depend du montage choisi :

| montage | empilement | degagement sous l'ecrou |
|---|---|---|
| plaque 38 (d'origine) | 91,5 mm | 65,9 mm |
| **couvercle ramene a 5** (fait le 09/08) | **86,5 mm** | 65,9 mm |
| plaque ramenee a 12 (outils ≤ 40) | 60,5 mm | 39,9 mm |
| **lit de la CNC perce, sans plaque** | **48,5 mm** | 27,9 + epaisseur du lit + vide dessous |

> **Le test, 30 secondes.** Monte ton outil le plus long (le releve du 08/08 dit
> **60 mm** sous l'ecrou). Fais monter Z tout en haut (`G53 G0 Z0`). Mesure du
> **bout de l'outil au martyre**. Il faut **l'empilement de ta ligne, plus une
> vingtaine de millimetres de marge**.

**A verifier au passage** : `[AXIS_Z] MIN_LIMIT` est passe de −185 a **−140**
le 9 aout. Si cette limite est un choix logiciel et non une butee physique, elle
vient de couter 45 mm — exactement la grandeur en jeu ici.

### Les trois leviers, par ordre de rendement

1. **Percer le lit de la CNC** (43 mm) — l'outil traverse le lit et prend son
   degagement dans le vide en dessous. La plaque bois disparait.
2. **Amincir la plaque** (jusqu'a 26 mm) — `plaque_ep` n'existe que pour laisser
   le bec ressortir sous le bloc, et le bloc donne deja **27,94 mm**. Il faut
   `plaque_ep ≥ outil_le_plus_long − 27,94` : 32 mm pour un outil de 60,
   **12 mm pour un outil de 40**.
3. **Le couvercle** (5 mm) — fait le 09/08, `COUVERCLE_EP` 10 → 5.

Les leviers 1 et 2 s'excluent. Dans les deux cas la vraie question est la meme :
**quel est l'outil le plus long que tu mets AU MAGASIN ?** Les autres peuvent
rester en manuel, le sous-programme sait les renvoyer.

### Si tu perces le lit

- **Poser le bloc sur quelque chose qui ne bouge pas.** Le martyre se
  resurface ; a chaque passe, le magasin descend d'autant et **`engage_z` est
  faux** — la fenetre ne fait que ± 1 mm. Boulonner a travers le lit dans le
  bati, pas dans le martyre.
- **Faire percer les trous par la machine elle-meme**, aux coordonnees des
  postes, avant de poser le bloc. Aucune erreur de report : ce sont exactement
  les coordonnees que la macro utilisera.
- Les goupilles Ø8 et les vis de bridage, que la plaque portait, vont
  desormais dans le lit. Goupilles au Ø **nominal** dans le bois : on ne les
  chasse pas, on les glisse.
- Les Ø28 debouchent sous la machine : les copeaux tomberont au travers.
- **Le modele ne sait pas encore le faire** : `PLAQUE_EP = 0` plante
  (`makeBox`, hauteur nulle). Il faut un drapeau `AVEC_PLAQUE`, sur le modele
  d'`AVEC_CHAPEAU` qui existe deja, et `outil_max()` doit alors lire le
  degagement reel sous le bloc au lieu de l'epaisseur d'une plaque.

---

## 2. Ou poser le magasin

### Encombrement

| | X | Y | Z au-dessus du martyre |
|---|---|---|---|
| magasin x6 | **450 mm** | **71,2 mm** | 86,5 mm (48,5 sans plaque) |
| magasin x4 | 300 mm | 71,2 mm | 86,5 mm (48,5 sans plaque) |
| quai dust shoe | ~150 mm | ~160 mm (Ø170 a l'arc) | ~94 mm |

Postes espaces de **75 mm**, le premier a **37,5 mm** du bout du bloc. Positionne
par **2 goupilles Ø8** dans la table, plus les vis M6 : le bridage ne fait que
serrer, il ne localise pas.

### Course machine

X de **−50 a 1240**, Y de **−2 a 1286**, Z de **−140 a +5**.

### Deja pris — ne pas empieter

- **Palpeur fixe : X −50, Y 60.** Au ras de la limite X. Chaque changement
  d'outil y passe.
- **Position de montage manuel : X 150, Y 0.** Utilisee par `toolchange.ngc`
  pour les outils hors magasin.
- **Laser T100 : decale de la broche.** Quand le laser travaille, la broche est
  ~90 mm a cote. Toute la zone que le laser peut atteindre doit rester libre du
  passage de la broche.
- **Quai dust shoe : au FOND de la machine** (decide le 08/08), le sabot y entre
  par une translation pure en **+X**. Laisser son couloir d'entree degage.

### Disposition qui tombe juste

Le quai etant au fond, le magasin va **a l'avant**, long axe en X :

```
   Y+  +--------------------------------------------------+
       |            QUAI DUST SHOE (entree +X)            |   fond
       |                                                  |
       |                                                  |
       |                 ZONE DE TRAVAIL                  |
       |                                                  |
       |   [] magasin x6, 450 x 71,2, long axe en X       |   avant
   Y0  +--------------------------------------------------+
        X-50 (palpeur)                              X1240
```

Poser le bloc a partir de **X ≈ 300** laisse le palpeur (X −50) et la position
de montage manuel (X 150) tranquilles ; le x6 va alors de X 300 a X 750, et le
poste 1 tombe a **X 337,5**.

`_atc_axe = 1` bascule tout en Y si tu preferes le long du cote gauche.

---

## 3. Les 4 valeurs a relever

Elles valent **999** dans `atc_config.ngc`, et le sous-programme **refuse de
tourner** tant qu'elles y sont. Magasin boulonne, goupilles en place :

| Parametre | Comment l'obtenir |
|---|---|
| `_atc_poste1_x` | X machine de l'axe du poste 1 |
| `_atc_poste1_y` | Y machine de l'axe des postes |
| `_atc_engage_z` | **la recette ci-dessous** |
| `_atc_z_sur` | Z machine de transit : bout de l'outil le plus long au-dessus de l'empilement (§ 1), plus une marge |

### La recette pour `engage_z`

> Ecrou **visse a fond sur la broche**. Descendre jusqu'a ce qu'il **touche le
> cone** du siege — le siege est encore en butee haute, il ne s'enfonce pas.
> Descendre **1,00 mm de plus**. Ce Z est `engage_z`.

**Tolerance ± 1,00 mm, pas un dixieme de plus.** C'est toute la fenetre que le
ressort peut rattraper (`COURSE − FILETAGE_ENGAGE` = 12 − 10). Trop haut,
l'ecrou n'est pas serre en fin de vissage et l'outil part au premier passage —
en silence. Trop bas, le siege tape le fond de poche pendant le devissage.

**Ne pas confondre avec « enfoncer le siege de 10 a 12 mm »** : a `engage_z` le
siege n'est enfonce que de **1 mm**. Les 11 mm ne sont atteints qu'en fin de
devissage.

---

## 4. Mise en service, dans l'ordre

Ne pas sauter d'etape : la piece qui encaisse est un siege imprime.

### Etape 1 — a blanc, aucune rotation

`_atc_essai = 1` (valeur par defaut). Magasin en place, **poste vide**, broche
vide.

```gcode
O<atc_toolchange> call [1]
```

La broche fait tous les mouvements, **aucune rotation**, et s'arrete a la
precharge en annoncant ce qu'elle attend. Verifier a l'oeil :

- elle vise bien l'axe du poste ;
- elle ne touche rien en transit ;
- au fond de la prise, le nez est bien **1 mm dans** l'ecrou.

Refaire sur le dernier poste : c'est lui qui cumule les tolerances de `_atc_pas`.

### Etape 2 — a blanc, avec un ecrou

Meme chose, un ecrou + pince + outil court dans le poste. On regarde si le
six-pans descend droit dans la chambre et si les billes l'attrapent.

### Etape 3 — depose seule, en rotation

`_atc_essai = 0`, `_atc_confirmer = 1`, `_atc_rpm_depose = 800`. Outil monte a
la main, serre normalement. Depose uniquement.

**Regarder le siege apres chaque essai.** Le regime est borne en bas par le
couple qu'il faut, en haut par ce que le PETG supporte, et **aucune des deux
bornes n'est connue**. Monter par paliers de 100 a 200 tr/min. Un siege fendu se
voit ; un ecrou mal serre, non.

### Etape 4 — prise en rotation

Puis verifier le serrage **a la clef** : si l'ecrou se laisse tourner a la main,
augmenter `_atc_coups` avant d'augmenter `_atc_rpm_serrage`.

### Etape 5 — brancher M6

Quand les deux sens passent dix fois de suite :

```ini
REMAP=M6 modalgroup=6 ngc=atc_toolchange
```

Puis supprimer le palpage duplique de `toolchange.ngc` et le faire appeler
`palper_outil.ngc` — une seule des deux copies doit survivre.

---

## 5. Aide-memoire

```gcode
O<atc_toolchange> call [3]     ; essai en MDI, outil 3
```

```bash
python3 outils/verifier_ngc.py subroutines/*.ngc
```

| Symptome | Ce qu'il faut toucher |
|---|---|
| abandon « parametre a 999 » | une valeur d'etabli manque |
| abandon « plongee au-dessus du plafond » | baisser `_atc_rpm_prise` (max 759) |
| le six-pans reste assis sur les billes | baisser `_atc_f_coup` |
| l'ecrou n'est pas serre | `_atc_coups`, puis `_atc_rpm_serrage` |
| le siege tape en fin de devissage | `engage_z` trop bas |
| l'outil part en cours d'usinage | `engage_z` trop haut : l'ecrou n'a jamais ete serre |

---

## 6. Pieges connus

- **La pompe a eau demarrera a chaque changement.** `spindle_cooldown` est cable
  sur le FLOOD : des que la broche tourne, la pompe part, et reste 30 s apres.
  Circuit ferme de refroidissement broche, donc sans danger pour le magasin.
- **Aucune sortie libre pour un soufflage.** M7 = air du laser, M8 = pompe,
  AUX0-3 toutes prises. Piste : teer M7, puisque graver et changer d'outil ne
  coexistent jamais.
- **Rien ne dit que la broche tourne encore apres un M5.**
  `spindle.0.at-speed` est force a VRAI des qu'elle est a l'arret commande (le
  correctif laser de juillet). D'ou `_atc_arret_broche`, a caler sur le temps de
  deceleration du Huanyang (PD015).
- **Chaque coup de serrage est un calage du variateur.** Verifier ce que le
  Huanyang fait sur surintensite avant le premier essai en rotation : une
  protection agressive fera disjoncter au premier coup.
- **Incoherence a trancher** : `tool.tbl` porte `Y+88.75` pour T100, mais
  `toolchange.ngc` utilise `laser_y_offset = -90`. Les deux ne peuvent pas etre
  vrais. Sans rapport avec l'ATC, mais ca traine.
