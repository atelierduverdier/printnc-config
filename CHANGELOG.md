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
Test de perte de pas recommande (allers-retours G0 pleine course, verifier
le retour exact a la position de depart).

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

Note : les erreurs "page_allocator ... Invalid argument" au demarrage
(liees a QtWebEngine / page web de QtDragon, non utilisee) sont presentes
mais sans rapport avec ce bug ; non traitees.

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

- [ ] Test de perte de pas a 10 000 (validation finale de la vitesse).
- [ ] Eventuellement tenter 12 000 mm/min par paliers, en surveillant le
      fouettement des vis.
- [ ] Travailler MAX_ACCELERATION (actuellement 200) si l'accel est le facteur
      limitant ressenti sur trajets courts.
- [ ] Retirer 0_tmp du suivi git.
- [ ] Projet de documentation complete de la machine (a partir des reels
      Instagram, export JSON).
