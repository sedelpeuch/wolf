Notion2LaTeX - Compilation des pages Notion
===========================================

Le module **Notion2Latex** est un utilitaire servant à interagir avec l'API Notion et à compiler les pages Notion en fichiers LaTeX puis les publier sur Github en tant que pdf.

Fonctionnement
--------------

Le module utilise une integration Notion (voir https://www.notion.so/my-integrations).

Il récupère ensuite l'identifiant de la page Notion principale et trouve les sous pages qui seront envoyées à la tâche Notion2Latex.

Il récupère aussi un template LaTeX sur un dépôt Github. Le template doit contenir un fichier `src/template.tex` que le module va remplir avec les données de la page Notion.
Le template doit prendre en entrée à minima les champs "client", "titre", "phase_id", "phase_nom"

Chaque page à compiler doit **obligatoirement** contenir un header avec les champs nécessaires au template LaTeX. À minima, le header doit contenir les champs "client", "titre", "phase_id", "phase_nom".

.. code-block:: markdown

    ---
    client: Quelqu’un
    titre: Un projet
    phase_id: 1
    phase_nom: État de l'art
    ---

Le résultat de la compilation est un fichier pdf qui est publié sur le dépôt Github.

Token
-----

Le token d'intégration Notion doit être fourni à Wolf sous le nom "notion"

L'identifiant de la page Notion principale doit être fourni à Wolf sous le nom "notion_master_file".

Le token ayant les droits en écriture sur le dépôt github doit être fourni à Wolf sous le nom "github_doc_publish".

Le token ayant les droits en lecture sur le dépôt github servant de template latex doit être fourni à Wolf sous le nom "github_doc_latex".

-----------------

.. automodule:: notion_latex
   :members:
   :undoc-members:
   :show-inheritance:
   :private-members:
