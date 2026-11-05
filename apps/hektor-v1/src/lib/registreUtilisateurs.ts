// REGISTRE DES UTILISATEURS ET DES AGENCES -- étape 3, lot A : LES LECTURES (05/11/2026).
// Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §35-§42 ; maquette validée (§38) :
// https://claude.ai/artifact/XMLpyh5kDkfpXPwGTB5738. Décision de Frédéric (05/11) : le bouton « Utilisateurs » existant
// ouvre CETTE maquette, réservée aux administrateurs ; les gestes (créer, modifier un accès, lien de mot de passe) restent
// ceux qui marchaient déjà.
// ⛔ LECTURE SEULE : rien ici n'écrit, rien ne part chez Hektor.
// Une source qui ne se lit pas n'éteint que SON bloc (« n'a pas pu être lu ») ; le détail part en console.
import { supabase, hasSupabaseEnv } from './supabase'

export type RuFiche = {
  sorte: 'fiche_negociateur' | 'compte_utilisateur' | string
  negoId: string | null
  userId: string | null
  agence: string | null
  email: string | null
  portable: string | null
  telephone: string | null
  typeCompte: string | null
  actif: boolean
  present: boolean
  rattachePar: string | null
  derniereVue: string | null
  absentDepuis: string | null
}

export type RuPersonne = {
  id: number
  nom: string
  civilite: string | null
  prenom: string | null
  nomFamille: string | null
  email: string | null
  emailPro: string | null
  telephone: string | null
  portable: string | null
  photo: string | null
  fonction: string | null
  type: string
  actif: boolean
  origine: string | null
  appUserId: string | null
  aValider: string | null
  appAgenceId: number | null
  creeLe: string | null
  fiches: RuFiche[]
}

export type RuIdentite = {
  appUserId: string
  googleEmail: string | null
  hektorUserId: string | null
  hektorNegociateurId: string | null
  negociateurEmail: string | null
  derniereConnexion: string | null
  source: string | null
}

export type RuAgence = {
  id: number
  nom: string
  statut: string | null
  email: string | null
  telephone: string | null
  fax: string | null
  site: string | null
  responsable: string | null
  adresse: string | null
  codePostal: string | null
  ville: string | null
  siret: string | null
  logoUrl: string | null
  baremeUrl: string | null
  hektorAgenceId: string | null
  hektorCompteId: string | null
  present: boolean
  derniereVue: string | null
  absentDepuis: string | null
  ecritures: string[]
}

export type RuSociete = Record<string, string | null>

export type RuEvenement = { quand: string; texte: string; aSignaler: boolean }

export type RuDonnees = {
  personnes: RuPersonne[] | null
  identites: Map<string, RuIdentite>
  agences: RuAgence[] | null
  societe: RuSociete | null
  /** `objet:id:champ` des champs saisis au carnet (la nuit ne les écrit plus) */
  carnet: Set<string>
  /** écarts signalés et pas encore traités, par personne */
  ecartsParPersonne: Map<number, number>
  derniereNuit: string | null
  erreurs: string[]
}

const txt = (v: unknown) => (v == null || String(v).trim() === '' ? null : String(v))

async function lire<T>(nom: string, erreurs: string[], promesse: PromiseLike<{ data: unknown; error: { message: string } | null }>): Promise<T[] | null> {
  try {
    const { data, error } = await promesse
    if (error) throw new Error(error.message)
    return (data ?? []) as T[]
  } catch (e) {
    console.error(`[registre] ${nom} illisible`, e)
    erreurs.push(nom)
    return null
  }
}

