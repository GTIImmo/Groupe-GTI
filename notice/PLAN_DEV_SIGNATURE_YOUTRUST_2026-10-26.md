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
> **✅ Réponses de Frédéric (26/10) :**
> - **D21** — ✅ précisé (26/10) : **le négociateur DU BIEN signe** quand il est actif ; **la
>   personne qui envoie** signe seulement s'il est inactif ou absent de l'annuaire ; **jamais**
>   l'e-mail de l'agence.
> - **Procédures ImmoSign en cours à l'allumage** — ✅ (26/10) : leurs boutons **Relancer /
>   Annuler sont GARDÉS** jusqu'à leur fin (R2) ; aucun nouvel envoi ImmoSign.
> - **D22** — *« il faut ajouter par défaut le conjoint »* : une fiche de couple donne **deux
>   signataires d'office** (le conjoint est pré-ajouté, à compléter) ; société → représentant.
> - **D23** — oui : e-mail saisi à l'envoi ET enregistré sur la fiche du contact.
> - **D24** — réexpliqué, puis ✅ **oui** (26/10) : *« le mandat généré est enregistré chez nous
>   d'abord, Hektor le reçoit ensuite en arrière-plan »* → **lot 4 bis**.
> - ⛔ **RAPPEL DE FRÉDÉRIC (26/10)** : *« quand on allume le système de signature électronique de
>   mon app, ce sera UNIQUEMENT Youtrust, plus ImmoSign ; on garde uniquement la lecture par la
>   console, les runs qui mettent à jour les états »*. ⇒ interrupteur ALLUMÉ : **aucun nouvel envoi
>   ImmoSign** (plus de bouton « ouvrir Hektor pour signer ») ; le mandat généré est enregistré
>   **chez nous seulement, SANS dépôt chez Hektor** (le seul but du dépôt était ImmoSign — mémoire
>   du 29/06) ; le mandat signé et ses preuves restent chez nous (**D12 tombe**). La lecture
>   ImmoSign par les runs continue pour les procédures déjà en cours. « Interrupteur éteint =
>   comme aujourd'hui » ne désigne QUE la période avant l'allumage, pas une option.
> - ⭐ **EXIGENCE GÉNÉRALE** : *« il faut une fenêtre d'envoi qui contrôle la complétude des
>   signataires, et propose de mettre à jour si nécessaire certaines infos sur les signataires »*.
>   ⇒ **La fenêtre d'envoi vient AVANT la fabrication du PDF** : les cases de signature dépendent
>   des signataires (un conjoint ajouté = une case de plus). Cœur du lot 6a/6b.
>
> ### ✅ LOT 4 BIS CODÉ ET ÉPROUVÉ LE 26/10 — NON ACTIF (worker non redémarré), interrupteur éteint
> **D24** — `handleGenerateMandatDocument` : signature Youtrust **allumée** → `enregistrerMandatChezNous`
> (ligne `source = 'app'`, `envoi_hektor_statut = 'sans_hektor'`, `hektor_document_id` NULL ;
> **reprenable** par `metadata_json.generation_job_id`) ; **aucun** travail `upload_document_to_hektor`.
> ⛔ **LA RÈGLE DE STOCKAGE EST RESPECTÉE** — Frédéric, 26/10 : *« il ne faut pas changer les règles
> s'il y a des raisons que uniquement certains états »*. J'avais d'abord FORCÉ la copie au coffre ;
> l'audit a retrouvé les 3 raisons de `shouldKeepCloud` (indépendance : le serveur porte tout ;
> volume ; le coffre n'est PAS sauvegardé — mémoire `stockage-documents-serveur-cloud-acces`) et
> le mécanisme à la demande déjà prévu (`prepare_document_cloud`). ⇒ copie serveur toujours,
> coffre seulement pour les biens vivants ; **l'envoi Youtrust lit la copie SERVEUR**
> (`lirePdfDuDocumentPourSignature` : serveur d'abord, coffre ensuite, refus si ce n'est pas un PDF).
> Mesure : 18 générations de mandat depuis le 29/06 (essais) ; en usage normal (Estimation, Actif)
> la règle met déjà le mandat au coffre — le forçage ne servait à rien, il contournait la règle ailleurs. **Éteinte** :
> le chemin d'avant, **inchangé** (seule différence : la lecture de l'interrupteur).
> **D21** — `mandataireDuMandat` : négo DU BIEN s'il est actif et a un e-mail ; sinon l'expéditeur
> (`job.requested_by` → compte, complété par l'annuaire en égalité EXACTE d'e-mail — `ilike` traite
> `_` en joker) ; sinon **refus d'état** ; le résolveur de l'avis de valeur (repli agence) n'est
> plus appelé par l'envoi.
> **Preuves :** `node Console/test_mandat_chez_nous_et_mandataire.js` **22/22** (éteint = mêmes
> appels et même charge que le code d'AVANT, tiré de git ; allumé = 1 ligne, 0 travail Hektor,
> coffre SELON LA RÈGLE (Estimation : oui ; Vendu : non), lecture serveur puis coffre, refus d'un
> non-PDF, pas de doublon au rejeu ; D21 : actif, inactif, absent, sans e-mail, joker `_`,
> hors annuaire, refus, fenêtre). Tous les tests du lot 4 **verts** (garde R1 22, signataires 16,
> adoption 16, domaine 13, envoi différé 35, choix PDF 7) + essai sandbox réel **18/18** à
> 3 mandants. ⚠ Écran (lot 6b) : avec Youtrust allumé, la question « Faire signer ? » qui ouvre
> Hektor ne doit plus apparaître — c'est la fenêtre d'envoi qui la remplace.
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

