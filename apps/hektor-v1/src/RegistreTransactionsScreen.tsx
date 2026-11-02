import { useEffect, useMemo, useRef, useState } from 'react'
import {
  bienEstDansLesAnnonces, loadBienHistoriquePourStatut, loadDossierDeLaChaine, loadRegistreDossiers, loadRepartitionsDesChaines,
  type AffaireLedgerRow, type AffairePartieRow, type DossierDeLaChaine, type RegistreDossierRow, type RegistreEtape, type RepartitionLigne,
} from './lib/api'
import './registre-transactions.css'

// Registre des transactions -- étape « écran liste » (01/11/2026), derrière l'interrupteur
// `registre_transactions_ecran`. Une ligne = un DOSSIER (offre -> compromis -> vente).
// Étape 4 (02/11/2026) : un clic ouvre la FICHE DU DOSSIER (lecture), et ses boutons ouvrent la
// fenêtre de statut EXISTANTE sur la bonne transaction -- l'écran n'écrit rien lui-même.
// Les gestes ne sont proposés que si le bien est encore dans les annonces : un dossier vendu se
// modifie à l'étape 4C (note § 10).
// Maquette : https://claude.ai/artifact/3FA3yDqWuDWuqLdZAkvS8x · note : notice/AUDIT_GESTES_REGISTRE_TRANSACTIONS_2026-10-30.md § 8-10.
// ⛔ Aucun mot « Hektor » à l'écran (décision du 30/10) ; une lecture ratée se dit, sans détail technique.

export type GesteDuRegistre = { onglet: 'offre' | 'compromis' | 'vente'; appAffaireId: number | null; hektorAffaireId?: string | null }

type RegistreTransactionsScreenProps = {
  isAdmin: boolean
  libelleTypeBien?: (code: string | null | undefined) => string
  /** La fiche du bien : vivante, ou par le détail gardé d'un bien vendu ou clos. */
  onOuvrirBien?: (ligne: RegistreDossierRow) => void
  /** Ouvre la fenêtre de statut sur ce bien, cet onglet et cette transaction. Absent = pas de geste. */
  onGeste?: (ligne: RegistreDossierRow, geste: GesteDuRegistre) => void
  /** Vrai tant que la fenêtre de statut est ouverte : à sa fermeture, la liste et la fiche se relisent. */
  fenetreOuverte?: boolean
  onOuvrirContact?: (contactId: string) => void
}

const ETAPES: Array<{ cle: RegistreEtape; libelle: string }> = [
  { cle: 'offre_proposee', libelle: 'Offre proposée' },
  { cle: 'offre_acceptee', libelle: 'Offre acceptée' },
  { cle: 'compromis', libelle: 'Compromis' },
  { cle: 'vendu', libelle: 'Vendu' },
  { cle: 'compromis_annule', libelle: 'Compromis annulé' },
  { cle: 'offre_refusee', libelle: 'Offre refusée' },
]
const LIBELLE_ETAPE = Object.fromEntries(ETAPES.map((etape) => [etape.cle, etape.libelle])) as Record<RegistreEtape, string>
const EN_COURS: RegistreEtape[] = ['offre_proposee', 'offre_acceptee', 'compromis']

const PAR_PAGE = 50
const ANNEE_COURANTE = new Date().getFullYear()
const ANNEES = Array.from({ length: ANNEE_COURANTE - 2006 + 1 }, (_, index) => ANNEE_COURANTE - index)

type Tri = 'recent' | 'prix' | 'honoraires'

const euros = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
const entier = new Intl.NumberFormat('fr-FR')
const dateParis = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris' })

function formatEuros(valeur: number | null | undefined) {
  return valeur == null || Number.isNaN(valeur) ? '—' : euros.format(valeur)
}

function formatMillions(valeur: number) {
  if (Math.abs(valeur) >= 1_000_000) return `${(valeur / 1_000_000).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} M€`
  if (Math.abs(valeur) >= 10_000) return `${Math.round(valeur / 1000).toLocaleString('fr-FR')} k€`
  return euros.format(valeur)
}

// Les dates du registre sont du TEXTE, en plusieurs formes : « 2026-01-05 », « 2019-12-30 23:00:00 »
// (minuit à Paris écrit en UTC), « 2026-11-01T04:24:59Z », et « 0000-00-00 » pour une date vide.
function dateEnClair(valeur: string | null | undefined): string | null {
  const texte = String(valeur ?? '').trim()
  if (!texte || texte.startsWith('0000')) return null
  if (texte.length <= 10) {
    const [annee, mois, jour] = texte.split('-')
    return annee && mois && jour ? `${jour}/${mois}/${annee}` : texte
  }
  const iso = texte.replace(' ', 'T')
  const date = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  return Number.isNaN(date.getTime()) ? texte.slice(0, 10) : dateParis.format(date)
}

function anneeDe(valeur: string | null | undefined) {
  const texte = String(valeur ?? '').trim()
  return texte && !texte.startsWith('0000') ? Number(texte.slice(0, 4)) : null
}

