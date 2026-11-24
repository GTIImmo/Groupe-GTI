// RECRUTEMENT R6 (24/11/2026) — les lectures et les gestes de l'écran Recrutement.
// Chantier à part : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md, §14 (R6, conception écrite
// avant de coder) ; maquettes validées : notice/maquettes_recrutement/ ; base : supabase/patch_recrutement_ecran_2026-11-24.sql.
// ⛔ Rien ne part chez Hektor. Tout passe par les fonctions public.rec_* (administrateurs seuls, sinon 42501).
// ⛔ Les coordonnées affichées sont celles que les réseaux montrent EN CLAIR (règle du 20/11, note §9-§10).
// En local sans base (mode maquette), un petit vivier FICTIF tient lieu de base : noms et numéros inventés.
import { hasSupabaseEnv, supabase } from './supabase'

export type Statut = 'pas_interesse' | 'a_verifier' | 'a_trancher'

export type Candidat = {
  reseau: string
  identifiant: string
  origine: 'collecte' | 'saisie'
  prenom: string | null
  nom: string | null
  fonction: string | null
  agence: string | null
  commune: string | null
  code_postal: string | null
  departement: string | null
  lat: number | null
  lon: number | null
  agence_gti_proche: string | null
  distance_km: number | null
  telephone: string | null
  email: string | null
  siren: string | null
  nb_annonces: number | null
  nb_avis: number | null
  note_avis: number | null
  distinction: string | null
  desactive: boolean
  etat_suivi: string | null
  etat_depuis: string | null
  motif_depart: string | null
  premiere_vue: string | null
  url: string | null
  entreprise_creee_le: string | null
  entreprise_etat: 'A' | 'C' | null
  opposition: boolean
  etape: number
  statut: Statut | null
  reprise_le: string | null
  prochaine_action: string | null
  prochaine_le: string | null
  suivi_par: string | null
  archive: boolean
  corrige: boolean
}

export type AgenceGti = { nom: string; departement: string; lat: number; lon: number }

export type EtatCollecte = {
  collecte: { numero: number; debut: string; fin: string | null; etat: string; note: string | null } | null
  sources: Array<{ reseau: string; vus: number | null; precedent: number | null; sante: 'premiere' | 'saine' | 'malade'; raison: string | null }>
  fiches: number
  par_etat: Record<string, number>
}

export type Vivier = { etat: EtatCollecte | null; agences: AgenceGti[]; candidats: Candidat[] }

export type Evenement = {
  id: number
  quand: string
  type: 'appel' | 'note' | 'email' | 'rdv' | 'etape' | 'correction' | 'ajout' | 'retrait' | 'info'
  resultat: 'messagerie' | 'pas_disponible' | 'interesse' | 'pas_interesse' | null
  texte: string | null
  rdv_le: string | null
  par: string | null
}

export type FicheBrute = {
  reseau: string; identifiant: string; origine: 'collecte' | 'saisie'; url: string | null
  prenom: string | null; nom: string | null; fonction: string | null; agence: string | null
  commune: string | null; code_postal: string | null; departement: string | null
  telephone: string | null; email: string | null; source_contact: string | null
  siren: string | null; rsac_ville: string | null; premiere_vue: string | null; derniere_vue: string | null
  nb_annonces: number | null; nb_avis: number | null; note_avis: number | null
}

export type Detail = {
  fiche: FicheBrute
  entreprise: { siren: string; trouve: boolean | null; date_creation: string | null; etat: 'A' | 'C' | null; siege_commune: string | null; opposition: boolean } | null
  suivi: {
    etape: number; statut: Statut | null; reprise_le: string | null; info_donnee_le: string | null
    prochaine_action: string | null; prochaine_le: string | null; suivi_par: string | null
    agence_envisagee: string | null; archive: boolean; archive_le: string | null
  } | null
  carnet: Array<{ champ: string; valeur: string | null; le: string; par: string | null }>
  fil: Evenement[]
  autres: Array<{ reseau: string; identifiant: string; url: string | null; etat_suivi: string | null }>
  suivi_par_nom: string | null
}

export type ChampCorrigeable = 'prenom' | 'nom' | 'telephone' | 'email' | 'commune' | 'code_postal' | 'fonction' | 'agence'
export type ChampsSuivi = Partial<{
  statut: Statut | null; reprise_le: string | null; prochaine_action: string | null; prochaine_le: string | null
  suivi_par: string | null; agence_envisagee: string | null; archive: boolean; info_donnee: boolean
}>
export type NiveauRetrait = 'archiver' | 'ne_plus_contacter' | 'effacer'

export const ETAPES = ['Repérée', 'Contactée', 'Rendez-vous', 'Proposition', 'Contrat signé', 'Accès ouvert'] as const

// Les mêmes noms que le collecteur (recrutement/collecte_annuaires.py, NOMS_RESEAUX).
export const NOMS_RESEAUX: Record<string, string> = {
  iad: 'iad', safti: 'SAFTI', kw: 'Keller Williams', registre: 'Indépendant (registre)', orpi: 'Orpi', laforet: 'Laforêt',
  c21: 'Century 21', '42avenue': '42ème Avenue', manufacture: 'La Manufacture de l’Immo', capifrance: 'Capifrance',
  optimhome: 'Optimhome', bsk: 'BSK Immobilier', megagence: 'Megagence', expertimo: 'Expertimo', drhouse: 'Dr House Immo',
  '3g': '3G Immo', lfimmo: 'LF immo', sextant: 'Sextant', cotepart: 'Côté Particuliers', exp: 'eXp France',
  groupement: 'Groupement Immobilier', immodiffusion: 'Immo-Diffusion', lucarne: 'La Lucarne de l’immobilier',
  liberkeys: 'Liberkeys', maxihome: 'Maxihome', saisie: 'Ajouté à la main',
}
export const nomReseau = (cle: string) => NOMS_RESEAUX[cle] ?? cle

// Ce que dit la source quand une coordonnée manque (repris du collecteur, POURQUOI_SANS_CONTACT).
const SANS_CONTACT: Record<string, string> = {
  iad: 'numéro derrière un clic', kw: 'e-mail par formulaire', registre: 'aucune coordonnée publique',
  laforet: 'aucun contact personnel publié', c21: 'aucun contact personnel publié', '42avenue': 'e-mail par formulaire',
  orpi: 'e-mail par formulaire', megagence: 'e-mail par formulaire', sextant: 'e-mail par formulaire',
  '3g': 'e-mail non affiché', immodiffusion: 'pas d’e-mail publié', lucarne: 'pas d’e-mail publié',
}
export function pourquoiSansContact(c: Pick<Candidat, 'reseau' | 'telephone' | 'email'>): string {
  if (c.telephone && c.email) return ''
  if (SANS_CONTACT[c.reseau]) return SANS_CONTACT[c.reseau]
  if (!c.telephone && !c.email) return 'rien d’affiché sur la page'
  return c.telephone ? 'pas d’e-mail affiché' : 'pas de téléphone affiché'
}

export function distanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const r = (x: number) => (x * Math.PI) / 180
  const a = Math.sin(r(lat2 - lat1) / 2) ** 2 + Math.cos(r(lat1)) * Math.cos(r(lat2)) * Math.sin(r(lon2 - lon1) / 2) ** 2
  return 6371 * 2 * Math.asin(Math.min(1, Math.sqrt(a)))
}

export const nomComplet = (c: { prenom: string | null; nom: string | null }) =>
  [c.prenom, c.nom].map((x) => (x ?? '').trim()).filter(Boolean).join(' ') || 'Sans nom'

// Le prochain passage de la tâche « GTI Recrutement » : le 1er dimanche de décembre, février, avril, juin, août, octobre.
export function prochaineRelecture(depuis = new Date()): Date {
  for (let i = 0; i < 14; i += 1) {
    const mois = new Date(depuis.getFullYear(), depuis.getMonth() + i, 1, 10)
    if (mois.getMonth() % 2 !== 1) continue           // déc = 11, fév = 1, avr = 3… : les mois impairs en JS
    while (mois.getDay() !== 0) mois.setDate(mois.getDate() + 1)
    if (mois > depuis) return mois
  }
  return depuis
}

function erreurLisible(error: { message?: string; code?: string } | null): Error {
  if (error?.code === '42501') return new Error('Réservé aux administrateurs.')
  return new Error(error?.message || 'La base n’a pas répondu.')
}

