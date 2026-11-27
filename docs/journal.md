## 2026-11-26 : PostgreSQL prêt pour le projet

**Objectif** : disposer d'une base PostgreSQL locale (Podman rootless sur Fedora) avec extensions, rôles et schémas, amorçable et vérifiable en une commande.

**Fait**
- Conteneur PostgreSQL 18.7 avec pgvector 0.8.7, port `127.0.0.1:5433`.
- Six extensions, trois rôles, cinq schémas ; amorçage rejouable (`just db-bootstrap`).
- Réglages applicatifs validés (`src/refdata/config.py`) et tests unitaires et d'intégration.

## 2026-11-27 : Validateur d'ISIN

### Décision 1 : contrat de la fonction
**Questions**:
- Aurai-je besoin de compter les ISIN invalides par raison ?
- Une valeur invalide est-elle un cas normal de mon sujet, ou un cas exceptionnel qui justifie de lever une exception ?
- Ai-je besoin à la fois d'un résultat détaillé et d'un simple oui/non pour les appelants qui ne veulent pas le détail ?

**Options** :
- A. Un booléen.
- B. Une exception levée quand la valeur est invalide.
- C. Un résultat détaillé (valide ou non, avec les raisons).

**Critère**
Le but du projet est de mesurer la qualité des données de référence financières publiques. L'option retenue doit permettre de :

- fournir un décompte par type d'anomalie ;
- comparer les mesures entre sources et dans le temps, ce qui impose des catégories de défauts identiques, stables et fermées d'une exécution à l'autre ;
- traiter un grand nombre de lignes sans interruption : une valeur invalide est un cas courant, pas une situation exceptionnelle.

**Évaluation des options**

| Exigence | A. Booléen | B. Exception | C. Résultat détaillé |
|---|---|---|---|
| Décompte par type d'anomalie | non | oui, mais il faut définir une exception par type d'anomalie et compter en capturant chacune | oui |
| Catégories stables et comparables | non | oui, mais l'ensemble des classes d'exception doit rester fermé et leurs noms stables | oui, si l'ensemble des raisons est fermé et leurs valeurs stables |
| Traitement de masse sans interruption | oui | oui, mais chaque appel doit être entouré d'un bloc de capture ; un oubli interrompt tout le traitement | oui |

**Décision** : option C (résultat détaillé), accompagnée d'un booléen dérivé de ce résultat pour les appelants qui n'ont pas besoin du détail.

**Raisons** :

- Besoin de compter les ISIN invalides par raison : assurer une mesure qualitative des données nécessite de détailler les cas d'anomalie, l'option C est la seule à permettre ce décompte sans restriction.
- Valeur invalide, cas normal ou exceptionnel : une valeur invalide est un cas normal, pas une exception : il faut donc traiter une information invalide comme une valeur retournée.
- Résultat détaillé et simple oui/non : les appelants qui veulent seulement filtrer les lignes valides ou conditionner un traitement n'ont pas besoin du détail des raisons, et un booléen leur évite de manipuler le résultat complet. Il est dérivé du résultat détaillé (valide si et seulement si aucune raison d'échec), et non réimplémenté à part : une seule logique de validation existe, donc les deux niveaux ne peuvent pas se contredire.

**Conséquences pour les tests** :

- Chaque test d'un ISIN invalide vérifie l'ensemble exact des raisons attendues, et pas seulement le fait que l'ISIN est invalide.
- Un test vérifie que le booléen est toujours cohérent avec le résultat détaillé : il vaut vrai si et seulement si aucune raison d'échec n'est présente.
- Les tests comparent les raisons aux membres de l'énumération, jamais à des chaînes écrites en dur ; un test fige les valeurs de l'énumération, pour qu'un renommage involontaire soit détecté avant qu'il casse les comparaisons dans le temps.
- Un test vérifie que le résultat est immuable.
- Le résultat expose aussi des avertissements, distincts des raisons d'échec (voir décision 2).

