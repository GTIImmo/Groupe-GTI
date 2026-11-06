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
// Actif et Clos (lot 3), les affaires du bien (lot 4) et les boutons d'envoi (lot 5) suivent : d'ici là,
// l'ancienne modale reste en service (interrupteur éteint).

import { useState, type ComponentType, type Dispatch, type ReactNode, type SetStateAction } from 'react'
import type { Dossier } from './types'
import { situationDuBien, type AffaireLedgerRow, type GardesParcours, type HektorAnnonceStatusTarget } from './lib/statutParcours'
import { DESCRIPTION_CARTE, guidePour } from './lib/statutGuide'
import type {
  AffaireCondition, ConditionCatalogueRow, DataScope, MandantContactSearchOption, RepartitionLigne, RepartitionPersonne,
} from './lib/statutV2Types'
import { bvs } from './lib/bienvuTexte'

type Setter<T> = Dispatch<SetStateAction<T>>
type Cote = 'entree' | 'sortie'

/** Lot 2 (06/11) — tout ce que le formulaire offre / compromis / vente de l'ancien bloc lit et appelle, SOUS LES
 *  MÊMES NOMS (App.tsx les passe en raccourci `{ statusChangeAmount, … }`). Rien d'autre. */
export type FormulaireStatutProps = {
  statusChangeAmount: string; setStatusChangeAmount: Setter<string>
  statusChangeSalePrice: string; setStatusChangeSalePrice: Setter<string>
  statusChangeDate: string; setStatusChangeDate: Setter<string>
  statusChangeValidityDays: string; setStatusChangeValidityDays: Setter<string>
  statusChangeSignatureDate: string; setStatusChangeSignatureDate: Setter<string>
  statusChangeRetractionDays: string; setStatusChangeRetractionDays: Setter<string>
  statusChangeSelectedMandat: string; setStatusChangeSelectedMandat: Setter<string>
  statusChangePrixVenteManuel: boolean; setStatusChangePrixVenteManuel: Setter<boolean>
  statusChangeBuyers: MandantContactSearchOption[]
  statusChangeBuyerSearch: string; setStatusChangeBuyerSearch: Setter<string>
  statusChangeBuyerOptions: MandantContactSearchOption[]
  statusChangeBuyerLoading: boolean
  statusChangeBuyerError: string | null
  statusChangeMandants: Array<{ id: string; nom: string }>; setStatusChangeMandants: Setter<Array<{ id: string; nom: string }>>
  statusChangeMandantsAffirmes: boolean; setStatusChangeMandantsAffirmes: Setter<boolean>
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
  SelecteurMandants: ComponentType<{
    choisis: Array<{ id: string; nom: string }>; scope: DataScope | null | undefined
    onAjouter: (option: MandantContactSearchOption) => void; onRetirer: (id: string) => void
  }>
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

function Section(props: { titre: string; dest?: 'hektor' | 'nous' | 'mixte'; children: ReactNode; pied?: ReactNode }) {
  return (
    <section className="stv2-sec">
      <div className="stv2-sech">
        <h4>{props.titre}</h4>
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
    statusChangeSelectedMandat, setStatusChangeSelectedMandat, statusChangePrixVenteManuel, setStatusChangePrixVenteManuel,
    statusChangeBuyers, statusChangeBuyerSearch, setStatusChangeBuyerSearch, statusChangeBuyerOptions,
    statusChangeBuyerLoading, statusChangeBuyerError, statusChangeMandants, setStatusChangeMandants,
    statusChangeMandantsAffirmes, setStatusChangeMandantsAffirmes, statusChangeSellerNotaryId, setStatusChangeSellerNotaryId,
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
    affaireCourante, offreAccepteeAReprendreAuCompromis, affaireEstVivante, SelecteurMandants, SelecteurNotaire,
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
  const pastille = (cle: string, valeur: string, sources: Array<[string, unknown]>, requis = false): Pastille | null => {
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
      <Section titre={titreAffaire} dest="hektor">
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
              }} inputMode="numeric" placeholder="Ex : 180000" required /><span className="stv2-u">€</span></span>
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
            }} inputMode="numeric" placeholder="Ex : 180000" required={statusChangeNeedsSalePrice(statusChangeStatus)} /><span className="stv2-u">€</span></span>
          </Champ>
          <Champ libelle={statusChangeStatus === 'sold' ? 'Date de l’acte' : statusChangeStatus === 'compromise' ? 'Date du compromis' : 'Date de l’offre'} requis
            pastille={pastille('transaction_date', statusChangeDate, [['Actuel', affaireCourante?.date], ['Aujourd’hui', aujourdhui]], true)}>
            <span className="stv2-in"><input type="date" value={statusChangeDate} onChange={(event) => { setStatusChangeDate(event.target.value); toucherStatusChange('transaction_date') }} required /></span>
          </Champ>
          {statusChangeStatus === 'offer' ? (
            <Champ libelle="Validité de l’offre" pastille={pastille('validity_days', statusChangeValidityDays, [['Par défaut', '10']])}>
              <span className="stv2-in"><input value={statusChangeValidityDays} onChange={(event) => { setStatusChangeValidityDays(event.target.value); toucherStatusChange('validity_days') }} inputMode="numeric" placeholder="10" /><span className="stv2-u">jours</span></span>
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
          <Champ libelle="N° de mandat" pastille={pastille('selected_mandat', statusChangeSelectedMandat,
            [['Actuel', affaireCourante?.numero_mandat], ['Repris du compromis', compromisRepris?.numero_mandat], ['Mandat du bien', statusChangeTarget.numero_mandat]])}>
            <span className="stv2-in"><input value={statusChangeSelectedMandat} onChange={(event) => { setStatusChangeSelectedMandat(event.target.value); toucherStatusChange('selected_mandat') }} placeholder="Attribué automatiquement si vide" /></span>
          </Champ>
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
          <SelecteurMandants
            choisis={statusChangeMandants}
            scope={dataScope}
            onAjouter={(option) => {
              const id = String(option.hektor_contact_id ?? '').trim()
              if (!id) return
              setStatusChangeMandants((liste) => (
                liste.some((x) => x.id === id)
                  ? liste
                  : [...liste, { id, nom: mandantContactOptionTitle(option) }]))
              setStatusChangeMandantsAffirmes(true)
            }}
            onRetirer={(id) => {
              setStatusChangeMandants((liste) => liste.filter((x) => x.id !== id))
              setStatusChangeMandantsAffirmes(true)
            }} />
          {statusChangeMandantsAffirmes ? (
            <p className="stv2-note is-alerte">
              La liste des vendeurs sera <strong>{bvs("envoyée à Hektor")}</strong> et remplacera la sienne. Tant que tu
              n’y touches pas, c’est la sienne qui vaut.
            </p>
          ) : null}
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

export default function ModaleStatutV2(props: ModaleStatutV2Props) {
  const {
    statusChangeTarget: cible, statusChangeStatus, setStatusChangeStatus, setStatusChangeAffaireChoisie,
    statusChangeAffaires, statusChangePending, closeStatusChangeModal, options, gardes, isValidationApproved,
    pastilleStatut, formulaire,
  } = props
  const [commentOuvert, setCommentOuvert] = useState(false)

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

        <div className="stv2-corps">
          <div className="stv2-parcours" role="group" aria-label="Le statut à donner au bien">
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
          ) : (
            <div className="stv2-attente">
              Lot 2 de la refonte : la saisie de l’étape « {libelle(statusChangeStatus)} » arrive au lot 3, les affaires du
              bien au lot 4 et les boutons d’envoi au lot 5. Interrupteur éteint, l’ancienne modale reste en service.
            </div>
          )}
        </div>

        <footer className="stv2-pied">
          <button className="stv2-btn stv2-btn-2" type="button" onClick={closeStatusChangeModal} disabled={statusChangePending}>Fermer</button>
        </footer>
      </section>
    </div>
  )
}
