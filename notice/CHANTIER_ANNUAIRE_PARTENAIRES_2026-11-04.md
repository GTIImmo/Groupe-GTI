# CHANTIER — L'ANNUAIRE DES PARTENAIRES · ouvert le 04/11/2026

> Sorti du chantier ⑧ (couples et contacts). Sources : `SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md` §66 à §69,
> `AUDIT_INDEX_GLOBAL_CONTACTS_2026-11-04.md` §12 à §16.
> **Rien n'est codé. Rien n'est décidé.** Cette note porte la maquette, l'audit, l'inventaire anti-perte, les décisions
> qui attendent Frédéric, et (plus tard, sur son « vas-y ») le plan par lots.
> Données personnelles : jamais dans git ni chez Supabase. Les exemples de la maquette sont FICTIFS.

## 0. Où on en est

- ✅ maquette relue : 7 planches (§68-69) ;
- ✅ les manques dessinés le 04/11 : planches 8, 9 et 10 (voir §2) ;
- ⛔ retour de Frédéric le 04/11 : **maquette refusée** (« un design à la hauteur de mon app », et l'intégration aux
  contacts et aux annonces) → §6 ; la carte d'intégration est proposée au §6.2, le design est à refaire sur la vraie
  fiche de l'app ;
- ✅ **LE PLAN PAR LOTS EST PRÊT le 04/11** (§8, sur le « vas-y » de Frédéric) : lot 0 mesurer · 1 le métier sur le
  serveur · 2 le registre en base · 3 la page partenaire · 4 le syndic · 5 le diagnostiqueur · 6 et 7 courtier et
  apporteur (ordre à fixer). Rien n'est codé ;
- ✅ **TOUTES LES DÉCISIONS SONT TRANCHÉES le 04/11** (§6 bis) : D1 petite table du métier · D2 rien ne part chez
  Hektor (sauf la naissance d'un partenaire créé dans l'app, forme « 1 ») · D3 syndic d'abord, puis diagnostiqueur · D4
  « A » (ils ne sont pas dans l'annuaire des partenaires) · P1 « B » (archivé reste modifiable) · P2 « B » (case à cocher
  + raison) · P4 « B » (la fiche client ne change pas) · Q1 « A » (lien partenaire ↔ client dès le premier jour) · Q2
  « A » (règle légale du DPE) · Q3 « A » (reprise des syndics de Hektor puis suivi de nuit). Forme générale : tous les
  partenaires sont des CONTACTS, le registre se pose par-dessus. ⇒ La liste du §7 est à relire avec ces décisions (§7
  quater) ; le plan par lots attend le « vas-y » ;
- ✅ **DESIGN VALIDÉ par Frédéric le 04/11** (« OK je valide le design ») : les quatre maquettes du §6.3. Sa demande
  suivante : « lister TOUS les mini-chantiers pour TOUTES les fonctions » → §7 ;
- ⬜ les décisions D1 à D4, et les petites décisions P1 à P4 (§5) ;
- ⬜ le plan par lots (§6) — seulement après son « vas-y ».

## 1. La maquette

**https://claude.ai/artifact/Y7xzFasspGEyAX14v4v838** (Design, privée). Dix planches :
1. l'annuaire, interactif (six tuiles de métier, liste, aperçu) ;
2. le téléphone, interactif (cartes, feuille qui monte) ;
3. à 6. une page par métier : banque et courtier, diagnostiqueur, apporteur et parrain, syndic ;
7. « À classer » ;
8. ⭐ **neuve** — le bas de chaque page métier : l'activité (Fil, Rendez-vous, Échanges, les 7 filtres), « La fiche »
   (négociateur, actif ou archivé, éligible app, partenaire depuis, doublon, métier et sa source), « Qualité de la fiche »
   repliée, la « Zone sensible » tout en bas ; le menu « ⋯ » ouvert ; les trois états chargement / vide / erreur ;
9. ⭐ **neuve** — une seule fenêtre pour confirmer Archiver, Réactiver et Supprimer, et la fiche archivée ;
10. ⭐ **neuve** — la page d'un partenaire au téléphone, en trois parties : le métier, l'activité, la fiche.

Corrigé au passage sur la planche 7 : elle disait « le métier part ensuite chez Hektor », ce qui tranchait D2 à la place
de Frédéric. Elle dit maintenant que c'est à décider.

## 2. L'audit (lecture du code et de la base, 04/11)

**Audit limité au contact partenaire et à ses liens.** Annonce, recherche, mandat, document : non concernés, sauf ce qui
est dit.

Les gestes, objet par objet :
- **le contact partenaire — créer** : existe. Le formulaire connaît le métier (`hektorPartnerJobOptions`, `App.tsx` 41067),
  et le worker l'envoie à Hektor (`metier`, `console_job_worker.js` 18683).
- **le contact partenaire — modifier** : existe. Le worker RELIT le formulaire de Hektor avant d'écrire
  (`updateHektorContactIdentity`, 19382). Un métier laissé vide n'est jamais envoyé (`cleanString` et
  `cleanOptionalText` rendent `null`) : **une modification ne peut pas effacer le métier**. Mais elle ne peut pas non plus
  le retirer.
- **le contact partenaire — archiver, réactiver, supprimer** : existent (`archive_hektor_contact`,
  `delete_hektor_contact`). Archiver : `canManageContacts`. Supprimer : `canDeleteContacts` (administrateur et manager).
- **le contact partenaire — lire le métier** : **jamais**. L'API de Hektor ne le rend pas, et aucune colonne chez nous
  ne le porte (vérifié le 04/11 sur `information_schema` : aucune colonne `metier`, `partner`, `courtier`, `syndic`,
  `diagnostiq`, `apporteur`). ⭐ Mais le formulaire HTML de Hektor le porte : le worker le lit déjà à chaque modification.
  Le lire pour ~200 fiches coûterait ~200 requêtes. **Non mesuré** : combien de fiches ont un métier chez Hektor.
- **le type Notaire** : il n'est PAS stocké, il est DÉDUIT du rôle dans le registre (`contactDirectoryCategories`,
  `App.tsx` 40493). Les autres métiers n'ont pas de rôle dans un registre : ils ne peuvent pas être déduits de la même
  façon.
- **les liens d'un partenaire** (courtier ↔ acquéreur, diagnostiqueur ↔ bien, apporteur ↔ affaire, syndic ↔ bien) :
  **rien n'existe**, ni créer, ni modifier, ni supprimer, ni lire. Seule table voisine : `app_notaire_interlocuteur`
  (avec `ecrit_le`, `ecrit_par`, `retire_le`, `retire_par`).
- **transaction** : les conditions de prêt et leurs échéances se lisent dans le registre des transactions.
- **RDV** : Google Agenda, inchangé.
- **recherche, mandat** : sans objet pour un partenaire.

Trois faits trouvés en passant :
- ⚠ **La liste des métiers de Hektor n'a ni « Courtier » ni « Parrain »** (18 valeurs : Notaire 2, Confrère 3,
  Diagnostiqueur 4, Syndic 5, Autre 6, Collaborateur 7, Apporteur 15, « A supprimer » 16, Administration 17, Banque 19,
  Mandataire 20, Agent immobilier 22, Technicien 23…). Elle a en revanche un métier « A supprimer ».
- ⚠ **Netty n'a pas de code « Syndic »** (§16 de l'audit). Le nombre de syndics est donc inconnu ; le « 5 » de la
  maquette est fictif.
- Les nombres des tuiles (30, 16, 50, 5, 13) sont à recompter au moment du code. Netty dit : courtiers 43, banques 39,
  apporteurs 43, parrains 17, diagnostiqueurs 30, administration 11, sociétés 12.

## 3. Ce que la fiche contact fait aujourd'hui, et ce qu'elle confirme

- **Archiver et réactiver** passent par une boîte du navigateur (`window.confirm`, `useArchivageContact`, `App.tsx`
  45392), qui dit le prix : les recherches actives sont archivées aussi, et la réactivation ne les rend pas.
- **Supprimer** passe par une fenêtre où l'on tape `SUPPRIMER CONTACT <numéro>`, avec une raison.
- **Archiver la recherche d'un acheteur** passe par une fenêtre Oui / Non.
- **Supprimer un RDV** passe par une boîte du navigateur.
- Archiver et Supprimer sont dans le même menu « ⋯ » qu'« Ouvrir dans Hektor » (`App.tsx` 47252-47266).

## 4. ANTI-PERTE — chaque fonction de la fiche contact V2, et sa place

- Retour, fil de navigation → le fil « Partenaires › métier » (planches 3 à 6, 8).
- Identité et types → le bandeau (planches 3 à 6).
- Foyer et couple → **retirés d'une page partenaire**, comme la fiche notaire ; ils restent sur la fiche client (§69).
- Créer un RDV → le bandeau, une seule fois (planches 3 à 6, 8).
- Modifier, Changer le métier, Ouvrir dans Hektor → le menu « ⋯ » (planche 8). « Ouvrir dans Hektor » caché sans numéro.
- **Archiver, Réactiver, Supprimer** → ✅ placés : « Zone sensible », tout en bas (planche 8), une seule fenêtre
  (planche 9).
- Coordonnées → Appeler et Écrire dans le bandeau, plus le bloc « Interlocuteurs » (planche 3).
- **Négociateur, actif ou archivé, éligible app, partenaire depuis, sévérité du doublon** → ✅ placés : bloc « La fiche »
  (planche 8), avec le métier et sa source.
- Recherches et rapprochement → sans objet pour un partenaire.
- Biens et mandats liés → remplacés par le bloc du métier (planches 3 à 6).
- « À faire » et relances → le bloc « À faire », avec « + Relance » (planche 3).
- **Activité** (Fil, Rendez-vous, Échanges, les 7 filtres, modifier ou supprimer un RDV, bon de visite, actualiser les
  e-mails) → ✅ placée : en bas de chaque page (planche 8). Les boutons « + RDV » et « + E-mail » de la bande ne sont pas
  repris : ils sont dans le bandeau.
- **Qualité de la fiche** (doublons, complétude, Comparer et fusionner, données Hektor) → ✅ placée, repliée (planche 8).
- Les 7 modales → reprises telles quelles. Seule la confirmation change de forme (planche 9).
- États d'erreur distincts d'un vide → ✅ dessinés (planche 8).
- Au téléphone → ✅ dessiné (planche 10).

## 5. LES DÉCISIONS QUI ATTENDENT FRÉDÉRIC — rien n'est pris

### D1 — Où vit le MÉTIER d'un partenaire chez nous

Les faits : rien ne le porte aujourd'hui (§2). Trois sources possibles : le classeur de Netty (~212 fiches, 113 retrouvées
chez Hektor), l'écran (« Changer le métier », « À classer »), et le formulaire de Hektor (non mesuré).
- **A — une colonne neuve sur la fiche contact.** Simple à lire. ⚠ Non vérifié : si la synchro de nuit réécrit cette
  table, la colonne pourrait être écrasée.
- **B — une petite table à part** (le contact, le métier, sa source : Netty, écran ou Hektor, qui l'a confirmé, quand),
  sur le modèle de `app_notaire_interlocuteur`. La nuit n'y touche pas, et la source se lit à l'écran (« d'après Netty,
  confirmé par Frédéric le 04/11 », planche 8).
- Le remplissage depuis Netty se ferait EN LOCAL (rapprochement nom, prénom, jour de création) ; seul le couple
  numéro de contact + code de métier partirait chez Supabase. C'est une écriture en production : accord obligatoire.
- Ma préférence, pour qu'il en juge : **B**, parce qu'elle garde la source et ne dépend pas de la nuit.

### D2 — « Changer le métier » l'écrit-il aussi chez Hektor ?

Les faits : le geste existe déjà techniquement (le worker envoie `metier` en modification). Mais Hektor n'a ni
« Courtier » ni « Parrain », et l'app ne sait pas retirer un métier chez lui.
- **A — chez nous seulement.** Hektor garde ce qu'il a. Aucun risque d'écrasement.
- **B — chez nous, et chez Hektor quand le métier existe dans sa liste** (banque, diagnostiqueur, syndic, apporteur,
  administration…) ; courtier et parrain restent chez nous seuls.
- **C — chez nous, et chez Hektor toujours**, avec une correspondance approchée (courtier → Banque, parrain → Apporteur).
  ⚠ Ce serait écrire une information fausse chez Hektor.
- Ma préférence : **B**. C est déconseillée.

### D3 — Lequel des quatre liens neufs d'abord

Au premier jour, chaque bloc de métier est VIDE : il se remplit au fil des gestes.
- **courtier ↔ acquéreur** : s'appuie sur les conditions de prêt et leurs échéances, qui existent déjà ; 82 courtiers
  et banques dans Netty ;
- **diagnostiqueur ↔ bien** : s'appuie sur les DPE des biens ; 30 dans Netty ;
- **apporteur ↔ affaire** : touche une commission à régler ; 60 apporteurs et parrains dans Netty, 53 liens historiques ;
- **syndic ↔ bien** : s'appuie sur les champs de copropriété (statut du syndicat sur 494 annonces) ; nombre de syndics
  inconnu.
- Je n'ai pas de préférence fondée sur une mesure : la question est commerciale (lequel sert le plus au quotidien).

### D4 — Les demandes d'estimation (673) et les candidats (332) rangés « partenaire »

- **A — ils restent dans « À classer »**, avec un bouton vers les leads et vers le recrutement (planche 7, telle qu'elle est).
- **B — l'annuaire les écarte à l'affichage**, sans rien écrire nulle part.
- **C — on les retype chez Hektor.** Écriture en masse chez Hektor : accord obligatoire, et les leads (A.5) sont à
  l'étape 3.
- Ma préférence : **B**, réversible et sans écriture.

### Les petites décisions de la maquette

- **P1** — une fiche archivée est-elle en LECTURE SEULE ? (planche 9 ; §69 point 7)
- **P2** — la fenêtre unique : la suppression garde-t-elle le texte à taper `SUPPRIMER CONTACT <numéro>` ? La maquette
  le garde (planche 9).
- **P3** — les 7 filtres de l'activité restent-ils tous (dont « Annonce » et « Rapprochements », rares pour un
  partenaire) ? La maquette les garde, pour ne rien perdre.
- **P4** — le menu « ⋯ » de la fiche CLIENT perd-il aussi Archiver et Supprimer ? La maquette ne touche qu'aux pages
  partenaire.

## 6. ⛔ RETOUR DE FRÉDÉRIC (04/11) : LA MAQUETTE EST REFUSÉE

> « NON, j'ai besoin d'un design à la hauteur de mon app. Il faut des fonctions adaptées aux métiers, mais il faut
> aussi réfléchir où les récupérer et comment les intégrer à l'existant, afin de lier les partenaires aux contacts ou
> annonces. »

Ce que ça veut dire, et ce qui change :
- **Le design** : les dix planches étaient un dessin À PART (une autre mise en page, d'autres cartes). Le design de l'app
  existe déjà : la fiche notaire v3 (`maquettes/fiche-notaire-v3.html`, mise en production le 28/10) et la fiche contact
  v30 (`maquettes/detail-contact-v30-dashboard.html`) — volet gauche, quatre chiffres à liseré, une section principale
  dépliable, une colonne « À venir », avec la police bienvu. ⇒ Une page partenaire doit être **cette fiche-là, déclinée
  par métier**, pas une page neuve.
- **L'intégration** : un partenaire ne vaut que par ses LIENS. Ils doivent se poser là où l'on travaille déjà (la fiche
  annonce, la fiche d'une affaire, la fiche d'un client), et la page du partenaire ne fait que les relire. C'est
  exactement le chemin du notaire.

### 6.1 Ce que l'audit complémentaire a trouvé (04/11, lecture seule)

- ⭐⭐ **Hektor A un lien annonce ↔ syndic et annonce ↔ diagnostiqueur.** La page console de l'annonce porte deux listes
  « Contacts » : `diagnostiqueur` et `syndic` (`diagnostics_contacts_console_json`). Leur valeur est un NUMÉRO DE CONTACT
  Hektor (vérifié : 6 chiffres + un libellé). ⚠ Cela corrige le §69 de la synthèse (« Hektor ne porte aucune donnée de
  métier »). Mais :
  - ce bloc n'est lu que pour **97 annonces sur 13 525** (le bloc console, comme au chantier ⑧) ; 1 seule a un syndic,
    0 un diagnostiqueur. Le taux réel sur le parc est **non mesuré** ;
  - ⚠ **défaut dormant** : l'assistant d'annonce de l'app a les champs « Diagnostiqueur » et « Syndic » (`App.tsx` 1626),
    et le worker les envoie comme du TEXTE (`setWizardTextIfPresent`, `console_job_worker.js` 11480-11482 ; « texte
    libre (nom du syndic) », `App.tsx` 10952). Hektor attend un numéro de contact. Mesure : **0 saisie** dans l'app à ce
    jour. Rien n'est donc perdu, mais le champ ne peut pas marcher tel qu'il est ;
  - la fiche annonce en production (`CockpitDetail`) ne les montre pas ; seules l'ancienne fiche et la fiche téléphone
    les affichent (`App.tsx` 35794, 39862).
- **Copropriété** : 731 annonces sont « copropriété : OUI » (détail lu) ; le statut du syndicat est sur 494.
- **Documents** : 16 292 documents ont un nom de diagnostic (DPE, amiante, Carrez…), 1 168 un nom de copropriété
  (pré-état daté, PV d'AG, règlement), 3 176 un nom de prêt ou de financement. Certains noms portent le logiciel ou
  l'entreprise du diagnostiqueur. Le contenu des PDF n'est pas lu (non mesuré).
- **Netty, les affaires** (`affairs_contacts_relations.xlsx`, 50 202 liens) : vendeur 20 085, acquéreur 15 831, notaire
  du vendeur 10 233, notaire de l'acquéreur 4 000, **apporteur 53** (43 côté vendeur, 10 côté acquéreur). Aucun lien
  banque, courtier, syndic ou diagnostiqueur.
- **Netty, le métier** : la session du chantier ⑧ l'a déjà rangé (§70-71 de la synthèse, commit 35fb26e) : table locale
  `contact_metier_netty` sur le serveur, 941 fiches (notaire 844, apporteur 35, courtier 22, diagnostiqueur 16,
  parrain 15, banque 8, administration 7…), sans aucun nom. Et les 260 partenaires entrent dans l'app à partir de la nuit
  du 04/11 (`APP_PERIMETRE_REGISTRE=1`). ⇒ **D1 a déjà un début de réponse côté serveur** ; il reste à le monter chez
  Supabase et à le confirmer à l'écran.
- **Les commissions** de Hektor (`intervenants_json`) ne portent que des négociateurs et des agences : aucun apporteur.
- **Le chemin du notaire, le modèle à suivre** : un notaire est une PARTIE d'une affaire (`app_affaire_partie`, rôles
  `notaire_vendeur` / `notaire_acquereur`) ; l'annuaire en tire le type Notaire, et la fiche notaire relit ses dossiers.
  Les liens d'un bien vivent dans `app_relation` (mandant, propriétaire), qui accepte déjà un lien posé par l'app.

### 6.2 La carte d'intégration proposée (rien n'est décidé)

Où le lien se pose, d'où il vient, et ce que la page du partenaire en relit :
- **Syndic ↔ bien** — se pose sur la **fiche annonce**, dans un bloc « Intervenants du bien » (visible si copropriété).
  Sources : la liste `syndic` de Hektor (numéro de contact), puis la saisie dans l'app. Rangé dans `app_relation`, rôle
  `syndic`. La page du syndic relit : ses copropriétés, ses biens en vente, les documents de copropriété, les demandes.
- **Diagnostiqueur ↔ bien** — même bloc de la fiche annonce. Sources : la liste `diagnostiqueur` de Hektor, puis la
  saisie, et une proposition tirée du nom des documents. Rangé dans `app_relation`, rôle `diagnostiqueur`. La page relit :
  les biens diagnostiqués, les DPE (classe, date, échéance), les documents déposés.
- **Courtier ou banque ↔ acquéreur, dans une affaire** — se pose sur la **fiche de l'affaire** (registre des
  transactions), à côté des notaires, et se lit sur la fiche du client acheteur (« son financement »). Source : la saisie
  seulement (ni Hektor ni Netty ne l'ont). Rangé dans `app_affaire_partie`, rôle `courtier` ou `banque`. La page relit :
  les acquéreurs suivis, leurs conditions de prêt et leurs échéances (elles existent déjà, `app_affaire_condition`).
- **Apporteur ou parrain ↔ affaire** — se pose sur la **fiche de l'affaire**, et sur la fiche annonce dès le mandat
  (« apporté par »). Sources : les 53 liens de Netty (à rapprocher des affaires de Hektor, non mesuré), puis la saisie.
  Rangé dans `app_affaire_partie`, rôle `apporteur`. La page relit : les affaires apportées, leur état, la commission due.
- **Le choix du partenaire**, partout : le MÊME moteur de recherche que le mandant, l'acquéreur et le notaire
  (`searchMandantContactOptions`), filtré par métier quand le métier est connu.
- **L'annuaire** : le métier vient des rôles (comme le notaire) ET de la table du métier (Netty, puis l'écran).

⚠ Ce que ça pourrait casser ailleurs, à vérifier avant tout code :
- `app_affaire_partie` est CALCULÉE (`calcule_le`, `origine`) : une ligne posée par l'app doit survivre au recalcul
  (non vérifié) ;
- `app_relation` : un rôle neuf ne doit pas être lu comme un mandant ou un propriétaire par les écrans qui comptent
  les mandants, ni partir chez Hektor par le push des relations (non vérifié) ;
- écrire le syndic ou le diagnostiqueur chez Hektor demande le NUMÉRO du contact, pas son nom (le défaut dormant).

### 6.3 Le design refait sur la vraie fiche (04/11, « Oui, redessine ») — rien n'est codé

Quatre fichiers, sous `maquettes/` (servis par la configuration « maquettes », port 8099), données FICTIVES. Chacun a le
bouton « Origine des données » : il dit, bloc par bloc, ce qui existe déjà et ce qui naît d'un lien neuf.
- **`fiche-partenaire-v1.html`** : la fiche notaire v3 (feuille de la fiche contact en production, recopiée telle
  quelle), déclinée en quatre métiers par un sélecteur en bas (`?m=courtier|diag|syndic|apporteur`). Même squelette :
  volet gauche (identité, action propre au métier en magenta, coordonnées, interlocuteurs, négociateur, statut, MÉTIER et
  sa source), quatre chiffres, la section du métier dépliable avec ses étapes et ses pièces, « À venir », deux blocs
  « avec nous », l'activité, la qualité repliée, la zone sensible (Archiver, Supprimer) tout en bas.
  - courtier ou banque : acquéreurs suivis (orientés → accord de principe → offre de prêt → financés), pièces du
    financement, conditions de prêt (registre), banques de ses dossiers ;
  - diagnostiqueur : commandes et biens (commandé → RDV → rapport → au coffre), diagnostics attendus, DPE qui expirent,
    classes énergie de ses biens ;
  - syndic : copropriétés (lots, charges, statut du syndicat : fiche du bien), documents de copropriété, demandes et
    délais (pré-état daté), assemblées générales ;
  - apporteur ou parrain : affaires apportées (contact → mandat → commission due → réglée), commission convenue, pièces
    (convention, facture, règlement).
- **`accroche-annonce-v1.html`** : la fenêtre « Contacts du bien » de l'annonce (maquette v34, celle que la fiche
  annonce en production a reprise), dont le bloc devient « Intervenants du bien » : diagnostiqueur, syndic (avec le
  sélecteur ouvert, filtré sur les syndics, qui propose d'abord le syndic des autres biens à la même adresse), les deux
  notaires (registre), « Apporté par » (lien neuf), et le financement de l'acquéreur, relu depuis l'affaire.
- **`accroche-affaire-v1.html`** : les parties d'une affaire, côté vendeur et côté acquéreur ; l'apporteur (avec sa
  commission) et le financement (courtier, banque prêteuse, montant) à côté des notaires ; la condition de prêt avec
  « Prévenir le courtier ». ⚠ Dessinée dans la fenêtre de la v34 : à caler sur la fiche du registre (v4) au moment du code.
- **`accroche-client-v1.html`** : la fiche contact d'un acheteur, avec un bloc « Ses partenaires » dans le volet gauche
  (son courtier et l'échéance du prêt, son notaire, « Indiquer qui l'a apporté ») ; la fiche RELIT les liens, rien d'autre
  n'y change.

⭐ **Trouvé en dessinant — le point d'accroche existe déjà, et il est mort.** La rubrique Contacts de la fiche annonce en
production (`CockpitDetail`, `App.tsx` 34422-34458) a un bloc « Diagnostics et syndic ». Il lit `intervenants_json`,
une clé qu'AUCUNE annonce n'a (0 sur 13 525, mesuré le 04/11) : il ne s'affiche donc jamais. Ses boutons
« ＋ Ajouter un syndic » et « Fiche » n'ont aucune action. ⇒ Le code le plus naturel est de le RANIMER (le nourrir des
listes `syndic` et `diagnostiqueur` de Hektor, des notaires du registre et des liens neufs), pas d'en écrire un autre.

