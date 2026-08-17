#!/bin/bash
# sync-gcode.sh
# Synchronise les fichiers G-code entre le partage reseau et le dossier
# local de LinuxCNC, avec rsync.
#
# VERSIONNE DANS LE DEPOT depuis le 17/08/2026, et appele par le bouton
# « MAJ DEPUIS SERVEUR » de la page FILE de QtDragon (voir la methode
# btn_sync_gcode_clicked du gestionnaire). Il etait auparavant dans
# ~/Scripts/ sur le Pi seulement : cette copie-la est desormais un
# doublon, et un doublon de script finit toujours par divergent de celui
# qui est reellement appele. Le bouton n'appelle QUE cette version-ci,
# celle du dossier de configuration.
#
# POURQUOI COPIER PLUTOT QUE GRAVER DEPUIS LE PARTAGE. Le partage reste
# la REFERENCE (il est sauvegarde, et il est accessible machine eteinte) ;
# nc_files n'est qu'un cache jetable. Mais LinuxCNC lit le programme au
# fil de l'execution : une coupure reseau au milieu d'un nuancier de 3 Mo,
# soit plusieurs heures, casserait la gravure. D'ou la copie locale AVANT
# de graver.
#
# Le sens PUSH (local -> serveur) est garde parce qu'il sert a la main,
# mais le bouton n'emploie QUE le sens PULL : un seul sens automatique,
# donc aucune divergence possible sur la question de savoir qui fait foi.
#
# Par defaut le script tourne en mode ESSAI (dry-run) : il montre ce qu'il
# ferait sans rien modifier. Ajoute "go" pour executer reellement.
#
# Usage :
#   ./sync-gcode.sh            essai,      sens serveur -> local
#   ./sync-gcode.sh go         execution,  sens serveur -> local
#   ./sync-gcode.sh push       essai,      sens local -> serveur
#   ./sync-gcode.sh push go    execution,  sens local -> serveur

# --- Configuration a adapter une seule fois ---
DISTANT="/mnt/srv-partage/Gcode"         # dossier des G-code sur le partage
LOCAL="$HOME/linuxcnc/nc_files"        # dossier local lu par LinuxCNC
# -----------------------------------------------

# Options rsync adaptees a un montage CIFS :
# -r recursif, -t conserve les dates, -v verbeux, -h tailles lisibles
# --modify-window=1 tolere l'ecart d'horodatage entre Linux et CIFS
# --progress affiche l'avancement des gros fichiers
RSYNC="rsync -rtvh --modify-window=1 --progress"

# Determiner le sens et le mode a partir des arguments
SENS="pull"
MODE="essai"
for arg in "$@"; do
    case "$arg" in
        push) SENS="push" ;;
        go)   MODE="reel" ;;
    esac
done

# Verifier que le partage reseau est bien monte
if ! mountpoint -q /mnt/srv-partage; then
    echo "ERREUR : le partage /mnt/srv-partage n'est pas monte."
    echo "Lance d'abord : sudo mount /mnt/srv-partage"
    exit 1
fi

# Definir source et destination selon le sens
# (le slash final sur la source est important pour rsync)
if [ "$SENS" = "pull" ]; then
    SRC="$DISTANT/"
    DST="$LOCAL/"
    echo ">>> Sens : SERVEUR -> LOCAL"
else
    SRC="$LOCAL/"
    DST="$DISTANT/"
    echo ">>> Sens : LOCAL -> SERVEUR"
fi

mkdir -p "$LOCAL"

# Executer en mode essai ou reel
if [ "$MODE" = "essai" ]; then
    echo ">>> Mode ESSAI (dry-run) : rien ne sera modifie."
    echo ">>> Pour executer reellement, relance la meme commande avec 'go'."
    echo
    $RSYNC --dry-run "$SRC" "$DST"
else
    echo ">>> Mode REEL : synchronisation en cours..."
    echo
    $RSYNC "$SRC" "$DST"
    echo
    echo "OK : synchronisation terminee."
fi
