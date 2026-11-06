// A.2 (06/11/2026) -- LA FENETRE « FAIRE SIGNER » REFAITE (maquette validee par Frederic : habillage + points 1 a 4 ;
// le point 5, l'ordre / une voie recommandee, est abandonne : l'ordre reste Youtrust, Hektor, manuscrite).
// Elle reprend le bandeau et la carte du document de la fenetre d'envoi Youtrust, qui la suit : les deux se lisent
// comme un seul parcours. Les trois voies restent VISIBLES ; une voie fermee garde son titre lisible et dit pourquoi.
//   1. l'identite du document (n° de mandat, date de generation, cases, depot chez Hektor) ;
//   2. qui signe (lu dans la photo du PDF ; un modele Hektor n'en a pas) ;
//   3. « Regenerer le mandat » quand Youtrust est ferme faute d'un PDF de l'editeur ;
//   4. « Voir le suivi » quand une signature electronique est en cours.
// Rien d'autre ne change : les trois gestes sont ceux d'avant (onYoutrust / onHektor / onManuscrite).
// La regle des voies et la lecture de l'identite vivent dans lib/choixSignature.ts.
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { createConsoleDocumentSignedUrl } from './lib/api'
import { identiteDuDocument, TEXTE_REGENERER, type Choix, type ChoixDeSignature } from './lib/choixSignature'
import type { ConsoleDocument } from './types'
import './choix-signature.css'

type Voie = { cle: 'youtrust' | 'hektor' | 'manuscrite'; titre: string; fournisseur: string; desc: string; faits: string; verbe: string; c: Choix; agir: () => void }

