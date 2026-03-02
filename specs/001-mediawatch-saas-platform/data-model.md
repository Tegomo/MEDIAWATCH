# Modèle de Données : MediaWatch CI

**Feature** : MediaWatch CI - Plateforme SaaS de Veille Médias  
**Date** : 5 février 2026  
**Phase** : Phase 1 - Design

## Vue d'Ensemble

Ce document définit le schéma de base de données complet pour MediaWatch CI, incluant toutes les entités, relations, contraintes et index de performance.

## Diagramme Entité-Relation

```
┌─────────────┐       ┌──────────┐       ┌─────────┐
│Organization │1─────*│   User   │       │ Source  │
└─────────────┘       └──────────┘       └─────────┘
       │1                                       │1
       │                                        │
       │*                                       │*
┌─────────────┐                          ┌─────────┐
│   Keyword   │                          │ Article │
└─────────────┘                          └─────────┘
       │1                                       │1
       │                                        │
       │*                                       │*
       └──────────────┐    ┌───────────────────┘
                      │    │
                      │*  *│
                   ┌──────────┐
                   │ Mention  │
                   └──────────┘
```

## Entités

### 1. Organization (Organisations Clientes)

Représente un compte client (agence, entreprise, institution).

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    
    -- Abonnement
    subscription_plan VARCHAR(50) NOT NULL DEFAULT 'basic', -- basic, pro, enterprise
    subscription_status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, suspended, cancelled
    subscription_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subscription_ends_at TIMESTAMPTZ,
    
    -- Limites de plan
    keyword_limit INTEGER NOT NULL DEFAULT 10,
    user_limit INTEGER NOT NULL DEFAULT 3,
    
    -- Paiement
    stripe_customer_id VARCHAR(255),
    orange_money_customer_id VARCHAR(255),
    last_payment_at TIMESTAMPTZ,
    next_billing_date DATE,
    
    -- Métriques d'utilisation
    current_keyword_count INTEGER NOT NULL DEFAULT 0,
    current_user_count INTEGER NOT NULL DEFAULT 0,
    total_mentions_count INTEGER NOT NULL DEFAULT 0,
    
    -- Métadonnées
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ -- Soft delete
);

-- Index
CREATE INDEX idx_organizations_status ON organizations(subscription_status) 
    WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_billing ON organizations(next_billing_date) 
    WHERE subscription_status = 'active';
```

**Règles de Validation** :
- `subscription_plan` : Valeurs autorisées = ['basic', 'pro', 'enterprise']
- `subscription_status` : Valeurs autorisées = ['active', 'suspended', 'cancelled', 'trial']
- `keyword_limit` : basic=10, pro=50, enterprise=illimité (999)
- `current_keyword_count` ≤ `keyword_limit`

---

### 2. User (Utilisateurs)

Représente un individu avec accès à la plateforme.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Authentification (géré par Supabase Auth)
    supabase_user_id UUID NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    
    -- Profil
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer', -- admin, client, viewer
    
    -- Préférences
    alert_enabled BOOLEAN NOT NULL DEFAULT true,
    alert_threshold DECIMAL(3,2) DEFAULT 0.3, -- Seuil sentiment négatif (0-1)
    alert_frequency VARCHAR(50) DEFAULT 'immediate', -- immediate, hourly, daily
    timezone VARCHAR(50) DEFAULT 'Africa/Abidjan',
    language VARCHAR(10) DEFAULT 'fr',
    
    -- Métadonnées
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Index
CREATE INDEX idx_users_org ON users(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_supabase ON users(supabase_user_id);
CREATE INDEX idx_users_role ON users(organization_id, role);
```

**Règles de Validation** :
- `role` : Valeurs autorisées = ['admin', 'client', 'viewer']
- `alert_threshold` : Entre 0.0 et 1.0
- `alert_frequency` : Valeurs autorisées = ['immediate', 'hourly', 'daily', 'disabled']
- Un seul admin par organisation (contrainte application)

---

### 3. Keyword (Mots-Clés de Surveillance)

Représente un terme de surveillance configuré par une organisation.

