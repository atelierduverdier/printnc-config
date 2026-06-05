# CHANGELOG — PrintNC Flexi-HAL 6000
## Atelier du Verdier

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