function sansAccents(texte: string) {
  return texte.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

function nomPart(ligne: RepartitionLigne) {
  const nom = (ligne.nomAuMoment ?? '').trim()
  if (!nom) return 'Sans nom'
  if (/supprim/i.test(nom)) return 'Compte supprimé'
  return nom
}

function Repartition({ lignes }: { lignes: RepartitionLigne[] | undefined }) {
  if (lignes === undefined) return <span className="rt-mute">…</span>
  if (!lignes.length) return <span className="rt-mute">—</span>
  const cotes: Array<{ cle: 'entree' | 'sortie'; libelle: string }> = [
    { cle: 'entree', libelle: 'Entrée' },
    { cle: 'sortie', libelle: 'Sortie' },
  ]
  return (
    <div className="rt-repartition">
      {cotes.map(({ cle, libelle }) => {
        const parts = lignes.filter((ligne) => ligne.cote === cle).sort((a, b) => a.rang - b.rang)
        if (!parts.length) return null
        return (
          <div key={cle} className="rt-repartition-cote">
            <span className="rt-repartition-libelle">{libelle}</span>
            {parts.map((part) => (
              <span key={`${cle}-${part.rang}-${part.hektorUserId}`} className="rt-part">
                {nomPart(part)} <b>{entier.format(part.pourcentage)} %</b>
              </span>
            ))}
          </div>
        )
      })}
    </div>
  )
}

function Parcours({ ligne }: { ligne: RegistreDossierRow }) {
  const offre = dateEnClair(ligne.date_offre)
  const compromis = dateEnClair(ligne.date_compromis)
  const vente = dateEnClair(ligne.date_vente)
  const acte = dateEnClair(ligne.date_acte_prevue)
  const tombe = ligne.etape === 'compromis_annule' || ligne.etape === 'offre_refusee'
  const marches: Array<{ cle: string; libelle: string; date: string | null; etat: 'fait' | 'ici' | 'tombe' | 'vide' }> = [
    { cle: 'offre', libelle: 'Offre', date: offre, etat: ligne.etape === 'offre_refusee' ? 'tombe' : ligne.etape.startsWith('offre') ? 'ici' : offre || compromis || vente ? 'fait' : 'vide' },
    { cle: 'compromis', libelle: 'Compromis', date: compromis, etat: ligne.etape === 'compromis_annule' ? 'tombe' : ligne.etape === 'compromis' ? 'ici' : compromis || vente ? 'fait' : 'vide' },
    { cle: 'vente', libelle: ligne.etape === 'compromis' && acte ? 'Acte prévu' : 'Vente', date: vente ?? (ligne.etape === 'compromis' ? acte : null), etat: ligne.etape === 'vendu' ? 'ici' : 'vide' },
  ]
  return (
    <ol className={`rt-parcours${tombe ? ' is-tombe' : ''}`} aria-label="Parcours du dossier">
      {marches.map((marche) => (
        <li key={marche.cle} className={`rt-marche is-${marche.etat}`} title={`${marche.libelle}${marche.date ? ` : ${marche.date}` : ''}`}>
          <span className="rt-point" aria-hidden="true" />
          <span className="rt-marche-texte">
            <span className="rt-marche-libelle">{marche.libelle}</span>
            <span className="rt-marche-date">{marche.date ?? '—'}</span>
          </span>
        </li>
      ))}
    </ol>
  )
}

// ─── La fiche d'un dossier (étape 4, 02/11/2026) ───

const montantNombre = (valeur: unknown) => {
  const texte = String(valeur ?? '').trim().replace(',', '.')
  if (!texte) return null
  const nombre = Number(texte)
  return Number.isFinite(nombre) ? nombre : null
}

function libelleLigne(ligne: AffaireLedgerRow) {
  const etat = String(ligne.state ?? '').toLowerCase()
  if (ligne.kind === 'offre') return etat === 'accepted' ? 'Offre acceptée' : etat === 'refused' ? 'Offre refusée' : 'Offre proposée'
  if (ligne.kind === 'compromis') return etat === 'cancelled' ? 'Compromis annulé' : 'Compromis signé'
  if (ligne.kind === 'vente') return 'Vente actée'
  return 'Transaction'
}

function classeLigne(ligne: AffaireLedgerRow): RegistreEtape {
  const etat = String(ligne.state ?? '').toLowerCase()
  if (ligne.kind === 'offre') return etat === 'accepted' ? 'offre_acceptee' : etat === 'refused' ? 'offre_refusee' : 'offre_proposee'
  if (ligne.kind === 'compromis') return etat === 'cancelled' ? 'compromis_annule' : 'compromis'
  return 'vendu'
}

function joursJusqua(valeur: string | null | undefined) {
  const texte = String(valeur ?? '').trim()
  if (!texte || texte.startsWith('0000')) return null
  const cible = new Date(`${texte.slice(0, 10)}T12:00:00`)
  if (Number.isNaN(cible.getTime())) return null
  const aujourdhui = new Date()
  aujourdhui.setHours(12, 0, 0, 0)
  return Math.round((cible.getTime() - aujourdhui.getTime()) / 86_400_000)
}

const ROLES: Array<{ cle: string; libelle: string; pluriel: string }> = [
  { cle: 'vendeur', libelle: 'Vendeur', pluriel: 'Vendeurs' },
  { cle: 'acquereur', libelle: 'Acquéreur', pluriel: 'Acquéreurs' },
  { cle: 'notaire_vendeur', libelle: 'Notaire du vendeur', pluriel: 'Notaires du vendeur' },
  { cle: 'notaire_acquereur', libelle: 'Notaire de l’acquéreur', pluriel: 'Notaires de l’acquéreur' },
]

const ETAT_CONDITION: Record<string, string> = { attente: 'en attente', levee: 'levée', non_levee: 'non levée', sans_objet: 'sans objet' }

function FicheDossier(props: {
  ligne: RegistreDossierRow
  type: string | null
  relecture: number
  onRetour: () => void
  onOuvrirBien?: (ligne: RegistreDossierRow) => void
  onGeste?: (ligne: RegistreDossierRow, geste: GesteDuRegistre) => void
  onOuvrirContact?: (contactId: string) => void
}) {
  const { ligne, type, relecture, onRetour, onOuvrirBien, onGeste, onOuvrirContact } = props
  const [dossier, setDossier] = useState<DossierDeLaChaine | null>(null)
  const [vivant, setVivant] = useState<boolean | null>(null)
  // 4C : un bien hors annonces est dans l'historique (vendu ou clos) ou archivé (lecture seule).
  const [historique, setHistorique] = useState<boolean | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [essai, setEssai] = useState(0)
  const retourRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    retourRef.current?.focus()
  }, [ligne.app_chaine_id])

  useEffect(() => {
    let annule = false
    setErreur(null)
    Promise.all([
      loadDossierDeLaChaine(ligne.app_chaine_id),
      ligne.app_dossier_id == null ? Promise.resolve(false) : bienEstDansLesAnnonces(ligne.app_dossier_id),
    ])
      .then(async ([lu, estVivant]) => {
        const estHistorique = !estVivant && ligne.app_dossier_id != null
          ? (await loadBienHistoriquePourStatut(ligne.app_dossier_id)) != null
          : false
        if (annule) return
        setDossier(lu)
        setVivant(estVivant)
        setHistorique(estHistorique)
      })
      .catch((cause: unknown) => {
        console.error('[registre des transactions] fiche du dossier illisible', cause)
        if (!annule) setErreur('Ce dossier n’a pas pu être chargé. Réessayez dans un instant.')
      })
    return () => {
      annule = true
    }
  }, [ligne.app_chaine_id, ligne.app_dossier_id, relecture, essai])

  const lignes = dossier?.lignes ?? []
  const derniereDuGenre = (kind: string) => [...lignes].reverse().find((item) => item.kind === kind) ?? null
  const offre = derniereDuGenre('offre')
  const compromis = derniereDuGenre('compromis')
  const vente = derniereDuGenre('vente')
  const peutAgir = Boolean(onGeste && vivant && ligne.app_dossier_id != null)
  // 4C (02/11/2026) : bien vendu, dans l'historique -> seule LA VENTE se corrige (la base refuse toute
  // création hors annonces, et l'offre et le compromis sont verrouillés par la vente).
  const venteACorriger = onGeste && vivant === false && historique && ligne.app_dossier_id != null
    && vente && vente.present_in_hektor !== false ? vente : null
  const agir = (geste: GesteDuRegistre) => onGeste?.(ligne, geste)
  const corrigerLaVente = (cible: AffaireLedgerRow) => agir({ onglet: 'vente', appAffaireId: Number(cible.app_affaire_id), hektorAffaireId: cible.hektor_affaire_id == null ? null : String(cible.hektor_affaire_id) })

  // Le geste « suivant » de l'étape, en tête de fiche.
  const suivant: { libelle: string; geste: GesteDuRegistre } | null = !peutAgir ? null
    : ligne.etape === 'offre_proposee' && offre ? { libelle: 'Accepter ou refuser l’offre', geste: { onglet: 'offre', appAffaireId: offre.app_affaire_id } }
      : ligne.etape === 'offre_acceptee' ? { libelle: 'Passer au compromis', geste: { onglet: 'compromis', appAffaireId: null } }
        : ligne.etape === 'compromis' ? { libelle: 'Enregistrer la vente', geste: { onglet: 'vente', appAffaireId: null } }
          : null

  // Les parties : une personne par rôle, prise sur la transaction la plus récente qui la nomme.
  const parties = useMemo(() => {
    const rangDe = new Map(lignes.map((item, index) => [Number(item.app_affaire_id), index]))
    const triees = [...(dossier?.parties ?? [])].sort((a, b) => (rangDe.get(b.app_affaire_id) ?? 0) - (rangDe.get(a.app_affaire_id) ?? 0) || a.rang - b.rang)
    const parRole = new Map<string, AffairePartieRow[]>()
    const vus = new Set<string>()
    for (const partie of triees) {
      const qui = partie.hektor_contact_id ?? partie.app_contact_id ?? `${partie.app_affaire_id}-${partie.rang}`
      const cle = `${partie.role}|${qui}`
      if (vus.has(cle)) continue
      // On ne garde que les personnes de la transaction la plus récente pour ce rôle.
      const deja = parRole.get(partie.role)
      if (deja?.length && deja[0].app_affaire_id !== partie.app_affaire_id) continue
      vus.add(cle)
      parRole.set(partie.role, [...(deja ?? []), partie])
    }
    return parRole
  }, [dossier, lignes])

  const acquereursDe = (appAffaireId: number) => (dossier?.parties ?? [])
    .filter((partie) => partie.app_affaire_id === appAffaireId && partie.role === 'acquereur')
    .map((partie) => partie.nom || (partie.fiche_sans_nom ? 'Fiche sans nom' : null))
    .filter(Boolean)
    .join(', ')

  const prix = ligne.montant
  const netVendeur = montantNombre(compromis?.prix_net_vendeur) ?? montantNombre(offre?.prix_net_vendeur)
  const tauxHonoraires = prix && ligne.honoraires ? (ligne.honoraires / prix) * 100 : null
  const quatrieme = ligne.etape === 'vendu'
    ? { libelle: 'Vendu le', valeur: dateEnClair(ligne.date_vente), detail: ligne.date_compromis ? `compromis du ${dateEnClair(ligne.date_compromis)}` : '' }
    : ligne.etape === 'compromis'
      ? (() => {
          const jours = joursJusqua(ligne.date_acte_prevue)
          return {
            libelle: 'Acte prévu',
            valeur: dateEnClair(ligne.date_acte_prevue),
            detail: jours == null ? 'date non saisie' : jours > 0 ? `dans ${entier.format(jours)} jour${jours > 1 ? 's' : ''}` : jours === 0 ? 'aujourd’hui' : `dépassé de ${entier.format(-jours)} jour${jours < -1 ? 's' : ''}`,
            alerte: jours != null && jours < 0,
          }
        })()
      : { libelle: ligne.etape === 'compromis_annule' ? 'Compromis du' : 'Offre du', valeur: dateEnClair(ligne.etape === 'compromis_annule' ? ligne.date_compromis : ligne.date_offre), detail: '' }

  const conditions = lignes.flatMap((item) => (dossier?.conditions.get(Number(item.app_affaire_id)) ?? []).map((condition) => ({ ...condition, kind: item.kind })))
  const notes = lignes
    .map((item) => ({ kind: item.kind, libelle: libelleLigne(item), texte: (dossier?.notes.get(Number(item.app_affaire_id)) ?? '').trim() }))
    .filter((note) => note.texte)

  const titre = [type, ligne.ville || 'Ville inconnue'].filter(Boolean).join(' · ')

  return (
    <section className="rt-ecran rt-fiche" aria-labelledby="rt-fiche-titre">
      <nav className="rt-fiche-fil" aria-label="Fil d’Ariane">
        <button ref={retourRef} type="button" className="rt-bouton rt-retour" onClick={onRetour}>
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 6l-6 6 6 6" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" /></svg>
          Registre des transactions
        </button>
        <span className="rt-mute">Dossier N° {ligne.app_chaine_id}</span>
      </nav>

      <header className="rt-fiche-entete">
        <div className="rt-fiche-identite">
          {ligne.photo_url_listing ? (
            <img className="rt-fiche-photo" src={ligne.photo_url_listing} alt="" />
          ) : (
            <span className="rt-fiche-photo rt-vignette-vide" aria-hidden="true" />
          )}
          <div className="rt-fiche-titres">
            <span className="rt-fiche-pastilles">
              <span className={`rt-pastille is-${ligne.etape}`}>{LIBELLE_ETAPE[ligne.etape]}</span>
              {vivant === false && ligne.app_dossier_id != null ? <span className="rt-pastille is-neutre">Bien {String(ligne.statut_annonce ?? '').toLowerCase() || 'hors annonces'}</span> : null}
            </span>
            <h2 id="rt-fiche-titre" className="rt-fiche-titre">{titre}{ligne.code_postal ? <span className="rt-mute"> {ligne.code_postal}</span> : null}</h2>
            <span className="rt-mute">
              {[ligne.numero_mandat ? `Mandat ${ligne.numero_mandat}` : null, ligne.agence_nom, ligne.negociateur_email ? `suivi par ${ligne.negociateur_email}` : null].filter(Boolean).join(' · ') || '—'}
            </span>
          </div>
        </div>
        <div className="rt-fiche-actions-tete">
          {onOuvrirBien && ligne.app_dossier_id != null ? (
            <button type="button" className="rt-bouton" onClick={() => onOuvrirBien(ligne)}>Ouvrir la fiche du bien</button>
          ) : null}
          {suivant ? (
            <button type="button" className="rt-bouton rt-bouton-principal" onClick={() => agir(suivant.geste)}>{suivant.libelle}</button>
          ) : null}
          {venteACorriger ? (
            <button type="button" className="rt-bouton rt-bouton-principal" onClick={() => corrigerLaVente(venteACorriger)}>Modifier la vente</button>
          ) : null}
        </div>
      </header>

      <div className="rt-indicateurs" aria-label="Chiffres du dossier">
        <div className="rt-carte rt-indicateur">
          <span className="rt-indicateur-libelle">{ligne.etape === 'vendu' ? 'Prix de vente' : ligne.etape.startsWith('offre') ? 'Montant de l’offre' : 'Prix'}</span>
          <strong className="rt-indicateur-valeur rt-num">{formatEuros(prix)}</strong>
          <span className="rt-indicateur-detail">{ligne.nb_transactions > 1 ? `${ligne.nb_transactions} transactions dans ce dossier` : 'une transaction'}</span>
        </div>
        <div className="rt-carte rt-indicateur">
          <span className="rt-indicateur-libelle">Net vendeur</span>
          <strong className="rt-indicateur-valeur rt-num">{formatEuros(netVendeur)}</strong>
          <span className="rt-indicateur-detail">{netVendeur == null ? 'non renseigné' : 'au compromis'}</span>
        </div>
        <div className="rt-carte rt-indicateur">
          <span className="rt-indicateur-libelle">Honoraires</span>
          <strong className="rt-indicateur-valeur rt-num">{ligne.honoraires ? formatEuros(ligne.honoraires) : '—'}</strong>
          <span className="rt-indicateur-detail">
            {ligne.honoraires
              ? [`entrée ${formatEuros(ligne.honoraires_entree ?? 0)}`, `sortie ${formatEuros(ligne.honoraires_sortie ?? 0)}`, tauxHonoraires ? `${tauxHonoraires.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} % du prix` : null].filter(Boolean).join(' · ')
              : 'non renseignés'}
          </span>
        </div>
        <div className={`rt-carte rt-indicateur${'alerte' in quatrieme && quatrieme.alerte ? ' is-alerte' : ''}`}>
          <span className="rt-indicateur-libelle">{quatrieme.libelle}</span>
          <strong className="rt-indicateur-valeur rt-num">{quatrieme.valeur ?? '—'}</strong>
          <span className="rt-indicateur-detail">{quatrieme.detail}</span>
        </div>
      </div>

      {erreur ? (
        <div key="erreur" className="rt-carte rt-etat rt-etat-erreur" role="alert">
          <p>{erreur}</p>
          <button type="button" className="rt-bouton" onClick={() => setEssai((valeur) => valeur + 1)}>Réessayer</button>
        </div>
      ) : !dossier ? (
        <div key="chargement" className="rt-carte rt-etat" role="status">Chargement du dossier…</div>
      ) : (
        <div key="dossier" className="rt-fiche-grille">
          <div className="rt-fiche-colonne">
            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-parcours">
              <h3 id="rt-bloc-parcours" className="rt-bloc-titre">Parcours du dossier</h3>
              {!lignes.length ? <p className="rt-mute">Aucune transaction lisible pour ce dossier.</p> : (
                <ol className="rt-etapes">
                  {lignes.map((item) => {
                    const montant = montantNombre(item.montant)
                    const acquereurs = acquereursDe(Number(item.app_affaire_id))
                    const details = item.kind === 'offre'
                      ? [item.jours_validite ? `validité ${item.jours_validite} jours` : null, acquereurs || null]
                      : item.kind === 'compromis'
                        ? [
                            dateEnClair(item.date_fin_retractation) ? `fin de rétractation ${dateEnClair(item.date_fin_retractation)}` : null,
                            dateEnClair(item.date_acte) ? `acte prévu ${dateEnClair(item.date_acte)}` : null,
                            montantNombre(item.sequestre) ? `séquestre ${formatEuros(montantNombre(item.sequestre))}` : null,
                            acquereurs || null,
                          ]
                        : [acquereurs || null]
                    const retiree = item.present_in_hektor === false
                    const onglet: GesteDuRegistre['onglet'] = item.kind === 'offre' ? 'offre' : item.kind === 'compromis' ? 'compromis' : 'vente'
                    return (
                      <li key={item.app_affaire_id} className={`rt-etape is-${classeLigne(item)}${retiree ? ' is-retiree' : ''}`}>
                        <span className="rt-etape-point" aria-hidden="true" />
                        <div className="rt-etape-corps">
                          <div className="rt-etape-haut">
                            <b>{libelleLigne(item)}</b>
                            {retiree ? <span className="rt-pastille is-neutre">supprimée</span> : null}
                            <span className="rt-mute rt-num">{dateEnClair(item.date) ?? 'date inconnue'}</span>
                            <span className="rt-etape-montant rt-num">{formatEuros(montant)}</span>
                          </div>
                          {details.some(Boolean) ? <span className="rt-mute">{details.filter(Boolean).join(' · ')}</span> : null}
                        </div>
                        {peutAgir && !retiree ? (
                          <button type="button" className="rt-bouton rt-bouton-petit" onClick={() => agir({ onglet, appAffaireId: Number(item.app_affaire_id), hektorAffaireId: item.hektor_affaire_id == null ? null : String(item.hektor_affaire_id) })}>
                            Ouvrir
                          </button>
                        ) : venteACorriger && item.app_affaire_id === venteACorriger.app_affaire_id ? (
                          <button type="button" className="rt-bouton rt-bouton-petit" onClick={() => corrigerLaVente(venteACorriger)}>
                            Modifier
                          </button>
                        ) : null}
                      </li>
                    )
                  })}
                </ol>
              )}
              {onGeste && vivant === false && historique !== null && ligne.app_dossier_id != null ? (
                <p className="rt-fiche-remarque">
                  {venteACorriger
                    ? 'Ce bien n’est plus en annonce : la vente se corrige ici, mais aucune nouvelle transaction ne peut être créée.'
                    : historique
                      ? 'Ce bien n’est plus en annonce : ce dossier se consulte ici. Seule une vente se corrige depuis le registre.'
                      : 'Ce bien est archivé : ce dossier se consulte ici, il ne se modifie pas.'}
                </p>
              ) : null}
            </section>

            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-repartition">
              <div className="rt-bloc-tete">
                <h3 id="rt-bloc-repartition" className="rt-bloc-titre">Répartition des honoraires</h3>
                {(peutAgir && (vente ?? compromis ?? offre)) || venteACorriger ? (
                  <button
                    type="button"
                    className="rt-bouton rt-bouton-petit"
                    onClick={() => {
                      if (venteACorriger) return corrigerLaVente(venteACorriger)
                      const cible = vente ?? compromis ?? offre
                      if (cible) agir({ onglet: cible.kind === 'offre' ? 'offre' : cible.kind === 'compromis' ? 'compromis' : 'vente', appAffaireId: Number(cible.app_affaire_id), hektorAffaireId: cible.hektor_affaire_id == null ? null : String(cible.hektor_affaire_id) })
                    }}
                  >
                    Modifier
                  </button>
                ) : null}
              </div>
              {!dossier.repartition.length ? <p className="rt-mute">Aucune répartition saisie.</p> : (
                <ul className="rt-parts">
                  {[...dossier.repartition].sort((a, b) => (a.cote === b.cote ? a.rang - b.rang : a.cote === 'entree' ? -1 : 1)).map((part) => (
                    <li key={`${part.cote}-${part.rang}-${part.hektorUserId}`} className="rt-part-ligne">
                      <span className={`rt-part-cote is-${part.cote}`}>{part.cote === 'entree' ? 'Entrée' : 'Sortie'}</span>
                      <span className="rt-part-nom">{nomPart(part)}</span>
                      <span className="rt-mute rt-num">{entier.format(part.pourcentage)} %</span>
                      <b className="rt-num">{ligne.honoraires ? formatEuros((ligne.honoraires * part.pourcentage) / 100) : '—'}</b>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <div className="rt-fiche-colonne">
            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-parties">
              <h3 id="rt-bloc-parties" className="rt-bloc-titre">Les parties</h3>
              {!parties.size ? <p className="rt-mute">Aucune partie connue pour ce dossier.</p> : (
                <div className="rt-parties">
                  {ROLES.filter((role) => parties.get(role.cle)?.length).map((role) => {
                    const personnes = parties.get(role.cle) ?? []
                    return (
                      <div key={role.cle} className="rt-partie">
                        <span className="rt-indicateur-libelle">{personnes.length > 1 ? `${role.pluriel} · ${personnes.length}` : role.libelle}</span>
                        {personnes.map((personne) => {
                          const id = String(personne.hektor_contact_id ?? personne.app_contact_id ?? '').trim()
                          const nom = personne.nom || (personne.fiche_sans_nom ? 'Fiche sans nom' : id ? `Contact n° ${id}` : 'Contact inconnu')
                          return onOuvrirContact && id ? (
                            <button key={`${personne.app_affaire_id}-${personne.rang}-${id}`} type="button" className="rt-lien" onClick={() => onOuvrirContact(id)}>{nom}</button>
                          ) : (
                            <b key={`${personne.app_affaire_id}-${personne.rang}-${id}`}>{nom}</b>
                          )
                        })}
                      </div>
                    )
                  })}
                </div>
              )}
            </section>

            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-conditions">
              <h3 id="rt-bloc-conditions" className="rt-bloc-titre">Conditions suspensives</h3>
              {!conditions.length ? <p className="rt-mute">Aucune condition saisie.</p> : (
                <ul className="rt-conditions">
                  {conditions.map((condition, index) => (
                    <li key={`${condition.kind}-${condition.rang ?? index}`} className="rt-condition">
                      <b>{condition.libelle}</b>
                      <span className="rt-mute">
                        {[dateEnClair(condition.date_echeance) ? `échéance ${dateEnClair(condition.date_echeance)}` : null, ETAT_CONDITION[String(condition.etat ?? '')] ?? condition.etat].filter(Boolean).join(' · ')}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-notes">
              <h3 id="rt-bloc-notes" className="rt-bloc-titre">Notes</h3>
              {!notes.length ? <p className="rt-mute">Aucune note sur ce dossier.</p> : (
                <ul className="rt-notes">
                  {notes.map((note, index) => (
                    <li key={`${note.kind}-${index}`}>
                      <span className="rt-indicateur-libelle">{note.libelle}</span>
                      <p>{note.texte}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      )}
    </section>
  )
}

export default function RegistreTransactionsScreen({ isAdmin, libelleTypeBien, onOuvrirBien, onGeste, fenetreOuverte, onOuvrirContact }: RegistreTransactionsScreenProps) {
  const [annee, setAnnee] = useState<number | null>(ANNEE_COURANTE)
  const [lignes, setLignes] = useState<RegistreDossierRow[]>([])
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState<string | null>(null)
  const [relecture, setRelecture] = useState(0)
  const [etape, setEtape] = useState<RegistreEtape | 'en_cours' | null>(null)
  const [recherche, setRecherche] = useState('')
  const [seulementNomme, setSeulementNomme] = useState(false)
  const [tri, setTri] = useState<Tri>('recent')
  const [page, setPage] = useState(1)
  const [repartitions, setRepartitions] = useState<Map<string, RepartitionLigne[]>>(new Map())
  const [ouverte, setOuverte] = useState<RegistreDossierRow | null>(null)
  const [relectureFiche, setRelectureFiche] = useState(0)
  const fenetreEtaitOuverte = useRef(false)

  // À la fermeture de la fenêtre de statut ouverte depuis la fiche : on relit la fiche et la liste.
  useEffect(() => {
    if (fenetreOuverte) {
      fenetreEtaitOuverte.current = true
      return
    }
    if (!fenetreEtaitOuverte.current) return
    fenetreEtaitOuverte.current = false
    setRelectureFiche((valeur) => valeur + 1)
    setRepartitions(new Map())
    setRelecture((valeur) => valeur + 1)
  }, [fenetreOuverte])

  // La fiche suit la ligne relue (étape, montants) sans se fermer.
  useEffect(() => {
    setOuverte((avant) => (avant ? lignes.find((ligne) => ligne.app_chaine_id === avant.app_chaine_id) ?? avant : avant))
  }, [lignes])

  useEffect(() => {
    let annule = false
    setChargement(true)
    setErreur(null)
    loadRegistreDossiers(annee)
      .then((resultat) => {
        if (!annule) setLignes(resultat)
      })
      .catch((cause: unknown) => {
        console.error('[registre des transactions] lecture impossible', cause)
        if (!annule) {
          setLignes([])
          setErreur('Les dossiers n’ont pas pu être chargés. Réessayez dans un instant.')
        }
      })
      .finally(() => {
        if (!annule) setChargement(false)
      })
    return () => {
      annule = true
    }
  }, [annee, relecture])

  useEffect(() => setPage(1), [annee, etape, recherche, seulementNomme, tri])

  const aDesNommes = useMemo(() => lignes.some((ligne) => ligne.je_suis_nomme), [lignes])

  const chiffres = useMemo(() => {
    const ventes = lignes.filter((ligne) => ligne.etape === 'vendu' && (annee == null || anneeDe(ligne.date_vente) === annee))
    const compromis = lignes.filter((ligne) => ligne.etape === 'compromis')
    const offres = lignes.filter((ligne) => ligne.etape === 'offre_acceptee' || ligne.etape === 'offre_proposee')
    const somme = (liste: RegistreDossierRow[], cle: 'montant' | 'honoraires') => liste.reduce((total, ligne) => total + (ligne[cle] ?? 0), 0)
    const parEtape = new Map<RegistreEtape, number>()
    for (const ligne of lignes) parEtape.set(ligne.etape, (parEtape.get(ligne.etape) ?? 0) + 1)
    return {
      ventes: ventes.length,
      volume: somme(ventes, 'montant'),
      honoraires: somme(ventes, 'honoraires'),
      compromis: compromis.length,
      honorairesAttendus: somme(compromis, 'honoraires'),
      offres: offres.length,
      parEtape,
    }
  }, [lignes, annee])

  const filtrees = useMemo(() => {
    const mots = sansAccents(recherche.trim()).split(/\s+/).filter(Boolean)
    const resultat = lignes.filter((ligne) => {
      if (etape === 'en_cours' && !EN_COURS.includes(ligne.etape)) return false
      if (etape && etape !== 'en_cours' && ligne.etape !== etape) return false
      if (seulementNomme && !ligne.je_suis_nomme) return false
      if (!mots.length) return true
      const texte = sansAccents(
        [ligne.ville, ligne.code_postal, ligne.acquereur_nom, ligne.numero_mandat, ligne.app_chaine_id, ligne.hektor_annonce_id, ligne.agence_nom, ligne.negociateur_email]
          .filter((valeur) => valeur != null && valeur !== '')
          .join(' '),
      )
      return mots.every((mot) => texte.includes(mot))
    })
    const cle = (ligne: RegistreDossierRow) => String(ligne.date_dernier_evenement ?? '').replace(/^0000.*/, '')
    return resultat.sort((a, b) => {
      if (tri === 'prix') return (b.montant ?? -1) - (a.montant ?? -1)
      if (tri === 'honoraires') return (b.honoraires ?? -1) - (a.honoraires ?? -1)
      return cle(b).localeCompare(cle(a)) || b.app_chaine_id - a.app_chaine_id
    })
  }, [lignes, etape, recherche, seulementNomme, tri])

  const pages = Math.max(1, Math.ceil(filtrees.length / PAR_PAGE))
  const pageCourante = Math.min(page, pages)
  const visibles = useMemo(() => filtrees.slice((pageCourante - 1) * PAR_PAGE, pageCourante * PAR_PAGE), [filtrees, pageCourante])

  // La répartition se lit pour la PAGE affichée seulement (50 dossiers) : elle n'est pas dans la liste.
  useEffect(() => {
    const manquantes = visibles.map((ligne) => String(ligne.app_chaine_id)).filter((id) => !repartitions.has(id))
    if (!manquantes.length) return
    let annule = false
    loadRepartitionsDesChaines(manquantes).then((lues) => {
      if (annule) return
      setRepartitions((avant) => {
        const suite = new Map(avant)
        for (const id of manquantes) suite.set(id, lues.get(id) ?? [])
        return suite
      })
    })
    return () => {
      annule = true
    }
  }, [visibles, repartitions])

  const typeEnClair = (code: string | null) => {
    if (!code) return null
    const libelle = libelleTypeBien ? libelleTypeBien(code) : code
    return libelle && libelle !== '-' ? libelle : null
  }

  const ouvrir = (ligne: RegistreDossierRow) => setOuverte(ligne)

  if (ouverte) {
    return (
      <FicheDossier
        ligne={ouverte}
        type={typeEnClair(ouverte.type_bien)}
        relecture={relectureFiche}
        onRetour={() => setOuverte(null)}
        onOuvrirBien={onOuvrirBien}
        onGeste={onGeste}
        onOuvrirContact={onOuvrirContact}
      />
    )
  }

  const periode = annee == null ? 'toutes années' : String(annee)
  const filtres: Array<{ cle: RegistreEtape | 'en_cours' | null; libelle: string; nombre: number }> = [
    { cle: null, libelle: 'Tous', nombre: lignes.length },
    { cle: 'en_cours', libelle: 'En cours', nombre: EN_COURS.reduce((total, cle) => total + (chiffres.parEtape.get(cle) ?? 0), 0) },
    ...ETAPES.map((item) => ({ cle: item.cle, libelle: item.libelle, nombre: chiffres.parEtape.get(item.cle) ?? 0 })),
  ]

  return (
    <section className="rt-ecran" aria-labelledby="rt-titre">
      <header className="rt-entete">
        <div className="rt-entete-titres">
          <span className="rt-surtitre">Ventes</span>
          <h1 id="rt-titre" className="rt-titre">Registre des transactions</h1>
          <p className="rt-sous-titre">
            {chargement ? 'Chargement des dossiers…' : `${entier.format(lignes.length)} dossier${lignes.length > 1 ? 's' : ''} · ${periode} · une ligne par dossier, de l’offre à l’acte`}
            {!isAdmin ? ' · vos biens et les dossiers où vous êtes nommé' : ''}
          </p>
        </div>
        <label className="rt-periode">
          <span>Période</span>
          <select value={annee == null ? 'tout' : String(annee)} onChange={(event) => setAnnee(event.target.value === 'tout' ? null : Number(event.target.value))}>
            {ANNEES.map((valeur) => (
              <option key={valeur} value={valeur}>{valeur}</option>
            ))}
            <option value="tout">Toutes les années</option>
          </select>
        </label>
      </header>

      <div className="rt-indicateurs" aria-label="Indicateurs">
        <div className="rt-carte rt-indicateur">
          <span className="rt-indicateur-libelle">Honoraires actés · {periode}</span>
          <strong className="rt-indicateur-valeur">{chargement ? '…' : formatMillions(chiffres.honoraires)}</strong>
          <span className="rt-indicateur-detail">entrée + sortie, sur les ventes</span>
        </div>
        <div className="rt-carte rt-indicateur">
          <span className="rt-indicateur-libelle">Ventes actées</span>
          <strong className="rt-indicateur-valeur">{chargement ? '…' : entier.format(chiffres.ventes)}</strong>
          <span className="rt-indicateur-detail">{chargement ? '' : `${formatMillions(chiffres.volume)} de volume`}</span>
        </div>
        <div className="rt-carte rt-indicateur">
          <span className="rt-indicateur-libelle">Sous compromis</span>
          <strong className="rt-indicateur-valeur">{chargement ? '…' : entier.format(chiffres.compromis)}</strong>
          <span className="rt-indicateur-detail">{chargement ? '' : `${formatMillions(chiffres.honorairesAttendus)} d’honoraires attendus`}</span>
        </div>
        <div className="rt-carte rt-indicateur">
          <span className="rt-indicateur-libelle">Offres en cours</span>
          <strong className="rt-indicateur-valeur">{chargement ? '…' : entier.format(chiffres.offres)}</strong>
          <span className="rt-indicateur-detail">proposées ou acceptées</span>
        </div>
      </div>

      <div className="rt-carte rt-liste">
        <div className="rt-outils">
          <label className="rt-recherche">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth={2} /><path d="m20 20-3.5-3.5" stroke="currentColor" strokeWidth={2} strokeLinecap="round" /></svg>
            <span className="rt-cache">Rechercher un dossier</span>
            <input
              type="search"
              value={recherche}
              onChange={(event) => setRecherche(event.target.value)}
              placeholder="Ville, acquéreur, n° de mandat, de dossier ou d’annonce…"
            />
          </label>
          <label className="rt-tri">
            <span className="rt-cache">Trier</span>
            <select value={tri} onChange={(event) => setTri(event.target.value as Tri)}>
              <option value="recent">Plus récents</option>
              <option value="prix">Prix le plus haut</option>
              <option value="honoraires">Honoraires les plus hauts</option>
            </select>
          </label>
          {aDesNommes ? (
            <label className="rt-case">
              <input type="checkbox" checked={seulementNomme} onChange={(event) => setSeulementNomme(event.target.checked)} />
              <span>Où je suis nommé</span>
            </label>
          ) : null}
        </div>
        <div className="rt-filtres" role="group" aria-label="Étape du dossier">
          {filtres.map((filtre) => (
            <button
              key={filtre.cle ?? 'tous'}
              type="button"
              className={`rt-filtre${etape === filtre.cle ? ' is-actif' : ''}`}
              aria-pressed={etape === filtre.cle}
              onClick={() => setEtape(filtre.cle)}
            >
              {filtre.cle && filtre.cle !== 'en_cours' ? <span className={`rt-pastille-point is-${filtre.cle}`} aria-hidden="true" /> : null}
              {filtre.libelle}
              <span className="rt-compte">{chargement ? '…' : entier.format(filtre.nombre)}</span>
            </button>
          ))}
        </div>

        {erreur ? (
          <div className="rt-etat rt-etat-erreur" role="alert">
            <p>{erreur}</p>
            <button type="button" className="rt-bouton" onClick={() => setRelecture((valeur) => valeur + 1)}>Réessayer</button>
          </div>
        ) : chargement ? (
          <div className="rt-etat" role="status">Chargement des dossiers…</div>
        ) : !filtrees.length ? (
          <div className="rt-etat">{lignes.length ? 'Aucun dossier ne correspond à ces critères.' : `Aucun dossier pour ${periode}.`}</div>
        ) : (
          <>
            <div className="rt-table-boite">
              <table className="rt-table">
                <thead>
                  <tr>
                    <th scope="col">Dossier</th>
                    <th scope="col">Bien</th>
                    <th scope="col">Acquéreur</th>
                    <th scope="col">Parcours</th>
                    <th scope="col" className="rt-droite">Prix</th>
                    <th scope="col" className="rt-droite">Honoraires</th>
                    <th scope="col">Répartition</th>
                  </tr>
                </thead>
                <tbody>
                  {visibles.map((ligne) => {
                    const type = typeEnClair(ligne.type_bien)
                    return (
                      <tr key={ligne.app_chaine_id} className="is-ouvrable" onClick={() => ouvrir(ligne)}>
                        <td>
                          <div className="rt-dossier">
                            <span className={`rt-pastille is-${ligne.etape}`}>{LIBELLE_ETAPE[ligne.etape]}</span>
                            <span className="rt-mute rt-num">N° {ligne.app_chaine_id}</span>
                            {ligne.je_suis_nomme ? <span className="rt-nomme">nommé</span> : null}
                          </div>
                        </td>
                        <td>
                          <div className="rt-bien">
                            {ligne.photo_url_listing ? (
                              <img className="rt-vignette" src={ligne.photo_url_listing} alt="" loading="lazy" />
                            ) : (
                              <span className="rt-vignette rt-vignette-vide" aria-hidden="true" />
                            )}
                            <div className="rt-bien-texte">
                              <button type="button" className="rt-lien" onClick={(event) => { event.stopPropagation(); ouvrir(ligne) }}>
                                {ligne.ville || 'Ville inconnue'}
                              </button>
                              <span className="rt-mute">
                                {[type, ligne.numero_mandat ? `mandat ${ligne.numero_mandat}` : null].filter(Boolean).join(' · ') || '—'}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td>{ligne.acquereur_nom || <span className="rt-mute">—</span>}</td>
                        <td><Parcours ligne={ligne} /></td>
                        <td className="rt-droite rt-num">{formatEuros(ligne.montant)}</td>
                        <td className="rt-droite rt-num">{ligne.honoraires ? formatEuros(ligne.honoraires) : <span className="rt-mute">—</span>}</td>
                        <td><Repartition lignes={repartitions.get(String(ligne.app_chaine_id))} /></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <ul className="rt-cartes" aria-label="Dossiers">
              {visibles.map((ligne) => {
                const type = typeEnClair(ligne.type_bien)
                const derniere = dateEnClair(ligne.date_dernier_evenement)
                const contenu = (
                  <>
                    <span className="rt-carte-haut">
                      <span className={`rt-pastille is-${ligne.etape}`}>{LIBELLE_ETAPE[ligne.etape]}</span>
                      <span className="rt-mute rt-num">N° {ligne.app_chaine_id}{derniere ? ` · ${derniere}` : ''}</span>
                    </span>
                    <span className="rt-carte-milieu">
                      <span className="rt-carte-bien">
                        <b>{ligne.ville || 'Ville inconnue'}</b>
                        <span className="rt-mute">{[type, ligne.acquereur_nom].filter(Boolean).join(' · ') || '—'}</span>
                      </span>
                      <span className="rt-carte-prix">
                        <b className="rt-num">{formatEuros(ligne.montant)}</b>
                        <span className="rt-mute rt-num">{ligne.honoraires ? `${formatEuros(ligne.honoraires)} d’honoraires` : 'sans honoraires'}</span>
                      </span>
                    </span>
                  </>
                )
                return (
                  <li key={ligne.app_chaine_id}>
                    <button type="button" className="rt-carte-dossier" onClick={() => ouvrir(ligne)}>{contenu}</button>
                  </li>
                )
              })}
            </ul>

            <nav className="rt-pages" aria-label="Pages">
              <span className="rt-mute">
                {entier.format((pageCourante - 1) * PAR_PAGE + 1)}–{entier.format(Math.min(pageCourante * PAR_PAGE, filtrees.length))} sur {entier.format(filtrees.length)}
              </span>
              <span className="rt-pages-boutons">
                <button type="button" className="rt-bouton" disabled={pageCourante <= 1} onClick={() => setPage(pageCourante - 1)}>Précédent</button>
                <span className="rt-num">{pageCourante} / {pages}</span>
                <button type="button" className="rt-bouton" disabled={pageCourante >= pages} onClick={() => setPage(pageCourante + 1)}>Suivant</button>
              </span>
            </nav>
          </>
        )}
      </div>
    </section>
  )
}
