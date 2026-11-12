// GED (12/11/2026, morceau 2) -- LA FENÊTRE DE DÉPÔT : plusieurs fichiers d'un coup, des photos de plusieurs pages
// assemblées en un seul PDF, le type et le nom proposés d'après le nom du fichier, le doublon reconnu, les pièces des
// personnes toujours en privé. Derrière l'interrupteur `ged_depot_multiple` (cran « admin » = Frédéric seul) : éteint,
// le panneau garde son formulaire d'aujourd'hui, inchangé.
// ⭐ L'ENVOI NE CHANGE PAS : chaque fichier part par createUploadDocumentToHektorJob, TEL QUEL, un après l'autre (le
//   chemin d'aujourd'hui : chez nous d'abord, Hektor ensuite). Puis app_ged_classer enregistre son type CHEZ NOUS.
//   Un classement raté n'empêche jamais un dépôt : la ligne le dit et propose de reclasser.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.7.
import { useEffect, useMemo, useRef, useState, type DragEvent, type ReactNode } from 'react'
import { createUploadDocumentToHektorJob } from './lib/api'
import {
  empreinteFichier, gedClasser, GED_FAMILLES, GED_TAILLE_MAX, GED_TYPES_ACCEPTES, loadGedTypes, nomEnConflit,
  type GedType,
} from './lib/ged'
import { typeParNom } from './lib/gedTypeParNom'
import type { ConsoleDocument, ConsoleJob, Dossier } from './types'
import './DepotDocuments.css'

type EtatLigne = 'pret' | 'envoi' | 'envoye' | 'classement_echec' | 'echec'

