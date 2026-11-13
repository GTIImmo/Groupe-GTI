// GED (12/11/2026, morceau 4) -- L'IA PROPOSE LE TYPE D'UN FICHIER AVANT SON ENVOI.
// Tout se décide ICI, dans le navigateur, avant qu'un octet sorte : on fait des vignettes BASSE définition de quelques
// pages (512 px), on lit la couche texte du PDF, et la GARDE RIB tranche. ⛔ Un RIB n'est JAMAIS envoyé à l'IA
// (décision du 12/11) : nom « RIB » / « IBAN », type déjà choisi « jamais envoyé », ou un IBAN (clé de contrôle
// vérifiée) ou « relevé d'identité bancaire » dans le texte -> rien ne part. Le serveur revérifie (2e verrou,
// backend/app/services/ged_garde_rib.py, mêmes règles, mêmes exemples dans les deux essais).
// L'IA PROPOSE ; l'humain choisit. Rien ne s'écrit sur le bien. Interrupteur `ged_lecture_ia` (off / admin / on).
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.9.
import { useEffect, useState } from 'react'
import { loadInterrupteurTroisCrans } from './ged'
import { hasSupabaseEnv, supabase } from './supabase'

export const IA_COTE_VIGNETTE = 512
export const IA_PAGES_MAX = 12
export const IA_TEXTE_MAX = 6000
const IA_PAGES_TEXTE_GARDE = 150 // la garde RIB lit le texte de toutes les pages jusqu'à 150 ; seul un extrait part

export type ResultatIa = {
  typeCode: string
  confiance: 'haute' | 'moyenne' | 'basse'
  nomPropose: string | null
  pieces: Array<{ typeCode: string; pageDebut: number; pageFin: number }>
  sensible: boolean
  lisible: boolean
  remarque: string | null
  costUsd?: number | null
}

export type Preparation =
  | { envoyable: false; raison: string; rib: boolean }
  | { envoyable: true; nbPages: number; pages: Array<{ numero: number; image: string }>; texte: string }

// ── la garde RIB (fonctions pures, testées hors ligne : test_ged_classement_ia.cjs) ─────────────────────────────
const sansAccents = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '')

export function ibanValide(candidat: string): boolean {
  const brut = candidat.replace(/ /g, '').toUpperCase()
  if (brut.length < 15 || brut.length > 34 || !/^[A-Z]{2}\d{2}[A-Z0-9]+$/.test(brut)) return false
  const tourne = brut.slice(4) + brut.slice(0, 4)
  let reste = 0
  for (const c of tourne) {
    const v = parseInt(c, 36).toString()
    for (const chiffre of v) reste = (reste * 10 + Number(chiffre)) % 97
  }
  return reste === 1
}

export function texteDitRib(texte: string | null | undefined): boolean {
  if (!texte) return false
  const plat = sansAccents(texte).toLowerCase().replace(/’/g, "'")
  if (plat.includes("releve d'identite bancaire") || plat.includes('releve d identite bancaire')) return true
  const maj = sansAccents(texte).toUpperCase()
  const debut = /\b[A-Z]{2}\d{2}/g
  let m: RegExpExecArray | null
  while ((m = debut.exec(maj))) {
    const suite = /^(?: ?[A-Z0-9]){11,40}/.exec(maj.slice(m.index + m[0].length))
    const brut = (m[0] + (suite ? suite[0] : '')).replace(/ /g, '')
    for (let n = 15; n <= Math.min(brut.length, 34); n += 1) if (ibanValide(brut.slice(0, n))) return true
  }
  return false
}

export function nomDitRib(nom: string | null | undefined): boolean {
  if (!nom) return false
  const plat = sansAccents(nom).toLowerCase().replace(/[^a-z0-9]+/g, ' ')
  return /(^| )(rib|iban)( |$)/.test(plat) || plat.includes('identite bancaire')
}

// Les pages montrées à l'IA : toutes jusqu'à 12, sinon les 8 premières et les 4 dernières (la signature, l'annexe).
export function pagesAEnvoyer(nbPages: number): number[] {
  if (nbPages <= IA_PAGES_MAX) return Array.from({ length: nbPages }, (_, i) => i + 1)
  return [1, 2, 3, 4, 5, 6, 7, 8, nbPages - 3, nbPages - 2, nbPages - 1, nbPages]
}

