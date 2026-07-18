# Workflow laser (T100) - PrintNC Atelier du Verdier

Mise a jour : 17 juillet 2026

Memo operatoire pour graver au laser LaserTree LT-80W-AA-PRO monte sur
glissiere. A suivre dans l'ordre, sans sauter d'etape.

---

## Les 3 reperes a ne jamais confondre

| Repere | C'est quoi | Valeur |
|--------|-----------|--------|
| **Nez** | Le cone en bout de laser. C'est LUI qui touche la pastille du palpeur. C'est la reference de `T100 M6`. | - |
| **Focus** | Le point ou le faisceau est le plus fin. Il est **8.5 mm SOUS le nez**. | 8.5 mm |
| **Offset XY** | Ecart nez / axe broche. Dans `tool.tbl`, applique par `G43 H100`. | X +2.0 / Y -90.0 |

**Regle d'or :** apres `T100 M6` + `G43 H100`, **Z0 = le NEZ**, pas le
focus. Pour mettre le focus sur la surface, il faut donc travailler a
`Z = <hauteur de la surface> + 8.5`.

**Le nez touche-t-il la piece ?** Ca depend du mode :

- **Mode Martyre** : JAMAIS. Le nez ne touche que la pastille du
  palpeur, tout seul, pendant `T100 M6`. Si le nez frotte le bois
  pendant un job, le Z du G-code est faux (voir Pieges).
- **Mode Piece** : OUI, une fois, volontairement, au moment du touch-off
  manuel sur le dessus de la piece (voir Workflow C).

---

## WORKFLOW A - Job 100% laser (le cas normal)

Mode Martyre. Aucun touch-off manuel, aucune fraise a monter.

### 1. Physique (machine a l'arret)

- [ ] Monter le laser sur la glissiere, **engager jusqu'a la butee**
- [ ] Brancher le laser (24V + fil jaune PWM)
- [ ] Poser la piece sur le martyre, **brider**
- [ ] **Mesurer l'epaisseur au pied a coulisse** -> la noter, on en a besoin
- [ ] Degager la zone : rien sur le trajet du portique

### 2. Securite (non negociable)

- [ ] **Lunettes laser** sur le nez
- [ ] Extincteur a portee de main
- [ ] Aspiration / ventilation en marche
- [ ] Personne d'autre dans l'atelier sans lunettes

### 3. LinuxCNC - preparation de session

- [ ] Machine ON, lever l'arret d'urgence
- [ ] **Homing** complet (Z monte en premier, puis X et Y)
- [ ] Bouton **Reset Ref** -> remet `#1000` et `#1002` a zero
- [ ] Bouton **Mode Martyre** -> `#1001 = 0`

> L'ordre Reset Ref PUIS Mode Martyre n'a pas d'importance, mais les
> deux doivent etre faits AVANT le T100 M6.

### 4. Palpage du laser

En MDI :

    T100 M6