async function appeler<T>(fonction: string, params?: Record<string, unknown>): Promise<T> {
  if (!supabase) throw new Error('Pas de base.')
  const { data, error } = await supabase.rpc(fonction, params ?? {})
  if (error) throw erreurLisible(error)
  return data as T
}

const enLocal = () => !hasSupabaseEnv || !supabase

// ─── les lectures ───

export async function lireVivier(): Promise<Vivier> {
  if (enLocal()) return demoVivier()
  const brut = await appeler<Vivier>('rec_candidats')
  return {
    etat: brut?.etat ?? null,
    agences: Array.isArray(brut?.agences) ? brut.agences : [],
    candidats: Array.isArray(brut?.candidats) ? brut.candidats.map((c) => ({ ...c, distance_km: c.distance_km == null ? null : Number(c.distance_km) })) : [],
  }
}

export async function lireCandidat(reseau: string, identifiant: string): Promise<Detail> {
  if (enLocal()) return demoDetail(reseau, identifiant)
  const d = await appeler<Detail>('rec_candidat', { p_reseau: reseau, p_identifiant: identifiant })
  return { ...d, carnet: d.carnet ?? [], fil: d.fil ?? [], autres: d.autres ?? [] }
}

export type Doublons = { sur_liste_noire: boolean; fiches: Array<{ reseau: string; identifiant: string; prenom: string | null; nom: string | null; commune: string | null }> }
export async function chercherDoublons(p: { prenom: string; nom: string; telephone: string; email: string; siren: string; departement: string }): Promise<Doublons> {
  if (enLocal()) {
    const cle = `${p.prenom} ${p.nom}`.trim().toLowerCase()
    return { sur_liste_noire: false, fiches: DEMO.candidats.filter((c) => cle.length > 2 && nomComplet(c).toLowerCase() === cle).map((c) => ({ reseau: c.reseau, identifiant: c.identifiant, prenom: c.prenom, nom: c.nom, commune: c.commune })) }
  }
  return appeler<Doublons>('rec_doublons', { p_prenom: p.prenom, p_nom: p.nom, p_telephone: p.telephone, p_email: p.email, p_siren: p.siren, p_departement: p.departement })
}

// ─── les gestes ───

export async function noter(reseau: string, identifiant: string, type: 'appel' | 'note' | 'email' | 'rdv', texte: string, resultat?: Evenement['resultat'], rdvLe?: string | null): Promise<void> {
  if (enLocal()) return demoNoter(reseau, identifiant, type, texte, resultat ?? null, rdvLe ?? null)
  await appeler('rec_noter', { p_reseau: reseau, p_identifiant: identifiant, p_type: type, p_texte: texte, p_resultat: resultat ?? null, p_rdv_le: rdvLe ?? null })
}

export async function marquerEtape(reseau: string, identifiant: string, etape: number): Promise<void> {
  if (enLocal()) return demoEtape(reseau, identifiant, etape)
  await appeler('rec_etape', { p_reseau: reseau, p_identifiant: identifiant, p_etape: etape })
}

export async function majSuivi(reseau: string, identifiant: string, champs: ChampsSuivi): Promise<void> {
  if (enLocal()) return demoSuivi(reseau, identifiant, champs)
  await appeler('rec_suivi_maj', { p_reseau: reseau, p_identifiant: identifiant, p_champs: champs })
}

export async function corriger(reseau: string, identifiant: string, champ: ChampCorrigeable, valeur: string | null, revenir = false): Promise<void> {
  if (enLocal()) return demoCorriger(reseau, identifiant, champ, valeur, revenir)
  await appeler('rec_corriger', { p_reseau: reseau, p_identifiant: identifiant, p_champ: champ, p_valeur: valeur, p_revenir: revenir })
}

export type NouveauCandidat = {
  prenom: string; nom: string; fonction: string; agence: string; commune: string; code_postal: string; departement: string
  lat: number | null; lon: number | null; agence_gti_proche: string; distance_km: number | null
  telephone: string; email: string; source_contact: string; siren: string; etape: number; agence_envisagee: string
}
export async function ajouterCandidat(p: NouveauCandidat): Promise<{ reseau: string; identifiant: string }> {
  if (enLocal()) return demoAjouter(p)
  return appeler<{ reseau: string; identifiant: string }>('rec_ajouter', { p })
}

