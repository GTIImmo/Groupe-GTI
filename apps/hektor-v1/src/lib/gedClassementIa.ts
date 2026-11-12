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
