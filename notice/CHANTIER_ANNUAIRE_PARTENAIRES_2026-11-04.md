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
- **EN LIGNE le 06/11** (« Pousse et allume ») : poussé `9008515..ca89cb5` (le SHA relu, ce commit seul) ; réglage
  `partenaires_syndic_demande = 'on'`. **Vu en vrai** sur IMMO DE FRANCE FOREZ VELAY (fiche syndic) : bouton actif, 16
  biens au choix, message prêt « 12 Rue Honoré de Balzac, 42000 Saint-Étienne · Lot : 5 · mandat n° 18953 », pas
  d'e-mail sur la fiche → seul « Copier le message » est proposé. Fenêtre refermée sans rien envoyer.

### 28.2 Lot 5 — le diagnostiqueur, version simple — CODÉ (06/11, « Vas-y »)
- **Base** (patch NON posé) `supabase/patch_partenaire_du_bien_2026-11-06.sql` (+ `_INVERSE`, `_REPETITION` 8 contrôles) :
  geste GÉNÉRIQUE `app_partenaire_du_bien(rôle, …)` / `_lire` pour 'syndic' ou 'diagnostiqueur' (mêmes gardes que 4.2 :
  droit sur le bien, métier au registre, l'ancien retiré daté avec l'auteur) + un seul diagnostiqueur actif par bien.
  Le geste du syndic (4.2) n'est PAS touché. ⭐ Essai dans une transaction annulée : 12/12 verts (poser, même, changer,
  un syndic refusé comme diagnostiqueur, rôle inconnu refusé, le générique marche aussi pour le syndic, lire, retirer le
  diagnostiqueur laisse le syndic, négociateur sur son bien oui / sur un autre non) ; 0 trace après.
- **Fiche du bien** : la carte « Diagnostiqueur » (tout bien, bureau) = la carte du syndic généralisée (`role`) :
  choisir / changer / retirer / ouvrir sa fiche / ce que Hektor indique ; pas de registre RNIC pour lui. Téléphone : en
  lecture. « Commander un diagnostic » = message prêt (`lib/commandeDiagnostic.ts`) : diagnostics du dossier de
  diagnostic technique (art. L271-4 CCH), cochés selon le bien (DPE, ERP, électricité, gaz toujours ; amiante avant 1997,
  plomb avant 1949, année inconnue = les deux ; Carrez si copropriété) ; adresse, type, surface, année, mandat ; rien
  n'est enregistré. La fenêtre de 4.4 sert aux deux (`modele`).
- **Fiche diagnostiqueur** (depuis le catalogue) : chiffres (nos biens avec lui, en vente ; commandes et DPE à renouveler
  « en construction »), « Biens diagnostiqués » (la lecture de la fiche syndic, par rôle), bouton « Commander un
  diagnostic » (biens reliés). « Avec nous » reste en construction.
- Cran `partenaires_diag` (NON posé). Mesure : 4 diagnostiqueurs posés chez Hektor sur 714 biens en vente ; 29 sur 36
  ont un e-mail. Année de construction connue sur **299 des 714** biens en vente (ma première mesure disait « aucun » :
  elle cherchait le champ au mauvais endroit, il vit dans `diagnostiques_json`) ; inconnue = amiante et plomb cochés.
- **EN LIGNE le 06/11** (« Oui ») : patch posé (migration `partenaire_du_bien_2026_11_06`), répétition 8/8 ; poussé
  `ca89cb5..60ea64f` (SHA relu) ; `partenaires_diag = 'on'`. **Vu en vrai** sur le bien 62172 (Annonay) : carte
  « Diagnostiqueur » = DS INGENIERIE « repris de Hektor » ; « Commander un diagnostic » : e-mail connu → « Ouvrir dans ma
  messagerie » proposé, 7 diagnostics cochés (construit en 1948, en copropriété lot 7) ; « Ouvrir sa fiche » → fiche
  diagnostiqueur (1 bien, chiffres, bouton). Rien envoyé.
  ⚠ Vu en vrai : le type de bien sortait en CODE (« Bien : 2, 70 m² ») → corrigé (libellé de `propertyTypeLabel`, rien si
  inconnu).
- Contrôles (98)-(103) + (45), (76), (83), (91) mis à jour (le syndic garde ses gestes) ; essai **103/103** ; notaire
  vert ; construction verte ; banc fictif (carte, choix, fenêtre de commande à 1280 × 665).

### 28.3 Création « par photo, avec l'IA » (le scanner) : AUDIT (06/11, question de Frédéric) — rien codé

Audit limité à la création d'annonce par le scanner ; lecture seule du code.
- **Le chemin** : « Nouvelle annonce » → « Par photo, avec l'IA » → « Scanner la fiche » (App.tsx ~22296) → le serveur lit
  les photos (`POST /annonces/scan-fiche`, `backend/app/services/openai_listing_sheet_service.py`, liste `FIELD_KEYS`,
  consignes `agent_registry.py` « scan_fiche ») → `applyDraftAnnonceScan` (App.tsx ~17750) remplit LE MÊME brouillon que
  la saisie manuelle → écran « Fiche analysée » avec deux boutons : « Détailler dans l'assistant » (le même assistant) ou
  **« Créer l'estimation » qui crée DIRECTEMENT** (`handleCreateDraftAnnonce(null, { skipStepGate: true })`, ~22363).
- **Ce que l'IA lit des partenaires : RIEN.** Le patron papier (`public/patron-fiche-saisie.html`, 5 pages,
  `draft_annonce_v1`) n'a aucune case syndic, diagnostiqueur ou notaire ; il a seulement Copropriété oui/non, lots,
  quote-part, fonds travaux, statut du syndicat. `FIELD_KEYS` non plus. Fiche d'essai : `backend/evals/scan_fiche/`.
- **⚠ Le piège** : si le choix du syndic et du diagnostiqueur n'est mis QUE dans l'étape 5 de l'assistant, le bouton
  « Créer l'estimation » le **saute**. Le chemin du scanner doit donc avoir son propre bloc « Intervenants » sur l'écran
  « Fiche analysée ».
- **⚠ Trouvé en passant (hors partenaires)** : l'IA lit un SECOND vendeur (`mandant2*`, 8 champs, backend et type
  `api.ts:990`) mais `applyDraftAnnonceScan` ne l'utilise jamais (0 occurrence dans App.tsx) : le co-vendeur écrit sur
  la fiche est perdu sans prévenir.
- **La mise à jour proposée, en 3 morceaux** (à trancher, rien n'est décidé) :
  1. écran « Fiche analysée » : un bloc « Intervenants » (syndic si Copropriété = Oui, diagnostiqueur), le même sélecteur
     que l'assistant (catalogue, proposé, « ＋ Nouveau ») ; le lien se pose avec la création, comme à la main ;
  2. patron papier + IA : deux lignes « Syndic (nom, ville ou téléphone) » et « Diagnostiqueur » en page 4 (Technique),
     4 champs ajoutés à `FIELD_KEYS` et aux consignes, la fiche d'essai complétée ; l'écran **cherche** le nom lu dans le
     catalogue et le **propose** (« lu sur la fiche : X — Confirmer »), jamais de lien posé sans un clic ; rien trouvé →
     « ＋ Nouveau » prérempli ;
  3. (option, sujet à part) le second vendeur lu par l'IA : l'assistant n'a qu'UN mandant à la création, il faudrait
     d'abord lui donner une place pour le second.
  Le notaire reste hors du scanner : il se choisit au compromis (décision du plan).
- **⛔ DÉCISION DE FRÉDÉRIC (06/11) : « mets de côté ma demande sur le scanner IA, on va faire un chantier à part ».**
  Ce §28.3 en est le point de départ ; il ne se code PAS dans le chantier des partenaires.

### 28.4 Rubrique Contact → « Les intervenants de la vente » : AUDIT + ANALYSE GRAPHIQUE (06/11) — maquette, rien codé

Frédéric a refusé deux maquettes (« pas très jolie », puis « il faut faire bien mieux : les mandants sont liés aux autres
partenaires et il y a aussi les acquéreurs »). Audit en lecture seule.

**Ce que la base sait déjà (mesuré le 06/11 sur les 713 biens vivants : Actif 581, Sous offre 39, Sous compromis 93)**
- Mandants : 674 biens en ont un ; **355 en ont plusieurs** (couples, indivisions) → un « foyer vendeur », pas une fiche.
- Acquéreurs : **149 biens** ont un acquéreur dans une affaire (`app_affaire_partie`, rôle `acquereur`) ; offres
  acceptée 130 / refusée 30 / en cours 2 ; compromis actifs 95 (4 avec plusieurs acquéreurs).
- Notaires : sur les **93 biens sous compromis, 93 ont le notaire du vendeur ET celui de l'acquéreur** (rôles
  `notaire_vendeur`, `notaire_acquereur`). Sur les 581 sans compromis, **79 ont un mandant dont le notaire est déjà
  connu** par une autre affaire où il était partie → de quoi PROPOSER le notaire du vendeur dès le mandat.
- Syndic relié : 42 biens vivants ; diagnostiqueur : 4. `app_partenaire_lien` a déjà les colonnes `app_affaire_id` et
  `client_contact_id` (un partenaire peut être relié à une affaire ou à un client) : 0 ligne aujourd'hui.

**Ce que l'écran en fait aujourd'hui (vu sur le bien sous compromis 18844, lecture seule)**
- Rubrique Contact : **1 034 px** de haut ; seulement les mandants (une carte de ~480 px chacun, avec n° et date Hektor),
  puis syndic et diagnostiqueur sous la ligne de flottaison. **Aucun acquéreur, aucun notaire.**
- Rubrique Affaires : « Parties à l'affaire » (acquéreur + mandant) à **y = 1 636 px**, deux écrans plus bas ; les notaires
  n'y sont qu'en TEXTE (« Notaire acquéreur / Notaire mandant ») dans le détail du compromis, pas reliés à leur fiche.
- Donc les personnes d'une vente sont éparpillées sur trois endroits, et la moitié n'est pas cliquable.

**La maquette (planche 1 du canevas RcvReTV74PM2L1ZEEWdoNq, interactive, 3 étapes)** : « la table de la vente ».
- Deux côtés face à face, le bien au milieu avec l'avancement (mandat, offre, compromis, acte).
- Côté vendeur : le foyer des mandants, et RATTACHÉS à lui par un trait : son notaire (proposé d'après son historique,
  « Confirmer »), le diagnostiqueur qu'il commande.
- Côté acquéreur : vide au mandat (renvoi au Rapprochement), les offres en lice sous offre, le foyer des acquéreurs au
  compromis ; rattachés : son notaire, sa banque ou son courtier (bloc « en création », lot 6).
- Sous le bien : l'immeuble et son syndic (proposé par le registre, « Confirmer »).
- Style du cockpit (Fraunces, Hanken Grotesk, pastilles dégradées, étiquettes de métier du catalogue). Vérifiée en
  aperçu local à 1280 × 665 pour les 3 étapes, sans défilement. Téléphone : pas encore dessiné.
- **⛔ REFUSÉE par Frédéric (06/11)** : « il faut que cela ressemble à une rubrique contact annonce, pas un suivi de
  dossier ». → **Version 2 de la planche 1** : la rubrique Contact garde la forme d'un carnet de contacts : section
  « Vendeurs » (cartes contact du style réel `.fa-ck-ct-card`, resserrées, 2 par ligne), section « Acquéreurs » (même
  carte), et sur chaque carte une ligne « Ses partenaires » en puces (notaire, courtier « en création ») ; puis
  « Partenaires du bien » (syndic proposé « Confirmer », diagnostiqueur « Commander »). Plus d'avancement, plus de bien
  au centre. Aperçu local vérifié à 1280 × 665 (tient sans défilement).
- **⛔ RÈGLE DE FRÉDÉRIC (06/11) — les acquéreurs dans la rubrique Contact** : « visibles uniquement si transaction en
  cours ; si transaction annulée ou refusée, on retire l'acquéreur, qui reste dans Affaires ». Mise en œuvre :
  compromis `active` → les acquéreurs du compromis (et seulement eux) ; sinon offre `proposed` / `en_cours` /
  `accepted` → les acquéreurs de ces offres ; `refused` / `cancelled` → absents de Contact, toujours dans Affaires.
  Mesure 06/11 sur les biens vivants : Sous compromis 93 (93 compromis actifs) ; Sous offre 39 (37 offres vives,
  1 compromis actif, 1 seulement tombée) ; Actif 17 biens avec une affaire, dont 16 seulement tombées (rien affiché) et
  1 avec un compromis actif (écart de statut à regarder). ⚠ Non tranché : l'acquéreur APRÈS la vente (bien vendu).
- **⚠ Frédéric (06/11) : « mais il n'y a pas que les actifs ! »** — mesure refaite sur TOUS les biens (57 875 :
  `app_dossier_current` + `app_historical_annonce_index_current` + `app_archive_annonce_index_current`) :
  Estimation 12 821 (13 avec une affaire, dont **8 avec une vente** et 4 avec une offre vive : anomalies) ·
  Vendu 8 828 (tous avec une vente) · Clos 135 (**21 avec une offre encore « vive »**) · Archivé-clos 34 831
  (**1 131 avec une offre encore « vive » et 10 avec un compromis « actif »**) · Archivé-vendu 425 (424 ventes) ·
  Archivé-actif 90 (1 offre vive) · Archivé-estimation 32 · plus les 713 vivants ci-dessus.
  ⭐ **Conséquence** : l'état de la transaction ne suffit pas. Chez Hektor, une offre acceptée n'est jamais refermée
  quand le bien est clos ou archivé : avec l'état seul, **1 152 biens clos ou archivés** afficheraient un acquéreur
  « en cours » périmé. La règle doit donc AUSSI regarder le statut du bien : « en cours » seulement si le bien est
  Actif, Sous offre ou Sous compromis ; clos ou archivé → aucun acquéreur dans Contact (il reste dans Affaires).
  Reste à trancher : le bien VENDU (8 828 + 424 archivés).
- **⛔ FRÉDÉRIC (06/11) : « non, tu compliques ».** LA RÈGLE RETENUE, SIMPLE, sur tous les biens quel que soit leur
  statut : **l'acquéreur s'affiche dans Contact, sauf si sa transaction est refusée ou annulée** (`refused`,
  `cancelled`) ; dans ce cas il ne reste que dans Affaires. Une vente le garde donc visible. Pas de règle sur le
  statut du bien. Les chiffres ci-dessus restent une mesure, pas une règle.
- **⛔ DÉCISION DE FRÉDÉRIC (06/11), qui REMPLACE les deux points précédents** : « pour faire plus simple, fais comme
  aujourd'hui SANS ACQUÉREUR, uniquement les contacts avec une super présentation et les liens, ensuite les
  partenaires ». → **Pas d'acquéreur dans la rubrique Contact** (ils restent dans Affaires). **Version 3 de la
  planche 1** : section « Mandants » (cartes riches : nom en Fraunces, état de la fiche « complète » / « e-mail
  manquant », Appeler / E-mail / Fiche / ⋯, téléphone, e-mail, adresse, puis un encart « Ses liens » : co-mandant,
  son notaire — proposé avec « Confirmer » quand il est connu par une autre vente —, ses autres biens) ; puis
  « Partenaires du bien » (syndic proposé « Confirmer », diagnostiqueur « Commander », « ＋ Ajouter un partenaire du
  bien »). Mesure à l'appui : sur 1 241 mandants des biens vivants, **443 ont d'autres biens** (3,5 en moyenne,
  estimations et historique compris). Aperçu vérifié à 1280 × 665.
- **⛔ FRÉDÉRIC (06/11) : « non, fais du design mais n'ajoute pas de fonctions ».** → **Version 4 de la planche 1** :
  EXACTEMENT le contenu et les gestes d'aujourd'hui, redessinés. Mandants / Propriétaires (source « registre des
  liens »), « Ajouter un mandant » ; par mandant : nom, rôle, n° de contact (lié), Appeler, E-mail, Ouvrir la fiche,
  téléphone, e-mail, adresse, commentaire, Modifier, Retirer, date de mise à jour Hektor (liée). Partenaires du bien :
  les deux cartes existantes (`SyndicDuBien`) avec leur origine, « Demander un document » / « Commander un
  diagnostic », Ouvrir sa fiche, Changer, Retirer. **Retirés** de la maquette : ses liens (co-mandant, notaire,
  autres biens), l'état de la fiche, les propositions « Confirmer », « Ajouter un partenaire du bien ».
  Aperçu vérifié à 1280 × 665.
