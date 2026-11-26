## 2026-11-26 : PostgreSQL prêt pour le projet

**Objectif** : disposer d'une base PostgreSQL locale (Podman rootless sur Fedora) avec extensions, rôles et schémas, amorçable et vérifiable en une commande.

**Fait**
- Conteneur PostgreSQL 18.7 avec pgvector 0.8.7, port `127.0.0.1:5433`.
- Six extensions, trois rôles, cinq schémas ; amorçage rejouable (`just db-bootstrap`).
- Réglages applicatifs validés (`src/refdata/config.py`) et tests unitaires et d'intégration.
