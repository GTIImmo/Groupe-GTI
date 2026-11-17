// GED (17/11/2026, lot 10c) -- LA FENÊTRE « CE QUE DIT LE COMPROMIS ». Le compromis lu face à SA transaction, ligne par
// ligne (lib/gedBilanCompromis.ts) : à trancher, à ajouter, déjà tranché, d'accord. On choisit la valeur qui RESTE en la
// touchant (celle du compromis ou celle de la transaction) ; rien ne s'écrit avant « Enregistrer ».
// ⛔ Chaque ligne dit OÙ elle va (Frédéric, 17/11 : « cela dépend des champs ») : « envoyé à Hektor » passe par la modale
//   « Modifier le compromis », préremplie, où l'on valide ; « gardé chez nous » s'écrit ici (les conditions).
// Le document se montre à la page lue, dessiné dans le navigateur (même chemin que « Voir le document »).
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.28.
import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { createConsoleDocumentSignedUrl } from './lib/api'
import { apercuPremierePage } from './lib/gedClassementIa'
import type { DecisionGed } from './lib/ged'
import type { BilanCompromis as Bilan, LigneBilan } from './lib/gedBilanCompromis'
import type { ConsoleDocument } from './types'
import './BilanCompromis.css'

export type ChoixBilan = 'prendre' | 'garder'
export type ResultatBilan = { message: string; ferme: boolean }

// Les champs que Hektor connaît partent par la modale « Modifier le compromis » de l'écran principal : la fenêtre la
// DEMANDE par un événement (le panneau des documents n'a pas la modale). `pris` dit qu'un écran l'a prise en charge.
export const EVENEMENT_MODIFIER_TRANSACTION = 'ged:modifier-transaction'
export type DemandeModifierTransaction = {
  app_dossier_id: number
  appAffaireId: number
  hektorAffaireId: string | null
  hektorAnnonceId: string
  lectureId: string | null
  nom: string
  lignes: LigneBilan[]
  pris: boolean
}
// Qui peut modifier une transaction (responsable ou admin) : l'écran principal répond, le panneau demande.
export const EVENEMENT_DROITS_TRANSACTION = 'ged:droits-transaction'

const jjmm = (iso: string) => new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })
const lu = (iso: string | null) => (iso ? new Date(iso).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).replace(' ', ' à ') : null)

// ce qu'une décision passée dit, en clair (le journal ne garde que « remplie » / « ignorée »)
function dejaDit(l: LigneBilan, d: DecisionGed): string {
  const quand = jjmm(d.le)
  if (d.decision === 'echec') return `Essai du ${quand} : rien n'a été écrit`
  if (d.decision === 'ignoree') return l.etat === 'ajouter' ? `Non retenu le ${quand}` : `Transaction gardée le ${quand}`
  if (l.destination === 'hektor') return `Envoyé à Hektor le ${quand}`
  return l.condition?.retirer ? `Condition retirée le ${quand}` : l.etat === 'ajouter' ? `Ajouté le ${quand}` : `Pris du compromis le ${quand}`
}

function Destination({ d }: { d: LigneBilan['destination'] }) {
  return d === 'hektor' ? (
    <span className="bc-dest is-h">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8" /></svg>
      envoyé à Hektor
    </span>
  ) : (
    <span className="bc-dest is-n">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 11l8-7 8 7v9H4z" /></svg>
      gardé chez nous
    </span>
  )
}