> ### 🔎 AUDIT DU LOT 5 — 05/11/2026 (lecture seule, rien codé)
> *Audit limité au lot 5 (recevoir les avis, rapatrier le signé et les preuves, prévenir) ; les autres objets ne sont pas
> mesurés ici.*
>
> **CE QUI EXISTE DÉJÀ.** Base (lot 3, en production) : `app_signature_request` (statut, signataires, dates `done_at` /
> `canceled_at` / `expired_at`, `signed_storage_path`, `proofs`, `last_event_at`) et `app_signature_event` (`event_id`
> clé primaire = dédoublonnage ; index « à traiter » sur `processed_at`), RLS en lecture seule pour les connectés,
> aucune écriture ni pour `anon` ni pour `authenticated`. Au 05/11 : **0 demande, 0 avis, 0 travail Youtrust**,
> interrupteur `off`. Le type `youtrust_sync_signature` est dans les trois verrous, et son handler est un refus
> (« pas encore en service »). Client (`youtrust_client.js`) : `lireDemande`, `lireSignataire`, `telechargerDocuments`
> (`version=completed`), `telechargerAuditTrail` (PDF par signataire) et `verifierSignatureWebhook` (HMAC sur le corps
> brut) existent ; **manque** la lecture JSON des preuves (`GET …/signers/{id}/audit_trails`). Le miroir s'écrit par
> `majMiroirSignatureDocument`. Le modèle ImmoSign du signé (`downloadSignedProcedureDocument`) : PDF sous
> `…/documents/<id>/signed/`, la COLONNE `storage_path` pointe vers le signé (la policy de lecture l'exige),
> `metadata_json.signed_document` {chemin, taille, sha256…} ; l'original reste à son chemin.
>
> **CE QUE DIT LA DOC YOUTRUST (relue le 05/11, developers.youtrust.com).** Chaque avis porte `event_id`,
> `event_name`, `event_time` (époque Unix), `sandbox`, `data.signature_request` (état complet, `external_id`,
> `signers[].status`) et `data.signer` (`status`, `signed_at`). En-tête `X-Yousign-Signature-256` = `sha256=` + HMAC hex
> du corps BRUT. Réponse 2xx **en moins de 1 s** (10 s pour les nouvelles tentatives) ; 8 nouvelles tentatives sur ~4
> jours ; **un même avis peut arriver plusieurs fois, et l'ORDRE n'est pas garanti** ⇒ le travail relit la demande chez
> Youtrust au lieu de croire l'avis. Adresses d'origine : 5 plages publiées. **L'abonnement par l'API n'existe qu'en
> production** (`POST /webhooks`, offres Plus et au-delà) : pendant l'essai, il se crée **à la main dans l'app** (M4).
> Preuves JSON d'un signataire : seulement quand il a signé (IP, consentement, mode et heure du code, empreintes du
> document, certificat) ; PDF par signataire et PDF de toutes les preuves.
>
> **CE QUE LE LOT 5 POURRAIT CASSER AILLEURS — trouvé :**
> 1. ⚠⚠ **La date de signature.** Le pilotage ne lit `signed_at` qu'en « jj/mm/aaaa » (`lib/pilotage.ts:231`) et la
>    pastille l'affiche telle quelle (« Signé le … »). ImmoSign écrit « 16/06/2026 à 14:35 » (459 signés, 0 en ISO).
>    ⇒ Youtrust doit écrire **la même forme** (heure de Paris), l'heure exacte ISO à côté (`signed_at_iso`) et dans
>    `done_at`. *Trouvé en passant, hors périmètre :* « signé à la main » écrit une date ISO → le pilotage ne la lirait
>    pas ; dormant (0 document « à la main »).
> 2. **Le fil du cockpit** lit `sent_at` en ISO : déjà ce que l'envoi écrit. Rien à faire.
> 3. **L'interrupteur ne doit pas couper la lecture.** Une demande partie doit être suivie jusqu'au bout même si
>    `signature_youtrust` repasse à `off` (même règle qu'ImmoSign : « la lecture n'est jamais coupée ») ⇒ le travail de
>    mise à jour NE refuse PAS sur l'interrupteur, contrairement à l'envoi.
> 4. **La fonction Supabase doit accepter un appel SANS jeton** (`verify_jwt = false`) : Youtrust n'en a pas. Les deux
>    fonctions existantes l'exigent. Sa seule protection est donc le HMAC (401 sinon) ; elle n'écrit que l'avis et un
>    travail, avec la clé de service.
> 5. **La cloche est déjà saturée** : 1 963 notifications non lues sur 1 998 (1 800 rapprochements). L'index unique
>    (destinataire, dossier, type, non lu) écarte les doublons ⇒ peu de types, un par étape, jamais par relance.
> 6. **Le coffre** : la règle de stockage tient (serveur toujours, coffre pour les biens vivants) ; un mandat se signe
>    sur un bien vivant, donc au coffre. Seulement des PDF (pas de ZIP). Le signé ne remplace pas l'objet original.
> 7. **L'écran** : il sait « Ouvrir le signé » (`signed_document`) ; il n'existe **aucun** bouton « Ouvrir les preuves »
>    (le tableau du §2 bis disait « existe déjà » : faux) ; et le cockpit (`ckSigStatus`) n'accepte un « en attente »
>    qu'avec un `procedure_id` → un mandat Youtrust en cours n'y apparaît pas. ⇒ P8 (écran), pas le lot 5.
> 8. **Les gardes existantes** : R1 (les lectures ImmoSign ne touchent pas une ligne `youtrust`), le marquage 8f et la
>    nuit (ligne `sans_hektor`, sans numéro Hektor) laissent la ligne tranquille ; le mandat signé n'est PAS déposé chez
>    Hektor (D12 tombée le 26/10).
>
> **⏰ LE CALENDRIER.** L'essai Youtrust finit vers le **09/11**. La preuve du lot 5 exige une signature COMPLÈTE en
> sandbox (mandants puis négociateur), donc : la fonction déployée, l'abonnement créé dans l'app, le secret posé, les
> services redémarrés — et quelqu'un qui signe.
>
> **PROPOSITION DE DÉCOUPAGE (à valider) :**
> - **L5-1 la fonction `youtrust-webhook`** : HMAC (401), avis rangé (doublon ignoré), travail `youtrust_sync_signature`
>   posé s'il n'y en a pas déjà un en attente pour cette demande, 200 tout de suite ; un avis d'une demande inconnue est
>   gardé sans travail. Essai hors ligne (Deno) avec avis fabriqués, signature juste / fausse, doublon.
> - **L5-2 la mise à jour** (`youtrust_sync_signature`, idempotent) : relit la demande et chaque signataire, met à jour
>   la table, le miroir (R3 : `pending` + « x/N », `signed` + date ImmoSign + ISO, `cancelled`, `expired`), marque les
>   avis traités ; respecte « à la main » (D18).
> - **L5-3 le signé et les preuves** : à `done`, une seule fois : PDF signé (modèle ImmoSign) ; pour chaque signataire,
>   le PDF de preuves (coffre) et le JSON (`proofs`) ; empreintes contrôlées.
> - **L5-4 les notifications** au négociateur du bien : « les mandants ont signé : à vous de contresigner », « mandat
>   signé », « e-mail non remis à … / incident », « expiré » — rien d'autre.
>
> **QUESTIONS POUR FRÉDÉRIC :**
> - (Q1) la date de signature écrite comme ImmoSign (« jj/mm/aaaa à hh:mm »), l'heure exacte à côté — recommandé : oui ;
> - (Q2) les 4 notifications ci-dessus, au négociateur du bien — recommandé : oui ;
> - (Q3) le suivi continue même si l'interrupteur repasse à `off` — recommandé : oui ;
> - (Q4) la preuve : qui signe en sandbox ? (a) toi, depuis ta boîte, 3 fois (code par e-mail) ; (b) moi, dans le
>   navigateur intégré, sur les liens de signature que le worker demande à Youtrust, avec ton accord à chaque fois ;
> - (Q5) l'ordre : L5-1 → L5-2 → L5-3 → L5-4, P8 (l'écran) ensuite.
>
> ✅ **RÉPONSES DE FRÉDÉRIC (05/11) : « Oui, et Q4 = a »** →
> - **D37** (Q1) `signed_at` écrit comme ImmoSign, « jj/mm/aaaa à hh:mm » (heure de Paris), l'heure exacte ISO à côté ;
> - **D38** (Q2) quatre notifications au négociateur du bien : à contresigner, signé, e-mail non remis / incident, expiré ;
> - **D39** (Q3) le suivi d'une demande partie continue même interrupteur `off` ;
> - **D40** (Q4 = a) la preuve en sandbox : **Frédéric signe lui-même**, depuis sa boîte, les 3 fois (code par e-mail) ;
> - **D41** (Q5) l'ordre L5-1 → L5-2 → L5-3 → L5-4, puis P8.
>
> ✅ **L5-1 ÉCRIT LE 05/11** (code neuf dormant : rien déployé, rien commité, aucun abonnement créé) :
> `supabase/functions/youtrust-webhook/logique.ts` (sans dépendance : HMAC par Web Crypto sur le corps BRUT, comparaison
> à durée constante, rangement de l'avis, travail `youtrust_sync_signature` assuré s'il n'y en a pas déjà un EN ATTENTE
> pour la demande, priorité 22, sans demandeur) + `index.ts` (branchement supabase-js avec la clé de service ; dépôt
> idempotent `onConflict: 'event_id', ignoreDuplicates`). Réponses : 401 signature fausse / absente / corps modifié ;
> 405 hors POST ; 400 corps illisible ou sans `event_id` ; 500 secret absent ou panne de base (Youtrust renvoie) ; 200
> sinon. ⭐ Un avis rangé dont le travail a raté : au RENVOI, le doublon est ignoré MAIS le travail est posé.
> Essai `supabase/functions/youtrust-webhook/test_logique.mjs` (Node 24 lit le TypeScript tel quel) **14/14**, avec
> témoin (signatures calculées par node:crypto, un autre code que celui de la fonction). Vérifié en base (lecture) :
> `requested_by` peut être vide, `status` vaut `pending` par défaut, aucun déclencheur sur ce type de travail.
> ⚠ NON ÉPROUVÉ : le vrai Deno de Supabase (pas de Deno sur le serveur) et un vrai avis.
> **Les gestes du déploiement (Frédéric)** : (1) déployer `npx supabase functions deploy youtrust-webhook
> --no-verify-jwt` ; (2) créer l'abonnement dans l'app Youtrust (sandbox) vers
> `https://<projet>.supabase.co/functions/v1/youtrust-webhook`, avis `signature_request.*` et `signer.*` du tableau
> §2 bis ; (3) poser le secret : `npx supabase secrets set YOUTRUST_WEBHOOK_SECRET=…`. Sans L5-2 (worker), les avis
> seront rangés et les travaux refusés proprement (« pas encore en service »).
>
> ✅ **L5-2 CODÉ LE 05/11** (« vas-y » de Frédéric ; rien commité, services non redémarrés) : `handleYoutrustSyncSignature`
> relit la demande chez Youtrust, met à jour les signataires (statut ; heure de signature lue UNE fois sur le
> signataire), la table (`status`, `done_at`, `canceled_at`, `expired_at`, `expiration_at`, `last_synced_at`,
> `last_event_at`), le miroir R3 (`pending` « x/N », `signed`, `cancelled`, `expired`) et marque les avis vus comme
> traités. **D37** : `signed_at` = « 05/11/2026 à 10:52 » (heure de Paris), l'ISO dans `signed_at_iso` ; **D39** : aucun
> refus sur l'interrupteur ; **D18 / R1** : « à la main » et autre fournisseur non touchés ; 404 = refus d'état écrit
> sur la demande, 503 = erreur ordinaire (rejouée). Les transitions sont rendues pour L5-3 / L5-4.
> Essai `Console/test_youtrust_sync_signature.js` **23/23** (dont la VRAIE regex du pilotage qui lit la date, rejeu
> idempotent, témoin inverse) ; voisins verts (18, 23, 23, 26, 22, 15, 8 ; couples 26).
> ⚠ NON ÉPROUVÉ en réel : que `GET /signature_requests/{id}` rende bien `signers[].status` et `completed_at` (à voir
> à la preuve sandbox, D40).
>
> ✅ **L5-3 CODÉ LE 05/11** (rien commité, services non redémarrés) : `rapatrierSigneYoutrust`, appelé par la mise à jour
> à `done`, UNE fois (`signed_storage_path`), AVANT de marquer les avis (un échec les laisse « à traiter ») : PDF signé
> (`version=completed`) sous `…/documents/<id>/signed/` + une preuve PDF par signataire sous `…/proofs/` (serveur
> toujours ; COFFRE seulement si l'original y est — la règle de stockage n'est pas réinterprétée) ; la colonne
> `storage_path` ne bascule vers le signé que s'il est au coffre ; `metadata_json.signed_document` (fournisseur youtrust,
> taille, sha256, date façon ImmoSign, liste des preuves) ; les preuves JSON (`lireAuditTrail`, ajouté au client) dans
> `app_signature_request.proofs` (une indisponibilité est notée, sans bloquer) ; l'original jamais écrasé ; un fichier
> qui n'est pas un PDF (ZIP) = erreur ordinaire, rien rangé. « À la main » : rien téléchargé.
> ✅ **L5-4 CODÉ LE 05/11** (D38) : `notifierSignatureYoutrust`, au MANDATAIRE de la demande, sur une TRANSITION
> seulement : « à vous de contresigner » (les mandants viennent tous de signer), « signé », « e-mail non remis /
> incident » (le signataire nommé), « expiré » ; l'index unique écarte le doublon ; une cloche en panne n'empêche pas la
> mise à jour (avertissement au journal).
> Essai `Console/test_youtrust_sync_signature.js` **42/42** (L5-2 + L5-3 + L5-4, témoin inverse) ; L5-1 14/14 ;
> voisins verts (18, 23, 23, 26, 22, 15).
> ✅ **COMMITÉ** (`781110d`, 05/11). ✅ **FONCTION DÉPLOYÉE LE 05/11** par moi, sur l'accord explicite de Frédéric
> (« déploie toi-même ») : `youtrust-webhook` version 1, ACTIVE, `verify_jwt = false`, fichiers identiques au commit
> (empreintes contrôlées avant). Éprouvée sans rien écrire : GET → 405 ; POST sans secret → 500 « secret absent » ;
> base inchangée (0 avis, 0 travail). ⚠ **Démarrage à froid : 1,34 s au premier appel** (0,08 à 0,10 s ensuite) — au-delà
> de la seconde exigée par Youtrust pour un premier envoi ⇒ **cocher « relance automatique » (auto_retry) à la création
> de l'abonnement** : la nouvelle tentative a 10 s de délai. Un avis perdu reste rattrapé par le travail suivant ou la
> nuit (lot 7).
> ✅ **GESTES FAITS LE 05/11 au soir** : abonnement créé par Frédéric dans l'app Youtrust (sandbox, tous les avis
> cochés — sans effet nuisible : un avis sans demande est rangé sans travail) ; secret `YOUTRUST_WEBHOOK_SECRET` posé
> par lui dans Supabase (vérifié : un avis à signature fausse rend désormais 401 « signature invalide », plus 500 ;
> base inchangée) — ⚠ que ce soit la BONNE clé ne se saura qu'au premier vrai avis ; **les 4 services redémarrés par
> Frédéric à 18:15:51-53**, file vide avant (0 en attente, 0 en cours ; dernier travail fini à 18:15:41), code sur le
> disque = `781110d` sans modification, processus lancés APRÈS l'écriture du fichier (16:43:28), journaux de démarrage
> normaux (le service Documents annonce `youtrust_sync_signature`), 0 erreur depuis.
> **RESTE** : la preuve sandbox (D40). ⚠ L'envoi exige l'interrupteur `signature_youtrust` (éteint pour tous).
> ✅ **PREUVE SANDBOX D40 — FAITE (05/11 au soir → 06/11 07:09, bien d'essai 61398 / mandat 18420, Chrome de Frédéric)** :
> ✅ **2 sur 3 signés, chaîne prouvée de bout en bout jusque-là** : génération chez nous seulement (`f0d73f5a…`,
> 183 593 octets, photo des 3 signataires, `sans_hektor`) → envoi (`0eed0f32…`, 4 s, 3 × `otp_email`, demande
> Youtrust `c3d1f2be…`, notre ligne `4f9582e4…`) → avis reçus par la fonction et traités 4 à 6 s après (activated,
> notified ×2, link_opened, done ×2, notified mandataire) → Pauline signée 20:03:49 UTC, Delphine 20:07:13 UTC,
> document « pending 2/3 » → cloche « Le mandat : à vous de contresigner » posée au mandataire à 20:07:21.
> ✅✅ **D40 PROUVÉ LE 06/11 au matin** : contresignature de Frédéric 06:09:05 UTC → avis `signer.done` +
> `signature_request.done` traités à 06:09:11 → demande `done` (06:09:07) → document « signed 3/3 »,
> `signed_at` « 06/11/2026 à 07:09 » (heure de Paris, façon ImmoSign) + `signed_at_iso` → **PDF signé rangé à 06:09:12**
> sous `…/signed/Mandat de vente - 18420 - signe.pdf` (285 311 octets) **au coffre ET sur le serveur, empreinte
> identique** (`f832c780…`, recalculée sur le disque), la colonne `storage_path` pointe vers lui, **l'original intact**
> (183 593 octets) → **3 preuves PDF** (une par signataire, `proofs/`, coffre + serveur, empreintes vérifiées) et 3
> preuves JSON dans la table → cloche « Le mandat est signé » au mandataire à 06:09:14, et « Le mandat est signé » au
> fil d'activité de la fiche. La nuit n'a rien abîmé (vérifié avant la signature : fiches, attentes, document, demande,
> 0 critical à la sonde de 06:48).
> ⚠ **Vu à l'écran : le cockpit dit encore « Numéro attribué — à éditer »** alors que le mandat est signé — c'est
> exactement le point P8 (« le cockpit qui voit un mandat Youtrust ») : `ckSigStatus` prend le PREMIER document
> « mandat » de la liste (ici l'ancien ImmoSign annulé), pas celui de Youtrust.
> ~~⏰ RESTE : la contresignature de Frédéric (mandataire), le 06/11 au matin après le run.~~ Interrupteur : allumé
> seulement 19:37:50-19:38:58, 19:42:03-19:45:23 et 19:58:56-19:59:28 ; **éteint** depuis (la suite n'en a pas besoin).
> **Ce que l'essai a trouvé (rien n'est corrigé dans le code, tout est à trancher par Frédéric)** :
> 1. **Une vieille procédure ImmoSign « en attente » cache l'éditeur** (mode `envoye` du cockpit) : il a fallu annuler la
>    procédure d'essai 107 du 19/08 (accord de Frédéric ; un 2ᵉ travail d'annulation, né d'un clic bloqué par la fenêtre
>    de confirmation, a fini en erreur « déjà supprimée »).
> 2. **Le garde-fou P7 a mordu pour de vrai** : « TEST GTI Delphine » sans prénom → génération refusée. Fiche corrigée
>    dans l'app (prénom Delphine, nom TEST GTI) ; **Hektor a refusé** (« formulaire d'édition introuvable » : fiche
>    archivée), la correction n'existe que chez nous.
> 3. ⚠⚠ **Corriger un e-mail / un portable dans la fenêtre d'envoi RÉÉCRIT LA FICHE DU CONTACT** (chez nous + un travail
>    `update_hektor_mandant_contact` + une attente `app_contact_pending`). Les alias d'essai se sont retrouvés sur les
>    fiches 115527 et 140142 ; Hektor n'a rien pris (fiches archivées, puis garde anti-écrasement → 2 conflits). Adresses
>    d'origine remises chez nous, les 2 attentes abandonnées (trace dans `app_pending_resolution`). ⬜ **À confronter à
>    D33** (« l'écran ne corrige que les canaux de remise ») : une correction pour UN envoi doit-elle toucher la fiche ?
> 4. ⚠⚠ **Le mandataire part en code SMS sur le portable de l'annuaire** (ici le vrai portable d'Emmanuelle PEREIRA) et
>    **l'écran ne permet pas de le changer**. Le travail accepte `payload.mandataire` (D21, « fenêtre d'envoi ») : c'est
>    ce qui a servi, posé à la main avec l'accord de Frédéric (mandataire = lui, code par e-mail).
> 5. **La sandbox refuse les alias « + »** (déjà su le 05/11 matin) : 1ᵉʳ envoi `87e3855a…` en HTTP 400 à l'activation,
>    brouillon jeté tout seul au rejeu. ⚠ **Le worker n'écrit pas le corps du refus** (ni au journal ni dans `erreur`) :
>    il a fallu le retrouver dans ce plan.
> 6. **Gmail range les e-mails des deux mandants dans UNE conversation** (même objet, même boîte) : Frédéric n'a vu
>    que le premier. En production chaque mandant a sa boîte ; sans effet, sauf deux mandants à la même adresse.
> 7. L'avis `signature_request.deleted` du brouillon jeté reste « non traité » pour toujours (plus rattaché à rien) :
>    sans effet, à savoir.
> 8. **Le monitoring a crié 3 fois** (20:48 : 2 critical « travaux en erreur » ; 21:51 : `data.contact_conflit` 2) — tout
>    vient de l'essai. Conflits soldés ; ✅ **les 5 travaux en erreur tranchés le 05/11 à 23:21** (accord de Frédéric),
>    même trace que `app_action_resolve` dans `app_pending_resolution` (« refait » : annulation en double et 1ᵉʳ envoi,
>    faits par un autre travail ; « abandon » : les 3 mises à jour de contact). Vérifié avant : 0 ligne de carnet
>    d'annonce au même instant, donc l'abandon ne défaisait rien. L'écran l'aurait refusé (moins de 3 h) : écrit en
>    base directement. Reste à trancher sur 30 jours : **0**.
>
> 🔎 **AUDIT P8 (06/11, lecture seule : code worker + écran + base ; rien codé)**
> **A. Le retour du signé — ImmoSign** (`downloadSignedProcedureDocument`, worker ~5677-5729) : **même ligne**, le
> fichier signé est rangé **à côté** (`…/<id>/signed/<nom> - signe.pdf` au coffre, `signed_<nom> - signe.pdf` à plat sur
> le serveur) et la colonne `storage_path` (+ taille, empreinte) **bascule vers le signé** ; l'original n'est ni écrasé ni
> effacé ; `metadata_json.local_archive_path` reste celui de l'original. Preuves : 2 ZIP (`procedure-<id>.zip`,
> `preuves-<id>.zip`) dans `metadata_json.immosign_files`, au coffre sous `immosign/` seulement si `shouldKeepCloud`
> (le signé, lui, monte TOUJOURS). Mesure : 466 signés (465 ImmoSign + 1 Youtrust), 466 pointent `…/signed/…`, 464 ont
> leur ZIP de preuves (manque 24113, connu ; et le Youtrust, qui range autrement), 0 « signé à la main ».
> **Youtrust** (`rapatrierSigneYoutrust` ~6649) : même principe, mais (1) la colonne ne bascule que si l'original était
> au coffre (sinon signé serveur seul, `signed_document.storage_path` nul) ; (2) preuves = 1 PDF par signataire dans
> `signed_document.preuves[]` (`proofs/` au coffre, `proofs_preuves-…` à plat sur le serveur), JSON dans
> `app_signature_request.proofs` ; (3) `signature` sans `procedure_id` (R2), avec `provider`, `provider_request_id`,
> `signature_request_id`, `signed_at` façon ImmoSign + `signed_at_iso`, état `expired` en plus.
> **B. La nuit ne touche pas un document Youtrust** (pas de numéro Hektor, source `app`, `signatureProtegee`, pas de
> procédure). ⚠ Risques LATENTS, jamais observés : si la ligne recevait un jour un `hektor_document_id`,
> `persistConsoleDocumentFile` remonterait l'ORIGINAL sur le chemin du SIGNÉ (le garde « signé préservé » ne couvre que
> les lignes `modelo`) ; `prepare_document_cloud` monterait l'original d'un signé resté serveur seul ; le ménage du coffre
> (`menage_coffre_documents.js:205`) protège `immosign/` et `signed/` mais **pas `proofs/`** ; « Supprimer » sur une ligne
> `sans_hektor` finit en erreur (« ID Hektor supprimable absent ») — sans dégât, mais le geste n'existe pas.
> **C. L'écran** — ce qui MARCHE pour Youtrust : la pastille (`SignatureBadge`, en cours et signé), la liste Documents et
> ses filtres, « Ouvrir le signé », le fil d'activité (`app_cockpit_activite` accepte `provider_request_id`), le pilotage
> (même forme de date). Ce qui NE MARCHE PAS :
> 1. **Cockpit + Mandat V3** (`ckSigStatus`, App.tsx:32775 ; `mv3Mode`, 33087) : prend le PREMIER document dont le nom
>    contient « mandat » ; la liste est triée `document_type` puis `document_name` (api.ts:8778) et la collation met
>    `document` (Hektor) avant `Mandat` (l'app) → sur 61398 il lit un vieux « Mandat (Avec saisie du numéro) » sans
>    procédure → `null` → « à éditer ». Et un Youtrust EN COURS serait ignoré même premier (exige `procedure_id`). Pendant
>    une signature Youtrust, Mandat V3 réafficherait donc l'éditeur. Textes « ImmoSign » en dur (32851, 33503, 33519).
> 2. **Boutons qui se trompent sur un Youtrust en cours** : « Signé à la main » (12078) reste affiché et la fonction
>    `app_console_mark_document_signed_manual` ne teste ni le fournisseur ni l'état (elle marquerait « signé » une demande
>    encore ouverte chez Youtrust) ; « Signature » de `MandatSignatureTracker` (11630) et de la liste quand l'interrupteur
>    est éteint (12072) renvoient vers Hektor/ImmoSign pour un second envoi.
> 3. **Aucun suivi par personne** (ni ImmoSign ni Youtrust) : rien dans `src` ne lit `app_signature_request` ;
>    `MandatSignatureTracker` = une pastille par document (et il liste les 11 « mandat » de 61398, vieux modèles compris).
> 4. **Aucun geste Youtrust à l'écran** : le worker a `youtrust_remind_signer`, `youtrust_cancel_signature`,
>    `youtrust_signing_link` ; aucune fonction d'`api.ts` ne les pose. Relancer / Annuler restent gardés par `procedure_id`
>    (donc masqués, sans faux geste ImmoSign).
> 5. **Ouvrir les preuves : impossible pour TOUS** — la règle de lecture du coffre (`hektor_console_documents_read_scope`)
>    n'ouvre qu'un objet dont le chemin est ÉGAL à la colonne `storage_path` d'un document `cloud_available` : ni les ZIP
>    ImmoSign, ni les PDF de preuves Youtrust, ni l'ORIGINAL d'un document signé ne sont lisibles depuis l'écran.
> 6. **Après l'envoi** : la liste est relue tout de suite (avant la fin du travail, ~4 s) sans relance ; depuis l'éditeur,
>    aucune relecture ; le cockpit n'est relu qu'à la relecture de l'app. L'état `expired` n'a ni pastille ni libellé.
>    ⚠ Correction après vérification : depuis la liste Documents, le travail d'envoi est SUIVI (`rememberHektorActionJob`)
>    et sa fin relit l'app (App.tsx:15312-15320) — la liste se met donc à jour seule. Le trou réel : l'éditeur
>    (pas d'`onSent`), et une signature faite plus tard (avis Youtrust) ne relit pas un écran resté ouvert.
> **D. Mesure du cockpit sur le parc (règle d'aujourd'hui rejouée en SQL, même tri)** : 630 biens vivants ont au moins
> un document « mandat » ; 317 n'ont aucun état fiable ; 240 lisent bien « signé ». ⚠ **40 lisent « rien » alors qu'un
> état fiable existe** (36 signés, 4 en attente) et **21 ont à la fois une attente et un signé** (le gagnant dépend de
> l'ordre alphabétique). Parmi les biens dont le cockpit montre le cycle du mandat (validation « à contrôler ») :
> **3 affichent « à éditer » alors qu'un mandat signé existe** (61398, 63173, 62457) et 4 mélangent attente + signé.
> Aucun signé n'est antérieur au mandat en cours (0 sur 299 biens) : le risque « vieux mandat signé » n'existe pas.
> **E. Les preuves Youtrust (mesurées sur l'essai)** : par signataire, la preuve PDF (piste d'audit) ET la piste JSON :
> identité (nom, prénom, e-mail, téléphone), adresse IP, contexte (« signé depuis le lien envoyé par courriel »), heure du
> consentement et de fin, mode du code + heure de validation, **empreinte du document de départ (`initial_hash`) =
> l'empreinte de NOTRE original (vérifié : `a0dadac8…` identique)**, empreinte après chaque signature, certificat
> (DN, OID, empreinte, PEM ; « Yousign - Test » en sandbox), horodatage qualifié « Non », l'expéditeur (API + IP de notre
> serveur). Plus l'historique des avis (`app_signature_event`). Non récupéré : la piste d'audit fusionnée de la demande
> (`/signature_requests/{id}/audit_trails/download`, restreinte, activation par le support Youtrust) — inutile, on a
> chaque signataire. ⚠ **La piste JSON contient le CODE à usage unique** (`authentication.code`) : on le garde en base
> sans raison → à masquer.
> **RÉPONSES DE FRÉDÉRIC (06/11)** : P8-2 = garder « Signé à la main » mais, **si une procédure est lancée**, un message
> qui explique d'annuler la procédure pour pouvoir signer à la main ; P8-3 (suivi par personne) = OK ; P8-4 = OUI + analyser
> ce que Youtrust donne comme preuves (fait, ci-dessus) ; P8-1 = à réexpliquer en détail (règle hybride) ; P8-5 =
> « pas nécessaire pour Youtrust ? » (réponse : presque — voir C.6 corrigé).
> **CONSIGNES DE FRÉDÉRIC (06/11, suite)** : (1) « ImmoSign a un système différent pour récupérer les états, il ne faut
> pas le casser avant la coupure » ; (2) avant la coupure, **UN SEUL bouton « Signature »** qui propose un choix :
> **signature électronique (Youtrust) · signature Hektor (ImmoSign) · signature manuscrite**.
> **Ce qui fait vivre ImmoSign (P8 n'y touche PAS)** : lecture des états par la page Documents de Hektor
> (`parseSignatureFromRow` → `reconcileSignatureStates`) à l'ouverture de la fiche et dans `sync_console_documents` ;
> le suivi de nuit (`enqueue_console_sync_jobs.js`, `loadSignatureFollowSet` : toute annonce à procédure en cours) ;
> le retour du signé (`downloadSignedProcedureDocument`, ZIP) et des compagnons (`persistImmoSignCompanionFiles`) ;
> Relancer / Annuler (`relance_signature`, `cancel_signature_procedure`) ; la garde R1 (`signatureProtegee`). P8 ne change
> que la LECTURE de l'écran (cockpit : la règle d'aujourd'hui devient le repli ; une procédure ImmoSign reste « fiable »)
> et les boutons. ⚠ L'app ne sait PAS créer une procédure ImmoSign (aucun appel `ImmoSign-create…`) : « signature Hektor »
> = ouvrir Hektor sur l'onglet Documents (fenêtre actuelle), et le document doit EXISTER chez Hektor.
> **Les portes de signature d'aujourd'hui** : « Signature » de la liste Documents (interrupteur allumé → fenêtre Youtrust ;
> éteint → « Oui, ouvrir Hektor ») ; « Signé à la main » (à part) ; « Signature » du suivi du mandat
> (`MandatSignatureTracker`, toujours Hektor) ; l'éditeur qui ouvre la fenêtre Youtrust après « Générer » (allumé).
> ⚠ **Réaudit (06/11, Frédéric : « normalement le document est déposé dans Hektor »)** : vrai AUJOURD'HUI — interrupteur
> ÉTEINT en production, `handleGenerateMandatDocument` pose `upload_document_to_hektor` ; mesuré : les 18 générations
> d'avant le 05/11 (24113, 62774) ont leur dépôt `done` (une seule sans dépôt retrouvé, 24113 le 29/06). Seule la génération
> de l'essai (interrupteur ALLUMÉ, 05/11) est `sans_hektor`, par la règle de Frédéric du 26/10 (« allumé = UNIQUEMENT
> Youtrust … sans dépôt chez Hektor »), qui avait remplacé la 1ʳᵉ forme de D24 (« chez nous d'abord, Hektor le reçoit
> ensuite en arrière-plan »). Le choix à trois boutons revient sur cette règle → à trancher.
> ✅ **TRANCHÉ (06/11) : A, « comme aujourd'hui il y a deux temps : d'abord l'édition d'un document qui fonctionnait,
> puis la signature » — et REPRENDRE LE CODE QUI FONCTIONNAIT** (le chemin éprouvé, pas le dépôt différé dormant).
> **Audit du chemin éprouvé** : `handleGenerateMandatDocument` (éteint) → PDF sous `temp/uploads/<travail>/` →
> `upload_document_to_hektor` (priorité 40) → `envoyerDocumentAHektor` → la ligne naît de la LISTE Hektor
> (`upsertConsoleDocuments`, source Hektor, `hektor_document_id`) → `persistProvidedDocumentFile` (serveur + coffre si
> `shouldKeepCloud`) → temporaire retiré → relecture de la fiche. L'éditeur attend la ligne jusqu'à 150 s (App.tsx:5793)
> puis ouvre la fenêtre « Signature Hektor ». **Il sait déjà porter une donnée de l'éditeur jusqu'à la ligne** : le prix
> d'avenant (`avenant_new_price`) voyage dans la charge du dépôt et est FUSIONNÉ dans `metadata_json` après le dépôt
> (fusion non destructive, worker ~9762). La synchro de nuit GARDE les clés ajoutées (`...current.metadata_json`, 5089)
> et l'état Youtrust (`signatureProtegee`, 5108).
> **Ce qui manque sur ce chemin pour Youtrust** : la photo des signataires (`signataires_du_pdf`), `contenu_imprime`,
> `remplace_document_id` + la marque P5 de l'ancien PDF, `generation_job_id` — à faire voyager comme le prix d'avenant.
> ⛔ **LE PIÈGE TROUVÉ** : une ligne DÉPOSÉE chez Hektor repasse dans `persistConsoleDocumentFile` à CHAQUE synchro
> (boucle ~6958). Sa garde « signé préservé » ne couvre que les modèles Hektor (`modelo && signed_document`, 5221). Une
> fois signée par Youtrust (ou par ImmoSign), elle relirait l'ORIGINAL (`local_archive_path`) et le MONTERAIT AU COFFRE
> SUR LE CHEMIN DU SIGNÉ (`storage_path`), empreinte et taille comprises : l'écran ouvrirait le non signé. Mesure : les
> 466 documents signés portant `signed_document` sont 464 modèles Hektor + 1 ligne `hektor_immosign_signed` absente +
> l'essai Youtrust ⇒ **le cas « déposé puis signé » n'est JAMAIS arrivé** (les 18 générations n'ont jamais été signées) ;
> la garde élargie à « toute ligne qui porte `signed_document` » ne change donc rien à l'existant.
> 🔎 **AUDIT « LA MEILLEURE SOLUTION » (06/11, Frédéric : « audit, analyse projet et chantier »)**
> 1. ⭐ **« Chez nous d'abord, Hektor ensuite » TOURNE DÉJÀ EN PRODUCTION pour les documents ajoutés à la main** depuis
>    le 19/10 (lot 2c du chantier ③ : RPC `app_console_creer_document_optimistic`, api.ts:9076 →
>    `completerEnvoiDocumentDiffere`) : 11 travaux, 6 documents, **tous finis chez Hektor** (`envoye`), repris par la tâche
>    « GTI Reprise Envois Hektor » (12:30) quand le 1ᵉʳ essai échoue. ⚠ Le commentaire du worker (~9699, « DORMANT : aucun
>    appelant ») est PÉRIMÉ. Et ces lignes `source = app` reçoivent bien de la synchro le bloc signature de Hektor
>    (`to_send`, `hektor_doc_id`) : la lecture ImmoSign s'applique donc à NOTRE ligne une fois déposée.
> 2. ⛔ **UN DÉFAUT RÉEL, NON CONNU, trouvé par cet audit** : le 23/10 sur **59203**, 4 documents ajoutés à la main ont été
>    DÉPOSÉS chez Hektor (n° 715224-715227) mais le contrôle a conclu « Upload Hektor non confirmé dans la liste » → statut
>    `echec` → la reprise du 24/10 les a **RENVOYÉS** (n° 715252-715255) ⇒ **4 documents EN DOUBLE chez Hektor**, et 2 lignes
>    chacun chez nous (la nôtre + une `hektor_console_uploaded_private`). La reprise ne regarde pas si Hektor a DÉJÀ le
>    fichier. Cause du « non confirmé » NON ÉTABLIE (4 envois en 30 s ; le même nom est confirmé le lendemain). Le chemin
>    « Hektor d'abord » partage `envoyerDocumentAHektor` et donc le même risque à son rejeu.
> 3. Le piège du signé (ci-dessus) vaut pour toute ligne déposée : à fermer AVANT qu'un mandat déposé soit signé.
> **⇒ LA SOLUTION RECOMMANDÉE — « l'édition chez nous, le dépôt Hektor en arrière-plan, la signature au choix »** :
> (a) l'édition naît TOUJOURS chez nous (le code du 26/10, prouvé le 05/11 : 4 s, photo des signataires) — l'interrupteur
> ne décide plus du chemin de génération ; (b) le dépôt chez Hektor part TOUJOURS ensuite, par le chemin DÉJÀ EN
> PRODUCTION des ajouts (statut `a_envoyer`, reprise à 12:30 si Hektor ne répond pas) ; (c) AVANT, corriger son défaut :
> relire la liste de Hektor avant de conclure « non confirmé », et avant tout renvoi ADOPTER le document s'il y est déjà ;
> (d) étendre la garde du signé à toute ligne qui porte `signed_document` ; (e) un seul bouton « Signature » à trois
> choix — Youtrust (interrupteur + photo), Hektor (seulement une fois le dépôt `envoye`, sinon « dépôt en cours »),
> manuscrite — et le message « annulez la procédure en cours » ; (f) la lecture ImmoSign ne change pas. À la coupure,
> on éteint le dépôt et le choix Hektor, rien d'autre.
> ✅ **VALIDÉE par Frédéric (06/11) « à une condition : un audit pour être sûr que tout fonctionne et est conforme à mon
> projet »** → 🔎 **AUDIT DE CONFORMITÉ (06/11, code + base + notes ; rien codé)** :
> **Conforme** — (1) à l'approche hybride du 29/06 (mémoire `feature-pdf-mandat-vers-hektor` : « Générer → tout
> s'enregistre (Hektor + local + Supabase), puis "Faire signer ?" ») : mêmes deux temps, ordre inversé seulement ;
> (2) à D24 première forme (26/10) ; (3) au chantier ③ (lot 2c, déjà en production pour les ajouts) et au chantier ⑧
> (« naître complet chez nous, Hektor complète ») ; (4) aux 5 règles : un numéro ne se perd jamais (notre ligne garde son
> id, adopte le n° Hektor), Hektor confirme sans écraser (adoption par le numéro posé AVANT la réindexation), fin visible
> (à condition G5), Hektor reste à jour (dépôt toujours), le miroir n'est pas touché ; (5) à la règle de stockage
> (`shouldKeepCloud` inchangée) ; (6) à R1/R2/D12/D18/D21/D31-33/P5 (rien de ces décisions ne bouge) ; (7) au quota Hektor
> (un dépôt par mandat, comme aujourd'hui). (8) ⭐ **La lecture ImmoSign s'applique à notre ligne** : elle retrouve la
> ligne suivie par `signature.hektor_doc_id` (~5889), que la synchro pose sur une ligne `app` déposée (mesuré : les 4 de
> 59203 l'ont) ; à défaut, par le nom (candidate, ~5930).
> **Ce qui ne fonctionnerait PAS sans correctif (G1-G6, à inclure dans le lot)** :
> - **G1 doublon** (59203, 4 documents en double chez Hektor) : relire la liste avant « non confirmé », adopter avant
>   tout renvoi.
> - **G2 signé écrasé** : la garde « signé préservé » (~5221) ne couvre que les modèles Hektor → toute ligne à
>   `signed_document`.
> - **G3 « supprimé chez Hektor » sur un mandat signé** : un document déposé qui part en ImmoSign QUITTE la liste des
>   dépôts (commentaire ~5732 ; seul précédent réel, 24113 le 29/06 : la ligne déposée a disparu, le signé vit dans une
>   ligne à part `immosign-signed-710698-2`). Notre ligne `app` ne serait pas supprimée (la purge ignore la source `app`)
>   mais MARQUÉE « absente » (~5165) → l'exempter quand elle porte une signature suivie.
> - **G4 dépôt sans copie au coffre** : `completerEnvoiDocumentDiffere` exige `storage_path` (~9517) ; un bien hors statut
>   « vivant » n'en a pas → lire la copie serveur, comme l'envoi Youtrust.
> - **G5 fin visible** : l'état du dépôt (`a_envoyer` / `echec`) n'est affiché que par l'ancienne présentation (12257) →
>   le montrer dans la liste v21 et dans le choix « Signature Hektor » (« dépôt en cours / en échec, repris à 12:30 »).
> - **G6 l'éditeur** attend aujourd'hui Hektor (150 s) → attendre NOTRE ligne (4 s), puis ouvrir le choix.
> **À trancher à part** : les 4 doublons de 59203 chez Hektor (suppression = geste chez Hektor) ; et D42 à écrire : « avant
> la coupure, trois signatures (Youtrust, Hektor, manuscrite) ; à la coupure, Youtrust et manuscrite » (remplace le
> rappel du 26/10 « allumé = uniquement Youtrust »).
> **La preuve** : les essais hors ligne qui découpent déjà ces chemins (`test_envoi_hektor_differe.js`, reprise, garde
> R1, photo, remplacement) + témoins inverses ; puis en réel sur 61398 : générer → ligne chez nous → dépôt chez Hektor
> confirmé → les trois choix. ⚠ Lancer une vraie procédure ImmoSign consomme un crédit chez Hektor : à décider.
> ✅ **« Oui supprime doublons. Et vas y » (Frédéric, 06/11)** :
> - **Doublons de 59203 SUPPRIMÉS (06/11 ~08:40)** : les 4 seconds dépôts (n° Hektor 715252-715255, lignes
>   `hektor_console_uploaded_private`) par le geste « Supprimer » de l'app (`delete_document_from_hektor`, trace complète
>   dans le journal des suppressions, raison « doublon_hektor_59203 »). Vérifié avant : empreintes IDENTIQUES aux
>   originaux, fichiers distincts. Après : 4 travaux `done`, suppression CONFIRMÉE chez Hektor par le worker, il reste
>   1 ligne par document (la nôtre, n° 715224-715227), présente, fichier au coffre.
> - **D42 (06/11)** : *avant la coupure, trois signatures — Youtrust, Hektor (ImmoSign), manuscrite ; à la coupure, Youtrust
>   et manuscrite.* Remplace le rappel du 26/10 « allumé = uniquement Youtrust ». L'édition naît chez nous, le dépôt chez
>   Hektor part ensuite.
> - ✅ **P8-0 CODÉ (worker, 06/11) — NON ACTIF** (services non redémarrés ; nouvel interrupteur `mandat_nait_chez_nous`
>   absent = éteint) : **G1** anti-doublon (`numerosHektorDejaPris`, `documentNonReclame` ; une ligne déjà tentée —
>   `echec` ou travail rejoué — ADOPTE le document que Hektor a déjà au lieu de le renvoyer ; la liste est relue 3 fois
>   avant « non confirmé » ; le numéro choisi est celui qu'aucune autre ligne ne réclame) ; **G2** « signé préservé » pour
>   toute ligne à `signed_document` + `monterSigneAuCoffre` (« préparer » un signé monte le SIGNÉ) ; **G3**
>   `signatureSuivieOuSigne` exempte du marquage « absent chez Hektor » ; **G4** dépôt différé depuis la copie serveur ;
>   **génération** : interrupteur allumé → `enregistrerMandatChezNous` (ligne `a_envoyer`) puis `poserDepotMandatChezHektor`
>   (un seul travail `upload_document_to_hektor` avec `app_document_id`, jamais deux au rejeu ; un échec de pose ne fait
>   pas tomber la génération, la reprise de 12:30 le fera). Éteint : exactement le chemin d'avant (A1 le prouve).
>   Commentaire « DORMANT » du worker corrigé. **Essais** : `test_envoi_hektor_differe` 44/44 (+9 : g1-g7) ;
>   `test_p8_0_signe_preserve_et_absent` 14/14 (neuf) ; `test_mandat_chez_nous_et_mandataire` 32/32 (+10 : A4-A5) ;
>   `test_photo_signataires_pdf` 23/23 ; `test_regeneration_remplace` 23/23 ; `test_garde_r1_signature` 26/26 ;
>   `test_youtrust_sync_signature` 42/42 ; `test_nettoyage_temporaire` 9/9. **Témoins inverses (worker de HEAD)** :
>   g1, g3, g5 ROUGES (renvoi au lieu d'adopter), g6 fait tomber l'essai (« sans fichier ») ; G2-1 ROUGE et MONTRE le
>   défaut en vrai (« LIT original | MONTE …/signed/… ») ; G2-4, G2-7, G3-1, G3-5 rouges (absents).
>   ⏰ **RESTE de P8** : l'écran (G5, G6, P8-1 cockpit, P8-2 bouton unique, P8-3 suivi, P8-4 preuves, P8-5), la garde de
>   « signé à la main » en base, puis l'allumage et la preuve sur 61398.
> - ✅ **P8-1 + G5 + G6 CODÉS (écran, 06/11) — commit `3c32daa` pour le worker ; l'écran NON DÉPLOYÉ** :
>   **P8-1** `src/lib/etatSignatureMandat.ts` — le cockpit et Mandat V3 lisent TOUS les documents du mandat et le plus
>   récent état fiable l'emporte (Youtrust tous états, procédure ImmoSign, signé, PDF de l'éditeur) ; ⚠ **piège trouvé par le
>   rejeu** : pour ImmoSign `sent_at` = le jour où l'app a VU l'attente (18/08, 15/10), pas l'envoi → entre procédures
>   ImmoSign, c'est le NUMÉRO qui ordonne (une attente de numéro inférieur au signé est périmée : 62806 809<843, 59502
>   372<386, 63066 851<853). Textes « ImmoSign » en dur remplacés selon le fournisseur. **G5** la liste v21 (et l'ancienne)
>   montre « Chez nous — dépôt chez Hektor en cours / a échoué, il sera repris à 12:30 ». **G6** l'éditeur relit
>   `mandat_nait_chez_nous` au clic : la ligne est là en secondes, la signature Hektor n'est proposée qu'au dépôt CONFIRMÉ
>   (occupé jusque-là ; échec dit et arrêt). **Essais** : `test_etat_signature_mandat.cjs` 23/23 (ancienne règle rejouée à
>   côté : 8 cas où elle avait raison → même réponse) ; build OK ; conjoints 26/26, écarts 18/18.
>   **REJEU SUR LE PARC (SQL, lecture seule, 630 biens vivants à document « mandat »)** : 581 IDENTIQUES ; 49 changent —
>   38 « rien » → « signé » (dont les 5 dont le cockpit montre le cycle : 61398, 40612, 62457, 63173, 63248), 8 « attente
>   périmée » → « signé », 2 « rien » → « attente », et **1 seul « signé » → « en attente » : 63443** (procédure 958 en cours
>   APRÈS la 951 signée, mandat 18991) — à regarder avec Frédéric. ⚠ Non vu à l'écran (pas de session sur un serveur local).
>   Commité `aa0baae` (06/11).
> - ✅ **P8-2 CODÉ (écran, 06/11) — COMMITÉ, NON POUSSÉ, NON DÉPLOYÉ ; GARDE EN BASE POSÉE** : **un seul bouton « Signature », trois choix**
>   (`src/lib/choixSignature.ts` + `ChoixSignatureFenetre`), allumé seulement si `signature_youtrust` OU
>   `mandat_nait_chez_nous` l'est (`useChoixSignatureActif`) — les deux éteints : les boutons d'avant, à l'identique. Les trois
>   choix restent VISIBLES ; un choix fermé ne fait que dire pourquoi. **Youtrust** : interrupteur + PDF de l'éditeur.
>   **Hektor** : le document doit être chez Hektor (né chez nous : dépôt `envoye` ; sinon « dépôt en cours » / « échec, repris
>   à 12:30 » / « pas chez Hektor »). **Manuscrite** : mandat ou avenant. ⭐ **Consigne de Frédéric** : une procédure lancée
>   (Youtrust `pending`, ou ImmoSign `pending` avec procédure) → les trois restent, chacun dit « annulez-la d'abord ».
>   Branché sur : la liste Documents (les deux présentations), le suivi de signature du mandat (`MandatSignatureTracker`,
>   + sa signature manuscrite et sa fenêtre Youtrust), l'éditeur juste après « Générer » (le choix se met à jour tant que
>   le dépôt n'est pas confirmé). **Garde en base POSÉE le 06/11** (accord de Frédéric « Oui, vas-y ») : `supabase/patch_a2_p8_2_signe_main_garde_2026-11-06.sql`
>   (+ `_REPETITION`, tout dans une transaction annulée, 5 contrôles ; + `_INVERSE`) — `app_console_mark_document_signed_manual`
>   refuse pendant une signature en cours. **Essais** : `test_choix_signature.cjs` 21/21 (neuf) ; cockpit 23/23 (contrôle G6
>   mis à jour : l'attente du dépôt passe par le choix) ; conjoints 26/26 ; écarts 18/18 ; build OK (`tsc -b` compris).
>   **Pose (06/11)** : empreinte `66e1ebec…` → `160f30c2…`, droits inchangés (authenticated, postgres, service_role).
>   **Répétition : 5/5 vert**, document d'essai f0d73f5a **intact** après l'annulation (signé Youtrust, `updated_at` du matin).
>   **Témoin inverse** : l'ancienne fonction, remise dans une transaction annulée, ACCEPTE le « signé à la main » sur un
>   Youtrust en cours. ⚠ **Le 1er passage de la répétition a MENTI** : sa mise en scène, jouée en `authenticated`, n'écrivait
>   rien (RLS active, aucune règle UPDATE sur `app_console_document`), la fonction voyait « signé » et le contrôle [2] tombait
>   pour une fausse raison. Corrigé : mise en scène en propriétaire, APPEL seul en `authenticated`, chaque mise en scène vérifiée.
> **Le nœud** : interrupteur allumé, un mandat généré naît `sans_hektor` (D24) → « signature Hektor » impossible sans le
> DÉPOSER chez Hektor. Un chemin DORMANT existe (`completerEnvoiDocumentDiffere`, `upload_document_to_hektor` avec
> `app_document_id` : « aucun appelant ») — jamais éprouvé. À l'inverse, un document venu de Hektor (modèle ImmoSign,
> 498/499 des mandats signés) n'a pas la photo des signataires → pas de Youtrust (il faut régénérer).
> **RESTE (historique)** : les gestes de Frédéric (créer l'abonnement M4 dans
> l'app Youtrust, poser `YOUTRUST_WEBHOOK_SECRET`, redémarrer les 4 services file vide) ; puis la preuve sandbox
> (D40 : Frédéric signe 3 fois) — **avant la fin de l'essai (~09/11)** ; puis P8 (l'écran : suivi par personne,
> « Ouvrir les preuves », le cockpit qui voit un mandat Youtrust en cours) et le lot 7 (rattrapage de nuit).

### ⭐ L'OUTIL DE RÉDACTION — décision de Frédéric (26/10)
*« Actuellement Hektor, mais nous avons déjà développé dans l'app un éditeur de documents qu'il
faut utiliser. »* — Mesuré le 26/10 : les mandats signés viennent à 498/499 du modèle ImmoSign de
Hektor (texte Hektor : « Inscrit au registre des mandats au numéro… », « loi Hoguet ») ; s'y
ajoutent 95 fichiers « Mandat de vente 2026 » produits par **Word** (Microsoft) ou **iText**,
déposés dans Hektor ; le générateur de l'app n'a servi qu'à **18 essais** et **0 avenant**.
**L'outil à utiliser = `MandatDocumentEditor`** (mandat ET avenant ; `EstimationDocumentEditor`
pour l'avis de valeur ; le bon de visite n'est qu'imprimable). Ce qu'il a DÉJÀ tranché :
- **les mandants sont VERROUILLÉS** (`LockedDataField`) : *« pour ajouter, retirer ou corriger un
  mandant, passez par la fiche du contact »* ⇒ D22 et D23 se complètent **sur la fiche du
  contact**, par les gestes existants — jamais dans le document ;
- le bien et le prix se corrigent au **crayon** (`CorrigeableAnnonceField`), enregistré sur l'annonce ;
- un onglet **« Signature »** existe : destinataires pré-remplis depuis les mandants, canal
  e-mail / SMS, « modifiable avant envoi ImmoSign » ⇒ **c'est la base de la fenêtre d'envoi** (6a/6b),
  à faire évoluer plutôt qu'à recréer ; ⚠ en mode Youtrust, un signataire = une CASE du PDF :
  la liste ne peut plus accepter un destinataire libre sans mandant (le contrôle des repères
  refuserait l'envoi) ; le conjoint pré-ajouté (D22) doit donc devenir un **mandant de la fiche**.
- ⚠ à vérifier au lot 6a : que le gabarit couvre les modèles Hektor utilisés (« Mandat (Avec saisie
  du numéro) », « Mandat (Vente ou Recherche) », « Mandat de vente simple », « viager »…) ; l'état
  de l'interrupteur Mandat V3 (`VITE_APP_MANDAT_V3_ENABLED`) sur Vercel (absent des `.env` locaux) ;
  et la formation des négociateurs (le vrai changement pour eux : RÉDIGER dans l'app).

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

**⭐ D25 — LE CONJOINT NON LIÉ AU BIEN : ON LE LIE COMME MANDANT** *(Frédéric, 05/11 : « Le lier comme mandant »)*.
Audit du 05/11 (proposition §8) : sur 42 couples « conjoint nommé » mandants de biens vivants, le conjoint n'est mandant
du même bien que 10 fois ; les 32 autres sont connus chez nous (`couple_json.conjoint`) mais ne seraient ni dans le PDF
ni signataires. La fenêtre d'envoi **propose de lier le conjoint au bien comme mandant, en un clic CONFIRMÉ par l'agent**,
par la porte qui existe (`app_link_mandant_optimistic` → travail `link_hektor_mandant`, 5 fois `done`, jamais sur une
seconde fiche). Mesuré : les 14 conjoints déjà mandants d'un bien vivant viennent TOUS de Hektor (synchro) → Hektor
accepte une seconde fiche comme mandant. ⚠ À savoir : la porte de liaison n'a pas de refus sur un mandat numéroté, mais
celle du **retrait** en a un (`app_unlink_mandant_optimistic`) → un lien fait par erreur sur un mandat numéroté ne se
défait pas depuis l'app : d'où la confirmation. Corriger ce conjoint ensuite passe par « modifier le conjoint » (fiche
principale), jamais par la porte du mandant (§8.3 de la proposition). **Rien codé** : lot 6b, après la maquette.

**⭐ D26 à D30 — LES CINQ AUTRES RÉPONSES** *(Frédéric, 05/11 : « Oui, Q2 à Q6 », mes recommandations de la proposition §7)* :
- **D26 (Q2)** l'éditeur passe de 6 à 5 onglets : « Mandants » et « Signature » fusionnent en « Mandants et signataires ».
- **D27 (Q3)** la porte « modifier un mandant » apprend le **2e téléphone** (`phone_secondary`) : un portable saisi pour la
  signature ne remplace plus un fixe. ⚠ Touche la fonction `app_update_mandant_contact_optimistic` (liste de 8 champs) ET le
  worker (`updateHektorMandantContact` n'écrit que la 1re case `telephone[]`) : patch additif, à proposer avec son retour arrière.
- **D28 (Q4)** Youtrust allumé, le bouton « Signature » n'apparaît que sur un **mandat ou un avenant**.
- **D29 (Q5)** **aucun mandant ne se décoche** : tous signent ; un cas spécial passe par « Signé à la main ».
- **D30 (Q6)** la correction d'un e-mail APRÈS l'envoi est **éprouvée en sandbox d'abord**, avant de prévoir le bouton.
  ✅ **ÉPROUVÉ LE 05/11** (`Console/essai_youtrust_correction_signataire.js`, sandbox, boîte de Frédéric seulement, code
  par e-mail) : deux demandes, chacune ANNULÉE à la fin. **(a)** signataire encore « initiated » (invitation pas partie) :
  prénom puis e-mail changés → **acceptés**. **(b)** signataire « notified » (invitation partie, `--attendre-notifie`) :
  prénom seul → **accepté** ; e-mail vers un alias de la même boîte (`+essai-a2`) → **accepté**, le statut reste
  « notified », l'adresse relue est la nouvelle. ⭐ **Le lien de signature CHANGE à chaque correction** (empreintes
  `bd0d87f12a` → `7fde090548` → `171eef04d8`) : notre « Signer maintenant » devra relire le lien après une correction.
  ⚠ **NON MESURÉ** : si Youtrust renvoie une invitation à la nouvelle adresse (à lire dans la boîte de Frédéric : demande
  `d4fd50e8…`, le 05/11 vers 10:20), et si l'ANCIEN lien est mort. ⇒ le bouton « corriger l'e-mail » est POSSIBLE ; sa
  forme dépend de la réponse sur le renvoi (sinon : corriger PUIS relancer avec `send_reminder`).
  ✅ **LA RÉPONSE (05/11, e-mails collés par Frédéric, demande `d4fd50e8…`)** : (1) 09:24:14 UTC l'invitation de départ,
  « Bonjour Frederic (avant) », vers l'adresse d'origine ; (2) **09:24:19 UTC « Vos coordonnées ont été mises à jour »**,
  « Bonjour Frederic (corrige) », « Vous pouvez maintenant terminer le processus de signature », **avec un lien neuf**
  (même `magic_link_id`, autre jeton). ⇒ **Youtrust PRÉVIENT TOUT SEUL le signataire après une correction** : le bouton
  « corriger » n'a PAS à relancer. ⚠ Ce 2e e-mail est parti vers l'adresse d'ORIGINE : il répond à la correction du
  PRÉNOM. Pour l'e-mail changé vers l'alias, rien n'est arrivé — **limite de la sandbox, prouvée** : 3e essai
  (`c40bdbe3…`, 10:29) → la relance vers l'alias est REFUSÉE, HTTP 400 « In sandbox mode, the recipient email must
  belong to your organization ». ⇒ **Ce qui reste NON PROUVÉ et ne peut pas l'être en sandbox** : qu'en production le
  message parte vers la NOUVELLE adresse (à faire confirmer par Youtrust / le commercial, avec D5) ; et si l'ancien lien
  est mort. Forme du bouton retenue en attendant : corriger (PATCH) → relire le signataire → afficher « nouvel e-mail
  envoyé par Youtrust » ; « Relancer » reste un geste à part.

**⛔ D31 à D33 — LA FENÊTRE D'ENVOI NE TOUCHE PAS AU PDF** *(Frédéric, 05/11 ; détail : proposition §10)* :
- **D31** « Rien ne doit modifier le PDF qui va être envoyé » : ni bien, ni prix, ni clauses, ni la présence d'un mandant ;
  un signataire absent du mandat n'est pas ajouté. ⇒ les signataires viennent du DOCUMENT : à la génération, le worker range
  la photo des mandants imprimés avec le PDF ; l'envoi la relit (plus `payload_json.mandants`). *(L'idée de la photo : ses
  réponses 1 et 2 la supposent ; je la lui ai redite pour qu'il la corrige si je me trompe.)*
- **D32** « La notion du couple et de son conjoint doit être faite dans l'ÉDITEUR du document, pour savoir s'il apparaît ou
  pas dans le document. » ⇒ D25 (lier le conjoint) quitte la fenêtre d'envoi et va dans l'éditeur, avant la génération.
- **D33** = **A** : un e-mail ou un portable manquant se complète dans la fenêtre d'envoi et s'enregistre sur la fiche ; le
  PDF ne change pas. ⇒ D23 et D30 restent, comme canaux de remise.
- **Remplacés** : D25 (sa place), D26 et D27 (sortent de la fenêtre d'envoi), D29 (devient automatique).

**D34 à D36 — LE COUPLE DANS L'ÉDITEUR** *(Frédéric, 05/11 : « ok » après la réexplication des questions (a), (b), (c) de la
proposition §11.2, recommandation « oui » aux trois ; détail : proposition §11.2)* :
- **D34** (a) : un conjoint nommé ET lié au bien est dans le mandat par défaut (comme aujourd'hui) ; « Non » le retire du
  DOCUMENT seulement (sa fiche et son lien au bien restent).
- **D35** (b) : un conjoint nommé mais NON lié au bien est absent par défaut (comme aujourd'hui) ; « Oui » le lie au bien
  comme mandant (clic confirmé, porte `app_link_mandant_optimistic`, comme « Lier comme mandant »), puis il apparaît.
- **D36** (c) : Youtrust allumé, un mandant imprimé sans prénom ou sans nom BLOQUE la génération (il se corrige sur la
  fiche) ; un e-mail ou un portable manquant n'est qu'un avertissement (il se complète à l'envoi, D33).
- Place de conjoint vide : « Le conjoint n'est pas connu » + gestes F / G existants ; sinon le mandant signe seul.

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

**⭐ LOT 6b REDÉCOUPÉ LE 05/11** — après D31-D33 et les deux maquettes validées (« OUI VALIDE » pour les cartes,
« Oui, validé » pour le parcours « corriger puis régénérer » ; proposition §10-§12.1). Tout reste derrière
`signature_youtrust` ; chaque pièce a son « vas-y », son essai, son retour arrière. ⚠ Le texte du lot 6b ci-dessus
(« signataires modifiables ») est REMPLACÉ par ce découpage : seuls l'e-mail et le portable se corrigent à l'envoi.
- **P1 — worker : la photo du PDF.** À la génération (chemin « chez nous », mandat ET avenant), ranger
  `metadata_json.signataires_du_pdf` (rang, civilité, prénom, nom, e-mail et téléphone imprimés, numéro de la fiche,
  repères attendus) depuis `render_payload.mandants`. ⚠ L'identifiant imprimé est celui de la carte de l'écran
  (`detail-contact-<rang>-<n°>`) : le vrai numéro de fiche doit être porté par l'écran.
  ✅ **P1 CODÉ LE 05/11, NON ACTIF** (interrupteur éteint, services non redémarrés, rien commité au moment d'écrire) :
  `ficheDuMandantImprime` + `photoSignatairesDuPdf` (worker, avant `enregistrerMandatChezNous`), photo rangée dans
  `metadata_json.signataires_du_pdf` à la création de la ligne, et dite au journal du travail. La photo est CONFRONTÉE au
  HTML rendu : signatures s1..sN+1 et mentions s1..sN, sinon `valide: false` + `problemes` (P2 refusera l'envoi).
  Essai `Console/test_photo_signataires_pdf.js` **23/23**, sur le HTML RÉEL du gabarit (mandat 2/3/4 mandants, avenant 2)
  écrit par `test_reperes_signature.mjs` : refus d'un rendu à 3 mandants pour un PDF à 2 (et l'inverse), d'un PDF sans
  repères, d'un rendu vide ; numéro de fiche (carte, membre de couple, ligne à la main = aucun, numéro de l'écran
  prioritaire) ; copie figée ; rejeu = une ligne ; ⭐ témoin inverse : le worker d'avant ne range aucune photo.
  `test_mandat_chez_nous_et_mandataire.js` mis à jour (tranches de la photo) et vert ; voisins verts (R1, couples,
  documents retirés). Aucun autre lecteur de `handleGenerateMandatDocument`.
- **P2 — worker : l'envoi lit la photo.** `handleYoutrustSendSignature` ne prend plus `payload_json.mandants` ; il lit la
  photo, refuse si elle manque, n'accepte de l'écran que des corrections d'e-mail / portable PAR RANG. Contrôles O3
  gardés. P1 + P2 = un seul redémarrage des services (documents + synchro), file vide.
  ✅ **P2 CODÉ LE 05/11, NON ACTIF** : `signatairesDepuisLaPhoto` (worker, bloc du lot 4) ; `handleYoutrustSendSignature`
  prend les mandants de la photo, ignore `payload_json.mandants` (et l'écrit au journal), accepte de l'écran
  `payload_json.corrections = [{ rang, email?, telephone? }]` et REFUSE toute autre clé (« le reste est imprimé ») ou un
  rang hors du PDF ; refus sans photo ou photo invalide, AVANT tout appel à Youtrust ; chaque signataire de notre ligne
  garde `hektor_contact_id` et `corrige`. Essais : `Console/test_envoi_lit_la_photo.js` **18/18** hors ligne (faux
  Youtrust, aucun crédit) — ⭐ témoin inverse : le worker d'avant faisait signer LES NOMS DE L'ÉCRAN, à nombre égal ;
  `essai_youtrust_handler_sandbox.js` mis à la règle (la photo remplace la liste ; scène 6 = photo fausse) et rejoué
  **en vraie sandbox le 05/11, 18/18**, sur un PDF RÉEL du gabarit (mandat à 2 mandants, `test_reperes_signature.mjs` →
  Chromium), boîte de Frédéric seulement, code par e-mail. Voisins verts (photo, 4 bis, R1, couples).
- **P3 — base + worker : le 2e téléphone (D27)** dans la porte « modifier un mandant », pour qu'un portable complété à
  l'envoi n'écrase pas un fixe.
  🔎 **AUDIT DE P3 (05/11), rien codé** : la porte du MANDANT (`updateHektorMandantContact`) écrit le téléphone dans la
  PREMIÈRE ligne `telephone[]`, quelle que soit son étiquette (`replaceFirstArrayParam`) → si cette ligne est le fixe, le
  portable saisi l'écrase (et garde l'étiquette « fixe »). C'est le vrai risque. ⭐ **Le remède existe déjà ailleurs** :
  le chantier partenaires a posé le 05/11 la règle D-5 dans la porte du CONTACT (`remplacerCoordonnee` : on remplace la
  ligne de MÊME étiquette, portable ou fixe, avec son numéro interne ; sinon on en ajoute une), derrière l'interrupteur
  `contact_coordonnees_remplacer` = **on** depuis le 05/11 10:05 UTC. ⇒ P3 devient : **la porte du mandant suit D-5**
  (même fonction, même interrupteur) ; éteint = le chemin d'avant. **Pas de patch Supabase** : le 2e téléphone n'est pas
  nécessaire pour D33 (le portable va sur la ligne « portable », le fixe reste). Mesure : 10 modifications de mandant en
  tout, la dernière le 08/10, 2 avec un téléphone. ✅ « vas-y » de Frédéric (05/11).
  ✅ **P3 CODÉ LE 05/11** (rien commité au moment d'écrire, services non redémarrés) : `updateHektorMandantContact`
  lit `interrupteurCoordonneesRemplacer()` ; allumé → `remplacerCoordonnee` pour l'e-mail (repli sur la dernière ligne)
  et le portable (une valeur vide ne part pas) ; éteint → le chemin d'avant, à l'octet ; le journal dit
  `coordonnees: remplacees_par_etiquette | premiere_ligne`. ⚠⚠ **PAS DORMANT** : l'interrupteur D-5 est déjà « on » →
  actif au prochain redémarrage des services, pour le geste « modifier un mandant » de tous. ⭐ Le témoin inverse a prouvé
  un DÉFAUT DORMANT de l'ancien chemin : `replaceFirstArrayParam` vide TOUTES les valeurs `telephone[]` et n'en remet
  qu'une, sans toucher aux étiquettes → un mandant portable + fixe perdait la valeur du fixe. Essai
  `Console/test_mandant_coordonnees.js` **15/15** (portable + fixe, fixe en 1re ligne, aucun téléphone, téléphone vide,
  éteint = à l'octet sur 4 envois, interrupteur illisible = éteint). Voisins verts (D-5, couples, partenaires, photo,
  envoi, 4 bis, R1). ⚠ `Console/test_localite_mandant.js` était CASSÉ depuis le 02/11 (« hektorContactFormGroup is not
  defined ») : réparé en lui ajoutant les tranches manquantes, 8/8. Session partenaires prévenue.
  ⚠⚠ **P3 ACTIF EN PRODUCTION DEPUIS LE 05/11 À 12:37:05, AVANT SON COMMIT** : Frédéric a redémarré les 4 services pour
  le correctif des partenaires (fichier écrit à 12:36:38, avec mes lignes) — vérifié par l'heure des processus
  (12:37:05-07) ; 0 erreur aux 4 journaux depuis ; 0 modification de mandant et 0 travail Youtrust depuis 12:30 UTC.
  P1 et P2 sont chargés aussi, mais dorment (`signature_youtrust` = off).
- **P4 — écran : la fenêtre d'envoi-confirmation** (maquette « corriger » vue 1-2) : PDF, signataires lus dans la photo,
  🔒 / ✎, envoi bloqué tant qu'un e-mail manque ; elle remplace `SignaturePromptModal` quand l'interrupteur est allumé.
  ✅ **P4 CODÉ LE 05/11** (rien commité ni déployé au moment d'écrire) : `EnvoiSignatureYoutrust.tsx` +
  `envoi-signature.css` (préfixe `ens-`) ; `lib/api.ts` : `photoSignatairesDuDocument`, `loadFichesDesSignataires`
  (par `hektor_target_id`), `enregistrerCanalDuMandant` (porte du mandant avec SEULEMENT nom d'aujourd'hui + e-mail +
  portable — ⚠ `createUpdateHektorMandantContactJob` envoie des clés vides qui EFFACERAIENT adresse / ville chez Hektor),
  `createYoutrustSendSignatureJob` (numéro du document + `corrections` par rang). `App.tsx` : `useSignatureYoutrust()` ;
  panneau Documents (les 2 rendus) : allumé → « Signature » seulement sur un PDF qui porte sa photo et hors demande
  Youtrust en cours, et il ouvre la nouvelle fenêtre ; éditeur : après la génération, la fenêtre s'ouvre sur le document
  neuf (« Mandat enregistré chez nous »). Éteint : le chemin d'avant, à l'identique. Un CONJOINT : la correction part dans
  la demande, pas sur sa fiche (message « Modifier le conjoint »). `npm run build` vert ; vu dans le navigateur sur une
  page d'essai temporaire (document fictif, retirée ensuite) à 1280 × 665 et en 375 px : signataires, cadenas + bulle,
  e-mail refusé puis accepté, envoi débloqué avec « 4 crédits », PDF sans photo / photo invalide refusés.
  ⚠ NON ÉPROUVÉ : l'envoi réel par l'écran (interrupteur éteint en production) et l'écriture sur la fiche.
- **P5 — écran : « Corriger le mandat »** (vues 3, 4, 6) : l'éditeur rouvert sur le bon onglet avec son bandeau,
  « Régénérer et revenir à l'envoi », « ce qui a changé » ; l'ancien PDF marqué « remplacé, jamais envoyé », sans bouton
  Signature.
  🔎 **AUDIT DE P5 (05/11)** : le front n'a AUCUN droit d'écriture sur `app_console_document` (la voie manuscrite passe
  par une RPC dédiée) → la marque « remplacé » se pose dans le **worker**, au moment de la régénération (aucun patch
  Supabase). L'ancien PDF ne portait pas ce qu'il imprime (la photo ne garde que les signataires) → le nouveau garde
  `contenu_imprime`. Le panneau Documents et l'éditeur sont deux composants séparés : le panneau DEMANDE à l'éditeur du
  même bien de s'ouvrir (événement `hektor:corriger-mandat`, le premier éditeur monté le prend, un seul s'ouvre).
  ✅ **P5 CODÉ LE 05/11** (rien commité, rien déployé, services non redémarrés) :
  · **worker** (dormant : seulement le chemin « Youtrust allumé ») : `enregistrerMandatChezNous` range
    `contenu_imprime` (prix, net vendeur, honoraires, charge, bien, clauses, numéro, date…) et, si la charge porte
    `remplace_document_id`, appelle `marquerDocumentRemplace` **APRÈS** l'enregistrement du nouveau PDF : il ne marque
    qu'un PDF de l'éditeur, du même bien, ni signé ni en signature (le PATCH porte la même condition, syntaxe vérifiée
    contre le vrai PostgREST par une lecture : 401 droits, contre 400 pour un filtre cassé exprès) ; un refus ou une
    erreur ne défait JAMAIS la génération (avertissement `mandat_remplace` au journal). `signatairesDepuisLaPhoto`
    **refuse** un PDF marqué remplacé (il ne part pas, même si une demande arrivait).
  · **écran** : fenêtre d'envoi : « ✎ Corriger le mandat » (en-tête du PDF) et dans la bulle du cadenas (« Corriger le
    mandat / Laisser tel quel ») ; au retour, bandeau « Nouveau mandat généré à … ; l'ancien gardé, marqué remplacé »
    (ou, s'il n'a pas pu l'être : alerte « ne l'envoyez pas ») et **« ce qui a changé »** (noms, mandant ajouté ou
    retiré, nombre de signataires donc de crédits, et tout ce qui est imprimé ; un ancien PDF sans `contenu_imprime` →
    « seuls les signataires sont comparés ») ; un PDF remplacé ouvert → envoi bloqué. Éditeur : bandeau « Correction
    avant l'envoi » avec « Revenir à l'envoi sans rien changer » et « ↻ Régénérer et revenir à l'envoi » ; il attend la
    marque jusqu'à 45 s avant de revenir. Documents (les 2 rendus) : mention « Remplacé le … — jamais envoyé », pastille
    « Remplacé », plus de bouton Signature. Ouvert depuis le panneau sans éditeur monté → « ouvrez-le depuis la rubrique
    Mandat ».
  · **ce que ça aurait cassé ailleurs, fermé** : le cockpit du mandat prend le PREMIER document « mandat » / « avenant »
    venu (même nom pour l'ancien et le nouveau) → il pouvait lire le PDF remplacé, et afficher l'ANCIEN prix proposé
    d'un avenant corrigé ; il saute désormais un PDF remplacé (`ckSigStatus`, `avenantDoc`). « Signé à la main » n'est
    plus offert sur un PDF remplacé. Rien ne change pour un document non marqué (tous ceux d'aujourd'hui).
  · **essais** : `Console/test_regeneration_remplace.js` **23/23** (marque, ordre « après », 8 refus dont signé / en
    signature / autre bien / demande partie entre lecture et marque / 503, annulée = marquable, rejoué, génération
    ordinaire inchangée, refus d'envoi, témoin inverse = le worker d'avant ne marque rien). Voisins verts après ajout des
    deux fonctions à leurs montages : photo 23/23, chez nous 22/22, envoi 18/18, 4 bis 26/26, coordonnées 15/15,
    localité 8/8. `npm run build` vert. Vu dans le navigateur sur une page d'essai temporaire (données fictives, retirée
    ensuite) à 1280 × 665 et en 375 px : « ce qui a changé », ancien non marqué, PDF remplacé, bulle, bandeau éditeur,
    ligne « Remplacé ».
  ⚠ NON ÉPROUVÉ en réel : la boucle entière dans l'app (interrupteur éteint en production) — l'ouverture de l'éditeur
  par le panneau, l'attente de la marque, la marque posée par le vrai worker (il faut redémarrer les services).
- **P6 — écran : « la fiche a changé depuis ce PDF »** (vue 5), comparaison photo ↔ fiche à l'ouverture.
  🔎 **AUDIT DE P6 (05/11)** : « la fiche d'aujourd'hui » = le brouillon d'ouverture de l'éditeur
  (`buildMandatDocumentDraft(dossier, detail, contacts, address)`), le même chemin que celui qui a imprimé le PDF.
  Les trois écrans qui montrent le panneau Documents (cockpit, fiche bureau, téléphone) ont `detail`, `contacts` et
  `address`. On ne compare QUE ce que la fiche porte : mandants (ordre et noms), n° et type de mandat, bien,
  adresse, pièces, surfaces, prix FAI, net vendeur, honoraires. La date, la charge, l'occupation, les clauses et les
  options se saisissent dans l'éditeur : pas comparées (sinon le bandeau sonnerait à chaque fois).
  ✅ **P6 CODÉ LE 05/11** (rien commité, rien déployé) :
  · `src/lib/ecartsFichePdf.ts` (nouveau, pur) : `ecartsAvecLaFiche` (PDF → fiche ; espaces, casse et écriture des
    montants ne font pas un écart ; une fiche muette ne contredit pas le PDF) ; « ce qui a changé » de P5 y est
    déplacé, à l'identique.
  · fenêtre d'envoi : cadre ambre « ⚠ La fiche a changé depuis ce PDF » (PDF : … → fiche : …) ; le pied devient
    « Envoyer quand même… » + « ↻ Régénérer avant d'envoyer » (= « Corriger le mandat ») ; « Envoyer quand même »
    demande une confirmation écrite (« Envoyer le PDF du 04/11 17:05 tel qu'il est — sans Mme X, Prix FAI 205 000 € ? ») ;
    le choix part dans la demande (`payload_json.ecarts_acceptes`) et le worker l'écrit au journal du travail (une
    ligne, dormante derrière l'interrupteur). Un PDF d'avant le 05/11 (sans `contenu_imprime`) : seuls les mandants,
    et il le dit.
  · panneau Documents : reçoit la fiche aux 3 endroits ; éditeur : ne compare PAS un PDF qu'il vient de générer
    (c'est la saisie du moment), compare celui qu'on retrouve par « Revenir à l'envoi sans rien changer ».
  · essais : `apps/hektor-v1/test_ecarts_fiche_pdf.cjs` **18/18** (fidèle = 0 écart, écritures différentes = 0
    avec témoin, mandant ajouté / retiré / renommé, prix, fiche muette, champs saisis ignorés, PDF d'avant le 05/11,
    sans fiche, P5 déplacé inchangé, mêmes clés que le worker et que l'écran, les 3 panneaux, la trace) ; voisins
    worker verts (23, 18, 23, 26, 22) ; build vert ; vu sur une page d'essai temporaire (retirée) à 1280 × 665 et
    375 px, confirmation comprise.
  ⚠ NON ÉPROUVÉ en réel (interrupteur éteint). ⚠ Risque connu : juste après une correction de prix ou de nom sur la
  fiche, si la fiche affichée n'est pas encore relue, le bandeau peut parler de l'ancienne valeur — il ne bloque
  rien, il propose de régénérer.
- **P7 — éditeur : le couple (D32)** et le contrôle du prénom / nom — ✅ réponses reçues le 05/11 : « oui » aux trois
  (D34, D35, D36). ✅ « vas-y » le 05/11.
  🔎 **AUDIT DE P7 (05/11)** : les cartes de l'éditeur portent le numéro HEKTOR (registre : `hektor_target_id` ; détail
  Hektor : `item.id`) ; ⚠⚠ **`couple_json.conjoint.id` est NOTRE numéro** (0 sur 40 trouvés comme numéro Hektor, 25 sur
  40 comme le nôtre) ; le numéro Hektor du conjoint est **`couple_json.conjoint.hektor_id`** (300 sur 300, égal à sa
  fiche 253 fois sur 253) — c'est lui que vise la porte « lier comme mandant ». ⛔ Règle du 02/11 tenue : couple ⇔
  `nature_fiche = 'couple'` (16 052 personnes seules ont un `couple_json` « vide »). **Mesure refaite avec les règles
  du code** (biens vivants, lecture seule) : 688 biens avec mandant, 54 couples mandants, 42 conjoints nommés → **10
  liés (a)**, **32 non liés (b)**, 0 archivé ; **6 places vides** ; 1 353 personnes, **43 sans prénom** (bloquées par
  D36 si Youtrust est allumé), 0 sans nom — exactement le §8.2.
  ✅ **P7 CODÉ LE 05/11** (rien commité, rien déployé ; tout derrière `signature_youtrust`, éteint = l'éditeur d'avant) :
  · `src/lib/conjointsDuMandat.ts` (nouveau, pur) : `situationsDesConjoints` (lie / non_lie / inconnu), `mandantsImprimes`
    (retraits D34, ajouts D35 juste après le principal, jamais deux fois), `mandantsSansPrenomOuNom` (D36).
  · `lib/api.ts` : `loadCouplesDesMandants` (nature, couple_json, civilité ; lecture seule).
  · éditeur : onglet « Mandants » — une ligne par couple « X, conjoint(e) de Y, figure-t-il (elle) dans ce mandat ? »
    Oui / Non ; (b) « Oui » ouvre une confirmation (« ⚠ sur un mandat numéroté, il ne pourra pas être retiré depuis
    l'app ») puis `createLinkHektorMandantJobOptimistic` (porte existante) et l'imprime ; un conjoint archivé ne se lie
    pas ; place vide → « le conjoint n'est pas connu, complétez-le depuis la fiche du contact ». La liste affichée,
    l'aperçu, la génération et la photo du PDF suivent le mandat TEL QU'IL SERA IMPRIMÉ (`draftDuDocument`). D36 :
    avertissement dans l'onglet et l'onglet en « ! », et la génération est REFUSÉE au clic (interrupteur relu) avec le
    rang et ce qui manque.
  · le PDF retient les conjoints retirés exprès (`contenu_imprime.conjoints_retires`, worker, dormant) → le bandeau de P6
    ne les prend pas pour un écart.
  · essais : `apps/hektor-v1/test_conjoints_du_mandat.cjs` **26/26** (numéros, a, b, archive, relecture sans doublon,
    place vide, règle de nature, couple_json en texte, D36, worker, branchements ; témoin : sans la note, P6 crierait) ;
    P6 18/18 ; worker 23, 18, 23, 22 ; build vert ; cartes vues (balisage recopié sur une page d'essai, retirée) à
    1280 × 665 et 375 px.
  ⚠ NON FAIT, à décider : « Compléter » / « Ajouter » le conjoint DEPUIS l'éditeur (gestes F / G) — aujourd'hui un texte
  renvoie à la fiche du contact. ⚠ NON ÉPROUVÉ en réel : la lecture des couples, le lien posé depuis l'éditeur, le blocage
  (interrupteur éteint en production).
- **P8 — le suivi par personne** (« Relancer », « Corriger l'adresse », vue 7 « déjà envoyé ») : après le lot 5 (avis
  Youtrust), dont il a besoin.
Ordre proposé : P1 → P2 → P3 → P4 → P5 → P6 → P7, puis lot 5, puis P8.

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
