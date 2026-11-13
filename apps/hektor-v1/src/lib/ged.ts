// GED (12/11/2026, morceau 2) : ce que la fenêtre de dépôt lit et écrit en base.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.7. Tables : supabase/patch_ged_m1_base_2026-11-12.sql ;
// fonction : supabase/patch_ged_m2_classer_2026-11-12.sql. Rien ici n'écrit dans app_console_document ni chez Hektor.
import { useEffect, useState } from 'react'
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
