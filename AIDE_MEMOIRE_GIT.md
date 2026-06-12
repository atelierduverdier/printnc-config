# Aide-memoire — Commandes essentielles
## PrintNC Flexi-HAL — Atelier du Verdier

Depot : https://github.com/atelierduverdier/printnc-config
Dossier config : ~/linuxcnc/configs/flexi-hal

---

## RECUPERER les modifications (depuis GitHub vers la machine)

A faire sur le PC ou le Pi pour rapatrier ce qui a ete pousse ailleurs
(tablette, autre machine) :

    cd ~/linuxcnc/configs/flexi-hal
    git pull origin main

---

## ENVOYER les modifications (depuis la machine vers GitHub)

Methode rapide avec le script (demande un message) :

    push-config

Ou manuellement :

    cd ~/linuxcnc/configs/flexi-hal
    git add -A
    git commit -m "Description de la modif"
    git push origin main

---

## VOIR l'etat du depot

Quels fichiers ont change :

    cd ~/linuxcnc/configs/flexi-hal
    git status

---

## WORKFLOW TYPE (PC <-> Pi via GitHub)

1. Sur le PC : modifier l'interface, tester en simulation
       linuxcnc ~/linuxcnc/configs/flexi-hal/remora-flexi-sim.ini
2. Sur le PC : envoyer
       push-config
3. Sur le Pi : recuperer avant d'usiner
       cd ~/linuxcnc/configs/flexi-hal && git pull origin main

Regle d'or : toujours "git pull" en arrivant sur une machine, pour partir
de la derniere version. Ca evite les conflits.

---

## LANCER LINUXCNC

Sur le Pi (machine reelle) :

    linuxcnc ~/linuxcnc/configs/flexi-hal/remora-flexi.ini

Sur le PC (simulation, fenetre) :

    linuxcnc ~/linuxcnc/configs/flexi-hal/remora-flexi-sim.ini

---

## OUVRIR QT DESIGNER (editer l'interface)

    qtdesigner

(alias deja configure dans ~/.bashrc ; ouvre directement qtdragon_hd.ui)

---

## EN CAS DE CONFLIT (git refuse le pull)

Si git dit qu'il y a des modifications locales qui bloquent :

1. Voir ce qui a change localement :
       git status
2. Si les modifs locales sont a garder : les commiter puis pull
       push-config
       git pull origin main
3. Si les modifs locales sont a jeter (revenir a la version GitHub) :
       git checkout -- .
       git pull origin main

   (ATTENTION : "git checkout -- ." efface les modifs locales non commitees)

En cas de doute, ne rien forcer et demander de l'aide.

---

## VERIFIER QUI ON EST (config git)

    git config --global user.name
    git config --global user.email

---

## LE SCRIPT push-config (pour reference / reinstallation)

Le script vit dans ~/bin/push-config.sh (hors depot git), rendu executable
avec : chmod +x ~/bin/push-config.sh
Alias dans ~/.bashrc : alias push-config='~/bin/push-config.sh'

Contenu du script :

    #!/bin/bash
    # Pousse la config LinuxCNC vers le depot git.
    # Demande un message de commit, puis add + commit + push.

    CONFIG_DIR="$HOME/linuxcnc/configs/flexi-hal"
    cd "$CONFIG_DIR" || { echo "Dossier introuvable : $CONFIG_DIR"; exit 1; }

    if [ ! -d .git ]; then
        echo "Erreur : $CONFIG_DIR n'est pas un depot git."
        exit 1
    fi

    echo "=== Etat actuel du depot ==="
    git status --short

    if [ -z "$(git status --porcelain)" ]; then
        echo "Rien a commiter, le depot est propre."
        exit 0
    fi

    echo ""
    read -r -p "Message de commit : " MSG

    if [ -z "$MSG" ]; then
        echo "Message vide, abandon."
        exit 1
    fi

    git add -A
    git commit -m "$MSG" || { echo "Echec du commit."; exit 1; }

    BRANCH=$(git rev-parse --abbrev-ref HEAD)

    echo ""
    echo "=== Envoi vers origin/$BRANCH ==="
    git push origin "$BRANCH"

    echo ""
    echo "Termine."

---

## ALIAS A AVOIR DANS ~/.bashrc

    # Ouvre Qt Designer avec l'interface QtDragon (adapter aarch64 / x86_64)
    alias qtdesigner='PYQT5_DESIGNERPATH=/usr/lib/python3/dist-packages/qtvcp/plugins QT_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt5/plugins designer ~/linuxcnc/configs/flexi-hal/qtvcp/screens/qtdragon_hd/qtdragon_hd.ui'

    # Pousse la config vers GitHub (demande un message)
    alias push-config='~/bin/push-config.sh'

Note : sur le Raspberry Pi, remplacer "x86_64-linux-gnu" par "aarch64-linux-gnu"
dans l'alias qtdesigner.

Apres modification de ~/.bashrc : source ~/.bashrc
