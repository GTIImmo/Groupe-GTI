# A.2 — Lot 6a : l'éditeur, la fenêtre d'envoi, les fiches des mandants

> **Proposition, rien n'est codé.** Écrite le 26/10/2026 après un audit en lecture seule :
> l'éditeur et toutes les fenêtres de signature (App.tsx), l'historique git, les gestes qui
> modifient un contact ou un mandant (front, RPC, worker), une mesure en base, la doc Youtrust.
> Plan parent : `notice/PLAN_DEV_SIGNATURE_YOUTRUST_2026-10-26.md` (lots 6a / 6b).
> ⚠ Les lignes d'App.tsx sont celles de l'arbre de travail du 26/10 au soir (fichier modifié
> par l'autre session, pas encore commité) : elles bougeront.

**Audit limité** à : mandat / avenant (document), contact / mandant (modifier, créer, lier),
signature (envoyer, suivre, relancer, annuler, signé à la main). Les autres objets ne sont
pas mesurés.

---

## 1. Ce qui existe aujourd'hui, en clair

### 1.1 L'éditeur (`MandatDocumentEditor`, App.tsx:5290)

- **6 onglets** : Mandants · Bien · Prix · Clauses · Signature · Contrôle. En avenant, une seule page.
- **Mandants : tout est VERROUILLÉ** (`LockedDataField`), décision du 28/07 (`3a3d714`) : le brouillon ne
  poussait que le PDF, le document pouvait diverger de la fiche. Texte : *« Pour ajouter, retirer ou
  corriger un mandant, passez par la fiche du contact. »* — **sans lien ni bouton** vers elle.
- **Bien / Prix : un crayon** (`CorrigeableAnnonceField`, `1d82e1f`, `0d7ee63`) qui écrit **dans la fiche**
  (`editAnnonceOptimistic`, chez nous d'abord). ⭐ C'est le bon modèle. Le « lot 3 » prévu — le même
  crayon sur les coordonnées des mandants — **n'a jamais été fait** (mémoire `crayon-corriger-modale-mandat`).
- **Signature** (`42008ae`, 18/05) : une liste **libre** de destinataires (nom affiché, rôle, canal,
  e-mail, téléphone, ajouter, retirer, « Reprendre mandants »).

### 1.2 Ce que la liste « Signature » devient — ⚠ RIEN

Mesuré : le worker ne lit **jamais** `render_payload` ni `destinataires` (0 occurrence). La liste sert
seulement :
- à afficher les noms dans la fenêtre « Oui, ouvrir Hektor » ;
- aux compteurs.

Le négociateur **ressaisit tout dans la popin ImmoSign de Hektor**. Les cases du PDF viennent des
**mandants**, pas des destinataires. Une correction faite ici **ne remonte jamais** sur la fiche.

### 1.3 Les fenêtres de signature (toutes ImmoSign)

| fenêtre | où | ce qu'elle fait |
|---|---|---|
| « Faire signer ce document par Yousign ? » (`SignaturePromptModal`, :5177) | après « Générer », et bouton **Signature** des Documents | « Oui, ouvrir Hektor » → onglet Documents de Hektor |
| bouton **Signature** (:11615) | sur **tout** document non signé, DPE et factures compris | même fenêtre |
| **Relancer / Annuler** (:11576) | document `pending` avec `procedure_id` | `relance_signature` / `cancel_signature_procedure` |
| **Signé à la main** (:11482) | Mandat V3, nom contenant mandat/avenant | RPC `app_console_mark_document_signed_manual` |
| `MandatSignatureTracker` (:11104) | rubrique Mandat V3 (envoyé, valider), classique | mêmes boutons ; **Signature ouvre Hektor sans la fenêtre** |
| crans de la rubrique Mandat V3 (:30454) | `editer` → `envoye` → `valider` → `attente` (+ avenant) | textes « Envoyé sur ImmoSign », « Signé sur ImmoSign » |

### 1.4 Corriger un mandant aujourd'hui — le geste existe déjà

| geste | écran | chemin | chez nous d'abord ? |
|---|---|---|---|
| **modifier un mandant** | `HektorMandantContactEditForm` (:3681) | `app_update_mandant_contact_optimistic` → travail `update_hektor_mandant_contact` + `app_edit_contact_optimistic` | ✅ oui (patch 5b du 08/10) ; **contrôle au retour actif** (`contact_retour_controle`) |
| créer + lier un mandant | `HektorMandantContactForm` (:3226) | `app_create_mandant_contact_optimistic` (numéro ≥ 20 M) | ✅ oui |
| lier un existant | idem, 2e onglet | `app_link_mandant_optimistic` | ✅ oui |
| retirer | `RetirerMandantBouton` (:3578) | `app_unlink_mandant_optimistic` | ✅ — **refusé si le mandat est numéroté** |
| modifier un contact | fiche contact | `app_edit_contact_optimistic` (12 champs, dont `phone_secondary`) | ✅ oui |

⭐ **Conclusion : « mettre à jour la fiche du mandant depuis la fenêtre d'envoi » ne demande AUCUN
circuit neuf.** C'est le geste « modifier un mandant », déjà chez nous d'abord, déjà contrôlé au retour.
Il suffit de l'appeler depuis l'éditeur, comme le crayon du prix appelle `editAnnonceOptimistic`.

---

## 2. La mesure qui change tout (base, 26/10 au soir)

Mandants des biens **actifs** (`app_contact_relations_current`, rôle `mandant`, `is_active_annonce`) :

| | liens | part |
|---|---|---|
| liens de mandant | **1 705** sur **712** biens | |
| avec un prénom | 1 360 | 80 % → **345 sans prénom** |
| avec un e-mail valide | 1 242 | 73 % → **463 sans e-mail** |
| avec un portable (06/07) | 1 232 | 72 % → 473 sans portable |
| **fiches muettes « Mr./Mme »** (ni nom ni prénom) | **303** | 18 % |
| `menage_resolu` / `menage_orphelin` | 218 / 54 | |

**Ce que ça veut dire :**
- ⚠ **environ un lien de mandant sur quatre n'est pas signable tel quel** chez Youtrust, qui exige
  prénom, nom et e-mail. La fenêtre d'envoi doit donc **faire compléter**, pas seulement contrôler.
- ⚠⚠ **303 conjoints sont liés au bien comme mandants, mais par une fiche vide.** Leur prénom et leur
  e-mail ne sont **nulle part chez nous** : le bloc conjoint de Hektor (`nom_m2`, `prenom_m2`…) vit
  dans son formulaire web, pas dans l'API (sonde du 11/09), et nous n'avons aucune colonne pour lui.
- ⚠ **Défaut trouvé** : l'éditeur fusionne la fiche muette avec sa porteuse et en fait **un mandant à
  part entière** : nom « Mr./Mme », sans prénom, e-mail du conjoint. Elle reçoit **une case de
  signature dans le PDF**. Avec Youtrust allumé, le worker refuserait l'envoi (*« fiche de couple à
  éclater »*) — **après** avoir fabriqué le PDF.

---

## 3. Ce que Youtrust permet (doc relue le 26/10)

- **Modifier un signataire** (`PATCH /signers/{id}`) : prénom, nom, e-mail, portable. Seule
  restriction écrite : le mode d'authentification, après activation, n'est modifiable que si le
  signataire n'a pas encore ouvert. ⚠ **Modifier l'e-mail APRÈS l'envoi n'est pas documenté
  clairement → à éprouver en sandbox avant d'en faire un bouton.**
- **Ajouter un signataire** : seulement en brouillon (`draft`). Après l'envoi, on ne peut plus en ajouter :
  **la liste doit être juste AVANT.**
- **La préparation intégrée** (`embedded_preparation_link`, 10 min) sert **seulement à placer des
  champs**. Elle ne touche pas aux signataires, et nos ancres sont déjà posées : **inutile pour nous**.
- **`signer.notification_delivery_failed`** : Youtrust prévient si **le premier e-mail** ne passe pas
  (adresse fausse, rebond, anti-spam). ⭐ C'est le moment où l'on peut dire « corrigez l'adresse ».
- La **fiche contact** de Youtrust (API Contacts) n'est pas utilisée (D20) : **la vérité reste chez nous.**

---

## 4. La proposition

### Principe : une seule vérité, la fiche du contact

> **La fenêtre d'envoi ne garde AUCUNE copie libre des signataires.** Elle les LIT sur les fiches,
> elle les fait CORRIGER sur les fiches, par le geste existant. Ce qui part chez Youtrust, ce qui est
> imprimé dans le PDF et ce qui est sur la fiche sont la même chose, par construction.

C'est la décision du 28/07 (« le document ne doit pas diverger de la fiche »), poussée jusqu'au bout :
on ne **verrouille** plus, on **corrige à la source**, comme le crayon du prix.

### 4.1 L'éditeur : 6 onglets → 5

| aujourd'hui | proposé |
|---|---|
| Mandants (verrouillé) + Signature (liste libre) | **« Mandants et signataires »**, UN onglet : une carte par personne |
| Bien · Prix · Clauses | inchangés (le crayon reste) |
| Contrôle | **« Contrôle et envoi »** : le récapitulatif, puis LE bouton |

**Chaque carte de mandant** porte :
- l'identité imprimée dans le mandat : civilité, prénom, nom, adresse ;
- les coordonnées de signature : e-mail, portable ;
- **un crayon sur chaque champ**, qui écrit dans la fiche (« Mis à jour dans la fiche · synchro Hektor
  en cours », mêmes mots que le crayon du prix) ;
- **un état lisible** :
  - ✅ « Prêt à signer — code par SMS au 06 •• •• 12 34 » ;
  - ✅ « Prêt — code par e-mail (pas de portable) » ;
  - ⚠ « Il manque : prénom, e-mail ».

**Le négociateur** est la dernière carte, **non modifiable ici** (D21 : le négo du bien s'il est actif,
sinon celui qui envoie). L'ordre est écrit en clair : **« 1. Les mandants, en même temps → 2. Vous. »**

**Ce qui disparaît en mode Youtrust** (et reste tel quel tant que l'interrupteur est éteint) :
- « Nom affiché », « Rôle », « Canal » : Youtrust envoie toujours par e-mail, et le code passe par
  SMS si un portable existe ;
- « Ajouter un destinataire » : on ajoute **un mandant**, avec le formulaire existant ouvert sur place ;
- la case « ne signe pas » et « Retirer » : **tout mandant du mandat signe**. Le cas spécial (procuration,
  indivision…) passe par « Signé à la main », qui reste.

### 4.2 Le conjoint (D22) — ⛔ décision à prendre

La fiche muette ne devient **plus** un mandant du document. À sa place, l'éditeur affiche une
**carte « Conjoint à compléter »** : civilité, prénom, nom, e-mail, portable. Une fois remplie,
elle s'enregistre. Trois façons de le faire :

| | où vit le conjoint | pour | contre |
|---|---|---|---|
| **A** ⭐ | **une vraie fiche contact**, créée et liée au bien comme mandant par le geste existant « Créer et associer » (numéro ≥ 20 M, chez nous d'abord) | geste existant et prouvé ; e-mail obligatoire, déjà exigé ; le conjoint devient un vrai contact, retrouvable, qui survivra à la coupure | chez Hektor, le ménage aura une 3e fiche (porteuse, muette, nouvelle) ; la muette reste liée (retrait refusé si le mandat est numéroté) |
| B | **la fiche muette elle-même**, nommée | une fiche de moins | ⛔ contredit la règle « ne jamais écrire dans nom/prénom du muet » ; ce que fait Hektor est inconnu (la sonde C.9-couple n'a jamais été passée sur un vrai ménage) |
| C | le bloc conjoint de Hektor (`nom_m2`…) | le modèle de Hektor | aucune colonne chez nous, modification non supportée par l'écran ; c'est le point « D » **que tu as reporté** ; ça disparaît à la coupure |

**Recommandé : A.** C'est la seule qui pose la donnée chez nous, par un geste qui existe déjà.

### 4.3 « Contrôle et envoi » : un seul bouton, et la complétude AVANT le PDF

- Le bouton **« Générer et envoyer en signature »** reste **grisé** tant qu'une carte est ⚠. Il dit
  pourquoi : « Il manque l'e-mail de Mme Martin ». Aujourd'hui, « Générer » n'est **jamais** bloqué.
- Pourquoi avant : le PDF imprime les noms et porte **une ancre par signataire**. Après l'envoi, on ne
  peut plus ajouter de signataire. Une liste fausse = un crédit perdu et un mandat à refaire.
- Un clic fait tout, et la progression s'affiche **dans la même fenêtre** :
  1. mandat enregistré chez nous (lot 4 bis) ;
  2. demande créée chez Youtrust ;
  3. envoyé à M. et Mme X ;
  4. à vous de signer, avec un bouton « Signer maintenant » (D8).
- **Fini** la question « Oui, ouvrir Hektor », et l'attente de 150 s du dépôt chez Hektor.

### 4.4 Après l'envoi : le suivi par signataire (lot 6b)

`MandatSignatureTracker` devient une **ligne par personne** (Youtrust le donne, ImmoSign ne le donnait
pas) : *« M. Dupont — signé le 27/10 à 14:02 · Mme Dupont — a ouvert le lien, pas encore signé ·
Vous — en attente des mandants »*.

| bouton | ce qu'il fait |
|---|---|
| **Relancer** | par personne, seulement si elle a été prévenue et n'a pas signé (règle Youtrust) |
| **Annuler** | toute la demande, avec un motif |
| **« E-mail non délivré à Mme X — corriger l'adresse »** | sur l'avis `notification_delivery_failed` ; le crayon corrige la fiche, et le changement du signataire chez Youtrust **seulement si la sandbox le prouve** |

Les boutons restent **aiguillés par fournisseur** (R2) : une procédure ImmoSign en cours garde ses
boutons ImmoSign.

### 4.5 Le bouton « Signature » des Documents

Interrupteur allumé, il **n'apparaît plus que sur un mandat ou un avenant**, et ouvre la même
fenêtre. Aujourd'hui, il est aussi sur les DPE et les factures. ⛔ À confirmer par toi.

---

## 5. Ce que ça pourrait casser ailleurs

| risque | parade |
|---|---|
| le crayon déclenche le bandeau « La fiche a été mise à jour pendant votre saisie » (garde du 09/10, :5350) — l'utilisateur croirait que quelqu'un d'autre a changé la fiche | la fenêtre **reconnaît ses propres corrections** (elle recale sa référence après son propre enregistrement) ; le bandeau reste pour les vrais changements extérieurs |
| couple fusionné : le formulaire actuel écrit les valeurs fusionnées sur la **seule** fiche principale (défaut existant, :3736) | une carte = **une fiche** (`sourceId` gardé par carte) ; on n'édite jamais une valeur fusionnée |
| la porte du mandant n'écrit que `phone` : un portable saisi **écraserait un fixe** en `phone_primary` | **petit patch additif** : la porte accepte `phone_secondary` (la porte contact le sait déjà) ; le portable va là où il ne remplace rien |
| la porte du mandant avale une erreur locale en silence (`exception when others then null`, patch 5b l. 137) : la fenêtre afficherait « mis à jour » sans valeur chez nous | la fenêtre **relit la fiche** après le geste et n'affiche ✅ que si la valeur est là (« une lecture ratée n'est jamais un vert ») |
| les mandants du document n'ont aucun numéro de contact (`buildMandatDocumentMandants`) : le worker ne saurait pas quelle fiche est quel signataire | la charge du travail porte, par signataire, **son numéro de contact** |
| interrupteur éteint | **rien ne change** : les 6 onglets, la liste libre, « Oui, ouvrir Hektor » restent tels quels jusqu'à l'allumage |
| le téléphone (`MobileDossierDetail`, :37921, éditeur compact) | la maquette doit être vue **aussi en étroit** (mémoire `toujours-controler-le-telephone`) |
| droits : un commercial ne modifie un mandant que **sur ses biens** (L2-A) | c'est déjà la porte du mandant qui le vérifie ; la fenêtre affiche son refus en clair |

---

## 6. Défauts trouvés en passant (notés, pas traités)

1. Le picto « Modifier » du mandant s'affiche `âœŽ` (mauvais encodage, :3764).
2. « Reprendre mandants » écrase la liste **sans confirmation** (:5452).
3. « Générer » n'est jamais bloqué par les champs manquants (:5771).
4. En avenant, « charge honoraires » est réclamé sans champ pour le saisir.
5. `docMode` (mandat/avenant) n'est pas recalculé si le dossier change sous la fenêtre.
6. `MandantsEnCreation` (« En création… ») n'est monté que dans l'ancienne fiche, absent du cockpit.
7. Le bouton Signature du suivi ouvre Hektor sans la fenêtre de confirmation (:11201), celui des Documents avec.

---

## 7. Ce que je te demande de trancher

| | question | ma recommandation |
|---|---|---|
| **Q1** | le conjoint : A, B ou C (§4.2) ? | **A** |
| **Q2** | fusionner « Mandants » et « Signature » en un onglet (6 → 5) ? | oui |
| **Q3** | la porte du mandant apprend `phone_secondary` (petit patch additif) ? | oui |
| **Q4** | bouton « Signature » seulement sur mandat / avenant quand Youtrust est allumé ? | oui |
| **Q5** | aucun mandant ne peut être décoché ; le cas spécial passe par « Signé à la main » ? | oui |
| **Q6** | éprouver en sandbox la correction d'un e-mail APRÈS l'envoi, avant de prévoir le bouton ? | oui |

Ensuite : maquette validée → découpage du lot 6b en pièces → « vas-y » pièce par pièce.

---

## 8. Ce que le chantier des couples a changé pour la signature — audit du 05/11/2026

*Demande de Frédéric : « auditer les correctifs apportés depuis dans mon projet qui concernent ton dev, puis on reprend ».
Audit limité à ce qui touche la fenêtre d'envoi et le worker de signature ; les autres objets ne sont pas mesurés ici.
Lecture seule, sauf mon propre essai (`test_garde_r1_signature.js`), adapté.*

### 8.1 Ce qui existe désormais (commits du 27/10 au 05/11)
- **Le défaut « case vide = mandant » est corrigé** (`dafb499`, 3-A, en ligne) : `lib/mandantsDocument.ts`
  (`sansCasesVides`) écarte la case vide d'un couple du document de mandat ET des destinataires de signature, sur un
  critère de TEXTE (nom réduit à une civilité ou « Contact <n> », aucune coordonnée). C'était mon défaut du §2.
- **La « nature » de chaque fiche existe chez Supabase** (`nature_fiche`, `civilite_app`, `couple_json`,
  `couple_deuxieme`, `supprimee_chez_hektor`… dans `app_contact_current` et sa vue), calculée la nuit ET à la relecture
  d'une fiche (`APP_NATURE_A_LA_RELECTURE=1`). `couple_json.conjoint` porte nom, prénom, e-mail, téléphone, numéros.
- **Quatre gestes du conjoint, en production, ouverts à tous** : modifier le conjoint (pièce E, par la fiche PRINCIPALE,
  fonction `app_edit_conjoint_optimistic`, cran `contacts_couples_modif = on`) ; compléter le conjoint (F) ; ajouter un
  conjoint (G, `link_hektor_conjoint`, biens partagés, cran `contacts_couples_ajout = on`) ; et la fiche et l'annuaire du
  couple (C, D).
- **La porte « modifier un mandant » du worker sait éditer un couple** (`748383f`) : elle relit le groupe
  `contactCoupleAll` au lieu d'échouer sur « Formulaire edition contact Hektor introuvable ». ⚠ La fonction de base
  `app_update_mandant_contact_optimistic` est INCHANGÉE : 8 champs, pas `phone_secondary`, rien sur le conjoint.
- **Le ménage des documents ne supprime plus, il MARQUE** (`6b0efc7`, ⑧ 8f) une fiche retirée chez Hektor. La garde R1
  (`signatureProtegee`) est toujours appliquée AVANT : une ligne Youtrust ou « à la main » n'est ni effacée ni marquée.
  Mon essai ne connaissait pas le nouveau réglage (`DOCUMENTS_RETIRES_EFFACES`) et tombait au montage : adapté, et une
  scène « 4 bis » ajoutée pour le chemin du marquage → **tout vert**.
- **Le pilotage lit `metadata_json.signature.status`** (`signed` / `pending`, index posé le 03/11) : mon envoi écrit déjà
  `pending` ; le lot 5 devra écrire `signed` ET `signed_at` (le pilotage s'en sert).
- **Un autre chantier (partenaires, 05/11) a des lignes NON commitées dans le worker** (`hektorContactFormGroup`,
  `updateHektorContactIdentity`) : mon commit du 4 bis devra prendre MES blocs seulement (par patch).

### 8.2 La mesure refaite (05/11, mêmes règles que le §2)
- **1 638 liens de mandant sur 688 biens vivants** (1 705 / 712 le 26/10).
- **289 sont des cases vides**, maintenant RECONNUES par `nature_fiche` (`case_conjoint_vide` 264, `case_vide_orpheline`
  25). Elles ne sont pas des personnes : le document les écarte déjà.
- **Restent 1 349 vraies personnes** : 1 281 personnes seules, 54 premières fiches de couple, 9 conjoints nommés,
  5 conjoints sans prénom. **146 n'ont pas d'e-mail valide (11 %), 43 pas de prénom.** Le « un sur quatre » du 26/10
  venait surtout des cases vides : le vrai manque est d'**un sur neuf**.
- ⚠⚠ **Le conjoint n'est presque jamais lié au bien** : sur 42 couples « conjoint nommé » mandants, le conjoint n'est
  mandant du même bien que **10 fois** ; les **32 autres** ont un conjoint nommé (36 sur 42 avec prénom, 35 avec e-mail)
  dans `couple_json.conjoint`, mais il n'est **pas dans la liste des mandants** → il ne serait **ni dans le PDF ni
  signataire**. C'est D22 (« conjoint ajouté d'office ») qui doit le prendre là.

### 8.3 Ce que ça change à la proposition
- **Q1 (le conjoint) est en grande partie TRANCHÉE par le chantier des couples** : le conjoint EST la seconde fiche de
  Hektor (le bloc `_m2`), il est connu chez nous dans `couple_json.conjoint`, et les gestes pour le modifier, le compléter
  ou l'ajouter existent. Il ne faut plus rien inventer : la fenêtre RÉUTILISE ces portes. Ce qui reste à décider, c'est
  **comment un conjoint non lié au bien devient signataire** (voir le message du 05/11).
- ⛔ **Règle nouvelle pour la fenêtre** : une correction sur le CONJOINT passe par « modifier le conjoint » (la fiche
  principale, `app_edit_conjoint_optimistic`), **jamais** par la porte du mandant sur la seconde fiche. Le formulaire
  d'une seconde fiche chez Hektor est celui du FOYER (essais du 30/10) : y écrire nom/prénom du conjoint risquerait
  d'écrire sur la place 1. ⚠ **NON MESURÉ** (une lecture GET sur un couple fictif le dirait) — et le risque existe DÉJÀ
  aujourd'hui pour les 9 conjoints liés comme mandants, par le crayon de l'onglet Mandants. Noté pour le chantier des couples.
- **La fenêtre lira `nature_fiche`** pour classer chaque carte (personne, couple, conjoint, case vide), plutôt que de
  deviner par le texte. Le filtre 3-A du document reste tel quel (il n'est pas à moi).
- **Q3 reste vraie** (la porte du mandant ignore toujours le 2e téléphone). Q2, Q4, Q5, Q6 inchangées.

### 8.4 Les essais rejoués sur le code du 05/11
`test_mandat_chez_nous_et_mandataire.js` vert · `test_garde_r1_signature.js` vert (avec la scène 4 bis) ·
`apps/hektor-v1/scripts/test_reperes_signature.mjs` vert · `test_couple_modification.js` vert · `node --check` du worker OK.
Base : `signature_youtrust = off`, 0 demande, 0 événement, 0 travail Youtrust.

### 8.5 Tranché le 05/11 — D25
**Le conjoint nommé mais non lié au bien est LIÉ COMME MANDANT**, par un clic que l'agent confirme dans la fenêtre
(porte `app_link_mandant_optimistic`). Détail et réserves : plan signature, « D25 » (avant le lot 6b). Q1 est donc
tranchée pour ce cas. Restent Q2 à Q6.

### 8.6 Tranché le 05/11 — D26 à D30
« Oui, Q2 à Q6 » : mes recommandations du §7 sont retenues (détail : plan signature, « D26 à D30 »). Toutes les questions
de la proposition sont tranchées ; la suite est la maquette (lot 6a), puis le lot 6b en pièces.