export default function ChoixSignatureFenetre(props: {
  document: ConsoleDocument
  choix: ChoixDeSignature
  onYoutrust: () => void
  onHektor: () => void
  onManuscrite: () => void
  onClose: () => void
  // Le bien (sous-titre du bandeau), le n° de mandat et le negociateur qui contresigne (points 1 et 2).
  adresse?: string | null
  numeroMandat?: string | null
  negociateur?: string | null
  // Point 3 : ouvre l'editeur pour un nouveau mandat ; rend false si aucun editeur n'a pu s'ouvrir (la fenetre le dit).
  onRegenerer?: () => boolean | void
  // Point 4 : mene au suivi des signataires (ou se trouve « Annuler la signature »).
  onVoirSuivi?: () => void
}) {
  const { document: doc, choix } = props
  const id = identiteDuDocument(doc as ConsoleDocument & { created_at?: string | null }, { numeroMandat: props.numeroMandat, negociateur: props.negociateur })
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    const echap = (event: KeyboardEvent) => { if (event.key === 'Escape') props.onClose() }
    window.addEventListener('keydown', echap)
    return () => window.removeEventListener('keydown', echap)
  }, [props])

  const voies: Voie[] = [
    { cle: 'youtrust', titre: 'Signature électronique', fournisseur: 'Youtrust', c: choix.youtrust, agir: props.onYoutrust, verbe: 'Préparer l’envoi',
      desc: 'Chaque mandant reçoit son lien par e-mail et signe avec un code. Le négociateur contresigne en dernier.',
      faits: `Suivi ici, signataire par signataire ; preuves rangées avec le mandat ; 1 crédit par signataire${id.cases ? `, ${id.cases} pour ce mandat` : ''}.` },
    { cle: 'hektor', titre: 'Signature Hektor', fournisseur: 'ImmoSign', c: choix.hektor, agir: props.onHektor, verbe: 'Ouvrir Hektor',
      desc: 'Hektor s’ouvre dans un nouvel onglet, sur l’onglet Documents : vous y lancez la procédure.',
      faits: 'L’état de la signature revient dans l’app quand Hektor est relu.' },
    { cle: 'manuscrite', titre: 'Signature manuscrite', fournisseur: 'sur papier', c: choix.manuscrite, agir: props.onManuscrite, verbe: 'Marquer signé',
      desc: 'Le document a été signé à la main par tous les mandants.',
      faits: 'À faire une fois le PDF signé joint aux documents du bien.' },
  ]

  async function voirPdf() {
    const onglet = window.open('about:blank', '_blank')
    try {
      const url = await createConsoleDocumentSignedUrl(doc)
      if (onglet) { onglet.opener = null; onglet.location.href = url } else window.open(url, '_blank', 'noopener')
    } catch (err) {
      onglet?.close()
      setMessage(err instanceof Error ? err.message : 'Le PDF ne s’ouvre pas.')
    }
  }
  function regenerer() {
    if (!props.onRegenerer) return
    if (props.onRegenerer() === false) setMessage('Ouvrez la rubrique Mandat du bien pour régénérer le mandat : l’éditeur n’est pas ouvert ici.')
  }

  const titre = id.estMandat ? 'Faire signer ce mandat' : 'Faire signer ce document'
  const pdfOuvrable = doc.storage_status === 'cloud_available' && Boolean(doc.storage_path)

  // Monte dans le body : le panneau de la fiche porte un `transform`, qui piege un `position: fixed` (essai reel du 06/11).
  return createPortal(
    <div className="cxs-voile" role="dialog" aria-modal="true" aria-label={titre} onClick={props.onClose}>
      <div className="cxs-modale" onClick={(event) => event.stopPropagation()}>
        <div className="cxs-tete">
          <span className="cxs-ico" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21c3-1 5-3 7-6" /><path d="M14 4l6 6-9 9-5 1 1-5z" /></svg>
          </span>
          <div className="cxs-titres">
            <strong>{titre}</strong>
            {props.adresse ? <small>{props.adresse}</small> : null}
          </div>
          <button type="button" className="cxs-fermer" onClick={props.onClose}>Fermer</button>
        </div>

        <div className="cxs-corps">
          {/* Point 1 : quel document. */}
          <div className="cxs-doc">
            <span className="cxs-pdf" aria-hidden="true"><i /><b>PDF</b></span>
            <div className="cxs-doc-txt">
              <strong>{id.titre}</strong>
              {id.meta ? <small>{id.meta}</small> : null}
            </div>
            <div className="cxs-doc-droite">
              <span className={`cxs-depot ${id.depot.ton}`}>{id.depot.texte}</span>
              {pdfOuvrable ? <button type="button" className="cxs-lien" onClick={() => void voirPdf()}>Voir le PDF</button> : null}
            </div>
          </div>

          {/* Point 2 : qui signe. */}
          {id.signataires ? <p className="cxs-qui">{id.signataires}</p> : null}

          {/* Point 4 : une signature est deja en cours. */}
          {choix.procedureEnCours ? (
            <div className="cxs-encours" role="status">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
              <div>
                <strong>{choix.procedureEnCours === 'youtrust'
                  ? `Une signature électronique est en cours${id.progression ? ` : ${id.progression}` : ''}.`
                  : 'Une signature Hektor (ImmoSign) est en cours.'}</strong>{' '}
                Un document ne part jamais dans deux procédures : annulez celle-ci d’abord pour en choisir une autre.
                {choix.procedureEnCours === 'youtrust' && props.onVoirSuivi
                  ? <> <button type="button" className="cxs-lien" onClick={props.onVoirSuivi}>Voir le suivi</button></>
                  : choix.procedureEnCours === 'immosign' ? ' (bouton « Annuler » du document)' : null}
              </div>
            </div>
          ) : null}

          <div className="cxs-question">Comment le faire signer ?</div>
          <div className="cxs-voies">
            {voies.map((v) => {
              const ouvert = v.c.possible
              const contenu = (
                <>
                  <span className={`cxs-pastille ${v.cle}`} aria-hidden="true">
                    {v.cle === 'youtrust' ? <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg>
                      : v.cle === 'hektor' ? <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 4h6v6" /><path d="M20 4l-9 9" /><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></svg>
                      : <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20h16" /><path d="M6 16l9-9 3 3-9 9H6z" /></svg>}
                  </span>
                  <span className="cxs-voie-txt">
                    <span className="cxs-voie-titre"><b>{v.titre}</b><small>{v.fournisseur}</small></span>
                    <span className="cxs-voie-desc">{v.desc}</span>
                    {ouvert ? <span className="cxs-voie-faits">{v.faits}</span> : null}
                  </span>
                  <span className={`cxs-verbe${ouvert ? '' : ' ferme'}`}>{ouvert ? v.verbe : 'Indisponible'}</span>
                </>
              )
              return (
                <div key={v.cle} className={`cxs-voie${ouvert ? '' : ' is-ferme'}`} data-choix={v.cle}>
                  {ouvert
                    ? <button type="button" className="cxs-voie-main" onClick={v.agir}>{contenu}</button>
                    : <div className="cxs-voie-main" aria-disabled="true">{contenu}</div>}
                  {!ouvert && v.c.raison ? (
                    <div className="cxs-raison">
                      <span>{v.c.raison}</span>
                      {/* Point 3 : le seul cas ou l'app peut l'ouvrir elle-meme. */}
                      {v.cle === 'youtrust' && v.c.raison === TEXTE_REGENERER && props.onRegenerer
                        ? <button type="button" className="cxs-lien" onClick={regenerer}>Régénérer le mandat</button>
                        : null}
                    </div>
                  ) : null}
                </div>
              )
            })}
          </div>
          {message ? <p className="cxs-message" role="alert">{message}</p> : null}
        </div>
      </div>
    </div>,
    window.document.body,
  )
}
