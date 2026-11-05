# Audit pour la refonte de la modale « Changer le statut » — visuel seul, guide métier GTI

*05/11/2026. Lecture seule : rien n'a été écrit en base, chez Hektor ni dans le code. La modale a été
ouverte en production dans la session Chrome de Frédéric (fenêtre 1280 × 665) sur V770063362 (Actif,
Jullianges) et VM412 (Sous compromis, Vollore-Ville), puis refermée sans rien envoyer.*

Maquette : https://claude.ai/artifact/Nx54fe4qLykaqMDr8EyuaF (privée).

## 0. Consigne et sources

**Consigne de Frédéric (05/11)** : « tu dois tout changer visuellement mais rien dans le fonctionnement
derrière ». Les explications parlent **du métier et de GTI Immobilier** (« un petit guide pour les aider à
faire les étapes correctement »), pas de Hektor. Relier la modale aux autres objets de l'app (documents,
partenaires). Animations dynamiques.

Cet audit **ne refait pas** ce qui existe, il s'appuie dessus :
- `AUDIT_ERGONOMIE_STATUT_ANNONCE_AFFAIRES_2026-10-02.md` — les défauts G1-G4, I1-I6, D1-D7 et l'architecture cible.
  ⭐ Il disait déjà : « Le négociateur pense « j'ai reçu une offre »… jamais « je change le statut » ».
- `AUDIT_MODALE_STATUT_REGLES_2026-10-30.md` — chaque geste, chaque garde, chaque droit, les dépendances cachées.
- Trois relevés du jour (documents et signature ; contacts et partenaires ; métier déjà écrit dans l'app).
- Mesures du jour sur le registre (`app_affaire_ledger`) et la file (`app_console_job`).

## 1. Le contrat de non-régression

**Ne change pas — appelé exactement comme aujourd'hui, avec les mêmes valeurs :**
- `handleChangeHektorAnnonceStatus(event, reprendre)` → `createChangeHektorAnnonceStatusJob` (même charge), puis
  `setMandatClotureApp`, `saveRepartition`, `ecrireAffaireCommission`, conditions, note, `relireApresLeGeste`.
- `handleGesteHektor('refus' | 'accepte' | 'annuler_compromis' | 'supprimer_compromis' | 'supprimer_vente')` → `gesteAffaireOptimistic`.
- Tous les états React de la modale (`statusChange*`, ~60), les drapeaux d'intention (`…Affirmes`, `…Touche`,
  `statusChangeTouches`), `statusChangeAffaireChoisie`, les effets de préremplissage et d'héritage.
- Toutes les gardes : bien vendu / clos / estimation, bien engagé, garde-fou de chaîne, offre verrouillée,
  compromis verrouillé, offre acceptée figée, négociateur manquant, travail déjà en cours, montant / prix /
  motif exigés, droits manager-admin.
- La version téléphone garde le même état et les mêmes gestes.

**Change — l'écran seulement :**
- l'entrée : un **événement métier** au lieu d'un statut (table §2) ; l'événement pose `statusChangeStatus`
  ou appelle `handleGesteHektor`, comme les boutons d'aujourd'hui ;
- l'ordre, le regroupement, les libellés, le guide, les animations ;
- `window.confirm` (suppression du compromis, de la vente) devient un dialogue dessiné **avec le même
  avertissement et le même résultat** (oui → le geste, non → rien) ; les mots suivent le nouveau vocabulaire
  (« Effacer », « Le compromis tombe » au lieu de « Supprimer », « Annuler le compromis »).

**Ajouté en LECTURE seule (aucune écriture nouvelle), à valider :**
- `loadConsoleDocuments(app_dossier_id)` à l'ouverture, pour montrer les pièces de l'étape (§5) ;
- `piecesDuDossier()` (déjà exporté par `FicheNotaire.tsx:109`) sur les noms de ces documents ;
- `openContactDirectory(id)` (App.tsx:16321) branché sur les jetons acquéreur / mandant / notaire.
  ⚠ Superposition avec la fiche contact en pop-up **non vérifiée** ; depuis le registre l'app bascule sur
  l'écran Contacts (relevé du jour, §3) : il faudra l'éprouver avant de le promettre.
- l'ajout d'un document passe par le panneau existant `ConsoleDocumentsPanel` (même travail d'envoi).

**Retiré de la v2 de la maquette, parce que ce serait un changement de fonctionnement :** enchaîner
« annuler le compromis » et « Actif », créer et accepter une offre d'un seul geste, rendre l'acquéreur
obligatoire, un motif d'annulation du compromis, limiter « Clos » aux biens sans affaire.
⚠ Le premier contredisait d'ailleurs une décision écrite (étude du 01/09 : « un compromis échoué ne relance
pas la diffusion automatiquement »).

## 2. Événement métier → geste existant (rien d'autre n'est appelé)

