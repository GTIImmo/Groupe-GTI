# AUDIT — SIGNATURE ÉLECTRONIQUE EN PROPRE AVEC YOUTRUST

**Lundi 26/10/2026.** Demande de Frédéric : *« fais un audit de mon projet au sujet de la signature
électronique […] tu as tous les éléments pour dev une interaction API entre Youtrust et mon app
afin de remplacer Hektor pour l'envoi de mes PDF pour signature et aussi le retour […] j'attends
un rapport complet. »*

Tâche du plan maître : **A.2 — Signature en propre** (étape 3 ; lignes 32 et 33 du tableau
d'ordonnancement, `PLAN_DEV_ACTUALISE_2026-08-20.md`). **Lecture seule** : aucun code modifié,
aucun appel à Hektor ni à Youtrust, seulement des requêtes `SELECT` sur Supabase et la lecture
de fichiers locaux.

> **Audit limité à l'objet « document à signer » et à ses gestes de signature.** Les autres
> objets (annonce, contact, recherche, relation, transaction, RDV) ne sont **pas mesurés** ici ;
> le mandat n'est vu que comme document à signer (son registre et son numéro relèvent de A.3).

|  | créer | modifier | supprimer / annuler | lire / remonter |
|---|---|---|---|---|
| **document à signer** (mandat, avenant) | ✅ PDF fabriqué chez nous (worker, Chromium) · 🟡 avenant sans cases numérotées · ⛔ bon de visite imprimable seulement, ⛔ offre d'achat : aucun générateur | non mesuré *(un PDF généré ne se modifie pas : on en génère un autre)* | ✅ suppression du dépôt Hektor existe (`delete_document_from_hektor`) | ✅ coffre + `app_console_document` |
| **procédure de signature** | ⛔ **lancée à la main dans Hektor** — aucun code | ⛔ aucun geste *(changer un signataire = annuler et refaire)* | ⛔ annulation **via ImmoSign/Hektor** (`ImmoSign-deleteProcedure`) | ⛔ état lu dans le **HTML Hektor**, contexte négociateur requis |
| **signataire** | 🟡 liste calculée par l'app (`buildMandatSignatureRecipients`)… **jamais lue par le worker** | ⛔ | ⛔ | ⛔ progression « x/y » seulement, pas qui a signé |
| **relance** | ⛔ via ImmoSign/Hektor (`ImmoSign-remindProcedureSignatories`), toute la procédure | — | — | ⛔ |
| **PDF signé + preuves** | — | — | — | ⛔ ZIP via Hektor ; ✅ rangés chez nous ensuite (428 sur 429 ont leurs preuves, mesure du 21/10) |

---

## 0. EN UNE PAGE

```
CE QUE TU AS AUJOURD'HUI          ImmoSign = Yousign v3 en marque blanche, payé par Hektor
                                  -> 499 procédures, ~55 signées par mois depuis mars
                                  -> 498 sur 499 portent sur un document RÉDIGÉ DANS HEKTOR
                                  -> l'app sait suivre, relancer, annuler, rapatrier
                                  -> l'app ne sait PAS lancer une signature

CE QUE YOUTRUST EST               le MÊME moteur (api.yousign.app/v3), en direct
                                  -> même niveau juridique que tes signatures actuelles
                                     (signature simple + code SMS, prouvé par un audit trail)

CE QU'IL FAUT CONSTRUIRE          ~6 à 9 jours pour mandat + avenant :
                                  envoyer · recevoir l'état (webhook) · rapatrier signé + preuves
                                  · relancer · annuler · filet de rattrapage

LE VRAI CHEMIN CRITIQUE           pas le code : (1) tes négociateurs rédigent leurs mandats
                                  DANS Hektor, pas dans l'app ; (2) le volume (~1 800 crédits
                                  par an) dépasse les 500 inclus dans les offres affichées
```

**Verdict : faisable, et plus simple que tout ce qu'on a tenté avec ImmoSign.** Youtrust est une
API propre, documentée, avec un retour d'état en temps réel. Notre gabarit de mandat est en
HTML : on peut y poser des **ancres de texte invisibles** qui placent les cases de signature
toutes seules. Le problème de coordonnées qui avait fait abandonner l'automatisation ImmoSign
le 29/06 disparaît donc.

---

## 1. CE QUI ME MANQUE — À TRANCHER OU À FOURNIR

### 1.1 Ce que toi seul peux fournir (bloquant pour coder)

| # | Quoi | Pourquoi | Où le mettre |
|---|---|---|---|
| **M1** | **La clé API sandbox** — Youtrust > API > Clés API : environnement *Sandbox*, portée *organisation*, droits *Full-Access* | le mail n'en contient pas ; sans elle, aucun essai | `Console/.env`, sous le nom `YOUTRUST_API_KEY` *(ne pas me la coller dans le chat)* |
| **M2** | **La vraie date de fin d'essai** | tu dis 14 jours ; le mail **et** la doc disent **40 jours** | — |
| **M3** | **Les boîtes de test invitées comme utilisateurs** de ton organisation Youtrust | pendant l'essai, la sandbox **n'envoie qu'aux utilisateurs de l'organisation** ; 5 signataires au plus par demande | ta boîte au minimum, plus 1 ou 2 boîtes GTI pour jouer « mandant » et « négociateur » |
| **M4** | **La création du webhook dans l'app Youtrust**, le jour où je te donne l'URL | pendant l'essai, un webhook **ne se crée qu'à la main dans l'app**, pas par l'API | je te donnerai l'URL et la liste des événements à cocher ; Youtrust te donnera une **clé secrète** à mettre dans les secrets Supabase |

### 1.2 Les décisions qui sont les tiennes (voir §8 pour le détail et ma recommandation)

| # | Décision |
|---|---|
| **D1** | Le périmètre du premier lot : mandat + avenant seulement, ou aussi bon de visite et offre d'achat |
| **D2** | Le gabarit de mandat de l'app remplace-t-il le modèle Hektor « Mandat (Avec saisie du numéro) (Vente) » ? |
| **D3** | Qui signe : les mandants seuls, ou les mandants **et** le négociateur (c'est le cas aujourd'hui) |
| **D4** | Qui envoie les e-mails d'invitation : Youtrust (au nom « GTI Immobilier »), ou notre propre messagerie |
| **D5** | L'offre commerciale (Plus ou Pro) et le pack de crédits, vu le volume mesuré |
| **D6** | Où recevoir le webhook : Edge Function Supabase (ma recommandation) ou backend Render |

---

## 2. CE QUE TON APP FAIT AUJOURD'HUI — MESURÉ

### 2.1 Le circuit actuel

```
  APP                          HEKTOR                       IMMOSIGN (= Yousign v3)
  ───                          ──────                       ───────────────────────
  Générer le PDF du mandat ──► dépôt du document
  (job generate_mandat_document,
   Chromium, PDF A4)
  « Faire signer ? » Oui ────► onglet Hektor ouvert
                               le négo place le tampon ──►  procédure créée, e-mails, SMS
                               et envoie À LA MAIN
                                                            signature des parties
  suivi : lecture du HTML  ◄── page Documents du bien ◄──  webhook vers Hektor
  relance / annulation     ──► xmlrpc ImmoSign-*        ──►
  PDF signé + preuves      ◄── ZIP ImmoSign-download*
```

L'app ne parle **jamais** à Yousign. Le jeton ImmoSign se lit dans une iframe de Hektor, et
l'abonnement est **celui de Hektor** (fiche mémoire du 18/08). À la coupure, tout s'arrête.

### 2.2 Les chiffres (Supabase, `app_console_document`, 26/10)

| Mesure | Valeur |
|---|---|
| Procédures de signature connues | **499** (441 signées, **55 en attente**, 3 sans statut) |
| Signées par mois | févr. 2 · mars 58 · avr. 48 · mai 66 · juin 71 · juil. 51 · août 38 · sept. 60 · oct. 47 (au 26) |
| **Moyenne mars–oct.** | **~55 signatures par mois, soit ~660 par an** |
| Signataires par procédure | « x/2 » 18 fois, « x/3 » 24 fois, puis /4, /5, /6 → **~2,7 en moyenne** |
| **Procédures sur un document RÉDIGÉ DANS HEKTOR** (bloc ImmoSign, `doc_type 4`) | **498 sur 499** |
| Procédures sur un PDF **généré par l'app** | **1** (« Mandat de vente - 1.pdf », bien test 24113) |

Modèles Hektor réellement signés : « Mandat (Avec saisie du numéro) (Vente) » **465** ·
« Mandat (Avec saisie du numéro) » 7 · « Bon de visite (Vente) » 3 · environ vingt documents
libres nommés d'après un numéro de mandat. Modèles **rédigés** sans être tous envoyés :
674 mandats de vente, 16 autres mandats, **14 bons de visite**, 9 « Mandat (Vente ou Recherche) »,
**9 avenants**, 3 avis de valeur, **3 offres d'achat** ou transmissions d'offre, 1 protocole
Tracfin, 1 avenant de mandat d'agent commercial.

> ⚠ **C'est le constat le plus important de cet audit.** Remplacer Hektor pour la signature,
> ce n'est pas seulement « envoyer nos PDF à Youtrust ». Aujourd'hui, tes négociateurs
> **rédigent** leurs mandats dans l'éditeur de modèles de Hektor ; notre gabarit n'a servi
> qu'une fois. Sans Hektor, l'éditeur de modèles disparaît aussi. Le gabarit de mandat de
> l'app (`MandatDocumentEditor`, rubrique Mandat V3) doit donc devenir **le** mandat de GTI.
> → décision **D2**.

### 2.3 Le niveau juridique actuel — prouvé

J'ai lu l'audit trail d'une procédure signée (n° 305, bien 40608, mandat du 04/05/2026) :

- émetteur : **API**, organisation « MYLEGITECH SAS – IMMO SIGN SAS », *« Certified by yousign »* ;
- **authentification : SMS (OTP)**, consentement horodaté, *« signing process managed by the integrator »* ;
- **certificat Yousign**, OID `1.2.250.1.302.1.13.1.0`, horodatage qualifié : **non** ;
- 3 signataires : les 2 mandants **et la négociatrice** (adresse @gti-immobilier.fr) ;
- expiration : 6 mois après l'envoi.

C'est une **signature électronique simple (SES) avec code SMS**. Youtrust propose exactement
ce niveau : `signature_level: electronic_signature` avec `signature_authentication_mode: otp_sms`.
**Tu ne perds aucune valeur juridique en passant en direct.** *(Je ne donne pas d'avis juridique :
je constate que le niveau est identique.)*

### 2.4 Ce qui existe déjà dans le code — et se réutilise

| Brique | Où | Réutilisable ? |
|---|---|---|
| Gabarit mandat HTML + une case de signature par mandant **et** une pour le mandataire | `apps/hektor-v1/src/mandat-template.html` ; `mandatSignatureBlocksHtml` `App.tsx:4879` (`data-sign-area`) | ✅ on y ajoute les ancres |
| Gabarit avenant | `avenantPreviewHtml` `App.tsx:5041` — **sans** cases numérotées | 🟡 à compléter |
| PDF côté worker | `renderHtmlToPdfBuffer` `console_job_worker.js:7861` (Playwright Chromium) | ✅ |
| Job de génération du mandat | `handleGenerateMandatDocument` `:8126` → enchaîne aujourd'hui `upload_document_to_hektor` | ✅, à rebrancher vers Youtrust |
| **Liste des signataires** (nom, prénom, e-mail, téléphone, couples éclatés) | `buildMandatDocumentMandants` `App.tsx:4400`, `buildMandatSignatureRecipients` `:4450` | ✅ **déjà envoyée** dans `payload.destinataires` (`:4572`)… **mais le worker ne la lit pas** |
| Mandants lus depuis **notre registre** | `loadAnnonceMandants` `api.ts:9800` (`app_contact_relations_current`) | ✅ indépendant de Hektor |
| Badges d'état (à envoyer, en attente x/y, signé le…, annulé le…) | `SignatureBadge` `App.tsx:10222`, `MandatSignatureTracker` `:11047`, `ConsoleDocumentsPanel` `:11151` | ✅ |
| Boutons Relancer / Annuler / Ouvrir le signé | `:11124-11139`, `api.ts:8804/8834/8862` | ✅, à rebrancher |
| Rangement du PDF signé + preuves dans le coffre | `downloadSignedProcedureDocument` `:5658`, `metadata_json.signed_document` / `immosign_files` | ✅, même forme |
| Voie « signé à la main » | RPC `app_console_mark_document_signed_manual`, bouton `:11552` | ✅ reste telle quelle |
| Droits du négociateur sur relance et annulation | `patch_..._l2b_negociateur_documents_photos_2026-10-12.sql:133-136` | ✅ à étendre au nouvel envoi |

**Ce qui n'existe pas :** aucun appel Yousign, Youtrust ou DocuSign ; aucune variable
d'environnement dédiée ; **aucune route capable de recevoir un webhook** (ni FastAPI, ni Edge
Function : il n'y a que `admin-users` et `hektor-diffusion`) ; aucun job qui *lance* une
signature ; aucun générateur PDF d'offre d'achat ni de compromis ; le bon de visite n'est
qu'une **fenêtre imprimable** dans le navigateur (`visitVoucherHtml` `App.tsx:40415`).

---

## 3. CE QU'EST YOUTRUST — ANALYSÉ

### 3.1 Identité

**Youtrust est le nouveau nom de Yousign.** La doc s'intitule *« Youtrust Public API v3 »*, les
adresses sont `api-sandbox.yousign.app/v3` et `api.yousign.app/v3`, et les en-têtes de webhook
s'appellent `X-Yousign-*`. **C'est le même moteur que celui qu'ImmoSign utilise sous ta
signature actuelle.**

### 3.2 Les éléments techniques utiles

| Sujet | Ce que dit la doc |
|---|---|
| Authentification | `Authorization: Bearer {clé}` ; clé par environnement, portée organisation ou espace de travail, droits complets ou lecture seule |
| Environnements | Sandbox `https://api-sandbox.yousign.app/v3` · Production `https://api.yousign.app/v3`, totalement séparés |
| Le parcours | `POST /signature_requests` (brouillon) → `POST …/documents` (PDF, `parse_anchors=true`) → `POST …/signers` → `POST …/activate` |
| États d'une demande | `draft` · `ongoing` · `done` · `declined` · `expired` · `canceled` · `deleted` (+ `approval`, `rejected`, `paused`) |
| États d'un signataire | `initiated` → `notified` → `signed` (ou `declined`, `error`) |
| **Placement des cases** | **ancres intelligentes** : du texte dans le PDF, par exemple `{{s1\|signature\|170\|60}}`, de la couleur du fond, sur une seule ligne, en Arial de 10 à 14 px ; ou coordonnées x/y depuis le coin haut-gauche |
| Mentions | `{{s1\|mention\|Lu et approuvé le %date%\|M1}}`, date de signature, nom, initiales, cases à cocher… |
| Niveaux | simple (`electronic_signature`) · avancée (vérification de pièce d'identité, à activer par le support) · qualifiée (vidéo) |
| Codes | `no_otp`, `otp_email`, `otp_sms` (SMS : numéro E.164 obligatoire) |
| Relances | automatiques (tous les 1, 2, 7 ou 14 jours, de 1 à 10 fois) **et** manuelles (`POST …/signers/{id}/send_reminder`) |
| Annulation | `POST …/cancel` (si `ongoing`) — définitive ; il faut recréer une demande |
| PDF signé | `GET …/documents/download?version=completed` (PDF, ou ZIP avec `archive=true`) |
| Preuves | audit trail **par signataire** : PDF `GET …/signers/{id}/audit_trails/download`, JSON aussi ; **conservé 10 ans** par Youtrust (Arkhineo) |
| Identifiant à nous | `external_id` (renvoyé dans les webhooks) + métadonnées libres |
| Expéditeur des e-mails | nom de l'organisation, de l'espace de travail ou nom libre ; texte d'invitation et de relance personnalisable (texte brut) |
| Webhooks | HTTPS public ; signature **HMAC-SHA256** dans `X-Yousign-Signature-256` ; **répondre en 2xx en moins d'1 seconde** (10 s pour les nouvelles tentatives) ; 8 nouvelles tentatives étalées sur environ 4 jours ; dédoublonner par `event_id` ; adresses d'origine `57.130.41.144/28` |
| Événements utiles | `signature_request.activated`, `.done`, `.canceled`, `.declined`, `.expired`, `.reminder_executed` ; `signer.notified`, `signer.done`, `signer.declined`, `signer.error`, `signer.notification_delivery_failed` |
| Débit | Sandbox **30/min et 200/h** (+ 100 demandes activées par jour pendant l'essai) · Production **60/min et 1 200/h** |
| Limites | 50 Mo par document · 50 documents et **100 signataires** par demande (**5 pendant l'essai**) |

### 3.3 Les contraintes de l'essai à connaître avant de coder

- **40 jours** de sandbox, pas de production pendant l'essai.
- Documents **filigranés**, signatures **sans valeur légale**.
- **Envois limités aux utilisateurs de ton organisation** (→ M3).
- **Webhook à créer à la main** dans l'app (→ M4).
- Certaines options sont réservées aux abonnés (l'« expérience personnalisée » avec logo et
  couleurs relève de l'offre Pro).
- La doc **déconseille les tests automatiques** sur la sandbox : nos tests de non-régression
  devront simuler Youtrust, pas l'appeler.

### 3.4 Le seul doute technique — et pourquoi il est faible

La page « Document » de la doc exige un PDF **en version 1.6 ou plus** pour un document à
signer ; la page « Limits » dit *« any PDF version »*. Or **nos mandats sortent en PDF 1.4**
(vérifié sur 3 fichiers : en-tête `%PDF-1.4`, producteur `Skia/PDF m149` et `m150`).
**Témoin positif :** le seul mandat de l'app passé chez ImmoSign — donc chez Yousign v3 — a été
**signé** sans encombre. Le risque est faible, mais **c'est le premier essai à faire** en
sandbox. Repli si besoin : l'option `flatten` à l'envoi, ou réenregistrer le PDF en 1.7 avant
l'envoi (quelques lignes).

### 3.5 Le prix — à faire chiffrer

Grille publique (HT, engagement de 12 mois) : **Plus 104 €/mois**, **Pro 129 €/mois**, **500
signatures simples incluses par an** ; Scale sur devis. **Un crédit est décompté par
signataire, à l'envoi**, même si la personne ne signe pas.

```
~55 procédures par mois × ~2,7 signataires  ≈  150 crédits par mois  ≈  1 800 par an
                                               500 inclus  ->  ~1 300 à acheter en pack
```

Le prix du pack n'est pas public (*« sur devis »*). **Si le négociateur ne signe plus (D3),
on passe à environ 1,7 signataire, soit ~1 100 crédits par an.** Les SMS de code et
l'archivage légal (Pro, facturation annuelle seulement) ne sont pas chiffrés non plus. → **D5 :
demander un devis** avec ces volumes. *(Ce n'est pas un conseil financier : ce sont tes
volumes mesurés, pour que le devis soit juste.)*

---

## 4. L'ARCHITECTURE QUE JE PROPOSE

### 4.1 Le circuit cible

```
  APP (navigateur)               WORKER documents                YOUTRUST
  ────────────────               ────────────────                ────────
  Générer le mandat  ─job─►  PDF Chromium + ancres
  « Envoyer en signature »       (cases placées seules)
  (liste des signataires ─job─►  youtrust_send :
   vérifiée, coût annoncé)       créer → PDF → signataires ──────►  demande « ongoing »
                                 → activer                         e-mails + SMS
                                 écrit app_signature_request
                                                                   le client signe
                      EDGE FUNCTION youtrust-webhook  ◄──────────  webhook signé HMAC
                      (vérifie, range, répond en <1 s)
                                 │ app_signature_event
                                 ▼
                         WORKER youtrust_fetch_signed
                         PDF signé + audit trails ──► coffre (bucket) + metadata_json
  badges « En attente 1/3 »  ◄── vues existantes
  « Signé le … », Ouvrir, Preuves
  Relancer / Annuler  ─job─►  send_reminder / cancel ──────────►
                         FILET QUOTIDIEN youtrust_reconcile : relit toute demande non
                         terminée (un webhook perdu ne fige jamais un état)
```

### 4.2 Les choix, et pourquoi

1. **Le worker parle à Youtrust, jamais le navigateur.** La clé API reste secrète
   (`Console/.env`), et on garde le modèle « l'app demande un job, le worker exécute »
   qui tient tout le projet.
2. **Les ancres plutôt que les coordonnées.** Notre PDF sort de HTML, donc il contient du
   vrai texte — ce qui manquait dans la visionneuse ImmoSign, uniquement en canvas.
   `mandatSignatureBlocksHtml` écrit une ancre blanche dans chaque case :
   mandant 1 → `{{s1|signature|170|60}}`, mandant 2 → `{{s2|…}}`, négociateur → `{{sN|…}}`.
   L'ordre des signataires créés doit être **le même** que celui des cases : c'est la seule
   règle à verrouiller. Ajout possible : `{{s1|mention|Bon pour mandat|M1}}`.
3. **Le webhook dans une Edge Function Supabase**, pas sur Render. Youtrust exige une réponse
   **en moins d'une seconde**, et Render met du temps à démarrer à froid (CLAUDE.md : « Render
   chaud ce matin »). L'Edge Function ne fait que trois choses : vérifier la signature HMAC,
   insérer l'événement (clé unique `event_id` = idempotence), répondre 200. Le travail lourd
   — télécharger le PDF signé et les preuves — est confié au worker par un job.
4. **Un filet quotidien.** Fiche mémoire « une lecture ratée n'est jamais un vert » : si un
   webhook se perd (Edge Function en panne, 4 jours de nouvelles tentatives épuisés), le
   passage de nuit relit chaque demande `ongoing` par `GET /signature_requests/{id}` et
   rattrape. Coût : quelques dizaines d'appels par nuit, très loin des 1 200 par heure.
5. **Une table dédiée, plus un miroir dans `metadata_json.signature`.** La table porte la
   vérité ; le miroir garde intacts les badges et boutons existants, qui lisent déjà
   `status`, `progress`, `signed_at` et `procedure_id`.
6. **ImmoSign et Youtrust cohabitent** avec un champ `provider`. Les **55 procédures ImmoSign
   en cours** continuent d'être suivies par le code actuel jusqu'à leur fin. Rien n'est retiré
   avant la coupure.

### 4.3 Les données (migration à écrire)

```
app_signature_request                      app_signature_event
─────────────────────                      ───────────────────
id uuid                                    event_id text UNIQUE   (dédoublonnage)
provider 'youtrust' | 'immosign'           event_name text
provider_request_id text UNIQUE            provider_request_id text
app_console_document_id uuid               payload jsonb
app_dossier_id bigint                      received_at timestamptz
document_kind 'mandat' | 'avenant' | …     processed_at timestamptz
status draft|ongoing|done|declined|        erreur text
       expired|canceled|failed
signers jsonb  [{index, role, nom, email,
  phone, provider_signer_id, status,
  signed_at}]
requested_by uuid (auth.users)
activated_at, done_at, canceled_at
signed_storage_path, proofs jsonb
sandbox boolean
created_at, updated_at
```

Nouveaux types de travaux — **les trois verrous** (fiche mémoire du même nom) : la CHECK
`app_console_job_job_type_check`, la distribution `app_console_claim_next_job` (worker
`documents`), le worker (liste `DOCUMENT_JOB_TYPES` + `switch` + redémarrage) ; **plus** les
droits `app_console_can_request_job` et le type `ConsoleJobType` du front (déjà en retard sur
le worker, à rattraper au passage).

| Job | Rôle |
|---|---|
| `youtrust_send_signature` | créer, déposer le PDF, ajouter les signataires, activer ; écrire la demande |
| `youtrust_fetch_signed` | après `done` : PDF signé + un audit trail par signataire → coffre |
| `youtrust_remind_signer` | relance manuelle d'un signataire (`notified` seulement) |
| `youtrust_cancel_signature` | annulation (`ongoing` seulement) |
| `youtrust_reconcile` | filet de nuit |

### 4.4 Les points de vigilance déjà connus

- **Le coffre n'accepte que certains types de fichiers** (fiche « le coffre refuse un type »).
  Le PDF passe ; un ZIP de preuves ne passe que si `application/zip` figure dans la liste
  blanche réelle du bucket (ajouté à la main le 18/08, mais absent du fichier SQL du dépôt).
  Je propose de ranger les audit trails **en PDF un par un** : plus de dépendance au ZIP.
- **Le PDF signé ne doit pas écraser l'original** : même garde-fou que le lot ImmoSign
  (`storage_path` vers `signed/…`, contrôle `file_size` contre `signed_document.size`).
- **Le téléphone en E.164** (`+33…`) est obligatoire pour le code SMS : à contrôler **avant**
  l'envoi, avec un message clair si un mandant n'a pas de portable.
- **Un couple = deux signataires** (`buildMandatDocumentMandants` éclate déjà les couples).
- **Avant chaque envoi, l'app affiche le coût** (« 3 signataires = 3 crédits ») : un envoi
  consomme des crédits même s'il est annulé ensuite.
- **Ne pas autoriser le refus** (`signers_allowed_to_decline: false`), comme aujourd'hui : le
  client ne peut pas refuser, le commercial peut annuler.

---

## 5. CE QUE FAIT CHAQUE ÉCRAN APRÈS LE CHANTIER

| Geste | Aujourd'hui | Après |
|---|---|---|
| Générer le mandat | PDF → dépôt Hektor | PDF → coffre (dépôt Hektor optionnel tant qu'il vit) |
| Envoyer en signature | onglet Hektor, tampon et envoi à la main | une fenêtre dans l'app : signataires (nom, e-mail, portable), coût, **Envoyer** |
| Voir l'état | lecture du HTML Hektor, parfois une nuit de retard | en temps réel : « En attente 1/3 », qui a signé, quand |
| Relancer | toute la procédure | **par signataire**, avec relances automatiques réglables |
| Annuler | xmlrpc Hektor | `cancel` Youtrust, puis renvoi possible avec une nouvelle demande |
| Récupérer le signé | ZIP Hektor, choix du plus gros PDF | PDF signé et preuves séparés, sans devinette |
| Preuves | ZIP | un audit trail PDF par signataire, conservé aussi 10 ans chez Youtrust |

---

## 6. LE DÉCOUPAGE EN LOTS ET L'EFFORT

| Lot | Contenu | Effort | Dépend de |
|---|---|---|---|
| **0** | Prérequis : clé, utilisateurs invités, secret Supabase | 0,5 j (toi) | M1, M3 |
| **1** | Client Youtrust dans le worker + **essai de bout en bout en sandbox** sur le PDF 1.4 (créer → activer → signer → télécharger) | 1–1,5 j | 0 |
| **2** | Ancres dans le mandat ; cases numérotées et ancres dans l'avenant | 0,5–1 j | 1 |
| **3** | Migration : 2 tables, 5 types de travaux, droits, miroir `metadata_json` | 1 j | 1 |
| **4** | Edge Function webhook + traitement worker (signé + preuves) | 1–1,5 j | 3, M4 |
| **5** | Front : fenêtre d'envoi, suivi par signataire, relance, annulation, preuves | 1,5–2 j | 3 |
| **6** | Filet de nuit + ligne du moniteur (lire les CHECK de la table d'abord) | 0,5–1 j | 4 |
| **Total mandat + avenant** | | **6 à 9 jours** | |
| *7 (hors lot)* | *bon de visite en PDF worker, offre d'achat : tâche 31 du plan* | *6–9 j* | *D1* |
| *8 (hors lot)* | *passage en production : clé de prod, webhook prod par l'API, essai réel sur ta boîte* | *0,5 j* | *contrat* |

Ordre conseillé : **lot 1 d'abord, dès réception de la clé.** Il lève en une heure les deux
seuls doutes (PDF 1.4, ancres reconnues dans notre gabarit) avant d'écrire la moindre migration.

Le plan maître prévoyait 4–8 j + 6–10 j pour A.2 (parties 1 et 2, cette dernière incluant
« prolonger un mandat »). Mon chiffrage tient dans la partie 1 ; il ne couvre pas la
prolongation de mandat (fiche mémoire « ne pas modifier ni prolonger un mandat » : sujet fermé).

---

## 7. CE QUE LES 40 JOURS PERMETTENT — ET LEUR LIMITE

L'essai suffit pour **tout développer et tout éprouver** (lots 1 à 6), à condition que la clé
et les utilisateurs soient là dans les premiers jours. Il ne permet **pas** de signer un vrai
mandat : il faut l'abonnement. **Le contrat est donc le chemin critique** (plan, §« les
contrats démarrent à la fin »). Si tu veux couper Hektor juste après le développement, la
négociation du devis (D5) doit commencer **pendant** l'essai, pas après. Et à la fin de
l'essai sans abonnement, **la sandbox elle-même se ferme**.

---

## 8. LES DÉCISIONS — AVEC MA RECOMMANDATION

| # | Question | Ma recommandation | Pourquoi |
|---|---|---|---|
| **D1** | Périmètre du 1er lot | **Mandat + avenant** | 472 signatures sur 499 sont des mandats ; l'avenant suit la même chaîne ; le bon de visite (3 signatures) et l'offre (0) relèvent de la tâche 31 |
| **D2** | Le gabarit de l'app devient le mandat de GTI | **Oui, mais à faire valider sur le fond par toi** (et ton conseil si besoin) avant le lot 5 | aujourd'hui 465 mandats viennent du modèle Hektor ; sans Hektor, il n'y a plus de modèle |
| **D3** | Le négociateur signe-t-il ? | **Oui, comme aujourd'hui** | même valeur que l'existant ; c'est lui le mandataire ; coût ~+40 % de crédits, à arbitrer avec D5 |
| **D4** | Qui envoie les e-mails | **Youtrust**, expéditeur au nom « GTI Immobilier » | relances, échecs de remise, preuves d'envoi gérés pour nous ; notre messagerie reste libre |
| **D5** | Offre | **Devis Plus vs Pro avec 1 100 à 1 800 crédits par an** | les webhooks et les ancres sont dans Plus ; Pro ajoute logo et couleurs, journaux API et archivage légal |
| **D6** | Webhook | **Edge Function Supabase** | réponse en moins d'1 s exigée ; Render démarre à froid |

---

## 8 bis. SUIVI DU 26/10 — LES RÉPONSES DE FRÉDÉRIC

| | Réponse | Mesure |
|---|---|---|
| **M1** clé | posée dans `Console/.env` (`YOUTRUST_API_KEY`) | ✅ **acceptée** : `GET /signature_requests`, `/users`, `/workspaces` → HTTP 200 (lecture seule) ; 0 demande, 1 espace « Gti-immobilier » |
| **M2** durée | ⚠ **il reste 14 jours**, soit une fin vers le **09/11/2026** | — |
| **M3** utilisateurs | ok, à inviter | ⚠ **1 seul utilisateur aujourd'hui** (Frédéric, owner). Une demande à 2 mandants + 1 négociateur exige **3 boîtes différentes** invitées |
| **M4** webhook | ok, à créer dans l'app le jour venu | — |
| **D1** | ✅ **oui à la recommandation** : mandat + avenant d'abord | — |
| **D2** | ✅ **oui** — *« je l'ai déjà entièrement fait, mais attention : uniquement à la coupure »* | ⇒ **tout le circuit Youtrust reste DORMANT derrière un interrupteur jusqu'à la coupure** ; d'ici là, le modèle Hektor et ImmoSign continuent comme aujourd'hui |
| **D3** | ✅ **oui** : le négociateur signe | ⇒ ~2,7 signataires par mandat, ~1 800 crédits/an |
| **D4** | ❓ *« je sais pas »* | expliqué le 26/10, à trancher |
| **D5** | ⏳ le commercial Youtrust le recontacte **à la fin de l'essai** | lui donner les volumes du §3.5 |
| **D6** | ❓ demande d'explication | expliqué le 26/10 (le « webhook » = l'avis que Youtrust nous envoie à chaque changement d'état) |
| **Lot 1** | ✅ **« vas-y »** le 26/10 | voir §8 ter |

## 8 ter. LOT 1 — L'ESSAI DE BOUT EN BOUT EN SANDBOX (26/10)

Deux fichiers neufs, **dormants** (aucun handler du worker ne les appelle) :
`Console/youtrust_client.js` (client de l'API, sandbox par défaut, vérification HMAC des
webhooks) et `Console/essai_youtrust_sandbox.js` (`--envoyer` puis `--suivre`, signataire limité
à la boîte de Frédéric, refus hors sandbox). Mandat **fictif**, mêmes classes CSS que
`mandatSignatureBlocksHtml`, rendu par le même Chromium.

| Contrôle | Résultat |
|---|---|
| PDF fabriqué | 61 281 octets, **`%PDF-1.4`** |
| Document accepté par Youtrust | ✅ **oui** — le doute du §3.4 tombe : le 1.4 passe |
| Ancres détectées (`total_anchors`) | ✅ **2 sur 2** (mandant 1 et mandataire) |
| Champ créé à l'activation | ✅ **1** — page 2, x 43, y 86, 150 × 45, rattaché au seul signataire ; l'ancre `s2` est ignorée faute de 2ᵉ signataire, **comme la doc l'annonce** |
| Statut après activation | ✅ `ongoing`, invitation envoyée à la boîte de Frédéric |
| Signature par Frédéric | ✅ code e-mail validé 10:46:35, consentement 10:46:39, terminé 10:46:40 → demande `done`, signataire `signed` |
| PDF signé (`version=completed`) | ✅ 75 337 octets, `application/pdf`, filigrane « Sandbox » |
| Audit trail (par signataire) | ✅ 96 835 octets, **en français** (`audit_trail_locale: fr`) |
| **Intégrité** | ✅ sha256 de NOTRE PDF = « empreinte initiale » de l'audit trail (`f0ff4f81…`) ; sha256 du PDF téléchargé = « empreinte » de la signature (`7f451175…`) — **à l'octet** |
| Même politique de certificat qu'ImmoSign | ✅ OID **`1.2.250.1.302.1.13.1.0`**, comme l'audit trail ImmoSign de la procédure 305 ; certificat de **test** « Yousign - Test » en sandbox |
| Signature cryptographique dans le PDF | ⚠ **absente en sandbox** (0 `/ByteRange`) — **c'est annoncé par la doc** (*« the legal Signature is not present »*). À revérifier au premier envoi de production |

Demande sandbox : `68fc07cf-08c8-4ca3-b329-b645baba1051`.

**Remarque de Frédéric (26/10) : « la société n'a pas signé, la case du groupe GTI est vide ».**
Exact, et voulu dans ce 1er essai : un seul signataire, donc l'ancre `s2` (mandataire) a été
ignorée sans erreur. ⭐ Mesuré sur un brouillon aussitôt supprimé : **Youtrust accepte la même
adresse pour deux signataires**. 2ᵉ essai (`--deux-signataires`, `ordered_signers: true`) :
demande `e118c748-5500-4ce0-98b8-d3b723b1f6f2`, **2 ancres → 2 champs**, page 2 : mandant
x 43, **mandataire x 310**, chacun sur son signataire. ✅ **Signé dans l'ordre** : mandant 10:51:07, puis mandataire
10:51:58 (le 2ᵉ e-mail n'est parti qu'après la 1ʳᵉ signature) → demande `done`, 2 signataires
`signed`. PDF signé 87 706 octets ; **un audit trail par signataire** (99 088 et 99 068 octets).
⭐ **La chaîne d'empreintes est complète** : notre PDF `56e2813a…` → après le mandant
`f50d6bb7…` → après le mandataire `3988e7e1…` = **le PDF téléchargé, à l'octet**. Chaque
signature s'appose sur la précédente : rien ne peut être glissé entre deux signataires. ⚠ **Leçon pour le lot 2 :** une ancre sans signataire ne lève AUCUNE erreur.
Le worker devra donc contrôler, après l'activation, que **le nombre de champs créés égale le
nombre de signataires** — sinon annuler la demande et signaler, jamais laisser partir un
mandat sans la case GTI.

**➡ LOT 1 VERT.** Les deux doutes de l'audit sont levés par la mesure : le PDF 1.4 de Chromium
passe, et les ancres posées dans nos cases sont reconnues et placent le champ au bon endroit.
⚠ **Ce que l'essai n'a PAS couvert :** plusieurs signataires (un seul utilisateur dans
l'organisation), le code SMS, le webhook, la relance et l'annulation. Ce sont les lots 3 à 5.

## 8 quater. ⛔ LA GARANTIE DEMANDÉE PAR FRÉDÉRIC (26/10)

*« Tu me confirmes que tout ce chantier n'écrase pas le système actuel tant qu'il ne sera pas
opérationnel et mon accord ? »* — **Oui**, vérifié par `git status` le 26/10 après le lot 1 :
worker, front, `supabase/`, `scheduled/`, backend **non modifiés** ; aucune écriture en base ;
aucun appel à Hektor ; aucun redémarrage ni déploiement. Les deux fichiers neufs ne sont
appelés par personne.

**Règles pour tous les lots suivants :**
1. Le circuit Youtrust est **éteint par défaut, derrière un interrupteur** ; il ne s'allume
   qu'à la coupure, sur l'accord de Frédéric (D2).
2. **Rien d'ImmoSign n'est retiré** avant la coupure : bouton vers Hektor, lecture des états,
   relance, annulation, suivi des procédures en cours.
3. Les **ancres** du gabarit de mandat (lot 2, seul fichier existant touché) ne sont écrites
   **que si l'interrupteur est allumé** : éteint, le PDF reste identique à l'octet près à celui
   d'aujourd'hui (à prouver par comparaison au lot 2).
4. Types de travaux et tables **ajoutés**, jamais modifiés ; chaque migration a son inverse.
5. **Accord explicite** avant : chaque lot de code, tout patch en production, tout redémarrage,
   tout déploiement, l'allumage de l'interrupteur, et l'usage d'une clé de **production**.

## 9. CE QUE CET AUDIT N'A PAS FAIT

- Aucun appel à Youtrust (pas de clé) ni à Hektor.
- La page des tarifs ne donne ni le prix du pack, ni celui des SMS, ni celui de l'archivage.
- La valeur juridique du gabarit de mandat de l'app face au modèle Hektor n'est pas de mon
  ressort (D2).
- La liste blanche **réelle** des types du bucket n'a pas été relue en base (seulement le
  fichier SQL du dépôt).
- Le sort des 55 procédures ImmoSign en cours à la coupure reste le sujet du plan (liste A.2
  et E.1 : « solder les signatures en cours »).

*Sources : documentation `developers.youtrust.com` (index `llms.txt`, pages mises à jour du
07/09 au 19/10/2026), page tarifs `youtrust.com/fr-fr/prix-api`, base Supabase (26/10),
`console_job_worker.js`, `App.tsx`, `api.ts`, `mandat-template.html`, fiches mémoire ImmoSign
du 29/06 au 18/08.*
