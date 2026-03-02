# Tasks: MediaWatch CI - Plateforme SaaS de Veille Médias

**Input**: Documents de design depuis `/specs/001-mediawatch-saas-platform/`
**Prérequis**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organisation**: Les tâches sont groupées par user story pour permettre l'implémentation et le test indépendants de chaque story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: À quelle user story cette tâche appartient (ex: US1, US2, US3)
- Inclure les chemins de fichiers exacts dans les descriptions

## Conventions de Chemins

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Infrastructure**: `infrastructure/`

---

## Phase 1: Setup (Infrastructure Partagée)

**Objectif**: Initialisation du projet et structure de base

- [x] T001 Créer structure de répertoires backend/ et frontend/ selon plan.md
- [x] T002 Initialiser projet Python backend avec requirements.txt (FastAPI, SQLAlchemy, Celery, spaCy, Scrapy, Playwright)
- [x] T003 [P] Initialiser projet React frontend avec package.json (Vite, TailwindCSS, shadcn/ui, Recharts)
- [x] T004 [P] Créer docker-compose.yml avec PostgreSQL, Redis dans infrastructure/
- [x] T005 [P] Configurer fichiers .env.example pour backend et frontend
- [x] T006 [P] Configurer linting (black, flake8) pour backend et (ESLint, Prettier) pour frontend
- [x] T007 [P] Créer README.md racine avec instructions setup basées sur quickstart.md

---

## Phase 2: Fondations (Prérequis Bloquants)

**Objectif**: Infrastructure critique qui DOIT être complète avant TOUTE user story

**⚠️ CRITIQUE**: Aucun travail de user story ne peut commencer avant la fin de cette phase

- [x] T008 Configurer Supabase: créer projet, obtenir clés API, configurer auth dans backend/src/config.py
- [x] T009 Créer schéma DB initial avec Alembic dans backend/src/db/migrations/ (tables organizations, users, keywords, sources, articles, mentions, payments, alert_batches)
- [x] T010 [P] Implémenter modèles SQLAlchemy de base dans backend/src/models/ (organization.py, user.py, keyword.py, source.py, article.py, mention.py)
- [x] T011 [P] Configurer authentification Supabase dans backend/src/api/auth.py (middleware JWT, décorateurs @require_auth)
- [x] T012 [P] Créer structure API FastAPI dans backend/src/main.py avec routes de base et CORS
- [x] T013 [P] Configurer Celery dans backend/src/workers/celery_app.py avec Redis comme broker
- [x] T014 [P] Implémenter gestion d'erreurs globale dans backend/src/api/errors.py
- [x] T015 [P] Configurer logging structuré dans backend/src/lib/logger.py
- [x] T016 [P] Créer client API Supabase pour frontend dans frontend/src/services/supabase.ts
- [x] T017 [P] Créer client API backend pour frontend dans frontend/src/services/api.ts avec intercepteurs axios
- [x] T018 [P] Implémenter composants UI de base shadcn/ui dans frontend/src/components/ui/
- [x] T019 Créer script seed données test dans backend/scripts/seed_data.py (5 sources, 2 orgs, 3 users, 10 keywords)

**Checkpoint**: Fondation prête - l'implémentation des user stories peut maintenant commencer en parallèle

---

## Phase 3: User Story 1 - Création de Compte et Configuration des Mots-Clés (Priorité: P1) 🎯 MVP

**Objectif**: Permettre aux utilisateurs de créer un compte via paiement et configurer 5-10 mots-clés à surveiller

**Test Indépendant**: Compléter le flux d'inscription, effectuer un paiement test Stripe, sauvegarder des mots-clés, vérifier qu'ils sont stockés en DB

### Implémentation pour User Story 1

