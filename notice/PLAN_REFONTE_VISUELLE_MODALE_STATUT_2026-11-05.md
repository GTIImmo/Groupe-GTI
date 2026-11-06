# Plan — refonte VISUELLE de la modale « Changer le statut »

*05/11/2026. Plan seulement : aucune ligne de code n'est écrite. Chaque lot attend le « vas-y » de
Frédéric (modification de code existant). Audit de référence : `AUDIT_REFONTE_MODALE_STATUT_2026-11-05.md`
(§9 à §11) · règles de la modale : `AUDIT_MODALE_STATUT_REGLES_2026-10-30.md` · maquette retenue :
« version professionnelle », https://claude.ai/artifact/Nx54fe4qLykaqMDr8EyuaF.*

## 0. La consigne, et ce qu'elle veut dire dans le code

Frédéric, 05/11 : « cela est juste du visuel, aucun code ne doit changer derrière ».

**Ne change pas — et on le PROUVE (§4) :**
- les fonctions qui agissent : `handleChangeHektorAnnonceStatus`, `handleGesteHektor`,
  `openStatusChangeModal`, `closeStatusChangeModal`, `createChangeHektorAnnonceStatusJob`,
  `gesteAffaireOptimistic`, `setMandatClotureApp`, `saveRepartition`, `ecrireAffaireCommission`,
  l'écriture des conditions et de la note, `relireApresLeGeste`, `rememberHektorActionJob` ;
- les ~60 états `statusChange*`, les drapeaux d'intention, tous les effets de préremplissage et
  d'héritage, `affaireCourantePourStatut` et les fonctions de garde (`etatFermeAuxTransactions`,
  `bienEngage`, `offreVerrouilleeParSonDossier`, `compromisVerrouilleParSaVente`, `gesteOffreSansEffet`,
  `modifierChezHektorPossible`, `nouvelleOffreFermeeSurBienEngage`, `avisGardeFouSaisie`…) ;
- les droits (manager et admin), la base, le worker, les messages d'erreur et de succès ;
- l'onglet d'ouverture, la fermeture après l'envoi, la confirmation du navigateur pour supprimer.

**Change — l'écran :** la mise en page, les couleurs, la typographie, l'ordre visuel, les libellés des
boutons (même action), les textes d'aide, le guide GTI, les pastilles, l'aperçu « avant → après », les
animations. La nouvelle vue LIT l'état existant et APPELLE les fonctions existantes, rien d'autre.

## 1. Ce que la maquette proposait et qui n'est PAS du visuel — écarté ou remplacé

