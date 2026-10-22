# CHANTIER ⑧ — GARDÉ CHEZ NOUS EN ENTIER — *ouvert le 21/10/2026*

> Source : plan, section « 🧭 LES CHANTIERS DE L'ÉTAPE 2 », ligne ⑧ ·
> `notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md` §2 ⑧ (l. 207-228) et §3 (contact, mandant,
> documents, RDV).
> Méthode : CLAUDE.md §0. Un point à la fois. Rien n'est fini tant que ce n'est pas écrit ici.

## Les points

| # | le point | état |
|---|---|---|
| 8a | contact : champs écrits chez nous à la **création** et à la **modification** | 🔎 **audit REFAIT le 21/10 à la demande de Frédéric (« on l'a déjà fait ») — verdict corrigé : FAUX pour l'étape 2**, il avait raison ; attend sa décision de clore |
| 8b | périmètre du cloud : 62 281 contacts sur ~356 000 *(question à Frédéric)* | ⬜ |
| 8c | corps complet des archives d'annonces seulement dans le miroir `data/hektor.sqlite` | ⬜ |
| 8d | sauvegarde quotidienne : `app_relation`, `app_relation_registry`, `app_mandat`, carnets ; stockage Supabase ; Veeam jamais restauré | ⬜ |
| 8e | bon de visite archivé nulle part | ⬜ |
| 8f | document retiré dans Hektor : ligne supprimée sans trace | ⬜ *(⚠ le prune a changé le 20/10 : deux garde-fous — à remesurer)* |
| 8g | ⏳ C.9-couple : la mesure exige un geste humain, **tant que Hektor vit** | ⬜ |

---

## 8a — les champs du contact

### Audit du 21/10 *(lecture seule)* — verdict : **PARTIEL**

**Le code, en base** *(empreintes `md5(replace(pg_get_functiondef, chr(13), ''))`)* :

| fonction | empreinte | ce qu'elle écrit dans `app_contact_current` |
|---|---|---|
| `app_create_contact_optimistic(jsonb, integer)` | `f1563f572a8f2b4ea985e5f111144b37` | nom, prénom, display_name, email, phone_primary, negociateur_email, agence_nom |
| `app_create_mandant_contact_optimistic(bigint, text, jsonb, integer)` | `e787461fd5efed34663e93ba5c92fea6` | **les mêmes** *(2ᵉ porte, trouvée par une recherche de tous les `insert into app_contact_current`)* |
| `app_edit_contact_optimistic(text, jsonb, integer)` | `79d39e0e506d8afd3224fe20624598b3` | 12 colonnes : nom, prénom, civilité, email, phone_primary, phone_secondary, ville, code_postal, adresse, birth_date, birth_place, marital_status |

**Ce que l'écran envoie** : `hContactPayload` (`apps/hektor-v1/src/lib/api.ts:9782`) — une
quarantaine de clés. La modification envoie **toutes** les clés non vides dans `push_fields`
(`api.ts:9905-9909`) : **tout part chez Hektor**, seules les 12 colonnes s'écrivent chez nous.

**Trois familles de champs :**

1. **Ils ont une colonne, mais la création ne les écrit pas** : civilité, 2ᵉ téléphone,
   adresse, code postal, ville, date et lieu de naissance, situation familiale, commentaire.
   Ils n'apparaissent qu'après le retour de Hektor **et** le run de la nuit.
   ⚠⚠ **Trois d'entre eux, Hektor ne les renvoie JAMAIS** : `CHAMPS_APP_CONTACT =
   ("birth_date", "birth_place", "marital_status")` (`phase2/identite/contrat_autorite.py:63`).
   Saisis à la création, **ils n'arrivent jamais dans notre base** — ils ne restent que dans
   la charge du travail.
2. **Il a une colonne, mais la modification ne l'écrit pas** : le **commentaire**
   (colonne `commentaires` ajoutée le 02/10, `supabase/patch_contact_commentaires_2026-10-02.sql`,
   **17 978 contacts** l'ont). `col_map` ne le connaît pas.
3. **Aucune colonne chez nous** : raison sociale, forme juridique, SIRET, métier, site web,
   les 7 champs du conjoint, catégorie, source, réglages CRM. Ils ne vivent que chez Hektor.
   Même le miroir du serveur ne les porte presque pas *(échantillon de 20 000 `raw_json` :
   SIRET 43, société 0, conjoint 0 — la liste Hektor ne les livre pas)*.
   Le formulaire de modification les **pré-remplit à vide** (`App.tsx`,
   `contactIdentityInputFromContact`) ; ce n'est **pas destructeur** : une case vide devient
   `null` (`api.ts:9773`) et n'est pas envoyée.

**L'usage réel, mesuré :**

| travail | nombre | dernier | champs « perdus » remplis |
|---|---|---|---|
| `create_hektor_contact` | 16, tous `done` | 21/09 | naissance 0 · adresse 1 · commentaire 2 *(essais de mai-juin)* |
| `create_hektor_mandant_contact` | 17, tous `done` | 25/08 | 5 avec adresse / commentaire / naissance |
| `update_hektor_contact` | 23, tous `done` | 12/10 | société, SIRET, conjoint : **0 sur 39 charges** |
| `app_contact_pending` | 0 ligne | | |

➡ **Le trou est réel dans la structure, quasi nul dans l'usage** : aucune création depuis
le 21/09, aucune perte mesurée d'un champ que Hektor ne rend pas.

**L'historique** : aucune décision de limiter les champs. Le commentaire de la fonction dit
*« on n'inscrit QUE ce qu'on sait dire, un champ absent reste vide plutôt que d'être
inventé »* — c'est contre l'**invention**, pas contre un champ **saisi**. La liste vient de la
ligne provisoire de C.9 (31/08), recopiée par L4-b (21/09).

**Vérifié, ne casse pas** : le garde-fou anti-écrasement du worker ne lit que `_date_maj` dans
la photo (`console_job_worker.js:18277-18292`) · au retour d'une création, le worker ne
patche que `hektor_target_id` (`:18184-18201`) · la nuit, un contact en attente est protégé en
entier (`push_contacts_to_supabase.py`, `fetch_dirty_contact_ids`) et les 3 champs propres à
l'app sont réinjectés (`fetch_app_owned_contact_fields`).

### ⛔ Audit refait le 21/10 — **le premier verdict était FAUX** *(Frédéric : « c'est bizarre, on l'a déjà fait »)*

Le premier audit *(et celui du 08/10)* n'a regardé que **la fonction qui crée**. Il n'a pas
suivi **ce qui se passe après**. Deux mécanismes existent déjà :

1. **La relecture juste après la création.** Quand Hektor a créé le contact, le worker enfile
   un `refresh_console_contact_data` *(« sync_job » dans le résultat du travail)*, qui relit la
   fiche Hektor et **réécrit toute la ligne** de `app_contact_current`
   (`console_job_worker.js:4326`, `phase2/sync/refresh_contact_inproc.py`). **Mesuré** sur les
   créations du 21/09 : clic 13:06:10 → Hektor 13:06:28 → **fiche complète 13:06:47** ; 14:35:09
   → 14:35:41 → **14:36:02**. Même geste après une modification réussie (`:18300`).
   **105 relectures `done` depuis le 15/09, 1 en erreur.**
2. **La naissance, le lieu, la situation familiale** : ⚠ **ma phrase « ils n'arrivent jamais »
   était FAUSSE.** Hektor ne les rend pas par son API, mais une étape du run de nuit **lit le
   formulaire Hektor** et les pousse chez nous (`phase2/sync/sync_console_contact_missing.py`,
   `run_full_pipeline.ps1:800-825`, 50 contacts par nuit, les plus récents d'abord, jamais par du
   vide, jamais sur un contact en cours d'édition).

➡ **Les « 6 champs » ne durent qu'environ 40 secondes**, le temps que Hektor réponde.

**Ce qui reste VRAI, et seulement ça :**
- **si Hektor ne répond pas** *(panne, création en échec — non rejouée, décision C.4-bis)*, les
  champs en plus restent dans la charge du travail et ne s'affichent pas sur la fiche. Aucun cas
  mesuré : **16 + 17 créations, toutes `done`**. L'échec se voit depuis 4c *(chantier ④)* ;
- **raison sociale, SIRET, conjoint, site, catégorie, CRM** n'ont pas de colonne chez nous, même
  après la relecture. Ils ne vivent que chez Hektor. **0 sur 39 charges** les a remplis. C'est
  un sujet de **coupure** *(étape 3)*, pas de l'étape 2 où Hektor vit.

**Leçon** : *un audit d'une fonction d'écriture doit suivre le geste jusqu'au bout — ce que
le worker et le run font APRÈS*. Voir [[un-commentaire-de-code-n-est-pas-une-mesure]].

### ⭐ Le cadrage de Frédéric (21/10) : *« le but est d'anticiper la coupure »*

Sous cet angle, 8a **redevient un vrai point** — mais pas celui du premier audit :
**aujourd'hui la fiche est complète PARCE QUE Hektor nous la renvoie.** Le jour de la coupure,
le relais disparaît.

**Ce que Hektor renvoie vraiment** *(mesuré : toutes les clés non vides des `raw_json` des
5 369 contacts 600000-605500 de `data/hektor.sqlite`)* : civilité, nom, prénom, email,
portable, fixe, bureau, adresse, code postal, ville, commentaires, SIRET, site (`url`),
typologie, `refCouple`, négociateur, agence. **+** naissance / lieu / situation par le
lecteur du formulaire *(50 par nuit, périmètre « éligible »)*.

**Ce qu'il ne renvoie JAMAIS** — saisi dans l'app, ça n'existe chez nous que dans la charge du
travail (`app_console_job.payload_json`) : **forme juridique, métier du partenaire, source,
catégorie, les 3 réglages CRM**. Le **conjoint** devient une seconde fiche chez Hektor, liée
par `refCouple` → c'est **8g (C.9-couple)**, non mesuré.

### 🔎 Revue complète du registre des contacts — 21/10 *(Frédéric : « nous avons passé des mois sur le registre des contacts pour l'autonomie, tu dois tout savoir »)*

**Ce qui EXISTE, relu dans le code et mesuré :**

| protection | où | mesure du 21/10 |
|---|---|---|
| le registre des **numéros** (jamais de suppression, `absent_depuis`) | `phase2.sqlite` → `app_contact` · dans la sauvegarde quotidienne (`backup_critical.py:125`) | 356 584 numéros |
| la **fiche** chez nous, 44 colonnes | Supabase `app_contact_current` — adresse *(lot 1, `85fd24a`, 24/06)*, naissance/lieu/situation *(lot 3, `f0851e8`, propres à l'app)*, commentaires *(02/10)* | 62 281 fiches · 32 655 adresses · 261 naissances · 17 978 commentaires |
| la **doublure** sur le serveur | `phase2.sqlite` → `app_contact_current__sb`, redescendue chaque matin | **identique** : 62 281 · 32 655 · 261 · 17 978 · fraîche du 21/10 04:55 UTC |
| le filet « **connu de l'app seule** » *(26bis-CONTACTS, `bc359b6`, 21/09)* | `phase2/identite/contacts_app_seuls.py` → `app_contact_app_seul` | 15 lignes, toutes `absent_depuis` *(rejointes par le miroir)*. ⚠ ne copie que **5 champs**, **par choix écrit** : *« on OBSERVE ; injecter se décide champ par champ, lot L3 »* |
| le push **ne supprime jamais** un contact ≥ 10 M | `push_contacts_to_supabase.py:527-551` | |
| la **modification** écrit chez nous d'abord, 12 champs dont adresse et naissance | `app_edit_contact_optimistic` | |
| la **saisie en attente** jamais purgée, protégée la nuit | `app_contact_pending` | 0 ligne |
| le **cache de naissance** lu dans le formulaire Hektor | `hektor_contact_missing_detail`, dans la sauvegarde (`backup_critical.py:144`) | |

⚠ La **doublure** n'est pas dans la sauvegarde quotidienne de 09:00 ; elle n'est couverte que par
l'instantané de `phase2.sqlite` et par Veeam *(jamais restauré, G.3/G.4)* — c'est le sujet **8d**.

**Ce qui MANQUE — un seul endroit : la CRÉATION.** Les deux fonctions de création
(`app_create_contact_optimistic`, `app_create_mandant_contact_optimistic`) n'écrivent que
7 champs ; tout le reste arrive **par Hektor** (relecture ~40 s, naissance la nuit). Le jour de
la coupure, ce relais n'existe plus. Origine : la liste de la **ligne provisoire de C.9
(31/08)**, recopiée par L4-b (21/09) — **aucune décision ne l'a voulue**. Et 5 réglages
(forme juridique, métier, source, catégorie, CRM) n'ont **aucune** place chez nous, à la création
comme à la modification.

### Pourquoi on n'a pas « tout écrit chez nous d'abord » — *question de Frédéric, 21/10*

**Ce n'est pas propre au contact : TOUTES les créations font pareil** *(mesuré dans les
fonctions en base)* :

| création | ce qu'elle écrit chez nous tout de suite | le reste |
|---|---|---|
| contact / mandant | 7 champs dans `app_contact_current` | par Hektor, ~40 s |
| annonce | **11 champs sur 167** dans `app_dossier_current` | par Hektor, ~72 s |
| recherche | tous ses critères, mais dans `app_search_provisional` | |
| affaire | complète *(le registre des affaires)* | |

**C'est voulu, par deux décisions écrites** :
- **21/09** *(journal, l. 67)* : *« Pendant toute la migration, les commerciaux saisissent encore
  dans Hektor. […] Rien de ce qu'on construit ne doit inverser le courant aujourd'hui. »* → en
  étape 2, l'objet **naît** chez nous (numéro, visible tout de suite) et **Hektor fait foi pour
  le corps**.
- **13/10** *(journal, l. 154)* : on ne donne l'autorité à l'app que pour un champ **que l'app
  crée et que Hektor n'entretient pas** — sinon *« on promeut un affichage transitoire en
  autorité »*. *« Ce qui nous rendra prêts, c'est la coupure. D'ici là le carnet est le bon
  véhicule. »*

➡ Écrire **plus de champs** dans la ligne de naissance **ne contredit pas** ces décisions : c'est
de l'**affichage provisoire**, que la relecture de Hektor remplace 40 s plus tard par les mêmes
valeurs. Ce qui serait contraire, c'est de dire « l'app gagne » sur ces champs avant la coupure.

### « Je pensais que tous les champs étaient enregistrés chez nous tout de suite, puis réconciliés » — *Frédéric, 21/10*

**C'est vrai pour la SAISIE, pas pour la FICHE.** Mesuré :
- **toute la saisie est gardée chez nous à la seconde** — dans la **demande au worker**
  (`app_console_job.payload_json`), écrite **dans la même transaction** que la naissance de la
  fiche. Une création d'annonce y porte ~60 champs à plat + la boîte `hektor_wizard_fields` ;
  une création de contact, toutes les clés de `hContactPayload`. **Rien n'est effacé** : 99 496
  demandes conservées, la plus ancienne du 14/05 ;
- **la fiche**, elle, ne reçoit que 7 champs (contact) ou 11 (annonce) ;
- **la réconciliation** ne recopie PAS la demande dans la fiche : Hektor crée → on range son
  numéro → on **relit la fiche chez Hektor** et on la recopie chez nous. La fiche est complétée
  **depuis la copie de Hektor**, conformément aux décisions du 21/09 et du 13/10.

➡ À la coupure, rien de ce qui a été saisi n'est perdu — mais ce qui n'a pas été relu chez Hektor
reste **dans la demande**, pas **rangé dans la fiche**. ⚠ Audit limité au **contact** ; pour
l'**annonce**, seules la ligne de naissance (11 champs) et la forme de la demande sont mesurées.

### « On l'a corrigé dans les chantiers de l'audit du 07/10 » — *Frédéric, 21/10* — **NON, il a été RECLASSÉ**

- **07/10** : l'audit complet l'avait vu — liste, tâche **`L10-2` « CRÉER SANS HEKTOR »**
  (`LISTE_TACHES_A_COCHER_2026-08-29.md:2692`) : *« ANNONCE : 11 champs métier au cloud, le corps
  dans le payload du travail »* et *« une saisie ne se perd jamais doit couvrir les CRÉATIONS »*
  (`:45`). Lot **L10 « Préparer la coupure »**, plan l. 205.
- **08/10** : l'audit par objet l'a **reclassé en étape 3** — annotation sous L10-2 : *« PAS une
  anomalie de l'étape 2 : la fiche complète revient en ~1 min, 13 463/13 463 vivantes l'ont.
  Étape 3 (naître sans Hektor). »* Et §4 de l'audit : *« ce qui est étape 3, à ne pas compter en
  rouge »*.
- **Ce que les chantiers ont corrigé autour** : seulement le cas d'**échec** — chantier ④ (4a, 4c :
  une création qui rate se voit ; 4d : la purge à 24 h amendée et comptée). **Le corps de la
  création n'a été corrigé nulle part.** `L10-2` est toujours **`[ ]`**, L10 toujours **⬜**.
- Pour le contact, ce reste a atterri dans ⑧ sous la forme « 6 champs à la création » : **8a EST
  ce point-là.**

⚠ **Une incohérence de l'audit du 08/10** : pour l'**annonce**, il classe la création en étape 3
*parce que* la fiche revient en ~1 min ; pour le **contact**, il range « 6 champs à la création »
dans ⑧ (étape 2) — sans avoir vu que la fiche du contact revient, elle aussi, en ~40 s. Même
mécanisme, deux classements.

**Les doublures ne répondent pas à cette question** *(Frédéric : « à quoi servent les
doublures ? »)* : une doublure `__sb` est une **photocopie** de Supabase sur le serveur
(`pull_from_supabase.py`, tâche B.1 du 21/08 : *« tout ce que l'app a INVENTÉ n'existait qu'en
ligne, sans aucune copie »*). Elle protège contre la **perte du cloud** ; elle copie la fiche
**telle qu'elle est** — si la fiche n'a que 7 champs, la doublure en a 7. Elle ne remplit rien.

**La doublure des annonces est complète** *(mesuré le 21/10, `phase2.sqlite`, descente de
07:45)* : `app_dossier_current` 13 496 lignes, 74 colonnes · `app_dossier_detail_current`
13 496 lignes, **0** fiche de détail vide, 28,8 Ko en moyenne. Le matin, chaque annonce a reçu
sa fiche de Hektor depuis longtemps : la doublure n'est incomplète que pour une annonce **dont
Hektor n'a jamais renvoyé la fiche**. ⚠ Il n'y a **pas** de table `app_dossier_current__sb` : la
copie porte le **même nom** (`pull_from_supabase.py` ne suffixe que ce qui existe déjà en local).

**Pendant la minute d'attente** : la liste montre l'annonce avec ses 11 champs ; le reste
(description, pièces, surfaces, équipements) arrive avec la relecture, ~72 s *(24/09 : 10:21:20
→ 10:22:32)*. ⚠ **Non vérifié à l'écran** : ce que montre la fiche si on l'ouvre dans cette minute.

### Décision — 21/10

✅ **Frédéric : « A maintenant, mais audit encore avant de proposer une méthode ».** Le contact
(8a), puis l'annonce (L10-2d), puis le contrôle au retour (N.2) sont repris **dans ⑧**. L'audit
transversal vit dans **`notice/AUDIT_PORTES_DE_CREATION_2026-10-21.md`**. Méthode : *proposée,
pas encore validée*.

### Pièce 1 — le contact naît complet : audit du 21/10 *(Frédéric : « oui »)*

**Les deux portes, relues en base** :

| porte | empreinte | l'écran envoie (`api.ts`) | écrit aujourd'hui | en plus, avec une colonne qui existe |
|---|---|---|---|---|
| `app_create_contact_optimistic` | `f1563f57…` | `hContactPayload` (l. 9782) | nom, prénom, nom affiché, email, téléphone, négociateur, agence | **civilité, 2ᵉ téléphone, adresse, code postal, ville, naissance, lieu, situation, commentaire** |
| `app_create_mandant_contact_optimistic` | `e787461f…` *(corps en CRLF)* | `createHektorMandantContactJob` (l. 9996) : 8 clés | idem | **civilité, adresse, code postal, ville** |

**Vérifié** : les 9 colonnes sont toutes `text` · un seul déclencheur sur la table,
`app_contact_remplir_cible`, qui ne touche que `hektor_target_id` et seulement sous 10 M ·
11 vues lisent la table, colonnes nommées · droits : `authenticated` et `service_role`, pas
`anon` · aucun autre appelant que le front *(le worker ne les cite qu'en commentaire, l. 1463 et
18161)* · au retour, les **deux** gestes mettent une relecture du contact en file *(`:18300`,
`:19491`)* · formats saisis = formats en base *(civilité `M.` / `Mme.` ; situation `married`…)*.

⚠ **Deux pièges trouvés** :
1. **La date de naissance est un texte libre** `jj-mm-aaaa` *(App.tsx:38226, 38626, 40936)*,
   envoyé **sans conversion**. La base ne porte que de l'ISO *(261 sur 261)*. Recopiée telle
   quelle, elle serait ensuite **réinjectée** à chaque relecture *(champ propre à l'app)*.
   ➡ convertir `jj-mm-aaaa` en ISO, et **ne rien écrire** si la forme est inconnue.
   *(La modification a le même défaut, aujourd'hui sans victime : noté, hors pièce 1.)*
2. **La porte du mandant écrit le contact dans un bloc « best effort »** qui **avale toute
   erreur** : une valeur qui ferait échouer l'insertion ferait disparaître **tout** le contact
   chez nous, en silence. ➡ aucune conversion risquée dans ce bloc, que du texte.

**Usage** : 16 + 17 créations, aucune depuis le 21/09 ; un essai réel crée un vrai contact chez
Hektor.

### Pièce 1 — le code *(Frédéric : « A », avec interrupteur — 21/10)*

Trois fichiers, **rien n'est appliqué** :
- `supabase/patch_8a_contact_nait_complet_2026-10-21.sql` — interrupteur `contact_nait_complet`
  posé à `off` · fonction neuve `app_contact_champs_naissance(jsonb)` *(fermée à `anon` et
  `authenticated`)* · un bloc à part posé **après** l'insertion du contact dans les deux portes,
  par **ancre exacte**, seulement si l'empreinte est celle du 21/10 ;
- `…_INVERSE.sql` — retire le bloc et **n'écrit que si la fonction redonne exactement
  l'empreinte d'avant** ; retire la fonction neuve et l'interrupteur ;
- `…_REPETITION.sql` — **généré** depuis les deux autres
  *(scratchpad `gen_repetition_8a.py`)* : le vrai patch, un **vrai appel des deux portes** au nom
  du compte admin de Frédéric *(interrupteur éteint puis allumé)*, le vrai inverse, puis l'erreur
  volontaire.

**Éprouvé en LECTURE SEULE avant d'écrire** *(requêtes sur la base réelle, aucune écriture)* :
- les deux ancres apparaissent **1 fois** chacune ;
- empreintes **attendues après le patch** : contact **`95fde3280af1dff65ab45596f4b3bead`**,
  mandant **`04a25df1327d4b7b19413a757f861aeb`** ;
- **retirer le bloc redonne exactement** `f1563f57…` et `e787461f…` *(calculé)* ;
- la conversion de la date, sur 10 formes : `21-09-1978`, `21/09/1978`, `21.09.1978` →
  `1978-09-21` · ISO gardé · `1-9-1978`, `1978/21/09`, `32-01-1980`, `21-13-1980`, `abc` →
  **rien écrit**.

**Le message attendu de la répétition** :
```
ESSAI ANNULE -- 01 empreinte_contact_apres=95fde3280af1dff65ab45596f4b3bead | 02 empreinte_mandant_apres=04a25df1327d4b7b19413a757f861aeb | 03 interrupteur=off | 04 fonction_eteinte=NULL | 05 A_eteint_nom=ESSAI 8A | 06 A_eteint_champs_en_plus=0 | 07 B_allume_nom=ESSAI 8A | 08 B_allume_champs_en_plus=9 | 09 B_naissance=1978-09-21 | 10 C_mandant_champs_en_plus=4 | 11 C_mandant_lien=1 | 12 D_date_inconnue_ecrite=non | 13 empreinte_contact_retour=f1563f572a8f2b4ea985e5f111144b37 | 14 empreinte_mandant_retour=e787461fd5efed34663e93ba5c92fea6 | 15 fonction_retiree=oui | 16 interrupteur_retire=oui | 17 erreurs=aucune
```

✅ **LA RÉPÉTITION EST VERTE — 17 mesures sur 17, au caractère près** *(21/10, jouée par
l'outil SQL après que Frédéric a levé le garde-fou pour la conversation)* : le message reçu est
**identique** au message attendu ci-dessus. ⚠ **Non vérifié après coup** : le contrôle « tout est
annulé » *(lecture seule)* a été **refusé** par le blocage automatique de l'outil, puis toute
lecture SQL aussi. L'annulation reste garantie par Postgres *(l'erreur finale annule la
transaction entière, aucun COMMIT)* et l'inverse s'était déjà prouvé dans l'essai *(mesures 13 à
16)* — mais il faut le **relire**.
✅ **RELU après l'ajout de la permission par Frédéric** : les deux portes sont **à leur empreinte
d'avant** (`f1563f57…`, `e787461f…`), la fonction neuve et l'interrupteur **absents**, **0**
contact « ESSAI 8A », **0** travail, **0** lien d'essai. **La répétition n'a rien laissé.**

✅ **LE PATCH EST EN PRODUCTION — 21/10 à 15:34, interrupteur ÉTEINT** *(accord de Frédéric :
« Oui, applique le vrai patch avec l'interrupteur éteint »)*. Les 6 contrôles du patch sont
verts, et relus à part : contact **`95fde3280af1dff65ab45596f4b3bead`**, mandant
**`04a25df1327d4b7b19413a757f861aeb`** *(exactement les empreintes calculées d'avance)* ·
`contact_nait_complet = off` · la fonction neuve n'est exécutable que par `postgres` et
`service_role`. **Rien ne change pour les utilisateurs tant que l'interrupteur est éteint.**
➡ Restent : **allumer** l'interrupteur, puis **l'essai réel** *(il crée un vrai contact chez
Hektor)* — deux gestes, deux accords.

✅ **INTERRUPTEUR ALLUMÉ le 21/10 à 15:37** *(accord : « Oui vas y »)*.

✅ **L'ESSAI RÉEL, dans l'app, dans le Chrome de Frédéric — 21/10 à 15:44** : « Nouveau contact »,
type Propriétaire, sans annonce, sous le compte de formation `franck.gerphagnon@gmail.com`, avec
portable, fixe, adresse, code postal, ville, naissance `21-09-1978`, lieu, situation, note.
- contact **20000006**, travail `create_hektor_contact` `done` en **16 s**, Hektor a donné
  **605922** ;
- **dans notre base, à la seconde** : les **16 champs** sont là — `phone_secondary 0400000082`,
  `adresse`, `code_postal 42000`, `ville Saint-Étienne`, **`birth_date 1978-09-21`** *(convertie)*,
  `birth_place`, `marital_status married`, `commentaires` ✅.

⭐⭐ **ET L'ESSAI A PROUVÉ L'UTILITÉ DU CORRECTIF, PAR ACCIDENT** : la relecture qui suit la
création (`refresh_console_contact_data`, 15:44:39 → 15:45:00) a **échoué** — l'API de Hektor
répond **500** à l'authentification *(« Hektor OAuth authenticate failed after 4 attempts »,
déjà vu à 15:40 sur un autre contact, une réussite à 15:41 entre les deux)*. Et ce travail **n'est
pas rejoué** par le filet *(absent de `app_console_action_enqueue_due_retries`)*.
➡ **Sans 8a, ce contact n'aurait aujourd'hui que 7 champs**, jusqu'au run de la nuit.

⬜ **Non vérifié** : que la version de Hektor, quand elle redescendra, ne fasse rien perdre.
↳ **15:50, relecture relancée une fois** *(accord : « B »)*, travail `5319cac4…` copié sur celui
qui avait échoué : **même échec à 15:50:58** *(API Hektor toujours en 500 à l'authentification)*.
La fiche est **intacte** : les 16 champs, toujours. ⚠ **Si l'API de Hektor reste en panne, le run
de cette nuit en dépend aussi.**

⛔⛔ **15:04 — LA RELECTURE RELANCÉE A CRÉÉ UN DOUBLON, ET C'EST MA RELANCE QUI L'A FAIT ABOUTIR.**
- ⏱ **Ce n'est pas un bannissement** *(question de Frédéric)* : le premier `500` est de **15:40:06**,
  sur une fiche ouverte par quelqu'un, **avant** mon premier appel à Hektor *(15:44:23)* ; 7 travaux
  dans l'heure ; un bannissement répond `403` et bloque tout, or le témoin de **16:02** *(contact
  10650744)* est passé. *(Non mesuré : les appels à Hektor hors de la file de travail.)*
- 🔍 **La cause, dans le code du worker** : après une création, `handleCreateHektorContact` met la
  relecture en file avec **le numéro de Hektor** — `enqueueRefreshConsoleContactDataJobBestEffort(job,
  created.contactId, …)` (`console_job_worker.js:18226`) — alors que la relecture attend **notre**
  numéro *(commentaires `:4326` et `:4362` : « ce point d'entrée prend l'IDENTITÉ, pas la cible »)*.
  Le registre local ne connaissant pas encore la paire, le build a fabriqué une fiche **sous
  605922**. **Même défaut** dans la porte du mandant (`:19491`).
- 📅 **Le défaut dort depuis la bascule du 23/09** : avant, les deux numéros étaient égaux ;
  depuis, **aucune création** n'avait eu lieu *(dernière : 21/09)*. Ce matin, la relecture
  automatique avait échoué (panne Hektor) : **ma relance, copie exacte de sa demande**, l'a fait
  aboutir. **8a n'en est pas la cause** *(le doublon vient de la relecture, pas de la création)*,
  mais **c'est mon geste qui l'a déclenché**.
- 📏 **L'étendue, mesurée** : **1** fiche en trop dans Supabase (`605922`, `app_contact_id` vide,
  `birth_date` vide) · **1** dans la couche locale de `phase2.sqlite` · registre `app_contact`
  **intact** · **0** lien, **0** recherche, **0** saisie en attente. ⭐ La sentinelle l'a vu :
  `app_v_contacts_en_double_identite` = **1**.

✅ **DOUBLON SUPPRIMÉ — 21/10 à 16:1x** *(accord : « OUI SUPPRIME LE »)* : copie datée avant geste
`notice/SUPPRESSION_DOUBLON_605922_2026-10-21.json` · `605922` cherché dans les **25** tables qui
portent `hektor_contact_id` → **1 seule** ligne · supprimée dans Supabase *(1 ligne)* et dans la
couche locale de `phase2.sqlite` *(1 ligne, `busy_timeout` 60 s)* · relu : **0** doublon, la
sentinelle `app_v_contacts_en_double_identite` revenue à **0**, la bonne fiche **20000006** garde
**ses deux numéros** *(identité 20000006, cible Hektor 605922 — exigence de Frédéric)* et ses 16 champs.

⛔ **LE CORRECTIF « ÉVIDENT » SERAIT DANGEREUX** — donner l'identité à la relecture *(`:18225`,
`:19491`)* ne suffit pas : `cible_hektor()` (`phase2/sync/refresh_contact_inproc.py:31-60`) traduit
l'identité par la couche **LOCALE**, où un contact né il y a une minute **n'est pas encore**. Elle
rendrait alors l'identité telle quelle → **Hektor interrogé avec NOTRE numéro** → *« 404, puis
liste noire, et une fiche vide dans le miroir sous notre numéro »* (son propre commentaire).
➡ **La relecture d'après-création ne sait pas traiter un contact neuf, quel que soit le numéro
qu'on lui donne.** Le chemin prévu pour lui est la nuit : `descendre_correspondance_contacts.py`
redescend la paire, le build traduit, le push met à jour 20000006. **Décision à Frédéric.**

❓ **Frédéric : « il faut que l'on puisse modifier la fiche avant 24 h ; sans réconciliation ce
sera compliqué, non ? »** — **Oui, et ça change la recommandation.** Relu dans le code :
- **la modification elle-même part bien chez Hektor avant la nuit** : `cibleHektorContact`
  (`console_job_worker.js:2126`) lit le numéro Hektor dans **Supabase** (`hektor_target_id`), que
  le worker range **16 s** après la création ;
- **mais la relecture qui suit une modification** (`:18303`, avec l'identité) tombe dans le **même
  trou** : `cible_hektor()` traduit par la couche **locale**, qui ignore le contact neuf → Hektor
  interrogé avec **notre** numéro ;
- **UNE SEULE CAUSE RACINE** : le serveur n'apprend la paire « identité ↔ numéro Hektor » que la
  nuit (`descendre_correspondance_contacts.py`, run l. 670, qui refait **toute** la table
  `app_contact_identite_app` : DELETE + INSERT). Or le build **sait déjà** traduire avec cette table
  (`charger_identites_app`, `build_contacts_layer.py:364-433`) : **il ne lui manque que la paire.**

➡ **Proposition corrigée — « la relecture apprend la paire tout de suite »** *(pas encore codée,
audit à finir)* : au début de chaque relecture, si l'identité est à nous et inconnue en local,
**lire sa paire dans Supabase et l'écrire dans `app_contact_identite_app`** (une ligne,
`INSERT OR REPLACE`, comme la descente de nuit) ; `cible_hektor()` la lit aussi ; et le worker
passe **l'identité** après une création (`:18225`, `:19491`).

### Les trois derniers doutes, audités — 21/10 *(Frédéric : « audit les derniers doutes »)*

**① La descente de nuit et la ligne apprise en journée — LEVÉ.** `descendre_correspondance_contacts.py`
refait `app_contact_identite_app` depuis la vue `app_v_correspondance_identite_cible`, qui lit
**toutes** les fiches de Supabase ayant une cible ≠ identité ≥ 10 M *(62 282 lignes, **dont 20000006**)*
— pas seulement le périmètre éligible. La ligne apprise en journée y est **réécrite à l'identique**.
⭐ Et ce script **est né le 21/09 contre CE doublon** *(« ESSAI L4B », 10000001 / 605450)* : il ne
protège que la **nuit**. La relecture de **journée** n'a jamais été couverte.

**② L'envoi vers Supabase d'un contact né dans l'app — LEVÉ.** `delete_contacts_except_dirty`
**ne supprime jamais** une identité ≥ 10 M (`push_contacts_to_supabase.py`, `est_ne_dans_l_app`) :
la fiche est **fusionnée** ; `app_contact_id` et les 3 champs propres à l'app ne sont pas dans la
couche locale, donc **conservés**. ⭐ **Preuve par le doublon** *(qui était la version de Hektor)* :
sur 13 champs, **10 identiques** aux nôtres, **3 absents chez Hektor** (naissance, lieu, situation),
**0 différent**. ➡ **Le retour de Hektor ne fait rien perdre.** *(C'était le contrôle ⬜ ci-dessus.)*

**③ Les autres relectures — même chemin, même trou, même remède.** Toutes passent par
`phase2/sync/refresh_contact_inproc.py` : l'ouverture d'une fiche *(le front, avec l'identité)*,
après une modification (`:18303`), un ajout ou une modification de recherche (`:18504`, `:19299`,
`:19356`), un mandant (`:19715`) — **certaines avec le numéro Hektor**. Pour les 356 000 contacts
anciens, la paire est connue en local : **aucun risque**. Pour un contact **né le jour même**,
**toutes** tombent dans le trou.

➡ **LA SOLUTION, RESSERRÉE : un seul fichier, `refresh_contact_inproc.py`, et PAS le worker** *(donc
pas de redémarrage des 4 services : le script est relancé à chaque relecture)*. Au début :
quel que soit le numéro reçu, trouver la paire — en local d'abord, **sinon dans Supabase**
*(`hektor_contact_id = X` ou `hektor_target_id = X`)* — l'écrire dans `app_contact_identite_app`
*(une ligne)*, puis donner **le numéro Hektor** aux étapes détail/normalisation et **l'identité** au
build et au push. Si une identité ≥ 10 M n'a **pas** de numéro Hektor, ou si Supabase ne répond
pas : **la relecture s'arrête en erreur**, elle n'interroge jamais Hektor avec notre numéro.

### La correction de la relecture — CODÉE, ÉPROUVÉE HORS PRODUCTION, **PAS INSTALLÉE** *(21/10, « vas-y »)*

⚠ **Piège évité de justesse** : `refresh_contact_inproc.py` est **exécuté à chaque relecture** par le
worker — le modifier, c'est le mettre en service **sur-le-champ**. Ma première édition l'a été ~1 min
*(15:3x)* : **aucune relecture n'a tourné pendant ce temps** *(la dernière : 15:03:49)*. Le fichier en
service a été **remis à l'identique** (`git checkout`) ; la nouvelle version attend dans le scratchpad
(`refresh_contact_inproc_NOUVEAU.py`, 321 lignes).

**Ce qu'elle ajoute** *(avant les 4 étapes, rien d'autre ne change)* : `paire_connue_en_local()` →
sinon `demander_la_paire_a_supabase()` *(la vue de la descente de nuit, même contrôle de forme)* →
`ecrire_la_paire()` *(une ligne dans `app_contact_identite_app`)* → le build et le push reçoivent
**l'identité**, Hektor **son numéro**. Arrêt en erreur *(code 3)* si une identité à nous n'a pas de
numéro Hektor ou si Supabase ne répond pas, **et** une dernière barrière dans `_steps()`.

**Banc d'essai hors production** *(base fabriquée + lecture seule de Supabase)* — **13 sur 13** :
contact ancien par identité et par numéro Hektor → **chemin d'avant, aucune paire écrite** · contact
neuf par **notre** numéro → paire apprise, Hektor visé par 605922, fiche par 20000006 · **le cas du
doublon** *(reçu avec 605922)* → on rend **20000006** · identité sans numéro Hektor → **arrêt** ·
numéro Hektor inconnu partout → chemin d'avant · Supabase muet → **arrêt** · dernière barrière →
**arrêt**.
**Témoin inverse** : l'**ancienne** version, mêmes cas → reçue avec `20000006` elle interroge Hektor
avec **20000006** ; avec `605922` elle construit **605922** *(le doublon)*. Le banc sait voir le défaut.
**Sur la vraie base, lecture seule** : 3 à 10 ms ; les contacts anciens (10650744, 414472) **connus en
local** → **aucun appel à Supabase** pour eux.

**Pensé à tout** *(demande de Frédéric)* : les **doublures** (`__sb`) ne sont pas touchées · la
**descente** de 07:45 ne copie pas cette table · la **descente de correspondance** du run *(l. 670)* la
réécrit à l'identique · le **run** n'utilise pas ce script *(il appelle le build directement)* · le
**registre des liens** (`relation_ledger.py`) lit la même table : une paire juste ne peut que l'aider ·
le **worker** et le **front** ne changent pas, **pas de redémarrage** · la **sauvegarde** ne porte pas
cette table *(elle se reconstruit chaque nuit)* · ⚠ pendant un verrou long du run sur
`phase2.sqlite`, l'écriture de la paire peut échouer → la relecture finit **en erreur, sans appeler
Hektor**.

✅ **INSTALLÉE le 21/10 à 16:40** *(accord : « Oui »)* — `phase2/sync/refresh_contact_inproc.py`,
identique octet pour octet à la version éprouvée. **Essai réel** sur le contact d'essai :

| relecture | résultat |
|---|---|
| **avec notre numéro** `20000006` *(16:40:46 → 16:41:05, `done`)* | paire **apprise** *(`605922 → 20000006`, 14:40:47Z)* · la fiche **20000006 mise à jour par Hektor** *(`has_contact_detail` vrai, typologie `mandant` arrivée)* · `app_contact_id`, **naissance, lieu, situation conservés** · **0 doublon**, sentinelle **0** ✅ |
| **avec le numéro Hektor** `605922` *(16:41:46 → 16:42:01, `done`)* | **0 doublon**, sentinelle **0** ✅ · ⚠ mais la fiche **n'est pas mise à jour** *(push : 0 ligne)* : la paire étant connue en local, la relecture suit **le chemin d'avant, tel quel** — et ce chemin, reçu avec un numéro Hektor, ne met pas la fiche à jour. **C'est déjà le cas aujourd'hui pour les contacts anciens** *(5 appelants du worker passent le numéro Hektor : `:15841`, `:18504`, `:19299`, `:19356`, `:19715`)*. **Hors de la pièce 1, non corrigé — question à Frédéric.** |

✅ **CONTACT D'ESSAI SUPPRIMÉ — 16:43:29 → 16:43:47** *(accord : « Oui »)* par
`app_console_create_delete_contact_job` *(la fonction du bouton « Supprimer »)* : chez Hektor
*(605922)*, dans le miroir *(`hektor_contact`, `raw_api_response`, `sync_contact_state`)*, dans la
couche locale et dans Supabase · **1** ligne au journal des suppressions · **0** fiche restante ·
sentinelle **0**. Reste la paire apprise dans `app_contact_identite_app` : la descente de cette nuit
la retirera *(elle refait la table depuis la vue, où le contact n'est plus)*.

### Les relectures reçues avec le numéro Hektor — audit du 21/10 *(Frédéric : « A »)*

- **Les 5 appelants donnent le numéro Hektor** *(`contactId` = résultat de `cibleHektorContact`)* :
  `:15841` qualification d'acquéreur archivée *(`cibleArchive`)* · `:18504` ajout de recherche ·
  `:19299` modification de recherche · `:19356` suppression de recherche · `:19715` modification d'un
  mandant. **Notre numéro est disponible dans chacun** *(`identite`)*.
- **Mesuré depuis la bascule (24/09)** : **1** vraie relecture reçue avec un numéro Hektor — après la
  modification d'un mandant, le **08/10 à 11:06** *(605030)* → **0 ligne écrite**. Les **70**
  relectures de l'ouverture d'une fiche *(le front donne l'identité)* → **1 ligne chacune**.
- **Le mécanisme** : reçue avec un numéro Hektor dont la paire est connue, la relecture lit bien
  Hektor et reconstruit la fiche **sous notre numéro** *(le build traduit)*, mais **envoie sous le
  numéro Hektor** → le push ne trouve rien à envoyer. **La fiche dans l'app reste à l'ancienne
  version** jusqu'au run de la nuit. Rien n'est perdu ni abîmé : c'est **un rafraîchissement perdu**.
- **Ce n'était pas une décision** : le commentaire `:4326` (C-12, 23/09) l'avait vu — *« Les deux
  appelants lui passaient encore la cible : invisible tant que les deux numéros sont égaux, faux le
  jour de la bascule »* — et n'avait corrigé que deux appelants.

➡ **Correctif proposé (A, recommandé) — dans le même fichier, pas dans le worker** :
`resoudre_le_numero()` rend **l'identité** quand elle reçoit un numéro Hektor dont la paire est
connue en local. La relecture suit alors **exactement le chemin de l'ouverture d'une fiche**
*(70 réussites mesurées)*. Pas de redémarrage. **Alternative (B)** : corriger les 5 appelants du
worker *(5 lignes, redémarrage des 4 services)*.

### 8a bis — le rafraîchissement perdu : CODÉ, ÉPROUVÉ, PAS INSTALLÉ *(21/10, « vas-y »)*

**Explication retenue par Frédéric** : *« la relecture échoue parce qu'on donne le numéro Hektor à
l'app qui ne le retrouve pas »* — exactement : les étapes 1-2 *(Hektor)* ont besoin de **605922**, le
build traduit seul, mais **le push reçoit 605922** alors que la fiche préparée porte **20000006** →
il ne trouve rien et n'envoie rien. **Uniquement les contacts** : la relecture d'annonce retrouve
elle-même notre numéro *(551 / 551)*, les annonces ayant deux numéros depuis toujours.

**Le code** *(copie `refresh_contact_inproc_V2.py` du scratchpad, PAS en service)* :
`identite_connue_en_local()` — le registre `app_contact` ou `app_contact_identite_app` donnent
l'identité d'un numéro Hektor ; **une identité ambiguë n'est pas choisie** *(chemin d'avant)* ;
`resoudre_le_numero()` la rend quand la paire est connue.

**Éprouvé** : banc élargi *(il prend désormais le fichier à tester en argument)* — **copie : 17 / 17** ·
**version en service : 13 / 17**, échoue **exactement** sur les 4 nouveaux contrôles *(témoin
inverse)*. **Vraie base, lecture seule** : `414472 → 10215521` *(la paire vérifiée le 02/10)* ·
`605030 → 10355712` *(le « TEST MANDANT » du 08/10)* · 3 à 16 ms.

✅ **8a bis INSTALLÉ le 21/10 à 18:43** *(accord : « Oui créer même un nouveau contact pour être
sûr »)* — banc **17 / 17 sur le fichier en service**. **Trois essais réels, tous verts** :

| essai | numéro reçu | résultat |
|---|---|---|
| le cas du 08/10 *(« TEST MANDANT », 18:43:58 → 18:44:23)* | `605030` | le build reçoit **10355712** · **1 ligne écrite** *(0 le 08/10)* · 0 doublon |
| **un contact NEUF créé dans l'app** *(« ESSAI 8A BIS », 18:47)* | — | **20000007**, ses **9 champs à la seconde**, naissance `03-05-1982` → **`1982-05-03`** · Hektor : **605925** *(`done` 18:48:09)* |
| ↳ sa relecture **automatique** *(18:48:08 → 18:48:49)* | `605925` *(le worker)* | **paire apprise** · **1 ligne écrite** · typologie `mandant` · naissance, lieu, situation, note **conservés** · **0 doublon** — *le chemin qui avait fabriqué le doublon ce matin* |
| ↳ une relecture, paire **déjà connue** *(18:49:52)* | `605925` | **1 ligne écrite** · 0 doublon · sentinelle **0** |

⬜ Le contact d'essai **20000007 / 605925** existe encore — sa suppression attend l'accord.

---

## Pièce 2 — L'ANNONCE NAÎT COMPLÈTE *(L10-2d)* — audit du 21/10

**Ce que l'écran envoie** (`createHektorDraftAnnonceJob`, `api.ts:10980-11081`) : **~60 champs à
plat** sous les noms de l'app en `snake_case` *(adresse, prix, net vendeur, surfaces, pièces,
chambres, niveaux, salles d'eau, WC, cuisine, exposition, vue, états, terrain, jardin, terrasses,
garages, parkings, piscine, année, DPE, GES, copropriété ×4, description, note)* **+**
`hektor_wizard_fields` *(les équipements, sous les noms de **Hektor**, filtrés par type de bien —
`App.tsx:16068`)* **+** `composition_pieces` **+** les mandants *(existant ou nouveau)*.

**Ce qui est écrit chez nous au clic** (`app_create_annonce_job_optimistic`, interrupteur
`c9_annonce_nait_dans_app` allumé) : **11 colonnes** de `app_dossier_current` *(titre, prix,
ville, code postal, statut, négociateur, agence…)* — et **aucune ligne** dans
`app_dossier_detail_current`. Tout le reste ne vit que dans la demande au worker, **qui n'est pas
un lieu sûr** *(nettoyages des 21/08 et 15/10)*.

**Le retour de Hektor — il marche, et depuis le 24/09** : `push_single_annonce_to_supabase.py`
**adopte le numéro de l'app** avant d'en fabriquer un *(« C.9-e (e1) », l. 188-247, avec la
fonction de `descendre_correspondance_annonces`)* — **l'équivalent exact** du correctif contact
d'aujourd'hui. Preuve : l'annonce d'essai `10000000 / 63147` du 24/09 a **une seule** fiche et son
détail complet *(15 534 car.)*. Toutes les relectures d'annonce depuis le 24/09 écrivent *(551 / 551)*.

**Trois vocabulaires pour les mêmes champs** ⚠ *(le piège de N.1, 28/09)* : la création parle
`snake_case` de l'app (`bedroom_count`), la modification `camelCase` (`bedroomCount`) **et** les
noms de Hektor (`NB_CHAMBRES`), le calque d'affichage **les noms de Hektor**. La traduction existe
**en morceaux** : `col_map` / `json_map` de `app_edit_annonce_optimistic` *(~20 clés, recopiées à
l'identique dans `app_annonce_reappliquer_saisies`)*, les alias du worker
(`HEKTOR_CLEANFIELD_ALIASES`), et la correspondance des 189 champs (`correspondance_champs_annonce.py`,
qui **imprime** sans rien écrire).

**Usage** : 79 créations d'annonce au total, **2 depuis le 24/09** *(des essais)*.

**Non vérifié** : ce que **montre la fiche** d'une annonce ouverte avant le retour de Hektor
*(aucune ligne de détail)*.

### Pièce 2 — le dernier audit avant de proposer *(Frédéric : « doublure, descente, etc. »)*

**Tout ce qui touche la fiche détaillée** (`app_dossier_detail_current`), recensé dans le code et en
base, et ce que deviendrait une **fiche de départ posée au clic** :

| qui | ce qu'il fait | avec une fiche de départ |
|---|---|---|
| **la relecture** (`push_single_annonce_to_supabase.py`) | adopte notre numéro *(C.9-e)*, puis **remplace** la fiche par celle de Hektor *(upsert)*, puis repose les saisies en attente *(L3)* | ✅ Hektor confirme, comme aujourd'hui ; le calque disparaît |
| **le run de nuit** (`push_upgrade_to_supabase.py`) | efface les fiches « disparues »… **sauf** une annonce née dans l'app que le serveur ne connaît pas encore *(C.9-c, `separer_annonces_app_en_attente`, l. 1075)* | ✅ **épargnée** si Hektor n'a jamais répondu ; remplacée par celle de Hektor sinon |
| **la descente de 07:45** (`pull_from_supabase.py`) | copie la table entière sur le serveur *(370 Mo)* | ✅ la fiche de départ est copiée — **elle a sa doublure** |
| **la sauvegarde** | `app_dossier` *(l'identité)* est sauvegardé ; la table descendue l'est par l'instantané | ✅ inchangé |
| **la modification** (`app_edit_annonce_optimistic`) | écrit le calque par un **UPDATE** de la ligne | ✅ **mieux qu'aujourd'hui** : la ligne existe, le calque se pose *(aujourd'hui, avant le retour de Hektor, il ne se pose sur rien)* |
| **la sentinelle** `data.annonce_sans_numero_hektor` *(seuil 0)* | compte les fiches **et** les détails sans numéro Hektor | ⚠ compte **déjà** la ligne de 11 champs pendant la minute d'attente ; en compterait **deux** — et **crie si Hektor ne répond jamais** *(voulu)*. Son commentaire *« rien ne doit en produire avant la tâche 22 »* est **périmé** depuis l'allumage de C.9 (25/09) |
| **les rapprochements** (`app_dossier_match_payload`, `app_dossier_match_attrs`, `app_get_rapprochements`) | ne lisent que les biens **Actifs ET diffusables** | ✅ une annonce neuve n'est pas diffusable : **non concernée** |
| **la vitrine publique**, les **mails aux acquéreurs** (`rapprochement_email.py`) | biens diffusables seulement | ✅ non concernés |
| **les RDV publics** (`appointment_service.py`) | lisent par numéro Hektor | ✅ non concernés tant qu'il n'y en a pas |
| **l'espace client** (`espace_client.py`) | lit la fiche par notre numéro | ✅ verrait la saisie au lieu de rien |
| **les équipements, les photos** (`app_dossier_equipements`, `app_get_dossier_photos`) | lisent des clés de la fiche | ⚠ **à vérifier** : une fiche de départ doit porter les clés qu'ils attendent, ou rien |
| **l'écran** (vue `app_dossier_details_current`) | lit **le calque en premier**, sous les noms de Hektor *(`App.tsx:2557-2645`)* | ⚠ **à vérifier en réel** |

### Pièce 2 — l'annonce d'essai, en réel *(21/10 à 20:12, Firminy — choix de Frédéric)*

Créée par l'écran **Estimations → Nouvelle estimation → Manuellement** *(statut Estimation, non
diffusée)* ; agence « Groupe GTI Firminy », dont le **seul** négociateur proposé est **Emmanuelle
PEREIRA** *(le compte de formation n'a pas d'agence dans la liste)*. Titre « ESSAI 8A ANNONCE - ne
pas diffuser », 17 champs dont 7 techniques.

| moment | ce qu'on voit |
|---|---|
| **20:12:55, le clic** | fiche **10000001** née chez nous, **11 champs**, **aucune fiche détaillée** |
| **pendant l'attente** | ⚠ **l'estimation N'APPARAÎT PAS dans la liste** *(recherche « ESSAI 8A » → « 0 estimations »)* ; seule une fenêtre « Suivi de l'action — Création » *(Hektor ● / App ○)* |
| **20:13:55** *(60 s)* | Hektor l'a créée : **63329** |
| **20:14:24** *(89 s)* | la relecture a écrit la fiche détaillée *(18 277 car.)*, **une seule fiche** ; l'estimation **apparaît** dans la liste, la fenêtre dit « Annonce disponible » |

**Ce que Hektor a renvoyé, comparé à la saisie** *(un premier contrôle « N.2 », à la main)* :
surface **85**, pièces **4**, chambres **3**, salle de bain **1**, cave **OUI**, balcon **OUI**,
ascenseur **OUI**, année **1975**, DPE **180**, GES **30**, code postal **42700**, ville **Firminy**
— **tout est retenu**. ⚠⚠ **SAUF L'ADRESSE** : saisie *« 3 rue de l'Essai »*, renvoyée **« 3 Rue de
l'Ondaine »** — Hektor a **remplacé** une rue inconnue par une vraie rue de Firminy. **C'est
exactement le genre d'écart que le contrôle au retour (pièce 3) devra noter.**

**Ce que ça dit pour la pièce 2** : ⭐ aujourd'hui, pendant ~90 s, **l'annonce n'existe pas à
l'écran** — ni fiche, ni ligne dans la liste. Une fiche complète dès le clic la ferait **apparaître
tout de suite**. *(Non vérifié : pourquoi la liste l'écarte — un filtre de la liste sur une donnée
que seule la fiche détaillée porte ? à lire avant de coder.)*

⬜ **Non essayé** : modifier l'annonce pendant la minute d'attente *(le point 3)*.
⬜ **L'annonce d'essai 10000001 / 63329 existe encore** — sa suppression attend l'accord.

⚠ **Un point à part, trouvé en passant** : une modification faite **avant** le retour de Hektor
garde `hektor_annonce_id` **vide** dans sa saisie en attente, et le balayeur l'envoie telle quelle
(`app_annonce_enqueue_due_pushes`). **Non vérifié** : si le worker retrouve le numéro par
`app_dossier_id`.

⚠ **Trouvaille HORS SUJET, notée** : dans `app_console_job.error_message`, la **première** trace
de l'échec d'authentification de 15:40 porte **le secret OAuth de Hektor EN CLAIR** dans l'URL
*(la ligne `raise_for_status`)* ; seul le message final le masque (`***`). À traiter à part.

⛔ **Je ne colle pas moi-même** *(Frédéric a proposé le 21/10 que je passe par son Chrome)* : la
règle du chantier interdit d'écrire en production, **même dans une transaction annulée**, et
passer par le navigateur la contournerait.

*(ancienne formulation, gardée : A = la création et la modification écrivent elles-mêmes tout ce qui a
une colonne · A+ = A, plus une place pour les champs que Hektor ne renvoie jamais, et la reprise
des charges déjà envoyées)*

### Pièce 2 — le code *(Frédéric : « garde et code pièce 2 » — 21/10)* — ÉCRIT, **PAS APPLIQUÉ**

Trois fichiers, tous en `LF`, la répétition **générée** depuis les deux autres
*(`gen_repetition_8a2.py`, dans le brouillon de la session ; il vérifie que le bloc est
identique, à l'octet, dans le patch et dans l'inverse)* :
`supabase/patch_8a2_annonce_nait_complete_2026-10-21.sql` · `…_INVERSE.sql` · `…_REPETITION.sql`.

**Ce que fait le patch** — additif, derrière l'interrupteur **`annonce_nait_complete`, posé ÉTEINT** :
1. une fonction **neuve**, `app_annonce_corps_de_naissance(jsonb)`, fermée à `anon` et
   `authenticated` *(la création est `SECURITY DEFINER` : elle l'appelle quand même — vérifié)* ;
   elle rend `NULL` si l'interrupteur est éteint ;
2. dans `app_create_annonce_job_optimistic`, **juste après** l'insertion de la fiche *(branche C.9,
   la seule active : `c9_annonce_nait_dans_app = on`)*, un bloc **à part** *(son échec ne peut ni
   empêcher ni défaire la création)* qui :
   - complète la fiche : **`search_text`**, **`date_enregistrement_annonce`** *(heure de Paris,
     seulement si vide)*, **`type_bien` en CODE** *(`hektor_id_type`, jamais le libellé)*, l'adresse,
     le code postal et la ville **privés** ;
   - pose une **fiche détaillée de départ** : surface, pièces, chambres, la date, le **calque**
     `app_optimistic_overlay` *(les équipements, déjà aux noms de Hektor, + titre, corps, prix, net
     vendeur, surface, pièces, chambres, adresse, codes et villes)* — c'est ce que l'écran lit
     **en premier** *(`wizardDetailValue`)* — et la **saisie telle quelle** `app_saisie_creation`,
     **sans le mandant** *(ses coordonnées vivent dans les contacts)*.
   - ⛔ **N'invente pas** ce que seul Hektor fabrique : numéro Hektor, numéro de dossier,
     diffusable, blocs `equipements_json` / `ag_*_json` / photos.

**Gardes** : empreinte de la création **`3407a05c…`** *(mesurée le 21/10)*, ancre trouvée **1 fois**,
marque absente — sinon ARRÊT. L'inverse ne réécrit que si, bloc retiré, il redonne **exactement**
`3407a05c…`.

**Contrôlé en lecture seule, le 21/10** :
- empreinte d'après attendue **`a5e70b57…`**, et le retour redonne **`3407a05c…`** ✅ ;
- ⭐⭐ **le texte de recherche calculé sur la VRAIE saisie de l'essai 10000001 est IDENTIQUE, au
  caractère près, à celui que le serveur a écrit 90 s plus tard** *(« ESSAI 8A ANNONCE - ne pas
  diffuser Firminy 42700 Emmanuelle PEREIRA Groupe GTI »)* ; le type aussi (`2`) ;
- la relecture **remplace** bien la fiche détaillée : `push_single_annonce_to_supabase.py` l'efface
  puis l'insère **par `app_dossier_id`** *(l. 391-410, 669)* — la nôtre ne peut pas la bloquer ;
- **les 6 lecteurs** de la fiche détaillée en base : `app_edit_annonce_optimistic` et
  `app_annonce_reappliquer_saisies` **trouvent désormais une ligne à mettre à jour** *(avant : 0
  ligne, la modification de la première minute ne s'y voyait pas — c'est un MIEUX)* ;
  `app_dossier_match_payload` lit `surface` / `nb_pieces` / `nb_chambres` *(les clés posées)* ;
  `app_dossier_equipements` lit les blocs que nous **ne** fabriquons **pas** → rend vide, comme
  avant ; `app_get_dossier_photos`, `app_get_rapprochements` : rien de changé.

**La répétition** *(jamais validée, finit par « ESSAI ANNULE -- … »)* : le vrai patch, un vrai appel
au nom de l'admin Frédéric, éteint **puis** allumé, puis le vrai inverse. 22 mesures, dont : la saisie
du **mandant ne doit PAS** être recopiée, une valeur **vide** et un **objet** dans les équipements ne
doivent **pas** entrer dans le calque, et le rapprochement doit lire les pièces. ⚠ Elle consomme
**2 numéros d'annonce de l'app** *(un trou dans la série)*.

⬜ **À faire, chacun avec son accord** : jouer la répétition → appliquer le patch (éteint) → allumer
→ un essai réel *(une nouvelle estimation à Firminy)*.

### Pièce 2 — la répétition : **22 VERTES SUR 22** *(21/10, 22:22, jouée par moi avec l'accord de Frédéric : « Oui »)*

`ESSAI ANNULE -- 01 empreinte_apres=a5e70b57… (= l'attendue) | 02 interrupteur=off | 03 fonction_eteinte=NULL |
04 A_eteint_fiche_detaillee=0 | 05 A_eteint_texte_recherche=NULL | 06 A_eteint_type_date=NULL / NULL |
07 B_allume_fiche_detaillee=1 | 08 B_texte_recherche=ESSAI 8A2 - ne pas diffuser Firminy 42700 Emmanuelle PEREIRA Groupe GTI |
09 B_type_et_date=2 / 2026-10-21 22:22:52 | 10 B_adresse_cp_ville=3 rue de l'Essai / 42700 / Firminy | 11 B_empreinte_source=c9e3: |
12 B_calque_nb_champs=18 | 13 B_calque_titre_et_cave=ESSAI 8A2 - ne pas diffuser / OUI | 14 B_calque_vide_et_objet=absent / absent |
15 B_mandant_dans_la_saisie=absent | 16 B_surface_pieces_chambres=85 m2 / 4 p / 3 ch | 17 B_rapprochement_nb_pieces=4 |
18 empreinte_retour=3407a05c… | 19 fonction_retiree=oui | 20 interrupteur_retire=oui | 21 droits_creation=inchanges | 22 erreurs=aucune`

- ⭐ **Le témoin inverse est là** : éteint (A), **0** fiche détaillée, pas de texte de recherche, ni type
  ni date — exactement le défaut d'aujourd'hui ; allumé (B), tout apparaît.
- 18 champs dans le calque = **6 équipements** (le vide et l'objet écartés) **+ 12 principaux** : le compte juste.
- L'heure est celle de **Paris** (22:22 pour un essai joué à 22:22).
- **Après coup, mesuré à part** : empreinte revenue à `3407a05c…`, fonction et interrupteur absents,
  **0** fiche et **0** travail « ESSAI 8A2 » en base. La séquence est passée de 10000001 à
  **10000003** : les 2 numéros annoncés, un trou, rien de plus.

⬜ **Reste, avec accord** : appliquer le patch (interrupteur **éteint**) → allumer → essai réel.

### Pièce 2 — patch APPLIQUÉ, interrupteur ÉTEINT *(21/10, Frédéric : « oui »)*

`patch_8a2` collé par moi : **5 contrôles verts** — interrupteur posé `off`, empreinte de la création
**`a5e70b57`** (= celle de la répétition), la fonction neuve rend `NULL`, droits inchangés, fonction
fermée à `anon` / `authenticated`. **Rien ne change pour les négociateurs tant qu'il est éteint.**

### Pièce 2 bis — TOUS LES CHAMPS *(Frédéric, 21/10 : « il faut vraiment tester tous les champs, pas juste 16 »)*

**La liste complète** : la fiche de l'annonce affiche **173 champs distincts** *(`draftAnnonceWizardGroups`,
App.tsx:1414-1696 ; 195 avec les doublons d'étape)*. Chacun est lu **calque d'abord, par son nom Hektor**
*(`wizardDetailValue`, App.tsx:2631)*. ⚠ J'avais d'abord dit 165 : **faux**, recompté sur le code.

**Ce que la liste a trouvé dans la version 1** *(posée éteinte, donc personne n'en a souffert)* :
1. **27 champs « à plat »** de la saisie *(salles de bain, WC, Carrez, séjour, cuisine, états, DPE, GES,
   copropriété ×3, charges, parkings ×2, terrasse, garage ×2, niveaux, jardin, piscine, exposition, vue,
   année…)* partent bien chez Hektor — le worker leur donne leur nom Hektor
   *(`buildWizardStep2/4/6/7Body`, console_job_worker.js:10669-10862)* — **mais le calque ne les
   reprenait pas** : la fiche les aurait montrés **vides** pendant ~90 s ;
2. **la surface du séjour** servait de repli à la surface **habitable** : faux, le worker l'envoie dans
   `SURF_SEJOUR` ;
3. **l'ordre** : le worker applique les équipements **en dernier** à chaque étape
   (`applyExactHektorWizardFields`, appelé à la fin de chaque étape), ils **gagnent** — la v1 faisait
   l'inverse.

**La version 2** *(`supabase/patch_8a2b_annonce_tous_les_champs_2026-10-21.sql` + `_INVERSE` + `_REPETITION`)*
ne remplace **que** `app_annonce_corps_de_naissance` *(garde : empreinte v1 `2e33944a`)* : une table de
correspondance **copiée du worker** (38 noms Hektor ← leurs clés), les équipements qui gagnent, et 19
noms « à plat » que les **autres** écrans lisent *(en-tête, listes, rapprochement)*. La création n'est
**pas** retouchée.

**La répétition** *(jouée par moi, tout annulé ; ⚠ la 1re passe avait perdu T6 : mon test écrivait ses
résultats DANS le bloc qui s'annule — corrigé, T6 rejoué seul)* :

| essai | résultat |
|---|---|
| T1 — chacun des **173 champs** de la fiche, avec SA valeur | ✅ **173 sur 173**, aucun échec |
| T2 — les **38** noms Hektor nourris par les champs à plat | ✅ **38 sur 38** |
| T3 — un équipement gagne sur le champ à plat | ✅ `w001` attendu `w001` |
| T4 — le séjour seul ne remplit plus l'habitable | ✅ vide |
| T5 — les **19** noms à plat des autres écrans | ✅ **19 sur 19** ; négociateur, agence, statut posés |
| mandant et jeton recopiés ? | ✅ **absents** ; note et composition **gardées** |
| T6 — **vraie création** au nom de l'admin : la fiche posée en base | ✅ **173 sur 173** ; le travail du worker porte **la saisie intacte** ; recherche + type posés |
| retour arrière | ✅ version 1 retrouvée (`2e33944a`), création non retouchée (`a5e70b57`) |

Empreinte de la v2 : **`944db16b`** *(figée dans le contrôle n° 1 du patch)*. Vérifié à part après coup :
fonction toujours en v1, interrupteur `off`, **0** fiche et **0** travail d'essai. Séquence passée à
**10000005** *(2 numéros de plus, un trou)*.

⬜ **Reste, avec accord** : appliquer la v2 → allumer → essai réel chez Hektor.
⬜ **Ce que je ne fais PAS à la naissance, volontairement** : `NO_DOSSIER`, `diffusable`, latitude /
longitude — seul Hektor les fabrique ; si l'écran les saisit, ils restent dans le calque tels quels.

### Pièce 2 bis — version 2 APPLIQUÉE, interrupteur ÉTEINT *(21/10, Frédéric : « oui »)*

Collée par moi : **5 contrôles verts** — empreinte **`944db16b`** (= celle de la répétition),
interrupteur **inchangé (`off`)**, la fonction rend `NULL` tant qu'il est éteint, la création **non
retouchée** (`a5e70b57`), la fonction reste fermée à `anon` / `authenticated`.
Retour arrière : `…_8a2b_…_INVERSE.sql` (revient à la v1), puis `…_8a2_…_INVERSE.sql` (retire tout).

⬜ **Reste, avec accord** : allumer → essai réel chez Hektor, **champ par champ**.

### Pièce 2 — L'ESSAI RÉEL PAR L'ÉCRAN, tous les champs *(21/10, 23:47-23:5x, Frédéric : « A, et cela permet de voir les champs manquants »)*

**Interrupteur `annonce_nait_complete` ALLUMÉ à 23:47:29** (heure de Paris), avec l'accord de Frédéric.

**Le geste** : dans son Chrome, « + Nouveau » → la création en 7 étapes, une **maison** à Firminy
*(Emmanuelle PEREIRA, Groupe GTI Firminy)*, **chaque champ que l'écran propose rempli** — l'écran a dit
**« 151 champs remplis »**. ⚠ Ouverte depuis l'accueil, la création se faisait en **Actif** ; je suis passé
sur l'écran Estimations, la saisie intacte, et elle est partie en **Estimation** comme annoncé
*(App.tsx:13510 : le statut dépend de l'écran d'où l'on crée)*.

| mesure | résultat |
|---|---|
| **1,3 s** après le clic | l'annonce **10000006** existe : type **1** (maison), recherche, date, adresse, **fiche détaillée de 116 champs** |
| ce que l'écran a envoyé au worker | **116 champs non vides** dans les équipements + les champs du haut + la pièce (avec ses 3 notes) + la note |
| **gardés chez nous à la naissance** | ✅ **116 sur 116**, zéro écart de valeur |
| la LISTE, avant le retour de Hektor | ⭐ l'estimation est **EN TÊTE** (Maison · Firminy · 187 000 € · PEREIRA) — au 1er essai, invisible 90 s |
| la FICHE, avant le retour de Hektor | ⭐ ouverte, titre / adresse / prix / **1 670 €/m²** ; rubriques remplies : Intérieur 8/9, Construction récente 7/7, Confort 19/22, Diagnostics 29/35, Disponibilité 5/5, Localisation 10/10… |
| Hektor a créé | **63330** à 21:54:34 UTC — **2 min 20 s** *(contre 60 s au 1er essai, moins de champs)* |

**Les champs que l'écran n'a PAS envoyés** *(sur les 173 que la fiche sait afficher)* — et pourquoi :
- **propres à l'appartement**, masqués pour une maison *(le filtre par profil)* : étage, dernier étage,
  balcon ×3, résidence ×2, ascenseur, gardien, syndic, copropriété ×8, diagnostic loi Carrez ×3 ;
- **propres au terrain** : constructible, surface constructible, viabilisé, raccordements ×4 ;
- **piscine** ×8 : masqués parce que piscine = NON ;
- **honoraires vendeur** ×3 : masqués parce que honoraires vendeur = NON ;
- **location** : taxe d'habitation, loyer estimé, charges locatives, rendement, occupation ;
- **fabriqués par Hektor** : numéro de dossier, date de création, diffusable ;
- `immeuble`, `clearing`, `cable`, `floorState` : **non proposés** à la création pour une maison
  *(à vérifier un par un : lesquels l'écran ne montre JAMAIS)* ;
- ⚠ **le chauffage** (format, type, énergie) : **rempli à l'écran mais PAS envoyé** — j'avais choisi les
  valeurs **par défaut** (4 / 9 / 14), et l'écran ne retient un champ que s'il CHANGE. Pas une perte
  (l'écran et Hektor retombent sur le même défaut), mais **ces 3 champs ne sont PAS éprouvés** par l'essai.
- `masque` (masquer le prix) : laissé vide **par moi**.

⚠⚠ **Trouvaille de l'écran : le même champ y est proposé DEUX ou TROIS fois, avec des valeurs SÉPARÉES.**
Exposition, vue, garages, surfaces, pièces, prix… existent à l'étape 1 (champs « du haut »), à l'étape 5
et à l'étape 7 (équipements). Mon remplissage automatique les avait mis en désaccord (exposition SUD à
l'étape 1, NORD-EST à l'étape 7 ; garages 1 et 30) : **c'est la valeur de l'étape 7 qui part chez Hektor**
(le worker applique les équipements en dernier). Un négociateur qui corrige l'étape 1 sans voir l'étape 7
enverrait l'ancienne. *Noté, non traité : hors pièce 2.*
⚠ **Fil d'Ariane** : la fiche affiche `#null` tant que Hektor n'a pas répondu. Cosmétique, noté.
⚠ **Une table d'essai posée par moi en base** : `essai_8a2b_naissance_20261021` *(la photo de la naissance,
pour la comparaison ; fermée à anon / authenticated)*. **À supprimer avec l'accord.**

**Le retour de Hektor** *(relecture à 21:55 UTC : la fiche détaillée de Hektor, 29 000 car., a REMPLACÉ la
nôtre, le calque a disparu — comme prévu)*. **Comparaison des 116 champs, un par un** :

| | nombre | détail |
|---|---|---|
| identiques | **92** | |
| même valeur, autre FORME | **12** | toutes les dates : `15-09-2026` → `2026-09-15` |
| recalculés par Hektor | **2** | latitude / longitude, d'après l'adresse (`45.388` → `45.397`) |
| ⚠ **écart réel** | **1** | `corps` : le **« Texte annonce » de l'étape 7 est PERDU** — Hektor n'a gardé que la « Description » (2 textes, tous deux la description). À la naissance nous montrions le texte saisi, après le retour la description |
| ⚠ **absents de la fiche relue** | **10** | `TRANSPORT`, `PROXIMITE`, `ENVIRONNEMENT`, `diagnostiqueur`, `Particularites`, et les honoraires `_selecterHonoraires2/3`, `_tauxHonoraire2`, `_pourcentHonoraire2`, `_detailHonoraire2` (seul le **montant** 12 000 « Acheteur » revient, par `honoraires_json`) |

⚠ **NON MESURÉ, et je ne le suppose pas** : si ces 10 champs sont **perdus chez Hektor** ou seulement **pas
encore relus** — les blocs que l'app tire de la CONSOLE (`secteur_console_json`,
`honoraires_detail_console_json`, `pieces_detail_console_json`) sont **vides**, statut de l'extraction
console `null` : elle n'est pas encore passée. Pour trancher : lire l'annonce **63330 dans Hektor** (lecture
seule), ou attendre l'extraction.

