# La mise à jour quotidienne depuis le Sheet — audit des gestes et plan (27/11/2026)

> Demandé par Frédéric le 27/11 après-midi : « mettre en place une mise à jour quotidienne de mon
> projet — l'app et le serveur — à partir des nouvelles lignes et des modifications de lignes de
> mon Sheet. Des écritures chez nous, et des gestes chez Hektor par le worker, selon la colonne. »
>
> ⛔ **Rien ne se code et rien ne s'écrit avant qu'il ait lu ce plan.** Le seul geste fait le 27/11
> est celui qu'il a autorisé : le socle du protocole en base.
>
> Méthode : lecture du code (worker, RPC en base), de la base (`app_console_job` depuis mai,
> `app_affaire_ledger`, `app_setting`) et de ce qui est déjà écrit (mémoires, notes, commentaires du
> worker). Aucune lecture ni écriture chez Hektor pour cet audit. **Une case qu'on ne sait pas remplir
> porte « non mesuré ».**

---

## 0. En une page

**① On sait créer et corriger une transaction chez Hektor : le geste existe, ne pas le reconstruire.**
`change_hektor_annonce_status` crée une offre, un compromis ou une vente en changeant le statut du
bien. Avec `reprendre_transaction` et `champs_touches`, il corrige une transaction existante, date
comprise. L'offre a son chemin propre (`createOffre`, puis `updateOffre`). Le compromis et la vente
passent par l'assistant de Hektor, et le worker récupère l'identifiant.

**② Mais ce geste n'a presque jamais servi en vrai.** Depuis mai, 138 travaux de création ou de
correction ont abouti. Ils portent sur **8 biens seulement**, et 135 d'entre eux sur les biens d'essai :
24933 (le bac à sable, 85 gestes), 24113 (la vente d'essai, 25), 62774 (19), 62965 (3). Il reste 3
gestes sur des biens réels. **Aucune correction n'a jamais été faite sur un bien vendu réel, ni sur
une transaction ancienne.** C'est exactement ce que le stock du Sheet demanderait.

**③ Le stock du Sheet tombe presque entièrement là où nos propres gardes interdisent le geste.**
- Sur les 81 dates de compromis en écart, 77 sont sur des biens sortis du parc (vendus ou archivés).
  Or modifier le compromis d'une chaîne qui porte une vente est **verrouillé en base** :
  l'interrupteur `compromis_verrouille_par_vente` est allumé, parce que le statut du bien repartirait
  « Sous compromis » chez Hektor.
- 7 de ces 81 sont des compromis annulés, et Hektor refuse en clair de modifier un compromis clôturé.
- Les 41 écarts de « Vente Fixée » sont tous sur des biens vendus hors du parc. Corriger une vente
  sur un bien vendu a été prouvé **une seule fois**, sur la vente d'essai 23358, le 02/11.
- Modifier une offre acceptée est impossible : Hektor rend 200 et zéro octet.

**④ La conséquence pour le plan :** chaque matin, l'outil écrit chez nous, et il n'informe Hektor que
pour une affaire **vivante**, par un geste déjà prouvé **dans l'état exact de la pièce**. Le stock
historique reste chez nous. C'est déjà la règle écrite le 15/11 pour les transactions nées du
classeur : « elle n'en aura jamais » (de numéro Hektor).

**⑤ Les 190 transactions nées du classeur le 16/11 restent chez nous** (§ 4). Toutes sont mortes :
35 compromis annulés, 96 offres refusées, 59 offres acceptées dont le bien est vendu à un autre
acheteur. Les créer chez Hektor remettrait 114 biens vendus en « Sous offre » ou en « Sous
compromis », et poserait la date du jour sur chacune.

**⑥ Le plan suit ton ordre** (§ 6), revu le 27/11 au soir :
1. l'audit (ce document) ;
2. la règle des 334 : ✅ **R30a validée le 27/11 au soir** (190 pièces, aucun dossier ne bouge) ;
3. les dates d'annulation élargies ;
3 bis. **les écritures sans risque chez nous** (~840 cases : répartitions, COMMENTAIRES, En attente de,
   avis) — ajoutée par lui le 27/11 au soir ;
4. la Commission TTC chez nous, avec les **quatre** contrôles de D6. L'essai chez Hektor se fait sur
   0bc98552 (son choix) ;
5. la boucle, qui regarde seulement ;
6. la boucle, qui écrit chez nous ;
7. les lignes neuves ;
8. R1 à R5, la fin du chantier, là où le gel s'endort ;
9. **en dernier, et peut-être jamais** : la boucle qui informe Hektor. **0 geste mesuré en 4 jours sur
   les affaires vivantes** (§ 6, étape 9).

Ce qui survit à chacune des deux coupures (celle du Sheet, celle de Hektor) est écrit étape par étape au
§ 6.1.

---

## 1. Ce qui existe déjà et sert — on ne repart pas de zéro

- **La photo du Sheet** : l'« image » du protocole, prise par `phase2/checks/protocole_classeur.py`. Il
  y en a 5 en cache, soit 624 Mo. Ta règle du 26/11 : 15 jours de rétention.
- **Le juge** : le protocole et ses 29 règles. Au passage 82, 4 733 lignes sur 4 803 sont tranchées.
  ⭐ **Depuis le 27/11, sa mémoire est en base.** Les tables `app_classeur_protocole_passage`,
  `_verdict`, `_temoin`, `_motif` et `_fichier` portent 82 passages, 393 449 verdicts, 65 361 lignes
  de témoin, 18 motifs et 8 fichiers. Elles sont relues identiques, octet pour octet, par mon contrôle
  et par le tien.
- **Les places chez nous**, déjà remplies par le rapatriement des 16-17/11 :
  - les notes : `app_affaire_note`, origine `classeur:G` ou `classeur:F` ;
  - les avis : `app_classeur_avis` ;
  - la répartition : `app_affaire_repartition`, sur la chaîne ;
  - la charge : le carnet du mandat, `app_mandat_champ_app` ;
  - les cases `_app` du registre : `honoraires_entree_app`, `charge_commission_app`,
    `date_annulation_app`, `motif_annulation_app`, `vente_reglee_app`, `numero_facture_app`,
    `numero_mandat_app` ;
  - la colonne A : `app_sheet_ecrit`, ancrée sur l'ID Unique et la colonne, 4 725 lignes.
- **Le patron d'écriture chez nous**, éprouvé sur une vingtaine de lots depuis le 04/11 : un script
  qui mesure et fabrique le SQL, puis un patch, son inverse et sa répétition. Le patch se joue à
  blanc avant d'être joué pour de vrai.
- **Les gestes du worker sur les transactions** (§ 2) :
  - `change_hektor_annonce_status` (création, et correction avec `reprendre_transaction`) ;
  - `change_hektor_offre_status` ;
  - `cancel_hektor_compromis` ;
  - `delete_hektor_compromis` ;
  - `delete_hektor_vente`.
- **Les gardes en base** :
  - `app_modifier_affaire_optimistic` refuse une transaction sans numéro Hektor ou que Hektor ne rend
    plus, et refuse le compromis d'une chaîne vendue ;
  - `app_geste_affaire_optimistic` refuse de bouger une offre si son dossier porte un compromis vivant
    ou une vente.
- **Le juge honnête d'un geste** : `phase2/sync/transaction_etat_from_api.py`, qui lit une transaction
  par son numéro. Depuis le 12/11, c'est la règle : « un travail `done` n'est pas une preuve ».
- **Le patron « naître complet » du chantier ⑧**, qui est en service pour les affaires :
  - les interrupteurs `affaire_nait_complete`, `affaire_modif_au_registre` et
    `affaire_modif_champs_touches` sont allumés ;
  - l'affaire reçoit son `app_affaire_id` au clic, avant que Hektor réponde ;
  - le numéro Hektor revient ensuite par la preuve du worker, puis par le filet
    `poserNumerosManquants`.
- **Le détecteur de cicatrices** : `phase2/checks/classeur_detecteur_cicatrices.py`.

---

## 2. Le tableau des gestes, pièce par pièce et état par état

> Sources : les travaux réellement posés depuis mai (`app_console_job`, relus le 27/11), le code du
> worker et des RPC, les mémoires et les notes. « Essai » veut dire que la preuve n'existe que sur un
> bien d'essai.

> Abréviations des sources, toutes dans `notice/` sauf W :
> - **W** : `Console/console_job_worker.js`
> - **MES** : `MESURE_MODIFIER_OFFRE_ACCEPTEE_2026-10-13.md`
> - **ACT** : `ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md`
> - **PRO** : `PROTOCOLE_TEST_STATUTS_TRANSACTIONS_2026-09-01.md`
> - **PAV** : `PROTOCOLE_ASSISTANT_VENTE_HEKTOR_2026-08-30.md`
> - **ARC** : `ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md`
> - **AGR** : `AUDIT_GESTES_REGISTRE_TRANSACTIONS_2026-10-30.md`
> - **LT** : `LISTE_TACHES_A_COCHER_2026-08-29.md`
> - **T1** : `CHANTIER_CLASSEUR_TEMPS1_INVENTAIRE_ECRITURES_DE_MASSE_2026-11-19.md`
>
> **Les travaux posés depuis mai**, comptés le 27/11 sur les seuls travaux `done` :
> - créations : 16 offres, 33 compromis, 17 ventes. Le numéro Hektor a été confirmé par l'API pour
>   60 d'entre elles ;
> - corrections : 2 offres, 46 compromis, 3 ventes ;
> - en erreur : 4 corrections ;
> - changements d'état d'offre : 1 253, dont 1 205 refus d'offres acceptées pendant les lots de masse
>   des 10-12/11 ;
> - annulations de compromis : 27 ; suppressions de compromis : 19 ; suppressions de vente : 15.
>
> ⚠ Ton « 116 créées, 106 corrigées » ne se retrouve pas avec ces définitions. **116**, c'est le nombre
> de travaux dont la preuve porte un numéro de transaction, corrections comprises. Je compte 66 créations
> et 51 corrections. Le « 106 » : non reconstitué.

### 2.1 L'offre

- **Créer.** ✅ Ça marche. Le chemin propre de l'offre est `mode=annonce-SuiviVente-offre-createOffre`,
  un envoi en une fois (W l. 15702, 15845-15888).
  - Il faut le compte du **négociateur**. Hektor refuse l'administrateur : « Un compte administrateur
    ne peux pas saisir une offre » (ACT l. 81).
  - L'ouverture `init=1` rend toujours `error: true` : c'est toléré, 10 envois sur 10 (MES).
  - Hektor nomme l'offre créée dans `returnValue.offre.id`.
  - Le statut du bien monte : Actif → Sous offre.
  - Cicatrices connues :
    - un doublon (33026 et 33027) le 25/08 ;
    - l'acquéreur d'une offre n'est jamais relu (ARC, 23/10).
  - **Une date passée** : rien d'écrit. Sans date dans la charge, le worker prend la date du jour
    (W l. 14065-14076).
- **Modifier une offre proposée.** ✅ Ça marche (33050, 165 000 → 167 000, le 08/09, vérifié le 13/10).
  - ⚠ `dateOffre` arrive pré-remplie au jour : sans date dans la charge, la date de l'offre est écrasée.
  - ⚠ Corriger le montant d'abord, accepter ensuite.
- **Modifier une offre acceptée.** ⛔ **Échoue en silence chez Hektor** : HTTP 200 et 0 octet, 9 sur 9
  (MES).
  - Chez nous, c'est une **erreur franche** : « Reponse Hektor JSON invalide init Sous offre » (1
    travail, le 13/10).
  - Aucun verbe connu ne repasse une offre en « proposée ».
