# CHANTIER GED — LA GESTION ÉLECTRONIQUE DES DOCUMENTS (ouvert le 06/11/2026)

> Demande de Frédéric (06/11, avant le lot 4 du chantier partenaires) : *« mon projet a bien un système de gestion de
> documents mais il devrait être plus perfectionné, permettant aux différents outils de trouver facilement un document ou
> une famille de documents, comme les documents de copropriété, les mandats, les justificatifs du mandat, un avenant, les
> documents spécifiques aux fiches métier, les documents de transactions (offres, compromis…). Il faut améliorer
> considérablement l'outil d'ajout de documents dans l'app : ajout multiple, choix du type de document avec proposition
> automatique modifiable. J'ai besoin d'un chantier GED. »*
>
> Méthode : audit → explication (« ce que ça pourrait casser ») → « vas-y » → code additif derrière un interrupteur →
> contrôle → documents. **Ce §1 est l'audit ; rien n'est codé.**

## 0. LE PLAN DU CHANTIER — L'ÉTAT AU PRÉSENT (réécrit le 12/11 soir ; se RÉÉCRIT, ne s'empile pas)
> Le détail et le pourquoi de chaque morceau sont au §12. Ici : où on en est, et ce qui reste, dans l'ordre.
> Cadre (§12.1) : outil d'ajout de documents DANS L'APP seulement, essayé par Frédéric seul (interrupteurs à trois crans
> réglés sur « admin »), run de nuit et worker non touchés, chaque document part chez Hektor par le chemin existant.

**Ordre décidé par Frédéric le 12/11 soir : finir TOUT le code et les essais, PUIS l'habillage (§12.12).**

| morceau | contenu | état |
|---|---|---|
| 1 | la base (types, classements, interrupteurs) | ✅ en production (§12.6) |
| 2 | la fenêtre de dépôt (plusieurs fichiers, type, nom, visibilité) | ✅ en production, cran admin (§12.7) |
| 3 | « Reçu / Manque » par moment du dossier | ✅ en production, cran admin (§12.8) |
| 4 | l'IA classe avant l'envoi (type, nom, découpage) | ✅ en production, cran admin (§12.9) |
| 5 | les 13 règles sans IA (« À regarder ») | ✅ en production, cran admin (§12.10) |
| 6 lot 1 | lecture : état des risques, DPE, dossier de diagnostics | ✅ en production (`c631a6d`), **essai réel fait le 12/11** (§12.14) |
| 6 lot 2 | lecture : **taxe foncière, titre de propriété, fiche synthétique, charges de copro** — avec les NOMS | ✅ en production (`0466c7c`), **essai réel fait le 12/11** : 5/5 lus, 0 fuite, 0 doublon (§12.14) ; affichage après rechargement (« Lu par l'IA ») en production (`49dab5d`), vu sur 62774 |
| 6 lot 3 | lecture : offre d'achat, compromis, PV d'AG | ✅ en production (`6b26c07`), **essai réel fait le 12/11** : 3/3 lus, compromis texte + pages 44-45 en image, 0 fuite (§12.15) |
| 6 lot 4 | lecture : mandat déposé à la main, avenant, fin de mandat, acte, annulation, facture, petits diagnostics, assainissement, surfaces, règlement | ✅ **écrit et contrôlé le 13/11** (80 + 49 VERT, banc 64/64, 0 fuite), patch d'étiquette posé (14/14 « lue »), poussé (`7c4e3fb`) ; **essai réel fait le 13/11 sur 63331** : 8/8 envoyés et lus, 0 fuite ; ⚠ « Note honoraires » classée « notes internes » par la règle du nom (§12.16) |
| 7 | comparateurs et règles avec lecture (titre ↔ mandants, taxe ↔ fiche, copro…) | ✅ **écrit et poussé le 13/11** : 7a (`81be8ad`, socle + justificatifs et diagnostics du bien), 7b (`973592c`, le mandat), 7c (les transactions, résolveur) ; 84 VERT ; **pas encore regardé sur un vrai bien** (§12.17) |
| 8 | propositions (« remplir », un clic par case) | ✅ **écrit, posé et poussé le 13/11** (`9320c02`, 27 VERT, patch m8 6/6), interrupteur `ged_remplir` **allumé en admin le 13/11 à 14:42** ; **épreuve d'écriture sur 63331 faite dans les deux sens, prouvée en base** (Hektor accepte `dpe_date`, date d'ERP, nb de lots, quote-part ; rien d'autre ne bouge ; copropriété reste OUI) — §12.18 |
| 9 | pièces des personnes (identité — le justificatif le plus déposé —, état civil, financement) | ✅ **9a** (identité, registre à part) en production et éprouvé ; **9b** (P4-P6) regardé en réel le 14/11 ; **9c** (remplir la fiche d'un mandant) corrigé (les deux numéros) et prouvé le 16/11 ; **9d-1** (financement, P7-P8) lecture éprouvée, ⚠ P7/P8 PAS prouvées en réel (aucun bien d'essai n'a de compromis vivant) ; **9d-2** (état civil, P9-P10) éprouvé le 16/11 (§12.19) |
| 10 | mesure (vrai / faux / déjà su) | ✅ en production le 16/11 (`d4ca8fe`, table `app_ged_jugement`) ; ⏰ **la mesure court jusqu'au 30/11**, compte rendu par `supabase/requete_mesure_ged_m10_2026-11-16.sql` ; 63331, 62774, 61398 ne se jugent pas (§12.20) |
| habillage | la maquette RETRAVAILLÉE (toile https://claude.ai/artifact/S16jkpfnqtPF83xvUdkNtm) | ✅ **COMPLET le 17/11** : H1 le bloc « Le dossier », H2 la fenêtre de dépôt, H3 l'après-envoi (« La fiche du bien », « Voir le document » ; « Voir la preuve » NON fait, décision), H4 le panneau photo du téléphone (viseur dans l'app NON fait, décision) — tous vus en production (§12.21) |
| 10a | le compromis lu → SA transaction (date d'acte prévue, séquestre) | ⛔ **REMPLACÉ le 17/11 par 10c** : la date d'acte et le séquestre s'écrivaient « chez nous seulement », alors que ce sont des champs que Hektor connaît (§12.22, §12.28) |
| 10b | les conditions suspensives du compromis → SA transaction | ✅ en ligne le 17/11 (`cf09297`) ; ses cartes sont reprises par 10c (§12.23) |
| 10c | « Ce que dit le compromis » : la fenêtre de validation, champ par champ, chacun par SON chemin | ✅ **EN LIGNE le 17/11** (`50164c1` → `2250250`, « Oui vas y » ; Vercel et Render servent `2250250`) ; **vu en production sur 18849** : date de l'acte à trancher (correction proposée), séquestre « pas chez Hektor », conditions générales à part -- fenêtre refermée SANS enregistrer ; ⚠ l'envoi direct n'est pas encore éprouvé en réel (§12.28) |
| lecture | « pas ce type » refusé au hasard : la cause (le CODE du type seul dans l'en-tête) prouvée au banc | ✅ **EN PRODUCTION le 18/11** (`9d5a6fd`, Render) : l'en-tête donne le libellé du catalogue ; banc par le vrai code 95/95, **essai réel vert sur 63331** (la fiche synthétique refusée la veille sort « lu ») (§12.34, §12.35) |
| recours | « C'est bien ce type : garder la lecture » sur une lecture refusée | ✅ **EN PRODUCTION le 18/11** (`5b93490`, patch posé 4/4, répétition 8/8, Vercel) ; ⚠ pas vu sur un vrai cas : il n'existe plus de lecture refusée (§12.36) |

**Reste, au 20/11** (réécrit ; le détail des lots A à G est aux §12.41-12.56, tous ÉPROUVÉS EN RÉEL) :
- **le visuel** : maquette V2 du 18/11 (`notice/AUDIT_GRAPHIQUE_GED_2026-11-18.md` §7, « la liste DEVIENT le dossier »)
  livrée, PAS codée, son avis attendu, avec ses points à trancher (§5 de l'audit ; garder la mesure après le 30/11) ;
- **le dossier « cran on »** (§12.37) : DPA (geste de Frédéric), registre des traitements, analyse d'impact, mention au
  mandat, et DEUX DÉCISIONS : une durée de conservation des lectures, un chemin d'effacement pour une personne ;
- ⏰ **la mesure** court jusqu'au 30/11 : au 20/11, **8 jugements** (7 vrais, 1 faux), lectures réelles sur 2 biens
  seulement (59541, 62850) -- elle ne dira presque rien sans usage réel ;
- **essais réels qui attendent une cible** : l'envoi direct de 10c, « Ce que dit l'offre » sur une offre vivante, P6 à
  l'écran ; P7/P8 mis de côté le 17/11 ;
- **options non tranchées** : règle de nommage commune (§12.26), masquer l'IBAN d'un compromis (§12.27), les types « hors
  plan » du §12.41 (livret de famille, facture d'honoraires, syndic, fonds de travaux, règlement, adresse et régime) ;
- ⚠ **un interrupteur a bougé hors de ce chantier** : `ged_depot_multiple = 'on'` depuis le 18/11 21:26, posé par la
  session Étape 4 chap. 6 (`ffd7483`, §85 de sa note) -- le DÉPÔT est ouvert aux négociateurs, pas la LECTURE par l'IA
  (`ged_lecture_ia`, `ged_lecture_personnes`, `ged_remplir`, `ged_propositions`, `ged_recu_manque` restent « admin »).
  Au 20/11 : aucun dépôt par l'app depuis.
✅ Toutes les pièces d'essai sont SUPPRIMÉES (63331, 63147 le 18/11 ; 63331, 63330 le 20/11, §12.58) ; leurs lectures
restent en base, invisibles. Les fiches d'essai gardent les valeurs écrites par les preuves.

**Avant les négociateurs (cran « on »)** : le contrat de sous-traitance (DPA) avec le fournisseur d'IA — décision du
12/11 : « à la fin du dev » —, l'analyse d'impact, le registre des traitements (avec les NOMS lus depuis le lot 2), la
clause au mandat.
**Fermé, à ne pas re-proposer** : lire les ~193 000 documents déjà en base (le stock) ; le RIB n'est JAMAIS lu.

## 1. AUDIT (06/11) — ce que la base contient

- **`app_console_document`** : **193 392 documents** sur 25 987 annonces (médiane 4 par bien, 10 % en ont plus de 18,
  maximum 120). 22 116 sur les 4 891 biens vivants.
- ⛔ **AUCUN CLASSEMENT** : `document_type` vaut « document » pour **193 391** d'entre eux (un seul « Mandat »). Le seul
  repère est le **nom du fichier**. `metadata_json` porte des clés techniques (archive, signature, modelo, ImmoSign), pas
  de type.
- **Rattachement** : 100 % à une annonce (`hektor_annonce_id` / `app_dossier_id`). **Aucun** document rattaché à un
  contact, une affaire (offre, compromis, vente), un mandat en tant que tel, un partenaire.
- **Origine** : Hektor pour la quasi-totalité (console privée 189 243, partagée 2 178, modèles 1 150, ImmoSign 778 + 36
  signés) ; **ajoutés depuis l'app : 7** (19/10 → 05/11 : attestations de propriété, CI vendeurs, avenant, mandat…).
- **Stockage** : serveur OVH = tout ; coffre Supabase (`hektor-console-documents`) = copie des biens vivants
  (`cloud_available` 24 856, `local_only` 168 536). Le coffre REFUSE définitivement les types hors liste (ex. `.odt`) et
  > 50 Mo (mémoire « coffre-refus-de-type »).
- **Formats** : PDF 160 618, JPEG 24 973, PNG 5 636, Excel/Word/ODT ~1 900.
- **Signature** : `app_signature_request` = 1 demande (mandat, Youtrust).
- **Hektor ne donne aucun type** : son API v2 ne parle pas des documents ; ils viennent de sa console, sans catégorie.

### 1.1 Ce que les NOMS permettent déjà de reconnaître (estimation grossière, règles sur le nom)

Premier passage (règles à espaces) : mandat 14 466 · avenant 7 431 · diagnostics 13 608 · offre 9 641 · compromis
6 447 · urbanisme/plans 16 130 (règle trop large) · factures/devis 7 707 · identité/justificatifs 5 922 · visite 3 115 ·
estimation 2 401 · financement 2 263 · copropriété 772 · location 695 · propriété 221 · acte de vente 48 · images sans
nom parlant 20 650 · **non reconnu 81 875 (42 %)**.

⚠ Une bonne partie du « non reconnu » se reconnaît avec des règles tenant compte des `_` : `avis_de_valeur_marchande`
(1 836), `titre_de_propriete` / `tp_` (~2 300), `taxe_fonciere` / `tf_` / `avis_de_taxes_foncieres` (~1 850),
`informationsparcelles` (1 621, cadastre), `accord_honoraires` (469), `diags_` / `diag_` (~800), `bv_` (296, bon de
visite), `courrier_d_annulation` (256), `spanc` (183), `charges` (145)… ⇒ **une proposition automatique par le nom est
réaliste**, à faire confirmer ou corriger par l'humain.

## 2. AUDIT — le code (inventaire du 06/11, chemins vérifiés par sondage)

- **Une seule table, une seule accroche** : `app_console_document`, par annonce (`app_dossier_id`, `hektor_annonce_id`).
  Mandat et affaire passent par l'annonce ; aucun document de contact, d'affaire, de partenaire en tant qu'objet.
- **L'outil d'ajout** : un seul composant, `ConsoleDocumentsPanel` (`App.tsx` ~11644, formulaire ~11948-12020), monté sur
  la fiche annonce seulement (cockpit, fiche classique, téléphone).
  - **un fichier à la fois** (`files?.[0]`, pas de `multiple`) ; un bouton « Caméra » ;
  - « Libellé » libre (= nom du fichier chez Hektor), « Visibilité » privé/public, « Type » en liste figée : Autre, DPE,
    Mandat, Diagnostic, Plan, Facture, Photo, Taxe foncière, Bon de visite, Pièce d'identité ;
  - envoi : `createUploadDocumentToHektorJob` (`api.ts` ~9018) → coffre `temp/uploads/…` → ligne optimiste
    (`app_console_creer_document_optimistic`, `source='app'`) → travail `upload_document_to_hektor` → serveur + coffre
    puis Hektor.
- ⛔ **LE TYPE CHOISI EST PERDU** — prouvé en base le 06/11 : les deux « Plan cadastral » envoyés avec le type « Plan » le
  30/10 sont aujourd'hui `document_type = 'document'`, `source = hektor_console_uploaded_private`. Cause : la synchro
  (`extractDocumentEntries`, `document_type: "document"` en dur ; `upsertConsoleDocuments` le réécrit) re-clé la ligne
  et écrase le type. Et le type n'est jamais envoyé à Hektor (qui n'en a pas). ⇒ **un classement ne peut pas vivre dans
  `document_type` tant que la synchro le réécrit.** Mesure aussi : sur 12 ajouts récents, 10 sans type (« Autre »).
- **La lecture** : une fonction, `loadConsoleDocuments` (par `app_dossier_id`, 300 lignes max). Ouvrir = URL signée, et
  seulement si `cloud_available`.
- **« Trouver un document » aujourd'hui = des expressions régulières sur le NOM, différentes d'un écran à l'autre** :
  `docTypeOf` (cockpit v21), `/mandat/i` (suivi de signature), `/avenant/i` (3 endroits), « Signé à la main »
  `/mandat|avenant/i`, registre des transactions `/compromis|promesse|offre|acte|authentique/i`, fiche notaire « pièces
  du dossier » (11 règles), backend « Avis de valeur% ». **Le pré-état daté n'est cherché nulle part.**
- **Documents générés par l'app** : avis de valeur (`document_type` « Avis de valeur »), mandat / avenant (« Mandat »,
  métadonnées `genere_par`, `remplace_document_id`…), plan cadastral (« Plan ») ; signatures ImmoSign / Youtrust rangées
  sous `signed/` et `proofs/` (décrites dans `metadata_json`). Les **bons de visite** ne sont pas des documents (impression
  navigateur).
- Valeurs codées : `source` (7), `storage_status` (7), `visibility` (3). `backend/` et `phase2/` ne classent rien.

## 3. Les décisions déjà prises qui touchent les documents

- ⑦-9 (19/10) : **renommer un document = fermé** ; le champ « Libellé » existe à l'envoi (nom du fichier chez Hektor).
- Domaine des documents (20-21/10) : identifiant = sha1 de l'URL complète ; correctif « re-clé par le chemin » posé ;
  **pas de remède sur la clé** (décision du 21/10).
- Un document déposé chez Hektor ne fait PAS bouger la date de l'annonce (≠ photo) : la détection passe par l'empreinte
  de la page documents (`app_console_document_fingerprint`), mécanisme « installé à moitié ».
- Partenaires (D2, 04/11) : rien ne part chez Hektor pour les métiers — à rappeler pour les documents de métier.

## 4. LE DÉCOUPAGE PROPOSÉ (06/11) — rien n'est décidé

- **GED-1 — la nomenclature** : familles et types de documents (mandat et ses justificatifs, avenant, bien et
  diagnostics, copropriété, transaction : offre / compromis / acte / financement, estimation, visite, urbanisme et
  cadastre, documents de métier, identité, factures, autre…), **chiffrée sur les 193 392 documents** et validée par
  Frédéric AVANT tout écran (règle : raisonnement métier chiffré avant le graphisme).
- **GED-2 — le classement, rangé à part** : une table à nous (le type, son origine auto/humain, qui, quand) que la synchro
  ne touche JAMAIS (« une saisie ne se perd jamais ») ; et les rattachements d'un document à un mandat, une affaire, un
  contact, un partenaire (pas seulement l'annonce).
- **GED-3 — le classement automatique du stock** : des règles sur le nom proposent un type pour les 193 392 ; mesure de
  justesse sur un échantillon ; tout reste corrigeable.
- **GED-4 — l'outil d'ajout** : plusieurs fichiers d'un coup (glisser-déposer), type PROPOSÉ par le nom et modifiable,
  rattachement (bien, mandat, affaire, contact, partenaire), libellé ; sur la fiche annonce, puis contact, affaire,
  fiche métier.
- **GED-5 — trouver** : une fonction unique « les documents de telle famille / tel type pour tel objet », utilisée par
  tous les écrans (pièces du notaire, registre des transactions, suivi de signature, copropriété du syndic…) à la place
  des expressions régulières dispersées.
- **GED-6 — les écrans de consultation** : documents groupés par famille, filtres, recherche ; au téléphone aussi.

⚠ Ce que ça pourrait casser : la synchro des documents (on n'y touche pas : le classement vit à côté) ; les écrans qui
cherchent par le nom (ils gardent leur repli tant que GED-5 n'est pas branché) ; Hektor (rien ne lui est envoyé de plus).

## 5. LE CONSEIL (06/11, « donne-moi la meilleure méthode… et analyse la signature pour ne rien casser »)

### 5.1 La méthode
1. **Le fichier ne bouge pas ; sa FICHE vit à côté.** Le fichier, son identité (`hektor_document_id`, chemin, sha256) et
   sa synchro avec Hektor restent tels quels. Le classement (famille, type, rattachements, dates, statut, origine) va dans
   des tables à nous que la synchro ne touche jamais.
2. **Une nomenclature unique, courte, en base** (famille → type, codes stables, libellés modifiables), lue par tous les
   écrans — plus aucune liste ni expression régulière en dur.
3. **Un document peut concerner plusieurs objets** : bien, mandat, avenant → son mandat, affaire (offre, compromis, acte),
   contact, partenaire.
4. **Classer à l'entrée, l'humain confirme** : type proposé par le nom (plus tard par le contenu), origine tracée
   (automatique / humain / généré par l'app), l'humain gagne toujours.
5. **Cycle de vie** : versions (« remplace », existe déjà pour le mandat), statut, document signé = immuable.
6. **Dates qui comptent** : validité des diagnostics (DPE 10 ans…), pré-état daté, pièce d'identité → alertes.
7. **Complétude** : pour chaque étape (mandat, compromis, vente), la liste des pièces attendues et celles qui manquent.
8. **Une seule porte pour trouver** : « les documents de telle famille / tel type pour tel objet ».

### 5.2 La sécurité
- Mesuré le 06/11 : coffre `hektor-console-documents` PRIVÉ (50 Mo), lecture limitée au périmètre du compte (règle
  `app_console_document_select_scope` + règle du coffre), dépôt seulement dans `temp/`. **C'est sain ; à garder.**
- À ajouter : une **sensibilité** par type (identité, RIB, avis d'imposition = données personnelles) → accès plus
  restreint, durée de conservation (RGPD), jamais en pièce jointe sans le vouloir ; le **journal des consultations**
  (`last_accessed_at` existe, à compléter) ; le **contrôle d'intégrité** des signés (sha256 vérifié au rapatriement et de
  temps en temps) ; à l'entrée, **doublons** (sha256) et **formats refusés** dits tout de suite (ex. `.odt`).

### 5.3 Ne pas casser la signature électronique (chantier A.2 Youtrust, autre session, essai jusqu'au ~09/11)
- **Sa colonne vertébrale** : l'état de signature vit dans `metadata_json.signature` du document (`provider`
  immosign / youtrust / manuscrite, `procedure_id`, `provider_request_id`), écrit par DEUX écrivains (Hektor/ImmoSign,
  Youtrust) avec la règle R1 (un écrivain ne touche que les siens). `app_signature_request.app_console_document_id`
  pointe sur la ligne du document.
- **Règles pour la GED** : ne JAMAIS écrire `metadata_json` ni les colonnes d'identité / de stockage de
  `app_console_document` ; la GED LIT l'état de signature, ne l'écrit pas ; un document signé ou en cours de signature ne
  peut être ni supprimé ni remplacé depuis la GED ; les mandats générés par l'app (`genere_par`, `document_type`
  « Mandat ») sont classés d'office « mandat » / « avenant ».
- **Les lecteurs par le nom** (`/mandat/` du suivi de signature, `/avenant/` de l'envoi Youtrust, « Signé à la main »,
  registre des transactions, pièces du notaire) gardent leur repli jusqu'à ce que GED-5 les remplace UN PAR UN, chacun
  avec son essai.
- **Calendrier** : l'autre session modifie en ce moment les mêmes fichiers (App.tsx, worker, panneau des documents) ;
  tout ce qui touche l'écran des documents (GED-4, GED-6) attend la fin de ses lots ou se fait en accord avec elle. GED-1
  à GED-3 (nomenclature, fiche à part, classement du stock) ne touchent ni l'écran ni la signature.

### 5.3 bis La réponse de la session signature (06/11) — ce qu'elle touche, à ne pas piétiner
- Règles GED **acceptées**. Elle demande de garder GED-4 APRÈS ses lots, ou de la prévenir avant.
- **Commité (`3c32daa`, worker, non actif)** : `persistConsoleDocumentFile` préserve toute ligne qui porte
  `metadata_json.signed_document` ; `handlePrepareDocumentCloud` monte le SIGNÉ d'un document signé (`monterSigneAuCoffre`) ;
  le marquage « absent chez Hektor » épargne une ligne engagée en signature (`signatureSuivieOuSigne`) ; le dépôt différé
  (`completerEnvoiDocumentDiffere`) a un anti-doublon ; interrupteur `app_setting` `mandat_nait_chez_nous` (absent = éteint).
- **En cours, non commité, dans `App.tsx`** : `ConsoleDocumentsPanel` affiche l'état du dépôt Hektor
  (`mentionDepotHektor`, `envoi_hektor_statut`) ; le cockpit lit `src/lib/etatSignatureMandat.ts` (et non plus le 1er
  document `/mandat/`) ; l'éditeur relit `mandat_nait_chez_nous`.
- **À venir dans `ConsoleDocumentsPanel`** : un bouton « Signature » unique (Youtrust / Hektor / manuscrite), le suivi par
  signataire (lecture de `app_signature_request`), l'ouverture des preuves (règle de lecture du coffre élargie à
  `proofs/` et `immosign/`).
- ⛔ **Sa règle pour la GED** : un document signé garde l'ORIGINAL à côté (même ligne, `storage_path` basculé vers
  `…/signed/`) ; ne jamais remonter `local_archive_path` (l'original) sur `storage_path`.

### 5.4 L'ordre recommandé
GED-1 nomenclature (validée par Frédéric) → GED-2 fiche à part + GED-3 classement du stock (base seule, rien à l'écran)
→ GED-5 la porte « trouver », d'abord pour les besoins neufs (copropriété du syndic, pré-état daté), puis à la place des
anciennes règles → GED-4 l'outil d'ajout (après les lots signature) → complétude et dates d'expiration → plus tard :
lien de dépôt pour le client, lecture du contenu des PDF, bons de visite rangés comme documents.

## 6. GED-1 — LA NOMENCLATURE, CHIFFRÉE (06/11 après-midi) — ⏳ EN ATTENTE DE LA DÉCISION DE FRÉDÉRIC

> Audit limité aux **documents** (`app_console_document`) : objets et gestes des autres familles non mesurés ici.
> **Rien n'a été écrit** : ni base, ni Hektor, ni coffre, ni écran. Mesure rejouable :
> `python phase2/checks/ged1_mesure_nomenclature.py` (lecture seule, `--reste` pour les noms non reconnus).

### 6.1 La re-mesure (le §1 tient)
- 193 392 documents, 25 987 annonces ; `document_type` ≠ « document » : **toujours 1** ; `source = 'app'` : 7 ; dernier
  document créé le 05/11 à 21:17. Coffre : 24 856 documents `cloud_available` sur **5 101 biens** (= ce que l'app sait ouvrir).
- Sources : console privée 189 243 · partagée 2 178 · modèles Hektor 1 150 (dont 985 « Bon de Visite Groupe GTI ») ·
  ImmoSign 778 (dont 642 « Mandat (avec saisie du numéro) (vente) ») · signés ImmoSign 36 · app 7.

### 6.2 La méthode
- Le nom est mis à plat (accents, majuscules, `_`). ⚠ **Hektor coupe les lettres accentuées** : « foncie_re », « proprie_te »,
  « e_tat », « pi_ce » — la mise à plat les recolle, sinon 1 nom sur 20 échappait.
- **Règles ordonnées, la première qui gagne** (« offre de prêt » n'est pas une offre, « avenant au mandat » n'est pas un
  mandat, un nom qui cite deux diagnostics est un dossier de diagnostics). Chaque règle a une **force** : *sûr* (mot clair) ou
  *probable* (abréviation, mot ambigu → à faire confirmer par l'humain). Les noms vides de sens sont *muets*.
- **Contrôle de justesse par le contenu** : ~70 PDF tirés au hasard ouverts EN LECTURE sur le disque du serveur. Types
  *sûrs* : **33 sur 34** PDF lisibles conformes. Types *probables* : 2 règles fausses trouvées et corrigées (ci-dessous).
- ⭐ **Ce que le contenu a appris, et que le nom ne disait pas** :
  `odp_…` = **offre de prêt** (CA, CIC, CASDEN), pas une offre d'achat · `est_N` = **facture d'honoraires d'estimation**,
  pas un avis de valeur · `rapport_<n>_<horodatage>` = **dossier d'estimation** (outil externe) · `copie_aae_promesse…` =
  promesse signée chez le notaire · `AAAA_MM_JJ_facture_<nom>` = facture d'honoraires GTI (2015-2017) ·
  `accord_honoraires_N` = le **courriel de validation** d'une baisse d'honoraires · `adp_…` = attestation de demande de prêt ·
  `lp_…` = lettre au client · `annulation_<nom>` = courriel d'**annulation de vente** (pas de mandat) · `sci_<nom>_dossier` =
  **dossier de diagnostics** (pas un Kbis) · `d1`…`d9` = la numérotation des diagnostiqueurs (d1 plomb, d2 amiante,
  d4 gaz, d5 électricité, d6 risques, d7 DPE, d9 attestation sur l'honneur).

### 6.3 Le résultat global
**Sûr 145 305 (75,1 %) · probable 21 174 (10,9 %) · muet 10 574 (5,5 %) · non reconnu 16 339 (8,4 %)** ⇒ **86 %** des
documents recevraient une proposition de type par leur seul nom.

### 6.4 La nomenclature proposée — 14 familles, 59 types (+ partenaires, + non classé)
Colonnes : code (le contrat, stable) · libellé (modifiable) · nombre · dont *probable* · biens où il s'ouvre dans l'app
(sur 5 101) · rattachement naturel (pour GED-2). ⚠ = sensible (données personnelles).

| famille | code | libellé | nb | prob. | biens app | rattachement |
|---|---|---|---:|---:|---:|---|
| **mandat** 31 769 | `mandat.vente` | Mandat de vente | 20 117 | | 921 (18 %) | mandat |
| | `mandat.avenant` | Avenant au mandat (baisse de prix…) | 8 308 | | 264 | mandat |
| | `mandat.fin` | Fin de mandat (résiliation, dénonciation) | 1 630 | | 23 | mandat |
| | `mandat.honoraires` | Accord / baisse d'honoraires | 1 113 | | 80 | mandat |
| | `mandat.recherche` | Mandat de recherche | 601 | | 15 | mandat (acquéreur) |
| **justificatifs** du mandat 30 254 | `justif.titre` | Titre / origine de propriété (acte, donation, succession) | 13 723 | 3 501 | 722 (14 %) | bien + propriétaire |
| | `justif.identite` ⚠ | Pièce d'identité | 8 591 | | 577 | contact |
| | `justif.taxe` | Taxe foncière / impôts locaux | 5 336 | | 477 | bien |
| | `justif.pouvoir` | Pouvoir / procuration | 944 | | 13 | contact |
| | `justif.societe` | Société venderesse (Kbis, statuts) | 880 | 408 | 77 | contact |
| | `justif.etat_civil` ⚠ | État civil / capacité (livret, mariage, décès, tutelle) | 745 | | 58 | contact |
| | `justif.rib` ⚠ | RIB | 35 | | 8 | contact |
| **transaction** 27 925 | `transaction.offre` | Offre d'achat (et sa réponse) | 10 948 | | 242 | affaire |
| | `transaction.avant_contrat` | Compromis / promesse de vente | 7 896 | | 237 | affaire |
| | `transaction.financement` ⚠ | Financement (offre / accord de prêt, simulation) | 4 563 | | 81 | affaire + acquéreur |
| | `transaction.acte` | Acte de vente / attestation de vente | 1 346 | | 93 | affaire |
| | `transaction.renseignements` | Fiche de renseignements acquéreurs / vendeurs | 1 330 | 1 330 | 86 | affaire |
| | `transaction.notaire` | Dossier / courrier du notaire | 766 | 766 | 30 | affaire + notaire |
| | `transaction.annulation` | Annulation d'une vente / désistement | 458 | 409 | 9 | affaire |
| | `transaction.sru` | Notification SRU / rétractation | 386 | | 10 | affaire |
| | `transaction.mobilier` | Liste du mobilier | 229 | 229 | 11 | affaire |
| | `transaction.sequestre` | Séquestre / dépôt de garantie | 3 | | 0 | affaire |
| **visite** 4 411 | `visite.bon` | Bon de visite | 4 388 | | 281 | bien + acquéreur |
| | `visite.compte_rendu` | Compte rendu de visite | 23 | | 1 | bien |
| **estimation** 5 734 | `estimation.avis` | Avis de valeur / dossier d'estimation | 5 734 | | 2 866 (56 %) | bien |
| **diagnostics** 21 514 | `diag.dpe` | DPE | 6 231 | | 318 | bien |
| | `diag.dossier` | Dossier de diagnostics (DDT) / autre | 5 792 | 68 | 362 | bien |
| | `diag.erp` | État des risques (ERP, ERRIAL, Géorisques) | 2 919 | | 414 | bien |
| | `diag.assainissement` | Assainissement (SPANC, raccordement) | 1 465 | | 103 | bien |
| | `diag.amiante` | Amiante | 1 254 | | 80 | bien |
| | `diag.surface` | Surface (Carrez, Boutin) | 1 047 | 1 047 | 135 | bien |
| | `diag.electricite` | Électricité | 1 021 | | 87 | bien |
| | `diag.gaz` | Gaz | 657 | | 38 | bien |
| | `diag.plomb` | Plomb (CREP) | 596 | | 40 | bien |
| | `diag.audit` | Audit énergétique | 453 | | 134 | bien |
| | `diag.termites` | Termites / parasites / mérule | 79 | | 4 | bien |
| **copropriété** 5 074 | `copro.pv_ag` | PV / convocation d'assemblée générale | 1 928 | 422 | 83 | bien (+ syndic) |
| | `copro.arrete_charges` | Arrêté / décompte de charges (dépenses réelles) | 1 202 | 770 | 117 | bien (+ syndic) |
| | `copro.appel_fonds` | Appels de fonds / provisions / budget prévisionnel | 913 | 14 | 108 | bien (+ syndic) |
| | `copro.reglement` | Règlement de copropriété / état descriptif | 472 | | 50 | bien (+ syndic) |
| | `copro.autre` | Autre document de copropriété | 284 | 284 | 27 | bien (+ syndic) |
| | `copro.carnet` | Carnet d'entretien / fiche synthétique | 249 | | 41 | bien (+ syndic) |
| | `copro.dtg` | DTG / plan pluriannuel de travaux | 23 | | 7 | bien (+ syndic) |
| | `copro.etat_date` | Pré-état daté / état daté | **3** | | 1 | bien + affaire |
| **urbanisme** et terrain 20 597 | `urba.cadastre` | Cadastre / parcelles | 15 693 | | 2 451 (48 %) | bien |
| | `urba.permis` | Permis / déclaration de travaux / conformité | 1 710 | | 77 | bien |
| | `urba.certificat` | Certificat d'urbanisme / PLU / lotissement | 1 586 | | 96 | bien |
| | `urba.bornage` | Bornage / division / servitudes | 1 471 | | 127 | bien |
| | `urba.etude_sol` | Étude de sol (G1, G2) | 137 | | 11 | bien |
| **bien** 4 362 | `bien.plans` | Plans / vues du bien | 2 876 | 2 876 | 269 | bien |
| | `bien.cles` | Clés (photo, remise) | 593 | 593 | 12 | bien |
| | `bien.entretien` | Entretien / énergie (chaudière, ramonage, factures) | 501 | 501 | 43 | bien |
| | `bien.descriptif` | Descriptif / fiche commerciale | 392 | 392 | 63 | bien |
| **facturation** 10 302 | `facture.honoraires` | Facture / note d'honoraires GTI | 7 812 | | 1 341 | affaire / mandat |
| | `facture.autre` | Autre facture | 1 766 | 1 766 | 109 | bien |
| | `facture.devis` | Devis / travaux | 724 | 724 | 46 | bien |
| **location** 794 | `location.bail` | Bail / état des lieux / quittance / gérance | 794 | | 47 | bien |
| **entreprise** 165 | `entreprise.comptes` | Bilans / comptes (fonds de commerce) | 165 | 165 | 4 | bien |
| **courrier** 2 138 | `courrier` | Courrier / lettre / accusé de réception | 2 138 | 2 138 | 59 | selon le cas |
| **interne** 1 542 | `interne.notes` | Notes / suivi interne | 1 542 | 1 542 | 275 | bien |
| **partenaires** 0 | `partenaire.convention` · `.assurance` · `.certification` · `.societe` · `.tarifs` · `.autre` | (proposés) | **0** | | | partenaire |
| **non classé** 26 913 | `muet` | Nom muet (scan, photo, « sans titre ») | 10 574 | | 693 | — |
| | `reste` | Nom parlant non reconnu | 16 339 | | 846 | — |

- **Les documents générés par l'app** se classent d'office par leur ORIGINE, pas par le nom : avis de valeur →
  `estimation.avis`, mandat → `mandat.vente`, avenant → `mandat.avenant`, plan cadastral → `urba.cadastre`.
- **Le non reconnu (16 339)** : 5 913 « un nom propre + des chiffres » (`dupont_3.pdf`), 1 135 « attestation » sans
  précision, 549 contrat / demande / autorisation, 409 « maison / terrain + lieu », 8 067 divers. Ni la règle ni le nom
  n'y peuvent rien : c'est l'humain (ou, plus tard, la lecture du contenu).
- **Partenaires (fiches métier) : vide aujourd'hui**, parce qu'aucun document ne peut s'accrocher à un partenaire. Seuls
  236 noms du stock évoquent une assurance, une convention ou une certification, éparpillés dans les dossiers des biens.

### 6.5 Ce que les chiffres disent (lecture métier)
- **Le besoin du syndic couvre toute la famille copropriété**, pas seulement le pré-état daté *(rectifié par Frédéric le
  06/11 : « arrêté de charges, règlement de copro, etc. »)*. Le stock existe : **4 972 documents de copropriété**, et
  **161 biens** que l'app sait ouvrir en ont au moins un (charges 108 biens, PV d'AG 83, règlement 50, carnet / fiche
  synthétique 41, DTG 7). Dans les charges, le nom distingue déjà deux choses que le métier distingue :
  **ce qui a été dépensé** (arrêté de charges 25, décompte / relevé / régularisation 288) et **ce qui est appelé**
  (appels de fonds / provisions 831, budget prévisionnel 11) ; 853 disent seulement « charges ».
  ⚠ **Seul le pré-état daté est presque absent : 3 documents** — celui-là naîtra avec l'outil d'ajout (GED-4).
- Sur les 5 101 biens dont l'app ouvre les documents (estimations comprises) : mandat de vente reconnu sur **18 %**,
  titre de propriété 14 %, DPE 6 % (+ dossier de diagnostics 7 %), cadastre 48 %, avis de valeur 56 %. Les pièces
  manquent souvent, ou dorment sous un nom muet. ⚠ La future **complétude** (§5.1-7) devra le dire sans accuser : le
  dénominateur mêle biens en estimation et biens sous mandat (non séparés ici).
- **7 812 factures d'honoraires GTI** dorment dans les dossiers des biens : ce sont des pièces de l'agence, pas du
  client → leur visibilité est une question pour GED-2.

### 6.6 Les écrans d'aujourd'hui y retrouvent-ils leurs pièces ? (préparation de GED-5)
- **Pièces du notaire** (`FicheNotaire.tsx`, 11 règles) : toutes couvertes (`justif.titre`, `diag.*`,
  `transaction.avant_contrat`, `transaction.sru`, `justif.identite`, `justif.taxe`, `mandat.vente`,
  `transaction.sequestre`, `transaction.financement`, `diag.assainissement`, `urba.cadastre`).
- **Cockpit v21** (`docTypeOf`, `App.tsx`) : avenant, mandat, diagnostic, avis, cadastre → couverts.
- **Fiche syndic** (`estDocumentCopro`) → la famille `copropriété` entière.
- **Registre des transactions** (`/compromis|promesse|offre|acte|authentique/`) → `transaction.offre / avant_contrat /
  acte`. ⚠ Aujourd'hui une **offre de prêt y passe pour une offre** ; la nomenclature les sépare → au branchement, les
  compteurs bougeront (voulu, à annoncer ce jour-là).
- **Signature** (`/mandat/`, `/avenant/`, « Signé à la main ») → `mandat.vente`, `mandat.avenant`. ⚠ `/mandat/` attrape
  aujourd'hui « avenant au mandat » ; la nomenclature les sépare.

### 6.7 Ce que ça pourrait casser ailleurs
- **Aujourd'hui, rien** : GED-1 n'a rien écrit. Seul ajout au dépôt : le script de mesure, en lecture seule (194
  lectures REST de 1 000 lignes avec la clé de service, comme les autres contrôles ; zéro appel à Hektor). Les PDF ont
  été ouverts en lecture sur le disque du serveur.
- **Demain** (quand GED-2 et GED-5 s'en serviront) : les **codes deviennent un contrat** lu par plusieurs écrans. On
  pourra changer un libellé, ajouter un type, mais **pas renommer un code** (un écran chercherait un type disparu) ;
  scinder un type obligerait à reclasser. D'où la validation maintenant.
- Les lecteurs par le nom gardent leur repli tant que GED-5 ne les remplace pas un par un ; deux changements de
  comportement sont déjà connus (offre de prêt, avenant ≠ mandat — §6.6).
- **Signature** : la nomenclature ne lit que le nom et la source ; elle n'écrit jamais `metadata_json` ; les 36 signés
  ImmoSign se classent comme leur original. Aucune table de la session signature n'est touchée → pas de message à lui
  envoyer pour GED-1 ; il sera prévenu avant GED-2.

### 6.8 À trancher par Frédéric
1. Le découpage en 14 familles (+ partenaires + non classé), dont **« justificatifs du mandat » séparés du « mandat »**.
2. **Diagnostics : un type par diagnostic (11)** — recommandé, car leurs durées de validité diffèrent et serviront aux
   alertes (§5.1-6) — ou un seul type « diagnostics » ?
3. Garder les **petits types** qui servent à chercher (pré-état daté 3, séquestre 3, DTG 23, compte rendu de visite 23,
   RIB 35), ou les fondre dans leur famille ?
4. Les familles **courrier, interne, entreprise, location** : utiles, ou fondues dans « autre » ?
5. Les **probables** (10,9 %) : en GED-3, proposés « à confirmer » (recommandé), ou pas proposés du tout ?
6. Marquer **sensibles** dès la nomenclature : identité, état civil, RIB, financement — et les factures d'honoraires ?
7. Les types **partenaires** proposés (convention, assurance, certification, Kbis, tarifs, autre) : à compléter par lui.
8. **Copropriété : scinder les charges en deux types** — `copro.arrete_charges` (arrêté, décompte, relevé,
   régularisation : les dépenses réelles) et `copro.appel_fonds` (appels de fonds, provisions, budget prévisionnel) — les
   853 « charges » sans précision restant à confirmer ? *(question ajoutée après sa remarque du 06/11)*

### 6.9 La décision de Frédéric
- ✅ **Point 8 TRANCHÉ le 06/11 : « Oui, deux types »** → `copro.arrete_charges` et `copro.appel_fonds` (le tableau
  ci-dessus est à jour ; total copropriété 5 074, les règles ont aussi appris « re_gularisation », « da_compte »,
  « bilan_charges », « charges annuelles »). Les 853 « charges » sans précision sont proposées en `copro.arrete_charges`
  *à confirmer* : sur 11 lues, 7 étaient des dépenses réelles et 4 des appels de fonds. Global après la scission :
  sûr 75,8 %, probable 10,3 %, non reconnu 16 288.
- ✅ **Points 1 à 7 TRANCHÉS le 12/11, un par un** → voir §12.3. ⚠ Le point 5 change le périmètre : **les documents
  déjà en base ne sont pas traités** (pas de classement du stock, GED-3 abandonné).

## 7. LE GAIN DE TEMPS — conseil du 06/11 (question de Frédéric : « je n'ai vu ni maquette ni gain de temps, hormis un classement »)

> Il a raison : **un classement seul ne fait gagner de temps à personne.** C'est le socle ; le temps se gagne dans les
> GESTES qu'il rend possibles. L'architecture (la fiche à part, que la synchro ne touche pas) reste la bonne ; c'est
> l'ORDRE du §5.4 qui doit changer : commencer par ce que le collaborateur fait chaque jour.

**Les volumes (mesurés le 06/11)** : au moins **8 601 documents déposés sur les 1 559 biens enregistrés depuis 12 mois**
(plancher : les biens vendus / clos sortent de `app_dossier_current`), soit ~720 par mois, médiane 5 par bien.
**12 598 fichiers identiques sont déposés sur plusieurs biens — 16 833 copies en trop** (même empreinte sha256) :
cadastres, mandats, DPE, titres, compromis, taxes foncières.

**Les gestes qui font gagner du temps, du plus rentable au moins** *(les minutes sont des ESTIMATIONS, à chronométrer
sur l'écran réel avant d'être promises)* :
1. **Déposer d'un coup** : glisser 10 fichiers, le type est proposé, l'humain ne corrige que l'erreur. Aujourd'hui :
   un fichier à la fois, libellé et type à la main. ~30 s gagnées par document × ~8 600 / an ≈ **70 h / an**.
2. **Les pièces manquantes, à chaque étape** (prise de mandat, offre, compromis) : une liste « reçu / manque » au lieu
   de rouvrir les documents un par un — et un **lien de dépôt envoyé au client**, qui dépose lui-même ses pièces
   (identité, titre, taxe foncière…), classées à l'arrivée. Supprime les scans et les relances.
3. **Le dossier du notaire en un clic** : les 11 pièces de `FicheNotaire` existent déjà en liste ; les rassembler en un
   envoi (lien ou archive) au lieu de les chercher et de les joindre une par une.
4. **Déposer une fois, servir partout** : un règlement de copropriété, un PV d'AG, un cadastre servent à plusieurs
   biens (16 833 copies le prouvent) → rattacher à l'immeuble / au syndic, et chaque lot en hérite.
5. **Lire le contenu, pas seulement le nom** (lecture du PDF, reconnaissance de texte sur les scans) : classe les 14 %
   muets ou non reconnus, et surtout **remplit l'annonce** — étiquette et date du DPE, surface Carrez, montant de la taxe
   foncière, charges annuelles depuis l'arrêté de charges (obligatoires dans l'annonce). ⚠ Données personnelles : où et
   par quoi le contenu est lu est à décider (sur notre serveur, ou un service extérieur).
6. **Les alertes de validité** avant le compromis (état des risques 6 mois, électricité et gaz 3 ans, DPE 10 ans).
7. **Une recherche unique** : « taxe foncière Dupont » trouve la pièce sans ouvrir le bien.

**L'ordre recommandé, révisé** : GED-1 (la liste des types) → **GED-4 l'outil de dépôt** (gestes 1 et 4) **et les pièces
manquantes** (geste 2), parce que c'est là que le temps se gagne → GED-2 / GED-3 en dessous (le classement du stock sert
la recherche et les pièces manquantes) → le dossier du notaire → la lecture du contenu.
⚠ GED-4 touche le panneau des documents : à faire avec la session signature (§5.3 bis).
➡ **Prochaine étape proposée** : regarder l'écran de dépôt RÉEL (Chrome, 1280 × 665 et téléphone), le chronométrer,
puis une maquette des parcours 1, 2 et 4 — avec données fictives. *(« Oui, vas-y » de Frédéric, 06/11 → §8)*

## 8. LA MAQUETTE DES PARCOURS 1, 2 ET 4 (06/11 soir) — ⏳ À REGARDER PAR FRÉDÉRIC

**Lien** : https://claude.ai/artifact/7Tf4Yt2i5VqZsvSoz6oeHo (privé). 5 écrans, données fictives : le dossier du bien
(onglet Documents) · déposer 9 fichiers d'un coup · le téléphone (photographier une pièce) · demander des pièces au
client + la page qu'il reçoit · la copropriété déposée une fois pour tous les lots.

### 8.1 L'écran réel regardé d'abord (06/11, Chrome de Frédéric, 1280 × 665, bien actif 63417, RIEN envoyé)
- 16 documents ; **13 cartes portent l'étiquette « DOCUMENT »**, aucune famille ; ordre alphabétique.
- Une carte fait ~100 px de haut : **3 documents visibles** sur l'écran de 665 px.
- **Un bouton « Signature » sur chaque carte**, cartes d'identité et cadastre compris.
- Le tiroir d'ajout : Parcourir (un seul fichier) · Libellé · Privé / Public · Type (10 choix figés) · Envoyer =
  **8 gestes par document** (estimation, non chronométrée : un vrai dépôt aurait écrit chez Hektor).
- Rien ne dit ce qui manque : ce bien a déjà une promesse, mais pas de taxe foncière ni d'état des risques visible.
- ⚠ Le rendu téléphone n'a pas pu être vu (la fenêtre de Chrome ne descend pas à 390 px) : le panneau y est le même, en
  mode `compact` (`App.tsx`, `ConsoleDocumentsPanel` monté 3 fois). À voir sur un vrai téléphone.

### 8.2 Habillage (ne change rien derrière)
Documents rangés par famille, lignes de 44 px (une quinzaine visibles au lieu de 3), étiquette du type au lieu de
« DOCUMENT », recherche et filtres par famille, bouton « Signature » montré seulement sur ce qui se signe.

### 8.3 Fonctionnement nouveau — ⚠ À TRANCHER, un par un (rien n'est décidé)
1. **Les pièces attendues par étape** (mandat, bien, vente) : une RÈGLE à écrire, qui dépend du bien (maison hors
   réseau → assainissement ; copropriété → pièces de copro ; terrain → étude de sol). Base existante : les 11 pièces de
   `FicheNotaire.tsx`.
2. **Dépôt multiple avec type proposé** : la règle du §6 à l'entrée ; doublon reconnu par l'empreinte sha256 (la
   colonne existe) ; format refusé dit tout de suite (`.odt`). ⚠ Touche `ConsoleDocumentsPanel` et
   `createUploadDocumentToHektorJob` : à faire AVEC la session signature (§5.3 bis).
3. **Rattacher un document à une personne ou à une affaire** (identité de Léa Bastide, offre de prêt → la vente) :
   c'est GED-2.
4. **Le lien de dépôt pour le client** : une page publique nouvelle (sécurité, durée du lien, données personnelles),
   envoi par e-mail / SMS, relance automatique à 5 jours. Le plus gros gain, et le plus gros chantier.
5. **La copropriété comme objet** (la résidence, ses lots, son syndic) : les documents communs déposés une fois.
   Recoupe la fiche syndic du chantier partenaires.
6. **Lire le contenu** (« lue sur la page : avis d'impôt », charges réelles de l'arrêté proposées pour l'annonce) :
   reconnaissance de texte ; où et par quoi, à décider (données personnelles).
7. **Les alertes de validité** (« état des risques valable jusqu'au 18/11 ») : il faut la date du diagnostic, donc
   souvent la lecture du contenu (point 6).
8. **Visibilité par défaut « privé »** pour les pièces sensibles (identité, prêt).

### 8.3 ter LA RÈGLE QUI REMPLACE LE §8.3 bis — « un seul endroit » (06/11, après l'objection de Frédéric)
> Frédéric : *« les documents seront visibles une fois sur le contact, une fois sur le bien, l'utilisateur risque de se
> tromper, et le syndic séparé ??? Trouve mieux. »* — Il a raison : un document montré à trois endroits, c'est trois
> endroits où chercher, et le doute sur celui qui fait foi.

1. **Un seul endroit pour voir et déposer : l'onglet Documents du bien** (le dossier de la vente). Tout y est : pièces
   du vendeur, des acquéreurs, de la copropriété.
2. **Aucune autre liste de documents** : ni sur la fiche contact, ni sur la fiche syndic, ni sur une « résidence ».
   Ces fiches ne gardent pas les documents ; le syndic est quelqu'un à qui l'on DEMANDE une pièce (bouton dans le
   dossier, pièce 4.4 de l'autre chantier), pas un classeur.
3. **Réutiliser sans recopier, au moment où l'on en a besoin** : quand un dossier attend une pièce déjà reçue ailleurs
   (la même personne, la même résidence), il le PROPOSE : « 4 pièces de la résidence déjà reçues pour le lot 12 : les
   reprendre ici ». Un clic = le même fichier relié à ce dossier, pas une copie. L'humain décide ; rien n'apparaît
   tout seul dans un dossier.
4. ⭐ **Conséquence : la GED ne dépend plus de la pièce 4.3 (l'immeuble)** pour les documents. Pour reconnaître « la même
   résidence », le même syndic et la même adresse suffisent pour PROPOSER (l'humain confirme) ; le numéro du registre
   national des copropriétés, s'il vient, rendra la proposition plus sûre. ⚠ À mesurer avant de le promettre : combien
   de nos 80 biens chez un syndic partagent une adresse.
- Maquette mise à jour (écran 5) : bandeau « Les reprendre ici », plus de bouton « Fiche du syndic », plus de liste des
  lots.

### 8.3 bis (REMPLACÉ par le §8.3 ter) « Le bloc copro, on le met où ? » — première proposition
- **Une seule source : la copropriété elle-même** (la résidence), pas un bien. C'est l'« immeuble » prévu en **pièce 4.3
  du chantier partenaires** (`CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md` §27.1 ; repère possible : le numéro du
  registre national des copropriétés, déjà interrogé par l'app). Il n'existe pas encore : sans lui, pas d'héritage.
- **Deux sortes de pièces** : communes à la résidence (règlement et état descriptif, PV d'AG, carnet d'entretien / fiche
  synthétique, DTG / plan de travaux) ; propres au lot (arrêté de charges, appels de fonds, pré-état daté).
- **Montrées à trois endroits, depuis la même source** : 1. l'onglet Documents de chaque lot (maquette, écran 5) ;
  2. la fiche du syndic, regroupée par résidence (aujourd'hui « un bien = sa copropriété », §27.2 de l'autre chantier) ;
  3. une ligne d'état sur la fiche du bien, dans le bloc « Diagnostics et syndic » (« copropriété : 4 pièces, pré-état
  daté à demander »).
- **Au dépôt d'une pièce commune**, l'app propose « pour toute la résidence (3 lots) » ou « seulement ce lot ».
- **Mesuré le 06/11** : 1 472 documents de copropriété (par le nom) ; 125 fichiers identiques déposés sur plusieurs
  biens, **169 copies en trop**, un même fichier sur 6 biens. Le gain est réel mais modeste aujourd'hui ; il grandit avec
  l'outil d'ajout et la demande au syndic (4.4).
- ⚠ **À coordonner avec le chantier partenaires** (`FicheSyndic.tsx`, `ficheSyndic.ts` : pas touchés ici).

### 8.4 Ce que ça pourrait casser ailleurs
Aujourd'hui rien : une maquette, aucun code. Demain : le point 2 touche le panneau que la session signature modifie en
ce moment (bouton « Signature » unique, suivi des signataires) → la prévenir avant la première ligne ; les écrans qui
cherchent par le nom gardent leur repli (§6.6) ; Hektor reçoit toujours le fichier comme aujourd'hui (le type reste
chez nous).

## 9. LES DOCUMENTS SUR LES FICHES CONTACT ET PARTENAIRE, ET LES 5 ÉTAPES (06/11 soir) — ⏳ À VALIDER

> Frédéric : *« comment avoir les documents d'identité aussi dans la fiche contact […] en fonction de la nature du contact
> (acquéreur, mandant, notaire, partenaire) — attention, une annonce peut avoir plusieurs mandats sur des périodes
> différentes avec des contacts différents […] la complétude du mandat, de la mise en vente (demande de validation), de
> l'offre, du compromis : il faut absolument la prendre en compte. »* Maquette : 3 écrans ajoutés (rangée 3) et l'écran 1
> refait (les 5 étapes).

### 9.1 Mesuré le 06/11 (lecture seule)
- **Plusieurs mandats sur un bien : rare mais réel** — 57 biens en ont 2 ou plus, dont **39 avec des mandants
  différents** ; 63417 en a même **deux en même temps** (exclusif du 02/11, simple du 03/11). (556 mandats de recherche
  n'ont pas d'annonce.)
- ⚠ **Le lien mandat ↔ mandants n'est presque jamais une fiche** : 391 mandats sur 27 474 portent un contact ; les autres
  n'ont que `mandants_texte`. Le lien personne ↔ bien existe (`app_relation`, 74 251 « mandant », 58 663
  « propriétaire »), mais **par annonce, pas par mandat** (6 seulement marqués « retirés »).
- ✅ **L'affaire connaît ses parties** : `app_affaire_partie`, 31 126 affaires — vendeur 58 577, acquéreur 35 078,
  notaire du vendeur 16 589, notaire de l'acquéreur 6 794.
- ✅ **La mise en vente a déjà sa liste** : les motifs de refus de la validation (`refusalReasonOptions`, `App.tsx`) —
  mandat non valide, DPE manquant, justificatif de propriété manquant, justificatif d'identité manquant (+ photos,
  texte, barème : sans pièce). Baisse de prix : avenant signé. Annulation : document du mandat.

### 9.2 La règle : UNE maison par document, montré là où il sert (précise le §8.3 ter)
- **La maison dépend du type** (§6) :
  pièce de la **personne** (identité, état civil, pouvoir, RIB, Kbis / statuts, financement) → la fiche de la personne ;
  pièce du **bien** (diagnostics, cadastre, urbanisme, copropriété, titre de propriété) → le bien ;
  pièce du **mandat** (mandat, avenant, fin, honoraires) → le mandat, avec son numéro et sa période ;
  pièce de l'**affaire** (offre, compromis, acte, SRU, séquestre, renseignements) → l'affaire, avec ses parties.
- **Le dossier du bien rassemble** ce qui sert au mandat EN COURS et à l'affaire EN COURS : pièces du bien + du mandat en
  cours + des mandants de CE mandat + de l'affaire et de ses parties. Les pièces d'un mandat précédent (autres
  mandants) restent avec lui, repliées (« Voir l'ancien mandat »), et ne comptent pas dans la complétude.
- **La fiche contact montre « Ses pièces »** (celles dont elle est la maison), chacune avec « reçue pour… », et
  **« Ses dossiers »** par rôle (mandante, acquéreuse…), avec un lien vers le dossier, jamais la liste des pièces du bien.
- **Déposer ici ou là, c'est la même chose** : une seule maison, jamais deux copies. Une pièce encore valable est
  PROPOSÉE au dossier suivant (nouveau mandat, nouvelle offre) au lieu d'être redemandée.
- **Qui est concerné, au dépôt** : la colonne « Concerne » propose les mandants du mandat en cours et les parties de
  l'affaire en cours ; l'humain choisit. ⚠ Vu le §9.1, on ne peut PAS déduire seul « le mandant de ce mandat » : le
  rattachement document → personne doit être écrit par la GED (GED-2), pas recalculé.
- **Selon la nature du contact** : mandant / propriétaire → identité, état civil, capacité, pouvoir, RIB, société ;
  acquéreur → identité, financement (sensible), mandat de recherche ; **notaire** → aucune pièce propre, la fiche suit
  les dossiers échangés avec l'étude (état et dates, lien vers le dossier) ; **diagnostiqueur et autres partenaires** →
  leurs pièces propres (certifications, assurance avec date d'expiration, convention, tarifs) + où sont leurs rapports.
- ⚠ Fiches métier : `FichePartenaire.tsx` / `FicheNotaire.tsx` appartiennent au chantier partenaires → à poser avec lui.

### 9.3 Les 5 étapes (maquette, écran « La règle »)
Le mandat (proposé ; appui : la génération du mandat est déjà bloquée sans nom et prénom des mandants) · la mise en
vente (**écrit dans l'app** : les motifs de refus de Pauline) · l'offre (proposé) · le compromis (**écrit dans l'app** : les
11 pièces de la fiche notaire ; copropriété et terrain proposés) · la vente (proposé). Une pièce reçue compte pour les
étapes suivantes ; les pièces « si… » ne s'ajoutent que si la fiche le dit (société, tutelle, prêt, hors réseau,
copropriété, terrain).
⚠ **La demande de validation à Pauline pourrait montrer la liste** (« 4 pièces sur 4 ») AVANT l'envoi : la moitié de ses
motifs de refus deviendrait impossible. À trancher : simple avertissement, ou envoi bloqué ?

### 9.4 À trancher
✅ **Point 1 VALIDÉ le 06/11 : « oui pour le principe »** — avec un recadrage : *« le niveau ergonomique et surtout
design n'est pas suffisamment expert et pro, il faut faire mieux, et maquetter aussi l'intégration dans la fiche
contact : les blocs, où et comment »* → §10.
1. La règle « une maison par document » (§9.2). 2. Les 5 listes, ligne par ligne (surtout celles marquées
« proposé »). 3. Avertir ou bloquer la demande de validation quand une pièce manque. 4. Ce que voit un négociateur sur
la fiche d'un contact qui n'est pas son client (pièces sensibles).

## 10. L'INTÉGRATION DANS LES VRAIES FICHES (06/11, nuit) — ⏳ À REGARDER PAR FRÉDÉRIC
Maquette, rangée du haut : **A** (fiche du bien, onglet Documents) et **B** (fiche contact). Les écrans 1 et « fiche
contact » de la première version sont marqués « remplacés ».

### 10.1 La vraie fiche contact, regardée d'abord (prod, Chrome, 1280 × 665, un mandant de 63417, rien modifié)
Colonne gauche : retour, identité, **Foyer** (personnes, « Ajouter un conjoint »), actions, coordonnées, négociateur.
Zone de travail (`contact-detail-v2.css`, blocs `fa-cx-mod`, titres `fa-cx-sec`) : « Recherche & rapprochement » (2/3) et
« À faire » (1/3) ; « Biens & mandats liés » ; « Activité & relation » (Fil / Rendez-vous / Échanges, filtres Tout,
Annonce, RDV, Emails, Rapprochements, Transactions, Relances) ; « Qualité de la fiche » (repliée). La colonne de droite
est vide sous « À faire ». ⚠ Vu au passage : « Biens & mandats liés » montrait le mandat 18989 mais pas le 18986 que le
fil cite « signé » (deux mandats simultanés) — non creusé, à signaler.

### 10.2 Les 3 ajouts sur la fiche contact (rien d'autre ne bouge)
1. **Un bloc « Pièces »** dans la colonne de droite, sous « À faire » (la place vide) : les pièces de chaque personne du
   foyer, avec leur validité ; ce qui manque est dit (« Jean : carte d'identité, manque ») ; « Déposer une pièce » reprend
   exactement le geste de « Planifier une relance ». Pièces sensibles marquées d'un cadenas.
2. **Dans « Biens & mandats liés », sous chaque mandat** : l'état de ses pièces (4 sur 5, « il manque la taxe foncière »)
   et « Ouvrir les documents du bien ». Un mandat clos garde les siennes (autres mandants).
3. **Dans « Activité & relation »** : un filtre « Pièces » et les événements « pièces demandées » / « pièce reçue ».

### 10.3 La fiche du bien, onglet Documents (sous « Médias et documents », à côté de Photos et Visite 3D)
- En haut, **la ligne des 5 étapes** (même dessin que le parcours du cockpit) : où en est le dossier, d'un regard.
- Au centre, **l'étape en cours**, rangée par vendeurs / bien / acquéreurs : une ligne par pièce, ce qui manque hachuré
  (on y glisse le fichier), action au bout de la ligne (Ouvrir, Demander, Relancer, Refaire).
- À droite, **toujours visibles** : déposer (plusieurs fichiers), demander au client, envoyer au notaire (grisé tant
  que des pièces manquent), chercher, et tous les documents par famille.
- Contrôle du rendu : A et B regardés dans la maquette publiée (textes coupés raccourcis, un repère déplacé).
  ⚠ Le téléphone n'est pas encore dessiné pour A et B (la fiche contact s'empile en une colonne sous 900 px).

## 11. LES PIÈCES PAR ÉTAPE : AUDIT ET BONNES PRATIQUES DE LA PROFESSION (06/11, nuit) — ✅ 6 MOMENTS VALIDÉS (§11.7), points 2-4 ouverts
> Frédéric : *« pour les étapes et les documents nécessaires par étape, refais un audit et une analyse des bonnes
> pratiques de la profession, propose-moi. »* Remplace la liste du §9.3 (écran « La règle »).

### 11.1 Sources (lues le 06/11) et leur poids
- **Officiel** : service-public.gouv.fr F10798 (DDT en vente, vérifié le 07/03/2025) ; CCH L271-4 (DDT), L721-2
  (copropriété, via réponses ministérielles) ; C. env. L125-5 (état des risques).
- **Pratique notariale** : la liste « pièces à fournir et questionnaire » d'une étude (bordelais-ligne.notaires.fr) — la
  plus concrète trouvée.
- **Profession** : FNAIM (pré-état daté), sites d'agences et de presse spécialisée (offre d'achat, ERP, audit). Ces
  sources secondaires se contredisent parfois : seules les règles concordantes sont retenues, le reste est marqué
  « à vérifier ».
- **L'app** : motifs de refus de Pauline (`refusalReasonOptions`), 11 pièces de `FicheNotaire.tsx`, génération du mandat
  bloquée sans nom et prénom des mandants, parcours du cockpit (avis de valeur, mandat, offre, compromis, vente).

### 11.2 Ce que la base dit de nos dossiers (06/11, reconnu par le NOM, biens en cours)
| | Actif (583) | Sous offre (38) | Sous compromis (93) |
|---|---:|---:|---:|
| aucun document | **95** | 0 | 0 |
| mandat (document) | 67 % | 97 % | 92 % |
| pièce d'identité | **52 %** | 87 % | 95 % |
| titre de propriété | 45 % | 63 % | 76 % |
| taxe foncière | 32 % | 58 % | 54 % |
| DPE ou dossier de diagnostics | **35 %** | 34 % | 52 % |
| état des risques (ou DDT) | **50 %** | 61 % | 70 % |
| cadastre | 59 % | 82 % | 80 % |
| bon de visite | 22 % | 42 % | 59 % |
| financement | — | 24 % | 37 % |
| copro : règlement / PV d'AG / charges | 25 / 43 / 52 % (96) | 2, 4, 4 sur 8 | 5, 4, 4 sur 9 |
⚠ **Lecture prudente** : une absence par le nom n'est pas une absence prouvée (14 % de noms muets ; un DDT contient souvent
l'état des risques ; une pièce peut être chez le notaire ou sur papier). Mais l'ordre de grandeur est net : **l'état des
risques, qui doit être remis dès la première visite, n'est au dossier que d'un bien actif sur deux**, et le rapport DPE
d'un sur trois (l'étiquette, elle, est saisie dans la fiche : c'est ce que contrôle « Diagnostics manquants »).
⚠ Un zéro a été corrigé en route (charges de copro à 0 % : mon script portait encore l'ancien nom du type).

### 11.3 LA PROPOSITION — 6 moments, chaque pièce marquée OBLIGATOIRE / BONNE PRATIQUE / SI…
**1. Prise de mandat** (avant la signature)
- OBLIGATOIRE : identité de chaque mandant (vigilance anti-blanchiment : identifier, vérifier, garder 5 ans) ; le mandat
  écrit, numéroté au registre (loi Hoguet).
- BONNE PRATIQUE forte : titre de propriété (l'agent vérifie la qualité de vendeur) ; situation familiale — contrat de
  mariage ou PACS, livret de famille (le conjoint doit consentir pour le logement de la famille) ; taxe foncière.
- SI société : Kbis, statuts, pouvoir du gérant, bénéficiaires effectifs · SI succession ou indivision : attestation de
  propriété ou de notoriété, tous les indivisaires · SI personne protégée : jugement, autorisation du juge · SI quelqu'un
  signe pour un autre : pouvoir.
**2. Mise en vente** (validation par Pauline, avant l'annonce et la 1re visite)
- OBLIGATOIRE : DPE (étiquettes énergie et climat et estimation des dépenses dans l'annonce ; F ou G : « logement à
  consommation énergétique excessive ») ; état des risques de moins de 6 mois, à remettre DÈS LA PREMIÈRE VISITE, et la
  mention Géorisques dans l'annonce (depuis le 01/01/2023) ; audit énergétique SI maison ou monopropriété classée E, F ou
  G (depuis 2025 pour E), remis aussi dès la 1re visite.
- Les contrôles déjà écrits de Pauline : mandat valide, justificatif de propriété, d'identité (+ photos, texte, barème).
- SI copropriété : l'annonce doit donner le nombre de lots, les charges annuelles et une éventuelle procédure (à vérifier
  sur le texte) → arrêté de charges et fiche synthétique dès la mise en vente.
- BONNE PRATIQUE : commander le DDT complet dès le mandat (pas de surprise amiante ou plomb au compromis).
**3. Visites**
- BONNE PRATIQUE forte : bon de visite signé (preuve de la mise en relation) ; ⭐ **tracer la remise de l'état des risques
  (et de l'audit) à chaque visiteur** — c'est l'obligation la moins tenue (§11.2) et la plus facile à prouver avec la GED.
**4. Offre**
- BONNE PRATIQUE : offre écrite signée par chaque acquéreur (prix, financement, conditions, délai de validité de 5 à 10
  jours) ; identité des acquéreurs (vigilance : à confirmer sur le texte pour l'acquéreur) ; plan de financement ou
  accord de principe ; réponse écrite des vendeurs ; ⚠ toutes les offres sont transmises au vendeur, refusées comprises :
  les garder au dossier.
**5. Compromis** (le dossier au notaire)
- Vendeurs : identité, état civil et régime matrimonial, titre de propriété, taxe foncière, RIB, attestation d'assurance
  du bien (selon l'étude).
- Diagnostics VALABLES À LA DATE DE SIGNATURE (service-public, avec leurs conditions) : DPE ; audit SI E, F, G ; plomb SI
  avant 1949 ; amiante SI permis avant le 01/07/1997 ; électricité et gaz SI installation de plus de 15 ans ; termites SI
  zone ; état des risques SI zone (6 mois) ; bruit SI zone d'aérodrome ; assainissement (non collectif : contrôle SPANC de
  moins de 3 ans) ; mérule SI zone (dans l'acte) ; surface Carrez SI lot de copropriété ; carnet d'information du logement
  SI permis ou déclaration depuis le 01/01/2023.
- SI travaux ou construction de moins de 10 ans : permis ou déclaration, achèvement (DAACT), dommage-ouvrage ou factures
  et décennales des entreprises.
- SI copropriété : coordonnées du syndic, règlement et état descriptif (et modificatifs), PV des 3 dernières AG, fiche
  synthétique, carnet d'entretien, amiante des parties communes, pré-état daté (pratique : seul l'état daté est légal, à
  l'acte), DTG ou plan de travaux s'il existe.
- SI loué : bail, congé · questionnaire vendeur : détecteur de fumée, ramonage, chaudière, cuve, contrats (alarme,
  photovoltaïque, affichage).
- Acquéreurs : identité, état civil, financement (apport, banque, montant), projet (travaux).
- Après la signature : notification SRU (10 jours de rétractation, preuve d'envoi et de réception) ; attestation de
  séquestre (dépôt de garantie, souvent 5 à 10 %).
**6. Vente** (jusqu'à l'acte)
- Offre de prêt acceptée et conditions levées ; SI copropriété : état daté du syndic ; diagnostics à date courte
  revérifiés à la date de l'acte (état des risques, termites : 6 mois) ; attestation de vente ou copie de l'acte ;
  facture d'honoraires ; remise des clés ; tout garder 5 ans (vigilance).

### 11.4 Les durées de validité qui feront les alertes
DPE 10 ans (⚠ les DPE de 2013 à mi-2021 ont expiré fin 2022 ou fin 2024) · électricité et gaz 3 ans · état des risques 6
mois · termites 6 mois · plomb 1 an s'il est positif, sans limite sinon · amiante sans limite s'il est négatif et fait
depuis le 01/04/2013 · assainissement non collectif 3 ans · audit énergétique : à vérifier (5 ans selon plusieurs
sources) · bruit : à vérifier.

### 11.5 Ce que ça change par rapport au §9.3
Une étape « Visites » apparaît (bon de visite + remise de l'état des risques) ; la situation familiale entre au mandat ;
le compromis suit la liste service-public avec ses CONDITIONS (âge du bien, zones, copropriété, travaux de moins de 10
ans, location) au lieu d'une liste fixe ; les durées de validité deviennent des alertes ; tout est étiqueté obligatoire /
bonne pratique / si… pour que l'app sache quoi BLOQUER et quoi seulement SIGNALER.

### 11.6 À trancher
1. Les 6 moments et leurs listes. 2. Ce qui BLOQUE (proposé : rien au début, seulement signaler ; puis bloquer la mise en
vente sans DPE ni état des risques valables). 3. Tracer la remise de l'état des risques aux visiteurs. 4. Les conditions
demandent des faits sur le bien (année de construction, chauffage, assainissement, zones) : les lire dans la fiche
Hektor quand ils existent, sinon les demander une fois.

### 11.7 La décision de Frédéric (06/11)
- ✅ **Point 1 VALIDÉ** : *« Oui, validés »* — les 6 moments (prise de mandat, mise en vente, visites, offre, compromis,
  vente) et leurs listes du §11.3, avec les étiquettes obligatoire / bonne pratique / si… et les durées du §11.4. Ils
  remplacent les 5 étapes du §9.3 (écran « La règle » de la maquette).
- ⏳ **Points 2, 3 et 4 encore ouverts** : ce qui bloque, la trace de la remise de l'état des risques aux visiteurs, où lire
  les faits dont dépendent les conditions.
- Restent « à vérifier » sur texte (non tranchés par cette validation) : vigilance anti-blanchiment pour l'acquéreur,
  mentions de copropriété dans l'annonce, durée de validité de l'audit énergétique et du diagnostic bruit.
- Rien n'est codé : GED-2 et la suite attendent toujours un « vas-y » explicite.

## 12. L'OUTIL D'AJOUT DE DOCUMENTS — LA PROPOSITION ARRÊTÉE (11-12/11/2026)

> Travail fait en LECTURE SEULE (équipe d'agents, puis étude d'experts). Page de référence, maquettes comprises :
> https://claude.ai/artifact/WEHAruTgvuctKN74N8Rt6r (version 10). Rapports complets (hors dépôt) : bloc-notes de la
> session, dossier `ged_equipe/` (1 à 6) et `ged_equipe/etude/` (A à D par famille, **E_synthese_catalogue.md = la
> référence du catalogue**). ⭐ Le 12/11, « on peut reprendre » : le morceau 1 commence (§12.6).

### 12.1 Le cadre (décisions de Frédéric du 12/11)
- **Seuls les documents déposés DANS L'APP sont lus.** Pas de lecture du soir des documents arrivés par la console Hektor
  (proposée le 11/11, **refusée** : « uniquement ajout de documents dans l'app »). Ne pas re-proposer.
- **Développé et essayé par Frédéric SEUL, avant la migration des négociateurs.** Tout derrière des interrupteurs à trois
  crans (off / admin / on), réglés sur « admin » pendant les essais ; les négociateurs gardent le formulaire d'aujourd'hui.
- **Le run de nuit et la collecte des mises à jour Hektor NE SONT PAS TOUCHÉS.** Effet indirect seulement : la descente
  (`phase2/sync/pull_from_supabase.py`) recopie d'elle-même toute table neuve.
- **Jusqu'à la coupure, chaque document part chez Hektor par le chemin existant** (`createUploadDocumentToHektorJob` →
  `upload_document_to_hektor`, dépôt différé), une fois son type et son nom validés. Le nom reste définitif (⑦-9).
- **Le worker n'est pas modifié** : l'anti-doublon du dépôt différé (4 doublons de 59203, 23/10) est écrit depuis le 06/11
  (G1, commit `3c32daa`, session signature). ⏰ Vérifier qu'il est CHARGÉ (heure des processus) avant le 1er essai.
- **L'IA classe chaque fichier AVANT l'envoi** (type parmi les 60, nom, découpage en pièces) **et lit les valeurs APRÈS**
  (PDF et photos). **L'IA extrait, NOTRE CODE compare.** Rien ne s'écrit sans clic. La lecture tourne sur le backend
  Render (fichier déjà au coffre) : pas de 5ᵉ service Windows.
- **Les pièces des personnes SONT lues** (« il faut bien récupérer les données sur la carte d'identité, ce n'est pas
  inutile pour vérifier ou compléter la data ») : identité, état civil, fiche de renseignements, financement.
- ⛔ **Le RIB est EXCLU de toute lecture** (« NON IL FAUT EXCLURE LES RIB ! ») : jamais envoyé à l'IA. Garde : un nom
  « RIB » ou un IBAN dans le texte d'un PDF → reconnu chez nous, jamais envoyé ; une photo muette part en basse définition
  pour le seul classement, et si c'est un RIB rien n'est gardé à part le type.
- ✅ **Registre anti-blanchiment : OUI** — le numéro, la date et le lieu de délivrance de la pièce d'identité restent CHEZ
  NOUS (table à accès restreint : admin, managers, négociateur du bien), jamais chez Hektor.
- **Mesure de protection** : seulement sa nature (tutelle, curatelle, habilitation), le représentant, la date du jugement.
  Jamais le motif ni la santé.
- **Pas de choix complète / resserrée d'avance** : morceaux livrés dans l'ordre de valeur ; la resserrée est un point
  d'arrêt ; décision après 2 semaines de mesure (vrai / faux / déjà su, règle par règle).

### 12.2 Le catalogue (étude d'experts du 12/11, détail dans `E_synthese_catalogue.md`)
- **23 types lus, 37 « classer seulement »** dont 5 jamais envoyés à l'IA : RIB, comptes d'entreprise, notes internes,
  courrier, clés. Taxe foncière : classée, pas lue en V1 (pas une mention obligatoire ; seul geste = groupe
  `mandat_infofi`, prix + honoraires).
- **7 comparateurs** (nombre, date, personnes, lieu, références, liste, présence) + 2 étapes (normaliser, résoudre la
  cible). Réponses : égal / proche / différent / incomparable ; seul « différent » alerte.
- **42 règles V1** : 13 sans IA (N1-N13), 19 avec lecture des documents du bien et des affaires (L1-L19), 10 avec lecture
  des pièces des personnes (P1-P10, le RIB retiré). Une cinquantaine « plus tard », une vingtaine « jamais ».
- Mesuré sur les biens en cours : date de naissance remplie pour 167 mandants sur 1 292, situation de famille 72 ;
  acquéreurs 10 sur 252. Geste existant : `editContactOptimistic` (`api.ts:11643`, accepte `birth_date`, `birth_place`,
  `marital_status` ; 6 envois `update_hektor_contact` avec date de naissance déjà `done`).

### 12.3 La nomenclature : points 1 à 7 du §6.8 tranchés le 12/11
1. 14 familles, justificatifs séparés du mandat. 2. Un type par diagnostic (11). 3. Petits types gardés. 4. Familles
courrier, interne, entreprise, location gardées. 5. ⛔ **« On ne va pas traiter les documents déjà en base »** : rien n'est
classé, lu ni écrit pour les ~193 000 anciens ; leur NOM sert seulement, à l'affichage, à dire « trouvé » dans « Reçu /
Manque » et les règles sans IA (« non trouvé », jamais « absent »). 6. Factures d'honoraires NON sensibles. 7. Les 6
types partenaires gardés.

### 12.4 Ce que l'étude a corrigé (vérifié en base et dans le code)
- Les groupes de `app_dossier_detail_current.detail_payload_json` sont du JSON **rangé en chaîne** : décoder deux fois,
  à UN seul endroit, sinon toutes les cases paraissent vides (714/714 mesuré le 12/11).
- Le groupe `diagnostiques` n'a **jamais** rempli une case vide en modification (le 22/10 sur 63331 = renvoi à
  l'identique) : épreuve sur 62774 avant tout « remplir » DPE / état des risques.
- `app_set_mandat_charge_optimistic` **écrase** et **efface sur null** (`patch_charge_honoraires_mandat_2026-11-02.sql`
  l. 295-311) ; `app_conditions_affaire_ecrire` efface puis repose toute la liste et est réservée managers / admins en
  base ; le report RNIC (`App.tsx:11603`) écrit le syndic en texte libre ; le cadastre IGN n'est pas une référence.

### 12.5 Le chemin et le coût
Morceaux : 1 base (2 j) · 2 fenêtre de dépôt (6 j) · 3 « Reçu / Manque » (3 j) · 4 classement par l'IA avant l'envoi
(4 j) · 5 les 13 règles sans IA (3 j) · 6 les 14 fiches de lecture (7,5 j) · 7 comparateurs et 19 règles (7 j) ·
8 propositions (5 j) · 9 pièces des personnes (9 j) · 10 mesure (1,5 j). **≈ 48 j de développement, ≈ 57 avec essais et
coordination** ; point d'arrêt resserré ≈ 35 / 42. **Coût IA** (≈ 1 150 dépôts / mois après migration) : ≈ 1,3 € / mois
(gpt-6-luna), 2,6 € (gpt-5.6-luna), 4,7 € (gpt-4.1-mini) ; 3 à 10 € au maximum avec marge ; < 0,50 € / mois pendant
les essais. Avant le 1er document réel : contrat de sous-traitance avec le fournisseur d'IA et `store:false`. Avant les
négociateurs : analyse d'impact, registre des traitements, clause au mandat.

### 12.6 Le morceau 1 — la base (ouvert le 12/11)
**Audit (12/11, lecture seule)** : aucune table ni réglage `ged` en base ; `app_console_document.id` est un uuid, une
seule clé étrangère pointe vers elle (`app_signature_request`, ON DELETE SET NULL) ; une table neuve donne PAR DÉFAUT
tous les droits à `authenticated` (`pg_default_acl`) → chaque rôle se nomme dans les `revoke` ; patron suivi :
`patch_affaire_suivi_2026-11-09.sql` (RLS sans politique = personne n'accède sauf le service_role).

**Le patch écrit, PAS appliqué** : `supabase/patch_ged_m1_base_2026-11-12.sql` (+ `_INVERSE`, + `_REPETITION`
fabriquée à partir du patch, qui lève une erreur volontaire : rien n'est gardé ; attendu « 12 VERT, 0 ROUGE »).
- 4 tables : `app_ged_type` (66 codes = 60 types + 6 partenaires ; `lecture` lue 23 / classer / jamais_envoye 5 ;
  `sensible` 5), `app_ged_classement` (une fiche par document DÉPOSÉ AVEC L'OUTIL), `app_ged_rattachement`,
  `app_ged_journal` ; 3 interrupteurs `ged_depot_multiple`, `ged_lecture_ia`, `ged_propositions` = `off`.
- ⭐ **Choix d'audit : AUCUNE clé étrangère vers `app_console_document`** — un simple uuid + une empreinte de secours
  (annonce, sha256, nom). Raisons : ne pas verrouiller ni modifier la table de la signature, et la synchro supprime /
  recrée des lignes (une clé `ON DELETE SET NULL` perdrait le lien au premier dédoublonnage). ⇒ le morceau 1 ne touche
  pas `app_console_document` : la session signature sera prévenue au morceau 2 (le panneau des documents).
- Pas encore les tables de lecture, de valeurs et de propositions (morceaux 6 à 9) ; aucune fonction ; rien à l'écran.
- Effet ailleurs : la descente de 07:45 recopiera les 4 tables (66 lignes + vides).
✅ **POSÉ EN PRODUCTION le 12/11, avec l'accord de Frédéric (« Oui, vas-y »)** :
- répétition d'abord : **12 VERT, 0 ROUGE**, puis vérifié que rien n'était resté (0 table `app_ged_*`, 0 réglage) ;
- patch posé, puis les 12 contrôles relus en production : **12 VERT** ;
- ⭐ témoin inverse (en rôle `authenticated`, transaction annulée) : lecture du classement **REFUSÉE**, écriture dans la
  nomenclature **REFUSÉE**.
Les 3 interrupteurs sont éteints ; rien ne lit encore ces tables. Commité et poussé (`7db04f9`, accord de Frédéric).

### 12.7 Le morceau 2 — la fenêtre de dépôt (audit du 12/11, rien codé)
**Audit** :
- `ConsoleDocumentsPanel` (`App.tsx:11831`), monté 3 fois (`33593` cockpit v21, `37246` fiche classique, `41326`
  téléphone) ; le formulaire `uploadForm` (`12152-12225`) est partagé par les deux habillages (`12365`, `12461`) : un
  seul fichier (`files?.[0]`), libellé, privé / public, type en liste figée de 10.
- L'envoi `createUploadDocumentToHektorJob` (`api.ts:9106`) : travail → coffre `temp/uploads/` → ligne chez nous
  (`app_console_creer_document_optimistic`) → relecture du travail, qui porte alors `app_document_id`.
- Mesuré sur 30 jours : 14 envois par l'app, tous `done`, 2 personnes, 12 avec la ligne chez nous, 3 avec un type,
  durée médiane 21,6 s.
- L'anti-doublon G1 (`3c32daa`, 06/11) est CHARGÉ : les 4 services worker ont démarré le 10/11 à 18:47
  (`Win32_Process.CreationDate`).
- Interrupteur à trois crans : patron `loadSignatureYoutrustActive` (`api.ts:9295`, 'admin' = admin actif seul).
- Règles de classement par le nom : `phase2/checks/ged1_mesure_nomenclature.py:95-182` (≈ 80 motifs, la première qui
  gagne, « sûr » / « probable », détection des noms muets) → à porter UNE fois en TypeScript, pour le dépôt ET pour
  « Reçu / Manque » (morceau 3).
- Aucune bibliothèque PDF dans le front (`package.json`).
- Session signature prévenue le 12/11 (message : ce qui est posé, la ligne prévue dans son panneau, deux questions).
  **Sa réponse (12/11)** : rien en cours ni prévu sur `ConsoleDocumentsPanel` ni sur `createUploadDocumentToHektorJob`
  (la bascule Youtrust n'est faite que de réglages). Un document déposé par l'outil ne gêne pas la signature s'il passe
  par le chemin existant (marquage manuscrit, fenêtre « Faire signer », cockpit inchangés). À respecter :
  - ⚠ **LES NOMS** : au réessai d'un dépôt, le worker ADOPTE le document Hektor « du même nom qu'aucune autre ligne ne
    réclame » avec un rapprochement LARGE (égal, ou l'un CONTIENT l'autre : `documentNonReclame`,
    `console_job_worker.js` ~10019). ⇒ la fenêtre doit refuser ou suffixer un nom qui contient, ou est contenu dans, celui
    d'un autre document du bien (déjà là ou du même lot) ; envoi un par un ;
  - relancer après la modification : `test_choix_signature.cjs`, `test_pieces_signature.cjs`,
    `test_suivi_signataires.cjs`, `test_code_par_email.cjs`, `test_etat_signature_mandat.cjs` (ils comptent les montages
    dans le panneau ; ne toucher qu'à `uploadForm`) ;
  - ne jamais écrire `metadata_json.signature`, `signed_document`, `remplace`, `signataires_du_pdf` ;
  - ⚠ `App.tsx` et `lib/api.ts` portent des changements NON commités d'une autre session : stager par blocs.
✅ **« Vas-y, morceau 2 » (12/11). ÉCRIT ET CONTRÔLÉ HORS LIGNE, PAS ENCORE EN SERVICE :**
- `apps/hektor-v1/src/lib/gedTypeParNom.ts` : les règles du nom, FABRIQUÉES à partir du Python (script du bloc-notes
  `ged_m1/gen_type_par_nom.py` ; corriger les règles en Python puis refabriquer). ⭐ Témoin : **193 629 noms sur 193 629
  classés à l'identique** par les deux versions ; témoin inverse : une règle abîmée → 7 235 écarts (la comparaison voit).
  Le fichier des noms a été effacé aussitôt.
- `src/lib/ged.ts` (lecture des types, `gedClasser`, interrupteur à trois crans `useGedDepotMultiple`, empreinte, règle
  des noms `nomEnConflit`) ; `src/DepotDocuments.tsx` + `.css` (la fenêtre) ; `pdf-lib@1.17.1` (chargé seulement pour
  assembler des photos).
- `App.tsx` : +19 / −2, dans `ConsoleDocumentsPanel` seulement — `formulaireAjout = gedDepot ? <DepotDocuments …> :
  uploadForm`, monté aux deux endroits où l'était `uploadForm` ; le formulaire d'aujourd'hui reste le secours.
- `supabase/patch_ged_m2_classer_2026-11-12.sql` (+ `_INVERSE`, + `_REPETITION` fabriquée par `ged_m1/gen_ged_m2_repetition.py`) :
  colonne `app_console_job_id` + fonction `app_ged_classer` (gardes : utilisateur actif, SON travail d'envoi, type actif ;
  annonce et document lus dans le travail ; idempotente). **Répétition jouée : 12 OK, 0 KO** (dont : le dépôt d'un autre
  refusé, type inconnu refusé, rappel sans écriture, `app_console_document` intacte) ; vérifié ensuite que rien n'est resté.
  **PAS POSÉ** (accord à demander).
- Contrôles : `npm run build` vert ; `test_ged_depot.cjs` **17 VERT** (noms, type proposé, branchement) ; les 5 essais de
  la session signature **verts** ; écran vu sur une page d'essai à données fictives (bureau 1280 × 665 et téléphone) :
  conflit de nom refusé, nom muet → type obligatoire puis nom « DPE 12-11-2026 », `.odt` refusé, pièce d'identité en
  privé forcé, 3 photos → 1 PDF.
✅ **« Oui, les trois » (12/11)** : `patch_ged_m2_classer` **POSÉ EN PRODUCTION**, contrôles relus **7 VERT**
(colonne, fonction SECURITY DEFINER, anon refusé, authenticated autorisé, classement vide, une seule clé étrangère vers
`app_console_document`, interrupteur `ged_depot_multiple` toujours `off`) ; commité et poussé.
✅ **ALLUMÉ le 12/11 à 12:26 (« Oui, allume admin »)** : `ged_depot_multiple = 'admin'` ; `ged_lecture_ia` et
`ged_propositions` restent `off`. ⚠ Le cran « admin » montre la fenêtre aux **4 admins actifs**, pas à Frédéric seul
(même règle que `signature_youtrust`). Les négociateurs gardent le formulaire d'aujourd'hui.
ÉTEINDRE : `update public.app_setting set value = 'off', updated_at = now() where key = 'ged_depot_multiple';`
✅ **ESSAI RÉEL du 12/11 (Frédéric, bien d'essai 62774, 12:34) : 3 documents d'un coup** — 2 images de pièce
d'identité et 1 PDF d'offre. Mesuré :
- 3 travaux `upload_document_to_hektor`, tous `done` **au premier essai** (`attempt_count` 1), 40 s à 1 min 15 l'un après
  l'autre ; 3 numéros Hektor posés, `envoi_hektor_statut = envoye` ;
- **aucun doublon** : pour chaque document, 1 seule ligne par nom, par empreinte et par numéro Hektor ;
- 3 classements, chacun avec son rattachement au bien et sa ligne de journal ; les 3 types proposés par le nom ont été
  gardés (`justif.identite` × 2, `transaction.offre`) ; les 3 en privé ;
- ⭐ l'empreinte calculée par le navigateur = celle du serveur (3 sur 3) : le repérage des doublons au dépôt marchera ;
- ⭐ `app_console_document.document_type` vaut déjà « document » sur les 3 : la synchro a réécrit le type, comme mesuré le
  06/11 — le classement vit bien à part ;
- les 15 autres documents du bien n'ont été touchés que par la resynchro habituelle d'après dépôt ; le marqueur de
  signature « to_send » posé sur le nouveau PDF vient de cette même synchro (tous les PDF du bien l'ont), pas de la GED.
⏳ Pas encore essayé : un nom muet, la photo de plusieurs pages, le vrai téléphone.

### 12.8 Le morceau 3 — « Reçu / Manque » (audit du 12/11, rien codé)
**Audit** :
- Les pièces par moment : §11.3 (6 moments validés le 06/11, étiquettes obligatoire / bonne pratique / si…), durées §11.4.
  §11.6 points 2-4 encore ouverts (ce qui bloque, trace de l'état des risques remis aux visiteurs, faits des conditions).
- Le moment en cours, mesuré sur les 714 biens en cours : Actif 579 (dont 164 sans numéro de mandat), Sous offre 43,
  Sous compromis 92 ; un bien vendu n'est plus dans `app_dossier_current` (le moment « vente » n'est pas atteignable ici).
- Les faits des conditions, remplis sur les biens en cours : copropriété « oui » 114 ; année de construction
  (`diagnostiques_json.ANNEE_CONS`) 301 sur 714 (42 %) ; assainissement (`equipements_json.ASSAINISSEMENT`) 211 ; dates
  de diagnostics gaz / termites / assainissement presque jamais (0 à 4).
- Le code qui existe : `FicheNotaire.tsx:94` (`PIECES_DU_DOSSIER`, 11 pièces par motifs, sa propre copie des règles) ;
  motifs de refus de Pauline (`App.tsx:7092`, `refusalReasonOptions`) ; `DemandeDocument.tsx` (demander au syndic,
  commander un diagnostic) monté à `App.tsx:48818`. Maquette de l'onglet : écran E0 (bloc « Reçu / manque » au-dessus de
  la liste existante, laissée telle quelle ; « Manque : glisse le fichier ici »).
- Lecture des classements : `app_ged_classement` n'est lisible par personne aujourd'hui (RLS sans politique) → il faut
  une politique de lecture (même périmètre que `app_console_document`).
⏳ Attend le « vas-y » de Frédéric.
✅ **« Vas-y, morceau 3 » (12/11). ÉCRIT ET CONTRÔLÉ HORS LIGNE, PAS ENCORE EN SERVICE :**
- `apps/hektor-v1/src/lib/gedPieces.ts` (fonction pure) : les pièces par moment (§11.3), le moment en cours (pas de
  n° de mandat → prise de mandat ; actif avec mandat → mise en vente et visites ; sous offre → offre ; sous compromis →
  compromis), les conditions (copropriété, année < 1997 / < 1949, bâti de plus de 15 ans, maison classée E/F/G avec la
  classe recalculée, assainissement non collectif, terrain / garage sans diagnostics, case « DPE non concerné ») ; une
  condition que la fiche ne dit pas → « selon le cas », jamais « non trouvé », et non comptée. Reconnaissance : le type
  décidé (classement GED) d'abord, sinon le NOM (`gedTypeParNom`, « sûr » ou « probable ») ; un dossier de diagnostics
  compte pour les diagnostics, « dans un dossier ». Moments précédents : seules leurs pièces OBLIGATOIRES non trouvées.
- `src/RecuManque.tsx` + `.css` : le bloc ; ce qui manque d'abord, les reçues repliées sur une ligne ; cliquer une pièce
  non trouvée ouvre la fenêtre de dépôt avec ce type choisi (bandeau « Prochain fichier : … »).
- `src/lib/ged.ts` : `useGedRecuManque`, `loadGedClassements` (lecture ratée = les noms suffisent).
- `src/DepotDocuments.tsx` : `typeAttendu` (le prochain fichier prend ce type ; nom muet → « <type> <date> »).
- `App.tsx` (+44 / −1, `ConsoleDocumentsPanel` et une fonction `faitsGedDuBien` qui lit la fiche par
  `rawWizardDetailField`) : `blocRecuManque` monté au-dessus du dépôt dans les deux habillages.
- `supabase/patch_ged_m3_recu_manque_2026-11-12.sql` (+ `_INVERSE`, + `_REPETITION`) : lecture de `app_ged_classement`
  au périmètre des documents (lecteur global, ou biens du portefeuille), SELECT seul pour authenticated, interrupteur
  `ged_recu_manque = off`. **Répétition : 5 OK, 0 KO** (admin voit les 3 classements, un négociateur 0 = ce qu'il doit
  voir, écriture directe refusée) ; rien n'est resté. ⚠ Pas de témoin positif côté négociateur (aucun n'a encore de
  classement sur ses biens). **PAS POSÉ.**
- Contrôles : `npm run build` vert ; `test_ged_recu_manque.cjs` **29 VERT** ; `test_ged_depot.cjs` 17 VERT ; les 5 essais
  de la signature verts ; écran vu sur une page d'essai à données fictives (bureau 1280 × 665 : bloc de 349 px ;
  téléphone 375 : rien ne déborde ; clic sur une pièce → type pré-choisi).
✅ **« Oui, les quatre » (12/11)** : patch m3 **POSÉ EN PRODUCTION**, contrôles relus **5 VERT** ; commité, poussé ;
`ged_recu_manque` allumé en `admin` (les 4 admins actifs). ⏳ Reste : le voir sur de vrais biens (un actif, un sous offre,
un sous compromis) et juger la liste avec Frédéric.

### 12.9 Le morceau 4 — l'IA classe avant l'envoi (audit du 12/11, rien codé)
**Audit (lecture seule)** :
- L'interrupteur existe déjà : `ged_lecture_ia` (posé par le morceau 1, éteint), sa description dit « le classement par
  l'IA avant l'envoi et la lecture des valeurs après ». **Aucun patch de base n'est nécessaire** : `app_ged_classement`
  porte déjà `type_propose` / `type_propose_par` (contrainte `'ia' | 'nom'`), `app_ged_classer` les accepte, et
  `app_agent_run` (journal des agents, 16 lignes `redacteur`, dernière le 23/07, 0,011 $ en tout) reçoit tokens et coût.
- Le backend Render appelle déjà OpenAI : `openai_listing_sheet_service.py` (`/v1/responses`, image en `input_image`,
  schéma non strict, **sans `store:false`**, sans relevé d'usage), registre `agent_registry.py` (fiche en code, surchargée
  par `app_agent_prompt`), modèle par défaut `OPENAI_VISION_MODEL` = `gpt-4.1-mini`. La route `/annonces/scan-fiche`
  vérifie le jeton et le rôle (`load_profile`).
- Le navigateur n'a **aucun lecteur de PDF** : `pdf-lib` assemble mais ne dessine pas une page et ne lit pas son texte.
  Le backend non plus (`requirements.txt` : ni PyMuPDF ni pypdf).
- La fenêtre de dépôt (`DepotDocuments.tsx`) propose le type par le nom (`typeParNom`) et l'enregistre avec
  `typeProposePar: 'nom'` ; doc, xls, zip et txt passent aussi par elle.

**Proposition** :
- Tout se décide DANS LE NAVIGATEUR avant qu'un octet sorte : `pdfjs-dist` (chargé à la demande) dessine des vignettes
  basse définition (512 px, au plus 12 pages : les 8 premières et les 4 dernières) et lit la couche texte.
  ⛔ Garde RIB chez nous : nom « RIB », type choisi `justif.rib` ou un des 5 types `jamais_envoye`, ou un IBAN /
  « relevé d'identité bancaire » dans le texte → AUCUN envoi. Doc, xls, zip, txt : jamais envoyés (le nom seul).
- Le backend (route neuve `POST /ged/classer`, fichier neuf) revérifie : jeton, admin actif si l'interrupteur est sur
  « admin », interrupteur allumé, **refus si le texte reçu porte un IBAN** (deuxième verrou), plafond de 2 $ par jour.
  Appel `store:false`, schéma STRICT : type parmi les 60 codes, confiance, nom proposé (jamais un nom de personne), pièces
  (plages de pages et type), pièce sensible oui / non. Ni la fiche du bien ni le nom du mandant ne partent. Journal :
  une ligne `app_agent_run` `ged_classement` (tokens, coût, type et confiance ; aucune valeur lue).
- À l'écran : « Lecture du type… » sur la ligne ; nom muet ou type seulement probable → le type de l'IA est pré-choisi,
  marqué « proposé par l'IA, à vérifier » ; nom sûr et IA en désaccord → la proposition s'affiche, rien ne change sans
  clic ; confiance basse → proposée, pas pré-choisie. Si l'IA dit RIB : seul le type est gardé. Plusieurs pièces dans un
  PDF → « Séparer en N fichiers » (pdf-lib, déjà chargé), un clic. L'envoi reste possible sans attendre l'IA.
- Retour arrière : `ged_lecture_ia = off` (plus aucun appel) ; le code se retire par `git revert`.
- ⚠ Avant le 1er document réel : contrat de sous-traitance (DPA) d'OpenAI accepté par Frédéric ; le premier essai se fait
  sur des documents FICTIFS (un faux DPE, un faux RIB dont on prouve qu'il ne part pas).
✅ **« Vas-y, morceau 4 » (12/11). ÉCRIT ET CONTRÔLÉ, PAS ENCORE EN SERVICE (rien poussé, interrupteur éteint) :**
- Serveur (Render) : `backend/app/services/ged_garde_rib.py` (2e verrou : IBAN à clé de contrôle vérifiée, « relevé
  d'identité bancaire », nom « RIB » / « IBAN ») ; `backend/app/services/openai_ged_classement_service.py` (fiche d'agent
  `ged_classement` ajoutée au registre, modèle `gpt-6-luna` sans raisonnement, `store:false`, images `detail: low` refusées
  au-delà de 400 Ko, schéma STRICT dont le type ne sort que de `app_ged_type`, plafond de 2 $ par jour lu dans
  `app_agent_run` — une lecture ratée de la dépense = pas d'appel ; un RIB vu par l'IA ne garde que son type ; un nom
  proposé portant un long numéro ou un @ est jeté) ; `backend/app/routers/ged.py` (`POST /ged/classer` : jeton, admin
  actif au cran « admin », interrupteur relu à chaque appel ; journal `app_agent_run` avec type, confiance et coût, SANS
  le nom proposé ni la remarque) ; `main.py` +2 lignes.
- Navigateur : `pdfjs-dist` 4.10.38 (chargé à la demande, morceau à part de 335 Ko) ; `src/lib/gedClassementIa.ts`
  (vignettes 512 px des pages 1-8 et des 4 dernières, garde RIB sur le texte de TOUTES les pages jusqu'à 150 avant toute
  vignette, extrait de 6 000 caractères, appel au serveur, séparation d'un PDF par pdf-lib, `useGedLectureIa`) ;
  `DepotDocuments.tsx` (file une ligne à la fois ; pré-choix seulement si le nom n'est pas sûr, que personne n'a choisi et
  que l'IA ne devine pas ; sinon « L'IA pense : … [Prendre ce type] » ; « Séparer en N fichiers » ; « Redemander » sur
  erreur ; le classement retient `type_propose_par = 'ia'` quand l'IA a répondu) ; `.css` +3 lignes.
- Contrôles : `backend/tests/test_ged_classer.py` **28 VERT** (aucun appel réseau) ; `test_ged_classement_ia.cjs`
  **25 VERT** (mêmes exemples RIB que le serveur) ; témoins inverses : sans le 2e verrou l'essai serveur tombe, garde du
  navigateur cassée → 4 ROUGE ; `npm run build` vert ; `test_ged_depot` 17, `test_ged_recu_manque` 29 et les 5 essais de
  la signature verts ; le serveur complet s'importe (`/ged/classer` monté). ⚠ `tests/test_rapprochement_email.py` était
  déjà rouge (« Voir ce bien » absent du HTML, fichier du 27/09, sans lien) — noté, pas touché.
- **Banc réel sur 2 documents ENTIÈREMENT FICTIFS** (service appelé directement, rien écrit en base) : photo muette d'un
  DPE → `diag.dpe`, confiance haute, 5,6 s ; scan de 4 pages → compromis + état des risques p. 4 vus comme 2 pièces,
  3,9 s ; **0,0006 $ les deux** (≈ 2 300 à 3 000 jetons lus, surtout la liste des 66 types).
- Écran vu sur une page d'essai (serveur simulé qui NOTE chaque demande) : 4 fichiers fictifs déposés → 3 demandes, **le
  faux relevé portant un IBAN n'a fait AUCUNE demande** (« Un IBAN est dans le texte : jamais envoyé à l'IA », type RIB,
  privé imposé) ; photo muette → type et nom pré-choisis ; « DPE mars 2024 » (nom sûr) garde DPE, l'avis de l'IA se
  montre ; « Séparer en 2 fichiers » → 3 pages + 1 page, deux lignes typées. Téléphone 375 px : rien ne déborde.
✅ **« Oui, commite et pousse » (12/11)** : commit `a61db50` POUSSÉ ; Render a redémarré dessus à 14:51 (`/health` rend
`a61db50`), `/ged/classer` sans jeton répond 401 (la route existe et refuse).
✅ **DÉCISION DE FRÉDÉRIC (12/11)** : « je suis le seul à l'utiliser, on fera le DPA à la fin du dev » → `ged_lecture_ia`
**ALLUMÉ en `admin` le 12/11 à 14:58** (⚠ cran admin = les 4 admins actifs). ⛔ Le DPA d'OpenAI reste OBLIGATOIRE avant
l'arrivée des négociateurs (cran `on`). Éteindre : `update public.app_setting set value = 'off', updated_at = now() where key
= 'ged_lecture_ia';`

### 12.10 Le morceau 5 — les 13 règles sans IA (audit du 12/11, rien codé)
**Audit (lecture seule)** — catalogue : `E_synthese_catalogue.md` §3.1 (N1 à N13).
- ⭐ **Cinq règles sont DÉJÀ couvertes par « Reçu / Manque »** (morceau 3, `gedPieces.ts`) : N1a mandat non trouvé, N3
  pièce d'identité, N4 état des risques non trouvé, N6 audit (maison E/F/G), N7 pièces de copro du compromis. Les recoder
  ferait deux fois la même ligne à l'écran.
- **Restent les croisements**, et leurs sources existent toutes, sans patch de base :
  N1b signature seulement en attente sur un bien diffusable (`app_signature_request.status`, lecture déjà faite par
  l'écran, `api.ts:10392`) ; N1c sous offre / compromis sans mandat signé (statut × pièce) ; N2 baisse de prix ≥ 3 % après
  le début du mandat sans avenant (`app_dossier_current.price_change_last_*` × `mandat_date_debut` : **99 baisses
  mesurées le 12/11**, le journal ne commence que le 20/06) ; N4 état des risques déposé il y a plus de 6 mois
  (`created_at_hektor` / `created_at` du document : la date du DÉPÔT, pas de l'état) ; N5 DPE échu sur la fiche (calcul
  pur, `dpe_date` de la fiche décodée deux fois) ou bien bâti diffusé sans DPE ; N8 case copropriété à NON avec des pièces
  de copro au dossier (alerte seulement, jamais remplir) ; N9 lots ou charges vides sur un bien en copro ; N10 un document
  d'offre / compromis / acte sans la transaction au registre (`app_affaire_ledger`, lecture déjà faite par l'écran) ;
  N11 offre ou compromis daté après la fin du mandat (« selon le cas » si la tacite reconduction n'est pas lisible) ;
  N12 date d'acte prévue passée sans acte au dossier.
- ⚠ **N13 « déjà déposé sur un AUTRE bien »** : pas d'index sur `app_console_document.sha256`, une recherche = **630 ms
  de lecture complète** (193 632 lignes, mesuré). Le même bien est déjà couvert (morceau 2). L'index se pose
  `CONCURRENTLY`, mais sur la table de la session signature : son accord d'abord.
- ⚠ N12 « vente de plus de 30 jours sans facture » : un bien vendu sort de `app_dossier_current` ; non mesuré par quel
  chemin sa fiche s'ouvre — à vérifier avant de la promettre.
- Décision de l'étude encore ouverte : **n° 5, l'état des risques du compromis est-il refait par le notaire ?** Si oui,
  N4 au compromis devient une simple information (77 compromis sur 92 sonneraient sinon).

**Proposition** : une fonction pure `lib/gedRegles.ts` (comme `gedPieces.ts`, essais hors ligne), affichée dans le bloc
« Reçu / Manque » sous un titre « À regarder », une ligne par règle qui sonne, toujours « non trouvé », jamais
« absent » ; derrière l'interrupteur déjà posé `ged_propositions` (sa description couvre « alerte, pièce manquante »),
allumé en `admin` sur accord. Rien n'écrit, rien ne part chez Hektor.
⏳ Attend le « vas-y » de Frédéric et la réponse à la question n° 5.
✅ **« Vas-y, morceau 5 » (12/11). ÉCRIT ET CONTRÔLÉ, PAS POUSSÉ, `ged_propositions` reste éteint :**
- `src/lib/gedRegles.ts` (fonction pure) : N1b, N1c, N2, N4 (âge), N5 (échu / diffusé sans DPE), N8, N9 (lots, quote-part),
  N10 (offre ; compromis ou acte), N11 (une ligne par sorte), N12. Les dates vides de Hektor (`0000-00-00`) et la date zéro
  (`1970-01-01`) ne sont pas des dates. Validité du DPE : avant 2018 → 31/12/2022, jusqu'au 30/06/2021 → 31/12/2024, puis
  10 ans. ⚠ **Question n° 5 non tranchée : N4 au compromis est posé en simple INFORMATION** (alerte à l'offre) — à
  changer d'un mot si Frédéric répond « non, le notaire ne le refait pas ».
- `RecuManque.tsx` : section « À regarder (N) » au-dessus des pièces, alertes d'abord, informations à la fin ; une ligne
  qui a une pièce à déposer ouvre la fenêtre de dépôt avec ce type ; registre lu par `loadAffairesForDossier` (lecture
  ratée = les règles se taisent) ; état de signature par `etatFiableDuDocument` ; un document `hektor_console_modele` n'est
  PAS un mandat papier signé. `lib/ged.ts` : `useGedPropositions`. `App.tsx` : `faitsGedDuBien` rend `FaitsRegles`
  (+ diffusion, date du DPE, lots, quote-part, prix, dates du mandat) et le bloc reçoit `appDossierId`.
- ⭐ **Deux règles mentaient, vues par la mesure, pas par les essais** : (1) les charges — `CHARGES` vaut 0 sur 684 fiches
  sur 714, la mention de l'annonce est la **quote-part annuelle** (`copropriete_quote_part`, remplie sur 87 copros sur
  114) : 88 → **26** (le chiffre de l'étude) ; (2) un modèle de mandat généré par Hektor faisait taire « sans mandat
  signé » comme un papier.
- **Mesure sur les 714 biens en cours** (lecture seule, mêmes fonctions que l'écran) : N1b 1 · N1c 10 · N2 21 · N5 échu 3,
  diffusé sans DPE 15 · N8 12 · N9 lots 7, quote-part 26 · N10 offre 11, compromis / acte 104 (⚠ sur des biens actifs :
  presque toujours l'acte de la vente PRÉCÉDENTE, donc le titre de propriété — information seulement) · N11 16 · N12 14 ·
  N4 au compromis non compté (information). **209 biens sur 714 ont au moins une ligne, 3 au plus.** N1b sonne peu :
  sur 24 biens diffusés avec une signature en attente, 17 ont aussi un mandat signé et 5 un PDF papier.
- Contrôles : `test_ged_regles.cjs` **39 VERT** (chaque règle a son témoin qui se tait) ; témoin inverse (avenant ignoré
  → 2 ROUGE) ; `npm run build` vert ; GED 29 / 17 / 25 et les 5 essais de la signature verts ; écran vu sur une page
  d'essai (6 lignes, clic « Baisse de prix » → dépôt d'un « Avenant au mandat » ; le mot « absent » n'apparaît pas ;
  téléphone 375 px sans débordement, mais le bloc fait 1 142 px dans le pire cas).
- Non fait : N13 sur un autre bien (index `sha256` à poser avec l'accord de la session signature) ; N12 « vente sans
  facture » (un bien vendu sort de `app_dossier_current`).
✅ **« Oui, les trois » (12/11)** : commit `8509638` POUSSÉ ; `ged_propositions` **allumé en `admin` à 15:29** (les 4 admins
actifs). Éteindre : `update public.app_setting set value = 'off', updated_at = now() where key = 'ged_propositions';`
⏳ Reste : Frédéric juge les lignes « À regarder » sur ses biens (vrai / faux / déjà su).
✅ **QUESTION N° 5 TRANCHÉE (12/11)** : « C'EST NOUS, COMME LES AUTRES DIAGNOSTICS » → l'agence annexe l'état des risques au
compromis : N4 est une **ALERTE** au compromis comme à l'offre, comparée à la date de SIGNATURE du compromis (aujourd'hui à
l'offre).
⚠⚠ **EN LE FAISANT, LA MESURE A TROUVÉ QUE N4 NE POUVAIT JAMAIS SONNER** : la date d'un document venu de Hektor n'est pas
connue chez nous — `created_at_hektor` est vide sur les 94 états des risques des biens sous compromis, et `created_at` est le
jour où NOTRE ligne est née (86 en octobre 2026 : les lignes recréées par le défaut du domaine). Les essais passaient, la
règle était muette. **Corrigé** : `deposeAuPlusTard()` prend la plus petite borne entre nos dates et le numéro Hektor du
document (`hektor_uploaded_document_id`, croissant) calé sur 13 points relevés le 12/11 (maximum cumulé par jour ; trous
connus 19/05→26/06 et 20/08→05/10). La règle ne sonne que si même la borne a plus de 6 mois : elle peut se taire à tort,
jamais crier à tort. ⚠ **Conséquence mesurée : aucune ligne N4 avant le 18/11/2026** (nos données commencent le 19/05) ; la
vraie date de l'état viendra de sa lecture (morceau 6, L2). Essais 44 VERT ; mesure : 218 biens sur 723 avec une ligne.

### 12.11 Le morceau 6 — les fiches de lecture (audit du 12/11, rien codé)
**Audit (lecture seule)** — catalogue : `E_synthese_catalogue.md` §3.2 (L1 à L19) et §5 (14 fiches, 19 types lus) ; forme
commune `3_analyste_ia_rgpd.md` §2 (`$defs` stricts `txt` / `num` / `date` / `personne`, états `lu` / `incertain` /
`non_vu`, interdits partout : naissance, numéros fiscaux, IBAN, pièce d'identité, adresse personnelle, santé).
- **Rien n'existe pour garder une valeur lue** : ni table, ni colonne. Il faut un patch de base (deux tables neuves).
- **Le fichier** : après « Envoyer », il est au coffre (`temp/uploads`, puis sa place définitive par le worker) ; le
  serveur sait faire une adresse signée (`supabase_storage.create_signed_url`) mais **ne sait pas lire un PDF** (ni PyMuPDF
  ni pypdfium2 dans `requirements.txt`). Le navigateur, lui, a encore le fichier ET sait le lire (`pdfjs-dist`, morceau 4).
  ⚠ §12.1 disait « fichier déjà au coffre » : lire depuis le coffre toucherait la place des documents de la session
  signature (prévenir d'abord) et ajouterait une bibliothèque au serveur.
- Le classement (morceau 2) est créé à l'envoi et porte le travail : une lecture s'y accroche sans toucher
  `app_console_document`.
- Les personnes : les fiches 4 (compromis) et 5 (mandat) lisent des NOMS (vendeurs, acquéreurs, mandants) pour la
  résolution de la cible ; jamais de date ni de lieu de naissance (schéma strict). DPA : décision du 12/11, à la fin du dev.

**Proposition** :
- **La lecture part du navigateur, juste après l'envoi** (le fichier y est encore) : texte du PDF quand il suffit, sinon
  les pages utiles en haute définition, vers une route neuve du serveur `POST /ged/lire` (même portier que `/ged/classer` :
  jeton, interrupteur `ged_lecture_ia`, plafond du jour, garde RIB, `store:false`), qui vérifie que le classement est bien
  celui de l'utilisateur, appelle la fiche du type et ÉCRIT la lecture (clé de service). ⚠ Fenêtre fermée avant la
  lecture = document non lu (un bouton « Lire » viendra si besoin).
- **Base** : `app_ged_lecture` (une par document lu : classement, type, version de la fiche, modèle, coût, état) et
  `app_ged_valeur` (clé, valeur, page, état) ; lecture au même périmètre que les classements ; aucune écriture par l'écran.
- **Livré en 4 lots**, chacun commité et essayé : lot 1 l'état des risques, le DPE et le dossier de diagnostics (fiches
  1 à 3) + la base + la route + l'affichage « Lu : … » ; lot 2 compromis et mandat ; lot 3 facture, acte, offre, avenant ;
  lot 4 titre, surfaces, petits diagnostics, copropriété, fin de mandat, annulation. Chaque lot a son jeu de documents
  FICTIFS de référence (valeurs attendues connues) passé au vrai modèle.
- Rien ne se compare ni ne s'écrit sur le bien ici (morceaux 7 et 8) ; seule exception utile tout de suite : la date LUE
  de l'état des risques remplace la date de dépôt « au plus tard » dans la règle N4.
✅ **« Vas-y, lot 1 » (12/11). ÉCRIT ET CONTRÔLÉ, RIEN POSÉ NI POUSSÉ :**
- Base : `supabase/patch_ged_m6_lecture_2026-11-12.sql` (+ `_INVERSE`, + `_REPETITION`) — `app_ged_lecture`, `app_ged_valeur`,
  lecture au périmètre des classements, aucune écriture par l'écran. **Répétition : 7 OK, 0 KO**, rien n'est resté (⚠ pas
  de témoin positif côté négociateur : 0 attendu, 0 vu).
- Serveur : `backend/app/services/openai_ged_lecture_service.py` (fiches `diag.erp`, `diag.dpe`, `diag.dossier`, schéma
  STRICT construit depuis la fiche, `ce_type` → « pas ce type », valeur hors forme jetée, page hors document effacée,
  pièce des personnes refusée jusqu'au morceau 9, garde RIB, `detail: high`, 6 pages au plus) ; route `POST /ged/lire`
  (`routers/ged.py` : même portier, le classement doit être celui de l'utilisateur — `decide_par` —, écrit la lecture et
  ses valeurs par la clé de service, coût au journal des agents) ; le plafond de 2 $ / jour compte classement ET lecture.
- Navigateur : `lib/gedClassementIa.ts` (`preparerLecture` : texte seul si les 3 premières pages ont ≥ 30 mots, sinon 4
  pages à 1 600 px ; garde RIB avant toute image ; `lireParIa`) ; `lib/gedLecture.ts` (types lus, résumé « Lu : … »,
  date de l'état, `loadGedLectures`) ; `DepotDocuments.tsx` (après l'envoi, une lecture à la fois, « L'IA lit les
  valeurs… » puis le résumé, « Relire » sur échec ; quitter la page pendant une lecture demande confirmation) ;
  `RecuManque.tsx` (le résumé à côté des pièces reçues ; la date LUE de l'état des risques fait foi dans N4).
- **Banc réel, 3 documents fictifs** : ERP en texte (date de l'état et non de l'arrêté de 2019, commune, INSEE), DPE
  scanné (numéro ADEME, 2 dates, classe, consommation, émissions), dossier de diagnostics (5 diagnostics, dates,
  conclusions, DPE E) : **12 valeurs sur 12** (« Saint-Étienne » rendu avec son accent) ; 3,7 à 5,6 s ;
  **0,0009 $ les trois**.
- Contrôles : `backend/tests/test_ged_lire.py` **17 VERT** + `test_ged_classer.py` 28 ; témoin inverse (sans le contrôle
  du propriétaire, l'essai tombe) ; `test_ged_lecture.cjs` **15 VERT** ; règles 44, Reçu / Manque 29, dépôt 17,
  classement 25 et les 5 essais de la signature verts ; `npm run build` vert ; le serveur s'importe (`/ged/lire` monté) ;
  écran vu sur une page d'essai (« ERP 2026.pdf — Lu : établi le 01/12/2025 · Saint-Étienne. » ; N4 « établi le
  01/12/2025 : plus de 6 mois au compromis du 01/07/2026 »).
- ⚠ Non vu : la file des lectures dans la vraie fenêtre de dépôt (le banc ne simule pas l'envoi) — premier vrai essai.
⏳ Ordre des gestes, sur accord : 1. POSER le patch (avant le serveur : sinon la lecture paierait l'appel puis échouerait
à l'écriture) ; 2. commit ; 3. push ; 4. essai réel sur un document fictif déposé sur 62774.
✅ **« Oui, les trois » (12/11)** : patch m6 **POSÉ** (contrôle : 2 tables, RLS, SELECT seul pour authenticated, 0 droit
anon, 2 règles de lecture, 0 ligne) ; commit `c631a6d` **POUSSÉ** ; Render a redémarré dessus à 15:56, `/ged/lire` sans
jeton → 401. ⚠ **Le push a emporté `1942d3f`** (étiquettes, AUTRE session : une note et 2 fichiers SQL déjà posés, aucun
code d'app), commité SOUS le mien : relecture et push étaient dans la même commande. Frédéric prévenu.
⏳ Reste : l'essai réel (un état des risques fictif déposé sur 62774).

### 12.12 ⚠ L'ÉCRAN NE SUIT PAS LA MAQUETTE (remarque de Frédéric, 12/11 soir) — audit, rien codé
Frédéric : « le rendu design graphique et visuel de la modale n'est pas identique à la maquette du chantier ». **Il a
raison.** Maquette de référence : https://claude.ai/artifact/WEHAruTgvuctKN74N8Rt6r (version 10), écrans E0 à E6.
Comparaison faite écran par écran (maquette servie en local, captures) :
- **E0, l'onglet Documents** : maquette = UN bouton « Déposer des documents » dans l'en-tête du panneau ; « Reçu /
  manque » en lignes serrées (coche verte ou cercle vide, cadenas pour les pièces des personnes, « Manque : glisse le
  fichier ici » sur fond hachuré, on peut y DÉPOSER un fichier). Construit : le bloc en cartes avec bordures pointillées,
  « Non trouvée : déposer », les reçues repliées.
- **E1 / E1-bis / E2 / E3 / E4, la fenêtre de dépôt** : maquette = une **FENÊTRE (modale)** à en-tête sombre (« Déposer des
  documents », le bien, pastilles « Mise en vente », « Mandat 1234 », croix), grande zone de dépôt, ligne « Il manque pour
  la mise en vente : … » ; puis une **liste à gauche** (vignette, nom modifiable, type en pastille-menu, nom du fichier et
  pages, cadenas de visibilité, pastille d'état « Prêt » / « À vérifier » / « Déjà là » / « Non envoyé ») et un **aperçu à
  droite** (la page, « page 1 / 12 », « Ouvrir en grand », fichier, type, d'où vient le type, visibilité) ; compteurs
  (« 9 fichiers · 6 prêts · 2 à vérifier · 1 déjà dans ce dossier »), filtres « Tous / À vérifier », « + Ajouter » ; pied
  « Fermer » + « Envoyer N documents » ; les cas particuliers (E3) dans la même liste, l'explication et les gestes dans
  l'aperçu ; fermer avant d'envoyer (E4) = une bande DANS la fenêtre (« Envoyer maintenant » / « Fermer sans envoyer »).
  Construit : un bloc DANS le panneau, des lignes de champs (nom, menu de type, Privé / Public, état), sans aperçu, sans
  compteurs ni filtres, et un avertissement du navigateur au lieu de la bande.
- **E5, « À vérifier » après l'envoi** : maquette = des cartes étiquetées (« Remplir », « Alerte ») avec leurs gestes.
  Construit : « À regarder » (morceau 5) en lignes du bloc Reçu / Manque. ⚠ La maquette n'a pas d'écran pour les règles
  sans IA : elles iraient dans ce bloc E5, avec l'étiquette « Alerte ».
**Cause** : j'ai codé les morceaux 2 à 6 sur le FONCTIONNEMENT de la maquette en gardant le style des formulaires du
panneau, sans la rouvrir pour l'habillage. ⛔ Leçon : une maquette validée se suit À L'ÉCRAN, pas seulement dans le texte.
**Proposition** : refaire l'habillage SANS changer ce que fait l'outil (mêmes gestes, mêmes données, mêmes interrupteurs) :
la fenêtre modale E1-E4 (avec l'aperçu de page par la bibliothèque PDF déjà chargée), le bloc E0, et « À regarder » au
format des cartes E5. Les places de l'IA (type proposé, « Lu : … », « Séparer ») vont dans l'aperçu (« D'où vient le type :
l'IA », la lecture sous l'état). Environ 2 jours.
✅ **Décision de Frédéric (12/11 soir) : « On peut finir les codes et tests avant de faire l'habillage. »** L'habillage
passe APRÈS les morceaux 6 (lots 2 à 4) à 10 ; il reprendra ce §12.12 tel quel, maquette rouverte écran par écran. En
attendant, chaque morceau garde le style actuel du bloc, sans en inventer un troisième.

### 12.13 Le morceau 6, lot 2 — le compromis et le mandat (audit du 12/11 soir, rien codé)
**Audit (lecture seule)** — fiches 4 et 5 du catalogue (`E_synthese_catalogue.md` §5) ; mandat : `3_analyste_ia_rgpd.md`
§2.5 corrigé par l'étude A ; compromis : étude C §3.2. Types en base : `mandat.vente` et `transaction.avant_contrat`,
tous deux NON sensibles (vérifié).
- **Ce que le lot 1 ne sait pas faire et que le lot 2 exige** :
  1. **Des NOMS.** La consigne commune dit « ne recopie jamais un nom de personne » ; les fiches 4 et 5 lisent les
     mandants, vendeurs et acquéreurs (nom, prénoms, qualité, page — jamais naissance, adresse, régime, état civil), pour
     que le morceau 7 reconnaisse les parties (CPV-6 : un mandant absent des vendeurs). → l'interdit devient « sauf dans
     la liste des parties de la fiche ».
  2. **Les DERNIÈRES pages et une IMAGE même quand il y a du texte.** Signatures et date en dernière page ; cases cochées à
     la main (exclusif / simple ; qui paie les honoraires — les deux cases peuvent être cochées : `les_deux`) invisibles
     dans la couche texte. Le lot 1 envoie le texte seul OU les 4 premières pages. → pour ces deux types : tout le texte
     ET les images de la page 1, de la page des honoraires (trouvée dans le texte) et des deux dernières (5 au plus,
     sous le plafond serveur de 6).
  3. **Un texte plus long.** Un compromis fait 20 à 40 pages ; 20 000 caractères s'arrêtent avant la date limite du prêt.
     → 80 000 caractères pour ces deux fiches seulement (≈ 20 000 jetons, ≈ 0,002 $ ; non mesuré sur un vrai compromis).
- **Fiche 5, mandat** : numéro (chiffres seuls) + `numero_present`, type (exclusif / simple / semi_exclusif / autre),
  dates de signature / début / fin, durée, tacite reconduction, prix de présentation, net vendeur, honoraires € et %,
  `charge_honoraires` (vendeur / acquéreur / les_deux), commune, désignation courte, `signataire_represente` (oui / non,
  JAMAIS pourquoi), signatures des mandants (nombre), du mandataire (oui / non / illisible), date signée, signature
  électronique (oui / non), formulaire de rétractation ; liste `parties` (mandants).
- **Fiche 4, compromis** : date de signature, forme (en agence / chez le notaire), nature (compromis / promesse), prix,
  net vendeur, honoraires, qui les paie, mobilier, condition de prêt + date limite (JAMAIS montant, taux, banque),
  réitération au plus tard, séquestre et dépositaire, notaires (études : des professionnels), n° de mandat cité,
  signatures ; liste `parties` (vendeurs, acquéreurs).
- **Rien ne se compare ni ne s'écrit ici** (morceaux 7 et 8) ; le résumé « Lu : » ne montre pas les noms (« 2 vendeurs,
  1 acquéreur »).
- **Ce que ça pourrait casser ailleurs** : la consigne commune et le choix des pages ne changent QUE pour ces deux types
  (le lot 1 garde exactement son envoi, essais à l'appui) ; la base ne change pas (les noms vont dans `app_ged_valeur`,
  au périmètre du bien, comme les autres valeurs) ; aucune table de la signature n'est touchée. ⚠ Les noms des parties
  sont des données personnelles : déjà dans nos contacts, mais une copie de plus → au registre des traitements avec le
  DPA, à la fin du dev.
- **Essais** : hors ligne (schéma, normalisation, choix des pages, lot 1 inchangé) ; banc réel sur un mandat et un
  compromis FICTIFS (une case cochée à la main, signatures en dernière page, vraies valeurs connues) ; puis l'essai réel
  du lot 1 et du lot 2 ensemble sur 62774, sur accord.
⛔ **REMPLACÉ par le §12.14** (Frédéric, 12/11 soir : le mandat est édité par l'app, donc pas le plus utile ; les NOMS
sont obligatoires ; d'abord les justificatifs du mandat et de la mise en vente — titre, taxe foncière, copropriété).

### 12.14 L'ordre des lots revu sur les VRAIS documents (analyse du 12/11 soir, lecture seule, rien codé)
Demande de Frédéric : « analyse mes documents ; plus utile de savoir constituer les justificatifs du mandat puis ceux de la
mise en vente, beaucoup de vérifications avec les champs de l'annonce et des mandants ; compromis et offres intéressants,
les offres quasi similaires, les compromis de mises en page différentes ; tous les documents de copropriété, et surtout
titre de propriété et taxe foncière ». **Les noms sont obligatoires** (sans eux, pas de vérification avec les mandants).
- **Le mandat** : seuls les mandats passent par la signature de l'app (`app_signature_request.document_kind` = `mandat`,
  3 demandes, dernière le 06/11) ; un mandat récent est un PDF texte de 12 pages (46 / 50) : il sort de l'app → dernier lot.
- **Le rythme réel** (noms des documents déposés chez Hektor du 20/08 au 12/11, numéros Hektor ≥ 712 625, ≈ 2,8 mois) :
  pièces d'identité 300, offres 120, mandats 112, compromis 84, taxe foncière 63, titres 36, PV d'AG 26, état civil 22,
  charges de copro 20, règlement 8, carnet / DTG 6, fiche synthétique 4.
- **La forme** (script de lecture seule sur les 50 PDF les plus récents de chaque famille, au disque du serveur
  `HektorConsoleDocuments`, n'imprime que des nombres ; « ressemblance » = mots communs de la page 1, mesurable sur les
  seuls PDF à couche texte) :
  · **titre** : 9 pages (p90 40), **42 scans sur 50** (+ 1 338 photos JPG au total) ; ressemblance 0,12 ;
  · **taxe foncière** : 2 pages, 29 scans sur 50 ; ressemblance 0,45 (l'avis officiel, mise en page stable) ;
  · **fiche synthétique** : 2 pages, 19 textes sur 21 ; ressemblance 0,69 (formulaire réglementaire) ;
  · **charges de copro** : 1 page, 31 textes sur 50 ; ressemblance 0,14 (chaque syndic la sienne) ;
  · **PV d'AG** : 12 pages (p90 34), moitié scans ; ressemblance 0,15 ;
  · **règlement / EDD** : 34 pages (p90 65), 26 scans sur 29 ;
  · **compromis** : 39 pages (p90 54), 34 textes sur 50 ; ressemblance 0,26, **1 % de paires proches** → confirme
    Frédéric : des mises en page très différentes ;
  · **offre** : 1 page, **45 scans sur 50** (+ 1 435 photos) → la ressemblance ne se mesure pas sur un scan : « quasi
    similaires » n'est ni confirmé ni démenti ; ce qui est sûr : une page, presque toujours scannée ou photographiée.
- **Ce que ça change à la technique** : la lecture doit savoir lire des NOMS (liste « personnes » : nom, prénoms, qualité,
  droits — jamais naissance ni adresse) et des SCANS de plusieurs pages (le titre : les 6 premières pages en haute
  définition, où sont les parties et la désignation ; l'origine de propriété, plus loin, n'est pas lue).
- **Les vérifications servies au morceau 7** (étude A §6-7, D §4) : titre ↔ mandants (chaque propriétaire doit être
  mandant ; 39 biens à 3 propriétaires ou plus sans titre), commune du titre ; taxe : montant ↔ case `TAXE_FONCIERE`
  (97 biens vides avec un avis, 166 comparables), redevables ↔ mandants, commune, avis ancien ; copro : nombre de lots,
  charges (26 biens en copro sans charges), procédure, numéros de lot (57 vides), syndic à relier (73 sans syndic).
**Proposition (ordre de valeur)** :
- **Lot 2 — justificatifs du mandat et de la mise en vente** : taxe foncière, titre de propriété, fiche synthétique,
  charges de copro (appel de fonds / arrêté), avec les noms.
- **Lot 3 — la vente** : offre d'achat (une page scannée), compromis (texte long, mises en page variées), PV d'AG.
- **Lot 4 — le reste** : mandat déposé à la main, avenant, acte, facture, petits diagnostics, surfaces, règlement.
- ⚠ **La pièce d'identité est le justificatif le PLUS déposé (300 en 2,8 mois)**, mais c'est une pièce des personnes
  (morceau 9, registre anti-blanchiment, DPA) : elle ne rentre pas dans ces lots ; l'avancer est une décision de Frédéric.
✅ **« Oui vas-y » (12/11 soir)** : le lot 2 = taxe foncière, titre, fiche synthétique, charges de copro. Et « mets à
jour le plan de ce chantier » → le §0 en tête de cette note porte désormais l'état au présent.
✅ **LOT 2 ÉCRIT ET CONTRÔLÉ (12/11 soir), RIEN POSÉ NI POUSSÉ :**
- Serveur (`openai_ged_lecture_service.py`) : 4 fiches neuves — `justif.taxe` (année, montant total, ordures ménagères,
  somme à payer, commune et adresse DES BIENS, plusieurs biens ; redevables), `justif.titre` (nature et date de l'acte,
  étude, décès, commune, adresse, contenance, extrait partiel ; nouveaux propriétaires avec droits et quote-part ; lots et
  tantièmes), `copro.carnet` (fiche synthétique : immatriculation, lots, syndic société, budget, fonds de travaux,
  procédure, plan de sauvegarde), une fiche commune à `copro.appel_fonds` et `copro.arrete_charges` (provision, budget du
  lot, charges réelles, fonds de travaux, travaux appelés, lots, syndic ; JAMAIS le copropriétaire destinataire). Une fiche
  porte désormais PLUSIEURS listes. **Les noms** : liste `personnes` (nom, prénoms, qualité, + droits / quote-part pour le
  titre) sur la taxe et le titre SEULEMENT ; la consigne commune garde l'interdit « sauf dans la liste personnes quand la
  fiche la demande ». Gardes ajoutées : un « nom » avec un chiffre ou une arobase est jeté ; **un numéro de 9 chiffres ou
  plus (fiscal, de rôle) n'est gardé dans AUCUN champ**, même espacé ; 12 personnes au plus. Le titre : 40 000 caractères
  de texte et 6 pages en image (les autres types gardent 20 000 et 4).
- Écran : `gedLecture.ts` (8 types lus ; résumés « Lu : … » qui COMPTENT les personnes — « 2 redevables, 1 usufruitier » —
  sans jamais un nom ; la date d'une taxe ne peut plus passer pour celle d'un état des risques) ; `gedClassementIa.ts`
  (pages et texte réglés par type) ; `DepotDocuments.tsx` (le type est passé à la préparation, une ligne).
- Base : RIEN d'obligatoire (les valeurs vont dans `app_ged_valeur`). ⚠ Seule retouche proposée : la colonne
  `app_ged_type.lecture` dit encore « classer » pour la taxe (étiquette sans effet) → `patch_ged_m6_lot2_taxe_lue_2026-11-12.sql`
  (+ `_INVERSE`), à poser sur accord, ou pas.
- **Banc réel, 4 documents FICTIFS** (taxe scannée 2 pages, titre scanné 3 pages, fiche synthétique en texte, appel de
  fonds scanné) : **25 valeurs sur 25**, noms et qualités justes (le vendeur et l'ancien propriétaire de l'origine NON
  relevés ; un nom lu « FICTIF née ESSAI » : le morceau 7 devra savoir lire « née ») ; **0 fuite** sur 12 mots interdits
  (dates de naissance, ville et adresse du destinataire, numéro fiscal, référence d'avis, solde débiteur, régime, profession,
  copropriétaire de l'appel) ; 3,4 à 7 s ; **0,0028 $ les quatre**. Lot 1 rejoué : 12 sur 12 (« Saint-Étienne » avec son
  accent).
- Contrôles : `test_ged_lire.py` **38 VERT** (dont ce qui part vraiment vers l'IA, appel simulé, et 3 témoins « le lot 1
  ne change pas ») ; `test_ged_classer.py` 28 ; `test_ged_lecture.cjs` **25 VERT** ; règles 44, Reçu / Manque 29, dépôt 17,
  classement 25, les 4 essais de la signature verts ; `npm run build` vert.
✅ **« Oui avec patch taxe » (12/11 soir)** : patch de la taxe **POSÉ** (`justif.taxe` → « lue », contrôle vert) ; commit
`0466c7c`. La relecture avant le push a trouvé `f3ef0de` (autre session : un script d'essai du chaînage, `phase2/sync/`,
aucun code d'app) SOUS le mien → dit à Frédéric, qui a répondu « vas-y » → **les deux POUSSÉS** (`ee13b7c..0466c7c`, SHA
exact). Render (`/health` = `0466c7c`, `/ged/lire` sans jeton → 401) et Vercel (le paquet sert `justif.titre`) à jour.
✅ **ESSAI RÉEL DES LOTS 1 ET 2 — « Fais essai » (12/11, 19:20-19:25)**, Chrome de Frédéric, cran admin, bien d'essai
**62774** (⚠ il est « Clos » depuis l'essai du 21/10 : la fiche est en lecture seule, mais l'onglet Documents dépose quand
même). Worker vérifié AVANT : les 4 services ont démarré le 10/11 18:47, après l'anti-doublon `3c32daa` du 06/11.
- 5 documents FICTIFS (fabriqués par `essai_reel/fabriquer_scans.py` et `fabriquer_textes.cjs`, bloc-notes de la session) :
  état des risques (texte), taxe foncière (scan 2 p.), titre (scan 3 p.), fiche synthétique (texte), appel de fonds (scan).
- **Classement (morceau 4)** : 5 sur 5 « le nom et l'IA sont d'accord ».
- **Envoi chez Hektor** : 5 travaux `done` (18:21:21 → 18:23:16 UTC), numéros Hektor **716030 à 716034**, consécutifs,
  **aucun doublon** (le bien passe de 18 à 23 documents).
- **Lecture (morceau 6)** : la file a lu les 5, une à une, juste après l'envoi ; les résumés s'affichent dans la fenêtre :
  « établi le 02/09/2026 · Firminy » ; « taxe 2026 · 1 234 € · FIRMINY · 1 redevable, 1 usufruitier » ; « acte de vente ·
  du 04/03/2019 · 2 propriétaires · FIRMINY · lots 12, 31 » ; « 48 lots dont 20 principaux · syndic SYNDIC EXEMPLE LOIRE
  SAS · aucune procédure · établie le 30/06/2026 » ; « provision 420 € (trimestre) · travaux appelés 1 200 € · lots 12, 31
  · syndic … ». **Aucun nom à l'écran.**
- **En base** : 5 `app_ged_lecture` (état « lu » ; texte pour les 2 PDF texte, pages 1-2 / 1-3 / 1 pour les scans) ;
  valeurs justes (contenance « 4 a 50 ca » → 450 m², tantièmes, quote-part « moitié ») ; **0 fuite** (le seul mot attrapé
  par mon filtre était l'immatriculation attendue « AB1234567 ») ; journal des agents : 5 lectures, **aucun nom** ;
  **coût total classement + lecture : 0,0041 $**.
- **Après rechargement** : « Mise en vente : 1 pièce sur 4 » (l'état des risques compte, son résumé « Lu : établi le
  02/09/2026 » à côté) ; et une règle du morceau 5 a parlé d'elle-même : « Case copropriété à NON, mais 2 pièces de
  copropriété au dossier » (vrai : 62774 n'est pas en copro).
- ⚠ **Trouvé** : après rechargement, les lectures de la taxe, du titre et des pièces de copro ne se VOIENT nulle part
  — « Reçu / Manque » ne montre que le moment en cours (ici la mise en vente) et, des moments précédents, les seules
  pièces obligatoires manquantes ; la taxe et le titre (moment « mandat », bonne pratique) et la copro (bien sans copro)
  n'y apparaissent pas. Les valeurs sont en base ; c'est l'affichage qui manque → à traiter au morceau 7 (les règles les
  utiliseront) et à l'habillage (aperçu du document, cartes E5).
- Les 5 documents fictifs restent sur 62774 (chez nous et chez Hektor) ; les retirer = un geste « Supprimer » par
  document, sur accord.
✅ **« Règle d'abord » (12/11 soir) — L'AFFICHAGE DES LECTURES APRÈS RECHARGEMENT, ÉCRIT, RIEN POUSSÉ** : dans « Reçu /
Manque », une ligne repliée **« ▸ Lu par l'IA : N documents »** (sous les pièces reçues, au style actuel du bloc) liste
CHAQUE document lu avec son résumé, quel que soit son moment (`RecuManque.tsx`, additif : aucune ligne existante ne
change). Banc d'écran local (lectures factices : état des risques, DPE, taxe, titre) : la ligne se déplie et montre
« Taxe fonciere 2026.pdf — Lu : taxe 2026 · 1 234 € · FIRMINY · 1 redevable, 1 usufruitier » et « Titre de
propriete.pdf — Lu : acte de vente · du 04/03/2019 · 2 propriétaires · lot 12 », aucun nom. Essais : `test_ged_lecture.cjs`
26 VERT, Reçu / Manque 29, règles 44, `npm run build` vert. ✅ « Oui » puis « Pousse » : commit `49dab5d`, poussé avec
`c6f79e9` et `7af2b99` (autre session : deux scripts d'essai du chaînage, aucun code d'app, dits AVANT, accord donné).
**VU EN PRODUCTION sur 62774** (Chrome, après rechargement) : « ▾ Lu par l'IA : 5 documents » montre les 5 résumés.

### 12.15 Le morceau 6, lot 3 — l'offre d'achat, le compromis, le PV d'AG (audit du 12/11 soir, rien codé)
**Audit (lecture seule)** — fiches : étude C §3.1 (offre) et §3.2 (compromis), étude D §3.1 (PV d'AG). Types en base :
`transaction.offre` et `transaction.avant_contrat` « lue », NON sensibles ; **`copro.pv_ag` encore « classer »** (même
cas que la taxe) ; `transaction.financement` reste une pièce des personnes (morceau 9), jamais lue ici.
- **La forme des vrais fichiers** (mesure du §12.14) : offre = 1 page, 45 scans sur 50 ; compromis = 39 pages, 34 textes
  sur 50, mises en page toutes différentes ; PV d'AG = 12 pages (p90 34), moitié scans.
- **Où sont les valeurs d'un compromis** (script de lecture seule sur les 40 compromis à couche texte les plus récents,
  n'imprime que des nombres, `position_valeurs_compromis.py`) : texte total **124 000 caractères** en médiane (p90 162 000) ;
  1re mention du prix ≤ 29 000 (40/40), de la réitération ≤ 36 000 (40/40), de la condition de prêt médiane 35 000, p90
  51 000, max 84 000 (32/40 la citent), des honoraires p90 63 000 (40/40). → **80 000 caractères** couvrent le prix, la
  réitération, 31 conditions de prêt sur 32 et 39 honoraires sur 40 ; les 20 000 du lot 1 en perdraient la moitié.
  Les signatures sont à la FIN → il faut aussi l'IMAGE des deux dernières pages, même quand il y a du texte.
- **Ce que ça demande de neuf** : un envoi « texte ET images des dernières pages » (le lot 1 et le lot 2 envoient l'un OU
  l'autre) ; pour un compromis scanné, les 4 premières pages et les 2 dernières en image (6, le plafond) — les valeurs du
  milieu d'un scan de 40 pages resteront « non vues » (dit, pas caché).
- **Fiche offre** : montant, base (frais d'agence inclus / net vendeur), date de l'offre, validité, condition de prêt
  (oui / non — JAMAIS montant, apport, banque), réponse du vendeur (acceptée / refusée / contre-proposition / non signée)
  et sa date, nombre de signatures, n° de mandat ou adresse du bien ; **personnes = les acquéreurs** (nom, prénoms).
- **Fiche compromis** : date de signature, forme (en agence / chez le notaire), nature (compromis / promesse), prix, net
  vendeur, honoraires, qui les paie, mobilier, condition de prêt et sa date limite (JAMAIS montant, taux, banque),
  réitération au plus tard, séquestre et dépositaire, études notariales, n° de mandat ; **personnes = vendeurs et
  acquéreurs** (qualité « vendeur » / « acquéreur »).
- **Fiche PV d'AG** : PV ou convocation, date, ordinaire / extraordinaire, syndic (société seulement), budget voté,
  cotisation au fonds de travaux, procédure (mandataire ad hoc, administration provisoire, plan de sauvegarde) ; liste des
  **travaux votés** (objet, montant pour l'immeuble, dates du 1er et du dernier appel). **AUCUN nom** : ni copropriétaires,
  ni feuille de présence, ni débiteurs, ni votes nominatifs.
- **Ce que ça pourrait casser ailleurs** : rien pour les lots 1 et 2 (réglages par type, témoins dans les essais) ; la base
  ne change pas, sauf l'étiquette de `copro.pv_ag` (« classer » → « lue », patch facultatif comme la taxe) ; coût d'un
  compromis ≈ 20 000 jetons de texte + 2 images ≈ 0,003 $.
- **Essais** : hors ligne, puis banc réel sur une offre scannée, un compromis long FICTIF (valeurs placées au milieu,
  signatures en dernière page) et un PV FICTIF (feuille de présence et débiteur nommé qui NE doivent PAS sortir) ; puis
  essai réel sur 62774, sur accord.
✅ **« Vas-y » (12/11 soir) — LOT 3 ÉCRIT ET CONTRÔLÉ, RIEN POSÉ NI POUSSÉ :**
- Serveur : 3 fiches (`transaction.offre`, `transaction.avant_contrat` — 80 000 caractères —, `copro.pv_ag` — 40 000 —) ;
  qualités « vendeur » / « acquéreur » ; consigne commune aux deux pièces de vente : signatures sur les DERNIÈRES pages
  montrées en image, JAMAIS le prêt (montant, taux, durée, banque, apport). PV : aucune personne ; ⭐ **« aucune
  procédure » ne PEUT PAS se lire sur un PV** (le banc l'a vu déduire « aucune » d'un PV muet : retiré des réponses
  possibles, un PV ne prouve pas l'absence — étude D, COPRO-5). `par_texte` vaut désormais « du texte a été envoyé »
  (vrai aussi quand des images l'accompagnent).
- Écran : `pagesAImager()` (avec texte : les dernières pages si le type les veut ; scan : les premières, et les
  dernières à la place des suivantes) — compromis 80 000 car. + 2 dernières pages, scanné 1-4 + 2 dernières ; offre :
  sa dernière page en image même avec du texte ; PV comme le titre ; résumés « Lu : … » (parties COMPTÉES, jamais nommées).
- **Banc réel, 3 documents FICTIFS** : offre scannée 7/7 (FAI, validité, prêt oui, acceptée et sa date, l'acquéreur) ;
  **compromis de 45 pages, 82 000 caractères, date du prêt placée à 37 000** : 13/13 (dont la date limite du prêt, le
  séquestre chez le notaire, 1 signature du vendeur et 2 des acquéreurs LUES SUR L'IMAGE), vendeur et 2 acquéreurs ;
  PV 6/6 + les travaux VOTÉS seulement (le ravalement, pas la toiture rejetée), procédure « non vue » ; **0 fuite** sur 19
  mots interdits (naissances, adresse, téléphone, montant du prêt, banque, taux, apport, régime, feuille de présence,
  copropriétaire qui vote contre, débiteur nommé et sa dette) ; **0,0035 $ les trois** (le compromis : 22 700 jetons,
  0,0025 $).
- Contrôles : `test_ged_lire.py` **48 VERT** ; `test_ged_lecture.cjs` **34 VERT** (dont 3 témoins « lots 1 et 2
  inchangés ») ; classement 25, Reçu / Manque 29, règles 44, dépôt 17, les 4 essais de la signature ; `npm run build` vert.
- Base : rien d'obligatoire ; patch facultatif `patch_ged_m6_lot3_pv_lu_2026-11-12.sql` (+ `_INVERSE`) : `copro.pv_ag`
  « classer » → « lue ».
✅ **« Oui tout » (12/11 soir)** : patch du PV **POSÉ** (`copro.pv_ag` → « lue », contrôle vert) ; commit `6b26c07` poussé SEUL
(`2326641..6b26c07`) ; Render (`/health`) et Vercel à jour, `/ged/lire` sans jeton → 401.
✅ **ESSAI RÉEL DU LOT 3 — « Vas y test » (12/11, ~21:50)**, Chrome de Frédéric, 62774 : 3 documents FICTIFS
(`essai_reel/fabriquer_offre_scan.py`, `fabriquer_lot3.cjs`) — une offre scannée signée, un **compromis PDF texte de 45
pages** (date du prêt en page 20, signatures DESSINÉES sur les pages 44 et 45), un PV texte (feuille de présence, vote
nominatif, débiteur, toiture rejetée).
- Classement 3/3 « le nom et l'IA sont d'accord » ; envoi chez Hektor 3 `done`, numéros **716035 à 716037** (26 documents
  sur le bien, aucun doublon).
- ⭐ **Le navigateur a envoyé le compromis EXACTEMENT comme prévu** : `par_texte` vrai ET `pages_lues` = [44, 45] (le
  texte + les 2 dernières pages en image), 21 812 jetons, 0,0026 $. Valeurs toutes justes, chacune à sa page : prix,
  net vendeur, honoraires et charge (p. 3), réitération et notaires (p. 13), séquestre (p. 14), **prêt et sa date (p. 20)**,
  **1 signature du vendeur (p. 44) et 2 des acquéreurs (p. 45) lues sur l'image**, vendeur et 2 acquéreurs.
- Offre (scan, page 1 en image) : « offre 180 000 € FAI · du 20/09/2026 · acceptée le 22/09/2026 · sous condition de
  prêt · 1 acquéreur » ; PV (texte seul) : « AG du 12/05/2026 · budget 85 000 € · travaux votés : Ravalement de façade ·
  syndic … » — la toiture rejetée n'y est pas.
- **0 fuite** (naissances, adresse, téléphone, banque, montant du prêt, apport, taux, régime, feuille de présence,
  débiteur et sa dette, toiture) ; coût des 3 lectures 0,0037 $.
- Après rechargement : « ▸ Lu par l'IA : 8 documents » (les 5 du lot 2 + les 3 du lot 3) ; la règle copro dit maintenant
  « 3 pièces de copropriété ». Les 8 documents fictifs restent sur 62774 (chez nous et chez Hektor).

### 12.16 Le morceau 6, lot 4 — le reste (audit du 13/11, lecture seule, rien codé)
« Oui lot 4 » (13/11). Mesures, même méthode qu'au §12.14 : le rythme = noms des documents déposés chez Hektor depuis le
20/08 (numéro Hektor ≥ 712 625, ≈ 2,8 mois) ; la forme = les 50 PDF les plus récents de chaque famille au disque du
serveur, script `forme_lot4.py` (scratchpad), qui n'imprime que des nombres.
- **Mandat** : 106 déposés (81 biens), mais **12 pages et 46 textes sur 50** → ce sont les mandats sortis du modèle ;
  4 scans sur 50 seulement. Confirme Frédéric : le lire ne sert que pour un mandat signé à la main et déposé.
- **Avenant** : **72** (53 biens), 1 page (p90 5), **25 scans purs sur 50**, 20 textes. Le plus fréquent du lot.
- **Fin de mandat** : 7, 1 page, 40 scans sur 50. **Annulation de vente** : 9. (Types déjà marqués « lue » en base,
  hors de la liste du lot 4 : à trancher par Frédéric.)
- **Acte / attestation de vente** : 21 (9 biens), **4 pages** en médiane (l'attestation du notaire ; p90 31), 41 scans.
- **Factures** : 80 (31 biens), 2 pages, 42 scans — ⚠ **les noms disent EDF, granulés, sinistre** : des factures
  d'énergie ou de travaux, PAS des notes d'honoraires GTI. Lire `facture.honoraires` ne servirait presque jamais.
- **Petits diagnostics** (texte surtout) : électricité 8 (7 pages, 35 textes), gaz 9 (9 pages), amiante 16 (21 pages,
  42 textes), plomb 13 (17 pages), termites 0 récents (8 pages). La conclusion est en synthèse au début du rapport.
- **Assainissement** : 25 (23 biens), 5 pages, **30 scans**, et **55 % de paires très proches** (les formulaires du
  SPANC se ressemblent).
- **Surfaces** : 15, **1 page**, 36 scans sur 50.
- **Règlement / EDD** : 8, **37 pages** (p90 74), 36 scans : en 6 pages on lit la date, l'étude, l'immeuble, pas
  l'état descriptif ni le lot du bien.
- L'écran : `dateEtatLue` ne sert qu'à l'état des risques (règle de 6 mois du morceau 5) → le lot 4 ne la touche pas ;
  les validités des petits diagnostics vont au morceau 7.
- Vérifié dans le code : seule la fenêtre de dépôt (`DepotDocuments.tsx`) demande une lecture → le mandat que l'app fait
  signer n'est JAMAIS lu ; seul un mandat déposé à la main l'est.
✅ **« Avec » (13/11)** : le lot 4 COMPLET, facture et règlement compris, plus la fin de mandat et l'annulation.
✅ **LOT 4 ÉCRIT ET CONTRÔLÉ (13/11), RIEN POSÉ NI POUSSÉ :**
- Serveur (`openai_ged_lecture_service.py`) : 14 fiches neuves (25 en tout). `mandat.vente` (numéro, date, nature,
  durée, prix, net vendeur, honoraires et % et qui paie, commune, signatures ; les MANDANTS), `mandat.avenant` (objet,
  ancien et nouveau prix, nouveaux honoraires, nouvelle fin, signatures ; mandants), `mandat.fin` (dates du courrier et
  d'effet, à l'initiative de qui, motif dans une LISTE FERMÉE — une raison personnelle devient « autre », jamais
  recopiée ; mandants), `transaction.acte` (nature, date de la VENTE ≠ date de l'attestation, prix, mobilier, étude,
  commune, lots ; vendeurs et acquéreurs ; jamais le prêt), `transaction.annulation` (nature, dates, qui, séquestre ;
  jamais le prêt ni la raison personnelle), `facture.honoraires` (numéro, date, HT / TVA / TTC, objet, payeur = une
  QUALITÉ ; une facture de fournisseur est dite « pas ce type »), une fiche commune aux rapports électricité, gaz,
  amiante, plomb, termites (date, validité imprimée, RÉSULTAT dans une liste fermée, conclusion, société, commune),
  `diag.assainissement` (type, contrôle, conformité, délai), `diag.surface` (Carrez, habitable, hors Carrez, lots),
  `copro.reglement` (nature, date, étude, immeuble, nombre de lots, destination, modificatifs, lots et tantièmes).
  Qualité « mandant » ajoutée. Les diagnostics, la facture et le règlement ne lisent AUCUN nom (consigne : jamais le
  propriétaire ni le donneur d'ordre). Pages : mandat 6 + 40 000 car. + ses 2 dernières en image ; avenant et fin de
  mandat : la dernière en image ; acte et règlement : 6 pages, 40 000 car.
- Écran : `gedLecture.ts` (25 types lus ; résumés sans nom — « avenant du … · au mandat 18836 · baisse de prix ·
  nouveau prix 175 000 € · 1 mandant ») ; `gedClassementIa.ts` (les trois tables de réglage).
- Base : RIEN d'obligatoire. Étiquette : `patch_ged_m6_lot4_types_lus_2026-11-13.sql` (+ `_INVERSE`) — amiante, plomb,
  termites, règlement passent de « classer » à « lue » (les 10 autres types du lot l'étaient déjà).
- **Essais hors ligne** : serveur 80 VERT (48 avant) ; écran 49 VERT (34 avant) — dont, nouveau, les tables de pages
  lues DANS LES DEUX SOURCES et comparées clé par clé (un écart écran / serveur ne passe plus) ; `npm run build` vert.
- **Banc réel, 15 documents FICTIFS** (avenant, mandat de 3 pages et fin de mandat scannés, attestation de vente
  scannée, rétractation, note d'honoraires, les 5 rapports, SPANC et Carrez scannés, règlement) : **64 valeurs sur 64**,
  **0 fuite** sur 20 mots interdits (naissances, adresses, téléphone, prêt, banque, régime, « divorce », « perte
  d'emploi », propriétaire, opérateurs, promoteur, cadastre) ; le **témoin** — une facture EDF déposée en « facture
  d'honoraires » — est dit « pas ce type ». Coût 0,006 $.
  ⚠ Ce que le banc a attrapé : (a) une attestation de vente dite « pas ce type » 1 fois sur 3 → consigne précisée
  (« vrai pour une attestation, même courte, même si elle cite le financement ») → 6 sur 6 ; (b) une « fuite » qui
  n'en était pas une : le mot témoin « Ailleurs » (rue fictive) se retrouvait dans le motif « vendu_ailleurs ».
✅ **« Oui tout » (13/11)** : patch d'étiquette POSÉ (contrôle : les 14 types du lot 4 sont « lue ») ; le lot 4 commité
et poussé (`7c4e3fb`, avec deux commits d'une autre session, accord « Pousse ») ; Render et Vercel le servent.
✅ **ESSAI RÉEL DU LOT 4 (13/11), sur le bien d'essai 63331** (n° 10000009, « ESSAI 8A3 PIECE 3 - ne pas diffuser »,
statut Estimation, choisi par Frédéric) — ⚠ **62774 ne prend plus de documents** : clos, il a quitté les biens courants
la nuit du 12 au 13/11 ; sa fiche « index léger » refuse le dépôt (« Désarchivez ou réintégrez le bien »).
- 8 documents FICTIFS déposés par l'écran, dans Chrome (avenant, mandat de 3 pages, attestation de vente, SPANC et
  Carrez SCANNÉS ; rapport électricité, note d'honoraires, règlement EN TEXTE).
- **Classement : 7 sur 8 justes d'emblée (le nom et l'IA d'accord).** ⚠ **La note d'honoraires a été proposée en
  « Notes, suivi interne »** : la règle du nom (`gedTypeParNom.ts`) attend « note d honoraires » ; « Note honoraires GTI »
  (sans « d' ») tombe sur `\bnotes?\b` → `interne.notes`, type « jamais envoyé » à l'IA, donc l'IA ne peut pas
  rattraper. Corrigé à la main pour l'essai. ✅ **Corrigé dans le code le 13/11 (« Oui, corrige »)** : dans la SOURCE
  `phase2/checks/ged1_mesure_nomenclature.py`, « note d honoraires » devient `\bnotes? (d )?honoraires?\b`, puis
  `gedTypeParNom.ts` refabriqué (une ligne change). Mesure avant : 3 noms réels de plus reconnus, 0 pris à une autre
  règle. Témoins : « Notes visite » reste une note interne, « Accord honoraires mandat » et « Baisse d honoraires »
  restent au mandat. Tests dépôt 19 VERT, lecture 49, classement 25, build vert. ⚠ La source Python n'avait JAMAIS été
  commitée (fichier non suivi depuis le 12/11).
- **Envoi chez Hektor : 8 sur 8 `done`**, numéros 716062-716064, 716066, 716067, 716069, 716071, 716075 ; le bien porte
  exactement 8 documents (aucun doublon).
- **Lectures : 8 sur 8, toutes justes, chacune avec sa page** : avenant (scan, page 1 en image ; 2 mandants), mandat
  (scan, pages 1-3 ; numéro, exclusif, prix, net vendeur, honoraires 5 % à la charge de l'acquéreur, durée, **2
  signatures de mandants et celle de l'agence lues page 3**), attestation (date de la VENTE 12/01/2027 ≠ date de
  l'attestation 20/01/2027 ; 2 vendeurs, 2 acquéreurs), électricité (texte ; anomalies), SPANC (travaux obligatoires
  sous 12 mois), Carrez (64,35 m², lot 12), facture (HT / TVA / TTC, payeur vendeur, mandat 18836), règlement (texte ;
  48 lots, destination mixte, lots et tantièmes, modificatif).
- **0 fuite** sur 18 mots interdits, vérifiée en base. Coût des 8 lectures : 0,0038 $.
- Après rechargement : **« ▸ Lu par l'IA : 8 documents »**, chaque résumé sans un nom ; « Prise de mandat : 1 pièce
  sur 5 » (le mandat déposé compte) ; la règle du morceau 5 dit « un compromis ou un acte est au dossier, aucun au
  registre ». Les 8 documents fictifs restent sur 63331 (chez nous et chez Hektor).

### 12.17 Le morceau 7 — comparer ce qui est lu à ce que nous avons (audit du 13/11, lecture seule, rien codé)
« Oui » (13/11) au morceau 7. Catalogue : `E_synthese_catalogue.md` §2 (7 comparateurs, 2 étapes) et §3.2 (L1 à L19) ;
plus les vérifications des justificatifs ajoutées au §12.14 (taxe, titre).

**Audit limité au DOCUMENT LU comparé à la fiche, aux mandants et aux deux registres. Aucun geste n'est créé :**

| | créer | modifier | supprimer / archiver | lire / remonter |
|---|---|---|---|---|
| annonce (fiche) | — | — (« remplir » = morceau 8) | — | lu : prix, net vendeur, taxe, Carrez, surface, commune, copropriété, DPE, dates du mandat |
| contact | — | — | — | lu : les mandants / propriétaires du bien (`ficheDuMandat.contacts`) |
| recherche | — | — | — | non concernée |
| relation (mandant, propriétaire, acquéreur) | — | — | — | lue (rôle du lien) ; ⚠ acquéreurs rangés « mandant » depuis juillet |
| transaction (offre, compromis, vente) | — | — | — | lu : registre `app_affaire_ledger` (déjà chargé par « À regarder ») |
| mandat | — | — (⛔ jamais modifier ni prolonger) | — | lu : numéro, dates (la fiche) ; charge (carnet du registre) |
| document / photo | — | — | — | lu : les valeurs lues (`app_ged_valeur`, déjà chargées) |
| RDV / visite | — | — | — | non concerné |

- **Ce qui existe et se réutilise** : la forme du morceau 5 — fonction PURE `lib/gedRegles.ts` (une `Alerte` = code,
  niveau, texte, pourquoi, pièce à déposer), affichée sous « À regarder » dans `RecuManque.tsx`, derrière
  `ged_propositions` (cran admin, allumé le 12/11). `RecuManque` charge DÉJÀ les lectures (`loadGedLectures`) et le
  registre des transactions (`loadAffairesForDossier`). `faitsGedDuBien` (`App.tsx:11852`) lit la fiche par
  `rawWizardDetailField` (le double décodage des groupes y est fait une fois). La présence (C7) = `gedPieces.ts`.
- **Ce qui manque à l'écran pour comparer** : les MANDANTS du bien (`ficheDuMandat.contacts`, déjà dans le panneau, pas
  passés à « Reçu / Manque ») ; des champs de la fiche pas encore lus : `TAXE_FONCIERE`, `prix`, `PRIXNETVENDEUR`
  (groupe `mandat_infofi`), `SURF_CARREZ`, `surfappart` (`ag_interieur`), la commune et le code postal (`localite`),
  `copropriete_statut_syndicat` ; du registre, déjà rendus mais pas gardés : montant, net vendeur, honoraires,
  mandants et acquéreurs (`mandants_json`, `acquereurs_json`).
- **Mesures (lecture seule, 13 567 fiches en base)** : taxe foncière remplie sur 1 935 ; Carrez remplie sur **85 biens en
  copropriété sur 737** (L15 ne pourra comparer que là) ; surface `surfappart` 10 479 ; commune 13 567 ; groupe
  honoraires 1 510. ⭐ Les noms lus sont des noms d'USAGE : « Mme FICTIF Jeanne née ESSAI » est lu FICTIF / Jeanne (essai
  du 13/11) — la comparaison aux mandants se fait sur le nom d'usage, la « née » n'est pas gardée.
- **Pièges connus, à tenir dans le code** : une fiche de couple = DEUX personnes (mémoire « contacts muets, fiches de
  couple ») ; des acquéreurs rangés « mandant » depuis juillet → seul « une personne LUE inconnue de la fiche » alerte,
  jamais l'inverse ; « incomparable » (vide, non vu, incertain, unité inconnue) ne sonne JAMAIS ; les tolérances dans UNE
  table ; la date de référence = le registre (compromis vivant), jamais `compromis_date_start`.
- **Rien n'écrit** : ni la fiche, ni Hektor, ni le worker, ni le run de nuit ; pas de patch de base si l'interrupteur
  `ged_propositions` est réutilisé.
**Proposition — trois sous-lots, chacun commité et essayé** (ordre de valeur de Frédéric, §12.14 : les justificatifs d'abord) :
- **7a — le socle et les justificatifs du bien** : `lib/gedComparer.ts` (normaliser, nombre, date et validités, lieu,
  liste, références, personnes) ; règles : titre et taxe ↔ mandants (L11 partiel), taxe ↔ fiche (montant, commune, avis
  de plus d'un an), document d'un autre bien (L13, commune lue ≠ commune du bien), validités des diagnostics (L2 : ERP,
  DPE, électricité, gaz, assainissement, termites, plomb), DPE lu ≠ fiche (L6), Carrez (L15), copropriété (L16 lots et
  charges, L17 procédure).
- **7b — le mandat** : termes (L12), avenant (L14), prix de signature (L4), charge des honoraires (L1, conflit
  seulement), signatures papier (L10), fin de mandat (L18), vendeurs du compromis ↔ mandants (fin de L11).
- **7c — les transactions** : le résolveur de la ligne visée, transaction lue ↔ registre (L7), facture (L8),
  honoraires (L9), annulation (L19).
Choix par défaut annoncés et non contredits : une alerte sur une personne AFFICHE son nom ; même interrupteur
`ged_propositions` (pas de patch de base).
✅ **« Oui vas y » (13/11) : SOUS-LOT 7a ÉCRIT ET CONTRÔLÉ, RIEN POUSSÉ :**
- `src/lib/gedComparer.ts` (socle pur) : normaliser (accents, « Saint » = « St », « 0 » de Hektor = vide), C1 nombre
  (tolérances dans UNE table `TOLERANCES`), annualiser, C2 validités (électricité, gaz, assainissement non collectif
  3 ans ; termites 6 mois ; plomb 1 an au-dessus du seuil, sans limite sinon), C4 commune (égal / proche / différent /
  incomparable, sans table des communes nouvelles → « à vérifier »), C3 personnes (nom et prénom, particules ignorées,
  nom et prénom inversés et fiche de couple « M. et Mme X » = proche ; seul « aucun mot retrouvé » = différent). Seules
  les valeurs lues NETTEMENT comparent (« incertain » se tait).
- `src/lib/gedReglesLues.ts` (règles pures) : **L13** commune lue ≠ commune du bien ; **L11** propriétaires du titre et
  redevables de la taxe absents des mandants (avec leur nom ; un vendeur cité au titre ne compte pas ; fiche sans
  mandant = silence) ; **T1** taxe lue ≠ fiche (± 2 % ou 5 €), fiche vide = information, avis de plusieurs biens =
  silence ; **T2** avis de plus d'un an ; **L2** validités à la signature du compromis (date du REGISTRE), alerte sous
  offre / compromis, information avant ; **L6** DPE lu ≠ fiche (± 1, classe recalculée) ; **L15** Carrez mesurée plus
  petite de plus de 5 % ; **L16** lots (le total OU les principaux) et charges annualisées (± 10 % ou 120 €) ; **L17**
  procédure de copropriété lue (et « la fiche dit le contraire »). L'état des risques reste N4, le DPE de la fiche N5.
- Branchement : `gedRegles.ts` (4 champs facultatifs de plus dans `FaitsRegles`) ; `App.tsx` (`faitsGedDuBien` lit
  `TAXE_FONCIERE`, `SURF_CARREZ`, `copropriete_statut_syndicat`, la ville ; `personnesGedDuBien` : une ligne par
  personne, un couple fusionné compte ses `members`) ; `RecuManque.tsx` (les deux familles de règles dans « À
  regarder », même ordre, même interrupteur).
- **Contrôles** : `test_ged_regles_lues.cjs` **45 VERT** (chaque règle a son témoin qui se tait) ; **témoin inverse** :
  sans la prudence sur les couples, 3 essais tombent ; règles 44, Reçu / Manque 29, lecture 49, dépôt 19, classement 25
  verts ; `npm run build` vert. **Banc d'écran local** (données fictives, `ged_m7_vue`) : 9 lignes « À regarder » dont 5
  du 7a, justes ; le redevable « ESSAI » trouvé dans « M. et Mme ESSAI » se tait ; 375 px sans débordement.
- ⚠ Non vu en réel : sur un vrai bien, les lignes dépendent des documents LUS par l'outil (63331 et 62774 seulement).
✅ **7a POUSSÉ (13/11, `81be8ad`, avec `e2ecc56` et `d655c1f` d'une autre session — le second touche
`push_contacts_to_supabase.py` du run de nuit —, accord « Pousse ») ; Vercel le sert.**
✅ **« Oui, 7b » (13/11) : SOUS-LOT 7b ÉCRIT ET CONTRÔLÉ, RIEN POUSSÉ.** Sources mesurées : la charge des honoraires au
REGISTRE des mandats (`app_registre_mandats_current.mandat_charge_honoraires_app` : vendeur 23 342, acquéreur 131, vide
1 119 — la vue que l'écran lit déjà pour la clôture) ; le type du mandat sur la fiche (`mandat_type` : SIMPLE 365,
EXCLUSIF 254, ACCORD 62).
- `gedComparer.ts` : C5 `comparerNumero` (les chiffres, zéros de tête ignorés), C6 `comparerListe` (synonymes : Hektor
  dit « acheteur »).
- `gedReglesLues.ts` : **L12** termes du mandat lu (numéro ; type, hors « ACCORD » ; date de signature = début du
  mandat à 1 jour près) — ⭐ un mandat lu sous un AUTRE numéro (l'ancien mandat du bien) donne UNE ligne et rien d'autre
  n'est comparé ; **L14** dernier avenant (son numéro ; le prix qu'il fixe ≠ prix affiché, sauf si le prix a encore bougé
  APRÈS l'avenant : c'est N2) ; **L4** prix de signature ≠ prix affiché sans avenant lu qui l'explique (information) ;
  **L1** qui paie, lu (l'avenant fait foi sur le mandat) face au registre — registre pas lu = silence, vide =
  information, « les deux » = information ; **L10** moins de signatures que de mandants LUS DANS LE MÊME DOCUMENT (jamais la
  fiche : elle peut porter des acquéreurs rangés « mandant »), agence non signataire ; **L18** fin du mandat EN COURS au
  dossier, bien encore diffusé ; **L11 étendu** aux mandants lus (mandat, avenant) et aux vendeurs du compromis (une
  qualité non lue au compromis se tait : ce pourrait être un acquéreur). ⛔ Rien ne modifie ni ne prolonge un mandat.
- Branchement : `FaitsRegles` (+ `prix`, `mandatType`, `chargeRegistre`) ; `App.tsx` lit le prix et le type ;
  `RecuManque.tsx` lit la charge au registre (`loadRegisterCycleAffaires`, lecture ratée = `undefined` = silence).
- **Contrôles** : `test_ged_regles_lues.cjs` **66 VERT** (21 de plus) ; **témoin inverse** : sans la garde « autre
  numéro », l'essai de l'ancien mandat tombe — ⚠ il ne tombait pas au premier essai (une ligne sortait par un autre
  chemin) : essai durci jusqu'à ce qu'il tombe ; l'essai L1 a trouvé une faute (« de le vendeur ») corrigée ; règles 44,
  Reçu / Manque 29, lecture 49, dépôt 19, classement 25 ; build vert. **Banc d'écran local** : 12 lignes, dont les 7 du
  mandat, justes ; N1c et N2 se taisent d'eux-mêmes (un mandat papier et un avenant sont au dossier).
✅ **7b POUSSÉ (13/11, `973592c`, avec `f782658` d'une autre session — notes seulement —, accord « Pousse ») ; Vercel le sert.**
✅ **« Oui, 7c » (13/11) : SOUS-LOT 7c ÉCRIT ET CONTRÔLÉ, RIEN POUSSÉ.** Registre mesuré (lignes depuis 2025) : compromis
698 (montant, net vendeur, honoraires d'entrée et de sortie tous remplis ; **prix = net + entrée + sortie pour 679**),
offres 1 901 (montant rempli, jamais de net), ventes 645 (montant et honoraires, pas de net) ; acquéreurs en
`acquereurs_json` (un OBJET pour une offre, une LISTE pour un couple : `nom`, `prenom`).
- `gedComparer.ts` : **`resoudreCible`** — la ligne visée par un document lu : par les acquéreurs (nom retrouvé), puis la
  date (± 15 j), puis le montant (± 1 %) ; une ligne seule se prend ; **zéro ou plusieurs à la fin -> rien, silence**
  (jamais comparer à la mauvaise ligne). Pour une offre, le nom passe avant la date (la date d'une offre refusée est celle
  du refus).
- `gedReglesLues.ts` : **L7** offre (montant, sauf base « net vendeur »), compromis (prix, net vendeur, honoraires entrée
  + sortie, date de signature à 1 jour : UNE ligne qui dit tout), acte (date de la VENTE, prix) face à LEUR ligne ; **L8**
  facture TTC ≠ honoraires de la vente (« un partage avec une autre agence ? ») ; **L9** équation prix = net +
  honoraires (mandat, compromis) et honoraires du compromis ou de la facture AU-DESSUS du mandat (ou du dernier avenant ;
  en dessous = une remise, silence) ; **L19** annulation lue d'un compromis encore actif au registre (« annuler le
  compromis d'abord, puis refuser l'offre » : dit, jamais fait).
- `RecuManque.tsx` : le registre garde montant, net vendeur, honoraires, acquéreurs ; lignes absentes de Hektor écartées.
- **Contrôles** : `test_ged_regles_lues.cjs` **84 VERT** (18 de plus) ; **témoin inverse** : un résolveur qui prend la
  première ligne venue fait tomber 2 essais ; règles 44, Reçu / Manque 29, lecture 49, dépôt 19, classement 25 ; build
  vert ; banc d'écran local (13 lignes, dont « Compromis : prix 190 000 € lu, 185 000 € au registre ; net vendeur… »),
  console sans erreur. ⚠ `tsc --noEmit` lancé une fois par réflexe (contraire à la page d'entrée) : sans effet, rien écrit.
✅ **7c POUSSÉ (13/11, `a580c9e`, seul) ; Vercel le sert. LE MORCEAU 7 EST COMPLET.**

### 12.18 Le morceau 8 — proposer de REMPLIR la fiche depuis un document lu (audit du 13/11, lecture seule, rien codé)
« Ok suis le plan » (13/11). Sources : `E_synthese_catalogue.md` §1.2, §3.2 (L1, L3, L5, L16), §6.1, §7 (questions 1 à 4
et 7) ; `2_developpeur.md` §3 (un « remplir » n'appelle QUE le geste existant), §4.5 (table des propositions), §5.4-5.5.

**Audit limité à l'ÉCRITURE d'une valeur lue sur la fiche, au registre des mandats et aux conditions d'une affaire :**

| | créer | modifier | supprimer / archiver | lire / remonter |
|---|---|---|---|---|
| annonce (fiche) | — | ⚠ une case VIDE seulement, par `editAnnonceOptimistic` → `app_edit_annonce_optimistic` → travail `update_hektor_annonce_fields` → Hektor (contrôle au retour existant) | — | relue juste avant d'écrire |
| contact | — | — | — | non concerné |
| recherche | — | — | — | non concernée |
| relation | — | — | — | non concernée |
| transaction (affaire) | — | condition « Obtention crédit » par `ecrireAffaireConditions` (chez nous seulement, aucun travail Hektor) — ⚠ la fonction EFFACE puis repose la liste, réservée managers / admins | — | liste relue juste avant |
| mandat | — | charge des honoraires au REGISTRE par `ecrireMandatCharge` (chez nous ; garde l'auteur) — ⚠ ÉCRASE et EFFACE sur vide ; ⛔ aucun autre champ du mandat | — | registre relu juste avant |
| document / photo | — | — | — | les lectures (déjà là) |
| RDV / visite | — | — | — | non concerné |

- **Les trois gestes existent et ne sont PAS modifiés** : on les appelle seulement, et seulement pour une case vide,
  relue au dernier moment (la lecture de la fiche décode les groupes une fois : `rawWizardDetailField`).
- **Ce qui n'existe pas** : garder la DÉCISION (« rempli », « ignoré ») — sans elle, une proposition ignorée revient à
  chaque ouverture, et on ne sait pas qui a rempli quoi → une petite table neuve (patch de base). Et un interrupteur
  propre : c'est la première fois que l'outil ÉCRIT chez Hektor.
- **⛔ Ce qu'on n'écrit PAS** : la taxe foncière (groupe `mandat_infofi`, qui renvoie AUSSI prix, honoraires, charges) ;
  tout champ du mandat (décision ⑦-7) ; l'adresse, les mandants (alertes seulement) ; jamais par-dessus une valeur.
- **Mesures** : les lectures en base ne concernent que les deux biens d'essai (62774 : 8, 63331 : 8) → **aucune
  proposition réelle tant que les négociateurs n'utilisent pas l'outil** ; la valeur du morceau 8 est pour après.
  Historique du travail Hektor sur ces champs : 6 travaux, tous sur 63331 le 22/10 (dont 1 en erreur) et 1 en août.
- **Les épreuves avant d'allumer** (études : « remplir une case VIDE par une modification » n'a jamais été prouvé pour
  `dpe_date` et la date d'ERP ; le groupe copropriété a 2 écritures de quote-part) : 62774 ne prend plus rien (sorti des
  biens courants). **63331 et 63330 ont TOUTES leurs cases remplies** (DPE, dates, copropriété) : l'épreuve sera donc
  « changer puis remettre » une valeur sur 63331 (bien d'essai, Estimation, jamais diffusé) — même chemin d'écriture.
**Proposition (V1 = les 4 « remplir » de l'étude)** :
- **P1 DPE et état des risques** : `dpe_cons`, `dpe_ges`, `dpe_date`, date de l'ERP — après l'épreuve diagnostics.
- **P2 copropriété** : nombre de lots, quote-part annuelle — après l'épreuve copropriété (la case copropriété doit
  rester OUI ; la garde du worker existe).
- **P3 charge des honoraires** au registre des mandats, si la case est vide (jamais sur l'affaire).
- **P4 condition « Obtention crédit »** avec la date limite du prêt lue au compromis, si la liste est vide.
- Affichage : sous « À regarder », une ligne « à remplir » avec la valeur, la page du document, et deux boutons
  « Remplir la fiche » / « Ignorer » ; rien ne s'écrit sans le clic ; « tout remplir » n'existe pas.
- Base : `app_ged_decision` (la proposition, la décision, qui, quand, ce qui a été envoyé) + interrupteur
  `ged_remplir` (off / admin / on), posé ÉTEINT ; patch, inverse et répétition.
✅ **« Vas y » (13/11) : MORCEAU 8 ÉCRIT ET CONTRÔLÉ, RIEN POSÉ NI POUSSÉ, AUCUNE ÉPREUVE FAITE :**
- Base : `supabase/patch_ged_m8_remplir_2026-11-13.sql` (+ `_INVERSE`, + `_REPETITION` qui se termine par un
  rollback) — `app_ged_decision` (journal : ni mise à jour ni effacement), `app_ged_decider()` (SECURITY DEFINER : compte
  actif, interrupteur pour l'appelant, périmètre du bien, auteur = `auth.uid()`), `ged_remplir` posé **off**. Le journal
  GED existant (`app_ged_journal`) n'est PAS touché (sa contrainte d'objet reste).
- `src/lib/gedRemplir.ts` (pur) : P1 DPE (consommation, émissions, date) et date de l'ERP ; P2 lots et quote-part
  annuelle — seulement sur un bien MARQUÉ copropriété ; P3 charge au registre (lu et vide ; « les deux » et un autre
  mandat : rien) ; P4 « Obtention Crédit » sur LA transaction du compromis lu (résolveur), liste comptée vide. Une
  valeur « incertaine » ne se propose pas ; une décision prise ne revient pas (une autre valeur lue, si). `caseVide` :
  « 0 », « 0000-00-00 », la date zéro.
- `src/lib/ged.ts` : `useGedRemplir`, `loadGedDecisions` (lecture ratée -> null -> AUCUNE proposition),
  `gedDecider`, **`compterConditionsStrict`** — ⚠ trouvé à l'écriture : `loadAffairesConditions` rend une carte VIDE sur
  erreur ; s'en servir pour « liste vide » aurait pu EFFACER des conditions existantes (la fonction efface puis repose).
- `src/App.tsx` : `remplirDepuisDocument` — fiche RELUE fraîche (`loadDossierDetail` + `detailPayload`) juste avant,
  case pleine -> rien écrit + décision « echec » ; copropriété : seulement si encore OUI ; puis `editAnnonceOptimistic`
  (le geste de « Reporter dans la fiche », inchangé) ; charge : la ligne du registre relue (sans elle, rien), jamais une
  charge vide ; condition : comptée strictement juste avant ; la décision « remplie » gardée APRÈS le geste réussi.
- `src/RecuManque.tsx` : « À remplir (N) » au-dessus de « À regarder », « Remplir la fiche » / « Ignorer », un clic par
  proposition ; ⚠ trouvé : la fonction passée change à chaque rendu — les lectures dépendent de sa PRÉSENCE seulement.
- **Contrôles** : `test_ged_remplir.cjs` **27 VERT** ; **témoin inverse** : sans la garde « case déjà remplie », l'essai
  tombe (⚠ le premier essai était faussé : Python sous Windows avait réécrit `App.tsx` en fins de ligne CRLF ; refait
  avec `newline=''`, exactement 1 ROUGE) ; tous les essais GED verts (84, 44, 29, 49, 19, 25) ; build vert (`tsc -b`).
  **Banc d'écran local** : « À remplir (1) — État des risques : établi le 01/12/2025 — lu dans ERP 2026.pdf, page 1 » ;
  le clic appelle le geste avec le bon champ et la bonne valeur ; console sans erreur.
✅ **« Vas y » (13/11) : patch m8 POSÉ — 6 contrôles VERTS** (table et RLS ; aucune écriture directe ; porte SECURITY
DEFINER fermée à anon ; `ged_remplir` **off** ; table vide) ; le code commité et poussé dans le même geste.
✅ **« Oui epreuve » (13/11) : ÉPREUVE D'ÉCRITURE SUR 63331, par l'ÉCRAN du bien (modification en place,
« Enregistrer »), dans le Chrome de Frédéric :**
- Avant (base) : `dpe_date` et `diag_risques_nat_tech_date` 2026-09-10, `copropriete_nb_lot` 24,
  `copropriete_quote_part` 120, `copropriete` OUI (+ tous les champs des deux groupes relevés).
- **ALLER, PROUVÉ EN BASE** : file `app_annonce_pending` = exactement les 4 champs (11/09, 11/09, 25, 121), départ
  différé de 10 min ; travail `update_hektor_annonce_fields` **done** à 12:51:28, groupes **diagnostiques** (dpe_date,
  diag_risques_nat_tech_date) ET **copropriete** (copro_lots → copropriete_nb_lot, copro_quote_part →
  copropriete_quote_part) : « mise à jour effectuée » chacun ; relecture `refresh_console_data` synced 12:51:57 ; la
  fiche RELUE de Hektor porte les 4 nouvelles valeurs, **TOUS les autres champs des deux groupes inchangés,
  `copropriete` reste OUI** ; vue des écarts du contrôle au retour : vide. ⭐ **C'est la première preuve que Hektor
  accepte `dpe_date` et la date d'ERP EN MODIFICATION** (l'étude disait : jamais fait).
- **RETOUR (remise des valeurs d'origine)** : file = exactement les 4 valeurs d'origine, départ ~13:07 ; l'écran montre
  ensuite 2026-09-10, 2026-09-10, 24, 120, copropriété Oui, « Hektor · à jour », aucune modification en attente.
  ✅ **PROUVÉ EN BASE (13/11, plus tard)** — le connecteur Supabase restant en panne, lecture par le chemin de secours
  du projet (`node Console/apply_sql_patch.js`, par le pooler, mesure enveloppée dans un `raise exception` : rien
  écrit ; la lecture directe par la clé de service, refusée par l'outil, n'a PAS été retentée) : travail
  `update_hektor_annonce_fields` **done** (créé 13:08:00, fini 13:08:25, `skipped_fields` vide, groupe diagnostiques
  mis à jour), relecture `refresh_console_data` **synced** à 13:09:00 ; fiche RELUE de Hektor : `dpe_date` et
  `diag_risques_nat_tech_date` 2026-09-10, `copropriete_nb_lot` 24, `copropriete_quote_part` 120, `copropriete` OUI,
  et les autres champs des deux groupes identiques à l'état d'avant (lot 12, fonds travaux 3 500, syndicat ALERTE,
  DPE 210/45, coûts 900-1 300…) ; file d'attente **0** ; écarts du contrôle au retour **0**.
  ➡ **L'ÉPREUVE EST COMPLÈTE DANS LES DEUX SENS.**
✅ **« Oui » (13/11) : `ged_remplir` ALLUMÉ EN ADMIN à 14:42:41 UTC** — connecteur Supabase en panne, posé par
`node Console/apply_sql_patch.js` (transaction gardée : 1 ligne, valeur relue « admin », sinon arrêt) puis relu à part.
⚠ Une première tentative par le connecteur avait rendu une erreur 500 : relue AVANT de reposer, elle n'avait rien écrit.
Les 5 interrupteurs GED sont désormais en « admin ». Retour arrière :
`update public.app_setting set value='off', updated_at=now() where key='ged_remplir';`
⚠ **Pas encore VU à l'écran en service** : 63331 a toutes ses cases remplies, il n'y a donc rien à y proposer ; la
première proposition réelle viendra d'un bien qui a un document lu ET une case vide.

### 12.19 Le morceau 9 — les pièces des personnes (audit du 13/11, lecture seule, rien codé)
**Ce qui existe (code et base, mesuré le 13/11)** :
- `app_ged_type` : `justif.identite`, `justif.etat_civil`, `transaction.financement`, `transaction.renseignements` sont
  déjà « lue » et `sensible` ; `justif.rib` « jamais_envoye ». La SEULE porte fermée est le serveur :
  `openai_ged_lecture_service.py` refuse tout type sensible (« lue plus tard (morceau 9) ») ; côté écran, `FICHES_LUES`
  ne les contient pas. La garde RIB (nom « RIB » ou IBAN valide dans le texte) reste en amont, inchangée.
- La lecture ne part QUE de la fenêtre de dépôt (fichier local) : un document déjà déposé ne peut pas être lu après
  coup. Les 2 pièces d'identité déposées le 12/11 sur 62774 (« CNI DAUBORD RECTO / VERSO ») ne seront donc jamais lues.
- Droits : `app_ged_lecture` et `app_ged_valeur` se lisent par « périmètre » = admin, manager, lecture (0 compte actif)
  OU biens du portefeuille. Comptes actifs : 4 admins, 2 commerciaux. `loadGedLectures` charge TOUTES les valeurs d'un
  bien à chaque ouverture des documents.
- ⚠ La descente de nuit (`phase2/sync/pull_from_supabase.py`) découvre les tables par la spec PostgREST et recopie
  toute table neuve du schéma public sur le serveur local : une table de pièces d'identité y serait recopiée.
- Fiche contact : `editContactOptimistic` → `app_edit_contact_optimistic` → `update_hektor_contact` ; la charge porte
  `birth_date`, `birth_place`, `marital_status`, l'adresse, mais renvoie la fiche ENTIÈRE (nom, téléphones…). Le
  conjoint d'une fiche de couple (bloc `_m2`) n'a PAS de date de naissance dans la charge : la remplir demanderait de
  toucher au worker.
**Découpage proposé** : 9a lire la pièce d'identité et la fiche de renseignements (sans rien écrire, interrupteur
neuf) ; 9b les règles P4 nom différent, P5 pièce périmée (cartes 2004-2013 : 15 ans), P6 une pièce par personne ;
9c remplir la fiche contact P1-P3 (après épreuve sur un contact fictif, personnes seules d'abord) ; 9d état civil et
financement, P7-P10. Décision attendue : où vivent le numéro, la date et le lieu de délivrance (même table, ou table à
part non exposée, non descendue, conservation 5 ans).

**✅ « B » puis « Vas y » (13/11) : LOT 9a ÉCRIT ET CONTRÔLÉ HORS LIGNE — RIEN POSÉ, RIEN POUSSÉ.**
- **Serveur** (`openai_ged_lecture_service.py`) : `FICHES_PERSONNES` à part de `FICHES` (les 25 types ne bougent pas) —
  `justif.identite` (liste `pieces` : nature, nom, nom d'usage, prénoms, date et lieu de naissance, numéro, date et
  autorité de délivrance, fin de validité ; JAMAIS adresse, sexe, taille, nationalité, signature, ligne codée) et
  `transaction.renseignements` (liste `personnes` : qualité, noms, prénoms, naissance, adresse, situation de famille,
  régime ; JAMAIS téléphone, e-mail, profession, revenus, banque, enfants, santé). Sortes neuves : `naissance` (dates
  dès 1900, les autres dates gardent 1950) et `piece` (le numéro, seule exception à la règle des longs numéros).
  `PRIVES` (numéro, date et autorité de délivrance) sort de la liste DANS `lire()` : jamais dans `app_ged_valeur`,
  jamais dans la réponse ; `enregistrer()` l'envoie à `app_ged_piece_privee_ecrire` AVANT les valeurs (échec → 503,
  les valeurs ne partent pas). La porte : sans l'interrupteur → 422 « lecture fermée » ; l'état civil et le
  financement restent refusés ; la garde RIB est inchangée et passe aussi sur la fiche de renseignements.
- **Route** (`routers/ged.py`) : l'interrupteur `ged_lecture_personnes` n'est lu QUE pour ces deux types, compte par
  compte (même règle à trois crans) ; `interrupteur(cle)` du portier prend la clé en paramètre (défaut inchangé).
- **Base** : `supabase/patch_ged_m9a_pieces_personnes_2026-11-13.sql` (+ `_INVERSE`, + `_REPETITION`) — schéma
  `ged_prive` (non exposé par l'API, donc ni lisible par l'app ni recopié par la descente), table `piece_identite`
  (clés limitées aux 3, effacement à 5 ans), écriture par la clé de service seule, lecture admin / manager actif /
  portefeuille (pas le rôle « lecture »), interrupteur posé éteint. **Répétition jouée le 13/11 : 6/6 VERT** (dont un
  témoin positif : 3 valeurs écrites, effacement à +5 ans ; un état des risques refusé), annulée ; relu après : rien
  n'est resté (0 schéma, 0 fonction, 0 interrupteur, 0 lecture d'essai).
- **Écran** : `FICHES_PERSONNES_LUES` (gedLecture.ts), `useGedLecturePersonnes` (ged.ts), `typeLu()` aux deux endroits
  du dépôt (DepotDocuments.tsx) ; résumés « Lu : carte d'identité valable jusqu'au … » / « fiche de renseignements · du …
  · 2 vendeurs » — ⚠ SANS nom (la règle de tous les résumés depuis le lot 2), ni naissance, ni adresse ; l'écran ne
  connaît pas le registre.
- **Essais** : serveur 80 + **35** (`tests/test_ged_lire_personnes.py`) + classer 28 ; écran lecture **59** (dont 10 neufs),
  dépôt 19, règles 44 + 84, Reçu/Manque 29, remplir 27, classement 25 ; **build vert**. Témoins inverses : sans le filtre
  `PRIVES` → ROUGE « la réponse ne porte ni le numéro ni la délivrance » ; sans l'interrupteur à l'écran → ROUGE.
- ⏳ **Ordre, chacun sur accord** : poser le patch → commit et push (Render, Vercel) → `ged_lecture_personnes` en admin →
  essai réel sur 63331 avec de FAUSSES pièces « SPÉCIMEN » fabriquées (jamais une vraie ; les CNI DAUBORD de 62774 ne
  peuvent pas être lues).
✅ **« Oui, pose et pousse » (13/11)** : patch m9a POSÉ par `node Console/apply_sql_patch.js` (connecteur Supabase
toujours en panne) ; ses **7 contrôles VERTS**, relus à part (table et RLS ; aucun droit des rôles de l'app ; schéma
fermé à anon et authenticated ; écriture par la clé de service seule ; lecture authenticated, pas anon ;
`ged_lecture_personnes` **off** ; registre vide). Code commité et poussé dans le même geste.
✅ **« Oui, allume et essaie » (13/11)** : `ged_lecture_personnes` → **admin** à 15:17:55 UTC (apply_sql_patch.js,
transaction gardée, relu). **ESSAI RÉEL SUR 63331, par l'écran, dans le Chrome de Frédéric**, 3 pièces ENTIÈREMENT
FICTIVES marquées « SPÉCIMEN - FICTIF » (scratchpad `ged_m9/fabriquer_pieces_specimen.py`) : une carte nouveau
modèle (photo, ligne codée fictive), une ancienne carte recto + verso en PDF scanné (adresse et taille au verso), une
fiche de renseignements de deux vendeurs (téléphone, e-mail, profession, nationalité écrits).
- Type proposé : « le nom et l'IA sont d'accord » pour les 3. Envoyés chez Hektor : 3 `upload_document_to_hektor`
  **done** (15:20:42, 15:21:09, 15:21:23), relecture done 15:22:01.
- **3 lectures « lu »** (gpt-6-luna, 0,0013 $ en tout). Écran : « carte d'identité valable jusqu'au 03/03/2033 »,
  « … jusqu'au 13/06/2022 », « fiche de renseignements · du 01/10/2026 · 2 vendeurs » ; après rechargement « Lu par
  l'IA : 11 documents », « Prise de mandat : 2 pièces sur 5 » (la pièce d'identité est trouvée).
- **Valeurs** : nature (ancien / nouveau modèle justes), nom, nom d'usage, prénoms, lieu de naissance, fin de validité ;
  la fiche : les 2 vendeurs complets (naissance, adresse, CP, ville, « marié », communauté légale).
- **Registre `ged_prive`** : ancienne carte = numéro EX0612300175, délivrée le 2012-06-14, PRÉFECTURE DE LA LOIRE ;
  nouvelle carte = numéro X4RTBPFW4 (sa date de délivrance n'est pas imprimée : rien) ; effacement 2031-11-13.
- **0 FUITE**, mesurée sur toutes les valeurs du bien : aucun numéro ni délivrance dans `app_ged_valeur`, ni ligne
  codée, ni téléphone, e-mail, profession, nationalité, taille ; pas l'adresse du verso de la carte.
- ⚠ **TROUVÉ : la date de naissance des 2 CARTES n'est pas gardée** (celle de la fiche de renseignements, si). Cause
  (déduite, pas mesurée : le serveur ne garde pas la réponse brute) : la consigne v1 disait « tels qu'imprimés » et le
  champ `naissance` n'annonçait pas son format → « 02 04 1938 », rejeté par la normalisation. Preuve indirecte : la fin
  de validité, imprimée pareil sur la même carte mais annoncée AAAA-MM-JJ, est passée. **Correctif écrit, NON
  poussé** : fiche `justif.identite` **v2** (format AAAA-MM-JJ annoncé pour `naissance`, dit dans la consigne ; nom
  d'usage sans « ép. ») ; essais 37 + 80 + 59 VERTS. À éprouver par un nouveau dépôt après le push.
✅ **« Oui, pousse et refais » puis « Ok vas y » (13/11)** : le push de `bc16ffe` a trouvé `origin/main` déjà plus loin —
une autre session avait poussé jusqu'à `685d775`, AVEC `bc16ffe` et son `e2f5861` dessous ; rien à pousser de plus.
Render sur `fb50639` (contient `bc16ffe`) à 15:36. **2e dépôt sur 63331** : ⭐ le garde-fou anti-doublon a REFUSÉ les
mêmes fichiers renommés (« Déjà dans ce dossier (…) : l'envoyer quand même ») ; refaits avec un contenu différent
(mention « ESSAI 2 », `ged_m9/fabriquer_pieces_specimen_essai2.py`), noms « ESSAI2 Piece identite SPECIMEN … ».
- 2 lectures `justif.identite/2` « lu » ; envois chez Hektor done 16:02:39 et 16:02:52.
- ✅ **Date de naissance GARDÉE** : 1938-04-02 et 1960-05-12. ✅ Nom d'usage « ESSAI » (sans « ép. »). Registre : les
  mêmes valeurs que le 1er dépôt. **0 fuite.**
- ⚠ **La nature de la carte neuve est lue « ancien modèle »** (juste au 1er dépôt) : ma fausse carte n'a pas le dessin
  d'une vraie, l'IA hésite. Sans effet sur la règle de validité de 9b : le bonus de 15 ans ne concerne que les cartes
  dont la fin imprimée tombe entre 2014 et 2023, et celle-ci finit en 2033. À regarder sur de vraies pièces (mesure).

**✅ « Vas y » (13/11) : LOT 9b ÉCRIT ET CONTRÔLÉ HORS LIGNE — RIEN POUSSÉ, rien en base.** Frédéric n'a pas tranché
« garder / remplacer » la ligne « Pièce d'identité de chaque mandant » : ma recommandation est appliquée, elle RESTE
(elle reconnaît les anciens documents par leur nom) et P6 s'ajoute.
- `src/lib/gedReglesPersonnes.ts` (pur) : `piecesLuesDe` (une entrée par pièce, nom lu NETTEMENT), `finEffective`,
  `reglesPersonnes` ; branché dans `RecuManque.tsx` avec les autres règles (même tri, même interrupteur
  `ged_propositions`). Ne connaît pas le registre (numéro, délivrance).
  - **P4 le nom** : chaque pièce face aux mandants de la fiche ET aux acquéreurs des offres et compromis VIVANTS, par le
    nom de naissance OU d'usage : inconnue → alerte ; écrite autrement (prénom absent, couple) → information.
  - **P5 la validité** : référence = le compromis vivant le plus récent, sinon la signature du mandat LUE, sinon le début
    du mandat de la fiche, sinon aujourd'hui. Carte d'identité dont la fin imprimée tombe du 02/01/2014 au 31/12/2023 :
    +5 ans (délivrée 2004-2013), sauf mineur à la délivrance (naissance lue) — le « modèle » lu ne décide PAS (l'IA l'a
    mal lu au 2e essai). Passeport, titre de séjour, permis : la date imprimée. Périmée à la référence → alerte ; valide
    au mandat mais périmée aujourd'hui avant tout compromis → information.
  - **P6 une pièce par personne** : chaque mandant, et chaque acquéreur d'un compromis vivant ; ne parle que si une
    pièce au moins a été LUE sur le bien ; « couverte » = nom ET prénom (le nom seul ne suffit que si la fiche n'a pas
    de prénom).
- **Essais** : `test_ged_regles_personnes.cjs` **32 VERT** ; tous les autres GED verts (59, 84, 44, 29, 27, 19, 25) ;
  build vert. ⭐ Les essais ont trouvé 2 défauts avant toute mise en ligne : « le passeport… était périméE » (accord), et
  P6 qui tenait Jeanne FICTIF pour couverte par la pièce de Marc FICTIF (le nom seul). Témoin inverse : sans la
  prolongation → 4 ROUGE.
- **Banc d'écran** (`scratchpad/ged_m9_vue`, launch « ged-banc-m9 », hors ligne) : « À regarder (3) » = la pièce de Paul
  DURAND (inconnu), le passeport de Marc FICTIF périmé au mandat du 02/03/2026, la pièce de Luc ABSENT non trouvée ; la
  carte de Jeanne (fin imprimée 2022, prolongée 2027) se tait. Console sans erreur.
- ✅ « Oui » (14/11) : commité et poussé (Vercel). ⏳ Reste à le regarder sur 63331 (attendu : les pièces SPECIMEN / FICTIF face à la
  fiche du bien d'essai).

**👁 9b REGARDÉ EN RÉEL sur 63331 (14/11, Chrome de Frédéric, lecture seule, console sans erreur).** « À regarder (10) »
dont 5 lignes de 9b ; le mandant de la fiche est « Mandant ESSAI 8A C1 », les pièces sont celles des 2 essais (Marc FICTIF,
Jeanne SPECIMEN, chacune déposée deux fois).
- **P4 alerte** : « La pièce d'identité de Marc FICTIF n'est ni à un mandant ni à un acquéreur du bien » — JUSTE (il n'est
  pas sur la fiche), mais **affichée DEUX FOIS** (une par dépôt).
- **P4 information** : « La pièce dit « Jeanne, Marie SPECIMEN (nom d'usage ESSAI) », la fiche « Mandant ESSAI 8A C1 » » —
  **DEUX FOIS aussi** (la 1re lecture porte encore « ép. ESSAI », fiche v1). Le « proche » vient du nom d'usage ESSAI de la
  fausse carte, qui croise le nom du mandant d'essai : artefact des données d'essai, la règle fait ce qu'elle dit.
- **P5** : muette, et c'est JUSTE (ancienne carte de Jeanne finie en 2022 → prolongée 2027 ; cartes neuves → 2033).
- **P6** : « Pièce d'identité de Mandant ESSAI 8A C1 : non trouvée parmi les pièces lues » — JUSTE selon la règle (un
  « proche » ne couvre pas une fiche qui a un prénom).
- ⚠ **DÉFAUT VU : une ligne PAR PIÈCE, pas par personne.** La même personne déposée deux fois (ou CNI + passeport, cas
  réel courant) répète la même ligne. → **« Oui regroupe » (14/11) : CODÉ** — P4 regroupée par personne (verdict + nom
  normalisé de la pièce + personne de la fiche), une seule ligne suivie de « (N pièces) ». Essais **35 VERT** (+3, dont
  2 témoins inverses : sans le regroupement → 2 ROUGE) ; tous les autres GED verts ; build vert. **Poussé le 14/11 sur « Oui » (`661240e`) et VU sur 63331** : « À regarder » passe de 10 à 8 —
  « …Marc FICTIF n'est ni à un mandant ni à un acquéreur du bien (2 pièces) » et l'information sur Jeanne « (2 pièces) ».
  ⚠ Même famille, NON TOUCHÉE (à trancher) : P5 juge aussi pièce par pièce — un passeport périmé sonne même si la
  personne a une carte valide au dossier, et une carte périmée déposée deux fois sonne deux fois. ⚠ Et P4 redit en partie la ligne déjà existante « Marc FICTIF (mandant au mandat) n'est pas
  parmi les mandants du bien » (règle du mandat lu, morceau 7) : deux angles différents, à garder ou fondre — à trancher.

**✅ « P5 aussi » (14/11) : P5 JUGÉE PAR PERSONNE — écrit, contrôlé et poussé le 14/11.** Une personne est en règle si UNE de
ses pièces est valable à la date de référence : un vieux passeport périmé se tait à côté d'une carte valable ; la même
pièce périmée déposée deux fois ne sonne qu'une fois. Quand aucune ne vaut, c'est la pièce qui va LE PLUS LOIN qui parle,
avec « (N pièces, aucune valable) ». Même règle pour l'information « périmée depuis » (avant compromis). Clé de la
personne : prénom + nom de la pièce, normalisés (comme P4). Essais **38 VERT** (+3) ; témoin inverse (une ligne par
pièce) → **3 ROUGE** ; tous les autres GED verts ; build vert. Sur 63331 rien ne doit changer (toutes les pièces y sont
valables).

**🔎 AUDIT DU LOT 9c (14/11, lecture seule, rien codé) — remplir la fiche contact depuis les pièces.**
Ce que P1-P3 veulent dire ici (aucun document ne les définissait : déduit du découpage du 13/11 et des 3 cases que le
geste contact sait écrire) : **P1 date de naissance**, **P2 lieu de naissance** (pièce d'identité OU fiche de
renseignements), **P3 situation de famille** (fiche de renseignements seule). Jamais l'adresse, jamais le régime.
- **Le geste existe et accepte un envoi PARTIEL** : `app_edit_contact_optimistic` (empreinte `eb93494b`) n'écrit chez nous
  que les clés reçues (`birth_date`, `birth_place`, `marital_status` y sont), pose la bannette `app_contact_pending`
  (anti-écrasement par `_date_maj`) ; `app_contact_enqueue_due_pushes` enfile `update_hektor_contact` avec ces seules clés.
- ⚠ **Le worker EXIGE le nom** (`normalizeHektorContactPayload`, `requireName`) : un envoi « date de naissance seule »
  ÉCHOUERAIT. Il faut joindre le nom ACTUEL, inchangé. Le wrapper écran `editContactOptimistic` l'exige déjà.
- Le worker relit le formulaire de Hektor et ne remplace QUE les champs envoyés (`dateNaissance` en JJ-MM-AAAA par
  `normalizeOptionalFrenchDate`, `lieuNaissance`, `marital_status`) ; un couple est relu comme couple (bloc `_m2`).
- ⚠ **D-4 (déjà noté au chantier partenaires)** : chaque modification ajoute `_email_rgpd=1` sauf `send_rgpd_email: false`.
  Le geste de 9c l'enverra à `false` (la clé n'a pas de colonne : elle part dans la charge seulement).
- ⚠ **Le contrôle au retour (8a5, `contact_retour_controle` ON) NE JUGE PAS ces 3 champs** : `app_contact_champs_modif`
  ne connaît que nom, prénom, civilité, e-mail, 2 téléphones, adresse, CP, ville, commentaires. Sans patch, un remplissage
  n'a de fin visible que par la relecture de la fiche.
- Codes Hektor mesurés (`app_contact_current`) : `married` 43, `single` 28, `widower` 15, `divorced` 8, `civil_union` 3
  — 94 859 vides. Traduction : marie, celibataire, veuf, divorce, pacse ; **separe, concubinage, autre → rien**.
- L'écran ne connaît des mandants que nom et prénom (`personnesGedDuBien`, `DetailContact` sans naissance) : il faudra
  relire `app_contact_current` (3 cases + `nature_fiche`) pour proposer, et RELIRE au clic (case vide), comme le morceau 8.
- Contact d'épreuve tout trouvé : **20000009 « Mandant ESSAI 8A C1 »**, mandant de 63331, personne seule, 3 cases vides.

**✅ LOT 9c CODÉ (14/11, après le « oui » de Frédéric : SANS le patch du contrôle au retour) — rien poussé, rien posé.**
Décision du 14/11 : on ne lie pas 9c à l'extension du contrôle au retour. Ce contrôle ne juge DÉJÀ pas ces 3 cases pour la
fenêtre « Modifier » (trou ancien, de tout le chemin contact) ; l'étendre touche TOUTES les modifications de contact, et
le risque de fausses alertes (lieu réécrit par Hektor) n'est pas mesuré. ➡ **Morceau à part, plus tard** : une répétition
sans écrire sur les modifications récentes, compter les écarts, puis poser (accord) ou d'abord une comparaison tolérante.
- **Les clés** (pour ne pas les confondre avec P1-P4 du bien) : `C1.birth_date.<contact>`, `C2.birth_place.<contact>`,
  `C3.marital_status.<contact>`. Même table `app_ged_decision`, même interrupteur `ged_remplir` (admin).
- **`src/lib/gedRemplirContact.ts`** (pur, neuf) : `propositionsContact(contacts, personnesDuBien, docs, decisions, aujourdhui)`.
  Sources : `justif.identite` (liste `pieces`) et `transaction.renseignements` (liste `personnes`), valeurs `lu` seulement.
  Rattachement STRICT : nom de naissance OU d'usage ÉGAL (sans casse, accents ni ponctuation) ET premier prénom égal — pas
  le verdict « egal » de `personneSurLaFiche`, trop large ici (un mot du nom suffit) ; et une SEULE personne du bien qui
  les porte. Personne seule seulement. Date : AAAA-MM-JJ réelle, après 1900, avant aujourd'hui. Deux pièces qui
  disent deux valeurs : rien (une situation sans code Hektor compte comme une voix et contredit).
- **`src/lib/ged.ts`** : `loadContactsEtatCivil(ids)` relit `app_contacts_current` (la VUE : même périmètre que
  l'annuaire) ; erreur → `null` → aucune proposition contact.
- **`src/RecuManque.tsx`** : prop `contactsDuBien` ; relecture de l'état civil à chaque tour (`relire`) ; les propositions
  contact s'ajoutent à « À remplir » ; bouton « Remplir la fiche du contact ».
- **`src/App.tsx`** : `contactsGedDuBien` (numéro = `sourceId`, `seul` = pas de membres ni de `refCouple`) et la branche
  `contact` de `remplirDepuisDocument` : relit le contact → personne seule active → case encore vide (`caseVide` pour la
  date) → nom présent → `editContactOptimistic({ lastName: nom ACTUEL, personType, sendRgpdEmail: false, <le champ> })`
  → `hektor:contact-updated` → décision « remplie ». Sinon décision « echec » avec son motif, et RIEN d'écrit.
- **Vérifié avant de coder, ce que l'envoi partiel ne casse pas** : la charge porte aussi `contact_kind` (« acquereur » par
  défaut de `hContactPayload`) et `person_type`, mais (a) `app_edit_contact_optimistic` n'en fait rien (aucune colonne),
  (b) le worker en modification ne pose NI `qualification` NI `statut` (seulement à la création : `applyHektorContactIdentityValues`),
  (c) `app_contact_champs_modif` ne juge que le nom, joint inchangé → aucune fausse alerte au retour. Aucune recherche
  n'est créée en modification. L'e-mail RGPD est coupé.
- **Essais** : `node test_ged_remplir_contact.cjs` → **40 verts, 0 rouge** (témoins inverses compris ; l'essai « rien
  d'autre n'est envoyé » a lui-même été éprouvé : il voit un téléphone glissé dans l'appel). Les essais voisins restent
  verts : remplir 27, règles personnes 38, règles lues 84, règles 44. `npm run build` vert.
- ⚠ **Trouvé en passant, NON traité (hors périmètre)** : des `birth_place` de `app_contact_current` portent du texte de
  COMMENTAIRE (« …Recontacter le 28 février…]]> ») — un défaut de lecture XML côté synchro. 9c n'y écrit pas (case non
  vide = rien). Non compté.
- **Reste, sur accord** : pousser ; puis l'**épreuve réelle** sur 63331 / contact 20000009 avec une pièce SPÉCIMEN
  fabriquée à son nom (C1 et C2 par la pièce d'identité ; C3 demande une fiche de renseignements SPÉCIMEN) ; vérifier
  chez nous à l'instant, puis chez Hektor après le passage du worker (≈ 10 min de délai d'envoi), la valeur exacte.
  Retour arrière : `ged_remplir` → off ; une valeur écrite se vide à la main par la fenêtre « Modifier ».

**✅ 9c POUSSÉ (15/11, `77509ae` seul ; Vercel prêt). ⚠ ÉPREUVE RÉELLE DU 16/11 : ELLE A TROUVÉ UN DÉFAUT — 9c était MUET.**
« Oui lance la » (16/11), sur 63331 dans le Chrome de Frédéric. Pièces fabriquées : `scratchpad/ged_m9c/fabriquer_pieces_specimen_9c*.py`
(carte nouveau modèle + fiche de renseignements d'un vendeur, « SPÉCIMEN - FICTIF », naissance 14/07/1955 à ROANNE (42),
célibataire). Avant le dépôt : aucune proposition contact (point de départ).
- **1er dépôt** (07:16 UTC, envois Hektor done) : date, lieu, prénom, « celibataire » lus, MAIS le nom « ESSAI 8A C1 » est
  « non vu » sur les deux pièces : la lecture REFUSE tout nom qui porte un chiffre (`openai_ged_lecture_service.py` l. 524,
  garde-fou voulu : un chiffre trahit une adresse, une date, un numéro). Juste pour un vrai client : NON TOUCHÉ. Le défaut
  était le nom du contact d'essai.
- **« Oui » (16/11) : le contact 20000009 RENOMMÉ « ESSAI CONTACT »** par la fenêtre « Modifier » (travail
  `update_hektor_mandant_contact` done en 15 s chez Hektor, fiche 605947, rien resté en attente). ⚠ Vu, NON mesuré : le
  compte rendu donne à la commune `idCode 1`, `idVille 1`. **2e dépôt** (07:20) : nom « ESSAI CONTACT » lu sur les deux
  pièces, mêmes valeurs. La ligne P6 « Pièce d'identité de Mandant ESSAI 8A C1 : non trouvée » DISPARAÎT (la pièce est
  reconnue). Mais **aucune section « À remplir »**.
- ⛔ **LA CAUSE — DEUX NUMÉROS** : les contacts d'un bien à l'écran portent le numéro HEKTOR (`DetailContact.sourceId`,
  605947) ; `app_contact_current.hektor_contact_id` est NOTRE numéro (20000009, ≥ 10 000 003) — **0 égaux sur 94 956** ;
  le numéro Hektor est dans `hektor_target_id` (rempli partout, UNIQUE, ≤ 606 355). 9c lisait par `hektor_contact_id`
  avec le numéro Hektor : AUCUNE ligne, pour AUCUN contact. Inerte (plages disjointes : jamais le mauvais contact), mais
  muet. J'avais écrit le 14/11 que `sourceId` était la clé de `app_contact_current` : FAUX, et les essais hors ligne ne
  pouvaient pas le voir (ils testent la fonction pure, pas la jointure).
- **RÈGLE DE FRÉDÉRIC (16/11)** : « ID Hektor pour communiquer avec Hektor, worker etc. ; et notre ID app pour notre app ».

**✅ « Vas y » (16/11) : 9c CORRIGÉ — rien poussé.**
- `src/lib/ged.ts` : `loadContactsEtatCivil(ids, par: 'hektor' | 'app')` — `'hektor'` lit par `hektor_target_id` (le PONT
  écran -> notre fiche), `'app'` par `hektor_contact_id` ; la carte est rangée par la colonne lue ; un numéro Hektor porté
  par deux fiches (aucun au 16/11) est ambigu et sort de la carte.
- `src/RecuManque.tsx` : l'écran lit par `'hektor'` ; la proposition porte NOTRE numéro (`String(r.hektor_contact_id)`),
  donc la clé de décision aussi (`C1.birth_date.20000009`). Aucune décision C* n'existait : rien à migrer.
- `src/App.tsx` (branche `contact` de `remplirDepuisDocument`) : relecture au clic par `'app'` (notre numéro), écriture
  `editContactOptimistic` par notre numéro comme ses autres appelants ; la décision garde aussi `numero_hektor`.
- **Essais** `test_ged_remplir_contact.cjs` : **48 verts, 0 rouge** (+8, dont un bloc ⑤ qui rejoue la lecture contre une
  fausse base aux deux colonnes). **Témoin inverse** (l'ancienne colonne remise) -> **2 ROUGES**, puis restauré -> 48.
  Voisins verts : remplir 27, règles personnes 38, règles lues 84, règles 44. `npm run build` vert.
- **Reste, sur accord** : pousser, puis REJOUER l'épreuve sur 63331 (les 2 pièces « ESSAI CONTACT » déjà lues resservent,
  rien à redéposer) : 3 propositions attendues (14/07/1955, « ROANNE (42) », « célibataire »), 3 clics, contrôle chez nous
  (`scratchpad/ged_m9c/controle_epreuve_9c.sql`) puis chez Hektor sur 605947. Sur 63331 restent 4 pièces SPÉCIMEN de plus.

**✅✅ 9c ÉPROUVÉ EN RÉEL DE BOUT EN BOUT (16/11) — « Oui pousse et rejoue ».** `a3539e9` poussé SEUL (relu juste avant :
seul au-dessus d'`origin/main`), Vercel prêt. Sur 63331, dans le Chrome de Frédéric :
- **« À remplir (3) »** apparaît : « Mandant ESSAI CONTACT : date de naissance 14/07/1955 », « … lieu de naissance ROANNE
  (42) », « … situation de famille « célibataire » », source « ESSAI9C2 Fiche de renseignements… page 1 ». ⭐ Témoins
  vivants : rien pour Marc FICTIF ni Jeanne SPECIMEN (pas des contacts du bien), rien depuis les 2 pièces « ESSAI 8A C1 »
  (nom illisible). Console sans erreur.
- **3 clics** (07:51:49, 07:52:02, 07:52:17 UTC), chacun « Envoyé : … part chez Hektor par le chemin habituel », puis
  « À remplir (0) ». **Chez nous à l'instant** : `birth_date 1955-07-14`, `birth_place ROANNE (42)`, `marital_status
  single` ; 3 décisions `remplie` sous NOTRE numéro (`C1.birth_date.20000009`…), le détail porte `numero_hektor 605947`
  et `email_rgpd false` ; bannette : `last_name` inchangé + les 3 champs (+ `contact_kind`/`person_type`, sans effet).
- ⚠ La bannette porte `send_rgpd_email: "false"` en TEXTE : vérifié, le worker le lit comme non
  (`console_job_worker.js` l. 19587 accepte `false`, `"false"`, `"0"`). Aucun e-mail RGPD.
- **Chez Hektor** : `update_hektor_contact` done 08:03:18 sur **605947** (`date_naissance 14-07-1955`, `lieu_naissance
  ROANNE (42)`, `statut_matrimonial single`) ; relecture `refresh_console_contact_data` done 08:03:34 (détail Hektor relu
  08:03:24). **Après la relecture DEPUIS HEKTOR**, notre fiche porte toujours les 3 valeurs : Hektor les a gardées. Rien
  d'autre n'a bougé (prénom, e-mail, adresse, CP, ville intacts ; « coordonnées remplacées » du compte rendu = la logique
  des téléphones, aucun envoyé, aucun avant ni après) ; type toujours `mandant` / `proprietaire` ; contrôle au retour
  (`app_v_contact_modif_ecarts`) : **aucun écart**.
- **Reste sur 63331** : 4 pièces SPÉCIMEN de plus ; le contact d'essai 20000009 s'appelle désormais « ESSAI CONTACT »
  et porte l'état civil fictif. Pour revenir : `ged_remplir` -> off ; les valeurs se vident par la fenêtre « Modifier ».
- ⚠ Toujours NON mesuré : `idCode 1` / `idVille 1` de la commune au renommage (compte rendu du 1er geste).

**🔎 AUDIT DU LOT 9d (16/11, « A », lecture seule, rien codé, rien écrit) — l'état civil et le financement.**
Audit limité aux documents `justif.etat_civil` et `transaction.financement` ; objets touchés : document (lire), contact,
transaction et mandat (lire seulement) ; aucun geste chez Hektor dans la proposition de base.
- **P7-P10 n'étaient écrits NULLE PART** (note, catalogue E, rapports A-D) : le découpage du 13/11 dit seulement « 9d état
  civil et financement, P7-P10 ». Ce qui suit est une PROPOSITION, à trancher.
- **Le cadre est celui du 12/11 (§12.1)**, qui DÉPASSE les « plus tard / jamais » des experts (EC-1, EC-2, FIN-2, REN-2,
  ID-3) : les pièces des personnes SONT lues, état civil et financement compris ; mesure de protection : sa nature, le
  représentant, la date du jugement, JAMAIS le motif ni la santé ; RIB jamais. Restent « jamais » sans décision contraire :
  montant, taux, durée, banque, apport, assurance du prêt (santé), revenus ; les enfants d'un livret.
- **Code** : `app_ged_type` a déjà les deux types en `lecture = lue`, `sensible = true` ; le serveur les refuse (422 « lue
  plus tard (morceau 9) », `openai_ged_lecture_service.py` l. 596) car ils ne sont pas dans `FICHES_PERSONNES` ; l'écran
  les connaît déjà comme pièces attendues (`gedPieces.ts` l. 79, 93, 108) et par le nom (`gedTypeParNom.ts`). La règle
  FIN-1 du catalogue V1 (J-7 avant la date limite du prêt sans pièce de financement) n'est PAS codée. Pages envoyées par
  défaut : 4 en image + un extrait de texte (`LECTURE_PAGES_HD`, `texte_max`) — ⚠ une offre de prêt porte l'assurance
  (santé) plus loin : il faudra n'envoyer QUE la 1re page pour ce type (à vérifier : que l'extrait de texte suit bien les
  mêmes pages).
- **Mesure (par le NOM, approchée, tout le stock `app_console_document`)** : financement **4 490 documents / 2 782 biens,
  357 ces 30 jours** (offre de prêt 1 173, accord 883, simulation 527, refus 200) ; état civil **995 / 688 biens, 73 ces
  30 jours** (protection — tutelle, curatelle, habilitation — 264, jugement ou ordonnance 285, décès 196, livret 149,
  divorce 94, contrat de mariage ou PACS 92). Dans la GED (dépôts de l'app) : 0 hors essais (tout est en « admin »).
- **Proposition** :
  - **P7 — le prêt à la date limite** (financement ↔ compromis lu). Lire : nature (`offre_de_pret`, `accord_de_principe`,
    `refus`, `simulation`, `autre`), date du document, emprunteurs (noms). Dire : date limite passée sans offre ni accord
    lu avant elle → alerte ; un REFUS lu → alerte (« la condition suspensive peut jouer ») ; une simulation seule → info
    (« une simulation n'est pas un accord ») ; + FIN-1 (J-7 sans aucune pièce de financement), sans lecture.
  - **P8 — l'emprunteur est l'acquéreur** : emprunteurs lus ↔ acquéreurs du compromis vivant (comparateur `personnes`) ;
    inconnu → alerte « pièce d'une autre affaire ».
  - **P9 — le conjoint** (C. civ. 215 al. 3, logement de la famille) : lire sur livret / acte de mariage / contrat / PACS
    (et la fiche de renseignements déjà lue) : nature, date, les deux époux ou partenaires ; jamais les enfants. Dire : un
    mandant marié dont le conjoint n'est ni mandant ni signataire du mandat lu → alerte « consentement du conjoint à
    vérifier » (« à vérifier » : on ne sait pas si c'est le logement de la famille).
  - **P10 — la capacité et le décès** : lire sur jugement / ordonnance / acte de décès : nature de la mesure (tutelle,
    curatelle, sauvegarde, habilitation familiale), personne protégée, représentant, date du jugement ; décès : personne,
    date. JAMAIS le motif, la santé, un certificat médical. Dire : personne protégée mandante sans son représentant parmi
    les signataires du mandat lu → alerte ; tutelle → info « autorisation du juge à prévoir » ; mandant décédé avant la
    signature → alerte « succession : ce sont les héritiers qui signent ».
- **À trancher par Frédéric** : (1) P7-P10 tels quels, ou une partie ; (2) les valeurs de PROTECTION dans `app_ged_valeur`
  (visibles du négociateur du bien, comme le reste) ou au registre à part `ged_prive` (recommandé : santé indirecte,
  art. 9) ; (3) la situation de famille lue sur un livret ou un acte de mariage nourrit-elle aussi C3 (9c) — recommandé
  plus tard ; (4) l'ordre : financement d'abord (flux 5 fois plus fort, règle la plus utile), état civil ensuite.
- **Ce que ça pourrait casser** : rien d'existant (types neufs dans `FICHES_PERSONNES`, derrière `ged_lecture_personnes`
  en « admin ») ; risque RGPD si la 1re page ne suffit pas et qu'on élargit ; un « décès » ou une « protection » mal lus
  crieraient fort : niveau « à vérifier », jamais un blocage.

**✅ « Oui, financement » (16/11) : LOT 9d-1 (LE FINANCEMENT, P7 et P8) ÉCRIT ET CONTRÔLÉ HORS LIGNE — rien poussé, rien posé.**
Pas de patch SQL : `transaction.financement` est déjà `lue` et `sensible` dans `app_ged_type` ; il manquait la fiche au
serveur. Tout reste derrière `ged_lecture_personnes` (lecture) et `ged_propositions` (règles), en « admin ».
- **Serveur** (`openai_ged_lecture_service.py`) : fiche `transaction.financement` v1 DANS `FICHES_PERSONNES` — `nature`
  (`offre_de_pret`, `accord_de_principe`, `refus`, `simulation`, `autre`), `date_document`, liste `personnes` (qualité
  emprunteur / co_emprunteur / caution / autre, nom, nom d'usage, prénoms). JAMAIS montant, taux, durée, mensualités,
  coût, banque ou courtier, apport, revenus, assurance, santé, compte, adresse. ⛔ `premiere_page_seule` : le serveur
  REDIT la 1re page (texte coupé au repère « --- page 2 --- », images des autres pages retirées) APRÈS la garde RIB, qui
  regarde tout ce qui arrive ; `texte_max` 6 000.
- **Écran** : `FICHES_PERSONNES_LUES` + financement ; `gedClassementIa.ts` `PREMIERE_PAGE_SEULE` (texte et image de la
  page 1 seulement ; la garde RIB lit toujours toutes les pages AVANT) ; résumé « offre de prêt · du … · 2 emprunteurs »
  (jamais un nom).
- **Règles** `src/lib/gedReglesFinancement.ts` (pure), branchées dans `RecuManque` avec les autres. Rien sans compromis
  VIVANT. Le compromis lu le plus récent avec `condition_pret = oui`, rattaché à UNE ligne (`resoudreCible`), donne la
  date limite.
  - **P7** : refus lu -> alerte ; limite dans 7 jours ou passée sans AUCUNE pièce de financement (type ou NOM d'un ancien
    document) -> pièce à déposer / alerte (FIN-1) ; limite passée, pièces lues sans offre ni accord -> alerte (information
    si une pièce non lue est au dossier) ; accord daté APRÈS la limite -> information (prorogation ?) ; accord sans date
    lue -> silence ; seule une simulation (limite à venir) -> information.
  - **P8** : une pièce dont AUCUN emprunteur n'est acquéreur (registre + compromis lu) -> alerte, une ligne par groupe
    d'emprunteurs ; aucun acquéreur connu -> silence.
- **Essais** : `test_ged_regles_financement.cjs` **32 verts** ; `backend/tests/test_ged_lire_financement.py` **19 verts**
  (`PYTHONIOENCODING=utf-8`). **Témoins inverses** : la coupe à la 1re page retirée du serveur -> ROUGE (l'assurance et le
  montant partaient) ; la garde « compromis vivant » retirée -> ROUGE (un refus sur un compromis annulé sonnait) ; restaurés
  -> verts. Essais adaptés (le financement n'est plus « fermé » ; leurs témoins passent à l'état civil, toujours fermé) :
  lire 80, lire personnes 36, lecture 59, règles personnes 38 ; voisins verts (remplir contact 48, remplir 27, règles lues
  84, règles 44, classer 28). `npm run build` vert.
- **Reste, sur accord** : pousser (Render pour le serveur, Vercel pour l'écran), puis l'épreuve réelle sur un bien d'essai
  avec un compromis vivant : une fausse offre de prêt SPÉCIMEN de PLUSIEURS pages (une page « assurance » en 2) pour
  prouver que seule la 1re part. ⚠ Une offre en PDF texte qui porte un IBAN est refusée en bloc par la garde RIB : voulu.

**✅ 9d-1 EN LIGNE ET LA LECTURE ÉPROUVÉE EN RÉEL (16/11, « Vas y »).** `251b784` est parti chez GitHub AVEC `bf47572` (l'autre
session l'a poussé juste au-dessus ; mon push, arrivé après, a été refusé sans effet) ; Vercel et Render (`/health`) sur
`bf47572`, qui le contient. Épreuve sur 63331 dans le Chrome de Frédéric, 3 pièces FICTIVES « SPÉCIMEN » fabriquées
(`scratchpad/ged_m9d/fabriquer_offres_specimen.cjs` et `fabriquer_offre_scan.py`) : une offre de prêt de 3 pages en TEXTE et
la même SCANNÉE — page 1 nature, date 02/11/2026, emprunteurs SPECIMEN Paul et Lucie ; page 2 « assurance emprunteur,
questionnaire de santé » (MARQUEUR-SANTE-P2) ; page 3 montant, taux, banque, revenus (MARQUEUR-MONTANT-P3) — et un accord
de principe avec un IBAN fictif en page 3.
- Les 3 proposées en « Financement » ; 3 envois Hektor done (09:15:52, 09:16:06, 09:16:23 UTC).
- **Offre en texte** : lue PAR LE TEXTE SEUL (`par_texte` vrai, aucune image), **1 033 jetons** (la page 1 seule).
  **Offre scannée** : `pages_lues = {1}`, 3 043 jetons. Les deux : « Lu : offre de prêt · du 02/11/2026 · 2 emprunteurs » ;
  valeurs `nature offre_de_pret`, `date_document 2026-11-02`, SPECIMEN Paul (emprunteur) et Lucie (co_emprunteur) ;
  **toutes en page 1, aucune fuite** (ni marqueur, ni montant, ni taux, ni banque, ni santé). Coût 0,0007 $.
- **Accord avec IBAN** : AUCUNE lecture (garde RIB, toutes les pages lues avant de couper). ⚠ **TROUVÉ, NON TRAITÉ** : la
  fenêtre de dépôt l'a RANGÉ en « RIB » (`justif.rib`) — règle existante (`DepotDocuments.tsx` l. 220 : un IBAN trouvé
  chez nous pré-choisit RIB si personne n'a choisi). Conséquence pour 9d : une VRAIE offre de prêt qui porte l'IBAN du
  compte de prélèvement dans son texte sera rangée en RIB et jamais lue ; le négociateur peut corriger le type (la
  lecture restera refusée, voulu). À trancher : garder, ou ne pas pré-choisir RIB quand l'IA ou le nom disent
  « financement ».
- **Écran** : « À regarder » reste à 7 — P7 et P8 SE TAISENT, comme voulu (63331 n'a aucune transaction). « Lu par l'IA :
  19 documents ». Console sans erreur.
- ⚠ **P7 et P8 ne sont PAS éprouvés en réel** : aucun bien d'essai n'a de compromis vivant (63331 aucune transaction ;
  61398 une offre proposée ; 62774 compromis annulé ; le seul compromis vivant à acquéreur « test », annonce 42965, est
  hors parc — vrai client probable, ÉCARTÉ). Les éprouver demanderait une offre puis un compromis d'essai sur 63331
  (écritures chez Hektor, à défaire ensuite) : décision à part.

**✅ « Financement » puis « Vas y » (16/11) : une offre de prêt avec IBAN reste rangée en « Financement » — rien poussé.**
`DepotDocuments.tsx` (l. 219-223) : le pré-choix « RIB » quand un IBAN est trouvé chez nous NE remplace plus un type
« Financement » proposé par le NOM du fichier (`financementParNom`). Un nom muet avec un IBAN garde « RIB », comme avant.
La lecture reste refusée (garde RIB inchangée, à l'écran et au serveur) ; le type reste modifiable à la main.
Essais `test_ged_regles_financement.cjs` **36 verts** (+4) ; témoin inverse (la condition retirée) -> ROUGE ; `test_ged_depot`
19 verts ; build vert.

**✅ « Ok on y vas » (16/11) : LOT 9d-2 (L'ÉTAT CIVIL, P9 et P10) ÉCRIT ET CONTRÔLÉ HORS LIGNE — rien poussé, rien posé.**
Recommandations du 16/11 appliquées (financement d'abord, fait ; la situation de famille d'un livret ne remplit PAS la
fiche contact). ⭐ **SIMPLIFICATION sur la protection** : au lieu de ranger son détail au registre à part, on n'en garde
QUE LA NATURE (ni personne, ni date, ni représentant) -- P10 peut déjà alerter avec ça. Donc PAS de patch SQL, rien de
sensible à ranger à part ; la décision du 12/11 (« sa nature, le représentant, la date ») est respectée en MOINS. Si
Frédéric veut le représentant et la date, ce sera un lot à part, avec le registre `ged_prive` et un patch.
- **Serveur** : fiche `justif.etat_civil` v1 dans `FICHES_PERSONNES` — `nature` (acte_mariage, livret_famille,
  contrat_mariage, pacs, divorce, acte_deces, protection, autre), `date_acte` (dès 1900), `personnes` (epoux, partenaire,
  defunt, autre ; nom, nom d'usage, prénoms). JAMAIS enfants, parents, témoins, officier, adresse, profession, cause de
  décès, motif, certificat médical, santé. `premiere_page_seule` ; `nature_seule: ["protection"]` : le serveur JETTE tout
  sauf la nature d'une mesure de protection, même lue avec doute, même si l'IA a rendu des noms.
- **Écran** : `FICHES_PERSONNES_LUES` + état civil ; `PREMIERE_PAGE_SEULE` + état civil ; résumé « acte de mariage · du … ·
  2 personnes » ou « mesure de protection (rien d'autre n'est lu) ».
- **Règles** `src/lib/gedReglesEtatCivil.ts` (pure), branchées dans `RecuManque`. Au dossier = la fiche + les mandants du
  mandat lu. **P9** : un mandant MARIÉ (acte, livret ou contrat) dont l'époux n'est ni sur la fiche ni signataire -> alerte
  « consentement du conjoint (art. 215) -- à vérifier » ; se tait sur un divorce lu, un décès du conjoint, un PACS (215 ne
  vaut que pour des époux), une fiche sans prénom ; une ligne par couple. **P10** : un mandant décédé -> alerte « un mandat
  prend fin au décès du mandant (art. 2003) » ; une mesure de protection au dossier -> alerte « vérifier qui signe (tuteur,
  curateur, juge) », sans nom.
- **Essais** : `test_ged_regles_etat_civil.cjs` **23 verts** ; `backend/tests/test_ged_lire_etat_civil.py` **16 verts**.
  **Témoins inverses** : la garde « nature seule » retirée -> ROUGE (le nom et la date d'une protection passaient) ; le
  silence sur divorce retiré -> ROUGE ; restaurés -> verts. Essais adaptés (leurs témoins « fermé » passent au RIB) : lire 81,
  lire personnes 36, lire financement 19, lecture 59, règles financement 36 ; voisins verts ; `npm run build` vert.
- **Reste, sur accord** : pousser (Render + Vercel), puis une épreuve sur 63331 avec un faux acte de mariage (le conjoint
  absent de la fiche -> P9 doit parler), un faux acte de décès au nom du mandant d'essai (P10) et un faux jugement de
  tutelle dont la page 1 porte un nom et une date (seule la nature doit rester).

**✅ 9d-2 EN LIGNE (`6da5485`, Render et Vercel) ET ÉPROUVÉ EN RÉEL (16/11, « Oui ») sur 63331, dans le Chrome de Frédéric.**
Pièces FICTIVES (`scratchpad/ged_m9d/fabriquer_etat_civil_specimen.cjs`, `fabriquer_deces_scan.py`, `fabriquer_mariage_b.cjs`) :
acte de mariage en texte (« ESSAI CONTACT Mandant » x « SPECIMEN Claire », enfants en page 2), acte de décès SCANNÉ du
mandant d'essai (héritiers en page 2), jugement de tutelle en texte (nom, date et tuteur en page 1 ; « certificat médical »
en page 2). 4 envois Hektor done (11:08-11:10 UTC). Coût des 4 lectures : 0,0007 $.
- **Type** : par le NOM, « Acte de mariage » et « Acte de décès » sont pris pour un TITRE de propriété (« probable » : la
  règle `acte` du titre passe avant celle de l'état civil, `gedTypeParNom.ts`) ; ⭐ l'IA a corrigé les deux en
  « État civil » avant l'envoi. ⚠ **TROUVÉ, NON TRAITÉ** : les ANCIENS documents (jamais classés par l'IA) nommés « acte de
  mariage / de décès / de naissance » comptent donc comme titre de propriété dans « Reçu / Manque ».
- **Lectures** : décès `pages_lues {1}` (acte_deces, 2026-11-01, défunt ESSAI CONTACT / Mandant) ; mariage par le texte
  seul ; **tutelle : la nature « protection » SEULE** (ni nom, ni date, ni tuteur). **0 fuite** (aucun enfant, héritier,
  marqueur, mot de santé), **0 valeur hors page 1**, **0 valeur de protection au-delà de la nature**.
- ⚠ **1er acte de mariage** : écrit « Epoux : ESSAI CONTACT Mandant » sans étiquettes, l'IA a mis le nom ENTIER dans `nom`
  sans prénom -> le mandant n'était que « proche » -> **P9 s'est tue** (prudente, voulu). **2e acte** (« Nom : … - Prénoms : … »,
  comme un vrai acte) : nom et prénom séparés -> **P9 PARLE**.
- **Écran** : « À regarder » 7 -> 10 : **P9** « Mandant ESSAI CONTACT est marié(e) depuis le 20/06/1987 avec Claire
  SPECIMEN, qui n'est ni sur la fiche ni signataire du mandat » ; **P10** « …est décédé(e) le 01/11/2026 : un mandat prend
  fin au décès du mandant » ; **P10** « Une mesure de protection juridique est au dossier ». « Prise de mandat : 3 pièces sur
  5 » (l'état civil compte). Console sans erreur.
- Cosmétique, à reprendre : le « pourquoi » de P9 finit par « -- à vérifier » alors que l'écran préfixe déjà « à vérifier : » ;
  celui de la protection commence par « vérifier qui signe » (« à vérifier : vérifier… »).
- **Reste sur 63331** : 4 pièces d'état civil SPÉCIMEN ; P9 et P10 y sonneront tant qu'elles y sont (bien d'essai, admin).

**✅ « Oui corrige » (16/11) : un acte d'état civil n'est plus pris pour un titre par son NOM — rien poussé.**
Dans la SOURCE (`phase2/checks/ged1_mesure_nomenclature.py`, comme le 13/11 pour « Note honoraires ») : une règle SÛRE
`acte (de |d )?(naissance|deces|mariage)|certificat (de )?deces` -> `justif.etat_civil`, placée APRÈS la règle sûre du
titre et AVANT sa règle probable `acte`. Puis `gedTypeParNom.ts` refabriqué (`scratchpad/ged_m1/gen_type_par_nom.py`) :
UNE ligne change. Mesure sur le stock : **106 noms** basculent du titre « probable » à l'état civil (« acte de deces 13 »,
« acte deces papa », « acte mariage », « extrait acte de naissance … ») ; le seul nom mixte, « titre de propriete et acte
de deces », RESTE titre. Effet : « Reçu / Manque » ne compte plus ces actes comme un titre trouvé ; le dépôt propose
« État civil ».
Au passage, texte seulement : le « pourquoi » de P9 et de la protection ne redit plus « vérifier » (l'écran met déjà
« à vérifier : »).
Essais `test_ged_regles_etat_civil.cjs` **28 verts** (+5, dont 3 témoins : nom mixte, acte de vente / notarié / notoriété,
livret) ; témoin inverse (l'ancien fichier) -> ROUGE ; les 11 essais GED de l'écran verts ; build vert.

### 12.20 Le morceau 10 — la mesure (audit du 16/11, lecture seule, rien codé)
**Ce qu'il doit faire** (§12.1, l. 34, l. 1016) : Frédéric juge chaque ligne « À regarder » de ses vrais biens -- **vrai /
faux / déjà su** -- pendant 2 semaines ; puis décision RÈGLE PAR RÈGLE (garder, resserrer, retirer) ; la « resserrée » est
un point d'arrêt possible.
**Ce qui existe (mesuré)** : RIEN pour juger une ligne. `app_ged_decision` ne garde que les propositions « remplir »
(contrainte `remplie / ignoree / echec`, porte `app_ged_decider` derrière `ged_remplir`) : **3 lignes** (l'épreuve 9c).
`app_ged_journal` : classements et rattachements (35). Une ligne « À regarder » (`Alerte` : code, niveau, texte,
pourquoi) n'a PAS d'identifiant : elle est recalculée à chaque ouverture, dans le navigateur.
⚠ **Aucune mesure automatique des règles lues n'est possible sur les vrais biens** : il n'y a de lectures QUE sur les biens
d'essai (tout le GED est en « admin » ; les dépôts des négociateurs passent par l'ancien formulaire). Les 13 règles SANS
IA, elles, ont été mesurées sur les 714 biens en cours le 12/11 (§12.10) : 209 biens ont une ligne au moins.
**Découpage proposé** :
- **10a, la base** (patch SQL, À POSER sur accord) : table `app_ged_jugement` (bien, code de la règle, CLÉ de la ligne =
  code + texte normalisé, texte, niveau, verdict `vrai / faux / deja_su`, commentaire facultatif, qui, quand ; journal :
  le plus récent fait foi) ; porte `app_ged_juger` (compte actif, interrupteur `ged_propositions` pour l'appelant,
  périmètre du bien) ; lecture par le même périmètre que les décisions.
- **10b, l'écran** : trois petits boutons sur chaque ligne « À regarder » (Vrai · Faux · Déjà su), le verdict affiché et
  modifiable ; même interrupteur `ged_propositions` (admin) : les négociateurs ne voient rien.
- **10c, le compte rendu** : une requête (lecture seule) qui donne, règle par règle, le nombre de lignes jugées et la part
  vrai / faux / déjà su ; avec les « remplir » (remplie / ignorée / échec) et les lectures (lu / incomplet / pas ce type,
  coût). À relancer au bout des 2 semaines.
**Ce que ça pourrait casser** : rien d'existant (une table et une fonction NEUVES, des boutons sous un interrupteur déjà
en « admin »). ⚠ La descente de nuit recopie d'elle-même toute table neuve de `public` sur le serveur local : les TEXTES
des lignes y partiraient (ils portent des noms, comme `app_ged_valeur`, déjà recopiée).

**✅ « Vas y » (16/11) : MORCEAU 10 ÉCRIT ET CONTRÔLÉ HORS LIGNE — rien poussé, PATCH NON POSÉ.**
- **10a, la base** : `supabase/patch_ged_m10_jugement_2026-11-16.sql` (+ `_INVERSE`, `_REPETITION` SANS commit, qui finit
  par rollback). Table `app_ged_jugement` (bien, règle, clé, texte et niveau TELS QU'AFFICHÉS, verdict `vrai / faux /
  deja_su`, commentaire ≤ 500, qui, quand ; journal, le plus récent fait foi), RLS au périmètre des décisions,
  `authenticated` en LECTURE seule ; porte `app_ged_juger` (SECURITY DEFINER ; compte actif ; interrupteur
  `ged_propositions` pour l'appelant ; périmètre ; auteur = `auth.uid()`). AUCUN interrupteur neuf ni touché. 6 contrôles
  après le commit.
- **10b, l'écran** : `src/lib/gedMesure.ts` (pure : `cleJugement` = règle + texte normalisé ; une ligne dont le texte change
  est une AUTRE ligne, à rejuger), `lib/ged.ts` (`loadGedJugements` : le plus récent par ligne, erreur -> null ;
  `gedJuger`), `RecuManque.tsx` : sous chaque ligne « À regarder », « Cette ligne est : Vrai · Faux · Déjà su », ou « Jugé
  faux le … · » et les trois boutons pour changer. ⭐ **Tant que le patch n'est pas posé, la lecture échoue -> AUCUN bouton**
  (on peut pousser l'écran AVANT de poser le patch, sans rien casser). La barre est SOUS la ligne (une ligne « Déposer » est
  déjà un bouton).
- **10c, le compte rendu** : `supabase/requete_mesure_ged_m10_2026-11-16.sql` (lecture seule) : ① règle par règle, lignes
  jugées, biens, vrai / faux / déjà su et leurs parts ; ② les « faux » mot pour mot ; ③ les « remplir » (remplie /
  ignorée / échec) ; ④ les lectures hors biens d'essai (lu / incomplet / pas ce type, coût). ③ et ④ tournent déjà
  (③ : les 3 « remplies » de l'épreuve 9c ; ④ : aucune lecture hors essais).
- **Essais** : `test_ged_mesure.cjs` **22 verts** (clé, fausse base, patch, branchement) ; témoin inverse (clé sans
  normalisation) -> ROUGE ; les 12 essais GED de l'écran verts ; build vert. ⚠ La RÉPÉTITION SQL n'est PAS jouée (elle
  touche la base de production, même en rollback) : à coller avant le patch.
- **Reste, sur accord** : pousser ; coller la RÉPÉTITION (« RÉPÉTITION VERTE ») ; poser le patch (6 contrôles) ; puis juger
  pendant deux semaines et relancer le compte rendu.

**✅ MORCEAU 10 EN LIGNE ET POSÉ (16/11, « Oui pousse » puis « Oui vas y »).** `d4ca8fe` poussé seul, Vercel prêt ; VU sur 63331
AVANT le patch : aucun bouton, 10 lignes intactes, console propre (l'ordre « écran d'abord » tient). **Répétition jouée**
(connecteur, transaction terminée par rollback) : 5 contrôles verts, `app_ged_jugement` ABSENTE après. **Patch posé**
(le fichier, de `begin` à `commit`, mot pour mot) : **6 contrôles VERTS** (table et RLS ; authenticated lecture seule ;
anon rien ; porte SECURITY DEFINER fermée à anon ; `ged_propositions` toujours « admin » ; table vide). **VU après** :
« Cette ligne est : Vrai · Faux · Déjà su » sous les 10 lignes de 63331, console propre. ⚠ Les trois boutons étaient
COLLÉS (« VraiFauxDéjà su ») : espacés (flex, écart 10 px), essai 22 verts, build vert -- commit local, À POUSSER.
Retour arrière : `supabase/patch_ged_m10_jugement_2026-11-16_INVERSE.sql`. Compte rendu :
`supabase/requete_mesure_ged_m10_2026-11-16.sql`. ⏰ **La mesure commence : deux semaines, jusqu'au 30/11/2026.**
⚠ Les lignes des biens d'ESSAI (63331, 62774, 61398) ne doivent pas être jugées, ou alors être écartées du compte rendu.

### 12.21 L'habillage : la maquette RETRAVAILLÉE d'abord (16/11, demande de Frédéric)
Au moment de coder l'habillage sur la maquette du 12/11 (v10, écrans E0-E6), Frédéric : « il faut retravailler cette
maquette, j'ai besoin d'une ergonomie adaptée et d'un design moderne graphique avec des animations dynamiques ». RIEN
n'avait été codé de l'habillage. Nouvelle maquette (toile Design, privée) : **https://claude.ai/artifact/S16jkpfnqtPF83xvUdkNtm**
-- 4 écrans interactifs : ① l'onglet Documents (élément fort : LE DOSSIER, les moments de la vente et une feuille par pièce
attendue, qui se remplit et se coche), ② la fenêtre de dépôt (zone, arrivée des fichiers pendant que l'IA lit le type,
liste + aperçu, « Prendre ce type », Séparer, « Envoyer quand même », RIB jamais envoyé, envoi fichier par fichier, bande
« Fermer sans envoyer »), ③ après l'envoi (lectures qui arrivent, « Remplir la fiche » : la valeur VOLE vers la case vide
de la fiche ; « Voir la preuve » ; alertes et Vrai · Faux · Déjà su), ④ le téléphone (photographier recto puis verso).
Raisonnement métier MESURÉ (par le numéro Hektor du document, pas `created_at`, faussé par les recréations d'octobre) :
1 042 documents en 31 jours sur 212 biens ; 301 dépôts, **2 fichiers en médiane**, 45 au plus ; 21 % de photos ; 8 % de
noms muets ; **40 % de noms qu'aucune règle ne reconnaît** -> le TYPE est le cœur du travail. Mêmes gestes qu'aujourd'hui,
aucune fonction ajoutée ; animations coupées par « moins de mouvement ». ⏳ Attend l'avis de Frédéric avant tout code.

**✅ « Oui, on code » (16/11) : HABILLAGE H1 (le bloc de l'onglet) ÉCRIT — rien poussé.** `RecuManque.tsx` : même logique,
mêmes données, mêmes gestes ; seul le RENDU change, d'après la maquette retravaillée. En tête « Le dossier » : les 4
moments (mandat, mise en vente, offre, compromis) en pastilles reliées -- passé complet coché, passé incomplet « N non
trouvées » (cliquable : ses pièces obligatoires non trouvées remplacent les feuilles ; c'était le repli « Moments
précédents »), courant « R pièces sur A », à venir grisé. Puis UNE FEUILLE par pièce : reçue = cochée (coche tracée, barre
verte qui se remplit, coin plié, la liste des documents au survol) ; non trouvée = hachurée, bouton « Non trouvée :
déposer » (⛔ jamais « absente » ni « manque », décision du 12/11 sur les noms muets) ; selon le cas = grisée. « À remplir »
et « À regarder » en CARTES côte à côte (étiquettes Remplir / Alerte / Pièce / Info ; « Déposer la pièce » devient un bouton
DE la carte, la barre Vrai · Faux · Déjà su sa voisine). « Lu par l'IA » en pastille. Les reçues ne se replient plus : elles
SONT les feuilles. `RecuManque.css` : styles `gm2-*` ajoutés (les anciens restent), animations coupées par « moins de
mouvement », 2 colonnes de feuilles sous 760 px. Essais GED tous verts (1 adapté : `test_ged_mesure` vérifie que la barre est
à côté du bouton « Déposer », jamais dedans) ; build vert. ⚠ PAS VU : le bloc dépend des interrupteurs en base ; la capture
contre capture se fera en production sur 63331 après le push. Reste : H2 la fenêtre de dépôt, H3 après l'envoi, H4 téléphone.

**✅ H1 EN LIGNE (16/11, « Oui, les trois » : `c77ca7e`, `a2812ba` de l'autre session, `b5f390c`) ET VU sur 63331** : bureau
838 px, 4 moments, 5 feuilles (3 reçues, 2 non trouvées), 10 cartes « À regarder » avec leurs jugements, aucun débordement,
console propre -- conforme à la maquette. ⚠ **TÉLÉPHONE (390 px, mesuré dans un cadre de la même page, retiré après)** :
le bloc DÉBORDAIT de 87 px (« Mise en vente et visites » sur une ligne, grille du bloc à la taille de son contenu, cartes en
colonnes de 300 px minimum). Corrigé : bloc en `minmax(0, 1fr)`, moments 2 par ligne avec retour à la ligne, colonnes des
cartes `min(300px, 100%)` -> débordement 0. Essais GED verts, build vert ; commit local À POUSSER. *(Poussé : en ligne à
`e8ae253`, vu au téléphone.)*

**✅ « Oui, H2 » (16/11) : HABILLAGE H2 (la fenêtre de dépôt) ÉCRIT — rien poussé.** Même logique, mêmes données, mêmes
gestes, même envoi (un fichier après l'autre, `createUploadDocumentToHektorJob` puis `app_ged_classer`, inchangés). Ce qui
change à l'écran, d'après la planche « Dépôt » de la maquette :
- **une FENÊTRE au-dessus du bien** en skin cockpit (`onFermer` présent ; portail sur `document.body`, voile, la page
  derrière ne défile plus, le clavier va dans la fenêtre). En skin classique, elle reste posée dans le panneau, comme avant.
  Interrupteur éteint : le formulaire d'aujourd'hui, inchangé (l'essai `test_ged_depot` le garde).
- **en-tête sombre** (bien, réf., « Déposer des documents », pastilles du moment et du mandat, croix) ;
- **vide** : une grande zone (icône qui flotte, « Choisir des fichiers », « Photographier une page ») et, sous elle, les
  pièces **non trouvées** du moment, LUES PAR « Le dossier » (`RecuManque` rend son résultat par `onResultat` : une seule
  lecture, aucune requête neuve). Glisser des fichiers marche sur TOUTE la fenêtre (« Lâche les fichiers ici ») ;
- **pleine** : le compte (prêts, à vérifier, à corriger, déjà dans ce dossier), la LISTE (vignette, nom éditable, fichier
  et taille, le type en pastille-menu, « L'IA lit le type… » qui scintille, d'où vient le type écrit lettre à lettre, le
  cadenas Privé / Public, une pastille d'état, la barre d'envoi) et l'**APERÇU** de la ligne choisie : la PAGE 1 dessinée
  DANS LE NAVIGATEUR (`apercuPremierePage`, pdf.js déjà chargé, rien ne part ni au serveur ni à l'IA), le type, d'où il
  vient, la visibilité, la page 1 / N, et les deux bandes : l'avis de l'IA avec « Prendre ce type », la raison d'un
  non-envoi (RIB). Choisie par défaut : la première ligne « à vérifier ». Au téléphone (aperçu sous la liste), l'avis et la
  raison restent AUSSI sur la ligne ;
- **fermer** : la croix, « Fermer » et Échap passent tous par une GARDE -- un fichier non parti, un envoi ou une lecture en
  cours fait monter une bande (« N documents ne sont pas partis. Les envoyer avant de fermer ? » · « Fermer sans envoyer »
  / « Envoyer maintenant »). ⭐ Avant H2, le bouton « Fermer » du panneau DÉMONTAIT la fenêtre sans rien demander : les
  fichiers non partis étaient perdus en silence (l'avertissement du navigateur ne joue qu'en quittant la page). Un clic à
  côté de la fenêtre ne la ferme pas (témoin).
Fichiers : `DepotDocuments.tsx` (rendu réécrit ; `etiquetteType` devient `sourceType`), `DepotDocuments.css` (styles
`dd-*` ajoutés, les anciens restent ; animations coupées par « moins de mouvement » ; plein écran sous 760 px),
`lib/gedClassementIa.ts` (`apercuPremierePage`), `RecuManque.tsx` (`onResultat`), `App.tsx` (`contexteDepot`, la fenêtre
montée sans le cadre `fa-ck-docup`). Essais : `test_ged_depot` 19 -> 28 (garde de fermeture et son TÉMOIN INVERSE --
retirer « fichier non parti » de la garde la fait rougir --, aperçu qui ne part nulle part, pièces non trouvées venues du
« Dossier », vocabulaire « non trouvée ») ; les 12 essais GED verts ; build vert. ⚠ PAS VU : la capture contre capture se
fera en production sur 63331 après le push (bureau et téléphone). Reste : H3 après l'envoi, H4 téléphone.

**✅ H2 EN LIGNE (16/11, « Oui, pousse » : `5a89b1b`, Vercel READY) ET VU sur 63331, SANS RIEN ENVOYER** : deux faux fichiers
glissés dans la page seulement (« RIB SPECIMEN essai.pdf », que son nom tient loin de l'IA, et un texte que l'IA ne lit
pas : aucun appel au serveur). Bureau : fenêtre au-dessus du bien conforme à la planche (en-tête, pastille « Prise de
mandat » -- pas de pastille de mandat, 63331 n'en a pas --, pièces non trouvées « Titre de propriété » et « Taxe
foncière », les mêmes que « Le dossier ») ; liste + aperçu (page 1 dessinée, « 1 / 2 », « Toujours privé », bande « Ce
type ne part jamais à l'IA ») ; la croix fait monter la bande « 2 documents ne sont pas partis » ; « Fermer sans envoyer »
ferme, rend le défilement de la page, console propre, **toujours 24 documents**. ⚠ **TÉLÉPHONE (cadre de 390 px, retiré
après)** : le téléphone prend la skin CLASSIQUE, la fenêtre y est posée dans le panneau, **278 px** de large. Aucun
débordement, MAIS la ligne était écrasée (95 px pour le nom : « RIB SF », le type réduit à « R.. »), une barre de
défilement DANS la fenêtre, et le bouton d'envoi tronqué (« r 2 doc »). Cause : mes règles « étroites » jugeaient la
largeur de l'ÉCRAN, pas celle de la fenêtre. Corrigé : les règles passent en `@container` (la fenêtre est son propre
conteneur, seuil 720 px) ; vignette masquée en étroit, état sur sa ligne, plus de défilement interne posé dans le panneau,
texte du pied sur sa ligne et boutons dessous. ⭐ Éprouvé AVANT le commit en injectant ces règles dans le cadre de la
production : 170 px pour le nom, « Envoyer 2 documents » en entier, 0 débordement. Essais verts, build vert ; commit local
À POUSSER.

**✅ Correctif téléphone EN LIGNE (16/11, `7c69804`, Vercel READY) ET REVU sans injection** : au téléphone, les mêmes
mesures que l'essai (règle `@container` servie par la production, 170 px, bouton entier, ni défilement interne ni
débordement) ; au bureau, la fenêtre garde ses deux colonnes (706 + 360 px), la vignette et les pastilles. Échap fait
monter la bande. ⚠ **Et la revue a trouvé une faute** : avec UN fichier, la bande disait « 1 document **ne est** pas
parti » (le gabarit ne savait pas élider). Corrigé : « 1 document n'est pas parti. L'envoyer avant de fermer ? », et de
même « Il est déposé ; fermer arrête sa lecture ». Essai `test_ged_depot` 28 -> 29 (le contrôle aurait rougi sur
l'ancienne phrase) ; build vert ; commit local À POUSSER. Toujours 24 documents sur 63331 : rien n'est parti.
*(Poussé le 16/11 avec `8af44f1` de la session classeur posé dessous, accord de Frédéric : `c0f09fa`, Vercel READY ; vu en
production avec un seul faux fichier : « 1 document n'est pas parti. L'envoyer avant de fermer ? ».)* ➡ **H2 EST FINI.**

**H3 (après l'envoi) : la planche mêlait trois choses, Frédéric a tranché (16/11) : « Fais A et B. C pas nécessaire. »**
A = l'habillage pur, B = le panneau « La fiche du bien », C = « Voir la preuve » (la phrase lue surlignée dans la page :
il aurait fallu que l'IA rende la citation, un changement du serveur de lecture, et relire le fichier au coffre) --
**C n'est PAS fait**. **✅ A ET B ÉCRITS — rien poussé** (`RecuManque.tsx`, `RecuManque.css`, une ligne de
`DepotDocuments.tsx/.css`) :
- **A** -- la carte « À remplir » dit ce que porte la case AVANT (« Fiche : vide », « Registre des mandats : vide »,
  « Compromis : aucune condition ») et d'où vient la valeur (« lu dans <document>, page N ») ; après le clic, la décision
  se REPLIE à sa place en une ligne (verte cochée « Envoyé… », grise « Ignorée… Elle ne reviendra pas. », ambre « Rien
  écrit… », rose pour une erreur) -- avant, un seul message en tête du bloc, effacé au clic suivant. Dans la fenêtre de
  dépôt, le résumé de lecture ENTRE à la place du scintillement « L'IA lit les valeurs… ».
- **B** -- « La fiche du bien », à côté de « À remplir » : les 6 cases que le geste « fiche » sait remplir (consommation,
  émissions, date du DPE, date de l'état des risques ; nombre de lots et charges du lot pour une copropriété), leur valeur
  ACTUELLE lue dans les faits de la fiche (rien de neuf n'est lu), « vide » sinon. Visible seulement s'il y a une case à
  remplir d'ici. Un « Remplir la fiche » qui a ÉCRIT fait voler la valeur du bouton jusqu'à sa case, qui s'allume (sans
  mouvement si « moins de mouvement » est demandé : la case s'allume seulement). « Rien écrit » n'allume rien.
Les gestes ne changent pas : `onRemplir` et `gedDecider` tels quels, toujours un clic par proposition. Essais :
`test_ged_remplir` 27 -> 32 (mêmes portes d'écriture, la case ne s'allume que si le geste a écrit -- TÉMOIN INVERSE :
allumer sans cette condition fait rougir --, le panneau ne lit rien de neuf, le vol coupé sous « moins de mouvement ») ;
les 12 essais GED verts, build vert. ⚠ PAS VU à l'écran : il faut une proposition « fiche » vivante sur 63331 pour voir la
carte, le panneau et le vol ; à regarder après le push.
⏳ **Question posée à Frédéric** : « peut-on juste montrer un aperçu du bon document ? » -- oui, la proposition garde le
numéro de sa lecture (donc le document) et la page. ⚠ Mais le seul chemin d'ouverture existant
(`createConsoleDocumentSignedUrl`) ÉCRIT au passage la date de consultation (`app_console_touch_document` :
`last_accessed_at` ET `updated_at` du document), et la règle demande de prévenir la session signature avant de toucher
`app_console_document` / le coffre. À trancher : passer par l'ouverture d'aujourd'hui (même effet qu'un clic sur
« Ouvrir »), ou lire le fichier sans cette écriture.
✅ **Tranché par Frédéric (16/11) : « Comme Ouvrir ». ÉCRIT — rien poussé.** Chaque carte « À remplir » dont la lecture
retrouve son document porte « Voir le document » : l'aperçu prend la place de « La fiche du bien » (croix pour revenir),
avec la PAGE OÙ LA VALEUR A ÉTÉ LUE (lue dans la source « …, page N »), dessinée dans le navigateur par pdf.js
(`apercuPremierePage` apprend un numéro de page ; hors du document -> la dernière). Le fichier vient de
`createConsoleDocumentSignedUrl`, l'ouverture d'aujourd'hui, avec son écriture de la date de consultation -- rien
d'autre n'est écrit, rien ne part à l'IA. Un fichier pas encore au coffre le dit (« Préparer » dans la liste). Un
« Remplir la fiche » qui écrit referme l'aperçu pour que la valeur vole dans le panneau. Essai `test_ged_remplir`
32 -> 35. ⚠ La session signature n'a PAS été prévenue : je n'ai pas son numéro dans les sessions liées ; le chemin est
celui d'« Ouvrir », inchangé, et ne touche ni `metadata_json.signature` ni `storage_path`.
**✅ H3 EN LIGNE (16/11, « Pousse vas y » : `722315c` + `cc1c19f`, Vercel READY) — ⚠ PAS ENCORE VU.** Sur 63331, le
bloc ne porte AUCUNE proposition « À remplir » (mesuré en lecture : ses 23 lectures sont des pièces des personnes, les 3
décisions sont les C1-C3 du contact d'essai, déjà remplies) : le panneau reste caché, comme voulu, donc rien de H3 ne
s'affiche. 62774 n'est plus dans `app_dossiers_current`, 61398 n'a aucune lecture. Pour voir la carte, le panneau,
l'aperçu et le vol, il faut une proposition vivante -- donc un DÉPÔT réel (une pièce SPECIMEN dont la case est vide),
qui écrit chez Hektor : à décider par Frédéric.
⚠ Mesuré avant tout geste : sur 63331, les 6 cases sont PLEINES (DPE 210 / 45 du 10/09/2026, état des risques du
10/09/2026, 24 lots, 120 €) -- un faux DPE n'y aurait fait naître AUCUNE proposition. Frédéric a choisi **63147 (ESSAI C9
bis)**, cases DPE vides. **✅ ESSAI RÉEL DU 16/11, VU** : « DPE SPECIMEN essai 2026.pdf » (PDF fabriqué dans la page,
marqué SPECIMEN : 212 kWh, 46 kg, établi le 14/03/2026) déposé par la fenêtre -- type « DPE », « le nom et l'IA sont
d'accord », aperçu de la page ; envoyé : « Déposé, part chez Hektor », puis « Lu : énergie D, climat E · 212 kWh/m²/an ·
établi le 14/03/2026… ». Fiche rechargée : **« À remplir (3) »** (consommation, émissions, date ; chacune « Fiche :
vide · lu dans DPE SPECIMEN essai 2026.pdf, page 1 ») et **« La fiche du bien »** (4 cases « vide », pas de lignes de
copropriété : le bien n'en est pas une) -- conforme à la planche. **« Voir le document »** : la page 1 servie par le
coffre et dessinée dans le panneau, croix pour revenir ; console propre. **Téléphone (cadre 390 px, retiré)** : 3 cartes,
puis le panneau, 0 débordement. ⛔ **« Remplir la fiche » NON cliqué** (hors de l'accord) : le vol et la ligne repliée
ne sont pas encore vus. Le faux DPE RESTE sur 63147 (et chez Hektor) avec ses 3 propositions ouvertes. ⚠ Remarque : au
téléphone, l'aperçu s'ouvre à la place du panneau, donc SOUS les cartes -- il n'est pas ramené à l'écran.
**✅ « Remplir la fiche » CLIQUÉ (16/11, « Oui ») sur la consommation de 63147** : la carte se replie en ligne verte
cochée (« Envoyé : DPE : consommation 212 kWh/m²/an. La fiche part chez Hektor par le chemin habituel… »), « À remplir
(2) », la case affiche 212 kWh/m²/an. Écriture vérifiée en base : décision `remplie` P1.dpe_cons = 212 (geste
`editAnnonceOptimistic`) ; la fiche chez nous porte 212 ; la demande attend dans `app_annonce_pending` (`dpe_cons: 212`,
départ 10 min après, le chemin de toute modification de fiche). ⚠ **Le vol n'a PAS été vu** : le Chrome de cette machine
demande « moins de mouvement » -- le vol est coupé EXPRÈS (c'est la règle). ⚠ **Et l'essai a trouvé un défaut** : sous ce
réglage, la case remplie redevenait GRISE (l'allumage n'était porté que par l'animation). Corrigé : la case remplie d'ici
garde un fond vert fixe (`RecuManque.css`) -- éprouvé en injectant la règle dans la production (fond 230, 243, 236), puis
retirée. Build vert, essais verts ; commit local À POUSSER.
⛔ **INCIDENT DE COMMIT (16/11), ma faute** : mon commit `ac886a6` (ce correctif + la note) a EMBARQUÉ 5 fichiers que la
session classeur avait déjà mis dans l'index (`PLAN_CHANTIER_CLASSEUR_2026-10-28.md`, `patch_c9_avis_etiquette_2026-11-16`
et `patch_verrou_tables_classeur_2026-11-16`, avec leurs inverses) -- j'avais relu l'index DANS LA MÊME COMMANDE que le
commit, sans m'arrêter. Avant que je puisse défaire mon commit, la session classeur a commité PAR-DESSUS (`a7b2dec`,
VIDE : ses fichiers étaient déjà dans le mien) et POUSSÉ. ➡ Tout est publié, contenu INTACT ; seule l'étiquette de
l'historique est fausse : le travail du classeur (verrou des 4 tables, étiquette des avis) est classé sous le message
de `ac886a6`, et `a7b2dec` porte son message sans ses fichiers. Rien n'a été défait (on ne réécrit pas un historique
publié). Le correctif « case verte » est donc EN LIGNE (Vercel READY sur `a7b2dec`) et vu : règle servie, 212 kWh/m²/an
désormais lu sur la fiche, 2 cartes restantes sur 63147. Leçon : l'index se relit SEUL, puis on commite dans un
second temps.
**Remarque du téléphone CORRIGÉE (16/11, « as-tu corrigé ») — rien poussé** : à l'ouverture, l'aperçu est amené à
l'écran (`scrollIntoView` « au plus près » : au bureau, où il est à côté de la carte, rien ne bouge ; sans glissé sous
« moins de mouvement »). Build et essais verts. À voir au téléphone après le push.
✅ **Poussé (`102c389`, Vercel READY) et VU sur 63147** : téléphone (cadre 390 px, retiré) -- panneau hors de l'écran
avant le clic (à 1 174 px pour un cadre de 776), l'aperçu ramené à l'écran après (338 -> 773 px), page dessinée ; bureau
-- le bloc ne bouge pas (128 px avant et après), l'aperçu s'affiche à côté. ➡ **H3 EST FINI.** Reste H4 (téléphone :
photographier recto puis verso).

**H4 (le téléphone) : la planche mêlait l'habillage du geste photo et un VISEUR DANS L'APP (caméra en direct, détection
de la page) -- une fonction neuve (accès caméra du navigateur, détection d'image, iPhone/Android). Frédéric (16/11) :
« Oui A » -- l'habillage seul, PAS de viseur.** ✅ **ÉCRIT — rien poussé** (`DepotDocuments.tsx/.css`) : au téléphone
(sous 760 px), dès la première photo, les pages montent dans un PANNEAU DU BAS (poignée, en-tête sombre « Photographier
une page »), avec les VRAIES vignettes numérotées qui tombent à leur place, l'éclair blanc au retour de l'appareil,
« N pages : un seul document », et les MÊMES gestes : « Ajouter une page (le verso) » (l'appareil photo du téléphone,
comme aujourd'hui), « Faire un PDF de N pages », « Annuler les photos ». Au-delà de 760 px, rien ne change (la bande de la
fenêtre). Les vignettes sont des adresses locales, rendues après usage. Essai `test_ged_depot` 29 -> 32 (mêmes gestes ;
TÉMOIN : ni viseur ni envoi) ; les 12 essais GED verts, build vert. ⚠ PAS VU : à éprouver après le push dans le cadre de
390 px, avec une photo glissée dans la page seulement (rien n'est envoyé sans « Faire un PDF » puis « Envoyer »).
✅ **EN LIGNE (`dbe9f61`, poussé le 17/11 par une autre session avec `b4feb29` de l'assistant posé dessous -- accord de
Frédéric ; Vercel READY sur `acd5949`) ET VU sur 63147, SANS RIEN ENVOYER** : téléphone (cadre 390 px, retiré) -- deux
fausses photos SPECIMEN (« RECTO », « VERSO ») glissées dans l'appareil photo : le panneau monte dès la 1re (1 vignette),
la 2e arrive par « Ajouter une page (le verso) » (2 vignettes, images chargées), « 2 pages : un seul document », les
3 gestes tiennent dans l'écran (598 à 750 px sur 776), la bande de la fenêtre est masquée, 0 débordement ; « Annuler
les photos » referme, aucune ligne créée. Bureau (1 280 px) : le panneau reste caché, la bande de la fenêtre s'affiche,
comme avant. Toujours 1 document sur 63147. ➡ **H4 EST FINI : L'HABILLAGE H1-H4 EST COMPLET.** ⚠ Remarque, d'avant H4 :
la bande de la fenêtre dit « 1 page photographiée : ELLES formeront un seul document » (pluriel au singulier).
✅ Corrigé (17/11, « Corrige ») : « 1 page photographiée : elle formera un document ; ajoute le verso si besoin. » ;
le pluriel inchangé. Essai `test_ged_depot` 32 -> 33, build vert.

### 12.22 Le lot 10a -- le compromis lu nourrit SA transaction (17/11)
Frédéric (17/11), après l'explication de P7/P8 : « non, trop compliqué pour le moment ; il faudrait juste qu'à la lecture
du compromis, donc à son ajout, les dates soient récupérées -- pour comparer ou remplir les champs dans la transaction
correspondante, et même les conditions suspensives ». Puis, sur où écrire : **« chez nous seulement »**.
**L'audit** : la lecture du compromis rapporte déjà `date_signature`, `date_limite_pret`, `date_reiteration` (+ prix, net
vendeur, honoraires, séquestre, notaires) ; seule la condition de PRÊT est lue (pas les autres conditions). Existait :
L7 (comparer prix, net vendeur, honoraires, date de signature) et P4 (remplir « Obtention Crédit », liste vide).
⚠ La porte « chez nous » (`editAffaireOptimistic`) écrit le CARNET de l'app (`app_affaire_champ_app`) et la colonne du
registre ; la nuit remet la colonne à la valeur de Hektor (`CHAMPS_APP_AFFAIRE` est VIDE) -- le carnet fait donc foi, et
l'écran le superpose maintenant au registre. ⚠ La lecture d'aujourd'hui du carnet rend VIDE sur erreur : une lecture
STRICTE a été ajoutée (`lireCarnetAffairesStrict`), sinon une case remplie chez nous aurait paru vide.
**✅ ÉCRIT (17/11) — rien poussé** :
- **Remplir, chez nous** (propositions `P4.date_acte`, `P4.sequestre`, geste « transaction », bouton « Remplir la
  transaction ») : la date d'acte prévue = la réitération lue, le séquestre lu -- seulement sur LA transaction du
  compromis (résolveur), vivante, case VIDE carnet compris, carnet lu sans erreur. Le geste RELIT la ligne et le carnet
  (strictement) juste avant, refuse si la case est remplie ou la transaction close, écrit par `editAffaireOptimistic`,
  garde la décision ; message « Enregistré : … (chez nous ; Hektor n'est pas prévenu) ».
- **Comparer** (L7) : date d'acte prévue ≠ réitération lue, séquestre ≠ lu -- seulement quand les deux existent (une
  case vide se propose, elle ne sonne pas).
- ⛔ **La date de SIGNATURE ne se remplit pas** : un compromis sans date au registre est souvent non signé (audit des 267
  transactions sans date) ; elle reste comparée.
Essais : `test_ged_remplir` 35 -> 43 (avec TÉMOIN INVERSE : sans la condition « carnet lu », l'essai rougit),
`test_ged_regles_lues` 84 -> 88 ; les 12 essais GED verts, build vert.
⏳ **Pas fait dans ce lot** : les AUTRES conditions suspensives (vente d'un bien, permis, préemption…) -- il faut
apprendre à la fiche de lecture du serveur à les rapporter (nature + date limite), puis comparer à la liste de la
transaction / proposer de l'écrire si elle est vide. Ça change le serveur de lecture (Render) et ne vaudra que pour les
compromis lus APRÈS. Lot suivant, sur accord.
✅ **10a EN LIGNE (`270cbd7`, poussé le 17/11 par une autre session avec `e97a208` et `9d59fbc` dessous -- accord de
Frédéric ; Vercel READY).** Contrôle de non-régression en production : 63147 -- « À remplir (2) », « La fiche du bien »,
5 feuilles, console propre ; 63331 -- les MÊMES 10 lignes « À regarder » qu'avant, console propre (la lecture du carnet
ne fait rien taire). ⚠ Pas vu en réel : aucun bien d'essai n'a de compromis AU REGISTRE (63331 a un compromis déposé,
« aucun au registre ») -- le lot ne peut rien y proposer, c'est voulu.

### 12.23 Le lot 10b -- les conditions suspensives du compromis (17/11, « Oui, les conditions »)
**L'audit** : les conditions d'une transaction sont une donnée de l'APP seule (`app_affaire_condition`, jamais chez
Hektor -- décision du 16/09) ; le catalogue de l'agence n'a que 2 entrées (« Préemption mairie », « Obtention Crédit ») ;
5 conditions posées en tout dans la base. L'écriture (`ecrireAffaireConditions`) remplace TOUTE la liste ; la lecture
d'aujourd'hui (`loadAffairesConditions`) rend une carte VIDE sur erreur.
⛔ **Confidentialité** : la condition de prêt d'un compromis porte souvent le MONTANT du prêt, son TAUX, sa BANQUE --
interdits (`_PRET`). On ne lit donc QUE la NATURE de chaque condition (liste fermée : pret, preemption, vente_bien,
permis_construire, urbanisme, servitudes, hypotheque, autre) et sa DATE LIMITE, jamais son texte.
**✅ ÉCRIT (17/11) — rien poussé** :
- **Serveur** (`openai_ged_lecture_service.py`) : la fiche du compromis passe en **v2** avec une liste « conditions »
  (nature, date limite). `test_ged_lire` 81 -> 83 (TÉMOIN : aucun champ texte, montant, taux, banque).
- **Lire** (`gedComparer.conditionsLuesDe`) : une nature une fois ; « pas de prêt » / « renonciation » écarte la
  condition de prêt ; une lecture v1 (avant) retombe sur la seule condition de prêt, comme avant.
- **Remplir** : si la liste de la transaction est VIDE (comptée strictement), UNE proposition écrit toutes les conditions
  lues (`P4.conditions`, libellé du catalogue quand il y figure) ; le prêt SEUL garde la forme d'avant
  (`P4.condition_credit`), les décisions déjà prises restent valables. Le geste décode la liste APRÈS le compte strict.
- **Comparer** (**L20**) : liste de la transaction lue strictement (`lireConditionsAffairesStrict`) et NON vide --
  condition du compromis non trouvée dans la transaction ; date limite différente ; « renonciation » / « pas de prêt »
  alors que la transaction suit le crédit.
- **Résumé** du dépôt : « … · conditions : Obtention Crédit, Préemption mairie ».
Essais : `test_ged_remplir` 43 -> 49 (TÉMOIN INVERSE : sans la garde « liste vide », deux contrôles rougissent),
`test_ged_regles_lues` 88 -> 93, `test_ged_lecture` 59 -> 60 ; les 12 essais GED et les 5 du serveur verts, build vert.
⚠ Ne vaut que pour les compromis lus APRÈS le déploiement du serveur (Render). ⚠ Pas vu en réel : aucun bien d'essai n'a
de compromis au registre.
✅ **10b EN LIGNE (17/11, « Oui, pousse » : `cf09297` avec `3ed2e10` et `f68dd6f` de l'assistant dessous ; Vercel READY,
Render sert `cf09297`).** Non-régression en production : 63147 -- « À remplir (2) » et « La fiche du bien », comme avant ;
63331 -- les mêmes 10 lignes « À regarder », « Lu par l'IA : 23 documents » ; console propre. ⚠ Pas vu en réel : il
faudrait un compromis lu APRÈS ce déploiement, sur un bien qui a SA transaction au registre.

### 12.24 AUDIT -- la taille des documents que l'IA lit à l'étape 2 (17/11, demande de Frédéric, lecture seule)
Question de Frédéric : « regarde dans mes documents la taille moyenne des documents que l'IA va devoir lire à l'étape 2,
surtout le compromis, pour adapter le nombre de pages : les compromis sont beaucoup plus gros que 12 pages, mais ils
comprennent beaucoup de pages de diagnostics ou autres ». Mesure sur le disque du serveur
(`C:\Hektor\HektorConsoleDocuments\annonces`), scripts du bloc-notes de la session (`audit_compromis_taille.py`,
`_zones.py`, `_fin.py`, `_pages.py`, `forme_documents.py`), qui n'impriment QUE des nombres.
**Ce que l'étape 2 envoie aujourd'hui pour un compromis** : PDF texte -> les 80 000 premiers caractères + les 2 dernières
pages en image ; PDF scanné -> les 4 premières pages + les 2 dernières en image (6 au plus, plafond du serveur).
**Les compromis (100 les plus récents)** : **38 pages** en médiane (p10 22, p90 53, max 172) ; **62 à couche texte, 38
SCANS** (28 pages en médiane). Un compromis texte = trois blocs : le **CORPS** (15 pages en médiane, p90 22 ; 45 000
caractères, p90 67 000 ; 60/62 sous 80 000), puis les **ANNEXES** (diagnostics surtout -- 446 pages sur 608 repérées --,
puis titre, urbanisme, copro ; de 37 % à 78 % du fichier, ~58 000 caractères), puis une **FIN** d'environ 9 pages
(25 000 caractères) qui se termine par les signatures (les 2 dernières pages : 97/124 courtes, 85/124 avec des mots de
signature). Texte total : 124 000 caractères en médiane.
**Où sont les données (page de la 1re mention, compromis texte)** : réitération p. 6 (p90 8) ; conditions suspensives
p. 4 (p90 9) ; honoraires p. 7 (p90 18) ; prix p. 8 (p90 10) ; préemption p. 8 (p90 10) ; séquestre p. 10 (p90 13) ;
prêt p. 13 (p90 19) ; date limite du prêt p. 13 (p90 17) ; clauses d'urbanisme p. 15 (p90 23). En caractères : tout
sous 80 000 sauf 3 honoraires sur 62 (max 111 000) et 1 prêt sur 51 (84 000).
**Verdicts** :
- **Compromis TEXTE : le réglage tient.** 80 000 caractères couvrent le corps (60/62) et les données : prix 62/62,
  réitération 62/62, séquestre 58/58, préemption 61/61, prêt 50/51, date limite 30/30, honoraires 59/62. Il lit au
  passage ~35 000 caractères de diagnostics, inutiles mais sans danger (0,0026 $ le compromis). ⛔ **Sauter les annexes
  n'est PAS sûr** : repérées par leurs mots, elles avalent de vraies clauses (le prêt tombe dans la « zone d'annexes » de
  9 compromis sur 61, l'urbanisme de 36) -- un corps qui CITE le DPE ressemble à une annexe.
- ⚠⚠ **Compromis SCANNÉ (38 sur 100) : le réglage PERD l'essentiel.** Dans les 6 premières pages : prix 21/62, séquestre
  7/58, préemption 11/61, prêt 3/51, **date limite du prêt 0/30**. Dans les 16 premières : prix 61/62, séquestre 56/58,
  préemption 60/61, conditions 58/62, prêt 44/51, date limite 27/30 (mesuré sur les compromis texte, pris pour modèle des
  scans -- la mise en page d'un scan n'est pas mesurable sans reconnaissance de caractères). Coût mesuré : ~2 500 jetons
  par page en image (titre ou mandat à 3 images : ~7 900) -> **16 premières + 2 dernières = 18 images ≈ 45 000 jetons ≈
  0,005 $** le compromis scanné.
- **Les autres types (60 plus récents)** : mandat 12 pages, 55/60 texte (40 000 caractères + 2 dernières en image :
  tient) ; titre 9 pages (p90 42), 51/60 scans, 6 pages en image (parties et désignation au début : tient) ; PV d'AG 12
  pages (p90 34), moitié scans, 6 pages (⚠ travaux votés parfois plus loin : non mesuré) ; règlement / EDD 34 pages
  (p90 65), 26/30 scans, 6 pages (⚠ lots et tantièmes souvent plus loin : non mesuré) ; taxe, charges, fiche synthétique
  2 pages, offre 1 page (tiennent).
- **L'étape 1 (le classement)** est un autre sujet : au-delà de 12 pages elle ne voit que 1-8 et les 4 dernières, d'où le
  lien « Chercher les pièces » proposé (non codé).
**Proposition** : compromis SCANNÉ -> les 16 premières pages + les 2 dernières en image (le serveur doit admettre 18 pages
pour ce type) ; compromis texte inchangé (ou 100 000 caractères pour 3 honoraires et 1 prêt de plus, +25 % de coût).
Rien n'est codé.
✅ **« Oui, fais-le » (17/11) : COMPROMIS SCANNÉ -> 16 PREMIÈRES PAGES + 2 DERNIÈRES, ÉCRIT — rien poussé.** Écran
(`gedClassementIa.ts`, `PAGES_HD_PAR_TYPE`) : `transaction.avant_contrat` 6 -> 18 ; `pagesAImager` (inchangée) donne, pour
un scan de 28 pages, 1-16 + 27-28 ; un compromis à couche texte reste « 80 000 caractères + 2 dernières pages ». Serveur :
`MAX_PAGES_COMPROMIS_SCAN = 18`, `PAGES_HD` du compromis = 18, et le plafond devient PAR TYPE
(`max(6, PAGES_HD[type])`) -- tous les autres types gardent 6 ; la route admet 18 images au plus (le service redit le
plafond du type). Essais : `test_ged_lire` 83 -> 87 (18 images partent ; 19 -> 413 ; un titre à 7 -> 413) ;
`test_ged_lecture` 60 -> 62, et le contrôle « même table à l'écran et au serveur » sait lire une valeur nommée du serveur
(TÉMOIN INVERSE : écran à 16, serveur à 18 -> deux rouges). Les 12 essais GED et les 5 du serveur verts, build vert.
⚠ Coût attendu ≈ 0,005 $ par compromis scanné (18 images ≈ 45 000 jetons), requête ≈ 7 Mo (18 images de 1 600 px).
⚠ Pas vu en réel : il faudra un compromis SCANNÉ fictif de ~28 pages (prix p. 8, prêt p. 13) déposé sur un bien d'essai.

### 12.25 « Chercher les pièces » -- le découpage d'un PDF, à la demande (17/11)
Question de Frédéric : « nous avions prévu une fonctionnalité qui permettait de découper des documents, par exemple un PDF
de 25 pages avec carte d'identité, taxe foncière… ». Elle existait (morceau 4, « Séparer en N fichiers »), éprouvée sur
un scan de 4 pages ; mais le classement ne voit, au-delà de 12 pages, que les pages 1-8 et les 4 dernières -> une pièce
au milieu d'un gros PDF passait inaperçue. Décisions de Frédéric : **à la demande, pas systématique** (« il faut que ce soit
une fonction pas systématique »), et **le lien sur CHAQUE PDF**, pas seulement au-delà de 12 pages.
**✅ ÉCRIT (17/11) — rien poussé** :
- **Écran** : sur la ligne de chaque PDF (pas un PDF d'une page ; pas quand « Séparer » est déjà proposé ; derrière
  `ged_lecture_ia`), le lien « Chercher les pièces dans les N pages ». Au clic (`preparerDecoupage`) : la garde RIB lit
  tout le texte d'abord ; puis TOUTES les pages en vignettes basse définition (40 au plus) et les 300 premiers caractères
  de chaque page. Le résultat rejoint l'avis de l'IA de la ligne -- seules les pièces changent : plusieurs pièces -> le
  « Séparer en N fichiers » d'aujourd'hui ; une seule -> « Une seule pièce trouvée dans les N pages ». Rien n'est envoyé
  chez Hektor, rien n'est enregistré, aucune valeur n'est lue.
- **Serveur** (`openai_ged_classement_service.py`, `routers/ged.py`) : le classement accepte `decoupage: true` -> 40 pages
  au plus (12 sinon, inchangé), 16 000 caractères de texte, une consigne en plus (« toutes les pages, sans trou ni
  chevauchement ; les annexes agrafées sont des pièces à part ») ; le journal des agents note `decoupage`.
Essais : `test_ged_classer` 28 -> 34 (25 pages passent en découpage ; SANS lui, refusées comme avant ; 41 refusées ;
le classement ordinaire inchangé ; un IBAN refusé avant tout envoi) ; `test_ged_classement_ia` 25 -> 31 (TÉMOIN INVERSE :
sans la règle « pas sur un PDF d'une page », il rougit). Les 12 essais GED et le serveur verts, build vert.
⚠ Coût : 40 vignettes basse définition ≈ de l'ordre du dixième de centime par clic. ⚠ Pas vu en réel : un faux dossier
SPECIMEN de ~25 pages (pièce d'identité, taxe, compromis) à déposer sur 63147.
⛔ **REMPLACÉ LE 17/11, AVANT TOUT PUSH** -- Frédéric : « je ne trouve pas cela très logique ni ergonomique ; l'étape 1 ne
devrait-elle pas être améliorée ? le découpage de base est-il efficace, et pas un coût pas toujours utile ? audit et
propose ». **L'audit** (36 classements réels) : la liste des 66 types fait l'essentiel du coût (~2 100 jetons à CHAQUE
appel) ; une page en vignette ne coûte que ~220 jetons (~0,00002 $) -> voir 40 pages au lieu de 12 = ~0,001 $ de plus
par gros PDF. Les dépôts en lot sont rares (~0,6 % des noms ; 26 mêlent identité et taxe/titre). ⚠⚠ Et l'audit a trouvé
un DÉFAUT dans le lien : sa consigne disait « les annexes agrafées à un compromis sont des pièces à part » -- un
compromis signé et ses annexes forment UN acte ; « Séparer » remplace l'original : on aurait cassé l'acte signé.
**✅ Proposition A, « Oui, fais A » (17/11) — ÉCRIT, rien poussé (le commit du lien, `1098595`, ne part pas seul : il
est défait par le commit suivant, posé dessus)** :
- **L'étape 1 voit TOUTES les pages** (40 au plus ; au-delà : les 36 premières et les 4 dernières), en vignettes basse
  définition, avec le début de CHAQUE page repéré (« --- page N --- » : 2 000 caractères pour les pages 1 à 3, où le
  type se lit ; 300 pour les suivantes ; 16 000 au plus). Le « Séparer en N fichiers » d'aujourd'hui apparaît TOUT SEUL.
  Les documents de 1 à 3 pages ne changent pas (sinon le repère de page).
- **La consigne** : un lot de pièces SANS RAPPORT se sépare (pièce d'identité + taxe + titre…), toutes les pages, sans
  trou ni chevauchement ; ⛔ **JAMAIS un acte et SES annexes** (compromis, promesse, mandat, avenant, acte de vente avec
  les diagnostics, plans, titre ou règlement annexés) ni un DDT ; dans le doute, rien.
- **Le lien « Chercher les pièces » et le mode à part sont RETIRÉS** (écran et serveur : `MAX_PAGES` du classement passe à
  40, `MAX_TEXTE_CARACTERES` à 16 000).
Essais : `test_ged_classer` 33 (25 pages sans clic ; la consigne « jamais un acte et ses annexes » ; 41 refusées ; un
IBAN en page 9 refusé avant tout envoi) ; `test_ged_classement_ia` 30 (TÉMOIN INVERSE : revenir à 12 pages fait rougir 4
contrôles ; plus aucune trace du lien). Les 12 essais GED et le serveur verts, build vert.
⚠ Latence : préparer 40 vignettes prend quelques secondes de plus dans le navigateur ; l'envoi reste possible sans
attendre l'IA. ⚠ Pas vu en réel : un faux lot SPECIMEN (identité + taxe + titre) et un faux compromis avec annexes, à
déposer sur 63147 -- le lot doit se proposer à séparer, le compromis jamais.
✅ **Proposition A EN LIGNE (17/11, poussée par Frédéric ; Render et Vercel sur `f3fa65f`, qui la contient).** Pas vue en
réel (faux lot SPECIMEN et faux compromis avec annexes à déposer sur 63147).
⚠ **Trouvé en vérifiant le push** : la session classeur a passé le catalogue des conditions suspensives de 2 à **6**
clauses (Préemption mairie, Obtention Crédit, Permis de construire, Délai de rétractation SRU, Dépôt du permis de
construire, Obtention du permis de construire). Le lot 10b écrivait « Obtention d'un permis de construire » -> aucun
lien au catalogue. ✅ **« Oui, aligne » (17/11)** : libellé aligné sur « Obtention du permis de construire » ; essai
`test_ged_remplir` 49 -> 51 (les libellés écrits figurent MOT POUR MOT au catalogue ; dépôt et obtention du permis se
reconnaissent comme permis ; le délai SRU n'est pas une condition lue). Build vert ; commit local À POUSSER.

### 12.26 « Prendre ce nom » -- le nom proposé par l'IA, montré (17/11)
Question de Frédéric : « avait-on prévu que l'IA propose le libellé du document quand il n'est pas conforme ? ». **En
partie** : l'IA propose un nom court à chaque classement (jamais un nom de personne, d'adresse ni de numéro), mais il ne
s'appliquait QUE sur un nom de fichier muet ou non reconnu (et sans IA : « <type> <date> ») ; sur un nom reconnu mais pas
propre (« tf 2.pdf », « DIAGS.pdf »), il était JETÉ, jamais montré. Aucune règle de nommage n'a été fixée (les types
l'ont été, pas les noms). Le nom est DÉFINITIF une fois envoyé (⑦-9 fermé le 19/10) : c'est avant l'envoi qu'il se
corrige. **✅ « Oui, ajoute-le » (17/11) — ÉCRIT, rien poussé** (`DepotDocuments.tsx`) : quand le nom de l'IA diffère de
celui de la ligne (casse, accents, espaces près), la ligne dit « L'IA propose le nom « Taxe foncière 2025 ». » avec
**« Prendre ce nom »** ; un clic le prend et le nom compte alors comme choisi. Il ne s'applique toujours TOUT SEUL que
sur un nom muet. Essai `test_ged_classement_ia` 30 -> 33. Build vert. ⏳ Option non tranchée : une règle de nommage
commune (« Type année, précision ») que l'IA suivrait.

### 12.27 La garde RIB bloquait un compromis qui CITE « relevé d'identité bancaire » (17/11, essai de Frédéric)
**Le constat** (Frédéric : « j'ai fait un test d'ajout d'une promesse de vente ; l'étape 1 la classe en RIB et ne veut
pas la faire lire par l'IA, alors que c'est un compromis ») : vérifié EN LOCAL sur son fichier, en n'imprimant que des
verdicts. 38 pages à couche texte ; le nom dit « compromis » avec certitude ; **aucun IBAN** ; mais la PAGE 13 contient la
phrase « relevé d'identité bancaire » (une clause, ou la liste des pièces). La garde RIB -- écran ET serveur -- comptait
cette PHRASE, n'importe où dans le texte, comme un RIB -> rien ne partait à l'IA (classement ni lecture), ET le type
« compromis » était remplacé par « RIB » (seule exception jusqu'ici : le financement).
**✅ « Oui, corrige » (17/11) — ÉCRIT, rien poussé** :
- **La phrase ne compte que sur un document COURT** (3 pages au plus ; un vrai RIB en fait une), à l'écran
  (`texteDitRib(texte, nbPages)`) et au serveur (`texte_porte_un_rib(texte, nb_pages)`, classement et lecture). **Un vrai
  numéro IBAN bloque TOUJOURS**, quelle que soit la longueur : la règle « un RIB n'est jamais envoyé à l'IA » est tenue
  par le numéro. Nombre de pages inconnu : comme avant. (Le nombre de pages vient du navigateur ; un client trafiqué qui
  l'enflerait resterait arrêté par le numéro IBAN.)
- **Un type reconnu avec certitude par le nom n'est jamais remplacé par « RIB »** (généralise l'exception du
  financement) ; un document qui porte un vrai IBAN ne part pas plus à l'IA, il garde seulement son vrai type.
- Rejoué EN LOCAL sur le fichier de Frédéric : `texteDitRib(texte, 38)` = faux (avant : vrai) ; texte extrait effacé.
Essais : `test_ged_classement_ia` 33 -> 37, `test_ged_classer` 33 -> 36 (MÊMES exemples des deux côtés ; TÉMOIN : un vrai
IBAN dans 38 pages bloque toujours) ; `test_ged_regles_financement` : 2 motifs adaptés à la nouvelle signature (ce qu'ils
gardent ne change pas). Les 12 essais GED et le serveur verts, build vert.
⏳ **Cas voisin, NON traité (décision à part)** : un compromis qui porte un VRAI IBAN (compte séquestre du notaire) reste
entièrement bloqué pour l'IA ; on pourrait masquer le numéro dans le texte au lieu de tout refuser.

### 12.28 Le lot 10c -- « Ce que dit le compromis » : la fenêtre de validation (17/11, essai réel de Frédéric sur 18849)
**Le constat** (Frédéric, sur la vraie promesse déposée sur 18849 = annonce 62850 : « l'IA a lu, j'ai cliqué et rien ;
normalement une modale montre les données à ajouter avec oui / non, les conflits ») : l'écran faisait ce qui était construit
(une carte « Remplir la transaction » pour le séquestre, deux lignes « À regarder »), mais **aucune fenêtre de validation
n'avait été construite**. Mesuré en base : ses deux « Vrai » (L7, L20) sont gardés (15:47) -- ils notent la RÈGLE, ils ne
corrigent rien ; et son clic de 15:46 sur « Remplir la transaction » a écrit **le séquestre 12 400 € au carnet SEULEMENT**
(`app_affaire_champ_app`, transaction 30770) : **Hektor ne l'a pas.**
**⛔ Sa correction (« Attention, chez nous seulement NON, cela dépend des champs ») -- vérifiée dans le code** : la
correction « sans envoyer à Hektor » des valeurs d'une transaction a été RETIRÉE le 15/09 par sa décision (App.tsx,
« CORRIGER SANS ENVOYER A HEKTOR A ETE RETIRE ») ; prix, dates, séquestre, net vendeur et honoraires partent par la modale
« Modifier le compromis » (travail `change_hektor_annonce_status`, `reprendreTransaction`). Seules les conditions
suspensives sont gardées chez nous (décision du 16/09). Le lot 10a était donc FAUX sur ce point.
**Deux corrections de Frédéric après la première version (17/11, avant toute mise en ligne)** :
- ⛔ **La date d'acte** : « la date butoir sur le compromis et la date prévue de l'acte sur la transaction sont les mêmes
  dates ; elles doivent être identiques ; différentes, c'est un conflit ». J'avais d'abord fait de la réitération une
  LIMITE (une date prévue avant elle passait pour cohérente) : **c'était faux, c'est retiré**. L7 et la fenêtre disent
  un conflit dès que les deux dates diffèrent (de plus d'un jour), dans un sens comme dans l'autre. Sur 18849 :
  01/02/2027 au compromis, 23/01/2027 au registre -> **à trancher**.
- ⛔ **Les conditions générales** : « la préemption de la mairie et l'état hypothécaire ne sont pas des conditions
  suspensives particulières mais des conditions en général ; pas nécessaire de les récupérer ; l'indiquer pour éviter
  que cela fasse sonner ». **Et** : « je veux bien sûr qu'il continue à récupérer les conditions suspensives, obtention
  de prêt, etc. ». Donc : `CONDITIONS_GENERALES` (gedComparer.ts) = préemption, état hypothécaire -- **écartées** de
  `conditionsLuesDe` (résumé, L20, fenêtre : elles ne sonnent plus) et **dites à part** dans la fenêtre (« Conditions
  générales du compromis : … ni reprises ni comparées ») ; la consigne de lecture du serveur dit à l'IA de ne pas les
  lister (fiche inchangée, v2). Le prêt, le permis, la vente d'un bien, l'urbanisme, les servitudes **restent repris**
  (témoin : un prêt non suivi se propose, avec sa date et sa clause du catalogue).
  ✅ **Et l'absence de servitude** (sa réponse, 17/11) : « une condition générale, pas besoin de la mettre en condition
  particulière » -> ajoutée aux conditions générales (écran et consigne). Restent reprises : prêt, permis, vente d'un
  bien, urbanisme, autre.
- Au passage : la clause du catalogue se choisit au **libellé exact** d'abord (« Obtention du permis de construire »), à
  la nature ensuite (sinon « Permis de construire », plus haut dans le catalogue, l'emportait).
- « État hypothécaire » et « Absence de servitude » ne sont pas au catalogue, mais la modale accepte une **condition
  libre** (je lui avais dit à tort qu'elles ne pouvaient pas être ajoutées).
**✅ « Oui vas-y, mais soigne la mise en page, le graphisme et l'ergonomie » -- ÉCRIT, rien poussé** :
- `lib/gedBilanCompromis.ts` (pur) : le compromis lu face à SA transaction (même résolution que P4), une ligne par champ,
  **chacune avec sa DESTINATION** : « envoyé à Hektor » (prix, date de signature, acte, séquestre, net vendeur, honoraires)
  ou « gardé chez nous » (les conditions) ; état « à trancher » / « à ajouter » / « d'accord » ; la page lue ; la ligne
  « À regarder » liée. `conditionsApres` : la liste COMPLÈTE après les choix (état, levée, note des autres gardés).
  `verdictDesChoix` : un choix vaut la note Vrai / Faux de la ligne « À regarder » (plus de double clic).
- `BilanCompromis.tsx/.css` : la fenêtre (habillage de la fenêtre de dépôt). Chaque ligne montre DEUX PLAQUES face à face
  -- le compromis (papier, coin plié) et la transaction --, on **touche la valeur qui reste** (le verbe est dans la
  plaque : prendre, ajouter, garder, laisser vide, retirer) ; l'autre s'efface. « page N » montre la page du compromis
  à droite (par-dessus la liste au téléphone). Groupes : À trancher, À ajouter, Déjà tranché (« Ajouté le … · Changer »),
  D'accord (replié). Le pied résume (« 2 envoyés à Hektor · 1 gardé chez nous · 1 laissé tel quel ») et le bouton dit ce
  qu'il fera (« Enregistrer et ouvrir la transaction »). Rien ne s'écrit avant « Enregistrer ». Lecture seule pour qui
  n'est ni responsable ni admin.
- **Où elle s'ouvre** : seule, une fois, quand une lecture de compromis a moins de 30 minutes et qu'il y a quelque chose à
  trancher ; sinon par la carte « Ce que dit le compromis » dans « À remplir », ou par « Revoir ce qu'il dit » dans
  « Lu par l'IA » (retrouver plus tard ce que l'IA a lu, et ce qui a été tranché, avec la date : `loadGedDecisionsDetail`).
- **L'écriture, par le chemin de chaque champ** (`appliquerBilan`, App.tsx) : la transaction RELUE d'abord ; « garder » =
  le journal seulement ; conditions = liste complète relue STRICTEMENT (`lireConditionsCompletesStrict`) puis réécrite ;
  champs Hektor = la modale « Modifier le compromis » EXISTANTE s'ouvre (événement), sur LA transaction, les valeurs
  posées APRÈS le préremplissage et marquées touchées, avec un bandeau « Repris du compromis lu… c'est ce bouton qui
  envoie à Hektor ». La décision « remplie » n'est notée qu'APRÈS l'envoi réussi de « Mettre à jour le compromis », et
  seulement si la case porte encore la valeur du compromis.
- **Retiré** : les cartes P4 (gedRemplir.ts) et la porte « chez nous seulement » de la date d'acte et du séquestre
  (remplirDepuisDocument refuse désormais ce geste) -- un seul chemin par champ.
Essais : `test_ged_bilan.cjs` 37 VERT (le cas réel de 18849 et ses témoins) ; `test_ged_remplir` adapté (38) ;
`test_ged_regles_lues` 95, `test_ged_lecture` 62 ; serveur `test_ged_lire` 88 ; les 13 essais GED verts, build vert. **Banc d'essai** (la vraie fenêtre, les valeurs de
18849, sans base) regardé à l'ordinateur et au téléphone (390 px) : lignes resserrées, plaques côte à côte, page du
document par-dessus au téléphone.
**AUDIT du 17/11 (« fais un audit quand même pour être sûr de toi ») -- ce qui part chez Hektor, PROUVÉ** :
- **fiche du bien et fiche d'un contact** : partent seules par les workers (file `app_annonce_pending` /
  `app_contact_pending`, puis travail `update_hektor_annonce_fields` / `update_hektor_contact`, ~10 min) : DPE de 63147
  écrit 17:41 -> travail 17:52 « updated » ; contact d'essai écrit 07:52 -> travail 08:03 « updated » ;
- **gardés chez nous, par décision** : conditions suspensives (aucun lecteur dans le worker ni la synchro) ; charge des
  honoraires au registre des mandats (chez Hektor elle vit sur le MANDAT : ⑦-7 interdit de le modifier) ;
- **valeurs d'une transaction** : le CARNET n'est envoyé par PERSONNE (`CHAMPS_APP_AFFAIRE = ()` depuis le 16/09 ; le
  worker ne lit le carnet que pour le juger -- R3 --, le retirer à l'arrivée, le purger) ; le SEUL chemin vers Hektor est
  `app_modifier_affaire_optimistic` -> `change_hektor_annonce_status` en reprise, et **depuis le 03/11 seules les cases
  TOUCHÉES partent** (le worker garde le reste du formulaire de Hektor ; témoin de reprise « modifiée dans Hektor depuis
  votre saisie ») -- prouvé : séquestre 6 500 envoyé le 23/10, « changed ».
**⛔ Deux erreurs de ma part, corrigées** : j'avais dit que la modale renvoyait le formulaire ENTIER (faux depuis le
03/11) ; et que pour 30770 il suffisait d'ouvrir « Modifier » et de valider (faux : la case préremplie depuis le carnet
n'est pas TOUCHÉE, elle ne serait pas partie). **Défaut trouvé** : la ligne « saisie_app » du lot 10a (30770, 12 400 €)
n'est jamais jugée par R3 (il ne juge que création et modification) ; la nuit remettra la colonne à la valeur de Hektor
et le carnet gardera 12 400 en silence -- et la fenêtre, qui comparait au CARNET, aurait dit « d'accord ».
**✅ LOT 1 (« Lot 1 oui, et à trancher doit proposer de corriger le registre avec la donnée du doc ») -- ÉCRIT, rien poussé** :
- **on compare à ce que Hektor a** (RecuManque, `lireCarnetDetailStrict`) : la colonne du registre ; une ligne de carnet
  « saisie_app » = jamais partie -> la case compte comme VIDE (« pas chez Hektor », à ajouter, et la fenêtre le dit) ;
  une ligne de création / modification pas encore jugée arrivée = en route -> comparée à la valeur envoyée, dite « pas
  encore confirmée ». Vaut aussi pour L7 (le lot 10a comparait au carnet, en ligne depuis `270cbd7`).
- **envoi DIRECT** (`envoyerAffaireChampsDirect`, api.ts) de la date de signature, de la date de l'acte et du séquestre :
  la MÊME porte que « Mettre à jour » (`app_modifier_affaire_optimistic`), la charge ne porte QUE ces cases, nommées
  touchées. Gardes de la modale AVANT toute écriture : un négociateur Hektor sur l'annonce, aucun geste Hektor en cours
  (`gesteHektorEnCours`, lu strictement). Le travail est suivi (onJobCreated), la décision notée après sa création.
  **Prix, net vendeur, honoraires** : par la modale (Hektor ne recalcule pas le net ; elle vérifie net + honoraires =
  prix) -- et s'il y en a un, TOUT passe par elle (un seul travail).
- **« À trancher » arrive PROPOSÉ** : la valeur du document est choisie d'avance (« corriger le registre »), on la
  décoche en touchant la transaction ; rien ne part avant « Enregistrer » ; lecture seule : rien de choisi.
Essais : `test_ged_bilan` 46 VERT (dont 30770 « jamais parti », le témoin « en route », l'envoi direct et ses gardes) ;
les 13 essais GED verts ; build vert ; banc d'essai regardé (correction proposée, « pas chez Hektor »).
⚠ **L'envoi direct n'est PAS encore éprouvé en réel** : sa charge est plus courte que celle de la modale (le worker
reprend le formulaire de Hektor pour le reste) -- à éprouver sur un bien d'essai avant tout usage sur un vrai bien.
✅ **MIS EN LIGNE le 17/11** (« Oui vas y ») : 11 commits poussés jusqu'à `2250250` -- les 4 du lot 10c et 7 d'autres
sessions glissés entre eux (classeur `3008f59`, `a05fc4c`, `bb8a78c` ; assistant `d03aae8`, `da872cd`, `0c55b36`,
`775f8a5`), accord de Frédéric pour l'ensemble. Vercel et Render servent `2250250`. **Vu en production sur 18849**
(fenêtre ouverte par « Voir et trancher », refermée sans enregistrer : 0 décision, le seul travail est la relecture
d'ouverture de la fiche, en lecture).
**⛔ L'ESSAI RÉEL DE L'ENVOI DIRECT A ÉCHOUÉ (17/11, 18849, « on éprouve le 18849 »)** : séquestre seul, travail
`080b32a1` -> refusé par le worker AVANT tout envoi (« Montant requis pour ce changement de statut »,
normalizeStatusTransactionPayload : il lit le montant dans la charge). Rien d'écrit chez Hektor (l'ouverture de
l'assistant est une lecture). **Frédéric : « les chantiers des workers sont tous documentés, si tu réutilises les workers
actuels comment a-t-il pu être refusé ? »** -- parce que je ne l'ai PAS réutilisé tel qu'il est documenté : le code le dit
(« la charge reste ENTIÈRE, le worker reconstruit le formulaire de Hektor avec elle » ; la RPC : « on ne l'allège pas ») et
j'ai envoyé une charge allégée en affirmant qu'aucun montant n'était exigé, sans aller jusqu'au contrôle. Ma faute.
Le travail raté est rejoué par la base (5 essais, aucun n'écrit chez Hektor), puis s'abandonne (le bouton n'agit qu'après
5 essais ou 3 h).
**✅ Décision de Frédéric (17/11) : « passer par la modale et cliquer tout seul, sans que l'utilisateur ne voie rien »** --
ÉCRIT, rien poussé :
- **l'envoi direct est RETIRÉ** (api.ts : `envoyerAffaireChampsDirect`, `gesteHektorEnCours`) : un seul chemin vers Hektor ;
- **la charge de la modale est sortie telle quelle** dans `chargeDeLaModale(reprendre)` (App.tsx), utilisée par le bouton
  « Mettre à jour » ET par l'envoi en arrière-plan : une seule construction ;
- **la modale en arrière-plan** (date de signature, date de l'acte, séquestre) : elle s'ouvre CACHÉE (rien n'est dessiné),
  se préremplit comme d'habitude, reçoit les valeurs du document marquées touchées, et part quand elle est PRÊTE (LA
  transaction désignée chargée, son carnet lu -- repère `carnetChargePour`), au rendu suivant, une seule fois ; mêmes gardes
  que son bouton (négociateur Hektor, geste en cours, montant) ; pas prête en 20 s -> rien ne part ;
- ⛔ **cachée, elle n'écrit RIEN d'autre que le travail** : visible, elle enregistre aussi la répartition (et, sur un dossier
  qui n'en a pas, une répartition 50/50 PAR DÉFAUT), la commission, les conditions, la note -- en arrière-plan ce serait
  écrit sans être vu ; rien n'y a changé, donc rien n'est écrit ;
- prix, net vendeur, honoraires : la modale s'ouvre VISIBLE (elle vérifie net + honoraires = prix) -- et s'il y en a un,
  tout passe par elle ;
- le résultat (envoyé ou refusé) s'affiche DANS la fenêtre « Ce que dit le compromis » ;
- **un envoi raté se voit** : si le dernier envoi d'une transaction est en erreur (`lireDernierEnvoiAffairesStrict`), sa
  valeur « en route » compte comme absente de Hektor -- « le dernier envoi à Hektor a échoué » -- et se propose de nouveau.
Essais : `test_ged_bilan` 51 VERT ; les 13 essais GED verts ; build vert. ⚠ L'envoi en arrière-plan n'est PAS encore
éprouvé en réel : sur 18849, le séquestre, une fois le travail raté abandonné.
✅ **EN LIGNE (`e4a2197`, « Pousse les deux ») ET PROUVÉ EN RÉEL le 17/11 à 20:44 sur 18849** : séquestre seul, par la
fenêtre -> la modale cachée a posé le travail `a6c4a212` avec la charge ENTIÈRE (montant 124 000, acquéreur 10650686,
`champs_touches` = sequestration seul) -> **« compromis 50139 MODIFIÉ et RELU chez Hektor : sequestre=12400 »**, prix,
net, date du compromis et date de l'acte INCHANGÉS ; carnet retiré à l'arrivée (0 ligne) ; registre = ce que Hektor a
retenu (séquestre 12 400) ; la condition suivie intacte ; aucune répartition écrite ; décision notée. La fenêtre a affiché
« Envoyé à Hektor (Séquestre 12 400 €) pour 18849 ». **Le séquestre de l'essai de Frédéric est donc corrigé chez Hektor.**
⚠ Vu pendant l'essai, corrigé : une décision « envoyé » dont l'envoi avait ÉCHOUÉ rangeait la ligne dans « Déjà tranché »
(sous « le dernier envoi a échoué ») -- elle redevient à trancher.
⏳ **Reste** : abandonner le travail raté `080b32a1` (5 essais épuisés ; le bouton de Santé n'apparaît qu'au prochain
relevé de surveillance) ; l'extension aux autres gestes (offre, vente) -- audit d'abord.
⏳ (ancien) **À faire après la mise en ligne** : la regarder sur 18849 (ouvrir la fenêtre et la modale, SANS cliquer « Mettre à
jour ») ; **le séquestre 12 400 € de 30770 est au carnet mais PAS chez Hektor** : ouvrir « Modifier » sur ce compromis
(la case est préremplie depuis le carnet) et « Mettre à jour le compromis » -- c'est son geste à lui.

### 12.29 Le lot 2 -- « Ce que dit l'offre » ; l'acte de vente n'a pas de bilan (17/11, « Pousse les deux et étends », puis « Vas-y »)

**Le plan présenté** : offre (montant, date, validité) par la modale en arrière-plan, l'offre acceptée dite « figée » ;
acte de vente (date en arrière-plan, prix par la modale visible), premier essai sur un bien vendu choisi par Frédéric.

**Ce que l'audit du code et de la base a trouvé en le faisant -- deux écarts au plan, dits ici :**

1. ⛔ **L'ACTE DE VENTE N'EST PAS ATTEIGNABLE** : un bien vendu sort des annonces -- **0 sur 147 ventes depuis juin**
   sont encore dans `app_dossier_current` (mesure du 17/11). Sa fiche s'ouvre alors en fiche d'index léger, qui n'a **pas
   de panneau des documents** (« Les documents ne peuvent pas être modifiés depuis une fiche d'index léger ») : la fenêtre
   ne s'afficherait jamais. **Rien n'est codé pour l'acte.** Le cas réel qui reste : l'attestation du notaire déposée sur
   un bien encore au COMPROMIS (pas encore de vente au registre) -- ce serait CRÉER la vente (passer en Vendu), un autre
   geste, à décider par Frédéric.
2. ⚠ **L'OFFRE NE PART PAS CACHÉE, elle ouvre sa modale VISIBLE** : le chemin de l'offre dans le worker
   (`submitHektorTransactionStatus`, POST plat) construit un corps NEUF et y met TOUJOURS `montantOffre`, `dateOffre`,
   `nbJoursValidite` (et les honoraires de sortie) depuis la charge -- **il n'applique ni la liste des cases touchées (B,
   03/11) ni le témoin du rejeu (B2)**, qui n'existent que dans l'assistant (compromis, vente). Corriger une seule case
   renvoie donc les autres telles que la modale les a préremplies. Caché, ce serait envoyé sans être vu : la règle retenue
   est « en arrière-plan seulement là où le worker n'envoie que les cases touchées ». Une ligne suffit à changer d'avis
   (`estEnvoiDirect`, BilanCompromis.tsx).

**Ce qui est fait (rien poussé) :**
- `bilanOffre` (lib/gedBilanCompromis.ts) : l'offre lue face à SON offre au registre -- montant (seulement frais d'agence
  inclus ou sans base lue, comme L7), **date de la PROPOSITION** (`dateOffreFaite`, jamais la colonne `date` qui porte le
  dernier mouvement -- mémoire du 12/11), validité en jours (lue, ou déduite de « valable jusqu'au », 1 à 365). Départage
  des offres par la date de proposition. `bilansDuDossier` : l'offre puis le compromis, chacun sa fenêtre.
- ⛔ **Offre ACCEPTÉE** : figée chez Hektor (200 + corps vide, mesure du 13/10) ; **offre REFUSÉE** : le registre porte la
  date du refus, la modifier la réécrirait -- leurs écarts se MONTRENT (groupe « Figé chez Hektor », raison dite), rien ne
  se propose, la carte ne les compte pas « à trancher ». Garde en défense dans l'envoi caché (`offreAccepteeFigeeChezHektor`).
- La fenêtre dit « Ce que dit l'offre » / « L'offre » ; la modale s'ouvre sur l'onglet **Offre** et LE numéro de l'offre ;
  seul le **montant** est marqué touché (jamais le prix de vente, relu chez Hektor par le worker) ; la validité a sa case
  (`validity_days`) ; la décision est notée `modale_modifier_offre` après l'envoi ; la bannière dit « Repris de l'offre lue ».
- La garde du montant de l'envoi caché ne demande plus le prix de vente que là où le bouton le demande
  (`statusChangeNeedsSalePrice`).
Essais : `test_ged_bilan` **66 VERT** (14 neufs, section ⑥) ; les 13 fichiers GED verts ; build vert.
⚠ **Pas vu à l'écran, pas éprouvé en réel** : une seule offre lue en base (62774, SPECIMEN, bien hors annonces), aucune
sur une offre PROPOSÉE vivante. L'essai réel demande une offre proposée et sa pièce lue -- à choisir par Frédéric.
✅ **DÉCISIONS DE FRÉDÉRIC (17/11)** : « 1. Oui 2 laisse tomber 3. Visible ».
- **POUSSÉ** (`869e260`, seul commit de la liste, relue juste avant).
- ⛔ **L'ACTE DE VENTE : « laisse tomber »** -- ni bilan, ni « créer la vente depuis l'attestation ». **Ne pas relancer.**
- ⛔ **L'OFFRE PART PAR SA MODALE VISIBLE** -- jamais en arrière-plan (tranché). Ne pas l'ajouter à `ENVOI_DIRECT`.
⏳ **Reste** : l'essai réel, sur une offre PROPOSÉE d'un bien vivant avec sa pièce lue (à choisir par Frédéric).

### 12.30 AUDIT du lot 3 -- la fiche du bien face à ses documents (17/11, « On enchaîne », lecture seule, rien codé)

**Aujourd'hui** : les cartes « Remplir » (gedRemplir.ts, P1 à P3) ne remplissent qu'une case VIDE, relue juste avant
(`remplirDepuisDocument`) ; une case remplie qui diffère sonne seulement dans « À regarder » (L6 DPE, L15 Carrez, L16
copropriété, L12/L14/L4/L1 mandat). Le lot 3 = ces écarts deviennent « à trancher », la correction proposée avec la valeur
du document (accord de principe de Frédéric : « à trancher doit proposer de corriger le registre avec la donnée du doc »).

**Les cases, et par où elles partent** (toutes par `editAnnonceOptimistic` -> `app_annonce_pending` -> worker
`update_hektor_annonce_fields`, ~10 min, contrôle au retour 8a7 -- PAS de modale, l'envoi est déjà en arrière-plan) :
- DPE : `dpe_cons`, `dpe_ges`, `dpe_date` (L6, tolérance ± 1) -- ⭐ `dpe_cons` prouvé en réel le 16/11 (63147, 17:41 -> 17:52) ;
- état des risques : `diag_risques_nat_tech_date` ;
- copropriété (bien MARQUÉ copropriété seulement) : `copropriete_nb_lot`, `copropriete_quote_part` (L16) -- ⚠ le groupe de
  Hektor qui porte la copropriété est celui que la sauvegarde du SECTEUR remet à zéro : garde du worker active (22/10) ;
- Carrez : `SURF_CARREZ` (L15, sens unique : seulement plus PETITE de 5 %) -- part dans le groupe « surfaces » du worker
  (13 champs : surface, pièces, chambres…), jamais éprouvée depuis la GED.
- ⛔ **le mandat** (n°, prix, honoraires, charge au registre, prix de l'avenant face au prix affiché) : décision ⑦-7
  (« je ne souhaite pas pouvoir modifier un mandat ») -- montré, jamais corrigé d'ici. Le prix affiché part dans le
  groupe prix de Hektor, qui renvoie aussi les honoraires : à ne pas ouvrir sans décision.

**Mesure** : 0 document de ces types lu sur un bien réel -- tout est sur les biens d'essai (63147 DPE, 62774 ERP et
copropriété, 63331 surfaces et mandat). La lecture n'est pas allumée pour le parc (DPA d'abord).
⚠ **Trouvé en passant** : deux portes, deux seuils sur la même case -- P2 propose de remplir `copropriete_quote_part` si
ELLE est vide, L16 compare à `quote_part ?? CHARGES`. Une fiche qui porte CHARGES sans quote-part reçoit les deux.

### 12.31 Le lot 3 -- la fiche du bien face à ses documents (18/11, « Oui » au plan du §12.30, mandat seulement montré)

**Fait (rien poussé)** :
- `lib/gedBilanFiche.ts` (`bilansFiche`) : une fenêtre par document -- « Ce que dit le DPE » (consommation, émissions ± 1,
  date), « l'état des risques » (date), « la fiche synthétique » (nombre de lots ; la fiche qui porte les lots PRINCIPAUX
  est d'accord, comme L16), « l'appel de fonds » (charges annuelles du lot, ± 10 %, comparées à `copropriete_quote_part`
  seule -- la case écrite), « le métré » (Carrez, SENS UNIQUE comme L15). Case vide -> « à ajouter » ; remplie et
  différente -> « à trancher », la valeur du document proposée (« corriger la fiche »). ⛔ Copropriété : seulement sur un
  bien marqué copropriété. ⛔ **Le mandat n'a pas de fenêtre** (⑦-7) : ses écarts restent dans « À regarder ».
- Chaque ligne porte sa case Hektor (`champFiche`) et ce que la fiche portait (`temoin`). L'écriture
  (`appliquerBilanFiche`, App.tsx) RELIT la fiche, n'écrit que les cases qui portent encore le témoin (et la copropriété
  encore marquée), en UN `editAnnonceOptimistic` -- le chemin habituel de la fiche (chez nous tout de suite, Hektor par le
  worker ~10 min, contrôle au retour 8a7), sans modale. Une case changée entre-temps : rien écrit, décision « echec »
  (`case_changee`), et c'est dit.
- La fenêtre dit « La fiche » au lieu de « La transaction » ; qui tranche la fiche = qui peut la remplir (les cartes
  « Remplir »). Les bilans de la fiche ne dépendent pas de la lecture des transactions.
- ⛔ **Un seul chemin par case** : les cartes « Remplir » P1 (DPE, état des risques) et P2 (copropriété) sont RETIRÉES
  (la fenêtre propose aussi la case vide). P3 (la charge vide au registre des mandats) reste.
- La note Vrai / Faux de « À regarder » se déduit des choix pour L6, L15 et L16 aussi (`verdictDesChoix` : toute ligne de
  la même règle, sauf L20 qui se départage par libellé).
Essais : `test_ged_bilan` **84 VERT** (18 neufs, section ⑦) ; `test_ged_remplir` 38 VERT (5 essais P1/P2 réécrits : ils
prouvent que les cartes ne reviennent pas) ; les 13 fichiers GED verts ; build vert.
⚠ **Pas vu à l'écran, pas éprouvé en réel** : seule la consommation du DPE a été envoyée en réel par ce chemin (16/11,
63147) ; émissions, dates, copropriété et Carrez jamais. Premier essai proposé sur les biens d'essai (63147 DPE, 62774
copropriété et état des risques, 63331 métré).

**✅ POUSSÉ (`c64709c`) ET ÉPROUVÉ EN RÉEL le 18/11 (00:20 -> 00:47) sur le bien d'essai 63331**, pièces ENTIÈREMENT
FICTIVES fabriquées pour l'essai (scratchpad `lot3_essai/fabriquer.cjs`), déposées par l'écran (« Pousse et … éprouve la
plupart des modifications ») :
- **tour A** : DPE (245 kWh, 38 kg, 15/10/2026), état des risques (04/11/2026), fiche synthétique (36 lots, 14
  principaux), appel de fonds (450 € par trimestre). 4 dépôts `done` chez Hektor ; 3 lectures « lu », ⚠ la fiche
  synthétique lue « pas_ce_type » (valeurs lues, type refusé par l'IA) -> pas de fenêtre pour elle.
  Fenêtres : « Ce que dit le DPE : 3 à trancher » (fiche 210 / 45 / 10/09/2026), « l'état des risques : 1 » (10/09/2026),
  « l'appel de fonds : 1 » (fiche 120 € par an -> 1 800). Choix : consommation et date CORRIGÉES, émissions GARDÉES
  (décision « ignoree »), état des risques et charges corrigés. **UN travail** `update_hektor_annonce_fields`
  (`b5babe1b`, 00:34:00 -> 00:34:17, 0 erreur) : Hektor « mise à jour effectuée » pour les groupes diagnostiques
  (dpe_date, diag_risques_nat_tech_date), dpe_cons et copropriété (quote-part). **Relu chez Hektor** (`3c434bee`) :
  dpe_cons 245, dpe_date 2026-10-15, risques 2026-11-04, quote-part 1800 ; **témoins inverses** : émissions gardées =
  45 (intactes), copropriété toujours OUI, nombre de lots non touché = 24.
- **tour B** : DPE RECTIFICATIF (198 kWh, 29 kg, 10/11/2026) -> la fenêtre montre la fiche telle que Hektor l'a
  rendue (245 / 45 / 15/10/2026), trois corrections de cases REMPLIES, enregistrées en un envoi.
  ✅ Travail `cf7fe8a9` (00:48:03 -> 00:48:16, 0 erreur), Hektor « mise à jour effectuée » ; relu : 198 / 29 / 2026-11-10.
- ✅ **LE CONTRÔLE AU RETOUR A JUGÉ LES DEUX ENVOIS** (`app_annonce_saisie_modif`, témoin positif du zéro de
  `app_v_annonce_modif_ecarts`) : `b5babe1b` 4/4 « identique », `cf7fe8a9` 3/3 « identique » -- 7 cases sur 7, 0 écart.
⏳ Reste : voir à l'écran les deux corrections (en ligne avec `d2e8888`, poussé par la session « Page d'accueil » avec
  l'accord de Frédéric) ; ⚠ la fiche synthétique jugée « pas_ce_type » par l'IA (valeurs lues justes) -- à regarder dans
  la consigne de `copro.carnet` (une fiche synthétique EST de ce type, sous-type `fiche_synthetique`). La Carrez de 63331
  (64,35 m² lus, 66 m² sur la fiche : -2,5 %) est « d'accord » par la règle du sens unique (5 %) -- pas de carte, JUSTE.
⚠ **Deux défauts d'ergonomie vus à l'écran, corrigés (commit suivant, pas poussé)** :
1. les cartes « Ce que dit… » n'apparaissaient qu'au RECHARGEMENT : la lecture IA finit après l'arrivée du document et
   rien ne le disait au panneau -> le dépôt émet `ged:lecture-faite`, le panneau relit ses lectures ;
2. après « Enregistrer », la fenêtre BASCULAIT seule sur la lecture neuve suivante et cachait son résultat -> plus jamais
   pendant qu'une fenêtre est ouverte, et une seule ouverture par lot de lectures neuves.

### 12.32 Contrôle d'après la nuit du 17 au 18/11, et la fiche synthétique refusée (18/11, « Oui et le run de nuit est fini contrôle tes correctifs »)

**✅ Ce que la nuit devait remettre à la valeur de Hektor a TENU** (mesuré à 06:50, lecture seule) :
- **63331** (`app_dossier_details_current`, relue par la nuit : `date_entree_file` 04:48:36) : consommation 198, émissions
  29, date du DPE 2026-11-10, état des risques 2026-11-04, quote-part 1800 ; témoins : copropriété OUI, lots 24, Carrez 66.
- **18849 / transaction 30770** (`app_affaire_ledger`) : séquestre **12 400**, prix 124 000, net 115 000, date 2026-10-23,
  date d'acte 2027-01-23 ; carnet (`app_affaire_champ_app`) : **0 ligne** -- la nuit, qui remet la colonne à la valeur
  de Hektor, a gardé 12 400 : c'est bien Hektor qui l'a.
- **Contrôle au retour** : `b5babe1b` 4/4 et `cf7fe8a9` 3/3 toujours « identique » ; `app_v_annonce_modif_ecarts` = 0.
- ⚠ Le run n'était pas tout à fait fini à 06:51 (dernière étape : rattrapage des photos, 06:47) ; la descente de 06:45
  l'attend.
- ⏳ **Toujours en `error`** : le travail raté `080b32a1` (5 essais, « Montant requis… », rien d'écrit chez Hektor) --
  l'abandonner depuis Santé est un geste en base, sur accord.

**La fiche synthétique de 63331 lue « pas_ce_type » -- ce qui est mesuré** :
- l'IA a rendu `ce_type = faux` ET, dans la même réponse, `sous_type = fiche_synthetique` avec TOUTES les valeurs justes
  (36 lots, 14 principaux, 30/09/2026, budget 62 000, fonds 9 300, syndic professionnel, aucune procédure) ;
- la même fiche de lecture (`copro.carnet/1`), le même modèle (`gpt-6-luna`, effort « none »), par le texte, avait
  ACCEPTÉ le 12/11 une fiche synthétique fictive presque identique sur 62774 (48 lots) ;
- la seule différence de texte : « (SPECIMEN) » dans la phrase d'essai (présente aussi sur le DPE, l'état des risques et
  l'appel de fonds, acceptés) et une immatriculation « ZZ9999999 (fictif) ».
- ⇒ **ce n'est pas la consigne** : c'est le jugement « est-ce le bon type ? » de l'IA qui n'est pas stable sur une pièce
  fictive. Cause exacte NON PROUVÉE (il faudrait relire, donc payer un appel ; pas fait).
- ⚠ **Le vrai défaut, pour l'utilisateur** : un « pas_ce_type » JETTE toute la lecture (`gedLecture.ts:280`), l'écran dit
  « vérifie le type » -- or le type est juste -- et AUCUN geste ne permet de relire ni de garder la lecture (« Relire »
  n'existe que sur une lecture en ERREUR, dans la fenêtre de dépôt, `DepotDocuments.tsx:686`).
- Pistes présentées à Frédéric, RIEN codé : A) contradiction côté serveur (ce_type faux mais sous_type attendu -> « lu ») ;
  B) sur un « pas_ce_type », un bouton « C'est bien ce type : garder la lecture » (sans nouvel appel, décision notée) ;
  C) un bouton « Relire » (un appel payé, peut refuser encore).

### 12.33 AUDIT -- « pas ce type » : un verdict rendu AVANT la lecture, et sans recours (18/11, « Audite plus en profondeur ce problème et trouve la solution idéale », lecture seule, rien codé)

**Mesuré** : 42 lectures en base, 1 seule « pas_ce_type » (la fiche synthétique de 63331) ; le journal des agents dit
pareil (39 `ged_lecture`, 1 refus). Mais c'est une FAMILLE, pas un cas : le banc du 13/11 (§12.16) avait vu une
attestation de vente refusée 1 fois sur 3, soignée alors en retouchant LA consigne de ce seul type.

**La cause, dans le code** (`openai_ged_lecture_service.py`) :
1. `schema()` met `ce_type` en PREMIÈRE case d'un schéma strict, et l'appel tourne en effort « none » : l'IA écrit son
   verdict sur le type AVANT d'avoir relevé une seule valeur. Sur 63331 elle a dit « faux » puis, trois cases plus loin,
   `sous_type = fiche_synthetique` avec les 12 valeurs justes.
2. L'en-tête annonce un CODE (« Type annoncé : copro.carnet »), pas le libellé du catalogue (« Carnet d'entretien, fiche
   synthétique ») : le mot « carnet » tire vers le carnet d'entretien.
3. La règle est floue : « faux si ce document n'est manifestement pas du type annoncé » -- rien ne dit qu'une pièce
   fictive, partielle ou d'essai reste de ce type. Les deux pièces refusées étaient fictives ; celle de 62774 (12/11),
   presque identique, était passée : le verdict est un tirage.
4. La consigne commune vient du CODE (`app_agent_prompt` n'a aucune ligne `ged%`) : une correction au code vaut pour les
   25 fiches d'un coup.

**Ce qu'un refus fait aujourd'hui** : les valeurs SONT gardées en base (`enregistrer`), mais TOUS les lecteurs de
l'écran ne prennent que `etat = 'lu'` (gedBilanFiche, gedBilanCompromis, gedRemplir, gedReglesLues, `dateEtatLue`) et le
résumé dit « vérifie le type » -- or le type est juste. Aucun recours : « Relire » n'existe que sur une ERREUR, dans la
fenêtre de dépôt (`DepotDocuments.tsx:686`), parce que relire demande le fichier DANS le navigateur ; et le nom d'un
document est définitif une fois envoyé. Les valeurs PRIVÉES (numéro de pièce) sont jetées dès le refus (voulu).

**Le garde-fou doit rester** : il a refusé à juste titre la facture EDF déposée en « facture d'honoraires » (§12.16).

**La solution proposée, en deux couches** (rien codé, attend le « vas-y ») :
- **A. Prévenir, au serveur, pour toute la famille, sans base** : `ce_type` passe en DERNIÈRE case (après les valeurs) ;
  l'en-tête donne le libellé (« Carnet d'entretien, fiche synthétique ») ; la règle commune dit : faux SEULEMENT si le
  document est d'un AUTRE type ; une pièce d'essai, fictive, incomplète ou mal remplie reste de ce type. Les consignes
  propres (facture d'un fournisseur, attestation courte) ne bougent pas. Coût par lecture : nul. Preuve : un banc sur
  pièces FICTIVES (les deux refusées doivent passer, la facture EDF doit rester refusée), ~1 centime, sur accord.
- **B. Recours, à l'écran, l'humain tranche** : sur une lecture refusée, la pièce dit « L'IA doute que ce soit un(e)
  <libellé> » avec « C'est bien ce type : garder la lecture ». Une fonction neuve passe la lecture à « lu » et ÉCRIT
  AVANT / APRÈS au journal (`app_ged_journal`, objet « lecture » à ajouter à son CHECK) : le verdict de l'IA n'est jamais
  perdu, et AUCUN lecteur ne change (ils lisent déjà `etat = 'lu'`) -- les cartes « Ce que dit… » apparaissent.
  Patch en base (accord). Pas pour les 5 types sensibles (pièces des personnes) : leur registre ne se remplit que par
  une lecture jugée juste par l'IA.
- **Écartées** : la contradiction côté serveur (ne vaut que pour les fiches qui ont un sous-type -- un remède par cas) ;
  un bouton « Relire » (un appel payé, le fichier à rapatrier, et le tirage peut retomber faux).

### 12.34 LE BANC -- pourquoi l'étape 2 refuse au hasard : LE CODE DU TYPE, PROUVÉ (18/11, « il faut vérifier »)

**Le banc** (`scratchpad/banc_type/` : `textes.mjs` refait le texte EXACT du navigateur avec pdfjs ; `banc.py` rejoue
l'appel de `/ged/lire` À L'IDENTIQUE -- consigne, schéma strict, en-tête, `gpt-6-luna`, effort « none » -- N fois par
variante). Pièces FICTIVES seulement, appel direct à l'IA, RIEN écrit en base. ~640 appels, **~0,19 $**.
L'outil d'enquête : une variante « raison » ajoute, JUSTE APRÈS `ce_type`, deux cases « ce qu'est ce document » et
« pourquoi » -- elle fait PARLER l'IA et GROSSIT le défaut (une loupe, pas un remède).

**Les mesures** (refus / appels) :
- à l'identique : fiche synthétique de 63331 **0/30** (+ 0/2), celle de 62774 **1/30** -> le refus de production est un
  tirage RARE (~2 %), tombé sur 63331 ;
- avec la loupe : **11/30**, et la raison est TOUJOURS la même : « c'est une fiche synthétique, **et non un carnet
  d'entretien** comme annoncé ». L'IA lit le CODE `copro.carnet` comme « carnet d'entretien » -- malgré la consigne qui
  dit pourtant « fiche synthétique ou carnet d'entretien » ;
- **⛔ mes hypothèses du §12.33 étaient en partie FAUSSES** : sans « fictif / specimen » -> **20/30** (pire : ce n'est pas
  la pièce fictive) ; `ce_type` en dernière case -> **8/30** (ne guérit pas) ; la règle « faux seulement si AUTRE
  type » -> **29/30** (AGGRAVE : l'IA tient la fiche synthétique pour un autre type que le carnet) ;
- **le libellé du catalogue dans l'en-tête** (« Type annoncé : Carnet d'entretien, fiche synthétique (copro.carnet) ») :
  **0/30** avec la loupe, **0/30 + 0/30** à l'identique sur les deux fiches. Les trois réunis : 0/30 ;
- **le garde-fou TIENT avec le libellé** : note d'honoraires annoncée « carnet » 15/15 refusée ; appel de fonds annoncé
  « carnet » 15/15 ; fiche synthétique annoncée « facture d'honoraires » 15/15 ; et la vraie note d'honoraires 0/15.
  Bilan libellé : **0 bon document refusé sur 105, 45 mauvais refusés sur 45** ;
- **la famille** : une CONVOCATION d'AG annoncée `copro.pv_ag` -> 0/20 à l'identique mais **20/20 avec la loupe**
  (« le type annoncé est un procès-verbal »), alors que sa consigne dit « procès-verbal ou convocation » -> **0/20 avec
  le libellé**. Un budget prévisionnel en `copro.appel_fonds` : 0 refus dans tous les cas. L'attestation de vente en
  TEXTE : 0/150 (le refus du 13/11 était sur un SCAN, en images -- non reproduit, cause non prouvée).
- ⇒ **LA CAUSE** : l'en-tête n'annonce que le code (« Type annoncé : copro.carnet ») ; quand le code ne nomme QU'UN des
  documents que le type couvre (carnet / fiche synthétique ; PV / convocation ; mais aussi, NON mesurés : appel de fonds
  / budget, règlement / état descriptif, acte / attestation, compromis / promesse, titre / origine, fin / dénonciation,
  annulation / désistement, facture / note, surfaces Carrez / habitable), l'autre document passe pour « pas ce type »
  -- rarement en temps normal, mais au hasard. Le CODE pèse plus que la consigne.

**Le remède, mesuré** (rien codé, attend le « vas-y ») : l'en-tête donne le LIBELLÉ du catalogue avant le code.
`OpenAIGedLectureService` charge DÉJÀ le catalogue (`self.portier.types()`, en cache, pour les types sensibles) : deux
ou trois lignes, aucune requête de plus, aucun coût par lecture ; repli sur le code seul si le libellé manque. Vaut pour
les 29 types lus d'un coup. **Ne PAS** retoucher la règle commune ni l'ordre des cases (mesuré : inutile ou pire).
Le recours à l'écran (§12.33, couche B) devient un filet pour un éventuel reste, à décider à part.

### 12.35 LE REMÈDE CODÉ -- le libellé du catalogue dans l'en-tête de la lecture (18/11, « Oui, vas-y »)

**Le code** (`backend/app/services/openai_ged_lecture_service.py`) : une méthode `type_annonce(code)` rend
« <libellé du catalogue> (<code>) », lu dans `self.portier.types()` (le catalogue `app_ged_type`, DÉJÀ chargé et en cache
pour les types sensibles : aucune requête de plus, aucun coût par lecture). L'en-tête devient
« Type annoncé : Carnet d'entretien, fiche synthétique (copro.carnet) ». **Repli sur le code seul** si le libellé manque
ou si le catalogue est illisible (la lecture n'en dépend jamais). Vaut pour TOUS les types lus, pièces des personnes
comprises (leur en-tête gagne aussi le libellé ; même mécanisme, non mesuré à part). **Rien d'autre ne bouge** : ni la
règle commune, ni l'ordre des cases, ni les consignes, ni l'écran, ni la base.

**Les essais** : `backend/tests/test_ged_lire.py` 91/91 (3 neufs : le libellé puis le code ; TÉMOIN sans libellé, le code
seul ; catalogue en panne, repli sur le code) ; les trois autres bancs de lecture verts (état civil 16, financement 19,
personnes 36).

**La preuve par le VRAI code** (`scratchpad/banc_type/banc_vrai.py` : appelle `OpenAIGedLectureService.lire()` lui-même,
qui n'écrit RIEN en base -- c'est `enregistrer()` qui écrit ; catalogue de production recopié, 5 lignes lues le 18/11) :
95 appels, **0,0225 $**, **95/95 verts** --
- acceptés comme il faut : fiche synthétique de 63331 0/20 refus, celle de 62774 0/20, convocation d'AG en PV d'AG 0/15,
  note d'honoraires en facture d'honoraires 0/10 ;
- refusés comme il faut (le garde-fou tient) : note d'honoraires annoncée carnet 10/10, appel de fonds annoncé carnet
  10/10, fiche synthétique annoncée facture d'honoraires 10/10 -- ⭐ avec le VRAI libellé « Facture ou note d'honoraires
  GTI » (le banc du §12.34 en avait pris un approchant).

**✅ POUSSÉ et EN SERVICE (18/11)** : 9d5a6fd poussé avec l'accord de Frédéric (« Oui, pousse ») ; Render sert ce commit,
`/health` démarré à 09:09:28 UTC. **Ce qui reste** :, en production, une fiche synthétique
déposée en `copro.carnet` doit sortir « lu ». La couche B (recours à l'écran) reste à décider à part.

**✅ ÉPROUVÉ EN RÉEL le 18/11 à 10:18 (« vas y test »), par l'écran, sur le bien d'essai 63331** : la MÊME pièce fictive
que celle refusée la nuit du 17/11 (fichier identique octet pour octet, `lot3_essai/tourA/…`), redéposée sous le nom
« ESSAI LIBELLE en-tete lecture IA 63331 FICTIF.pdf » (l'écran a vu le doublon de contenu et refusé un nom trop proche :
cochée « l'envoyer quand même », nom changé), type proposé et gardé « Carnet d'entretien, fiche synthétique ».
- lecture **« lu »** (`copro.carnet/1`, par le texte, 0,000256 $), 12 valeurs lues -- les MÊMES 12 que la lecture
  « pas_ce_type » du 17/11 (syndic, immatriculation, sous-type fiche synthétique…) ;
- la fenêtre « Ce que dit la fiche synthétique » s'est ouverte seule : 1 à trancher (36 lots lus / 24 sur la fiche) ->
  **FERMÉE SANS ENREGISTRER** : rien écrit sur le bien, le témoin « 24 lots » reste ;
- dépôt chez Hektor : travail `666b63e5` `upload_document_to_hektor` **done** en 15 s, 1 essai, 0 erreur.
⚠ Une pièce FICTIVE de plus sur 63331 : elle rejoint le ménage SPECIMEN/FICTIF à faire (63331, 63147). L'ancienne
lecture « pas_ce_type » du 17/11 reste telle quelle (aucune relecture d'un dépôt passé).

### 12.36 Les trois restes (18/11, « vas y » sur les trois) -- mesuré, RIEN écrit

**1. Le travail `080b32a1` (62850) : DÉJÀ TRANCHÉ, ne rien faire.** Tranché le 17/11 à 23:26 (Paris) en mode « refait » au
nom de Frédéric (`app_pending_resolution` 2075, `supabase/patch_trancher_62850_2026-11-17.sql`, commit `b244441`) : le
geste avait abouti au 2e essai (20:44, « Sous compromis »). Il reste `error` EXPRÈS (historique) ; 0 geste en attente
d'un humain. ⛔ « Abandonner » aurait DÉFAIT un vrai changement de statut. Ma ligne « toujours en erreur » était périmée.

**2. Le ménage des pièces fictives -- la liste** (`app_console_document`) : **31 documents**, 30 sur 63331 et 1 sur 63147
(« DPE SPECIMEN essai 2026.pdf ») ; TOUS marqués ESSAI / SPECIMEN / FICTIF (0 sans marque), tous privés, tous portent
leur numéro Hektor supprimable, AUCUN engagé en signature (statut `to_send` ou vide ; 0 demande de signature liée).
Le geste existe : `delete_document_from_hektor` (43 faits, 0 erreur) -- il refuse un document signé, ÉCRIT LA TRACE
avant de détruire (journal des suppressions), vérifie chez Hektor, puis retire coffre, serveur et ligne.
⚠ Ce qu'il ne fait PAS : la GED n'a pas de clé vers `app_console_document` -- les 31 classements, leurs lectures,
valeurs et le registre privé des pièces d'essai RESTENT en base (invisibles à l'écran : le panneau croise lectures et
documents présents). Les retirer = un patch à part (la cascade part du classement).
⚠ Règle du projet : prévenir la session signature avant de toucher `app_console_document`.

**3. Le recours à l'écran (couche B du §12.33) -- le dessin**, sur le patron de `app_ged_decider` :
- base : une fonction `app_ged_lecture_garder(lecture)` (compte actif, interrupteur `ged_lecture_ia`, périmètre du bien,
  refus si l'état n'est pas « pas_ce_type » ou si le type est SENSIBLE) qui passe la lecture à « lu » (ou « incomplet »
  sans valeur) et écrit AVANT / APRÈS dans `app_ged_journal` (objet « lecture » à ajouter à son CHECK) ; inverse et
  répétition ;
- écran (`RecuManque.tsx`, liste « Lu par l'IA ») : sur une lecture refusée, « C'est bien ce type : garder la
  lecture », puis relecture des lectures -- les cartes « Ce que dit… » apparaissent ; AUCUN lecteur ne change ;
- mesuré : 1 seule lecture « pas_ce_type » en base (63331, 17/11) -- le filet servirait d'abord à elle.

**✅ LE MÉNAGE EST FAIT (18/11, 10:22 -> 10:34, « Pousse et vas y »)** : 31 travaux `delete_document_from_hektor`
(raison `menage_pieces_fictives_18_11`, au nom de Frédéric, la charge du geste de l'écran) -- d'abord 1 seul (63147,
`acbfdf55`, done) pour éprouver, puis les 30 de 63331. **31/31 done** ; 1 échec « Hektor 500 on context switch » (à
l'ouverture de la session Hektor, AVANT tout appel de suppression : rien d'effacé) sur l'état des risques, reposé et
passé (`da9d08f4`). Journal des suppressions : **31 traces, 31 « confirmé chez Hektor »**. Il reste **0 document** sur
63331 et 63147 ; file vide. Les lectures GED de ces pièces restent en base (invisibles, cf. plus haut) -- dont la
seule « pas_ce_type », dont le document n'existe plus.

**✅ LE RECOURS EST EN PRODUCTION (18/11, « Oui, pose et pousse »)** : patch POSÉ (4 contrôles verts : CHECK du journal
élargi, porte SECURITY DEFINER fermée à anon, `ged_lecture_ia` inchangé « admin », 0 lecture touchée) ; `5b93490` et
`4e0a82c` POUSSÉS (jusqu'à `4e0a82c` seulement : le commit `527c378` de la session classeur, posé par-dessus, est
resté chez elle) ; l'écran est EN LIGNE sur Vercel (le bouton est dans le paquet servi). Le détail :
- `supabase/patch_ged_garder_lecture_2026-11-18.sql` (+ `_INVERSE`, + `_REPETITION`) : la fonction
  `app_ged_lecture_garder` et le CHECK du journal élargi à « lecture ». **Répétition jouée VERTE (8 contrôles,
  rollback)** en utilisateur (Frédéric) : refusée -> lu, sans valeur -> incomplet, 2e fois refusée, pièce sensible
  refusée, lecture « lu » refusée, écriture directe interdite, 2 lignes au journal à son nom, rien d'autre touché ;
  vérifié ensuite : rien n'est resté (fonction absente, CHECK d'origine, mise en scène partie). L'inverse s'ARRÊTE si
  une lecture a déjà été gardée (une décision humaine ne se défait pas en silence).
- écran : `lib/ged.ts` `gedGarderLecture` ; `RecuManque.tsx`, liste « Lu par l'IA » : le bouton « C'est bien ce type :
  garder la lecture » sur une lecture refusée (pas pour les 4 types des personnes lus), la pastille dit « · N refusé(s)
  par l'IA », puis relecture des lectures. Build vert, 13 bancs GED de l'écran verts.
- ⚠ ORDRE : poser le patch AVANT de pousser l'écran (sinon le bouton appellerait une fonction absente -- sans dégât :
  il n'y a aujourd'hui AUCUNE lecture refusée à l'écran). ⚠ Pas vu à l'écran : il n'existe plus de cas réel ; la
  première lecture refusée le montrera.

### 12.37 AUDIT -- les faits du dossier « cran on » (DPA, analyse d'impact, registre, clause) (18/11, « enchaîne dans le chantier », lecture seule, rien rédigé)

Le code du chantier est fini (hors options et essais qui attendent Frédéric) ; la mesure court jusqu'au 30/11. L'étape
suivante du plan (§0) est le dossier à réunir AVANT le cran « on ». Voici les faits, mesurés dans le code et la base.

**Les deux appels à l'IA** (fournisseur OpenAI, API Responses, modèle `gpt-6-luna`, `store: false` sur chaque appel) :
- **étape 1, le classement** (`/ged/classer`) : le nom du fichier, le nombre de pages, le DÉBUT du texte de chaque page
  et/ou des images de pages -> un type proposé ;
- **étape 2, la lecture** (`/ged/lire`) : le texte du document (20 000 caractères, 80 000 pour un compromis, titre plus
  long) et/ou jusqu'à 6 pages en image (18 pour un compromis scanné) -> les champs de la fiche du type.
- ⚠ **L'IA VOIT TOUT CE QUI EST ENVOYÉ**, pas seulement les champs gardés : un compromis part en entier (dans la limite),
  avec les noms, adresses, prix, et ce que les parties y ont écrit. Ce que NOUS gardons est plus étroit que ce qui PART.
- Gardes avant envoi : le RIB jamais (nom du fichier, IBAN dans le texte) ; pièces des personnes derrière leur propre
  interrupteur (`ged_lecture_personnes`) ; 1re page seule pour certaines pièces ; les catégories exclues par décision
  (santé, montant / taux / banque du prêt, assurance, feuille de présence, débiteurs, photo ou signature d'une pièce,
  bande MRZ, motif d'une mesure de protection, enfants) ne sont pas dans les schémas.
- ⚠ À VÉRIFIER dans les conditions du fournisseur (pas mesurable d'ici) : la durée de conservation côté OpenAI malgré
  `store: false` (surveillance des abus), le lieu de traitement, l'éventuelle « conservation zéro ».

**Ce que NOUS gardons** (base Supabase, sans limite de durée aujourd'hui) :
- `app_ged_valeur` : les champs de 29 types (dates, montants, communes, numéros de mandat / ADEME, syndic, notaires...) ;
- des **PERSONNES** (nom, prénoms, qualité, page) pour 8 types : taxe foncière, offre, compromis, mandat, avenant, fin
  de mandat, acte, annulation ; le titre ajoute droits et quote-part ;
- **pièces des personnes** : identité (nature, nom, nom d'usage, prénoms, date et lieu de naissance, fin de validité),
  fiche de renseignements (adresse, date et lieu de naissance, situation de famille, régime matrimonial), financement et
  état civil (nature, date, noms) ;
- **à part** (`ged_prive.piece_identite`) : numéro, date et autorité de délivrance d'une pièce d'identité -- jamais à
  l'écran ;
- `app_agent_run` : le journal des appels (qui, quand, coût, nombre de valeurs) -- pas le contenu.

**Qui y accède** : tous les interrupteurs GED sont en « admin » (les 4 admins actifs). Le cran « on » ouvrirait aux
négociateurs, sur LEUR périmètre (les fonctions et lectures passent par `app_mes_biens_portefeuille`).

**Ce qui a déjà tourné** (au 18/11) : 88 appels (48 classements, 40 lectures), **0,037 $**, 2 utilisateurs ; 5 biens lus
dont **2 réels** (59541 : un avenant ; 62850 : un compromis) -- des noms réels sont donc déjà partis chez le fournisseur,
sous la décision du 12/11 (« je suis le seul à l'utiliser, on fera le DPA à la fin du dev »).

**⚠ DEUX MANQUES TROUVÉS, à trancher avec le dossier** :
1. **AUCUNE DURÉE DE CONSERVATION** : les lectures et valeurs restent tant que le classement existe ; supprimer le
   DOCUMENT ne les efface pas (vu le 18/11 : 31 documents supprimés, leurs lectures restent). Le registre des
   traitements et l'analyse d'impact exigent une durée.
2. **AUCUN CHEMIN D'EFFACEMENT pour une personne** : les noms lus sont du TEXTE, sans lien vers la fiche contact ;
   supprimer un contact n'efface pas ce que l'IA a lu de lui. Une demande d'effacement (droit des personnes) ne se
   servirait aujourd'hui qu'à la main.

**Le dossier à réunir** (rien rédigé) :
- **le contrat de sous-traitance (DPA) d'OpenAI** : il s'accepte en ligne par le titulaire du compte -- un geste de
  Frédéric, que je ne peux pas faire ; vérifier en même temps la conservation et le lieu de traitement ;
- **la fiche du registre des traitements** (« lecture des documents d'un dossier de vente par une IA ») ;
- **l'analyse d'impact** (pièces d'identité, données de personnes qui ne sont pas nos clients -- les acquéreurs --, IA
  d'un fournisseur hors UE à vérifier) ;
- **la mention d'information** au mandat (et pour les acquéreurs : au bon de visite ou à l'offre) ;
- **la durée de conservation** et **le chemin d'effacement** ci-dessus : deux décisions, puis peut-être du code.

### 12.38 AUDIT GRAPHIQUE et MAQUETTE de la GED (18/11, « avant ces derniers points, une optimisation du visuel »)

Frédéric met le dossier « cran on » (§12.37) en attente : d'abord le visuel. Audit d'expert écrit à part :
**`notice/AUDIT_GRAPHIQUE_GED_2026-11-18.md`** (écrans vus en production sur 62850 et 59541, inventaire exact du code,
10 constats, le parti pris, 5 points « à trancher » qui changeraient un comportement, le tableau anti-perte).
Maquette : **https://claude.ai/artifact/VxtNCjmAVXkThs641fHX1z** (4 écrans : l'onglet Documents au bureau, la fenêtre
de dépôt, « Ce que dit le compromis », le téléphone ; animations jouables). RIEN codé ; attend son avis.

### 12.39 AUDIT -- chaque type lu est-il comparé au registre, avec la fenêtre « Ce que dit… » ? (18/11, « audit, analyse et mesure », lecture seule, RIEN codé)

**La question de Frédéric** : « normalement, tous les types de documents sont lus en étape 2 et comparés au registre ;
une case vide qu'on peut compléter ou un conflit, on fait la même chose que compromis ou DPE ». **Réponse mesurée : NON,
pas encore.** La fenêtre est générique, mais seuls 8 types y entrent.

**Le catalogue (mesuré en base, `app_ged_type` actif)** : 68 types. **29 lus** (`lecture = 'lue'`), 34 classés sans
lecture, 5 jamais envoyés (RIB, clés, comptes, courrier, notes). En production : 40 lectures sur 21 des 29 types ; 8
types lus n'ont encore jamais été lus (fin de mandat, annulation, DDT, amiante, gaz, plomb, termites, arrêté de charges).

**Les quatre chemins qui existent (code)** :
- **la fenêtre « Ce que dit… »** (`BilanCompromis.tsx`, `gedBilanCompromis.ts`, `gedBilanFiche.ts`) : case vide =
  « à ajouter », valeur qui diffère = « à trancher » ; 7 genres ;
- **la carte « Remplir »** (`gedRemplir.ts` P3, `gedRemplirContact.ts` C1-C3) : case VIDE seulement, jamais un conflit ;
- **l'alerte « À regarder »** (`gedReglesLues.ts`, `gedReglesPersonnes.ts`, `gedReglesEtatCivil.ts`,
  `gedReglesFinancement.ts`) : on signale, on n'écrit rien ;
- **rien** : lu, montré dans la feuille, comparé à rien.

**A. Les 8 types qui suivent la règle (vide ou conflit -> la fenêtre)** :
- `transaction.avant_contrat` -> « Ce que dit le compromis » (la transaction) ;
- `transaction.offre` -> « Ce que dit l'offre » (la transaction) ;
- `diag.dpe` -> « Ce que dit le DPE » : consommation, émissions, date (`dpe_cons`, `dpe_ges`, `dpe_date`) ;
- `diag.erp` -> « Ce que dit l'état des risques » : sa date (`diag_risques_nat_tech_date`) ;
- `copro.carnet` (fiche synthétique) -> le nombre de lots (`copropriete_nb_lot`) ;
- `copro.appel_fonds` et `copro.arrete_charges` -> les charges annuelles du lot (`copropriete_quote_part`) ;
- `diag.surface` -> la Carrez (`SURF_CARREZ`).

**B. Exclus par DÉCISION écrite (ne pas relancer)** :
- `mandat.vente`, `mandat.avenant`, `mandat.fin` : décision ⑦-7 (« je ne souhaite pas pouvoir modifier un mandat ») --
  alertes L1, L4, L10, L12, L14, L18 ; seule la charge des honoraires, VIDE au registre, a sa carte « Remplir » (P3) ;
- `transaction.acte` : « acte de vente : laisse tomber » -- alerte L7 seule ;
- `justif.taxe` : exclu de « Remplir » le 13/11 (§12.18) parce que le groupe Hektor de `TAXE_FONCIERE` renvoie aussi le
  prix et les honoraires -- alertes T1 (vide = info, conflit = alerte) et T2.

**C. ⚠ LES TROUS : lus, une case du registre existe, et ni fenêtre ni carte** (la fiche porte ces cases :
`App.tsx` l. 1640-1735, étape 5 de l'assistant de saisie) :
- `diag.electricite`, `diag.gaz`, `diag.plomb`, `diag.termites`, `diag.amiante` : l'IA lit la date et le résultat ; la
  fiche a `diag_electrique` / `_date`, `diag_gaz` / `_date`, `diag_plomb` / `_date`, `diag_termites` / `_date`,
  `diag_amiante` / `_date`. Seule la validité est contrôlée (L2, une alerte) ; ⚠ l'amiante n'a même pas L2 ;
- `diag.assainissement` : date du contrôle et conformité lues ; la fiche a `diag_assainissement` / `_date` -- L2 seule
  (et seulement en non-collectif) ;
- `diag.surface` : la date du métré (`diag_loi_carrez_date`) et la surface habitable (`surfappart`) ne sont pas
  proposées -- seule la Carrez l'est ;
- `diag.dossier` (le DDT) : l'IA y lit les valeurs du DPE, mais la fenêtre et L6 ne regardent QUE `diag.dpe` -> un DPE
  arrivé dans un dossier de diagnostics n'est jamais comparé ;
- `copro.carnet`, `copro.appel_fonds`, `copro.pv_ag` : le syndic (`syndic`), le fonds de travaux
  (`montant_fonds_travaux`), le plan de sauvegarde (`copropriete_plan_sauvegarde`) et la procédure
  (`copropriete_statut_syndicat`) sont lus ; seule la procédure sonne (L17, une alerte), rien ne se propose ;
- `copro.reglement` : le nombre de lots est lu, mais seule la fiche synthétique alimente `copropriete_nb_lot`.
⭐ **Mesuré en base : ce ne sont pas des champs théoriques.** Les lectures réelles portent, à l'état « lu » : la date
et le résultat de l'électricité (1), la date et la conformité de l'assainissement (1), le syndic (5 lectures), le fonds
de travaux (4), le plan de sauvegarde et la procédure (2), les classes et le diagnostiqueur du DPE (3), le nombre de
lots du règlement (1).

**D. Les personnes : la règle n'est suivie qu'à MOITIÉ** -- `justif.identite`, `transaction.renseignements`,
`justif.etat_civil` : une case VIDE du contact (naissance, lieu, situation de famille) a sa carte « Remplir » (C1-C3,
une personne seule) ; un CONFLIT (le nom, P4) n'est qu'une alerte. ⛔ Garde-fous écrits : jamais le régime matrimonial,
ni l'adresse ; pas les couples. `transaction.financement` : rien à écrire (jamais un montant, un taux, une banque) --
alertes P7, P8 seules, c'est voulu.

**E. Sans case à corriger, et c'est normal** : `justif.titre` (L11 : les propriétaires parmi les mandants ; la contenance
lue n'est pas comparée au terrain -- non tranché), `transaction.annulation` (L19), `facture.honoraires` (L8, L9 -- la
facture face aux honoraires de la vente au registre : écrire ces honoraires est une autre affaire, non tranché).

**Ce qui n'est PAS mesuré** : le taux de remplissage de ces cases sur le parc (le détail de la fiche n'est pas dans une
table lisible en SQL, `rawWizardDetailField` le lit dans la charge Hektor) ; si chaque case de C passe par le geste
existant `editAnnonceOptimistic` sans effet de bord sur son groupe Hektor (le piège de la taxe foncière, §12.18, et celui
du secteur qui remet la copropriété à zéro) -- **à éprouver case par case avant de les ouvrir**.

**Ce qu'il faudrait pour suivre la règle partout** (à décider par Frédéric, rien codé) : ajouter à `gedBilanFiche.ts` les
genres de C -- les 5 rapports (date + résultat), l'assainissement, la date du métré et la surface habitable, le DDT dans le
DPE, le syndic / fonds de travaux / plan de sauvegarde / procédure, le nombre de lots du règlement -- même modèle de ligne,
même fenêtre, même écriture ; et dire si les conflits du contact (D) doivent avoir leur fenêtre.

### 12.40 DÉCISIONS DE FRÉDÉRIC et AUDIT DES COUPLES (18/11, « rajoute titre de propriété / taxe foncière / charges, il faut aussi auditer pour trouver une solution à contact en couple et la date de naissance », lecture seule, RIEN codé)

**La règle, dans ses mots** : « chaque document a son "Ce que dit…" comme le compromis et le DPE, sauf si inutile ».

**Décisions du 18/11** (en plus des 10 types « la case existe » du §12.39) :
- **Titre de propriété** : sa fenêtre (contenance face à la surface du terrain `surfterrain`).
- **Taxe foncière** : sa fenêtre, `TAXE_FONCIERE`. ⛔ L'exclusion du 13/11 (§12.18) est LEVÉE par Frédéric. Mesure du 18/11 :
  le groupe Hektor `mandat_infofi` est DÉJÀ écrit en modification -- 21 travaux `update_hektor_annonce_fields` done, 0 erreur,
  0 refus « Credential Error » (le prix) ; et l'écran de modification laisse déjà saisir la taxe à la main (App.tsx l. 1731).
  ⚠ Mais la taxe ELLE-MÊME n'a JAMAIS été écrite en modification (0 travail ; 38 fois à la création seulement) :
  épreuve aller-retour sur 63331 AVANT d'ouvrir.
- **Charges** : sa ligne, `CHARGES` = « Charges copro / MOIS » (App.tsx l. 1732), depuis l'appel de fonds (annuel / 12).
  Même groupe que la taxe, même épreuve (2 travaux de modification avec charges, done).
- **Inutiles ou interdits** (pas de fenêtre) : mandat, avenant, fin (⑦-7) ; acte de vente (« laisse tomber ») ; plan de
  financement (rien à écrire, par dessein) ; annulation (un statut, par la modale visible).
- **Encore à trancher** : livret de famille / acte de mariage -> situation de famille ; facture d'honoraires -> honoraires de
  la transaction ; syndic (texte libre) ; fonds de travaux (solde ou cotisation ?) ; adresse et régime (garde du 14/11).

**⚠ Correction du §12.39** : « le taux de remplissage des cases n'est pas mesurable en SQL » est FAUX. La fiche brute est en base
(`app_dossier_detail_current.detail_payload_json -> detail_raw_json`, chaîne JSON à décoder, groupes `->'props'->case->'value'`),
comme au §12.17. Ma requête sur tout le parc a dépassé le délai : à refaire découpée.

**AUDIT -- le contact en couple et sa date de naissance** (objet CONTACT seul ; annonce, recherche, relation, transaction,
mandat, document, RDV non touchés) :
- **Chez Hektor, la case EXISTE.** Le formulaire de modification d'un couple (groupe `mefContacts/contactCoupleAll`, 54 champs,
  mesuré le 02/11 sur 606104, SYNTHESE_CHANTIER_CONTACTS_COUPLES §27) porte `dateNaissance_m2` et `lieuNaissance_m2` ; les
  captures de création du 01/06 aussi (`Console/exports/contact_owner_status_success_…/proprietaire_couple_filled.html`). La
  situation de famille (`marital_status`) n'existe qu'UNE fois pour le couple : pas de `_m2`, et c'est juste.
- **Le chemin d'écriture EXISTE et est prouvé** : « modifier le conjoint par la première fiche » (pièce E, §27-28) --
  `app_edit_conjoint_optimistic` (chez nous à l'instant, sur la fiche du conjoint) -> worker `updateHektorContactIdentity`
  (relit `contactCoupleAll`, renvoie le bloc `_m2`) -> relecture de la seconde fiche. Prouvé sur le prénom : la seconde fiche
  Hektor (606105) SUIT.
- **Ce qui MANQUE (trois trous, mesurés dans le code)** :
  (1) le worker ne connaît pas la naissance du conjoint : `normalizeHektorContactPayload` (l. ~19511) lit nom, prénom, e-mail,
      téléphone, adresse du conjoint, PAS sa naissance ; `applyHektorContactIdentityValues` (l. ~19735-19760) n'écrit que
      `dateNaissance` / `lieuNaissance` de la première personne ;
  (2) la base : `app_edit_conjoint_optimistic` (patch_couple_phase3e…, l. 54-57) ne pose que nom, prénom, e-mail, téléphone
      sur la fiche du conjoint, pas `birth_date` / `birth_place` ;
  (3) l'écran : `gedRemplirContact.ts` ne propose qu'à une PERSONNE SEULE (`personneSeule`).
- ⭐ **La première personne d'un couple** n'a besoin QUE du (3) : le worker écrit déjà `dateNaissance` dans le formulaire relu,
  quel que soit son groupe (à confirmer à l'épreuve : la case doit être dans `contactCoupleAll`).
- **Mesure (app_contact_current, 18/11)** : 8 790 premières fiches de couple, dont 25 avec date de naissance ; 397 conjoints
  NOMMÉS, dont 3 avec date ; 5 014 conjoints SANS PRÉNOM ; 15 127 cases de conjoint vides. Personnes seules : 63 800, dont 240
  avec date. ⭐ `birth_date`, `birth_place`, `marital_status` sont des champs « à nous » (`contrat_autorite.py:63`) : la nuit
  ne les écrase pas.
- **LA SOLUTION PROPOSÉE (à valider, rien codé)** -- passer par la première fiche, le chemin prouvé :
  a. worker : `spouse_birth_date` / `spouse_birth_place` -> `dateNaissance_m2` / `lieuNaissance_m2`, seulement si le formulaire
     relu est celui d'un couple ;
  b. base : `app_edit_conjoint_optimistic` accepte ces deux clés et les pose sur la fiche du conjoint (patch + inverse +
     répétition) ;
  c. écran : la proposition C1/C2 s'ouvre aux couples -- la personne lue est rattachée à la PREMIÈRE ou au CONJOINT (nom ET
     prénom stricts, comme 9c) ; la première par `editContactOptimistic`, le conjoint par le geste « modifier le conjoint » ;
     C3 (situation de famille) une seule fois pour le couple ;
  d. épreuve sur le couple fictif 20000031/32 <-> 606104/05 (gardé pour ça), avec des pièces SPÉCIMEN : la date doit arriver
     sur `dateNaissance_m2` de 606104 ET sur la fiche 606105.
- **Non mesuré** : que Hektor recopie `dateNaissance_m2` sur la seconde fiche (prouvé pour le prénom seulement) ; le conjoint
  SANS prénom (5 014) ne peut pas se rattacher strictement -- le compléter (pièce F) serait un autre geste, pas décidé ;
  écrire DIRECTEMENT la seconde fiche par son propre numéro (formulaire non relu, écarté).

**DÉCISION DE FRÉDÉRIC (18/11, sur la solution des couples)** : « pas nécessaire de l'envoyer à Hektor, on garde chez nous,
protégé ». ⭐ Conforme au contrat du projet : `contrat_autorite.py:63` -- « Hektor ne renvoie JAMAIS ces trois-là : seule l'app
les écrit » (`birth_date`, `birth_place`, `marital_status`), et `push_contacts_to_supabase.py` (l. 728-743, 1118) les PRÉSERVE
à chaque passage, la nuit comme la relecture immédiate (`refresh_contact_inproc.py` passe par lui). Conséquences sur la
solution : la pièce (a) du worker TOMBE ; la pièce (b) devient un geste CHEZ NOUS SEULEMENT (aucun travail Hektor), qui
n'existe pas encore (aucune fonction de base n'écrit la naissance sans envoi : vérifié dans supabase/*.sql) ; l'épreuve chez
Hektor (606104/05) n'est plus nécessaire, une épreuve en base suffit. ⬜ À trancher : la même règle pour les personnes seules
(9c envoie AUJOURD'HUI la fiche entière chez Hektor par `editContactOptimistic`) ; qui peut LIRE ces dates (non mesuré).

**VÉRIFIÉ (18/11, « je crois qu'on n'envoie jamais la date de naissance, vérifie »)** : ON L'ENVOIE, quand elle est saisie.
Le worker met `dateNaissance` / `lieuNaissance` dans le formulaire Hektor (`console_job_worker.js` l. 19759-19760, création
l. 20538 et 20714). En base, 14 travaux done portent une date envoyée : 7 `create_hektor_contact`, 7 `update_hektor_contact`,
du 24/06 au 16/11 -- TOUS des contacts d'essai (ESSAI 8A, 8 R3, TROIS, QUATRE, CINQ, ESSAI CONTACT ; FERANCK 604020 en
juin, essai probable, non prouvé), et le compte rendu du worker porte `date_naissance` dans les 14. Ce qui est vrai : Hektor
ne la RENVOIE jamais (contrat_autorite.py:63) -- le sens Hektor -> nous. Donc aujourd'hui : envoyée à l'aller, jamais
relue ; et en pratique jamais envoyée pour un vrai contact, parce que personne ne la saisit (240 personnes seules sur 63 800).

**DÉCISION DE FRÉDÉRIC, REVUE (18/11)** : « on va plutôt envoyer à Hektor aussi pour le conjoint, au moins ce sera la même
règle pour les contacts ; cela devrait fonctionner mais il faudra tester ». ➡ La décision « chez nous seulement » est
REMPLACÉE : la solution d'origine (a, b, c, d) revient ENTIÈRE -- worker, base, écran, épreuve sur le couple fictif.

### 12.41 LE PLAN -- un « Ce que dit… » pour chaque document utile (18/11, proposé, RIEN codé, attend le « vas-y »)

**Mesure des groupes Hektor écrits en MODIFICATION** (`update_hektor_annonce_fields` done, toutes dates) : `ag_interieur` 40,
`mandat_infofi` 21, `copropriete` 13, `secteur` 13, `diagnostiques` 11, `terrain` **1**. Aller-retour prouvé depuis la GED :
`diagnostiques` (dpe_date, date de l'ERP) et `copropriete` (lots, quote-part), 13/11 sur 63331.

Une tâche de code à la fois ; chaque lot : essais hors ligne + banc d'écran + build, puis épreuve réelle sur 63331 si un
champ neuf part chez Hektor ; retour arrière = l'interrupteur `ged_remplir` (off), le commit, ou le patch inverse (lot G).
**Un seul chemin par case** (règle du lot 3) : quand une fenêtre prend une case, l'alerte ou la carte « Remplir » du même
sujet se retire.
- **A -- les 6 diagnostics et le DDT** (écran seul, `gedBilanFiche.ts`) : électricité, gaz, plomb, termites, amiante,
  assainissement -> `diag_…` = OUI et `diag_…_date` ; le DDT -> les cases du DPE. Groupe `diagnostiques` (prouvé). Épreuve :
  un `diag_…` (jamais écrit en modification) aller-retour sur 63331. Casse possible : rien hors de la fenêtre ; L2 (validité)
  reste une alerte.
- **B -- copropriété** : plan de sauvegarde et procédure (fiche synthétique, PV d'AG) -> `copropriete_plan_sauvegarde`,
  `copropriete_statut_syndicat`. Groupe `copropriete` (garde du worker contre le secteur active). L17 se retire au profit de
  la fenêtre. Épreuve des deux cases.
- **C -- taxe foncière et charges** : `justif.taxe` -> `TAXE_FONCIERE` ; appel de fonds -> `CHARGES` (annuel / 12, « charges
  copro / mois »). Groupe `mandat_infofi` (renvoie prix et honoraires RELUS). ⛔ ÉPREUVE D'ABORD : la taxe n'a jamais été écrite
  en modification -> aller-retour sur 63331, prix et honoraires relus identiques avant d'ouvrir. T1 se retire.
- **D -- le métré complet** : surface habitable `surfappart` et date `diag_loi_carrez_date`. Groupe `ag_interieur` (40 écrits,
  mais jamais depuis la GED ; il renvoie 13 champs) : épreuve.
- **E -- le titre de propriété** : contenance -> `surfterrain` (groupe `terrain` : 1 seule écriture connue) : épreuve.
- **F -- les pièces des personnes dans la fenêtre** : « Ce que dit la carte d'identité / la fiche de renseignements » --
  naissance, lieu, situation de famille (renseignements) ; vide -> ajouter, différent -> trancher (on n'écrit par-dessus que
  sur le choix de l'humain). Personne seule et PREMIÈRE personne d'un couple par `editContactOptimistic`. Les cartes C1-C3
  se retirent. P4 (le nom) reste une alerte.
- **G -- le conjoint** : worker `spouse_birth_date` / `spouse_birth_place` -> `dateNaissance_m2` / `lieuNaissance_m2` (formulaire
  de couple relu seulement) ; base : `app_edit_conjoint_optimistic` accepte ces clés (patch + inverse + répétition) ; écran :
  la personne lue rattachée au conjoint (nom ET prénom). Épreuve sur 20000031/32 <-> 606104/05 avec des pièces SPÉCIMEN : la
  date doit arriver sur 606104 (`_m2`) ET sur 606105. ⏰ Redémarrer les 4 services worker, file vide (0 pending, 0 running).
**Hors plan, à trancher** : livret de famille / acte de mariage, facture d'honoraires, syndic, fonds de travaux, règlement de
copropriété, adresse et régime, conjoints sans prénom (5 014).

**⛔ CORRECTION (18/11, Frédéric : « non tu te trompes … la doublure, le chantier autonomie ») -- j'avais écrit que la fiche
du bien est « remplacée par ce que Hektor rend » à la relecture et la nuit. FAUX.** Une modification de l'app est protégée
(chantier ⑧, `CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md`, tableau « Clôturer 8a ») : calque chez nous au clic ; **L3** --
`app_annonce_reappliquer_saisies` repose nos saisies en attente après chaque relecture ; un champ que Hektor refuse ->
`partial`, l'attente GARDÉE, sentinelle `data.annonce_partielle` ; au retour, **8a7** compare l'envoyé au revenu
(`annonce_retour_controle` on, sentinelle `data.annonce_modif_ecart`). `CHAMPS_APP_ANNONCE` vide = l'ANCIEN mécanisme,
remplacé (même erreur que le 29/10, `AUDIT_CLASSE_C_…`). ➡ Pour le plan : l'« épreuve » de chaque lot ne PROTÈGE rien, elle
ne fait que VÉRIFIER (Hektor prend-il la case, laisse-t-il intact le reste de son groupe) ; un refus ou un écart se voit de
toute façon. Elle devient le PREMIER usage réel sur 63331, lu par le contrôle au retour -- plus une étape à part.

### 12.42 LE LOT A -- les six diagnostics et le DDT ont leur « Ce que dit… » (18/11, « Oui, lot A ») -- ÉCRIT, rien poussé

**Mesure avant d'écrire** (4 000 fiches, `detail_raw_json`, lecture seule) : les cases `diag_electrique`, `diag_gaz`,
`diag_plomb`, `diag_termites`, `diag_amiante`, `diag_assainissement` sont VIDES à ~99,5 % ; quand elles sont remplies,
**OUI vient avec sa date et son commentaire** (amiante 11/14, électricité 9/11, plomb 4/6), **NON presque jamais** (1 sur 37)
-> la case dit « diagnostic fait », pas le résultat.
**Fait (écran seul, aucun geste neuf)** :
- `lib/gedBilanFiche.ts` : chaque rapport (`diag.electricite`, `diag.gaz`, `diag.plomb`, `diag.termites`, `diag.amiante`,
  `diag.assainissement`) a SA fenêtre -- « … réalisé » (OUI ; fiche vide -> ajouter, NON -> trancher) et sa date
  (`diag_…_date` ; l'assainissement prend la date du CONTRÔLE). Le résultat lu (anomalies, présence, conformité) est DIT
  en note, jamais écrit : il n'a pas de case chez Hektor.
- Le **DDT** a UNE fenêtre (« Ce que dit le dossier de diagnostics ») : ses valeurs `dpe_*` ET chaque diagnostic de sa liste
  (date du rapport, page, conclusion). ⛔ **Un seul chemin par case** : pour chaque case, le document le plus RÉCENT parle
  (un document daté passe devant un non daté ; à date égale, le rapport seul) -- un DDT récent prend le DPE et les
  diagnostics qu'il contient, un DDT ancien ne garde que ceux qu'il est seul à dire.
- `gedBilanCompromis.ts` (7 genres neufs), `BilanCompromis.tsx` (leurs mots), `RecuManque.tsx` (aucune ligne « À regarder »
  liée : L2 parle de validité), `gedRemplir.ts` (`diagnostics` dans les faits), `App.tsx` `faitsGedDuBien` (les six cases et
  leurs dates, brutes). L'écriture est celle du lot 3 (`appliquerBilanFiche` : fiche relue, témoin, UN
  `editAnnonceOptimistic`) -- les cases partent par le groupe `diagnostiques` du worker, qui les porte déjà toutes
  (`HEKTOR_WIZARD_UPDATE_GROUPS`).
**Contrôles** : `test_ged_bilan` **102 VERT** (16 neufs, section ⑧) ; témoins inverses -- « le plus récent ne parle plus » ->
1 ROUGE, « NON tenu pour d'accord » -> 1 ROUGE ; voisins verts (remplir 38, remplir contact 48, règles lues 95, règles 44,
Reçu/Manque 29, lecture 62, personnes 38) ; `npm run build` vert. **Banc d'écran** (`scratchpad/banc_lotA`, lancement
« ged-banc-lotA ») : « Ce que dit le dossier de diagnostics » -- à trancher 3 (consommation 250 / 180, date du DPE, électricité
Oui / Non avec « résultat lu : anomalies sans danger »), à ajouter 1, d'accord 3 ; « Ce que dit le diagnostic gaz » -- 2 à
ajouter ; « Enregistrer » rend les bons champs ; console sans erreur.
⏳ **Reste** : pousser (Vercel) ; premier usage réel sur 63331 -- un `diag_…` n'a jamais été écrit en modification : le
contrôle au retour (8a7) dira si Hektor le prend et garde le reste du groupe `diagnostiques`.
**Poussé le 18/11** (`e4d7f99`, Vercel prêt). **Premier usage réel (18/11, 18:23)** : les 30 documents d'essai de 63331 avaient
été SUPPRIMÉS le matin (10:23, depuis l'app, en lot ; le classement GED reste, sans fichier) -> le rapport électricité FICTIF
redéposé par l'écran, lu, la fenêtre s'ouvre seule : date à trancher (03/02/2026 lu / 10/09/2026 fiche), « réalisé » d'accord
avec « résultat lu : anomalies ». « Enregistrer » : la fiche porte 03/02/2026 à l'instant ; calque `app_annonce_pending` =
`{diag_electrique_date: 2026-02-03}` seul, envoi à +10 min. Photo du groupe `diagnostiques` AVANT (37 cases) gardée pour le
contrôle au retour (`scratchpad/lotA_63331_avant.json`).
✅ **PROUVÉ AU RETOUR (18:34-18:35)** : travail `update_hektor_annonce_fields` done -- groupe `diagnostiques`, champs
`[diag_electrique_date]`, 0 écarté, Hektor « mise à jour effectuée » ; relecture done ; calque soldé (0 en attente) ; groupe
APRÈS : 37 cases, UNE seule a bougé (`diag_electrique_date` 2026-09-10 -> 2026-02-03), les 36 autres identiques. ➡ **Un `diag_…`
s'écrit en modification, et Hektor garde le reste du groupe.**

**DÉCISION DE FRÉDÉRIC (18/11, 19:20)** : « peux-tu être plus autonome jusqu'au point G, à l'aide de tests et contrôles, et aller
jusqu'à G sauf problème » -> les lots B à G s'enchaînent sans « vas-y » par lot ; chacun : essais, témoins inverses, build,
commit, puis premier usage réel sur les biens et contacts d'essai ; arrêt sur un problème.

### 12.43 LE LOT B -- la procédure du syndicat et le plan de sauvegarde (18/11) -- ÉCRIT

**Mesure avant d'écrire** : les VRAIS codes Hektor (formulaire `copropriete`, boutons radio, export de 62649) -- statut du
syndicat `ALERTE` « soumis à une procédure d'alerte », `REDRESSEMENT`, `PROCESS` « procédure en cours », `NOTPROCESS` « pas de
procédure en cours » ; plan de sauvegarde `OUI` / `NON`. Sur 6 000 fiches : `NOTPROCESS` 47, `PROCESS` 24, `ALERTE` 1 ; plan
`NON` 20, `OUI` 1. ⚠ **Trouvé en passant, PAS corrigé** : l'écran de saisie (`wizardProcedureOptions`, App.tsx ~l. 1421) et le
remplissage par le scan (App.tsx ~l. 11808) proposent `PAS_DE_PROCEDURE` / `PROCEDURE_EN_COURS`, qui ne sont PAS des valeurs
Hektor (radio : le worker ne traduit que les `<select>`) -- mesure : AUCUNE fiche ne porte ces codes ; à regarder à part.
**Fait** (`gedBilanFiche.ts`) : la fiche synthétique (« aucune » -> `NOTPROCESS`, mandataire ad hoc -> `ALERTE`, administration
provisoire -> `REDRESSEMENT`, autre -> `PROCESS` ; plan oui/non) et le PV d'AG le plus récent qui NOMME une procédure (jamais
une convocation ; ⛔ un PV ne prouve pas l'absence) ; par case, le plus récent des deux parle. Les lignes de la fiche synthétique
rejoignent SA fenêtre (`copro_lots`) ; le PV a la sienne (`copro_ag`, « Ce que dit le procès-verbal d'assemblée générale »).
Seulement sur un bien marqué copropriété. Les anciens codes de l'écran valent leurs équivalents ; le témoin garde la case telle
quelle. **L17** : comme L16 au lot 3, elle RESTE dans « À regarder » et reçoit sa note Vrai / Faux du choix (lignes liées
`regle: 'L17'` quand le document dit une procédure ou un plan) -- « se retire » du plan §12.41 lu ainsi, pour ne pas changer
les comptes de « À regarder ».
**Contrôles** : `test_ged_bilan` **113 VERT** (11 neufs, section ⑨) ; témoins inverses -- « le PV plus récent ne parle plus »,
« une convocation parle », « mandataire ad hoc = procédure en cours » -> 1 ROUGE chacun ; voisins verts (remplir 38, remplir
contact 48, règles lues 95, règles 44, Reçu/Manque 29, lecture 62) ; `npm run build` vert. Commit `a67c371`.

### 12.44 LE LOT C -- la taxe foncière et les charges au mois (18/11) -- ÉCRIT

**Fait** (`gedBilanFiche.ts`) : l'avis de taxe le plus récent (par année d'imposition, comme T1) a SA fenêtre (`taxe`, « Ce que dit
l'avis de taxe foncière ») -> `TAXE_FONCIERE` (± 5 €, l'année en note, liée à T1 hors accord) ; ⛔ un avis qui porte PLUSIEURS
biens ne se propose pas. L'appel de fonds ajoute à SA fenêtre (`copro_charges`) la charge AU MOIS -> `CHARGES` (« Charges copro /
mois »), l'annuel / 12 arrondi à l'euro, tolérance de l'année / 12 (± 10 €, 10 %), liée à L16. Une case à 0 est vide : c'est
`lireNombre` qui le fait déjà (le témoin inverse d'une garde en double est resté vert -> garde retirée). T1 RESTE une ligne de
« À regarder » et prend sa note du choix (comme L16, L17) ; T2 (un avis ancien) reste à part. Groupe Hektor `mandat_infofi`
(renvoie prix et honoraires relus). ⏳ **Épreuve réelle** : la taxe n'a jamais été écrite en modification -> premier usage sur
63331 (fiche : taxe 900, charges 150 ; l'avis FICTIF dit 1 234 € -> à trancher), prix (139 000) et net vendeur (130 000) relus
identiques au retour.
**Contrôles** : `test_ged_bilan` **122 VERT** (9 neufs, section ⑩) ; témoins inverses -- « un avis de plusieurs biens se
propose » -> 1 ROUGE, « les charges au mois = l'année » -> 2 ROUGE ; `npm run build` vert. Commit `98515c4`.

### 12.45 LES LOTS D et E -- le métré complet ; le titre de propriété -> le terrain (18/11) -- ÉCRITS

**Mesure** (6 000 fiches) : `surfappart` rempli 4 619, dont **233 à décimale « . »** (130.6, 69.45…) -> Hektor accepte les
décimales ; `SURF_CARREZ` 178 (35 décimales) ; `diag_loi_carrez` OUI 7 (5 avec date), NON jamais ; `surfterrain` 2 497, entiers
sauf 1.
**D -- fait** : la fenêtre du métré (`surface`) garde la Carrez à sens unique (L15) et ajoute : « mesurage Carrez réalisé = OUI »
(`diag_loi_carrez`) et sa date (`diag_loi_carrez_date` = date du mesurage) -- seulement quand une surface Carrez est lue, comme
les rapports du lot A ; la **surface habitable** mesurée -> `surfappart` (deux décimales « . »), dans les DEUX sens, ± 1 m² ou
2 %, sans règle liée (aucune règle de « À regarder » ne la compare). Un métré sans Carrez (une maison) : la surface habitable
seule. La fenêtre s'ouvre désormais dès qu'une surface est lue (avant : seulement avec une Carrez).
**E -- fait** : le titre de propriété le plus récent (`date_acte`) a SA fenêtre (`titre`, « Ce que dit le titre de propriété »)
-> sa contenance dans `surfterrain` (± 1 m², note « contenance cadastrale du titre »). ⛔ **Seulement sur un bien
EXPLICITEMENT hors copropriété (`copropriete = NON`) et un titre qui ne cite aucun lot** : la contenance d'un immeuble en
copropriété n'est pas le terrain d'un appartement ; un bien « non dit » ne se propose pas.
**Contrôles** : `test_ged_bilan` **133 VERT** (11 neufs, sections ⑪ ⑫ ; l'essai du lot A mis à jour : sept cases lues, avec
`diag_loi_carrez`) ; témoins inverses -- titre sur un bien en copropriété, titre avec lots, le titre le plus ancien parle,
surface habitable sans tolérance -> 1 ROUGE chacun ; voisins verts ; `npm run build` vert.
⏳ **Épreuves réelles** : `surfappart` (groupe `ag_interieur`, jamais depuis la GED) et `surfterrain` (groupe `terrain`, UNE
écriture connue) -- sur 63331 (appartement, copropriété OUI : le titre ne s'y propose PAS, par construction) le métré seul ;
le terrain demande un bien d'essai hors copropriété. Commit `273c5de`.

### 12.46 LE LOT F -- « Ce que dit la pièce d'identité / la fiche de renseignements » (18/11) -- ÉCRIT

**Audit avant d'écrire** (objet CONTACT, geste modifier) : (1) le worker (`updateHektorContactIdentity`) RELIT le formulaire
Hektor -- « un couple chez Hektor est édité comme un couple (bloc `_m2`), quoi que dise l'envoi » -- et n'écrit le bloc du
conjoint que s'il est ENVOYÉ : modifier la naissance de la première personne laisse le conjoint intact ; (2) la fonction de base
`app_edit_contact_optimistic` ne touche pas à la nature de la fiche, elle pose seulement les cases envoyées (dont `birth_date`,
`birth_place`, `marital_status`) ; (3) **mesure** des premières fiches de couple actives (6 597) : **3 104 au prénom fusionné**
(« Annette et Patrick ») et **640 au nom fusionné** (« DUPONT/ MARTIN ») -- leur premier prénom ne dit pas QUI est la première
personne chez Hektor ; (4) chez nous, dates ISO (268) et situation en codes Hektor (married 43, single 29, widower 15, divorced 8,
civil_union 3) ; (5) le couple d'essai 20000031/32 <-> 606104/05 n'est PLUS dans les contacts (sa suppression était prévue après
les essais du 02/11).
**Fait** :
- `gedRemplirContact.ts` -- `bilansPersonnes` : UNE fenêtre par document lu (`identite`, `renseignements`) ; ses lignes, pour
  chaque personne du bien qu'il nomme (nom ET premier prénom stricts, une seule personne du bien qui les porte, comme 9c) : date
  et lieu de naissance, et (fiche de renseignements seulement) la situation de famille en code Hektor. Vide -> à ajouter ;
  différent -> à trancher ; égal -> d'accord. **Personne seule et PREMIÈRE personne d'un couple** ; ⛔ une première au nom ou au
  prénom fusionné ne se propose pas. ⛔ Un seul chemin par case : la naissance vient de la pièce d'identité la plus récemment lue
  (les autres pièces de la personne d'accord, sinon aucune ne parle) ; la fiche de renseignements n'en parle que si aucune pièce
  d'identité ne nomme la personne. Jamais l'adresse, le régime, ni le numéro / la délivrance / l'autorité (ged_prive).
- `RecuManque.tsx` : les fenêtres des personnes rejoignent les autres ; **les cartes C1-C3 sont RETIRÉES** (la fonction
  `propositionsContact` reste, testée, sans appelant) ; la fenêtre ouverte se repère par son genre ET sa lecture (deux pièces
  d'identité = deux fenêtres ; avant, une seule fenêtre par genre).
- `App.tsx` : `contactsGedDuBien` donne chaque MEMBRE d'un couple fusionné à l'écran (la « principale » de l'écran n'est pas
  forcément la première chez Hektor : on lit la nature de CHAQUE fiche) ; `appliquerBilanPersonne` -- par contact : relu
  (actif, personne seule ou première, jamais un conjoint), témoin case par case, UN `editContactOptimistic` (nom actuel joint,
  e-mail RGPD coupé, rien d'autre envoyé), décision notée après l'écriture.
- `gedBilanCompromis.ts` (`GenrePersonne`, `estGenrePersonne` ; l'aiguillage passe AVANT celui de la fiche), `BilanCompromis.tsx`
  (« La fiche du contact »).
**Contrôles** : `test_ged_remplir_contact` **66 VERT** (18 neufs, section ⑥ ; l'essai qui vérifiait le branchement des cartes C
vérifie leur retrait) ; témoins inverses -- première fusionnée proposée, la fiche parle malgré la CNI, deux pièces
contradictoires, le conjoint proposé -> rouges ; les 13 fichiers d'essais GED verts ; `npm run build` vert.
⚠ **Limite** : l'état civil n'est relu que pour celui qui peut remplir (comme avant) -- les autres ne voient pas ces fenêtres.
⏳ **Épreuve réelle** : une pièce SPÉCIMEN sur une personne seule d'essai, puis sur la première d'un couple d'essai (à recréer).
Commit `580eff5`.

### 12.47 LE LOT G -- la naissance du CONJOINT, chez nous ET chez Hektor (18/11) -- ÉCRIT, patch POSÉ, worker PAS redémarré

**Audit avant d'écrire** : (1) l'attente d'un contact (`app_contact_enqueue_due_pushes`) passe TOUTE la saisie au worker (aucune
liste blanche) ; (2) le contrôle au retour des contacts (8a5, `app_contact_champs_modif`) ne compare QUE nom, coordonnées et
commentaire -- il ne criera pas sur la naissance, mais ne la contrôlera pas non plus (Hektor ne renvoie jamais les dates de
naissance, `contrat_autorite.py:63`) ; (3) 329 conjoints « nature ET rôle conjoint », TOUS nommés par leur principale ; 45 autres
« conjoint » sans rôle, 3 seulement liés -> écartés.
**Fait** :
- **worker** (`console_job_worker.js`) : `normalizeHektorContactPayload` lit `spouse_birth_date` / `spouse_birth_place` (jamais une
  valeur vide) ; `applyHektorContactIdentityValues` les pose dans `dateNaissance_m2` / `lieuNaissance_m2` -- seulement dans le
  bloc d'un COUPLE, et seulement si le formulaire RELU porte la case ; le compte rendu les dit. Essai pur
  `Console/test_couple_naissance_conjoint.js` **11 OK** (extrait les vraies fonctions, sans réseau) ; témoins inverses -- sans la
  garde du formulaire relu, une valeur vide part, la naissance écrase celle de la première -> en échec ; voisin
  `test_couple_modification.js` vert.
- **base** : `supabase/patch_ged_lotG_naissance_conjoint_2026-11-18.sql` (+ `_INVERSE`, `_REPETITION`) --
  `app_edit_conjoint_optimistic` pose `birth_date` / `birth_place` sur la fiche du conjoint ; ⛔ une naissance SEULE sur une case
  de conjoint « vide » ne nomme personne -> refus `naissance_sans_conjoint_nomme`. **Répétition (rien ne reste)** sur un VRAI couple
  (10335289 / 10335292) : 01 ok · 02 conjoint=ok · 03 principale=ok · 04 vide=ok · 05 seule=ok · 06 anon=ok · 07 l'ancien envoi
  marche toujours=ok · 08 l'inverse rend l'empreinte d'origine=ok ; vérifié après : empreinte `e5ac0baa…` et fiche intactes.
  ✅ **POSÉ en production le 18/11 à ~19:00** (Frédéric : « allez jusqu'à G ») : empreinte `8bc3ff858ec29401c11b9e726de44ed5`,
  `anon` non, `authenticated` oui.
- **écran** : `api.ts` (`spouseBirthDate` / `spouseBirthPlace` -> `spouse_birth_*` ; le geste du conjoint porte `birthDate` /
  `birthPlace` et rend `raison`), `ged.ts` (l'état civil relu porte `hektor_couple_contact_id`), `gedRemplirContact.ts` (le
  conjoint « nature ET rôle » se propose : naissance seulement, ⛔ jamais la situation de famille -- une seule par couple),
  `RecuManque.tsx` (`conjointDe`), `App.tsx` (`appliquerBilanPersonne` : relit le conjoint ET sa principale ; CHEZ NOUS d'abord
  par `editConjointOptimistic` -- s'il refuse, RIEN ne part chez Hektor -- puis la principale par `editContactOptimistic` avec la
  seule naissance du conjoint et son nom actuel). `test_ged_remplir_contact` **74 VERT** (8 neufs, section ⑦) ; témoins inverses
  rouges ; les essais GED verts ; `npm run build` vert.
⛔ **PAS FAIT -- le redémarrage des 4 services worker** : tenté par moi à 19:00, file vide, REFUSÉ par Windows (droits) -- et la
mémoire le dit : c'est Frédéric qui redémarre. Rien n'est cassé (les services tournent sur l'ancien code). ⚠ **ORDRE OBLIGATOIRE** :
redémarrer AVANT de pousser l'écran -- sinon un envoi `spouse_birth_*` serait « fait » par l'ancien worker sans rien écrire chez
Hektor (clé ignorée, en silence). Commande (PowerShell admin, file vide) :
`Restart-Service HektorConsoleWorkerAdmin,HektorConsoleWorkerActions,HektorConsoleWorkerDocuments,HektorConsoleWorkerSyncLight -Force`
puis comparer `CreationDate` des 4 `node.exe` à l'heure du fichier.
⏳ **Épreuve réelle** : un couple FICTIF à recréer (20000031/32 n'existe plus) et une pièce SPÉCIMEN du conjoint : la date doit
arriver sur `dateNaissance_m2` de la principale chez Hektor ET sur la fiche du conjoint chez nous.
✅ **Redémarrage fait par Frédéric** (vérifié : les 4 processus worker datent de 19:32:44-46, après le fichier, 18:52:45).
**Poussé le 18/11** (`64a7914`, avec les 4 commits d'autres sessions annoncés ; Vercel prêt).

### 12.48 LES ÉPREUVES RÉELLES DES LOTS B, C, D, F (18/11, 19:39-19:55, 63331 et le contact d'essai 20000009)

Pièces déposées PAR L'ÉCRAN, toutes FICTIF / SPÉCIMEN : la fiche synthétique fictive (« aucune » procédure, plan « non »), l'avis
de taxe 2026 fictif (1 234 €), un certificat de mesurage FABRIQUÉ pour l'épreuve (`scratchpad/lotD`, Carrez 66,20, habitable
70,40, du 02/11/2026), une fiche de renseignements SPÉCIMEN variante « marié » (`scratchpad/lotF`, mêmes date et lieu que 9c2).
Chaque fenêtre s'est ouverte seule après la lecture, avec ce qui était prévu : **B** procédure « Pas de procédure » / « Procédure
d'alerte » et plan « Non » / « Oui » à trancher (le nombre de lots, 48 / 24, GARDÉ exprès : hors épreuve) ; **C** 1 234 € / 900 €,
« avis 2026 » ; **D** date du mesurage 02/11 / 10/09 et surface habitable 70,4 / 68 à trancher, Carrez et « réalisé » d'accord ;
**F** « Ce que dit la fiche de renseignements », en-tête « La fiche du contact », situation « marié(e) » / « célibataire » à
trancher, date et lieu d'accord.
**Au retour** : UN travail `update_hektor_annonce_fields` (les quatre saisies réunies dans le même calque) -- groupes
`mandat_infofi` [TAXE_FONCIERE], `diagnostiques` [diag_loi_carrez_date], `copropriete` [plan, statut], `ag_interieur` [surfappart],
chacun « mise à jour effectuée », 0 écarté ; relecture faite ; calque soldé. **Comparaison case par case (script, 70 cases des
groupes copropriété, intérieur, mandat_infofi, terrain + diagnostics relevé en base)** : EXACTEMENT 5 cases ont bougé --
plan OUI -> NON, statut ALERTE -> NOTPROCESS, surfappart 68 -> 70.4, TAXE_FONCIERE 900 -> 1234, diag_loi_carrez_date 09-10 ->
11-02 ; prix 139 000 et net vendeur 130 000 relus IDENTIQUES (la crainte du §12.41 sur `mandat_infofi` tombe), CHARGES 150 intact.
➡ **Prouvés en réel : `copropriete_plan_sauvegarde`, `copropriete_statut_syndicat` (les codes Hektor), `TAXE_FONCIERE` (jamais
écrite en modification avant), `surfappart` depuis la GED (décimale « . » acceptée), `diag_loi_carrez_date`.**
**F** : travail `update_hektor_contact` done, « updated », formulaire personne seule, `statut_matrimonial: married` ; la fiche
chez nous porte `married` au clic. ⚠ Hektor ne renvoie jamais la situation de famille (`contrat_autorite.py:63`) : l'écriture
chez Hektor n'est donc pas relisible, seulement « acceptée ». Le compte rendu porte les clés neuves `conjoint_date_naissance` :
preuve que le worker redémarré tourne sur le code du lot G. (La charge porte `contact_kind: acquereur`, défaut du geste -- même
chemin que 9c : la modification ne pose pas la qualification.)
⏳ **Non éprouvés en réel** : E (le terrain : il faut un bien d'essai HORS copropriété), G (il faut un couple d'essai, à recréer),
`CHARGES` (l'appel fictif tombe d'accord), la première personne d'un couple (F).

### 12.49 L'ÉPREUVE RÉELLE DU LOT G -- la naissance du CONJOINT (18/11, 21:32-22:00, 63331, couple fictif 20000052/53)

**Le couple fictif, créé PAR L'ÉCRAN** (Contacts -> Nouveau contact, Propriétaire, Couple, « ESSAI LOTG Un / Deux », e-mails
`@example.com`, sans téléphone, e-mail RGPD DÉCOCHÉ, compte Emmanuelle PEREIRA, « Rattacher un bien existant » 63331) : travail
`create_hektor_contact` done, paire née d'un coup -- **20000052 <-> 606429 (Un)**, **20000053 <-> 606430 (Deux)**.
Puis `relire_couple_rattache.py --principal 20000052 --conjoint 20000053` (⚠ avec `.venv/Scripts/python.exe`, le Python du
worker : le Python du système n'a pas `tzdata`, la relecture y casse sur « Europe/Paris ») -> 20000052 « couple », résumé
« nommé » ; 20000053 « conjoint », rôle « conjoint », lien 20000052.
**Pièce** : une carte d'identité SPÉCIMEN de « Deux ESSAI LOTG », SANS bande MRZ, née le 03/03/1962 à MONTBRISON (42)
(`scratchpad/lotG/fabriquer.py`), déposée par la fenêtre de dépôt, type « Pièce d'identité », privée.
**L'écran** : « Ce que dit la pièce d'identité : 2 à ajouter » -- date et lieu de naissance de Deux ESSAI LOTG, la fiche du
contact « vide » ; les deux gardés, « Enregistrer et envoyer à Hektor » -> « envoyé à Hektor … (par la fiche principale du
couple) ». **Chez nous à la seconde** : 20000053 porte `1962-03-03` / `MONTBRISON (42)` ; calque `app_contact_pending` posé sur
20000052 (`spouse_birth_date`, `spouse_birth_place`, départ +10 min).
**Chez Hektor (21:00:16 UTC)** : travail `update_hektor_contact` done, `status: updated`, **`couple: true`, formulaire
`mefContacts/contactCoupleAll`** (le formulaire RELU fait foi, `console_job_worker.js:20478` -- la charge disait
`personne_seule`), `conjoint_date_naissance: 03-03-1962`, `conjoint_lieu_naissance: MONTBRISON (42)`, aucune autre case
envoyée (nom seul ; e-mails, prénoms, téléphones à `null` = non touchés). Calque soldé. **Relecture automatique** (21:00:41) :
étape conjoint « 1 conjoint nommé », nature « 20000052=couple, 20000053=conjoint » ; prénoms, e-mails INCHANGÉS ; la naissance
du conjoint RESTE chez nous (Hektor ne la rend jamais, `contrat_autorite.py:63` : elle n'est donc pas relisible chez lui,
seulement « acceptée » par le formulaire de couple).
➡ **Le lot G est PROUVÉ EN RÉEL dans le cas que le code couvre** (les deux fiches du couple reliées au bien).

⚠⚠ **TROU TROUVÉ PAR L'ÉPREUVE -- le cas courant n'est PAS couvert.** L'écran ne fusionne un couple en « membres »
(`mergeDetailContacts`) que si LES DEUX fiches sont reliées au bien ; `contactsGedDuBien` et `personnesGedDuBien` ne voient donc
le conjoint QUE dans ce cas. Avec la seule première reliée (mon premier montage), la carte est restée muette ET une ligne
« La pièce dit « Deux ESSAI LOTG », la fiche « Mandant ESSAI CONTACT » » est apparue (appariement au mauvais mandant).
**Mesure (Supabase, 18/11)** : 330 conjoints nommés actifs ; 118 ont leur première reliée à un bien (mandant / propriétaire) ;
**12 seulement** ont AUSSI leur fiche reliée au même bien. ⇒ **pour 106 sur 118, le lot G reste muet.**
**Le correctif proposé (NON écrit, à décider)** : dans « Reçu / Manque », après la lecture de l'état civil, pour chaque première
de nature « couple » sans rôle, lire aussi la fiche dont `hektor_couple_contact_id` = elle, `couple_role = conjoint` (une requête
de plus, même table) ; l'ajouter aux contacts ET aux personnes du bien (le nom et le prénom du conjoint). Additif, écran seul, sans
interrupteur neuf (celui du lot G suffit).
**Trouvé en passant** : (1) un contact créé avec « Rattacher un bien existant » est bien lié CHEZ HEKTOR mais n'apparaît sur le
bien qu'après la nuit -- la création ne pose pas la ligne `app_relation` (le geste « Rattacher un mandant existant » la pose, et
le worker répond `already_linked` sans rien réécrire) ; (2) ⚠ CORRIGÉ après l'audit demandé par Frédéric : les DROITS
d'un négociateur couvrent TOUT LE RÉSEAU (décision « R » du chantier ②, `CHANTIER_2_DROITS_NEGOCIATEUR_2026-10-09.md` l. 456 ;
règle `app_contact_current_select_scoped`, les 6 comptes actifs en périmètre `reseau`). Ce qui a filtré, c'est l'ÉCRAN : la
recherche de « Rattacher un mandant existant » passe `negociateur_email` = celui du bien (`App.tsx:3401`, commit `c502caf` du
27/08, « scopée au négociateur du dossier »), AVANT la décision du 12/10 et jamais réalignée ; même filtre dans le sélecteur de
mandant de la création de bien (`App.tsx:16034`). Un reste, pas une règle -- à décider ; (3) le compte rendu porte `qualification: "2"` (défaut `contact_kind` du geste) -- non mesuré ici.
**Au nettoyage (à décider)** : deux couples fictifs restent -- **20000050/51 <-> 606427/28** (compte formation, sans bien : mon
premier essai, la recherche du rattachement ne le trouvait pas) et **20000052/53 <-> 606429/30** (PEREIRA, reliés à 63331).
Suppression prévue par l'app (« Supprimer (tout le foyer) »), comme le 02/11.

### 12.50 LE FILTRE DU RATTACHEMENT RETIRÉ, ET L'ÉPREUVE ENTRE DEUX AGENCES (19/11, 00:10-00:25, 63331)

**La question de Frédéric** : « est-ce que le worker fonctionnait avant sans ce filtre ? Si oui, pourquoi ne pas le retirer ;
audite pourquoi on l'a ajouté ».
**L'audit** : le filtre est né le **01/06** dans le sélecteur de mandant de la création de bien (`6c1af71`, message sans aucune
raison), puis a été **recopié le 27/08** dans « Rattacher un mandant existant » (`c502caf` : « scopée au négociateur du dossier,
comme le fait le sélecteur de la création »). Aucune note ne le justifie. Le chantier ② (12/10) borne le geste au **BIEN**
(« rattacher un mandant -- son bien »), pas au contact. Le worker écrit sous le négociateur du bien et, depuis le **31/08**,
prouve le lien par l'API quand la console (filtrée par agence) ne le montre pas (`lienMandantSelonApi`, mémoire
`console-hektor-filtree-par-agence`). 47,6 % des liens vendeur ont un autre négociateur que le bien (mesure du 31/08). Les
autres recherches de contacts de l'app ne filtrent pas ainsi. Effet de bord du filtre : un contact SANS négociateur
(ex. 10355712) n'était jamais trouvable.
**Le correctif** (`b6b4d5d`, poussé et en ligne le 19/11 vers 00:20, bundle `index-QZ2JbhrQ.js`) : « Rattacher » cherche sur
tout le réseau ; la création de bien garde la liste du négociateur choisi quand le champ est vide, et cherche sur tout le
réseau dès qu'on tape. Chaque résultat affiche déjà « négociateur - agence ». Worker inchangé. `npm run build` vert.
**L'épreuve réelle, par l'écran** : depuis 63331 (PEREIRA, Groupe GTI Firminy), « ESSAI GED » trouve les deux fiches du
couple du **Compte formation** (affichées « FRANCK GERPHAGNON - Compte formation - mandant »). Rattaché « M. Un ESSAI GED »
(20000050 <-> 606427). Travail `469a244b` : demandé 00:24:27, `done` 00:24:49, **`status: linked`** (lien NEUF), 4 lectures
console sans le voir puis **« Association confirmée par l'API (la console ne la montrait pas depuis ce compte) »** -- le
chemin du 31/08, éprouvé pour la première fois sur un lien neuf entre deux agences. `relation_etablie` : la ligne est
établie tout de suite. Relecture `db2c806a` `done` 00:25:22 : **4 liens établis** sur 63331 après relecture, rien de perdu.
⚠ Non mesuré : la durée de la recherche sur tout le réseau (« Recherche en cours… » encore visible à 3 s, résultats à ~8 s
dans mon essai, une seule mesure).
**Au nettoyage** : le couple 20000050/51 <-> 606427/28 est maintenant RELIÉ à 63331 (la principale seulement) ; il
rejoint les deux couples à supprimer par l'app (§12.49).

### 12.51 LOT G' -- LE CONJOINT LU PAR LE LIEN DE COUPLE (19/11, nuit) -- ÉCRIT, ESSAIS VERTS, PAS ENCORE ÉPROUVÉ EN RÉEL

**Le trou (§12.49)** : l'écran ne fusionne un couple que si ses DEUX fiches sont reliées au bien. Mesure du 19/11 : 118
conjoints nommés ont leur première reliée à un bien, **105** n'ont QUE la première (aucune première n'a deux conjoints).
Pour eux, « Ce que dit la pièce d'identité » restait muet sur le conjoint, et la règle P4 rattachait sa pièce au mauvais
mandant (P9 pouvait aussi le dire « ni sur la fiche »).
**Le correctif** : `loadConjointsDesPremieres` (lib/ged.ts) lit, pour chaque PREMIÈRE active du bien, la fiche dont
`hektor_couple_contact_id` = elle, rôle ET nature « conjoint », active ; deux conjoints -> aucun, lecture ratée -> null.
`RecuManque.tsx` l'ajoute aux personnes du bien (`personnesCompletes`, utilisées par les règles et les fenêtres) et aux
contacts de la fenêtre, avec `conjointDe` = sa première : l'écriture du lot G (App.tsx, `appliquerBilanPersonne`) passe
déjà par elle, inchangée. Un conjoint déjà relié (couple fusionné) n'est pas ajouté deux fois. Lu seulement quand
`ged_propositions` ou `ged_remplir` est allumé. Rien de neuf n'est écrit nulle part.
**Contrôles** : les 13 essais hors ligne de la GED verts (4 réalignés sur `personnesCompletes`, 6 nouveaux « lot G' » dans
`test_ged_remplir_contact.cjs`, 80 verts) ; `npm run build` vert.
**Pas encore éprouvé en réel -- et pourquoi** : le couple d'essai « ESSAI GED » (20000050/51), rattaché ce soir à 63331
(§12.50), n'a pas encore le rôle « conjoint » : il est posé par `conjoints_des_couples.py` (la nuit) seulement si la
première est ÉLIGIBLE, et l'éligibilité (`active_annonce_relation`) n'est recalculée que par la construction de nuit de la
couche. Relancés à la main sans effet : `relire_couple_rattache.py` (OK, 5 étapes) puis `conjoints_des_couples.py` (4 804
marqués, 20000051 non) et l'envoi des deux fiches. ➡ Après le run du 19/11, déposer une pièce SPECIMEN de « Deux ESSAI GED »
sur 63331 et éprouver.
⚠ **Trouvé en passant** : (1) un couple qu'on vient de relier à un bien n'a son conjoint « conjoint » qu'à la nuit suivante --
le lot G attend donc une nuit pour lui ; (2) `conjoints_des_couples.py` marque **4 804** conjoints nommés à envoyer, alors que
Supabase n'en porte que **330** actifs nommés au rôle « conjoint » -- écart NON expliqué, non mesuré plus loin.

### 12.52 LOT G' ÉPROUVÉ EN RÉEL (19/11, 07:00-07:27, 63331, couple fictif 20000050/51)

**Mise en ligne** : `origin/main` fusionné ici (2 commits de l'étape 4 chap. 6 lot 0), poussé `757489c` avec `a7c560c` et 7
commits du Classeur (notes, CSV, contrôles, patchs SQL DORMANTS). Vercel : bundle `index-bHtjuVlj.js`, qui porte la requête
`.eq("couple_role","conjoint").eq("nature_fiche","conjoint")`.
⚠ **Fausse alerte en route** : après la fusion, 2 essais GED (`test_ged_remplir*.cjs`) sont sortis ROUGES sur le disque. Cause :
la fusion a réécrit `App.tsx` en CRLF (`core.autocrlf=true`), et ces essais cherchent des `\n`. Le fichier COMMITÉ est en LF :
les 13 essais GED rejoués sur `git archive` (LF) sont VERTS. Rien n'a été corrigé, rien n'était cassé.
**Le blocage du §12.51 était levé au matin** : 20000051 portait `conjoint` / `conjoint`, lien 20000050 (étape qui l'a posé
non mesurée). Sur 63331, seule 20000050 est reliée (`app_contact_relation_current`) : c'est le cas du lot G'.
**L'écran, avant le dépôt** (état React relu dans l'onglet) : `conjointsLus` = {606429 -> 20000053, 606427 -> 20000051} ;
`conjointsEnPlus` = [20000051] (20000053 écarté : déjà relié, couple fusionné) ; `personnesCompletes` porte « Deux ESSAI GED ».
⚠ **P6 ne réclame pas sa pièce** -- ce n'est PAS le lot G' : `personneSurLaFiche` (gedComparer.ts:219) dit « egal » dès qu'UN
mot du nom est commun et le prénom égal ; la carte de « Deux ESSAI LOTG » « couvre » donc « Deux ESSAI GED » (mot « ESSAI »).
Artefact des noms d'essai ; en vrai, deux personnes du bien au même prénom partageant un mot du nom (« Jean MARTIN » /
« Jean MARTIN DUPONT ») seraient confondues de même -- noté, non traité. La fenêtre, elle, exige le nom ENTIER (`memePersonne`).
**Pièce** : carte SPÉCIMEN de « Deux ESSAI GED », SANS MRZ, née le 05/05/1964 à FEURS (42) (`scratchpad/lotGprime/fabriquer.py`),
déposée par la fenêtre de dépôt, type « Pièce d'identité », privée -> `upload_document_to_hektor` done (07:14).
**L'écran** : « Ce que dit la pièce d'identité » s'ouvre seul, « À ajouter 2 » : date et lieu de naissance de Deux ESSAI GED, la
fiche du contact « vide ». Les deux pris, « Enregistrer et envoyer à Hektor » -> « envoyé à Hektor … (par la fiche principale du
couple) ». **Chez nous à la seconde** : 20000051 `1964-05-05` / `FEURS (42)` ; calque `app_contact_pending` sur 20000050
(`spouse_birth_date`, `spouse_birth_place`, départ 07:25).
**Chez Hektor** : `update_hektor_contact` done 07:26:11, `status: updated`, `couple: true`, formulaire
`mefContacts/contactCoupleAll`, `conjoint_date_naissance: 05-05-1964`, `conjoint_lieu_naissance: FEURS (42)`, rien d'autre
envoyé (nom seul). Calque soldé. Relecture `refresh_console_contact_data` done 07:26:49 : 20000050 « couple », 20000051
« conjoint », sa naissance INCHANGÉE chez nous.
➡ **Le lot G' est PROUVÉ EN RÉEL** : le conjoint d'une première seule reliée au bien est lu, proposé, écrit chez nous, et part chez
Hektor par la fiche principale.
**Au nettoyage (à décider)** : les deux couples fictifs (§12.49) et la carte SPÉCIMEN « Deux ESSAI GED » sur 63331.

**✅ LE NETTOYAGE EST FAIT (19/11, 07:43 -> 07:46, « Pousse et nettoie »)** -- sauvegarde d'abord
(`scratchpad/lotGprime/sauvegarde_menage_couples_specimen_20261119.json`). **Contacts, par l'écran** (« Supprimer (tout le
foyer) » sur la principale, puis « Supprimer » sur le conjoint resté chez nous, comme le 02/11) : 20000050 -> Hektor 606427
supprimé ; 20000052 -> 606429 supprimé ; 20000051 et 20000053 -> `hektor_delete_sent: false`, `after_found: false` : ils
n'existaient déjà plus chez Hektor (**cascade du foyer confirmée une 3e fois**). 4 travaux `delete_hektor_contact` done, 0 erreur.
**Pièces** : 2 travaux `delete_document_from_hektor` (raison `menage_specimen_lot_g_19_11`, au nom de Frédéric, la charge du
18/11) -> done : cartes SPÉCIMEN « Deux ESSAI GED » (716264) et « Deux ESSAI LOTG » (716263).
**Après** : 0 ligne pour les 4 contacts dans `app_contacts_current` et `app_contact_pending` ; 63331 ne garde que son mandant
d'essai 20000009 (propriétaire) et **5 pièces FICTIF, GARDÉES EXPRÈS** (électricité, fiche copro, mesurage, taxe foncière, fiche
de renseignements « marié ») : elles servent aux preuves E et CHARGES encore à faire. Les lectures GED des pièces retirées restent
en base, invisibles (comme le 18/11).

### 12.53 L'ÉPREUVE RÉELLE DE `CHARGES` (lot C) (19/11, 09:23-09:35, 63331, « POUSSE ET ENCHAÎNE »)

**Pièce** : un appel de fonds FICTIF fabriqué pour l'épreuve (`scratchpad/lotCharges/fabriquer.cjs`) : budget 2027 du lot 12
= **2 400 €/an** (la fiche portait CHARGES 150 €/mois et quote-part 1 800 €/an, d'accord entre elles -- d'où le « tombe
d'accord » du §12.48). Déposé PAR L'ÉCRAN (« Ajouter un document »), type « Appels de fonds, budget prévisionnel » proposé, le
nom et l'IA d'accord, privé -> `upload_document_to_hektor` done (09:23:39). Lu : « budget du lot 2 400 € par an · lot 12 ».
**L'écran** : « Ce que dit l'appel de fonds » s'ouvre SEUL, deux lignes à trancher (quote-part 2 400 / 1 800, charges
200 / 150). **Enregistré** -> « envoyé à Hektor : Charges annuelles du lot 2400 € par an, Charges de copropriété par mois
200 € par mois (chemin habituel de la fiche, contrôlé au retour) » ; calque `app_annonce_pending` {CHARGES 200,
copropriete_quote_part 2400}, départ +10 min.
**Chez Hektor** : `update_hektor_annonce_fields` done 09:34:25, `status: updated` -- groupe `copropriete` [copro_quote_part]
et groupe `mandat_infofi` [copro_charges -> CHARGES], chacun « mise à jour effectuée », 0 écarté ; calque soldé ; relecture
`refresh_console_data` done 09:35:02 ; 0 écart dans `app_v_annonce_modif_ecarts`. **Fiche relue** : EXACTEMENT 2 cases ont
bougé dans copropriété / mandat_infofi / terrain -- `copropriete_quote_part` 1800 -> 2400, `CHARGES` 150 -> 200 ; prix 139 000,
net vendeur 130 000, TAXE_FONCIERE 1 234 INCHANGÉS.
➡ **`CHARGES` est PROUVÉ EN RÉEL** (l'annuel / 12 du document, écrit par la GED, accepté et relu chez Hektor).
⚠ **La quote-part n'était pas visée** : je comptais la garder à 1 800. Elle est partie avec, par un clic de trop -- voir
ci-dessous. Bien d'essai, valeur fictive : rien à défaire.
⚠⚠ **TROUVAILLE, NON CORRIGÉE (à décider)** : la fenêtre « Ce que dit… » s'ouvre d'elle-même pendant que la fenêtre de DÉPÔT
est encore à l'écran, et son bouton « Enregistrer » tombe à l'endroit du « Fermer » du dépôt. Or une ligne « à trancher »
arrive DÉJÀ COCHÉE sur la valeur du document (`BilanCompromis.tsx:119`, voulu). Un clic destiné à FERMER le dépôt a donc
ENREGISTRÉ et envoyé à Hektor les deux valeurs du document. Pistes : ne pas ouvrir la fenêtre tant que le dépôt est ouvert,
ou ne rien cocher d'avance quand elle s'ouvre seule. Rien n'a été codé.
⏳ **Reste E** (le terrain, `surfterrain` depuis le titre) : par construction il ne se propose QUE sur un bien EXPLICITEMENT hors
copropriété ; 63331 est en copropriété OUI -> il faut un bien d'essai hors copropriété (à décider). Sur 63331 : 1 pièce FICTIF
de plus (l'appel de fonds), à joindre au ménage.

### 12.54 L'ÉPREUVE RÉELLE DU LOT E -- le terrain depuis le titre de propriété (19/11, 09:39-09:52, 63330, « Ok enchaîne »)

**Le bien** : pas de bien à créer -- **63330** (10000006, « ESSAI 8A2B TOUS CHAMPS - ne pas diffuser », maison, Estimation,
diffusable 0) est EXPLICITEMENT hors copropriété (`copropriete = NON`), terrain 600 m², aucun document, rien en attente.
**Pièce** : un titre de propriété FICTIF fabriqué pour l'épreuve (`scratchpad/lotE/fabriquer.cjs`) : maison « non soumise au
statut de la copropriété, aucun lot », cadastre AB 123 (612 m²) + AB 124 (130 m²), **contenance totale 742 m²**, acte du
15/03/2011. Déposé PAR L'ÉCRAN, type « Titre ou origine de propriété » (le nom et l'IA d'accord), privé ->
`upload_document_to_hektor` done 09:40:43.
**L'écran** : « Ce que dit le titre de propriété » s'ouvre SEUL : « À trancher 1 », Surface du terrain **742 m²** (titre,
« correction » cochée d'avance) / 600 m² (fiche), note « contenance cadastrale du titre », page 1. Enregistré (exprès cette
fois) -> « envoyé à Hektor : Surface du terrain 742 m² (chemin habituel de la fiche, contrôlé au retour) » ; calque
{surfterrain 742}.
**Chez Hektor** : `update_hektor_annonce_fields` done 09:51:12, `status: updated`, groupe `terrain` [land_surface ->
surfterrain] « mise à jour effectuée », 0 écarté ; calque soldé ; relecture done 09:51:50 ; 0 écart. **Fiche relue** :
EXACTEMENT 1 case a bougé dans copropriété / mandat_infofi / terrain / intérieur -- `surfterrain` 600 -> 742 ; SHON 130,
terrain arboré et piscinable, prix 187 000, net 175 000 INCHANGÉS.
➡ **Le lot E est PROUVÉ EN RÉEL** (2e écriture connue de `surfterrain`, la 1re depuis la GED).
⚠ **La trouvaille du §12.53 se CONFIRME** : la fenêtre s'est ouverte pendant l'attente, et son « Enregistrer et envoyer à
Hektor » était SOUS LE CURSEUR, à la place du « Envoyer 1 document » du dépôt -- un double clic sur « Envoyer » aurait
enregistré. Toujours non corrigé (à décider).
**Au ménage** : 63330 porte 1 pièce FICTIF (le titre) ; son terrain vaut maintenant 742 (valeur d'essai).
⏳ **Restent non éprouvés** : la première personne d'un couple (F).

### 12.55 LE CLIC DE TROP CORRIGÉ : « Ce que dit… » attend la fermeture du dépôt (19/11, « Oui, corrige-le », « Oui, pousse »)

**Choix** : la fenêtre ATTEND (le cochage d'avance, voulu, ne change pas). `lib/gedFenetreDepot.ts` (neuf) : un compteur des
fenêtres de dépôt ouvertes + l'événement `ged:fenetre-depot` ; `DepotDocuments.tsx` se signale ouvert / fermé SEULEMENT en
fenêtre au-dessus du bien (`onFermer`, skin cockpit) ; `RecuManque.tsx` : l'ouverture d'elle-même ne part pas tant que le
dépôt est ouvert, et ne marque RIEN vu avant (elle part à la fermeture). Commit `a71cf0b`, poussé seul (`c4b319a`), en ligne
(`index-DSLJjWT0.js`, la chaîne `ged:fenetre-depot` est dans le paquet servi).
**Contrôles** : `test_ged_bilan` **136 VERT** (3 neufs) ; témoin inverse (garde retirée) -> 1 ROUGE ; dépôt 33, Reçu / Manque
29 verts ; `npm run build` vert. (`test_ged_remplir_contact` rouge SUR LE DISQUE = App.tsx en CRLF depuis la fusion du matin ;
80 / 80 sur le contenu commité -- la correction ne touche pas App.tsx.)
**Épreuve à l'écran** (63330, un 2e titre FICTIF : 800 m², acte du 02/06/2015) : envoyé, lu en ~10 s (« acte de vente du
02/06/2015 ») -- **20 s après, AUCUNE fenêtre par-dessus le dépôt** (la veille : là en moins de 10 s). « Fermer » le dépôt ->
« Ce que dit le titre de propriété » s'ouvre : terrain 800 / 742, à trancher. Refermée par « Fermer » SANS enregistrer : 0
calque, aucun `update_hektor_annonce_fields`, terrain toujours 742 ; la ligne reste sur sa carte « Voir et trancher ».
⚠ **Reste, noté** : la fenêtre s'ouvre à l'instant où le dépôt se ferme, et son « Enregistrer » est encore sous le curseur
qui vient de cliquer « Fermer » -- un DOUBLE-CLIC sur « Fermer » pourrait encore enregistrer. Remède possible (non fait) :
« Enregistrer » inactif une seconde après une ouverture d'elle-même.
**Au ménage** : 63330 porte 2 titres FICTIF ; son terrain vaut 742 (valeur d'essai).
**Le double-clic, bloqué (19/11, « Enchaîne »)** : dans `BilanCompromis.tsx`, « Enregistrer » est INACTIF la première seconde
après TOUTE ouverture de la fenêtre (d'elle-même ou par « Voir et trancher » : dans les deux cas le bouton peut arriver sous
un curseur qui vient de cliquer). C'est le seul chemin qui enregistre (pas de touche Entrée, pas de formulaire). Contrôles :
`test_ged_bilan` **137 VERT** (1 neuf) ; témoin inverse (délai retiré) -> 1 ROUGE ; `npm run build` vert. Pas encore poussé.
**✅ En ligne et éprouvé (19/11, « Pousse et vérifie »)** : poussé seul (`da23acf`), Vercel READY, paquet `index-BOcjX_vM.js`.
Sur 63330, « Voir et trancher » (titre 800 / fiche 742) : « Enregistrer et envoyer à Hektor » mesuré INACTIF à 153 ms et
654 ms, ACTIF à 1 355 ms. Puis fermé, rouvert, et DEUX clics sur « Enregistrer » à 200 ms : inactif au clic, aucun
« Enregistré » au pied, 0 calque, 0 `update_hektor_annonce_fields`, terrain toujours 742. Fenêtre refermée sans rien écrire.
**Le rouge de `test_ged_remplir_contact` signalé sur main (session « Page d'accueil », 19/11) : FAUSSE ALERTE de fins de
ligne**, pas le lot G -- rejoué sur le contenu commité (`git -c core.autocrlf=false archive`) : 505ffa6 80/80, 64a7914 74/74 ;
par un `git archive` par défaut (CRLF sous Windows) : 79/1 et 73/1. L'essai lit désormais ses sources en LF (`lireSource`,
commit `280d0d2`) : 80/80 sur le disque en CRLF.

### 12.56 L'ÉPREUVE RÉELLE DU LOT F SUR LA PREMIÈRE D'UN COUPLE (19/11, 10:40-11:13, 63331, couple fictif 20000054/55)

**Le couple fictif, créé PAR L'ÉCRAN** (Contacts -> Nouveau contact, Propriétaire, Couple, M. « Un / Deux ESSAI LOTF »,
e-mails `@example.com`, sans téléphone, e-mail RGPD DÉCOCHÉ -- il est coché d'avance --, « Rattacher un bien existant »
63331) : `create_hektor_contact` done -- **20000054 <-> 606436 (Un)**, **20000055 <-> 606437 (Deux)**. ⚠ Sous le compte
formation, la recherche du bien de l'étape 2 ne trouve PAS 63331 (« Aucune annonce trouvée ») : elle est limitée aux biens du
compte choisi -- refait sous le compte d'Emmanuelle PEREIRA (le reste du formulaire garde sa saisie, vérifié). Puis
`relire_couple_rattache.py --principal 20000054 --conjoint 20000055` (Python de `.venv`) : ok, 20000054 « couple »,
20000055 « conjoint » de 20000054.
**Pièce** : une carte d'identité SPÉCIMEN de « Un ESSAI LOTF », SANS MRZ, né le 07/07/1960 à SAINT-CHAMOND (42)
(`scratchpad/lotFcouple/fabriquer.py`), déposée par la fenêtre de dépôt (type et nom d'accord, privée), lue « carte
d'identité valable jusqu'au 20/09/2034 ». ⭐ La correction du §12.55 a tenu : AUCUNE fenêtre pendant le dépôt.
⚠ **Au premier passage, PAS de « Ce que dit… »** : la rubrique Contact lit le REGISTRE des mandants (`loadAnnonceMandants`),
et la création d'un contact n'y pose pas de ligne (déjà noté au §12.49) -- l'écran ne voyait que « Mandant ESSAI CONTACT »,
et les règles comparaient la carte à lui (« La pièce dit Un ESSAI LOTF, la fiche Mandant ESSAI CONTACT » : la confusion P6
du §12.52, par le mot « ESSAI »). Geste prévu : Contact -> Ajouter un mandant -> « Rattacher un mandant existant » -> Un ESSAI
LOTF -> `link_hektor_mandant` done, registre 2 mandants.
**L'écran** : « Ce que dit la pièce d'identité » s'ouvre SEUL (lecture de moins de 30 min) : « À ajouter 2 » -- date et lieu
de naissance de Un ESSAI LOTF, la fiche du contact « vide ». Les deux pris, « Enregistrer et envoyer à Hektor » -> « envoyé à
Hektor … (chemin habituel de la fiche du contact) ». **Chez nous à la seconde** : 20000054 `1960-07-07` / `SAINT-CHAMOND (42)` ;
20000055 INCHANGÉ. Calque `app_contact_pending` sur 20000054 : `birth_date`, `birth_place`, nom actuel joint,
`send_rgpd_email: false`, `person_type: personne_seule`, `contact_kind: acquereur` (défaut du geste, comme au §12.48).
**Chez Hektor** : `update_hektor_contact` done 11:07:21, `status: updated`, **`couple: true`, formulaire
`mefContacts/contactCoupleAll`** (le formulaire relu fait foi, la charge disait `personne_seule`), `date_naissance: 07-07-1960`,
`lieu_naissance: SAINT-CHAMOND (42)` ; **tous les champs `conjoint_*` à null** (prénom, nom, e-mail, téléphone, date et lieu de
naissance du conjoint NON envoyés) ; prénom, e-mail de la première à null (non touchés). Calque soldé. Relecture 11:07:53 :
nature « 20000054=couple, 20000055=conjoint », la naissance de la première RESTE, le conjoint INTACT (« Deux », son e-mail,
sans naissance ; le résumé de couple porte toujours Deux).
➡ **Le lot F est PROUVÉ EN RÉEL sur la PREMIÈRE PERSONNE D'UN COUPLE** : sa naissance part par le formulaire de couple sans
toucher au conjoint (le point (1) de l'audit du §12.46, enfin éprouvé). **Toutes les épreuves réelles des lots A à G' sont
faites.**
⚠ Noté en passant (non traité) : `coordonnees: "remplacees"` dans le compte rendu du worker -- rien n'a bougé dans les
coordonnées relues (pas de téléphone, e-mail inchangé), mais le mot n'est pas expliqué ici.
**Ménage fait** (11:09-11:12) : carte SPÉCIMEN retirée (`delete_document_from_hektor`, raison `menage_specimen_lot_f_couple_19_11`) ;
« Supprimer (tout le foyer) » sur 20000054 -> Hektor 606436 supprimé ; « Supprimer » sur 20000055 -> `hektor_delete_sent:
false`, il n'existait déjà plus (cascade du foyer, 4e fois). 0 contact, 0 calque, 63331 ne garde que 20000009 et ses 6 pièces
FICTIF ; file vide.

### 12.57 (19/11) -- P6 ne confond plus deux personnes ; « Nouveau contact » protégé du double-clic ; « remplacees » expliqué

**Feu vert de Frédéric** : « Alors corrige et enchaîne ».
**P6, la cause** (`gedReglesPersonnes.ts`) : une personne était « couverte » dès qu'UNE pièce lue lui ressemblait (`egal` de
`personneSurLaFiche` : un mot du nom commun et le même prénom). Une seule carte couvrait donc deux personnes : « Jean MARTIN »
couvrait aussi « Jean MARTIN DUPONT », et la carte de « Deux ESSAI LOTG » couvrait « Deux ESSAI GED » (§12.52, mot « ESSAI »).
**Le correctif** (`652cdab`) : chaque pièce couvre la SEULE personne du bien (mandants ET acquéreurs vivants, offre comprise)
qui lui ressemble le mieux -- verdict, puis part du nom en commun (nom de naissance OU d'usage), puis premier prénom
(`personnesCouvertes`). Égalité parfaite entre deux personnes : la pièce ne couvre NI l'une NI l'autre (les deux sont
réclamées : une pièce manquante se réclame plutôt que de se taire), SAUF si chacune porte exactement un nom de la pièce --
la même personne inscrite sous son nom de naissance et son nom d'usage. `personneSurLaFiche` n'est PAS touchée (6 appelants :
P4, état civil, financement, règles lues, offres) ; seul `motsDe` est exporté. Ce qui ne change pas : la règle « proche
seulement si la fiche n'a pas de prénom » (13/11), une seule personne au nom composé couverte par la carte au nom court.
**Essais** : `test_ged_regles_personnes.cjs` 46 verts (8 neufs) ; **témoin inverse** : sur l'ancien code, les 5 cas neufs
sont ROUGES, les 41 autres verts. Les 13 essais GED verts ; `test_ged_remplir.cjs` montre 7 rouges sur le disque = la
fausse alerte CRLF du §12.55 (App.tsx en CRLF) -- 38 verts en lisant les sources sans CRLF. Build vert.
⚠ **Non traité, noté** : P4 dit encore « La pièce dit Un ESSAI LOTF, la fiche Mandant ESSAI CONTACT » (verdict `proche`,
un mot du nom commun). C'est le dessin de P4 (une information, jamais une alerte, rien ne s'écrit) : en vrai, c'est le cas
« Jean DUPONT » face à « Marie DUPONT ». Pas touché.
**« coordonnees: remplacees »** (§12.56) : ce n'est PAS un défaut. Le mot dit seulement que l'interrupteur
`contact_coordonnees_remplacer` est ALLUMÉ (`console_job_worker.js:20528`, mode D-5 du 05/11) ; il ne dit pas qu'une
coordonnée a changé. Une valeur vide ne part jamais dans ce mode (`if (contact.email)`), et la charge du lot F n'en portait
aucune : rien n'est parti, ce que la relecture a confirmé.
**« Nouveau contact », le double-clic** (`94d0a7a`, App.tsx) : le bouton du bas change de rôle sous le curseur -- « Étape
suivante » devient « Créer le contact » (passage synchrone à l'étape 2), et « Créer » devient « Continuer malgré doublon »
quand des doublons sont trouvés. Le 2e clic d'un double-clic créait donc le contact sans montrer l'étape 2, ou acceptait le
doublon. Parade : le bouton reste inactif 1 s après chaque changement d'étape ou l'apparition des doublons (pas au premier
affichage) -- la même que « Ce que dit… » (§12.55). Essai statique `test_contact_double_clic.cjs` 4 verts, témoin inverse
compris. ⚠ **Pas vu à l'écran** : il faut le déploiement (accord de Frédéric).
**En ligne et éprouvé le 20/11** : les 3 commits rejoués sur `origin/main` (le dossier local avait divergé : un `git push`
simple était refusé), poussés en `03e03bf`, déployés par Vercel (`dpl_65W6i7SbAKTHHMsrUB8Ed2MsAyUU`, READY). Le bundle servi
porte les deux correctifs (`(c.length===1||o&&o[1]===1)` pour P6 ; `disabled:se||Mt` et `setTimeout(…,1e3)` sur `[re,vn]`).
**À l'écran**, Nouveau contact, identité fictive « ESSAI DOUBLECLIC » / `@example.com`, compte formation, UN seul clic sur
« Étape suivante » : 0 ms « Étape suivante » actif -> 100 ms « Créer le contact » INACTIF -> 500 ms INACTIF -> 1 300 ms actif.
Fenêtre fermée sans enregistrer ; 0 travail de contact créé (vérifié en base). Pas de vrai double-clic tenté : un échec
aurait créé le contact chez Hektor. P6 n'est pas éprouvée à l'écran (il faudrait deux personnes au même prénom sur un bien).

### 12.58 (20/11, « Fais 1, 2, 3 ») -- le ménage des pièces d'essai, deux trouvailles auditées, un essai rendu insensible aux fins de ligne

**1. LE MÉNAGE EST FAIT (20/11, 08:50 -> 08:53, heure de Paris).** Sauvegarde datée d'abord
(`scratchpad/menage2011/sauvegarde_menage_pieces_fictives_20261120.json` : les 8 fiches, leur numéro Hektor, leur chemin).
Contrôles avant : 8 documents en tout sur 63331 et 63330, TOUS marqués ESSAI / FICTIF / SPECIMEN, signature `to_send`,
0 demande de signature liée, file vide. Le geste : `delete_document_from_hektor`, raison `menage_pieces_fictives_20_11`,
au nom de Frédéric, la charge du 18/11 -- d'abord UN seul (63330, titre de propriété, done en ~40 s, Hektor 716269
confirmé), puis les 7 autres. **8/8 done, 0 erreur** ; journal des suppressions : **8 traces, 8 « confirmé chez
Hektor »** ; il reste **0 document** sur 63331 et 63330. Comme le 18/11, les lectures GED de ces pièces restent en base,
invisibles à l'écran.
⚠ **Ce que le ménage ne défait pas, exprès** : les valeurs écrites sur les fiches d'essai par les preuves restent
(63330 terrain 742 m², 600 avant ; 63331 CHARGES 200 et quote-part 2 400, 150 et 1 800 avant). Les remettre = une
écriture chez Hektor de plus, non demandée.

**2a. « La recherche du bien, à la création d'un contact, ne regarde que le compte choisi » : C'EST LE DESSIN, PAS UN
DÉFAUT.**
- Le filtre est là depuis le 01/06 (`8ef77ba`, App.tsx, `scope: { negotiatorEmail: selectedHektorEmail }`) ; l'écran le
  DIT quand la liste est vide : « Les annonces récentes du négociateur apparaissent ici ».
- Le compte choisi est le NÉGOCIATEUR DU CONTACT (la carte d'aperçu l'écrit : « Négociateur · … »), et le worker ouvre la
  session Hektor de ce compte (`ensureHektorExecutionContext`, `preferRequester`). Montrer ses biens à lui garde le contact
  et le bien chez le même négociateur.
- Pas de contournement : un numéro tapé ne vaut que s'il est choisi dans la liste (`setOwnerAnnonceId('')` à chaque frappe).
- ⚠ Une différence, NOTÉE seulement : les deux autres recherches de bien (fenêtres de RDV, App.tsx ~40056 et ~47166)
  cherchent dans toute l'AGENCE quand elle est connue. Rien ne dit qu'il faille aligner : ce sont d'autres usages.
- ⚠ NON MESURÉ : si Hektor accepterait de relier un bien d'une autre agence que celle du compte (la console est filtrée
  par agence). Je ne l'ai pas essayé : ce serait une écriture chez Hektor.
- Ce qui m'avait surpris le 19/11 venait de moi : j'avais pris le compte formation pour un bien d'Emmanuelle PEREIRA.

**2b. « Un contact créé dans l'app n'a pas de ligne au registre des mandants » : VRAI, MAIS SEULEMENT JUSQU'À LA NUIT,
et le chemin n'a servi que deux fois, les deux par moi.**
- Le lien existe BIEN chez Hektor : la création avec « Rattacher un bien existant » appelle `linkHektorMandantContact` et
  attend sa confirmation (19/11 : `post_create_step.status = linked`, 606436 sur 63331).
- Ce qui manque est CHEZ NOUS : l'écran lit `app_relation` (vue `app_contact_relations_current`). Les TROIS portes du
  mandant l'écrivent au clic puis le marquent établi (`app_link_mandant_optimistic`, `app_create_mandant_contact_optimistic`,
  `app_unlink_mandant_optimistic` ; dans le worker l'étape `relation_etablie`). La création d'un contact
  (`app_create_contact_optimistic`) n'y touche pas, et le worker ne relit après coup que le CONTACT, pas le bien.
- La nuit rattrape : `relation_ledger.py` recopie chaque nuit les liens que Hektor montre, et elle le fait AUSSI pour les
  contacts nés dans l'app (mesuré : 7 lignes `sync_annonce_contact_link` sur des contacts >= 20 000 000, premières vues
  à 04:48 et 04:55 les 23 et 24/10). ⚠ Mais le cas EXACT (création avec rattachement, puis la nuit) n'a jamais été observé :
  les deux fois (18/11 20:38, 19/11 09:50), j'ai refait « Rattacher un mandant existant » dans l'heure.
- L'usage réel : 49 créations de contact depuis le 29/05, dont **2** avec « Rattacher un bien existant », toutes deux sur
  63331, par moi. 17 « Terminer », 14 sans étape, 14 avec recherche.
- Effet, donc : le mandant rattaché à la création n'apparaît ni sur la fiche du bien ni dans la rubrique de la GED avant la
  nuit. Rien ne se perd.
- Le remède, s'il est voulu (code existant -> « vas-y ») : faire comme les trois autres portes, c'est-à-dire écrire le lien
  au clic, ou au minimum après la confirmation de Hektor (le patron est `marquerLienDeLaCreationEtabli`, worker l. ~18907).

**3. `test_ged_remplir.cjs` lit ses six sources sans les retours chariot** (`.replace(/\r\n/g, '\n')`, comme
`test_ged_remplir_contact.cjs`) : **38 verts sur le disque** (7 rouges avant, tous dus au CRLF d'App.tsx).
⛔ **DÉCISION DE FRÉDÉRIC (20/11) sur 2b : « Non, laisse ».** On ne corrige pas : la nuit rattrape le lien, rien ne se
perd. Ne pas relancer.

### 12.59 VISUEL V3, MORCEAU 1 -- la base de « Masquer » (20/11, « Oui, vas-y ») -- ÉCRIT ET RÉPÉTÉ, PAS POSÉ

Décisions de Frédéric (20/11, `notice/AUDIT_GRAPHIQUE_GED_2026-11-18.md` §8-9) : la période de test est retirée ; un point
d'attention s'écarte par « Masquer », réversible par « Réafficher » ; le masquage vaut POUR TOUT LE MONDE sur le bien.
**Le patch** `supabase/patch_ged_masquer_2026-11-20.sql` (+ `_INVERSE`, + `_REPETITION`) : le journal `app_ged_jugement`
apprend deux verdicts, `masque` et `reaffiche` (CHECK de la table + garde de `app_ged_juger`, rien d'autre ne bouge dans la
fonction ; droits reposés à l'identique). Le plus récent d'une ligne fait foi : `reaffiche` -> visible, tout autre -> masqué.
Garde à l'entrée : l'empreinte de la fonction (`4d945b66…`) et le CHECK d'origine, sinon ARRÊT. L'inverse refuse s'il
existe des `masque` / `reaffiche` (le journal ne s'efface pas) et vérifie qu'il défait bien SA fonction.
**Répétition jouée VERTE (8 contrôles), en Frédéric sur 63331, sans rien garder** : masquer puis réafficher passent, un
verdict inconnu est refusé, les anciens verdicts passent, `authenticated` n'écrit toujours pas en direct, 3 lignes d'essai
à son nom, aucun ancien jugement touché, porte fermée à `anon`. **Aller-retour patch + inverse VERT** : la fonction revient
à l'empreinte exacte du 16/11 et le CHECK d'origine. Après chaque essai, mesuré : porte intacte, CHECK intact, 8 jugements.
⚠ Une limite vue en répétition : dans UNE transaction les deux lignes ont le même `juge_le` ; à l'écran chaque clic est sa
propre transaction (le plus récent fait foi). ⚠ Tant que l'écran (morceau 4) n'écrit pas ces mots, ce patch ne change RIEN
à ce que voit un utilisateur. **Reste : le poser en base (accord de Frédéric), puis le morceau 2.**
**✅ POSÉ EN BASE le 20/11 (« Oui, pose-le »)** : état revérifié juste avant (empreinte `4d945b66…`, CHECK d'origine,
8 jugements, `ged_propositions = admin`) ; patch passé d'un bloc ; **5 contrôles sur 5 VERTS** (CHECK et porte acceptent
`masque` / `reaffiche`, porte SECURITY DEFINER fermée à `anon`, 8 jugements intacts, interrupteur inchangé). Aucun écran ne
l'utilise encore (morceau 4). Retour arrière : `supabase/patch_ged_masquer_2026-11-20_INVERSE.sql`.

### 12.60 VISUEL V3, MORCEAU 2 -- le socle : la GED branchée sur la charte bienvu (20/11, « Oui, enchaîne », « La charte ») -- ÉCRIT, PAS EN LIGNE

**Trouvé en l'auditant** (`AUDIT_GRAPHIQUE_GED_2026-11-18.md` §9, correction) : la charte est déjà dans l'app (`src/bienvu.css`,
jetons `--bv-*` sous `:root.bv`, allumée en production) avec DEUX polices -- titres Plus Jakarta Sans, texte Hanken Grotesk.
Ma maquette V3 disait « une police » : faux. **Décision de Frédéric : « La charte »** (Hanken au texte, comme tout bienvu).
**Le code** (CSS seulement, 3 fichiers, 127 lignes remplacées une pour une) : `RecuManque.css` (71 couleurs, 4 polices),
`DepotDocuments.css` (64, 7), `BilanCompromis.css` (16, 5) -- chaque couleur qui a un rôle dans la charte (magenta, framboise,
roses, encre, gris, traits, brume, vert et fonds d'état) devient `var(--bv-…, <ancienne valeur>)`, chaque police
`var(--bv-font-display | --bv-font-ui, <ancienne pile>)`. ⭐ Le repli est l'ancienne valeur : interrupteur bienvu éteint =
mêmes pixels. Gardés en dur, exprès : le blanc, les textes foncés d'état (vert, ambre, rouge : contraste sur fond pâle), le
papier, les bleus et teintes sans rôle dans la charte. Rien d'autre ne change (ni mise en page, ni texte, ni geste).
**Ce qui se verra, interrupteur allumé** : des teintes légèrement corrigées (encre #222323, vert #2f7d59, survols en
framboise #8c0044, fonds roses unifiés) ; mêmes polices qu'avant.
**Contrôles** : `test_ged_socle.cjs` **16 VERT** (aucune couleur de la charte en dur, chaque jeton existe et garde son repli,
chaque police passe par la charte, deux polices) ; témoin inverse sur l'ancien fichier : **13 ROUGE**. Les 14 autres essais GED
verts (bilan 137, lues 95, remplir contact 80…). `npm run build` passe ; le paquet porte `var(--bv-magenta, #c5005f)` et
`.bc{--bc-encre: var(--bv-ink, #1f2121)…`. ⚠ Pas vu à l'écran : il faut le déploiement (accord de Frédéric).

### 12.61 VISUEL V3, MORCEAU 3 -- « Le dossier » : la liste du cockpit rangée par moment (20/11, « Oui mais audite de nouveau ») -- ÉCRIT, PAS EN LIGNE

Ré-audit avant le code : `AUDIT_GRAPHIQUE_GED_2026-11-18.md` §10 bis (9 risques, 9 parades). La session signature (Youtrust)
a été prévenue (`notice/PROMPT_AVERTIR_SESSION_SIGNATURE_GED_2026-11-20.md`) : rien en cours chez elle, DEUX CONDITIONS,
tenues -- (1) « Voir le suivi » déplie le groupe et la ligne du document PUIS défile (`ouvrirPuisSuivi`, sinon `sst-<id>`
n'existe pas) ; (2) l'état de signature reste visible ligne REPLIÉE (la pastille d'aujourd'hui + « signée le / en attente /
expirée … à renvoyer » ; « À envoyer en signature » reste dans la carte, cf. §5.1 de l'audit graphique, non tranché).
**Le code** :
- `lib/gedPieces.ts` : fonction NEUVE `dossierParMoment` (le moment en cours d'abord, puis les précédents ; une pièce une
  seule fois ; au passé, les reçues et les obligatoires non trouvées) -- `recuManque` non touchée ;
- `RecuManque.tsx` : deux propriétés neuves, `rangeEnListe` (cockpit seulement : plus de grille de feuilles ni de pastille
  « Lu par l'IA », les moments ne se cliquent plus) et `onDossier` (il transmet à la liste ce qu'il sait DÉJÀ : groupes,
  lectures en morceaux, « Revoir ce qu'il dit », « garder la lecture ») ; sans elles (fiche « classic ») : l'écran d'avant ;
- `App.tsx` (`ConsoleDocumentsPanel`, skin `v21`) : au filtre « Tous » (qui s'appelle « Le dossier » quand le rangement est
  là), les groupes dépliables (le moment en cours ouvert) ; une ligne par document (pièce, nom du fichier, 2 valeurs lues,
  état) ; dépliée : « Ce que l'IA a lu » puis la carte d'aujourd'hui (`carteDocument`, le MÊME texte qu'avant, sorti de la
  boucle) ; les manquantes à leur place avec « Déposer » (même geste que les feuilles) ; « Autres documents » pour le reste
  (calculé dans App : un document absent de chez Hektor ne se perd pas). « À préparer », « Signés », « Cloud » : la liste à
  plat d'aujourd'hui. Les négociateurs (interrupteurs GED en « admin ») voient la liste d'avant ;
- `RecuManque.css` : classes neuves `gd3-…`, couleurs de la charte.
**Contrôles** : `test_ged_dossier_range.cjs` **16 VERT** -- `docRowActions` et la carte IDENTIQUES AU CARACTÈRE à ceux du
commit `0022771` (lus dans git), suivi des signataires toujours monté 3 fois, fenêtres de signature inchangées, les deux
conditions, le classic intact, le rangement (moment en cours d'abord, une pièce une fois, aucun document perdu, comptes =
`recuManque`) ; témoin inverse (un espace ajouté dans la carte) : **2 ROUGE**. Les 15 autres essais GED verts (un « absent »
dans un commentaire avait fait sonner 3 essais : reformulé) ; les 5 essais de la signature demandés par sa session VERTS
(choix, état du mandat, expirée, pièces, suivi) ; `npm run build` passe. ⚠ **Pas vu à l'écran** : il faut le déploiement.
**✅ EN LIGNE le 20/11 (« Oui, pousse »)** : les 15 commits GED rejoués SEULS sur `origin/main` (rien du Classeur), l'arbre
rejoué essayé à part (essais GED et signature verts, build), poussé en `e1342f6` ; Vercel a servi la feuille neuve
(`var(--bv-magenta, #c5005f)`, `gd3-dossier`). **Vu dans le Chrome de Frédéric sur 18849 (62850), lecture seule** : « Le
dossier 20 », le Compromis ouvert, les pièces lues avec leurs pastilles, la carte d'aujourd'hui dans la ligne dépliée
(Ouvrir, Signature, Supprimer). ⚠ **Un défaut vu à l'écran et corrigé** : trois fichiers du MÊME nom (« Copie AAE PROMESSE… »)
revenaient chacun trois fois, et deux lignes se dépliaient ensemble -- le nom était répété dans la pièce. Corrigé (`9ba911a`,
un contrôle de plus dans l'essai, 17 verts), poussé et revu : **20 lignes pour 20 documents**, aucun doublon, 9 pièces
manquantes à leur place, **aucun élément ne déborde**. Restent à l'ancienne : « À remplir », « À regarder » et « Vrai / Faux /
Déjà su » (morceau 4).

### 12.62 VISUEL V3, MORCEAU 4 -- « À traiter » : Masquer à la place de la période de test (20/11, « Enchaîne ») -- ÉCRIT, PAS EN LIGNE

**Le code** (`RecuManque.tsx`, `lib/gedMesure.ts`, `RecuManque.css` ; s'applique au cockpit ET au classic : c'est le même bloc) :
- un en-tête **« À traiter »** magenta avec le NOMBRE (fenêtres « Ce que dit… » à ouvrir + propositions + points d'attention
  visibles) ; « À remplir » devient « À corriger ou compléter » ; « Voir et trancher » devient **« Voir et corriger »** (une
  valeur diffère) ou **« Voir et ajouter »** (cases vides) ;
- « À regarder » devient **« Points d'attention »** : une alerte qu'une fenêtre « Ce que dit… » montre déjà N'A PLUS SA CARTE
  (le même écart apparaissait deux fois, ex. 18849) ; **plus de « Vrai / Faux / Déjà su »** ; à la place **« Masquer »**
  (verdict `masque`, pour tout le monde sur le bien, à côté de « Déposer la pièce ») et, en bas, « N point(s) d'attention
  masqué(s) pour tout le monde -- Réafficher » (verdict `reaffiche` pour chacun) ;
- **seul « masque » masque** (`estMasquee`) : les 8 jugements vrai / faux du 17-19/11 ne cachent RIEN ; ⛔ correction de ma
  note du patch (§12.59), qui disait « tout autre dernier mot -> masqué » : c'est l'écran qui décide, et il ne masque que
  sur « masque » ;
- enregistrer une fenêtre « Ce que dit… » **n'écrit plus de note de mesure** (la boucle `verdictDesChoix` est retirée ; la
  fonction et ses essais restent dans la lib).
**Contrôles** : `test_ged_mesure.cjs` (§④ réécrit sur la décision : Masquer seulement si les jugements se lisent, plus de
barre, masque / reaffiche, le doublon retiré, plus de note à l'enregistrement, les anciens verdicts ne masquent rien) **26
VERT** ; témoin inverse (Masquer écrivant « vrai », doublon remis) **2 ROUGE**. Tous les autres essais GED et les 5 de la
signature verts ; `npm run build` passe. ⚠ Pas vu à l'écran : il faut le déploiement.
**✅ EN LIGNE (constaté le 26/11)** : le commit `7272556` était déjà dans `origin/main` -- une autre session a poussé la
branche locale entière entre le 20 et le 24/11 ; rien à pousser. La production sert `gm2-traiter-h`, `gm2-masquees`,
« Voir et corriger », « Masquage… ». **Vu dans le Chrome de Frédéric, lecture seule** : 18849 (62850) -- « À traiter 1 »,
« À corriger ou compléter (1) », « Voir et corriger », et l'alerte en double de la date de l'acte a DISPARU (plus de bloc
« Points d'attention ») ; EA32610 (59541) -- « Points d'attention (1) » : « Avenant : 2 mandants, 1 signature lue »,
« Déposer la pièce » et **« Masquer »** à côté, plus aucune barre « Vrai / Faux / Déjà su ». ⚠ **« Masquer » n'a PAS été
cliqué** : sur un bien réel il écrit dans le journal pour tout le monde ; l'essai demande une cible choisie par Frédéric.
**✅ ESSAI RÉEL de « Masquer » / « Réafficher » (26/11, « Sur EA32610 »)** : avant, 8 jugements, aucun sur 59541. **Masquer**
(09:14:10, heure de Paris) -> la carte « Avenant : 2 mandants, 1 signature lue » disparaît, « À traiter 0 », « Points
d'attention (0) », « 1 point d'attention masqué pour tout le monde -- Réafficher » ; en base, une ligne L10 `masque` au
nom de Frédéric. **Réafficher** (09:14:31) -> la carte revient avec « Déposer la pièce » et « Masquer », « À traiter 1 » ;
en base, une ligne `reaffiche` (le journal garde les deux, le plus récent fait foi). Aucun message d'erreur. Le bien est
revenu à son état d'avant l'essai (le point d'attention est visible). ⚠ Vu en passant : quand tout est masqué, l'en-tête
dit « À traiter 0 » -- il pourrait se taire ; non corrigé, à trancher.
**26/11 (« Oui, le cacher »)** : l'en-tête « À traiter » ne s'affiche plus quand il n'y a rien à traiter (tout masqué ou
fait) -- condition `nbATraiter > 0` ; la ligne « N point(s) d'attention masqué(s) -- Réafficher » reste. `test_ged_mesure`
27 VERT (un contrôle de plus), témoin inverse (`>= 0`) 1 ROUGE ; essais voisins verts ; build. Commité, PAS POUSSÉ.

### 12.63 VISUEL V3, MORCEAU 5 -- « Ce que dit… » à l'habit de la V3 (26/11, « Enchaîne ») -- ÉCRIT, PAS EN LIGNE

**Le code** (`BilanCompromis.tsx` : deux ajouts ; `BilanCompromis.css` : des règles AJOUTÉES en fin de fichier) :
- la **page du document s'ouvre d'office** à la première ligne à trancher qui a une page (sinon la première qui en a une) --
  plus de colonne vide « Touche « page » sur une ligne » ; ⚠ **pas au téléphone** (≤ 760 px), où la page remplace la liste ;
  sans document retrouvé, rien (point 2 du §5 de l'audit graphique) ;
- **en-tête clair** (blanc, titre encre) au lieu du bandeau noir ;
- la **plaque du document** (« Le compromis », « Le DPE »…) marquée magenta : la classe `is-document` que le code pose
  n'avait JAMAIS reçu de style (la CSS visait `is-compromis`, point 4 du §5) -- le papier beige n'est pas repris (V3) ;
- une écriture **réussie se signe d'une coche tracée** dans le pied ; une erreur, non.
**Rien de ce qu'elle écrit ne change** : `enregistrer` intact (un seul appel à `onEnregistrer`), mêmes chemins vers Hektor.
**Contrôles** : `test_ged_bilan_v3.cjs` **9 VERT** ; témoin inverse (page jamais ouverte d'office) **1 ROUGE** ; tous les essais
GED (bilan 137, socle 16…) et les 5 de la signature verts ; build. ⚠ Pas vu à l'écran : il faut le déploiement.
**✅ EN LIGNE le 26/11 (« Oui, pousse »)** : rejoué seul sur `origin/main`, l'arbre exact essayé à part (bilan v3 9, bilan 137,
socle 16, mesure 27, build), poussé en `c21ef1e` ; la production sert `bc-msg-coche`. **Vu dans le Chrome de Frédéric sur
18849, sans rien enregistrer** : « Voir et corriger » ouvre « Ce que dit le compromis » avec l'en-tête CLAIR, la plaque « Le
compromis : le 01/02/2027 » cadrée magenta (« correction ») face à « La transaction : le 23/01/2027 » barrée, et **la page 5
sur 38 ouverte d'office** dans la colonne de droite, dessinée en quelques secondes. Fermée par « Fermer ». La coche de réussite
n'a pas été vue (il aurait fallu enregistrer, donc écrire chez Hektor).

### 12.64 VISUEL V3, MORCEAU 6 -- la fenêtre de dépôt à l'habit de la V3 (26/11, « Enchaîne ») -- ÉCRIT, PAS EN LIGNE

**CSS seulement** (`DepotDocuments.css`, règles AJOUTÉES en fin de fichier ; `DepotDocuments.tsx` NON touché -- la fenêtre est
ouverte aux négociateurs depuis le 18/11, seul l'habit bouge) : en-tête CLAIR (sauf la feuille du téléphone, dont la poignée
blanche est faite pour un fond sombre) ; chaque fichier en petite page blanche à bande magenta ; les lignes en cartes (la
liste perd son cadre). **Pas fait dans ce morceau** : les animations de la maquette (les pages qui s'écartent à la
séparation, la barre qui se remplit fichier par fichier) -- elles demandent de toucher le composant, donc son code d'envoi ;
à décider à part.
**Contrôles** : `test_ged_depot_v3.cjs` **6 VERT** (dont « DepotDocuments.tsx non modifié ») ; témoin inverse (habit retiré)
**5 ROUGE** ; tous les essais GED verts ; build. ⚠ Pas vu à l'écran : il faut le déploiement.
**✅ EN LIGNE le 26/11 (« Oui, pousse »)** : rejoué seul sur `origin/main` avec la note du morceau 5, l'arbre exact essayé à part
(dépôt 33, socle 16, classement 37, lecture 62, build), poussé en `8d13a3c` ; la production sert la feuille neuve. **Vu dans le
Chrome de Frédéric sur 18849, sans rien déposer** : « Déposer des documents » s'ouvre avec l'en-tête CLAIR (titre encre,
pastilles « Compromis » et « Mandat 18849 » sur fond brume, croix claire), la zone « Glisse les fichiers ici » et la liste des
pièces non trouvées inchangées ; refermée par « Fermer ». Les lignes en cartes et les pages à bande magenta n'ont pas été vues
(il faut déposer un fichier).
