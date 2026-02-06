#!/bin/bash
# Script de déploiement production MediaWatch CI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== MediaWatch CI - Déploiement Production ==="
echo "Répertoire: $PROJECT_ROOT"
echo ""

# Vérifier les variables d'environnement requises
REQUIRED_VARS=(
    "DATABASE_URL"
    "SECRET_KEY"
    "SUPABASE_URL"
    "SUPABASE_ANON_KEY"
    "SUPABASE_SERVICE_KEY"
    "STRIPE_SECRET_KEY"
    "STRIPE_PUBLISHABLE_KEY"
    "STRIPE_WEBHOOK_SECRET"
    "REDIS_URL"
)

echo "--- Vérification des variables d'environnement ---"
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "ERREUR: Variable $var non définie"
        exit 1
    fi
done
echo "OK: Toutes les variables requises sont définies"
echo ""

# Backend
echo "--- Backend ---"
cd "$PROJECT_ROOT/backend"

echo "Installation des dépendances Python..."
pip install -r requirements.txt --quiet

echo "Exécution des migrations Alembic..."
alembic upgrade head 2>/dev/null || echo "Alembic non configuré, skip migrations"

echo "Vérification du health check..."
python -c "from src.config import settings; print(f'Config OK: {settings.app_name}')"

echo ""

# Frontend
echo "--- Frontend ---"
cd "$PROJECT_ROOT/frontend"

echo "Installation des dépendances Node..."
npm ci --silent

echo "Build de production..."
npm run build

echo "Build frontend terminé: $(du -sh dist/ | cut -f1)"
echo ""

# Celery workers
echo "--- Celery Workers ---"
echo "Pour démarrer les workers Celery:"
echo "  cd $PROJECT_ROOT/backend"
echo "  celery -A src.workers.celery_app worker --loglevel=info --concurrency=4"
echo "  celery -A src.workers.celery_app beat --loglevel=info"
echo ""

# Backend server
echo "--- Serveur Backend ---"
echo "Pour démarrer le serveur:"
echo "  cd $PROJECT_ROOT/backend"
echo "  gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001"
echo ""

echo "=== Déploiement préparé avec succès ==="
echo "N'oubliez pas de:"
echo "  1. Configurer le reverse proxy (nginx/caddy)"
echo "  2. Activer HTTPS (Let's Encrypt)"
echo "  3. Configurer les backups DB"
echo "  4. Vérifier les webhooks Stripe/Orange Money"
