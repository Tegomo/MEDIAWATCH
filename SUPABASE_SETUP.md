# Configuration Supabase pour MediaWatch CI

Ce guide explique comment configurer Supabase pour MediaWatch CI.

## 1. Créer un Projet Supabase

1. Aller sur https://supabase.com
2. Se connecter ou créer un compte
3. Cliquer sur "New Project"
4. Remplir les informations :
   - **Name**: `mediawatch-ci` (ou votre choix)
   - **Database Password**: Choisir un mot de passe fort (le noter !)
   - **Region**: Choisir la région la plus proche (ex: `eu-west-1` pour Europe)
   - **Pricing Plan**: Free tier suffit pour le développement

5. Attendre 2-3 minutes que le projet soit créé

## 2. Récupérer les Clés API

Une fois le projet créé :

1. Aller dans **Settings** > **API**
2. Noter les informations suivantes :
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGc...` (clé publique)
   - **service_role key**: `eyJhbGc...` (clé secrète - NE PAS PARTAGER)

## 3. Configurer les Variables d'Environnement

### Backend (`backend/.env`)

Créer le fichier `backend/.env` depuis `backend/.env.example` :

```bash
cd backend
cp .env.example .env
```

Modifier les valeurs suivantes dans `backend/.env` :

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...votre_anon_key
SUPABASE_SERVICE_KEY=eyJhbGc...votre_service_key

# Database - Utiliser la connection string Supabase
DATABASE_URL=postgresql://postgres:[VOTRE_MOT_DE_PASSE]@db.xxxxx.supabase.co:5432/postgres
```

**Pour obtenir la DATABASE_URL complète** :
1. Aller dans **Settings** > **Database**
2. Copier la **Connection string** (mode URI)
3. Remplacer `[YOUR-PASSWORD]` par le mot de passe choisi à l'étape 1

### Frontend (`frontend/.env.local`)

Créer le fichier `frontend/.env.local` depuis `frontend/.env.example` :

```bash
cd frontend
cp .env.example .env.local
```

Modifier les valeurs suivantes dans `frontend/.env.local` :

```env
# Supabase
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...votre_anon_key
```

## 4. Appliquer les Migrations de Base de Données

Une fois les variables d'environnement configurées :

```bash
cd backend

# Activer l'environnement virtuel
source venv/bin/activate  # Windows: venv\Scripts\activate

# Appliquer les migrations
alembic upgrade head
```

Cela créera toutes les tables nécessaires dans votre base Supabase.

## 5. Configurer l'Authentification Supabase

1. Aller dans **Authentication** > **Providers**
2. Activer **Email** (activé par défaut)
3. (Optionnel) Activer d'autres providers (Google, GitHub, etc.)

### Configurer les URLs de redirection

1. Aller dans **Authentication** > **URL Configuration**
2. Ajouter les URLs autorisées :
   - `http://localhost:5173` (frontend dev)
   - `http://localhost:3000` (alternative)
   - Votre domaine de production quand disponible

## 6. Charger les Données de Test

```bash
cd backend
python scripts/seed_data.py
```

Cela créera :
- 2 organisations
- 3 utilisateurs (admin + 2 clients)
- 5 sources médias
- 10 mots-clés

**⚠️ Important** : Les utilisateurs créés dans la DB doivent aussi être créés dans Supabase Auth :

1. Aller dans **Authentication** > **Users**
2. Cliquer sur **Add user**
3. Créer les comptes pour :
   - `admin@mediawatch.ci`
   - `client1@agence.ci`
   - `client2@orange.ci`

## 7. Vérification

### Vérifier la Base de Données

1. Aller dans **Table Editor** dans Supabase
2. Vérifier que les tables existent :
   - organizations
   - users
   - keywords
   - sources
   - articles
   - mentions

### Tester l'API Backend

```bash
cd backend
uvicorn src.main:app --reload
```

Ouvrir http://localhost:8000/docs pour voir la documentation Swagger.

### Tester le Frontend

```bash
cd frontend
npm run dev
```

Ouvrir http://localhost:5173

## 8. Row Level Security (RLS) - Optionnel mais Recommandé

Pour sécuriser l'accès aux données :

1. Aller dans **Table Editor**
2. Pour chaque table, cliquer sur **RLS** (Row Level Security)
3. Activer RLS
4. Créer des policies appropriées

Exemple de policy pour la table `keywords` :

```sql
-- Les utilisateurs peuvent voir uniquement les keywords de leur organisation
CREATE POLICY "Users can view their org keywords"
ON keywords FOR SELECT
USING (
  organization_id IN (
    SELECT organization_id 
    FROM users 
    WHERE supabase_user_id = auth.uid()
  )
);
```

## Troubleshooting

### Erreur de connexion à la base de données

- Vérifier que `DATABASE_URL` est correcte
- Vérifier que le mot de passe ne contient pas de caractères spéciaux non encodés
- Essayer d'encoder le mot de passe : `urllib.parse.quote_plus(password)`

### Erreur d'authentification

- Vérifier que `SUPABASE_URL` et `SUPABASE_ANON_KEY` sont corrects
- Vérifier que les URLs de redirection sont configurées

### Tables non créées

- Vérifier que les migrations Alembic ont bien été appliquées
- Vérifier les logs : `alembic upgrade head --sql` pour voir le SQL généré

## Ressources

- [Documentation Supabase](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Supabase Auth](https://supabase.com/docs/guides/auth)
