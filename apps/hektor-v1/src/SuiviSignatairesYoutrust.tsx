// A.2 P8-3 (06/11/2026) -- LE SUIVI PAR SIGNATAIRE d'un document envoye par Youtrust : qui a signe, quand, qui attend,
// et les deux gestes « Relancer » (une personne) et « Annuler la signature » (la demande).
// Ne s'affiche que pour un document dont la signature est Youtrust (`provider: youtrust` + `signature_request_id`) :
// ImmoSign garde ses boutons a l'identique. Les gestes ne sont proposes que si l'interrupteur `signature_youtrust` est
// allume (le worker les refuse sinon : exigerInterrupteurYoutrust) ; eteint, le suivi reste LISIBLE, sans bouton.
// Les regles des gestes vivent dans lib/suiviSignataires.ts (celles de Youtrust : aucun travail qu'il refuserait).
import { useEffect, useState } from 'react'
import { createYoutrustCancelSignatureJob, createYoutrustRemindSignerJob, loadDemandeSignature } from './lib/api'
import { suiviDeLaDemande, type DemandeSignature } from './lib/suiviSignataires'
import type { ConsoleDocument, ConsoleJob } from './types'
import './suivi-signataires.css'

type SignatureYoutrust = { provider?: string | null; status?: string | null; progress?: string | null; signature_request_id?: string | null }

export function signatureYoutrustDuDocument(document: ConsoleDocument): SignatureYoutrust | null {
  const sig = (document.metadata_json as { signature?: SignatureYoutrust } | null)?.signature
  return sig && sig.provider === 'youtrust' && sig.signature_request_id ? sig : null
}

export default function SuiviSignatairesYoutrust({ document, gestesActifs, onJobCreated, onChange }: {
  document: ConsoleDocument
  gestesActifs: boolean
  onJobCreated?: (job: ConsoleJob) => void
  onChange?: () => void
}) {
  const sig = signatureYoutrustDuDocument(document)
  const id = sig?.signature_request_id ?? null
  const [demande, setDemande] = useState<DemandeSignature | null>(null)
  const [lu, setLu] = useState(false)
  const [ouvert, setOuvert] = useState(sig?.status === 'pending')
  const [occupe, setOccupe] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  // Relu quand le miroir du document bouge (un avis Youtrust a ete traite : statut ou « 1/3 » change).
  useEffect(() => {
    if (!id) return
    let annule = false
    setLu(false)
    void loadDemandeSignature(id)
      .then((d) => { if (!annule) { setDemande(d); setLu(true) } })
      .catch((err) => { if (!annule) { setErreur(err instanceof Error ? err.message : 'Suivi de signature illisible'); setLu(true) } })
    return () => { annule = true }
  }, [id, sig?.status, sig?.progress])

  if (!id) return null
  const suivi = suiviDeLaDemande(demande)

  async function relancer(signerId: string, nom: string, email: string | null) {
    if (!window.confirm(`Renvoyer le lien de signature à ${nom}${email ? ` (${email})` : ''} ?\n\n${document.document_name}`)) return
    setOccupe(signerId); setMessage(null); setErreur(null)
    try {
      const job = await createYoutrustRemindSignerJob({ document, signatureRequestId: id!, providerSignerId: signerId })
      onJobCreated?.(job)
      setMessage(`Relance demandée pour ${nom}.`)
    } catch (err) { setErreur(err instanceof Error ? err.message : 'Impossible de demander la relance') }
    finally { setOccupe(null) }
  }

  async function annuler() {
    if (!window.confirm(`Annuler la signature électronique en cours ?\n\n${document.document_name}\n\nLes signataires ne pourront plus signer ce lien. Le document redeviendra « à signer » : vous pourrez le renvoyer, ou le signer à la main.`)) return
    setOccupe('annuler'); setMessage(null); setErreur(null)
    try {
      const job = await createYoutrustCancelSignatureJob({ document, signatureRequestId: id! })
      onJobCreated?.(job)
      setMessage('Annulation demandée : elle sera faite dans quelques secondes.')
      onChange?.()
    } catch (err) { setErreur(err instanceof Error ? err.message : "Impossible de demander l'annulation") }
    finally { setOccupe(null) }
  }

  return (
    <div className="sst-suivi" data-statut={demande?.status ?? ''}>
      <button type="button" className="sst-entete" aria-expanded={ouvert} onClick={() => setOuvert((v) => !v)}>
        <span className="sst-chevron" aria-hidden="true">{ouvert ? '▾' : '▸'}</span>
        <span>{lu ? `Signataires — ${suivi.resume}` : 'Signataires — lecture…'}</span>
      </button>
      {ouvert ? (
        <div className="sst-corps">
          {lu && !demande && !erreur ? <p className="sst-vide">Demande de signature introuvable.</p> : null}
          {suivi.lignes.length ? (
            <ul className="sst-liste">
              {suivi.lignes.map((l) => (
                <li key={l.cle} className="sst-ligne" data-ton={l.ton}>
                  <span className="sst-point" aria-hidden="true" />
                  <span className="sst-qui">
                    <strong>{l.nom}</strong>
                    <span className="sst-role">{l.role}</span>
                  </span>
                  <span className="sst-etat">{l.libelle}</span>
                  {gestesActifs && l.relancable && l.providerSignerId ? (
                    <button type="button" className="ghost-button sst-relancer" disabled={occupe !== null}
                      onClick={() => void relancer(l.providerSignerId!, l.nom, l.email)}>
                      {occupe === l.providerSignerId ? 'Envoi…' : 'Relancer'}
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}
          {gestesActifs && suivi.annulable ? (
            <div className="sst-pied">
              <button type="button" className="ghost-button sst-annuler" disabled={occupe !== null} onClick={() => void annuler()}>
                {occupe === 'annuler' ? 'Annulation…' : 'Annuler la signature'}
              </button>
            </div>
          ) : null}
          {message ? <p className="console-documents-message sst-msg">{message}</p> : null}
          {erreur ? <p className="console-documents-error sst-msg" role="alert">{erreur}</p> : null}
        </div>
      ) : null}
    </div>
  )
}
