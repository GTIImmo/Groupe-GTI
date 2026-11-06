// CHANTIER PARTENAIRES · LOT 5 (06/11/2026) — « COMMANDER UN DIAGNOSTIC », VERSION SIMPLE. Règles pures.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.2. Même principe que 4.4 : un MESSAGE PRÊT, modifiable,
// à copier ou à ouvrir dans la messagerie (29 diagnostiqueurs sur 36 ont un e-mail au 06/11). RIEN n'est stocké.
import type { BienDemande, PieceCopro } from './demandeDocument'

// Les diagnostics du dossier de diagnostic technique remis à la vente (art. L271-4 du code de la construction et de
// l'habitation). Cochés d'office : ceux qui valent pour tout bien vendu, et ceux que l'année de construction impose
// (année inconnue : on coche, mieux vaut demander que manquer).
export const DIAGNOSTICS: PieceCopro[] = [
  { cle: 'dpe', libelle: 'Diagnostic de performance énergétique (DPE)', defaut: true },
  { cle: 'erp', libelle: 'État des risques et pollutions (ERP)', defaut: true },
  { cle: 'electricite', libelle: "État de l'installation intérieure d'électricité", defaut: true },
  { cle: 'gaz', libelle: "État de l'installation intérieure de gaz", defaut: true },
  { cle: 'amiante', libelle: "Repérage de l'amiante (permis de construire avant le 1er juillet 1997)", defaut: false },
  { cle: 'plomb', libelle: "Constat de risque d'exposition au plomb (construit avant 1949)", defaut: false },
  { cle: 'carrez', libelle: 'Mesurage loi Carrez (lot de copropriété)', defaut: false },
  { cle: 'termites', libelle: 'État relatif aux termites (si la commune est concernée)', defaut: false },
  { cle: 'assainissement', libelle: "Contrôle de l'assainissement non collectif", defaut: false },
]

const texte = (v: unknown) => String(v ?? '').trim()

export function diagnosticsParDefaut(b: BienDemande): string[] {
  const annee = Number(b.annee)
  const connue = Number.isFinite(annee) && annee > 1000
  const coches = DIAGNOSTICS.filter((d) => d.defaut).map((d) => d.cle)
  if (!connue || annee < 1997) coches.push('amiante')
  if (!connue || annee < 1949) coches.push('plomb')
  if (b.copro) coches.push('carrez')
  return coches
}

export function messageCommande(input: { bien: BienDemande; pieces: string[]; signature?: string | null }): { sujet: string; corps: string } {
  const b = input.bien
  const rue = texte(b.adresse)
  const ville = [texte(b.codePostal), texte(b.ville)].filter(Boolean).join(' ')
  const adresse = [rue, ville].filter(Boolean).join(', ') || texte(b.titre) || 'le bien'
  const annee = Number(b.annee)
  const choisis = DIAGNOSTICS.filter((d) => input.pieces.includes(d.cle))
  const lignesBien = [
    `- Adresse : ${adresse}`,
    [texte(b.typeBien), texte(b.surface) ? `${texte(b.surface)} m²` : ''].filter(Boolean).length
      ? `- Bien : ${[texte(b.typeBien), texte(b.surface) ? `${texte(b.surface)} m²` : ''].filter(Boolean).join(', ')}` : null,
    Number.isFinite(annee) && annee > 1000 ? `- Année de construction : ${annee}` : null,
    b.copro ? `- En copropriété${texte(b.lots) ? ` (lot${/[,;\s-]/.test(texte(b.lots)) ? 's' : ''} ${texte(b.lots)})` : ''}` : null,
    texte(b.mandat) ? `- Notre référence : mandat n° ${texte(b.mandat)}` : null,
  ].filter(Boolean)
  const corps = [
    'Bonjour,',
    '',
    'Nous préparons la vente du bien suivant :',
    ...lignesBien,
    '',
    choisis.length ? 'Pourriez-vous réaliser les diagnostics suivants :' : 'Pourriez-vous réaliser les diagnostics nécessaires à la vente de ce bien ?',
    ...choisis.map((d) => `- ${d.libelle}`),
    '',
    'Merci de nous proposer une date de rendez-vous et de nous indiquer votre tarif.',
    '',
    'Bien cordialement,',
    texte(input.signature) || 'Groupe GTI',
  ]
  return { sujet: `Commande de diagnostics : ${adresse}`, corps: corps.join('\n') }
}
