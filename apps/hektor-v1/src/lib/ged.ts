// GED (12/11/2026, morceau 2) : ce que la fenêtre de dépôt lit et écrit en base.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.7. Tables : supabase/patch_ged_m1_base_2026-11-12.sql ;
// fonction : supabase/patch_ged_m2_classer_2026-11-12.sql. Rien ici n'écrit dans app_console_document ni chez Hektor.
import { useEffect, useState } from 'react'
import type { VerdictGed } from './gedMesure'
import { hasSupabaseEnv, supabase } from './supabase'

export type GedType = {
  code: string
  famille: string
  libelle: string
  lecture: 'lue' | 'classer' | 'jamais_envoye'
  sensible: boolean
  ordre: number
}

// Les familles dans l'ordre de la nomenclature (§6.4), avec leur nom à l'écran.
export const GED_FAMILLES: Record<string, string> = {
  mandat: 'Mandat',
  justificatifs: 'Justificatifs du mandat',
  transaction: 'Transaction',
  visite: 'Visite',
  estimation: 'Estimation',
  diagnostics: 'Diagnostics',
  copropriete: 'Copropriété',
  urbanisme: 'Urbanisme et terrain',
  bien: 'Bien',
  facturation: 'Facturation',
  location: 'Location',
  entreprise: 'Entreprise',
  courrier: 'Courrier',
  interne: 'Interne',
  partenaires: 'Partenaires',
}

export async function loadGedTypes(): Promise<GedType[]> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Base non configurée')
  const { data, error } = await supabase
    .from('app_ged_type')
    .select('code,famille,libelle,lecture,sensible,ordre')
    .eq('actif', true)
    .order('ordre', { ascending: true })
  if (error) throw new Error(error.message)
  return (data ?? []) as GedType[]
}

// Enregistre le type d'un document déposé (le sien seulement : la fonction relit le travail d'envoi).
export async function gedClasser(input: {
  jobId: string
  typeCode: string
  typePropose: string | null
  typeProposePar: 'nom' | 'ia' | null
  sha256: string | null
}): Promise<{ ok: boolean; classement_id: string; deja: boolean }> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Base non configurée')
  const { data, error } = await supabase.rpc('app_ged_classer', {
    p_job_id: input.jobId,
    p_type_code: input.typeCode,
    p_origine: 'humain',
    p_type_propose: input.typePropose,
    p_type_propose_par: input.typeProposePar,
    p_sha256: input.sha256,
  })
  if (error) throw new Error(error.message)
  return data as { ok: boolean; classement_id: string; deja: boolean }
}

// Un interrupteur à TROIS crans (patron de loadSignatureYoutrustActive, api.ts) : 'on' = tout le monde ;
// 'admin' = les admins ACTIFS seuls ; le reste, absent ou illisible = éteint.
export async function loadInterrupteurTroisCrans(key: string): Promise<boolean> {
  if (!hasSupabaseEnv || !supabase) return false
  try {
    const { data, error } = await supabase.from('app_setting').select('value').eq('key', key).maybeSingle()
    if (error || !data) return false
    const valeur = String((data as { value?: unknown }).value ?? '').trim().toLowerCase()
    if (['on', 'true', '1', 'yes'].includes(valeur)) return true
    if (valeur !== 'admin') return false
    const { data: session } = await supabase.auth.getUser()
    const id = session?.user?.id
    if (!id) return false
    const { data: profil, error: erreurProfil } = await supabase.from('app_user_profile').select('role,is_active').eq('id', id).maybeSingle()
    if (erreurProfil || !profil) return false
    const p = profil as { role?: string | null; is_active?: boolean | null }
    return p.is_active === true && p.role === 'admin'
  } catch {
    return false
  }
}

export function useGedDepotMultiple(): boolean {
  const [actif, setActif] = useState(false)
  useEffect(() => {
    let annule = false
    void loadInterrupteurTroisCrans('ged_depot_multiple').then((v) => { if (!annule) setActif(v) })
    return () => { annule = true }
  }, [])
  return actif
}

// GED morceau 3 : le bloc « Reçu / Manque » a son propre interrupteur (même règle à trois crans).
export function useGedRecuManque(): boolean {
  const [actif, setActif] = useState(false)
  useEffect(() => {
    let annule = false
    void loadInterrupteurTroisCrans('ged_recu_manque').then((v) => { if (!annule) setActif(v) })
    return () => { annule = true }
  }, [])
  return actif
}

