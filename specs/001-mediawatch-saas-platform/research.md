# Recherche & Décisions Techniques : MediaWatch CI

**Feature** : MediaWatch CI - Plateforme SaaS de Veille Médias  
**Date** : 5 février 2026  
**Phase** : Phase 0 - Recherche et résolution des clarifications

## Vue d'Ensemble

Ce document résout tous les points "NEEDS CLARIFICATION" identifiés dans le contexte technique et documente les décisions architecturales clés pour MediaWatch CI.

## Décisions Techniques

### 1. Intégration Orange Money pour la Côte d'Ivoire

**Contexte** : Le système de paiement doit supporter à la fois les cartes de crédit internationales (via Stripe) et Orange Money, le principal système de paiement mobile en Côte d'Ivoire.

**Décision** : Utiliser l'API Orange Money Developer (https://developer.orange.com/apis/orange-money-webpay) en complément de Stripe.

**Rationale** :
- Orange Money est le leader du mobile money en Côte d'Ivoire avec >60% de part de marché
- L'API Orange Money Webpay permet l'intégration web pour paiements récurrents
- Stripe gère les cartes internationales et la facturation récurrente
- Architecture dual-gateway permet de maximiser la conversion locale tout en gardant l'accès international

**Implémentation** :
- Backend FastAPI : endpoints séparés `/payments/stripe` et `/payments/orange-money`
- Webhook handlers pour les deux systèmes
- Table `payments` avec champ `provider` (stripe|orange_money)
- Fallback automatique : si Orange Money échoue, proposer Stripe

**Alternatives considérées** :
- **Stripe uniquement** : Rejeté car faible adoption cartes bancaires en CI (~15% population)
- **Orange Money uniquement** : Rejeté car limite marché international et agences avec cartes corporate
- **Wave/MTN Mobile Money** : Considéré mais Orange Money a meilleure API et documentation

**Ressources** :
- Documentation API : https://developer.orange.com/apis/orange-money-webpay/api-reference
- SDK Python (communautaire) : https://github.com/Orange-OpenSource/python-orange-money
- Coûts : ~2.5% commission Orange Money vs 2.9% + 0.30€ Stripe

---

### 2. Architecture de Scraping Multi-Sources

**Contexte** : Le système doit scraper 50+ sources médias ivoiriennes avec structures HTML différentes, certaines nécessitant JavaScript, d'autres avec anti-scraping.

**Décision** : Architecture hybride Scrapy (sites statiques) + Playwright (sites dynamiques) avec pattern Strategy par source.

**Rationale** :
- Scrapy : Performant pour sites statiques (Fraternité Matin, Abidjan.net), gestion robuste des erreurs
- Playwright : Nécessaire pour sites JavaScript (certains médias modernes), contournement anti-scraping léger
- Pattern Strategy : Chaque source = classe dédiée implémentant interface `MediaScraper`
- Celery Beat : Orchestration des scrapings périodiques (toutes les 30min-1h)

**Implémentation** :
```python
# backend/src/services/scraping/base.py
class MediaScraper(ABC):
    @abstractmethod
    async def scrape(self) -> List[Article]: pass
    
# backend/src/services/scraping/sources/
# - fraternite_matin.py (Scrapy)
# - abidjan_net.py (Scrapy)
# - koaci.py (Playwright - site dynamique)
# - france24_whatsapp.py (API WhatsApp Business)
```

**Alternatives considérées** :
- **BeautifulSoup uniquement** : Rejeté car pas de gestion async efficace, pas de support JS
- **Selenium** : Rejeté car trop lourd en ressources vs Playwright
- **Services tiers (ScrapingBee)** : Rejeté car coût prohibitif à l'échelle (50+ sources × 48 scrapes/jour)

**Gestion des échecs** :
- Retry exponentiel : 3 tentatives avec backoff 1min, 5min, 15min
- Circuit breaker : Si source échoue 5× en 24h → alerte admin + pause 6h
- Fallback : Scraping RSS si disponible (Fraternité Matin, Koaci ont flux RSS)

---

### 3. Modèles NLP pour Français Ivoirien

**Contexte** : L'analyse de sentiment et extraction d'entités doit fonctionner avec le français ivoirien (expressions locales, noms propres ivoiriens).

**Décision** : Modèle pré-entraîné `camembert-base` (français) + fine-tuning sur corpus ivoirien + dictionnaire entités locales.

**Rationale** :
- CamemBERT : Meilleur modèle français open-source (BERT entraîné sur 138GB texte français)
- Fine-tuning : Dataset annoté de 500-1000 articles ivoiriens pour adapter au dialecte local
- Dictionnaire entités : Liste noms politiques, entreprises, lieux ivoiriens pour améliorer extraction
- spaCy pipeline : Intégration facile avec modèle Transformers custom

