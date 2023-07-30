Installation
============

Pour installer le projet, suivez les instructions ci-dessous :

Clonez le projet sur votre machine en utilisant la commande suivante :
bash

```bash
git clone git@github.com:sedelpeuch/wolf.git
```

Installation pour les utilisateurs
----------------------------------

Créez un environnement virtuel et installez le package :

```bash
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install poetry
poetry install

```

Installation pour les développeurs
----------------------------------

Le projet utilise des submodules Git, vous devez donc les initialiser comme suit :

```bash
git submodule init
git submodule update
cd core
git checkout main
```

Ensuite, installez les dépendances du projet et le package wolf_core :

```bash
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install poetry
cd core
poetry install
```

Configuration
-------------

Le projet utilise les arguments de la ligne de commande pour définir les paramètres de connexion à divers outils.
Vous pouvez placer vos tokens directement via les arguments de la
ligne de commande.

```bash
python install.py --token1 VOTRE_TOKEN1 --token2 VOTRE_TOKEN2 ...
```

N'oubliez pas de remplacer VOTRE_NOTION_TOKEN et VOTRE_DOLIBARR_TOKEN par vos véritables tokens.
Vous pouvez également placer vos tokens dans le fichier `install.py`.

Pour enregistrer la configuration et lancer le projet en tant que service systemd, exécutez la commande suivante :

```bash
deactivate
sudo python3 install.py
```