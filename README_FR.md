# Document de Synthèse : Tableau de Bord Stratégique UCAR

Ce document dresse le bilan technique et fonctionnel de la plateforme d'aide à la décision développée pour la Présidence et la Vice-Présidence de l'Université de Carthage. Cet outil centralise les indicateurs stratégiques relatifs à l'académie, la recherche et l'employabilité.

## 1. Structuration des Données Stratégiques (ucar_strategic_data.json)

Une architecture de données JSON a été spécifiquement conçue pour isoler les mesures de performance institutionnelles. Les données de nature strictement opérationnelle (données financières, logistiques, ressources humaines classiques et critères environnementaux, sociaux et de gouvernance) ont été volontairement exclues du périmètre.

Les indicateurs conservés et modélisés couvrent les périmètres suivants :
- Employabilité : taux d'insertion professionnelle, durée moyenne d'accès à l'emploi et analyse des besoins en recrutement.
- Accréditation : statut réglementaire (accrédité, à l'étude ou non-accrédité), volumétrie globale des programmes et identification des formations présentant un risque de conformité.
- Recherche : évaluation chiffrée, recensement des publications académiques annuelles et suivi des projets de recherche en cours.
- Performance académique : statistiques de réussite et taux de redoublement par établissement.
- Cartographie des compétences : identification de l'expertise du corps professoral ainsi que des domaines d'enseignement majeurs et mineurs.

## 2. Interface Décisionnelle (app.py)

Une application web analytique a été programmée en Python, exploitant les bibliothèques Streamlit et Pandas. La plateforme est structurée en modules distincts facilitant l'analyse granulaire.

- Architecture de navigation et de filtrage : Un système de paramètres latéraux permet l'isolation des données selon trois axes (l'établissement, le niveau d'alerte et le statut d'accréditation).
- Indicateurs Clés de Performance (KPI) : L'écran de synthèse agrège les métriques globales au moyen de tableaux de bord quantitatifs (moyennes de réussite, volumétrie des publications, indicateurs de placement externe).
- Visualisation de données : L'application génère dynamiquement des représentations graphiques (diagrammes circulaires, histogrammes comparatifs et nuages de points multidimensionnels) afin de modéliser visuellement la corrélation entre différents indicateurs (par exemple : taux de réussite par rapport au redoublement pondéré par l'employabilité).
- Tableaux de données synchronisées : Une matrice de comparaison regroupe les performances institutionnelles pour une lecture rapide.

## 3. Système d'Alertes Algorithmiques

L'application intègre un moteur de règles automatisant l'identification des situations critiques. Des alertes directionnelles sont générées dès le franchissement de seuils de vulnérabilité définis, notamment :
- Risque d'employabilité évalué lorsque le taux d'insertion est inférieur à 70%.
- Risque de conformité institutionnelle lié aux statuts d'accréditation sous évaluation ou refusés.
- Performance de la recherche jugée fragile sous un score repère de 75.
- Risque académique signalé en deçà d'un taux de réussite global de 70%.
- Risque critique de rétention si le taux de redoublement excède 15%.

## 4. Intégration de l'Assistant Stratégique (Grok - xAI)

Le modèle d'intelligence artificielle Grok (fourni via l'API xAI) a été directement interconnecté au système d'information.  

Le flux d'intégration prend la forme suivante :
- Injection des variables de données : L'interface compile silencieusement l'état instantané du fichier JSON.
- Requête sécurisée : Le contexte macroéconomique des établissements de l'université est transmis au modèle.
- Interaction décisionnelle : Le moteur répond aux requêtes en langage naturel de la présidence (ex: "Quels sont les masters nécessitant une intervention face aux risques d'accréditation ?" ou "Listez les manques en matière de compétences pédagogiques."), en justifiant ses réponses exclusivement par les variables internes du système.

---

## Instructions d'Exécution

Pour amorcer le serveur applicatif local, exécutez la commande suivante à la racine du répertoire :

streamlit run app.py

L'interface sera accessible de façon standard ou sécurisée sur un navigateur à l'adresse locale (généralement http://localhost:8501).
