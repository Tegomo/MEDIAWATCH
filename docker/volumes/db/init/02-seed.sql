-- MediaWatch CI - Seed data for local development
-- Sources médias ivoiriennes

INSERT INTO sources (id, name, url, type, scraper_class, scraping_enabled, prestige_score) VALUES
    (uuid_generate_v4(), 'Abidjan.net', 'https://news.abidjan.net', 'PRESS', 'jina_reader', TRUE, 80),
    (uuid_generate_v4(), 'Fraternité Matin', 'https://www.fratmat.info', 'PRESS', 'jina_reader', TRUE, 85),
    (uuid_generate_v4(), 'L''Infodrome', 'https://www.linfodrome.com', 'PRESS', 'jina_reader', TRUE, 70),
    (uuid_generate_v4(), 'Jina Search API', 'https://s.jina.ai', 'API', 'jina_search', FALSE, 50)
ON CONFLICT (name) DO NOTHING;

-- Note: les utilisateurs (organizations + users) sont créés via l'API auth
-- qui les insère à la fois dans Supabase Auth (GoTrue) et dans la table users.
-- Pour créer les utilisateurs de test, lancez le script create_auth_users après le démarrage.
