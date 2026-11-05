// A.2 lot 6b P5-P6 (05/11/2026) -- COMPARER CE QU'UN PDF IMPRIME. Pur, sans requete (essai : test_ecarts_fiche_pdf.cjs).
//   P5 « ce qui a change » : ancien PDF -> nouveau PDF (maquette « corriger » vue 4).
//   P6 « la fiche a change depuis ce PDF » : PDF -> fiche d'aujourd'hui (vue 5). On ne compare QUE ce qui vient de la
//      fiche : les mandants, le bien, les prix, les honoraires, le numero et le type. La date, la charge, l'occupation,
//      les clauses et les options se SAISISSENT dans l'editeur : la fiche n'en dit rien, elles ne sont pas comparees.
import type { ContenuImprimePdf, PhotoSignatairesPdf } from './api'

export type MandantImprime = { civilite: string | null; prenom: string | null; nom: string | null; id?: string | null }
// Le numero de fiche d'une carte de l'editeur -- memes regles que le worker (ficheDuMandantImprime) et que
// lib/conjointsDuMandat.ts (recopiees ici : ce module reste sans dependance).
const ficheDeLaCarte = (id?: string | null) => {
  const t = String(id ?? '')
  return t.match(/-member-(\d+)$/)?.[1] ?? t.match(/^[a-z-]*contact-\d+-(\d+)$/i)?.[1] ?? null
}
export type FicheDuJourPdf = { mandants: MandantImprime[]; contenu: ContenuImprimePdf }
export type LigneDiff = { k: string; avant?: string; apres?: string; plus?: string; moins?: string; note?: string }

export const CHAMPS_IMPRIMES: Array<[keyof ContenuImprimePdf, string, 'euros' | 'texte']> = [
  ['numero_mandat', 'N° mandat', 'texte'], ['type_mandat', 'Type de mandat', 'texte'], ['date_signature', 'Date de signature', 'texte'],
  ['bien_titre', 'Bien', 'texte'], ['bien_adresse', 'Adresse du bien', 'texte'], ['nombre_pieces', 'Pièces', 'texte'],
  ['surface_habitable', 'Surface habitable', 'texte'], ['surface_terrain', 'Surface terrain', 'texte'], ['etat_occupation', 'Occupation', 'texte'],
  ['prix_vente', 'Prix FAI', 'euros'], ['prix_net_vendeur', 'Net vendeur', 'euros'], ['honoraires_ttc', 'Honoraires TTC', 'euros'],
  ['honoraires_charge', 'Charge des honoraires', 'texte'], ['execution_anticipee', 'Exécution anticipée', 'texte'],
  ['inclure_couverture', 'Couverture', 'texte'], ['clause_particuliere', 'Clause particulière', 'texte'],
]
// P6 : ce que la FICHE porte (le reste se saisit dans l'editeur).
export const CHAMPS_DE_LA_FICHE: Array<keyof ContenuImprimePdf> = [
  'numero_mandat', 'type_mandat', 'bien_titre', 'bien_adresse', 'nombre_pieces', 'surface_habitable', 'surface_terrain',
  'prix_vente', 'prix_net_vendeur', 'honoraires_ttc',
]

export function montrer(valeur: unknown, forme: 'euros' | 'texte'): string {
  if (valeur === true) return 'Oui'
  if (valeur === false) return 'Non'
  const t = String(valeur ?? '').trim()
  if (!t) return '—'
  if (forme === 'euros') { const n = Number(t.replace(/\s/g, '').replace(',', '.')); if (Number.isFinite(n)) return `${n.toLocaleString('fr-FR')} €` }
  if (t === 'acquereur') return 'Acquéreur'
  if (t === 'mandant') return 'Mandant'
  return t.length > 80 ? `${t.slice(0, 77)}…` : t
}
// Deux ecritures du meme contenu ne font pas un ecart : espaces, casse ; pour un montant, la valeur seule.
function cle(valeur: unknown, forme: 'euros' | 'texte'): string {
  const t = String(valeur ?? '').trim()
  if (!t) return ''
  if (forme === 'euros') { const n = Number(t.replace(/[\s  €]/g, '').replace(',', '.')); if (Number.isFinite(n)) return String(n) }
  return t.replace(/\s+/g, ' ').toLowerCase()
}
export const nomImprime = (m: MandantImprime) => [m.civilite, m.prenom, m.nom].map((x) => String(x ?? '').trim()).filter(Boolean).join(' ') || '—'
const cleNom = (m: MandantImprime) => nomImprime(m).replace(/\s+/g, ' ').toLowerCase()
const formeDe = (champ: keyof ContenuImprimePdf) => (CHAMPS_IMPRIMES.find(([c]) => c === champ)?.[2] ?? 'texte')
const libelleDe = (champ: keyof ContenuImprimePdf) => (CHAMPS_IMPRIMES.find(([c]) => c === champ)?.[1] ?? String(champ))