export async function retirerCandidat(reseau: string, identifiant: string, niveau: NiveauRetrait, qui: 'elle_meme' | 'notre_decision', demandeLe: string): Promise<{ niveau: string; fiches_effacees: number }> {
  if (enLocal()) return demoRetirer(reseau, identifiant, niveau)
  return appeler('rec_retirer', { p_reseau: reseau, p_identifiant: identifiant, p_niveau: niveau, p_qui: qui, p_demande_le: demandeLe })
}

// Les communes qui commencent par ce nom, dans nos quatre départements, avec leur centre (geo.api.gouv.fr, CORS
// ouvert, le service que l'app utilise déjà). Best-effort : une panne rend une liste vide, la saisie continue.
export type Commune = { nom: string; codePostal: string; departement: string; lat: number; lon: number }
export async function chercherCommunes(texte: string): Promise<Commune[]> {
  const q = texte.trim()
  if (q.length < 2) return []
  const parCp = /^\d{5}$/.test(q)
  const url = parCp
    ? `https://geo.api.gouv.fr/communes?codePostal=${q}&fields=nom,codesPostaux,codeDepartement,centre&format=json`
    : `https://geo.api.gouv.fr/communes?nom=${encodeURIComponent(q)}&fields=nom,codesPostaux,codeDepartement,centre&boost=population&limit=12&format=json`
  try {
    const lignes = (await fetch(url).then((r) => (r.ok ? r.json() : []))) as Array<{ nom?: string; codesPostaux?: string[]; codeDepartement?: string; centre?: { coordinates?: [number, number] } }>
    return (Array.isArray(lignes) ? lignes : [])
      .filter((l) => l.nom && l.centre?.coordinates)
      .map((l) => ({ nom: String(l.nom), codePostal: parCp ? q : (l.codesPostaux?.[0] ?? ''), departement: String(l.codeDepartement ?? ''), lon: l.centre!.coordinates![0], lat: l.centre!.coordinates![1] }))
      .sort((a, b) => Number(!['07', '42', '43', '63'].includes(a.departement)) - Number(!['07', '42', '43', '63'].includes(b.departement)))
      .slice(0, 8)
  } catch {
    return []
  }
}

// ─── le vivier FICTIF du mode local (noms et numéros inventés, comme les maquettes) ───

type Demo = { agences: AgenceGti[]; candidats: Candidat[]; fils: Record<string, Evenement[]>; suivis: Record<string, NonNullable<Detail['suivi']>>; carnets: Record<string, Detail['carnet']> }
const AG_DEMO: AgenceGti[] = [
  ['Saint-Étienne', '42', 45.4397, 4.3872], ['Saint-Just-Saint-Rambert', '42', 45.4997, 4.2411], ['Issoire', '63', 45.5442, 3.2492],
  ['Montbrison', '42', 45.6075, 4.0653], ['Annonay', '07', 45.2397, 4.6708], ['Le Puy-en-Velay', '43', 45.0434, 3.885],
  ['Firminy', '42', 45.3886, 4.2872], ['Courpière', '63', 45.7558, 3.5394], ['Brioude', '43', 45.2942, 3.3842],
  ['Monistrol-sur-Loire', '43', 45.2925, 4.1722], ['Ambert', '63', 45.5497, 3.7417], ['Yssingeaux', '43', 45.1428, 4.1236],
  ['Tence', '43', 45.1142, 4.2906], ['Saint-Bonnet-le-Château', '42', 45.4239, 4.0661], ['Craponne-sur-Arzon', '43', 45.3311, 3.8475],
  ['Saint-Didier-en-Velay', '43', 45.3036, 4.2775], ['Dunières', '43', 45.2153, 4.3442],
].map(([nom, departement, lat, lon]) => ({ nom: String(nom), departement: String(departement), lat: Number(lat), lon: Number(lon) }))

