# AUDIT PAR OBJET — ÉTAPE 2 — 08/10/2026

*Lecture seule. Cinq auditeurs en parallèle, un par groupe d'objets, puis synthèse. Les deux
constats les plus graves (sécurité, désarchivage) ont été **revérifiés en base** par la
session principale. Les autres reposent sur les preuves des auditeurs (fichier:ligne,
requête, commit), citées ci-dessous.*

> **Pourquoi cet audit.** L'audit du 07/10 (`AUDIT_AUTONOMIE_COMPLET_2026-10-07.md`) mélangeait
> l'étape 2 et l'étape 3 et s'est trompé sur plusieurs objets (voir §5). Frédéric : *« il faut
> refaire un audit sur les objets annonces contacts recherches etc... vert orange rouge en
> lecture seule »*.

> **La grille = l'étape 2 telle que Frédéric la définit (08/10)** : *« Dans l'étape 2 on utilise
> encore Hektor pour générer les id afin de faire fonctionner les workers. »* L'app fait tout le
> travail quotidien ; Hektor vit, **il fournit les numéros**, les workers lui **envoient** les
> mises à jour. **Étape 3** = registre électronique des mandats (nos numéros), puis signature,
> puis passerelles, plus les autres gestes d'autonomie (site, DNS, e-mail). Ce qui ne poserait
> problème qu'après la coupure est marqué ⚪ et **n'est pas rouge**.

**Légende** : 🟢 conforme à l'étape 2 · 🟠 fonctionne, mais écart ou fragilité réelle ·
🔴 bloque, ou une saisie peut se perdre aujourd'hui · ⚪ étape 3 · ♻ déjà traité · 📜 décision
écrite.

**Les huit critères** : C1 créer · C2 modifier · C3 statut / fin de vie · C4 afficher sans
Hektor · C5 mises à jour venues de Hektor · C6 identité et corps gardés chez nous ·
C7 surveillance · C8 utilisable par un négociateur.

---

## §0. LE VERDICT

**Le socle est solide pour les objets principaux.** L'annonce, la recherche et la transaction
naissent chez nous, s'affichent sans Hektor, et ce qui redescend de Hektor n'écrase pas une
saisie de l'app. Le travail sur les doublures, la protection champ par champ et les numéros tient.

**Les vrais trous ne sont PAS des champs qui manquent.** Ils sont de quatre sortes :
les **droits** des négociateurs · des **gestes qui passent encore par Hektor d'abord** · des
**échecs qui se perdent en silence** · quelques **bugs précis**, dont certains anciens, que
l'audit du 07/10 n'avait pas vus. Plus une **faille de sécurité** sérieuse.

---

## §1. LE TABLEAU

| Objet | C1 Créer | C2 Modifier | C3 Statut, fin de vie | C4 Afficher | C5 Mises à jour Hektor | C6 Gardé chez nous | C7 Surveillance | C8 Négociateur |
|---|---|---|---|---|---|---|---|---|
| **Annonce** | 🟢 naît chez nous · 🔴 la suite échoue en silence | 🟢 | 🔴 | 🟢 (🟠 archives) | 🟢 | 🟢 (🟠 archives) | 🟠 | 🔴 |
| **Contact** | 🟠 6 champs | 🟠 12 champs | 📜 / 🟠 | 🟢 (🟠 62 000 sur 356 000) | 🟢 | 🟢 | 🟢 / 🟠 | 🟢 |
| **Mandant** (relation) | 🔴 / 🟠 | 🔴 | 🟢 (🟠 cas rare) | 🟢 | 🟢 | 🟢 (🟠 sauvegarde) | 🟠 | 🔴 |
| **Recherche** | 🟢 (🔴 si échec) | 🟢 📜 | 🟢 📜 | 🟢 | 🟠 | 🟢 (🟠 2 perdues) | 🟠 | 🟠 |
| **Transaction** | 🟢 | 🟢 | 🟠 | 🟢 | 🟠 | 🟢 | 🟠 | 🟠 |
| **Mandat** | 🔴 dormant | 🔴 absent | 🔴 | 🟢 | 🟠 | 🟢 | 🟠 | 🟠 |
| **Documents** | 🔴 | 🟠 absent | 🔴 | 🟢 | 🔴 (connu, G.2) | 🟢 / 🟠 | 🟠 | 🔴 |
| **Photos** | 🔴 | 🔴 absent | 🔴 absent | 🟢 | 🟠 | 🟢 | 🟠 | 🔴 |
| **RDV, visites** | 🟢 | 🟢 / 🟠 | 🟢 | 🟢 | 🔴 agenda Hektor | 🟢 / 🟠 | 🟠 | 🟢 |

---

## §2. LES HUIT CHANTIERS — les gros problèmes, regroupés par thème

*Ce ne sont pas des objets : ce sont les thèmes qui traversent les objets. Numérotés par gravité.
**L'ordre de travail est une décision de Frédéric** ; voir le plan, section « 🧭 LES CHANTIERS
DE L'ÉTAPE 2 ».*

### ① SÉCURITÉ — des fonctions ouvertes à un visiteur non connecté (🔴, revérifié en base)

Toutes sont `SECURITY DEFINER`, sans contrôle de rôle (ni `is_app_admin`, ni `auth.role`),
et **EXECUTE accordé à `anon`** (`has_function_privilege('anon', …)` = vrai) : n'importe qui
avec la clé publique du front peut les lancer.

