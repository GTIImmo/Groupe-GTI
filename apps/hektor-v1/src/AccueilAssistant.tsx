import { Fragment, useCallback, useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import {
  RefusAssistant, listerConversations, poserQuestion, refuserCarte, relireConversation, validerCarte,
  type CarteAssistant, type ConversationAssistant, type EvenementFlux,
} from './lib/assistant'
import { EVENEMENT_ASSISTANT_OUVRIR, prendreDemandeConversation, signalerChangementAssistant } from './RailAssistant'
import './accueil-assistant.css'

// ─────────────────────────────────────────────────────────────────────────────
// Étape 4 de l'assistant IA, lot 2 (17/11/2026) -- L'ÉCRAN DE L'ASSISTANT, qui devient l'Accueil.
// Maquette VALIDÉE le 17/11 : planche 1 (l'accueil), 3 (la conversation), 6 (les fins d'une carte), 23 (les blocages).
// Audit et plan : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §13.
//
// ⛔ L'écran ne décide RIEN : la carte affiche la phrase que le serveur a écrite, le clic appelle le serveur, qui revérifie
//   tout (rôle, expiration, conditions) et exécute avec le jeton de la personne. Une phrase de blocage est celle du serveur.
// ⛔ Le tableau de bord d'aujourd'hui reste à un clic (« Tableau de bord »), rendu tel quel par l'appelant.
// Hors de ce lot : les liens vers les fiches et la relecture après « Valider » (lot 3), « Citer un bien » (lot 4).
// ─────────────────────────────────────────────────────────────────────────────

export type ChiffresAccueil = {
  demandes: { nombre: number; premiere?: { titre: string; depuis: string | null } }
  expirants: number
  bloquees: number
  erreurs: number
}

type CarteEcran = CarteAssistant & { detail?: string }
type Trace = { nom: string | null; fini: boolean }
type Tour = {
  cle: string
  question: string
  traces: Trace[]
  texte: string
  cartes: CarteEcran[]
  etat: 'flux' | 'fini' | 'coupe' | 'erreur' | 'arrete'
  detail?: string
  enregistre?: boolean
}
type Blocage = { genre: 'info' | 'pause' | 'ko' | 'net'; titre: string; sous?: string; renvoyer?: string }
type Mode = { type: 'accueil' } | { type: 'conversation' } | { type: 'toutes' }

// Les gestes : l'en-tête de la carte et la phrase de fin (le serveur ne rend que des numéros).
const GESTES: Record<string, { titre: string; fait: (r: Record<string, unknown>) => string; suite?: string }> = {
  demande_direction: { titre: 'Demande à la direction', fait: () => 'Demande envoyée.', suite: 'Elle attend la direction dans Suivi.' },
  creer_relance: { titre: 'Relance', fait: () => 'Relance créée.' },
  statut_relance: { titre: 'Relance', fait: () => 'Relance mise à jour.' },
  bien_propose: { titre: 'Bien proposé', fait: () => 'Proposition notée.' },
  statut_bien: { titre: 'Bien proposé', fait: () => 'Retour noté.' },
  notifications_lues: { titre: 'Notifications', fait: () => 'Notifications marquées lues.' },
  note_transaction: { titre: 'Note de transaction', fait: () => 'Note enregistrée.' },
  transaction: { titre: 'Transaction', fait: () => 'Transaction mise à jour.' },
  modifier_contact: { titre: 'Contact', fait: () => 'Contact modifié.' },
  archiver_contact: { titre: 'Contact', fait: (r) => (r.archive === false ? 'Contact réactivé.' : 'Contact archivé.') },
  archiver_recherche: { titre: 'Recherche', fait: () => 'Recherche archivée.' },
  creer_rdv: { titre: 'Rendez-vous', fait: () => 'Rendez-vous posé.' },
  deplacer_rdv: { titre: 'Rendez-vous', fait: () => 'Rendez-vous déplacé.' },
  supprimer_rdv: { titre: 'Rendez-vous', fait: () => 'Rendez-vous supprimé.' },
  email_interne: { titre: 'E-mail interne', fait: () => 'E-mail envoyé.' },
  email_client: { titre: 'E-mail au client', fait: () => 'E-mail envoyé.' },
  envoyer_rapprochement: { titre: 'Rapprochement', fait: () => 'Sélection envoyée.' },
  rdv_client: { titre: 'Rendez-vous client', fait: () => 'Rendez-vous posé.' },
  modifier_bien: { titre: 'Bien', fait: () => 'Bien modifié.' },
  couverture_photo: { titre: 'Photos', fait: () => 'Couverture changée.' },
  visibilite_photo: { titre: 'Photos', fait: (r) => (r.visible === true ? 'Photo affichée.' : r.visible === false ? 'Photo masquée.' : 'Photo mise à jour.') },
  deplacer_photo: { titre: 'Photos', fait: () => 'Photo déplacée.' },
  portail: { titre: 'Diffusion', fait: () => 'Diffusion mise à jour.' },
  creer_contact: { titre: 'Nouveau contact', fait: () => 'Contact créé.' },
  ajouter_recherche: { titre: 'Recherche', fait: () => 'Recherche ajoutée.' },
  modifier_recherche: { titre: 'Recherche', fait: () => 'Recherche modifiée.' },
}

// Les traces : le serveur envoie le NOM de la fonction appelée ; l'écran le dit en français, en cours puis fini.
const TRACES: Record<string, [string, string]> = {
  qui_suis_je: ['Je regarde ton profil…', 'Profil lu'],
  decrire: ['Je regarde les données…', 'Données repérées'],
  chercher: ['Je cherche…', 'Recherche faite'],
  compter: ['Je compte…', 'Comptage fait'],
  fiches_biens: ['Je lis les fiches…', 'Fiches lues'],
  notes_transaction: ['Je lis les notes…', 'Notes lues'],
  agenda: ["Je lis l'agenda…", 'Agenda lu'],
  lire_mon_agenda: ["Je lis l'agenda…", 'Agenda lu'],
  apercu_rapprochement: ['Je prépare le rapprochement…', 'Rapprochement lu'],
  lire_photos_bien: ['Je lis les photos…', 'Photos lues'],
  lire_portails_bien: ['Je lis les portails…', 'Portails lus'],
  rediger_annonce: ['Je rédige…', 'Texte rédigé'],
}

function libelleTrace(nom: string | null, fini: boolean): string {
  const connu = nom ? TRACES[nom] : undefined
  if (connu) return connu[fini ? 1 : 0]
  if (nom?.startsWith('proposer_')) return fini ? 'Carte préparée' : 'Je prépare la carte…'
  return fini ? 'Lecture faite' : 'Je lis…'
}

const IDEES: Array<{ texte: string; genre: 'lecture' | 'à valider'; picto: ReactNode }> = [
  { texte: "Qu'est-ce que j'ai dans mon agenda lundi ?", genre: 'lecture', picto: <path d="M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM8 3v4M16 3v4M3 10h18" /> },
  { texte: 'Les ventes 2026 par négociateur', genre: 'lecture', picto: <path d="M4 17l5-5 4 4 7-8M15 8h5v5" /> },
  { texte: 'Les annonces sur aucun portail', genre: 'lecture', picto: <path d="M4 12h3l3-7 4 14 3-7h3" /> },
  { texte: 'Une relance vendredi pour rappeler un vendeur', genre: 'à valider', picto: <path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15zM10 20a2 2 0 0 0 4 0" /> },
  { texte: "Une autre photo en couverture de l'annonce 63289", genre: 'à valider', picto: <><rect x="3" y="5" width="18" height="14" rx="2" /><circle cx="9" cy="10" r="1.6" /><path d="m21 16-5-5-8 8" /></> },
]

const heure = (iso?: string | null) => (iso ? new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '')
const jourMois = (iso?: string | null) => (iso ? new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }) : '')
const quandConversation = (iso?: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toDateString() === new Date().toDateString() ? heure(iso) : `${jourMois(iso)} à ${heure(iso)}`
}
const pluriel = (n: number, un: string, plusieurs: string) => (n > 1 ? plusieurs : un)
const estExpiree = (c: CarteAssistant) => c.etat === 'expiree' || (c.etat === 'proposee' && !!c.expire_le && new Date(c.expire_le).getTime() < Date.now())