**À l'écran, après le retour** *(même fiche, mêmes rubriques)* : Localisation **10/10 → 7/10** · Prix, mandat
& honoraires **13 → 8** remplis · Diagnostics **29 → 28** · Intérieur **8 → 7**. Le fil d'Ariane passe de
`#null` à `#63330`, la fenêtre dit « Annonce disponible ».

⭐⭐ **CE QUE ÇA DIT POUR LA SUITE — c'est le cœur de la pièce 3** : « garder chez nous » **tient jusqu'au
retour de Hektor, pas au-delà**. La relecture **remplace** la fiche détaillée — calque **et**
`app_saisie_creation` compris. Ce que Hektor ne renvoie pas (ou pas encore) **disparaît de chez nous** : il
ne reste que dans la demande au worker *(pas un lieu sûr)* et dans ma table d'essai. **La pièce 3 doit
donc GARDER la saisie au-delà de la relecture** (une place à part, que la relecture ne touche pas) **et
comparer** — exactement ce que la comparaison ci-dessus a fait à la main.

### Audit du 22/10 — latitude / longitude, et les 10 champs « absents » *(Frédéric : « nous avions déjà tout travaillé ces champs, cherche et explique »)*

**1. La latitude et la longitude : c'est NOUS, pas Hektor.** Prouvé de trois façons :
- le journal du worker, 21:54:21 : « **Localite privee mise a jour (BAN)** », localité 912954, « 8 Rue de
  l'Ondaine », Firminy — c'est `geocodeAddressBAN` (console_job_worker.js:3277) qui interroge la **BAN de
  l'État** (`data.geopf.fr/geocodage`), puis pose la localité chez Hektor (`updateLocaliteByFeature`) ;
