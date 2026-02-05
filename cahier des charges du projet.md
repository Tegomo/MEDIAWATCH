# 📋 CAHIER DES CHARGES COMPLET
## MEDIAWATCH CI - Plateforme SaaS Veille Médias Côte d'Ivoire
### Version 1.0 - Février 2026

---

## 📄 1. IDENTIFICATION PROJET

**Nom du projet** : MediaWatch CI  
**Client** : [Votre Nom/Entreprise]  
**Date** : 05 Février 2026  
**Version** : 1.0  
**Statut** : Prêt pour développement  

**Contacts** :  
- Responsable Projet : [Votre nom]  
- Email : [votre.email@domaine.ci]  
- Téléphone : [+225 XX XX XX XX]  

---

## 🎯 2. CONTEXTE & OBJECTIFS

### 2.1 Problématique actuelle
❌ Pige manuelle = 3-5M FCFA/mois (15-25€/jour)
❌ Collecte 2-3h/jour par employé
❌ Sources incomplètes (5-10 journaux max)
❌ Pas d'analyse temps réel (sentiment, tendances)
❌ Données non structurées (Excel manuels)

### 2.2 Objectifs métier
✅ Réduire coûts : 3M FCFA → 300K FCFA/mois (-93%)
✅ Couvrir 50+ sources (presse CI + WhatsApp + web)
✅ Alertes temps réel (email + WhatsApp optionnel)
✅ Dashboard analytics (graphiques, tendances)
✅ ROI Mois 2 : 3 clients = 75€ MRR
🎯 MRR Cible Y1 : 3K€ (150 clients @25€/mois)

### 2.3 Cibles clients
1️⃣ Agences de communication (80%)
2️⃣ Grandes entreprises CI (15%)
3️⃣ Institutions publiques (5%)
4️⃣ PME actives en PR (optionnel)

---

## 👥 3. USER STORIES (Priorisées MVP)

### Sprint 1 - Core MVP ⭐⭐⭐
US-001: Inscription Stripe + configuration mots-clés
"En tant que responsable com, je veux créer un compte et définir 5-10 mots-clés pour monitorer ma marque"

US-002: Dashboard mentions journalier
"En tant qu'utilisateur, je veux voir mes 20 dernières mentions avec source, sentiment, extrait"

US-003: Alertes email critiques
"En tant qu'utilisateur, je veux recevoir email si mention négative sur ma marque"

### Sprint 2 - Analytics ⭐⭐
US-004: Graphiques tendances 7j/30j
"En tant qu'utilisateur, je veux voir évolution mentions (ligne) et sources (barres)"

US-005: Filtres avancés
"En tant qu'utilisateur, je veux filtrer par date, source, sentiment, thème"

US-006: Export CSV/PDF hebdo
"En tant qu'utilisateur, je veux exporter mes données pour reporting interne"

### Sprint 3 - Admin & Scale ⭐
US-007: Monitoring scrapers (admin)
"En tant qu'admin, je veux voir santé des 50 sources (OK/KO)"

US-008: Gestion clients (admin)
"En tant qu'admin, je veux suspendre/activer comptes + voir usage"

---

## 🏗️ 4. ARCHITECTURE TECHNIQUE

