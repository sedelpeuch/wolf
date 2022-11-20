Documentation Wolf
===================================

.. figure:: ../img/wolf.png
   :align: center
   :alt: wolf
   :width: 50%


.. raw:: html

   <p>
   </p>

Le projet Wolf est une application Flask permettant de faire le lien entre les adhérents d'EirLab Community et Dolibarr
notre logiciel de gestion de l'association.

Le projet comporte actuellement les fonctionnalités suivantes :

1. Onglet :doc:`Adhérents <adherent>`
    - Obtenir la fiche d'un adhérent à partir de sa carte étudiante ou autre
    - Lier le profil d'un adhérent à partir de sa carte étudiante ou autre, son nom et prénom
2. Onglet :doc:`Formations <formation>`
    - Donner de nouvelles formations aux adhérents
3. Onglet :doc:`Stock <stock>`
    - Rechercher un article dans le stock
    - Ajouter une série d'articles dans le stock à partir d'une référence ou en scannant un code barre
4. Onglet :doc:`Emprunts <emprunt>`
    - Emprunter un article
    - Rendre un article
    - Voir les emprunts en cours


.. toctree::
    :glob:
    :numbered:
    :titlesonly:
    :caption: Site Web

    adherent.rst
    formation.rst
    stock.rst
    common.rst

.. toctree::
    :glob:
    :numbered:
    :titlesonly:
    :caption: Électronique & Système embarqué

    rfid.rst
    barcode.rst



