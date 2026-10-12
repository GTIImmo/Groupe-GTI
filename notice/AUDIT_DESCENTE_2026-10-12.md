# Audit — la descente du matin (Supabase → serveur)

*12/10/2026, lecture seule. Question de Frédéric : « à quoi sert la descente ? pourquoi ne pas
récupérer que les mises à jour ? ». Déclencheur : la descente de ce matin (49 min, fin 09:04) a
saturé Supabase de 08:44 à 09:00 — l'app recevait des 522/504, la relance de 09:00 a échoué.*

## 1. À quoi elle sert (code : `phase2/sync/pull_from_supabase.py`, lanceur `scheduled/run_descente.ps1`)

1. **Sauvegarde** (B.1, 22/08) : tout ce que l'app invente n'existe qu'en ligne (documents, travaux,
   rapprochements, estimations, notifications…). La descente en garde une copie dans
   `phase2/phase2.sqlite`, sauvegardée ensuite.
2. **Entrée du run de nuit** (depuis fin août) : les registres du serveur lisent les **doublures
   `__sb`** pour reprendre ce que l'app a créé et ne pas le dupliquer :
   `relation_ledger.py` (`app_relation__sb`, `app_contact_relation_current__sb`),
   `mandat_ledger.py` (`app_mandat__sb`), `affaire_ledger.py` (`app_affaire_ledger__sb`,
   `app_affaire_champ_app__sb`), `pousser_numeros_contact.py` (`app_contact_current__sb`),
   + la surveillance (`check_gti_health.py`).
3. **Relevé des écarts** (`comparer_doublures.py`) et magasin des champs app (`magasin_annonce_app.py`).

## 2. Ce qu'elle descend (journal du 12/10)

151 objets · 1 738 957 lignes · 2 530 appels · 2 957 s.

| catégorie | objets | lignes | part |
|---|---|---|---|
| **vues** (recalculées à chaque lecture, doublons de tables déjà copiées) | 41 | 437 956 | **25 %** |
| doublures `__sb` (lues par le run de nuit) | 15 | 349 652 | 20 % |
| autres tables | 95 | 951 349 | 55 % |

Plus grosses vues descendues : `app_contact_relations_current` 167 669 · `app_contacts_current`
62 189 · `app_v_correspondance_identite_cible` 62 189 · `app_annonces_current` 48 793 ·
`app_registre_mandats_current` 24 502 · `app_dossiers_current`, `app_dossier_details_current`,
`app_dossier_match_attrs` 13 475 chacune. Elles sont aussi les plus coûteuses côté Supabase :
chaque page refait le calcul de la vue (pages de 32 Mo ramenées à 500 lignes pour le détail).

## 3. Le delta existe déjà, mais sur 5 tables seulement (16/09 et 01/10)

`app_rapprochement_score_history`, `app_console_job_log`, `app_affaire_console`,
`app_affaire_repartition`, `app_console_photo`. Condition posée : l'horodatage doit être écrit à
**chaque** écriture (déclencheur ou historique où l'on ne fait qu'ajouter), sinon le delta
rate des modifications en silence. Filets : comparaison des totaux, copie complète tous les
7 jours, plafond de 50 000 lignes.
Le 12/10, `app_console_job_log` (307 422 lignes) est passée en copie complète : c'était son
tour hebdomadaire (`derniere_complete` = 12/10).

## 4. Ce qui change vraiment en 24 h (mesure du 12/10)

