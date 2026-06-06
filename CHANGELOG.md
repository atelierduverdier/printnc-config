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

## [2026-05-xx] — Mise en service ATC semi-automatique

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
| ATC | RapidChange Solo — X-50 Y160 |
| Palpeur fixe | X-50 Y60 |
| dist_palpeur_table | 50.525 mm |

---

## Architecture des variables ATC

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
