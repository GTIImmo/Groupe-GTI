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
