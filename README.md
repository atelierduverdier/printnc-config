# Configuration PrintNC - Atelier du Verdier - 21 mai 2026

Ce dépôt rassemble les fichiers de configuration LinuxCNC (`.ini` et `.hal`) utilisés pour piloter ma fraiseuse CNC **PrintNC (Format standard avec surface de travail utile d'environ 1275x1275mm)**.

La machine est contrôlée via l'architecture **Flexi-HAL** (firmware Remora) sur base Raspberry Pi 5 et l'interface graphique modernisée **QtDragon HD**.

---

## 🛠️ Nomenclature & Matériel Utilisé (BOM)

### 1. Motorisation & Alimentation (OMC-StepperOnline)
* **Moteurs (Axes X, Y1, Y2, Z) :** 4x Moteurs pas à pas en boucle fermée Nema 23 (3.00 Nm / 424.83 oz.in) avec encodeur magnétique 1000 PPR (4000 CPR).
  * *Référence :* `23HS40-5004-ME1K`
* **Drivers :** 4x Pilotes pas à pas en boucle fermée V4.1 (0-8.0A, 24-48VDC) adaptés pour Nema 17/23/24.
  * *Référence :* `CL57T-V41`
* **Câblage :** Kit de câbles d'extension de puissance et d'encodeur blindés AWG20 de 4.7m.
  * *Référence :* `CE5-M5-20`
* **Alimentations Moteurs :** Alimentations à découpage 350W 48V 7.3A (Sélectionnables 115/230V).
  * *Référence :* `LE-350-48`

### 2. Broche & Refroidissement (Aliexpress / G-Penny)
* **Broche :** Moteur de broche G-Penny Original 2.2kW ER20 refroidi par eau (Dimensions 80x230mm, 220V). Équipée de 4 roulements céramiques de la série 7 pour une déviation max de 0.01mm (Modèle long).
* **Variateur (VFD) :** Onduleur / Inverter HuangYang (HY) 2.2kW 220VAC classique.
* **Refroidissement :** Pompe à eau 220V 75W (Débit max 3200 L/H) avec 5 mètres de tuyau. Le circuit fonctionne en circuit fermé avec du **liquide de refroidissement automobile** pour prévenir l'oxydation interne et la prolifération d'algues.

### 3. Contrôle, Électronique & Sécurité
* **Calculateur :** Raspberry Pi 5 exécutant LinuxCNC (Version 2.9.8).
* **Carte d'interface (Interface Board) :** Expatria Flexi-HAL exploitant le firmware Remora pour la génération hardware des impulsions.
* **Gestion de la Puissance :** Contacteur ABB AF09-30-10-11 avec bobine basse tension en 24V (pour la sécurité générale de l'armoire électrique).
* **Capteurs de limites (Homing) :** Capteurs de proximité inductifs de type **NPN NC (Normalement Fermé)** câblés et alimentés en 5V.
* **Palpage :** Sonde mobile et/ou fixe (Tool Setter) gérée via l'interface de précision **VersaProbe**.

### 4. Structure Mécanique & Transmission
* **Châssis :** Profilés en tubes d'acier rectangulaires massifs de **100x50mm avec une épaisseur de 4mm** (Spécificité apportant une masse et une rigidité accrues par rapport aux recommandations standard du wiki). Enceinte et pièces décoratives/liaisons en hêtre gravé issues de l'atelier.
* **Transmission Axes X & Y :** Vis à billes SFU1610 (Pas de 10mm par tour) montées sur rails de guidage linéaires HGR20.
* **Transmission Axe Z :** Vis à billes fine SFU1204 (Pas de 4mm par tour) pour contrer l'effet de la gravité et optimiser le couple de maintien vertical de la broche.

---

## 📐 Paramètres de Configuration Clés (`.ini`)

* **Résolution des Pas (Scale) :**
  * Axe X : `-160.0` (Basé sur des drivers réglés à 1600 pas/tour, vis au pas de 10mm, direction inversée matériellement).
  * Axe Y1 (Maître) : `160.0` & Axe Y2 (Esclave/Tandem) : `-160.0` (Montage des moteurs face à face en effet miroir).
  * Axe Z : `400.0` (Basé sur un réglage à 1600 pas/tour et une vis fine au pas de 4mm).
* **Limites de Courses Logicielles :**
  * X : de `-5.0mm` à `1285.0mm` (Dégagement final à `5.0mm`).
  * Y : de `-2.0mm` à `1286.0mm` (Position de repli finale `HOME` établie à `1275.0mm`).
  * Z : de `-185.0mm` (Descente max) à `5.0mm` (Dégagement haut, `HOME` de sécurité à `0.0mm`).
* **Vitesses maximales (Max Velocity) :** * Axes X & Y : 250 mm/s ($15\ 000\text{ mm/min}$) avec un plafond `STEPGEN_MAXVEL` à 280 mm/s.
  * Axe Z : 33.33 mm/s ($2\ 000\text{ mm/min}$) avec une limite électrique `STEPGEN_MAXVEL` fixée à 100.0 mm/s face à la gravité.
* **Timings des impulsions (Stepgen) :** `STEPLEN = 2500` et `STEPSPACE = 2500` pour une stabilité électrique optimale avec les drivers CL57T sur la Flexi-HAL.
