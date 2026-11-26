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
