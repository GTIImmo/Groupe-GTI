# PLAN DE DEV — SIGNATURE ÉLECTRONIQUE EN PROPRE AVEC YOUTRUST (tâche A.2)

**Écrit le 26/10/2026**, à la demande de Frédéric : *« je veux faire un plan de dev précis au
sujet de Youtrust »*. Il s'appuie sur l'audit `notice/AUDIT_SIGNATURE_YOUTRUST_2026-10-26.md`
(mesures, doc Youtrust, décisions) : **ce plan ne le répète pas, il en tire les lots.**

> **Rien de ce plan n'est codé, sauf le lot 1** (`11e569f`). Chaque lot suivant attend un
> « vas-y » explicite, précédé de l'explication du lot (méthode du CLAUDE.md §0).

---

## 0. LE BUT, EN TROIS PHRASES

1. **GTI fait signer ses mandats et avenants par ses propres moyens**, depuis l'app, avec son
   propre contrat Youtrust — plus par ImmoSign, qui appartient à l'abonnement Hektor.
2. **L'app suit et range tout elle-même** : qui a signé, quand, relance, annulation, mandat
   signé et preuves dans le coffre.
3. **Rien de ce qui marche aujourd'hui n'est cassé** : la lecture des signatures Hektor et
   ImmoSign continue, et tous les mécanismes de l'app lisent les deux systèmes de la même façon.

---

## 1. LES DÉCISIONS QUI CADRENT LE PLAN (toutes de Frédéric, 26/10)

