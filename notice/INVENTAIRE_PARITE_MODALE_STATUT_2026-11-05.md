# Inventaire de parité — modale « Changer le statut » (lot 0 de la refonte visuelle)

*05/11/2026, soir. Lot 0 du plan `PLAN_REFONTE_VISUELLE_MODALE_STATUT_2026-11-05.md` (§3, §4). Aucune ligne de
l'application n'a été modifiée. Ce document dit ce que la nouvelle vue (`ModaleStatutV2.tsx`, lots 1 à 7) devra
afficher et appeler, et comment on prouvera que rien n'a bougé derrière.*

## 1. L'outil de preuve

`apps/hektor-v1/test_statut_v2_empreintes.cjs`, avec sa référence `apps/hektor-v1/statut_v2_reference.json`
(posée le 05/11 sur le sommet `e8bb683`).

    node apps/hektor-v1/test_statut_v2_empreintes.cjs            contrôle (0 vert · 1 écart · 2 pas pu mesurer)
    node apps/hektor-v1/test_statut_v2_empreintes.cjs --poser    repose la référence — seulement après avoir LU l'écart

Il prend l'empreinte de **61 morceaux** : 49 fonctions, 11 effets, et l'ancien bloc de la modale entier. Chaque
empreinte est double : texte exact, et texte sans commentaires ni espaces. Un écart sur la première seule est
signalé « commentaire seulement » (⚠, sans échec) ; un écart de code est un échec (⛔).

**Témoin inverse, joué à chaque contrôle sur une copie en mémoire (4 sur 4 verts le 05/11)** :
1. une instruction ajoutée dans `handleGesteHektor` → un seul écart, sur elle, « code » ;
2. une ligne ajoutée hors de tout morceau → zéro écart (les découpes ne débordent pas) ;
3. un commentaire ajouté dans `affaireEstVivante` → un seul écart, « commentaire seulement » ;
4. « Fermer » changé en « Fermez » dans l'ancien bloc → le bloc est signalé.

⚠ Le premier passage du témoin 4 a été ROUGE : la mutation visait une ligne fixe du bloc, qui ne portait pas
« Fermer ». C'est le témoin qui était mal visé ; il cherche maintenant la ligne qui porte le mot.

