# Changelog — 8 juin 2026
## PrintNC Flexi-HAL — Atelier du Verdier

Machine : PrintNC — FlexiHAL (Expatria / Remora) — LinuxCNC 2.9.8 — QtDragon_hd

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