| # | Décision |
|---|---|
| D1 | Mandat + avenant d'abord ; bon de visite et offre d'achat = tâche 31, plus tard |
| D2 / **D11** | Le mandat **de l'app** est le mandat envoyé à Youtrust — **dès l'allumage** (D11 = A) |
| D3 | Le négociateur signe (il est le mandataire) |
| D5 | Offre et pack de crédits : avec le commercial Youtrust **en fin d'essai** (~09/11) |
| D6 | Les avis de Youtrust arrivent dans une **fonction Supabase** *(recommandation, non contredite)* |
| **D7** | **Les mandants d'abord, en parallèle ; le négo contresigne une fois tous signés** |
| **D8** | Le négo signe **depuis l'app**, **l'e-mail en repli** |
| **D9** | **Signature sur place**, sur tablette, en rendez-vous |
| D10 | Pièces demandées au mandant + logo GTI : **si l'offre Pro** est retenue |
| **Calendrier** | **Un seul interrupteur, pour TOUS les utilisateurs**, allumé **dès que le contrat est signé et les lots prouvés — AVANT la coupure** |
| **ImmoSign** | **Plus aucune procédure neuve après l'allumage** ; la lecture Hektor finit les procédures en attente (55 le 26/10) et **n'est jamais coupée**, même vide |
| D4 | Les e-mails sont envoyés **par Youtrust** *(conséquence de D8 : l'e-mail est le repli)* |

---

## 2. LA COLONNE VERTÉBRALE — UNE LANGUE COMMUNE, DEUX ÉCRIVAINS

Tout le projet lit l'état de signature à **un seul endroit** : `app_console_document.
metadata_json.signature` *(mesuré le 26/10 : badges, suivi mandat, onglet Documents,
Mandat V3, fil d'activité du cockpit, signé à la main — détail : audit §8 bis-3)*.

```
          metadata_json.signature  =  {status, progress, sent_at, signed_at,
                                       cancelled_at, procedure_id, …}
          + provider : 'immosign' | 'youtrust' | 'manuscrite'      ← le SEUL ajout
          + provider_request_id  (identifiant Youtrust)             ← pour 'youtrust'
                 ▲                                    ▲
   ÉCRIVAIN 1 — EXISTANT, GARDÉ             ÉCRIVAIN 2 — NOUVEAU
   lecture Hektor / ImmoSign                avis Youtrust + rattrapage de nuit
   (jamais coupée)                          (nos documents envoyés par Youtrust)
                 └──────────────┬─────────────────────┘
                   TOUS LES LECTEURS — INCHANGÉS
```

**Règle R1 — un document = un fournisseur ; un écrivain ne touche que les siens.**
Un mandat Youtrust est aussi **déposé chez Hektor** (Hektor reste à jour tant qu'il vit) :
la lecture Hektor relirait sa ligne et **écraserait** l'état Youtrust par « à envoyer ».
→ garde-fou dans l'écrivain 1 : il ne réécrit jamais `signature` quand `provider = 'youtrust'`.

**Règle R2 — les boutons s'aiguillent selon le fournisseur.** Un document Youtrust ne porte
**pas** `procedure_id` (réservé à ImmoSign) ; « Relancer », « Annuler », « Ouvrir le signé »
choisissent leur travail selon `provider`.

**Règle R3 — traduction des états Youtrust dans les mots existants.**

| Youtrust | Langue commune |
|---|---|
| `draft` | `to_send` |
| `ongoing` | `pending` + `progress` « signés / total » |
| `done` | `signed` + `signed_at` |
| `canceled` | `cancelled` + `cancelled_at` |
| `expired` | **`expired`** *(seul mot neuf : badge à compléter)* |
| activation | `sent_at` |

---

## 3. LE DÉROULEMENT, VU PAR LE NÉGOCIATEUR (interrupteur allumé)

```
FICHE ANNONCE › rubrique Mandat
 ① Générer le mandat (ou l'avenant)     PDF de l'app, cases numérotées + repères invisibles
 ② « Envoyer en signature »             fenêtre : mandants (nom, e-mail, PORTABLE) + toi ;
                                         « 3 signataires = 3 crédits » ;
                                         [ Par e-mail ]  ou  [ Sur place, sur la tablette ]
 ③ Envoyer
    ÉTAPE 1 — LES MANDANTS, EN PARALLÈLE
      par e-mail : chacun reçoit son lien, code par SMS, signe quand il veut
      sur place  : chaque mandant signe à son tour sur la tablette, dans l'app
    ÉTAPE 2 — LE NÉGO (quand TOUS les mandants ont signé)
      cloche « À vous de contresigner » + bouton « Signer maintenant » dans l'app
      (+ l'e-mail Youtrust dans sa boîte, en repli)
 ④ « Signé le … »                       mandat signé + 1 dossier de preuves par signataire
                                         dans l'onglet Documents ; déposé chez Hektor
 Entre-temps : « En attente 1/3 » · qui a signé · Relancer (par personne) · Annuler
```

---

## 4. LE CATALOGUE DES OPÉRATIONS

| # | Opération | Déclencheur | Lot |
|---|---|---|---|
| O1 | Préparer le PDF signable (repères dans chaque case) | « Générer » | 2 |
| O2 | Envoyer : créer, déposer le PDF, signataires dans l'ordre D7, activer | négo | 4 |
| O3 | Contrôler l'envoi : nb de champs = nb de signataires, sinon annuler + alerte | auto | 4 |
| O4 | Recevoir les avis (signé, tout signé, annulé, expiré, e-mail non remis) | Youtrust | 5 |
| O5 | Rapatrier le PDF signé + 1 audit trail par signataire → coffre (+ dépôt Hektor) | auto | 5 |
| O6 | Relancer **un** signataire | négo | 6 |
| O7 | Annuler la demande | négo | 6 |
| O8 | Contresigner depuis l'app (« Signer maintenant ») | négo | 6 |
| O9 | Signature sur place (tablette) | négo | 6 bis |
| O10 | Rattrapage de nuit des demandes non terminées | tâche planifiée | 7 |
| O11 | Alertes : e-mail non remis, envoi en échec, avis absents | auto | 5 · 7 |
| O12 | **Lecture Hektor / ImmoSign — CONSERVÉE** (finit les procédures en attente) | existant | — *(R1 seulement)* |

---

## 5. LES LOTS

> Pour chaque lot : **ce qu'il fait · les fichiers · ce que ça pourrait casser ailleurs ·
> le retour arrière · la preuve · ce qui exige l'accord de Frédéric.**
> Ordre imposé : **2 → 3 → 4 → 5 → 6 → 6 bis → 7 → 8.** Une seule tâche en code à la fois.

### LOT 1 — Client Youtrust + essai de bout en bout ✅ FAIT (26/10, `11e569f`)

`Console/youtrust_client.js`, `Console/essai_youtrust_sandbox.js`. PDF 1.4 accepté, repères
reconnus, mandant puis mandataire signés, chaîne d'empreintes complète. *(Audit §8 ter.)*

### LOT 2 — Le PDF signable (O1) · 0,5–1 j

> ✅ **CODÉ ET PROUVÉ LE 26/10, NON DÉPLOYÉ** (D13 : *« vas-y avec mentions »*).
> `src/lib/signatureAnchors.ts` (neuf), `lib/api.ts` (`loadAppSettingActive`), `App.tsx`
> (`mandatSignatureBlocksHtml`, `renderMandatTemplate`, `mandatPreviewHtml`, `avenantPreviewHtml`
> + `avenantSignatureBlocksHtml` / `avenantAvecReperes`, l'appel de `generatePdf`).
> **Preuves :** `node scripts/test_reperes_signature.mjs` → **42/42 verts** — éteint, HTML du
> mandat (1, 2, 4 mandants) et de l'avenant (1, 2, 3) **identique au caractère près** au dernier
> commit ; allumé, s1..sN+1 + N mentions, invisibles, aucune accolade oubliée ; zone absente →
> génération **refusée**. **Témoin inverse** : une espace glissée exprès → 6 échecs, sortie 1.
> `npm run build` vert. **Sandbox réel** (gabarit réel, 2 mandants + mandataire) : mandat
> 5 repères → 3 signatures + 2 « Bon pour mandat », page 5 ; avenant 5 repères → 3 + 2
> « Bon pour accord » ; contrôle O3 OK ; demandes annulées.
> ⚠ **Mention = apposée automatiquement** par Youtrust à la signature (le mandant ne la tape
> pas) — corrigé le 26/10, j'avais dit l'inverse ; un champ tapé reste possible.
> ⚠ **Avenant à 2 mandants et plus : 2 pages** (le mandataire passe seul en page 2) — à juger.
> ⚠ `App.tsx` est aussi modifié, non commité, par une autre session (relecture 3b) : le commit
> ne prendra **que les morceaux du lot 2**.

**Ce qu'il fait.** Quand l'interrupteur est allumé, `mandatSignatureBlocksHtml` écrit dans
chaque case un repère invisible (`{{s1|signature|150|45}}` … `{{sN|…}}` pour les mandants,
`{{sN+1|…}}` pour le mandataire — même CSS que l'essai : Arial 10 px, couleur du fond
`#fafbfc`). L'**avenant** (`avenantPreviewHtml`) reçoit les **mêmes cases numérotées** qu'il
n'a pas aujourd'hui, avec leurs repères.

**Fichiers.** `apps/hektor-v1/src/App.tsx` (`mandatSignatureBlocksHtml` `:4879`,
`renderMandatTemplate` `:4903`, `avenantPreviewHtml` `:5041`) ; lecture de l'interrupteur.

**Ce que ça pourrait casser ailleurs.** Le PDF du mandat envoyé **aujourd'hui** à ImmoSign :
d'où la condition « interrupteur allumé ». La mise en page de la page Signatures (un repère
trop long élargirait la case → `white-space:nowrap` + position absolue, éprouvés au lot 1).
L'aperçu à l'écran : le repère y est invisible pour la même raison.

**Retour arrière.** Interrupteur éteint = aucun repère (aucun redéploiement nécessaire).

**Preuve.** (a) interrupteur éteint : le **HTML** rendu est **identique au caractère près** à
celui d'avant le lot, sur 3 mandats (1, 2 et 4 mandants) et 1 avenant *(pas le PDF : Chromium
ne rend jamais deux fois le même, mesuré au lot 1)* ; (b) allumé : envoi sandbox, `total_anchors`
= nb de cases ; (c) `npm run build` vert.

**Accord.** « vas-y » du lot ; **déploiement Vercel** (push).

### LOT 3 — La base (fondations) · 1 j

**Ce qu'il fait.** Un patch Supabase **additif** :
- interrupteur `signature_youtrust` dans `app_setting`, **`off`** (même forme que
  `annonce_nait_complete`) ;
- table **`app_signature_request`** (une ligne par demande : document, dossier, statut,
  signataires et leur état, identifiant Youtrust, `sandbox`, dates, qui a envoyé) ;
- table **`app_signature_event`** (les avis reçus, **`event_id` unique** = pas de doublon) ;
- **5 types de travaux**, avec **les trois verrous** (CHECK `app_console_job_job_type_check`,
  distribution `app_console_claim_next_job` → worker `documents`, droits
  `app_console_can_request_job` — négo sur ses biens, comme `l2b` du 12/10) :
  `youtrust_send_signature`, `youtrust_sync_signature`, `youtrust_remind_signer`,
  `youtrust_cancel_signature`, `youtrust_signing_link` ;
- **le fil d'activité du cockpit** : élargir le filtre `procedure_id is not null` à
  `provider_request_id` (`patch_cockpit_activite_sign_date_2026-07-23.sql:94-96` et sa
  jumelle du 31/07) — *seule retouche côté lecteurs*.
- `ConsoleJobType` (`types.ts:761`) : les 5 types, **et le rattrapage des 5 manquants**
  repérés le 26/10 (`generate_cadastre_document`, …).

**Ce que ça pourrait casser ailleurs.** La CHECK et la distribution sont **reconstruites** à
chaque patch de type de travail : un patch posé par une autre session entre-temps serait
écrasé → le patch vérifie l'**empreinte** de la fonction avant d'écrire et **s'arrête** si
quelqu'un est passé avant (méthode des patchs du chantier 7). Le fil du cockpit : la retouche
ne doit changer **aucun** événement ImmoSign existant (témoin : même nombre d'événements
avant / après sur tout le parc).

**Retour arrière.** `_INVERSE.sql` (solde d'abord les travaux en attente de ces types).

**Preuve.** `_REPETITION.sql` : verrous en place, interrupteur `off`, un négo peut demander
les 5 types **sur ses biens seulement**, témoin inverse du cockpit.

**Accord.** **Écriture en base de production** (le patch est collé par Frédéric).

### LOT 4 — Envoyer (O2, O3) + le garde-fou R1 · 1,5 j

**Ce qu'il fait.** Handler `youtrust_send_signature` dans le worker :
1. refuse si l'interrupteur est `off` (refus d'état, jamais un faux succès) ;
2. lit le PDF du document dans le coffre ;
3. prend les signataires : mandants du **registre** (`payload.destinataires`, déjà calculé
   par `buildMandatSignatureRecipients` et **jamais lu à ce jour**) + le **négo du bien**
   (e-mail et portable depuis `app_hektor_negotiator_agency_directory`) ;
4. vérifie : e-mail présent, **portable en +33…** (code SMS), autant de signataires que de
   cases ;
5. crée la demande : `custom_recipient_order: true`, mandants groupés (`group_with_id`) à
   l'étape 1, négo à l'étape 2 ; `otp_sms` ; `signers_allowed_to_decline: false` ;
   relances automatiques ; expéditeur « GTI Immobilier » ; `external_id` = id du document ;
6. active, puis **O3** : nb de champs = nb de signataires, sinon **annule** et signale ;
7. écrit `app_signature_request` + le miroir `metadata_json.signature`
   (`provider: 'youtrust'`, `pending`, `0/N`, `sent_at`).

**Le garde-fou R1** dans l'écrivain 1 : `extractDocumentEntries`, `reconcileSignatureStates`,
`adoptExistingImmoSignRows`, `upsertSyntheticSignedRow`, `pruneDeletedDocuments` ne
réécrivent **jamais** `signature` d'une ligne `provider = 'youtrust'`.

**Fichiers.** `Console/console_job_worker.js` (handler + `DOCUMENT_JOB_TYPES` + `switch` +
les 5 fonctions de lecture), `Console/youtrust_client.js` (paramètres d'ordre).

**Ce que ça pourrait casser ailleurs.** ⚠ **C'est le lot le plus délicat** : il touche les
fonctions de lecture ImmoSign qui font tourner le suivi actuel. Le garde-fou doit être un
**refus ciblé** (une seule condition sur `provider`), sans toucher aux pièges déjà payés
(contexte négociateur, PDF signé non écrasé, purge qui épargne les signés — mémoire
`hektor-documents-blocs-non-captures`). La purge `pruneDeletedDocuments` ne doit pas
supprimer une ligne Youtrust absente de Hektor.

**Retour arrière.** `git revert` du commit + redémarrage ; l'interrupteur éteint suffit à ne
plus rien envoyer.

**Preuve.** Essais hors ligne (tests sur des lignes fabriquées : une ImmoSign, une Youtrust,
une manuscrite → seule l'ImmoSign est réécrite) ; essai sandbox réel avec 2 mandants + négo
*(⚠ 5 signataires max pendant l'essai ; adresse de Frédéric répétée, accepté par Youtrust)* ;
**témoin inverse** : un sync documents sur une annonce ImmoSign rend exactement le même état
qu'avant.

**Accord.** « vas-y » (modification du worker) ; **redémarrage du service Documents, file
vide (0 pending, 0 running)**.

### LOT 5 — Recevoir les avis, rapatrier le signé (O4, O5, O11) · 1,5 j

**Ce qu'il fait.**
- **Fonction Supabase `youtrust-webhook`** (nouvelle) : vérifie la signature HMAC sur le corps
  brut (`verifierSignatureWebhook`, déjà écrite au lot 1), insère l'avis (`event_id` unique),
  pose un travail `youtrust_sync_signature`, **répond 200 en moins d'une seconde**.
- Handler **`youtrust_sync_signature`** (un seul, **idempotent**, utilisé par l'avis, le
  rattrapage de nuit et le rafraîchissement manuel) : relit la demande chez Youtrust, met à
  jour la table + le miroir (R3), et si `done` : PDF signé + **un audit trail PDF par
  signataire** → coffre (`signed/…`, sans écraser l'original), puis dépôt du signé chez Hektor
  *(tant qu'il vit — voir D12)*.
- **Notifications** (`app_notification`, cloche) : « Les mandants ont signé — à vous de
  contresigner » (au négo), « Mandat signé », « E-mail non remis à … ».

**Fichiers.** `supabase/functions/youtrust-webhook/index.ts` (neuf), worker (handler).

**Ce que ça pourrait casser ailleurs.** Le coffre : type `application/pdf` seulement (les ZIP
évités exprès) ; le garde-fou « le signé n'écrase pas l'original »
(`file_size = signed_document.size`, requête de contrôle de la mémoire). Les notifications :
150 non lues déjà en stock — ne pas en ajouter de bruit (un avis par étape, pas par relance).

**Retour arrière.** Supprimer l'abonnement webhook dans Youtrust (arrêt immédiat) ; la fonction
ne fait qu'insérer.

**Preuve.** Avis réels en sandbox (abonnement créé **à la main par Frédéric** dans l'app,
M4) ; un avis rejoué deux fois → une seule ligne ; signature HMAC fausse → 401 ; empreintes
de l'audit trail = fichiers du coffre.

**Accord.** **Déploiement de la fonction Supabase** (manuel, pas par push) ; secret du
webhook posé par Frédéric ; redémarrage du worker.

### LOT 6 — Les écrans (O6, O7, O8) + aiguillage R2 · 1,5–2 j

**Ce qu'il fait.** Interrupteur allumé :
- la question « Faire signer ? » (`SignaturePromptModal`) ouvre la **fenêtre d'envoi** au lieu
  de l'onglet Hektor : signataires (modifiables : e-mail, portable), coût, *Par e-mail /
  Sur place* ;
- **suivi par signataire** dans `MandatSignatureTracker` et `ConsoleDocumentsPanel` : qui a
  signé, quand, étape en cours ;
- **Relancer** (par personne), **Annuler**, **Signer maintenant** (négo, lien frais demandé
  par `youtrust_signing_link` — un lien vaut 48 h), **Ouvrir le signé**, **Ouvrir les preuves** ;
- **R2** : chaque bouton existant choisit son travail selon `provider` ; les documents ImmoSign
  gardent **leurs** boutons, à l'identique ;
- badge : le mot **« expiré »**.

Interrupteur éteint : **rien ne change à l'écran**.

**Fichiers.** `App.tsx` (`SignaturePromptModal` `:5123`, `MandatDocumentEditor` `:5236`,
`SignatureBadge` `:10222`, `MandatSignatureTracker` `:11047`, `ConsoleDocumentsPanel` `:11151`,
rubrique Mandat V3 `:29270`), `lib/api.ts`, `types.ts`.

**Ce que ça pourrait casser ailleurs.** Les boutons ImmoSign des **55 procédures en attente** :
ils doivent continuer à marcher (R2). La rubrique Mandat V3 (`ckSigStatus`) : elle lit le
miroir, donc rien à changer — à **vérifier** à l'écran. Le mobile.

**Retour arrière.** Interrupteur éteint.

**Preuve.** `npm run build` ; à l'écran, sur l'annonce bac à sable **62774** : un envoi sandbox
complet (envoi → suivi → relance → contresignature dans l'app → signé) **et** un document
ImmoSign existant dont les boutons répondent comme avant.

**Accord.** « vas-y » ; **déploiement Vercel**.

### LOT 6 bis — La signature sur place, sur tablette (O9) · 0,5–1 j

**Ce qu'il fait.** Choix « Sur place » : la demande est envoyée **sans e-mail aux mandants**
(`delivery_mode: none` pour eux) ; l'app affiche le parcours Youtrust **dans l'écran**
(iFrame), mandant après mandant sur la même tablette, puis le négo. Le code reste exigé
(SMS sur le portable de chaque mandant).

**Fichiers.** `App.tsx` (écran plein « signature en rendez-vous »), worker (option du handler
d'envoi).

**Ce que ça pourrait casser ailleurs.** Rien d'existant (écran neuf). ⚠ **En production,
Youtrust refuse l'iFrame tant que le domaine n'est pas autorisé** dans ses réglages
(`groupe-gti.vercel.app`) — en sandbox, paramètre `disable_domain_validation`.

**Preuve.** Sandbox, sur une tablette ou un téléphone : 2 signatures enchaînées dans l'app.

**Accord.** « vas-y » ; déploiement.

### LOT 7 — Le filet de nuit et la surveillance (O10, O11) · 0,5–1 j

**Ce qu'il fait.** Chaque nuit, un `youtrust_sync_signature` pour **chaque demande non
terminée** (un avis perdu ne fige jamais un état) ; une ligne au moniteur
(`check_gti_health.py`) : envois en échec, avis absents depuis 24 h sur une demande en cours,
demandes expirées.

**Ce que ça pourrait casser ailleurs.** ⚠ Mémoire « nouvelle ligne du moniteur : lire les
CHECK de la table » (le moniteur a été bloqué 6 h le 25/10) ; mémoire « décaler une tâche :
chercher les gardes horaires » ; budget de la nuit (le creux 23:18 → 03:00).
Coût Youtrust : quelques dizaines d'appels, loin de 1 200/h.

**Preuve.** Avis volontairement non traité en sandbox → rattrapé à la nuit ; la ligne du
moniteur passe au rouge puis au vert.

**Accord.** **Nouvelle tâche planifiée** (déclarée au moniteur AVANT d'être enregistrée).

### LOT 8 — Le passage en production · 0,5 j + délai du contrat

1. contrat signé (D5) ; **clé de production** dans `Console/.env` + `YOUTRUST_BASE_URL` posé
   explicitement (le client refuse la prod par défaut) ;
2. abonnement webhook de **production** (par l'API avec la clé de prod) ; domaine iFrame
   autorisé ; logo/couleurs et pièces demandées si **Pro** (D10) ;
3. **un vrai envoi sur la boîte de Frédéric** : vérifier que le PDF signé porte cette fois la
   signature cryptographique (`/ByteRange`, absente en sandbox) ;
4. **prévenir les négociateurs** : l'ordre s'inverse (aujourd'hui le négo signe en premier) ;
5. **allumer l'interrupteur**, pour tous ;
6. surveiller les 55 procédures ImmoSign restantes jusqu'à leur fin — **la lecture Hektor
   n'est jamais coupée**.

**Accord.** Chaque point.

---

## 6. LE CALENDRIER FACE AUX 14 JOURS D'ESSAI (fin ~09/11)

```
Lots 2 → 7  ≈ 6 à 8,5 jours de dev, TOUS éprouvables en sandbox
            → à faire PENDANT l'essai : à sa fin, sans abonnement, la sandbox se ferme
Lot 8       dès le contrat signé (le commercial rappelle en fin d'essai)
```

⚠ **Le risque calendrier** : si le contrat n'est pas signé à la fin de l'essai, l'accès
sandbox disparaît et les lots non éprouvés devront attendre l'abonnement.

---

## 7. CE QUI RESTE OUVERT

| # | Sujet | Qui |
|---|---|---|
| **D12** | Déposer **le mandat signé** chez Hektor (pour qu'il reste complet tant qu'il vit) ? *Recommandé : oui, sans attendre de réponse* | Frédéric |
| D5 | Offre et pack (~1 800 crédits/an mesurés ; 500 inclus) | Frédéric + commercial |
| — | **L'annuaire des négociateurs** est rempli depuis Hektor : à la coupure il doit devenir le nôtre (tâche 26 du plan maître), sinon un négo arrivé après la coupure ne pourra pas contresigner | plan maître |
| — | Un négo **sans portable** dans l'annuaire : repli `otp_email` pour lui seul ? | à trancher au lot 4 |
| — | État réel de l'interrupteur Mandat V3 (`VITE_APP_MANDAT_V3_ENABLED`) sur Vercel : **non vérifié** | lot 6 |
| — | Essai à **plusieurs vraies personnes** : une 2ᵉ boîte invitée dans Youtrust (M3, facultatif) | Frédéric |

---

## 8. LE TABLEAU DES GESTES, UNE FOIS LE PLAN FAIT

|  | créer | modifier | annuler | lire / remonter |
|---|---|---|---|---|
| **document à signer** (mandat, avenant) | app (lot 2) | régénérer | — | coffre |
| **demande de signature** | **app → Youtrust** (lot 4) | — *(annuler et refaire)* | **app** (lot 6) | **avis + nuit** (lots 5, 7) |
| **signataire** | registre + annuaire (lot 4) | dans la fenêtre d'envoi (lot 6) | — | **par personne** (lot 5) |
| **relance** | **par personne**, + automatiques (lot 6) | — | — | avis (lot 5) |
| **PDF signé + preuves** | — | — | — | **coffre + dépôt Hektor** (lot 5) |
| **procédures ImmoSign existantes** | ⛔ plus aucune après l'allumage | — | **inchangé** | **inchangé, jamais coupé** |