export async function loadRegistreUtilisateurs(): Promise<RuDonnees> {
  const vide: RuDonnees = { personnes: [], identites: new Map(), agences: [], societe: null, carnet: new Set(), ecartsParPersonne: new Map(), derniereNuit: null, erreurs: [] }
  if (!hasSupabaseEnv || !supabase) return vide
  const erreurs: string[] = []
  type Ligne = Record<string, unknown>
  const [personnes, fiches, identites, agences, alias, societe, carnet, journalNego, journalRegistre] = await Promise.all([
    lire<Ligne>('les personnes', erreurs, supabase.from('app_negociateur_personne')
      .select('app_personne_id,nom,email,type_personne,actif,origine,app_user_id,a_valider,created_at,civilite,prenom,nom_famille,fonction,app_agence_id,email_pro,telephone,portable,photo_url')
      .order('nom', { ascending: true }).limit(2000)),
    lire<Ligne>('les fiches Hektor', erreurs, supabase.from('app_negociateur_fiche')
      .select('app_personne_id,sorte,hektor_negociateur_id,hektor_user_id,agence_nom,email_vu,portable,telephone,user_type,actif_chez_hektor,present_chez_hektor,rattache_par,derniere_vue,absent_depuis')
      .limit(2000)),
    lire<Ligne>('les accès à l\'app', erreurs, supabase.from('app_google_workspace_identity')
      .select('app_user_id,google_email,hektor_user_id,hektor_negociateur_id,negociateur_email,last_login_at,metadata_json').limit(500)),
    lire<Ligne>('les agences', erreurs, supabase.from('app_registre_agence').select('*').order('app_agence_id', { ascending: true }).limit(200)),
    lire<Ligne>('les écritures d\'agence', erreurs, supabase.from('app_registre_agence_alias').select('app_agence_id,ecriture').limit(2000)),
    lire<Ligne>('la société', erreurs, supabase.from('app_registre_societe').select('*').limit(1)),
    lire<Ligne>('le carnet', erreurs, supabase.from('app_registre_champ_app').select('objet,objet_id,champ').limit(5000)),
    lire<Ligne>('le journal des négociateurs', erreurs, supabase.from('app_negociateur_journal')
      .select('app_personne_id,a_signaler,traite_le,nuit').order('nuit', { ascending: false }).limit(5000)),
    lire<Ligne>('le journal du registre', erreurs, supabase.from('app_registre_journal')
      .select('objet,objet_id,a_signaler,traite_le,nuit').eq('a_signaler', true).is('traite_le', null).limit(5000)),
  ])

  const fichesParPersonne = new Map<number, RuFiche[]>()
  for (const f of fiches ?? []) {
    const id = Number(f.app_personne_id)
    if (!Number.isFinite(id)) continue
    const liste = fichesParPersonne.get(id) ?? []
    liste.push({
      sorte: String(f.sorte ?? ''), negoId: txt(f.hektor_negociateur_id), userId: txt(f.hektor_user_id), agence: txt(f.agence_nom),
      email: txt(f.email_vu), portable: txt(f.portable), telephone: txt(f.telephone), typeCompte: txt(f.user_type),
      actif: f.actif_chez_hektor === true, present: f.present_chez_hektor === true, rattachePar: txt(f.rattache_par),
      derniereVue: txt(f.derniere_vue), absentDepuis: txt(f.absent_depuis),
    })
    fichesParPersonne.set(id, liste)
  }
  for (const liste of fichesParPersonne.values()) {
    // actives d'abord, puis les plus récemment vues
    liste.sort((a, b) => Number(b.actif) - Number(a.actif) || String(b.derniereVue ?? '').localeCompare(String(a.derniereVue ?? '')))
  }

  const ecritures = new Map<number, string[]>()
  for (const a of alias ?? []) {
    const id = Number(a.app_agence_id)
    const e = txt(a.ecriture)
    if (!e) continue
    ecritures.set(id, [...(ecritures.get(id) ?? []), e])
  }

  const ecartsParPersonne = new Map<number, number>()
  let derniereNuit: string | null = null
  for (const j of journalNego ?? []) {
    const nuit = txt(j.nuit)
    if (nuit && (!derniereNuit || nuit > derniereNuit)) derniereNuit = nuit
    if (j.a_signaler === true && j.traite_le == null && j.app_personne_id != null) {
      const id = Number(j.app_personne_id)
      ecartsParPersonne.set(id, (ecartsParPersonne.get(id) ?? 0) + 1)
    }
  }
  for (const j of journalRegistre ?? []) {
    const nuit = txt(j.nuit)
    if (nuit && (!derniereNuit || nuit > derniereNuit)) derniereNuit = nuit
    if (j.objet === 'personne' && j.objet_id != null) {
      const id = Number(j.objet_id)
      ecartsParPersonne.set(id, (ecartsParPersonne.get(id) ?? 0) + 1)
    }
  }

  const mapIdentites = new Map<string, RuIdentite>()
  for (const i of identites ?? []) {
    const id = txt(i.app_user_id)
    if (!id) continue
    const meta = (i.metadata_json ?? {}) as { match_source?: string }
    mapIdentites.set(id, {
      appUserId: id, googleEmail: txt(i.google_email), hektorUserId: txt(i.hektor_user_id), hektorNegociateurId: txt(i.hektor_negociateur_id),
      negociateurEmail: txt(i.negociateur_email), derniereConnexion: txt(i.last_login_at), source: txt(meta.match_source),
    })
  }

  return {
    personnes: personnes === null ? null : personnes.map((p) => ({
      id: Number(p.app_personne_id), nom: String(p.nom ?? ''), civilite: txt(p.civilite), prenom: txt(p.prenom), nomFamille: txt(p.nom_famille),
      email: txt(p.email), emailPro: txt(p.email_pro), telephone: txt(p.telephone), portable: txt(p.portable), photo: txt(p.photo_url),
      fonction: txt(p.fonction), type: String(p.type_personne ?? ''), actif: p.actif === true, origine: txt(p.origine),
      appUserId: txt(p.app_user_id), aValider: txt(p.a_valider), appAgenceId: p.app_agence_id == null ? null : Number(p.app_agence_id),
      creeLe: txt(p.created_at), fiches: fichesParPersonne.get(Number(p.app_personne_id)) ?? [],
    })),
    identites: mapIdentites,
    agences: agences === null ? null : agences.map((a) => ({
      id: Number(a.app_agence_id), nom: String(a.nom ?? ''), statut: txt(a.statut), email: txt(a.email), telephone: txt(a.telephone),
      fax: txt(a.fax), site: txt(a.site), responsable: txt(a.responsable), adresse: txt(a.adresse), codePostal: txt(a.code_postal),
      ville: txt(a.ville), siret: txt(a.siret_etablissement), logoUrl: txt(a.logo_url), baremeUrl: txt(a.bareme_url),
      hektorAgenceId: txt(a.hektor_agence_id), hektorCompteId: txt(a.hektor_compte_id), present: a.present_chez_hektor === true,
      derniereVue: txt(a.derniere_vue), absentDepuis: txt(a.absent_depuis), ecritures: ecritures.get(Number(a.app_agence_id)) ?? [],
    })),
    societe: societe === null ? null : (societe[0] ? Object.fromEntries(Object.entries(societe[0]).map(([k, v]) => [k, txt(v)])) : null),
    carnet: new Set((carnet ?? []).map((c) => `${c.objet}:${c.objet_id}:${c.champ}`)),
    ecartsParPersonne,
    derniereNuit,
    erreurs,
  }
}

