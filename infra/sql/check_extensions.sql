-- infra/sql/check_extensions.sql : vérifie que chaque extension fonctionne
\set ON_ERROR_STOP on
SELECT extname, extversion FROM pg_extension WHERE extname <> 'plpgsql' ORDER BY extname;

BEGIN;
-- pg_stat_statements : chargé au démarrage du serveur
SELECT count(*) >= 0 AS pg_stat_statements_actif FROM pg_stat_statements;
-- vector : distance entre deux vecteurs
SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector AS distance_vector;
-- unaccent + pg_trgm : similarité d'un nom avec et sans accents
SELECT similarity(unaccent('Société Générale'), 'Societe Generale') AS similarite;
-- fuzzystrmatch : distance de Levenshtein
SELECT levenshtein('Amundi', 'Amundy') AS levenshtein;
-- btree_gist : contrainte d'exclusion (identifiant égal + périodes qui se chevauchent)
CREATE TEMP TABLE t_scd2 (
  isin text,
  validity tstzrange,
  EXCLUDE USING gist (isin WITH =, validity WITH &&)
);
INSERT INTO t_scd2 VALUES ('FR0000120271', '[2024-01-01,2025-01-01)');
INSERT INTO t_scd2 VALUES ('FR0000120271', '[2025-01-01,2026-01-01)');
DO $$
BEGIN
  INSERT INTO t_scd2 VALUES ('FR0000120271', '[2025-06-01,2025-07-01)');
  RAISE EXCEPTION 'ECHEC : le chevauchement aurait dû être refusé';
EXCEPTION WHEN exclusion_violation THEN
  RAISE NOTICE 'OK : le chevauchement est refusé (btree_gist)';
END $$;
ROLLBACK;
