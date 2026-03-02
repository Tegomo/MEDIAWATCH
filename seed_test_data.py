"""Seed de données de test sur 20 jours pour MediaWatch CI"""
import random
from datetime import datetime, timedelta
from uuid import uuid4

import psycopg2
from psycopg2.extras import execute_values

# Lire DATABASE_URL
db_url = None
with open(r"E:\DEV\MEDIAWATCH\backend\.env", "r") as f:
    for line in f:
        if line.startswith("DATABASE_URL="):
            db_url = line.split("=", 1)[1].strip()
            break

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

# Récupérer les organisations et keywords existants
cur.execute("SELECT id, name FROM organizations")
orgs = cur.fetchall()

cur.execute("SELECT id, text, normalized_text, organization_id FROM keywords")
keywords = cur.fetchall()

if not keywords:
    print("Aucun keyword trouvé. Créons-en quelques-uns...")
    cur.execute("SELECT id FROM organizations LIMIT 1")
    org_id = cur.fetchone()[0]
    test_keywords = [
        ("Orange CI", "orange ci", "brand", org_id),
        ("MTN", "mtn", "competitor", org_id),
        ("Moov Africa", "moov africa", "competitor", org_id),
        ("Alassane Ouattara", "alassane ouattara", "person", org_id),
        ("RHDP", "rhdp", "custom", org_id),
        ("Cacao", "cacao", "custom", org_id),
        ("CAN 2025", "can 2025", "custom", org_id),
        ("Abidjan", "abidjan", "custom", org_id),
    ]
    for text, norm, cat, oid in test_keywords:
        cur.execute(
            """INSERT INTO keywords (id, text, normalized_text, category, enabled, alert_enabled, 
               alert_threshold, organization_id, total_mentions_count, created_at, updated_at)
               VALUES (%s, %s, %s, %s, true, true, 0.3, %s, 0, now(), now())""",
            (str(uuid4()), text, norm, cat, str(oid)),
        )
    cur.execute("SELECT id, text, normalized_text, organization_id FROM keywords")
    keywords = cur.fetchall()

print(f"Keywords: {len(keywords)}")

# Créer les sources si elles n'existent pas
cur.execute("SELECT id, name FROM sources")
existing_sources = cur.fetchall()

sources_data = [
    ("Fraternité Matin", "https://www.fratmat.info", "press", "FraterniteMatin", 0.9),
    ("Abidjan.net", "https://news.abidjan.net", "press", "AbidjanNet", 0.8),
    ("Koaci", "https://www.koaci.com", "press", "Koaci", 0.7),
    ("Linfodrome", "https://www.linfodrome.com", "press", "Linfodrome", 0.75),
    ("AIP", "https://www.aip.ci", "press", "AIP", 0.85),
    ("RTI Info", "https://www.rti.ci", "press", "RTI", 0.8),
]

source_ids = {}
if not existing_sources:
    for name, url, stype, scraper, prestige in sources_data:
        sid = str(uuid4())
        cur.execute(
            """INSERT INTO sources (id, name, url, type, scraper_class, scraping_enabled, 
               prestige_score, consecutive_failures, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, true, %s, 0, now(), now())""",
            (sid, name, url, stype, scraper, prestige),
        )
        source_ids[name] = sid
    print(f"Sources créées: {len(source_ids)}")
else:
    for sid, name in existing_sources:
        source_ids[name] = str(sid)
    print(f"Sources existantes: {len(source_ids)}")

# Titres d'articles réalistes
ARTICLE_TITLES = [
    "Le président Ouattara annonce un plan de relance économique",
    "Orange CI lance un nouveau forfait internet illimité",
    "MTN Côte d'Ivoire investit dans la fibre optique à Abidjan",
    "Le cours du cacao atteint un record historique",
    "CAN 2025 : les Éléphants en préparation intensive",
    "Moov Africa étend sa couverture réseau dans le nord",
    "Le RHDP organise un congrès extraordinaire à Yamoussoukro",
    "Abidjan accueille le sommet africain du numérique",
    "Nouvelle usine de transformation de cacao à San Pedro",
    "Les exportations ivoiriennes en hausse de 15%",
    "Orange CI et MTN se disputent le marché du mobile money",
    "Le gouvernement lance un programme d'emploi pour les jeunes",
    "Inauguration du métro d'Abidjan : les travaux avancent",
    "Le FMI salue la croissance économique de la Côte d'Ivoire",
    "CAN 2025 : le stade d'Ebimpé prêt pour l'événement",
    "Scandale financier : une banque ivoirienne sous enquête",
    "Crise dans le secteur du cacao : les planteurs manifestent",
    "Orange CI accusé de surfacturation par des consommateurs",
    "Le RHDP perd du terrain dans les sondages",
    "Insécurité à Abidjan : hausse des agressions nocturnes",
    "MTN lance une offre promotionnelle pour la rentrée",
    "Le port d'Abidjan bat son record de trafic conteneurs",
    "Moov Africa signe un partenariat avec une fintech locale",
    "Le président Ouattara en visite officielle en France",
    "Réforme de l'éducation : les enseignants en grève",
    "Le cacao ivoirien menacé par le changement climatique",
    "CAN 2025 : polémique sur la billetterie en ligne",
    "Orange CI déploie la 5G dans le district d'Abidjan",
    "Le RHDP annonce des réformes constitutionnelles",
    "Abidjan : embouteillages monstres sur le pont HKB",
    "MTN accusé de coupures réseau répétées",
    "Le gouvernement augmente le prix du carburant",
    "Succès du festival des arts d'Abidjan",
    "Orange CI remporte le prix de l'innovation digitale",
    "Les planteurs de cacao demandent une revalorisation",
    "CAN 2025 : la billetterie ouvre dans 3 mois",
    "Moov Africa lance son service de paiement mobile",
    "Le RHDP et le PDCI en discussions pour une alliance",
    "Abidjan Smart City : le projet avance à grands pas",
    "Cybersécurité : Orange CI renforce ses infrastructures",
]