function fictif(i: number, prenom: string, nom: string, reseau: string, commune: string, lat: number, lon: number, autre: Partial<Candidat> = {}): Candidat {
  const proche = AG_DEMO.map((a) => ({ a, d: distanceKm(lat, lon, a.lat, a.lon) })).sort((x, y) => x.d - y.d)[0]
  return {
    reseau, identifiant: `demo-${i}`, origine: 'collecte', prenom, nom, fonction: null, agence: null, commune, code_postal: null,
    departement: '42', lat, lon, agence_gti_proche: proche.a.nom, distance_km: Math.round(proche.d * 10) / 10,
    telephone: null, email: null, siren: null, nb_annonces: null, nb_avis: null, note_avis: null, distinction: null,
    desactive: false, etat_suivi: 'present', etat_depuis: '2026-11-20', motif_depart: null, premiere_vue: '2026-11-20',
    url: 'https://exemple.invalid/fiche', entreprise_creee_le: null, entreprise_etat: null, opposition: false,
    etape: 1, statut: null, reprise_le: null, prochaine_action: null, prochaine_le: null, suivi_par: null, archive: false, corrige: false,
    ...autre,
  }
}

const DEMO: Demo = {
  agences: AG_DEMO,
  candidats: [
    fictif(1, 'Camille', 'Roux', 'safti', 'Saint-Étienne', 45.43, 4.42, { telephone: '06 00 00 00 01', email: 'camille.roux@exemple.invalid', nb_annonces: 17, nb_avis: 28, note_avis: 4.6, distinction: 'Club Excellence', siren: '000000001', entreprise_creee_le: '2016-10-03', entreprise_etat: 'A' }),
    fictif(2, 'Julien', 'Perret', 'iad', 'Saint-Priest-en-Jarez', 45.4747, 4.3767, { nb_annonces: 12, nb_avis: 64, note_avis: 4.9, entreprise_creee_le: '2020-03-01', entreprise_etat: 'A', etape: 2, prochaine_action: 'rappeler', prochaine_le: '2026-11-26' }),
    fictif(3, 'Sophie', 'Marcoux', 'orpi', 'Saint-Étienne', 45.445, 4.38, { fonction: 'Conseillère en transaction', agence: 'Orpi Saint-Étienne Centre', telephone: '04 00 00 00 03', etape: 3, prochaine_action: 'rendez-vous à l’agence', prochaine_le: '2026-11-26' }),
    fictif(4, 'Nadia', 'Belkacem', 'registre', 'Villars', 45.4686, 4.3539, { fonction: 'entrepreneur individuel (68.31Z)', siren: '000000004', entreprise_creee_le: '2023-05-01', entreprise_etat: 'A' }),
    fictif(5, 'Thomas', 'Giraud', 'capifrance', 'La Talaudière', 45.4772, 4.4297, { telephone: '06 00 00 00 05', email: 'thomas.giraud@exemple.invalid', nb_avis: 12, note_avis: 4.8, entreprise_creee_le: '2024-09-01', entreprise_etat: 'A' }),
    fictif(6, 'Lucie', 'Faure', '42avenue', 'Saint-Étienne', 45.435, 4.39, { fonction: 'Agent commercial', telephone: '06 00 00 00 06', entreprise_creee_le: '2022-01-10', entreprise_etat: 'A', etape: 2, statut: 'pas_interesse', reprise_le: '2027-05-01' }),
    fictif(7, 'Marc', 'Chapuis', 'iad', 'Sorbiers', 45.4914, 4.4436, { nb_annonces: 3, nb_avis: 0, entreprise_creee_le: '2014-02-01', entreprise_etat: 'A', opposition: true, statut: 'a_trancher' }),
    fictif(8, 'Inès', 'Morel', 'drhouse', 'Saint-Genest-Lerpt', 45.4486, 4.3375, { telephone: '06 00 00 00 08', email: 'ines.morel@exemple.invalid', nb_avis: 9, note_avis: 5, entreprise_creee_le: '2025-06-01', entreprise_etat: 'A', etat_suivi: 'nouveau' }),
    fictif(9, 'Patrick', 'Vial', 'safti', 'Unieux', 45.405, 4.27, { telephone: '06 00 00 00 09', email: 'patrick.vial@exemple.invalid', nb_annonces: 8, entreprise_creee_le: '2011-04-01', entreprise_etat: 'C', statut: 'a_verifier' }),
    fictif(10, 'Élodie', 'Brun', 'orpi', 'Saint-Just-Saint-Rambert', 45.5, 4.24, { fonction: 'Conseillère en transaction', agence: 'Orpi Saint-Just', telephone: '04 00 00 00 10' }),
    fictif(11, 'Hugo', 'Delmas', 'optimhome', 'Issoire', 45.55, 3.25, { departement: '63', telephone: '06 00 00 00 11', email: 'hugo.delmas@exemple.invalid', nb_avis: 21, note_avis: 4.7, entreprise_creee_le: '2019-06-01', entreprise_etat: 'A', etape: 2, prochaine_action: 'envoyer la plaquette' }),
    fictif(12, 'Claire', 'Bonnefoy', 'laforet', 'Savigneux', 45.6175, 4.0833, { fonction: 'Conseillère immobilier vente', agence: 'Laforêt Montbrison' }),
    fictif(13, 'Anaïs', 'Roche', 'bsk', 'Le Puy-en-Velay', 45.04, 3.89, { departement: '43', telephone: '06 00 00 00 13', email: 'anais.roche@exemple.invalid', nb_annonces: 6, nb_avis: 31, note_avis: 4.9, entreprise_creee_le: '2021-02-01', entreprise_etat: 'A' }),
  ],
  fils: {},
  suivis: {},
  carnets: {},
}