| Fonction | Ce qu'elle fait |
|---|---|
| **`app_bascule_identite_contact_annuler(p_appliquer)`** | ramène tous les contacts au numéro Hektor sur 13 tables (rapprochements, e-mails, propositions, relances, saisies en attente…) — **la plus dangereuse** |
| `app_bascule_identite_contact(p_appliquer)` | relance la bascule des contacts |
| `app_attribuer_chaines_affaire()` | écrit dans le registre des affaires |
| `app_annonce_pending_solder_hektor(…)` | solde une saisie d'annonce en attente (elle reste au journal) |
| `app_photos_remplir_adresses_app(p_heures, p_tout)` | réécrit les adresses des photos (a un plancher) |
| `app_photo_marquer_sortie_vitrine()` | marque des photos sorties de la vitrine (a un plancher) |

Plus : la vue `app_contact_relations_current` (propriétaire postgres, pas `security_invoker`,
SELECT accordé à `anon`) est lisible sans connexion : numéros, titres, numéros de mandat.
Origine probable : `supabase/patch_c13_bascule_identite_contact_2026-09-23.sql:245,320` accorde
à `service_role` **sans REVOKE sur PUBLIC**. La liste des « 9 fonctions anon » de l'audit du
07/10 ne citait pas ces fonctions.

### ② LES DROITS DU NÉGOCIATEUR (🔴 — bloque l'étape 2 elle-même)

`app_console_can_request_job` n'autorise un commercial que pour 7 types de travaux
(documents). Avec un compte commercial, voici ce qui est refusé :
- **annonce** : modifier, changer le statut, archiver, désarchiver, changer de négociateur,
  supprimer. Il peut seulement créer, et seulement dans une agence où il porte déjà une annonce ;
- **mandant** : tous les gestes (rattacher, retirer, créer, modifier) ;
- **transaction** : tout (`is_app_admin` dans les 4 RPC). La décision du 25/08 (E.0) suppose un
  circuit de demande de validation, mais **il n'en existe aucun pour les transactions**
  (seulement diffusion, baisse de prix, annulation de mandat) ;
- **documents et photos** : générer un avis de valeur, un mandat ou un plan cadastral,
  supprimer un document, ajouter une photo, resynchroniser ;
- **mandat** : demander un numéro (admin ou manager seulement, sans décision écrite trouvée).

Comptes actifs : 3 admins, 2 commerciaux, 0 manager, contre **39 négociateurs** qui portent le
parc vivant. Tous les usages mesurés viennent d'un admin. *(Déjà noté L10-11.)*
**Il faut d'abord une décision de Frédéric** : que fait un négociateur seul, que demande-t-il ?

### ③ DES GESTES QUI PASSENT ENCORE PAR HEKTOR D'ABORD (🔴)

- **Annonce, mise sous mandat (Estimation → Actif) et « Mandat clos »** : rien n'est écrit chez
  nous (`app_change_annonce_status_optimistic`, cas cible `active` / `closed`). 18 mises sous
  mandat depuis l'app, la dernière le 03/09.
- **Annonce, archiver et changer de négociateur** : l'intention va dans le carnet
  `app_annonce_champ_app`, que **ni l'écran ni le run ne lisent** (aucun lecteur dans `api.ts`,
  `run_full_pipeline.ps1:1173-1181`). Le motif d'archivage ne vit que dans la charge du travail.
- **Mandat, clôture** : `submitHektorClosedStatus` (worker l. 13121-13135) part chez Hektor
  d'abord, et **la date de clôture posée par l'app n'arrive ni au registre ni dans `app_mandat`**.
  Mesuré : mandat 62966/18842 (clos dans l'app le 28/08), `mandat_date_cloture` NULL dans les
  deux tables. Le registre lit la clôture dans `versions_json` (`export_app_payload` l. 1796),
  jamais dans le carnet. 📜 Hektor n'est pas informé de la clôture (C.13, 28/08,
  `CLOTURE_MANDAT_CHEZ_HEKTOR=false`).
- **Documents et photos, ajout** : la ligne n'existe chez nous qu'après Hektor
  (`handleUploadDocumentToHektor` l. 7891, `handleUploadHektorPhoto`). Le chemin « chez nous
  d'abord » existe mais dort (aucun appelant ne pose `app_document_id`, l. 7899 et 8071). 105
  fichiers jamais effacés dans `temp/uploads`.
- **Document, suppression** : Hektor d'abord, puis **notre copie est détruite** (fichier du
  serveur, cloud, ligne ; `handleDeleteDocumentFromHektor` l. 8164-8213).

### ④ DES ÉCHECS QUI SE PERDENT EN SILENCE (🔴 / 🟠)

- **La suite de la création d'une annonce** : si les champs complémentaires ou le mandant saisis
  à la création échouent, le travail est quand même marqué « réussi », sans nouvel essai ni
  alerte (`console_job_worker.js:19709-19725` et 19761-19862). C'est arrivé 3 fois sur 79
  créations pour les champs (dernière le 08/07) et 1 fois pour un mandant (28/08).
- **Aucun nouvel essai automatique** pour : `create_hektor_annonce` (le brouillon),
  `create_hektor_contact`, `add_hektor_contact_search`, `upload_document_to_hektor`, l'ajout
  d'une photo, les gestes mandant. Tous sont absents de `types_rejouables`
  (`app_console_action_enqueue_due_retries`). Le worker écrit pourtant « Le travail sera
  repris » (`cibleHektorContact`, l. 1993), ce qui est faux pour ces cas.