| situation du bien | événement affiché | ce qui est appelé (inchangé) |
|---|---|---|
| Actif sans affaire | Une offre est faite | onglet `offer` → « Envoyer vers Offre » |
| | Le compromis est signé directement | onglet `compromise` → « Envoyer vers Compromis » |
| | Le mandat s'arrête | onglet `closed` → « Envoyer vers Clos » |
| | (autres) L'acte est signé sans compromis | onglet `sold` |
| Offre en cours, non acceptée | Le vendeur accepte / refuse | `handleGesteHektor('accepte' / 'refus')` |
| | Corriger l'offre | onglet `offer` → « Modifier chez Hektor » |
| | Une autre offre arrive | onglet `offer` → « Envoyer vers Offre » (si non engagé) |
| Offre acceptée (engagé) | Le compromis est signé | onglet `compromise` (préremplissage de l'offre acceptée) |
| | L'offre tombe | `handleGesteHektor('refus')` |
| | Refuser une offre concurrente | « Choisir » puis `refus` (offre écartée d'un bien engagé) |
| Sous compromis | L'acte est signé | onglet `sold` (héritage du compromis) |
| | Mettre à jour le compromis | onglet `compromise` → « Modifier chez Hektor » |
| | Le compromis tombe | `handleGesteHektor('annuler_compromis')` |
| | (autres) Effacer une erreur de saisie | `handleGesteHektor('supprimer_compromis')` + confirmation |
| Vendu | Corriger la vente / (autres) Effacer | onglet `sold` → « Modifier » / `supprimer_vente` |
| Vendu, Clos, Estimation, ou partout en « autres » | Remettre en vente | onglet `active` → « Envoyer vers Actif » |
| partout en « autres » | Clore le mandat | onglet `closed` |

Les gestes impossibles ne sont **pas proposés** (les mêmes fonctions de garde décident) ; s'ils le sont
aujourd'hui sous forme d'onglet, ils restent atteignables dans « Autres gestes » avec la phrase qui dit
pourquoi ils sont fermés — on ne perd aucun chemin.

## 3. Ce que dit l'usage (mesuré le 05/11)

- Statuts du parc vivant : Actif 584 · Sous offre 37 · Sous compromis 94 · Estimation 12 818.
- Registre depuis janvier 2025 : 698 compromis, 640 ventes ; 88 % des compromis ont une offre avant, 98 % des
  ventes un compromis ; ventes sans rien avant : 5 sur 640. Offre → compromis : 32 j (médiane) ;
  compromis → acte : 90 j. 8 % des compromis tombent (58 sur 698).
- Du compromis à la vente : prix identique 97 %, acquéreur 96 %, notaires 92-95 %, honoraires vendeur 99,8 %.
  De l'offre au compromis : prix 95 %, acquéreur 91 %.
- Offres en 2025 : 331 acceptées, 4 proposées, 0 refusée → elles sont saisies une fois acceptées.
- Qui envoie : 108 des 176 travaux `change_hektor_annonce_status` sont de Frédéric (le reste : essais, scripts).
- Gardé chez nous : répartition 16 122 lignes ; conditions suspensives 5 en tout ; notes 9.
- Documents : 193 289 fiches, toutes `document_type = "document"`. Reconnues par le nom : mandat 14 112,
  offre 11 821, diagnostics 8 778, avenant 7 380, identité 5 776, avis de valeur 5 413, compromis 4 155,
  titre de propriété 4 146, taxe foncière 3 575, bon de visite 2 933, acte 2 395.
- Partenaires (`app_partenaire_metier`) : notaire 1 656, syndic 75, diagnostiqueur 36, apporteur 35,
  courtier 22, parrain 15, banque 8… ; `app_partenaire_lien` : 83 liens, tous sur un **bien** (79 syndics,
  4 diagnostiqueurs), **aucun** sur une affaire, et **aucun écran ne la lit**.
- En production, fenêtre 1280 × 665 : zone utile 482 px ; formulaire 1 260 px (offre) à 1 982 px (compromis).

## 4. Le guide métier GTI — ce que l'app sait déjà (aucune règle inventée)

Chaque phrase du guide vient d'une source du projet :

- **Une affaire a trois étapes : offre → compromis → vente** (définition de Frédéric,
  `ETUDE_STATUT_ANNONCE_TRANSACTIONS_MANDAT_2026-09-01.md`). « Une offre peut être refusée, un compromis annulé
  — la vente est définitive » (App.tsx:30152).
- **Plusieurs acheteurs peuvent proposer en même temps ; une seule offre peut être acceptée**
  (`avisPlusieursAffaires`). Une fois acceptée, **le bien est engagé** : plus de nouvelle offre tant que le
  dossier vit.
- **Une offre acceptée est figée** : pour changer son montant, la refuser, la corriger, l'accepter de nouveau.
- **Validité de l'offre et rétractation : 10 jours par défaut** (App.tsx:18264-18265).
- **Un seul compromis à la fois** (`ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md`, garde-fou de chaîne).
- **Le compromis reprend l'offre acceptée** (montant, acquéreurs), **la vente reprend le compromis**.
- **Annuler n'est pas supprimer** : annuler garde la trace (« c'est le geste normal quand une vente ne se fait
  pas ») ; supprimer efface, sans retour, et sert aux erreurs de saisie et aux essais.
- **Seule la création d'une transaction déplace le statut** : refuser, accepter, annuler ne le bougent pas
  (protocole du 01/09). Après un compromis tombé, le bien reste « Sous compromis » **jusqu'à ce qu'on le remette
  en vente** ; la diffusion ne repart pas seule (arbitrage du 01/09).
- **Remettre en vente (Actif) rallume la diffusion** (`diffusable = 1`, AUDIT_MODALE §3.4).
- **Conditions suspensives** : catalogue « Préemption mairie » (0 j) et « Obtention Crédit » (45 j) ; échéance =
  date du compromis + délai ; états En attente / Levée / Non levée / Sans objet ; « Suivez les conditions
  suspensives jusqu'à l'acte » (cockpit, étape compromis).
- **Les pièces du dossier notaire** (`PIECES_DU_DOSSIER`, 11) : titre de propriété, diagnostics (DDT),
  compromis signé, notification SRU, pièces d'identité, taxe foncière, mandat de vente, attestation de séquestre,
  offre de prêt de l'acquéreur, assainissement (SPANC), plan cadastral.
- **Qui paie la commission** : vendeur dans 95,5 % des cas (bascule de 2017, A10/A11) — défaut « Vendeur ».
- **Répartition** : entrée (qui a rentré le bien) et sortie (qui l'a vendu), parts égales jusqu'à 3 ; ce qui
  manque à 100 % est la part réseau ; au-delà de 100 % c'est refusé. Elle reste chez nous.
- **Honoraires vendeur à l'offre** : gardés chez nous. Au compromis : « celle du mandat si vide ».
- **Le compte** : prix = net vendeur + honoraires vendeur + honoraires acquéreur ; on prévient, on ne bloque pas.
- **Vendu** : le bien reste dans les biens actuels ; l'archiver est un geste à part, rare. Le mandat est clos
  chez nous à la date de la vente (worker `cloturerMandatLocalement`).
- **Clore le mandat** : motifs non renouvelé / vendu (agence, confrère, propriétaire) / autre ; la date et le
  motif restent chez nous ; « S'il y a une offre ou un compromis en cours, vérifie-les avant de clôturer ».
  « Vendu par l'agence » : passer par l'acte signé, pas par la clôture (doublon signalé I6 du 02/10).
- **Demandes à la Direction (Pauline)** : la baisse de prix (avenant) et l'annulation de mandat passent par une
  demande ; « le prix et le statut ne changent qu'après acceptation ». Le guide y renvoie, il ne les remplace pas.

## 5. Les liens avec le reste de l'app

- **Documents** : aucun lien document ↔ transaction en base ; on reconnaît par le nom (comme la fiche Notaire
  et le registre des transactions, `DOCUMENT_DE_TRANSACTION`). Sur VM412, les noms racontent l'affaire :
  offre PELAYO, deux refus de prêt (CIC, Banque Chalus) → compromis annulé ; offre LEREST 97 000 € signée par
  les trois vendeurs ; « Copie AAE COMPROMIS CTS CAULIER _ LEREST ». Pièces du dossier : 6 sur 11 (manquent
  SRU, taxe foncière, attestation de séquestre, offre de prêt, SPANC).
  Par étape : offre → « offre » ; compromis → les 11 pièces ; acte → « acte » / « authentique ».
  Sur V770063362 (Jullianges) : 4 sur 11 reconnues, alors que 6 sont là — le mandat signé s'appelle
  « 18978 - FOURNERY » et la carte d'identité « CI FOURNERY » (la règle attend « mandat », « CNI » ou
  « identité »). La reconnaissance par le nom sous-compte : à dire à l'écran, pas à cacher.
- **Contacts** : les jetons de la modale ne s'ouvrent pas aujourd'hui ; le registre des transactions le fait
  déjà (bloc « Les parties », `onOuvrirContact`) — c'est le modèle.
- **Partenaires** : un partenaire est un contact (décision `CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md`) ;
  le notaire a sa fiche (`FicheNotaire.tsx`, « Partenaire depuis AAAA », pièces du dossier). Courtier, banque,
  apporteur : le registre existe mais aucun lien n'est posé sur une affaire et l'annuaire (K6) n'est pas codé —
  la maquette ne les montre donc **pas** comme une donnée.

## 6. Les animations proposées (cohérentes avec l'existant)

Repères existants : `--bv-ease`, 150 / 240 ms ; `fa-ck-rise` (cascade), `fa-ck-jalon-pulse` (jalon courant),
`mv3beacon` (balise du bouton principal), coche tracée de `BienvuLoader`. ⚠ Jamais de `transform` sur le
conteneur `fixed` de la modale (piège noté dans `fa-mandat-v3.css`) ; tout sous
`prefers-reduced-motion: no-preference`.

1. la frise de l'affaire se trace jusqu'à l'étape en cours, le jalon courant pulse ;
2. les cartes d'événement entrent en cascade (40 ms) ;
3. le passage événement → formulaire : la carte choisie devient le titre (fondu + glissement interne) ;
4. « Repris de… » : chaque ligne reçoit sa coche tracée, l'une après l'autre ;
5. la pastille « Aujourd'hui → Après » glisse quand on change d'événement ;
6. le compte (net + honoraires = prix) et la jauge de répartition s'animent quand on tape ;
7. les pièces du dossier se cochent ; la jauge « 6 sur 11 » se remplit ;
8. le bouton principal porte la balise `mv3beacon` quand tout l'essentiel est rempli ;
9. confirmation destructive : dialogue dessiné, le bouton rouge n'est actif qu'après lecture (1,5 s).

## 7. Incohérences relevées en passant (non traitées)

- Le cockpit dit, à l'étape `offre_ref` : « L'annonce repasse en Actif » ; la règle mesurée dit qu'un refus ne
  déplace pas le statut. Un des deux textes est faux.
- Clôture : « définitive côté Hektor » puis « réactivable via Actif » (I6 du 02/10, toujours là le 05/11).
- Sur un bien Actif, la modale propose « Actif » (I1 du 02/10, toujours là).
- Jargon toujours affiché le 05/11 : « le worker relance une reprise ciblée… le run quotidien… ».

## 8. Questions ouvertes (déjà posées le 02/10, sans réponse retrouvée)

1. Le négociateur doit-il pouvoir remettre en Actif ? 2. Compromis sans offre : libre ou guidé ?
3. Supprimer réservé à l'admin ? 4. Répartition dès l'offre ?
Et du jour : 5. brancher l'ouverture des fiches contact depuis la modale (lecture, mais superposition à
éprouver) ; 6. charger les documents à l'ouverture (lecture).

