import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  RefusAssistant, chercherPublicsParcours, deposerCoordonneesMandant, deposerFichier, lireFicheParcours, photosDuBienParcours, repondreParcours,
  type CaseParcours, type PhotoDuBien, type CatalogueParcours, type CoordonneesMandant, type ParcoursVue, type PropositionPublique, type QuestionParcours,
} from './lib/assistant'

// ─────────────────────────────────────────────────────────────────────────────
// 19/11/2026 (étape 4 chap. 6, P2) -- LE PARCOURS GUIDÉ DANS LA CONVERSATION : une question à la fois, des boutons.
// Maquette VALIDÉE, toile v27 (planches 5, 7, 11) : en-tête rose et fil des rubriques, compteurs « − 5 + », pastilles
// (magenta = choisie), « Je ne sais pas », « Valider » ; les réponses données en pastilles vertes « Modifier ».
// ⛔ Un clic n'appelle PAS le modèle : il part au serveur (P1), qui garde la réponse et rend la question suivante.
// ⛔ Les cases et leurs listes sont celles de la FENÊTRE de création, fournies par l'App (catalogueParcoursFenetre) : une
//   seule source. Une case que la fenêtre ne montre pas pour ce type de bien n'est pas montrée ici.
// ─────────────────────────────────────────────────────────────────────────────

type Valeurs = Record<string, unknown>
type Piece = { idTypePiece: string; typeLabel: string; surfacePiece: string; etagePiece: string; detailPiece: string }

// P4-c : les questions où un service public peut proposer quelque chose (l'intérieur, le dehors, l'énergie, la copropriété)
const QUESTIONS_PUBLIQUES = new Set(['interieur', 'dehors', 'energie', 'copropriete'])
const PILULES_MAX = 12  // au-delà, une liste se choisit dans un menu (les 29 types de bien, les agences…)
const OUI = new Set(['OUI', '1'])

const Coche = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5 10 17 19 7" /></svg>
)

/** P4-d : ce qu'une phrase gardée a fait, en mots simples (planche 7 : « gardé, lu avec tes autres phrases ») */
function direPhrase(p: { carte?: string[]; remplies?: string[]; note?: boolean }): string {
  const morceaux: string[] = []
  const n = (p.carte?.length ?? 0) + (p.remplies?.length ?? 0)
  if (p.carte?.length) morceaux.push(`${p.carte.length} case${p.carte.length > 1 ? 's' : ''} ici`)
  if (p.remplies?.length) morceaux.push(`${p.remplies.length} plus loin`)
  if (p.note) morceaux.push('le reste dans la note')
  return n || p.note ? `gardée · ${morceaux.join(', ')}` : 'gardée'
}

function texte(v: unknown): string {
  return v === null || v === undefined ? '' : String(v)
}

/** La case se montre-t-elle ? (dans le catalogue de ce type de bien, et sa condition « si » remplie) */
function montree(c: CaseParcours | undefined, valeurs: Valeurs): c is CaseParcours {
  return !!c && (!c.si || texte(valeurs[c.si.nom]) === c.si.vaut)
}

/** Une case oui / non (cochée = OUI ou 1) : dans « Qu'y a-t-il dehors ? », elle devient une pastille à cocher. */
function estACocher(c: CaseParcours): string | null {
  if (c.genre !== 'liste' || !c.options) return null
  const vals = c.options.map((o) => o.value).filter(Boolean)
  if (vals.length === 2 && vals.includes('OUI') && vals.includes('NON')) return 'OUI'
  if (vals.length === 1 && vals[0] === '1') return '1'
  return null
}

function libelleValeur(c: CaseParcours | undefined, v: unknown): string {
  const t = texte(v)
  return c?.options?.find((o) => o.value === t)?.label ?? t
}

/** Le résumé d'une réponse donnée, dans sa pastille verte. */
function resume(q: QuestionParcours & { etat: string | null }, reponses: Valeurs, cat: CatalogueParcours): string {
  if (q.etat === 'nsp') return 'je ne sais pas'
  if (q.etat === 'passee') return 'plus tard'
  if (q.forme === 'pieces') {
    const n = Array.isArray(reponses.composition) ? reponses.composition.length : 0
    return n ? `${n} pièce${n > 1 ? 's' : ''}` : 'aucune pièce'
  }
  if (q.forme === 'mandant') return texte(reponses.mandant_choix) === 'nouveau' ? 'nouveau mandant' : texte(reponses.mandant_choix) === 'existant' ? 'mandant existant' : 'plus tard'
  if (q.forme === 'fichiers') {  // P6 : « 8 photos · 1 masquée »
    const photos = Array.isArray(reponses.photos) ? reponses.photos as PhotoDuBien[] : []
    const masquees = photos.filter((x) => x && x.visible === false).length
    return photos.length ? `${photos.length} photo${photos.length > 1 ? 's' : ''}${masquees ? ` · ${masquees} masquée${masquees > 1 ? 's' : ''}` : ''}` : 'aucune photo'
  }
  // ses ESSENTIELS d'abord (le bien : le type, puis la rue -- pas « Vente classique »), puis le reste ; une même valeur
  // (l'adresse recopiée en privée et en publique) ne compte qu'une fois
  const essentiels = q.essentiels ?? []
  const ordre = [...essentiels, ...q.champs.filter((c) => !essentiels.includes(c))]
  const tous = ordre.filter((c) => texte(reponses[c]).trim()).map((c) => {
    const cas = cat.cases[c]
    const v = libelleValeur(cas, reponses[c])
    if (cas && estACocher(cas)) return OUI.has(texte(reponses[c])) ? cas.libelle : `pas de ${cas.libelle.toLowerCase()}`
    return cas?.genre === 'nombre' ? `${cas.libelle} : ${v}` : v
  })
  const dits = [...new Set(tous)]
  if (!dits.length) return 'rien de plus'
  return dits.slice(0, 2).join(' · ') + (dits.length > 2 ? ` +${dits.length - 2}` : '')
}

