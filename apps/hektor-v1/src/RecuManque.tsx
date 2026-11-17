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
import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { createPortal } from 'react-dom'
import { createConsoleDocumentSignedUrl, dateOffreFaite, loadAffairesForDossier, loadConditionCatalogue, loadRegisterCycleAffaires } from './lib/api'
import { apercuPremierePage } from './lib/gedClassementIa'
import { etatFiableDuDocument } from './lib/etatSignatureMandat'
import { gedDecider, gedJuger, lireCarnetDetailStrict, lireConditionsAffairesStrict, lireDernierEnvoiAffairesStrict, loadContactsEtatCivil, loadGedClassements, loadGedDecisions, loadGedDecisionsDetail, loadGedJugements, useGedPropositions, useGedRemplir, type DecisionGed, type EtatCivilLu, type JugementGed } from './lib/ged'
import { cleJugement, LIBELLE_VERDICT, VERDICTS, type VerdictGed } from './lib/gedMesure'
import { propositionsRemplir, type FaitsRemplir, type PropositionRemplir } from './lib/gedRemplir'
import { propositionsContact } from './lib/gedRemplirContact'
import { dateEtatLue, loadGedLectures, resumeLecture, type LectureDocument } from './lib/gedLecture'
import { reglesPersonnes } from './lib/gedReglesPersonnes'
import { reglesFinancement } from './lib/gedReglesFinancement'
import { reglesEtatCivil } from './lib/gedReglesEtatCivil'
import { LIBELLE_MOMENT, recuManque, type LignePiece, type MomentDossier } from './lib/gedPieces'
import { deposeAuPlusTard, LIBELLE_A_DEPOSER, reglesSansIa, type AffaireRegle, type Alerte, type FaitsRegles } from './lib/gedRegles'
import { lireDateIso, type PersonneDuBien } from './lib/gedComparer'
import { reglesLues } from './lib/gedReglesLues'
import { bilansDuDossier, estGenreFiche, verdictDesChoix, type BilanCompromis as Bilan, type CatalogueCondition, type GenreBilan } from './lib/gedBilanCompromis'
import { bilansFiche } from './lib/gedBilanFiche'
import BilanCompromis, { MOTS, type ChoixBilan, type ResultatBilan } from './BilanCompromis'
import type { LigneBilan } from './lib/gedBilanCompromis'
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

// ── habillage H3 (16/11, planche « Après l'envoi ») : ce qu'on vient de décider reste À SA PLACE, replié en une ligne ;
// « La fiche du bien » montre les cases que les documents savent remplir (geste « fiche » de gedRemplir.ts) et leur
// valeur ACTUELLE, lue dans les faits de la fiche -- rien de neuf n'est lu. Une case remplie d'ici s'allume.
type Faite = { cle: string; message: string; sort: 'rempli' | 'ignore' | 'refus' | 'erreur' }
const AVANT: Record<PropositionRemplir['geste'], [string, string]> = {
  fiche: ['Fiche', 'vide'], contact: ['Fiche du contact', 'vide'], charge: ['Registre des mandats', 'vide'], condition: ['Compromis', 'aucune condition'], affaire: ['Transaction', 'vide'],
}
const jjmmaaaa = (d: Date) => `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`
const nombre = (v: string | number) => String(Math.round(Number(v) * 100) / 100).replace('.', ',')
// une valeur de case, en clair : celle de la fiche (faits) ou celle qu'une proposition vient d'écrire (texte brut)
function caseEnClair(champ: string, v: string | number | null | undefined): string | null {
  if (v == null || v === '' || (typeof v === 'number' && !Number.isFinite(v))) return null
  if (champ === 'dpe_cons') return `${Math.round(Number(v))} kWh/m²/an`
  if (champ === 'dpe_ges') return `${Math.round(Number(v))} kg CO₂/m²/an`
  if (champ === 'dpe_date' || champ === 'diag_risques_nat_tech_date') { const d = lireDateIso(String(v)); return d ? jjmmaaaa(d) : null }
  if (champ === 'copropriete_nb_lot') return `${Math.round(Number(v))} lots`
  if (champ === 'copropriete_quote_part') return `${nombre(v)} € par an`
  return String(v)
}
const CASES_FICHE: Array<{ champ: string; libelle: string; copro?: boolean; lire: (f: FaitsRegles & Partial<Pick<FaitsRemplir, 'quotePart' | 'erpDate'>>) => string | number | null | undefined }> = [
  { champ: 'dpe_cons', libelle: 'Consommation d\'énergie', lire: (f) => f.dpeConso },
  { champ: 'dpe_ges', libelle: 'Émissions', lire: (f) => f.dpeGes },
  { champ: 'dpe_date', libelle: 'Date du DPE', lire: (f) => f.dpeDate },
  { champ: 'diag_risques_nat_tech_date', libelle: 'Date de l\'état des risques', lire: (f) => f.erpDate },
  { champ: 'copropriete_nb_lot', libelle: 'Nombre de lots', copro: true, lire: (f) => f.nbLots },
  { champ: 'copropriete_quote_part', libelle: 'Charges du lot', copro: true, lire: (f) => f.quotePart },
]

