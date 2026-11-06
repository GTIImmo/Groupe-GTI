# Audit — un registre des négociateurs à nous (04/11/2026)

> Frédéric, 04/11 : « normalement tous les registres restent chez nous donc Hektor ne devrait pas l'écraser », « il n'y a
> pas des négociateurs anciens chez nous qui ne sont pas chez Hektor ? », puis « Oui, audite ».
> **Audit seulement : rien n'est codé, rien n'est écrit en base.** Point de départ : `AUDIT_PILOTAGE_GLOBAL_2026-11-02.md`
> §40 bis à §40 quinquies.

## 1. Le projet a DÉJÀ ce chantier au plan

- **Chapitre 26 du plan, « L'annuaire des négociateurs devient le nôtre » (L10-11-c, 3-5 j)**, + l'ajout du 26/10
  « les AGENCES et les MENUS (filtres, formulaire de création) tirés de nos annuaires » (`PLAN_DEV_ACTUALISE_2026-08-20.md` l. 372).
- **B11 de l'audit du 07/10, BLOQUANT** (`AUDIT_AUTONOMIE_COMPLET_2026-10-07.md` l. 510) : l'annuaire est recopié de
  Hektor chaque nuit ; créneaux RDV, répartition, Google Agenda et vitrine sont rangés sous le numéro Hektor ; **un
  nouveau collaborateur se crée dans Hektor (décision du 19/09)** ; après la coupure, un négociateur embauché n'existerait
  nulle part. **A12** du même audit : « annuaire à nous, création d'un collaborateur, droits réécrits (F.1 avant E.2),
  comptes, puis E.2 » — marqué « oublié ».
- **B6 / L10-8e (chapitre 5, « les planchers Hektor répond vide »)** : l'étape de l'annuaire « efface sans plancher ».
- **1.7 « Annuaire négociateurs → reporté au jour J »** : le worker a besoin de l'`idUser` Hektor pour s'impersonner.
- Les méthodes déjà posées pour les fiches multiples : **C.18 (28/08)** dans le worker ; **`app_mes_chaines_nommees()`
  (31/10)** dans les droits du registre — la personne = les fiches de l'annuaire au même e-mail.

⇒ Ce qui est demandé aujourd'hui, c'est **d'avancer une partie du chapitre 26**. L'ordre du plan ne se change pas sans
Frédéric : c'est la première décision (§7).

## 2. Ce que nous avons aujourd'hui — mesuré

**Trois tables, toutes des COPIES de Hektor :**
- `data/hektor.sqlite` → `hektor_negociateur` (219 fiches) : écrite chaque nuit par `upsert_negos`
  (`normalize_source.py:556`) en upsert. ⭐ Une fiche n'est **jamais supprimée** ; ⚠ mais **n° d'utilisateur, agence, nom,
  prénom, e-mail, téléphones sont RÉÉCRITS** par ce que Hektor dit ce soir-là.
- Supabase `app_hektor_negotiator_agency_directory` (219) : reconstruite chaque nuit depuis la table locale
  (`phase2/sync/push_hektor_directory_to_supabase.py`), puis `delete_missing` ; `is_active` = la liste des actifs de Hektor.
- Supabase `app_user_directory` (49) et `app_agence_directory` (20) : reconstruites depuis l'API de Hektor, puis
  `delete_missing` **SANS PLANCHER** (l. 415-424) — ⛔ une réponse vide de Hektor viderait les deux, et les patchs de droits
  exigent une présence NEGO dans `app_user_directory`. C'est le B6 du 07/10, toujours ouvert.

**Aucun historique.** `raw_api_response` ne garde que la DERNIÈRE réponse de chaque page (mesuré : `list_negos` pages 0-2
du 04/11, pages 3-4 restées du 03/04 ; `list_negos_inactive` pages 0-4 du 04/11, 5-8 du 05/06). Le « 0 changement »
qu'on en tire **ne prouve rien** : on ne sait pas si Hektor a déjà changé une fiche.

**Les fiches** : la dernière liste de Hektor (04/11 03:55) porte 186 fiches ; nous en avons 219.
- **33 n'existent plus que chez nous** (§40 quinquies) — dont 6 portent des données : Aline VALETTE 42 (960 annonces,
  2 918 contacts), Pauline GIRINON 16 (163 / 4 929), Delphine BLANCHARD 21 (15 / 3 871), Caroline GERPHAGNON 24
  (245 / 2 731), Franck GERPHAGNON 19 (170 / 20), Frédéric GERPHAGNON 20 (41 / 12).
- **Une personne = plusieurs fiches** (une par agence, même e-mail) : 19 personnes actives, « Groupe GTI » 11 fiches.
  L'annuaire est cohérent aujourd'hui : 0 e-mail à deux noms, 0 nom à deux e-mails ; 13 fiches sans e-mail.
- **5 numéros d'utilisateur de la répartition n'ont AUCUNE fiche** (1 364 lignes) : 0 et 24 « Cet utilisateur a été
  supprimé » (460 et 145 dossiers), comptes d'agence Annonay 17, Firminy 19, Ambert 23.
- **14 anciens du classeur** (2017-2025, avant Hektor) : un nom, aucun numéro.

**Les comptes de l'app** (`app_user_profile`, 8 comptes) : reliés à leur fiche par l'e-mail. 2 commerciaux actifs, fiche
active tous les deux ; sans fiche : le compte d'essai `codex.test@`, `franck.gerphagnon@gti-immobilier.fr` (admin), un
commercial inactif.

## 3. Qui lit et écrit l'identité d'un négociateur (inventaire du code, 04/11)

**Écrivent** : `upsert_negos` (local, upsert, jamais de suppression) ; `push_hektor_directory_to_supabase.py` (l'annuaire
des fiches depuis le local ; les comptes `app_user_directory` = comptes directs du compte parent + négociateurs ACTIFS,
forcés NEGO ; puis `delete_missing` — ⇒ **un négociateur devenu inactif SORT de `app_user_directory` la nuit même**) ;
`backend/app/services/supabase_admin.py:159` (photo `app_google_workspace_identity`, au dernier contrôle) ;
`app_repartition_commission_set` et `phase2/sync/repartition_commission.py:223` (`nom_au_moment`, figé à vie).

