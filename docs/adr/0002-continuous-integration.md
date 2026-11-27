# ADR 0002 : intégration continue et protection de la branche principale

- **Statut** : accepté
- **Date** : 2026-11-26
- **Décideur** : Matperson
- **Liens** : ADR 0001, `.github/workflows/ci.yml`, `docs/environment.md`

## Contexte

Le dépôt est public et mené par une seule personne.
Les contrôles actuels (hooks pre-commit, ruff, pyright strict, pytest, sqlfluff) ne tournent que sur ma machine.
Rien ne garantit qu'ils passent ailleurs, ni qu'ils sont respectés avant une fusion.
Les tests d'intégration exigent une base PostgreSQL avec pgvector et les trois rôles.
La CI utilise la version de Python déclarée dans .python-version (3.14).

## Décisions

### D1. GitHub Actions, avec les mêmes contrôles qu'en local
Hooks pre-commit sur tous les fichiers, ruff, pyright, sqlfluff, tests unitaires avec couverture.

Alternatives écartées :
- **Autre service de CI (GitLab CI, CircleCI)** : le code est sur GitHub, GitHub Actions
  évite un second compte et une intégration.
- **Aucun contrôle automatique** : la qualité repose sur la discipline individuelle.

### D2. Deux jobs séparés : qualité, puis intégration
Le premier est rapide et sans base de données ; le second démarre PostgreSQL.

Alternatives :
- **Un seul job** : lent, et un échec ne dit pas si la cause est le code ou la base.
- **Intégration seulement en local** : le test des droits des rôles ne serait jamais
  rejoué sur machine propre.

### D3. PostgreSQL comme conteneur de service, même image épinglée
`docker.io/pgvector/pgvector:0.8.7-pg18`, identique à `compose.yaml`.

Alternatives :
- **Installer PostgreSQL sur la machine de CI** : divergence avec l'environnement local.
- **Réutiliser `podman compose` en CI** : couche inutile et dépendance à Podman, alors que
  le service de conteneur natif de GitHub Actions suffit.

### D4. Aucun vrai secret en CI
Les mots de passe sont factices et définis dans le workflow. Les secrets GitHub ne sont
utilisés que pour de vraies clés d'API, plus tard.

Alternatives :
- **Mots de passe réels en secrets GitHub** : aucun intérêt, la base de CI est éphémère.

### D5. Moindre privilège et versions épinglées
Permissions du workflow limitées à la lecture du dépôt ; actions épinglées à une version
précise (idéalement un identifiant de commit) ; Dependabot pour les mises à jour.

Alternatives :
- **Versions flottantes (`@v4`, `@main`)** : une mise à jour malveillante ou cassante
  s'appliquerait sans relecture.

### D6. `main` protégée, tout passe par une pull request
Pull request obligatoire, vérifications de CI obligatoires et à jour, historique linéaire,
poussées forcées et suppression interdites, règle appliquée aussi à l'administrateur.
Mode de fusion : squash. Le titre de la pull request suit Conventional Commits, car il
devient le message du commit sur `main`.

Alternatives :
- **Pas de protection** : une poussée directe contourne toutes les vérifications.
- **Exemption de l'administrateur** : c'est précisément le cas de ce dépôt, où je suis le
  seul acteur.
- **Fusion par rebase** : conserve chaque commit, mais laisse sur `main` les commits
  intermédiaires de correction.

## Conséquences

**Positives**
- Chaque modification est vérifiée sur machine propre avant d'entrer dans `main`.
- Les droits des rôles sont retestés à chaque pull request.

**Négatives et risques**
- Une pull request à chaque changement, même minime : un peu de friction.
- Les versions épinglées demandent une relecture des mises à jour proposées.
- Les healthchecks en CI diffèrent de Podman rootless : la CI ne remplace pas le test local.

**Suites**
- Ajouter des contrôles (audit des dépendances, analyse statique de sécurité).
- Décider du premier déploiement hors poste local.