- **Modifier une offre refusée.** Le formulaire s'ouvre et se pré-remplit, mais **l'enregistrement n'a
  jamais été essayé** (MES).
- **Changer l'état (accepter, refuser).** ✅ Ça marche, administrateur compris :
  `GET annonce-SuiviVente-updateOffre&id=&type=refus|accepte`.
  - Succès = `"1"`. Échec = `"[]"`, que l'offre n'existe pas ou que le type soit faux.
  - 1 253 gestes, 0 échec. L'aller-retour refusée → acceptée → refusée marche (offre 33048).
  - Cicatrices :
    - la colonne `date` prend **la date du geste** (1 205 offres sur 1 205 le 11/11) ;
    - 6 à 8 dates ont été **fabriquées** sur des offres sans entrée datée (T1) ;
    - accepter une offre sur un bien **vendu** le remet « Sous offre » : 15 biens le 12/11 ;
    - refuser la dernière offre laisse le bien « Sous offre » ;
    - Hektor ne refuse jamais seul les offres concurrentes.
  - L'ordre, ⚠ nuancé par l'écrit : « on annule le compromis d'abord, l'offre devient refusable
    ensuite » repose sur **notre propre verrou** (`offre_verrouillee`, 16/09) et sur une statistique du
    parc. Refuser chez Hektor l'offre acceptée d'un compromis **actif** n'a jamais été essayé. Refuser une
    offre **concurrente** pendant un compromis marche (essai du 26/10).
- **Annuler.** Ce n'est pas un geste à part : une offre ne s'annule pas, elle se refuse.
- **Supprimer.** `deleteOffre` a été relevé le 28/08. **Jamais codé, jamais essayé.**

### 2.2 Le compromis

- **Créer.** ✅ Ça marche, par l'assistant : `createCompromis` (la coquille), puis `getStepCompromis` et
  son panier. Il faut le compte **administrateur** : en négociateur, Hektor répond « Vous n'avez pas les
  droits pour créer un compromis ».
  - ⚠ Sans l'appel `findProspect`, l'acquéreur est ignoré **en silence** (PRO, 02/09).
  - ⚠ Hektor recompose le montant à partir du mandat : net vendeur + honoraires d'entrée.
  - Le statut du bien passe « Sous compromis ».
  - **Si un compromis actif existe déjà** : Hektor ne crée rien, sans message. Le worker refuse
    désormais avant d'envoyer : « il faut l'annuler avant d'en créer un autre » (W l. 18063-18080).
    ⚠ Les écrits se contredisent sur le cas où ce compromis est annulé (ACT 29/08, PAV 31/08, ta remarque
    du 09/11 sur un « bug »). À vérifier sur un bien d'essai.
  - 7 travaux de fin août à octobre rendent « aucun compromis nouveau vu en 15 s ». Au moins une fois
    c'était faux : le 50128 avait été créé, et il est apparu plus tard. Le filet `poserNumerosManquants`
    est là pour ça.
