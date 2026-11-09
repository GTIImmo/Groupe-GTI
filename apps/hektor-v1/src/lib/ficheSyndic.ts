// CHANTIER PARTENAIRES · LOT 4, PIÈCE 4.1 (06/11/2026) — LA FICHE SYNDIC REMPLIE, EN LECTURE SEULE. Règles pures (aucun import).
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §27. Maquette : planche « Fiche-Syndic » (fiche-partenaire).
// Sources (aucune écriture) : les liens syndic ↔ bien du registre (`app_partenaire_lien`, role 'syndic', repris de Hektor
// chaque nuit), la fiche du bien (`app_dossiers_current`, sinon les index des archives), le détail du bien
// (`app_dossier_detail_current.detail_payload_json` → `copropriete_json`), et les documents du bien reconnus par leur NOM
// (la GED les rangera plus tard : chantier GED, `notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md`).
// En attendant le regroupement par immeuble (pièce 4.3), une « copropriété » = un de nos biens chez ce syndic.

export type CoproDuBien = {
  lots: number | null            // copropriete_nb_lot
  quotePart: number | null       // copropriete_quote_part (charges annuelles du lot, €)
  fondsTravaux: number | null    // montant_fonds_travaux (€)
  numerosLots: string | null     // copropriete_lot
  procedure: 'aucune' | 'en_cours' | null   // copropriete_statut_syndicat : NOTPROCESS = aucune
  planSauvegarde: boolean | null // copropriete_plan_sauvegarde
}

const texte = (v: unknown) => String(v ?? '').trim()
const nombre = (v: unknown): number | null => {
  const t = texte(v).replace(/\s/g, '').replace(',', '.')
  if (!t) return null
  const n = Number(t)
  return Number.isFinite(n) ? n : null
}
const objet = (v: unknown): Record<string, unknown> | null => {
  if (v && typeof v === 'object' && !Array.isArray(v)) return v as Record<string, unknown>
  if (typeof v === 'string' && v.trim().startsWith('{')) {
    try { const o = JSON.parse(v); return o && typeof o === 'object' && !Array.isArray(o) ? o : null } catch { return null }
  }
  return null
}

// Le détail du bien porte la copropriété sous `copropriete_json` (texte JSON : {titre, props: {clé: {label, value}}}),
// ou sous `detail_raw_json.copropriete`. Rien de lisible = null (on ne fabrique jamais un zéro).
export function lireCopro(detailPayload: unknown): CoproDuBien | null {
  const d = objet(detailPayload)
  if (!d) return null
  const groupe = objet(d.copropriete_json) ?? objet(objet(d.detail_raw_json)?.copropriete)
  const props = objet(groupe?.props)
  if (!props) return null
  const val = (cle: string) => objet(props[cle])?.value
  const statut = texte(val('copropriete_statut_syndicat')).toUpperCase()
  const plan = texte(val('copropriete_plan_sauvegarde')).toUpperCase()
  return {
    lots: nombre(val('copropriete_nb_lot')),
    quotePart: nombre(val('copropriete_quote_part')),
    fondsTravaux: nombre(val('montant_fonds_travaux')),
    numerosLots: texte(val('copropriete_lot')) || null,
    procedure: !statut ? null : statut === 'NOTPROCESS' ? 'aucune' : 'en_cours',
    planSauvegarde: !plan ? null : ['OUI', 'YES', '1', 'TRUE'].includes(plan),
  }
}