- **Une création d'annonce en échec** reste affichée « Annonce en création » sans marque
  d'erreur, car le marqueur lit une table qui n'est plus remplie. La fiche saisie ne vit que
  dans la charge du travail, et une purge manuelle l'a déjà effacée (21/08 : 19 créations).
- **Une recherche créée en échec** : la ligne affichée passe en erreur, puis disparaît au bout
  de 24 h (`app_sweep_stale_provisionals`) ; il n'y a pas de bouton « réessayer ». 0 cas réel.
- **Photos ajoutées en créant une annonce** : elles attendent dans la mémoire du navigateur
  (`draftAnnonceQueuedPhotos`, `App.tsx:12210`, `:13175-13192`). Si l'onglet se ferme ou si la
  création échoue, **elles sont perdues**.
- **L'alarme « travaux en erreur » est bloquée au rouge à 15 depuis le 01/10** (14 relectures
  du 01 au 05/10, plus 1 retrait de mandant le 03/10). Un nouvel échec s'y noie. Les gestes
  mandant et transaction ne dépassent jamais 1 tentative, donc n'entrent jamais dans
  `geste_abandonne` (qui en exige 5). Les 4 types de gestes de transaction sont absents de
  `JOB_TYPES_A_NOTIFIER` (worker l. 17101).

### ⑤ DES BUGS PRÉCIS — des gestes cassés (🔴 / 🟠)

| # | Bug | Objet | État | Preuve |
|---|---|---|---|---|
| 5a | **Désarchiver est impossible.** `app_restore_annonce_optimistic` cherche le bien dans `app_dossier_current` et lève `dossier_not_found`. Or **0 archive sur 35 317** y figure. Cassé depuis `e7b9df7` (30/08). | Annonce | 🔴 revérifié en base, pas éprouvé à l'écran | bouton `App.tsx:29701` → `api.ts:9560` |
| 5b | **Modifier un mandant depuis sa carte** : l'écran passe le **numéro Hektor** (`App.tsx:7272` `sourceId = hektor_target_id`, puis `:3691`). `app_update_mandant_contact_optimistic` appelle `app_edit_contact_optimistic` avec ce numéro, qui répond `contact_not_found`, et l'erreur est avalée. Ni valeur chez nous, ni file d'attente, ni nouvel essai. Contournement : la fiche contact. | Mandant | 🔴 | jamais exécuté depuis la bascule (dernier le 31/08) |
| 5c | **Le premier numéro de mandat demandé depuis l'app** fera échouer l'envoi de nuit de `app_mandat`, **chaque nuit**. Pas de copie fraîche avant `mandat_ledger.py` (run l. 819-824 et 946), donc le run donne un second numéro ; l'envoi se fait sans `on_conflict` (`push_upgrade` l. 501-503) et heurte l'unicité `(hektor_annonce_id, numero_mandat)`. S'y ajoutent : la date est au format `JJ-MM-AAAA` (`inputDateToFrench`, `App.tsx:3779`) ; un numéro est brûlé si les étapes 2 à 5 échouent. | Mandat | 🔴 dormant (3 usages, le dernier le 28/08) | |
| 5d | **Le filet du rattachement d'un mandant vise la mauvaise clé.** Le worker filtre `hektor_contact_id = identité` (l. 14914 et 15169), alors que la RPC range le **numéro Hektor** dans cette colonne (travail `22c75301` : `contact_id 10355712`, ligne 1000009 : `hektor_contact_id 605030`). Un rattachement refusé par Hektor reste affiché à vie. `cef0ed2` annonçait ce filet réparé : jamais éprouvé. | Mandant | 🟠 | |
| 5e | **Retirer puis rattacher le même mandant** : la RPC fait `ON CONFLICT DO NOTHING`, donc `retire_le` reste posé. Le lien est créé chez Hektor mais reste invisible et impossible à retirer (`relation_ledger.py:514`). Cas réel : contact 10355712 sur 62963 et 62964. | Mandant | 🟠 | |
| 5f | **Un échec passager sur une offre ou un compromis** remet l'ancien état (`restaurerEtatAffaire` l. 18677, dans tous les `catch`). Si le nouvel essai réussit, rien ne repose l'état : l'écran montre l'ancien jusqu'au run de nuit. **Contraire à la décision du 29/08** (C.4-bis). | Transaction | 🟠 | |
| 5g | **Supprimer un contact** depuis la bascule : le nettoyage local reçoit NOTRE numéro (`console_job_worker.js:18250` → `delete_local_contact.py`), alors que le miroir est rangé par numéro Hektor. La ligne survit et le build la reconstruirait probablement. Les liens `app_relation` ne sont pas effacés. | Contact | 🟠 jamais éprouvé | |
| 5h | **Créer un mandant qui échoue** : le contact et le lien restent affichés comme réels, avec un contact sans numéro Hektor. | Mandant | 🟠 | |
| 5i | **Conflit causé par l'app elle-même** : si un autre geste de l'app touche le bien chez Hektor pendant les 10 min d'attente d'une modification, la saisie est soldée « Hektor plus récent » sans prévenir. Jamais arrivé. | Annonce | 🟠 | `app_annonce_pending_solder_hektor` |

### ⑥ CE QUI NE REDESCEND PAS DE HEKTOR (🔴 / 🟠)

- **Documents des 724 biens en vente** : aucun relu depuis le 20/08, 132 jamais lus. Connu :
  **G.2 (ajouter `--detect`) puis G.6, après le rattrapage**, périmètre = toutes les annonces
  vivantes, estimations comprises (décision de Frédéric, 07/10). L'ouverture d'une annonce ne
  rafraîchit que la signature.