/** L'historique d'une personne, lu à l'ouverture de sa fiche : le journal des négociateurs et celui du registre. */
export async function loadHistoriquePersonne(id: number): Promise<RuEvenement[] | null> {
  if (!hasSupabaseEnv || !supabase) return []
  const erreurs: string[] = []
  type Ligne = Record<string, unknown>
  const [nego, registre] = await Promise.all([
    lire<Ligne>('le journal des négociateurs', erreurs, supabase.from('app_negociateur_journal')
      .select('evenement,champ,avant,apres,a_signaler,vu_le').eq('app_personne_id', id).order('vu_le', { ascending: false }).limit(200)),
    lire<Ligne>('le journal du registre', erreurs, supabase.from('app_registre_journal')
      .select('evenement,champ,avant,apres,a_signaler,vu_le').eq('objet', 'personne').eq('objet_id', id).order('vu_le', { ascending: false }).limit(200)),
  ])
  if (nego === null && registre === null) return null
  return [...(nego ?? []), ...(registre ?? [])]
    .map((j) => ({ quand: String(j.vu_le ?? ''), texte: phraseJournal(j), aSignaler: j.a_signaler === true }))
    .sort((a, b) => b.quand.localeCompare(a.quand))
}

const CHAMPS: Record<string, string> = {
  app_user_id: 'Accès à l’app', email: 'E-mail', email_pro: 'E-mail professionnel', portable: 'Portable', telephone: 'Téléphone',
  nom: 'Nom', fonction: 'Fonction', app_agence_id: 'Agence', actif: 'Statut', civilite: 'Civilité', prenom: 'Prénom', nom_famille: 'Nom',
  photo_url: 'Photo', actif_chez_hektor: 'Fiche Hektor',
}

function phraseJournal(j: Record<string, unknown>): string {
  const champ = CHAMPS[String(j.champ ?? '')] ?? (txt(j.champ) ?? '')
  const avant = txt(j.avant)
  const apres = txt(j.apres)
  switch (String(j.evenement ?? '')) {
    case 'compte_app_relie': return `Accès à l’app : ${apres ?? 'relié'}${avant ? ` (avant : ${avant})` : ''}`
    case 'personne_nouvelle': return `Entrée au registre : ${apres ?? ''}`.trim()
    case 'adoptee': return `Une fiche Hektor lui est rattachée${apres ? ` : ${apres}` : ''}`
    case 'disparue': return `Une fiche Hektor a disparu de la liste de Hektor${avant ? ` (${avant})` : ''}`
    case 'reapparue': return `Une fiche Hektor est réapparue${apres ? ` (${apres})` : ''}`
    case 'actif': return `${champ || 'Statut'} : ${avant ?? '—'} → ${apres ?? '—'}`
    case 'ecart': return `Écart avec Hektor sur ${champ.toLowerCase() || 'un champ'} : chez nous ${avant ?? '—'}, chez Hektor ${apres ?? '—'}`
    case 'pose': return `${champ} posé : ${apres ?? '—'}`
    case 'changement': return `${champ || 'Changement'} : ${avant ?? '—'} → ${apres ?? '—'}`
    default: return `${String(j.evenement ?? 'Événement')}${champ ? ` · ${champ}` : ''}${apres ? ` : ${apres}` : ''}`
  }
}
