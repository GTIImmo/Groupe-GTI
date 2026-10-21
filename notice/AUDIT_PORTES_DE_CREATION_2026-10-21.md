# LES PORTES DE CRÉATION — audit transversal, et une méthode pour anticiper l'étape 3

*21/10/2026 — lecture seule. Né du point 8a du chantier ⑧
(`notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md`), à la demande de Frédéric :*
> *« Le but étant d'avoir tous les champs possibles immédiatement saisis chez nous, puis au retour
> du worker faire un contrôle et compléter les champs que seul Hektor peut nous fournir. »*

⚠ **Périmètre de la mesure** : les fonctions de création **relues en base aujourd'hui** sont
contact, mandant créé, mandant rattaché, annonce, recherche, transaction. Photos, documents et
RDV sont décrits **d'après le journal des décisions**, **non remesurés** aujourd'hui.

---

## 1. Les trois mécanismes — à ne pas confondre

| mécanisme | ce qu'il fait | ce qu'il ne fait pas |
|---|---|---|
| **la demande au worker** (`app_console_job.payload_json`) | garde **toute la saisie**, à la seconde, dans la même transaction que la naissance ; jamais effacée *(99 496 demandes, depuis le 14/05)* | elle n'est **lue par aucun écran** |
| **la relecture chez Hektor** (`refresh_console_contact_data`, `refresh_console_data`) | **remplit la fiche** ~40 s (contact) ou ~72 s (annonce) après, depuis la copie de Hektor | elle **disparaît à la coupure** |
| **la doublure** (descente de 07:45, `pull_from_supabase.py`) | **photocopie le cloud** sur le serveur — complète aujourd'hui *(13 496 annonces, 0 détail vide ; 62 281 contacts)* | elle copie la fiche **telle qu'elle est**, elle ne remplit rien |

---

## 2. La situation, porte par porte

| objet | écrit chez nous AU CLIC | complété au retour de Hektor | ce que SEUL Hektor fournit | état |
|---|---|---|---|---|
| **transaction** (offre, compromis, vente) — `app_change_annonce_status_optimistic` | **tout le corps** dans `app_affaire_ledger` (montant, date, acquéreur, chaîne, `payload_json`) | le numéro Hektor de l'affaire, en quelques secondes | `hektor_affaire_id` — *« la case reste VIDE »*, dit la fonction | ✅ **le modèle visé** *(330 nées dans l'app, 0 sans numéro, audit du 08/10)* |
| **mandant rattaché** — `app_link_mandant_optimistic` | le **lien durable** `app_relation` | rien à compléter | — | ✅ *(lien durable à la saisie, 30/09)* |
| **recherche** — `app_create_search_optimistic` | **tous les critères**, mais dans une table **d'attente** (`app_search_provisional`) | la vraie recherche arrive en 30-40 s par la relecture du contact | `idCritere`, la position `search_index` | 🟡 complet, mais pas dans le registre |
| **contact** — `app_create_contact_optimistic` | **7 champs** | toute la fiche ~40 s ; naissance / lieu / situation la nuit | numéro Hektor (`hektor_target_id`), localité typée et coordonnées, `refCouple` (ménage), dates Hektor | 🟠 |
| **mandant créé** — `app_create_mandant_contact_optimistic` | **7 champs** + le lien | idem contact | idem contact | 🟠 |
| **annonce** — `app_create_annonce_job_optimistic` | **11 champs** dans `app_dossier_current` ; **rien** dans `app_dossier_detail_current` | toute la fiche ~72 s *(24/09 : 15 534 octets de détail)* | numéro Hektor, numéro de dossier (VA/EM), `diffusable`, secteur et géolocalisation, numéro de mandat (PROTEXA), dates Hektor | 🟠 *(classé étape 3 le 08/10)* |
| **photo** | chez nous avant Hektor *(journal 14/10)* | | numéro de photo Hektor | ✅ *(non remesuré)* |
| **document** | chez nous avant Hektor *(3d, journal 14/10)* | | `hektor_document_id` | ✅ *(non remesuré)* |
| **numéro de mandat** — `create_hektor_mandat_auto_number` | rien | le numéro | le numéro (série PROTEXA) | ⚪ étape 3 — registre légal A.3 |
| **RDV** | Google, puis le lien chez nous, **sans Hektor** | | — | ✅ *(non remesuré)* |

