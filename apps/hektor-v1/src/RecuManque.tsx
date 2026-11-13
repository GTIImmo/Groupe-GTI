// GED (12/11/2026, morceau 3) -- LE BLOC « REÇU / MANQUE » en haut de l'onglet Documents : les pièces attendues au
// moment en cours du dossier (lib/gedPieces.ts), reçues ou non trouvées. Derrière l'interrupteur `ged_recu_manque`.
// On SIGNALE, on ne bloque rien. Une pièce non trouvée se dépose d'un clic, son type déjà choisi.
// Les anciens documents comptent par leur NOM (décision du 12/11 : le stock n'est pas classé) ; ceux déposés avec
// l'outil comptent par le type que l'utilisateur leur a donné.
// ⭐ Morceau 5 (§12.10) : sous « À regarder », les règles sans IA (lib/gedRegles.ts), derrière `ged_propositions`.
// ⭐ Morceau 7 (§12.17) : au même endroit, ce que l'IA a lu comparé à la fiche et aux mandants (lib/gedReglesLues.ts).
// ⭐ Morceau 8 (§12.18) : « À remplir », une case VIDE et la valeur lue (lib/gedRemplir.ts), derrière `ged_remplir` ;
//   « Remplir la fiche » appelle l'écran du bien (onRemplir), « Ignorer » garde la décision. Rien sans clic.
import { useEffect, useMemo, useState } from 'react'
import { loadAffairesForDossier, loadRegisterCycleAffaires } from './lib/api'
import { etatFiableDuDocument } from './lib/etatSignatureMandat'
import { compterConditionsStrict, gedDecider, loadGedClassements, loadGedDecisions, useGedPropositions, useGedRemplir } from './lib/ged'
import { propositionsRemplir, type FaitsRemplir, type PropositionRemplir } from './lib/gedRemplir'
import { dateEtatLue, loadGedLectures, resumeLecture, type LectureDocument } from './lib/gedLecture'
import { LIBELLE_MOMENT, recuManque, type LignePiece } from './lib/gedPieces'
import { deposeAuPlusTard, LIBELLE_A_DEPOSER, reglesSansIa, type AffaireRegle, type Alerte, type FaitsRegles } from './lib/gedRegles'
import type { PersonneDuBien } from './lib/gedComparer'
import { reglesLues } from './lib/gedReglesLues'
import type { ConsoleDocument } from './types'
import './RecuManque.css'

const NIVEAU: Record<LignePiece['niveau'], string> = {
  obligatoire: 'obligatoire',
  bonne_pratique: 'bonne pratique',
  selon_le_cas: 'selon le cas',
}

// Le jour du dépôt AU PLUS TARD d'un document (gedRegles : nos dates et le numéro Hektor), en « AAAA-MM-JJ ».
function depose(d: ConsoleDocument): string | null {
  const brut = (d.metadata_json as { hektor_uploaded_document_id?: unknown } | null)?.hektor_uploaded_document_id
  const numero = brut != null && /^\d+$/.test(String(brut)) ? Number(brut) : null
  return deposeAuPlusTard(numero, [d.created_at_hektor, d.created_at])?.toISOString().slice(0, 10) ?? null
}

const NIVEAU_ALERTE: Record<Alerte['niveau'], string> = { alerte: 'à vérifier', piece: 'pièce non trouvée', info: 'pour information' }

// Un montant du registre (en euros, texte ou nombre) ; vide ou zéro -> null.
const euros = (v: string | number | null | undefined) => { const x = Number(v); return v != null && v !== '' && Number.isFinite(x) && x > 0 ? x : null }

