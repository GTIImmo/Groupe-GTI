// GED (12/11/2026, morceau 6) -- CE QUE L'IA A LU dans un document déposé avec l'outil : les types qui ont une fiche de
// lecture, le résumé d'une lecture en une phrase, et la lecture des lectures d'un bien (tables app_ged_lecture /
// app_ged_valeur, écrites par le serveur seul ; patch_ged_m6_lecture_2026-11-12.sql). L'écran LIT, il n'écrit rien ici.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.11.
import { hasSupabaseEnv, supabase } from './supabase'

// Lot 1 : les fiches 1 à 3 de l'étude. Lot 2 (§12.14) : les justificatifs du mandat et de la mise en vente. Lot 3
// (§12.15) : la vente. Lot 4 (§12.16) : le reste. Même liste que FICHES côté serveur (openai_ged_lecture_service.py).
export const FICHES_LUES = new Set([
  'diag.erp', 'diag.dpe', 'diag.dossier',
  'justif.taxe', 'justif.titre', 'copro.carnet', 'copro.appel_fonds', 'copro.arrete_charges',
  'transaction.offre', 'transaction.avant_contrat', 'copro.pv_ag',
  'mandat.vente', 'mandat.avenant', 'mandat.fin', 'transaction.acte', 'transaction.annulation', 'facture.honoraires',
  'diag.electricite', 'diag.gaz', 'diag.amiante', 'diag.plomb', 'diag.termites', 'diag.assainissement', 'diag.surface',
  'copro.reglement',
])

const QUALITE: Record<string, [string, string]> = {
  proprietaire: ['propriétaire', 'propriétaires'], usufruitier: ['usufruitier', 'usufruitiers'],
  nu_proprietaire: ['nu-propriétaire', 'nus-propriétaires'], indivisaire: ['indivisaire', 'indivisaires'],
  heritier: ['héritier', 'héritiers'], donataire: ['donataire', 'donataires'], redevable: ['redevable', 'redevables'],
  vendeur: ['vendeur', 'vendeurs'], acquereur: ['acquéreur', 'acquéreurs'], mandant: ['mandant', 'mandants'],
  autre: ['autre personne', 'autres personnes'],
}
// Lot 4 : les mots des listes fermées, tels que l'écran les dit
const MOTS: Record<string, string> = {
  exclusif: 'exclusif', simple: 'simple', semi_exclusif: 'semi-exclusif', baisse_prix: 'baisse de prix',
  hausse_prix: 'hausse de prix', honoraires: 'honoraires', duree: 'durée', exclusivite: 'exclusivité',
  vendu_ailleurs: 'vendu par ailleurs', retrait_vente: 'retiré de la vente', autre_agence: 'confié à une autre agence',
  acte_authentique: 'acte de vente', attestation: 'attestation de vente', retractation: 'rétractation',
  refus_pret: 'refus de prêt', accord_amiable: 'accord des parties', caducite: 'caducité', desistement: 'désistement',
  sans_anomalie: 'sans anomalie', anomalies: 'anomalies', danger_grave: '⚠ danger grave', absence: 'absence',
  presence: '⚠ présence', sous_le_seuil: 'plomb sous le seuil', au_dessus_du_seuil: '⚠ plomb au-dessus du seuil',
  collectif: 'tout-à-l\'égout', non_collectif: 'assainissement individuel', conforme: 'conforme',
  non_conforme: 'non conforme', travaux_obligatoires: '⚠ travaux obligatoires', absence_installation: '⚠ aucune installation',
  raccorde: 'raccordé', reglement: 'règlement', edd: 'état descriptif', reglement_et_edd: 'règlement et état descriptif',
  modificatif: 'modificatif', habitation: 'habitation', mixte: 'habitation et activités', mandant: 'du mandant',
  agence: 'de l\'agence', acquereur: 'de l\'acquéreur', vendeur: 'du vendeur', les_deux: 'des deux parties',
}
const mot = (x: string | null) => (x ? MOTS[x.replace(' (?)', '')] ?? x : null)
const RAPPORTS = new Set(['diag.electricite', 'diag.gaz', 'diag.amiante', 'diag.plomb', 'diag.termites'])
const NATURE_ACTE: Record<string, string> = {
  vente: 'acte de vente', donation: 'donation', donation_partage: 'donation-partage', attestation_succession: 'attestation après décès',
  notoriete: 'notoriété', partage: 'partage', adjudication: 'adjudication', echange: 'échange', autre: 'acte',
}
const euros = (x: string) => `${x.replace(/^\d+/, (n) => n.replace(/\B(?=(\d{3})+(?!\d))/g, ' '))} €`