➡ **Le projet possède DÉJÀ le patron demandé** : c'est celui des **transactions** — tout le corps
écrit au clic, la seule case de Hektor laissée vide, remplie à son retour. **Le contact et
l'annonce ne l'ont pas reçu.** Ils datent de C.9 (31/08) et L4-b (21/09), qui visaient
**« naître avec notre numéro »**, pas **« naître complet »**.

**Pourquoi ce n'était pas une faute** : décisions du **21/09** *(« rien ne doit inverser le courant
aujourd'hui »)* et du **13/10** *(« on ne promeut pas un affichage transitoire en autorité »)*.
Écrire la saisie dans la fiche **comme affichage provisoire**, que Hektor confirme ensuite, **ne
contredit aucune des deux**.

⚠ **Incohérence de classement de l'audit du 08/10** : la création de l'annonce est rangée en
étape 3 *parce que* la fiche revient en ~1 min ; celle du contact est rangée dans ⑧ (étape 2),
alors que sa fiche revient en ~40 s. Même mécanisme.

---

## 2 bis. ⛔ CE QUI EST DÉJÀ FAIT SUR LES CHAMPS — retrouvé après coup *(Frédéric : « on a déjà répertorié les champs annonce et contact »)*

**J'ai proposé de refaire une carte qui existe.** Les études existantes, chacune sur **sa** question :

| date | étude | la question | objet | le résultat |
|---|---|---|---|---|
| 24-26/06 | lots 1-3 contact *(mémoire `contact-mapping-trous-readthrough`)* | que renvoie Hektor pour un contact ? | contact | colonne `adresse` ; naissance/lieu/situation **propres à l'app** ; le lecteur du formulaire |
| 19/08 | **carte A1** — `A1_CHAMPS_PROPRIETE_APP_2026-08-19.md` | **qui est l'auteur** de chaque champ ? *(VERT / BLEU / ORANGE)* | annonce, 189 champs | tout VERT sauf les BLEUS *(numéro de mandat, diffusion, cycle de transaction, photos, agence)* et 3 ORANGE · ⚠ *« contacts et recherches : à traiter à part »* |
| 16-18/09 | campagne **0.1** de l'affaire | Hektor **accepte-t-il** chaque champ ? *(A / B / C)* + verdict au retour | transaction | close le 18/09 ; carnet à 10 colonnes, `etat` + valeur d'avant + valeur relue |
| 21/09 | `CARTE_CHAMPS_ANNONCE_2026-09-21.md` | créable / modifiable ? | annonce, contact | chiffre « 102 » faux *(deux vocabulaires)* |
| 25/09 | `AUDIT_L5_GESTES_MANQUANTS_2026-09-25.md` | créable / modifiable, refait | annonce 178/182 · contact 8/24 | **aucun champ créable sans être corrigible** |
| 28/09 | **N.1** — `phase2/checks/campagne_champs_annonce.py` | Hektor accepte-t-il ? *(A / B / C)* | annonce | **B 24 · A 0 · C 16** → `CHAMPS_APP_ANNONCE` reste vide |
| 28/09 | **N.1-(b)** — `phase2/checks/correspondance_champs_annonce.py` | nom du worker ↔ colonne / clé de blob | annonce | **189 sur 189**, 9 ambigus |
| 28/09 | **N.2 redessinée** *(plan l. 478-480)* | après la relecture, **ce qui est REVENU = ce qui a été ENVOYÉ ?** | annonce | ⬜ **pas faite** |
| 28/09 | « 🎯 FINIR L'ANNONCE » *(plan l. 421-440)* | l'annonce au niveau des trois autres | les 4 objets | le tableau de comparaison |
| — | `phase2/identite/contrat_autorite.py` | sur quel champ **l'app gagne** ? | tous | contact : 3 · annonce : vide · affaire : vide · mandat : allumé |

**Ce qu'aucune de ces études n'a posé** : *la création écrit-elle la saisie DANS LA FICHE,
tout de suite ?* Elles portent sur l'**envoi** vers Hektor, la **redescente**, la
**correction** — pas sur la **naissance**. Et le **contrôle au retour** existe pour la
**transaction**, est **dessiné** pour l'annonce *(N.2, non faite)*, **n'existe pas** pour le contact.

➡ **La méthode ci-dessous est donc corrigée** : son étape ① est **déjà faite** pour l'annonce
*(A1 + N.1 + N.1-(b))* et en partie pour le contact ; son étape ③ **est N.2**.

