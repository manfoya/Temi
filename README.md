
# Plateforme Temi : Système de Suivi Académique et d'Orientation par IA

## Description du Projet

Temi est une solution logicielle conçue pour l'École Nationale de la Statistique, de la Planification et de la Démographie (ENSPD). Elle vise à moderniser la gestion du cursus LMD (Licence-Master-Doctorat) en y intégrant une couche d'intelligence artificielle dédiée à l'orientation professionnelle.

Contrairement aux systèmes de gestion classiques (type Okapi) qui se limitent à l'archivage administratif des notes, Temi exploite les données académiques pour fournir un diagnostic de compétences en temps réel et des recommandations personnalisées alignées sur les objectifs de carrière de l'étudiant.

**État du projet :** Prototype Fonctionnel (Module 1 d'IA intégré).

## Fonctionnalités Implémentées

### 1. Gestion Académique (LMD)
*   **Modélisation Structurelle :** Gestion hiérarchique des Filières, Classes, Unités d'Enseignement (UE) et Éléments Constitutifs (ECUE).
*   **Moteur de Calcul LMD :** Algorithme de calcul des moyennes pondérées respectant les règles de l'ENSPD (Pondération des types d'évaluation : Devoirs vs Examens, Coefficients UE, Crédits).
*   **Gestion des Identités :** Séparation stricte entre l'identité pérenne de l'étudiant (Matricule) et ses inscriptions annuelles (cursus).

### 2. Module d'Intelligence Artificielle (Niveau 1)
Actuellement, la plateforme intègre la première brique du moteur d'IA : le **Diagnostic de Carrière**.
*   **Cartographie des Compétences :** Liaison relationnelle entre les formations académiques (ECUE) et les compétences requises par le marché (ex: Python, SQL pour un Data Scientist).
*   **Analyse Algorithmique :** Détection automatique des écarts (Gap Analysis) entre les compétences acquises par l'étudiant (via ses notes) et les pré-requis de son métier cible.
*   **Coaching Génératif :** Interfaçage avec le modèle **Google Gemini 2.0** pour transformer les données analytiques en conseils pédagogiques contextualisés et bienveillants.

### 3. Administration
*   Importation en masse des étudiants et inscriptions via fichiers CSV/Excel.
*   Configuration des modalités d'évaluation et des coefficients.

## Architecture Technique

Le projet suit une architecture modulaire basée sur le framework **FastAPI** (Python), favorisant la maintenabilité et l'évolutivité.

### Arborescence du Projet

```text
Temi/
├── app/
│   ├── api/                 # Contrôleurs API (Routes)
│   │   └── v1/
│   │       ├── academic.py  # Gestion structurelle (Filières, Classes)
│   │       ├── advisor.py   # Endpoints du module IA
│   │       ├── auth.py      # Authentification
│   │       ├── career.py    # Gestion des carrières et compétences
│   │       ├── grades.py    # Saisie des notes et bulletins
│   │       ├── pedagogy.py  # Gestion des UE/ECUE
│   │       ├── students.py  # Gestion des étudiants
│   │       └── users.py     # Gestion des utilisateurs système
│   ├── core/                # Configuration globale
│   │   ├── database.py      # Connexion BDD (SQLAlchemy)
│   │   └── security.py      # Hachage et sécurité
│   ├── models/              # Modèles de données (ORM)
│   │   ├── academic.py      # Tables Année, Filière, Classe
│   │   ├── career.py        # Tables Domaine, Skill et Liaisons
│   │   ├── grade.py         # Table Notes
│   │   ├── pedagogy.py      # Tables UE, ECUE, Evaluation
│   │   └── user.py          # Tables User, Enrollment
│   ├── schemas/             # Schémas de validation (Pydantic)
│   └── services/            # Logique métier complexe
│       ├── ai_advisor.py    # Moteur de diagnostic et client Gemini
│       ├── calculator.py    # Algorithmes de calcul de moyennes
│       └── importer.py      # Service d'import Excel/CSV
├── .env                     # Variables d'environnement (Clés API)
├── main.py                  # Point d'entrée de l'application
└── requirements.txt         # Dépendances Python
```

## Installation et Déploiement

### Pré-requis
*   Python 3.10 ou version supérieure.
*   Une clé API Google AI Studio valide (pour le module IA).

### Procédure d'installation

1.  **Cloner le dépôt :**
    ```bash
    git clone https://github.com/manfoya/Temi.git
    cd Temi
    ```

2.  **Configurer l'environnement virtuel :**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Linux/Mac
    # ou venv\Scripts\activate sur Windows
    ```

3.  **Installer les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration :**
    Créez un fichier `.env` à la racine et ajoutez votre clé :
    ```env
    GOOGLE_API_KEY=votre_cle_ici
    ```

### Initialisation de la Base de Données

Un script de démonstration est fourni pour peupler la base de données avec un scénario complet (École, Matières, Compétences, Étudiant, Notes).

```bash
# 1. Lancer le serveur pour créer la structure des tables
uvicorn app.main:app --reload
# (Une fois le serveur démarré, l'arrêter avec CTRL+C)

# 2. Exécuter le script de remplissage
python seed_full_demo.py
```

### Lancement

```bash
uvicorn app.main:app --reload
```
L'interface de documentation (Swagger UI) est accessible à l'adresse : `http://127.0.0.1:8000/docs`

---

## Auteurs
**Martial TCHOKPON**
Projet académique pour l'ENSPD.

---
