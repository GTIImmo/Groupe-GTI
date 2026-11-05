// A.2 lot 6b P4 (05/11/2026) -- LA FENETRE D'ENVOI EN SIGNATURE YOUTRUST, devenue une CONFIRMATION.
// Maquette validee par Frederic le 05/11 (notice/PROPOSITION_FENETRE_ENVOI_SIGNATURE_2026-10-26.md §12.1, vues 1-2).
//
// ⛔ ELLE NE MODIFIE JAMAIS LE PDF (D31) : les signataires sont LUS dans la photo rangee avec le document a sa
//   generation (metadata_json.signataires_du_pdf, P1), dans l'ordre de leurs cases. Pas d'ajout, pas de retrait,
//   pas de nom modifiable : ce qui est imprime porte un cadenas, et la bulle dit de corriger le mandat puis de le
//   regenerer (le chemin « Corriger le mandat » est la piece P5).
// ✎ Seuls l'E-MAIL et le PORTABLE se completent ici (D33) : ce sont des canaux de remise. Ils partent dans la demande
//   (corrections par rang, que le worker controle, P2) et s'enregistrent sur la fiche du mandant (porte du mandant,
//   regle D-5). ⚠ Pas pour un CONJOINT : sa fiche se corrige par « Modifier le conjoint », depuis la fiche principale
//   (proposition §8.3) -- la correction part alors seulement dans la demande.
// N'est montee que si l'interrupteur `signature_youtrust` est allume (App.tsx) ; eteint, rien ne change a l'ecran.
// P5 (05/11) : « Corriger le mandat » rouvre l'editeur (onCorriger) ; au retour d'une regeneration, `ancien` est le
//   PDF remplace et la fenetre dit « ce qui a change » (maquette « corriger » vues 3-4). Un PDF remplace ne part pas.
// P6 (05/11) : `ficheDuJour` -- si la fiche a change depuis le PDF (mandants, bien, prix, honoraires), un bandeau le dit
//   et propose de regenerer ; « Envoyer quand meme… » demande une confirmation, ecrite dans la demande (vue 5).
import { useEffect, useMemo, useState } from 'react'
import {
  contenuImprimeDuDocument,
  createConsoleDocumentSignedUrl,
  createYoutrustSendSignatureJob,
  documentRemplace,
  enregistrerCanalDuMandant,
  loadFichesDesSignataires,
  photoSignatairesDuDocument,
  type CorrectionSignataire,
  type FicheSignataire,
} from './lib/api'
import { ceQuiAChange, ecartsAvecLaFiche, type FicheDuJourPdf } from './lib/ecartsFichePdf'
import type { ConsoleDocument, ConsoleJob, Dossier } from './types'
import './envoi-signature.css'

// Memes regles que le worker (emailSignataireValide, portableE164) : l'ecran ne laisse pas partir ce qu'il refuserait.
const emailValide = (email: string | null | undefined) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(email ?? '').trim())
function portableValide(numero: string | null | undefined) {
  let n = String(numero ?? '').replace(/[^\d+]/g, '')
  if (!n) return false
  if (n.startsWith('00')) n = `+${n.slice(2)}`
  if (/^0[67]\d{8}$/.test(n)) n = `+33${n.slice(1)}`
  return /^\+33[67]\d{8}$/.test(n) || /^\+(?!33)\d{8,15}$/.test(n)
}
const NATURES_CONJOINT = new Set(['conjoint', 'conjoint_sans_prenom'])
const masquer = (tel: string) => { const d = tel.replace(/\D/g, ''); return d.length >= 4 ? `•• ${d.slice(-4, -2)} ${d.slice(-2)}` : tel }

type Saisie = { email?: string; telephone?: string }
export type OngletCorrection = 'mandants' | 'bien' | 'prix' | 'clauses' | 'apercu'
// P5 : le panneau Documents n'a pas l'editeur sous la main ; il demande a l'editeur DU MEME BIEN de s'ouvrir.
// Le premier editeur monte qui repond met `pris` a vrai (un seul s'ouvre) ; personne -> la fenetre le dit.
export const EVENEMENT_CORRIGER_MANDAT = 'hektor:corriger-mandat'
export type DemandeCorrectionMandat = { app_dossier_id: Dossier['app_dossier_id']; document: ConsoleDocument; onglet: OngletCorrection; pris: boolean }