- **Modifier un compromis actif.** ✅ Ça marche par la reprise (50065 et 50078), mais sur des **biens
  d'essai** seulement : 46 corrections sur 4 biens.
  - Le statut du bien est remis à « Sous compromis » à chaque correction : 48 sur 48.
  - Notre garde refuse si Hektor a changé depuis la saisie (« REFUS D'ETAT », 03/11).
  - **Verrou en base** : `compromis_verrouille_par_vente` est allumé. Le compromis d'une chaîne qui porte
    une vente ne se corrige pas, parce que son statut repartirait « Sous compromis ».
  - ⚠ Le net vendeur retarde d'une correction (LT). Hektor a changé sa réponse d'API le 02/11 : la
    relecture est passée en `version=v2` le jour même.
- **Modifier un compromis annulé.** ⛔ **Échoue en clair** : « Désolé, un compromis clôturé ne peut pas
  être modifié » (travail du 02/11).
- **Annuler.** ✅ Ça marche, administrateur compris : `GET annonce-SuiviVente-cloture&idCompromis=&notes=`.
  - Le worker juge le succès sur `status=2`, relu.
  - Effets : le statut du bien est **inchangé**, et l'offre reste **acceptée**.
  - Notre cascade (`cascade_annulation_compromis`, allumée) refuse ensuite l'offre, chez Hektor aussi,
    mais elle n'écrit aucune date.
  - Hektor affiche « Compromis clôturé », le même mot que pour un compromis vraiment tombé.
- **Supprimer.** ✅ Ça marche, et c'est irréversible :
  `GET annonce-SuiviVente-deleteCompromis&idCompromis=&idAnn=`.
  - ⚠ Avec de mauvais noms de paramètres : `{"empty":"0"}`, sans effet.
  - ⚠ **Le statut ne redescend pas tout seul** (relevé du 07/09). C'est notre worker qui envoie la
    redescente, comme le fait l'écran de Hektor. Les notes du 29/08 et du 26/10 disent l'inverse :
    elles passaient par notre worker.
- **Réactiver un compromis annulé** : rien d'écrit.

### 2.3 La vente (elle n'a pas d'état chez Hektor)

- **Créer.** ✅ Ça marche par l'assistant `getStepVente`. 17 ventes créées, toutes sur des biens d'essai.
  - ⚠ **La réponse ment** : « Vous ne pouvez pas creer un bien » ×8 et `{"result":false}`, alors que la
    vente 23287 a bien été créée. Seule la relecture juge.
  - ⚠ Si une vente existe déjà, Hektor ne crée rien. Le worker refuse avant : « la suppression d'une
    vente est DÉFINITIVE, c'est une décision qui doit rester humaine ».
  - ⚠ « Enregistrer & archiver » a **détruit** la vente 23288.
  - Effets :
    - le statut passe à 5 ;
    - le compromis reste actif ;
    - **`diffusable` repasse à 1** : 989 biens vendus sont diffusables, et ta décision a été « on verra
      plus tard » ;
    - Hektor ajoute l'acquéreur aux mandants du bien ;
    - chez nous, le mandat est clos.
- **Modifier.** ✅ Ça marche, sans doublon : 23301 (08/09), puis le 18/09, puis **115 001 sur un bien
  vendu** le 02/11, sur la vente d'essai 23358.
  - ⚠ Le piège `amount` contre `sale_price` est corrigé le 02/11.
  - ⚠ Avec `transaction_date`, la clôture du mandat est rejouée à la date de la vente.
- **Supprimer.** ✅ Ça marche, et c'est définitif : `GET ventes-deleteVente&id=`. ⚠ Hektor rend **200 et
  un corps vide, au succès comme à l'échec**. Le juge, c'est `VenteById` qui rend 404.
  - Effets :
    - le statut passe de Vendu à Sous compromis, et c'est Hektor qui le fait ;
    - le compromis ne revit pas ;
    - `diffusable` repasse à 1.
  - Sur un bien sorti des annonces vivantes, l'effet est **non mesuré**.
- **Annuler.** Impossible chez Hektor : une vente se supprime. Ton geste « vente annulée » du 09/11 se
  joue chez nous seulement : la ligne reste, marquée et datée.

### 2.4 Le statut du bien et `diffusable` — ce qui décide de passer ou non par Hektor

- Toute **création** fait monter le statut du bien, et le worker envoie lui-même `upval status` juste
  après. ⛔ **On ne crée donc jamais chez Hektor une pièce plus ancienne que l'état du bien** : ce serait
  faire reculer un bien vendu.
- Le chemin sûr pour remettre un statut sans créer de transaction s'appelle `redescendreStatutHektor`.
  Passer par `change_hektor_annonce_status` en « sold » **créerait une vente**.
- « Actif » remet `diffusable` à 1, et c'est notre worker qui l'envoie (W l. 14036). « Clos » met 6 et 0.
- L'app refuse de créer hors du parc vivant (`transaction_hors_parc_vivant`, décision du 24/10) et sur
  une estimation (`transaction_refusee_sur_estimation`, allumé).

### 2.5 Ce que le tableau veut dire pour l'outil du matin

1. **Il y a trois verbes, et ils ne se remplacent pas** : créer, corriger un champ (la reprise), changer
   un état. Corriger une offre acceptée est impossible ; changer son état marche.
2. **Un geste se décide par l'état de la pièce ET par l'état du bien.** Une offre acceptée, un compromis
   annulé ou un compromis d'une chaîne vendue ne se corrigent pas chez Hektor. Une pièce plus ancienne
   que l'état du bien ne se crée pas chez Hektor.
3. **L'ordre** :
   - montant puis acceptation, pour une offre proposée ;
   - annulation du compromis puis refus de l'offre (c'est notre verrou) ;
   - suppression de la vente avant toute retouche du compromis, et c'est définitif : jamais par une
     règle, toujours par une décision humaine.
4. **Jamais « done » comme preuve.** Deux réponses de Hektor mentent : la création de vente, et la
   suppression de vente. Un seul juge, la relecture par numéro.
5. **Chaque changement d'état est une cicatrice** : la date de l'offre bouge, le statut bouge,
   `diffusable` bouge. Un geste de masse s'écrit avec ce qu'il laisse derrière lui.

---

## 3. Colonne par colonne : où la valeur s'écrit, qui l'écrit, Hektor est-il informé

> **Ta règle** : si notre case est vide, on prend le Sheet ; si elle est remplie et qu'elle diffère, le
> Sheet gagne.
>
> **Ses trois conditions** : chaque écrasement garde sa valeur d'avant ; il est écrit au journal ; la
> boucle s'arrête d'elle-même si le témoin du matin n'est pas vert.
>
> **« Qui écrit »** :
> - **la boucle** : l'outil du matin, qui écrit chez nous ;
> - **le worker** : il écrit chez Hektor, par un travail.
>
> **« Hektor informé »** : seulement pour une affaire **vivante**, c'est-à-dire un bien au parc et une
> pièce dans un état que le geste a prouvé (§ 2). Pour tout le reste : **chez nous seulement**, et c'est
> voulu.

**Offre Achat (la date de l'offre)**. Elle entre, puisqu'une ligne neuve commence par elle.

*L'audit, fait le 27/11 au soir* : même méthode que les 18 (Sheet du 26/11, verdict du passage 82, base
en direct). La date comparée chez nous est celle de la **première proposition** de l'offre, lue dans
son journal (`premiere_proposition`, règle R29 du juge), et jamais la colonne `date`, qui porte le
dernier mouvement.
- **4 769 cases au Sheet**, dont 64 sur des lignes non tranchées, qui n'ont pas de pièce sûre.
- Sur les 4 705 tranchées, **4 421 sont égales au jour près** : 4 279 sur une offre de Hektor, 142 sur
  une offre née du classeur le 16/11.
- **114 écarts**, médiane 2 jours ; 74 font 3 jours ou moins, 9 plus de 30 jours, le maximum 366. Ils
  portent sur :
  - **93 offres acceptées**, dont 13 sur un bien au parc : la correction est impossible chez Hektor ;
  - **21 offres refusées** : chez Hektor, leur date est déjà celle du refus.
  → **Aucun ne peut se corriger chez Hektor : chez nous seulement.**
- **170 manquent : la ligne n'a aucune offre parmi ses pièces.** 113 ont un compromis et une vente,
  49 un compromis seul, 8 une vente seule. C'est le cas « offre jamais saisie » : 66 % des offres
  depuis 2025 sont saisies chez Hektor **déjà acceptées**, et certaines jamais. Pour ces 170, créer
  l'offre chez Hektor ferait reculer le bien (§ 2.4) ; leur sort est ta décision **D10**.

