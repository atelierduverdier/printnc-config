# Affectation des sorties auxiliaires (AUX) — PrintNC Flexi-HAL
## Atelier du Verdier

Mise a jour : 16 juin 2026

---

## Tableau des sorties

| Sortie | Pin G-code        | Bouton QtDragon | Affectation              | Etat       |
|--------|-------------------|-----------------|--------------------------|------------|
| AUX0   | motion.digital-out-00 | qtdragon.aux0 | Aspirateur               | Cable      |
| AUX1   | motion.digital-out-01 | qtdragon.aux1 | Lumiere                  | Cable      |
| AUX2   | motion.digital-out-02 | qtdragon.aux2 | Ventilateurs broche      | Cable      |
| AUX3   | motion.digital-out-03 | qtdragon.aux3 | LIBRE (reserve)          | Disponible |

Note : la pompe a eau n'est PAS sur une sortie AUX. Elle est branchee sur la
sortie FLOOD (flexi.output.COOLANT), commandee par M8 / M9.

---

## Refroidissement de la broche (pompe + ventilateurs)

La pompe a eau (FLOOD) et les ventilateurs (AUX2) fonctionnent ensemble comme
un seul circuit de refroidissement, pilote par un signal commun "cooling-active" :

- Demarrage immediat quand la broche tourne (M3) ou quand on lance M8.
- Post-refroidissement : apres l'arret de la broche (M5) ou M9, la pompe ET les
  ventilateurs restent actifs encore 30 secondes pour evacuer la chaleur, puis
  s'arretent ensemble.
- Le bouton AUX2 de QtDragon et M64 P2 / M65 P2 commandent toujours les
  ventilateurs manuellement.

Le delai de 30 s se regle dans remora-flexi.hal :
`setp spindle_cooldown.off-delay 30` (en secondes).

---

## Commandes

- G-code : M64 P0..P3 (activer), M65 P0..P3 (desactiver)
  - M64 P0 -> aspirateur ON,    M65 P0 -> aspirateur OFF
  - M64 P1 -> lumiere ON,       M65 P1 -> lumiere OFF
  - M64 P2 -> ventilateurs ON,  M65 P2 -> ventilateurs OFF
- M8 -> pompe a eau ON (flood),  M9 -> pompe a eau OFF
- Boutons QtDragon : combines avec le G-code via les composants or2
  (relais actif si bouton OU G-code le demande).
- Refroidissement : M8 et la rotation broche activent pompe ET ventilateurs
  ensemble, avec 30 s de post-refroidissement apres l'arret (voir section
  dediee ci-dessus).

---

## Notes

- AUX3 est laissee libre volontairement (porte ouverte pour un futur
  accessoire : eclairage zone, signal fin de programme, electrovanne air
  comprime, etc.). Cablage propre et disponible, rien a modifier pour
  l'activer le moment venu.
- La pompe a eau utilise la sortie FLOOD (COOLANT), pas une AUX : cela permet
  de la commander avec M8/M9 et de la lier au refroidissement de la broche.
- Rappel materiel : modules relais cables en active HIGH (jumper sur H).
  Alimentes et commandes via le bornier AUX 2 fils (jumper P17 sur MAIN = 24V),
  avec un pont DC+ <-> IN sur chaque module. Config HAL directe (sans inversion),
  les boutons et le G-code sont combines par les composants or2.
  Voir le changelog du 6-7 juin pour le detail cablage.
