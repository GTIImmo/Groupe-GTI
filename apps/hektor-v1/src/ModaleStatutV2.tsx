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
// Les formulaires, les affaires du bien et les boutons d'envoi arrivent aux lots 2 à 5 : d'ici là, l'ancienne
// modale reste en service (interrupteur éteint).

import { useState, type ReactNode } from 'react'
import type { Dossier } from './types'
import { situationDuBien, type AffaireLedgerRow, type GardesParcours, type HektorAnnonceStatusTarget } from './lib/statutParcours'
import { DESCRIPTION_CARTE, guidePour } from './lib/statutGuide'

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

export default function ModaleStatutV2(props: ModaleStatutV2Props) {
  const {
    statusChangeTarget: cible, statusChangeStatus, setStatusChangeStatus, setStatusChangeAffaireChoisie,
    statusChangeAffaires, statusChangePending, closeStatusChangeModal, options, gardes, isValidationApproved,
    pastilleStatut,
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

          <div className="stv2-attente">
            Lot 1 de la refonte : la saisie de l’étape « {libelle(statusChangeStatus)} », les affaires du bien et les
            boutons d’envoi arrivent aux lots suivants. Interrupteur éteint, l’ancienne modale reste en service.
          </div>
        </div>

        <footer className="stv2-pied">
          <button className="stv2-btn stv2-btn-2" type="button" onClick={closeStatusChangeModal} disabled={statusChangePending}>Fermer</button>
        </footer>
      </section>
    </div>
  )
}