SENTIMENTS = ["positive", "negative", "neutral"]
THEMES = ["politics", "economy", "sport", "society", "technology", "culture", "other"]

now = datetime.utcnow()
articles_created = 0
mentions_created = 0

print("Génération des données sur 20 jours...")

for day_offset in range(20):
    date = now - timedelta(days=19 - day_offset)
    # 3-8 articles par jour
    num_articles = random.randint(3, 8)

    for _ in range(num_articles):
        source_name = random.choice(list(source_ids.keys()))
        source_id = source_ids[source_name]
        title = random.choice(ARTICLE_TITLES)
        
        # Varier l'heure dans la journée
        hour = random.randint(6, 22)
        minute = random.randint(0, 59)
        pub_date = date.replace(hour=hour, minute=minute, second=0)

        # Contenu simulé
        content = f"{title}. " * random.randint(10, 30)
        # Injecter des mots-clés dans le contenu
        for kw in keywords:
            if random.random() < 0.4:  # 40% de chance d'inclure chaque keyword
                content += f" {kw[1]} est mentionné dans cet article. "

        import hashlib
        content_hash = hashlib.sha256(f"{title}{pub_date}{random.random()}".encode()).hexdigest()

        article_id = str(uuid4())
        try:
            cur.execute(
                """INSERT INTO articles (id, title, url, content_hash, raw_content, cleaned_content,
                   author, published_at, scraped_at, source_id, nlp_processed, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    article_id,
                    title,
                    f"https://{source_name.lower().replace(' ', '')}.ci/article/{article_id[:8]}",
                    content_hash,
                    content,
                    content,
                    random.choice(["Jean Kouassi", "Marie Koné", "Ibrahim Diallo", "Awa Touré", None]),
                    pub_date,
                    pub_date + timedelta(minutes=random.randint(1, 30)),
                    source_id,
                    pub_date + timedelta(minutes=random.randint(5, 60)),
                    pub_date,
                ),
            )
            articles_created += 1
        except Exception as e:
            # URL unique constraint
            continue

        # Créer 1-3 mentions par article
        matched_keywords = [kw for kw in keywords if kw[1].lower() in content.lower()]
        if not matched_keywords:
            matched_keywords = random.sample(keywords, min(2, len(keywords)))

        for kw in matched_keywords[:3]:
            sentiment = random.choices(
                SENTIMENTS,
                weights=[30, 25, 45],  # 30% positif, 25% négatif, 45% neutre
                k=1,
            )[0]

            if sentiment == "positive":
                score = random.uniform(0.3, 0.95)
            elif sentiment == "negative":
                score = random.uniform(-0.95, -0.3)
            else:
                score = random.uniform(-0.2, 0.2)

            theme = random.choice(THEMES)
            visibility = random.uniform(0.3, 0.95)

            context = f"...dans un contexte où {kw[1]} fait l'actualité, {title.lower()}..."

            mention_id = str(uuid4())
            detected_at = pub_date + timedelta(minutes=random.randint(5, 120))

            try:
                cur.execute(
                    """INSERT INTO mentions (id, keyword_id, article_id, matched_text, match_context,
                       sentiment_score, sentiment_label, visibility_score, theme, detected_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (keyword_id, article_id) DO NOTHING""",
                    (
                        mention_id,
                        str(kw[0]),
                        article_id,
                        kw[1],
                        context,
                        round(score, 3),
                        sentiment,
                        round(visibility, 2),
                        theme,
                        detected_at,
                    ),
                )
                mentions_created += 1

                # Mettre à jour le compteur du keyword
                cur.execute(
                    "UPDATE keywords SET total_mentions_count = total_mentions_count + 1, last_mention_at = %s WHERE id = %s",
                    (detected_at, str(kw[0])),
                )
            except Exception as e:
                continue

print(f"\n{'='*60}")
print(f"Données de test générées avec succès!")
print(f"{'='*60}")
print(f"  Articles créés: {articles_created}")
print(f"  Mentions créées: {mentions_created}")
print(f"  Période: {(now - timedelta(days=19)).strftime('%d/%m/%Y')} - {now.strftime('%d/%m/%Y')}")
print(f"  Sources: {len(source_ids)}")
print(f"  Keywords: {len(keywords)}")

cur.close()
conn.close()
