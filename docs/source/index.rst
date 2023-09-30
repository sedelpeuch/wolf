Documentation Wolf
===================================

.. figure:: ../img/wolf.png
   :align: center
   :alt: wolf
   :width: 50%


.. raw:: html

   <p>
   </p>

Le projet Wolf est un projet ayant pour but de créer un environnement d'interconnexion entre les différents outils pouvant être utilisés dans la gestion d'associatins, de projets etc

Le projet est composé de deux packages. Wolf et Wolf Core.
Il défini plusieurs interfaces permettant de définir une
application à executer via les github action

Les interfaces principales sont :

- :class:`wolf_core.api.API` : Interface permettant de définir la connexion avec une API externe.
- :class:`wolf_core.api.Application` : Interface permettant de définir une application à exécuter à une certaine fréquence.

Wolf est un package applicatif utilisant Wolf Core pour définir des applications à exécuter.

.. toctree::
    :glob:
    :numbered:
    :titlesonly:
    :caption: Wolf

    installation.md
    notion_main.md
    notion
    notion2latex

.. toctree::
    :glob:
    :numbered:
    :titlesonly:
    :caption: Wolf Core

    core/core


