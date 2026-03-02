# Guide d'Installation et Test - MediaWatch CI

Ce guide vous accompagne pas à pas pour configurer Supabase et tester l'infrastructure.

## ⏱️ Temps estimé : 20-30 minutes

---

## Étape 1 : Créer un Projet Supabase (5 min)

### 1.1 Créer le compte et le projet

1. Aller sur https://supabase.com
2. Cliquer sur **"Start your project"** ou **"Sign in"**
3. Se connecter avec GitHub, Google, ou email
4. Cliquer sur **"New Project"**

### 1.2 Configurer le projet

Remplir les informations :

- **Name** : `mediawatch-ci`
- **Database Password** : Générer un mot de passe fort (cliquer sur "Generate a password")
  - ⚠️ **IMPORTANT** : Copier et sauvegarder ce mot de passe immédiatement !
- **Region** : Choisir la région la plus proche
  - Europe : `West EU (Ireland)` ou `Central EU (Frankfurt)`
  - Afrique : `West EU (Ireland)` (le plus proche)
- **Pricing Plan** : Free (500 MB, largement suffisant pour le développement)

5. Cliquer sur **"Create new project"**
6. Attendre 2-3 minutes que le projet soit créé ☕

---

## Étape 2 : Récupérer les Clés API (2 min)

Une fois le projet créé :

1. Dans le menu latéral, aller dans **Settings** (⚙️ en bas à gauche)
2. Cliquer sur **API** dans le sous-menu
3. Copier les informations suivantes :

### Informations à copier :

```
Project URL: https://xxxxxxxxxxxxx.supabase.co
anon public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ...
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ...
```

⚠️ **ATTENTION** : Ne partagez JAMAIS la `service_role key` publiquement !

### Récupérer la Connection String

1. Toujours dans **Settings**, cliquer sur **Database**
2. Faire défiler jusqu'à **Connection string**
3. Sélectionner l'onglet **URI**
4. Copier la connection string :
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
   ```
5. Remplacer `[YOUR-PASSWORD]` par le mot de passe de l'étape 1.2

---

## Étape 3 : Configurer le Backend (5 min)

### 3.1 Créer le fichier .env

```bash
cd backend
cp .env.example .env
```

### 3.2 Éditer backend/.env

Ouvrir `backend/.env` et remplacer les valeurs :

```env
# Application
APP_NAME=MediaWatch CI
APP_ENV=development
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production-12345

# Supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...votre_anon_key
SUPABASE_SERVICE_KEY=eyJhbGc...votre_service_key

# Database
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@db.xxxxxxxxxxxxx.supabase.co:5432/postgres

# Redis (local)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# SendGrid (laisser vide pour l'instant)
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=noreply@mediawatch.ci
SENDGRID_FROM_NAME=MediaWatch CI

# Stripe (mode test - laisser vide pour l'instant)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Orange Money (optionnel)
ORANGE_MONEY_API_KEY=
ORANGE_MONEY_MERCHANT_KEY=
ORANGE_MONEY_API_URL=

# Storage
STORAGE_BUCKET=mediawatch-exports
STORAGE_URL=

# NLP Models
SPACY_MODEL=fr_core_news_lg
CAMEMBERT_MODEL=camembert-base

# Scraping
SCRAPING_USER_AGENT=MediaWatch CI Bot/1.0
SCRAPING_RATE_LIMIT=30
PLAYWRIGHT_HEADLESS=True

# Monitoring (optionnel)
SENTRY_DSN=

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# API
API_V1_PREFIX=/v1
```

### 3.3 Installer les dépendances Python

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

⏱️ Temps d'installation : 2-3 minutes

### 3.4 Appliquer les migrations

```bash
# Toujours dans backend/ avec venv activé
alembic upgrade head
```

✅ Vous devriez voir :
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema, Initial schema
```

### 3.5 Vérifier les tables dans Supabase

1. Retourner sur https://supabase.com
2. Ouvrir votre projet `mediawatch-ci`
3. Aller dans **Table Editor** (icône tableau)
4. Vérifier que les tables suivantes existent :
   - ✅ organizations
   - ✅ users
   - ✅ keywords
   - ✅ sources
   - ✅ articles
   - ✅ mentions

### 3.6 Charger les données de test

```bash
# Toujours dans backend/
python scripts/seed_data.py
```

✅ Vous devriez voir :
```
🌱 Chargement des données de test...
✅ Organisations créées: Agence Com CI, Orange Côte d'Ivoire
✅ Utilisateurs créés: admin@mediawatch.ci, client1@agence.ci, client2@orange.ci
✅ Sources créées: 5 sources
✅ Mots-clés créés: 10 keywords
```

### 3.7 Vérifier les données dans Supabase

Dans **Table Editor**, cliquer sur chaque table pour voir les données :
- `organizations` : 2 lignes
- `users` : 3 lignes
- `sources` : 5 lignes
- `keywords` : 10 lignes

---

## Étape 4 : Démarrer Redis (2 min)

Redis est nécessaire pour Celery (tâches asynchrones).

```bash
# Depuis la racine du projet
cd infrastructure
docker-compose up -d redis
```

Vérifier que Redis fonctionne :
```bash
docker-compose ps
```

✅ Vous devriez voir :
```
NAME                  STATUS
mediawatch-redis      Up
```

---

## Étape 5 : Tester le Backend (3 min)

### 5.1 Démarrer l'API

```bash
cd backend
# Venv doit être activé
uvicorn src.main:app --reload
```

