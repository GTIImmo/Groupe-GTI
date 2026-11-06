// CHANTIER PARTENAIRES · LOT 4, PIÈCE 4.4 (06/11/2026) — LA FENÊTRE « DEMANDER UN DOCUMENT » AU SYNDIC (version simple).
// Règles : lib/demandeDocument.ts. Un message prêt, modifiable ; « Copier » et, si l'e-mail est connu, « Ouvrir dans ma
// messagerie ». RIEN n'est enregistré ni envoyé par l'app (le suivi des demandes viendra plus tard).
import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { PIECES_COPRO, adresseLisible, lienMessagerie, messageDemande, piecesParDefaut, type BienDemande } from './lib/demandeDocument'
import './demande-document.css'

export default function DemandeDocument(props: {
  syndicNom: string
  syndicEmail: string | null
  biens: BienDemande[]
  bienInitial?: string | null
  signature?: string | null
  onClose: () => void
}) {
  const [bienId, setBienId] = useState<string>(props.bienInitial ?? props.biens[0]?.id ?? '')
  const [pieces, setPieces] = useState<string[]>(piecesParDefaut)
  const bien = props.biens.find((b) => b.id === bienId) ?? props.biens[0] ?? null
  const propose = useMemo(() => (bien ? messageDemande({ bien, pieces, signature: props.signature }) : null), [bien, pieces, props.signature])
  const [corps, setCorps] = useState(propose?.corps ?? '')
  const [retouche, setRetouche] = useState(false)
  const [copie, setCopie] = useState<'non' | 'ok' | 'echec'>('non')
  // Tant que le texte n'a pas été retouché à la main, il suit le bien et les pièces choisis.
  useEffect(() => { if (!retouche && propose) setCorps(propose.corps) }, [propose, retouche])
  useEffect(() => {
    const echap = (e: KeyboardEvent) => { if (e.key === 'Escape') props.onClose() }
    window.addEventListener('keydown', echap)
    return () => window.removeEventListener('keydown', echap)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const sujet = propose?.sujet ?? ''
  const lien = lienMessagerie(props.syndicEmail, sujet, corps)
  const basculer = (cle: string) => setPieces((p) => (p.includes(cle) ? p.filter((x) => x !== cle) : [...p, cle]))
  async function copier() {
    try { await navigator.clipboard.writeText(`${sujet}\n\n${corps}`); setCopie('ok') } catch { setCopie('echec') }
  }

  return createPortal(
    <div className="dd-fond" onClick={props.onClose}>
      <section className="dd-fenetre" role="dialog" aria-modal="true" aria-label="Demander un document au syndic" onClick={(e) => e.stopPropagation()}>
        <header className="dd-tete">
          <div>
            <h2>Demander un document</h2>
            <p>à {props.syndicNom}</p>
          </div>
          <button type="button" className="dd-fermer" aria-label="Fermer" onClick={props.onClose}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12" /></svg>
          </button>
        </header>

        {!bien ? <p className="dd-vide">Aucun de nos biens n'est relié à ce syndic : choisissez d'abord le syndic sur la fiche d'un bien.</p> : (
          <div className="dd-corps">
            <div className="dd-gauche">
              {props.biens.length > 1 ? (
                <label className="dd-champ"><span>Pour quel bien ?</span>
                  <select value={bien.id} onChange={(e) => { setBienId(e.target.value); setRetouche(false) }}>
                    {props.biens.map((b) => <option key={b.id} value={b.id}>{adresseLisible(b)}{b.mandat ? ` · mandat ${b.mandat}` : ''}</option>)}
                  </select>
                </label>
              ) : <div className="dd-champ"><span>Le bien</span><strong>{adresseLisible(bien)}</strong></div>}
              <fieldset className="dd-pieces">
                <legend>Les pièces demandées</legend>
                {PIECES_COPRO.map((p) => (
                  <label key={p.cle}><input type="checkbox" checked={pieces.includes(p.cle)} onChange={() => { basculer(p.cle); setRetouche(false) }} />{p.libelle}</label>
                ))}
              </fieldset>
            </div>
            <div className="dd-droite">
              <label className="dd-champ"><span>Objet</span><input type="text" value={sujet} readOnly /></label>
              <label className="dd-champ dd-message"><span>Message {retouche ? <em>retouché</em> : null}</span>
                <textarea value={corps} onChange={(e) => { setCorps(e.target.value); setRetouche(true) }} />
              </label>
              <p className={`dd-dest${props.syndicEmail ? '' : ' manque'}`}>
                {props.syndicEmail ? <>À : <b>{props.syndicEmail}</b></> : "Pas d'e-mail sur la fiche de ce syndic : copiez le message, ou ajoutez son e-mail sur sa fiche."}
              </p>
            </div>
          </div>
        )}

        <footer className="dd-pied">
          <span className="dd-note">Rien n'est enregistré : le suivi des demandes et des délais viendra plus tard.</span>
          {bien ? <button type="button" className="dd-btn" onClick={() => { void copier() }}>{copie === 'ok' ? 'Copié' : copie === 'echec' ? 'Copie impossible' : 'Copier le message'}</button> : null}
          {bien && lien ? <a className="dd-btn primaire" href={lien}>Ouvrir dans ma messagerie</a> : null}
        </footer>
      </section>
    </div>,
    document.body,
  )
}