// Le type de l'IA est-il PRÉ-CHOISI sur la ligne, ou seulement montré ? Pré-choisi seulement si le nom ne disait rien
// de sûr, que l'humain n'a rien choisi (ni à la main, ni depuis « Reçu / Manque ») et que l'IA ne devine pas.
export function preChoisirTypeIa(l: { forceNom: 'sur' | 'probable' | 'muet' | 'reste'; typeTouche: boolean; typeAttendu: boolean }, r: ResultatIa): boolean {
  if (l.typeTouche || l.typeAttendu || r.confiance === 'basse' || !r.lisible) return false
  return l.forceNom !== 'sur'
}

// ── la préparation, dans le navigateur ─────────────────────────────────────────────────────────────────────────
function canvasEnJpeg(canvas: HTMLCanvasElement): string {
  return canvas.toDataURL('image/jpeg', 0.7)
}

async function vignetteImage(file: Blob): Promise<string> {
  const bitmap = await createImageBitmap(file)
  const echelle = Math.min(1, IA_COTE_VIGNETTE / Math.max(bitmap.width, bitmap.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(bitmap.width * echelle))
  canvas.height = Math.max(1, Math.round(bitmap.height * echelle))
  canvas.getContext('2d')?.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  return canvasEnJpeg(canvas)
}

async function chargerPdfjs() {
  const [pdfjs, travailleur] = await Promise.all([import('pdfjs-dist'), import('pdfjs-dist/build/pdf.worker.min.mjs?url')])
  pdfjs.GlobalWorkerOptions.workerSrc = travailleur.default
  return pdfjs
}

export async function preparerPourIa(file: File, typeChoisiJamaisEnvoye: boolean): Promise<Preparation> {
  if (typeChoisiJamaisEnvoye) return { envoyable: false, raison: 'Ce type ne part jamais à l\'IA.', rib: false }
  if (nomDitRib(file.name)) return { envoyable: false, raison: 'RIB : jamais envoyé à l\'IA.', rib: true }
  if (/^image\/(jpeg|png|webp)$/.test(file.type)) {
    return { envoyable: true, nbPages: 1, pages: [{ numero: 1, image: await vignetteImage(file) }], texte: '' }
  }
  if (file.type !== 'application/pdf') return { envoyable: false, raison: 'Format non lu par l\'IA (le nom seul compte).', rib: false }

  const pdfjs = await chargerPdfjs()
  const doc = await pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise
  try {
    const nbPages = doc.numPages
    const textes: string[] = []
    for (let n = 1; n <= Math.min(nbPages, IA_PAGES_TEXTE_GARDE); n += 1) {
      const page = await doc.getPage(n)
      const contenu = await page.getTextContent()
      textes.push(contenu.items.map((it) => ('str' in it ? it.str : '')).join(' '))
    }
    // ⛔ la garde RIB lit TOUT le texte, pas seulement l'extrait qui partirait
    if (texteDitRib(textes.join('\n'))) return { envoyable: false, raison: 'Un IBAN est dans le texte : jamais envoyé à l\'IA.', rib: true }
    const pages: Array<{ numero: number; image: string }> = []
    for (const n of pagesAEnvoyer(nbPages)) {
      const page = await doc.getPage(n)
      const base = page.getViewport({ scale: 1 })
      const vue = page.getViewport({ scale: IA_COTE_VIGNETTE / Math.max(base.width, base.height) })
      const canvas = document.createElement('canvas')
      canvas.width = Math.max(1, Math.round(vue.width))
      canvas.height = Math.max(1, Math.round(vue.height))
      const ctx = canvas.getContext('2d')
      if (!ctx) continue
      await page.render({ canvasContext: ctx, viewport: vue }).promise
      pages.push({ numero: n, image: canvasEnJpeg(canvas) })
    }
    const texte = textes.slice(0, 3).join('\n').replace(/[ \t]+/g, ' ').trim().slice(0, IA_TEXTE_MAX)
    return { envoyable: true, nbPages, pages, texte }
  } finally {
    void doc.destroy()
  }
}

// ── l'appel au serveur ─────────────────────────────────────────────────────────────────────────────────────────
const backendApiBaseUrl = (
  import.meta.env.VITE_BACKEND_API_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8010' : '')
).trim().replace(/\/+$/, '')

export async function classerParIa(prep: Extract<Preparation, { envoyable: true }>, nomFichier: string, hektorAnnonceId: string | number | null): Promise<ResultatIa> {
  if (!backendApiBaseUrl) throw new Error('Serveur non configuré')
  if (!hasSupabaseEnv || !supabase) throw new Error('Session absente')
  const jeton = (await supabase.auth.getSession()).data.session?.access_token
  if (!jeton) throw new Error('Session absente')
  const reponse = await fetch(`${backendApiBaseUrl}/ged/classer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jeton}` },
    body: JSON.stringify({
      nomFichier,
      hektorAnnonceId: hektorAnnonceId == null ? null : String(hektorAnnonceId),
      nbPages: prep.nbPages,
      pages: prep.pages,
      texte: prep.texte || null,
    }),
  })
  const corps = await reponse.json().catch(() => ({}))
  if (!reponse.ok || corps?.ok !== true) {
    const detail = typeof corps?.detail === 'string' ? corps.detail : `erreur ${reponse.status}`
    throw new Error(detail)
  }
  return corps as ResultatIa
}

