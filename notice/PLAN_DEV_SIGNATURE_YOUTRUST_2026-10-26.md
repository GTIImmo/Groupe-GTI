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

## 2 bis. CE QUE YOUTRUST NOUS REND — ET CE QU'IMMOSIGN NE NOUS DONNAIT PAS (doc lue le 26/10)

**Deux sources, complémentaires :** les **avis** (webhooks : Youtrust nous prévient *quand*
quelque chose change) et l'**API** (on va chercher *le détail*). Chaque avis porte **l'état
complet de la demande** — statut, `external_id` (= notre document), dates, **et le statut de
chaque signataire** — plus le signataire concerné (`status`, `signed_at`, réponses aux champs).
Un seul avis suffit donc à reconstruire « En attente 2/3 ».

| Information | ImmoSign via Hektor (aujourd'hui) | Youtrust (demain) |
|---|---|---|
| état de la demande | à envoyer / en attente / signé / annulé, lu dans le HTML, **avec retard** | idem **+ expiré, en pause**, à l'instant (`signature_request.*`) |
| progression | « x/y » seulement pendant l'attente | **qui** a signé, **à quelle heure**, à chaque signature (`signer.done`) |
| **le client a ouvert son lien** | ✖ | ✅ `signer.link_opened` — « M. Dupont a ouvert à 10:32, pas encore signé » |
| invitation partie | ✖ | ✅ `signer.notified` |
| **e-mail non remis** (adresse fausse, boîte pleine, spam) | ✖ | ✅ `signer.notification_delivery_failed`, avec la raison |
| relances envoyées | ✖ | ✅ manuelles **et** automatiques (`…reminder_executed`) |
| date d'expiration | ✖ | ✅ dans chaque avis + `signature_request.expired` |
| incident de signature | ✖ | ✅ `signer.error` (la demande est annulée d'office → alerte) |
| PDF signé | ZIP, on devine « le plus gros PDF » | ✅ téléchargement direct `version=completed` |
| preuves | ZIP | ✅ **un dossier par signataire**, PDF **et** JSON (IP, mode et heure du code, consentement, empreintes, certificat), gardé 10 ans chez Youtrust |
| **crédits consommés** | ✖ | ✅ API `/consumptions` — suivi du pack (500 inclus, ~1 800/an mesurés) |
| rattrapage | relecture HTML, contexte négociateur requis | ✅ liste filtrable par `external_id`, `status`, dates |

**LE SORT DE CHAQUE AVIS — aucun n'est reçu pour rien.** Le *dos* (lots 3 à 5, 7) range
**tout** ; ce que l'*écran* en montre se décide à l'étape d'ergonomie (lot 6a).

| Avis | Ce que fait le dos | Ce que l'écran pourra montrer (à décider en 6a) |
|---|---|---|
| `signature_request.activated` | état `pending`, `sent_at` | « envoyé en signature » (fil du cockpit — existe déjà) |
| `signer.notified` | signataire « invité » | « invitation envoyée à M. Dupont » |
| `signer.link_opened` | signataire « a ouvert » + heure | **« ouvert, pas signé »** |
| `signer.done` | signataire « signé » + heure, progression | « M. Dupont a signé à 10:51 » ; **si tous les mandants ont signé → cloche du négo « à vous de contresigner »** |
| `signature_request.done` | état `signed`, `signed_at` → **travail : PDF signé + preuves** | « Signé le … », Ouvrir le signé, Ouvrir les preuves (existe déjà) |
| `signature_request.reminder_executed` / `…automatic_reminder_executed` | journal « relancé » | « relancé le … (3ᵉ relance) » |
| `signer.notification_delivery_failed` | **alerte** + raison | **« e-mail non remis à M. Dupont : adresse invalide »** + cloche |
| `signer.error` | **alerte** (Youtrust a annulé la demande) | « incident, à renvoyer » + cloche |
| `signature_request.expired` | état `expired` | « expiré le … » (fil du cockpit — ✅ décidé) ; proposer de renvoyer |
| `signature_request.reactivated` | état `pending` à nouveau | « relancée après expiration » |
| `signature_request.canceled` | état `cancelled` | « annulé » (existe déjà) |
| `signer.declined` / `signature_request.declined` | état `declined` (*ne doit pas arriver : refus désactivé*) | alerte si jamais |
| `signature_request.paused` / `.resumed` / `.deleted` / `.permanently_deleted` | journal (*gestes que l'app ne fait pas : seulement si quelqu'un agit dans l'app Youtrust*) | alerte « modifié hors de l'app » |
| **non abonnés** : `approver.*`, `signer.identification_*`, `signer.identity_saved`, `signer.sender_contacted` (signature avancée/qualifiée et approbateurs, non utilisés), `contact.created`, `electronic_seal.*` | — | — |

**Ce que ça ajoute au plan (proposé, D15) :**
1. s'abonner à **tous les avis de signature** (`signature_request.*` et `signer.*`, sauf ceux de
   la signature avancée/qualifiée que nous n'utilisons pas) ;
2. garder **chaque avis** (`app_signature_event`, lot 3) → un **journal par mandat** : envoyé,
   ouvert, relancé, signé par untel, e-mail non remis ;
3. afficher au négo « **ouvert, pas signé** » et « **e-mail non remis** » (lot 6) — deux
   raisons concrètes de relancer ou de corriger une adresse ;
4. une ligne **crédits consommés / restants** à l'écran Santé (lot 7).

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
> Ordre imposé : **2 → 3 → 4 → 5 → 6a (ergonomie, validée) → 6b → 6 bis → 7 → 8.** Une seule
> tâche en code à la fois. *L'audit d'ergonomie 6a (lecture seule) peut se faire pendant le
> code des lots 3 à 5.*

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

> **Audit du 26/10 (lecture seule) :** CHECK 48 types · `app_console_claim_next_job`
> `4aa93a31…` · `app_console_can_request_job` `8b2c4378…` · `app_setting` 17 réglages, pas de
> `signature_youtrust` · lecteurs SQL de la signature : **2** (`app_cockpit_activite`
> `8b96ef02…`, `app_console_mark_document_signed_manual` `66e1ebec…`) · lecture des documents =
> `is_app_global_reader() OR app_mes_biens_portefeuille()`, `anon` exclu · 0 travail Youtrust.
>
> **✅ « expiré » dans le fil du cockpit : oui** (Frédéric, 26/10).
>
> ### ✅✅ LOT 3 POSÉ EN PRODUCTION LE 26/10 (~16:43, heure de Paris) — par moi, sur autorisation explicite de Frédéric
> *(« Je t'ai autorisé pour le faire toi-même »)*. Fichier posé = la version commitée `775ec71`,
> via le pooler (mémoire `eprouver-un-patch-dans-une-transaction-annulee`), en 4,0 s.
> **Tableau de fin 7/7** : interrupteur `off` · tables posées · 5/5 dans les trois verrous ·
> cockpit posé · relance/annulation ImmoSign intactes. **Témoin du cockpit identique**
> (`b05d7373…`, la même valeur qu'à l'essai). **Répétition en production : 12/12 OK.**
> **Conseiller de sécurité Supabase** : 0 signalement sur les nouvelles tables (rapport lu en entier).
> **Distribution éprouvée en transaction annulée** : un `relance_signature` et un
> `youtrust_sync_signature` posés → **tous deux pris par le worker documents**, aucun par le
> worker admin ; 0 travail d'essai restant. ⚠ Piège rencontré : `app_console_claim_next_job` ne
> sert QUE les identifiants de worker en `…:service:v9` / `…:scheduled:v9` — un nom libre ne
> reçoit rien (ce n'est pas une panne).
> Rien à redémarrer. Rien ne change pour les utilisateurs (interrupteur éteint).
>
> *Historique :* **patch écrit et éprouvé le 26/10 avant la pose :**
> `supabase/patch_a2_signature_youtrust_lot3_2026-10-26.sql` + `_INVERSE.sql` + `_REPETITION.sql`.
> **Essai dans UNE transaction annulée** (patch → répétition → inverse → contrôles, erreur finale
> + ROLLBACK) : **18/18 verts en 6,9 s** — 12 de la répétition (dont négociateur : 5 types sur
> SON bien, refusé sur celui d'un autre ; relance ImmoSign toujours permise ; écriture refusée à
> un utilisateur connecté ; admin partout) et 6 de l'inverse (aucune trace, ImmoSign intact).
> Témoin du cockpit identique avant/après (407 dossiers) ; **témoin éprouvé** : un défaut glissé
> exprès fait s'arrêter le patch (« le fil d'activité a CHANGÉ »). Base intacte après l'essai
> (empreintes `4aa93a31…`, `8b2c4378…`, `8b96ef02…` inchangées, aucune table).
> ⚠ La contrainte est modifiée **en dernier** (l'ALTER TABLE verrouille `app_console_job`
> jusqu'au COMMIT : ainsi un instant, pas 7 s).
> Front : `types.ts` reçoit les 5 types Youtrust **et 9 types oubliés** (48 en base, 39 dans
> le front — et non 5 comme dit l'inventaire du 26/10). `npm run build` vert.
>
> **✅ D14 — « signé à la main » : FAIRE COMME AVEC IMMOSIGN** (Frédéric, 26/10 : *« déjà géré
> avec ImmoSign, regarde et fais pareil »*). Mesuré : la base **ne refuse rien** (la fonction
> pose `status signed` + `source manuscrite` quel que soit l'état) ; l'écran montre le bouton
> tant que le document n'est pas signé (`APP_MANDAT_V3_ENABLED`) ; le worker **exclut** ensuite
> tout document `manuscrite` du suivi (`console_job_worker.js:5810`). ⇒ **aucune garde neuve en
> base** ; l'écrivain Youtrust (lots 4-5) exclura `manuscrite` **exactement comme** l'écrivain
> ImmoSign. *Point à trancher au lot 6 :* une demande Youtrust en cours resterait active (relances)
> — proposer « annuler aussi la demande Youtrust ? » dans la confirmation.
> ⚠ **Noté, non traité (hors périmètre) :** la fusion de la synchro documents
> (`console_job_worker.js:5092-5096`, `{ ...inc, sent_at, signed_at }`) **ne garde pas**
> `source` : une relecture Hektor qui rapporte un état sur un document marqué « à la main »
> effacerait la marque. **0 document « à la main » en base au 26/10** (le bouton dort derrière
> `APP_MANDAT_V3_ENABLED`) : défaut dormant. Le garde-fou R1 du lot 4 peut le couvrir aussi.

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

> **📧 L'E-MAIL QUE REÇOIT LE CLIENT (lu dans la boîte de Frédéric le 26/10, avec son accord ;
> 20 e-mails Youtrust sur 24 h).** Expéditeur affiché « Youtrust pour GTI Immobilier »
> (`notifications@…yousign.app`). Ce que Frédéric a trouvé « incompréhensible » vient **de nos
> essais**, pas de Youtrust : le titre et l'objet reprennent le **nom technique** de la demande
> (« ESSAI A.2 lot 4 - demande exacte… »), le nom du signataire portait « (Mandant1) », le
> fichier s'appelait `mandat_essai_lot4.pdf`, et mon texte d'essai était sans accents.
> **Tout cela, c'est le worker qui l'écrit → se décide AU LOT 4 (D19).**
> **Le logo et les couleurs ne dépendent pas du code :** avec l'expéditeur « organisation »,
> Youtrust affiche **le logo de l'organisation** (réglage de l'app Youtrust, sans offre Pro) ;
> avec un expéditeur « personnalisé », le logo n'apparaît **que** par une « expérience
> personnalisée » (**offre Pro**, D10), qui seule change aussi les couleurs (bouton vert) et le
> pied de page Youtrust. ⇒ essai possible tout de suite : renommer l'organisation
> « GTI Immobilier » et y déposer le logo dans l'app Youtrust, puis envoyer en expéditeur
> « organisation ».

> **Audit du 26/10 (lecture seule).** La ligne du mandat est créée par la RELECTURE de la liste
> Hektor après dépôt (`upsertConsoleDocuments`) — c'est la même ligne que la synchro de nuit
> relira : le risque R1 est RÉEL. Écrivains à protéger : ① fusion `upsertConsoleDocuments`
> (l. 5092) ; ② `reconcileSignatureStates`, cible suivie (l. 5887) ; ③ rattachement d'un signé
> orphelin (l. 5909) ; ④ `pruneDeletedDocuments`. Le filtre « procédure en cours » (l. 5803)
> exclut déjà un document sans `procedure_id`. Coordonnées mesurées : mandants des biens vivants
> 1 495 — e-mail 74 %, portable 73 %, **les deux 69 %** ; négociateurs : 165/219 portable mobile.
> Le worker se charge sans démarrer (`require.main === module`, l. 23008) → tests hors ligne
> sur le code réel (méthode de `test_domaine_documents.js`). Redémarrage : services
> **documents ET synchro** (`refresh_console_data` appelle aussi `reconcileSignatureStates`).
>
> **✅ Décisions de Frédéric (26/10) :**
> - **D16** : e-mail obligatoire (sauf « sur place ») ; portable → `otp_sms` ; sans portable →
>   repli `otp_email` (ne pas bloquer ~3 mandants sur 10).
> - **D17** : le mandataire = **le négociateur DU BIEN** (fiche), pas celui qui clique ;
>   modifiable dans la fenêtre d'envoi (lot 6b).
> - **D18** : le garde-fou R1 protège aussi les documents **« signé à la main »**.
> - Les **gestes worker** relancer / annuler / lien « Signer maintenant » entrent dans le lot 4
>   (la mise à jour d'état reste au lot 5).
>
> ### ✅ LOT 4 CODÉ ET ÉPROUVÉ LE 26/10 — NON ACTIF (worker pas redémarré), interrupteur éteint
> **Code** (`Console/console_job_worker.js`, additif) : `signatureProtegee()` + le garde-fou R1 aux
> 4 endroits (fusion, suivi, rattachement, purge) — couvre aussi « à la main » (D18) ; un bloc
> « A.2 — SIGNATURE YOUTRUST, LOT 4 » : `handleYoutrustSendSignature`, `…RemindSigner`,
> `…CancelSignature`, `…SigningLink` (+ `…SyncSignature` qui refuse « lot 5 ») ; les 5 types dans
> `DOCUMENT_JOB_TYPES`, l'aiguillage et `JOB_LIBELLES`. Textes D19 ; expéditeur
> `YOUTRUST_EXPEDITEUR` (« GTI Immobilier » par défaut, `organisation` = logo de l'organisation).
> **Reprenable sans double envoi** : la ligne est écrite AVANT Youtrust, l'id gardé dès la création,
> un rejeu reprend (« deja_envoye ») ; refus non guérissables = `MARQUE_REFUS_ETAT` (jamais rejoués).
> ⭐ **Trou trouvé en écrivant l'essai, et bouché** : « une case par signataire » ne voit pas un PDF
> à 2 mandants envoyé avec 1 seul (le négo aurait signé dans la case du mandant 2) → **compte des
> repères AVANT activation** (`2 × mandants + 1`), brouillon supprimé, aucun crédit.
> **Preuves :** `node Console/test_garde_r1_signature.js` **22/22** — chaque scène jouée sur le code
> d'AVANT (git) et d'après : l'ancien code ÉCRASE / RÉÉCRIT / RATTACHE / PURGE Youtrust et « à la
> main », le nouveau les garde ; **la ligne ImmoSign sort identique des deux** (témoin inverse).
> Tests existants complétés de la tranche `signatureProtegee` (« on ajoute, on ne restructure
> pas ») et **verts** : adoption 16, domaine 13, choix PDF 7, envoi différé 35. ⚠ Leçon : je lisais
> d'abord le code de sortie de `tail`, pas du test — deux tests paraissaient verts et ne l'étaient pas.
> `node Console/essai_youtrust_handler_sandbox.js --pdf=…` : **15/15 contre la vraie sandbox**
> (fausse base, interrupteur « on » en mémoire seulement) — refus éteint, envoi, ordre D7, titre D19,
> miroir sans `procedure_id`, rejeu sans double envoi, relance (et refus avant son tour), lien refusé
> avant son tour, annulation, repères 5≠3 refusés avant activation.
> **Plusieurs mandants (question de Frédéric, 26/10) — éprouvé en sandbox, vrais handlers :**
> **2, 3 et 4 mandants** + le négociateur (4 = le maximum de l'essai : 5 signataires) → **tout
> vert** : les N mandants invités en parallèle, le négo attend ; chaque mandant 1 signature +
> 1 mention, le négo 1 signature et aucune mention ; la case GTI est la DERNIÈRE de la grille
> (3 mandants : à côté du 3ᵉ, x 310 / 37 ; 4 mandants : seule en dessous, y 297) ; compte des
> repères refusé pour N−1 (7 au lieu de 5, 9 au lieu de 7). Au-delà de 4 : prouvé jusqu'à
> **12 mandants** au niveau des repères (lot 2, `test_reperes_signature.mjs`) ; l'envoi réel à
> 5+ mandants attend la production (limite de l'essai). ⚠ Mon premier contrôle de position
> (« le négo SOUS la grille ») était faux pour un nombre impair — corrigé en ordre de lecture.
> **⏳ Pour l'activer :** redémarrer les services **documents ET synchro** (file vide). Sans
> redémarrage, l'ancien code tourne — sans risque : aucun document Youtrust n'existe.
> **✅ D20 (Frédéric, 26/10) : PAS de contacts Youtrust ; les négociateurs sont des signataires
> SIMPLES (sans compte ni licence Youtrust).** Mesuré : créer des signataires ne crée aucun contact
> (0 en sandbox) ; le chemin « contact → signataire » marche (éprouvé puis supprimé) mais exigerait
> une table de correspondance et recopierait les données des clients. Un « utilisateur » Youtrust
> = une licence payante (1 seule incluse) ; un utilisateur signataire consomme aussi 1 crédit.
> Comptes Youtrust : Frédéric (et éventuellement l'administration) seulement.
>
> ### 🔍 AUDIT DE COMPLÉTUDE DU LOT 4 (26/10, demandé par Frédéric : « compléter correctement »)
> **Ce que Youtrust exige d'un signataire (référence API) :** `email`, `first_name`, `last_name`,
> `locale` **obligatoires** — l'e-mail l'est **même en signature sur place** ; e-mail ≤ 100 car. ;
> portable E.164 obligatoire seulement pour le code SMS.
> **Nos mandants réels (1 495 sur les 712 biens vivants), mesurés :**
>
> | Cas | Nombre | Ce qui se passe |
> |---|---|---|
> | sans e-mail | **394 (26 %)** | ⛔ ne peuvent pas signer chez Youtrust tant que l'e-mail manque → **D23** |
> | e-mail invalide | 4 | refus clair du worker |
> | fiche de couple « Mr./Mme » sans prénom | **309** (301 totalement muettes ; dans **223** cas la personne porteuse est AUSSI mandante du bien) | l'écran écarte la fiche muette → **le conjoint ne signerait pas** → **D22** |
> | sociétés / succession / collectivité | 4 / 1 / 1 | il faut un **représentant** (prénom + nom) → **D22** |
> | portable mobile FR | 1 094 | code SMS |
> | portable étranger seul | 10 | code SMS (accepté hors Chine) |
> | fixe seul / aucun téléphone | 49 / 342 | code par e-mail (D16) |
> | deux mandants, même e-mail | 78 biens | ✅ accepté par Youtrust (éprouvé) |
> | 5 mandants et plus | 67 biens, **jusqu'à 16** | ✅ repères prouvés jusqu'à 16 (`test_reperes_signature.mjs`) ; production 100 signataires |
>
> **Les négociateurs des 712 biens :** 625 actifs · **37 inactifs · 50 absents de l'annuaire**
> → **87 biens (12 %)** où « le négo du bien » (D17) ne donne personne de valable — et le résolveur
> retomberait sur **l'e-mail de l'agence** → **D21**.
> **Le chemin du document :** le mandat généré ne naît chez nous **qu'après le dépôt chez Hektor**
> (`handleGenerateMandatDocument` → `upload_document_to_hektor` → relecture) et l'écran attend
> jusqu'à 150 s ce dépôt. Le chemin « chez nous d'abord » (envoi différé, `completerEnvoiDocumentDiffere`)
> existe pour les ajouts à la main, **pas pour le mandat généré** → à la coupure, plus de ligne,
> donc plus d'envoi Youtrust → **D24**.
>
> **Corrigé tout de suite (défaut dans MON code du lot 4) :** `prenomNomSignataire` **inventait** un
> prénom (« DUPONT » → prénom DUPONT ; « M. et Mme DUPONT » → prénom « et »). Désormais : jamais
> de prénom inventé, refus clair « fiche de couple à éclater, ou représentant de société à
> indiquer ». `node Console/test_signataires_youtrust.js` **16/16** (prénoms + portables).
> `test_garde_r1_signature.js` corrigé : sa version « d'avant » est le worker juste avant le commit
> qui introduit `signatureProtegee` (une fois le lot 4 commité, HEAD le contenait : 7 faux échecs).
>
> **Décisions à prendre (recommandations) :**
> - **D21** négo du bien inactif / absent → **l'utilisateur connecté qui envoie** signe comme
>   mandataire, et **jamais l'e-mail de l'agence** ; l'écran le montre.
> - **D22** couples et sociétés → dans l'éditeur du mandat, **alerte** « fiche de couple : un seul
>   signataire, ajouter le conjoint ? » et saisie du **représentant** d'une société (lots 6a/6b).
> - **D23** e-mail manquant → **saisi dans la fenêtre d'envoi** ET **enregistré sur la fiche du
>   contact** (« une saisie ne se perd jamais »), par le geste de modification de contact existant.
> - **D24** le mandat généré **naît chez nous d'abord** (réutiliser l'envoi différé), Hektor
>   reçoit ensuite le dépôt → indispensable à la coupure, et supprime l'attente de 150 s
>   (**lot 4 bis**, avant le lot 6b).
>
> **Payload attendu du front (lot 6b)** : `{ app_console_document_id, document_kind, numero_mandat,
> bien_adresse, mandants: [{prenom, nom, email, telephone}] (ordre des cases), mandataire? }`.
>
> **🔍 CONTRE-AUDIT DOC + SANDBOX DU 26/10 (demandé par Frédéric avant validation) — la demande
> EXACTE du lot 4 jouée en sandbox** (mandat réel 2 mandants + négociateur, boîte de Frédéric ×3,
> `custom_recipient_order`, `group_with_id`, relances, expéditeur, puis annulation) :
>
> | Hypothèse du lot 4 | Doc | Sandbox |
> |---|---|---|
> | mandants **en parallèle**, puis le négo (D7) | ✅ « stages », `group_with_id` | ✅ 3 s après l'activation : mandants 1 et 2 `notified`, négo `initiated` (attend) |
> | repère sN = N-ième signataire **créé**, même groupé | ⚠ ambigu | ✅ s1→mandant 1, s2→mandant 2, s3→négo + 2 mentions « Bon pour mandat » |
> | expéditeur « GTI Immobilier » + objet/texte de l'e-mail | ✅ | ✅ acceptés |
> | relances automatiques (2 j × 3) | ✅ | ✅ acceptées |
> | refus désactivé | ✅ (défaut) | ✅ |
> | expiration 6 mois | ✅ | ✅ `2027-04-26` |
> | lien de signature récupérable même avec envoi par e-mail (« Signer maintenant », D8) | ✅ | ✅ pour un signataire invité (valable **48 h**) ; **absent tant que ce n'est pas son tour** |
> | relance manuelle | ✅ « notified » seulement | ✅ acceptée sur un mandant invité ; **refusée** (400) sur le négo pas encore invité |
> | annulation | ✅ | ✅ `canceled` |
> | code par **SMS** (D16) | ✅ portable E.164 obligatoire | ⏳ **non éprouvé** (aucun SMS vers un numéro sans l'accord de son titulaire) |
>
> **Ce que l'essai change au code :** (1) la notification est **asynchrone** (~3 s) : le worker
> ne doit pas attendre « invité » juste après l'activation — le contrôle O3 des cases, lui, est
> immédiat ; (2) « Relancer » seulement pour un signataire **invité** ; (3) le lien « Signer
> maintenant » se demande **au clic** (il n'existe qu'à son tour et vaut 48 h) ; (4) l'étape
> (`recipient_stage_index`) n'est pas rendue par la lecture de la demande : l'ordre se garde chez
> nous (`signers[].index`).

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

### LOT 6a — L'ERGONOMIE AVANT LE CODE (méthode de Frédéric) · 1 j + ses validations

*Ajouté le 26/10 à la demande de Frédéric : « on ajoute des fonctions, il faudra réfléchir au
front et à l'ergonomie ».* Méthode « ergonomie d'abord, design ensuite » (mémoire
`refonte-design-methode`) :
1. **cartographier** tout ce qui touche la signature aujourd'hui : rubrique Mandat (V3 et
   actuelle), `SignaturePromptModal`, `MandatSignatureTracker`, onglet Documents
   (`ConsoleDocumentsPanel`), fil d'activité du cockpit, cloche, écran Santé — chaque bouton,
   chaque badge, chaque modale ;
2. **tableau anti-perte** : chaque fonction d'aujourd'hui → sa place demain (aucun bouton perdu,
   y compris les boutons ImmoSign des procédures encore en cours) ;
3. **plan ergonomique** : où vivent les nouveautés (fenêtre d'envoi, suivi par signataire,
   « ouvert, pas signé », « e-mail non remis », journal du mandat, « Signer maintenant »,
   signature sur place, crédits) — regroupées, sans scroll inutile ;
4. **maquette** (capture exacte de l'écran réel, mémoire `capture-exacte-ecran-pour-design`) ;
5. validation de Frédéric → seulement alors le lot 6b.

**Le dos n'attend pas l'écran :** les lots 3, 4, 5 et 7 rangent **tous** les avis ; l'écran
choisit ensuite quoi en montrer. Aucune donnée n'est perdue si une décision d'écran change.

### LOT 6b — Les écrans (O6, O7, O8) + aiguillage R2 · 1,5–2 j

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