- la BAN interrogée à nouveau le 22/10 rend **exactement** `4.292822 / 45.39706` (score 0,96) — les
  valeurs que Hektor a gardées ;
- la recette est écrite depuis le **29/07** (mémoire `hektor-adresse-secteur-graphql`,
  `adresse-edit-geoloc-et-overlay`), et l'app géocode aussi elle-même à la modification d'une adresse
  (`geocodeAddress`, lib/api.ts:4477, appelé App.tsx:29601).
⭐ **Donc on est autonome sur ce point** : le service est public, les deux codes existent. ⚠ **Le seul
trou** : à la **création**, l'app ne géocode PAS (un seul appel, à la modification) — les coordonnées
n'arrivent chez nous **qu'à la relecture**, par Hektor. Pendant les ~2 min, et le jour de la coupure : une
annonce sans coordonnées (carte, estimation, cadastre lisent `latitude_detail`). **Remède connu, petit** :
géocoder à la naissance (l'écran avant l'envoi, ou la fonction de naissance). *Non codé.*

**2. Les 10 champs absents ne sont PAS perdus chez Hektor : le worker les y a écrits.** Journal 21:54:12
et 21:54:21 : « Sauvegarde groupe secteur » avec `TRANSPORT`, `PROXIMITE`, `ENVIRONNEMENT` (deux fois) ;
`diagnostiques`, `mandat_infofi` sauvegardés ; `error_groups: []`. C'est **notre RELECTURE qui ne les
rapporte pas** — l'API de Hektor (`AnnonceById`) ne les rend pas. C'était écrit le **08/06**
(`notice/NOTE_EXTRACTION_CONSOLE_CHAMPS_MANQUANTS_2026-06-08.md`) : secteur (`immeuble`, `TRANSPORT`,
`PROXIMITE`, `ENVIRONNEMENT`), contacts diagnostics (`diagnostiqueur`, `syndic`), détail des honoraires,
location / rendement, détail des pièces → **seule la console** les donne, par
`Console/extract_hektor_missing_fields.js` (via `phase2/sync/sync_console_missing_fields.py`).

