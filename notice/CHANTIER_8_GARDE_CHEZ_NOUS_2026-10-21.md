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
