# Auto-archivage RGPD des recherches — plan du 29/10/2026 (RIEN CODÉ)

> ⛔ **REPORTÉ PAR FRÉDÉRIC LE 29/10** : « laisse tomber, on verra plus tard comme prévu pour mettre en place un
> auto-archivage autonome ». Ce plan reste la base de ce futur chantier ; ne pas le relancer de soi-même.

> Ouvert par Frédéric le 29/10. Suite de `AUDIT_NAVIGATION_APRES_ACTION_2026-10-23.md` §19.6 (le geste « cadenas »).
> *Audit limité à l'objet **recherche** ; la date d'auto-archivage des **contacts** est citée, pas traitée.*

## 1. Les décisions de Frédéric (29/10, mot pour mot)

> « Sur les recherches actives mettre la date de création de la recherche + 2 ans avec la possibilité de la décaler ou
> modifier dans la fiche contact + pour les recherches actives actuelles récupérer leur date d'auto-archivage à leur
> prochaine lecture chez Hektor, normalement une fois par jour. »
> « D'abord chez nous il faut gérer cela, puis dans les workers chez Hektor. »

Antécédent : le 16/10 (`CHANTIER_7`, décision C), « capter la date d'auto-archivage » avait été renvoyé à **« un
auto-archivage conforme RGPD, c'est un autre dev »** — c'est ce chantier. Rien n'avait été conçu.

## 2. Ce que l'audit a mesuré (29/10)

| fait | mesure |
|---|---|
| Hektor pose une date d'auto-archivage à chaque recherche | **création + 2 ans** (mesuré le 16/10 : 22-06-2026 → 22-06-2028 ; 05-06-2026 → 05-06-2028) |
| **la lecture quotidienne NE la ramène PAS** | la tâche **« GTI Recherches Actives », 02:00** (relevé dans le planificateur le 29/10 ; `scheduled/run_recherches_actives.ps1` → `phase2/sync/sync_active_searches.py` → `sync_contact_details.py`) relit chaque nuit les ~4 000 contacts à recherche active, mais par l'**API** `/Api/Contact/ContactById` — **pas par la console** : une recherche y porte `offre, archive, types, villes, quartiers, particularites, criteres` — **ni numéro, ni date de création, ni date d'auto-archivage** (relu sur 605946 le 29/10) |
| où vit la date | **seulement dans la page Hektor** (`recherche-changeTab`) : « Créée le » et `recentValueAutoarchivage<id>`, une recherche par lecture (`searchNum`) |
| la date du **contact**, elle | arrive par l'API (`contact.dateAutoArchiv`, 355 985 contacts dans le miroir) — hors de ce plan |
| volume | **4 231 recherches actives**, 4 011 contacts → **~4 200 lectures de page** pour un passage complet |
| date de création connue chez nous | registre `app_search_registry.first_seen_at` : **320** recherches actives vues après le 21/08 (≈ création, à un jour près) ; **3 911** vues dès la naissance du registre (21/08) → date réelle inconnue sans la page |
| ce qui archive vraiment | le **cadenas** (bascule), pas la date — §19.6 F ; codé le 29/10, non mis en service |

⚠ **La phrase « à leur prochaine lecture chez Hektor, une fois par jour » ne peut pas se tenir telle quelle** : la lecture
quotidienne est l'API, aveugle à cette date. Il faut une **lecture de page dédiée**, par le worker (session console, ses
4 freins), comme le balayage des photos masquées.

## 3. Le plan proposé — chez nous d'abord, Hektor ensuite