### Décision 2 : écarts de forme récupérables (casse, espaces)

**Question** : un ISIN dont la forme s'écarte de la norme sans ambiguïté (minuscules, espaces autour) doit-il être accepté, accepté après correction, ou refusé ?

**Options** :

- A. Refuser
- B. Accepter après correction
- C. Accepter après correction et signaler

**Critère** : l'option retenue doit permettre de :

- détecter toutes les anomalies de forme ;
- conserver la valeur telle qu'elle a été reçue ;
- disposer d'une forme commune, pour comparer des valeurs entre sources.

**Évaluation des options**

| Exigence | A. Refuser | B. Accepter après correction | C. Accepter après correction et signaler |
|---|---|---|---|
| Détecter toutes les anomalies de forme | oui | non | oui |
| Conserver la valeur telle qu'elle a été reçue | oui | non, si la correction remplace la valeur d'origine | oui |
| Disposer d'une forme commune pour comparer entre sources | non | oui | oui |

**Décision** : accepter après correction et signaler (option C) ; les écarts de forme récupérables sont des avertissements, pas des raisons d'échec.

**Impact sur la décision 1** : le résultat porte, en plus des raisons d'échec, un ensemble d'avertissements (un défaut de casse ou d'espaces, par exemple).
`valid` ne dépend que des raisons d'échec : un ISIN en minuscules ou avec des espaces mais correct par ailleurs est donc valide, avec un avertissement.
Le résultat conserve à la fois la valeur reçue et la valeur normalisée.
Les avertissements forment, comme les raisons d'échec, un ensemble fermé de valeurs stables.
Les avertissements sont distincts par nature d'écart (casse, espaces), pour pouvoir les compter séparément.

**Règle** : un écart est récupérable si, après correction, la valeur est identifiable sans ambiguïté ; sinon c'est une raison d'échec.

**Raisons** :

- Saisie ou mesure : l'outil sert à la mesure, pas à la saisie.
- Effet d'une correction sur la mesure : une correction silencieuse fausserait la mesure, car elle effacerait l'écart de forme.
- Place de la correction : la correction est faite pendant la validation, afin de conserver une trace de l'écart de forme. La validation émet un avertissement pour des écarts de forme, et non un échec. Cela se justifie par : (1) l'écart de forme n'empêche pas l'identification de l'ISIN sans ambiguïté, (2) déclarer la valeur invalide ferait perdre une valeur exploitable et (3) l'avertissement permet de répondre aux exigences de détection et de conservation.

**Conséquences pour les tests** :

- Un ISIN valide écrit en minuscules ou avec des espaces (aux bords et à l'intérieur) est valide, sans raison d'échec, avec un avertissement d'écart de forme, et sa valeur normalisée est l'ISIN en majuscules et sans espaces.
- Un ISIN en casse mixte est traité comme un ISIN en minuscules : valide, avec le même avertissement de casse.
- Un ISIN avec une tabulation, un saut de ligne ou un espace insécable en bord est traité comme un ISIN avec des espaces : valide, avec l'avertissement d'espaces.
- Un ISIN avec à la fois de la casse et des espaces à corriger est valide, avec deux avertissements distincts.
- Un ISIN en minuscules et invalide pour une autre raison (par exemple une clé de contrôle fausse) est invalide : la raison d'échec **et** l'avertissement d'écart de forme apparaissent tous les deux dans le résultat.
- Une chaîne vide, ou composée uniquement d'espaces, est invalide : après correction, la valeur n'est plus identifiable, donc c'est une raison d'échec (la longueur incorrecte).
- La valeur reçue est toujours conservée telle quelle dans le résultat, quelle que soit la correction appliquée ; un test vérifie qu'elle n'est jamais modifiée.

### Décision 3 : préfixe de l'ISIN

**Question** : le préfixe de deux lettres d'un ISIN doit-il être seulement contrôlé dans sa
forme, ou vérifié contre une liste de préfixes connus ?

**Options** :

- A. Contrôler la forme seulement : deux lettres majuscules, sans liste.
- B. Vérifier l'appartenance à une liste fermée de préfixes (codes pays ISO 3166 et préfixes
  spéciaux).
- C. Séparer deux contrôles : la forme du préfixe maintenant, l'appartenance à un référentiel
  plus tard, dans une étape distincte.

**Critère** : l'option retenue doit permettre de :

- ne jamais rejeter à tort un ISIN réel ;
- ne pas dépendre d'une liste sans source officielle exploitable ni mise à jour assurée ;
- pouvoir mesurer les préfixes inconnus comme une anomalie.

**Évaluation des options**

| Exigence | A. Forme seulement | B. Liste fermée | C. Forme maintenant, référentiel plus tard |
|---|---|---|---|
| Ne jamais rejeter à tort un ISIN réel | oui | oui, si la liste est complète et à jour | oui |
| Ne pas dépendre d'une liste sans source exploitable | oui | non | oui, pour le contrôle de forme ; le référentiel est reporté |
| Mesurer les préfixes inconnus comme une anomalie | non | oui | oui, une fois le contrôle référentiel ajouté |

**Décision** : option C. Le validateur contrôle la forme du préfixe (deux lettres majuscules
après correction) et ne vérifie aucune liste. Le contrôle d'appartenance à un référentiel sera
ajouté dans une étape distincte, quand une source de vérité aura été choisie.

**Impact sur la décision 1** : le résultat gagne une raison d'échec propre au préfixe de forme
incorrecte. Cette raison s'ajoute à l'ensemble fermé des raisons d'échec.

**Règle** : un préfixe de forme correcte mais absent d'un référentiel n'est pas, à ce stade,
une raison d'échec. Quand le contrôle référentiel existera, un préfixe inconnu sera traité
selon la règle de la décision 2 : l'ISIN reste identifiable, donc ce sera un avertissement,
pas un échec.

**Raisons** :

- Source de vérité : les directives de l'ANNA ne publient pas de liste des préfixes valides ;
  elles renvoient à la base de ses membres. Une liste maintenue par mes soins serait sans
  source officielle exploitable.
- Pas seulement des pays : le préfixe n'est pas toujours un code pays ISO 3166 (`XS`, `EU`,
  `XT`, `XA` à `XD`, ou `US` pour des titres de la règle 144A). Une liste de pays ISO
  rejetterait à tort des ISIN réels.
