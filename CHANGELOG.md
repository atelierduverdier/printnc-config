# Changelog — 16-17 juillet 2026 — Integration laser : outil T100, PWM direct, at-speed multi-broche
## PrintNC Flexi-HAL — Atelier du Verdier

Machine : PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd

---

## 1. Objectif

Rendre le laser (LaserTree LT-80W-AA-PRO, spindle.1) utilisable comme un outil
ordinaire : palpage automatique, offsets, et lancement d'un G-code laser sans
manipulation particuliere. Trois problemes distincts se sont enchaines.

## 2. Le laser devient l'outil T100

Le laser est monte sur une glissiere amovible a l'avant du porte-broche, decale
de **X +2 / Y -90** par rapport a l'axe de la broche. Son nez conique peut
palper le VersaProbe comme une fraise : pas besoin de mecanisme separe.

Convention : **tout outil numerote >= 100 est un laser**.

`tool.tbl`, ligne T100 : X = 2.0, Y = -90.0, Z = 0 (recalcule a chaque palpage).
Le script ne fait que `G10 L1 P<n> Z<offset>` : les colonnes X/Y saisies a la
main ne sont jamais ecrasees.

En tete d'un G-code laser : `T100 M6` puis `G43 H100`.

### 2.1 Palpage decale (toolchange.ngc)

Sans correction, `G53 G0 X-50 Y60` amene l'AXE BROCHE au-dessus du palpeur :
c'est la fraise en place qui touche, pas le laser. Pour les outils >= 100, la
cible est decalee de l'INVERSE de l'offset laser :

```gcode
#<laser_x_offset> =   2.0
#<laser_y_offset> = -90.0

#<eff_probe_x> = #<probe_x>
#<eff_probe_y> = #<probe_y>
O130 IF [#<tool_num> GE 100]
    #<eff_probe_x> = [#<probe_x> - #<laser_x_offset>]
    #<eff_probe_y> = [#<probe_y> - #<laser_y_offset>]
    O135 IF [#<eff_probe_x> LT -49.5]
        #<eff_probe_x> = -49.5
    O135 ENDIF
O130 ENDIF
```

Le clamp a -49.5 est necessaire : le palpeur est au ras de la limite X (-50.0,
= HOME_OFFSET de JOINT_0), donc -50 - 2 = -52 est hors course et LinuxCNC
refuse le mouvement ("would exceed X's negative limit"). La pastille faisant
20 mm de diametre (rayon 10 mm), toucher a 2.5 mm du centre ne fausse rien.

Le clamp est A L'INTERIEUR de la branche laser : place a l'exterieur, il
s'appliquait aussi aux fraises et polluait chaque changement d'outil.

### 2.2 Garde-fou de reference : d'abord M1, puis MSG

Premiere version : si aucune reference n'existait (`#1000 EQ 0`) et que l'outil
etait un laser, message + `M1`. **Mauvaise idee, retiree le 17 juillet.**

Deux raisons :
- Ce `M1` s'enchainait avec celui du montage d'outil et bloquait la reprise
  dans QtDragon (bouton pause allume, aucun effet). Meme famille de probleme
  que les blocs `IF ... M2 ... ENDIF` casse-preview deja signales en tete du
  script. Symptome caracteristique : ca passait si on palpait une fraise avant.
- Sur le fond, il protegeait d'un faux danger. La distance palpeur->martyre est
  MECANIQUE (`#<dist_palpeur_table>` = 50.525) : elle ne depend pas de quel
  outil touche. Un job 100% laser peut donc legitimement definir le zero seul.

Devenu un simple `(MSG, ...)` informatif, non bloquant.

## 3. CAUSE RACINE : gel au premier G1 des jobs laser

Symptome : le laser va en position (G0 OK), s'allume, puis **plus rien ne bouge**.
Aucun message d'erreur. Un fichier de fraisage passait sans probleme.

Fausses pistes eliminees en cours de route (toutes verifiees par `halcmd`) :
`spindle.1.at-speed` (TRUE, non connecte), bouton FEED_HOLD physique
(`halui.program.is-paused` = FALSE), feed override (= 1).

Diagnostic reel : **l'attente "spindle at speed" du planificateur de trajectoire
n'est pas cloisonnee par numero de broche.** Apres un demarrage ou un changement
de vitesse, motion attend `spindle.0.at-speed` AVANT le premier mouvement en
avance travail (les G0 ne sont pas concernes) -- meme si seule spindle.1 a ete
commandee par `M3 $1`. Or `hy_vfd` rapporte FALSE tant que le VFD est a l'arret.
Un job laser seul attendait donc un evenement qui n'arriverait jamais.

Confirmation a chaud, pendant un gel :

```bash
halcmd unlinkp spindle.0.at-speed
halcmd setp spindle.0.at-speed 1
# -> le mouvement repart instantanement
```

### Correctif (remora-flexi.hal)

`spindle.0.at-speed` = (VFD a vitesse) OU (broche 0 arretee) :

```hal
loadrt not names=...,s0_on_not
loadrt or2 names=...,atspeed_or
addf s0_on_not servo-thread
addf atspeed_or servo-thread

net spindle-at-speed vfd.spindle-at-speed => atspeed_or.in0
net spindle-on => s0_on_not.in
net s0-off s0_on_not.out => atspeed_or.in1
net s0-at-speed atspeed_or.out => spindle.0.at-speed
```

La securite fraisage est conservee : broche 0 commandee mais pas encore a
vitesse -> FALSE -> LinuxCNC attend toujours le spin-up du VFD avant de plonger.
Verification au repos : `halcmd getp spindle.0.at-speed` doit valoir TRUE.

## 4. Bascule en PWM direct (suppression du convertisseur)

La chaine passait par un module externe 0-10V vers PWM. **Deux exemplaires ont
grille** (juin, puis 16 juillet). Le second est mort a la mise sous tension,
broche du microcontroleur Nuvoton brulee, avec seuls l'alim 24V (bonne polarite,
meme alim que la Flexi) et le fil jaune connectes. Cause exacte jamais
formellement etablie.

Decision : **supprimer le maillon fragile** plutot que d'en racheter un
troisieme. La Flexi-HAL sait sortir du PWM nativement.

### 4.1 Jumpers (serigraphie "SPINDLE PWM CONFIG")

| Jumper | Reglage laser | Role |
|--------|---------------|------|
| P6 | **5V** | Alimente le LM358 (U6 pin 8) via le net `SPINDLE_PWR_12V` |
| P7 | **vertical** | Mode PWM : bypasse le filtre RC (horizontal = 0-10V) |

**NE JAMAIS mettre P6 sur 12V en mode PWM.** P6 ne choisit pas un "niveau de
signal" : il fixe l'alimentation de l'ampli op, donc l'amplitude du carre en
sortie. Sur 12V le PWM swinguerait a ~10.5V droit dans l'entree TTL 5V du laser.

Point cle du schema (page 5, FLEXI_HAL_2000) : **P7 ne bypasse pas l'ampli op,
seulement le filtre RC**. Le signal traverse le LM358 dans les deux modes :

```
SPINDLE_PWM -> R9 -> optocoupleur U7 -> R12 (pull-up vers le rail P6)
            -> LM358 U6A -> P7 -> [filtre RC U6B/R32/C2  ou  bypass] -> sortie
```

### 4.2 laser_scale simplifie

`flexi.SP.SPINDLE_PWM` attend un rapport cyclique en pourcent :

```hal
setp laser_scale.gain   0.1     # duty = S / 10
setp laser_scale.offset 0
```

