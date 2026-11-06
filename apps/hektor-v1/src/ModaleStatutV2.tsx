// Modale « Changer le statut », refonte VISUELLE — la nouvelle vue (lot 1, 06/11/2026 : la coquille).
//
// Plan : notice/PLAN_REFONTE_VISUELLE_MODALE_STATUT_2026-11-05.md · inventaire de parité :
// notice/INVENTAIRE_PARITE_MODALE_STATUT_2026-11-05.md · maquette « version professionnelle ».
//
// ⛔ COMPOSANT DE PRÉSENTATION, RIEN D'AUTRE. Consigne de Frédéric (05/11) : « juste du visuel, aucun code
//   ne doit changer derrière ». Il LIT l'état de la modale et APPELLE les fonctions d'App.tsx qu'il reçoit ;
//   il n'importe rien de lib/api, n'appelle pas la base ni le worker, n'a aucun effet de chargement.
//   Le contrôle `test_statut_v2_empreintes.cjs` le vérifie (partie « parité »).
// ⛔ Seul état interne autorisé : l'interface (« Comment faire » ouvert ou fermé).
// Rendu à la place de l'ancien bloc seulement si VITE_APP_STATUT_V2_ENABLED est allumé au build.
//
// Lot 1 : en-tête, bandeau du bien, parcours (Actuel / Conseillé / Hors parcours / Lecture seule), guide GTI.
// Lot 2 : le formulaire offre / compromis / vente (FormulaireTransaction), chaque saisie reprise mot pour mot.
// Lot 3 : Actif, Clos (Cloture) et l'offre verrouillée par son dossier en lecture seule.
// Lot 4 : les affaires du bien et leurs bandeaux (AffairesDuBien).
// Lot 5 : le pied (Pied), ses notes (NotesDesBoutons) et l'aperçu « avant → après » ; la vue est un <form>.
// Restent le téléphone (lot 6), les animations et l'accessibilité (lot 7), les contrôles et la bascule (lot 8).

import { useEffect, useRef, useState, type ComponentType, type Dispatch, type FormEvent, type ReactNode, type SetStateAction } from 'react'
import type { Dossier } from './types'
import { situationDuBien, type AffaireLedgerRow, type GardesParcours, type HektorAnnonceStatusTarget } from './lib/statutParcours'
import { DESCRIPTION_CARTE, guidePour } from './lib/statutGuide'
import type {
  AffaireCondition, AffairePersonneEcart, ConditionCatalogueRow, DataScope, MandantContactSearchOption, RepartitionLigne, RepartitionPersonne,
} from './lib/statutV2Types'
import { bvs } from './lib/bienvuTexte'

type Setter<T> = Dispatch<SetStateAction<T>>
type Cote = 'entree' | 'sortie'
/** Une partie d'affaire, comme App.tsx la déclare (CkAffaireParty). */
type CkAffaireParty = { id?: string | null; civilite?: string | null; nom?: string | null; prenom?: string | null; coordonnees?: unknown; app_contact_id?: string | number | null }
/** Les motifs de clôture, comme App.tsx les déclare (formulaire PopinClos de Hektor). */
type HektorClosureEtat = 'choiceNonRenouv' | 'choiceVendu' | 'choiceAutre'

/** Lot 2 (06/11) — tout ce que le formulaire offre / compromis / vente de l'ancien bloc lit et appelle, SOUS LES
 *  MÊMES NOMS (App.tsx les passe en raccourci `{ statusChangeAmount, … }`). Rien d'autre. */
export type FormulaireStatutProps = {
  statusChangeAmount: string; setStatusChangeAmount: Setter<string>
  statusChangeSalePrice: string; setStatusChangeSalePrice: Setter<string>
  statusChangeDate: string; setStatusChangeDate: Setter<string>
  statusChangeValidityDays: string; setStatusChangeValidityDays: Setter<string>
  statusChangeSignatureDate: string; setStatusChangeSignatureDate: Setter<string>
  statusChangeRetractionDays: string; setStatusChangeRetractionDays: Setter<string>
  statusChangePrixVenteManuel: boolean; setStatusChangePrixVenteManuel: Setter<boolean>
  statusChangeBuyers: MandantContactSearchOption[]
  statusChangeBuyerSearch: string; setStatusChangeBuyerSearch: Setter<string>
  statusChangeBuyerOptions: MandantContactSearchOption[]
  statusChangeBuyerLoading: boolean
  statusChangeBuyerError: string | null
  statusChangeSellerNotaryId: string; setStatusChangeSellerNotaryId: Setter<string>
  statusChangeSellerNotaryNom: string; setStatusChangeSellerNotaryNom: Setter<string>
  statusChangeBuyerNotaryId: string; setStatusChangeBuyerNotaryId: Setter<string>
  statusChangeBuyerNotaryNom: string; setStatusChangeBuyerNotaryNom: Setter<string>
  setStatusChangeNotairesAffirmes: Setter<{ acquereur: boolean; mandant: boolean }>
  statusChangeBuyerFees: string; setStatusChangeBuyerFees: Setter<string>
  statusChangeBuyerFeesRate: string; setStatusChangeBuyerFeesRate: Setter<string>
  statusChangeHonorairesEntree: string; setStatusChangeHonorairesEntree: Setter<string>
  setStatusChangeHonorairesEntreeTouche: Setter<boolean>
  setStatusChangeCommissionTouchee: Setter<boolean>
  statusChangeChargeCommission: string; setStatusChangeChargeCommission: Setter<string>
  statusChangeNetSellerPrice: string; setStatusChangeNetSellerPrice: Setter<string>
  statusChangeNetManuel: boolean; setStatusChangeNetManuel: Setter<boolean>
  statusChangeSequestration: string; setStatusChangeSequestration: Setter<string>
  statusChangeConditions: AffaireCondition[]
  conditionCatalogue: ConditionCatalogueRow[]
  statusChangeNote: string; setStatusChangeNote: Setter<string>
  statusChangeTouches: string[]
  repartitionCases: Record<Cote, number>
  repartitionPersonnes: RepartitionPersonne[]
  repartitionTotal: number
  ecartPrixTransaction: { prix: number; net: number; entree: number; sortie: number; attendu: number; ecart: number } | null
  dataScope: DataScope | undefined
  toucherStatusChange: (...cles: string[]) => void
  apresSaisieCommission: (suivant: { montant?: string; entree?: string; sortie?: string }) => void
  ajouterAcquereurStatut: (option: MandantContactSearchOption) => void
  retirerAcquereurStatut: (id: string) => void
  ajouterCondition: (depuis: ConditionCatalogueRow | null) => void
  modifierCondition: (rang: number, champ: keyof AffaireCondition, valeur: string) => void
  retirerCondition: (rang: number) => void
  echeanceCondition: (condition: AffaireCondition) => string
  repartitionLigne: (cote: Cote, rang: 1 | 2 | 3) => RepartitionLigne | null
  repartitionRangs: (cote: Cote) => Array<1 | 2 | 3>
  repartitionPoser: (cote: Cote, rang: 1 | 2 | 3, idUser: string) => void
  repartitionPourcentage: (cote: Cote, rang: 1 | 2 | 3, valeur: string) => void
  repartitionAjouterCase: (cote: Cote) => void
  repartitionRetirerCase: (cote: Cote) => void
  statusChangeNeedsTransaction: (value: HektorAnnonceStatusTarget) => boolean
  statusChangeNeedsSalePrice: (value: HektorAnnonceStatusTarget) => boolean
  mandantContactOptionTitle: (option: MandantContactSearchOption | null | undefined) => string
  mandantContactOptionSubtitle: (option: MandantContactSearchOption) => string
  formatDate: (value: string | null | undefined) => string
  formatPrice: (value: number | string | null | undefined) => string
  /** le résultat de affaireCourantePourStatut(), calculé dans App comme l'ancien bloc le fait */
  affaireCourante: AffaireLedgerRow | null
  offreAccepteeAReprendreAuCompromis: (lignes: AffaireLedgerRow[]) => AffaireLedgerRow | null
  affaireEstVivante: (a: AffaireLedgerRow) => boolean
  // Lot 3 (06/11) — Clos, et l'offre verrouillée par son dossier.
  statusChangeCloseEtat: HektorClosureEtat; setStatusChangeCloseEtat: Setter<HektorClosureEtat>
  statusChangeCloseRaison: string; setStatusChangeCloseRaison: Setter<string>
  statusChangeCloseDate: string; setStatusChangeCloseDate: Setter<string>
  statusChangeCloseReason: string; setStatusChangeCloseReason: Setter<string>
  hektorClosureEtatOptions: Array<{ value: HektorClosureEtat; label: string; raisons: Array<{ value: string; label: string }> }>
  hektorClosureRaisonsFor: (etat: HektorClosureEtat) => Array<{ value: string; label: string }>
  offreVerrouilleeParSonDossier: (lignes: AffaireLedgerRow[], affaire: AffaireLedgerRow | null | undefined) => AffaireLedgerRow | null
  rattachementOffreProposee: (lignes: AffaireLedgerRow[], offre: AffaireLedgerRow) => { quand: string; compromis: AffaireLedgerRow } | null
  // Lot 4 (06/11) — les affaires du bien et leurs bandeaux.
  setStatusChangeAffaireChoisie: (value: number | null) => void
  AFFAIRE_PAR_STATUT: Partial<Record<HektorAnnonceStatusTarget, string>>
  AFFAIRE_ETATS_MORTS: Set<string>
  AFFAIRE_GENRE_LABEL: Record<string, string>
  affaireEtatLabel: (kind: string, state: string | null | undefined) => string
  affairesVivantesPourStatut: () => AffaireLedgerRow[]
  avisPlusieursAffaires: (genre: string, vivantes: AffaireLedgerRow[]) => { ton: 'normal' | 'avertir' | 'alerte'; titre: string; detail: string } | null
  gardeFouPourStatut: () => { bloque: boolean; titre: string; detail: string } | null
  dossiersOuvertsDuBien: (lignes: AffaireLedgerRow[]) => Array<{ chaine: string; ouvert: boolean }>
  bienEngage: (lignes: AffaireLedgerRow[]) => boolean
  offreEcarteeSurBienEngage: (lignes: AffaireLedgerRow[], affaire: AffaireLedgerRow | null | undefined) => boolean
  ckPartyName: (p?: CkAffaireParty | null) => string
  parseJson: <T>(value: string | null | undefined, fallback: T) => T
  carnetAffaires: Map<number, Record<string, string>>
  carnetEtats: Map<number, Record<string, string>>
  carnetEcarts: Map<number, Set<string>>
  carnetEcartErreur: string; setCarnetEcartErreur: Setter<string>
  setCarnetRelecture: Setter<number>
  isAdmin: boolean
  gestesEcartCarnet: (etat: string) => Array<{ decision: 'hektor' | 'app' | 'attendre'; libelle: string; aide: string }>
  trancherAffaireCarnetEcart: (appAffaireId: number, champ: string, decision: 'hektor' | 'app' | 'attendre') => Promise<void>
  personnesEcarts: AffairePersonneEcart[]
  personnesEcartErreur: string; setPersonnesEcartErreur: Setter<string>
  fermerAffairePersonneEcart: (id: number) => Promise<void>
  rechargerPersonnesEcarts: () => Promise<void>
  HistoriqueOffre: ComponentType<{ propositions: unknown }>
  // Lot 5 (06/11) — le pied et les notes qui expliquent ses boutons.
  statusChangeCorrectionPending: boolean
  handleGesteHektor: (geste: 'refus' | 'accepte' | 'annuler_compromis' | 'supprimer_compromis' | 'supprimer_vente') => Promise<void>
  handleChangeHektorAnnonceStatus: (event: FormEvent<HTMLFormElement>, reprendre?: boolean) => Promise<void>
  gesteOffreSansEffet: (affaire: AffaireLedgerRow | null | undefined, geste: 'refus' | 'accepte') => boolean
  offreARegulariser: (lignes: AffaireLedgerRow[], affaire: AffaireLedgerRow | null | undefined) => boolean
  compromisDeLaRegularisation: (lignes: AffaireLedgerRow[], affaire: AffaireLedgerRow | null | undefined) => AffaireLedgerRow | null
  dateOffreFaite: (a: AffaireLedgerRow) => string
  modifierChezHektorPossible: (statut: string, affaire: AffaireLedgerRow | null | undefined, lignes: AffaireLedgerRow[]) => boolean
  offreAccepteeFigeeChezHektor: (affaire: AffaireLedgerRow | null | undefined) => boolean
  compromisVerrouilleParSaVente: (lignes: AffaireLedgerRow[], affaire: AffaireLedgerRow | null | undefined) => AffaireLedgerRow | null
  nouvelleOffreFermeeSurBienEngage: (statut: string, lignes: AffaireLedgerRow[]) => boolean
  hektorStatusTargetLabel: (value: HektorAnnonceStatusTarget | string | null | undefined) => string
  SelecteurNotaire: ComponentType<{
    libelle: string; aide: string; nom: string; numero: string; scope: DataScope | null | undefined
    onChoisir: (option: MandantContactSearchOption) => void; onRetirer: () => void
  }>
}