**Le worker** (écrire chez Hektor sous une identité) : `resolveHektorExecutionUser` l. 2488 (n° d'utilisateur du travail,
puis le propriétaire du dossier, puis les e-mails), `resolveHektorNegotiatorFromAgencyDirectory` l. 2437 (n° de
négociateur, e-mail, départagé par l'agence — C.18), `isOwnerNegotiatorActive` l. 2917, `ensureHektorExecutionContext`
l. 2952 (36 appels ; `CONSOLE_HEKTOR_AGENCY_FALLBACK=true` en production : un propriétaire inactif écrit par l'agence),
`mandataireDuMandat` l. 6343 (signature), `handleAssignHektorAnnonceNegotiator` l. 17299.

**Les droits** (clé : l'e-mail du compte de l'app) : `can_access_negotiator_email`, `app_mes_biens_portefeuille`,
`app_mon_agence` (+ `app_voit_cette_ligne`, `app_voit_ce_dossier_selon_perimetre`), `app_mes_chaines_nommees` (tous les
n° d'utilisateur à mon e-mail), `app_console_resolve_contact_hektor_user`.

**Le front** : `loadUserNegotiatorContext`, `loadHektorNegotiatorOptions` (actifs), `loadNegotiatorOptionForContact`,
`loadRepartitionPersonnes`, `loadNomsNegociateurs`, et le pilotage (`lireAnnuaire`, `construireRepere`).

**Les copies du nom et de l'e-mail** sur les dossiers, le registre des mandats et les contacts sont refaites chaque nuit
(`build_case_index.py`, `view_generale.py`, `export_app_payload.py`, `build_contacts_layer.py`) depuis la fiche du jour.

### 3 bis. Deux défauts trouvés en passant — la confusion des deux numéros, DANS LE CODE

- ⛔ **Les rendez-vous donnent le téléphone d'une AUTRE personne** — `backend/app/services/appointment_service.py:317`
  `_load_contact_details` : si l'e-mail du négociateur n'est pas dans `app_user_directory` (le cas de TOUT inactif, purgé
  la nuit), il cherche `id_user = commercial_id`, c'est-à-dire un n° de négociateur pris pour un n° d'utilisateur. Le
  téléphone trouvé est recopié dans `app_appointment_public_link`.
  **Mesuré** : 178 liens publics sur les 1 516 qui portent un téléphone l'ont pris chez une autre personne (47 un autre
  négociateur, 36 une secrétaire, 95 un compte d'agence) — Mélanie LEGRAND → Caroline GERPHAGNON, Alice RONDEAU → Pauline
  GIRINON, Aline VALETTE → Dylan JOURGET… ; créés du 29/04 au 09/07 ; **un seul encore actif : annonce 33220, Hugo LABBE,
  téléphone de Lucille FORLICO**. Exposition aujourd'hui : 816 biens vivants retomberaient sur ce chemin.
- ⚠ **Le worker a le même piège, endormi** — `console_job_worker.js:2538` (`dossier_commercial_id_legacy`) :
  `loadHektorDirectoryUserById(dossier.commercial_id)`. 20 des 41 n° de négociateur en usage tombent sur le compte d'une
  autre personne (Aline VALETTE 42 → compte de Dylan JOURGET, Mélanie LEGRAND 5 → compte de Caroline GERPHAGNON).
  **Mesuré** : jamais utilisé — 0 ligne sur les ~5 500 travaux journalisés depuis le 15/05 (sources réelles :
  `dossier_commercial_id_agency` 5 237 travaux, `payload_agency_directory` 153, `payload` 36, `email` 33). Il ne sert que
  si l'annuaire par agence échoue ; il endosserait alors QUELQU'UN D'AUTRE chez Hektor.

## 4. Le tableau des gestes — objet « négociateur »

- **créer** : chez Hektor seulement (décision du 19/09) ; chez nous il ARRIVE la nuit. L'app ne crée pas de négociateur.
  Le compte de l'app se crée dans l'outil « Utilisateurs » (l'app est maître), relié par l'e-mail.
- **modifier** : chez Hektor seulement ; notre copie est RÉÉCRITE chaque nuit, sans trace.
- **supprimer / archiver** : chez Hektor (inactif, ou utilisateur supprimé → « Cet utilisateur a été supprimé » dans la
  page des commissions) ; chez nous la fiche locale reste, `is_active` passe à faux. Aucun geste dans l'app.
- **lire** : menus de choix (actifs de l'agence), résolution du worker pour écrire chez Hektor, droits (portefeuille,
  dossiers nommés), répartition, RDV et vitrine, Google Agenda, pilotage.
- **relation négociateur ↔ compte de l'app** : par l'e-mail, sans table de lien.
- Objets voisins : annonce / contact / mandat portent le n° de négociateur (`commercial_id`, `hektor_negociateur_id`) et
  une copie du nom ; transaction : la répartition porte le n° d'utilisateur + `nom_au_moment` (gardé à vie).

## 5. Ce que ça pourrait casser ailleurs

- **Tout ce qui lit l'annuaire suit Hektor le soir même** : si Hektor change l'e-mail d'une fiche, les copies des dossiers
  suivent mais pas le compte de l'app → le négociateur perd son portefeuille, ses dossiers nommés, son agence ; si une
  adresse est réattribuée, des parts anciennes changent de personne. Rien ne le signalerait (pas d'historique).
- **Un négociateur qui devient inactif** sort la nuit même de `app_user_directory` : le worker passe par l'agence (prévu),
  les rendez-vous tombent sur le mauvais téléphone (§3 bis), la signature retombe sur l'expéditeur.
- **Une réponse vide de Hektor** viderait `app_user_directory` et `app_agence_directory` (pas de plancher).
- Un registre à nous **ne casse rien s'il est posé à côté** (lu par personne au début) ; il ne change quelque chose que
  quand un lecteur bascule dessus — et chaque bascule touche du code qui marche (droits, worker) : une à la fois, avec
  témoin.

## 6. Proposition — en trois temps, du plus sûr au plus engageant

**A. Les défauts, à part** (indépendants du registre) :
- A1 rendez-vous : ne plus chercher un n° de négociateur parmi les comptes ; prendre le téléphone sur la fiche du
  négociateur (`app_hektor_negotiator_agency_directory.telephone/portable`, par son n°) ; puis **réparer les 178 liens**
  (écriture en production, sauvegarde datée, retour arrière) — le lien actif de 33220 d'abord ;
- A2 worker : retirer le recours `dossier_commercial_id_legacy` (jamais servi) ;
- A3 les planchers de la purge des comptes et des agences (L10-8e, chapitre 5).

**B. Le registre, à côté, dormant** (une partie du chapitre 26, additive) :
- `app_negociateur_personne` — NOTRE numéro de personne (une plage à nous, hors de celle de Hektor), son nom, son e-mail
  principal, actif ou ancien, d'où elle vient ;
- `app_negociateur_fiche` — chaque fiche Hektor (n° de négociateur, n° d'utilisateur, agence), **rattachée une fois pour
  toutes** à une personne, avec ce qu'elle disait la première et la dernière fois, et « encore chez Hektor » oui ou non ;
- `app_negociateur_journal` — chaque changement d'une fiche (champ, avant, après, nuit) ;
- rempli une fois depuis les 219 fiches + les 5 n° d'utilisateur sans fiche (« supprimé », comptes d'agence) ; les 14 du
  classeur plus tard (chantier classeur) ;
- chaque nuit, après l'annuaire : comparer, **journaliser**, ajouter les fiches nouvelles (rattachées par l'e-mail si
  c'est sans ambiguïté, sinon personne nouvelle + signal), **ne jamais supprimer ni re-rattacher seul** ; un changement
  d'e-mail ou de n° d'utilisateur = une sentinelle, pas une modification silencieuse.

**C. Les lecteurs basculent, un par un** (chaque fois un « vas-y ») : pilotage, `app_mes_chaines_nommees`, résolution du
worker, rendez-vous, menus. Puis, à l'étape 3, créer un collaborateur dans l'app (la décision du 19/09 « il se crée dans
Hektor » serait à revoir à la coupure).

## 7. Ce qui se décide avec Frédéric

1. **A1** : corriger le téléphone des rendez-vous, et réparer les 178 liens (dont l'actif de 33220) ?
2. **B** : avancer maintenant une partie du chapitre 26 (le registre dormant + son journal), ou le garder à sa place ?
3. **A2 et A3** : les faire avec A1, ou à leur place dans le plan (A3 = chapitre 5) ?
4. La plage de nos numéros de personne (proposition : ≥ 1 000 000, comme les relations et les mandats posés par l'app).

## 8. LA DÉCISION DE FRÉDÉRIC (04/11) — son propre registre, sur le modèle des autres

> « Je veux faire mon propre registre des négociateurs comme contacts, annonces etc… mais ne pas perdre les anciens
> inactifs, que mon app lise direct ce registre, on utilise encore les anciens ID Hektor comme aujourd'hui pour les
> workers etc… comme les autres registres. »

**Le modèle des autres registres, relu** (`phase2/identite/registre_contacts.py`, commentaires de `app_mandat`,
`app_relation`, `app_affaire_ledger`) : NOTRE numéro, le numéro de Hektor à côté (vide pour ce qui naît chez nous),
**une ligne n'est jamais supprimée** (`absent_depuis` / `present_in_hektor = false`), maintenu CHAQUE NUIT après la
couche qui fabrique la source, idempotent.

**Ce que ça donne pour les négociateurs — mesuré le 04/11** : 219 fiches Hektor → **168 personnes** (regroupées par
e-mail, à défaut par nom), dont **30 actives** et 25 à plusieurs fiches ; + 5 numéros d'utilisateur sans fiche ; + les 14
anciens du classeur (plus tard). Numéros Hektor : négociateur jusqu'à 225, utilisateur jusqu'à 268.

Deux niveaux, parce qu'une personne a plusieurs fiches chez Hektor :
- **la personne** — notre numéro, nom, e-mail, actif ou ancien, et son compte de l'app ;
- **ses fiches Hektor** — n° de négociateur + n° d'utilisateur + agence, rattachées une fois pour toutes ; **ce sont ces
  numéros que les workers continuent d'utiliser**, comme aujourd'hui.

## 9. Les deux arrivées — un nouveau négociateur dans Hektor, un nouvel utilisateur dans l'app (04/11)

**Aujourd'hui, mesuré dans le code** :
- **un négociateur créé dans Hektor** (décision du 19/09) arrive LA NUIT : `list_negos` → `upsert_negos` → annuaire
  (actif) → `app_user_directory` (NEGO) → il paraît dans les menus le lendemain matin. Il n'a pas de compte dans l'app
  tant qu'un admin ne l'a pas créé ;
- **un utilisateur créé dans l'app** (outil « Utilisateurs », `backend/app/services/supabase_admin.py:379` `create_user`,
  e-mail @gti-immobilier.fr obligatoire) est relié à Hektor **une seule fois, à la création**, par son e-mail
  (`_resolve_hektor_google_identity` l. 55 → `app_google_workspace_identity`). ⚠ C'est une PHOTO : si le compte est créé
  avant que sa fiche Hektor existe ou soit descendue, le lien reste vide et n'est jamais refait seul. Mesuré : 6 photos,
  toutes de juin et d'octobre ; Pauline GIRINON, Franck GERPHAGNON et Frédéric GERPHAGNON « liés » sans aucun numéro Hektor.
- les droits, eux, passent par l'e-mail du compte (§3) : ils marchent dès que les copies de la nuit portent cet e-mail.

**Avec le registre** — il devient le point qui relie les trois : la personne ↔ ses fiches Hektor ↔ son compte de l'app.
- **Nouveau négociateur dans Hektor** : la nuit, sa fiche est adoptée. Son e-mail est déjà celui d'une personne (une
  nouvelle agence pour quelqu'un de connu) → rattachée à elle ; c'est l'e-mail d'un compte de l'app sans personne → la
  personne est créée et reliée au compte ; inconnu → personne créée, marquée « nouvelle », et un signal. Jamais de fusion
  ni de déplacement automatique au-delà de ces cas sans ambiguïté.
- **Nouvel utilisateur dans l'app** : à la création, l'outil cherche la personne au même e-mail → reliée ; sinon une
  personne « sans fiche Hektor » est créée, et sa fiche s'y rattachera seule la nuit où elle arrivera. Pour les cas
  tordus (e-mail gmail contre e-mail de l'agence, comme Franck), un choix manuel de la personne dans l'outil.
- **Hektor reste celui qui crée les fiches et les numéros** tant qu'il vit (décision du 19/09 inchangée) ; le registre ne
  fait que les ADOPTER, comme `app_contact` adopte les contacts.
- À trancher en route : le type de personne (négociateur, secrétaire, compte d'agence comme « Groupe GTI » / accueil@) et
  les 13 fiches sans e-mail (rattachées par le nom → liste à valider par Frédéric).

## 10. Étape 1 PRÉPARÉE (04/11) — Frédéric : « Oui, prépare l'étape 1 » — ⛔ RIEN N'EST POSÉ

- Patch : `supabase/patch_registre_negociateurs_2026-11-04.sql` ; retour arrière `…_INVERSE.sql` (les trois tables).
  Garde au départ (s'arrête si une table existe déjà) ; contrôles à la fin (toutes les fiches de l'annuaire et tous les
  n° d'utilisateur de la répartition ont leur place, aucune personne sans fiche) — un contrôle faux annule tout.
  Droits : lecture pour les comptes actifs de l'app (comme l'annuaire), le journal pour les admins ; aucune écriture par l'API.
- **Les sources** : les 219 fiches de l'annuaire ; les comptes de `app_user_directory` qui n'ont pas de fiche
  (14 agences, 5 secrétaires) ; les n° de la répartition qui n'ont rien (0, 24, 23).
- **Trois pièges trouvés en le préparant, et traités** :
  - le compte Hektor « Compte Formation » (u1) porte l'adresse de Frédéric ; Tence et Yssingeaux partagent `yssingeaux@` ;
    Pauline GIRINON a un compte de secrétaire sous une adresse gmail au nom de Sasha ⇒ **les agences ne se réunissent
    jamais par l'e-mail** (une personne par agence), et une personne citée sous deux adresses est réunie par son nom,
    marquée à valider ;
  - mon premier essai perdait les n° de la répartition sans fiche : une colonne sans nom dans une sous-requête lisait la
    colonne de la requête extérieure (`select u_id from comptes` = toujours vrai) — colonnes nommées partout ;
  - 17 personnes ont pour e-mail une boîte d'agence (craponne@, gtiimmobilier.ambert@wanadoo.fr…) ⇒ marquées « e-mail
    partagé », pour qu'à l'étape 2 la nuit ne s'en serve jamais pour rattacher une nouvelle fiche.
- **L'essai (tables temporaires, rien ne reste)** : 187 personnes, 241 fiches ou comptes — 167 négociateurs dont 33 actifs,
  18 agences, 2 utilisateurs supprimés ; 5 comptes de l'app reliés. Liste : `REGISTRE_NEGOCIATEURS_A_VALIDER_2026-11-04.md`.
- ⛔ **Frédéric : « je retrouve pas mon compte », « j'ai un compte admin chez Hektor »** (04/11). Mesuré : le compte
  ADMINISTRATEUR de Hektor n'est dans AUCUNE de nos tables — `push_hektor_directory_to_supabase.py:144` ne lit que
  `/Api/User/UsersOfParent/` (les comptes SOUS le compte principal), jamais le compte principal lui-même (le n° 4 manque
  dans la suite 1-21). Le journal du worker le connaît : « Session Hektor administrateur active », `user_id 4`, rôle
  ADMIN, alias « GROUPE GTI IMMOBILIER » (3 354 sessions en 3 jours). Dans l'essai, Frédéric n'apparaît que par sa fiche
  n° 20 (Firminy, plus listée) ⇒ classé « ancien », et le compte Hektor « Compte Formation » (u1, type AGENCE) porte son
  adresse. ✅ **Vérifié dans son Chrome le 04/11** (lecture seule) : le compte connecté chez Hektor est « GROUPE GTI
  IMMOBILIER — Administrateur », en tête de l'organigramme, au-dessus des 4 secrétaires (Delphine BLANCHARD, Caroline
  GERPHAGNON, Franck GERPHAGNON, Pauline GIRINON) puis des agences (« AGENCES SUPPRIMÉE », « COMPTE FORMATION »…) — le même
  nom et le même rôle que le compte n° 4 du worker. ⇒ **son compte admin = u4, partagé avec le worker.** Restait : Le patch devra l'ajouter (source : le journal du worker, faute
  de lecture par l'API), et le type de sa personne (dirigeant / administrateur).
- ✅ **LISTE VALIDÉE PAR FRÉDÉRIC le 04/11** (« je valide »), sur `REGISTRE_NEGOCIATEURS_CORRESPONDANCE_2026-11-04.csv`
  (185 personnes, 242 fiches) : les rattachements tels quels, y compris les 4 secrétaires rangées « négociateur », les 11
  fiches sans e-mail réunies par le nom, les agences (Firminy avec « gti immobilier » et « Négo GTI »), et lui-même
  administrateur avec le compte n° 4.
- ⚠ La dernière marque (« e-mail partagé ») a été ajoutée après le dernier essai complet : la pose la vérifiera (une erreur
  de texte annule toute la pose, rien ne resterait à moitié).


## 11. ✅ ÉTAPE 1 POSÉE EN PRODUCTION (04/11) — Frédéric : « Oui, pose-la »

- Migration `registre_negociateurs_etape1_2026_11_04` (texte : `supabase/patch_registre_negociateurs_2026-11-04.sql`) :
  garde de départ et les 4 contrôles de fin **passés** (toutes les fiches de l'annuaire, tous les n° de la répartition,
  aucune personne sans fiche).
- **Le résultat réel = la table validée, à l'octet** : empreinte md5 des 242 lignes `a71424e78813a39607f661437952d22e`, la
  même que `REGISTRE_NEGOCIATEURS_CORRESPONDANCE_2026-11-04.csv`. Personnes 1000001 → 1000185 ; 1000001 = Frédéric
  GERPHAGNON, administrateur, actif, compte de l'app relié. Types : 1 administrateur, 164 négociateurs, 18 agences, 2 inconnus.
- **Droits** : un commercial actif lit 185 personnes et 242 fiches, le journal reste fermé (0) ; la clé publique ne lit rien.
  ⚠ **Trouvé au contrôle et corrigé** (migration `registre_negociateurs_lecture_seule_2026_11_04`) : les droits par
  défaut de Supabase donnaient insert/update/delete/TRUNCATE à `authenticated` — « revoke from public » ne les ferme pas
  (mémoire `revoke-from-public-ne-ferme-pas-authenticated`). La RLS bloquait déjà l'écriture, mais TRUNCATE ne passe pas par
  elle. Retirés ; contrôle vert.
- **Rien d'autre n'a bougé** : l'annuaire a toujours 219 fiches ; aucun lecteur (app, worker, run de nuit) ne lit encore le
  registre. Retour arrière : `patch_registre_negociateurs_2026-11-04_INVERSE.sql`.
- ⏳ **Étape 2** (la mise à jour de nuit : adopter les fiches nouvelles, journaliser les changements, signal sur un
  changement d'e-mail) — pas commencée. Tant qu'elle n'existe pas, le registre est une PHOTO du 04/11 : une fiche créée chez
  Hektor demain n'y entrera pas seule.

## 12. Étape 2 — LA MISE À JOUR DE NUIT : l'audit (04/11) — Frédéric : « oui audit étape 2 » — ⛔ rien n'est codé

**Périmètre** : le registre des négociateurs (3 tables), la nuit. Gestes : la nuit LIT l'annuaire, les comptes, la
répartition et les dernières listes de Hektor déjà téléchargées ; elle ÉCRIT seulement dans le registre. Aucun appel à
Hektor, aucun travail du worker, rien ne change pour l'app (personne ne lit le registre).

### 12.1 Ce que la nuit sait, et où (mesuré)

- `run_full_pipeline.ps1` l. 1369 : « phase2 push hektor directory to supabase » reconstruit l'annuaire (219 fiches, depuis
  la table locale qui ne purge jamais) et `app_user_directory` (les comptes ACTIFS sous le compte principal, purgé). C'est
  LE moment où tout est frais : l'étape du registre se place **juste après**.
- **La présence chez Hektor** n'est connue que localement : `raw_api_response`, `list_negos` + `list_negos_inactive`,
  relues chaque nuit (`sync_raw.py` l. 849 ; ce matin pages 0-2 et 0-4 à 03:55-03:56). ⚠ Une page qui n'existe plus reste
  avec sa vieille date (pages 3-4 d'avril, 5-8 de juin) : **seules les pages de la nuit comptent**. Ce matin : 186 fiches.
- **Le compte admin n° 4** n'est dans AUCUNE de ces sources (§10) : rattaché par décision, il ne doit jamais être déclaré
  absent par la nuit.
- **Pas d'historique ailleurs** (§2) : le journal du registre sera le premier.
- **La descente du matin** recopiera les 3 tables en local toute seule (`pull_from_supabase.py` lit le schéma exposé) ;
  ⚠ la **sauvegarde quotidienne** (`backup_critical.py`, liste fixe `CRITICAL_TABLES`) ne les prend pas : à ajouter.

### 12.2 Les cas de la nuit (le tableau des gestes de l'objet « fiche » et « personne »)

- **fiche connue, rien n'a changé** → `derniere_vue` = cette nuit.
- **fiche connue, un champ a changé** (nom, prénom, e-mail, n° d'utilisateur, agence, téléphones, actif) → le journal
  garde AVANT / APRÈS ; la fiche prend la valeur de Hektor ; **la personne ne bouge pas** (rattachement fixe).
- **fiche absente de la liste de la nuit** → `present_chez_hektor = false`, `absent_depuis`, une ligne au journal. Jamais
  supprimée. **Réapparue** → l'inverse, au journal.
- **fiche NOUVELLE** (n° inconnu) → adoptée : son e-mail (s'il n'est pas une boîte d'agence) appartient à UNE personne →
  rattachée à elle ; c'est une agence (mêmes règles qu'à l'étape 1) → à l'agence ; son nom est celui d'UNE personne →
  rattachée ET signalée ; sinon → **personne nouvelle**, signalée. Jamais de fusion de deux personnes par la nuit.
- **compte utilisateur** (secrétaire, agence) nouveau / disparu → mêmes règles ; le n° 4 est hors de ces règles.
- **n° d'utilisateur nouveau dans la répartition** (sans fiche) → place « numéro de répartition », signalée.
- **compte de l'app nouveau** sans personne → relié par l'e-mail d'une fiche de négociateur ; à défaut par le nom, signalé.
- **la personne** : jamais supprimée ; `actif` recalculé (une fiche active ou un compte présent).

### 12.3 Les signaux — le patron du projet

Le projet signale une anomalie de données par **une vue des lignes ouvertes + une sentinelle « data.… » du moniteur**
(`monitoring/check_gti_health.py`, ex. `data.contact_modif_ecart` l. 773 : sévérité warning, se tait quand un admin marque
« vu » par une RPC). Proposé : `data.negociateur_registre_signal` (warning), sur les lignes du journal marquées « à
signaler » et non traitées. ⚠ Les warnings ne font pas sonner l'e-mail du matin (seuls les critical) : ils s'y LISENT.

### 12.4 Les planchers — une nuit ratée ne doit rien abîmer

- si la liste de la nuit compte **moins de 90 %** des fiches présentes la veille → **aucune absence** n'est marquée, un
  signal « liste Hektor incomplète » est posé ;
- si `app_user_directory` a moins de 40 comptes (le cas d'une réponse vide, §2 et A3) → aucun compte n'est déclaré absent ;
- l'étape est **non bloquante** (`Invoke-OptionalStepWithRetry`, une tentative) : ratée, le registre garde la nuit d'avant.

### 12.5 Ce que ça pourrait casser ailleurs

Rien en production ne lit le registre. L'étape lit des tables que d'autres écrivent, sans les toucher ; zéro appel Hektor ;
quelques secondes. Le seul risque est pour le registre lui-même (une mauvaise adoption) : d'où l'essai à blanc et les
signaux. ⚠ Une clé de battement neuve doit être DÉCLARÉE dans `app_worker_registry` avant d'être utilisée (mémoire
« battement : clé non enregistrée part dans le vide »), et une tâche surveillée se déclare dans `check_gti_health.py`.

### 12.6 La proposition — en pièces

1. **SQL** (patch + inverse + essai en transaction annulée) : le journal reçoit `evenement`, `a_signaler`, `traite_le`,
   `traite_par` (additif) ; une fonction `app_negociateur_registre_maintenir(p_presents, p_nuit, p_a_blanc)` réservée au
   service, qui fait tout le §12.2 et rend son compte rendu ; la vue des signaux ouverts ; la RPC admin « marquer vu ».
2. **Python** `phase2/sync/maintenir_registre_negociateurs.py` : lit la présence de la nuit dans le local (pages de la nuit
   seulement), appelle la fonction, écrit le compte rendu au journal du run. **Interrupteur `.env`
   `APP_REGISTRE_NEGOCIATEURS`** : `0` = rien, `blanc` = calcule et écrit seulement le compte rendu, `1` = écrit.
3. **Le run** : une étape non bloquante juste après l'annuaire, clé de battement `phase2.registre_negociateurs` déclarée.
4. **La surveillance** : la sentinelle `data.negociateur_registre_signal` ; et les 3 tables dans `backup_critical.py`.
5. **L'épreuve** : une nuit « à blanc » (compte rendu lu le matin, rien d'écrit), puis allumage.

### 12.7 Ce qui se décide avec Frédéric

1. Quels changements **signalent** : proposé = e-mail, n° d'utilisateur, nom, personne nouvelle, rattachement par le nom,
   liste incomplète ; **au journal seulement** = téléphone, agence, actif, présence.
2. Les règles d'adoption d'une fiche nouvelle (§12.2) telles quelles ?
3. Commencer par une nuit à blanc, puis allumer ?

## 13. Étape 2 CODÉE et éprouvée (04/11) — Frédéric : « Oui, vas-y » — ⏳ le patch attend d'être COLLÉ

- **La base** : `supabase/patch_registre_negociateurs_nuit_2026-11-04.sql` (+ `_INVERSE`). Le journal reçoit événement,
  signal, nuit, levée ; `app_negociateur_registre_maintenir(p_presents, p_a_blanc)` (service seulement) ; l'aide
  `app_neg_adopter` ; la vue `app_v_negociateur_signaux` ; la RPC admin `app_negociateur_signal_traiter` ; la clé de
  battement `phase2.registre_negociateurs`. **À blanc = le même chemin, puis tout est annulé** (exception rattrapée dans un
  sous-bloc) : le compte rendu du matin est exactement ce que la vraie nuit aurait fait.
- **Éprouvé sur des COPIES temporaires du registre** (garde : les noms mènent aux copies ; témoin : le vrai registre est
  resté à 242 fiches, journal 0) :
  - à blanc → compte rendu, 0 ligne écrite ;
  - la nuit d'aujourd'hui (liste incomplète) → 1 signal « liste incomplète », 0 faux changement ;
  - e-mail de Claire RIBBES changé → au journal, signalé ; fiche n° 225 de Lucca MEJEAN retirée → réadoptée PAR L'E-MAIL à
    sa personne (1000039) ; liste complète sans n° 5 → Mélanie LEGRAND « disparue » ; nuit suivante → « réapparue »,
    `absent_depuis` effacé ; liste de 10 fiches → plancher, aucune absence, pas de 2e signal ; le compte admin n° 4 intact.
- **Le script** `phase2/sync/maintenir_registre_negociateurs.py` (interrupteur `APP_REGISTRE_NEGOCIATEURS` : absent ou 0 =
  rien, `blanc`, `1`) ; **le run** : étape non bloquante juste après l'annuaire (`run_full_pipeline.ps1`) ; **la
  sentinelle** `data.negociateur_registre_signal` (`check_gti_health.py`, domaine data_quality) ; **la sauvegarde** :
  les 3 tables dans `backup_critical.py`.
- ⛔ **L'outil a REFUSÉ la pose** (écriture en production) : c'est la règle du projet, **Frédéric colle**
  `patch_registre_negociateurs_nuit_2026-11-04.sql` dans l'éditeur SQL de Supabase ; le patch se contrôle lui-même (un
  essai à blanc à la fin, 0 ligne écrite exigée). Tant qu'il n'est pas collé : l'étape de nuit dit « éteint » (code 0) et
  la sentinelle est « illisible » (inconnu, pas critique).
- Ensuite : poser `APP_REGISTRE_NEGOCIATEURS=blanc` dans `.env` pour la première nuit ; lire le compte rendu au journal
  du run le matin ; puis `1`.

### 13 bis. ⚠ TROUVÉ EN CODANT : la nuit ne lit JAMAIS la liste complète des négociateurs

- `sync_raw.py:1665` `resolve_generic_max_pages` : en mode nuit, les négociateurs sont plafonnés à `--update-max-pages`
  (5) ; **et** `iter_pages` compte depuis 0 alors que Hektor commence à 1 — les pages « 0 » et « 1 » sont la MÊME page 1.
  Mesuré dans `raw_api_response` : `list_negos_inactive` = 152 fiches sur 8 pages, la nuit lit les pages 1, 1, 2, 3, 4 ;
  les pages 5 à 8 n'ont plus été lues depuis le **05/06**. (`list_negos`, les actifs, tient en 2 pages : complète.)
- Conséquence : la présence chez Hektor n'est jamais complète → le script le voit (aucune page « sans page suivante » pour
  la liste complète) et passe une présence INCONNUE → la nuit ne marque aucune absence, un seul signal. Pas de faux
  « disparu », mais pas de vrai non plus.
- C'est le même plafond que celui qui fige la diffusion par portail depuis le 26/10 (mémoire
  `diffusion-portails-figee-plafond-5-pages`). Remède proposé, À PART (code du run, attend son « vas-y ») : lire toutes les
  pages des négociateurs la nuit (comme les ventes) — environ 4 requêtes de plus par nuit.

### 13 ter. ✅ ÉTAPE 2 POSÉE (04/11) — Frédéric : « FAIS LE SQL TOI MEME TU AS MON ACCORD ENSUITE JE POUSSE »

- Migration `registre_negociateurs_nuit_2026_11_04` posée ; son contrôle de fin est passé (essai à blanc, 0 ligne écrite).
- **Droits vérifiés** : ni `authenticated` ni `anon` ne peuvent lancer la nuit ni adopter une fiche ; `anon` ne lit pas la
  vue des signaux et ne peut pas « marquer vu » ; personne n'écrit au journal par l'API. Clé de battement déclarée.
- **Le vrai script, à blanc, contre la vraie base** (`--a-blanc`) : code 0, compte rendu = 185 personnes, 242 fiches,
  1 signal « liste incomplète » (la nuit ne lit pas la liste complète, §13 bis), **0 faux changement** ; journal resté à 0.
- **`.env` : `APP_REGISTRE_NEGOCIATEURS=blanc`** (ajouté sans lire le fichier) — la PREMIÈRE NUIT sera à blanc. ⏰ Demain
  matin : lire le compte rendu dans le journal du run (étape « phase2 registre des negociateurs ») ; puis passer à `1`.

## 14. ✅ LA NUIT LIRA LA LISTE COMPLÈTE DES NÉGOCIATEURS (04/11) — Frédéric : « VAS Y »

- **`sync_raw.py`** `resolve_generic_max_pages` : `negos` n'a plus le plafond de 5 pages du mode nuit (comme `ventes`) ;
  la boucle s'arrête seule à la dernière page. Les autres listes gardent leur plafond. Le départ à 0 (pages « 0 » et
  « 1 » = la même) n'est PAS changé : il touche toutes les listes ; ici une requête de trop, sans conséquence.
- **Éprouvé hors ligne** (faux client, aucun appel à Hektor) : negos → toutes les pages ; annonces 5, contacts 5,
  diffusion 5, mandats 15, offres 10, compromis 10 inchangés ; une liste de 152 fiches / 8 pages → 9 requêtes, **152 fiches
  lues** ; témoin avec l'ancien plafond → 5 requêtes, **80 fiches** — exactement la mesure de ce matin.
- **Le piège que ça ouvrait, traité** : l'étape 1 a compté 186 fiches « présentes » (vieilles pages d'avril et de juin) ;
  la vraie liste en compte 152 → le plancher des 90 % aurait tout bloqué. Migration
  `registre_negociateurs_nuit_total_2026_11_04` (`supabase/patch_registre_negociateurs_nuit_total_2026-11-04.sql`,
  + `_INVERSE`) : la fonction reçoit `p_total` (le total annoncé par Hektor) ; **une liste lue jusqu'à ce total fait foi** ;
  plus de 5 disparitions en une nuit → signal `disparitions_nombreuses`. Contrôle de fin passé (liste de 152 / total 152 :
  acceptée, 34 disparitions comptées, 0 ligne écrite à blanc). Le script transmet le total de `list_negos_inactive`.
- **Attendu la nuit du 04 au 05/11 (à blanc)** : la liste complète lue (environ 4 requêtes de plus), `liste_ok = true`,
  ~34 fiches « disparues » (celles des vieilles pages) et 1 signal « disparitions nombreuses » — à lire avec Frédéric avant
  de passer l'interrupteur à `1`.

## 15. Étape 3, premier lecteur : LE PILOTAGE LIT LE REGISTRE (04/11) — Frédéric : « j'ai push enchaine »

- `lib/pilotage.ts` : `lireRegistre()` lit `app_negociateur_personne` + `app_negociateur_fiche` ; `construireRepereDepuisRegistre()`
  fait la personne = celle du registre (rattachement fixe) avec TOUS ses numéros — y compris le compte admin n° 4, les
  comptes de secrétaire, les n° de la répartition sans fiche. L'e-mail de la personne passe avant celui de ses fiches.
- `PilotageScreen.tsx` : le registre d'abord, **l'annuaire de Hektor en repli** si le registre ne répond pas (le bandeau dit
  lequel sert) ; le sélecteur marque « · agence » les agences et « · ancien » les personnes que le registre dit inactives.
- Ce que ça change à l'écran (mesuré dans le registre) : Pauline GIRINON, Caroline GERPHAGNON, Delphine BLANCHARD ne sont
  plus « ancien » (actives par leur compte de secrétaire) ; « Groupe GTI » n'est plus UNE personne de 11 fiches mais une
  agence par agence ; « gti immobilier » rejoint l'agence de Firminy ; Frédéric = administrateur avec le compte n° 4.
- Contrôlé sur le serveur d'essai (le bandeau dit « Registre des négociateurs », mêmes chiffres qu'avec l'annuaire) ;
  build vert. ⏳ Contrôle en ligne après le push.
- Rien d'autre ne lit encore le registre : menus, répartition, droits, rendez-vous, worker = à venir, un par un.
- ✅ **Contrôlé EN LIGNE le 04/11** (bundle `index-COn_gXxf.js`, Chrome de Frédéric) : le bandeau dit « Registre des
  négociateurs » ; Claire RIBBES inchangée (100 083 € HT, 18 actes, 38 mandats, 151 k€ de potentiel ; 342 lignes par le
  numéro, 0 par le nom) ; le sélecteur compte 44 personnes ; Pauline GIRINON, Caroline GERPHAGNON, Delphine BLANCHARD n'y
  sont plus « ancien » ; les agences y sont marquées « · agence » (Annonay, Firminy, Saint-Étienne).

## 16. Étape 3, deuxième lecteur : LES RENDEZ-VOUS LISENT LE REGISTRE (04/11) — Frédéric : « Oui, enchaîne »

- **Le code** (`backend/app/services/appointment_service.py`) : une aide `_load_registre_negociateur(commercial_id, email)` —
  la personne par son n° de NÉGOCIATEUR (à défaut par l'e-mail d'une fiche, s'il ne désigne qu'une personne), puis le
  téléphone de sa fiche, à défaut d'une autre fiche de la même personne (actives d'abord). **Jamais `id_user = commercial_id`.**
  Deux appelants corrigés : `_load_contact_details` (page publique de rendez-vous, recopiée dans le lien) et
  `_hydrate_estimation_negotiator` — ⚠ trouvé en passant : la page d'ESTIMATION avait le même défaut, et il y donnait le
  NOM et l'E-MAIL d'une autre personne en plus du téléphone (la clé de rotation `user_id` n'est pas touchée).
- **Éprouvé en lecture seule contre la vraie base** : Aline VALETTE (n° 42), Mélanie LEGRAND (n° 5), Hugo LABBE (n° 29),
  Claire RIBBES (n° 15) reçoivent chacun LEUR téléphone ; l'ancien chemin leur donnait celui de Dylan JOURGET, Caroline
  GERPHAGNON, Lucille FORLICO, et de l'agence de Dunières ; par l'e-mail seul → Claire RIBBES ; un n° inconnu → rien.
- **La réparation des 178 liens** : `supabase/patch_rdv_telephone_negociateur_2026-11-04.sql` (+ `_INVERSE`), sauvegarde
  datée `app_appointment_public_link_avant_tel_20261104`. Mesuré à blanc : 178 liens faux, 178 retrouvent leur négociateur
  au registre, 178 recevront son téléphone, 0 restera vide. Contrôle de fin : plus aucun lien au téléphone d'une autre
  personne. ⛔ **À poser APRÈS la mise en ligne du backend** (Render) : l'ancien code réécrit un lien dont une case est vide.
- ✅ **POSÉE le 04/11** après la mise en ligne du backend (Render `/health` : commit `3f82225`, qui contient `72b71a0`) —
  migration `rdv_telephone_negociateur_2026_11_04`. Contrôle de fin passé (plus aucun lien au téléphone d'une autre
  personne). Mesuré ensuite : **178 liens sauvés et réparés**, et SEULEMENT eux (178 touchés sur 2 298) ; la sauvegarde
  n'est lisible ni par `anon` ni par `authenticated`. **Le lien actif de l'annonce 33220** (Hugo LABBE) : avant
  06…27 = Lucille FORLICO → après 07…54 = Hugo LABBE, au registre.

## 17. Le worker : le piège endormi RETIRÉ (04/11) — Frédéric : « Oui, enchaîne »

- `Console/console_job_worker.js`, `resolveHektorExecutionUser` : le recours `dossier_commercial_id_legacy` (chercher le
  COMPTE dont l'id_user vaut le n° de NÉGOCIATEUR du bien) est retiré. À défaut de l'annuaire par agence, la suite passe
  déjà par l'e-mail du négociateur du bien, qui désigne la bonne personne. Rien ne lisait cette source (cherché dans tout
  le dépôt). Syntaxe vérifiée (`node --check`) ; le worker n'a pas été lancé (règle : ne jamais le lancer pour l'inspecter).
- ⚠ **Pas encore actif** : les 4 services worker tournent sur le code chargé à leur démarrage. Le retrait n'agira qu'au
  prochain redémarrage — ⛔ qui chargera AUSSI les modifications non commitées de l'autre session dans ce fichier
  (signature Youtrust, génération de mandat). Le redémarrage se décide avec Frédéric, file vide (0 pending, 0 running).
- Seul mon bloc est commité ; les autres blocs du fichier restent à l'autre session.
- ✅ **ACTIF depuis le 04/11 à 14:13:34-36** : Frédéric a poussé et redémarré les 4 services (heure des processus mesurée
  par `Win32_Process`, après le commit `eda00f0` de 14:09:38). File vide au redémarrage, aucun travail coupé. ⚠ Ce
  redémarrage a aussi mis en service le code NON commité de l'autre session dans ce fichier.

## 18. L'interrupteur allumé, les menus audités, l'agenda corrigé (04/11) — Frédéric : « ALLUME TOUT DE SUITE ET ENCHAINE »

- **Interrupteur** : `.env` `APP_REGISTRE_NEGOCIATEURS=1` (ligne remplacée sans lire le fichier). La nuit du 05/11 ÉCRIT.
- **Essai à blanc forcé juste après** (`--a-blanc`) : les pages de la nuit du 04/11 étaient encore plafonnées (96 fiches,
  1 liste sur 2 lue jusqu'au bout) → `liste_ok: false`, **aucune absence marquée**, 1 signal `liste_incomplete`,
  49 comptes cohérents, rien écrit. C'est le plancher qui joue ; la correction de `sync_raw` agit dès cette nuit.
- **Les menus** (`loadHektorNegotiatorOptions`, `api.ts`) : ils lisent l'annuaire, actifs seulement. Mesuré : annuaire
  30 actifs = registre 30 actifs, **0 sans jumeau** (même n° de négociateur, même compte, même agence). Basculer ne
  changerait rien à l'écran aujourd'hui. ⚠ Ces options partent dans des gestes chez Hektor (changer le négociateur d'un
  bien : `target_agency_id_user` ; créer un contact : `hektorAgencyUserId`) et portent `agence_id_user`, **que le registre
  n'a pas**. Basculer = ajouter cette colonne au registre (écriture en base) → **non fait, à décider par Frédéric**.
- **⛔ Trouvé en passant, CORRIGÉ : l'agenda Google d'une autre personne.** `resolveGoogleWorkspaceCalendarEmail`
  (`App.tsx`) cherchait l'agenda, à défaut d'adresse Workspace, en comparant le n° de NÉGOCIATEUR aussi au n° de COMPTE
  des options. Mesuré : **22 anciens numéros** tombaient sur un compte actif (21 sur une autre personne : Aline VALETTE
  n° 42 → Dylan JOURGET, Marion BILLIG DURAND n° 39 → Claire RIBBES…), et parmi les actifs le n° 55 (Christine BRAVARD) →
  Stéphanie MARTINEZ. **0 cas réel ce jour** : sur 13 525 biens, les 4 256 sans adresse Workspace n'ont soit pas de
  négociateur (4 232), soit un n° sans collision ; sur 2 298 liens de RDV, 705 sans adresse, 0 collision. **Piège dormant**,
  fermé : la comparaison ne garde que `commercialId` et `hektorNegociateurId` (tous les appelants passent un n° de
  négociateur). Build vert. Pas de preuve à l'écran possible : aucun cas à montrer.

## 19. Les CUMULS par négociateur du pilotage (04/11) — Frédéric : « quelques erreurs de cumul »

**Ce qui est corrigé et ce qui ne l'est pas.** Le FILTRE par négociateur lit le registre (§ étape 3, vu en ligne le 04/11 :
« Registre des négociateurs · 342 lignes rattachées par le numéro » pour Claire RIBBES). Mais les CUMULS par négociateur ne
passent PAS par le registre (`lib/pilotage.ts`) : Ventes regroupe par n° de COMPTE de la répartition sous le nom de la
première ligne (`parts`, l. 402) ; Mandats par le NOM écrit (`calculerMandats`, l. 499) ; Stock par le nom sans accents
(l. 594) ; Classements fusionne les trois PAR LE NOM (`calculerClassements`, l. 848).

**Mesuré (base, 04/11), source par source :**
- Mandats 2026 et 2025 (767 en 2025) : **propres** — un nom = une personne du registre ; 9 mandats 2026 sans négociateur.
- Stock (712 biens, 32 personnes) : propre, sauf 2 biens écrits « gti immobilier » / « Groupe GTI » (comptes d'agence
  Firminy et Saint-Étienne au registre) et 1 mandat « gti immobilier ».
- **Ventes : le défaut.** Des lignes de répartition portent le nom « Cet utilisateur a été supprimé » (c'est ainsi que
  Hektor nomme un compte supprimé) alors que LE REGISTRE CONNAÎT leur titulaire. Le pilotage les range sous « Négociateur
  supprimé » : 2026 → Hugo LABBE (compte 54, annonce 35474, ≈ 8 000 €) et le compte d'agence d'Annonay (17, 35529,
  ≈ 10 500 €) ; 2025 (la colonne « an passé ») → Annonay 22 lignes ≈ 60 500 €, Firminy (19) ≈ 10 000 €.
- **Ventes : 12 dossiers vendus en 2026 dont la répartition ne fait pas 100 %** (la règle du pilotage : entrée + sortie =
  100 %, vraie pour 274 dossiers sur 286). 5 sans aucune ligne (39664, 59196, 59525, 29425, 23238), 1 à 0 % (62527), 6
  partiels (61739 à 50 %, 59393 50 %, 59119 50 %, 47348 50 %, 45671 75 %, 1993 88 %) → **≈ 77 000 € d'honoraires 2026
  attribués à personne** (honoraires lus au registre des affaires, approximation). Ce n'est pas un défaut de code : c'est
  une répartition à compléter ; mais l'écran ne le DIT pas dans le classement, donc la somme des négociateurs ne fait pas
  le total.

**Remède proposé, PAS codé (attend le « vas-y ») :**
- A — les cumuls par PERSONNE DU REGISTRE : Ventes par compte → personne (`parUser`), Mandats et Stock par n° de
  négociateur → personne (`parNego`), le nom en repli seulement ; Classements fusionne par la personne. Effet mesuré :
  Hugo LABBE +8 000 € en 2026, les comptes d'agence retrouvent leurs lignes, plus de ligne « Négociateur supprimé ».
- B — une ligne « non réparti » visible (Ventes et Classements), avec la liste des 12 dossiers, pour que le cumul des
  négociateurs égale le total ; les compléter reste un geste de saisie.

## 20. Filtré par négociateur : compte-t-on SA PART de commission ? (04/11) — question de Frédéric

**Pilotage** (`filtrerParPersonne`, `lib/pilotage.ts` l. 1073) :
- VENTES ACTÉES : OUI. Pour chaque dossier vendu, honoraires × (somme de SES pourcentages, entrée + sortie) / 100 ; un
  dossier où il n'a aucune part est retiré ; une part sur le bien d'un autre est comptée. ⚠ Le NOMBRE de ventes compte 1
  par dossier où il a une part (pas 0,5), et le VOLUME garde le prix entier. Dossier vendu SANS répartition → 100 % au
  négociateur du bien (repli par l'e-mail).
- COMPROMIS, OFFRES, ACTES À VENIR, onglet Affaires : NON. La répartition n'est lue que pour les chaînes VENDUES
  (`lireVentes` → `chaines()` filtre `etape === 'vendu'`) ; le reste passe au négociateur DU BIEN, à 100 %. ⚠ Le bandeau
  dit « Ventes et compromis répartis : sa part » — FAUX pour les compromis. Mesuré : 126 compromis en cours, 88 ont déjà
  une répartition saisie, 8 partagés entre plusieurs personnes.
- Mandats, stock, signatures, acquéreurs : le négociateur du bien ou de la fiche (normal, rien ne se partage).

**Registre des transactions** (`RegistreTransactionsScreen.tsx` l. 1331-1356) : NON. Le filtre (admin seulement) garde
les dossiers dont LE BIEN est suivi par ce négociateur (`negociateur_email`) et les chiffres de tête additionnent 100 %
des honoraires. Une part sur le bien d'un autre n'apparaît pas ; un bien partagé compte en entier. La répartition ne sert
qu'à l'affichage de la fiche (avec la ligne « Non attribué »).

**L'écart, mesuré sur les ventes 2026 (TTC, registre des affaires)** — Transactions contre Pilotage :
Sandrine DELAVAUD 14 ventes / 123 290 € contre 12 / 83 991 € · Aline VALETTE 2 / 23 000 € contre 0 · Nicolas COUDERT
14 / 142 700 € contre 16 / 165 200 € · Lionel FLANDIN 66 000 € contre 48 250 € · Alice RONDEAU 43 850 € contre 60 649 € ·
Claudie FERNANDEZ 0 contre 3 / 15 000 €. Claire RIBBES : identique (18 ventes, 120 100 € TTC = 100 083 € HT), elle ne
partage rien.

**Remède proposé, PAS codé :** pilotage — lire la répartition aussi pour les compromis (et corriger le bandeau) ;
Transactions — quand un négociateur est choisi, compter SA part (dossiers où il a une part, ses biens comme ceux des
autres), ou à défaut dire en clair « les biens qu'il suit, honoraires entiers ». Décision de Frédéric.

## 21. LA RÈGLE DE CALCUL DE LA RÉPARTITION, posée dans le pilotage ET les transactions (04/11)

**Décision de Frédéric** : « corrige le mode de calcul, on corrigera la répartition des honoraires avec le sheet dans
le chantier dédié ». Ses réponses : aucune répartition → 100 % au négociateur du mandat ; répartition à 0 % → 50 % / 50 % ;
un seul côté saisi (entrée OU sortie) → le même négociateur de l'autre côté ; total incomplet → ramené à 100 % dans la même
proportion ; pilotage ET transactions, compromis compris. « Pense au registre des répartitions d'honoraires. »

**Le registre des répartitions n'est PAS touché.** `app_affaire_repartition` reste ce que la nuit (`app_repartition_absorber`,
depuis Hektor) et la saisie (`app_repartition_commission_set`) y mettent ; la règle ne fait que COMPTER, côté écran.
Lecteurs en base vérifiés : `app_mes_chaines_nommees` (les DROITS « où je suis nommé » — inchangés : être nommé reste une
question de saisie), `app_negociateur_registre_maintenir`, la vue `app_v_repartition_orpheline`. La fiche d'un dossier
montre toujours la saisie telle quelle, avec sa ligne « Non attribué » : c'est ce qui restera à corriger au classeur.

**Le code** :
- `lib/repartitionEffective.ts` (neuf) : `repartitionEffective()` — LA règle, une seule fonction — et `partDe()`.
- `lib/pilotage.ts` : la répartition est lue pour TOUS les dossiers (compromis et offres compris, avant : les ventes
  seulement) par une lecture qui ÉCHOUE franchement (avant : `loadRepartitionsDesChaines` rendait une carte vide en silence,
  ce qui avec la règle aurait donné 100 % au mandat sans rien dire) ; `appliquerRepartition` / `compterRepartitions` (la
  personne du registre sur chaque ligne ; le négociateur du mandat = celui du bien, par son e-mail au registre) ;
  `nommerParRegistre` (les cumuls par nom de Mandats / Stock / Classements prennent le nom du registre, APRÈS le filtre,
  qui garde son contrôle) ; Ventes rangées par PERSONNE (plus de « Négociateur supprimé »).
- `PilotageScreen.tsx` : la règle appliquée une fois, avant le filtre et tous les calculs ; bandeau et note des
  classements corrigés (« ventes, compromis et offres en cours : sa part… »).
- `RegistreTransactionsScreen.tsx` : un négociateur choisi → les dossiers où il a une PART (ses biens et ceux des autres),
  honoraires actés et attendus = SA part, la liste montre « X € · 50 % » ; le menu propose aussi ceux qui n'ont qu'une part
  sur le bien d'un autre ; tant que sa part n'est pas calculable, l'ancien filtre (biens suivis) et l'indicateur le dit.
  Le volume reste le prix entier (comme au pilotage).

**Contrôlé** : build vert. Règle : 12 cas réels + 5 cas construits, tous verts (essai hors ligne). ⭐ **LE VRAI CODE exécuté
sur les vraies ventes 2026** (script en lecture seule, `appliquerRepartition` + `calculerVentes` + `filtrerParPersonne`) :
286 ventes, 2 168 198 € d'honoraires, **attribués 2 168 199 € (100 %, arrondis)**, **0 ligne « supprimé »**. Sandrine
DELAVAUD 83 991 → 98 991 € (61739 recopié), Hugo LABBE 8 000 € (le contrôle dit « 2 portent son numéro sous un autre nom »),
Aline VALETTE 14 000 € (39664, 100 % au mandat), Annonay 10 500 €. ⭐ **Témoin indépendant** : la même règle écrite en SQL
donne **les mêmes 33 lignes à l'euro près**. ⚠ Pas encore VU à l'écran : il faut la mise en ligne (push) — puis contrôle
dans l'app (pilotage filtré Sandrine DELAVAUD 98 991 € TTC ; Transactions filtré sur elle, même chiffre).
⚠ Reste au négociateur du bien (non réparti par la règle) : l'onglet Affaires « prix obtenu, notaires » (source
`app_pilotage_affaires_plus`), mandats, stock, signatures, acquéreurs — comme le dit le bandeau.
- ✅ **VU EN LIGNE le 04/11** (déploiement Vercel de `f545e13`, fichier `index-BPsbhBlX.js`), dans le Chrome de Frédéric :
  pilotage, onglet Ventes, réseau entier : **aucune ligne « supprimé »** ; filtré Sandrine DELAVAUD : nouveau bandeau, contrôle
  245 lignes par le numéro, **honoraires TTC à date 98 991 €** (l'attendu exact), 12 ventes, 5 compromis datés 24 k€.
  Transactions 2026 filtré sur elle : **99 k€ « sa part, selon la répartition »**, 12 ventes, 5 compromis 24 k€ « (sa part) »,
  lignes « 5 150 € · 50 % » (dont un bien d'Alice RONDEAU où elle a la sortie) ; Claudie FERNANDEZ (parts seulement) est
  au menu. « contre 0 € » en 2025 : juste (ses 2 ventes 2025 sont après le 4 novembre).
- ⛔ **Trouvé à l'écran, CORRIGÉ (non encore en ligne)** : filtré, le bloc « Négociateurs » de l'onglet Ventes disait
  91 592 € « 93 % attribués » — les honoraires déjà réduits à sa part étaient multipliés une 2e fois par ses pourcentages
  (défaut d'avant la règle, devenu visible). Ses lignes sont remises à 100 % de sa part (`filtrerParPersonne`). Vrai code
  rejoué : bloc = tête pour Sandrine (98 991), Nicolas COUDERT (165 200), Hugo LABBE (8 000), Claire RIBBES (120 100).
  Réglages de Frédéric remis comme avant l'essai (filtre Transactions « tous », pilotage onglet Stock en HT).
- ✅ **Correction du bloc VUE EN LIGNE le 04/11** (déploiement de `63552e1`, `index-BymjBxGI.js`) : filtré Sandrine
  DELAVAUD, bloc « Négociateurs » = **98 991 €, « attribués sur 98 991 € (100 %) »**, égal à la tête. Réglages remis
  (pilotage onglet Stock, HT).

## 22. Le NOUVEL UTILISATEUR DE L'APP relié au registre dès sa création (04/11) — Frédéric : « OK 1 ET APRES 2 »

**Avant** : l'outil « Utilisateurs » (backend `create_user` / `update_user`) reliait le compte à Hektor par l'annuaire, une
fois (`app_google_workspace_identity`), et ne touchait PAS au registre ; seule la nuit reliait un compte à une personne
(par l'e-mail d'une fiche, à défaut le nom, signalé). Mesuré : 8 comptes, 5 reliés ; non reliés : CODEX (essai), Sasha
Gerphagnon (gmail, sans fiche), Franck GERPHAGNON (compte @gti-immobilier.fr). ⚠ **Franck a DEUX comptes de l'app** : le
gmail (`0b500395…`, relié à la personne 1000036) et le @gti (`3603c8bc…`, non relié) — une personne n'a qu'un compte.

**Le remède (codé, aucune modification de la base)** — `backend/app/services/supabase_admin.py`
`lier_registre_negociateurs`, appelé après la création et la modification :
1. la personne CHOISIE par l'admin (refus si elle est reliée à un autre compte ; si le compte change de personne,
   l'ancienne le lâche, les deux au journal) ;
2. sinon UNE personne au même e-mail (le sien ou celui d'une de ses fiches Hektor, jamais une agence) → reliée ;
3. sinon des personnes au même NOM (même clé que la nuit, `app_neg_cle_nom`), MÊME déjà reliées → rien n'est relié,
   l'écran PROPOSE (évite le doublon de Franck) ;
4. sinon, **à la création seulement**, une personne « née dans l'app, sans fiche Hektor » (`origine = 'app'`,
   `a_valider`, journal `personne_nouvelle` signalé) ; sa fiche Hektor s'y rattachera la nuit par l'e-mail
   (`app_neg_adopter` cherche aussi `personne.email`). À la modification : « pas relié », rien n'est créé.
Le compte est déjà créé quand on arrive là : un échec du registre est RENDU à l'écran, il ne défait pas le compte.
`models.py` : `registrePersonneId` (facultatif). Front : `lib/api.ts` (`RegistreLien`, `loadRegistrePersonnes`,
`texteRegistreLien`), `App.tsx` outil « Utilisateurs » : la personne de chaque compte (« Registre : X (n° …) » ou « pas
relié »), un choix « Personne du registre des négociateurs » à la création et à la modification, le message dit ce qui a
été fait. ⚠ Le chemin de SECOURS (fonction Supabase `admin-users`, hors push) ne relie pas : la nuit le fera par l'e-mail.

**Éprouvé contre la vraie base, écritures interceptées (rien d'écrit)** : 9 cas sur 9 — Franck @gti (modification ET
création) → « à choisir : FRANCK GERPHAGNON (déjà reliée) », pas de doublon ; Frédéric → « déjà » ; nouveau compte au mail
de Sandrine → relié par l'e-mail ; inconnu → personne créée (création) / « pas relié » (modification) ; choix de Franck
gmail pour le compte @gti → refusé (conflit) ; choix libre → relié ; personne inexistante → erreur rendue. Build vert.
⏳ À mettre en ligne (Render + Vercel, par le push), puis à voir dans l'outil. ⛔ À DÉCIDER par Frédéric : lequel des deux
comptes de Franck est relié à sa personne (et l'autre archivé ?).
- ✅ **Décision de Frédéric (04/11) : « le compte @gti »** — posée en base (une ligne, garde avant/après) : la personne
  1000036 FRANCK GERPHAGNON est reliée au compte `franck.gerphagnon@gti-immobilier.fr` (`3603c8bc…`) ; le compte gmail
  (`0b500395…`) n'est plus relié, ni supprimé ni archivé. Journal : `compte_app_relie`, avant = le gmail. La nuit ne le
  défera pas (son étape D ne relie qu'une personne SANS compte).

## 23. LES MENUS DE NÉGOCIATEURS LISENT LE REGISTRE (04/11) — Frédéric : « OK 1 ET APRES 2 », « reprend le dev »

**Le point bloquant (§18)** : les menus (`loadHektorNegotiatorOptions`, `loadNegotiatorOptionForContact`) envoient à Hektor
le n° du compte d'AGENCE (`agence_id_user`) — changer le négociateur d'un bien, créer un contact. Le registre ne le
portait pas, et il ne se déduit pas (18 agences = 18 comptes d'agence, mais le lien agence → compte n'est pas au registre).

**Le patch** `supabase/patch_registre_negociateurs_agence_user_2026-11-04.sql` (+ `_INVERSE`) : une colonne
`app_negociateur_fiche.agence_id_user`, remplie depuis l'annuaire par le n° de négociateur, et TENUE CHAQUE NUIT : sept
lignes de `app_negociateur_registre_maintenir` modifiées EN PLACE depuis la version en base (empreinte `e68a3f86…`
vérifiée ; chaque ancre doit apparaître une fois, sinon ARRÊT) — lecture, création, journal des changements, mise à jour,
comparaison. ⭐ **Éprouvé dans une transaction ANNULÉE** : 219 fiches remplies, **30 actifs sur 30 au bon compte
d'agence**, 0 écart avec l'annuaire, la nuit à blanc ne journalise aucun faux changement, et le RETOUR ARRIÈRE rend la
fonction à l'IDENTIQUE (empreinte `e68a3f86…` retrouvée). ⚠ Mon 1er essai s'est arrêté sur MON contrôle (seuil 7 au lieu
de 5) — tout annulé, vérifié (pas de colonne, empreinte intacte), seuil corrigé.

**Le front** (`lib/api.ts`) : les deux lectures passent par le REGISTRE d'abord (jamais purgé : une nuit où Hektor rend
une liste tronquée ne vide plus le menu ; `loadNegotiatorOptionForContact` retrouve aussi les anciens), l'annuaire en
REPLI (registre illisible, vide, ou colonne pas encore posée → l'ordre de mise en ligne est sans danger). Mesuré : pour
les 30 actifs, nom, e-mail, agence, n° de négociateur, n° de compte et n° de compte d'agence IDENTIQUES à l'annuaire —
le menu ne change pas à l'œil. Build vert. ⏳ Patch à poser (accord), puis push, puis contrôle dans un menu.
- ✅ **PATCH POSÉ le 04/11** (Frédéric : « Oui vas y ») — migration `registre_negociateurs_agence_user_2026_11_04`, ses
  contrôles internes passés. Mesuré après : 219 fiches de négociateur sur 219 remplies, **30 actifs sur 30 au bon compte
  d'agence**, droits inchangés (`authenticated` : lecture seule), aucune ligne parasite au journal. Nouvelle empreinte de
  la fonction de nuit : `725267743d8fedad1c582d830250673a` (l'INVERSE la rend à `e68a3f86…`). ⏳ Reste : le push (le front
  lit déjà le registre dès qu'il est en ligne), puis un menu vu à l'œil.
- ✅ **EN LIGNE et vu le 04/11** (Vercel `index-H-2wWDRo.js`, Chrome de Frédéric) : au chargement, l'app lit
  `app_negociateur_fiche` avec `agence_id_user` (réponse 200) et **ne lit plus l'annuaire pour les menus** (0 lecture de
  `app_hektor_negotiator_agency_directory` sur la page) — le repli n'a pas joué. ⚠ À ne pas confondre : le filtre
  « Négociateur » de la liste des annonces (50 noms, anciens compris, ex. Aline VALETTE) vient des NOMS PORTÉS PAR LES BIENS
  (`filterCatalog.commercials`), pas de ces menus ; inchangé. La fenêtre « Nouvelle annonce » a été ouverte puis annulée
  (rien créé) : son menu de négociateurs n'apparaît qu'à une étape plus loin, que je n'ai pas franchie (risque de brouillon
  chez Hektor).

## 24. LA 1re NUIT QUI ÉCRIT (05/11, étape « phase2 registre des negociateurs » à 06:28:47) — contrôle du matin

Mesuré en base à 06:35 (le run, lui, tournait encore : rattrapage des photos) : **liste complète lue — 152 fiches
présentes** (96 la nuit d'avant, plafonnée) ; journal de la nuit = **34 `disparue` + 1 `disparitions_nombreuses`
signalé**, exactement l'attendu ; **30 actives, 0 active marquée absente** ; 67 fiches « absentes de chez Hektor » (les 34
de la nuit + 33 déjà absentes depuis la photo du 04/11), toutes GARDÉES ; aucune fiche créée (pas de nouveau
négociateur) ; 185 personnes, aucune supprimée. ⚠ Le signal `disparitions_nombreuses` fera crier la sentinelle
`data.negociateur_registre_signal` au prochain passage du moniteur : il est ATTENDU (vieilles pages), à marquer traité
(`app_negociateur_signal_traiter`) — décision de Frédéric.
- ✅ **Les 34 « disparues » relues une par une (05/11)** : toutes ont encore leur FICHE et leur PERSONNE au registre ; toutes
  étaient DÉJÀ des fiches inactives chez Hektor (aucune fiche active n'a disparu). 20 appartiennent à des personnes qui ont
  une autre fiche encore présente (Dylan JOURGET, Emmanuelle PEREIRA, Céline HERITIER, Mélanie LEGRAND, Nadège PEYRARD,
  Stéphanie JEOFFROY, Stéphanie MARTINEZ, Guillaume PERRET, Vincent-Lucas GONZALEZ, 7 comptes d'agence) ; 14 à des anciens
  sans fiche restante (Hugo LABBE ×3, Frédérique JORAND ×2, Cyril LACHAIZE, Pierrick MARTINEZ, Tharah KLAU, agences d'Ambert,
  Issoire, Le Puy, Saint-Étienne). Signal `disparitions_nombreuses` du 05/11 **marqué traité** à la demande de Frédéric
  (« Oui ») — fait en base au nom de son compte (`traite_par` = son app_user_id ; la RPC exige une session admin) ;
  0 signal ouvert ensuite.

## 25. ⛔ CORRECTION (05/11) — les « Groupe GTI » NE SONT PAS des anciens ; et un TROU : 3 comptes d'agence absents

Frédéric : « groupe gti saint etienne est pas en ancien… les anciens n'ont pas GTI dans leur libellé ». **Il a raison.**
L'organigramme de Hektor (Mon réseau → Organigramme, lu le 05/11) montre les 18 agences VIVANTES, dont GROUPE GTI
SAINT-ÉTIENNE (dernière connexion 30/10, 2 négociateurs = Lucille FORLICO n° 4 et Mélanie LEGRAND n° 5, 1 208 biens actifs).

**Ce qui a « disparu » cette nuit n'est PAS une agence** : ce sont des FICHES DE NÉGOCIATEUR au nom de l'agence (« Groupe
GTI », n° 2, accueil@ — Saint-Étienne ; n° 12 Ambert, n° 98 Issoire, n° 99 Le Puy…), que Hektor ne rend plus dans aucune
liste (n° 2 vu pour la dernière fois dans la liste des ACTIFS, page 3, le 03/04/2026). Le registre les a rangées, à juste
titre, sous la personne de l'agence (`app_neg_adopter` : un nom « Groupe GTI… » = l'agence). ⛔ Mon message du 05/11 les
appelait « anciens comptes d'agence » : FAUX. Le n° 2 porte encore 31 003 contacts non archivés, 1 453 mandats, 171 biens.

**Le trou trouvé en vérifiant** — le compte UTILISATEUR de l'agence (celui que les menus envoient comme `agence_id_user`) :
- ABSENT du registre : Saint-Étienne (compte n° 25), Issoire (n° 22), « Agences supprimée » (agence 19, compte n° 26) ;
- MAL RANGÉ : Le Puy (compte n° 24) est sous une personne « Utilisateur supprimé n° 24 » (type inconnu) au lieu de
  « Groupe Gti Le Puy en Velay » ; Ambert (n° 23) n'y est que comme « numéro de répartition ».
- Cause : les comptes d'agence viennent de `app_user_directory` (UsersOfParent, ~12 comptes) — ces 4-5 n'y sont pas.
- Sans effet sur les menus (le n° du compte d'agence est recopié de l'annuaire sur chaque fiche, 30/30 justes), mais la
  personne « agence » du registre est incomplète et marquée inactive alors que l'agence vit.
⏳ Remède à proposer (écriture en base, accord requis) : rattacher les comptes 25, 22, 24, 23 à leur agence, et faire dire
« agence » (jamais « ancien ») à l'écran pour le type agence.
- ✅ **CORRIGÉ le 05/11** (Frédéric : « Rattache oui ») — `supabase/patch_registre_negociateurs_comptes_agence_2026-11-05.sql`
  (+ `_INVERSE`), migration `registre_negociateurs_comptes_agence_2026_11_05`. Comptes d'agence rattachés PAR DÉCISION
  (la nuit ne les touche pas, ne les marque jamais absents — même règle que le compte admin n° 4) : n° 25 → Groupe GTI
  Saint-Etienne (créé), n° 22 → Groupe GTI Issoire (créé), n° 24 → Groupe Gti Le Puy en Velay (fiche déplacée depuis
  « Utilisateur supprimé n° 24 », qui reste, vide, avec une note), n° 23 → Groupe GTI Ambert (de « numéro de répartition »
  à compte d'agence). Les 4 agences ACTIVES. Éprouvé avant dans une transaction annulée, nuit à blanc comprise (aucun
  évènement nouveau sur ces fiches). Mesuré après : **18 comptes d'agence sur 19 sous leur agence** ; reste le n° 26
  (agence 19 « Agences supprimée »), non demandé ; 8 lignes de journal ; 0 signal ouvert.

## 26. LA RÉPARTITION DES HONORAIRES LIT LE REGISTRE (05/11) — Frédéric : « Vas-y »

Deux lectures de l'annuaire restaient autour de la répartition (`lib/api.ts`) :
- `loadRepartitionPersonnes` — la liste des négociateurs ACTIFS proposés dans la fenêtre de répartition (par n° de
  COMPTE, celui que la répartition enregistre) ;
- `loadNomsNegociateurs` — le NOM d'un négociateur par son e-mail (registre des transactions : fiche, menu, recherche).
Les deux lisent maintenant les fiches du REGISTRE (actives seulement pour la première ; la fiche active d'abord pour la
seconde), l'annuaire en REPLI (registre illisible ou vide). Les lignes de répartition déjà saisies ne changent pas.
Mesuré avant : 155 e-mails des deux côtés, **0 nom différent**, même ensemble de négociateurs actifs (0 d'un côté sans
l'autre). Build vert. ⏳ À pousser, puis voir la fenêtre de répartition et un nom dans Transactions.
Reste à l'étape 3 : les DROITS (`app_mes_chaines_nommees`, ce que voit un négociateur).

## 27. LES MENUS DE CHOIX DE NÉGOCIATEUR — inventaire et DÉCISIONS de Frédéric (05/11) — ⛔ rien n'est codé

Inventaire complet (agent de recherche, lecture seule) : 6 menus de saisie (nouvelle annonce/estimation, réaffecter le
négociateur d'un bien, répartition des honoraires, création de contact, modification de contact, + une ancienne version
morte), les filtres « Négociateur » des listes (Annonces, Estimations, Contacts, Registre des mandats, Suivi, mobile),
Pilotage, Transactions, l'agenda global, l'outil Utilisateurs. Constat de fond : pour un compte `commercial`, `dataScope`
(App.tsx:14461) ne charge QUE sa fiche dans `hektorNegotiators` — d'où sa présélection, mais aussi des filtres réduits.

**Décisions (05/11)** :
- SAISIE / MODIFICATION : un négociateur a SON NOM d'office (son agence aussi ; s'il a plusieurs fiches, le choix entre
  SES agences seulement). Admin / manager : actifs d'agences actives, case à cocher « comptes d'agence » (on peut choisir
  une agence, mais derrière la case). Valeur déjà en place : affichée, « ancien » s'il l'est, non choisissable pour une
  nouvelle ligne.
- MODIFICATION D'UN CONTACT : le négociateur ne peut que GARDER la valeur en place ou mettre SON nom (« OK ta propo »).
  ⚠ À vérifier avant de coder : ce que `app_edit_contact_optimistic` fait du compte choisi.
- AGENDA : un négociateur n'a accès qu'à SA boîte — plus de saisie libre d'une autre adresse.
- FILTRES : tout le monde voit tout le monde (tous les comptes ont le périmètre « réseau », mesuré : 8 comptes sur 8),
  case à cocher « afficher les anciens » (décochée par défaut). Pilotage, Transactions, Utilisateurs : la même case.
- Réaffecter le négociateur d'un bien : masquer l'entrée pour un négociateur (aujourd'hui : un message d'erreur).
- Une seule fonction d'app (registre, mode saisie / filtre / administration, valeur en place) servira tous les menus.

## 28. ⛔ PAS DE COMPTES D'AGENCE DANS LES CHOIX DE NÉGOCIATEUR (05/11) — décision de Frédéric

« Les comptes agences n'ont rien à faire dans le choix des négociateurs. » La case « comptes d'agence » (§27) est
ABANDONNÉE — elle n'avait jamais été codée. Vérifié le 05/11 : les menus de choix proposent 30 personnes, comme
l'annuaire avant le registre, 0 agence. Ce qui reste, et pourquoi :
- `agence_id_user` sur les fiches (§23) : numéro TECHNIQUE envoyé à Hektor AVEC le négociateur choisi (Hektor l'exige pour
  changer le négociateur d'un bien ou créer un contact) — n'ajoute aucune agence au choix ; À GARDER.
- le rattachement des comptes d'agence (§25) : GARDÉ (« Oui, garde-le »). Seul effet affiché : 290 lignes de répartition
  2006-2012 du compte n° 24 (« Cet utilisateur a été supprimé » chez Hektor) passent de « Négociateur supprimé » à l'agence
  du Puy dans le pilotage ; Ambert (8 lignes) était déjà à Ambert ; les comptes 22 et 25 ne portent aucune ligne.
Le plan des menus (§27) continue SANS agences.

## 29. Menus de choix, 1re livraison (05/11) — Frédéric : « Oui, commence »

- MODIFICATION D'UN CONTACT : le comportement voulu EXISTAIT déjà (un négociateur ne voit que son nom + le négociateur en
  place du contact → il garde ou met son nom). Ajouté : « (ancien) » à côté du négociateur en place quand sa fiche est
  inactive (`HektorNegotiatorOption.actif`, rempli par `loadNegotiatorOptionForContact` depuis le registre ou l'annuaire).
- RÉAFFECTER LE NÉGOCIATEUR D'UN BIEN : l'entrée du menu « Plus » de la fiche bien est MASQUÉE pour un négociateur (elle ne
  lui montrait qu'une erreur). Les panneaux photos / documents / mandat gardent leur message « demande à un admin ».
- AGENDA GLOBAL : pour un négociateur, le champ « Agenda » est en lecture seule sur SA boîte, et l'agenda lu (et celui où se
  crée un RDV) est ramené à sa boîte s'il en différait. Admin et manager inchangés.
- Build vert. ⏳ À pousser. ⏳ Reste le gros morceau : les FILTRES « Négociateur » (tout le monde pour tous, case « afficher
  les anciens ») et la même case dans Pilotage, Transactions, Utilisateurs.

## 30. « SES BIENS » DEVIENT UN PRÉFILTRE RETIRABLE ; LE FILTRE « NÉGOCIATEUR » POUR TOUS (05/11) — Frédéric : « vas y »

**Le constat** : depuis la 1re version de l'app (07/04/2026), un compte `commercial` avait une BARRIÈRE d'écran
(`dataScope` = son e-mail) sur toutes ses listes — alors que la base lui ouvre le réseau depuis le chantier ② (12/10,
réglage « Tout le réseau »). Ce n'était pas une décision : un reste. Son filtre « Négociateur » ne montrait que lui.

**Le code** (`App.tsx`) :
- `listScope` remplace `dataScope` pour les LISTES (annonces, mandats, contacts, travaux), leurs compteurs, la présence
  des diffusions, « annonces ailleurs ». `dataScope` reste la barrière des usages internes (bien d'un travail, saisie des
  mandants, menus de saisie = son nom d'office).
- Préfiltre « Mes biens » / « Mes contacts » en tête du filtre « Négociateur » pour un négociateur, actif à l'ouverture ;
  « Tous » ou un collègue le retire ; « Réinitialiser » le remet. La recherche globale porte sur le réseau.
- ⛔ **Le réglage du compte est respecté** (question de Frédéric) : un compte « Son agence » ou « Ses biens seulement »
  garde la barrière d'écran (son préfiltre ne se retire pas), ET la base l'applique de toute façon — vérifié le 05/11 :
  `app_dossiers_current`, `app_contacts_current`, `app_work_items_current` sont en `security_invoker`, et les règles des
  tables (`app_dossier_current`, `app_contact_current`) lisent `app_perimetre_courant()`. Aujourd'hui les 8 comptes sont
  « réseau ».
- Le filtre « Négociateur » (7 endroits, une seule fonction `renderFiltreNegociateur`) : le catalogue est construit sur
  tout ce que la base laisse voir ; les noms qui ne sont plus actifs au registre (`loadNomsNegociateursActifs`) ne
  paraissent qu'avec la case « Afficher les anciens » ; la valeur en place reste proposée. Mesuré : 41 noms portés par les
  biens → 34 par défaut, +7 avec la case (Aline VALETTE, Cyril LACHAIZE, Groupe GTI, gti immobilier, Pierrick MARTINEZ,
  Vincent-Lucas GONZALEZ, Vivien BERGER). Lecture ratée du registre → tous les noms montrés.
- Build vert. ⏳ À pousser, puis voir à l'écran (admin : la case ; un négociateur : « Mes biens » retirable).

**⛔ Trouvé en vérifiant, PAS corrigé (écriture en base, accord requis)** : la vue `app_registre_mandats_current` n'est PAS en
`security_invoker` et `authenticated` a le droit de la lire → elle lit `app_mandat_register_current` (règle : admin et
manager seulement) avec les droits de son propriétaire. L'ÉCRAN du registre est réservé admin/manager, mais un compte
négociateur peut lire tout le registre par l'API. Remède : `alter view … set (security_invoker = true)` — à mesurer avant
(qui la lit : `loadMandatRegisterPage`, `loadMandatFilterCatalog`…).
- ✅ **EN LIGNE et vu le 05/11** (Vercel `index-2sJGO2mP.js`, Chrome de Frédéric, compte admin, liste Annonces) : filtre
  « Négociateur » = 35 noms (+ Tous, Sans) sans la case ; la case « Afficher les anciens » en ajoute 13 (Aline VALETTE,
  Charlène PARANIER, Cyril LACHAIZE, Frédéric MONNE, Groupe GTI, gti immobilier, Hélène DEFOUR, Négo GTI, Nicole VURPILLOT,
  Pierrick MARTINEZ, Stéphane PIOCHEL, Vincent-Lucas GONZALEZ, Vivien BERGER) — plus que les 7 mesurés sur les biens seuls,
  le catalogue reprenant aussi mandats et travaux. Case remise décochée. ⚠ Non vu : le préfiltre « Mes biens » d'un compte
  négociateur (pas de session négociateur pour l'essai).

## 31. ✅ LA FAILLE DU REGISTRE DES MANDATS FERMÉE (05/11) — Frédéric : « Oui, audite et corrige »

**Le défaut** : `app_registre_mandats_current` (vue) n'était pas en `security_invoker` → elle lisait
`app_mandat_register_current` (règle : admin/manager seulement) avec les droits de son propriétaire ; `authenticated` a
SELECT. Mesuré avec le compte de Mélanie LEGRAND : 24 577 lignes par la vue, 0 par la table. Un compte réglé « Ses biens
seulement » aurait lu tout le registre.
**Pourquoi pas « fermer »** : lecteurs mesurés dans le code — écran Registre (admin/manager), recherche globale (catégorie
mandats, négociateurs compris), `loadRegisterCycleAffaires` (fiche d'un bien : date de clôture du mandat, charge des
honoraires, offre / compromis / vente — tous les jours pour les négociateurs), `loadMandatFilterCatalog`, pastille « fiche
de mandat ailleurs », vue `app_filter_catalog_registre`. Fermer aurait vidé la fiche de leurs biens.
**Le remède posé** (`supabase/patch_registre_mandats_perimetre_2026-11-05.sql` + `_INVERSE`, migration
`registre_mandats_perimetre_2026_11_05`) : une 2e règle de lecture sur la table, COPIE de celle des biens (réseau / agence /
portefeuille), et la vue en `security_invoker`. Éprouvé dans une transaction annulée : Mélanie « réseau » 24 577 (inchangé),
Mélanie « ses biens seulement » 346 (les siennes), admin 24 577, catalogue 93. Vérifié après la pose : Mélanie lit 24 577 par
la VUE et par la TABLE ; témoin positif — elle voit le cycle de son bien 62527 (mandat 18712) et de 59393 / 61739.
Aucun changement pour les 8 comptes actuels (tous « réseau ») ; la faille est fermée pour les réglages restreints.

## 32. La case « Afficher les anciens » partout (05/11) — Frédéric : « ON ENCHAINE ALORS »

- PILOTAGE (menu « Négociateur ») : les personnes inactives au registre ne paraissent qu'avec la case ; les agences restent
  (« · agence ») ; la personne choisie reste proposée. Style `.pl-filtre.pl-case`.
- TRANSACTIONS (menu admin « Négociateur ») : même règle, la mention « · ancien » ajoutée ; un e-mail inconnu du registre
  reste montré (rien n'est caché sur une lecture incomplète).
- OUTIL UTILISATEURS (« Personne du registre », création et modification) : par défaut les 34 personnes actives au lieu de
  167 ; la case « Afficher les anciens dans « Personne du registre » » montre tout ; la personne déjà reliée ou choisie reste.
- Build vert. ⏳ À pousser et voir à l'écran.
- ✅ **VU EN LIGNE le 05/11** (Vercel `index-B75ACLSC.js`, Chrome de Frédéric, compte admin) : PILOTAGE 35 noms sans la
  case, 44 avec (9 « · ancien » : Aline VALETTE, Anne FARGET, Cyril LACHAIZE, Frédérique JORAND, Hugo LABBE, Joel
  CHAMPAGNAC, Lucie DECHANDON, Vincent-Lucas GONZALEZ, Vivien BERGER) ; TRANSACTIONS 29 sans, 35 avec (6 anciens) ;
  UTILISATEURS « Personne du registre » 34 sans, 167 avec. Cases remises décochées, tiroir refermé, rien d'enregistré.

## 33. MAQUETTE « REGISTRE DES UTILISATEURS » (05/11) — Frédéric : « oui » — ⛔ rien n'est codé

Idée de Frédéric : un vrai écran admin, ouvert par le bouton « Utilisateurs », avec le listing du registre et ses
fonctions (dont « Ajouter un utilisateur »). Maquette (données réelles du 05/11) :
https://claude.ai/artifact/XMLpyh5kDkfpXPwGTB5738 — trois écrans :
1. LA LISTE : 6 chiffres (185 personnes, 34 actifs, 133 anciens, 18 agences, 8 comptes dont 5 reliés, 34 à valider),
   recherche, agence, type, « Tous / Avec un compte / Sans compte / À valider », case « Afficher les anciens » (vivante),
   une ligne par PERSONNE du registre (type, agence active, n° Hektor, compte de l'app, statut).
2. LA FICHE (exemple réel : Dylan JOURGET, 4 fiches dont 3 disparues le 05/11) : ses fiches Hektor, son journal, son compte
   de l'app (« Créer son compte »), ce qu'il y a à valider (« Marquer traité »), ce que l'app retient de lui.
3. AJOUTER : le formulaire d'aujourd'hui en pleine page, la personne du registre déjà proposée quand on vient de sa fiche,
   et le message de résultat.
À trancher à la validation : qui y accède (admin seul, ou managers aussi comme l'outil actuel) ; ce qu'on fait des 34
« à valider » (une file de travail ?) ; l'ajout d'un ancien sans fiche Hektor (les 14 du classeur).

## 34. AUDIT (05/11) — les COORDONNÉES des utilisateurs et un REGISTRE DES AGENCES, en vue de la coupure

Frédéric : « il manque dans mon registre de récupérer et conserver les coordonnées mail etc. des utilisateurs … pour avoir
un registre des utilisateurs complet et utilisable de manière autonome avec nos id. Également il faut un registre des
Agences similaire … impossible d'ajouter une agence avant la coupure donc on note « À venir » sur le bouton ajouter ».

**Ce que Hektor fournit sur un NÉGOCIATEUR** (listes `list_negos` / `list_negos_inactive` et `nego_by_id`, les mêmes
12 champs ; local `data/hektor.sqlite` `hektor_negociateur.raw_json`, 219 fiches) : id, idUser, agence, nom, prénom,
fonction (un CODE : 159, 465…), téléphone, portable, e-mail, couleur, logo, avatar (photo, URL du CDN de Hektor). Rien
d'autre par l'API (ni adresse, ni signature, ni carte).
**Ce que le registre garde** : par FICHE `nom_vu` (prénom + nom collés), `email_vu`, téléphone, portable, agence, les
numéros ; par PERSONNE seulement `nom` et `email`. **Manquent** : prénom / nom séparés, fonction, photo, logo, couleur — et
surtout des coordonnées À NOUS sur la personne (aujourd'hui elles ne vivent que sur les fiches, recopiées de Hektor
chaque nuit : à la coupure elles se figent sans qu'on puisse les tenir).

**Ce que Hektor fournit sur une AGENCE** (`list_agences`, local `hektor_agence.raw_json`, 19 agences) : id, idUser (compte
d'agence), nom, alias, mail, tél, fax, site, responsable, couleur, logo, avatar, **barème** (URL d'un document), parent,
type ; **informations juridiques** (forme, raison sociale, SIRET, NAF, capital, RCS et sa ville, TVA, siège social,
signature, téléphone et e-mail de la société, RCP, RSAC, médiateur et son adresse, assureur et son adresse) ; **carte
professionnelle** (type, numéro, délivrée par, DATE DE VALIDITÉ — ex. 14/09/2027 —, détenteur, maniement de fonds, garant,
montant, adresse et compte du garant). ⚠ Pas d'adresse postale de l'agence elle-même dans l'API (seulement le siège).
**Ce que la base de l'app garde** : `app_agence_directory` = id, compte, nom, mail, tél, responsable, parent — le reste
(juridique, carte, barème, logo) n'existe QUE dans le fichier local de la nuit, pas dans la base de l'app.
**Fichiers hébergés chez Hektor** (photos des négociateurs, logos, barèmes) : à RECOPIER chez nous avant la coupure.
⛔ Rien n'est codé. Proposition au §35 (à valider).

## 35. AUDIT D'INTÉGRATION — registre des UTILISATEURS et des AGENCES (05/11) — ⛔ rien n'est codé

Frédéric : « audit ce projet registre utilisateur et agence pour être sûr de son intégration dans mon app ».
Règle du projet suivie : le modèle des autres registres (notre n°, n° Hektor à côté, jamais supprimé, tenu chaque nuit,
« Hektor confirme, il n'écrase pas » : un champ modifié dans l'app devient le nôtre, un écart de Hektor se signale).

### 35.1 Ce que l'app lit AUJOURD'HUI (mesuré dans le code le 05/11)

AGENCES — toujours par leur NOM écrit, jamais par un numéro :
- worker `console_job_worker.js:8481` : bloc « Agence » des PDF générés (`generate_mandat_document`, `generate_estimation_pdf`)
  = tél, mail, responsable par `app_agence_directory?nom=ilike.<nom>` ; repli du tél/mail du conseiller sur ceux de l'agence ;
- backend `appointment_service.py` (l. 354, 441-469) : tél/mail de l'agence sur les pages publiques RDV/estimation ; agence
  par défaut, par id, par clé ;
- front `loadHektorAgencyOptions` (`api.ts`) : menus d'agence (réaffecter un bien, créer un contact) ;
- pilotage, filtres, droits « Son agence » (`app_mon_agence()`) : comparent `agence_nom` en TEXTE.
COORDONNÉES DES NÉGOCIATEURS :
- registre (déjà) : pages RDV / estimation (`_load_registre_negociateur`), menus, pilotage, Transactions ;
- ANNUAIRE de Hektor (encore) dans le worker : l. 2406 et 2837 (compte qui exécute un geste ; « source de vérité
  actif/inactif »), l. 2875 `loadAgencyDirectoryRowForOwner` (coordonnées du conseiller dans les PDF), l. 6350-6361 ;
- Google Workspace pour l'agenda et l'e-mail (inchangé, propre à l'app).
Le juridique et la carte professionnelle des agences ne sont lus NULLE PART dans l'app (les « SIRET » du code sont ceux des
contacts société).

### 35.2 Ce que les données disent (mesures)

- 30 écritures différentes du nom d'agence dans biens / mandats / contacts → 29 après nettoyage (espaces, accents, casse) :
  « Groupe GTI Ambert␣␣␣ », « COURPIÈRE » ≠ « Groupe GTI COURPIERE », « Groupe Gti Le Puy en Velay »… → un registre des
  agences doit porter les ALIAS (toutes les écritures connues) pour rattacher chaque ligne à NOTRE n° d'agence.
- Juridique : rempli sur UNE agence (« Compte formation » = la société Groupe G.T.I : SIRET 502 811 144 00018, RCS, TVA
  FR24502811144, capital 309 968, siège 22 rue Jean Jaurès 42700 Firminy, RCP Allianz 60583928, médiateur ANM Conso) ; un
  SIRET d'établissement sur une autre ; 17 vides.
- Carte professionnelle : LA MÊME pour les 19 (CPI 4202 2019 000 043 878, CCI Saint-Étienne, détenteur Franck GERPHAGNON,
  valable jusqu'au 14/09/2027). Barème et logo : 1 seul fichier chacun, communs.
- Coordonnées douteuses chez Hektor : Courpière → ambert@, Saint-Just-Saint-Rambert → montbrison@, Saint-Didier → monistrol@.
- Fonction des négociateurs : un champ MÉLANGÉ (« Collaborateur » 51, « Négociateur » 22, « Négociatrice » 19… et ~60
  CODES numériques sans libellé). Photos : 10 personnalisées, les autres = image par défaut de Hektor.

### 35.3 Le modèle proposé

1. **La SOCIÉTÉ** (une ligne, notre n°) : raison sociale, forme, SIRET, NAF, capital, RCS et sa ville, TVA, siège, RCP et
   assureur, médiateur, CARTE PROFESSIONNELLE (n°, délivrée par, validité, détenteur, garant), barème, logo. Source : la
   fiche Hektor qui porte le juridique ; le reste à saisir chez nous.
2. **Les AGENCES** (notre n° 2000001+) : nom, ALIAS (écritures connues), mail, tél, responsable, adresse (à saisir — Hektor
   ne la donne pas), SIRET d'établissement, n° Hektor de l'agence et du COMPTE d'agence, actif. Bouton « Ajouter une
   agence » = « À venir » (Frédéric : impossible avant la coupure).
3. **Les PERSONNES** (registre actuel) gagnent leurs COORDONNÉES À NOUS : civilité, prénom, nom, e-mail pro, tél, portable,
   fonction (texte libre, reprise de Hektor quand c'est du texte), photo (recopiée chez nous).
4. **Le carnet** (même patron que `app_mandat_champ_app`) : un champ modifié dans l'app y est écrit (qui, quand) ; la nuit ne
   le touche plus ; un écart avec Hektor devient un signal « à valider » dans la fiche.
5. **Les fichiers** (10 photos, logo, barème) : recopiés dans notre stockage (CDN de Hektor, hors quota d'API), seulement
   quand ils changent.

### 35.4 Les gestes (objets × gestes)

| | créer | modifier | désactiver / archiver | lire |
|---|---|---|---|---|
| société | non (une seule) | admin, dans l'app (carnet) | non | admin ; mentions des documents |
| agence | « À venir » (après la coupure) | admin (carnet) ; Hektor la nuit sauf champs du carnet | la nuit (absente de Hektor) ; jamais supprimée | tous les comptes actifs |
| personne | la nuit (fiche Hektor) ; l'outil Utilisateurs (née dans l'app) | admin (carnet) ; Hektor la nuit sauf carnet | la nuit (fiches inactives) | tous les comptes actifs |
| compte de l'app | admin (outil Utilisateurs) | admin | admin (case « actif ») | admin |
| fichiers (photo, logo, barème) | la nuit (recopie) ; admin (dépôt) | admin | — | tous |
| signal / écart | la nuit | admin : « Marquer traité » / « garder la nôtre » / « prendre celle de Hektor » | — | admin |

### 35.5 Ce que ça pourrait casser ailleurs — et l'ordre proposé

- Les lecteurs par NOM d'agence (worker PDF, RDV, droits « Son agence », pilotage) : on ne les touche PAS au début ; le
  registre des agences vient À CÔTÉ ; on bascule un lecteur à la fois, chacun avec son « vas-y » (comme pour les négos).
- Le WORKER : 5 lectures de l'annuaire → à basculer en dernier, fichier partagé avec l'autre session (blocs non commités) ;
  redémarrage des 4 services, file vide.
- La purge de nuit de l'annuaire et de `app_agence_directory` sans plancher (B6 / L10-8e, toujours ouvert) : le registre
  des agences, jamais purgé, en protège les lecteurs une fois basculés.
- Droits : coordonnées et agences lisibles par tout compte actif (comme aujourd'hui) ; société / carte / carnet / signaux :
  admin seulement ; écriture : aucune pour `authenticated` (piège des droits par défaut — révoquer).
- Données à corriger À LA MAIN dans le carnet (mails d'agence croisés, adresses d'agence, fonctions en code).

Ordre : (1) maquette complétée (coordonnées, écarts, société, agences, « À venir ») → (2) tables + nuit à blanc (rien lu
par l'app) → (3) écrans Registre des utilisateurs / des agences → (4) recopie des fichiers → (5) lecteurs un par un
(RDV, PDF du worker, menus d'agence, filtres, droits) → (6) le jour de la coupure : rien à convertir.

## 36. ÉTAPE 1 DU §35 FAITE — la maquette est complète (05/11) — Frédéric : « Oui, étape 1 » — ⛔ rien n'est codé

Maquette : https://claude.ai/artifact/XMLpyh5kDkfpXPwGTB5738 (canevas, version 7), six écrans :

1. **Utilisateurs — la liste** : onglets Utilisateurs / Agences / La société ; compteurs (185 personnes, 34 « à valider ») ;
   recherche, segments, case « Afficher les anciens » ; bouton « Ajouter un utilisateur ».
2. **Utilisateurs — la fiche** (Dylan JOURGET) : les COORDONNÉES À NOUS, champ par champ avec leur source (« repris de
   Hektor » / « modifié dans l'app » / « à saisir ») ; ses 4 fiches Hektor ; le journal ; un ÉCART à valider (« Garder la
   nôtre » / « Prendre celle de Hektor ») ; l'encart « Ce que l'app retient ».
3. **Ajouter un utilisateur** : le formulaire et le message de résultat.
4. **Agences — la liste** : 19 lignes sous notre n° 2000001+ ; « Ajouter une agence » GRISÉ avec la pastille « À venir » ;
   compteurs (17 agences + Compte formation + Agences supprimée · 30 négos actifs · 8 e-mails à vérifier · 19 à saisir) ;
   les 8 e-mails croisés marqués ⚠.
5. **Agence — la fiche** (Groupe GTI Saint-Étienne, n° 2000014, Hektor 18 / compte 25) : coordonnées à nous, adresse et
   responsable « à saisir » ; les ÉCRITURES DE SON NOM (alias) ; ses numéros Hektor, dont l'ancienne fiche négo n° 2
   gardée ; ses négos actifs ; l'écart de l'e-mail (firminy@) à valider.
6. **La société** (Groupe G.T.I) : informations juridiques reprises de la fiche « Compte formation » ; la CARTE
   PROFESSIONNELLE (T, CPI 4202 2019 000 043 878, CCI Saint-Étienne, F. GERPHAGNON, valable au 14/09/2027) avec un rappel
   3 mois avant ; barème et logo « à recopier ».

⚠ Correction en passant : la liste des agences disait « 7 e-mails à vérifier » alors qu'elle en marque 8 (Courpière,
Dunières, Issoire, St-Bonnet, St-Didier, St-Étienne, St-Just, Yssingeaux) — corrigé à 8, comme au §34.

**À trancher par Frédéric avant l'étape 2** (rien n'est choisi) :
- qui ouvre ces registres : les administrateurs seuls, ou aussi les managers ;
- les 34 « à valider » : une file de travail à vider, ou un simple repère dans la fiche ;
- ajouter un ANCIEN sans fiche Hektor (les 14 anciens du classeur) : permis dès maintenant, ou après la coupure ;
- l'agence n° 26 « Agences supprimée » : gardée dans la liste (statut « Supprimée ») ou cachée par défaut.

➡ Étape suivante (2) : tables + nuit à blanc — ⛔ écriture en base de production, ACCORD OBLIGATOIRE.

## 37. La maquette retournée : CES REGISTRES SONT LES NÔTRES (05/11) — Frédéric — ⛔ rien n'est codé

Sa consigne : « il faut que ce registre soit plus orienté vers l'app que vers Hektor ; il est important de savoir sur quel
id est reliée la fiche utilisateur et laquelle est active chez Hektor, mais ce n'est pas ce que l'on doit voir en premier ».

Ce qui a changé (maquette, version 10) :
- **Liste des utilisateurs** : personne (notre n°, l'e-mail À NOUS), fonction, agence, portable, ACCÈS À L'APP (rôle,
  périmètre, dernière connexion), statut chez nous. Hektor n'a plus qu'une colonne grise « Synchro Hektor » (à jour /
  1 écart / éteint) dont le survol donne les numéros. Les 18 comptes d'agence sortent de la liste (registre des agences).
  Nouveau : « Comptes de l'app reliés à personne · 3 » (codex.test@, franck.gerphagnon@gmail.com désactivé,
  sashagerphagnon@gmail.com désactivé).
- **Fiche** (exemple Franck GERPHAGNON, n° 1000036) : « Qui il est » → « Son accès à l'app » (+ ses deux autres comptes
  non reliés, dont `gmail.ccom` = faute de frappe, jamais connecté) → historique → **« Synchro avec Hektor » en bas** :
  par quelle fiche l'accès agit chez Hektor (négo n° 1), et ses 3 fiches (négo 1 active, compte 7 actif, négo 19 éteinte).
  L'écart d'e-mail (gti contre gmail.com) est l'exemple « À valider ».
- **Ajouter** : identité, fonction, agence, portable d'abord ; puis l'accès ; « Déjà au registre ? » ; le lien Hektor
  se fait « en coulisse ».
- **Agences / fiche d'agence / société** : nos numéros et nos coordonnées d'abord ; les numéros Hektor en dernière colonne
  grise ou dans « Synchro avec Hektor » en bas.

Mesures du 05/11 reprises dans la maquette : 167 personnes hors agences, 34 actives (champ `actif` du registre), 133
anciens, 34 « à valider », 5 comptes de l'app reliés. ⚠ Le champ `actif` du registre dit déjà « actif chez nous » :
toi, Pauline, Caroline et Delphine BLANCHARD y sont ACTIFS ; ce sont les MENUS qui lisent la fiche négo (`actif_chez_hektor`).
La règle reste à trancher (§36).

## 38. MAQUETTE VALIDÉE ET QUATRE DÉCISIONS (05/11) — Frédéric : « oui » — ⛔ rien n'est codé

La maquette orientée app (§37, version 10) est validée. Décisions, dans ses réponses :
1. **Règle de l'actif dans les menus de négociateurs (filtres, saisie) : « actif chez nous »** — le champ `actif` de
   `app_negociateur_personne` décide, plus `actif_chez_hektor` de la fiche négo. Effet mesuré : Frédéric, Pauline,
   Caroline et Delphine BLANCHARD redeviennent actifs dans les menus (30 → 34). Les comptes d'agence restent HORS des
   choix de négociateurs (décision du 05/11, inchangée). ⚠ C'est une modification de code EXISTANT (front) : « vas-y » à
   demander ; lecteurs à basculer : `loadHektorNegotiatorOptions`, `loadNegotiatorOptionForContact`,
   `loadNomsNegociateursActifs` (api.ts), et les filtres qui s'en servent.
2. **Accès aux deux registres : administrateurs seuls.**
3. **Ajouter une personne sans fiche Hektor : permis dès maintenant** (notre numéro tout de suite ; les 14 anciens du
   classeur pourront être saisis).
4. **L'agence n° 26 « Agences supprimée » : VISIBLE dans la liste**, statut « Supprimée ».
- Non tranché explicitement, gardé tel que maquetté : les « à valider » sont un repère à côté du nom + un filtre, pas une
  file de travail.

➡ Suite : (a) la règle de l'actif dans les menus (code front, « vas-y ») ; (b) étape 2 du §35 — tables + nuit à blanc
(⛔ écriture en base de production, ACCORD OBLIGATOIRE).

## 39. « ACTIF CHEZ NOUS » : seulement ce qui reste dans l'app (05/11) — Frédéric : « il faut surtout pas casser les workers », « pour tous les gestes qui communiquent avec Hektor !!!! »

**La règle posée** : tout geste qui COMMUNIQUE AVEC HEKTOR garde les fiches négociateur ACTIVES CHEZ HEKTOR (le numéro part
chez lui par le worker ; une fiche éteinte = un refus, ou un bien rangé sous une fiche que son écran ne montre plus). Ce qui
reste dans l'app suit « actif chez nous » (champ `actif` de `app_negociateur_personne`).

L'audit des lecteurs (code, 05/11) :
- **déjà « actif chez nous »** : les filtres « Négociateur » (`loadNomsNegociateursActifs` lit aussi les personnes
  actives) ; les menus du Pilotage et des Transactions (`p.actif`).
- **communiquent avec Hektor → INCHANGÉS** : `loadHektorNegotiatorOptions` (création d'annonce, réaffecter, propriétaire
  d'un contact, boîte de l'agenda, RDV) et `loadNegotiatorOptionForContact` (fiche contact).
- **reste dans l'app → BASCULÉ** : `loadRepartitionPersonnes` (choix des personnes de la répartition des honoraires).
  Preuve qu'elle ne part pas chez Hektor : `console_job_worker.js` l. 14582 (« la répartition de commission ne part plus
  chez Hektor ») et l. 22818 (`app_repartition_commission_set` → aucun travail).

Le correctif (`apps/hektor-v1/src/lib/api.ts`, `loadRepartitionPersonnes`) : les 30 fiches actives comme avant, PLUS les
personnes actives sans fiche négo active, chacune avec SA fiche la plus employée dans les répartitions (à défaut la plus
récente). Mesure du 05/11 : 30 → 34, avec Frédéric n° 46 (40 lignes), Caroline n° 49 (156), Delphine BLANCHARD n° 45 (56 —
et non 114, la plus récente, 0 ligne), Pauline n° 41 (2). Repli sur l'annuaire inchangé. `npm run build` vert. ⏰ À voir en
ligne après le push : la liste de la répartition doit montrer les 4 noms.

**Contrôle en ligne (05/11, après le push de 02468bd)** : Vercel a servi `index-BzMLpYk6.js`, qui porte le code neuf. Dans
l'app ouverte avec la session de Frédéric, les mêmes lectures que `loadRepartitionPersonnes` rendent 219 fiches, 30 numéros
actifs chez Hektor + 4 ajouts = **34** : Caroline → 49 (156 lignes), Delphine BLANCHARD → 45 (56), Pauline → 41 (2),
Frédéric → 46 (40). ⚠ Non vu : la modale de changement de statut elle-même (pas ouverte, pour ne rien enregistrer).
⚠ Réserve : un NÉGOCIATEUR ne lit `app_affaire_repartition` que sur son périmètre (politique `app_affaire_repartition_read`)
— pour lui, le choix de la fiche peut retomber sur « la plus récente » (ex. Delphine → 114). Sans effet sur les comptes :
le Pilotage retrouve la part par la PERSONNE, quelle que soit la fiche.

## 40. ÉTAPE 2 POSÉE : les tables et la tenue de nuit À BLANC (05/11) — Frédéric : « Oui, étape 2 »

**Posé en production** (`supabase/patch_registre_utilisateurs_agences_etape2_2026-11-05.sql`, migration appliquée ;
retour arrière `..._INVERSE.sql`) — additif, TABLES VIDES, rien n'est lu par l'app, aucun worker touché :
- `app_registre_societe` (une ligne, n° 3000001), `app_registre_agence` (n° 2000001+, n° Hektor à côté, jamais
  supprimée), `app_registre_agence_alias` (clé = `app_neg_cle_agence`, la même que `cleAgence` du front),
  `app_registre_champ_app` (LE CARNET), `app_registre_journal` (pose / changement / nouvelle / disparue / réapparue / écart) ;
- `app_negociateur_personne` + 9 colonnes vides : civilité, prénom, nom de famille, fonction, agence (notre n°), e-mail
  pro, téléphone, portable, photo ;
- `app_registre_poser` + `app_registre_utilisateurs_agences_maintenir(p_agences, p_negos, p_a_blanc)` : « Hektor
  complète, il n'écrase pas » (une valeur vide n'efface rien ; un champ du carnet n'est jamais écrit, un écart se signale
  une fois par valeur) ; l'e-mail de l'ACCÈS À L'APP fait foi pour l'e-mail pro (une autre adresse chez Hektor = écart) ;
- droits : agences et alias lisibles par les comptes actifs ; société, carnet et journal par les administrateurs ;
  AUCUNE écriture ni exécution pour un compte connecté (contrôlé) ; clé de battement `phase2.registre_agences` déclarée.

**L'essai dans une transaction annulée** (annuaires en base + fiche brute du Compte formation), en ÉCRITURE réelle :
20 agences, société complète (33 champs : SIRET, RCS, TVA, RCP Allianz, médiateur, carte CPI … valable au 14/09/2027),
787 coordonnées ; un 2e passage = 0 changement (idempotent) ; un champ mis au carnet n'est pas écrasé et sort en écart ;
l'écart d'e-mail de Franck sort (gti contre gmail.com). ⭐ **Il a trouvé un défaut** : un compteur de numéros N'EST PAS
annulé par un retour arrière — chaque nuit à blanc aurait brûlé 20 numéros (1re agence née 2000021). Corrigé : à blanc, le
compteur est remis derrière le plus grand numéro posé ; le patch le contrôle (compteur à 2000000 après son essai).

**La vraie nuit, à blanc, avec les listes BRUTES** (`python phase2/sync/maintenir_registre_agences.py --a-blanc`, 19
agences, 219 négociateurs, aucune écriture — vérifié après : 0 agence, 0 journal, compteur 2000000) :
19 agences numérotées EXACTEMENT comme la maquette (2000001 Ambert … 2000007 Firminy … 2000010 Monistrol … 2000014
Saint-Étienne … 2000018 Agences supprimée, 2000019 Compte formation), 19 alias, 134 champs d'agence, 33 de la société,
904 coordonnées de personnes (137 portables, 165 agences rattachées), 1 écart (Franck), **0 écriture d'agence non
rattachée** dans les fiches et les biens. Accents intacts (vérifiés hors console).

**Branché dans le run** (`run_full_pipeline.ps1`, juste après « phase2 registre des negociateurs », non bloquant,
`-MaxAttempts 1`). ⛔ Interrupteur `APP_REGISTRE_AGENCES` ABSENT = éteint : pour la nuit à blanc, Frédéric ajoute
`APP_REGISTRE_AGENCES=blanc` dans le .env (je ne lis ni n'écris le .env). Le passage à `1` = une décision à part, après
lecture du compte rendu de la nuit.
⚠ Pas encore de sentinelle sur les écarts (`app_registre_journal.a_signaler`) : elle viendra avec les écrans (étape 3).

## 41. LE LIEN « COMPTE DE L'APP → COMPTE HEKTOR » PASSE PAR LE REGISTRE (05/11) — Frédéric : « Vas-y »

**La demande** : « ajout d'utilisateur dans l'app qui se relie à l'utilisateur Hektor actif connu » ; puis « moi j'ai un
compte à relier (le compte principal), ensuite Franck, Caroline, Pauline et Delphine sont tous à relier sur des comptes
secrétaires chez Hektor ».

**Audit (code + base, 05/11)** :
- `backend/app/services/supabase_admin.py` cherchait le compte Hektor **par l'e-mail seul**, et **seulement parmi les
  NÉGOCIATEURS** (`app_user_directory.user_type = NEGO`), **AVANT** de relier le compte à sa personne du registre.
  Résultat sur les 6 comptes de l'app : LEGRAND (30/5) et PEREIRA (51/26) reliés ; Franck (@gti, fiche Hektor en gmail),
  Frédéric, Pauline et le compte d'essai NON reliés.
- Les comptes Hektor de la personne sont DÉJÀ au registre (`app_negociateur_fiche`, sorte `compte_utilisateur`) :
  Frédéric **ADMIN n° 4** · Franck **SECRÉTAIRE n° 7** · Caroline **5** · Pauline **8** (et un 2e, n° 3, adresse
  sashagerphagnon@gmail.com — à confirmer par Frédéric) · Delphine **6**. Caroline et Delphine n'ont pas encore de compte
  dans l'app ; leur e-mail Hektor est le leur, la création les reliera par l'e-mail.
- **Qui lit le lien** : aucune fonction en base, ni le worker, ni la nuit. Le FRONT seul (`App.tsx` ~21140) : le
  négociateur par défaut de la fiche contact et de l'agenda, et ce numéro PART DANS LES GESTES
  (`hektor_user_id` → `resolveHektorExecutionUser`, qui **refuse tout numéro qui n'est pas un NEGO** de
  `app_user_directory` — `loadHektorDirectoryUserById`, console_job_worker.js l. 2384). Le lien entre aussi dans la
  RLS des rendez-vous (`negociateur_email`) et dans le droit Agenda/Gmail d'un négociateur
  (`_assert_workspace_subject_allowed`).
- ⛔ **Donc un compte SECRÉTAIRE ou ADMIN ne peut PAS aller dans `hektor_user_id`** : les gestes partiraient au nom d'une
  secrétaire, ou échoueraient. Deux liens séparés.

**Le correctif (serveur seul, `supabase_admin.py`)** :
1. `create_user` / `update_user` : le **registre d'abord**, puis le compte Hektor (`_personne_reliee`).
2. `_resolve_hektor_google_identity(…, personne)` : l'e-mail garde la priorité ; s'il ne trouve rien, la **fiche
   négociateur ACTIVE de la personne** (`_identite_par_registre`) — seulement s'il y en a **exactement une**, confirmée
   **active par les deux annuaires que lit le worker** ; son e-mail n'est repris que s'il n'appartient à aucune autre
   personne (une boîte d'agence ouvrirait l'agenda et Gmail de l'agence). Jamais une fiche éteinte.
3. Les comptes administrateur/secrétaire de la personne sont **notés** dans `metadata_json.comptes_hektor` (pour l'écran
   du registre, étape 3), **jamais envoyés**.
Mesure de la base au 05/11 : 0 personne à deux fiches actives, 0 fiche active à e-mail partagé, 0 fiche active hors
`app_user_directory` — les garde-fous ne mordent sur personne aujourd'hui.

**Contrôle hors ligne** : `backend/tests/test_lien_hektor_par_registre.py` — **13/13 verts** (les 6 vrais comptes +
5 garde-fous + l'ordre registre → Hektor). **Avarie** : garde-fous retirés → les 4 essais de garde ROUGISSENT, Franck reste
vert (ils mordent vraiment).

**Ce qui reste** : pousser (Render se déploie seul) ; puis **réenregistrer le compte de Franck** dans l'écran Utilisateurs
→ sa ligne doit porter `hektor_user_id 2`, `hektor_negociateur_id 1`, `match_source registre_fiche_active`, et
`comptes_hektor` avec le 7. ⚠ Sa fiche active est rangée dans l'agence « Compte formation » (déjà le défaut de la fiche
contact, par la ruse du nom). ⚠ Le lien reste une PHOTO prise à l'enregistrement : une mise à jour de nuit = étape à part.
Retour arrière : `git revert` du commit.

**✅ PROUVÉ EN RÉEL le 05/11** : poussé par Frédéric, Render sur `71bb15d` (démarré 13:35:06 UTC, lu sur `/health`).
Compte de Franck réenregistré par Frédéric à 13:41:06 → sa ligne porte `hektor_user_id 2`, `hektor_negociateur_id 1`,
`negociateur_email franck.gerphagnon@gmail.com`, `match_source registre_fiche_active`, `agence_nom Compte formation`,
`comptes_hektor [SECRETAIRE 7]`. Le registre n'a pas bougé (toujours relié à son compte @gti, 0 ligne de journal,
0 personne née). Les 5 autres lignes inchangées (aucune n'a été réenregistrée).

## 42. ÉTAPE 3, LOT A : LA MAQUETTE DERRIÈRE LE BOUTON « UTILISATEURS » (05/11) — Frédéric : « Changé la règle d'accès à ce bouton en limitant aux admins donc plus besoin de l'ancien »

**Ses décisions** : réutiliser l'existant (le bouton « Utilisateurs » et les gestes qui marchent) ; après le clic, LA
MAQUETTE validée (§38) ; le bouton réservé aux ADMINISTRATEURS (le tiroir des managers disparaît).

**Ce qui est codé (front seul, lecture seule)** :
- `apps/hektor-v1/src/RegistreUtilisateurs.tsx` + `registre-utilisateurs.css` (préfixe `ru-`) + lectures
  `lib/registreUtilisateurs.ts` : onglets Utilisateurs / Agences / La société ; liste (chiffres de tête, recherche, agence,
  fonction, accès, anciens), fiche d'une personne (qui il est, son accès à l'app, historique = les deux journaux, synchro
  Hektor en bas : la fiche des gestes ET le compte secrétaire « noté, jamais envoyé »), « comptes de l'app reliés à
  personne », registre des agences (liste, fiche, écritures, équipe, e-mails partagés) et la société. Une source illisible
  n'éteint que son bloc.
- La fonction et l'agence non saisies sont DÉDUITES de Hektor et l'écran le dit (« d'après ses comptes / fiches chez
  Hektor ») : fonction = la seule que donnent ses comptes ACTIFS (Franck : négo + secrétaire → « à choisir ») ; agence = sa
  fiche négo active, sinon la seule de ses fiches, sinon « à choisir ».
- `App.tsx` : les TROIS entrées (bouton d'en-tête, menu « Mon compte », menu du téléphone) passent de manager+admin à
  **admin** ; elles ouvrent le registre. « Ajouter un utilisateur », « Lui donner l'accès à l'app » (pré-rempli, personne
  choisie), « Modifier son accès », « Relier à une personne » et « Envoyer un lien de mot de passe » rappellent les gestes
  EXISTANTS (`handleCreateAppUser`, `handleUpdateAppUser`, `handleSendPasswordReset`) : le tiroir s'ouvre par-dessus,
  réduit au formulaire demandé, et se referme après l'enregistrement ; le registre se relit.
- ⭐ Trouvaille : sur TÉLÉPHONE, le bouton « Utilisateurs » n'ouvrait RIEN (le tiroir n'existait que dans le rendu
  ordinateur). Le tiroir et le registre sont maintenant rendus par les deux.

**Contrôle** : `npm run build` vert ; aperçu local (mode sans base) : l'écran s'ouvre sur téléphone et sur ordinateur, le
formulaire de création s'ouvre seul par-dessus. Chiffres attendus en réel (mesurés en base) : 167 personnes dont 133
anciens, 34 actives, 5 accès + 3 comptes reliés à personne, 34 à valider, 18 comptes d'agence. ⏰ À voir EN RÉEL après le
push. Agences et société : vides tant que la nuit n'a pas écrit (l'écran le dit).
Retour arrière : `git revert` du commit (aucune base touchée).

**✅ VU EN LIGNE le 05/11** (Chrome de Frédéric, consultation seule, version Vercel de `d62e757` qui contient `8fe4c3c`) : les
chiffres sont EXACTEMENT ceux de la base — 167 personnes dont 133 anciens, 34 actives, 5 accès + 3 comptes reliés à
personne, 34 à valider, synchro nuit du 05/11. Fiche de Franck : la fiche des gestes n° 1 (Compte formation), le compte
secrétaire 7 « noté, jamais envoyé dans un geste », la fiche 19 éteinte ; agences : « pas encore rempli ».
**Ce que l'œil a trouvé, corrigé dans le commit suivant** :
- « jamais connecté » MENTAIT : `app_google_workspace_identity.last_login_at` n'a JAMAIS été tenue (vide pour les 6). La
  vraie date est `auth.users.last_sign_in_at` (Franck 15/09, Pauline 05/11…) → `list_users` (serveur) l'ajoute à chaque
  compte, en lecture ; si elle n'est pas rendue, l'écran dit « inconnue », jamais « jamais connecté ».
- l'e-mail affiché était celui de Hektor (gmail de Franck) : c'est l'accès @gti qui passe devant (règle de l'étape 2) ;
- « à saisir » pour une fonction → « à choisir » ; le fixe n'est montré que s'il diffère du portable ; la synchro est
  ouverte par défaut (comme la maquette) ; plus de nom d'interrupteur à l'écran.
**✅ RETOUCHES VUES EN LIGNE le 05/11** (Render et Vercel sur `544641a`) : les dates de connexion sont celles de la base
(Franck 15/09, Frédéric 31/10, Pauline 05/11, LEGRAND 20/05, PEREIRA « jamais connecté » — vrai, aucune connexion ; les
3 comptes non reliés : 05/06, 01/06, 01/04) et l'e-mail de Franck est son accès @gti. Lot A clos.

## 43. ÉTAPE 3, LOT C : LA SAISIE AU CARNET, AVEC LE STATUT (05/11) — Frédéric : « Vas-y, avec le statut »

**Audit** : la nuit des agences respecte déjà le carnet (`app_registre_poser` : un champ au carnet n'est plus écrit, un
écart de Hektor est journalisé une fois par valeur) ; mais la NUIT DES NÉGOCIATEURS recalcule `actif` sans le consulter
(`app_negociateur_registre_maintenir`, la boucle « actif recalculé ») → un « ancien » saisi aurait été remis actif.

**Le patch** `supabase/patch_registre_saisie_lot_c_2026-11-05.sql` (+ `_INVERSE`, + `_REPETITION` = 9 contrôles à
coller après) :
- `app_registre_saisir(objet, id, champs)` : un ADMINISTRATEUR (contrôle `is_app_admin()` DANS la fonction) écrit des
  champs d'une personne (civilité, prénom, nom, fonction, agence, e-mail pro, portable, fixe, **actif**), d'une agence
  ou de la société ; la valeur est écrite, INSCRITE AU CARNET (qui, quand) et tracée au journal (`saisie`, avant →
  après, `par`) ; les écarts ouverts du champ se classent. Liste fermée des champs (`app_registre_champs_saisissables`).
- `app_registre_rendre` (le champ sort du carnet, la nuit le repose), `app_registre_trancher` (« garder » / « prendre »,
  ou classer un signal des fiches), `app_registre_personne_vue` (retire « À valider », motif gardé au journal).
- La nuit des négociateurs : UNE ligne ajoutée (`where not exists … champ = 'actif'`), posée par remplacement d'ancre
  sur empreinte vérifiée (`725267743d8fedad1c582d830250673a`).
- ⛔ Rien ne part chez Hektor. Les gestes vers Hektor gardent leurs fiches actives (§39) : le statut saisi ne touche que
  ce qui lit `app_negociateur_personne.actif` (répartition, filtres « anciens »).

**Répétition dans une transaction annulée (05/11), TOUT VERT** : 3 champs saisis (carnet 3, journal 3, à son nom) ;
⭐ UNE VRAIE NUIT DES NÉGOCIATEURS exécutée en écriture : Franck saisi « ancien » RESTE ancien, et le TÉMOIN (Mélanie
LEGRAND mise ancienne SANS carnet) est remis active ; rendre, prendre, garder, écart déjà tranché refusé, « vu », agence
d'essai (n° explicite, compteur non consommé) ; refus : champ interdit, statut vide, agence absente, négociateur (×2) ;
l'INVERSE rend la nuit identique à l'octet (même empreinte). Après annulation : rien n'est resté.
⚠ La pose par l'outil a été REFUSÉE (écriture en production) : Frédéric colle le patch puis la répétition.

**L'écran** (`RegistreUtilisateurs.tsx`, `lib/registreUtilisateurs.ts`) : « Modifier » sur la fiche d'une personne,
d'une agence et de la société (un formulaire, « saisi chez nous · Rendre à Hektor » / « repris de Hektor » sous chaque
champ, la valeur de Hektor en grisé) ; « Le passer en ancien » / « Le remettre actif » en DEUX clics ; « À valider » :
« C'est vu », « Garder la nôtre », « Prendre celle de Hektor ». L'écran se relit après chaque geste.

**La sentinelle** `data.registre_ecart` (warning) dans `monitoring/check_gti_health.py` : les écarts non tranchés de
`app_registre_journal`. (Seule ma ligne est commitée dans ce fichier : l'autre session y a des modifications en cours.)

**Contrôle** : `npm run build` vert (types compris) ; le moniteur charge 45 sondes dont la nouvelle. ⏰ À voir EN RÉEL
après la pose et le push : une saisie sur une fiche, puis la nuit.
**✅ POSÉ le 05/11 vers 14:37 UTC** (Frédéric : « colle le sql et je pousse » ; migration
`patch_registre_saisie_lot_c_2026_11_05`) : les 9 contrôles de la répétition sont VERTS (carnet vide, aucune saisie). La
nuit des négociateurs a maintenant l'empreinte `a2dab5d05f2b02f0d03357b510679785` (avant : `725267743d…`, que l'inverse
sait retrouver).
**✅ VU EN LIGNE le 05/11** (consultation seule, formulaire ouvert puis ANNULÉ : carnet 0, gestes 0 vérifiés en base) : fiche
de Franck → « Modifier », « Modifier son accès », « Le passer en ancien », « C'est vu » ; le formulaire s'ouvre avec les
valeurs affichées en grisé. Retouches de libellés (commit suivant) : le grisé dit « affiché : » (l'e-mail montré est
l'accès @gti, pas Hektor), le fixe n'est pas proposé s'il égale le portable, un champ vide dit « vide chez nous · la nuit le
remplira » (pas « repris de Hektor »), la phrase « Garder la nôtre » seulement s'il y a un écart.
**✅ PREMIÈRE SAISIE RÉELLE le 05/11 à 14:44:59 UTC, par Frédéric, depuis l'écran** : Caroline GERPHAGNON (1000024),
civilité → « Mme ». La colonne est écrite (`updated_at` 14:44:59), le carnet porte `Mme` À SON NOM, le journal porte
`saisie` (avant vide → Mme, `par` = Frédéric). La chaîne écran → fonction → carnet → journal est prouvée.
À 14:46:10, Frédéric a passé le compte de l'app de Franck en **manager** par « Modifier son accès » (le geste existant) :
le lien Hektor a été recalculé et reste juste (`registre_fiche_active`, 2/1). ⚠ C'est le RÔLE dans l'app, pas la fonction
du registre (`fonction` toujours vide) — à confirmer : un manager n'a plus l'écran Utilisateurs, ni Pilotage, ni Santé.
**Rectifié le 05/11 à 14:54 UTC** (Frédéric : « Non, remets admin ») : le compte de Franck est remis **administrateur** par
le geste existant (« Modifier son accès », depuis le registre, dans le Chrome de Frédéric). Vérifié en base : rôle admin,
actif, tout le réseau ; lien Hektor recalculé et juste (2/1, `registre_fiche_active`, 14:54:12) ; registre toujours relié.


## 44. Le ménage du compte n° 3, et l'abandon du lot B (05/11)

- **Lot B ABANDONNÉ** (Frédéric) : pas d'« ajouter une personne sans accès à l'app ». Après la coupure, un utilisateur
  n'existe que par son compte de l'app (la création de compte fait déjà naître la personne) ; les personnes sans compte
  sont l'historique repris de Hektor.
- **Compte Hektor n° 3** (« Pauline GIRINON », sashagerphagnon@gmail.com, dernière connexion 09/10/2025) : un compte
  d'ESSAI, rangé sous l'agence COMPTE FORMATION, INACTIF — visible seulement avec le filtre « Tous les comptes » de
  l'organigramme (vu dans le Chrome de Frédéric). ⛔ Le champ `state` de `UsersOfParent` vaut '1' pour les 20 comptes,
  inactif compris : ce n'est PAS l'indicateur actif. Fiche 1000088 figée `rattache_par = 'decision'`,
  `actif_chez_hektor = false` (la nuit saute les fiches « decision »), tracé au journal. Le vrai compte de Pauline = n° 8.
- **L'accès d'essai de l'app** (même adresse, désactivé, rien derrière lui) : SUPPRIMÉ sur demande de Frédéric ;
  sauvegarde sans secret `app_user_supprime_sashagerphagnon_20261105`.

## 45. AUDIT DE L'ÉTAPE 4 — la recopie des fichiers (05/11) — Frédéric : « Oui, l'audit » — ⛔ rien n'est codé

**Ce que Hektor héberge** (mesuré : copie locale de la nuit, un appel `UsersOfParent` en lecture, téléchargements d'essai) :
- **Photos de négociateurs** : 10 personnalisées sur 219 fiches (CDN `staticlbi.com/.../negociateurs/avatar_…`, jusqu'à
  1,1 Mo) ; 209 = l'image par défaut `nego.jpg`. Secrétaires et administrateur : image par défaut `secretaire.png`.
- **Photos d'agence** : 17 personnalisées sur 19 (`.../agences/avatar_…`, ~300 Ko) ; 2 = `agence.png` par défaut.
- **Logo** : UN seul, commun aux 19 agences et aux 219 fiches (`logosadmin/logoadmin_temp_1229405569.jpg`, 6 Ko).
- **Barème** : ⚠ le lien que donne Hektor (`/i/redac/honoraires?honofor=4`) répond **500** sur les deux domaines. Le
  barème vivant est la page publique `www.gti-immobilier.fr/honoraires` et son **PDF `/honoraires.pdf`** (200, 2,6 Ko) :
  tranches de 15 000 € (1 800 €) à > 400 001 € (4,5 %), location 8 € + 3 € TTC du m².
- Tout se télécharge **hors quota d'API** (CDN et site public) : zéro requête Hektor.

**Ce qui est chez nous** : les colonnes existent (`app_negociateur_personne.photo_url`, `app_registre_agence.logo_url /
avatar_url / bareme_url`, `app_registre_societe.logo_url / bareme_url`) ; la nuit y écrira les ADRESSES de Hektor dès le
06/11 (la photo par défaut `nego.jpg` est déjà écartée, `agence.png` ne l'est pas). Aucun fichier copié. Le coffre public
`gti-photo` existe (celui des photos d'annonces).

**Qui les lit** : seul l'écran du registre (photo de la fiche, « chez Hektor — à recopier » pour le logo et le barème).
Les PDF du worker et les e-mails utilisent NOS logos (embarqués, `app_setting.appointment_email_logo_url`, `/rdv/gti-logo.png`).
⚠ Noté pour l'étape 5 : le REPLI des PDF du worker pointe `www.gti-immobilier.fr/images/logoSite.png` (le site de Hektor),
`console_job_worker.js` l. 8260 et 9269.

**Proposition** : une table `app_registre_fichier` (objet, n°, champ, adresse source, chemin chez nous, empreinte, taille,
type, recopié le) ; un script de nuit après le registre des agences, derrière l'interrupteur `APP_REGISTRE_FICHIERS`
(absent = éteint, `blanc` = mesure sans écrire) : il télécharge chaque adresse de Hektor, la dépose dans `gti-photo/registre/…`
SEULEMENT si l'empreinte change, et ne touche jamais aux colonnes (Hektor complète, il n'écrase pas). Images par défaut
écartées, exclusion déclarée. L'écran lit notre copie d'abord, Hektor en repli. Le dépôt par un admin = un lot à part.

**⏸ DÉCISION (05/11) — Frédéric : « ce n'est pas très utile, on verra plus tard, pas la peine de récupérer ces fichiers
tout de suite ».** L'étape 4 est REPORTÉE, rien n'est codé. La mesure ci-dessus reste valable pour le jour où on la reprendra.

## 46. AUDIT DE L'ÉTAPE 5 — les lecteurs qui lisent encore les annuaires de Hektor (05/11) — Frédéric : « Oui, l'audit » — ⛔ rien n'est codé

Recensé dans le code (front, API, worker) et en base (fonctions, politiques) : tout ce qui lit `app_agence_directory`,
`app_user_directory`, `app_hektor_negotiator_agency_directory` ou compare un `agence_nom` en texte.

**A. RESTENT sur l'annuaire de Hektor — décision du §39 (« tout geste qui communique avec Hektor garde les fiches
actives chez Hektor »)** : worker `loadActiveHektorNegoUserIds`, `loadHektorDirectoryUserByEmail/ById`,
`loadHektorNegotiatorAgencyRows`, `resolveHektorExecutionUser` (l. 2360-2493), `resolveAgencyContextForFallback`
(l. 2837), `handleAssignHektorAnnonceNegotiator` (l. 17784) ; en base `app_console_create_contact_search_job`,
`app_console_create_update_contact_job`, `app_console_resolve_contact_hektor_user` ; front : la fenêtre « affecter un
négociateur » (`loadHektorAgencyOptions`, l'agence y est un n° HEKTOR envoyé à Hektor). ⛔ Ne pas basculer.

**B. Les COORDONNÉES affichées ou imprimées — candidates** :
1. Pages publiques RDV / estimation (`appointment_service.py`) : tél et mail de l'agence par son NOM (l. 354), agence
   d'estimation par n° Hektor ou par clé de nom (l. 439-480). ⚠ Les liens publics portent la clé : à garder lisibles.
2. PDF du worker : bloc « Agence » (`resolveEstimNegotiatorContact`, l. 8804, par nom) et coordonnées du conseiller
   (`loadAgencyDirectoryRowForOwner`, l. 2882).
3. Le mandataire Youtrust (`mandataireDuMandat`, l. 6350 : nom, e-mail, portable du négociateur du bien). ⚠ Circuit de
   signature (A.2) : à voir avec l'autre session.
Mesure du jour (annuaire des agences) : Tence porte le mail ET le tél d'Yssingeaux ; Saint-Étienne = dorian@ ; Courpière
est désormais juste (courpiere@). L'intérêt de basculer : une correction saisie dans le registre arrive enfin sur les
pages publiques et les PDF ; aujourd'hui elle n'y arrive pas.

**C. L'APPARTENANCE à une agence (texte) — candidates** :
4. Les droits « son agence » : `app_mon_agence()` (agence du négociateur ACTIF de même e-mail, en TEXTE), lue par
   `app_voit_cette_ligne`, `app_voit_ce_dossier_selon_perimetre`, `app_mes_biens_selon_perimetre` et 5 politiques
   (biens, contacts, registre des mandats, deux index d'annonces). ⭐ MESURE : AUCUN compte n'a le périmètre « agence »
   (6 comptes actifs, tous « réseau ») → ces droits DORMENT. Et un compte secrétaire n'aurait AUCUNE agence (pas de fiche
   négociateur).
5. Le pilotage : l'agence d'un négociateur vient de l'annuaire (`pilotage.ts` `lireAnnuaire`), en texte.
6. Les filtres d'agence de l'écran : ils lisent l'`agence_nom` des lignes elles-mêmes. Mesure : 13 533 biens et 94 859
   contacts, TOUS au nom exact d'une agence de l'annuaire, sauf « Agences supprimée » (115 biens, 108 contacts) → rien à
   corriger aujourd'hui.

**Ce que ça pourrait casser** : A — les gestes (d'où : on n'y touche pas). B1 — un lien public déjà envoyé (on garde la
lecture par clé et par n° Hektor, le registre porte le n° Hektor de chaque agence). B2-B3 — le worker : fichier partagé
avec l'autre session, redémarrage des 4 services file vide. C4 — les droits : un écart = un négociateur qui voit trop ou
pas assez (dormant aujourd'hui, donc éprouvable sans risque). Chaque lecteur basculé garde l'annuaire de Hektor en REPLI
si le registre ne répond pas.

**Ordre proposé** (un « vas-y » chacun, APRÈS la 1re nuit qui écrit les agences, le 06/11) : B1 (API seule, Render) →
B2 (worker) → C5 (pilotage) → C4 (droits, avec un témoin inverse) ; B3 avec l'autre session ; C6 rien.

## 47. ÉTAPE 5, AUDIT APPROFONDI (05/11) — Frédéric : « audit de nouveau de manière approfondie, il ne faut pas faire d'erreur » — ⛔ rien n'est codé

Méthode : la base mesurée en production (toutes les fonctions, vues, politiques, déclencheurs et tâches pg_cron qui lisent
un annuaire) ; chaque lecteur relu dans son code avec ses appelants ; un balayage INDÉPENDANT de tout le dépôt (front,
API, worker, scripts, fonction edge, fichiers locaux de la nuit) ; puis croisement. ⚠ Le §46 contenait DEUX erreurs, corrigées ici.

**⛔ Erreur 1 du §46** : `loadAgencyDirectoryRowForOwner` (worker l. 2875) n'est PAS un simple lecteur de coordonnées : il
sert aussi `isOwnerNegotiatorActive` (l. 2913), qui décide si un geste part au nom du négociateur ou de l'AGENCE
(`ensureHektorExecutionContext` l. 2957). → On n'y touche pas ; le PDF devra lire le registre À CÔTÉ.
**⛔ Erreur 2 du §46** : le pilotage lit DÉJÀ le registre ; l'annuaire n'y est qu'un repli (`pilotage.ts` l. 70), et
ses regroupements d'agence viennent des lignes elles-mêmes. → Rien à basculer.

**1. RESTENT sur Hektor (§39 : tout ce qui choisit un compte, une agence ou une passerelle chez Hektor)** — worker :
`loadActiveHektorNegoUserIds`, `loadHektorDirectoryUserByEmail/ById`, `loadHektorNegotiatorAgencyRows`,
`agencyNameMatches`, `resolveHektorNegotiatorFromAgencyDirectory`, `resolveHektorExecutionUser`,
`resolveAgencyContextForFallback`, `loadAgencyDirectoryRowForOwner`, `isOwnerNegotiatorActive`,
`resolveContactAgencyExecutionPayload` (l. 19281), `handleAssignHektorAnnonceNegotiator` ; `Console/resolve_hektor_annonce_agency.py`
(compte d'agence lu dans le fichier local) ; base : `app_console_resolve_contact_hektor_user` et ses deux copies (contacts,
recherches, espace client) ; front : `loadUserNegotiatorContext` (compte Hektor par défaut), menus de négociateurs et
choix d'agence de la fenêtre « affecter » ; diffusion : cibles par nom d'agence (`hektor_bridge.py` l. 185, fonction edge
`hektor-diffusion` l. 140, `hektor_diffusion_writeback.py` l. 145, aperçu `api.ts` l. 8170). Plus `app_mes_chaines_nommees`
(droits « où je suis nommé » : inchangés, §15) et la connexion (`_resolve_hektor_google_identity`, déjà adossée au registre).

**2. DÉJÀ sur le registre (annuaire en repli)** : menus de négociateurs, fiche contact, répartition, noms du registre des
transactions, pilotage, pages RDV pour le TÉLÉPHONE DU NÉGOCIATEUR.

**3. LES CANDIDATS — ce que voient ou reçoivent des clients et des tiers** :
- **3a. Page publique de RDV** (`appointment_service._load_contact_details` l. 332) : tél et mail de l'AGENCE par son nom
  (`app_agence_directory`, `nom=ilike`). Le tél du négociateur vient des FICHES du registre (copie de Hektor), pas des
  coordonnées À NOUS de la personne. ⚠⚠ **Le lien garde une COPIE** (`app_appointment_public_link`) et ne la relit que s'il
  lui manque une valeur : **1 522 liens sur 2 304 sont figés** (116 créés en 60 jours, par les e-mails de rapprochement).
  Basculer la lecture ne change donc RIEN pour eux ; seuls les liens neufs ou incomplets en profitent — sauf décision de
  rafraîchir les copies. Mesure : 25 liens de Tence portent le mail d'Yssingeaux, 47 de Saint-Étienne portent dorian@.
  Aucune demande de RDV n'a jamais été enregistrée (`app_appointment_request` vide).
- **3b. Page publique d'estimation** (l. 439-642) : agence par clé de nom ; son MAIL sert de DESTINATAIRE de la demande
  quand le conseiller n'en a pas ; son tél sert de repli. ⚠ La rotation du conseiller prend les négociateurs des biens de
  l'agence, INACTIFS COMPRIS (Saint-Étienne : 6 tournent, 2 actifs). ⚠ La page sans agence prend la 1re agence « gti » par
  tri de TEXTE du n° → ANNONAY. Dernier usage mesuré : 18/06 (rotation de Saint-Étienne, 66 passages).
- **3c. PDF « avis de valeur »** (`resolveEstimNegotiatorContact` l. 8767) : bloc Agence (`app_agence_directory` par nom) et
  coordonnées du conseiller + QR vCard. 1 PDF en 60 jours. (Le PDF du MANDAT est construit par l'écran : l'agence n'y est
  qu'un nom.)
- **3d. Signataire Youtrust** (`mandataireDuMandat` l. 6339) : e-mail et portable du négociateur envoyés à Youtrust.
  Circuit A.2 de l'autre session (commits du 05/11) : à faire avec elle.
- **3e. Vitrine** (`Ecrans Android/export_project_vitrine.py` l. 425) : tél du négociateur, sinon de l'agence, lus dans le
  fichier local. Usage non mesuré.
- **3f. Mentions légales CODÉES EN DUR à 4 endroits** (mandat `App.tsx` l. 4822, espace client `espace_client.py` l. 1180,
  e-mails `rapprochement_email.py` l. 87, avis de valeur worker l. 8642) : capital, siège, RCS, carte CPI. Pas une
  dépendance à Hektor (elles survivent à la coupure) ; le registre de la société pourrait les fournir — carte valable
  jusqu'au 14/09/2027.

**4. Les droits « son agence »** (`app_mon_agence()` + 5 politiques + `app_mes_biens_selon_perimetre`) : par e-mail → fiche
négociateur active → nom d'agence en TEXTE. DORMANTS : 0 compte au périmètre « agence » (6 actifs, tous « réseau »).

**5. Trouvé en passant, hors périmètre, NON corrigé** : la fenêtre de RDV (`App.tsx` l. 39188) cherche le négociateur avec
`idUser: dossier.commercial_id` — un n° de NÉGOCIATEUR pris pour un n° de COMPTE (le piège de Claire RIBBES 15/39) ; effet :
le périmètre de la recherche de contacts peut viser la mauvaise agence (lecture seule, rien ne part chez Hektor).

**Prérequis commun** : agences ET coordonnées des personnes sont VIDES dans le registre (0/185 portables, 0 agence) jusqu'à
la 1re nuit qui écrit (06/11). Rien ne peut basculer avant. Chaque bascule garde l'annuaire de Hektor en REPLI.

## 48. ÉTAPE 5, LECTEUR 1 : LA PAGE PUBLIQUE DE RDV LIT LE REGISTRE, ET LES LIENS LE SUIVENT (05/11) — Frédéric : « 1 puis 2 », puis « 1 » (les liens suivent le registre) — ✅ EN LIGNE (f889043, poussé le 05/11 au soir)

**Ce qui change** (`backend/app/services/appointment_service.py`, seul fichier du serveur touché) :
- **L'agence** (tél, mail) vient d'abord du REGISTRE DES AGENCES (`_load_registre_agence`) : par l'écriture EXACTE du nom
  dans les alias, sinon par la CLÉ (`_cle_agence`, identique à `app_neg_cle_agence` — vérifié sur les 31 écritures réelles
  des biens, contacts, liens, annuaires et registre des mandats : 0 différence). Clé ambiguë ou rien : `None`. L'annuaire de
  Hektor reste le REPLI, champ par champ.
- **Le négociateur** : ses coordonnées À NOUS (`app_negociateur_personne.telephone / portable`) passent devant ses fiches
  Hektor (`_load_registre_negociateur`, aussi lu par l'estimation : le tél du conseiller y suit donc la même règle).
- **Le lien relit à chaque ouverture** (`_maybe_enrich_link_contacts`) et sa copie n'est réécrite QUE si une valeur a
  changé. Ordre : registre → annuaire de Hektor → COPIE du lien → texte de l'annonce (la copie passe avant le texte : un
  lien sans portable ne relit pas l'annonce à chaque ouverture). Si tout tombe, la copie reste.
- Rien ne part chez Hektor ; aucune table, aucun droit, aucun worker touché ; avant la 1re nuit (registre vide) la page
  rend EXACTEMENT ce qu'elle rend aujourd'hui.

**Les essais** (`backend/tests/test_rdv_suit_le_registre.py`, hors ligne) : **20/20 verts** — registre vide = rien ne change ni
ne s'écrit (témoin) ; correction au registre = le lien figé est réécrit ; 2e ouverture = aucune écriture ; repli champ par
champ ; portable à nous ; pannes = copie gardée sans relire l'annonce ; lien vide = texte de l'annonce comme avant ; clé
ambiguë = annuaire ; écriture exacte départage. **Témoin inverse** : les mêmes essais sur l'ANCIEN code → **10 rouges**,
exactement les 10 des nouveautés. Essais voisins : `test_lien_hektor_par_registre` 13/13, `test_email_tracking` et
`test_relance_engine` verts ; `test_rapprochement_email` ROUGE **à l'identique sur l'ancien code** (libellé d'e-mail, sans
rapport).

**Reste** : pousser APRÈS la nuit du 06/11 (Render se déploie seul) ; puis mesurer en lecture ce que donneraient les 2 304
liens (combien changent, lesquels) ; puis voir une page en vrai.

**✅ EN LIGNE le 05/11 (poussé par Frédéric ; Render sur f889043), prouvé par deux vrais liens** : Firminy
(u1ITQE0yMsQrCSmh), déjà juste → page identique, copie NON réécrite (updated_at du 31/10 inchangé) ; Dunières
(HV8d8BjbHoKY2YDh), copie à tence@ → la page rend dunieres@, copie réécrite à 19:43:05. ⭐ MESURE : seuls **443 liens sont
ACTIFS** sur 2 304 (les autres répondent 404 « Lien RDV introuvable », sans rapport) ; registre encore vide, UN SEUL lien actif
changeait (celui de Dunières). Les 1 107 « mails à changer » comptés avant étaient presque tous des liens INACTIFS.
⏰ Reste : après la nuit du 06/11, mesurer les 443 contre le registre rempli.

## 49. CONTRÔLE DE LA NUIT DU 06/11, 1re ÉCRITURE DU REGISTRE DES AGENCES, ET UN DÉFAUT RATTRAPÉ (06/11)

**La nuit** (run 04:00 → 06:39:40, code 0, aucune erreur) : registre des négociateurs relu à 06:24 (170 fiches vues, 0
événement) ; carnet intact (civilité de Caroline) ; fiche 1000088 toujours « decision ». ⚠ **Le registre des agences n'a
RIEN écrit** : l'étape a pris le chemin « interrupteur éteint » (< 1 s) → `APP_REGISTRE_AGENCES` n'est pas à 1 dans le .env
lu par le run (non lu par moi). ⚠ Le journal du run ne garde plus la sortie des étapes depuis le 05/11 (le 04/11 il
gardait encore le compte rendu de l'annuaire) — noté, non traité.

**La 1re écriture, à la main, sur accord de Frédéric (« Oui, écris-le »)** : `APP_REGISTRE_AGENCES=1` posé pour ce seul
lancement (le .env non touché) ; essai à blanc d'abord (rien écrit, compteur 2000000), puis écriture : **19 agences
(2000001-2000019), 19 alias, la société (SIRET 50281114400018, carte CPI valable au 14/09/2027), 904 coordonnées pour 167
personnes (137 portables, 165 agences), 1 écart (Franck, gmail)**, 0 écriture non rattachée ; carnet intact. Portables des
personnes : 137 sur 137 présents dans leurs fiches (aucun croisement).

**⛔ LE DÉFAUT, vu au contrôle et corrigé dans l'heure** : Hektor a DEUX sources du mail d'une agence et elles se
contredisent — la FICHE agence (liste des agences, reprise par le registre) et le COMPTE de l'agence (`app_agence_directory`,
ce que montrent la page RDV d'avant et l'organigramme de Hektor). **9 agences diffèrent** : Courpière ambert@ / courpiere@,
Dunières tence@ / dunieres@, Issoire brioude@ / issoire@, Saint-Bonnet craponne@ / stbonnet@, Saint-Didier monistrol@ /
stdidier@, Saint-Étienne firminy@ / dorian@, Saint-Just montbrison@ / strambert@, Tence tence@ + 04 71 59 81 45 /
yssingeaux@ + 04 71 56 02 36, Yssingeaux lepuy@ / yssingeaux@ — **240 liens actifs** derrière. La page du §48 prenait le
registre EN PREMIER : elle aurait servi la fiche croisée. Mesuré : **0 lien réécrit** entre l'écriture et la correction.
**Correction** (`_load_registre_agence`) : la page ne prend du registre QUE ce qu'un administrateur a SAISI au carnet ;
sinon l'annuaire, sa source d'avant. Essais 22/22 (nouveau cas 11 : registre croisé sans carnet → annuaire, aucune
réécriture) ; la version en ligne (f889043) échoue les cas 2, 3, 4 et 11 du nouvel essai → la correction est nécessaire.
⚠ **À trancher par Frédéric** : laquelle des deux sources de Hektor est la bonne, agence par agence (Tence : la fiche donne
un numéro propre à Tence, le compte celui d'Yssingeaux). La bonne valeur se SAISIT au carnet (écran du registre) ; la nuit
ne l'écrasera plus.

**⛔ CORRECTION DU §49 (06/11, Frédéric : « je pense que tu fais une erreur ») — HEKTOR N'A PAS DEUX MAILS.** Vu dans son
Chrome : l'organigramme ET la fiche de l'agence de Courpière (« Email de contact » et « Email de l'utilisateur ») disent
courpiere@ ; les 9 agences de l'organigramme portent les valeurs de `app_agence_directory`. **La vraie cause est chez nous** :
la copie locale `hektor_agence` est reconstruite chaque nuit (synced_at du jour) à partir d'UNE SEULE réponse brute de
`ListAgences`, reçue le **03/04/2026** (`raw_api_response` id 77072) — le run ne relit pas les agences
(`run_full_pipeline.ps1` l. 399 : `--resources negos annonces contacts offres compromis ventes broadcasts`, sans `agences`).
En avril, ces mails étaient croisés ; Hektor les a corrigés depuis. ⚠ Le « Coordonnées douteuses chez Hektor » du §35.2
venait de la MÊME copie périmée : c'était faux aussi. Les négociateurs, eux, sont FRAIS (`list_negos` relu le 06/11 à
03:53) : les 904 coordonnées des personnes sont justes. La fiche de Hektor porte en plus une ADRESSE d'agence (Courpière :
7 Place de la Cité Administrative, 63120) que la liste ne rend pas.

## 50. LE REGISTRE DES AGENCES RELU FRAIS, LES AGENCES REMISES DANS LE RUN, LA PAGE RDV AU « REGISTRE D'ABORD » (06/11) — Frédéric : « donc 1, mais ensuite il faut changer ton script […] puis oui on allume, puis le 4 pour le registre des négos et des agences, les deux »

**1. Le registre des agences réécrit depuis Hektor FRAIS** (sur accord) : une requête en LECTURE (`ListAgences`, la même que
l'annuaire de chaque nuit), puis la même fonction de base ; essai à blanc d'abord. Résultat : **les 9 mails d'avril corrigés**
(Courpière courpiere@, Dunières dunieres@, Issoire issoire@, Saint-Bonnet stbonnet@, Saint-Didier stdidier@, Saint-Étienne
dorian@, Saint-Just strambert@, Tence yssingeaux@ + 0471560236, Yssingeaux yssingeaux@) ; les adresses d'image et de barème
passent sur www.gti-immobilier.fr ; **une 20e agence** née (n° 2000020, « Gestion site », AGENCE_SEULE, aucun bien, mail
`…@gti-immobilier.frr` tel que chez Hektor). ⚠ **La société** : Hektor donne AUJOURD'HUI la carte professionnelle valable au
**04/11/2025** (14/09/2027 en avril) — même n° CPI 4202 2019 000 043 878. Le registre reflète Hektor ; **à trancher par Frédéric**.

**2. Pourquoi c'était périmé, et ce qui l'est encore** :
- AGENCES : `run_full_pipeline.ps1` relisait `negos annonces contacts offres compromis ventes broadcasts` — PAS `agences`. La
  copie locale vivait sur la réponse du 03/04. → **`agences` remis dans la liste** (une requête par nuit). Mesuré AVANT :
  noms et n° de compte des 19 agences IDENTIQUES à avril (l'`agence_nom` des 13 533 biens et 94 859 contacts ne bouge pas,
  donc ni droits, ni filtres, ni passerelles) ; changent les mails, le « parent » (lu nulle part en aval) et la 20e agence.
  Script analysé sans erreur, encodage (BOM) préservé. `sync_raw.py` (modifié par une autre session) NON touché.
- NÉGOCIATEURS : `list_negos` et `list_negos_inactive` sont relus CHAQUE nuit (06/11 03:53) — frais. ⚠ Mais `upsert_negos`
  (`normalize_source.py` l. 595) réapplique APRÈS elles les 15 réponses `nego_by_id` du 03/04 : 11 concordent avec le jour,
  4 sont des négociateurs disparus des listes (historique), **1 diffère** : Sylvie TEYSSONNIER n° 41 (avril : portable
  0658803706 ; aujourd'hui : portable 0471560236, fixe 0471598145). NON corrigé (cœur de la normalisation, à décider).

**3. L'interrupteur** : `APP_REGISTRE_AGENCES=1` à poser par Frédéric dans `C:\Hektor\Projet\.env` (je ne lis ni n'écris le .env).

**4. La page RDV repasse au « registre d'abord »** (`_load_registre_agence` lit la colonne du registre : la saisie du carnet si un
administrateur a corrigé, sinon la valeur de Hektor tenue par la nuit ; annuaire en repli champ par champ). Le négociateur
l'était déjà (coordonnées À NOUS de la personne d'abord, §48). Essais **22/22** ; la version en ligne (aa3d016, carnet
seulement) en échoue 6. **Mesure réelle avant de pousser** : sur les **439 liens actifs**, registre = annuaire pour le tél
ET le mail de chaque agence, **0 lien ne changerait**.

## 51. LES FICHES DE SECOURS D'AVRIL N'ÉCRASENT PLUS LES LISTES DU JOUR (06/11) — Frédéric : « 1 »

**Le défaut** : `normalize_source.upsert_negos` reconstruit chaque nuit `hektor_negociateur` depuis les listes du jour
(`list_negos`, `list_negos_inactive`), PUIS repose par-dessus les fiches de secours `nego_by_id` — 15, lues une à une le
03/04/2026 parce qu'absentes alors de la seule liste des actifs. Depuis l'ajout de la liste des inactifs, 11 de ces 15 sont
dans les listes : leur fiche d'avril les écrasait quand même. Une seule différait : Sylvie TEYSSONNIER n° 41 (avril
06 58 80 37 06 ; Hektor aujourd'hui portable 04 71 56 02 36, fixe 04 71 59 81 45).
**La correction** : une fiche de secours ne repasse plus sur un n° vu dans les listes du jour ; elle sert toujours aux
négociateurs ABSENTS des listes (n° 37, 42, 43, 93 gardés). Si les listes manquent une nuit, le secours joue comme avant.
**L'épreuve** (hors ligne, petite base faite des VRAIES réponses rangées) : l'ANCIENNE version reproduit à l'identique la
table de cette nuit (0 différence = témoin) ; la NOUVELLE ne diffère QUE sur le n° 41, qui suit Hektor. Compilation verte.
**Effet** : actif dès le run de cette nuit (le run lance le fichier du serveur) ; Sylvie suivra Hektor dans la copie locale,
puis l'annuaire, le registre des négociateurs et, si l'interrupteur des agences est allumé, ses coordonnées à nous.

## 52. ÉTAPE 5, LECTEUR 2 : LA PAGE PUBLIQUE D'ESTIMATION (06/11) — Frédéric : « non c'est bon, enchaîne », puis « 1 » (Firminy) — ✅ EN LIGNE (06/11, 10:51)

**L'audit** : la page (`apps/rdv-public`, `/public/appointments/estimation/…`) s'ouvre avec une agence (`?agency=…`) ou sans ;
elle désigne un conseiller À TOUR DE RÔLE et la demande part sur son mail (sinon celui de l'agence). Usage mesuré très
faible : une seule rotation enregistrée (Saint-Étienne, 66 passages, dernier le 18/06) ; aucune demande jamais enregistrée.
Défauts : (1) la rotation prenait toute personne ayant un bien dans l'agence, INACTIFS COMPRIS — 7 agences sur 18 (Firminy
7 dont 1 active, Saint-Étienne 5 dont 2, Ambert, Annonay, Brioude, Tence) ; et `agence_nom=ilike.<nom>` ratait « Groupe GTI
Ambert␣␣␣ » ; (2) la page sans agence prenait la 1re agence « gti » au tri du n° en TEXTE → ANNONAY.

**Ce qui change** (`appointment_service.py`) :
- `_read_registre_agency_negotiators` : la rotation = les fiches de négociateur ACTIVES chez Hektor dans CETTE agence (par le
  n° d'agence Hektor, plus par le nom), d'une personne que l'app n'a pas passée en « ancien ». Registre muet (panne) :
  l'ancien chemin, inchangé. Registre sans actif : personne ne tourne → la demande part sur le mail de l'agence (comme avant).
- `_read_default_agency_row` : la page sans agence = **FIRMINY** (décision de Frédéric).
- `_avec_registre_agence` : tél et mail de l'agence du REGISTRE d'abord (même règle que la page RDV, §50), annuaire en repli ;
  le n° d'agence reste celui de Hektor (clé de la rotation inchangée).

**Les essais** (`backend/tests/test_estimation_registre.py`) : **12/12** ; l'ancienne version en échoue 8 (témoin). Essais
voisins verts (RDV 22/22, lien Hektor 13/13). **Mesure réelle** : chaque agence ne fait plus tourner que ses actifs, tous en
@gti (Firminy : Emmanuelle PEREIRA ; Saint-Étienne : Lucille FORLICO, Mélanie LEGRAND ; Ambert : Alice RONDEAU, Sandrine
DELAVAUD — que l'ancien chemin ratait) ; Agences supprimée et Gestion site : personne (mail de l'agence).

**En ligne** (poussé par Frédéric le 06/11 à 10:51, Render sert 03b74fd qui le contient) : la page sans agence ouvre
**Groupe GTI Firminy** (04 77 06 20 20, firminy@) — sans conseiller nommé, comme avant (la rotation ne joue qu'avec une
agence) ; `?agency=saint-etienne` désigne **Lucille FORLICO** (n° 4, forlico@), agence dorian@ (= registre = annuaire,
« laisse » de Frédéric), 555 créneaux. La rotation est passée de 66 à 67 passages : le prochain visiteur aura Mélanie LEGRAND.

**Interrupteur allumé** (06/11, sur accord explicite de Frédéric) : `APP_REGISTRE_AGENCES=1` ajouté en fin de `.env` (2 lignes, rien d'autre
lu ni touché) ; relu par le chargeur de la nuit (`push_contacts_to_supabase.load_env_file`) → « ECRIT ». La nuit du 06→07/11 est la
1re à écrire le registre des agences d'elle-même.

## 53. ÉTAPE 5, CANDIDAT 3c : LE PDF « AVIS DE VALEUR » — AUDIT (06/11) — Frédéric : « PDF avis de valeur » — ⛔ rien n'est codé

Audit limité au PDF avis de valeur (`generate_estimation_pdf`, service worker DOCUMENTS) ; les autres objets ne sont pas mesurés.
Gestes : il LIT (conseiller, agence) et CRÉE un document chez Hektor par le travail `upload_document_to_hektor`, inchangé.

**Qui lit quoi** : `resolveEstimNegotiatorContact` (worker, seul appelant l. ~8945) part de l'e-mail du compte CONNECTÉ
(`negociateurConnecte`, option B du 24/06), cherche la personne dans l'ANNUAIRE par e-mail (`loadAgencyDirectoryRowForOwner`,
⛔ fonction partagée avec le choix du compte d'exécution, §47 : on n'y touche pas), puis l'agence par son NOM (`nom=ilike`).
⚠ Depuis 50a7732 (26/06) le résultat remplace AUSSI le bloc visible « Votre conseiller » (la mémoire disait « QR seul ») : le
conseiller imprimé est la personne connectée, pas le négociateur du bien.

**Mesures** : 37 PDF en tout, 1 en 60 jours, 2 demandeurs seulement (Frédéric, Franck). Sur les 5 comptes vivants :
Frédéric, Pauline, LEGRAND, PEREIRA → l'annuaire et le registre disent la même chose (nom, portable, agence, coordonnées).
⛔ **Franck** : son e-mail de compte (`franck.gerphagnon@gti-immobilier.fr`) n'est PAS dans l'annuaire (qui n'a que son gmail) →
le PDF MÉLANGE deux personnes : le NOM et le téléphone du négociateur du bien, l'E-MAIL de Franck, et un QR vCard au même
mélange (ex. 05/08, bien de Tatiana CROIZIER). Le registre, lui, le connaît par son compte (personne 1000036 : nom, portable
0625486395) — mais son agence y est « Compte formation » (fiche active n° 1), coordonnées 06.58.77.08.93 / frederic@ : à ne
pas imprimer sur un document client.
Le compte `codex.test` n'a d'identité nulle part (même mélange s'il générait un PDF).

**Ce que la bascule ferait** : conseiller pris au REGISTRE par le NUMÉRO DU COMPTE qui a demandé (`requested_by` →
`app_negociateur_personne.app_user_id`), plus par l'e-mail ; identité prise d'UNE seule source (jamais de mélange) ; agence du
registre (tél/mail), annuaire en repli ; chemin actuel inchangé si le registre ne répond pas. Question ouverte : l'agence à
imprimer quand celle de la personne est « Compte formation » (ou absente).

## 54. ⛔ AUDIT « UN ADMIN N'APPARAÎT JAMAIS SUR UN DOCUMENT » (06/11) — Frédéric : « j'ai peur d'avoir tout cassé, audit »

**La règle (Frédéric, 06/11)** : un NÉGOCIATEUR agit en son nom ; un ADMIN utilise l'identité du NÉGOCIATEUR EN CHARGE du
mandat ou du contact. L'identité d'un admin n'apparaît jamais sur un document d'annonce ou de contact (sauf cas exceptionnel à
définir). ⛔ Ma proposition du §53 (« le conseiller pris au registre par le compte qui demande ») VIOLAIT cette règle : retirée.

**Méthode** : deux lectures indépendantes du code (front ; serveur + worker) + mesures en base. Aucun code ne teste le rôle
admin pour choisir une identité imprimée ; le seul test de rôle du worker est `role === "commercial"` (l. 2547).

**CE QUE MON CHANTIER A CASSÉ — une seule chose** : 71bb15d (§41, 05/11) relie un compte à la fiche négociateur active de sa
personne SANS FILTRE DE RÔLE (`supabase_admin._resolve_hektor_google_identity` l. ~221). Franck (ADMIN dans l'app) porte
depuis le 05/11 13:41 `hektor_user_id 2` / négo 1 « Compte formation » (`app_google_workspace_identity`). Effet : la fenêtre de
création de contact le propose par défaut, et ses recherches passent sous cette fiche (le `hektor_user_id` de la charge est
prioritaire : worker l. 2489, SQL `app_console_create_update_contact_job` et `app_console_resolve_contact_hektor_user`).
**Mesure : 0 geste d'écriture de Franck depuis 13:41** (2 rafraîchissements seulement) → aucun dégât à réparer.
Frédéric et Pauline (admins sans fiche active) : `hektor_user_id` vide → inchangés.
**Le reste de mon chantier respecte la règle** : page RDV (négo du bien ; 0 lien actif sur les 193 biens rangés au nom d'une
fiche d'admin), page d'estimation (rotation sur fiches actives : aucune fiche d'admin active dans une vraie agence),
correction de nuit des négos (données seules).
Les 25 contacts créés par Frédéric au n° 2 depuis le 18/09 : clés `target_…` = choix fait dans la fenêtre (essais en
Compte formation), pas une valeur automatique.

**DÉJÀ LÀ AVANT MOI (non introduit par le registre)** :
- Avis de valeur PDF (68fa3d4 + 50a7732, 24-26/06) : bloc « Votre conseiller » + QR = la personne CONNECTÉE, admin compris ;
  l'e-mail d'estimation, lui, est au nom du négo du bien → les deux se contredisent. VIOLE.
- Agenda global (App.tsx l. 21656) : un admin crée par défaut sur SON agenda ; le bon de visite qui en sort imprime l'adresse
  de cet agenda (l. 44897). VIOLE.
- Replis sur la boîte connectée quand le négo n'a pas d'adresse @gti : e-mail de rapprochement (l. 24982), envoi à un
  acquéreur (l. 24951), e-mail CRM de la fiche contact (l. 44275). VIOLE EN REPLI.
- Youtrust `mandataireDuMandat` (098290c, décision D21 du 26/10) : négo du bien s'il est actif, SINON LA PERSONNE QUI ENVOIE.
  VIOLE EN REPLI (37 négos inactifs + 50 absents au 26/10) — décision de Frédéric à réarbitrer.
- Gestes chez Hektor : la charge `hektor_user_id` passe devant le négo du contact sans contrôle de rôle (worker l. 2489).
- RESPECTENT : PDF du mandat et avenant, e-mail d'estimation, espace client, page RDV, demandes de visite, gestes sur une annonce
  (pas de `hektor_user_id` envoyé → négo du bien, ou l'agence s'il est inactif — repli agence actif).

**✅ CORRIGÉ le 06/11 (Frédéric : « Oui, vas-y »)** :
- Code (`supabase_admin._resolve_hektor_google_identity`) : un compte qui n'est pas « commercial » (admin, manager, lecture)
  rend TOUJOURS un lien vide (`match_source compte_non_negociateur`), ni par l'e-mail ni par le registre ; ses comptes Hektor
  restent notés dans `comptes_hektor`. Le chemin du §41 reste entier pour un NÉGOCIATEUR.
- Essais `backend/tests/test_lien_hektor_par_registre.py` : **15/15** (Franck admin jamais relié ; un admin à l'e-mail d'un
  négo actif non plus, manager et lecture pareil ; le cas Franck en « commercial » encore relié ; les 5 garde-fous du registre
  désormais éprouvés sur un compte négociateur). Témoin : ancien code → 4 rouges.
- Base (accord) : ligne de Franck dans `app_google_workspace_identity` remise à vide (`hektor_user_id`, `hektor_negociateur_id`,
  `negociateur_email` = null ; `comptes_hektor [SECRETAIRE 7]` gardé). Sauvegarde datée
  `app_google_workspace_identity_avant_regle_admin_20261106` (RLS, aucun droit public). Retour : recopier la ligne.
- ⚠ Tant que ce n'est pas poussé, Render garde l'ancien code : réenregistrer le compte de Franck dans l'écran Utilisateurs le
  relierait de nouveau. Et une session de Franck déjà ouverte garde l'ancien lien jusqu'au rechargement de la page.

**✅ 06/11, 2e volet (Frédéric : « vas-y fais la correction pour les admins »)** : la fenêtre de contact ne présélectionne plus
pour un admin une fiche tirée de SA session. Avant : l'e-mail de session (repli de `contactHektorUserEmail`) passait par
`findContactHektorOption`, qui lit aussi le NOM dans l'e-mail → « franck.gerphagnon » choisissait « FRANCK GERPHAGNON -
Compte formation » (preuve : le contact du 05/11 au matin, avant le §41, partait déjà sous le n° 2). Après
(`emailHektorHorsSession`, App.tsx) : pour un compte non « commercial », un e-mail égal à la session ne désigne plus personne ;
la fenêtre prend le négociateur du contact, sinon oblige à choisir (garde existante « Choisis le negociateur Hektor… »). Un
e-mail ou un numéro désigné autrement (propriétaire de l'agenda choisi) reste. Les recherches d'un contact (deux fiches) : l'e-mail
de session d'un admin ne passe plus devant le négociateur du contact. Un négociateur : inchangé.
Contrôles : `npm run build` vert (tsc compris) ; essai hors ligne sur les VRAIES fonctions extraites de App.tsx, 8/8 (Franck
admin : aucune présélection ; contact de PEREIRA : PEREIRA ; agenda de LEGRAND : LEGRAND ; LEGRAND négociatrice : elle-même) ;
témoin ancien comportement → « FRANCK GERPHAGNON ». Non vu à l'écran (il faut une session admin).
⚠ App.tsx était modifié en même temps par une autre session (modale statut) : le commit a été construit sur HEAD + ce seul
changement, son travail est resté dans l'arbre, non touché.

**EN LIGNE le 06/11** : 3b30a0b servi par Render (commit 67a9ffb et suivants), f95c230 servi par Vercel (déploiement 8155bb7 READY). Base : les 4 comptes admin sans lien Hektor, LEGRAND 30/5 et PEREIRA 51/26 inchangés.

## 55. LE PDF « AVIS DE VALEUR » SELON LA RÈGLE DU §54 — AUDIT (06/11) — Frédéric : « Oui, l'audit » — ⛔ rien n'est codé

Remplace la proposition du §53 (fausse). Audit limité au PDF avis de valeur et à l'e-mail qui l'accompagne.

**Aujourd'hui** : le bloc « Votre conseiller », son téléphone, son e-mail, son agence et le QR vCard = la personne CONNECTÉE
(`negociateurConnecte`, worker `resolveEstimNegotiatorContact` + 50a7732), admin compris. L'écran envoie pourtant le négo du
bien (`negociateur` : `commercial_nom`, `agence_nom`, `negociateur_email`, App.tsx l. ~6712 et ~17336) ; le worker l'écrase.
L'e-mail d'estimation part au nom du négo du bien (ou accueil@).

**Mesure des biens au statut estimation (12 821)** — le négo du bien selon le registre (fiche par `commercial_id`) :
7 067 négo ACTIF (55 %) · 4 223 SANS négo (33 %) · 1 338 négo INACTIF · 193 sur une ancienne fiche d'ADMIN (Pauline n° 16
Monistrol 158, Franck 18 + 5, Frédéric 12). Les autres statuts (714) : 690 actifs. ⇒ quand un ADMIN génère le PDF, 45 % des
estimations n'ont pas de négociateur en charge utilisable : c'est le « cas exceptionnel » à définir.

**La règle proposée** (worker, rôle lu par `requested_by` → `app_user_profile.role`) :
- le demandeur est NÉGOCIATEUR → lui-même : sa fiche par le lien de son compte (`app_google_workspace_identity`), ses
  coordonnées au registre (personne), son agence au registre ;
- le demandeur est ADMIN → le négo du bien (`commercial_id`) s'il est ACTIF au registre et n'est pas une fiche d'admin :
  nom et coordonnées du registre, agence du bien ;
- sinon (sans négo, inactif, fiche d'admin) → CAS À TRANCHER ; jamais l'admin.
Le QR suit la même identité. L'agence vient du registre (tél/mail), annuaire en repli. Registre muet → ancien chemin SANS
l'identité de session pour un admin.

**Décision de Frédéric (06/11) : « L'agence seule »** pour le cas sans négociateur utilisable. **CODÉ** (worker,
`conseillerAvisDeValeurSelonRegle` + `cleAgenceRegistre`, branché dans `handleGenerateEstimationPdf`) :
- négociateur demandeur → lui-même (personne du registre par son compte, son agence au registre) ; négociateur absent du
  registre → l'ancien chemin, sa session (c'est lui) ;
- admin (ou pas de demandeur) → le négo du bien s'il a une fiche ACTIVE, une personne active, et pas de compte autre que
  « commercial » ; agence du bien ;
- sinon → l'agence seule (nom vide → « Votre conseiller Groupe GTI », tél/mail de l'agence, QR de l'agence) ;
- quand la règle tranche, l'identité vient d'UNE source (plus de complément par le négo envoyé par l'écran) ; registre muet →
  ancien chemin SANS la session (jamais un admin).
Essai `Console/test_avis_valeur_regle_admin.js` (lecture seule, fonctions extraites du worker) : **11/11** ; témoin sur
l'ancien worker : Frédéric génère sur le bien de GENTES → « Frédéric GERPHAGNON / Groupe GTI Firminy » imprimé.
Vraies données (lecture) : les 6 biens des derniers PDF générés par des admins (63156, 62609, 62884, 62853, 62764, 62597)
imprimeraient leur négo du bien (GENTES, PEREIRA, TEYSSONNIER, CROIZIER, BILLIG DURAND, VALLA), coordonnées du registre.
⚠ TEYSSONNIER : le registre porte encore 0658803706 (copie d'avril) ; la nuit du 06→07 doit le passer à 0471560236 (§51).
Reste : push, puis redémarrer HektorConsoleWorkerDocuments FILE VIDE (c'est lui qui porte `generate_estimation_pdf`).

**✅ EN SERVICE le 06/11 à 13:22** : 18e90ae poussé ; les 4 services worker redémarrés par Frédéric (file vide vérifiée avant :
0 pending, 0 running). Preuve par l'heure des processus : node de DOCUMENTS (pid 21424) né à 13:22:41, après la dernière écriture
du worker (12:42:41) ; journal `console_worker_service_documents.log` : démarrage propre, `generate_estimation_pdf` dans ses
types ; un rafraîchissement posé à 13:23 traité (done). ⚠ Le redémarrage a aussi chargé un travail NON COMMITÉ d'une autre
session (A.2 : 3e cran « admin » de l'interrupteur Youtrust) — inerte tant que `signature_youtrust` = off (mesuré : off).
Pas encore vu sur un vrai PDF (aucun généré depuis).

## 56. AGENDA GLOBAL ET BON DE VISITE SELON LA RÈGLE DU §54 — AUDIT (06/11) — Frédéric : « Oui, l'audit » — ⛔ rien n'est codé

Audit limité à l'agenda (global et de l'annonce) et au bon de visite imprimé ; les autres objets ne sont pas mesurés.

**Bon de visite** (`visitVoucherHtml`, App.tsx ~l. 45022) : bloc « Agence » = `contact.agence_nom` sinon « Groupe GTI » ;
« Représenté par » = `contact.commercial_nom` (le négo du CONTACT, pas du bien) sinon `event.google_calendar_email` (L'ADRESSE
de l'agenda) sinon « A completer ». Depuis l'agenda global (`visitVoucherContactFromGoogleEvent`) et depuis l'agenda d'une
annonce (`visitVoucherContactFromAnnonceEvent` → `appContactFromDetailContact`), le contact est fabriqué SANS `commercial_nom`
ni `agence_nom` → le bon imprime « Groupe GTI » et l'E-MAIL de l'agenda (celui d'un admin si le RDV est sur son agenda), jamais
le négo du bien. Champs modifiables à la main avant impression.
**Agenda global** (`GoogleAgendaGlobalScreen`) : agenda par défaut = `contactHektorUserEmail` (pour un admin : sa session) ;
un admin/manager peut choisir l'agenda d'un négo (`canSelectTeam`), un négo reste sur le sien (05/11). Un RDV créé sur
l'agenda d'un admin envoie l'invitation au client depuis la boîte de l'admin.
**Mesure** (`app_google_calendar_event_link`) : 11 RDV en tout, TOUS sur des agendas d'admin (Frédéric 6 du 12 au 15/06,
Franck 5 du 2 au 8/06), 10 sur un bien, 0 à venir, 0 créé par un négociateur → essais de juin ; aucun usage réel depuis.
**Correctif proposé** : bon de visite → « Représenté par » = le négo propriétaire de l'agenda s'il est négociateur, sinon le
négo ACTIF du bien, sinon l'agence seule (champ vide « À compléter ») ; « Agence » = l'agence du bien ; jamais une adresse
e-mail à la place d'un nom. Agenda : décision à prendre (voir le message du 06/11).

**Décision de Frédéric (06/11) pour le bon de visite : « toujours connecté sauf si admin prendre négo du contact ».** CODÉ (front) :
`loadRepresentantBonDeVisite` (api.ts) — négociateur connecté → lui-même (personne du registre par son compte, son agence ; nom
de profil s'il manque au registre) ; admin → le négo du CONTACT (`app_contact_current.hektor_negociateur_id`) s'il a une fiche
active, une personne active et pas de compte autre que « commercial » ; sinon la case reste « A completer » (agence du contact).
`visitVoucherHtml` ne retombe plus JAMAIS sur l'adresse de l'agenda (`event.google_calendar_email`) ; `openVisitVoucherPrint`
résout le représentant au moment d'imprimer (les 6 points d'impression en profitent, la fenêtre est ouverte avant).
Contrôles : `npm run build` vert ; essai hors ligne sur la vraie fonction extraite, 8/8 (LEGRAND connectée → elle-même et
Saint-Étienne, même sur un contact de GENTES ; admin → GENTES ; contact sans négo / négo parti / négo admin / invité → à
compléter ; panne → ancien nom du contact, jamais l'adresse). Témoin : l'ancien gabarit l. 45053 retombait sur
`google_calendar_email`. Non vu à l'écran. L'agenda (un admin peut-il poser un RDV client sur son agenda ?) : NON TRANCHÉ.

**Agenda — décision de Frédéric (06/11) : « Oui, laisser »** : un admin peut toujours poser un RDV client sur son propre agenda (invitation depuis sa boîte). Rien à coder ; seul le bon de visite suit la règle. Ne pas relancer.

## 57. ÉTAPE 5, CANDIDAT 3e : LA VITRINE (LES ÉCRANS EN VITRINE D'AGENCE) — AUDIT (06/11) — Frédéric : « vérifie vitrine doit prendre dans le registre, c'est les écrans en vitrine » — ⛔ rien n'est codé

Audit limité à la vitrine ; rien d'autre n'est mesuré.

**Qui la fait** : `Ecrans Android/export_project_vitrine.py`, étape « android vitrine export and push » du RUN DE NUIT
(`run_full_pipeline.ps1` l. ~1869) ; publie `catalogue_vitrine.json` sur GitHub (GTIImmo/vitrine) que lisent les écrans. Les
photos viennent déjà de chez nous (Supabase, G.15). **L'agence et le négociateur viennent de la COPIE LOCALE de Hektor**
(`hektor.sqlite` : `hektor_agence.tel`, `hektor_negociateur.nom/prenom/portable`, par `hektor_annonce`), pas du registre.
Ce qui est imprimé, par bien : « <agence> TEL : <tél agence> NEGOCIATEUR EN CHARGE DU BIEN : <prénom nom> TEL : <portable> »,
plus `phone` = portable du négo sinon tél de l'agence (et le QR du RDV, qui passe par la page RDV, déjà au registre).

**Mesure de la publication de cette nuit (06/11 05:39, 438 biens)** comparée au registre :
- agences : 16 sur 17 identiques ; ⛔ **Tence** publie 04 71 59 81 45 (copie d'AVRIL) alors que le registre porte 0471560236
  (la valeur actuelle de Hektor, « laisse, cela correspond » de Frédéric) ;
- négociateurs : 27 sur 28 identiques au registre ; ⛔ **Guillaume PERRET** (5 biens) publié SANS téléphone (copie locale vide),
  le registre a 0763983009 ; TEYSSONNIER : 0658803706 des deux côtés (le registre suivra Hektor cette nuit, §51) ;
- 8 biens sans négo (agence seule), 1 « gti immobilier » ; aucun admin imprimé.
La copie locale des agences est relue chaque nuit depuis ce soir (§50) : Tence se corrigerait seul, mais pas une saisie du
CARNET (correction d'un admin) ni les coordonnées propres à la personne (PERRET).

**Correctif proposé** (script de nuit, additif) : une lecture du registre en tête (agences + alias, fiches + personnes) ; par bien,
agence = registre par son n° Hektor (sinon alias du nom), tél du registre ; négo = fiche du n° du bien → personne : nom et
portable du registre, imprimé seulement si la fiche est ACTIVE, la personne active et pas un compte admin (sinon l'agence
seule) ; registre illisible → la copie locale comme aujourd'hui (repli total, comme pour les photos).

**CODÉ le 06/11 (Frédéric : « vas-y mais réaudite pour être bien sûr de ton écriture »)** — `export_project_vitrine.py` :
`charger_registre()` (une lecture : agences, fiches, personnes, profils ; plafond = refus ; illisible → copie locale, repli total)
et `contact_du_bien()` ; interrupteur `VITRINE_REGISTRE` (absent = allumé). Le TÉLÉPHONE de l'agence vient du registre par son
n° Hektor ; le NÉGO (nom + portable) par le n° Hektor du bien → personne, imprimé seulement si la personne est un
NÉGOCIATEUR (`type_personne`), ACTIVE, et pas un compte admin. ⛔ Le NOM de l'agence garde sa source : les écrans FILTRENT sur
lui (`?agence=Saint-Etienne`, `normalizeAgency(x.agence).includes`). Le format du texte est inchangé (lu par
`extractContactFromAgence`).
**Le réaudit a corrigé deux erreurs de ma 1re écriture** : (1) juger la FICHE active masquait aussi un négo encore là dont le
bien pointe une fiche éteinte → on juge la PERSONNE ; (2) juger la personne faisait imprimer une FICHE D'AGENCE (« gti
immobilier » → « Groupe GTI Firminy », qui aurait en plus fait entrer un bien de Brioude dans le filtre Firminy) → on exige
`type_personne = negociateur`.
**Mesure sur les vraies données, sans rien publier** (catalogue construit en mémoire, avec / sans registre) : 438 biens, 31
changent, tous voulus — PERRET (5) gagne 0763983009 ; Tence (23) prend 0471560236 (valeur actuelle de Hektor, validée) ;
GONZALEZ (2, personne passée « ancien », 3 fiches éteintes : les écrans montraient le portable d'un parti) et « gti immobilier »
(1, fiche d'agence) → l'agence seule. **Lecture par les écrans** (fonctions extraites des DEUX `script.js`) : même nom d'agence
pour les 438, 0 téléphone illisible, négo avec portable 424 → 427, filtres d'agence identiques (Saint-Étienne 39, Firminy 33,
Tence 23, Monistrol 12, Brioude 22, Yssingeaux 43). Actif dès la nuit du 06→07/11 (le run exécute la copie du serveur).