L'ancien `gain 0.102 / offset -6` compensait le plancher de la chaine
analogique. Il n'a plus aucune raison d'etre.

### 4.3 Mesures de validation (17 juillet)

| S | duty | tension |
|------|------|---------|
| 0    | 0%   | 0.67 V (niveau bas statique) |
| 250  | 25%  | 1.37 V |
| 500  | 50%  | 2.08 V |
| 750  | 75%  | 2.73 V |
| 1000 | 100% | 3.44 V (niveau haut statique) |

Linearite parfaite (ecarts < 0.02V). A 0% et 100% il n'y a aucune commutation :
ces valeurs sont les VRAIS niveaux logiques, pas des moyennes. Un oscilloscope
n'a donc pas ete necessaire.

## 5. Correction d'un diagnostic errone du 10 juillet

Le bloc de calibration de `laser_scale` documentait le plancher de ~0.73V a S0
comme un **"clampage firmware irrattrapable"**. C'etait faux.

C'est la limite basse de sortie du **LM358**. Preuve : en passant P6 de 12V a
5V, le plafond suit V+ (10.43 -> 3.44V) mais le plancher ne bouge quasiment pas
(0.73 -> 0.67V). Signature typique du LM358, qui n'est pas rail-to-rail :
`V_OH = V+ - 1.5V` (5 - 1.5 = 3.5V, mesure 3.44), `V_OL` independant de V+.
Aucun gain/offset HAL n'aurait jamais pu le corriger.

**Consequence heureuse** : en PWM, ce plancher n'est plus un probleme. Sur la
chaine 0-10V, 0.73V etait une vraie consigne analogique (~7% de puissance : le
laser emettait a S0). En PWM, 0.67V est un niveau logique bas que l'entree TTL
lit comme "eteint". AUX3 reste malgre tout la coupure de reference.

## 6. Autres corrections

- **README.md** : le tableau AUX indiquait AUX2 = pompe a eau. Corrige en
  ventilateurs broche (la pompe est sur FLOOD), conformement a AFFECTATION_AUX.md.
- **Origine piece et courses** : un job dont le parcours s'etend de X-243 a
  X+243 autour du zero exige une origine a X machine >= +193.5 (limite X a -50).
  Sinon "would exceed X's negative limit" en pleine passe.

## 7. Fichiers touches

- `toolchange.ngc` : offsets laser, palpage decale, clamp X, garde-fou -> MSG
- `remora-flexi.hal` : `atspeed_or` + `s0_on_not`, section LASER reecrite,
  `laser_scale` gain 0.1 / offset 0
- `remora-flexi.ini` : en-tete [SPINDLE_1] (jumpers, PWM direct, T100)
- `README.md`, `AFFECTATION_AUX.md` : section Laser, tableau AUX, BOM
- `tool.tbl` : ligne T100 (X 2.0, Y -90.0)

## 8. Reste a faire

- Determiner proprement la distance focale (valeur de travail : `#<z_focus> = 7`).
- Verifier la reponse en puissance par une bande de test S100->S1000 : lignes
  separees a S constant (un `G1` unique par ligne), pas une bande continue --
  avec G64 le planificateur fusionne les segments colinearies et les changements
  de S ne tombent plus forcement aux frontieres. Pour de la vraie gravure
  modulee, la voie propre est `M67 E0 Q<valeur>` (sortie synchronisee).
- Surveiller le niveau bas a 0.67V : le seuil V_IL typique est vers 0.8V, la
  marge est correcte mais pas confortable. Si un residu marque a S0, prevoir un
  pull-down cote laser.

---

# Changelog — 24 juin 2026 — Bouton CAM VERS OUTIL (decalage camera/broche)
## PrintNC Flexi-HAL — Atelier du Verdier

**Machine :** PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd

---

## 1. Objectif