export default function EnvoiSignatureYoutrust(props: {
  document: ConsoleDocument
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'negociateur_email' | 'commercial_nom' | 'numero_mandat'>
  adresse?: string | null
  onClose: () => void
  onSent?: (job: ConsoleJob) => void
  // P5 : rouvre l'editeur sur l'onglet donne ; rend false si aucun editeur n'a pu s'ouvrir (la fenetre le dit).
  onCorriger?: (onglet: OngletCorrection) => boolean | void
  // P5 : le PDF que ce document remplace (retour d'une regeneration), relu apres la marque du worker.
  ancien?: ConsoleDocument | null
  // P6 : ce que la fiche du bien dirait aujourd'hui (absent = pas de comparaison : PDF tout juste genere, fiche inconnue).
  ficheDuJour?: FicheDuJourPdf | null
}) {
  const photo = useMemo(() => photoSignatairesDuDocument(props.document), [props.document])
  const remplace = documentRemplace(props.document)
  const ecarts = useMemo(() => ecartsAvecLaFiche(photo, contenuImprimeDuDocument(props.document), props.ficheDuJour ?? null),
    [photo, props.document, props.ficheDuJour])
  const ficheAChange = ecarts.lignes.length > 0
  const [confirmerEcarts, setConfirmerEcarts] = useState(false)
  const diff = useMemo(() => (props.ancien
    ? ceQuiAChange(photoSignatairesDuDocument(props.ancien), photo, contenuImprimeDuDocument(props.ancien), contenuImprimeDuDocument(props.document))
    : null), [props.ancien, props.document, photo])
  const [corrigerImpossible, setCorrigerImpossible] = useState(false)
  const corriger = (onglet: OngletCorrection) => {
    if (!props.onCorriger) return
    setCorrigerImpossible(props.onCorriger(onglet) === false)
  }
  const kind: 'mandat' | 'avenant' = /avenant/i.test(props.document.document_name || '') ? 'avenant' : 'mandat'
  const [fiches, setFiches] = useState<Map<string, FicheSignataire>>(new Map())
  const [saisies, setSaisies] = useState<Record<number, Saisie>>({})
  const [edition, setEdition] = useState<{ rang: number; champ: 'email' | 'telephone' } | null>(null)
  const [brouillon, setBrouillon] = useState('')
  const [bulle, setBulle] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [fait, setFait] = useState<{ avertissements: string[] } | null>(null)

  useEffect(() => {
    if (!photo) return
    let annule = false
    loadFichesDesSignataires(photo.mandants.map((m) => String(m.hektor_contact_id ?? '')))
      .then((map) => { if (!annule) setFiches(map) })
      .catch(() => { /* sans fiche, on ne sait pas qui est conjoint : l'enregistrement sur la fiche sera simplement saute */ })
    return () => { annule = true }
  }, [photo])

  useEffect(() => {
    const echap = (event: KeyboardEvent) => { if (event.key === 'Escape' && !busy) { if (edition) setEdition(null); else if (bulle != null) setBulle(null); else props.onClose() } }
    window.addEventListener('keydown', echap)
    return () => window.removeEventListener('keydown', echap)
  }, [busy, edition, bulle, props])

  const valeur = (rang: number, champ: 'email' | 'telephone') => {
    const s = saisies[rang]
    if (s && s[champ] !== undefined) return s[champ] ?? ''
    const m = photo?.mandants.find((x) => x.rang === rang)
    return (m?.[champ] ?? '') || ''
  }
  const mandantsPrets = (photo?.mandants ?? []).map((m) => ({ m, email: valeur(m.rang, 'email'), tel: valeur(m.rang, 'telephone') }))
  const manques = mandantsPrets.filter((x) => !emailValide(x.email)).map((x) => [x.m.civilite, x.m.prenom, x.m.nom].filter(Boolean).join(' '))
  const nomComplet = (m: { civilite: string | null; prenom: string | null; nom: string | null }) => [m.civilite, m.prenom, m.nom].filter(Boolean).join(' ') || '—'

  const ouvrirPdf = async () => {
    try {
      const url = await createConsoleDocumentSignedUrl(props.document)
      window.open(url, '_blank', 'noopener,noreferrer')
    } catch (e) {
      setErreur(e instanceof Error ? e.message : 'Impossible d’ouvrir le PDF')
    }
  }
  const commencer = (rang: number, champ: 'email' | 'telephone') => { setBulle(null); setEdition({ rang, champ }); setBrouillon(valeur(rang, champ)) }
  const valider = () => {
    if (!edition) return
    const v = brouillon.trim()
    if (edition.champ === 'email' && v && !emailValide(v)) { setErreur('Cette adresse e-mail n’est pas valide.'); return }
    if (edition.champ === 'telephone' && v && !portableValide(v)) { setErreur('Ce numéro n’est pas un portable (06, 07 ou un numéro étranger).'); return }
    setErreur(null)
    setSaisies((cur) => ({ ...cur, [edition.rang]: { ...cur[edition.rang], [edition.champ]: v } }))
    setEdition(null)
  }

  const envoyer = async () => {
    if (!photo || busy || manques.length || remplace) return
    setBusy(true)
    setErreur(null)
    const corrections: CorrectionSignataire[] = []
    for (const m of photo.mandants) {
      const s = saisies[m.rang]
      if (!s) continue
      const c: CorrectionSignataire = { rang: m.rang }
      if (s.email !== undefined && s.email !== (m.email ?? '')) c.email = s.email
      if (s.telephone !== undefined && s.telephone !== (m.telephone ?? '')) c.telephone = s.telephone
      if (c.email !== undefined || c.telephone !== undefined) corrections.push(c)
    }
    const avertissements: string[] = []
    // D33 : enregistrer sur la fiche ce qui a ete complete (jamais pour un conjoint, jamais sans fiche connue).
    for (const c of corrections) {
      const m = photo.mandants.find((x) => x.rang === c.rang)!
      const numero = String(m.hektor_contact_id ?? '')
      const fiche = fiches.get(numero)
      const qui = nomComplet(m)
      if (!fiche) { avertissements.push(`${qui} : fiche introuvable, la correction part seulement dans la demande.`); continue }
      if (NATURES_CONJOINT.has(String(fiche.nature_fiche ?? ''))) {
        avertissements.push(`${qui} est un conjoint : reportez la correction par « Modifier le conjoint », depuis la fiche principale.`)
        continue
      }
      try {
        await enregistrerCanalDuMandant({
          dossier: props.dossier,
          numeroHektor: numero,
          nomActuel: fiche.nom || m.nom || '',
          email: c.email ?? valeur(m.rang, 'email'),
          portable: c.telephone ?? null,
        })
      } catch (e) {
        avertissements.push(`${qui} : la fiche n'a pas pu être mise à jour (${e instanceof Error ? e.message : 'erreur'}) ; la correction part quand même dans la demande.`)
      }
    }
    try {
      const job = await createYoutrustSendSignatureJob({
        document: props.document,
        kind,
        numeroMandat: props.dossier.numero_mandat ?? null,
        bienAdresse: props.adresse ?? null,
        corrections,
        // P6 : envoye malgre une fiche changee -- le choix est ecrit dans la demande (et au journal par le worker).
        ...(ficheAChange ? { ecartsAcceptes: ecarts.lignes.map((l) => `${l.k} : ${l.avant ?? ''}${l.apres !== undefined ? ` (fiche : ${l.apres})` : ''}${l.plus ?? ''}${l.moins ?? ''}${l.note ? ` ${l.note}` : ''}`.trim()) } : {}),
      })
      props.onSent?.(job)
      setFait({ avertissements })
    } catch (e) {
      setErreur(e instanceof Error ? e.message : 'La demande d’envoi n’a pas pu être créée.')
    } finally {
      setBusy(false)
    }
  }

  const casesTotal = photo ? photo.mandants.length + 1 : 0
  const genereLe = (props.document.metadata_json as { cree_le?: string } | null)?.cree_le || photo?.pris_le
  const dateGen = genereLe ? new Date(genereLe).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : null
  const heure = (iso?: string | null) => (iso ? new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '?')
  const ancienGenere = props.ancien ? ((props.ancien.metadata_json as { cree_le?: string } | null)?.cree_le || photoSignatairesDuDocument(props.ancien)?.pris_le) : null
  const ancienMarque = props.ancien ? documentRemplace(props.ancien) : null
  const bloque = !photo || !photo.valide || Boolean(remplace)

  return (
    <div className="ens-voile" role="dialog" aria-modal="true" aria-label="Envoyer en signature" onClick={() => { if (!busy) props.onClose() }}>
      <div className="ens-modale" onClick={(event) => event.stopPropagation()}>
        <div className="ens-tete">
          <span className="ens-ico" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M4 12l16-8-6 16-2-6z" /></svg></span>
          <div className="ens-titre">
            <strong>Envoyer en signature <span className="ens-yt">● Youtrust</span></strong>
            <small>{props.adresse || props.document.document_name}</small>
          </div>
          <button type="button" className="ens-fermer" onClick={props.onClose} disabled={busy}>Fermer</button>
        </div>

        <div className="ens-corps">
          <div className="ens-pdf">
            <span className="ens-feuille" aria-hidden="true" />
            <div className="ens-pdf-txt">
              <b>{props.document.document_name}</b>
              <small>{[dateGen ? `Généré le ${dateGen}` : null, photo ? `${casesTotal} case${casesTotal > 1 ? 's' : ''} de signature` : null].filter(Boolean).join(' · ')}</small>
            </div>
            <div className="ens-pdf-act">
              <button type="button" className="ens-btn sec" onClick={() => void ouvrirPdf()} disabled={!props.document.storage_path}
                title={props.document.storage_path ? 'Ouvrir le PDF' : 'Ce PDF n’a de copie que sur le serveur'}>Voir le PDF</button>
              {props.onCorriger && !fait && !remplace ? (
                <button type="button" className="ens-btn sec" onClick={() => corriger('mandants')} disabled={busy}
                  title="Rouvre l’éditeur du mandat : corriger, puis régénérer et revenir ici">✎ Corriger le mandat</button>
              ) : null}
            </div>
          </div>
          {corrigerImpossible ? (
            <div className="ens-bandeau info">L’éditeur du mandat n’est pas ouvert sur cet écran : ouvrez-le depuis la rubrique <b>Mandat</b> du bien, corrigez, puis régénérez.</div>
          ) : null}

          {props.ancien && !fait ? (
            <>
              {ancienMarque ? (
                <div className="ens-bandeau ok"><b>Nouveau mandat généré à {heure(genereLe)}.</b> L’ancien ({heure(ancienGenere)}) est gardé dans les documents, marqué « remplacé, jamais envoyé ».</div>
              ) : (
                <div className="ens-bandeau alerte"><b>Nouveau mandat généré à {heure(genereLe)}</b>, mais l’ancien ({heure(ancienGenere)}) n’a pas pu être marqué « remplacé » : il reste dans les documents, ne l’envoyez pas.</div>
              )}
              {diff ? (
                <div className="ens-diff">
                  <h3>Ce qui a changé depuis le PDF de {heure(ancienGenere)}</h3>
                  {diff.lignes.length ? diff.lignes.map((l, i) => (
                    <div key={i} className="ens-d">
                      <span className="ens-k">{l.k}</span>
                      {l.avant !== undefined ? <><s>{l.avant}</s> → <span className="ens-n">{l.apres}</span></> : null}
                      {l.plus ? <span className="ens-n">{l.plus}</span> : null}
                      {l.moins ? <span className="ens-moins">{l.moins}</span> : null}
                      {l.note ? <span className="ens-note">{l.note}</span> : null}
                    </div>
                  )) : <div className="ens-note">Rien n’a changé dans {diff.compare ? 'ce qui est imprimé' : 'les signataires'}.</div>}
                  <div className="ens-note">{diff.compare
                    ? (diff.lignes.length ? 'Tout le reste de ce qui est imprimé est identique.' : null)
                    : 'Le contenu de l’ancien PDF n’est pas connu (généré avant le 05/11) : seuls les signataires sont comparés.'}</div>
                </div>
              ) : null}
            </>
          ) : null}

          {ficheAChange && !fait && !remplace && photo?.valide ? (
            <div className="ens-diff ens-fiche-change">
              <h3>⚠ La fiche a changé depuis ce PDF{dateGen ? ` (généré le ${dateGen})` : ''}</h3>
              {ecarts.lignes.map((l, i) => (
                <div key={i} className="ens-d">
                  <span className="ens-k">{l.k}</span>
                  {l.avant !== undefined ? <><span>PDF : <s>{l.avant}</s></span> → <span className="ens-n">fiche : {l.apres}</span></> : null}
                  {l.plus ? <span className="ens-n">{l.plus}</span> : null}
                  {l.moins ? <span className="ens-moins">{l.moins}</span> : null}
                  {l.note ? <span className="ens-note">{l.note}</span> : null}
                </div>
              ))}
              <div className="ens-note">Le PDF, lui, ne le dit pas. Régénérez-le pour qu’il suive la fiche{!ecarts.prixCompare ? ' (PDF généré avant le 05/11 : seuls les mandants sont comparés)' : ''}.</div>
            </div>
          ) : null}
          {confirmerEcarts && ficheAChange && !fait ? (
            <div className="ens-bandeau alerte">
              <b>Envoyer le PDF{dateGen ? ` du ${dateGen}` : ''} tel qu’il est</b> — {ecarts.resume.join(', ')} ? Ce choix est écrit dans la demande d’envoi.
            </div>
          ) : null}

          {remplace ? (
            <div className="ens-bandeau alerte">
              <b>Ce PDF a été remplacé</b> le {new Date(remplace.le).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })} par une version régénérée : il ne part plus en signature. Envoyez le nouveau mandat.
            </div>
          ) : !photo || !photo.valide ? (
            <div className="ens-bandeau alerte">
              <b>Ce PDF ne peut pas partir en signature.</b>{' '}
              {!photo
                ? 'Il n’a pas été fait par l’éditeur avec ses cases de signature : régénérez le mandat depuis l’éditeur, puis envoyez-le.'
                : `Il ne correspond pas à ses mandants (${photo.problemes.join(' ; ') || 'photo invalide'}) : régénérez le mandat.`}
            </div>
          ) : fait ? (
            <div className="ens-fait">
              <div className="ens-bandeau ok"><b>Envoi demandé.</b> Youtrust prévient les mandants par e-mail ; vous signerez après eux. Le suivi apparaît sur le document.</div>
              {fait.avertissements.map((a) => <div key={a} className="ens-bandeau info">{a}</div>)}
            </div>
          ) : (
            <>
              <div className="ens-sec">Ils vont signer <small>lu dans le PDF : ni plus, ni moins, dans l’ordre des cases</small></div>
              <div className="ens-liste">
                {mandantsPrets.map(({ m, email, tel }) => {
                  const manque = !emailValide(email)
                  return (
                    <div key={m.rang} className={`ens-sig${manque ? ' manque' : ''}`}>
                      <span className="ens-rang">{m.rang}</span>
                      <div className="ens-qui">
                        <b>{nomComplet(m)}
                          <button type="button" className={`ens-cad${bulle === m.rang ? ' actif' : ''}`} aria-label="Imprimé dans le mandat" onClick={() => setBulle(bulle === m.rang ? null : m.rang)}>🔒</button>
                        </b>
                        <small>{m.qualite || 'Mandant'} {m.rang}</small>
                        {bulle === m.rang ? (
                          <div className="ens-bulle" role="note">
                            <b>Ce nom est imprimé dans le mandat.</b> Le corriger demande de <b>régénérer le PDF</b> : corrigez la fiche dans l’éditeur du mandat, régénérez-le, puis revenez ici.
                            <div className="ens-bulle-bt">
                              {props.onCorriger ? <button type="button" className="ens-btn prim mini" onClick={() => { setBulle(null); corriger('mandants') }}>Corriger le mandat</button> : null}
                              <button type="button" className="ens-btn clair mini" onClick={() => setBulle(null)}>{props.onCorriger ? 'Laisser tel quel' : 'Compris'}</button>
                            </div>
                          </div>
                        ) : null}
                      </div>
                      <div className="ens-canal">
                        {(['email', 'telephone'] as const).map((champ) => {
                          const v = champ === 'email' ? email : tel
                          const enCours = edition && edition.rang === m.rang && edition.champ === champ
                          const lbl = champ === 'email' ? 'E-mail' : 'Portable'
                          if (enCours) {
                            return (
                              <div key={champ} className="ens-ch edit">
                                <span className="ens-lbl">{lbl}</span>
                                <input autoFocus value={brouillon} inputMode={champ === 'telephone' ? 'tel' : 'email'} aria-label={lbl}
                                  onChange={(event) => setBrouillon(event.target.value)}
                                  onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); valider() } }} />
                                <button type="button" className="ens-btn prim mini" onClick={valider}>OK</button>
                              </div>
                            )
                          }
                          const vide = !v
                          return (
                            <button key={champ} type="button" className={`ens-ch${vide ? ' vide' : ''}${champ === 'email' && manque && !vide ? ' faux' : ''}`} onClick={() => commencer(m.rang, champ)}>
                              <span className="ens-lbl">{lbl}</span>
                              <span className="ens-val">{vide ? (champ === 'email' ? '＋ Saisir l’e-mail (obligatoire)' : '＋ Ajouter un portable') : v}</span>
                              <span className="ens-cr" aria-hidden="true">✎</span>
                            </button>
                          )
                        })}
                      </div>
                      <div className="ens-otp">{portableValide(tel) ? `Code par SMS au ${masquer(tel)}` : 'Code par e-mail'}</div>
                      <span className={`ens-etat ${manque ? 'ko' : 'ok'}`}>{manque ? '⚠ E-mail' : '✓ Prêt'}</span>
                    </div>
                  )
                })}
                <div className="ens-sig nego">
                  <span className="ens-rang">{casesTotal}</span>
                  <div className="ens-qui"><b>{props.dossier.commercial_nom || 'Le négociateur du bien'}</b><small>Mandataire · signe en dernier</small></div>
                  <div className="ens-canal"><div className="ens-note">Le négociateur du bien s’il est actif, sinon vous.</div></div>
                  <div className="ens-otp" />
                  <span className="ens-etat nego">Ensuite</span>
                </div>
              </div>
              <div className="ens-note">🔒 imprimé dans le mandat : ne se change pas ici · ✎ canal de remise : se corrige ici et s’enregistre sur la fiche, sans toucher au PDF.</div>
            </>
          )}
          {erreur ? <div className="ens-bandeau alerte">{erreur}</div> : null}
        </div>

        <div className="ens-pied">
          {fait ? (
            <><span className="ens-esp" /><button type="button" className="ens-gros envoi" onClick={props.onClose}>Fermer</button></>
          ) : (
            <>
              <span className="ens-note">{remplace ? 'Ce PDF est remplacé : envoyez le nouveau.' : !photo || !photo.valide ? 'Régénérez le mandat dans l’éditeur.' : manques.length ? <>L’envoi attend <b>l’e-mail de {manques.join(', ')}</b>.</> : ficheAChange ? <>La fiche a changé depuis ce PDF · <b>{casesTotal} crédit{casesTotal > 1 ? 's' : ''}</b> s’il part tel quel.</> : <>Tout le monde est prêt · <b>{casesTotal} crédit{casesTotal > 1 ? 's' : ''}</b> Youtrust (un par signataire).</>}</span>
              <span className="ens-esp" />
              {ficheAChange && !bloque && !confirmerEcarts ? (
                <>
                  <button type="button" className="ens-gros sec" onClick={() => setConfirmerEcarts(true)} disabled={busy || manques.length > 0}>Envoyer quand même…</button>
                  {props.onCorriger ? <button type="button" className="ens-gros envoi" onClick={() => corriger('mandants')} disabled={busy}>↻ Régénérer avant d’envoyer</button> : null}
                </>
              ) : ficheAChange && !bloque ? (
                <>
                  <button type="button" className="ens-gros sec" onClick={() => setConfirmerEcarts(false)} disabled={busy}>Annuler</button>
                  <button type="button" className="ens-gros envoi" onClick={() => void envoyer()} disabled={busy || manques.length > 0}>{busy ? 'Envoi…' : 'Oui, envoyer ce PDF tel quel'}</button>
                </>
              ) : (
                <button type="button" className="ens-gros envoi" onClick={() => void envoyer()} disabled={busy || bloque || manques.length > 0}>
                  {busy ? 'Envoi…' : 'Envoyer en signature'}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
