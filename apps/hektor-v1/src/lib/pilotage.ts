// Pilotage (écran admin), 02/11/2026 — notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md.
// LECTURE SEULE. Les lectures et TOUS les calculs des quatre onglets (vue d'ensemble, ventes, mandats,
// stock) vivent ici ; l'écran (PilotageScreen.tsx) ne fait qu'afficher.
// ⚠ Règles mesurées, à ne pas « simplifier » :
//   . honoraires d'une vente = entrée + sortie, TTC, en EUROS (registre des transactions) ;
//   . part d'une personne = honoraires TOTAUX × pourcentage / 100 (entrée et sortie confondues) ;
//   . « à date » = du 1er janvier au même jour et mois, pour l'année comparée ;
//   . HT = TTC / 1,2 ;
//   . le type de mandat « ACCORD » est le SEMI-EXCLUSIF (Frédéric, 02/11) ;
//   . les noms d'agence arrivent sous plusieurs formes (« Groupe GTI Ambert␣␣␣ », « Groupe Gti Le Puy en
//     Velay », « COURPIÈRE ») : on compare par une CLÉ (cleAgence), jamais par le texte brut.
import { hasSupabaseEnv, supabase } from './supabase'
import { loadRegistreDossiers, loadRepartitionsDesChaines, type RegistreDossierRow, type RepartitionLigne } from './api'

// ───────────────────────────── les ESSAIS, écartés partout ─────────────────────────────
// Décision de Frédéric (03/11) : les transactions d'essai qu'on ne supprime pas chez Hektor sont ÉCARTÉES du pilotage.
// Liste mesurée : notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md § 21. ⚠ Un bien d'essai se reconnaît à ses MANDANTS
// (« TEST GTI Delphine », « Test SELL AND SIGNE »…), jamais à un nom approchant : TESTUD est un vrai patronyme.
//   23287 (VA31732, mandant « test GERPHAGNON ») : compromis 19133 + vente 5537 du 25/11/2024 (300 000 €)
//   24933 (« Test SELL AND SIGNE ») · 61398 (« TEST GTI Delphine », mandat 18420) · 62774 (bac à sable, clos le 21/10)
//   62965 (« CLAUDE TESTCLAUDE »)
// ⛔ VA6482 / 24113 N'EST PAS un bien d'essai (vrais clients) : seules ses OFFRES d'essai sont écartées, une par une.
const ANNONCES_ESSAI = new Set([23287, 24933, 61398, 62774, 62965])
/** Offres d'essai posées sur de VRAIS biens (une offre ne se supprime pas) : VA6482 / 24113, et 41559 (acquéreur
 *  « Test vv GERPHAGNON »). Pour l'onglet Affaires. */
export const OFFRES_ESSAI = new Set(['32849', '33109', '33110', '33112', '33114', '33115', '33116', '20588'])
export const estAnnonceEssai = (annonce: number | string | null | undefined) => ANNONCES_ESSAI.has(Number(annonce))

// ───────────────────────────── les lignes lues ─────────────────────────────

// annonce / negoId (04/11) : le bien et le n° de NÉGOCIATEUR du mandat, pour le filtre par négociateur
export type PilotageMandat = { debut: string; type: string; agence: string | null; nego: string | null; montant: number | null; annonce: number | null; negoId: string | null }
export type PilotageStock = {
  app_dossier_id: number
  statut_annonce: string
  agence_nom: string | null
  commercial_nom: string | null
  commercial_id: string | null
  hektor_annonce_id: number | null
  prix: number | null
  mandat_type: string | null
  mandat_date_debut: string | null
  mandat_date_fin: string | null
  diffusable: string | null
  nb_portails_actifs: number | null
  price_change_last_old_value: number | null
  price_change_last_new_value: number | null
  honoraires: number | null
}
export type PilotageSignature = { statut: 'signed' | 'pending'; signeLe: string | null; annonce: number | null }
export type PilotagePortail = { dossier: number; portail: string; ok: boolean; erreur: boolean }

export type PilotageSources = {
  annee: number
  ventes: { n: RegistreDossierRow[]; p: RegistreDossierRow[]; repN: Map<string, RepartitionLigne[]>; repP: Map<string, RepartitionLigne[]> } | Error
  mandats: PilotageMandat[] | Error
  stock: PilotageStock[] | Error
  signatures: PilotageSignature[] | Error
  portails: PilotagePortail[] | Error
  // 03/11 : deux lectures réservées aux admins (supabase/patch_pilotage_acquereurs_affaires_2026-11-03.sql)
  acquereurs: PilotageAcquereurs | Error
  affairesPlus: PilotageAffairesPlus | Error
  // 04/11 : l'annuaire des négociateurs (les deux numéros de chaque fiche), pour le filtre par négociateur
  annuaire: PilotageNegociateur[] | Error
  // 04/11 : LE REGISTRE DES NÉGOCIATEURS (nos personnes et leurs fiches Hektor) ; l'annuaire ne sert plus que de repli
  registre: PilotageRegistre | Error
}

export type PilotageAcquereurs = {
  total: number; vivantes: number; crees: number; crees_prec: number; touchees90: number; sans_nego: number; sans_contact: number
  qualite: { tel: number; mail: number; recherche: number; type: number; budget: number; secteur: number; taille: number }
  vivier: [number, number, number, number, number]
  conversion: { fiches: number; avec_offre: number; acheteurs: number; delai_median: number | null; sous30: number }
  budgets: Array<{ tranche: number; n: number }>
  negos: Array<{ nom: string; crees: number; crees_prec: number; vivantes: number; avec_rech: number; completes: number; joignables: number; touchees90: number }>
}
export type PilotageAffairesPlus = {
  // nego / nego_nom (04/11) : le n° et le nom du négociateur du mandat (offres) ou du bien (actes, compromis)
  offres: Array<{ d: string; state: string | null; agence: string | null; nego?: string | null; nego_nom?: string | null; type: string | null; ratio: number | null; jours: number | null; premiere: boolean }>
  actes: Array<{ d: string; agence: string | null; nego?: string | null; nego_nom?: string | null; etude_id: string | null; etude: string | null; delai: number | null; retard: boolean | null }>
  // 03/11, 2e pose : les compromis en cours, notaire retrouvé par son numéro (même numéro que sur les ventes)
  compromis?: Array<{ app_chaine_id?: number; d: string; prevue: string | null; agence: string | null; nego?: string | null; nego_nom?: string | null; etude_id: string | null; etude: string | null }>
}

// L'agence (clé de cleAgence) filtre les fiches par l'agence de la fiche, celle du négociateur qui la suit.
// La personne (04/11) : TOUS ses n° de négociateur, et ses noms (clé cleNom) en repli pour une fiche sans numéro.
export async function lireAcquereurs(annee: number, agence: string | null = null, personne: { negos: string[]; noms: string[] } | null = null): Promise<PilotageAcquereurs> {
  if (!hasSupabaseEnv || !supabase) return mockAcquereurs()
  const { data, error } = await supabase.rpc('app_pilotage_acquereurs', {
    p_annee: annee, p_agence: agence, p_negos: personne ? personne.negos : null, p_noms: personne ? personne.noms : null,
  })
  if (error) throw new Error(error.message)
  if (!data) throw new Error('lecture réservée aux administrateurs')
  return data as PilotageAcquereurs
}

async function lireAffairesPlus(annee: number): Promise<PilotageAffairesPlus> {
  if (!hasSupabaseEnv || !supabase) return mockAffairesPlus(annee)
  const { data, error } = await supabase.rpc('app_pilotage_affaires_plus', { p_annee: annee })
  if (error) throw new Error(error.message)
  if (!data) throw new Error('lecture réservée aux administrateurs')
  return data as PilotageAffairesPlus
}

const PAQUET = 1000
async function toutLire<T>(lire: (de: number, a: number) => PromiseLike<{ data: unknown; error: { message: string } | null }>): Promise<T[]> {
  const lignes: T[] = []
  for (let page = 0; page < 50; page += 1) {
    const { data, error } = await lire(page * PAQUET, page * PAQUET + PAQUET - 1)
    if (error) throw new Error(error.message)
    const paquet = (data ?? []) as T[]
    lignes.push(...paquet)
    if (paquet.length < PAQUET) break
  }
  return lignes
}

const enErreur = (raison: unknown) => (raison instanceof Error ? raison : new Error(String(raison)))
const nombre = (valeur: unknown) => (valeur == null || valeur === '' ? null : Number.isFinite(Number(valeur)) ? Number(valeur) : null)

async function lireVentes(annee: number) {
  const [toutN, toutP] = await Promise.all([loadRegistreDossiers(annee), loadRegistreDossiers(annee - 1)])
  const n = toutN.filter((ligne) => !estAnnonceEssai(ligne.hektor_annonce_id))
  const p = toutP.filter((ligne) => !estAnnonceEssai(ligne.hektor_annonce_id))
  const chaines = (lignes: RegistreDossierRow[]) => lignes.filter((ligne) => ligne.etape === 'vendu').map((ligne) => ligne.app_chaine_id)
  const [repN, repP] = await Promise.all([lireRepartitions(chaines(n)), lireRepartitions(chaines(p))])
  return { n, p, repN, repP }
}

// La lecture de la répartition passe par l'adresse : on la découpe en paquets de 150 dossiers.
async function lireRepartitions(ids: number[]) {
  const sortie = new Map<string, RepartitionLigne[]>()
  for (let i = 0; i < ids.length; i += 150) {
    const lu = await loadRepartitionsDesChaines(ids.slice(i, i + 150))
    for (const [cle, lignes] of lu) sortie.set(cle, lignes)
  }
  return sortie
}