// Les personnes lues, COMPTÉES par qualité (« 2 redevables, 1 usufruitier ») : le résumé ne montre jamais un nom.
export function personnesLues(valeurs: ValeurLue[]): string | null {
  const rangs = new Set(valeurs.filter((x) => x.cle === 'personnes.nom' && x.etat !== 'non_vu' && x.valeur).map((x) => x.rang))
  if (!rangs.size) return null
  const parQualite = new Map<string, number>()
  for (const r of rangs) {
    const q = valeurs.find((x) => x.cle === 'personnes.qualite' && x.rang === r && x.etat !== 'non_vu')?.valeur ?? 'autre'
    parQualite.set(q, (parQualite.get(q) ?? 0) + 1)
  }
  return [...parQualite].map(([q, n]) => `${n} ${(QUALITE[q] ?? QUALITE.autre)[n > 1 ? 1 : 0]}`).join(', ')
}

export type ValeurLue = {
  cle: string
  rang: number
  valeur: string | null
  valeur_num: number | null
  valeur_date: string | null
  page: number | null
  etat: 'lu' | 'incertain' | 'non_vu'
}
// `id` (morceau 8) : la lecture d'où vient une valeur proposée à « remplir » (gardée avec la décision)
export type LectureDocument = { id?: string; typeCode: string; etat: 'lu' | 'incomplet' | 'pas_ce_type'; luLe: string | null; valeurs: ValeurLue[] }

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
  } else if (l.typeCode === 'justif.taxe') {
    if (v('annee_imposition')) morceaux.push(`taxe ${v('annee_imposition')}`)
    if (v('montant_total')) morceaux.push(euros(v('montant_total') as string))
    if (v('commune')) morceaux.push(v('commune') as string)
    const p = personnesLues(l.valeurs)
    if (p) morceaux.push(p)
    if (v('plusieurs_biens') === 'oui') morceaux.push('l\'avis porte plusieurs biens')
  } else if (l.typeCode === 'justif.titre') {
    const nature = v('nature_acte')
    if (nature) morceaux.push(NATURE_ACTE[nature.replace(' (?)', '')] ?? nature)
    if (v('date_acte')) morceaux.push(`du ${v('date_acte')}`)
    const p = personnesLues(l.valeurs)
    if (p) morceaux.push(p)
    if (v('commune')) morceaux.push(v('commune') as string)
    const lots = l.valeurs.filter((x) => x.cle === 'lots.numero' && x.etat !== 'non_vu' && x.valeur).map((x) => x.valeur as string)
    if (lots.length) morceaux.push(`lot${lots.length > 1 ? 's' : ''} ${lots.join(', ')}`)
    if (v('extrait_partiel') === 'oui') morceaux.push('extrait partiel')
  } else if (l.typeCode === 'copro.carnet') {
    if (v('sous_type') === 'carnet_entretien') morceaux.push('carnet d\'entretien (rien à relever)')
    if (v('nb_lots_total')) morceaux.push(`${v('nb_lots_total')} lots${v('nb_lots_principaux') ? ` dont ${v('nb_lots_principaux')} principaux` : ''}`)
    if (v('syndic_nom')) morceaux.push(`syndic ${v('syndic_nom')}`)
    else if (v('syndic_type') === 'benevole') morceaux.push('syndic bénévole')
    if (v('procedure') && v('procedure') !== 'aucune') morceaux.push(`⚠ procédure : ${(v('procedure') as string).replace(/_/g, ' ')}`)
    if (v('procedure') === 'aucune') morceaux.push('aucune procédure')
    if (v('date_etablissement')) morceaux.push(`établie le ${v('date_etablissement')}`)
  } else if (l.typeCode === 'copro.appel_fonds' || l.typeCode === 'copro.arrete_charges') {
    if (v('charges_courantes_lot')) morceaux.push(`charges du lot ${euros(v('charges_courantes_lot') as string)} sur l'exercice`)
    if (v('budget_annuel_lot')) morceaux.push(`budget du lot ${euros(v('budget_annuel_lot') as string)} par an`)
    else if (v('provision_budget')) morceaux.push(`provision ${euros(v('provision_budget') as string)}${v('periode') ? ` (${v('periode')})` : ''}`)
    if (v('appel_travaux')) morceaux.push(`travaux appelés ${euros(v('appel_travaux') as string)}`)
    const lots = l.valeurs.filter((x) => x.cle === 'lots.numero' && x.etat !== 'non_vu' && x.valeur).map((x) => x.valeur as string)
    if (lots.length) morceaux.push(`lot${lots.length > 1 ? 's' : ''} ${lots.join(', ')}`)
    if (v('syndic_nom')) morceaux.push(`syndic ${v('syndic_nom')}`)
  } else if (l.typeCode === 'transaction.offre') {
    if (v('montant_offert')) morceaux.push(`offre ${euros(v('montant_offert') as string)}${v('base_prix') === 'net_vendeur' ? ' net vendeur' : v('base_prix') === 'fai' ? ' FAI' : ''}`)
    if (v('date_offre')) morceaux.push(`du ${v('date_offre')}`)
    const reponse: Record<string, string> = { acceptee: 'acceptée', refusee: 'refusée', contre_proposition: 'contre-proposition', non_signee: 'réponse du vendeur non signée' }
    const r = v('acceptation_vendeur')
    if (r) morceaux.push(`${reponse[r.replace(' (?)', '')] ?? r}${v('date_acceptation') ? ` le ${v('date_acceptation')}` : ''}`)
    if (v('condition_pret') === 'oui') morceaux.push('sous condition de prêt')
    const p = personnesLues(l.valeurs)
    if (p) morceaux.push(p)
  } else if (l.typeCode === 'transaction.avant_contrat') {
    if (v('date_signature')) morceaux.push(`signé le ${v('date_signature')}`)
    if (v('prix')) morceaux.push(euros(v('prix') as string))
    if (v('honoraires')) morceaux.push(`honoraires ${euros(v('honoraires') as string)}${v('charge_honoraires') ? ` (${(v('charge_honoraires') as string).replace('les_deux', 'les deux').replace('acquereur', 'acquéreur')})` : ''}`)
    if (v('date_limite_pret')) morceaux.push(`prêt avant le ${v('date_limite_pret')}`)
    if (v('date_reiteration')) morceaux.push(`acte au plus tard le ${v('date_reiteration')}`)
    const p = personnesLues(l.valeurs)
    if (p) morceaux.push(p)
  } else if (l.typeCode === 'copro.pv_ag') {
    if (v('type_piece') === 'convocation') morceaux.push('convocation')
    if (v('date_ag')) morceaux.push(`AG du ${v('date_ag')}`)
    if (v('budget_vote')) morceaux.push(`budget ${euros(v('budget_vote') as string)}`)
    const travaux = l.valeurs.filter((x) => x.cle === 'travaux.objet' && x.etat !== 'non_vu' && x.valeur).map((x) => x.valeur as string)
    if (travaux.length) morceaux.push(`travaux votés : ${travaux.join(', ')}`)
    if (v('procedure') && v('procedure') !== 'aucune') morceaux.push(`⚠ procédure : ${(v('procedure') as string).replace(/_/g, ' ')}`)
    if (v('syndic_nom')) morceaux.push(`syndic ${v('syndic_nom')}`)
  } else if (l.typeCode === 'mandat.vente') {
    if (v('numero_mandat')) morceaux.push(`mandat ${v('numero_mandat')}`)
    if (v('nature')) morceaux.push(mot(v('nature')) as string)
    if (v('date_signature')) morceaux.push(`signé le ${v('date_signature')}`)
    if (v('prix')) morceaux.push(euros(v('prix') as string))
    if (v('honoraires')) morceaux.push(`honoraires ${euros(v('honoraires') as string)}${v('charge_honoraires') ? ` (${(v('charge_honoraires') as string).replace('les_deux', 'les deux').replace('acquereur', 'acquéreur')})` : ''}`)
    const p = personnesLues(l.valeurs)
    if (p) morceaux.push(p)
  } else if (l.typeCode === 'mandat.avenant') {
    if (v('date_avenant')) morceaux.push(`avenant du ${v('date_avenant')}`)
    if (v('numero_mandat')) morceaux.push(`au mandat ${v('numero_mandat')}`)
    if (v('objet')) morceaux.push(mot(v('objet')) as string)
    if (v('nouveau_prix')) morceaux.push(`nouveau prix ${euros(v('nouveau_prix') as string)}`)
    if (v('nouveaux_honoraires')) morceaux.push(`honoraires ${euros(v('nouveaux_honoraires') as string)}`)
    if (v('nouvelle_date_fin')) morceaux.push(`jusqu'au ${v('nouvelle_date_fin')}`)
    const p = personnesLues(l.valeurs)
    if (p) morceaux.push(p)
  } else if (l.typeCode === 'mandat.fin') {
    morceaux.push(`fin du mandat${v('numero_mandat') ? ` ${v('numero_mandat')}` : ''}`)
    if (v('a_l_initiative_de')) morceaux.push(`à l'initiative ${mot(v('a_l_initiative_de'))}`)
    if (v('date_effet')) morceaux.push(`le ${v('date_effet')}`)
    else if (v('date_courrier')) morceaux.push(`courrier du ${v('date_courrier')}`)
    if (v('motif') && v('motif') !== 'autre') morceaux.push(mot(v('motif')) as string)
  } else if (l.typeCode === 'transaction.acte') {
    if (v('nature')) morceaux.push(mot(v('nature')) as string)
    if (v('date_vente')) morceaux.push(`vente du ${v('date_vente')}`)
    if (v('prix')) morceaux.push(euros(v('prix') as string))
    if (v('etude_notariale')) morceaux.push(v('etude_notariale') as string)
    const p = personnesLues(l.valeurs)
    if (p) morceaux.push(p)
  } else if (l.typeCode === 'transaction.annulation') {
    if (v('nature')) morceaux.push(mot(v('nature')) as string)
    if (v('date_document')) morceaux.push(`du ${v('date_document')}`)
    if (v('date_compromis')) morceaux.push(`compromis du ${v('date_compromis')}`)
    if (v('a_l_initiative_de')) morceaux.push(`à l'initiative ${mot(v('a_l_initiative_de'))}`)
    if (v('sequestre_restitue') === 'oui') morceaux.push('séquestre restitué')
  } else if (l.typeCode === 'facture.honoraires') {
    if (v('numero_facture')) morceaux.push(`facture ${v('numero_facture')}`)
    if (v('date_facture')) morceaux.push(`du ${v('date_facture')}`)
    if (v('montant_ttc')) morceaux.push(`${euros(v('montant_ttc') as string)} TTC`)
    if (v('payeur') && v('payeur') !== 'autre') morceaux.push(`payée par ${v('payeur') === 'vendeur' ? 'le vendeur' : "l'acquéreur"}`)
  } else if (RAPPORTS.has(l.typeCode)) {
    if (v('resultat')) morceaux.push(mot(v('resultat')) as string)
    if (v('date_etablissement')) morceaux.push(`établi le ${v('date_etablissement')}`)
    if (v('date_validite')) morceaux.push(`valable jusqu'au ${v('date_validite')}`)
  } else if (l.typeCode === 'diag.assainissement') {
    if (v('type')) morceaux.push(mot(v('type')) as string)
    if (v('conformite')) morceaux.push(mot(v('conformite')) as string)
    if (v('delai_travaux_mois')) morceaux.push(`travaux sous ${v('delai_travaux_mois')} mois`)
    if (v('date_controle')) morceaux.push(`contrôle du ${v('date_controle')}`)
  } else if (l.typeCode === 'diag.surface') {
    if (v('surface_carrez')) morceaux.push(`Carrez ${v('surface_carrez')} m²`)
    if (v('surface_habitable')) morceaux.push(`habitable ${v('surface_habitable')} m²`)
    const lots = l.valeurs.filter((x) => x.cle === 'lots.numero' && x.etat !== 'non_vu' && x.valeur).map((x) => x.valeur as string)
    if (lots.length) morceaux.push(`lot${lots.length > 1 ? 's' : ''} ${lots.join(', ')}`)
    if (v('date_mesurage')) morceaux.push(`mesuré le ${v('date_mesurage')}`)
  } else if (l.typeCode === 'copro.reglement') {
    if (v('sous_type')) morceaux.push(mot(v('sous_type')) as string)
    if (v('date_acte')) morceaux.push(`du ${v('date_acte')}`)
    if (v('nb_lots')) morceaux.push(`${v('nb_lots')} lots`)
    if (v('destination')) morceaux.push(`destination : ${mot(v('destination'))}`)
    if (v('modificatifs_mentionnes') === 'oui') morceaux.push('modificatifs cités')
  }
  if (!morceaux.length) return "L'IA n'a rien pu relever : la lecture est incomplète."
  return `Lu : ${morceaux.join(' · ')}.`
}