```
┌────────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ VPS HETZNER CX22 │───▶│ SUPABASE PRO │───▶│ REACT DASHBOARD │
│ 2 vCPU | 4GB RAM │ │ PG 8GB + Auth │ │ TailwindCSS │
│ FastAPI + Workers │ │ Storage 100GB │ │ Recharts │
└────────┬───────────┘ └────────┬────────┘ └────────┬──────┘
│ │ │
▼ ▼ ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ JINA AI READER │ │ NLP spaCy + │ │ STRIPE + ALERTS │
│ Scraping URLs │ │ Transformers │ │ Email Service │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 4.1 Stack technique détaillé

**BACKEND**: FastAPI 0.104 + Python 3.11.6 + Uvicorn 0.29
**DATABASE**: Supabase PostgreSQL 15 + pgvector (embeddings)
**SCRAPING**: Jina AI Reader API + requests 2.31 + BeautifulSoup4 4.12
**NLP**: spaCy fr_core_news_lg 3.7 + Transformers 4.41 (sentiment)
**FRONTEND**: React 18.2.0 + Vite 5.4 + TailwindCSS 3.4 + Recharts 2.12
**DEPLOYMENT**: VPS Ubuntu 22.04 + Nginx 1.24 + PM2 5.3 + Docker 27.3
**AUTH**: Supabase Auth (JWT + RBAC)
**PAYMENTS**: Stripe Checkout (CI cards + Orange Money)
**MONITORING**: Sentry + UptimeRobot + PM2 logs
**CI/CD**: GitHub Actions (gratuit)

---

## 💰 5. BUDGET DÉTAILLÉ (Prix Février 2026)

| Catégorie | Service | Mois 1-3 (MVP) | Mois 4-12 (Scale) | Notes |
|-----------|---------|----------------|-------------------|-------|
| **Infrastructure** | Hetzner CX22 VPS | **3,79€** | **3,79€** | 2 vCPU, 4GB RAM, 20TB trafic |
| **Base de données** | Supabase Pro | **0€→25€** | **25€** | 8GB PG + 100GB Storage + Auth |
| **Scraping IA** | Jina AI Reader | **0€→5€** | **5€** | 5K pages/jour gratuit 2 mois |
| **Paiements** | Stripe CI (2,9%) | **0€** | **50€** | Sur 3K€ MRR = 87€ frais |
| **Monitoring** | Sentry + UptimeRobot | **0€** | **9€** | Free tiers suffisant |
| **Domaine** | mediawatch.ci | **1,25€** | **1,25€** | 15€/an chez Hetzner |
| **Développement** | Freelance initial | **800€** | **0€** | 40h @20€/h (one-time) |
| **Presse CI** | Abonnements sources | **5K FCFA** | **20K FCFA** | Fraternité Matin + autres |
| **TOTAL** | | **805€ (M1)** | **94€/mois** | **ROI Mois 2** (3 clients) |

### Projections financières
Mois 1: 0 clients → -805€
Mois 2: 3 clients → +270€ (75€ MRR - 30€ coûts)
Mois 6: 50 clients → +4.940€ (1.250€ MRR)
Mois 12: 150 clients → +14.900€ (3.750€ MRR)

---

## 🛠️ 6. SPÉCIFICATIONS FONCTIONNELLES

### 6.1 Module Scraping (5 sources prioritaires)
1. **Fraternité Matin Digital** (payant 5K FCFA/mois)
2. **Abidjan.net** (gratuit - titrologie + articles)
3. **Koaci.com/ci** (gratuit - actualités CI)
4. **Linfodrome.com** (gratuit - politique/économie)
5. **France24 WhatsApp** (gratuit - 4,7M abonnés)

**Pipeline technique** :
```
URL → Jina Reader API → Markdown propre → spaCy NER →
stockage Supabase → matching keywords clients → alertes
```

### 6.2 Module NLP (Analyse intelligente)
- **EXTRACTION**: Marques, personnes, lieux (spaCy fr_core_news_lg)
- **SENTIMENT**: Positif/Négatif/Neutre (Transformers DistilBERT)
- **THÉMATIQUE**: Politique/Économie/Sport/Société (zero-shot)
- **SCORE VISIBILITÉ**: Position + taille titre + source prestige

### 6.3 Dashboard Client (Responsive)
**🏠 PAGE D'ACCUEIL**:
- KPI: Mentions 24h, 7j, 30j
- Graph ligne: Évolution quotidienne
- Top 5 sources du jour
- Alertes critiques (rouges)

**📊 PAGE MENTIONS**:
- Tableau filtrable (date/source/sentiment)
- Pagination 25/50/100
- Export CSV/PDF

**⚙️ PAGE CONFIG**:
- Mots-clés (ajout/suppression)
- Seuil alerte configurable
- Concurrents à suivre

---

## 🗄️ 7. SCHÉMA BASE DONNÉES SUPABASE

```sql
-- USERS & ORGANISATIONS
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  stripe_customer_id TEXT,
  plan TEXT DEFAULT 'basic',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  organization_id UUID REFERENCES organizations(id),
  role TEXT DEFAULT 'client',
  created_at TIMESTAMP DEFAULT NOW()
);

-- SOURCES MÉDIAS
CREATE TABLE sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  url TEXT NOT NULL,
  type TEXT CHECK (type IN ('press','whatsapp','rss')),
  prestige_score INTEGER DEFAULT 50,
  status TEXT DEFAULT 'active',
  last_scraped TIMESTAMP
);

-- ARTICLES BRUTS
CREATE TABLE articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id UUID REFERENCES sources(id),
  title TEXT,
  url TEXT UNIQUE,
  raw_content TEXT,
  jina_content TEXT,  -- nettoyé par Jina AI
  pub_date TIMESTAMP,
  scraped_at TIMESTAMP DEFAULT NOW()
);

-- MENTIONS CLIENTS
CREATE TABLE mentions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id UUID REFERENCES articles(id),
  organization_id UUID REFERENCES organizations(id),
  keyword_matched TEXT,
  sentiment TEXT CHECK (sentiment IN ('positive','negative','neutral')),
  visibility_score INTEGER,
  theme TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- CONFIG CLIENTS
