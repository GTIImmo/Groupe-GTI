// GED (12/11/2026, morceau 3) -- « REÇU / MANQUE » : les pièces attendues au MOMENT en cours du dossier.
// La liste vient de la note du chantier GED §11.3 (les 6 moments validés par Frédéric le 06/11, chaque pièce marquée
// obligatoire / bonne pratique / selon le cas). On SIGNALE, on ne bloque rien (§11.6, point 2 encore ouvert).
// ⛔ Un document non reconnu se dit « non trouvé », JAMAIS « absent » : 14 % des noms sont muets (décision du 12/11).
// Fonction PURE : elle ne lit rien, elle reçoit la fiche et les documents ; essais : test_ged_recu_manque.cjs.
import { typeParNom } from './gedTypeParNom'

export type MomentDossier = 'mandat' | 'mise_en_vente' | 'offre' | 'compromis'
export type NiveauPiece = 'obligatoire' | 'bonne_pratique' | 'selon_le_cas'
export type EtatPiece = 'recu' | 'non_trouve' | 'selon_le_cas'

export const LIBELLE_MOMENT: Record<MomentDossier, string> = {
  mandat: 'Prise de mandat',
  mise_en_vente: 'Mise en vente et visites',
  offre: 'Offre',
  compromis: 'Compromis',
}
const ORDRE: MomentDossier[] = ['mandat', 'mise_en_vente', 'offre', 'compromis']

// Les faits de la fiche dont dépendent les pièces « selon le cas ». null = la fiche ne le dit pas.
export type FaitsDuBien = {
  statut: string | null
  numeroMandat: string | null
  typeBien: string | null
  copropriete: boolean | null
  anneeConstruction: number | null
  assainissement: string | null
  dpeConso: number | null
  dpeGes: number | null
  // la case « DPE non concerné » de la fiche (bâtiment non soumis) : le DPE n'est alors pas attendu
  dpeNonConcerne: boolean
}

export type DocumentDuDossier = { nom: string; typeCode: string | null }

type Condition = (f: FaitsDuBien) => boolean | null
type Piece = { cle: string; libelle: string; types: string[]; niveau: NiveauPiece; si?: Condition; pourquoi?: string; sensible?: boolean }

// Les codes Hektor du type de bien (hektorContactSearchTypeOptions, App.tsx) : maison 1, villa 25, maison de village 39 ;
// terrain 5, terrain à bâtir 43, garage 15, parking 16 (rien de bâti à diagnostiquer).
const MAISONS = new Set(['1', '25', '39'])
const NON_BATIS = new Set(['5', '43', '15', '16'])
const bati = (f: FaitsDuBien): boolean | null => (f.typeBien ? !NON_BATIS.has(f.typeBien) : null)

// La classe DPE (2021) recalculée depuis les valeurs de la fiche : la pire des deux étiquettes, énergie et climat.
export function classeDpe(conso: number | null, ges: number | null): string | null {
  if (conso == null || ges == null || conso <= 0) return null
  const e = conso <= 70 ? 0 : conso <= 110 ? 1 : conso <= 180 ? 2 : conso <= 250 ? 3 : conso <= 330 ? 4 : conso <= 420 ? 5 : 6
  const g = ges <= 6 ? 0 : ges <= 11 ? 1 : ges <= 30 ? 2 : ges <= 50 ? 3 : ges <= 70 ? 4 : ges <= 100 ? 5 : 6
  return 'ABCDEFG'[Math.max(e, g)]
}

const siCopro: Condition = (f) => f.copropriete
const siBati: Condition = (f) => bati(f)
const siDpeAttendu: Condition = (f) => (f.dpeNonConcerne ? false : bati(f))
const siAuditAttendu: Condition = (f) => {
  if (f.typeBien && !MAISONS.has(f.typeBien)) return false
  const c = classeDpe(f.dpeConso, f.dpeGes)
  if (!f.typeBien || !c) return null
  return ['E', 'F', 'G'].includes(c)
}
const siAvant = (annee: number): Condition => (f) => {
  if (bati(f) === false) return false
  return f.anneeConstruction == null ? null : f.anneeConstruction < annee
}
const siNonCollectif: Condition = (f) => {
  if (bati(f) === false) return false
  const a = (f.assainissement ?? '').toUpperCase()
  if (!a || a === 'OUI') return null
  return a !== "TOUT A L'EGOUT" && a !== 'SANS'
}