// La date de l'état lue (« établie le ») d'un document, en AAAA-MM-JJ, si elle a été vue (lu ou incertain).
export function dateEtatLue(l: LectureDocument | undefined): string | null {
  if (!l || l.etat === 'pas_ce_type') return null
  // seulement les diagnostics : une taxe ou une fiche synthétique a aussi une « date d'établissement »
  const cle = l.typeCode === 'diag.erp' || l.typeCode === 'diag.dpe' ? 'date_etablissement' : null
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
      .select('app_console_document_id, app_ged_lecture(id, type_code, etat, lu_le, app_ged_valeur(cle, rang, valeur, valeur_num, valeur_date, page, etat))')
      .eq('hektor_annonce_id', String(hektorAnnonceId))
      .not('app_console_document_id', 'is', null)
    if (error) return parDocument
    type Ligne = { app_console_document_id: string; app_ged_lecture: Array<{ id: string; type_code: string; etat: LectureDocument['etat']; lu_le: string | null; app_ged_valeur: ValeurLue[] }> | null }
    for (const r of (data ?? []) as unknown as Ligne[]) {
      const lectures = [...(r.app_ged_lecture ?? [])].sort((a, b) => String(b.lu_le).localeCompare(String(a.lu_le)))
      const l = lectures[0]
      if (l) parDocument.set(r.app_console_document_id, { id: l.id, typeCode: l.type_code, etat: l.etat, luLe: l.lu_le, valeurs: l.app_ged_valeur ?? [] })
    }
  } catch {
    // lecture ratée : rien ne casse
  }
  return parDocument
}