const cleDemo = (reseau: string, identifiant: string) => `${reseau}/${identifiant}`
const trouverDemo = (reseau: string, identifiant: string) => {
  const c = DEMO.candidats.find((x) => x.reseau === reseau && x.identifiant === identifiant)
  if (!c) throw new Error('fiche introuvable')
  return c
}
let idDemo = 100
function evenementDemo(reseau: string, identifiant: string, type: Evenement['type'], texte: string | null, autre: Partial<Evenement> = {}) {
  const cle = cleDemo(reseau, identifiant)
  DEMO.fils[cle] = [{ id: (idDemo += 1), quand: new Date().toISOString(), type, resultat: null, texte, rdv_le: null, par: 'Moi (essai local)', ...autre }, ...(DEMO.fils[cle] ?? [])]
}
function suiviDemo(c: Candidat): NonNullable<Detail['suivi']> {
  const cle = cleDemo(c.reseau, c.identifiant)
  DEMO.suivis[cle] ??= { etape: c.etape, statut: c.statut, reprise_le: c.reprise_le, info_donnee_le: null, prochaine_action: c.prochaine_action, prochaine_le: c.prochaine_le, suivi_par: c.suivi_par, agence_envisagee: null, archive: c.archive, archive_le: null }
  return DEMO.suivis[cle]
}