*Où la date s'écrit* :
- **la pièce existe chez Hektor** : rien ne s'écrit si la date est égale. Si elle diffère, la date du
  Sheet va **au carnet** (`app_affaire_champ_app`, champ `date` de l'offre), qui prime à l'écran.
  - ⚠ La colonne `date` du registre est relue chez Hektor chaque nuit, et la protection lui est refusée
    nommément (`R2_JUGES_SUR_LE_REGISTRE`) : on n'y écrit pas.
  - Chez Hektor, seule une offre **proposée** se corrige (prouvé sur l'offre 33050). Elle n'est
    concernée par aucun des 114 écarts.
- **la pièce n'existe pas chez Hektor** : D10 pour le stock, D5 pour une ligne neuve.

*Une ligne neuve qui n'a qu'une offre* (aujourd'hui, 436 lignes tranchées n'ont qu'une offre, ni
compromis ni vente ; 417 sont « Annulée » et 19 « Offre d'achat », vivantes) :
1. La boucle voit la ligne neuve dans le journal des différences (étape 5).
2. Le juge cherche l'offre sur le bien, par la date. Tant que les négociateurs saisissent dans Hektor,
   la nuit l'a normalement déjà descendue. **Les 5 lignes neuves des 24 et 26/11 sont toutes dans ce
   cas** : le juge les a tranchées au passage 82, sur leur offre de Hektor.
3. Si elle est trouvée, la ligne prend son étiquette, et ses autres cases s'écrivent chez nous :
   - la Commission TTC → `honoraires_entree_app` (ta décision du 27/11) ;
   - la répartition → `app_affaire_repartition` ;
   - les notes et les avis.
   **Rien ne part chez Hektor.**
4. Si elle n'est pas trouvée après N jours : un **signal** dans le rapport du matin. C'est D5 :
   signaler, ou créer chez Hektor par `change_hektor_annonce_status`, cible `offer`, avec
   `transaction_date` = la date du Sheet.
   - ⚠ Sans `transaction_date`, la date du jour est posée.
   - ⚠ La création met le bien « Sous offre ». Elle est interdite sur un bien vendu, clos, en
     estimation ou déjà engagé.
   - ⚠ Si le Sheet la dit acceptée, il faut corriger le montant d'abord, puis `updateOffre accepte`.

**Compromis (la date)**. 4 246 cases, 4 096 égales à Hektor, 81 écarts, 51 manquants.
- **Compromis actif, bien au parc** : correction chez Hektor par la reprise (`transaction_date` →
  `dateStart`). Elle est prouvée 46 fois, mais sur des biens d'essai seulement. **3 des 81 écarts sont
  dans ce cas.**
- **Compromis actif d'un bien sorti du parc** : **70 des 81.** Quand sa chaîne porte une vente, ce qui
  est le cas ordinaire d'un bien vendu, il est verrouillé en base (`compromis_verrouille_par_vente` est
  allumé) → chez nous seulement. ⚠ Je n'ai pas compté combien des 70 ont une vente dans leur chaîne :
  c'est la première mesure de l'étape 7.
- **Compromis annulé** : Hektor refuse en clair (« un compromis clôturé ne peut pas être modifié ») →
  chez nous seulement. **7 des 81.**
- **Où chez nous** : le carnet, au champ `date` du compromis.
  - ⚠ Le compromis porte sa date de signature en colonne, relue chaque nuit.
  - ⚠ Avant que « le Sheet gagne » : **109 lignes** portent une annulation antérieure à la date du
    compromis, toutes avec « Signé » à FALSE. Il est probable que la case Compromis du Sheet porte
    alors le **rendez-vous** prévu, et non la signature. Faire gagner le Sheet là-dessus écrirait une
    date de signature qui n'a jamais eu lieu.
- 1 écart reste illisible pour l'outil.

**Vente Fixée (la date de la vente)**. 3 804 cases, 3 670 égales, 41 écarts, 92 sans vente chez nous.
- **Les 41 écarts sont tous des ventes de biens sortis du parc.** Écart médian 11 jours, maximum 50.
- Corriger une vente sur un bien vendu par la reprise (`transaction_date` → `date`) est prouvé **une
  fois**, sur la vente d'essai 23358 le 02/11, pour le prix et pas pour la date.
- Avec `transaction_date`, la correction rejoue la clôture du mandat chez nous, à la date de la vente :
  c'est le choix « A » du 02/11.
- → **chez nous seulement**, au carnet (`date` de la vente), tant qu'un essai réel sur une vente réelle
  n'a pas été fait avec ton accord.

**Commission TTC**. Ta décision du 27/11 est au § 5.
- Au stade de l'offre : `honoraires_entree_app`, chez nous.
- Les conflits sur un compromis ou une vente : chez Hektor, par la reprise (`seller_fees` →
  `honorairesEntree`), puis la nuit redescend la valeur.
- ⚠ Mais 4 seulement sur 46 tombent dans un cas déjà prouvé. Le détail est au § 5.

**Charge Commission**. 991 cases, 940 chez nous, 5 écarts, 21 manquants.
- **Chez nous seulement** : le carnet du mandat, `app_mandat_champ_app`, champ `charge_commission`.
- Hektor : **non mesuré**. Je ne sais pas si Hektor porte un champ « charge » sur le mandat ou sur la
  transaction ; le worker n'en envoie aucun.

**Les 6 colonnes des négociateurs et des pourcentages**. 4 499 lignes chez nous, 1 écart, 203
manquantes (toutes des affaires annulées), 30 illisibles par la règle du 13/11.
- **Chez nous seulement** : `app_affaire_repartition`, sur la chaîne, origine `classeur`.
- Hektor : le worker pose le négociateur à la **création** d'une transaction (`forme_negociateur`).
  Modifier la répartition d'une transaction existante chez Hektor : **non mesuré**. Les ventes de
  Hektor ont des champs `retro_*` que je n'ai pas lus.

**COMMENTAIRES (G) et En attente de (F)**. **Chez nous seulement**, `app_affaire_note`, origine
`classeur:G` ou `classeur:F`. Jamais chez Hektor.
- La nuit ne touche pas cette table.
- Une note neuve ou changée devient une **note neuve datée**. On n'écrase jamais une note : ta règle 6,
  « on ne supprime pas une part ».
- Ma proposition pour F reste :
  - garder hors les « V » et les pictogrammes seuls, comme tu l'as décidé le 17/11 ;
  - prendre tout le reste, y compris « SRU » ;
  - reposer en note neuve les 84 textes abîmés par le nettoyage (le « + » perdu 68 fois).

**Vente Réglée et Numéro de facture**. **Chez nous seulement** (`vente_reglee_app`,
`numero_facture_app`). La vente de Hektor n'a pas ces champs. Ceux qu'elle rend : id, prix,
honoraires, date, `retro_*`, honoraires d'entrée, de sortie et HT, commission de l'agence, part admin.
- 16 dates réglées et 14 factures peuvent se poser tout de suite : la vente existe chez nous.

**Annulée (la date)**. **Chez nous seulement** (`date_annulation_app`).
- Ta règle du 16/11 : la date va sur le compromis.
- Ta règle élargie du 27/11 : s'il n'y a aucun compromis et seulement une offre refusée, la date va
  sur l'offre. Cela concerne 249 lignes.
- **On ne touche pas l'état de la pièce** : c'est ton interdit. Sur les 6 lignes « annulées » au Sheet
  mais vivantes chez nous, on pose la date, et l'état reste tel quel.
- Pour une ligne neuve qui s'annule, voir la décision D4 au § 8.

**Les 3 colonnes d'avis**. **Chez nous seulement**, `app_classeur_avis`, ancrés sur l'ID Unique.

**Les 6 colonnes laissées dehors** (Prix, Mandat, Acquéreur, Vendeur, Vente Prévue — et Offre Achat, qui
rentre désormais). Elles restent **lues par le juge comme preuve**, et ne sont jamais écrites. ⛔
Règle du 25/11 : une source que le juge lit comme preuve ne se réécrit pas avec son verdict.

**Les colonnes que tu n'as pas citées** : Etat Actuel, Signé, Signée, Notaire, Nature, Agence, Ville,
les adresses, Divers, Lien CRM, product_ref. **Je les laisse dehors** sans ton mot.
- « Etat Actuel » n'est jamais touché : c'est ta réponse du 26/11.
- Le notaire existe pourtant chez Hektor sur la transaction (`notaires_json`).

---

## 4. Les 190 transactions nées du classeur, sans numéro Hektor

**Ce qu'elles sont**, mesuré le 27/11 : 35 compromis annulés, 96 offres refusées et 59 offres acceptées.
- Toutes ont été posées le 16/11 (lots C5 / B), avec `transaction_origine = 'classeur'`.
- Toutes ont `present_in_hektor = false`, et aucune n'a de date d'annulation.
- Leurs dates vont de 2018 à 2026 ; 104 sont postérieures au 01/01/2025.
- **114 sont sur un bien vendu chez Hektor** : les 59 offres acceptées, 36 des offres refusées et 19
  des compromis.
- 9 seulement sont sur un bien encore au parc : 4 compromis et 5 offres, toutes mortes.
- 177 ont dans leur chaîne une autre pièce qui, elle, est chez Hektor.

**Ce que le projet a déjà décidé** : la note du 15/11 (`patch_transaction_origine_2026-11-15.sql`)
distingue deux cas.
- « Elle **attend** son numéro Hektor » : c'est anormal si ça dure, et la sentinelle crie.
- « Elle **n'en aura jamais** » : c'est assumé. « Une reprise de l'historique (le classeur) n'ira pas
  chez Hektor. »
- La sentinelle `data.affaire_sans_numero_hektor` garde son seuil à 0 parce que ces 190 sont marquées.

**Pourquoi les créer chez Hektor serait un mauvais geste**, mesuré :
- créer passe par le statut du bien : 114 biens vendus repasseraient « Sous offre » ou « Sous
  compromis ». C'est l'accident du 12/11, quand 15 biens vendus sont redevenus « Sous offre » ;
- le worker refuse de toute façon un compromis sur un bien qui en porte un en cours, et une vente sur
  un bien qui en porte une ;
- une offre créée sans `transaction_date` prend la date du jour. Avec la date, la refuser ensuite pour
  la remettre dans son état déplace sa date au jour du refus : c'est la cicatrice du 11/11 ;
- elles sont mortes : Hektor n'en a besoin ni pour la diffusion ni pour le statut. Ta règle n° 4 : Hektor
  reste à jour **tant qu'il diffuse**.

**Ma recommandation : on n'en fait rien chez Hektor.** Elles restent chez nous, marquées, avec leur
ligne du Sheet. Deux choses restent ouvertes :
- elles n'ont pas de date d'annulation. Les dates élargies (étape 3) en poseront sur les offres
  refusées, et ta règle du 16/11 en posera sur les compromis ;
- `app_modifier_affaire_optimistic` les refuse (« cette transaction n'existe pas encore chez
  Hektor ») : on ne peut pas les corriger par l'écran. Une correction passe par le carnet, comme le
  reste du stock.

---

## 5. La Commission TTC, et les 19 compromis sans honoraires

**Ta décision du 27/11, reprise telle quelle** :
- la Commission TTC se pose **en entier dans les honoraires d'entrée**, comme Hektor le fait ;
- au stade de l'offre : `honoraires_entree_app`, chez nous ;
- les conflits sur un compromis ou une vente : chez Hektor, par la reprise ;
- les compromis annulés sans honoraires : on ne touche à rien.

**Pourquoi les 19 sont vides — c'est trouvé.** Sur les 21 lignes que mon audit rangeait « sans valeur » :
- **18 sont des compromis que nous avons créés le 16/11 depuis le classeur.** Ils ne sont pas chez
  Hektor : ce sont des 35 du § 4. Le lot ne posait que l'état et la date, jamais un montant. **Hektor
  n'en a jamais porté de vide : il ne les connaît pas.** Ta mesure « Hektor en porte sur 100 % des
  autres » est donc juste, et ces 18 n'y font pas exception.
- **1** est le compromis 46188 (bien 39684). Il est « actif » chez nous, mais Hektor ne le rend plus,
  il n'a aucun honoraire et sa date est `0000-00-00`.
- **2 sont une erreur de mon audit** : les compromis annulés 42816 et 13300 portent bien des honoraires
  d'entrée chez Hektor (7 670 et 11 290). Mon calcul les lisait par le prix moins le net vendeur, et
  ce net est vide. Le compte juste des « sans valeur » est donc **19**, et non 21.
- **Ma proposition pour les 18** : poser la Commission TTC du Sheet dans `honoraires_entree_app`, chez
  nous, comme pour les offres. Ils ne sont pas chez Hektor, donc il n'y a rien à corriger là-bas.
  C'est ta décision, et rien n'est fait.

**Les conflits, avant d'envoyer quoi que ce soit chez Hektor.** Mon audit en compte **46** : 34 vrais
désaccords, plus 12 où la vente porte une part et le Sheet le total. Ton chiffre est 43, et je ne
reconstitue pas l'écart de 3. Voici ce que chacun permet chez Hektor :
- **12** sont sur un compromis annulé → **impossible** (refus franc de Hektor) → chez nous seulement ;
- **14** sont sur une chaîne qui porte compromis et vente → le compromis est verrouillé, et la
  correction ne peut viser **que la vente** ;
- **15** sont sur une vente seule, d'un bien vendu → possible, mais une seule preuve, sur la vente
  d'essai 23358 ;
- **4** sont sur un compromis actif d'un bien au parc, « Sous compromis » → le seul cas **déjà couvert**
  par la reprise prouvée ;
- **1** est sur un compromis actif d'un bien sorti du parc → non mesuré.
- Pour les 12 où la vente porte une part : faut-il remettre le total chez Hektor, ou laisser la part ?
  C'est ta décision ; elle touche le partage entre agences (« c'est le nom des deux parts qui dit le
  partage »).
- ⛔ **Rien ne part avant un essai réel sur UNE vente réelle**, que tu choisis, relue par le juge
  honnête.

---

## 6. Le plan, étape par étape

> **À chaque étape, la méthode** : audit, explication de ce que ça pourrait casser ailleurs, ton
> « vas-y », code dormant, essai à blanc, ton accord, geste, relecture, documents.
>
> **Les coûts sont des estimations, pas des mesures.** Une écriture en base ou chez Hektor demande
> toujours ton accord, geste par geste.

**Étape 0 — le socle en base. ✅ FAIT le 27/11.** Copie relue identique, octet pour octet, par mon
contrôle et par le tien. Ensuite, chaque nouveau passage se recopie
(`socle_du_protocole_en_base_2026-11-27.py --ecrire` ne copie que les passages absents).

**Étape 1 — l'audit des gestes. ✅ CE DOCUMENT**, à ta lecture.

**Étape 2 — la règle des 334, ton geste 6.**
- **Ce qu'elle fait** : rattacher les pièces « à part sans effet sur l'étiquette » à leur ligne.
- **Où** : dans le juge, sur une copie du socle (un passage 83 joué sur copie).
- **Avant** : trancher les **24 pièces nommées par deux lignes**.
- **Preuve** : rejouée dans le juge avec ses gardes (mémoire « une règle se mesure dans le juge »), et
  0 ligne déjà rendue ne change d'étiquette.
- **Ni base ni Hektor.** Environ ½ jour.
- ✅ **MESURÉE le 27/11 au soir** (carnet § 20.98). C'est la variante **R30** du juge, éteinte par défaut,
  qui joue après tous les verdicts.
  - **Le témoin**, rejoué deux fois sans la variante : 4 803 verdicts du 82 sur 4 803 identiques.
  - **Avec R30** : 0 verdict et 0 étiquette changés. **277 pièces rattachées sur 258 lignes.** Les 57
    autres restent à part : 24 pièces nommées par 2 à 4 lignes (plusieurs façons : on s'abstient), et 3
    possibles aussi pour une ligne non tranchée.
  - ⚠ **Avant de la valider** : 87 des 277 sont dans un dossier orphelin, qu'aucune ligne ne porte. Les
    rattacher à leur ligne est un geste de chaînage. Et l'écrivain de la colonne A lit ces pièces :
    son effet est à mesurer sur la copie.
  - ✅ **Les deux mesures sont faites** (carnet § 20.99) :
    - **L'écrivain** : ses cases ne changent pas, mais son témoin 1 tombe de 4 733 à 4 660, parce que
      73 lignes auraient leurs pièces dans plusieurs dossiers.
    - **Les 87 orphelins** : 58 pièces y sont seules. 16 feraient changer l'étiquette en cas de fusion,
      et 6 touchent une pièce tenue par une autre ligne.
    - ⭐ **R30a**, la forme restreinte aux pièces déjà dans le dossier de leur ligne : 190 pièces sur 186
      lignes, 0 verdict et 0 étiquette changés, les témoins de l'écrivain intacts. **C'est la forme
      sûre**, et elle est proposée à sa validation.
  - ✅✅ **R30a VALIDÉE le 27/11 au soir** (son mot : « Oui, R30a. Tu as bien fait de reculer. »). Elle
    est dans `REGLES_VALIDEES` et joue à chaque passage. Le rejeu de contrôle donne 190 pièces sur 186
    lignes, 0 verdict et 0 étiquette changés.
    - ⛔ **R30 complète est refusée** ; elle ne reste dans le code que pour la mesure.
    - **Les 87 orphelins restent dehors.** Ils se reprendront comme un geste de chaînage, à part, et
      seulement les 58 qui sont seules dans leur dossier.
    - ⏰ **Le prochain passage officiel (83) portera R30a.** Il n'est pas joué : il change le passage que
      lisent l'écrivain et la boucle, et il se recopie ensuite en base. Les deux gestes attendent ton accord.
    - ✅ **Joué le 27/11 au soir, à son mot.** Le **passage 83** est sorti **ROUGE** : 5 lignes de témoin
      ont basculé.
      - 2 dans « ses_decisions » : R30a ajoutait 4782 à 91IHSGNC et 26697 à MQ6H8TVQ, deux lignes dont il a
        fixé les pièces.
      - 3 dans « v3_neutres » : la V3 rangeait déjà ces pièces avec leur ligne.
      - **Correction** : R30a ne touche plus aucune ligne de ses décisions, et le témoin v3_neutres compte
        « rattachée par R30a » comme un accord. Le **passage 84** est **VERT**
        (`temoin_d_apres_le_passage_83_2026-11-27.py 84 …`) : 188 pièces sur 184 lignes, 0 verdict et 0
        étiquette changés, identique au rejeu sur copie, témoins identiques au 82 (825), même image, mêmes
        entrées. Les témoins de l'écrivain restent 4 733 et 4 731 (« les 5 » échoue comme au 82, et c'est
        antérieur).
      - Le 83 reste au socle, comme trace.
      - ⏰ **Recopier les passages 83 et 84 en base, et faire passer l'écrivain et la boucle au 84** :
        attendent son accord.

**Étape 3 — les dates d'annulation élargies.**
- **Ce qu'elle fait** : s'il n'y a aucun compromis et seulement une offre refusée, la date va sur
  l'offre (249 lignes). On pose aussi la date sur les 6 lignes annulées au Sheet et vivantes chez nous,
  sans toucher leur état.
- **Où** : chez nous seulement, `date_annulation_app`, par le patron des lots du 16/11 : script, patch,
  inverse, répétition.
- **Ce que ça touche ailleurs** : les lecteurs de `date_annulation_app` (pilotage, écran du registre). À
  recenser avant le patch.
- **Ni Hektor ni l'état d'une pièce.** Les 109 « antérieures » attendent ta décision D3.
- Environ ½ à 1 jour.

**Étape 3 bis — les écritures sans risque, chez nous seulement** (ajoutée par lui le 27/11 au soir :
« Je ne vois aucune raison d'attendre cinq étapes pour poser ce qui ne risque rien »).
- **Les cases**, environ 840 :
  - En attente de : 245 manquantes et 160 écarts ;
  - les répartitions : 203 ;
  - COMMENTAIRES : 94 manquants et 107 écarts ;
  - les avis : 27 et 4 écarts.
  Elles ne touchent ni Hektor ni la nuit (la nuit ne touche ni `app_affaire_note`, ni `app_classeur_avis`,
  ni `app_affaire_repartition`).
- **Sa règle, telle quelle** : une case vide prend le Sheet ; une case remplie qui diffère, le Sheet gagne.
  - **Pour les notes, jamais d'écrasement** : une note neuve datée, et l'ancienne reste.
  - **Pour une part de répartition qui diffère** : la règle 6, « on ne supprime pas une part, on la met de
    côté ».
  - **Pour un avis qui diffère** : la valeur d'avant est gardée au journal.
  - Pour En attente de, sa décision du 17/11 tient : les « V » et les pictogrammes seuls restent dehors.
    Les 84 textes abîmés par le nettoyage reviennent en notes neuves.
- **La place de chaque note** : sur une pièce que le protocole donne à la ligne, avec R30a, donc après le
  passage 83. C'est aussi ce qui règle les 62 notes que la garde (famille B) a trouvées hors de leur ligne.
- **Le patron** : script, patch, inverse, répétition ; l'essai à blanc, puis ton accord.
- Les 30 répartitions illisibles par la règle du 13/11 restent dehors.
- Environ 1 jour.

**Étape 4 — la Commission TTC, ta décision.**
- **4a, chez nous** :
  - 298 cases au stade de l'offre → `honoraires_entree_app` ;
  - et, si tu dis oui (D2), les 18 compromis nés du classeur ;
  - un patch, son inverse, sa répétition.
- **4b, chez Hektor** : les conflits sur un compromis ou une vente. ⛔ **Déplacé à l'étape 9, en
  dernier** (ton mot du 27/11 au soir). D'ici là, chaque conflit est un **signal** du rapport du matin,
  et tu le corriges toi-même dans Hektor si tu le veux.
- Environ ½ jour.

**Étape 5 — la boucle, qui regarde seulement** (quelques jours, ta demande). Elle a huit pièces :
1. **la photo du jour** : l'image existe ; une tâche planifiée la prend chaque jour et la garde 15 jours.
   ⚠ Une tâche neuve se déclare d'abord dans la surveillance (`check_gti_health.py`). Hors 04:00-07:30.
2. **le journal des différences** : la photo du jour contre celle de la veille, case par case (ID Unique
   × colonne). Chaque case est neuve, modifiée ou disparue. Il est écrit dans une table chez nous : ta
   mémoire des décisions va en base.
3. **le juge** sur les lignes neuves ou modifiées, avec son empreinte (`empreinte_du_juge()`).
4. **le routeur** : UNE table en base, `app_champ_destination`. ⛔ **Pas une sixième liste : il y en a
   déjà cinq** (recommandation du 22/10, jamais créée). Une ligne par colonne : la destination chez
   nous, la règle (vide → Sheet, différent → Sheet gagne, ou exclue), le geste chez Hektor, ses
   conditions d'état, l'interrupteur. ⭐ **La même table servira à R3**, l'app qui écrit le Sheet : une
   seule table pour les deux sens.
5. **la décision par case** : ce qui s'écrirait chez nous, et le geste qui partirait chez Hektor, filtré
   par les règles du § 2.5 (pièce vivante, état prouvé, bien au parc, ordre).
6. **le témoin du matin**. Il est vert si :
   - la photo est lue ;
   - le juge est passé et reproductible ;
   - les sommes bouclent ;
   - aucune ligne déjà rendue ne change d'étiquette sans règle.
   S'il n'est pas vert, la boucle s'arrête d'elle-même.
7. **la garde, ta famille B** (§ 18.3, le geste 9) : chaque écriture (date, note, avis, répartition) est
   relue pour voir si elle est toujours sur la pièce que le protocole lui donne. Sinon, la boucle propose
   la place juste et le journal le dit. En mode « regarder », elle montre seulement. Déjà mesuré : 15
   dates et 62 notes ne sont pas sur une pièce de leur ligne.
8. **le rapport du matin**, que tu lis : les cases neuves et modifiées, ce qui s'écrirait, ce qui partirait
   chez Hektor, ce qui ne peut pas.

Elle n'écrit que dans ses propres tables, et ces tables se créent avec ton accord. Environ 3 à 4 jours.

**Étape 6 — la boucle écrit chez nous**, derrière un interrupteur, après tes jours de lecture.
- Chaque écrasement garde sa valeur d'avant et sa ligne de journal. Le carnet porte déjà
  `valeur_hektor_au_moment`.
- ⚠ **Le point ① de la note du 22/10 est toujours ouvert** : il faut une porte appelable sans écran.
  Aujourd'hui, nos écritures du stock passent par des patchs SQL. La boucle a besoin d'un chemin de
  code avec les mêmes gardes que les patchs.
- Environ 2 à 3 jours.

**Étape 7 — les lignes neuves.** ~30 à 40 par mois (mesure du 19/11).
- Aujourd'hui, le négociateur saisit dans Hektor et la nuit descend la transaction. Le juge rattache la
  ligne à sa pièce.
- **Non mesuré** : qui arrive en premier, la ligne du Sheet ou la transaction de Hektor ; et pourquoi le
  Sheet a deux formes d'ID Unique (4 166 en majuscules, 631 en minuscules hexadécimales).
- Ma proposition : la boucle attend que la pièce existe, et la signale si elle manque après N jours. La
  création chez Hektor par la boucle ne vient que par ta règle (D5).
- Environ 1 jour.

**Étape 8 — R1 à R5, la fin du chantier.** C'est là que le gel s'endort. Repris de la note du 19/11
(§ 10.6), sans changement de fond.
- **R1 LIRE** : la colonne A est relue chaque nuit dans une table chez nous (étiquette → ID Unique,
  numéro de ligne), avec une vue que l'app interroge. La sentinelle des lignes non reliées en sort
  presque gratuite. Environ ½ jour.
- **R2 MONTRER** : sur l'écran d'une affaire, « sa ligne du classeur » ; tu choisis les colonnes.
  Environ 1 jour de front.
- **R3 ÉCRIRE** : l'app écrit dans le Sheet (la phase B), avec la table de routage de l'étape 5, une
  table des livraisons, un écrivain neuf et `app_sheet_ecrit`. ⛔ Le verrou V1 est toujours à toi : lire
  les Apps Script du classeur, puisque Sheet1 nourrit la paie. Environ 2 jours.
- **R4 LES LIGNES NEUVES** : l'app crée la ligne avec son étiquette à la naissance de l'affaire, à la
  validation du siège (§ 7.7 de la note du 09/11). Dès ce jour, plus aucune ligne ne naît sans
  étiquette : **le gel s'endort.**
- **R5 LES NON ÉCRITES** : le protocole s'arrête aux 70. Ce sont tes 61 « rien à étiqueter », tes 9
  impossibles, et tes 2 doubles vides par décision. R5 les **signale**, il ne les cherche plus.

**Étape 9 — EN DERNIER, et peut-être jamais : la boucle informe Hektor.** Ton mot du 27/11 au soir :
c'est la plus chère et la plus risquée, et elle ne concerne que les affaires vivantes.

*La mesure demandée* : combien de gestes chez Hektor par semaine, en vrai, si la boucle ne traite que
les affaires vivantes ?
- **La source** : les 6 photos du Sheet en cache, du 22/11 10:44 au 26/11 09:49, soit **4,0 jours**.
- **Qui est vivant** : une ligne tranchée au passage 82 dont une pièce est vivante (offre proposée ou
  acceptée, compromis actif, ou vente), sur un bien au parc, avec son numéro Hektor. **135 lignes sur
  4 733.** Tu en comptes 142 ; je ne reconstitue pas l'écart de 7, faute de ta définition.
- **Ce qui a bougé en 4 jours** : 187 cases sur toutes les lignes, hors colonne A. Dont 50
  COMMENTAIRES, 45 En attente de, 17 Etat Actuel, 9 avis, 8 Compromis, 8 Vente Fixée, 7 factures, 6
  charges. Et 5 lignes neuves.
- **Sur les affaires vivantes, dans les colonnes qui informeraient Hektor** : 13 changements, et
  **aucun ne demande de geste** :
  - les 8 « Vente Fixée » sont des dates **à venir** (30/11 au 17/12) sur des affaires qui n'ont pas
    encore de vente : la vente se crée à la signature ;
  - 4 des 5 « Compromis » sont des dates **à venir**, ou de la semaine (24/11 au 08/12), sur des
    affaires qui n'ont pas encore de compromis ;
  - le 5e est le Sheet qui rattrape Hektor : la date est déjà égale.
  - « Annulée » posée sur une affaire vivante : 0 ;
  - les 5 lignes neuves ont toutes leur offre chez Hektor. Leurs cases s'écrivent chez nous, et leur
    Commission TTC va dans `honoraires_entree_app`.
- **Réponse : 0 geste chez Hektor en 4 jours.** Ramené à la semaine : 0. La mesure est courte (4 jours,
  une semaine de fin novembre), mais elle va dans ton sens.
- ⭐ **Et elle apprend une chose** : sur une affaire vivante, le Sheet porte les dates de compromis et de
  vente **avant** l'évènement. Ce sont des rendez-vous. C'est la même chose que les 109 « antérieures »
  (D3) : une date du Sheet n'est une date de signature que si la pièce existe.

*Ma recommandation* : pas d'étape 9 pour l'instant. Le rapport du matin porte une rubrique « à
corriger dans Hektor ? », une ligne par cas, et tu corriges toi-même si tu le veux. On ne rouvre
l'étape 9 que si la rubrique dépasse deux ou trois cas par semaine pendant un mois.

*Si on la faisait un jour, ses quatre préalables restent* :
- **une porte sans écran pour la reprise** :
  - `app_modifier_affaire_optimistic` exige un administrateur connecté (`is_app_manager_or_admin`) ;
  - sa charge « part entière », fabriquée par l'écran, et le worker de l'offre reconstruit le
    formulaire de Hektor avec elle ;
  - il faudrait la fabriquer côté serveur, sans copier l'écran : c'est l'interdit écrit dans le code.
- **un essai réel par état touché** (135 gestes sur 138 sont sur des biens d'essai) ;
- **le débit** : quota de 13 000 à 17 000 requêtes par période. Le coût d'une reprise en requêtes n'est
  pas mesuré ;
- **les interdits codés** :
  - créer une pièce plus ancienne que l'état du bien ;
  - corriger une offre acceptée, un compromis annulé, ou le compromis d'une chaîne vendue ;
  - supprimer une vente ;
  - changer un état (D4).

Environ 3 à 5 jours plus les essais, si un jour il le faut.

**Le total, sans l'étape 9** : environ 12 à 15 jours de travail, sans compter les attentes d'accord ni les
jours de lecture de la boucle. C'est une estimation.

### 6.1 Ce qui survit à la coupure, et ce qui meurt avec elle — étape par étape

> **La boucle est un transitoire** : c'est le nom que tu lui as donné le 26/11. Il y a **deux
> coupures**, et elles ne tuent pas les mêmes choses :
> - **la coupure du Sheet** : R3 et R4, quand l'app écrit le Sheet et qu'on n'y saisit plus. Le Sheet
>   cesse d'être une source ;
> - **la coupure de Hektor** : ton étape 2 du 08/10, « l'app fait tout le travail quotidien, Hektor ne
>   fournit plus que les numéros ». Hektor cesse d'être une destination pour les transactions.

- **Étape 0, le socle en base** : **survit.** C'est la mémoire des décisions, et elle sert à l'histoire.
- **Étape 2, la règle des 334** : son **résultat survit**, puisque les pièces restent rattachées. Le
  juge **meurt à la coupure du Sheet** : quand chaque ligne naît avec son étiquette (R4), on n'apparie
  plus.
- **Étape 3, les dates d'annulation** et **étape 4a, la Commission chez nous** : **survivent.** Ce sont
  des données chez nous, et c'est leur place définitive.
- **Étape 5, la boucle qui regarde** :
  - la photo du jour, le journal des différences et le juge du jour **meurent à la coupure du Sheet** ;
  - ⭐ **la table de routage survit** : elle sert à R3 dans l'autre sens (D9, confirmé) ;
  - la garde (ta famille B) **survit tant que la nuit recalcule les chaînes** ;
  - le témoin et le rapport du matin **changent d'objet** : ils surveilleront l'écriture de l'app dans le
    Sheet.
- **Étape 6, la boucle qui écrit chez nous** : son code **meurt à la coupure du Sheet** (le sens
  s'inverse) ; **son journal survit**, avec les valeurs d'avant de chaque écrasement.
- **Étape 7, les lignes neuves** : **meurt à la coupure du Sheet**, puisque R4 fait naître la ligne avec
  son étiquette.
- **Étape 8, R1 à R5** :
  - R1 (lire la colonne A) **devient un contrôle** : vérifier que le Sheet porte ce que l'app a écrit ;
  - R2 (montrer), R3 (écrire) et R4 (créer la ligne) **survivent : c'est le sens définitif** ;
  - R5 (signaler les non écrites) survit tant qu'il en reste.
- **Étape 9, informer Hektor** : **meurt entièrement à la coupure de Hektor.** C'est la raison de plus
  pour ne pas la construire avant d'en avoir besoin.
- ⭐ **Ce qui ne meurt avec aucune des deux coupures** : les places chez nous (carnet, notes, avis,
  répartition, cases `_app`), la table de routage, et le journal. C'est là que va l'effort.

---

## 7. Ce qui ne se mesure pas aujourd'hui — dit au lieu d'être supposé

- Ce que fait une correction de compromis ou de vente sur un **bien vendu réel**. Une seule preuve
  existe, sur la vente d'essai 23358.
- Refuser chez Hektor l'offre **acceptée** d'un compromis **actif**.
- Enregistrer la modification d'une offre **refusée**.
- **Créer avec une date passée** : rien d'écrit, aucun essai.
- Supprimer une offre.
- L'effet de la suppression d'une vente sur un bien sorti des annonces vivantes.
- Le nombre de requêtes Hektor par geste.
- Combien des 70 compromis hors parc ont une vente dans leur chaîne.
- Combien de cases du Sheet changent par jour **sur la durée**. Je n'ai que 4 jours (187 cases, 5 lignes
  neuves, du 22 au 26/11) : le journal des différences n'existe pas encore.
- Si Hektor porte un champ « charge » ou la répartition sur une transaction.
- Tes chiffres 106, 43, 426, 386, 154 et 1 163 : je ne les reconstitue pas, faute de ta définition.
- Les Apps Script du classeur (V1).
- Si Hektor recalcule le hors-taxe au moment où l'on change le montant d'une vente. Ma déduction est oui :
  l'essai sur 0bc98552 le dira, en relisant tous les champs avant et après.

### 7.1 ⚠ Les réserves — ses aberrations, NOTÉES ET NON TOUCHÉES (son mot du 27/11 au soir)

> « Le Prix est hors périmètre, mais je ne veux pas que ça se perde. » Rien de ce qui suit ne s'écrit : on le
> signale.

- **La colonne Prix porte 42, 43 ou 63 sur 990 lignes** (437 fois 43, 308 fois 42, 245 fois 63) : un numéro
  de département, pas un prix.
- **La colonne Prix porte 0 sur 12 lignes.**
- **743 € sur la ligne VMSFVBJS**, ta saisie, que tu as vue toi-même.
- **650e65c8 est réglée avant sa vente** : vente 3265 du 29/01/2026, « Vente Réglée » au 15/12/2025.
- ⚠ Conséquence pour le contrôle ③ de D6 : sur ces lignes, le prix ne peut pas concorder. Le jour où leur
  vente arrivera, elles sortiront en « écart de prix » et seront signalées, jamais écrites.

---

## 8. Ce que je te demande de trancher

> ✅ **SES RÉPONSES DU 27/11 AU SOIR — elles font foi** (« J'ai poussé. Voilà mes réponses, enchaîne. »)
>
> - **D1 OUI** : les 190 restent chez nous. « Elles sont mortes, elles restent. »
> - **D2 OUI** : la Commission TTC des 18 compromis nés du classeur va dans `honoraires_entree_app`.
> - **D3 OUI, les 109 sont exclues**, et voici la raison à écrire : « ce ne sont pas des écarts de date de
>   compromis, c'est ma date d'annulation qui tombe avant le rendez-vous de signature. Les corriger serait
>   corriger la mauvaise colonne. »
> - **D4 : la date et le signal. Jamais l'état.** « Changer un état chez Hektor automatiquement, c'est
>   refuser une offre ou annuler un compromis sans qu'un humain l'ait voulu. Hors de question. »
> - **D5 : signaler d'abord.** La boucle ne crée rien chez Hektor de son propre chef.
> - **D6 : le Sheet fait foi sur le montant. Mais on ne corrige que si l'on est sûr de comparer la bonne
>   chose.** Trois contrôles doivent passer avant d'écrire une seule commission :
>   - **① HT ou TTC** : la colonne porte la commission **TTC**. Le champ visé doit être le TTC, et non une
>     part hors taxes. `commission_agence` en est une, et elle est vide depuis mai 2026 : **ne jamais la
>     comparer à la colonne** ;
>   - **② la bonne transaction** : on compare à la **vente** quand elle existe. Sans vente, la commission
>     du compromis est provisoire : c'est une affaire en cours, elle reste **en attente** ;
>   - **③ le prix doit concorder** : si le montant de Hektor diffère du Prix du Sheet, ce n'est pas un écart
>     de commission mais un écart de prix. On le **signale à part**.
>
>   - **④ le partage entre agences** (ajouté et accepté par lui le 27/11 au soir) : avant de corriger une
>     commission, vérifier que le montant du Sheet n'est pas une **part** d'un partage entre agences, par
>     exemple exactement la moitié ou les trois quarts du montant de Hektor. Si c'en est une, on ne corrige
>     pas : on signale.
>
>     ⭐ **Élargi le 27/11 au soir (son mot : « prends tous les rapports ronds de partage, pas trois valeurs
>     choisies »)** : tout rapport de 5 % en 5 %, ainsi que le tiers et les deux tiers.
>   - **⑤ l'entrée seule** (le sien, 27/11 au soir) : si le montant du Sheet est égal aux seuls honoraires
>     d'entrée et que la sortie n'est pas nulle, on ne touche à rien. C'est rare (la sortie n'est remplie
>     que sur 0,2 % des ventes) ; exemple : a49d96ef, 15 000 d'entrée et 11 000 de sortie.
>   - **⑥ un coefficient connu** (le sien, 27/11 au soir) : si le rapport du Sheet sur Hektor vaut un
>     coefficient de TVA (1,2, 1/1,2, 1,196, 1,1), on ne corrige pas : on signale. Exemple : 0bc98552,
>     6 000 contre 5 000, soit exactement 1,2.
>   - **Le recompte du 27/11 au soir, avec les six contrôles : 6 vrais conflits sur 19.**
>     - 13 sont retirés : 11 parts rondes (50 %, 60 %, 75 %, 80 %), 1 entrée seule, 1 coefficient de TVA.
>     - Les 6 restants sont 78bb247a, 650e65c8, b7aabaf3, ad8681cd, EAQJ9D0T et KO6QPUV7. Chacun a une
>       raison connue, écrite au carnet § 20.101.
>
>   Quand les six passent, **le Sheet gagne et on corrige l'app** : « c'est mon montant qui sert à la
>   paie ». Et tout ce qui paraît aberrant (un prix à 743 €) se **signale**, sans jamais s'écrire en
>   silence.
>   - ✅ **Mesuré aux trois contrôles** (carnet § 20.99) :
>     - ① le champ TTC est égal au Sheet sur 3 683 ventes ; `commission_agence` ne l'est que 3 fois ;
>     - ② 1 020 lignes sans vente sont en attente ;
>     - ③ 10 écarts de prix sont signalés à part ;
>     - **19 conflits** passent les trois contrôles, mais **9 sont un partage** (le Sheet porte exactement
>       la moitié ou les trois quarts) : un 4e contrôle est proposé. Il en reste 10.
>   - **Aberrations** : la colonne Prix porte 42, 43 ou 63 (un département) sur 990 lignes, et 743 sur
>     VMSFVBJS.
> - **D7** : trois ventes candidates à lui proposer (réelles, récentes, avec un petit écart), chacune avec
>   ses risques. C'est lui qui choisit. Proposées : 0bc98552, ba54cb6c et b7aabaf3 (carnet § 20.99).
>   - ⛔ **0bc98552 EST RETIRÉE le 27/11 au soir** (son mot : « si tu ne peux pas l'expliquer, change de
>     candidate »). Son rapport vaut exactement 1,2, et rien chez nous ne l'explique : Hektor est cohérent
>     avec lui-même (prix 96 000 = net vendeur 91 000 + 5 000, sur le compromis comme sur la vente), le Sheet
>     dit 6 000, et le montant de la facture GGTI00004518 n'est pas en base.
>     **Aucune autre candidate ne passe ses critères** :
>     - 78bb247a est un de ses cas en attente, et elle baisse le montant ;
>     - 650e65c8 est aberrante ;
>     - b7aabaf3 et ad8681cd sont hors de l'index historique, et portent un partage 50/50 chez Hektor ;
>     - EAQJ9D0T a une facture suivie d'un avoir, KO6QPUV7 un protocole d'accord : leur montant a été
>       renégocié.
>
>     **Ma recommandation** : pas d'essai maintenant. L'étape « informer Hektor » est la dernière, et peut-être
>     jamais nécessaire (D11).
>   - *(l'ancien choix, gardé pour l'histoire)* **0bc98552** (vente 23319, bien 43437, 23/09/2026, prix 96 000 ; Sheet 6 000 contre
>     Hektor 5 000). Elle est dans l'index historique, et « je préfère qu'un premier essai monte un montant
>     plutôt qu'il le baisse ». b7aabaf3 est écartée : elle a deux risques à la fois.
>   - **Sa question avant l'essai** : Hektor recalcule-t-il son hors-taxe ou sa part admin quand on change
>     le montant ? Mesuré le 27/11 dans nos copies de Hektor (9 292 ventes), sans rien écrire :
>     - la **part admin** vaut 0 sur les 9 292 ventes : il n'y a rien à recalculer ;
>     - la **rétrocession** vaut 0 partout ;
>     - **`commission_agence`** vaut 0 sur 23319. Elle est vide depuis mai : 4 ventes sur 185 en portent
>       une ;
>     - le **hors-taxe** de 23319 vaut 4 166,67, soit exactement 5 000 / 1,2 : c'est la forme calculée, que
>       portent les ventes récentes (sur 9 000 ventes anciennes, ce champ porte le TTC tel quel).
>
>     ⛔ **Ce que je ne sais pas** : si Hektor recalcule le hors-taxe au moment de la modification. La seule
>     modification d'honoraires sur une vente date du 18/09, sur une vente d'essai supprimée depuis, et elle
>     n'a rien gardé du hors-taxe avant et après. **Ma déduction** : le hors-taxe passera à 5 000 (6 000 /
>     1,2).
>
>     **Le protocole proposé pour l'essai** : relire la vente par son numéro, en lecture seule, AVANT et
>     APRÈS, et comparer **tous** ses champs, pas la seule case visée : prix, honoraires, hors-taxe,
>     commission de l'agence, part admin, date, acquéreurs, mandants. Seul `seller_fees` part dans
>     `champs_touches`, et jamais `transaction_date` (sinon la clôture du mandat est rejouée).
> - **D8 OUI** : le Notaire et les colonnes non citées restent dehors.
> - **D9** : déjà confirmé.
> - **D10 NON** : on ne crée pas l'offre chez Hektor pour les 170 lignes. Leur date va chez nous.
> - **D11 OUI, le signal suffit.** L'étape « informer Hektor » reste en dernier, et elle ne se prépare que
>   si le rapport du matin montre qu'elle sert vraiment.
> - **R30** : ses deux mesures (les 87 dossiers orphelins, et l'effet sur l'écrivain de la colonne A) se
>   font sans l'attendre. Puis R30 lui est présentée complète, et c'est là qu'il dira oui ou non.

- **D1** — Les 190 nées du classeur : rien chez Hektor, elles restent chez nous. *(ma recommandation)*
- **D2** — Les 18 compromis nés du classeur : leur Commission TTC va dans `honoraires_entree_app`.
- **D3** — « Le Sheet gagne » sur la date du compromis : faut-il en exclure les 109 lignes annulées avant
  leur compromis, toutes avec « Signé » à FALSE ? *(ma recommandation : oui, les exclure)*
- **D4** — Une ligne qui s'annule au Sheet alors que l'affaire est vivante chez Hektor : la boucle
  pose-t-elle la date et signale-t-elle, ou change-t-elle l'état chez Hektor (annuler le compromis,
  refuser l'offre) ? *(ma recommandation : la date et le signal ; l'état reste un geste humain)*
- **D5** — Une affaire neuve du Sheet qui n'existe pas chez Hektor après N jours : la boucle la signale,
  ou la crée ? *(ma recommandation : la signaler d'abord)*
- **D6** — Les 12 ventes qui portent une part quand le Sheet porte le total : remettre le total chez
  Hektor, ou laisser la part ?
- **D7** — L'essai réel de l'étape 4b : sur quelle vente ?
- **D8** — Le Notaire et les autres colonnes que tu n'as pas citées restent dehors : confirmé ?
- **D9** — ✅ **CONFIRMÉ le 27/11 au soir** : une seule table de routage en base
  (`app_champ_destination`), pour les deux sens. « C'est elle qui empêchera l'aller-retour entre mon
  Sheet et mon app, et je ne veux pas d'une sixième liste. »
- **D10** — Les 170 lignes dont l'offre n'a jamais été saisie, alors qu'elles ont un compromis ou une
  vente : on crée l'offre chez nous seulement (origine `classeur`, comme les lots du 16/11), ou on
  laisse la case du Sheet seule ? Chez Hektor, c'est exclu : le bien reculerait.
- **D11** — L'étape 9 (informer Hektor) : on la remplace par une rubrique « à corriger dans Hektor ? »
  du rapport du matin. *(ma recommandation : oui ; 0 geste mesuré en 4 jours)*