// GED morceau 5 : les règles sans IA (« À regarder » dans « Reçu / Manque ») ont leur interrupteur, déjà posé au morceau 1.
export function useGedPropositions(): boolean {
  const [actif, setActif] = useState(false)
  useEffect(() => {
    let annule = false
    void loadInterrupteurTroisCrans('ged_propositions').then((v) => { if (!annule) setActif(v) })
    return () => { annule = true }
  }, [])
  return actif
}

// GED morceau 8 : proposer de REMPLIR la fiche depuis un document lu -- son propre interrupteur (il écrit).
export function useGedRemplir(): boolean {
  const [actif, setActif] = useState(false)
  useEffect(() => {
    let annule = false
    void loadInterrupteurTroisCrans('ged_remplir').then((v) => { if (!annule) setActif(v) })
    return () => { annule = true }
  }, [])
  return actif
}

// GED morceau 9 (lot 9a) : LIRE les pièces des personnes (identité, fiche de renseignements) -- son propre interrupteur.
export function useGedLecturePersonnes(): boolean {
  const [actif, setActif] = useState(false)
  useEffect(() => {
    let annule = false
    void loadInterrupteurTroisCrans('ged_lecture_personnes').then((v) => { if (!annule) setActif(v) })
    return () => { annule = true }
  }, [])
  return actif
}

// Les décisions déjà prises sur ce bien (« remplie », « ignoree »), en clés « cle|valeur » : elles ne reviennent pas.
// ⚠ Lecture ratée -> null (pas un ensemble vide) : l'écran ne propose alors RIEN, plutôt que de reproposer.
export async function loadGedDecisions(hektorAnnonceId: string | number): Promise<Set<string> | null> {
  if (!hasSupabaseEnv || !supabase) return null
  try {
    const { data, error } = await supabase
      .from('app_ged_decision')
      .select('cle,valeur,decision')
      .eq('hektor_annonce_id', String(hektorAnnonceId))
    if (error) return null
    return new Set(((data ?? []) as Array<{ cle: string; valeur: string; decision: string }>)
      .filter((d) => d.decision === 'remplie' || d.decision === 'ignoree')
      .map((d) => `${d.cle}|${d.valeur}`))
  } catch {
    return null
  }
}

// GED lot 9c (14/11) : l'état civil des contacts du bien, RELU dans la vue des contacts (même périmètre que l'annuaire).
// ⚠ Lecture ratée -> null : l'écran ne propose alors RIEN (jamais croire une case vide qu'on n'a pas lue). Un numéro
//   absent de la réponse = contact inconnu chez nous : il n'est pas dans la carte, donc rien ne se propose pour lui.
// ⛔ DEUX NUMÉROS (16/11, trouvé par l'épreuve réelle : 0 égaux sur 94 956) : les contacts d'un bien à l'écran portent
//   le numéro HEKTOR (`DetailContact.sourceId`) ; chez nous la clé est NOTRE numéro (`hektor_contact_id`, malgré son
//   nom), et le numéro Hektor est dans `hektor_target_id`. Règle de Frédéric : le numéro Hektor pour parler à Hektor,
//   le nôtre pour l'app. `par: 'hektor'` ne sert que de PONT (écran -> notre fiche) ; tout le reste se fait par 'app'.
//   Un numéro Hektor porté par deux fiches (aucune au 16/11) est ambigu : il n'est pas dans la carte.
export type EtatCivilLu = {
  hektor_contact_id: string; hektor_target_id: string | null; nom: string | null; prenom: string | null; birth_date: string | null
  birth_place: string | null; marital_status: string | null; nature_fiche: string | null; couple_role: string | null; archive: boolean | null
}
export async function loadContactsEtatCivil(ids: string[], par: 'hektor' | 'app'): Promise<Map<string, EtatCivilLu> | null> {
  if (!hasSupabaseEnv || !supabase) return null
  const numeros = [...new Set(ids.map((x) => String(x ?? '').trim()).filter((x) => /^\d+$/.test(x)))]
  if (!numeros.length) return new Map()
  const colonne = par === 'hektor' ? 'hektor_target_id' : 'hektor_contact_id'
  try {
    const { data, error } = await supabase
      .from('app_contacts_current')
      .select('hektor_contact_id,hektor_target_id,nom,prenom,birth_date,birth_place,marital_status,nature_fiche,couple_role,archive')
      .in(colonne, numeros)
    if (error) return null
    const carte = new Map<string, EtatCivilLu>()
    const ambigus = new Set<string>()
    for (const r of (data ?? []) as EtatCivilLu[]) {
      const cle = String(r[colonne] ?? '').trim()
      if (!cle) continue
      if (carte.has(cle)) ambigus.add(cle)
      carte.set(cle, r)
    }
    for (const cle of ambigus) carte.delete(cle)
    return carte
  } catch {
    return null
  }
}

