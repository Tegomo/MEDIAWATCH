# Plan d'Implémentation : MediaWatch CI - Plateforme SaaS de Veille Médias

**Branche** : `001-mediawatch-saas-platform` | **Date** : 5 février 2026 | **Spec** : [spec.md](./spec.md)
**Input** : Spécification fonctionnelle depuis `/specs/001-mediawatch-saas-platform/spec.md`

**Note** : Ce plan est généré par la commande `/speckit.plan`. Voir `.specify/templates/commands/plan.md` pour le workflow d'exécution.

## Résumé

MediaWatch CI est une plateforme SaaS de veille médias pour la Côte d'Ivoire permettant aux agences de communication et entreprises de surveiller automatiquement leurs mentions dans 50+ sources de presse ivoiriennes. La plateforme automatise le scraping multi-sources, l'analyse NLP (sentiment, entités, thématiques), les alertes temps réel par email, et fournit un dashboard analytics avec export CSV/PDF. L'objectif est de réduire les coûts de veille manuelle de 93% (de 3M FCFA/mois à 300K FCFA/mois) tout en améliorant la réactivité avec des alertes sous 5 minutes.

## Contexte Technique

**Language/Version** : Python 3.11+ (backend), TypeScript/JavaScript (frontend React)  
**Primary Dependencies** :
- Backend : FastAPI, Supabase (auth/DB), spaCy/Transformers (NLP), BeautifulSoup/Scrapy (scraping), Celery (tâches async)
- Frontend : React 18+, TailwindCSS, shadcn/ui, Recharts (visualisations)
- Paiements : Stripe API, Orange Money API (NEEDS CLARIFICATION - intégration spécifique CI)

**Storage** : PostgreSQL via Supabase (données structurées), Redis (cache/queues), S3-compatible (exports PDF/CSV)  
**Testing** : pytest (backend), Jest/React Testing Library (frontend), Playwright (E2E)  
**Target Platform** : Web application (responsive mobile-first), déploiement cloud (Vercel frontend + backend containerisé)  
**Project Type** : Web (frontend + backend séparés)  
**Performance Goals** :
- Dashboard : <2s chargement sur 3G
- Alertes email : <5min après détection
- Scraping : 50+ sources toutes les 30min-1h
- API : <200ms p95 pour endpoints dashboard
- NLP : >85% précision sentiment

**Constraints** :
- Uptime : 99.5% sur périodes 30 jours
- Support 100 utilisateurs concurrent sans dégradation
- Gestion français ivoirien (accents, expressions locales)
- Conformité RGPD pour données utilisateurs
- Budget infrastructure : <500K FCFA/mois pour 10 clients

**Scale/Scope** :
- MVP : 3 clients payants Mois 2
- 5 sources prioritaires (extensible à 50+)
- ~50-100 mentions/utilisateur/semaine
- 8 user stories (3 P1, 3 P2, 2 P3)
- 50 exigences fonctionnelles
- 6 entités de données principales

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Statut** : ✅ PASS - Aucune constitution de projet définie, pas de violations possibles.

La constitution du projet est actuellement vide (template par défaut). Aucune contrainte architecturale spécifique n'est imposée. Le projet peut procéder avec les meilleures pratiques standard pour une application web SaaS.

## Structure du Projet

### Documentation (cette feature)

```text
specs/001-mediawatch-saas-platform/
├── spec.md              # Spécification fonctionnelle (déjà créée)
├── plan.md              # Ce fichier (sortie /speckit.plan)
├── research.md          # Phase 0 output (à créer)
├── data-model.md        # Phase 1 output (à créer)
├── quickstart.md        # Phase 1 output (à créer)
├── contracts/           # Phase 1 output (à créer)
│   ├── api.openapi.yaml
│   └── webhooks.yaml
├── checklists/          # Déjà créé
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks - PAS créé par /speckit.plan)
```

### Code Source (racine du dépôt)

```text
backend/
├── src/
│   ├── models/          # Entités SQLAlchemy (Organization, User, Keyword, Source, Article, Mention)
│   ├── services/        # Logique métier (scraping, NLP, alertes, analytics)
│   │   ├── scraping/    # Scrapers par source média
│   │   ├── nlp/         # Analyse sentiment, extraction entités
│   │   ├── alerts/      # Système d'alertes email
│   │   └── exports/     # Génération CSV/PDF
│   ├── api/             # Routes FastAPI
│   │   ├── auth.py      # Authentification Supabase
│   │   ├── keywords.py  # CRUD mots-clés
│   │   ├── mentions.py  # Liste mentions, filtres
│   │   ├── analytics.py # Graphiques tendances
│   │   └── admin.py     # Gestion sources/clients
│   ├── workers/         # Celery tasks (scraping async, NLP, alertes)
│   ├── db/              # Migrations Alembic, schéma DB
│   └── config.py        # Configuration environnement
├── tests/
│   ├── unit/            # Tests unitaires services
│   ├── integration/     # Tests API endpoints
│   └── e2e/             # Tests Playwright
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── components/      # Composants React réutilisables
│   │   ├── ui/          # shadcn/ui components
│   │   ├── mentions/    # MentionCard, MentionList
│   │   ├── analytics/   # TrendChart, SourceChart
│   │   └── filters/     # FilterBar, DateRangePicker
│   ├── pages/           # Pages Next.js/React Router
│   │   ├── dashboard/   # Dashboard principal
│   │   ├── analytics/   # Page analytics
│   │   ├── settings/    # Configuration mots-clés
│   │   └── admin/       # Panneau admin
│   ├── services/        # API clients, hooks
│   │   ├── api.ts       # Client API backend
│   │   └── supabase.ts  # Client Supabase auth
│   ├── lib/             # Utilitaires, helpers
│   └── types/           # TypeScript types
├── tests/
│   └── components/      # Tests composants React
├── package.json
└── tailwind.config.js

infrastructure/
├── docker-compose.yml   # Dev local (backend, Redis, PostgreSQL)
├── nginx.conf           # Reverse proxy
└── scripts/             # Scripts déploiement

.specify/                # Configuration SpecKit (déjà existant)
```

**Décision de Structure** : Architecture web classique avec séparation frontend/backend. Le backend Python gère le scraping, NLP et API REST. Le frontend React fournit l'interface utilisateur responsive. Cette structure permet un développement parallèle, un déploiement indépendant (Vercel pour frontend, conteneur pour backend), et une scalabilité horizontale.

## Complexity Tracking

**Statut** : N/A - Aucune violation de constitution à justifier.
