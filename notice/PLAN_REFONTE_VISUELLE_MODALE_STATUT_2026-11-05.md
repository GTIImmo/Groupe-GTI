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
- **Lot 1 — coquille.** Interrupteur, composant vide branché, feuille `.stv2`, en-tête, bandeau du bien,
  parcours (cartes Actuel / Conseillé / Hors parcours / Lecture seule) et guide GTI. `statutParcours.ts`
  éprouvé sur les 11 situations de l'audit (§10.4).
- **Lot 2 — le formulaire offre / compromis / vente.** L'affaire, les personnes (sélecteurs existants),
  honoraires et commission, répartition (repliée, MÊME éditeur complet dépliable), conditions
  suspensives, note, alerte d'écart de prix, pastilles Actuel / Repris / Modifié / À remplir (lues sur
  `statusChangeTouches` et les fonctions de reprise existantes).
- **Lot 3 — Actif, Clos, offre en lecture seule.** Motifs, raison, date, « Précisez », mêmes messages.
- **Lot 4 — les affaires du bien et tous les bandeaux.** Garde-fou, plusieurs affaires vivantes, bien
  engagé, reprise d'une affaire morte, plusieurs mandats, personnes non gardées (« J'ai vu, fermer »),
  détail dépliable, états du carnet, gestes admin sur un écart, « Choisir », historique de l'offre.
- **Lot 5 — le pied.** Les mêmes boutons avec les mêmes conditions (Refuser, Accepter, Modifier,
  Annuler le compromis, Supprimer le compromis, Supprimer la vente, Envoyer), les mêmes états « Envoi… »,
  nouvel ordre et nouveaux libellés ; aperçu « avant → après » au survol (texte seulement).
- **Lot 6 — téléphone.** Même composant, mise en page étroite ; contrôle à 390, 768 et 1280 × 665.
- **Lot 7 — animations et accessibilité.** Courbes et durées du cockpit, tout coupé si moins
  d'animations est demandé, focus visible, contrastes.
- **Lot 8 — contrôles et bascule** (§4), puis mise à jour des documents.

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

## 7. À trancher avant le lot 1

1. Valider les 6 remplacements du §1.
2. Valider l'approche « composant séparé » (recommandé) plutôt qu'un rhabillage de l'ancien bloc.
3. Qui pose `VITE_APP_STATUT_V2_ENABLED` dans Vercel, et quand (après le lot 8).
4. L'envoi réel de contrôle sur 62774 : oui ou non.
