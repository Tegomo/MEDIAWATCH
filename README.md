# MediaWatch CI - Plateforme SaaS de Veille Médias

Plateforme de veille médias automatisée pour la Côte d'Ivoire. Surveillance de 50+ sources de presse avec analyse NLP (sentiment, entités, thématiques), alertes temps réel, et dashboard analytics.

## 🚀 Démarrage Rapide

### Prérequis

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**

### Installation (15 minutes)

#### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-org/mediawatch-ci.git
cd mediawatch-ci
```

#### 2. Configurer Supabase

**MediaWatch CI utilise Supabase pour la base de données et l'authentification.**

Suivre le guide détaillé : **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)**

Résumé rapide :
1. Créer un projet sur https://supabase.com
2. Récupérer les clés API (URL, anon key, service key)
3. Configurer `backend/.env` et `frontend/.env.local`
4. Appliquer les migrations : `alembic upgrade head`

**Optionnel** : Pour Redis local (tâches Celery) :
```bash
cd infrastructure
docker-compose up -d redis
```

#### 3. Configuration Backend

```bash
cd backend

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Configurer variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API (Supabase, SendGrid, Stripe)

# Créer les tables de base de données
alembic upgrade head

# (Optionnel) Charger données de test
python scripts/seed_data.py
```

#### 4. Lancer Backend

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

API disponible sur : http://localhost:8000  
Documentation interactive : http://localhost:8000/docs

#### 5. Configuration Frontend

```bash
cd frontend

# Installer dépendances
npm install

# Configurer variables d'environnement
cp .env.example .env.local
# Éditer .env.local avec vos clés API
```

#### 6. Lancer Frontend

```bash
cd frontend
npm run dev
```

Application disponible sur : http://localhost:5173

#### 7. Vérification

1. Ouvrir http://localhost:5173
2. Créer un compte test
3. Ajouter un mot-clé (ex: "Orange CI")
4. Vérifier que le dashboard s'affiche

✅ **Installation complète !**

## 📁 Structure du Projet

```
mediawatch-ci/
├── backend/                 # API FastAPI
│   ├── src/
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Logique métier
│   │   ├── api/            # Routes FastAPI
│   │   ├── workers/        # Celery tasks
│   │   └── db/             # Migrations Alembic
│   └── tests/
├── frontend/                # React + Vite
│   ├── src/
│   │   ├── components/     # Composants React
│   │   ├── pages/          # Pages/routes
│   │   └── services/       # API clients
│   └── tests/
├── infrastructure/          # Docker, scripts
└── specs/                   # Documentation design
```

## 🛠️ Commandes Utiles

### Backend

```bash
# Lancer API
uvicorn src.main:app --reload

# Lancer Celery worker
celery -A src.workers.celery_app worker --loglevel=info

# Lancer Celery beat (scheduler)
celery -A src.workers.celery_app beat --loglevel=info

# Créer migration DB
alembic revision --autogenerate -m "description"

# Appliquer migrations
alembic upgrade head

# Tests
pytest tests/

# Linting
black .
flake8
```

### Frontend

```bash
# Dev server
npm run dev

# Build production
npm run build

# Tests
npm run test

# Linting
npm run lint
npm run format
```

### Docker

```bash
# Démarrer services
docker-compose up -d

# Voir logs
docker-compose logs -f postgres

# Arrêter services
docker-compose down
```

## 🎯 Technologies Clés

| Composant | Technologie | Pourquoi |
|-----------|-------------|----------|
| **Backend API** | FastAPI | Performance, async, OpenAPI auto |
| **Frontend** | React + Vite | Écosystème riche, hot-reload rapide |
| **Database** | PostgreSQL (Supabase) | Relations complexes, full-text search |
| **Auth** | Supabase Auth | JWT, social login, RLS intégré |
| **Queue** | Celery + Redis | Tâches async (scraping, NLP) |
| **Scraping** | Scrapy + Playwright | Hybride static/dynamic sites |
| **NLP** | spaCy + CamemBERT | Français, fine-tunable |
| **Email** | SendGrid | Deliverability 99.9% |
| **Paiements** | Stripe + Orange Money | International + local CI |
| **UI** | TailwindCSS + shadcn/ui | Moderne, composants prêts |

## 📚 Documentation

- **Spécification complète** : [specs/001-mediawatch-saas-platform/spec.md](specs/001-mediawatch-saas-platform/spec.md)
- **Plan d'implémentation** : [specs/001-mediawatch-saas-platform/plan.md](specs/001-mediawatch-saas-platform/plan.md)
- **Schéma DB** : [specs/001-mediawatch-saas-platform/data-model.md](specs/001-mediawatch-saas-platform/data-model.md)
- **API OpenAPI** : [specs/001-mediawatch-saas-platform/contracts/api.openapi.yaml](specs/001-mediawatch-saas-platform/contracts/api.openapi.yaml)
- **Guide démarrage** : [specs/001-mediawatch-saas-platform/quickstart.md](specs/001-mediawatch-saas-platform/quickstart.md)
- **Tâches** : [specs/001-mediawatch-saas-platform/tasks.md](specs/001-mediawatch-saas-platform/tasks.md)

## 🔐 Configuration Requise

### Comptes Nécessaires

1. **Supabase** (gratuit) : https://supabase.com
   - Créer projet
   - Obtenir URL et clés API
   - Configurer auth

2. **SendGrid** (100K emails/mois gratuits) : https://sendgrid.com
   - Obtenir clé API
   - Vérifier domaine expéditeur

3. **Stripe** (mode test gratuit) : https://stripe.com
   - Obtenir clés test
   - Configurer webhooks

4. **Orange Money** (optionnel pour dev) : https://developer.orange.com
   - Obtenir clés API CI

## 🚦 Statut du Projet

- ✅ Phase 1: Setup - **COMPLÉTÉ**
- 🔄 Phase 2: Fondations - **EN COURS**
- ⏳ Phase 3-5: User Stories P1 (MVP) - **À VENIR**
- ⏳ Phase 6: Infrastructure Scraping/NLP - **À VENIR**
- ⏳ Phase 7-13: Features P2/P3 + Polish - **À VENIR**

## 📈 Métriques Cibles

- Dashboard : <2s chargement sur 3G
- Alertes email : <5min après détection
- Scraping : 50+ sources toutes les 30min-1h
- API : <200ms p95 pour endpoints dashboard
- NLP : >85% précision sentiment
- Uptime : 99.5% sur périodes 30 jours

## 🤝 Contribution

1. Créer branche feature depuis main
2. Développer avec TDD
3. Linter et formatter
4. Commit et push
5. Créer Pull Request

## 📝 Licence

Propriétaire - MediaWatch CI © 2026

## 💬 Support

- Issues : GitHub Issues
- Email : support@mediawatch.ci