| pièce | quoi | où | risque |
|---|---|---|---|
| **R1 — la table** | `app_search_auto_archivage` : `app_search_id` (clé, le numéro du registre, qui ne bouge pas), `date_auto_archivage`, `origine` (`hektor` lue · `calcul` création + 2 ans · `utilisateur`), `modifie_par`, `modifie_le`. **Table à part** : `app_contact_search_current` est réécrite par la relecture du contact, une colonne y serait écrasée | Supabase (patch, inverse, répétition) | nul (additif) |
| **R2 — récupérer les dates actuelles** | **greffé sur la tâche de 02:00** (Frédéric : « à leur prochaine lecture chez Hektor ») : après sa lecture API, elle dépose un **lot de lectures de page** que le worker exécute (la session console est la sienne, avec ses freins — le script Python n'en a pas) : pour chaque recherche active sans date, lire sa page (`searchNum`) → date d'auto-archivage **et** « Créée le » → R1 (`origine = hektor`). Plafond par nuit, comme le balayage photos | worker + script de lot + tâche | **quota Hektor** : ~4 200 lectures ; la nuit en consomme déjà ~4 500 pour un mur à 13-17 000 → **1 000 par nuit ≈ 5 nuits** |
| **R3 — les nouvelles recherches** | créée **dans l'app** : date = **création + 2 ans** posée chez nous au clic (`origine = calcul`) — Hektor pose la même. Créée **dans Hektor** : le lot R2 la trouve (pas de date chez nous) et la lit **une fois** | RPC de création + lot R2 | faible |
| **R4 — l'afficher et la modifier** | sur chaque recherche de la fiche contact : « Auto-archivage le JJ/MM/AAAA », un sélecteur de date pour **décaler ou modifier** → chez nous **tout de suite**, puis un travail qui la pose chez Hektor (`modifDateArchiveCritere` **seul, JAMAIS de bascule**) et **relit le cadenas** (il doit rester absent) | écran + RPC + **nouveau type de travail** (3 verrous : contrainte, droits, distribution) | ⚠ **non mesuré** : poser une date **future** sur une recherche active peut-elle la faire basculer ? La page bascule si `desarchiveCritere` — le 16/10, une date future sur une archivée n'a rien réactivé. **Un essai réel est nécessaire** avant d'ouvrir le geste |
| **R5 — archiver à la date** | chaque nuit : les recherches actives dont la date est **passée** → **le même geste que la corbeille** (chez nous d'abord, puis le worker : date + cadenas) | tâche de nuit + RPC existante | ⚠ **volume de la 1ʳᵉ nuit** : à compter **à blanc** avant d'allumer ; plafond par nuit ; interrupteur |

**Pourquoi pousser la date chez Hektor (R4)** : sinon Hektor garde sa propre date (création + 2 ans) et **archive de
lui-même**, plus tôt que la date décalée dans l'app — les deux dates divergeraient.

**Préalable à tout** : le geste « cadenas » du 29/10 (§19.6 F) doit être **en service et éprouvé en réel** — R5 s'en sert.

## 4. Ce que ça pourrait casser ailleurs

- **Le quota de Hektor** (R2) : la seule dépense réelle ; elle passe par le worker et ses freins, en lot plafonné.
- **Les rapprochements** : une recherche archivée n'en produit plus (patch du 21/08) — c'est l'effet voulu de R5.
- **La relecture du contact** : elle ne touche pas une table à part (R1). À vérifier que rien ne la purge.
- **La décision C.3** (une modification de recherche ne part plus chez Hektor, 24/08) : R4 est une **exception** voulue,
  limitée à la date. À confirmer par Frédéric.
- **Les recherches archivées** : hors périmètre (« sur les recherches actives »). Une recherche réactivée dans Hektor
  serait vue par R2 au passage suivant.

## 5. À trancher par Frédéric

1. **R2 : 1 000 lectures par nuit** (≈ 5 nuits), dans le creux 23:18-03:00 ?
2. **R4 : pousser la date modifiée chez Hektor** (exception à C.3) — et **qui** peut la modifier : le négociateur sur ses
   contacts, l'admin partout ?
3. **R4 : une limite** au décalage (RGPD : durée de conservation raisonnable) ou libre ?
4. **R5 : allumer l'archivage de nuit** après un compte à blanc, avec quel plafond ?
5. **Ordre** : R1 → R2 → R3 → R4 → R5, chacun derrière son interrupteur ?
6. La date des **contacts** (`dateAutoArchiv`, déjà reçue) : l'afficher aussi, ou sujet à part ?
