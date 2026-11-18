-- infra/sql/bootstrap.sql : prépare la base du projet (idempotent)
-- Variables psql attendues : app_pw, ro_pw

-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 2. Rôles : création si absents, mot de passe toujours resynchronisé avec le .env
SELECT format('CREATE ROLE refdata_app LOGIN PASSWORD %L', :'app_pw')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'refdata_app') \gexec
SELECT format('ALTER ROLE refdata_app PASSWORD %L', :'app_pw') \gexec

SELECT format('CREATE ROLE refdata_ro LOGIN PASSWORD %L', :'ro_pw')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'refdata_ro') \gexec
SELECT format('ALTER ROLE refdata_ro PASSWORD %L', :'ro_pw') \gexec

ALTER ROLE refdata_ro SET default_transaction_read_only = on;
ALTER ROLE refdata_ro SET statement_timeout = '30s';

-- 3. Accès à la base : seulement les deux rôles du projet
REVOKE ALL ON DATABASE refdata FROM PUBLIC;
GRANT CONNECT ON DATABASE refdata TO refdata_app, refdata_ro;
ALTER DATABASE refdata SET timezone TO 'UTC';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- 4. Schémas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS ops;

-- 5. Droits : l'application crée et écrit ; le rôle de lecture lit seulement
GRANT USAGE, CREATE ON SCHEMA raw, staging, core, marts, ops TO refdata_app;
GRANT USAGE ON SCHEMA raw, staging, core, marts, ops TO refdata_ro;
GRANT USAGE ON SCHEMA public TO refdata_app, refdata_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA raw, staging, core, marts, ops TO refdata_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE refdata_app IN SCHEMA raw, staging, core, marts, ops
GRANT SELECT ON TABLES TO refdata_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE refdata_owner IN SCHEMA raw, staging, core, marts, ops
GRANT SELECT ON TABLES TO refdata_ro;
