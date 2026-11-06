// A.2 P8-4 (06/11/2026) -- « PREUVES » : ouvrir l'original non signé et les preuves d'un document signé (Youtrust ou
// ImmoSign), au coffre. Derrière l'interrupteur `signature_preuves` (app_setting ; absent = éteint) : éteint, aucun bouton.
// La liste des pièces vit dans lib/piecesSignature.ts ; la règle du coffre qui les ouvre, dans
// supabase/patch_a2_p8_4_preuves_coffre_2026-11-06.sql (sans elle, chaque pièce répond « pas lisible »).
import { useEffect, useState } from 'react'
import { createPieceSignatureUrl, loadAppSettingActive, piecesAuCoffre } from './lib/api'
import { piecesDeSignature, type PieceSignature } from './lib/piecesSignature'
import type { ConsoleDocument } from './types'

export function useSignaturePreuves() {
  const [actif, setActif] = useState(false)
  useEffect(() => {
    let annule = false
    void loadAppSettingActive('signature_preuves').then((v) => { if (!annule) setActif(v) })
    return () => { annule = true }
  }, [])
  return actif
}

// Ouvre une pièce : un PDF dans un onglet, un ZIP en téléchargement. L'onglet est ouvert AVANT l'appel (sinon le
// navigateur bloque une fenêtre ouverte après une attente), puis dirigé vers l'adresse signée -- ou refermé.
export async function ouvrirPieceSignature(piece: PieceSignature): Promise<void> {
  const onglet = window.open('about:blank', '_blank')
  try {
    const url = await createPieceSignatureUrl(piece)
    if (onglet) { onglet.opener = null; onglet.location.href = url } else window.open(url, '_blank', 'noopener')
  } catch (err) {
    onglet?.close()
    throw err
  }
}

export function PiecesSignatureFenetre({ document, onClose }: { document: ConsoleDocument; onClose: () => void }) {
  const pieces = piecesDeSignature(document)
  const [occupe, setOccupe] = useState<string | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  // Présence au coffre, lue à l'ouverture : une pièce absente (serveur seul) se montre grisée, sans geste.
  const [presence, setPresence] = useState<Record<string, boolean | null> | null>(null)
  useEffect(() => {
    let annule = false
    void piecesAuCoffre(pieces).then((r) => { if (!annule) setPresence(r) }).catch(() => { if (!annule) setPresence({}) })
    return () => { annule = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [document.id])
  async function ouvrir(p: PieceSignature) {
    setOccupe(p.cle); setErreur(null)
    try { await ouvrirPieceSignature(p) }
    catch (err) { setErreur(err instanceof Error ? err.message : 'Pièce indisponible') }
    finally { setOccupe(null) }
  }
  return (
    <div role="dialog" aria-modal="true" onClick={onClose}
      style={{ position: 'fixed', inset: 0, zIndex: 10060, background: 'rgba(17,17,23,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
      <div onClick={(event) => event.stopPropagation()}
        style={{ background: '#fff', borderRadius: '14px', maxWidth: '480px', width: '100%', padding: '22px 24px', boxShadow: '0 24px 70px rgba(0,0,0,0.35)' }}>
        <strong style={{ display: 'block', fontSize: '17px', marginBottom: '6px' }}>Pièces de la signature</strong>
        <p style={{ margin: '0 0 14px', color: '#555', fontSize: '13px' }}>{`Document : ${document.document_name ?? ''}`}</p>
        {pieces.length ? (
          <div style={{ display: 'grid', gap: '8px' }}>
            {pieces.map((p) => {
              const absente = presence?.[p.cle] === false
              return (
                <button key={p.cle} type="button" className="ghost-button" data-piece={p.genre} disabled={occupe !== null || absente} onClick={() => void ouvrir(p)}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', textAlign: 'left', padding: '10px 12px', borderRadius: '10px', opacity: absente ? 0.55 : 1 }}>
                  <span style={{ fontWeight: 600 }}>{p.libelle}</span>
                  <span style={{ fontSize: '12px', color: '#666' }}>{absente ? 'Sur le serveur seulement' : presence === null ? 'Vérification…' : occupe === p.cle ? 'Ouverture…' : p.format === 'zip' ? 'Télécharger' : 'Ouvrir'}</span>
                </button>
              )
            })}
          </div>
        ) : <p style={{ margin: 0, color: '#666' }}>Aucune pièce au coffre pour ce document : elles n’existent que sur le serveur.</p>}
        {erreur ? <p className="console-documents-error" role="alert" style={{ margin: '12px 0 0' }}>{erreur}</p> : null}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '14px' }}>
          <button className="ghost-button button-subtle" type="button" onClick={onClose}>Fermer</button>
        </div>
      </div>
    </div>
  )
}