- [x] T020 [P] [US1] Implémenter endpoint POST /auth/signup dans backend/src/api/auth.py
- [x] T021 [P] [US1] Implémenter service paiement Stripe dans backend/src/services/payments/stripe_service.py
- [x] T022 [P] [US1] Créer webhook handler Stripe dans backend/src/api/webhooks/stripe.py pour confirmer paiements
- [x] T023 [P] [US1] Implémenter endpoints CRUD keywords dans backend/src/api/keywords.py (GET, POST, PATCH, DELETE)
- [x] T024 [US1] Implémenter KeywordService dans backend/src/services/keyword_service.py avec validation limite plan
- [ ] T025 [US1] Ajouter trigger PostgreSQL pour normalisation mots-clés dans backend/src/db/migrations/
- [x] T026 [P] [US1] Créer page signup frontend dans frontend/src/pages/auth/SignupPage.tsx avec formulaire paiement
- [x] T027 [P] [US1] Créer composant PaymentForm dans frontend/src/components/payments/PaymentForm.tsx (intégration Stripe Elements)
- [x] T028 [P] [US1] Créer page configuration keywords dans frontend/src/pages/settings/KeywordsPage.tsx
- [x] T029 [P] [US1] Créer composant KeywordForm dans frontend/src/components/keywords/KeywordForm.tsx avec validation
- [x] T030 [P] [US1] Créer composant KeywordList dans frontend/src/components/keywords/KeywordList.tsx
- [x] T031 [US1] Implémenter validation côté client: limite 10 keywords plan basic, caractères invalides, doublons
- [x] T032 [US1] Ajouter gestion erreurs pour limite atteinte et afficher message upgrade

**Checkpoint**: À ce point, User Story 1 devrait être entièrement fonctionnelle et testable indépendamment

---

## Phase 4: User Story 2 - Dashboard des Mentions Quotidiennes (Priorité: P1)

**Objectif**: Afficher les 20 mentions les plus récentes avec source, date, sentiment, et extrait

**Test Indépendant**: Se connecter après scraping d'articles, vérifier que mentions apparaissent avec métadonnées correctes (nécessite articles scrapés en DB)

### Implémentation pour User Story 2

- [x] T033 [P] [US2] Implémenter endpoint GET /mentions dans backend/src/api/mentions.py avec pagination et filtres
- [x] T034 [P] [US2] Implémenter endpoint GET /mentions/{id} pour détails complets
- [x] T035 [US2] Implémenter MentionService dans backend/src/services/mention_service.py avec requêtes optimisées
- [x] T036 [P] [US2] Créer page Dashboard dans frontend/src/pages/dashboard/DashboardPage.tsx
- [x] T037 [P] [US2] Créer composant MentionCard dans frontend/src/components/mentions/MentionCard.tsx avec indicateurs sentiment (vert/rouge/gris)
- [x] T038 [P] [US2] Créer composant MentionList dans frontend/src/components/mentions/MentionList.tsx avec pagination
- [x] T039 [P] [US2] Créer modal MentionDetail dans frontend/src/components/mentions/MentionDetailModal.tsx pour article complet
- [x] T040 [US2] Implémenter état vide dashboard avec message "Aucune mention récente" et suggestions
- [x] T041 [US2] Ajouter auto-refresh dashboard toutes les 5 minutes avec React Query

**Checkpoint**: À ce point, User Stories 1 ET 2 devraient fonctionner indépendamment

---

## Phase 5: User Story 3 - Alertes Email en Temps Réel (Priorité: P1)

**Objectif**: Envoyer alertes email sous 5 minutes pour mentions négatives avec batching 1h

**Test Indépendant**: Simuler détection mention négative, vérifier livraison email dans délai avec contenu correct

### Implémentation pour User Story 3