export function RecuManque({
  hektorAnnonceId, appDossierId, documents, faits, personnesDuBien = [], onDeposer, onRemplir,
}: {
  hektorAnnonceId: string | number
  appDossierId?: number
  documents: ConsoleDocument[]
  faits: FaitsRegles & Partial<Pick<FaitsRemplir, 'quotePart' | 'erpDate'>>
  // morceau 8 : écrire UNE proposition (l'écran du bien relit la case, appelle le geste existant, garde la décision) ;
  // rend le message à afficher. Sans lui, les propositions ne se montrent pas.
  onRemplir?: (p: PropositionRemplir) => Promise<string>
  // morceau 7 : les mandants / propriétaires de la fiche, une ligne par personne (un couple = deux)
  personnesDuBien?: PersonneDuBien[]
  onDeposer?: (typeCode: string, libelle: string) => void
}) {
  const regles = useGedPropositions()
  const [affaires, setAffaires] = useState<AffaireRegle[] | null>(null)
  const [classements, setClassements] = useState<Map<string, string>>(() => new Map())
  // morceau 6 : ce que l'IA a lu dans les documents déposés avec l'outil (la plus récente lecture par document)
  const [lectures, setLectures] = useState<Map<string, LectureDocument>>(() => new Map())
  const [ouvrirPrecedents, setOuvrirPrecedents] = useState(false)
  // ce qui manque d'abord ; les pièces reçues se replient sur une ligne (écran bas : 665 px)
  const [ouvrirRecues, setOuvrirRecues] = useState(false)
  const [ouvrirLus, setOuvrirLus] = useState(false)
  const nbDocuments = documents.length

  useEffect(() => {
    let annule = false
    void loadGedClassements(hektorAnnonceId).then((m) => { if (!annule) setClassements(m) })
    void loadGedLectures(hektorAnnonceId).then((m) => { if (!annule) setLectures(m) })
    return () => { annule = true }
    // relu quand la liste des documents change (un dépôt vient d'arriver)
  }, [hektorAnnonceId, nbDocuments])

  // Les transactions du bien (registre), lues seulement si les règles sont allumées. Une lecture ratée : les règles
  // qui en ont besoin se taisent (null), jamais « aucune transaction ».
  useEffect(() => {
    if (!regles || !appDossierId) return
    let annule = false
    loadAffairesForDossier(appDossierId)
      .then((rows) => { if (!annule) setAffaires(rows.filter((a) => a.present_in_hektor !== false).map((a) => ({
        kind: String(a.kind), state: a.state ?? null, date: a.date ?? null, dateActe: a.date_acte ?? null, id: Number(a.app_affaire_id),
        // morceau 7c : de quoi comparer une transaction lue (montant en euros ; acquéreurs : un objet seul ou une liste)
        montant: euros(a.montant), prixNetVendeur: euros(a.prix_net_vendeur), honorairesEntree: euros(a.honoraires_entree), honorairesSortie: euros(a.honoraires_sortie),
        acquereurs: (Array.isArray(a.acquereurs_json) ? a.acquereurs_json : a.acquereurs_json ? [a.acquereurs_json] : [])
          .map((p) => ({ nom: String((p as { nom?: unknown })?.nom ?? '').trim(), prenom: String((p as { prenom?: unknown })?.prenom ?? '').trim() }))
          .filter((p) => p.nom || p.prenom),
      }))) })
      .catch(() => { if (!annule) setAffaires(null) })
    return () => { annule = true }
  }, [regles, appDossierId])

  // morceau 7b : qui paie les honoraires, au REGISTRE des mandats (la vue que l'écran lit déjà pour la clôture). Lecture
  // ratée ou pas encore faite = `undefined` : la règle L1 se tait ; lue et vide = `null`.
  const [chargeRegistre, setChargeRegistre] = useState<string | null | undefined>(undefined)
  const numeroMandat = String(faits.numeroMandat ?? '').trim()
  useEffect(() => {
    setChargeRegistre(undefined)
    if (!regles || !numeroMandat) return
    let annule = false
    loadRegisterCycleAffaires(hektorAnnonceId)
      .then((rows) => {
        if (annule) return
        const ligne = rows.find((r) => String(r.numero_mandat ?? '').trim() === numeroMandat)
        setChargeRegistre(ligne ? (String(ligne.mandat_charge_honoraires_app ?? '').trim() || null) : undefined)
      })
      .catch(() => { if (!annule) setChargeRegistre(undefined) })
    return () => { annule = true }
  }, [regles, hektorAnnonceId, numeroMandat])

  const alertes = useMemo(() => {
    if (!regles || affaires === null) return []
    const docs = documents
      .filter((d) => d.present_in_hektor !== false)
      .map((d) => ({ nom: d.document_name, typeCode: classements.get(d.id) ?? null, date: depose(d), signature: etatFiableDuDocument(d)?.status ?? null, modele: d.source === 'hektor_console_modele', dateEtat: dateEtatLue(lectures.get(d.id)) }))
    // morceau 7 : ce que l'IA a lu, comparé à la fiche et aux mandants ; même ordre (alertes, pièces, informations)
    const docsLus = documents
      .filter((d) => d.present_in_hektor !== false && lectures.has(d.id))
      .map((d) => ({ nom: d.document_name, lecture: lectures.get(d.id) as LectureDocument }))
    const ordre: Record<Alerte['niveau'], number> = { alerte: 0, piece: 1, info: 2 }
    return [...reglesSansIa(faits, docs, affaires, new Date()), ...reglesLues({ ...faits, chargeRegistre }, docsLus, personnesDuBien, affaires, new Date())]
      .sort((a, b) => ordre[a.niveau] - ordre[b.niveau])
  }, [regles, affaires, faits, documents, classements, lectures, personnesDuBien, chargeRegistre])

  // ── morceau 8 : les propositions « remplir », derrière `ged_remplir` (il ÉCRIT) ──────────────────────────────
  // Les décisions déjà prises et le nombre de conditions des compromis vivants sont relus à chaque fois ; une lecture
  // ratée (null) -> AUCUNE proposition (jamais reproposer, jamais croire une liste vide).
  const remplir = useGedRemplir()
  // la PRÉSENCE du geste (la fonction change à chaque rendu de la fiche : elle ne doit pas relancer les lectures)
  const peutRemplir = Boolean(onRemplir)
  const [decisions, setDecisions] = useState<Set<string> | null>(null)
  const [conditions, setConditions] = useState<Map<number, number> | null>(null)
  const [enCours, setEnCours] = useState<string | null>(null)
  const [messageRemplir, setMessageRemplir] = useState<string | null>(null)
  const [relire, setRelire] = useState(0)
  useEffect(() => {
    if (!remplir || !peutRemplir) return
    let annule = false
    void loadGedDecisions(hektorAnnonceId).then((d) => { if (!annule) setDecisions(d) })
    return () => { annule = true }
  }, [remplir, peutRemplir, hektorAnnonceId, relire])
  const idsCompromis = useMemo(() => (affaires ?? []).filter((a) => a.kind === 'compromis' && a.id != null).map((a) => a.id as number).join(','), [affaires])
  useEffect(() => {
    if (!remplir || !peutRemplir) return
    let annule = false
    compterConditionsStrict(idsCompromis ? idsCompromis.split(',').map(Number) : [])
      .then((m) => { if (!annule) setConditions(m) })
      .catch(() => { if (!annule) setConditions(null) })
    return () => { annule = true }
  }, [remplir, peutRemplir, idsCompromis, relire])
  const propositions = useMemo(() => {
    if (!remplir || !peutRemplir || !decisions || !conditions || affaires === null) return []
    const docsLus = documents
      .filter((d) => d.present_in_hektor !== false && lectures.has(d.id))
      .map((d) => ({ nom: d.document_name, lecture: lectures.get(d.id) as LectureDocument }))
    return propositionsRemplir({ ...faits, chargeRegistre }, docsLus, affaires, decisions, conditions)
  }, [remplir, peutRemplir, decisions, conditions, affaires, documents, lectures, faits, chargeRegistre])
  const agir = async (p: PropositionRemplir, geste: 'remplir' | 'ignorer') => {
    if (enCours || !onRemplir) return
    setEnCours(p.cle); setMessageRemplir(null)
    try {
      if (geste === 'remplir') setMessageRemplir(await onRemplir(p))
      else {
        await gedDecider({ hektorAnnonceId, lectureId: p.lectureId, cle: p.cle, champ: p.champ, valeur: p.valeur, decision: 'ignoree' })
        setMessageRemplir(`Ignoré : ${p.texte}.`)
      }
    } catch (e) {
      setMessageRemplir(e instanceof Error ? e.message : 'Rien n\'a été écrit.')
    } finally {
      setEnCours(null); setRelire((n) => n + 1)
    }
  }

  // le résumé de la lecture, à côté du nom d'un document reçu (« DPE 2024.pdf — Lu : énergie D… »)
  const resumeParNom = useMemo(() => {
    const m = new Map<string, string>()
    for (const d of documents) { const l = lectures.get(d.id); if (l) m.set(d.document_name, resumeLecture(l)) }
    return m
  }, [documents, lectures])
  const avecLecture = (nom: string) => (resumeParNom.has(nom) ? `${nom} — ${resumeParNom.get(nom)}` : nom)

  // TOUT ce que l'IA a lu, quel que soit le moment de la pièce : la liste ci-dessous ne montre que le moment en cours
  // (essai réel du 12/11 : la taxe, le titre et la copro lus restaient invisibles après rechargement, §12.14).
  const lus = useMemo(() => documents
    .filter((d) => d.present_in_hektor !== false && lectures.has(d.id))
    .map((d) => ({ id: d.id, nom: d.document_name, resume: resumeLecture(lectures.get(d.id) as LectureDocument) })), [documents, lectures])

  const resultat = useMemo(() => recuManque(
    faits,
    documents
      .filter((d) => d.present_in_hektor !== false)
      .map((d) => ({ nom: d.document_name, typeCode: classements.get(d.id) ?? null })),
  ), [faits, documents, classements])

  const ligne = (l: LignePiece) => {
    const recu = l.etat === 'recu'
    const contenu = (
      <>
        <span className={`gm-ic is-${l.etat}`} aria-hidden="true">{recu ? '✓' : l.etat === 'selon_le_cas' ? '?' : ''}</span>
        <span className="gm-t">
          {l.libelle}
          {l.sensible ? <span className="gm-prive" title="Toujours privé">privé</span> : null}
          <small>{NIVEAU[l.niveau]}{l.pourquoi ? ` : ${l.pourquoi}` : ''}</small>
        </span>
        <span className="gm-d" title={recu ? l.documents.map(avecLecture).join('\n') : undefined}>
          {recu
            ? `${l.dansUnDossier ? 'Dans un dossier de diagnostics : ' : ''}${l.documents.slice(0, 2).map(avecLecture).join(', ')}${l.documents.length > 2 ? ` (+${l.documents.length - 2})` : ''}`
            : l.etat === 'selon_le_cas'
              ? 'La fiche ne dit pas si elle est due'
              : onDeposer ? 'Non trouvée : déposer' : 'Non trouvée'}
        </span>
      </>
    )
    if (!recu && onDeposer) {
      return (
        <button key={l.cle} type="button" className={`gm-l is-${l.etat}`} onClick={() => onDeposer(l.typeADeposer, l.libelle)} aria-label={`Déposer : ${l.libelle}`}>
          {contenu}
        </button>
      )
    }
    return <div key={l.cle} className={`gm-l is-${l.etat}`}>{contenu}</div>
  }

  const manquantesAvant = resultat.precedents.reduce((n, p) => n + p.manquantes.length, 0)

  return (
    <section className="gm" aria-label="Reçu / manque">
      <div className="gm-h">
        <h4>{`${LIBELLE_MOMENT[resultat.moment]} : ${resultat.recues} pièce${resultat.recues > 1 ? 's' : ''} sur ${resultat.attendues}`}</h4>
        <span>Reçu / manque, d'après le type de chaque document (son nom pour les anciens)</span>
      </div>
      {propositions.length || messageRemplir ? (
        <div className="gm-liste">
          <p className="gm-avant-t">{`À remplir (${propositions.length})`}</p>
          {messageRemplir ? <p className="gm-avant-t" role="status">{messageRemplir}</p> : null}
          {propositions.map((p) => (
            <div key={`${p.cle}|${p.valeur}`} className="gm-l is-selon_le_cas">
              <span className="gm-ic is-selon_le_cas" aria-hidden="true">+</span>
              <span className="gm-t">{p.texte}<small>{`case vide : lu dans ${p.source}`}</small></span>
              <span className="gm-d">
                <button type="button" className="gm-avant-b" disabled={enCours !== null} onClick={() => void agir(p, 'remplir')}>{enCours === p.cle ? 'Écriture…' : 'Remplir la fiche'}</button>
                {' '}
                <button type="button" className="gm-avant-b" disabled={enCours !== null} onClick={() => void agir(p, 'ignorer')}>Ignorer</button>
              </span>
            </div>
          ))}
        </div>
      ) : null}
      {alertes.length ? (
        <div className="gm-liste">
          <p className="gm-avant-t">{`À regarder (${alertes.length})`}</p>
          {alertes.map((a, i) => {
            const contenu = (
              <>
                <span className={`gm-ic is-${a.niveau === 'info' ? 'selon_le_cas' : 'non_trouve'}`} aria-hidden="true">{a.niveau === 'info' ? 'i' : '!'}</span>
                <span className="gm-t">{a.texte}<small>{`${NIVEAU_ALERTE[a.niveau]} : ${a.pourquoi}`}</small></span>
                <span className="gm-d">{a.typeADeposer && onDeposer ? 'Déposer la pièce' : ''}</span>
              </>
            )
            return a.typeADeposer && onDeposer ? (
              <button key={`${a.code}-${i}`} type="button" className="gm-l is-non_trouve" onClick={() => onDeposer(a.typeADeposer as string, LIBELLE_A_DEPOSER[a.typeADeposer as string] ?? a.texte)} aria-label={`Déposer : ${a.texte}`}>{contenu}</button>
            ) : (
              <div key={`${a.code}-${i}`} className={`gm-l is-${a.niveau === 'info' ? 'selon_le_cas' : 'non_trouve'}`}>{contenu}</div>
            )
          })}
        </div>
      ) : null}
      <div className="gm-liste">{resultat.pieces.filter((l) => l.etat !== 'recu').map(ligne)}</div>
      {resultat.recues ? (
        <div className="gm-avant">
          <button type="button" className="gm-avant-b" onClick={() => setOuvrirRecues((v) => !v)} aria-expanded={ouvrirRecues}>
            {`${ouvrirRecues ? '▾' : '▸'} ${resultat.recues} pièce${resultat.recues > 1 ? 's' : ''} reçue${resultat.recues > 1 ? 's' : ''}`}
          </button>
          {ouvrirRecues ? <div className="gm-liste">{resultat.pieces.filter((l) => l.etat === 'recu').map(ligne)}</div> : null}
        </div>
      ) : null}
      {lus.length ? (
        <div className="gm-avant">
          <button type="button" className="gm-avant-b" onClick={() => setOuvrirLus((v) => !v)} aria-expanded={ouvrirLus}>
            {`${ouvrirLus ? '▾' : '▸'} Lu par l'IA : ${lus.length} document${lus.length > 1 ? 's' : ''}`}
          </button>
          {ouvrirLus ? (
            <div className="gm-liste">
              {lus.map((l) => (
                <div key={l.id} className="gm-l is-recu">
                  <span className="gm-ic is-recu" aria-hidden="true">✓</span>
                  <span className="gm-t">{l.nom}<small>{l.resume}</small></span>
                  <span className="gm-d" />
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
      {manquantesAvant ? (
        <div className="gm-avant">
          <button type="button" className="gm-avant-b" onClick={() => setOuvrirPrecedents((v) => !v)} aria-expanded={ouvrirPrecedents}>
            {`${ouvrirPrecedents ? '▾' : '▸'} Moments précédents : ${manquantesAvant} pièce${manquantesAvant > 1 ? 's' : ''} obligatoire${manquantesAvant > 1 ? 's' : ''} non trouvée${manquantesAvant > 1 ? 's' : ''}`}
          </button>
          {ouvrirPrecedents ? resultat.precedents.map((p) => (
            <div key={p.moment} className="gm-liste">
              <p className="gm-avant-t">{LIBELLE_MOMENT[p.moment]}</p>
              {p.manquantes.map(ligne)}
            </div>
          )) : null}
        </div>
      ) : null}
    </section>
  )
}