Contrôlé : bureau 1440 × 900, écran bas 1280 × 665, téléphone 390 × 844 (aucun débordement de la page).
La maquette Design des dix planches (https://claude.ai/artifact/Y7xzFasspGEyAX14v4v838) est remplacée par ces fichiers.

## 6 bis. ⭐⭐ AUDIT DES SYNDICS — FRÉDÉRIC AVAIT RAISON *(04/11, « j'ai un doute, nous devrions avoir plus de fiches syndic » ; lecture seule : Supabase, base du serveur, classeur Netty, et Hektor dans son Chrome)*

**Audit limité aux partenaires (syndic et diagnostiqueur surtout).** Les autres objets ne sont pas mesurés ici.

Ce que NOS données disent (et pourquoi elles trompent) :
- Supabase : 7 fiches seulement portent le mot « syndic » (sur 94 741).
- Base du serveur (tous les contacts de Hektor, 356 824) : 42 portent le mot.
- Netty : 9 fiches, rangées « Autre » ou sans type (Netty n'a pas de code syndic).
- Le détail des annonces : 1 syndic sur les 97 annonces dont on lit le bloc console.
⇒ On cherchait par le NOM. Or les fiches syndic de Hektor ne disent presque jamais « syndic » dans leur nom (2 sur 75).

Ce que HEKTOR dit (lu en direct, requêtes GET, sous le frein, aucune écriture) :
- **La liste « syndic » d'une annonce propose 75 contacts, et la liste « diagnostiqueur » 21.** Ce sont exactement les
  contacts dont le MÉTIER est Syndic (code 5) ou Diagnostiqueur (code 4) : vérifié sur trois fiches, par leur formulaire.
  ⇒ **Une seule lecture par liste donne tous les syndics et tous les diagnostiqueurs de Hektor.**
- **Les 75 syndics** : tous actifs, tous de typologie « partenaire », créés de novembre 2025 à ce mois-ci (73 en 2026), dans
  toutes les agences (Saint-Étienne 18, Firminy 10, Courpière 6…). Presque tous SANS coordonnées (3 e-mails, 1 téléphone).
  ⛔ **Aucun n'est dans l'app** (aucune raison d'y entrer : pas de lien à un bien chez nous, pas dans Netty). Les
  diagnostiqueurs : 21, dont 1 seul dans l'app.
- **Échantillon des 40 annonces en copropriété les plus récentes** : **17 ont un syndic chez Hektor (42 %)**, 0 un
  diagnostiqueur. 11 syndics différents, certains sur 3 biens. Sur les 731 biens en copropriété, cela ferait de l'ordre
  de 300 biens avec un syndic (extrapolation d'un échantillon récent : à mesurer en entier).
- Les négociateurs remplissent donc le syndic DANS HEKTOR, en créant au besoin une fiche réduite à un nom. L'app n'en voit
  rien : elle ne lit ce bloc que pour 97 annonces, et ne fait pas entrer ces fiches.
- Les partenaires créés chez Hektor depuis la migration (numéros ≥ 601 900) : 266, dont 122 hors de l'app. Leur métier se
  lit dans leur formulaire, une requête par fiche (~266 requêtes, une nuit).
- Remarque : le menu de l'administration Hektor affichait « Une erreur est survenue » pendant l'audit (l'interface, pas
  les requêtes, qui ont toutes répondu 200).

### Les recommandations qui en découlent (pour les décisions du §5 et du §7 bis)

- **D1 — où vit le métier : une petite table à part**, nourrie par TROIS sources, chacune notée : Netty (941, déjà sur le
  serveur), les deux listes de Hektor (75 syndics, 21 diagnostiqueurs, 2 lectures), et le formulaire des 266 partenaires
  créés depuis la migration (~266 lectures, une nuit). Puis l'écran (« Changer le métier »).
- **Faire ENTRER ces partenaires dans l'app** : une raison d'envoi de plus, « partenaire au métier connu », sur le
  modèle de `partenaire_netty` (§71 de la synthèse, chantier ⑧). ⚠ C'est le périmètre de nuit du chantier ⑧ : à faire
  avec lui, et avec ton accord.
  ⚠ Précision du 04/11 : le chantier ⑧ a déjà fait entrer les **partenaires de NETTY** (260, raison `partenaire_netty`,
  §73-74 de la synthèse). Cela ne couvre PAS ceux-ci : **0 des 75 syndics et 0 des 21 diagnostiqueurs de Hektor sont
  dans `contact_metier_netty`**, et je les ai mesurés hors de l'app APRÈS cet envoi. La recommandation 2 ne porte donc
  que sur les partenaires connus par HEKTOR (75 syndics, 20 diagnostiqueurs, et les partenaires créés depuis la
  migration dont le métier se lit dans leur formulaire).
- **D2 — « Changer le métier » écrit aussi chez Hektor quand Hektor a ce métier.** C'est maintenant nécessaire, pas
  seulement utile : la liste « syndic » d'une annonce chez Hektor ne propose QUE les contacts de métier Syndic. Un syndic
  que l'app connaît mais que Hektor ne range pas en Syndic ne pourrait pas être posé sur l'annonce chez Hektor.
- **Les liens syndic et diagnostiqueur : chez nous, puis chez Hektor, ET relus chaque nuit depuis Hektor.** Les
  négociateurs travaillent déjà dans Hektor (17 biens sur 40) : l'app doit d'abord LIRE ce qui existe (balayage de
  ~13 500 annonces, ou seulement les 731 en copropriété en premier), puis écrire par numéro de contact.
- **D3 — commencer par le SYNDIC**, puis le diagnostiqueur. C'est le seul métier qui a déjà des données vivantes (75
  fiches, des centaines de biens), un bloc d'écran qui existe (mort), et le même mécanisme servira tel quel au
  diagnostiqueur. Le courtier et l'apporteur n'ont de données nulle part : tout y naîtra de la saisie.

### ✅ D2 TRANCHÉE PAR FRÉDÉRIC (04/11) : RIEN NE PART CHEZ HEKTOR

> « Ce n'est pas nécessaire de communiquer les contacts métiers créés dans l'app à Hektor, donc c'est plus simple. »

- Le MÉTIER et les LIENS (syndic, diagnostiqueur, courtier, banque, apporteur) vivent **chez nous seulement**. Aucune
  écriture vers Hektor pour ce chantier.
- Ma recommandation n° 3 (écrire chez Hektor) tombe. On garde le sens inverse, qui n'écrit rien : **LIRE** chez Hektor ce
  que les négociateurs y ont mis (les 75 syndics, les 21 diagnostiqueurs, les syndics des annonces), tant qu'ils y
  travaillent.
- Conséquences sur les mini-chantiers du §7 :
  - **A4 FERMÉ par décision** (envoyer le métier chez Hektor) ;
  - **B5 REMPLACÉ** : on n'écrit plus le syndic chez Hektor. À la place, l'assistant d'annonce doit CESSER d'envoyer
    « Diagnostiqueur » et « Syndic » en texte à Hektor (ça ne peut pas marcher), et poser le lien chez nous ;
  - **0.6 devient inutile** (le format attendu par la liste de Hektor ne sert qu'à écrire) ;
  - B6 (lire les listes de Hektor) est GARDÉ.
- ⚠ Une précision à confirmer : un partenaire CRÉÉ dans l'app passe aujourd'hui par Hektor comme tout contact
  (`create_hektor_contact`), et le formulaire envoie même son métier. Ma recommandation : **ne rien changer à la
  création** (le chemin existe et il est prouvé), et ne simplement rien envoyer de plus ensuite. Faire naître un contact
  sans numéro Hektor serait un autre chantier.

### ✅ RECOMMANDATIONS 1, 2 ET 3 VALIDÉES PAR FRÉDÉRIC (04/11) — « 1 oui petite table, 2 oui, 3 oui »

- **D1 tranchée** : le métier vit dans une PETITE TABLE À PART chez Supabase (le contact, le métier, sa source, qui l'a
  confirmé et quand). Sources : Netty (`contact_metier_netty`, 941), les deux listes de Hektor (75 syndics,
  21 diagnostiqueurs), le formulaire des partenaires créés depuis la migration, puis l'écran.
- **Entrée dans l'app des partenaires connus par Hektor** (75 syndics, 20 diagnostiqueurs hors app, partenaires créés
  depuis la migration) : **oui**. ⚠ C'est l'étape de nuit du chantier ⑧ (`elargir_perimetre_registre.py`) : à
  coordonner avec lui, et chaque écriture en production reste soumise à son accord, geste par geste.
- **D3 tranchée** : le **SYNDIC d'abord**, puis le diagnostiqueur. L'ordre du courtier et de l'apporteur reste à fixer.

### ⚠ LA QUESTION DE FRÉDÉRIC : « quand avons-nous testé les gestes des contacts sur des fiches partenaires chez Hektor ? Jamais, je crois »

**Il a raison : JAMAIS.** Mesuré le 04/11 dans le journal des travaux (`app_console_job`, depuis le 29/05) :
- **création** : 35 travaux, tous des propriétaires (20) ou des acquéreurs (14), 1 sans type ; **0 partenaire, 0 métier
  envoyé** ;
- **modification** : 28 travaux, **0 sur une fiche partenaire**, 0 avec un métier ;
- **archivage** : 3 travaux (Gladys DURIEUX, 16/10), **0 partenaire** ;
- **suppression** : 35 travaux, **0 partenaire** sur les 24 qui gardent une photo de la fiche ; les 11 autres ne sont pas
  vérifiables (pas de photo, fiche disparue) ;
- seules des RELECTURES ont touché des partenaires (48 « refresh », lecture seule).
⇒ Tout ce que la note dit des gestes sur un partenaire vient de la LECTURE DU CODE, pas d'un essai. En particulier :
« une modification garde le métier » (le worker relit le formulaire), la création d'une PERSONNE MORALE (raison sociale,
forme juridique, SIRET), l'archivage et la suppression d'un partenaire : **non éprouvés**.
⇒ Nouveau mini-chantier **0.7** (§7).

### ⭐⭐⭐ DÉCISION DE FRÉDÉRIC (04/11) : UN REGISTRE DES PARTENAIRES AUTONOME

> « Il n'y a pas d'intérêt [à éprouver les gestes chez Hektor]. On ne peut pas avoir un registre des partenaires
> indépendant ? » — « Indépendant de Hektor, mais utile à notre app et lu par elle, bien sûr. » — « Avec tous les
> gestes, mais sans les envoyer à Hektor. »

**Ce que ça veut dire**
- Les partenaires (syndics, diagnostiqueurs, courtiers, banques, apporteurs, parrains, administrations…) vivent dans
  **notre propre registre**, avec NOTRE numéro. Ils ne sont ni créés, ni modifiés, ni archivés, ni supprimés chez Hektor.
  Tous les gestes se font chez nous, à l'instant, sans worker ni travail chez Hektor.
- Les **liens** (partenaire ↔ bien, partenaire ↔ affaire, partenaire ↔ client) vivent dans une table de liens du
  registre, PAS dans `app_relation` ni dans `app_affaire_partie` (deux tables qui reflètent Hektor, dont une recalculée).
- L'app LIT le registre partout : la page partenaire (design validé, inchangé), le bloc « Intervenants du bien » de
  l'annonce, la fiche de l'affaire, la fiche du client, l'annuaire.
- **Les notaires ne changent pas** : ils restent des contacts de Hektor, parties des affaires, avec leur fiche du 28/10.
- Modèle déjà présent dans le projet : `app_notaire_interlocuteur` (des fiches qui ne vivent que chez nous, avec
  `ecrit_le / ecrit_par / retire_le / retire_par`).
- ⭐ Argument mesuré : `app_contact_current` est RÉÉCRITE chaque nuit (suppression puis réinsertion,
  `build_contacts_layer.py` l. 1281). Un registre à part n'est pas touché par la nuit.

**Le premier remplissage (une REPRISE, une seule fois, puis le registre est maître)**
- les 75 syndics et les 21 diagnostiqueurs des listes de Hektor ;
- les ~97 professionnels de Netty hors notaires (`contact_metier_netty`) ;
- les partenaires créés chez Hektor depuis la migration, dont on lit le métier ;
- chaque fiche reprise garde son numéro Hektor ou Netty D'ORIGINE, pour mémoire et pour éviter les doubles ;
- les liens annonce ↔ syndic déjà posés dans Hektor (17 annonces en copropriété sur 40 dans l'échantillon).

**Ce que ça change dans le chantier**
- **0.1, 0.2, 0.6, 0.7 deviennent inutiles** (plus de rôle neuf dans les tables de Hektor, plus d'écriture chez Hektor,
  plus de geste à éprouver chez lui) ;
- **D1** : le métier est une colonne du registre lui-même (la « petite table » devient le registre) ;
- **A4, B5 (ancien), B6 (balayage de nuit)** : remplacés par la reprise ci-dessus ; un éventuel rafraîchissement
  depuis Hektor est une question ouverte (Q3) ;
- **la recommandation 2** (faire entrer ces contacts de Hektor dans l'app par l'étape de nuit du chantier ⑧) **tombe** :
  ils entrent dans le REGISTRE, par la reprise ;
- l'assistant d'annonce : ses champs « Diagnostiqueur » et « Syndic » cessent d'aller chez Hektor et posent le lien dans
  le registre.

**Ce que ça pourrait casser ailleurs, à vérifier au moment du code**
- un même syndic peut exister deux fois : une fiche contact « partenaire » dans le miroir de Hektor (annuaire des
  contacts) et une fiche dans notre registre. Le numéro d'origine les relie ; l'annuaire des partenaires lit le registre ;
- un négociateur qui travaille encore dans Hektor ne verra pas les partenaires créés dans l'app (accepté : D2) ;
- un partenaire qui est AUSSI client (rare) aurait deux fiches : un lien optionnel entre les deux.

**Question ouverte Q3** : la reprise depuis Hektor (fiches et liens aux annonces) se fait-elle UNE FOIS, ou la nuit
relit-elle Hektor tant que des négociateurs y saisissent des syndics ?

**Ce que fait la nuit aujourd'hui (mesuré le 04/11, pour répondre à la question de Frédéric avant Q3)**
- **Vers le serveur** : la nuit lit chaque nuit les contacts de Hektor nouveaux ou retraités (`sync_raw.py`, liste triée
  par `dateLastTraitement`). Preuve : les 2 syndics créés chez Hektor en NOVEMBRE sont déjà sur le serveur. ⚠ Une fiche
  modifiée sans que cette date bouge n'est pas relue (le cas des couples, mémoire du 03/11).
- **Vers Supabase** : la nuit n'envoie QUE les contacts qui ont une raison d'entrer (`supabase_sync_eligible`), et seulement
  ceux qui ont changé (empreinte par fiche, `app_contact_supabase_push_state`). Les raisons sont RECALCULÉES CHAQUE NUIT,
  dont `registre_relation` et `partenaire_netty` (`elargir_perimetre_registre.py`, allumé). Le rattrapage de 13:56
  n'était qu'une avance sur la nuit : la suite se fait toute seule.
- **Les partenaires** : seuls ceux appariés à Netty ont une raison. Les 75 syndics et 20 des 21 diagnostiqueurs de Hektor
  n'en ont aucune : ils sont sur le serveur, mais n'iront jamais dans l'app, ni cette nuit ni les suivantes. Un syndic
  créé demain chez Hektor arrivera sur le serveur, pas dans l'app.

**Recommandation pour Q3 (à décider par Frédéric)**
- **les FICHES syndic et diagnostiqueur : relues chaque nuit.** Une seule lecture par liste donne tous les syndics
  (resp. diagnostiqueurs) de Hektor : 2 requêtes par nuit. Un syndic créé par un négociateur dans Hektor entre dans le
  registre le lendemain, avec son numéro d'origine (jamais en double).
- **les LIENS annonce ↔ syndic : une reprise complète une fois** (les 731 biens en copropriété, ~731 lectures étalées
  sous le frein), **puis chaque nuit seulement les annonces relues par la nuit** (celles dont Hektor a bougé). Non mesuré :
  si poser un syndic chez Hektor fait bouger la date de l'annonce.
- **rien ne repart chez Hektor** (D2). Si un lien diffère entre Hektor et le registre, le registre gagne et l'écart est
  signalé, jamais écrasé en silence.

**La proposition de Frédéric (04/11) : « Donc on change juste "ou être un partenaire connu de Netty". »**
- Lecture : élargir la raison d'entrée `partenaire_netty` en **« partenaire au métier connu », de Netty OU de Hektor**.
  L'étape de nuit existe et tourne déjà (`elargir_perimetre_registre.py`, chantier ⑧) : c'est une ligne de règle de plus.
- Ce qu'il faut en plus : la SOURCE du métier Hektor sur le serveur. Une petite étape de nuit lit les deux listes de Hektor
  (2 requêtes) et range numéro + métier dans une table locale, comme `contact_metier_netty`. Plus tard, le formulaire des
  partenaires créés depuis la migration (lecture, ~266 requêtes une fois).
- Effet : les 75 syndics et les 20 diagnostiqueurs entrent dans l'app la nuit suivante, puis tout nouveau syndic créé chez
  Hektor le lendemain de sa création ; ils sont tenus à jour par la nuit comme tout contact.
- ⚠ Conséquence sur le registre autonome : les partenaires de Hektor deviennent des CONTACTS de l'app (le miroir), et le
  registre se pose PAR-DESSUS, rattaché par le numéro du contact (métier, liens, gestes de l'app, rien n'est envoyé à
  Hektor). Il n'y a plus de reprise séparée ni de doublon contact / fiche du registre. Seul un partenaire CRÉÉ dans l'app
  n'a pas de contact Hektor : il vit dans le registre seul. ⇒ à confirmer par Frédéric (forme « A »).
- Coordination : le fichier est celui du chantier ⑧.

### ✅ D4 TRANCHÉE (04/11) : « A, mais normalement ils ne devraient pas être dans l'app »

- **Décision A** : l'annuaire des partenaires les écarte ; rien n'est modifié nulle part.
- **Mesuré (classeur Netty → numéro Hektor → serveur)** : il a raison, ils n'y sont presque pas.
  - demandes d'estimation (code 82) : 1 046 retrouvées ; **838 rangées « partenaire » chez Hektor sont HORS de l'app**, 17
    seulement y sont ; 115 autres sont dans l'app sous un autre type (des propriétaires devenus clients) ;
  - candidats (code 85) : 416 retrouvés ; **351 « partenaire » hors de l'app**, 10 dedans.
  - Ceux qui sont dans l'app y sont pour une vraie raison : lien à un bien, registre, transaction, recherche. Seuls 7
    sont entrés par `partenaire_netty` : leur fiche Netty porte AUSSI un code professionnel.
- ⇒ Dans la forme retenue, l'annuaire des partenaires est tiré du MÉTIER, pas de la typologie « partenaire » de Hektor :
  ces fiches n'y apparaissent donc pas, sans aucun filtre à écrire.

### ✅ P1 TRANCHÉE (04/11) : « B » — une fiche partenaire archivée reste modifiable

- Tout reste possible sur une fiche archivée (modifier, RDV, écrire, commander, demander), comme aujourd'hui. Seul un
  bandeau dit qu'elle est archivée, avec « Réactiver ». La planche 9 de l'ancienne maquette (lecture seule) ne s'applique pas.

### ✅ P2 TRANCHÉE (04/11) : « B » — supprimer un partenaire : une case à cocher et la raison

- Plus de texte à taper (`SUPPRIMER CONTACT <numéro>`). La fenêtre de confirmation demande : une case « je comprends que
  c'est définitif » ET la raison (gardée au journal des suppressions). Le geste lui-même ne change pas (Hektor puis chez
  nous, administrateur et manager). Sur la fiche partenaire ; pour la fiche client, voir P4.

### ✅ P4 TRANCHÉE (04/11) : « B » — la fiche CLIENT ne change pas

- Archiver et Supprimer restent dans le menu « ⋯ » de la fiche client, avec leurs confirmations actuelles (texte à taper
  pour supprimer). Seule la page PARTENAIRE a la zone sensible en bas, la fenêtre commune et la case à cocher.

### ✅ Q1 TRANCHÉE (04/11) : « A » — un partenaire se relie à un CLIENT dès le premier jour

- On peut relier un apporteur (« Apporté par ») ou un courtier (« Son courtier ») à un client AVANT tout mandat ou toute
  affaire, depuis la fiche du client. Le lien suit ensuite le mandat puis l'affaire quand ils naissent. Les étapes
  « Contact apporté » (apporteur) et « Orientés » (courtier) existent.
- Exemples donnés à Frédéric : Julien Morel apporte les Chazal le 3 mars, mandat le 2 avril, vente le 12 octobre,
  commission de 1 200 € ; M. Benali orienté vers Courtage Horizon le 15 septembre, offre le 20 octobre.
- ⇒ Le mini-chantier **B4** (lien partenaire ↔ client sans affaire) est retenu.

### ✅ Q2 TRANCHÉE (04/11) : « A » — la règle de validité du DPE est celle de la loi

- DPE réalisé AVANT le 01/01/2018 : plus valable ; entre le 01/01/2018 et le 30/06/2021 : plus valable depuis le
  01/01/2025 ; DEPUIS le 01/07/2021 : valable 10 ans. (Règle donnée de mémoire, à revérifier sur le texte officiel au
  moment du code, mini-chantier F3.)
- Elle nourrit « DPE qui expire » et « mandat sans DPE valable » (page diagnostiqueur, fiche annonce).

### ✅ Q3 TRANCHÉE (04/11) : « A » — les syndics posés chez Hektor : reprise complète une fois, puis suivi chaque nuit

- Une reprise des 731 annonces en copropriété (~731 lectures sous le frein, une ou deux nuits), puis chaque nuit les
  seules annonces que la nuit relit déjà. Rien ne part chez Hektor ; en cas d'écart, l'app gagne et l'écart est signalé.
- ⚠ À mesurer AVANT de coder : poser un syndic chez Hektor fait-il bouger la date de l'annonce ? Sinon le suivi de nuit
  raterait ces changements (même famille que « le run ne relit le détail que si la datemaj change »).

### ✅ LA FORME RETENUE PAR FRÉDÉRIC (04/11, « on part sur 1 ») — elle remplace le « registre à fiches à part »

- **Tous les partenaires sont des CONTACTS de l'app**, quelle que soit leur origine :
  - ceux de Hektor (75 syndics, 21 diagnostiqueurs, partenaires créés depuis la migration) entrent par la nuit, avec la
    raison élargie « **partenaire au métier connu (Netty ou Hektor)** » ; ils sont tenus à jour chaque nuit comme tout
    contact ;
  - ceux de Netty y sont déjà (`partenaire_netty`, §73-74 de la synthèse) ;
  - un partenaire **créé dans l'app** est créé comme tout contact, **aussi chez Hektor** (chemin existant
    `create_hektor_contact`, prouvé). ⇒ **Seule la NAISSANCE de la fiche part chez Hektor.**
- **Le registre des partenaires se pose PAR-DESSUS les contacts**, rattaché par le numéro du contact. Il porte, chez nous
  seulement, sans rien envoyer à Hektor : le **métier** (et sa source), les **liens** (bien, affaire, client), les
  **commandes, demandes, financements et commissions**, et les **gestes** de l'app.
- Ainsi chaque partenaire profite de tout ce qui existe pour les contacts (RDV Google, e-mail, fil d'activité, recherche
  globale, annuaire, qualité de la fiche), sans doublon.
- ⚠ À régler au moment du code : la modification des COORDONNÉES d'un partenaire. Le geste « Modifier » d'un contact part
  aujourd'hui chez Hektor (`update_hektor_contact`). Deux voies : le laisser tel quel (c'est un contact comme un autre),
  ou garder la modification chez nous. À présenter à Frédéric avec le mini-chantier.
- Conséquences sur le §7 : **A1** = la table du métier, rattachée au contact ; **la raison élargie** et **la source
  Hektor du métier** (2 lectures par nuit + une lecture unique des partenaires créés depuis la migration) deviennent des
  mini-chantiers de la famille A ; les liens (famille B) vivent dans les tables du registre, PAS dans `app_relation` ni
  `app_affaire_partie` (0.1 et 0.2 restent donc inutiles) ; **0.7** (éprouver les gestes chez Hektor) revient pour la
  SEULE création d'un partenaire personne morale, jamais éprouvée.

## 7. LES MINI-CHANTIERS, FONCTION PAR FONCTION *(04/11, design validé ; rien n'est codé, l'ordre n'est PAS décidé)*

> Chaque mini-chantier suivra la méthode (`CLAUDE.md` §0) : audit, explication avec « ce que ça pourrait casser »,
> « vas-y », code derrière un interrupteur éteint, contrôle, documents. Une seule tâche en code à la fois.
> Légende de ce que chaque mini-chantier touche : **lecture** (aucune écriture) · **front** · **base** (écriture en
> production : accord obligatoire) · **worker** (redémarrage : accord) · **Hektor** (écriture chez Hektor : accord) ·
> **nuit** (le run de nuit).
> « Bloqué par » nomme la décision de Frédéric qu'il attend.

### 0. Les vérifications d'abord (lecture seule)

- **0.1** La table des parties (`app_affaire_partie`) est RECALCULÉE : prouver qu'une ligne posée par l'app survit au
  recalcul, ou écrire la règle qui la protège. Lire la fonction de calcul, essai dans une transaction annulée. *lecture*
- **0.2** Un rôle neuf dans `app_relation` (syndic, diagnostiqueur) : lister tous ses lecteurs (écrans, compteurs,
  `contactDirectoryCategories`, `loadAnnonceMandants`, le push des relations vers Hektor) et prouver qu'aucun ne le
  prendra pour un mandant ou un propriétaire, ni ne l'enverra chez Hektor. *lecture*
- **0.3** Mesurer, sur un échantillon, combien d'annonces ont un syndic ou un diagnostiqueur dans les listes de Hektor
  (aujourd'hui lu sur 97 annonces seulement). *lecture, mais des requêtes chez Hektor : à faire sous le frein*
- **0.4** Mesurer si les 53 apports de Netty se rapprochent des affaires de Hektor (classeur local, numéro de mandat). *lecture*
- **0.5** Lire la VRAIE fiche d'une affaire du registre (v4) pour caler l'accroche « affaire ». *lecture*
- **0.6** Lire comment la liste « syndic » de la page console de Hektor attend sa valeur (numéro de contact, liste des
  choix possibles, filtre par métier ?) avant d'écrire quoi que ce soit chez Hektor. *lecture*

- **0.7** ⭐ ÉPROUVER LES GESTES DE CONTACT SUR UNE FICHE PARTENAIRE, jamais faits (mesure du 04/11) : sur une fiche
  d'ESSAI que Frédéric choisit, créer un partenaire personne morale avec un métier, le modifier (le métier doit
  rester), l'archiver puis le réactiver, le supprimer ; vérifier chaque fois ce que Hektor a vraiment gardé (relire le
  formulaire), et le témoin inverse. *Hektor (écriture) : accord obligatoire, geste par geste.*

### A. Le métier

