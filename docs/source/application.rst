Application
===================================

Définit une classe de base abstraite (`ABC`) pour représenter une Application exécutable et une énumération `Status` pour suivre l'état actuel d'une Application.

- L'énumération `Status` contient les différents statuts qu'une application peut avoir, tels que `RUNNING`, `WAITING`, `ERROR`, et `SUCCESS`.

- La classe `Application` est une classe de base abstraite (ne peut pas être instanciée directement). Elle fournit un modèle pour créer d'autres classes qui sont considérées comme des Applications, ce qui signifie qu'elles doivent implémenter les méthodes spécifiées dans cette classe abstraite. Cette classe met en place la journalisation et initialise diverses propriétés telles que les APIs, la fréquence d'exécution, et le statut.

- La méthode `api()` récupère une instance API à partir de la liste privée `_apis` en fonction de son nom de classe.

- La méthode `run()` est utilisée pour exécuter l'application. Elle définit le statut comme `RUNNING` et essaie ensuite d'appeler la méthode abstraite `job()`. Si une exception se produit pendant ce processus, elle enregistre l'erreur et définit le statut comme `ERROR`. Si le mode de débogage est activé, elle relève à nouveau l'exception.

- La méthode `shutdown()` est un espace réservé qui peut être remplacé par des implémentations de sous-classe si l'Application a besoin de libérer des ressources ou d'effectuer des actions de nettoyage lorsqu'elle est arrêtée. Si elle n'est pas remplacée, elle ne fait rien.

- Ce script utilise également les bibliothèques `schedule` et `logging` pour la planification des tâches et la création de journaux d'application, respectivement.

.. automodule:: application
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:
