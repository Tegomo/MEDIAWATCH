# Spécification Fonctionnelle : MediaWatch CI - Plateforme SaaS de Veille Médias

**Branche Feature** : `001-mediawatch-saas-platform`  
**Créé le** : 5 février 2026  
**Statut** : Brouillon  
**Description** : MediaWatch CI - Plateforme SaaS de veille médias pour la Côte d'Ivoire permettant le scraping automatisé de 50+ sources de presse, l'analyse NLP (sentiment, entités, thématiques), des alertes temps réel, et un dashboard analytics avec export CSV/PDF

## Scénarios Utilisateurs & Tests *(obligatoire)*

### User Story 1 - Création de Compte et Configuration des Mots-Clés (Priorité : P1)

Un responsable d'agence de communication doit surveiller les mentions de sa marque et de ses clients dans les médias ivoiriens. Il visite la plateforme, crée un compte via un flux de paiement, et configure 5-10 mots-clés à suivre (noms de marques, produits, dirigeants, concurrents).

**Pourquoi cette priorité** : C'est le point d'entrée pour tous les utilisateurs. Sans création de compte et configuration des mots-clés, aucune autre fonctionnalité ne peut fonctionner. Cela apporte une valeur immédiate en permettant aux utilisateurs de définir ce qu'ils veulent surveiller.

**Test Indépendant** : Peut être entièrement testé en complétant le flux d'inscription, en effectuant un paiement test, et en sauvegardant avec succès les mots-clés. Apporte de la valeur en établissant les paramètres de surveillance même avant que des articles ne soient scrapés.

**Scénarios d'Acceptation** :

1. **Étant donné** un nouveau visiteur sur la page d'accueil, **Quand** il clique sur "Créer un compte" et complète le formulaire de paiement avec des informations valides, **Alors** son compte est créé et il est redirigé vers la page de configuration des mots-clés
2. **Étant donné** un compte nouvellement créé sur la page de configuration des mots-clés, **Quand** il entre 5-10 mots-clés (ex: "Orange CI", "MTN", "Alassane Ouattara") et sauvegarde, **Alors** les mots-clés sont stockés et la surveillance commence pour ces termes
3. **Étant donné** un utilisateur avec un abonnement actif, **Quand** il tente d'ajouter plus de 10 mots-clés sur le plan basique, **Alors** il reçoit un message indiquant qu'il a atteint sa limite et est invité à upgrader
4. **Étant donné** un utilisateur saisissant des mots-clés, **Quand** il entre des mots-clés dupliqués ou des caractères invalides, **Alors** il reçoit un retour de validation immédiat

---

### User Story 2 - Dashboard des Mentions Quotidiennes (Priorité : P1)

Un utilisateur se connecte à son dashboard chaque matin pour consulter les mentions de ses mots-clés suivis des dernières 24 heures. Il voit une liste de 20 mentions récentes avec le nom de la source, la date de publication, l'indicateur de sentiment (positif/négatif/neutre), et un bref extrait mettant en évidence son mot-clé.

**Pourquoi cette priorité** : C'est la proposition de valeur principale - voir ce qui se dit sur votre marque. Sans cela, les utilisateurs ne peuvent pas consommer les données collectées.

**Test Indépendant** : Peut être testé en se connectant après que des articles aient été scrapés et en vérifiant que les mentions apparaissent avec les métadonnées correctes. Apporte de la valeur en fournissant une visibilité immédiate sur les mentions de marque.

**Scénarios d'Acceptation** :

1. **Étant donné** un utilisateur avec des mots-clés configurés et des articles scrapés, **Quand** il se connecte à son dashboard, **Alors** il voit ses 20 mentions les plus récentes triées par date avec source, sentiment et extrait
2. **Étant donné** un utilisateur visualisant une mention dans le dashboard, **Quand** il clique sur une mention, **Alors** il peut voir le contenu complet de l'article et les métadonnées
3. **Étant donné** un utilisateur sans mentions dans les dernières 24 heures, **Quand** il consulte son dashboard, **Alors** il voit un message indiquant l'absence de mentions récentes et des suggestions pour ajuster les mots-clés
4. **Étant donné** des mentions avec différents sentiments, **Quand** affichées dans le dashboard, **Alors** les mentions positives montrent des indicateurs verts, les négatives en rouge, et les neutres en gris

---

### User Story 3 - Alertes Email en Temps Réel (Priorité : P1)

Un utilisateur reçoit une alerte email immédiate lorsqu'une mention négative de sa marque apparaît dans les sources surveillées. L'email contient le titre de l'article, la source, l'extrait, et un lien pour voir la mention complète dans son dashboard.

**Pourquoi cette priorité** : La gestion de crise nécessite une prise de conscience immédiate. Cette fonctionnalité permet aux utilisateurs de réagir rapidement à une couverture négative, ce qui est critique pour la gestion de réputation.

**Test Indépendant** : Peut être testé en simulant la détection d'une mention négative et en vérifiant la livraison de l'email dans le délai attendu. Apporte de la valeur en permettant une réponse rapide aux mentions critiques.

**Scénarios d'Acceptation** :

1. **Étant donné** un utilisateur avec des seuils d'alerte configurés, **Quand** une mention négative (score de sentiment sous le seuil) est détectée, **Alors** une alerte email est envoyée dans les 5 minutes contenant les détails de l'article et le lien du dashboard
2. **Étant donné** un utilisateur recevant plusieurs mentions négatives en 1 heure, **Quand** les alertes sont déclenchées, **Alors** les alertes sont regroupées en un seul email pour éviter le spam
3. **Étant donné** un utilisateur avec les alertes email activées, **Quand** il veut désactiver temporairement les alertes, **Alors** il peut désactiver les alertes dans ses paramètres sans perdre sa configuration
4. **Étant donné** un email d'alerte envoyé à un utilisateur, **Quand** l'email échoue à être livré, **Alors** le système réessaie jusqu'à 3 fois et enregistre l'échec

---

### User Story 4 - Analyses de Tendances et Visualisations (Priorité : P2)

Un utilisateur veut comprendre comment le volume de mentions et le sentiment ont évolué dans le temps. Il accède à la page analytics pour voir des graphiques en ligne montrant les tendances de mentions sur 7 jours et 30 jours, et des graphiques en barres montrant quelles sources les mentionnent le plus fréquemment.

**Pourquoi cette priorité** : Bien que la surveillance quotidienne soit essentielle, comprendre les tendances aide les utilisateurs à prendre des décisions stratégiques. Cela ajoute une profondeur analytique au-delà des listes brutes de mentions.

**Test Indépendant** : Peut être testé en générant des données historiques de mentions et en vérifiant que les graphiques s'affichent correctement avec des données précises. Apporte de la valeur en fournissant des insights stratégiques sur les patterns de visibilité de marque.

**Scénarios d'Acceptation** :

1. **Étant donné** un utilisateur avec au moins 7 jours d'historique de mentions, **Quand** il consulte la page analytics, **Alors** il voit un graphique en ligne montrant le volume quotidien de mentions et la distribution du sentiment
2. **Étant donné** un utilisateur visualisant les graphiques de tendances, **Quand** il bascule entre les vues 7 jours et 30 jours, **Alors** le graphique se met à jour pour afficher la période sélectionnée
3. **Étant donné** des données de mentions provenant de plusieurs sources, **Quand** affichées en graphique en barres, **Alors** les sources sont classées par nombre de mentions avec des indicateurs visuels
4. **Étant donné** des données insuffisantes (moins de 3 jours), **Quand** un utilisateur consulte les analytics, **Alors** il voit un message indiquant que plus de données sont nécessaires pour des tendances significatives

---

### User Story 5 - Filtrage Avancé et Recherche (Priorité : P2)

Un utilisateur doit trouver des mentions spécifiques d'une période particulière, d'une source, ou d'un sentiment. Il utilise des filtres pour affiner sa liste de mentions par plage de dates, nom de source, type de sentiment, et catégorie thématique.

**Pourquoi cette priorité** : À mesure que le volume de mentions augmente, les utilisateurs ont besoin de moyens efficaces pour trouver les informations pertinentes. Le filtrage permet une analyse ciblée et des rapports.

**Test Indépendant** : Peut être testé en appliquant diverses combinaisons de filtres et en vérifiant que les résultats correspondent aux critères. Apporte de la valeur en rendant les grands ensembles de données de mentions navigables.

**Scénarios d'Acceptation** :

1. **Étant donné** un utilisateur visualisant sa liste de mentions, **Quand** il applique un filtre de plage de dates (ex: 7 derniers jours), **Alors** seules les mentions dans cette plage sont affichées
2. **Étant donné** des résultats filtrés, **Quand** un utilisateur applique plusieurs filtres (date + sentiment + source), **Alors** les résultats correspondent à tous les critères (logique ET)
3. **Étant donné** un utilisateur avec des filtres actifs, **Quand** il efface les filtres, **Alors** la liste complète non filtrée des mentions est restaurée
4. **Étant donné** des résultats de filtre, **Quand** aucune mention ne correspond aux critères, **Alors** un message clair indique l'absence de résultats et suggère d'ajuster les filtres

---

### User Story 6 - Export CSV et PDF (Priorité : P2)

Un utilisateur prépare un rapport hebdomadaire pour son équipe de direction. Il exporte ses mentions de la semaine passée sous forme de fichier CSV pour analyse dans des tableurs, ou sous forme de rapport PDF formaté pour présentation.

**Pourquoi cette priorité** : Les utilisateurs doivent partager des insights avec des parties prenantes qui n'ont peut-être pas accès à la plateforme. La fonctionnalité d'export permet l'intégration dans les workflows existants.

**Test Indépendant** : Peut être testé en déclenchant des exports et en vérifiant le format de fichier, l'exactitude du contenu, et la fonctionnalité de téléchargement. Apporte de la valeur en permettant l'analyse hors ligne et le reporting.

**Scénarios d'Acceptation** :

1. **Étant donné** un utilisateur visualisant des mentions filtrées, **Quand** il clique sur "Exporter CSV", **Alors** un fichier CSV se télécharge contenant toutes les mentions visibles avec les métadonnées complètes
2. **Étant donné** un utilisateur sélectionnant l'export PDF, **Quand** l'export se termine, **Alors** un PDF formaté avec branding, graphiques et résumés de mentions est généré
3. **Étant donné** un grand ensemble de données (500+ mentions), **Quand** un export est demandé, **Alors** le système traite l'export de manière asynchrone et envoie le lien de téléchargement par email
4. **Étant donné** des fichiers exportés, **Quand** ouverts, **Alors** les données sont correctement formatées avec en-têtes, dates en format lisible, et sans troncature

---

### User Story 7 - Monitoring de Santé des Sources (Admin) (Priorité : P3)

Un administrateur de plateforme doit s'assurer que toutes les 50+ sources médias sont scrapées avec succès. Il accède à un dashboard admin montrant le statut de chaque source (OK/KO), l'heure du dernier scraping réussi, et les messages d'erreur pour les sources en échec.

**Pourquoi cette priorité** : La fiabilité du système dépend de la collecte de données cohérente. Le monitoring admin permet une résolution proactive des problèmes avant que les utilisateurs ne remarquent des lacunes.

**Test Indépendant** : Peut être testé en simulant des échecs de sources et en vérifiant que le dashboard admin reflète un statut précis. Apporte de la valeur en permettant une supervision opérationnelle.

**Scénarios d'Acceptation** :

1. **Étant donné** un admin connecté au panneau admin, **Quand** il consulte le dashboard des sources, **Alors** il voit toutes les 50+ sources avec indicateurs de statut et horodatages du dernier scraping
2. **Étant donné** une source qui a échoué au scraping, **Quand** affichée dans le dashboard admin, **Alors** elle montre les détails de l'erreur et un bouton "Réessayer"
3. **Étant donné** des sources avec différents états de santé, **Quand** triées par statut, **Alors** les sources en échec apparaissent en haut pour attention prioritaire
4. **Étant donné** une source échouant constamment, **Quand** elle échoue 5 fois en 24 heures, **Alors** une alerte est envoyée à l'équipe admin

---

### User Story 8 - Gestion des Comptes Clients (Admin) (Priorité : P3)

Un administrateur de plateforme gère les comptes clients, incluant la capacité de suspendre des comptes pour non-paiement, réactiver des comptes, consulter les statistiques d'utilisation, et ajuster les limites de plan.

**Pourquoi cette priorité** : Les opérations commerciales nécessitent une gestion du cycle de vie des comptes. Cela permet le support client et l'application de la facturation.

**Test Indépendant** : Peut être testé en effectuant des opérations sur les comptes et en vérifiant les changements d'état et les contrôles d'accès. Apporte de la valeur en permettant l'administration de la plateforme.

**Scénarios d'Acceptation** :

1. **Étant donné** un admin consultant la liste des clients, **Quand** il sélectionne un compte client, **Alors** il voit les détails du compte, le statut d'abonnement, les métriques d'utilisation, et les boutons d'action
2. **Étant donné** un client avec des problèmes de paiement, **Quand** un admin suspend le compte, **Alors** le client ne peut pas se connecter et reçoit une notification concernant la suspension
3. **Étant donné** un compte suspendu, **Quand** le paiement est résolu et l'admin le réactive, **Alors** le client retrouve un accès complet immédiatement
4. **Étant donné** un admin consultant les statistiques d'utilisation, **Quand** il filtre par plage de dates ou type de plan, **Alors** les métriques agrégées montrent le volume de mentions, les utilisateurs actifs, et la santé du système

---

### Cas Limites

- Que se passe-t-il lorsqu'une source média change sa structure de site web et le scraping échoue ?
- Comment le système gère-t-il les articles dupliqués de la même source ?
- Que se passe-t-il lorsque le mot-clé d'un utilisateur correspond à des milliers d'articles en une seule journée ?
- Comment le système gère-t-il les caractères spéciaux ou les accents dans les mots-clés en français ivoirien (ex: "Côte d'Ivoire") ?
- Que se passe-t-il lorsque le traitement du paiement échoue pendant la création de compte ?
- Comment le système gère-t-il les modifications concurrentes des mots-clés par le même utilisateur ?
- Que se passe-t-il lorsqu'une alerte email rebondit ou que la boîte de réception de l'utilisateur est pleine ?
- Comment le système gère-t-il les sources qui nécessitent une authentification ou sont derrière des paywalls ?
- Que se passe-t-il lorsque l'analyse NLP échoue ou retourne un sentiment ambigu ?
- Comment le système gère-t-il les différences de fuseau horaire pour les dates de publication ?

## Exigences *(obligatoire)*

### Exigences Fonctionnelles

#### Compte & Authentification
- **EF-001**: Le système DOIT permettre aux utilisateurs de créer des comptes via un flux d'inscription intégré au paiement
- **EF-002**: Le système DOIT authentifier les utilisateurs de manière sécurisée et maintenir l'état de session
- **EF-003**: Le système DOIT supporter l'accès basé sur les rôles (rôles client, admin, viewer)
- **EF-004**: Les utilisateurs DOIVENT pouvoir réinitialiser leur mot de passe par email
- **EF-005**: Le système DOIT s'intégrer au traitement des paiements pour valider les abonnements

#### Gestion des Mots-Clés
- **EF-006**: Les utilisateurs DOIVENT pouvoir configurer 5-10 mots-clés par compte (limite plan basique)
- **EF-007**: Le système DOIT valider les mots-clés pour les caractères invalides et les doublons
- **EF-008**: Les utilisateurs DOIVENT pouvoir ajouter, modifier et supprimer des mots-clés à tout moment
- **EF-009**: Le système DOIT supporter les mots-clés en langue française avec gestion appropriée des accents
- **EF-010**: Les utilisateurs DOIVENT pouvoir définir des seuils d'alerte par mot-clé

#### Scraping Médias
- **EF-011**: Le système DOIT scraper au moins 5 sources médias ivoiriennes prioritaires (Fraternité Matin, Abidjan.net, Koaci.com, Linfodrome.com, France24 WhatsApp)
- **EF-012**: Le système DOIT scraper les sources à intervalles réguliers pour assurer une collecte de contenu opportune
- **EF-013**: Le système DOIT extraire le titre de l'article, le contenu, la date de publication, et l'URL source
- **EF-014**: Le système DOIT gérer les échecs de scraping avec élégance et réessayer les sources en échec
- **EF-015**: Le système DOIT détecter et prévenir le stockage d'articles dupliqués

#### Analyse NLP
- **EF-016**: Le système DOIT analyser le contenu des articles pour extraire les entités mentionnées (marques, personnes, lieux)
- **EF-017**: Le système DOIT classifier le sentiment de l'article comme positif, négatif, ou neutre
- **EF-018**: Le système DOIT catégoriser les articles par thème (politique, économie, sport, société)
- **EF-019**: Le système DOIT calculer un score de visibilité basé sur la proéminence de l'article
- **EF-020**: Le système DOIT faire correspondre les mots-clés utilisateurs avec le contenu et les entités des articles

#### Dashboard & Mentions
- **EF-021**: Les utilisateurs DOIVENT pouvoir voir leurs 20 mentions les plus récentes sur le dashboard
- **EF-022**: Le système DOIT afficher les mentions avec source, date, sentiment, extrait, et mot-clé correspondant
- **EF-023**: Les utilisateurs DOIVENT pouvoir cliquer pour voir le contenu complet de l'article
- **EF-024**: Le système DOIT mettre à jour les listes de mentions en quasi temps réel au fur et à mesure que de nouveaux articles sont traités
- **EF-025**: Les utilisateurs DOIVENT pouvoir paginer l'historique des mentions (25/50/100 par page)

#### Alertes
- **EF-026**: Le système DOIT envoyer des alertes email lorsque des mentions négatives sont détectées
- **EF-027**: Le système DOIT livrer les alertes dans les 5 minutes suivant la détection de mention
- **EF-028**: Le système DOIT regrouper plusieurs alertes en 1 heure pour prévenir le spam email
- **EF-029**: Les utilisateurs DOIVENT pouvoir configurer les préférences d'alerte (on/off, niveaux de seuil)
- **EF-030**: Le système DOIT inclure les détails de l'article et le lien du dashboard dans les emails d'alerte

#### Analytics
- **EF-031**: Les utilisateurs DOIVENT pouvoir voir les tendances de volume de mentions sur des périodes de 7 jours et 30 jours
- **EF-032**: Le système DOIT afficher la distribution du sentiment dans les visualisations de tendances
- **EF-033**: Le système DOIT montrer les principales sources par nombre de mentions en format graphique en barres
- **EF-034**: Le système DOIT gérer les scénarios de données insuffisantes avec une messagerie appropriée

#### Filtrage & Recherche
- **EF-035**: Les utilisateurs DOIVENT pouvoir filtrer les mentions par plage de dates
- **EF-036**: Les utilisateurs DOIVENT pouvoir filtrer les mentions par source
- **EF-037**: Les utilisateurs DOIVENT pouvoir filtrer les mentions par type de sentiment
- **EF-038**: Les utilisateurs DOIVENT pouvoir filtrer les mentions par catégorie thématique
- **EF-039**: Le système DOIT supporter plusieurs filtres simultanés avec logique ET
- **EF-040**: Les utilisateurs DOIVENT pouvoir effacer tous les filtres pour revenir à la vue non filtrée

#### Export
- **EF-041**: Les utilisateurs DOIVENT pouvoir exporter les mentions sous forme de fichiers CSV
- **EF-042**: Les utilisateurs DOIVENT pouvoir exporter les mentions sous forme de rapports PDF formatés
- **EF-043**: Le système DOIT inclure toutes les métadonnées de mentions dans les exports
- **EF-044**: Le système DOIT gérer les grands exports (500+ mentions) de manière asynchrone avec livraison par email

#### Fonctions Admin
- **EF-045**: Les admins DOIVENT pouvoir voir le statut de santé de toutes les sources médias
- **EF-046**: Les admins DOIVENT pouvoir réessayer manuellement les scrapings de sources en échec
- **EF-047**: Les admins DOIVENT pouvoir voir tous les comptes clients et leurs statistiques d'utilisation
- **EF-048**: Les admins DOIVENT pouvoir suspendre et réactiver les comptes clients
- **EF-049**: Le système DOIT alerter les admins lorsque des sources échouent de manière répétée
- **EF-050**: Les admins DOIVENT pouvoir ajuster les limites de plan pour des comptes individuels

### Entités Clés

- **Organisation**: Représente un compte client (agence, entreprise, institution). Possède un plan d'abonnement, un statut de paiement, des limites de mots-clés, et des métriques d'utilisation. Une organisation peut avoir plusieurs utilisateurs.

- **Utilisateur**: Représente un individu avec accès à la plateforme. Appartient à une organisation. Possède un rôle (client, admin, viewer), email, identifiants d'authentification.

- **Mot-Clé**: Représente un terme de surveillance configuré par une organisation. Possède le texte du mot-clé, catégorie, statut activé, seuil d'alerte. Appartient à une organisation.

- **Source**: Représente un média en cours de scraping. Possède nom, URL, type (presse/whatsapp/rss), score de prestige, statut de scraping, horodatage du dernier scraping.

- **Article**: Représente un article média scrapé. Possède titre, URL, contenu brut, contenu nettoyé, date de publication, horodatage de scraping. Appartient à une source.

- **Mention**: Représente une correspondance de mot-clé dans un article. Lie un article à une organisation via correspondance de mot-clé. Possède mot-clé correspondant, classification de sentiment, score de visibilité, catégorie thématique, horodatage de détection.

## Critères de Succès *(obligatoire)*

### Résultats Mesurables

- **CS-001**: Les utilisateurs peuvent compléter la création de compte et la configuration des mots-clés en moins de 3 minutes
- **CS-002**: Le système scrape 5 sources prioritaires avec >90% de disponibilité (scrapings réussis / scrapings tentés)
- **CS-003**: L'analyse de sentiment NLP atteint >85% de précision lorsque validée contre le jugement humain
- **CS-004**: Les alertes email sont livrées dans les 5 minutes suivant la détection de mention négative dans 95% des cas
- **CS-005**: Le dashboard charge la liste de mentions en moins de 2 secondes sur connexion mobile 3G
- **CS-006**: Le système gère 100 utilisateurs concurrents sans dégradation de performance
- **CS-007**: Les utilisateurs complètent avec succès leur tâche principale (visualiser les mentions) à la première tentative 90% du temps
- **CS-008**: La plateforme atteint 99,5% de disponibilité mesurée sur des périodes de 30 jours
- **CS-009**: Le coût par client réduit de 3M FCFA/mois (manuel) à 300K FCFA/mois (automatisé) - réduction de 93%
- **CS-010**: La plateforme atteint 3 clients payants d'ici le Mois 2 (point d'équilibre ROI)
- **CS-011**: La fonctionnalité d'export génère des fichiers en moins de 10 secondes pour des ensembles de données jusqu'à 500 mentions
- **CS-012**: L'admin peut identifier et résoudre les échecs de scraping de sources dans les 15 minutes suivant la détection

### Hypothèses

- Les sources médias ivoiriennes maintiennent des structures de sites web relativement stables (refonte majeure <2 fois par an)
- Les utilisateurs accèdent principalement à la plateforme pendant les heures de bureau (8h-18h WAT)
- L'utilisateur moyen surveille 7 mots-clés et génère 50-100 mentions par semaine
- Le traitement des paiements supporte à la fois les cartes de crédit internationales et Orange Money (paiement mobile Côte d'Ivoire)
- Les modèles NLP en langue française fournissent une précision suffisante pour le dialecte français ivoirien
- Les utilisateurs ont une littératie numérique de base et peuvent naviguer dans les dashboards web sans formation extensive
- L'email est le canal de communication principal pour les alertes (les alertes WhatsApp sont une amélioration future optionnelle)