export type ModaleStatutV2Props = {
  statusChangeTarget: Dossier
  statusChangeStatus: HektorAnnonceStatusTarget
  setStatusChangeStatus: (value: HektorAnnonceStatusTarget) => void
  setStatusChangeAffaireChoisie: (value: number | null) => void
  statusChangeAffaires: AffaireLedgerRow[]
  statusChangePending: boolean
  closeStatusChangeModal: () => void
  /** les libellés et descriptions des 5 statuts, ceux de l'ancienne modale (hektorStatusTargetOptions) */
  options: Array<{ value: HektorAnnonceStatusTarget; label: string; description: string }>
  /** les gardes d'App.tsx, passées telles quelles (une seule copie de chaque règle) */
  gardes: GardesParcours
  isValidationApproved: (value: string | null | undefined) => boolean
  /** la pastille de statut de l'ancienne modale (StatusPill), déjà rendue */
  pastilleStatut: ReactNode
  formulaire: FormulaireStatutProps
}

const ETIQUETTE: Record<string, string> = { conseille: 'Conseillé', actuel: 'Actuel', hors: 'Hors parcours' }

function aujourdhuiLocal(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function jourFr(iso: string | null | undefined): string {
  const t = String(iso ?? '').trim().slice(0, 10)
  return /^\d{4}-\d{2}-\d{2}$/.test(t) && !t.startsWith('0000') ? t.split('-').reverse().join('/') : ''
}

function IcoGuide() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3a6 6 0 0 0-3.5 10.9V17h7v-3.1A6 6 0 0 0 12 3z" /><path d="M9.5 20.5h5" />
    </svg>
  )
}

// ─── Les pastilles « Actuel / Repris / Modifié / À remplir » (lot 2) ───
// ⚠ ELLES DÉCRIVENT, ELLES NE DÉCIDENT RIEN. « Modifié » lit statusChangeTouches (point E du 23/10 : ce que
//   l'utilisateur a vraiment changé, et seulement cela part au carnet) ; « À remplir » suit les `required` de
//   l'ancien bloc ; une source n'est nommée QUE si la valeur du champ lui est ÉGALE — jamais deviné.
type Pastille = { texte: string; ton: 'modif' | 'manque' | 'actuel' | 'repris' }
const nombreSaisi = (v: unknown): number | null => {
  const t = String(v ?? '').replace(/\s/g, '').replace(',', '.').trim()
  if (!t) return null
  const n = Number(t)
  return Number.isFinite(n) ? n : null
}
const memeValeur = (a: unknown, b: unknown): boolean => {
  const x = nombreSaisi(a), y = nombreSaisi(b)
  if (x !== null && y !== null) return Math.abs(x - y) < 0.005
  const s = String(a ?? '').trim()
  return s !== '' && s === String(b ?? '').trim().slice(0, s.length === 10 ? 10 : undefined)
}

function Champ(props: { libelle: string; requis?: boolean; pastille?: Pastille | null; aide?: ReactNode; large?: boolean; children: ReactNode }) {
  return (
    <label className={`stv2-champ${props.large ? ' is-large' : ''}`}>
      <span className="stv2-lab">
        {props.libelle}
        {props.requis ? <span className="stv2-req" aria-hidden="true">*</span> : null}
        {props.pastille ? <span className={`stv2-bdg stv2-bdg-${props.pastille.ton}`}>{props.pastille.texte}</span> : null}
      </span>
      {props.children}
      {props.aide ? <small className="stv2-aide">{props.aide}</small> : null}
    </label>
  )
}

function Section(props: { titre: string; dest?: 'hektor' | 'nous' | 'mixte'; compte?: number; children: ReactNode; pied?: ReactNode }) {
  return (
    <section className="stv2-sec">
      <div className="stv2-sech">
        <h4>{props.titre}</h4>
        {props.compte != null ? <span className="stv2-compte">{props.compte}</span> : null}
        {props.dest === 'hektor' ? <span className="stv2-dest stv2-dest-h">envoyé à Hektor</span> : null}
        {props.dest === 'nous' ? <span className="stv2-dest stv2-dest-n">gardé chez nous</span> : null}
      </div>
      <div className="stv2-secb">{props.children}</div>
      {props.pied}
    </section>
  )
}

/** Le formulaire offre / compromis / vente. ⛔ Chaque `onChange` reprend MOT POUR MOT celui de l'ancien bloc
 *  (mêmes setters, même ordre) : seuls la mise en page, les libellés et les pastilles changent. */
