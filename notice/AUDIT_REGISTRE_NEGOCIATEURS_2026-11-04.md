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