// P5 -- « ce qui a change » entre deux PDF : les signataires (photos) et tout ce qui est imprime (contenu_imprime).
export function ceQuiAChange(ancienPhoto: PhotoSignatairesPdf | null, neuvePhoto: PhotoSignatairesPdf | null, ancienContenu: ContenuImprimePdf | null, neufContenu: ContenuImprimePdf | null) {
  const lignes: LigneDiff[] = []
  const a = ancienPhoto?.mandants ?? [], n = neuvePhoto?.mandants ?? []
  for (let i = 0; i < Math.max(a.length, n.length); i += 1) {
    if (a[i] && n[i] && nomImprime(a[i]) !== nomImprime(n[i])) lignes.push({ k: `Mandant ${i + 1}`, avant: nomImprime(a[i]), apres: nomImprime(n[i]) })
    else if (!a[i] && n[i]) lignes.push({ k: 'Mandants', plus: `＋ ${nomImprime(n[i])}`, note: `(mandant ${i + 1})` })
    else if (a[i] && !n[i]) lignes.push({ k: 'Mandants', moins: `− ${nomImprime(a[i])}`, note: `(n’est plus dans le mandat)` })
  }
  if (a.length !== n.length) lignes.push({ k: 'Signataires', avant: String(a.length + 1), apres: String(n.length + 1), note: `· donc ${n.length + 1} crédits au lieu de ${a.length + 1}` })
  const compare = Boolean(ancienContenu && neufContenu)
  if (ancienContenu && neufContenu) {
    for (const [champ, label, forme] of CHAMPS_IMPRIMES) {
      const av = montrer(ancienContenu[champ], forme), ap = montrer(neufContenu[champ], forme)
      if (av !== ap) lignes.push({ k: label, avant: av, apres: ap })
    }
  }
  return { lignes, compare }
}

// P6 -- le PDF (photo + contenu imprime) confronte a la fiche d'aujourd'hui. `avant` = le PDF, `apres` = la fiche.
// `resume` : ce que le PDF ENVERRAIT tel qu'il est, pour la confirmation « Envoyer quand meme ».
export function ecartsAvecLaFiche(photo: PhotoSignatairesPdf | null, contenu: ContenuImprimePdf | null, fiche: FicheDuJourPdf | null) {
  const lignes: LigneDiff[] = []
  const resume: string[] = []
  if (!photo || !fiche) return { lignes, resume, prixCompare: false }
  // P7 (D34) : un conjoint RETIRE expres de ce mandat n'est pas un ecart -- on l'ote de la fiche avant de comparer.
  const retires = new Set((contenu?.conjoints_retires ?? []).map(String))
  const p = photo.mandants ?? []
  const f = (fiche.mandants ?? []).filter((m) => { const n = ficheDeLaCarte(m.id); return !(n && retires.has(n)) })
  for (let i = 0; i < Math.max(p.length, f.length); i += 1) {
    if (p[i] && f[i] && cleNom(p[i]) !== cleNom(f[i])) {
      lignes.push({ k: `Mandant ${i + 1}`, avant: nomImprime(p[i]), apres: nomImprime(f[i]) })
      resume.push(`au nom de ${nomImprime(p[i])}`)
    } else if (!p[i] && f[i]) {
      lignes.push({ k: 'Mandants', plus: `＋ ${nomImprime(f[i])}`, note: 'ajouté sur la fiche, absent du PDF' })
      resume.push(`sans ${nomImprime(f[i])}`)
    } else if (p[i] && !f[i]) {
      lignes.push({ k: 'Mandants', moins: `− ${nomImprime(p[i])}`, note: 'dans le PDF, plus mandant sur la fiche' })
      resume.push(`avec ${nomImprime(p[i])}`)
    }
  }
  const prixCompare = Boolean(contenu)
  if (contenu) {
    for (const champ of CHAMPS_DE_LA_FICHE) {
      const forme = formeDe(champ)
      const cp = cle(contenu[champ], forme), cf = cle(fiche.contenu[champ], forme)
      // Une fiche muette ne contredit pas le PDF (ce que la fiche n'a pas, on ne le compare pas).
      if (!cf || cp === cf) continue
      lignes.push({ k: libelleDe(champ), avant: montrer(contenu[champ], forme), apres: montrer(fiche.contenu[champ], forme) })
      resume.push(`${libelleDe(champ)} ${montrer(contenu[champ], forme)}`)
    }
  }
  return { lignes, resume, prixCompare }
}