1. **Ouvrir sur l'étape conseillée** → changerait `openStatusChangeModal`. Remplacé : la modale s'ouvre
   comme aujourd'hui ; la carte conseillée porte « Conseillé » et le guide propose « Aller à l'étape
   conseillée » (un clic = le même geste qu'un clic sur la carte).
2. **Garder la modale ouverte pour le suivi en 3 étapes** → changerait la fin de
   `handleChangeHektorAnnonceStatus`. Écarté de ce chantier (la modale se ferme comme aujourd'hui, le
   bandeau des travaux existant suit le geste).
3. **Confirmation de suppression dessinée** → changerait `handleGesteHektor` (`window.confirm`). Écarté :
   la confirmation du navigateur reste, avec son texte.
4. **Case « Je le fais volontairement » qui bloque l'envoi** → ajouterait une condition. Remplacé : le
   bandeau « Hors du parcours conseillé » informe, sans bloquer.
5. **Bouton éteint tant qu'un champ obligatoire est vide** → ajouterait une condition. Remplacé : le champ
   est marqué « À remplir » ; au clic, le message d'aujourd'hui s'affiche comme avant.
6. **Pièces du dossier notaire (6/11) et fiches contact cliquables** → nouvelle lecture et nouveau
   branchement. Écartés : les jetons gardent leur comportement actuel ; le guide ne cite que ce que la
   modale connaît déjà.

## 2. L'approche technique

- **Un interrupteur**, sur le modèle des refontes précédentes : `VITE_APP_STATUT_V2_ENABLED`, lu au
  build, ÉTEINT par défaut. Éteint = l'ancienne modale, octet pour octet. Retour arrière = remettre la
  variable à `false` dans Vercel et redéployer.
- **Un composant de présentation séparé**, `src/ModaleStatutV2.tsx`, rendu à la place de l'ancien bloc
  quand l'interrupteur est allumé. Il reçoit en propriétés EXACTEMENT ce que l'ancien bloc utilise :
  les valeurs d'état, les setters, les fonctions d'action, les fonctions de garde. Il n'importe AUCUNE
  fonction de `lib/api.ts`, n'appelle ni Supabase ni le worker, n'a pas d'effet de chargement.
  Seul état interne autorisé : l'interface (« Comment faire » ouvert, survol du bouton, section repliée).
- **Les composants existants sont réutilisés tels quels** : `SelecteurMandants`, `SelecteurNotaire`,
  `HistoriqueOffre`, `StatusPill`.
- **Deux petits modules sans effet** : `src/lib/statutParcours.ts` (situation du bien → étape actuelle,
  conseillée, hors parcours, lecture seule ; ne fait qu'appeler les fonctions de garde existantes) et
  `src/lib/statutGuide.ts` (les textes du guide GTI, chacun avec sa source en commentaire).
- **Une feuille de style à part**, `src/statut-v2.css`, toutes ses règles sous `.stv2` : aucune fuite
  sur le reste de l'app.

## 3. Les lots — un seul en code à la fois, chacun avec son « vas-y »

- **Lot 0 — inventaire et empreintes (sans toucher au code).** Liste de parité de TOUT ce que l'ancien
  bloc affiche et appelle (champs, jetons, sélecteurs, bandeaux, boutons et leurs conditions, versions
  téléphone `.rq-mobile`). Empreinte (hachage) des fonctions « derrière » du §0, pour prouver plus tard
  qu'elles n'ont pas bougé.
  ✅ **FAIT le 05/11 (soir)** — `notice/INVENTAIRE_PARITE_MODALE_STATUT_2026-11-05.md` ; outil
  `apps/hektor-v1/test_statut_v2_empreintes.cjs` + référence `statut_v2_reference.json` (sommet `e8bb683`) :
  **61 morceaux** (49 fonctions, 11 effets, l'ancien bloc de 1 318 lignes), témoin inverse **4 sur 4**, contrôle
  vert. Ligne de base des essais relevée (les 2 rouges de `test_bienvu_textes` existaient avant). Aucune ligne
  de l'application modifiée.
- **Lot 1 — coquille.** Interrupteur, composant vide branché, feuille `.stv2`, en-tête, bandeau du bien,
  parcours (cartes Actuel / Conseillé / Hors parcours / Lecture seule) et guide GTI. `statutParcours.ts`
  éprouvé sur les 11 situations de l'audit (§10.4).
  ✅ **FAIT le 06/11** — `src/ModaleStatutV2.tsx`, `src/lib/statutParcours.ts`, `src/lib/statutGuide.ts`,
  `src/statut-v2.css` (tout sous `.stv2`) ; interrupteur `APP_STATUT_V2_ENABLED` dans `App.tsx` : l'ancien bloc
  est seulement ENTOURÉ (`{APP_STATUT_V2_ENABLED ? (…V2…) : (<>` avant, `</>)}` après), pas une ligne ne change.
  Mesures : empreintes **61 morceaux identiques** + inventaire identique + parité verte ; `test_statut_parcours.cjs`
  vert (11 situations, 9 cas voisins, 55 guides complets, témoin inverse sur 2 gardes) ; les 3 essais de la modale
  verts ; `test_bienvu_textes` garde ses 2 rouges d'avant ; `npm run build` vert. À l'écran en local (démonstration
  `hektor-mock-statut-v2`, port 5193) : 1280 × 665 et téléphone 375 × 812 ; interrupteur éteint
  (`hektor-mock-statut-v2-eteint`, port 5192) : l'ancienne modale s'ouvre, la nouvelle n'est pas rendue.
  **Les gardes sont PASSÉES à `statutParcours`** (etatFermeAuxTransactions, bienEngage, dossiersOuvertsDuBien,
  isValidationApproved) : aucune règle recopiée. Le guide note la source de chaque phrase.
  **Trouvé et corrigé pendant le lot** : la date vide de Hektor `0000-00-00` lue comme un mandat échu (attrapé par
  l'essai) ; un registre VIDE sur un bien « Sous offre / Sous compromis » conseillait « Actif » (lecture en cours
  ou ratée : désormais aucun conseil et un avertissement) ; au téléphone et jusqu'à 1 180 px la modale s'ouvrait
  DERRIÈRE la fiche du bien (couche 50 < 100) → couche 180, comme `.modal-overlay` dans `mobile.css`.
  **Écarts assumés** : la situation 5 (annulation du mandat demandée) n'est pas reconnue, la modale ne lit pas les
  demandes et ce lot n'ajoute aucune lecture ; le bandeau « hors parcours » informe sans case à cocher (§1, point 4) ;
  les descriptions des cartes parlent métier (« Un acquéreur propose un prix. »), les libellés restent ceux d'avant.
  ⏰ Pour le lot 6 : au téléphone, la carte choisie peut être hors de la rangée qui défile.
- **Lot 2 — le formulaire offre / compromis / vente.** L'affaire, les personnes (sélecteurs existants),
  honoraires et commission, répartition (repliée, MÊME éditeur complet dépliable), conditions
  suspensives, note, alerte d'écart de prix, pastilles Actuel / Repris / Modifié / À remplir (lues sur
  `statusChangeTouches` et les fonctions de reprise existantes).
  ✅ **FAIT le 06/11** — `FormulaireTransaction` dans `src/ModaleStatutV2.tsx` (+ `src/lib/statutV2Types.ts`, les TYPES
  seulement). `App.tsx` : un seul ajout, la propriété `formulaire={{ … }}` qui passe les valeurs, setters et fonctions
  SOUS LEURS PROPRES NOMS (raccourci), plus `affaireCourante: affaireCourantePourStatut()`. Les sélecteurs existants
  (`SelecteurMandants`, `SelecteurNotaire`) sont passés tels quels.
  ⭐ **Preuve nouvelle dans l'outil du lot 0** (`test_statut_v2_empreintes.cjs`, partie parité) : chaque gestionnaire
  de saisie de la zone portée doit se retrouver MOT POUR MOT dans la vue, ou être déclaré. Résultat : **35 sur 35**,
  dont **1 écart déclaré** — « Qui paie la commission » passe d'un menu à deux boutons (même valeur, mêmes setters ; un
  clic sur le choix déjà posé ne fait rien, comme un menu dont la valeur ne change pas, sinon la commission serait
  « touchée » à tort). Témoin inverse : retirer un seul `toucherStatusChange` dans la vue → contrôle ROUGE, le geste
  nommé. Le contrôle s'étendra aux zones des lots 3 à 5.
  **Pastilles** : « Modifié » lit `statusChangeTouches` ; « À remplir » suit les `required` de l'ancien bloc ; une source
  (« Actuel », « Repris de l'offre », « Repris du compromis », « Prix du bien », « Aujourd'hui », « Par défaut »,
  « Mandat du bien ») n'est nommée QUE si la valeur du champ lui est ÉGALE — jamais devinée.
  **Répartition repliée** (résumé : jauge, noms, total) ; « Modifier » déplie le MÊME éditeur ; l'alerte de total reste
  visible repliée. Mesures : empreintes 61 morceaux identiques ; essais de la modale verts ; `test_bienvu_textes`
  garde ses 2 rouges d'avant ; `npm run build` vert. À l'écran (démonstration, 1280 × 665 et 375 × 812) : le montant
  tapé fait suivre le prix de vente et déduit le net (200 000 − 10 000 = 190 000), chaque case touchée passe
  « Modifié », « L'acquéreur » se choisit, la répartition se déplie, une condition libre s'ajoute ; l'onglet Offre
  montre la validité et pas de conditions. Corrigé en passant : la règle générale `.filter-field span` mettait les
  titres des sélecteurs en capitales — défaite dans la vue seulement.
  ⚠ Le formulaire n'est pas encore un `<form>` et n'a pas de bouton d'envoi : c'est le lot 5.
- **Lot 3 — Actif, Clos, offre en lecture seule.** Motifs, raison, date, « Précisez », mêmes messages.
  ✅ **FAIT le 06/11** — `Cloture` et la section « Remettre le bien en vente » dans `src/ModaleStatutV2.tsx` ;
  `App.tsx` : 3 lignes de plus dans `formulaire={{ … }}` (les 4 états de clôture et leurs setters,
  `hektorClosureEtatOptions`, `hektorClosureRaisonsFor`, `offreVerrouilleeParSonDossier`, `rattachementOffreProposee`).
  **Clos** : les 3 motifs en cartes, la raison reste un menu, la date, « Précisez » avec « À remplir » quand il est vide.
  Les 4 gestes repris **mot pour mot** (zone ajoutée à la parité de l'outil : 4 sur 4). ⚠ **Un texte corrigé, parce
  qu'il était faux** : « La clôture est définitive côté Hektor » (audit §7, I6 du 02/10) devient ce que le code fait —
  le statut part chez Hektor et coupe la diffusion, la date et le motif restent chez nous (prouvé le 21/10 sur 62774 :
  `closure: cloture_locale_uniquement`), le bien se remet en vente par « Actif » ; plus le conseil de la version
  téléphone (« vérifie l'offre ou le compromis en cours »). **Actif** : aucune saisie, ce que fait le geste.
  **Offre verrouillée par son dossier** (compromis ou vente derrière, règle du 16/09) : les 5 champs de l'offre passent
  en `readOnly` avec la pastille « Figée » et le bandeau « On ne revient plus sur cette offre » (mêmes mots, et la
  phrase de l'option 2 sur le rattachement) en pied de section — rien de ce qui part ne change (une valeur en lecture
  seule reste la même). Mesures : empreintes 61 morceaux identiques ; parité 35/35 et 4/4 ; essais de la modale verts ;
  `test_bienvu_textes` garde ses 2 rouges d'avant ; `npm run build` vert. À l'écran (démonstration, 1280 × 665 et
  375 × 812) : changer de motif remet la raison sur la première du motif, « Précisez » n'apparaît qu'avec « Autre
  motif ». ⚠ **Non vu à l'écran** : l'offre en lecture seule — la démonstration ne charge pas les affaires ; à
  regarder en production au lot 8 (VM412).
- **Lot 4 — les affaires du bien et tous les bandeaux.** Garde-fou, plusieurs affaires vivantes, bien
  engagé, reprise d'une affaire morte, plusieurs mandats, personnes non gardées (« J'ai vu, fermer »),
  détail dépliable, états du carnet, gestes admin sur un écart, « Choisir », historique de l'offre.
  ✅ **FAIT le 06/11** — `AffairesDuBien` dans `src/ModaleStatutV2.tsx` : les bandeaux (garde-fou, plusieurs affaires
  vivantes, bien engagé, reprise d'une affaire morte, plusieurs mandats, personnes non gardées avec « J'ai vu, fermer »)
  puis une ligne dépliable par affaire (genre, état, montant, date, acquéreur, dossier, « Choisir », « visée par les
  actions », plus dans Hektor, née dans l'app, rattachement) ; le détail (carnet d'abord, registre ensuite, états du
  carnet, gestes admin sur un écart, historique de l'offre). Mêmes calculs, sur les fonctions d'App.tsx passées.
  `App.tsx` : 5 lignes de plus dans `formulaire={{ … }}`. Parité : zone ajoutée à l'outil, **3 gestes sur 3** repris mot
  pour mot (« Choisir », « J'ai vu, fermer », les gestes admin) ; formulaire 35/35, Clos 4/4. Empreintes 61 morceaux
  identiques ; essais verts ; `npm run build` vert. **À l'écran** : la démonstration ne charge pas d'affaires, donc
  un RENDU D'ESSAI de la vue (`react-dom/server`, affaires fabriquées : offre acceptée, offre refusée d'un dossier
  terminé, compromis vivant visé, un écart de carnet, une personne non gardée), regardé à 1280 × 665 : bandeaux, offre
  refusée barrée, dossier « terminé », compromis « visé », états « arrivé » / « conflit » et les deux gestes admin.
  ⚠ Ce rendu n'exerce pas les VRAIES règles des bandeaux (elles sont passées, et déjà éprouvées par leurs essais) ;
  la vraie liste se regardera en production au lot 8.
  **Répartition des notes de fin** : « Modifier chez Hektor reprend… », régularisation, bien fermé aux transactions,
  compromis verrouillé, offre acceptée figée — elles expliquent les BOUTONS, elles viennent au lot 5 avec eux
  (l'offre verrouillée est déjà au lot 3).
- **Lot 5 — le pied.** Les mêmes boutons avec les mêmes conditions (Refuser, Accepter, Modifier,
  Annuler le compromis, Supprimer le compromis, Supprimer la vente, Envoyer), les mêmes états « Envoi… »,
  nouvel ordre et nouveaux libellés ; aperçu « avant → après » au survol (texte seulement).
  ✅ **FAIT le 06/11** — `Pied` et `NotesDesBoutons` dans `src/ModaleStatutV2.tsx`. La vue est désormais un
  `<form onSubmit={handleChangeHektorAnnonceStatus}>` comme l'ancien bloc : les `required` jouent au clic, Entrée
  envoie (aucun bouton sans `type`). **Libellés** : le bouton principal dit ce qu'il fait (« Enregistrer l'offre / le
  compromis / la vente », « Remettre en vente », « Clore le mandat ») ; « Modifier chez Hektor » devient « Mettre à
  jour l'offre / le compromis / la vente » ; « Annuler » devient « Fermer ». **Ordre** : Fermer et les gestes sans
  retour (« Supprimer le compromis… », « Supprimer la vente… », en lien rouge) à gauche, à l'écart ; Refuser,
  Accepter, Annuler le compromis, Mettre à jour, puis le bouton principal à droite. La confirmation du navigateur pour
  supprimer reste (elle est dans `handleGesteHektor`, plan §1 point 3). **Aperçu** au survol ou au focus du bouton
  principal : statut avant → après et deux effets sûrs (texte seulement). **Les 5 notes** qui expliquent les boutons
  (mise à jour d'une affaire existante, régularisation, bien fermé aux transactions, compromis verrouillé, offre
  acceptée figée) : mêmes conditions, mots alignés sur les nouveaux libellés. `App.tsx` : 3 lignes de plus.
  ⭐ **L'outil de parité contrôle aussi les CONDITIONS** (les `disabled={…}` et les conditions d'affichage
  `{cond ? (`), sur toutes les zones portées : formulaire 25/25, Clos 1/1, affaires 10/10 (1 écart déclaré : « Aucune
  affaire lue » au lieu de rien), pied 15/15 ; gestes : pied 7/7. Il a trouvé son propre défaut (un commentaire
  `/* */` au milieu d'une expression n'était pas retiré) — corrigé. Témoin inverse : retirer le garde-fou de
  l'extinction du bouton principal → ROUGE, la condition nommée. Empreintes 61 morceaux identiques ; essais verts ;
  `npm run build` vert. **À l'écran** : démonstration (1280 × 665 et 375 × 812) — formulaire réel, le montant vidé rend
  le formulaire invalide (`checkValidity`, sans envoyer), « Clore le mandat » avec « Précisez » vide aussi, aperçu
  vu au survol ; rendu d'essai avec un compromis en cours — Fermer, Supprimer le compromis…, Annuler le compromis,
  Mettre à jour le compromis, Enregistrer le compromis. ⚠ Rien n'a été ENVOYÉ : l'envoi réel est au lot 8 (62774,
  accord redemandé).
- **Lot 6 — téléphone.** Même composant, mise en page étroite ; contrôle à 390, 768 et 1280 × 665.
  ✅ **FAIT le 06/11** — `src/statut-v2.css` et `src/ModaleStatutV2.tsx` seulement (aucune ligne d'`App.tsx`).
  **Téléphone (≤ 767 px)** : les principes de l'ancienne modale (`modales-telephone.css`) — une feuille qui monte du
  bas avec sa poignée (94 dvh), les statuts en pastilles avec la description du choix dessous, le pied en colonne
  inversée (geste principal en haut, 52 px, pleine largeur ; Fermer tout en bas), des cibles ≥ 38 px, des champs de
  48 px **en 16 px** (en dessous, iOS zoome à chaque saisie ; l'ancienne était à 15). **La carte choisie reste
  visible** : un `useEffect` d'interface fait défiler la RANGÉE seulement (jamais le corps). **Tablette (768–1 023)** :
  champs sur 2 colonnes. **Hauteur** : plafond relevé de 640 à 820 px (les grands écrans gagnent de la place) ; à
  ≤ 700 px de haut, en-tête, bandeau et pied se resserrent. Mesures : à 1280 × 665 la zone utile passe de 445 à
  **487 px** (l'ancienne modale : 482) ; à 1366 × 600, 422 px et le pied visible ; à 390 × 844, rien ne déborde,
  champs en 16 px. ⚠ **Défaut trouvé à l'écran et corrigé** : à 390 px la rangée des statuts était TASSÉE (pastilles
  coupées) — le défaut que l'ancienne modale avait déjà payé ; même remède, aucun enfant du corps ne rétrécit.
  Contrôlé : démonstration à 390 × 844, 768 × 1024, 1280 × 665 et 1366 × 600 ; rendu d'essai à 390 × 844 avec un
  compromis en cours (le pied complet). Empreintes 61 morceaux identiques ; parité verte ; essais verts ; build vert.
  ⏰ **Pour le lot 7** : avec un compromis en cours, les 5 boutons empilés prennent ~260 px au téléphone (comme
  l'ancienne modale) — à resserrer si Frédéric le souhaite.
- **Lot 7 — animations et accessibilité.** Courbes et durées du cockpit, tout coupé si moins
  d'animations est demandé, focus visible, contrastes.
  ✅ **FAIT le 06/11** — `src/statut-v2.css` seulement. **Mouvements du cockpit** (`fa-cockpit-v2.css`,
  `fa-mandat-v3.css`) : entrée « rise » 0,32 s sur `cubic-bezier(.22, 1, .36, 1)` en cascade, « pop » des pastilles,
  transitions 150 / 240 ms sur `--bv-ease`, et la balise du mandat V3 (2,4 s) sur le bouton principal quand le
  formulaire est complet (`:valid`, c'est-à-dire les `required` de l'ancien bloc tous remplis ; écran seulement).
  **Moins d'animations demandé** : TOUT s'arrête, transitions comprises. ⭐ Éprouvé sans le vouloir : le navigateur de
  test est réglé ainsi, et aucune animation n'y tourne (cartes, bouton) ; la balise est contrôlée par sa règle (elle
  vise le bouton formulaire complet, plus formulaire incomplet). **Focus** : un contour magenta sur TOUT élément
  cliquable de la vue, y compris les sélecteurs existants et leurs listes (37 sur 37), éprouvé au clavier.
  **Contrastes MESURÉS** (chaque texte contre le fond réellement derrière lui, seuil 4,5 : 1, 3 : 1 en grand) : rendu
  d'essai, 389 textes, **1 sous le seuil** (« dossier n° … · terminé », 4,31) → foncé ; puis 0. Démonstration, onglets
  Compromis, Actif, Offre, Vendu (hors parcours), Clos : 0. Plus les textes d'aide des champs foncés (#6e7375).
  Empreintes 61 morceaux identiques ; parité verte ; essais verts ; build vert.
  ⚠ **Non fait, volontairement** : fermer avec Échap et garder le focus dans la fenêtre — l'ancienne modale ne le
  fait pas, et ce serait un comportement nouveau (Échap fermerait la saisie en cours). À trancher. Le pied empilé au
  téléphone (~260 px avec un compromis en cours) n'a pas été resserré non plus.
- **Lot 8 — contrôles et bascule** (§4), puis mise à jour des documents.
  🔧 **EN COURS le 06/11 — les étapes 1 à 5 du §4 sont FAITES, les étapes 6 et 7 attendent Frédéric.**
  1. Empreintes : **61 morceaux identiques** (référence du 05/11, l'autre session a modifié `App.tsx` dix fois depuis
     sans toucher un seul morceau suivi).
  2. Parité, ⭐ **complète** : l'inventaire du lot 0 est retrouvé ENTIER dans la vue — setters 35/35, gestes 3/3,
     fonctions 54/54, états 46/46, composants 5/5 — et chaque zone de l'ancien bloc est couverte, de l'en-tête au pied :
     gestes repris mot pour mot (en-tête et cartes 2/2, formulaire 35/35, Clos 4/4, affaires 3/3, pied 7/7) et conditions
     d'affichage et d'extinction (1/1, 25/25, 1/1, 10/10, 15/15). **3 écarts déclarés**, tous d'écran : la carte passe
     par `choisir` (mêmes deux appels), « qui paie » en deux boutons, « Aucune affaire lue » au lieu de rien.
  3. Les règles des boutons : `test_boutons_modale_point5`, `test_heritage_compromis_offre`, `test_offre_regularisation`
     verts ; `test_statut_parcours` vert (11 situations).
  4. `npm run build` vert.
  5. À l'écran en local : les 5 statuts × 390 × 844, 768 × 1024, 1280 × 665, interrupteur ALLUMÉ (15 sur 15 : pied et
     carte choisie visibles, rien ne déborde, le bon libellé) et ÉTEINT (l'ancienne modale, « Annuler » / « Envoyer vers
     … », la nouvelle jamais rendue).
  6. ✅ **EN PRODUCTION, SANS ENVOYER — 06/11.** Bascule : Frédéric a poussé les lots 6 à 8 et posé la variable.
     ⚠ **Deux faux départs, à retenir** : (a) une variable posée APRÈS la construction ne compte pas — il faut
     REDÉPLOYER ; (b) Vercel REFUSE une variable « Secret » dont le nom commence par `VITE_` (préfixe public) : le
     formulaire bloquait, la variable n'existait donc pas, et deux redéploiements ont produit le même paquet (même
     contenu = même fichier). Remède : type **Config**. Vérifié ensuite dans le paquet servi (`index-CoyP2ng2.js`) :
     l'interrupteur de la modale compilé à `"true"`. ⚠ Interroger le site toutes les 10 s depuis le serveur a
     déclenché le pare-feu de Vercel (contrôle anti-robot) : vérifier depuis le Chrome de Frédéric, en une lecture.
     **VM412** (sous compromis, 4 affaires) : Actuel Compromis, Conseillé Vendu, Offre grisée, Actif et Clos hors
     parcours ; les 4 affaires et leurs dossiers (dont « terminé ») ; le garde-fou éteint « Enregistrer le compromis » ;
     pied Supprimer / Annuler / Mettre à jour le compromis ; **l'offre en lecture seule vue en vrai** (5 champs
     « Figée », « On ne revient plus sur cette offre… n° 50120 », Refuser/Accepter absents, « Mettre à jour l'offre »
     éteint) ; Vendu « Repris du compromis ». **Jullianges** (Actif, aucune affaire) : Conseillé Offre, Actif grisé,
     Vendu hors parcours, « Aucune affaire lue », les 5 onglets et leurs boutons. **Rien envoyé** : sur les deux biens,
     les seuls travaux de la période sont deux `refresh_console_data` (la relecture posée à l'ouverture d'une fiche).
  7. ⏳ **L'envoi réel sur 62774**, avec son accord redemandé au moment du geste.

## 4. Comment on prouve que « rien n'a changé derrière »

1. **Empreintes** : les fonctions du §0 ont la même empreinte avant et après (script, témoin inverse :
   une modification volontaire doit être détectée).
2. **Parité** : un script vérifie que chaque setter, fonction d'action et fonction de garde utilisé par
   l'ancien bloc l'est aussi par `ModaleStatutV2.tsx`, et que celui-ci n'importe rien d'interdit
   (`lib/api`, Supabase, `create…Job`).
3. **Les règles des boutons** : `test_boutons_modale_point5.cjs` et `test_heritage_compromis_offre.cjs`
   restent verts ; `statutParcours.ts` a son propre essai sur les 11 situations.
4. **Build** : `npm run build` (jamais `tsc --noEmit`) ; `vite.config.*` remis par `git checkout` après.
5. **À l'écran, en local** (maquette de démonstration `hektor-mock-bienvu`) : les 5 statuts sur 3 formats,
   interrupteur allumé ET éteint (éteint = ancienne modale identique).
6. **En production** (après accord, variable posée par Frédéric dans Vercel) : ouvrir VM412 et
   Jullianges, parcourir les 5 statuts SANS envoyer, comparer à la liste de parité.
7. **Un envoi réel, seulement avec ton accord**, sur le bien d'essai 62774 : il prouve que le câblage
   appelle bien les mêmes fonctions.

## 5. Ce que ça pourrait casser ailleurs

- Un setter ou une fonction mal branché dans la nouvelle vue → attrapé par le script de parité (§4.2)
  et le parcours à l'écran.
- La répartition et les conditions se chargent par des effets dans `App` : ils ne bougent pas, mais
  la nouvelle vue doit afficher la même liste (contrôle §4.5).
- Le téléphone : la modale est un rendu unique partagé ; les classes `.rq-mobile` d'aujourd'hui doivent
  avoir leur équivalent.
- Les textes passés par `bvs()` (lot vocabulaire bienvu) : la nouvelle vue écrit ses propres textes,
  l'ancienne garde les siens ; `test_bienvu_textes.cjs` doit rester vert.
- Une autre session modifie `App.tsx` : relire `git log` avant chaque lot, stager fichier par fichier.

## 6. Retour arrière

Interrupteur éteint (variable Vercel à `false`, redéploiement) : l'ancienne modale revient telle
quelle. Le code ajouté est additif ; le retirer = supprimer le composant, les deux modules, la feuille
de style et la ligne d'aiguillage.

## 7. Tranché par Frédéric le 05/11/2026 (soir)

1. ✅ **Les 6 remplacements du §1 sont validés**, tels quels.
2. ✅ **Composant séparé** (`ModaleStatutV2.tsx` derrière l'interrupteur), pas de rhabillage de l'ancien bloc.
3. ✅ **Frédéric pose `VITE_APP_STATUT_V2_ENABLED=true` dans Vercel lui-même, APRÈS le lot 8**, quand je le
   lui dis. Avant, tout se contrôle en local (interrupteur allumé et éteint).
4. ✅ **Oui à l'envoi réel de contrôle sur 62774, à la fin** — son accord se redemande au moment du geste.

➡ ~~Prochaine étape : le lot 0~~ ✅ fait le 05/11. ~~Le lot 1~~ ✅ fait le 06/11. ~~Le lot 2~~ ✅ fait le 06/11. ~~Le lot 3~~ ✅ fait le 06/11. ~~Le lot 4~~ ✅ fait le 06/11. ~~Le lot 5~~ ✅ fait le 06/11, **poussé par Frédéric** (sommet distant `8155bb7`, interrupteur
VÉRIFIÉ ÉTEINT dans le paquet servi). ~~Le lot 6~~ ✅ fait le 06/11. ~~Le lot 7~~ ✅ fait le 06/11. **Lot 8 : étapes 1 à 5 faites le 06/11.**
**La nouvelle modale est EN PRODUCTION depuis le 06/11** (interrupteur allumé, contrôlé sans envoyer sur VM412 et
Jullianges). **06/11, après la bascule** : audit des champs « Vendeurs » et « N° de mandat »
(`notice/AUDIT_CHAMPS_VENDEURS_ET_MANDAT_MODALE_STATUT_2026-11-06.md`) — les deux retirés de la vue, et la modale
n'envoie plus de numéro de mandat (il faisait partir les offres sans mandat). ✅ **Poussé, puis l'envoi réel de
contrôle FAIT le 06/11 à 16:40** depuis la nouvelle modale, avec l'accord de Frédéric — sur **61398** (bien d'essai ;
62774 est clos depuis le 21/10) : offre 33132 de 170 000 €, `done`, 0 erreur, **mandat parti sous la forme de Hektor
`3-PROTEXA`** et rendu par Hektor (`id_mandat 3`, `PROTEXA`). Détail : note d'audit §4. ⏰ Reste à lire après la
nuit : `mandat_origine = hektor` au registre pour l'offre 33132.
⚠ Reste hors de ce chantier : le défaut « Choisir » (audit §12, les champs principaux ne se rechargent pas),
qui demande une décision à part — la refonte visuelle ne le corrige pas et ne doit pas le masquer.
