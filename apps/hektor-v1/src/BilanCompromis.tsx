// GED (17/11/2026, lot 10c) -- LA FENÊTRE « CE QUE DIT LE COMPROMIS ». Le compromis lu face à SA transaction, ligne par
// ligne (lib/gedBilanCompromis.ts) : à trancher, à ajouter, déjà tranché, d'accord. On choisit la valeur qui RESTE en la
// touchant (celle du compromis ou celle de la transaction) ; rien ne s'écrit avant « Enregistrer ».
// ⛔ Chaque ligne dit OÙ elle va (Frédéric, 17/11 : « cela dépend des champs ») : « envoyé à Hektor » passe par la modale
//   « Modifier le compromis », préremplie, où l'on valide ; « gardé chez nous » s'écrit ici (les conditions).
// Le document se montre à la page lue, dessiné dans le navigateur (même chemin que « Voir le document »).
// Lot 2 (17/11) : la même fenêtre dit « Ce que dit l'offre » (bilan.genre) ; les lignes d'une offre acceptée ou refusée
// se montrent FIGÉES (raison dite, rien à choisir), et l'offre part toujours par sa modale VISIBLE.
// Lot 3 (18/11) : la FICHE DU BIEN face à ses documents (DPE, état des risques, copropriété, Carrez) -- « La fiche » au lieu
// de « La transaction » ; les cases partent par le chemin habituel de la fiche (pas de modale), écrites par l'écran.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.28, §12.29 et §12.31.
import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { createConsoleDocumentSignedUrl } from './lib/api'
import { apercuPremierePage } from './lib/gedClassementIa'
import type { DecisionGed } from './lib/ged'
import { estGenreFiche, type BilanCompromis as Bilan, type GenreBilan, type LigneBilan } from './lib/gedBilanCompromis'
import type { ConsoleDocument } from './types'
import './BilanCompromis.css'

export type ChoixBilan = 'prendre' | 'garder'
export type ResultatBilan = { message: string; ferme: boolean }

// Les champs que Hektor connaît partent par la modale « Modifier le compromis » de l'écran principal : la fenêtre la
// DEMANDE par un événement (le panneau des documents n'a pas la modale). `pris` dit qu'un écran l'a prise en charge.
export const EVENEMENT_MODIFIER_TRANSACTION = 'ged:modifier-transaction'
export type DemandeModifierTransaction = {
  genre: GenreBilan            // lot 2 : l'onglet de la modale (Offre ou Compromis)
  app_dossier_id: number
  appAffaireId: number
  hektorAffaireId: string | null
  hektorAnnonceId: string
  lectureId: string | null
  nom: string
  lignes: LigneBilan[]
  // 17/11 (décision de Frédéric) : la modale s'ouvre CACHÉE et part toute seule (date de signature, date de l'acte,
  // séquestre) ; faux : elle s'ouvre visible, préremplie (prix, net, honoraires)
  arrierePlan: boolean
  pris: boolean
}
// Qui peut modifier une transaction (responsable ou admin) : l'écran principal répond, le panneau demande.
export const EVENEMENT_DROITS_TRANSACTION = 'ged:droits-transaction'
// Le RÉSULTAT de l'envoi en arrière-plan (la modale cachée) : la fenêtre, restée ouverte, l'affiche.
export const EVENEMENT_RESULTAT_ENVOI = 'ged:resultat-envoi'
export type ResultatEnvoi = { texte: string; erreur: boolean }
// Les champs que Hektor connaît et qui partent DIRECTEMENT (Frédéric, 17/11) : date de signature, date de l'acte,
// séquestre -- une case seule, rien à recalculer. Le prix, le net vendeur et les honoraires passent par la fenêtre de la
// transaction (Hektor ne recalcule pas le net : elle vérifie net + honoraires = prix).
export const ENVOI_DIRECT: ReadonlySet<string> = new Set(['transaction_date', 'signature_date', 'sequestration'])
// ⛔ Lot 2 : JAMAIS une ligne d'offre (« O. ») -- le chemin de l'offre construit un corps neuf et renvoie montant, date et
//   validité préremplis, sans la liste des cases touchées ni le témoin : sa modale s'ouvre visible, toujours.
export const estEnvoiDirect = (l: LigneBilan) => l.cle.startsWith('B.') && l.champModale != null && ENVOI_DIRECT.has(l.champModale)
// les mots du document, selon le genre du bilan ; `cible` : ce qu'il corrige (la transaction, ou la fiche du bien)
type Mots = { le: string; Le: string; du: string; etiquette: string; cible: string; Cible: string }
const TRANSACTION = { cible: 'la transaction', Cible: 'La transaction' }
const FICHE = { cible: 'la fiche', Cible: 'La fiche' }
export const MOTS: Record<GenreBilan, Mots> = {
  compromis: { le: 'le compromis', Le: 'Le compromis', du: 'du compromis', etiquette: 'Compromis', ...TRANSACTION },
  offre: { le: 'l\'offre', Le: 'L\'offre', du: 'de l\'offre', etiquette: 'Offre', ...TRANSACTION },
  dpe: { le: 'le DPE', Le: 'Le DPE', du: 'du DPE', etiquette: 'DPE', ...FICHE },
  erp: { le: 'l\'état des risques', Le: 'L\'état des risques', du: 'de l\'état des risques', etiquette: 'Risques', ...FICHE },
  copro_lots: { le: 'la fiche synthétique', Le: 'La fiche synthétique', du: 'de la fiche synthétique', etiquette: 'Copropriété', ...FICHE },
  copro_charges: { le: 'l\'appel de fonds', Le: 'L\'appel de fonds', du: 'de l\'appel de fonds', etiquette: 'Copropriété', ...FICHE },
  taxe: { le: 'l\'avis de taxe foncière', Le: 'L\'avis de taxe foncière', du: 'de l\'avis de taxe foncière', etiquette: 'Taxe foncière', ...FICHE },
  copro_ag: { le: 'le procès-verbal d\'assemblée générale', Le: 'Le procès-verbal d\'assemblée générale', du: 'du procès-verbal d\'assemblée générale', etiquette: 'Copropriété', ...FICHE },
  surface: { le: 'le métré', Le: 'Le métré', du: 'du métré', etiquette: 'Surfaces', ...FICHE },
  ddt: { le: 'le dossier de diagnostics', Le: 'Le dossier de diagnostics', du: 'du dossier de diagnostics', etiquette: 'Diagnostics', ...FICHE },
  diag_electricite: { le: 'le diagnostic électricité', Le: 'Le diagnostic électricité', du: 'du diagnostic électricité', etiquette: 'Électricité', ...FICHE },
  diag_gaz: { le: 'le diagnostic gaz', Le: 'Le diagnostic gaz', du: 'du diagnostic gaz', etiquette: 'Gaz', ...FICHE },
  diag_plomb: { le: 'le constat plomb', Le: 'Le constat plomb', du: 'du constat plomb', etiquette: 'Plomb', ...FICHE },
  diag_termites: { le: 'l\'état termites', Le: 'L\'état termites', du: 'de l\'état termites', etiquette: 'Termites', ...FICHE },
  diag_amiante: { le: 'le repérage amiante', Le: 'Le repérage amiante', du: 'du repérage amiante', etiquette: 'Amiante', ...FICHE },
  diag_assainissement: { le: 'le contrôle d\'assainissement', Le: 'Le contrôle d\'assainissement', du: 'du contrôle d\'assainissement', etiquette: 'Assainissement', ...FICHE },
}

const jjmm = (iso: string) => new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })
const lu = (iso: string | null) => (iso ? new Date(iso).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).replace(' ', ' à ') : null)

// ce qu'une décision passée dit, en clair (le journal ne garde que « remplie » / « ignorée »)
function dejaDit(l: LigneBilan, d: DecisionGed): string {
  const quand = jjmm(d.le)
  if (d.decision === 'echec') return `Essai du ${quand} : rien n'a été écrit`
  if (d.decision === 'ignoree') return l.etat === 'ajouter' ? `Non retenu le ${quand}` : `${l.champFiche ? 'Fiche' : 'Transaction'} gardée le ${quand}`
  if (l.destination === 'hektor') return `Envoyé à Hektor le ${quand}`
  return l.condition?.retirer ? `Condition retirée le ${quand}` : l.etat === 'ajouter' ? `Ajouté le ${quand}` : `Pris ${MOTS[l.cle.startsWith('O.') ? 'offre' : 'compromis'].du} le ${quand}`
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
  // Frédéric (17/11) : « à trancher doit proposer de corriger le registre avec la donnée du document » -- la valeur du
  // document arrive CHOISIE sur chaque ligne à trancher (on la décoche en touchant la transaction). Rien ne part avant
  // « Enregistrer ». Lecture seule : rien n'est choisi.
  const [choix, setChoix] = useState<Map<string, ChoixBilan>>(() => new Map(peutModifier
    ? bilan.lignes.filter((l) => l.etat === 'trancher' && !l.fige && !decisions?.has(`${l.cle}|${l.valeur}`)).map((l) => [l.cle, 'prendre' as ChoixBilan])
    : []))
  const [rouvertes, setRouvertes] = useState<Set<string>>(() => new Set())
  const [enCours, setEnCours] = useState(false)
  const [message, setMessage] = useState<{ texte: string; erreur: boolean } | null>(null)
  const [accordOuvert, setAccordOuvert] = useState(false)
  const fenetre = useRef<HTMLElement | null>(null)
  const mots = MOTS[bilan.genre]

  // une décision « envoyé » dont l'envoi a ÉCHOUÉ (ou jamais parti) ne compte pas : la ligne redevient à trancher
  // (essai réel du 17/11 : « Envoyé à Hektor le 17/11 » affiché sous « le dernier envoi a échoué »)
  const decisionDe = (l: LigneBilan) => (rouvertes.has(l.cle) || l.attente === 'echec' || l.attente === 'jamais_envoye' ? undefined : decisions?.get(`${l.cle}|${l.valeur}`))
  const groupes = useMemo(() => {
    const vivantes = bilan.lignes.filter((l) => l.etat !== 'accord' && !l.fige)
    return {
      trancher: vivantes.filter((l) => l.etat === 'trancher' && !decisionDe(l)),
      ajouter: vivantes.filter((l) => l.etat === 'ajouter' && !decisionDe(l)),
      tranche: vivantes.filter((l) => decisionDe(l)),
      fige: bilan.lignes.filter((l) => l.etat !== 'accord' && l.fige),
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
  // l'envoi en arrière-plan a fini (réussi ou refusé) : on le dit ici
  useEffect(() => {
    const ecoute = (e: Event) => { const r = (e as CustomEvent<ResultatEnvoi>).detail; if (r) setMessage({ texte: r.texte, erreur: r.erreur }) }
    window.addEventListener(EVENEMENT_RESULTAT_ENVOI, ecoute)
    return () => window.removeEventListener(EVENEMENT_RESULTAT_ENVOI, ecoute)
  }, [])
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
  // le chemin vers Hektor : les dates et le séquestre partent DIRECTEMENT ; le prix, le net et les honoraires passent par
  // la fenêtre de la transaction (elle vérifie net + honoraires = prix) -- et s'il y en a un, tout passe par elle
  // (lot 3 : une case de la fiche n'ouvre aucune fenêtre -- elle part par le chemin habituel de la fiche)
  const parLaFenetre = choisies.some((l) => l.destination === 'hektor' && choix.get(l.cle) === 'prendre' && !estEnvoiDirect(l) && !l.champFiche)
  const fiche = estGenreFiche(bilan.genre)
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
    const actif = !d && l.etat !== 'accord' && !l.fige
    const plaque = (cote: 'document' | 'transaction') => {
      const valeur = cote === 'document' ? l.lu : (l.transaction ?? (l.condition ? 'non suivie' : l.attente === 'jamais_envoye' || l.attente === 'echec' ? 'pas chez Hektor' : 'vide'))
      const pris = cote === 'document' ? c === 'prendre' : c === 'garder'
      const ecarte = c != null && !pris
      const vide = cote === 'transaction' && l.transaction == null
      const titre = cote === 'document' ? mots.Le : mots.Cible
      const aria = cote === 'document'
        ? (l.condition?.retirer ? `${l.libelle} : retirer la condition` : `${l.libelle} : prendre la valeur ${mots.du}, ${l.lu}`)
        : (vide ? `${l.libelle} : laisser ${mots.cible} ${l.condition ? 'sans cette condition' : 'vide'}` : `${l.libelle} : garder la valeur de ${mots.cible}, ${valeur}`)
      // le verbe du geste, dit DANS la plaque (on comprend qu'elle se touche, et ce qu'elle fera)
      const verbe = cote === 'document'
        ? (l.condition?.retirer ? (pris ? 'retirée' : 'retirer') : l.etat === 'ajouter' ? (pris ? 'ajouté' : 'ajouter') : (pris ? 'correction' : fiche ? 'corriger la fiche' : 'corriger le registre'))
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
        <button type="button" className={`bc-plaque is-${cote}${pris ? ' is-pris' : ''}${ecarte ? ' is-ecarte' : ''}`} aria-pressed={pris} aria-label={aria} disabled={enCours} onClick={() => basculer(l, cote === 'document' ? 'prendre' : 'garder')}>{contenu}</button>
      ) : (
        <div className={`bc-plaque is-${cote} is-fixe`}>{contenu}</div>
      )
    }
    const signe = l.etat === 'accord' ? '=' : l.fige ? '≠' : l.etat === 'ajouter' ? '+' : '≠'
    return (
      <li key={l.cle} className={`bc-l is-${l.etat}${d ? ' is-tranche' : ''}${l.fige ? ' is-fige' : ''}${pageVue != null && pageVue === l.page ? ' is-vue' : ''}`} style={{ animationDelay: `${60 + i * 50}ms` }}>
        <div className="bc-l-t">
          <b>{l.libelle}</b>
          <Destination d={l.destination} />
          {l.page && document ? (
            <button type="button" className="bc-page" aria-pressed={pageVue === l.page} onClick={() => setPageVue(pageVue === l.page ? null : l.page)}>{`page ${l.page}`}</button>
          ) : null}
        </div>
        <div className="bc-l-v">
          {plaque('document')}
          <span className={`bc-signe is-${l.etat}`} aria-hidden="true">{signe}</span>
          {plaque('transaction')}
        </div>
        {l.note || d || l.fige ? (
          <p className="bc-l-n">
            {l.fige ? <span className="bc-deja">{l.fige}</span> : null}
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
  const libelleBouton = enCours ? 'Enregistrement…' : parLaFenetre ? 'Enregistrer et ouvrir la transaction' : versHektor ? 'Enregistrer et envoyer à Hektor' : 'Enregistrer'
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
            <h2 id="bc-titre">{`Ce que dit ${mots.le}`}</h2>
          </div>
          <span className="bc-hd-pil">{fiche ? 'La fiche du bien' : `Transaction : ${bilan.genre}${bilan.dateTransaction ? ` du ${jjmm(bilan.dateTransaction)}` : ''}`}</span>
          <button type="button" className="bc-hd-x" aria-label="Fermer" disabled={enCours} onClick={onFermer}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </header>

        <div className="bc-corps">
          <div className="bc-liste">
            <p className="bc-mode">
              {peutModifier
                ? 'Touche la valeur qui doit rester. Rien ne s\'écrit avant « Enregistrer ».'
                : fiche ? 'Lecture seule : tu ne modifies pas la fiche de ce bien.' : 'Lecture seule : seul un responsable modifie une transaction.'}
            </p>
            {rienAFaire && !groupes.tranche.length && !groupes.fige.length ? <p className="bc-vide">{`${mots.Le} et ${mots.cible} disent la même chose. Rien à trancher.`}</p> : null}
            {groupe('À trancher', `${mots.Le} et ${mots.cible} ne disent pas la même chose. Proposé : corriger ${fiche ? 'la fiche' : 'le registre'} avec la valeur ${mots.du} (touche ${mots.cible} pour la garder).`, groupes.trancher)}
            {groupe('À ajouter', `${mots.Cible} est vide sur ces points.`, groupes.ajouter, groupes.trancher.length)}
            {groupe('Déjà tranché', null, groupes.tranche, groupes.trancher.length + groupes.ajouter.length)}
            {groupe('Figé chez Hektor', 'Ces écarts se voient, ils ne se corrigent pas d\'ici.', groupes.fige, groupes.trancher.length + groupes.ajouter.length + groupes.tranche.length)}
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
                <p>{`${mots.Le} s'affiche ici, à la page où chaque valeur a été lue.`}</p>
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
                {apercu && typeof apercu === 'object' && 'image' in apercu ? <img className="bc-doc-page" src={apercu.image} alt={`Page ${apercu.page} ${mots.du}`} /> : null}
                {apercu && typeof apercu === 'object' && 'erreur' in apercu ? <p className="bc-doc-err">{`Pas d'aperçu : ${apercu.erreur}`}</p> : null}
              </>
            )}
          </aside>
        </div>

        <footer className="bc-pied">
          {message ? <p className={`bc-msg${message.erreur ? ' is-erreur' : ''}`} role="status">{message.texte}</p> : (
            <p className="bc-resume" aria-live="polite">
              {resume || (rienAFaire ? 'Tout est déjà tranché.' : 'Aucun choix pour l\'instant.')}
              {parLaFenetre ? <small>{bilan.genre === 'offre'
                ? 'La fenêtre de l\'offre s\'ouvre préremplie : elle renvoie à Hektor le montant, la date et la validité, tu vérifies, et c\'est elle qui envoie.'
                : 'Le prix, le net vendeur ou les honoraires changent : la fenêtre de la transaction s\'ouvre préremplie, tu vérifies, et c\'est elle qui envoie à Hektor.'}</small>
                : versHektor && fiche ? <small>Écrit sur la fiche tout de suite, puis envoyé à Hektor par le chemin habituel de la fiche (une dizaine de minutes, contrôlé au retour).</small>
                : versHektor ? <small>Envoyé à Hektor par la fenêtre de la transaction, en arrière-plan : seulement les cases corrigées, le reste ne bouge pas.</small> : null}
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
