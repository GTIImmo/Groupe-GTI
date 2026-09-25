# Audit — la règle des deux numéros, appliquée à TOUTES les tables

*25/09/2026, demandé par Frédéric après que j'ai reproduit le même défaut deux fois
dans la même journée.*

> *« Ce n'est pas normal, les deux points document et photos faisaient partie du plan
> dev, comment as-tu pu oublier alors qu'on a tout fait pour que tu ne perdes pas le
> fil ? C'est l'essence même du dev. »*

---

## 1. Le mécanisme de l'oubli — il est systématique, pas accidentel

**Le matin :** j'audite `app_console_document_fingerprint`, je trouve qu'elle n'a que
le numéro Hektor, je la corrige (`3f2c203`), j'écris un test, je documente.

**Trois heures plus tard :** j'écris `rattrapage_photos.js`, qui crée **435 126 lignes**
avec le seul numéro Hektor. Le même défaut, dans du code neuf, le jour même.

**Le diagnostic :** *j'applique la règle quand j'INSPECTE du code existant ; je ne me
l'applique pas quand j'en ÉCRIS.* Les garde-fous du projet (§0 de CLAUDE.md, la mémoire,
les notes) sont tous tournés vers l'audit de l'existant. Aucun ne se déclenche au moment
où une table gagne une ligne neuve.

**La parade, concrète :** tout code qui **crée** une ligne portant un numéro Hektor doit
passer le contrôle « et notre numéro ? » **avant** d'être proposé, au même titre que la
syntaxe. Les tests de `rattrapage_photos.js` le vérifient désormais (contrôles u à z), et
c'est ce patron qu'il faut reprendre pour tout nouveau magasin.

---

## 2. L'audit systématique — trois questions, trois réponses

### ① Quelles tables portent un numéro Hektor SANS notre numéro ?

**19 trouvées.** Toutes ne sont pas des défauts :

| nature | combien | verdict |
|---|---|---|
| **vues** (`app_v_*`, `app_contact_searches_current`, `app_*_sans_numero`…) | 6 | ✅ dérivées, elles ne stockent rien |
| **tables de diagnostic** qui parlent justement des numéros manquants | 4 | ✅ c'est leur sujet |
| **`*_provisional`** (annonce, contact, recherche) — 0 ligne | 3 | ✅ la couche « avant le numéro », par conception |
| `app_ticket_migration` — 12 162 lignes | 1 | ✅ trace de migration, ancrée sur Hektor par nature |

**Restent 5 vrais trous :**

| table | lignes | ce que c'est |
|---|---:|---|
| **`app_matterport_group`** | **4 484** | les visites virtuelles, par annonce — **et absente du repointage** |
| `app_hektor_negotiator_agency_directory` | 219 | l'annuaire négociateurs / agences *(déjà au plan)* |
| `app_diffusion_agency_target` | 34 | les cibles de diffusion par agence |
| `app_google_workspace_identity` | 5 | la correspondance comptes Google ↔ négociateurs |
| **`app_mandat_champ_app`** | **2** | ⚠ **les champs du mandat qui appartiennent à l'app** — presque vide aujourd'hui, mais c'est l'un des interrupteurs de fond de l'autonomie. Elle va grossir avec le seul numéro Hektor. |

### ② Toutes les tables de `REPOINT_TABLES` ont-elles bien `app_dossier_id` ?

**✅ 22 sur 22.** Sans la colonne, le repointage échouerait ligne par ligne, en silence.
La liste est saine.

### ③ Quelles tables portent NOTRE numéro mais sont HORS du repointage ?

C'était exactement le défaut de l'empreinte. Résultat :

| table | lignes | verdict |
|---|---:|---|
| `app_contact_relation_current` | 81 343 | ✅ **reconstruite chaque nuit** (DELETE + rebuild par contact) — elle se répare seule |
| `app_affaire_ledger` | 31 229 | ✅ l'upsert **remet à jour** `app_dossier_id` à chaque passage (l. 767)… ⚠ **sauf pour une affaire que Hektor ne rend plus** : `delete-never` la fige, son numéro ne bougera plus |
| `app_affaire_repartition` | 15 993 | ⚠ **non vérifié** |
| `app_console_deleted_annonce_log` | 78 | ✅ journal, par conception |
| `app_annonce_champ_app` | 3 | ⚠ **à surveiller** — les champs d'annonce qui appartiennent à l'app, hors repointage |
| `app_annonce_pending`, `app_pending_resolution`, `app_affaire_personne_ecart` | 1 à 2 | ✅ couches éphémères |
| `app_dossier_v1`, `app_dossier_detail_v1`, `app_work_item_v1`, `app_relation_provisional`, `app_affaire_condition`, `app_affaire_note` | 0 | ✅ vides — anciennes versions |

---

## 3. Ce qu'il faut faire, par ordre

| | | |
|---|---|---|
| **1** | `app_matterport_group` | 4 484 lignes, numéro Hektor seul **et** hors repointage — **exactement le défaut de l'empreinte**, en plus gros |
| **2** | `app_mandat_champ_app` | donner le numéro d'app **maintenant**, pendant qu'elle a 2 lignes, pas quand elle en aura 50 000 |
| **3** | `app_annonce_champ_app` | entrer dans `REPOINT_TABLES` |
| **4** | `app_affaire_repartition` | vérifier si elle se répare seule |
| **5** | `app_affaire_ledger` | le cas des affaires que Hektor ne rend plus |
| **6** | négociateurs / agences / diffusion / Google | déjà au plan, volumes faibles |

⚠ **Et le contrôle qui manque au projet** : une sonde qui vérifie chaque nuit
qu'aucune table ne porte un numéro Hektor sans le nôtre. Les trois requêtes de cet audit
en sont le brouillon. Sans elle, le prochain magasin créé refera le même défaut — j'en
suis la preuve.

## 4. Ce qui n'a pas été mesuré

- Si les 4 484 lignes Matterport sont réellement orphelinées aujourd'hui *(la table est
  peut-être réécrite à chaque run, comme `app_contact_relation_current`)*.
- `app_affaire_repartition` : réécrite ou accumulée.
- Les tables **locales** (SQLite) n'ont pas été passées au même crible — cet audit ne
  porte que sur Supabase.
