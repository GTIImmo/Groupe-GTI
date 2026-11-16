// GED (12/11/2026, morceau 3) -- LE BLOC « REÇU / MANQUE » en haut de l'onglet Documents : les pièces attendues au
// moment en cours du dossier (lib/gedPieces.ts), reçues ou non trouvées. Derrière l'interrupteur `ged_recu_manque`.
// On SIGNALE, on ne bloque rien. Une pièce non trouvée se dépose d'un clic, son type déjà choisi.
// Les anciens documents comptent par leur NOM (décision du 12/11 : le stock n'est pas classé) ; ceux déposés avec
// l'outil comptent par le type que l'utilisateur leur a donné.
// ⭐ Morceau 5 (§12.10) : sous « À regarder », les règles sans IA (lib/gedRegles.ts), derrière `ged_propositions`.
// ⭐ Morceau 7 (§12.17) : au même endroit, ce que l'IA a lu comparé à la fiche et aux mandants (lib/gedReglesLues.ts).
// ⭐ Morceau 8 (§12.18) : « À remplir », une case VIDE et la valeur lue (lib/gedRemplir.ts), derrière `ged_remplir` ;
//   « Remplir la fiche » appelle l'écran du bien (onRemplir), « Ignorer » garde la décision. Rien sans clic.
// ⭐ Morceau 9, lot 9c : au même endroit, la date, le lieu de naissance et la situation de famille d'un mandant
//   (lib/gedRemplirContact.ts), lus sur ses pièces, pour SA fiche contact relue (loadContactsEtatCivil).
import { useEffect, useMemo, useState } from 'react'
import { loadAffairesForDossier, loadRegisterCycleAffaires } from './lib/api'
import { etatFiableDuDocument } from './lib/etatSignatureMandat'
import { compterConditionsStrict, gedDecider, gedJuger, loadContactsEtatCivil, loadGedClassements, loadGedDecisions, loadGedJugements, useGedPropositions, useGedRemplir, type EtatCivilLu, type JugementGed } from './lib/ged'
import { cleJugement, LIBELLE_VERDICT, VERDICTS, type VerdictGed } from './lib/gedMesure'
import { propositionsRemplir, type FaitsRemplir, type PropositionRemplir } from './lib/gedRemplir'
import { propositionsContact } from './lib/gedRemplirContact'
import { dateEtatLue, loadGedLectures, resumeLecture, type LectureDocument } from './lib/gedLecture'
import { reglesPersonnes } from './lib/gedReglesPersonnes'
import { reglesFinancement } from './lib/gedReglesFinancement'
import { reglesEtatCivil } from './lib/gedReglesEtatCivil'
import { LIBELLE_MOMENT, recuManque, type LignePiece, type MomentDossier } from './lib/gedPieces'
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
// habillage H1 : les moments de la vente, dans l'ordre (le même que gedPieces.ts)
const ORDRE_MOMENTS: MomentDossier[] = ['mandat', 'mise_en_vente', 'offre', 'compromis']

// Un montant du registre (en euros, texte ou nombre) ; vide ou zéro -> null.
const euros = (v: string | number | null | undefined) => { const x = Number(v); return v != null && v !== '' && Number.isFinite(x) && x > 0 ? x : null }

