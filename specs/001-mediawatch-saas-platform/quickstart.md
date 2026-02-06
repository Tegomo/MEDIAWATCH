# Guide de Démarrage Rapide : MediaWatch CI

**Feature** : MediaWatch CI - Plateforme SaaS de Veille Médias  
**Date** : 5 février 2026  
**Audience** : Développeurs rejoignant le projet

## Vue d'Ensemble

MediaWatch CI est une plateforme SaaS de veille médias pour la Côte d'Ivoire. Ce guide vous permet de configurer votre environnement de développement et de comprendre l'architecture en 30 minutes.

## Prérequis

### Outils Requis

- **Python 3.11+** : Backend FastAPI
- **Node.js 18+** : Frontend React
- **Docker & Docker Compose** : Services locaux (PostgreSQL, Redis)
- **Git** : Contrôle de version
- **VS Code** (recommandé) avec extensions :
  - Python
  - ESLint
  - Prettier
  - REST Client

### Comptes Nécessaires

- **Supabase** : Auth et base de données (tier gratuit)
- **SendGrid** : Emails (100K gratuits/mois)
- **Stripe** : Paiements test (mode test gratuit)

## Installation Rapide (15 min)

### 1. Cloner le Dépôt

```bash
git clone https://github.com/votre-org/mediawatch-ci.git
cd mediawatch-ci
git checkout 001-mediawatch-saas-platform
```

### 2. Configuration Backend

```bash
cd backend

# Créer environnement virtuel Python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Copier fichier env
cp .env.example .env
```

**Éditer `.env`** :
```bash
# Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_ANON_KEY=votre_anon_key
SUPABASE_SERVICE_KEY=votre_service_key

# Database (local via Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mediawatch

# Redis
REDIS_URL=redis://localhost:6379/0

# SendGrid
SENDGRID_API_KEY=votre_api_key
SENDGRID_FROM_EMAIL=noreply@mediawatch.ci

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Orange Money (optionnel pour dev)
ORANGE_MONEY_API_KEY=
ORANGE_MONEY_MERCHANT_KEY=
```

### 3. Démarrer Services Locaux

```bash
# Depuis la racine du projet
docker-compose up -d

# Vérifier que PostgreSQL et Redis sont up
docker-compose ps
```

### 4. Migrations Base de Données

```bash
cd backend

# Créer les tables
alembic upgrade head

# Seed données de test (optionnel)
python scripts/seed_data.py
```

### 5. Lancer Backend

```bash
cd backend

# Mode développement avec hot-reload
uvicorn src.main:app --reload --port 8000

# API disponible sur http://localhost:8000
# Docs interactives : http://localhost:8000/docs
```

### 6. Configuration Frontend

```bash
cd frontend

# Installer dépendances
npm install

# Copier fichier env
cp .env.example .env.local
```

**Éditer `.env.local`** :
```bash
VITE_API_URL=http://localhost:8000/v1
VITE_SUPABASE_URL=https://votre-projet.supabase.co
VITE_SUPABASE_ANON_KEY=votre_anon_key
```

### 7. Lancer Frontend

```bash
cd frontend

# Mode développement
npm run dev

# Application disponible sur http://localhost:5173
```

### 8. Vérification Installation

Ouvrir http://localhost:5173 et :
1. Créer un compte test
2. Ajouter un mot-clé (ex: "Orange CI")
3. Vérifier que le dashboard s'affiche

✅ **Installation complète !**

---

## Architecture du Projet

### Structure des Répertoires

```
mediawatch-ci/
├── backend/                    # API FastAPI
│   ├── src/
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Logique métier
│   │   │   ├── scraping/      # Scrapers par source
│   │   │   ├── nlp/           # Analyse NLP
│   │   │   ├── alerts/        # Système alertes
│   │   │   └── exports/       # Génération CSV/PDF
│   │   ├── api/               # Routes FastAPI
│   │   ├── workers/           # Celery tasks
│   │   └── db/                # Migrations Alembic
│   ├── tests/
│   └── requirements.txt
│
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── components/        # Composants React
│   │   ├── pages/             # Pages/routes
│   │   ├── services/          # API clients
│   │   └── lib/               # Utilitaires
│   ├── tests/
│   └── package.json
│
├── infrastructure/
│   ├── docker-compose.yml     # Services dev local
│   └── scripts/               # Scripts déploiement
│
└── specs/                      # Documentation design
    └── 001-mediawatch-saas-platform/
        ├── spec.md            # Spécification fonctionnelle
        ├── plan.md            # Plan d'implémentation
        ├── research.md        # Décisions techniques
        ├── data-model.md      # Schéma DB
        └── contracts/         # Contrats API
```