type Ligne = {
  id: string
  file: File
  nom: string
  nomTouche: boolean
  type: string
  typePropose: string | null
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

  useEffect(() => {
    let annule = false
    loadGedTypes()
      .then((t) => { if (!annule) setTypes(t) })
      .catch((e) => { if (!annule) setErreurTypes(e instanceof Error ? e.message : String(e)) })
    return () => { annule = true }
  }, [])

  // « une saisie ne se perd jamais » : quitter la page avec des fichiers non envoyés demande confirmation
  useEffect(() => {
    if (!lignes.some((l) => l.etat === 'pret' && l.aEnvoyer)) return
    const avant = (e: BeforeUnloadEvent) => { e.preventDefault() }
    window.addEventListener('beforeunload', avant)
    return () => window.removeEventListener('beforeunload', avant)
  }, [lignes])

  const parCode = useMemo(() => new Map((types ?? []).map((t) => [t.code, t])), [types])
  const familles = useMemo(() => {
    const groupes = new Map<string, GedType[]>()
    for (const t of types ?? []) groupes.set(t.famille, [...(groupes.get(t.famille) ?? []), t])
    return [...groupes.entries()]
  }, [types])

  if (erreurTypes) {
    return (
      <div className="ged-depot">
        <p className="ged-depot-alerte">{`La nouvelle fenêtre de dépôt n'a pas pu lire la liste des types (${erreurTypes}). Le formulaire habituel reste disponible :`}</p>
        {formulaireClassique}
      </div>
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
      const propose = typeParNom(file.name)
      const sha256 = await empreinteFichier(file).catch(() => null)
      const doublon = sha256 ? documents.find((d) => d.sha256 === sha256) ?? null : null
      const attendu = typeAttendu && parCode.has(typeAttendu.code) ? typeAttendu.code : null
      const type = attendu ?? propose.code ?? ''
      const muet = propose.force === 'muet' || propose.force === 'reste'
      nouvelles.push({
        id: crypto.randomUUID(),
        file,
        nom: attendu && muet ? `${parCode.get(attendu)?.libelle ?? 'Document'} ${aujourdhui()}` : racine(file.name).replace(/[_]+/g, ' ').trim(),
        nomTouche: false,
        type,
        typePropose: propose.code,
        forceNom: propose.force,
        visibilite: 'private',
        sha256,
        doublonDe: doublon ? doublon.document_name : null,
        aEnvoyer: !doublon,
        refus: null,
        etat: 'pret',
        message: null,
        jobId: null,
      })
    }
    setLignes((avant) => verifier([...avant, ...nouvelles]))
    if (typeAttendu && nouvelles.length) onTypeAttenduUtilise?.()
  }

  function modifier(id: string, patch: Partial<Ligne>) {
    setLignes((avant) => verifier(avant.map((l) => {
      if (l.id !== id) return l
      const suivante = { ...l, ...patch }
      // un nom muet prend le nom du type choisi et la date, tant que l'utilisateur ne l'a pas écrit lui-même
      if (patch.type !== undefined && !l.nomTouche && (l.forceNom === 'muet' || l.forceNom === 'reste') && patch.type) {
        suivante.nom = `${parCode.get(patch.type)?.libelle ?? 'Document'} ${aujourdhui()}`
      }
      // une pièce des personnes part TOUJOURS en privé
      if (suivante.type && parCode.get(suivante.type)?.sensible) suivante.visibilite = 'private'
      return suivante
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
          typeProposePar: ligne.typePropose ? 'nom' : null,
          sha256: ligne.sha256,
        })
        modifierEtat(ligne.id, { etat: 'envoye', jobId: job.id, message: null })
      } catch (e) {
        modifierEtat(ligne.id, { etat: 'classement_echec', jobId: job.id, message: e instanceof Error ? e.message : String(e) })
      }
    }
    setEnvoiEnCours(false)
    onTermine?.()
  }

  async function reclasser(ligne: Ligne) {
    if (!ligne.jobId) return
    modifierEtat(ligne.id, { message: null })
    try {
      await gedClasser({ jobId: ligne.jobId, typeCode: ligne.type, typePropose: ligne.typePropose, typeProposePar: ligne.typePropose ? 'nom' : null, sha256: ligne.sha256 })
      modifierEtat(ligne.id, { etat: 'envoye', message: null })
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

  function deposer(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setSurvol(false)
    const fichiers = Array.from(e.dataTransfer.files ?? [])
    if (fichiers.length) void ajouterFichiers(fichiers)
  }

  const prets = lignes.filter((l) => l.etat === 'pret' && l.aEnvoyer && !l.refus).length
  const bloques = lignes.filter((l) => l.etat === 'pret' && l.aEnvoyer && l.refus).length
  const nouvelleVersion = () => { versionInput.current += 1; forcer((n) => n + 1) }

  return (
    <div className="ged-depot">
      <div className="ged-depot-tete">
        <strong>Ajouter des documents</strong>
        <small>Chaque document part chez Hektor, un après l'autre, une fois son type et son nom vérifiés.</small>
      </div>

      {typeAttendu ? (
        <div className="ged-depot-pages">
          <span>{`Prochain fichier : ${typeAttendu.libelle}`}</span>
          <button className="ghost-button" type="button" onClick={() => onTypeAttenduUtilise?.()}>Annuler</button>
        </div>
      ) : null}

      <div
        className={`ged-depot-zone${survol ? ' is-survol' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setSurvol(true) }}
        onDragLeave={() => setSurvol(false)}
        onDrop={deposer}
      >
        <span>Glisse les fichiers ici, ou</span>
        <label className="ghost-button">
          Choisir des fichiers
          <input
            key={`f-${versionInput.current}`}
            type="file"
            multiple
            onChange={(e) => { const f = Array.from(e.target.files ?? []); nouvelleVersion(); if (f.length) void ajouterFichiers(f) }}
          />
        </label>
        <label className="ghost-button ged-depot-camera">
          Photographier une page
          <input
            key={`c-${versionInput.current}`}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={(e) => { const f = Array.from(e.target.files ?? []); nouvelleVersion(); if (f.length) setPages((p) => [...p, ...f]) }}
          />
        </label>
      </div>

      {pages.length ? (
        <div className="ged-depot-pages">
          <span>{`${pages.length} page${pages.length > 1 ? 's' : ''} photographiée${pages.length > 1 ? 's' : ''} : elles formeront un seul document.`}</span>
          <button className="ghost-button button-primary" type="button" disabled={assemblage} onClick={() => void assemblerPages()}>
            {assemblage ? 'Assemblage…' : `Faire un PDF de ${pages.length} page${pages.length > 1 ? 's' : ''}`}
          </button>
          <button className="ghost-button" type="button" disabled={assemblage} onClick={() => setPages([])}>Annuler les photos</button>
        </div>
      ) : null}

      {types === null ? <p className="ged-depot-note">Chargement des types…</p> : null}

      {lignes.length ? (
        <ul className="ged-depot-liste">
          {lignes.map((l) => {
            const t = l.type ? parCode.get(l.type) : undefined
            const fige = l.etat !== 'pret'
            return (
              <li key={l.id} className={`ged-depot-ligne is-${l.etat}${l.aEnvoyer ? '' : ' is-ecartee'}`}>
                <div className="ged-depot-fichier">
                  <span className="ged-depot-fichier-nom" title={l.file.name}>{l.file.name}</span>
                  <small>{taille(l.file.size)}</small>
                </div>
                <label className="ged-depot-champ">
                  <span>Nom chez Hektor</span>
                  <input value={l.nom} disabled={fige} onChange={(e) => modifier(l.id, { nom: e.target.value, nomTouche: true })} />
                </label>
                <label className="ged-depot-champ">
                  <span>{l.typePropose && l.type === l.typePropose ? `Type (proposé d'après le nom${l.forceNom === 'probable' ? ', à confirmer' : ''})` : 'Type'}</span>
                  <select value={l.type} disabled={fige || !types} onChange={(e) => modifier(l.id, { type: e.target.value })}>
                    <option value="">{l.forceNom === 'muet' ? 'Nom muet : choisis le type' : 'Choisis le type'}</option>
                    {familles.map(([famille, liste]) => (
                      <optgroup key={famille} label={GED_FAMILLES[famille] ?? famille}>
                        {liste.map((x) => <option key={x.code} value={x.code}>{x.libelle}</option>)}
                      </optgroup>
                    ))}
                  </select>
                </label>
                <div className="ged-depot-champ">
                  <span>Visibilité</span>
                  <div className="console-segmented-control">
                    <button type="button" className={l.visibilite === 'private' ? 'is-active' : ''} disabled={fige} onClick={() => modifier(l.id, { visibilite: 'private' })}>Privé</button>
                    <button type="button" className={l.visibilite === 'shared' ? 'is-active' : ''} disabled={fige || Boolean(t?.sensible)} title={t?.sensible ? 'Une pièce des personnes reste toujours privée' : undefined} onClick={() => modifier(l.id, { visibilite: 'shared' })}>Public</button>
                  </div>
                </div>
                <div className="ged-depot-etat">
                  {l.etat === 'pret' && l.doublonDe ? (
                    <label className="ged-depot-doublon">
                      <input type="checkbox" checked={l.aEnvoyer} onChange={(e) => modifier(l.id, { aEnvoyer: e.target.checked })} />
                      {`Déjà dans ce dossier (« ${l.doublonDe} ») : l'envoyer quand même`}
                    </label>
                  ) : null}
                  {l.etat === 'pret' && l.aEnvoyer && l.refus ? <span className="ged-depot-refus">{l.refus}</span> : null}
                  {l.etat === 'envoi' ? <span>Envoi en cours…</span> : null}
                  {l.etat === 'envoye' ? <span className="ged-depot-ok">Déposé chez nous, envoi chez Hektor en cours. Type enregistré.</span> : null}
                  {l.etat === 'classement_echec' ? (
                    <span className="ged-depot-refus">
                      {`Déposé, mais le type n'a pas été enregistré (${l.message ?? 'erreur'}).`}
                      <button className="ghost-button" type="button" onClick={() => void reclasser(l)}>Réessayer</button>
                    </span>
                  ) : null}
                  {l.etat === 'echec' ? <span className="ged-depot-refus">{`Pas envoyé : ${l.message ?? 'erreur'}. Le fichier reste ici.`}</span> : null}
                  {l.etat === 'pret' || l.etat === 'echec' ? (
                    <button className="ghost-button ged-depot-retirer" type="button" onClick={() => retirer(l.id)} disabled={envoiEnCours}>Retirer</button>
                  ) : null}
                </div>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="ged-depot-note">Aucun fichier pour l'instant. Au téléphone, « Photographier une page » autant de fois que de pages.</p>
      )}

      {message ? <p className="ged-depot-alerte">{message}</p> : null}

      <div className="ged-depot-pied">
        {bloques ? <span className="ged-depot-refus">{`${bloques} fichier${bloques > 1 ? 's' : ''} à corriger avant l'envoi.`}</span> : <span />}
        <button className="ghost-button button-primary" type="button" disabled={!prets || envoiEnCours || !types} onClick={() => void envoyer()}>
          {envoiEnCours ? 'Envoi…' : prets ? `Envoyer ${prets} document${prets > 1 ? 's' : ''}` : 'Rien à envoyer'}
        </button>
      </div>
    </div>
  )
}