- Un ensemble qui évolue : l'ANNA détermine elle-même les préfixes supplémentaires. Une liste
  fermée écrite aujourd'hui serait périmée demain.
- Mesure : l'observatoire pourra mesurer les préfixes inconnus plus tard, sans que le
  validateur de forme n'ait à changer.

**Conséquences pour les tests** :

- Un ISIN dont le préfixe est un code pays courant (par exemple `FR`, `US`, `DE`) est valide.
- Un ISIN dont le préfixe est spécial (par exemple `XS` ou `EU`) est valide : le validateur
  n'applique pas de liste de pays.
- Un ISIN dont le préfixe est de forme correcte mais inventé (par exemple `ZZ`) est valide
  tant que la clé de contrôle est correcte ; un test documente cette limite connue, qui
  changera quand le contrôle référentiel sera ajouté.
- Un préfixe contenant un chiffre, un caractère non alphabétique, ou de longueur différente de
  deux lettres est invalide, avec la raison de préfixe de forme incorrecte.
- Un préfixe en minuscules est valide avec l'avertissement de casse (décision 2).

**Sources** : [ANNA, ISIN Uniform Guidelines, version 26 (juin 2026)](https://anna-web.org/wp-content/uploads/2026/06/ISIN-Guidelines-Version-26-Jun-2026.pdf) · [ANNA, mise en œuvre de l'ISO 6166 révisée](https://anna-web.org/implementation-of-revised-iso-6166/), consultées le 2026-11-27.