CREATE TABLE keywords (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  keyword TEXT NOT NULL,
  category TEXT,
  enabled BOOLEAN DEFAULT true,
  alert_threshold INTEGER DEFAULT 80
);
```

---

## 📅 8. PLANNING & LIVRABLES

### Phase 1 : Fondations (Semaines 1-2)
- ☐ VPS Hetzner CX22 configuré (Ubuntu 22.04 + Nginx)
- ☐ Supabase Pro créé (8GB PG + 100GB Storage)
- ☐ 1er scraper Fraternité Matin (Jina AI)
- ☐ FastAPI base (auth + /health)

**LIVRABLE**: API fonctionnelle + 100 articles test

### Phase 2 : Core Business (Semaines 3-4)
- ☐ Pipeline NLP complet (spaCy + Transformers)
- ☐ 5 scrapers CI opérationnels
- ☐ React dashboard v1 (tableau mentions)
- ☐ Stripe Checkout intégré

**LIVRABLE**: 1er client beta peut s'inscrire

### Phase 3 : Production (Semaines 5-6)
- ☐ Alertes email temps réel
- ☐ Graphiques Recharts (tendances)
- ☐ Monitoring Sentry + UptimeRobot
- ☐ Documentation utilisateur

**LIVRABLE**: Version 1.0 production

### Phase 4 : Scale (Semaines 7-8)
- ☐ 20+ sources scraping
- ☐ Export PDF/Excel automatisé
- ☐ WhatsApp alerts (option Pro)
- ☐ Performance optimisation

**LIVRABLE**: 10 clients paying

---

## 🎨 9. DESIGN SYSTEM

### 9.1 Palette couleurs (Côte d'Ivoire)
```css
--primary:    #1E3A8A   /* Bleu CI */
--secondary:  #F59E0B   /* Or CI */
--success:    #10B981
--warning:    #F59E0B
--danger:     #EF4444
--dark:       #1F2937
--light:      #F9FAFB
```

### 9.2 Typographie
- **Headings**: Poppins Bold (Google Fonts)
- **Body**: Inter Regular (Google Fonts)
- **Code**: JetBrains Mono

### 9.3 Pages prioritaires
1. `/login` → Supabase Auth (1 min)
2. `/dashboard` → KPI + graphiques (vue d'ensemble)
3. `/mentions` → Tableau filtrable + export
4. `/keywords` → Gestion mots-clés drag&drop
5. `/billing` → Stripe Checkout + factures
6. `/admin/sources` → Monitoring scrapers (admin only)

---

## 🔐 10. SÉCURITÉ & QUALITÉ

### 10.1 Sécurité
- ✅ HTTPS Let's Encrypt (auto-renew 90 jours)
- ✅ JWT Supabase Auth (RBAC: admin/client/viewer)
- ✅ Rate limiting: 100 req/min/client
- ✅ Input validation (Pydantic)
- ✅ OWASP Top 10 compliance
- ✅ Logs audit (Sentry)
- ✅ Backup quotidien (Supabase)

### 10.2 Performance cible
- ✅ API response: <500ms (95% percentile)
- ✅ Dashboard load: <2s (mobile 3G)
- ✅ Scraping: 5K articles/jour
- ✅ Concurrence: 100 clients simultanés
- ✅ Uptime: 99.5% (UptimeRobot)

---

## 📞 11. SUPPORT & MAINTENANCE

### 11.1 Support client
- 🌐 Discord communauté (gratuit)
- 📧 support@mediawatch.ci (SLA 24h)
- 📖 Documentation Swagger (/docs)
- 📊 Status page (UptimeRobot public)

### 11.2 Maintenance technique
- 🔄 GitHub Actions CI/CD (auto-deploy)
- 💾 Backup Supabase (quotidien + PITR)
- 🛡️ Security patches (mensuel)
- 📈 Monitoring 24/7 (Sentry + PM2)

---

## ✅ 12. CRITÈRES D'ACCEPTATION FINALE

### MVP Doit avoir (Must Have)
- ☐ Scraping 5 sources CI (>90% uptime)
- ☐ NLP précision >85% (entités + sentiment)
- ☐ Dashboard responsive mobile-first
- ☐ Stripe paiements OK (test + live)
- ☐ 1 client beta onboardé + feedback
- ☐ Deploy VPS Hetzner (99.5% uptime)
- ☐ Alertes email fonctionnelles

### MVP Devrait avoir (Should Have)
- ☐ 20+ sources scraping opérationnelles
- ☐ Export Excel/PDF automatique
- ☐ WhatsApp scraper (France24/RFI)
- ☐ Graphiques comparatifs concurrents

---

## 📄 13. LIVRABLES FINAUX
1. Code source GitHub (privé)
2. Documentation technique (ce fichier)
3. Documentation utilisateur (5 pages)
4. Schema Supabase SQL importable
5. Script deploy VPS 1-clic
6. 1 mois support technique inclus
7. Formation 2h (Zoom/vidéo)

---

## SIGNATURE

**Client** : _McCANN Douala__**Date**: __________  
**Développeur** : _Armand TEGOMO VOUKENG__ **Date**: __________

---

**Budget total estimé** : 800-1.200€ (40-60h @20€/h)  
**Durée totale** : 6-8 semaines  
**MVP live** : 05 Mars 2026

---

*MediaWatch CI - Tous droits réservés 2026*