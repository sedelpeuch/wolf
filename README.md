# Wolf 🐺

Le projet Wolf est une application Flask permettant de faire le lien entre les adhérents d'EirLab Community et Dolibarr

Le projet comporte actuellement les fonctionnalités suivantes :

1. Onglet Adhérents
    - Obtenir la fiche d'un adhérent à partir de sa carte étudiante ou autre
    - Lier le profil d'un adhérent à partir de sa carte étudiante ou autre, son nom et prénom
2. Onglet Formations
    - Donner de nouvelles formations aux adhérents

## Installation

- Cloner le projet sur son poste : `git clone git@github.com:Eirlab/wolf.git`
- Configurer le token pour requêter vers l'API Dolibarr. Aller dans `config.py` et éditer la variable `token`
- Il est nécessaire d'avoir un environnement Python3 avec Flaks installé
- Il suffit ensuite de lancer le projet avec la commande : `python3 run_api.py`

Pour une installation sur un PC, il faut déployer et activer `wolf.service`.
Copier ce fichier dans `/etc/systemd/system/` puis lancer la commande `systemctl enable wolf.service`. Le service se 
lancera alors au démarrage du poste et sera relancé automatiquement en cas de plantage.

Le site sera accessible sur `http://localhost:5000/` ou `http://<adresse_ip_hôte>:5000` pour un accès depuis un autre
poste du même réseau.