function FormulaireTransaction(props: {
  f: FormulaireStatutProps
  statusChangeTarget: Dossier
  statusChangeStatus: HektorAnnonceStatusTarget
  statusChangeAffaires: AffaireLedgerRow[]
  statusChangePending: boolean
}) {
  const { statusChangeTarget, statusChangeStatus, statusChangeAffaires, statusChangePending } = props
  const {
    statusChangeAmount, setStatusChangeAmount, statusChangeSalePrice, setStatusChangeSalePrice,
    statusChangeDate, setStatusChangeDate, statusChangeValidityDays, setStatusChangeValidityDays,
    statusChangeSignatureDate, setStatusChangeSignatureDate, statusChangeRetractionDays, setStatusChangeRetractionDays,
    statusChangePrixVenteManuel, setStatusChangePrixVenteManuel,
    statusChangeBuyers, statusChangeBuyerSearch, setStatusChangeBuyerSearch, statusChangeBuyerOptions,
    statusChangeBuyerLoading, statusChangeBuyerError, statusChangeSellerNotaryId, setStatusChangeSellerNotaryId,
    statusChangeSellerNotaryNom, setStatusChangeSellerNotaryNom, statusChangeBuyerNotaryId, setStatusChangeBuyerNotaryId,
    statusChangeBuyerNotaryNom, setStatusChangeBuyerNotaryNom, setStatusChangeNotairesAffirmes,
    statusChangeBuyerFees, setStatusChangeBuyerFees, statusChangeBuyerFeesRate, setStatusChangeBuyerFeesRate,
    statusChangeHonorairesEntree, setStatusChangeHonorairesEntree, setStatusChangeHonorairesEntreeTouche,
    setStatusChangeCommissionTouchee, statusChangeChargeCommission, setStatusChangeChargeCommission,
    statusChangeNetSellerPrice, setStatusChangeNetSellerPrice, statusChangeNetManuel, setStatusChangeNetManuel,
    statusChangeSequestration, setStatusChangeSequestration, statusChangeConditions, conditionCatalogue,
    statusChangeNote, setStatusChangeNote, statusChangeTouches, repartitionCases, repartitionPersonnes, repartitionTotal,
    ecartPrixTransaction, dataScope, toucherStatusChange, apresSaisieCommission, ajouterAcquereurStatut,
    retirerAcquereurStatut, ajouterCondition, modifierCondition, retirerCondition, echeanceCondition, repartitionLigne,
    repartitionRangs, repartitionPoser, repartitionPourcentage, repartitionAjouterCase, repartitionRetirerCase,
    statusChangeNeedsSalePrice, mandantContactOptionTitle, mandantContactOptionSubtitle, formatDate, formatPrice,
    affaireCourante, offreAccepteeAReprendreAuCompromis, affaireEstVivante, SelecteurNotaire,
    offreVerrouilleeParSonDossier, rattachementOffreProposee,
  } = props.f
  // Seul état de la vue : la répartition repliée ou dépliée.
  const [repartitionOuverte, setRepartitionOuverte] = useState(false)

  // Les sources possibles d'une valeur, pour les pastilles (lecture seulement).
  const aujourdhui = aujourdhuiLocal()
  const offreReprise = statusChangeStatus === 'compromise' && !affaireCourante
    ? offreAccepteeAReprendreAuCompromis(statusChangeAffaires) : null
  const compromisVivants = statusChangeStatus === 'sold' && !affaireCourante
    ? statusChangeAffaires.filter((a) => String(a.kind) === 'compromis' && affaireEstVivante(a)) : []
  const compromisRepris = compromisVivants.length === 1 ? compromisVivants[0] : null
  // ─── LOT 3 : L'OFFRE VERROUILLÉE PAR SON DOSSIER (règle du 16/09) ───
  // Son dossier porte un compromis ou une vente : la base refuse de la modifier. Ses champs passent en LECTURE
  // SEULE (`readOnly` : la valeur reste la même, rien de ce qui part ne change) et la section dit pourquoi, avec
  // les mots de l'ancien bandeau.
  const verrou = statusChangeStatus === 'offer' ? offreVerrouilleeParSonDossier(statusChangeAffaires, affaireCourante) : null
  const rattachee = verrou && affaireCourante ? rattachementOffreProposee(statusChangeAffaires, affaireCourante) : null
  const pastille = (cle: string, valeur: string, sources: Array<[string, unknown]>, requis = false): Pastille | null => {
    if (verrou) return { texte: 'Figée', ton: 'actuel' }
    if (statusChangeTouches.includes(cle)) return { texte: 'Modifié', ton: 'modif' }
    if (requis && !String(valeur ?? '').trim()) return { texte: 'À remplir', ton: 'manque' }
    for (const [texte, source] of sources) {
      if (source != null && memeValeur(valeur, source)) return { texte, ton: texte === 'Actuel' ? 'actuel' : 'repris' }
    }
    return null
  }
  const sourcesPrix: Array<[string, unknown]> = [
    ['Actuel', affaireCourante?.montant], ['Repris de l’offre', offreReprise?.montant],
    ['Repris du compromis', compromisRepris?.montant], ['Prix du bien', statusChangeTarget.prix],
  ]
  const genre = statusChangeStatus === 'offer' ? 'L’offre' : statusChangeStatus === 'compromise' ? 'Le compromis' : 'La vente'
  const titreAffaire = affaireCourante ? `${genre} en cours` : statusChangeStatus === 'offer' ? 'L’offre à enregistrer'
    : statusChangeStatus === 'compromise' ? 'Le compromis à enregistrer' : 'La vente à enregistrer'
  const nomRepartition = (l: RepartitionLigne) =>
    repartitionPersonnes.find((p) => p.idUser === l.hektorUserId)?.nom || (l.nomAuMoment ?? '').trim() || `Utilisateur ${l.hektorUserId}`
  const resumeRepartition = (cote: Cote) => repartitionRangs(cote)
    .map((rang) => repartitionLigne(cote, rang))
    .filter((l): l is RepartitionLigne => Boolean(l && l.hektorUserId.trim()))
    .map((l) => `${nomRepartition(l)} ${String(l.pourcentage).replace('.', ',')} %`)
  const totalAffiche = repartitionTotal.toFixed(3).replace(/0+$/, '').replace(/\.$/, '').replace('.', ',')

  return (
    <div className="stv2-form">
      <Section titre={verrou ? 'L’offre, en lecture seule' : titreAffaire} dest="hektor"
        pied={verrou ? (
          <p className="stv2-note is-alerte stv2-sec-pied" role="status">
            <strong>On ne revient plus sur cette offre.</strong>{' '}
            Son dossier porte {String(verrou.kind) === 'vente' ? 'une vente' : 'un compromis en cours'}
            {String(verrou.hektor_affaire_id ?? '').trim() ? ` (n° ${String(verrou.hektor_affaire_id ?? '').trim()})` : ''}.
            La refuser ou l’accepter maintenant couperait l’affaire en deux dans le registre. Pour y revenir, il faut
            d’abord {String(verrou.kind) === 'vente' ? 'supprimer la vente' : 'annuler le compromis'}.
            {rattachee?.quand === 'fait'
              ? ' Elle est restée « proposée », ce qui est fréquent : elle est bien rattachée à ce compromis.'
              : ''}
          </p>
        ) : null}>
        <div className="stv2-grille">
          {/* ⚠ Pas de « montant » sur la vente : chez Hektor une vente n'a pas de prix public (14/09). */}
          {statusChangeStatus !== 'sold' ? (
            <Champ libelle={statusChangeStatus === 'offer' ? 'Montant de l’offre' : 'Montant (prix public)'} requis
              pastille={pastille('amount', statusChangeAmount, sourcesPrix, true)}>
              <span className="stv2-in"><input value={statusChangeAmount} onChange={(event) => {
                setStatusChangeAmount(event.target.value); toucherStatusChange('amount')
                apresSaisieCommission({ montant: event.target.value })
                if (statusChangeStatus === 'compromise' && !statusChangePrixVenteManuel) {
                  setStatusChangeSalePrice(event.target.value); toucherStatusChange('sale_price')
                }
              }} inputMode="numeric" placeholder="Ex : 180000" required readOnly={Boolean(verrou)} /><span className="stv2-u">€</span></span>
            </Champ>
          ) : null}
          <Champ libelle="Prix de vente" requis={statusChangeNeedsSalePrice(statusChangeStatus)}
            pastille={pastille('sale_price', statusChangeSalePrice, sourcesPrix, statusChangeNeedsSalePrice(statusChangeStatus))}
            aide={(statusChangeStatus === 'compromise' || statusChangeStatus === 'sold') && statusChangeTarget?.prix != null && String(statusChangeTarget.prix).trim() !== ''
              ? `Prix du mandat : ${formatPrice(statusChangeTarget.prix)}` : statusChangeStatus === 'offer' ? 'Facultatif à l’offre' : null}>
            <span className="stv2-in"><input value={statusChangeSalePrice} onChange={(event) => {
              setStatusChangeSalePrice(event.target.value); toucherStatusChange('sale_price')
              if (statusChangeStatus === 'sold') apresSaisieCommission({ montant: event.target.value })
              // Vider la case rend le prix de vente au montant.
              setStatusChangePrixVenteManuel(event.target.value.trim() !== '')
            }} inputMode="numeric" placeholder="Ex : 180000" required={statusChangeNeedsSalePrice(statusChangeStatus)} readOnly={Boolean(verrou)} /><span className="stv2-u">€</span></span>
          </Champ>
          <Champ libelle={statusChangeStatus === 'sold' ? 'Date de l’acte' : statusChangeStatus === 'compromise' ? 'Date du compromis' : 'Date de l’offre'} requis
            pastille={pastille('transaction_date', statusChangeDate, [['Actuel', affaireCourante?.date], ['Aujourd’hui', aujourdhui]], true)}>
            <span className="stv2-in"><input type="date" value={statusChangeDate} onChange={(event) => { setStatusChangeDate(event.target.value); toucherStatusChange('transaction_date') }} required readOnly={Boolean(verrou)} /></span>
          </Champ>
          {statusChangeStatus === 'offer' ? (
            <Champ libelle="Validité de l’offre" pastille={pastille('validity_days', statusChangeValidityDays, [['Par défaut', '10']])}>
              <span className="stv2-in"><input value={statusChangeValidityDays} onChange={(event) => { setStatusChangeValidityDays(event.target.value); toucherStatusChange('validity_days') }} inputMode="numeric" placeholder="10" readOnly={Boolean(verrou)} /><span className="stv2-u">jours</span></span>
            </Champ>
          ) : null}
          {statusChangeStatus === 'compromise' ? (
            <>
              <Champ libelle="Date d’acte prévue" pastille={pastille('signature_date', statusChangeSignatureDate, [['Actuel', affaireCourante?.date_acte]])}>
                <span className="stv2-in"><input type="date" value={statusChangeSignatureDate} onChange={(event) => { setStatusChangeSignatureDate(event.target.value); toucherStatusChange('signature_date') }} /></span>
              </Champ>
              <Champ libelle="Rétractation" pastille={pastille('retraction_days', statusChangeRetractionDays, [['Par défaut', '10']])}>
                <span className="stv2-in"><input value={statusChangeRetractionDays} onChange={(event) => { setStatusChangeRetractionDays(event.target.value); toucherStatusChange('retraction_days') }} inputMode="numeric" placeholder="10" /><span className="stv2-u">jours</span></span>
              </Champ>
            </>
          ) : null}
          {/* 06/11 (décision de Frédéric, audit AUDIT_CHAMPS_VENDEURS_ET_MANDAT_MODALE_STATUT_2026-11-06.md) : plus de
              « N° de mandat ». Ignoré au compromis et à la vente ; à l'offre, prérempli d'un numéro seul, il passait
              DEVANT la valeur de Hektor (« 553-PROTEXA ») et l'offre partait sans mandat. La modale ne l'envoie plus. */}
        </div>
      </Section>

      <Section titre="Les personnes" dest="hektor">
        <div className="stv2-personnes">
          {/* L'acquéreur : la même mécanique que l'ancien bloc (2.5 + 2.6) — le PREMIER reste buyer_contact_id. */}
          <div className="filter-field status-change-acq">
            <span>Acquéreur{statusChangeBuyers.length > 1 ? 's' : ''}</span>
            {statusChangeBuyers.length ? (
              <div className="sca-acq-choisis">
                {statusChangeBuyers.map((option, rang) => {
                  const id = String(option.hektor_contact_id ?? '').trim()
                  // Hektor n'accepte qu'un contact déjà « acquéreur » (18/09) : seulement pour le compromis et la vente.
                  const typologies = Array.isArray(option.typologies_json)
                    ? option.typologies_json
                    : (() => { try { return JSON.parse(String(option.typologies_json ?? '[]')) } catch { return [] } })()
                  const typologieConnue = option.typologies_json != null && Array.isArray(typologies) && typologies.length > 0
                  const aQualifier = (statusChangeStatus === 'compromise' || statusChangeStatus === 'sold')
                    && typologieConnue
                    && !typologies.some((t: unknown) => /acqu/i.test(String(t ?? '')))
                  return (
                    <span className={`sca-acq-jeton${aQualifier ? ' is-a-qualifier' : ''}`} key={`acq-${id}`}
                      title={aQualifier ? bvs("Pas encore acquéreur chez Hektor : il sera qualifié automatiquement à l'envoi (recherche créée puis archivée)") : undefined}>
                      <b>{mandantContactOptionTitle(option)}</b>
                      {aQualifier ? <i className="sca-acq-qualif">sera qualifié</i> : null}
                      {rang === 0 && statusChangeBuyers.length > 1
                        ? <i title={bvs("C'est lui que Hektor recevra en premier")}>principal</i> : null}
                      <button type="button" aria-label={`Retirer ${mandantContactOptionTitle(option)}`}
                        onClick={() => retirerAcquereurStatut(id)}>×</button>
                    </span>
                  )
                })}
              </div>
            ) : null}
            {(statusChangeStatus === 'compromise' || statusChangeStatus === 'sold') && statusChangeBuyers.some((option) => {
              const t = Array.isArray(option.typologies_json) ? option.typologies_json
                : (() => { try { return JSON.parse(String(option.typologies_json ?? '[]')) } catch { return [] } })()
              return option.typologies_json != null && Array.isArray(t) && t.length > 0
                && !t.some((x: unknown) => /acqu/i.test(String(x ?? '')))
            }) ? (
              <small className="sca-acq-etat">
                {bvs("Hektor n'accepte comme acquéreur qu'un contact déjà qualifié. Ceux marqués « sera qualifié » le seront automatiquement à l'envoi : une recherche est créée, la transaction est enregistrée, puis la recherche est archivée.")}
              </small>
            ) : null}
            <input
              value={statusChangeBuyerSearch}
              onChange={(event) => setStatusChangeBuyerSearch(event.target.value)}
              placeholder={statusChangeBuyers.length ? 'Ajouter un acquéreur…' : 'Nom, email, téléphone…'} />
            {statusChangeBuyerLoading ? <small className="sca-acq-etat">Recherche…</small> : null}
            {statusChangeBuyerError ? <small className="sca-acq-err">{statusChangeBuyerError}</small> : null}
            {statusChangeBuyerOptions.length ? (
              <div className="sca-acq-liste">
                {statusChangeBuyerOptions.map((option) => (
                  <button type="button" key={`acq-opt-${option.hektor_contact_id}`}
                    onClick={() => ajouterAcquereurStatut(option)}>
                    <b>{mandantContactOptionTitle(option)}</b>
                    <small>{mandantContactOptionSubtitle(option)}</small>
                  </button>
                ))}
              </div>
            ) : statusChangeBuyerSearch.trim().length > 0
                && statusChangeBuyerSearch.trim().length < (/^\d+$/.test(statusChangeBuyerSearch.trim()) ? 1 : 3)
              ? <small className="sca-acq-etat">Trois lettres suffisent, ou un numéro de contact.</small>
              : statusChangeBuyerSearch.trim().length >= 3 && !statusChangeBuyerLoading
                ? <small className="sca-acq-etat">Aucun contact trouvé dans ton périmètre.</small>
                : null}
          </div>
          {/* 06/11 (même décision) : plus de champ « Vendeurs ». Hektor les pose seul à partir du mandat (699/699
              compromis, 640/642 ventes depuis 2025) ; sans geste, la liste ne partait jamais — 9 usages, tous sur des
              biens d'essai. Le retirer ne change rien à ce qui part. */}
          <div className="stv2-notaires">
            <SelecteurNotaire
              libelle="Notaire des vendeurs"
              aide="Nom du notaire, ou son numéro…"
              nom={statusChangeSellerNotaryNom}
              numero={statusChangeSellerNotaryId}
              scope={dataScope}
              onChoisir={(option) => {
                setStatusChangeSellerNotaryId(String(option.hektor_contact_id ?? '').trim())
                setStatusChangeSellerNotaryNom(mandantContactOptionTitle(option))
                setStatusChangeNotairesAffirmes((etat) => ({ ...etat, mandant: true }))
                toucherStatusChange('seller_notary_id')
              }}
              onRetirer={() => {
                // Retirer n'efface pas chez Hektor : on cesse seulement de l'envoyer (voir l'ancien bloc).
                setStatusChangeSellerNotaryId('')
                setStatusChangeSellerNotaryNom('')
                setStatusChangeNotairesAffirmes((etat) => ({ ...etat, mandant: false }))
                toucherStatusChange('seller_notary_id')
              }} />
            <SelecteurNotaire
              libelle="Notaire de l’acquéreur"
              aide="Nom du notaire, ou son numéro…"
              nom={statusChangeBuyerNotaryNom}
              numero={statusChangeBuyerNotaryId}
              scope={dataScope}
              onChoisir={(option) => {
                setStatusChangeBuyerNotaryId(String(option.hektor_contact_id ?? '').trim())
                setStatusChangeBuyerNotaryNom(mandantContactOptionTitle(option))
                setStatusChangeNotairesAffirmes((etat) => ({ ...etat, acquereur: true })); toucherStatusChange('buyer_notary_id')
              }}
              onRetirer={() => {
                setStatusChangeBuyerNotaryId('')
                setStatusChangeBuyerNotaryNom('')
                setStatusChangeNotairesAffirmes((etat) => ({ ...etat, acquereur: false })); toucherStatusChange('buyer_notary_id')
              }} />
          </div>
        </div>
      </Section>

      <Section titre="Honoraires et commission" dest="mixte"
        pied={ecartPrixTransaction ? (
          <p className="stv2-note is-alerte stv2-sec-pied" role="status">
            Le compte n’y est pas : {ecartPrixTransaction.net.toLocaleString('fr-FR')} net
            {' + '}{ecartPrixTransaction.entree.toLocaleString('fr-FR')} d’honoraires vendeur
            {ecartPrixTransaction.sortie ? ` + ${ecartPrixTransaction.sortie.toLocaleString('fr-FR')} acquéreur` : ''}
            {' = '}{ecartPrixTransaction.attendu.toLocaleString('fr-FR')}, et non
            {' '}{ecartPrixTransaction.prix.toLocaleString('fr-FR')}
            {' '}(écart de {Math.abs(ecartPrixTransaction.ecart).toLocaleString('fr-FR')} €).
            {' '}{bvs("Vous pouvez envoyer quand meme — Hektor recalculera le net vendeur.")}
          </p>
        ) : null}>
        <div className="stv2-grille">
          <Champ libelle="Honoraires acquéreur (TTC)" pastille={pastille('buyer_fees', statusChangeBuyerFees, [])}>
            <span className="stv2-in"><input value={statusChangeBuyerFees} onChange={(event) => {
              setStatusChangeBuyerFees(event.target.value); toucherStatusChange('buyer_fees')
              apresSaisieCommission({ sortie: event.target.value })
            }} inputMode="numeric" placeholder="0" /><span className="stv2-u">€</span></span>
          </Champ>
          <Champ libelle="Taux d’honoraires" pastille={pastille('buyer_fees_rate', statusChangeBuyerFeesRate, [])}>
            <span className="stv2-in"><input value={statusChangeBuyerFeesRate} onChange={(event) => { setStatusChangeBuyerFeesRate(event.target.value); toucherStatusChange('buyer_fees_rate') }} inputMode="decimal" placeholder="0" /><span className="stv2-u">%</span></span>
          </Champ>
          {/* L'offre : Hektor ne garde aucun honoraire, la valeur va dans NOTRE colonne (lot 1c, 16/10). */}
          {statusChangeStatus === 'offer' ? (
            <Champ libelle="Honoraires vendeur (agence, TTC)" pastille={pastille('seller_fees', statusChangeHonorairesEntree, [])}
              aide={<span className="stv2-dest stv2-dest-n">gardé chez nous</span>}>
              <span className="stv2-in"><input value={statusChangeHonorairesEntree} onChange={(event) => {
                setStatusChangeHonorairesEntree(event.target.value); toucherStatusChange('seller_fees')
                setStatusChangeHonorairesEntreeTouche(true)
                setStatusChangeCommissionTouchee(true)
              }} inputMode="numeric" placeholder="0" /><span className="stv2-u">€</span></span>
            </Champ>
          ) : null}
          {statusChangeStatus === 'compromise' ? (
            <>
              <Champ libelle="Prix net vendeur" pastille={pastille('net_seller_price', statusChangeNetSellerPrice, [])}
                aide={statusChangeNetManuel
                  ? 'Saisi à la main : il ne suit plus les commissions.'
                  : 'Montant − commission vendeur − honoraires acquéreur.'}>
                <span className="stv2-in"><input value={statusChangeNetSellerPrice} onChange={(event) => {
                  setStatusChangeNetSellerPrice(event.target.value); toucherStatusChange('net_seller_price')
                  // Vider la case rend la main au calcul.
                  setStatusChangeNetManuel(event.target.value.trim() !== '')
                }} inputMode="numeric" placeholder="Calculé si vide" /><span className="stv2-u">€</span></span>
              </Champ>
              <Champ libelle="Honoraires vendeur (agence, TTC)" pastille={pastille('seller_fees', statusChangeHonorairesEntree, [])}>
                <span className="stv2-in"><input value={statusChangeHonorairesEntree} onChange={(event) => {
                  setStatusChangeHonorairesEntree(event.target.value); toucherStatusChange('seller_fees')
                  setStatusChangeHonorairesEntreeTouche(true)
                  apresSaisieCommission({ entree: event.target.value })
                }} inputMode="numeric" placeholder="Celle du mandat si vide" /><span className="stv2-u">€</span></span>
              </Champ>
              <Champ libelle="Séquestre" pastille={pastille('sequestration', statusChangeSequestration, [['Actuel', affaireCourante?.sequestre]])}>
                <span className="stv2-in"><input value={statusChangeSequestration} onChange={(event) => { setStatusChangeSequestration(event.target.value); toucherStatusChange('sequestration') }} inputMode="numeric" placeholder="0" /><span className="stv2-u">€</span></span>
              </Champ>
            </>
          ) : null}
          {statusChangeStatus === 'sold' ? (
            <Champ libelle="Honoraires vendeur (agence, TTC)" pastille={pastille('seller_fees', statusChangeHonorairesEntree, [])}>
              <span className="stv2-in"><input value={statusChangeHonorairesEntree} onChange={(event) => {
                setStatusChangeHonorairesEntree(event.target.value); toucherStatusChange('seller_fees')
                setStatusChangeHonorairesEntreeTouche(true)
                apresSaisieCommission({ entree: event.target.value })
              }} inputMode="numeric" placeholder="Celle du mandat si vide" /><span className="stv2-u">€</span></span>
            </Champ>
          ) : null}
        </div>
        {/* Qui paie : la même valeur que le menu de l'ancien bloc ('vendeur' | 'acquereur'). ⚠ Un clic sur le choix
            DÉJÀ posé ne fait rien — comme un menu dont la valeur ne change pas (sinon « touchée » à tort). */}
        <div className="stv2-ligne">
          <span className="stv2-lab">Qui paie la commission ?</span>
          <div className="stv2-seg" role="group" aria-label="Charge de la commission">
            {([['vendeur', 'Les vendeurs'], ['acquereur', 'L’acquéreur']] as const).map(([valeur, libelle]) => (
              <button key={valeur} type="button" aria-pressed={statusChangeChargeCommission === valeur} onClick={() => {
                if (statusChangeChargeCommission === valeur) return
                setStatusChangeChargeCommission(valeur)
                setStatusChangeCommissionTouchee(true)
              }}>{libelle}</button>
            ))}
          </div>
          <span className="stv2-dest stv2-dest-n">gardé chez nous</span>
        </div>
      </Section>

      {/* La répartition : REPLIÉE par défaut, et l'éditeur complet de l'ancien bloc se déplie (plan §3, lot 2). */}
      <Section titre="Répartition de la commission" dest="nous"
        pied={repartitionTotal > 100.001 || (repartitionTotal > 0 && repartitionTotal < 100 - 0.01) ? (
          <p className="stv2-note is-alerte stv2-sec-pied" role="status">
            Les parts font {repartitionTotal.toFixed(3).replace(/0+$/, '').replace(/\.$/, '')} %.
            {repartitionTotal < 100
              ? ` Il reste ${(100 - repartitionTotal).toFixed(2)} % attribue a personne.`
              : " Au-dessus de 100 %, l'enregistrement sera refuse."}
          </p>
        ) : null}>
        <div className="stv2-ligne">
          <span className="stv2-jauge" aria-hidden="true"><span style={{ width: `${Math.min(100, Math.max(0, repartitionTotal))}%` }} /></span>
          <span className="stv2-resume">
            <b>Entrée</b> {resumeRepartition('entree').join(', ') || 'personne'} · <b>Sortie</b> {resumeRepartition('sortie').join(', ') || 'personne'}
            {repartitionTotal > 0 ? ` · ${totalAffiche} %` : ''}
          </span>
          <button type="button" className="stv2-lnk" aria-expanded={repartitionOuverte} onClick={() => setRepartitionOuverte((o) => !o)}>
            {repartitionOuverte ? 'Replier' : 'Modifier'}
          </button>
        </div>
        {repartitionOuverte ? (
          <div className="stv2-repartition">
            {(['entree', 'sortie'] as const).map((cote) => (
              <div className="stv2-rep-cote" key={cote}>
                {repartitionRangs(cote).map((rang) => {
                  const ligne = repartitionLigne(cote, rang)
                  return (
                    <label className="stv2-champ" key={`${cote}-${rang}`}>
                      <span className="stv2-lab">
                        {cote === 'entree' ? 'Entrée' : 'Sortie'}
                        {repartitionCases[cote] > 1 ? ` ${rang}` : ''}
                        {rang === 1 && ligne?.origine === 'defaut' ? <span className="stv2-bdg stv2-bdg-repris">Proposé</span> : null}
                      </span>
                      <span className="stv2-rep-ligne">
                        <span className="stv2-in"><select
                          value={ligne?.hektorUserId ?? ''}
                          onChange={(event) => repartitionPoser(cote, rang, event.target.value)}
                          disabled={statusChangePending}>
                          <option value="">—</option>
                          {/* Un ancien reste LISIBLE sans être choisissable (Frédéric, 01/11). */}
                          {ligne && ligne.hektorUserId.trim()
                            && !repartitionPersonnes.some((p) => p.idUser === ligne.hektorUserId) ? (
                            <option value={ligne.hektorUserId} disabled>
                              {(ligne.nomAuMoment ?? '').trim() || `Utilisateur ${ligne.hektorUserId}`} · ancien
                            </option>
                          ) : null}
                          {repartitionPersonnes.map((p) => (
                            <option key={p.idUser} value={p.idUser}>
                              {p.nom}{p.agenceNom ? ` · ${p.agenceNom}` : ''}
                            </option>
                          ))}
                        </select></span>
                        {ligne ? (
                          <span className="stv2-in stv2-in-pct"><input
                            value={String(ligne.pourcentage)}
                            onChange={(event) => repartitionPourcentage(cote, rang, event.target.value)}
                            inputMode="decimal"
                            aria-label={`Part ${cote} ${rang} en pour cent`}
                            placeholder="%" /><span className="stv2-u">%</span></span>
                        ) : null}
                      </span>
                    </label>
                  )
                })}
                {repartitionCases[cote] < 3 || repartitionCases[cote] > 1 ? (
                  <div className="stv2-rep-ajout">
                    {repartitionCases[cote] < 3 ? (
                      <button type="button" className="stv2-lnk"
                              onClick={() => repartitionAjouterCase(cote)}
                              disabled={statusChangePending}>
                        + un intervenant {cote === 'entree' ? 'à l’entrée' : 'en sortie'}
                      </button>
                    ) : null}
                    {repartitionCases[cote] > 1 && !repartitionLigne(cote, repartitionCases[cote] as 1 | 2 | 3) ? (
                      <button type="button" className="stv2-lnk"
                              onClick={() => repartitionRetirerCase(cote)}
                              disabled={statusChangePending}>
                        − retirer la case vide
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}
      </Section>

      {statusChangeStatus === 'compromise' ? (
        <Section titre="Conditions suspensives" dest="nous">
          {statusChangeConditions.map((condition, rang) => {
            const echeance = echeanceCondition(condition)
            return (
              <div className="stv2-cond" key={`cond-${rang}`}>
                <Champ libelle={`Condition ${rang + 1}`}>
                  <span className="stv2-in"><input
                    value={condition.libelle}
                    onChange={(event) => modifierCondition(rang, 'libelle', event.target.value)}
                    placeholder="Obtention du prêt, préemption…" /></span>
                </Champ>
                <Champ libelle="Délai" aide={echeance ? `Échéance ${formatDate(echeance)}` : null}>
                  <span className="stv2-in"><input
                    value={condition.jours == null ? '' : String(condition.jours)}
                    onChange={(event) => modifierCondition(rang, 'jours', event.target.value)}
                    inputMode="numeric"
                    placeholder="45" /><span className="stv2-u">jours</span></span>
                </Champ>
                <Champ libelle="État">
                  <span className="stv2-in"><select
                    value={condition.etat ?? 'attente'}
                    onChange={(event) => modifierCondition(rang, 'etat', event.target.value)}>
                    <option value="attente">En attente</option>
                    <option value="levee">Levée</option>
                    <option value="non_levee">Non levée</option>
                    <option value="sans_objet">Sans objet</option>
                  </select></span>
                </Champ>
                <button type="button" className="stv2-lnk stv2-cond-retirer" onClick={() => retirerCondition(rang)}>Retirer</button>
              </div>
            )
          })}
          <div className="stv2-ligne">
            <span className="stv2-in stv2-in-auto"><select
              value=""
              aria-label="Ajouter une condition du catalogue"
              onChange={(event) => {
                const choix = conditionCatalogue.find((c) => c.id === event.target.value)
                if (choix) ajouterCondition(choix)
              }}>
              <option value="">Ajouter depuis le catalogue…</option>
              {conditionCatalogue.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.libelle}{c.jours_defaut ? ` · ${c.jours_defaut} j` : ''}
                </option>
              ))}
            </select></span>
            <button type="button" className="stv2-lnk" onClick={() => ajouterCondition(null)}>+ Condition libre</button>
          </div>
          {statusChangeConditions.length >= 30 ? (
            <p className="stv2-note is-alerte">Trente conditions au maximum : la base n’en accepte pas davantage.</p>
          ) : null}
        </Section>
      ) : null}

      <Section titre="Note pour l’équipe" dest="nous">
        <textarea
          className="stv2-zone"
          aria-label="Note libre"
          value={statusChangeNote}
          maxLength={4000}
          rows={3}
          onChange={(event) => setStatusChangeNote(event.target.value)}
          placeholder="Relancer la banque avant le 15, dossier incomplet…" />
        <small className="stv2-aide">Elle n’apparaîtra pas sur les documents que Hektor imprime.</small>
      </Section>

      {statusChangeStatus === 'sold' ? (
        <p className="stv2-note">
          Le bien restera dans tes biens avec le statut <strong>Vendu</strong>. Pour le sortir du portefeuille, utilise
          l’archivage depuis la fiche : c’est un geste à part, rare.
        </p>
      ) : null}
    </div>
  )
}

/** Les affaires du bien et leurs bandeaux (lot 4). ⛔ Tout est repris de l'ancien bloc : les mêmes calculs (sur les
 *  mêmes fonctions d'App.tsx, passées), les mêmes conditions d'affichage, les mêmes gestes mot pour mot (« Choisir »,
 *  « J'ai vu, fermer », les gestes admin sur un écart du carnet). Aucune requête nouvelle : statusChangeAffaires est
 *  déjà chargée, et ne filtre rien (c'est ce qui permet de retrouver une affaire née dans l'app). */
function AffairesDuBien(props: {
  f: FormulaireStatutProps
  statusChangeStatus: HektorAnnonceStatusTarget
  statusChangeAffaires: AffaireLedgerRow[]
}) {
  const { statusChangeStatus, statusChangeAffaires } = props
  const {
    affaireCourante, setStatusChangeAffaireChoisie, AFFAIRE_PAR_STATUT, AFFAIRE_ETATS_MORTS, AFFAIRE_GENRE_LABEL,
    affaireEtatLabel, affairesVivantesPourStatut, avisPlusieursAffaires, gardeFouPourStatut, dossiersOuvertsDuBien,
    bienEngage, offreEcarteeSurBienEngage, affaireEstVivante, rattachementOffreProposee, ckPartyName, parseJson,
    carnetAffaires, carnetEtats, carnetEcarts, carnetEcartErreur, setCarnetEcartErreur, setCarnetRelecture, isAdmin,
    gestesEcartCarnet, trancherAffaireCarnetEcart, personnesEcarts, personnesEcartErreur, setPersonnesEcartErreur,
    fermerAffairePersonneEcart, rechargerPersonnesEcarts, HistoriqueOffre, formatDate, formatPrice,
  } = props.f
  if (statusChangeAffaires.length === 0) {
    return (
      <Section titre="Les affaires de ce bien">
        <p className="stv2-note">Aucune affaire lue pour ce bien : ni offre, ni compromis, ni vente.</p>
      </Section>
    )
  }
  const courante = affaireCourante
  const vivantesDuGenre = affairesVivantesPourStatut()
  const ambigu = vivantesDuGenre.length > 1
  const avis = avisPlusieursAffaires(AFFAIRE_PAR_STATUT[statusChangeStatus] ?? '', vivantesDuGenre)
  const garde = gardeFouPourStatut()
  const dossiersClos = new Set(
    dossiersOuvertsDuBien(statusChangeAffaires)
      .filter((d) => !d.ouvert).map((d) => d.chaine))
  const engage = bienEngage(statusChangeAffaires)
  const GENRE = AFFAIRE_GENRE_LABEL
  const etatLabel = affaireEtatLabel
  const mandats = Array.from(new Set(
    statusChangeAffaires
      .map((a) => String(a.numero_mandat ?? '').trim())
      .filter(Boolean),
  ))
  const visibles = personnesEcarts.filter((e) => statusChangeAffaires.some(
    (a) => a.kind === e.kind && String(a.hektor_affaire_id ?? '').trim() === e.hektor_affaire_id))
  const ton = (t: string) => (t === 'normal' ? 'info' : t === 'alerte' ? 'alerte' : 'warn')
  return (
    <Section titre="Les affaires de ce bien" compte={statusChangeAffaires.length}>
      {garde ? (
        <p className={`stv2-bandeau is-${garde.bloque ? 'alerte' : 'info'}`} role={garde.bloque ? 'alert' : 'status'}>
          <b>{garde.titre}</b><span>{garde.detail}</span>
        </p>
      ) : null}
      {avis && !courante ? (
        <p className={`stv2-bandeau is-${ton(avis.ton)}`} role={avis.ton === 'normal' ? 'status' : 'alert'}>
          <b>{avis.titre}</b><span>{avis.detail}</span>
        </p>
      ) : null}
      {engage && (AFFAIRE_PAR_STATUT[statusChangeStatus] ?? '') === 'offre' ? (
        <p className="stv2-bandeau is-info" role="status">
          <b>Ce bien est déjà engagé</b>
          <span>
            Une offre acceptée ou un compromis est en cours : on n’enregistre pas de nouvelle offre, et on ne reprend
            pas une autre offre tant que ce dossier vit — il faudrait d’abord le libérer. Une offre d’un autre acquéreur
            encore en cours peut seulement être refusée (« Choisir »), sauf une offre oubliée, datée d’avant le
            compromis : elle peut alors être acceptée pour s’y rattacher. Les actions ci-dessous visent l’offre en cours.
          </span>
        </p>
      ) : null}
      {courante && !affaireEstVivante(courante) ? (
        <p className="stv2-bandeau is-alerte" role="alert">
          <b>
            Tu reprends {GENRE[courante.kind] ?? courante.kind}
            {' '}{etatLabel(courante.kind, courante.state) ? `« ${etatLabel(courante.kind, courante.state)} »` : ''}
          </b>
          <span>
            {bvs("Hektor l'accepte, et le geste ajoutera une ligne a son historique plutot que d'en corriger une. Mais rouvrir un dossier terminé peut en laisser deux ouverts sur ce bien : un compromis créé ensuite ne saurait plus auquel se rattacher, et partirait seul.")}
          </span>
        </p>
      ) : null}
      {mandats.length >= 2 ? (
        <p className="stv2-bandeau is-info" role="status">
          <b>{mandats.length} mandats différents sur ce bien</b>
          <span>({mandats.join(', ')}). Les affaires les plus anciennes appartiennent à une mise en vente précédente :
            vérifie le numéro avant d’agir.</span>
        </p>
      ) : null}
      {visibles.length ? (
        <div className="stv2-perdues">
          {visibles.map((e) => (
            <p key={e.id} className="stv2-bandeau is-alerte" role="alert">
              <b>
                Hektor n’a pas gardé {e.role === 'mandant' ? 'le mandant' : 'l’acquéreur'}{' '}
                {e.contact_nom || `n° ${e.contact_id}`}
              </b>
              <span>
                Sur {({ offre: "l'offre", compromis: 'le compromis', vente: 'la vente' } as Record<string, string>)[e.kind] ?? e.kind} n° {e.hektor_affaire_id},
                {' '}envoi du {formatDate(e.constate_le)}. Hektor n’a signalé aucune erreur : la personne a simplement
                {' '}disparu de la transaction. Vérifie la fiche chez Hektor, puis renvoie-la ou ferme ce message.
              </span>
              <span>
                <button type="button" className="stv2-mini" onClick={async () => {
                  setPersonnesEcartErreur('')
                  try {
                    await fermerAffairePersonneEcart(e.id)
                    await rechargerPersonnesEcarts()
                  } catch (err) {
                    setPersonnesEcartErreur(err instanceof Error ? err.message : String(err))
                  }
                }}>
                  J'ai vu, fermer
                </button>
              </span>
            </p>
          ))}
          {personnesEcartErreur ? (
            <small className="stv2-erreur">Fermeture impossible : {personnesEcartErreur}</small>
          ) : null}
        </div>
      ) : null}
      <ul className="stv2-affaires">
        {statusChangeAffaires.map((a) => {
          const morte = AFFAIRE_ETATS_MORTS.has(String(a.state ?? '').trim().toLowerCase())
          const visee = courante != null && courante.app_affaire_id === a.app_affaire_id
          // `acquereur_json` est du jsonb : PostgREST le rend déjà désérialisé (voir l'ancien bloc).
          const acqBrut: unknown = a.acquereur_json
          const acq = ckPartyName(
            typeof acqBrut === 'string'
              ? parseJson<CkAffaireParty | null>(acqBrut, null)
              : (acqBrut as CkAffaireParty | null),
          )
          const numero = String(a.hektor_affaire_id ?? '').trim()
          const partie = Boolean(numero) && a.present_in_hektor === false
          // Deux sources, dans l'ordre du contrat d'autorité : le carnet (l'app) prime, puis la colonne du registre.
          const carnet = carnetAffaires.get(Number(a.app_affaire_id)) ?? {}
          const etats = carnetEtats.get(Number(a.app_affaire_id)) ?? {}
          const champ = (cle: string, colonne?: unknown) => {
            const duCarnet = String(carnet[cle] ?? '').trim()
            if (duCarnet) return { v: duCarnet, app: true, cle }
            const duLedger = colonne == null ? '' : String(colonne).trim()
            return { v: duLedger, app: false, cle }
          }
          const notaireAffiche = <T extends { v: string; app: boolean }>(x: T, id: unknown, nom: unknown): T => {
            const n = nom == null ? '' : String(nom).trim()
            return x.app && n && x.v === String(id ?? '').trim() ? { ...x, v: n } : x
          }
          const argent = <T extends { v: string }>(x: T): T =>
            x.v ? { ...x, v: formatPrice(x.v) } : x
          const jour = <T extends { v: string }>(x: T): T =>
            x.v ? { ...x, v: formatDate(x.v) } : x
          const detail: Array<[string, { v: string; app: boolean; cle: string }]> = [
            ['Montant', argent(champ('montant', a.montant))],
            ['Prix public', argent(champ('prix_publique'))],
            ['Prix net vendeur', argent(champ('prix_net_vendeur'))],
            ['Honoraires', argent(champ('honoraires'))],
            ['Taux honoraires', champ('taux_honoraires').v ? { ...champ('taux_honoraires'), v: `${champ('taux_honoraires').v} %` } : champ('taux_honoraires')],
            ['Validité', champ('jours_validite', a.jours_validite).v ? { ...champ('jours_validite', a.jours_validite), v: `${champ('jours_validite', a.jours_validite).v} jours` } : champ('jours_validite', a.jours_validite)],
            ['Rétractation', champ('jours_retractation').v
              ? { ...champ('jours_retractation'), v: `${champ('jours_retractation').v} jours` }
              : a.date_fin_retractation
                ? { v: `jusqu'au ${formatDate(a.date_fin_retractation)}`, app: false, cle: 'jours_retractation' }
                : champ('jours_retractation')],
            ['Séquestre', argent(champ('sequestre', a.sequestre))],
            ['Date', jour(champ('date', a.date))],
            ["Date d'acte", jour(champ('date_acte', a.date_acte))],
            ['Notaire acquéreur', notaireAffiche(champ('notaire_id', a.notaire_acquereur_nom || a.notaire_acquereur_id), a.notaire_acquereur_id, a.notaire_acquereur_nom)],
            ['Notaire vendeur', notaireAffiche(champ('notaire_mandant_id', a.notaire_mandant_nom || a.notaire_mandant_id), a.notaire_mandant_id, a.notaire_mandant_nom)],
            ['N° mandat', (() => {
              const m = champ('numero_mandat', a.numero_mandat)
              const devine = !m.app && m.v
                && String(a.mandat_origine ?? '').startsWith('deduit')
              return devine ? { ...m, v: `${m.v} · déduit` } : m
            })()],
          ]
          // Qui peut-on désigner (règle du 08/09, corrigée le 26/10) : la même expression que l'ancien bloc.
          const choisissable = (() => {
            const genreVise = AFFAIRE_PAR_STATUT[statusChangeStatus] ?? ''
            if (visee || a.kind !== genreVise) return false
            if (genreVise === 'offre') return !engage || offreEcarteeSurBienEngage(statusChangeAffaires, a)
            return ambigu && affaireEstVivante(a)
              && !(a.app_chaine_id != null
                   && dossiersClos.has(String(a.app_chaine_id)))
          })()
          const rattachement = rattachementOffreProposee(statusChangeAffaires, a)
          return (
            <li key={a.app_affaire_id}>
              <details className={`stv2-aff${morte ? ' is-morte' : ''}${visee ? ' is-visee' : ''}`}>
                <summary className="stv2-aff-ligne">
                  <b className="stv2-aff-g">{GENRE[a.kind] ?? a.kind}</b>
                  <span className={`stv2-aff-e${morte ? ' is-morte' : ''}`}>{etatLabel(a.kind, a.state)}</span>
                  <span className="stv2-aff-m">{a.montant != null && String(a.montant).trim() ? formatPrice(a.montant) : '—'}</span>
                  <span className="stv2-aff-d">{a.date ? formatDate(a.date) : '—'}</span>
                  <span className="stv2-aff-a">{acq || '—'}</span>
                  <span className="stv2-aff-t">
                    {a.app_chaine_id != null ? (
                      <i className={dossiersClos.has(String(a.app_chaine_id)) ? 'stv2-tag is-clos' : 'stv2-tag'}>
                        dossier n° {a.app_chaine_id}
                        {dossiersClos.has(String(a.app_chaine_id)) ? ' · terminé' : ''}
                      </i>
                    ) : null}
                    {choisissable ? (
                      <button type="button" className="stv2-mini"
                        onClick={(e) => { e.preventDefault(); e.stopPropagation()
                                          setStatusChangeAffaireChoisie(a.app_affaire_id) }}>
                        Choisir
                      </button>
                    ) : null}
                    {visee ? <b className="stv2-tag is-visee">visée par les actions</b> : null}
                    {partie ? <i className="stv2-tag is-alerte">plus dans Hektor</i> : null}
                    {personnesEcarts.some((e) => e.kind === a.kind && e.hektor_affaire_id === numero)
                      ? <i className="stv2-tag is-alerte">personne non gardée par Hektor</i> : null}
                    {!numero ? <i className="stv2-tag">née dans l’app, sans numéro Hektor</i> : null}
                    {rattachement ? (
                      <i className="stv2-tag">{rattachement.quand === 'fait'
                        ? `rattachée au compromis${rattachement.compromis.date ? ` du ${formatDate(rattachement.compromis.date)}` : ''}`
                        : `sera rattachée cette nuit au compromis${rattachement.compromis.date ? ` du ${formatDate(rattachement.compromis.date)}` : ''}`}</i>
                    ) : null}
                  </span>
                </summary>
                <div className="stv2-aff-corps">
                  <div className="stv2-aff-grille">
                    {detail.map(([k, x]) => {
                      // On ne qualifie QUE ce qui vient du carnet (3.1) ; les mots des états sont ceux de R3 (23/10).
                      const etat = x.app ? String(etats[x.cle] ?? '') : ''
                      const dit = etat === 'conflit' ? 'conflit'
                        : etat === 'en_attente' ? 'pas encore parti'
                        : etat === 'arrivee' ? 'arrivé'
                        : etat === 'echec' ? 'échec, non envoyé'
                        : etat === 'sans_objet' ? 'sans objet' : ''
                      // R4 (26/10) : un champ en écart qui attend la réponse de l'admin porte ses deux gestes.
                      const gestes = isAdmin && x.app
                        && carnetEcarts.get(Number(a.app_affaire_id))?.has(x.cle)
                        ? gestesEcartCarnet(etat) : []
                      return (
                        <div key={k} className={x.app ? 'is-app' : undefined}>
                          <span className="stv2-aff-k">{k}</span>
                          <span className="stv2-aff-v">
                            {x.v || '—'}
                            {dit ? <i className={`stv2-etat is-${etat}`}>{dit}</i> : null}
                            {gestes.map((g) => (
                              <button key={g.decision} type="button" className="stv2-mini" title={g.aide}
                                onClick={async (e) => {
                                  e.preventDefault(); e.stopPropagation()
                                  setCarnetEcartErreur('')
                                  try {
                                    await trancherAffaireCarnetEcart(Number(a.app_affaire_id), x.cle, g.decision)
                                    setCarnetRelecture((n) => n + 1)
                                  } catch (err) {
                                    setCarnetEcartErreur(err instanceof Error ? err.message : String(err))
                                  }
                                }}>
                                {g.libelle}
                              </button>
                            ))}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                  {carnetEcartErreur && carnetEcarts.has(Number(a.app_affaire_id)) ? (
                    <p className="stv2-erreur">Le geste n’est pas passé : {carnetEcartErreur}</p>
                  ) : null}
                  {a.kind === 'offre' ? <HistoriqueOffre propositions={a.propositions_json} /> : null}
                  <div className="stv2-aff-pied">
                    <span>N° app <b>{a.app_affaire_id}</b></span>
                    <span>N° Hektor <b>{numero || '—'}</b></span>
                    <span className="stv2-aff-leg">Les valeurs sur fond vert viennent de ta saisie : elles survivent au run
                      de nuit. <b>Conflit</b> : quelqu’un a changé cette valeur chez Hektor. <b>Pas encore parti</b> :
                      l’envoi n’est pas passé.</span>
                  </div>
                </div>
              </details>
            </li>
          )
        })}
      </ul>
    </Section>
  )
}

// ─── Lot 5 (06/11) — le pied, ses notes, l'aperçu « avant → après » ───
const GENRE_DU_STATUT: Record<string, string> = { offer: 'l’offre', compromise: 'le compromis', sold: 'la vente' }
const LIBELLE_ENVOI: Record<string, string> = {
  active: 'Remettre en vente', offer: 'Enregistrer l’offre', compromise: 'Enregistrer le compromis',
  sold: 'Enregistrer la vente', closed: 'Clore le mandat',
}
/** L'aperçu du bouton principal : TEXTE seulement, et seulement ce que le code fait sûrement (plan §1 et §3). */
const APRES: Record<string, { statut: string; effets: string[] }> = {
  active: { statut: 'Actif', effets: ['La diffusion sur les portails repart.', 'La fiche est relue après l’envoi.'] },
  offer: { statut: 'Sous offre', effets: ['L’offre est enregistrée chez Hektor.', 'Les honoraires vendeur, la répartition et la note restent chez nous.'] },
  compromise: { statut: 'Sous compromis', effets: ['Le compromis est enregistré chez Hektor.', 'Les conditions suspensives, la répartition et la note restent chez nous.'] },
  sold: { statut: 'Vendu', effets: ['Le mandat est clos chez nous à la date de la vente.', 'Le bien reste dans tes biens, au statut Vendu.'] },
  closed: { statut: 'Clos', effets: ['La diffusion sur les portails est coupée.', 'La date et le motif restent chez nous.'] },
}

/** Les notes qui expliquent les boutons (ancien bloc, juste au-dessus du pied) — mêmes conditions, les mots suivent
 *  les nouveaux libellés. L'offre verrouillée par son dossier est dite au lot 3, dans sa section. */
function NotesDesBoutons(props: { f: FormulaireStatutProps; statusChangeTarget: Dossier; statusChangeStatus: HektorAnnonceStatusTarget; statusChangeAffaires: AffaireLedgerRow[]; etatFermeAuxTransactions: GardesParcours['etatFermeAuxTransactions'] }) {
  const { statusChangeTarget, statusChangeStatus, statusChangeAffaires, etatFermeAuxTransactions } = props
  const {
    affaireCourante, modifierChezHektorPossible, compromisDeLaRegularisation, dateOffreFaite, compromisVerrouilleParSaVente,
    offreAccepteeFigeeChezHektor, offreVerrouilleeParSonDossier, statusChangeNeedsTransaction, formatDate,
  } = props.f
  const notes: Array<{ titre: string; texte: string }> = []
  if (modifierChezHektorPossible(statusChangeStatus, affaireCourante, statusChangeAffaires)) {
    notes.push({
      titre: `Ce bien porte déjà ${statusChangeStatus === 'offer' ? 'une offre' : statusChangeStatus === 'compromise' ? 'un compromis' : 'une vente'}.`,
      texte: `« Mettre à jour ${GENRE_DU_STATUT[statusChangeStatus] ?? ''} » reprend celle-là au lieu d’en créer une seconde. Un champ laissé vide n’efface rien : il conserve ce que Hektor porte déjà.`,
    })
  }
  if (statusChangeStatus === 'offer' && affaireCourante) {
    const compromis = compromisDeLaRegularisation(statusChangeAffaires, affaireCourante)
    if (compromis) {
      notes.push({
        titre: 'Régularisation possible.',
        texte: `Cette offre date du ${formatDate(dateOffreFaite(affaireCourante))}, avant le compromis${compromis.date ? ` du ${formatDate(compromis.date)}` : ' en cours'}. Si c’est bien elle qui a mené au compromis, « Accepter l’offre » la rattache à ce compromis (au calcul de la nuit). Si c’est une offre concurrente, refuse-la.`,
      })
    }
  }
  if (statusChangeNeedsTransaction(statusChangeStatus)) {
    const ferme = etatFermeAuxTransactions(statusChangeTarget)
    if (ferme) {
      notes.push({
        titre: ferme === 'vendu' ? 'Ce bien est vendu.' : ferme === 'clos' ? 'Ce bien est clos.' : 'Ce bien est en estimation.',
        texte: 'On n’y enregistre pas d’offre, de compromis ni de vente : elles se font sur un bien Actif. '
          + (ferme === 'vendu' ? 'Pour revenir en arrière, il faut d’abord supprimer la vente (onglet Vendu).'
            : 'Pour en enregistrer une, remets d’abord le bien en vente (onglet Actif).'),
      })
    }
  }
  const vente = statusChangeStatus === 'compromise' ? compromisVerrouilleParSaVente(statusChangeAffaires, affaireCourante) : null
  if (vente) {
    const numero = String(vente.hektor_affaire_id ?? '').trim()
    notes.push({
      titre: 'On ne revient plus sur ce compromis.',
      texte: `Son dossier porte une vente${numero ? ` (n° ${numero})` : ''}. Le modifier, l’annuler ou le supprimer maintenant remettrait le bien « Sous compromis ». Pour y revenir, il faut d’abord supprimer la vente.`,
    })
  }
  if (offreAccepteeFigeeChezHektor(affaireCourante)) {
    const refusHorsDePortee = Boolean(offreVerrouilleeParSonDossier(statusChangeAffaires, affaireCourante))
    notes.push({
      titre: 'Cette offre est acceptée : son montant ne se corrige plus directement.',
      texte: 'Une fois acceptée, une offre est figée chez Hektor : il n’ouvre même pas son formulaire, et l’envoi échouerait sans un mot d’explication.'
        + (refusHorsDePortee
          ? ' Pour y revenir, il faut d’abord défaire ce que dit la section de l’offre.'
          : ' Pour changer le montant : refuse l’offre, corrige-la, puis accepte-la de nouveau.'),
    })
  }
  if (!notes.length) return null
  return (
    <div className="stv2-notes" role="note">
      {notes.map((n) => <p key={n.titre} className="stv2-bandeau is-info"><b>{n.titre}</b><span>{n.texte}</span></p>)}
    </div>
  )
}

/** Le pied (lot 5). ⛔ Chaque bouton garde SA condition d'affichage, SA condition d'extinction et SON geste, mot pour
 *  mot (contrôle de parité). Changent : l'ordre (les gestes sans retour à gauche, en lien rouge, à l'écart ; le geste
 *  principal à droite), les libellés, et l'aperçu « avant → après » au survol ou au focus du bouton principal. */
function Pied(props: {
  f: FormulaireStatutProps
  statusChangeTarget: Dossier
  statusChangeStatus: HektorAnnonceStatusTarget
  statusChangeAffaires: AffaireLedgerRow[]
  statusChangePending: boolean
  closeStatusChangeModal: () => void
  etatFermeAuxTransactions: GardesParcours['etatFermeAuxTransactions']
}) {
  const { statusChangeTarget, statusChangeStatus, statusChangeAffaires, statusChangePending, closeStatusChangeModal, etatFermeAuxTransactions } = props
  const {
    affaireCourante, statusChangeCorrectionPending, handleGesteHektor, handleChangeHektorAnnonceStatus, gesteOffreSansEffet,
    offreEcarteeSurBienEngage, offreARegulariser, offreVerrouilleeParSonDossier, modifierChezHektorPossible,
    offreAccepteeFigeeChezHektor, compromisVerrouilleParSaVente, statusChangeNeedsTransaction,
    nouvelleOffreFermeeSurBienEngage, gardeFouPourStatut, hektorStatusTargetLabel,
  } = props.f
  // Seul état de la vue : l'aperçu ouvert ou fermé (survol / focus du bouton principal).
  const [apercu, setApercu] = useState(false)
  const affaireCourantePourStatut = () => affaireCourante
  const principalAbsent = (statusChangeNeedsTransaction(statusChangeStatus)
    && etatFermeAuxTransactions(statusChangeTarget))
   || nouvelleOffreFermeeSurBienEngage(statusChangeStatus, statusChangeAffaires)
  const apres = APRES[statusChangeStatus]
  return (
    <footer className="stv2-pied">
      <button className="stv2-btn stv2-btn-2" type="button" onClick={closeStatusChangeModal} disabled={statusChangePending || statusChangeCorrectionPending}>Fermer</button>
      {affaireCourantePourStatut() && statusChangeStatus === 'compromise'
       && !compromisVerrouilleParSaVente(statusChangeAffaires, affaireCourantePourStatut()) ? (
        <button className="stv2-danger" type="button"
          onClick={() => handleGesteHektor('supprimer_compromis')}
          disabled={statusChangePending || statusChangeCorrectionPending}
          title="Le compromis disparaît de Hektor et le statut du bien redescend. Rien ne le remet.">
          Supprimer le compromis…
        </button>
      ) : null}
      {affaireCourantePourStatut() && statusChangeStatus === 'sold' ? (
        <button className="stv2-danger" type="button"
          onClick={() => handleGesteHektor('supprimer_vente')}
          disabled={statusChangePending || statusChangeCorrectionPending}>
          Supprimer la vente…
        </button>
      ) : null}
      <span className="stv2-pied-espace" />
      {affaireCourantePourStatut() && statusChangeStatus === 'offer'
       && !offreVerrouilleeParSonDossier(statusChangeAffaires,
                                         affaireCourantePourStatut()) ? (
        <>
          {!gesteOffreSansEffet(affaireCourantePourStatut(), 'refus') ? (
          <button className="stv2-btn stv2-btn-2" type="button"
            onClick={() => handleGesteHektor('refus')}
            disabled={statusChangePending || statusChangeCorrectionPending}>
            Refuser l’offre
          </button>
          ) : null}
          {!gesteOffreSansEffet(affaireCourantePourStatut(), 'accepte')
           && (!offreEcarteeSurBienEngage(statusChangeAffaires, affaireCourantePourStatut())
               || offreARegulariser(statusChangeAffaires, affaireCourantePourStatut())) ? (
          <button className="stv2-btn stv2-btn-2" type="button"
            onClick={() => handleGesteHektor('accepte')}
            disabled={statusChangePending || statusChangeCorrectionPending}>
            Accepter l’offre
          </button>
          ) : null}
        </>
      ) : null}
      {affaireCourantePourStatut() && statusChangeStatus === 'compromise'
       && !compromisVerrouilleParSaVente(statusChangeAffaires, affaireCourantePourStatut()) ? (
        <button className="stv2-btn stv2-btn-2" type="button"
          onClick={() => handleGesteHektor('annuler_compromis')}
          disabled={statusChangePending || statusChangeCorrectionPending}
          title="Le compromis tombe : la trace reste. C’est le geste normal quand une vente ne se fait pas.">
          Annuler le compromis
        </button>
      ) : null}
      {modifierChezHektorPossible(statusChangeStatus, affaireCourantePourStatut(), statusChangeAffaires) ? (
        <button className="stv2-btn stv2-btn-2" type="button"
          onClick={(e) => { void handleChangeHektorAnnonceStatus(e as unknown as FormEvent<HTMLFormElement>, true) }}
          disabled={statusChangePending || statusChangeCorrectionPending
            || offreAccepteeFigeeChezHektor(affaireCourantePourStatut())}
          title={offreAccepteeFigeeChezHektor(affaireCourantePourStatut())
            ? 'Une offre acceptée est figée chez Hektor : il n’ouvre pas son formulaire, la mise à jour ne peut pas aboutir.'
            : 'Reprend la transaction existante chez Hektor au lieu d’en créer une nouvelle.'}>
          {statusChangePending ? 'Envoi…' : `Mettre à jour ${GENRE_DU_STATUT[statusChangeStatus] ?? ''}`}
        </button>
      ) : null}
      {principalAbsent ? null : (
        <span className="stv2-principal">
          <button className="stv2-btn stv2-btn-1" type="submit"
            aria-describedby={apercu && apres ? 'stv2-apercu' : undefined}
            onMouseEnter={() => setApercu(true)} onMouseLeave={() => setApercu(false)}
            onFocus={() => setApercu(true)} onBlur={() => setApercu(false)}
            title={gardeFouPourStatut()?.bloque
              ? `${gardeFouPourStatut()?.titre} — ${gardeFouPourStatut()?.detail}`
              : undefined}
            disabled={statusChangePending || statusChangeCorrectionPending
              || Boolean(gardeFouPourStatut()?.bloque)}>
            {statusChangePending ? 'Envoi…' : (LIBELLE_ENVOI[statusChangeStatus] ?? `Envoyer vers ${hektorStatusTargetLabel(statusChangeStatus)}`)}
          </button>
          {apercu && apres ? (
            <span id="stv2-apercu" role="tooltip" className="stv2-apercu">
              <span className="stv2-apercu-statuts">
                <span className="stv2-pill">{statusChangeTarget.statut_annonce || '—'}</span>
                <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h13M13 6l6 6-6 6" /></svg>
                <span className="stv2-pill stv2-pill-apres">{apres.statut}</span>
              </span>
              {apres.effets.map((x) => <span key={x} className="stv2-apercu-effet">{x}</span>)}
            </span>
          ) : null}
        </span>
      )}
    </footer>
  )
}

/** Clos (lot 3). ⛔ Les gestes sont ceux de l'ancien bloc, mot pour mot. Les 3 motifs deviennent des cartes ; la
 *  raison reste un menu (ses valeurs dépendent du motif). Le texte de fin dit ce que le code fait VRAIMENT : depuis le
 *  28/08 seul le STATUT part chez Hektor (prouvé le 21/10 sur 62774 : `closure: cloture_locale_uniquement`) ; l'ancien
 *  « définitive côté Hektor » était trompeur (audit §7, I6 du 02/10). */
function Cloture(props: { f: FormulaireStatutProps; statusChangeTarget: Dossier }) {
  const { statusChangeTarget } = props
  const {
    statusChangeCloseEtat, setStatusChangeCloseEtat, statusChangeCloseRaison, setStatusChangeCloseRaison,
    statusChangeCloseDate, setStatusChangeCloseDate, statusChangeCloseReason, setStatusChangeCloseReason,
    hektorClosureEtatOptions, hektorClosureRaisonsFor,
  } = props.f
  const motifManque = statusChangeCloseEtat === 'choiceAutre' && !statusChangeCloseReason.trim()
  return (
    <Section titre={`Pourquoi le mandat ${statusChangeTarget.numero_mandat ?? ''} s’arrête`} dest="nous"
      pied={
        <p className="stv2-note stv2-sec-pied">
          Le statut « Clos » part chez Hektor et coupe la diffusion sur les portails. La date et le motif restent chez
          nous. Le bien se remet en vente par « Actif ». S’il y a une offre ou un compromis en cours, vérifie-les avant
          de clôturer.
        </p>
      }>
      <div className="stv2-motifs" role="radiogroup" aria-label="Motif de clôture">
        {hektorClosureEtatOptions.map((etat) => (
          <button
            key={etat.value}
            type="button"
            role="radio"
            aria-checked={statusChangeCloseEtat === etat.value}
            className={`stv2-carte stv2-motif${statusChangeCloseEtat === etat.value ? ' is-selected' : ''}`}
            onClick={() => { setStatusChangeCloseEtat(etat.value); setStatusChangeCloseRaison(etat.raisons[0]?.value ?? '') }}
          >
            <span className="stv2-carte-t">
              <span className="stv2-marque">{statusChangeCloseEtat === etat.value ? <span className="stv2-marque-point" /> : null}</span>
              {etat.label}
            </span>
          </button>
        ))}
      </div>
      <div className="stv2-grille">
        <Champ libelle="Raison">
          <span className="stv2-in"><select value={statusChangeCloseRaison} onChange={(event) => setStatusChangeCloseRaison(event.target.value)}>
            {hektorClosureRaisonsFor(statusChangeCloseEtat).map((raison) => (
              <option key={raison.value} value={raison.value}>{raison.label}</option>
            ))}
          </select></span>
        </Champ>
        <Champ libelle="Date de clôture du mandat" aide="Vider la case efface notre date ; celle de Hektor revient s’il en a une.">
          <span className="stv2-in"><input
            type="date"
            value={statusChangeCloseDate}
            onChange={(event) => setStatusChangeCloseDate(event.target.value)}
          /></span>
        </Champ>
      </div>
      {statusChangeCloseEtat === 'choiceAutre' ? (
        <Champ libelle="Précisez le motif" requis pastille={motifManque ? { texte: 'À remplir', ton: 'manque' } : null}>
          <textarea className="stv2-zone" value={statusChangeCloseReason} onChange={(event) => setStatusChangeCloseReason(event.target.value)} placeholder="Ex : mandat clos à la demande du propriétaire" required />
        </Champ>
      ) : null}
    </Section>
  )
}

export default function ModaleStatutV2(props: ModaleStatutV2Props) {
  const {
    statusChangeTarget: cible, statusChangeStatus, setStatusChangeStatus, setStatusChangeAffaireChoisie,
    statusChangeAffaires, statusChangePending, closeStatusChangeModal, options, gardes, isValidationApproved,
    pastilleStatut, formulaire,
  } = props
  const [commentOuvert, setCommentOuvert] = useState(false)
  // Lot 6 (06/11) : au téléphone la rangée des cartes défile ; la carte choisie doit y rester VISIBLE (sinon on
  // choisit « Vendu » et on voit « Actif »). Interface seulement : on fait défiler la rangée, rien d'autre.
  const rangee = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const r = rangee.current
    const c = r?.querySelector<HTMLElement>('.stv2-carte.is-selected')
    if (!r || !c || r.scrollWidth <= r.clientWidth) return
    const doux = !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    r.scrollTo({ left: Math.max(0, c.offsetLeft - 16), behavior: doux ? 'smooth' : 'auto' })
  }, [statusChangeStatus])

  const mandatValide = isValidationApproved(cible.validation_diffusion_state)
  const situation = situationDuBien({
    statutAnnonce: cible.statut_annonce,
    affaires: statusChangeAffaires,
    mandatDateFin: cible.mandat_date_fin,
    mandatValide,
    aujourdhui: aujourdhuiLocal(),
  }, gardes)
  const carteChoisie = situation.cartes.find((c) => c.statut === statusChangeStatus)
  const guide = guidePour(statusChangeStatus, situation)
  const libelle = (v: HektorAnnonceStatusTarget | null) => options.find((o) => o.value === v)?.label ?? ''

  // ⚠ LE MÊME GESTE QUE LA CARTE DE L'ANCIENNE MODALE : poser le statut ET oublier l'affaire choisie.
  const choisir = (value: HektorAnnonceStatusTarget) => {
    setStatusChangeStatus(value)
    setStatusChangeAffaireChoisie(null)
  }

  const finMandat = jourFr(cible.mandat_date_fin)
  const echu = situation.avertissements.some((a) => a.startsWith('Le mandat est échu'))
  const titre = cible.titre_bien || cible.numero_dossier || `Annonce ${cible.hektor_annonce_id}`

  return (
    <div className="stv2" onClick={closeStatusChangeModal}>
      <section className="stv2-panel" role="dialog" aria-modal="true" aria-labelledby="stv2-titre" onClick={(event) => event.stopPropagation()}>
        <header className="stv2-head">
          <div className="stv2-head-titres">
            <span className="stv2-eyebrow">Pilotage de l’annonce</span>
            <h3 id="stv2-titre">Changer le statut</h3>
          </div>
          <button className="stv2-fermer" type="button" aria-label="Fermer" onClick={closeStatusChangeModal} disabled={statusChangePending}>
            <svg aria-hidden="true" viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </header>

        <div className="stv2-bien">
          <div className="stv2-bien-id">
            <strong title={titre}>{titre}</strong>
            <span>{cible.numero_dossier ?? '-'}{cible.ville ? ` · ${cible.ville}` : ''}</span>
          </div>
          {pastilleStatut}
          <span className={`stv2-pill${echu || !mandatValide ? ' stv2-pill-warn' : ' stv2-pill-ok'}`}>
            Mandat {cible.numero_mandat ?? '-'}
            {echu ? ` · échu le ${finMandat}` : mandatValide ? ' · validé' : ' · à contrôler'}
          </span>
        </div>

        {/* Comme l'ancien bloc : un <form> dont l'envoi est handleChangeHektorAnnonceStatus ; les `required` des champs
            valent donc au clic, et la touche Entrée dans un champ envoie, comme avant. */}
        <form className="stv2-envoi" onSubmit={formulaire.handleChangeHektorAnnonceStatus}>
        <div className="stv2-corps">
          <div ref={rangee} className="stv2-parcours" role="group" aria-label="Le statut à donner au bien">
            {situation.cartes.map((carte) => {
              const option = options.find((o) => o.value === carte.statut)
              const choisie = carte.statut === statusChangeStatus
              const muette = carte.etat === 'lecture' || carte.etat === 'sans_effet'
              const etiquette = carte.conseille ? 'conseille' : carte.actuel ? 'actuel' : carte.etat === 'hors' ? 'hors' : ''
              const classes = ['stv2-carte', choisie ? 'is-selected' : '', muette ? 'is-muette' : '', carte.actuel ? 'is-actuel' : '']
                .filter(Boolean).join(' ')
              return [
                carte.statut === 'closed' ? <span key="sep" className="stv2-sep" aria-hidden="true" /> : null,
                <button key={carte.statut} className={classes} type="button" aria-pressed={choisie} onClick={() => choisir(carte.statut)}>
                  {etiquette ? <span className={`stv2-etiquette stv2-etiquette-${etiquette}`}>{ETIQUETTE[etiquette]}</span> : null}
                  <span className="stv2-carte-t">
                    <span className="stv2-marque">{choisie ? <span className="stv2-marque-point" /> : null}</span>
                    {option?.label ?? carte.statut}
                  </span>
                  <span className="stv2-carte-d">{muette ? carte.raison : DESCRIPTION_CARTE[carte.statut]}</span>
                </button>,
              ]
            })}
          </div>
          {/* Au téléphone, les cartes ne montrent que leur nom : ce que veut dire la carte choisie passe dessous,
              comme dans l'ancienne modale (.rq-mobile st-desc). Caché au bureau. */}
          <p className="stv2-desc-mobile">
            {carteChoisie && (carteChoisie.etat === 'lecture' || carteChoisie.etat === 'sans_effet')
              ? carteChoisie.raison : DESCRIPTION_CARTE[statusChangeStatus]}
          </p>

          <div key={statusChangeStatus} className={`stv2-guide stv2-guide-${guide.ton}`}>
            <div className="stv2-guide-haut">
              <span className="stv2-guide-ico"><IcoGuide /></span>
              <div className="stv2-guide-txt">
                <strong>{guide.titre}</strong>
                {guide.texte ? <span>{guide.texte}</span> : null}
              </div>
              <div className="stv2-guide-actions">
                {situation.conseille && situation.conseille !== statusChangeStatus ? (
                  <button className="stv2-guide-btn" type="button" onClick={() => choisir(situation.conseille as HektorAnnonceStatusTarget)}>
                    Aller à l’étape conseillée : {libelle(situation.conseille)}
                  </button>
                ) : null}
                <button className="stv2-guide-btn" type="button" aria-expanded={commentOuvert} onClick={() => setCommentOuvert((o) => !o)}>
                  Comment faire
                  <svg aria-hidden="true" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6" /></svg>
                </button>
              </div>
            </div>
            {commentOuvert ? (
              <ol className="stv2-guide-etapes">
                {guide.etapes.map(([quoi, precision], rang) => (
                  <li key={rang}><span className="stv2-guide-n">{rang + 1}</span><span><b>{quoi}</b> {precision}</span></li>
                ))}
              </ol>
            ) : null}
            {situation.avertissements.length ? (
              <ul className="stv2-avert">{situation.avertissements.map((a) => <li key={a}>{a}</li>)}</ul>
            ) : null}
          </div>

          {carteChoisie?.etat === 'hors' ? (
            <div key={`hors-${statusChangeStatus}`} className="stv2-hors">
              <span><b>Hors du parcours conseillé.</b> Le geste reste possible : relis le guide ci-dessus avant d’envoyer.</span>
              {situation.conseille ? (
                <button className="stv2-btn stv2-btn-2" type="button" onClick={() => choisir(situation.conseille as HektorAnnonceStatusTarget)}>
                  Revenir à l’étape conseillée
                </button>
              ) : null}
            </div>
          ) : null}

          {formulaire.statusChangeNeedsTransaction(statusChangeStatus) ? (
            <FormulaireTransaction f={formulaire} statusChangeTarget={cible} statusChangeStatus={statusChangeStatus}
              statusChangeAffaires={statusChangeAffaires} statusChangePending={statusChangePending} />
          ) : statusChangeStatus === 'closed' ? (
            <Cloture f={formulaire} statusChangeTarget={cible} />
          ) : (
            <Section titre="Remettre le bien en vente" dest="hektor">
              <p className="stv2-note">
                Aucune saisie : le statut « Actif » part directement chez Hektor, puis la fiche est relue.
                La diffusion sur les portails est rallumée.
              </p>
            </Section>
          )}
          <AffairesDuBien f={formulaire} statusChangeStatus={statusChangeStatus} statusChangeAffaires={statusChangeAffaires} />
          <NotesDesBoutons f={formulaire} statusChangeTarget={cible} statusChangeStatus={statusChangeStatus}
            statusChangeAffaires={statusChangeAffaires} etatFermeAuxTransactions={gardes.etatFermeAuxTransactions} />
        </div>

        <Pied f={formulaire} statusChangeTarget={cible} statusChangeStatus={statusChangeStatus}
          statusChangeAffaires={statusChangeAffaires} statusChangePending={statusChangePending}
          closeStatusChangeModal={closeStatusChangeModal} etatFermeAuxTransactions={gardes.etatFermeAuxTransactions} />
        </form>
      </section>
    </div>
  )
}