// Un document « de copropriété », reconnu par son NOM (accents, espaces et « _ » tolérés). Provisoire : la GED.
const DOC_COPRO = /(pr[eé][\s_-]*[eé]tat|[eé]tat[\s_-]*dat|\bpv\b|pv[\s_-]*(d[\s_'’-]*)?ag|proc[eè]s[\s_-]*verbal|assembl[eé]e|r[eè]glement[\s_-]*(de[\s_-]*)?copro|carnet[\s_-]*d[\s_'’-]*entretien|fiche[\s_-]*synth|appel[\s_-]*de[\s_-]*fonds|copro|syndic|plan[\s_-]*pluri|\bdtg\b|diagnostic[\s_-]*technique[\s_-]*global)/i
export const estDocumentCopro = (nom: string | null | undefined) => DOC_COPRO.test(texte(nom))

const EN_VENTE = new Set(['actif', 'sous offre', 'sous compromis'])
export type BienSyndic = {
  // 09/11 (§28.10) : la CLÉ d'un bien est NOTRE numéro (« h » + numéro Hektor seulement pour un lien qui n'a pas le nôtre).
  cle: string
  appDossierId: number | null
  hektorAnnonceId: string          // '' tant que Hektor n'a pas rendu le sien (ou s'il est coupé)
  titre: string
  ville: string
  statut: string
  enVente: boolean
  mandat: string | null
  photo: string | null
  copro: CoproDuBien | null
  documents: string[]
  // 4.4 (06/11) : pour le message « Demander un document » (adresse lue dans le détail du bien).
  adresse: string | null
  codePostal: string | null
  // Lot 5 (06/11) : pour « Commander un diagnostic » (année lue dans `diagnostiques_json`, « 0 » = inconnue).
  annee: number | null
}
export type VueSyndic = {
  biens: BienSyndic[]
  enVente: number
  quotePartMoyenne: number | null
  avecDocuments: number
}

// Les biens du syndic, triés : en vente d'abord, puis par titre. Un bien inconnu des index (rare) reste montré par son numéro.
// ⚠ On ne SOMME pas les lots : plusieurs de nos biens peuvent être dans le même immeuble (le regroupement vient en 4.3).
// 09/11 (§28.10) : l'app doit marcher Hektor coupé -> tout se rapproche par NOTRE numéro (`app_dossier_id`) d'abord ; le
// numéro Hektor (déjà chez nous) ne sert plus qu'en repli : biens archivés (leurs index n'ont que lui), lien sans le nôtre.
export function construireVueSyndic(input: {
  liens: { hektor_annonce_id: string | number | null; app_dossier_id: string | number | null }[]
  biens: Record<string, unknown>[]
  details: { hektor_annonce_id: string | number | null; app_dossier_id?: string | number | null; detail_payload_json: unknown }[]
  documents: { hektor_annonce_id: string | number | null; app_dossier_id?: string | number | null; document_name: string | null }[]
}): VueSyndic {
  const indexer = <T,>(rangs: T[], cle: (r: T) => unknown) => {
    const m = new Map<string, T>()
    for (const r of rangs) { const k = texte(cle(r)); if (k && !m.has(k)) m.set(k, r) }
    return m
  }
  const bienParDossier = indexer(input.biens, (b) => b.app_dossier_id)
  const bienParAnnonce = indexer(input.biens, (b) => b.hektor_annonce_id)
  const detailParDossier = indexer(input.details, (d) => d.app_dossier_id)
  const detailParAnnonce = indexer(input.details, (d) => d.hektor_annonce_id)
  const docsPar = new Map<string, string[]>()   // clés « d<notre n°> » et « h<n° Hektor> »
  for (const doc of input.documents) {
    if (!estDocumentCopro(doc.document_name)) continue
    const nom = texte(doc.document_name)
    for (const k of [texte(doc.app_dossier_id) && `d${texte(doc.app_dossier_id)}`, texte(doc.hektor_annonce_id) && `h${texte(doc.hektor_annonce_id)}`]) {
      if (!k) continue
      const liste = docsPar.get(k) ?? []
      if (!liste.includes(nom)) liste.push(nom)
      docsPar.set(k, liste)
    }
  }
  const vus = new Set<string>()
  const biens: BienSyndic[] = []
  for (const l of input.liens) {
    const dossierLien = texte(l.app_dossier_id)
    const annonceLien = texte(l.hektor_annonce_id)
    const cle = dossierLien || (annonceLien && `h${annonceLien}`)
    if (!cle || vus.has(cle)) continue
    vus.add(cle)
    const b = (dossierLien && bienParDossier.get(dossierLien)) || (annonceLien && bienParAnnonce.get(annonceLien)) || {}
    const statut = texte(b.statut_annonce)
    const dossier = nombre(b.app_dossier_id ?? l.app_dossier_id)
    const id = texte(b.hektor_annonce_id) || annonceLien
    const ligneDetail = (dossierLien && detailParDossier.get(dossierLien)) || (id && detailParAnnonce.get(id)) || null
    const detail = objet(ligneDetail?.detail_payload_json)
    const docs = new Set([...(dossierLien ? docsPar.get(`d${dossierLien}`) ?? [] : []), ...(id ? docsPar.get(`h${id}`) ?? [] : [])])
    biens.push({
      cle,
      appDossierId: dossier,
      hektorAnnonceId: id,
      titre: texte(b.titre_bien) || `Bien ${id || dossierLien}`,
      ville: texte(b.ville),
      statut: statut || 'inconnu',
      enVente: EN_VENTE.has(statut.toLowerCase()),
      mandat: texte(b.numero_mandat) || null,
      photo: texte(b.photo) || null,
      copro: lireCopro(ligneDetail?.detail_payload_json),
      documents: [...docs].sort((a, z) => a.localeCompare(z, 'fr')),
      adresse: texte(detail?.adresse_detail) || null,
      codePostal: texte(detail?.code_postal_detail) || texte(detail?.code_postal) || null,
      annee: (() => { const a = nombre(objet(objet(objet(detail?.diagnostiques_json)?.props)?.ANNEE_CONS)?.value); return a && a > 1000 ? a : null })(),
    })
  }
  biens.sort((a, z) => Number(z.enVente) - Number(a.enVente) || a.titre.localeCompare(z.titre, 'fr'))
  const qp = biens.map((b) => b.copro?.quotePart).filter((n): n is number => n != null && n > 0)
  return {
    biens,
    enVente: biens.filter((b) => b.enVente).length,
    quotePartMoyenne: qp.length ? Math.round(qp.reduce((s, n) => s + n, 0) / qp.length) : null,
    avecDocuments: biens.filter((b) => b.documents.length > 0).length,
  }
}