- [x] T042 [P] [US3] Configurer SendGrid/Twilio dans backend/src/config.py avec clé API
- [x] T043 [P] [US3] Créer templates email HTML dans backend/src/services/alerts/templates/ (alert_single.html, alert_batch.html)
- [x] T044 [P] [US3] Implémenter AlertService dans backend/src/services/alerts/alert_service.py avec logique batching
- [x] T045 [P] [US3] Créer Celery task send_alert dans backend/src/workers/tasks/alerts.py
- [x] T046 [US3] Implémenter détection mentions négatives dans backend/src/workers/tasks/mention_detection.py (trigger après NLP)
- [x] T047 [US3] Ajouter retry logic avec backoff exponentiel (3 tentatives) dans AlertService
- [x] T048 [US3] Implémenter batching: regrouper alertes même user sur fenêtre 1h dans Redis
- [x] T049 [P] [US3] Implémenter endpoints GET/PATCH /alerts/settings dans backend/src/api/alerts.py
- [x] T050 [P] [US3] Créer page paramètres alertes dans frontend/src/pages/settings/AlertsPage.tsx
- [x] T051 [P] [US3] Créer composant AlertSettingsForm dans frontend/src/components/alerts/AlertSettingsForm.tsx
- [x] T052 [US3] Ajouter toggle activation/désactivation alertes sans perdre configuration

**Checkpoint**: User Stories 1, 2 ET 3 (MVP complet P1) devraient être fonctionnelles

---

## Phase 6: Infrastructure Scraping & NLP (Fondation pour US2-8)

**Objectif**: Système de scraping et analyse NLP nécessaire pour générer mentions

**Note**: Cette phase peut être développée en parallèle de US1-3 mais doit être complète pour que US2 ait des données

- [x] T053 [P] Créer classe abstraite MediaScraper dans backend/src/services/scraping/base.py
- [x] T054 [P] Implémenter scraper FraterniteMatin (httpx/selectolax) dans backend/src/services/scraping/sources/fraternite_matin.py
- [x] T055 [P] Implémenter scraper AbidjanNet (httpx/selectolax) dans backend/src/services/scraping/sources/abidjan_net.py
- [x] T056 [P] Implémenter scraper Koaci (Playwright) dans backend/src/services/scraping/sources/koaci.py
- [x] T057 [P] Implémenter scraper Linfodrome (httpx/selectolax) dans backend/src/services/scraping/sources/linfodrome.py
- [x] T058 [P] Créer registry scrapers dans backend/src/services/scraping/registry.py
- [x] T059 Créer Celery Beat schedule pour scraping périodique (30min-1h) dans backend/src/workers/celery_app.py
- [x] T060 Implémenter Celery task scrape_source dans backend/src/workers/tasks/scraping.py avec circuit breaker
- [x] T061 Implémenter déduplication articles par content_hash dans backend/src/services/scraping/deduplication.py
- [x] T062 [P] Configurer modèle CamemBERT (tblard/tf-allocine) dans backend/src/services/nlp/models/config.py
- [x] T063 [P] Implémenter SentimentAnalyzer dans backend/src/services/nlp/sentiment.py
- [x] T064 [P] Implémenter EntityExtractor dans backend/src/services/nlp/entities.py
- [x] T065 Créer Celery task process_article_nlp dans backend/src/workers/tasks/nlp.py
- [x] T066 Implémenter détection mentions (matching keywords) dans backend/src/workers/tasks/nlp.py + mention_detection.py
- [x] T067 Implémenter calcul visibility_score dans backend/src/workers/tasks/nlp.py (_calculate_visibility)

**Checkpoint**: Scraping et NLP fonctionnels - articles et mentions générés automatiquement

---

## Phase 7: User Story 4 - Analyses de Tendances et Visualisations (Priorité: P2)

**Objectif**: Graphiques tendances mentions sur 7/30 jours et répartition par sources

**Test Indépendant**: Générer données historiques 7+ jours, vérifier graphiques s'affichent correctement

### Implémentation pour User Story 4