export function RecuManque({
  hektorAnnonceId, appDossierId, documents, faits, personnesDuBien = [], contactsDuBien = [], onDeposer, onRemplir,
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
  // lot 9c : les contacts de la fiche par leur numéro ; `seul` = ni fiche fusionnée de couple, ni référence de couple
  contactsDuBien?: Array<{ id: string; seul: boolean }>
  onDeposer?: (typeCode: string, libelle: string) => void
}) {
  const regles = useGedPropositions()
  const [affaires, setAffaires] = useState<AffaireRegle[] | null>(null)
  const [classements, setClassements] = useState<Map<string, string>>(() => new Map())
  // morceau 6 : ce que l'IA a lu dans les documents déposés avec l'outil (la plus récente lecture par document)
  const [lectures, setLectures] = useState<Map<string, LectureDocument>>(() => new Map())
  // habillage H1 (16/11) : les pièces reçues sont des feuilles cochées, les moments précédents se choisissent en tête
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
    // morceau 9 (9b) : les pièces d'identité LUES -- le nom, la validité au jour de la signature, une pièce par personne
    return [...reglesSansIa(faits, docs, affaires, new Date()), ...reglesLues({ ...faits, chargeRegistre }, docsLus, personnesDuBien, affaires, new Date()),
      ...reglesPersonnes(faits, docsLus, personnesDuBien, affaires, new Date()), ...reglesFinancement(docs, docsLus, affaires, new Date()), ...reglesEtatCivil(docsLus, personnesDuBien)]
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
  // lot 9c : l'état civil des contacts du bien, relu à chaque fois (lecture ratée -> null -> aucune proposition contact).
  // L'écran donne le numéro HEKTOR (pont) ; la proposition porte NOTRE numéro (règle du 16/11 : le nôtre pour l'app).
  const idsContacts = useMemo(() => contactsDuBien.map((c) => c.id).join(','), [contactsDuBien])
  const [etatCivil, setEtatCivil] = useState<Map<string, EtatCivilLu> | null>(null)
  useEffect(() => {
    if (!remplir || !peutRemplir) return
    let annule = false
    void loadContactsEtatCivil(idsContacts ? idsContacts.split(',') : [], 'hektor').then((m) => { if (!annule) setEtatCivil(m) })
    return () => { annule = true }
  }, [remplir, peutRemplir, idsContacts, relire])
  const propositions = useMemo(() => {
    if (!remplir || !peutRemplir || !decisions || !conditions || affaires === null) return []
    const docsLus = documents
      .filter((d) => d.present_in_hektor !== false && lectures.has(d.id))
      .map((d) => ({ nom: d.document_name, lecture: lectures.get(d.id) as LectureDocument }))
    const contacts = etatCivil ? contactsDuBien.flatMap((c) => {
      const r = etatCivil.get(c.id)
      return r && r.archive !== true ? [{
        contactId: String(r.hektor_contact_id), nom: r.nom ?? '', prenom: r.prenom ?? '',
        personneSeule: c.seul && r.nature_fiche === 'personne_seule' && !r.couple_role,
        naissance: r.birth_date, lieu: r.birth_place, situation: r.marital_status,
      }] : []
    }) : []
    return [...propositionsRemplir({ ...faits, chargeRegistre }, docsLus, affaires, decisions, conditions),
      ...propositionsContact(contacts, personnesDuBien, docsLus, decisions, new Date())]
  }, [remplir, peutRemplir, decisions, conditions, affaires, documents, lectures, faits, chargeRegistre, etatCivil, contactsDuBien, personnesDuBien])
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

  // ── morceau 10 : JUGER chaque ligne « À regarder » (vrai / faux / déjà su), derrière `ged_propositions`. Lecture
  // ratée ou table pas encore posée (null) -> pas de boutons. Le jugement le plus récent d'une ligne fait foi.
  const [jugements, setJugements] = useState<Map<string, JugementGed> | null>(null)
  const [jugeEnCours, setJugeEnCours] = useState<string | null>(null)
  const [relireJugements, setRelireJugements] = useState(0)
  const [messageJuge, setMessageJuge] = useState<string | null>(null)
  useEffect(() => {
    if (!regles) return
    let annule = false
    void loadGedJugements(hektorAnnonceId).then((m) => { if (!annule) setJugements(m) })
    return () => { annule = true }
  }, [regles, hektorAnnonceId, relireJugements])
  const juger = async (a: Alerte, verdict: VerdictGed) => {
    const cle = cleJugement(a)
    if (jugeEnCours) return
    setJugeEnCours(cle); setMessageJuge(null)
    try {
      await gedJuger({ hektorAnnonceId, regle: a.code, cle, texte: a.texte, niveau: a.niveau, verdict })
    } catch (e) {
      setMessageJuge(e instanceof Error ? e.message : 'Le jugement n\'a pas été gardé.')
    } finally {
      setJugeEnCours(null); setRelireJugements((n) => n + 1)
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

  // ── habillage H1 (16/11, maquette https://claude.ai/artifact/S16jkpfnqtPF83xvUdkNtm) : LE DOSSIER. Les moments de la
  // vente en tête, une FEUILLE par pièce attendue (reçue : cochée ; non trouvée : à déposer). Mêmes données, mêmes gestes.
  const [momentVu, setMomentVu] = useState<MomentDossier | null>(null)
  const momentCourant = resultat.moment
  const indexCourant = ORDRE_MOMENTS.indexOf(momentCourant)
  const precedent = momentVu ? resultat.precedents.find((p) => p.moment === momentVu) ?? null : null
  const feuillesVues = precedent ? precedent.manquantes : resultat.pieces

  const feuille = (l: LignePiece, i: number) => {
    const recu = l.etat === 'recu'
    const delai = { animationDelay: `${i * 70}ms` } as const
    const titre = (
      <span className="gm2-fn">
        {l.libelle}
        {l.sensible ? <svg className="gm2-cad" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" role="img" aria-label="toujours privé"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg> : null}
      </span>
    )
    if (recu) {
      return (
        <div key={l.cle} className="gm2-f is-recu" style={delai} title={l.documents.map(avecLecture).join('\n')}>
          <span className="gm2-niveau" aria-hidden="true" style={{ animationDelay: `${220 + i * 70}ms` }} />
          <span className="gm2-ic is-recu" aria-hidden="true">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none"><path style={{ animationDelay: `${300 + i * 70}ms` }} d="M3.5 8.5l3 3 6-7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </span>
          {titre}
          <span className="gm2-fd">{`${l.dansUnDossier ? 'Dans un dossier de diagnostics : ' : ''}${l.documents.slice(0, 2).map(avecLecture).join(', ')}${l.documents.length > 2 ? ` (+${l.documents.length - 2})` : ''}`}</span>
        </div>
      )
    }
    const cas = l.etat === 'selon_le_cas'
    const contenu = (
      <>
        <span className={`gm2-ic is-${l.etat}`} aria-hidden="true">{cas ? '?' : '+'}</span>
        {titre}
        <span className="gm2-fd">{cas ? 'La fiche ne dit pas si elle est due' : onDeposer ? 'Non trouvée : déposer' : 'Non trouvée'}</span>
        <small className="gm2-fq">{NIVEAU[l.niveau]}{l.pourquoi ? ` : ${l.pourquoi}` : ''}</small>
      </>
    )
    if (onDeposer) {
      return (
        <button key={l.cle} type="button" className={`gm2-f is-${l.etat}`} style={delai} onClick={() => onDeposer(l.typeADeposer, l.libelle)} aria-label={`Déposer : ${l.libelle}`}>
          {contenu}
        </button>
      )
    }
    return <div key={l.cle} className={`gm2-f is-${l.etat}`} style={delai}>{contenu}</div>
  }

  const ETIQUETTE: Record<Alerte['niveau'], string> = { alerte: 'Alerte', piece: 'Pièce', info: 'Info' }

  return (
    <section className="gm gm2" aria-label="Reçu / manque">
      <div className="gm2-h">
        <h4>Le dossier</h4>
        <span>Reçu / manque, d'après le type de chaque document (son nom pour les anciens). Une pièce arrive, sa feuille se remplit.</span>
      </div>

      <ol className="gm2-moments" aria-label="Les moments de la vente">
        {ORDRE_MOMENTS.map((m, i) => {
          const passe = i < indexCourant
          const courant = i === indexCourant
          const manquantes = resultat.precedents.find((p) => p.moment === m)?.manquantes.length ?? 0
          const vu = momentVu ? momentVu === m : courant
          const ouvrable = courant || (passe && manquantes > 0)
          const compte = courant
            ? `${resultat.recues} pièce${resultat.recues > 1 ? 's' : ''} sur ${resultat.attendues}`
            : passe ? (manquantes ? `${manquantes} non trouvée${manquantes > 1 ? 's' : ''}` : 'complet') : 'à venir'
          return (
            <li key={m} className={`gm2-m${passe ? ' is-passe' : ''}${courant ? ' is-courant' : ''}`}>
              <button type="button" className="gm2-mb" aria-pressed={vu} disabled={!ouvrable} onClick={() => setMomentVu(courant ? null : m)}>
                <span className={`gm2-mp${passe && !manquantes ? ' is-fait' : ''}`} aria-hidden="true">{passe && !manquantes ? '✓' : String(i + 1)}</span>
                <span className="gm2-mt"><b>{LIBELLE_MOMENT[m]}</b><small>{compte}</small></span>
              </button>
            </li>
          )
        })}
      </ol>

      {precedent ? <p className="gm2-note" role="status">{`${LIBELLE_MOMENT[precedent.moment]} : les pièces obligatoires non trouvées.`}</p> : null}
      <div className="gm2-feuilles" key={momentVu ?? 'courant'}>{feuillesVues.map(feuille)}</div>

      {propositions.length || messageRemplir || alertes.length ? (
        <div className="gm2-col2">
          {propositions.length || messageRemplir ? (
            <div className="gm2-bloc">
              <p className="gm2-bt">{`À remplir (${propositions.length})`}</p>
              {messageRemplir ? <p className="gm2-msg" role="status">{messageRemplir}</p> : null}
              {propositions.map((p, i) => (
                <div key={`${p.cle}|${p.valeur}`} className="gm2-carte" style={{ animationDelay: `${i * 80}ms` }}>
                  <div className="gm2-c1"><span className="gm2-et is-remplir">Remplir</span><b>{p.texte}</b></div>
                  <small className="gm2-src">{`case vide : lu dans ${p.source}`}</small>
                  <div className="gm2-gestes">
                    <button type="button" className="gm2-b1" disabled={enCours !== null} onClick={() => void agir(p, 'remplir')}>{enCours === p.cle ? 'Écriture…' : p.geste === 'contact' ? 'Remplir la fiche du contact' : 'Remplir la fiche'}</button>
                    <button type="button" className="gm2-lien" disabled={enCours !== null} onClick={() => void agir(p, 'ignorer')}>Ignorer</button>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
          {alertes.length ? (
            <div className="gm2-bloc">
              <p className="gm2-bt">{`À regarder (${alertes.length})`}</p>
              {messageJuge ? <p className="gm2-msg" role="status">{messageJuge}</p> : null}
              {alertes.map((a, i) => {
                // morceau 10 : la carte porte son geste « Déposer » ET la barre de jugement (plus de ligne-bouton)
                const cle = cleJugement(a)
                const juge = jugements?.get(cle)
                return (
                  <div key={`${a.code}-${i}`} className="gm2-carte" style={{ animationDelay: `${120 + i * 80}ms` }}>
                    <div className="gm2-c1"><span className={`gm2-et is-${a.niveau}`}>{ETIQUETTE[a.niveau]}</span><b>{a.texte}</b></div>
                    <small className="gm2-src">{`${NIVEAU_ALERTE[a.niveau]} : ${a.pourquoi}`}</small>
                    <div className="gm2-gestes">
                      {a.typeADeposer && onDeposer ? (
                        <button type="button" className="gm2-b2" onClick={() => onDeposer(a.typeADeposer as string, LIBELLE_A_DEPOSER[a.typeADeposer as string] ?? a.texte)} aria-label={`Déposer : ${a.texte}`}>Déposer la pièce</button>
                      ) : null}
                      <span className="gm2-esp" />
                      {jugements ? (
                        <div className="gm2-juge" role="group" aria-label={`Juger : ${a.texte}`}>
                          <small>{juge ? `Jugé ${LIBELLE_VERDICT[juge.verdict]} le ${new Date(juge.jugeLe).toLocaleDateString('fr-FR')}` : 'Cette ligne est'}</small>
                          <span className="gm2-seg">
                            {VERDICTS.map((v) => (
                              <button key={v.code} type="button" className={`gm2-v is-${v.code}${juge?.verdict === v.code ? ' is-pris' : ''}`} disabled={jugeEnCours !== null} aria-pressed={juge?.verdict === v.code}
                                onClick={() => void juger(a, v.code)}>{jugeEnCours === cle ? '…' : v.libelle}</button>
                            ))}
                          </span>
                        </div>
                      ) : null}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : null}
        </div>
      ) : null}

      {lus.length ? (
        <div className="gm2-lus">
          <button type="button" className="gm2-pil" onClick={() => setOuvrirLus((v) => !v)} aria-expanded={ouvrirLus}>
            {`Lu par l'IA : ${lus.length} document${lus.length > 1 ? 's' : ''}`}
          </button>
          {ouvrirLus ? (
            <ul className="gm2-lus-l">
              {lus.map((l) => <li key={l.id}><b>{l.nom}</b> <span>{l.resume}</span></li>)}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