function Pilules({ c, valeur, onChange }: { c: CaseParcours; valeur: string; onChange: (v: string) => void }) {
  const options = (c.options ?? []).filter((o) => o.value !== '')
  if (options.length > PILULES_MAX) {
    return (
      <label className="asp-champ asp-champ-large">
        <span>{c.libelle}</span>
        <select value={valeur} onChange={(e) => onChange(e.target.value)}>
          <option value="">Choisir</option>
          {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </label>
    )
  }
  return (
    <div className="asp-choix" role="group" aria-label={c.libelle}>
      <span className="asp-lbl">{c.libelle}</span>
      {options.map((o) => (
        <button key={o.value} type="button" className={`asp-puce${valeur === o.value ? ' is-on' : ''}`} aria-pressed={valeur === o.value}
          onClick={() => onChange(valeur === o.value ? '' : o.value)}>{o.label}</button>
      ))}
    </div>
  )
}

// un clic = un pas, calculé sur la valeur À JOUR (deux clics rapides comptent deux, même avant le rendu suivant)
function pas(avant: unknown, delta: number): string {
  const n = Number.parseInt(texte(avant), 10)
  return Number.isNaN(n) ? String(Math.max(0, delta)) : String(Math.max(0, n + delta))
}

function Compteur({ c, valeur, onPas }: { c: CaseParcours; valeur: string; onPas: (delta: number) => void }) {
  const n = Number.parseInt(valeur, 10)
  const vide = !valeur.trim() || Number.isNaN(n)
  return (
    <div className={`asp-cp${vide ? ' is-vide' : ''}`}>
      <span>{c.libelle}</span>
      <span className="asp-cp-n">
        <button type="button" aria-label={`${c.libelle} : un de moins`} disabled={vide || n <= 0} onClick={() => onPas(-1)}>−</button>
        <b aria-live="polite">{vide ? '?' : n}</b>
        <button type="button" aria-label={`${c.libelle} : un de plus`} onClick={() => onPas(1)}>+</button>
      </span>
    </div>
  )
}

function Champ({ c, valeur, onChange }: { c: CaseParcours; valeur: string; onChange: (v: string) => void }) {
  if (c.genre === 'long') {
    return (
      <label className="asp-champ asp-champ-large">
        <span>{c.libelle}</span>
        <textarea rows={3} value={valeur} onChange={(e) => onChange(e.target.value)} />
      </label>
    )
  }
  return (
    <label className="asp-champ">
      <span>{c.libelle}</span>
      <input value={valeur} onChange={(e) => onChange(e.target.value)}
        inputMode={c.genre === 'nombre' ? (c.entier ? 'numeric' : 'decimal') : undefined} />
    </label>
  )
}

function EditeurPieces({ pieces, types, onChange }: { pieces: Piece[]; types: CatalogueParcours['typesPiece']; onChange: (p: Piece[]) => void }) {
  const maj = (i: number, cle: keyof Piece, v: string) => onChange(pieces.map((p, j) => (j !== i ? p : {
    ...p, [cle]: v, ...(cle === 'idTypePiece' ? { typeLabel: types.find((t) => t.value === v)?.label ?? '' } : {}),
  })))
  return (
    <div className="asp-pieces">
      {pieces.length ? pieces.map((p, i) => (
        <div key={i} className="asp-piece">
          <label className="asp-champ"><span>Pièce</span>
            <select value={p.idTypePiece} onChange={(e) => maj(i, 'idTypePiece', e.target.value)}>
              <option value="">Choisir</option>
              {types.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </label>
          <label className="asp-champ"><span>Surface m²</span><input inputMode="decimal" value={p.surfacePiece} onChange={(e) => maj(i, 'surfacePiece', e.target.value)} /></label>
          <label className="asp-champ"><span>Étage</span><input value={p.etagePiece} onChange={(e) => maj(i, 'etagePiece', e.target.value)} /></label>
          <label className="asp-champ asp-champ-large"><span>Détail</span><input value={p.detailPiece} onChange={(e) => maj(i, 'detailPiece', e.target.value)} /></label>
          <button type="button" className="asp-retirer" aria-label={`Retirer la pièce ${i + 1}`} onClick={() => onChange(pieces.filter((_, j) => j !== i))}>×</button>
        </div>
      )) : <p className="asp-note">Aucune pièce pour l'instant.</p>}
      <button type="button" className="asp-sec asp-ajout" onClick={() => onChange([...pieces, { idTypePiece: '', typeLabel: '', surfacePiece: '', etagePiece: '', detailPiece: '' }])}>+ Ajouter une pièce</button>
    </div>
  )
}

export type MandantTrouve = { id: string; nom: string; detail?: string }

// ── Morceau 3 (D7), planche 11 : LE MANDANT. Un contact déjà dans l'app (son NUMÉRO seul part dans les réponses) ou un
// NOUVEAU mandant : ses coordonnées vivent dans `coordonnees`, un état de l'écran qui ne part JAMAIS au serveur de
// l'assistant -- elles sont déposées au coffre privé (P3) par l'écran, avec le jeton de la personne.
const CASES_MANDANT: Array<{ cle: keyof CoordonneesMandant; libelle: string; large?: boolean }> = [
  { cle: 'nom', libelle: 'Nom' }, { cle: 'prenom', libelle: 'Prénom' }, { cle: 'email', libelle: 'E-mail (exigé par la fenêtre)' },
  { cle: 'telephone', libelle: 'Téléphone' }, { cle: 'adresse', libelle: 'Adresse', large: true }, { cle: 'cp', libelle: 'Code postal' },
  { cle: 'ville', libelle: 'Ville' },
]
const CHOIX_MANDANT: Array<[string, string]> = [['existant', "Un contact déjà dans l'app"], ['nouveau', 'Un nouveau mandant']]

function QuestionMandant({ valeurs, setValeur, coordonnees, setCoordonnees, chercher, dejaDeposees }: {
  valeurs: Valeurs
  setValeur: (nom: string, v: unknown) => void
  coordonnees: CoordonneesMandant
  setCoordonnees: (maj: (avant: CoordonneesMandant) => CoordonneesMandant) => void
  chercher?: (texte: string) => Promise<MandantTrouve[]>
  dejaDeposees: boolean
}) {
  const choix = texte(valeurs.mandant_choix)
  const [recherche, setRecherche] = useState('')
  const [trouves, setTrouves] = useState<MandantTrouve[] | null>(null)
  const [choisi, setChoisi] = useState<MandantTrouve | null>(null)
  useEffect(() => {
    if (choix !== 'existant' || !chercher || recherche.trim().length < 2) { setTrouves(null); return }
    let vivant = true
    const minuterie = window.setTimeout(() => {
      chercher(recherche.trim()).then((l) => { if (vivant) setTrouves(l) }).catch(() => { if (vivant) setTrouves([]) })
    }, 250)
    return () => { vivant = false; window.clearTimeout(minuterie) }
  }, [choix, recherche, chercher])
  const changerChoix = (v: string) => {
    setValeur('mandant_choix', v)
    if (v !== 'existant') { setValeur('mandant', ''); setChoisi(null) }
  }
  return (
    <>
      <div className="asp-choix" role="group" aria-label="Le mandant">
        {CHOIX_MANDANT.map(([v, l]) => (
          <button key={v} type="button" className={`asp-puce${choix === v ? ' is-on' : ''}`} aria-pressed={choix === v}
            onClick={() => changerChoix(choix === v ? '' : v)}>{l}</button>
        ))}
      </div>
      {choix === 'existant' ? (
        <div className="asp-mandant">
          {texte(valeurs.mandant) ? (
            <p className="asp-note">Choisi : <b>{choisi?.nom ?? `le contact n° ${texte(valeurs.mandant)}`}</b>{' '}
              <button type="button" className="asp-lien" onClick={() => { setValeur('mandant', ''); setChoisi(null) }}>Changer</button></p>
          ) : (
            <>
              <label className="asp-champ asp-champ-large"><span>Chercher dans tout le réseau (nom, téléphone, e-mail ou numéro)</span>
                <input value={recherche} onChange={(e) => setRecherche(e.target.value)} placeholder="Au moins 2 lettres" /></label>
              {trouves && !trouves.length ? <p className="asp-note">Aucun contact trouvé.</p> : null}
              {trouves?.length ? (
                <div className="asp-trouves">
                  {trouves.map((m) => (
                    <button key={m.id} type="button" className="asp-trouve" onClick={() => { setValeur('mandant', m.id); setChoisi(m) }}>
                      <b>{m.nom}</b>{m.detail ? <span>{m.detail}</span> : null}
                    </button>
                  ))}
                </div>
              ) : null}
            </>
          )}
        </div>
      ) : null}
      {choix === 'nouveau' ? (
        <div className="asp-mandant">
          <div className="asp-garde">
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
            <b>Ces cases vont directement dans la fenêtre de création. L'assistant ne les lit pas.</b>
          </div>
          {dejaDeposees ? <p className="asp-note">Des coordonnées sont déjà gardées pour la fenêtre. Les retaper les remplace ; laisser vide les garde.</p> : null}
          <div className="asp-choix" role="group" aria-label="Civilité">
            <span className="asp-lbl">Civilité</span>
            {['M.', 'Mme'].map((c) => (
              <button key={c} type="button" className={`asp-puce${coordonnees.civilite === c ? ' is-on' : ''}`} aria-pressed={coordonnees.civilite === c}
                onClick={() => setCoordonnees((avant) => ({ ...avant, civilite: avant.civilite === c ? '' : c }))}>{c}</button>
            ))}
          </div>
          <div className="asp-grille">
            {CASES_MANDANT.map((c) => (
              <label key={c.cle} className={`asp-champ${c.large ? ' asp-champ-large' : ''}`}><span>{c.libelle}</span>
                <input value={coordonnees[c.cle] ?? ''} autoComplete="off" inputMode={c.cle === 'cp' || c.cle === 'telephone' ? 'tel' : c.cle === 'email' ? 'email' : undefined}
                  onChange={(e) => { const v = e.target.value; setCoordonnees((avant) => ({ ...avant, [c.cle]: v })) }} /></label>
            ))}
          </div>
        </div>
      ) : null}
    </>
  )
}

// Le haut de la fenêtre et son adresse privée : la même rue, le même code postal, la même ville (§89, D6 : le parcours
// remplit les deux) -- proposés en recopie tant que la personne ne les a pas changés.
const RECOPIES: Record<string, string[]> = {
  adresse_haut: ['adresse'], cp: ['codeprive', 'codepublique'], ville: ['villeprivee', 'villepublique'],
}

// P6 (20/11) : LES PHOTOS DU BIEN dans le parcours (maquette v27, planche 13) -- la galerie de l'annonce, JAMAIS la fiche
//   de visite : déposées au coffre de l'assistant (comme le trombone), dans leur ordre (la 1re = couverture), visibles ou
//   masquées ; à l'ouverture, la fenêtre les reçoit à son étape 2 « Photos ». Personne ne les lit (ni scan, ni modèle).
const MAX_PHOTOS_DU_BIEN = 20
function QuestionPhotos({ parcoursId, photos, onChange }: { parcoursId: string; photos: PhotoDuBien[]; onChange: (l: PhotoDuBien[]) => void }) {
  const [apercus, setApercus] = useState<Record<string, { url: string; nom: string }>>({})
  const [absentes, setAbsentes] = useState(0)
  const [depot, setDepot] = useState<{ en: number; erreur: string | null }>({ en: 0, erreur: null })
  const choix = useRef<HTMLInputElement | null>(null)
  const derniere = useRef(photos)
  derniere.current = photos
  // les photos déjà gardées : relues au coffre (lien de lecture court) ; une photo purgée est comptée.
  // ⚠ 20/11 (§100.1, vu en réel) : la carte s'affiche d'abord avec les valeurs de la question d'AVANT (aucune photo),
  //   puis reçoit les siennes : la relecture suit donc la liste des photos SANS aperçu, pas seulement le premier rendu.
  const sansApercu = photos.filter((p) => !apercus[p.id]).map((p) => p.id).join(',')
  useEffect(() => {
    if (!sansApercu) return
    let annule = false
    photosDuBienParcours(parcoursId).then((r) => {
      if (annule) return
      setApercus((avant) => ({ ...Object.fromEntries(r.photos.map((p) => [p.id, { url: p.url, nom: p.nom }])), ...avant }))
      setAbsentes(r.absentes)
    }).catch(() => undefined)
    return () => { annule = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [parcoursId, sansApercu])
  const joindre = async (liste: FileList | null) => {
    const tous = Array.from(liste ?? [])
    const place = MAX_PHOTOS_DU_BIEN - photos.length
    const images = tous.filter((f) => /^image\/(jpeg|png|webp)$/.test(f.type))
    const refusees = tous.length - images.length
    const prises = images.slice(0, Math.max(0, place))
    if (!prises.length) {
      setDepot({ en: 0, erreur: refusees ? 'Seules les images JPEG, PNG ou WebP sont des photos du bien.' : `${MAX_PHOTOS_DU_BIEN} photos au plus, comme la fenêtre.` })
      return
    }
    setDepot({ en: prises.length, erreur: null })
    const deposees: PhotoDuBien[] = []
    const erreurs: string[] = []
    for (const f of prises) {
      try {
        const d = await deposerFichier(f)
        setApercus((avant) => ({ ...avant, [d.id]: { url: URL.createObjectURL(f), nom: f.name } }))
        deposees.push({ id: d.id, visible: true })
      } catch (e) {
        erreurs.push(e instanceof Error ? e.message : `« ${f.name} » n'a pas pu être déposée.`)
      }
    }
    onChange([...derniere.current, ...deposees].slice(0, MAX_PHOTOS_DU_BIEN))
    setDepot({ en: 0, erreur: erreurs.length ? erreurs.join(' ') : refusees ? `${refusees} fichier(s) ignoré(s) : ce ne sont pas des images.`
      : images.length > prises.length ? `${MAX_PHOTOS_DU_BIEN} photos au plus : ${images.length - prises.length} non jointe(s).` : null })
  }
  const masquees = photos.filter((p) => !p.visible).length
  return (
    <div className="asp-photos">
      <input ref={choix} type="file" hidden multiple accept="image/jpeg,image/png,image/webp"
        onChange={(e) => { void joindre(e.target.files); e.target.value = '' }} />
      {photos.length ? (
        <ul className="asp-galerie" aria-label="Les photos du bien">
          {photos.map((p, i) => (
            <li key={p.id} className={p.visible ? '' : 'is-masquee'}>
              {apercus[p.id] ? <img src={apercus[p.id].url} alt={apercus[p.id].nom} /> : <span className="asp-galerie-vide" aria-hidden="true" />}
              {i === 0 ? <em className="asp-couv">couverture</em> : null}
              {!p.visible ? <em className="asp-masq">masquée</em> : null}
              <span className="asp-galerie-actions">
                <button type="button" onClick={() => onChange(photos.map((x) => (x.id === p.id ? { ...x, visible: !x.visible } : x)))}>{p.visible ? 'Masquer' : 'Afficher'}</button>
                {i > 0 ? <button type="button" onClick={() => onChange([p, ...photos.filter((x) => x.id !== p.id)])}>En couverture</button> : null}
                <button type="button" onClick={() => onChange(photos.filter((x) => x.id !== p.id))} aria-label={`Retirer ${apercus[p.id]?.nom ?? 'la photo'}`}>Retirer</button>
              </span>
            </li>
          ))}
        </ul>
      ) : <p className="asp-note">Les <b>photos du bien</b> : la galerie de l'annonce (salon, façade, jardin…). Pas la fiche de visite : elle se lit plus haut.</p>}
      <div className="asp-photos-pied">
        <span>{photos.length ? `${photos.length} photo${photos.length > 1 ? 's' : ''} jointe${photos.length > 1 ? 's' : ''}${masquees ? ` · ${masquees} masquée${masquees > 1 ? 's' : ''}` : ''} · la 1re en couverture` : ''}
          {depot.en ? ` Je dépose ${depot.en} photo${depot.en > 1 ? 's' : ''}…` : ''}</span>
        <button type="button" className="asp-sec" disabled={!!depot.en || photos.length >= MAX_PHOTOS_DU_BIEN} onClick={() => choix.current?.click()}>
          {photos.length ? 'En ajouter' : 'Joindre les photos du bien'}</button>
      </div>
      {absentes ? <p className="asp-note asp-photos-ko">{absentes > 1 ? `${absentes} photos n'étaient plus au coffre (les dépôts sont gardés 2 jours) : rejoins-les.` : "Une photo n'était plus au coffre (les dépôts sont gardés 2 jours) : rejoins-la."}</p> : null}
      {depot.erreur ? <p className="asp-note asp-photos-ko" role="alert">{depot.erreur}</p> : null}
    </div>
  )
}

function valeursDe(q: QuestionParcours, reponses: Valeurs): Valeurs {
  const v: Valeurs = {}
  for (const c of q.champs) v[c] = c === 'composition' || c === 'photos' ? (Array.isArray(reponses[c]) ? reponses[c] : []) : texte(reponses[c])
  return v
}

export type ParcoursGuideProps = {
  vue: ParcoursVue
  catalogue: (profil: string | null) => CatalogueParcours
  onVue: (vue: ParcoursVue) => void
  /** Morceau 4 : « Ouvrir la fenêtre remplie » (l'App la remplit avec les réponses) */
  onOuvrirFenetre?: (vue: ParcoursVue) => void
  onOuvrirBien?: (appDossierId: string) => void
  /** Morceau 3 : chercher un mandant existant dans tout le réseau (la recherche de la fenêtre) */
  chercherMandants?: (texte: string) => Promise<MandantTrouve[]>
  /** P4-b : le trombone est ouvert à ce compte -> « Lire la fiche de visite » (sinon, la bande ne s'affiche pas) */
  ficheOuverte?: boolean
  /** P4-d : la question OUVERTE (ou aucune) -- la zone du bas y envoie les phrases libres */
  onQuestion?: (parcoursId: string, question: { id: string; titre: string } | null) => void
}

export default function ParcoursGuide({ vue, catalogue, onVue, onOuvrirFenetre, onOuvrirBien, chercherMandants, ficheOuverte, onQuestion }: ParcoursGuideProps) {
  const cat = useMemo(() => catalogue(vue.profil), [catalogue, vue.profil])
  const [ouverte, setOuverte] = useState<string | null>(null)  // une réponse déjà donnée que l'on modifie
  const q = ouverte ? vue.questions.find((x) => x.id === ouverte) ?? null : vue.question
  const [valeurs, setValeurs] = useState<Valeurs>(() => (q ? valeursDe(q, vue.reponses) : {}))
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  // ⛔ les coordonnées d'un nouveau mandant : un état À PART, jamais dans `valeurs` (qui part au serveur de l'assistant)
  const [coordonnees, setCoordonnees] = useState<CoordonneesMandant>({})
  // P4-b : des coordonnées lues sur la fiche sont DÉJÀ au coffre
  const [deposees, setDeposees] = useState(Boolean(vue.fiche?.coffre))
  useEffect(() => { if (vue.fiche?.coffre) setDeposees(true) }, [vue.fiche?.coffre])
  // P4-b : la fiche papier jointe pendant le parcours (déposée au trombone, puis lue par le scan côté serveur)
  const [fiche, setFiche] = useState<{ etat: 'repos' | 'depot' | 'lecture'; erreur: string | null }>({ etat: 'repos', erreur: null })
  const choixFiche = useRef<HTMLInputElement | null>(null)
  const lireFiche = async (liste: FileList | null) => {
    const photos = Array.from(liste ?? []).slice(0, 5)
    if (!photos.length) return
    setFiche({ etat: 'depot', erreur: null })
    try {
      const joints = await Promise.all(photos.map((f) => deposerFichier(f)))
      setFiche({ etat: 'lecture', erreur: null })
      onVue(await lireFicheParcours(vue.id, joints.map((d) => d.id)))
      setFiche({ etat: 'repos', erreur: null })
    } catch (e) {
      setFiche({ etat: 'repos', erreur: e instanceof Error ? e.message : "La fiche n'a pas pu être lue." })
    }
  }
  // P4-c : l'adresse dite -> les services publics sont lus EN ARRIÈRE-PLAN (DPE, année, parcelle, copropriété) ; une fois
  //   par adresse (la clé dit l'adresse, le type et la surface). Rien n'est posé : ce sont des propositions.
  const [publicsEnCours, setPublicsEnCours] = useState(false)
  const publicsDemandes = useRef(new Set<string>())
  const clePublics = ['adresse_haut', 'cp', 'ville', 'type', 'surfappart'].map((c) => texte(vue.reponses[c]).trim().toLowerCase()).join('|')
  const enCoursPublics = vue.etat === 'en_cours' && vue.app_dossier_id == null
  useEffect(() => {
    if (!enCoursPublics || !vue.publics?.possible || vue.publics.a_jour) return
    const cle = `${vue.id}|${clePublics}`
    if (publicsDemandes.current.has(cle)) return
    publicsDemandes.current.add(cle)
    setPublicsEnCours(true)
    // une panne ne dérange pas la personne : on ne propose rien, c'est tout
    chercherPublicsParcours(vue.id).then(onVue, () => undefined).finally(() => setPublicsEnCours(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vue.id, clePublics, vue.publics?.possible, vue.publics?.a_jour, enCoursPublics])
  // « Oui » remplit les cases de la carte ; « Autre » range la proposition. La personne valide toujours elle-même.
  const [ecartees, setEcartees] = useState<Set<string>>(() => new Set())
  const [reprises, setReprises] = useState<Record<string, string>>({})  // proposition reprise -> sa source (dite sous la carte)

  // P4-c : la clé suit les réponses GARDÉES de la question (et plus `maj_le`) : la lecture publique qui revient pendant
  //   que la personne tape ne vide pas sa saisie ; une réponse, une fiche lue, une autre question la renouvellent.
  const cleQuestion = `${vue.id}:${q?.id ?? 'fin'}:${q ? JSON.stringify(q.champs.map((c) => vue.reponses[c] ?? null)) : ''}`
  useEffect(() => {
    setValeurs(q ? valeursDe(q, vue.reponses) : {})
    setErreur(null)
    setReprises({})
  // la question affichée (ou ce qu'en dit le serveur) a changé : on repart de ses réponses gardées
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cleQuestion])
  // P4-d : une phrase libre lue -- ses cases vont dans la CARTE de sa question (APRÈS la remise à zéro ci-dessus) ;
  //   la personne vérifie et valide elle-même
  useEffect(() => {
    const r = vue.remplir
    if (!r || !q || r.question !== q.id) return
    if (Object.keys(r.cases).length) {
      setValeurs((avant) => ({ ...avant, ...r.cases }))
      setReprises((avant) => ({ ...avant, phrase: 'ta phrase' }))
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vue.remplir?.jeton])
  // P4-d : la zone du bas sait quelle question est ouverte (une phrase tapée y va, sans tour d'IA)
  const enCoursQ = vue.etat === 'en_cours' && vue.app_dossier_id == null
  useEffect(() => {
    onQuestion?.(vue.id, enCoursQ && q ? { id: q.id, titre: q.titre } : null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vue.id, q?.id, enCoursQ])

  const setValeur = (nom: string, v: unknown) => setValeurs((avant) => {
    const apres: Valeurs = { ...avant, [nom]: v }
    for (const cible of RECOPIES[nom] ?? []) {
      if (!(cible in avant)) continue
      if (!texte(avant[cible]).trim() || texte(avant[cible]) === texte(avant[nom])) apres[cible] = v
    }
    return apres
  })

  const envoyer = async (geste: 'repondre' | 'passer' | 'nsp') => {
    if (!q || envoi) return
    setEnvoi(true)
    setErreur(null)
    try {
      let corps: Valeurs = {}
      if (geste === 'repondre' && q.forme === 'mandant' && texte(valeurs.mandant_choix) === 'nouveau') {
        // d'abord le coffre privé (si quelque chose est tapé) ; s'il refuse, rien ne part au serveur de l'assistant
        if (Object.values(coordonnees).some((v) => String(v ?? '').trim())) {
          await deposerCoordonneesMandant(vue.id, coordonnees)
          setDeposees(true)
          setCoordonnees({})
        } else if (!deposees) {
          throw new Error("Tape au moins le nom et l'e-mail du nouveau mandant, ou choisis « Plus tard ».")
        }
      }
      if (geste === 'repondre') {
        // seules les cases MONTRÉES partent (une case vidée part vide : le serveur la retire)
        for (const c of q.champs) {
          if (c === 'composition') {
            corps.composition = ((valeurs.composition as Piece[]) ?? []).filter((p) => p.idTypePiece || p.surfacePiece.trim() || p.detailPiece.trim())
          } else if (q.forme === 'mandant') {
            if (c in valeurs) corps[c] = valeurs[c]
          } else if (montree(cat.cases[c], valeurs)) {
            corps[c] = texte(valeurs[c]).trim()
          }
        }
        if (q.forme === 'fichiers') corps = { photos: (valeurs.photos as PhotoDuBien[]) ?? [] }  // P6 : l'ordre et la visibilité
      }
      onVue(await repondreParcours(vue.id, q.id, geste, corps))
      setOuverte(null)
    } catch (e) {
      setErreur(e instanceof RefusAssistant || e instanceof Error ? e.message : "La réponse n'a pas été gardée.")
    } finally {
      setEnvoi(false)
    }
  }

  const donnees = vue.questions.filter((x) => x.etat && x.id !== q?.id)
  const enCours = vue.etat === 'en_cours' && vue.app_dossier_id == null

  const corpsQuestion = (): ReactNode => {
    if (!q) return null
    if (q.forme === 'pieces') {
      return <EditeurPieces pieces={(valeurs.composition as Piece[]) ?? []} types={cat.typesPiece} onChange={(p) => setValeur('composition', p)} />
    }
    if (q.forme === 'fichiers') {
      if (!ficheOuverte) {
        return <p className="asp-note">Les <b>photos du bien</b> (la galerie de l'annonce : visibles ou masquées, la couverture) se déposent dans la fenêtre de création, à son étape Photos. Ce n'est pas la fiche de visite.</p>
      }
      return <QuestionPhotos parcoursId={vue.id} photos={(valeurs.photos as PhotoDuBien[]) ?? []} onChange={(l) => setValeur('photos', l)} />
    }
    if (q.forme === 'mandant') {
      return <QuestionMandant valeurs={valeurs} setValeur={setValeur} coordonnees={coordonnees} setCoordonnees={setCoordonnees}
        chercher={chercherMandants} dejaDeposees={deposees} />
    }
    // P4-b : une case lue sur la fiche avec peu de confiance porte « à vérifier » dans son libellé
    const cases = q.champs.map((c) => cat.cases[c]).filter((c) => montree(c, valeurs))
      .map((c) => (vue.doutes?.[c.nom] != null ? { ...c, libelle: `${c.libelle} · à vérifier` } : c))
    if (!cases.length) return <p className="asp-note">Rien à demander ici pour ce type de bien.</p>
    // P4-c : les propositions des services publics pour CETTE question (maquette E03, E04, E05, N07)
    const proposees = (vue.publics?.propositions ?? []).filter((p) => p.question === q.id && !ecartees.has(p.id) && !(p.id in reprises)
      // P4-d : une case déjà remplie dans la carte (tapée, ou venue d'une phrase) : la proposition se retire
      && Object.keys(p.cases).every((c) => !texte(valeurs[c]).trim()))
    const reprendre = (p: PropositionPublique) => {
      setValeurs((avant) => ({ ...avant, ...p.cases }))
      setReprises((avant) => ({ ...avant, [p.id]: p.source }))
    }
    const aCocher = q.forme === 'cocher' ? cases.filter((c) => estACocher(c)) : []
    const compteurs = q.forme === 'compteurs' ? cases.filter((c) => c.genre === 'nombre' && c.entier) : []
    const listes = cases.filter((c) => c.genre === 'liste' && !aCocher.includes(c))
    const saisies = cases.filter((c) => c.genre !== 'liste' && !compteurs.includes(c))
    return (
      <>
        {proposees.map((p) => (
          <div key={p.id} className="asp-prop" role="group" aria-label={`Proposition : ${p.source}`}>
            <p><b>{p.phrase}</b> <span className="asp-prop-src">({p.source})</span>{p.prudence ? <span className="asp-prop-pru">{p.prudence}</span> : null}</p>
            <div className="asp-prop-q">
              <span>{p.demande}</span>
              <button type="button" className="asp-sec asp-prop-oui" onClick={() => reprendre(p)}>{p.oui}</button>
              <button type="button" className="asp-sec" onClick={() => setEcartees((avant) => new Set(avant).add(p.id))}>{p.non}</button>
            </div>
          </div>
        ))}
        {aCocher.length ? (
          <div className="asp-choix" role="group" aria-label="À cocher">
            {aCocher.map((c) => {
              const on = OUI.has(texte(valeurs[c.nom]))
              return (
                <button key={c.nom} type="button" className={`asp-puce${on ? ' is-on' : ''}`} aria-pressed={on}
                  onClick={() => setValeur(c.nom, on ? '' : estACocher(c))}>{on ? <Coche /> : null}{c.libelle}</button>
              )
            })}
          </div>
        ) : null}
        {compteurs.length ? (
          <div className="asp-cpt">{compteurs.map((c) => <Compteur key={c.nom} c={c} valeur={texte(valeurs[c.nom])} onPas={(d) => setValeurs((avant) => ({ ...avant, [c.nom]: pas(avant[c.nom], d) }))} />)}</div>
        ) : null}
        {saisies.length ? (
          <div className="asp-grille">{saisies.map((c) => <Champ key={c.nom} c={c} valeur={texte(valeurs[c.nom])} onChange={(v) => setValeur(c.nom, v)} />)}</div>
        ) : null}
        {listes.map((c) => <Pilules key={c.nom} c={c} valeur={texte(valeurs[c.nom])} onChange={(v) => setValeur(c.nom, v)} />)}
      </>
    )
  }

  const rang = q ? Math.max(1, vue.questions.findIndex((x) => x.id === q.id) + 1) : vue.repere.total
  return (
    <div className="asp" aria-label="Parcours guidé">
      {donnees.length ? (
        <div className="asp-reps">
          {donnees.map((x) => (
            <span key={x.id} className="asp-rep" title={x.etat === 'connue' ? "D'après ta demande : pas reposée, tu peux la modifier" : undefined}>
              <span className={`asp-ok${x.etat === 'faite' || x.etat === 'connue' ? '' : ' is-pale'}`}><Coche /></span>
              <i>{x.titre}</i><b>{resume(x, vue.reponses, cat)}</b>{x.etat === 'connue' ? <em className="asp-dit">{x.champs.some((c) => vue.sources?.[c] === 'demande' || vue.sources?.[c] === 'phrase') ? 'dit' : 'lu'}</em> : null}
              {enCours ? <button type="button" onClick={() => setOuverte(x.id)} disabled={envoi}>Modifier</button> : null}
            </span>
          ))}
        </div>
      ) : null}
      {enCours && ficheOuverte ? (
        <div className="asp-fiche" role="group" aria-label="La fiche de visite">
          <input ref={choixFiche} type="file" hidden multiple accept="image/jpeg,image/png,image/webp"
            onChange={(e) => { void lireFiche(e.target.files); e.target.value = '' }} />
          {fiche.etat === 'depot' ? <span>Je dépose les photos…</span>
            : fiche.etat === 'lecture' ? <span>Je lis la fiche, une page à la fois (environ 30 secondes)…</span>
              : vue.fiche ? <span>Fiche de visite lue : {Object.values(vue.sources ?? {}).filter((s) => s === 'scan').length} cases remplies{vue.fiche.doutes ? `, ${vue.fiche.doutes} à vérifier` : ''}{vue.fiche.coffre ? ', le mandant gardé à part' : ''}.</span>
                : <span>Tu as la <b>fiche de visite</b> remplie (le patron, pas les photos du bien) ? Joins ses pages : je la lis d'un coup et ne te pose que ce qu'elle ne dit pas.</span>}
          {fiche.etat === 'repos' ? (
            <button type="button" className="asp-sec" onClick={() => choixFiche.current?.click()}>{vue.fiche ? 'Lire une autre page' : 'Lire la fiche de visite'}</button>
          ) : null}
          {fiche.erreur ? <span className="asp-fiche-ko" role="alert">{fiche.erreur}</span> : null}
        </div>
      ) : null}
      {!enCours ? (
        <article className="asp-q is-faite">
          <header className="asp-qh"><h3>{vue.genre === 'creation_annonce' ? 'Annonce créée' : 'Estimation créée'}</h3></header>
          <div className="asp-qb"><p className="asp-phrase">Le parcours est terminé : la fiche a été créée par la fenêtre.</p></div>
          {vue.app_dossier_id != null && onOuvrirBien ? (
            <footer className="asp-pied"><span /><div><button type="button" className="asp-sec" onClick={() => onOuvrirBien(String(vue.app_dossier_id))}>Ouvrir la fiche</button></div></footer>
          ) : null}
        </article>
      ) : q ? (
        <article className="asp-q" aria-label={`Question : ${q.titre}`}>
          <header className="asp-qh">
            <h3>{q.titre}</h3>
            <span className="asp-rang">{rang} sur {vue.repere.total}</span>
            <ol className="asp-fil" aria-label="Les rubriques">
              {vue.questions.map((x) => (
                <li key={x.id} className={x.id === q.id ? 'is-c' : x.etat ? 'is-f' : ''} aria-current={x.id === q.id ? 'step' : undefined}>
                  {x.etat && x.id !== q.id ? <Coche /> : null}{x.titre}
                </li>
              ))}
            </ol>
          </header>
          <div className="asp-qb">
            <p className="asp-phrase">{q.phrase}</p>
            {(vue.phrases ?? []).filter((p) => p.question === q.id).map((p, i) => (
              <div key={`${p.le ?? ''}${i}`} className="asp-phr"><span>« {p.texte} »</span><em>{direPhrase(p)}</em></div>
            ))}
            {vue.remplir && vue.remplir.question === q.id && (vue.remplir.dire.vendeur || vue.remplir.dire.retires) ? (
              <p className="asp-note asp-phr-avis">{vue.remplir.dire.retires ? "Le téléphone ou l'e-mail a été retiré de la phrase avant la lecture. " : ''}
                {vue.remplir.dire.vendeur ? "Le vendeur ne se garde pas par une phrase : saisis-le dans la question « Le mandant » (cases protégées)." : ''}</p>
            ) : null}
            {Object.keys(reprises).length ? (
              <p className="asp-note asp-prop-repris">Repris de : {[...new Set(Object.values(reprises))].join(', ')}. Vérifie, puis « Valider ».</p>
            ) : null}
            {publicsEnCours && QUESTIONS_PUBLIQUES.has(q.id) ? <p className="asp-note">Je regarde le DPE, le cadastre et les registres publics pour cette adresse…</p> : null}
            {corpsQuestion()}
          </div>
          {erreur ? <div className="asp-ko" role="alert">{erreur}</div> : null}
          <footer className="asp-pied">
            <span>{q.forme === 'fichiers' && ficheOuverte ? "Elles vont à l'étape 2 « Photos » de la fenêtre (20 au plus) et partent comme aujourd'hui, une par une, après « Créer »." : "Les listes sont celles de la fenêtre de création. Un clic ici n'appelle pas l'IA."}</span>
            <div>
              {ouverte ? <button type="button" className="asp-sec" onClick={() => setOuverte(null)} disabled={envoi}>Annuler</button> : null}
              <button type="button" className="asp-sec" onClick={() => void envoyer('nsp')} disabled={envoi}>Je ne sais pas</button>
              <button type="button" className="asp-sec" onClick={() => void envoyer('passer')} disabled={envoi}>Plus tard</button>
              <button type="button" className="asp-go" onClick={() => void envoyer('repondre')} disabled={envoi}>{envoi ? 'Je garde…' : 'Valider'}</button>
            </div>
          </footer>
        </article>
      ) : (
        <article className="asp-q is-fin">
          <header className="asp-qh"><h3>Tout est répondu</h3><span className="asp-rang">{vue.repere.faites} sur {vue.repere.total}</span></header>
          <div className="asp-qb">
            <p className="asp-phrase">La fenêtre de création s'ouvre remplie de tes réponses. Rien n'est créé tant que tu n'as pas cliqué « Créer » dans la fenêtre.</p>
          </div>
          {erreur ? <div className="asp-ko" role="alert">{erreur}</div> : null}
          <footer className="asp-pied">
            <span>Tu peux encore modifier une réponse ci-dessus.</span>
            <div>{onOuvrirFenetre ? <button type="button" className="asp-go" onClick={() => onOuvrirFenetre(vue)}>Ouvrir la fenêtre remplie</button> : null}</div>
          </footer>
        </article>
      )}
    </div>
  )
}