// ── morceau 6 : la LECTURE des valeurs, juste après l'envoi (le fichier est encore dans le navigateur) ─────────────
// Texte d'abord : si les premières pages portent une vraie couche texte (≥ 30 mots chacune), on envoie le texte seul ;
// sinon les premières pages en haute définition (1 600 px), 4 au plus. ⛔ La garde RIB repasse avant tout envoi.
export const LECTURE_PAGES_HD = 4
const LECTURE_COTE_HD = 1600
const LECTURE_TEXTE_MAX = 20000
// Lot 2 (§12.14) : le titre de propriété (9 pages en médiane, 42 scans sur 50) a ses parties et sa désignation dans les
// premières pages -> 6 pages en image, 40 000 caractères en texte. Même réglage côté serveur (PAGES_HD, texte_max).
// Lot 3 (§12.15) : un compromis (124 000 caractères en médiane) a son prêt et ses honoraires avant 80 000, et ses
// SIGNATURES à la fin -> 80 000 caractères ET ses 2 dernières pages en image ; scanné : les 4 premières et les 2 dernières.
// Une offre (1 page, presque toujours scannée) : sa dernière page en image même avec du texte. PV d'AG : comme le titre.
// Lot 4 (§12.16) : le mandat (12 pages) comme le compromis, 40 000 caractères ; l'avenant et la fin de mandat (1 page) :
// la dernière en image ; l'acte (attestation de 4 pages, 41 scans sur 50) et le règlement (37 pages) : comme le titre.
const PAGES_HD_PAR_TYPE: Record<string, number> = {
  'justif.titre': 6, 'copro.pv_ag': 6, 'transaction.avant_contrat': 6, 'mandat.vente': 6, 'transaction.acte': 6, 'copro.reglement': 6,
}
const TEXTE_MAX_PAR_TYPE: Record<string, number> = {
  'justif.titre': 40000, 'copro.pv_ag': 40000, 'transaction.avant_contrat': 80000, 'mandat.vente': 40000, 'transaction.acte': 40000,
  'copro.reglement': 40000,
}
const FIN_EN_IMAGE_PAR_TYPE: Record<string, number> = {
  'transaction.avant_contrat': 2, 'transaction.offre': 1, 'mandat.vente': 2, 'mandat.avenant': 1, 'mandat.fin': 1,
}

// Les pages à mettre en image (numéros à partir de 1). Avec du texte : seulement les dernières, si le type les veut
// (signatures). Sans texte (scan) : les premières, et, si le type le veut, les dernières à la place des suivantes.
export function pagesAImager(nbPages: number, pagesHd: number, fin: number, avecTexte: boolean): number[] {
  const toutes = Array.from({ length: nbPages }, (_, i) => i + 1)
  if (avecTexte) return fin > 0 ? toutes.slice(-Math.min(fin, nbPages)) : []
  if (nbPages <= pagesHd) return toutes
  if (fin <= 0) return toutes.slice(0, pagesHd)
  return [...toutes.slice(0, pagesHd - fin), ...toutes.slice(-fin)]
}

export type PreparationLecture =
  | { lisible: false; raison: string }
  | { lisible: true; nbPages: number; pages: Array<{ numero: number; image: string }>; texte: string }