async function lireMandats(annee: number): Promise<PilotageMandat[]> {
  if (!hasSupabaseEnv || !supabase) return mockMandats(annee)
  const client = supabase
  const lignes = await toutLire<Record<string, unknown>>((de, a) => client
    .from('app_mandat_register_current')
    .select('hektor_annonce_id,mandat_date_debut,mandat_type,agence_nom,commercial_nom,commercial_id,mandat_montant,register_source_kind')
    .gte('mandat_date_debut', `${annee - 1}-01-01`)
    .lte('mandat_date_debut', `${annee}-12-31 23:59:59`)
    .order('register_row_id', { ascending: true })
    .range(de, a))
  return lignes
    .filter((ligne) => String(ligne.register_source_kind ?? '') !== 'recherche' && !estAnnonceEssai(ligne.hektor_annonce_id as number | null))
    .map((ligne) => ({
      debut: String(ligne.mandat_date_debut ?? '').slice(0, 10),
      type: String(ligne.mandat_type ?? '').trim().toUpperCase(),
      agence: (ligne.agence_nom as string | null) ?? null,
      nego: (ligne.commercial_nom as string | null) ?? null,
      montant: nombre(ligne.mandat_montant),
      annonce: nombre(ligne.hektor_annonce_id),
      negoId: String(ligne.commercial_id ?? '').trim() || null,
    }))
}

async function lireStock(): Promise<PilotageStock[]> {
  if (!hasSupabaseEnv || !supabase) return mockStock()
  const { data, error } = await supabase.rpc('app_pilotage_stock')
  if (error) throw new Error(error.message)
  return ((data ?? []) as Array<Record<string, unknown>>).filter((ligne) => !estAnnonceEssai(ligne.hektor_annonce_id as number | null)).map((ligne) => ({
    app_dossier_id: Number(ligne.app_dossier_id),
    statut_annonce: String(ligne.statut_annonce ?? ''),
    agence_nom: (ligne.agence_nom as string | null) ?? null,
    commercial_nom: (ligne.commercial_nom as string | null) ?? null,
    commercial_id: String(ligne.commercial_id ?? '').trim() || null,
    hektor_annonce_id: nombre(ligne.hektor_annonce_id),
    prix: nombre(ligne.prix),
    mandat_type: (ligne.mandat_type as string | null) ?? null,
    mandat_date_debut: (ligne.mandat_date_debut as string | null) ?? null,
    mandat_date_fin: (ligne.mandat_date_fin as string | null) ?? null,
    diffusable: ligne.diffusable == null ? null : String(ligne.diffusable),
    nb_portails_actifs: nombre(ligne.nb_portails_actifs),
    price_change_last_old_value: nombre(ligne.price_change_last_old_value),
    price_change_last_new_value: nombre(ligne.price_change_last_new_value),
    honoraires: nombre(ligne.honoraires),
  }))
}

// Signatures électroniques (ImmoSign) : l'état est rangé dans les métadonnées du document.
async function lireSignatures(): Promise<PilotageSignature[]> {
  if (!hasSupabaseEnv || !supabase) return mockSignatures()
  const client = supabase
  const lignes = await toutLire<{ hektor_annonce_id?: number | null; signature?: { status?: string; signed_at?: string } | null }>((de, a) => client
    .from('app_console_document')
    .select('id,hektor_annonce_id,signature:metadata_json->signature')
    .in('metadata_json->signature->>status', ['signed', 'pending'])
    .order('id', { ascending: true })
    .range(de, a))
  return lignes
    .filter((ligne) => !estAnnonceEssai(ligne.hektor_annonce_id))
    .map((ligne) => ({ statut: ligne.signature?.status === 'signed' ? 'signed' as const : 'pending' as const, signeLe: dateSignature(ligne.signature?.signed_at), annonce: nombre(ligne.hektor_annonce_id) }))
}

// « 12/03/2026 à 14:05 » -> « 2026-03-12 »
function dateSignature(texte: string | undefined) {
  const m = String(texte ?? '').match(/(\d{2})\/(\d{2})\/(\d{4})/)
  return m ? `${m[3]}-${m[2]}-${m[1]}` : null
}

async function lirePortails(): Promise<PilotagePortail[]> {
  if (!hasSupabaseEnv || !supabase) return mockPortails()
  const client = supabase
  const lignes = await toutLire<Record<string, unknown>>((de, a) => client
    .from('app_mandat_broadcast_current')
    .select('app_dossier_id,passerelle_key,is_success,is_error')
    .order('app_dossier_id', { ascending: true })
    .order('passerelle_key', { ascending: true })
    .range(de, a))
  return lignes.map((ligne) => ({ dossier: Number(ligne.app_dossier_id), portail: String(ligne.passerelle_key ?? ''), ok: ligne.is_success === true, erreur: ligne.is_error === true }))
}

// L'annuaire des négociateurs, reconstruit chaque nuit (push_hektor_directory_to_supabase.py) : 219 fiches, chacune
// avec son n° de NÉGOCIATEUR et son n° d'UTILISATEUR (Claire RIBBES : 15 et 39). Mesuré le 04/11 : 219 ↔ 219.
async function lireAnnuaire(): Promise<PilotageNegociateur[]> {
  if (!hasSupabaseEnv || !supabase) return mockAnnuaire()
  const client = supabase
  const lignes = await toutLire<Record<string, unknown>>((de, a) => client
    .from('app_hektor_negotiator_agency_directory')
    .select('hektor_negociateur_id,hektor_user_id,prenom,nom,email,agence_nom,is_active')
    .order('hektor_negociateur_id', { ascending: true })
    .range(de, a))
  return lignes.map((l) => ({
    nego: String(l.hektor_negociateur_id ?? '').trim(), user: String(l.hektor_user_id ?? '').trim() || null,
    nom: `${String(l.prenom ?? '').trim()} ${String(l.nom ?? '').trim()}`.trim(), email: String(l.email ?? '').trim() || null,
    agence: (l.agence_nom as string | null) ?? null, actif: l.is_active === true,
  })).filter((l) => l.nego)
}

// LE REGISTRE DES NÉGOCIATEURS (04/11, notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md) : la personne (NOTRE numéro) et
// TOUTES ses fiches Hektor, rattachées une fois pour toutes — y compris ce que l'annuaire ne sait pas (le compte admin n° 4,
// les comptes de secrétaire, les numéros de la répartition sans fiche, les anciens que Hektor ne liste plus).
export type PilotageRegistre = {
  personnes: Array<{ id: number; nom: string; email: string | null; type: string; actif: boolean }>
  fiches: Array<{ personne: number; nego: string | null; user: string | null; email: string | null; nom: string | null }>
}
async function lireRegistre(): Promise<PilotageRegistre> {
  if (!hasSupabaseEnv || !supabase) return mockRegistre()
  const client = supabase
  const [personnes, fiches] = await Promise.all([
    toutLire<Record<string, unknown>>((de, a) => client.from('app_negociateur_personne')
      .select('app_personne_id,nom,email,type_personne,actif').order('app_personne_id', { ascending: true }).range(de, a)),
    toutLire<Record<string, unknown>>((de, a) => client.from('app_negociateur_fiche')
      .select('app_fiche_id,app_personne_id,hektor_negociateur_id,hektor_user_id,email_vu,nom_vu').order('app_fiche_id', { ascending: true }).range(de, a)),
  ])
  if (!personnes.length) throw new Error('registre des négociateurs vide')
  return {
    personnes: personnes.map((p) => ({ id: Number(p.app_personne_id), nom: String(p.nom ?? ''), email: (p.email as string | null) ?? null,
      type: String(p.type_personne ?? ''), actif: p.actif === true })),
    fiches: fiches.map((f) => ({ personne: Number(f.app_personne_id), nego: String(f.hektor_negociateur_id ?? '').trim() || null,
      user: String(f.hektor_user_id ?? '').trim() || null, email: (f.email_vu as string | null) ?? null, nom: (f.nom_vu as string | null) ?? null })),
  }
}

/** Tout ce que le pilotage lit, pour l'année choisie et la précédente. Une source qui échoue n'empêche
 *  pas les autres : elle revient en Error, et seul son onglet le dit. */
export async function loadPilotage(annee: number): Promise<PilotageSources> {
  const [ventes, mandats, stock, signatures, portails, acquereurs, affairesPlus, annuaire, registre] = await Promise.allSettled([
    hasSupabaseEnv && supabase ? lireVentes(annee) : Promise.resolve(mockVentes(annee)),
    lireMandats(annee), lireStock(), lireSignatures(), lirePortails(), lireAcquereurs(annee), lireAffairesPlus(annee), lireAnnuaire(), lireRegistre(),
  ])
  const v = <T,>(r: PromiseSettledResult<T>) => (r.status === 'fulfilled' ? r.value : enErreur(r.reason))
  return {
    annee, ventes: v(ventes), mandats: v(mandats), stock: v(stock), signatures: v(signatures), portails: v(portails),
    acquereurs: v(acquereurs), affairesPlus: v(affairesPlus), annuaire: v(annuaire), registre: v(registre),
  }
}

// ───────────────────────────── outils communs ─────────────────────────────

const NOMS_AGENCES: Record<string, string> = {
  AMBERT: 'Ambert', ANNONAY: 'Annonay', BRIOUDE: 'Brioude', COURPIERE: 'Courpière', 'CRAPONNE-SUR-ARZON': 'Craponne-sur-Arzon',
  DUNIERES: 'Dunières', FIRMINY: 'Firminy', ISSOIRE: 'Issoire', 'LE-PUY-EN-VELAY': 'Le Puy-en-Velay', 'MONISTROL-SUR-LOIRE': 'Monistrol-sur-Loire',
  MONTBRISON: 'Montbrison', 'SAINT-BONNET-LE-CHATEAU': 'Saint-Bonnet-le-Château', 'SAINT-DIDIER-EN-VELAY': 'Saint-Didier-en-Velay',
  'SAINT-ETIENNE': 'Saint-Étienne', 'SAINT-JUST-SAINT-RAMBERT': 'Saint-Just-Saint-Rambert', TENCE: 'Tence', YSSINGEAUX: 'Yssingeaux',
}

/** La clé d'une agence, quelle que soit son écriture. Vide = sans agence. */
export function cleAgence(nom: string | null | undefined) {
  return String(nom ?? '')
    .replace(/^\s*groupe\s+gti\s*/i, '')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .trim().toUpperCase().replace(/[\s-]+/g, '-')
}

export function nomAgence(cle: string) {
  if (!cle) return 'Sans agence'
  return NOMS_AGENCES[cle] ?? cle.toLowerCase().split('-').map((mot) => mot.charAt(0).toUpperCase() + mot.slice(1)).join(' ')
}

