# Lunii

Reverse engineering de la fabrique à histoire **Lunii v1**.

* [Installation](#installation)
  + [Clone du projet](#clone-du-projet)
  + [Prérequis pour Windows](#prérequis-pour-windows)
  + [Prérequis pour CentOS](#prérequis-pour-centos)
* [Lister le contenu audio présent sur le boitier Lunii](#lister-le-contenu-audio-présent-sur-le-boitier-lunii)
* [Extraire un pack](#extraire-un-pack)
* [Uploader un pack](#uploader-un-pack)
* [Décoder un pack ](#d-coder-un-pack)
* [Encoder un pack ](#encoder-un-pack)
* [Suppression d'un pack](#suppression-d-un-pack)
* [Divers](#divers)
  + [Format image](#format-image)
  + [Format audio](#format-audio)
  + [Format pack binaire](#format-pack-binaire)
  + [Format pack yaml](#format-pack-binaire)

## Installation

## Clone du projet

```
python3 -m pip install libusb pyyaml
git clone https://github.com/dmachard/lunii.git
```

## Prérequis pour Windows

* Installer les [drivers USB](https://github.com/dmachard/lunii/releases/download/0.1.0/usb.drivers.win.zip) du boitier Lunii.

* Téléchargement du logiciel [ffmpeg](https://ffmpeg.org/download.html#build-windows)

Le logiciel ffmeg n'est pas obligatoire néanmoins il est fortement conseillé de l'installer pour profiter de la conversion automatique des images et des fichiers audios.
Le répertoire ffmeg est à déposer à la racine du projet: /<projet_lunii>/ffmpeg/bin/ffmpeg.exe
  
## Prérequis pour CentOS

```
yum install libusb ffmpeg
```

## Lister le contenu audio présent sur le boitier Lunii

L'option --content permet d'afficher la version du firmware, l'espace disque disponible et utilisé et les packs d'histoires.
    
```
py audio4lunii.py --content
Firwmare:
    Version: 1.2
SD Card (bytes):
    Total: 7886520320
    Used: 1746597376
    Free: 6139922944
Packs:
    Total: 6
    Stories:
            c4139d59-872a-4d15-8cf1-76d34cdf38c6
            74e59c16-6a28-45ce-9906-fca8fd69f23c
            d489f67b-0e51-4669-b1e1-1555f3c18541
            2675f48b-9038-4be1-8d9b-146d83331cf9
            644e75ef-2b2c-4feb-9e5c-07ffff51e5f0
            a8f3072a-b95b-4fab-a3f5-19fd71168cf9
```

## Extraire un pack
    
L'option --download permet d'extraire un pack audio (identifié par son ID) présent dans le boitier

```
py audio4lunii.py --download d489f67b-0e51-4669-b1e1-1555f3c18541
[##################################################] 100.0%
```

## Uploader un pack
    
L'option --upload permet de déverser un pack d'histoire sur le boitier Lunii.
Le pack d'histoire doit être présent dans le répertoire `./packs/`.

```
py audio4lunii.py --upload monhistoire.pack
[##################################################] 100.0%
```

## Décoder un pack 

L'option --decode permet de décoder un pack binaire et ainsi extraire les fichiers images et audios.
Le pack à décoder doit être présent dans le répertoire `./packs/`.
Le pack décodé est ensuite disponible dans le répertoire `./working/<nomdupack>/`.

```
py audio4lunii.py --decode monhistoire.pack
pack successfully decoded
```

## Encoder un pack 

L'option --encode permet d'encoder un pack à partir d'images, de fichier audios et du fichier de description yaml.
Le pack à encoder doit être présent dans le répertoire `./working/<nomdupack>/`.
Le pack encodé est ensuite disponible dans le répertoire `./packs/`.

```
py audio4lunii.py --encode basic_example.pack
pack successfully encoded
```

## Suppression d'un pack 

L'option --delete permet de supprimer un pack audio du boitier.

```
py audio4lunii.py --delete d489f67b-0e51-4669-b1e1-1555f3c18541
```

## Divers

## Format image

Le format d'image supporté par le boitier:
 - BMP
 - 320x240 pixels
 - 24 bits

Privilégier des images en noir et blanc pour un meilleur rendu.

## Format audio

Le format audio supporté par le boitier:
 - WAV
 - Mono
 - 16 bits
 - 32000Hz

## Format pack binaire

| Format                                               |
|------------------------------------------------------|
| pack (nb elements, is factory, version)              |
| xx element(s) (uuid, image offset, image size,<br>audio offset, audio size,<br>next offset, nb next, next index,<br>home offset, nb home, home index,<br>ctrl wheel, ctrl ok, ctrl_home,<br>ctrl_pause, ctrl_autonext)<br>        |
| xx transition(s) (element id, ... )                  |
| data ... images                                      |      
| data ... audio                                       |      
| end                                                  |


## Format pack yaml

Un pack décodé se constitue:
- d'un répertoire "image" contenant les images associées à chaque histoire.
- d'un répertoire "audio" contenant l'ensemble des fichiers audio.
- d'un ficher `pack.yaml` décrivant les enchainements entre les histoires.

Les fichiers sont automatiquement convertis dans le format supporté (wav,bmp) à l'aide de **ffmpeg**.

Le nom des images et des fichiers audios doit respecter la règle suivante:
- <element_id>.<extension_fichier>

Le fichier de description yaml doit être de la forme suivante:

```yaml
elements:
  <element_id>:
    controls-enabled:
    - wheel
    - ok
    transition-index: <transition_id>
  <element_id>:
    controls-enabled:
    - home
    - pause
    - autojump
    transition-index: <transition_id>
transitions:
  <transition_id>:
    next:
    - <element_id>
  <transition_id>:
    next:
    - <element_id>
```

Un exemple de pack *basic_example* est disponible dans le répertoire `working`.