```sql
CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Mot-clé
    text VARCHAR(255) NOT NULL,
    normalized_text VARCHAR(255) NOT NULL, -- Lowercase, sans accents pour matching
    
    -- Configuration
    category VARCHAR(100), -- brand, product, person, competitor, custom
    enabled BOOLEAN NOT NULL DEFAULT true,
    alert_enabled BOOLEAN NOT NULL DEFAULT true,
    alert_threshold DECIMAL(3,2) DEFAULT 0.3,
    
    -- Statistiques
    total_mentions_count INTEGER NOT NULL DEFAULT 0,
    last_mention_at TIMESTAMPTZ,
    
    -- Métadonnées
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Index
CREATE UNIQUE INDEX idx_keywords_unique ON keywords(organization_id, normalized_text) 
    WHERE deleted_at IS NULL;
CREATE INDEX idx_keywords_enabled ON keywords(organization_id, enabled) 
    WHERE deleted_at IS NULL;
```

**Règles de Validation** :
- `text` : Non vide, max 255 caractères
- `category` : Valeurs suggérées = ['brand', 'product', 'person', 'competitor', 'custom']
- `alert_threshold` : Entre 0.0 et 1.0
- Unicité : (organization_id, normalized_text) unique

**Triggers** :
```sql
-- Auto-normalisation du texte
CREATE OR REPLACE FUNCTION normalize_keyword_text()
RETURNS TRIGGER AS $$
BEGIN
    NEW.normalized_text = lower(unaccent(NEW.text));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_normalize_keyword
BEFORE INSERT OR UPDATE ON keywords
FOR EACH ROW EXECUTE FUNCTION normalize_keyword_text();
```

---

### 4. Source (Sources Médias)

Représente un média en cours de scraping.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identification
    name VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(500) NOT NULL,
    type VARCHAR(50) NOT NULL, -- press, whatsapp, rss, api
    
    -- Configuration scraping
    scraper_class VARCHAR(255) NOT NULL, -- Nom classe Python (FraterniteMatin, AbidjanNet)
    scraping_enabled BOOLEAN NOT NULL DEFAULT true,
    scraping_interval_minutes INTEGER NOT NULL DEFAULT 60,
    requires_javascript BOOLEAN NOT NULL DEFAULT false,
    
    -- Métadonnées
    country VARCHAR(2) DEFAULT 'CI',
    language VARCHAR(10) DEFAULT 'fr',
    prestige_score DECIMAL(3,2) DEFAULT 0.5, -- 0-1, importance de la source
    
    -- Statut scraping
    last_scrape_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_error_at TIMESTAMPTZ,
    last_error_message TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    total_articles_scraped INTEGER NOT NULL DEFAULT 0,
    
    -- Métadonnées
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Index
CREATE INDEX idx_sources_scraping ON sources(scraping_enabled, last_scrape_at) 
    WHERE deleted_at IS NULL;
CREATE INDEX idx_sources_failures ON sources(consecutive_failures) 
    WHERE consecutive_failures > 0;
```

**Règles de Validation** :
- `type` : Valeurs autorisées = ['press', 'whatsapp', 'rss', 'api']
- `prestige_score` : Entre 0.0 et 1.0
- `scraping_interval_minutes` : Min 15, max 1440 (24h)

**Circuit Breaker** :
- Si `consecutive_failures` ≥ 5 → `scraping_enabled` = false + alerte admin
- Reset `consecutive_failures` = 0 après succès

---

### 5. Article (Articles Scrapés)

Représente un article média scrapé. **Partitionné par mois** pour performance.

```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    
    -- Contenu
    title TEXT NOT NULL,
    url VARCHAR(1000) NOT NULL,
    raw_content TEXT, -- HTML brut
    cleaned_content TEXT, -- Texte nettoyé pour NLP
    excerpt TEXT, -- Premier paragraphe ou résumé
    
    -- Métadonnées article
    author VARCHAR(255),
    published_at TIMESTAMPTZ NOT NULL,
    
    -- NLP (calculé après scraping)
    nlp_processed BOOLEAN NOT NULL DEFAULT false,
    nlp_processed_at TIMESTAMPTZ,
    sentiment_score DECIMAL(3,2), -- -1 (négatif) à +1 (positif)
    sentiment_label VARCHAR(20), -- negative, neutral, positive
    extracted_entities JSONB, -- {persons: [], organizations: [], locations: []}
    themes JSONB, -- [politics, economy, sport, society]
    
    -- Métadonnées scraping
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    content_hash VARCHAR(64) NOT NULL, -- SHA256 pour déduplication
    
    -- Métadonnées
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (published_at);

-- Partitions (créer pour chaque mois)
CREATE TABLE articles_2026_02 PARTITION OF articles
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE articles_2026_03 PARTITION OF articles
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
-- ... créer automatiquement via script