- **Photos** : les ajouts remontent (95 la nuit du 07/10), mais **ni les retraits ni l'ordre**
  (`present_in_hektor = false` sur 0 des 437 346 lignes ; cas vérifié : annonce 63065, photo
  485136). Seul le bouton admin « Resynchroniser » corrige.
- **Agenda des visites Hektor** : importé nulle part. Environ 115 bons de visite par mois dans
  Hektor (chiffre du 07/10, non remesuré). **Question à Frédéric** : vos négociateurs
  saisissent-ils encore leurs visites dans Hektor ?
- **Recherche créée dans Hektor** : le carnet « devenu acquéreur » n'a rien détecté en 18 jours
  (aveugle aux contacts déjà acquéreurs). Elle arrive par des chemins détournés (date de mise à
  jour du contact, relecture). 📜 Rattrapage global avant la coupure (20/09).
- **2 recherches archivées ont disparu du cloud** (74680 et 76218), avec 7 lignes accrochées
  (5 notifications). Les sentinelles sonnent depuis le 30/09 et le 07/10 sans suite. Cause non
  établie.
- **RDV déplacé directement dans Google** : il ne revient pas chez nous.

### ⑦ DES GESTES QUI N'EXISTENT PAS (🔴 / 🟠)

- **Mandat** : modifier ou prolonger un mandat. Il n'y a ni travail worker ni RPC ; l'avenant ne
  change que le prix. Il faut ouvrir Hektor.
- **Photos** : changer l'ordre, choisir la photo principale, rendre visible ou masquer, retirer
  (E.0-bis).
- **Document** : renommer.

### ⑧ CE QUI N'EST GARDÉ CHEZ NOUS QU'EN PARTIE (🟠)

- **Contact** : à la création, seuls 6 champs sont écrits chez nous (nom, prénom, email,
  téléphone, négociateur, agence) ; à la modification, 12 (`col_map` de
  `app_edit_contact_optimistic`). Société, SIRET, conjoint, commentaire, catégorie et réglages
  CRM attendent le retour de Hektor.
- **Périmètre** : le cloud porte 62 154 contacts sur 356 395. Je n'ai trouvé aucune décision
  écrite sur ce choix. **Question à Frédéric.**
- **Archives d'annonces** : le corps complet n'existe que dans `data/hektor.sqlite`, qui n'est
  pas dans la sauvegarde automatique (`--full` jamais passé : `run_backup.ps1:41`). La fiche
  d'archive exige « Préparer », qui passe par le worker (7 fiches en cache sur 35 317).
- **Sauvegarde quotidienne** : `app_relation`, `app_relation_registry`, `app_mandat`,
  `app_affaire_champ_app` et les carnets n'y sont pas (`backup_critical.py`). Les liens nés dans
  l'app et pas encore adoptés n'existent qu'en un seul exemplaire (Supabase). Le stockage
  Supabase n'est pas sauvegardé, Veeam n'a jamais été restauré (G.3, G.4).
- **Bon de visite** : autonome, mais **archivé nulle part** (ni PDF, ni ligne). Son numéro
  `BDV-` ne forme pas une série.
- **Document retiré dans Hektor** : sa ligne est supprimée (`pruneDeletedDocuments` l. 5352) et
  son fichier reste orphelin. Pas de règle « delete-never » comme pour les photos. 193 lignes
  sans fichier chez nous (G.1-d).

---

## §3. LE DÉTAIL PAR OBJET

