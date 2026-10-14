# Le système du Pi, hors LinuxCNC

Ce que ce dépôt ne portait pas : les réglages du **système** du Raspberry Pi 5
de l'atelier, faits à la main en dehors de la config LinuxCNC. Une carte SD
neuve, ou une réinstallation de l'image LinuxCNC, les perd tous. Ce dossier en
garde les fichiers tels qu'ils étaient sur le Pi le 14/10/2026, et la façon de
les refaire.

**Ces fichiers ne sont lus par rien.** LinuxCNC ne les charge pas, un
`git pull` ne les pose pas. Ce sont des copies de sauvegarde : ils ne servent
qu'à les remettre à la main, à leur place, sur un Pi neuf.

Le Pi, relevé le 14/10/2026 : Debian 12.13, noyau temps réel
`6.6.31-rt31`, LinuxCNC 2.9.10, bureau Xfce (xfwm4), serveur Xorg pilote
`modesetting`.

| Fichier ici | Sa place sur le Pi | Pourquoi |
|---|---|---|
| `etc/X11/xorg.conf.d/99-v3d.conf` | `/etc/X11/xorg.conf.d/99-v3d.conf` | l'écran passe par le GPU du Pi (`vc4`, pilote `modesetting`) |
| `etc/ntpsec/ntp.conf` | `/etc/ntpsec/ntp.conf` | l'heure se cale sur srv (192.168.1.85) en premier |
| `xfce/xfwm4.xml` | `~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml` | composition des fenêtres coupée |
| `mesa-avant-backports-20261014.txt` | — | les versions de Mesa **d'avant** le 14/10, pour revenir en arrière |

## 1. Les pilotes graphiques : Mesa des backports (14/10/2026)

Le Mesa de Debian 12 (22.3.6) date d'avant le Pi 5 et ne connaît pas son GPU
(V3D 7.1, pris en charge à partir de Mesa 23.3). Vulkan retombait sur
**llvmpipe**, le rendu par le processeur : VerdierCAM ramait, et QtDragon
moins visiblement. Mesa 25 des **bookworm-backports** le reconnaît. Il ne
change que les pilotes graphiques : ni le noyau temps réel, ni LinuxCNC.

**LinuxCNC fermé, machine à l'arrêt.** La ligne des backports est déjà dans
`/etc/apt/sources.list` (ligne 5) :

```bash
deb http://deb.debian.org/debian bookworm-backports main contrib non-free non-free-firmware
```

Puis :

```bash
sudo apt update
sudo apt install -t bookworm-backports mesa-vulkan-drivers libgl1-mesa-dri libglx-mesa0 \
  libegl-mesa0 libgbm1 mesa-va-drivers mesa-vdpau-drivers
sudo apt install libfuse2
sudo reboot
```

apt tire derrière lui `mesa-libgallium`, `libdrm*` 2.4.123 et les deux
`-dev` déjà présents : **15 paquets** en `~bpo12` au total
(`dpkg-query -W | grep bpo12`). Vérifier :

```bash
sudo apt install vulkan-tools
vulkaninfo --summary | grep -i devicename
```

Doit dire **V3D 7.1** (relevé : « V3D 7.1.7.0 »). `llvmpipe` veut dire que
l'ancien Mesa est encore là. `libfuse2` sert à lancer les AppImage
(VerdierCAM ARM64).

Revenir en arrière : les versions d'avant sont dans
`mesa-avant-backports-20261014.txt`, à réinstaller par
`sudo apt install <paquet>=<version>`.

## 2. Le curseur qui clignote : composition coupée

Avec le nouveau Mesa, le curseur de la souris clignotait toutes les ~3 s sur
le bureau et dans QtDragon. Le remède est de couper la composition de xfwm4.
Seules les ombres sous les fenêtres disparaissent. Dans la session graphique :

```bash
xfconf-query -c xfwm4 -p /general/use_compositing -s false
```

Ce qui n'y a rien fait, essayé puis remis d'origine :

- `vblank_mode` à `xpresent` (il est à `auto`) ;
- `Option "SWcursor" "true"` dans `99-v3d.conf`.

**Piège payé** : `SWcursor`, laissé actif, faisait clignoter le curseur
*dans VerdierCAM*. Le retirer du `.conf` ne suffit pas : le serveur X garde
l'option jusqu'à sa relance (`sudo systemctl restart lightdm`, ou un
redémarrage). Vérifier qu'il n'en reste rien :

```bash
grep -c SWcursor /var/log/Xorg.0.log    # doit dire 0
```

## 3. L'heure sur srv (17/08/2026)

Le Pi n'a pas de pile : après une coupure d'alimentation, il repart de
l'heure de sa dernière extinction propre (`fake-hwclock`). La ligne
`server 192.168.1.85 iburst prefer`, en fin de `ntp.conf`, le recale sur srv
en ~90 s. Elle donne l'**adresse** de srv, pas son nom : srv est aussi le
serveur DNS. Le commentaire au-dessus de la ligne dit pourquoi. Vérifier :

```bash
timedatectl show -p NTPSynchronized    # doit dire yes
```

Une heure fausse ne déplace aucune trajectoire. Elle ne fausse que les dates
des fichiers et des commits : **ne pas commiter depuis le Pi** tant que
`NTPSynchronized` ne dit pas `yes`.