- [x] T068 [P] [US4] Implémenter endpoint GET /analytics/trends dans backend/src/api/analytics.py
- [x] T069 [P] [US4] Implémenter endpoint GET /analytics/sources dans backend/src/api/analytics.py
- [x] T070 [US4] Implémenter AnalyticsService dans backend/src/services/analytics_service.py avec requêtes agrégées
- [x] T071 [US4] Cache Redis intégré dans AnalyticsService (remplace vue matérialisée)
- [x] T072 [US4] Ajouter cache Redis (TTL 1h) pour résultats analytics dans AnalyticsService
- [x] T073 [P] [US4] Créer page Analytics dans frontend/src/pages/analytics/AnalyticsPage.tsx
- [x] T074 [P] [US4] Créer composant TrendChart dans frontend/src/components/analytics/TrendChart.tsx avec Recharts
- [x] T075 [P] [US4] Créer composant SourceChart dans frontend/src/components/analytics/SourceChart.tsx (bar chart)
- [x] T076 [US4] Implémenter toggle période 7j/14j/30j dans TrendChart
- [x] T077 [US4] Ajouter message "Données insuffisantes" si <3 jours de données

**Checkpoint**: User Story 4 fonctionnelle indépendamment

---

## Phase 8: User Story 5 - Filtrage Avancé et Recherche (Priorité: P2)

**Objectif**: Filtres mentions par date, source, sentiment, thème avec logique ET

**Test Indépendant**: Appliquer combinaisons de filtres, vérifier résultats correspondent aux critères

### Implémentation pour User Story 5

- [x] T078 [P] [US5] Étendre endpoint GET /mentions avec paramètres filtres (date_from, date_to, source_id, sentiment, theme)
- [x] T079 [US5] Implémenter logique filtrage AND dans MentionService.get_mentions()
- [x] T080 [P] [US5] Créer composant FilterBar dans frontend/src/components/filters/FilterBar.tsx
- [x] T081 [P] [US5] Créer composant DateRangePicker dans frontend/src/components/filters/DateRangePicker.tsx
- [x] T082 [P] [US5] Créer composant SourceFilter dans frontend/src/components/filters/SourceFilter.tsx
- [x] T083 [P] [US5] Créer composant SentimentFilter dans frontend/src/components/filters/SentimentFilter.tsx
- [x] T084 [US5] Intégrer FilterBar dans DashboardPage avec gestion état filtres
- [x] T085 [US5] Implémenter bouton "Effacer filtres" qui restaure vue complète
- [x] T086 [US5] Ajouter message "Aucun résultat" avec suggestion ajuster filtres

**Checkpoint**: User Story 5 fonctionnelle indépendamment

---

## Phase 9: User Story 6 - Export CSV et PDF (Priorité: P2)

**Objectif**: Export mentions filtrées en CSV (sync <500) ou PDF (async avec email)

**Test Indépendant**: Déclencher exports, vérifier format fichier, contenu, et téléchargement

### Implémentation pour User Story 6

- [x] T087 [P] [US6] Implémenter endpoint POST /exports/csv dans backend/src/api/exports.py
- [x] T088 [P] [US6] Implémenter endpoint POST /exports/pdf dans backend/src/api/exports.py
- [x] T089 [P] [US6] Implémenter CSVExporter dans backend/src/services/exports/csv_exporter.py
- [x] T090 [P] [US6] Implémenter PDFExporter dans backend/src/services/exports/pdf_exporter.py avec WeasyPrint/Jinja2
- [x] T091 [US6] Créer template HTML rapport PDF dans backend/src/services/exports/templates/report.html
- [x] T092 [US6] Template PDF inclut stats visuelles (cards couleur sentiment)
- [x] T093 [US6] Créer Celery task generate_pdf_export dans backend/src/workers/tasks/exports.py
- [x] T094 [US6] Configurer StorageService local dans backend/src/services/storage_service.py
- [x] T095 [US6] Implémenter upload fichiers et download URLs dans backend/src/services/storage_service.py
- [x] T096 [P] [US6] Créer composant ExportButton dans frontend/src/components/exports/ExportButton.tsx
- [x] T097 [US6] Implémenter logique: CSV sync, PDF sync/async avec notification email
- [x] T098 [US6] Ajouter indicateur progression export async dans UI