✅ Vous devriez voir :
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 5.2 Tester les endpoints

Ouvrir un navigateur et aller sur :

1. **Documentation API** : http://localhost:8000/docs
   - ✅ Vous devriez voir l'interface Swagger avec tous les endpoints

2. **Health check** : http://localhost:8000/health
   - ✅ Vous devriez voir :
   ```json
   {
     "status": "healthy",
     "environment": "development"
   }
   ```

3. **Root endpoint** : http://localhost:8000/
   - ✅ Vous devriez voir :
   ```json
   {
     "message": "MediaWatch CI API",
     "version": "1.0.0",
     "docs": "/docs"
   }
   ```

### 5.3 Tester la connexion DB

Dans Swagger (http://localhost:8000/docs), vous pouvez tester les endpoints une fois qu'ils seront créés.

---

## Étape 6 : Configurer le Frontend (5 min)

### 6.1 Créer le fichier .env.local

```bash
cd frontend
cp .env.example .env.local
```

### 6.2 Éditer frontend/.env.local

```env
# API Backend
VITE_API_URL=http://localhost:8000/v1

# Supabase
VITE_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...votre_anon_key

# Stripe (laisser vide pour l'instant)
VITE_STRIPE_PUBLISHABLE_KEY=

# App Config
VITE_APP_NAME=MediaWatch CI
VITE_APP_ENV=development
```

### 6.3 Installer les dépendances Node.js

```bash
# Toujours dans frontend/
npm install
```

⏱️ Temps d'installation : 3-5 minutes

---

## Étape 7 : Tester le Frontend (2 min)

### 7.1 Démarrer le serveur de développement

```bash
# Dans frontend/
npm run dev
```

✅ Vous devriez voir :
```
VITE v5.0.11  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### 7.2 Ouvrir l'application

Ouvrir http://localhost:5173 dans votre navigateur.

⚠️ **Note** : L'application affichera une page vide pour l'instant car nous n'avons pas encore créé les pages. C'est normal !

---

## Étape 8 : Configurer l'Authentification Supabase (3 min)

### 8.1 Créer les utilisateurs de test dans Supabase Auth

1. Dans Supabase, aller dans **Authentication** > **Users**
2. Cliquer sur **Add user** > **Create new user**
3. Créer 3 utilisateurs :

**Utilisateur 1 - Admin**
- Email : `admin@mediawatch.ci`
- Password : `Admin123!`
- ✅ Cocher "Auto Confirm User"

**Utilisateur 2 - Client 1**
- Email : `client1@agence.ci`
- Password : `Client123!`
- ✅ Cocher "Auto Confirm User"

**Utilisateur 3 - Client 2**
- Email : `client2@orange.ci`
- Password : `Client123!`
- ✅ Cocher "Auto Confirm User"

### 8.2 Configurer les URLs de redirection

1. Aller dans **Authentication** > **URL Configuration**
2. Dans **Site URL**, mettre : `http://localhost:5173`
3. Dans **Redirect URLs**, ajouter :
   - `http://localhost:5173/**`
   - `http://localhost:3000/**`

---

## ✅ Checklist de Vérification Finale

Cochez chaque élément :

### Backend
- [ ] Projet Supabase créé
- [ ] Clés API récupérées
- [ ] `backend/.env` configuré
- [ ] Dépendances Python installées
- [ ] Migrations appliquées (`alembic upgrade head`)
- [ ] Tables visibles dans Supabase Table Editor
- [ ] Données de test chargées (`seed_data.py`)
- [ ] Redis démarré (`docker-compose up -d redis`)
- [ ] API backend accessible sur http://localhost:8000
- [ ] Swagger docs accessible sur http://localhost:8000/docs

### Frontend
- [ ] `frontend/.env.local` configuré
- [ ] Dépendances Node.js installées
- [ ] Frontend accessible sur http://localhost:5173
- [ ] Aucune erreur dans la console du navigateur

### Supabase
- [ ] 6 tables créées (organizations, users, keywords, sources, articles, mentions)
- [ ] 3 utilisateurs créés dans Authentication
- [ ] URLs de redirection configurées

---

## 🎉 Félicitations !

Votre infrastructure MediaWatch CI est maintenant configurée et fonctionnelle !

## 🚀 Prochaines Étapes

Vous êtes maintenant prêt pour :
- **Phase 3** : Implémenter User Story 1 (Création de compte + Mots-clés)
- Développer les endpoints API
- Créer les pages frontend

## 🐛 Troubleshooting

### Erreur : "Cannot connect to database"
- Vérifier que `DATABASE_URL` est correct dans `.env`
- Vérifier que le mot de passe ne contient pas de caractères spéciaux non encodés
- Tester la connexion depuis Supabase SQL Editor

### Erreur : "Module not found"
- Backend : Vérifier que le venv est activé
- Frontend : Relancer `npm install`

### Redis ne démarre pas
- Vérifier que Docker est installé et lancé
- Essayer : `docker-compose down` puis `docker-compose up -d redis`

### Port déjà utilisé
- Backend (8000) : Changer le port dans la commande uvicorn : `--port 8001`
- Frontend (5173) : Vite choisira automatiquement un autre port

---

## 📚 Ressources

- [Documentation Supabase](https://supabase.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Vite Docs](https://vitejs.dev)
- [README.md](README.md) - Guide général du projet
- [SUPABASE_SETUP.md](SUPABASE_SETUP.md) - Détails configuration Supabase
