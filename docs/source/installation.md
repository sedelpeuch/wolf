Installation
============

Pour installer le projet, il faut d'abord cloner le projet sur votre machine:

```bash
git clone git@github.com:eirlab/wolf.git
```

Installation pour les développeurs
----------------------------------

Le projet est basé sur les submodules git, il faut donc initialiser les submodules:

```bash
git submodule init
git submodule update
cd core
git checkout main
```

Ensuite, il faut installer les dépendances du projet et installer le package `wolf_core` :

```bash
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install poetry
cd core
poetry install
```

Installation pour les utilisateurs
----------------------------------

Créez un environnement virtuel et installez le package `wolf_core` :

```bash
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install 'wolf_core @ git+https://github.com/Eirlab/wolf-core.git' 
```
