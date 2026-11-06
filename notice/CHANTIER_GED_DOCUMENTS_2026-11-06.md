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

### 5.4 L'ordre recommandé
GED-1 nomenclature (validée par Frédéric) → GED-2 fiche à part + GED-3 classement du stock (base seule, rien à l'écran)
→ GED-5 la porte « trouver », d'abord pour les besoins neufs (copropriété du syndic, pré-état daté), puis à la place des
anciennes règles → GED-4 l'outil d'ajout (après les lots signature) → complétude et dates d'expiration → plus tard :
lien de dépôt pour le client, lecture du contenu des PDF, bons de visite rangés comme documents.