function demoVivier(): Vivier {
  const n = DEMO.candidats.length
  return {
    etat: { collecte: { numero: 2, debut: '2026-11-24T13:34:00Z', fin: '2026-11-24T16:10:00Z', etat: 'finie', note: null }, sources: [{ reseau: 'kw', vus: 4, precedent: 10, sante: 'malade', raison: 'essai local' }], fiches: n, par_etat: { present: n } },
    agences: DEMO.agences,
    candidats: DEMO.candidats.map((c) => ({ ...c })),
  }
}
function demoDetail(reseau: string, identifiant: string): Detail {
  const c = trouverDemo(reseau, identifiant)
  const cle = cleDemo(reseau, identifiant)
  return {
    fiche: { reseau, identifiant, origine: c.origine, url: c.url, prenom: c.prenom, nom: c.nom, fonction: c.fonction, agence: c.agence, commune: c.commune, code_postal: c.code_postal, departement: c.departement, telephone: c.telephone, email: c.email, source_contact: c.telephone || c.email ? `affiché sur sa fiche ${nomReseau(reseau)}` : null, siren: c.siren, rsac_ville: c.siren ? 'Saint-Étienne' : null, premiere_vue: c.premiere_vue, derniere_vue: '2026-11-24', nb_annonces: c.nb_annonces, nb_avis: c.nb_avis, note_avis: c.note_avis },
    entreprise: c.siren ? { siren: c.siren, trouve: true, date_creation: c.entreprise_creee_le, etat: c.entreprise_etat, siege_commune: c.commune, opposition: c.opposition } : null,
    suivi: suiviDemo(c),
    carnet: DEMO.carnets[cle] ?? [],
    fil: DEMO.fils[cle] ?? [],
    autres: [],
    suivi_par_nom: null,
  }
}
function demoNoter(reseau: string, identifiant: string, type: Evenement['type'], texte: string, resultat: Evenement['resultat'], rdvLe: string | null) {
  const c = trouverDemo(reseau, identifiant)
  evenementDemo(reseau, identifiant, type, texte || null, { resultat, rdv_le: rdvLe })
  if (type === 'appel' && resultat === 'pas_interesse') { c.statut = 'pas_interesse'; suiviDemo(c).statut = 'pas_interesse' }
}
function demoEtape(reseau: string, identifiant: string, etape: number) {
  const c = trouverDemo(reseau, identifiant)
  c.etape = etape
  suiviDemo(c).etape = etape
  evenementDemo(reseau, identifiant, 'etape', etape === 0 ? 'parcours remis à zéro' : `étape : ${ETAPES[etape - 1]}`)
}
function demoSuivi(reseau: string, identifiant: string, champs: ChampsSuivi) {
  const c = trouverDemo(reseau, identifiant)
  const s = suiviDemo(c)
  if ('statut' in champs) { s.statut = champs.statut ?? null; c.statut = s.statut }
  if ('reprise_le' in champs) { s.reprise_le = champs.reprise_le ?? null; c.reprise_le = s.reprise_le }
  if ('prochaine_action' in champs) { s.prochaine_action = champs.prochaine_action?.trim() || null; c.prochaine_action = s.prochaine_action }
  if ('prochaine_le' in champs) { s.prochaine_le = champs.prochaine_le ?? null; c.prochaine_le = s.prochaine_le }
  if ('suivi_par' in champs) { s.suivi_par = champs.suivi_par ?? null; c.suivi_par = s.suivi_par }
  if ('agence_envisagee' in champs) s.agence_envisagee = champs.agence_envisagee ?? null
  if ('info_donnee' in champs) {
    s.info_donnee_le = champs.info_donnee ? new Date().toISOString() : null
    if (champs.info_donnee) evenementDemo(reseau, identifiant, 'info', 'informée de la source de ses coordonnées et de son droit de refus')
  }
  if ('archive' in champs) {
    s.archive = Boolean(champs.archive); c.archive = s.archive; s.archive_le = s.archive ? new Date().toISOString() : null
    evenementDemo(reseau, identifiant, 'retrait', s.archive ? 'retirée de ma liste' : 'remise dans ma liste')
  }
}
function demoCorriger(reseau: string, identifiant: string, champ: ChampCorrigeable, valeur: string | null, revenir: boolean) {
  const c = trouverDemo(reseau, identifiant)
  const cle = cleDemo(reseau, identifiant)
  const carnet = (DEMO.carnets[cle] ??= []).filter((x) => x.champ !== champ)
  if (!revenir) carnet.unshift({ champ, valeur: valeur?.trim() || null, le: new Date().toISOString(), par: 'Moi (essai local)' })
  DEMO.carnets[cle] = carnet
  ;(c as Record<string, unknown>)[champ] = revenir ? (c as Record<string, unknown>)[champ] : (valeur?.trim() || null)
  c.corrige = carnet.length > 0
  evenementDemo(reseau, identifiant, 'correction', revenir ? `${champ} : retour à la valeur de l’annuaire` : `${champ} corrigé`)
}
function demoAjouter(p: NouveauCandidat) {
  const id = `demo-${(idDemo += 1)}`
  DEMO.candidats.unshift({
    ...fictif(idDemo, p.prenom, p.nom, 'saisie', p.commune, p.lat ?? 45.44, p.lon ?? 4.39),
    identifiant: id, origine: 'saisie', fonction: p.fonction || null, agence: p.agence || null, code_postal: p.code_postal || null,
    telephone: p.telephone || null, email: p.email || null, siren: p.siren || null, etape: p.etape, premiere_vue: new Date().toISOString().slice(0, 10), url: null,
  })
  evenementDemo('saisie', id, 'ajout', `ajoutée à la main${p.source_contact ? ` : ${p.source_contact}` : ''}`)
  return { reseau: 'saisie', identifiant: id }
}
function demoRetirer(reseau: string, identifiant: string, niveau: NiveauRetrait) {
  if (niveau === 'archiver') { demoSuivi(reseau, identifiant, { archive: true }); return { niveau, fiches_effacees: 0 } }
  DEMO.candidats = DEMO.candidats.filter((x) => !(x.reseau === reseau && x.identifiant === identifiant))
  return { niveau, fiches_effacees: 1 }
}