/** « Mme. Sandrine DELAVAUD » -> « Sandrine DELAVAUD » */
export function nomPersonne(nom: string | null | undefined) {
  const propre = String(nom ?? '').replace(/^(m_mme|mr\.?\/mme\.?|mme\.?|mlle\.?|mr\.?|m\.)\s+/i, '').trim()
  if (!propre || /supprim/i.test(propre)) return 'Négociateur supprimé'
  return propre
}

export function aujourdhui() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const estDate = (texte: string | null | undefined) => /^[12]\d{3}-\d{2}-\d{2}/.test(String(texte ?? ''))
const jours = (de: string, a: string) => Math.round((Date.parse(a.slice(0, 10)) - Date.parse(de.slice(0, 10))) / 86400000)
export const mediane = (valeurs: number[]) => {
  if (!valeurs.length) return null
  const tri = [...valeurs].sort((a, b) => a - b)
  const milieu = Math.floor(tri.length / 2)
  return tri.length % 2 ? tri[milieu] : (tri[milieu - 1] + tri[milieu]) / 2
}
const somme = (valeurs: Array<number | null | undefined>) => valeurs.reduce<number>((total, valeur) => total + (valeur ?? 0), 0)

/** La borne « à date » de l'année comparée : même jour et mois, ou la fin de l'année si elle est close. */
export function borneADate(annee: number) {
  const jour = aujourdhui()
  return Number(jour.slice(0, 4)) === annee ? jour.slice(5) : '12-31'
}

// ───────────────────────────── VENTES ─────────────────────────────

export type VentesCalcul = {
  annee: number
  enCours: boolean
  borne: string
  honoraires: number
  honorairesPrec: number
  ventes: number
  ventesPrec: number
  volume: number
  volumePrec: number
  delaiOffreCompromis: number | null
  delaiCompromisActe: number | null
  delaisPrec: [number | null, number | null]
  delaiOffreActe: number | null
  delaiOffreActePrec: number | null
  parMois: Array<{ n: number; h: number }>
  parMoisPrec: Array<{ n: number; h: number }>
  actesDates: { n: number; h: number; parMois: Map<string, { n: number; h: number }>; dIciTroisMois: { n: number; h: number } }
  negos: Array<{ id: string; nom: string; dossiers: number; part: number; partPrec: number }>
  attribue: number
  agences: Map<string, { ventes: number; h: number; hPrec: number; ventesPrec: number }>
  // 03/11 (tableau de bord v3) : compromis signés dans l'année, mois par mois, et ce qui est en route aujourd'hui.
  compromis: { n: number; nPrec: number; parMois: number[]; parMoisPrec: number[] }
  enRoute: {
    compromis: { n: number; h: number }
    // Une offre acceptée n'a presque jamais ses honoraires (ils arrivent au compromis : 44 sur 47 à 0 le 03/11) :
    // ceux qui manquent sont estimés au taux de l'année (honoraires ÷ prix des ventes), comptés dans `estimes`.
    offresAcceptees: { n: number; h: number; estimes: number; taux: number }
    actesDepasses: { n: number; h: number }
    offresSansCompromis30: { n: number; h: number; estimes: number }
  }
}

