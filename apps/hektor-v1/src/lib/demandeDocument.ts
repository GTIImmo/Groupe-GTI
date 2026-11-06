// CHANTIER PARTENAIRES · LOT 4, PIÈCE 4.4 (06/11/2026) — « DEMANDER UN DOCUMENT » AU SYNDIC, VERSION SIMPLE. Règles pures.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28 (plan accéléré) et §28.1.
// Un MESSAGE PRÊT (le bien, ses lots, son mandat, les pièces cochées), modifiable, à copier ou à ouvrir dans la messagerie
// quand l'e-mail du syndic est connu (3 syndics sur 75 au 06/11). RIEN n'est stocké ni envoyé par l'app : le suivi des
// demandes et des délais reste « en construction ».

export type BienDemande = {
  id: string
  titre: string
  adresse: string | null
  codePostal: string | null
  ville: string | null
  lots: string | null
  mandat: string | null
  // Lot 5 (06/11) : pour la commande de diagnostics (facultatif ; une donnée absente n'est pas écrite).
  annee?: number | null
  copro?: boolean
  typeBien?: string | null
  surface?: string | null
}

export type PieceCopro = { cle: string; libelle: string; defaut: boolean }

// Les pièces de copropriété qu'on demande pour vendre un lot (celles que la loi fait joindre à la promesse, art. L721-2
// du code de la construction et de l'habitation, et le pré-état daté). Les cinq premières sont cochées d'office.
export const PIECES_COPRO: PieceCopro[] = [
  { cle: 'pre_etat_date', libelle: 'Pré-état daté', defaut: true },
  { cle: 'pv_ag', libelle: 'Procès-verbaux des assemblées générales des trois dernières années', defaut: true },
  { cle: 'reglement', libelle: 'Règlement de copropriété et état descriptif de division, avec leurs modificatifs', defaut: true },
  { cle: 'fiche_synthetique', libelle: 'Fiche synthétique de la copropriété', defaut: true },
  { cle: 'carnet', libelle: "Carnet d'entretien de l'immeuble", defaut: true },
  { cle: 'charges', libelle: 'Charges courantes et hors budget des deux derniers exercices', defaut: false },
  { cle: 'travaux', libelle: 'Diagnostic technique global ou plan pluriannuel de travaux', defaut: false },
]
export const piecesParDefaut = () => PIECES_COPRO.filter((p) => p.defaut).map((p) => p.cle)

const texte = (v: unknown) => String(v ?? '').trim()

export function adresseLisible(b: BienDemande): string {
  const rue = texte(b.adresse)
  const ville = [texte(b.codePostal), texte(b.ville)].filter(Boolean).join(' ')
  return [rue, ville].filter(Boolean).join(', ') || texte(b.titre) || 'le bien'
}

// Le message : sujet + corps, en français, sans rien inventer (une donnée absente n'est pas écrite).
export function messageDemande(input: { bien: BienDemande; pieces: string[]; signature?: string | null }): { sujet: string; corps: string } {
  const b = input.bien
  const lots = texte(b.lots)
  const adresse = adresseLisible(b)
  const choisies = PIECES_COPRO.filter((p) => input.pieces.includes(p.cle))
  const lignesBien = [
    `- Adresse : ${adresse}`,
    lots ? `- Lot${/[,;\s-]/.test(lots) ? 's' : ''} : ${lots}` : null,
    texte(b.mandat) ? `- Notre référence : mandat n° ${texte(b.mandat)}` : null,
  ].filter(Boolean)
  const corps = [
    'Bonjour,',
    '',
    'Nous sommes chargés de la vente d\'un lot dans une copropriété dont vous êtes le syndic :',
    ...lignesBien,
    '',
    choisies.length ? 'Pourriez-vous nous transmettre les documents suivants :' : 'Pourriez-vous nous transmettre les documents de copropriété de ce lot ?',
    ...choisies.map((p) => `- ${p.libelle}`),
    '',
    input.pieces.includes('pre_etat_date') ? "Merci de nous indiquer aussi le délai et, le cas échéant, le coût d'établissement du pré-état daté." : null,
    input.pieces.includes('pre_etat_date') ? '' : null,
    'Bien cordialement,',
    texte(input.signature) || 'Groupe GTI',
  ].filter((l) => l !== null) as string[]
  return {
    sujet: `Demande de documents de copropriété : ${adresse}${lots ? ` (lot${/[,;\s-]/.test(lots) ? 's' : ''} ${lots})` : ''}`,
    corps: corps.join('\n'),
  }
}

// Le lien « ouvrir dans ma messagerie » (null sans e-mail valable).
export function lienMessagerie(email: string | null | undefined, sujet: string, corps: string): string | null {
  const e = texte(email)
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) return null
  return `mailto:${e}?subject=${encodeURIComponent(sujet)}&body=${encodeURIComponent(corps)}`
}
