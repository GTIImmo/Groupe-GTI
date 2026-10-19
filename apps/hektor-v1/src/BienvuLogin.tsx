// bienvu — page de connexion (lot 2). Remplace l'ancien écran UNIQUEMENT si
// VITE_APP_BIENVU_ENABLED est allumé au build (voir App.tsx). Ne contient aucune logique
// d'authentification : tout passe par les gestionnaires existants de App.tsx, inchangés.
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent, type ReactNode } from 'react'
import { BienvuLogo, BienvuSymbol } from './BienvuLogo'
import './bienvu-login.css'

const CLE_DERNIERE_METHODE = 'bienvu.derniere-methode'

function lireDerniereMethode(): string | null {
  try { return window.localStorage.getItem(CLE_DERNIERE_METHODE) } catch { return null }
}
function noterDerniereMethode(valeur: 'google' | 'mot-de-passe') {
  try { window.localStorage.setItem(CLE_DERNIERE_METHODE, valeur) } catch { /* confort, jamais bloquant */ }
}

/**
 * App.tsx n'a qu'un seul champ de message pour les erreurs ET pour les confirmations
 * (« Lien de reinitialisation envoye… », « Mot de passe mis a jour… »). L'ancien écran affichait
 * donc une confirmation en rouge. Ici on les distingue par leur début, sans toucher aux gestionnaires.
 */
export function classerMessageAuth(message: string | null): 'ok' | 'erreur' | null {
  if (!message || !message.trim()) return null
  return /^(lien de r[ée]initialisation envoy|mot de passe mis [àa] jour)/i.test(message.trim()) ? 'ok' : 'erreur'
}

export type BienvuLoginProps = {
  mode: 'connexion' | 'recuperation'
  domaine: string
  message: string | null
  // connexion
  email: string
  onEmail: (valeur: string) => void
  motDePasse: string
  onMotDePasse: (valeur: string) => void
  emailValide: (valeur: string) => boolean
  onConnexion: (event: FormEvent<HTMLFormElement>) => void
  connexionEnCours: boolean
  onGoogle: () => void
  googleEnCours: boolean
  oubliOuvert: boolean
  onOubli: (ouvert: boolean) => void
  onEnvoiLien: (event: FormEvent<HTMLFormElement>) => void
  envoiEnCours: boolean
  // récupération
  nouveauMotDePasse: string
  onNouveauMotDePasse: (valeur: string) => void
  confirmation: string
  onConfirmation: (valeur: string) => void
  onRecuperation: (event: FormEvent<HTMLFormElement>) => void
  recuperationEnCours: boolean
}

const G = (
  <svg viewBox="0 0 48 48" aria-hidden="true">
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
  </svg>
)
const EYE = <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></svg>
const EYE_OFF = <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18" /><path d="M10.6 5.1A10.7 10.7 0 0 1 12 5c6.4 0 10 7 10 7a17 17 0 0 1-3.2 4" /><path d="M6.6 6.6A16.6 16.6 0 0 0 2 12s3.6 7 10 7a10 10 0 0 0 4.4-1" /><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" /></svg>

function ChampMotDePasse(props: { id: string; libelle: string; valeur: string; onChange: (v: string) => void; autoComplete: string; avecLien?: ReactNode }) {
  const [visible, setVisible] = useState(false)
  const [majuscules, setMajuscules] = useState(false)
  const touche = (e: KeyboardEvent<HTMLInputElement>) => { if (e.getModifierState) setMajuscules(e.getModifierState('CapsLock')) }
  return (
    <div className="bvl-field">
      <div className="bvl-row">
        <label className="bvl-label" htmlFor={props.id}>{props.libelle}</label>
        {props.avecLien}
      </div>
      <div className="bvl-in">
        <input id={props.id} type={visible ? 'text' : 'password'} value={props.valeur} onChange={(e) => props.onChange(e.target.value)} onKeyDown={touche} onKeyUp={touche} onBlur={() => setMajuscules(false)} autoComplete={props.autoComplete} enterKeyHint="go" placeholder="••••••••" required />
        <button className="bvl-eye" type="button" onClick={() => setVisible((v) => !v)} aria-label={visible ? 'Masquer le mot de passe' : 'Afficher le mot de passe'} aria-pressed={visible}>{visible ? EYE_OFF : EYE}</button>
      </div>
      {majuscules ? <p className="bvl-caps" role="status"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4 5 12h4v5h6v-5h4z" /><path d="M9 20h6" /></svg>Verr. Maj est activé.</p> : null}
    </div>
  )
}

function ChampEmail(props: { id: string; libelle: string; valeur: string; onChange: (v: string) => void; domaine: string; valide: boolean; autoFocus?: boolean }) {
  return (
    <div className="bvl-field">
      <label className="bvl-label" htmlFor={props.id}>{props.libelle}</label>
      <div className={`bvl-in${props.valide ? ' is-ok' : ''}`}>
        <input id={props.id} type="email" value={props.valeur} onChange={(e) => props.onChange(e.target.value)} autoComplete="username" inputMode="email" enterKeyHint="next" autoCapitalize="none" spellCheck={false} placeholder={`prenom.nom@${props.domaine}`} required autoFocus={props.autoFocus} />
        <svg className="bvl-tick" viewBox="0 0 100 100" aria-hidden="true"><path pathLength={100} d="M22 52 L43 73 L78 30" fill="none" stroke="#c5005f" strokeWidth={12} /></svg>
      </div>
    </div>
  )
}

export function BienvuLogin(props: BienvuLoginProps) {
  const genre = classerMessageAuth(props.message)
  const [secousse, setSecousse] = useState(false)
  const [derniere, setDerniere] = useState<string | null>(null)
  // Dans bienvu l'accès se fait par Google Workspace : le mot de passe reste derrière un libellé, replié.
  // Il s'ouvre de lui-même si c'était la dernière méthode utilisée.
  const [mdpOuvert, setMdpOuvert] = useState(false)
  const [focusEmail, setFocusEmail] = useState(false)
  const racine = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const m = lireDerniereMethode()
    setDerniere(m)
    if (m === 'mot-de-passe') setMdpOuvert(true)
  }, [])

  // Une erreur secoue légèrement le formulaire (sauf si l'utilisateur réduit les animations : le CSS l'éteint)
  useEffect(() => {
    if (genre !== 'erreur') return
    setSecousse(true)
    const t = window.setTimeout(() => setSecousse(false), 450)
    return () => window.clearTimeout(t)
  }, [props.message, genre])

  // Léger mouvement du panneau avec le pointeur (sans état React : on écrit deux variables CSS)
  useEffect(() => {
    const el = racine.current
    if (!el || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
    const bouger = (e: PointerEvent) => {
      const r = el.getBoundingClientRect()
      el.style.setProperty('--bvl-px', (((e.clientX - r.left) / r.width) * 2 - 1).toFixed(3))
      el.style.setProperty('--bvl-py', (((e.clientY - r.top) / r.height) * 2 - 1).toFixed(3))
    }
    el.addEventListener('pointermove', bouger)
    return () => el.removeEventListener('pointermove', bouger)
  }, [])

  const message = props.message && genre ? (
    <p className={`bvl-msg ${genre === 'ok' ? 'is-ok' : 'is-err'}`} role={genre === 'ok' ? 'status' : 'alert'}>
      {genre === 'ok'
        ? <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="m8 12.5 3 3 5-6" /></svg>
        : <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v6M12 16.5v.5" /></svg>}
      <span>{props.message}</span>
    </p>
  ) : null

  let contenu: ReactNode
  if (props.mode === 'recuperation') {
    contenu = (
      <>
        <h1>Nouveau mot de passe</h1>
        <p className="bvl-sub">Choisis un nouveau mot de passe pour finaliser la récupération de ton compte.</p>
        {message}
        <form onSubmit={props.onRecuperation}>
          <ChampMotDePasse id="bvl-nouveau" libelle="Nouveau mot de passe" valeur={props.nouveauMotDePasse} onChange={props.onNouveauMotDePasse} autoComplete="new-password" />
          <ChampMotDePasse id="bvl-confirmation" libelle="Confirmation" valeur={props.confirmation} onChange={props.onConfirmation} autoComplete="new-password" />
          <button className="bvl-go" type="submit" disabled={props.recuperationEnCours}>
            {props.recuperationEnCours ? <><span className="bvl-spin" />Mise à jour…</> : 'Mettre à jour le mot de passe'}
          </button>
        </form>
      </>
    )
  } else if (props.oubliOuvert) {
    contenu = (
      <>
        <button className="bvl-link bvl-back" type="button" onClick={() => props.onOubli(false)}>← Retour à la connexion</button>
        <h1>Mot de passe oublié</h1>
        <p className="bvl-sub">Indique ton e-mail de connexion. On t'envoie un lien pour en choisir un nouveau.</p>
        {message}
        <form onSubmit={props.onEnvoiLien}>
          <ChampEmail id="bvl-email-oubli" libelle="E-mail de connexion" valeur={props.email} onChange={props.onEmail} domaine={props.domaine} valide={props.emailValide(props.email)} />
          <button className="bvl-go" type="submit" disabled={props.envoiEnCours}>
            {props.envoiEnCours ? <><span className="bvl-spin" />Envoi…</> : 'Envoyer le lien'}
          </button>
        </form>
      </>
    )
  } else {
    contenu = (
      <>
        <h1>Bon retour</h1>
        <p className="bvl-sub">Connecte-toi pour retrouver tes biens, tes mandats et tes contacts.</p>
        {message}
        <button className="bvl-google" type="button" disabled={props.googleEnCours || props.connexionEnCours} onClick={() => { noterDerniereMethode('google'); props.onGoogle() }}>
          {G}{props.googleEnCours ? 'Ouverture de Google…' : 'Continuer avec Google Workspace'}
          {derniere === 'google' && !props.googleEnCours ? <span className="bvl-last">Dernière utilisation</span> : null}
        </button>
        <p className="bvl-safe"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>Réservé aux comptes @{props.domaine}</p>
        <button className={`bvl-toggle${mdpOuvert ? ' is-open' : ''}`} type="button" aria-expanded={mdpOuvert} aria-controls="bvl-mdp" onClick={() => { setFocusEmail(!mdpOuvert); setMdpOuvert((o) => !o) }}>
          <span>Accès par mot de passe</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
        </button>
        {mdpOuvert ? (
          <form id="bvl-mdp" className="bvl-unfold" onSubmit={(e) => { if (props.emailValide(props.email)) noterDerniereMethode('mot-de-passe'); props.onConnexion(e) }}>
            <ChampEmail id="bvl-email" libelle="E-mail" valeur={props.email} onChange={props.onEmail} domaine={props.domaine} valide={props.emailValide(props.email)} autoFocus={focusEmail} />
            <ChampMotDePasse id="bvl-motdepasse" libelle="Mot de passe" valeur={props.motDePasse} onChange={props.onMotDePasse} autoComplete="current-password"
              avecLien={<button className="bvl-link" type="button" onClick={() => props.onOubli(true)}>Mot de passe oublié ?</button>} />
            <button className="bvl-go" type="submit" disabled={props.connexionEnCours}>
              {props.connexionEnCours ? <><span className="bvl-spin" />Connexion…</> : 'Se connecter'}
            </button>
          </form>
        ) : null}
      </>
    )
  }

  return (
    <div className="bvl" ref={racine}>
      <main className="bvl-left">
        <div className="bvl-logo"><BienvuLogo animated /></div>
        <div className="bvl-center">
          <div className={`bvl-form${secousse ? ' is-shake' : ''}`}>{contenu}</div>
        </div>
        <div className="bvl-foot"><span>Un outil Groupe GTI</span><span>Besoin d'aide ? Demande à ton administrateur.</span></div>
      </main>

      <aside className="bvl-right" aria-hidden="true">
        <div className="bvl-tag">Chaque bien,<br />bien vu.</div>
        <p className="bvl-pitch">Tes biens, tes mandats et tes contacts, au même endroit.</p>
        <div className="bvl-sym"><BienvuSymbol /></div>
        <div className="bvl-card bvl-card-1"><div><span className="bvl-ico"><svg viewBox="0 0 100 100"><path pathLength={100} d="M22 52 L43 73 L78 30" fill="none" /></svg></span><span><b>Mandat validé</b><small>Appartement T3 · exemple</small></span></div></div>
        <div className="bvl-card bvl-card-2"><div><span className="bvl-avs"><i>CD</i><i>AM</i><i>SL</i></span><span><b>3 acquéreurs correspondent</b><small>Rapprochement · exemple</small></span></div></div>
      </aside>
    </div>
  )
}