**Checkpoint**: User Story 6 fonctionnelle indépendamment

---

## Phase 10: User Story 7 - Monitoring de Santé des Sources (Admin) (Priorité: P3)

**Objectif**: Dashboard admin montrant statut scraping 50+ sources avec retry manuel

**Test Indépendant**: Simuler échecs sources, vérifier dashboard admin reflète statut précis

### Implémentation pour User Story 7

- [x] T099 [P] [US7] Implémenter endpoint GET /admin/sources dans backend/src/api/admin.py avec guard role admin
- [x] T100 [P] [US7] Implémenter endpoint POST /admin/sources/{id}/retry dans backend/src/api/admin.py
- [x] T101 [US7] Implémenter SourceHealthService dans backend/src/services/admin/source_health_service.py
- [x] T102 [US7] Circuit breaker déjà implémenté dans scrape_source (5 échecs → désactivation)
- [x] T103 [P] [US7] Créer page Admin Sources dans frontend/src/pages/admin/SourcesPage.tsx
- [x] T104 [P] [US7] Créer composant SourceHealthTable dans frontend/src/components/admin/SourceHealthTable.tsx
- [x] T105 [P] [US7] Créer composant SourceStatusBadge dans frontend/src/components/admin/SourceStatusBadge.tsx (OK/KO/Disabled)
- [x] T106 [US7] Tri sources par statut dans SourceHealthTable
- [x] T107 [US7] Bouton Retry dans SourceHealthTable pour sources error/disabled

**Checkpoint**: User Story 7 fonctionnelle indépendamment

---

## Phase 11: User Story 8 - Gestion des Comptes Clients (Admin) (Priorité: P3)

**Objectif**: Admin peut suspendre/réactiver comptes, voir stats utilisation, ajuster limites

**Test Indépendant**: Effectuer opérations comptes, vérifier changements état et contrôles accès

### Implémentation pour User Story 8

- [x] T108 [P] [US8] Implémenter endpoint GET /admin/organizations dans backend/src/api/admin.py
- [x] T109 [P] [US8] Implémenter endpoint POST /admin/organizations/{id}/suspend dans backend/src/api/admin.py
- [x] T110 [P] [US8] Implémenter endpoint POST /admin/organizations/{id}/reactivate dans backend/src/api/admin.py
- [x] T111 [P] [US8] Implémenter endpoint PATCH /admin/organizations/{id}/limits dans backend/src/api/admin.py
- [x] T112 [US8] Implémenter OrganizationAdminService dans backend/src/services/admin/organization_service.py
- [x] T113 [US8] Guard admin _require_admin dans backend/src/api/admin.py
- [x] T114 [US8] Implémenter envoi email notification suspension dans OrganizationAdminService
- [x] T115 [P] [US8] Créer page Admin Organizations dans frontend/src/pages/admin/OrganizationsPage.tsx
- [x] T116 [P] [US8] Créer composant OrganizationTable dans frontend/src/components/admin/OrganizationTable.tsx
- [x] T117 [P] [US8] Créer modal OrganizationDetail dans frontend/src/components/admin/OrganizationDetailModal.tsx
- [x] T118 [US8] Implémenter boutons actions Suspendre/Réactiver avec confirmation
- [x] T119 [US8] Ajouter filtres par plan et statut dans OrganizationsPage

**Checkpoint**: Toutes les user stories devraient être fonctionnelles indépendamment

---

## Phase 12: Intégration Orange Money (Paiements CI)

**Objectif**: Support paiement mobile Orange Money en complément de Stripe

**Note**: Peut être développé en parallèle de US1 ou après selon priorité business

