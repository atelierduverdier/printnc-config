# Affectation des sorties auxiliaires (AUX) — PrintNC Flexi-HAL
## Atelier du Verdier

Mise a jour : 8 juin 2026

---

## Tableau des sorties

| Sortie | Pin G-code        | Bouton QtDragon | Affectation              | Etat       |
|--------|-------------------|-----------------|--------------------------|------------|
| AUX0   | motion.digital-out-00 | qtdragon.aux0 | Aspirateur               | Cable      |
| AUX1   | motion.digital-out-01 | qtdragon.aux1 | Lumiere                  | Cable      |
| AUX2   | motion.digital-out-02 | qtdragon.aux2 | Pompe a eau              | Cable      |
| AUX3   | motion.digital-out-03 | qtdragon.aux3 | LIBRE (reserve)          | Disponible |

---

## Commandes

- G-code : M64 P0..P3 (activer), M65 P0..P3 (desactiver)
  - M64 P0 -> aspirateur ON,  M65 P0 -> aspirateur OFF
  - M64 P1 -> lumiere ON,     M65 P1 -> lumiere OFF
  - M64 P2 -> pompe ON,       M65 P2 -> pompe OFF
- Boutons QtDragon : combines avec le G-code via les composants or2
  (relais actif si bouton OU G-code le demande).

---

## Notes

- AUX3 est laissee libre volontairement (porte ouverte pour un futur
  accessoire : eclairage zone, signal fin de programme, electrovanne air
  comprime, etc.). Cablage propre et disponible, rien a modifier pour
  l'activer le moment venu.
- Rappel materiel : modules relais cables en active HIGH (jumper sur H).
  Alimentes et commandes via le bornier AUX 2 fils (jumper P17 sur MAIN = 24V),
  avec un pont DC+ <-> IN sur chaque module. Config HAL directe (sans inversion),
  les boutons et le G-code sont combines par les composants or2.
  Voir le changelog du 6-7 juin pour le detail cablage.
