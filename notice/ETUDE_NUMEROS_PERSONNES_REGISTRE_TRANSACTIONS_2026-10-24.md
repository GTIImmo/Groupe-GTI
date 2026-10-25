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
3. ~~Le chaînage d'une nouvelle offre compare deux séries~~ — **FAUX, corrigé au §9** : depuis 1b (22/10), la création passe à
   `app_chaine_pour` le numéro de **Hektor** (`v_acquereur_cible`), reconnu par nos deux numéros.
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

---

## 8. ⛔ RÉVISION — « on a un registre des contacts et un registre des relations : pourquoi créer encore une liste ? » *(Frédéric, 24/10)*

**Frédéric a raison, et le projet l'avait DÉJÀ décidé le 30/09.** Ma recommandation C (une table des personnes de l'affaire) est
**retirée** : elle fabriquait une troisième copie.

**Ce que le projet a écrit le 30/09** (`relation_ledger.py` l. 28-38 ; `patch_app_relation_2026-09-30.sql` l. 34 ;
`patch_relations_lisent_le_registre_2026-09-30.sql` l. 43-53 ; `patch_liens_deux_absences_2026-09-30.sql` l. 129-136) :
- le **registre des relations** (`app_relation`) porte les liens **personne ↔ bien** (mandant / propriétaire : un seul fait, « propriétaire
  du bien »), avec **quatre numéros** (la personne et le bien, chez nous et chez Hektor) ;
- **« LES ACQUÉREURS NE SE RECOPIENT PAS, C'EST UNE DÉCISION.** Un acquéreur n'est pas un lien au bien : il existe PARCE QU'IL A FAIT UNE
  OFFRE. Ce fait est déjà tenu chez nous dans `app_affaire_ledger`. Le registre les **PROJETTERA** depuis le ledger ; il ne les stockera pas.
  **Deux copies finissent toujours par dire deux choses.** »
- la projection a été **remise à plus tard, pour une seule raison** : les co-acquéreurs du blob `acquereurs_json` sont sur les numéros de
  HEKTOR. *« LA PROJECTION VIENDRA QUAND CE BLOB SERA SUR NOS NUMÉROS. »* (La 2ᵉ mesure du 30/09 : le ledger connaît 98,9 % des couples,
  co-acquéreurs compris ; il restait 180 compromis à comprendre.)
- en attendant, la vue des liens d'un contact lit encore les acquéreurs dans la table de nuit refaite depuis Hektor.

**Donc les rôles sont déjà fixés :**
| registre | porte | numéros |
|---|---|---|
| des **contacts** | la personne | les deux (le dictionnaire) |
| des **relations** | personne ↔ bien (mandant, propriétaire) | les quatre |
| des **transactions** | personne ↔ affaire : acquéreurs (et co-acquéreurs), notaires | **le nôtre**, + la trace brute de Hektor là où elle est déjà (décision du 23/09) |
Il ne manque **aucune liste** : il manque que le registre des transactions désigne ses personnes **par nos numéros**.

**Le mécanisme révisé — À DÉCIDER, rien codé**
1. **Acquéreurs** : dans `acquereur_json` et `acquereurs_json`, chaque personne porte **aussi** notre numéro (`app_contact_id`) à côté de
   celui de Hektor (`id`) — exactement le montage du principal (deux colonnes), mais **dans le blob existant** : aucune colonne, aucune
   liste, la trace de Hektor gardée (23/09). La création l'écrit au clic ; la nuit le traduit par la doublure du serveur (G-10, `app_contact`,
   complète) et ne l'efface jamais.
2. **Notaires** : `notaire_acquereur_id` / `notaire_mandant_id` portent **notre** numéro (la nuit traduit, le plan du §50). La trace brute
   de Hektor reste où elle est déjà : `notaires_json` (vente, API) et `app_affaire_console` (compromis, console).
