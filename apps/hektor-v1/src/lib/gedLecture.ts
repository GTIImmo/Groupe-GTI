// GED (12/11/2026, morceau 6) -- CE QUE L'IA A LU dans un document déposé avec l'outil : les types qui ont une fiche de
// lecture, le résumé d'une lecture en une phrase, et la lecture des lectures d'un bien (tables app_ged_lecture /
// app_ged_valeur, écrites par le serveur seul ; patch_ged_m6_lecture_2026-11-12.sql). L'écran LIT, il n'écrit rien ici.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.11.
import { hasSupabaseEnv, supabase } from './supabase'

// Lot 1 : les fiches 1 à 3 de l'étude. Les autres types attendent leur lot.
export const FICHES_LUES = new Set(['diag.erp', 'diag.dpe', 'diag.dossier'])

export type ValeurLue = {
  cle: string
  rang: number
  valeur: string | null
  valeur_num: number | null
  valeur_date: string | null
  page: number | null
  etat: 'lu' | 'incertain' | 'non_vu'
}
export type LectureDocument = { typeCode: string; etat: 'lu' | 'incomplet' | 'pas_ce_type'; luLe: string | null; valeurs: ValeurLue[] }

const jjmmaaaa = (iso: string) => { const [a, m, j] = iso.slice(0, 10).split('-'); return `${j}/${m}/${a}` }

// La valeur d'une clé (rang 0), si elle a été vue ; « incertain » est suivi d'un point d'interrogation.
export function valeurLue(valeurs: ValeurLue[], cle: string): string | null {
  const v = valeurs.find((x) => x.cle === cle && x.rang === 0)
  if (!v || v.etat === 'non_vu') return null
  const brut = v.valeur_date ? jjmmaaaa(v.valeur_date) : v.valeur_num != null ? String(v.valeur_num).replace('.', ',') : v.valeur
  return brut == null ? null : `${brut}${v.etat === 'incertain' ? ' (?)' : ''}`
}

// Le résumé en une phrase, pour la ligne du dépôt et la pièce reçue.
export function resumeLecture(l: Pick<LectureDocument, 'typeCode' | 'etat' | 'valeurs'>): string {
  if (l.etat === 'pas_ce_type') return "L'IA dit que ce n'est pas ce type de document : vérifie le type."
  const v = (cle: string) => valeurLue(l.valeurs, cle)
  const morceaux: string[] = []
  if (l.typeCode === 'diag.erp') {
    if (v('date_etablissement')) morceaux.push(`établi le ${v('date_etablissement')}`)
    if (v('commune')) morceaux.push(v('commune') as string)
  } else if (l.typeCode === 'diag.dpe') {
    const classes = [v('classe_energie') && `énergie ${v('classe_energie')}`, v('classe_ges') && `climat ${v('classe_ges')}`].filter(Boolean).join(', ')
    if (classes) morceaux.push(classes)
    if (v('conso_ep')) morceaux.push(`${v('conso_ep')} kWh/m²/an`)
    if (v('date_etablissement')) morceaux.push(`établi le ${v('date_etablissement')}`)
    if (v('date_validite')) morceaux.push(`valable jusqu'au ${v('date_validite')}`)
  } else if (l.typeCode === 'diag.dossier') {
    const noms = l.valeurs.filter((x) => x.cle === 'diagnostics.diagnostic' && x.etat !== 'non_vu' && x.valeur).map((x) => x.valeur as string)
    if (noms.length) morceaux.push(`${noms.length} diagnostic${noms.length > 1 ? 's' : ''} (${noms.join(', ')})`)
    if (v('dpe_classe_energie')) morceaux.push(`DPE ${v('dpe_classe_energie')}`)
  }
  if (!morceaux.length) return "L'IA n'a rien pu relever : la lecture est incomplète."
  return `Lu : ${morceaux.join(' · ')}.`
}

// La date de l'état lue (« établie le ») d'un document, en AAAA-MM-JJ, si elle a été vue (lu ou incertain).
export function dateEtatLue(l: LectureDocument | undefined): string | null {
  if (!l || l.etat === 'pas_ce_type') return null
  const cle = l.typeCode === 'diag.dossier' ? null : 'date_etablissement'
  const v = cle ? l.valeurs.find((x) => x.cle === cle && x.rang === 0 && x.etat !== 'non_vu') : null
  return v?.valeur_date ?? null
}

// Les lectures des documents d'un bien, la plus récente par document. Clé : la ligne du document chez nous. Une lecture
// ratée rend une carte vide : rien ne casse, les règles retombent sur la date de dépôt.
export async function loadGedLectures(hektorAnnonceId: string | number): Promise<Map<string, LectureDocument>> {
  const parDocument = new Map<string, LectureDocument>()
  if (!hasSupabaseEnv || !supabase) return parDocument
  try {
    const { data, error } = await supabase
      .from('app_ged_classement')
      .select('app_console_document_id, app_ged_lecture(type_code, etat, lu_le, app_ged_valeur(cle, rang, valeur, valeur_num, valeur_date, page, etat))')
      .eq('hektor_annonce_id', String(hektorAnnonceId))
      .not('app_console_document_id', 'is', null)
    if (error) return parDocument
    type Ligne = { app_console_document_id: string; app_ged_lecture: Array<{ type_code: string; etat: LectureDocument['etat']; lu_le: string | null; app_ged_valeur: ValeurLue[] }> | null }
    for (const r of (data ?? []) as unknown as Ligne[]) {
      const lectures = [...(r.app_ged_lecture ?? [])].sort((a, b) => String(b.lu_le).localeCompare(String(a.lu_le)))
      const l = lectures[0]
      if (l) parDocument.set(r.app_console_document_id, { typeCode: l.type_code, etat: l.etat, luLe: l.lu_le, valeurs: l.app_ged_valeur ?? [] })
    }
  } catch {
    // lecture ratée : rien ne casse
  }
  return parDocument
}
