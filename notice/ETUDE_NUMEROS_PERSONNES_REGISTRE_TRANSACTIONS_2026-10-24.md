# Les numéros des personnes dans le registre des transactions — étude du 24/10/2026

*Demande de Frédéric (24/10) : « fais une étude et analyse avec un audit complet de mon projet, notes, code actuel et historique,
approfondi, pour me proposer le meilleur mécanisme pour les notaires et les acquéreurs (les acquéreurs peuvent être multiples) afin de
résoudre mes problèmes d'id dans le registre des transactions ».*
**Lecture seule. Rien n'est codé.** Chantier ⑧. Notes liées : `ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md` §47-50.

---

## 1. La règle à servir

- **« L'id Hektor pour communiquer avec Hektor, et mon id app pour le registre, comme les autres fiches de mon app gèrent les deux id »**
  (Frédéric, 24/10).
- « Les ids Hektor étant les axes, il y aura un problème lors de la coupure » (Frédéric, 01/09, commit `db771db`).
- « Un numéro ne se perd jamais » (règle du projet, CLAUDE.md §4).
- **Reconnaître par la plage** (08/10) : contact < 10 000 000 = Hektor ; ≥ 10 000 000 = nous (10-20 M : contacts venus de Hektor ;
  ≥ 20 M : nés dans l'app).
- **Décision du 23/09 (question 2, `AUDIT_COMPLET_AVANT_BASCULE_2026-09-23.md` §4)** : `hektor_acquereur_id` **reste le numéro de Hektor —
  « la trace brute de ce que Hektor a dit »** ; le doublage se fait en **ajoutant** notre numéro à côté (`app_contact_id`), pas en
  traduisant sur place.

## 2. L'histoire, datée *(relevé d'un agent de lecture, sources vérifiées par sondage)*

| date | quoi | source |
|---|---|---|
| 31/07 | registre d'affaires : `acquereur_json` ne garde que le **premier** acquéreur | `5d99510` |
| 19-21/08 | le serveur numérote les contacts, plage de l'app à partir de 10 M | `AUDIT_IDENTITE_CONTACTS_2026-08-20` |
| 01/09 | **`app_contact_id` ajouté à côté de `hektor_acquereur_id`** (remarque de Frédéric sur la coupure) ; COALESCE, jamais d'effacement | `db771db` |
| 02-06/09 | plusieurs acquéreurs désignés à l'écran (`buyer_contact_ids`, 2.5 / 2.6) ; au clic, la liste porte les numéros de `app_contact_current` | `f44971e`, `6c162ce`, `patch_acquereurs_multiples_2026-09-06.sql` |
| 04-05/09 | 1.8 : `acquereurs_json`, la liste complète (33 465 acquéreurs, 2 377 transactions multiples) ; la chaîne suit la SÉQUENCE (1.7) | `b3bfacd`, `31afa9f` |
| 15-16/09 | les notaires partent chez Hektor des deux côtés ; colonnes `notaire_acquereur_*` / `notaire_mandant_*` remplies la nuit ; `notaire_id` devient inerte | `0853c6c` |
| 16/09 | Hektor garde bien 2 acquéreurs ; `acquereurs_affirmes` : on ne pose la liste que si l'écran l'a touchée | `33a6d60` |
| 17-18/09 | 1.4 : l'acquéreur perdu (`app_affaire_personne_ecart`, `personnes_posees`) | `ba197f7`, `8d70f1e` |
| 21-23/09 | **la bascule** : `hektor_contact_id` porte NOTRE identité, `hektor_target_id` celui de Hektor ; C-1 (le worker vise la cible), **C-9 (notaires et mandants traduits avant l'envoi)**, G-10 (la nuit traduit par les deux numéros) ; question 2 : `hektor_acquereur_id` reste Hektor | `d26ad2e`, `fced315`, `f3122de` |
| 10/10 | `acquereurs_json` mélangeait les deux séries ; la vraie table de traduction est `app_contact` (serveur), pas `app_contact_identite_app` | `AUDIT_5_QUESTIONS_REGISTRE_RELATIONS_2026-10-10.md` |
| 21/10 | « le co-acquéreur est au registre jusqu'à la nuit seulement ; le notaire du vendeur et les mandants choisis ne sont nulle part ailleurs que dans la charge » | `CHANTIER_8_GARDE_CHEZ_NOUS` |
| 22/10 | 1b : la création rangeait notre identité dans `hektor_acquereur_id` → doublon de nuit ; corrigé (le numéro de Hektor y va, le nôtre dans `app_contact_id`) | `03baa2f` |
| 23/10 | défaut 6 (contact né dans l'app, second numéro fabriqué) corrigé ; F2 (acquéreur « inconnu » à la vente) corrigé ; C4 `aliasNumerosAcquereur` | `b9e58b8`, `7fce928`, `1c5d70d` |
| 24/10 | notaires : 100 % au numéro de Hektor après la nuit ; le worker traduit bien avant l'envoi (essai 5) | note §47-50 |

## 3. Mesures du 24/10 *(Supabase et serveur, lecture seule)*

**Le dictionnaire existe et il est complet.** Supabase `app_contact_current` : 62 319 fiches, toutes avec nos deux numéros. Serveur
`phase2.sqlite` `app_contact` (doublure d'identité, jamais reconstruite) : **356 649** lignes avec `hektor_target_id` ; il porte même les
220 notaires absents de Supabase.

**Ce que le registre des transactions porte, après la nuit :**
| personne | où | numéro |
|---|---|---|
| acquéreur principal | `hektor_acquereur_id` | Hektor (30 422 lignes) |
| acquéreur principal | `app_contact_id` | **nous** (30 413 ; 9 manquent) |
| acquéreur principal | `acquereur_json.id` | Hektor (0 à nous) |
| **co-acquéreurs** | `acquereurs_json[].id` | **Hektor seul — 4 581 personnes sans notre numéro** (2 965 sur des compromis, 1 616 sur des ventes) |
| notaire de l'acquéreur / du vendeur | `notaire_acquereur_id` / `notaire_mandant_id` | **Hektor, 100 %** (23 340 références, ~1 327 notaires) |
| mandants | `mandants_json[].id` | Hektor |
Transactions à plusieurs acquéreurs : **1 809 compromis** (jusqu'à 8), **637 ventes** (jusqu'à 8), dont 18 nées dans l'app ; l'offre n'en a
qu'un. **Au clic**, la création écrit nos numéros (liste, notaires) et traduit `hektor_acquereur_id` ; **la nuit** réécrit listes et
notaires avec ceux de Hektor — seul `app_contact_id` (le principal) est traduit vers le nôtre.

## 4. Qui écrit, qui lit

| | écrit | lit |
|---|---|---|
| création / modification (Supabase) | nos numéros au clic ; `hektor_acquereur_id` traduit | `app_chaine_pour` |
| `affaire_ledger.py` (nuit) | `acquereur_json`, `acquereurs_json`, `hektor_acquereur_id` (Hektor, depuis le miroir) ; `app_contact_id` traduit (G-10) | le miroir |
| `registre_depuis_console.py` (nuit) | notaires (Hektor : API pour la vente, console pour le compromis) | `app_affaire_console` |
| worker | `hektor_affaire_id`, verdicts R3 | la charge ; **traduit nous → Hektor avant tout envoi** (C-9) ; R3 `@notaire` traduit, mais seulement après la nuit |
| écran | — | noms des parties ; `aliasNumerosAcquereur` (ne relie que la paire du **principal**) ; `loadNomsContacts` (notaires, par les deux numéros) |
| `export_app_payload.py`, `build_contacts_layer.py` | résumé du cockpit, rôles des contacts | le **miroir** Hektor, puis substitution d'identité |

## 5. Les défauts que cela produit aujourd'hui

1. **Les co-acquéreurs n'ont pas notre numéro au registre** (4 581) : ils ne survivraient pas à la coupure ; l'écran ne les relie pas à
   leur fiche par notre numéro (`aliasNumerosAcquereur` ne connaît que le principal).
2. **Les notaires perdent notre numéro chaque nuit** ; la ligne `notaire_id` du carnet reste « en attente » (R3 ne traduit qu'après la nuit
   et ne tourne qu'à la fin d'un travail).
3. ⚠ **Le chaînage d'une nouvelle offre compare deux séries** : `app_chaine_pour` cherche le même acquéreur par `hektor_acquereur_id`
   (Hektor) alors que la création lui passe `buyer_contact_id` de l'écran (nous). Une offre du même acquéreur ne retrouve donc pas son
   dossier ouvert par l'acquéreur. **Effet non mesuré** : la nuit recalcule les chaînes par la séquence.
4. Tout lecteur qui compare une personne doit savoir dans quelle série il est : c'est l'origine de C4 (« X et X »), de F2 (acquéreur
   inconnu), du doublon 1b et du défaut 6 — **cinq défauts de la même famille en un mois**.

## 6. Les mécanismes possibles

| | A — traduire sur place (notre numéro seul) | B — les deux numéros dans chaque personne | C — une table des personnes de l'affaire |
|---|---|---|---|
| principe | la nuit remplace le numéro de Hektor par le nôtre dans les listes et les colonnes notaires | chaque personne porte `id` (nous) **et** `hektor_id` : dans les objets JSON des listes ; pour les notaires, une colonne de plus par rôle | `app_affaire_personne` (affaire, rôle, rang, **notre numéro, celui de Hektor**, nom au moment, origine, saisi le / confirmé le) — comme `app_affaire_repartition` ; le registre garde intacte la trace de Hektor |
| la trace brute de Hektor (décision du 23/09) | ⛔ **perdue** dans les listes et les notaires | ✅ gardée | ✅ gardée (le registre n'est pas touché) |
| co-acquéreurs multiples | oui | oui, dans le JSON | ✅ une ligne par personne, sans JSON |
| comparer avec Hektor (R3, 1.4, adoption, chaînage) | il faut retraduire à chaque fois | direct, par `hektor_id` | direct, par la colonne Hektor |
| survit à la coupure | oui | oui (on ignore `hektor_id`) | oui (on ignore la colonne Hektor) |
| la saisie survit à la nuit | non : la nuit la réécrit | non : la nuit la réécrit | ✅ **oui** : la nuit **confirme**, elle ne remplace pas (« chez nous d'abord, Hektor confirme ») |
| « quelles affaires pour ce contact ? » | lire tous les JSON | lire tous les JSON | ✅ une requête par numéro |
| colonnes / listes de plus | aucune | 2 colonnes (notaires) | une table |
| ampleur | petite (2 scripts de nuit + rattrapage) | moyenne (nuit, création, lecteurs) | **la plus grande** : table, création, nuit, rattrapage, lecteurs migrés un par un |

**Volumes à rattraper (mesure du 24/10)** : acquéreurs principaux 30 422 + co-acquéreurs 4 581 + notaires 23 340 = **~58 300 personnes** ;
**+ 58 474 mandants** si on les y met (~116 800). ⚠ Les mandants sont **déduits par Hektor** (décision du 22/10) : les inclure est une
question à part.

## 7. Recommandation

**C, par étapes** — c'est la forme que le projet a déjà prise pour ce qui est « à nous » (répartition, conditions, notes : nos tables, que
la nuit ne réécrit pas), et c'est la seule qui règle **en même temps** les quatre défauts du §5 :
- elle garde **les deux numéros de chaque personne**, comme les fiches de l'app (la règle de Frédéric) ;
- elle respecte la décision du 23/09 : le registre reste la trace de Hektor, on **ajoute** à côté ;
- la saisie au clic **survit** à la nuit (le défaut du 21/10 « jusqu'à la nuit seulement ») ;
- les acquéreurs multiples sont des lignes, pas un JSON à re-traduire.

**Étapes proposées** (chacune réversible, derrière un interrupteur, avec essais et témoin inverse) :
1. la table, vide, et sa répétition ;
2. la création l'écrit au clic (nos numéros + ceux de Hektor par la fiche contact) ;
3. la nuit la **confirme** depuis le miroir (traduction par `app_contact` du serveur), sans jamais effacer une saisie ;
4. rattrapage des transactions existantes (accord) ;
5. les lecteurs passent un par un : la rubrique Affaires, la modale, R3, le chaînage (`app_chaine_pour` par notre numéro) ;
6. ensuite seulement, les colonnes et JSON de personnes du registre deviennent « la trace de Hektor », lue pour comparer.

**Si C est jugée trop grande maintenant** : **A pour les notaires seulement** (le plan du §50 de la note) règle le défaut 2 tout de suite,
et C viendra ensuite ; mais A perd la trace brute de Hektor pour les notaires — à trancher.

**Ce que ça pourrait casser ailleurs**, à mesurer à chaque étape : le chaînage (rejeu existant, fidèle à 100 %), l'adoption de nuit
(C.4 / 1b), le résumé du cockpit et les rôles des contacts (ils lisent le miroir, pas le registre — inchangés), le classeur (ne lit pas ces
champs, à confirmer), le problème des types de contacts (à ne pas mélanger : un acquéreur reste acquéreur).

⛔ **Décision de Frédéric attendue** : le mécanisme (A, B ou C), et l'ordre par rapport à R2 et au problème des types.