const DIAG_DOSSIER = 'diag.dossier'
const PIECES: Record<MomentDossier, Piece[]> = {
  mandat: [
    { cle: 'mandat', libelle: 'Mandat de vente signé', types: ['mandat.vente'], niveau: 'obligatoire' },
    { cle: 'identite', libelle: 'Pièce d\'identité de chaque mandant', types: ['justif.identite'], niveau: 'obligatoire', sensible: true },
    { cle: 'titre', libelle: 'Titre de propriété', types: ['justif.titre'], niveau: 'bonne_pratique' },
    { cle: 'etat_civil', libelle: 'Situation familiale (livret, contrat de mariage)', types: ['justif.etat_civil'], niveau: 'bonne_pratique', sensible: true },
    { cle: 'taxe', libelle: 'Taxe foncière', types: ['justif.taxe'], niveau: 'bonne_pratique' },
  ],
  mise_en_vente: [
    { cle: 'dpe', libelle: 'DPE', types: ['diag.dpe', DIAG_DOSSIER], niveau: 'obligatoire', si: siDpeAttendu },
    { cle: 'erp', libelle: 'État des risques (moins de 6 mois)', types: ['diag.erp', DIAG_DOSSIER], niveau: 'obligatoire' },
    { cle: 'audit', libelle: 'Audit énergétique', types: ['diag.audit'], niveau: 'selon_le_cas', si: siAuditAttendu, pourquoi: 'maison classée E, F ou G' },
    { cle: 'charges', libelle: 'Charges de copropriété (arrêté ou appel de fonds)', types: ['copro.arrete_charges', 'copro.appel_fonds'], niveau: 'selon_le_cas', si: siCopro, pourquoi: 'copropriété' },
    { cle: 'fiche_synthetique', libelle: 'Fiche synthétique de la copropriété', types: ['copro.carnet'], niveau: 'selon_le_cas', si: siCopro, pourquoi: 'copropriété' },
    { cle: 'ddt', libelle: 'Dossier de diagnostics complet', types: [DIAG_DOSSIER], niveau: 'bonne_pratique', si: siBati },
    { cle: 'bon_visite', libelle: 'Bons de visite', types: ['visite.bon'], niveau: 'bonne_pratique' },
  ],
  offre: [
    { cle: 'offre', libelle: 'Offre d\'achat signée', types: ['transaction.offre'], niveau: 'bonne_pratique' },
    { cle: 'financement', libelle: 'Plan de financement ou accord de principe', types: ['transaction.financement'], niveau: 'bonne_pratique', sensible: true },
  ],
  compromis: [
    { cle: 'compromis', libelle: 'Compromis signé', types: ['transaction.avant_contrat'], niveau: 'obligatoire' },
    { cle: 'dpe', libelle: 'DPE', types: ['diag.dpe', DIAG_DOSSIER], niveau: 'obligatoire', si: siDpeAttendu },
    { cle: 'erp', libelle: 'État des risques (moins de 6 mois)', types: ['diag.erp', DIAG_DOSSIER], niveau: 'obligatoire' },
    { cle: 'amiante', libelle: 'Amiante', types: ['diag.amiante', DIAG_DOSSIER], niveau: 'selon_le_cas', si: siAvant(1997), pourquoi: 'construit avant le 01/07/1997' },
    { cle: 'plomb', libelle: 'Plomb (CREP)', types: ['diag.plomb', DIAG_DOSSIER], niveau: 'selon_le_cas', si: siAvant(1949), pourquoi: 'construit avant 1949' },
    { cle: 'electricite', libelle: 'Électricité', types: ['diag.electricite', DIAG_DOSSIER], niveau: 'selon_le_cas', si: siAvant(new Date().getFullYear() - 15), pourquoi: "bâti de plus de 15 ans (l'âge de l'installation n'est pas connu)" },
    { cle: 'assainissement', libelle: 'Assainissement (contrôle SPANC)', types: ['diag.assainissement'], niveau: 'selon_le_cas', si: siNonCollectif, pourquoi: 'assainissement non collectif' },
    { cle: 'carrez', libelle: 'Surface Carrez', types: ['diag.surface', DIAG_DOSSIER], niveau: 'selon_le_cas', si: siCopro, pourquoi: 'lot de copropriété' },
    { cle: 'reglement', libelle: 'Règlement de copropriété', types: ['copro.reglement'], niveau: 'selon_le_cas', si: siCopro, pourquoi: 'copropriété' },
    { cle: 'pv_ag', libelle: 'PV des 3 dernières assemblées', types: ['copro.pv_ag'], niveau: 'selon_le_cas', si: siCopro, pourquoi: 'copropriété' },
    { cle: 'pre_etat_date', libelle: 'Pré-état daté', types: ['copro.etat_date'], niveau: 'selon_le_cas', si: siCopro, pourquoi: 'copropriété' },
    { cle: 'titre', libelle: 'Titre de propriété', types: ['justif.titre'], niveau: 'obligatoire' },
    { cle: 'etat_civil', libelle: 'État civil des vendeurs', types: ['justif.etat_civil'], niveau: 'obligatoire', sensible: true },
    { cle: 'sru', libelle: 'Notification SRU (après la signature)', types: ['transaction.sru'], niveau: 'bonne_pratique' },
    { cle: 'sequestre', libelle: 'Attestation de séquestre', types: ['transaction.sequestre'], niveau: 'bonne_pratique' },
  ],
}