// Un montant du registre (en euros, texte ou nombre) ; vide ou zéro -> null.
const euros = (v: string | number | null | undefined) => { const x = Number(v); return v != null && v !== '' && Number.isFinite(x) && x > 0 ? x : null }

export function RecuManque({
  hektorAnnonceId, appDossierId, documents, faits, personnesDuBien = [], contactsDuBien = [], onDeposer, onRemplir, onResultat, onBilan, peutModifierTransaction = false,
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
  // habillage H2 : la fenêtre de dépôt montre le moment et les pièces non trouvées, LUES ICI (une seule vérité)
  onResultat?: (r: { moment: MomentDossier; nonTrouvees: string[] }) => void
  // lot 10c (17/11) : « Ce que dit le compromis » -- l'écran du bien écrit les choix (conditions chez nous ; champs que
  // Hektor connaît par la modale « Modifier le compromis ») et rend le message. Sans lui, la fenêtre ne se montre pas.
  onBilan?: (b: Bilan, choix: Array<{ ligne: LigneBilan; choix: ChoixBilan }>) => Promise<ResultatBilan>
  peutModifierTransaction?: boolean
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

  // lot 10c : relire les transactions après un enregistrement de « Ce que dit le compromis » (conditions écrites)
  const [relireAffaires, setRelireAffaires] = useState(0)
  // Les transactions du bien (registre), lues seulement si les règles sont allumées. Une lecture ratée : les règles
  // qui en ont besoin se taisent (null), jamais « aucune transaction ».
  useEffect(() => {
    if (!regles || !appDossierId) return
    let annule = false
    loadAffairesForDossier(appDossierId)
      .then(async (rows) => {
        const vivantes = rows.filter((a) => a.present_in_hektor !== false)
        // lot 10c (17/11, audit) : on compare à ce que HEKTOR a. La colonne du registre porte sa valeur (relue chaque nuit) ;
        // le CARNET dit ce qui n'y est pas encore : une ligne « saisie_app » (l'ancien chemin « chez nous seulement », lot
        // 10a) n'est jamais partie -> la case compte comme VIDE (elle se propose à envoyer) ; une ligne de création ou de
        // modification pas encore jugée arrivée est EN ROUTE -> on compare à la valeur envoyée. Lu strictement : raté ->
        // on compare au registre, on ne propose rien.
        const carnet = await lireCarnetDetailStrict(vivantes.map((a) => Number(a.app_affaire_id))).catch(() => null)
        // le dernier envoi à Hektor de chaque transaction : en ERREUR, ce qui était « en route » n'y est pas (essai du 17/11)
        const envois = await lireDernierEnvoiAffairesStrict(vivantes.map((a) => Number(a.app_affaire_id))).catch(() => null)
        const conditions = await lireConditionsAffairesStrict(vivantes.map((a) => Number(a.app_affaire_id))).catch(() => null)
        if (annule) return
        setAffaires(vivantes.map((a) => {
          const c = carnet?.get(Number(a.app_affaire_id)) ?? {}
          const enAttente: Record<string, 'jamais_envoye' | 'en_route' | 'echec'> = {}
          const dernierEnvoi = envois?.get(Number(a.app_affaire_id)) ?? null
          const chezHektor = (champ: string, registre: string | number | null | undefined): string | number | null => {
            const l = c[champ]
            if (!l) return registre ?? null
            if (l.origine === 'saisie_app') { enAttente[champ] = 'jamais_envoye'; return null }
            if (!['arrivee', 'sans_objet'].includes(l.etat)) {
              // envoi raté : la valeur n'est pas chez Hektor -> la case compte comme vide (elle se propose de nouveau)
              if (dernierEnvoi === 'error') { enAttente[champ] = 'echec'; return null }
              enAttente[champ] = 'en_route'; return l.valeur
            }
            return registre ?? null
          }
          const date = chezHektor('date', a.date), dateActe = chezHektor('date_acte', a.date_acte)
          const montant = chezHektor('montant', a.montant), sequestre = chezHektor('sequestre', a.sequestre), net = chezHektor('prix_net_vendeur', a.prix_net_vendeur)
          // lot 2 : une offre se compare par la date de sa PROPOSITION (la colonne `date` porte son dernier mouvement) --
          // sauf si le carnet en dit autre chose (en route : la valeur envoyée ; jamais partie ou ratée : vide)
          const offre = String(a.kind) === 'offre'
          const validite = chezHektor('jours_validite', a.jours_validite)
          return {
            kind: String(a.kind), state: a.state ?? null, date: date == null ? null : String(date), dateActe: dateActe == null ? null : String(dateActe), id: Number(a.app_affaire_id),
            // morceau 7c : de quoi comparer une transaction lue (montant en euros ; acquéreurs : un objet seul ou une liste)
            montant: euros(montant), prixNetVendeur: euros(net), honorairesEntree: euros(a.honoraires_entree), honorairesSortie: euros(a.honoraires_sortie),
            acquereurs: (Array.isArray(a.acquereurs_json) ? a.acquereurs_json : a.acquereurs_json ? [a.acquereurs_json] : [])
              .map((p) => ({ nom: String((p as { nom?: unknown })?.nom ?? '').trim(), prenom: String((p as { prenom?: unknown })?.prenom ?? '').trim() }))
              .filter((p) => p.nom || p.prenom),
            sequestre: euros(sequestre), carnetLu: carnet !== null, enAttente,
            conditions: conditions ? (conditions.get(Number(a.app_affaire_id)) ?? []) : null,
            dateProposee: offre ? (c.date ? (date == null ? null : String(date)) : dateOffreFaite(a) || null) : null,
            joursValidite: offre ? euros(validite) : null,
          }
        }))
      })
      .catch(() => { if (!annule) setAffaires(null) })
    return () => { annule = true }
  }, [regles, appDossierId, relireAffaires])

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
  const [enCours, setEnCours] = useState<string | null>(null)
  // H3 : les décisions de cette visite, repliées ; les cases envoyées d'ici (en attendant la fiche relue) ; le vol
  const [faites, setFaites] = useState<Faite[]>([])
  const [envoyees, setEnvoyees] = useState<Record<string, string>>({})
  const [vol, setVol] = useState<{ valeur: string; x: number; y: number; dx: number; dy: number } | null>(null)
  // H3 : l'aperçu du document d'où vient une proposition, à la page lue (décision du 16/11 : « comme Ouvrir »)
  const [apercu, setApercu] = useState<{ cle: string; nom: string; page: number | null; vue: 'lecture' | { image: string; nbPages: number; page: number } | { erreur: string } } | null>(null)
  const [relire, setRelire] = useState(0)
  useEffect(() => {
    if (!remplir || !peutRemplir) return
    let annule = false
    void loadGedDecisions(hektorAnnonceId).then((d) => { if (!annule) setDecisions(d) })
    return () => { annule = true }
  }, [remplir, peutRemplir, hektorAnnonceId, relire])
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
    if (!remplir || !peutRemplir || !decisions || affaires === null) return []
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
    return [...propositionsRemplir({ ...faits, chargeRegistre }, docsLus, decisions),
      ...propositionsContact(contacts, personnesDuBien, docsLus, decisions, new Date())]
  }, [remplir, peutRemplir, decisions, affaires, documents, lectures, faits, chargeRegistre, etatCivil, contactsDuBien, personnesDuBien])
  const agir = async (p: PropositionRemplir, geste: 'remplir' | 'ignorer', depart?: HTMLElement | null) => {
    if (enCours || !onRemplir) return
    setEnCours(p.cle)
    let faite: Faite
    try {
      if (geste === 'remplir') {
        const message = await onRemplir(p)
        // le geste rend « Envoyé… » / « Enregistré… » quand il a écrit, « Rien écrit… » quand la relecture a refusé
        const ecrit = /^(Envoyé|Enregistré)/.test(message)
        faite = { cle: p.cle, message, sort: ecrit ? 'rempli' : 'refus' }
        // l'aperçu ouvert cède la place à « La fiche du bien » : la valeur y vole au rendu suivant
        if (ecrit && p.geste === 'fiche') { setApercu(null); window.requestAnimationFrame(() => window.requestAnimationFrame(() => envoler(p, depart))) }
      } else {
        await gedDecider({ hektorAnnonceId, lectureId: p.lectureId, cle: p.cle, champ: p.champ, valeur: p.valeur, decision: 'ignoree' })
        faite = { cle: p.cle, message: `Ignorée : ${p.texte}. Elle ne reviendra pas.`, sort: 'ignore' }
      }
    } catch (e) {
      faite = { cle: p.cle, message: e instanceof Error ? e.message : 'Rien n\'a été écrit.', sort: 'erreur' }
    } finally {
      setEnCours(null); setRelire((n) => n + 1)
    }
    setFaites((avant) => [...avant.filter((f) => f.cle !== p.cle), faite])
  }

  // H3 : la valeur écrite VOLE du bouton jusqu'à sa case de « La fiche du bien », qui s'allume (sans mouvement si
  // l'utilisateur l'a demandé : la case s'allume seulement).
  function envoler(p: PropositionRemplir, depart?: HTMLElement | null) {
    const affichee = caseEnClair(p.champ, p.valeur) ?? p.valeur
    setEnvoyees((avant) => ({ ...avant, [p.champ]: affichee }))
    const cible = document.querySelector(`[data-case="${p.champ}"]`)
    if (!depart || !cible || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
    const a = depart.getBoundingClientRect()
    const b = cible.getBoundingClientRect()
    setVol({ valeur: affichee, x: b.left + 8, y: b.top + 4, dx: a.left - b.left, dy: a.top - b.top })
    window.setTimeout(() => setVol(null), 760)
  }

  // H3 : le document d'où vient une proposition (par le numéro de sa lecture) et la page où la valeur a été lue
  const documentDe = (p: PropositionRemplir) => (p.lectureId ? documents.find((d) => lectures.get(d.id)?.id === p.lectureId) ?? null : null)
  const pageDe = (p: PropositionRemplir) => { const m = /, page (\d+)$/.exec(p.source); return m ? Number(m[1]) : null }
  // Décision de Frédéric (16/11) : l'aperçu passe par l'ouverture d'AUJOURD'HUI (createConsoleDocumentSignedUrl) -- le même
  // effet qu'un clic sur « Ouvrir », date de consultation comprise. Le fichier est dessiné DANS LE NAVIGATEUR (pdf.js),
  // rien ne part à l'IA ni au serveur de lecture. Un fichier pas encore au coffre se dit, il ne se cherche pas ailleurs.
  async function voirDocument(p: PropositionRemplir) {
    const d = documentDe(p)
    if (!d) return
    const page = pageDe(p)
    setApercu({ cle: p.cle, nom: d.document_name, page, vue: 'lecture' })
    // au téléphone, l'aperçu s'ouvre SOUS les cartes : on l'amène à l'écran (au bureau, à côté, rien ne bouge)
    window.requestAnimationFrame(() => document.querySelector('.gm2-apercu')?.scrollIntoView({
      block: 'nearest', behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    }))
    try {
      const url = await createConsoleDocumentSignedUrl(d)
      const reponse = await fetch(url)
      if (!reponse.ok) throw new Error(`le coffre a répondu ${reponse.status}`)
      const brut = await reponse.blob()
      const fichier = brut.type ? brut : new Blob([brut], { type: d.mime_type ?? '' })
      const vue = await apercuPremierePage(fichier, 720, page ?? 1)
      setApercu((a) => (a?.cle === p.cle ? { ...a, vue: vue ?? { erreur: 'ce format ne se dessine pas ici : ouvre-le depuis la liste.' } } : a))
    } catch (e) {
      const raison = e instanceof Error ? e.message : String(e)
      const texte = /non disponible dans le cloud/i.test(raison) ? 'le fichier n\'est pas encore au coffre : « Préparer » dans la liste des documents.' : raison
      setApercu((a) => (a?.cle === p.cle ? { ...a, vue: { erreur: texte } } : a))
    }
  }

  // H3 : les cases de « La fiche du bien » -- les cases de copropriété seulement pour un bien en copropriété (ou quand une
  // proposition les vise) ; le panneau ne se montre que s'il y a une case à remplir d'ici, ou une case venant d'être remplie.
  const casesFiche = CASES_FICHE
    .filter((c) => !c.copro || faits.copropriete === true || propositions.some((p) => p.champ === c.champ) || envoyees[c.champ])
    .map((c) => {
      const surLaFiche = caseEnClair(c.champ, c.lire(faits))
      return { ...c, valeur: surLaFiche ?? envoyees[c.champ] ?? null, allume: Boolean(envoyees[c.champ]) }
    })
  const ficheVisible = propositions.some((p) => p.geste === 'fiche') || Object.keys(envoyees).length > 0 || apercu !== null

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

  // ── lot 10c (17/11) : « CE QUE DIT LE COMPROMIS ». Derrière `ged_remplir` (elle écrit). Le catalogue des conditions
  // et le journal des décisions (avec leur date) sont relus ; une lecture ratée du journal -> la fenêtre ne s'ouvre pas.
  const peutBilan = remplir && Boolean(onBilan)
  const [catalogue, setCatalogue] = useState<CatalogueCondition[] | null>(null)
  const [journal, setJournal] = useState<Map<string, DecisionGed> | null>(null)
  const [bilanOuvert, setBilanOuvert] = useState<GenreBilan | null>(null)
  useEffect(() => {
    if (!peutBilan) return
    let annule = false
    void loadConditionCatalogue().then((c) => { if (!annule) setCatalogue(c.map((x) => ({ id: x.id, libelle: x.libelle }))) })
    return () => { annule = true }
  }, [peutBilan])
  useEffect(() => {
    if (!peutBilan) return
    let annule = false
    void loadGedDecisionsDetail(hektorAnnonceId).then((j) => { if (!annule) setJournal(j) })
    return () => { annule = true }
  }, [peutBilan, hektorAnnonceId, relire])
  // lot 2 (17/11) : un bilan par document de transaction lu -- l'offre, puis le compromis
  // lot 3 (18/11) : puis la fiche du bien face à ses documents (DPE, état des risques, copropriété, Carrez) -- sans attendre
  // les transactions (une lecture ratée du registre ne les fait pas taire)
  const bilans = useMemo(() => {
    if (!peutBilan) return []
    const docsLus = documents
      .filter((d) => d.present_in_hektor !== false && lectures.has(d.id))
      .map((d) => ({ nom: d.document_name, lecture: lectures.get(d.id) as LectureDocument }))
    const transactions = affaires === null || catalogue === null ? [] : bilansDuDossier(docsLus, affaires, catalogue)
    return [...transactions, ...bilansFiche(faits, docsLus)]
  }, [peutBilan, affaires, catalogue, documents, lectures, faits])
  // qui tranche : la transaction, un responsable ; la fiche, celui qui peut la remplir (les cartes « Remplir »)
  const peutTrancher = (b: Bilan) => (estGenreFiche(b.genre) ? peutRemplir : peutModifierTransaction)
  // à trancher : ni d'accord, ni déjà décidé, ni figé chez Hektor (une offre acceptée se montre, elle ne réclame rien)
  const aTrancherDe = (b: Bilan) => (journal ? b.lignes.filter((l) => l.etat !== 'accord' && !l.fige && !journal.has(`${l.cle}|${l.valeur}`)) : [])
  const documentDuBilanDe = (b: Bilan) => documents.find((d) => lectures.get(d.id)?.id === b.lectureId) ?? null
  const bilan = bilans.find((b) => b.genre === bilanOuvert) ?? null
  const cartesBilan = bilans.map((b) => ({ b, lignes: aTrancherDe(b) })).filter((x) => x.lignes.length)
  const aTrancher = cartesBilan.flatMap((x) => x.lignes)
  // une lecture NEUVE (moins de 30 minutes) avec quelque chose à trancher ouvre la fenêtre d'elle-même, une seule fois
  // par lecture et par navigateur (une commodité : sans mémoire, elle se rouvre, rien ne casse)
  const neuf = bilans.find((b) => b.lectureId && aTrancherDe(b).length && b.luLe && Date.now() - new Date(b.luLe).getTime() < 30 * 60 * 1000) ?? null
  const cleOuverture = neuf ? `ged-bilan-vu:${neuf.lectureId}` : null
  useEffect(() => {
    if (!cleOuverture || !neuf) return
    try { if (window.localStorage.getItem(cleOuverture)) return; window.localStorage.setItem(cleOuverture, '1') } catch { /* sans mémoire : on ouvre */ }
    setBilanOuvert(neuf.genre)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cleOuverture])
  // la modale « Modifier le compromis » a envoyé : ses lignes sont notées (écran principal) -> on relit journal et registre
  useEffect(() => {
    const relu = () => { setRelire((n) => n + 1); setRelireAffaires((n) => n + 1) }
    window.addEventListener('ged:decisions-changees', relu)
    return () => window.removeEventListener('ged:decisions-changees', relu)
  }, [])
  // la ligne « À regarder » qui dit la même chose qu'un bilan (sa note Vrai / Faux se déduit des choix)
  const alerteDuBilan = (g: GenreBilan, a: Alerte) => ({
    compromis: (a.code === 'L7' && a.texte.startsWith('Compromis')) || a.code === 'L20',
    offre: a.code === 'L7' && a.texte.startsWith('Offre'),
    dpe: a.code === 'L6',
    erp: false,
    copro_lots: a.code === 'L16' && a.texte.startsWith('Copropriété'),
    copro_charges: a.code === 'L16' && a.texte.startsWith('Charges'),
    surface: a.code === 'L15',
  })[g]
  const enregistrerBilan = async (choix: Array<{ ligne: LigneBilan; choix: ChoixBilan }>): Promise<ResultatBilan> => {
    if (!bilan || !onBilan) throw new Error('Rien n\'a été écrit.')
    const r = await onBilan(bilan, choix)
    // la mesure du morceau 10 : un choix vaut la note de la ligne « À regarder » qui disait la même chose
    const carte = new Map(choix.map((c) => [c.ligne.cle, c.choix]))
    for (const a of alertes.filter((x) => alerteDuBilan(bilan.genre, x))) {
      const verdict = verdictDesChoix(a.texte, a.code, bilan.lignes, carte)
      if (verdict) await gedJuger({ hektorAnnonceId, regle: a.code, cle: cleJugement(a), texte: a.texte, niveau: a.niveau, verdict }).catch(() => undefined)
    }
    setRelire((n) => n + 1); setRelireJugements((n) => n + 1); setRelireAffaires((n) => n + 1)
    return r
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
  useEffect(() => {
    onResultat?.({ moment: resultat.moment, nonTrouvees: resultat.pieces.filter((l) => l.etat === 'non_trouve').map((l) => l.libelle) })
  }, [resultat, onResultat])

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

      {propositions.length || faites.length || alertes.length || aTrancher.length ? (
        <div className="gm2-col2">
          {propositions.length || faites.length || aTrancher.length ? (
            <div className="gm2-bloc">
              <p className="gm2-bt">{`À remplir (${propositions.length + aTrancher.length})`}</p>
              {cartesBilan.map(({ b, lignes }) => (
                <div key={b.genre} className="gm2-carte gm2-prop gm2-cpv">
                  <div className="gm2-c1"><span className="gm2-et is-remplir">{MOTS[b.genre].etiquette}</span><b>{`Ce que dit ${MOTS[b.genre].le} : ${[
                    lignes.filter((l) => l.etat === 'trancher').length ? `${lignes.filter((l) => l.etat === 'trancher').length} à trancher` : null,
                    lignes.filter((l) => l.etat === 'ajouter').length ? `${lignes.filter((l) => l.etat === 'ajouter').length} à ajouter` : null,
                  ].filter(Boolean).join(', ')}`}</b></div>
                  <div className="gm2-pv">
                    <span>{lignes.map((l) => l.libelle).join(' · ')}</span>
                    <span>{`lu dans ${b.nom}`}</span>
                  </div>
                  <div className="gm2-gestes">
                    <button type="button" className="gm2-b1" onClick={() => setBilanOuvert(b.genre)}>Voir et trancher</button>
                  </div>
                </div>
              ))}
              {faites.map((f) => (
                <p key={f.cle} className={`gm2-faite is-${f.sort}`} role="status">
                  {f.sort === 'rempli' ? <svg className="gm2-coche" width="17" height="17" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg> : null}
                  <span>{f.message}</span>
                </p>
              ))}
              {propositions.map((p, i) => (
                <div key={`${p.cle}|${p.valeur}`} className="gm2-carte gm2-prop" style={{ animationDelay: `${i * 80}ms` }}>
                  <div className="gm2-c1"><span className="gm2-et is-remplir">Remplir</span><b>{p.texte}</b></div>
                  <div className="gm2-pv">
                    <span>{`${AVANT[p.geste][0]} : `}<i>{AVANT[p.geste][1]}</i></span>
                    <span>{`lu dans ${p.source}`}</span>
                  </div>
                  <div className="gm2-gestes">
                    <button type="button" className="gm2-b1" disabled={enCours !== null} onClick={(e) => void agir(p, 'remplir', e.currentTarget)}>{enCours === p.cle ? 'Écriture…' : p.geste === 'contact' ? 'Remplir la fiche du contact' : p.geste === 'affaire' ? 'Remplir la transaction' : 'Remplir la fiche'}</button>
                    <button type="button" className="gm2-lien" disabled={enCours !== null} onClick={() => void agir(p, 'ignorer')}>Ignorer</button>
                    {documentDe(p) ? (
                      <button type="button" className="gm2-lien gm2-voir" aria-pressed={apercu?.cle === p.cle} onClick={() => void voirDocument(p)}>Voir le document</button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
          {apercu ? (
            <div className="gm2-bloc gm2-fiche gm2-apercu" key={apercu.cle}>
              <div className="gm2-ap-t">
                <p className="gm2-bt">{`Le document : ${apercu.nom}${typeof apercu.vue === 'object' && 'page' in apercu.vue ? `, page ${apercu.vue.page}` : apercu.page ? `, page ${apercu.page}` : ''}`}</p>
                <button type="button" className="gm2-ap-x" aria-label="Fermer l'aperçu du document" onClick={() => setApercu(null)}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
                </button>
              </div>
              {apercu.vue === 'lecture' ? <span className="gm2-ap-page is-lit" aria-label="Aperçu en préparation" /> : null}
              {typeof apercu.vue === 'object' && 'image' in apercu.vue ? <img className="gm2-ap-page" src={apercu.vue.image} alt={`Page ${apercu.vue.page} de ${apercu.nom}`} /> : null}
              {typeof apercu.vue === 'object' && 'erreur' in apercu.vue ? <p className="gm2-faite is-refus">{`Pas d'aperçu : ${apercu.vue.erreur}`}</p> : null}
              <small className="gm2-src">{typeof apercu.vue === 'object' && 'nbPages' in apercu.vue ? `Page ${apercu.vue.page} sur ${apercu.vue.nbPages}, celle où la valeur a été lue. ` : ''}Rien ne s'écrit sans ton clic.</small>
            </div>
          ) : ficheVisible ? (
            <div className="gm2-bloc gm2-fiche">
              <p className="gm2-bt">La fiche du bien</p>
              <small className="gm2-src">Les cases que les documents savent remplir.</small>
              <dl>
                {casesFiche.map((c) => (
                  <div key={c.champ}>
                    <dt>{c.libelle}</dt>
                    <dd data-case={c.champ} className={c.valeur ? (c.allume ? 'is-allume' : '') : 'is-vide'}>{c.valeur ?? 'vide'}</dd>
                  </div>
                ))}
              </dl>
              <small className="gm2-src">Une case déjà remplie n'est jamais réécrite : la proposition ne vient pas.</small>
            </div>
          ) : null}
          {alertes.length ? (
            <div className={`gm2-bloc${ficheVisible ? ' gm2-large' : ''}`}>
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
              {lus.map((l) => (
                <li key={l.id}>
                  <b>{l.nom}</b> <span>{l.resume}</span>
                  {bilans.filter((b) => documentDuBilanDe(b)?.id === l.id).map((b) => (
                    <button key={b.genre} type="button" className="gm2-lien gm2-revoir" onClick={() => setBilanOuvert(b.genre)}>Revoir ce qu'il dit</button>
                  ))}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {vol ? createPortal(
        <span className="gm2-vol" aria-hidden="true" style={{ left: vol.x, top: vol.y, '--dx': `${vol.dx}px`, '--dy': `${vol.dy}px` } as CSSProperties}>{vol.valeur}</span>,
        document.body,
      ) : null}
      {bilan ? (
        <BilanCompromis key={bilan.genre} bilan={bilan} decisions={journal} peutModifier={peutTrancher(bilan)} document={documentDuBilanDe(bilan)}
          onFermer={() => setBilanOuvert(null)} onEnregistrer={enregistrerBilan} />
      ) : null}
    </section>
  )
}
