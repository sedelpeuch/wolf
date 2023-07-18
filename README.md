# Projet Wolf

Wolf Status

[![Documentation Status](https://readthedocs.org/projects/wolf-eirlab-community/badge/?version=latest)](https://wolf-eirlab-community.readthedocs.io/?badge=latest) [![Unittest](https://github.com/Eirlab/wolf/actions/workflows/unittest.yml/badge.svg)](https://github.com/Eirlab/wolf/actions/workflows/unittest.yml)

Wolf-Core Status

[![Documentation Status](https://readthedocs.org/projects/wolf-eirlab-community/badge/?version=latest)](https://wolf-eirlab-community.readthedocs.io/?badge=latest) [![Wolf Core](https://github.com/Eirlab/wolf-core/actions/workflows/unittest.yml/badge.svg)](https://github.com/Eirlab/wolf-core/actions/workflows/unittest.yml)

Le projet Wolf est une initiative de l'association EirLab Community visant à gérer les ressources internes. Son objectif
est de fournir un
environnement d'interconnexion entre différents outils de gestion tels que HelloAsso et Dolibarr. Cette solution permet
une gestion centralisée et
harmonisée des processus de l'association.

## Installation

Pour installer le projet, suivez les instructions ci-dessous :

Clonez le projet sur votre machine en utilisant la commande suivante :
bash

```bash
git clone git@github.com:eirlab/wolf.git
```

### Installation pour les utilisateurs

Créez un environnement virtuel et installez le package `wolf_core` :

```bash
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install 'wolf_core @ git+https://github.com/Eirlab/wolf-core.git'

```

### Installation pour les développeurs

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

### Configuration

Le projet utilise un fichier de configuration pour définir les paramètres de connexion aux différents outils. Vous devez
créer un fichier de configuration à placer dans le répertoire wolf nommé `token.json` ayant le format suivant :

```json
{
  "notion": "SECRET_HERE",
  "dolibarr": "SECRET_HERE"
}
```

Attention, ce fichier ne doit pas être versionné ! Vous devez donc l'ajouter au fichier `.gitignore` du projet.

Une fois l'installation terminée, vous pouvez commencer à utiliser le projet Wolf.

## Documentation

La documentation complète du projet est disponible dans le répertoire /docs. Vous pouvez consulter cette documentation
pour en savoir plus sur les
fonctionnalités du projet et son utilisation.

La documentation est disponibe en ligne à l'adresse suivante : https://wolf-eirlab-community.readthedocs.io/

## Contributions

Nous accueillons avec plaisir les contributions à notre projet ! Si vous souhaitez contribuer, veuillez suivre les
étapes suivantes :

- Forker le dépôt
- Créer une nouvelle branche
- Effectuer vos modifications
- Valider vos changements
- Pousser votre branche
- Soumettre une pull request

Nous apprécions les contributions de la communauté pour améliorer et faire évoluer le projet Wolf !

## Licence

Ce projet est distribué sous licence GPL3. Pour plus d'informations, veuillez consulter le fichier LICENSE.

Nous espérons que le projet Wolf répondra à vos besoins de gestion des ressources internes. N'hésitez pas à nous
contacter si vous avez des questions
ou des commentaires. Merci de votre intérêt pour notre projet !