-- Index
CREATE UNIQUE INDEX idx_articles_url ON articles(source_id, url);
CREATE UNIQUE INDEX idx_articles_hash ON articles(content_hash);
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_nlp ON articles(nlp_processed) WHERE nlp_processed = false;

-- Full-text search
CREATE INDEX idx_articles_content_fts ON articles 
    USING gin(to_tsvector('french', cleaned_content));
```

**Règles de Validation** :
- `url` : Unique par source (même URL peut exister sur sources différentes)
- `content_hash` : Unique globalement (déduplication cross-source)
- `sentiment_score` : Entre -1.0 et 1.0
- `sentiment_label` : Valeurs autorisées = ['negative', 'neutral', 'positive']

**Déduplication** :
```sql
-- Avant insertion, vérifier hash
SELECT id FROM articles WHERE content_hash = :hash;
-- Si existe → skip insertion
```

---

### 6. Mention (Correspondances Mot-Clé)

Représente une correspondance de mot-clé dans un article.

```sql
CREATE TABLE mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    keyword_id UUID NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    
    -- Matching
    matched_text VARCHAR(255) NOT NULL, -- Texte exact trouvé dans article
    match_context TEXT, -- 200 caractères autour du match
    match_positions INTEGER[], -- Positions dans le texte
    
    -- Analyse (hérité de article + spécifique)
    sentiment_score DECIMAL(3,2) NOT NULL,
    sentiment_label VARCHAR(20) NOT NULL,
    visibility_score DECIMAL(3,2) NOT NULL, -- Basé sur prestige source + position match
    theme VARCHAR(100),
    
    -- Alertes
    alert_sent BOOLEAN NOT NULL DEFAULT false,
    alert_sent_at TIMESTAMPTZ,
    alert_batch_id UUID, -- Pour regroupement alertes
    
    -- Métadonnées
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index
CREATE INDEX idx_mentions_org_date ON mentions(organization_id, detected_at DESC);
CREATE INDEX idx_mentions_keyword ON mentions(keyword_id, detected_at DESC);
CREATE INDEX idx_mentions_article ON mentions(article_id);
CREATE INDEX idx_mentions_alerts ON mentions(organization_id, alert_sent) 
    WHERE alert_sent = false;
CREATE UNIQUE INDEX idx_mentions_unique ON mentions(keyword_id, article_id);
```

**Règles de Validation** :
- `sentiment_score` : Entre -1.0 et 1.0
- `sentiment_label` : Valeurs autorisées = ['negative', 'neutral', 'positive']
- `visibility_score` : Entre 0.0 et 1.0
- Unicité : (keyword_id, article_id) unique (un article ne peut matcher qu'une fois par mot-clé)

**Calcul Visibility Score** :
```python
visibility_score = (
    source.prestige_score * 0.5 +  # Importance source
    (1 - match_position / content_length) * 0.3 +  # Position dans article
    (len(match_positions) / 10) * 0.2  # Nombre d'occurrences
)
```

---

### 7. Payment (Paiements)

Suivi des transactions de paiement.

```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Transaction
    provider VARCHAR(50) NOT NULL, -- stripe, orange_money
    provider_transaction_id VARCHAR(255) NOT NULL UNIQUE,
    amount_fcfa INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'XOF',
    
    -- Statut
    status VARCHAR(50) NOT NULL, -- pending, succeeded, failed, refunded
    payment_method VARCHAR(100), -- card, mobile_money
    
    -- Métadonnées
    metadata JSONB, -- Données provider-specific
    error_message TEXT,
    
    -- Dates
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index
CREATE INDEX idx_payments_org ON payments(organization_id, created_at DESC);
CREATE INDEX idx_payments_status ON payments(status) WHERE status = 'pending';
```

---

### 8. Alert_Batch (Regroupement Alertes)

Regroupement d'alertes envoyées ensemble pour éviter spam.

```sql
CREATE TABLE alert_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Contenu
    mention_count INTEGER NOT NULL,
    negative_count INTEGER NOT NULL,
    
    -- Envoi
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    email_provider_id VARCHAR(255), -- SendGrid message ID
    email_status VARCHAR(50), -- sent, delivered, opened, clicked, bounced
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index
CREATE INDEX idx_alert_batches_org ON alert_batches(organization_id, sent_at DESC);
```

---

## Relations et Contraintes

### Cardinalités

- **Organization → User** : 1:N (une organisation a plusieurs utilisateurs)
- **Organization → Keyword** : 1:N (une organisation a plusieurs mots-clés)
- **Source → Article** : 1:N (une source produit plusieurs articles)
- **Keyword + Article → Mention** : N:M via table Mention
- **Organization → Mention** : 1:N (via Keyword)

### Contraintes de Cohérence

```sql
-- Limiter keywords par organisation selon plan
CREATE OR REPLACE FUNCTION check_keyword_limit()
RETURNS TRIGGER AS $$
DECLARE
    org_limit INTEGER;
    current_count INTEGER;
BEGIN
    SELECT keyword_limit INTO org_limit 
    FROM organizations WHERE id = NEW.organization_id;
    
    SELECT COUNT(*) INTO current_count 
    FROM keywords 
    WHERE organization_id = NEW.organization_id AND deleted_at IS NULL;
    
    IF current_count >= org_limit THEN
        RAISE EXCEPTION 'Keyword limit reached for organization';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_keyword_limit
BEFORE INSERT ON keywords
FOR EACH ROW EXECUTE FUNCTION check_keyword_limit();
```

---

## Vues Matérialisées (Performance)

### Vue : Organization Stats

```sql
CREATE MATERIALIZED VIEW organization_stats AS
SELECT 
    o.id AS organization_id,
    o.name,
    COUNT(DISTINCT k.id) AS keyword_count,
    COUNT(DISTINCT u.id) AS user_count,
    COUNT(DISTINCT m.id) AS total_mentions,
    COUNT(DISTINCT m.id) FILTER (WHERE m.detected_at > NOW() - INTERVAL '7 days') AS mentions_last_7d,
    COUNT(DISTINCT m.id) FILTER (WHERE m.sentiment_label = 'negative') AS negative_mentions,
    AVG(m.sentiment_score) AS avg_sentiment
FROM organizations o
LEFT JOIN keywords k ON k.organization_id = o.id AND k.deleted_at IS NULL
LEFT JOIN users u ON u.organization_id = o.id AND u.deleted_at IS NULL
LEFT JOIN mentions m ON m.organization_id = o.id
WHERE o.deleted_at IS NULL
GROUP BY o.id, o.name;

CREATE UNIQUE INDEX idx_org_stats ON organization_stats(organization_id);

-- Refresh toutes les heures
CREATE OR REPLACE FUNCTION refresh_org_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY organization_stats;
END;
$$ LANGUAGE plpgsql;
```

---

## Migrations et Versioning

**Outil** : Alembic (Python)

**Stratégie** :
- Migrations versionnées dans `backend/src/db/migrations/`
- Naming : `YYYY-MM-DD_HHmm_description.py`
- Toujours tester rollback avant déploiement
- Migrations data-heavy en background (Celery task)

**Exemple Migration** :
```python
# backend/src/db/migrations/2026-02-05_1400_create_organizations.py
def upgrade():
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(), nullable=False),
        # ... colonnes
    )

def downgrade():
    op.drop_table('organizations')
```

---

## Stratégie de Backup

- **Supabase automatique** : Backups quotidiens, rétention 7 jours (tier Pro)
- **Point-in-time recovery** : Disponible sur tier Pro (jusqu'à 7 jours)
- **Export manuel** : Script hebdomadaire export CSV des données critiques vers S3

---

## Considérations de Performance

### Partitionnement
- **Articles** : Partitionné par mois sur `published_at`
- Création automatique nouvelles partitions via cron mensuel
- Archivage partitions >6 mois vers stockage froid

### Indexation
- **Full-text search** : Index GIN sur `articles.cleaned_content`
- **Filtrage mentions** : Index composite sur `(organization_id, detected_at DESC)`
- **Recherche keywords** : Index unique sur `(organization_id, normalized_text)`

### Caching
- **Redis** : Cache résultats requêtes analytics (TTL 1h)
- **Vues matérialisées** : Refresh toutes les heures pour stats organisations

---

## Sécurité (Row Level Security)

Supabase RLS activé pour toutes les tables :

```sql
-- Exemple : Users ne peuvent voir que leur organisation
ALTER TABLE mentions ENABLE ROW LEVEL SECURITY;

CREATE POLICY mentions_org_isolation ON mentions
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id FROM users 
            WHERE supabase_user_id = auth.uid()
        )
    );
```

---

## Prochaines Étapes

✅ **Data Model complété**

**À venir** :
- Générer contrats API OpenAPI
- Créer quickstart.md
- Mettre à jour contexte agent
