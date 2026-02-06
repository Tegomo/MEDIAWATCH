"""Migration: créer la table alert_settings"""
import psycopg2

# Lire DATABASE_URL depuis .env
db_url = None
with open(r"E:\DEV\MEDIAWATCH\backend\.env", "r") as f:
    for line in f:
        if line.startswith("DATABASE_URL="):
            db_url = line.split("=", 1)[1].strip()
            break

if not db_url:
    print("ERREUR: DATABASE_URL non trouvée")
    exit(1)

sql = """
DO $block$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_channel') THEN
    CREATE TYPE alert_channel AS ENUM ('email', 'sms', 'whatsapp');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_frequency') THEN
    CREATE TYPE alert_frequency AS ENUM ('immediate', 'batch_1h', 'batch_4h', 'daily');
  END IF;
END
$block$;

CREATE TABLE IF NOT EXISTS alert_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT true,
    channel alert_channel NOT NULL DEFAULT 'email',
    frequency alert_frequency NOT NULL DEFAULT 'batch_1h',
    negative_only BOOLEAN NOT NULL DEFAULT true,
    min_sentiment_score FLOAT NOT NULL DEFAULT 0.3,
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alert_settings_user ON alert_settings(user_id);
"""

print("Connexion à la base de données...")
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()
cur.execute(sql)
print("Migration alert_settings OK")
cur.close()
conn.close()
