# Wolf 🐺

Le projet Wolf est une application Flask permettant de faire le lien entre les adhérents d'EirLab Community et Dolibarr
notre logiciel de gestion de l'association.

Le projet comporte actuellement les fonctionnalités suivantes :

1. Onglet Adhérents
    - Obtenir la fiche d'un adhérent à partir de sa carte étudiante ou autre
    - Lier le profil d'un adhérent à partir de sa carte étudiante ou autre, son nom et prénom
2. Onglet Formations
    - Donner de nouvelles formations aux adhérents
    - Voir les formations à venir et permettre aux fabmanager de s'y inscrire
3. Onglet Stock
    - Rechercher un article dans le stock
    - Ajouter une série d'articles dans le stock à partir d'une référence ou en scannant un code barre
    - Gérer les articles en alerte de stock et générer les commandes fournisseurs dans dolibarr
4. Onglet Emprunts
    - Emprunter un article
    - Rendre un article
    - Voir les emprunts en cours

## Installation

- Cloner le projet depuis le github d'EirLab Community : `git clone git@github.com:Eirlab/wolf.git`
- Configurer le token pour réaliser des requêtes vers l'API Dolibarr. Aller dans `config.py` et éditer la
  variable `token`
- Il est nécessaire d'avoir un environnement Python3 avec Flaks installé (`flask`, `flask-cors`, `flask-socketio`)
- Il suffit ensuite de lancer le projet avec la commande : `python3 run_api.py`

Pour une installation sur un PC, il faut déployer et activer `wolf.service`.
Copier ce fichier dans `/etc/systemd/system/` puis lancer la commande `systemctl enable wolf.service`. Le service se
lancera alors au démarrage du poste et sera relancé automatiquement en cas de plantage.

Pour utiliser le module de stock avec un scanner de code barre il est nécessaire de faire le lien bluetooth entre le
scanner et votre pc : voir [ce tutoriel](https://wolf-eirlab-community.readthedocs.io/fr/latest/barcode.html)

Le site sera accessible sur `http://localhost:5000/` ou `http://<adresse_ip_hôte>:5000` pour un accès depuis un autre
poste du même réseau.
