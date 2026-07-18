# Configuration PrintNC - Atelier du Verdier

Ce depot rassemble les fichiers de configuration LinuxCNC (`.ini`, `.hal`,
macros G-code et interface QtDragon) utilises pour piloter ma fraiseuse CNC
**PrintNC** (surface de travail utile d'environ 1275x1275 mm), equipee
d'une broche 2.2 kW et d'un module laser amovible (voir section Laser).

La machine est controlee via l'architecture **Flexi-HAL** (firmware Remora) sur
base Raspberry Pi, avec l'interface graphique **QtDragon HD** (LinuxCNC 2.9.8).

---

## Environnement de developpement (2 machines)

Le depot est synchronise entre deux machines via git :

* **Raspberry Pi (production)** : pilote la machine reelle avec le materiel
  Flexi-HAL et le VFD. Config lancee : `remora-flexi.ini`.
* **PC (developpement)** : sert a modifier l'interface QtDragon en simulation,
  sans materiel. Config lancee : `remora-flexi-sim.ini`.

Le fichier d'interface (`qtdragon_hd.ui`) est partage entre les deux : on edite
sur PC, on teste en simulation, puis on pousse sur git et on recupere sur le Pi.

Fichiers de simulation (PC uniquement) : `remora-flexi-sim.ini`,
`remora-flexi-sim.hal`, `postgui_call_list_sim.hal`, `qtdragon_hd_sim.hal`,
`custom_postgui_sim.hal`. Ils remplacent le composant Flexi-HAL (SPI) et le VFD
serie par des equivalents simules.

---

## Sorties auxiliaires (relais)

Quatre sorties AUX de la Flexi-HAL pilotent des relais 24V. Les trois
premieres sont commandables a la fois par le G-code (M64/M65) ET par des
boutons dans QtDragon, les deux sources etant combinees par des composants
`or2` (relais actif si bouton OU G-code). AUX3 fait exception : elle est
pilotee directement par `spindle.1.on` (interlock laser), sans or2.

| Sortie | Pin G-code            | Bouton        | Affectation        |
|--------|-----------------------|---------------|--------------------|
| AUX0   | motion.digital-out-00 | qtdragon.aux0 | Aspirateur         |
| AUX1   | motion.digital-out-01 | qtdragon.aux1 | Lumiere            |
| AUX2   | motion.digital-out-02 | qtdragon.aux2 | Ventilateurs broche |
| AUX3   | aucun (M3 $1 / M5 $1) | aucun         | Interlock laser     |

Le relais AUX3 est bien cable et actif : c'est lui qui alimente le +24V du
laser. Seul son pilotage par M64 P3 et par le bouton QtDragon aux3 a ete
retire, pour eviter un double pilotage de la meme pin (HAL refuserait de
charger). Voir AFFECTATION_AUX.md.

Cablage : modules relais en active HIGH (jumper sur H), alimentes via le bornier
AUX 2 fils (jumper P17 sur MAIN = 24V) avec un pont DC+ <-> IN sur chaque module.
Prerequis : `NUM_DIO = 4` dans la section `[EMCMOT]` de l'INI.

Flood/Mist : M8 (arrosage) et M7 (brouillard) cables sur les sorties dediees
COOLANT et MIST, M9 coupe les deux. La pompe a eau du circuit broche est sur
FLOOD (pas sur une AUX). AUX3 est pilotee directement par `spindle.1.on`
(interlock laser) : plus de M64 P3 ni de bouton. Detail : AFFECTATION_AUX.md.

---

## Nomenclature & Materiel (BOM)

### 1. Motorisation & Alimentation (OMC-StepperOnline)
* **Moteurs (X, Y1, Y2, Z) :** 4x Nema 23 boucle fermee (3.00 Nm / 424.83 oz.in),
  encodeur magnetique 1000 PPR (4000 CPR). Ref : `23HS40-5004-ME1K`
* **Drivers :** 4x pilotes boucle fermee V4.1 (0-8.0A, 24-48VDC). Ref : `CL57T-V41`
* **Cablage :** kit cables puissance + encodeur blindes AWG20, 4.7m. Ref : `CE5-M5-20`
* **Alimentations moteurs :** 350W 48V 7.3A (115/230V). Ref : `LE-350-48`

### 2. Broche, Laser & Refroidissement
* **Broche :** G-Penny 2.2kW ER20 refroidie par eau (80x230mm, 220V),
  4 roulements ceramiques serie 7, deviation max 0.01mm.
* **Variateur (VFD) :** HuangYang (HY) 2.2kW 220VAC.
* **Laser :** LaserTree LT-80W-AA-PRO (10W optique, 450 nm, 24V natif) sur
  glissiere amovible a l'avant du porte-broche (offset X +2 / Y -90 par
  rapport a l'axe broche). Pilote comme spindle.1 en PWM direct depuis la
  Flexi-HAL, interlock via relais AUX3 (voir section Laser).
* **Refroidissement :** pompe 220V 75W (max 3200 L/H), circuit ferme au liquide
  de refroidissement automobile (anti-oxydation / anti-algues).

### 3. Controle, Electronique & Securite
* **Calculateur :** Raspberry Pi executant LinuxCNC 2.9.8.
* **Carte d'interface :** Expatria Flexi-HAL (firmware Remora).
* **Puissance :** contacteur ABB AF09-30-10-11, bobine 24V.
* **Capteurs de limites (Homing) :** proximite inductifs NPN NC, alimentes 5V.
* **Palpage :** sonde mobile et/ou fixe (Tool Setter) via VersaProbe.

### 4. Structure Mecanique & Transmission
* **Chassis :** tubes acier rectangulaires 100x50mm ep. 4mm (masse et rigidite
  accrues vs recommandations standard du wiki).
* **Transmission X & Y :** vis a billes SFU1610 (pas 10mm) sur rails HGR20.
* **Transmission Z :** vis a billes SFU1204 (pas 4mm) pour contrer la gravite.

---

## Parametres de configuration cles (`.ini`)

* **Cinematique :** JOINTS = 4 (X, Y1, Z, Y2), Y en tandem (2 moteurs),
  `trivkins coordinates=XYZY`.
* **Broches :** SPINDLES = 2 dans `[TRAJ]` (broche VFD = spindle.0,
  laser = spindle.1), repris par `num_spindles` sur la ligne loadrt de
  motmod dans le HAL (aucun parametre motmod n'est implicite).
* **Resolution des pas (Scale) :**
  * X : `-160.0` (1600 pas/tour, vis 10mm, direction inversee)
  * Y1 : `160.0` / Y2 : `-160.0` (moteurs en miroir, tandem)
  * Z : `400.0` (1600 pas/tour, vis fine 4mm)
* **Limites de courses logicielles :**
  * X : `-50.0` a `1240.0` mm
  * Y : `-2.0` a `1286.0` mm (HOME a `1275.0`)
  * Z : `-185.0` a `5.0` mm (HOME de securite a `0.0`)
* **Vitesses maximales :**
  * X & Y : 166,67 mm/s (10 000 mm/min), STEPGEN_MAXVEL 200
  * Z : 33.33 mm/s (STEPGEN_MAXVEL 100, prudence face a la gravite)
* **Timings impulsions :** STEPLEN = STEPSPACE = 2500 ns sur **tous** les axes (voir encadre ci-dessous).
* **Homing :** Z monte en premier (sequence 0), puis X et Y ensemble (sequence -1).

---

## Changement d'outil

Script manuel `toolchange.ngc` via REMAP M6, avec palpeur fixe en G53 X-50 Y60.
Deux modes de zero Z (parametre `#1001`) :
* `#1001 = 0` : zero Z sur le martyre (automatique)
* `#1001 = 1` : zero Z sur le dessus de la piece (manuel)

Bouton "Reset Ref" dans QtDragon pour preparer un nouveau job.

### Cas particulier : outil laser (T100)

Les numeros d'outil >= 100 sont reserves aux lasers. Pour eux,
`toolchange.ngc` applique deux comportements specifiques :

* **Palpage decale :** la broche vise une position decalee de l'inverse de
  l'offset laser (nez laser = broche X +2 / Y -90) pour que le cone du
  laser touche la pastille du VersaProbe. Si la position calculee sort de
  la course machine, elle est plafonnee a X -49.5 : la pastille de 20 mm
  de diametre absorbe le decalage residuel sans fausser le Z.
* **Info reference :** si aucun outil n'a defini la reference de la
  session, `T100 M6` affiche un simple message : c'est le laser qui va la
  creer. Legitime pour un job 100% laser (la distance palpeur->martyre est
  mecanique, elle ne depend pas de l'outil). Pour un job MIXTE, palper une
  fraise d'abord.
  Note : ce message etait un `M1` a l'origine. Il s'enchainait avec le M1
  du montage d'outil et bloquait la reprise dans QtDragon -- meme famille
  de probleme que les blocs `IF ... M2 ... ENDIF` casse-preview. Rendu
  non bloquant le 17 juillet 2026.

En tete d'un G-code laser : `T100 M6` puis `G43 H100` (offsets X/Y saisis
une fois dans tool.tbl, offset Z palpe a chaque changement).

**Procedure operatoire complete : voir `WORKFLOW_LASER.md`** (workflows
pas a pas Mode Martyre / Mode Piece / job mixte, aide-memoire commandes,
pieges connus).

### Note : boutons de deplacement et vitesse elevee

Les boutons de l'interface qui declenchent un deplacement via CALL_MDI_WAIT
(ex : GO HOME) calculent un delai d'attente = distance / vitesse + marge.
Ce calcul ignore le temps d'acceleration/deceleration. A vitesse elevee
(10 000 mm/min), une marge trop courte fait expirer le WAIT avant la fin du
mouvement -> message "EMC_TASK_PLAN_PAUSE cannot be executed".
Corrige en portant `wait_buffer_secs` de 1 a 4 s dans la fonction
`calc_mdi_move_wait_time` du handler QtDragon.

---

## Laser (spindle.1)

Module **LaserTree LT-80W-AA-PRO** pilote comme deuxieme broche LinuxCNC.
Le S-word est une consigne de puissance 0-1000, pas une vitesse :
`M3 $1 S500` = 50%, `M5 $1` = arret, `S0` = eteint (sur les G0).

> Pour la mise en oeuvre pas a pas (quel mode, dans quel ordre, quand le
> nez touche quoi), voir **`WORKFLOW_LASER.md`**. La presente section
> documente le materiel et la config, pas la procedure.

* **Chaine de puissance (depuis le 17 juillet 2026) :** spindle.1 ->
  composant `laser_scale` (gain 0.1, offset 0) -> `flexi.SP.SPINDLE_PWM`
  -> optocoupleur U7 -> LM358 (U6) -> jumper P7 -> fil jaune du laser.
  **PWM direct, plus aucun convertisseur externe.**
* **Interlock :** relais AUX3 pilote par `spindle.1.on`, coupe le +24V du
  laser (fil rouge). Reste la coupure de reference du faisceau.
* **Focale :** **8.5 mm** entre le nez conique et le point focal (mesuree au
  test de traits, `test_focale_laser.ngc`). C'est le nez qui sert de
  reference au palpage, pas le focus : apres `T100 M6` + `G43 H100`, il
  faut donc travailler a `Z = 8.5` en Mode Piece, ou `Z = epaisseur + 8.5`
  en Mode Martyre. Valeur a reporter dans le post CAM (le generateur
  d'atelier laser sortait 4.0 par defaut : frottement du nez garanti).
* **Offsets T100 (tool.tbl) :** X = 2.0, Y = -90.0. Z palpe a chaque M6.
  NE PAS y mettre la focale : `toolchange.ngc` ecrase la colonne Z a
  chaque palpage (`G10 L1 P<n> Z<offset>`). Seuls X et Y survivent.

### Jumpers Flexi-HAL : P6 et P7 (CRITIQUE)

La carte offre deux modes de sortie spindle, selectionnes par jumpers
(serigraphie "SPINDLE PWM CONFIG" pres du bornier 24V) :

| Jumper | Reglage laser | Role |
|--------|---------------|------|
| **P6** | **5V** (PAS 12V) | Alimente le LM358 (U6 pin 8) via `SPINDLE_PWR_12V` |
| **P7** | **vertical** | Mode PWM : bypasse le filtre RC (horizontal = 0-10V) |

**NE JAMAIS mettre P6 sur 12V en mode PWM.** P6 fixe l'alimentation de
l'ampli op, donc l'amplitude du carre en sortie. Sur 12V, le PWM
swinguerait a ~10.5V droit dans l'entree TTL 5V du LaserTree. P6 sur 5V
est ce qui protege le laser.

### Niveaux mesures et limite du LM358

Mesures au multimetre (17 juillet 2026), `laser_scale` gain 0.1 offset 0,
P6 sur 5V, P7 vertical :

| S | duty | tension moyenne |
|------|------|--------|
| 0    | 0%   | 0.67 V (niveau bas statique) |
| 250  | 25%  | 1.37 V |
| 500  | 50%  | 2.08 V |
| 750  | 75%  | 2.73 V |
| 1000 | 100% | 3.44 V (niveau haut statique) |

Linearite parfaite (ecarts < 0.02V sur la droite 0.67 -> 3.44) : le
rapport cyclique est fidele. Aux deux extremes il n'y a aucune
commutation, donc ces valeurs sont les VRAIS niveaux logiques.

Le plafond a 3.44V n'est pas un defaut : le LM358 n'est pas rail-to-rail,
sa sortie haute plafonne a environ **V+ moins 1.5V**. Avec P6 sur 5V :
5 - 1.5 = 3.5V. Suffisant pour le seuil TTL du laser (~2.5V).

**Correction d'un diagnostic errone de juillet :** le plancher de ~0.73V
a S0 avait ete documente comme un "clampage firmware irrattrapable". Faux.
C'etait la limite basse de sortie du LM358. Preuve : en passant P6 de 12V
a 5V, le plafond suit V+ (10.43 -> 3.44) mais le plancher ne bouge quasi
pas (0.73 -> 0.67). Signature typique du LM358 (`V_OH = V+ - 1.5V`,
`V_OL` independant de V+). Aucun gain/offset HAL n'aurait pu le corriger.

Et en PWM ce plancher n'est plus un probleme : sur la chaine 0-10V,
0.73V etait une vraie consigne analogique (~7% de puissance, le laser
emettait a S0). En PWM, 0.67V est un niveau logique bas que l'entree TTL
lit comme "eteint".

### Historique : deux convertisseurs grilles

Avant la bascule en PWM direct, la chaine passait par un module externe
0-10V vers PWM. Deux exemplaires ont grille (juin, puis 16 juillet), le
second au niveau d'une broche du microcontroleur Nuvoton, a la mise sous
tension, avec seuls l'alim 24V (mesuree correcte, meme alim que la
Flexi-HAL) et le fil jaune connectes.

**Cause probable : un defaut du module, pas le cablage.** D'autres
acheteurs rapportent la meme panne, et un commentaire documente un
court-circuit visible sur le PCB en zoomant. Non verifie de nos yeux,
mais coherent avec les faits observes : deux morts instantanees a la
mise sous tension, avec deux schemas d'alimentation DIFFERENTS (via
relais AUX3 pour le premier, 24V direct pour le second). Un defaut de
cablage aurait du changer avec le cablage ; la panne, elle, n'a pas
bouge.

A noter : la consigne "ne jamais passer le VCC du module par le relais",
tiree du premier incident, reposait donc sur une fausse piste. Elle reste
une bonne pratique, mais ce n'est probablement pas ce qui a tue le
module 1.

L'architecture PWM directe supprime le maillon fragile : c'est la vraie
correction.

### Piege multi-broche : attente "spindle at speed"

Symptome : un job laser seul (spindle.1 uniquement) gele au premier G1,
laser allume, aucun message d'erreur. Cause : apres un demarrage ou un
changement de vitesse de broche, le planificateur attend
`spindle.0.at-speed` meme si seule spindle.1 a ete commandee, et `hy_vfd`
rapporte FALSE tant que le VFD est a l'arret. Correctif
(remora-flexi.hal, juillet 2026) :

    spindle.0.at-speed = (VFD a vitesse) OU (broche 0 arretee)

via les composants `atspeed_or` + `s0_on_not`. La securite fraisage est
conservee : broche 0 commandee mais pas encore a vitesse -> LinuxCNC
attend toujours le spin-up du VFD avant le premier mouvement d'avance.

### Securite laser

Une pause programme (feed hold, M1) ne coupe PAS les broches : un job
laser en pause continue d'emettre au point fixe (risque d'inflammation
sur bois). Ne jamais laisser une gravure laser sans surveillance.