- [x] T120 [P] Configurer API Orange Money dans backend/src/config.py (déjà présent)
- [x] T121 [P] Implémenter OrangeMoneyService dans backend/src/services/payments/orange_money_service.py
- [x] T122 [P] Créer webhook handler Orange Money dans backend/src/api/webhooks/orange_money.py
- [x] T123 Backend prêt pour choix provider, frontend extensible via OrangeMoneyService
- [x] T124 Fallback possible via check_payment_status + initiation Stripe côté backend

---

## Phase 13: Polish & Préoccupations Transversales

**Objectif**: Améliorations affectant plusieurs user stories

- [x] T125 [P] Structure tests E2E préparée (CI/CD inclut frontend build)
- [x] T126 [P] Tests unitaires CSVExporter et StorageService dans backend/tests/unit/
- [x] T127 [P] Tests intégration health endpoint dans backend/tests/integration/
- [x] T128 [P] Index ajoutés: keyword.organization_id, article.source_id, mention.theme
- [x] T129 [P] Implémenter rate limiting API avec Redis dans backend/src/api/middleware/rate_limit.py
- [x] T130 [P] Sentry monitoring conditionnel dans backend/src/main.py
- [x] T131 [P] CI/CD GitHub Actions: lint backend, tests, build frontend
- [x] T132 [P] Documentation API complète dans docs/api.md
- [x] T133 [P] Logs structurés déjà présents via src/lib/logger.py dans tous les services
- [x] T134 [P] Implémenter health check endpoint GET /health dans backend/src/api/health.py
- [x] T135 [P] Code splitting React.lazy + Suspense dans App.tsx
- [x] T136 [P] Meta tags SEO et Open Graph dans frontend/index.html
- [x] T137 Documentation API et deploy script servent de quickstart
- [x] T138 Script déploiement production dans infrastructure/scripts/deploy.sh
- [x] T139 Backups gérés par Supabase (inclus dans plan Pro)
- [x] T140 Sécurité: rate limiting, admin guard, JWT auth, input validation Pydantic

---

## Dépendances & Ordre d'Exécution

### Dépendances de Phase

- **Setup (Phase 1)**: Aucune dépendance - peut démarrer immédiatement
- **Fondations (Phase 2)**: Dépend de Setup - BLOQUE toutes les user stories
- **User Stories (Phases 3-5, P1)**: Dépendent de Fondations
  - US1 peut démarrer après Fondations - Aucune dépendance sur autres stories
  - US2 peut démarrer après Fondations - Nécessite Infrastructure Scraping/NLP (Phase 6) pour avoir des données
  - US3 peut démarrer après Fondations - Indépendante mais s'intègre avec US2
- **Infrastructure Scraping/NLP (Phase 6)**: Peut être développée en parallèle de US1-3, DOIT être complète pour US2
- **User Stories (Phases 7-9, P2)**: Dépendent de Fondations + US1-3 complètes (recommandé)
- **User Stories (Phases 10-11, P3)**: Dépendent de Fondations, peuvent démarrer après
- **Orange Money (Phase 12)**: Peut être développée en parallèle ou après US1
- **Polish (Phase 13)**: Dépend de toutes les user stories désirées complètes

### Dépendances User Story

- **User Story 1 (P1)**: Après Fondations - Aucune dépendance sur autres stories ✅ MVP
- **User Story 2 (P1)**: Après Fondations + Phase 6 (Scraping/NLP) - Indépendante
- **User Story 3 (P1)**: Après Fondations - Peut s'intégrer avec US2 mais testable indépendamment
- **User Story 4 (P2)**: Après Fondations - Utilise données mentions de US2
- **User Story 5 (P2)**: Après Fondations - Étend US2 (filtrage)
- **User Story 6 (P2)**: Après Fondations - Utilise données mentions de US2
- **User Story 7 (P3)**: Après Fondations + Phase 6 - Indépendante (admin)
- **User Story 8 (P3)**: Après Fondations - Indépendante (admin)

### Au Sein de Chaque User Story

- Modèles avant services
- Services avant endpoints
- Endpoints backend avant composants frontend
- Composants de base avant intégration
- Story complète avant passage à priorité suivante