## 9. Les 5 améliorations retenues par Frédéric (05/11, soir) — maquette « haut de gamme »

Base validée : la version simple (structure de la modale actuelle). Au-dessus, ces 5 améliorations,
toutes côté écran, sans rien changer aux envois :

1. **Statuts impossibles grisés avec leur raison sur la carte** (« Figée : un compromis est en cours »,
   « Le bien est déjà en vente »). Les mêmes fonctions de garde décident ; la carte reste cliquable et
   ouvre l'explication.
2. **Avant → après au survol du bouton principal** : statut avant, statut après, 2 effets réels
   (diffusion rallumée par Actif, mandat clos à la date de la vente, portails coupés par Clos…).
3. **Repris / modifié / actuel sur chaque champ** : pastille « Repris du compromis », « Prix du bien »,
   « Aujourd'hui », « Par défaut », et « Modifié » dès qu'on tape. Repose sur `statusChangeTouches`,
   déjà tenu par la modale (seuls les champs touchés partent en modification).
4. **Champs obligatoires signalés avant le clic** : astérisque, pastille « À remplir », bouton éteint et
   phrase « À remplir avant d'envoyer : … ». Mêmes règles que les messages actuels (montant, prix de
   vente, motif « Autre »), seulement avancées avant le clic.
5. **Suivi du geste après le clic** : « Enregistré chez nous », « Envoyé à Hektor », « Rubriques
   relues », puis « Prochaine étape » avec un lien vers un geste existant. ⚠ C'est le seul point qui
   change un comportement d'écran : aujourd'hui la modale se ferme tout de suite ; ici elle reste
   ouverte le temps du suivi. Le suivi lit le travail déjà mémorisé (`rememberHektorActionJob`).

