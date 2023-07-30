Runner
===================================

Ce script Python est un gestionnaire pour exécuter diverses applications et API qui peuvent être intégrées à ce système. Il fournit des fonctionnalités de journalisation, de chargement d'applications et d'API, de suivi d'état et un environnement d'exécution pour ces applications. Il utilise massivement le multithreading pour permettre potentiellement l'exécution simultanée et le suivi de plusieurs applications.

La classe ``Runner`` est divisée en plusieurs parties :

1. Initialisation de la classe (``__init__``) : Initialise le Runner avec des attributs pour stocker les API et les applications, les indicateurs de débogage et de test, la configuration du logger, les événements de thread et le verrou pour le threading.

2. Configuration du logger (``__setup_logger``) : Cette méthode configure le logger pour le Runner, y compris un gestionnaire de fichiers et un gestionnaire de flux (console) en utilisant le module ``logging``.

3. Chargement des applications (``__load_applications``) : Cette méthode est chargée de charger les instances de chaque application à partir des sous-classes de ``application.Application``. Seules les sous-classes qui ne surchargent pas la méthode ``run`` mais qui surchargent la méthode ``job`` sont prises en compte. Leurs instances sont stockées et leur logger est configuré.

4. Chargement des API (``__load_apis``) : Cette méthode est chargée de charger les instances de chaque API à partir des sous-classes de ``api.API``, de les stocker et de configurer leur logger.

5. Suivi d'état (``__get_all_status`` et ``__status_thread``) : Ces méthodes sont utilisées pour obtenir l'état de toutes les applications individuellement ou dans un thread séparé de suivi d'état. Le thread de suivi d'état enregistre l'état de toutes les applications après l'avoir obtenu et déterminé le type de message correspondant (erreur, avertissement, débogage).

6. Détection de la surcharge de méthodes (``is_method_overridden``) : Cette méthode vérifie si une certaine méthode est surchargée dans les sous-classes d'une application donnée.

7. Exécution du module principal (``run``) : Cette méthode charge les API, charge les applications, puis exécute toutes les applications une fois si le drapeau de débogage est activé ou les programme pour qu'elles s'exécutent à leurs fréquences.

8. Arrêt (``shutdown``) : Cette méthode arrête le module principal.

L'implémentation utilise la bibliothèque externe ``schedule`` pour programmer des travaux (c'est-à-dire exécuter des instances d'application à intervalles réguliers).

Dans l'ensemble, ce script est un exemple assez complexe mais modulaire d'une application Python qui pourrait être utilisée pour exécuter et gérer plusieurs applications et API de manière robuste avec un soutien étendu à la journalisation et au suivi d'état.

.. automodule:: runner
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members: