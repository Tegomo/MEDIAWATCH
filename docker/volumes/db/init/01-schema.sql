-- MediaWatch CI - Schema initialization for local Supabase
-- Extensions and roles are created in 00-roles.sql

-- Make extensions available without schema prefix
SET search_path TO public, extensions;

-- Enum types (uppercase to match Supabase cloud convention)
DO $$ BEGIN
    CREATE TYPE subscription_plan AS ENUM ('BASIC', 'PRO', 'ENTERPRISE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'SUSPENDED', 'CANCELED', 'TRIAL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('ADMIN', 'CLIENT', 'VIEWER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE source_type AS ENUM ('PRESS', 'WHATSAPP', 'RSS', 'API');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE keyword_category AS ENUM ('BRAND', 'PRODUCT', 'PERSON', 'COMPETITOR', 'CUSTOM');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE sentiment_label AS ENUM ('NEGATIVE', 'NEUTRAL', 'POSITIVE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE theme_type AS ENUM ('POLITICS', 'ECONOMY', 'SPORT', 'SOCIETY', 'TECHNOLOGY', 'CULTURE', 'OTHER');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_channel AS ENUM ('EMAIL', 'SMS', 'WHATSAPP');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_frequency AS ENUM ('IMMEDIATE', 'BATCH_1H', 'BATCH_4H', 'DAILY');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subscription_plan subscription_plan NOT NULL DEFAULT 'BASIC',
    subscription_status subscription_status NOT NULL DEFAULT 'TRIAL',
    keyword_limit INTEGER NOT NULL DEFAULT 10,
    user_limit INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'CLIENT',
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    supabase_user_id UUID NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_supabase_id ON users(supabase_user_id);

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(512) NOT NULL,
    type source_type NOT NULL DEFAULT 'PRESS',
    scraper_class VARCHAR(100) NOT NULL,
    scraping_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    prestige_score FLOAT NOT NULL DEFAULT 0.5,
    last_scrape_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    last_error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text VARCHAR(255) NOT NULL,
    normalized_text VARCHAR(255) NOT NULL,
    category keyword_category NOT NULL DEFAULT 'CUSTOM',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    alert_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    alert_threshold FLOAT NOT NULL DEFAULT 0.3,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    total_mentions_count INTEGER NOT NULL DEFAULT 0,
    last_mention_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_keywords_text ON keywords(text);
CREATE INDEX IF NOT EXISTS idx_keywords_org ON keywords(organization_id);

CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(512) NOT NULL,
    url VARCHAR(1024) NOT NULL UNIQUE,
    content_hash VARCHAR(64) NOT NULL,
    raw_content TEXT NOT NULL,
    cleaned_content TEXT NOT NULL,
    author VARCHAR(255),
    published_at TIMESTAMPTZ NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    nlp_processed TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_hash ON articles(content_hash);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_article_source_hash ON articles(source_id, content_hash);

CREATE TABLE IF NOT EXISTS mentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword_id UUID NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    matched_text VARCHAR(255) NOT NULL,
    match_context TEXT NOT NULL,
    sentiment_score FLOAT NOT NULL,
    sentiment_label sentiment_label NOT NULL,
    visibility_score FLOAT NOT NULL DEFAULT 0.5,
    theme theme_type,
    extracted_entities JSONB,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    alert_sent TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_mentions_keyword ON mentions(keyword_id);
CREATE INDEX IF NOT EXISTS idx_mentions_article ON mentions(article_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mention_keyword_article ON mentions(keyword_id, article_id);
CREATE INDEX IF NOT EXISTS idx_mention_sentiment_date ON mentions(sentiment_label, detected_at);
CREATE INDEX IF NOT EXISTS idx_mention_theme ON mentions(theme);
CREATE INDEX IF NOT EXISTS idx_mentions_detected ON mentions(detected_at);

CREATE TABLE IF NOT EXISTS alert_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    channel alert_channel NOT NULL DEFAULT 'EMAIL',
    frequency alert_frequency NOT NULL DEFAULT 'BATCH_1H',
    negative_only BOOLEAN NOT NULL DEFAULT TRUE,
    min_sentiment_score FLOAT NOT NULL DEFAULT 0.3,
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Row Level Security (désactivé pour l'API backend qui utilise service_key)
-- ============================================================================
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE mentions ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_settings ENABLE ROW LEVEL SECURITY;

-- Policy: service_role bypass RLS
CREATE POLICY "Service role bypass" ON organizations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role bypass" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role bypass" ON sources FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role bypass" ON keywords FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role bypass" ON articles FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role bypass" ON mentions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role bypass" ON alert_settings FOR ALL USING (true) WITH CHECK (true);

-- Grant access to service role schemas
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated;
