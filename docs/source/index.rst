Documentation Wolf
===================================

.. figure:: ../img/wolf.png
   :align: center
   :alt: wolf
   :width: 50%


.. raw:: html

   <p>
   </p>

Le projet Wolf est un projet ayant pour but la gestion des ressources internes de l'association EirLab Community. L'objectif du projet est de
fournir un environnement d'interconnexion entre les différents outils de gestions de l'association (HelloAsso, Dolibarr, etc...).

Le projet est composé de deux packages. Wolf et Wolf Core.
Wolf Core est un package permettant de mettre en place un runner de tâches asynchrones. Il défini plusieurs interfaces permettant de définir une
application à exécuter a une certaine fréquence en se basant sur la librairie `schedule <https://schedule.readthedocs.io/en/stable/>`_. Les
interfaces principales sont :

- :class:`wolf_core.api.API` : Interface permettant de définir la connexion avec une API externe.
- :class:`wolf_core.api.Application` : Interface permettant de définir une application à exécuter à une certaine fréquence.

Wolf est un package applicatif utilisant Wolf Core pour définir des applications à exécuter.

.. toctree::
    :glob:
    :numbered:
    :titlesonly:
    :caption: Wolf

    installation.md
    notion

.. toctree::
    :glob:
    :numbered:
    :titlesonly:
    :caption: Wolf Core

    core/core


