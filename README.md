# refdata-observatory

[![CI](https://github.com/Matperson/refdata-observatory/actions/workflows/ci.yml/badge.svg)](https://github.com/Matperson/refdata-observatory/actions/workflows/ci.yml)

Observatoire de la qualité des données de référence financières publiques : collecte, rapprochement et contrôle de lacohérence entre sources ouvertes.

## Objectif

Mesurer et rendre visible la qualité des référentiels financiers publics (identifiants, émetteurs, instruments) :
complétude, cohérence entre sources, évolution dans le temps.

## Sources

| Source | Contenu |
|---|---|
| ESMA FIRDS | référentiel des instruments financiers |
| GLEIF | identifiants d'entités juridiques (LEI) |
| OpenFIGI | identifiants d'instruments (FIGI) |
| BCE | données de référence publiées par la Banue centrale européenne |

Toutes les données utilisées sont publiques.

## État du projet

Socle technique en place : outillage Python, intégration continue, base PostgreSQL et
tests d'intégration. L'ingestion des sources est la prochaine étape.

## Structure du dépôt

| Dossier | Rôle |
|---|---|
| `src/refdata/` | code Python (réglages, accès à la base) |
| `tests/` | tests unitaires et d'intégration |
| `infra/` | conteneur PostgreSQL, scripts SQL d'amorçage |
| `transform/` | transformations SQL |
| `orchestration/` | exécution planifiée des chargements |
| `analytics/` | analyses et restitutions |
| `docs/` | environnement, décisions d'architecture (`docs/adr/`), journal |

## Base de données

PostgreSQL 18 avec pgvector, en conteneur Podman (rootless).

**Prérequis** : Podman et `podman-compose`, [just](https://just.systems), [uv](https://docs.astral.sh/uv/).
Détails et versions testées : [docs/environment.md](docs/environment.md).

**Démarrage**
```bash
cp .env.example .env     # puis remplir les mots de passe
just install
just db-up
```

Pour générer un mot de passe sans caractère problématique : `openssl rand -hex 24`.

**Ce que vous obtenez**
- PostgreSQL 18.7 sur `127.0.0.1:5433`, données dans un volume Podman.
- Six extensions, trois rôles (`refdata_owner`, `refdata_app`, `refdata_ro`) et cinq schémas
  (`raw`, `staging`, `core`, `marts`, `ops`).

**Commandes utiles**
| Commande | Effet |
|---|---|
| `just db-check` | vérifie extensions, rôles et schémas |
| `just db-shell` | ouvre `psql` |
| `just db-logs` | affiche les journaux |
| `just db-down` | arrête la base (données conservées) |
| `just db-reset` | recrée la base à zéro |

Choix de conception : [ADR 0001](docs/adr/0001-postgresql-extensions-roles-schemas.md).

## Développement

| Commande | Effet |
|---|---|
| `just install` | installe les dépendances (verrou `uv.lock`, Python 3.14) |
| `just check` | contrôles de qualité complets |
| `just lint` / `just lint-sql` / `just typecheck` | lint Python, lint SQL, typage |
| `just test` | tests unitaires |
| `just test-int` | tests d'intégration (base démarrée) |

## Contribuer

1. Créer une branche : `git switch -c task/<sujet>`.
2. Commits au format [Conventional Commits](https://www.conventionalcommits.org) ; les hooks
   pre-commit (`uv run pre-commit install`) vérifient le format et la qualité.
3. Ouvrir une pull request vers `main`. Son titre suit Conventional Commits : il devient le
   message du commit après fusion par squash.
4. Fusionner quand les vérifications `quality` et `integration` sont vertes.

## Licence

Voir le fichier [LICENSE](LICENSE).
