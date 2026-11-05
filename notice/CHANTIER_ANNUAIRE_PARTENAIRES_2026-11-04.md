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

### 7 ter. Les dépendances (techniques, pas un ordre décidé)

- 0 avant tout le reste ; 0.1 avant B2 ; 0.2 avant B1 ; 0.6 avant B5 ; 0.3 avant B6 ; 0.4 avant B7 ; 0.5 avant C2.
- A1 avant A2, A3, A5, K1, K6.
- B1, B2, B3 avant C1, C2, C3, et avant les blocs de métier (E2, F2, G3, H2).
- Les familles E, F, G, H sont indépendantes entre elles : leur ordre est D3.
- E4 et E5 servent aussi la fiche notaire : à faire une seule fois pour les deux.