### Flux de Données Principal

```
1. SCRAPING (Celery Beat toutes les 30min)
   └─> Scrapers → Articles → DB

2. NLP PROCESSING (Celery worker)
   └─> Articles → spaCy/Transformers → Sentiment/Entités → DB

3. MENTION DETECTION (Celery worker)
   └─> Articles × Keywords → Mentions → DB

4. ALERTS (Celery worker)
   └─> Mentions négatives → Batching → SendGrid → Email

5. USER DASHBOARD (API REST)
   └─> Frontend → API → PostgreSQL → JSON → Frontend
```

### Technologies Clés

| Composant | Technologie | Pourquoi |
|-----------|-------------|----------|
| **Backend API** | FastAPI | Performance, async, OpenAPI auto |
| **Frontend** | React + Vite | Écosystème riche, hot-reload rapide |
| **Database** | PostgreSQL (Supabase) | Relations complexes, full-text search |
| **Auth** | Supabase Auth | JWT, social login, RLS intégré |
| **Queue** | Celery + Redis | Tâches async (scraping, NLP) |
| **Scraping** | Scrapy + Playwright | Hybride static/dynamic sites |
| **NLP** | spaCy + CamemBERT | Français, fine-tunable |
| **Email** | SendGrid | Deliverability 99.9%, tracking |
| **Paiements** | Stripe + Orange Money | International + local CI |
| **UI** | TailwindCSS + shadcn/ui | Moderne, composants prêts |

---

## Workflows de Développement

### Créer une Nouvelle Feature

```bash
# 1. Créer branche depuis main
git checkout main
git pull
git checkout -b feature/nom-feature

# 2. Développer avec TDD
# - Écrire tests d'abord (tests/unit/, tests/integration/)
# - Implémenter fonctionnalité
# - Vérifier tests passent

# 3. Linter et formatter
cd backend && black . && flake8
cd frontend && npm run lint && npm run format

# 4. Commit et push
git add .
git commit -m "feat: description de la feature"
git push origin feature/nom-feature

# 5. Créer Pull Request sur GitHub
```

### Ajouter un Nouveau Scraper

**Exemple** : Ajouter scraper pour "Nouveau Média CI"

```python
# backend/src/services/scraping/sources/nouveau_media.py
from ..base import MediaScraper
from bs4 import BeautifulSoup

class NouveauMediaScraper(MediaScraper):
    """Scraper pour Nouveau Média CI (site statique)"""
    
    source_name = "Nouveau Média CI"
    base_url = "https://nouveaumedia.ci"
    
    async def scrape(self) -> List[Article]:
        # 1. Fetch page liste articles
        html = await self.fetch_page(f"{self.base_url}/actualites")
        soup = BeautifulSoup(html, 'html.parser')
        
        # 2. Extraire URLs articles
        article_links = soup.select('.article-card a')
        
        articles = []
        for link in article_links[:20]:  # Limiter à 20 derniers
            article_url = link['href']
            
            # 3. Fetch article complet
            article_html = await self.fetch_page(article_url)
            article = self.parse_article(article_html, article_url)
            
            if article:
                articles.append(article)
        
        return articles
    
    def parse_article(self, html: str, url: str) -> Optional[Article]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Adapter sélecteurs CSS selon structure site
        title = soup.select_one('h1.article-title').text.strip()
        content = soup.select_one('.article-content').text.strip()
        date_str = soup.select_one('.publish-date').text.strip()
        
        return Article(
            title=title,
            url=url,
            raw_content=html,
            cleaned_content=content,
            published_at=self.parse_date(date_str),
            source_id=self.source_id
        )
```

