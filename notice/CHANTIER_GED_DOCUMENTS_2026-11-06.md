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