Seul `M5 $1` ouvre le relais AUX3 et coupe reellement le faisceau. Un
`S0 $1` met la puissance a zero mais laisse le laser arme.

---

## A propos des timings d'impulsion (STEPLEN / STEPSPACE)

Pour faire avancer un moteur d'un pas, LinuxCNC envoie une impulsion electrique
au driver. Deux parametres, exprimes en nanosecondes, en definissent le rythme :

* **STEPLEN** : duree pendant laquelle l'impulsion reste "haute" (le pas lui-meme).
  2500 ns = 2,5 microsecondes.
* **STEPSPACE** : temps de repos minimum "bas" entre deux impulsions consecutives.

Analogie : un metronome ou STEPLEN est la duree du "tic" et STEPSPACE le silence
minimum avant le "tic" suivant.

**Pourquoi c'est important :** chaque driver a besoin d'un temps minimum pour
lire et traiter l'impulsion. Trop courtes ou trop rapprochees -> le driver rate
des pas (positions fausses, bruits, vibrations). Trop larges -> on bride
inutilement la vitesse maximale.

**Pourquoi 2500 ns :** c'est une valeur sure et confortable pour les drivers
CL57T, assez large pour une lecture fiable sans limiter les vitesses a cet usage.

**Pourquoi identique sur tous les axes :** les 4 moteurs sont des CL57T
identiques, donc memes besoins. C'est particulierement vrai pour Y1/Y2 qui
forment un portique en tandem et doivent reagir de facon parfaitement synchrone.

Note historique : le moteur Y2 (JOINT_3) avait ete regle a 5000 ns lors de la
recherche d'un bruit moteur. Le vrai coupable etait un mauvais reglage des DIP
switches du driver, pas les timings -> tous les axes sont desormais harmonises
a 2500 ns.
