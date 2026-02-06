"""Seed mentions de test sur 20 jours"""
import random
import hashlib
from datetime import datetime, timedelta
from uuid import uuid4

import psycopg2

db_url = None
with open(r"E:\DEV\MEDIAWATCH\backend\.env", "r") as f:
    for line in f:
        if line.startswith("DATABASE_URL="):
            db_url = line.split("=", 1)[1].strip()
            break

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

# Vérifier les enum values
cur.execute(
    "SELECT enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'sentimentlabel'"
)
sentiment_labels = [r[0] for r in cur.fetchall()]
print(f"Sentiment labels en DB: {sentiment_labels}")

cur.execute(
    "SELECT enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'theme'"
)
theme_labels = [r[0] for r in cur.fetchall()]
print(f"Theme labels en DB: {theme_labels}")

# Récupérer keywords et articles
cur.execute("SELECT id, text FROM keywords")
keywords = cur.fetchall()
print(f"Keywords: {len(keywords)}")

cur.execute("SELECT id, published_at FROM articles ORDER BY published_at")
articles = cur.fetchall()
print(f"Articles: {len(articles)}")

if not sentiment_labels or not articles or not keywords:
    print("ERREUR: données manquantes")
    exit(1)

# Supprimer les mentions existantes pour repartir propre
cur.execute("DELETE FROM mentions")
print("Mentions existantes supprimées")

mentions_created = 0

for art_id, pub_date in articles:
    # 1-3 keywords matchés par article
    num_kw = random.randint(1, min(3, len(keywords)))
    matched = random.sample(keywords, num_kw)

    for kw_id, kw_text in matched:
        sentiment = random.choices(
            sentiment_labels,
            weights=[30, 45, 25] if len(sentiment_labels) == 3 else [1] * len(sentiment_labels),
            k=1,
        )[0]

        if "positive" in sentiment.lower():
            score = round(random.uniform(0.3, 0.95), 3)
        elif "negative" in sentiment.lower():
            score = round(random.uniform(-0.95, -0.3), 3)
        else:
            score = round(random.uniform(-0.15, 0.15), 3)

        theme = random.choice(theme_labels) if theme_labels else None
        visibility = round(random.uniform(0.3, 0.95), 2)
        detected_at = pub_date + timedelta(minutes=random.randint(5, 120))
        context = f"...dans un contexte où {kw_text} fait l'actualité en Côte d'Ivoire..."

        mention_id = str(uuid4())

        try:
            if theme:
                cur.execute(
                    """INSERT INTO mentions 
                       (id, keyword_id, article_id, matched_text, match_context,
                        sentiment_score, sentiment_label, visibility_score, theme, detected_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s::sentimentlabel, %s, %s::theme, %s)
                       ON CONFLICT (keyword_id, article_id) DO NOTHING""",
                    (mention_id, str(kw_id), str(art_id), kw_text, context,
                     score, sentiment, visibility, theme, detected_at),
                )
            else:
                cur.execute(
                    """INSERT INTO mentions 
                       (id, keyword_id, article_id, matched_text, match_context,
                        sentiment_score, sentiment_label, visibility_score, detected_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s::sentimentlabel, %s, %s)
                       ON CONFLICT (keyword_id, article_id) DO NOTHING""",
                    (mention_id, str(kw_id), str(art_id), kw_text, context,
                     score, sentiment, visibility, detected_at),
                )
            mentions_created += 1
        except Exception as e:
            print(f"ERR: {e}")
            continue

# Mettre à jour les compteurs keywords
for kw_id, kw_text in keywords:
    cur.execute(
        "SELECT count(*), max(detected_at) FROM mentions WHERE keyword_id = %s",
        (str(kw_id),),
    )
    count, last = cur.fetchone()
    cur.execute(
        "UPDATE keywords SET total_mentions_count = %s, last_mention_at = %s WHERE id = %s",
        (count, last, str(kw_id)),
    )

print(f"\n{'='*60}")
print(f"Mentions créées: {mentions_created}")
print(f"{'='*60}")

# Stats rapides
cur.execute("SELECT sentiment_label, count(*) FROM mentions GROUP BY sentiment_label")
for label, count in cur.fetchall():
    print(f"  {label}: {count}")

cur.execute("SELECT date(detected_at), count(*) FROM mentions GROUP BY date(detected_at) ORDER BY 1")
for d, c in cur.fetchall():
    print(f"  {d}: {c} mentions")

cur.close()
conn.close()