Ce qui se passe :
1. La broche remonte en G53 Z0
2. Elle va au-dessus du palpeur, **decalee** pour que ce soit le nez du
   laser qui soit sur la pastille (message : `Decalage laser hors course
   X - palpage plafonne a -49.5` = normal, c'est prevu)
3. **PAUSE** : message `Verifiez que l outil est bien monte`
   -> le laser est deja monte (etape 1) -> appuyer sur **RESUME**
4. Palpage en 2 passes -> `touch_z = [~47.5]`
5. Message `Premier outil reference - Zero martyre defini`
   -> Z0 est maintenant le **dessus du martyre**
6. Message `Info - Le LASER T100 va definir la reference de cette
   session` -> **normal et voulu** pour un job laser seul

Puis, toujours en MDI :

    G43 H100

-> active la compensation : offset Z du palpage + offsets X/Y de `tool.tbl`.
Le DRO affiche desormais la position du **nez du laser**.

### 5. Zero X/Y sur la piece

- [ ] Jogger jusqu'au coin de reference de la gravure
- [ ] Pour viser precisement, tir bref a faible puissance :

      M3 $1 S20      (le spot apparait)
      ... jog ...
      M5 $1          (extinction)

- [ ] Touch-off **X0** et **Y0** a ce point

> Ne PAS toucher au Z ici. Il est deja defini (martyre).

### 6. Generer le G-code

Dans l'atelier laser FreeCAD, renseigner :

- **Focale : 8.5** (et pas 4, valeur par defaut du generateur)
- **Epaisseur : <la mesure du pied a coulisse>**

-> le Z de gravure doit sortir a `epaisseur + 8.5`.

**Verification obligatoire avant de lancer** : ouvrir le .ngc et lire
les premieres lignes.

    G0 Z<degagement>
    G0 Z<epaisseur + 8.5>     <- CE CHIFFRE

Exemple : chute de 16.3 mm -> le Z de gravure doit etre **24.8**.
Si le fichier dit Z9, le nez va labourer le bois. Ne pas lancer.

### 7. Lancer

- [ ] Charger le .ngc dans QtDragon
- [ ] Verifier la preview (pas d'erreur de parsing)
- [ ] **Rester devant la machine** pendant toute la gravure

### 8. Fin de job

- [ ] `M5 $1` si le fichier ne l'a pas fait (coupe le relais AUX3)
- [ ] Verifier qu'aucun point ne rougeoie sur la piece
- [ ] Retirer le laser de la glissiere si on repasse au fraisage

---

## WORKFLOW B - Job mixte (fraisage + gravure)

Meme chose, sauf que **la fraise doit etre le PREMIER outil de la
session**, car c'est elle qui definit la reference.

1. Reset Ref + Mode Martyre
2. Monter la fraise -> `T2 M6` -> RESUME
   -> message `Premier outil reference - Zero martyre defini`
3. Faire l'usinage
4. `M5` (broche off), attendre l'arret complet
5. Monter le laser sur la glissiere
6. `T100 M6` -> RESUME
   -> message `Offset outil calcule - Mode martyre` (et PAS "Premier
   outil reference" : c'est le signe que l'ordre est bon)
7. `G43 H100`
8. Lancer le job laser

> Si on voit `Premier outil reference` au moment du T100 M6 dans un job
> mixte, c'est que le Reset Ref a ete refait entre temps : la reference
> fraise est perdue, les deux outils ne sont plus coherents.

---

## WORKFLOW C - Mode Piece (zero Z sur le dessus de la piece)

Mode Piece. Le Z est pris manuellement sur la piece, pas sur le martyre.

### Quand l'utiliser plutot que le Mode Martyre

- La piece n'est PAS posee a plat sur le martyre (gabarit, plaque a
  depression, cales)
- L'epaisseur est irreguliere, ou on ne veut pas la mesurer
- On veut que le generateur n'ait qu'UNE constante a connaitre : 8.5.
  Plus de saisie d'epaisseur, donc plus d'oubli possible.

### Etapes

1 a 3 : **identiques au Workflow A** (physique, securite, homing),
sauf qu'on n'a PAS besoin de mesurer l'epaisseur.

4. Bouton **Reset Ref**
5. Bouton **Mode Piece** -> `#1001 = 1`
6. En MDI :

       T100 M6

   -> RESUME a la pause -> palpage
   -> message `Premier outil reference - Mode piece`
   (et PAS "Zero martyre defini" : en Mode Piece le script ne touche
   jamais au G54)

7. En MDI :

       G43 H100

   -> offset outil = 0 (le laser est la reference), offsets X/Y appliques

8. **Touch-off Z sur la piece** :
   - Jogger le nez au-dessus de la piece
   - Descendre **doucement** (increments 0.1 puis 0.01 mm) jusqu'a
     effleurer la surface. Intercaler une feuille de papier et s'arreter
     quand elle coince : ca evite de mater le cone sur le bois.
   - Touch-off **Z = 0** (ou Z = epaisseur du papier, ~0.1)
   - -> G54 Z0 = **nez du laser au niveau de la surface**

9. Zero X/Y : comme au Workflow A, etape 5 (tir de visee `M3 $1 S20`)

10. Generateur : **Focale 8.5**, **Epaisseur 0**
    -> le Z de gravure doit sortir a **8.5** tout court.

11. Verification avant lancement : ouvrir le .ngc, le `G0 Z<...>` de
    gravure doit dire **Z8.5**. Si autre chose, ne pas lancer.

12. Lancer, surveiller, `M5 $1` en fin de job.

### Pourquoi T100 M6 AVANT le touch-off (et pas apres)

L'ordre compte. Au moment du touch-off manuel, il ne doit y avoir aucun
offset outil parasite : sinon il se retrouve fige dans le G54 et fausse
tout le reste.

`T100 M6` en premier met l'offset de T100 a **zero** (il devient la
reference de la session, `G10 L1 P100 Z0`). Le `G43 H100` qui suit
n'ajoute donc rien en Z, et le touch-off se fait sur une base propre.

Si on touche-off d'abord, l'offset actif est celui laisse par la session
precedente -> valeur silencieusement fausse.

**Variante job mixte en Mode Piece :** meme principe, mais c'est la
FRAISE qui prend le zero. Ordre : Reset Ref -> Mode Piece -> `T2 M6` ->
`G43 H2` -> touch-off Z0 sur la piece -> usinage -> `M5` -> monter le
laser -> `T100 M6` -> `G43 H100` -> graver a Z8.5. Avantage : le nez du
laser ne touche jamais la piece.

---

## Quel mode choisir ?

| | Mode Martyre | Mode Piece |
|---|---|---|
| Touch-off manuel | non | oui |
| Nez du laser sur la piece | jamais | oui (une fois) |
| Epaisseur a mesurer | **oui** (pied a coulisse) | non |
| Z de gravure | `epaisseur + 8.5` | `8.5` |
| Piece sur cales / gabarit | non adapte | **adapte** |
| Risque principal | oublier de saisir l'epaisseur | mater le cone au touch-off |

**Par defaut : Mode Martyre** (workflow A), plus rapide et sans contact.
**Mode Piece** des que la piece n'est pas a plat sur le martyre.

---

## Aide-memoire commandes

| Besoin | Commande |
|--------|----------|
| Palper le laser | `T100 M6` puis `G43 H100` |
| Armer le laser (relais AUX3) | `M3 $1 S0` |
| Tir de visee faible puissance | `M3 $1 S20` |
| Puissance a 50% | `S500 $1` |
| Puissance a zero (laser reste arme) | `S0 $1` |
| **Extinction reelle** (ouvre AUX3) | `M5 $1` |
| Nouveau job | Bouton **Reset Ref** |
| Zero Z sur martyre | Bouton **Mode Martyre** (`#1001 = 0`) |
| Zero Z sur piece | Bouton **Mode Piece** (`#1001 = 1`) |

---

## Pieges connus (tous rencontres au moins une fois)

**Le nez frotte le bois**
-> Le Z du G-code est faux. Verifier le `G0 Z<...>` de gravure en tete
de fichier :
- Mode Martyre : doit valoir `epaisseur + 8.5`
- Mode Piece : doit valoir `8.5`

Cause habituelle : le generateur a garde son epaisseur (5 mm) ou sa
focale (4 mm) par defaut.

**Mettre la focale dans tool.tbl**
-> Inutile : `toolchange.ngc` ecrase la colonne Z a chaque `M6`
(`G10 L1 P<n> Z<offset>`). Seuls X et Y survivent. La focale est
l'affaire du generateur, pas de la table d'outils.

**Le job gele au premier G1, laser allume, plus rien ne bouge**
-> Le correctif at-speed n'est pas charge dans le HAL. Verifier :

    halcmd getp spindle.0.at-speed

Doit etre **TRUE** broche a l'arret. Si FALSE, `remora-flexi.hal` n'a
pas les composants `atspeed_or` / `s0_on_not`. Voir README.

**Erreur "Nested comment found"**
-> Le G-code contient des parentheses imbriquees dans un commentaire.
Bug du generateur. Chercher `(... (...) ...)` dans le .ngc.

**La gravure part 90 mm a cote**
-> `G43 H100` oublie, ou colonnes X/Y de T100 vides dans `tool.tbl`
(doivent valoir X 2.0 / Y -90.0).

**Pas de degrade, tout noir**
-> Saturation du materiau : augmenter le feed, baisser la puissance max.
Ou `laser_scale` revenu a gain 0.102 / offset -6 : verifier avec
`halcmd getp laser_scale.gain` (doit valoir 0.1) et `.offset` (0).

---

## Securite - rappels durs

- Une **pause programme ne coupe PAS le laser**. Un job en pause continue
  d'emettre au point fixe. Sur bois, c'est un depart de feu en quelques
  secondes. Seul `M5 $1` ouvre le relais AUX3.
- Ne jamais laisser une gravure sans surveillance, meme 30 secondes.
- Lunettes laser en permanence, y compris pour un tir de visee a S20.
- Le laser reste arme apres un `S0 $1`. Pour l'eteindre vraiment :
  `M5 $1`.
