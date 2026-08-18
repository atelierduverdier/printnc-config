#!/usr/bin/env python3
"""Engendre subroutines/banc/atc_config.ngc depuis le vrai fichier.

Le banc a besoin des memes 27 parametres que la machine, avec seulement
les quatre valeurs [ETABLI] remplacees par des valeurs plausibles. Les
recopier a la main serait le piege que ce depot connait bien : une
valeur ecrite deux fois finit par diverger, et ici la divergence se
verrait comme une sequence qui « marche au banc » et rate a l'atelier.

Le fichier engendre porte le MEME nom que le vrai. C'est le
SUBROUTINE_PATH de remora-flexi-sim.ini, qui cite banc/ en premier, qui
decide lequel est lu -- la machine, dont l'ini ne cite pas ce dossier,
ne peut pas y tomber.
"""
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
SOURCE = RACINE / "subroutines" / "atc_config.ngc"
CIBLE = RACINE / "subroutines" / "banc" / "atc_config.ngc"

# Les seules valeurs que le banc invente. Rondes a dessein : on ne doit
# pas pouvoir les confondre avec un releve.
BANC = {
    "_atc_poste1_x": ("37.5", "bloc de X0 a X450, poste 1 a 37,5 du bout"),
    "_atc_poste1_y": ("1275.0", "au fond, dans le vide Y1000-Y1350 entre tubes"),
    "_atc_engage_z": ("-60.0", "ARBITRAIRE : la vraie se releve ecrou en main"),
    "_atc_z_sur": ("-10.0", "transit XY au-dessus du magasin"),
}

# Le vrai fichier sort en essai A BLANC (_atc_essai = 1) : aucune rotation,
# arret a la precharge, ce qui est la bonne prudence a l'atelier tant que
# personne n'a vu le nez toucher l'ecrou. Au banc c'est l'inverse -- sans
# rotation, la moitie de la sequence n'est jamais parcourue, et c'est
# justement celle qui visse. Le banc n'a rien a casser.
ESSAI_BANC = "0"

BANDEAU = """; =====================================================================
; ENGENDRE PAR outils/faire_config_banc.py -- NE PAS EDITER ICI.
; Corriger le vrai subroutines/atc_config.ngc, ou les valeurs de banc
; dans le script, puis relancer.
;
; CONFIGURATION DE BANC : elle ne pilote AUCUNE machine. Seules les
; quatre valeurs [ETABLI] different du vrai fichier ; tout le reste en
; sort tel quel, pour que le banc et l'atelier ne racontent pas deux
; geometries.
;
; IMPLANTATION SUPPOSEE : sous le lit, des tubes acier de 100 de large
; courent selon X au pas de 450 (100 de tube, 350 de vide). Le bloc fait
; 450 x 71,2 : pose EN Y il couvrirait un tube et perdrait un poste ;
; pose EN X, parallele aux tubes, il tient dans un vide avec 139 mm de
; marge de chaque cote et garde ses six postes.
; =====================================================================
(MSG, ATC : configuration de BANC - valeurs provisoires, aucune machine)
"""


def main():
    texte = SOURCE.read_text()
    for nom, (valeur, pourquoi) in BANC.items():
        motif = re.compile(rf"^(#<{nom}>\s*)=\s*-9999.*$", re.M)
        if not motif.search(texte):
            sys.exit(f"{nom} : plus de sentinelle dans le vrai fichier — releve fait ?"
                     " Alors ce script n'a plus lieu d'etre.")
        texte = motif.sub(rf"\g<1>= {valeur}   ; [BANC] {pourquoi}", texte)

    motif_essai = re.compile(r"^(#<_atc_essai>\s*)=\s*1", re.M)
    if not motif_essai.search(texte):
        sys.exit("_atc_essai n'est plus a 1 dans le vrai fichier : verifier"
                 " ce que le banc doit faire avant de forcer quoi que ce soit.")
    texte = motif_essai.sub(rf"\g<1>= {ESSAI_BANC}   ; [BANC] rotation exercee, rien a casser ici", texte)

    # Le bandeau se glisse APRES la ligne `O<atc_config> sub`, sans quoi
    # le sous-programme ne serait plus appelable.
    lignes = texte.split("\n")
    lignes.insert(1, BANDEAU)
    texte = "\n".join(lignes)

    if "-9999" in re.sub(r"^;.*$", "", texte, flags=re.M):
        sys.exit("il reste une sentinelle hors commentaire — le banc refuserait de tourner")

    CIBLE.parent.mkdir(parents=True, exist_ok=True)
    CIBLE.write_text(texte)
    print(f"  {CIBLE.relative_to(RACINE)} engendre depuis {SOURCE.name}")
    print(f"  {len(BANC)} valeurs d'etabli remplacees, le reste tel quel")


if __name__ == "__main__":
    main()