// ── le texte d'une réponse : paragraphes, gras, listes. Rien d'autre, et jamais de HTML injecté. ──
function EnLigne({ texte }: { texte: string }) {
  const morceaux = texte.split(/(\*\*[^*]+\*\*)/g)
  return <>{morceaux.map((m, i) => (m.startsWith('**') && m.endsWith('**') && m.length > 4 ? <strong key={i}>{m.slice(2, -2)}</strong> : <Fragment key={i}>{m}</Fragment>))}</>
}

function TexteReponse({ source, curseur }: { source: string; curseur: boolean }) {
  const blocs = source.replace(/\r/g, '').split(/\n{2,}/).filter((b) => b.trim())
  const fin = curseur ? <span className="asi-curseur" aria-hidden="true" /> : null
  if (!blocs.length) return curseur ? <p>{fin}</p> : null
  return (
    <>
      {blocs.map((bloc, i) => {
        const dernier = i === blocs.length - 1
        const lignes = bloc.split('\n').filter((l) => l.trim())
        if (lignes.every((l) => /^\s*[-*•]\s+/.test(l))) {
          return <ul key={i}>{lignes.map((l, j) => <li key={j}><EnLigne texte={l.replace(/^\s*[-*•]\s+/, '')} />{dernier && j === lignes.length - 1 ? fin : null}</li>)}</ul>
        }
        if (lignes.every((l) => /^\s*\d+[.)]\s+/.test(l))) {
          return <ol key={i}>{lignes.map((l, j) => <li key={j}><EnLigne texte={l.replace(/^\s*\d+[.)]\s+/, '')} />{dernier && j === lignes.length - 1 ? fin : null}</li>)}</ol>
        }
        return <p key={i}>{lignes.map((l, j) => <Fragment key={j}>{j ? <br /> : null}<EnLigne texte={l} /></Fragment>)}{dernier ? fin : null}</p>
      })}
    </>
  )
}