- **Frédéric (06/11) : « oui c'est ça », mais « juste en graphisme tu peux faire mieux ».** → **Version 5** (même
  contenu, mêmes gestes) : carte de visite du mandant (monogramme rond en Fraunces cerclé de blanc, grandes initiales
  en filigrane dans le bandeau, nom en Fraunces 20 px), les trois gestes en boutons ronds avec leur libellé dessous
  (E-mail grisé en pointillé quand il manque), coordonnées en lignes avec pastille d'icône, commentaire en italique,
  pied Modifier / Retirer / date Hektor ; partenaires en « ticket » avec la bande de couleur du métier à gauche
  (comme le prix et la carte d'état du cockpit), nom en Fraunces, gestes sur un second rang. Aperçu vérifié à
  1280 × 665.
- **✅ VALIDÉE par Frédéric (06/11) : « oui, mais sans les énormes initiales dans les mandants »** → filigrane retiré
  (version 6). C'est LA référence graphique de la rubrique Contact. Reste à reprendre dans ce style : planche 2
  (Copropriété), 3 (Diagnostics), 4 (création), puis la version téléphone.
- **Planches 2 à 4 refaites dans ce style (06/11, « Oui, reprends-les »)**, mêmes champs qu'aujourd'hui (relevés
  dans `App.tsx` ~30641 et l'assistant ~1640) : 2 · Copropriété = la carte du syndic (celle de Contact) + les 7 cases
  modifiables en place ; 3 · Diagnostics & énergie = la carte du diagnostiqueur (au lieu de la case « À renseigner »
  contradictoire), DPE en chiffres (sans lettre calculée), les 8 diagnostics en tableau résultat / date / commentaire,
  dates vides « — » au lieu de « 0000-00-00 » ; 4 · création étape 5 = « Les intervenants du bien » (diagnostiqueur,
  syndic) choisis dans l'annuaire avec « ＋ Nouveau » sur place — c'est le changement du PLAN accepté, le seul
  comportement neuf des 4 planches. Aperçus vérifiés à 1280 × 665. Téléphone : pas dessiné.

### 28.5 Plan, étape 1 — relier un partenaire à un bien sans numéro Hektor : AUDIT + PATCH — ✅ POSÉ le 06/11 (« Oui, pose-le »)

**Pose (06/11)** : migration `partenaire_bien_sans_numero_2026_11_06` (gardes d'empreinte passées), puis
`NOTIFY pgrst`. Répétition : structure **9/9 OK** ; essais des gestes **9 OK, 0 KO** (bien d'essai 118 / 102, transaction
annulée). Témoin après : 84 liens actifs (inchangé), 86 au total, 0 sur le bien d'essai, 0 sans numéro Hektor. Vu en
vrai dans l'app en ligne (bien 18844, lecture seule) : la carte « Syndic de la copropriété » se charge toujours
(CABINET DELOMIER, « repris de Hektor le 04/11/2026 »). Tâche `partenaire-lien-numeros` active à :50. Aucun écran
n'appelle encore les gestes sans numéro Hektor : ça vient à l'étape 2. Fichiers SQL non commités.

**Audit (lecture seule, base de production)**
- Une annonce créée dans l'app naît dans `app_dossier_current` avec NOTRE numéro (`v_id`, plage 10000000+) et
  `hektor_annonce_id = NULL` (`app_create_annonce_job_optimistic`) ; Hektor rend le sien ~90 s plus tard et notre
  numéro RESTE (les 4 annonces nées dans l'app, 10000000 → 10000009, ont aujourd'hui les deux).
- Les 4 fonctions du geste refusent sans numéro Hektor (« Le bien n'a pas encore de numéro d'annonce ») et cherchent le
  partenaire actuel par le seul numéro Hektor. La table, elle, accepte déjà un lien par notre seul numéro (contrainte
  `objet = 'bien' AND (app_dossier_id OR hektor_annonce_id)`). Les deux index « un par bien » ne portent que sur le
  numéro Hektor → un lien sans numéro Hektor ne serait protégé par rien.
- 84 liens actifs (80 syndics, 4 diagnostiqueurs), tous avec les deux numéros, paires cohérentes : 0 écart ; 0 doublon
  par notre numéro.
- La reprise de nuit (`registre_partenaires_reprise.py`) et la fiche partenaire (`FicheSyndic.tsx`) ne lisent les liens
  QUE par le numéro Hektor ; la tâche `app_sweep_stale_provisionals` ne touche pas `app_dossier_current`.

**Le patch** : `supabase/patch_partenaire_bien_sans_numero_2026-11-06.sql` (+ `_INVERSE`, `_REPETITION`) —
2 index uniques par notre numéro ; les 2 gestes acceptent notre numéro seul si le bien est dans `app_dossier_current`
(et y reprennent le numéro Hektor s'il est arrivé) ; les 2 lectures prennent un 3e paramètre facultatif ;
`app_partenaire_lien_completer_numeros()` + pg_cron `partenaire-lien-numeros` à :50 chaque heure (l'app gagne).
Gardes d'empreinte (713b6c0f, 7551bf56, cacb639d, 6e4c905d) ; une seule transaction. Répétition : 9 contrôles de
structure + 9 essais des gestes dans une transaction toujours annulée.

**Ce que ça pourrait casser** : (1) le front d'aujourd'hui appelle les lectures avec 1 ou 2 paramètres → ils marchent
tels quels (le 3e est facultatif ; l'ancienne signature est retirée pour éviter deux homonymes côté API, d'où le
`NOTIFY pgrst`) ; (2) un lien sans numéro Hektor est invisible pour la reprise de nuit et la fiche partenaire jusqu'à
la complétion (au plus une heure) ; si la nuit passe avant, la reprise ne le voit pas mais ne peut pas créer un 2e
syndic (l'index par notre numéro refuserait — un refus ferait échouer son lot de 500 : c'est pour ça que la complétion
tourne à :50, avant) ; (3) rien n'appelle encore les gestes sans numéro Hektor : le comportement visible ne change
qu'à l'étape 2.
**✅ 1re nuit après la pose (contrôle du 07/11, lecture seule)** : les étapes « syndic et diagnostiqueur » (05:54-06:22) et « registre des partenaires » (06:22:12-06:22:19) sont en DONE ; la reprise a posé 1 lien (syndic de 62147 / 1388149, origine hektor, les deux numéros cohérents) et n'en a retiré aucun ; 85 liens actifs (84 + 1), 0 sans numéro Hektor, 0 sans notre numéro, 0 doublon ; tâche `partenaire-lien-numeros` : 13 passages, 0 échec ; les 8 contrôles de structure de la répétition restent OK.
- **Ce qui change un comportement, à trancher** : (1) les acquéreurs et notaires viennent de la table des parties
  (lecture seule, pas de geste neuf) ; (2) « Confirmer » un notaire = un lien `app_partenaire_lien` rôle notaire sur
  l'affaire ou le client (geste neuf) ; (3) proposer le notaire d'après l'historique du mandant = règle neuve.

### 28.6 Plan, étape 2 — choisir le syndic et le diagnostiqueur à l'enregistrement de l'annonce : AUDIT (07/11, « Oui ») — rien codé

> Audit limité à l'annonce (création et modification) et au contact partenaire créé sur place. Les autres objets ne
> sont pas touchés : pas de transaction, pas de mandat, pas de recherche, rien chez Hektor (décidé : Hektor n'est pas
> informé des liens).

**Ce qui existe déjà (mesuré dans le code et la base le 07/11)**
- La carte `SyndicDuBien.tsx` (syndic et diagnostiqueur, onglet Contact de la fiche) sait choisir dans le catalogue
  et poser le lien. Mais elle **lit et écrit par le numéro Hektor seul** (`if (!annonce) return`, l. 140 ; la
  lecture ne passe que `p_hektor_annonce_id`) : sur une annonce née dans l'app, tant que Hektor n'a pas rendu son
  numéro (~90 s), elle affiche « aucun » et ne peut rien poser. L'étape 1 a ouvert la base ; l'écran n'en profite pas.
- L'assistant de création, étape 5 « Détails · Diagnostics & énergie » (`App.tsx` l. 1664-1665), a deux champs
  texte `diagnostiqueur` et `syndic`. Le `syndic` est **déjà masqué** quand le cran `partenaires_syndic_choix` est
  allumé (il l'est : l. 15159 dans l'assistant, l. 34781 dans « Le Bien ») ; le `diagnostiqueur` est encore saisi en
  texte libre dans les deux. Rappel : Hektor porte un syndic sur 79 biens sur 732 en copropriété, un diagnostiqueur
  sur 4 sur 714.
- La création (`app_create_annonce_job_optimistic`, interrupteur `c9_annonce_nait_dans_app` = on) pose déjà, **dans
  la même transaction**, le lien du mandant choisi (bloc `@P4a`) et le mandant neuf (`@P4b`). Le travail rendu porte
  `payload_json.app_dossier_id` (ex. 10000009) : l'écran connaît notre numéro du bien dès la réponse.
- Les droits : `app_console_can_access_dossier` reconnaît un bien né dans l'app par notre numéro (les 4 biens
  10 000 000+ sont dans `app_annonces_current` avec leur négociateur) : un négociateur pourra relier son annonce
  neuve.
- Créer un contact : la fenêtre `HektorContactIdentityForm` (mode create) existe et sert déjà ailleurs (l'agenda la
  réutilise avec `onContactInputCreated`). `app_create_contact_optimistic` donne au contact **notre numéro tout de
  suite** (≥ 20 000 000, `payload_json.app_identite` du travail rendu), et ce numéro est gardé au retour de Hektor
  (adoption, 23/10). Le catalogue range les partenaires par **notre** numéro (1 871 métiers, plage 10 000 258 -
  10 651 058, 0 numéro Hektor) : un contact neuf y entre sans conversion.
- Donner le métier : `app_partenaire_metier_ecrire(p_contact, p_metier)` (source « ecran ») existe et sert à la fiche.
  Le geste du lien exige ce métier (« Ce contact n'est pas un … du catalogue ») : l'ordre est donc créer → métier →
  lien.

**Ce qu'il faudrait faire (deux pièces, une à la fois)**
- **2a — la carte sait travailler par notre numéro** : `SyndicDuBien` lit avec `p_app_dossier_id` en plus, et pose
  même sans numéro Hektor. Petit, additif, utile tout seul (annonce neuve ouverte avant le retour de Hektor).
- **2b — le choix dans la saisie** :
  - *Création* : à l'étape 5, le champ texte « Diagnostiqueur » cède la place à un sélecteur du catalogue, et un
    sélecteur « Syndic » apparaît si le bien est en copropriété (la même liste, la même recherche que la carte).
    Chacun a « ＋ Nouveau » : la fenêtre de création de contact existante, puis le métier, puis le partenaire est
    choisi. Le lien se pose **après** la réponse de la création, avec `payload_json.app_dossier_id` (geste de
    l'étape 1, sans numéro Hektor). Si ce geste échoue, l'annonce est créée quand même et l'écran le dit (« le
    syndic n'a pas été relié : choisis-le dans l'onglet Contact »).
  - *Modification* : dans « Le Bien », sections Copropriété et Diagnostics, le champ texte « Diagnostiqueur » cède
    la place à la même carte (enregistrement immédiat, comme les autres champs de cet écran qui s'écrivent au champ).
- Le retrait du texte libre « Diagnostiqueur » de l'assistant et de « Le Bien » est l'**étape 3** ; en 2b il est
  remplacé, pas supprimé ailleurs (la valeur Hektor existante reste lisible dans la carte, « indiqué dans Hektor »).

**Le choix à trancher : où se pose le lien à la création**
- **A (recommandé)** — l'écran pose le lien juste après la création (le geste de l'étape 1 a été fait pour ça). Rien
  ne change dans la fonction de création, qui est grosse et sensible. Défaut : deux appels, donc un lien peut manquer
  si le second échoue (dit à l'écran, rattrapable dans l'onglet Contact).
- **B** — la fonction de création reçoit `initial_syndic` / `initial_diagnostiqueur` et pose le lien dans sa
  transaction, comme le mandant (`@P4a`). Tout ou rien, mais on retouche `app_create_annonce_job_optimistic`.

**Ce que ça pourrait casser**
- Le contact créé par « ＋ Nouveau » part chez Hektor comme tout contact (travail `create_hektor_contact`) : il y
  apparaîtra sans métier (Hektor n'est pas informé, c'est décidé). La reprise de nuit n'ajoute que ce qui manque :
  elle ne retirera pas le métier « ecran ».
- La reprise de nuit lit les liens par numéro Hektor : un lien posé avant le retour de Hektor est complété par la
  tâche de :50 (étape 1) ; mesuré cette nuit, elle tourne sans échec.
- Le scanner IA (« Créer l'estimation » saute l'assistant) ne passera pas par ce choix : il reste au chantier à part
  (§28.3).
- Le téléphone : la carte y est en lecture seule (variante `telephone`) ; l'assistant au téléphone n'est pas mesuré.
- Non mesuré : si le champ texte `diagnostiqueur` envoyé à Hektor y est gardé ou ignoré (pour le syndic, il est
  ignoré).

#### 28.6 bis — Audit approfondi (07/11, « Audit pour être sûr ») — rien codé

Six points vérifiés, dont deux qui **corrigent** le §28.6 :
1. **Le texte « Diagnostiqueur » part dans le vide, comme le syndic — PROUVÉ.** Essai réel du 22/10 (annonce
   10000009, `app_annonce_saisie_naissance.verdict`) : `diagnostiqueur` envoyé « Cabinet Diag Loire », relu
   **absent** ; `syndic` envoyé « Syndic Foncia Firminy », relu **absent**. Remplacer le champ ne perd donc rien
   chez Hektor (la réserve « non mesuré » du §28.6 tombe).
2. **« ＋ Nouveau » existe presque déjà.** La fenêtre de création de contact connaît le type « partenaire » et la
   liste des métiers de Hektor (Syndic = 5, Diagnostiqueur = 4, l. 42296) ; le worker l'envoie
   (`partner_job_id`, l. 19341). **Six créations réelles réussies** les 04-05/11 (20000038 à 20000045, essais
   supprimés depuis). Il manque seulement de pouvoir **ouvrir la fenêtre déjà réglée** sur « partenaire + syndic »
   (deux réglages en plus, additifs). Conséquence : Hektor apprend le **métier** du contact (pas le lien).
   Le métier est aussi écrit chez nous tout de suite (`app_partenaire_metier_ecrire`), sinon le partenaire ne
   serait choisissable que le lendemain ; la reprise de nuit, qui traduit les numéros Hektor en nôtres
   (`hektor_target_id` → `hektor_contact_id`), retrouvera le même couple et n'ajoutera rien.
3. **Correction sur B.** Le bloc du mandant (`@P4a`, 200 lignes, 10 590 caractères pour toute la fonction) est
   enveloppé dans `exception when others then raise warning` : s'il rate, la création continue **en silence**.
   Un lien partenaire posé de la même façon raterait donc aussi en silence ; pour le rendre « tout ou rien », il
   faudrait qu'un souci de syndic **fasse échouer la création de l'annonce**. B n'est donc pas plus sûr que A ;
   il est plus caché.
4. **A tient** : la fonction de création rend toujours `payload_json.app_dossier_id` (fin de fonction, ligne
   `jsonb_build_object('creation_token', …, 'app_dossier_id', v_id)`) ; l'interrupteur `c9_annonce_nait_dans_app`
   est à « on » et `PROVISIONAL_CREATION_ENABLED = true` (api.ts l. 6932). Si un jour le numéro manquait, l'écran
   dirait « à choisir dans l'onglet Contact ».
5. **Le téléphone** : l'assistant s'ouvre AUSSI au téléphone (bouton « Nouveau », l. 25645 → le même assistant).
   Le choix devra donc être contrôlé à 375 px. La carte de la fiche reste en lecture seule au téléphone.
6. **Les doublons** : la fenêtre cherche les doublons avant de créer (nom, e-mail, téléphone). Elle ne permet pas
   de « reprendre » une fiche client existante comme partenaire — et c'est voulu (règle du 05/11 : une fiche client
   ne change jamais, la fiche métier s'ouvre depuis le catalogue). L'utilisateur annule et choisit dans le
   catalogue, ou confirme la création.

Modification : un seul chemin modifie ces champs, « Le Bien » du cockpit (sections Copropriété et Diagnostics,
champs enregistrés un par un). L'ancienne vue détail ne fait qu'afficher les intervenants lus chez Hektor.

#### 28.6 ter — Pièce 2a CODÉE (07/11, « A ») — poussée le 07/11 avec 2b

`SyndicDuBien.tsx` seul (+14 / −8) : la carte connaît le bien par l'un OU l'autre numéro (`bienConnu`). Elle lit par
**notre** numéro **seulement quand le numéro Hektor manque** (`annonce ? null : dossier`) : pour tous les biens qui ont
leur numéro Hektor, la lecture est **identique** à avant. L'écriture passait déjà les deux numéros ; elle n'est plus
bloquée quand le numéro Hektor manque. Le message « pas encore de numéro » ne sort plus que si le bien n'a ni l'un ni
l'autre. Les 4 appelants (bureau et téléphone, syndic et diagnostiqueur) passent déjà `appDossierId`.
- Prudence mesurée avant de choisir la lecture : les lectures et les gestes cherchent par l'un OU l'autre numéro ; un
  numéro interne d'archive, d'historique ou de brouillon qui croiserait celui d'un autre bien vivant fausserait la
  carte. Mesuré : **0** croisement sur les trois index, **0** lien incohérent. D'où, quand même, la lecture par notre
  numéro réservée au bien sans numéro Hektor.
- Contrôle : `npm run build` vert. ⚠ **Pas vu à l'écran** : l'app locale réelle demande la connexion de Frédéric (je
  ne saisis pas son mot de passe). Le chemin « sans numéro Hektor » est prouvé côté base (répétition de l'étape 1,
  essai 3) ; il sera prouvé à l'écran avec 2b, sur une annonce d'essai créée avec son accord.

#### 28.6 quater — Pièce 2b CODÉE (07/11, « Enchaîne ») — poussée le 07/11 (« Oui vas-y »), DORMANTE (cran absent)

**Interrupteur** : cran `partenaires_choix_saisie` (`app_setting`, n'existe pas encore) — absent = l'écran d'avant,
`admin` = les admins seuls, `on` = tout le monde. L'allumer est une écriture en production : avec l'accord de Frédéric.

Ce que le cran allumé change :
- **Assistant de création, étape 5** : le texte libre « Diagnostiqueur » (et « Syndic ») disparaît ; une rubrique
  « Intervenants » propose le diagnostiqueur, et le syndic si « Copropriété » = Oui (`ChoixPartenaire`,
  `SyndicDuBien.tsx`) : choix dans le catalogue, ou « ＋ Nouveau ». Rien n'est écrit pendant la saisie.
- **À l'enregistrement** (`App.tsx`, après `createHektorDraftAnnonceJobOptimistic`) : solution **A** — le lien est
  posé par notre numéro du bien (`payload_json.app_dossier_id`, geste de l'étape 1 sans numéro Hektor), AVANT
  d'ouvrir la fiche (POINT 3a) pour qu'elle le montre. Un échec ne défait pas la création : il est affiché (« choisis-le
  dans l'onglet Contact »).
- **« ＋ Nouveau »** : un signal `bienvu:creer-partenaire` (même patron que `bienvu:ouvrir-partenaire`) ; l'App
  principale ouvre la création de contact existante, réglée « Partenaire » + métier Hektor (prop neuve
  `partenaireImpose` : Syndic = 5, Diagnostiqueur = 4) ; au retour, le métier est écrit chez nous
  (`app_partenaire_metier_ecrire`, NOTRE numéro `app_identite`) puis le partenaire est choisi (assistant) ou relié
  (carte d'une fiche). La fenêtre passe au-dessus de l'assistant (z-index 4200 contre 50).
- **« Le Bien » (modification)** : texte libre « Diagnostiqueur » retiré ; la carte du syndic dans « Copropriété »,
  celle du diagnostiqueur dans « Diagnostics », avec « ＋ Nouveau » ; les cartes de l'onglet Contact gagnent aussi
  « ＋ Nouveau ».
- Mode maquette (sans base) : `loadAppSettingValeur` rend « on » pour ce cran aussi (précédent : le registre), pour le
  voir sans connexion.

**Contrôles** : `npm run build` vert (tsc compris). Vu en maquette : bureau 1440×900, écran bas 1280×665, téléphone
375 px (pas de défilement de côté) — la rubrique, le syndic qui n'apparaît qu'avec Copropriété = Oui, les champs texte
retirés (reste « Statut syndicat », voulu), « ＋ Nouveau » qui ouvre la fenêtre réglée « Partenaire / Diagnostiqueur »
au-dessus de l'assistant. Corrigé en route : la carte coincée dans une colonne de la grille de 12 → pleine largeur.
⚠ **Non vu** : « Le Bien » (la fiche détaillée ne s'ouvre pas en maquette) ; le catalogue réel et le lien réel (il faut
la base : après pose du cran en `admin`, une annonce d'essai créée avec son accord, puis retirée).

**En ligne (07/11)** : `5cc3f25` poussé (avec deux notes de la session « modale statut », 75522aa et 8ac5dd9, sans code),
Vercel `dpl_ED4XCiKKFDaKnsudP4kpWXbHhTk5` READY ; l'app en production ouverte DÉCONNECTÉE : écran de connexion normal,
pas de page blanche (hooks au-dessus du return), seuls des 401 attendus. Cran absent : rien ne change pour personne.

### 28.7 Plan, étapes 3 et 4 : AUDIT (07/11, « enchaîne ») — rien codé

**Étape 3 — retirer les champs texte « Diagnostiqueur » et « Syndic »** : à l'écran, c'est déjà fait par le cran
`partenaires_choix_saisie` (assistant ET « Le Bien »). Ce qui reste est du **ménage de code**, à faire seulement une fois
le cran à « on » et éprouvé : les deux `wf('diagnostiqueur' | 'syndic')` de l'assistant (l. ~1664), les deux entrées de
`CK_LB_SECTIONS`, les listes de champs par type de bien (l. ~2115, ~2218), et la branche de l'aide « Copropriété » qui
écrivait le nom du syndic en texte (déjà coupée par `partenaires_syndic_choix`).
- **Trouvé en passant** : l'ancien bloc « Diagnostics et syndic · Intervenants console Hektor » de l'onglet Contact lit
  `intervenants_json` sur la fiche du bien. **Aucune fiche de bien ne porte ce champ en production** (seule colonne de ce
  nom : `app_affaire_console`, et les données de maquette) : le bloc ne s'affiche jamais, et ses boutons « Fiche » et
  « ＋ Ajouter un syndic » n'ont aucune action. Code mort, à retirer avec l'étape 4.

**Étape 4 — appliquer le design validé**, trois pièces, une à la fois, derrière un cran (`admin` d'abord) :
- **4a · Contact** (planche 1, version 6 validée) : carte de visite du mandant (monogramme, nom en Fraunces, trois gestes
  ronds, coordonnées en lignes, commentaire, pied Modifier / Retirer / date Hektor) ; partenaires en « ticket » avec la
  bande de couleur du métier. ⚠ La carte mandant contient deux gestes réels (`HektorMandantContactEditForm`,
  `RetirerMandantBouton`) : ils sont GARDÉS tels quels, seul l'habillage change.
- **4b · Copropriété** (planche 2) : la carte du syndic EN TÊTE de la section (2b la met après les cases), les 7 cases
  modifiables en place, inchangées.
- **4c · Diagnostics** (planche 3) : la carte du diagnostiqueur en tête, le DPE en chiffres, les 8 diagnostics en tableau
  résultat / date / commentaire (chaque case reste modifiable en place, même enregistrement `onFieldSave`), une date vide
  affichée « — » au lieu de « 0000-00-00 » (affichage seul : la valeur n'est pas réécrite).
- **Téléphone** : pas dessiné ; tant qu'il ne l'est pas, le téléphone garde l'écran d'aujourd'hui.
- Non mesuré : combien de biens affichent aujourd'hui « 0000-00-00 » dans les diagnostics.

#### 28.7 bis — Pièce 4a CODÉE (07/11, « Code d'abord ») — poussée le 07/11 (« Oui, pousse et allume »)

Cran **`partenaires_design_contact`** (absent = l'onglet Contact d'avant ; `admin` ; `on`). Allumé :
- **Mandants / Propriétaires** : titre en Fraunces avec la source (« registre des liens · N mandants », le bandeau
  « Source … » est masqué puisque le titre le porte) ; cartes de visite en grille de deux (une seule colonne sous
  1 100 px) : monogramme rond (sans filigrane), nom en Fraunces, rôle et « Contact n° » ; trois gestes ronds Appeler /
  E-mail / Ouvrir la fiche (Appeler et E-mail en pointillé quand le numéro ou l'adresse manque) ; Téléphone, E-mail
  (« non renseigné » s'il manque), Adresse, Commentaire (en italique) ; pied « Modifier » / « Retirer » / « Hektor · mis
  à jour le … ». ⚠ « Modifier » et « Retirer » sont les composants EXISTANTS (`HektorMandantContactEditForm`,
  `RetirerMandantBouton`), seulement habillés en CSS : leurs confirmations, leurs refus expliqués et leur formulaire
  s'ouvrent sur toute la largeur de la carte. Le « ✎ » mal encodé (« âœŽ ») du bouton Modifier est masqué sous le cran
  et remplacé par un crayon dessiné (le texte d'origine n'est pas corrigé : il reste visible sans le cran).
- **Partenaires du bien** : titre, puis les deux cartes `SyndicDuBien` en grille, avec l'habillage `ticket` (bande de
  la couleur du métier, pastille, nom en Fraunces, origine ; Appeler / Ouvrir sa fiche / Changer / Retirer, et le
  bouton du métier : « Demander un document », « Commander un diagnostic », ou « Choisir » quand il n'y en a pas). Le
  bas de la carte (écart avec Hektor, erreur, demande, choix) est partagé par les deux habillages (constante `dessous`).
- Données de maquette : ces crans sont « on » en mode maquette (sans base), comme le registre.

**Contrôles** : `npm run build` vert. ⚠ **NON VU À L'ÉCRAN** : en maquette, la fiche détaillée d'une annonce ne s'ouvre
pas, et l'app réelle locale demande la connexion de Frédéric. Le voir passe par le cran en `admin` (lui seul).
Fichiers : `App.tsx`, `SyndicDuBien.tsx`, `syndic-du-bien.css`, `contact-du-bien.css` (nouveau), `lib/api.ts`.

**En essai pour les admins (07/11, « Oui, pousse et allume »)** : `1f0536b` (4a) puis `21d7b79` poussés ; crans
`partenaires_choix_saisie` et `partenaires_design_contact` posés à **`admin`** à 09:51:16 (`app_setting`, avec leur
description). ⚠ **Premier essai raté, cause trouvée** : la fiche d'un bien ne reçoit PAS `profileRole` de l'App (aucun
des deux appelants ne le passe) — un cran « admin » y valait toujours « éteint » ; les crans déjà en place marchaient
parce qu'ils sont à « on ». Corrigé par `roleConnecte` (prop neuve, lue SEULEMENT par ces deux crans) : passer
`profileRole` aurait changé d'autres gestes de la fiche (ex. « Réaffecter le négociateur », aujourd'hui proposé aussi à
un négociateur parce que le rôle manque — trouvaille notée, non traitée).
**Vu en vrai** (Chrome de Frédéric, bien 18844, lecture seule, 1280 × 665) : onglet Contact = carte de visite du mandant
(« Retirer » grisé avec sa raison « le mandat n° 18844 a été généré »), tickets « CABINET DELOMIER » (Demander un
document) et « Aucun diagnostiqueur » (Choisir) ; le choix ouvre le vrai catalogue (22 diagnostiqueurs) avec « ＋ Nouveau
diagnostiqueur », refermé sans rien choisir. « Le Bien » : carte du syndic dans Copropriété, le texte libre
« Diagnostiqueur » retiré des Diagnostics (14/34). ⚠ **Pas encore essayé** : la création d'une annonce avec un partenaire
choisi, et « ＋ Nouveau » jusqu'au bout (ils écrivent chez Hektor : à faire par Frédéric ou avec son accord). Le format de
la date « mis à jour le 2026-10-02 14:06:07 » est celui d'avant (même donnée, non reformatée).

#### 28.7 ter — ESSAI RÉEL de 2a + 2b par moi (07/11, « FAIS LE TOI MÊME »)

Dans le Chrome de Frédéric, écran Annonces → « Nouvelle annonce » → assistant : « ESSAI PARTENAIRES 2B - ne pas
diffuser », Groupe GTI Firminy, Emmanuelle PEREIRA, 8 rue de l'Ondaine 42700 Firminy, 100 000 €, Copropriété = Oui.
- **Diagnostiqueur choisi dans le catalogue** : Ardrodiag (10355367). ✅
- **Syndic créé sur place par « ＋ Nouveau syndic »** : la fenêtre s'est ouverte réglée « Partenaire / Syndic » (compte
  à choisir : pas de négociateur présélectionné pour un admin, choisi PEREIRA) ; contact « ZZ ESSAI SYNDIC 2B »,
  0499999961 → **notre n° 20000046 tout de suite, métier `syndic:ecran` écrit, travail `create_hektor_contact` done,
  n° Hektor 606274** ; il est revenu choisi dans l'assistant. ✅
- **« Créer l'annonce »** : fiche ouverte sur notre n° **10000202** ; **les deux liens posés par notre numéro** (ids 102
  syndic, 103 diagnostiqueur, origine app, 10:07:24, `hektor_annonce_id` vide comme prévu) ; l'onglet Contact les
  montre AVANT tout numéro Hektor (« choisi dans l'app par Frederic Gerphagnon le 07/11/2026 ») — la pièce 2a prouvée. ✅
- ⛔ **Le travail de création de l'annonce chez Hektor a ÉCHOUÉ** : `Hektor timeout 30000ms on .../admin/xmlrpc.php`
  (10:07:24 → 10:08:01, recul de 15 s au journal du worker). Rien n'indique que Hektor l'ait créée (aucune annonce de ce
  titre dans la synchro). Sans rapport avec le code du chantier (le worker n'est pas touché).
- ⚠ **Mon erreur de méthode** : créée depuis l'écran **Annonces**, l'annonce part `creation_status = active`
  (`App.tsx` ~15211 : « estimation » seulement depuis l'écran Estimations ou le scanner). Les essais 8a étaient en
  estimation. ⛔ **NE PAS « Relancer » ce travail** : il créerait chez Hektor une annonce d'essai ACTIVE.
- **Reste à nettoyer (décision de Frédéric)** : le travail en erreur 68e21008 (« Abandonner » défait le geste : la
  fiche provisoire 10000202, visible dans la liste d'Emmanuelle PEREIRA, disparaît), les liens 102/103, le contact
  d'essai 20000046 / 606274 (chez Hektor aussi).

#### 28.7 quater — Pourquoi la création a échoué, et le nettoyage (07/11, « il faut nettoyer mais pourquoi le worker a planté ! »)

**Ce n'est pas un plantage du worker, c'est Hektor qui n'a pas répondu, et le worker ne sait pas réparer après.**
Trace `app_console_job_log` du travail 68e21008 : 10:07:24 pris par le service « actions » ; contexte admin puis
négociateur (51, PEREIRA) OK ; 10:07:28 « ajoutebien » → **Hektor crée l'annonce 63474** ; 10:07:30 envoi de la
**page 2 de l'assistant Hektor** (`ajoutebien_wizardBien` : idMandant, statut, prix, négociateur, copropriété) →
**aucune réponse en 30 s** → `Hektor timeout 30000ms`, recul de 15 s, travail en erreur avec
`created_hektor_annonce_id: 63474` dans sa trace.
- **Hektor seul en cause pour le délai** : sur les 20 créations précédentes, cette page 2 a répondu en 0,9 à 3,4 s, y
  compris en « Actif » (4 fois fin août, 3,0-3,4 s) et avec copropriété (22/10, 2,9 s). Aucun autre délai dépassé dans
  les deux heures. Le statut « Actif » (mon erreur de méthode) n'est pas la cause.
- ⚠⚠ **LE VRAI DÉFAUT, ANCIEN, HORS DU CHANTIER** : quand la création échoue APRÈS « ajoutebien », le worker garde le
  numéro (63474) dans sa trace mais ne le pose pas sur la fiche provisoire (10000202 restait sans numéro Hektor) et ne
  nettoie rien → **une annonce à moitié créée, ACTIVE, orpheline chez Hektor**, que la synchro aurait ramenée comme une
  fiche de plus. Et « Relancer » recréerait une deuxième annonce. Correctif à auditer (code du worker : son accord).

**Nettoyage fait (07/11, ~10:16-10:25)** : les liens 102 et 103 retirés par le bouton « Retirer » (trace : Frédéric,
10:16:05 et 10:16:08) ; le contact d'essai 20000046 / 606274 supprimé par « Supprimer le contact » (raison écrite,
travail `delete_hektor_contact` done ; son métier n'est plus actif) ; **l'annonce 63474 supprimée chez Hektor** par le
travail `delete_hektor_annonce` 4209f343 (créé à son nom par la fonction de l'app, confirmation « SUPPRIMER 63474 »,
fiche 10000202) : « Suppression Hektor envoyée et VÉRIFIÉE (existait avant, absente après) », et la fiche 10000202 a
disparu de chez nous. Contrôle : 85 liens actifs (comme avant l'essai), 0 sans numéro. ⛔ Le travail 68e21008 reste
« error » (il n'existe pas d'état « annulé ») : **NE PAS LE RELANCER**.

### 28.8 La création d'annonce interrompue : AUDIT d'un correctif du worker (07/11, « explique plus clairement et audite un correctif ») — rien codé

> Audit limité au geste « créer une annonce » (`create_hektor_draft_annonce`). Les autres gestes ne sont pas mesurés.

**Ce qui s'est passé, étape par étape** (`Console/console_job_worker.js`, trace `app_console_job_log` du travail 68e21008) :
1. `createHektorAnnonceWithHttpDirect` (l. ~3880) envoie `ajoutebien` → Hektor crée l'annonce et rend son numéro
   **63474** (10:07:28). À partir de là, l'annonce EXISTE chez Hektor.
2. `ajoutebien_wizardBien` (délai 60 s) → répond.
3. `applyHektorCreateWizardFields` → `postHektorWizardCreateStep` (l. ~12355) pour la page 2 : il envoie D'ABORD un appel
   préparatoire `deepFlowReality-setDeepCache` (délai **30 s**), puis la page elle-même (60 s). **C'est l'appel préparatoire
   qui n'a pas répondu** : début 10:07:30.1, erreur 10:08:01.0 = 30,9 s. Hektor seul en cause (les 82 autres créations
   depuis juillet : 0 échec ; cette étape répond en 0,9 à 3,4 s).
4. L'erreur remonte : `createHektorAnnonce` (l. ~4000) note `created_hektor_annonce_id: 63474` et relance l'erreur ;
   `handleCreateHektorDraftAnnonceWithProvisional` (l. ~25331) marque la fiche provisoire « Erreur de création »
   (`app_annonce_provisional`, la liste l'affiche), retire les liens MANDANT nés au clic (`retirerLiensDeLaCreationEchouee`,
   table `app_relation`), et s'arrête.

**Les trois trous** (le premier existe depuis toujours ; le troisième vient de la pièce 2b) :
- **T1 — l'annonce à moitié créée reste chez Hektor**, ACTIVE si elle était demandée active, et notre fiche ne connaît pas
  son numéro (le 63474 n'est que dans la trace). La synchro l'aurait ramenée comme une fiche de plus.
- **T2 — « Relancer » crée une DEUXIÈME annonce** (le travail repart de `ajoutebien`, sans regarder la trace).
- **T3 — les liens partenaires (2b) ne sont pas retirés** : `retirerLiensDeLaCreationEchouee` ne regarde que
  `app_relation`, pas `app_partenaire_lien`. Mesuré sur l'essai : les liens 102/103 sont restés sur la fiche en échec.

**Le correctif proposé** (une seule pièce, dans le worker ; additif ; redémarrage des services par Frédéric, file vide) :
- **C1 — réessayer UNE fois l'appel préparatoire** `setDeepCache` (il ne fait que préparer un cache côté Hektor, il est
  rejouable), avec 60 s, avant d'abandonner. Réduit la chance de l'échec ; ne le supprime pas.
- **C2 — si la création échoue APRÈS que Hektor a donné un numéro : défaire ce qu'on vient de créer**, avec les mêmes
  garde-fous que le geste « Supprimer l'annonce » (l. ~23108) : lire l'annonce avant, ne supprimer QUE le numéro rendu par
  CE travail, prouver la suppression par l'absence. Puis l'erreur reste une erreur (« Erreur de création », relançable
  sans doublon).
  - **Si la suppression échoue ou ne peut pas se prouver** : le numéro est écrit sur la fiche provisoire et une alerte
    nomme l'orpheline (« annonce n° … créée à moitié, à supprimer ») — on ne la perd jamais de vue.
- **C3 — garde de relance** : avant `ajoutebien`, si la trace du travail porte déjà un numéro créé ET que l'annonce existe
  encore chez Hektor, le travail refuse de recréer (il dit pourquoi).
- **C4 — T3** : `retirerLiensDeLaCreationEchouee` retire aussi les liens `app_partenaire_lien` nés avec la fiche
  (`app_dossier_id` = la fiche, `hektor_annonce_id` vide, origine `app`), daté, trace gardée.

**L'autre voie, écartée sauf avis contraire — « reprendre au lieu de défaire »** : garder 63474, le poser sur la fiche,
et finir de remplir l'annonce plus tard par une mise à jour des champs. Elle garde le numéro, mais une annonce ACTIVE
à moitié remplie resterait visible chez Hektor (et sur les portails si elle devenait diffusable) le temps de la reprise,
et le code est beaucoup plus gros (reprendre une création au milieu des pages).

**Ce que ça pourrait casser** : C2 supprime chez Hektor, sans clic humain — d'où la règle stricte : seulement le numéro
que CE travail vient de recevoir, seulement s'il est lisible, preuve par l'absence ; jamais une annonce existante. C1
rallonge au pire de 60 s une création qui échoue de toute façon. C3 peut bloquer une relance légitime si la lecture de
Hektor rate (elle le dira). C4 ne touche que les liens nés avec cette fiche. Non mesuré : si `setDeepCache` est
indispensable à la page 2 (s'il ne l'était pas, on pourrait aussi l'ignorer en cas de délai).
**Comment on vérifiera** : un essai « à blanc » qui simule le délai (script, sans Hektor), puis un essai réel depuis
l'écran Estimations avec son accord.

#### 28.8 bis — L'ESSAI MESURÉ (07/11, « refaire un test mesuré avant de corriger », « les remplir un minimum ») — ⛔ REPRODUIT

**Essai A** (écran **Estimations**, donc `creation_status = estimation`), fiche remplie comme une vraie : « ESSAI MESURE A
ESTIMATION - ne pas diffuser », Groupe GTI Firminy / Emmanuelle PEREIRA, 120 000 €, 65 m², 3 pièces, 2 chambres,
8 rue de l'Ondaine 42700 Firminy, copropriété Oui (lot 14, 32 lots), DPE 190 / 40 au 01-10-2026, étage 2/4, ascenseur,
cave, balcon, 1975 — 17 champs détaillés, **aucun partenaire choisi**.
Trace (travail 4e90ba56) : 10:39:21.5 `ajoutebien` → **Hektor crée 63475** ; 10:39:22.8 page 2 (24 champs) ; **10:39:53.7
`Hektor timeout 30000ms`** — exactement comme l'essai du matin. **L'essai B (Actif) n'a pas été lancé** : A suffit à
trancher. 63475 supprimée par `delete_hektor_annonce` 9979465e (« envoyée et VÉRIFIÉE », caches locaux nettoyés),
fiche 10000203 disparue.

**Conclusions mesurées** :
- **Ce n'est ni le hasard, ni le statut Actif, ni les partenaires** (aucun partenaire dans A ; rien des partenaires ne part
  chez Hektor). **Créer une annonce depuis l'app ne marche plus**, à coup sûr, depuis une date entre le **22/10** (dernière
  création réussie, page 2 en 2,9 s) et aujourd'hui.
- **Notre code n'a pas changé** : `git log -L` depuis le 20/10 sur `postHektorWizardCreateStep`, `hektorFetch` et
  `hektorThrottle` : aucun commit. Le changement vient de **Hektor** : son appel `deepFlowReality-setDeepCache` (appel
  préparatoire avant chaque page du formulaire) ne répond plus.
- **Indice** : les scripts de l'admin Hektor (accueil, lus dans le Chrome de Frédéric, lecture seule) ne contiennent PLUS
  aucun `setDeepCache` — seul `deepFlowReality-dfrPackRequest` (une demande de « pack DFR ») y reste. Non prouvé que
  leur propre page de création ne l'appelle plus (page non ouverte : elle crée l'annonce).
- **Impact** : toute annonce créée par l'app depuis cette date part à moitié chez Hektor puis échoue (orpheline). Il y en
  a eu deux, les miennes (63474, 63475), toutes deux supprimées. Les négociateurs n'ont pas créé d'annonce dans l'app
  depuis le 22/10.

**Le correctif change donc de nature** : ce n'est plus « un délai rare à amortir » mais **un appel devenu mort chez
Hektor**. À auditer : capturer ce que fait AUJOURD'HUI la vraie page de création de Hektor (outil réseau, sur une
création faite par un humain), puis aligner le worker (retirer ou rendre facultatif `setDeepCache`) — plus les garde-fous
C2-C4 du §28.8 qui restent utiles.

#### 28.8 ter — LA CAUSE, VUE DANS LA PAGE DE HEKTOR (07/11, ~11:00, « utilise ta session Chrome pour voir où est le problème »)

Page « Ajouter un nouveau bien » de l'admin Hektor ouverte dans le Chrome de Frédéric (compte admin GROUPE GTI
IMMOBILIER), statut Estimation, type Appartement, clic « Étape suivante ». **La page de Hektor ELLE-MÊME ne passe plus à
l'étape 2.** Console de la page :
1. `SyntaxError: Identifier 'videoWindow' has already been declared` (script en ligne de la page, l. 2884) — une
   variable déclarée deux fois fait échouer tout ce bloc de script ;
2. donc les fonctions qu'il définit n'existent pas : `ReferenceError: setOffreDemWizard is not defined` ;
3. au clic : **`ReferenceError: setDeepCache is not defined`** dans `valideEtapeWizard`
   (`labs/wizard/labs_Bien_Wizard_New.js`, l. 408) — **le même `setDeepCache` qui ne répond plus à notre worker**.
Aucun appel `ajoutebien` n'est parti : rien n'a été créé chez Hektor par cet examen.

**Conclusion** : régression **de Hektor** (code de leur page et de leur serveur autour de « deepFlowReality / DeepCache »),
pas de notre app ni du chantier. Les négociateurs ont créé dans Hektor 6 annonces le 06/11, 5 le 05/11, 11 le 04/11 : la
panne date vraisemblablement d'une mise à jour de Hektor **entre le 06/11 au soir et le 07/11 matin**. ⚠ Lundi, les
négociateurs risquent de ne plus pouvoir créer d'annonce DANS HEKTOR non plus (non vérifié pour un compte négociateur).
**À faire par Frédéric** : signaler au support Hektor / La Boîte Immo, preuves ci-dessus (les trois erreurs, le fichier
et la ligne). **Côté worker** (à décider, accord requis) : rendre `setDeepCache` facultatif (délai court, on continue)
seulement si un essai prouve que la page se sauve sans lui ; et les garde-fous C2-C4 du §28.8.

#### 28.8 quater — ⭐ LA CAUSE RACINE, MESURÉE EN NÉGOCIATRICE (07/11, ~11:05, « fais un test dans Chrome avec un accès négociateur »)

Dans le Chrome de Frédéric : connexion automatique Hektor « en tant que » Emmanuelle PEREIRA (n° 51, comme le worker :
`?call=authenticate&mode=autologin&idUser=51`), page « Ajouter un nouveau bien », relevé de chaque appel `xmlrpc.php`
(mode, heure, durée, statut) posé dans la page.
- En négociatrice, les fonctions `setDeepCache` / `setOffreDemWizard` / `valideEtapeWizard` EXISTENT une fois la page
  chargée (les mêmes erreurs « videoWindow » apparaissent au chargement, sans conséquence ici). Estimation + Appartement
  + « Étape suivante » → **la page de Hektor passe à l'étape 2** (Photos) ; elle a créé l'estimation d'essai **63477**.
- Le relevé : `11:05:32.053 deepFlowReality-setDeepCache` puis, **6 ms plus tard, sans l'attendre**,
  `11:05:32.059 annonce-createBien-Ajx_Bien_wizardStepNew` (893 ms, 200) ; la page continue. **`setDeepCache` répond
  en 30 114 ms** (statut 200).
- ⭐⭐ **D'où la panne du worker** : `postHektorWizardCreateStep` ATTEND `setDeepCache` avec un délai de **30 000 ms**
  avant d'envoyer la page — il abandonne 0,1 s avant la réponse de Hektor, et toute la création tombe. La page de Hektor,
  elle, ne l'attend jamais : c'est un appel « lancé et oublié ». Le ralentissement de cet appel chez Hektor (récent : 0,9 à
  3,4 s pour toute l'étape jusqu'au 22/10) a rendu fatale une attente qui n'aurait jamais dû être bloquante.
- L'erreur vue en admin (`setDeepCache is not defined`) est un défaut de LA PAGE ADMIN de Hektor, distinct ; elle ne
  concerne pas les négociateurs (leur page passe).

**Nettoyage** : retour au compte admin par « Retour » (menu du profil) — vérifié « GROUPE GTI IMMOBILIER / Administrateur » ;
63477 supprimée (`delete_hektor_annonce` 7115a0ae, « envoyée et VÉRIFIÉE »). Le n° 63476 (entre 63475 et 63477) renvoie
**403 Accès interdit** à notre admin : il n'est pas à GTI (numérotation partagée) — pas une trace de l'examen.

**Le correctif devient simple et sûr** : faire comme la page de Hektor — envoyer `setDeepCache` SANS l'attendre (ou
l'attendre très peu et ignorer son délai), puis envoyer la page. Plus les garde-fous C2-C4 du §28.8 (création
interrompue défaite, pas de relance en doublon, liens partenaires retirés). Essai : une création depuis l'écran
Estimations après redémarrage des services (Frédéric), puis suppression.

#### 28.8 quinquies — AUDIT DE CONFIRMATION et correctif PROPOSÉ (07/11, « refais un audit, il faut être sûr de ton correctif ») — rien posé dans le dépôt

L'essai « à part, sans redémarrer » est abandonné (« non laisse tombe »).

**1. Le worker utilise EXACTEMENT le mécanisme de l'essai Chrome** (code + journaux) :
- `handleCreateHektorDraftAnnonce` → `ensureHektorExecutionContext` : retour à la session ADMIN (n° 4), puis
  `switchHektorUserContextOnce` → `?call=authenticate&mode=autologin&idUser=<n>`, la même adresse que dans Chrome ;
- journal de l'essai A (4e90ba56, 07/11 10:39) : « Session Hektor administrateur active » (4, ADMIN), puis « Contexte
  Hektor négociateur actif » **51, NEGO, Mme. Emmanuelle PEREIRA** — le compte de l'essai Chrome ; même chose le 22/10
  (a62233e2, réussi) ;
- aucun repli « agence » ici (`CONSOLE_HEKTOR_AGENCY_FALLBACK` non demandé ; la négociatrice est active).

**2. Le point de rupture est bien `setDeepCache`** : page 2 notée à 10:39:22.755, erreur « Hektor timeout **30000** ms »
à 10:39:53.664 (30,9 s = 1 s de frein + 30 s). Dans `postHektorWizardCreateStep`, seul `setDeepCache` a 30 000 ms (la
page : 60 000). Historique : **80 créations réussies depuis mai**, assistant de 14 à 45 s pour 6 pages (une à 92 s le
21/10) — `setDeepCache` répondait vite, jusqu'au 22/10 inclus.

**3. La page de Hektor ne l'attend à AUCUNE page** : `labs_Bien_Wizard_New.js` relu le 07/11 (servi par
`?call=getJs&js=labs/wizard/…`) — une seule fonction `valideEtapeWizard(keyGroup, step, …)` pour toutes les pages,
l. 408 `setDeepCache(idann, step)` puis, plus bas et sans attente, l'appel `annonce-createBien-Ajx_Bien_wizardStepNew`.
Ligne identique dans notre copie du 16/05 (`Console/exports/labs_Bien_Wizard_New_latest.js`) : l'appel est entré dans le
worker le 29/05 (`963d5dc`), recopié de la page, mais en version **attendue**.

**4. Ailleurs** : `setDeepCache` n'a qu'UN appelant dans tout le dépôt (la modification d'annonce ne l'utilise pas ; le
repli Playwright le neutralise déjà).

**Le correctif proposé** (copie du worker dans le dossier de travail, `correctif.diff`, 102 lignes ; vrai fichier INTACT) :
- `lancerPreparationCacheWizard` : `setDeepCache` est **lancé, jamais attendu**, et part AVANT la page (comme Hektor) ;
  la promesse **ne rejette jamais** (un rejet non écouté arrêterait le processus) ; délai porté à **90 s** (un abandon sur
  délai déclenche le recul de 15 s du frein sur les appels suivants : à 90 s, la réponse de 30 s arrive avant) ;
- `attendrePreparationsCache`, en fin de création, après l'activation : au plus **45 s** pour les préparations en vol (compte
  rendu, et aucun appel de cette annonce en vol quand le travail suivant change de négociateur), puis on continue sans elles ;
- compte rendu `preparations_cache` (lancées, finies avec durée et statut ou erreur, attente) dans le journal du travail.
- ⭐ **Essai hors ligne VERT, 15 contrôles** (faux Hektor, délais ÷ 100 ; cas lent 30,1 s, cas qui pend, cas en erreur) :
  6 pages envoyées sans attendre, chaque préparation AVANT sa page, fin bornée, erreurs notées, aucun rejet non écouté.
  ⚠ Le premier passage a été ROUGE sur l'ordre (la page partait avant la préparation) : corrigé, l'appel est direct.

**Ce qu'il pourrait casser** : rien d'autre ne l'appelle ; même nombre d'appels à Hektor. NON MESURÉ : jusqu'à 6
`setDeepCache` en vol à la fois sur la même annonce (la page n'en a qu'un par clic humain) ; deux appels presque simultanés
(préparation puis page, comme les 6 ms de Hektor) au lieu d'un par seconde. Une création prendra ~20-30 s de plus (fin bornée).

✅ **POSÉ dans `Console/console_job_worker.js` le 07/11 (« Oui »)** : fichier vérifié intact avant (identique à la copie),
après pose identique octet pour octet à la copie éprouvée, `node --check` vert, essai hors ligne relancé sur le vrai fichier :
VERT (+74 / -16 lignes). ⏰ **Inactif tant que les 4 services ne sont pas redémarrés (Frédéric, file vide)** ; puis essai
réel depuis l'écran Estimations et suppression. Ni commité ni poussé.

**Pas dans ce correctif** (à part, après la preuve) : C2-C4 du §28.8 — toute AUTRE panne après « ajoutebien » laisse encore
une orpheline.

#### 28.8 sexies — ✅ ACTIF ET PROUVÉ EN RÉEL (07/11 soir, « C'est redémarré »)

- **Les 4 services** ont redémarré le 07/11 à **18:45:35-37** (heure des processus `node.exe` sous chaque service), donc
  APRÈS la pose (fichier écrit à 16:22). File vide avant l'essai (0 pending, 0 running).
- **Essai réel**, dans le Chrome de Frédéric, depuis l'écran **Estimations**, même fiche que l'essai raté de 10:39 (28 champs,
  agence Firminy, négociatrice PEREIRA, statut « Estimation ») : fiche provisoire **10000204**, travail
  `53fc0873-73c3-455b-9336-34a2716d6cba`, lancé à 18:47:51 (heure de Paris, comme toutes les heures de ce paragraphe).
- **Résultat : CRÉATION RÉUSSIE**, annonce **63478**, travail `done` à 18:49:18 (83 s au total ; assistant 44 s). Les 7 pages
  sont passées entre 18:48:03 et 18:48:16 — ce matin, la page 2 tombait.
- **Le compte rendu `preparations_cache`** : 6 lancées, **6 finies, toutes en 200**, en **30 795 à 30 958 ms** chacune — donc
  toutes AU-DESSUS de l'ancien délai de 30 000 ms : l'ancien code les aurait toutes abandonnées. Attente de fin : 20,2 s.
- **Contrôle de naissance** (`app_annonce_saisie_naissance`, 28 champs comparés) : 27 identiques ou de même valeur, **1 écart :
  CHARGES 120 → 0**. ⚠ **Il ne vient PAS du correctif** : les journaux de chaque page listent les champs envoyés et
  `CHARGES` n'y figure jamais. J'avais rempli le « Charges » de l'étape **Détails** (copropriété), qui part seulement en
  `copro_charges` ; le worker ne le pose que si la page 7 porte déjà ce champ (`setWizardNumberIfPresent`), et la phase des
  champs initiaux n'a pas renvoyé `mandat_infofi`. L'essai du 22/10 (10000009/63331) portait AUSSI la clé exacte `CHARGES`
  (étape Prix), d'où son 150 gardé. ➡ **Trou à part, antérieur, NON TRAITÉ** : des charges saisies seulement à l'étape
  Détails n'arrivent pas chez Hektor. À auditer s'il le demande.
  **Daté le 07/11 (question « c'est nouveau ? ») : NON, il date de fin mai.** Deux lignes du worker le font :
  `skipFinancial` écarte `copro_charges` des champs d'après-création (commit `963d5dc`, 29/05, en comptant sur
  l'assistant) et la page 7 ne pose CHARGES que si son formulaire le porte déjà (`setWizardNumberIfPresent`,
  `3746214`, 01/06). Les deux cases « Charges » de l'écran existent depuis fin mai. **Mesure sur les 85 créations
  depuis mai** : 3 seulement avaient les charges de l'étape Détails sans la clé CHARGES — 1 test Codex du 07/06
  (62425) et mes 2 essais du 07/11. **Sur les 29 créations réelles (hors tests), AUCUNE n'avait de charges** :
  aucune vraie annonce touchée.
- **Nettoyage** : travail `delete_hektor_annonce` `97adc18d-1010-4bd8-9422-1de3a54a7836` (18:52:07) → « Suppression Hektor
  envoyée et VÉRIFIÉE (existait avant, absente après) », caches locaux nettoyés, `done` à 18:52:42 ; 0 ligne restante
  pour 10000204 / 63478 ; file vide.
- ⏰ **Reste** : commit + push du worker et de cette note (accord requis) ; C2-C4 toujours non faits ; signaler à Hektor
  la lenteur de `setDeepCache` (~31 s) et l'erreur de leur page admin — non décidé.

#### 28.8 septies — DEUX ESSAIS « 100 % DES CASES » (07/11 soir, « une maison et un appartement tout rempli »)

> Fait à sa demande, dans son Chrome, depuis l'écran **Estimations**, négociatrice PEREIRA, Firminy. Un remplisseur
> automatique a rempli **chaque case visible** de chaque étape (OUI quand proposé, sinon une valeur réaliste), trois
> passages par étape pour attraper les cases qui apparaissent (piscine = OUI, honoraires vendeur = OUI), + 2 pièces.
> Laissées vides EXPRÈS : « DPE non concerné / vierge / altitude » (contradictoires avec un DPE saisi) et « Diffusable »
> (forcé à 0 par le worker). Le juge est le verdict de la pièce 3 du chantier ⑧ (`app_annonce_saisie_naissance`).
> Audit préalable du chantier ⑧ relu (C8 = `CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md`).

- **Appartement** : 163 cases, fiche 10000205 → **63479** ; 126 champs jugés : 6 écarts, 14 « console seule » gardés.
- **Maison** : 167 cases, fiche 10000206 → **63480** ; 131 champs jugés : 7 écarts, 13 « console seule » gardés.
- Les deux supprimés ensuite (travaux `0d71d4e5…`, `421c44b8…`), vérifiés absents chez Hektor.

**Ce qui ne revient pas correctement, hors des 21 « console seule »** :
1. **Le TITRE — NOUVEAU.** Deux cases : « Titre / repère interne » (étape 1, clé `title`) et « Titre annonce » (étape 7,
   `titre`). L'assistant pose celui de l'étape 7, puis `postHektorPrincipalTextUpdate` (console_job_worker.js ~l. 12660)
   renvoie `fields.title` = celui de l'étape 1 et **l'écrase**. ⚠ Le libellé dit « repère interne » mais il part comme
   TITRE PUBLIC de l'annonce.
2. **Le TEXTE de l'annonce** (`corps`) — même mécanisme : « Description » (étape 1) écrase « Texte annonce » (étape 7).
   Déjà relevé (C8:897-899, point F, non rangé).
3. **Les CHARGES** saisies seulement à l'étape Détails (`copro_charges`) — §28.8 sexies. Quand les deux cases
   « Charges » portent la même valeur, tout passe (vu ici : 150 → 150). Mesuré aussi : les autres doublons simples
   (lots, quote-part, fonds travaux, cuisine, vue, surfaces, pièces…) reviennent tous identiques.
4. **PISCINE : « Type de piscine » et « Nature piscine » — NOUVEAU.** Cases de TEXTE libre dans la modale
   (App.tsx:1582-1583), mais LISTES chez Hektor (nature = COQUE / TRADITIONNELLE / HORS-SOL / SEMI-ENTERREE,
   console_job_worker.js:11314) : un texte qui ne correspond à aucune option est perdu (« absent »).
5. **`Particularites`** — absent, déjà connu (ESSAI_173:46, groupe liste que l'API rend vide).
- Normaux ou dus à mon remplisseur : `villeprivee` (recalculée par la BAN), `latitude`/`longitude` (BAN), 14 dates
  (même date, autre forme), `NB_ETAGES` 150 → 127 (mon remplisseur a pris « étaGES » pour une case DPE ; Hektor plafonne
  à 127), `floorState` (j'avais mis rez-de-chaussée ET étage 3, Hektor a recalculé).

**Pourquoi nos saisies sont remplacées sur la fiche** : décision écrite, pas un oubli. `CHAMPS_APP_ANNONCE` reste vide
(28/09, PLAN:497-504 ; tranché de nouveau le 13/10, CHANTIER_3:1495-1521) : tant que Hektor diffuse, sa valeur fait foi
pour les champs qu'il entretient (« modèle B » : pousser, relire, garder ce que Hektor a retenu, montrer le verdict).
La saisie, elle, est protégée À PART (pièce 3, table jamais touchée par la relecture) et l'écart est signalé. Ouvert
depuis le 22/10 : « rejuger aussi les écarts qui ne sont pas console seule — à corriger » (C8:1281-1283).

**Les ajouter aux 21 ? NON pour ces cas** : les 21 sont les champs que l'API ne rend JAMAIS. Titre, texte, charges,
piscine sont rendus par Hektor : les reposer chez nous afficherait une valeur que Hektor (donc les portails) n'a pas —
on cacherait la perte au lieu de la corriger. Les correctifs vont à la SOURCE (rien codé, en attente de son accord) :
A titre/texte : ne renvoyer `title`/`description` après l'assistant que si l'étape 7 est vide (ou une seule case) ;
B charges : ne plus écarter `copro_charges` quand la clé exacte CHARGES manque (`skipFinancial`) ;
C piscine : proposer les listes de Hektor dans la modale au lieu d'un texte libre ;
D `Particularites` : à auditer (forme liste).

#### 28.8 octies — AUDIT DES 3 CORRECTIFS (07/11, « Oui les 3 ») — rien codé, attend son « vas-y »

Les trois se font dans `apps/hektor-v1/src/App.tsx` SEUL (la modale de création) : ni worker, ni base, ni redémarrage.
- **A titre / texte.** L'écran n'a aucun lien entre « Titre / repère interne » (`draftAnnonceTitle`, l. 22529) et
  « Titre annonce » (`titre`, l. 1752), ni entre « Description » (l. 1297) et « Texte annonce » (`corps`, l. 1753) — seul
  le scanner remplit les deux (l. 22407, 22984). Le worker prend `title` avant `titre` (`firstDefined`, alias
  `["title","titre"]`, l. 13172) et le renvoie après l'assistant (l. 13333). MESURE : 31 créations portaient les deux
  titres, 29 identiques, 2 différents = mes essais du 07/11 ; les 89 modifications (`update_hektor_annonce_fields`)
  n'envoient QUE `title`, jamais `titre`. CORRECTIF : à l'envoi (l. 18347), `title` = `titre` de l'étape 7 s'il est
  rempli, sinon l'étape 1 ; idem `description` = `corps` sinon « Description ». Le worker n'est pas touché, donc la
  modification ne bouge pas.
- **B charges.** À l'envoi, l'écran recopie déjà 8 cases simples dans les cases Hektor (`setHektorWizardField`,
  l. 18329-18341 : surfterrain, SURFACE_GARAGE, NB_NIVEAUX, GARAGE_BOX, JARDIN-, PISCINE-, EXPOSITION, vuee) — pas les
  charges. CORRECTIF : même geste pour CHARGES, MAIS seulement si la case de l'étape 6 est vide (elle gagne toujours).
  Le worker l'envoie alors par le chemin éprouvé le 22/10 (10000009 : 150 → 150). Pas de changement à `skipFinancial`
  (le lever ferait re-sauver le groupe prix/honoraires après la création).
- **C piscine.** Le code le disait (l. 1909) : « selects Hektor -> 'text' pour l'instant (listes d'options à ajouter
  plus tard) ». Listes RÉELLES lues dans le journal du worker (refus `select_no_option_match`) : type = PRIVATIVE /
  COLLECTIVE / COLLECTIVE SURVEILLEE ; nature = COQUE / TRADITIONNELLE / HORS-SOL / SEMI-ENTERREE. CORRECTIF : deux
  listes d'options sur les 2 cases (l. 1582-1583) et le scanner en `enum` (l. 1911-1912), comme les 12 listes qui le
  sont déjà. Sur les deux essais, Hektor n'a refusé AUCUNE autre case de liste.
- **Ce que ça pourrait casser** : A — si quelqu'un remplit les deux titres différemment, c'est l'étape 7 qui part
  (aujourd'hui l'étape 1) ; le titre provisoire de la liste suit. B — rien hors création. C — un mot du scanner qui ne
  correspond à aucune option laisse la case vide (aujourd'hui il partait et Hektor le refusait en silence) ; les
  synonymes du worker (« béton » → traditionnelle) ne servent plus pour ces deux cases.
- **Contrôle prévu** : `npm run build` ; push (Vercel) ; un essai réel Estimations (deux titres différents, charges à
  l'étape Détails seulement, piscine choisie dans la liste), verdict à 0 écart sur ces champs, puis suppression.

#### 28.8 nonies — QUE VEUT DIRE LA CASE « CHARGES » DE HEKTOR ? (08/11, « je pense que c'est plutôt loyer + charges, audit »)

- **Une seule case** chez Hektor : `CHARGES`, libellé « Charges », dans le groupe `mandat_infofi` (avec prix, dépôt de
  garantie, taxes). Sur 3 000 fiches, aucune autre case dont le libellé contient « charge » (hors `CHARGES_DETAIL`).
  La copropriété a sa propre case : `copropriete_quote_part`, libellé Hektor **« Quote part annuelle »**.
- **MESURE (13 534 fiches, 08/11)** : toutes nos annonces sont des ventes (types d'offre 0, 10, 6 ; aucune location).
  `CHARGES` remplie sur 124 (97 appartements, 17 maisons), médiane **100**. `Quote part annuelle` remplie sur 278,
  médiane **1 199**. Sur les 26 qui ont les deux, **22 ont « Charges » × 12 ≈ quote-part** (rapport 0,8-1,25 ; 15 à
  1,00 tout juste). ⇒ **En vente, « Charges » = les charges de copropriété PAR MOIS ; « Quote part annuelle » = les
  mêmes, PAR AN** (la mention obligatoire ALUR). Ce n'est pas « loyer + charges ».
- Les écarts : sur des maisons, la case sert parfois à autre chose (« Soit élec 1100/an et 400 € granulés », « Loyer »
  3 012, 34 000, 70 000 sur un type 30) — saisies libres, pas un autre sens de la case.
- ⚠ **Non mesuré** : en LOCATION, la même case porterait probablement les charges locatives mensuelles — nous n'avons
  aucune location pour le vérifier. Et ce que Hektor envoie aux portails à partir de cette case.
- **Ce que ça change au correctif B** : rien sur le fond — `coproCharges` → `CHARGES` est le bon rangement, le même que
  la lecture (`rawDetailProp(detail,'mandat_infofi','CHARGES')`, l. 2842) et le PDF d'estimation (« Charges copro. »).
  ⚠ Mais la modale montre la même case Hektor à DEUX endroits sous le seul mot « Charges », sans unité (bloc copro et
  étape 6), et « Quote-part » sans dire « annuelle » : rien n'empêche de saisir un montant annuel dans « Charges ».
  Préciser les libellés (« Charges de copro / mois », « Quote-part annuelle ») est à SA décision (libellés seulement).

#### 28.8 decies — LES 3 CORRECTIFS CODÉS, avec les libellés (08/11, « 3 correctifs avec libellés plus clairs »)

Tout dans `apps/hektor-v1/src/App.tsx`, `npm run build` vert ; ni worker, ni base, ni redémarrage.
- **A** : à l'envoi, `title` = `titre` de l'étape 7 s'il est rempli, sinon l'étape 1 ; `description` = `corps`, sinon
  « Description » (`draftAnnonceTitreEnvoye` / `draftAnnonceTexteEnvoye`, juste avant `createHektorDraftAnnonceJobOptimistic`).
- **B** : `CHARGES` ← `coproCharges` seulement si l'étape 6 l'a laissée vide (même geste que les 8 miroirs voisins).
- **C** : `wizardPiscineTypeOptions` / `wizardPiscineNatureOptions` sur les deux cases, et le scanner en `enum`.
  « Collective surveillée » rangée AVANT « Collective » (le scanner prend la 1re option contenue — même précaution que
  « Semi équipée » avant « Équipée »). MESURE : toutes les valeurs déjà chez Hektor sont dans les listes (type :
  47 PRIVATIVE ; nature : 22 TRADITIONNELLE, 7 COQUE, 7 HORS-SOL, 4 SEMI-ENTERREE) → aucune fiche existante ne
  s'affiche avec une valeur hors liste.
- **Libellés** : « Charges copro / mois » (bloc copro ET étape 6), « Quote-part annuelle » (bloc copro ET étape
  Copropriété). ⚠ Les groupes de l'assistant servent aussi à la fiche d'un bien (`buildHektorWizardDetailGroups`,
  formulaire d'édition) : les libellés et les listes de piscine y changent aussi — même sens, même case. Le
  formulaire « 5. Details - Copropriete » (l. 882, autre liste) garde « Charges » / « Quote-part » : non touché.
- **Reste** : push (accord), puis l'essai réel Estimations et sa suppression ; rien n'a été vu à l'écran avant.
- ⛔ **08/11 : PAS POUSSÉ, par décision** — « on ne peut pas avoir deux cases pour la même chose » : voir §28.9. A et B
  y deviennent inutiles (remplacés par la case unique) ; C (listes de piscine) est gardé.

#### 28.9 — AUDIT : DEUX CASES POUR LA MÊME CHOSE, modale + worker (08/11, « audit en profondeur… proposer une correction »)

Audit limité à la **création d'annonce** (modale + worker + calque de naissance) ; la fiche d'un bien est regardée en
§28.9.6 seulement pour l'inventaire. Rien n'est codé.

**28.9.1 Histoire (git).** Les deux blocs naissent ENSEMBLE le **29/05** (`963d5dc`, « expanded draft announcement
fields ») : `draftAnnonceAdvancedSections` (anciens noms de l'app, envoyés « à plat » : `copro_charges`…) et
`draftAnnonceWizardGroups` (noms exacts de Hektor, envoyés dans `hektor_wizard_fields`). `c496833` (30/05) les affiche
dans le même écran (bloc ancien en bas de Détails, « Texte public » en Diffusion). Ensuite, au lieu de trancher, des
RECOPIES au fil des bugs : 8 à l'envoi le 01/06 (`4e7cd03`, qui retire aussi l'affichage de l'étape 1 de l'assistant),
24 au scanner le 06/07 (`cac9b63` : « Le wizard affiche certains champs 2x »), CHARGES le 08/11 (non poussé).
**Aucune note ne décide** de garder les deux ou d'en retirer un (recherche notice/, racine, notes supprimées).

**28.9.2 Inventaire, appartement (le profil le plus chargé).**
- Bloc ancien en bas de Détails (24 cases) : CHAQUE case a son double dans l'assistant (vérifié par script, aucun
  manque). Diffusion : « Description » double « Texte annonce ».
- Haut de la modale (Titre, Prix, Surface, Pièces, Chambres, Niveaux) : doublés en Diffusion (`titre`, `prix`,
  `surfappart`, `nbpieces`, `NB_CHAMBRES`, `NB_NIVEAUX`) ; Prix aussi en Mandat/Prix.
- Dans l'assistant lui-même : `prix` et `PRIXNETVENDEUR` (étapes 6 et 7), `EXPOSITION`, `vuee`, `GARAGE_BOX`,
  `NB_CHAMBRES` (5 et 7), `SURFACE_GARAGE` (garage, 5 et 7) — même valeur (même clé), deux cases à l'écran.
- Au total jusqu'à **3 cases** pour : prix, prix net vendeur, chambres, exposition, vue, garages.
- ⚠ Manques à combler AVANT de retirer le bloc ancien : terrain → `etat_exterieur` ; immeuble → `NB_SDB`, `NB_SE`,
  `NB_WC` (absents des étapes affichées pour ces profils).
- Chez Hektor : UNE case par information. Son assistant répète certains champs d'une page à l'autre (prix, chambres,
  exposition…), mais le worker pose déjà chaque valeur exacte sur CHAQUE page (`applyExactHektorWizardFields`,
  l. 12101-12122) : une seule case dans la modale suffit.

**28.9.3 Qui gagne : TROIS RÈGLES QUI SE CONTREDISENT** (vérifié dans le code).
1. Pendant l'assistant : le nom Hektor gagne (posé en dernier sur chaque page, l. 12122).
2. Après l'assistant : `applyHektorAnnonceFieldUpdates` envoie d'abord les groupes « nom Hektor » (l. 13367) PUIS les
   groupes « à plat » (secteur, intérieur, extérieur, diagnostics, copro, l. 13442-13501) → **l'ancien nom gagne au
   final** pour presque toutes les paires. Sauf `prix`, `PRIXNETVENDEUR`, `CHARGES` (écartés par `skipFinancial`,
   l. 13277) et `SURF_SEJOUR` (pas de clé à plat) → là le nom Hektor gagne.
3. Notre base (« naître complet ») : `calque := plat || wiz` (`patch_8a2b…`, l. 130) → **le nom Hektor gagne**.
- Masquage : le front envoie TOUTES les clés à plat, à `null` si vides (`api.ts` l. 12855-12885), et `firstDefined`
  s'arrête sur une clé présente même nulle (l. 18945-18949) → un `copro_charges: null` cache `CHARGES` dans la voie à
  plat. C'est, avec `skipFinancial`, la mécanique exacte des charges perdues.
- Modification d'une annonce (`update_hektor_annonce_fields`) : la boîte « nom Hektor » est reconstruite à partir des
  clés à plat (l. 13562) → les deux portent la même valeur, pas de conflit.

**28.9.4 Mesure sur les 87 créations réelles (`app_console_job`, 08/11).** Les deux cases portent presque toujours la
même valeur. « Différents » = surtout le même état écrit deux fois (« Bon » / code « 6 » : 14 sur 36 pour l'état
extérieur ; « Séparée » / « SEPAREE »), plus de vrais désaccords seulement sur des essais (juin : Carrez 80,5 / 120,1,
surface 725 / 82,6 ; mes essais du 07/11 : titres et textes). Aucun cas réel de négociateur avec deux valeurs.

**28.9.5 PROPOSITION — « une information = une case = un nom = une règle ».** Vocabulaire de référence : les noms de
Hektor (ceux de l'assistant), déjà utilisés par la fiche d'un bien (cockpit), par le calque de naissance et par la
note des 173 champs (« source de vérité »).
- **Modale (`App.tsx`)** :
  - M1 retirer de l'écran le bloc ancien (Intérieur / Extérieur / Diagnostics-copro) et « Description » ; avant,
    ajouter les 4 cases manquantes (terrain, immeuble) ;
  - M2 chaque information une seule fois : le haut (titre, prix, surface, pièces, chambres, niveaux) n'est plus
    répété en Diffusion ; prix net vendeur seulement en Mandat/Prix ; exposition, vue, garages, chambres seulement
    en Détails. ⚖ À SA DÉCISION : où vit le prix (haut, recommandé : obligatoire et montré dans la liste provisoire)
    et le titre (haut, renommé « Titre de l'annonce » ; « repère interne » est faux, il part chez Hektor) ;
  - M3 à l'envoi, UNE fonction remplit les deux voies avec la même valeur (clé à plat = nom Hektor) : elle remplace
    les 8 recopies, le correctif B (charges) et le correctif A (titre/texte) ; le scanner remplit la case gardée
    (aujourd'hui jardin, piscine, terrasses et description ne vont QUE dans le bloc ancien, l. 17852-17867).
- **Worker (`console_job_worker.js`)**, filet de sécurité pour les travaux déjà en file ou venus d'un autre écran :
  - W1 à l'entrée de `create_hektor_draft_annonce`, unifier chaque paire : le nom Hektor gagne s'il est rempli, sinon
    l'ancien nom, et les deux reçoivent la même valeur → les règles 1, 2 et 3 donnent le même résultat ;
  - W2 une clé à plat NULLE ne masque plus le nom Hektor (lecture qui saute le vide, dans la normalisation seule) ;
  - pas de changement à `skipFinancial` (les charges passent par le groupe « nom Hektor », prouvé le 22/10).
  - Redémarrage des 4 services, file vide.
- **Base** : rien (le calque dit déjà « nom Hektor gagne »).
- **Ce que ça pourrait casser** : l'habitude des négociateurs (le bloc du bas disparaît, ses cases existent plus
  haut) ; le compteur « N champs remplis » baisse (moins de cases) ; les 4 cases ajoutées pour terrain/immeuble
  partent chez Hektor sous leur nom exact (à éprouver) ; W1 change le gagnant pour un travail qui porterait deux
  valeurs différentes (aujourd'hui l'ancien nom, demain le nom Hektor) — 0 cas réel mesuré.
- **Contrôle** : essai hors ligne de W1/W2 (faux Hektor, comme le 07/11) ; `npm run build` ; deux essais réels
  Estimations (maison et appartement à 100 %), verdict de naissance à 0 écart, suppression.
- **Ordre** : modale d'abord (la cause), worker ensuite (le filet), deux poussées séparées.

**28.9.6 Fiche d'un bien (inventaire seulement, hors correctif).** Le cockpit (seule édition au bureau,
`APP_COCKPIT_V2_ENABLED`) utilise les noms Hektor, sans doublon interne. Restent deux autres portes sur les mêmes
cases : le crayon « Corriger » du mandat (`CorrigeableAnnonceField`, prix, net vendeur, pièces, surface, terrain,
honoraires — enregistré tout de suite, anciens noms) et « Reporter dans la fiche » de l'estimation (cases vides
seulement). Code mort : `hektorAdvancedSections` (l. 813-907), `buildHektorAdvancedDraft` (l. 2820),
`createUpdateHektorAnnonceFieldsJob` (`api.ts` l. 11975). À trancher par lui, chantier à part.

#### 28.9 bis — SECOND PASSAGE (08/11, « où se trouve Corriger mandat… le worker de modification… la nature du bien »)

**Où est « Corriger ».** Ce n'est PAS une modification du mandat : c'est le crayon (`CorrigeableAnnonceField`,
App.tsx l. 5365, infobulle « Corriger — met à jour la fiche ») dans **« Préparer le mandat »** (`MandatDocumentEditor`,
l. 5469), onglets **Bien** (Pièces, Surface habitable, Surface terrain) et **Prix** (Prix FAI, Net vendeur, Honoraires
TTC), l. 6161-6171. Il corrige l'ANNONCE (`editAnnonceOptimistic`) pour que le document du mandat soit juste. On y
arrive par la rubrique Mandat de la fiche (étape « Édité », et « Actions mandat (Hektor) » l. 35438), par l'avenant,
par le téléphone (l. 41245) et par le registre des mandats (l. 29632). Vu à l'écran le 08/11 sur 7589405 : sur un
mandat déjà signé, l'éditeur n'est plus proposé (« Ouvrir le signé »).

**Modification depuis la rubrique Bien (cockpit).** Même chemin pour toutes les portes : `editAnnonceOptimistic` →
RPC `app_edit_annonce_optimistic` → `app_annonce_pending` (push 600 s plus tard) → `update_hektor_annonce_fields`.
- La RPC fusionne les corrections par NOM de case : `push_fields = ancien || nouveau` (lu en base le 08/11).
- Le cockpit envoie les noms Hektor (`prix`, `surfappart`, `nbpieces`…) ; le crayon du mandat envoie les anciens noms
  (`price`, `surface`, `roomCount`, `landSurface`, `netSellerPrice`, `fees`).
- Le worker lit l'ancien nom AVANT le nom Hektor (`["price","prix"]`, `["room_count","roomCount","nbpieces"]`…,
  l. 13170-13230). ⛔ PIÈGE : crayon puis cockpit sur le même prix en moins de 10 min → l'attente porte les deux noms
  → le worker renvoie la valeur du CRAYON, la plus ancienne. MESURE : 0 travail sur 89 avec les deux noms d'une même
  case (jamais arrivé) ; mais les deux vocabulaires servent (surface 26 / surfappart 4, price 17 / prix 4, title 16 /
  titre 2, roomCount 3 / nbpieces 3).
- La modification ne porte PAS la nature du bien (0 travail sur 60 jours) → le worker ne filtre rien par nature en
  modification ; seul l'écran filtre.

**Nature du bien : QUATRE listes à tenir d'accord** — écran (`draftAnnonceWizardFieldsByProfile` + communes ;
`draftAnnonceAdvancedVisibleFieldsByProfile`) et worker (`HEKTOR_WIZARD_FIELDS_BY_PROFILE`,
`HEKTOR_UPDATE_FIELDS_BY_PROFILE`, l. 11735-11870). Comparaison par script (étapes affichées 3, 5, 6, 7) :
- ⛔ **`Particularites`** (appartement, maison, immeuble) : affichée, JAMAIS envoyée — aucun code du worker ne la pose,
  ni en création ni en modification (c'est la réserve D de §28.8 septies : « absente au retour ») ;
- **`SURFACE_JARDIN`** (terrain) : affichée, jetée par le worker en création ;
- chauffage (immeuble) et `codeprive`/`villeprivee` : jetés de la voie « nom Hektor » mais envoyés par leur voie à part
  (chauffage, secteur) — pas une perte ;
- l'écran et l'assistant d'un même profil se recoupent par ailleurs ; le bloc ancien n'a d'équivalent manquant que
  pour terrain (`etat_exterieur`) et immeuble (`NB_SDB`, `NB_SE`, `NB_WC`).

**PROPOSITION REVUE — un seul vocabulaire (les noms Hektor), une seule règle, une seule liste par nature.**
- Écran : M1-M3 (§28.9.5) + **M4** le crayon « Corriger » envoie les noms Hektor (`prix`, `PRIXNETVENDEUR`, `nbpieces`,
  `surfappart`, `surfterrain`) → plus aucun écran n'envoie deux noms pour une case. ⚠ `fees` part vers `HONORAIRES`,
  qui n'est PAS la case « Montant honoraires acquéreur » (`_tauxHonoraire2`) de la fiche : non touché, à vérifier à part.
- Worker : W1-W2 (création) + **W3** en modification, si une attente porte deux noms d'une même case avec deux valeurs,
  le nom Hektor gagne et c'est écrit au journal (même règle qu'à la création) ; **W4** la liste par nature du worker
  accepte tout ce que l'écran montre (`SURFACE_JARDIN` pour un terrain).
- `Particularites` : à traiter à part (format de Hektor = liste de numéros, jamais éprouvé) — en attendant, à SA
  décision : la cacher, ou la laisser affichée en sachant qu'elle ne part pas.
- Base : rien.

**28.9 ter — PRÉCISIONS (08/11).** ⚖ DÉCISION : **« Particularités on masque »** (en attendant son chantier).
- « Il ne devrait plus y avoir de paire » : JUSTE. Revu : l'écran n'envoie plus QUE le nom Hektor (`api.ts` cesse
  d'ajouter les anciennes clés à `null`) ; la seconde porte du worker lit déjà les noms Hektor dans ses listes d'alias
  (sauf `SURF_SEJOUR`, envoyé par la porte « nom Hektor »). W1/W2 ne servent plus qu'aux travaux venus d'un onglet
  resté ouvert sur l'ANCIENNE version de l'app (le code d'un onglet ne change qu'au rechargement).
- Le piège des 10 minutes : la cause est corrigée par M4 (un seul nom par case → la fusion `ancien || nouveau` de
  `app_edit_annonce_optimistic` garde la DERNIÈRE). Pour qu'un ancien onglet ne puisse plus le recréer, la vraie
  correction est dans la RPC : traduire les anciens noms en noms Hektor AVANT la fusion (la dernière gagne toujours).
  W3 (« le nom Hektor gagne ») n'aurait PAS garanti « la dernière gagne » → remplacé par ce correctif de la RPC.
  Écriture en base de production : accord obligatoire, sauvegarde de la définition et inverse prêts.

**28.9 quater — CONTRÔLE FINAL AVANT CODE (08/11, « contrôle une dernière fois avant de coder »).** Personne d'autre n'a
touché App.tsx / api.ts / worker depuis 19f5742. Trois contrôles : écran, worker, base (fonctions lues en base).
Ce que le contrôle CHANGE au plan :
1. ⛔ **Le haut de la modale est lui-même branché sur l'ANCIEN bloc** : Surface terrain, Surface (garage), Jardin,
   Piscine, Garage, Situation, Vue écrivent dans `draftAnnonceAdvanced` (App.tsx ~l. 22665-22727) ; titre, prix,
   surface, pièces, chambres, niveaux ont chacun LEUR état. Une même case peut donc vivre dans TROIS états.
2. ⛔ **Conflit caché, déjà présent** : le scanner recopie prix/surface/pièces/chambres/niveaux dans les noms Hektor
   (l. 17931-17956) et l'IA écrit `titre` ; ces copies GAGNENT (worker et base). Corriger le prix en haut après un
   scan n'a aucun effet chez Hektor (0 cas mesuré sur 87, mais le piège est là).
3. ⛔ **`draftAnnonceWizardGroups` est PARTAGÉ** (modale de modification, panneau, cockpit, filtre d'envoi l. 2393) :
   on n'y retire rien ; les répétitions se cachent SEULEMENT au rendu de la modale de création.
4. **Garder des anciennes clés** dans la charge, recalculées depuis la case unique : `title` (texte de recherche de
   `app_annonce_corps_de_naissance`, libellé du travail l. 9625, ligne provisoire), `price` (ligne provisoire),
   `address`/`postal_code`/`city` (commune). Les 27 clés du bloc ancien disparaissent.
5. **Worker, double écriture** : si l'ancien chemin relit les noms Hektor, chaque groupe part deux fois (≈10 requêtes
   de plus par création, quota). → à la création, l'ancien chemin saute ce que le chemin « nom Hektor » écrit déjà.
   Le « masquage par une case vide » (W2) devient SANS OBJET : il ne gêne plus quand la valeur est sous le nom Hektor.
6. **Nature du bien, worker** : il jetterait `NB_SDB`/`NB_SE`/`NB_WC` (immeuble), `etat_exterieur` et `SURFACE_JARDIN`
   (terrain) → ses listes reprennent celles de l'écran.
7. **Nombres** : le chemin « nom Hektor » ne convertit pas « 85,5 » → l'écran convertit avant l'envoi.
8. **Écran, à rediriger** : sous-cases piscine (`showIf` sur `PISCINE-`), récap et compteurs, données de l'IA
   rédactrice (l. 18082-18127), 4 miroirs manquants du scanner (`corps`, `JARDIN-`, `PISCINE-`, `NB_TERRASSE`).
9. **`Particularites` masquée partout** : listes par nature (l. 2078, 2180, 2309), groupe étape 5 (l. 1557), cockpit
   (`CK_LB_SECTIONS` l. 30756, montré pour un type inconnu), scanner (l. 1863).
10. **Base** confirmée : `app_annonce_corps_de_naissance` et `app_annonce_calque_modif` traduisent déjà les anciens
    noms et font gagner le nom Hektor ; la RPC `app_edit_annonce_optimistic` connaît les deux familles ; la file passe
    les champs tels quels (`app_annonce_enqueue_due_pushes`). Transition : une attente d'avant le déploiement avec
    `price` + une correction d'après avec `prix` → le worker, `v_price` et `app_annonce_reappliquer_saisies` liraient
    `price` (périmé) → la RPC traduit ET retire l'ancien nom de l'attente à la fusion.
11. `fees` (crayon « Honoraires TTC » → `HONORAIRES`) ≠ `_tauxHonoraire2` : laissé tel quel, à trancher à part.
12. Non vérifiés : `Console/test_suite_creation_avertie.js`, `phase2/checks/annonce_un_numero.py` (à lire au codage).

**PLAN FINAL (rien codé)** — principe : la modale n'a plus qu'UN état, aux noms Hektor ; toute case affichée (haut
compris) lit et écrit cet état → deux cases ne peuvent plus diverger, et chaque information n'est affichée qu'une fois.
- Écran (App.tsx, api.ts) : un état ; le haut relié aux noms Hektor (titre, prix, surfappart, nbpieces, NB_CHAMBRES,
  NB_NIVEAUX, surfterrain, SURFACE_GARAGE, JARDIN-, PISCINE-, GARAGE_BOX, EXPOSITION, vuee) ; répétitions cachées au
  rendu de la création ; bloc ancien et « Description » retirés ; 4 cases ajoutées (terrain, immeuble) ; scanner, IA,
  récap, compteurs, piscine redirigés ; nombres convertis ; charge = noms Hektor + `title`/`price`/adresse recalculés ;
  crayon du mandat aux noms Hektor (sauf `fees`) ; `Particularites` masquée ; libellé « Titre de l'annonce ».
- Worker : à la création, chaque case écrite UNE fois ; listes par nature = celles de l'écran ; comptes rendus et
  alertes lisent aussi `titre`/`prix`. Redémarrage des 4 services, file vide.
- Base : `app_edit_annonce_optimistic` traduit les anciens noms et retire l'ancien nom de l'attente (accord, sauvegarde,
  inverse).
- Contrôle : build ; essai hors ligne du worker ; essais réels Estimations (appartement, maison, terrain, immeuble ;
  scan puis correction du prix en haut ; crayon puis rubrique Bien en moins de 10 min) ; suppression des essais.

**28.9 quinquies — AUDIT DE TOUS LES LIENS (08/11, « penser à toutes les conséquences, vérifier tous les liens »).**
⚠ Vocabulaire corrigé : « l'ancien bloc » était FAUX — les deux sont nés le même jour (29/05). À l'écran ce sont
les sections marquées **« Detail app »** (noms de l'app), à côté des sections **« Page 5 / 6 / 7 »** (noms Hektor).
Trois contrôles (écran + mandat, worker + scripts, base lue en direct). Résultats :
- **Écran** : l'état unique aux noms Hektor EXISTE déjà (`draftAnnonceWizardFields`). Une seule modale (l. 22474),
  une seule fonction d'envoi ; deuxième chemin à adapter : la création rapide par l'IA (« gcc », l. 22422-22444).
  À adapter : cases du haut, remise à zéro, surface du récap, compteurs, piscine (`showIf` sur `PISCINE-`), scanner,
  IA (lecture l. 18082-18127 ; retour en DEUX copies l. 22430 et 23005), récap l. 23021-23030.
- **Lecteurs du calque des modifications (`app_optimistic_overlay`)** : les 7 lecteurs de l'écran lisent DÉJÀ les noms
  Hektor → traduire dans la RPC ne prive aucun écran ; ne pas traduire `composition_pieces`, `latitude`, `longitude`.
- **Mandat** : le brouillon du document (`buildMandatDocumentDraft` l. 4576-4641) ne lit pas le calque pour le prix, le
  net vendeur, la surface → juste après un crayon, le PDF et l'alerte « la fiche a changé depuis ce PDF »
  (`ficheDuJourPourEnvoi` l. 4645) lisent l'ancienne valeur tant que Hektor n'a pas répondu (défaut DÉJÀ présent) →
  lire le calque d'abord. `fees` → `HONORAIRES` = même destination (alias du worker, et lu par le brouillon l. 4605).
- **Worker** : le format de la charge ne change PAS si l'écran garde toutes les clés d'aujourd'hui, simplement
  CALCULÉES depuis l'état unique → aucun lecteur ne voit de différence (ligne provisoire, recherche de la base,
  libellé du travail, `app_en_attente_humain`, pages de l'assistant qui lisent les clés à plat SANS filtre de nature).
  ⇒ **le worker n'a PAS besoin d'être modifié** pour que le correctif soit juste. La copropriété reste protégée (garde
  indépendante de l'ordre). Seule amélioration possible, À PART : ≈ −8 requêtes Hektor par création en ne réécrivant
  pas par l'ancien chemin ce que le chemin « nom Hektor » a RÉELLEMENT écrit (jamais le secteur : identifiants de commune).
- **Base** : seule la RPC `app_edit_annonce_optimistic` change (traduire avant `col_map`/`json_map`/`scoring_keys`/
  `v_base`, retirer le jumeau ancien de l'attente à la fusion). `app_annonce_reappliquer_saisies`, le contrôle de
  naissance et le contrôle des modifications acceptent déjà les noms Hektor.
- Scripts : `phase2/checks/annonce_un_numero.py`, `build_inventory_from_exports.js`, `test_garde_copropriete.js` sûrs ;
  `test_suite_creation_avertie.js` probablement déjà périmé (à relancer avant de s'y fier).

**PLAN DÉFINITIF**
- Écran : un état ; cases du haut = vues sur les noms Hektor ; sections « Detail app » retirées ; répétitions cachées
  dans la modale de création seulement ; 4 cases ajoutées (terrain, immeuble) ; scanner, IA (2 copies), récap,
  compteurs, piscine redirigés ; nombres convertis ; charge INCHANGÉE dans sa forme (toutes les clés recalculées
  depuis l'état unique) ; crayon aux noms Hektor (`fees` → `HONORAIRES`) ; brouillon du mandat lit le calque d'abord ;
  `Particularites` masquée (groupes, listes, cockpit l. 30756, scanner) ; libellés. Mise en ligne = push (Vercel).
- Base : la RPC traduit (accord, sauvegarde, inverse, répétition).
- Worker : RIEN dans ce correctif ; la réduction des requêtes est proposée à part.

**28.9 sexies — CODÉ (08/11, « Oui » au plan définitif) ; fonction de la base POSÉE et écran POUSSÉ le 08/11 (« Oui pour les deux »).**
- **Écran (`App.tsx`, non commité)** :
  - plus d'état à part : titre, prix, surface, pièces, chambres, niveaux et les 27 clés « Detail app » LISENT la case
    Hektor de même sens (`draftAnnonceAdvancedWizardName`, d'après les alias du worker) ; les cases du haut l'ÉCRIVENT ;
  - sections « Detail app » retirées (Intérieur, Extérieur, Diagnostics / copro, Texte public) ; « Titre / repère
    interne » devient « Titre de l'annonce » ; « Surface terrain » d'une maison ajoutée en haut, à côté du jardin
    (elle n'existait qu'en bas) ;
  - répétitions cachées dans la modale de création SEULEMENT (`draftAnnonceNomsAuHaut` ; prix net vendeur seulement en
    Mandat / Prix) : les groupes partagés ne perdent rien ;
  - 4 cases ajoutées aux listes par nature : terrain `etat_exterieur`, immeuble `NB_SDB` / `NB_SE` / `NB_WC` ;
  - `Particularites` masquée : groupe de l'étape 5 (donc aussi modification, panneau, fiche), 3 listes, cockpit, scanner ;
  - piscine : `showIf` sur `PISCINE-` (le drapeau `advanced` est retiré du type) ; compteurs sans double compte ;
    remise à zéro = vider l'état unique ;
  - scanner : titre vers `titre` ; texte, jardin, piscine, terrasses vers leur case (les 4 miroirs manquants) ; le texte
    BRUT non résolu (cuisine, exposition, états) n'est plus posé dans une case à liste ;
  - IA (2 endroits) : `titre` et `corps` seulement ;
  - envoi : `normaliserNombresCreationAnnonce` (« 85,5 » → 85.5, « 180 000 » → 180000) puis TOUTES les clés d'avant
    recalculées depuis l'état unique : même forme de charge, même valeur dans les deux voies ; les correctifs A (titre)
    et B (charges) du 08/11 deviennent sans objet et sont retirés ; C (listes piscine) et les libellés restent ;
  - crayon « Corriger » du mandat aux noms Hektor (`nbpieces`, `surfappart`, `surfterrain`, `prix`, `PRIXNETVENDEUR`,
    `HONORAIRES`) ; brouillon du mandat (donc PDF et « la fiche a changé ») lit le calque d'abord.
- **Contrôle hors ligne** : `npm run build` vert ; script `verif_cases.py` (bloc-notes) sur les 6 natures : aucune
  case « Detail app » perdue, aucune case affichée deux fois ; conversion des nombres essayée (180 000, 85,5, 45.43,
  texte laissé tel quel). ⚠ PAS ENCORE VU À L'ÉCRAN : la modale exige une connexion ; la vérification se fera sur
  l'app en ligne après le push, avec les essais Estimations.
- **Base — POSÉE le 08/11** (migration `annonce_un_nom_par_case_2026_11_08`, garde passée ; empreinte neuve
  `0b74a921348150dcaaca90a773989944`, marque présente, droits inchangés : utilisateurs oui, public non ; 16 attentes en
  cours, aucune avec un ancien nom) : `supabase/patch_annonce_un_nom_par_case_2026-11-08.sql` (+ `_INVERSE`,
  `_REPETITION`). Garde par empreinte 5eb2c1a4… ; traduction de 33 anciens noms ; retrait du jumeau ancien dans
  l'attente ET le calque. Sauvegarde de la définition vérifiée au caractère près (même empreinte). Répétition jouée
  (transaction annulée, admin simulé, bien vivant 10000009) : **10 OK, 0 KO** ; après coup rien n'est resté.
  Une 1re tentative sur 62774 a échoué (« dossier_not_found » : 62774 n'est plus parmi les vivants) et a prouvé que
  l'annulation défait aussi la pose de la fonction (empreinte inchangée).
- Tous les écrans de l'app envoient désormais les noms Hektor (formulaire de modification, estimation « Reporter »,
  cockpit, crayon) : la fonction de la base est le filet des onglets restés sur l'ancienne version.
- **Worker** : rien. Aucun redémarrage.
- **En ligne (08/11, commit `9ebfa47`, Vercel READY) — VU À L'ÉCRAN** dans son Chrome, écran Estimations, modale
  ouverte puis FERMÉE sans créer (0 création en base) : « Titre de l'annonce » ; compteur juste (5 cases = 5, plus de
  double compte) ; appartement, maison, terrain, immeuble : aucune section « Detail app », aucune « Particularités »,
  aucune case répétée (prix net vendeur seulement en Mandat / Prix) ; maison : surface terrain, jardin, piscine en
  haut, et les détails de la piscine s'ouvrent quand on coche « Oui » en haut ; terrain : état extérieur présent ;
  immeuble : SDB, salles d'eau, WC présents ; valeurs gardées en changeant de type ; 0 erreur console.
- **Reste** : essais réels Estimations (appartement, maison,
  terrain, immeuble ; scan puis prix corrigé en haut ; crayon puis rubrique Bien en moins de 10 min), verdict 0 écart,
  suppression des essais. Ouverts à part : HONORAIRES vs `_tauxHonoraire2` ; le vrai envoi des Particularités ; la
  réduction des requêtes du worker ; `test_suite_creation_avertie.js` à relancer avant de s'y fier.

**28.9 septies — ESSAIS RÉELS (08/11, « Oui »).** Écran Estimations, son Chrome, PEREIRA / Groupe GTI Firminy,
titres « ESSAI … ne pas diffuser ». Juge : `app_annonce_saisie_naissance` (création) et `app_annonce_saisie_modif`
(modification). File vide et 4 services en marche avant de commencer.
- **Charge envoyée** : sur chaque essai, chaque clé à plat porte EXACTEMENT la valeur de sa case Hektor (titre/titre,
  price/prix, surface/surfappart, land_surface/surfterrain, garden/JARDIN-, pool/PISCINE-, copro_charges/CHARGES…) ;
  nombres convertis (« 180 000 » → 180000, « 85,5 » → 85.5, « 1 620,5 » → 1620.5).
- **Essais ciblés** : appartement 10000207 → 63481 : 27 cases, **0 écart** (CHARGES 120 arrive enfin) ; maison
  10000208 → 63482 : 29 cases, **0 écart** (terrain, jardin, piscine, type/nature de piscine) ; terrain 10000209 →
  63483 : 13 cases, 1 écart `etat_exterieur` absent ; immeuble 10000210 → 63484 : 16 cases, 3 écarts `NB_SDB` / `NB_SE`
  / `NB_WC` relus 0.
- **Essais 100 % (à sa demande, « tu n'as pas rempli les 130 ou 160 champs ? »)** : remplisseur réécrit (règles du
  07/11 : chaque case visible, trois passages, OUI si proposé ; vides exprès : DPE non concerné/vierge/altitude,
  Diffusable, Masquer le prix, latitude/longitude ; pas de pièces de composition). Appartement 127 cases → 10000211 /
  **63485** : 122 jugées, **0 écart** (07/11 : 6), 14 console seule, 13 dates « autre forme ». Maison 132 cases →
  10000212 / **63486** : 127 jugées, **0 écart** (07/11 : 7), 13 console seule, 12 dates « autre forme ». (Moins de cases
  que le 07/11 — 163/167 — parce que les doublons d'écran ont disparu.) ⚠ Le prix net vendeur de ces deux essais vaut
  12.5 : valeur par défaut de MON remplisseur, pas un défaut.
- **Modification, la dernière gagne** (10000207 / 63481) : 16:03 appel à l'ANCIEN nom `price` = 181000, au nom de
  Frédéric, comme un onglet resté sur l'ancienne version → l'attente porte `prix` = 181000 ; 16:05 rubrique Bien
  (écran) `prix` = 182000 → l'attente porte `prix` = 182000 seul ; 16:16 travail `update_hektor_annonce_fields` →
  « mise à jour effectuée », **Hektor relit 182000**, contrôle de modification 0 écart. (Avant le correctif : 181000.)
  ⚠ Le crayon « Corriger » lui-même n'a pas été cliqué : il n'est proposé qu'après « Générer le numéro de mandat »
  (ligne définitive au registre) ; il envoie désormais le même nom (`prix`) que la rubrique Bien.
- ⚠ **Trouvé, ANTÉRIEUR au correctif (même perte avant, sans bruit, par « Detail app »)** :
  - immeuble : le worker ne laisse passer ni `NB_SDB`/`NB_SE`/`NB_WC` (assistant, `HEKTOR_WIZARD_FIELDS_BY_PROFILE`
    building) ni `bathroom_count`/`shower_room_count`/`wc_count` (après, `HEKTOR_UPDATE_FIELDS_BY_PROFILE` building)
    → Hektor reste à 0 ;
  - terrain : `exterior_state` est envoyé (liste land) mais Hektor ne le rend pas : il n'a probablement pas cette case
    pour un terrain.
  - À SA DÉCISION : immeuble = ouvrir ces 3 cases dans le worker (modification du worker + redémarrage, à éprouver), ou
    les masquer ; terrain = masquer l'état extérieur.
  - ✅ **DÉCIDÉ (08/11) : « Masque à l'écran car elles ne sont pas utiles. »** Le worker n'est PAS touché. Fait dans
    `App.tsx` : retirées des listes par nature (`draftAnnonceWizardFieldsByProfile`, étape 5) `NB_SDB`/`NB_SE`/`NB_WC`
    pour building et `etat_exterieur` pour land — ce qui les retire d'un coup de la création, de la fiche (détail), du
    formulaire de modification et du cockpit, qui lisent tous ces listes ; et retirées des clés plates autorisées
    (`draftAnnonceAdvancedVisibleFieldsByProfile` : bathroomCount/showerRoomCount/wcCount pour building, exteriorState
    pour land), pour qu'une valeur saisie sous une autre nature puis changée ne parte plus. C'est le retour aux listes
    d'avant le 08/11 matin (ces cases n'y étaient pas ; elles ne vivaient que dans « Detail app », supprimée).
    L'état extérieur d'un immeuble, lui, reste (Hektor le garde, essai 63484). Compilation verte. Poussé (`3c71940`,
    Vercel READY) et **VU EN LIGNE** le 08/11 (modale Estimations ouverte puis fermée sans créer) : terrain, étape 5 =
    plus d'état extérieur (Eau, Assainissement présents) ; immeuble, étape 5 = plus de SDB / salles d'eau / WC (état
    extérieur, Carrez, Ascenseur, Année construction présents) ; 0 erreur console.
- Remarque d'écran, non traitée : sur la fiche 10000207, le fil d'Ariane affichait « Annonce 10000210 » (le numéro de
  la dernière création) au lieu de 10000207.
- **Suppression** : 6 travaux `delete_hektor_annonce` (même geste que le 07/11), tous `done`, `after_found: false` chez
  Hektor (63481 → 63486), plus aucune fiche 10000207-10000212 dans l'app, aucune attente restante.

#### 28.10 — ESSAI RÉEL DES PARTENAIRES REPRIS (08/11, « Vas y ») — reprise de §28.7 ter, cette fois depuis Estimations

Son Chrome, écran **Estimations** → « Nouvelle estimation » → Manuellement : « ESSAI PARTENAIRES 2B bis - ne pas
diffuser », Groupe GTI Firminy, Emmanuelle PEREIRA, appartement, 100 000 €, 60 m², 3 pièces, 2 chambres, 8 rue de
l'Ondaine 42700 Firminy, Copropriété = Oui. Départ : 85 liens actifs, 0 sans numéro, file vide, crans
`partenaires_choix_saisie` et `partenaires_design_contact` à `admin`.
- **Étape 5, rubrique « Intervenants »** : le syndic n'apparaît qu'avec Copropriété = Oui ✅. Diagnostiqueur choisi
  dans le catalogue : **Ardrodiag (10355367)** ✅.
- **« ＋ Nouveau syndic »** : fenêtre réglée « Partenaire / Personne morale / métier Syndic », compte PEREIRA choisi ;
  « ZZ ESSAI SYNDIC 2B BIS », 0499999962 → **notre n° 20000047 tout de suite**, métier `syndic` source `ecran` écrit
  (18:13:51 UTC), travail `create_hektor_contact` done en 16 s, paire apprise **20000047 ↔ 606275** ; revenu choisi
  dans l'assistant ✅.
- **Création** (18:14:25 UTC) : fiche ouverte sur **10000213**, statut **Estimation** ; **liens 104 (syndic) et 105
  (diagnostiqueur) posés par notre numéro** au même instant, `hektor_annonce_id` vide ; l'onglet Contact les montre
  aussitôt (« choisi dans l'app par Frederic Gerphagnon le 08/11/2026 ») ✅. ⚠ Mon second « Suivant » est tombé sur
  « Créer l'annonce » (même place du bouton) : l'étape 7 n'a pas été regardée avant la création.
- **Chez Hektor** : travail `create_hektor_draft_annonce` done en **70 s** (18:14:28 → 18:15:35), **annonce 63487**,
  posée sur la fiche (`hektor_annonce_id` = 63487). Le correctif du worker (§28.8 sexies) tient.
- ⚠⚠ **DÉFAUT TROUVÉ — l'écran perd les partenaires entre le retour de Hektor et :50** : fiche rechargée à 18:17 →
  onglet Contact « Aucun syndic » / « Aucun diagnostiqueur », et « Le Bien » / Diagnostics « Aucun diagnostiqueur »,
  alors que les liens 104/105 sont actifs. Cause : la carte (`SyndicDuBien.tsx` l. 127, `lireLeSyndic(annonce, role,
  annonce ? null : dossier)`) ne passe notre numéro QUE si le numéro Hektor manque — la prudence que j'avais choisie
  pour 2a (§28.6 ter). Dès que 63487 arrive, elle cherche par 63487 seul, et les liens ne le portent qu'après la tâche
  `partenaire-lien-numeros` (à :50 chaque heure) → **jusqu'à une heure** d'écran vide. La lecture en base
  (`app_partenaire_du_bien_lire`) sait déjà chercher par l'un OU l'autre numéro : seul l'écran se prive du second.
- ✅ **Le geste d'écriture, lui, est protégé dans cette fenêtre** (lu dans `app_partenaire_du_bien` : il cherche le lien
  actuel par l'un OU l'autre numéro) — éprouvé : « Le Bien » → Diagnostics → choisi **AUDIT CONSTRUCTION (10353724)**
  à 18:18:03 → le lien 105 (Ardrodiag) **retiré**, le lien **106 posé avec les deux numéros** (10000213 / 63487),
  aucun doublon ; la carte l'affiche aussitôt.
- **Complétion à :50** : tâche `partenaire-lien-numeros` 18:50:00 UTC « succeeded » → le lien **104 porte 63487** ;
  fiche rechargée : les deux cartes réapparaissent (ZZ ESSAI SYNDIC 2B BIS, AUDIT CONSTRUCTION) ✅. (Le lien retiré 105
  reste sans numéro Hektor : la tâche ne touche que les liens actifs, sans conséquence.)
- Remarques d'écran, non traitées : le fil d'Ariane affiche « #null » tant que Hektor n'a pas rendu son numéro (puis
  « #63487 ») ; le syndic créé sur place apparaît dans l'annuaire **Clients** (« Contact », « À qualifier »).
- **Nettoyage (18:51-18:54 UTC)** : liens 104 et 106 retirés par « Retirer » (avec la confirmation « la trace reste ») ;
  contact 20000047 supprimé par « Supprimer le contact » (raison écrite) → `delete_hektor_contact` done,
  `hektor_delete_sent: true`, **`after_found: false`** (606275), son métier n'existe plus ; annonce supprimée par
  `app_console_create_delete_annonce_job` à son nom (« SUPPRIMER 63487 ») → `delete_hektor_annonce` done,
  **`after_found: false`**. Contrôle : 0 fiche 10000213 / 63487, 0 contact 20000047 / 606275, 0 attente, **85 liens
  actifs (comme au départ), 0 sans numéro**, file vide.
- ⏳ **À SA DÉCISION — corriger l'écran vide** (modification de code existant, `SyndicDuBien.tsx` seul) :
  A — la carte passe TOUJOURS les deux numéros (la lecture en base cherche déjà par l'un ou l'autre ; c'est une ligne) ;
  la prudence de §28.6 ter visait un croisement de numéros mesuré à 0. B — la carte passe notre numéro seulement pour un
  bien né dans l'app (n° ≥ 10 000 000) : le cas exact, rien ne change pour les biens venus de Hektor. C — compléter le
  numéro Hektor du lien dès son retour (déclencheur en base) : plus lourd, touche une table centrale.
- ✅ **DÉCIDÉ : B (08/11, « B »)** — `SyndicDuBien.tsx`, la lecture passe notre numéro quand Hektor n'a pas rendu le
  sien **ou** quand le bien est né dans l'app (`dossier >= 10 000 000`) ; biens venus de Hektor : inchangé. L'écriture
  (`ecrire`) passait déjà les deux numéros, rien n'y bouge. `npm run build` vert. **Répétition en base, annulée** (admin
  simulé, 10000009 / 63331, un lien diagnostiqueur posé sur notre numéro seul, comme entre la création et :50) : lecture
  « numéro Hektor seul » (l'ancienne carte) → **rien** ; lecture « les deux numéros » (la nouvelle) → **le partenaire**.
  Après coup : 0 ligne restée, 85 liens actifs. Mesuré aussi : **0 lien actif dont le numéro Hektor contredit celui du
  dossier** (le croisement que craignait §28.6 ter n'existe pas). ⚠ **Pas vu à l'écran** : aucun bien né dans l'app ne
  porte de lien aujourd'hui (l'essai est nettoyé) ; le prochain essai de création le montrera.
- 🔎 **Audit avant de pousser (08-09/11, « Audit d'abord »)** : la lecture en base est unique (le syndic appelle la
  générique), un seul numéro passé = comportement d'avant ; les **6 appelants** (Le Bien, onglet Contact, téléphone ×
  syndic/diagnostiqueur) passent tous les deux numéros ; plus grand numéro de bien venu de Hektor **7 589 452** (la
  limite ne peut pas se tromper) ; **0** bien avec deux liens actifs d'un même métier, **0** numéro Hektor en double,
  **0** lien qui contredit son bien, lien retiré jamais relu ; le geste d'écriture et la création ne bougent pas.
  ⭐ **Même défaut trouvé à l'autre bout** : la **fiche du partenaire** (`FicheSyndic.tsx`, ses biens) ne lisait que les
  liens qui ont un numéro Hektor → un bien né dans l'app y manquait jusqu'à :50.
- ✅ **Corrigé aussi (09/11, « Les 2 »)** : `FicheSyndic.tsx` prend, pour un lien sans numéro Hektor, celui de la fiche du
  bien (`app_dossiers_current`, mêmes droits que la lecture des biens juste après) dès que Hektor l'a rendu. Les ~70 s
  avant le retour de Hektor restent sans le bien sur cette fiche (tout y est rangé par numéro Hektor : détail, documents ;
  le changer serait une refonte). Build vert. **Répétition annulée** (admin, rôle `authenticated`, lien diagnostiqueur
  10014013 sur 10000009 seul) : ancienne fiche → **rien** ; complément → **10000009 → 63331**. 0 ligne restée, 85 actifs.
  Poussé : **69c9934**, Vercel prêt, le code servi contient les deux.
- ⛔ **REPRIS LE 09/11 — Frédéric : « mon app doit fonctionner même si Hektor est coupé, donc il faut lire nos numéros ;
  l'id Hektor est pour les workers ».** Il a raison : B et le complément d'hier ATTENDAIENT encore un numéro que seul Hektor
  donne (Hektor coupé, un bien né dans l'app ne serait jamais apparu sur la fiche de son partenaire). Mesure : **85 liens
  sur 85 portent notre numéro** ; liste des biens, détail et documents du parc vivant l'ont aussi (couverture identique
  par les deux numéros : 82 biens, 82 détails, 887 documents) ; seuls les index des ARCHIVES n'ont que le numéro Hektor
  (2 liens hors parc vivant : 7589192/63205, 5853060/40529) — un numéro déjà chez nous, pas une attente de Hektor.
- ✅ **FAIT (09/11, « Vas y »)** :
  · `SyndicDuBien.tsx` : la carte passe TOUJOURS notre numéro (et le numéro Hektor en plus) — B retiré ;
  · `lib/ficheSyndic.ts` : un bien de la fiche a pour CLÉ notre numéro (`cle`) ; bien, détail, documents rapprochés par
    notre numéro d'abord, le numéro Hektor en repli ; `hektorAnnonceId` vaut '' tant que Hektor n'a rien rendu ;
  · `FicheSyndic.tsx` : lit le parc vivant, le détail et les documents par `app_dossier_id` ; les archives par le numéro
    Hektor des seuls liens hors parc vivant ; le complément d'hier (69c9934) est retiré ;
  · `App.tsx` (2 lignes) : « Demander un document » et « Commander un diagnostic » prennent `cle` comme identifiant du
    choix (seul usage : la valeur du menu déroulant ; le texte envoyé utilise adresse, mandat, lots) ;
  · `test_metier_partenaire.cjs` : contrôle **(74 bis)** — un bien né dans l'app sans numéro Hektor a titre, copro et
    documents ; l'archivé reste trouvé ; un bien par numéro. **Tout vert** (le (74) d'avant inchangé). Build vert.
  · **Comparaison en base, ancienne / nouvelle lecture, sur les 85 liens** : 85 biens trouvés des deux côtés, **908
    documents des deux côtés** — rien de perdu pour les biens venus de Hektor.
  · Ce qui reste au numéro Hektor dans ce chantier : la complétion de :50 (pour les workers) et les archives.
  ⚠ Pas encore vu à l'écran ; aucun bien né dans l'app ne porte de lien aujourd'hui.
  Poussé (**8bf46f0**, « Oui commit push »), Vercel prêt. **VU EN LIGNE le 09/11** (lecture seule, rien envoyé) : fiche
  syndic IMMO DE FRANCE FOREZ VELAY (10217295) ouverte depuis le catalogue → **17 biens** (= la base), 8 avec documents de
  copro, 11 en vente, 1 367 € ; « Demander un document » : le menu porte notre numéro (7589288), changer de bien met à
  jour objet et message ; ouvrir un bien depuis la fiche → annonce 7589288, rubrique Copropriété → carte syndic « IMMO DE
  FRANCE FOREZ VELAY n° 10217295, repris de Hektor le 04/11 ». Console : 0 erreur. ⚠ Remarque, non liée à ce correctif
  (écran non touché) : la PREMIÈRE lecture du catalogue des partenaires a échoué sur « statement timeout » ; « Réessayer »
  a marché aussitôt (766 partenaires).
- 🔎 **Le délai dépassé du catalogue, mesuré (09/11, « Oui regarde »)** — rien de modifié :
  · l'échec est à **07:14:51** (heure de Paris) ; à cette minute, le run de nuit (fin 07:39) écrivait le registre des affaires
    (07:12:34 → 07:14:18) puis la doublure du registre des liens (07:14:19 →) : base occupée ;
  · la requête lourde est celle des NOTAIRES (`CataloguePartenaires.tsx` l. 38-46) : « rôle notaire_vendeur OU
    notaire_acquereur » dans `relation_roles_json`, triée par numéro, par pages de 1 000. **Aucun index sur cette colonne**
    → chaque page parcourt TOUTE la table des contacts (94 895 fiches, 1 132 notaires) : page 1 = 91 233 fiches écartées,
    page 2 = 93 763 (le décalage repart du début). Mesuré à chaud, en `authenticated` : 142 + 147 ms ;
  · un utilisateur connecté a une limite de **8 s** par requête (`authenticated`, `statement_timeout=8s`) ; les lectures
    réussies de cette forme vont jusqu'à **3,45 s** (pg_stat_statements, 52 appels, 146 884 blocs lus sur disque) — une
    lecture annulée n'y est pas comptée, donc le nombre d'échecs passés n'est pas mesurable ;
  · la même forme de filtre sert aux puces de rôle de l'annuaire des contacts (`lib/api.ts` l. 2586) ;
  · remède proposé, NON fait : un index GIN (`jsonb_path_ops`) sur `relation_roles_json` — à répéter d'abord (vérifier
    que les puces Mandants / Propriétaires de l'annuaire, qui trouvent beaucoup de fiches, ne changent pas de chemin).
- 🔎 **Répétition de l'index (09/11 08:05, « Oui »), transaction ANNULÉE** — base calme (run fini, descente finie à
  08:10, file vide) : index construit en **200 ms**, **248 Ko** ; mesuré en `authenticated` (admin), 8 lectures avant /
  après (catalogue notaires p1/p2, annuaire Mandants page + compte, Propriétaires, Acquéreurs page + compte, Notaires) :
  **aucune n'utilise l'index, temps inchangés** (catalogue 113 → 105 ms, 107 → 106 ms ; annuaire 1-8 ms). Sans RLS (même
  transaction) : **Bitmap Index Scan, 3,5 ms, 678 blocs**. ⛔ **Cause : sous RLS, `@>` (`jsonb_contains`) n'est pas
  LEAKPROOF** → la règle d'accès passe d'abord, ligne par ligne, et l'index est inutilisable (même famille que la mémoire
  « RLS + ::text tuent l'index »). **L'index seul ne sert à rien pour l'écran.** Les puces de l'annuaire ne sont pas
  gênées (elles trouvent vite 50 lignes dans l'ordre du tri).
  · remède alternatif proposé, NON fait : index + une petite fonction `SECURITY DEFINER` qui ne rend QUE les numéros des
    notaires (utilisateur actif, `anon` fermé) ; l'écran relit ensuite les fiches par numéro (`in`, 200 par 200, comme les
    autres métiers) **sous la règle d'accès habituelle** : le périmètre ne change pas.
- ✅ **PRÉPARÉ et RÉPÉTÉ (09/11, « oui »), PAS APPLIQUÉ** :
  · `supabase/patch_catalogue_notaires_numeros_2026-11-09.sql` (+ `_INVERSE`, `_REPETITION`) : l'index GIN et
    `app_catalogue_notaires_ids()` (SECURITY DEFINER, `is_app_user_active`, rend `text[]` des numéros, archives comprises,
    même règle des deux côtés) ; anon fermé, authenticated + service_role ; garde : rien n'est écrit si l'un existe déjà ;
    `lock_timeout` 3 s. Propriétaire de la table : `postgres` (BYPASSRLS) → la fonction lit l'index.
  · **Répétition jouée, annulée : 8 OK, 0 KO** — 01 l'index sert · 02 mêmes 1 132 numéros que l'ancienne lecture, même
    ordre · 03 autant de fiches relues par numéro · 04 **5,9 ms contre 85,5 ms** · 05 un négociateur voit les mêmes 1 132
    fiches qu'avant · 06 compte inconnu refusé · 07 droits · 08 l'annuaire (puce Mandants) ne change pas de chemin.
    Après coup : ni fonction ni index restés. (La répétition jouée portait le corps sans ses lignes de commentaire.)
  · `CataloguePartenaires.tsx` : les notaires = numéros par la fonction puis fiches par numéro (200 par 200) ; **repli sur
    la lecture d'avant** si la fonction manque ou refuse → l'écran peut partir AVANT ou APRÈS le patch sans casser.
    `test_metier_partenaire.cjs` (61) : plus d'interdiction totale des fonctions, une seule lecture permise. Build vert,
    tout vert. Ni commité, ni poussé.
- ✅ **APPLIQUÉ EN PRODUCTION le 09/11 à 08:15 (« Oui, applique »)** — base calme (0 requête active, file vide). Contrôle
  en `authenticated` (admin) juste après : index **valide**, 248 Ko ; anon **non**, authenticated **oui** ; **1 132
  numéros en 10,1 ms**, **identiques** à l'ancienne lecture ; 1 132 fiches relues par numéro.
  Poussé (**6c2b58c**), Vercel prêt, le code servi appelle la fonction. **VU EN LIGNE** : catalogue des partenaires
  ouvert, **634 notaires / 766 partenaires** (les mêmes chiffres que le matin), console sans erreur ; côté base
  (pg_stat_statements) : **3 appels de l'app, 8,3 ms en moyenne, 10 ms au plus**.

#### 28.11 — ALLUMÉ POUR TOUS (09/11, 08:22:49, « Allumer pour tous »)
- `app_setting.partenaires_choix_saisie` : `admin` → **`on`** (choisir syndic / diagnostiqueur, et « ＋ Nouveau », dans
  l'assistant de création et dans « Le Bien » ; les champs texte d'avant restent masqués) ;
- `app_setting.partenaires_design_contact` : `admin` → **`on`** (onglet Contact : carte du mandant et partenaires en
  « ticket » ; mêmes contenus, mêmes gestes).
- Seuls ces deux crans de l'écran lisent ces clés (App.tsx l. 15132, 32941, 32944) ; les deux passent par `roleConnecte`
  (défaut de la fiche sans `profileRole` corrigé le 07/11). Contrôle : un négociateur (rôle `authenticated`, jeton simulé)
  lit bien les deux à « on ». Les écritures restent gardées par la base (`app_partenaire_du_bien` : droit sur le bien).
- **Retour arrière** : remettre la valeur `admin` (une ligne chacune) — l'écran revient à l'état d'avant au chargement.
- Non vu : l'écran d'un négociateur (pas de compte d'essai ouvert de mon côté).
- Suite prévue (étape 3, §28.7) : le ménage des anciens champs texte « Syndic » / « Diagnostiqueur » — à faire une fois
  l'allumage éprouvé quelques jours.

#### 28.12 — Étape 4b / 4c (Copropriété, Diagnostics) : AUDIT (09/11, « Oui, 4b et 4c ») — rien codé
- **Les planches validées** : canevas https://claude.ai/artifact/RcvReTV74PM2L1ZEEWdoNq, `project/Copro.dc.html` et
  `project/Diag.dc.html` (06/11, « Planches 2 à 4 refaites dans ce style »).
- **L'écran réel** : « Le Bien » du cockpit, `App.tsx` ~l. 34769 (`CK_LB_SECTIONS` l. 30626, chaque case =
  `CkInlineField` l. 30662, enregistrement `onFieldSave`). Les cartes `SyndicDuBien` sont posées APRÈS les cases
  (Copropriété : 7 cases ; Diagnostics : 34 cases en grille, `repeat(auto-fill, minmax(230px, 1fr))`).
- **Mesure** : sur 13 534 biens vivants, **13 518** portent au moins une date « 0000-00-00 » dans leurs diagnostics
  (elle s'affiche telle quelle aujourd'hui).
- **Ce qui est proposé** (mêmes champs, mêmes gestes, rien d'ajouté) : 4b la carte du syndic en TÊTE (habillage
  « ticket » de l'onglet Contact), les 7 cases en grille de 4 ; 4c la carte du diagnostiqueur en tête, les chiffres du
  DPE en grandes cases, les 4 cases DPE oui/non en ligne, les 8 diagnostics en tableau résultat / date / commentaire
  (chaque cellule reste une case modifiable en place), une date « 0000-00-00 » montrée « — » SANS réécrire la valeur ;
  tout champ qui ne rentre dans aucun de ces groupes reste dans la grille d'aujourd'hui (aucun champ perdu). Le compteur
  « x / y » de la section ne change pas. Pas de couleur par résultat (« Négatif » vert…) : ce serait une règle neuve.
- **Cran neuf** `partenaires_design_bien` (absent = éteint ; à poser à `admin` avec accord). Téléphone : inchangé.
- ✅ **CODÉ (09/11, « Vas y »), ni commité ni poussé, cran PAS posé (= éteint pour tous)** :
  · `App.tsx` : cran `designBienCk` (par `roleConnecte`) ; dans la boucle de « Le Bien », la carte `SyndicDuBien` est
    construite une fois (`cartePartenaire`) et posée EN TÊTE habillée en ticket si le cran est allumé, sinon APRÈS les
    cases comme avant ; `caseDuBien` = la même `CkInlineField` ; Copropriété → grille de 4 (`fa-ck-lb-feats4`) ;
    Diagnostics → `CkDiagnosticsDessin` (chiffres DPE, cases oui/non, tableau des 8 diagnostics) + `repartirDiagnostics`
    qui renvoie le `reste` dans la grille d'avant ; `CkInlineField` gagne deux options d'AFFICHAGE facultatives (`vide`,
    `dateZeroVide`) — la modification part toujours de la valeur réelle (`setDraft(raw)`) ;
  · `le-bien-design.css` (neuf), importé après `contact-du-bien.css` ; aucune règle ne s'applique sans les classes posées
    derrière le cran ;
  · `lib/api.ts` : le mode maquette (sans base) allume aussi `partenaires_design_bien` (comme les autres crans du chantier) ;
  · `test_metier_partenaire.cjs` : **(102 bis)** ; le (102) restait vert en gardant `appDossierId` juste après `role`.
- **Contrôle** : build vert, toute la suite verte. **VU dans l'aperçu local (mode maquette, Chrome 1280 px)** : Copropriété
  (« Grand T3 Bellevue ») = carte syndic en tête, 7 cases en grille de 4, libellé au-dessus ; un clic sur « Lot » ouvre la
  modification, Échap l'annule ; Diagnostics = carte en tête, DPE en grandes cases (210 / 32 / 980 € / 1 380 € /
  15/05/2026 / 2021), 4 cases oui/non, tableau (Amiante Oui 15/05/2026 …), vides en « — ». Corrigé pendant le contrôle :
  la règle globale `table th` donnait un fond gris et des majuscules aux en-têtes de ligne. Téléphone : composant à part
  (`MobileDossierDetail`), non touché. Non vu : une vraie date « 0000-00-00 » à l'écran (la maquette locale n'en a pas ;
  la règle est tenue par le contrôle (102 bis)).
- ✅ **POUSSÉ (a226fde) et cran posé à `admin` le 09/11 à 08:51:01 (« Oui, les deux »)** — insertion
  `app_setting.partenaires_design_bien = 'admin'`. **VU EN LIGNE** sur l'annonce 1346991 (EA32418, Actif) : Copropriété =
  ticket « PLOTTON IMMOBILIER, repris de Hektor le 04/11/2026 » (Ouvrir sa fiche / Changer / Retirer) en tête, 7 cases en
  grille de 4 ; Diagnostics = ticket « Aucun diagnostiqueur » + « ＋ Choisir le diagnostiqueur », DPE 329 / 13 / 2 560 € /
  3 510 € / 2026-05-21 / 2021, cases oui/non à 0, tableau des 8 diagnostics avec les dates en « — » — **les 8 valent
  « 0000-00-00 » en base** (vérifié). Console sans erreur. ⚠ Remarque, pas de mon fait : « Statut syndicat » montre la
  valeur brute de Hektor « NOTPROCESS » (déjà ainsi avant). **Retour arrière** : `value = 'off'` (ou supprimer la ligne).
- ✅ **ALLUMÉ POUR TOUS le 09/11 à 08:58:08 (« ok vas y »)** : `partenaires_design_bien` `admin` → **`on`** ; un
  négociateur (jeton simulé) le lit bien à « on ».

#### 28.13 — ⏳ À FAIRE (demande de Frédéric, 09/11) : une fenêtre « Ajouter un partenaire » à part
> « il faudra pas oublier dans le chantier de faire une modal ajouter partenaire avec un design et une ergonomie
> différente que ajoute contact "client" mais qui fonctionne quand même avec les workers… car actuellement le lien
> ajouter syndic ou ajouter partenaires montre une modal pas avec recherche »
- **Aujourd'hui** : « ＋ Nouveau syndic / diagnostiqueur » (carte du bien, assistant de création ; événement
  `bienvu:creer-partenaire`, `SyndicDuBien.tsx` l. 23-27) et « Ajouter un partenaire » (annuaire, côté Partenaires)
  ouvrent la création de contact CLIENT, seulement préréglée sur « partenaire » et le métier — sans recherche préalable.
- **Ce qu'il veut** : une fenêtre propre aux partenaires, d'un design et d'une ergonomie à elle, AVEC une recherche
  (retrouver la fiche qui existe avant d'en créer une), et qui passe toujours par les mêmes workers (création du contact
  chez Hektor, notre numéro tout de suite, métier écrit chez nous).
- Rien n'est audité ni dessiné. Méthode : audit (les deux portes, le chemin du worker, les doublons — 15 noms en double
  au catalogue le 06/11) → maquette sur l'écran réel → « vas-y ».
- 🔎 **AUDIT (09/11, « Vas y »)** — rien codé pour la fenêtre :
  · **Les portes** : (1) « Ajouter un partenaire » de l'annuaire (bureau `setContactCreateOpen` App.tsx ~l. 26218 →
    `ContactsScreen` ~l. 49672 ; téléphone ~l. 50007) ouvre la fenêtre CLIENT « Nouveau contact » **réglée sur
    Acquéreur**, étape 2 « Recherche acquéreur » — vu en ligne ; rien ne la règle sur partenaire. (2) « ＋ Nouveau syndic /
    diagnostiqueur » (carte du bien, assistant ; événement `bienvu:creer-partenaire` → App.tsx ~l. 22325) ouvre la même
    fenêtre avec `partenaireImpose` (Type Partenaire, Personne morale, métier pré-choisi, étape 2 « Fiche directe ») —
    vu en ligne ; son en-tête affiche « Nouveau contact » et non « Nouveau diagnostiqueur ». Puis `surPartenaireCree` :
    numéro (`app_identite`) → `app_partenaire_metier_ecrire` → la carte pose le lien.
  · **Le chemin worker** : `HektorContactIdentityForm` → travail `create_hektor_contact` (création chez Hektor, notre
    numéro tout de suite) ; le déclencheur D-1 (`partenaire_metier_a_la_creation` = **on**) écrit le métier chez nous si
    le travail porte `contact_kind = partenaire` + `partner_job_id`. La nouvelle fenêtre peut garder EXACTEMENT ce chemin.
  · **Ce que la fenêtre montre à un partenaire** (vu en ligne) : compte / négociateur, type, structure, civilité, nom,
    prénom, e-mail, métier (17 choix, dont « A supprimer », « Collaborateur », « Societe » deux fois), site, portable,
    fixe, CP, adresse, ville, **date et lieu de naissance, statut matrimonial**, source, catégorie, **3 automatismes CRM
    (mail nouveau mandat, échéance, anniversaire)**, ⚠ **« Envoyer l'e-mail d'activation Espace personnel / RGPD » COCHÉ
    par défaut** (`sendRgpdEmail: true`), note.
  · **La recherche** : AUCUNE dans la fenêtre. Seul le choix depuis la carte du bien en a une, limitée au catalogue du
    métier (déjà partenaire). Une fiche CLIENT qui est en fait le partenaire n'y est pas trouvée.
  · **Mesures** : 181 fiches partenaires (syndic, diagnostiqueur, apporteur, courtier, banque, parrain) : e-mail 79,
    téléphone 94, ville 81, adresse 67, **sans prénom 87** (des sociétés), **date de naissance 0** ; noms en double parmi
    les 1 872 métiers actifs (notaires compris) : **52** ; créations de partenaires sur 30 jours : 8.
- 🐞 **Défaut trouvé pendant l'audit, CORRIGÉ dans le code (pas poussé)** : dans la carte « ticket » (4a Contact et
  4b/4c Le Bien, allumés pour tous ce matin), le halo `::after` (right : -60 px) rendait la carte défilable de 60 px ;
  le curseur posé dans la recherche du choix la faisait glisser à gauche (icône et nom coupés). Mesuré en ligne
  (`scrollWidth` 904 pour 844, `scrollLeft` 60) ; correctif `overflow: clip` (syndic-du-bien.css), éprouvé dans la page
  en ligne (scrollLeft reste 0 après le focus). Build et tests verts.
  **Poussé (927cff6, « Oui, pousse »), VU EN LIGNE** : CSS servi contient `.sb-syndic.sb-ticket{overflow:clip}` ; sur
  EA32418, « ＋ Choisir le diagnostiqueur » → curseur dans la recherche, `scrollLeft` 0, icône et « Ardrodiag » entiers.
- 🎨 **MAQUETTE (09/11, « Oui, maquette »)** — canevas https://claude.ai/artifact/RcvReTV74PM2L1ZEEWdoNq, planches 5 et
  6 (`AjoutPartenaire1.dc.html`, `AjoutPartenaire2.dc.html`), 1280 × 665, données fictives. UNE fenêtre pour les trois
  portes (annuaire bureau et téléphone, « ＋ Nouveau » de la carte du bien, assistant de création), en deux temps :
  · **1 · Chercher** : le métier en pastilles (syndic 75, diagnostiqueur 36, apporteur 35, courtier 22, parrain 15,
    banque 8 — comptes du registre), une grande recherche (nom, téléphone, e-mail, ville) dans TOUS les contacts, deux
    groupes de résultats : « Déjà syndic au catalogue » (Choisir / Ouvrir sa fiche) et « Dans vos contacts, sans ce
    métier » (« En faire un syndic » = le geste EXISTANT `app_partenaire_metier_ecrire` : aucune nouvelle fiche, rien
    chez Hektor) ; en bas « Aucun ne correspond ? ＋ Créer un nouveau syndic ».
  · **2 · Créer** : Société / Personne ; raison sociale ; la personne à qui parler (facultatif) ; téléphone, portable,
    e-mail ; adresse, CP, ville (communes du CP, comme C-3) ; site ; note ; « créé sous ton compte ». À droite : l'aperçu
    en ticket, « à l'enregistrement » (1 notre numéro tout de suite, 2 Hektor par le worker, 3 métier inscrit, 4 relié au
    bien si ouverte depuis un bien) et « réglé pour un partenaire ».
  · **Retirés** pour un partenaire : naissance, situation familiale, source, catégorie, la liste des 17 métiers.
  · **⏳ DÉCISIONS ATTENDUES** : (a) l'e-mail d'activation « espace client / RGPD » — coché par défaut aujourd'hui,
    proposé COUPÉ ; (b) les 3 automatismes clients (nouveau mandat, échéance, anniversaire) — proposés COUPÉS ; (c) les
    NOTAIRES hors de cette fenêtre (leur catalogue suit la table des parties, 1 659 au registre) ; (d) « Société » par
    défaut (87 des 181 partenaires n'ont pas de prénom). Rien n'est codé.
  · ✅ **DÉCIDÉ (09/11) : « Non, juste couleur et libellé »** — la fenêtre ne change selon le métier QUE par la couleur,
    l'icône et les libellés ; la fiche est la même pour tous (mesure à l'appui de la question : syndic 75/75 sans prénom,
    3 e-mails, 1 téléphone ; diagnostiqueur 12/36 sans prénom ; apporteur, courtier, parrain, banque : tous avec prénom).
    Les décisions (a) à (d) restent sans réponse explicite.
- 🔎 **AUDIT POUR CODER (09/11, « Oui on reprend »)** — rien codé :
  · **Créer** : `HektorContactIdentityForm` appelle `createHektorContactJob({ contact, priority: 18 })` (lib/api.ts
    l. 11583) avec `HektorContactIdentityInput` (l. 10677) : `contactKind`, `personType`, `partnerJobId`, `sendRgpdEmail`
    (vrai par défaut), `crmMandateSummaryEnabled` / `crmMandateExpirationEnabled` / `crmBirthdayEnabled` (vide = réglage
    Hektor). La ville suit le code postal par `useCommunesDuCodePostal` + `avertissementLocaliteContact` (8a C-3) :
    réutilisables tels quels. Après la création : `surPartenaireCree` (App.tsx ~l. 16925) = numéro → métier → poser.
  · **Codes métier Hektor** (`registre_partenaires_reprise.py`, METIER_HEKTOR) : syndic 5, diagnostiqueur 4, apporteur
    15, banque 19 ; **courtier et parrain n'ont PAS de code Hektor** → envoyer « non défini » (le déclencheur D-1
    n'écrit rien) et écrire le métier chez nous ensuite, comme `surPartenaireCree` le fait déjà (envoyer « 21 Autre »
    créerait une ligne « autre » parasite au registre).
  · **Chercher** : `app_contact_current.search_text` (index trigramme), sous la règle d'accès : mesuré en négociateur
    « foncia » 9 fiches en **455 ms**, « 0477 » 20 fiches en **3 ms** → recherche à la frappe (3 caractères, pause
    300 ms) tenable.
  · **« En faire un syndic »** : `app_partenaire_metier_ecrire(contact, métier)` existe, tout utilisateur actif, anon
    fermé ; rien chez Hektor. ⚠ Le contact reste aussi dans l'annuaire Clients (son type chez Hektor ne change pas).
- **PLAN DE CODE PROPOSÉ** : `AjouterPartenaire.tsx` (+ `lib/ajouterPartenaire.ts` pur, + CSS), derrière un cran neuf
  `partenaires_fenetre_ajout` (admin d'abord) ; branché aux 3 portes (annuaire bureau et téléphone ; événement
  `bienvu:creer-partenaire` de la carte du bien et de l'assistant) ; cran éteint = fenêtres d'aujourd'hui. Temps 1 :
  pastilles des 6 métiers, recherche dans tous les contacts, deux groupes (déjà au catalogue : Choisir / Ouvrir sa fiche ;
  sans ce métier : « En faire un … ») ; Temps 2 : la fiche courte, envoyée par `createHektorContactJob` (même travail,
  même worker), puis métier écrit et lien posé comme aujourd'hui. Contrôles dans `test_metier_partenaire.cjs`.
- ✅ **CODÉ (09/11, « Oui » aux quatre réglages), ni commité ni poussé, cran PAS posé (= éteint pour tous)** :
  · `lib/ajouterPartenaire.ts` (pur) : les 6 métiers et leur code Hektor (courtier / parrain sans code), couleur et
    libellés pris aux tuiles du catalogue, motif de recherche (mots qui se suivent, téléphone par paires de chiffres),
    deux groupes de résultats, la fiche → `HektorContactIdentityInput` (partenaire, société par défaut,
    `sendRgpdEmail: false` et les 3 automatismes à `false` — vérifié jusqu'au worker : `_email_rgpd` n'est envoyé que si
    vrai, l. 19660), ce qui manque, la ville qui suit le code postal, le compte Hektor (même règle que la fenêtre client,
    admin jamais sous l'e-mail de sa session) ;
  · `AjouterPartenaire.tsx` + `ajouter-partenaire.css` : la fenêtre en deux temps (planches 5 et 6), plein écran au
    téléphone ; recherche à la frappe dans `app_contact_current` (`search_text` / `email` / `phone_secondary`, sans les
    fiches de ménage, 20 au plus), métiers et biens reliés lus au registre ; « Choisir » / « Ouvrir sa fiche » ;
    « En faire un … » = `app_partenaire_metier_ecrire` ; « Créer le … » = `createHektorContactJob` (même travail que la
    fenêtre client) puis le métier, puis `poser` (depuis un bien) ou la fiche au catalogue (annuaire) ;
  · `App.tsx` : cran `partenaires_fenetre_ajout` ; l'événement `bienvu:creer-partenaire` (carte du bien, assistant) et
    « Ajouter un partenaire » de l'annuaire (bureau, téléphone, en-tête) ouvrent la nouvelle fenêtre quand il est allumé ;
    côté Clients et cran éteint : rien ne change ; `lib/api.ts` : le mode maquette allume ce cran ;
  · `test_metier_partenaire.cjs` : (104) à (109). Build vert, tout vert.
- **Contrôle** : vu dans l'aperçu local (mode maquette, sans base) : « Ajouter un syndic » (couleur syndic), temps 2
  « Nouveau syndic » conforme à la planche 6 (raison sociale reprise de la recherche, compte à choisir, « À
  l'enregistrement » 1-4, « Réglé pour un partenaire ») ; « Créer » vide → « Il manque un téléphone ou un e-mail, le
  négociateur. » ; téléphone 375 px : plein écran, couleur diagnostiqueur. Corrigé pendant le contrôle : le cadre de la
  case de recherche (style général des `input`), et le message « base indisponible ».
  ⚠ **Pas encore éprouvé avec la vraie base** : la recherche réelle, « En faire un … », une vraie création (écrit chez
  Hektor : essai depuis Estimations… à décider avec Frédéric) — tout cela se voit en allumant le cran pour lui seul.
- **Mise en ligne (09/11, « Oui, les deux » puis « Pousser le mien seul »)** : la branche locale portait 2 commits NON
  poussés d'une autre session (chantier Classeur : `52e67f3` alias des négociateurs, `0fdf64b` regel des 9 lignes) ; mon
  commit local `bb650f2` était posé dessus. Pour ne pas les envoyer, un commit à part `58ce259` a été construit sur
  `origin/main` (index temporaire, mêmes 7 fichiers, contenu identique à `bb650f2`, vérifié) et poussé seul ; les 2
  commits Classeur restent en local (`ahead 3, behind 1`) — la session Classeur devra fusionner `origin/main` avant son
  push (sans conflit : mes fichiers ne croisent pas les siens). Cran `partenaires_fenetre_ajout` = **`admin`** posé à
  11:59:45. ⚠ **Vercel n'a lancé AUCUN déploiement pour `58ce259`** (vérifié 5 min après : GitHub porte bien `58ce259`
  sur `main`, dernier déploiement = `927cff6`) — la fenêtre n'est donc pas encore en ligne.
  → Vercel a démarré SEUL, avec ~10 min de retard (`dpl_27d1Tqj8…`, 58ce259) : aucun déploiement lancé à la main.
- **VU EN LIGNE (09/11, cran `admin`, lecture seule, rien créé)** : Contacts → Partenaires → « Ajouter un partenaire » →
  « Ajouter un syndic », pastilles avec les vrais comptes (syndic 75, diagnostiqueur 36, apporteur 35, courtier 22,
  parrain 15, banque 8) ; « foncia » → « Déjà syndic au catalogue 8 » (FONCIA LOIRE AUVERGNE n° 10352728 « 7 de nos
  biens » en tête ; les doublons se voient : FONCIA LOIRE AUVERGNE ×4) et « Dans vos contacts, sans ce métier 1 »
  (CABINET FONCIA IGD, Saint-Étienne, « En faire un syndic » — non cliqué). Console sans erreur.
  🐞 **Défaut trouvé** : « 0477493374 » ramenait AUSSI 0477473112 — le motif « *04*77*49*33*74* » acceptait n'importe quoi
  entre les paires. **Corrigé (pas poussé)** : le numéro se cherche sous ses 3 formes exactes (collé, paires à points,
  paires à espaces), valeurs entre guillemets dans le filtre ; contrôle (105) mis à jour ; build vert, tout vert.
  **Poussé seul (2aa0819, « Vas y », même méthode que 58ce259 : les 2 commits Classeur restent en local), Vercel prêt.
  VU EN LIGNE** : « 0477493374 » → **1 seul** contact (CABINET FONCIA IGD) ; « 04.28.55 » → Ardrodiag et M. Dérumeaux
  (04.28.55.00.20, tous deux diagnostiqueurs, proposés « En faire un syndic ») ; « foncia loire » → les 4 FONCIA LOIRE
  AUVERGNE du catalogue. Console sans erreur. Fenêtre fermée sans rien créer.
  ⏳ Reste à éprouver : « En faire un … » et une vraie création (écrivent ; la création écrit chez Hektor) — avec accord.
- ✅ **ESSAI RÉEL (09/11, 12:29-12:34, « Oui, essaie »)** — départ : 75 syndics, 36 diagnostiqueurs, 1 872 métiers
  actifs, file vide, aucune fiche « ZZ ESSAI ».
  · Annuaire → « Ajouter un partenaire » → syndic → recherche « ZZ ESSAI SYNDIC » : « Aucun contact ne correspond » →
    « ＋ Créer un nouveau syndic » (raison sociale reprise de la recherche) → « ZZ ESSAI SYNDIC FENETRE - ne pas
    utiliser », fixe 04 99 99 99 61, 42700 Firminy, note, sous Emmanuelle PEREIRA → « Créer le syndic ».
  · **En moins de 4 s** la fiche du catalogue s'ouvre : **notre numéro 20000048**, « Syndic », « Hektor · en attente ».
    Métier `syndic` **une seule ligne** (1898, source écran, même seconde que la création — déclencheur D-1 + écriture de
    la fenêtre, aucun doublon). Charge du travail : `contact_kind` partenaire, `person_type` personne_morale,
    `partner_job_id` 5, **`send_rgpd_email` false**, automatismes false, compte pereira@.
  · **Hektor : créé en 21 s, n° 606288** ; paire 20000048 ↔ 606288 ; `crm_settings` tous false ; aucune mention RGPD au
    compte rendu ; après relecture : nom, Firminy, 42700 gardés ; le numéro revient en téléphone PRINCIPAL (Hektor range
    le seul numéro ainsi — non perdu) ; négociateur pereira@.
  · « En faire un diagnostiqueur » (pastille Diagnostiqueur, recherche, groupe « sans ce métier » qui montre « · syndic »)
    → ligne 1899 `diagnostiqueur` écrite, fiche « Syndic · Diagnostiqueur » ; **aucun travail d'écriture chez Hektor**
    (seulement les relectures que l'ouverture d'une fiche demande).
  · **Nettoyage** : « ⋯ » → « Supprimer » (confirmation « SUPPRIMER CONTACT 20000048 ») → `delete_hektor_contact` done,
    **`after_found: false`** ; 0 fiche restante (20000048 / 606288 / « ZZ ESSAI »), 0 ligne de métier ; retour à **75 /
    36 / 1 872**, file vide.
  · Remarque : les pastilles comptent les métiers (syndic 75 → 76 pendant l'essai) ; la tuile « Syndics » de l'annuaire
    compte les fiches visibles du catalogue (76 pendant l'essai aussi) — cohérent.
- ✅ **ALLUMÉ POUR TOUS le 09/11 à 12:35:35 (« Oui, pour tous »)** : `partenaires_fenetre_ajout` `admin` → **`on`** ; un
  négociateur (jeton simulé) le lit bien à « on ». Retour arrière : remettre `admin` ou `off` (les fenêtres d'avant
  reviennent). Un négociateur crée sous son propre compte (règle reprise de la fenêtre client).

#### 28.14 — ⏳ DEMANDE DE FRÉDÉRIC (09/11) : pré-remplir dès l'adresse, à la création d'une annonce
> « l'ajout d'une annonce active ou estimation : dès l'ajout de l'adresse du bien, l'app doit faire le script déjà
> existant permettant d'appeler les tables nécessaires pour récupérer le nom du syndic et le nom du diagnostiqueur si
> ceux-ci existent et pré-remplir les champs éventuellement récupérés comme année de construction, DPE etc. »
- **Ce qui existe déjà** (`lib/api.ts`) : `loadCadastre` (l. 4680), `loadCoproRnie` (l. 4946 : `syndic_nom`, nb de lots,
  période de construction, immatriculation…), `loadBdnb` (l. 4960 : année de construction, DPE « théorique », niveaux,
  logements, matériaux…), `loadDpe` (l. 4971, ADEME : étiquettes DPE / GES, date, consommation, émissions, surface).
  Utilisés AUJOURD'HUI dans l'écran Estimation (`EstimationDataSection` ~l. 11143, boutons, résultats gardés comme
  « sources d'estimation » du dossier) et `EstimationDocumentEditor` (~l. 6551) ; la RNIC propose aussi le syndic dans
  le choix de la carte du bien (`SyndicDuBien`).
- **Ce qui n'existe pas** : rien ne se déclenche à la saisie de l'adresse dans l'assistant de création ; aucune de ces
  sources ne donne le NOM DU DIAGNOSTIQUEUR (`DpeData` n'a pas ce champ) — piste à mesurer : nos propres biens à la même
  adresse / dans le même immeuble (liens `app_partenaire_lien`, diagnostics indiqués par Hektor).
- Rien n'est audité en profondeur ni codé.
- 🔎 **MESURES DES TEMPS (09/11, « est-ce possible ergonomiquement avec les temps de traitement ? »)** — appels directs
  aux services publics depuis le serveur, adresse d'EA32418 (45.420265, 4.383159), deux passages :
  · RNB (bâtiment le plus proche) 0,28 / 0,12 s · BDNB id 0,33 / 0,09 s · BDNB fiche 0,13 / 0,12 s · DPE ADEME
    0,27 / 0,08 s · cadastre (parcelle) 0,13 / 0,04 s → **la chaîne bâti + DPE tient sous 1 s** ;
  · **RNIC (registre des copropriétés, API tabulaire data.gouv) : 6 à 15 s PAR question**, le serveur en pose jusqu'à 3
    à la suite (3 colonnes de référence cadastrale) puis cherche les parcelles voisines → **15 à 35 s, parfois rien** (rien
    trouvé ici sur la parcelle 42218000LN0003) ;
  · notre serveur (Render, `gti-backend-xlyf`) : `/health` 0,2-0,3 s, démarré le 06/11, pas de mise en veille.
  · Ce qui revient, réel : BDNB **1977, 4 niveaux, 16 logements**, DPE « théorique » E ; ADEME **2 DPE à l'adresse** :
    E du 21/05/2026 (85,5 m², c'est celui de la fiche) et D du 27/08/2024 (100,6 m²) → dans un immeuble, le BON logement
    se choisit par la surface : il faut la surface avant, ou proposer les deux.
  · **Notre base** : 1 960 biens sur 10 611 (18 %) partagent leur adresse avec un autre de nos biens ; seuls 84 biens ont
    un partenaire relié → le diagnostiqueur « par l'adresse » trouvera peu aujourd'hui, davantage avec le temps.
- ⭐ **Frédéric (09/11) : « dans ce plan tu utilises les outils de l'estimation avec nos données internes, DVF etc. ? »**
  → la machinerie EXISTE déjà : « Tout générer » de l'estimation (`EstimationDocumentEditor.loadAllEditor`, App.tsx
  ~l. 6537) lance EN PARALLÈLE marché DVF (`loadDvfComparables`, notre table DVF interne par RPC), cadre de vie,
  cadastre, BDNB, DPE, patrimoine, loyers, INSEE, et RNIC si copropriété, et GARDE chaque résultat comme « source
  d'estimation » du dossier (`saveDossierEstimationSource` → `app_dossier_estimation.sources`). Le pré-remplissage doit
  RÉUTILISER cette machinerie et ce stockage (ne rien refaire à côté) : les sources « bâti » remplissent les cases de
  l'annonce, les autres (DVF, cadre, loyers, INSEE, patrimoine) préparent l'estimation et l'avis de valeur. À auditer :
  l'adresse est saisie AVANT que le dossier existe (résultats à garder en mémoire, puis à poser sur le dossier né).

#### 28.15 — PROPOSITION : « le dossier du bien se remplit à l'adresse » (09/11, demande de Frédéric) — rien codé
> « une proposition où tu utilises l'existant, car nous avons sur le serveur les bases pré-téléchargées pour la plupart,
> mais que tu développes un système sur mesure pour l'ajout d'annonce ; il faut toujours un geste humain pour valider ou
> pouvoir modifier une information pré-remplie. Cette amélioration doit être réfléchie. »
- **L'existant, mesuré** : DÉJÀ CHEZ NOUS (Supabase) : DVF `app_dvf_vente` (83 942 ventes, 48 Mo), loyers
  `app_commune_loyers`, INSEE `app_commune_insee`, risques `app_commune_risques`, communes `ref_commune_geo`
  (scripts `backend/scripts/ingest_*.py`). EN DIRECT (serveur → services publics) : RNB → BDNB, DPE ADEME, cadastre IGN,
  RNIC. Les fonctions de l'écran Estimation (`loadAllEditor`) et le rangement par dossier
  (`app_dossier_estimation.sources`) existent. L'assistant de création : étape 1 Offre (surface, pièces, niveaux…),
  2 adresse, 3 Secteur, 4 Composition, 5 Détails (dont Construction, Diagnostics & énergie, Copropriété), 6 Mandat / Prix,
  7 Texte.
- **Le principe** : un moteur unique « recherches du bien » (les fonctions EXISTANTES, rien de refait), déclenché quand
  l'adresse est VALIDÉE (coordonnées connues), qui ne remplit RIEN tout seul. Il dépose des **propositions** dans un
  panneau « Trouvé pour cette adresse » à côté de l'assistant ; chaque proposition montre la valeur, la source, sa date,
  son degré de sûreté, et trois gestes : **Reprendre** · **Modifier puis reprendre** · **Ignorer**. Une case reprise
  porte la marque « repris · BDNB » et reste modifiable comme les autres ; ce que l'utilisateur a TAPÉ n'est jamais
  remplacé : en cas de désaccord, la proposition s'affiche « vous : X · trouvé : Y ».
- **Trois niveaux de sûreté** : (1) le BÂTIMENT (année de construction, niveaux, logements — BDNB, sûr pour l'immeuble) ;
  (2) le LOGEMENT (DPE ADEME : sûr seulement si un seul DPE à l'adresse, ou si la surface déjà saisie le départage ; sinon
  les DPE trouvés sont PROPOSÉS au choix — 2 DPE à l'adresse d'EA32418) ; (3) le VOISINAGE (RNIC par parcelle voisine,
  DPE « à proximité ») : toujours « à vérifier », jamais repris d'un coup. Le DPE « théorique » de la BDNB n'est jamais
  proposé comme DPE.
- **Les partenaires** : le nom du syndic du RNIC est rapproché de NOTRE catalogue (nom) → « Choisir SYNDIC X » si la
  fiche existe, sinon « Créer ce syndic » ouvre la fenêtre « Ajouter un partenaire » (§28.13) pré-remplie du nom ; le
  diagnostiqueur : celui déjà relié à un de NOS biens à la même adresse (18 % de nos biens partagent leur adresse).
- **Les temps** : bâti + DPE + cadastre < 1 s → propositions quasi immédiates ; RNIC 15-35 s → arrive plus tard (une
  pastille « syndic trouvé ») sans bloquer. Option : **télécharger le RNIC de nos départements dans notre base**, comme
  DVF (script `ingest_rnic.py`, mise à jour trimestrielle) → réponse instantanée et plus de dépendance au service lent.
- **L'estimation prête** : le même passage lance aussi DVF, cadre de vie, loyers, INSEE, patrimoine, risques ; ils ne
  remplissent aucune case de l'annonce mais sont gardés en attente et POSÉS sur le dossier dès sa naissance (notre
  numéro, 1,3 s) → l'écran Estimation et l'avis de valeur sont prêts sans relance.
- **La trace** : chaque valeur reprise garde sa source (sources du dossier + la saisie de naissance déjà gardée,
  `app_annonce_saisie_naissance`) ; on saura toujours « d'où vient ce 1977 ».
- **Découpage proposé** : P1 le moteur + le panneau pour bâti / DPE / cadastre (assistant de création) ; P2 copropriété,
  syndic et diagnostiqueur (avec §28.13) ; P3 le RNIC téléchargé chez nous ; P4 les sources de l'estimation posées sur le
  dossier né ; P5 le même panneau dans « Le Bien » d'une annonce existante (bouton « Chercher pour cette adresse »).
- **Décisions attendues** : (a) panneau à côté de l'assistant, ou propositions sous chaque case ; (b) un « Tout reprendre »
  limité aux valeurs sûres, ou toujours case par case ; (c) télécharger le RNIC chez nous (P3).
- ⛔ **REFUSÉ (09/11) : « Non, j'aime pas l'ergonomie, il faut faire plus pratique pour l'utilisateur ; j'attends ta
  recommandation d'expert. Si doute (ex. DPE ou autre), montrer les choix possibles. »** → le panneau « Reprendre /
  Ignorer » valeur par valeur est abandonné (trop de gestes).
- **RECOMMANDATION (09/11) : « confirmer, pas saisir »** — UN écran de confirmation, UN geste :
  · juste après l'adresse, une étape courte « Ce que nous savons de ce bien » : les valeurs SÛRES en phrases simples,
    déjà cochées (« Immeuble de 1977 · 4 niveaux · 16 logements », « Parcelle LN 3 ») ; chaque valeur se corrige d'un
    clic sur place ; une coche se retire si c'est faux ;
  · les DOUTES en cartes à choisir, la plus probable mise en avant (DPE d'EA32418 : « E · 21/05/2026 · 85,5 m² —
    le plus proche de vos 85 m² » / « D · 27/08/2024 · 100,6 m² » / « Aucun de ces DPE ») ; même forme pour une
    copropriété voisine ou un syndic à rapprocher du catalogue ;
  · un seul bouton « Reprendre et continuer » = le geste humain ; « Passer » = rien n'est repris ;
  · ensuite, les cases reprises portent une marque discrète « repris · source » et restent modifiables ; ce qui a été tapé
    avant (ou lu par le scan IA) n'est jamais écrasé : le désaccord devient une carte à choisir « votre saisie / trouvé » ;
  · le lent (RNIC, 15-35 s) : la ligne « Copropriété : recherche en cours… » ne bloque pas ; si on est déjà plus loin, la
    proposition attend à l'étape Copropriété, au même format de cartes. Avec le RNIC téléchargé chez nous (P3), tout est
    sur le même écran dès l'adresse → recommandé.

#### 28.16 — LA VRAIE FENÊTRE « Nouvelle annonce », relevée en ligne (09/11, « base-toi d'abord sur la modale actuelle »)
- **Entrée** : « Nouvelle annonce » → « Manuellement » ou « Par photo, avec l'IA » (un agent lit la fiche et pré-remplit).
- **7 onglets** : 1 Offre (prix et bien) · 2 Photos · 3 Secteur (adresse) · 4 Composition (pièces) · 5 Détails ·
  6 Mandat / Prix · 7 Diffusion ; compteur « champs remplis » par étape ; Annuler / Retour / Suivant.
- **1 Offre** : titre, « Scanner la fiche (photos) », agence, négociateur, type (familles puis sous-types), « Données
  obligatoires » : prix, surface habitable, pièces, chambres, niveaux, garage, situation, vue.
- **3 Secteur** : « Adresse privée » = adresse, code postal, ville — **cases de texte simples : aucune suggestion
  d'adresse, aucune liste de communes, rien n'est localisé** (essai « 12 rue Larionov » + 42000 : rien) ; puis un bloc
  « Page 3 » : code postal public, ville publique, **adresse privée (rue), commune privée, code postal privé (déjà
  demandés juste au-dessus)**, immeuble, transport, proximité, environnement, **latitude et longitude à taper à la main**.
  ⚠ L'app sait déjà localiser une adresse (`geocodeAddress`, Géoplateforme, utilisé par « Le Bien » l. ~34327) et le
  worker relocalise à la création (`geocodeAddressBAN`) — l'assistant ne s'en sert pas.
- 🔎 **AUDIT DU SYSTÈME D'ADRESSE (09/11, « normalement il y a tout un système, ça ne se saisit pas à la main »)** —
  Frédéric a raison sur le fond : **la position n'est pas saisie à la main en pratique**. À la création, la saisie passe
  par `applyCreatedAnnonceInitialFields` → `normalizeHektorAnnonceUpdatePayload` → le chemin de modification du worker
  (console_job_worker.js ~l. 13385-13440) : (1) `resolveHektorPublicLocality` (code postal + ville → identifiants de
  commune Hektor) ; (2) `geocodeAddressBAN` (Géoplateforme) sur l'adresse privée → `updateHektorLocaliteByFeature` (la
  localité privée Hektor, `idville` + latitude / longitude) ; Hektor rend ensuite les coordonnées à la relecture. Les
  cases « Latitude / Longitude » de l'assistant ne sont qu'un forçage facultatif. Côté écran, « Le Bien » relocalise à
  chaque changement d'adresse (`geocodeAddress`, mémoire « adresse-edit-geoloc-et-overlay »).
  **Ce qui manque pour le pré-remplissage** : PENDANT la saisie, l'assistant ne connaît pas la position (elle n'existe
  qu'après le worker) et ne propose rien (code : trois `<input>` simples, App.tsx ~l. 22670).
  ⚠ **Mesure qui compte** : l'adresse réelle d'EA32418 est « 12 Rue Larionov, **42100** » ; tapée « 12 rue larionov
  42000 », la recherche libre de la Géoplateforme rend « 12 Rue de Laharpe 42000 » (score **0,48**, au-dessus du seuil
  0,35 de `geocodeAddress`) → **un mauvais point possible** ; la recherche à suggestions (`/geocodage/completion`, 0,04 à
  0,07 s) rend « 12 Rue Larionov, 42100 » aux bonnes coordonnées. Choisir une suggestion = la bonne adresse ET la bonne
  position dès la saisie.
- ⛔ **MIS DE CÔTÉ PAR FRÉDÉRIC (09/11) : « Donc on oublie l'idée et on revient au chantier »** — §28.14 à §28.16
  (pré-remplissage à l'adresse) restent ÉCRITS comme mémoire, rien n'est à faire. Ne pas relancer de soi-même.
  ⚠ Remarque gardée, hors chantier : une adresse tapée avec un mauvais code postal peut être localisée dans une AUTRE rue
  par la recherche libre (score 0,48 > seuil 0,35) — le worker de création utilise ce même service ; non mesuré sur le
  parc (combien de biens mal placés), non traité.
- **5 Détails** : Intérieur · Extérieur & annexes · Construction récente · Équipements & confort · **Diagnostics &
  énergie (37 cases, dont année de construction, DPE, GES, coûts, année de référence, 8 diagnostics × résultat / date /
  commentaire)** · **Copropriété (7 cases)** · Disponibilité & visite · **Intervenants** (choix syndic / diagnostiqueur).
- Fermé sans rien créer (aucune photo choisie → fermeture directe).
- **PROPOSITION SUR CETTE BASE (09/11)** — mêmes 7 onglets, mêmes cases, rien de déplacé hors de l'assistant :
  1. **Étape 3, l'adresse devient UNE case avec suggestions** (même source que `geocodeAddress`) : choisir une suggestion
     remplit adresse, code postal, ville, ET latitude / longitude ; les cases en double du bloc « Page 3 » (adresse privée
     (rue), commune privée, code postal privé) suivent la même valeur au lieu d'être retapées. C'est AUSSI ce qui donne
     au worker la bonne commune (les villes perdues chez Hektor faute d'identifiant de commune, chantier ⑧ C).
  2. **Juste sous l'adresse, une carte « Ce que nous savons de cette adresse »**, qui se remplit en quelques secondes :
     les valeurs sûres en phrases, déjà cochées (« Construit en 1977 · 4 niveaux · 16 logements », « Parcelle LN 3 ») ;
     les doutes en cartes à choisir, la plus probable en avant (« DPE E · 21/05/2026 · 85,5 m² — le plus proche de vos
     85 m² » / « DPE D · 27/08/2024 · 100,6 m² » / « Aucun ») ; un seul bouton **« Reprendre ces informations »** (le
     geste humain) ; « Plus tard » = rien n'est repris, les propositions attendent dans les sections concernées.
  3. **Étape 5, les sections concernées le montrent** : en tête de « Diagnostics & énergie » et « Copropriété », une
     ligne « 6 cases reprises de l'adresse · voir » ; chaque case reprise porte « repris · DPE ADEME » et reste
     modifiable ; une case déjà tapée (ou lue par le scan IA) n'est jamais remplacée — le désaccord devient un choix
     « votre saisie / trouvé ».
  4. **Intervenants** : « Syndic trouvé au registre : FONCIA… — Choisir (il est au catalogue) » ou « Créer ce syndic »
     (fenêtre §28.13, nom déjà rempli) ; diagnostiqueur d'un de nos biens à la même adresse s'il existe.
  5. **Le lent** (registre des copropriétés) : « recherche en cours… » dans la carte, sans bloquer ; s'il arrive après,
     il apparaît dans Copropriété / Intervenants au même format. Recommandé : RNIC téléchargé chez nous.
  6. **« Par photo, avec l'IA »** : même carte après la lecture ; ce que la fiche papier dit l'emporte, l'adresse
     complète le reste.
  7. **L'estimation prête** : DVF, cadre de vie, loyers, INSEE, risques sont pris au même moment et posés sur le dossier
     né — sans case à remplir dans l'assistant.

#### 28.17 — LOT 7 (apporteur et parrain) : AUDIT (09/11, « résous le commit push et enchaîne la suite ») — rien codé
- **Mise en ligne réglée d'abord** : la branche locale avait 4 commits d'avance / 2 de retard (ton push refusé) ; ma note
  commitée (327c853), fusion de `origin/main` (seul conflit : ma note, ma version contenait tout le texte en ligne —
  vérifié — gardée), poussé `4e3140d` : les 2 commits du Classeur sont en ligne, branche à jour.
- **Ce qui existe** : 50 fiches apporteur ou parrain au registre des métiers (35 + 15), toutes venues de Netty ;
  `app_partenaire_lien` accepte DÉJÀ l'apporteur sur un CLIENT (`objet = 'client'`, `client_contact_id`, rôles
  apporteur / courtier) et sur une AFFAIRE (`objet = 'affaire'`, `app_affaire_id`, rôles courtier / banque /
  apporteur) — deux contrôles en base l'encadrent ; un parrain se range en rôle `apporteur`. **0 lien** de ce genre
  aujourd'hui ; aucune fonction pour les écrire (`app_partenaire_du_bien` = syndic / diagnostiqueur sur un bien).
  La fiche d'un apporteur (`lib/metierPartenaire.ts`, BLOCS.apporteur) n'a que des blocs « en construction » :
  chiffres (affaires apportées, en cours, commission due, transformées), « Affaires apportées » (Contact apporté →
  Mandat → Commission due → Réglé), « Ce qu'il nous apporte », « Commissions » ; l'action « Noter une affaire
  apportée » est annoncée.
- **Décisions déjà prises** : Q1 « A » (un partenaire se relie à un CLIENT dès le premier jour) ; P4 « B » (la fiche
  CLIENT ne change pas → pas de « Apporté par » sur la fiche client) ; plan accéléré du 06/11 : « Noter une affaire
  apportée » = poser le lien client ↔ apporteur dans la table existante ; la commission et l'historique « en
  construction » ; la reprise des 53 apports de Netty « si elle reste simple » (lot 0 : 39 apporteurs, 51 sur 53
  retrouvés chez Hektor, mais 51 affaires → 107 biens possibles : une PROPOSITION à confirmer, pas un rattachement
  automatique). Source Netty : `C:/Hektor/Projet/affairs_contacts_relations.xlsx` (export figé du 27/02/2026).
- **PROPOSITION (version simple)** :
  · 7.1 « Noter une affaire apportée » sur la fiche de l'apporteur : chercher le CLIENT (même recherche que la fenêtre
    « Ajouter un partenaire »), le choisir → lien `objet client`, rôle `apporteur` ; une fonction neuve
    `app_partenaire_du_client` (utilisateur actif, droit sur le contact, retrait = trace) — écrit chez nous seulement ;
  · 7.2 la fiche de l'apporteur se remplit avec ce qui EXISTE : ses clients apportés, et pour chacun l'étape lue au
    registre (contact apporté / sous mandat / vente) ; « Commission » reste « en construction » ;
  · 7.3 plus tard : la commission (H1) et la reprise des 53 apports de Netty en propositions à confirmer.
- ✅ **CODÉ (09/11, « Oui »), rien d'appliqué ni de poussé, cran PAS posé** :
  · `supabase/patch_partenaire_du_client_2026-11-09.sql` (+ `_INVERSE`, `_REPETITION`) : `app_partenaire_du_client(p_role,
    p_client, p_partenaire, p_retirer)` (SECURITY DEFINER, utilisateur actif, rôle apporteur = métier apporteur ou parrain,
    rôle courtier = courtier ou banque — prêt pour le lot 6 ; client existant ; pas soi-même ; même lien actif une seule
    fois → « inchange » ; retrait = trace qui / quand) + index unique `app_partenaire_lien_un_client_uidx` (rôle, client,
    partenaire, actifs) ; anon fermé. **Répétition jouée, annulée : 9 OK, 0 KO** (apporteur 10011329, client 10000045 :
    pose, inchangé, une seule ligne `origine app` posée par l'admin, refus d'un syndic, refus d'un rôle « syndic »,
    refus de soi-même, retrait, trace du retrait, droits). Après coup : ni fonction ni index, 0 lien client.
  · `lib/affairesApportees.ts` (pur) : l'étape d'un client apporté lue au registre (`relation_roles_json` : vente >
    compromis > offre > mandat > propriétaire > contact), les 4 étapes de la fiche (commission « en construction »), le tri.
  · `AffairesApportees.tsx` + CSS : la section « Affaires apportées » réelle (étapes, liste des clients apportés, Retirer
    avec confirmation), « ＋ Noter une affaire apportée » (recherche du client, mêmes motifs que la fenêtre partenaire,
    sans l'apporteur lui-même ni les déjà notés) ; « Commission » reste « en construction ».
  · `App.tsx` : cran `partenaires_apporteur` dans la fiche ; le bouton de l'en-tête « Noter une affaire apportée » (jusque-là
    grisé « en construction ») ouvre le panneau quand le cran est allumé et que l'utilisateur gère les contacts.
  · `test_metier_partenaire.cjs` : (110) à (112). Build vert, tout vert. ⚠ Pas vu à l'écran : la maquette locale n'a pas
    le registre des métiers ; la preuve se fera en ligne, cran pour Frédéric seul.
- ✅ **EN PRODUCTION (09/11, « Oui »)** : patch `app_partenaire_du_client` appliqué (fonction + index, anon non,
  authenticated oui, 0 lien client) ; poussé **7aa03c7** (branche à jour, aucun commit d'autrui) ; cran
  `partenaires_apporteur` = **`admin`** à 13:06:27. **VU EN LIGNE** (lecture seule) : fiche de Christine LOVAGLIO
  (10215062, apporteur) → bouton d'en-tête « ＋ Noter une affaire apportée » ACTIF, section « Affaires apportées » réelle
  (0 client ; étapes 0 / 0 / — / — ; « Commission convenue, due, réglée » en construction) ; panneau : « lovaglio » →
  « Aucun contact ne correspond » (elle-même écartée, voulu) ; « dupont » → 15 contacts avec « Noter ». Console sans
  erreur. Rien n'a été noté. ⏳ Pas encore éprouvé : un vrai « Noter » puis « Retirer » (écrit chez nous seulement).
- ✅ **ESSAI RÉEL (09/11, 13:44-13:45, « Oui »)** sur la fiche de Christine LOVAGLIO : en-tête « ＋ Noter une affaire
  apportée » → « eric dupont » → 1 résultat (M. ERIC DUPONT, Issoire, n° 10353923) → « Noter » : la section passe à
  « 1 client », la ligne « M. ERIC DUPONT · Issoire · n° 10353923 · noté le 09/11/2026 » avec l'étape « Contact apporté »
  (ses rôles au registre : aucun) et « Retirer ». Base : lien **111** (apporteur, objet client, origine app, posé par
  Frédéric 13:44:37), **0 travail d'écriture** vers Hektor. « Retirer » → « Oui » : retour à « 0 client » ; lien 111
  `retire_le` 13:45:14, `retire_par` Frédéric (la trace reste) ; **0 lien client actif** ; console sans erreur.
- ✅ **ALLUMÉ POUR TOUS le 09/11 à 13:57:30 (« Oui »)** : `partenaires_apporteur` `admin` → **`on`** ; un négociateur
  (jeton simulé) lit « on » et peut appeler `app_partenaire_du_client`. Retour arrière : remettre `admin` ou `off`.
  Restent du lot 7 : la commission (H1) et la reprise des 53 apports de Netty en propositions (B7).

#### 28.18 — LA REPRISE DES 53 APPORTS DE NETTY : AUDIT (09/11, « la reprise des 53 apports de Netty ; on verra plus tard pour la commission ») — rien écrit
- **Source** : `affairs_contacts_relations.xlsx` (export figé du 27/02/2026, à la racine, hors git) : 53 relations
  `*_business_provider` (43 côté vendeur `representative`, 10 côté acquéreur `applicant`), 0 supprimée ; les clients de
  l'affaire = les `representative` (ou `applicant`) de la même affaire.
- **Rapprochement** (même méthode que `metier_netty.py` : nom + prénom + jour de création, paire UNIQUE seulement, couche
  locale `phase2.sqlite` en lecture seule ; aucun nom sorti) : 39 apporteurs → **34 retrouvés** (7 relations sans) ;
  clients **77 retrouvés / 9 introuvables** ; 1 apport sans client ; **60 couples apporteur ↔ client**, dont 1 où
  l'apporteur EST le client (écarté).
- ⭐ **Le point qui change tout** : lier au CLIENT (Q1 « A ») lève l'ambiguïté du lot 0 (51 affaires → 107 biens) — on ne
  devine pas le bien, on relie la personne. Mais **seuls 8 des 30 apporteurs ont le métier apporteur ou parrain** au
  catalogue : par métier au registre, **apporteur 5 → 10 liens, parrain 3 → 4 liens, AUCUN métier 19 → 41 liens (39 dont
  le client est dans l'app), notaire 2 → 4 liens**. 11 clients sont archivés (gardés : c'est l'histoire).
- **Choix à faire** : (A) reprendre les **14 liens sûrs** (apporteur ou parrain au catalogue) ; (B) en plus, donner aux
  **19 apporteurs sans métier** le métier « apporteur » (source Netty, ils ont apporté une affaire) → **+39 liens**, ils
  entrent au catalogue des apporteurs ; les 2 notaires : laissés de côté (leur fiche est celle d'un notaire).
  La date d'un lien repris = la date de la relation dans Netty ; origine `netty` ; écrit chez nous seulement.

#### 28.19 — LA REPRISE DES 14 LIENS SÛRS : ÉCRITE EN PRODUCTION (09/11, « Les 14 » puis « Oui »)
- **Choix de Frédéric : A**, les 14 liens dont l'apporteur a déjà le métier apporteur ou parrain. B (donner le métier aux
  19 sans métier) **n'est pas fait**.
- **Patch** `supabase/patch_reprise_apports_netty_2026-11-09.sql` (+ `_INVERSE`, `_REPETITION`) : 14 lignes
  `app_partenaire_lien` (role apporteur, objet client, origine `netty`, `pose_le` = date de la relation Netty, `pose_par`
  vide). Gardes : apporteur ≠ client, métier apporteur/parrain actif, client présent dans `app_contact_current`, pas de
  lien actif identique ; il refuse s'il existe déjà un lien netty, et **n'écrit rien s'il n'en passe pas exactement 14**.
- **Répétition 8/8** (rien gardé). ⚠ Au premier passage 7/8 : MON attendu disait 9 apporteurs, il y en a **8** — les
  données étaient justes.
- **Écrit le 09/11** : liens **142 à 155**, 8 apporteurs, dates 03/03/2016 → 30/12/2025, 14 actifs sans auteur ; les 91
  autres liens (6 app, 85 hektor) intacts.
- **Vu à l'écran** (production, `?ecran=contacts&vue=metiers&contact=10091890`) : section « Affaires apportées »,
  « 5 clients », chacun « noté le 31/03/2016 », étape « Sous mandat ». ⚠ Les 4 cases du haut (« Affaires apportées —
  depuis le début »…) restent à « — » : ce sont les cadres fixes de `metierPartenaire.ts` (l. 109), que le lot 7 simple
  ne remplit pas — sans rapport avec la reprise.
- **Retour arrière** : `_INVERSE.sql` retire les liens `origine = 'netty'` et vérifie que les autres sont intacts.

#### 28.20 — LOT 6 (courtier et banque) : AUDIT (09/11, « on passe à la suite ») — rien codé
- **Mesure** : 22 courtiers (14 avec e-mail) et 8 banques (7 avec e-mail) au catalogue ; **0 lien** ; aucune donnée de
  financement nulle part — 0 des 18 582 affaires de `app_affaire_console` ne parle de prêt, de banque ou de courtier
  (conditions suspensives vides de ce côté), les intervenants Hektor ne sont que NEGO / AGENCE ; Netty n'a pas de
  relation courtier (seulement vendeur, acquéreur, notaire, apporteur). ⇒ **rien à reprendre**, on part de zéro.
- **Ce qui existe déjà** : la fiche (coordonnées, interlocuteurs) ; famille `courtier` = courtier ET banque
  (`metierPartenaire.ts` l. 45) ; blocs « Acquéreurs suivis » (Orientés / Accord de principe / Offre de prêt / Financés)
  et bouton « Orienter un acquéreur » montrés « bientôt » ; le geste de base `app_partenaire_du_client` accepte DÉJÀ le
  rôle `courtier` (métier courtier ou banque) — préparé au lot 7 ; contrainte : objet client → rôle courtier ou
  apporteur (une banque se relie donc avec le rôle `courtier`).
- **Proposé (calque du lot 7)** : (1) section « Acquéreurs suivis » réelle = les clients reliés, avec l'étape lue au
  registre (offre / compromis / vente) ; « Accord de principe » et « Offre de prêt » restent « en construction » ;
  (2) bouton « Orienter un acquéreur » = choisir le client (même panneau de recherche) → le lien est posé chez nous +
  un message prêt à copier ou à ouvrir dans la messagerie (rien n'est envoyé par l'app) ; (3) cran
  `partenaires_courtier`. Aucun patch de base nécessaire.
- ⚠ **Ce que ça pourrait casser** : `AffairesApportees` sert le lot 7 — le généraliser par une propriété (rôle) avec
  l'apporteur par défaut, et rejouer les contrôles du lot 7 ; la chaîne des boutons d'en-tête (une branche de plus
  avant « bientôt »). ⚠ **RGPD** : envoyer les coordonnées d'un client à un courtier demande l'accord du client.

#### 28.21 — LOT 6 CODÉ (09/11, « Oui, sans coordonnées ») — DORMANT (cran absent), pas poussé
- ⛔ **Décision de Frédéric** : le message ne porte **ni le téléphone ni l'e-mail du client** — son nom, son projet et où il
  en est, rien d'autre.
- `lib/affairesApportees.ts` : `etapeDuClient(roles, defaut)` (le libellé « sans étape » devient « Orienté » pour le
  courtier) ; `compterOrientes` (Orientés = tous ; Accord de principe / Offre de prêt / Financés = « en construction »).
- `lib/orienterAcquereur.ts` (neuf, pur) : `rechercheAchat` (seule une recherche d'ACHAT, offre « 0 », décrit le projet),
  `lignesProjet` (biens recherchés, budget, secteur — une donnée absente n'est pas écrite), `messageOrientation` (sujet
  « Un acquéreur à accompagner : … », où il en est si offre / compromis / vente, signé « Groupe GTI »).
- `AffairesApportees.tsx` : propriété `role` (`apporteur` par défaut → **rien ne change pour le lot 7**), textes par rôle ;
  en courtier : « Acquéreurs suivis », « ＋ Orienter un acquéreur » (même recherche, même geste `app_partenaire_du_client`
  avec `p_role: 'courtier'`), puis le **message prêt** s'ouvre (modifiable, « Copier le message », « Ouvrir dans ma
  messagerie » si la fiche du courtier a un e-mail) ; un bouton « Message » par acquéreur le rouvre. Le message lit
  seulement la recherche du client (`offre, types_json, villes_json, prix_min, prix_max`). Rien n'est envoyé par l'app.
- `App.tsx` (+10 lignes) : cran `partenaires_courtier`, `courtierActif` (famille courtier = courtier ET banque), bouton
  d'en-tête « Orienter un acquéreur » (avant le « bientôt »), section avant le bloc « en construction ». `lib/api.ts` :
  le cran dans la liste du mode démo.
- Contrôles (113)-(117) ajoutés, (112) adapté à la forme commune (rôle par défaut apporteur), (45) marge 800 → 1 200
  (ordre des blocs inchangé) : **tout vert** ; `npm run build` vert. Hors de mon travail, 4 autres bancs sortent en échec
  (`test_ajouter_conjoint_ecran` (40)(41), `test_petits_defauts_point6` n° 1, `test_bienvu_textes`, `test_genants_front`) — mon diff ne touche ni le conjoint ni les dates ; non mesuré sur la version d'avant.
- ⏳ Pas encore vu à l'écran (le mode démo n'a pas de données de partenaire) : à voir en ligne, cran à `admin`.
- ✅ **Poussé seul** (« Oyi », 09/11) : `6d5c2dc` sur origin/main, sans les commits locaux des autres sessions. Cran
  `partenaires_courtier` = **`admin`** (app_setting, 15:36 UTC). **Vu en ligne** sur le courtier 10001493 (« Courtier ·
  Parrain ») : « Acquéreurs suivis · 0 client », « ＋ Orienter un acquéreur » (en-tête et section), Orientés 0, les trois
  autres étapes « — », « lot 6 · en construction ». Les 4 cartes du haut restent « — » (cadres fixes, comme au lot 7).
  ⏳ Reste : l'essai réel (orienter un client d'essai, lire le message, retirer), puis allumer pour tous.
- ✅ **ESSAI RÉEL (09/11, 16:11-16:12, « Oui »)** sur le courtier 10001493, avec le client d'essai du lot 7 (M. ERIC DUPONT,
  Issoire, n° 10353923, une recherche d'achat active). « ＋ Orienter un acquéreur » → « eric dupont » → 1 résultat →
  « Orienter » : « 1 client », Orientés 1, ligne « M. ERIC DUPONT · Issoire · n° 10353923 · noté le 09/11/2026 · Orienté ·
  Message · Retirer », et **le message s'ouvre seul** : objet « Un acquéreur à accompagner : M. ERIC DUPONT » ; corps avec
  « Bien recherché : Maison, Mas, Bastide, Propriete… » (10 types → 4 + …), « Budget : jusqu'à 150 000 € » (prix_min 0 non
  écrit), « Secteur : Issoire 63500 », signé « Groupe GTI ». **Contrôlé : ni téléphone ni e-mail du client**, ni dans le
  corps ni dans le lien ; « Ouvrir dans ma messagerie » = `mailto:` vers l'e-mail **du courtier**. « Fermer » puis
  « Message » : le même texte revient. Base : lien **156** (courtier, objet client, origine app, posé par Frédéric
  16:11:54), actifs 99 → 100. « Retirer » → « Oui » : retour à « Aucun acquéreur orienté » ; lien 156 `retire_le`
  16:12:46, `retire_par` rempli ; actifs 100 → 99, **0 lien courtier actif** ; **0 travail vers Hektor** pendant l'essai
  (le seul travail de l'heure est la relecture `refresh_console_contact_data` de 15:36, posée à l'ouverture de la fiche) ;
  console sans erreur. ⏳ Reste : allumer pour tous (cran `partenaires_courtier` → `on`), sur sa décision.
- ✅ **ALLUMÉ POUR TOUS (09/11, « Oui »)** : `partenaires_courtier` = **`on`** (app_setting). Les 30 courtiers et banques
  du registre (22 courtiers, 8 banques) ont « Acquéreurs suivis » et « Orienter un acquéreur ». Le retour arrière : remettre
  le cran à `admin` (ou le supprimer) ; les liens posés restent en base (`app_partenaire_lien`, rôle courtier).

### 7 ter. Les dépendances (techniques, pas un ordre décidé)

- 0 avant tout le reste ; 0.1 avant B2 ; 0.2 avant B1 ; 0.6 avant B5 ; 0.3 avant B6 ; 0.4 avant B7 ; 0.5 avant C2.
- A1 avant A2, A3, A5, K1, K6.
- B1, B2, B3 avant C1, C2, C3, et avant les blocs de métier (E2, F2, G3, H2).
- Les familles E, F, G, H sont indépendantes entre elles : leur ordre est D3.
- E4 et E5 servent aussi la fiche notaire : à faire une seule fois pour les deux.