export function momentDuDossier(f: Pick<FaitsDuBien, 'statut' | 'numeroMandat'>): MomentDossier {
  const s = (f.statut ?? '').toLowerCase()
  if (s.includes('compromis')) return 'compromis'
  if (s.includes('offre')) return 'offre'
  if (!(f.numeroMandat ?? '').trim()) return 'mandat'
  return 'mise_en_vente'
}

// Le type d'un document : celui que l'humain a décidé (classement GED), sinon celui que dit son nom (« sûr » ou
// « probable »). Un nom muet ou non reconnu n'a pas de type.
export function typeDuDocument(d: DocumentDuDossier): string | null {
  if (d.typeCode) return d.typeCode
  const t = typeParNom(d.nom)
  return t.force === 'sur' || t.force === 'probable' ? t.code : null
}

export type LignePiece = {
  cle: string
  libelle: string
  niveau: NiveauPiece
  etat: EtatPiece
  pourquoi: string | null
  documents: string[]
  dansUnDossier: boolean
  typeADeposer: string
  sensible: boolean
}

function evaluer(pieces: Piece[], faits: FaitsDuBien, docs: Array<{ nom: string; type: string | null }>): LignePiece[] {
  const lignes: LignePiece[] = []
  for (const p of pieces) {
    const condition = p.si ? p.si(faits) : true
    if (condition === false) continue
    const directs = docs.filter((d) => d.type && p.types.includes(d.type) && d.type !== DIAG_DOSSIER)
    const viaDossier = docs.filter((d) => d.type === DIAG_DOSSIER && p.types.includes(DIAG_DOSSIER))
    const trouves = directs.length ? directs : viaDossier
    lignes.push({
      cle: p.cle,
      libelle: p.libelle,
      niveau: condition === null ? 'selon_le_cas' : p.niveau,
      etat: trouves.length ? 'recu' : condition === null ? 'selon_le_cas' : 'non_trouve',
      pourquoi: p.pourquoi ?? null,
      documents: trouves.map((d) => d.nom),
      dansUnDossier: !directs.length && viaDossier.length > 0,
      typeADeposer: p.types[0],
      sensible: Boolean(p.sensible),
    })
  }
  return lignes
}

export type RecuManque = {
  moment: MomentDossier
  pieces: LignePiece[]
  recues: number
  attendues: number
  precedents: Array<{ moment: MomentDossier; manquantes: LignePiece[] }>
}

export function recuManque(faits: FaitsDuBien, documents: DocumentDuDossier[]): RecuManque {
  const moment = momentDuDossier(faits)
  const docs = documents.map((d) => ({ nom: d.nom, type: typeDuDocument(d) }))
  const pieces = evaluer(PIECES[moment], faits, docs)
  const comptees = pieces.filter((l) => l.etat !== 'selon_le_cas')
  const precedents = ORDRE.slice(0, ORDRE.indexOf(moment))
    .map((m) => ({ moment: m, manquantes: evaluer(PIECES[m], faits, docs).filter((l) => l.etat === 'non_trouve' && l.niveau === 'obligatoire') }))
    // une pièce déjà demandée au moment en cours n'est pas répétée dans les moments précédents
    .map((p) => ({ ...p, manquantes: p.manquantes.filter((l) => !pieces.some((x) => x.cle === l.cle)) }))
    .filter((p) => p.manquantes.length)
  return { moment, pieces, recues: comptees.filter((l) => l.etat === 'recu').length, attendues: comptees.length, precedents }
}