3. **Vers Hektor** : rien à changer — le worker prend le numéro de Hektor dans le registre des contacts avant chaque envoi (C-9).
4. **Ensuite, la décision du 30/09** : le registre des relations **projette** les acquéreurs depuis le registre des transactions, au lieu de
   la table de nuit — la seconde copie disparaît.
5. Les lecteurs : `aliasNumerosAcquereur` relie chaque personne de la liste (pas seulement le principal), R3 compare nos numéros, le chaînage
   SQL reçoit le numéro de Hektor (ou compare `app_contact_id`).

---

## 9. AUDIT DÉTAILLÉ DU MÉCANISME RÉVISÉ (§8) — pièce par pièce, 24/10 *(Frédéric : « oui, lance-le »)* — lecture seule, **rien codé**

### ⛔ Deux corrections de ce que j'avais écrit
- **Le chaînage n'a PAS le défaut annoncé** (§5, point 3) : la création calcule `v_acquereur_cible` (numéro de Hektor, par nos deux
  numéros — 1b du 22/10) et c'est lui qu'elle passe à `app_chaine_pour` et qu'elle range dans `hektor_acquereur_id`.
- **Il y a un SECOND écrivain du blob, en journée** : à la fin du travail de création, le worker **réécrit** `acquereurs_json`,
  `acquereur_json` et `mandants_json` avec ce que Hektor a **relu** (« classe B, les personnes », 16/09, worker l. ~15235-15300) — donc en
  numéros de Hektor, quelques minutes après le clic, sans toucher `hektor_acquereur_id` (« la CLÉ du chaînage des offres et de
  l'adoption au run »).

### Où vit vraiment le registre des transactions
**Le maître est le registre LOCAL du serveur** : chaque nuit `affaire_ledger.py` le refait depuis le miroir de Hektor (UPSERT, `acquereurs_json
= excluded`), `registre_depuis_console.py` y pose les notaires, puis le push recopie **toutes** les lignes chez Supabase. Le jour, deux
écrivains passent directement chez Supabase : la création (au clic) et le worker (la relecture). ➡ **Conséquence décisive pour le
rattrapage : une traduction écrite dans le code de nuit s'applique à TOUTES les lignes dès la première nuit** — il n'y a pas de
script de rattrapage séparé à lancer, mais c'est un effet de production à décider comme tel.

### Les écrivains, et ce que chacun devrait écrire
| écrivain | où | aujourd'hui | à changer |
|---|---|---|---|
| **la création** | Supabase, `app_change_annonce_status_optimistic` + `app_acquereurs_json` | principal : les deux numéros (1b) ; la liste : `id` = notre identité, ⚠ **un co-acquéreur passé sous son numéro de Hektor DISPARAÎT de la liste** (mesuré : `app_acquereurs_json(['605976'])` → 0 ; `(['20000015'])` → 1) ; notaires : nos numéros | la liste reconnaît **les deux** numéros (comme 1b) et chaque personne porte `id` (Hektor) **et** `app_contact_id` (nous) |
| **le worker (relecture)** | Supabase, PATCH | la liste relue chez Hektor : `id` = Hektor seul | ajouter `app_contact_id` à chaque personne (traduction par la fiche contact) — ou laisser la nuit le faire (quelques heures sans notre numéro) |
| **la nuit, acquéreurs** | local, `affaire_ledger.py` | la liste du miroir : `id` = Hektor ; `app_contact_id` traduit pour le principal seul (G-10) | traduire **chaque** personne de la liste avec la même table (`app_contact`, complète) ; ne jamais effacer |
| **la nuit, notaires** | local, `registre_depuis_console.py` | numéro de Hektor (API pour la vente, console pour le compromis) | écrire **notre** numéro (traduit) ; ⚠ traduire AVANT la comparaison « neuf = ancien », sinon chaque nuit réécrit tout ; garder le comptage des contradictions API / console **en numéros de Hektor** |
| **le push** | local → Supabase | recopie | rien (le blob est déjà décodé en jsonb) |

### Les lecteurs, et ce qui pourrait casser
| lecteur | lit | risque | parade |
|---|---|---|---|
| écran : noms des parties, « X et X » (`aliasNumerosAcquereur`) | `id` des personnes ; la paire du principal seulement | aucun : on **ajoute** une clé, `id` ne change pas | relier chaque personne par son `app_contact_id` |
| modale : préremplissage des acquéreurs | `acquereurs_json[].id` (Hektor) | il alimente la liste qui DISPARAÎT à la création (ci-dessus) | proposer `app_contact_id` d'abord |
| modale / rubrique : notaires | colonne notaire + `loadNomsContacts` (deux numéros) | aucun | — |
| **R3 `@notaire`** | la colonne notaire **comme preuve de ce que Hektor a retenu** | ⛔ **si la colonne porte NOTRE numéro, R3 comparerait la saisie à elle-même : « arrivée » sans preuve** (risque déjà noté le 23/10) | R3 juge contre la source Hektor (`notaires_json` de la vente, `app_affaire_console` du compromis), traduite |
| chaînage SQL, adoption de nuit (C.4 / 1b) | `hektor_acquereur_id` | aucun : la colonne reste celle de Hektor | — |
| worker, envoi | la charge, traduite (C-9) | aucun | — |
| worker, `personnes_posees` / 1.4 | numéros de Hektor des deux côtés | aucun | — |
| résumé du cockpit, rôles des contacts | le **miroir**, pas le registre | aucun | — |
| les deux formes du blob | 19 905 listes et 41 619 objets seuls (local, singulier compris) | un lecteur qui n'attend qu'une forme saute l'autre en silence (piège du 30/09) | traiter les deux, comme `lireMandantsAffaire` |

### La projection des acquéreurs dans les relations (la décision du 30/09) — mesurée
Sur le serveur, en lecture seule : la table de nuit porte **16 273** couples (acquéreur, bien), en **notre** identité ; le registre des
transactions en porte 16 300 en numéros de Hektor. **Comparés tels quels : 0 en commun** (deux séries). **Traduits par la doublure : 16 273
sur 16 273 (100 %)**, et 27 de plus que la nuit ne connaît pas. Les 180 compromis manquants du 30/09 n'existent plus. ➡ **La projection est
faisable dès que le blob porte nos numéros** ; elle remplacera la branche « acquéreurs » de la vue `app_contact_relations_current` (qui
lit encore la table de nuit). ⚠ Elle touche l'affichage des types de contacts : à faire avec le chantier des types, pas avant.

### L'ordre proposé (chaque pièce réversible, essais + témoin inverse ; ⛔ rien sans le « vas-y »)
1. **La création** : la liste reconnaît les deux numéros et porte `app_contact_id` (patch de base, accord) — corrige aussi la perte
   silencieuse d'un co-acquéreur.
2. **La nuit, acquéreurs** : chaque personne de la liste reçoit `app_contact_id` (code de nuit ; s'applique à tout dès la 1ʳᵉ nuit).
3. **La nuit, notaires** + **R3 contre la source Hektor** (code de nuit + worker, redémarrage des services file vide).
4. **Les lecteurs de l'écran** (alias, préremplissage).
5. **La projection des acquéreurs** dans les relations — avec le chantier des types.

---

## 10. PIÈCE 1 — PRÉPARÉE ET RÉPÉTÉE, **NON POSÉE** — 24/10 *(Frédéric : « vas-y »)*

**Le patch** : `supabase/patch_personnes_deux_numeros_2026-10-24.sql` (+ `_INVERSE`, `_REPETITION`), générateur
`phase2/checks/gen_patch_personnes_deux_numeros.py`. **Une seule fonction**, `app_acquereurs_json` — celle qui fabrique la liste des
personnes pour la **création** (les acquéreurs, le principal en tête) **et** pour la **modification** (les mandants) : la corriger couvre
les deux portes. Empreinte **1b82fdda → 69904a53**, une ancre (le corps), interrupteur `affaire_personnes_deux_numeros` posé **éteint**
(éteint = le texte d'avant, à l'identique).
- **Allumé** : une personne est trouvée par ses **deux** numéros ; `id` = numéro de **Hektor** (comme la relecture du worker et la nuit —
  `id` ne change plus de sens dans la journée) ; `app_contact_id` = **le nôtre** ; une personne donnée deux fois ne sort qu'une fois ;
  inconnue : rien ; sans numéro de Hektor encore : `id` garde notre identité.

**Répétition : 8/8**, envoyée telle que le fichier (T1 éteint : 605976 introuvable = le défaut ; T2-T3 trouvé par l'un ou l'autre numéro,
`id` 605976, `app_contact_id` 20000015 ; T4 une seule sortie pour deux numéros ; T5 l'ordre gardé ; T6 un inconnu ne fabrique personne ;
**T7 la création, appelée comme l'écran sur le bien d'essai 63331 avec l'acquéreur sous son numéro de Hektor, range l'acquéreur
(id 605976, app_contact_id 20000015) — avant, la liste sortait VIDE** ; T8 l'inverse rend 1b82fdda). Vérifié après : empreinte
1b82fdda, pas d'interrupteur, 63331 en Estimation, 0 ligne, 0 travail.

**Ce que ça pourrait casser ailleurs** : `id` passe de notre identité au numéro de Hektor **au clic** ; ce qui le lisait entre le clic et la
relecture du worker (quelques minutes) voit désormais le numéro que tout le reste porte déjà. Lecteurs vérifiés : la modale (préremplissage —
reconnu à présent dans les deux sens), la qualification (cherche les deux numéros depuis F2), `aliasNumerosAcquereur` (relie Hektor → nous),
le worker (lit la charge, pas le registre). Le principal, le chaînage et l'adoption ne bougent pas (`hektor_acquereur_id` / `app_contact_id`).
**Limite, dite franchement** : la relecture du worker puis la nuit réécrivent la liste **sans** `app_contact_id` — la clé ne tient
durablement qu'avec les pièces 2 (la nuit) et, pour la journée, l'ajout dans la relecture du worker. Seule, la pièce 1 corrige surtout la
**perte silencieuse** d'une personne passée sous son numéro de Hektor (acquéreurs à la création, mandants à la modification).

**Pour l'activer** : (1) coller le patch (accord) ; (2) allumer l'interrupteur (accord). Aucun déploiement, aucun redémarrage.

---

## 11. PIÈCE 2 — LA NUIT POSE NOTRE NUMÉRO SUR CHAQUE PERSONNE — codée, éprouvée hors ligne, **ÉTEINTE** — 24/10 *(Frédéric : « oui, d'abord pièce 2 »)*

**Le code** (`phase2/sync/affaire_ledger.py`, `refresh_ledger`) : juste avant l'écriture de chaque transaction, `poser_nos_numeros()`
**ajoute** `app_contact_id` (notre numéro) à chaque personne connue de `acquereur_json` (le principal) et de `acquereurs_json` (la liste) —
par la même table que la colonne du principal (G-10 : `app_contact` du serveur, complète). `id` garde le numéro de Hektor (la trace brute,
décision du 23/09) ; la forme du blob (liste ou objet seul) est gardée ; une personne inconnue ne reçoit rien ; rien à poser = le texte
d'origine à l'octet près. Le journal de nuit le dit : « personnes avec nos deux numéros : N numéro(s) posé(s) » — ou « ÉTEINT ».
- **Interrupteur** : `APP_AFFAIRE_PERSONNES_DEUX_NUMEROS=1` dans `.env`, lu **après** `.env` (même chemin que `APP_CHAINAGE_V2`, piège du 20/10).
  **Absent = éteint** : le fichier est en service dès qu'il est enregistré, mais il ne change rien tant que la ligne n'est pas posée.
- Lecteurs vérifiés : le chaînage (`_acquereurs`) ne lit que `id` ; la redescente des lignes de l'app ne ramène pas ces colonnes ; le push
  décode déjà le blob en jsonb.

**Essais** : `phase2/checks/test_personnes_deux_numeros.py` — **13/13**, sur trois copies des tables utiles (phase2.sqlite et le miroir
de Hektor ouverts en **lecture seule**, dossier temporaire effacé) :
- la fonction seule : 8 contrôles (liste, objet seul, inconnu, illisible, vide, « 0 », déjà posé, l'ordre et les clés gardés) ;
- **TÉMOIN INVERSE sur la vraie nuit** : la version d'avant (git HEAD) et la neuve **éteinte** rendent **le même registre, à l'octet près,
  sur les 31 103 lignes** (hors horodatages du run) ;
- **allumée** : aucune autre colonne ne bouge ; les listes ne changent **que** par l'ajout de `app_contact_id` ; **65 401 numéros posés sur
  30 410 lignes** ; **les 2 446 listes à plusieurs acquéreurs sont complètes** (= 1 809 compromis + 637 ventes mesurés au §3).
- **2 mutants attrapés** : l'interrupteur ignoré (le témoin inverse tombe), `id` remplacé au lieu d'ajouter (deux contrôles tombent).

**Ce que ça pourrait casser ailleurs** : rien de ce qui lit `id`. Une fois allumée, la **première nuit** pose nos numéros sur **toutes** les
transactions (c'est le rattrapage, sans script à part) ; Supabase les reçoit par le push habituel. ⚠ Le jour, la relecture du worker réécrit
encore la liste sans `app_contact_id` jusqu'à la nuit suivante — l'ajouter dans la relecture est une pièce à part (worker, redémarrage).

**Pour l'activer** : (1) Frédéric pousse ; (2) poser la pièce 1 (patch de base, accord) ; (3) ajouter `APP_AFFAIRE_PERSONNES_DEUX_NUMEROS=1`
au `.env` du serveur (accord) — effet à la nuit suivante ; (4) contrôler le lendemain matin le journal de nuit et quelques transactions.
---

## 12. PIÈCE 3 — LES NOTAIRES SOUS NOTRE NUMÉRO, ET R3 JUGE SUR LA SOURCE DE HEKTOR — codée, éprouvée hors ligne, **éteinte / non déployée** — 24/10 *(Frédéric : « oui, prépare la pièce 3 »)*

### 3a. La nuit — `phase2/sync/registre_depuis_console.py`
Quand il a choisi le notaire de chaque côté (l'API pour la vente, la console pour le compromis — numéros de Hektor), le script le
**traduit en notre numéro** par la doublure du serveur (`app_contact` : `hektor_target_id` → `app_contact_id`), **après** le comptage
des contradictions API / console (qui compare deux numéros de Hektor) et **avant** la comparaison « neuf = ancien » (sinon chaque nuit
réécrirait tout). Inconnu : le numéro de Hektor reste (reconnaissable à sa plage) ; on n'invente rien. Noms, origine, taux, unités : inchangés.
Le journal le dit (« notaires sous NOTRE numéro : N » ou « ÉTEINT »).
- **Interrupteur** : `APP_AFFAIRE_NOTAIRES_NOTRE_NUMERO=1` dans `.env` (à part de celui de la pièce 2 : un interrupteur, un changement).
  Absent = éteint. ⚠ Le script est en service dès qu'il est enregistré : il ne change rien tant que la ligne n'est pas posée.
- **Essais** `phase2/checks/test_notaires_notre_numero.py` — **7/7** sur copies (lecture seule, jamais `--pousser`) : **témoin inverse**
  (version d'avant = neuve éteinte, 31 103 lignes) ; allumée : aucune autre colonne ne bouge, chaque notaire change pour **notre numéro de
  la même personne**, **23 340 traduits, 0 sans paire** ; **stable** : une seconde nuit n'a plus rien à écrire. **2 mutants attrapés**
  (interrupteur ignoré, traduction supprimée).
- Premier passage allumé : les 23 340 lignes s'écrivent, et le script les envoie lui-même à Supabase (`--pousser`, ses huit colonnes) —
  c'est le rattrapage, la même nuit.

### 3b. R3 — `Console/console_job_worker.js` (`@notaire`)
R3 jugeait le notaire **sur la colonne du registre**, qui portait le numéro de Hektor. Une fois la colonne passée à **notre** numéro, il
aurait comparé la saisie à elle-même (« arrivée » sans preuve). Il lit désormais **ce que Hektor porte** :
- **vente** : `notaires_json` du registre (relu la nuit par l'API ; `entree` = acquéreur) — seulement une fois la nuit passée ;
- **compromis** : `app_affaire_console.notaires_acquereur` (la lecture de l'assistant) — seulement si elle est **postérieure** à la saisie ;
et compare **la personne** : notre saisie traduite par la fiche contact (ou déjà un numéro de Hektor). Indépendant de l'interrupteur 3a :
la règle est juste avant comme après.
- **Essais** `Console/test_controle_carnet_r3.js` — **47/47** (36 avant, dont (5) et (6) passés sur la console) : **(6b) le piège** — colonne
  à notre numéro, rien lu chez Hektor → « en attente », pas « arrivée » ; **(6b') témoin inverse** : la règle d'avant disait « arrivée » sur le
  même piège ; (6c) lecture de l'assistant antérieure → « en attente » ; (6d) vente, même personne → « arrivée » ; (6e) vente, autre notaire
  (JSON en texte) → « conflit » ; (6f) vente avant la nuit → « en attente ».
- ⚠ **Ne sert qu'après un redémarrage des 4 services, file vide** (Frédéric).

### Ce que ça pourrait casser ailleurs
L'écran nomme le notaire par ses deux numéros (`loadNomsContacts`) : rien à changer. La modale préremplit **notre** numéro, que le worker
traduit avant l'envoi (C-9). Le classeur et les exports ne lisent pas ces colonnes. Le comptage des contradictions reste en numéros de Hektor.

### Pour l'activer, dans l'ordre (chaque geste avec l'accord de Frédéric)
1. pousser (worker, scripts, essais) ; 2. redémarrer les 4 services, file vide (R3 neuf) ; 3. ajouter
`APP_AFFAIRE_NOTAIRES_NOTRE_NUMERO=1` au `.env` du serveur — effet à la nuit suivante ; 4. le lendemain matin : le journal de nuit
(« notaires sous NOTRE numéro ») et les deux lignes « notaire » en attente de l'essai 5, qui doivent passer « arrivée » à la relecture suivante.

---

## 13. ACTIVATION DES PIÈCES 1 À 3 — 24/10/2026, fin d'après-midi *(Frédéric : « active les pièces 1 à 3 »)*

| geste | quand | preuve |
|---|---|---|
| push (Frédéric) | avant 17:47 | `origin/main` = `41f0f2c` |
| file des travaux | avant le redémarrage | 0 en attente, 0 en cours |
| redémarrage des 4 services (Frédéric) | 17:47:48-50 | heure de démarrage des 4 processus `node`, postérieure au commit du worker (17:40:43) → **R3 neuf en service** |
| **pièce 1** posée | — | les 4 contrôles du patch OK (empreinte 69904a53, SECURITY DEFINER, fermée à authenticated, éteinte = comportement d'avant) |
| **pièce 1** allumée (`affaire_personnes_deux_numeros = on`) | — | `app_acquereurs_json(['605976'])` → l'acquéreur avec `id` 605976 et `app_contact_id` 20000015 ; sous ses deux numéros → 1 personne ; inconnu → rien |
| **pièce 2** : `APP_AFFAIRE_PERSONNES_DEUX_NUMEROS=1` au `.env` | — | sauvegarde `.env.avant_pieces_personnes_20261024` ; la fonction de la nuit le lit **allumé** |
| **pièce 3** : `APP_AFFAIRE_NOTAIRES_NOTRE_NUMERO=1` au `.env` | **après** le redémarrage | la fonction de la nuit le lit **allumé** (posé après, exprès : sans le R3 neuf, la colonne à notre numéro aurait été jugée « arrivée » sans preuve) |

**Retour arrière** : pièce 1 → éteindre l'interrupteur (ou `_INVERSE.sql`) ; pièces 2 et 3 → retirer la ligne du `.env` (la nuit suivante
reprend le comportement d'avant ; les numéros déjà posés restent, une clé de plus dans les listes, notre numéro dans les colonnes notaire).

**⏰ À CONTRÔLER DEMAIN MATIN (25/10), après le run de nuit :**
1. journal de nuit : « personnes avec nos deux numéros : N numéro(s) posé(s) » (attendu ~65 000) et « notaires sous NOTRE numéro » (attendu
   ~23 340, 0 sans paire) ;
2. Supabase : les listes `acquereurs_json` portent `app_contact_id` (les 2 446 multiples complètes) ; les colonnes notaire en ≥ 10 000 000 ;
3. l'essai 5 : la vente 23358 → acquéreur 605976 + 20000015 ; notaires 10064499 / 10355906 ; les deux lignes « notaire » du carnet passent
   « arrivée » à la prochaine relecture de l'annonce (R3 lit la console et `notaires_json`) ;
4. aucun travail en erreur, aucune alerte.

---

## 14. PIÈCE 4 — LES ÉCRANS LISENT NOTRE NUMÉRO — codée, **pas poussée** — 24/10 *(Frédéric : « oui, pièce 4 »)*

**Le code** (`apps/hektor-v1/src/App.tsx`, écran seul, rien en base ni chez Hektor) :
- le type d'une partie (`CkAffaireParty`) connaît `app_contact_id` ;
- **`aliasNumerosAcquereur`** relie désormais **chaque personne des listes** (`id` Hektor → `app_contact_id` nous), plus seulement la
  paire du principal : un **co-acquéreur** vu sous ses deux numéros sur deux étapes de la chaîne n'est plus compté deux fois (le « X et X »
  de C4, qui restait vrai pour le 2ᵉ acheteur) — rubrique Affaires, noms des parties, dédoublonnage de la chaîne ;
- **`lireMandantsAffaire`** rend aussi notre numéro (`app`) quand la liste le porte ;
- **la modale** préremplit les acquéreurs **par notre numéro** d'abord, celui de Hektor sinon. Les deux sont reconnus à la création
  (pièce 1) et traduits par le worker avant l'envoi (C-9) : ce qui part chez Hektor ne change pas.
- Non touchés, et c'est voulu : les mandants (Hektor les déduit — décision du 22/10 ; la liste relue n'a pas notre numéro), les notaires
  (l'écran les nomme déjà par leurs deux numéros).

**Essais** `apps/hektor-v1/test_rubrique_affaires_complete.cjs` — **32/32** (2 neufs) ; **témoin inverse** : la version d'avant échoue
**exactement** les 2 neufs (le co-acquéreur y est nommé deux fois ; le lecteur ne rend pas notre numéro). `npm run build` vert ; `\r\r\n` = 0.

**Ce que ça pourrait casser ailleurs** : rien de ce qui lit `id` (on ajoute un champ). Les listes ne portent notre numéro qu'avec les pièces
1 et 2 : avant elles, l'écran se comporte comme avant. ✅ **Vu à l'écran le 24/10 vers 18:20** (poussé `61bdb50` ; Vercel a construit les deux commits, d'où deux noms de code, C2YzI53r
puis mQoUX400 — aucun autre commit) : VA6482, rubrique Affaires → 7 dossiers, l'acquéreur de la vente nommé **une seule fois** ; modale,
onglets Vendu et Compromis → l'acquéreur prérempli une fois, boutons inchangés ; modale fermée sans rien envoyer ; **0 erreur** dans la
console. Les listes ne portent pas encore notre numéro (la nuit les posera) : l'écran prend donc le numéro de Hektor, comme prévu.
⚠ Le 1ᵉʳ chargement juste après le déploiement est resté bloqué sur « Préparation de ton agenda… » ; un rechargement l'a débloqué.
L'accueil affichait « Synchronisations en erreur : 3 » : c'est le compte des **biens en erreur de diffusion** (le même que les « 3 erreurs »
de la carte Diffusions, `mandatStats.withErrors`), pas des travaux — aucun travail en erreur depuis le redémarrage de 17:47.

---

## 15. LA PREMIÈRE NUIT DES PIÈCES 2 ET 3 — contrôle du 25/10 à 07:20 *(Frédéric : « le run est terminé, peux-tu contrôler »)*

**Le run** (`logs/scheduled/quotidien_2026-10-25_04-00-01.log`) : **exit 0, « Pipeline finished successfully »** à 06:22:40.
- pièce 2 : « personnes avec nos deux numéros : **65 426 numéros posés** » (l'essai sur copie en annonçait 65 401 la veille) ;
- pièce 3 : « notaires sous NOTRE numéro : **23 340** (sans traduction : **0**) » ; **17 121** lignes écrites et **17 121 envoyées** à l'app.
- Avertissements connus, sans rapport : le ménage des orphelins de recherche échoue (3ᵉ nuit), des 403 sur des fiches de contacts.

**La descente** (`descente_2026-10-25_06-45-01.log`) : **exit 0**, 06:45 → 07:05 (descente, relevé, magasin).

**Supabase après la nuit** :
| quoi | mesure |
|---|---|
| personnes des listes avec notre numéro | **35 005 / 35 008** (3 inconnues de la doublure : rien inventé) |
| acquéreurs principaux avec notre numéro | **30 421** |
| listes à plusieurs acquéreurs complètes | **2 447 / 2 447** |
| notaire de l'acquéreur | **6 772 à notre numéro, 0 à celui de Hektor** |
| notaire du vendeur | **16 568 à notre numéro, 0 à celui de Hektor** |
| travaux depuis 14 h | 1 059 faits, **0 en erreur** |
**L'essai 5** : offre, compromis et vente portent l'acquéreur sous ses deux numéros (605976 / 20000015), dans la colonne et dans la liste ;
notaires 10064499 (« CORNU, SELARL… » côté console, « Tiffany SELARL… » côté API) et 10355906. Les deux lignes « notaire » du carnet sont
encore « en attente » (jugées le 23/10) : R3 les rejugera à la prochaine relecture de l'annonce (plus de 6 h après) — à voir.

### ⚠ Trouvé au passage : LES TÂCHES ONT GLISSÉ D'UNE HEURE (passage à l'heure d'hiver, nuit du 24 au 25/10)
Les déclencheurs sont enregistrés avec un décalage figé `+01:00` (heure d'été, tâches synchronisées sur l'heure universelle) : depuis cette nuit,
elles tournent **une heure plus tôt** en heure locale. Quotidien 05:00 → **04:00** · Descente 07:45 → **06:45** · Sauvegarde 09:00 →
**08:00** · Recherches 03:00 → **02:00** · Balayage photos 00:00 → **23:00** · Entretien photos 21:00 → **20:00** · Entretien documents
22:00 → **21:00** · Reprise envois 12:30 → **11:30** · Relances e-mail : **08:00 inchangé** (pas d'heure figée). Toutes ont rendu 0 ; l'ordre
de la nuit est gardé, mais la Sauvegarde tombe désormais à la même heure que les Relances (08:00). **Rien n'a été modifié : à décider par Frédéric.**
