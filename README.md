# Projet Wolf

Wolf Status

[![Documentation Status](https://readthedocs.org/projects/wolf-project/badge/?version=latest)](https://wolf-project.readthedocs.io/?badge=latest) [![Unittest](https://github.com/sedelpeuch/wolf/actions/workflows/unittest.yml/badge.svg)](https://github.com/sedelpeuch/wolf/actions/workflows/unittest.yml)

Wolf-Core Status

[![Documentation Status](https://readthedocs.org/projects/wolf-project/badge/?version=latest)](https://wolf-project.readthedocs.io/?badge=latest) [![Wolf Core](https://github.com/sedelpeuch/wolf-core/actions/workflows/unittest.yml/badge.svg)](https://github.com/sedelpeuch/wolf-core/actions/workflows/unittest.yml) [![Publish to Test PyPI](https://github.com/sedelpeuch/wolf-core/actions/workflows/publish.yaml/badge.svg)](https://github.com/sedelpeuch/wolf-core/actions/workflows/publish.yaml)

Le projet Wolf est un projet ayant pour but de créer un environnement d'interconnexion entre les différents outils pouvant être utilisés dans la gestion d'associatins, de projets
etc

## Installation

Pour installer le projet, suivez les instructions ci-dessous :

Clonez le projet sur votre machine en utilisant la commande suivante :
bash

```bash
git clone git@github.com:sedelpeuch/wolf.git
```

### Installation

Créez un environnement virtuel et installez le package :

```bash
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install poetry
poetry install

```

Il est nécessaire de créer un fichier `wolf/token.json` en remplissant avec les tokens adaptés (cela dépend de vos api et applications). Dans le cas du projet actuel :

```json
{
  "notion": "",
  "dolibarr": "",
  "github_doc_latex": "",
  "github_doc_publish": "",
  "notion_master_file": ""
}
```

## Documentation

La documentation complète du projet est disponible dans le répertoire /docs. Vous pouvez consulter cette documentation
pour en savoir plus sur les
fonctionnalités du projet et son utilisation.

La documentation est disponible en ligne à l'adresse suivante : https://wolf-project.readthedocs.io/

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
