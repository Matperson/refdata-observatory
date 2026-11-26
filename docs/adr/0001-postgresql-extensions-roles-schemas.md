# ADR 0001 : PostgreSQL, extensions, rôles, schémas et amorçage

- **Statut** : accepté
- **Date** : 2026-11-26
- **Décideur** : Matperson
- **Liens** : `infra/compose.yaml`, `infra/sql/bootstrap.sql`, `docs/environment.md`

## Contexte

Le projet consolide des données de référence financières publiques (ESMA FIRDS, GLEIF,
OpenFIGI, BCE) et mesure leur qualité. Les besoins qui orientent la base :

- rapprocher des entités entre sources (noms d'émetteurs, LEI, ISIN) avec des noms
  hétérogènes (accents, abréviations, fautes) ;
- conserver l'historique des valeurs de référence (périodes de validité) ;
- séparer les données brutes, nettoyées, modélisées et publiées ;
- tourner en local, sans serveur ni service payant, sur Fedora avec Podman rootless ;
- ne jamais stocker de secret dans le dépôt, qui est public.

## Décisions

### D1. PostgreSQL 18 avec pgvector, via une image épinglée

Image `docker.io/pgvector/pgvector:0.8.7-pg18` (PostgreSQL 18.7, pgvector 0.8.7).

Alternatives écartées :
- **Image `postgres` officielle + compilation de pgvector** : plus de travail, plus de
  surface de maintenance, aucun gain.
- **Base vectorielle dédiée (Qdrant, etc.)** : un service de plus pour un volume faible,
  et on perd les jointures SQL entre vecteurs et données de référence.
- **SQLite / DuckDB seuls** : pas de rôles ni de droits, donc impossible de démontrer la
  séparation des accès, qui fait partie des objectifs du projet.

### D2. Six extensions activées

| Extension | Usage dans le projet |
|---|---|
| `vector` | similarité sémantique entre noms d'entités (rapprochement) |
| `pg_trgm` | rapprochement approximatif de noms, index de recherche par similarité |
| `fuzzystrmatch` | distance de Levenshtein, codes phonétiques en complément de trigrammes |
| `unaccent` | normalisation des noms avant comparaison |
| `btree_gist` | contraintes d'exclusion sur périodes de validité (pas de chevauchement) |
| `pg_stat_statements` | mesure des requêtes lentes (chargée au démarrage du serveur) |

`pg_stat_statements` impose `shared_preload_libraries` : c'est pourquoi la commande du
conteneur est surchargée dans `compose.yaml`.

Alternatives pour le rapprochement de noms :
- **Faire le calcul en Python (rapidfuzz)** : plus souple, mais les données sortent de la
  base et on perd les index.
- **Un moteur de recherche (Elasticsearch, etc.)** : disproportionné ici.

### D3. Extensions écartées

| Extension | Raison |
|---|---|
| `pgcrypto` | aucun besoin de chiffrement en base ; les empreintes éventuelles se calculent hors base |
| `uuid-ossp` | `gen_random_uuid()` est natif depuis PostgreSQL 13 |
| `citext` | la normalisation de la casse se fait explicitement en couche `staging` |
| `ltree` | les hiérarchies d'entités (parent, ultime parent) se traitent avec des requêtes récursives |
| `postgis` | aucune donnée géographique à analyser |
| `timescaledb` | volumes modestes, absente de l'image retenue |
| `pg_cron` | l'orchestration se fait hors de la base, pour garder un seul endroit où voir les exécutions |

Règle : une extension n'est activée que si un usage concret est écrit ici. Toute nouvelle
extension passe par un nouvel ADR.

### D4. Trois rôles

| Rôle | Droits |
|---|---|
| `refdata_owner` | superutilisateur créé par l'image (`POSTGRES_USER`), utilisé **uniquement** pour l'amorçage |
| `refdata_app` | lecture, écriture et création dans les cinq schémas ; rien dans `public` |
| `refdata_ro` | lecture seule, transaction en lecture seule par défaut, `statement_timeout` de 30 s |

Alternatives :
- **Un seul rôle** : le plus simple, mais le code applicatif tournerait avec les droits
  d'administration. Une erreur ou une injection pourrait tout détruire.
- **Deux rôles (propriétaire + application)** : suffisant pour l'écriture, mais aucun
  accès sûr pour la consultation (notebooks, exploration, BI).
- **Un rôle par schéma ou par outil** : plus fin, mais lourd à gérer pour un projet
  mené par une seule personne ; à reconsidérer si l'équipe grandit.

### D5. Cinq schémas

`raw` (données telles que reçues), `staging` (nettoyées et typées), `core` (modèle de
référence), `marts` (tables prêtes à l'analyse), `ops` (suivi des chargements et de la
qualité).

Alternatives :
- **Un seul schéma avec des préfixes (`raw_`, `stg_`)** : aucune frontière de droits
  possible, risque de mélange.
- **Une base par couche** : pas de jointure entre bases en PostgreSQL, ce qui oblige à
  copier les données.

### D6. Amorçage rejouable plutôt que dossier d'initialisation

Un script SQL idempotent (`infra/sql/bootstrap.sql`), lancé par `just db-bootstrap`, crée
rôles, schémas, droits et extensions. Il se rejoue sans danger.

Alternatives :
- **`/docker-entrypoint-initdb.d`** : ne s'exécute qu'à la première création du volume.
  Toute modification oblige à détruire les données.
- **Outil de migration (Alembic, Flyway, sqitch)** : adapté aux tables, mais les rôles
  sont des objets du serveur, hors périmètre de ces outils. Les tables relèveront de dbt
  ou d'un outil de migration dans un ADR ultérieur.

### D7. Mots de passe hors dépôt

Les mots de passe vivent dans `.env` (ignoré par Git) ; `.env.example` ne contient que
des valeurs factices. `bootstrap.sql` reçoit les mots de passe par variables `psql`
(`-v app_pw=... -v ro_pw=...`), jamais écrits dans le fichier. Un hook `gitleaks` bloque
les commits contenant un secret.

Alternatives :
- **Mots de passe en clair dans `compose.yaml`** : exposés dans l'historique Git.
- **Secrets Podman ou SOPS** : plus robustes, mais inutiles pour une base locale non
  exposée (port lié à `127.0.0.1`). À reconsidérer si le projet est déployé.

## Conséquences

**Positives**
- Base reproductible : même image, même amorçage, même résultat sur toute machine.
- Droits minimaux : l'application ne peut pas toucher `public` ni administrer le serveur.
- Les contrôles (`just db-check`, tests d'intégration) vérifient rôles, schémas et
  extensions.

**Négatives et risques**
- Le tag d'image est épinglé : les mises à jour sont manuelles.
- Changer de version majeure de PostgreSQL impose une sauvegarde puis une restauration.
- `refdata_owner` reste superutilisateur : son mot de passe doit rester hors des outils
  courants.
- Les healthchecks de Podman rootless dépendent de la session systemd utilisateur ;
  `db-wait` s'appuie donc sur `pg_isready` via `podman exec`.

**Suites**
- ADR pour l'outil de transformation et la gestion des tables.
- Revoir D4 et D7 en cas de déploiement hors poste local.