**Enregistrer le scraper** :
```python
# backend/src/services/scraping/registry.py
from .sources.nouveau_media import NouveauMediaScraper

SCRAPERS = {
    'fraternite_matin': FraterniteMatin,
    'abidjan_net': AbidjanNet,
    'nouveau_media': NouveauMediaScraper,  # Ajouter ici
}
```

**Ajouter en DB** :
```sql
INSERT INTO sources (name, url, type, scraper_class, scraping_enabled)
VALUES ('Nouveau Média CI', 'https://nouveaumedia.ci', 'press', 'nouveau_media', true);
```

### Tester Localement

```bash
# Tests unitaires
cd backend
pytest tests/unit/

# Tests intégration
pytest tests/integration/

# Tests E2E
cd frontend
npm run test:e2e

# Test scraper spécifique
python -m src.services.scraping.sources.nouveau_media
```

---

## Commandes Utiles

### Backend

```bash
# Lancer API
uvicorn src.main:app --reload

# Lancer Celery worker (scraping, NLP, alertes)
celery -A src.workers.celery_app worker --loglevel=info

# Lancer Celery beat (scheduler)
celery -A src.workers.celery_app beat --loglevel=info

# Créer migration DB
alembic revision --autogenerate -m "description"

# Appliquer migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Shell interactif
python -m src.shell
```

### Frontend

```bash
# Dev server
npm run dev

# Build production
npm run build

# Preview build
npm run preview

# Linter
npm run lint

# Tests
npm run test
```

### Docker

```bash
# Démarrer services
docker-compose up -d

# Voir logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Arrêter services
docker-compose down

# Reset complet (⚠️ perte données)
docker-compose down -v
```

---

## Debugging

### Backend API

**Activer logs détaillés** :
```python
# backend/src/config.py
LOG_LEVEL = "DEBUG"
```

**Breakpoint Python** :
```python
import pdb; pdb.set_trace()
```

**Logs Celery** :
```bash
celery -A src.workers.celery_app worker --loglevel=debug
```

### Frontend React

**React DevTools** : Extension Chrome/Firefox

**Logs API calls** :
```typescript
// frontend/src/services/api.ts
axios.interceptors.request.use(request => {
  console.log('API Request:', request);
  return request;
});
```

### Base de Données

**Connexion psql** :
```bash
docker exec -it mediawatch-postgres psql -U postgres -d mediawatch
```

**Requêtes utiles** :
```sql
-- Voir dernières mentions
SELECT m.*, k.text, a.title 
FROM mentions m
JOIN keywords k ON k.id = m.keyword_id
JOIN articles a ON a.id = m.article_id
ORDER BY m.detected_at DESC
LIMIT 10;

-- Statut scraping sources
SELECT name, last_success_at, consecutive_failures
FROM sources
WHERE scraping_enabled = true
ORDER BY consecutive_failures DESC;
```

---

## Ressources

### Documentation

- **Spec complète** : `specs/001-mediawatch-saas-platform/spec.md`
- **Décisions techniques** : `specs/001-mediawatch-saas-platform/research.md`
- **Schéma DB** : `specs/001-mediawatch-saas-platform/data-model.md`
- **API OpenAPI** : http://localhost:8000/docs (après lancement backend)

### Liens Externes

- **FastAPI** : https://fastapi.tiangolo.com/
- **React** : https://react.dev/
- **Supabase** : https://supabase.com/docs
- **spaCy** : https://spacy.io/usage
- **Celery** : https://docs.celeryq.dev/

### Support

- **Slack** : #mediawatch-dev
- **Issues** : GitHub Issues
- **Wiki** : Confluence (lien interne)

---

## Prochaines Étapes

Après avoir configuré votre environnement :

1. **Lire la spec** : `specs/001-mediawatch-saas-platform/spec.md`
2. **Explorer le code** : Commencer par `backend/src/main.py` et `frontend/src/App.tsx`
3. **Lancer les tests** : Vérifier que tout passe
4. **Choisir une tâche** : Voir `specs/001-mediawatch-saas-platform/tasks.md` (après génération)
5. **Demander aide** : N'hésitez pas sur Slack !

Bienvenue dans l'équipe MediaWatch CI ! 🚀