Ajouter un bouton "CAM VERS OUTIL" amenant la camera a la place de la fraise
(decalage relatif de l'offset camera/broche), pour pointer un repere a l'ecran
puis poser le zero piece via le bouton REF CAMERA.

Workflow retenu :
1. Positionner la fraise sur le point vise (position quelconque, ex. X240 Y500).
2. Clic CAM VERS OUTIL -> decalage relatif G91 G0 X[-cam_x] Y[-cam_y] : la camera
   vient au-dessus du point que la fraise visait.
3. Ajustement fin au jog en regardant l'image camera.
4. Clic REF CAMERA -> G10 L20 P0 avec les offsets camera : pose du zero piece.

Avantage : le decalage et la compensation REF CAMERA lisent les MEMES champs
(lineEdit_camera_x / lineEdit_camera_y), donc coherents par construction. Plus
besoin de passer par X0 Y0 comme avant.

## 2. CAUSE RACINE du bug (RESOLU)

Symptome : en MDI manuel, "G91 G0 X-76 Y-85" fonctionne et va direct en 2 s.
Lance depuis le bouton, la fraise traversait toute la table vers l'origine.
Le handler Python etait pourtant correct (le status bar affichait bien la bonne
commande "MDI envoye : G91 G0 X-10 Y-10").

Diagnostic : le bouton btn_camera_to_tool avait ete cree dans Designer en
REUTILISANT un bouton existant, qui conservait sa connexion d'origine dans le
.ui vers le slot btn_goto_location_clicked(). Cette methode fait un
"G53 G0 Z0" puis un "G53 G0 X.. Y.." en coordonnees MACHINE.

Resultat : a chaque clic, DEUX actions partaient en parallele :
  - la connexion Python ajoutee a la main (bon deplacement relatif G91)
  - la connexion parasite du .ui (G53 absolu machine -> traversee vers origine)
En MDI manuel ce parasite n'existe pas, d'ou la difference de comportement.

Localisation du parasite (grep sur le .ui) :
    <sender>btn_camera_to_tool</sender>
    <signal>clicked()</signal>
    <receiver>MainWindow</receiver>
    <slot>btn_goto_location_clicked()</slot>

## 3. Correction

Suppression du bloc <connection> parasite dans le .ui (le bouton ne garde que
la connexion Python definie dans initialized__).

```bash
# sauvegarde + suppression du bloc <connection> de btn_camera_to_tool
sed -i.bak '17579,17594d' qtvcp/screens/qtdragon_hd/qtdragon_hd.ui
# verification : ne doit rester que la definition du widget
grep -n "btn_camera_to_tool" qtvcp/screens/qtdragon_hd/qtdragon_hd.ui
#   -> une seule ligne : <widget class="QPushButton" name="btn_camera_to_tool">
```

Connexion conservee dans le handler (initialized__) :
```python
if hasattr(self.w, 'btn_camera_to_tool'):
    self.w.btn_camera_to_tool.clicked.connect(self.btn_camera_to_tool_clicked)
```

Methode finale (qtdragon_hd_handler.py) :
```python
def btn_camera_to_tool_clicked(self):
    if not STATUS.is_all_homed():
        self.add_status("Machine non referencee (homing requis)", WARNING)
        return
    try:
        cam_x = float(self.w.lineEdit_camera_x.text())
        cam_y = float(self.w.lineEdit_camera_y.text())
    except ValueError:
        self.add_status("Erreur : valeurs d'offset camera invalides", WARNING)
        return
    if cam_x == 0 and cam_y == 0:
        self.add_status("Offset camera = 0,0 : verifier les champs", WARNING)
        return

    cmd = "G91 G0 X{:.3f} Y{:.3f}".format(-cam_x, -cam_y)
    self.add_status("MDI envoye : " + cmd)
    ACTION.SET_MDI_MODE()
    ACTION.CALL_MDI_WAIT(cmd, 30)
    ACTION.CALL_MDI_WAIT("G90", 5)
```

## 4. Lecons

- Reutiliser un bouton dans Designer conserve ses connexions signal/slot du .ui,
  invisibles cote handler. Toujours verifier dans Designer (F4, Edit Signals/Slots)
  ou par grep sur le .ui, et supprimer l'ancienne connexion avant d'en cabler une
  nouvelle (ou tout gerer cote Python en laissant le bouton non connecte dans le .ui).
- Quand un widget reagit "en double" alors que le Python semble correct, le
  diagnostic est dans le .ui, pas dans le handler.
- cam_to_tool.ngc (sous-programme externe) abandonne : tout passe par le handler,
  fichier supprime.

## 5. A faire ensuite

- [ ] Confirmer le SENS du decalage sur plusieurs reperes (signes de cam_x/cam_y).
- [ ] Renommer eventuellement la methode / le label si la fonction evolue.
- [ ] Ajouter *.bak au .gitignore pour ne pas suivre les sauvegardes.

---
# Changelog — 16 juin 2026 — Refroidissement broche (pompe + ventilateurs)
## PrintNC Flexi-HAL — Atelier du Verdier

Machine : PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd

---

## 1. Pompe et ventilateurs lies, avec post-refroidissement

La pompe a eau (sortie FLOOD / COOLANT, M8) et les ventilateurs (AUX2) sont
desormais pilotes ensemble par un signal commun "cooling-active". Objectif :
refroidir la broche pendant l'usinage ET continuer un moment apres, pour
evacuer la chaleur residuelle et menager la broche.

Comportement obtenu :
- M3 (broche ON) ou M8 -> pompe + ventilateurs demarrent immediatement.
- M5 (broche OFF) ou M9 -> pompe + ventilateurs restent actifs encore 30 s,
  puis s'arretent ensemble (post-refroidissement).
- Bouton AUX2 et M64 P2 / M65 P2 -> commande manuelle des ventilateurs (inchange).

## 2. Composants HAL ajoutes

remora-flexi.hal :
- 2 or2 supplementaires (cool_or1, cool_or2) et 1 timedelay (spindle_cooldown)
  ajoutes aux lignes loadrt / addf.
- timedelay configure : on-delay 0 (demarrage immediat), off-delay 30
  (post-refroidissement de 30 s, ajustable).
- La sortie FLOOD n'est plus pilotee directement par iocontrol.0.coolant-flood :
  elle passe par cool_or1 = (M8) OU (cooldown broche). Le signal resultant
  "cooling-active" pilote flexi.output.COOLANT.

```hal
loadrt or2 names=aux0_or,aux1_or,aux2_or,aux3_or,cool_or1,cool_or2
loadrt timedelay names=spindle_cooldown
addf cool_or1 servo-thread
addf cool_or2 servo-thread
addf spindle_cooldown servo-thread

setp spindle_cooldown.on-delay 0
setp spindle_cooldown.off-delay 30
net spindle-on => spindle_cooldown.in

# FLOOD = M8 OU post-refroidissement broche
net coolant-m8 iocontrol.0.coolant-flood => cool_or1.in0
net spindle-cooldown spindle_cooldown.out => cool_or1.in1
net cooling-active cool_or1.out => flexi.output.COOLANT
```

custom_postgui.hal :
- AUX2 (ventilateurs) passe par cool_or2 = (bouton OU M64 P2) OU cooling-active.
  Ainsi les ventilateurs suivent exactement la pompe.

```hal
# AUX2 (ventilateurs) = (bouton OU M64) OU refroidissement actif
net aux2-or-out aux2_or.out => cool_or2.in0
net cooling-active => cool_or2.in1
net aux2-out cool_or2.out => flexi.output.AUX2
```

## 3. Reglage du delai

Le post-refroidissement se regle avec une seule ligne dans remora-flexi.hal :
`setp spindle_cooldown.off-delay 30` (valeur en secondes).

## 4. Correction affectation AUX

Le document AFFECTATION_AUX.md indiquait AUX2 = pompe a eau. Correction : AUX2
= ventilateurs broche. La pompe a eau est sur la sortie FLOOD (COOLANT), pas
sur une AUX.

---



## 1. Environnement de developpement PC + simulation

Mise en place d'un PC de developpement (x86_64, Debian) en complement du
Raspberry Pi de production, synchronises par git.

- Config de simulation creee pour travailler l'interface sans le materiel :
  remora-flexi-sim.ini / .hal, postgui_call_list_sim.hal, qtdragon_hd_sim.hal,
  custom_postgui_sim.hal. Remplace le composant flexi (SPI) et le VFD serie
  par des equivalents simules (joints boucles cmd->fb, broche simulee).
- Lancement : linuxcnc ~/linuxcnc/configs/flexi-hal/remora-flexi-sim.ini
- Affichage fenetre (pas plein ecran) : retirer l'option -f de la ligne
  DISPLAY (c'etait -f = fullscreen qui forcait le plein ecran).

## 2. Qt Designer sur PC (x86_64)

- Paquet : qttools5-dev-tools (binaire "designer").
- Le script setup_designer fonctionne sur x86_64 (contrairement au Pi aarch64
  ou il echoue a cause d'un chemin x86_64 code en dur).
- Alias PC (~/.bashrc) : memes variables que le Pi mais avec
  x86_64-linux-gnu au lieu de aarch64-linux-gnu.

## 3. Boutons lanceurs d'applications

Ajout dans le handler de 4 fonctions lancant des applications externes sans
bloquer l'interface (subprocess.Popen) : terminal (xfce4-terminal en priorite),
geany, navigateur (xdg-open), explorateur de fichiers. Connexions defensives
(hasattr) : actives seulement si le bouton existe dans le .ui.
objectName attendus : btn_terminal, btn_geany, btn_navigateur, btn_fichiers.

## 4. Timings d'impulsion harmonises

Le moteur Y2 (JOINT_3) etait regle a STEPLEN/STEPSPACE = 5000 (reste d'un test
sur un bruit moteur dont la vraie cause etait les DIP switches du driver).
Harmonise a 2500 sur tous les axes -> son nettement meilleur.

## 5. Augmentation vitesse X/Y : 6000 -> 10000 mm/min

Passage de MAX_VELOCITY 100 -> 166,67 mm/s (10 000 mm/min) sur X, Y1, Y2.
Modifications dans : [AXIS_X], [JOINT_0], [AXIS_Y], [JOINT_1], [JOINT_3]
(MAX_VELOCITY + STEPGEN_MAXVEL 86 -> 200), [DISPLAY] et [TRAJ]
(MAX_LINEAR_VELOCITY -> 166,67). Z inchange (33,33).

Latence du Pi verifiee avec latency-test : excellente (max jitter servo
~28 us, base ~24 us) -> le Pi a la marge pour cette vitesse.

Facteur limitant theorique a surveiller pour aller plus haut : vitesse critique
de fouettement des vis SFU1610 sur ~1,3 m (a 10 000 mm/min, ~1000 tr/min).

VALIDATION : test de perte de pas effectue a 10 000 mm/min -> aucune perte de
pas. Vitesse fiable et adoptee pour l'usage courant.

## 6. Bug bouton GO HOME a haute vitesse (RESOLU)

Symptome : a 10 000 mm/min, en fin de deplacement GO HOME, message
"command (EMC_TASK_PLAN_PAUSE) cannot be executed until the machine is out of
E-stop and turned on". N'apparaissait pas a 6000.

Diagnostic : le bouton btn_go_home (handler, fonction btn_go_home_clicked)
utilise ACTION.CALL_MDI_WAIT avec un delai calcule par calc_mdi_move_wait_time :
delai = distance / vitesse + marge. Ce calcul ignore le temps d'acceleration
et de deceleration. A haute vitesse, ce temps devient proportionnellement
important ; avec une marge de seulement 1 s, le WAIT expirait avant la fin
reelle du mouvement (CALL_MDI_WAIT timeout surpassed 5 seconds), cassant la
sequence et declenchant le message.

Correction : wait_buffer_secs porte de 1 a 4 dans calc_mdi_move_wait_time.
Resultat : message disparu, GO HOME fonctionne a 10 000 mm/min.

Localisation precise de la correction :
- Fichier : qtvcp/screens/qtdragon_hd/qtdragon_hd_handler.py
- Fonction modifiee : calc_mdi_move_wait_time (def vers ligne 1606)
    avant : def calc_mdi_move_wait_time(self, dest_x, dest_y, wait_buffer_secs=1)
    apres  : def calc_mdi_move_wait_time(self, dest_x, dest_y, wait_buffer_secs=4)
- Fonction appelante : btn_go_home_clicked (CALL_MDI_WAIT vers lignes 888-891)
Note : les numeros de ligne sont indicatifs (le meme fichier contient aussi
les boutons lanceurs d'applications ajoutes le meme jour, ce qui peut decaler
la numerotation).

## 6bis. Widget web (QtWebEngine) supprime — erreurs page_allocator (RESOLU)

Symptome : au demarrage, terminal affichant deux lignes
"[...FATAL:page_allocator_internals_posix.h] Check failed: Invalid argument (22)"
suivies d'un gel de la boucle (task: main loop took ~0.18 s).

Diagnostic : la page HTML de l'onglet SETUP de QtDragon utilise un widget
QtWebEngine (moteur Chromium) qui plante au demarrage sur ce systeme. Page non
utilisee.

Correction :
- Widget web_view supprime dans Qt Designer (onglet HTML du SETUP ; les onglets
  PDF et PROPERTIES sont conserves).
- Handler protege : le bloc d'init du web_view est conditionne par
  hasattr(self.w,'web_view') and hasattr(self.w,'layout_HTML'), sinon exception
  "VCPWindow object has no attribute layout_HTML" + gel au demarrage.
Resultat : plus d'erreur page_allocator, plus de gel, demarrage propre.

## 6ter. Message EMC_TASK_PLAN_PAUSE au demarrage (RESOLU)

Symptome : popup "command (EMC_TASK_PLAN_PAUSE) cannot be executed until the
machine is out of E-stop and turned on" apres deverrouillage E-stop. Present
"depuis toujours", independant des modifs du jour.

Diagnostic : la carte lit ses entrees en logique active basse
(flexi.input.FEED_HOLD = TRUE au repos). La logique Hold du HAL utilisait
FEED_HOLD directement -> halui.program.pause force a TRUE en permanence ->
pause demandee au demarrage alors que la machine n'est pas prete.
Verifie : halcmd show pin halui.program.pause = TRUE.

Correction (remora-flexi.hal, bloc "Hold logic") :
    avant : net hold_button flexi.input.FEED_HOLD     => hold_button_toggle.in
    apres  : net hold_button flexi.input.FEED_HOLD.not => hold_button_toggle.in
FEED_HOLD.not est FALSE au repos -> plus de pause parasite. Coherent avec
CYCLE_START qui utilisait deja .not. Apres correction :
halui.program.pause = FALSE, message disparu.

Sujet connexe NON resolu : la telecommande 3 boutons (RJ45)
CYCLE_START / HOLD / HALT ne repond physiquement que sur HALT ; CYCLE_START et
HOLD ne changent pas d'etat a l'appui. Probleme de cablage / brochage RJ45 a
traiter separement.

## 7. Maintenance git

- .gitignore ajoute (linuxcnc.var, qtdragon.pref, *.halscope, 0_tmp, etc.).
- Fichier temporaire 0_tmp (genere par NGCGUI) a retirer du suivi
  (git rm --cached) car ajoute avant le .gitignore.
- Script push-config (dans ~/bin, hors depot) : add + commit avec message
  demande + push.
- Authentification GitHub : mot de passe non supporte, utiliser un token
  d'acces personnel (ou cle SSH).

---

## A faire ensuite

- [x] Test de perte de pas a 10 000 : VALIDE, aucune perte de pas. Vitesse
      adoptee pour l'usage courant.
- [ ] Eventuellement tenter 12 000 mm/min par paliers, en surveillant le
      fouettement des vis SFU1610 (~1200 tr/min a 12 000).
- [ ] Travailler MAX_ACCELERATION (actuellement 200) si l'accel est le facteur
      limitant ressenti sur trajets courts.
- [ ] Telecommande 3 boutons (RJ45) : faire fonctionner CYCLE_START et HOLD
      (seul HALT repond) — cablage / brochage a verifier.
- [ ] Retirer 0_tmp du suivi git.
- [ ] Projet de documentation complete de la machine (a partir des reels
      Instagram, export JSON).

---

# Changelog — 7 juin 2026 — Interface QtDragon : boutons AUX

**Machine :** PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd
**Plateforme :** Raspberry Pi (aarch64) sous Debian 12 (bookworm)

> Suite du changelog du 6 juin (cablage relais, alimentation rail AUX, jumper
> P17, mesures). Le materiel et le principe M64/M65 n'y sont pas repris ici :
> voir l'entree precedente. Ce document couvre uniquement l'ajout des boutons
> dans l'interface et la logique bouton + G-code.

---

## 1. Logique bouton OU G-code (or2)

Chaque sortie AUX est desormais pilotee par un or2 : relais actif si le bouton
OU le G-code le demande.

    bouton (qtdragon.auxN) ─┐
                            ├─► auxN_or ─► flexi.output.AUXN
    M64/M65 (digital-out-N) ┘

### remora-flexi.hal (HAL principal)

```hal
loadrt or2 names=aux0_or,aux1_or,aux2_or,aux3_or
addf aux0_or servo-thread
addf aux1_or servo-thread
addf aux2_or servo-thread
addf aux3_or servo-thread
```

```hal
# Entree G-code (M64/M65) vers les or2
	net aux0-gcode motion.digital-out-00 => aux0_or.in0
	net aux1-gcode motion.digital-out-01 => aux1_or.in0
	net aux2-gcode motion.digital-out-02 => aux2_or.in0
	net aux3-gcode motion.digital-out-03 => aux3_or.in0
```

### custom_postgui.hal (charge APRES le GUI)

Les pins des boutons n'existent qu'apres chargement du GUI : ce bloc doit etre
dans le postgui, jamais dans le HAL principal.

```hal
# Boutons AUX (PushButton HAL QtDragon) vers les or2
	net aux0-btn qtdragon.aux0 => aux0_or.in1
	net aux1-btn qtdragon.aux1 => aux1_or.in1
	net aux2-btn qtdragon.aux2 => aux2_or.in1
	net aux3-btn qtdragon.aux3 => aux3_or.in1

# Sortie combinee (bouton OU G-code) vers les relais
	net aux0-out aux0_or.out => flexi.output.AUX0
	net aux1-out aux1_or.out => flexi.output.AUX1
	net aux2-out aux2_or.out => flexi.output.AUX2
	net aux3-out aux3_or.out => flexi.output.AUX3
```

IMPORTANT : le prefixe reel des pins de boutons est "qtdragon" (et NON "qtvcp").
Toujours confirmer avec :  halcmd show pin | grep -i aux

---

## 2. Creation des boutons dans QtDragon_hd

### Copier l'ecran (ne jamais modifier l'ecran systeme)

`qtvcp copy` -> destination : /home/expatria/linuxcnc/configs/flexi-hal
Cree .../flexi-hal/qtvcp/screens/qtdragon_hd/ (.ui, handler, qss, resources).
LinuxCNC charge en priorite cette copie locale plutot que /usr/share/...

### Boutons

- Widget : PushButton de la categorie "linuxcnc - hal" (PAS le PushButton Qt
  standard ni la checkbox).
- Par bouton : objectName = aux0..aux3, checkable coche, text au choix.
- Le PushButton HAL cree automatiquement la pin qtdragon.<objectName>.
- Popup .qrc manquant a l'ouverture -> repondre No (sans incidence).
- Placement valide : page Utility (TabWidget interne). Eviter le StackedWidget
  principal.

---

## 3. Lancer Qt Designer avec les widgets LinuxCNC (specifique ARM64)

Le script officiel `setup_designer` echoue sur Pi : il cherche libpyqt5.so dans
un chemin x86_64 code en dur, alors que le fichier est en aarch64. Contournement
par variables d'environnement :

```bash
cd ~/linuxcnc/configs/flexi-hal/qtvcp/screens/qtdragon_hd/
export PYQT5_DESIGNERPATH=/usr/lib/python3/dist-packages/qtvcp/plugins
export QT_PLUGIN_PATH=/usr/lib/aarch64-linux-gnu/qt5/plugins
designer qtdragon_hd.ui
```

Sur ce systeme le binaire est `designer` (pas `designer-qt5`). Paquet requis :
qttools5-dev-tools (deja installe).

Alias pratique (~/.bashrc) :

```bash
alias qtdesigner='PYQT5_DESIGNERPATH=/usr/lib/python3/dist-packages/qtvcp/plugins QT_PLUGIN_PATH=/usr/lib/aarch64-linux-gnu/qt5/plugins designer ~/linuxcnc/configs/flexi-hal/qtvcp/screens/qtdragon_hd/qtdragon_hd.ui'
```

---

## 4. Incident rencontre

Erreur au demarrage : "Pin 'qtdragon.aux0' does not exist".
Cause : les boutons aux0/aux1 perdus pendant des manipulations de placement
dans Designer ; leurs pins n'etaient plus creees.

Procedure de secours :
1. Commenter les lignes `aux?-btn` du custom_postgui.hal pour permettre le
   demarrage (le G-code M64/M65 continue de fonctionner).
2. Recreer les boutons manquants dans Designer (objectName + checkable).
3. Verifier : halcmd show pin | grep qtdragon.aux  (les 4 doivent apparaitre).
4. Decommenter les lignes boutons, redemarrer.

Lecon : faire fonctionner d'abord, faire joli ensuite. Une modif a la fois,
avec Ctrl+S + redemarrage + test entre chaque.

---

## 5. Limitation connue (NON resolue)

Apres un M64 P0, le bouton correspondant ne peut plus eteindre le relais : le
or2 maintient la sortie active tant que l'entree G-code (in0) reste TRUE. De
plus l'etat visuel du bouton checkable peut se desynchroniser de l'etat reel
(bouton et G-code sont deux sources independantes).

- Usage bouton OU G-code separement : acceptable (M65 P0 rend la main au bouton).
- Besoin que le bouton reprenne toujours la main : a revoir (resynchronisation
  de l'etat, ou abandon du or2 au profit d'une autre logique). A trancher.

---

## 6. A faire ensuite

- [ ] Trancher la limitation bouton/G-code ci-dessus.
- [ ] git commit de l'etat fonctionnel.
- [ ] Placement esthetique (frame AUX), une etape a la fois.


# CHANGELOG — PrintNC Flexi-HAL 6000
## Atelier du Verdier

# Changelog — Sorties auxiliaires (relais) FlexiHAL

**Date :** 6 juin 2026
**Machine :** PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd

---# Changelog # Changelog — Sorties auxiliaires (relais) FlexiHAL
# Changelog — Sorties auxiliaires (relais) FlexiHAL

**Date :** 6 juin 2026
**Machine :** PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd

---

## Objectif

Piloter 6 relais (charges : lumiere, arrosage, aspiration, etc.) via les sorties
auxiliaires de la FlexiHAL, commandables depuis QtDragon et le G-code (M64/M65,
M7/M8/M9).

---

## Configuration HAL retenue (AUX0–AUX3)

Connexion directe, sans inversion (modules cables en active HIGH) :

```hal
# Sorties auxiliaires (pilotables par M64/M65)
    net aux0-sig motion.digital-out-00 => flexi.output.AUX0
    net aux1-sig motion.digital-out-01 => flexi.output.AUX1
    net aux2-sig motion.digital-out-02 => flexi.output.AUX2
    net aux3-sig motion.digital-out-03 => flexi.output.AUX3
```

Prerequis INI (sinon M64/M65 sont ignores silencieusement) :

```ini
[EMCMOT]
NUM_DIO = 4
```

Flood / Mist (inchanges, sorties dediees du firmware) :

```hal
# Flood and mist outputs
    net flood flexi.output.COOLANT <= iocontrol.0.coolant-flood
    net mist  flexi.output.MIST    <= iocontrol.0.coolant-mist
```

---

## Cablage materiel valide

L'alimentation ET le signal sont pris directement sur le bornier AUX 2 fils
(borne + et borne -) de la FlexiHAL. Sur le module relais, un petit pont relie
DC+ et IN.

```
Bornier AUX n  (+)  -> DC+ du module, ponte directement vers IN
                       (le + commute fournit a la fois l'alim et le signal)
Bornier AUX n  (+)  -> IN  (via le pont DC+ <-> IN sur le module)
Bornier AUX n  (-)  -> DC- du module (masse, c'est le - de la prise du bornier)
```

Soit, par module :
- Borne + du bornier AUX -> DC+
- Pont court DC+ <-> IN sur le module
- Borne - du bornier AUX -> DC-

Regles importantes :
- Chaque relais est alimente et commande par sa propre prise AUX 2 fils.
- Le pont DC+ <-> IN est ce qui declenche le relais (module active HIGH :
  IN au + = relais actif).
- Le rail AUX doit etre alimente (voir section jumper P17 ci-dessous), sinon la
  borne + sort 0V et rien ne se passe.

---

## Alimentation du rail AUX (point cle)

Les 4 sorties AUX partagent un rail d'alimentation high-side, selectionne par le
jumper P17. C'est ce rail qui fournit le + present sur chaque bornier AUX 2 fils
(et donc, dans notre cablage, l'alim DC+ et le signal IN du module) :
- MAIN  : alim de la carte principale (24V dans notre cas)
- 12V / 5V : max 20 mA, signalisation TTL uniquement — JAMAIS pour charge inductive
- P17 retire : alim via l'entree dediee (fusible + protection polarite)

Ne jamais peupler P17 ET l'alim externe en meme temps.

Limites : 1000 mA combines pour les 4 AUX, resistance de bobine >= 150 Ohm.

---

## Journal de resolution (causes successives ecartees)

1. M64/M65 sans effet
   -> `NUM_DIO` absent du fichier INI. Ajout de `NUM_DIO = 4`. Les pins
      `motion.digital-out-0x` passent writable et changent bien d'etat.

2. Plusieurs relais actifs au demarrage
   -> Sorties AUX a TRUE par defaut + jumpers de modules incoherents (un sur L,
      les autres sur H). Homogeneisation des jumpers.

3. Tests d'inversion HAL (composant `not`)
   -> Piste exploree (modules supposes active LOW) puis abandonnee. Erreurs
      rencontrees : `not.0.in` inexistant (le composant est charge avec
      `names=...`, pas par index), puis `flood_not.in` inexistant (ligne
      `loadrt not` incomplete). Finalement retour au HAL direct.

4. MIST/FLOOD OK mais AUX a 2V puis 0V
   -> Mesure decisive : borne + AUX0 = 0V alors que MIST = 24V. Le rail AUX
      n'etait pas alimente.

5. CAUSE RACINE : le jumper P17 ne faisait pas contact.
   -> Jumper remplace. Le rail AUX recoit enfin 24V, les sorties sortent le bon
      niveau, les relais reagissent correctement.

Conclusion : la configuration HAL et le cablage etaient corrects ; le seul vrai
defaut materiel etait un jumper P17 defectueux.

---

## A verifier / faire ensuite

- [ ] Etendre la config aux 6 relais si besoin (les AUX physiques se limitent a
      4 : AUX0–AUX3 ; les 2 relais restants peuvent passer par COOLANT/MIST ou
      d'autres sorties).
- [ ] Verifier le sens de chaque sortie (M64 = ON, M65 = OFF) apres cablage final.
- [ ] Mesurer la resistance de bobine de chaque relais (>= 150 Ohm) et confirmer
      le total sous 1000 mA.
- [ ] Ajouter la page "Auxiliaires" + boutons ON/OFF dans QtDragon_hd
      (maquette deja realisee).

---

## Notes annexes

- OPT STOP : active/desactive l'arret optionnel sur M1.
- OPT BLOCK : active/desactive le saut des lignes commencant par `/` (block delete).

**Date :** 6 juin 2026
**Machine :** PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd

---

## Objectif

Piloter 6 relais (charges : lumiere, arrosage, aspiration, etc.) via les sorties
auxiliaires de la FlexiHAL, commandables depuis QtDragon et le G-code (M64/M65,
M7/M8/M9).

---

## Configuration HAL retenue (AUX0–AUX3)

Connexion directe, sans inversion (modules cables en active HIGH) :

```hal
# Sorties auxiliaires (pilotables par M64/M65)
    net aux0-sig motion.digital-out-00 => flexi.output.AUX0
    net aux1-sig motion.digital-out-01 => flexi.output.AUX1
    net aux2-sig motion.digital-out-02 => flexi.output.AUX2
    net aux3-sig motion.digital-out-03 => flexi.output.AUX3
```

Prerequis INI (sinon M64/M65 sont ignores silencieusement) :

```ini
[EMCMOT]
NUM_DIO = 4
```

Flood / Mist (inchanges, sorties dediees du firmware) :

```hal
# Flood and mist outputs
    net flood flexi.output.COOLANT <= iocontrol.0.coolant-flood
    net mist  flexi.output.MIST    <= iocontrol.0.coolant-mist
```

---

## Cablage materiel valide

L'alimentation ET le signal sont pris directement sur le bornier AUX 2 fils
(borne + et borne -) de la FlexiHAL. Sur le module relais, un petit pont relie
DC+ et IN.

```
Bornier AUX n  (+)  -> DC+ du module, ponte directement vers IN
                       (le + commute fournit a la fois l'alim et le signal)
Bornier AUX n  (+)  -> IN  (via le pont DC+ <-> IN sur le module)
Bornier AUX n  (-)  -> DC- du module (masse, c'est le - de la prise du bornier)
```

Soit, par module :
- Borne + du bornier AUX -> DC+
- Pont court DC+ <-> IN sur le module
- Borne - du bornier AUX -> DC-

Regles importantes :
- Chaque relais est alimente et commande par sa propre prise AUX 2 fils.
- Le pont DC+ <-> IN est ce qui declenche le relais (module active HIGH :
  IN au + = relais actif).
- Le rail AUX doit etre alimente (voir section jumper P17 ci-dessous), sinon la
  borne + sort 0V et rien ne se passe.

---

## Alimentation du rail AUX (point cle)

Les 4 sorties AUX partagent un rail d'alimentation high-side, selectionne par le
jumper P17. C'est ce rail qui fournit le + present sur chaque bornier AUX 2 fils
(et donc, dans notre cablage, l'alim DC+ et le signal IN du module) :
- MAIN  : alim de la carte principale (24V dans notre cas)
- 12V / 5V : max 20 mA, signalisation TTL uniquement — JAMAIS pour charge inductive
- P17 retire : alim via l'entree dediee (fusible + protection polarite)

Ne jamais peupler P17 ET l'alim externe en meme temps.

Limites : 1000 mA combines pour les 4 AUX, resistance de bobine >= 150 Ohm.

---

## Journal de resolution (causes successives ecartees)

1. M64/M65 sans effet
   -> `NUM_DIO` absent du fichier INI. Ajout de `NUM_DIO = 4`. Les pins
      `motion.digital-out-0x` passent writable et changent bien d'etat.

2. Plusieurs relais actifs au demarrage
   -> Sorties AUX a TRUE par defaut + jumpers de modules incoherents (un sur L,
      les autres sur H). Homogeneisation des jumpers.

3. Tests d'inversion HAL (composant `not`)
   -> Piste exploree (modules supposes active LOW) puis abandonnee. Erreurs
      rencontrees : `not.0.in` inexistant (le composant est charge avec
      `names=...`, pas par index), puis `flood_not.in` inexistant (ligne
      `loadrt not` incomplete). Finalement retour au HAL direct.

4. MIST/FLOOD OK mais AUX a 2V puis 0V
   -> Mesure decisive : borne + AUX0 = 0V alors que MIST = 24V. Le rail AUX
      n'etait pas alimente.

5. CAUSE RACINE : le jumper P17 ne faisait pas contact.
   -> Jumper remplace. Le rail AUX recoit enfin 24V, les sorties sortent le bon
      niveau, les relais reagissent correctement.

Conclusion : la configuration HAL et le cablage etaient corrects ; le seul vrai
defaut materiel etait un jumper P17 defectueux.

---

## A verifier / faire ensuite

- [ ] Etendre la config aux 6 relais si besoin (les AUX physiques se limitent a
      4 : AUX0–AUX3 ; les 2 relais restants peuvent passer par COOLANT/MIST ou
      d'autres sorties).
- [ ] Verifier le sens de chaque sortie (M64 = ON, M65 = OFF) apres cablage final.
- [ ] Mesurer la resistance de bobine de chaque relais (>= 150 Ohm) et confirmer
      le total sous 1000 mA.
- [ ] Ajouter la page "Auxiliaires" + boutons ON/OFF dans QtDragon_hd
      (maquette deja realisee).

---

## Notes annexes

- OPT STOP : active/desactive l'arret optionnel sur M1.
- OPT BLOCK : active/desactive le saut des lignes commencant par `/` (block delete).
— Sorties auxiliaires (relais) FlexiHAL

**Date :** 6 juin 2026
**Machine :** PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd

---

## Objectif

Piloter 6 relais (charges : lumiere, arrosage, aspiration, etc.) via les sorties
auxiliaires de la FlexiHAL, commandables depuis QtDragon et le G-code (M64/M65,
M7/M8/M9).

---

## Configuration HAL retenue (AUX0–AUX3)

Connexion directe, sans inversion (modules cables en active HIGH) :

```hal
# Sorties auxiliaires (pilotables par M64/M65)
    net aux0-sig motion.digital-out-00 => flexi.output.AUX0
    net aux1-sig motion.digital-out-01 => flexi.output.AUX1
    net aux2-sig motion.digital-out-02 => flexi.output.AUX2
    net aux3-sig motion.digital-out-03 => flexi.output.AUX3
```

Prerequis INI (sinon M64/M65 sont ignores silencieusement) :

```ini
[EMCMOT]
NUM_DIO = 4
```

Flood / Mist (inchanges, sorties dediees du firmware) :

```hal
# Flood and mist outputs
    net flood flexi.output.COOLANT <= iocontrol.0.coolant-flood
    net mist  flexi.output.MIST    <= iocontrol.0.coolant-mist
```

---

## Cablage materiel valide

L'alimentation ET le signal sont pris directement sur le bornier AUX 2 fils
(borne + et borne -) de la FlexiHAL. Sur le module relais, un petit pont relie
DC+ et IN.

```
Bornier AUX n  (+)  -> DC+ du module, ponte directement vers IN
                       (le + commute fournit a la fois l'alim et le signal)
Bornier AUX n  (+)  -> IN  (via le pont DC+ <-> IN sur le module)
Bornier AUX n  (-)  -> DC- du module (masse, c'est le - de la prise du bornier)
```

Soit, par module :
- Borne + du bornier AUX -> DC+
- Pont court DC+ <-> IN sur le module
- Borne - du bornier AUX -> DC-

Regles importantes :
- Chaque relais est alimente et commande par sa propre prise AUX 2 fils.
- Le pont DC+ <-> IN est ce qui declenche le relais (module active HIGH :
  IN au + = relais actif).
- Le rail AUX doit etre alimente (voir section jumper P17 ci-dessous), sinon la
  borne + sort 0V et rien ne se passe.

---

## Alimentation du rail AUX (point cle)

Les 4 sorties AUX partagent un rail d'alimentation high-side, selectionne par le
jumper P17. C'est ce rail qui fournit le + present sur chaque bornier AUX 2 fils
(et donc, dans notre cablage, l'alim DC+ et le signal IN du module) :
- MAIN  : alim de la carte principale (24V dans notre cas)
- 12V / 5V : max 20 mA, signalisation TTL uniquement — JAMAIS pour charge inductive
- P17 retire : alim via l'entree dediee (fusible + protection polarite)

Ne jamais peupler P17 ET l'alim externe en meme temps.

Limites : 1000 mA combines pour les 4 AUX, resistance de bobine >= 150 Ohm.

---

## Journal de resolution (causes successives ecartees)

1. M64/M65 sans effet
   -> `NUM_DIO` absent du fichier INI. Ajout de `NUM_DIO = 4`. Les pins
      `motion.digital-out-0x` passent writable et changent bien d'etat.

2. Plusieurs relais actifs au demarrage
   -> Sorties AUX a TRUE par defaut + jumpers de modules incoherents (un sur L,
      les autres sur H). Homogeneisation des jumpers.

3. Tests d'inversion HAL (composant `not`)
   -> Piste exploree (modules supposes active LOW) puis abandonnee. Erreurs
      rencontrees : `not.0.in` inexistant (le composant est charge avec
      `names=...`, pas par index), puis `flood_not.in` inexistant (ligne
      `loadrt not` incomplete). Finalement retour au HAL direct.

4. MIST/FLOOD OK mais AUX a 2V puis 0V
   -> Mesure decisive : borne + AUX0 = 0V alors que MIST = 24V. Le rail AUX
      n'etait pas alimente.

5. CAUSE RACINE : le jumper P17 ne faisait pas contact.
   -> Jumper remplace. Le rail AUX recoit enfin 24V, les sorties sortent le bon
      niveau, les relais reagissent correctement.

Conclusion : la configuration HAL et le cablage etaient corrects ; le seul vrai
defaut materiel etait un jumper P17 defectueux.

---

## A verifier / faire ensuite

- [ ] Etendre la config aux 6 relais si besoin (les AUX physiques se limitent a
      4 : AUX0–AUX3 ; les 2 relais restants peuvent passer par COOLANT/MIST ou
      d'autres sorties).
- [ ] Verifier le sens de chaque sortie (M64 = ON, M65 = OFF) apres cablage final.
- [ ] Mesurer la resistance de bobine de chaque relais (>= 150 Ohm) et confirmer
      le total sous 1000 mA.
- [ ] Ajouter la page "Auxiliaires" + boutons ON/OFF dans QtDragon_hd
      (maquette deja realisee).

---

## Notes annexes

- OPT STOP : active/desactive l'arret optionnel sur M1.
- OPT BLOCK : active/desactive le saut des lignes commencant par `/` (block delete).


## Objectif

Piloter 6 relais (charges : lumiere, arrosage, aspiration, etc.) via les sorties
auxiliaires de la FlexiHAL, commandables depuis QtDragon et le G-code (M64/M65,
M7/M8/M9).

---

## Configuration HAL retenue (AUX0–AUX3)

Connexion directe, sans inversion (modules cables en active HIGH) :

```hal
# Sorties auxiliaires (pilotables par M64/M65)
    net aux0-sig motion.digital-out-00 => flexi.output.AUX0
    net aux1-sig motion.digital-out-01 => flexi.output.AUX1
    net aux2-sig motion.digital-out-02 => flexi.output.AUX2
    net aux3-sig motion.digital-out-03 => flexi.output.AUX3
```

Prerequis INI (sinon M64/M65 sont ignores silencieusement) :

```ini
[EMCMOT]
NUM_DIO = 4
```

Flood / Mist (inchanges, sorties dediees du firmware) :

```hal
# Flood and mist outputs
    net flood flexi.output.COOLANT <= iocontrol.0.coolant-flood
    net mist  flexi.output.MIST    <= iocontrol.0.coolant-mist
```

---

## Cablage materiel valide

L'alimentation ET le signal sont pris directement sur le bornier AUX 2 fils
(borne + et borne -) de la FlexiHAL. Sur le module relais, un petit pont relie
DC+ et IN.

```
Bornier AUX n  (+)  -> DC+ du module, ponte directement vers IN
                       (le + commute fournit a la fois l'alim et le signal)
Bornier AUX n  (+)  -> IN  (via le pont DC+ <-> IN sur le module)
Bornier AUX n  (-)  -> DC- du module (masse, c'est le - de la prise du bornier)
```

Soit, par module :
- Borne + du bornier AUX -> DC+
- Pont court DC+ <-> IN sur le module
- Borne - du bornier AUX -> DC-

Regles importantes :
- Chaque relais est alimente et commande par sa propre prise AUX 2 fils.
- Le pont DC+ <-> IN est ce qui declenche le relais (module active HIGH :
  IN au + = relais actif).
- Le rail AUX doit etre alimente (voir section jumper P17 ci-dessous), sinon la
  borne + sort 0V et rien ne se passe.

---

## Alimentation du rail AUX (point cle)

Les 4 sorties AUX partagent un rail d'alimentation high-side, selectionne par le
jumper P17. C'est ce rail qui fournit le + present sur chaque bornier AUX 2 fils
(et donc, dans notre cablage, l'alim DC+ et le signal IN du module) :
- MAIN  : alim de la carte principale (24V dans notre cas)
- 12V / 5V : max 20 mA, signalisation TTL uniquement — JAMAIS pour charge inductive
- P17 retire : alim via l'entree dediee (fusible + protection polarite)

Ne jamais peupler P17 ET l'alim externe en meme temps.

Limites : 1000 mA combines pour les 4 AUX, resistance de bobine >= 150 Ohm.

---

## Journal de resolution (causes successives ecartees)

1. M64/M65 sans effet
   -> `NUM_DIO` absent du fichier INI. Ajout de `NUM_DIO = 4`. Les pins
      `motion.digital-out-0x` passent writable et changent bien d'etat.

2. Plusieurs relais actifs au demarrage
   -> Sorties AUX a TRUE par defaut + jumpers de modules incoherents (un sur L,
      les autres sur H). Homogeneisation des jumpers.

3. Tests d'inversion HAL (composant `not`)
   -> Piste exploree (modules supposes active LOW) puis abandonnee. Erreurs
      rencontrees : `not.0.in` inexistant (le composant est charge avec
      `names=...`, pas par index), puis `flood_not.in` inexistant (ligne
      `loadrt not` incomplete). Finalement retour au HAL direct.

4. MIST/FLOOD OK mais AUX a 2V puis 0V
   -> Mesure decisive : borne + AUX0 = 0V alors que MIST = 24V. Le rail AUX
      n'etait pas alimente.

5. CAUSE RACINE : le jumper P17 ne faisait pas contact.
   -> Jumper remplace. Le rail AUX recoit enfin 24V, les sorties sortent le bon
      niveau, les relais reagissent correctement.

Conclusion : la configuration HAL et le cablage etaient corrects ; le seul vrai
defaut materiel etait un jumper P17 defectueux.

---

## A verifier / faire ensuite

- [ ] Etendre la config aux 6 relais si besoin (les AUX physiques se limitent a
      4 : AUX0–AUX3 ; les 2 relais restants peuvent passer par COOLANT/MIST ou
      d'autres sorties).
- [ ] Verifier le sens de chaque sortie (M64 = ON, M65 = OFF) apres cablage final.
- [ ] Mesurer la resistance de bobine de chaque relais (>= 150 Ohm) et confirmer
      le total sous 1000 mA.
- [ ] Ajouter la page "Auxiliaires" + boutons ON/OFF dans QtDragon_hd
      (maquette deja realisee).

---

## Notes annexes

- OPT STOP : active/desactive l'arret optionnel sur M1.
- OPT BLOCK : active/desactive le saut des lignes commencant par `/` (block delete).

---

## [2026-06-05] — Session de debug intensive

### Corrigé — `toolchange.ngc` : récursion M6 cassant la preview
**Problème :** Le script `toolchange.ngc` appelé par `REMAP=M6` contenait
lui-même un `M6`, créant une récursion infinie. Effet visible : la preview
G-code de QtDragon ne se chargeait plus pour aucun fichier contenant M6.

**Correction :** Suppression du `M6` parasite dans le script.

---

### Corrigé — `toolchange.ngc` : utilisation de `#<_selected_tool>`
**Problème :** Le script utilisait `#5400` pour identifier l'outil à palper,
mais `#5400` contient l'outil **courant** (pas le nouveau demandé).
Au premier M6 sans outil en broche, `#5400 = 0` → script sortait sur "T0
selectionne" sans palper.

**Correction :** Utilisation de `#<_selected_tool>` (paramètre passé par
LinuxCNC au REMAP) qui contient le numéro d'outil demandé par `T_ M6`.
Capture dans `#<tool_num>` au début du script pour clarté.

---

### Corrigé — `toolchange.ngc` : gestion d'erreur incompatible avec la preview
**Problème :** Les blocs `IF [#5070 EQ 0] ... M2 ... ENDIF` (vérification
de palpage réussi) cassaient la preview QtDragon. Le `M2` (fin programme)
conditionnel dans le script empêchait le rendu du parcours.

**Correction :** Suppression de la gestion d'erreur manuelle.
`G38.2` déclenche déjà automatiquement une erreur LinuxCNC en cas
d'échec de palpage, donc la vérification de `#5070` était redondante.

---

### Corrigé — `remora-flexi.ini` : TOOLSET_X incohérent
**Problème :** `[PROBE] TOOLSET_X = -25.0` ne correspondait pas à la position
réelle du palpeur définie dans `[VERSA_TOOLSETTER] X = -50.0`.

**Correction :**
```ini
TOOLSET_X = -25.0  →  TOOLSET_X = -50.0
```

---

## [2026-05-xx] — Mise en service changement d'outil manuel avec palpage auto

> Note : un OpenATC (changement semi-automatique) avait ete tente puis abandonne.
> La solution retenue est un changement d'outil MANUEL avec palpage AUTOMATIQUE
> de la longueur d'outil au palpeur fixe.

### Ajouté — `toolchange.ngc`
Script de changement d'outil via `REMAP=M6` :
- Palpage automatique au palpeur fixe (X-50 Y60)
- Double palpage (rapide + lent) pour précision
- Mode 0 : Z zéro sur le martyre (automatique)
- Mode 1 : Z zéro sur la pièce (manuel)
- Gestion du premier outil de référence via `#1000` et `#1002`

### Ajouté — Subroutines MDI
- `reset_ref.ngc` : remet `#1000` et `#1002` à zéro avant nouveau job
- `set_mode_martyre.ngc` : sélectionne le mode Z martyre (`#1001 = 0`)
- `set_mode_piece.ngc` : sélectionne le mode Z pièce (`#1001 = 1`)

---

## Bonnes pratiques apprises

### Pour les scripts REMAP
1. **Ne JAMAIS rappeler le code M qui a déclenché le REMAP** dans son
   propre script (ex : pas de `M6` dans `toolchange.ngc`).
2. **Utiliser `#<_selected_tool>`** pour récupérer l'outil demandé,
   pas `#5400` qui contient l'outil courant.
3. **Éviter les `IF` conditionnels contenant `M2` ou `M30`** — ils
   cassent la preview QtDragon. Privilégier des flags dans des variables.
4. **G38.2 gère ses propres erreurs** — pas besoin de vérifier `#5070`
   manuellement avec `G38.2` (à la différence de `G38.3`).


---

## Configuration de référence

| Paramètre | Valeur |
|---|---|
| Machine | PrintNC Flexi-HAL 6000 |
| OS | Debian Bookworm 12, Raspberry Pi 5 |
| LinuxCNC | 2.9.8 uspace |
| Interface | QtDragon_hd 1.5 |
| Carte | Flexi-HAL firmware Remora |
| Changement d'outil | Manuel avec palpage auto (toolchange.ngc) |
| Palpeur fixe | X-50 Y60 |
| dist_palpeur_table | 50.525 mm |

---

## Architecture des variables (changement d'outil + palpage)

```
#1000   -> Position Z de reference (premier outil de la session)
#1001   -> Mode de palpage : 0=martyre auto, 1=piece manuel
#1002   -> Flag session : 0=nouveau job, 1=session en cours
#5400   -> Numero d'outil courant (gere par LinuxCNC)
#5063   -> Position Z au contact du dernier palpage
#5420   -> X du WCS actif (G54)
#5421   -> Y du WCS actif (G54)

#<_selected_tool> -> Outil demande par T_ M6 (uniquement dans REMAP)
```

Bouton **Reset Ref** dans QtDragon → remet `#1000` et `#1002` à zéro
avant chaque nouveau job pour forcer une nouvelle prise de référence.