async function imageHd(source: CanvasImageSource & { width: number; height: number }): Promise<string> {
  const echelle = Math.min(1, LECTURE_COTE_HD / Math.max(source.width, source.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(source.width * echelle))
  canvas.height = Math.max(1, Math.round(source.height * echelle))
  canvas.getContext('2d')?.drawImage(source, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL('image/jpeg', 0.82)
}

export async function preparerLecture(file: File, typeCode?: string): Promise<PreparationLecture> {
  const pagesHd = (typeCode && PAGES_HD_PAR_TYPE[typeCode]) || LECTURE_PAGES_HD
  const texteMax = (typeCode && TEXTE_MAX_PAR_TYPE[typeCode]) || LECTURE_TEXTE_MAX
  const fin = (typeCode && FIN_EN_IMAGE_PAR_TYPE[typeCode]) || 0
  if (nomDitRib(file.name)) return { lisible: false, raison: 'RIB : jamais envoyé à l\'IA.' }
  if (/^image\/(jpeg|png|webp)$/.test(file.type)) {
    return { lisible: true, nbPages: 1, pages: [{ numero: 1, image: await imageHd(await createImageBitmap(file)) }], texte: '' }
  }
  if (file.type !== 'application/pdf') return { lisible: false, raison: 'Format non lu par l\'IA.' }
  const pdfjs = await chargerPdfjs()
  const doc = await pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise
  try {
    const nbPages = doc.numPages
    const textes: string[] = []
    for (let n = 1; n <= Math.min(nbPages, IA_PAGES_TEXTE_GARDE); n += 1) {
      const contenu = await (await doc.getPage(n)).getTextContent()
      textes.push(contenu.items.map((it) => ('str' in it ? it.str : '')).join(' ').replace(/\s+/g, ' ').trim())
    }
    if (texteDitRib(textes.join('\n'))) return { lisible: false, raison: 'Un IBAN est dans le texte : jamais envoyé à l\'IA.' }
    const premieres = textes.slice(0, Math.min(3, nbPages))
    const avecTexte = premieres.length > 0 && premieres.every((t) => t.split(' ').filter(Boolean).length >= 30)
    const texte = avecTexte ? textes.map((t, i) => `--- page ${i + 1} ---\n${t}`).join('\n').slice(0, texteMax) : ''
    const pages: Array<{ numero: number; image: string }> = []
    for (const n of pagesAImager(nbPages, pagesHd, fin, avecTexte)) {
      const page = await doc.getPage(n)
      const base = page.getViewport({ scale: 1 })
      const vue = page.getViewport({ scale: LECTURE_COTE_HD / Math.max(base.width, base.height) })
      const canvas = document.createElement('canvas')
      canvas.width = Math.max(1, Math.round(vue.width))
      canvas.height = Math.max(1, Math.round(vue.height))
      const ctx = canvas.getContext('2d')
      if (!ctx) continue
      await page.render({ canvasContext: ctx, viewport: vue }).promise
      pages.push({ numero: n, image: canvas.toDataURL('image/jpeg', 0.82) })
    }
    return { lisible: true, nbPages, pages, texte }
  } finally {
    void doc.destroy()
  }
}

export type ResultatLecture = { lectureId: string; fiche: string; etat: 'lu' | 'incomplet' | 'pas_ce_type'; valeurs: import('./gedLecture').ValeurLue[] }

export async function lireParIa(jobId: string, prep: Extract<PreparationLecture, { lisible: true }>, nomFichier: string): Promise<ResultatLecture> {
  if (!backendApiBaseUrl) throw new Error('Serveur non configuré')
  if (!hasSupabaseEnv || !supabase) throw new Error('Session absente')
  const jeton = (await supabase.auth.getSession()).data.session?.access_token
  if (!jeton) throw new Error('Session absente')
  const reponse = await fetch(`${backendApiBaseUrl}/ged/lire`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jeton}` },
    body: JSON.stringify({ jobId, nomFichier, nbPages: prep.nbPages, pages: prep.pages, texte: prep.texte || null }),
  })
  const corps = await reponse.json().catch(() => ({}))
  if (!reponse.ok || corps?.ok !== true) throw new Error(typeof corps?.detail === 'string' ? corps.detail : `erreur ${reponse.status}`)
  return corps as ResultatLecture
}

// Découpe un PDF en plusieurs fichiers, une pièce par fichier (pdf-lib, déjà chargé pour « Faire un PDF »).
export async function separerPdf(file: File, pieces: ResultatIa['pieces'], nomPiece: (i: number) => string): Promise<File[]> {
  const { PDFDocument } = await import('pdf-lib')
  const source = await PDFDocument.load(await file.arrayBuffer())
  const fichiers: File[] = []
  for (const [i, p] of pieces.entries()) {
    const sortie = await PDFDocument.create()
    const indices = Array.from({ length: p.pageFin - p.pageDebut + 1 }, (_, k) => p.pageDebut - 1 + k)
    for (const page of await sortie.copyPages(source, indices)) sortie.addPage(page)
    const octets = await sortie.save()
    fichiers.push(new File([octets.slice().buffer as ArrayBuffer], `${nomPiece(i)}.pdf`, { type: 'application/pdf' }))
  }
  return fichiers
}

export function useGedLectureIa(): boolean {
  const [actif, setActif] = useState(false)
  useEffect(() => {
    let annule = false
    void loadInterrupteurTroisCrans('ged_lecture_ia').then((v) => { if (!annule) setActif(v) })
    return () => { annule = true }
  }, [])
  return actif
}
