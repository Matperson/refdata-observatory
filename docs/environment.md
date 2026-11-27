# Environnement technique

Ce document décrit l'environnement de référence pour développer et exécuter refdata-observatory en local, et comment le vérifier.
Les versions de la colonne « testée » sont celles du poste de référence du projet.

Dernière mise à jour : 2026-11-18

## 1. Poste de référence

| Élément | Valeur |
|---|---|
| Système | Fedora Linux 44 (KDE Plasma Desktop Edition) |
| Conteneurs | Podman en mode rootless, sans démon |
| Fournisseur Compose | podman-compose, appelé par `podman compose` |
| Python | 3.14 (épinglé dans `.python-version`) |
| Gestionnaire Python | uv (dépendances verrouillées dans `uv.lock`) |
| Lanceur de tâches | just |

## 2. Logiciels requis

| Logiciel | Rôle | Version testée | Installation sous Fedora | Vérification |
|---|---|---|---|---|
| Git | Contrôle de version | 2.55.0 | `sudo dnf install git` | `git --version` |
| Podman | Conteneurs rootless | 5.8.4 | `sudo dnf install podman` | `podman --version` |
| podman-compose | Compose pour Podman | 1.6.0 | `sudo dnf install podman-compose` | `podman compose version` |
| uv | Python et dépendances | 0.13.8 | documentation officielle d'uv | `uv --version` |
| just | Commandes du projet | 1.59.0 | `sudo dnf install just` | `just --version` |
| Client SSH | Accès à GitHub | fourni par le système | | `ssh -T git@github.com` |

Python 3.14 est installé par uv selon `.python-version` : aucune installation système n'est nécessaire.

### Outils de développement (installés par uv)

Ces outils sont déclarés dans `pyproject.toml` (groupe de développement) et installés par `just install` : pytest, pytest-cov, ruff, pyright, pre-commit, sqlfluff.
Leurs versions exactes sont dans `uv.lock`.

### Comptes et accès

- Compte GitHub avec authentification à deux facteurs et clé SSH enregistrée.
- Aucun service payant ni compte cloud n'est requis à ce stade.

## 3. Base de données

| Composant | Version | Remarque |
|---|---|---|
| PostgreSQL | 18.7 | Image pgvector basée sur l'image officielle PostgreSQL |
| pgvector | 0.8.7 | Extension `vector` |
| Image | `docker.io/pgvector/pgvector:0.8.7-pg18` | Tag précis, jamais `latest` |
| Volume de données | monté sur `/var/lib/postgresql` | Chemin recommandé pour PostgreSQL 18 par la documentation officielle ; persistance vérifiée |

### Extensions activées

| Extension | Usage |
|---|---|
| vector | Embeddings, distances, index HNSW |
| pg_trgm | Similarité de textes, recherche floue |
| fuzzystrmatch | Distance de Levenshtein, soundex |
| unaccent | Retrait des accents avant comparaison |
| btree_gist | Contraintes d'exclusion sur périodes (historisation) |
| pg_stat_statements | Statistiques de requêtes (chargée via `shared_preload_libraries`) |

Les extensions sont créées par `infra/sql/bootstrap.sql` et vérifiées par `infra/sql/check_extensions.sql`.

### Rôles et schémas

- Rôles : `refdata_owner` (amorçage et administration), `refdata_app` (application), `refdata_ro` (lecture seule).
- Schémas : `raw`, `staging`, `core`, `marts`, `ops`.

## 4. Configuration locale

- Port publié sur la machine : `127.0.0.1:5433` (non exposé au réseau).
- Variables d'environnement : voir `.env.example` (7 variables). Le fichier `.env` n'est jamais versionné.
- Les mots de passe sont générés localement (`openssl rand -hex 24`).

## 5. Démarrage et vérification rapide

    # 1. fichier d'environnement : remplacer chaque CHANGE_ME (openssl rand -hex 24)
    cp .env.example .env
    # 2. dépendances Python
    just install
    # 3. hooks Git, une fois par clone
    uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
    # 4. démarre PostgreSQL et applique l'amorçage
    just db-up
    # 5. vérifications
    just db-check    # les 6 extensions fonctionnent
    just check       # lint, typage, tests unitaires
    just test-int    # tests d'intégration (base démarrée)

## 6. Politique de versions

- Les versions de l'image et de Python sont épinglées. Tout changement passe par une branche dédiée et un ADR.
- L'intégration continue (GitHub Actions) utilise Docker avec la même image que le poste local.
