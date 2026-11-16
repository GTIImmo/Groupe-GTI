// GED (12/11/2026, morceau 2) -- LA FENÊTRE DE DÉPÔT : plusieurs fichiers d'un coup, des photos de plusieurs pages
// assemblées en un seul PDF, le type et le nom proposés d'après le nom du fichier, le doublon reconnu, les pièces des
// personnes toujours en privé. Derrière l'interrupteur `ged_depot_multiple` (cran « admin » = Frédéric seul) : éteint,
// le panneau garde son formulaire d'aujourd'hui, inchangé.
// ⭐ L'ENVOI NE CHANGE PAS : chaque fichier part par createUploadDocumentToHektorJob, TEL QUEL, un après l'autre (le
//   chemin d'aujourd'hui : chez nous d'abord, Hektor ensuite). Puis app_ged_classer enregistre son type CHEZ NOUS.
//   Un classement raté n'empêche jamais un dépôt : la ligne le dit et propose de reclasser.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.7.
// ⭐ MORCEAU 4 (§12.9) : derrière `ged_lecture_ia`, l'IA PROPOSE le type de chaque fichier avant l'envoi, un fichier
//   après l'autre (lib/gedClassementIa.ts : vignettes basse définition, garde RIB dans le navigateur). Elle pré-choisit
//   seulement quand le nom ne disait rien de sûr et que personne n'a choisi ; sinon elle se montre (« Prendre ce type »).
//   Un PDF qui réunit plusieurs pièces peut être séparé d'un clic. On peut envoyer sans attendre l'IA.
// ⭐ HABILLAGE H2 (16/11, maquette https://claude.ai/artifact/S16jkpfnqtPF83xvUdkNtm, planche « Dépôt ») : une FENÊTRE
//   au-dessus du bien (en-tête sombre, zone de dépôt, liste + aperçu de la page 1, pied). Mêmes données, mêmes gestes,
//   même envoi. Fermer avec des fichiers non partis ne les perd plus en silence : une bande demande d'abord.
import { useEffect, useMemo, useRef, useState, type DragEvent, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { createUploadDocumentToHektorJob } from './lib/api'
import {
  empreinteFichier, gedClasser, GED_FAMILLES, GED_TAILLE_MAX, GED_TYPES_ACCEPTES, loadGedTypes, nomEnConflit,
  useGedLecturePersonnes, type GedType,
} from './lib/ged'
import { apercuPremierePage, classerParIa, lireParIa as lireValeursParIa, preChoisirTypeIa, preparerLecture, preparerPourIa, separerPdf, useGedLectureIa, type ResultatIa } from './lib/gedClassementIa'
import { FICHES_LUES, FICHES_PERSONNES_LUES, resumeLecture } from './lib/gedLecture'
import { LIBELLE_MOMENT, type MomentDossier } from './lib/gedPieces'
import { typeParNom } from './lib/gedTypeParNom'
import type { ConsoleDocument, ConsoleJob, Dossier } from './types'
import './DepotDocuments.css'

type EtatLigne = 'pret' | 'envoi' | 'envoye' | 'classement_echec' | 'echec'

// Où en est l'IA pour une ligne : null = pas encore demandée (ou interrupteur éteint).
type EtatIa =
  | { etat: 'lecture' }
  | { etat: 'fait'; r: ResultatIa }
  | { etat: 'non_envoye'; raison: string }
  | { etat: 'erreur'; raison: string }

type EtatLecture =
  | { etat: 'attente' }
  | { etat: 'lecture' }
  | { etat: 'fait'; resume: string }
  | { etat: 'erreur'; raison: string }

type Ligne = {
  id: string
  file: File
  nom: string
  nomTouche: boolean
  type: string
  typeTouche: boolean
  typeAttenduPose: boolean
  // le type déduit du NOM (pour l'étiquette) ; typePropose / typeProposePar = ce qui est enregistré avec le classement
  // (la proposition de l'IA si elle a répondu, sinon celle du nom), pour mesurer plus tard qui avait raison
  typeNom: string | null
  typePropose: string | null
  typeProposePar: 'nom' | 'ia' | null
  ia: EtatIa | null
  // morceau 6 : la lecture des valeurs APRÈS l'envoi (null = pas de fiche pour ce type, ou interrupteur éteint)
  lecture: EtatLecture | null
  forceNom: 'sur' | 'probable' | 'muet' | 'reste'
  visibilite: 'private' | 'shared'
  sha256: string | null
  doublonDe: string | null
  aEnvoyer: boolean
  refus: string | null
  etat: EtatLigne
  message: string | null
  jobId: string | null
}

const extension = (nom: string) => { const i = nom.lastIndexOf('.'); return i > 0 ? nom.slice(i) : '' }
const racine = (nom: string) => { const i = nom.lastIndexOf('.'); return i > 0 ? nom.slice(0, i) : nom }
const aujourdhui = () => new Date().toLocaleDateString('fr-FR').replace(/\//g, '-')
const taille = (o: number) => (o < 1024 * 1024 ? `${Math.max(1, Math.round(o / 1024))} Ko` : `${(o / 1024 / 1024).toFixed(1)} Mo`)

// Une image que le coffre refuse (HEIC…) est redessinée en JPEG quand le navigateur sait la lire.
async function versJpeg(file: File, cote = 2400): Promise<Blob | null> {
  try {
    const bitmap = await createImageBitmap(file)
    const echelle = Math.min(1, cote / Math.max(bitmap.width, bitmap.height))
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(bitmap.width * echelle)
    canvas.height = Math.round(bitmap.height * echelle)
    canvas.getContext('2d')?.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
    return await new Promise((ok) => canvas.toBlob((b) => ok(b), 'image/jpeg', 0.85))
  } catch {
    return null
  }
}

// Les photos de plusieurs pages deviennent UN PDF (une page par photo). pdf-lib n'est chargé qu'à ce moment-là.
async function photosEnPdf(photos: File[]): Promise<File> {
  const { PDFDocument } = await import('pdf-lib')
  const pdf = await PDFDocument.create()
  for (const photo of photos) {
    const jpeg = await versJpeg(photo)
    if (!jpeg) throw new Error(`La photo « ${photo.name} » ne peut pas être lue.`)
    const image = await pdf.embedJpg(await jpeg.arrayBuffer())
    const page = pdf.addPage([image.width, image.height])
    page.drawImage(image, { x: 0, y: 0, width: image.width, height: image.height })
  }
  const octets = await pdf.save()
  return new File([octets.slice().buffer as ArrayBuffer], `Document photographie ${aujourdhui()}.pdf`, { type: 'application/pdf' })
}

export function DepotDocuments({
  dossier, documents, peutEnvoyer, onJobCreated, onTermine, formulaireClassique, typeAttendu, onTypeAttenduUtilise,
  onFermer, contexte,
}: {
  dossier: Dossier
  documents: ConsoleDocument[]
  peutEnvoyer: () => boolean
  onJobCreated?: (job: ConsoleJob) => void
  onTermine?: () => void
  formulaireClassique: ReactNode
  // GED morceau 3 : une pièce « non trouvée » cliquée dans « Reçu / Manque » -- le prochain fichier prend ce type
  typeAttendu?: { code: string; libelle: string } | null
  onTypeAttenduUtilise?: () => void
  // H2 : présent = la fenêtre s'ouvre AU-DESSUS de la page et sait se fermer ; absent = posée dans le panneau, comme avant
  onFermer?: () => void
  // H2 : le moment de la vente et les pièces non trouvées, tels que « Le dossier » les a lus (null = bloc éteint)
  contexte?: { moment: MomentDossier; nonTrouvees: string[] } | null
}) {
  const [types, setTypes] = useState<GedType[] | null>(null)
  const [erreurTypes, setErreurTypes] = useState<string | null>(null)
  const [lignes, setLignes] = useState<Ligne[]>([])
  const [pages, setPages] = useState<File[]>([])
  const [assemblage, setAssemblage] = useState(false)
  const [envoiEnCours, setEnvoiEnCours] = useState(false)
  const [survol, setSurvol] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const versionInput = useRef(0)
  const [, forcer] = useState(0)
  // H2 : la ligne dont l'aperçu est montré, les pages 1 déjà dessinées, la bande « pas partis », le lot en cours d'envoi
  const [choisi, setChoisi] = useState<string | null>(null)
  const [apercus, setApercus] = useState<Record<string, { image: string; nbPages: number } | 'aucun' | 'lecture'>>({})
  const [bande, setBande] = useState(false)
  const [lot, setLot] = useState<string[]>([])
  const fenetreRef = useRef<HTMLElement | null>(null)
  // H4 : les vignettes des pages photographiées -- des adresses LOCALES (rien ne part), rendues dès que les photos
  // sont assemblées ou annulées
  const vignettesPages = useMemo(() => pages.map((f) => URL.createObjectURL(f)), [pages])
  useEffect(() => () => vignettesPages.forEach((u) => URL.revokeObjectURL(u)), [vignettesPages])

  useEffect(() => {
    let annule = false
    loadGedTypes()
      .then((t) => { if (!annule) setTypes(t) })
      .catch((e) => { if (!annule) setErreurTypes(e instanceof Error ? e.message : String(e)) })
    return () => { annule = true }
  }, [])

  // « une saisie ne se perd jamais » : quitter la page avec des fichiers non envoyés demande confirmation
  useEffect(() => {
    // (et, morceau 6, tant qu'une lecture attend : le fichier n'est plus que dans cette page)
    if (!lignes.some((l) => (l.etat === 'pret' && l.aEnvoyer) || l.lecture?.etat === 'attente' || l.lecture?.etat === 'lecture')) return
    const avant = (e: BeforeUnloadEvent) => { e.preventDefault() }
    window.addEventListener('beforeunload', avant)
    return () => window.removeEventListener('beforeunload', avant)
  }, [lignes])

  const lectureIa = useGedLectureIa()
  // Morceau 9 (9a) : une pièce des personnes n'est lue que si SON interrupteur est ouvert (le serveur le revérifie)
  const lecturePersonnes = useGedLecturePersonnes()
  const typeLu = (code: string) => FICHES_LUES.has(code) || (lecturePersonnes && FICHES_PERSONNES_LUES.has(code))

  // La file de l'IA : UNE ligne à la fois, dans l'ordre du dépôt ; une ligne déjà envoyée n'est plus demandée.
  useEffect(() => {
    if (!lectureIa || !types) return
    if (lignes.some((l) => l.ia?.etat === 'lecture')) return
    const suivante = lignes.find((l) => l.ia === null && l.etat === 'pret')
    if (suivante) void lireParIa(suivante)
    // lireParIa écrit par setLignes (état à jour) : seule la liste déclenche
  }, [lectureIa, types, lignes])

  // Morceau 6 : la file des LECTURES, une à la fois, pour les documents envoyés dont le type a une fiche.
  useEffect(() => {
    if (!lectureIa || lignes.some((l) => l.lecture?.etat === 'lecture')) return
    const suivante = lignes.find((l) => l.lecture?.etat === 'attente' && l.etat === 'envoye' && l.jobId)
    if (suivante) void lireValeurs(suivante)
  }, [lectureIa, lignes])

  const parCode = useMemo(() => new Map((types ?? []).map((t) => [t.code, t])), [types])
  const familles = useMemo(() => {
    const groupes = new Map<string, GedType[]>()
    for (const t of types ?? []) groupes.set(t.famille, [...(groupes.get(t.famille) ?? []), t])
    return [...groupes.entries()]
  }, [types])

  // ── H2 : l'aperçu montre la ligne choisie, sinon la première « à vérifier », sinon la première. La page 1 est dessinée
  // une fois par fichier, à la demande (jamais tout le lot d'un coup).
  const avisIa = (l: Ligne) => l.ia?.etat === 'fait' && l.ia.r.lisible && l.ia.r.typeCode !== l.type
  const selection = lignes.find((l) => l.id === choisi) ?? lignes.find((l) => l.etat === 'pret' && avisIa(l)) ?? lignes[0] ?? null
  const idSelection = selection?.id ?? null
  useEffect(() => {
    if (!idSelection || apercus[idSelection]) return
    const ligne = lignes.find((l) => l.id === idSelection)
    if (!ligne) return
    setApercus((a) => ({ ...a, [idSelection]: 'lecture' }))
    apercuPremierePage(ligne.file)
      .then((r) => setApercus((a) => ({ ...a, [idSelection]: r ?? 'aucun' })))
      .catch(() => setApercus((a) => ({ ...a, [idSelection]: 'aucun' })))
  }, [idSelection, apercus, lignes])

  // ── H2 : la fenêtre au-dessus de la page. Ouverte : la page derrière ne défile plus, le clavier est dans la fenêtre ;
  // fermée : tout revient comme avant.
  const modale = Boolean(onFermer)
  useEffect(() => {
    if (!modale) return
    const avant = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const defilement = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    fenetreRef.current?.focus()
    return () => { document.body.style.overflow = defilement; avant?.focus() }
  }, [modale])

  // « une saisie ne se perd jamais » : fermer avec des fichiers non partis, un envoi ou une lecture en cours demande
  // d'abord (la même règle que pour quitter la page, plus haut)
  const nonPartis = lignes.filter((l) => l.etat === 'pret' && l.aEnvoyer).length
  const lecturesEnCours = lignes.filter((l) => l.lecture?.etat === 'attente' || l.lecture?.etat === 'lecture').length
  function demanderFermer() {
    if (!onFermer) return
    if (envoiEnCours || nonPartis || lecturesEnCours) setBande(true)
    else onFermer()
  }

  const idTitre = `dd-t-${dossier.app_dossier_id}`
  const coque = (contenu: ReactNode, pied: ReactNode) => {
    const fenetre = (
      <section
        ref={fenetreRef}
        tabIndex={-1}
        className={`ged-depot dd${modale ? ' is-modale' : ''}${survol ? ' is-survol' : ''}`}
        role={modale ? 'dialog' : undefined}
        aria-modal={modale || undefined}
        aria-labelledby={idTitre}
        onKeyDown={(e) => { if (modale && e.key === 'Escape') { e.stopPropagation(); demanderFermer() } }}
        onDragOver={(e) => { e.preventDefault(); setSurvol(true) }}
        onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setSurvol(false) }}
        onDrop={deposer}
      >
        <header className="dd-hd">
          <div className="dd-hd-t">
            <p>{`${[dossier.titre_bien, dossier.ville].filter(Boolean).join(', ')}, réf. ${dossier.hektor_annonce_id}`}</p>
            <h2 id={idTitre}>Déposer des documents</h2>
          </div>
          {contexte ? <span className="dd-hd-pil">{LIBELLE_MOMENT[contexte.moment]}</span> : null}
          {dossier.numero_mandat ? <span className="dd-hd-pil">{`Mandat ${dossier.numero_mandat}`}</span> : null}
          {modale ? (
            <button type="button" className="dd-hd-x" aria-label="Fermer" onClick={demanderFermer}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
            </button>
          ) : null}
        </header>
        <div className="dd-c">{contenu}</div>
        {pied}
        {survol ? <div className="dd-lache" aria-hidden="true"><span>Lâche les fichiers ici</span></div> : null}
      </section>
    )
    return modale ? createPortal(<div className="dd-voile">{fenetre}</div>, document.body) : fenetre
  }

  if (erreurTypes) {
    return coque(
      <>
        <p className="ged-depot-alerte">{`La nouvelle fenêtre de dépôt n'a pas pu lire la liste des types (${erreurTypes}). Le formulaire habituel reste disponible :`}</p>
        {formulaireClassique}
      </>,
      modale ? <footer className="dd-pied"><span className="dd-pied-t" /><button type="button" className="dd-b2" onClick={() => onFermer?.()}>Fermer</button></footer> : null,
    )
  }

  const nomsDuDossier = documents.filter((d) => d.present_in_hektor !== false).map((d) => d.document_name)

  // Le refus et le conflit de nom se recalculent à chaque changement : un nom ne doit contenir aucun autre nom
  // du dossier ni du lot (voir nomEnConflit).
  const verifier = (liste: Ligne[]): Ligne[] => liste.map((l, i) => {
    if (l.etat !== 'pret') return l
    const nomFinal = `${l.nom.trim()}${extension(l.file.name)}`
    const autres = [...nomsDuDossier, ...liste.filter((x, j) => j !== i && x.aEnvoyer && x.etat !== 'echec').map((x) => `${x.nom.trim()}${extension(x.file.name)}`)]
    let refus: string | null = null
    if (!GED_TYPES_ACCEPTES.has(l.file.type)) refus = 'Format refusé par le coffre (PDF, image, Word, Excel, texte ou zip seulement).'
    else if (l.file.size > GED_TAILLE_MAX) refus = 'Fichier trop lourd : 50 Mo au plus.'
    else if (!l.nom.trim()) refus = 'Donne un nom au document.'
    else if (!l.type) refus = 'Choisis le type du document.'
    else {
      const conflit = nomEnConflit(nomFinal, autres)
      if (conflit) refus = `Le nom touche « ${conflit} » (l'un contient l'autre) : un réessai d'envoi pourrait les confondre. Change le nom.`
    }
    return { ...l, refus }
  })

  // Choisir un type sur une ligne : un nom muet prend le nom proposé (ou le type et la date) tant que l'utilisateur ne
  // l'a pas écrit lui-même ; une pièce des personnes part TOUJOURS en privé.
  function avecType(l: Ligne, code: string, nomPropose?: string | null): Ligne {
    const suivante = { ...l, type: code }
    if (code && !l.nomTouche && (l.forceNom === 'muet' || l.forceNom === 'reste')) {
      suivante.nom = nomPropose?.trim() || `${parCode.get(code)?.libelle ?? 'Document'} ${aujourdhui()}`
    }
    if (code && parCode.get(code)?.sensible) suivante.visibilite = 'private'
    return suivante
  }

  async function lireParIa(ligne: Ligne) {
    modifierEtat(ligne.id, { ia: { etat: 'lecture' } })
    try {
      const prep = await preparerPourIa(ligne.file, parCode.get(ligne.type)?.lecture === 'jamais_envoye')
      if (!prep.envoyable) {
        setLignes((avant) => verifier(avant.map((l) => {
          if (l.id !== ligne.id) return l
          const base: Ligne = { ...l, ia: { etat: 'non_envoye', raison: prep.raison } }
          // un IBAN trouvé chez nous vaut un RIB reconnu : pré-choisi si personne n'a choisi -- SAUF une pièce de financement
          // reconnue à son nom (lot 9d, décision du 16/11) : une offre de prêt porte souvent l'IBAN du compte de prélèvement ;
          // elle reste « Financement », et ne part pas plus à l'IA (la garde RIB refuse toujours l'envoi)
          const financementParNom = l.type === 'transaction.financement'
          return prep.rib && l.etat === 'pret' && !l.typeTouche && !l.typeAttenduPose && !financementParNom && parCode.has('justif.rib') ? avecType(base, 'justif.rib') : base
        })))
        return
      }
      const r = await classerParIa(prep, ligne.file.name, dossier.hektor_annonce_id)
      setLignes((avant) => verifier(avant.map((l) => {
        if (l.id !== ligne.id) return l
        const base: Ligne = { ...l, ia: { etat: 'fait', r } }
        if (l.etat !== 'pret' || !parCode.has(r.typeCode)) return base
        const enregistre: Ligne = { ...base, typePropose: r.typeCode, typeProposePar: 'ia' }
        return preChoisirTypeIa({ forceNom: l.forceNom, typeTouche: l.typeTouche, typeAttendu: l.typeAttenduPose }, r)
          ? avecType(enregistre, r.typeCode, r.nomPropose)
          : enregistre
      })))
    } catch (e) {
      modifierEtat(ligne.id, { ia: { etat: 'erreur', raison: e instanceof Error ? e.message : String(e) } })
    }
  }

  async function ligneNeuve(file: File): Promise<Ligne> {
    const propose = typeParNom(file.name)
    const sha256 = await empreinteFichier(file).catch(() => null)
    const doublon = sha256 ? documents.find((d) => d.sha256 === sha256) ?? null : null
    return {
      id: crypto.randomUUID(),
      file,
      nom: racine(file.name).replace(/[_]+/g, ' ').trim(),
      nomTouche: false,
      type: propose.code ?? '',
      typeTouche: false,
      typeAttenduPose: false,
      typeNom: propose.code,
      typePropose: propose.code,
      typeProposePar: propose.code ? 'nom' : null,
      ia: null,
      lecture: null,
      forceNom: propose.force,
      visibilite: 'private',
      sha256,
      doublonDe: doublon ? doublon.document_name : null,
      aEnvoyer: !doublon,
      refus: null,
      etat: 'pret',
      message: null,
      jobId: null,
    }
  }

  // Un PDF qui réunit plusieurs pièces (dit par l'IA) devient autant de fichiers, un clic, à la place de l'original.
  async function separer(ligne: Ligne, r: ResultatIa) {
    setMessage(null)
    try {
      const fichiers = await separerPdf(ligne.file, r.pieces, (i) => `${racine(ligne.file.name)} - partie ${i + 1}`)
      const nouvelles: Ligne[] = []
      for (const [i, file] of fichiers.entries()) {
        const code = r.pieces[i].typeCode
        const neuve = await ligneNeuve(file)
        const muette: Ligne = { ...neuve, forceNom: 'muet', typeNom: null, typePropose: code, typeProposePar: 'ia', ia: { etat: 'fait', r: { ...r, typeCode: code, nomPropose: null, pieces: [] } } }
        nouvelles.push(avecType(muette, code))
      }
      setLignes((avant) => verifier(avant.flatMap((l) => (l.id === ligne.id ? nouvelles : [l]))))
    } catch (e) {
      setMessage(`Le fichier n'a pas pu être séparé : ${e instanceof Error ? e.message : String(e)}`)
    }
  }

  async function ajouterFichiers(fichiers: File[]) {
    setMessage(null)
    const nouvelles: Ligne[] = []
    for (const brut of fichiers) {
      let file = brut
      // une image dans un format que le coffre refuse (HEIC…) : redessinée en JPEG si le navigateur la lit
      if (file.type.startsWith('image/') && !GED_TYPES_ACCEPTES.has(file.type)) {
        const jpeg = await versJpeg(file)
        if (jpeg) file = new File([jpeg], `${racine(file.name)}.jpg`, { type: 'image/jpeg' })
      }
      const neuve = await ligneNeuve(file)
      const attendu = typeAttendu && parCode.has(typeAttendu.code) ? typeAttendu.code : null
      nouvelles.push(attendu ? { ...avecType(neuve, attendu), typeAttenduPose: true } : avecType(neuve, neuve.type))
    }
    setLignes((avant) => verifier([...avant, ...nouvelles]))
    if (typeAttendu && nouvelles.length) onTypeAttenduUtilise?.()
  }

  function modifier(id: string, patch: Partial<Ligne>) {
    setLignes((avant) => verifier(avant.map((l) => {
      if (l.id !== id) return l
      const suivante = { ...l, ...patch }
      // un type choisi : le nom muet suit, la pièce des personnes reste privée (avecType)
      return patch.type !== undefined ? avecType(suivante, patch.type) : suivante
    })))
  }

  async function assemblerPages() {
    if (!pages.length) return
    setAssemblage(true)
    try {
      const pdf = await photosEnPdf(pages)
      setPages([])
      await ajouterFichiers([pdf])
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e))
    } finally {
      setAssemblage(false)
    }
  }

  async function envoyer() {
    const aPartir = lignes.filter((l) => l.etat === 'pret' && l.aEnvoyer && !l.refus)
    if (!aPartir.length) return
    if (!peutEnvoyer()) return
    setEnvoiEnCours(true)
    setMessage(null)
    setLot(aPartir.map((l) => l.id))
    // un fichier APRÈS l'autre, jamais en parallèle (réponse de la session signature, 12/11)
    for (const ligne of aPartir) {
      modifierEtat(ligne.id, { etat: 'envoi', message: null })
      let job: ConsoleJob
      try {
        job = await createUploadDocumentToHektorJob({
          dossier,
          file: ligne.file,
          visibility: ligne.visibilite,
          documentLabel: ligne.nom.trim(),
          documentType: parCode.get(ligne.type)?.libelle ?? null,
          priority: 20,
        })
        onJobCreated?.(job)
      } catch (e) {
        modifierEtat(ligne.id, { etat: 'echec', message: e instanceof Error ? e.message : String(e) })
        continue
      }
      try {
        await gedClasser({
          jobId: job.id,
          typeCode: ligne.type,
          typePropose: ligne.typePropose,
          typeProposePar: ligne.typePropose ? ligne.typeProposePar : null,
          sha256: ligne.sha256,
        })
        modifierEtat(ligne.id, { etat: 'envoye', jobId: job.id, message: null, lecture: lectureIa && typeLu(ligne.type) ? { etat: 'attente' } : null })
      } catch (e) {
        modifierEtat(ligne.id, { etat: 'classement_echec', jobId: job.id, message: e instanceof Error ? e.message : String(e) })
      }
    }
    setEnvoiEnCours(false)
    onTermine?.()
  }

  // Morceau 6 : lire les valeurs d'un document envoyé (le serveur écrit la lecture ; rien ne s'écrit sur le bien).
  async function lireValeurs(ligne: Ligne) {
    if (!ligne.jobId) return
    modifierEtat(ligne.id, { lecture: { etat: 'lecture' } })
    try {
      const prep = await preparerLecture(ligne.file, ligne.type)
      if (!prep.lisible) { modifierEtat(ligne.id, { lecture: { etat: 'erreur', raison: prep.raison } }); return }
      const r = await lireValeursParIa(ligne.jobId, prep, ligne.file.name)
      modifierEtat(ligne.id, { lecture: { etat: 'fait', resume: resumeLecture({ typeCode: ligne.type, etat: r.etat, valeurs: r.valeurs }) } })
    } catch (e) {
      modifierEtat(ligne.id, { lecture: { etat: 'erreur', raison: e instanceof Error ? e.message : String(e) } })
    }
  }

  async function reclasser(ligne: Ligne) {
    if (!ligne.jobId) return
    modifierEtat(ligne.id, { message: null })
    try {
      await gedClasser({ jobId: ligne.jobId, typeCode: ligne.type, typePropose: ligne.typePropose, typeProposePar: ligne.typePropose ? ligne.typeProposePar : null, sha256: ligne.sha256 })
      modifierEtat(ligne.id, { etat: 'envoye', message: null, lecture: lectureIa && typeLu(ligne.type) ? { etat: 'attente' } : null })
    } catch (e) {
      modifierEtat(ligne.id, { message: e instanceof Error ? e.message : String(e) })
    }
  }

  function modifierEtat(id: string, patch: Partial<Ligne>) {
    setLignes((avant) => avant.map((l) => (l.id === id ? { ...l, ...patch } : l)))
  }

  function retirer(id: string) {
    setLignes((avant) => verifier(avant.filter((l) => l.id !== id)))
  }

  function deposer(e: DragEvent<HTMLElement>) {
    e.preventDefault()
    setSurvol(false)
    if (erreurTypes) return
    const fichiers = Array.from(e.dataTransfer.files ?? [])
    if (fichiers.length) void ajouterFichiers(fichiers)
  }

  // D'où vient le type de la ligne, en clair (l'IA ne change jamais un type choisi : elle le montre).
  function sourceType(l: Ligne): string {
    if (!l.type) return l.forceNom === 'muet' ? 'le nom ne dit rien : choisis le type' : 'choisis le type'
    const parIa = l.ia?.etat === 'fait' && l.ia.r.typeCode === l.type
    const parNom = l.typeNom === l.type
    if (parIa && parNom) return "le nom et l'IA sont d'accord"
    if (l.typeTouche) return 'choisi par toi'
    if (l.typeAttenduPose) return 'la pièce demandée dans « Le dossier »'
    if (parIa) return "proposé par l'IA, à vérifier"
    if (parNom) return `reconnu par le nom${l.forceNom === 'probable' ? ', à confirmer' : ''}`
    return ''
  }

  // Ce que l'IA a dit, sous la ligne. L'avis (« Prendre ce type ») et la raison d'un non-envoi vivent dans l'aperçu ;
  // au téléphone, où l'aperçu est loin, ils restent aussi sur la ligne (dd-seul-tel).
  function etatIa(l: Ligne): ReactNode {
    const ia = l.ia
    if (!ia || ia.etat === 'lecture') return null
    if (ia.etat === 'non_envoye') return <span className="ged-depot-ia dd-seul-tel">{ia.raison}</span>
    if (ia.etat === 'erreur') {
      return (
        <span className="ged-depot-ia">
          {`L'IA n'a pas répondu (${ia.raison}) : choisis le type.`}
          <button className="dd-lien" type="button" onClick={() => modifierEtat(l.id, { ia: null })}>Redemander</button>
        </span>
      )
    }
    const r = ia.r
    return (
      <>
        {!r.lisible ? <span className="ged-depot-ia">L'IA n'a pas pu reconnaître ce document : choisis le type.</span> : null}
        {avisIa(l) ? <span className="ged-depot-ia is-avis dd-seul-tel">{avisTexte(l, r)}</span> : null}
        {r.pieces.length >= 2 && l.file.type === 'application/pdf' ? (
          <span className="ged-depot-ia is-avis">
            {`Ce fichier réunit ${r.pieces.length} pièces : ${r.pieces.map((p) => `${parCode.get(p.typeCode)?.libelle ?? p.typeCode} (p. ${p.pageDebut}${p.pageFin > p.pageDebut ? ` à ${p.pageFin}` : ''})`).join(', ')}.`}
            <button className="dd-lien" type="button" disabled={envoiEnCours} onClick={() => void separer(l, r)}>{`Séparer en ${r.pieces.length} fichiers`}</button>
          </span>
        ) : null}
      </>
    )
  }

  function avisTexte(l: Ligne, r: ResultatIa): ReactNode {
    return (
      <>
        {`L'IA pense : ${parCode.get(r.typeCode)?.libelle ?? r.typeCode} (confiance ${r.confiance}).`}
        <button className="dd-lien" type="button" onClick={() => modifier(l.id, { type: r.typeCode, typeTouche: true })}>Prendre ce type</button>
      </>
    )
  }

  // La pastille d'état de la ligne : un mot, la suite est dite dessous.
  function etatLigne(l: Ligne): { cle: string; texte: string } {
    if (l.etat === 'envoi') return { cle: 'envoi', texte: 'Envoi…' }
    if (l.etat === 'envoye') return { cle: 'envoye', texte: 'Déposé, part chez Hektor' }
    if (l.etat === 'classement_echec') return { cle: 'echec', texte: 'Type non enregistré' }
    if (l.etat === 'echec') return { cle: 'echec', texte: 'Pas envoyé' }
    if (!l.aEnvoyer) return { cle: 'deja', texte: 'Déjà dans ce dossier' }
    if (l.refus) return { cle: 'corriger', texte: 'À corriger' }
    if (l.ia?.etat === 'lecture') return { cle: 'lecture', texte: 'Lecture…' }
    if (avisIa(l)) return { cle: 'verif', texte: 'À vérifier' }
    return { cle: 'pret', texte: 'Prêt' }
  }

  const prets = lignes.filter((l) => l.etat === 'pret' && l.aEnvoyer && !l.refus).length
  const bloques = lignes.filter((l) => l.etat === 'pret' && l.aEnvoyer && l.refus).length
  const aVerifier = lignes.filter((l) => l.etat === 'pret' && l.aEnvoyer && !l.refus && avisIa(l)).length
  const dejaLa = lignes.filter((l) => l.etat === 'pret' && !l.aEnvoyer).length
  const iaLit = lignes.some((l) => l.ia?.etat === 'lecture')
  const nouvelleVersion = () => { versionInput.current += 1; forcer((n) => n + 1) }

  const choisirFichiers = (classe: string) => (
    <label className={classe}>
      Choisir des fichiers
      <input
        key={`f-${versionInput.current}`}
        type="file"
        multiple
        onChange={(e) => { const f = Array.from(e.target.files ?? []); nouvelleVersion(); if (f.length) void ajouterFichiers(f) }}
      />
    </label>
  )
  const photographier = (classe: string, libelle = 'Photographier une page') => (
    <label className={`${classe} ged-depot-camera`}>
      {libelle}
      <input
        key={`c-${versionInput.current}`}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={(e) => { const f = Array.from(e.target.files ?? []); nouvelleVersion(); if (f.length) setPages((p) => [...p, ...f]) }}
      />
    </label>
  )

  const cadenas = (ouvert: boolean) => (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d={ouvert ? 'M8 11V7a4 4 0 0 1 7.5-2' : 'M8 11V7a4 4 0 0 1 8 0v4'} /></svg>
  )

  const ligneVue = (l: Ligne, i: number) => {
    const t = l.type ? parCode.get(l.type) : undefined
    const fige = l.etat !== 'pret'
    const etat = etatLigne(l)
    const a = apercus[l.id]
    const nbPages = typeof a === 'object' ? a.nbPages : null
    const ton = !l.type ? 'vide' : avisIa(l) || (l.ia?.etat === 'fait' && l.ia.r.typeCode === l.type && l.typeNom !== l.type && !l.typeTouche) ? 'verif' : 'ok'
    const prive = l.visibilite === 'private'
    const source = sourceType(l)
    return (
      <li
        key={l.id}
        className={`ged-depot-ligne dd-l is-${l.etat} is-e-${etat.cle}${l.aEnvoyer ? '' : ' is-ecartee'}${selection?.id === l.id ? ' is-choisi' : ''}`}
        style={{ animationDelay: `${Math.min(i, 8) * 90}ms` }}
        onClick={() => setChoisi(l.id)}
        onFocusCapture={() => setChoisi(l.id)}
      >
        <button type="button" className="dd-vign" aria-label={`Voir l'aperçu de ${l.file.name}`} aria-pressed={selection?.id === l.id}>
          <span /><span /><span /><span />
        </button>
        <div className="dd-corps">
          <label className="dd-nom">
            <span className="dd-sr">Nom chez Hektor</span>
            <input value={l.nom} disabled={fige} onChange={(e) => modifier(l.id, { nom: e.target.value, nomTouche: true })} />
          </label>
          <span className="dd-fic" title={l.file.name}>{`${l.file.name}, ${taille(l.file.size)}${nbPages ? `, ${nbPages} page${nbPages > 1 ? 's' : ''}` : ''}`}</span>
          <div className="dd-type">
            <label className={`dd-pil is-${ton}`}>
              <span className="dd-sr">Type</span>
              <select value={l.type} disabled={fige || !types} onChange={(e) => modifier(l.id, { type: e.target.value, typeTouche: true })}>
                <option value="">{l.forceNom === 'muet' ? 'Nom muet : choisis le type' : 'Choisis le type'}</option>
                {familles.map(([famille, liste]) => (
                  <optgroup key={famille} label={GED_FAMILLES[famille] ?? famille}>
                    {liste.map((x) => <option key={x.code} value={x.code}>{x.libelle}</option>)}
                  </optgroup>
                ))}
              </select>
            </label>
            {l.etat === 'pret' && l.ia?.etat === 'lecture'
              ? <span className="dd-lit">L'IA lit le type…</span>
              : source ? <span key={`${l.type}|${source}`} className="dd-src">{source}</span> : null}
          </div>
          <div className="ged-depot-etat dd-dit">
            {l.etat === 'pret' && l.aEnvoyer && l.refus ? <span className="ged-depot-refus">{l.refus}</span> : null}
            {l.etat === 'pret' ? etatIa(l) : null}
            {l.etat === 'envoye' ? <span className="ged-depot-ok">Déposé chez nous, envoi chez Hektor en cours. Type enregistré.</span> : null}
            {l.etat === 'envoye' && l.lecture ? (
              <span key={l.lecture.etat} className={`ged-depot-ia${l.lecture.etat === 'fait' ? ' is-avis dd-entre' : ''}${l.lecture.etat === 'lecture' ? ' dd-lit' : ''}`}>
                {l.lecture.etat === 'attente' ? 'Lecture des valeurs à suivre…' : l.lecture.etat === 'lecture' ? "L'IA lit les valeurs…" : l.lecture.etat === 'fait' ? l.lecture.resume : `Pas lu (${l.lecture.raison}).`}
                {l.lecture.etat === 'erreur' ? <button className="dd-lien" type="button" onClick={() => modifierEtat(l.id, { lecture: { etat: 'attente' } })}>Relire</button> : null}
              </span>
            ) : null}
            {l.etat === 'classement_echec' ? (
              <span className="ged-depot-refus">
                {`Déposé, mais le type n'a pas été enregistré (${l.message ?? 'erreur'}).`}
                <button className="dd-lien" type="button" onClick={() => void reclasser(l)}>Réessayer</button>
              </span>
            ) : null}
            {l.etat === 'echec' ? <span className="ged-depot-refus">{`Pas envoyé : ${l.message ?? 'erreur'}. Le fichier reste ici.`}</span> : null}
          </div>
        </div>
        <button
          type="button"
          className={`dd-vis${t?.sensible ? ' is-verrou' : prive ? '' : ' is-public'}`}
          disabled={fige || Boolean(t?.sensible)}
          aria-label={t?.sensible ? 'Toujours privé : une pièce des personnes reste privée' : prive ? 'Privé : cliquer pour rendre public' : 'Public : cliquer pour rendre privé'}
          title={t?.sensible ? 'Une pièce des personnes reste toujours privée' : undefined}
          onClick={() => modifier(l.id, { visibilite: prive ? 'shared' : 'private' })}
        >
          {cadenas(!prive)}
          <small>{prive ? 'Privé' : 'Public'}</small>
        </button>
        <div className="dd-etat">
          <span className={`dd-badge is-${etat.cle}`}>{etat.texte}</span>
          {l.etat === 'envoi' ? <span className="dd-barre" aria-hidden="true"><span /></span> : null}
          {l.etat === 'pret' && l.doublonDe ? (
            <label className="ged-depot-doublon dd-doublon" title={`Déjà dans ce dossier : « ${l.doublonDe} »`}>
              <input type="checkbox" checked={l.aEnvoyer} onChange={(e) => modifier(l.id, { aEnvoyer: e.target.checked })} />
              {`Déjà dans ce dossier (« ${l.doublonDe} ») : l'envoyer quand même`}
            </label>
          ) : null}
          {l.etat === 'pret' || l.etat === 'echec' ? (
            <button className="dd-lien ged-depot-retirer" type="button" onClick={(e) => { e.stopPropagation(); retirer(l.id) }} disabled={envoiEnCours}>Retirer</button>
          ) : null}
        </div>
      </li>
    )
  }

  // L'aperçu de la ligne choisie : sa page 1, d'où vient son type, et ce que l'IA en dit.
  const apercuVue = (l: Ligne) => {
    const t = l.type ? parCode.get(l.type) : undefined
    const a = apercus[l.id]
    const ia = l.ia
    return (
      <aside className="dd-ap" aria-label="Aperçu">
        <b className="dd-ap-nom">{`${l.nom.trim() || racine(l.file.name)}${extension(l.file.name)}`}</b>
        <div className="dd-ap-h">
          <div className="dd-page" key={l.id}>
            {typeof a === 'object'
              ? <img src={a.image} alt={`Page 1 de ${l.file.name}`} />
              : a === 'aucun'
                ? <span className="dd-page-ext">{extension(l.file.name).slice(1).toUpperCase() || 'Fichier'}</span>
                : <span className="dd-page-lit" aria-label="Aperçu en préparation" />}
          </div>
          <dl>
            <div><dt>Type</dt><dd>{t?.libelle ?? 'Pas encore choisi'}</dd></div>
            <div><dt>D'où vient le type</dt><dd>{l.ia?.etat === 'lecture' ? "L'IA lit le type…" : sourceType(l) || '—'}</dd></div>
            <div><dt>Visibilité</dt><dd>{t?.sensible ? 'Toujours privé' : l.visibilite === 'private' ? 'Privé' : 'Public'}</dd></div>
            <div><dt>Page</dt><dd>{typeof a === 'object' ? `1 / ${a.nbPages}` : '—'}</dd></div>
            <div><dt>Taille</dt><dd>{taille(l.file.size)}</dd></div>
          </dl>
        </div>
        {l.etat === 'pret' && ia?.etat === 'fait' && avisIa(l) ? <p className="dd-ap-avis">{avisTexte(l, ia.r)}</p> : null}
        {l.etat === 'pret' && ia?.etat === 'non_envoye' ? <p className="dd-ap-rib">{ia.raison}</p> : null}
      </aside>
    )
  }

  // Le texte du pied : où en est le lot, en une phrase.
  const faitsDuLot = lignes.filter((l) => lot.includes(l.id) && l.etat !== 'pret' && l.etat !== 'envoi').length
  const piedTexte = envoiEnCours
    ? `Envoi, un fichier après l'autre (${faitsDuLot} sur ${lot.length})…`
    : !lignes.length
      ? (lectureIa ? "Le type de chaque fichier est proposé par son nom puis par l'IA ; tu le vérifies avant l'envoi." : "Le type de chaque fichier est proposé par son nom ; tu le vérifies avant l'envoi.")
      : bloques
        ? `${bloques} fichier${bloques > 1 ? 's' : ''} à corriger avant l'envoi.`
        : iaLit
          ? "L'IA lit le type de chaque fichier… Tu peux envoyer sans attendre."
          : prets
            ? "Rien n'est parti. Vérifie les types, puis envoie."
            : lecturesEnCours
              ? "Déposés chez nous, ils partent chez Hektor. L'IA lit leurs valeurs."
              : 'Déposés chez nous, ils partent chez Hektor.'

  const piedNormal = (
    <footer className="dd-pied">
      <p className={`dd-pied-t${bloques && !envoiEnCours ? ' is-refus' : ''}`} role="status">{piedTexte}</p>
      {modale ? <button type="button" className="dd-b2" onClick={demanderFermer}>Fermer</button> : null}
      <button className="dd-b1" type="button" disabled={!prets || envoiEnCours || !types} onClick={() => void envoyer()}>
        {envoiEnCours ? 'Envoi…' : prets ? `Envoyer ${prets} document${prets > 1 ? 's' : ''}` : 'Rien à envoyer'}
      </button>
    </footer>
  )
  const s = (n: number) => (n > 1 ? 's' : '')
  const piedBande = envoiEnCours ? (
    <footer className="dd-pied dd-bande" role="alert">
      <p className="dd-pied-t"><b>L'envoi n'est pas fini.</b> Attendre la fin avant de fermer ?</p>
      <button type="button" className="dd-b2" onClick={() => onFermer?.()}>Fermer quand même</button>
      <button type="button" className="dd-b1" onClick={() => setBande(false)}>Attendre</button>
    </footer>
  ) : nonPartis ? (
    <footer className="dd-pied dd-bande" role="alert">
      <p className="dd-pied-t"><b>{nonPartis > 1 ? `${nonPartis} documents ne sont pas partis.` : '1 document n\'est pas parti.'}</b>{prets ? (nonPartis > 1 ? ' Les envoyer avant de fermer ?' : ' L\'envoyer avant de fermer ?') : (nonPartis > 1 ? ' Ils sont à corriger avant l\'envoi.' : ' Il est à corriger avant l\'envoi.')}</p>
      <button type="button" className="dd-b2" onClick={() => onFermer?.()}>Fermer sans envoyer</button>
      {prets
        ? <button type="button" className="dd-b1" disabled={!types} onClick={() => { setBande(false); void envoyer() }}>Envoyer maintenant</button>
        : <button type="button" className="dd-b1" onClick={() => setBande(false)}>Revenir</button>}
    </footer>
  ) : (
    <footer className="dd-pied dd-bande" role="alert">
      <p className="dd-pied-t"><b>{`L'IA lit encore ${lecturesEnCours} document${s(lecturesEnCours)}.`}</b>{lecturesEnCours > 1 ? ' Ils sont déposés ; fermer arrête leur lecture.' : ' Il est déposé ; fermer arrête sa lecture.'}</p>
      <button type="button" className="dd-b2" onClick={() => onFermer?.()}>Fermer quand même</button>
      <button type="button" className="dd-b1" onClick={() => setBande(false)}>Attendre</button>
    </footer>
  )
  const bandeUtile = bande && (envoiEnCours || nonPartis > 0 || lecturesEnCours > 0)

  return coque(
    <>
      {typeAttendu ? (
        <div className="dd-attendu">
          <span>{`Prochain fichier : ${typeAttendu.libelle}`}</span>
          <button className="dd-lien" type="button" onClick={() => onTypeAttenduUtilise?.()}>Annuler</button>
        </div>
      ) : null}

      {pages.length ? (
        <div className="dd-attendu dd-pages">
          <span>{`${pages.length} page${pages.length > 1 ? 's' : ''} photographiée${pages.length > 1 ? 's' : ''} : elles formeront un seul document.`}</span>
          <button className="dd-b1 is-petit" type="button" disabled={assemblage} onClick={() => void assemblerPages()}>
            {assemblage ? 'Assemblage…' : `Faire un PDF de ${pages.length} page${pages.length > 1 ? 's' : ''}`}
          </button>
          <button className="dd-lien" type="button" disabled={assemblage} onClick={() => setPages([])}>Annuler les photos</button>
        </div>
      ) : null}

      {/* H4 (16/11, planche « Téléphone ») : au téléphone, les pages photographiées montent dans un panneau du bas -- les
          vraies vignettes, l'éclair au retour de l'appareil, « Ajouter une page (le verso) ». Mêmes gestes que la bande
          ci-dessus (masquée sous 760 px) : l'appareil photo du téléphone, « Faire un PDF », « Annuler les photos ». */}
      {pages.length ? createPortal(
        <div className="dd-feuille-voile">
          <section className="dd-feuille" role="dialog" aria-modal="true" aria-labelledby={`${idTitre}-photo`}>
            <span className="dd-feuille-poignee" aria-hidden="true" />
            <header className="dd-hd dd-feuille-hd">
              <div className="dd-hd-t">
                <p>{dossier.titre_bien}</p>
                <h2 id={`${idTitre}-photo`}>Photographier une page</h2>
              </div>
            </header>
            <div className="dd-feuille-c">
              <p className="dd-feuille-t">{`${pages.length} page${s(pages.length)} : un seul document`}</p>
              <div className="dd-vignettes">
                {vignettesPages.map((u, i) => (
                  <span key={u} className="dd-vp">
                    <img src={u} alt={`Page ${i + 1}`} onError={(e) => { e.currentTarget.style.visibility = 'hidden' }} />
                    <b>{i + 1}</b>
                  </span>
                ))}
              </div>
              <p className="dd-feuille-note">Le recto, puis le verso : chaque photo devient une page du même PDF.</p>
            </div>
            <footer className="dd-feuille-pied">
              {photographier('dd-b2', 'Ajouter une page (le verso)')}
              <button className="dd-b1" type="button" disabled={assemblage} onClick={() => void assemblerPages()}>
                {assemblage ? 'Assemblage…' : `Faire un PDF de ${pages.length} page${s(pages.length)}`}
              </button>
              <button className="dd-lien" type="button" disabled={assemblage} onClick={() => setPages([])}>Annuler les photos</button>
            </footer>
            <span key={pages.length} className="dd-flash" aria-hidden="true" />
          </section>
        </div>,
        document.body,
      ) : null}

      {types === null ? <p className="ged-depot-note">Chargement des types…</p> : null}
      {message ? <p className="ged-depot-alerte">{message}</p> : null}

      {lignes.length ? (
        <>
          <div className="dd-compte">
            <b>{`${lignes.length} fichier${s(lignes.length)}`}</b>
            {prets - aVerifier > 0 ? <span className="dd-badge is-pret">{`${prets - aVerifier} prêt${s(prets - aVerifier)}`}</span> : null}
            {aVerifier ? <span className="dd-badge is-verif">{`${aVerifier} à vérifier`}</span> : null}
            {bloques ? <span className="dd-badge is-corriger">{`${bloques} à corriger`}</span> : null}
            {dejaLa ? <span className="dd-badge is-deja">{`${dejaLa} déjà dans ce dossier`}</span> : null}
            <span className="dd-esp" />
            {choisirFichiers('dd-b2 is-petit')}
            {photographier('dd-b2 is-petit')}
          </div>
          <div className="dd-grille">
            <ul className="ged-depot-liste dd-liste">{lignes.map(ligneVue)}</ul>
            {selection ? apercuVue(selection) : null}
          </div>
        </>
      ) : (
        <>
          <div className="ged-depot-zone dd-zone">
            <span className="dd-zone-ic" aria-hidden="true">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 15V4" /><path d="M7 9l5-5 5 5" /><path d="M5 15v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3" /></svg>
            </span>
            <strong>Glisse les fichiers ici</strong>
            <span>PDF ou photos, un seul ou tout un lot. Rien ne part avant ton clic sur « Envoyer ».</span>
            <span className="dd-zone-b">
              {choisirFichiers('dd-b1')}
              {photographier('dd-b2')}
            </span>
            <small>Au téléphone, « Photographier une page » autant de fois que de pages.</small>
          </div>
          {contexte?.nonTrouvees.length ? (
            <p className="dd-nontrouvees">
              {`Non trouvées pour « ${LIBELLE_MOMENT[contexte.moment]} » :`}
              {contexte.nonTrouvees.map((n) => <span key={n}>{n}</span>)}
            </p>
          ) : null}
        </>
      )}
    </>,
    bandeUtile ? piedBande : piedNormal,
  )
}