// ── les pictos ──
const Sceau = ({ coche = false }: { coche?: boolean }) => (
  <svg className={coche ? 'asi-sceau' : undefined} viewBox="11.76 7.51 76.49 84.97" aria-hidden="true">
    <path d="M50.00 24.49L79.76 54.24L88.24 45.76L50.00 7.51L11.76 45.76L20.24 54.24Z" fill={coche ? '#2f7d59' : 'currentColor'} />
    {coche
      ? <path className="asi-coche" d="M28 68 44 84 72 56" fill="none" stroke="#C5005F" strokeWidth="12" />
      : <path d="M44.00 92.49L76.24 60.24L67.76 51.76L44.00 75.51L32.24 63.76L23.76 72.24Z" fill="#C5005F" />}
  </svg>
)
const Picto = ({ children, epais = 2 }: { children: ReactNode; epais?: number }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={epais} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
)
const PictoCoche = () => <Picto epais={2.6}><path d="m5 12 5 5 9-10" /></Picto>
const PictoTourne = () => <Picto><path d="M21 12a9 9 0 1 1-6.2-8.6" /></Picto>
const PictoHorloge = () => <Picto epais={2.2}><circle cx="12" cy="12" r="8" /><path d="M12 8v4l3 2" /></Picto>

function MessageBlocage({ blocage, onRenvoyer }: { blocage: Blocage; onRenvoyer: (q: string) => void }) {
  const picto = blocage.genre === 'pause' ? <path d="M10 9v6M14 9v6M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z" />
    : blocage.genre === 'ko' ? <path d="M12 3 2 20h20zM12 10v4M12 17v.5" />
      : blocage.genre === 'net' ? <path d="M2 8.5a15 15 0 0 1 20 0M5 12a10 10 0 0 1 14 0M8.5 15.5a5 5 0 0 1 7 0M12 19h.01M3 3l18 18" />
        : <path d="M12 11v6M12 7.5v.5M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z" />
  return (
    <div className={`asi-msg is-${blocage.genre}`} role={blocage.genre === 'info' ? 'status' : 'alert'}>
      <Picto>{picto}</Picto>
      <b>{blocage.titre}</b>
      {blocage.sous ? <span className="asi-msg-s">{blocage.sous}</span> : null}
      {blocage.renvoyer ? <span className="asi-msg-act"><button className="asi-b" type="button" onClick={() => onRenvoyer(blocage.renvoyer!)}>Renvoyer</button></span> : null}
    </div>
  )
}

// La phrase du serveur devient une phrase d'écran (planche 23) ; inconnue, elle est montrée telle quelle.
function blocageDepuis(erreur: unknown, question: string): Blocage {
  if (erreur instanceof RefusAssistant) {
    const d = erreur.message
    if (erreur.statut === 403 && /éteint/i.test(d)) return { genre: 'info', titre: "L'assistant n'est pas encore ouvert pour ton compte.", sous: 'Ton tableau de bord reste à un clic.' }
    if (erreur.statut === 429 && /questions/i.test(d)) return { genre: 'pause', titre: d.includes('100') ? 'Tu as posé 100 questions aujourd\'hui.' : d, sous: "L'assistant reprend demain." }
    if (erreur.statut === 429) return { genre: 'pause', titre: "L'assistant est en pause jusqu'à demain.", sous: 'Le budget du jour est atteint, pour tout le monde.' }
    if (erreur.statut === 401) return { genre: 'ko', titre: d }
    return { genre: 'ko', titre: d, sous: 'Rien n\'a été fait.' }
  }
  return { genre: 'net', titre: "Le serveur de l'assistant ne répond pas.", sous: "Ta question n'est peut-être pas partie. Renvoie-la quand le réseau revient.", renvoyer: question }
}

function CarteVue({ carte, onValider, onRefuser }: { carte: CarteEcran; onValider: () => void; onRefuser: () => void }) {
  const geste = GESTES[carte.geste]
  const titre = geste?.titre ?? 'Geste à valider'
  const expiree = estExpiree(carte)
  if (carte.etat === 'proposee' && !expiree) {
    return (
      <div className="asi-carte">
        <div className="asi-c-h"><PictoHorloge />{titre}{carte.expire_le ? <span className="asi-till">à valider avant {heure(carte.expire_le)}</span> : null}</div>
        <div className="asi-c-b"><p className="asi-resume">{carte.resume}</p></div>
        {carte.detail ? <div className="asi-c-end is-ko">{carte.detail}</div> : null}
        <div className="asi-c-f">
          <button className="asi-b is-main" type="button" onClick={onValider}>Valider</button>
          <button className="asi-b" type="button" onClick={onRefuser}>Refuser</button>
          <small>Rien ne part avant ton clic.</small>
        </div>
      </div>
    )
  }
  if (carte.etat === 'en_cours') {
    return (
      <div className="asi-carte is-cours" aria-busy="true">
        <div className="asi-c-h"><PictoTourne />En cours</div>
        <div className="asi-c-b"><p className="asi-resume">{carte.resume}</p></div>
      </div>
    )
  }
  if (carte.etat === 'executee') {
    return (
      <div className="asi-carte is-faite">
        <div className="asi-c-h"><Sceau coche />Validée{carte.execute_le ? ` à ${heure(carte.execute_le)}` : ''}</div>
        <div className="asi-c-b"><p className="asi-resume">{carte.resume}</p></div>
        <div className="asi-c-end"><b>{geste ? geste.fait(carte.resultat ?? {}) : 'Fait.'}</b>{geste?.suite ? <span>{geste.suite}</span> : null}</div>
      </div>
    )
  }
  if (carte.etat === 'echec') {
    return (
      <div className="asi-carte is-ko">
        <div className="asi-c-h">Non faite</div>
        <div className="asi-c-b"><p className="asi-resume">{carte.resume}</p></div>
        <div className="asi-c-end is-ko">{carte.detail || String((carte.resultat as { raison?: string } | null)?.raison ?? '') || "Non fait : l'écriture n'a pas abouti."}</div>
      </div>
    )
  }
  return (
    <div className="asi-carte is-passee">
      <div className="asi-c-h">{carte.etat === 'refusee' ? `Refusée${carte.execute_le ? ` à ${heure(carte.execute_le)}` : ''}` : 'Expirée'}</div>
      <div className="asi-c-b"><p className="asi-resume">{carte.resume}</p></div>
      <div className="asi-c-end"><span>{carte.etat === 'refusee' ? "Rien n'a été fait." : carte.detail || "Carte expirée : redemande-la à l'assistant."}</span></div>
    </div>
  )
}

export default function AccueilAssistant(props: {
  prenom: string
  chiffres: ChiffresAccueil
  chargerRecherches: (portee: string | null) => Promise<number>
  /** null = toutes (direction), une adresse = les siennes (négociateur), undefined = rôle pas encore connu */
  porteeRecherches: string | null | undefined
  peutOuvrirSuivi: boolean
  onOuvrirSuivi: () => void
  tableauDeBord: ReactNode
}) {
  const [vue, setVue] = useState<'assistant' | 'tableau'>('assistant')
  const [mode, setMode] = useState<Mode>({ type: 'accueil' })
  const [titre, setTitre] = useState('')
  const [tours, setTours] = useState<Tour[]>([])
  const [champ, setChamp] = useState('')
  const [enCours, setEnCours] = useState(false)
  const [chargement, setChargement] = useState(false)
  const [blocage, setBlocage] = useState<Blocage | null>(null)
  const [conversations, setConversations] = useState<ConversationAssistant[] | null>(null)
  const [recherches, setRecherches] = useState<number | null>(null)
  const conversationId = useRef<string | null>(null)
  const controleur = useRef<AbortController | null>(null)
  const fil = useRef<HTMLDivElement | null>(null)
  const champRef = useRef<HTMLTextAreaElement | null>(null)

  // la même requête que le tableau de bord, une fois le RÔLE connu (porteeRecherches = undefined tant que le profil
  // n'est pas chargé : avant, un admin passait pour un négociateur et ne voyait que SES recherches, 0 au lieu de 737,
  // vu en ligne le 16/11) ; relue si la portée change ; ratée, la ligne ne s'affiche pas
  const chargerRecherches = useRef(props.chargerRecherches)
  const { porteeRecherches } = props
  useEffect(() => {
    if (porteeRecherches === undefined) return
    let annule = false
    setRecherches(null)
    chargerRecherches.current(porteeRecherches).then((n) => { if (!annule) setRecherches(n) }).catch(() => undefined)
    return () => { annule = true }
  }, [porteeRecherches])

  const majDernierTour = useCallback((fn: (t: Tour) => Tour) => {
    setTours((liste) => (liste.length ? [...liste.slice(0, -1), fn(liste[liste.length - 1])] : liste))
  }, [])

  const arreter = useCallback(() => { controleur.current?.abort() }, [])

  const nouvelle = useCallback(() => {
    arreter()
    conversationId.current = null
    setTours([])
    setTitre('')
    setBlocage(null)
    setMode({ type: 'accueil' })
    setVue('assistant')
    window.setTimeout(() => champRef.current?.focus(), 0)
  }, [arreter])

  const ouvrir = useCallback(async (id: string) => {
    arreter()
    setVue('assistant')
    setMode({ type: 'conversation' })
    setBlocage(null)
    setTours([])
    setChargement(true)
    conversationId.current = id
    try {
      const { conversation, messages, cartes } = await relireConversation(id)
      if (conversationId.current !== id) return
      setTitre(conversation.titre || 'Conversation')
      const lus: Tour[] = []
      const departs: number[] = []
      for (const m of messages) {
        if (m.role === 'user') {
          lus.push({ cle: `m${m.id}`, question: m.contenu, traces: [], texte: '', cartes: [], etat: 'coupe' })
          departs.push(new Date(m.cree_le).getTime())
        } else if (lus.length) {
          lus[lus.length - 1] = { ...lus[lus.length - 1], texte: m.contenu, etat: 'fini' }
        }
      }
      // une carte appartient au dernier tour commencé avant elle
      for (const c of cartes) {
        const t = new Date(c.cree_le ?? 0).getTime()
        let k = -1
        departs.forEach((d, i) => { if (d <= t) k = i })
        if (k >= 0) lus[k].cartes.push({ ...c, etat: estExpiree(c) ? 'expiree' : c.etat })
      }
      // une question sans réponse enregistrée : la réponse a été coupée ou n'a pas été enregistrée
      setTours(lus.map((t) => (t.etat === 'coupe' && !t.texte ? { ...t, detail: 'Pas de réponse enregistrée pour cette question.' } : t)))
    } catch (erreur) {
      setBlocage({ ...blocageDepuis(erreur, ''), renvoyer: undefined })
    } finally {
      setChargement(false)
    }
  }, [arreter])

  const montrerToutes = useCallback(async () => {
    arreter()
    setVue('assistant')
    setMode({ type: 'toutes' })
    setBlocage(null)
    setConversations(null)
    try {
      setConversations(await listerConversations())
    } catch (erreur) {
      setConversations([])
      setBlocage({ ...blocageDepuis(erreur, ''), renvoyer: undefined })
    }
  }, [arreter])

  const appliquer = useCallback((id: string | null) => {
    if (id === null) nouvelle()
    else if (id === 'toutes') void montrerToutes()
    else void ouvrir(id)
  }, [nouvelle, montrerToutes, ouvrir])

  // le rail : la demande gardée au clic (l'Accueil n'était peut-être pas monté), puis les clics suivants
  useEffect(() => {
    const demande = prendreDemandeConversation()
    if (demande) appliquer(demande.conversationId)
    const ecouter = (e: Event) => {
      prendreDemandeConversation()
      appliquer((e as CustomEvent<{ conversationId: string | null }>).detail?.conversationId ?? null)
    }
    window.addEventListener(EVENEMENT_ASSISTANT_OUVRIR, ecouter)
    return () => window.removeEventListener(EVENEMENT_ASSISTANT_OUVRIR, ecouter)
  }, [appliquer])

  useEffect(() => () => controleur.current?.abort(), [])

  // le fil suit la réponse, sauf si la personne est remontée lire plus haut
  useEffect(() => {
    const el = fil.current
    if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 160) el.scrollTop = el.scrollHeight
  }, [tours])

  const envoyer = useCallback(async (brute: string) => {
    const question = brute.trim()
    if (!question || enCours) return
    setChamp('')
    setBlocage(null)
    setVue('assistant')
    if (mode.type !== 'conversation') {
      setMode({ type: 'conversation' })
      setTitre(question.slice(0, 80))
      setTours([])
    }
    const cle = `q${Date.now()}`
    setTours((liste) => [...liste, { cle, question, traces: [], texte: '', cartes: [], etat: 'flux' }])
    const c = new AbortController()
    controleur.current = c
    setEnCours(true)
    const surEvenement = (e: EvenementFlux) => {
      if (e.type === 'debut') conversationId.current = e.conversationId
      else if (e.type === 'texte') majDernierTour((t) => ({ ...t, texte: t.texte + e.delta }))
      else if (e.type === 'outil') majDernierTour((t) => ({ ...t, traces: [...t.traces.map((x) => ({ ...x, fini: true })), { nom: e.nom, fini: false }] }))
      else if (e.type === 'carte') majDernierTour((t) => ({ ...t, cartes: [...t.cartes, { id: e.id, geste: e.geste, resume: e.resume, expire_le: e.expire_le, etat: 'proposee' }] }))
      else if (e.type === 'fin') majDernierTour((t) => ({ ...t, etat: 'fini', enregistre: e.enregistre, traces: t.traces.map((x) => ({ ...x, fini: true })) }))
      else if (e.type === 'erreur') majDernierTour((t) => ({ ...t, etat: 'erreur', detail: e.detail, traces: t.traces.map((x) => ({ ...x, fini: true })) }))
    }
    try {
      const fini = await poserQuestion(question, conversationId.current, surEvenement, c.signal)
      if (!fini) {
        if (c.signal.aborted) majDernierTour((t) => ({ ...t, etat: 'arrete', traces: t.traces.map((x) => ({ ...x, fini: true })) }))
        else {
          majDernierTour((t) => ({ ...t, etat: 'coupe', traces: t.traces.map((x) => ({ ...x, fini: true })) }))
          setBlocage({ genre: 'net', titre: "La connexion s'est coupée pendant la réponse.", sous: 'Ta question est enregistrée. Renvoie-la quand le réseau revient.', renvoyer: question })
        }
      }
    } catch (erreur) {
      if (c.signal.aborted) majDernierTour((t) => ({ ...t, etat: 'arrete' }))
      else {
        // refusée avant le flux : la question n'a pas été posée, on la retire du fil et on la rend au champ
        setTours((liste) => liste.filter((t) => t.cle !== cle))
        setChamp(question)
        setBlocage(blocageDepuis(erreur, question))
      }
    } finally {
      if (controleur.current === c) controleur.current = null
      setEnCours(false)
      signalerChangementAssistant()
    }
  }, [enCours, mode.type, majDernierTour])

  // si la question refusée était la première, on revient à l'accueil plutôt qu'à un fil vide
  useEffect(() => {
    if (mode.type === 'conversation' && !tours.length && !chargement && !enCours && blocage && !conversationId.current) setMode({ type: 'accueil' })
  }, [mode.type, tours.length, chargement, enCours, blocage])

  const majCarte = useCallback((id: string, fn: (c: CarteEcran) => CarteEcran) => {
    setTours((liste) => liste.map((t) => (t.cartes.some((c) => c.id === id) ? { ...t, cartes: t.cartes.map((c) => (c.id === id ? fn(c) : c)) } : t)))
  }, [])

  const agirSurCarte = useCallback(async (carte: CarteEcran, geste: 'valider' | 'refuser') => {
    majCarte(carte.id, (c) => ({ ...c, etat: geste === 'valider' ? 'en_cours' : c.etat, detail: undefined }))
    try {
      const r = geste === 'valider' ? await validerCarte(carte.id) : await refuserCarte(carte.id)
      const maintenant = new Date().toISOString()
      majCarte(carte.id, (c) => ({ ...c, etat: r.etat, execute_le: maintenant, resultat: r.resultat ?? c.resultat, detail: r.ok ? undefined : r.detail }))
    } catch (erreur) {
      const d = erreur instanceof Error ? erreur.message : "Non fait : l'écriture n'a pas abouti."
      if (erreur instanceof RefusAssistant && erreur.statut === 409) {
        // la carte a changé ailleurs (expirée, déjà validée…) : la phrase du serveur, puis l'état vrai relu
        majCarte(carte.id, (c) => ({ ...c, etat: /expir/i.test(d) ? 'expiree' : c.etat === 'en_cours' ? 'proposee' : c.etat, detail: d }))
        if (conversationId.current && !/expir/i.test(d)) {
          relireConversation(conversationId.current).then(({ cartes }) => {
            const vraie = cartes.find((c) => c.id === carte.id)
            if (vraie) majCarte(carte.id, (c) => ({ ...c, ...vraie, detail: d }))
          }).catch(() => undefined)
        }
      } else {
        majCarte(carte.id, (c) => ({ ...c, etat: 'proposee', detail: erreur instanceof RefusAssistant && erreur.statut === 403 ? `${d}. Rien n'a été fait.` : `${d}` }))
      }
    } finally {
      signalerChangementAssistant()
    }
  }, [majCarte])

  const onTouche = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      void envoyer(champ)
    }
  }

  const aujourdhui = (() => {
    const t = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
    return t.charAt(0).toUpperCase() + t.slice(1)
  })()
  const pause = blocage?.genre === 'pause'

  const bascule = (
    <div className="asi-seg" role="group" aria-label="Vue de l'accueil">
      <button className={vue === 'assistant' ? 'is-on' : ''} type="button" aria-pressed={vue === 'assistant'} onClick={() => setVue('assistant')}><Sceau />Assistant</button>
      <button className={vue === 'tableau' ? 'is-on' : ''} type="button" aria-pressed={vue === 'tableau'} onClick={() => setVue('tableau')}>Tableau de bord</button>
    </div>
  )

  if (vue === 'tableau') {
    return (
      <div className="asi-tableau">
        <div className="asi-top"><span className="asi-when">{aujourdhui}</span><div className="asi-push">{bascule}</div></div>
        {props.tableauDeBord}
      </div>
    )
  }

  // ── « À traiter » : les mêmes chiffres que le tableau de bord ; les zéros tiennent sur une ligne ──
  const c = props.chiffres
  const lignes: Array<{ cle: string; n: number; titre: string; sous: string; action: string; onClick: () => void }> = []
  const zeros: string[] = []
  const versTableau = () => setVue('tableau')
  if (c.demandes.nombre > 0) {
    const p = c.demandes.premiere
    const sous = p ? `${c.demandes.nombre > 1 ? 'La plus ancienne : ' : ''}${p.titre}${p.depuis ? `, depuis le ${jourMois(p.depuis)}` : ''}` : ''
    lignes.push({ cle: 'demandes', n: c.demandes.nombre, titre: pluriel(c.demandes.nombre, 'Demande en attente', 'Demandes en attente'), sous, action: props.peutOuvrirSuivi ? 'Ouvrir Suivi' : 'Voir', onClick: props.peutOuvrirSuivi ? props.onOuvrirSuivi : versTableau })
  } else zeros.push('0 demande en attente')
  if (recherches !== null) {
    if (recherches > 0) lignes.push({ cle: 'recherches', n: recherches, titre: pluriel(recherches, 'Recherche à compléter', 'Recherches à compléter'), sous: 'Prix ou secteur manquant', action: 'Voir', onClick: versTableau })
    else zeros.push('0 recherche à compléter')
  }
  if (c.expirants > 0) lignes.push({ cle: 'expirants', n: c.expirants, titre: pluriel(c.expirants, 'Mandat qui expire', 'Mandats qui expirent'), sous: 'Sous 30 jours', action: 'Voir', onClick: versTableau })
  else zeros.push('0 mandat qui expire')
  if (c.bloquees > 0) lignes.push({ cle: 'bloquees', n: c.bloquees, titre: pluriel(c.bloquees, 'Diffusion bloquée', 'Diffusions bloquées'), sous: 'Non diffusées', action: 'Voir', onClick: versTableau })
  else zeros.push('0 diffusion bloquée')
  if (c.erreurs > 0) lignes.push({ cle: 'erreurs', n: c.erreurs, titre: pluriel(c.erreurs, 'Synchronisation en erreur', 'Synchronisations en erreur'), sous: 'À corriger', action: 'Voir', onClick: versTableau })
  else zeros.push('0 synchronisation en erreur')

  const champSaisie = (accueil: boolean) => (
    <form className="asi-ask" onSubmit={(e) => { e.preventDefault(); if (enCours) arreter(); else void envoyer(champ) }}>
      <div className="asi-ask-row">
        <textarea
          ref={champRef}
          rows={accueil ? 2 : 1}
          value={champ}
          disabled={pause}
          onChange={(e) => setChamp(e.target.value)}
          onKeyDown={onTouche}
          aria-label={accueil ? 'Ta question ou ta demande' : 'Ta réponse'}
          placeholder={pause ? "L'assistant reprend demain." : accueil ? 'Demande un chiffre, une liste, ou un geste à préparer…' : 'Réponds ou demande autre chose…'}
          autoFocus={accueil}
        />
        {enCours ? (
          <button className="asi-go is-stop" type="submit" aria-label="Arrêter la réponse"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor" /></svg></button>
        ) : (
          <button className="asi-go" type="submit" aria-label="Envoyer" disabled={pause || !champ.trim()}><Picto epais={2.3}><path d="M12 19V5M6 11l6-6 6 6" /></Picto></button>
        )}
      </div>
    </form>
  )

  if (mode.type === 'accueil') {
    return (
      <div className="asi">
        <div className="asi-top"><span className="asi-when">{aujourdhui}</span><div className="asi-push">{bascule}</div></div>
        <section className="asi-home">
          <div className="asi-home-in">
            <h1 className="asi-hi">Bonjour{props.prenom ? ` ${props.prenom}` : ''}, on commence par quoi ?</h1>
            {blocage ? <MessageBlocage blocage={blocage} onRenvoyer={(q) => void envoyer(q)} /> : null}
            {champSaisie(true)}
            <p className="asi-warn">L'assistant prépare, tu valides : rien ne s'écrit sans ton clic. Il peut se tromper, vérifie sur la fiche.</p>
            <div className="asi-cols">
              <div className="asi-box">
                <div className="asi-box-h"><h2>À traiter</h2></div>
                {lignes.map((l) => (
                  <button key={l.cle} className="asi-todo" type="button" onClick={l.onClick}>
                    <span className="asi-k">{l.n.toLocaleString('fr-FR')}</span>
                    <span><b>{l.titre}</b>{l.sous ? <span className="asi-todo-s">{l.sous}</span> : null}</span>
                    <span className="asi-open">{l.action}</span>
                  </button>
                ))}
                {zeros.length ? (
                  <div className="asi-calm"><PictoCoche /><span>{lignes.length ? "Rien d'autre" : 'Rien à traiter'} : {zeros.join(', ')}.</span></div>
                ) : null}
              </div>
              <div className="asi-box">
                <div className="asi-box-h"><h2>Demande-lui par exemple</h2></div>
                <div className="asi-ideas">
                  {IDEES.map((idee) => (
                    <button key={idee.texte} className="asi-idea" type="button" onClick={() => { setChamp(idee.texte); champRef.current?.focus() }}>
                      <Picto epais={1.8}>{idee.picto}</Picto>{idee.texte}<em>{idee.genre}</em>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    )
  }

  if (mode.type === 'toutes') {
    return (
      <div className="asi">
        <div className="asi-ctop">
          <h1>Toutes les conversations</h1>
          <div className="asi-push"><button className="asi-b is-quiet" type="button" onClick={nouvelle}><Picto><path d="M12 5v14M5 12h14" /></Picto>Nouvelle conversation</button></div>
        </div>
        <section className="asi-thread">
          <div className="asi-thread-in">
            {blocage ? <MessageBlocage blocage={blocage} onRenvoyer={() => undefined} /> : null}
            {conversations === null ? <p className="asi-vide">Je relis tes conversations…</p> : null}
            {conversations && !conversations.length && !blocage ? <p className="asi-vide">Aucune conversation pour l'instant. Pose ta première question depuis l'Accueil.</p> : null}
            {conversations?.length ? (
              <div className="asi-liste">
                {conversations.map((conv) => (
                  <button key={conv.id} className="asi-liste-l" type="button" onClick={() => void ouvrir(conv.id)}>
                    <span className="asi-liste-t">{conv.titre || 'Conversation sans titre'}</span>
                    <span className="asi-liste-d">{quandConversation(conv.maj_le)}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="asi">
      <div className="asi-ctop">
        <h1 title={titre}>{titre || 'Conversation'}</h1>
        <div className="asi-push"><button className="asi-b is-quiet" type="button" onClick={nouvelle}><Picto><path d="M12 5v14M5 12h14" /></Picto>Nouvelle conversation</button></div>
      </div>
      <section className="asi-thread" ref={fil}>
        <div className="asi-thread-in">
          {chargement ? <p className="asi-vide">Je relis la conversation…</p> : null}
          {tours.map((t, i) => {
            const dernier = i === tours.length - 1
            const ecrit = t.etat === 'flux'
            return (
              <Fragment key={t.cle}>
                <p className="asi-me">{t.question}</p>
                <div className="asi-ai">
                  <span className="asi-mk"><Sceau /></span>
                  <div className="asi-ai-b">
                    {t.traces.length ? (
                      <div className="asi-trace">
                        {t.traces.map((x, j) => (
                          <span key={j} className={`asi-tr${x.fini ? '' : ' is-live'}`}>{x.fini ? <PictoCoche /> : <PictoTourne />}{libelleTrace(x.nom, x.fini)}</span>
                        ))}
                      </div>
                    ) : ecrit && !t.texte ? <div className="asi-trace"><span className="asi-tr is-live"><PictoTourne />Je réfléchis…</span></div> : null}
                    {t.texte || (ecrit && t.traces.length) ? <div className="asi-texte"><TexteReponse source={t.texte} curseur={ecrit && dernier} /></div> : null}
                    {t.cartes.map((carte) => (
                      <CarteVue key={carte.id} carte={carte} onValider={() => void agirSurCarte(carte, 'valider')} onRefuser={() => void agirSurCarte(carte, 'refuser')} />
                    ))}
                    {t.etat === 'erreur' ? (
                      <MessageBlocage blocage={{ genre: 'ko', titre: "L'assistant n'a pas pu répondre.", sous: `${t.detail && t.detail !== "L'assistant n'a pas pu répondre" ? `${t.detail}. ` : ''}Rien n'a été fait. Repose la question, ou découpe-la en plus simple.` }} onRenvoyer={() => undefined} />
                    ) : null}
                    {t.etat === 'arrete' ? <p className="asi-note">Réponse arrêtée. Rien n'a été enregistré de cette réponse.</p> : null}
                    {t.etat === 'coupe' && t.detail ? <p className="asi-note">{t.detail}</p> : null}
                    {t.etat === 'fini' && t.enregistre === false ? (
                      <MessageBlocage blocage={{ genre: 'info', titre: 'Réponse affichée, mais pas enregistrée.', sous: "Elle ne sera pas dans l'historique de la conversation." }} onRenvoyer={() => undefined} />
                    ) : null}
                  </div>
                </div>
              </Fragment>
            )
          })}
          {blocage ? <MessageBlocage blocage={blocage} onRenvoyer={(q) => void envoyer(q)} /> : null}
        </div>
      </section>
      <div className="asi-dock">
        {champSaisie(false)}
        <p className="asi-warn">L'assistant peut se tromper : vérifie sur la fiche avant de valider.</p>
      </div>
    </div>
  )
}