## 2 ter. ⛔⛔ ET LE PROJET AVAIT DÉJÀ ÉCRIT LA MÉTHODE — audit poursuivi *(Frédéric : « ne t'arrête pas à la première découverte »)*

**Les 46 chapitres du 07/10** (`notice/CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md`, plan
l. 304-388, *refusés le 08/10 parce qu'ils mêlaient étapes 2 et 3*) portaient **exactement**
l'objectif de Frédéric, tâche par tâche :

| chapitre | tâche | ce qu'elle dit | état au 21/10 |
|---|---|---|---|
| **CH19** | **L10-2d** | *« Une annonce créée dans l'app a **tous ses champs chez nous dès le geste** »* — méthode écrite : **extraire la carte des champs de `app_edit_annonce_optimistic` dans une fonction partagée, écrire `app_dossier_detail_current` à la création, derrière un réglage NEUF**. Fin : *« 0 écart champ à champ avec la charge envoyée à Hektor »* | ⬜ jamais commencée |
| CH19 | 26bis-3a | le serveur tient le corps d'une annonce que le miroir ignore (`--injecter`) | ⬜ |
| **CH17** ⏳ | **26bis-3b** | *« Comparer tant que Hektor vit »* : la copie du cloud vaut-elle le miroir ? | ✅ **mesuré le 28/09 (N.4)** : 189 champs présents, 0 absent |
| CH17 ⏳ | C.9-couple-b | l'app fabrique la paire du ménage | ⬜ — c'est **8g** |
| **CH24** | **L10-2b** | la recherche naît chez nous : durable, numérotée, rapprochée tout de suite | ⬜ |
| **CH25** | **L10-2c** | les mandants saisis à la création d'une annonce sont écrits chez nous | ⬜ |
| CH8 | L10-2a | le balayeur n'efface plus rien de non traité | 🟡 **mesuré aujourd'hui** : les erreurs sont gardées **7 jours** (plus 24 h), les « reliées » effacées après 24 h |
| CH41 | 26bis-3c | le corps serveur de l'annonce lu depuis le cloud, derrière un interrupteur éteint | ⬜ |
| — | **N.2 redessinée** (plan l. 480) | **le contrôle au retour** : *« comparer, après la resynchro, ce qui est REVENU à ce qui a été ENVOYÉ, champ par champ »* | ⬜ |

**Et les champs que seul Hektor fournit ont déjà leurs deux listes** : la colonne **BLEU** de la
carte A1 *(numéro de mandat, état de diffusion, cycle de transaction, photos hébergées, agence)*
et `notice/ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20.md` *(seuls **3** workers dépendent
de Hektor parce qu'il **produit** quelque chose : numéro de mandat, relance et annulation de
signature — les 31 autres parce qu'il **détient** la donnée)*.

**Ce qui a fait disparaître ces tâches** : le 08/10, les 46 chapitres ont été remplacés par les
8 chantiers, et l'audit par objet a classé « naître sans Hektor » en **étape 3**. Aucune des
tâches ci-dessus n'a été reprise dans ①-⑧ — **sauf, pour le contact, la ligne « 6 champs à la
création » de ⑧**.

⚠ **LE VRAI TROU DU PLAN** : il n'existe **aucune** tâche « le corps complet du **contact** à la
naissance » *(ni dans les 46 chapitres, ni dans L10)*, et **aucun** contrôle au retour pour le
contact. Le contact n'a que **8a**.

⏳ **La péremption est écrite** *(journal de bord, l. 1257)* : *« N.4 LE CORPS LOCAL DE
L'ANNONCE : son remplissage vient du MIROIR, donc il exige que Hektor vive encore. »* Le contrôle
au retour aussi : **il ne peut se faire que tant que Hektor répond.**

## 2 quater. AUDIT APPROFONDI — 21/10, après la décision « A maintenant » de Frédéric

**① La demande au worker N'EST PAS un lieu sûr pour la saisie** *(ma phrase « jamais effacée »
était FAUSSE)*. Deux nettoyages délibérés l'ont prouvé :
- **21/08** : les travaux en erreur ont été **supprimés**, seul un **compte** a été gardé
  (`app_console_job_error_archive` : `job_type, motif, combien, premier, dernier` — **sans la
  saisie**). Dont **19 créations d'annonce** *(15/05 → 23/07)* et **2 de contact** *(29/05)* ;
- **15/10** : 33 travaux en erreur supprimés, **avec** une sauvegarde datée complète
  (`app_console_job_erreurs_avant_purge_2026_10_15`, `payload_json` compris).
➡ C'est une **file de travail**, pas un registre. La saisie doit vivre **dans la fiche**.

**② L'annonce, relue en base** :
- `app_create_annonce_job_optimistic` *(interrupteur `c9_annonce_nait_dans_app` allumé)* : 11
  colonnes dans `app_dossier_current`, **aucune ligne** dans `app_dossier_detail_current` ;
- `app_edit_annonce_optimistic` (empreinte `5eb2c1a4…`) écrit le **calque**
  `app_optimistic_overlay` par un **UPDATE** de la ligne détail — ⚠ **à vérifier** : sur une
  annonce née il y a moins d'une minute, cette ligne n'existe pas encore ;
- la **carte des champs** (`col_map`, `json_map`) est **recopiée à l'identique** dans
  `app_annonce_reappliquer_saisies` *(le commentaire le dit)* — c'est ce que L10-2d voulait
  extraire en une fonction partagée ;
- au retour, la relecture (`push_single_annonce_to_supabase.py`) **remplace** la fiche par celle
  de Hektor, **puis** repose les saisies encore en attente (L3, `reappliquer_saisies_app`) ;
- **le calque disparaît au retour** : 73 modifications passées, **0** calque restant en base.

**③ Le contrôle au retour qui EXISTE — celui de l'affaire** (`console_job_worker.js:15040-15080`) :
champ par champ, `arrivee` → la ligne est retirée du carnet, sinon `etat` + `valeur_hektor_relue`
+ `constate_le`. **Utilisé 9 fois, la dernière le 18/09.** ⚠ 17 lignes au carnet de l'affaire
*(04/09 → 13/10)* n'ont **aucun** verdict — non expliqué, à regarder.

**④ Le contact au retour** : la ligne est **remplacée** par celle de Hektor ; seuls les 3 champs
propres à l'app sont **réinjectés** (`fetch_app_owned_contact_fields`). **Aucune comparaison**.

**⑤ Les mandants saisis à la création d'une annonce** : envoyés chez Hektor pendant la création ;
un échec se **voit** depuis 4a (`bilanSuiteCreationIncomplete`, `:18892`) ; le lien n'est **pas**
écrit chez nous au clic — c'est **L10-2c**, toujours ouverte.

**⑥ Trouvailles HORS SUJET — notées, non traitées** :
- **9 annonces** portent une saisie en attente `source = 'diffusion'`, **sans champ**, posées du
  12/10 au 20/10, jamais transformées en travail. Or la relecture **saute** une annonce qui a une
  saisie en attente (`dirty_annonce_skipped`, `push_single_annonce_to_supabase.py:846-853`) —
  ⚠ **à vérifier** : sont-elles figées depuis ? *(un verrou de diffusion à délai existe,
  `diffusion_lock_expired`, non lu en entier)* ;
- les 17 lignes de carnet d'affaire sans verdict *(ci-dessus)*.

## 2 quinquies. LES RELECTURES APRÈS UN GESTE — audit du 21/10 *(Frédéric : « audit et explique les différents mécanismes de relecture »)*

**Ce qu'est une relecture** : après un geste envoyé à Hektor, le worker met en file un second
travail qui relit l'objet **chez Hektor** et recopie sa version chez nous. C'est un **complément** :
le geste, lui, est déjà fait. **Deux sortes**, recensées dans `console_job_worker.js` :

| relecture | appelée | numéro reçu | programme | mesuré depuis le 24/09 |
|---|---|---|---|---|
| **annonce** — `refresh_console_data` | **27** endroits *(statut, champs, photos, mandant, création…)* + l'ouverture d'une fiche | le numéro Hektor de l'annonce | `refresh_single_annonce.py` → `push_single_annonce_to_supabase.py` | **551 `done`, 0 erreur**. Ouverture : **506 / 506** écrivent la fiche. Après un geste : **36** écrivent la fiche, **8** écrivent l'index des **archives** ou des **vendus/clos** *(l'annonce venait d'y passer : c'est le bon endroit)*. ✅ **100 % efficace** |
| **contact** — `refresh_console_contact_data` | **13** endroits + l'ouverture d'une fiche | **notre** numéro *(ouverture, modification, archivage)* ou **le numéro Hektor** *(création, mandant, 3 gestes de recherche, qualification)* | `refresh_contact_inproc.py` | avec notre numéro : **74 / 75** écrivent la fiche *(1 sans écriture)*. ⚠ **avec un numéro Hektor dont la paire est connue : 0 écriture** *(08/10 sur un contact d'essai ; essai du 21/10)* |

**Les autres retours ne passent PAS par une relecture** :
- **transaction** : le worker écrit lui-même le numéro de Hektor dans le registre
  (`app_affaire_ledger`, `:21030`) puis **ce que Hektor a retenu** (`reporterAuRegistre`, `:15090`).
  **331 affaires nées dans l'app, 0 sans numéro Hektor**. ✅
- **photo, document** : écrits **chez nous avant Hektor** (chantier ③, 14/10), puis une synchro dédiée
  (`sync_hektor_photos`, `sync_console_documents`). **7 envois** depuis le 24/09, tous `done`. ✅
- **lien mandant existant** : la ligne durable `app_relation` est posée **au clic** (30/09). ✅

**Ce qui reste cassé, et seulement ça** : la relecture **de contact** reçue avec le **numéro Hektor**
d'un contact **déjà connu**. Elle lit bien Hektor, reconstruit la fiche **sous notre numéro**, puis
envoie sous **le numéro Hektor** → **rien n'est envoyé**. Effet **visible** sur un seul geste :
**ajouter une recherche** — la vraie recherche *(celle qui compte pour les rapprochements)* n'arrive
chez nous **qu'au run de la nuit** : jusque-là, l'acquéreur n'est **rapproché d'aucun bien**. *(Aucun
ajout de recherche depuis l'app depuis le 17/09 : effet lu dans le code, pas observé.)* Pour les
autres gestes *(mandant, modification ou suppression de recherche)*, l'app a déjà écrit la saisie :
**aucun effet visible**. ⭐ **Le contact neuf est déjà corrigé** *(16:40)*.

## 3. ~~LA MÉTHODE PROPOSÉE~~ — ⛔ **REMPLACÉE par CH19 + N.2 ci-dessus** *(gardée pour mémoire : elle redisait, moins bien, ce qui était écrit le 07/10)*

**① Une carte de champs PAR OBJET, mesurée, à quatre colonnes** *(sur le modèle de
`CARTE_CHAMPS_ANNONCE_2026-09-21.md`, mais pour la création)* :
`saisi dans l'app` · `écrit au clic` · `renvoyé par Hektor` · `fabriqué par Hektor SEUL`.
Mesurée en comparant, sur de vraies créations, **la demande** et **la fiche revenue** — jamais
lue dans les notes.

**② La création écrit TOUT ce qui est saisi, dans la fiche, tout de suite** — le patron des
transactions. Les cases « Hektor seul » restent **vides** (pas inventées). Pour l'annonce, le
véhicule **existe déjà** : le **calque** `app_optimistic_overlay` que la modification écrit
dans `detail_payload_json`, et que l'écran lit **en premier** *(01/07, `efd32e2`)*.

**③ Au retour du worker, un CONTRÔLE champ par champ** :
- une case « Hektor seul » → on la **remplit** ;
- un champ saisi, **égal** chez Hektor → rien ;
- un champ saisi, **différent** chez Hektor *(il a transformé : ville typée, arrondi, libellé)* →
  pendant l'étape 2, **la version de Hektor reste** *(décision du 13/10)*, **mais l'écart est
  noté** — c'est la mesure de ce que l'app ferait mal toute seule ;
- jamais « vide gagne » *(règle du 13/10)*.

**④ La liste « Hektor seul » devient la liste de l'étape 3** : pour chaque case, qui la
fabriquera après la coupure — nos numéros *(les séries ≥ 10 M existent déjà)*, le numéro de
dossier, la géolocalisation, le numéro de mandat *(registre légal, A.3)*, `diffusable`, le
ménage *(C.9-couple, 8g — à mesurer tant que Hektor vit)*.

**⑤ Le jour de la coupure**, il ne reste qu'à **éteindre la relecture** : la fiche est déjà
complète à la naissance, et les écarts notés ont dit ce qu'il faut corriger avant.

### Ce que ça ne change pas
Le circuit d'envoi vers Hektor, la décision « Hektor fait foi » pendant l'étape 2, les
interrupteurs `CHAMPS_APP_*` *(restent éteints)*, les doublures.

### Ce qui n'est PAS décidé — à Frédéric
- est-ce dans ⑧ (étape 2), ou un chantier à part qui prépare l'étape 3 ?
- par quel objet commencer ?