- **A1** Monter le métier chez Supabase : une table (le contact, le métier, sa source, qui l'a confirmé et quand),
  remplie depuis `contact_metier_netty` (941 fiches, déjà sur le serveur). *base* — **bloqué par D1**.
- **A2** Lire le métier dans l'app : le type d'écran par métier (couleur, icône), le filtre de l'annuaire. *front*
- **A3** Le geste « Changer le métier » (écran + écriture chez nous, trace de l'auteur). *front, base*
- ~~**A4**~~ ⛔ FERMÉ PAR DÉCISION (D2, 04/11). Envoyer le métier chez Hektor quand il existe dans sa liste (correspondance des codes ; ni courtier ni parrain
  chez lui). Le chemin existe déjà (`update_hektor_contact`, champ `metier`). *worker, Hektor* — **bloqué par D2**.
- **A5** Proposer un métier depuis un lien : un contact choisi comme syndic d'un bien devient « syndic » à confirmer. *front*
- **A6** « À classer » : trier les 16 098 « partenaires » qui n'en sont pas. *front, base* — **bloqué par D4**.

### B. Les liens (le socle de tout)

- **B1** Les rôles `syndic` et `diagnostiqueur` dans `app_relation`, avec la fonction qui pose et retire un lien (chez
  nous d'abord, trace de l'auteur, retrait daté, jamais de suppression). *base* — après 0.2.
- **B2** Les rôles `courtier`, `banque` et `apporteur` dans `app_affaire_partie`, avec la même fonction. *base* — après 0.1.
- **B3** Le sélecteur de partenaire : le moteur du mandant et du notaire (`searchMandantContactOptions`), filtré par
  métier, avec les propositions « même adresse » et « déjà lié à nos biens ». *front*
- **B4** Le lien courtier ↔ client SANS affaire (l'étape « Orientés ») et apporteur ↔ client SANS affaire (l'étape
  « Contact apporté »). *base, front* — **bloqué par la question Q1** (§7 bis).
- **B5** ⚠ REMPLACÉ (D2, 04/11) : l'assistant d'annonce cesse d'envoyer « Diagnostiqueur » et « Syndic » en texte à Hektor et pose le lien chez nous. *(Ancien libellé : écrire le syndic et le diagnostiqueur chez Hektor, par NUMÉRO de contact.)* Répare au passage le défaut dormant de
  l'assistant d'annonce (il envoie un nom en texte). *worker, Hektor* — après 0.6, **bloqué par D2**.
- **B6** Lire les listes syndic et diagnostiqueur de Hektor pour tout le parc : un balayage de nuit étalé (~13 500
  lectures, sur le modèle du balayage des photos), puis reprise dans `app_relation` avec l'origine « hektor ».
  *nuit, Hektor (lecture)* — après 0.3.
- **B7** Reprendre les 53 apports de Netty dans les parties, origine « netty ». *base* — après 0.4.

### C. Les points d'accroche (là où l'on pose les liens)

- **C1** La fiche annonce : ranimer le bloc « Diagnostics et syndic » de `CockpitDetail` (aujourd'hui jamais affiché),
  devenu « Intervenants du bien » : diagnostiqueur, syndic, les deux notaires (registre), « Apporté par », le financement
  relu depuis l'affaire ; boutons Choisir, Changer, Retirer, Fiche. *front* — après B1, B2, B3.
- **C2** La fiche d'une affaire (registre) : l'apporteur avec sa commission, le financement (courtier, banque, montant),
  « Prévenir le courtier » sur la condition de prêt. *front* — après 0.5, B2, E1, H1.
- **C3** La fiche du client : le bloc « Ses partenaires » (relecture) et « Indiquer qui l'a apporté ». *front* — après B2.
- **C4** Les trois accroches au téléphone (`MobileLayout`, `MobileDossierDetail`). *front*

### K. La page partenaire (commune aux quatre métiers)

- **K1** La page : le squelette de la fiche notaire, déclinée par métier (volet gauche, métier et sa source, quatre
  chiffres, section du métier, « À venir », blocs « avec nous », activité, qualité). *front* — après A2.
- **K2** Les interlocuteurs pour tous les métiers : généraliser `app_notaire_interlocuteur`, ou une table sœur.
  *base, front* — décision de forme à présenter.
- **K3** La zone sensible : Archiver et Supprimer à part, tout en bas, et la fenêtre unique de confirmation. *front* —
  **bloqué par P1, P2, P4**.
- **K4** Le menu « ⋯ » réduit (Modifier, Changer le métier, Ouvrir dans Hektor caché sans numéro). *front*
- **K5** Les états chargement / vide / erreur, distincts. *front*
- **K6** L'annuaire des partenaires : la liste par métier, les tuiles, la recherche (sur l'annuaire v2 existant). *front*
- **K7** La page au téléphone. *front*

### E. Courtier et banque

- **E1** Les champs du financement sur l'affaire : montant emprunté, apport, durée, banque prêteuse. *base, front*
- **E2** Le bloc « Acquéreurs suivis » et ses étapes, calculées depuis les parties, l'état de l'affaire et les conditions. *front*
- **E3** Les chiffres et « À venir » : les conditions de prêt (`app_affaire_condition`, existe), les RDV. *front*
- **E4** Les pièces du financement : rattacher et typer les documents d'une affaire. ⚠ Le même chantier sert la fiche
  notaire (ses « pièces du dossier » sont « en construction »). *base, front*
- **E5** « Envoyer le compromis au courtier » : la fenêtre d'e-mail existe ; y joindre les pièces du coffre. ⚠ Partagé
  avec le notaire. *front, peut-être backend*
- **E6** « Prévenir le courtier » depuis une condition de prêt : un e-mail prérempli. *front*
- **E7** Les blocs « Avec nous » et « Banques de ses dossiers » (calculs). *front*

### F. Diagnostiqueur

- **F1** La table des commandes (le bien, le diagnostiqueur, la date, le prix, les diagnostics demandés, l'état) et le geste
  « Commander un diagnostic » (e-mail et RDV, qui existent). *base, front*
- **F2** Le bloc « Commandes et biens » et ses étapes (commandé → RDV → rapport → au coffre). *front*
- **F3** Le DPE du bien (fiche du bien, existe), le calcul « DPE qui expire » et l'alerte « mandat sans DPE ». *front* —
  **bloqué par la règle de validité à fixer (Q2)**.
- **F4** Rattacher le rapport du coffre à la commande (proposition d'après le nom du fichier). *base, front*
- **F5** Les blocs « classes énergie » et « types de diagnostics ». *front*

### G. Syndic

- **G1** Regrouper les biens par immeuble (adresse normalisée) : c'est la « copropriété » de la page. Rien ne la porte
  aujourd'hui. *base ou calcul* — décision de forme à présenter.
- **G2** La table des demandes au syndic (pré-état daté, PV d'AG, règlement, carnet d'entretien, plan de travaux) et le
  geste « Demander un document », avec délai et relance. *base, front*
- **G3** Le bloc « Copropriétés » : lots, charges, statut (fiche du bien, existe) et documents du coffre (par leur nom). *front*
- **G4** Les assemblées générales (date saisie) dans « À venir ». *base, front*
- **G5** Les blocs « Nos biens dans ses copropriétés » et « Demandes et délais ». *front*

### H. Apporteur et parrain

- **H1** Les champs de la commission sur la partie « apporteur » : montant, échéance (à l'acte…), réglée le, mode. *base, front*
- **H2** Le bloc « Affaires apportées » et ses étapes (contact → mandat → commission due → réglée). *front* — l'étape
  « Contact apporté » dépend de **Q1**.
- **H3** Le geste « Marquer la commission réglée » et ses pièces (convention, facture, preuve). *base, front*
- **H4** « Noter une affaire apportée » depuis l'annonce, l'affaire ou le client (même lien que B2). *front*
- **H5** Les blocs « Ce qu'il nous apporte » et « Commissions ». *front*

### I. L'activité

- **I1** De nouveaux types d'événements dans le fil : commande, demande, commission, lien posé ou retiré. *base, front*

### 7 bis. Ce qui bloque, et qui revient à Frédéric

- ~~**D1**~~ ✅ tranchée le 04/11 : petite table à part (→ A1) · ~~**D2**~~ ✅ tranchée le 04/11 : rien ne part chez Hektor (A4 fermé, B5 remplacé) ·
  ~~**D3**~~ ✅ syndic d'abord, puis diagnostiqueur (G, puis F ; E et H à ordonner) · **D4** demandes d'estimation et candidats (→ A6) ;
- **P1** fiche archivée en lecture seule · **P2** le texte à taper pour supprimer · **P4** la fiche client perd-elle aussi
  Archiver et Supprimer de son menu (→ K3) ;
- **Q1** un lien partenaire ↔ client SANS affaire (étapes « Orientés » et « Contact apporté ») : on le crée, ou le
  partenaire n'apparaît qu'à partir de l'affaire (→ B4, H2) ;
- **Q2** la règle de validité d'un DPE à appliquer (→ F3) ;
- deux décisions de forme, à présenter le moment venu : les interlocuteurs (K2) et la copropriété (G1).

### 7 quater. LA LISTE RELUE AVEC LES DÉCISIONS DU 04/11 (elle prime sur les lignes ci-dessus)

- **Tombent** : 0.1 et 0.2 (les liens vivent dans les tables du registre, pas dans celles de Hektor) · 0.6 (rien n'est
  écrit chez Hektor) · A4 (le métier ne part pas chez Hektor) · A6 « À classer » (D4 : ces fiches ne sont pas dans
  l'annuaire des partenaires, qui se tire du métier) · B5 dans sa forme d'écriture.
- **Changent** :
  - A1 : la table du métier, rattachée au CONTACT (source Netty, Hektor, écran ; qui l'a confirmé et quand) ;
  - B1, B2 : les liens bien / affaire vivent dans une table de liens DU REGISTRE (rattachée au contact du partenaire) ;
  - B4 : RETENU (Q1) — le lien partenaire ↔ client sans affaire, qui suit le mandat puis l'affaire ;
  - B5 : l'assistant d'annonce cesse d'envoyer « Diagnostiqueur » et « Syndic » à Hektor et pose le lien dans le registre ;
  - B6 (Q3) : reprise des syndics des 731 annonces en copropriété, puis suivi de nuit ; après la mesure « la date de
    l'annonce bouge-t-elle ? » ;
  - K3 : sur la page PARTENAIRE seulement (P4) ; archivé reste modifiable (P1) ; supprimer = case à cocher + raison (P2) ;
  - F3 : règle légale du DPE (Q2), à revérifier sur le texte officiel.
- **S'ajoutent** :
  - **A7** une étape de nuit lit les listes « syndic » et « diagnostiqueur » de Hektor (2 lectures) et range numéro +
    métier sur le serveur, comme `contact_metier_netty` ; *nuit, Hektor (lecture)* ;
  - **A8** la raison d'entrée élargie « partenaire au métier connu (Netty OU Hektor) » dans
    `elargir_perimetre_registre.py` ; *nuit* — fichier du chantier ⑧, à coordonner ;
  - **A9** une lecture unique du métier des ~266 partenaires créés chez Hektor depuis la migration ; *Hektor (lecture)* ;
  - **0.7** (réduit) éprouver la CRÉATION d'un partenaire personne morale chez Hektor, jamais faite ; *Hektor (écriture),
    accord* ;
  - **0.8** mesurer si poser un syndic chez Hektor fait bouger la date de l'annonce (pour B6) ; *lecture* ;
  - **K8** la modification des coordonnées d'un partenaire : la laisser partir chez Hektor (comme tout contact) ou la garder
    chez nous — choix à présenter à Frédéric avec ce mini-chantier.
- **L'ordre des métiers** (D3) : G (syndic), puis F (diagnostiqueur) ; E (courtier) et H (apporteur) restent à ordonner.

## 8. LE PLAN DE RÉALISATION PAR LOTS *(04/11, « Oui, vas-y » au plan ; rien n'est codé)*

> Les règles, pour chaque lot : une seule tâche en code à la fois ; chaque tâche suit la méthode (`CLAUDE.md` §0 :
> audit, explication avec « ce que ça pourrait casser », « vas-y », code, contrôle, documents) ; tout est posé
> **derrière un interrupteur ÉTEINT** ; toute écriture en production (Supabase, Hektor, `.env`, allumage, redémarrage)
> demande l'accord de Frédéric, geste par geste ; contrôle sur trois formats (bureau, écran bas 1280 × 665, téléphone) ;
> stager fichier par fichier, Frédéric pousse.
> Les noms d'interrupteurs et de tables ci-dessous sont des PROPOSITIONS.

**Lot 0 — Mesurer avant de construire** *(lecture seule ; aucun code)*
- 0.3 compléter la mesure des syndics posés chez Hektor (échantillon déjà fait : 17 sur 40) ;
- 0.4 les 53 apports de Netty se rapprochent-ils des affaires de Hektor ;
- 0.5 lire la vraie fiche d'une affaire du registre (v4) ;
- 0.8 poser un syndic chez Hektor fait-il bouger la date de l'annonce (lecture d'annonces déjà modifiées) ;
- la règle du DPE vérifiée sur le texte officiel.
- **0.7** (à part, écriture chez Hektor, ACCORD) : créer un partenaire SOCIÉTÉ sur une fiche d'essai, relire ce que Hektor
  a gardé, puis le supprimer. ⇒ Sortie du lot : les réponses écrites dans cette note.

**Lot 1 — Le métier sur le serveur** *(nuit ; interrupteur `.env` proposé `APP_METIER_HEKTOR`, éteint)*
- A7 une étape de nuit lit les listes « syndic » et « diagnostiqueur » de Hektor (2 lectures) → table locale du métier
  Hektor, sur le modèle de `contact_metier_netty` ;
- A9 une lecture unique du métier des ~266 partenaires créés chez Hektor depuis la migration ;
- A8 la raison d'entrée « partenaire au métier connu (Netty ou Hektor) » dans `elargir_perimetre_registre.py`
  (**fichier du chantier ⑧, à coordonner**).
- Effet une fois allumé : les 75 syndics et 20 diagnostiqueurs entrent dans l'app la nuit suivante.
- Contrôle : à blanc d'abord, « personne n'entre sans raison, personne ne sort » ; le lendemain, les comptes chez Supabase.
- Retour arrière : éteindre ; ceux déjà envoyés restent (comme au §71 de la synthèse).

**Lot 2 — Le registre en base** *(Supabase ; patch + répétition + inverse ; ACCORD pour coller)*
- A1 la table du métier rattachée au contact (métier, source, confirmé par, confirmé le) et son remplissage depuis le
  serveur (Netty + Hektor) ;
- B1, B2, B4 la table des liens du registre : partenaire ↔ bien, ↔ affaire, ↔ client, avec rôle, posé par / le, retiré
  par / le (jamais de suppression) ;
- les fonctions qui posent et retirent un lien, et changent un métier (trace de l'auteur) ; droits fermés à la clé
  publique (⚠ `revoke from public` ne ferme pas `authenticated` : vérifier les deux) ;
- les vues de lecture pour l'écran (la page partenaire, le bloc de l'annonce, la fiche client).
- Contrôle : la répétition (témoins positifs et inverses), dans une transaction annulée d'abord.

**Lot 3 — La page partenaire, socle commun** *(front ; interrupteur Vercel proposé `VITE_APP_PARTENAIRES`, éteint)*
- K1 la page (squelette de la fiche notaire, déclinée par métier) ; A2 le métier affiché avec sa source ;
- A3 « Changer le métier » ; A5 le métier proposé depuis un lien ;
- B3 le sélecteur de partenaire (moteur du mandant, filtré par métier, « même adresse », « déjà lié ») ;
- K2 les interlocuteurs pour tous les métiers (forme à présenter : généraliser la table du notaire ou une table sœur) ;
- K3 la zone sensible (page partenaire seulement), la fenêtre commune, la case à cocher pour supprimer ; archivé reste
  modifiable ;
- K4 le menu « ⋯ » réduit ; K5 les états chargement / vide / erreur ; K6 l'annuaire des partenaires, tiré du métier ;
  K7 le téléphone ;
- K8 la modification des coordonnées : le choix (Hektor ou chez nous) présenté à Frédéric avant de coder.
- Les blocs de métier y sont vides tant que les lots 4 à 7 ne sont pas faits.

**Lot 4 — LE SYNDIC** *(premier métier, D3)*
- C1 ranimer le bloc « Intervenants du bien » de la fiche annonce (`CockpitDetail`), d'abord pour le syndic ;
- B5 l'assistant d'annonce cesse d'envoyer « Syndic » et « Diagnostiqueur » à Hektor et pose le lien dans le registre ;
- B6 la reprise des syndics des 731 annonces en copropriété (une ou deux nuits, sous le frein), puis le suivi de nuit
  (selon la réponse de 0.8) ; l'écart Hektor ↔ app est signalé, jamais écrasé ;
- G1 le regroupement des biens par immeuble (forme à présenter) ;
- G2 les demandes au syndic (table, geste « Demander un document », délai, relance) ; G3 le bloc « Copropriétés » ;
  G4 les assemblées générales ; G5 les blocs de calcul ; I1 les événements « demande » dans le fil ;
- C4 l'accroche de l'annonce au téléphone.

**Lot 5 — Le diagnostiqueur**
- le diagnostiqueur dans le bloc de l'annonce (même mécanisme que le syndic) ;
- F1 les commandes (table, geste « Commander un diagnostic », e-mail et RDV existants) ; F2 le suivi des commandes ;
- F3 « DPE qui expire » et « mandat sans DPE valable » (règle légale) ; F4 le rapport du coffre rattaché à la commande ;
  F5 les blocs de calcul ; I1 les événements « commande ».

**Lot 6 et Lot 7 — le courtier et l'apporteur** *(leur ordre reste à fixer par Frédéric)*
- **Courtier et banque** : E1 les champs du financement sur l'affaire ; C2 l'accroche « affaire » (financement à côté
  des notaires, « Prévenir le courtier ») ; C3 « Son courtier » sur la fiche client et l'étape « Orientés » ; E2, E3 les
  acquéreurs suivis, les conditions de prêt ; E4, E5 les pièces et l'envoi avec pièces (⚠ communs avec la fiche notaire :
  une seule fois pour les deux) ; E6, E7.
- **Apporteur et parrain** : H1 la commission sur le lien ; C3 « Apporté par » dès le premier jour (Q1) ; H2 les affaires
  apportées ; H3 « Commission réglée » et ses pièces ; H4 « Noter une affaire apportée » ; H5 ; B7 la reprise des
  53 apports de Netty (selon 0.4).

**L'allumage** : chaque interrupteur s'allume séparément, sur l'accord de Frédéric, après le contrôle de son lot. Le
front (`VITE_APP_PARTENAIRES`) peut rester éteint jusqu'à ce que le lot 4 soit prouvé, pour ne pas montrer une page vide.

## 9. AUDIT FINAL AVANT LE DEV — LES ERREURS TROUVÉES DANS MON PROPRE PLAN *(04/11, « fais un dernier audit global pour vérifier si tu ne fais pas d'erreur »)*

1. ⛔ **CONTRADICTION — les gestes du CONTACT partenaire partent chez Hektor.** Dans la forme « 1 », un partenaire est un
   contact de Hektor. Or « Modifier », « Archiver » et « Supprimer » d'un contact sont des travaux chez Hektor
   (`update_hektor_contact`, `archive_hektor_contact`, `delete_hektor_contact`), et la nuit RECOPIE l'état de Hektor
   (archivé, coordonnées) sur nos fiches. J'avais écrit « tous les gestes chez nous, rien n'est envoyé » : c'est faux
   pour ces trois gestes. Deux voies, **à trancher par Frédéric (E1)** :
   - **a** ces trois gestes restent ceux d'aujourd'hui (ils partent chez Hektor, comme pour tout contact) ; seuls les
     gestes du REGISTRE (métier, liens, commandes, demandes, commissions) restent chez nous ;
   - **b** ils restent chez nous : il faut alors une couche « chez nous » que la nuit respecte (le projet en a un modèle :
     `app_contact_override`, qui garde l'adresse, les commentaires… côté app), et un archivage local que la nuit ne défait
     pas. Plus lourd, et un partenaire « archivé chez nous » resterait actif chez Hektor.
   Ma recommandation : **a**.
2. ⚠ **P1 (« archivé reste modifiable ») + voie a** : on ne sait pas si Hektor accepte de modifier un contact archivé
   (jamais mesuré). Ajouté au lot 0.
3. ⚠ **La clé du registre** : le registre se rattache à NOTRE numéro (`hektor_contact_id`, plage 10 000 003 – 20 000 015
   chez Supabase), comme la fiche notaire — jamais au numéro Hektor. Les listes de Hektor donnent des numéros HEKTOR
   (`hektor_target_id`, 3 – 606 179) : la nuit doit les traduire. Et un contact qui sort de l'app est SUPPRIMÉ de
   Supabase par l'envoi de nuit (`mark_deleted_rows`) : le registre ne doit donc pas dépendre de la fiche par une clé
   en cascade ; il garde le numéro, et la fiche revient quand le contact revient.
4. ⚠ **L'ordre de la nuit** : la lecture des listes de Hektor (A7) doit passer AVANT l'étape d'entrée (A8), elle-même avant
   l'envoi. Et la lecture passe par UNE annonce (24113 à l'essai) : il faut une annonce de repli si elle disparaît.
   ⭐ Témoin positif déjà en main : les 12 syndics trouvés sur les 40 annonces de l'échantillon (plusieurs agences) sont
   TOUS dans la liste lue sur 24113 → la liste est bien commune à tout le groupe.
5. ✅ **Les interlocuteurs** : `app_notaire_interlocuteur` est VIDE (0 ligne). La généraliser à tous les partenaires ne
   déplace aucune donnée : K2 est plus simple que prévu.
6. ⚠ **Le lien client → affaire (Q1)** : il ne doit pas être RECOPIÉ sur l'affaire (deux copies divergent), mais RELU :
   l'affaire montre le courtier ou l'apporteur de son acquéreur ou de son vendeur, sauf lien posé sur l'affaire elle-même.
7. ⚠ **Le « 17 sur 40 »** : échantillon des annonces les plus RÉCENTES, donc pas représentatif ; la reprise (lot 4) donnera
   le vrai nombre.
8. ⚠ **Un partenaire créé dans l'app** : le formulaire envoie son métier à Hektor à la création (champ `metier`) ; pour un
   courtier ou un parrain, Hektor n'a pas ce métier : rien n'est envoyé, c'est sans effet. À garder tel quel.
9. ✅ Les noms d'interrupteurs proposés (`APP_METIER_HEKTOR`, `VITE_APP_PARTENAIRES`) ne sont utilisés nulle part.
10. ⚠ Le §69 de la synthèse des couples (« Hektor ne porte aucune donnée de métier ») est FAUX : Hektor a le métier et les
    listes syndic / diagnostiqueur. Corrigé ici (§6.1, §6 bis) ; signalé au chantier ⑧.

⇒ Le lot 0 gagne une mesure (modifier un contact archivé chez Hektor), et la décision **E1** est à prendre avant le lot 2.

✅ **E1 TRANCHÉE (04/11) : « a ».** Pour un partenaire, « Modifier », « Archiver » et « Supprimer » restent les gestes
d'aujourd'hui, qui partent chez Hektor comme pour tout contact. Seuls les gestes du REGISTRE (métier, liens, commandes,
demandes, financements, commissions) restent chez nous. ⇒ K8 est réglé (les coordonnées partent chez Hektor).
⇒ « Rien ne part chez Hektor » (D2) se lit désormais : rien de ce qui est PROPRE AUX PARTENAIRES.

**Le dev est lancé le 04/11 (« on lance le dev »), par le lot 0.**

### Lot 0 — résultats (04/11, lecture seule)

- **0.4 les 53 apports de Netty** (`affairs_contacts_relations.xlsx`, numéros sous la forme `[{'contact_id': N}]`) :
  39 apporteurs ; **51 sur 53 retrouvés chez Hektor** ; pour les 53 affaires, au moins un vendeur ou acquéreur est
  retrouvé ; **51 touchent un bien de notre registre** (`app_relation`). ⚠ Ces 51 affaires touchent 107 biens : un vendeur
  peut avoir plusieurs biens, et le fichier n'a pas le numéro de mandat de l'affaire. ⇒ La reprise B7 sera une
  PROPOSITION à confirmer à l'écran, pas un rattachement automatique.
- **0.5 la vraie fiche d'une affaire** (`RegistreTransactionsScreen.tsx`, `FicheDossier`, l. 709) : blocs « Parcours du
  dossier », « **Les parties** » (l. 1089, construit sur la liste `ROLES` : vendeur, acquéreur, notaires), « Répartition
  des honoraires », « **Conditions suspensives** » (avec échéance) et « Notes ». ⇒ C2 = ajouter courtier, banque et
  apporteur au bloc « Les parties » (lus dans le registre, même rendu `rt-partie`), et « Prévenir le courtier » sur la
  condition de prêt. Ma maquette « accroche affaire » est à transposer dans ce rendu.
- **La règle du DPE, vérifiée** (décret n° 2020-1610 du 17/12/2020 ; Service-public F16096) : DPE réalisé entre le
  01/01/2013 et le 31/12/2017 → valable jusqu'au 31/12/2022 ; entre le 01/01/2018 et le 30/06/2021 → jusqu'au
  31/12/2024 ; depuis le 01/07/2021 → 10 ans. (Avant 2013 : plus valable non plus.) Ma règle donnée de mémoire était juste.
- **0.3** : l'échantillon (17 sur 40) suffit pour lancer ; le vrai nombre viendra de la reprise (lot 4).
- **Restent, et ils ÉCRIVENT chez Hektor (accord obligatoire)** — un seul essai groupé sur des fiches d'essai :
  - 0.7 créer un partenaire SOCIÉTÉ avec un métier, relire ce que Hektor a gardé, puis le supprimer ;
  - modifier ce partenaire une fois ARCHIVÉ (P1 + E1), puis le réactiver ;
  - 0.8 poser un syndic sur l'annonce bac à sable 62774, relire si la date de l'annonce a bougé, puis le retirer.

### Lot 0 — L'ESSAI CHEZ HEKTOR (04/11, accord de Frédéric « Oui, accord ») — fiche d'essai « ZZ ESSAI SYNDIC BIENVU »

Fiche créée par l'écran de l'app (Contacts → Nouveau contact), sur le **compte formation** (FRANCK GERPHAGNON, n° 2) :
type Partenaire, Personne morale, SARL, métier Syndic, téléphone fictif 04 00 00 00 00, **e-mail d'activation RGPD
décoché**. Notre numéro **20000038**, numéro Hektor **606202**.

1. **Création** : travail `create_hektor_contact` fait en 13 s (15:32:32 → 15:32:45). Relu chez Hektor (formulaire) :
   raison sociale ✅, forme juridique SARL ✅, téléphone ✅, **métier : « Non défini » ⛔**. Le worker a bien envoyé
   `metier: 5` (journal du travail). ⇒ **Défaut D-1 : le métier d'un partenaire créé dans l'app n'est PAS gardé par
   Hektor.** Cause non établie ; piste : le formulaire de Hektor porte aussi un champ caché `metiers_ids`.
   Autres constats : la fiche s'affiche dans l'app avec le type « Contact » (pas « Partenaire ») et « Négociateur : Non
   affecté » juste après la création ; le formulaire exige un e-mail ou un téléphone (les 75 syndics de Hektor n'en ont
   presque jamais : ils ont été créés dans Hektor) ; l'e-mail d'activation RGPD est COCHÉ par défaut.
2. **Archivage** : travail `archive_hektor_contact` fait (15:33:54 → 15:34:05), Hektor répond « Modification archivage
   ok ». La boîte de confirmation du navigateur a été validée d'avance dans l'onglet (outil), son texte est le bon.
3. **Modification de la fiche ARCHIVÉE** (le fixe passé à 04 00 00 00 01) : ⛔⛔ **Défaut D-2, grave, en production** :
   - la fenêtre « Modifier le contact » traite la société comme une PERSONNE (civilité, nom, prénom) : ni raison
     sociale, ni forme juridique, ni métier ; et le numéro saisi en « fixe » à la création y apparaît en « portable » ;
   - l'envoi préparé (`app_contact_pending`, départ prévu 15:44:37) porte **`contact_kind: acquereur`**,
     **`person_type: personne_seule`**, la raison sociale en `last_name`, et **`send_rgpd_email: true`** ;
   - ⇒ modifier un partenaire société depuis l'app le RETYPE en acquéreur personne seule chez Hektor, et demande
     l'e-mail d'activation RGPD (qui partirait si la fiche avait un e-mail). Aucune modification de partenaire n'a
     encore été faite en production (mesure du 04/11), mais le défaut est actif pour tout le monde.
   - Laissé partir sur la fiche d'essai (sans e-mail) pour mesurer l'effet réel chez Hektor.
   - **RÉSULTAT (15:45)** : le travail `update_hektor_contact` a ÉCHOUÉ : « Formulaire edition contact Hektor introuvable
     pour 606202 ». Le worker relit le formulaire de Hektor et exige un champ `nom` (`updateHektorContactIdentity`,
     l. 19387) ; une SOCIÉTÉ n'a que `sociale`. ⇒ **On ne peut PAS modifier un partenaire société depuis l'app** ; rien
     n'est abîmé chez Hektor, mais l'app affiche un téléphone que Hektor n'a jamais reçu.
   - **Correction de mon alerte** : le `contact_kind: acquereur` de l'envoi ne RETYPE pas chez Hektor (le worker garde la
     typologie relue chez Hektor ; preuve : 2 mandants modifiés depuis l'app sont toujours « mandant »).
   - ⛔ **Défaut D-4, hors du chantier, en production** : `applyHektorContactIdentityValues` (l. 18720) ajoute
     `_email_rgpd=1` à CHAQUE modification dont l'envoi ne porte pas `send_rgpd_email: false`. Les 19 modifications de
     contact faites depuis l'app ont toutes porté `send_rgpd_email: true` (fenêtre « Modifier le contact »). Hektor
     envoie-t-il l'e-mail d'activation RGPD sur une MODIFICATION ? **Non mesuré.** À traiter à part, avec Frédéric.
4. **Réactivation** (15:46:33 → 15:46:46) : ✅ « Modification archivage ok », `reactivated`.
5. **Suppression** depuis l'app (raison + texte `SUPPRIMER CONTACT 20000038`, 15:47:26 → 15:47:41) : ✅ fiche retirée chez
   Supabase (0 ligne), inscrite au journal des suppressions, et ABSENTE chez Hektor (lecture du formulaire : 0 octet,
   contre 43 828 pour un syndic existant lu en témoin).
   ⚠ **Défaut D-3** : la suppression n'a PAS purgé l'envoi en attente (`app_contact_pending`, 1 essai) : la ligne reste,
   orpheline. Elle n'a pas été relancée à 15:55 (cause non vérifiée). C'est un reste de MON essai : sa suppression est
   une écriture en base, à faire avec l'accord de Frédéric.
   ✅ **Supprimée le 04/11 avec son accord** (« oui, supprime cette ligne orpheline ») : 1 ligne (`app_contact_pending`,
   20000038, « ZZ ESSAI SYNDIC BIENVU », 1 essai), vérifiée seule et sans fiche avant ; la file est vide après (0 ligne).
   **RGPD (D-4) : « on verra plus tard »** (Frédéric, 04/11) — noté, rien touché.
6. **0.8 (syndic sur 62774)** — ✅ FAIT à 17:02 (après la remarque de Frédéric « tu es passé par Chrome ? ») :
   - ⛔ **Mon erreur** : j'avais ouvert Hektor sur l'ANCIEN domaine (`groupe-gti-immobilier.la-boite-immo.com`), d'où le
     menu en erreur. Sur `www.gti-immobilier.fr/admin`, tout s'ouvre normalement.
   - Date de l'annonce lue par l'API (`phase2/sync/annonce_datemaj_from_api.py`, lecture seule) : **avant 21/10/2026
     09:38:42** → syndic « SYNDIC42 » posé dans « Caractéristiques › Diagnostics & Compléments › Contacts » → **après
     04/11/2026 17:02:48**. ⇒ **Poser un syndic chez Hektor CHANGE la date de l'annonce** : la nuit relira cette annonce.
   - ⚠ Mais le détail lu par la nuit (API) ne porte PAS le syndic : il faut, pour ces annonces, relire le bloc console
     « diagnostiques » (1 requête par annonce changée). C'est le dessin de B6.
   - Remis en l'état : syndic retiré et vérifié (liste vide), à 17:04.
   - ⭐ Vu au passage : chez Hektor, un bouton « + » à côté des listes Diag. et Syndic crée un contact depuis l'annonce.
     C'est ainsi que naissent les 75 fiches syndic SANS coordonnées.
   *(ancien libellé : NON FAIT — l'interface de Hektor ne s'ouvrait pas)* — l'interface de Hektor ne s'ouvre pas aujourd'hui (menu « Une erreur est
   survenue », la page du bien renvoie à l'accueil). À refaire quand elle reviendra.

## 10. CE QUE LES ESSAIS APPRENNENT SUR LES SYNDICS, ET COMMENT S'EN SERVIR *(04/11, « explique-moi ce que tu en ressors… et comment on pourrait l'utiliser, c'était le but »)*

**Ce qui est maintenant PROUVÉ**
1. Hektor a déjà un vrai système syndic : un MÉTIER sur le contact (Syndic 5, Diagnostiqueur 4), et sur chaque annonce deux
   listes (Diag., Syndic) qui proposent exactement les contacts de ce métier, avec un « + » pour en créer un.
2. Les négociateurs s'en servent : 17 annonces en copropriété sur 40 ont un syndic ; 75 syndics créés dans 8 agences et
   plus, presque tous depuis l'annonce (d'où l'absence de coordonnées).
3. LIRE tout cela coûte presque rien : 1 requête donne TOUS les syndics (et 1 tous les diagnostiqueurs) ; 1 requête donne
   le syndic d'une annonce ; et poser un syndic CHANGE la date de l'annonce, donc la nuit sait quelles annonces relire.
4. Notre app n'en voit rien aujourd'hui : syndics hors de l'app, bloc console lu pour 97 annonces, bloc de la fiche annonce
   jamais affiché, assistant qui envoie un nom au lieu d'un numéro.
5. ÉCRIRE depuis l'app est fragile : le métier envoyé à la création est perdu (D-1) ; modifier une société échoue (D-2).

**Comment s'en servir**
- **Le jour 1 n'est pas vide pour le syndic** : en reprenant ce que Hektor sait, la page d'un syndic montre tout de suite
  ses biens (ex. un syndic posé sur 3 biens), et le bloc « Intervenants du bien » s'allume sur ~40 % des annonces en
  copropriété. Le courtier et l'apporteur, eux, partent de zéro.
- **Chaque nuit, pour 2 requêtes** : la liste des syndics et diagnostiqueurs de Hektor → leur métier dans notre table →
  ils entrent dans l'app (lot 1). Un syndic créé le matin par un négociateur via « + » est dans l'app le lendemain.
- **Les liens annonce ↔ syndic** : une reprise des 731 annonces en copropriété (~731 requêtes, une ou deux nuits), puis
  chaque nuit seulement les annonces dont la date a changé, avec la relecture du bloc « diagnostiques ». Rangés dans le
  registre avec l'origine « hektor » ; un lien posé dans l'app gagne en cas d'écart (Q3).
- **La copropriété se déduit** : des biens qui partagent le même syndic et la même adresse forment un immeuble (G1).
- **Les négociateurs n'ont pas à changer leurs habitudes** : ce qu'ils posent dans Hektor arrive dans l'app ; ce qu'ils
  posent dans l'app reste chez nous (D2).
- **Ce qu'il ne faut PAS faire** : compter sur Hektor pour garder le métier d'un partenaire créé dans l'app (D-1 le
  prouve : notre table du métier est la seule fiable) ; ouvrir la page partenaire avec « Modifier » tant que la
  modification d'une société échoue (D-2 : mini-chantier à placer AVANT le lot 3, sur la voie « a » de E1).
- **Même mécanisme, gratuit, pour le diagnostiqueur** (21 fiches) ; mais 0 annonce sur 40 l'utilise : moins de valeur
  immédiate, cohérent avec D3 (syndic d'abord).

## 11. ⛔ CORRECTION (04/11) : LE SYNDIC ET LA COPROPRIÉTÉ SONT DÉJÀ RÉCUPÉRÉS — NE PAS LE FAIRE EN DOUBLE

> Frédéric : « De mémoire dans mon projet on récupère déjà copropriété et syndic, peut-être, cherche, on a déjà
> travaillé dessus, il ne faut pas le faire en double. » — Il avait raison.

**Ce qui EXISTE déjà**
- **La copropriété** vient de l'API de Hektor (`copropriete_json` dans le détail : 12 647 annonces ; lots, quote-part,
  fonds de travaux, statut du syndicat…). Rien à construire.
- **Le syndic et le diagnostiqueur** sont lus depuis JUIN par la console : `phase2/sync/sync_console_missing_fields.py`
  + `Console/extract_hektor_missing_fields.js` (`DIAGNOSTIC_CONTACT_KEYS = ["diagnostiqueur", "syndic"]`), rangés dans
  `diagnostics_contacts_console_json` (valeur = numéro du contact + libellé), et AFFICHÉS par l'ancienne fiche et la
  fiche téléphone (`App.tsx` 35794, 39862). Notes : `NOTE_EXTRACTION_CONSOLE_CHAMPS_MANQUANTS_2026-06-08.md`,
  `AUDIT_CHAMPS_HEKTOR_MANQUANTS_2026-07-07.md`.
- **L'étape de nuit existe** (`run_full_pipeline.ps1` l. 847, « console missing fields delta », portée « all »,
  25 annonces, relecture après 30 jours) mais elle est **ÉTEINTE** : c'est un commutateur (`-RunConsoleMissingFields`)
  qu'aucune tâche planifiée ne passe — décision de juin « pas de console la nuit », pour ménager Hektor. D'où les
  97-103 annonces seulement.
- **Le chantier ⑧ a déjà posé la question** (`CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md` l. ~933-945) : pour ~21 champs
  « console seule » (dont syndic et diagnostiqueur), trois voies — la garder éteinte · un balayage lent sous le mur ·
  ne garder que les annonces vivantes. **Non tranchée.**
- **Le défaut de l'assistant** (syndic et diagnostiqueur saisis en texte libre, alors que Hektor attend un contact) est
  DÉJÀ relevé par le chantier ⑧ (l. ~1244 et ~1280, essai du 22/10).

**Ce que ça change dans mon plan**
- **B6 « reprise des syndics des 731 annonces » : SUPPRIMÉ comme mécanisme neuf.** On réutilise l'étape existante ; la
  seule chose à faire est la DÉCISION du chantier ⑧ (l'allumer en balayage lent, d'abord sur les annonces en
  copropriété), puis relire `diagnostics_contacts_console_json` pour poser les liens dans le registre.
- **B5 (l'assistant)** : défaut déjà connu du chantier ⑧ ; à traiter une seule fois, en accord avec lui.
- **A7 (la liste de tous les syndics)** : le seul vrai manque — l'extracteur ne garde que la valeur CHOISIE, pas la
  liste des choix. ⇒ ne pas écrire de nouveau script : ajouter la liste des choix au même extracteur (lu 1 fois).
- **La copropriété (G3)** : lire `copropriete_json`, qui existe.

**Le coût en requêtes Hektor (corrigé le 04/11 par le chantier ⑧)**
- L'outil existant lit **21 pages par annonce** (la fiche + 10 blocs × 2 modes) : 731 annonces en copropriété ≈ 15 000
  requêtes. Lire le SEUL bloc « diagnostiques » coûte **1 requête par annonce** (731 au total).
- ⚠ **Mon chiffre « ~4 500 requêtes par nuit » était PÉRIMÉ** : depuis la nuit du 03-04/11, la nuit des contacts lit la
  liste entière (8 114 pages + 180 fiches, journal `logs/scheduled/nuit_contacts_2026-11-04_00-20-01.log` ; synthèse
  couples l. 1635) ⇒ **~12 800 requêtes par nuit**, déjà au niveau de l'estimation du quota (17 000-19 000 par 24 h,
  §45). Toute lecture ajoutée, même 731, est à rapporter à ce total : à Frédéric de trancher le rythme.

## 12. COPROPRIÉTÉ ET SYNDIC : CE QUE NOUS AVONS VRAIMENT, SERVEUR ET APP *(04/11, mesuré, lecture seule)*

> Frédéric : « est-ce que j'ai les informations de la copropriété ? Puisque le run de console a été coupé, est-ce qu'on
> l'avait déjà fait tourner au moins une fois pour tout rattraper ? Vérifier en data, serveur et app. »

**La copropriété (vient de l'API, chaque nuit)** — mesuré sur les 13 525 fiches détaillées, IDENTIQUE serveur et app :
- bloc copropriété présent : **12 697** ; « copropriété : OUI » **731**, « NON » **11 916**, vide 50 ;
- sur les 731 « OUI » : nombre de lots rempli 317, quote-part / charges 270, statut du syndicat 106 ;
- ⚠ **appartements (type 2) : 2 500, dont 576 « OUI » et 1 910 « NON »**. Un appartement est presque toujours en
  copropriété : beaucoup de ces « NON » sont sans doute la valeur PAR DÉFAUT de Hektor, jamais corrigée (non prouvé
  fiche par fiche). Maisons (type 1) : 73 « OUI » sur 8 013.
- Les archives et les vendus anciens ne sont pas mesurés ici.

**Le syndic et les ~20 autres champs « console seule »**
- Serveur (`data/hektor.sqlite`, table `hektor_annonce_console_detail`) : **179 annonces lues EN TOUT, depuis juin**,
  dont **122 le 08/06/2026** (la journée de mise au point de l'outil), puis quelques-unes par mois (17 en octobre,
  4 en novembre, au fil des créations et relectures). Parmi elles, 1 seule a un syndic, 0 un diagnostiqueur.
- App : 97 fiches vivantes ont ce bloc (serveur : 96).
- ⇒ **Non : aucun rattrapage complet n'a jamais tourné.** La note de juin le dit (`NOTE_EXTRACTION_CONSOLE_CHAMPS_MANQUANTS
  _2026-06-08.md` l. 77) : l'outil est gardé « comme outil de contrôle/rattrapage », avec de petits lots prudents
  (20 annonces, 60 s entre deux). L'étape de nuit est éteinte depuis.
- ⇒ Le syndic des ~300 biens en copropriété où les négociateurs l'ont posé (estimation de l'échantillon) n'est
  NULLE PART chez nous aujourd'hui.

## 13. LE SYNDIC DES COPROPRIÉTÉS : CODÉ LE 04/11 (« toutes les nuits en une fois, et maintenant pour mettre à jour »)

**Ce qui a été écrit** (sur le patron EXACT du chauffage, pas un mécanisme neuf) :
- `Console/extract_hektor_diag_contacts_only.js` (neuf) : jumeau de `extract_hektor_chauffage_only.js`. Un seul bloc
  console (« diagnostiques », mode editer), UNE requête par annonce, un navigateur pour tout le lot. Rend
  `diagnostics_contacts_console_json` sous la même forme que l'outil complet, et une fois par lot la LISTE des choix
  (tous les syndics et diagnostiqueurs de Hektor). Essai réel (24113, 62774) : 24113 → syndic 423683, 62774 → vide,
  choix 75 syndics / 21 diagnostiqueurs, 10 s.
- `phase2/sync/sync_hektor_contacts_diagnostics.py` (neuf) : jumeau de `sync_hektor_chauffages.py` (mêmes garde-fous :
  arrêt net sur 403, une reprise de session, vérification des jobs console). Portée « copro » par défaut (annonces que
  l'API marque en copropriété). Tables locales neuves dans `data/hektor.sqlite` : `hektor_annonce_diag_contacts_detail`
  et `hektor_diag_contacts_choix` (mise à jour, jamais vidée). À blanc : 731 annonces.
- `phase2/sync/export_app_payload.py` (modifié, additif) : la nuit transmet à l'app la lecture LA PLUS RÉCENTE du syndic
  (outil complet ou bloc seul), sans aucun champ neuf. Épreuve dans une base temporaire, **6 verts sur 6** (témoins :
  sans la table rien ne change ; une lecture en erreur n'écrit rien ; l'outil complet plus récent garde la main).
- `run_full_pipeline.ps1` (modifié, additif) : étape « hektor syndic et diagnostiqueur », juste après le chauffage, NON
  bloquante, **ÉTEINTE** (`-HektorDiagContactsLimit 0` par défaut). Syntaxe vérifiée (0 erreur), BOM intact. Pas de
  battement (aucune clé au registre des workers : à ajouter avant de s'y fier).

**Le premier passage** (« maintenant ») : lancé le 04/11 vers 17:25, 731 annonces, 1 requête par seconde, lots de 100 ;
compte rendu `logs/manual/syndics_copro_2026-11-04.json`.

**Résultat (17:11:26 → 17:34:35, 24 min, code 0)** :
- **731 lues, 730 rangées « done », 1 erreur** : l'annonce 61398 n'a pas les deux listes dans son bloc (forme
  inconnue) ; elle est DITE en erreur, pas rangée comme vide (le garde-fou a joué).
- **Un 403 en cours de route**, rattrapé par UNE reprise de session (comme prévu) ; aucun arrêt.
- ⭐ **79 annonces sur 731 ont un syndic (11 %)**, 29 syndics différents, tous dans la liste de Hektor ; un seul syndic
  porte 16 biens, un autre 7. **4 annonces** ont un diagnostiqueur. ⇒ Mon « 42 % » de l'échantillon des 40 annonces
  les plus RÉCENTES était très au-dessus de la réalité (les négociateurs remplissent le syndic surtout depuis peu).
- Liste des choix rangée : 75 syndics, 21 diagnostiqueurs.
- ⚠ **L'app ne l'a pas encore** : la nuit le transmettra (export + envoi de 05:00). Et l'écran qui l'affiche
  aujourd'hui est l'ancienne fiche et la fiche téléphone ; la fiche annonce en production attend le lot 4 (bloc
  « Intervenants du bien »).

✅ **ALLUMÉ le 04/11 (« oui, allume »)** : `-HektorDiagContactsLimit` passe de 0 à **1000** dans `run_full_pipeline.ps1`
(syntaxe vérifiée, BOM intact ; `scheduled/run_quotidien.ps1` appelle ce fichier sans forcer ce réglage). Effet dès la
nuit du 04 au 05/11.
- Durée : le run (début 04:00) finissait vers 06:12-06:19 du 30/10 au 04/11 ; avec ~24 min il finira vers ~06:45, plus
  d'une heure avant la descente de 07:45.
- Budget Hektor : ~731 requêtes de plus sur ~12 800 (voir §11).
- Retour arrière : remettre 0.
- ⏰ **Contrôle du 05/11 au matin** : dans `logs/scheduled/quotidien_2026-11-05_*.log`, la ligne « hektor syndic et
  diagnostiqueur » en DONE et sa durée ; dans `data/hektor.sqlite`, `hektor_annonce_diag_contacts_detail` relue
  (extracted_at du 05/11) ; chez Supabase, `diagnostics_contacts_console_json` présent sur ~731 fiches (contre 97) et
  ~79 avec un syndic ; l'heure de fin du run.
- ⚠ Pas de battement au registre des workers pour cette étape : un échec ne se voit que dans le journal (WARN).
- Rien n'est commité : `Console/extract_hektor_diag_contacts_only.js`, `phase2/sync/sync_hektor_contacts_diagnostics.py`
  (neufs), `phase2/sync/export_app_payload.py`, `run_full_pipeline.ps1` (modifiés). La nuit lit les fichiers du
  disque : elle tournera même sans commit.

## 14. LOT 2, PIÈCE 1 — LE REGISTRE EN BASE : ✅ POSÉ LE 04/11 (accord de Frédéric « oui tu as mon accord »)

✅ **Posé** par la migration `registre_partenaires_2026_11_04` (le contenu du fichier, garde comprise). **Répétition :
9 verts sur 9** (tables, RLS, anon fermé, authenticated en lecture seule, fonctions exécutables et SECURITY DEFINER,
index d'unicité, tables vides). Retour arrière : `_INVERSE.sql` (il recopie d'abord les lignes dans des tables datées).

- **Fichiers** : `supabase/patch_registre_partenaires_2026-11-04.sql` (+ `_REPETITION.sql`, `_INVERSE.sql`), sur le patron
  EXACT de `app_notaire_interlocuteur` (patch_notaire_blocs_2026-10-28.sql).
- **Ce qu'il pose** (rien d'existant n'est modifié, rien chez Hektor) :
  - `app_partenaire_metier` : le métier d'un contact (notre numéro), plusieurs possibles, source netty / hektor / ecran,
    confirmé par / le ;
  - `app_partenaire_lien` : partenaire ↔ bien (syndic, diagnostiqueur), ↔ affaire (courtier, banque, apporteur),
    ↔ client (courtier, apporteur — Q1) ; origine app / hektor / netty ; deux contrôles en base interdisent un rôle
    sur le mauvais objet ou deux cibles à la fois ; un même lien actif n'existe qu'une fois ;
  - `app_partenaire_metier_ecrire` et `app_partenaire_lien_ecrire` : tout compte actif, auteur et heure écrits, « retirer »
    ne détruit rien ; un double-clic ne fait pas deux lignes ; confirmer un métier de Netty ou Hektor garde sa source.
  - Lecture : tout compte actif (RLS) ; anon : rien ; authenticated : lecture seule, écriture par les fonctions.
  - SANS clé étrangère vers `app_contact_current` (la nuit y supprime un contact qui sort de l'app).
- **Éprouvé dans des transactions ANNULÉES** (le bloc finit par une erreur voulue ; vérifié après : 0 table, 0 fonction) :
  - essai 1 (structure, droits, contraintes, témoins) : **13 verts sur 13** ;
  - essai 2 (le patch COMPLET, en se faisant passer pour le compte de Frédéric) : **9 verts sur 9** — compte reconnu,
    double-clic, auteur et origine, retrait daté, retrait double refusé, courtier sur un bien refusé, confirmation d'un
    métier de Hektor (source gardée), second métier (source écran), retrait d'un métier.
- **À faire, avec l'accord de Frédéric** : coller le patch, puis la répétition (9 contrôles). Ensuite la PIÈCE 2 : la
  reprise de nuit (métier depuis Netty et les listes de Hektor ; liens syndic depuis
  `hektor_annonce_diag_contacts_detail`, en traduisant les numéros Hektor en nos numéros).

## 15. LOT 2, PIÈCE 2 — REMPLIR LE REGISTRE CHAQUE NUIT (04/11, « oui pièce 2 ») — ÉCRIT, ÉTEINT

- `phase2/contacts/registre_partenaires_reprise.py` (neuf) : lit EN LOCAL `contact_metier_netty`,
  `hektor_diag_contacts_choix` et `hektor_annonce_diag_contacts_detail`, traduit les numéros Hektor en nos numéros
  (`hektor_target_id` → `hektor_contact_id`), et complète chez Supabase `app_partenaire_metier` et
  `app_partenaire_lien`. Règles : notaires laissés de côté ; un métier n'est qu'AJOUTÉ (jamais modifié ni retiré par la
  nuit) ; un lien « hektor » est ajouté s'il manque, retiré (daté) si Hektor change ou retire le syndic d'une annonce
  qu'il vient de relire ; un lien posé dans l'APP n'est jamais touché, l'écart est compté. À blanc par défaut ;
  `--ecrire` n'écrit que si `APP_REGISTRE_PARTENAIRES` est dans le `.env` (sinon « éteint », sortie 0 — témoin vérifié).
  Vérification après écriture : tout métier voulu est bien là, sinon sortie 1.
- **À blanc sur la vraie base** : **213 métiers** à poser (Netty 118 hors 844 notaires : apporteur 35, courtier 22,
  diagnostiqueur 16, parrain 15, banque 8, administration 7, société 5, mandataire 4, autres 6 ; Hektor 95 : syndic 75,
  diagnostiqueur 20) et **83 liens** (79 syndics + 4 diagnostiqueurs sur des annonces) ; 0 à retirer, 0 écart.
- `run_full_pipeline.ps1` : étape « phase2 registre des partenaires » juste après la lecture du syndic, non bloquante.
  Syntaxe vérifiée, BOM intact.
- ⚠ Les 75 syndics de Hektor ne sont pas encore des contacts de l'app (raison d'entrée élargie A8, fichier du chantier ⑧) :
  le registre porte leur numéro, la fiche viendra quand ils entreront.
- ✅ **ALLUMÉ ET REMPLI le 04/11 vers 19:33 (« oui, allume »)** :
  - `.env` : copie datée `.env.avant_registre_partenaires_20261104_1933`, puis `APP_REGISTRE_PARTENAIRES=1` ajouté à
    la fin avec son commentaire (fins de ligne du fichier respectées, ligne présente une seule fois) ;
  - premier remplissage (`logs/manual/registre_partenaires_2026-11-04.json`, code 0) : 213 métiers + 83 liens écrits,
    vérification interne 0 manquant ;
  - **contrôle chez Supabase** : 213 métiers actifs (Netty 118, Hektor 95 : syndic 75, diagnostiqueur 20), 83 liens
    actifs (syndic 79, diagnostiqueur 4, origine « hektor »), **0 lien sans dossier**, 29 syndics différents, **0 lien
    dont le partenaire n'a pas le métier** ;
  - **second passage** : 0 à ajouter, 0 à retirer (la reprise ne fait pas de double).
  - Effet chaque nuit dès le 04-05/11, juste après la lecture du syndic. Retour arrière : retirer la ligne du `.env`
    (les lignes déjà écrites restent ; `_INVERSE.sql` du patch les recopie avant de retirer le registre).

## 16. LOT 1 — LES PARTENAIRES DE HEKTOR ENTRENT DANS L'APP (04/11 soir, « donc lot 1 »)

**A8 — la raison d'entrée élargie** (`phase2/contacts/elargir_perimetre_registre.py`, fichier du chantier ⑧, modifié
de façon ADDITIVE ; il était propre, sans modification en cours) :
- troisième raison **`partenaire_hektor`** : un contact que Hektor range en métier Syndic ou Diagnostiqueur (les choix des
  listes de l'annonce, `hektor_diag_contacts_choix`), plus ceux dont le formulaire porte un métier utile
  (`hektor_contact_metier`, hors notaire, autre, collaborateur, « à supprimer ») ; numéros Hektor traduits en nos numéros ;
- ⚠ 9 des 96 syndics et diagnostiqueurs sont des SOCIÉTÉS sans nom ni prénom : pour cette raison SEULE, la raison sociale
  (`display_name`) vaut nom ; la garde de la case vide reste entière pour les deux autres raisons ;
- lu seulement si les colonnes existent, liste passée en paramètre facultatif : les 11 essais d'origine passent
  inchangés ; **4 essais ajoutés** (syndic qui entre, société par sa raison sociale, la case vide du registre reste
  dehors, témoin sans liste) → **15 verts sur 15** ;
- **à blanc sur la vraie base : 95 contacts entreraient** (les 75 syndics et 20 diagnostiqueurs absents de l'app),
  0 par les autres raisons. L'étape étant déjà ALLUMÉE (`APP_PERIMETRE_REGISTRE=1`), **ils entreront la nuit du 04-05/11**
  et partiront chez Supabase avec l'envoi des contacts. Retour arrière : retirer la raison du fichier (ceux déjà envoyés
  restent, comme au §71 de la synthèse).

**A9 — le métier des partenaires créés depuis la migration** :
- `Console/extract_hektor_metier_contacts.js` (neuf, jumeau de l'extracteur du syndic : le formulaire d'un contact, une
  requête par fiche, lecture seule) et `phase2/contacts/metier_hektor_contacts.py` (neuf : range dans la table locale
  `hektor_contact_metier`, mise à jour sans être vidée ; `--importer` un compte rendu, ou `--lire`).
- Lecture faite le 04/11 (312 s, 203 fiches, 0 erreur) : **199 notaires, 4 sans métier**. ⇒ Il n'y a pas de banque ni
  d'apporteur caché parmi les partenaires récents : ce sont les notaires des compromis. Rangés (203), écartés par les
  deux étapes (notaires laissés de côté) : la reprise du registre trouve 0 métier de plus, l'entrée reste à 95.
- Non branché la nuit : les nouveaux syndics et diagnostiqueurs arrivent déjà par les listes de l'annonce, relues chaque
  nuit. `--lire` reste disponible pour une relecture ponctuelle.

✅ **Lot 1 commité le 04/11 : `b9dca1b`** (« Oui, commite »).

## 17. LE NOTAIRE ENTRE AU REGISTRE — DÉCISION « A » (04/11 soir) — ✅ POSÉ ET ALLUMÉ, LA NUIT ÉCRIT

**La question de Frédéric** : *« les partenaires ajoutés à partir de Netty et les notaires déjà présents dans l'annuaire
sont-ils regroupés avec les syndics et diagnostiqueurs récupérés ? »* Réponse : Netty + Hektor oui (même registre, 213
métiers) ; les notaires non, par construction (leur type vient de la table des parties). Deux formes proposées :
**A** les notaires entrent au registre (une seule source pour l'annuaire) · **B** ils restent à part (deux sources).
**Frédéric : « A ».**

**Mesuré (lecture seule)** — trois sources de notaires, par NOTRE numéro de contact :
- table des parties chez Supabase (rôles `notaire_vendeur` / `notaire_acquereur`) : **1 333** personnes, dont 1 127 dans l'app ;
- Netty (`contact_metier_netty`, « notaire ») : **844**, tous dans l'app (raison `partenaire_netty`) ;
- formulaire Hektor (`hektor_contact_metier`, code 2) : **199**, dont 144 dans l'app ;
- recoupements : parties ∩ Netty 574 · parties ∩ Hektor 146 · Netty ∩ Hektor 0 ⇒ **1 656 notaires distincts**, dont
  **1 397 déjà dans l'app** ; 0 hors de la couche locale ; 10 portent déjà un autre métier au registre (permis : un
  contact peut avoir plusieurs métiers).

**Préparé** :
- `supabase/patch_registre_partenaires_notaire_2026-11-04.sql` : remplace DEUX contrôles de `app_partenaire_metier` —
  le métier accepte `notaire`, la source accepte `transactions` (= la table des parties). Empreintes vérifiées avant, sinon
  arrêt. Aucune ligne écrite. `_REPETITION.sql` (6 contrôles), `_INVERSE.sql` (copie datée des lignes notaire /
  transactions, puis contrôles remis à leur forme EXACTE du 04/11, empreintes vérifiées).
- **Essai dans une transaction annulée (04/11)** : patch → un notaire « transactions » s'écrit ; un métier inconnu, une
  source inconnue et un doublon sont REFUSÉS ; inverse → 1 ligne copiée, les deux empreintes reviennent, 213 lignes avant
  et après. Base vérifiée inchangée ensuite (empreintes `64401c40…` et `90bff85f…`).
- `registre_partenaires_reprise.py` : les notaires (Netty « notaire », Hektor code 2, table des parties en source
  `transactions`, dans cet ordre de priorité) derrière un **SECOND interrupteur `APP_REGISTRE_PARTENAIRES_NOTAIRES`,
  ÉTEINT**. ⚠ Pourquoi un second interrupteur : sans le patch, le contrôle refuserait « notaire », et un lot de 500 refusé
  ferait échouer TOUT le lot (les syndics avec). `--notaires-a-blanc` compte sans jamais écrire.
  À blanc : interrupteur éteint → **0 ajout** (rien ne change cette nuit) ; avec les notaires → **1 656 ajouts**
  (Netty 844, Hektor 199, transactions 613).

**Ce qui NE change pas** : le type « Notaire » d'un contact (toujours tiré de la table des parties), la fiche notaire du
28/10, la vue `app_contact_relations_current`, `app_partenaire_lien` (pas de rôle notaire : le notaire d'une affaire est
déjà dans la table des parties), le lot 1 (`elargir_perimetre_registre.py` écarte toujours le code 2 : les 55 notaires
Hektor hors de l'app n'y entrent pas — **question ouverte**, voir plus bas). Rien chez Hektor.

**Ce que ça pourrait casser ailleurs** : rien ne lit encore `app_partenaire_metier` (l'annuaire est le lot 3). Le seul
lecteur est la reprise de nuit elle-même, protégée par l'interrupteur.

✅ **FAIT le 04/11 vers 21:10** (Frédéric : « d'abord finir les correctifs en cours sur le regroupement ») :
① patch posé chez Supabase (migration `registre_partenaires_notaire_2026_11_04`), **répétition 6/6 verte** ;
② `APP_REGISTRE_PARTENAIRES_NOTAIRES=1` ajouté au `.env` (copie : `.env.avant_registre_notaires_20261104_2111`) ;
à blanc, interrupteur allumé : **1 656 notaires à ajouter** (Netty 844, transactions 613, Hektor 199), 0 lien touché ;
③ commit. ⇒ **La nuit du 04-05/11 les écrit** (étape « phase2 registre des partenaires »).
⏰ **Contrôle du 05/11** : `app_partenaire_metier` actif = 213 + 1 656 = **1 869** ; `metier = 'notaire'` = 1 656
(sources netty 844 / transactions 613 / hektor 199) ; l'étape en code 0 dans le journal du run.
Retour arrière : éteindre l'interrupteur, PUIS `_INVERSE.sql`.
**Question ouverte** : les **259 notaires qui ne sont pas dans l'app** (206 venus des transactions, 53 de Hektor) doivent-ils
y entrer ? Aujourd'hui l'annuaire ne pourra afficher que les 1 397 présents.

### 17 bis. POURQUOI LES 206 NOTAIRES DES TRANSACTIONS NE SONT PAS DANS L'APP (04/11, « pourquoi les 206 n'y sont pas ? »)

Mesuré, lecture seule. **Ce n'est pas une décision, c'est un trou** : la règle qui fait entrer « toute personne que Hektor
nomme dans une transaction » (`phase2/contacts/elargir_perimetre_console.py`, raison `console_transaction_party`, écrite
le 11/09 — elle fait entrer 1 087 des 1 127 notaires présents) **ne lit qu'UNE des trois places** où le registre trouve
ses notaires : la liste `parties_json` du formulaire recopié (`app_affaire_console`). Or le registre des transactions
(`app_affaire_ledger`, colonnes `notaire_mandant_id` / `notaire_acquereur_id`, ajoutées le 16/09, CINQ JOURS APRÈS la
règle) les prend aussi ailleurs. Les 206 : 683 lignes de la table des parties, 640 transactions, toutes présentes chez
Hektor, toutes d'origine « listes du registre », 0 dans Netty :
- **337 lignes de COMPROMIS (≈ 199 personnes)** : lues par la console le **10/09**, avant que `parties_json` existe. Le
  notaire est dans les colonnes `notaires_mandant` / `notaires_acquereur` du formulaire recopié, que la règle ne lit pas ;
  `parties_json` y est VIDE ;
- **341 lignes de VENTES** : le notaire vient de l'**API de la vente** (règle de fusion du 16/09 : « vente, l'API
  d'abord »). Le formulaire de la vente a une liste de notaires vide (lu les 14-15/09). La règle ne lit pas le registre ;
- **5 lignes de ventes** : le formulaire nomme un AUTRE notaire que l'API (les « 27 contradictions » du 16/09 ; le
  registre garde l'API).
⚠ **Au passage** : la table des parties n'a PAS de numéro Hektor pour ces notaires, parce qu'elle le cherche dans
`app_contact_current` de Supabase… où ils ne sont pas. Le trou s'entretient lui-même.
⚠⚠ **LEÇON 9 — la même cause touche toute la famille** : personnes de la table des parties absentes de l'app, par rôle :
**acquéreurs 1 301 · vendeurs 496 · notaires du vendeur 133 · notaires de l'acquéreur 98**. Une partie des acquéreurs
et vendeurs peut entrer dès la nuit du 05/11 par la raison `registre_relation` de ⑧ (liens aux annonces) : **à
re-mesurer après la nuit** avant de conclure.
**Remède proposé (rien n'est codé)** : faire lire à la règle d'entrée la table des parties elle-même (nos numéros,
déjà calculés), au lieu du seul formulaire recopié. Périmètre (notaires seuls ou toute la famille) : **à Frédéric**.

## 18. D-2 « MODIFIER UN PARTENAIRE » — AUDIT (04/11 soir, « push puis modifier une société ») — rien codé

Poussé avant : `acc097c..cdeb374`.
**La cause, mesurée (lecture seule du formulaire de 2 syndics chez Hektor, 414566 et 414567)** : le formulaire d'un
PARTENAIRE porte le groupe **`mefContacts/contacts_full_accueil_partenaire`**. Le worker (`updateHektorContactIdentity`,
`console_job_worker.js` ~l. 19378) ne connaît que deux groupes : `contacts_full_accueil` (personne seule) et
`contactCoupleAll` (couple, corrigé le 02/11) ; `extractHektorFormValues` compare le groupe à l'IDENTIQUE (l. 10445)
⇒ aucun champ relu, pas de `nom` ⇒ « Formulaire edition contact Hektor introuvable ». **C'est donc TOUT partenaire
(personne ou société), pas seulement une société.** Le groupe d'une personne MORALE n'est pas mesuré (la fiche d'essai
606202 est supprimée).
**Ampleur** : 29 modifications de contact depuis juin, 27 faites, 2 en erreur « introuvable » (20000031 le 02/11, couple,
corrigé depuis ; 20000038, mon essai). **Aucun partenaire réel modifié à ce jour** : rien d'abîmé, le défaut dort.
**Remède proposé** : comme pour les couples, prendre le groupe du formulaire RELU — celui du champ `nom` ou `sociale` —
au lieu d'une liste de noms ; si le formulaire porte `sociale`, traiter la fiche en société (status 3 : la raison sociale
part dans `sociale`, le reste ne bouge pas). La fenêtre de l'écran (qui montre une société comme une personne) est un
second temps.

### 18 bis. ⛔ ERREUR DANS MON LOT 1 (trouvée le 04/11 soir en cherchant un syndic société)

J'avais écrit (§16) : « une société sans nom ni prénom entre par sa raison sociale (`display_name`) ». **C'est faux** :
la couche locale ne porte AUCUNE raison sociale ; pour une fiche sans nom ni prénom, `display_name` est FABRIQUÉ
(« Contact 10215568 », `build_contacts_layer.py` l. 200). ⇒ **9 des 95 entrants de cette nuit entreront nommés « Contact
1021… »** au lieu de « GIBERT IMMOBILIER », « PICHET IMMOBILIER SERVICES »… (leur vrai nom est dans
`hektor_diag_contacts_choix.libelle`). Ce n'est pas une perte (3 777 contacts de l'app portent déjà un tel nom), mais
c'est exactement ce que la garde de la case vide voulait éviter. Décision à Frédéric : les garder dehors ce soir (2 lignes)
ou les laisser entrer. **Frédéric : « les laisser… mais on va corriger pour les prochains ».**

### 18 ter. OÙ HEKTOR RANGE LE NOM D'UN PARTENAIRE « SANS NOM » (05/11 matin, après le run fini à 06:43, lecture seule)

- **9 592 fiches « partenaire » ont un nom fabriqué** dans la couche (« Contact 1… »), dont **250 dans l'app** ; 0 fiche née dans
  l'app. ⚠ Ce n'étaient PAS 9 592 sociétés cachées :
- l'API (raw_json) ET le formulaire d'édition ont `nom` et `prenom` **VIDES**, même pour GIBERT IMMOBILIER (414566) : le mot
  « GIBERT » n'est nulle part dans le formulaire (0 occurrence), ni en mode consultation ;
- Hektor l'affiche pourtant en titre de la fiche : il vient de la requête `mode=contacts-contactProfile-setContactContent`
  (le profil), calculé côté Hektor (vu dans Chrome, requête écoutée) ;
- même requête sur 4 fiches de l'échantillon (583835, 523707, 599679, 560025) : **AUCUN titre** ⇒ ce sont des fiches
  réellement VIDES chez Hektor (métier « Non défini », rien nulle part), pas des sociétés.
⇒ **Le cas « société au nom caché » est celui des syndics / diagnostiqueurs créés par le bouton « + » de l'annonce.**
**Remède proposé (rien codé)** : (1) le nom affiché prend le libellé de la liste syndic / diagnostiqueur
(`hektor_diag_contacts_choix.libelle`, 0 requête) avant « Contact … », et la règle d'entrée l'accepte ; (2) pour un autre
partenaire sans nom, s'il s'en présente, le titre du profil (1 requête par fiche) — à mesurer quand on traitera courtier et
apporteur.

## 19. LE NOM DES SYNDICS / DIAGNOSTIQUEURS SANS NOM — CODÉ LE 05/11, ÉTEINT (« je valide le correctif »)

Frédéric (05/11) : « raison sociale plus tard, d'abord finir le chantier des partenaires ; je valide le correctif pour
récupérer les noms à partir de la liste lors du run de nuit » — pour les 9 entrés le 04/11 et les futurs.
⚠ « Le bouton + » = celui de la fiche annonce **dans l'admin de Hektor** (pas dans l'app). Un partenaire société créé
**depuis l'app** a son nom dans la case « nom » de Hektor (essai ZZ ESSAI SYNDIC BIENVU du 04/11, relu 2 min après :
`nom` et `display_name` justes) : il n'est pas concerné.
⚠ L'API de Hektor ne rend AUCUN champ raison sociale (champs de 414566 listés le 05/11 : `siret` oui, raison sociale
non). Ajouter une colonne « raison sociale » chez nous = plus tard (Frédéric).

**Le code** (interrupteur `.env` **`APP_NOM_PARTENAIRE_PAR_LA_LISTE`**, absent = éteint, à l'identique d'avant) :
- `build_contacts_layer.py` : `nommer_par_la_liste_des_partenaires()` après `resoudre_menages()` dans `load_contacts`
  (donc la nuit ET la relecture du worker) ; une fiche sans nom NI prénom, hors ménage, prend le `libelle` de
  `hektor_diag_contacts_choix` (lu par `hektor_target_id`, le syndic avant le diagnostiqueur), sinon « Contact N » ;
  `nom` et `prenom` restent vides (on n'invente rien) ;
- `elargir_perimetre_registre.py` : interrupteur allumé, un `display_name` égal à « Contact <numéro> » ne vaut plus nom
  (la garde de la case vide redevient entière) ;
- essais : `test_nom_partenaire_liste.py` 9/9 (dont témoin éteint, ménage, libellé vide, table absente) et
  `test_elargir_perimetre_registre.py` +2 (nom fabriqué dehors / témoin éteint) ; avec `test_contacts_layer` et
  `test_couple_couche` : **27 essais verts**.

**Mesure à blanc** (copie de Hektor de la nuit du 05/11, lecture seule) : sur les 96 de la liste, **8 changent** —
GIBERT IMMOBILIER, AGENCE IMMOBILIERE DE BELLEVUE, PICHET IMMOBILIER SERVICES, SOCIETE DE GESTION IMMOBILIERE,
DETROIS IMMOBILIER, CABINET MELLIER MICHAS, GOUDARD PATOT, IMMO DE FRANCE FOREZ VELAY ; **le 9e (diagnostiqueur 423727,
chez nous 10217339) n'a de nom nulle part**, même pas dans la liste : il reste « Contact 10217339 », ne rentre plus par
`partenaire_hektor`, mais il est déjà dans l'app et `APP_GARDER_CONTACTS_DEJA_POUSSES=1` le garde à jour.
**Contrôle du registre ce matin** : 1 869 actifs dont 1 656 notaires (netty 844, transactions 613, hektor 199),
syndic 75, diagnostiqueur 36 — **exactement l'attendu du §17**.
**Retour arrière** : retirer la ligne du `.env` ; la nuit suivante refait les noms d'avant.
✅ **ALLUMÉ le 05/11 à 09:31** (« Allume et commite ») : ligne 132 du `.env`, copie
`.env.avant_nom_partenaire_liste_20261105_0931` ; vérifié sans rien écrire : la couche ET la règle d'entrée le lisent
allumé (GIBERT IMMOBILIER sort sous son nom, 423727 reste « Contact 423727 »).
✅ **LES 8 MIS À JOUR TOUT DE SUITE le 05/11 à 09:32-09:34** (Frédéric : « peux-tu le faire maintenant pour mettre à
jour les 9 ») : `phase2/sync/refresh_contact_inproc.py --contact-id <id>` (l'outil du worker : 1 lecture chez Hektor,
couche, push), un par un, 2 s de pause, aucune tâche du projet en cours ; 8 sorties en code 0. **Chez Supabase** :
10215568 GIBERT IMMOBILIER · 10215569 AGENCE IMMOBILIERE DE BELLEVUE · 10215570 PICHET IMMOBILIER SERVICES ·
10215778 SOCIETE DE GESTION IMMOBILIERE · 10215780 DETROIS IMMOBILIER · 10216239 CABINET MELLIER MICHAS · 10217294
GOUDARD PATOT · 10217295 IMMO DE FRANCE FOREZ VELAY ; `nom` et `prenom` restent vides. 10217339 (sans nom nulle part)
non relancé : « Contact 10217339 ».
⏰ **Contrôle du 06/11 au matin** : la nuit garde ces 8 noms (la couche entière est refaite) et 10217339 reste présent.

## 20. D-2 « MODIFIER UN PARTENAIRE » — AUDIT COMPLÉTÉ (05/11, « OK » pour attaquer D-2) — rien codé

**Lecture seule chez Hektor** (GET du formulaire d'édition, 3 fiches) : il y a **DEUX** formulaires de partenaire, pas un :
- **partenaire PERSONNE** — groupe `mefContacts/contacts_full_accueil_partenaire` : civilite, nom, prenom, metier,
  téléphones, e-mails, localité, adresse, naissance, commentaires… (GIBERT IMMOBILIER 414566 en est un, nom VIDE) ;
- **partenaire SOCIÉTÉ** — groupe `mefContacts/partenaireMoraleInfo` : sociale, juridique, siret, metier, url, logo,
  téléphones, e-mails, localité, adresse, commentaires — **pas de `nom`** (FONCIA LOIRE AUVERGNE 423684, ACTIV'
  EXPERTISES 56169).
⚠ **Correction du §18 ter** : pour une vraie SOCIÉTÉ, l'API rend la raison sociale dans `nom` (423684 : `nom` = « FONCIA
LOIRE AUVERGNE »). C'est GIBERT qui est une fiche PERSONNE sans nom. Et l'API ne distingue pas les deux (56169, société,
sort avec civilité « M. » et prénom « Franck ») : **seul le formulaire relu dit la sorte de fiche**.
**Le worker** (`updateHektorContactIdentity`) ne connaît que `contacts_full_accueil` et `contactCoupleAll` ; il filtre le
formulaire sur ce groupe (`extractHektorFormValues`, égalité stricte) ⇒ 0 champ ⇒ « introuvable ». Les DEUX sortes de
partenaire échouent. Et même relu, une société n'a pas de `nom` : la garde actuelle la refuserait encore.
**La fenêtre « Modifier le contact »** (`ContactEditModalV2`, App.tsx) envoie toujours `person_type` personne seule,
`companyName` vide, et préremplit le nom par `contact.nom || contact.display_name` ⇒ ⚠ sur une fiche SANS nom, enregistrer
écrirait chez Hektor le nom AFFICHÉ — y compris un nom fabriqué « Contact N » (défaut dormant : 0 cas à ce jour).
**Mesure Supabase (05/11)** : 14 772 contacts de l'app portent la typologie partenaire ; 2 563 sans nom ni prénom, dont
242 au nom fabriqué ; 3 794 noms fabriqués en tout. 29 modifications de contact depuis juin (27 faites, 2 erreurs),
**0 sur un partenaire** et 0 avec un nom fabriqué : rien d'abîmé.
**Remède proposé** : A worker — reconnaître les 4 groupes par le formulaire relu (celui qui porte `nom` ou `sociale`) ;
société ⇒ le nom part dans `sociale`, civilité / prénom ignorés, le reste relu ne bouge pas ; personne seule et couple
inchangés. B fenêtre — ne jamais préremplir le nom avec « Contact N ». C fenêtre « société » (raison sociale, forme,
SIRET) = lot 3. ⚠ Le POST `contacts-saveDataEditContact` avec ces deux groupes n'est PAS prouvé : essai réel sur fiches
d'essai (accord), puis redémarrage des 4 services file vide (accord).

✅ **A ET B CODÉS le 05/11** (« Oui, vas-y ») — **rien n'est actif tant que les 4 services ne sont pas redémarrés et
l'interrupteur allumé** :
- **A, worker** (`console_job_worker.js`) : `hektorContactFormGroup(html, { partenaires })` reconnaît
  `contacts_full_accueil_partenaire` et `partenaireMoraleInfo` (le couple d'abord, puis la société, puis la personne) ;
  `updateHektorContactIdentity` exige `sociale` pour une société, la passe en statut 3 (le nom saisi part dans
  `sociale`), et retire de son envoi les champs de personne qu'elle n'a pas (civilite, nom, prenom, dateNaissance,
  lieuNaissance, marital_status) ; le compte rendu porte `formulaire`. La modification d'un MANDANT n'est pas touchée.
  ⛔ **Interrupteur `app_setting` « contact_partenaire_modif »** (absent = éteint ; lecture ratée = éteint).
- **Essais** : `Console/test_partenaire_modification.js` **17/17** (témoins éteint, seul et couple inchangés ; métier,
  forme juridique, SIRET, site et commentaire gardés ; aucun champ de personne ajouté à une société) ;
  `test_couple_modification.js` vert (le contrôle (9) accepte le 2e argument) ; `test_couple_seconde_fiche.js` vert.
  ⚠ `test_porte_contacts.js` : **2 échecs DÉJÀ PRÉSENTS avant ce changement** (vérifié sur le worker de HEAD) — « les
  mandants d'une création d'annonce sont traduits », « AUCUN filtre ne jette plus un numéro d'app en silence ». Hors D-2.
- **B, écran** (`App.tsx`, `contactIdentityInputFromContact`) : le nom proposé n'est plus jamais « Contact N » (case vide,
  l'enregistrement demande un nom) ; les deux fenêtres de modification en profitent ; les recherches n'utilisent que le
  type. Pas d'interrupteur (une case vide au lieu d'un nom fabriqué). `npm run build` vert. ⚠ **Pas vu à l'écran** :
  l'aperçu local n'a pas de session ; à voir à l'essai réel.
- ⚠ Commit du worker : SEULS ces morceaux (l. ~19 370-19 465) ; le worker portait aussi des changements Youtrust d'une
  autre session, NON commités par moi.
**Reste, chacun sur accord** : pousser ; redémarrer les 4 services (file vide) ; poser `contact_partenaire_modif = on` ;
essai réel sur deux fiches d'essai (un partenaire personne, un partenaire société) : modifier le téléphone, relire le
formulaire chez Hektor, puis supprimer les fiches.
✅ **Poussé** (fab36af en ligne, poussé avec 0d267bb et 463c11a par une autre session). ✅ **Les 4 services redémarrés par
Frédéric le 05/11 à 10:24:37-39** (cette session n'a pas les droits d'administrateur : `Restart-Service` refusé, même avec
`-Force`) ; file vide avant ; numéros 18476/13496/15524/6912 → 5248/19604/17796/17088 ; journaux sans erreur ; le fichier
chargé porte le correctif. La session Youtrust avait confirmé que ses morceaux non commités du worker sont prêts et dorment
derrière `signature_youtrust` = off. **L'interrupteur `contact_partenaire_modif` reste ÉTEINT.**

✅✅ **ALLUMÉ ET PROUVÉ EN RÉEL le 05/11** (« Oui, vas-y ») :
- `app_setting.contact_partenaire_modif = on` posé à 10:26:38 (retour arrière : `off`).
- Deux fiches d'essai créées par l'écran (Contacts → Nouveau contact), compte formation, e-mail RGPD décoché :
  **ZZ ESSAI SOCIETE BIENVU** (20000039 / Hektor 606216, personne morale, SARL, métier Syndic, tél. 0499999901 — le
  0400000000 du 04/11 déclenchait un « doublon possible » avec un vrai contact) et **M. Bienvu ZZ ESSAI PARTENAIRE
  PERSONNE** (20000040 / 606217, personne physique, Diagnostiqueur, 0499999902). Relu en GET : 606216 porte
  `partenaireMoraleInfo`, 606217 `contacts_full_accueil_partenaire` — exactement la mesure du §20.
- Téléphone changé par « Modifier le contact » (0499999911 / 0499999912, RGPD décoché) ; envoi à 10:42-10:44 :
  **2 travaux `update_hektor_contact` FAITS, 0 erreur** ; compte rendu `formulaire` = le bon groupe pour chacun ; la
  société part en statut 3. **Relu chez Hektor** : raison sociale « ZZ ESSAI SOCIETE BIENVU » et SARL intactes ;
  civilité M., nom, prénom intacts ; le NOUVEAU numéro est bien chez Hektor. ⇒ **D-2 RÉPARÉ** (avant : « introuvable »).
- ⚠⚠ **DÉFAUT D-5 TROUVÉ, ANCIEN, HORS D-2** : changer un téléphone depuis l'app **AJOUTE une ligne** chez Hektor au
  lieu de remplacer — les 2 fiches ont ancien + nouveau numéro. Cause : `replaceContactTelephoneParams` envoie
  `id_telephone[]` VIDE (donc « nouveau téléphone ») et Hektor garde ceux qu'on ne renvoie pas. Commun à TOUTES les
  modifications de contact depuis juin : **604020 a 5 téléphones** (4 changements depuis l'app, juin et 12/10) ;
  14 modifications avec téléphone depuis juin. **Rien corrigé** : à décider par Frédéric.
- Rappels vus pendant l'essai : D-1 (métier « Non défini » chez Hektor après création, les deux fiches) ; D-4 (RGPD
  coché par défaut dans « Modifier le contact »).
- **Suppression** par l'écran (raison + « SUPPRIMER CONTACT 2000003x ») : 2 travaux `delete_hektor_contact` faits ;
  0 ligne dans `app_contact_current` et `app_contact_pending` ; 2 lignes au journal des suppressions ; formulaire Hektor
  vide (0 octet) pour 606216 et 606217. Onglet Chrome refermé.

## 21. D-5 « LE TÉLÉPHONE S'AJOUTE AU LIEU DE REMPLACER » — AUDIT (05/11, « Oui, audite D-5 ») — rien codé

**Les portes qui écrivent une coordonnée sur un contact EXISTANT** (`console_job_worker.js`) :
- « Modifier le contact » (`updateHektorContactIdentity` → `applyHektorContactIdentityValues`) : téléphone
  (`replaceContactTelephoneParams`), e-mail (`replaceParam id_email[] ""`), et pour un couple téléphone / e-mail du
  conjoint (`id_*_m2[] ""`) — **toutes avec un numéro interne VIDE** ⇒ Hektor crée une ligne et garde les anciennes.
  ⚠ La fenêtre envoie TOUS les champs à chaque enregistrement : même un numéro inchangé est renvoyé « neuf ».
- Modification d'un MANDANT (`updateHektorMandantContact`) : remplace la valeur mais GARDE les `id_*` relus (pas
  d'ajout). ⚠ Non mesuré : avec plusieurs téléphones relus, elle renvoie N numéros internes pour 1 numéro (tableaux
  désalignés) — effet chez Hektor inconnu.
- Les créations (`createHektorContact`, `createHektorMandantContact`) : numéro interne vide = normal (fiche neuve).
**Mesure (lecture seule, 05/11)** : 12 contacts modifiés par « Modifier le contact » depuis juin ; formulaires relus chez
Hektor (comptes, sans valeurs) : 604020 (TEST FERANCKd) **5 téléphones / 4 différents, 2 e-mails** ; 603798 (AVOIR TEST4)
**3 e-mails** ; 603953 (TESTCLAUDE) 2 e-mails identiques ; 605925 (essai 8a) 2 téléphones ; Gladys DURIEUX 113412 : 1 / 1
(rien) ; **les deux seules vraies personnes, M. Loïc GIMBERT 603585 et Mme Annick BRUNON 602945, ont leur numéro 2 fois** —
mais c'est l'ancienne fenêtre (25/06, 21/08) qui envoyait le MÊME numéro en portable ET en fixe, pas l'accumulation.
**Ce que voit l'app** : l'API ne rend qu'UN portable, UN fixe, UN e-mail (`coordonnees`), le plus récent de chaque sorte
(604020 : portable = le dernier envoyé) ⇒ la nuit ramène le bon numéro, **l'app est juste** ; les lignes en trop vivent
**chez Hektor seulement** (sa fiche, et tout ce que Hektor envoie lui-même : non mesuré).
**Remède proposé** : pour le portable, le fixe, l'e-mail (et le conjoint), renvoyer le numéro interne de la ligne relue
du même type (`label_telephone[]` portable / fixe, première ligne e-mail) avec la nouvelle valeur ; aucune ligne relue
⇒ ligne neuve (comme aujourd'hui) ; les autres lignes relues renvoyées telles quelles. Interrupteur app_setting proposé
`contact_coordonnees_remplacer`. Essai réel sur fiche d'essai (accord), redémarrage des 4 services (Frédéric).
**Ménage** : rien d'urgent — les fiches à lignes multiples sont des fiches d'essai ; GIMBERT et BRUNON = un numéro en
double (portable + fixe), à laisser ou à corriger à la main chez Hektor (décision de Frédéric).

✅ **CODÉ le 05/11** (« Oui, vas-y ») — **rien n'est actif tant que les 4 services ne sont pas redémarrés et
l'interrupteur allumé** :
- `console_job_worker.js` : `lignesCoordonnees` / `poserCoordonnee` / `ecrireLignesCoordonnees` / `remplacerCoordonnee` ;
  `applyHektorContactIdentityValues(values, contact, { remplacer })` — allumé, le portable, le fixe, l'e-mail et le
  conjoint (`_m2`) remplacent la **DERNIÈRE** ligne relue de leur sorte (celle que l'API rend, donc celle que l'app
  affiche) avec son numéro interne ; aucune ligne de la sorte = ligne neuve ; une valeur vide ne part pas ; les autres
  lignes repartent telles quelles. Seule la MODIFICATION passe l'option ; la création ne change pas. Compte rendu :
  `coordonnees` = « remplacees » / « ajoutees ».
- Libellés mesurés en GET sur 604020 : `label_telephone[]` = select portable|fixe|bureau|fax ; `label_email[]` = « email ».
- ⛔ **Interrupteur `app_setting` « contact_coordonnees_remplacer »** (absent = éteint ; lecture ratée = éteint).
- Essais : `Console/test_coordonnees_remplacer.js` **17/17** (témoins éteint ; forme de 604020 : 5 lignes avant et après,
  le dernier portable remplacé, les 4 autres intactes et dans l'ordre ; fixe ; e-mail ; aucune ligne ; valeur vide ;
  conjoint ; la création non touchée) ; partenaires 17/17, couples verts.
**Reste, chacun sur accord** : pousser ; redémarrage des 4 services par Frédéric (file vide) ; poser
`contact_coordonnees_remplacer = on` ; essai réel sur une fiche d'essai (changer téléphone ET e-mail, relire TOUTES les
lignes chez Hektor : même nombre, nouvelle valeur), puis la supprimer.

✅✅ **ALLUMÉ ET PROUVÉ EN RÉEL le 05/11** (« Oui, vas-y », puis « C'est redémarré ») :
- Les 4 services redémarrés par Frédéric à **11:05:30-32** (journaux sans erreur ; fichier chargé = commit 2fca55b, rien
  d'autre). `app_setting.contact_coordonnees_remplacer = on` posé à **11:05:51** (retour arrière : `off`).
- Fiche d'essai par l'écran : **M. Bienvu ZZ ESSAI COORDONNEES** (20000043 / Hektor 606222, partenaire personne, compte
  formation, RGPD décoché). Relue AVANT : 1 portable (n° interne 449901, 0499999921) et 1 e-mail (449902,
  essai.d5.avant@example.invalid).
- Modifiée par « Modifier le contact » : portable 0499999931 ET e-mail essai.d5.apres@example.invalid (RGPD décoché) ;
  envoi à 11:18:51, travail **fait à 11:19:18**, compte rendu `coordonnees` = « remplacees ».
- **Relue APRÈS chez Hektor : 1 portable (449901 → 0499999931), 1 e-mail (449902 → essai.d5.apres@…)** : mêmes numéros
  internes, nouvelles valeurs, **aucune ligne ajoutée**. ⇒ **D-5 RÉPARÉ.**
- Supprimée par l'écran : travail fait, 0 ligne dans `app_contact_current` / `app_contact_pending`, 1 ligne au journal
  des suppressions, formulaire Hektor vide (0 octet). Onglet Chrome refermé.
- ⚠ Non éprouvé en réel : le fixe et le conjoint (`_m2`) — couverts par les essais hors ligne (9) et (14) seulement.
- Ménage NON fait (décision de Frédéric) : les lignes en trop des fiches d'essai (604020…) et le numéro en double de
  GIMBERT 603585 / BRUNON 602945.

## 22. D-1 « LE MÉTIER D'UN PARTENAIRE CRÉÉ DANS L'APP EST PERDU » — AUDIT (05/11, « enchaîne D1 ») — rien codé

**Ce qui est déjà tranché** : D2 (04/11, Frédéric) — le métier et les liens vivent **chez nous seulement**, rien ne part
chez Hektor pour ce chantier ; recommandation acceptée : « ne rien changer à la création » (le chemin Hektor existe et il
est prouvé). ⇒ D-1 ne se répare PAS chez Hektor (son métier « Non défini » est sans conséquence pour nous) : il faut que
**notre registre** (`app_partenaire_metier`) reçoive le métier choisi à la création.
**Ce qui existe** : `app_partenaire_metier_ecrire(p_contact, p_metier, p_retirer)` (lot 2, SECURITY DEFINER, compte
actif exigé, source « ecran », trace de l'auteur) — **appelée par personne**. La nuit (`registre_partenaires_reprise.py`)
n'AJOUTE que ce qui manque et **ne retire jamais un métier** ⇒ une ligne « ecran » survit.
**Le trou** : la création (`app_create_contact_optimistic`, 9 237 caractères, empreinte `278d5570…`) range la charge
(dont `partner_job_id`) dans le travail `create_hektor_contact` et la fiche provisoire, mais n'écrit **rien** au registre ;
le worker envoie `metier` à Hektor, qui l'ignore.
**Mesure (05/11)** : depuis juin, **3** créations de partenaire avec métier, toutes mes fiches d'essai (20000038,
20000039, 20000040), supprimées ⇒ **0 vraie fiche touchée**, le défaut dort.
**Correspondance code Hektor → métier du registre** (celle de la nuit, `METIER_HEKTOR`) : 1 promoteur, 3 et 22
agent_immobilier, 4 diagnostiqueur, 5 syndic, 8 et 18 societe, 15 apporteur, 17 administration, 19 banque, 20
mandataire, 21 autre, 23 technicien ; + 2 notaire et 6 autre ; **7 Collaborateur et 16 « À supprimer » : rien d'écrit**.
**Remède proposé (A, recommandé)** : un déclencheur ADDITIF sur `app_console_job`, seulement à l'insertion d'un travail
`create_hektor_contact` dont la charge porte `partner_job_id` et `app_identite` : il écrit la ligne du registre (source
« ecran », auteur = celui qui crée), dans la MÊME transaction que la création ; la grosse fonction de création n'est pas
touchée ; toutes les portes de création sont couvertes. Il ne doit JAMAIS faire échouer une création (une erreur est
écrite au journal, pas levée). Interrupteur app_setting proposé `partenaire_metier_a_la_creation`. Patch + répétition +
inverse, collés sur accord. **B** (autre forme) : l'écran appelle `app_partenaire_metier_ecrire` juste après la création
(code du front, déploiement Vercel ; une seconde porte de création l'oublierait).
**Vu en passant (non traité)** : supprimer un contact ne retire pas ses lignes du registre (le nettoyage de
`delete_hektor_contact` ne connaît pas `app_partenaire_metier`) — à décider.

✅ **REMÈDE A ÉCRIT ET RÉPÉTÉ le 05/11** (« Oui, vas-y (A) ») — **rien n'est posé chez Supabase** :
- `supabase/patch_partenaire_metier_creation_2026-11-05.sql` : interrupteur `partenaire_metier_a_la_creation` posé
  « off » ; fonction `app_partenaire_metier_a_la_creation_trg()` (SECURITY DEFINER, fermée à anon et authenticated) ;
  déclencheur AFTER INSERT sur `app_console_job` WHEN `job_type = 'create_hektor_contact'`. Il n'écrit que pour
  `contact_kind = partenaire` avec `partner_job_id` et `app_identite` ; source « ecran », auteur = `requested_by` ;
  pas de doublon ; une erreur = WARNING, la création n'échoue jamais. Gardes : n'existe pas déjà, empreintes des deux
  contrôles (`0d785740…` métier, `e322ef89…` source). Modèle : `app_contact_saisie_modif_job_trg` (8a-B).
- `…_INVERSE.sql` : retire déclencheur, fonction, interrupteur ; vérifie qu'aucune trace ne reste et que les deux
  déclencheurs voisins de `app_console_job` sont là. Les lignes déjà écrites RESTENT (vrais métiers).
- `…_REPETITION.sql` (générée depuis les deux) : **26 / 26 essais verts**, joués chez Supabase à 11:3x dans une
  transaction annulée (témoin éteint ; syndic ; pas de doublon ; 2e métier ; 7, 16, inconnu → rien ; acquéreur ou sans
  type → rien ; une MODIFICATION → rien ; sans numéro ou sans métier → rien ; les 13 codes de la correspondance un par
  un ; 26 travaux créés ; registre qui refuse → le travail est créé quand même ; `app_create_contact_optimistic` intacte
  `278d5570…` ; fonction fermée ; retour arrière complet). Vérifié après : 0 déclencheur, 0 fonction, 0 interrupteur,
  0 ligne et 0 travail d'essai.
**Reste, chacun sur accord** : coller le patch ; allumer ; essai réel (créer un partenaire avec un métier depuis l'écran,
lire sa ligne au registre, supprimer la fiche — et décider du sort de sa ligne au registre, voir « vu en passant »).

✅✅ **POSÉ, ALLUMÉ ET PROUVÉ EN RÉEL le 05/11** (« Oui, vas-y ») :
- Patch collé comme migration `partenaire_metier_a_la_creation_2026_11_05` ; contrôlé : déclencheur présent (AFTER INSERT,
  WHEN create_hektor_contact), interrupteur « off », fonction fermée à anon et authenticated, 3 déclencheurs sur
  `app_console_job`, `app_create_contact_optimistic` inchangée (`278d5570…`).
- `partenaire_metier_a_la_creation = on` à **11:51:21**.
- Fiche d'essai par l'écran : **ZZ ESSAI METIER SYNDIC** (20000044 / Hektor 606232, société SARL, métier Syndic, compte
  formation, RGPD décoché). **Registre : ligne 1890 « syndic / ecran » écrite à 11:52:27.374756, la même micro-seconde
  que le travail de création, auteur = celui qui crée.** Le travail Hektor est fait à 11:52:43.
- Supprimée par l'écran (travail fait, 0 ligne dans `app_contact_current`, journal des suppressions 1, formulaire Hektor
  vide) ; puis **ligne 1890 retirée en la datant** (`retire_le` 11:53:56, `retire_par` = l'auteur), pas effacée.
- Registre après : **1 869 actifs, dont 1 656 notaires** (inchangé) ; 1 ligne « ecran » au total, 0 active.
- ⚠ Toujours ouvert (« vu en passant ») : supprimer un contact ne retire pas ses lignes du registre ; ici retiré à la main.

## 23. SUPPRIMER UN CONTACT LAISSE SES LIGNES AU REGISTRE DES PARTENAIRES — AUDIT (05/11, « Oui, audite-le ») — rien codé

**La suppression aujourd'hui** (`handleDeleteHektorContact`, `console_job_worker.js` ~l. 22046) : Hektor, puis le
nettoyage Supabase (`app_proposition`, `app_bien_acquereur_statut`, `app_contact_search_current`,
`app_contact_relation_current`, `app_contact_duplicate_member_current`, `app_contact_current` + les clés de recherche),
la base locale (`delete_local_contact.py`), et le registre des LIENS `app_relation` — **effacé physiquement**, décision de
Frédéric du 08/10 (5g : « je veux que les lignes soient physiquement effacées », exception assumée au « jamais effacer »).
**Rien pour le registre des PARTENAIRES** : `app_partenaire_metier` et `app_partenaire_lien` gardent leurs lignes actives.
Or ce registre a été posé le 04/11 avec la règle inverse : **on retire en datant, on n'efface jamais**.
**Mesure (05/11)** : 1 869 métiers actifs, dont **257 sur un contact absent de l'app** (hektor 53, transactions 204) —
**aucun** ne vient d'une suppression (0 contact du journal des suppressions) : ce sont les notaires hors périmètre de l'app
(le trou de `console_transaction_party`, §17 bis). 83 liens actifs, 0 sur un contact absent. 40 suppressions au journal
depuis le début. ⇒ **Aucun cas réel aujourd'hui** ; la fiche d'essai 20000044 a été retirée à la main.
**⚠ Un second trou, plus important pour le lot 3** : la nuit (`registre_partenaires_reprise.py`) compare ce qu'elle
« veut » aux seules lignes ACTIVES ⇒ un métier RETIRÉ (par une suppression, ou demain par « Retirer le métier » à l'écran)
est **RAJOUTÉ la nuit suivante** si une source le veut encore (Netty, Hektor, table des parties). Pour un contact supprimé,
Netty et Hektor passent par la couche locale (le contact n'y est plus) ; la table des parties, non mesuré.
**Remède proposé** :
1. Worker, à la suppression (après le registre des liens) : RETIRER EN DATANT les métiers actifs du contact et ses liens
   actifs (comme partenaire ou comme client), `retire_par` = celui qui supprime ; compte rendu et journal comme pour
   `app_relation`. Interrupteur app_setting proposé `partenaire_retire_a_la_suppression`. (Autre forme : effacer
   physiquement, comme `app_relation` le 08/10 — ⚠ contraire à la règle du registre des partenaires : à trancher.)
2. Nuit : **un métier déjà retiré pour ce contact n'est jamais rajouté** (un retrait humain fait foi) ; les liens d'origine
   « hektor » gardent leur logique (Hektor peut remettre un syndic). Derrière l'interrupteur de la nuit déjà allumé
   `APP_REGISTRE_PARTENAIRES`, ou un second — à présenter.
Ce que ça pourrait casser : un métier retiré PAR ERREUR ne reviendrait plus tout seul (il faudrait le remettre à la main) ;
la suppression gagne 2 requêtes Supabase, sans toucher à Hektor ni au reste du nettoyage.

✅ **DÉCISION DE FRÉDÉRIC (05/11) : « Effacer »** — à la suppression d'un contact, ses lignes du registre des partenaires
(métiers, et liens où il est partenaire ou client) sont **EFFACÉES physiquement**, comme `app_relation` depuis le 08/10.
Exception assumée à la règle « on retire en datant » du registre ; la trace reste dans le journal du travail et dans
`app_console_deleted_contact_log`. ⇒ Remède 1 révisé : DELETE au lieu de PATCH. Remède 2 réduit : la nuit ne rajoute pas
un métier pour un contact du journal des suppressions ; « un retrait à l'écran fait foi » est reporté au lot 3 (A3).

✅ **CODÉ le 05/11** (« Oui, vas-y ») — rien n'est actif côté worker tant que les 4 services ne sont pas redémarrés et
l'interrupteur allumé :
- **Worker** (`handleDeleteHektorContact`, juste après le registre des liens) : EFFACE `app_partenaire_metier` du contact
  (`contact_id` = notre numéro) et `app_partenaire_lien` où il est `partenaire_id` OU `client_contact_id` (DELETE avec
  `return=representation`, pour compter) ; compte rendu `cleanup.registre_des_partenaires` et journal du travail ; une
  erreur va dans `cleanup.errors` et au journal, la suppression continue ; aucune requête vers Hektor. Nouvel outil
  `interrupteurAppSetting(cle)`. ⛔ **Interrupteur `app_setting` « partenaire_efface_a_la_suppression »** (absent = éteint).
- **Nuit** (`registre_partenaires_reprise.py`) : `contacts_supprimes()` lit le journal des suppressions (notre numéro,
  `app_contact_id` ou `before_json.hektor_contact_id`) ; `ecarter_les_supprimes()` les retire de ce qui est VOULU (métiers
  et liens) — pas seulement de ce qui est ajouté, la vérification finale comparant à tout le voulu. Compte rendu :
  `contacts_supprimes_ecartes`. Sans interrupteur à part (il n'empêche que des lignes pour des contacts qui n'existent
  plus) : actif dès la nuit du 05 au 06/11, sous `APP_REGISTRE_PARTENAIRES`.
- Essais : `Console/test_partenaire_suppression.js` **11/11** ; `phase2/contacts/test_registre_partenaires_supprimes.py`
  **5/5** ; avec les essais voisins, 31 verts en Python ; D-5, D-2 et couples toujours verts.
- **À blanc sur la base réelle (05/11)** : 29 contacts supprimés lus au journal ; `contacts_supprimes_ecartes` = 0 ;
  métiers voulus 1 870, déjà là 1 869, 1 à ajouter (un notaire neuf des transactions) ; 83 liens, 0 à ajouter / retirer.
**Reste, chacun sur accord** : redémarrage des 4 services (Frédéric) ; `partenaire_efface_a_la_suppression = on` ; essai
réel (créer un partenaire avec métier → 1 ligne au registre → le supprimer → 0 ligne, compte rendu « done »).

✅✅ **§23 ALLUMÉ ET PROUVÉ EN RÉEL le 05/11** (« Oui, vas-y », puis « C'est redémarré ») :
- 4 services redémarrés par Frédéric à **12:37:05-07**, journaux sans erreur, mon code chargé.
  ⚠ **Le fichier chargé portait AUSSI un changement NON commité de la session Youtrust** (modifié à 12:36:38) : la règle
  D-5 étendue à `updateHektorMandantContact` (lot 6b P3). L'interrupteur `contact_coordonnees_remplacer` étant « on »,
  **ce changement est ACTIF depuis 12:37** pour toute modification de mandant. Pas à moi : signalé à Frédéric et à la
  session Youtrust (message envoyé), non touché.
- `partenaire_efface_a_la_suppression = on` à **12:37:48**.
- Fiche d'essai par l'écran : **ZZ ESSAI SUPPRESSION REGISTRE** (20000045 / Hektor 606235, SARL, Syndic) → ligne 1891
  « syndic / ecran » au registre (D-1). Supprimée par l'écran → travail fait ; compte rendu
  `cleanup.registre_des_partenaires = {status: done, metiers_effaces: 1, liens_effaces: 0}` ; **0 ligne pour 20000045** ;
  0 fiche ; journal des suppressions 1 ; formulaire Hektor vide. Registre : **1 869 actifs** (inchangé).

## 24. LOT 3 — LA PAGE PARTENAIRE : AUDIT ET DÉCOUPAGE (05/11, « ok donc on enchaîne ») — rien codé

**Ce qui existe** :
- le design validé (§6.3, `maquettes/fiche-partenaire-v1.html`, quatre métiers) ; les décisions E1 « a » (Modifier,
  Archiver, Supprimer partent chez Hektor — ✅ réparés et prouvés : D-2, D-5, §23), P1, P2, P4, K8 réglé ;
- la fiche notaire n'est PAS une page à part : ce sont des BLOCS de la fiche contact V2 (`ContactDetailPopupV2`,
  `App.tsx` ~46685 ; `FicheNotaire.tsx`, 549 l.), allumés quand la catégorie dominante est « notaire »
  (`ContactDirectoryType` = notaire | mandant | proprietaire | acheteur | acquereur | autre) ⇒ la page partenaire suit le
  MÊME chemin : des blocs dans la fiche contact, allumés par le MÉTIER du registre ;
- en base : `app_partenaire_metier` et `app_partenaire_lien` lisibles par tout compte actif (RLS `is_app_user_active`) ;
  `app_partenaire_metier_ecrire` et `app_partenaire_lien_ecrire` (jamais appelées par l'écran) ;
  `app_notaire_interlocuteur` (0 ligne) et `app_notaire_interlocuteur_ecrire` ;
- **le front ne lit RIEN du registre aujourd'hui** (0 référence à `app_partenaire_*`).
**Découpage proposé (une pièce à la fois, chacune derrière l'interrupteur, contrôlée bureau / écran bas / téléphone)** :
- **3.1 (A2)** afficher le métier et sa source dans le volet gauche de la fiche contact (« Syndic · Hektor »), pour
  tout contact qui a un métier actif ; lecture seule. Petit, utile tout de suite, et socle des suivantes.
- **3.2 (A3)** « Changer le métier » (ajouter / retirer, `app_partenaire_metier_ecrire`) **+ la garde de nuit « un métier
  retiré à l'écran ne revient pas »** (sinon la nuit défait le retrait, §23) — les deux ensemble.
- **3.3 (K1, K4, K3)** le squelette de la fiche partenaire : chiffres et section du métier « en construction » (ils se
  remplissent aux lots 4 à 7), menu « ⋯ » réduit, zone sensible en bas (Archiver, Supprimer — gestes existants).
- **3.4 (K2)** les interlocuteurs pour tous les partenaires (généraliser `app_notaire_interlocuteur`, vide : rien à
  déplacer) — forme à présenter.
- **3.5 (K6)** l'annuaire des partenaires : la liste par métier, tirée du registre, sur l'annuaire v2.
- **3.6 (K7, K5)** le téléphone et les états chargement / vide / erreur (vérifiés à chaque pièce, finis ici).
- B3 (le sélecteur de partenaire) va au lot 4, avec le bloc « Intervenants du bien » qui l'utilise.
**Interrupteur** : le plan disait `VITE_APP_PARTENAIRES` (Vercel, redéploiement pour allumer). Proposé à la place : un
réglage `app_setting` « partenaires_ecran » (off / admin / on), **comme les couples** (`contacts_couples_*`) — s'allume sans
déploiement, d'abord pour les admins.

✅ **PIÈCE 3.1 CODÉE le 05/11** (« Oui, vas-y 3.1 ») — invisible tant que le réglage n'existe pas :
- `src/lib/metierPartenaire.ts` (règles pures : libellés français, origine « d'après l'ancien logiciel (Netty) » /
  « d'après Hektor » / « d'après ses transactions » / « saisi dans l'app le jj/mm/aaaa », une origine commune dite une
  fois) ; `src/MetierPartenaire.tsx` (`useMetiersPartenaire` lit les lignes ACTIVES du contact par notre numéro, rien
  d'écrit ; `BlocMetierPartenaire` : rien en chargement ou sans métier, une erreur DITE) ; branché dans
  `ContactDetailPopupV2` (crochet `useCranCouplesVisible('partenaires_ecran')`, bloc sous le statut du volet gauche, comme la
  maquette) ; style `.fa-cx-metier` (+ mode sombre) dans `contact-detail-v2.css`.
- Essais : `test_metier_partenaire.cjs` **15/15** ; `test_fiche_notaire.cjs` vert ; `npm run build` vert.
- ⚠ Incident évité : la session Youtrust avait emporté mes 5 lignes d'`App.tsx` dans son commit de la signature (P4) ;
  défait par elle avant tout push (`ac1ae14` refait sans elles). Mes lignes commitées à part.
**Reste** : pousser ; poser `partenaires_ecran = admin` (accord) ; voir le bloc sur une vraie fiche (GIBERT IMMOBILIER
10215568, un courtier Netty, un notaire) au bureau, écran bas et téléphone ; puis « on » pour tous (accord).

✅✅ **3.1 EN LIGNE ET VUE, POUR LES ADMINS (05/11)** (« Oui, vas-y ») :
- Poussé (`7e56422`, avec `ac1ae14`, `d38589a`, `be61445` d'autres sessions) ; déploiement Vercel du commit `be61445`
  prêt vers 13:05 (le paquet contient le bloc) ; `app_setting.partenaires_ecran = admin` à **13:03:48**.
- Vu dans le Chrome de Frédéric (admin), écran 1280 × 665 : **GIBERT IMMOBILIER** (10215568) « Métier · Syndic ·
  D'après Hektor », sous le statut ; **M. Fabrice GUERY** (10001493) « Courtier · Parrain · Notaire · D'après l'ancien
  logiciel (Netty) » ; **M. Rachid RABHI** (10000258) « Notaire · D'après l'ancien logiciel (Netty) » ; un acquéreur
  (10650959) : aucun bloc. Aucun contact de l'app n'a deux métiers d'origines différentes (cas couvert par l'essai (7)).
- Téléphone : la fenêtre de Chrome refusant de se redimensionner, même fiche ouverte dans un cadre de 390 px (même
  session) : bloc à 15-356 px, **aucun débordement**, sous le statut.
- Non vu : le mode sombre au téléphone (règles posées) ; un compte NON admin (le cran « admin » le cache, par construction
  du crochet des couples).
✅ **`partenaires_ecran = on` le 05/11 (« Oui, pour tous »)** : le bloc « Métier » est visible pour tout le monde
(un réglage, effet au rechargement de la page). Retour arrière : `admin` ou `off`. **Suite : la pièce 3.2.**

## 25. LOT 3, PIÈCE 3.2 — « CHANGER LE MÉTIER » : AUDIT (05/11, « Oui, audite 3.2 ») — rien codé

**La maquette** (`fiche-partenaire-v1.html`) place le geste à deux endroits — un bouton « Changer » dans le bloc métier
(l. 809) et « Changer le métier » dans le menu « ⋯ » (l. 784) — mais **la fenêtre n'a jamais été dessinée**.
**L'écriture existe** : `app_partenaire_metier_ecrire(p_contact, p_metier, p_retirer)` (empreinte `02baca86…`) —
SECURITY DEFINER, exige un compte actif ; ajoute (source « ecran », `confirme_par` / `ecrit_par` = l'auteur), CONFIRME un
métier déjà actif (`confirme_le`), ou RETIRE en datant (`retire_le`, `retire_par`) ; ouverte à `authenticated`, fermée à
`anon`. Le bloc de la 3.1 sait déjà se relire (`useMetiersPartenaire`).
**Les droits** : à l'écran, « Modifier la fiche » est montré à admin, manager et commercial (`canManageContacts`) ; la
fonction accepte tout compte actif. Aujourd'hui 6 comptes actifs (4 admin, 2 commercial).
**La nuit** (`registre_partenaires_reprise.py`) ne compare qu'aux lignes ACTIVES : un métier retiré à l'écran serait
**RAJOUTÉ** la nuit suivante si Netty, Hektor ou les transactions le « veulent » encore. Mesure : 1 seule ligne retirée en
base (1890, la fiche d'essai 20000044, supprimée et au journal) ⇒ **aucun retrait réel à protéger aujourd'hui**.
**Remède proposé** :
1. **Fenêtre « Métier du contact »** — à DESSINER d'abord (maquette, comme « Ajouter un conjoint » le 03/11) : les
   métiers actifs avec leur origine et « Retirer », la liste des autres métiers à ajouter, un seul « Enregistrer » ;
   ouverte par « Changer » (bloc) et par « ⋯ › Changer le métier » (y compris pour un contact SANS métier : c'est la
   seule façon d'en faire un partenaire). Droits : comme « Modifier la fiche » (recommandé).
2. **Garde de nuit** : un couple (contact, métier) dont une ligne a été retirée PAR QUELQU'UN (`retire_par` rempli) et qui
   n'a pas de ligne active n'est **jamais rajouté** ; compte rendu `metiers_retires_ecartes`. Le retrait humain fait foi ;
   le remettre = le rajouter à l'écran.
3. **Interrupteur à part** `partenaires_metier_modif` (admin, puis on) — le bloc de lecture (3.1) est déjà ouvert à tous.
Ce que ça pourrait casser : un métier retiré par erreur ne revient plus tout seul ; un commercial peut changer le métier
de n'importe quel contact (trace de l'auteur gardée) ; rien chez Hektor.

✅ **« Oui, vas-y » (05/11) — garde de nuit CODÉE, fenêtre DESSINÉE ; la fenêtre n'est PAS codée (attend sa validation)** :
- **Garde de nuit** (`registre_partenaires_reprise.py`) : `metiers_retires_par_quelquun()` (lignes `retire_le` ET
  `retire_par` remplis) ; `ecarter_les_retires()` les retire de ce qui est VOULU sauf s'ils ont été remis (ligne active) ;
  compte rendu `metiers_retires_ecartes`. Sous `APP_REGISTRE_PARTENAIRES`, active dès la nuit du 05 au 06/11. Essais :
  `test_registre_partenaires_supprimes.py` **10/10** (+5). À blanc sur la base : `metiers_retires_ecartes` = 0 (le seul
  retrait, 1890, est la fiche d'essai supprimée), comptes inchangés (1 870 voulus, 1 869 là).
- **Maquette** `maquettes/fenetre-metier-v1.html` (données FICTIVES ; famille « Ajouter un conjoint ») : en-tête « Métier
  du contact » ; « Ses métiers » avec l'origine et « Retirer » (barré + « Garder » une fois marqué) ; « Ajouter un
  métier » en pastilles (les six métiers du chantier d'abord, en gras) ; une note « vit chez nous, ne revient pas avec
  la nuit » ; un bilan « 1 ajout · 1 retrait » et « Enregistrer » grisé sans changement ; cas sans métier (« pour en faire
  un partenaire »). Contrôlée : bureau, écran bas 1280 × 665 en sombre (corps qui défile, boutons toujours visibles —
  corrigé après un premier essai qui dépassait de 3 px et des boutons restés blancs), téléphone 375 × 812 (volet du bas,
  aucun débordement).

✅ **FENÊTRE CODÉE le 05/11** (« oui code-la ») — invisible tant que le cran n'existe pas :
- `src/MetierPartenaire.tsx` : `FenetreMetierPartenaire` (portail, Échap et clic dehors ferment ; « Enregistrer » envoie
  les RETRAITS puis les AJOUTS, un par un, par `app_partenaire_metier_ecrire` ; une erreur au milieu : ce qui est passé est
  relu, l'arrêt est dit) ; `useMetiersPartenaire` sait se relire (`recharger`) ; le bloc reçoit un bouton « Changer ».
- `src/lib/metierPartenaire.ts` : `METIERS_ORDONNES` (18, les six du chantier d'abord) et `planDesChangements` (ne retire
  que l'actif, n'ajoute pas l'actif, ignore l'inconnu et les doublons).
- `src/metier-partenaire.css` (la maquette, en `.mtp-*` ; sombre sous 1180 px comme la fiche) ; bouton « Changer » dans
  `contact-detail-v2.css`.
- Branché dans `ContactDetailPopupV2` : **deux portes** — « Changer » du bloc et « ⋯ › Changer le métier » (la seule pour
  un contact SANS métier) ; visible si `partenaires_ecran` ET **`partenaires_metier_modif`** (nouveau cran, admin / on)
  ET `canManageContacts` (admin, manager, commercial — comme « Modifier la fiche ») ET lecture prête.
- Essais : `test_metier_partenaire.cjs` **27/27** ; `test_fiche_notaire.cjs` vert ; `npm run build` vert.
**Reste** : pousser ; poser `partenaires_metier_modif = admin` ; essai réel sur une fiche d'essai (ajouter, retirer, relire
le registre) ; voir les trois formats ; puis « on » pour tous (accord).

✅✅ **3.2 EN LIGNE ET PROUVÉE EN RÉEL, POUR LES ADMINS (05/11)** (« Oui, vas-y ») :
- Poussé (`1cc4b88`, `957d489`) ; déploiement Vercel prêt vers 14:26 (le paquet contient `partenaires_metier_modif`) ;
  `app_setting.partenaires_metier_modif = admin` à **14:25:01**.
- Fiche d'essai **M. AVOIR TEST4** (10354488, aucun métier) dans le Chrome de Frédéric, écran 1280 × 665 :
  « ⋯ › Changer le métier » présent ; fenêtre entière à l'écran ; « Syndic » choisi → bilan « 1 ajout » → Enregistrer →
  fenêtre fermée, bloc relu « Syndic · Saisi dans l'app le 05/11/2026 · Changer » ; registre : ligne **1892** syndic /
  ecran, écrite à 14:27:12 par frederic.gerphagnon@… ; puis « Changer » → « Retirer » (barré, « 1 retrait ») →
  Enregistrer → bloc disparu ; ligne 1892 **retirée et datée** 14:27:53 par frederic.gerphagnon@… (pas effacée).
- Téléphone (cadre de 390 px, même session) : la fenêtre ouverte par le menu est un volet du bas, boutons visibles, aucun
  débordement ; fermée sans enregistrer.
- Non vu : le mode sombre au téléphone (règles posées) ; un compte non admin (caché par le cran).
✅ **`partenaires_metier_modif = on` le 05/11 (« Oui, pour tous »)** : la fenêtre est ouverte à tout compte qui peut
gérer les contacts (admin, manager, commercial). Retour arrière : `admin` ou `off`. ⏰ **Contrôle du 06/11** : la nuit
garde 1892 retirée (`metiers_retires_ecartes`, et aucune ligne active syndic pour 10354488). **Suite : pièce 3.3.**

## 26. LOT 3, PIÈCE 3.3 — LE SQUELETTE DE LA FICHE PARTENAIRE : AUDIT (05/11, « Oui, audite 3.3 ») — rien codé

**La maquette** (`fiche-partenaire-v1.html`) : volet gauche (icône et pastille du métier, action propre au métier en
magenta, coordonnées, interlocuteurs, négociateur, statut, métier) ; travail : quatre chiffres, la section du métier
(étapes, dossiers, pièces), « À venir », deux blocs « avec nous », l'activité, la qualité repliée, et une **zone sensible
en bas** (Archiver, Supprimer). Menu « ⋯ » réduit : Modifier, Changer le métier, Ouvrir dans Hektor.
**Les décisions déjà prises** : P1 « B » (archivée = modifiable, un bandeau « Réactiver ») ; P2 « B » (supprimer : une case
« je comprends » + la raison, plus de texte à taper — le worker exige `SUPPRIMER CONTACT <n>` : la fenêtre l'enverra
elle-même, le geste ne change pas, admin et manager) ; P4 « B » (la fiche CLIENT ne change pas) ; 27/10 pour le notaire :
les blocs sans données sont MONTRÉS, marqués « en construction ».
**La fiche aujourd'hui** (`ContactDetailPopupV2`) : volet (pastilles de type tirées des liens, actions RDV / Modifier / ⋯,
coordonnées, foyer, négociateur, statut, métier 3.1-3.2) ; travail (Recherche & rapprochement — masquée pour un notaire
sans recherche active —, Biens & mandats liés, À faire, Activité, Qualité) ; menu ⋯ : Ouvrir dans Hektor, Changer le
métier, Archiver, Supprimer (fenêtre `ContactWorkflowModal` avec texte à taper).
**Mesure (05/11)** : **202 fiches de l'app** ont un métier actif autre que notaire (syndic 75, diagnostiqueur 36,
apporteur 35, courtier 22, parrain 15, banque 8…) ; dont 10 aussi notaires, **4 avec une recherche active**, **38 avec des
biens liés**, **57 archivées** ; 196 portent déjà la typologie partenaire de Hektor.
**Découpage proposé (trois pièces, même interrupteur à créer `partenaires_fiche`, admin puis on)** :
- **3.3a — le volet** : la pastille du métier (couleur du métier), l'action propre au métier en magenta (désactivée,
  « en construction » jusqu'aux lots 4-7), le menu ⋯ réduit (Modifier, Changer le métier, Ouvrir dans Hektor caché sans
  numéro Hektor), le bandeau « Archivé · Réactiver » (P1).
- **3.3b — le travail** : les quatre chiffres, la section du métier, « À venir » et les deux blocs « avec nous », MONTRÉS
  et marqués « en construction » (règle du 27/10) ; « Recherche & rapprochement » masquée sans recherche active (comme le
  notaire ; les 4 qui en ont la gardent) ; « Biens & mandats liés », Activité et Qualité gardés tels quels.
- **3.3c — la zone sensible** en bas (Archiver, Supprimer, sortis du menu) et la fenêtre de suppression à case à cocher
  (P2), sur la fiche partenaire seulement (P4).
**Quelle fiche devient « partenaire »** (proposé) : un contact qui a un métier actif AUTRE que notaire ; s'il est aussi
classé notaire (10 cas), la fiche notaire existante garde la main.
Ce que ça pourrait casser : 202 fiches changent d'allure (interrupteur, admins d'abord) ; un geste déplacé doit rester
trouvable (Archiver / Supprimer en bas au lieu du menu) ; la fiche client et la fiche notaire ne bougent pas.

✅ **3.3a CODÉE le 05/11** (« Oui, vas-y 3.3a ») — invisible tant que le cran `partenaires_fiche` n'existe pas :
- `lib/metierPartenaire.ts` : `profilDuPartenaire()` — un métier actif autre que notaire ⇒ fiche partenaire ; métier
  principal dans l'ordre de `METIERS_ORDONNES` ; famille (courtier+banque, diag, syndic, apporteur+parrain, autre) ;
  action et lot (syndic « Demander un document » lot 4 ; diag « Commander un diagnostic » lot 5 ; courtier « Orienter un
  acquéreur » et apporteur « Noter une affaire apportée » lots 6 et 7 ; « autre » sans bouton).
- `App.tsx` (`ContactDetailPopupV2`) : `profilPartenaire` = `partenaires_ecran` ET `partenaires_fiche` ET pas fiche notaire
  ET lecture prête ; couleur `ty-<famille>` (`ty-partenaire` pour « autre ») et icône du métier ; pastille du métier avec
  les autres rôles du contact à côté (rien de perdu) ; l'action du métier en magenta, LARGE, **désactivée « bientôt »**
  (règle du 27/10) ; RDV passe en second ; « Modifier la fiche » passe dans le menu ⋯ (K4) ; « Ouvrir dans Hektor »
  caché sans numéro Hektor ; bandeau « Fiche archivée · elle reste modifiable » + « Réactiver » (P1, geste existant).
  Archiver et Supprimer restent dans le menu jusqu'à la pièce 3.3c.
- `contact-detail-v2.css` : couleurs des familles (reprises de la maquette), icônes, bouton large « bientôt », bandeau
  (+ sombre).
- Essais : `test_metier_partenaire.cjs` **39/39** ; `test_fiche_notaire.cjs` vert ; `npm run build` vert.
- ⚠ `App.tsx` portait en même temps des lignes NON commitées de la session Youtrust (lot 6b P6) : **seuls mes morceaux
  commités** (mise en attente morceau par morceau AVEC contexte ; un premier essai sans contexte avait posé un morceau
  28 lignes trop haut — vu par une vérification de la version en attente, refait) ; version en attente vérifiée valide
  sans ses lignes.

✅✅ **3.3a EN LIGNE ET VUE, POUR LES ADMINS (05/11)** (« Oui, vas-y ») :
- Poussé (`7c597e1`, avec `a0df1a4` / `e42a8be` Youtrust et `cd68af6` registre) ; `app_setting.partenaires_fiche = admin`
  à **14:54:34**.
- Vu dans le Chrome de Frédéric (admin), 1280 × 665 : **GIBERT IMMOBILIER** (10215568) violet `ty-syndic`, icône
  d'immeuble, pastille « Syndic », « Demander un document » grisé « bientôt », RDV, ⋯ ; menu : Modifier la fiche, Ouvrir
  dans Hektor, Changer le métier, Archiver, Supprimer (ces deux derniers jusqu'à 3.3c) ; **Michelle BONNET** (10011026,
  archivée) vert `ty-courtier`, pastilles « Courtier » + « Mandant », « Orienter un acquéreur », bandeau « Fiche archivée ·
  elle reste modifiable. Réactiver » ; **M. Franck ACTIV' EXPERTISES** (10030093) ambre `ty-diag`, « Commander un
  diagnostic » ; **PICARD Philippe STE CIVILE** (10177505) gris-bleu `ty-partenaire`, pastilles Société + Mandant +
  Propriétaire, PAS d'action, RDV + ⋯ ; un **acquéreur** (10650959) : inchangé (`ty-acq`, RDV + Modifier + ⋯, pas de bloc).
- ⚠ **Défaut vu en ligne et corrigé** : « Demander un document » était COUPÉ (« Dema… ») — le volet est plus étroit que la
  maquette. Réglé (`fb741de`) : RDV et ⋯ à 40 px, « bientôt » en étiquette sur le coin, pas de « + » sur un bouton
  « bientôt », police 12 px. Essayé d'abord par injection du style dans la page en ligne ; **mesuré : 0 px de dépassement
  pour les quatre libellés** (« Noter une affaire apportée », le plus long, compris). En ligne vers 15:00 : bureau et
  téléphone (cadre 390 px) sans coupure ni débordement.
- Non vu : le mode sombre au téléphone ; un compte non admin (caché par le cran).
✅ **`partenaires_fiche = on` le 05/11 (« Oui, pour tous »)** : les 202 fiches partenaire de l'app prennent leur volet
pour tout le monde (au rechargement). Retour arrière : `admin` ou `off`. **Suite : 3.3b (le travail), puis 3.3c.**

#### 26 bis. PIÈCE 3.3b — LA PARTIE DROITE (05/11, « Oui, vas-y 3.3b ») — codée, commitée `ce654b8`

- **Ce que c'est** : la zone de travail de la fiche partenaire, par famille, avec les libellés de la maquette
  `fiche-partenaire-v1` : **4 chiffres** (valeur « — », jamais un faux zéro), la **section du métier** avec ses étapes
  (« lot N · en construction »), **« À venir »** en tête de la colonne de droite, et les **deux blocs « avec nous »** sous
  le tableau de bord. Syndic (lot 4), diagnostiqueur (lot 5), courtier/banque et apporteur/parrain (lots 6 et 7). La famille
  **« autre »** (société, promoteur…) n'a **rien** de plus : elle garde la fiche d'avant.
- **La bande Recherche** se cache sur une fiche partenaire **à blocs** (les quatre familles) **sans recherche active**,
  comme sur la fiche notaire ; un partenaire qui a une recherche active la garde. ⚠ Corrigé après la mise en ligne : la
  première version la cachait aussi pour « autre » (vu sur PICARD, 10177505) — une société peut être acquéreur. Biens liés, Activité et Qualité restent.
- **Où** : `lib/metierPartenaire.ts` (`blocsDuPartenaire`, données pures), `FichePartenaire.tsx` (4 composants, aucune
  lecture ni écriture, classes de `fiche-notaire-v2.css`), 6 lignes dans `ContactDetailPopupV2`.
- **Cran** : le même que 3.3a (`partenaires_ecran` + `partenaires_fiche`, tous deux à « on ») — ⚠ donc **visible de tous
  dès le déploiement**. Retour arrière : `partenaires_fiche = admin` ou `off`, ou revenir sur `ce654b8`.
- **Contrôles** : `test_metier_partenaire.cjs` **47/47** (8 nouveaux) ; `npm run build` vert ; la version mise en attente
  construite à part (seuls mes morceaux d'App.tsx commités, les lignes des autres sessions laissées en l'état).
- ✅ **Poussé et vu en ligne le 05/11** (`e9c8965`, puis la retouche `b712572` poussée avec 4 commits d'autres sessions,
  « Oui, pousse tout ») : syndic GIBERT IMMOBILIER (10650712), courtier Michelle BONNET (10011026), diagnostiqueur ACTIV'
  EXPERTISES (10030093) à 1280 × 665, rien de coupé ; téléphone (cadre 390 px) : chiffres sur deux colonnes, pas de
  défilement de côté ; PICARD (« autre », 10177505) garde « Recherche & rapprochement » ; un acquéreur (10650959)
  inchangé. Retouche mesurée : 37 px entre la section et le titre suivant (2 px avant).
- Non vu : le mode sombre ; un compte non admin.
- **Suite : 3.3c** (Archiver et Supprimer sortis du menu, suppression avec case à cocher et raison).

#### 26 ter. ⛔ LA PORTE CHOISIT LA FICHE — RÈGLE DE FRÉDÉRIC (05/11, après la mise en ligne de 3.3b)

- **Le défaut** (vu par Frédéric sur PICARD) : 3.3a/3.3b décidaient la fiche d'après le CONTACT (un métier au registre ⇒
  fiche partenaire). Mesure : sur 202 fiches partenaire, **41 sont des clients** — 31 à métier connu (17 mandants,
  16 propriétaires, 2 acheteurs, 3 recherches actives ; ex. Michelle BONNET, courtier + mandante) et 10 « autre »
  (PICARD, « société »). Leur fiche avait changé (couleur, menu, bouton du métier, blocs, Recherche cachée). Affichage
  seulement : aucune donnée touchée.
- **La règle, dans ses mots** : « une fiche contact pour nos clients, et une fiche notaire, une fiche syndic, une fiche
  courtier, une fiche apporteur [+ diagnostiqueur, confirmé] et c'est tout ». Un contact lié à un métier est visible
  **dans le catalogue des métiers, avec sa fiche dédiée** ; s'il est aussi client, **depuis la liste des clients on ouvre
  sa fiche contact normale** (il apparaît donc aux deux endroits, de deux manières). **Le notaire est dans le catalogue** :
  sa fiche dédiée est la fiche notaire d'aujourd'hui, inchangée. « Société n'est pas un métier. »
- **Le correctif** : la fiche reçoit `ouverture='catalogue_metiers'` ; SEUL le catalogue (3.5) la passera. Sans elle, ou
  pour la famille « autre », pas de fiche métier. Fiche notaire : rien ne change (ni sa fiche ni son ouverture).
- ⚠ **Conséquence assumée** : tant que le catalogue (3.5) n'existe pas, aucune fiche syndic / diag / courtier / apporteur ne
  s'ouvre ; 3.5 vient juste après.
- Ce qui reste sur toutes les fiches : le bloc « Métier » (3.1, seulement si le contact a un métier) et « Changer le
  métier » (3.2, au menu) — c'est par là qu'on range un contact dans le catalogue. À retirer si Frédéric le demande.
- Essai : `test_metier_partenaire.cjs` 50/50 ; le contrôle (50) vérifie qu'aucune porte ne passe encore la valeur — à
  changer avec 3.5.
- ✅ **Poussé (`732109c`, avec 3 commits « Registre » d'une autre session, « Vas-y ») et vu en ligne le 05/11** :
  PICARD (10177505) et Michelle BONNET (10011026) = fiche **Mandant** d'avant (Recherche, Biens, pas de bouton de
  métier) ; le syndic GIBERT IMMOBILIER (10650712) = fiche ordinaire ; un notaire à rôle (10008890) = fiche notaire
  intacte (Dossiers en cours, Actes ≤ 30 jours…). Le bloc « Métier » reste visible avec « Changer ».
- ⚠ **Pour 3.5** : M. Rachid RABHI (10000258) a le métier notaire au registre (Netty) mais aucun rôle notaire dans les
  transactions → il n'a PAS la fiche notaire (c'était déjà le cas avant). Le catalogue devra dire quelle fiche ouvrir
  pour les notaires du registre sans transaction (registre : 1 656 notaires).
  ✅ **Tranché par Frédéric (05/11)** : « respecter les règles actuelles » — **les notaires au catalogue sont ceux qui ont
  AUJOURD'HUI la fiche notaire dans l'app**, avec cette même fiche. Un contact comme RABHI (sans rôle notaire) n'a pas
  la fiche notaire et ne l'aura pas. ⚠ J'avais d'abord compris « tout notaire du registre, sans liaison » : faux, corrigé.

#### 26 quater. PIÈCE 3.5 — LE CATALOGUE DES MÉTIERS : AUDIT (05/11, « OK on enchaîne ») — rien codé

- **Maquette validée le 04/11** (planche 1, `Main.dc.html`) : interrupteur « Clients | Partenaires » en tête de
  l'annuaire, tuiles par métier, liste, aperçu à droite (« Ouvrir la page »). Ses tuiles « Administrations » et « fiches
  à classer » tombent avec la règle du 05/11 (« et c'est tout »).
- **Les cinq tuiles, mesurées** : Notaires 1 130 (ceux qui ont la fiche notaire aujourd'hui ; 498 archivés) · Syndics 75 ·
  Apporteurs et parrains 50 (24 archivés) · Diagnostiqueurs 36 (14) · Banques et courtiers 30 (21).
- **Proposé** : l'interrupteur dans l'écran Contacts (côté Clients = la liste d'aujourd'hui) ; côté Partenaires les
  cinq tuiles, la liste du métier, recherche par nom ; un clic ouvre la fiche dédiée avec `ouverture='catalogue_metiers'`
  (notaire : la fiche notaire d'aujourd'hui). L'aperçu de droite plus tard (ses chiffres n'existent pas). Nouveau cran
  `partenaires_catalogue`, admin d'abord. ⚠ L'adresse doit garder « vue métiers » (sinon un rechargement rouvre la fiche
  normale).
- ✅ **Décision de Frédéric (05/11)** : **la pastille « Notaire » sort de la liste des clients** (« je la retire ») — retirée
  seulement là où le catalogue est visible (même cran), pour ne jamais perdre l'accès aux notaires.
- ✅ Confirmé (« Oui, vas-y ») : les actifs d'abord, les archivés à part (bouton « Voir les archivés (n) »).

#### 26 quinquies. PIÈCE 3.5 — CODÉE (05/11), derrière le cran `partenaires_catalogue` (pas encore posé = éteint)

- `lib/cataloguePartenaires.ts` (règles pures : 5 tuiles, banque→courtier, parrain→apporteur, société/administration
  dehors, actifs/archivés, recherche sans accents), `CataloguePartenaires.tsx` (lecture seule : registre + fiches ;
  notaires = rôle notaire, règle actuelle, lus par pages de 1 000), `catalogue-partenaires.css`.
- Écran Contacts : interrupteur « Clients | Partenaires » (cran visible seulement) ; côté Clients = la liste d'avant ;
  côté Partenaires = le catalogue. Un clic lit la fiche COMPLÈTE (`select *`) et l'ouvre avec
  `ouverture='catalogue_metiers'`. ⚠ Pourquoi pas par le numéro seul : `selectedContact` vient de la PAGE de la liste
  des clients et retombe sur son 1er contact si le numéro n'y est pas (App.tsx, `contactsDirectory.find(...) ?? [0]`).
- Adresse : clé `vue=metiers` ajoutée ; un rechargement garde le côté Partenaires et la fiche métier ;
  `showContactInDirectory` (« voir le contact » depuis une annonce…) remet toujours le côté Clients.
- Pastille « Notaire » retirée de la liste des clients LÀ OÙ le cran est visible ; un filtre « notaire » mémorisé est remis
  à « Tous ».
- ⚠ **Le téléphone** a son propre écran de contacts (`MobileContactCards`, sans pastilles) : **pas de catalogue au
  téléphone** dans cette pièce → les fiches syndic / diag / courtier / apporteur n'y sont pas accessibles (K7).
- Essai `test_metier_partenaire.cjs` **61/61** (11 nouveaux, dont (50) : une seule porte passe la fiche métier).
- ✅ **Poussé (`743cb96`, « Oui, pousse et pose ») ; `app_setting.partenaires_catalogue = admin` posé le 05/11 à 18:10.**
  Vu en ligne (admin, 1280 × 665) : interrupteur présent, pastille « Notaire » absente côté Clients ; tuiles Notaires
  632 (+498 archivés = 1 130), Syndics 75, Diagnostiqueurs 22 (+14), Banques et courtiers 9 (+21), Apporteurs et
  parrains 26 (+24) — conformes à la mesure. GIBERT IMMOBILIER (10215568) → fiche syndic, et un RECHARGEMENT de
  `?ecran=contacts&contact=10215568&vue=metiers` la rouvre en fiche syndic ; un notaire (10036717) → fiche notaire ;
  Michelle BONNET (archivée, 10011026) → fiche courtier avec le bandeau d'archivage ; la même par la liste des clients
  (`?ecran=contacts&contact=10011026`) → fiche Mandant, côté Clients.
- ⚠ Vu : trois « GIBERT IMMOBILIER » sans ville ni téléphone sont indiscernables dans la liste (doublons des données).
  Retouche proposée : montrer le numéro quand il n'y a ni ville ni téléphone. Non vu : un compte non admin, le mode sombre.
- ✅ **`partenaires_catalogue = on` le 05/11 à 18:18 (« Ouvrir à tous »)** : le catalogue est visible de tous, et la
  pastille « Notaire » quitte la liste des clients pour tous (au rechargement). Retour arrière : `admin` ou `off`.
  ⚠ Un négociateur ne voit au catalogue que les contacts de SON périmètre (politique `app_contact_current_select_scoped`,
  la même que la liste des clients) : ses nombres peuvent être plus petits que ceux de l'admin. Non vu en vrai.

#### 26 sexies. 3.5 — LE DESSIN REFAIT SUR LA MAQUETTE (05/11, « oui »)

- **Le défaut, vu par Frédéric** : « le design du catalogue ne correspond pas à ta maquette ». Cause : de la planche 1 je
  n'avais repris que les TEXTES, et dessiné avec les styles de la liste des contacts, sans rien lui montrer avant de coder
  (contre la méthode). L'aperçu de droite avait été retiré sans le lui demander.
- **Refait à l'identique** (mesures de `Main.dc.html`) : en-tête « Clients | Partenaires » (pastille beige) + recherche
  420 px + « Ajouter un partenaire » (ouvre la création de contact existante, droit de gérer les contacts) ; titre 34 px ;
  tuiles à icône dans l'ordre de la maquette (Notaires, Banques et courtiers, Diagnostiqueurs, Apporteurs et parrains,
  Syndics), la choisie remplie de sa couleur ; liste en cartes (avatar carré, « métier · ville », colonne activité,
  étiquette) ; filtre Agence ; aperçu à droite (bandeau coloré, Appeler / Écrire / RDV, trois chiffres, dernières
  affaires, lieux, « Ouvrir la fiche … ») ; un clic choisit, « Ouvrir la fiche » (ou double-clic) ouvre.
- **Adaptations dites et acceptées** : police et couleurs de l'app (celles des fiches) ; l'activité avec l'agence n'existe
  pas → « — » et « en construction » (anneau, chiffres, dernières affaires ; tri par nom) ; RDV grisé (il se crée depuis
  la fiche) ; ni « Administrations » ni « fiches à classer ». Côté Partenaires, la barre du haut des clients se cache.
- **Retouche du numéro faite** : une carte sans ville, téléphone ni e-mail montre « n° … » ; la recherche trouve aussi
  par numéro.
- **Contrôle avant le push** : banc local à données FICTIVES (esbuild, base simulée, servi par le serveur des maquettes,
  retiré ensuite) : 1212 px et 900 px, sans débordement. Essai `test_metier_partenaire.cjs` **65/65**.
- ✅ **Poussé (`619f1e0`, sorti en `997ba57` ; Vercel est resté ~5 min « en préparation », puis a relancé seul) et vu
  en ligne** (1280 × 665) : en-tête de la maquette, barre du haut des clients cachée, tuiles 632 / 9 / 22 / 26 / 75 ; les
  trois GIBERT IMMOBILIER enfin discernables (n° 10215568, 10352769, 10650712) ; aperçu → « Ouvrir la fiche syndic » →
  fiche syndic ; retour côté Clients : barre du haut revenue, pastille Notaire absente.
- ⛔ **Défaut trouvé en ligne et corrigé (non poussé)** : repasser côté Clients avec une fiche du catalogue OUVERTE la
  faisait retomber sur `props.selectedContact` = le 1er client de la page (M. Julien NEYRET à la place de GIBERT, avec les
  liens de GIBERT). Difficile à atteindre (la fiche couvre l'interrupteur ; atteint par script), mais une fiche ne doit
  jamais montrer un autre contact : quitter le côté Partenaires ferme désormais la fiche du catalogue. Essai 66/66.
  ✅ Poussé (`7dbd6bb`, « Ok ») et REJOUÉ en ligne : fiche GIBERT ouverte → côté Clients → la fiche se ferme, adresse `?ecran=contacts`.

#### 26 septies. ⛔ PIÈCE 3.3c FERMÉE PAR DÉCISION (05/11) — la zone sensible ne se fait pas

- Expliquée à Frédéric (planches 8 et 9 : Archiver / Supprimer sortis du menu vers une « zone sensible » en bas, une
  fenêtre commune, suppression par case à cocher + raison obligatoire). **Sa réponse : « Non, on peut garder comme
  contact "…" ».**
- ⇒ Sur la fiche métier, **Archiver et Supprimer restent dans le menu « ⋯ », comme sur la fiche contact**, avec les
  confirmations d'aujourd'hui (boîte du navigateur pour archiver, texte `SUPPRIMER CONTACT <n>` à taper pour supprimer).
  Rien n'est codé. Les décisions P2 (case à cocher) et K3 tombent avec elle. **Ne pas relancer.**

#### 26 octies. ✅ CONTRÔLE DU 06/11 AU MATIN (après le run, « vérifie tes correctifs »)

- **Les 8 noms de syndics tiennent** : relus par la nuit le 06/11 à 05:46, tous sous leur nom (GIBERT IMMOBILIER, AGENCE
  IMMOBILIERE DE BELLEVUE, PICHET IMMOBILIER SERVICES, SOCIETE DE GESTION IMMOBILIERE, DETROIS IMMOBILIER, CABINET
  MELLIER MICHAS, GOUDARD PATOT, IMMO DE FRANCE FOREZ VELAY) ; 10217339 présent, toujours « Contact 10217339 ».
- **Registre** : 1 870 actifs dont 1 657 notaires (attendu 1 869 / 1 656) ; l'écart = UNE ligne neuve, normale : 1893,
  Me Julien MILAN (10651024), notaire côté vendeur, source transactions, écrite à 06:11 par l'étape du registre.
  Sources : netty 962, transactions 614, hektor 294.
- **Garde des métiers retirés** : 0 métier retiré par quelqu'un puis remis par la nuit (2 lignes retirées à la main,
  dont 1892 toujours retirée depuis le 05/11 14:27) ; 0 ligne syndic active pour 10354488.
- **Garde des contacts supprimés** : 41 contacts supprimés au journal ; 0 ligne de métier et 0 lien pour l'un d'eux.
- Les 257 lignes actives sans fiche dans l'app = les notaires hors de l'app déjà connus (hektor 53, transactions 204 ;
  ils étaient 259 : 2 sont entrés) — sujet mis de côté par Frédéric.
- ⚠ **Trouvé** : le compte rendu JSON de l'étape (`contacts_supprimes_ecartes`, `metiers_retires_ecartes`…) n'est PAS
  dans le journal du run (ligne vide entre START et DONE, `logs/scheduled/quotidien_2026-11-06_04-00-02.log` l. 3007) :
  les gardes se contrôlent donc par la base, comme ci-dessus. À signaler, rien de changé.

#### 26 nonies. PIÈCE 3.6 — LE CATALOGUE AU TÉLÉPHONE (06/11, « d'abord 3.6 », « visible par tous ») — codée

- **Le manque** : le téléphone a son propre écran de contacts (`MobileContactCards`), sans catalogue → aucune fiche
  syndic / diag / courtier / apporteur n'y était accessible.
- **Dessin = la planche 2** (`Telephone.dc.html`) : « Partenaires » + bouton « + », recherche, pastilles de métier qui
  défilent (Notaires, Banques, Diagnostics, Apporteurs, Syndics, avec leur nombre), cartes ; au toucher, une FEUILLE qui
  monte (bandeau du métier, Appeler / Écrire / RDV grisé, trois chiffres « — », « Activité avec l'agence : en
  construction », l'action du métier « bientôt », « Voir toute la fiche » → la fiche dédiée). Sans « fiches à classer » ;
  archivés à part.
- **Branchement** : `CataloguePartenaires variante="telephone"` ; `MobileContactCards` reçoit `vue` / `onVueChange` /
  `onOpenCreate`, montre l'interrupteur « Clients | Partenaires » au-dessus de la liste des clients, la fiche du catalogue
  (pas le 1er de la page) avec `ouverture='catalogue_metiers'`, et la même garde de sortie qu'au bureau. La carte de
  recherche des clients se cache côté Partenaires. **Même cran `partenaires_catalogue` (déjà « on »)** : visible de
  tous dès le déploiement (choix de Frédéric).
- **Contrôles** : banc local à données FICTIVES en 390 × 844 (feuille 387→844 px, « Voir toute la fiche » visible,
  aucun débordement), retiré ensuite ; essai `test_metier_partenaire.cjs` **69/69** ((50) : deux portes seulement,
  bureau et téléphone) ; `npm run build` vert.
- ✅ **Poussé (« Oui, pousse ») — sorti en `aa3d016`** et vu en ligne au téléphone (l'app réelle dans un cadre 390 × 844,
  session admin) : interrupteur Clients | Partenaires ; côté Partenaires, carte de recherche des clients cachée ; pastilles
  Notaires 633 / Banques 9 / Diagnostics 22 / Apporteurs 26 / Syndics 75 ; GIBERT IMMOBILIER → feuille (Appeler, Écrire,
  RDV, « Demander un document · bientôt », « Voir toute la fiche ») → fiche SYNDIC, la feuille se range ; aucun débordement.
- ⚠ **Le push a emporté 2 commits d'autres sessions arrivés après ma question** : `a7f3cdf` (Youtrust, notes) et
  `aa3d016` (page RDV : `backend/app/services/appointment_service.py` + essai + notes → **parti chez Render**). Session
  « Vue registre transactions CRM immobilier » prévenue par message. Leçon : relire `origin/main..HEAD` JUSTE avant le
  push et redemander si la liste a changé depuis la question.

#### 26 decies. PIÈCE 3.4 — LES INTERLOCUTEURS POUR TOUS LES MÉTIERS (06/11, « A et on change le nom ») — prête, NON posée

- **Audit** : le carnet du notaire (`app_notaire_interlocuteur`, 28/10) est VIDE (0 ligne) ; sa fonction d'écriture accepte
  déjà n'importe quel contact ; deux lecteurs seulement (l'écriture, et `app_notaire_fiche`) ; la descente découvre ses
  tables seule (l'ancienne copie locale, vide, restera sur le serveur). La maquette met « Interlocuteurs + Ajouter » dans
  le volet gauche de chaque fiche métier.
- **Décision** : une seule table, renommée → `app_partenaire_interlocuteur`, colonne `contact_id`.
- **Patch** `supabase/patch_partenaire_interlocuteur_2026-11-06.sql` (une transaction, empreintes vérifiées avant) :
  renommage (table, colonne, séquence, index, contraintes, règle de lecture) ; `app_partenaire_interlocuteur_ecrire`
  (même geste) ; l'ancien nom devient un RELAIS (l'app en ligne l'appelle) ; `app_notaire_fiche` lit le nouveau nom.
  `_INVERSE.sql` (formes exactes rendues, empreintes vérifiées, lignes gardées) ; `_REPETITION.sql` (9 contrôles).
- **Éprouvé dans une transaction annulée (06/11)** : patch → écriture (syndic 10215568), écriture par le relais (notaire
  10008890) lue par la fiche notaire, modification, retrait, nom vide refusé → inverse → empreintes revenues ; base
  vérifiée inchangée après. ⚠ 1er essai : l'inverse réécrivait la fiche AVANT de rendre le nom à la table (une fonction en
  SQL est vérifiée à sa création) — ordre corrigé, 2e essai vert.
- **Écran** : `PartenaireInterlocuteurs` (FichePartenaire.tsx) lit la table renommée et réutilise le carnet du notaire
  (titre « Interlocuteurs », exemples par métier) ; fiches métier seulement (pas « autre », pas la fiche client) ; la
  fiche notaire est inchangée (titre, textes, appel par le relais).
- **Essais** : `test_metier_partenaire.cjs` 71/71 ; `test_fiche_notaire.cjs` vert — ⚠ il était ROUGE depuis 3.3b (la
  ligne `masquerRecherche` avait changé sans que je le relance) : contrôle mis à jour.
- **Ordre de pose** : 1. coller le patch (puis la répétition, 9 « OK ») ; 2. pousser l'écran (avant le patch, le carnet
  des fiches métier dirait « illisible »). Retour arrière : l'écran d'avant, PUIS `_INVERSE.sql`.
- ✅ **PATCH POSÉ le 06/11 (« Vas-y »)** — migration `partenaire_interlocuteur_2026_11_06` ; **répétition 9/9 « OK »**
  (0 ligne). L'app en ligne écrit par le relais : rien de cassé en attendant l'écran.
- ⏸ **Écran NON poussé** : sous `ab8f8b7` se trouve `63fbe36` (autre session : code serveur `appointment_service.py` +
  `run_full_pipeline.ps1`) — le pousser l'enverrait chez Render ; question posée à Frédéric.
- ✅ **Poussé (« Pousse », liste relue juste avant : inchangée) — `aa3d016..940b35d`**, avec `175b076`, `63fbe36` (code
  serveur page RDV + run de nuit, session « registre des agences ») et `caf0a04` (normalize_source.py). Vu en ligne :
  GIBERT IMMOBILIER (fiche syndic) → « Interlocuteurs · + Ajouter », texte « gestionnaires de copropriété, comptables,
  assistants », formulaire Nom / Rôle (gestionnaire, comptable…) / Téléphone / E-mail — ouvert puis ANNULÉ, rien saisi ;
  la fiche notaire 10008890 garde « Interlocuteurs de l'étude » et ses chiffres. Non éprouvé en réel : un ajout (ce
  serait une écriture en production) — prouvé seulement dans la transaction annulée.

## 27. LOT 4 — LE SYNDIC (06/11)

### 27.1 Audit (« Maintenant »)
- **B6 déjà fait** : la nuit lit le syndic des 731 annonces en copropriété, la reprise range les liens au registre →
  **80 biens reliés à 29 syndics** (max 16 pour IMMO DE FRANCE FOREZ VELAY), tous origine « hektor » ; les 29 sont nos
  fiches (numéros vérifiés 29/29). Les 46 autres syndics du catalogue n'ont aucun bien relié.
- **Copropriété** (`app_dossier_detail_current.detail_payload_json` → `copropriete_json`, texte JSON) : 79 des 80 biens ont
  lots, quote-part annuelle, fonds de travaux, statut (`NOTPROCESS` = aucune procédure), plan de sauvegarde, n° de lots.
- **Documents** : 807 documents sur ces biens, 159 de copropriété par leur nom, sur 35 biens.
- **RNIC** (registre national des copropriétés) déjà interrogé par l'app (`loadCoproRnie`, backend `/copro/rnie`) :
  immatriculation, lots, syndic, procédure → candidat pour l'immeuble (4.3).
- `app_partenaire_lien_ecrire` existe (poser / retirer un lien) ; le bloc « Diagnostics et syndic » de la fiche annonce
  montre le texte de Hektor sans choix ; défaut dormant B5 (texte libre envoyé à Hektor, 0 saisie).
- Découpage proposé et accepté (« Oui, vas-y 4.1 ») : 4.1 fiche syndic remplie · 4.2 choisir le syndic d'un bien ·
  4.3 l'immeuble · 4.4 « Demander un document » · 4.5 les assemblées générales · 4.6 le téléphone.
- ⏸ Entre-temps (06/11), Frédéric a ouvert le **chantier GED** (`notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md`) ; les documents
  de copropriété y seront classés ; 4.1 les reconnaît provisoirement par le nom.

### 27.2 Pièce 4.1 — la fiche syndic remplie, LECTURE SEULE — codée
- `lib/ficheSyndic.ts` (règles pures : `lireCopro`, `estDocumentCopro`, `construireVueSyndic` ; on ne somme PAS les lots,
  plusieurs biens peuvent être dans le même immeuble) ; `FicheSyndic.tsx` (lecture : liens → biens vivants puis index des
  archives → détail → documents ; aucune écriture ; droits de chacun) ; `fiche-syndic.css`.
- Sur une fiche SYNDIC ouverte depuis le catalogue, les blocs « en construction » de 3.3b cèdent la place : chiffres (nos
  biens chez lui, biens en vente, charges moyennes ; demandes = 4.4), « Copropriétés » (une carte par bien : statut,
  mandat, lots, charges / an, fonds de travaux, procédure, plan de sauvegarde, documents de copro ou « aucun au coffre » ;
  un clic ouvre le bien), « Nos biens dans ses copropriétés » (en vente / vendus / autres) ; « Demandes et délais » et
  « À venir » restent en construction (4.4, 4.5). Cran **`partenaires_syndic_fiche`** (absent = la fiche d'avant).
- Contrôles : `test_metier_partenaire.cjs` **77/77** (6 nouveaux) ; `test_fiche_notaire.cjs` vert ; banc à données
  FICTIVES (900 px et 390 px, aucun débordement) ; seuls mes morceaux d'App.tsx commités (le travail en cours de la session
  signature laissé en l'état), version commitée construite à part.
  ⚠ Le repli `contactsDirectory.find(...) ?? contactsDirectory[0]` d'App.tsx est ANCIEN et sert à toute l'app : non
  touché, à signaler.
- **EN LIGNE le 06/11** (accord de Frédéric : « oui ») : poussé `940b35d..03b74fd` — la liste relue juste avant le push
  était celle annoncée (avec les commits des autres sessions : A.2 front `aa0baae`, worker A.2 `3c32daa`, estimation
  publique `7ddc14b`, notes GED). Réglage posé : `app_setting.partenaires_syndic_fiche = 'admin'`. Vercel prêt en 45 s.
- **VU EN VRAI** sur IMMO DE FRANCE FOREZ VELAY (10217295), compte admin : chiffres 16 biens · 7 avec documents de
  copro · 10 en vente · charges moyennes 1 312 € ; 16 cartes, 24 puces de documents, 9 « aucun document au coffre » ;
  « Nos biens dans ses copropriétés » 10 / 0 / 6. Le clic sur une carte ouvre bien l'annonce (7589288), avec le retour
  « Fiche contact ». Téléphone (390 px) : 16 cartes, aucun débordement.
  ⚠ Vu au passage : certains biens s'affichent « [Sans titre] V790063303 » — c'est le titre tel qu'il est dans nos
  données (estimation sans titre), pas un défaut de la fiche.
- **OUVERTE À TOUS le 06/11** (Frédéric : « Ouvrir à tous ») : `partenaires_syndic_fiche = 'on'`. Retour arrière : la
  remettre à `admin`, ou supprimer la ligne (= la fiche partenaire d'avant).
- Reste : 4.2 → 4.6.

### 27.3 Pièce 4.2 — choisir le syndic d'un bien : AUDIT (06/11, « Oui, audit 4.2 »)
Audit limité aux biens (annonces) et à leur syndic ; le diagnostiqueur n'est mesuré que pour l'assistant (B5).

**Ce qu'on a, mesuré**
- 13 535 annonces, **732 en copropriété** ; **79 ont un syndic**, identique chez Hektor et chez nous (0 écart, 0 bien à
  deux syndics ; 80 liens actifs dont 1 bien hors du parc courant). **653 en copropriété SANS syndic, dont 72 en vente**
  (Actif 64, sous offre 4, sous compromis 4).
- Les 80 liens sont d'origine « hektor », posés par la nuit (`registre_partenaires_reprise.py`), aucun par l'app.
- `app_partenaire_lien_ecrire` existe mais **personne ne l'appelle** ; elle ne vérifie que « compte actif » : ni le droit
  sur le bien (un négociateur pourrait toucher le bien d'un autre), ni que le partenaire est bien un syndic, ni « un seul
  syndic par bien ». Le droit sur un bien existe déjà : `app_console_can_access_dossier` (admin/manager tout ; négociateur
  ses biens, y compris archives, historiques et brouillons).

**Les écrans, mesurés (quel composant s'affiche)**
- Ordinateur = `CockpitDetail` (cockpit v2). Son bloc « Diagnostics et syndic » (onglet Contact) lit `intervenants_json`,
  qui n'existe sur **aucune** annonce (0 / 13 535) → **jamais affiché** ; ses boutons « Ajouter un syndic » et « Fiche »
  n'ont pas d'action. **Sur ordinateur, on ne voit le syndic d'un bien nulle part.**
- Téléphone = `MobileDossierDetail` : montre le texte relu de Hektor (`diagnostics_contacts_console_json`), en lecture.
- L'ancien écran (`DossierDetailLayoutBase`, cockpit éteint) fait pareil que le téléphone.

**L'assistant d'annonce (B5)**
- Champs « Syndic » et « Diagnostiqueur » en TEXTE LIBRE ; le worker les envoie tels quels
  (`setWizardTextIfPresent`, l. 12137) alors que Hektor attend un CONTACT → ignoré. Mesure : **17 envois en tout, tous
  des essais** (mai-juin, 21-22/10), **0 vraie saisie**.
- L'aide « Copropriété » (registre RNIC) propose aussi « À compléter : syndic (nom — type) », même défaut ; jamais cliqué
  avec un syndic.
- Le worker n'a pas à changer : il n'envoie le champ que s'il est présent.

**La nuit et un choix fait dans l'app (lu dans `registre_partenaires_reprise.py`)**
- Un lien « app » n'est jamais touché ; si Hektor dit autre chose, l'app gagne et l'écart est seulement COMPTÉ
  (`ecarts_app_gagne`), dans un compte rendu que le journal du run ne garde pas (déjà signalé).
- **Changer** de syndic marche sans toucher la nuit, à condition de retirer (daté, avec l'auteur) le lien « hektor ».
- ⚠ **Retirer** un syndic venu de Hektor, sans en mettre un autre, serait **défait la nuit suivante** (la nuit remet le
  lien tant que Hektor l'a). Remède connu, déjà posé pour les métiers (§25) : ne pas remettre un lien retiré par quelqu'un.

**Découpage proposé**
- 4.2a base : une fonction « poser / changer / retirer le syndic d'un bien » (droit sur le bien, partenaire qui EST
  syndic au registre, l'ancien lien retiré daté avec l'auteur, en une seule opération) + un index « un seul syndic actif
  par bien » (0 doublon aujourd'hui). Additif ; la fonction existante n'est pas touchée.
- 4.2b fiche annonce (ordinateur) : ranimer le bloc de l'onglet Contact en « Syndic de la copropriété » : le syndic de chez
  nous, d'où il vient (Hektor / app, qui, quand), Choisir, Changer, Retirer, Ouvrir sa fiche ; le choix dans les syndics
  du catalogue (75), avec recherche, et en tête celui que propose le registre RNIC quand le nom correspond ; si Hektor
  dit un autre syndic, le DIRE sur la carte (lu dans la fiche du bien, rien à ajouter).
- 4.2c nuit : ne pas remettre un lien retiré par quelqu'un (comme §25).
- 4.2d B5 : l'assistant ne propose plus « Syndic » en texte (et l'aide RNIC propose de CHOISIR le syndic au lieu d'écrire
  un nom) ; « Diagnostiqueur » : à trancher (le retirer aussi maintenant, ou au lot 5 avec son sélecteur).
- Téléphone : la carte du syndic en lecture tout de suite, ou le choix aussi (sinon 4.6).
- Cran proposé : `partenaires_syndic_choix` (admin puis on), comme les autres.

### 27.4 Pièce 4.2 — CODÉE (06/11, « Oui, vas-y 4.2 », avec les trois choix par défaut)
Choix par défaut retenus : le diagnostiqueur de l'assistant attend le lot 5 ; le téléphone montre le syndic en LECTURE ;
cran `partenaires_syndic_choix` (admin d'abord). **Rien n'est en production** : le patch n'est pas posé, le réglage pas
créé, rien n'est poussé.
- **4.2a base** — `supabase/patch_partenaire_syndic_du_bien_2026-11-06.sql` (+ `_INVERSE`, `_REPETITION` 8 contrôles) :
  index « un seul syndic actif par bien » ; `app_partenaire_syndic_du_bien(dossier, annonce, partenaire, retirer)` (compte
  actif, DROIT SUR LE BIEN par `app_console_can_access_dossier`, partenaire = syndic du registre, l'ancien retiré daté
  avec l'auteur, en une opération, verrou de ligne) ; `app_partenaire_syndic_du_bien_lire(annonce)` (nom, origine, auteur).
  ⭐ **Essai dans une transaction annulée, 11/11 verts** : l'index refuse un 2e syndic ; poser / même syndic = inchangé /
  changer (1 actif, l'ancien retiré par l'admin) / un notaire refusé / lire (nom, « app », auteur) / retirer (0 actif) /
  rien à retirer refusé / sans numéro d'annonce refusé ; un négociateur pose sur SON bien, est refusé sur celui d'un autre.
  Après l'essai : 0 trace (fonctions, index, liens), 80 syndics actifs inchangés.
- **4.2b fiche annonce (ordinateur)** — `SyndicDuBien.tsx`, `lib/syndicDuBien.ts`, `syndic-du-bien.css`. Onglet Contact du
  cockpit, sur un bien en copropriété ou dont Hektor indique un syndic. Choisir / Changer / Retirer (confirmation, la trace
  reste) / Appeler / Ouvrir sa fiche. Le choix : les syndics du catalogue avec recherche (nom, ville) ; en tête celui que
  propose le registre RNIC (lu au clic « Choisir », un appel) puis celui de Hektor, quand le nom correspond. L'écart avec
  Hektor est DIT sur la carte (« Hektor indique un autre syndic… Hektor n'est pas modifié »). « Ouvrir sa fiche » ouvre la
  fiche syndic PAR LE CATALOGUE (vue métiers ; événement `bienvu:ouvrir-partenaire`, écouté avant le retour de connexion).
  Le vieux bloc dormant « Diagnostics et syndic » (intervenants_json) n'est pas touché.
- **Téléphone** — la même carte en lecture (Appeler, Ouvrir sa fiche, l'écart) dans « Contacts » de la fiche du bien.
- **4.2c nuit** — `registre_partenaires_reprise.py` : un lien retiré par quelqu'un n'est jamais remis pour le même
  partenaire sur le même bien ; si Hektor indique un AUTRE partenaire, il est posé ; l'écart « l'app gagne » est compté
  d'abord. Compteur `liens_retires_ecartes`. Essai hors ligne (lectures remplacées, aucune écriture) 4/4 verts.
  ⚠ Le lancement à blanc sur les vraies données a été refusé par l'outil (lecture de la production) : il tournera la nuit.
- **4.2d assistant (B5)** — cran allumé : plus de « Syndic » en texte dans l'assistant de création ni dans l'édition du
  cockpit ; l'aide « Copropriété » (RNIC) ne propose plus d'écrire le nom du syndic chez Hektor. Le worker n'est pas
  touché (il n'envoie le champ que s'il est présent). « Diagnostiqueur » reste (lot 5).
- **Contrôles** : `test_metier_partenaire.cjs` **88/88** (11 nouveaux, (60) mis à jour : le côté « clients » reste le
  défaut) ; `test_fiche_notaire.cjs` vert ; construction verte, ET la version commitée construite à part (seuls mes 14
  morceaux d'App.tsx ; le travail en cours de la session signature laissé en l'état) ; banc à données FICTIVES : choisir
  (proposition RNIC en tête), changer, retirer, refus hors périmètre affiché, « Ouvrir sa fiche », téléphone sans débordement.
- **Pour l'allumer (accord de Frédéric, geste par geste)** : 1. coller le patch puis la répétition (8 verts) ; 2. pousser ;
  3. créer `partenaires_syndic_choix = 'admin'` ; 4. essai réel sur un bien d'essai choisi par Frédéric.
- **EN PRODUCTION le 06/11** (« Oui, pose et pousse ») : patch posé (migration `partenaire_syndic_du_bien_2026_11_06`),
  répétition **8/8 verts** ; poussé `25c3b14..67a9ffb` (liste relue juste avant : celle annoncée) ; réglage créé à `admin`.
  ⚠ **Vu en ligne : la carte n'apparaissait pas, même pour l'admin.** Cause : la page « Détail annonce » (appel de
  `DossierDetailLayout` avec `eyebrow={detailEyebrowForScreen(screen)}`) est le seul des trois chemins vers la fiche d'un
  bien qui ne transmet PAS `profileRole` → un cran « admin » y est toujours éteint. Défaut ANCIEN : il fait aussi voir
  « Réaffecter le négociateur » aux négociateurs sur cette page (le code prévoit de le leur cacher). Non corrigé.
  ⇒ **Décision de Frédéric : « syndic tout de suite à tous »** → `partenaires_syndic_choix = 'on'`.
- **VU EN VRAI (lecture seule, aucun syndic choisi ni changé)** sur le bien 63303 (dossier 7589288) : carte « Syndic de la
  copropriété » = IMMO DE FRANCE FOREZ VELAY, « repris de Hektor le 04/11/2026 », Ouvrir sa fiche / Changer / Retirer ;
  « Ouvrir sa fiche » ouvre la fiche syndic PAR LE CATALOGUE (`vue=metiers`, 16 biens) ; téléphone (390 px) : la carte en
  lecture, « Ouvrir sa fiche » seul, aucun débordement. Reste : l'essai réel d'un choix sur un bien d'essai.
  Remarque : la carte montre « n° 10217295 » faute de ville et de téléphone sur la fiche de ce syndic.
- **ESSAI RÉEL du choix (06/11, « choisis un bien test »)** sur le bien d'essai **63331** (dossier 10000009, « ESSAI 8A3
  PIECE 3 - ne pas diffuser », mandant « Mandant ESSAI 8A C1 », en copropriété, sans syndic), par l'écran, compte de
  Frédéric. Rien chez Hektor.
  1. Choisir : recherche « foncia » → FONCIA LOIRE AUVERGNE (10217296) → ligne 90, origine app, posée par Frédéric ;
     la carte dit « choisi dans l'app par Frederic Gerphagnon le 06/11/2026 ». (Registre RNIC : rien pour ce bien d'essai.)
  2. Changer → AGENCE PEYROT (10355053) : ligne 90 retirée et ligne 91 posée À LA MÊME SECONDE, l'auteur des deux côtés.
     « Ouvrir sa fiche » → la fiche d'AGENCE PEYROT (catalogue) montre le bien d'essai dans « Copropriétés ».
  3. Retirer → confirmation (« la trace reste ») → « Aucun syndic ». Lignes 90 et 91 gardées, retirées, signées.
  ⇒ **Le bien d'essai est revenu à son état d'avant** (aucun syndic actif). La nuit ne remettra rien (Hektor n'indique aucun
  syndic sur 63331, et 4.2c ne remet pas un lien retiré par quelqu'un).
- ⚠⚠ **TROUVÉ PAR L'ESSAI : LES DOUBLONS DE SYNDICS.** Dans le choix, « FONCIA LOIRE AUVERGNE » apparaît 4 fois, sans rien
  pour les distinguer. Mesure : **15 noms de syndic en double au catalogue, 41 fiches**, presque toutes SANS ville —
  IMMO DE FRANCE FOREZ VELAY ×9, FONCIA LOIRE AUVERGNE ×4, GIBERT IMMOBILIER ×3, SOCIÉTÉ DE GESTION IMMOBILIÈRE ×3, puis
  11 noms ×2. Conséquence : un utilisateur choisit au hasard, les biens d'un même syndic se répartissent sur plusieurs
  fiches, et la fiche syndic (4.1) n'en montre qu'une partie (les « 16 biens » d'IMMO DE FRANCE ne comptent que 10217295).
  Non traité — à présenter à Frédéric (montrer de quoi distinguer dans le choix, et/ou désigner une fiche principale).
  ⇒ **Décision de Frédéric (06/11) : « Montrer de quoi choisir »** — CODÉ (front seul, même cran) : chaque ligne du choix
  montre son n°, son téléphone (sinon l'e-mail) et « N biens chez nous » (liens syndic actifs) ; « N fiches à ce nom »
  quand il y a des homonymes ; entre homonymes, la fiche qui porte DÉJÀ le plus de nos biens en tête ; la recherche
  accepte un n° ou un téléphone ; après un choix, le catalogue est relu (les comptes bougent). Rien en base.
  Contrôles (88)-(91) ; essai **92/92** ; construction verte ; banc fictif à 1280 × 665. Le regroupement des doublons
  (fiche principale) reste à étudier à part.
- **EN LIGNE le 06/11** (« Oui, pousse ») : `fc682cf..9443981`. Vu sur le bien d'essai, sans rien choisir : « immo de
  france » → 9 lignes « 9 fiches à ce nom », en tête n° 10217295 « 16 biens chez nous », les 8 autres « aucun de nos
  biens » (aucune n'a de téléphone : c'est le compte de biens qui départage).

### 27.5 Pièce 4.3 — l'immeuble : AUDIT (06/11, « ok enchaîne »)
But prévu : regrouper nos biens d'un même immeuble (sur la fiche syndic, une « copropriété » = un immeuble et non un bien).
**Ce que disent les sources, mesuré sur nos 732 biens en copropriété :**
- **Registre national (RNIC)** : lu et gardé pour **3 biens seulement** (`app_dossier_estimation.sources.copro`, rempli
  quand quelqu'un lance l'avis de valeur). Repère sûr (n° d'immatriculation), mais quasi absent ; le remplir demanderait
  ~730 appels au registre (par notre serveur, pas Hektor).
- **GPS** : INUTILISABLE pour ça — un même point (centre de Saint-Étienne) porte 72 biens et 64 adresses différentes.
- **Adresse** (`adresse_detail` + code postal) : 718 / 732 renseignées ; **37 adresses partagées par 86 biens**. Mais des
  variantes d'écriture (« 9 rue du champ mars 2eme étage » / « 9 rue du champs de mars »), des codes postaux différents
  pour la même rue (42000 / 42100), et souvent le **même lot remis en vente** (une estimation puis une annonce) plutôt
  que deux lots d'un immeuble.
- **Lots** (`copropriete_nb_lot`) : souvent « 0 » (non saisi), ne départage pas.
**Ce que ça changerait sur les fiches syndic aujourd'hui : presque rien.** Sur les 80 biens reliés à un syndic,
**77 sont à des adresses différentes** : IMMO DE FRANCE 16 biens = 16 adresses, FONCIA 7 = 7. Seuls 2 regroupements :
« 39 bd Docteur Philippe Raoul Duval » ×2 et « 7 rue Charles Rocher (Résidence Saint Clair 2) » ×3 — ce dernier
manqué par l'adresse exacte à cause du mot « résidence ».
**La GED n'en dépend plus** : sa règle « un seul endroit » (note GED §8.3 ter, en attente de Frédéric) propose de
reconnaître « la même résidence » par le même syndic + la même adresse, au moment voulu, l'humain confirmant.
⚠ **Coordination** : si Frédéric valide « un seul endroit » (« aucune liste de documents sur la fiche syndic »), les puces
de documents de copropriété des cartes de la fiche syndic (4.1) devront partir.
**Proposé à Frédéric** : A — ne pas créer d'objet « immeuble » maintenant (fermer 4.3 pour l'instant) et passer à 4.4 ;
B — 4.3 léger : sur la fiche syndic, regrouper les biens à la même adresse « nettoyée » (numéro + rue + code postal, sans
résidence / bâtiment / étage), en lecture, sans rien stocker.

### 27.6 Harmonisation de l'annuaire Clients / Partenaires (06/11, « Oui, code-la »)
- Demande de Frédéric : « harmoniser les deux vues… en gardant une unité visuelle par rapport aux autres pages ». Relevé
  sur l'app en ligne : Annonces et Clients ont la MÊME barre commune (recherche, bouton principal, Filtres,
  Réinitialiser, Stats, Priorités) puis une carte « titre + compte + onglets de vue » (« Annonces actives | Liste ·
  Publicité », `.av3-onglets`). Le côté Partenaires sortait du modèle (son propre en-tête, grand titre). Maquette :
  https://claude.ai/artifact/Gqhn3Gmb9Ewwh56oSWpeYk (deux essais refusés avant : « plus haut de gamme », « harmoniser »).
- Codé (dessin seulement, aucun geste changé) : la barre commune AUSSI côté Partenaires (recherche du catalogue,
  « Ajouter un partenaire », Filtres / Stats / Priorités grisés, Réinitialiser vide la recherche) ; « Clients |
  Partenaires » = `OngletsAnnuaire`, gabarit des onglets des Annonces, posé à côté du titre de la carte (« Annuaire des
  contacts » / « Annuaire des partenaires » + compte), le fond blanc glisse d'un onglet à l'autre ; les métiers en
  rangée de puces comme les catégories des clients (les deux cartes commencent à la même hauteur : 209 / 207 px au
  banc) ; Agence dans l'en-tête de la carte ; téléphone : l'onglet commun en pleine largeur (le reste inchangé).
- Le sélecteur flottant et son correctif de style (546f1e2) disparaissent avec l'harmonisation.
- **EN LIGNE le 06/11** (« Oui, pousse les deux », avec 223a0f1 de la session signature) et vu en vrai des deux côtés,
  bureau et téléphone ; la recherche du haut filtre le catalogue ; Filtres / Stats / Priorités inactifs côté Partenaires.
- **Retouche (06/11, Frédéric : « placés trop bas… non, sous la barre de recherche »)** : l'onglet de vue quitte le titre
  des cartes et vit dans la barre commune, SOUS la recherche, à gauche (`.hero-onglets`) : 114 px du haut au lieu de
  ~258, les deux cartes toujours alignées. Essayés et écartés sur la vraie page : DANS la barre (à 1280 px, recherche
  réduite à 255 px, Stats / Priorités ne tiennent plus) ; en tête des catégories (la rangée passe sur deux lignes) ;
  une ligne « Annuaire » tout en haut (proposée, refusée). Stats dépliées : l'onglet passe sous les chiffres (le forcer
  juste sous la recherche les chevauche).
- Contrôles : (64) réécrit pour la nouvelle règle ; 92/92 ; notaire vert ; construction verte, ET la version commitée
  construite à part ; banc fidèle (feuilles de style de l'app, données fictives) bureau 1280 × 665 et téléphone.

## 28. PLAN ACCÉLÉRÉ DES LOTS 4 À 7 (06/11, Frédéric)
> « Passe à 4.4 et peux-tu accélérer sur les fiches partenaires : on peut faire plus simple, avec toutes les pages, mais
> les blocs à développer “en création” pour les faire plus tard, car cela n'apporte pas beaucoup, comme l'immeuble… Adapte
> le chantier en gardant le principe général. »

**Principe gardé** : la fiche métier s'ouvre depuis le catalogue ; les liens vivent chez nous ; rien n'est écrit chez
Hektor ; ce qui n'existe pas encore est MONTRÉ « en construction » (règle du 27/10) ; chaque pièce derrière un cran.
**Ce qui change** : pour chaque métier, on livre la page entière tout de suite avec ce qui EXISTE ; le reste reste un
bloc « en construction ». On ne crée ni table de suivi ni objet nouveau tant que ce n'est pas nécessaire.
Mesure du 06/11 (fiches au catalogue / avec e-mail / liens) : syndic 75 / **3** / 80 ; diagnostiqueur 36 / 29 / 4 ;
apporteur 35 / 23 / 0 ; courtier 22 / 14 / 0 ; parrain 15 / 8 / 0 ; banque 8 / 7 / 0. Interlocuteurs saisis : 0.

- **Lot 4 — syndic** : 4.1 fiche ✅ ; 4.2 choisir le syndic d'un bien ✅ ; **4.4 « Demander un document » SIMPLE** : un
  message prêt (le bien, ses lots, son mandat, les pièces cochées), modifiable, à copier ou à ouvrir dans la messagerie
  si l'e-mail est connu ; rien n'est stocké. EN CONSTRUCTION : l'immeuble (4.3), le suivi des demandes et des délais,
  les assemblées générales (4.5), le choix du syndic au téléphone (4.6).
- **Lot 5 — diagnostiqueur** : la fiche montre « Nos biens diagnostiqués » (même lecture que le syndic) ; choisir le
  diagnostiqueur d'un bien (la carte du syndic, généralisée) ; « Commander un diagnostic » SIMPLE (message prêt, comme
  4.4 — 29 sur 36 ont un e-mail). EN CONSTRUCTION : le suivi des commandes, le DPE qui expire.
- **Lot 6 — courtier / banque** : la fiche (coordonnées, interlocuteurs : déjà là) ; « Orienter un acquéreur » SIMPLE
  (message prêt avec le client choisi). EN CONSTRUCTION : les financements des affaires, les délais.
- **Lot 7 — apporteur / parrain** : la fiche ; « Noter une affaire apportée » = poser le lien client ↔ apporteur dans
  la table EXISTANTE (`app_partenaire_lien`, objet client) ; la reprise des 53 apports de Netty si elle reste simple.
  EN CONSTRUCTION : la commission, l'historique des affaires.
- Ordre proposé : 4.4 → lot 5 → lot 7 → lot 6 (le plus de données d'abord).

### 28.1 Pièce 4.4 — « Demander un document » au syndic, version simple — CODÉE (06/11)
- `lib/demandeDocument.ts` (règles : 7 pièces, les 5 premières cochées d'office — celles que la loi fait joindre à la
  promesse, art. L721-2 CCH, et le pré-état daté ; le message ; le lien de messagerie) ; `DemandeDocument.tsx` (la
  fenêtre : le bien, les pièces, le message modifiable, « Copier le message », « Ouvrir dans ma messagerie » si l'e-mail
  est connu, sinon « ajoutez son e-mail sur sa fiche ») ; `demande-document.css`.
- Ouverte depuis la fiche syndic (le bouton « Demander un document » n'est plus « bientôt ») et depuis la carte syndic
  d'un bien (le bien déjà choisi). `lib/ficheSyndic.ts` lit en plus l'adresse et le code postal de chaque bien.
- RIEN n'est enregistré ni envoyé par l'app (aucune base, aucun travail, aucune requête) ; « Demandes et délais »
  reste en construction. Une donnée absente n'est pas écrite (ni lot ni mandat inventés).
- Cran `partenaires_syndic_demande` (NON posé). ⚠ Sur la page « Détail annonce », la carte ne reçoit pas le rôle (défaut
  ancien, §27.4) : en « admin », le bouton de la carte n'y paraît pas ; il paraît sur la fiche syndic.
- Contrôles (93)-(97) ; essai **97/97** ; notaire vert ; construction verte ; banc à données fictives à 1280 × 665
  (la fenêtre tient) et au téléphone (772 px sur 812, rien ne dépasse), avec et sans e-mail.

### 7 ter. Les dépendances (techniques, pas un ordre décidé)

- 0 avant tout le reste ; 0.1 avant B2 ; 0.2 avant B1 ; 0.6 avant B5 ; 0.3 avant B6 ; 0.4 avant B7 ; 0.5 avant C2.
- A1 avant A2, A3, A5, K1, K6.
- B1, B2, B3 avant C1, C2, C3, et avant les blocs de métier (E2, F2, G3, H2).
- Les familles E, F, G, H sont indépendantes entre elles : leur ordre est D3.
- E4 et E5 servent aussi la fiche notaire : à faire une seule fois pour les deux.