**3. Pourquoi ils ne sont pas revenus pour 63330 — DEUX causes, dont une NEUVE :**
- **(déjà écrit le 08/10, chantier ⑤ « 5a ter »)** : l'extraction console **ne tourne JAMAIS la nuit** —
  elle est derrière `-RunConsoleMissingFields` (`run_full_pipeline.ps1` l. 89, éteint par défaut) et
  `scheduled/run_quotidien.ps1` l. 39 ne le passe pas. Elle ne tourne que dans une relecture **non
  légère** d'une annonce précise (console_job_worker.js:4144-4155) ;
- ⚠ **NEUF, mesuré le 22/10** : pour une annonce **qui vient de naître**, cette extraction ciblée **ne
  sélectionne RIEN** (« selected: 0 », travail `7a29e1d5`, 21:54:45). Elle cherche l'annonce dans la table
  locale `app_view_generale` (`sync_console_missing_fields.py:123-147`), or cette ligne n'est écrite
  **qu'à l'étape SUIVANTE**, par `push_single_annonce_to_supabase.py:859-861`. **L'ordre des étapes la
  rend aveugle sur toute création.** Elle y est maintenant (vérifié en lecture), mais rien ne la relancera.

**4. Ce que ça pèse sur tout le parc** *(mesuré le 22/10, `app_dossier_detail_current`)* :

