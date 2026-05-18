# 🇬🇳 Chatbot L0027 - Statut des Agents de l'État

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

**Assistant IA intelligent pour la Loi L/2019/0027/AN portant Statut Général des Agents de l'État de la République de Guinée**

---

## 📋 Table des matières

- [Présentation](#-présentation)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Démarrage](#-démarrage)
- [Utilisation de l'API](#-utilisation-de-lapi)
- [Développement](#-développement)
- [Déploiement](#-déploiement)

---

## 🎯 Présentation

Le **Chatbot L0027** est un assistant juridique intelligent développé pour aider les agents de l'État guinéen, les gestionnaires RH et toute personne souhaitant comprendre le **Statut Général des Agents de l'État**.

### Caractéristiques principales

- 🤖 **Multi-LLM** : Support OpenAI GPT-4, Anthropic Claude, DeepSeek
- 🔍 **RAG** (Retrieval-Augmented Generation) pour des réponses précises
- ⚡ **Cache Redis** pour des temps de réponse ultra-rapides
- 📊 **225 articles** de loi indexés
- 💡 **Suggestions intelligentes** de questions
- 🔒 **Sécurisé** et conforme aux standards professionnels

---

## ✨ Fonctionnalités

### Pour les utilisateurs
- ❓ Poser des questions en langage naturel
- 📚 Obtenir des réponses basées sur les articles de loi
- 💡 Recevoir des suggestions de questions connexes
- 🔍 Rechercher dans les articles par thème
- 📖 Consulter des articles spécifiques

### Pour les administrateurs
- 📊 Statistiques d'utilisation
- 🗑️ Gestion du cache
- 🔧 Monitoring de santé des services
- 📈 Analytics des questions populaires

---

## 🚀 Installation

### Option 1 : Docker (Recommandé)

**Pour le développement :**

```bash
# Cloner le projet
git clone https://github.com/votre-repo/chatbot-l0027.git
cd chatbot-l0027

# Copier la configuration
cp .env.example .env

# Éditer les variables d'environnement
nano .env

# Démarrer les services (mode développement)
docker compose -f docker-compose.dev.yml up -d

# Vérifier les logs
docker compose -f docker-compose.dev.yml logs -f chatbot
```

**Pour la production :**

```bash
# Voir PRODUCTION.md pour les instructions complètes
docker compose --profile production up -d
```

### Option 2 : Installation manuelle

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Copier la configuration
cp .env.example .env
nano .env  # Configurer les variables

# Démarrer les services externes (PostgreSQL, Redis, Qdrant)
# ...

# Initialiser la base de données
python -c "from app.db.database import init_db; import asyncio; asyncio.run(init_db())"

# Indexer les données
python scripts/index_data.py

# Démarrer l'application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ⚙️ Configuration

### Variables d'environnement principales

| Variable | Description | Défaut |
|----------|-------------|--------|
| `OPENAI_API_KEY` | Clé API OpenAI | - |
| `ANTHROPIC_API_KEY` | Clé API Anthropic | - |
| `DEEPSEEK_API_KEY` | Clé API DeepSeek | - |
| `DEFAULT_LLM_PROVIDER` | Provider par défaut | `openai` |
| `POSTGRES_HOST` | Hôte PostgreSQL | `localhost` |
| `REDIS_HOST` | Hôte Redis | `localhost` |
| `QDRANT_HOST` | Hôte Qdrant | `localhost` |

Voir `.env.example` pour la liste complète.

---

## 🎮 Démarrage

### Avec Docker

**Mode développement (ports exposés) :**

```bash
# Démarrage complet
docker compose -f docker-compose.dev.yml up -d

# Avec les outils d'admin (pgAdmin, Redis Commander)
docker compose -f docker-compose.dev.yml --profile tools up -d

# Arrêt
docker compose -f docker-compose.dev.yml down

# Voir DEVELOPMENT.md pour plus de détails
```

**Mode production (avec Traefik) :**

```bash
# Démarrage avec Traefik reverse proxy
docker compose --profile production up -d

# Voir PRODUCTION.md pour les instructions complètes
```

### Sans Docker

```bash
# Activer l'environnement
source venv/bin/activate

# Démarrer
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Mode développement (avec rechargement automatique)
uvicorn app.main:app --reload
```

---

## 📡 Utilisation de l'API

### Endpoint principal : Poser une question

```bash
POST /api/v1/ask
Content-Type: application/json

{
    "question": "Quel est l'âge de la retraite pour un fonctionnaire ?",
    "session_id": "optionnel-session-id",
    "llm_provider": "openai",
    "include_suggestions": true
}
```

**Réponse :**
```json
{
    "response_id": "uuid",
    "question": "Quel est l'âge de la retraite pour un fonctionnaire ?",
    "answer": "Selon l'article 116 de la loi L/2019/0027/AN, l'âge limite de mise à la retraite est fixé à :\n- 60 ans pour les hiérarchies B1, B2, C et les contractuels permanents\n- 65 ans pour les hiérarchies A1, A2 et A3\n- 70 ans pour les professeurs de rang magistral",
    "articles_references": [
        {
            "numero": 116,
            "contenu": "...",
            "theme_principal": "age_retraite",
            "score": 0.95
        }
    ],
    "suggested_questions": [
        {"question": "Comment fonctionne la pension proportionnelle ?"},
        {"question": "Quels sont les droits à la retraite après 15 ans de service ?"}
    ],
    "confidence_score": 0.92,
    "llm_provider": "openai",
    "processing_time_ms": 1250,
    "cached": false
}
```

### Autres endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/v1/search/articles?query=...` | Rechercher des articles |
| `GET` | `/api/v1/articles/{numero}` | Obtenir un article |
| `GET` | `/api/v1/suggestions/popular` | Questions populaires |
| `GET` | `/api/v1/suggestions/starter` | Questions de démarrage |
| `GET` | `/api/v1/categories` | Liste des catégories |
| `GET` | `/api/v1/law/info` | Informations sur la loi |
| `POST` | `/api/v1/feedback` | Soumettre un feedback |
| `GET` | `/health` | État du système |

### Documentation interactive

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

---

## 🧪 Développement

### Tests

```bash
# Exécuter tous les tests
pytest

# Avec couverture
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_api.py -v
```

### Linting

```bash
# Format du code
black app/ scripts/ tests/

# Tri des imports
isort app/ scripts/ tests/

# Vérification du style
flake8 app/ scripts/ tests/

# Type checking
mypy app/
```

### Structure du projet

```
chatbot_l0027/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # Routes FastAPI
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Configuration
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py        # Connexion PostgreSQL
│   │   └── models.py          # Modèles SQLAlchemy
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Schémas Pydantic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache_service.py   # Service Redis
│   │   ├── llm_service.py     # Service LLM
│   │   ├── rag_service.py     # Service RAG
│   │   └── vector_service.py  # Service Qdrant
│   ├── utils/
│   │   └── __init__.py
│   └── main.py                # Application FastAPI
├── data/
│   ├── loi_L0027_enrichie.json
│   └── qa_entrainement_L0027.json
├── scripts/
│   ├── __init__.py
│   └── index_data.py          # Indexation Qdrant
├── tests/
│   └── __init__.py
├── .env.example
├── docker-compose.prod.yml     # Production (avec Traefik)
├── docker-compose.dev.yml     # Développement (ports exposés)
├── docker-compose.traefik.yml # Traefik (séparé)
├── Dockerfile
├── requirements.txt
├── DEVELOPMENT.md              # Guide de développement
├── PRODUCTION.md               # Guide de déploiement
├── traefik/
│   ├── traefik.yml            # Configuration Traefik
│   └── dynamic.yml            # Configuration dynamique
└── README.md
```

---

## 🚢 Déploiement

### Déploiement en production

1. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   # Éditer avec les valeurs de production
   ```

2. **Sécuriser les secrets**
   - Utiliser un gestionnaire de secrets (Vault, AWS Secrets Manager, etc.)
   - Ne jamais commiter les clés API

3. **Démarrer avec Docker Compose**

   **Développement :**
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

   **Production :**
   ```bash
   docker compose --profile production up -d
   ```

4. **Configurer un reverse proxy** (Traefik déjà configuré)
   - SSL/TLS automatique via Let's Encrypt
   - Rate limiting
   - Headers de sécurité
   - Voir PRODUCTION.md pour les détails

### Monitoring

- **Health check** : `GET /health`
- **Readiness** : `GET /ready`
- **Métriques** : Prometheus (optionnel)

---

## 📞 Support

Pour toute question ou assistance :

- **Division FUGAS** - Direction Générale de la Fonction Publique
- **Ministère du Travail et de la Fonction Publique**
- République de Guinée 🇬🇳

---

## 📜 Licence

Ce logiciel est la propriété du Ministère de la Fonction Publique de la République de Guinée.

---

**Développé avec ❤️ pour la fonction publique guinéenne**
