# 🔧 Configuration des Fichiers .env - MediaWatch CI

Ce guide vous aide à créer les fichiers `.env` nécessaires.

---

## ⚠️ Informations Manquantes à Récupérer

Vous devez récupérer 2 informations depuis Supabase :

### 1. Service Role Key (Backend)

1. Aller sur https://supabase.com/dashboard/project/zujclwfgmwnfuxomyjkt/settings/api
2. Faire défiler jusqu'à **Project API keys**
3. Copier la clé **service_role** (secret)

### 2. Mot de passe de la Base de Données

1. Aller sur https://supabase.com/dashboard/project/zujclwfgmwnfuxomyjkt/settings/database
2. Section **Connection string**
3. Cliquer sur l'onglet **URI**
4. Vous verrez : `postgresql://postgres:[YOUR-PASSWORD]@db.zujclwfgmwnfuxomyjkt.supabase.co:5432/postgres`
5. Remplacer `[YOUR-PASSWORD]` par le mot de passe que vous avez défini lors de la création du projet

---

## 📝 Étape 1 : Créer backend/.env

```bash
cd backend
copy .env.template .env
```

Puis éditer `backend/.env` et remplacer :

1. **SUPABASE_SERVICE_KEY** : Coller la service_role key récupérée
2. **DATABASE_URL** : Remplacer `VOTRE_MOT_DE_PASSE` par votre mot de passe DB

Le fichier est déjà pré-rempli avec :
- ✅ SUPABASE_URL
- ✅ SUPABASE_ANON_KEY
- ✅ Autres configurations par défaut

---

## 📝 Étape 2 : Créer frontend/.env.local

```bash
cd frontend
copy .env.local.template .env.local
```

Ce fichier est déjà complet ! Aucune modification nécessaire.

Il contient :
- ✅ VITE_SUPABASE_URL
- ✅ VITE_SUPABASE_ANON_KEY
- ✅ VITE_API_URL

---

## 🚀 Étape 3 : Installer les Dépendances

### Backend (Python)

```bash
cd backend

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat

# Installer les dépendances
pip install -r requirements.txt
```

⏱️ Temps d'installation : 2-3 minutes

### Frontend (Node.js)

```bash
cd frontend

# Installer les dépendances
npm install
```

⏱️ Temps d'installation : 3-5 minutes

---

## 🐳 Étape 4 : Démarrer Redis (Optionnel)

Redis est nécessaire pour Celery (tâches asynchrones).

```bash
cd infrastructure
docker-compose up -d redis
```

Vérifier :
```bash
docker-compose ps
```

---

## ✅ Étape 5 : Tester

### Tester le Backend

```bash
cd backend
# Venv doit être activé
uvicorn src.main:app --reload
```

Ouvrir http://localhost:8000/docs

### Tester le Frontend

```bash
cd frontend
npm run dev
```

Ouvrir http://localhost:5173

---

## 🎯 Résumé des Commandes

```bash
# 1. Backend .env
cd backend
copy .env.template .env
# Éditer .env : SUPABASE_SERVICE_KEY et DATABASE_URL

# 2. Frontend .env.local
cd frontend
copy .env.local.template .env.local
# Aucune modification nécessaire

# 3. Installer backend
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Installer frontend
cd frontend
npm install

# 5. Démarrer Redis
cd infrastructure
docker-compose up -d redis

# 6. Tester backend
cd backend
uvicorn src.main:app --reload

# 7. Tester frontend (nouveau terminal)
cd frontend
npm run dev
```

---

## 🔗 Liens Utiles

- **Récupérer Service Role Key** : https://supabase.com/dashboard/project/zujclwfgmwnfuxomyjkt/settings/api
- **Récupérer Connection String** : https://supabase.com/dashboard/project/zujclwfgmwnfuxomyjkt/settings/database
- **Dashboard Supabase** : https://supabase.com/dashboard/project/zujclwfgmwnfuxomyjkt

---

## ❓ Problèmes Courants

### "Module not found" (Backend)
- Vérifier que le venv est activé
- Relancer `pip install -r requirements.txt`

### "Cannot find module" (Frontend)
- Relancer `npm install`
- Supprimer `node_modules` et relancer `npm install`

### Redis ne démarre pas
- Vérifier que Docker est installé et lancé
- `docker-compose down` puis `docker-compose up -d redis`

### Erreur de connexion DB
- Vérifier que `DATABASE_URL` est correct dans `.env`
- Vérifier que le mot de passe ne contient pas de caractères spéciaux non encodés
