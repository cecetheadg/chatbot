-- ============================================
-- Chatbot L0027 - Initialisation PostgreSQL
-- ============================================

-- Extension UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Extension pour la recherche texte en français
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Configuration de la recherche texte française
-- Note: CREATE TEXT SEARCH CONFIGURATION doesn't support IF NOT EXISTS, so we check first
DO $$
BEGIN
    -- Vérifier si la configuration existe déjà
    IF NOT EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'french_unaccent'
    ) THEN
        -- Créer la configuration si elle n'existe pas
        CREATE TEXT SEARCH CONFIGURATION french_unaccent (COPY = french);
        
        -- Modifier le mapping pour utiliser unaccent et french_stem
        ALTER TEXT SEARCH CONFIGURATION french_unaccent
            ALTER MAPPING FOR hword, hword_part, word WITH unaccent, french_stem;
    ELSE
        -- Si elle existe déjà, juste mettre à jour le mapping
        ALTER TEXT SEARCH CONFIGURATION french_unaccent
            ALTER MAPPING FOR hword, hword_part, word WITH unaccent, french_stem;
    END IF;
END $$;

-- ============================================
-- Tables (créées par SQLAlchemy, mais backup ici)
-- ============================================

-- Note: Les tables sont créées automatiquement par SQLAlchemy
-- Ce script est pour la configuration initiale et les index supplémentaires

-- Index pour la recherche full-text sur les questions
-- CREATE INDEX IF NOT EXISTS idx_question_logs_fts 
--     ON question_logs USING GIN (to_tsvector('french_unaccent', question));

-- ============================================
-- Fonctions utilitaires
-- ============================================

-- Fonction pour nettoyer le texte français
CREATE OR REPLACE FUNCTION normalize_french(text_input TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN lower(unaccent(trim(text_input)));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================
-- Données initiales
-- ============================================

-- Rien à insérer au démarrage, les données viennent de l'application

-- ============================================
-- Permissions
-- ============================================

-- Accorder les permissions à l'utilisateur de l'application
-- (ajuster selon votre configuration)

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chatbot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chatbot_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO chatbot_user;

-- Message de confirmation
DO $$
BEGIN
    RAISE NOTICE 'Base de données Chatbot L0027 initialisée avec succès!';
END $$;