export function calculerVentes(source: Exclude<PilotageSources['ventes'], Error>, annee: number, agence: string | null): VentesCalcul {
  const borne = borneADate(annee)
  const enCours = Number(aujourdhui().slice(0, 4)) === annee
  const garde = (ligne: RegistreDossierRow) => !agence || cleAgence(ligne.agence_nom) === agence
  const vendus = (lignes: RegistreDossierRow[], an: number, aDate: boolean) => lignes.filter((ligne) => ligne.etape === 'vendu'
    && String(ligne.date_vente ?? '').startsWith(String(an)) && garde(ligne)
    && (!aDate || String(ligne.date_vente).slice(5, 10) <= borne))
  const n = vendus(source.n, annee, false)
  const p = vendus(source.p, annee - 1, true)
  const pAnnee = vendus(source.p, annee - 1, false)
  const mois = (lignes: RegistreDossierRow[]) => {
    const sortie = Array.from({ length: 12 }, () => ({ n: 0, h: 0 }))
    for (const ligne of lignes) {
      const m = Number(String(ligne.date_vente).slice(5, 7)) - 1
      if (m >= 0 && m < 12) { sortie[m].n += 1; sortie[m].h += ligne.honoraires ?? 0 }
    }
    return sortie
  }
  const delais = (lignes: RegistreDossierRow[]): [number | null, number | null] => [
    mediane(lignes.filter((l) => estDate(l.date_offre) && estDate(l.date_compromis)).map((l) => jours(l.date_offre as string, l.date_compromis as string)).filter((x) => x >= 0)),
    mediane(lignes.filter((l) => estDate(l.date_compromis) && estDate(l.date_vente)).map((l) => jours(l.date_compromis as string, l.date_vente as string)).filter((x) => x >= 0)),
  ]
  const delaiTotal = (lignes: RegistreDossierRow[]) =>
    mediane(lignes.filter((l) => estDate(l.date_offre) && estDate(l.date_vente)).map((l) => jours(l.date_offre as string, l.date_vente as string)).filter((x) => x >= 0))
  // Actes déjà datés : compromis en cours dont l'acte est prévu à partir d'aujourd'hui (N et N-1 lus).
  const jour = aujourdhui()
  const vus = new Set<number>()
  const actes = { n: 0, h: 0, parMois: new Map<string, { n: number; h: number }>(), dIciTroisMois: { n: 0, h: 0 } }
  const limite = (() => { const d = new Date(); d.setMonth(d.getMonth() + 3); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-31` })()
  for (const ligne of [...source.n, ...source.p]) {
    if (ligne.etape !== 'compromis' || !garde(ligne) || vus.has(ligne.app_chaine_id)) continue
    const date = String(ligne.date_acte_prevue ?? '').slice(0, 10)
    if (!estDate(date) || date < jour) continue
    vus.add(ligne.app_chaine_id)
    actes.n += 1; actes.h += ligne.honoraires ?? 0
    const cle = date.slice(0, 7)
    const m = actes.parMois.get(cle) ?? { n: 0, h: 0 }
    m.n += 1; m.h += ligne.honoraires ?? 0
    actes.parMois.set(cle, m)
    if (date.slice(0, 7) <= limite.slice(0, 7)) { actes.dIciTroisMois.n += 1; actes.dIciTroisMois.h += ligne.honoraires ?? 0 }
  }
  // Négociateurs : part = honoraires × pourcentage / 100, entrée et sortie confondues.
  const parts = (lignes: RegistreDossierRow[], rep: Map<string, RepartitionLigne[]>) => {
    const sortie = new Map<string, { nom: string; part: number; dossiers: Set<number> }>()
    for (const ligne of lignes) {
      for (const r of rep.get(String(ligne.app_chaine_id)) ?? []) {
        const id = r.hektorUserId || '0'
        const e = sortie.get(id) ?? { nom: nomPersonne(r.nomAuMoment), part: 0, dossiers: new Set<number>() }
        e.part += ((ligne.honoraires ?? 0) * r.pourcentage) / 100
        e.dossiers.add(ligne.app_chaine_id)
        sortie.set(id, e)
      }
    }
    return sortie
  }
  const pn = parts(n, source.repN)
  const pp = parts(p, source.repP)
  const negos = [...pn.entries()].map(([id, e]) => ({ id, nom: id === '0' ? 'Négociateurs supprimés' : e.nom, dossiers: e.dossiers.size, part: e.part, partPrec: pp.get(id)?.part ?? 0 }))
    .sort((a, b) => b.part - a.part)
  const agences = new Map<string, { ventes: number; h: number; hPrec: number; ventesPrec: number }>()
  for (const ligne of n) { const a = agences.get(cleAgence(ligne.agence_nom)) ?? { ventes: 0, h: 0, hPrec: 0, ventesPrec: 0 }; a.ventes += 1; a.h += ligne.honoraires ?? 0; agences.set(cleAgence(ligne.agence_nom), a) }
  for (const ligne of p) { const a = agences.get(cleAgence(ligne.agence_nom)) ?? { ventes: 0, h: 0, hPrec: 0, ventesPrec: 0 }; a.ventesPrec += 1; a.hPrec += ligne.honoraires ?? 0; agences.set(cleAgence(ligne.agence_nom), a) }
  // Compromis signés : une chaîne compte l'année de SA date de compromis, qu'elle soit allée à l'acte,
  // tombée ou encore en cours. Les deux lectures (N et N-1) sont parcourues : un compromis de décembre
  // vendu en janvier est rangé sous l'année de la vente par la lecture.
  const toutes = new Map<number, RegistreDossierRow>()
  for (const ligne of [...source.n, ...source.p]) if (garde(ligne) && !toutes.has(ligne.app_chaine_id)) toutes.set(ligne.app_chaine_id, ligne)
  const cp = { n: 0, nPrec: 0, parMois: Array.from({ length: 12 }, () => 0), parMoisPrec: Array.from({ length: 12 }, () => 0) }
  for (const ligne of toutes.values()) {
    const date = String(ligne.date_compromis ?? '').slice(0, 10)
    if (!estDate(date)) continue
    const m = Number(date.slice(5, 7)) - 1
    if (date.startsWith(String(annee))) { cp.n += 1; cp.parMois[m] += 1 }
    else if (date.startsWith(String(annee - 1))) { cp.parMoisPrec[m] += 1; if (date.slice(5, 10) <= borne) cp.nPrec += 1 }
  }
  // Ce qui est en route aujourd'hui (seulement les chaînes lues : dernier événement en N ou N-1).
  const tauxAnnee = (() => { const v = somme(n.map((l) => l.montant)); return v ? somme(n.map((l) => l.honoraires)) / v : 0 })()
  const route = { compromis: { n: 0, h: 0 }, offresAcceptees: { n: 0, h: 0, estimes: 0, taux: tauxAnnee }, actesDepasses: { n: 0, h: 0 }, offresSansCompromis30: { n: 0, h: 0, estimes: 0 } }
  const ilYa30 = (() => { const d = new Date(`${jour}T12:00:00`); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10) })()
  for (const ligne of toutes.values()) {
    const h = ligne.honoraires ?? 0
    if (ligne.etape === 'compromis') {
      route.compromis.n += 1; route.compromis.h += h
      const prevue = String(ligne.date_acte_prevue ?? '').slice(0, 10)
      if (estDate(prevue) && prevue < jour) { route.actesDepasses.n += 1; route.actesDepasses.h += h }
    } else if (ligne.etape === 'offre_acceptee') {
      const estime = h > 0 ? 0 : 1
      const hOffre = h > 0 ? h : (ligne.montant ?? 0) * tauxAnnee
      route.offresAcceptees.n += 1; route.offresAcceptees.h += hOffre; route.offresAcceptees.estimes += estime
      const offre = String(ligne.date_offre ?? '').slice(0, 10)
      if (estDate(offre) && offre <= ilYa30) { route.offresSansCompromis30.n += 1; route.offresSansCompromis30.h += hOffre; route.offresSansCompromis30.estimes += estime }
    }
  }
  return {
    annee, enCours, borne,
    compromis: cp, enRoute: route,
    honoraires: somme(n.map((l) => l.honoraires)), honorairesPrec: somme(p.map((l) => l.honoraires)),
    ventes: n.length, ventesPrec: p.length,
    volume: somme(n.map((l) => l.montant)), volumePrec: somme(p.map((l) => l.montant)),
    delaiOffreCompromis: delais(n)[0], delaiCompromisActe: delais(n)[1], delaisPrec: delais(p),
    delaiOffreActe: delaiTotal(n), delaiOffreActePrec: delaiTotal(p),
    parMois: mois(n), parMoisPrec: mois(pAnnee),
    actesDates: actes, negos, attribue: somme(negos.map((x) => x.part)), agences,
  }
}

// ───────────────────────────── MANDATS ─────────────────────────────

export type MandatsCalcul = {
  n: number; nPrec: number; exclusifs: number; exclusifsPrec: number; semi: number; semiPrec: number
  parMois: Array<{ n: number; ex: number }>
  parMoisPrec: number[]
  types: Array<{ cle: string; libelle: string; n: number; nPrec: number; prixMedian: number | null }>
  agences: Map<string, { n: number; nPrec: number; ex: number }>
  negos: Array<{ nom: string; n: number; nPrec: number; ex: number }>
  nbNegos: number
}

export const LIBELLE_TYPE: Record<string, string> = { SIMPLE: 'Simple', EXCLUSIF: 'Exclusif', ACCORD: 'Semi-exclusif' }

export function calculerMandats(lignes: PilotageMandat[], annee: number, agence: string | null): MandatsCalcul {
  const borne = borneADate(annee)
  const garde = (l: PilotageMandat) => !agence || cleAgence(l.agence) === agence
  const n = lignes.filter((l) => l.debut.startsWith(String(annee)) && l.debut.slice(5) <= borne && garde(l))
  const p = lignes.filter((l) => l.debut.startsWith(String(annee - 1)) && l.debut.slice(5) <= borne && garde(l))
  const pAnnee = lignes.filter((l) => l.debut.startsWith(String(annee - 1)) && garde(l))
  const parMois = Array.from({ length: 12 }, () => ({ n: 0, ex: 0 }))
  for (const l of n) { const m = Number(l.debut.slice(5, 7)) - 1; if (m >= 0 && m < 12) { parMois[m].n += 1; if (l.type === 'EXCLUSIF') parMois[m].ex += 1 } }
  const parMoisPrec = Array.from({ length: 12 }, () => 0)
  for (const l of pAnnee) { const m = Number(l.debut.slice(5, 7)) - 1; if (m >= 0 && m < 12) parMoisPrec[m] += 1 }
  const types = ['SIMPLE', 'EXCLUSIF', 'ACCORD'].map((cle) => ({
    cle, libelle: LIBELLE_TYPE[cle],
    n: n.filter((l) => l.type === cle).length, nPrec: p.filter((l) => l.type === cle).length,
    prixMedian: mediane(n.filter((l) => l.type === cle && (l.montant ?? 0) > 1000).map((l) => l.montant as number)),
  }))
  const agences = new Map<string, { n: number; nPrec: number; ex: number }>()
  for (const l of n) { const a = agences.get(cleAgence(l.agence)) ?? { n: 0, nPrec: 0, ex: 0 }; a.n += 1; if (l.type === 'EXCLUSIF') a.ex += 1; agences.set(cleAgence(l.agence), a) }
  for (const l of p) { const a = agences.get(cleAgence(l.agence)) ?? { n: 0, nPrec: 0, ex: 0 }; a.nPrec += 1; agences.set(cleAgence(l.agence), a) }
  const parNego = new Map<string, { nom: string; n: number; nPrec: number; ex: number }>()
  for (const l of n) { const cle = nomPersonne(l.nego); const e = parNego.get(cle) ?? { nom: cle, n: 0, nPrec: 0, ex: 0 }; e.n += 1; if (l.type === 'EXCLUSIF') e.ex += 1; parNego.set(cle, e) }
  for (const l of p) { const cle = nomPersonne(l.nego); const e = parNego.get(cle); if (e) e.nPrec += 1 }
  return {
    n: n.length, nPrec: p.length,
    exclusifs: n.filter((l) => l.type === 'EXCLUSIF').length, exclusifsPrec: p.filter((l) => l.type === 'EXCLUSIF').length,
    semi: n.filter((l) => l.type === 'ACCORD').length, semiPrec: p.filter((l) => l.type === 'ACCORD').length,
    parMois, parMoisPrec, types, agences,
    negos: [...parNego.values()].sort((a, b) => b.n - a.n), nbNegos: parNego.size,
  }
}

export function calculerSignatures(lignes: PilotageSignature[], annee: number) {
  const parMois = Array.from({ length: 12 }, () => 0)
  let signes = 0
  for (const l of lignes) {
    if (l.statut !== 'signed' || !l.signeLe?.startsWith(String(annee))) continue
    signes += 1
    parMois[Number(l.signeLe.slice(5, 7)) - 1] += 1
  }
  return { signes, enAttente: lignes.filter((l) => l.statut === 'pending').length, parMois }
}

// ───────────────────────────── STOCK ─────────────────────────────

export type StockCalcul = {
  actifs: number; engages: number; sousOffre: number; sousCompromis: number
  potentiel: number; avecHonoraires: number; sansHonoraires: number; estime: number; tauxMedian: number | null
  honorairesMedian: number | null; potentielEngages: number
  ageMedian: number | null; plusDe6Mois: number; plusDUnAn: number
  tranches: Array<{ libelle: string; biens: number; avec: number; h: number; ton: string }>
  types: Array<{ libelle: string; biens: number; h: number; ton: string }>
  nonDiffusables: number; hNonDiffusables: number; sansPortail: number
  baisses: number; baisseMediane: number | null
  echus: number; echoient30: number
  hBloque6Mois: number
  agences: Map<string, { actifs: number; engages: number; h: number; sans: number; ages: number[]; vieux: number; nonDif: number; echus: number }>
  // 03/11 : le même portefeuille, négociateur par négociateur (le nom de la fiche du bien). Un bien sans nom
  // n'est rangé chez personne : il est compté à part, pour que la note le dise.
  negos: Map<string, { nom: string; actifs: number; engages: number; h: number; sans: number; ages: number[]; vieux: number; nonDif: number; echus: number }>
  sansNego: { actifs: number; engages: number }
}

const estNonDiffusable = (s: PilotageStock) => s.diffusable === '0' || s.diffusable === 'false'
const estDiffusable = (s: PilotageStock) => s.diffusable === '1' || s.diffusable === 'true'

export function calculerStock(lignes: PilotageStock[], agence: string | null): StockCalcul {
  const jour = aujourdhui()
  const dans30 = (() => { const d = new Date(); d.setDate(d.getDate() + 30); return d.toISOString().slice(0, 10) })()
  const toutes = lignes.filter((s) => !agence || cleAgence(s.agence_nom) === agence)
  const actifs = toutes.filter((s) => s.statut_annonce === 'Actif')
  const engages = toutes.filter((s) => s.statut_annonce !== 'Actif')
  const age = (s: PilotageStock) => (estDate(s.mandat_date_debut) && String(s.mandat_date_debut) > '1990' ? jours(s.mandat_date_debut as string, jour) : null)
  const avec = actifs.filter((s) => (s.honoraires ?? 0) > 0)
  const taux = mediane(avec.filter((s) => (s.prix ?? 0) > 0).map((s) => (s.honoraires as number) / (s.prix as number)))
  const prixSans = somme(actifs.filter((s) => !((s.honoraires ?? 0) > 0)).map((s) => s.prix))
  const tranche = (min: number, max: number) => actifs.filter((s) => { const a = age(s); return a != null && a >= min && a <= max })
  const tranches = [
    { libelle: 'Moins de 3 mois', biens: tranche(0, 91), ton: '#1f6a49' },
    { libelle: '3 à 6 mois', biens: tranche(92, 183), ton: '#7fae95' },
    { libelle: '6 à 12 mois', biens: tranche(184, 365), ton: '#d8a24a' },
    { libelle: 'Plus d’un an', biens: tranche(366, 1e6), ton: '#8d3a37' },
    { libelle: 'Sans date', biens: actifs.filter((s) => age(s) == null), ton: '#c9ced0' },
  ].map((t) => ({ libelle: t.libelle, biens: t.biens.length, avec: t.biens.filter((s) => (s.honoraires ?? 0) > 0).length, h: somme(t.biens.map((s) => s.honoraires)), ton: t.ton }))
  const type = (s: PilotageStock) => String(s.mandat_type ?? '').trim().toUpperCase()
  const types = [
    { libelle: 'Simple', filtre: (s: PilotageStock) => type(s) === 'SIMPLE', ton: '#a9bfe0' },
    { libelle: 'Exclusif', filtre: (s: PilotageStock) => type(s) === 'EXCLUSIF', ton: '#2f5fa7' },
    { libelle: 'Semi-exclusif', filtre: (s: PilotageStock) => type(s) === 'ACCORD', ton: '#5b4a8b' },
    { libelle: 'Autre ou non renseigné', filtre: (s: PilotageStock) => !['SIMPLE', 'EXCLUSIF', 'ACCORD'].includes(type(s)), ton: '#c9ced0' },
  ].map((t) => { const biens = actifs.filter(t.filtre); return { libelle: t.libelle, biens: biens.length, h: somme(biens.map((s) => s.honoraires)), ton: t.ton } })
  const baisses = actifs.filter((s) => s.price_change_last_old_value != null && s.price_change_last_new_value != null && (s.price_change_last_new_value as number) < (s.price_change_last_old_value as number))
  const echu = (s: PilotageStock) => estDate(s.mandat_date_fin) && String(s.mandat_date_fin) > '1990' && String(s.mandat_date_fin).slice(0, 10) < jour
  type Portefeuille = { actifs: number; engages: number; h: number; sans: number; ages: number[]; vieux: number; nonDif: number; echus: number }
  const compter = (a: Portefeuille, s: PilotageStock) => {
    if (s.statut_annonce === 'Actif') {
      a.actifs += 1; a.h += s.honoraires ?? 0
      if (!((s.honoraires ?? 0) > 0)) a.sans += 1
      const x = age(s); if (x != null) { a.ages.push(x); if (x > 183) a.vieux += 1 }
      if (estNonDiffusable(s)) a.nonDif += 1
      if (echu(s)) a.echus += 1
    } else a.engages += 1
  }
  const agences = new Map<string, Portefeuille>()
  const negos = new Map<string, Portefeuille & { nom: string }>()
  const sansNego = { actifs: 0, engages: 0 }
  for (const s of toutes) {
    const cle = cleAgence(s.agence_nom)
    const a = agences.get(cle) ?? { actifs: 0, engages: 0, h: 0, sans: 0, ages: [], vieux: 0, nonDif: 0, echus: 0 }
    compter(a, s)
    agences.set(cle, a)
    if (!String(s.commercial_nom ?? '').trim()) {
      if (s.statut_annonce === 'Actif') sansNego.actifs += 1
      else sansNego.engages += 1
      continue
    }
    const cleN = cleNom(s.commercial_nom as string)
    const n = negos.get(cleN) ?? { nom: nomPersonne(s.commercial_nom), actifs: 0, engages: 0, h: 0, sans: 0, ages: [], vieux: 0, nonDif: 0, echus: 0 }
    compter(n, s)
    negos.set(cleN, n)
  }
  const ages = actifs.map(age).filter((x): x is number => x != null)
  return {
    actifs: actifs.length, engages: engages.length,
    sousOffre: engages.filter((s) => s.statut_annonce === 'Sous offre').length, sousCompromis: engages.filter((s) => s.statut_annonce === 'Sous compromis').length,
    potentiel: somme(actifs.map((s) => s.honoraires)), avecHonoraires: avec.length, sansHonoraires: actifs.length - avec.length,
    estime: taux != null ? prixSans * taux : 0, tauxMedian: taux,
    honorairesMedian: mediane(avec.map((s) => s.honoraires as number)), potentielEngages: somme(engages.map((s) => s.honoraires)),
    ageMedian: mediane(ages), plusDe6Mois: ages.filter((x) => x > 183).length, plusDUnAn: ages.filter((x) => x > 365).length,
    tranches, types,
    nonDiffusables: actifs.filter(estNonDiffusable).length, hNonDiffusables: somme(actifs.filter(estNonDiffusable).map((s) => s.honoraires)),
    sansPortail: actifs.filter((s) => estDiffusable(s) && !(s.nb_portails_actifs ?? 0)).length,
    baisses: baisses.length, baisseMediane: mediane(baisses.map((s) => (s.price_change_last_new_value as number) / (s.price_change_last_old_value as number) - 1)),
    echus: actifs.filter(echu).length,
    echoient30: actifs.filter((s) => estDate(s.mandat_date_fin) && String(s.mandat_date_fin).slice(0, 10) >= jour && String(s.mandat_date_fin).slice(0, 10) <= dans30).length,
    hBloque6Mois: somme(actifs.filter((s) => (age(s) ?? 0) > 183).map((s) => s.honoraires)),
    agences, negos, sansNego,
  }
}

export const NOMS_PORTAILS: Record<string, string> = {
  etreproprio: 'Etreproprio', superimmo: 'Superimmo', leboncoinDirect: 'Leboncoin', bienicidirect: 'Bien’ici', paper: 'Papier', seloger: 'SeLoger', logicimmo: 'Logic-immo',
}

export function calculerPortails(lignes: PilotagePortail[], stock: PilotageStock[], agence: string | null) {
  const actifs = new Set(stock.filter((s) => s.statut_annonce === 'Actif' && estDiffusable(s) && (!agence || cleAgence(s.agence_nom) === agence)).map((s) => s.app_dossier_id))
  const parPortail = new Map<string, { ok: number; erreur: number }>()
  for (const l of lignes) {
    if (!actifs.has(l.dossier)) continue
    const p = parPortail.get(l.portail) ?? { ok: 0, erreur: 0 }
    if (l.ok) p.ok += 1
    if (l.erreur) p.erreur += 1
    parPortail.set(l.portail, p)
  }
  return { diffusables: actifs.size, portails: [...parPortail.entries()].map(([cle, p]) => ({ cle, libelle: NOMS_PORTAILS[cle] ?? cle, ...p })).filter((p) => p.ok > 0).sort((a, b) => b.ok - a.ok) }
}

// ───────────────────────────── données de maquette (sans base) ─────────────────────────────
// Servies seulement quand l'app tourne sans base (mode maquette local) : des chiffres inventés, plausibles.

function hasard(graine: number) {
  let x = graine
  return () => { x = (x * 1103515245 + 12345) % 2147483648; return x / 2147483648 }
}
const AGENCES_MAQUETTE = ['Groupe GTI COURPIERE', 'Groupe GTI Craponne-sur-Arzon', 'Groupe Gti Le Puy en Velay', 'Groupe GTI Yssingeaux', 'Groupe GTI Ambert   ', 'Groupe GTI Issoire', 'Groupe GTI ANNONAY', 'Groupe GTI Firminy']
const NEGOS_MAQUETTE = ['Mélanie LEGRAND', 'Arnaud VALLA', 'Claire RIBBES', 'Mme. Sandrine DELAVAUD', 'Nicolas COUDERT', 'Christèle GENTES']

function mockVentes(annee: number) {
  const fabriquer = (an: number, graine: number) => {
    const r = hasard(graine)
    const lignes: RegistreDossierRow[] = []
    const repartition = new Map<string, RepartitionLigne[]>()
    const finMois = an === Number(aujourdhui().slice(0, 4)) ? Number(aujourdhui().slice(5, 7)) : 12
    for (let i = 0; i < 260; i += 1) {
      const m = 1 + Math.floor(r() * finMois)
      const j = 1 + Math.floor(r() * 27)
      const prix = 80000 + Math.round(r() * 220000)
      const h = Math.round(prix * (0.05 + r() * 0.03))
      const vendu = r() < 0.86
      const date = `${an}-${String(m).padStart(2, '0')}-${String(j).padStart(2, '0')}`
      const id = graine * 10000 + i
      lignes.push({
        app_chaine_id: id, app_dossier_id: id, hektor_annonce_id: id, etape: vendu ? 'vendu' : 'compromis',
        date_offre: date, date_compromis: date, date_acte_prevue: vendu ? null : `${an + 1}-0${1 + Math.floor(r() * 3)}-15`,
        date_vente: vendu ? date : null, date_dernier_evenement: date, montant: prix, honoraires_entree: h, honoraires_sortie: 0, honoraires: h,
        hektor_acquereur_id: null, acquereur_nom: null, numero_mandat: null, ville: null, code_postal: null, type_bien: '1', photo_url_listing: null,
        agence_nom: AGENCES_MAQUETTE[Math.floor(r() * AGENCES_MAQUETTE.length)], negociateur_email: null, statut_annonce: null, nb_transactions: 2, je_suis_nomme: false,
      })
      const a = Math.floor(r() * NEGOS_MAQUETTE.length)
      repartition.set(String(id), [
        { cote: 'entree', rang: 1, hektorUserId: String(a + 1), nomAuMoment: NEGOS_MAQUETTE[a], pourcentage: 50, origine: null },
        { cote: 'sortie', rang: 1, hektorUserId: String(((a + 2) % NEGOS_MAQUETTE.length) + 1), nomAuMoment: NEGOS_MAQUETTE[(a + 2) % NEGOS_MAQUETTE.length], pourcentage: 50, origine: null },
      ])
    }
    return { lignes, repartition }
  }
  const n = fabriquer(annee, 7)
  const p = fabriquer(annee - 1, 11)
  return { n: n.lignes, p: p.lignes, repN: n.repartition, repP: p.repartition }
}

function mockMandats(annee: number): PilotageMandat[] {
  const r = hasard(23)
  const sortie: PilotageMandat[] = []
  for (const an of [annee - 1, annee]) {
    const finMois = an === Number(aujourdhui().slice(0, 4)) ? Number(aujourdhui().slice(5, 7)) : 12
    for (let i = 0; i < 640; i += 1) {
      const t = r()
      sortie.push({
        debut: `${an}-${String(1 + Math.floor(r() * finMois)).padStart(2, '0')}-${String(1 + Math.floor(r() * 27)).padStart(2, '0')}`,
        type: t < 0.42 ? 'EXCLUSIF' : t < 0.5 ? 'ACCORD' : 'SIMPLE',
        agence: AGENCES_MAQUETTE[Math.floor(r() * AGENCES_MAQUETTE.length)], nego: NEGOS_MAQUETTE[Math.floor(r() * NEGOS_MAQUETTE.length)],
        montant: 90000 + Math.round(r() * 180000), annonce: null, negoId: null,
      })
    }
  }
  return sortie
}

function mockStock(): PilotageStock[] {
  const r = hasard(41)
  const jour = Date.now()
  return Array.from({ length: 420 }, (_, i) => {
    const prix = 70000 + Math.round(r() * 260000)
    const debut = new Date(jour - Math.round(r() * 520) * 86400000).toISOString().slice(0, 10)
    const fin = new Date(Date.parse(debut) + 365 * 86400000).toISOString().slice(0, 10)
    const statut = r() < 0.82 ? 'Actif' : r() < 0.6 ? 'Sous compromis' : 'Sous offre'
    const t = r()
    return {
      app_dossier_id: 900000 + i, statut_annonce: statut, agence_nom: AGENCES_MAQUETTE[Math.floor(r() * AGENCES_MAQUETTE.length)], commercial_nom: NEGOS_MAQUETTE[i % NEGOS_MAQUETTE.length],
      commercial_id: String((i % NEGOS_MAQUETTE.length) + 101), hektor_annonce_id: null,
      prix, mandat_type: t < 0.28 ? 'EXCLUSIF' : t < 0.36 ? 'ACCORD' : t < 0.8 ? 'SIMPLE' : null, mandat_date_debut: r() < 0.85 ? debut : null, mandat_date_fin: fin,
      diffusable: r() < 0.6 ? '1' : '0', nb_portails_actifs: r() < 0.95 ? 4 : 0,
      price_change_last_old_value: r() < 0.15 ? prix * 1.07 : null, price_change_last_new_value: prix, honoraires: r() < 0.72 ? Math.round(prix * 0.065) : null,
    }
  })
}

// Maquette : chaque négociateur a sa fiche n° 101… (celle du stock de maquette) et une 2e fiche dans une autre
// agence, sous le même e-mail — comme chez Hektor.
function mockAnnuaire(): PilotageNegociateur[] {
  return NEGOS_MAQUETTE.flatMap((nom, i) => {
    const propre = nomPersonne(nom)
    const email = `${propre.split(' ').pop()?.toLowerCase()}@exemple.fr`
    return [
      { nego: String(101 + i), user: String(i + 1), nom: propre, email, agence: AGENCES_MAQUETTE[i % AGENCES_MAQUETTE.length], actif: true },
      { nego: String(201 + i), user: String(51 + i), nom: propre, email, agence: AGENCES_MAQUETTE[(i + 3) % AGENCES_MAQUETTE.length], actif: false },
    ]
  })
}

// Maquette : le registre tiré de l'annuaire de maquette (une personne par e-mail).
function mockRegistre(): PilotageRegistre {
  const annuaire = mockAnnuaire()
  const ids = new Map<string, number>()
  for (const l of annuaire) if (!ids.has(l.email ?? l.nom)) ids.set(l.email ?? l.nom, 1000001 + ids.size)
  return {
    personnes: [...ids.entries()].map(([cle, id]) => {
      const l = annuaire.find((x) => (x.email ?? x.nom) === cle) as PilotageNegociateur
      return { id, nom: l.nom, email: l.email, type: 'negociateur', actif: annuaire.some((x) => (x.email ?? x.nom) === cle && x.actif) }
    }),
    fiches: annuaire.map((l) => ({ personne: ids.get(l.email ?? l.nom) as number, nego: l.nego, user: l.user, email: l.email, nom: l.nom })),
  }
}

function mockSignatures(): PilotageSignature[] {
  const r = hasard(59)
  const an = aujourdhui().slice(0, 4)
  const finMois = Number(aujourdhui().slice(5, 7))
  return Array.from({ length: 360 }, () => ({ statut: r() < 0.9 ? 'signed' as const : 'pending' as const, signeLe: `${an}-${String(2 + Math.floor(r() * Math.max(1, finMois - 1))).padStart(2, '0')}-10`, annonce: null }))
}

function mockPortails(): PilotagePortail[] {
  const stock = mockStock()
  const sortie: PilotagePortail[] = []
  for (const s of stock) for (const portail of ['etreproprio', 'superimmo', 'leboncoinDirect', 'bienicidirect']) sortie.push({ dossier: s.app_dossier_id, portail, ok: (s.app_dossier_id + portail.length) % 7 !== 0, erreur: (s.app_dossier_id + portail.length) % 41 === 0 })
  return sortie
}

// ───────────────────────────── AFFAIRES (03/11) ─────────────────────────────
// Une « affaire » est une chaîne du registre des transactions (une offre, puis peut-être un compromis, puis l'acte).
// Elle compte dans l'année de SA date d'offre. Les deux lectures (N et N-1) sont parcourues et dédoublonnées.

export type AffairesCalcul = {
  offres: number; offresPrec: number
  devenir: { poursuivies: number; enAttente: number; tombees: number; refusees: number; enDiscussion: number }
  offresParMois: number[]; offresParMoisPrec: number[]
  delaiOffreCompromis: { mediane: number | null; moins30: number; de30a60: number; plus60: number }
  compromis: number; compromisAnnules: number
  actesEnRetard: { n: number; sur: number }
  agences: Map<string, { offres: number; poursuivies: number; tombees: number; compromis: number; actes: number; delais: number[] }>
}

export function calculerAffaires(source: Exclude<PilotageSources['ventes'], Error>, annee: number, agence: string | null): AffairesCalcul {
  const borne = borneADate(annee)
  const garde = (ligne: RegistreDossierRow) => !agence || cleAgence(ligne.agence_nom) === agence
  const toutes = new Map<number, RegistreDossierRow>()
  for (const ligne of [...source.n, ...source.p]) if (garde(ligne) && !toutes.has(ligne.app_chaine_id)) toutes.set(ligne.app_chaine_id, ligne)
  const sortie: AffairesCalcul = {
    offres: 0, offresPrec: 0,
    devenir: { poursuivies: 0, enAttente: 0, tombees: 0, refusees: 0, enDiscussion: 0 },
    offresParMois: Array.from({ length: 12 }, () => 0), offresParMoisPrec: Array.from({ length: 12 }, () => 0),
    delaiOffreCompromis: { mediane: null, moins30: 0, de30a60: 0, plus60: 0 },
    compromis: 0, compromisAnnules: 0, actesEnRetard: { n: 0, sur: 0 }, agences: new Map(),
  }
  const delais: number[] = []
  const agenceDe = (cle: string) => {
    const a = sortie.agences.get(cle) ?? { offres: 0, poursuivies: 0, tombees: 0, compromis: 0, actes: 0, delais: [] }
    sortie.agences.set(cle, a)
    return a
  }
  for (const ligne of toutes.values()) {
    const offre = String(ligne.date_offre ?? '').slice(0, 10)
    const cp = String(ligne.date_compromis ?? '').slice(0, 10)
    const a = agenceDe(cleAgence(ligne.agence_nom))
    if (estDate(cp) && cp.startsWith(String(annee))) {
      sortie.compromis += 1; a.compromis += 1
      if (ligne.etape === 'compromis_annule') sortie.compromisAnnules += 1
    }
    if (ligne.etape === 'vendu' && String(ligne.date_vente ?? '').startsWith(String(annee))) {
      a.actes += 1
      const prevue = String(ligne.date_acte_prevue ?? '').slice(0, 10)
      if (estDate(prevue)) { sortie.actesEnRetard.sur += 1; if (String(ligne.date_vente).slice(0, 10) > prevue) sortie.actesEnRetard.n += 1 }
    }
    if (!estDate(offre)) continue
    const m = Number(offre.slice(5, 7)) - 1
    if (offre.startsWith(String(annee - 1))) {
      sortie.offresParMoisPrec[m] += 1
      if (offre.slice(5, 10) <= borne) sortie.offresPrec += 1
      continue
    }
    if (!offre.startsWith(String(annee))) continue
    sortie.offres += 1; sortie.offresParMois[m] += 1; a.offres += 1
    if (ligne.etape === 'vendu' || ligne.etape === 'compromis') { sortie.devenir.poursuivies += 1; a.poursuivies += 1 }
    else if (ligne.etape === 'offre_acceptee') sortie.devenir.enAttente += 1
    else if (ligne.etape === 'compromis_annule') { sortie.devenir.tombees += 1; a.tombees += 1 }
    else if (ligne.etape === 'offre_refusee') { sortie.devenir.refusees += 1; a.tombees += 1 }
    else sortie.devenir.enDiscussion += 1
    if (estDate(cp)) {
      const j = jours(offre, cp)
      if (j >= 0) {
        delais.push(j); a.delais.push(j)
        if (j <= 30) sortie.delaiOffreCompromis.moins30 += 1
        else if (j <= 60) sortie.delaiOffreCompromis.de30a60 += 1
        else sortie.delaiOffreCompromis.plus60 += 1
      }
    }
  }
  sortie.delaiOffreCompromis.mediane = mediane(delais)
  return sortie
}

// ───────────────────────────── CLASSEMENTS (03/11) ─────────────────────────────
// Négociateurs : honoraires = part de la répartition (comme l'onglet Ventes) ; mandats au négociateur de la fiche ;
// portefeuille = biens en vente à son nom aujourd'hui. Les trois sources ne portent pas le nom de la même façon :
// on les rapproche sur le nom sans civilité, sans accent, en minuscules.

export type LigneClassement = {
  cle: string; nom: string
  ca: number; caPrec: number; actes: number
  mandats: number; mandatsPrec: number; exclusifs: number
  portefeuille: number; potentiel: number
  compromis: number
}

export const cleNom = (nom: string) => nomPersonne(nom).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim()

export function calculerClassements(ventes: VentesCalcul | null, mandats: MandatsCalcul | null, stock: PilotageStock[] | null, affaires: AffairesCalcul | null, agence: string | null) {
  const vide = (cle: string, nom: string): LigneClassement => ({ cle, nom, ca: 0, caPrec: 0, actes: 0, mandats: 0, mandatsPrec: 0, exclusifs: 0, portefeuille: 0, potentiel: 0, compromis: 0 })
  const negos = new Map<string, LigneClassement>()
  const nego = (nom: string) => { const cle = cleNom(nom); const e = negos.get(cle) ?? vide(cle, nomPersonne(nom)); negos.set(cle, e); return e }
  for (const n of ventes?.negos ?? []) { if (n.id === '0') continue; const e = nego(n.nom); e.ca += n.part; e.caPrec += n.partPrec; e.actes += n.dossiers }
  for (const n of mandats?.negos ?? []) { if (/supprim/i.test(n.nom)) continue; const e = nego(n.nom); e.mandats += n.n; e.mandatsPrec += n.nPrec; e.exclusifs += n.ex }
  for (const s of stock ?? []) {
    if (agence && cleAgence(s.agence_nom) !== agence) continue
    if (!s.commercial_nom || /supprim/i.test(s.commercial_nom)) continue
    if (s.statut_annonce !== 'Actif') continue
    const e = nego(s.commercial_nom); e.portefeuille += 1; e.potentiel += s.honoraires ?? 0
  }
  const agences = new Map<string, LigneClassement>()
  const ag = (cle: string) => { const e = agences.get(cle) ?? vide(cle, nomAgence(cle)); agences.set(cle, e); return e }
  for (const [cle, a] of ventes?.agences ?? []) { if (!cle) continue; const e = ag(cle); e.ca += a.h; e.caPrec += a.hPrec; e.actes += a.ventes }
  for (const [cle, a] of mandats?.agences ?? []) { if (!cle) continue; const e = ag(cle); e.mandats += a.n; e.mandatsPrec += a.nPrec; e.exclusifs += a.ex }
  for (const [cle, a] of affaires?.agences ?? []) { if (!cle) continue; ag(cle).compromis += a.compromis }
  for (const s of stock ?? []) {
    const cle = cleAgence(s.agence_nom)
    if (!cle || (agence && cle !== agence)) continue
    if (s.statut_annonce !== 'Actif') continue
    const e = ag(cle); e.portefeuille += 1; e.potentiel += s.honoraires ?? 0
  }
  const garder = (e: LigneClassement) => e.ca > 0 || e.mandats > 0 || e.portefeuille > 0
  return { negos: [...negos.values()].filter(garder), agences: [...agences.values()].filter(garder) }
}

// ───────────────────────────── AFFAIRES, LE PRIX ET LES NOTAIRES (03/11) ─────────────────────────────

export type AffairesPlusCalcul = {
  remises: { n: number; mediane: number | null; tranches: Array<{ libelle: string; n: number; ton: string }> }
  exclusif: { jours: number | null; ratio: number | null; n: number }
  simple: { jours: number | null; ratio: number | null; n: number }
  notaires: Array<{ cle: string; nom: string; actes: number; delai: number | null; retard: number; avecDate: number; enCours: number; depasses: number }>
}

// `enCours` : les chaînes que le registre dit en compromis aujourd'hui. Le registre des transactions garde des
// compromis « actifs » sans acte rattaché que le registre ne compte plus (124 contre 87 le 03/11) : on s'aligne sur lui.
export function calculerAffairesPlus(source: PilotageAffairesPlus, annee: number, agence: string | null, enCours: Set<number> | null = null): AffairesPlusCalcul {
  const garde = (a: string | null) => !agence || cleAgence(a) === agence
  const offres = source.offres.filter((o) => o.d.startsWith(String(annee)) && garde(o.agence))
  const comparable = (o: PilotageAffairesPlus['offres'][number]) => o.state === 'accepted' && o.ratio != null && o.ratio >= 0.5 && o.ratio <= 1.2
  const acceptees = offres.filter(comparable).map((o) => Number(o.ratio))
  const tranche = (min: number, max: number) => acceptees.filter((r) => r >= min && r < max).length
  const parType = (type: string) => {
    const premieres = offres.filter((o) => o.premiere && o.type === type && o.jours != null && o.jours >= 0)
    return {
      jours: mediane(premieres.map((o) => Number(o.jours))),
      ratio: mediane(offres.filter((o) => o.type === type && comparable(o)).map((o) => Number(o.ratio))),
      n: premieres.length,
    }
  }
  // Les notaires : actes de l'année ET de la précédente (une étude fait peu d'actes par an), à partir de 5.
  const etudes = new Map<string, { cle: string; nom: string; delais: number[]; retard: number; avecDate: number; actes: number; enCours: number; depasses: number }>()
  for (const a of source.actes) {
    if (!a.d.startsWith(String(annee - 1)) && !a.d.startsWith(String(annee))) continue
    if (!garde(a.agence) || !a.etude) continue
    const cle = a.etude_id ?? a.etude
    const e = etudes.get(cle) ?? { cle, nom: a.etude, delais: [], retard: 0, avecDate: 0, actes: 0, enCours: 0, depasses: 0 }
    e.nom = a.etude
    e.actes += 1
    if (a.delai != null && a.delai >= 0) e.delais.push(a.delai)
    if (a.retard != null) { e.avecDate += 1; if (a.retard) e.retard += 1 }
    etudes.set(cle, e)
  }
  // Les compromis en cours de chaque étude : le nom de la vente est gardé quand l'étude en a une (il nomme l'étude,
  // celui de la fiche contact nomme souvent le seul notaire).
  const jour = aujourdhui()
  for (const c of source.compromis ?? []) {
    if (!garde(c.agence) || !c.etude) continue
    if (enCours && (c.app_chaine_id == null || !enCours.has(c.app_chaine_id))) continue
    const cle = c.etude_id ?? c.etude
    const e = etudes.get(cle) ?? { cle, nom: c.etude, delais: [], retard: 0, avecDate: 0, actes: 0, enCours: 0, depasses: 0 }
    e.enCours += 1
    if (c.prevue && /^\d{4}-\d{2}-\d{2}$/.test(c.prevue) && c.prevue < jour) e.depasses += 1
    etudes.set(cle, e)
  }
  return {
    remises: {
      n: acceptees.length, mediane: mediane(acceptees),
      tranches: [
        { libelle: 'Au prix (98 % et plus)', n: acceptees.filter((r) => r >= 0.98).length, ton: '#1a9a6c' },
        { libelle: '95 à 98 %', n: tranche(0.95, 0.98), ton: '#7fc4a5' },
        { libelle: '90 à 95 %', n: tranche(0.9, 0.95), ton: '#d98a00' },
        { libelle: '85 à 90 %', n: tranche(0.85, 0.9), ton: '#e0603a' },
        { libelle: 'Moins de 85 %', n: acceptees.filter((r) => r < 0.85).length, ton: '#a02e1f' },
      ],
    },
    exclusif: parType('EXCLUSIF'), simple: parType('SIMPLE'),
    notaires: [...etudes.values()].filter((e) => e.actes >= 5 || e.enCours >= 3 || e.depasses > 0)
      .map((e) => ({ cle: e.cle, nom: e.nom, actes: e.actes, delai: mediane(e.delais), retard: e.retard, avecDate: e.avecDate, enCours: e.enCours, depasses: e.depasses }))
      .sort((a, b) => b.depasses - a.depasses || b.enCours - a.enCours || b.actes - a.actes),
  }
}

function mockAcquereurs(): PilotageAcquereurs {
  return {
    total: 4200, vivantes: 2400, crees: 420, crees_prec: 390, touchees90: 210, sans_nego: 120, sans_contact: 300,
    qualite: { tel: 1650, mail: 1600, recherche: 1050, type: 1040, budget: 1000, secteur: 900, taille: 820 },
    vivier: [2400, 1050, 860, 740, 700],
    conversion: { fiches: 1100, avec_offre: 130, acheteurs: 112, delai_median: 18, sous30: 88 },
    budgets: [{ tranche: 1, n: 260 }, { tranche: 2, n: 210 }, { tranche: 3, n: 160 }, { tranche: 4, n: 230 }, { tranche: 5, n: 140 }],
    negos: ['Mélanie LEGRAND', 'Nadege PEYRARD', 'Christèle GENTES', 'Sandrine DELAVAUD', 'Claire RIBBES', 'Nicolas COUDERT'].map((nom, i) => ({
      nom, crees: 90 - i * 12, crees_prec: 80 - i * 9, vivantes: 400 - i * 40, avec_rech: 220 - i * 25, completes: 180 - i * 22, joignables: 300 - i * 30, touchees90: 40 - i * 5,
    })),
  }
}

function mockAffairesPlus(annee: number): PilotageAffairesPlus {
  const r = hasard(annee * 7)
  const agences = ['Ambert', 'Le Puy-en-Velay', 'Annonay', 'Craponne-sur-Arzon', 'Yssingeaux', 'Courpière']
  const offres = Array.from({ length: 260 }, (_, i) => ({
    d: `${annee - (i % 3 === 0 ? 1 : 0)}-${String(1 + (i % 10)).padStart(2, '0')}-1${i % 9}`,
    state: r() < 0.8 ? 'accepted' : 'refused', agence: agences[i % agences.length], type: r() < 0.4 ? 'EXCLUSIF' : 'SIMPLE',
    ratio: Math.round((0.82 + r() * 0.2) * 1000) / 1000, jours: Math.round(20 + r() * 160), premiere: r() < 0.7,
  }))
  const etudes = ['Office notarial des Pays de Craponne', 'Office notarial de Dunières', 'Office notarial St-Etienne', 'SCP ROYET et DIDIER']
  const actes = Array.from({ length: 120 }, (_, i) => ({
    d: `${annee}-${String(1 + (i % 10)).padStart(2, '0')}-0${1 + (i % 8)}`, agence: agences[i % agences.length],
    etude_id: String(i % 4), etude: etudes[i % 4], delai: Math.round(70 + r() * 60), retard: r() < 0.3,
  }))
  const compromis = Array.from({ length: 30 }, (_, i) => ({
    d: `${annee}-0${1 + (i % 9)}-10`, prevue: `${annee}-${String(9 + (i % 4)).padStart(2, '0')}-15`, agence: agences[i % agences.length],
    etude_id: String(i % 4), etude: etudes[i % 4], app_chaine_id: 900000 + i,
  }))
  return { offres, actes, compromis }
}

// ───────────────────────────── le pilotage PAR NÉGOCIATEUR (04/11) ─────────────────────────────
// notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md §40-40 ter. Un négociateur a DEUX numéros chez Hektor : sa fiche
// NÉGOCIATEUR (stock, mandats, contacts — Claire RIBBES = 15) et son compte UTILISATEUR (répartition des honoraires —
// Claire RIBBES = 39) ; et une personne a souvent UNE fiche par agence (Marion BILLIG DURAND : 52, 39, 89). L'annuaire
// relie tout : la PERSONNE = les fiches de l'annuaire au même e-mail (à défaut au même nom). Une ligne se rattache par son
// NUMÉRO ; par sécurité (Frédéric, 04/11), son nom est contrôlé, et sert de repli quand le numéro manque.
//   . une vente répartie compte pour lui avec SA PART : honoraires × somme de ses pourcentages / 100 ;
//   . une vente sans répartition, une offre, un compromis : le négociateur du bien (e-mail du registre) ;
//   . mandats, stock, signatures : le négociateur du mandat ou du bien ; diffusion : par le stock filtré ;
//   . prix obtenu, notaires : le négociateur que la base rend sur chaque ligne ; acquéreurs : lecture à part.
export type PilotageNegociateur = { nego: string; user: string | null; nom: string; email: string | null; agence: string | null; actif: boolean }
export type Personne = { cle: string; nom: string; actif: boolean; type?: string; negos: Set<string>; users: Set<string>; emails: Set<string>; noms: Set<string> }
export type RepereNegos = { source: 'registre' | 'annuaire'; personnes: Map<string, Personne>; parNego: Map<string, string>; parUser: Map<string, string>; parEmail: Map<string, string>; parNom: Map<string, string> }
/** Ce que le filtre a fait, pour le dire à l'écran : lignes rattachées par le numéro, par le nom (sans numéro), et les
 *  désaccords — son numéro mais un autre nom, ou son nom mais le numéro d'un autre. */
export type ControleNego = { parNumero: number; parNom: number; nomDifferent: number; autreNumero: number }

const cleEmail = (email: string | null | undefined) => String(email ?? '').trim().toLowerCase()
const cleNomSur = (nom: string | null | undefined) => (String(nom ?? '').trim() ? cleNom(String(nom)) : '')

export function construireRepere(annuaire: PilotageNegociateur[]): RepereNegos {
  const repere: RepereNegos = { source: 'annuaire', personnes: new Map(), parNego: new Map(), parUser: new Map(), parEmail: new Map(), parNom: new Map() }
  // Les fiches avec e-mail d'abord (l'e-mail regroupe les fiches d'une même personne), les actives en tête (nom affiché).
  const lignes = [...annuaire].sort((a, b) => Number(!cleEmail(a.email)) - Number(!cleEmail(b.email)) || Number(b.actif) - Number(a.actif))
  for (const l of lignes) {
    const email = cleEmail(l.email)
    const nom = cleNomSur(l.nom)
    const cle = (email && repere.parEmail.get(email)) || (nom && repere.parNom.get(nom)) || `p:${email || nom || `n${l.nego}`}`
    const p = repere.personnes.get(cle) ?? { cle, nom: nomPersonne(l.nom), actif: false, negos: new Set<string>(), users: new Set<string>(), emails: new Set<string>(), noms: new Set<string>() }
    p.actif = p.actif || l.actif
    p.negos.add(l.nego); repere.parNego.set(l.nego, cle)
    if (l.user) { p.users.add(l.user); repere.parUser.set(l.user, cle) }
    if (email) { p.emails.add(email); repere.parEmail.set(email, cle) }
    if (nom) { p.noms.add(nom); if (!repere.parNom.has(nom)) repere.parNom.set(nom, cle) }
    repere.personnes.set(cle, p)
  }
  return repere
}

/** Le repère tiré du REGISTRE : la personne est celle du registre (rattachement fixe, décidé une fois), avec tous ses
 *  numéros. L'e-mail de la personne passe avant celui de ses fiches (une boîte partagée ne déplace personne). */
export function construireRepereDepuisRegistre(registre: PilotageRegistre): RepereNegos {
  const repere: RepereNegos = { source: 'registre', personnes: new Map(), parNego: new Map(), parUser: new Map(), parEmail: new Map(), parNom: new Map() }
  const parId = new Map<number, Personne>()
  for (const p of registre.personnes) {
    const cle = `r:${p.id}`
    const personne: Personne = { cle, nom: nomPersonne(p.nom), actif: p.actif, type: p.type, negos: new Set(), users: new Set(), emails: new Set(), noms: new Set() }
    const nom = cleNomSur(p.nom)
    if (nom) { personne.noms.add(nom); if (!repere.parNom.has(nom)) repere.parNom.set(nom, cle) }
    const email = cleEmail(p.email)
    if (email) { personne.emails.add(email); repere.parEmail.set(email, cle) }
    repere.personnes.set(cle, personne)
    parId.set(p.id, personne)
  }
  for (const f of registre.fiches) {
    const personne = parId.get(f.personne)
    if (!personne) continue
    if (f.nego) { personne.negos.add(f.nego); repere.parNego.set(f.nego, personne.cle) }
    if (f.user) { personne.users.add(f.user); repere.parUser.set(f.user, personne.cle) }
    const email = cleEmail(f.email)
    if (email) { personne.emails.add(email); if (!repere.parEmail.has(email)) repere.parEmail.set(email, personne.cle) }
    const nom = cleNomSur(f.nom)
    if (nom) { personne.noms.add(nom); if (!repere.parNom.has(nom)) repere.parNom.set(nom, personne.cle) }
  }
  return repere
}

type Numero = { nego?: string | null; user?: string | null; email?: string | null }
function rattacher(repere: RepereNegos, numero: Numero, nom: string | null | undefined) {
  const n = cleNomSur(nom)
  const parNumero = (numero.nego && repere.parNego.get(String(numero.nego).trim()))
    || (numero.user && repere.parUser.get(String(numero.user).trim()))
    || (numero.email && repere.parEmail.get(cleEmail(numero.email))) || null
  if (parNumero) return { cle: parNumero, par: 'numero' as const, nom: n, nomOk: !n || (repere.personnes.get(parNumero)?.noms.has(n) ?? false) }
  return { cle: n ? repere.parNom.get(n) ?? null : null, par: 'nom' as const, nom: n, nomOk: true }
}

/** Les personnes qui ont au moins une ligne dans les sources (dans l'agence choisie, si elle l'est), par nom. */
export function personnesPresentes(sources: PilotageSources, repere: RepereNegos, agence: string | null): Personne[] {
  const vues = new Set<string>()
  const garde = (ag: string | null | undefined) => !agence || cleAgence(ag) === agence
  const noter = (numero: Numero, nom: string | null | undefined) => { const r = rattacher(repere, numero, nom); if (r.cle) vues.add(r.cle) }
  if (!(sources.stock instanceof Error)) for (const s of sources.stock) if (garde(s.agence_nom)) noter({ nego: s.commercial_id }, s.commercial_nom)
  if (!(sources.mandats instanceof Error)) for (const m of sources.mandats) if (garde(m.agence)) noter({ nego: m.negoId }, m.nego)
  if (!(sources.ventes instanceof Error)) {
    for (const [lignes, rep] of [[sources.ventes.n, sources.ventes.repN], [sources.ventes.p, sources.ventes.repP]] as const) {
      for (const l of lignes) {
        if (!garde(l.agence_nom)) continue
        const lr = rep.get(String(l.app_chaine_id)) ?? []
        if (lr.length) for (const x of lr) noter({ user: x.hektorUserId }, x.nomAuMoment)
        else noter({ email: l.negociateur_email }, null)
      }
    }
  }
  return [...vues].map((cle) => repere.personnes.get(cle) as Personne)
    .filter((p) => p && !/supprim/i.test(p.nom))
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'))
}

/** Les sources réduites à une personne. Les calculs des onglets ne changent pas : ils reçoivent moins de lignes. */
export function filtrerParPersonne(sources: PilotageSources, repere: RepereNegos, cle: string): { sources: PilotageSources; controle: ControleNego } {
  const controle: ControleNego = { parNumero: 0, parNom: 0, nomDifferent: 0, autreNumero: 0 }
  const moi = repere.personnes.get(cle)
  const est = (numero: Numero, nom: string | null | undefined) => {
    const r = rattacher(repere, numero, nom)
    if (r.cle === cle) {
      if (r.par === 'numero') { controle.parNumero += 1; if (!r.nomOk) controle.nomDifferent += 1 } else controle.parNom += 1
      return true
    }
    if (r.par === 'numero' && r.nom && moi?.noms.has(r.nom)) controle.autreNumero += 1
    return false
  }

  let ventes = sources.ventes
  if (!(ventes instanceof Error)) {
    const reduire = (lignes: RegistreDossierRow[], rep: Map<string, RepartitionLigne[]>) => {
      const sortie: RegistreDossierRow[] = []
      const repSortie = new Map<string, RepartitionLigne[]>()
      for (const l of lignes) {
        const lr = rep.get(String(l.app_chaine_id)) ?? []
        if (lr.length) {
          const miennes = lr.filter((x) => est({ user: x.hektorUserId }, x.nomAuMoment))
          if (!miennes.length) continue
          const part = miennes.reduce((t, x) => t + x.pourcentage, 0) / 100
          const fois = (v: number | null) => (v == null ? null : v * part)
          sortie.push({ ...l, honoraires: fois(l.honoraires), honoraires_entree: fois(l.honoraires_entree), honoraires_sortie: fois(l.honoraires_sortie) })
          repSortie.set(String(l.app_chaine_id), miennes)
        } else if (est({ email: l.negociateur_email }, null)) sortie.push(l)
      }
      return { lignes: sortie, rep: repSortie }
    }
    const n = reduire(ventes.n, ventes.repN)
    const p = reduire(ventes.p, ventes.repP)
    ventes = { n: n.lignes, p: p.lignes, repN: n.rep, repP: p.rep }
  }

  const mandats = sources.mandats instanceof Error ? sources.mandats : sources.mandats.filter((m) => est({ nego: m.negoId }, m.nego))
  const stock = sources.stock instanceof Error ? sources.stock : sources.stock.filter((s) => est({ nego: s.commercial_id }, s.commercial_nom))

  // Signatures : le négociateur du bien, retrouvé par le mandat (ou le stock) de la même annonce.
  let signatures = sources.signatures
  if (!(signatures instanceof Error)) {
    const parAnnonce = new Map<number, { nego: string | null; nom: string | null }>()
    if (!(sources.mandats instanceof Error)) for (const m of sources.mandats) if (m.annonce != null) parAnnonce.set(m.annonce, { nego: m.negoId, nom: m.nego })
    if (!(sources.stock instanceof Error)) for (const s of sources.stock) if (s.hektor_annonce_id != null) parAnnonce.set(s.hektor_annonce_id, { nego: s.commercial_id, nom: s.commercial_nom })
    signatures = signatures.filter((x) => { const q = x.annonce != null ? parAnnonce.get(x.annonce) : undefined; return q ? est({ nego: q.nego }, q.nom) : false })
  }

  let affairesPlus = sources.affairesPlus
  if (!(affairesPlus instanceof Error)) {
    const garde = (x: { nego?: string | null; nego_nom?: string | null }) => est({ nego: x.nego }, x.nego_nom)
    affairesPlus = { offres: affairesPlus.offres.filter(garde), actes: affairesPlus.actes.filter(garde), compromis: (affairesPlus.compromis ?? []).filter(garde) }
  }

  return { sources: { ...sources, ventes, mandats, stock, signatures, affairesPlus }, controle }
}