| bloc | annonces vivantes qui l'ont chez nous |
|---|---|
| **console** (secteur, contacts diagnostics, honoraires détaillés…) | ⚠⚠ **103 sur 13 497 (0,8 %)** |
| **chauffage** (le run de nuit, 50 par nuit, scope « current ») | **9 985 sur 13 497 (74 %)** |

⭐ **Frédéric avait raison sur le principe** (« vérifie dans le run chauffage s'il n'y a pas aussi le DPE ») :
le run de nuit **ne lit que le chauffage** (`extract_hektor_chauffage_only.js` : les tableaux
`chauffageExist*`). **Le DPE n'en a pas besoin** : il vient de l'API (groupe `diagnostiques`) et les
vignettes DPE/GES sont recalculées par `export_app_payload.py` — dans l'essai, `dpe_cons`, `dpe_ges`,
`valeurEnergieFinale`, les coûts, l'année de référence et toutes les dates de diagnostic sont revenus
**identiques**.

⚠⚠ **POUR LA COUPURE** : pour **99,2 % du parc**, transport / proximité / environnement / immeuble,
diagnostiqueur / syndic, honoraires détaillés et location **n'existent QUE chez Hektor**. Ce n'est inscrit
ni dans les 46 chapitres du 07/10 (L10-8f n'en parle que comme d'une garde de forme), ni dans la liste
« seul Hektor fournit » (pièce 4, à faire). **Ça a une date de péremption**, comme les photos masquées.
*Noté, non décidé.*

**5. Le « Texte annonce » perdu : c'est NOTRE worker.** Journal 21:53:56 : « **Sauvegarde texte
principal** » avec `title` + `description` — après le wizard, `applyCreatedAnnonceInitialFields` réécrit
le texte principal avec la **Description**, par-dessus le `corps` saisi à l'étape 7. *Noté, non traité.*

⬜ **L'interrupteur `annonce_nait_complete` est TOUJOURS ALLUMÉ** (la question du 21/10 n'a pas reçu de
réponse).

### Résumé de l'étude des champs — 22/10 *(Frédéric : « relis et étudie en profondeur, on avait pris des décisions »)*

**Les études déjà faites, retrouvées** :
- **08/06** `NOTE_GROUPES_API_DETAIL_SUPABASE_2026-06-08.md` — ce que l'**API** donne : 9 groupes exposés
  dans la fiche ; et la liste nommée de ce qu'elle **ne donne pas** : chauffage, `diagnostiqueur` /
  `syndic`, secteur (`immeuble`, `TRANSPORT`, `PROXIMITE`, `ENVIRONNEMENT`), détail des pièces,
  diagnostics terrain, détail des honoraires ;
- **08/06** `NOTE_EXTRACTION_CONSOLE_CHAMPS_MANQUANTS_2026-06-08.md` — l'extracteur console pour ceux-là,
  ⭐ **et la DÉCISION** : *« ne la lance plus par défaut dans le quotidien »*, « outil de
  contrôle/rattrapage, sans multiplier les lectures console Hektor » ;
- **09/06** `NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09.md` — le chauffage sorti à part, **lui** tous
  les soirs (50 / nuit) ;
- **07/07** `AUDIT_CHAMPS_HEKTOR_MANQUANTS_2026-07-07.md` — les champs qui manquaient **à l'écran**
  (terrain, diagnostics, piscine, construction récente…) : **ajoutés depuis** — ils sont dans les 173 ;
  ⚠ deux d'entre eux **ne l'ont jamais été** : `PLAIN_PIED` et `globalCondition` (0 occurrence dans
  App.tsx) ;
- **19/08** carte A1 (**189** noms côté worker = 27 textes + 26 nombres + 136 équipements ; les mêmes
  champs sous deux noms, d'où 173 à l'écran) · **28/09** N.1 et N.1-(b) · **08/10** chantier ⑤ « 5a ter »
  (la console ne tourne jamais la nuit, mesuré).

**Ce que ça donne, au 22/10 :**
- **à l'écran, il ne manque PAS de champ** : la fiche en affiche **173**, c'est bien « nos 170 » ;
- l'API de Hektor en rapporte **la grande majorité** — l'essai 63330 : 92 identiques + 11 dates
  (autre forme) + 2 coordonnées (les nôtres, BAN) sur 116 envoyés ; ⚠ *rectification : 11 dates, pas
  12 comme écrit plus haut* ;
- **~21 champs ne reviennent QUE par la console** : secteur ×4, contacts diagnostics ×2, honoraires
  détaillés ×8, location ×4 *(liste exacte : `extract_hektor_missing_fields.js` l. 24-36)*, chauffage ×3
  (son propre extracteur) — plus les **notes des pièces** (l'API ne rend que type / étage / libellé /
  surface) ;
- ⭐ **« on a réussi à récupérer honoraires, syndic… » est VRAI pour la MÉCANIQUE** : depuis juin l'app
  sait les **lire et les afficher** (`export_app_payload.py` l. 52-58 / 1429-1434 ; `App.tsx` l. 31357-31363
  et 36008-36014). **Ce qui manque, c'est le PASSAGE** : 103 annonces vivantes sur 13 497 l'ont eu. Le
  **montant** des honoraires, lui, vient de l'API (`honoraires_json`) ;
- `Particularites` : l'API rend son groupe `particularites` **vide** pour 63330 — envoyé ou non par le
  worker, **non vérifié** (le journal est tronqué) ;
- la « Note » de l'étape 6 : **non retrouvée** dans la fiche relue — **non vérifié** si Hektor l'a.

**Ce qui découle pour la coupure — À DÉCIDER PAR FRÉDÉRIC, rien n'est tranché :** la décision de juin
(« pas de console la nuit ») a été prise pour **ménager Hektor**, pas en pensant à la coupure. Pour 99,2 %
du parc, ces ~21 champs n'existent que chez Hektor. Trois voies : la garder telle quelle · un balayage
lent sous le mur (comme les photos masquées) · ne garder que les annonces vivantes.

### Le tableau des 173 champs, un par un — 22/10 *(Frédéric : « sois plus précis »)*

➡ **`notice/ESSAI_173_CHAMPS_ANNONCE_2026-10-22.md`** : pour chacun des 173 champs de la fiche, envoyé ou non
(et pourquoi), gardé à la naissance, revenu ou non, et son remplissage sur les **500 annonces actives les
plus récentes**. En bref : **116 envoyés** (116 gardés à la naissance), **57 non envoyés** (51 masqués par
l'écran — type maison, piscine NON, terrain, location, honoraires vendeur NON — 3 fabriqués par Hektor,
3 chauffage à sa valeur par défaut) ; **10 pas revenus** (9 console seule + `Particularites`) ; sur le lot,
**23 champs vides sur les 500** : 18 « console seule », 3 chauffage (lu dans une autre clé, rempli pour
311 / 500), `Particularites` (groupe API en LISTE que la rubrique ne lit pas, 7 / 500), un commentaire
jamais saisi.

**22/10 — DÉCISION DE FRÉDÉRIC : « Oui, garde allumé ».** L'interrupteur `annonce_nait_complete` reste à
`on` (allumé le 21/10 à 23:47:29). Sa question suivante : les gardes de la relecture ont-elles été
adaptées ? → audit ci-dessous.

### « Est-ce le même mécanisme qu'avant ? Les gardes ont-elles été adaptées ? » — audit du 22/10

**1. C'est le MÊME mécanisme, élargi — rien de neuf vers Hektor.**
- Depuis le **24/09 (C.9-e)**, une annonce **naît dans l'app** (numéro ≥ 10 000 000, 11 colonnes), le
  worker la crée chez Hektor, la relecture **adopte** notre numéro et complète. La pièce 2 ne change
  **qu'une chose** : ce que l'on écrit chez nous à la naissance (la fiche détaillée en plus).
- **Ce qui part chez Hektor est IDENTIQUE** : la demande au worker n'est pas touchée (répétition T6 :
  « la saisie intacte ») et le journal de 63330 montre les mêmes étapes qu'avant.
