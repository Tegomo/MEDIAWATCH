# MediaWatch CI - Déploiement Docker

## Prérequis

- **Docker** >= 24.0
- **Docker Compose** >= 2.20
- **Python 3** (pour les scripts de génération de clés et seed)

## Démarrage rapide

### 1. Générer les clés JWT

```bash
cd docker
python generate-keys.py
```

Copiez les valeurs affichées dans `.env`.

### 2. Créer le fichier `.env`

```bash
cp .env.example .env
# Éditez .env avec les clés générées + vos clés API (Jina, OpenRouter)
```

### 3. Lancer les services

```bash
docker compose up -d
```

Attendez ~30s que tous les services démarrent.

### 4. Créer les utilisateurs de test

```bash
pip install httpx  # si pas installé
python seed-users.py
```

### 5. Accéder aux services

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Application React |
| **Backend API** | http://localhost:8001/docs | Swagger FastAPI |
| **Supabase Studio** | http://localhost:3100 | Admin DB |
| **Supabase API** | http://localhost:8000 | PostgREST + Auth |

### 6. Identifiants de test

| Email | Mot de passe | Rôle |
|-------|-------------|------|
| admin@mediawatch.ci | Admin123! | ADMIN |
| client1@agence.ci | Client123! | CLIENT |
| client2@orange.ci | Client123! | CLIENT |

## Architecture

```
┌─────────────┐     ┌──────────────┐
│  Frontend   │────▶│   Backend    │
│  (nginx:80) │     │ (FastAPI:8000)│
└─────────────┘     └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Kong :8000  │ (API Gateway)
                    └──┬───────┬──┘
                       │       │
              ┌────────▼─┐  ┌──▼────────┐
              │ PostgREST │  │  GoTrue   │
              │ (REST API)│  │  (Auth)   │
              └─────┬─────┘  └─────┬─────┘
                    │              │
                    └──────┬───────┘
                    ┌──────▼───────┐
                    │  PostgreSQL  │
                    │    :5432     │
                    └──────────────┘
```

## Commandes utiles

```bash
# Voir les logs
docker compose logs -f backend
docker compose logs -f auth

# Reconstruire le backend après modifs
docker compose build backend && docker compose up -d backend

# Reconstruire le frontend après modifs
docker compose build frontend && docker compose up -d frontend

# Reset complet (supprime les données)
docker compose down -v
docker compose up -d

# Vérifier la santé des services
docker compose ps
```

## Résolution de problèmes

### Le backend ne démarre pas
- Vérifiez que Kong est accessible : `curl http://localhost:8000/rest/v1/`
- Vérifiez les clés JWT dans `.env`

### Erreur d'authentification
- Vérifiez que le seed des utilisateurs a fonctionné : `python seed-users.py`
- Vérifiez que `ANON_KEY` et `SERVICE_ROLE_KEY` sont corrects

### Studio ne se connecte pas
- Attendez 30-60s après le premier démarrage
- Vérifiez que le service `meta` est lancé : `docker compose logs meta`