| table | total | modifiées en 24 h | remarque |
|---|---|---|---|
| `app_console_document` | 156 300 | 7 998 (5 %) | `updated_at` sans déclencheur → non fiable en l'état |
| `app_console_job` | 92 597 | 1 012 (1 %) | idem (le statut change sans garantie d'horodatage) |
| `app_console_job_log` | 307 472 | 3 122 | journal, déjà en delta |
| `app_console_document_fingerprint` | 53 895 | 1 000 | sans déclencheur |
| `app_relation` | 132 728 | 132 711 | **`last_seen_at` réécrit chaque nuit par le run** → inutilisable comme delta |
| dont relations nées dans l'app (≥ 1 000 000) | **2** | | le run lit 132 728 lignes pour en adopter 2 |
| `app_affaire_ledger` nées dans l'app | 330 / 31 058 | | même constat |
| `app_mandat` nés dans l'app | 0 / 26 851 | | |

## 5. Pourquoi on ne descend pas « que les mises à jour » partout

- **Pas d'horodatage fiable** : sur la plupart des tables, `updated_at` n'est rempli que si
  l'écrivain y pense (aucun déclencheur, sauf `app_console_photo`). Un delta y raterait des
  changements sans bruit.
- **Un delta ne voit pas les suppressions** : d'où le filet du comptage + copie complète.
- **Certaines tables sont réécrites en entier chaque nuit** par le run lui-même
  (`app_relation`, contacts, annonces) : leur horodatage bouge pour toutes les lignes, le delta
  n'y gagnerait rien.

## 6. Pistes, de la plus sûre à la plus lourde (non décidées)

| | geste | gain estimé | risque |
|---|---|---|---|
| **A** ✅ *fait le 12/10 (`VUES_NON_DESCENDUES`, à blanc : 151 → 110, les 15 doublures intactes) — premier vrai passage : descente du 13/10 07:45* | **ne plus descendre les vues** (41 objets) : leurs tables sont déjà copiées ; ne garder que celles qu'un script lit réellement (à vérifier une par une) | ~25 % des lignes, et la partie la plus coûteuse pour Supabase | faible, si aucun script ne lit une vue descendue |
| **B** | **doublures `__sb` : ne descendre que les lignes nées dans l'app** (≥ 1 000 000) pour `app_relation`, `app_mandat`, `app_affaire_ledger`, `app_contact_relation_current` — c'est tout ce que les registres lisent pour adopter | ~15–18 % | moyen : vérifier chaque lecture des doublures (les retraits, la garde de fraîcheur de `relation_ledger`) |
| **C** | **poser des déclencheurs `updated_at`** (comme pour les photos le 01/10) sur `app_console_document`, `app_console_job`, `app_console_document_fingerprint`, puis les passer en delta | ~17 % | patch SQL à coller ; les filets du delta restent |
| **D** | ne plus descendre ce que le serveur a lui-même poussé dans la nuit (annonces, contacts) | variable | à auditer : ces tables portent aussi des colonnes écrites par l'app (photos `_app`, champs app) |

**Ordre conseillé** : A puis C, qui ne changent rien au run de nuit ; B ensuite, avec épreuve sur
les registres ; D seulement après audit des colonnes écrites par l'app.

## 7. Compléments du 12/10 (questions de Frédéric)

**Pourquoi les vues descendent ?** Aucune raison voulue. La descente prend « tout ce que l'API
expose » (découverte automatique, pour ne jamais oublier une table) ; les vues y sont exposées
comme les tables. La note du 21/08 le constatait déjà (« vues comprises, donc avec des
doublons ») sans le corriger. Vérifié le 12/10 : **aucun script local ne lit une copie de vue**
(`FROM`/`JOIN` sur les 41 noms, hors descente) ; les scripts qui nomment une vue l'interrogent
directement dans Supabase.

**Peut-on connaître les mises à jour de chaque table de l'app ?** Inventaire des 110 tables
(colonnes et déclencheurs ; `pg_stat` inutilisable ce jour, remis à zéro par le passage en Small) :

| | tables | lignes (est.) |
|---|---|---|
| A — date de modification garantie par la base (déclencheur) | 1 (`app_console_photo`) | 438 k |
| B — `updated_at` présent, rempli par le programme, non garanti | 48 | 437 k |
| C — autre date (`refreshed_at`, `last_seen_at`…) posée par le run/worker | 28 | 413 k |
| D — seulement une date de création (journaux… mais aussi `app_rapprochement`, `app_notification` qui SONT modifiées) | 21 | 817 k |
| E — aucune date | 12 | 103 k |

Méthode pour savoir précisément : **une seule fonction de déclencheur `updated_at := now()`,
posée sur chaque table modifiable, et qui ne tamponne que si la ligne change vraiment**
(`NEW IS DISTINCT FROM OLD`), sinon le run de nuit, qui réécrit tout, tamponnerait tout. Les
suppressions restent invisibles à une date : journal des suppressions ou copie complète
hebdomadaire (déjà en place).

**Les doublures `__sb`** : ce sont les seules tables qui existent **deux fois** — une version
construite par le serveur (nom normal, en local) et la version du cloud, qui contient en plus ce
que l'app y a écrit. La descente ne peut pas écraser la version du serveur : elle range celle du
cloud à côté, sous `<nom>__sb`. Le run de nuit les compare pour reprendre ce que l'app a créé.
Les 5 grosses (relations 132 k, relations contacts 85 k, contacts 62 k, affaires 31 k, mandats
27 k) sont surtout les lignes du serveur qui lui reviennent ; la part née dans l'app est de
2 relations, 330 affaires, 0 mandat.

## 8. Vérification approfondie (12/10, après « audite encore »)

**Vues — confirmé sans usage.** Aucun lecteur local : ni `FROM`/`JOIN`, ni lecture par
`sb_pull_state` (seuls lecteurs : `relation_ledger`, `relation_disparue`,
`decaler_doublure_contacts`, `repartition_commission`, `apres_descente` — aucun ne vise une vue).
La sauvegarde quotidienne (`backup_critical.py`) ne prend que des tables natives ; les copies
descendues ne sont sauvegardées que via l'instantané hebdomadaire de `phase2.sqlite`.
Les étapes 2 et 3 de la descente (`comparer_doublures`, `magasin_annonce_app`) ne lisent pas de vue.

**Doublures — CORRECTION de la § 7.** Le run de nuit **redescend lui-même** juste avant usage
`app_affaire_ledger`, `app_relation`, `app_mandat` et `app_affaire_console`
(`run_full_pipeline.ps1` l.850, 987, 1040, 1172). La copie du matin n'est donc PAS celle qu'utilisent
les registres ; elle sert au relevé des écarts, à la surveillance et à `pousser_numeros_contact`
(`app_contact_current__sb`, non redescendue la nuit). Et ce que lisent les registres :

| registre | lignes lues dans la doublure |
|---|---|
| `mandat_ledger` | seulement les mandats nés dans l'app (≥ 1 000 000) |
| `relation_ledger` | les relations nées dans l'app **+ tous les retraits** (`retire_le`) posés par l'app, y compris sur des liens venus de Hektor |
| `affaire_ledger` | **toutes** les affaires ayant un n° Hektor, pour reprendre le numéro donné par le cloud (+ les affaires sans n° Hektor) |

Donc « ne descendre que les lignes ≥ 1 000 000 » serait FAUX pour les relations (retraits ratés) et
pour les affaires (identités ratées). Le bon filtre est « ce qui a changé » — d'où le tampon.

**Tampon `updated_at` — points à respecter.**
- Les écrivains posent déjà `updated_at = now` à chaque passage, même sans changement
  (ex. `upsertConsoleDocuments`, à chaque synchro de documents) : la date actuelle ne dit donc pas
  « a changé », seulement « a été réécrite ».
- Le déclencheur doit comparer l'ancienne et la nouvelle ligne **hors colonnes de tampon**
  (`updated_at`, `synced_at`, `refreshed_at`, `last_seen_at`) et garder l'ancienne date si rien
  d'autre n'a bougé. À mesurer avant : `metadata_json` des documents change-t-il à chaque synchro
  (lien console à jeton) ? Si oui, il faut l'exclure ou le traiter.
- Lecteurs métier de `updated_at` trouvés : `app_console_action_enqueue_due_retries` (délai de
  reprise = 5 min × tentatives depuis `updated_at` des travaux), `app_action_status` (« depuis »),
  `app_cockpit_activite` (relances, en repli seulement). Le front n'utilise pas `updated_at` des
  documents ni des travaux. Le fil d'activité n'utilise plus `updated_at` des documents depuis le 23/07.
- Les suppressions restent invisibles : la copie complète hebdomadaire reste le filet.

*Non mesuré : la durée gagnée par piste (le temps est surtout dans les vues et les pages
lourdes, pas proportionnel aux lignes) ; quelles vues descendues sont lues par un script local.*
