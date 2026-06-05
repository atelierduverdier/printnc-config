### Revision du 05-06-2026
## Probleme - Preview G-code disparue dans QtDragon

### Symptôme
La zone de prévisualisation 3D affiche uniquement le contour de la table
(rectangle rouge) mais pas le parcours outil, quel que soit le fichier chargé.
Le tracé apparaît en live pendant l'usinage mais jamais en preview.

### Cause réelle
Le `REMAP=M6` dans `remora-flexi.ini` combiné avec un `M6` présent
**dans** le script `toolchange.ngc` créait une **récursion infinie** :

```
M6 → appelle toolchange.ngc → ligne 19 : M6 → appelle toolchange.ngc → ...
```
 CHANGELOG.md 
LinuxCNC détecte la récursion et bloque l'interpréteur au chargement
du fichier → la preview ne se génère jamais.

### Correction — toolchange.ngc
Supprimer le `M6` parasite dans le script de changement d'outil :

```ngc
; AVANT (ligne 19) :
M6    ; Changement outil   ← À SUPPRIMER

; APRÈS : ligne supprimée
```

La séquence correcte dans toolchange.ngc est :
1. `G53 G0 Z0` — remontée sécurité
2. `M5` — arrêt broche
3. `G4 P1.0` — attente
4. ~~M6~~ — NE PAS rappeler M6 dans le script REMAP M6 !
5. Suite du script (palpage, calcul offsets...)

---

## CORRECTIONS SUPPLÉMENTAIRES IDENTIFIÉES

### Incohérence TOOLSET_X dans remora-flexi.ini
```ini
; AVANT (incorrect) :
[PROBE]
TOOLSET_X = -25.0   ← utilisé par le bouton Probe de l'interface

; APRÈS (correct) :
[PROBE]
TOOLSET_X = -50.0   ← cohérent avec [VERSA_TOOLSETTER] X = -50.0
```

---

## CONFIGURATION DE RÉFÉRENCE

- **Machine** : PrintNC Flexi-HAL 6000
- **OS** : Debian Bookworm 12, Raspberry Pi 5
- **LinuxCNC** : 2.9.8 uspace
- **Interface** : QtDragon_hd 1.5
- **Carte** : Flexi-HAL firmware Remora
- **Post-processeur** : `LinuxCNC_Arcs_mm____ngc_.pp` (Atelier du Verdier)
- **ATC** : RapidChange Leverdier — X-50 Y160
- **Palpeur fixe** : X-50 Y60

---

## RAPPEL ARCHITECTURE ATC

```
#1001 = 0  → Mode martyre (Z zéro automatique sur la table)
#1001 = 1  → Mode pièce (Z zéro manuel sur le dessus de la pièce)
#1000      → Référence Z du premier outil de la session
#1002      → Flag "session en cours" (0=nouveau job, 1=en cours)
```

Bouton **Reset Ref** dans QtDragon → remet #1000 et #1002 à zéro
avant chaque nouveau job.