// Garder une décision (app_ged_decider : compte actif, interrupteur, périmètre ; l'auteur est l'appelant).
export async function gedDecider(input: {
  hektorAnnonceId: string | number
  lectureId: string | null
  cle: string
  champ: string
  valeur: string
  decision: 'remplie' | 'ignoree' | 'echec'
  detail?: Record<string, unknown> | null
}): Promise<void> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Base non configurée')
  const { error } = await supabase.rpc('app_ged_decider', {
    p_hektor_annonce_id: String(input.hektorAnnonceId),
    p_lecture_id: input.lectureId,
    p_cle: input.cle,
    p_champ: input.champ,
    p_valeur: input.valeur,
    p_decision: input.decision,
    p_detail: input.detail ?? null,
  })
  if (error) throw new Error(error.message)
}

// GED morceau 10 (16/11) : les jugements des lignes « À regarder » d'un bien, le PLUS RÉCENT par ligne (journal).
// Lecture ratée -- ou table pas encore posée -> null : l'écran ne montre alors PAS les boutons (rien ne se perd).
export type JugementGed = { verdict: VerdictGed; jugeLe: string }
export async function loadGedJugements(hektorAnnonceId: string | number): Promise<Map<string, JugementGed> | null> {
  if (!hasSupabaseEnv || !supabase) return null
  try {
    const { data, error } = await supabase
      .from('app_ged_jugement')
      .select('cle,verdict,juge_le')
      .eq('hektor_annonce_id', String(hektorAnnonceId))
      .order('juge_le', { ascending: false })
    if (error) return null
    const carte = new Map<string, JugementGed>()
    for (const j of (data ?? []) as Array<{ cle: string; verdict: VerdictGed; juge_le: string }>) {
      if (!carte.has(j.cle)) carte.set(j.cle, { verdict: j.verdict, jugeLe: j.juge_le })
    }
    return carte
  } catch {
    return null
  }
}

// Garder le jugement d'une ligne (app_ged_juger : compte actif, interrupteur ged_propositions, périmètre ; l'auteur est
// l'appelant). Le texte et le niveau sont gardés TELS QU'AFFICHÉS : c'est ce que l'écran a dit qui est jugé.
export async function gedJuger(input: {
  hektorAnnonceId: string | number
  regle: string
  cle: string
  texte: string
  niveau: 'alerte' | 'piece' | 'info'
  verdict: VerdictGed
  commentaire?: string | null
}): Promise<void> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Base non configurée')
  const { error } = await supabase.rpc('app_ged_juger', {
    p_hektor_annonce_id: String(input.hektorAnnonceId),
    p_regle: input.regle,
    p_cle: input.cle,
    p_texte: input.texte,
    p_niveau: input.niveau,
    p_verdict: input.verdict,
    p_commentaire: input.commentaire ?? null,
  })
  if (error) throw new Error(error.message)
}

// Le NOMBRE de conditions de chaque transaction, lu STRICTEMENT : une erreur LÈVE (jamais une carte vide).
// ⚠ C'est la garde de P4 : app_conditions_affaire_ecrire EFFACE puis repose la liste ; si une lecture ratée passait
//   pour « aucune condition », on effacerait celles qui existent. (loadAffairesConditions, api.ts, rend une carte vide
//   sur erreur : elle ne convient pas ici.)
export async function compterConditionsStrict(appAffaireIds: number[]): Promise<Map<number, number>> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Base non configurée')
  const ids = Array.from(new Set(appAffaireIds.filter((id) => Number.isFinite(id))))
  const compte = new Map<number, number>(ids.map((id) => [id, 0]))
  if (!ids.length) return compte
  const { data, error } = await supabase.from('app_affaire_condition').select('app_affaire_id').in('app_affaire_id', ids)
  if (error) throw new Error(error.message)
  for (const r of (data ?? []) as Array<{ app_affaire_id: number }>) compte.set(Number(r.app_affaire_id), (compte.get(Number(r.app_affaire_id)) ?? 0) + 1)
  return compte
}