- **Les champs non envoyés le restent, pour les mêmes raisons qu'avant** : l'écran masque ceux qui ne
  valent pas pour le type de bien (filtre par profil, côté écran ET côté worker,
  `isHektorWizardFieldAllowedForPayload`) ; le worker retire ses clés techniques (`mode`, `step`, `idann`…)
  et envoie le **chauffage par sa propre étape** (`applyHektorChauffage`, l. 11166). Un champ que l'écran
  n'envoie pas n'est **pas** non plus gardé chez nous : on ne garde que la saisie.
- Les champs « à l'app seulement » (`CHAMPS_APP_ANNONCE`) : **toujours éteints** (tranché le 13/10), non
  touchés.

**2. Les gardes qui existent — aucune n'avait à être adaptée, et je l'ai vérifié une par une :**

| garde | ce qu'elle regarde | touchée par la pièce 2 ? |
|---|---|---|
| le worker : « Création confirmée par liste GraphQL », puis « finalisée » (`isDraft`, `isBroadcasted`) | Hektor lui-même | non |
| le worker : `error_groups` à chaque groupe écrit | la réponse de Hektor | non |
| `phase2/checks/annonce_un_numero.py` (4c) : `en_attente` / `creation_echouee` | la ligne ≥ 10 M **et** l'état du travail | non — elle **ne lit pas** la fiche détaillée (l. 92-129) |
| le run de nuit C.9-c : épargne une annonce née dans l'app | `stale_ids`, **les 4 tables dont le détail** (`push_upgrade_to_supabase.py` l. 1407-1416) | non, et elle **protège** aussi notre fiche |
| l'écran « Suivi de l'action » (Hektor / App) | l'état du travail | non |
| la cloche du négociateur en cas d'échec (20/08) | l'état du travail | non |

**3. ⚠ CE QUI N'EXISTE PAS — et n'a jamais existé pour la création d'annonce :** une garde qui compare,
**champ par champ**, ce que nous avons envoyé et ce que Hektor a gardé. C'est **N.2**, prévue le 07/10 —
c'est **la pièce 3**. L'essai 63330 l'a faite **à la main** (92 identiques, 11 dates, 2 coordonnées,
1 texte remplacé, 10 non revenus).

**4. ⚠ UN EFFET À CONNAÎTRE** : avant, une création ratée chez Hektor se voyait aussi **à l'œil** — une
fiche vide. Maintenant la fiche est **pleine dès la naissance**, même si Hektor échoue ensuite. L'échec
reste signalé par le travail en erreur, la cloche, l'écran de suivi et la garde 4c (avec ~30-40 min de
retard pour l'alerte), mais **l'indice visuel a disparu**. *Noté, non traité : à prendre dans la pièce 3.*

## Pièce 3 — GARDER LA SAISIE AU-DELÀ DE LA RELECTURE + LE CONTRÔLE AU RETOUR (N.2) — audit du 22/10 *(Frédéric : « oui commence »)*

*Audit limité à l'ANNONCE (création, et ce que ça dit de la modification). Contact, recherche,
transaction, mandat : non mesurés ici.*

**Ce qui existe déjà — relu :**
- **le modèle B pour la MODIFICATION** *(plan l. 479-482, worker l. 10505-10580)* : la photo d'avant
  (`app_annonce_pending.base_snapshot`), le worker relit la date de Hektor avant d'écrire, `skipped` →
  `partial` et la ligne d'attente **gardée**, la sentinelle `data.annonce_partielle` (critical, seuil 0) ;
- **L3, la protection par champ** *(21/09, `patch_l3_protection_par_champ_2026-09-21.sql`)* : après
  chaque relecture, `push_single_annonce_to_supabase.py:461-470` appelle
  `app_annonce_reappliquer_saisies` qui **repose par-dessus** les saisies encore en attente — **et elles
  seules** : dès que Hektor a confirmé, la ligne disparaît et c'est lui qui parle ;
- **N.2 redessinée le 28/09, jamais codée** : *« comparer, après la resynchro, ce qui est REVENU à ce qui
  a été ENVOYÉ, champ par champ »*, avec **la cible de relecture figée champ par champ** (9 noms ambigus ;
  `titre_bien` préfère le listing au détail) — cible fournie par N.1-(b), et éprouvée à la main sur 63330 ;
- **le carnet de l'annonce** (`app_annonce_champ_app`, 12 lignes) **n'est PAS le bon endroit** : décision
  du 28/09, c'est un carnet d'**exceptions** (4 champs), « N.3 à abandonner, elle en ferait un doublon » ;
- le carnet de l'**affaire** (`app_affaire_champ_app`) a le patron du verdict : `valeur_hektor_au_moment`,
  `etat`, `valeur_hektor_relue`, `constate_le`.

**Le trou, mesuré :**
1. à la création, la saisie vit dans la fiche détaillée (`app_saisie_creation` + le calque) — **la
   relecture la remplace** (vu sur 63330). Il n'en reste que la demande au worker, qui n'est pas un lieu sûr ;
2. **le même trou existe pour la MODIFICATION, sur les champs « console seule »** : la ligne d'attente
   disparaît quand Hektor a confirmé l'écriture, la relecture ne rapporte pas le champ (l'API ne le donne
   pas) → il **disparaît de l'écran** alors qu'il est chez Hektor ;
3. personne ne compare ce qui est revenu à ce qui a été envoyé — ni à la création, ni à la modification
   (classe « C » : accepté puis recalculé → `wrote = true`, rien ne le voit).

**Les volumes** *(90 derniers jours)* : **9 créations** d'annonce (dont mes 2 essais ; 3 nées dans l'app)
et **23 modifications** ; une seule création portait du secteur (mon essai), 2 modifications des honoraires
détaillés. ➡ **l'enjeu n'est pas le volume d'aujourd'hui, c'est la coupure.**

### La méthode proposée — À ARBITRER PAR FRÉDÉRIC, rien n'est décidé

