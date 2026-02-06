# MediaWatch CI - Documentation API

## Base URL

```
http://localhost:8001/v1
```

## Authentification

Toutes les routes (sauf `/health`, `/v1/auth/*`, webhooks) nécessitent un token JWT dans le header:

```
Authorization: Bearer <token>
```

---

## Auth

### POST /v1/auth/signup
Inscription d'un nouvel utilisateur et création d'organisation.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "organization_name": "Mon Agence"
}
```

### POST /v1/auth/login
Connexion et obtention du token JWT.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:** `{ "access_token": "...", "token_type": "bearer", "user": {...} }`

### GET /v1/auth/me
Retourne le profil de l'utilisateur connecté.

---

## Keywords

### GET /v1/keywords
Liste les mots-clés de l'organisation.

### POST /v1/keywords
Crée un nouveau mot-clé.

**Body:**
```json
{
  "text": "Orange CI",
  "category": "brand"
}
```

### DELETE /v1/keywords/{id}
Supprime un mot-clé.

---

## Mentions

### GET /v1/mentions
Liste les mentions avec filtres et pagination.

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `limit` | int (1-100) | Nombre de résultats (défaut: 20) |
| `offset` | int | Décalage pagination |
| `keyword_id` | UUID | Filtrer par mot-clé |
| `sentiment` | string | `POSITIVE`, `NEUTRAL`, `NEGATIVE` |
| `source_id` | UUID | Filtrer par source |
| `date_from` | datetime | Date début (ISO 8601) |
| `date_to` | datetime | Date fin (ISO 8601) |
| `search` | string | Recherche texte libre |
| `theme` | string | `POLITICS`, `ECONOMY`, `SPORT`, `SOCIETY`, `TECHNOLOGY`, `CULTURE`, `OTHER` |

### GET /v1/mentions/{id}
Détail d'une mention.

### GET /v1/mentions/stats
Statistiques rapides (total, répartition sentiment).

---

## Analytics

### GET /v1/analytics/trends
Tendances des mentions par jour.

**Query params:** `days` (int, défaut: 30)

### GET /v1/analytics/sources
Répartition des mentions par source.

**Query params:** `days` (int, défaut: 30)

### GET /v1/analytics/keywords
Top mots-clés par nombre de mentions.

**Query params:** `days` (int, défaut: 30), `limit` (int, défaut: 10)

---

## Exports

### POST /v1/exports/csv
Export CSV synchrone des mentions filtrées. Retourne un fichier CSV.

**Query params:** mêmes filtres que `GET /v1/mentions`

### POST /v1/exports/pdf
Export PDF des mentions filtrées.

**Query params:** mêmes filtres + `async` (bool, défaut: false)
- `async=false` : retourne le PDF directement
- `async=true` : lance une tâche Celery, retourne `{ "task_id": "...", "status": "processing" }`

### GET /v1/exports/download/{file_id}
Télécharge un fichier d'export généré de manière asynchrone.

### GET /v1/exports/status/{task_id}
Vérifie le statut d'un export async.

---

## Alerts

### GET /v1/alerts/settings
Paramètres d'alerte de l'utilisateur.

### PUT /v1/alerts/settings
Met à jour les paramètres d'alerte.

**Body:**
```json
{
  "email_enabled": true,
  "frequency": "realtime",
  "sentiment_filter": "negative"
}
```

---

## Admin (rôle admin requis)

### GET /v1/admin/sources
Liste toutes les sources avec statut de santé.

### POST /v1/admin/sources/{id}/retry
Réactive une source et relance le scraping.

### POST /v1/admin/sources/{id}/toggle?enabled=true
Active/désactive une source.

### GET /v1/admin/organizations
Liste toutes les organisations.

**Query params:** `plan` (string), `status` (string)

### GET /v1/admin/organizations/{id}
Détails d'une organisation avec utilisateurs.

### POST /v1/admin/organizations/{id}/suspend
Suspend une organisation.

### POST /v1/admin/organizations/{id}/reactivate
Réactive une organisation.

### PATCH /v1/admin/organizations/{id}/limits
Met à jour les limites.

**Body:**
```json
{
  "keyword_limit": 50,
  "user_limit": 5
}
```

---

## Webhooks

### POST /v1/webhooks/stripe
Webhook Stripe pour les événements de paiement.

### POST /v1/webhooks/orange-money/callback
Webhook Orange Money pour les notifications de paiement.

---

## Health

### GET /health
Vérifie la santé de l'application (DB, Redis).

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-06T12:00:00",
  "services": {
    "database": { "status": "ok" },
    "redis": { "status": "ok" }
  }
}
```

---

## Rate Limiting

- **120 requêtes/minute** par IP
- Headers de réponse: `X-RateLimit-Limit`, `X-RateLimit-Remaining`
- Code 429 si dépassé, avec header `Retry-After: 60`

---

## Codes d'erreur

| Code | Description |
|------|-------------|
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès interdit (admin requis) |
| 404 | Ressource non trouvée |
| 422 | Erreur de validation |
| 429 | Rate limit dépassé |
| 500 | Erreur serveur |