// Lot 10a (17/11) : le CARNET de l'app des transactions (app_affaire_champ_app : les corrections faites chez nous), lu
// STRICTEMENT -- une erreur LÈVE. La lecture d'aujourd'hui (loadAffaireChampsApp) rend un carnet VIDE sur erreur : une
// case déjà remplie chez nous y paraîtrait vide, et on proposerait d'écrire par-dessus.
export async function lireCarnetAffairesStrict(appAffaireIds: number[]): Promise<Map<number, Record<string, string>>> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Base non configurée')
  const ids = Array.from(new Set(appAffaireIds.filter((id) => Number.isFinite(id))))
  const carnet = new Map<number, Record<string, string>>(ids.map((id) => [id, {}]))
  if (!ids.length) return carnet
  const { data, error } = await supabase.from('app_affaire_champ_app').select('app_affaire_id,champ,valeur_app').in('app_affaire_id', ids)
  if (error) throw new Error(error.message)
  for (const r of (data ?? []) as Array<{ app_affaire_id: number; champ: string; valeur_app: string | null }>) {
    const ligne = carnet.get(Number(r.app_affaire_id)) ?? {}
    ligne[String(r.champ)] = String(r.valeur_app ?? '')
    carnet.set(Number(r.app_affaire_id), ligne)
  }
  return carnet
}

// Lot 10b (17/11) : les conditions suspensives des transactions (libellé, date limite), lues STRICTEMENT -- la lecture
// d'aujourd'hui (loadAffairesConditions) rend une carte vide sur erreur : on dirait « condition non trouvée » à tort.
export async function lireConditionsAffairesStrict(appAffaireIds: number[]): Promise<Map<number, Array<{ libelle: string; date: string | null }>>> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Base non configurée')
  const ids = Array.from(new Set(appAffaireIds.filter((id) => Number.isFinite(id))))
  const sortie = new Map<number, Array<{ libelle: string; date: string | null }>>(ids.map((id) => [id, []]))
  if (!ids.length) return sortie
  const { data, error } = await supabase.from('app_affaire_condition').select('app_affaire_id,rang,libelle,date_echeance').in('app_affaire_id', ids).order('rang', { ascending: true })
  if (error) throw new Error(error.message)
  for (const r of (data ?? []) as Array<{ app_affaire_id: number; libelle: string | null; date_echeance: string | null }>) {
    sortie.get(Number(r.app_affaire_id))?.push({ libelle: String(r.libelle ?? ''), date: r.date_echeance ?? null })
  }
  return sortie
}

// Les types DÉCIDÉS des documents déposés avec l'outil, pour un bien (lecture : patch_ged_m3_recu_manque, même
// périmètre que les documents). Clé : la ligne du document chez nous. Une lecture ratée rend une liste vide :
// les documents retombent alors sur leur nom, rien ne casse.
export async function loadGedClassements(hektorAnnonceId: string | number): Promise<Map<string, string>> {
  const types = new Map<string, string>()
  if (!hasSupabaseEnv || !supabase) return types
  try {
    const { data, error } = await supabase
      .from('app_ged_classement')
      .select('app_console_document_id,type_code')
      .eq('hektor_annonce_id', String(hektorAnnonceId))
      .not('app_console_document_id', 'is', null)
    if (error) return types
    for (const r of (data ?? []) as Array<{ app_console_document_id: string; type_code: string }>) types.set(r.app_console_document_id, r.type_code)
  } catch {
    // lecture ratée : les noms suffisent
  }
  return types
}

// L'empreinte du fichier, la même que celle que le worker pose sur notre ligne (sha256 du contenu).
export async function empreinteFichier(file: Blob): Promise<string> {
  const tampon = await file.arrayBuffer()
  const hache = await crypto.subtle.digest('SHA-256', tampon)
  return Array.from(new Uint8Array(hache)).map((o) => o.toString(16).padStart(2, '0')).join('')
}

// Les types que le coffre accepte (storage.buckets, mesuré le 12/11) : tout autre type serait refusé
// définitivement (415), et un fichier de plus de 50 Mo aussi (413).
export const GED_TYPES_ACCEPTES = new Set([
  'application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/plain', 'application/zip',
])
export const GED_TAILLE_MAX = 50 * 1024 * 1024

// ⚠ LES NOMS (réponse de la session signature, 12/11) : au réessai d'un dépôt, le worker ADOPTE le document Hektor
// « du même nom » avec un rapprochement LARGE -- égal, ou l'un CONTIENT l'autre (documentNonReclame,
// Console/console_job_worker.js). On refuse donc un nom qui contient celui d'un autre document du bien, ou y est
// contenu, sans tenir compte des majuscules ni de l'extension (plus strict que le worker, jamais moins).
export function racineNom(nom: string): string {
  return nom.trim().replace(/\.[a-z0-9]{1,5}$/i, '').trim().toLowerCase()
}

export function nomEnConflit(nom: string, autres: string[]): string | null {
  const a = racineNom(nom)
  if (!a) return null
  for (const autre of autres) {
    const b = racineNom(autre)
    if (b && (a.includes(b) || b.includes(a))) return autre
  }
  return null
}
