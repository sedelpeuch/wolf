API
===================================

Ce script Python définit un module qui simplifie l'interaction avec une API.

Le script comprend les principales sections suivantes :

1. Une fonction décoratrice type_check() pour vérifier le type des arguments transmis à une fonction. Si les types des arguments ne correspondent pas aux types attendus, une TypeError est levée.
2. La classe API, qui sert d'interface à une API. Elle offre les fonctionnalités suivantes :

    - Stocker l'URL de base, le jeton, et les ressources liées à une instance de l'API.
    - Créer dynamiquement des méthodes pour les demandes GET, POST, PUT et DELETE en fonction des métadonnées de la ressource.
    - Valider les métadonnées de la ressource (c'est-à-dire, le nom de la ressource, le verbe HTTP, la méthode, et les paramètres) en utilisant un schéma JSON défini avec le module jsonschema. Une erreur sera consignée si les métadonnées ne correspondent pas au schéma.

3. La classe RequestResponse est utilisée pour stocker la réponse à une requête API. Elle inclut le code de statut de la requête et les données qui ont été renvoyées par celle-ci.

Voici une explication rapide des composants :

- type_check : Il s'agit d'une fonction décoratrice qui effectue une vérification de type sur chaque argument transmis à une fonction. La fonction décoratrice peut être appliquée à n'importe quelle fonction pour imposer des contraintes de type sur les arguments.
- API : C'est une classe de base abstraite qui représente une API générique. Elle met en œuvre la logique d'envoi de requêtes HTTP à une API et de traitement des réponses. Au sein de cette classe, les méthodes sont créées de manière dynamique pour les points de terminaison GET, POST, PUT et DELETE en fonction des métadonnées des ressources.
- set_method : C'est une méthode de la classe API. Elle détermine l'opération appropriée de l'API (verbe HTTP, comme GET, POST, PUT, DELETE) pour chaque ressource définie et décore la méthode avec le décorateur type_check, qui impose la vérification du type sur les arguments de la méthode.
- RequestResponse : Cette classe est utilisée pour stocker et accéder à la réponse d'une requête API. Elle comprend le code de statut HTTP et toutes les données renvoyées par la requête.

.. automodule:: api
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:
