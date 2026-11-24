// RECRUTEMENT R6 (24/11/2026) — l'écran « Recrutement » : le vivier des agents commerciaux possibles de nos quatre
// départements (07, 42, 43, 63), lu sur les annuaires publics des réseaux, et le suivi de chaque candidat.
// ADMINISTRATEURS SEULS (décision D3) : l'écran se cache derrière l'interrupteur `recrutement_ecran`, et la base
// refuse de toute façon les autres (public.rec_*, 42501).
// Maquettes validées le 20/11 : notice/maquettes_recrutement/ (Main, Candidat, Ajouter, Modifier, Supprimer).
// Note du chantier : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md, §14 (R6).
// ⛔ Rien ne part chez Hektor. ⛔ Aucun e-mail ne part d'ici : « Écrire un e-mail » ouvre la messagerie de
//   l'utilisateur et note l'envoi dans le fil (le modèle de premier contact attend la relecture de Frédéric, D5).
// En attente d'une décision (R7) et donc désactivés : le CV, le contrat, « créer son accès à bienvu ».
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { deposerPieceEmail, gmailPieceTailleMax, loadAppUsers, retirerPieceEmail, type GmailPieceOrdinateur } from './lib/api'
import {
  DELAI_ENVOI_MS, JOURS_ENTRE_DEUX, MODELES, PLAFOND_JOUR, blocDu, blocTexte, contexteDe, envoyer as envoyerEmail,
  html as htmlEmail, lireExpediteur, lireReglages, remplir, sourceDe, texteComplet, trous, valeursPour,
  type Expediteur, type ModeleCle, type Reglages,
} from './lib/recrutementEmail'
import { emailsDuJour } from './lib/recrutement'
import {
  ETAPES, ajouterCandidat, chercherCommunes, chercherDoublons, corriger, distanceKm, lireCandidat, lireVivier, majSuivi,
  marquerEtape, nomComplet, nomReseau, noter, pourquoiSansContact, prochaineRelecture, retirerCandidat,
  type AgenceGti, type Candidat, type ChampCorrigeable, type Commune, type Detail, type Doublons, type Evenement,
  type NiveauRetrait, type Vivier,
} from './lib/recrutement'
import type { UserProfile } from './types'
import './recrutement.css'

const RAYON_KM = 15
const PAR_PAGE = 50
const MEMO = 'gti_recrutement_v1'

// ─── petites aides ───

const entier = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })
const virgule = (n: number, d = 1) => n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: d })
const cle = (c: { reseau: string; identifiant: string }) => `${c.reseau}/${c.identifiant}`
function date(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('fr-FR')
}
function jourMois(iso: string | null | undefined): string {
  return date(iso).slice(0, 5)
}
function quand(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return `le ${d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })} à ${d.getHours()} h ${String(d.getMinutes()).padStart(2, '0')}`
}
function moisAnnee(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(`${iso.slice(0, 10)}T12:00:00`)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
}
function ans(dateCreation: string | null | undefined): number | null {
  if (!dateCreation) return null
  const t = new Date(`${dateCreation.slice(0, 10)}T12:00:00`).getTime()
  return Number.isNaN(t) ? null : (Date.now() - t) / (365.25 * 86400000)
}
function libelleAns(a: number | null): string {
  if (a == null) return '—'
  if (a < 1) return 'moins d’un an'
  const n = Math.floor(a)
  return n === 1 ? '1 an' : `${n} ans`
}
const initiales = (c: { prenom: string | null; nom: string | null }) =>
  nomComplet(c).split(/\s+/).filter(Boolean).slice(0, 2).map((m) => m[0]?.toUpperCase() ?? '').join('') || '?'
const sirenLisible = (s: string | null) => (s ? s.replace(/^(\d{3})(\d{3})(\d{3})$/, '$1 $2 $3') : '')
const telLien = (t: string) => `tel:${t.replace(/[^\d+]/g, '')}`
const aujourdhui = () => new Date().toISOString().slice(0, 10)
const plusMois = (n: number) => { const d = new Date(); d.setMonth(d.getMonth() + n); return d.toISOString().slice(0, 10) }
const COURT: Record<string, string> = {
  'Saint-Just-Saint-Rambert': 'St-Just-St-Rambert', 'Monistrol-sur-Loire': 'Monistrol', 'Saint-Bonnet-le-Château': 'St-Bonnet',
  'Craponne-sur-Arzon': 'Craponne', 'Saint-Didier-en-Velay': 'St-Didier',
}
const court = (nom: string) => COURT[nom] ?? nom
const DEPARTEMENTS: Record<string, string> = { '07': 'Ardèche', '42': 'Loire', '43': 'Haute-Loire', '63': 'Puy-de-Dôme' }

function lireMemo(): { zone: string | null } {
  try {
    const brut = JSON.parse(window.localStorage.getItem(MEMO) ?? '{}') as { zone?: unknown }
    return { zone: typeof brut.zone === 'string' ? brut.zone : null }
  } catch { return { zone: null } }
}
function ecrireMemo(zone: string | null) {
  try { window.localStorage.setItem(MEMO, JSON.stringify({ zone })) } catch { /* sans mémoire, l'écran marche */ }
}

// Le suivi d'une ligne : l'étape, sauf un statut ; « à vérifier » / « à trancher » se DÉDUISENT aussi d'une
// entreprise cessée ou d'une opposition au registre tant qu'on n'a pas commencé (comme sur la maquette).
function suiviDe(c: Candidat): { texte: string; classe: string; ensuite: string } {
  const ensuite = c.prochaine_action || c.prochaine_le
    ? [c.prochaine_action, c.prochaine_le ? `le ${jourMois(c.prochaine_le)}` : ''].filter(Boolean).join(' ')
    : ''
  if (c.archive) return { texte: 'Retiré de ma liste', classe: 'rc-p-non', ensuite: '' }
  if (c.statut === 'pas_interesse') return { texte: 'Pas intéressé', classe: 'rc-p-non', ensuite: c.reprise_le ? `reprendre en ${moisAnnee(c.reprise_le)}` : '' }
  if (c.statut === 'a_verifier') return { texte: 'À vérifier', classe: 'rc-p-afaire', ensuite }
  if (c.statut === 'a_trancher') return { texte: 'À trancher', classe: 'rc-p-afaire', ensuite }
  if (c.etape <= 1) {
    if (c.opposition) return { texte: 'À trancher', classe: 'rc-p-afaire', ensuite }
    if (c.entreprise_etat === 'C') return { texte: 'À vérifier', classe: 'rc-p-afaire', ensuite }
    return { texte: 'À contacter', classe: 'rc-p-afaire', ensuite }
  }
  const t = ['', '', 'Contacté', 'Rendez-vous', 'Proposition', 'Contrat signé', 'Accès ouvert'][c.etape] ?? 'À contacter'
  return { texte: t, classe: c.etape === 2 ? 'rc-p-contacte' : c.etape >= 5 ? 'rc-p-club' : 'rc-p-rdv', ensuite }
}

// Ce qu'il faut savoir d'une ligne, en une pastille (la plus importante).
function signalDe(c: Candidat): { texte: string; classe: string } | null {
  if (c.opposition) return { texte: 'Opposé à la prospection', classe: 'rc-p-oppose' }
  if (c.etat_suivi === 'parti') return { texte: `Parti de ${nomReseau(c.reseau)}`, classe: 'rc-p-cesse' }
  if (c.entreprise_etat === 'C') return { texte: 'Entreprise cessée', classe: 'rc-p-cesse' }
  if (c.etat_suivi === 'revenu') return { texte: 'Revenu', classe: 'rc-p-club' }
  if (c.distinction) return { texte: c.distinction, classe: 'rc-p-club' }
  if (c.etat_suivi === 'nouveau') return { texte: 'Nouveau', classe: 'rc-p-rdv' }
  if (c.desactive) return { texte: 'Fiche désactivée', classe: 'rc-p-non' }
  return null
}

// ─── les pictos ───

const Ico = {
  tel: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" /></svg>,
  mail: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3.5 6.5l8.5 6.5 8.5-6.5" /></svg>,
  agenda: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15" rx="2" /><path d="M3.5 10h17M8 3v4M16 3v4" /></svg>,
  plus: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>,
  export: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14" /></svg>,
  loupe: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#5c6163" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></svg>,
  croix: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>,
  fermer: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>,
  retour: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>,
  poubelle: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" /></svg>,
  coche: <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12.5l4 4 8-9" fill="none" stroke="#ffffff" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  cocheMarque: <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12.5l4 4 8-9" fill="none" stroke="#c5005f" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" /></svg>,
}

// ─── l'écran ───

type Vue = 'tous' | 'joignables' | 'relances' | 'encours'
type Filtres = { reseau: string | null; activite: string | null; anciennete: string | null; suivi: string | null; savoir: string | null }
const SANS_FILTRE: Filtres = { reseau: null, activite: null, anciennete: null, suivi: null, savoir: null }
type StatZone = { t: number; j: number; reseau: number; sources: Array<[string, number]> }

export default function RecrutementScreen({ monId }: { monId: string | null }) {
  const [vivier, setVivier] = useState<Vivier | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [zone, setZone] = useState<string | null>(() => lireMemo().zone)
  const [vue, setVue] = useState<Vue>('tous')
  const [recherche, setRecherche] = useState('')
  const [filtres, setFiltres] = useState<Filtres>(SANS_FILTRE)
  const [page, setPage] = useState(0)
  const [choisis, setChoisis] = useState<Set<string>>(new Set())
  const [ouvert, setOuvert] = useState<{ reseau: string; identifiant: string } | null>(null)
  const [ajout, setAjout] = useState(false)
  const [groupe, setGroupe] = useState(false)   // E2 : écrire aux candidats cochés
  const [admins, setAdmins] = useState<UserProfile[]>([])
  const listeRef = useRef<HTMLElement | null>(null)

  const charger = useCallback(async () => {
    try {
      setErreur(null)
      setVivier(await lireVivier())
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    }
  }, [])
  useEffect(() => { void charger() }, [charger])
  useEffect(() => {
    let annule = false
    loadAppUsers()
      .then((u) => { if (!annule) setAdmins(u.filter((p) => p.role === 'admin' && p.is_active)) })
      .catch(() => { /* sans la liste, « Qui la suit » ne propose que « Moi » */ })
    return () => { annule = true }
  }, [])
  useEffect(() => { ecrireMemo(zone) }, [zone])
  useEffect(() => { setPage(0) }, [zone, vue, recherche, filtres])

  const patcher = useCallback((k: string, patch: Partial<Candidat>) => {
    setVivier((v) => (v ? { ...v, candidats: v.candidats.map((c) => (cle(c) === k ? { ...c, ...patch } : c)) } : v))
  }, [])

  const candidats = useMemo(() => vivier?.candidats ?? [], [vivier])
  const agences = useMemo(() => vivier?.agences ?? [], [vivier])
  const agenceZone = agences.find((a) => a.nom === zone) ?? null
  // une zone choisie qui n'existe plus (agence renommée) ne doit pas filtrer en silence
  useEffect(() => { if (vivier && zone && !agences.some((a) => a.nom === zone)) setZone(null) }, [vivier, zone, agences])

  // « à 15 km » = de CETTE agence, pas seulement de la plus proche (conception R6)
  const actifs = useMemo(() => candidats.filter((c) => !c.archive), [candidats])
  const stats = useMemo(() => {
    const parAgence = new Map<string, StatZone>()
    const compter = (liste: Candidat[]): StatZone => {
      const src = new Map<string, number>()
      for (const c of liste) src.set(nomReseau(c.reseau), (src.get(nomReseau(c.reseau)) ?? 0) + 1)
      return {
        t: liste.length,
        j: liste.filter((c) => c.telephone || c.email).length,
        reseau: liste.filter((c) => c.reseau !== 'registre').length,
        sources: [...src.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5),
      }
    }
    for (const a of agences) {
      parAgence.set(a.nom, compter(actifs.filter((c) => c.lat != null && c.lon != null && distanceKm(c.lat, c.lon, a.lat, a.lon) <= RAYON_KM)))
    }
    return { parAgence, region: compter(actifs) }
  }, [actifs, agences])

  const distanceA = useCallback((c: Candidat): { km: number | null; agence: string | null } => {
    if (agenceZone && c.lat != null && c.lon != null) return { km: distanceKm(c.lat, c.lon, agenceZone.lat, agenceZone.lon), agence: agenceZone.nom }
    return { km: c.distance_km, agence: c.agence_gti_proche }
  }, [agenceZone])

  const filtrees = useMemo(() => {
    const q = recherche.trim().toLowerCase()
    const qChiffres = q.replace(/\s/g, '')
    let liste = filtres.suivi === 'archives' ? candidats.filter((c) => c.archive) : actifs
    if (agenceZone) liste = liste.filter((c) => c.lat != null && c.lon != null && distanceKm(c.lat, c.lon, agenceZone.lat, agenceZone.lon) <= RAYON_KM)
    if (vue === 'joignables') liste = liste.filter((c) => c.telephone || c.email)
    if (vue === 'relances') liste = liste.filter((c) => (c.prochaine_le || c.prochaine_action) && (!c.suivi_par || c.suivi_par === monId))
    if (vue === 'encours') liste = liste.filter((c) => c.etape >= 2 && c.statut !== 'pas_interesse')
    if (q) {
      liste = liste.filter((c) => [nomComplet(c), c.commune, c.code_postal, c.agence, nomReseau(c.reseau)].some((x) => (x ?? '').toLowerCase().includes(q))
        || (qChiffres.length >= 3 && /^\d+$/.test(qChiffres) && (c.siren ?? '').includes(qChiffres)))
    }
    if (filtres.reseau) liste = liste.filter((c) => c.reseau === filtres.reseau)
    if (filtres.activite === 'annonces') liste = liste.filter((c) => (c.nb_annonces ?? 0) > 0)
    if (filtres.activite === 'avis') liste = liste.filter((c) => (c.nb_avis ?? 0) > 0)
    if (filtres.activite === 'rien') liste = liste.filter((c) => !(c.nb_annonces ?? 0) && !(c.nb_avis ?? 0))
    if (filtres.anciennete) {
      liste = liste.filter((c) => {
        const a = ans(c.entreprise_creee_le)
        switch (filtres.anciennete) {
          case 'moins2': return a != null && a < 2
          case '2a5': return a != null && a >= 2 && a < 5
          case '5a10': return a != null && a >= 5 && a < 10
          case 'plus10': return a != null && a >= 10
          default: return a == null
        }
      })
    }
    if (filtres.suivi && filtres.suivi !== 'archives') {
      liste = liste.filter((c) => {
        switch (filtres.suivi) {
          case 'a_contacter': return c.etape <= 1 && !c.statut
          case 'contacte': return c.etape === 2
          case 'rdv': return c.etape === 3
          case 'proposition': return c.etape >= 4
          default: return c.statut === filtres.suivi
        }
      })
    }
    if (filtres.savoir) {
      liste = liste.filter((c) => {
        switch (filtres.savoir) {
          case 'distinction': return Boolean(c.distinction)
          case 'cessee': return c.entreprise_etat === 'C'
          case 'opposition': return c.opposition
          case 'corrige': return c.corrige
          case 'saisie': return c.origine === 'saisie'
          default: return c.etat_suivi === filtres.savoir
        }
      })
    }
    const tri = [...liste]
    if (vue === 'relances') tri.sort((a, b) => (a.prochaine_le ?? '9999').localeCompare(b.prochaine_le ?? '9999'))
    else if (agenceZone) tri.sort((a, b) => (distanceA(a).km ?? 999) - (distanceA(b).km ?? 999))
    else tri.sort((a, b) => (a.nom ?? '').localeCompare(b.nom ?? '', 'fr') || (a.prenom ?? '').localeCompare(b.prenom ?? '', 'fr'))
    return tri
  }, [candidats, actifs, agenceZone, vue, monId, recherche, filtres, distanceA])

  const pageLignes = filtrees.slice(page * PAR_PAGE, (page + 1) * PAR_PAGE)

  const exporter = () => {
    const lignes = choisis.size ? filtrees.filter((c) => choisis.has(cle(c))) : filtrees
    const colonnes = ['Réseau', 'Prénom', 'Nom', 'Fonction', 'Agence', 'Commune', 'Code postal', 'Téléphone', 'E-mail', 'SIREN', 'Agence GTI', 'Distance (km)', 'Suivi', 'Ensuite']
    const champ = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`
    const texte = [colonnes.map(champ).join(';'), ...lignes.map((c) => {
      const d = distanceA(c)
      const s = suiviDe(c)
      return [nomReseau(c.reseau), c.prenom, c.nom, c.fonction, c.agence, c.commune, c.code_postal, c.telephone, c.email, c.siren, d.agence, d.km == null ? '' : virgule(d.km), s.texte, s.ensuite].map(champ).join(';')
    })].join('\r\n')
    const lien = document.createElement('a')
    lien.href = URL.createObjectURL(new Blob(['﻿', texte], { type: 'text/csv;charset=utf-8' }))
    lien.download = `recrutement_${aujourdhui()}.csv`
    lien.click()
    window.setTimeout(() => URL.revokeObjectURL(lien.href), 2000)
  }

  if (ouvert) {
    const candidat = candidats.find((c) => c.reseau === ouvert.reseau && c.identifiant === ouvert.identifiant) ?? null
    return (
      <FicheCandidat
        key={cle(ouvert)}
        reseau={ouvert.reseau}
        identifiant={ouvert.identifiant}
        candidat={candidat}
        agences={agences}
        admins={admins}
        monId={monId}
        retour={zone ? `Recrutement, autour de ${zone}` : 'Recrutement'}
        onRetour={() => setOuvert(null)}
        onPatch={(patch) => patcher(cle(ouvert), patch)}
        onRetire={() => { setOuvert(null); void charger() }}
        onOuvrir={(r, i) => setOuvert({ reseau: r, identifiant: i })}
      />
    )
  }

  const etat = vivier?.etat
  const finCollecte = etat?.collecte?.fin ?? null
  const malades = (etat?.sources ?? []).filter((s) => s.sante === 'malade')
  const zoneStat = zone ? stats.parAgence.get(zone) ?? null : null
  const z = zoneStat ?? stats.region
  const maxT = Math.max(1, ...[...stats.parAgence.values()].map((s) => s.t))
  const classement = [...agences].sort((a, b) => (stats.parAgence.get(b.nom)?.t ?? 0) - (stats.parAgence.get(a.nom)?.t ?? 0))
  const filtreActif = (Object.keys(filtres) as Array<keyof Filtres>).some((k) => filtres[k] != null)

  return (
    <div className="rc-ecran">
      <header className="rc-entete">
        <div style={{ minWidth: 0 }}>
          <h1>Recrutement</h1>
          <p>
            {vivier
              ? <>{entier.format(stats.region.t)} candidats dans nos quatre départements, dont {entier.format(stats.region.j)} joignables.
                {' '}{finCollecte ? `Liste relue le ${date(finCollecte)}` : 'Liste pas encore relue'} ; prochaine relecture le {date(prochaineRelecture().toISOString())}.</>
              : erreur ? 'La liste n’a pas pu être lue.' : 'Lecture de la liste…'}
          </p>
        </div>
        <div className="rc-actions">
          <button className="rc-btn rc-btn-quiet" type="button" onClick={exporter} disabled={!filtrees.length}>{Ico.export}Exporter{choisis.size ? ` (${choisis.size})` : ''}</button>
          <button className="rc-btn rc-btn-main" type="button" onClick={() => setAjout(true)} disabled={!vivier}>{Ico.plus}Ajouter un candidat</button>
        </div>
      </header>

      {erreur ? <div className="rc-alerte rc-alerte-rouge" role="alert"><span>{erreur} <button className="rc-lien" type="button" onClick={() => void charger()}>Réessayer</button></span></div> : null}
      {malades.length ? (
        <div className="rc-alerte" role="status">
          <span><strong>{malades.length === 1 ? 'Une source n’a pas pu être relue' : `${malades.length} sources n’ont pas pu être relues`}</strong> à la dernière collecte : {malades.map((s) => nomReseau(s.reseau)).join(', ')}. Leurs candidats d’avant sont gardés tels quels ; personne n’est marqué parti à cause d’elles.</span>
        </div>
      ) : null}

      {vivier ? (
        <section className="rc-carte-bloc" aria-labelledby="rc-ou">
          <div className="rc-carte-col">
            <h2 id="rc-ou">Où recruter</h2>
            <p>Chaque disque est le vivier à {RAYON_KM} km d’une agence ; le cœur plein, ceux qu’on peut joindre.</p>
            {agences.length
              ? <CarteAgences agences={agences} stats={stats.parAgence} zone={zone} onChoisir={setZone} />
              : <p className="rc-texte-doux">La carte des agences arrive avec la prochaine montée de la collecte.</p>}
          </div>
          <div className="rc-classement">
            <div className="rc-classement-tete">
              <h3>Nos {agences.length} agences</h3>
              <button className={`rc-chip${zone ? '' : ' is-on'}`} type="button" onClick={() => setZone(null)}>Toutes les agences</button>
            </div>
            <div className="rc-rang-legende"><span>Agence</span><span /><span className="rc-droite">à {RAYON_KM} km</span><span className="rc-droite">joign.</span></div>
            {classement.map((a) => {
              const s = stats.parAgence.get(a.nom)
              const on = a.nom === zone
              return (
                <button key={a.nom} className={`rc-rang${on ? ' is-on' : ''}`} type="button" aria-pressed={on} onClick={() => setZone(on ? null : a.nom)}>
                  <span className="rc-rang-nom">{a.nom}</span>
                  <span className="rc-barre">
                    <span className="rc-b-total" style={{ width: `${(((s?.t ?? 0) / maxT) * 100).toFixed(1)}%` }} />
                    <span className="rc-b-joign" style={{ width: `${(((s?.j ?? 0) / maxT) * 100).toFixed(1)}%` }} />
                  </span>
                  <span className="rc-num rc-droite">{s?.t ?? 0}</span>
                  <span className="rc-num rc-joign">{s?.j ?? 0}</span>
                </button>
              )
            })}
          </div>
          <aside className="rc-zone" aria-live="polite">
            <div>
              <p className="rc-zone-titre">{zone ? 'Autour de' : 'Dans nos quatre départements'}</p>
              <p className="rc-zone-nom">{zone ?? 'la région'}</p>
            </div>
            <div className="rc-zone-chiffres">
              <div><strong className="rc-num">{entier.format(z.t)}</strong><span>candidats</span></div>
              <div><strong className="rc-num" style={{ color: '#f6b6d5' }}>{entier.format(z.j)}</strong><span>joignables</span></div>
              <div><strong className="rc-num">{entier.format(z.reseau)}</strong><span>dans un réseau</span></div>
            </div>
            <div className="rc-zone-sources">
              <p style={{ fontSize: 13, fontWeight: 600 }}>D’où ils viennent</p>
              {z.sources.map(([nom, n]) => (
                <div className="rc-zone-source" key={nom}>
                  <div><span>{nom}</span><span className="rc-zone-piste"><span style={{ width: `${z.t ? Math.round((n / z.t) * 100) : 0}%` }} /></span></div>
                  <span className="rc-num rc-droite" style={{ fontWeight: 700 }}>{n}</span>
                </div>
              ))}
            </div>
            <button className="rc-btn" type="button" onClick={() => listeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>Voir ces {entier.format(z.t)} candidats</button>
          </aside>
        </section>
      ) : null}

      {vivier ? (
        <section className="rc-liste-bloc" aria-labelledby="rc-titre-liste" ref={listeRef}>
          <div className="rc-liste-tete">
            <h2 id="rc-titre-liste">Les candidats</h2>
            <div className="rc-vues" role="group" aria-label="Vue">
              {([['tous', 'Tous'], ['joignables', 'Joignables'], ['relances', 'Mes relances'], ['encours', 'En cours de recrutement']] as Array<[Vue, string]>).map(([k, t]) => (
                <button key={k} type="button" className={vue === k ? 'is-on' : ''} aria-pressed={vue === k} onClick={() => setVue(k)}>{t}</button>
              ))}
            </div>
          </div>
          <div className="rc-filtres">
            <label className="rc-cherche">
              {Ico.loupe}
              <input type="search" placeholder="Nom, commune, SIREN" aria-label="Chercher un candidat" value={recherche} onChange={(e) => setRecherche(e.target.value)} />
            </label>
            {zone ? <button className="rc-chip is-on" type="button" onClick={() => setZone(null)}>À {RAYON_KM} km de {zone}<span aria-label="retirer ce filtre">{Ico.croix}</span></button> : null}
            <Choix libelle="Réseau" valeur={filtres.reseau} onChange={(v) => setFiltres({ ...filtres, reseau: v })}
              options={[...new Set(actifs.map((c) => c.reseau))].sort((a, b) => nomReseau(a).localeCompare(nomReseau(b), 'fr'))
                .map((r) => ({ v: r, t: nomReseau(r), n: actifs.filter((c) => c.reseau === r).length }))} />
            <Choix libelle="Activité" valeur={filtres.activite} onChange={(v) => setFiltres({ ...filtres, activite: v })}
              options={[{ v: 'annonces', t: 'Avec des annonces en ligne' }, { v: 'avis', t: 'Avec des avis clients' }, { v: 'rien', t: 'Sans activité visible' }]} />
            <Choix libelle="Ancienneté" valeur={filtres.anciennete} onChange={(v) => setFiltres({ ...filtres, anciennete: v })}
              options={[{ v: 'moins2', t: 'Moins de 2 ans' }, { v: '2a5', t: '2 à 5 ans' }, { v: '5a10', t: '5 à 10 ans' }, { v: 'plus10', t: '10 ans et plus' }, { v: 'inconnue', t: 'Inconnue (pas de SIREN)' }]} />
            <Choix libelle="Suivi" valeur={filtres.suivi} onChange={(v) => setFiltres({ ...filtres, suivi: v })}
              options={[{ v: 'a_contacter', t: 'À contacter' }, { v: 'contacte', t: 'Contactés' }, { v: 'rdv', t: 'Rendez-vous' }, { v: 'proposition', t: 'Proposition et au-delà' },
                { v: 'pas_interesse', t: 'Pas intéressés' }, { v: 'a_verifier', t: 'À vérifier' }, { v: 'a_trancher', t: 'À trancher' },
                { v: 'archives', t: 'Retirés de ma liste', n: candidats.filter((c) => c.archive).length }]} />
            <Choix libelle="À savoir" valeur={filtres.savoir} onChange={(v) => setFiltres({ ...filtres, savoir: v })}
              options={[{ v: 'distinction', t: 'Une distinction du réseau' }, { v: 'nouveau', t: 'Nouveaux à la dernière collecte' }, { v: 'parti', t: 'Partis de leur réseau' },
                { v: 'revenu', t: 'Revenus' }, { v: 'cessee', t: 'Entreprise cessée' }, { v: 'opposition', t: 'Opposés à la prospection' },
                { v: 'corrige', t: 'Corrigés par nous' }, { v: 'saisie', t: 'Ajoutés à la main' }]} />
            {filtreActif ? <button className="rc-lien" type="button" onClick={() => setFiltres(SANS_FILTRE)}>Tout effacer</button> : null}
          </div>

          {pageLignes.length ? (
            <div className="rc-table-zone">
              <table className="rc-table">
                <thead>
                  <tr>
                    <th><input type="checkbox" aria-label="Tout choisir sur cette page" checked={pageLignes.every((c) => choisis.has(cle(c)))}
                      onChange={(e) => { const n = new Set(choisis); for (const c of pageLignes) { if (e.target.checked) n.add(cle(c)); else n.delete(cle(c)) } setChoisis(n) }} /></th>
                    <th>Candidat</th><th>Où</th><th>Activité</th><th>Entreprise</th><th>À savoir</th><th>Joindre</th><th>Suivi</th>
                  </tr>
                </thead>
                <tbody>
                  {pageLignes.map((c) => {
                    const k = cle(c)
                    const d = distanceA(c)
                    const s = suiviDe(c)
                    const sig = signalDe(c)
                    const a = ans(c.entreprise_creee_le)
                    const sans = pourquoiSansContact(c)
                    return (
                      <tr key={k}>
                        <td className="rc-td-choix"><input type="checkbox" aria-label={`Choisir ${nomComplet(c)}`} checked={choisis.has(k)}
                          onChange={(e) => { const n = new Set(choisis); if (e.target.checked) n.add(k); else n.delete(k); setChoisis(n) }} /></td>
                        <td style={{ minWidth: 200 }}>
                          <button className="rc-nom" type="button" onClick={() => setOuvert({ reseau: c.reseau, identifiant: c.identifiant })}>{nomComplet(c)}</button>
                          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6, marginTop: 4 }}>
                            <span className="rc-res">{nomReseau(c.reseau)}</span>
                            {c.fonction && c.reseau !== 'registre' ? <span className="rc-mute" style={{ fontSize: 12 }}>{c.fonction}</span> : null}
                          </div>
                        </td>
                        <td data-l="Où" style={{ minWidth: 150 }}>{c.commune ?? '—'}<div className="rc-sub rc-num">{d.km != null && d.agence ? `${virgule(d.km)} km de ${court(d.agence)}` : ''}</div></td>
                        <td data-l="Activité" style={{ minWidth: 110 }}>
                          <span className="rc-num">{c.nb_annonces != null ? `${c.nb_annonces} annonce${c.nb_annonces > 1 ? 's' : ''}` : '—'}</span>
                          <div className="rc-sub rc-num">{c.nb_avis ? `${virgule(Number(c.note_avis ?? 0))} sur 5, ${c.nb_avis} avis` : c.nb_avis === 0 ? 'aucun avis' : ''}</div>
                        </td>
                        <td data-l="Entreprise" style={{ minWidth: 110 }}>
                          <span className="rc-num">{libelleAns(a)}</span>
                          <div className="rc-sub">{c.opposition ? 'registre : opposé' : c.entreprise_etat === 'A' ? 'active' : c.entreprise_etat === 'C' ? 'CESSÉE au registre' : c.siren ? 'registre non lu' : 'pas de SIREN publié'}</div>
                        </td>
                        <td data-l="À savoir" style={{ minWidth: 130 }}>{sig ? <span className={`rc-pill ${sig.classe}`}>{sig.texte}</span> : null}</td>
                        <td data-l="Joindre" style={{ minWidth: 110 }}>
                          <div className="rc-joindre">
                            <span className={`rc-ico${c.telephone ? '' : ' is-off'}`} title={c.telephone ? 'Téléphone affiché par le réseau' : 'Pas de téléphone public'}>{Ico.tel}</span>
                            <span className={`rc-ico${c.email ? '' : ' is-off'}`} title={c.email ? 'E-mail affiché par le réseau' : 'Pas d’e-mail public'}>{Ico.mail}</span>
                          </div>
                          <div className="rc-sub">{sans}</div>
                        </td>
                        <td data-l="Suivi" style={{ minWidth: 150 }}><span className={`rc-pill ${s.classe}`}>{s.texte}</span><div className="rc-sub">{s.ensuite}</div></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : <p className="rc-vide">Aucun candidat ne répond à ces critères.</p>}
          {choisis.size ? (
            // E2 (planche 2) : la barre d'action des candidats cochés
            <div className="rc-barre-action" role="region" aria-label="Candidats choisis">
              <span><strong>{choisis.size}</strong> choisi{choisis.size > 1 ? 's' : ''}</span>
              <button className="rc-lien" type="button" style={{ color: '#f6b6d5' }} onClick={() => setChoisis(new Set())}>Tout décocher</button>
              <button className="rc-btn rc-btn-main" type="button" style={{ marginLeft: 'auto', minHeight: 40 }} onClick={() => setGroupe(true)}>{Ico.mail}Écrire à {choisis.size} candidat{choisis.size > 1 ? 's' : ''}</button>
            </div>
          ) : null}
          <div className="rc-pied">
            <span className="rc-num">{filtrees.length ? `${entier.format(page * PAR_PAGE + 1)} à ${entier.format(page * PAR_PAGE + pageLignes.length)} sur ${entier.format(filtrees.length)} candidats` : ''}{choisis.size ? ` · ${choisis.size} choisi${choisis.size > 1 ? 's' : ''}` : ''}</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="rc-btn rc-btn-quiet rc-btn-petit" type="button" disabled={page === 0} onClick={() => setPage(page - 1)}>Précédents</button>
              <button className="rc-btn rc-btn-quiet rc-btn-petit" type="button" disabled={(page + 1) * PAR_PAGE >= filtrees.length} onClick={() => setPage(page + 1)}>Suivants</button>
            </div>
          </div>
        </section>
      ) : null}

      {groupe ? (
        <ModaleGroupe
          candidats={candidats.filter((c) => choisis.has(cle(c)))}
          onFermer={() => setGroupe(false)}
          onPatch={(k, patch) => patcher(k, patch)}
          onFini={() => { setGroupe(false); setChoisis(new Set()) }}
        />
      ) : null}
      {ajout ? (
        <ModaleAjouter
          agences={agences}
          admins={admins}
          monId={monId}
          onFermer={() => setAjout(false)}
          onOuvrir={(r, i) => { setAjout(false); setOuvert({ reseau: r, identifiant: i }) }}
          onAjoute={(r, i, ouvrir) => { setAjout(false); void charger().then(() => { if (ouvrir) setOuvert({ reseau: r, identifiant: i }) }) }}
        />
      ) : null}
    </div>
  )
}

// ─── un filtre en pastille, avec son menu ───

function Choix({ libelle, valeur, options, onChange }: { libelle: string; valeur: string | null; options: Array<{ v: string; t: string; n?: number }>; onChange: (v: string | null) => void }) {
  const [ouvert, setOuvert] = useState(false)
  const ref = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    if (!ouvert) return
    const dehors = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOuvert(false) }
    const echap = (e: KeyboardEvent) => { if (e.key === 'Escape') setOuvert(false) }
    document.addEventListener('mousedown', dehors)
    document.addEventListener('keydown', echap)
    return () => { document.removeEventListener('mousedown', dehors); document.removeEventListener('keydown', echap) }
  }, [ouvert])
  const choisi = options.find((o) => o.v === valeur)
  return (
    <div className="rc-menu-ancre" ref={ref}>
      <button className={`rc-chip${choisi ? ' is-on' : ''}`} type="button" aria-haspopup="listbox" aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>
        {choisi ? `${libelle} : ${choisi.t}` : libelle}
        {choisi ? <span aria-label="retirer ce filtre" onClick={(e) => { e.stopPropagation(); onChange(null); setOuvert(false) }}>{Ico.croix}</span> : null}
      </button>
      {ouvert ? (
        <div className="rc-menu" role="listbox" aria-label={libelle}>
          <button type="button" role="option" aria-selected={valeur == null} className={valeur == null ? 'is-on' : ''} onClick={() => { onChange(null); setOuvert(false) }}>Tous</button>
          {options.map((o) => (
            <button key={o.v} type="button" role="option" aria-selected={o.v === valeur} className={o.v === valeur ? 'is-on' : ''} onClick={() => { onChange(o.v); setOuvert(false) }}>
              <span>{o.t}</span>{o.n != null ? <span className="rc-num rc-mute">{o.n}</span> : null}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

// ─── la carte dessinée des agences (décision D4 : aucune dépendance neuve) ───

function CarteAgences({ agences, stats, zone, onChoisir }: { agences: AgenceGti[]; stats: Map<string, StatZone>; zone: string | null; onChoisir: (nom: string | null) => void }) {
  const L = 470
  const H = 340
  const marge = 34
  const dessin = useMemo(() => {
    const lats = agences.map((a) => a.lat)
    const lons = agences.map((a) => a.lon)
    const [la0, la1, lo0, lo1] = [Math.min(...lats), Math.max(...lats), Math.min(...lons), Math.max(...lons)]
    const k = Math.cos(((la0 + la1) / 2) * Math.PI / 180)
    const echelle = Math.min((L - 2 * marge) / Math.max(0.01, (lo1 - lo0) * k), (H - 2 * marge) / Math.max(0.01, la1 - la0))
    const dx = (L - (lo1 - lo0) * k * echelle) / 2
    const dy = (H - (la1 - la0) * echelle) / 2
    const points = agences.map((a) => {
      const s = stats.get(a.nom)
      const t = s?.t ?? 0
      const r = 5 + Math.sqrt(t) * 1.5
      return { a, x: dx + (a.lon - lo0) * k * echelle, y: dy + (la1 - a.lat) * echelle, t, r, rj: t ? r * Math.sqrt((s?.j ?? 0) / t) : 0 }
    }).sort((p, q) => q.t - p.t)
    // les étiquettes : à droite, sinon à gauche, dessus, dessous ; on n'écrit pas par-dessus une autre
    const poses: Array<{ x0: number; y0: number; x1: number; y1: number }> = points.map((p) => ({ x0: p.x - p.r, y0: p.y - p.r, x1: p.x + p.r, y1: p.y + p.r }))
    const libres = (b: { x0: number; y0: number; x1: number; y1: number }, sauf: number) =>
      b.x0 >= 0 && b.x1 <= L && b.y0 >= 0 && b.y1 <= H && poses.every((o, i) => i === sauf || b.x1 < o.x0 || b.x0 > o.x1 || b.y1 < o.y0 || b.y0 > o.y1)
    const etiquettes = points.map((p, i) => {
      const texte = court(p.a.nom)
      const w = texte.length * 6.2
      const essais: Array<{ x: number; y: number; ancre: 'start' | 'end' | 'middle'; b: { x0: number; y0: number; x1: number; y1: number } }> = [
        { x: p.x + p.r + 4, y: p.y + 4, ancre: 'start', b: { x0: p.x + p.r + 3, y0: p.y - 7, x1: p.x + p.r + 5 + w, y1: p.y + 6 } },
        { x: p.x - p.r - 4, y: p.y + 4, ancre: 'end', b: { x0: p.x - p.r - 5 - w, y0: p.y - 7, x1: p.x - p.r - 3, y1: p.y + 6 } },
        { x: p.x, y: p.y - p.r - 5, ancre: 'middle', b: { x0: p.x - w / 2, y0: p.y - p.r - 17, x1: p.x + w / 2, y1: p.y - p.r - 3 } },
        { x: p.x, y: p.y + p.r + 13, ancre: 'middle', b: { x0: p.x - w / 2, y0: p.y + p.r + 2, x1: p.x + w / 2, y1: p.y + p.r + 16 } },
      ]
      const ok = essais.find((e) => libres(e.b, i))
      if (!ok) return null
      poses.push(ok.b)
      return { nom: p.a.nom, texte, x: ok.x, y: ok.y, ancre: ok.ancre }
    })
    const depts = [...new Set(agences.map((a) => a.departement))].map((d) => {
      const ps = points.filter((p) => p.a.departement === d)
      const x = ps.reduce((s, p) => s + p.x, 0) / ps.length
      const y = Math.max(...ps.map((p) => p.y + p.r)) + 26
      return { nom: DEPARTEMENTS[d] ?? d, x: Math.min(L - 40, Math.max(40, x)), y: Math.min(H - 4, y) }
    })
    return { points, etiquettes, depts }
  }, [agences, stats])
  return (
    <svg className="rc-carte" viewBox={`0 0 ${L} ${H}`} role="img" aria-label={`Carte des ${agences.length} agences GTI et de leur vivier de candidats`}>
      {dessin.depts.map((d) => <text key={d.nom} x={d.x} y={d.y} textAnchor="middle" fontSize="11" fill="#9aa0a2">{d.nom}</text>)}
      {dessin.points.map((p) => {
        const on = p.a.nom === zone
        return (
          <g key={p.a.nom} className="rc-point" onClick={() => onChoisir(on ? null : p.a.nom)}>
            <title>{`${p.a.nom} : ${p.t} candidats à ${RAYON_KM} km`}</title>
            <circle cx={p.x} cy={p.y} r={p.r} fill={on ? 'rgba(197,0,95,0.16)' : 'rgba(34,35,35,0.06)'} stroke={on ? '#c5005f' : 'rgba(34,35,35,0.28)'} strokeWidth="1.2" />
            <circle cx={p.x} cy={p.y} r={p.rj} fill={on ? '#c5005f' : 'rgba(34,35,35,0.55)'} />
          </g>
        )
      })}
      {dessin.etiquettes.map((e) => (e ? (
        <text key={e.nom} x={e.x} y={e.y} textAnchor={e.ancre} fontSize="11.5" fontWeight={e.nom === zone ? 800 : 500} fill="#222323" style={{ pointerEvents: 'none' }}>{e.texte}</text>
      ) : null))}
    </svg>
  )
}

// ─── la fiche d'un candidat ───

type Onglet = 'appel' | 'note' | 'email' | 'rdv'
const ONGLETS: Array<[Onglet, string]> = [['appel', 'Appel'], ['note', 'Note'], ['email', 'E-mail'], ['rdv', 'Rendez-vous']]
const AIDES: Record<Onglet, string> = {
  appel: 'Comment s’est passé l’appel ?', note: 'Ce que tu veux retenir sur cette personne',
  email: 'Ce que tu lui écris (ta messagerie s’ouvre, l’envoi est noté ici)', rdv: 'Lieu, qui y va, ce qu’on prépare',
}
const BOUTONS: Record<Onglet, string> = { appel: 'Noter l’appel', note: 'Ajouter la note', email: 'Ouvrir ma messagerie', rdv: 'Noter le rendez-vous' }
const RESULTATS: Array<[NonNullable<Evenement['resultat']>, string]> = [['messagerie', 'messagerie'], ['pas_disponible', 'pas disponible'], ['interesse', 'intéressé'], ['pas_interesse', 'pas intéressé']]
const SUITES = ['la contacter une première fois.', 'la contacter une première fois.', 'fixer un rendez-vous.', 'lui présenter le barème et le simulateur de revenus.', 'préparer son contrat d’agent commercial.', 'lui ouvrir son accès à bienvu.', 'rien : elle fait partie de l’équipe.']
const QUAND_COURANTE = ['', 'à appeler', 'à planifier', 'barème à remettre', 'agent commercial', 'compte bienvu']
// le carnet écrit le nom technique du champ (« telephone corrigé ») : on l'affiche en français
const LIB_CHAMPS: Record<string, string> = { prenom: 'prénom', nom: 'nom', telephone: 'téléphone', email: 'e-mail', commune: 'commune', code_postal: 'code postal', fonction: 'fonction', agence: 'agence' }
const texteLisible = (e: { type: string; texte: string | null }) => {
  if (e.type === 'correction' && e.texte) return e.texte.replace(/^([a-z_]+)/, (m) => LIB_CHAMPS[m] ?? m)
  if (e.type === 'ajout' && e.texte) return e.texte.replace(/^ajoutée à la main( : )?/, '') || null   // le titre le dit déjà
  return e.texte
}
const LETTRES: Record<Evenement['type'], string> = { appel: 'A', note: 'N', email: 'E', rdv: 'RV', etape: 'É', correction: 'C', ajout: '+', retrait: '×', info: 'i' }

function titreEvenement(e: Evenement): string {
  const res = e.resultat ? RESULTATS.find(([k]) => k === e.resultat)?.[1] : null
  switch (e.type) {
    case 'appel': return res ? `Appel : ${res}` : 'Appel'
    case 'note': return 'Note'
    case 'email': return e.texte?.startsWith('Objet : ') ? `E-mail envoyé : ${e.texte.slice(8).split('\n')[0]}` : 'E-mail écrit'
    case 'rdv': return e.rdv_le ? `Rendez-vous ${quand(e.rdv_le)}` : 'Rendez-vous'
    case 'etape': return e.texte ? e.texte.charAt(0).toUpperCase() + e.texte.slice(1) : 'Étape'
    case 'correction': return 'Fiche corrigée'
    case 'ajout': return 'Ajoutée à la main'
    case 'retrait': return e.texte ? e.texte.charAt(0).toUpperCase() + e.texte.slice(1) : 'Retrait'
    case 'info': return 'Informée de la source de ses coordonnées'
    default: return 'Événement'
  }
}

type PropsFiche = {
  reseau: string; identifiant: string; candidat: Candidat | null; agences: AgenceGti[]; admins: UserProfile[]; monId: string | null
  retour: string; onRetour: () => void; onPatch: (patch: Partial<Candidat>) => void; onRetire: () => void; onOuvrir: (reseau: string, identifiant: string) => void
}

function FicheCandidat({ reseau, identifiant, candidat, agences, admins, monId, retour, onRetour, onPatch, onRetire, onOuvrir }: PropsFiche) {
  const [d, setD] = useState<Detail | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [occupe, setOccupe] = useState(false)
  const [onglet, setOnglet] = useState<Onglet>('appel')
  const [texte, setTexte] = useState('')
  const [resultat, setResultat] = useState<Evenement['resultat']>(null)
  const [reprise, setReprise] = useState(plusMois(6))
  const [rdvLe, setRdvLe] = useState('')
  const [relance, setRelance] = useState<{ quoi: string; le: string } | null>(null)
  const [modale, setModale] = useState<null | 'modifier' | NiveauRetrait>(null)
  const [ecrire, setEcrire] = useState(false)   // E1 : la fenêtre « Écrire » (modèle, aperçu, envoi)
  const saisieRef = useRef<HTMLTextAreaElement | null>(null)
  const hautRef = useRef<HTMLButtonElement | null>(null)
  // la fiche s'ouvre EN HAUT, pas à la hauteur où était la ligne dans la liste
  useEffect(() => { hautRef.current?.scrollIntoView({ block: 'start' }) }, [])

  const relire = useCallback(async () => {
    try {
      setErreur(null)
      setD(await lireCandidat(reseau, identifiant))
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    }
  }, [reseau, identifiant])
  useEffect(() => { void relire() }, [relire])

  // un geste : on l'écrit, on relit la fiche, et la ligne de la liste suit sans tout relire
  const geste = async (faire: () => Promise<void>, patch?: Partial<Candidat>) => {
    if (occupe) return
    setOccupe(true)
    setErreur(null)
    try {
      await faire()
      if (patch) onPatch(patch)
      await relire()
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    } finally {
      setOccupe(false)
    }
  }

  if (!d) {
    return (
      <div className="rc-ecran">
        <button className="rc-retour" type="button" onClick={onRetour} ref={hautRef}>{Ico.retour}{retour}</button>
        {erreur ? <div className="rc-alerte rc-alerte-rouge" role="alert">{erreur}</div> : <p className="rc-mute">Lecture de la fiche…</p>}
      </div>
    )
  }

  const f = d.fiche
  const corr = (champ: string) => d.carnet.find((x) => x.champ === champ) ?? null
  const val = (champ: 'prenom' | 'nom' | 'telephone' | 'email' | 'commune' | 'code_postal' | 'fonction' | 'agence') => {
    const c = corr(champ)
    return c ? c.valeur : f[champ]
  }
  const personne = { prenom: val('prenom'), nom: val('nom') }
  const tel = val('telephone')
  const mail = val('email')
  const commune = val('commune')
  const res = nomReseau(f.reseau)
  const suivi = d.suivi
  const etape = suivi?.etape ?? 1
  const ent = d.entreprise
  const age = ans(ent?.date_creation)
  const dist = candidat?.distance_km
  const proche = candidat?.agence_gti_proche
  const collecte = f.origine === 'collecte'
  const fonction = val('fonction')
  const phrase = [
    f.reseau === 'registre' ? 'Indépendant au registre public'
      : collecte ? (fonction ? `${fonction.charAt(0).toUpperCase()}${fonction.slice(1)} · ${res}` : `Chez ${res}`)
        : [fonction ? `${fonction.charAt(0).toUpperCase()}${fonction.slice(1)}` : '', val('agence') ? `chez ${val('agence')}` : ''].filter(Boolean).join(' ').replace(/^chez/, 'Chez') || 'Ajouté à la main',
    commune ? ` à ${commune}` : '',
    dist != null && proche ? `, à ${virgule(dist)} km de notre agence de ${proche}` : '',
    '.',
  ].join('')
  const dateEtape = (i: number): string => {
    if (i === 0) return collecte ? `le ${jourMois(f.premiere_vue)}, collecte ${res}` : `le ${jourMois(d.fil.find((e) => e.type === 'ajout')?.quand ?? f.premiere_vue)}, à la main`
    const ev = d.fil.find((e) => e.type === 'etape' && e.texte === `étape : ${ETAPES[i]}`)
    return ev ? `le ${jourMois(ev.quand)}` : 'faite'
  }
  const ensuite = suivi?.statut === 'pas_interesse'
    ? `pas intéressé pour l’instant${suivi.reprise_le ? `, à reprendre en ${moisAnnee(suivi.reprise_le)}` : ''}.`
    : suivi?.prochaine_action || suivi?.prochaine_le
      ? `${suivi.prochaine_action ?? 'relancer'}${suivi.prochaine_le ? `, le ${date(suivi.prochaine_le)}` : ''}.`
      : SUITES[etape] ?? SUITES[1]

  const sourceAnnuaire = f.reseau === 'registre' ? 'le registre public des entreprises' : `l’annuaire public des conseillers ${res}`
  const viaAnnuaire = collecte || /annuaire/i.test(f.source_contact ?? '')
  const provenance = (champ: 'telephone' | 'email') => {
    const c = corr(champ)
    if (c) return `corrigé${c.par ? ` par ${c.par}` : ''} le ${date(c.le)}`
    return `${f.source_contact ?? (collecte ? `affiché sur sa fiche ${res}` : 'saisi à la main')}${f.derniere_vue ? `, lu le ${jourMois(f.derniere_vue)}` : ''}`
  }

  const envoyerSaisie = () => {
    const t = texte.trim()
    if (onglet === 'email') {
      if (!mail) return
      const sujet = encodeURIComponent('GTI Immobilier')
      const corps = encodeURIComponent(t)
      window.location.href = `mailto:${mail}?subject=${sujet}${t ? `&body=${corps}` : ''}`
    }
    if (onglet === 'rdv' && !rdvLe) { setErreur('Choisis la date du rendez-vous.'); return }
    if (onglet === 'appel' && !resultat && !t) { setErreur('Dis comment s’est passé l’appel.'); return }
    if (onglet === 'note' && !t) return
    void geste(async () => {
      await noter(f.reseau, f.identifiant, onglet, t, onglet === 'appel' ? resultat : null, onglet === 'rdv' ? new Date(rdvLe).toISOString() : null)
      if (onglet === 'appel' && resultat === 'pas_interesse' && reprise) await majSuivi(f.reseau, f.identifiant, { reprise_le: reprise })
      setTexte(''); setResultat(null); setRdvLe('')
    }, onglet === 'appel' && resultat === 'pas_interesse' ? { statut: 'pas_interesse', reprise_le: reprise || null } : undefined)
  }
  const ouvrirOnglet = (o: Onglet) => { setOnglet(o); window.setTimeout(() => saisieRef.current?.focus(), 0) }

  const fil: Array<Evenement & { synthese?: boolean }> = [
    ...d.fil,
    ...(collecte ? [{ id: -1, quand: f.premiere_vue ?? '', type: 'ajout' as const, resultat: null, texte: `Fiche publique ${res}${commune ? `, ${commune}` : ''}${f.nb_annonces ? `, ${f.nb_annonces} annonces en ligne` : ''}.`, rdv_le: null, par: null, synthese: true }] : []),
  ]

  return (
    <div className="rc-ecran">
      <button className="rc-retour" type="button" onClick={onRetour} ref={hautRef}>{Ico.retour}{retour}</button>

      <header className="rc-f-entete">
        <div className="rc-f-qui">
          <div className="rc-avatar" aria-hidden="true">{initiales(personne)}</div>
          <div style={{ minWidth: 0 }}>
            <h1>{nomComplet(personne)}</h1>
            <p>{phrase}</p>
            <div className="rc-pills">
              <span className="rc-pill rc-p-afaire">{res}</span>
              {candidat?.distinction ? <span className="rc-pill rc-p-club">{candidat.distinction}</span> : null}
              {ent?.opposition ? <span className="rc-pill rc-p-oppose">opposé à la prospection</span>
                : ent?.etat === 'A' ? <span className="rc-pill rc-p-afaire">entreprise active, {libelleAns(age)}</span>
                  : ent?.etat === 'C' ? <span className="rc-pill rc-p-cesse">entreprise cessée</span> : null}
              {candidat?.etat_suivi === 'parti' ? <span className="rc-pill rc-p-cesse">partie de {res}</span> : null}
            </div>
          </div>
        </div>
        <div className="rc-actions">
          {tel ? <a className="rc-btn rc-btn-main" href={telLien(tel)}>{Ico.tel}Appeler</a>
            : <button className="rc-btn rc-btn-main" type="button" disabled title={pourquoiSansContact({ reseau: f.reseau, telephone: null, email: mail })}>{Ico.tel}Appeler</button>}
          <button className="rc-btn rc-btn-quiet" type="button" disabled={!mail} onClick={() => setEcrire(true)}>{Ico.mail}Écrire un e-mail</button>
          <button className="rc-btn rc-btn-quiet" type="button" onClick={() => ouvrirOnglet('rdv')}>{Ico.agenda}Planifier un rendez-vous</button>
          <button className="rc-btn rc-btn-quiet" type="button" onClick={() => setModale('modifier')}>Modifier</button>
          <button className="rc-btn rc-btn-quiet" type="button" aria-label="Retirer ou effacer ce candidat" style={{ padding: '0 12px' }} onClick={() => setModale('archiver')}>{Ico.poubelle}</button>
        </div>
      </header>

      {erreur ? <div className="rc-alerte rc-alerte-rouge" role="alert">{erreur}</div> : null}
      {suivi?.archive ? (
        <div className="rc-archive">
          <span>Retirée de ma liste{suivi.archive_le ? ` le ${date(suivi.archive_le)}` : ''} : elle n’apparaît plus dans le vivier.</span>
          <button className="rc-btn rc-btn-quiet rc-btn-petit" type="button" disabled={occupe} onClick={() => void geste(() => majSuivi(f.reseau, f.identifiant, { archive: false }), { archive: false })}>Remettre dans ma liste</button>
        </div>
      ) : null}

      <section className="rc-parcours" aria-labelledby="rc-parcours">
        <div className="rc-parcours-tete">
          <h2 id="rc-parcours">Son parcours avec nous</h2>
          <p>Clique une étape pour la marquer faite</p>
        </div>
        <ol className="rc-etapes">
          {ETAPES.map((nom, i) => {
            const faite = i < etape
            const courante = i === etape
            return (
              <li key={nom}>
                <button className="rc-etape" type="button" aria-pressed={faite} disabled={occupe}
                  onClick={() => { const n = faite && i + 1 === etape ? i : i + 1; void geste(() => marquerEtape(f.reseau, f.identifiant, n), { etape: n }) }}>
                  <span className="rc-etape-ligne">
                    <span className={`rc-rond${faite ? ' is-faite' : courante ? ' is-courante' : ''}`}>{faite ? Ico.coche : null}</span>
                    <span className={`rc-trait${i === ETAPES.length - 1 ? ' is-fin' : faite ? ' is-faite' : ''}`} />
                  </span>
                  <span className="rc-etape-nom">{nom}</span>
                  <span className="rc-etape-quand">{faite ? dateEtape(i) : courante ? QUAND_COURANTE[i] : ''}</span>
                </button>
              </li>
            )
          })}
        </ol>
        <div className="rc-ensuite">
          {relance ? (
            <div className="rc-relance">
              <input type="text" placeholder="La relancer pour…" aria-label="La relance" value={relance.quoi} onChange={(e) => setRelance({ ...relance, quoi: e.target.value })} />
              <input type="date" aria-label="Le" value={relance.le} onChange={(e) => setRelance({ ...relance, le: e.target.value })} />
              <button className="rc-btn rc-btn-petit" type="button" disabled={occupe || (!relance.quoi.trim() && !relance.le)}
                onClick={() => { const r = relance; void geste(async () => { await majSuivi(f.reseau, f.identifiant, { prochaine_action: r.quoi, prochaine_le: r.le || null }); setRelance(null) }, { prochaine_action: r.quoi.trim() || null, prochaine_le: r.le || null }) }}>Enregistrer</button>
              {suivi?.prochaine_action || suivi?.prochaine_le ? (
                <button className="rc-btn rc-btn-petit" type="button" disabled={occupe}
                  onClick={() => void geste(async () => { await majSuivi(f.reseau, f.identifiant, { prochaine_action: null, prochaine_le: null }); setRelance(null) }, { prochaine_action: null, prochaine_le: null })}>C’est fait</button>
              ) : null}
              <button className="rc-lien" type="button" style={{ color: '#f6b6d5' }} onClick={() => setRelance(null)}>Annuler</button>
            </div>
          ) : (
            <>
              <p><b>Ensuite :</b> {ensuite}</p>
              {suivi?.statut === 'pas_interesse' ? (
                <button className="rc-btn" type="button" disabled={occupe} onClick={() => void geste(() => majSuivi(f.reseau, f.identifiant, { statut: null, reprise_le: null }), { statut: null, reprise_le: null })}>Reprendre le suivi</button>
              ) : (
                <button className="rc-btn" type="button" onClick={() => setRelance({ quoi: suivi?.prochaine_action ?? '', le: suivi?.prochaine_le ?? '' })}>{suivi?.prochaine_action || suivi?.prochaine_le ? 'Changer la relance' : 'Prévoir une relance'}</button>
              )}
            </>
          )}
        </div>
      </section>

      <div className="rc-colonnes">
        <div className="rc-col">
          <section className="rc-bloc" aria-labelledby="rc-joindre">
            <h2 id="rc-joindre">La joindre</h2>
            <div className="rc-ligne"><span className="rc-cle">Téléphone</span><span className="rc-val">{tel ? <><a href={telLien(tel)} className="rc-num" style={{ fontWeight: 700 }}>{tel}</a><span className="rc-src">{provenance('telephone')}</span></> : <span className="rc-mute">{pourquoiSansContact({ reseau: f.reseau, telephone: null, email: 'x' }) || 'aucun'}</span>}</span></div>
            <div className="rc-ligne"><span className="rc-cle">E-mail</span><span className="rc-val">{mail ? <><a href={`mailto:${mail}`} style={{ fontWeight: 700 }}>{mail}</a><span className="rc-src">{provenance('email')}</span></> : <span className="rc-mute">{pourquoiSansContact({ reseau: f.reseau, telephone: 'x', email: null }) || 'aucun'}</span>}</span></div>
            {f.url ? <div className="rc-ligne"><span className="rc-cle">Sa fiche publique</span><a href={f.url} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 600 }}>ouvrir chez {res}</a></div> : null}
          </section>

          <section className="rc-rgpd" aria-labelledby="rc-rgpd">
            <h2 id="rc-rgpd">Au premier contact</h2>
            <p>{viaAnnuaire
              ? <>Dis-lui d’où viennent ses coordonnées : {sourceAnnuaire}. Et qu’elle peut demander à ne plus être contactée.</>
              : <>Ses coordonnées viennent d’elle-même ou de quelqu’un qu’elle connaît{f.source_contact ? ` (${f.source_contact})` : ''} : rien de plus à lui dire.</>}</p>
            <label className="rc-case">
              <input type="checkbox" checked={Boolean(suivi?.info_donnee_le)} disabled={occupe}
                onChange={(e) => { const oui = e.target.checked; void geste(() => majSuivi(f.reseau, f.identifiant, { info_donnee: oui })) }} />
              {suivi?.info_donnee_le ? `C’est fait, informée le ${date(suivi.info_donnee_le)}` : 'C’est fait, la personne est informée'}
            </label>
            <button className="rc-lien" type="button" onClick={() => setModale('ne_plus_contacter')}>Cette personne ne veut plus être contactée</button>
          </section>

          <section className="rc-bloc" aria-labelledby="rc-entreprise">
            <h2 id="rc-entreprise">Son entreprise</h2>
            {f.siren ? (
              <>
                <div className="rc-ligne"><span className="rc-cle">SIREN</span><span className="rc-num">{sirenLisible(f.siren)}</span></div>
                {ent?.opposition ? (
                  <div className="rc-ligne"><span className="rc-cle">Prospection</span><span style={{ color: '#8f3432', fontWeight: 600, textAlign: 'right' }}>opposée au registre : rien d’autre n’est gardé</span></div>
                ) : (
                  <>
                    <div className="rc-ligne"><span className="rc-cle">Créée le</span><span>{ent?.date_creation ? date(ent.date_creation) : '—'}</span></div>
                    <div className="rc-ligne"><span className="rc-cle">État au registre</span><span style={{ color: ent?.etat === 'C' ? '#8a4f0f' : '#2f7d59', fontWeight: 600 }}>{ent?.etat === 'A' ? 'active' : ent?.etat === 'C' ? 'cessée' : 'pas encore lu'}</span></div>
                    {f.rsac_ville ? <div className="rc-ligne"><span className="rc-cle">RSAC</span><span>{f.rsac_ville}</span></div> : null}
                    <div className="rc-ligne"><span className="rc-cle">Prospection</span><span>pas d’opposition au registre</span></div>
                  </>
                )}
              </>
            ) : <p className="rc-texte-doux" style={{ marginTop: 0 }}>{collecte ? `Pas de SIREN affiché sur sa fiche ${res}.` : 'Pas de SIREN saisi.'}</p>}
          </section>
        </div>

        <section className="rc-fil" aria-labelledby="rc-fil">
          <h2 id="rc-fil">Le fil des échanges</h2>
          <div className="rc-saisie">
            <div className="rc-onglets" role="tablist" aria-label="Que veux-tu noter ?">
              {ONGLETS.map(([k, t]) => (
                <button key={k} className={`rc-onglet${onglet === k ? ' is-on' : ''}`} role="tab" type="button" aria-selected={onglet === k} onClick={() => setOnglet(k)}>{t}</button>
              ))}
            </div>
            {onglet === 'email' ? (
              // E1 : un e-mail s'écrit dans la fenêtre « Écrire » (modèle, aperçu, envoi depuis la boîte de l'administrateur)
              <div className="rc-saisie-pied" style={{ padding: '6px 2px' }}>
                <span className="rc-mute" style={{ fontSize: 13 }}>{mail ? 'Modèle rempli depuis sa fiche, aperçu tel qu’elle le recevra, puis envoi.' : 'Pas d’e-mail connu.'}</span>
                <button className="rc-btn rc-btn-main" type="button" style={{ minHeight: 38, marginLeft: 'auto' }} disabled={!mail} onClick={() => setEcrire(true)}>Écrire l’e-mail</button>
              </div>
            ) : (<>
            <label style={{ display: 'block' }}>
              <span style={{ position: 'absolute', left: -9999 }}>{AIDES[onglet]}</span>
              <textarea ref={saisieRef} rows={3} placeholder={AIDES[onglet]} value={texte} onChange={(e) => setTexte(e.target.value)} />
            </label>
            <div className="rc-saisie-pied">
              {onglet === 'appel' ? (
                <div className="rc-resultats">
                  {RESULTATS.map(([k, t]) => (
                    <button key={k} type="button" className={`rc-pill ${k === 'interesse' ? 'rc-p-rdv' : 'rc-p-afaire'}${resultat === k ? ' is-on' : ''}`} aria-pressed={resultat === k} onClick={() => setResultat(resultat === k ? null : k)}>{t}</button>
                  ))}
                  {resultat === 'pas_interesse' ? <label className="rc-mute" style={{ fontSize: 12.5 }}>à reprendre le <input type="date" value={reprise} onChange={(e) => setReprise(e.target.value)} /></label> : null}
                </div>
              ) : onglet === 'rdv' ? (
                <label className="rc-mute" style={{ fontSize: 12.5 }}>le <input type="datetime-local" value={rdvLe} onChange={(e) => setRdvLe(e.target.value)} /></label>
              ) : <span />}
              <button className="rc-btn rc-btn-main" type="button" style={{ minHeight: 38, marginLeft: 'auto' }} disabled={occupe} onClick={envoyerSaisie}>{BOUTONS[onglet]}</button>
            </div>
            </>)}
          </div>
          <ol>
            {fil.map((e) => (
              <li key={e.id}>
                <span aria-hidden="true" className={`rc-puce${e.type === 'appel' || e.type === 'rdv' ? ' is-marque' : ''}`}>{e.synthese ? 'R' : LETTRES[e.type]}</span>
                <div style={{ minWidth: 0 }}>
                  <p className="rc-fil-titre">{e.synthese ? 'Repérée par la collecte' : titreEvenement(e)}</p>
                  {e.type === 'email' && e.texte?.startsWith('Objet : ') ? (
                    <details className="rc-fil-detail"><summary>voir l’e-mail tel qu’envoyé</summary><p className="rc-fil-texte">{e.texte.split('\n').slice(2).join('\n')}</p></details>
                  ) : e.texte && e.type !== 'etape' && e.type !== 'retrait' ? <p className="rc-fil-texte">{texteLisible(e)}</p> : null}
                  <p className="rc-fil-quand">{e.synthese ? `le ${date(e.quand)}` : `${quand(e.quand)}${e.par ? `, ${e.par}` : ''}`}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <div className="rc-col rc-col-droite">
          <section className="rc-bloc" aria-labelledby="rc-activite">
            <h2 id="rc-activite">{collecte ? `Son activité chez ${res}` : 'Son activité'}</h2>
            {collecte ? (
              <div className="rc-chiffres">
                <div><strong className="rc-num">{f.nb_annonces ?? '—'}</strong><span>annonces en ligne</span></div>
                <div><strong className="rc-num">{f.nb_avis ? virgule(Number(f.note_avis ?? 0)) : '—'}</strong><span>{f.nb_avis ? `sur 5, ${f.nb_avis} avis` : 'pas d’avis publié'}</span></div>
              </div>
            ) : null}
            <div className="rc-ligne"><span className="rc-cle">Secteur</span><span className="rc-val">{commune ?? '—'}</span></div>
            <div className="rc-ligne"><span className="rc-cle">{collecte ? 'Vue pour la 1ʳᵉ fois' : 'Ajoutée le'}</span><span>{date(f.premiere_vue) || '—'}</span></div>
            {d.autres.length ? (
              <div className="rc-ligne"><span className="rc-cle">Aussi chez</span><span className="rc-val">{d.autres.map((o, i) => (
                <span key={cle(o)}>{i ? ', ' : ''}<button className="rc-lien" type="button" onClick={() => onOuvrir(o.reseau, o.identifiant)}>{nomReseau(o.reseau)}</button></span>
              ))}</span></div>
            ) : null}
            {collecte ? <p className="rc-texte-doux">Chaque relecture, tous les deux mois, dira si elle change de réseau ou quitte {res}.</p> : null}
          </section>

          <section className="rc-bloc" aria-labelledby="rc-docs">
            <h2 id="rc-docs">Documents</h2>
            <div className="rc-ligne"><span>CV</span><button className="rc-btn rc-btn-quiet rc-btn-petit" type="button" disabled title="Arrive avec la suite du chantier">Déposer</button></div>
            <div className="rc-ligne"><span>Contrat d’agent commercial</span><button className="rc-btn rc-btn-quiet rc-btn-petit" type="button" disabled title="Arrive avec la suite du chantier">Préparer</button></div>
          </section>

          <section className="rc-bloc" aria-labelledby="rc-arrivee">
            <h2 id="rc-arrivee">Quand elle nous rejoint</h2>
            <p className="rc-texte-doux" style={{ margin: '0 0 12px' }}>Une fois le contrat signé, on lui ouvre son accès à bienvu et sa fiche passe dans l’annuaire des négociateurs.</p>
            <button className="rc-btn rc-btn-quiet" type="button" disabled style={{ width: '100%', justifyContent: 'center' }}>Créer son accès à bienvu</button>
          </section>
        </div>
      </div>

      {ecrire && mail ? (
        <ModaleEcrire detail={d} candidat={candidat} a={mail} nom={nomComplet(personne)}
          onFermer={() => setEcrire(false)}
          onEnvoye={(patch) => { onPatch(patch); void relire() }} />
      ) : null}
      {modale === 'modifier' ? (
        <ModaleModifier detail={d} candidat={candidat} agences={agences} admins={admins} monId={monId}
          onFermer={() => setModale(null)}
          onEnregistre={(patch) => { setModale(null); onPatch(patch); void relire() }} />
      ) : modale ? (
        <ModaleRetirer nom={nomComplet(personne)} reseau={f.reseau} identifiant={f.identifiant} initial={modale}
          onFermer={() => setModale(null)}
          onFait={(niveau) => { setModale(null); if (niveau === 'archiver') { onPatch({ archive: true }); void relire() } else onRetire() }} />
      ) : null}
    </div>
  )
}

// ─── les fenêtres ───

function Fenetre({ titre, sousTitre, largeur, icone, onFermer, pied, children }: { titre: string; sousTitre: string; largeur: number; icone?: ReactNode; onFermer: () => void; pied: ReactNode; children: ReactNode }) {
  useEffect(() => {
    const echap = (e: KeyboardEvent) => { if (e.key === 'Escape') onFermer() }
    document.addEventListener('keydown', echap)
    return () => document.removeEventListener('keydown', echap)
  }, [onFermer])
  return (
    <div className="rc-voile">
      <div className="rc-fenetre" role="dialog" aria-modal="true" aria-label={titre} style={{ width: largeur }}>
        <div className="rc-fenetre-tete">
          <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
            {icone}
            <div><h2>{titre}</h2><p>{sousTitre}</p></div>
          </div>
          <button className="rc-fermer" type="button" aria-label="Fermer" onClick={onFermer}>{Ico.fermer}</button>
        </div>
        <div className="rc-fenetre-corps">{children}</div>
        <div className="rc-fenetre-pied">{pied}</div>
      </div>
    </div>
  )
}

const RESEAUX_AJOUT = ['SAFTI', 'iad', 'Capifrance', 'Optimhome', 'BSK Immobilier', 'Keller Williams', 'Dr House Immo', '3G Immo', 'eXp France', 'Megagence', 'Expertimo', 'Autre réseau']
const SOURCES: Array<[string, string]> = [
  ['recommandée par un de nos agents', 'Recommandée par un de nos agents'], ['candidature reçue', 'Candidature reçue'],
  ['rencontrée (salon, réseau, visite)', 'Rencontrée (salon, réseau, visite)'], ['trouvée dans un annuaire public', 'Trouvée dans un annuaire public'],
]

function procheDe(agences: AgenceGti[], lat: number | null, lon: number | null): { nom: string; km: number } | null {
  if (lat == null || lon == null || !agences.length) return null
  return agences.map((a) => ({ nom: a.nom, km: distanceKm(lat, lon, a.lat, a.lon) })).sort((x, y) => x.km - y.km)[0]
}

function ChoixQuiSuit({ admins, monId, valeur, onChange }: { admins: UserProfile[]; monId: string | null; valeur: string; onChange: (v: string) => void }) {
  return (
    <select value={valeur} onChange={(e) => onChange(e.target.value)} aria-label="Qui la suit">
      <option value="">Personne en particulier</option>
      {monId ? <option value={monId}>Moi</option> : null}
      {admins.filter((a) => a.id !== monId).map((a) => <option key={a.id} value={a.id}>{a.display_name || [a.first_name, a.last_name].filter(Boolean).join(' ') || a.email}</option>)}
    </select>
  )
}

function ModaleAjouter({ agences, admins, monId, onFermer, onOuvrir, onAjoute }: {
  agences: AgenceGti[]; admins: UserProfile[]; monId: string | null; onFermer: () => void
  onOuvrir: (reseau: string, identifiant: string) => void; onAjoute: (reseau: string, identifiant: string, ouvrir: boolean) => void
}) {
  const [p, setP] = useState({ prenom: '', nom: '', telephone: '', email: '', siren: '', reseau: RESEAUX_AJOUT[0], agence: '', poste: '', source: SOURCES[0][0], etape: 1, suiviPar: monId ?? '', note: '' })
  const [situation, setSituation] = useState<'reseau' | 'independant' | 'agence' | 'hors'>('reseau')
  const [commune, setCommune] = useState<Commune | null>(null)
  const [saisieCommune, setSaisieCommune] = useState('')
  const [propositions, setPropositions] = useState<Commune[]>([])
  const [doublons, setDoublons] = useState<Doublons | null>(null)
  const [ignorer, setIgnorer] = useState(false)
  const [occupe, setOccupe] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const maj = (champ: keyof typeof p, v: string | number) => setP((x) => ({ ...x, [champ]: v }))

  useEffect(() => {
    if (commune && saisieCommune === `${commune.nom} (${commune.codePostal})`) { setPropositions([]); return }
    const t = window.setTimeout(() => { void chercherCommunes(saisieCommune).then(setPropositions) }, 300)
    return () => window.clearTimeout(t)
  }, [saisieCommune, commune])
  useEffect(() => {
    const assez = p.nom.trim().length >= 2 || p.telephone.replace(/\D/g, '').length >= 9 || p.email.includes('@') || p.siren.replace(/\D/g, '').length === 9
    if (!assez) { setDoublons(null); return }
    const t = window.setTimeout(() => {
      void chercherDoublons({ prenom: p.prenom, nom: p.nom, telephone: p.telephone, email: p.email, siren: p.siren, departement: commune?.departement ?? '' })
        .then((r) => { setDoublons(r); setIgnorer(false) })
        .catch(() => setDoublons(null))
    }, 500)
    return () => window.clearTimeout(t)
  }, [p.prenom, p.nom, p.telephone, p.email, p.siren, commune])

  const proche = procheDe(agences, commune?.lat ?? null, commune?.lon ?? null)
  const annuaire = p.source === SOURCES[3][0]
  const bloque = doublons?.sur_liste_noire === true
  const ajouter = async (ouvrir: boolean) => {
    if (!p.nom.trim()) { setErreur('Le nom est obligatoire.'); return }
    setOccupe(true)
    setErreur(null)
    try {
      const sirenUtile = situation === 'reseau' || situation === 'independant'
      const r = await ajouterCandidat({
        prenom: p.prenom.trim(), nom: p.nom.trim(),
        fonction: situation === 'agence' ? p.poste.trim() : situation === 'independant' ? 'indépendant' : situation === 'hors' ? 'hors immobilier' : '',
        agence: situation === 'reseau' ? p.reseau : situation === 'agence' ? p.agence.trim() : '',
        commune: commune?.nom ?? saisieCommune.trim(), code_postal: commune?.codePostal ?? '', departement: commune?.departement ?? '',
        lat: commune?.lat ?? null, lon: commune?.lon ?? null, agence_gti_proche: proche?.nom ?? '', distance_km: proche ? Math.round(proche.km * 10) / 10 : null,
        telephone: p.telephone.trim(), email: p.email.trim(), source_contact: p.source, siren: sirenUtile ? p.siren : '',
        etape: p.etape, agence_envisagee: '',
      })
      if (p.suiviPar) await majSuivi(r.reseau, r.identifiant, { suivi_par: p.suiviPar })
      if (p.note.trim()) await noter(r.reseau, r.identifiant, 'note', p.note.trim())
      onAjoute(r.reseau, r.identifiant, ouvrir)
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
      setOccupe(false)
    }
  }

  const premier = doublons?.fiches[0]
  return (
    <Fenetre titre="Ajouter un candidat" largeur={720} onFermer={onFermer}
      sousTitre="Quelqu’un qu’on t’a recommandé, une candidature, une rencontre. Les annuaires, eux, sont relus seuls tous les deux mois."
      pied={<>
        {erreur ? <span className="rc-erreur" role="alert">{erreur}</span> : null}
        <button className="rc-btn rc-btn-quiet" type="button" onClick={onFermer}>Annuler</button>
        <button className="rc-btn rc-btn-quiet" type="button" disabled={occupe || bloque} onClick={() => void ajouter(true)}>Ajouter et ouvrir sa fiche</button>
        <button className="rc-btn rc-btn-main" type="button" disabled={occupe || bloque} onClick={() => void ajouter(false)}>Ajouter au vivier</button>
      </>}>
      <div className="rc-groupe">
        <h3>Qui</h3>
        <div className="rc-deux">
          <label className="rc-champ">Prénom<input type="text" value={p.prenom} onChange={(e) => maj('prenom', e.target.value)} /></label>
          <label className="rc-champ">Nom<input type="text" value={p.nom} onChange={(e) => maj('nom', e.target.value)} /></label>
        </div>
        {bloque ? (
          <div className="rc-alerte rc-alerte-rouge" role="alert"><span><strong>Cette personne a demandé à ne plus être contactée.</strong> Elle ne peut pas être ajoutée au vivier.</span></div>
        ) : premier && !ignorer ? (
          <div className="rc-doublon" role="status">
            <p><strong>{doublons!.fiches.length > 1 ? `${doublons!.fiches.length} fiches lui ressemblent dans le vivier` : `${nomComplet(premier)} est déjà dans le vivier`}</strong> : {nomReseau(premier.reseau)}{premier.commune ? ` à ${premier.commune}` : ''}.</p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="rc-btn rc-btn-quiet rc-btn-petit" type="button" onClick={() => onOuvrir(premier.reseau, premier.identifiant)}>Ouvrir sa fiche</button>
              <button className="rc-btn rc-btn-quiet rc-btn-petit" type="button" onClick={() => setIgnorer(true)}>C’est quelqu’un d’autre</button>
            </div>
          </div>
        ) : null}
      </div>

      <div className="rc-groupe">
        <h3>Où</h3>
        <label className="rc-champ">Commune
          <input type="text" value={saisieCommune} placeholder="Nom ou code postal" autoComplete="off"
            onChange={(e) => { setSaisieCommune(e.target.value); setCommune(null) }} />
          {propositions.length && !commune ? (
            <div className="rc-propositions" role="listbox">
              {propositions.map((c) => (
                <button key={`${c.nom}-${c.codePostal}`} type="button" role="option" aria-selected={false} onClick={() => { setCommune(c); setSaisieCommune(`${c.nom} (${c.codePostal})`) }}>{c.nom} ({c.codePostal})</button>
              ))}
            </div>
          ) : null}
        </label>
        {proche ? (
          <p className="rc-ok">{Ico.cocheMarque}{proche.km <= RAYON_KM ? `À ${virgule(proche.km)} km de notre agence de ${proche.nom}.` : `À ${virgule(proche.km)} km de l’agence la plus proche (${proche.nom}).`}</p>
        ) : null}
      </div>

      <div className="rc-groupe">
        <h3>Sa situation aujourd’hui</h3>
        <div className="rc-seg" role="radiogroup" aria-label="Situation">
          {([['reseau', 'Dans un réseau'], ['independant', 'Indépendant'], ['agence', 'Salarié d’agence'], ['hors', 'Hors immobilier']] as const).map(([k, t]) => (
            <button key={k} type="button" role="radio" aria-checked={situation === k} className={situation === k ? 'is-on' : ''} onClick={() => setSituation(k)}>{t}</button>
          ))}
        </div>
        {situation === 'reseau' ? (
          <div className="rc-deux">
            <label className="rc-champ">Réseau<select value={p.reseau} onChange={(e) => maj('reseau', e.target.value)}>{RESEAUX_AJOUT.map((r) => <option key={r}>{r}</option>)}</select></label>
            <label className="rc-champ"><span>SIREN <span className="rc-opt">facultatif</span></span><input type="text" inputMode="numeric" placeholder="9 chiffres, sur sa fiche (RSAC)" value={p.siren} onChange={(e) => maj('siren', e.target.value)} /></label>
          </div>
        ) : situation === 'agence' ? (
          <div className="rc-deux">
            <label className="rc-champ">Agence<input type="text" placeholder="Enseigne et ville, ex. Orpi Saint-Étienne" value={p.agence} onChange={(e) => maj('agence', e.target.value)} /></label>
            <label className="rc-champ">Son poste<input type="text" placeholder="ex. conseillère en transaction" value={p.poste} onChange={(e) => maj('poste', e.target.value)} /></label>
          </div>
        ) : situation === 'independant' ? (
          <label className="rc-champ"><span>SIREN</span><input type="text" inputMode="numeric" placeholder="9 chiffres" value={p.siren} onChange={(e) => maj('siren', e.target.value)} /></label>
        ) : null}
      </div>

      <div className="rc-groupe">
        <h3>La joindre</h3>
        <div className="rc-deux">
          <label className="rc-champ">Téléphone<input type="tel" placeholder="06 00 00 00 00" value={p.telephone} onChange={(e) => maj('telephone', e.target.value)} /></label>
          <label className="rc-champ">E-mail<input type="email" placeholder="prenom.nom@exemple.fr" value={p.email} onChange={(e) => maj('email', e.target.value)} /></label>
        </div>
        <label className="rc-champ">D’où vient ce contact ?
          <select value={p.source} onChange={(e) => maj('source', e.target.value)}>{SOURCES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select>
        </label>
        <p className={`rc-info${annuaire ? ' is-marque' : ''}`}>{annuaire
          ? 'Coordonnées trouvées dans un annuaire : au premier contact, dis-lui d’où elles viennent et qu’elle peut refuser d’être recontactée.'
          : 'Elle nous a donné ses coordonnées elle-même, ou par quelqu’un qu’elle connaît : rien de plus à lui dire.'}</p>
      </div>

      <div className="rc-groupe">
        <h3>Le suivi</h3>
        <div className="rc-deux">
          <label className="rc-champ">Où en est-on ?<select value={p.etape} onChange={(e) => maj('etape', Number(e.target.value))}><option value={1}>Repérée</option><option value={2}>Contactée</option><option value={3}>Rendez-vous</option></select></label>
          <label className="rc-champ">Qui la suit<ChoixQuiSuit admins={admins} monId={monId} valeur={p.suiviPar} onChange={(v) => maj('suiviPar', v)} /></label>
        </div>
        <label className="rc-champ"><span>Note <span className="rc-opt">facultatif</span></span><textarea placeholder="Ce qu’on t’a dit d’elle, ce qu’elle cherche" value={p.note} onChange={(e) => maj('note', e.target.value)} /></label>
      </div>
    </Fenetre>
  )
}

type ChampModif = 'nom' | 'telephone' | 'email' | 'commune'
function ModaleModifier({ detail, candidat, agences, admins, monId, onFermer, onEnregistre }: {
  detail: Detail; candidat: Candidat | null; agences: AgenceGti[]; admins: UserProfile[]; monId: string | null
  onFermer: () => void; onEnregistre: (patch: Partial<Candidat>) => void
}) {
  const f = detail.fiche
  const res = nomReseau(f.reseau)
  const collecte = f.origine === 'collecte'
  const corr = (champ: string) => detail.carnet.find((x) => x.champ === champ) ?? null
  const shown = (champ: ChampCorrigeable) => { const c = corr(champ); return (c ? c.valeur : f[champ]) ?? '' }
  const [edition, setEdition] = useState<Partial<Record<ChampModif, boolean>>>({})
  const [v, setV] = useState({ prenom: shown('prenom'), nom: shown('nom'), telephone: shown('telephone'), email: shown('email'), commune: shown('commune'), code_postal: shown('code_postal') })
  const [revenir, setRevenir] = useState<Set<ChampCorrigeable>>(new Set())
  const [agenceEnv, setAgenceEnv] = useState(detail.suivi?.agence_envisagee ?? '')
  const [suiviPar, setSuiviPar] = useState(detail.suivi?.suivi_par ?? '')
  const [occupe, setOccupe] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)

  // ⚠ des FONCTIONS appelées, pas des composants : un composant déclaré ici changerait à chaque frappe et
  //   React remonterait la saisie (le curseur sortirait du champ à chaque lettre).
  const prov = (champ: ChampCorrigeable, enEdition = false) => {
    const c = corr(champ)
    if (enEdition) return <div className="rc-prov is-corrige"><span className="rc-point is-corrige" />{collecte ? `ta correction remplacera la valeur lue chez ${res}` : 'ta correction remplacera la saisie'}</div>
    if (revenir.has(champ)) return <div className="rc-prov is-corrige"><span className="rc-point is-corrige" />reviendra à la valeur lue chez {res}</div>
    if (c) return <div className="rc-prov is-corrige"><span className="rc-point is-corrige" />corrigé{c.par ? ` par ${c.par}` : ''} le {date(c.le)}</div>
    return collecte
      ? <div className="rc-prov"><span className="rc-point is-lu" />lu sur sa fiche {res}{f.derniere_vue ? ` le ${jourMois(f.derniere_vue)}` : ''}</div>
      : <div className="rc-prov"><span className="rc-point is-saisi" />saisi à la main</div>
  }
  const rangee = (lib: string, champ: ChampModif, champs: ChampCorrigeable[], rendu: ReactNode) => {
    const enEdition = Boolean(edition[champ])
    const corrige = champs.some((x) => corr(x)) && !champs.some((x) => revenir.has(x))
    return (
      <div className="rc-rangee">
        <span className="rc-lib">{lib}</span>
        <div>{enEdition ? rendu : <div className="rc-v">{champs.map((x) => (revenir.has(x) ? f[x] : shown(x))).filter(Boolean).join(' ') || '—'}</div>}{prov(champs[champs.length - 1], enEdition)}</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
          <button className="rc-lien" type="button" onClick={() => setEdition({ ...edition, [champ]: !enEdition })}>{enEdition ? 'Ne pas changer' : 'Corriger'}</button>
          {collecte && corrige && !enEdition ? (
            <button className="rc-lien" type="button" onClick={() => { const n = new Set(revenir); champs.forEach((x) => { if (corr(x)) n.add(x) }); setRevenir(n) }}>Revenir à celle de {res}</button>
          ) : null}
        </div>
      </div>
    )
  }

  const enregistrer = async () => {
    setOccupe(true)
    setErreur(null)
    const patch: Partial<Candidat> = {}
    try {
      for (const champ of revenir) {
        await corriger(f.reseau, f.identifiant, champ, null, true)
        ;(patch as Record<string, unknown>)[champ] = f[champ]
      }
      const groupes: Record<ChampModif, ChampCorrigeable[]> = { nom: ['prenom', 'nom'], telephone: ['telephone'], email: ['email'], commune: ['commune', 'code_postal'] }
      for (const [g, champs] of Object.entries(groupes) as Array<[ChampModif, ChampCorrigeable[]]>) {
        if (!edition[g]) continue
        for (const champ of champs) {
          const neuf = (v as Record<string, string>)[champ].trim()
          if (neuf === String(shown(champ) ?? '').trim()) continue
          await corriger(f.reseau, f.identifiant, champ, neuf || null)
          ;(patch as Record<string, unknown>)[champ] = neuf || null
          patch.corrige = true
        }
      }
      const suivi: { agence_envisagee?: string | null; suivi_par?: string | null } = {}
      if (agenceEnv !== (detail.suivi?.agence_envisagee ?? '')) suivi.agence_envisagee = agenceEnv || null
      if (suiviPar !== (detail.suivi?.suivi_par ?? '')) { suivi.suivi_par = suiviPar || null; patch.suivi_par = suiviPar || null }
      if (Object.keys(suivi).length) await majSuivi(f.reseau, f.identifiant, suivi)
      onEnregistre(patch)
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
      setOccupe(false)
    }
  }

  const historique = [
    ...detail.fil.filter((e) => e.type === 'correction' || e.type === 'ajout').map((e) => ({ k: `e${e.id}`, t: texteLisible(e) ?? titreEvenement(e), q: e.quand, par: e.par })),
    ...(collecte ? [{ k: 'n', t: `fiche créée par la collecte ${res}`, q: f.premiere_vue ?? '', par: null as string | null }] : []),
  ]
  const nomActuel = nomComplet({ prenom: shown('prenom') || null, nom: shown('nom') || null })
  return (
    <Fenetre titre={`Modifier la fiche de ${nomActuel}`} largeur={760} onFermer={onFermer}
      sousTitre="Ce qui vient des annuaires est relu tous les deux mois. Ce que tu corriges ici reste, même après la relecture."
      pied={<>
        {erreur ? <span className="rc-erreur" role="alert">{erreur}</span> : null}
        <button className="rc-btn rc-btn-quiet" type="button" onClick={onFermer}>Annuler</button>
        <button className="rc-btn rc-btn-main" type="button" disabled={occupe} onClick={() => void enregistrer()}>Enregistrer les modifications</button>
      </>}>
      <div className="rc-legende">
        <span><span className="rc-point is-lu" />lu dans un annuaire</span>
        <span><span className="rc-point is-corrige" />corrigé par nous, la relecture n’y touche plus</span>
        <span><span className="rc-point is-saisi" />saisi à la main</span>
      </div>

      <h3>Qui et comment la joindre</h3>
      {rangee('Prénom et nom', 'nom', ['prenom', 'nom'],
        <div className="rc-deux">
          <input className="rc-saisie-champ" aria-label="Prénom corrigé" value={v.prenom} onChange={(e) => setV({ ...v, prenom: e.target.value })} />
          <input className="rc-saisie-champ" aria-label="Nom corrigé" value={v.nom} onChange={(e) => setV({ ...v, nom: e.target.value })} />
        </div>)}
      {rangee('Téléphone', 'telephone', ['telephone'], <input className="rc-saisie-champ" type="tel" aria-label="Téléphone corrigé" value={v.telephone} onChange={(e) => setV({ ...v, telephone: e.target.value })} />)}
      {rangee('E-mail', 'email', ['email'], <input className="rc-saisie-champ" type="email" aria-label="E-mail corrigé" value={v.email} onChange={(e) => setV({ ...v, email: e.target.value })} />)}

      <h3>{collecte ? 'Ce que disent les annuaires' : 'Ce qui a été saisi'}</h3>
      {collecte ? <p style={{ margin: '0 0 4px', fontSize: 12.5, color: '#5c6163' }}>Ces lignes changent seules : si elle quitte {res} ou rejoint un autre réseau, tu le verras ici et dans son fil.</p> : null}
      <div className="rc-rangee"><span className="rc-lib">Réseau</span><div><div className="rc-v">{collecte ? res : (f.agence || f.fonction || '—')}</div>{collecte ? <div className="rc-prov"><span className="rc-point is-lu" />relu le {jourMois(f.derniere_vue)}</div> : null}</div><span /></div>
      {collecte ? <div className="rc-rangee"><span className="rc-lib">Annonces et avis</span><div><div className="rc-v">{f.nb_annonces != null ? `${f.nb_annonces} annonces` : '—'}{f.nb_avis ? `, ${virgule(Number(f.note_avis ?? 0))} sur 5 (${f.nb_avis} avis)` : ''}</div></div><span /></div> : null}
      {rangee('Commune', 'commune', ['commune', 'code_postal'],
        <div className="rc-deux">
          <input className="rc-saisie-champ" aria-label="Commune corrigée" value={v.commune} onChange={(e) => setV({ ...v, commune: e.target.value })} />
          <input className="rc-saisie-champ" aria-label="Code postal corrigé" inputMode="numeric" value={v.code_postal} onChange={(e) => setV({ ...v, code_postal: e.target.value })} />
        </div>)}
      {candidat?.distance_km != null && candidat.agence_gti_proche ? <p className="rc-texte-doux">À {virgule(candidat.distance_km)} km de notre agence de {candidat.agence_gti_proche}.</p> : null}

      <h3>Notre suivi</h3>
      <div className="rc-rangee">
        <span className="rc-lib">Agence envisagée</span>
        <div><select className="rc-saisie-champ" aria-label="Agence envisagée" value={agenceEnv} onChange={(e) => setAgenceEnv(e.target.value)}>
          <option value="">Pas encore choisie</option>
          {agences.map((a) => <option key={a.nom} value={a.nom}>{a.nom}</option>)}
        </select>{detail.suivi?.agence_envisagee ? <div className="rc-prov"><span className="rc-point is-saisi" />saisi par nous</div> : null}</div>
        <span />
      </div>
      <div className="rc-rangee">
        <span className="rc-lib">Qui la suit</span>
        <div className="rc-champ"><ChoixQuiSuit admins={admins} monId={monId} valeur={suiviPar} onChange={setSuiviPar} /></div>
        <span />
      </div>

      <h3>Ce qui a changé sur cette fiche</h3>
      <ol className="rc-histo">
        {historique.length ? historique.map((h) => <li key={h.k}><strong>{h.t.charAt(0).toUpperCase() + h.t.slice(1)}</strong>{h.par ? `, par ${h.par}` : ''}{h.q ? `, ${h.q.length === 10 ? `le ${date(h.q)}` : quand(h.q)}` : ''}</li>) : <li>Rien encore.</li>}
      </ol>
    </Fenetre>
  )
}

function ModaleRetirer({ nom, reseau, identifiant, initial, onFermer, onFait }: {
  nom: string; reseau: string; identifiant: string; initial: NiveauRetrait; onFermer: () => void; onFait: (niveau: NiveauRetrait) => void
}) {
  const [choix, setChoix] = useState<NiveauRetrait>(initial)
  // ne compte que pour « ne plus contacter » et « effacer », qui se choisissent le plus souvent à sa demande
  const [qui, setQui] = useState<'elle_meme' | 'notre_decision'>('elle_meme')
  const [le, setLe] = useState(aujourdhui())
  const [saisie, setSaisie] = useState('')
  const [occupe, setOccupe] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const C: Array<{ k: NiveauRetrait; titre: string; texte: string; reste: string; action: string; danger: boolean }> = [
    { k: 'archiver', titre: 'La retirer de ma liste', texte: 'Elle sort du vivier et ne revient pas à la relecture. Sa fiche reste dans les archives, tu peux la remettre en un clic.', reste: 'Reste : toute sa fiche, en archives.', action: 'Retirer de ma liste', danger: false },
    { k: 'ne_plus_contacter', titre: 'Ne plus jamais la contacter', texte: 'À choisir quand elle le demande. Son téléphone, son e-mail, ses notes et son fil sont effacés, et toutes ses autres fiches avec.', reste: 'Reste : son nom, son SIREN et la date de sa demande, pour que la collecte ne la remette jamais dans la liste.', action: 'Ne plus la contacter', danger: false },
    { k: 'effacer', titre: 'Effacer toutes ses données', texte: 'Quand elle demande que tout soit effacé. Rien ne reste lisible.', reste: 'Reste : une empreinte illisible, sans nom, qui empêche seulement de la réimporter.', action: 'Effacer définitivement', danger: true },
  ]
  const c = C.find((x) => x.k === choix)!
  const definitif = choix !== 'archiver'
  const bloque = choix === 'effacer' && saisie.trim().toUpperCase() !== 'EFFACER'
  const agir = async () => {
    setOccupe(true)
    setErreur(null)
    try {
      await retirerCandidat(reseau, identifiant, choix, qui, le)
      onFait(choix)
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
      setOccupe(false)
    }
  }
  return (
    <Fenetre titre={`Retirer ${nom}`} sousTitre="Choisis ce qui doit rester d’elle." largeur={680} onFermer={onFermer}
      icone={<span aria-hidden="true" style={{ flex: '0 0 40px', height: 40, borderRadius: 12, background: '#b94a48', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>{Ico.poubelle}</span>}
      pied={<>
        {erreur ? <span className="rc-erreur" role="alert">{erreur}</span> : null}
        <button className="rc-btn rc-btn-quiet" type="button" onClick={onFermer}>Annuler</button>
        <button className={`rc-btn ${c.danger ? 'rc-btn-danger' : 'rc-btn-main'}`} type="button" disabled={occupe || bloque} onClick={() => void agir()}>{c.action}</button>
      </>}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: '16px 0' }}>
        <div role="radiogroup" aria-label="Que faire de cette fiche ?" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {C.map((x) => {
            const on = x.k === choix
            const coul = x.danger ? '#b94a48' : '#c5005f'
            return (
              <button key={x.k} className="rc-choix" type="button" role="radio" aria-checked={on} onClick={() => { setChoix(x.k); setSaisie('') }}
                style={on ? { border: `2px solid ${coul}`, background: x.danger ? '#fdf6f6' : '#fdf0f6', padding: 15 } : undefined}>
                <span className="rc-radio" aria-hidden="true" style={{ borderColor: on ? coul : '#9aa0a2' }}><span style={{ background: on ? coul : 'transparent' }} /></span>
                <span><span className="t">{x.titre}</span><span className="d">{x.texte}</span><span className={`r${x.danger ? ' is-danger' : ''}`}>{x.reste}</span></span>
              </button>
            )
          })}
        </div>
        {definitif ? (
          <div className="rc-deux" style={{ paddingTop: 6 }}>
            <label className="rc-champ">Qui le demande ?<select value={qui} onChange={(e) => setQui(e.target.value as 'elle_meme' | 'notre_decision')}><option value="elle_meme">Elle-même</option><option value="notre_decision">Notre décision</option></select></label>
            <label className="rc-champ">Le<input type="date" value={le} onChange={(e) => setLe(e.target.value)} /></label>
          </div>
        ) : null}
        {choix === 'effacer' ? (
          <div className="rc-definitif">
            <p><strong>Définitif.</strong> Son fil d’échanges, ses notes et toutes ses fiches disparaissent. On ne pourra pas revenir en arrière.</p>
            <label className="rc-champ" style={{ color: '#7d2f2d' }}>Tape EFFACER pour confirmer<input type="text" value={saisie} onChange={(e) => setSaisie(e.target.value)} aria-label="Tape EFFACER pour confirmer" style={{ borderColor: '#e3a3a1' }} /></label>
          </div>
        ) : choix === 'ne_plus_contacter' ? (
          <p className="rc-info">Toutes ses fiches partent (même SIREN, même téléphone, même e-mail, même nom dans le même département), et elle ne pourra plus être rajoutée.</p>
        ) : null}
      </div>
    </Fenetre>
  )
}

// ─── E1 (24/11/2026) : écrire à UN candidat — maquette, planche 1 ───
// Le modèle se remplit depuis la fiche ; l'objet et le texte se modifient ; ce qui reste [À COMPLÉTER] bloque l'envoi ;
// le bloc d'information RGPD est AJOUTÉ SEUL et ne se retire pas ; l'aperçu est le HTML exact qu'elle recevra.
// Envoi par la boîte de l'administrateur (route Gmail existante) si `recrutement_envoi_email` est allumé ; sinon la
// messagerie s'ouvre avec le texte prêt. Après : le fil note l'e-mail, l'étape passe à « Contactée », « informée » se coche.
function ModaleEcrire({ detail, candidat, a, nom, onFermer, onEnvoye }: {
  detail: Detail; candidat: Candidat | null; a: string; nom: string; onFermer: () => void; onEnvoye: (patch: Partial<Candidat>) => void
}) {
  const f = detail.fiche
  const [de, setDe] = useState<Expediteur | null>(null)
  const [reglages, setReglages] = useState<Reglages | null>(null)
  const [modele, setModele] = useState<ModeleCle>(detail.fil.some((e) => e.type === 'email') ? 'relance' : 'premier')
  const [objet, setObjet] = useState('')
  const [corps, setCorps] = useState('')
  const [pieces, setPieces] = useState<GmailPieceOrdinateur[]>([])
  const [depots, setDepots] = useState(0)
  const [tel, setTel] = useState(false)
  const [etat, setEtat] = useState<'ecrire' | 'envoi' | 'envoye'>('ecrire')
  const [parApp, setParApp] = useState(true)
  const [erreur, setErreur] = useState<string | null>(null)
  // ce que l'envoi a fait, gardé AU MOMENT de l'envoi (la fiche relue ensuite ne le dit plus)
  const [fait, setFait] = useState<{ etape: boolean; informee: boolean }>({ etape: false, informee: false })
  const fichierRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    let annule = false
    void Promise.all([lireExpediteur(), lireReglages()]).then(([e, r]) => { if (!annule) { setDe(e); setReglages(r) } })
    return () => { annule = true }
  }, [])
  // le modèle se remplit à l'ouverture (dès que l'expéditeur est connu) et à chaque changement de modèle
  useEffect(() => {
    const m = MODELES.find((x) => x.cle === modele) ?? MODELES[0]
    const v = valeursPour(detail, candidat, de)
    setObjet(remplir(m.objet, v))
    setCorps(remplir(m.texte, v))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modele, de])

  const bloc = reglages ? blocTexte(detail, reglages) : ''
  const blocComplet = blocDu(detail)
  const source = sourceDe(detail)
  const aCompleter = [...trous(objet), ...trous(corps)]
  const reglagesManquants = trous(bloc)
  const opposition = detail.entreprise?.opposition === true
  const envoiApp = reglages?.envoi === true
  const pret = Boolean(de && reglages) && !aCompleter.length && !reglagesManquants.length && !opposition
    && Boolean(objet.trim()) && Boolean(corps.trim()) && depots === 0 && etat === 'ecrire'
  const apercu = useMemo(() => htmlEmail(corps, bloc || ' '), [corps, bloc])
  const prenom = valeursPour(detail, candidat, de).prenom

  // ce qui suit un envoi : le fil, l'étape, « informée »
  const noterEnvoi = async () => {
    await noter(f.reseau, f.identifiant, 'email', `Objet : ${objet.trim()}\n\n${texteComplet(corps, bloc)}`)
    const patch: Partial<Candidat> = { dernier_email: new Date().toISOString(), ...(blocComplet ? { info_donnee_le: new Date().toISOString() } : {}) }
    const avancer = (detail.suivi?.etape ?? 1) < 2
    if (avancer) { await marquerEtape(f.reseau, f.identifiant, 2); patch.etape = 2 }
    if (blocComplet) await majSuivi(f.reseau, f.identifiant, { info_donnee: true })
    setFait({ etape: avancer, informee: blocComplet })
    onEnvoye(patch)
  }

  const envoyerParApp = async () => {
    if (!pret || !de) return
    setEtat('envoi')
    setErreur(null)
    try {
      await envoyerEmail({ de, a, objet, corps, bloc, pieces, reseau: f.reseau, identifiant: f.identifiant })
    } catch (e) {
      setErreur(`L’e-mail n’est pas parti : ${e instanceof Error ? e.message : String(e)}`)
      setEtat('ecrire')
      return
    }
    try {
      await noterEnvoi()
    } catch (e) {
      setErreur(`L’e-mail est PARTI, mais le fil n’a pas pu être mis à jour : ${e instanceof Error ? e.message : String(e)}`)
    }
    setParApp(true)
    setEtat('envoye')
  }

  const ouvrirMessagerie = async () => {
    if (!pret) return
    const texte = texteComplet(corps, bloc)
    try { await navigator.clipboard.writeText(texte) } catch { /* sans presse-papiers, le mailto porte le texte s'il tient */ }
    const complet = `mailto:${a}?subject=${encodeURIComponent(objet.trim())}&body=${encodeURIComponent(texte)}`
    window.location.href = complet.length <= 1900 ? complet : `mailto:${a}?subject=${encodeURIComponent(objet.trim())}`
    try { await noterEnvoi() } catch (e) { setErreur(`Le fil n’a pas pu être mis à jour : ${e instanceof Error ? e.message : String(e)}`) }
    setParApp(false)
    setEtat('envoye')
  }

  const ajouterFichiers = async (liste: FileList | null) => {
    const fichiers = Array.from(liste ?? [])
    if (fichierRef.current) fichierRef.current.value = ''
    const refus: string[] = []
    const retenus = fichiers.filter((x) => {
      if (x.size > gmailPieceTailleMax) { refus.push(`« ${x.name} » dépasse 8 Mo.`); return false }
      return true
    }).slice(0, Math.max(0, 10 - pieces.length))
    setErreur(refus.length ? refus.join(' ') : null)
    setDepots((n) => n + retenus.length)
    await Promise.all(retenus.map(async (x) => {
      try { const p = await deposerPieceEmail(x); setPieces((c) => [...c, p]) }
      catch (e) { setErreur(e instanceof Error ? e.message : `« ${x.name} » n’a pas pu être déposé.`) }
      finally { setDepots((n) => n - 1) }
    }))
  }
  const retirerPiece = (id: string) => {
    setPieces((c) => c.filter((p) => p.id !== id))
    retirerPieceEmail(id).catch(() => undefined) // sinon le ménage des temporaires le retire après 2 jours
  }

  if (etat === 'envoye') {
    return (
      <Fenetre titre={parApp ? `Envoyé à ${nom}` : `Votre messagerie s’est ouverte pour ${nom}`} largeur={620} onFermer={onFermer}
        sousTitre={parApp ? `Parti de ${de?.email ?? 'votre boîte'}.` : 'Le texte est prêt dans votre messagerie, et copié : collez-le s’il manque.'}
        pied={<button className="rc-btn rc-btn-main" type="button" onClick={onFermer}>Fermer</button>}>
        <div style={{ padding: '16px 0', display: 'flex', flexDirection: 'column', gap: 10, fontSize: 14, lineHeight: 1.5 }}>
          {erreur ? <div className="rc-alerte rc-alerte-rouge" role="alert">{erreur}</div> : null}
          <p style={{ margin: 0 }}>Le fil des échanges note l’e-mail{fait.etape ? ', l’étape passe à « Contactée »' : ''}{fait.informee ? ', et la case « informée » est cochée' : ''}.</p>
          {!parApp && pieces.length ? <p className="rc-mute" style={{ margin: 0 }}>Les pièces jointes ne partent qu’avec l’envoi depuis l’app : joignez-les dans votre messagerie.</p> : null}
        </div>
      </Fenetre>
    )
  }

  return (
    <Fenetre titre={`Écrire à ${nom}`} largeur={1180} onFermer={onFermer}
      sousTitre={envoiApp ? 'Le message part de votre boîte Gmail. Rien ne part sans votre clic.' : 'Votre messagerie s’ouvrira avec le texte prêt (l’envoi depuis l’app n’est pas encore allumé).'}
      pied={<>
        <span className={erreur ? 'rc-erreur' : 'rc-mute'} role={erreur ? 'alert' : undefined} style={{ marginRight: 'auto', fontSize: 13 }}>
          {erreur ?? (opposition ? 'Opposée à la prospection au registre : on ne lui écrit pas.'
            : aCompleter.length ? `À compléter avant d’envoyer : ${aCompleter.join(', ')}.`
              : reglagesManquants.length ? 'Le bloc d’information attend deux réglages : l’adresse postale de GTI et l’adresse de contact pour les données.'
                : !de ? 'Lecture de votre boîte…' : '')}
        </span>
        <button className="rc-btn rc-btn-quiet" type="button" onClick={onFermer}>Annuler</button>
        {envoiApp
          ? <button className="rc-btn rc-btn-main" type="button" disabled={!pret} onClick={() => void envoyerParApp()}>{etat === 'envoi' ? 'Envoi…' : `Envoyer à ${prenom.startsWith('{') ? nom : prenom}`}</button>
          : <button className="rc-btn rc-btn-main" type="button" disabled={!pret} onClick={() => void ouvrirMessagerie()}>Ouvrir ma messagerie</button>}
      </>}>
      <div className="rc-ecrire">
        <div className="rc-ecrire-saisie">
          <div className="rc-champ">Modèle
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {MODELES.map((m) => (
                <button key={m.cle} type="button" className={`rc-chip${modele === m.cle ? ' is-on' : ''}`} aria-pressed={modele === m.cle} onClick={() => setModele(m.cle)}>{m.nom}</button>
              ))}
            </div>
          </div>
          <div className="rc-deux">
            <div className="rc-champ">De<span className="rc-saisie-champ rc-lecture">{de?.email ?? '…'}</span></div>
            <div className="rc-champ">À<span className="rc-saisie-champ rc-lecture">{a}</span></div>
          </div>
          <label className="rc-champ">Objet<input type="text" value={objet} onChange={(e) => setObjet(e.target.value)} /></label>
          <label className="rc-champ">Message<textarea className="rc-ecrire-texte" value={corps} onChange={(e) => setCorps(e.target.value)} /></label>
          {aCompleter.length ? <p className="rc-trous">À compléter : {aCompleter.join(', ')} — remplacez ces passages dans le texte.</p> : null}
          {opposition ? <div className="rc-alerte rc-alerte-rouge" role="alert"><span>Cette personne s’est <strong>opposée à la prospection</strong> au registre des entreprises : on ne lui écrit pas.</span></div> : null}
          <div className="rc-verrou">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flex: '0 0 auto', marginTop: 2 }}><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
            <span>{blocComplet
              ? <><strong>Ajouté seul, et il reste :</strong> d’où vient son adresse ({source}), ce que nous gardons, combien de temps, ses droits, et « Ne plus me contacter ».</>
              : <><strong>Ajouté seul :</strong> la ligne « Ne plus me contacter »{detail.suivi?.info_donnee_le ? ` (informée depuis le ${date(detail.suivi.info_donnee_le)})` : ''}.</>}</span>
          </div>
          <div className="rc-champ">Pièces jointes
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
              {pieces.map((p) => (
                <span key={p.id} className="rc-chip is-on">{p.nom}<button type="button" className="rc-lien" aria-label={`Retirer ${p.nom}`} onClick={() => retirerPiece(p.id)} style={{ marginLeft: 4 }}>{Ico.croix}</button></span>
              ))}
              <button className="rc-chip" type="button" disabled={pieces.length >= 10} onClick={() => fichierRef.current?.click()}>{depots ? 'Dépôt…' : 'Ajouter un fichier'}</button>
              <input ref={fichierRef} type="file" multiple hidden onChange={(e) => void ajouterFichiers(e.target.files)} />
            </div>
            {!envoiApp && pieces.length ? <span className="rc-mute" style={{ fontWeight: 500, fontSize: 12 }}>Avec la messagerie, les pièces se joignent à la main.</span> : null}
          </div>
        </div>
        <div className="rc-ecrire-apercu">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <p style={{ margin: 0, fontSize: 14, fontWeight: 700 }}>Aperçu — tel qu’elle le recevra</p>
            <div className="rc-seg" role="group" aria-label="Format de l’aperçu">
              <button type="button" className={tel ? '' : 'is-on'} aria-pressed={!tel} onClick={() => setTel(false)}>Bureau</button>
              <button type="button" className={tel ? 'is-on' : ''} aria-pressed={tel} onClick={() => setTel(true)}>Téléphone</button>
            </div>
          </div>
          <div className={`rc-ecrire-cadre${tel ? ' is-tel' : ''}`}>
            <div className="rc-ecrire-tetes">
              <div><strong>De :</strong> {de ? `${de.nom} — GTI Immobilier` : '…'}</div>
              <div><strong>Objet :</strong> {objet || '—'}</div>
              {pieces.length ? <div><strong>Pièces :</strong> {pieces.map((p) => p.nom).join(', ')}</div> : null}
            </div>
            {/* sans aucun script (pas d'allow-scripts) : le HTML est le nôtre, texte échappé ; « same-origin » pour qu'il s'affiche partout */}
            <iframe title="Aperçu de l’e-mail" sandbox="allow-same-origin" srcDoc={apercu} />
          </div>
        </div>
      </div>
    </Fenetre>
  )
}

// ─── E2 (24/11/2026) : écrire à PLUSIEURS candidats — maquette, planches 2 (écrire) et 3 (l'envoi, un par un) ───
// UN e-mail PAR personne (jamais une liste de destinataires), à son prénom, avec SA source et son bloc RGPD.
// Écartés avant d'envoyer, et l'écran dit pourquoi : pas d'e-mail ; opposé au registre (d'office) ; déjà écrit il y a moins
// de 30 jours (« lui écrire quand même »). Envoi doux : un toutes les 5 s, 40 par jour et par expéditeur (rec_emails_du_jour).
// ⚠ L'envoi tourne DANS CETTE FENÊTRE : elle doit rester ouverte (la maquette disait « vous pouvez fermer » : il faudrait une
//   file côté serveur, pas faite ici). « Arrêter l'envoi » s'arrête après le message en cours.
type EtatEnvoi = { etat: 'attente' | 'encours' | 'envoye' | 'refuse'; heure?: string; erreur?: string }

function ModaleGroupe({ candidats, onFermer, onPatch, onFini }: {
  candidats: Candidat[]; onFermer: () => void; onPatch: (cle: string, patch: Partial<Candidat>) => void; onFini: () => void
}) {
  const [de, setDe] = useState<Expediteur | null>(null)
  const [reglages, setReglages] = useState<Reglages | null>(null)
  const [dejaAujourdhui, setDejaAujourdhui] = useState<number | null | undefined>(undefined)
  const [modele, setModele] = useState<ModeleCle>('premier')
  const [objet, setObjet] = useState(MODELES[0].objet)
  const [corps, setCorps] = useState(MODELES[0].texte)
  const [surcharges, setSurcharges] = useState<Record<string, string>>({})
  const [retouche, setRetouche] = useState(false)
  const [inclure, setInclure] = useState<Set<string>>(new Set())
  const [i, setI] = useState(0)
  const [phase, setPhase] = useState<'ecrire' | 'envoi' | 'fini'>('ecrire')
  const [etats, setEtats] = useState<Record<string, EtatEnvoi>>({})
  const [ordre, setOrdre] = useState<Array<{ k: string; nom: string; detail: string }>>([])
  const arret = useRef(false)

  useEffect(() => {
    let annule = false
    void Promise.all([lireExpediteur(), lireReglages(), emailsDuJour()]).then(([e, r, n]) => {
      if (!annule) { setDe(e); setReglages(r); setDejaAujourdhui(n) }
    })
    return () => { annule = true }
  }, [])
  // un autre modèle : le texte commun repart du modèle, les retouches par personne aussi
  useEffect(() => {
    const m = MODELES.find((x) => x.cle === modele) ?? MODELES[0]
    setObjet(m.objet)
    setCorps(m.texte)
    setSurcharges({})
    setRetouche(false)
  }, [modele])

  // qui reçoit, qui est écarté, et pourquoi
  const ecartes: Array<{ c: Candidat; raison: string }> = []
  const recents: Array<{ c: Candidat; raison: string }> = []
  const recevront: Candidat[] = []
  for (const c of candidats) {
    const jours = c.dernier_email ? Math.floor((Date.now() - new Date(c.dernier_email).getTime()) / 86400000) : null
    if (!c.email) ecartes.push({ c, raison: 'pas d’e-mail public' })
    else if (c.opposition) ecartes.push({ c, raison: 'opposé à la prospection au registre : écarté d’office' })
    else if (jours != null && jours < JOURS_ENTRE_DEUX) {
      recents.push({ c, raison: jours === 0 ? 'déjà écrit aujourd’hui' : `déjà écrit le ${date(c.dernier_email)}, il y a ${jours} jour${jours > 1 ? 's' : ''}` })
      if (inclure.has(cle(c))) recevront.push(c)
    } else recevront.push(c)
  }
  const nbEcartes = ecartes.length + recents.filter((r) => !inclure.has(cle(r.c))).length
  const restant = dejaAujourdhui == null ? 0 : Math.max(0, PLAFOND_JOUR - dejaAujourdhui)
  const partent = recevront.slice(0, restant)
  const demain = recevront.length - partent.length

  const pour = (c: Candidat) => {
    const ctx = contexteDe(c)
    const v = valeursPour(ctx, c, de)
    const k = cle(c)
    return {
      k, c, objet: remplir(objet, v), corps: surcharges[k] ?? remplir(corps, v),
      bloc: reglages ? blocTexte(ctx, reglages) : '', blocComplet: blocDu(ctx),
    }
  }
  const index = Math.min(i, Math.max(0, partent.length - 1))
  const courant = partent.length ? pour(partent[index]) : null
  const aCompleter = [...new Set(partent.flatMap((c) => { const p = pour(c); return [...trous(p.objet), ...trous(p.corps)] }))]
  const reglagesManquants = partent.some((c) => trous(pour(c).bloc).length > 0)
  const envoiApp = reglages?.envoi === true
  const pret = phase === 'ecrire' && Boolean(de && reglages) && envoiApp && dejaAujourdhui != null && partent.length > 0
    && !aCompleter.length && !reglagesManquants && Boolean(objet.trim())
  const apercu = useMemo(() => (courant ? htmlEmail(courant.corps, courant.bloc || ' ') : ''), [courant?.corps, courant?.bloc])

  const message = !reglages || dejaAujourdhui === undefined ? 'Lecture de votre boîte et du compte du jour…'
    : !envoiApp ? 'L’envoi à plusieurs part de votre boîte Gmail, depuis l’app : l’envoi direct n’est pas encore allumé.'
      : dejaAujourdhui === null ? 'Le compte des e-mails du jour n’est pas lisible (le patch de l’envoi groupé n’est pas posé) : envoi bloqué.'
        : restant === 0 ? `Plafond du jour atteint (${PLAFOND_JOUR} e-mails) : reprenez demain.`
          : aCompleter.length ? `À compléter avant d’envoyer : ${aCompleter.join(', ')}.`
            : reglagesManquants ? 'Le bloc d’information attend l’adresse postale et l’adresse de contact pour les données.'
              : demain > 0 ? `${partent.length} partiront aujourd’hui ; ${demain} au-delà du plafond de ${PLAFOND_JOUR} : à refaire demain.` : ''

  const envoyerTout = async () => {
    if (!pret || !de) return
    arret.current = false
    const liste = partent.map(pour) // figé au clic : une retouche pendant l'envoi ne change rien
    setOrdre(liste.map((p) => ({ k: p.k, nom: nomComplet(p.c), detail: `${nomReseau(p.c.reseau)} · ${p.c.commune ?? ''}` })))
    setEtats(Object.fromEntries(liste.map((p) => [p.k, { etat: 'attente' } as EtatEnvoi])))
    setPhase('envoi')
    for (let n = 0; n < liste.length; n += 1) {
      if (arret.current) break
      const p = liste[n]
      setEtats((e) => ({ ...e, [p.k]: { etat: 'encours' } }))
      let parti = false
      try {
        await envoyerEmail({ de, a: p.c.email!, objet: p.objet, corps: p.corps, bloc: p.bloc, pieces: [], reseau: p.c.reseau, identifiant: p.c.identifiant })
        parti = true
      } catch (err) {
        setEtats((e) => ({ ...e, [p.k]: { etat: 'refuse', erreur: err instanceof Error ? err.message : String(err) } }))
      }
      if (parti) {
        const heure = new Date().toLocaleTimeString('fr-FR')
        setEtats((e) => ({ ...e, [p.k]: { etat: 'envoye', heure } }))
        try {
          await noter(p.c.reseau, p.c.identifiant, 'email', `Objet : ${p.objet.trim()}\n\n${texteComplet(p.corps, p.bloc)}`)
          const patch: Partial<Candidat> = { dernier_email: new Date().toISOString() }
          if (p.c.etape < 2) { await marquerEtape(p.c.reseau, p.c.identifiant, 2); patch.etape = 2 }
          if (p.blocComplet) { await majSuivi(p.c.reseau, p.c.identifiant, { info_donnee: true }); patch.info_donnee_le = new Date().toISOString() }
          onPatch(p.k, patch)
        } catch {
          setEtats((e) => ({ ...e, [p.k]: { etat: 'envoye', heure, erreur: 'parti, mais le fil n’a pas pu être mis à jour' } }))
        }
      }
      if (n < liste.length - 1 && !arret.current) await new Promise((r) => window.setTimeout(r, DELAI_ENVOI_MS))
    }
    setPhase('fini')
  }

  if (phase !== 'ecrire') {
    const valeurs = Object.values(etats)
    const envoyes = valeurs.filter((x) => x.etat === 'envoye').length
    const refuses = valeurs.filter((x) => x.etat === 'refuse').length
    const faits = envoyes + refuses
    return (
      <Fenetre largeur={760}
        titre={phase === 'envoi' ? `Envoi en cours : ${faits} sur ${ordre.length}` : `Envoi terminé : ${envoyes} envoyé${envoyes > 1 ? 's' : ''}${refuses ? `, ${refuses} refusé${refuses > 1 ? 's' : ''}` : ''}`}
        sousTitre={phase === 'envoi' ? `Un e-mail toutes les ${DELAI_ENVOI_MS / 1000} secondes. Gardez cette fenêtre ouverte pendant l’envoi.` : 'Chaque envoi est noté dans le fil de la personne.'}
        onFermer={phase === 'envoi' ? () => { arret.current = true } : onFini}
        pied={phase === 'envoi'
          ? <button className="rc-btn rc-btn-quiet" type="button" onClick={() => { arret.current = true }}>Arrêter l’envoi</button>
          : <button className="rc-btn rc-btn-main" type="button" onClick={onFini}>Fermer</button>}>
        <div style={{ padding: '16px 0', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="rc-progres" role="progressbar" aria-valuemin={0} aria-valuemax={ordre.length} aria-valuenow={faits} aria-label="Avancement de l’envoi">
            <span style={{ width: `${ordre.length ? (faits / ordre.length) * 100 : 0}%` }} />
          </div>
          {dejaAujourdhui != null ? <p className="rc-mute" style={{ margin: 0, fontSize: 12.5 }}>Aujourd’hui depuis votre boîte : {dejaAujourdhui + envoyes} sur {PLAFOND_JOUR}.</p> : null}
          <ul className="rc-liste-envoi">
            {ordre.map((o) => {
              const e = etats[o.k] ?? { etat: 'attente' }
              const style = e.etat === 'envoye' ? 'rc-p-club' : e.etat === 'refuse' ? 'rc-p-oppose' : e.etat === 'encours' ? 'rc-p-rdv' : 'rc-p-afaire'
              const libelle = e.etat === 'envoye' ? 'Envoyé' : e.etat === 'refuse' ? 'Refusé par Gmail' : e.etat === 'encours' ? 'En cours…' : 'En attente'
              return (
                <li key={o.k}>
                  <span><strong>{o.nom}</strong><span className="rc-sub" style={{ display: 'block' }}>{e.erreur ?? o.detail}</span></span>
                  <span className={`rc-pill ${style}`}>{libelle}</span>
                  <span className="rc-mute" style={{ fontSize: 12, textAlign: 'right' }}>{e.heure ?? ''}</span>
                </li>
              )
            })}
          </ul>
          <p className="rc-info">Un refus de Gmail (adresse qui n’existe plus) ne bloque pas les autres{phase === 'fini' && demain > 0 ? ` ; ${demain} personne${demain > 1 ? 's' : ''} au-delà du plafond, à reprendre demain` : ''}.</p>
        </div>
      </Fenetre>
    )
  }

  return (
    <Fenetre titre={`Écrire à ${candidats.length} candidat${candidats.length > 1 ? 's' : ''}`} largeur={1180} onFermer={onFermer}
      sousTitre="Un e-mail par personne, à son prénom, avec sa source et son lien de désinscription. Personne ne voit les autres."
      pied={<>
        <span className="rc-mute" style={{ marginRight: 'auto', fontSize: 13 }}>{message}</span>
        <button className="rc-btn rc-btn-quiet" type="button" onClick={onFermer}>Annuler</button>
        <button className="rc-btn rc-btn-main" type="button" disabled={!pret} onClick={() => void envoyerTout()}>Envoyer {partent.length} e-mail{partent.length > 1 ? 's' : ''}</button>
      </>}>
      <div className="rc-ecrire">
        <div className="rc-ecrire-saisie">
          <div className="rc-compteurs">
            <div className="is-vert"><strong>{recevront.length}</strong><span>recevront l’e-mail</span></div>
            <div className="is-ambre"><strong>{nbEcartes}</strong><span>{nbEcartes ? 'écartés, voici pourquoi' : 'écarté'}</span></div>
          </div>
          {ecartes.length || recents.length ? (
            <ul className="rc-ecartes">
              {ecartes.map(({ c, raison }) => <li key={cle(c)}><strong>{nomComplet(c)}</strong> — {raison}</li>)}
              {recents.map(({ c, raison }) => (
                <li key={cle(c)} className="is-recent"><strong>{nomComplet(c)}</strong> — {raison}
                  <label className="rc-case" style={{ marginTop: 6, fontSize: 12.5 }}>
                    <input type="checkbox" checked={inclure.has(cle(c))} onChange={(e) => { const n = new Set(inclure); if (e.target.checked) n.add(cle(c)); else n.delete(cle(c)); setInclure(n) }} />
                    Lui écrire quand même
                  </label>
                </li>
              ))}
            </ul>
          ) : null}
          <div className="rc-champ">Modèle
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {MODELES.map((m) => (
                <button key={m.cle} type="button" className={`rc-chip${modele === m.cle ? ' is-on' : ''}`} aria-pressed={modele === m.cle} onClick={() => setModele(m.cle)}>{m.nom}</button>
              ))}
            </div>
          </div>
          <label className="rc-champ">Objet (le même pour tous)<input type="text" value={objet} onChange={(e) => setObjet(e.target.value)} /></label>
          <label className="rc-champ">Message (commun){Object.keys(surcharges).length ? <span className="rc-opt">{Object.keys(surcharges).length} retouché(s) à part</span> : null}
            <textarea className="rc-ecrire-texte" value={corps} onChange={(e) => setCorps(e.target.value)} />
          </label>
          <p className="rc-mute" style={{ margin: 0, fontSize: 12.5 }}>{'{prenom}'}, {'{agence_proche}'} et {'{expediteur}'} se remplissent pour chacun.</p>
          {aCompleter.length ? <p className="rc-trous">À compléter : {aCompleter.join(', ')}.</p> : null}
          <div className="rc-info">
            <strong>Envoi doux</strong> : un e-mail toutes les {DELAI_ENVOI_MS / 1000} secondes, {PLAFOND_JOUR} au plus par jour et par expéditeur
            {dejaAujourdhui != null ? ` (aujourd’hui : ${dejaAujourdhui} envoyés)` : ''}.
          </div>
        </div>
        <div className="rc-ecrire-apercu">
          {courant ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button className="rc-nav" type="button" aria-label="Destinataire précédent" onClick={() => { setRetouche(false); setI((index + partent.length - 1) % partent.length) }}>{Ico.retour}</button>
                  <p style={{ margin: 0, fontSize: 14, fontWeight: 700 }} aria-live="polite">{index + 1} / {partent.length} — {nomComplet(courant.c)}</p>
                  <button className="rc-nav" type="button" aria-label="Destinataire suivant" onClick={() => { setRetouche(false); setI((index + 1) % partent.length) }} style={{ transform: 'scaleX(-1)' }}>{Ico.retour}</button>
                </div>
                <button className="rc-btn rc-btn-quiet rc-btn-petit" type="button" onClick={() => {
                  if (!retouche && surcharges[courant.k] == null) setSurcharges({ ...surcharges, [courant.k]: courant.corps })
                  setRetouche(!retouche)
                }}>{retouche ? 'Fermer la retouche' : 'Retoucher ce message seulement'}</button>
              </div>
              {retouche ? (
                <label className="rc-champ">Le message pour {nomComplet(courant.c)} seulement
                  <textarea className="rc-ecrire-texte" value={surcharges[courant.k] ?? courant.corps} onChange={(e) => setSurcharges({ ...surcharges, [courant.k]: e.target.value })} />
                  <button className="rc-lien" type="button" onClick={() => { const n = { ...surcharges }; delete n[courant.k]; setSurcharges(n); setRetouche(false) }}>Revenir au message commun</button>
                </label>
              ) : null}
              <div className="rc-ecrire-cadre">
                <div className="rc-ecrire-tetes">
                  <div><strong>À :</strong> {courant.c.email}</div>
                  <div><strong>Objet :</strong> {courant.objet || '—'}</div>
                </div>
                <iframe title={`Aperçu de l’e-mail à ${nomComplet(courant.c)}`} sandbox="allow-same-origin" srcDoc={apercu} />
              </div>
            </>
          ) : <p className="rc-vide">Personne ne recevra d’e-mail avec ces choix.</p>}
        </div>
      </div>
    </Fenetre>
  )
}
