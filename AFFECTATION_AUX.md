# Affectation des sorties auxiliaires (AUX) — PrintNC Flexi-HAL
## Atelier du Verdier

Mise a jour : 17 juillet 2026

---

## Tableau des sorties

| Sortie | Pin G-code        | Bouton QtDragon | Affectation              | Etat       |
|--------|-------------------|-----------------|--------------------------|------------|
| AUX0   | motion.digital-out-00 | qtdragon.aux0 | Aspirateur               | Cable      |
| AUX1   | motion.digital-out-01 | qtdragon.aux1 | Lumiere                  | Cable      |
| AUX2   | motion.digital-out-02 | qtdragon.aux2 | Ventilateurs broche      | Cable      |
| AUX3   | aucun (M3 $1 / M5 $1) | aucun         | Interlock laser          | Cable      |

Lecture du tableau : AUX3 est bien **cablee et active** (elle alimente le +24V
du laser). Les colonnes "aucun" signifient seulement qu'elle n'a plus de
pilotage par M64/M65 ni par bouton : c'est `spindle.1.on` qui la commande.

Note : la pompe a eau n'est PAS sur une sortie AUX. Elle est branchee sur la
sortie FLOOD (flexi.output.COOLANT), commandee par M8 / M9.

---

## Interlock laser (AUX3)

Depuis juillet 2026, AUX3 est dediee a l'interlock du laser (LaserTree
LT-80W-AA-PRO pilote comme spindle.1) :

- Pilotage direct par `spindle.1.on` : `M3 $1` ferme le relais et alimente
  le +24V du laser (fil rouge), `M5 $1` le coupe. Pas de composant or2 :
  ni M64 P3 ni le bouton QtDragon aux3 ne commandent plus cette sortie
  (nets commentes dans remora-flexi.hal pour eviter un double pilotage).
- Le relais coupe uniquement le VCC du laser. Il n'y a plus de
  convertisseur externe 0-10V vers PWM dans la chaine depuis le
  17 juillet 2026 : le PWM sort directement de la Flexi-HAL sur le fil
  jaune (voir README.md, section Laser). Deux convertisseurs ont grille
  avant cette bascule, le maillon a ete supprime.
- Securite : en PWM direct, S0 met la sortie au niveau bas statique
  (~0.67V), lu comme "eteint" par l'entree TTL du laser. Le plancher de
  ~0.73V de l'ancienne chaine 0-10V (qui etait une vraie consigne de
  puissance) n'existe plus. AUX3 reste malgre tout la coupure de
  reference : ceinture ET bretelles.

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

- G-code : M64 P0..P2 (activer), M65 P0..P2 (desactiver)
  - M64 P0 -> aspirateur ON,    M65 P0 -> aspirateur OFF
  - M64 P1 -> lumiere ON,       M65 P1 -> lumiere OFF
  - M64 P2 -> ventilateurs ON,  M65 P2 -> ventilateurs OFF
  - AUX3 : plus de M64/M65 ni bouton -> pilotee par M3 $1 / M5 $1 (laser)
- M8 -> pompe a eau ON (flood),  M9 -> pompe a eau OFF
- Boutons QtDragon (AUX0 a AUX2) : combines avec le G-code via les
  composants or2 (relais actif si bouton OU G-code le demande).
- Refroidissement : M8 et la rotation broche activent pompe ET ventilateurs
  ensemble, avec 30 s de post-refroidissement apres l'arret (voir section
  dediee ci-dessus).

---

## Notes

- AUX3 est desormais affectee a l'interlock laser (voir section dediee).
  Plus aucune sortie AUX libre : pour un futur accessoire (eclairage zone,
  signal fin de programme, electrovanne air comprime...), prevoir un module
  d'extension ou une reaffectation.
- La pompe a eau utilise la sortie FLOOD (COOLANT), pas une AUX : cela permet
  de la commander avec M8/M9 et de la lier au refroidissement de la broche.
- Rappel materiel : modules relais cables en active HIGH (jumper sur H).
  Alimentes et commandes via le bornier AUX 2 fils (jumper P17 sur MAIN = 24V),
  avec un pont DC+ <-> IN sur chaque module. Config HAL directe (sans inversion),
  les boutons et le G-code sont combines par les composants or2.
  Voir le changelog du 6-7 juin pour le detail cablage.