**Implémentation** :
```python
# backend/src/services/nlp/sentiment.py
from transformers import CamembertForSequenceClassification
model = CamembertForSequenceClassification.from_pretrained(
    "camembert-base", 
    num_labels=3  # positif/négatif/neutre
)
# Fine-tuning avec dataset annoté ivoirien
```

**Alternatives considérées** :
- **GPT-4 API** : Rejeté car coût prohibitif (~$0.03/1K tokens × 100 mentions/jour/user × 10 users = $90/jour)
- **spaCy fr_core_news_lg uniquement** : Rejeté car précision sentiment <70% sur textes ivoiriens
- **Entraînement from scratch** : Rejeté car nécessite >10K articles annotés et compute intensif

**Métriques de qualité** :
- Target : >85% précision sentiment (validé par annotation humaine)
- Baseline : Test sur 200 articles annotés manuellement
- Amélioration continue : Feedback utilisateurs sur mentions mal classées

---

### 4. Gestion des Alertes Email à Grande Échelle

**Contexte** : Le système doit envoyer des alertes email sous 5 minutes avec batching pour éviter le spam, tout en gérant 100+ utilisateurs.

**Décision** : Architecture Celery + Redis + SendGrid avec batching intelligent et rate limiting.

**Rationale** :
- Celery : Queue distribuée pour traitement async des alertes
- Redis : Backend Celery + cache pour deduplication alertes
- SendGrid : Service email transactionnel fiable (99.9% deliverability, 100K emails/mois gratuits)
- Batching : Regrouper alertes même utilisateur sur fenêtre 1h

**Implémentation** :
```python
# backend/src/workers/alerts.py
@celery.task
def send_alert_batch(user_id: str, mentions: List[Mention]):
    # Envoi email avec template HTML
    # Tracking: delivered, opened, clicked
    
# Trigger: Après détection mention négative
# Delay: Max 5min, batch si plusieurs mentions
```

**Alternatives considérées** :
- **SMTP direct** : Rejeté car risque blacklist IP, pas de tracking
- **AWS SES** : Considéré mais SendGrid a meilleure UX et templates
- **Mailgun** : Similaire à SendGrid mais pricing moins avantageux pour notre échelle

**Gestion des échecs** :
- Retry : 3 tentatives avec backoff exponentiel
- Dead letter queue : Alertes échouées après 3 tentatives → log + alerte admin
- Fallback : Si SendGrid down → queue emails pour envoi différé

---

### 5. Génération d'Exports PDF avec Graphiques

**Contexte** : Les utilisateurs doivent pouvoir exporter des rapports PDF formatés avec branding, graphiques de tendances, et tableaux de mentions.

**Décision** : WeasyPrint (HTML→PDF) + Recharts (génération graphiques en PNG via headless browser).

**Rationale** :
- WeasyPrint : Convertit HTML/CSS en PDF, support excellent CSS3, fonts custom
- Workflow : Template HTML Jinja2 → WeasyPrint → PDF
- Graphiques : Recharts génère SVG → Playwright capture PNG → embed dans HTML
- Stockage : S3-compatible (Supabase Storage) avec URLs signées temporaires

**Implémentation** :
```python
# backend/src/services/exports/pdf.py
async def generate_pdf_report(user_id, mentions, date_range):
    # 1. Générer graphiques PNG via Playwright
    charts = await generate_charts(mentions)
    
    # 2. Render template HTML avec mentions + charts
    html = render_template('report.html', mentions=mentions, charts=charts)
    
    # 3. HTML → PDF via WeasyPrint
    pdf = HTML(string=html).write_pdf()
    
    # 4. Upload S3 + URL signée 24h
    url = await upload_to_storage(pdf)
    return url
```

**Alternatives considérées** :
- **ReportLab** : Rejeté car génération programmatique complexe vs templates HTML
- **Puppeteer PDF** : Considéré mais WeasyPrint plus léger et meilleur rendu print
- **Services tiers (DocRaptor)** : Rejeté car coût ($0.05/PDF × 50 exports/mois/user = $25/user/mois)

**Performance** :
- Target : <10s pour rapports jusqu'à 500 mentions
- Async : Génération en background Celery task, email du lien de download
- Cache : Graphiques agrégés cachés 1h dans Redis

---

### 6. Architecture de Base de Données

**Contexte** : Le système doit stocker articles, mentions, utilisateurs avec relations complexes et requêtes analytics performantes.