⚠ La référence a été prise sur le fichier du disque, qui portait des modifications NON commitées d'une autre
session (catalogue des partenaires, lignes 16213, 25830, 26610, 48901-49035 d'`App.tsx`). Contrôlé : aucune ne
tombe dans les 61 morceaux. Si l'autre session touche un jour l'un d'eux, le contrôle dit lequel : lire l'écart,
puis reposer la référence.

**Au lot 1, la partie « parité » s'allume d'elle-même** dès que `src/ModaleStatutV2.tsx` existe : elle refuse
tout import de `lib/api`, toute mention de Supabase, tout `create…Job` et tout `fetch(`.

## 2. Ce qui ne doit pas bouger (les 61 morceaux)

**Dans `App.tsx` — les gestes et leur cycle (6)** : `handleChangeHektorAnnonceStatus`, `handleGesteHektor`,
`openStatusChangeModal`, `closeStatusChangeModal`, `relireApresLeGeste`, `rememberHektorActionJob`.

**La reprise et les gardes (25)** : `affaireCourantePourStatut`, `affairesVivantesPourStatut`, `gardeFouPourStatut`,
`etatFermeAuxTransactions`, `bienEngage`, `offreVerrouilleeParSonDossier`, `compromisVerrouilleParSaVente`,
`gesteOffreSansEffet`, `modifierChezHektorPossible`, `nouvelleOffreFermeeSurBienEngage`, `avisGardeFouSaisie`,
`offreEcarteeSurBienEngage`, `offreAccepteeFigeeChezHektor`, `dossiersOuvertsDuBien`, `affaireEstVivante`,
`avisPlusieursAffaires`, `gestesEcartCarnet`, `offreARegulariser`, `compromisDeLaRegularisation`,
`rattachementOffreProposee`, `dateOffreFaite`, `statusChangeNeedsTransaction`, `statusChangeNeedsSalePrice`,
`hektorClosureRaisonsFor`, `hektorStatusTargetLabel`.

**Les aides de saisie que le bloc appelle (11)** : `toucherStatusChange`, `apresSaisieCommission`,
`rechargerPersonnesEcarts`, `ajouterAcquereurStatut`, `retirerAcquereurStatut`, `ajouterCondition`,
`retirerCondition`, `modifierCondition`, `repartitionPoser`, `repartitionAjouterCase`, `repartitionRetirerCase`.

**Dans `lib/api.ts` (7)** : `createChangeHektorAnnonceStatusJob`, `gesteAffaireOptimistic`, `setMandatClotureApp`,
`saveRepartition`, `ecrireAffaireCommission`, `trancherAffaireCarnetEcart`, `fermerAffairePersonneEcart`.

**Les 11 effets de préremplissage et d'héritage** (un `useEffect` qui lit l'état de la modale et y écrit),
reconnus par leurs dépendances :
- `[statusChangeAffaires, statusChangeStatus, statusChangeAffaireChoisie]` — deux effets ;
- `[statusChangeTarget, statusChangeCommissionTouchee, statusChangeAffaires, chargeParMandat, …]` — la charge ;
- `[statusChangeBuyerSearch, statusChangeTarget?.app_dossier_id]` — la recherche d'acquéreur ;
- `[statusChangeAffaires, carnetRelecture]` — le carnet ;
- `[statusChangeAffaires, statusChangeStatus, carnetAffaires]` — trois effets, dont le grand préremplissage
  (181 lignes ; c'est lui qui ne dépend pas de l'affaire choisie, le défaut « Choisir » de l'audit §12) ;
- `[statusChangeBuyerNotaryId, …SellerNotaryNom]` — les notaires ;
- `[statusChangeTarget, repartitionChargeePour, repartitionChaineId, repartitionLignes, …]` — la répartition ;
- `[statusChangeAffaires, statusChangeStatus]` — l'héritage.

**L'ancien bloc entier** (`{statusChangeTarget ? (` … `) : null}`, 1 318 lignes, l. 22802-24119 le 05/11) :
interrupteur éteint, il doit rester octet pour octet.

## 3. Ce que l'ancien bloc utilise — la nouvelle vue devra le reprendre

**3 gestes** : `handleChangeHektorAnnonceStatus` (envoi, et « Modifier chez Hektor » avec `reprendre = true`),
`handleGesteHektor` (refus, accepte, annuler_compromis, supprimer_compromis, supprimer_vente),
`closeStatusChangeModal`.

**35 setters** : `setStatusChange…` Status, AffaireChoisie, Amount, SalePrice, Date, ValidityDays, SignatureDate,
RetractionDays, SelectedMandat, BuyerSearch, BuyerFees, BuyerFeesRate, BuyerNotaryId, BuyerNotaryNom,
SellerNotaryId, SellerNotaryNom, NotairesAffirmes, Mandants, MandantsAffirmes, ChargeCommission,
CommissionTouchee, HonorairesEntree, HonorairesEntreeTouche, NetSellerPrice, NetManuel, PrixVenteManuel,
Sequestration, Note, CloseEtat, CloseRaison, CloseReason, CloseDate ; plus `setCarnetEcartErreur`,
`setCarnetRelecture`, `setPersonnesEcartErreur`.

**46 états lus** : la cible (`statusChangeTarget`), le statut, les affaires, toutes les valeurs saisies ci-dessus,
`statusChangeBuyers` / `BuyerOptions` / `BuyerLoading` / `BuyerError`, `statusChangeConditions`,
`statusChangePending`, `statusChangeCorrectionPending`, `carnetAffaires`, `carnetEtats`, `carnetEcarts`,
`carnetEcartErreur`, `personnesEcarts`, `personnesEcartErreur`, `repartitionCases`, `repartitionPersonnes`,
`repartitionTotal`. La liste exacte est dans la référence (`inventaire.etats`).

**5 composants réutilisés tels quels** : `SelecteurMandants`, `SelecteurNotaire` (×2), `HistoriqueOffre`,
`StatusPill`, `CkAffaireParty`.

**Aides d'affichage, non suivies par empreinte** (elles ne décident rien ; la nouvelle vue peut les réutiliser) :
`bvs`, `formatDate`, `formatPrice`, `etatLabel`, `notaireAffiche`, `ckPartyName`, `mandantContactOptionTitle`,
`mandantContactOptionSubtitle`, `echeanceCondition`, `repartitionLigne`, `repartitionPourcentage`,
`repartitionRangs`, et les petites fonctions locales du bloc (`champ`, `jour`, `argent`).

## 4. Les boutons du pied — conditions d'affichage, à reprendre À L'IDENTIQUE

Tous sont éteints pendant un envoi (`statusChangePending || statusChangeCorrectionPending`).
- **Annuler** — toujours → `closeStatusChangeModal`.
- **Refuser l'offre** — une affaire courante, statut Offre, offre non verrouillée par son dossier, et le refus
  n'est pas sans effet (`gesteOffreSansEffet(…,'refus')`) → `handleGesteHektor('refus')`.
- **Accepter l'offre** — mêmes trois premières conditions, l'acceptation n'est pas sans effet, ET (l'offre n'est
  pas écartée d'un bien engagé OU elle est à régulariser, `offreARegulariser`) → `handleGesteHektor('accepte')`.
- **Modifier chez Hektor** — `modifierChezHektorPossible(statut, affaire, affaires)` ; éteint aussi si l'offre
  acceptée est figée (`offreAccepteeFigeeChezHektor`), avec l'infobulle qui dit pourquoi →
  `handleChangeHektorAnnonceStatus(e, true)`.
- **Annuler le compromis** puis **Supprimer le compromis** (rouge, second) — une affaire courante, statut
  Compromis, compromis non verrouillé par sa vente → `handleGesteHektor('annuler_compromis' | 'supprimer_compromis')`.
- **Supprimer la vente** (rouge) — une affaire courante, statut Vendu → `handleGesteHektor('supprimer_vente')`.
- **Envoyer vers {statut}** — absent si (le statut demande une transaction ET le bien est fermé aux transactions)
  OU une nouvelle offre est fermée sur un bien engagé ; éteint si le garde-fou bloque (`gardeFouPourStatut()`),
  avec son titre en infobulle → envoi du formulaire.

## 5. Le reste de l'écran, dans l'ordre de l'ancien bloc

1. En-tête : « Pilotage de l'annonce » / « Changer le statut », bouton Fermer.
2. Résumé du bien (titre, référence, mandat, `StatusPill`).
3. Les 5 cartes de statut (Actif, Offre, Compromis, Vendu, Clos) ; un clic pose le statut et remet l'affaire
   choisie à vide. Au téléphone (`.rq-mobile`), pastilles et description dessous.
4. Statut à transaction : montant, prix de vente (avec « Prix du mandat » pour compromis et vente), date,
   validité (offre), date d'acte et rétractation (compromis), numéro de mandat.
5. Acquéreurs : choisis (retirer ×), recherche, liste de propositions ; avertissement si les mandants sont
   « affirmés ».
6. Notaires acquéreur et vendeur (`SelecteurNotaire`).
7. Honoraires et commission : acquéreur, taux, vendeur (agence), charge, net vendeur, séquestre.
8. Répartition de la commission (entrée / sortie, jusqu'à 3 intervenants, ajouter / retirer une case, alerte si
   le total n'est pas 100 %).
9. Compromis : conditions suspensives (catalogue, condition libre, échéances, retirer ; alerte à 30).
10. Note libre ; alerte d'écart de prix (`ecartPrixTransaction`).
11. Vendu : texte de clôture sur la date de vente (le choix est retiré, C.19-c). Clos : état, raison (cartes),
    date de clôture, « Précisez le motif » si « Autre ».
12. Les bandeaux de la transaction : garde-fou (bloque ou informe), plusieurs affaires vivantes, « Ce bien est
    déjà engagé », reprise d'une affaire morte, plusieurs mandats, personnes non gardées (« J'ai vu, fermer »).
13. « Les affaires de ce bien » : genre, état, montant, date, personnes, n° de dossier (ouvert / clos), « visée
    par les actions », « Choisir », rattachement de l'offre proposée, états du carnet et gestes admin sur un écart.
14. Les notes de fin : « Modifier la transaction reprend… », offre verrouillée (« On ne revient plus sur cette
    offre »), « Régularisation possible », compromis verrouillé, offre acceptée figée.
15. Le pied (§4).

**50 conditions d'affichage** en tout dans le bloc (compte de la référence, `inventaire.conditions`) ; **2 classes
téléphone** (`rq-mobile`).

## 6. La ligne de base des essais (05/11, avant tout lot)

- `test_boutons_modale_point5.cjs` : vert.
- `test_heritage_compromis_offre.cjs` : vert.
- `test_offre_regularisation.cjs` : vert (21 cas, témoin, 3 mutants).
- `test_bienvu_textes.cjs` : **2 rouges qui existaient avant** (textes `bvs` orphelins, sans lien avec la
  modale) — à ne pas compter comme une régression au lot 8.
- `test_statut_v2_empreintes.cjs` : vert, 61 morceaux, témoin 4 sur 4.

## 7. Hors de ce chantier, rappel

Le défaut « Choisir » (audit §12) : le grand préremplissage ne dépend pas de l'affaire choisie. La refonte ne le
corrige pas — son effet est dans les 61 morceaux, donc le toucher ferait rougir le contrôle, ce qui est voulu.