Plus le bloc explicatif « Le guide GTI » (titre, deux phrases, « Comment faire » en 3 étapes), coloré
selon le ton (information, réussite, attention, blocage).

## 10. Quels onglets selon la situation du bien — analyse du 05/11 (demande de Frédéric)

Consigne : « tout ne devrait pas être accessible, il faut respecter un ordre logique ; orienter
l'utilisateur tout en gardant l'ensemble des fonctions accessibles pour les admins ».
⚠ Aujourd'hui la modale n'est ouverte qu'aux rôles `manager` et `admin` (`isManagerOrAdmin`) ; le rôle
`commercial` (négociateur) ne la voit pas. « Orienter » vise donc d'abord les managers.

### 10.1 L'ordre logique (retrouvé, pas inventé)
Avis de valeur (Estimation) → mandat signé → mandat validé par la Direction (débloque la diffusion) →
en vente (Actif) → offre(s) → offre acceptée (bien ENGAGÉ) → compromis (un seul à la fois) → acte
(Vendu, définitif). Sortie possible à tout moment avant l'acte : Clos. Retours : offre refusée,
compromis annulé — **le statut ne bouge pas** (seule la création d'une transaction le déplace), on
remet en vente par Actif. Effacer = erreur de saisie.
Sources : frise du cockpit, définition offre → compromis → vente, protocole du 01/09, garde-fou de
chaîne, `bienEngage`, textes `CK_STAGES` (man_valider, mandat_echu, mandat_annul).
Mesures (depuis 2025) : 88 % des compromis ont une offre avant, 98 % des ventes un compromis,
5 ventes sur 640 sans rien avant.

### 10.2 Ce qui décide — regarder le DOSSIER, pas seulement le statut
- le dossier d'affaire : aucun / offre(s) non acceptée(s) / engagé (offre acceptée) / compromis
  vivant / vendu ; les dossiers terminés ne comptent pas ;
- le mandat : validé ou « à contrôler », échu (date de fin passée), annulation demandée, clos ;
- l'annonce : estimation, archivée, brouillon (pas de modale pour ces deux derniers) ;
- le rôle.
Mesures du parc vivant (05/11) : Sous offre 37 dont 35 engagés par une offre acceptée, 1 sans
affaire vivante, 1 avec un compromis vivant ; Sous compromis 94, tous avec compromis vivant ; Actif
585 dont 1 avec un compromis vivant. → statut et dossier concordent à 99,6 % ; les 3 écarts
justifient de décider sur le dossier.
Mandats des biens Actif : 330 validés et en cours, 237 « à contrôler » (dont 164 sans date de fin),
26 échus. Sous compromis à mandat échu : 24 (normal : signé avant l'échéance). Depuis 2025, sur le
parc vivant : 10 offres sur 168 et 12 compromis sur 100 datés APRÈS la fin du mandat. ⚠ Les dates de
mandat ne sont pas toutes fiables (numéros recyclés, mandats « commencés après la vente ») : une
règle sur les dates doit prévenir avant de bloquer.

### 10.3 Règles déjà en place (base + écran) — inchangées, pour tous, admin compris
Pas d'offre / compromis / vente sur un bien Vendu, Clos ou en Estimation · pas de nouvelle offre sur un
bien engagé · un seul compromis / une seule vente par dossier ouvert · offre verrouillée par son
dossier · compromis verrouillé par sa vente · offre acceptée figée · archivé et brouillon : pas de geste.

### 10.4 La matrice proposée (orientation côté écran ; l'admin garde tout)
Pour chaque situation : l'onglet CONSEILLÉ (la modale s'ouvre dessus), les onglets OUVERTS, les FERMÉS
pour un manager (visibles, grisés, avec la raison), et l'admin qui peut tout rouvrir.
1. Estimation, pas de mandat → conseillé : aucun (créer puis faire valider le mandat, hors modale) ;
   ouvert : Clos ; fermé : Actif (« passe par le mandat et la validation »), Offre, Compromis, Vendu.
2. Mandat signé, « à contrôler » (pas validé), Actif → conseillé : demander la validation (hors modale) ;
   ouvert avec avertissement : Offre, Compromis, Clos ; fermé : Vendu, Actif. [à trancher : prévenir ou bloquer]
3. En vente (Actif, mandat validé et en cours, aucune affaire) → conseillé : Offre ; ouvert : Offre,
   Compromis (direct), Clos ; fermé : Actif (déjà actif), Vendu (sans compromis : rare).
4. Mandat échu, aucune affaire → conseillé : refaire ou proroger le mandat (hors modale) ; ouvert : Clos ;
   fermé : Offre, Compromis, Vendu. [à trancher : bloquer ou prévenir — dates peu fiables]
5. Annulation du mandat demandée (en attente de la Direction) → tout fermé (« actions commerciales
   gelées », comme le cockpit). Aucune aujourd'hui.
6. Offre(s) en cours, aucune acceptée → conseillé : Offre (accepter, refuser, en ajouter une) ;
   ouvert : Offre, Compromis (avec « accepte d'abord l'offre »), Clos (avertissement) ; fermé : Vendu,
   Actif (tant qu'une offre vit).
7. Engagé par une offre acceptée → conseillé : Compromis (repris de l'offre) ; ouvert : Offre (refuser
   l'acceptée ou une concurrente), Compromis ; fermé : Vendu, Actif, Clos (« fais d'abord tomber l'affaire »).
8. Compromis vivant → conseillé : Vendu (repris du compromis) ; ouvert : Compromis (modifier,
   annuler), Vendu ; lecture seule : Offre ; fermé : Actif, Clos, et Supprimer (admin).
9. Statut resté « Sous offre / Sous compromis » sans affaire vivante (après un refus ou une
   annulation) → conseillé : Actif (remettre en vente) ; ouvert : Actif, Offre, Compromis, Clos ; fermé : Vendu.
10. Vendu → conseillé : aucun (dossier terminé) ; ouvert : Vendu (corriger) ; admin seul : Supprimer la
    vente, Actif (rouvrir) ; fermé : le reste (déjà la règle).
11. Clos → conseillé : aucun ; admin seul ou à trancher : Actif (rouvrir le mandat) ; fermé : le reste.

### 10.5 Ce que voit l'admin
Le même écran guidé, plus un interrupteur « Tous les gestes » dans l'en-tête : les onglets fermés par
l'ORDRE se rouvrent avec un bandeau « hors parcours conseillé ». Les règles de la BASE (§10.3) restent
pour lui aussi : elles ne sont pas de l'orientation, ce sont des garde-fous.

### 10.6 À trancher par Frédéric
1. Mandat « à contrôler » : prévenir ou bloquer offre et compromis pour un manager ?
2. Mandat échu : bloquer ou prévenir ?
3. Clos → Actif : manager autorisé, ou nouveau mandat exigé (admin seul) ?
4. Supprimer un compromis, une vente : admin seul ?
5. Vendu sans compromis : admin seul ?
6. Un jour, ouvrir cette modale guidée aux négociateurs (rôle `commercial`) ?

## 11. Décision du 05/11 : modale réservée à admin et manager, TOUT reste accessible

Frédéric : « on réserve uniquement à admin / manager cette modale, donc toutes les fonctions doivent
rester accessibles, mais on évite les erreurs avec une bonne ergonomie ». La matrice du §10 ne FERME
donc rien par rôle : elle ORIENTE.
- la modale s'ouvre sur l'onglet CONSEILLÉ (seul l'onglet de départ change) ;
- un onglet hors du parcours logique reste ouvert, marqué « Hors parcours », avec un bandeau qui dit
  pourquoi et une case « Je le fais volontairement » à cocher avant d'envoyer (écran seulement) ;
- ce que la BASE interdit déjà reste montré en lecture seule, avec sa raison (rien de nouveau) ;
- les gestes sans retour passent par une fenêtre de confirmation dessinée, qui propose d'abord le geste
  réversible, bouton rouge actif après lecture.
Les questions 1 à 6 du §10.6 tombent : on ne bloque ni sur le mandat ni sur le rôle ; le mandat
« à contrôler » ou échu devient un AVERTISSEMENT dans le guide.
Maquette : version professionnelle, https://claude.ai/artifact/Nx54fe4qLykaqMDr8EyuaF (première planche).

## 12. Cliquer sur une autre affaire de la liste — ce qui se passe (lu dans le code le 05/11, non éprouvé)

- **Clic sur une ligne** : ouvre ou ferme son détail (`<details>`), en lecture seule. Rien d'autre.
- **« Choisir »** (affiché seulement : onglet Offre d'un bien NON engagé — toute offre, même refusée ;
  offre écartée d'un bien engagé, pour la refuser ; compromis ou vente quand plusieurs sont vivants) :
  `setStatusChangeAffaireChoisie(id)` → la ligne devient « visée par les actions », les boutons du pied
  la visent, les conditions et la note se rechargent pour elle (effet App.tsx:18209, dépend du choix),
  la reprise de commission se relance (18262), la répartition bascule sur son dossier (19136/19313) —
  SAUF si une ligne de répartition a été saisie : la saisie est gardée et serait enregistrée sur l'autre
  dossier (risque déjà noté le 30/10, §3.12, non mesuré).
- ⚠ **TROUVAILLE : les champs principaux ne se rechargent pas au choix.** L'effet de préremplissage
  (montant, prix, date, date d'acte, séquestre, net, honoraires, validité, rétractation, acquéreurs,
  mandants, notaires, mandat : App.tsx:18832 → 19012) dépend de `[statusChangeAffaires,
  statusChangeStatus, carnetAffaires]`, PAS de `statusChangeAffaireChoisie`. Après « Choisir », le
  formulaire garde les valeurs d'avant (souvent le prix du bien, posé à l'ouverture).
  Conséquence possible : « Modifier chez Hektor » sur l'affaire choisie part avec ces valeurs. Chez nous,
  le carnet et le registre sont protégés (interrupteurs `affaire_modif_champs_touches` et
  `affaire_modif_au_registre` à `on` : seul ce qui a été TAPÉ entre) ; mais la charge part ENTIÈRE au
  worker, qui reconstruit le formulaire de Hektor avec elle (commentaire de
  `app_modifier_affaire_optimistic`) → risque d'écrire chez Hektor des valeurs qui ne sont pas celles de
  l'affaire choisie. « Refuser » et « Accepter » ne lisent pas le formulaire : sans risque.
  Biens concernés aujourd'hui (onglet Offre, bien non engagé avec au moins une offre au registre) :
  14 biens Actif et 1 Sous offre.
  Depuis le registre des transactions, le choix est posé à l'ouverture avec le statut : les champs sont
  bien remplis (pas de défaut sur ce chemin).
- **Changer d'onglet** remet le choix à zéro (App.tsx:22815).
- ⛔ Corriger = ajouter le choix aux dépendances de l'effet : c'est du code « derrière », HORS du chantier
  visuel. À décider par Frédéric, et à éprouver (essai hors ligne + bien d'essai 62774).

## 13. Offre « proposée » dans un dossier, compromis en cours dans un autre (question du 05/11)

« Je ne peux pas valider l'offre d'achat pour la relier à la chaîne si j'ai oublié. »

**Ce qui existe déjà** — § 2.8 du chaînage (décision du 30/10, `ANALYSE_28_OFFRES_CHAINAGE_2026-10-30.md`) :
un compromis VIVANT rejoint la chaîne de l'offre « proposée » du MÊME acquéreur (le nom est obligatoire).
ALLUMÉ des deux côtés : `APP_CHAINAGE_OFFRE_PROPOSEE=1` (run de nuit) et
`app_setting chainage_offre_proposee = on` (base, à la création dans l'app).
Mesure du 05/11 : 15 chaînes portent une offre « proposée » ET un compromis vivant (déjà recollées) ;
0 bien du parc vivant n'a une offre « proposée » dans un AUTRE dossier que son compromis vivant.

**Ce que l'écran permet aujourd'hui**
- même dossier (recollé) : l'offre est « verrouillée par son dossier » → ni Accepter ni Refuser
  (écran ET base, `offre_verrouillee`). Elle reste « proposée », comme Hektor la laisse souvent.
- autre dossier (acquéreur au nom différent : offre au nom de Monsieur, compromis au nom de Madame) :
  l'offre est « écartée d'un bien engagé » → « Choisir » puis REFUSER seulement ; « Accepter » est caché
  par l'écran (décision du 26/10 : « une offre écartée se refuse, elle ne s'accepte pas », crainte
  d'engager le bien deux fois). ⚠ La base, elle, l'accepterait (elle ne regarde que le dossier de
  l'offre). Et la nuit, une offre ACCEPTÉE datée avant le compromis attire celui-ci (règle du 04/09,
  par les dates) : accepter suffirait donc à relier — NON ÉPROUVÉ, et la réaction de Hektor (accepter une
  offre quand un compromis existe) n'est PAS MESURÉE.
- offre jamais saisie, compromis déjà là : « Envoyer vers Offre » est fermé sur un bien engagé
  (écran seulement) → on ne peut pas régulariser l'oubli.

**Options (fonctionnement, donc HORS du chantier visuel, à décider)** :
1. « Accepter » permis pour une offre écartée DATÉE AVANT le compromis en cours, quand aucune autre offre
   n'est acceptée (régularisation) — écran seulement, la base l'accepte déjà ; à éprouver sur 62774
   (Hektor) et par simulation du chaînage.
2. Une ligne d'information dans la modale : « Cette offre sera rattachée cette nuit au compromis de … »
   (même acquéreur) — lecture seule, compatible avec le chantier visuel.
3. Enregistrer après coup une offre oubliée sur un bien engagé — rouvrirait la règle du 26/10.

## 14. Options 1 et 2 retenues par Frédéric (05/11) — le plan, AVANT tout code

### Ce qui a été vérifié
- **La base** (`app_geste_affaire_optimistic`, lue le 05/11) : pour « accepte » sur une offre, elle ne
  refuse que si le dossier DE L'OFFRE porte un compromis ou une vente vivant (`offre_verrouillee`). Une
  offre restée dans un autre dossier que le compromis passe. → **Rien à changer en base.**
- **La nuit** (`recalculer_les_chaines`, règle du 04/09) : un compromis rejoint la chaîne OUVERTE qui a
  une offre ACCEPTÉE, par ordre de date. Une offre acceptée datée AVANT le compromis l'attire donc. Le
  numéro de la chaîne fusionnée = le plus petit `app_affaire_id` (souvent l'offre).
- **La répartition** suit sa transaction : `app_repartition_purger_orphelines` (D8, 28/10), lancée chaque
  nuit par `run_full_pipeline.ps1` (`--purger-orphelines`), ramène une saisie orpheline vers le dossier
  qui porte désormais sa transaction. Exception : si l'autre dossier a AUSSI une saisie manuelle, elle
  est gardée de côté et signalée (`conflits`).
- **Le worker** : si Hektor refuse l'acceptation, il remet l'état d'avant (`restaurerEtatAffaire`).
  Ce que Hektor fait quand on accepte une offre alors qu'un compromis existe : NON MESURÉ.

### Option 1 — « Accepter » pour régulariser (écran seulement)
- Nouvelle fonction pure `offreARegulariser(lignes, offre)`, à côté de `offreEcarteeSurBienEngage` :
  vraie si l'offre est « écartée d'un bien engagé » (fonction existante) ET qu'il y a UN seul compromis
  vivant dans un dossier ouvert ET aucune offre acceptée vivante dans un dossier ouvert ET que l'offre
  est datée AVANT ce compromis.
- Bouton « Accepter l'offre » : condition actuelle `… && !offreEcarteeSurBienEngage(…)` devient
  `… && (!offreEcarteeSurBienEngage(…) || offreARegulariser(…))`.
- Un bandeau quand l'offre choisie est régularisable : « Régularisation : cette offre date d'avant le
  compromis du … ; l'accepter la rattache à ce compromis cette nuit. »
- Ce qui ne change pas : la base, le worker, le geste (`handleGesteHektor('accepte')`), les autres
  boutons, la règle du 26/10 pour une VRAIE offre concurrente (datée après, ou avec une autre offre
  acceptée : toujours « Refuser » seulement).

### Option 2 — dire le rattachement (lecture seule)
- Dans la liste des affaires et sur l'offre en lecture seule : « Rattachée au compromis du JJ/MM (même
  acquéreur) » quand une offre « proposée » est dans la chaîne d'un compromis vivant (15 chaînes
  aujourd'hui) ; « Sera rattachée cette nuit au compromis du JJ/MM » quand elle est dans un autre
  dossier avec le même acquéreur (0 aujourd'hui, possible si le compromis est créé chez Hektor).
- Même règle que le § 2.8 : le même numéro d'acquéreur.

### Contrôles prévus
1. Essai hors ligne `test_offre_regularisation.cjs` sur les vraies fonctions (modèle :
   `test_boutons_modale_point5.cjs`) : offre avant le compromis → oui ; après → non ; autre offre
   acceptée → non ; offre dans le dossier du compromis → non ; offre refusée → non ; témoin inverse.
2. Simulation du chaînage sur une copie (vraie fonction) : l'offre passée « acceptée » → le compromis
   rejoint sa chaîne ; aucune autre chaîne ne bouge.
3. `npm run build` ; les essais existants restent verts.
4. Écran (maquette de démonstration) : bouton et bandeau visibles seulement dans le bon cas.
5. **Essai réel, seulement avec l'accord de Frédéric** (écrit chez Hektor) : sur le bien d'essai 62774,
   une offre « proposée » au nom A, un compromis au nom B, accepter l'offre, relire Hektor, puis le
   chaînage de la nuit et la répartition.

### Retour arrière
Remettre la condition d'avant (une ligne) et retirer le bandeau ; aucune donnée à réparer, sauf une
offre réellement acceptée entre-temps (elle se refuse par le geste existant).

## 15. Options 1 et 2 CODÉES le 05/11 (« vas-y ») — éprouvées hors ligne, NON poussées

**Le code** (`apps/hektor-v1/src/App.tsx`, écran seulement ; ni base, ni worker, ni run) :
- `dateOffreFaite` : la date de la PREMIÈRE proposition, comme `_date_de_tri` de la nuit ;
- `compromisDeLaRegularisation` / `offreARegulariser` : les 4 conditions du §14 ; une condition de plus
  trouvée en codant : le dossier du compromis ne doit porter AUCUNE offre (sinon, § 2.8 même acquéreur,
  accepter l'autre offre l'en détacherait) ;
- `rattachementOffreProposee` : « fait » (même dossier qu'un compromis vivant) ou « nuit » (même numéro
  d'acquéreur, un seul compromis, daté après) ;
- écran : condition du bouton « Accepter l'offre » élargie à l'offre à régulariser ; bandeau
  « Régularisation possible » ; mention « rattachée au compromis du … » / « sera rattachée cette nuit… »
  dans la liste des affaires ; phrase ajoutée au bandeau « On ne revient plus sur cette offre » ; phrase
  du bandeau « Ce bien est déjà engagé » complétée.

**Les preuves** :
- `node apps/hektor-v1/test_offre_regularisation.cjs` → TOUT VERT (21 cas, témoin inverse, 3 mutants
  attrapés), sur les vraies fonctions découpées dans App.tsx ;
- `python phase2/sync/test_chainage_offre_regularisee.py` (`PYTHONPATH=.`) → TOUT VERT : la VRAIE
  `recalculer_les_chaines`, base en mémoire, interrupteurs de production (V2 et § 2.8 lus allumés) :
  offre « proposée » → deux dossiers ; ACCEPTÉE → le compromis rejoint le dossier de l'offre (n° de
  l'offre) ; même jour → rattachés ; témoin : acceptée mais datée APRÈS → pas de rattachement ;
- `npm run build` vert ; `test_boutons_modale_point5`, `test_heritage_compromis_offre`,
  `test_rubrique_affaires_complete` verts ; `test_bienvu_textes` : 2 rouges ANTÉRIEURS (textes du mandat,
  du conjoint et de l'API hors table, App.tsx:5790/9530/30531, lib/api.ts:11954) — sans lien, ces ajouts
  n'utilisent pas `bvs`.

**Pas vu à l'écran** : l'app de démonstration n'a pas d'affaires (pas de base) ; aucun bien du parc
n'est aujourd'hui dans le cas de l'option 1. Les 15 offres « proposées » déjà rattachées (option 2,
« rattachée au compromis du … ») seront visibles en ligne après déploiement.

**Reste** :
- commit : ⚠ `App.tsx` porte AUSSI une modification d'une autre session (fiche partenaire,
  `ContactDetailPopupV2`) → à séparer au moment du commit (patch par blocs), jamais `git add` du fichier entier ;
- déploiement (Frédéric) puis regard à l'écran sur un bien des 15 ;
- essai réel chez Hektor sur 62774 (accord à part) : accepter une offre quand un compromis existe.