| | quoi | où | ce que ça touche |
|---|---|---|---|
| **A — GARDER** | une place **à part** pour la saisie de naissance : une ligne par annonce, la saisie (sans le mandant), qui l'a écrite et quand. **La relecture ne la touche jamais.** | une table neuve, remplie au moment de la naissance *(un déclencheur sur l'insertion de la fiche de départ, ou le bloc de la création)* | base seulement ; et **la doublure** (la descente doit la copier) |
| **B — CONTRÔLER** | après la **première** relecture, comparer champ par champ, **avec la cible figée** (celle du tableau des 173), et écrire le verdict : identique · même valeur autre forme · recalculé · **remplacé** · non revenu (console seule) · **non revenu** | sur la même ligne (le patron de l'affaire : `etat`, `valeur_hektor_relue`, `constate_le`) | base seulement ; ne bloque jamais la relecture |
| **C — AFFICHER** | les champs que Hektor **a acceptés mais ne rend pas** (console seule) **restent visibles** après le retour, tant que la console ne les a pas rapportés | dans `app_annonce_reappliquer_saisies` (L3), **le même endroit** que les saisies en attente | la fiche ; ⚠ à trancher : si quelqu'un les change ensuite **dans Hektor**, notre valeur masquerait la sienne jusqu'au passage de la console |
| **D — SIGNALER** | un écart réel (remplacé, non revenu hors console) → **une ligne par annonce et par champ**, sur la fiche et dans Santé | sentinelle, sur le modèle de `data.annonce_partielle` | ⚠ à trancher : critical ou warning |

**Hors A-D, trouvés en chemin — à ranger par Frédéric (dans la pièce 3 ou à part) :**
- **E** l'extraction console **aveugle sur une création** (elle tourne avant que la ligne locale existe) —
  c'est un changement d'ordre dans le **worker** (redémarrage) ;
- **F** le « Texte annonce » réécrit par la Description (`applyCreatedAnnonceInitialFields`) — **worker** ;
- **G** géocoder à la naissance (BAN) — petit, base ou écran ;
- **H** le même trou « console seule » à la **modification** (point 2) — C le couvrirait si on l'étend
  aux modifications.
- **I** l'indice visuel perdu (fiche pleine même si Hektor échoue) — D le couvrirait.

### « Mais on a fait cela pour ajouter et modifier un contact ? » — 22/10

**À moitié — et la moitié faite est exactement le morceau C, pour 3 champs.**
- **Création de contact** (pièce 1) : la relecture **remplace** la ligne par celle de Hektor, puis
  **réinjecte** les 3 champs que Hektor ne renvoie jamais — naissance, lieu, situation — depuis notre
  propre ligne (`fetch_app_owned_contact_fields`, `push_contacts_to_supabase.py:490-512` et 848-870,
  « Lot 3 », correctif du 18/08). **Mesuré sur 20000007 après sa relecture** : les 13 champs saisis sont
  **tous là** (les 10 autres, l'API de Hektor les rend). Pour le contact, « garder » tient donc **par
  construction** : Hektor rend presque tout, et le reste est réinjecté.
- **Modification de contact** : une ligne d'attente (`app_contact_pending`) ; tant qu'elle existe, la
  relecture **saute le contact entier** (`dirty_contact_ids`, l. 833-846) — la protection **par bien**,
  celle que L3 a remplacée **par champ** pour l'annonce le 21/09.
- **Ce qui n'existe NI pour le contact NI pour l'annonce** : une **saisie gardée à part** et un **contrôle
  au retour** champ par champ *(audit du 21/10, `AUDIT_PORTES_DE_CREATION` l. 75 et 146-147 : « aucune
  comparaison »)*. Le seul contrôle au retour qui existe est celui de l'**affaire**
  (`console_job_worker.js:15040-15080`, `app_affaire_champ_app`).
➡ **Pour l'annonce, le même principe que le contact donnerait C** : réinjecter après la relecture les
champs que Hektor ne rend pas — mais ils sont ~18 (console seule), pas 3, et ils ne sont pas dans une
colonne chez nous : il faut d'abord **A** (les garder quelque part).
- **Le contrat qui porte cela pour le contact** : `phase2/identite/contrat_autorite.py` l. 61-68 —
  `CHAMPS_APP_CONTACT = (birth_date, birth_place, marital_status)`, *« Hektor ne renvoie JAMAIS ces
  trois-là : seule l'app les écrit »* ; `CHAMPS_APP_ANNONCE = ()` **vide, voulu** (13/10 : on n'y inscrit
  qu'un champ que l'app CRÉE et que Hektor N'ENTRETIENT PAS) ; `CHAMPS_APP_MANDAT =
  (mandat_date_cloture,)` sur ce critère, mesuré.
- ⭐ **Mesure du 22/10, qui éclaire la décision** : sur les **103** annonces qui ont le bloc console,
  `TRANSPORT` est rempli **2 fois**, `PROXIMITE` **3 fois**, `diagnostiqueur` **0 fois**. Ces champs sont
  **presque jamais saisis chez Hektor** — ils ressemblent aux 3 champs du contact. ⚠ Échantillon NON tiré
  au hasard (les 103 sont celles qu'une relecture complète a touchées) ; les honoraires détaillés ne sont
  **pas** mesurés ici. ➡ Le « trou de 99 % » pour la coupure porte donc **surtout sur des cases vides**.

### « Les doublures, le miroir qui n'écrase plus… ça n'évite pas cela ? » — 22/10

**Non, et voici pourquoi — chacune protège AUTRE CHOSE :**
- **La règle 5** (« le miroir se met à jour, il ne se remplace pas », 21/08) protège **`data/hektor.sqlite`**,
  l'archive de **tout ce que Hektor a dit** (plan l. 2995-3010). Elle garde les réponses de Hektor ; notre
  saisie n'y est jamais entrée.
- **La doublure** (la descente de 07:45, `pull_from_supabase.py`) **recopie Supabase tel qu'il est** :
  ce que la relecture a effacé dans Supabase, elle l'efface aussi. Mesuré : la doublure locale de
  `app_dossier_detail_current` (13 496 lignes) **n'a pas encore** 10000006 (née après la dernière
  descente) ; à la prochaine, elle aura la version **de Hektor** — sans la saisie.
- **La règle qui couvre ce cas existe** : **la règle 2, « Hektor confirme, il n'écrase pas »**. Elle est
  **appliquée** à la modification d'annonce (L3, par champ) et au contact (les 3 champs réinjectés). Elle
  ne l'est **pas** à la saisie de création d'annonce — **c'est exactement la pièce 3 (A + C)**.
- ⭐ **Et c'était prévu dès le 19/08** — carte A1 §2.3 : *« le blob ne peut pas être réécrit en entier par
  l'import — il faut préserver ces clés. C'est le point technique le plus délicat. »*

**22/10 — DÉCISION DE FRÉDÉRIC : « LES QUATRE, ET ENSUITE ON FAIT AUSSI POUR LES CONTACTS CE QUI EST
NÉCESSAIRE ».** Pièce 3 = A + B + C + D pour l'annonce ; puis le contact, à mesurer (ce qui lui manque
vraiment). E à I restent **notés, non rangés** (pas de réponse) — je ne les fais pas.
**Précision de Frédéric (22/10)** : *« ensuite il faudra finir aussi ajout et modifier contact, et pense à
contrôler ton travail »* → après la pièce 3 de l'annonce : **la création ET la modification de contact**,
complètes. Et chaque morceau est **éprouvé** avant d'être présenté.

### Pièce 3 — le code (22/10) — ÉCRIT, **PAS APPLIQUÉ**, répétition prête

`supabase/patch_8a3_annonce_saisie_gardee_2026-10-22.sql` · `…_INVERSE.sql` · `…_REPETITION.sql` (générée par
`gen_repetition_8a3.py`, brouillon de la session). Interrupteur **`annonce_saisie_gardee`, posé ÉTEINT**.
- **A** table `app_annonce_saisie_naissance` (une ligne par annonce née dans l'app : saisie, calque,
  auteur, verdict, écarts, « vu ») — RLS, fermée à anon / authenticated ;
- **B** `app_annonce_lecture_hektor` = **la cible figée** du tableau des 173 (noms à plat, 11 groupes, blocs
  console, chauffage) ; `app_annonce_verdict_naissance` → identique · autre_forme · recalcule · remplace ·
  absent · console_seule ; les « console seule » sont **rejugés** quand la console passe ;
- **C** les 21 champs « console seule » sont reposés dans le calque : **la valeur de Hektor** s'il l'a rendue,
  sinon la nôtre tant que son bloc n'est pas arrivé ; **une saisie en attente (L3) gagne** ; une
  modification dans l'app met la saisie gardée à jour ;
- **D** la vue `app_v_annonce_naissance_ecarts` (une ligne par champ en écart) et
  `app_annonce_naissance_ecart_traiter` (admin, « vu ») ; la sentinelle `data.annonce_naissance_ecart`
  sera ajoutée à `monitoring/check_gti_health.py` **après** la pose (avant, elle interrogerait une table
  absente) ;
- **un seul déclencheur** sur `app_dossier_detail_current` : il voit **toutes** les portes (naissance,
  relecture, run de nuit, modification, L3) ; un échec s'avale, l'écriture passe toujours ;
- **le retour arrière ne perd aucune saisie** : table non vide → renommée `…_avant_inverse_<date>`.

**Contrôle de mon propre travail, avant tout essai** : 2 défauts trouvés à la relecture et corrigés —
(1) une valeur de Hektor reposée par nous aurait été prise pour une saisie à la modification suivante,
**effaçant en silence un écart « remplacé »** ; (2) un champ console modifié dans l'app mais absent à la
naissance n'était jamais rejugé. Balises `$…$` équilibrées dans les 3 fichiers, aucun retour chariot.

**La répétition** (tout annulé) rejoue sur la **vraie** fiche de 63330 et sa photo de naissance : T1 naissance
· T2 retour de Hektor *(attendu : identique 92, autre_forme 11, recalcule 2, remplace 1, console_seule 9,
absent 1 ; 9 champs reposés ; le reste de la fiche intact)* · T3 la console passe · T4 une modification
dans l'app · T5 la garde anti-masquage · T6 interrupteur éteint · T7 une autre annonce intacte · T8 une
fiche illisible (l'écriture passe) · T9 une **vraie** création · T10 la vue et le « vu » · puis le vrai retour
arrière.

### Pièce 3 — la répétition : **21 sur 21, après UN défaut trouvé par elle** *(22/10, Frédéric : « vas-y »)*

**1er passage — ⛔ un défaut** : les 9 « console seule » de 63330 sortaient **`absent`**, et **aucun** n'était
reposé (T2 : 0 au lieu de 9). Cause : quand la fiche de Hektor porte la clé du bloc console **à `null`**,
`app_annonce_porteur_present` rendait un **booléen inconnu** (`jsonb_typeof(null) = 'object'` → NULL), et
« not inconnu » fait sauter la condition. **Corrigé** : `coalesce(…, false)` sur les deux retours.
⭐ *C'est exactement le rôle d'une répétition : la relecture du code ne l'avait pas vu.*

**2e passage — tout conforme à l'attendu :**

| essai | résultat |
|---|---|
| T1 la naissance | saisie gardée, **116** champs au calque |
| T2 le retour de Hektor | identique **92** · autre_forme **11** · recalcule **2** · remplace **1** (`corps`) · absent **1** (`Particularites`) · console_seule **9** — **2 écarts** ; **9 champs reposés** (TRANSPORT = « Bus ligne 4 a 200 m ») ; le reste de la fiche **intact à l'octet** |
| T3 la console passe | TRANSPORT **remplace** (Hektor dit « Tram », c'est lui qu'on affiche) · PROXIMITE **absent** (Hektor vide → rien d'affiché) · ENVIRONNEMENT **identique** — **4 écarts** |
| T4 une modification dans l'app | la saisie gardée prend « Cabinet X », et la relecture suivante **l'affiche** |
| T5 la garde anti-masquage | TRANSPORT **reste un écart** ; la saisie gardée n'a pas été écrasée par la valeur de Hektor |
| T6 interrupteur éteint | la fiche passe **telle quelle**, la saisie gardée **ne bouge pas** |
| T7 une autre annonce | **intacte à l'octet**, aucune ligne gardée pour elle |
| T8 une fiche illisible | **l'écriture passe** (le déclencheur s'efface) |
| T9 une **vraie** création | saisie gardée, TRANSPORT = « Gare à 5 min », **auteur = Frédéric**, **mandant absent** |
| T10 la vue et le « vu » | **4** lignes d'écart, 1 annonce marquée, **0** reste à signaler |
| droits | table et vue **fermées** à anon / authenticated |
| retour arrière | déclencheur, fonctions, interrupteur **retirés** ; la saisie **gardée sous `…_avant_inverse_20261022`** (aucune perte) ; création et naissance **non retouchées** |

**Vérifié à part après coup** : aucune table, aucune copie, aucun déclencheur, aucun interrupteur, **0** fiche
« ESSAI 8A3 ». Séquence **10000008** (2 numéros consommés, un par passage). ⚠ La fiche de 63330 a changé
d'empreinte depuis le 21/10 (`466d6092…` → `673ec222…`) : **le run de nuit l'a rafraîchie** — sans rapport
avec la répétition (annulée).

### Pièce 3 — APPLIQUÉE, interrupteur ÉTEINT *(22/10, Frédéric : « oui »)*

Collée par moi : **6 contrôles verts** — interrupteur `annonce_saisie_gardee` posé `off` · table créée, vide,
fermée à anon / authenticated · **un seul** déclencheur sur `app_dossier_detail_current` · création
(`a5e70b57`) et naissance (`944db16b`) **non retouchées** · « vu » ouvert aux connectés, fermé à anon.
**Tant que l'interrupteur est éteint, le déclencheur sort à sa première ligne : rien ne change.**

**La sentinelle (D)** : `data.annonce_naissance_ecart` ajoutée à `monitoring/check_gti_health.py` (liste
`DATA_SENTINELS`, après `data.annonce_push_bloque`) — sur la **vue** `app_v_annonce_naissance_ecarts`, filtre
`traite_le is null` : **une ligne par champ** en écart, échantillon de 5 (annonce, champ, état, envoyé, relu).
**`warning`** (un écart se regarde, il ne fait rien perdre) — *un mot à changer si Frédéric veut `critical`*.
**Éprouvée en lecture, sans lancer le contrôle** (qui peut envoyer des e-mails) : la vue se lit avec la clé du
contrôle (0 ligne), la règle rend `ok` à 0 et `warning` à 3, l'échantillon se lit. Fichier en **CRLF**,
préservé.

⬜ **Reste, avec accord** : allumer, puis un essai réel (une estimation créée par l'écran, avec des champs
« console seule » remplis) ; ensuite **la création et la modification de contact**.

### Pièce 3 — ALLUMÉE le 22/10 à 07:03:47 (heure de Paris) *(Frédéric : « oui, allume et fais l'essai réel par l'écran »)*

⚠ À l'allumage, **le run de nuit tournait encore** (`GTI Quotidien`, lancé à 05:00) et la descente (07:45)
n'était pas passée. **L'essai par l'écran attend la fin des deux** : la relecture d'une création écrit dans
`phase2.sqlite` comme le run (mémoire « phase2 : plusieurs écrivains »). L'interrupteur reste allumé pendant
ce temps : sur une annonce **sans** saisie gardée (toutes, aujourd'hui), le déclencheur ne fait qu'une lecture
de l'interrupteur et une recherche par clé primaire, et rend la ligne **telle quelle** (T7 de la répétition).

### Pièce 3 — L'ESSAI RÉEL PAR L'ÉCRAN : **RÉUSSI** *(22/10, 07:10-07:16, entre la fin du run (07:09:58, code 0) et la descente — idée de Frédéric)*

Estimation **appartement** créée par l'écran dans son Chrome (Firminy, PEREIRA, **152 champs remplis**),
avec cette fois les champs « console seule » (immeuble, transport, proximité, environnement, diagnostiqueur,
syndic, honoraires acquéreur 9 000 / 6,47 %) et le **chauffage hors défaut** (3 / 4 / 15). Clic à 07:10:20.

| mesure | résultat |
|---|---|
| **1,7 s** après le clic | annonce **10000009**, fiche de départ posée, **saisie gardée à part : 118 champs**, auteur = **frederic.gerphagnon@gti-immobilier.fr**, **mandant absent** |
| Hektor | **63331** créée à 07:12:42 (2 min 22 s), relecture à 07:13:03 |
| **le verdict (B), posé tout seul** | identique **91** · autre_forme **12** (les dates) · console_seule **14** · **remplace 1** |
| **l'affichage (C)** | les **14** « console seule » **reposés** dans le calque — dont le chauffage ; à l'écran **Localisation 10/10** (contre **7/10** à l'essai d'hier, sans la pièce 3), Transport « Gare SNCF a 400 m », Proximité, Environnement visibles |
| **la sentinelle (D)** | **1 ligne** : « 63331 · copropriete · remplace » → **warning** |

⭐⭐ **LE CONTRÔLE AU RETOUR A TROUVÉ UN VRAI DÉFAUT DU WORKER, dès son premier essai** : `copropriete`
envoyé **OUI**, Hektor garde **NON**. Journal : à 07:12:17 « Sauvegarde groupe copropriete » **avec**
`copropriete` ; à 07:12:37 **une 2ᵉ sauvegarde du même groupe**, venue des champs « à plat » (`copro_lots`,
`copro_quote_part`, `copro_works_fund`) **sans** `copropriete` — elle le remet très probablement à NON.
⚠ **Cause probable, NON prouvée** (il faudrait relire Hektor). *Noté, non traité : c'est le worker.*

⚠ **Trouvé en passant** : la fiche ouverte pendant la bascule « notre fiche → celle de Hektor » a affiché
**« 1 champ modifié · Enregistrer »** sans que rien ne soit saisi. Le compteur additionne les champs édités
**et** les pièces (`ckChangedPieces`, App.tsx:29577) : la copie locale des pièces était **périmée**. Rien
n'a été envoyé (je n'ai **pas** cliqué) ; **après rechargement, la barre a disparu**. Cause exacte **non
vérifiée**. *Noté, non traité.*
⚠ **Trouvé en passant (hors sujet)** : l'étape « ménage des orphelins de recherche » du run échoue **depuis
au moins 2 nuits** (21/10 06:54 et 22/10 06:58, `rpc/app_sweep_search_orphans`), non bloquante. *Noté.*

⬜ **Restent à supprimer, avec accord** : les essais 10000001/63329, 10000006/63330, 10000009/63331, le contact
20000007/605925, et la table `essai_8a2b_naissance_20261021`.
➡ **Suite décidée par Frédéric** : la **création et la modification de contact**, complètes.

### Le défaut de la copropriété — audit du 22/10 *(Frédéric : « avant, il faut régler le problème de copropriété »)*

**Ce qui est PROUVÉ :**
- chez Hektor, **63331 porte vraiment `copropriete = NON`** — lu dans son formulaire (extracteur console,
  lecture seule, 07:20), alors que le reste du groupe EST enregistré : lots **24**, lot **12**, quote-part
  **120**, fonds travaux **3 500**, plan de sauvegarde **OUI**, statut syndicat **ALERTE** ;
- **le témoin positif** : **62853** (créée le 05/08 avec `copropriete = OUI`) **porte OUI aujourd'hui**. Le
  geste a donc marché. **La différence** : 62853 n'a eu **qu'UNE** sauvegarde du groupe copropriété ;
  **63331 en a eu DEUX** — 07:12:17 (les équipements, dont `copropriete = OUI`) puis **07:12:37** (les champs
  « à plat » `copro_lots`, `copro_quote_part`, `copro_works_fund`, **sans** `copropriete`) ;
- **la 2ᵉ sauvegarde relit le formulaire avant d'écrire** (`postHektorMefUpdate`) et la relecture des radios
  est juste (`extractHektorFormValues` ne garde que la case **cochée**) ;
- **deux pistes ÉCARTÉES par la mesure** : (a) « le formulaire coche mal » — faux, le cache de 62853 montre
  OUI coché quand c'est OUI ; (b) « un champ caché `copropriete` en double » — faux, le HTML brut de 63331
  (`html_63331/copropriete_editer.html`, brouillon de la session) n'a que 3 radios (vide / OUI / NON).

**Ce qui n'est PAS prouvé** : si la 1ʳᵉ sauvegarde a bien posé OUI (puis la 2ᵉ l'a remis à NON), ou si OUI
n'a jamais pris. **Pour trancher, il faut ÉCRIRE chez Hektor** — rejouer les deux sauvegardes une par une sur
l'annonce d'essai 63331, en relisant entre les deux. ⛔ **Accord requis.**

**Deux autres écarts réels trouvés par la même lecture du formulaire (07:20)** :
- **le diagnostiqueur et le syndic sont VIDES chez Hektor** : ce sont des **listes de contacts** (`tag:
  select`, « Contacts »), l'app les saisit en **texte libre** → la valeur ne peut pas y entrer. *Défaut de
  l'écran de création (et sans doute de la modification), à mesurer.*
- **le pourcentage d'honoraires est RECALCULÉ** par Hektor : 6,92 % (= 9 000 / 130 000) au lieu de 6,47 %
  saisi — un champ « classe C » : Hektor calcule, l'app ne devrait pas l'imposer.
⭐ Et la même lecture **prouve** que transport, proximité, environnement, immeuble et les honoraires sont bien
chez Hektor — l'hypothèse « console seule » de la pièce 3 était juste.

### Le test de la copropriété chez Hektor, sur 63331 *(22/10, Frédéric : « oui »)* — ⚠ **mon hypothèse était FAUSSE**

Par la fonction que l'écran utilise (`app_edit_annonce_optimistic`, à son nom), puis lecture du formulaire de
Hektor après chaque étape :

| étape | ce que le worker a envoyé | ce que Hektor porte après |
|---|---|---|
| 1 *(07:32)* | **une** sauvegarde du groupe copropriété, `copropriete = OUI` seul | **OUI** ✅ |
| 2 *(07:35)* | **une 2ᵉ** sauvegarde du groupe, `copro_lots = 25` seul (relecture du formulaire avant) | lots **25**, copropriété **reste OUI** ✅ |

➡ **« La 2ᵉ sauvegarde du groupe remet la case à NON » est FAUX** : relire puis renvoyer le groupe garde la
case. **La cause de la création du 22/10 n'est donc PAS trouvée.** Ce qui distingue la création :
(a) l'annonce sortait juste du wizard (20 s entre les deux sauvegardes) ; (b) la 1ʳᵉ sauvegarde portait 7
champs dont **deux autres radios** (plan de sauvegarde, statut du syndicat) — qui, eux, ont pris ; (c) le
wizard avait déjà posté `copropriete` aux étapes 2 à 7. **Pistes écartées par la mesure** : un 2ᵉ champ caché
(HTML : 3 radios seulement), un champ `copropriete` dans un autre groupe (aucun), la normalisation de la valeur
(`OUI` reste `OUI`).

**Trois trouvailles du test, notées :**
- ⚠ **l'écran ne permet PAS de corriger une copropriété perdue** : la rubrique « Copropriété » de la fiche ne
  s'affiche que si la copropriété vaut déjà OUI (`condField: 'copropriete'`, App.tsx:26666) — j'ai dû passer
  par la fonction de modification ;
- ⚠ **un faux conflit** : le 1er essai a été **bloqué** (« bien modifié dans Hektor depuis l'édition ») —
  la date de Hektor était 07:20:32, 4 s après ma lecture du formulaire de 07:20:28. **Non reproduit** à
  l'étape 2 (la relecture avec lecture du formulaire n'a pas créé de conflit) : cause **non prouvée**. Saisie
  d'essai soldée en « abandon » (journal des résolutions) ;
- ⭐ **la pièce 3 rejuge en réel** : après la lecture du formulaire, les 15 « console seule » de 10000009 ont été
  rejugés — **10 identiques**, `_pourcentHonoraire2` **remplacé** (Hektor recalcule : 6,92), `diagnostiqueur`
  et `syndic` **absents** (listes de contacts chez Hektor, texte libre dans l'app) → **4 écarts, 0 en attente
  de la console**. ⚠ Et un manque de conception : le verdict de `copropriete` **reste « remplace »** alors que
  Hektor porte maintenant OUI — le verdict ne rejuge que les « console seule ». *À corriger : rejuger aussi
  les écarts, et les marquer « corrigé ».*

**Suite du test (22/10, Frédéric : « oui »)** — après la descente (finie à 08:07:07, code 0) :

| essai | envoi | Hektor après |
|---|---|---|
| 3 *(07:43)* | `copropriete = NON` seul | **NON** ✅ (point de départ) |
| 4 *(08:09)* | `copropriete = OUI` **et** `copro_lots = 26` en **un** envoi → le worker fait **exactement** le geste de la création : la sauvegarde avec la case (08:09:10), puis celle des lots **2 s après**, dans le même travail | **OUI** et **26** ✅ |

➡ **L'effet de temps est ÉCARTÉ** : deux sauvegardes rapprochées gardent la case. **Restent deux hypothèses** :
(b) la 1ʳᵉ sauvegarde de la création portait **7 champs dont deux autres radios** (plan de sauvegarde OUI,
statut du syndicat ALERTE) — peut-être que Hektor n'accepte pas la case **avec** eux ;
(c) l'annonce **sortait de l'assistant de création** — un état où Hektor ignore la case.

| 5 *(08:28)* | `copropriete = NON`, plan **NON**, statut **NOTPROCESS** | les trois pris ✅ (point de départ) |
| 6 *(08:30)* | **les 7 champs exacts de la création** en un envoi (case + lot + lots + quote-part + fonds + plan OUI + statut ALERTE) — le worker fait la sauvegarde « équipements » (08:30:08) **puis** celle des champs à plat (08:30:11) | **les 7 pris, copropriété OUI** ✅ |

➡ **L'hypothèse (b) est ÉCARTÉE.** **Six pistes écartées par la mesure** : la 2ᵉ sauvegarde du groupe, un champ
caché, un autre groupe, la normalisation, l'effet de temps, les 7 champs ensemble.

**Ce qui reste, et c'est maintenant étroit** : à la création, **entre** la sauvegarde de la case (07:12:17)
et la fin, le worker a fait **ce qu'aucun de mes essais n'a refait** : `construction_recente` (07:12:19), **la
localité privée par la BAN** (`updateLocaliteByFeature`, GraphQL, 07:12:23), le groupe **secteur** (07:12:24),
puis `ag_interieur`, **`ag_exterieur`** (étage, `floorState`, terrasse, garages, parkings — 07:12:34) et
`diagnostiques` (07:12:36). L'un d'eux, **côté serveur Hektor**, remettrait la copropriété à NON — sans que la
case soit dans leurs formulaires (vérifié : elle n'est que dans le groupe copropriété). *Non prouvé.*

### ⭐ LA CAUSE EST TROUVÉE — c'est la sauvegarde du SECTEUR *(22/10, 08:49-09:08, Frédéric : « oui, et si tu ne trouves pas on en recrée une de A à Z »)*

Sur 63331, par `app_edit_annonce_optimistic` (à son nom), puis lecture du formulaire copropriété de Hektor
(cache console relu **après** chaque travail) :

| essai | envoi | ce que le worker a sauvé | copropriété / lots chez Hektor après |
|---|---|---|---|
| 7 *(08:49)* | la fin de la création **sans la case** : adresse, immeuble, transports, construction, étage, parkings, états, 3 diagnostics | diagnostiques, ag_exterieur, construction_recente, **BAN**, **secteur**, ag_exterieur, diagnostiques — **aucune** sauvegarde copropriété | **NON / 0** ⛔ (lot 12, quote-part 120, fonds 3500, plan OUI, statut ALERTE **intacts**) |
| — *(08:55)* | remise `OUI` + `24` | copropriété | OUI / 24 |
| 8 *(08:59)* | **l'adresse seule** | **BAN** + **secteur** | **NON / 0** ⛔ |
| — *(09:03)* | remise `OUI` + `24` | copropriété | OUI / 24 |
| 9 *(09:07)* | **`immeuble` seul** — le secteur **sans** l'adresse, donc **sans la BAN** | **secteur** seul | **NON / 0** ⛔ |

➡ **C'EST LA SAUVEGARDE DU GROUPE SECTEUR** (`update_annonce_MEF`, `MEFgroup=secteur`) qui remet chez Hektor
`copropriete = NON` et `copropriete_nb_lot = 0`. **Ni la BAN, ni l'extérieur, ni les diagnostics, ni la
construction** (`construction_recente` ne porte que ses 4 radios, relu en lecture seule).
⚠ **Ce n'est PAS notre envoi qui écrit la case** : le formulaire secteur (`ihmChargeGroupe_Secteur`) ne porte
**aucun** champ copropriété (14 champs + `idpays`, vérifié), et `postHektorMefUpdate` ne poste **que** ce
formulaire. **C'est Hektor, côté serveur.**

**Et la création du 22/10 s'explique entièrement**, étape par étape *(heure de Paris)* :
07:12:17 copropriété OUI + 24 ✅ → **07:12:24 secteur → NON / 0** → 07:12:37 notre 2ᵉ passage « à plat »
renvoie `copro_lots = 24` mais **relit NON** dans le formulaire pour la case → **NON avec 24 lots** — exactement
ce que la relecture avait trouvé.

⭐⭐ **HEKTOR A CHANGÉ DE COMPORTEMENT** : 62853 (créée le 05/08) a eu **la même suite** — copropriété à
12:28:07, **secteur à 12:28:09** — et porte **toujours OUI / 3**. Entre le 05/08 et le 22/10, la sauvegarde du
secteur s'est mise à remettre la copropriété à zéro. *Date exacte non mesurée.*

**L'ampleur, mesurée sur les journaux (depuis le 07/06)** : 85 sauvegardes du secteur par le worker —
**74 à la création (44 annonces)**, **11 en modification (2 annonces, nos bacs à sable 62774 et 63331)**.
Créations ayant envoyé copropriété OUI : 10 — 8 de juin (hors parc vivant), 62853 (OUI, avant le changement),
63331 (perdue). ➡ **Aujourd'hui, une seule victime prouvée : 63331, l'essai.** Mais **toute** création avec
copropriété, et **toute** modification de l'adresse / immeuble / transports / proximité / environnement
depuis l'app, la ferait tomber désormais.

**NON MESURÉ, et je ne le suppose pas :**
- si la **même chose arrive quand un humain sauve le secteur dans l'écran de Hektor** (ce serait un défaut de
  Hektor pour tout le monde, et notre descente recopierait le NON) — il faudrait écrire chez Hektor par son
  écran pour le savoir ;
- si **d'autres champs** que ces deux-là tombent avec le secteur. Indice rassurant : à la création, la relecture
  a comparé **118 champs** et la copropriété est le **seul** écart inexpliqué ;
- depuis **quand**.

*63331 est laissée à NON / 0 (annonce d'essai, à supprimer avec accord).*

### La garde de la copropriété — ÉCRITE et éprouvée HORS LIGNE, **pas active** *(22/10, Frédéric : « prépare le correctif, sans redémarrer ni pousser »)*

**Où** : `Console/console_job_worker.js` — trois fonctions neuves juste avant `postHektorMefUpdate`
(`lireCoproprieteHektor`, `coproprieteDifferente`, `gardeCoproprieteApresSecteur`) et **deux branchements** dans
`postHektorMefUpdate`, **seulement quand le groupe est `secteur`**. ⭐ **Un seul endroit** : c'est le **seul**
chemin qui sauve un groupe chez Hektor (un seul appelant, `pushHektorGroupUpdate`) → il couvre **la création
ET la modification**, les groupes exacts comme les champs à plat.

**Le geste** : lire la copropriété (case + nombre de lots) **juste avant** le secteur → sauver le secteur →
la relire → si Hektor l'a bougée, **remettre ce qu'il portait** → **vérifier**.
- ⭐ **Il ne décide rien** : il remet l'AVANT. Une case passée à NON par l'utilisateur reste NON, quel que soit
  l'ordre des étapes.
- **Rien à perdre** (NON ou non renseignée, et 0 ou aucun lot) → une seule lecture, rien d'autre.
- ⚠ **Une case NON RENSEIGNÉE ("") devenue NON n'est PAS remise** — trouvé à ma relecture : ça ne perd aucune
  information, et remettre "" n'est pas éprouvé chez Hektor. Un refus aurait fait échouer **chaque**
  modification d'adresse des annonces sans copropriété (les maisons).
- **Aucun échec silencieux** : une remise qui ne tient pas **lève une erreur** nommant les champs, la valeur
  attendue et la valeur lue (création : le groupe est marqué en erreur et la création continue, comme les
  autres groupes ; modification : le travail échoue, rejouable). Une lecture impossible avant le secteur ne
  bloque pas le secteur, mais se **dit** au journal et au compte rendu (`garde_copropriete.status`).
- **Coût chez Hektor** : **+1 lecture** par sauvegarde du secteur (~1 à 2 par création) ; **+3 appels**
  (lecture, écriture, vérification) seulement quand la case est tombée.

**L'essai** : `node Console/test_garde_copropriete.js` — sur le **code réel** découpé dans le worker, avec un
**faux Hektor qui reproduit le défaut** mesuré. **16 contrôles verts**, dont :
- (2) **sans la garde, le faux Hektor fait tomber la case** — il est fidèle au défaut ;
- (4) **témoin inverse** : un Hektor qui ne remet rien à zéro → aucune écriture en plus ;
- (3e) le geste exact, appel par appel.

**Deux contre-épreuves** *(« une avarie qui ne change rien ne prouve rien »)* :
- garde cassée exprès (elle remettrait la valeur d'APRÈS) → **attrapée** par sa propre vérification, l'essai
  sort en code 2, pas en 0 ;
- ancienne vérification (qui jugeait aussi la case "" devenue NON) → **le contrôle (6c) échoue**, comme il le doit.
- Et la **vraie** fonction de lecture sur le **vrai** formulaire de 63331 capturé le matin lit
  `copropriete = NON`, `nb_lot = 24` — exactement l'état d'après la création.

⛔ **PAS ACTIVE** : il faut **redémarrer les 4 services worker** (file vide : 0 pending ET 0 running) — accord
de Frédéric obligatoire. Rien n'est poussé.
➡ **La preuve en réel, après redémarrage** : refaire l'essai 9 (`immeuble` seul sur 63331, case remise à OUI / 24
d'abord) → le journal doit dire « Garde copropriete : le secteur l'a remise a zero, on la remet » et Hektor
doit porter **OUI / 24** après.

### La garde de la copropriété — ACTIVE et PROUVÉE EN RÉEL *(22/10, Frédéric : « vas-y », puis « c'est fait, j'ai redémarré »)*

**Le redémarrage** : refusé à ma session (*« Impossible d'ouvrir le service »*, pas de droits d'administrateur) —
je ne l'ai pas contourné, Frédéric l'a fait. **Prouvé par les processus**, pas par la croyance : les 4 services
ont changé de numéro (17844 / 15324 / 13396 / 16844 → 536 / 4124 / 256 / 16624), les 4 `node.exe` sont nés à
**11:29:35-37**, après la dernière écriture du code (10:31:33). File vide avant ET au moment du redémarrage
(0 pending, 0 running, aucun travail dans les 15 min).

**La preuve, sur 63331** *(heure de Paris)* :

| heure | geste | résultat |
|---|---|---|
| 11:32 | remise `OUI` + `24` (groupe copropriété seul) | OUI / 24 chez Hektor (lu en lecture seule) — ⚠ voir l'incident ci-dessous |
| 12:00 | **`immeuble` seul** (secteur, sans BAN) — le geste de l'essai 9 qui faisait tomber la case | ⭐ voir le journal |

Le journal du travail `d86358dc` :
- 12:02:07 `Sauvegarde groupe secteur` (immeuble)
- 12:02:09 **`Garde copropriete : le secteur l'a remise a zero, on la remet`** — avant `OUI / 24`, après `NON / 0`
  ⭐ **le défaut a bien mordu, en réel**, et la garde l'a vu ;
- 12:02:10 `Sauvegarde groupe copropriete` (`copropriete`, `copropriete_nb_lot`)
- 12:02:13 travail `done`, compte rendu `garde_copropriete.status = "remise"`.

**Trois relectures indépendantes, toutes d'accord** : le formulaire Hektor en lecture seule (OUI coché, 24 lots,
lot 12, plan OUI, statut ALERTE), le cache console (extrait 12:02:24), **notre base** (OUI / 24, immeuble
« Residence Les Tilleuls »). File vide après.

**L'incident de 11:32, sans rapport avec la garde mais à connaître :**
- le processus « actions » s'est **arrêté net** (code `-1073740791` = `0xC0000409`, arrêt brutal de node, pas une
  erreur JavaScript) juste après les deux sauvegardes copropriété — ce travail ne touchait PAS le secteur, la
  garde n'a pas tourné ;