### Annonce (estimations comprises : 12 739 des 13 463 annonces vivantes)

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🟢 / 🔴 / 🟠 | La ligne naît chez nous avec notre numéro, dans la même transaction que le travail ; la fiche complète revient en environ 72 s (cas du 24/09 : demande 10:21:20, fiche 10:22:32, 15 534 octets). 🔴 suite en silence (④). 🟠 création en échec non rejouée (④). | `app_create_annonce_job_optimistic` ; interrupteur `c9_annonce_nait_dans_app` allumé le 25/09 ; 0 création depuis l'app depuis le 24/09 |
| C2 | 🟢 (🟠 5i) | Chez nous d'abord, visible tout de suite, envoyé après 10 min ; 5 essais, conflit visible, jamais purgé. File aujourd'hui : 0. | `app_edit_annonce_optimistic`, `app_annonce_enqueue_due_pushes`, worker l. 10515-10555 |
| C3 | 🔴 | ③ + 5a. Offre, compromis et vente : visibles tout de suite (l'affaire est écrite d'abord). Supprimer : 📜 Hektor d'abord (`f48d55a`, 01/09). « Admin seulement » pour le statut : **pas une décision datée**, seulement un commentaire dans la fonction. | |
| C4 | 🟢 / 🟠 | Liste et fiche lisent nos tables ; la relecture à l'ouverture tourne en arrière-plan (109 en 7 jours, médiane 26 s). 🟠 archives (⑧). 🟠 le contrôle de baisse de prix lit le prix chez Hektor (`hektor_bridge.py:410-427`, 491) : faux « Prix différent » si une saisie est en attente (L10-5). | `api.ts:4864` |
| C5 | 🟢 (🟠) | Protection champ par champ (run et relecture reposent les champs saisis dans l'app). 🟠 le run efface l'index des archives dans Supabase **sans plancher** si la copie locale revient vide (L10-8). | `push_upgrade_to_supabase.py:1232-1252`, 1636-1650 ; `app_annonce_reappliquer_saisies` ; `6932135` |
| C6 | 🟢 / 🟠 / ⚪ | 13 463 vivantes sur 13 463 avec leur fiche ; « une annonce, un numéro » : 0 écart. 🟠 archives (⑧). ⚪ numéro Hektor obligatoire dans 16 tables (L10-1), corps serveur refait depuis le miroir (N.4), `diffusable` vide à la naissance, numéro de dossier. | |
| C7 | 🟠 | Sentinelles conflit, saisie incomplète, envoi bloqué, un numéro. Rien sur la suite de création ni sur le carnet jamais appliqué ; alarme figée (④). | `check_gti_health.py` |
| C8 | 🔴 | ② | |

### Contact (fiches de couple comprises)

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🟠 | Naît chez nous tout de suite (`nextval(app_contact_identite_seq)`), le push ne supprime jamais un contact ≥ 10 M ; mais 6 champs seulement (⑧) et pas de nouvel essai (④). 16 créations au total, la dernière le 21/09. | `app_create_contact_optimistic` ; `push_contacts_to_supabase.py:527-551` |
| C2 | 🟠 | Chaîne bonne (file, 5 essais, conflit, jamais purgé, cron `app-contact-push-due` chaque minute) ; 12 champs affichés tout de suite (⑧). Aucune modification depuis l'app depuis le 31/08. | `app_edit_contact_optimistic` |
| C3 | 📜 / 🟠 | 📜 Suppression par Hektor d'abord, admin ou manager (30/08, plan l. 351). 🟠 5g. 12 suppressions passées, toutes avant le 23/09. | |
| C4 | 🟢 / 🟠 | Lu dans Supabase sous RLS, relecture asynchrone. 🟠 périmètre 62 154 / 356 395 (⑧). | |
| C5 | 🟢 | Saisie en attente protégée, garde-fou `date_maj` → conflit plutôt qu'écrasement, champs propres à l'app réinjectés. Fragilité : si la lecture de `app_contact_pending` échoue, la protection s'ouvre pour la nuit (`push_contacts_to_supabase.py:467`), mais la saisie reste dans la file. | worker l. 16722-16741 |
| C6 | 🟢 / ⚪ | 0 contact sous 10 M, 0 sans cible, 0 en double identité ; 14 sans `app_contact_id` (seuil 150) ; dans la sauvegarde quotidienne. Couples : 40 189 avec `refCouple`, 2 756 non traduits (seuil 3 000). ⚪ C.9-couple (Hektor fabrique la paire), **mais la mesure ne peut se faire que tant que Hektor vit** : sonde `033e946` prête, geste humain à faire. | |
| C7 | 🟢 / 🟠 | 11 sentinelles, toutes « ok » le 07/10 sauf `contact_lignes_sans_numero` (371 pour un seuil de 150). Un contact né dans l'app sans numéro Hektor ni saisie en attente n'est surveillé par rien. | `app_monitor_status` |
| C8 | 🟢 | Un commercial crée (sous son email) et modifie dans son périmètre ; ne supprime pas (aucune décision écrite trouvée). 0 travail contact demandé par un commercial. | `app_console_can_request_contact_job` |

### Mandant (relation contact ↔ bien)

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🔴 / 🟠 | 🔴 **mandants saisis à la création d'une annonce** : rien chez nous, perte silencieuse (④). 🟠 rattacher un existant : ligne `app_relation` posée au clic mais en « best effort » (erreur avalée), et filet inopérant (5d). 🟠 créer et rattacher : rien n'est défait si le worker échoue (5h). ⚪ refus `missing_hektor_annonce_id` sans numéro Hektor. Petite fragilité : `String(null)` = « null » passe le garde-fou (`api.ts:8122`). | |
| C2 | 🔴 | 5b. | |
| C3 | 🟢 / 🟠 | Retrait daté à la seconde, filet prouvé en réel le 03/10 (travail `b17f5417`). 📜 « mandat numéroté → refus » (`AUDIT_RETIRER_UN_MANDANT_2026-10-02.md` §6) ; 📜 Q3 (30/09). Gardes ⑤ et ⑥. 🟠 5e. | `run_full_pipeline.ps1:925-929` |
| C4 | 🟢 | Les deux fiches lisent le registre par la vue (`VITE_RUBRIQUE_CONTACT_REGISTRE` allumé par défaut, `api.ts:276`). Vue lisible par `anon` (①). | |
| C5 | 🟢 | Adoption par la clé (contact, bien), jamais de suppression, contrat sur `retire_le`. Lien 10354641 / 62964 retiré le 03/10, marqué absent le 05/10. | `relation_ledger.py:270-330`, 440-475 |
| C6 | 🟢 / 🟠 | 132 709 liens dans Supabase, 132 707 sur le serveur, carnet de 167 743 clés. 🟠 hors sauvegarde quotidienne (⑧). | |
| C7 | 🟠 | `relation_disparue` : 7 gardes, « ok ». Manque la garde « lien app non adopté après N jours » (plan ⑥.7). Échecs noyés (④). | `app_en_attente_humain` |
| C8 | 🔴 | ② | |

### Recherche acquéreur

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🟢 / 🔴 | Cas normal : affichée tout de suite, vraie recherche en 30 à 40 s, rapprochée la minute suivante (4 travaux, 4 réussis ; 87 des 90 recherches récentes ont des rapprochements). 🔴 échec non rejoué (④). Recherche saisie en créant le contact : 🟠 rien chez nous avant Hektor (11 créations sur 16, toutes réussies). | `app_create_search_optimistic`, `trg_search_dirty`, cron `rapprochement-dirty` |
| C2 | 🟢 📜 | UPDATE sur place, critères fusionnés, rapprochement recalculé dans le même appel, rien ne part chez Hektor (C.3, 24/08 ; 📜 20/08). | `app_edit_search_optimistic` |
| C3 | 🟢 📜 | Archive posée chez nous dans la même transaction, envoi sans retour attendu (📜 20/09). 3 travaux, 3 réussis. | `app_console_create_delete_contact_search_job` |
| C4 | 🟢 | `loadContactSearches` + `app_get_rapprochements`. | |
| C5 | 🟢 / 🟠 | Une recherche affinée n'est pas écrasée (prouvé : 255 000 € gardés 14 nuits). Fragilité : si la lecture de la protection échoue, elle s'ouvre (`push_contacts_to_supabase.py:440-441`), et la perte serait **définitive** (1 recherche exposée). 🟠 carnet aveugle (⑥). | |
| C6 | 🟢 / 🟠 | `app_search_id` rempli à 100 %, 0 doublon, 0 rapprochement orphelin. 🟠 2 recherches disparues (⑥). 🟠 registre local : 11 lignes sous le numéro de l'app au lieu du numéro Hektor (0 doublon à ce jour). ⚪ le distributeur `app_search_id_app_seq` n'a jamais servi. | |
| C7 | 🟠 | `recherche_disparue` = 2 (avertissement depuis le 30/09), `orphelins_recherche` = 7 (depuis le 07/10), sans suite. Rien sur une création en erreur. | |
| C8 | 🟠 | Gestes présents, jamais utilisés par un négociateur. Défauts d'écran : « Création Hektor » affiché même en modification ; recherche en création ni modifiable ni supprimable ; « Création expirée » annoncé à tort au bout de 15 min si le worker est lent. | `ContactSearchModal.tsx` |

### Transaction (offre, compromis, vente)

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🟢 | Ligne d'affaire écrite chez nous au clic, dans la même transaction SQL que le travail ; numéro Hektor posé en quelques secondes ; nouvel essai sans doublon. 330 affaires nées dans l'app, 0 sans numéro. Aucun usage depuis le 18/09. | `app_change_annonce_status_optimistic`, worker l. 18990-19060 |
| C2 | 🟢 | Montant et date corrigés tout de suite ; autres champs au carnet ; affichage « arrivé / pas encore parti / conflit ». | `app_modifier_affaire_optimistic` |
| C3 | 🟠 | 5f. Suppression : 📜 la ligne disparaît entièrement (07/09). | `app_geste_affaire_optimistic` |
| C4 | 🟢 | 31 047 lignes lues dans Supabase. | `loadAffairesForDossier` (`api.ts:1909`) |
| C5 | 🟠 | Principe bon (contrat vidé le 16/09). Trois fragilités : un geste fait **pendant** le run est écrasé jusqu'à la nuit suivante ; case 3.5 « une transaction supprimée peut ressusciter » encore ouverte ; marquage « absente » sans plancher (L10-8). | `affaire_ledger.py` ; `refresh_ledger` l. 870-903 |
| C6 | 🟢 / ⚪ | Une seule série `app_affaire_id`, corps complet dans `payload_json`. ⚪ chaînage sur les numéros Hektor ; le serveur local n'insère jamais une affaire née dans l'app (26bis). | |
| C7 | 🟠 | Sentinelles : `transaction_disparue` = 2 (compromis 49971, 49970), `ecart_statut_regle` = 6 pour un seuil de 4. Les gestes en échec ne préviennent personne (④). | |
| C8 | 📜 / 🟠 | ② | |

### Mandat

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🔴 dormant | 5c. 📜 Le numéro vient de PROTEXA via Hektor jusqu'à l'étape 3 (29/09) : c'est normal. | |
| C2 | 🔴 | ⑦ | |
| C3 | 🔴 | ③ (clôture) ; 📜 un mandat échu déclenche une alerte, il ne se clôt pas (30/07). | |
| C4 | 🟢 | Registre (24 494 lignes) et `app_mandat` (26 842) lus dans Supabase. ⚪ le registre est construit `FROM hektor.hektor_annonce`. | `app_registre_mandats_current` |
| C5 | 🟠 | Le run réécrit type, dates et mandants chaque nuit : juste à l'étape 2 puisque l'app ne modifie aucun mandat. Mais la date de clôture est exclue de l'`ON CONFLICT`, donc figée à la première insertion, **y compris pour les clôtures faites dans Hektor** : 118 clôtures au registre contre 91 dans `app_mandat` (cause probable, non prouvée). | `mandat_ledger.py` l. 546-566 |
| C6 | 🟢 / 🟠 / ⚪ | `app_mandat_id` propre, clé (annonce, numéro), rien n'est effacé, mandants pris dans nos liens (06/10). 🟠 hors sauvegarde quotidienne. 📜 montant retiré (06/10). ⚪ série légale, `hektor_annonce_id NOT NULL`. | |
| C7 | 🟠 | `mandat_disparu` et `mandat_un_numero` au vert. Rien ne voit une clôture faite dans l'app qui manque au registre. Non mesuré : si `mandat_corps_recopie` tourne chaque nuit. | |
| C8 | 🟠 | ② ; le négociateur passe par `demande_annulation_mandat` pour la clôture (📜 spéc. du 30/07). | |

### Documents

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🔴 | ③ (Hektor d'abord, pas de nouvel essai). PDF générés (avis de valeur, mandat, cadastre) : fabriqués chez nous, puis le même dépôt chez Hektor. Quand Hektor répond, ça marche (les 8 derniers envois sont sur le serveur et dans le cloud). | l. 7331, 7429, 7645 |
| C2 | 🟠 | ⑦ (renommer). | |
| C3 | 🔴 | ③ (suppression destructrice). 32 usages entre juin et juillet. | |
| C4 | 🟢 | 21 851 documents dans le cloud, 85 256 sur le serveur seul (« Préparer » les remonte sans Hektor). 🟠 193 sans fichier nulle part (G.1-d). | `handlePrepareDocumentCloud` |
| C5 | 🔴 / 🟠 | ⑥ (connu, G.2 puis G.6). Signature aboutie : n'arrive qu'à l'ouverture de l'annonce ou par une synchro (51 en attente, 308 signées avec leur PDF). Rattrapage : lot d'archives de 1 250 fait la nuit du 07/10, 0 erreur ; ensuite les ventes (lot 2 500 maintenu par Frédéric). G.1-b (brouillons) pas codé. | |
| C6 | 🟢 / 🟠 | Le serveur porte tout. 🟠 ⑧. | |
| C7 | 🟠 grave | Seule la tâche de 21 h est surveillée (`check_gti_health.py:110`). Le gel du 20/08 est passé inaperçu 7 semaines. | |
| C8 | 🔴 | ② | |

### Photos

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🔴 | ③ + ④ (perte possible à la création d'une annonce). Copie sur le serveur après confirmation : ♻ `c95cb9b`. | |
| C2 | 🔴 | ⑦ | |
| C3 | 🔴 | ⑦ | |
| C4 | 🟢 | 74 992 photos vivantes, toutes avec leurs versions réduites ; la vitrine a publié 449 annonces avec nos adresses. | |
| C5 | 🟠 | ⑥ | `rattrapage_photos.js` ne crée que les lignes absentes |
| C6 | 🟢 | 437 344 originaux sur 437 346 sur le serveur. La purge des six mois ne peut rien retirer avant le 26/03/2027 (📜 G.8). | |
| C7 | 🟠 | Les 4 étapes photo envoient leur signal de vie à des clés **absentes** de `app_worker_registry`. La sonde ne regarde que 25 annonces par nuit, et dans un seul sens. | |
| C8 | 🔴 | ② | |

### RDV et visites

| | Couleur | En une phrase | Preuve |
|---|---|---|---|
| C1 | 🟢 / 🟠 | RDV : Google d'abord, puis le lien chez nous, sans Hektor (`routers/google_workspace.py:506`). 11 liens, le dernier le 15/06 : pas d'usage réel. **Bon de visite : autonome** (`visitVoucherHtml`, `App.tsx:37607-37787`), mais 🟠 non archivé (⑧). Lien public de RDV : 2 250 liens, 0 demande reçue depuis toujours. | |
| C2 | 🟢 / 🟠 | Déplacer depuis l'app : Google et notre lien suivent (0 usage). Un déplacement fait dans Google ne revient pas (⑥). | |
| C3 | 🟢 | Suppression dans Google, lien marqué supprimé (3 cas). | |
| C4 | 🟢 | Lu dans Supabase. | |
| C5 | 🔴 | Agenda Hektor non importé (⑥). | |
| C6 | 🟢 / 🟠 | ⑧ (bon de visite). | |
| C7 | 🟠 | La tâche des liens publics est surveillée ; aucune sentinelle sur l'usage. | |
| C8 | 🟢 | Un commercial lié à Google agit sur son agenda ; les 2 commerciaux actifs sont liés. | `_assert_workspace_subject_allowed` |

**Mandat de vente (le document)** : le texte et le PDF sont fabriqués chez nous
(`mandatPreviewHtml`, Puppeteer), mais **gardés seulement après leur dépôt chez Hektor**. Le
numéro vient de PROTEXA (normal à l'étape 2). 18 PDF, le dernier le 24/07.

---

## §4. ⚪ CE QUI EST ÉTAPE 3 — à ne pas compter en rouge

- Numéro Hektor obligatoire dans 16 tables, et 8 fonctions qui refusent sans lui (L10-1).
- Corps serveur refait depuis le miroir (N.4, 26bis-CONTACTS, 26bis-RECHERCHES,
  26bis-TRANSACTIONS) ; registre des mandats construit depuis `hektor.hektor_annonce`.
- `diffusable` vide à la naissance (Hektor le donne en environ une minute) ; numéro de dossier
  EM/VA ; paire de ménage fabriquée par Hektor (C.9-couple, **à mesurer tant que Hektor vit**).
- Série légale des mandats, signature ImmoSign via Hektor, diffusion.
- La recherche ne naît pas sous notre numéro ; la modale n'exprime que 7 critères ;
  l'archivage d'une recherche dépend de l'envoi chez Hektor.
- Fichiers rangés sous le numéro Hektor de l'annonce ; liens publics `?ref=<numéro Hektor>`
  (jeton instable) ; fiche visite PDF fabriquée par Hektor ; logo du mandat chargé sur
  `www.gti-immobilier.fr` ; interrupteur `ENABLE_HEKTOR_ACTIONS`.

---

## §5. CE QUE L'AUDIT DU 07/10 DISAIT DE FAUX

| Il disait | En réalité |
|---|---|
| « L'annonce naît avec 11 champs » (anomalie) | Fiche complète en environ 1 minute, 13 463 sur 13 463 → ⚪ étape 3 |
| « La ligne provisoire de l'annonce est effacée en 24 h » | Faux depuis le 25/09 : l'annonce naît dans `app_dossier_current`, et le run l'épargne (`480be8e`) |
| « Une recherche créée dans l'app n'est qu'une ligne provisoire effacée 24 h après et jamais rapprochée » | Faux dans le cas normal : la vraie recherche arrive en 30 à 40 s et elle est rapprochée. Seul l'**échec** n'est pas rejoué. |
| « Le corps d'une transaction est fabriqué chez Hektor » | Faux : montant, date, acquéreurs et charge complète sont écrits chez nous au clic |
| « Le bon de visite dépend de Hektor » | Faux : il est autonome ; ce qui manque, c'est l'archivage, la série, et l'import de l'agenda Hektor |
| « Mandant : ligne durable ✅ » | Trop optimiste : best effort, filet sur la mauvaise clé, mandant créé en échec non défait |
| « Relation, modifier : — » | Le geste existe, mais il n'est pas optimiste dans les faits (5b) |
| « Le run réécrit le mandat chaque nuit » (défaut) | Vrai, mais pas un défaut à l'étape 2 : l'app ne modifie aucun mandat → étape 3 |
| « 19 RDV créés dans l'app » | 11 |
| Il n'avait vu | ni 5a (désarchivage), ni 5b (modifier un mandant), ni la suite de création en silence, ni la date de clôture perdue, ni 5f, ni les six fonctions ouvertes |

La même erreur sur les recherches était recopiée dans la liste (L1 rouverte, tâche L10-2) : corrigée le 08/10.

---

## §6. ♻ DÉJÀ FAIT — à ne pas refaire

- **Annonce** : naissance dans l'app avec notre numéro (`24849c4`, `59aac63`, `627399b`, essai
  `1596c5d`, interrupteur allumé le 25/09) · le run épargne une annonce née dans l'app (`480be8e`)
  · protection champ par champ (`6932135`) · une saisie ne se perd jamais (`31411aa`) · filet de
  rejeu des gestes (`04dadf3`) · carnet d'archivage (`e7b9df7`) · relecture immédiate réparée
  (`3607d29`, `113596c`).
- **Contact et mandant** : R-1 (`c020d47`) · retirer un mandant (`60ada75`, `a6f22ce`,
  `d13fb08`) · rattachement optimiste (`31c529b`, `b85a8f3`, `cef0ed2` avec le défaut 5d) · la
  vue dérive le rôle (`83ae243`) · contrat sur `retire_le` (`e284360`, `096f102`) · adoption
  depuis le cloud (`907eaeb`, `78b61b3`) · la rubrique lit le registre (`3f64a58`, `8daa282`) · le
  mandant naît dans l'app (`e926a53`) · tout le registre des liens monte au cloud (`9df21b3`) ·
  purge des provisoires (`126ab08`) · sonde C.9-couple (`033e946`).
- **Recherche** : passage en acquéreur (`d7a3586`) · sonde du carnet (`fb6abbd`) ·
  26bis-RECHERCHES (`230ce98`) · `recherche_divergente` corrigée (`3f0c0b1`) · C.3, C.1', fusion
  des critères, archive chez nous, nom figé.
- **Transaction et mandat** : écriture au clic (C.4, 25/08) · modifier les trois genres (3.1,
  3.2) · contrat vidé (3.3) · supprimer un compromis (3.4) · miroir aligné (`6bd4def`) · journal
  des suppressions (`b376d8b`, `bdf5d87`) · étape D (`b45f36a`) · C.13-a/b (`7fc43c7`, `ce57749`)
  · mandants depuis nos liens (`7808e56`) · montant retiré (`308fb70`).
- **Documents et photos** : photo gardée sur le serveur (`c95cb9b`) · photo retirée marquée
  (`4eeb446`) · G.10 à G.17, coffre public et vitrine (`4f65ee9`) · socle « chez nous d'abord »
  dormant (`7428303`, `db5c38c`, `ec838b2`) · suivi des signatures (`60cfe84`) · frein des appels
  (`7143a1a`) · rattrapage du soir par lots de 2 500 (`57b66d5`).

---

## §7. NON MESURÉ

- Le comportement réel des écrans : « Annonce en création » en échec, le bouton Désarchiver,
  les écrans vus avec un compte commercial (droits lus, jamais testés à l'écran).
- Le scénario « Hektor répond vide », non rejoué.
- La version du worker qui tourne réellement ; la valeur de `VITE_RUBRIQUE_CONTACT_REGISTRE` sur
  Vercel.
- La résurrection réelle d'un contact supprimé (aucune suppression depuis le 23/09).
- Les recherches créées dans Hektor encore invisibles (il faudrait lire chez Hektor).
- La cause des 2 recherches disparues et des 27 clôtures absentes de `app_mandat`.
- Si `mandat_corps_recopie` tourne chaque nuit ; la fréquence d'un geste fait pendant le run.
- Les « 350 photos retirées » et « 33 photos principales différentes » (1 cas confirmé sur 7).
- Le volume réel de l'agenda Hektor ; une restauration Veeam ; les sauvegardes Supabase.
- Archiver ou restaurer un contact ; liens acquéreurs et `mandantsVoulus` (Q2 et Q4 du 30/09).