**Décision** : PostgreSQL via Supabase avec indexation stratégique et partitionnement par date pour articles.

**Schéma clé** :
```sql
-- Partitionnement articles par mois (performance requêtes temporelles)
CREATE TABLE articles (
    id UUID PRIMARY KEY,
    source_id UUID REFERENCES sources(id),
    title TEXT,
    content TEXT,
    published_at TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (published_at);

-- Index pour recherche full-text français
CREATE INDEX idx_articles_content_fts ON articles 
USING gin(to_tsvector('french', content));

-- Index composite pour filtrage mentions
CREATE INDEX idx_mentions_org_date ON mentions(organization_id, detected_at DESC);
```

**Rationale** :
- Partitionnement : Articles anciens (>3 mois) rarement consultés → partition séparée améliore perf
- Full-text search : PostgreSQL natif avec support français (stemming, stop words)
- Supabase : Auth intégré, Row Level Security, real-time subscriptions, backups automatiques

**Alternatives considérées** :
- **MongoDB** : Rejeté car relations complexes et analytics nécessitent SQL
- **Elasticsearch** : Considéré pour full-text mais PostgreSQL FTS suffisant pour notre échelle
- **PostgreSQL auto-hébergé** : Rejeté car Supabase fournit auth/storage/real-time intégrés

---

### 7. Stratégie de Déploiement et Infrastructure

**Contexte** : Budget infrastructure <500K FCFA/mois (~€760) pour 10 clients avec contrainte uptime 99.5%.

**Décision** : Frontend Vercel (gratuit tier hobby) + Backend Railway/Render (conteneur Docker) + Supabase (tier gratuit puis Pro).

**Coûts estimés** :
- Vercel : Gratuit (tier hobby suffit pour 10 clients)
- Railway/Render : $20-30/mois (conteneur backend + Redis)
- Supabase Pro : $25/mois (500K requêtes, 8GB DB, 100GB bandwidth)
- SendGrid : Gratuit (100K emails/mois)
- **Total : ~$50-60/mois (~€50 = 33K FCFA)** ✅ Bien sous budget

**Rationale** :
- Vercel : Déploiement Git automatique, CDN global, SSL gratuit
- Railway : Simple, bon DX, auto-scaling, logs intégrés
- Monitoring : Sentry (erreurs), Uptime Robot (disponibilité)

**Alternatives considérées** :
- **AWS/GCP** : Rejeté car complexité setup et coûts imprévisibles
- **Heroku** : Considéré mais Railway meilleur pricing et DX
- **VPS auto-géré** : Rejeté car nécessite DevOps et risque downtime

**Scalabilité** :
- 10→50 clients : Passer Supabase Pro ($25→$99), Railway scale up ($30→$100)
- 50→200 clients : Migrer backend vers conteneurs multiples + load balancer
- Budget reste <500K FCFA jusqu'à ~30 clients

---

## Risques Identifiés et Mitigations

### Risque 1 : Changements Structure Sites Médias
**Impact** : Scraping échoue si site change HTML  
**Probabilité** : Moyenne (2-3 fois/an selon hypothèse)  
**Mitigation** :
- Tests automatisés quotidiens de scraping
- Alertes admin si échec >5× en 24h
- Scrapers modulaires faciles à mettre à jour
- Fallback RSS quand disponible

### Risque 2 : Précision NLP Insuffisante
**Impact** : Utilisateurs reçoivent alertes incorrectes  
**Probabilité** : Moyenne (baseline 70-80% avant fine-tuning)  
**Mitigation** :
- Fine-tuning obligatoire sur corpus ivoirien avant lancement
- Feedback utilisateurs pour amélioration continue
- Seuil de confiance : Alertes uniquement si score >0.7

### Risque 3 : Dépassement Budget Infrastructure
**Impact** : Perte rentabilité si coûts explosent  
**Probabilité** : Faible avec architecture actuelle  
**Mitigation** :
- Monitoring coûts temps réel (Railway/Supabase dashboards)
- Alertes si >80% budget mensuel
- Cache agressif (Redis) pour réduire requêtes DB
- Tier gratuits maximisés (Vercel, SendGrid)

---

## Prochaines Étapes

✅ **Phase 0 complétée** : Toutes les clarifications techniques résolues

**Phase 1 à venir** :
1. Générer `data-model.md` avec schéma DB détaillé
2. Créer contrats API OpenAPI dans `/contracts/`
3. Rédiger `quickstart.md` pour onboarding développeurs
4. Mettre à jour contexte agent Windsurf

**Décisions en attente utilisateur** : Aucune - toutes les décisions techniques sont prises et justifiées.