- ⚠ **ce plantage n'est PAS nouveau** : **42 fois** sur les 4 services depuis septembre (actions 16, sync_light 11,
  admin 9, documents 6), le dernier le 20/10. **Cause non cherchée** — noté, hors périmètre ;
- il laisse un travail **orphelin « running »**, qui **bloque tout travail sur la même annonce**
  (`app_console_claim_next_job` refuse un travail tant qu'un autre court sur la même annonce, et ne solde un
  « running » qu'après **30 minutes**). Soldé à la main à 11:55 **avec l'accord de Frédéric** (« clos »), message
  d'erreur explicite ;
- conséquence en chaîne : l'orphelin n'avait pas relu la fiche → notre base avait la date Hektor de 11:08, Hektor
  celle de 11:32 → l'envoi suivant a été **retenu à raison** par la garde anti-écrasement (`held_conflict`,
  aucune écriture chez Hektor). Sortie par les gestes de l'écran : saisie soldée « abandon » (journal des
  résolutions), relecture demandée (`app_console_request_annonce_refresh`), puis renvoi.

## 8a, fin — LA MODIFICATION DE CONTACT : audit du 22/10 *(Frédéric : « A »)* — lecture seule

> ⚠ **Audit limité au contact, geste « modifier »** (création : pièces 1 et 1 bis, faites). Les autres objets
> ne sont pas mesurés ici.

**Les portes — trois, une seule fonction.** Les deux fenêtres « Modifier le contact » (`App.tsx:37954` et
`:40832`) et « Modifier un mandant » (`app_update_mandant_contact_optimistic`, `api.ts:10061`, C.4 du 31/08)
passent **toutes** par `app_edit_contact_optimistic` (empreinte **`79d39e0e`**, inchangée depuis le 21/10).
L'ancienne `app_console_create_update_mandant_contact_job` n'est plus appelée par aucun écran (remplacée le
31/08, `f89c30a`) — ses 10 travaux datent de mai à octobre (essais).

**Le geste, suivi jusqu'au bout :**

| moment | ce qui se passe | où |
|---|---|---|
| clic | **12 colonnes écrites chez nous tout de suite** (nom, prénom, civilité, e-mail, 2 téléphones, adresse, CP, ville, naissance, lieu, situation) + ligne d'attente `app_contact_pending` avec la photo `_date_maj` | `app_edit_contact_optimistic` |
| clic | la fiche se recharge (`hektor:contact-updated`) → **affichage immédiat** | `App.tsx` |
| +10 min *(attente voulue, `debounce 600`)* | le worker envoie **toutes** les clés non vides chez Hektor ; **garde anti-écrasement** si Hektor a bougé depuis (`held_conflict`) | `handleUpdateHektorContact` |
| après l'envoi | le pending est **effacé**, puis relecture du contact (~40 s) | `:18380` |
| relecture | la ligne est **remplacée sur place** par Hektor (upsert qui fusionne) ; naissance / lieu / situation **réinjectés** depuis notre ligne | `refresh_contact_inproc.py` → `push_contacts_to_supabase.py:853` |
| la nuit | un contact en attente est **sauté en entier** ; les 3 champs propres à l'app sont gardés | `fetch_dirty_contact_ids` |

⭐ **Une fausse alerte de ma part, retirée par la mesure** : `fetch_app_owned_contact_fields` avale une erreur
(`except Exception: return {}`) — mais l'envoi ciblé est un **upsert qui fusionne**, une ligne sans ces 3 clés
**ne touche pas** les colonnes existantes. Rien ne se perd.

**La mesure — les 13 contacts modifiés, dernier envoi de chacun comparé à la fiche d'aujourd'hui**
*(jointure par les DEUX numéros : depuis la bascule, la fiche porte le nôtre, Hektor est dans `hektor_target_id`)* :

| | contacts |
|---|---|
| identiques à l'envoi | **8** |
| réécrits ensuite par une modification suivante (FERANCK → FERANCKd, 12/10) | 1 |
| **normalisés par Hektor** (FIRMINY → Firminy) | 1 |
| n'existent plus (essais de mai, supprimés) | 3 |
| ⛔ **une valeur PERDUE** | **1** |

⛔ **LE CAS PERDU — 605030 (contact d'essai, mandant de 62774), 08/10** : envoyé `ville = Saint-Étienne` **avec
un code postal VIDE**. Le worker a répondu **« updated »** ; chez Hektor la localité est **vide** (miroir :
`localite.ville = ""`, `code = ""`, `date_maj 08/10 16:39:57`) ; la relecture a remplacé notre « Saint-Étienne »
par ce vide. **Personne ne l'a vu.** ➡ Hektor ne garde pas une ville sans son code postal, **et il n'existe AUCUN
contrôle au retour pour le contact** — exactement le trou que la pièce 3 a bouché pour l'annonce.

**LES TROUS, rangés :**
1. ⛔ **Aucun contrôle au retour** (N.2 pour le contact) : un champ que Hektor ne garde pas est **remplacé en
   silence** par la relecture. Prouvé une fois (605030), sur un essai.
2. ⚠ **Le commentaire n'est PAS écrit chez nous au clic** : `col_map` ne connaît pas `comments` →
   `commentaires`. Il n'apparaît qu'au retour de Hektor, **~11 minutes après** (attente de 10 min + relecture).
   Hektor parti, il ne s'afficherait **jamais** (il resterait dans la charge du travail). 17 978 contacts ont un
   commentaire.
3. ⚠ **Une ville sans code postal est acceptée par l'écran** et perdue chez Hektor (cas 605030). *Non mesuré :
   laquelle des trois fenêtres l'a permis, et si les deux autres l'empêchent.*
4. 📜 **Pas de colonne chez nous** pour société, forme juridique, SIRET, métier, site, les 7 champs du conjoint,
   catégorie, source, 3 réglages CRM — ils ne vivent que chez Hektor. **0 sur 39 charges** les remplissent
   (mesure du 21/10). Sujet de **coupure**, déjà noté.
✅ **Ce qui tient** : les 12 colonnes au clic, la garde anti-écrasement, le contact protégé la nuit, les 3 champs
propres à l'app jamais perdus.

### 8a-A — le commentaire au clic : ÉCRIT, RÉPÉTÉ 8/8, **PAS APPLIQUÉ** *(22/10, Frédéric : « prépare A puis B »)*

**Le patch** : `supabase/patch_8a4_contact_commentaire_au_clic_2026-10-22.sql` (+ `_INVERSE`, + `_REPETITION`),
**générés tous trois depuis les mêmes ancres** (`phase2/checks/gen_patch_8a4_contact_commentaire.py`) pour ne pas
pouvoir diverger.
- un **interrupteur** `contact_commentaire_au_clic`, posé **éteint** ;
- dans `app_edit_contact_optimistic`, **trois ancres d'une ligne** (leçon 30) : allumé, `comments` (ou
  `commentaires`) s'écrit dans la colonne `commentaires` **au clic**, et sa valeur d'avant entre dans la photo
  (`base_snapshot`) comme les 12 autres. **Éteint : rien ne change.**
- **Empreintes calculées d'avance, hors base** : avant **`79d39e0e`**, après **`eb93494b`** ; le patch s'arrête
  si l'une ne colle pas, si une ancre n'est pas trouvée **une** fois, ou si quelqu'un est passé avant.

**La répétition — 8 sur 8**, elle joue le vrai patch puis appelle la fonction **comme l'écran**, au nom de
Frédéric, sur le contact d'essai 20000007, et **s'annule seule** :
T1 éteint → commentaire **inchangé** (témoin inverse) · T3a/T3b le nom s'écrit dans les deux cas · T2a allumé →
commentaire **écrit au clic** · T2b il **part chez Hektor** (ligne d'attente) · T2c la photo porte **sa valeur
d'avant + `_date_maj`** · T4 l'alias `commentaires` marche · T5 **l'inverse rend `79d39e0e`**.
**Vérifié après** : empreinte `79d39e0e`, pas d'interrupteur, contact d'essai intact, aucune ligne d'attente.

**Ce que ça pourrait casser ailleurs — relu :**
- l'envoi à Hektor, l'attente de 10 min, la garde anti-écrasement (elle ne lit que `_date_maj`), la relecture et
  la nuit : **inchangés** ;
- au retour, la relecture remplace le commentaire par celui de Hektor — **même forme** : mesuré, les 17 979
  commentaires chez nous sont du **texte simple** (0 balise, 0 entité HTML, 0 espace en bord ; 38 ont des retours
  à la ligne) ;
- la porte « Modifier un mandant » n'envoie pas de commentaire → **sans effet** sur elle ;
- ⚠ **inchangé, et noté** : l'écran n'envoie **pas** un commentaire **vidé** (`cleanOptionalText` → `null`, non
  envoyé) — on ne peut pas effacer un commentaire depuis l'app, ni avant ni après ce patch.

⛔ **Pour le poser** (accord de Frédéric) : coller le patch → 3 contrôles « OK » → allumer l'interrupteur → essai
réel par l'écran sur le contact d'essai.