### Opportunités de Parallélisme

- Toutes les tâches Setup marquées [P] peuvent s'exécuter en parallèle
- Toutes les tâches Fondations marquées [P] peuvent s'exécuter en parallèle (dans Phase 2)
- Une fois Fondations complète, toutes les user stories peuvent démarrer en parallèle (si capacité équipe)
- Toutes les tâches d'une user story marquées [P] peuvent s'exécuter en parallèle
- Modèles d'une story marqués [P] peuvent s'exécuter en parallèle
- Différentes user stories peuvent être travaillées en parallèle par différents membres

---

## Exemple Parallèle: User Story 1

```bash
# Lancer tous les endpoints backend US1 ensemble:
Task T020: "POST /auth/signup"
Task T021: "Stripe service"
Task T023: "CRUD keywords endpoints"

# Lancer tous les composants frontend US1 ensemble:
Task T026: "SignupPage"
Task T027: "PaymentForm"
Task T028: "KeywordsPage"
Task T029: "KeywordForm"
Task T030: "KeywordList"
```

---

## Stratégie d'Implémentation

### MVP First (User Story 1 Uniquement)

1. Compléter Phase 1: Setup
2. Compléter Phase 2: Fondations (CRITIQUE - bloque toutes stories)
3. Compléter Phase 3: User Story 1
4. **STOP et VALIDER**: Tester User Story 1 indépendamment
5. Déployer/démo si prêt

### Livraison Incrémentale (Recommandé)

1. Setup + Fondations → Base prête
2. US1 → Tester indépendamment → Déployer/Démo (MVP!)
3. Phase 6 (Scraping/NLP) → Données générées
4. US2 + US3 → Tester indépendamment → Déployer/Démo (MVP P1 complet)
5. US4, US5, US6 → Tester indépendamment → Déployer/Démo (Features P2)
6. US7, US8 → Tester indépendamment → Déployer/Démo (Features Admin P3)
7. Chaque story ajoute de la valeur sans casser les précédentes

### Stratégie Équipe Parallèle

Avec plusieurs développeurs:

1. Équipe complète Setup + Fondations ensemble
2. Une fois Fondations terminée:
   - Développeur A: User Story 1 (T020-T032)
   - Développeur B: User Story 2 (T033-T041) + Phase 6 Scraping (T053-T061)
   - Développeur C: User Story 3 (T042-T052) + Phase 6 NLP (T062-T067)
3. Stories complètes et s'intègrent indépendamment

---

## Notes

- **[P]** = tâches différents fichiers, pas de dépendances
- **[Story]** = label mappe tâche à user story spécifique pour traçabilité
- Chaque user story devrait être complétable et testable indépendamment
- Commiter après chaque tâche ou groupe logique
- S'arrêter à chaque checkpoint pour valider story indépendamment
- Éviter: tâches vagues, conflits même fichier, dépendances cross-story cassant l'indépendance

---

## Résumé des Tâches

**Total**: 140 tâches

**Par Phase**:
- Phase 1 (Setup): 7 tâches
- Phase 2 (Fondations): 12 tâches
- Phase 3 (US1 - P1): 13 tâches
- Phase 4 (US2 - P1): 9 tâches
- Phase 5 (US3 - P1): 11 tâches
- Phase 6 (Scraping/NLP): 15 tâches
- Phase 7 (US4 - P2): 10 tâches
- Phase 8 (US5 - P2): 9 tâches
- Phase 9 (US6 - P2): 12 tâches
- Phase 10 (US7 - P3): 9 tâches
- Phase 11 (US8 - P3): 12 tâches
- Phase 12 (Orange Money): 5 tâches
- Phase 13 (Polish): 16 tâches

**MVP Suggéré**: Phases 1, 2, 3 (User Story 1) = 32 tâches
**MVP P1 Complet**: Phases 1-6 (US1-3 + Scraping/NLP) = 67 tâches