export default function BilanCompromis({
  bilan, decisions, peutModifier, document, onFermer, onEnregistrer,
}: {
  bilan: Bilan
  decisions: Map<string, DecisionGed> | null
  peutModifier: boolean
  document: ConsoleDocument | null
  onFermer: () => void
  onEnregistrer: (choix: Array<{ ligne: LigneBilan; choix: ChoixBilan }>) => Promise<ResultatBilan>
}) {
  const [choix, setChoix] = useState<Map<string, ChoixBilan>>(() => new Map())
  const [rouvertes, setRouvertes] = useState<Set<string>>(() => new Set())
  const [enCours, setEnCours] = useState(false)
  const [message, setMessage] = useState<{ texte: string; erreur: boolean } | null>(null)
  const [accordOuvert, setAccordOuvert] = useState(false)
  const fenetre = useRef<HTMLElement | null>(null)

  const decisionDe = (l: LigneBilan) => (rouvertes.has(l.cle) ? undefined : decisions?.get(`${l.cle}|${l.valeur}`))
  const groupes = useMemo(() => {
    const vivantes = bilan.lignes.filter((l) => l.etat !== 'accord')
    return {
      trancher: vivantes.filter((l) => l.etat === 'trancher' && !decisionDe(l)),
      ajouter: vivantes.filter((l) => l.etat === 'ajouter' && !decisionDe(l)),
      tranche: vivantes.filter((l) => decisionDe(l)),
      accord: bilan.lignes.filter((l) => l.etat === 'accord'),
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bilan, decisions, rouvertes])

  // ── le document, à la page de la ligne regardée (le fichier est chargé UNE fois, chaque page dessinée à la demande) ──
  const [pageVue, setPageVue] = useState<number | null>(null)
  const [apercu, setApercu] = useState<{ image: string; page: number; nbPages: number } | { erreur: string } | 'lecture' | null>(null)
  const fichier = useRef<Blob | null>(null)
  useEffect(() => {
    if (pageVue == null || !document) return
    let annule = false
    setApercu('lecture')
    void (async () => {
      try {
        if (!fichier.current) {
          const reponse = await fetch(await createConsoleDocumentSignedUrl(document))
          if (!reponse.ok) throw new Error(`le coffre a répondu ${reponse.status}`)
          const brut = await reponse.blob()
          fichier.current = brut.type ? brut : new Blob([brut], { type: document.mime_type ?? '' })
        }
        const vue = await apercuPremierePage(fichier.current, 760, pageVue)
        if (!annule) setApercu(vue ?? { erreur: 'ce format ne se dessine pas ici.' })
      } catch (e) {
        const raison = e instanceof Error ? e.message : String(e)
        if (!annule) setApercu({ erreur: /non disponible dans le cloud/i.test(raison) ? 'le fichier n\'est pas encore au coffre : « Préparer » dans la liste des documents.' : raison })
      }
    })()
    return () => { annule = true }
  }, [pageVue, document])

  // Échap ferme (sauf pendant l'écriture) ; le focus entre dans la fenêtre à l'ouverture
  useEffect(() => { fenetre.current?.focus() }, [])
  useEffect(() => {
    const touche = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || enCours) return
      if (pageVue != null && window.matchMedia?.('(max-width: 760px)').matches) { setPageVue(null); return }
      onFermer()
    }
    window.addEventListener('keydown', touche)
    return () => window.removeEventListener('keydown', touche)
  }, [enCours, onFermer, pageVue])

  const basculer = (l: LigneBilan, c: ChoixBilan) => {
    if (!peutModifier || enCours) return
    setMessage(null)
    setChoix((avant) => { const m = new Map(avant); if (m.get(l.cle) === c) m.delete(l.cle); else m.set(l.cle, c); return m })
  }
  const choisies = bilan.lignes.filter((l) => choix.has(l.cle))
  const versHektor = choisies.filter((l) => l.destination === 'hektor' && choix.get(l.cle) === 'prendre').length
  const chezNous = choisies.filter((l) => l.destination === 'nous' && choix.get(l.cle) === 'prendre').length
  const gardees = choisies.filter((l) => choix.get(l.cle) === 'garder').length

  async function enregistrer() {
    if (!choisies.length || enCours) return
    setEnCours(true); setMessage(null)
    try {
      const r = await onEnregistrer(choisies.map((l) => ({ ligne: l, choix: choix.get(l.cle) as ChoixBilan })))
      setChoix(new Map()); setRouvertes(new Set())
      if (r.ferme) { onFermer(); return }
      setMessage({ texte: r.message, erreur: false })
    } catch (e) {
      setMessage({ texte: e instanceof Error ? e.message : 'Rien n\'a été écrit.', erreur: true })
    } finally {
      setEnCours(false)
    }
  }

  const ligneVue = (l: LigneBilan, i: number) => {
    const c = choix.get(l.cle)
    const d = decisionDe(l)
    const actif = !d && l.etat !== 'accord'
    const plaque = (cote: 'compromis' | 'transaction') => {
      const valeur = cote === 'compromis' ? l.lu : (l.transaction ?? (l.condition ? 'non suivie' : 'vide'))
      const pris = cote === 'compromis' ? c === 'prendre' : c === 'garder'
      const ecarte = c != null && !pris
      const vide = cote === 'transaction' && l.transaction == null
      const titre = cote === 'compromis' ? 'Le compromis' : 'La transaction'
      const aria = cote === 'compromis'
        ? (l.condition?.retirer ? `${l.libelle} : retirer la condition` : `${l.libelle} : prendre la valeur du compromis, ${l.lu}`)
        : (vide ? `${l.libelle} : laisser la transaction ${l.condition ? 'sans cette condition' : 'vide'}` : `${l.libelle} : garder la valeur de la transaction, ${valeur}`)
      // le verbe du geste, dit DANS la plaque (on comprend qu'elle se touche, et ce qu'elle fera)
      const verbe = cote === 'compromis'
        ? (pris ? 'pris' : l.condition?.retirer ? 'retirer' : l.etat === 'ajouter' ? 'ajouter' : 'prendre')
        : (pris ? (vide ? 'laissé vide' : 'gardé') : vide ? 'laisser vide' : 'garder')
      const contenu = (
        <>
          <small>{titre}</small>
          <b className={vide ? 'is-vide' : ''}>{valeur}</b>
          {actif && peutModifier ? (
            <span className="bc-verbe">
              {pris ? <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg> : null}
              {verbe}
            </span>
          ) : null}
        </>
      )
      return actif && peutModifier ? (
        <button type="button" className={`bc-plaque is-${cote}${pris ? ' is-pris' : ''}${ecarte ? ' is-ecarte' : ''}`} aria-pressed={pris} aria-label={aria} disabled={enCours} onClick={() => basculer(l, cote === 'compromis' ? 'prendre' : 'garder')}>{contenu}</button>
      ) : (
        <div className={`bc-plaque is-${cote} is-fixe`}>{contenu}</div>
      )
    }
    const signe = l.etat === 'accord' ? '=' : l.etat === 'ajouter' ? '+' : '≠'
    return (
      <li key={l.cle} className={`bc-l is-${l.etat}${d ? ' is-tranche' : ''}${pageVue != null && pageVue === l.page ? ' is-vue' : ''}`} style={{ animationDelay: `${60 + i * 50}ms` }}>
        <div className="bc-l-t">
          <b>{l.libelle}</b>
          <Destination d={l.destination} />
          {l.page && document ? (
            <button type="button" className="bc-page" aria-pressed={pageVue === l.page} onClick={() => setPageVue(pageVue === l.page ? null : l.page)}>{`page ${l.page}`}</button>
          ) : null}
        </div>
        <div className="bc-l-v">
          {plaque('compromis')}
          <span className={`bc-signe is-${l.etat}`} aria-hidden="true">{signe}</span>
          {plaque('transaction')}
        </div>
        {l.note || d ? (
          <p className="bc-l-n">
            {d ? <span className="bc-deja">{dejaDit(l, d)}</span> : null}
            {l.note ? <span>{l.note}</span> : null}
            {d && peutModifier ? <button type="button" className="bc-lien" onClick={() => setRouvertes((s) => new Set(s).add(l.cle))}>Changer</button> : null}
          </p>
        ) : null}
      </li>
    )
  }

  const groupe = (titre: string, aide: string | null, lignes: LigneBilan[], depart = 0) => (lignes.length ? (
    <section className="bc-g" aria-label={titre}>
      <h3>{titre}<span>{lignes.length}</span></h3>
      {aide ? <p className="bc-g-aide">{aide}</p> : null}
      <ol>{lignes.map((l, i) => ligneVue(l, depart + i))}</ol>
    </section>
  ) : null)

  const rienAFaire = !groupes.trancher.length && !groupes.ajouter.length
  const libelleBouton = enCours ? 'Enregistrement…' : versHektor ? 'Enregistrer et ouvrir la transaction' : 'Enregistrer'
  const resume = [
    versHektor ? `${versHektor} envoyé${versHektor > 1 ? 's' : ''} à Hektor` : null,
    chezNous ? `${chezNous} gardé${chezNous > 1 ? 's' : ''} chez nous` : null,
    gardees ? `${gardees} laissé${gardees > 1 ? 's' : ''} tel${gardees > 1 ? 's' : ''} quel${gardees > 1 ? 's' : ''}` : null,
  ].filter(Boolean).join(' · ')

  return createPortal(
    <div className="bc-voile" onMouseDown={(e) => { if (e.target === e.currentTarget && !enCours) onFermer() }}>
      <section ref={fenetre} className={`bc${pageVue != null ? ' a-page' : ''}`} role="dialog" aria-modal="true" aria-labelledby="bc-titre" tabIndex={-1}>
        <header className="bc-hd">
          <div className="bc-hd-t">
            <p>{[bilan.nom, lu(bilan.luLe) ? `lu le ${lu(bilan.luLe)}` : null].filter(Boolean).join(' · ')}</p>
            <h2 id="bc-titre">Ce que dit le compromis</h2>
          </div>
          <span className="bc-hd-pil">{`Transaction : compromis${bilan.dateTransaction ? ` du ${jjmm(bilan.dateTransaction)}` : ''}`}</span>
          <button type="button" className="bc-hd-x" aria-label="Fermer" disabled={enCours} onClick={onFermer}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </header>

        <div className="bc-corps">
          <div className="bc-liste">
            <p className="bc-mode">
              {peutModifier
                ? 'Touche la valeur qui doit rester. Rien ne s\'écrit avant « Enregistrer ».'
                : 'Lecture seule : seul un responsable modifie une transaction.'}
            </p>
            {rienAFaire && !groupes.tranche.length ? <p className="bc-vide">Le compromis et la transaction disent la même chose. Rien à trancher.</p> : null}
            {groupe('À trancher', 'Le compromis et la transaction ne disent pas la même chose.', groupes.trancher)}
            {groupe('À ajouter', 'La transaction est vide sur ces points.', groupes.ajouter, groupes.trancher.length)}
            {groupe('Déjà tranché', null, groupes.tranche, groupes.trancher.length + groupes.ajouter.length)}
            {!bilan.conditionsLues ? <p className="bc-vide">Les conditions suspensives de la transaction n'ont pas pu être lues : elles ne sont pas comparées.</p> : null}
            {bilan.conditionsGenerales.length ? (
              <p className="bc-generales">
                <b>{`Conditions générales du compromis : ${bilan.conditionsGenerales.join(', ')}.`}</b>
                <span>Ce ne sont pas des conditions suspensives particulières : elles ne sont ni reprises ni comparées.</span>
              </p>
            ) : null}
            {groupes.accord.length ? (
              <section className="bc-g is-accord" aria-label="D'accord">
                <button type="button" className="bc-g-plie" aria-expanded={accordOuvert} onClick={() => setAccordOuvert((v) => !v)}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
                  {`D'accord`}<span>{groupes.accord.length}</span>
                  <small>{groupes.accord.map((l) => l.libelle).join(', ')}</small>
                </button>
                {accordOuvert ? <ol>{groupes.accord.map((l, i) => ligneVue(l, i))}</ol> : null}
              </section>
            ) : null}
          </div>

          <aside className="bc-doc" aria-label="Le document">
            {pageVue == null ? (
              <div className="bc-doc-vide">
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg>
                <p>Le compromis s'affiche ici, à la page où chaque valeur a été lue.</p>
                <small>Touche « page » sur une ligne.</small>
              </div>
            ) : (
              <>
                <div className="bc-doc-t">
                  <button type="button" className="bc-doc-retour" onClick={() => setPageVue(null)} aria-label="Revenir à la liste">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
                  </button>
                  <b>{`Page ${pageVue}${apercu && typeof apercu === 'object' && 'nbPages' in apercu ? ` sur ${apercu.nbPages}` : ''}`}</b>
                </div>
                {apercu === 'lecture' ? <span className="bc-doc-page is-lit" aria-label="Page en préparation" /> : null}
                {apercu && typeof apercu === 'object' && 'image' in apercu ? <img className="bc-doc-page" src={apercu.image} alt={`Page ${apercu.page} du compromis`} /> : null}
                {apercu && typeof apercu === 'object' && 'erreur' in apercu ? <p className="bc-doc-err">{`Pas d'aperçu : ${apercu.erreur}`}</p> : null}
              </>
            )}
          </aside>
        </div>

        <footer className="bc-pied">
          {message ? <p className={`bc-msg${message.erreur ? ' is-erreur' : ''}`} role="status">{message.texte}</p> : (
            <p className="bc-resume" aria-live="polite">
              {resume || (rienAFaire ? 'Tout est déjà tranché.' : 'Aucun choix pour l\'instant.')}
              {versHektor ? <small>La fenêtre de la transaction s'ouvre préremplie : tu vérifies, tu valides, et c'est elle qui envoie à Hektor.</small> : null}
            </p>
          )}
          <button type="button" className="bc-b2" disabled={enCours} onClick={onFermer}>Fermer</button>
          {peutModifier && !rienAFaire || choisies.length ? (
            <button type="button" className="bc-b1" disabled={!choisies.length || enCours} onClick={() => void enregistrer()}>{libelleBouton}</button>
          ) : null}
        </footer>
      </section>
    </div>,
    globalThis.document.body,
  )
}
