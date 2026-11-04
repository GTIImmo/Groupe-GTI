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

