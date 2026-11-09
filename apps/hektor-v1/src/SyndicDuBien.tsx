// CHANTIER PARTENAIRES · LOT 4, PIÈCE 4.2 (06/11/2026) — « SYNDIC DE LA COPROPRIÉTÉ » SUR LA FICHE D'UN BIEN.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §27.3-27.4. Règles : lib/syndicDuBien.ts.
// Écriture : `app_partenaire_syndic_du_bien` (droit sur le bien, partenaire = syndic du registre, l'ancien lien retiré daté).
// Lecture : `app_partenaire_syndic_du_bien_lire`. Rien chez Hektor (décision D2) ; ce que Hektor indique est seulement montré.
// « Ouvrir sa fiche » passe par le catalogue des partenaires (règle du 05/11 : une fiche métier s'ouvre depuis le catalogue).
// Plan, étape 2a (07/11, §28.6) : la carte lit et pose aussi par NOTRE numéro du bien (`app_dossier_id`) — une annonce
// née dans l'app a son syndic avant que Hektor rende son numéro (~90 s). Le numéro Hektor, quand il est là, reste passé.
import { useEffect, useMemo, useState } from 'react'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import { loadCoproRnie } from './lib/api'
import {
  choixSyndics, distinguerSyndic, ecartAvecHektor, lireSyndicDuBien, origineDuSyndic, syndicSelonHektor,
  type SyndicCatalogue, type SyndicDuBien as Syndic,
} from './lib/syndicDuBien'
import DemandeDocument from './DemandeDocument'
import type { BienDemande } from './lib/demandeDocument'
import './syndic-du-bien.css'

export const EVENEMENT_OUVRIR_PARTENAIRE = 'bienvu:ouvrir-partenaire'
// Plan, étape 2b (07/11, §28.6) : « ＋ Nouveau » demande à l'App principale (qui connaît les négociateurs) d'ouvrir la
// création de contact existante, réglée sur « partenaire » et le métier ; une fois le contact né (NOTRE numéro, tout de
// suite) et son métier écrit chez nous, elle rappelle `poser` avec son numéro.
export const EVENEMENT_CREER_PARTENAIRE = 'bienvu:creer-partenaire'
export type DemandeCreerPartenaire = { role: RoleDuBien; poser: (id: string, nom: string) => void }
const demanderNouveauPartenaire = (demande: DemandeCreerPartenaire) => {
  try { window.dispatchEvent(new CustomEvent<DemandeCreerPartenaire>(EVENEMENT_CREER_PARTENAIRE, { detail: demande })) } catch { /* noop */ }
}

// LOT 5 (06/11/2026) : la même carte sert au DIAGNOSTIQUEUR (role='diagnostiqueur') — geste générique
// `app_partenaire_du_bien` / `_lire` ; le syndic garde ses fonctions de la 4.2 (rien ne change pour lui).
export type RoleDuBien = 'syndic' | 'diagnostiqueur'
const TEXTES: Record<RoleDuBien, { titre: string; nom: string; aucun: string; choisir: string; action: string; chercher: string; icone: string }> = {
  syndic: { titre: 'Syndic de la copropriété', nom: 'syndic', aucun: 'Aucun syndic', choisir: '＋ Choisir le syndic', action: 'Demander un document',
    chercher: 'Chercher un syndic (nom, ville, n° ou téléphone)…', icone: 'M3 21h18M5 21V7l7-4 7 4v14M9 9h.01M15 9h.01M9 13h.01M15 13h.01' },
  diagnostiqueur: { titre: 'Diagnostiqueur', nom: 'diagnostiqueur', aucun: 'Aucun diagnostiqueur', choisir: '＋ Choisir le diagnostiqueur', action: 'Commander un diagnostic',
    chercher: 'Chercher un diagnostiqueur (nom, ville, n° ou téléphone)…', icone: 'M9 11l3 3 8-8M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9' },
}

async function lireLeSyndic(annonce: number | null, role: RoleDuBien = 'syndic', dossier: number | null = null): Promise<Syndic | null> {
  if (!hasSupabaseEnv || !supabase) throw new Error('base indisponible')
  const r = role === 'syndic'
    ? await supabase.rpc('app_partenaire_syndic_du_bien_lire', { p_hektor_annonce_id: annonce, p_app_dossier_id: dossier })
    : await supabase.rpc('app_partenaire_du_bien_lire', { p_role: role, p_hektor_annonce_id: annonce, p_app_dossier_id: dossier })
  if (r.error) throw new Error(r.error.message)
  return lireSyndicDuBien(r.data)
}

const cataloguePromesses = new Map<RoleDuBien, Promise<SyndicCatalogue[]>>()
async function lireLesSyndics(role: RoleDuBien): Promise<SyndicCatalogue[]> {
  if (!hasSupabaseEnv || !supabase) throw new Error('base indisponible')
  const reg = await supabase.from('app_partenaire_metier').select('contact_id').eq('metier', role).is('retire_le', null)
  if (reg.error) throw new Error(reg.error.message)
  const ids = Array.from(new Set((reg.data ?? []).map((r) => String((r as { contact_id: string }).contact_id))))
  // Combien de nos biens chaque fiche porte déjà : ce qui départage les homonymes (15 noms en double, 06/11).
  const liens = await supabase.from('app_partenaire_lien').select('partenaire_id').eq('role', role).eq('objet', 'bien').is('retire_le', null)
  if (liens.error) throw new Error(liens.error.message)
  const biens = new Map<string, number>()
  for (const l of (liens.data ?? []) as { partenaire_id: string }[]) biens.set(String(l.partenaire_id), (biens.get(String(l.partenaire_id)) ?? 0) + 1)
  const liste: SyndicCatalogue[] = []
  for (let i = 0; i < ids.length; i += 200) {
    const r = await supabase.from('app_contact_current').select('hektor_contact_id,display_name,prenom,nom,ville,archive,phone_primary,email')
      .in('hektor_contact_id', ids.slice(i, i + 200))
    if (r.error) throw new Error(r.error.message)
    for (const c of (r.data ?? []) as Record<string, unknown>[]) {
      if (c.archive === true) continue
      const nom = String(c.display_name ?? '').trim() || [c.prenom, c.nom].filter(Boolean).join(' ').trim() || `Contact ${c.hektor_contact_id}`
      const id = String(c.hektor_contact_id)
      liste.push({ id, nom, ville: String(c.ville ?? '').trim() || null, telephone: String(c.phone_primary ?? '').trim() || null,
        email: String(c.email ?? '').trim() || null, biens: biens.get(id) ?? 0 })
    }
  }
  return liste
}
// Après un choix, les comptes de biens changent : la prochaine ouverture du choix relit le catalogue.
const oublierLeCatalogue = (role: RoleDuBien) => { cataloguePromesses.delete(role) }
const syndicsDuCatalogue = (role: RoleDuBien) => {
  let p = cataloguePromesses.get(role)
  if (!p) { p = lireLesSyndics(role).catch((e) => { cataloguePromesses.delete(role); throw e }); cataloguePromesses.set(role, p) }
  return p
}

const Ico = (props: { d: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={props.d} /></svg>
)
const TEL = 'M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.6A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.4-1.2a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z'

export default function SyndicDuBien(props: {
  appDossierId: number | null
  hektorAnnonceId: number | null
  diagnosticsHektor: unknown       // detail.diagnostics_contacts_console_json (ce que Hektor indique)
  latitude?: number | null         // pour la proposition du registre des copropriétés (RNIC), lue au clic « Choisir »
  longitude?: number | null
  variante?: 'bureau' | 'telephone'   // téléphone = lecture seule (le choix au téléphone viendra avec 4.6)
  // 4.4 (06/11) : « Demander un document » à ce syndic pour CE bien (cran `partenaires_syndic_demande`).
  bienDemande?: BienDemande | null
  demandePossible?: boolean
  role?: RoleDuBien
  // 2b (07/11) : « ＋ Nouveau » dans le choix (crée le contact, son métier, puis le relie au bien).
  nouveauPossible?: boolean
  // 4a (07/11, planche 1 validée) : 'ticket' = la même carte, mêmes gestes, habillée en ticket (bande de la couleur du
  // métier) dans l'onglet Contact, cran `partenaires_design_contact`. Absent : la carte d'avant.
  habillage?: 'ticket'
}) {
  const role: RoleDuBien = props.role ?? 'syndic'
  const T = TEXTES[role]
  const annonce = props.hektorAnnonceId
  const dossier = props.appDossierId
  const bienConnu = Boolean(annonce || dossier)
  const lectureSeule = props.variante === 'telephone'
  const [lecture, setLecture] = useState<{ etat: 'chargement' | 'pret' | 'erreur'; syndic?: Syndic | null; erreur?: string }>({ etat: 'chargement' })
  const [version, setVersion] = useState(0)
  const [choix, setChoix] = useState(false)
  const [catalogue, setCatalogue] = useState<{ etat: 'chargement' | 'pret' | 'erreur'; liste?: SyndicCatalogue[]; erreur?: string }>({ etat: 'chargement' })
  const [recherche, setRecherche] = useState('')
  const [nomRnic, setNomRnic] = useState<string | null>(null)
  const [retrait, setRetrait] = useState(false)
  const [travail, setTravail] = useState<string | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [demande, setDemande] = useState(false)

  useEffect(() => {
    let annule = false
    if (!bienConnu) { setLecture({ etat: 'pret', syndic: null }); return }
    setLecture((avant) => (avant.etat === 'pret' ? avant : { etat: 'chargement' }))
    // Notre numéro quand Hektor n'a pas encore rendu le sien, ET toujours pour un bien né dans l'app (n° ≥ 10 000 000) :
    // ses liens sont posés sur notre numéro et ne reçoivent le numéro Hektor qu'à la complétion de :50 -- sans lui, la
    // carte affichait « Aucun » jusqu'à une heure (essai 10000213 / 63487, 08/11, §28.10). La lecture cherche par l'un OU
    // l'autre numéro. Pour les biens venus de Hektor, rien ne change (numéro Hektor seul).
    lireLeSyndic(annonce, role, !annonce || (dossier ?? 0) >= 10_000_000 ? dossier : null)
      .then((syndic) => { if (!annule) setLecture({ etat: 'pret', syndic }) })
      .catch((e: unknown) => { if (!annule) setLecture({ etat: 'erreur', erreur: e instanceof Error ? e.message : String(e) }) })
    return () => { annule = true }
  }, [annonce, dossier, bienConnu, version, role])

  // Le sélecteur : les syndics du catalogue (une lecture par session) et, une fois, la proposition du registre RNIC.
  useEffect(() => {
    if (!choix) return
    let annule = false
    syndicsDuCatalogue(role)
      .then((liste) => { if (!annule) setCatalogue({ etat: 'pret', liste }) })
      .catch((e: unknown) => { if (!annule) setCatalogue({ etat: 'erreur', erreur: e instanceof Error ? e.message : String(e) }) })
    const lat = Number(props.latitude), lon = Number(props.longitude)
    if (role === 'syndic' && nomRnic === null && Number.isFinite(lat) && Number.isFinite(lon) && lat && lon) {
      loadCoproRnie({ lat, lon })
        .then((r) => { if (!annule) setNomRnic(r.ok ? String(r.syndic_nom ?? '').trim() : '') })
        .catch(() => { if (!annule) setNomRnic('') })
    }
    return () => { annule = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [choix])

  const hektor = useMemo(() => syndicSelonHektor(props.diagnosticsHektor, role), [props.diagnosticsHektor, role])
  const syndic = lecture.syndic ?? null
  const ecart = lecture.etat === 'pret' ? ecartAvecHektor(syndic, hektor) : null
  const liste = useMemo(() => choixSyndics({
    catalogue: catalogue.liste ?? [], recherche, actuel: syndic?.partenaireId ?? null,
    nomRnic: nomRnic || null, nomHektor: hektor?.nom ?? null,
  }), [catalogue.liste, recherche, syndic?.partenaireId, nomRnic, hektor?.nom])

  async function ecrire(partenaire: string | null, retirer: boolean) {
    if (!hasSupabaseEnv || !supabase || !bienConnu) return
    setTravail(retirer ? 'retrait' : partenaire); setErreur(null)
    const r = role === 'syndic'
      ? await supabase.rpc('app_partenaire_syndic_du_bien', {
        p_app_dossier_id: props.appDossierId, p_hektor_annonce_id: annonce, p_partenaire: partenaire, p_retirer: retirer,
      })
      : await supabase.rpc('app_partenaire_du_bien', {
        p_role: role, p_app_dossier_id: props.appDossierId, p_hektor_annonce_id: annonce, p_partenaire: partenaire, p_retirer: retirer,
      })
    setTravail(null)
    if (r.error) { setErreur(r.error.message); return }
    setChoix(false); setRetrait(false); setRecherche('')
    oublierLeCatalogue(role)
    setVersion((v) => v + 1)
  }

  const ouvrirFiche = (id: string) => {
    try { window.dispatchEvent(new CustomEvent(EVENEMENT_OUVRIR_PARTENAIRE, { detail: { contactId: id } })) } catch { /* noop */ }
  }

  // Écart avec Hektor, erreur, « Demander un document », choix dans le catalogue : communs aux deux habillages.
  const dessous = (
    <>
      {ecart ? (
        <p className="sb-ecart">
          {syndic ? <>Hektor indique un autre {T.nom} : <b>{ecart}</b>. C'est celui de l'app qui compte ; Hektor n'est pas modifié.</>
            : <>Hektor indique : <b>{ecart}</b>, mais il n'est pas relié chez nous.</>}
        </p>
      ) : null}

      {erreur ? <p className="sb-erreur">{erreur}</p> : null}

      {demande && syndic && props.bienDemande ? (
        <DemandeDocument modele={role === 'syndic' ? 'copro' : 'diag'} syndicNom={syndic.nom} syndicEmail={syndic.email} biens={[props.bienDemande]} onClose={() => setDemande(false)} />
      ) : null}

      {choix && !lectureSeule ? (
        <div className="sb-choix">
          <input className="sb-recherche" type="search" placeholder={T.chercher} value={recherche}
            onChange={(e) => setRecherche(e.target.value)} autoFocus />
          {catalogue.etat === 'chargement' ? <p className="sb-vide">Lecture du catalogue…</p>
            : catalogue.etat === 'erreur' ? <p className="sb-erreur">Le catalogue n'a pas pu être lu : {catalogue.erreur}</p>
            : liste.length === 0 ? <p className="sb-vide">Aucun {T.nom} du catalogue ne correspond. Un {T.nom} absent s'ajoute depuis Contacts → Partenaires → « Ajouter un partenaire ».</p>
            : (
              <ul className="sb-liste">
                {liste.map((s) => (
                  <li key={s.id}>
                    <button type="button" disabled={travail !== null} onClick={() => void ecrire(s.id, false)}>
                      <span className="sb-l-nom">{s.nom}</span>
                      {s.ville ? <span className="sb-l-ville">{s.ville}</span> : null}
                      {s.homonymes > 1 ? <span className="sb-l-tag double" title="Plusieurs fiches portent ce nom : choisis celle qui porte déjà nos biens">{s.homonymes} fiches à ce nom</span> : null}
                      <span className="sb-l-detail">{distinguerSyndic(s)}</span>
                      {s.propose === 'rnic' ? <span className="sb-l-tag">proposé par le registre des copropriétés</span>
                        : s.propose === 'hektor' ? <span className="sb-l-tag">indiqué dans Hektor</span> : null}
                      {travail === s.id ? <span className="sb-l-tag">enregistrement…</span> : null}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          <div className="sb-choix-pied">
            {role === 'syndic' && nomRnic === null && props.latitude && props.longitude ? <span>Lecture du registre des copropriétés…</span>
              : nomRnic ? <span>Registre des copropriétés : {nomRnic}</span> : null}
            {props.nouveauPossible ? (
              <button type="button" className="sb-btn sb-choisir" disabled={travail !== null}
                onClick={() => demanderNouveauPartenaire({ role, poser: (id) => { oublierLeCatalogue(role); void ecrire(id, false) } })}>
                ＋ Nouveau {T.nom}
              </button>
            ) : null}
            <button type="button" className="sb-btn" onClick={() => { setChoix(false); setRecherche('') }}>Fermer</button>
          </div>
        </div>
      ) : null}
    </>
  )

  if (props.habillage === 'ticket' && !lectureSeule) {
    const etat = !bienConnu ? `Le bien n'a pas encore de numéro : le ${T.nom} se choisira quand il l'aura.`
      : lecture.etat === 'chargement' ? `Lecture du ${T.nom}…`
      : lecture.etat === 'erreur' ? `Le ${T.nom} n'a pas pu être lu : ${lecture.erreur}`
      : syndic ? [origineDuSyndic(syndic), syndic.ville, syndic.telephone].filter(Boolean).join(' · ')
      : "chez nous · Hektor n'est pas modifié"
    return (
      <section className={`sb-syndic sb-ticket${role === 'diagnostiqueur' ? ' diag' : ''}`} aria-label={T.titre}>
        <span className="sb-pic"><Ico d={T.icone} /></span>
        <span className="sb-pid">
          <span className="sb-met">{T.titre}</span>
          <span className={`sb-pnom${syndic ? '' : ' vide'}`}>{syndic ? syndic.nom : T.aucun}</span>
          <span className={`sb-orig${lecture.etat === 'erreur' ? ' sb-erreur' : ''}`}>{etat}</span>
        </span>
        {bienConnu && lecture.etat === 'pret' ? (
          <span className="sb-pact">
            {syndic ? (
              <span className="sb-mini">
                {syndic.telephone ? <a className="sb-lien" href={`tel:${syndic.telephone.replace(/\s+/g, '')}`}>Appeler</a> : null}
                <button type="button" className="sb-lien" onClick={() => ouvrirFiche(syndic.partenaireId)}>Ouvrir sa fiche</button>
                <button type="button" className="sb-lien" onClick={() => { setChoix((c) => !c); setRetrait(false) }}>Changer</button>
                <button type="button" className="sb-lien ret" onClick={() => { setRetrait(true); setChoix(false) }}>Retirer</button>
              </span>
            ) : null}
            {syndic && props.demandePossible && props.bienDemande ? (
              <button type="button" className="sb-gros" onClick={() => setDemande(true)}>{T.action}</button>
            ) : !syndic ? (
              <button type="button" className="sb-gros" onClick={() => setChoix((c) => !c)}>{T.choisir}</button>
            ) : null}
          </span>
        ) : null}
        {retrait && syndic ? (
          <div className="sb-confirme">
            <span>Retirer {syndic.nom} de ce bien ? La trace reste (qui, quand).</span>
            <button type="button" className="sb-btn sb-retirer" disabled={travail !== null} onClick={() => void ecrire(null, true)}>{travail === 'retrait' ? 'Retrait…' : 'Oui, retirer'}</button>
            <button type="button" className="sb-btn" onClick={() => setRetrait(false)}>Non</button>
          </div>
        ) : null}
        {dessous}
      </section>
    )
  }

  return (
    <section className={`sb-syndic${lectureSeule ? ' tel' : ''}${role === 'diagnostiqueur' ? ' diag' : ''}`} aria-label={T.titre}>
      <div className="sb-tete">
        <span className="sb-ic"><Ico d={T.icone} /></span>
        <span className="sb-titre">{T.titre}</span>
        <span className="sb-k">chez nous · Hektor n'est pas modifié</span>
      </div>

      {!bienConnu ? <p className="sb-vide">Le bien n'a pas encore de numéro : le {T.nom} se choisira quand il l'aura.</p>
        : lecture.etat === 'chargement' ? <p className="sb-vide">Lecture du {T.nom}…</p>
        : lecture.etat === 'erreur' ? <p className="sb-erreur">Le {T.nom} n'a pas pu être lu : {lecture.erreur}</p>
        : syndic ? (
          <div className="sb-carte">
            <div className="sb-nom">{syndic.nom}</div>
            <div className="sb-sous">{[syndic.ville, syndic.telephone].filter(Boolean).join(' · ') || `n° ${syndic.partenaireId}`}</div>
            <div className="sb-origine">{origineDuSyndic(syndic)}</div>
            <div className="sb-actions">
              {syndic.telephone ? <a className="sb-btn" href={`tel:${syndic.telephone.replace(/\s+/g, '')}`}><Ico d={TEL} />Appeler</a> : null}
              <button type="button" className="sb-btn" onClick={() => ouvrirFiche(syndic.partenaireId)}>Ouvrir sa fiche</button>
              {!lectureSeule && props.demandePossible && props.bienDemande ? (
                <button type="button" className="sb-btn sb-choisir" onClick={() => setDemande(true)}>{T.action}</button>
              ) : null}
              {!lectureSeule ? <>
                <button type="button" className="sb-btn" onClick={() => { setChoix((c) => !c); setRetrait(false) }}>Changer</button>
                <button type="button" className="sb-btn sb-retirer" onClick={() => { setRetrait(true); setChoix(false) }}>Retirer</button>
              </> : null}
            </div>
            {retrait ? (
              <div className="sb-confirme">
                <span>Retirer {syndic.nom} de ce bien ? La trace reste (qui, quand).</span>
                <button type="button" className="sb-btn sb-retirer" disabled={travail !== null} onClick={() => void ecrire(null, true)}>{travail === 'retrait' ? 'Retrait…' : 'Oui, retirer'}</button>
                <button type="button" className="sb-btn" onClick={() => setRetrait(false)}>Non</button>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="sb-carte vide">
            <div className="sb-nom vide">{T.aucun}</div>
            {!lectureSeule ? <button type="button" className="sb-btn sb-choisir" onClick={() => setChoix((c) => !c)}>{T.choisir}</button> : null}
          </div>
        )}

      {dessous}
    </section>
  )
}

// Plan, étape 2b (07/11, §28.6) : le même choix, AVANT que le bien existe (assistant de création). Rien n'est écrit ici :
// le choix est rendu au parent, qui pose le lien quand la création a rendu notre numéro du bien.
export type PartenaireChoisi = { id: string; nom: string }
export function ChoixPartenaire(props: {
  role: RoleDuBien
  valeur: PartenaireChoisi | null
  onChange: (valeur: PartenaireChoisi | null) => void
}) {
  const T = TEXTES[props.role]
  const [ouvert, setOuvert] = useState(false)
  const [catalogue, setCatalogue] = useState<{ etat: 'chargement' | 'pret' | 'erreur'; liste?: SyndicCatalogue[]; erreur?: string }>({ etat: 'chargement' })
  const [recherche, setRecherche] = useState('')
  useEffect(() => {
    if (!ouvert) return
    let annule = false
    syndicsDuCatalogue(props.role)
      .then((liste) => { if (!annule) setCatalogue({ etat: 'pret', liste }) })
      .catch((e: unknown) => { if (!annule) setCatalogue({ etat: 'erreur', erreur: e instanceof Error ? e.message : String(e) }) })
    return () => { annule = true }
  }, [ouvert, props.role])
  const liste = useMemo(() => choixSyndics({
    catalogue: catalogue.liste ?? [], recherche, actuel: props.valeur?.id ?? null, nomRnic: null, nomHektor: null,
  }), [catalogue.liste, recherche, props.valeur?.id])
  const choisir = (valeur: PartenaireChoisi) => { props.onChange(valeur); setOuvert(false); setRecherche('') }
  const nouveau = () => demanderNouveauPartenaire({ role: props.role, poser: (id, nom) => { oublierLeCatalogue(props.role); choisir({ id, nom }) } })

  return (
    <section className={`sb-syndic sb-saisie${props.role === 'diagnostiqueur' ? ' diag' : ''}`} aria-label={T.titre}>
      <div className="sb-tete">
        <span className="sb-ic"><Ico d={T.icone} /></span>
        <span className="sb-titre">{T.titre}</span>
        <span className="sb-k">relié au bien à l'enregistrement</span>
      </div>
      {props.valeur ? (
        <div className="sb-carte">
          <div className="sb-nom">{props.valeur.nom}</div>
          <div className="sb-actions">
            <button type="button" className="sb-btn" onClick={() => setOuvert((o) => !o)}>Changer</button>
            <button type="button" className="sb-btn sb-retirer" onClick={() => props.onChange(null)}>Retirer</button>
          </div>
        </div>
      ) : (
        <div className="sb-carte vide">
          <div className="sb-nom vide">{T.aucun}</div>
          <button type="button" className="sb-btn sb-choisir" onClick={() => setOuvert((o) => !o)}>{T.choisir}</button>
        </div>
      )}
      {ouvert ? (
        <div className="sb-choix">
          <input className="sb-recherche" type="search" placeholder={T.chercher} value={recherche}
            onChange={(e) => setRecherche(e.target.value)} autoFocus />
          {catalogue.etat === 'chargement' ? <p className="sb-vide">Lecture du catalogue…</p>
            : catalogue.etat === 'erreur' ? <p className="sb-erreur">Le catalogue n'a pas pu être lu : {catalogue.erreur}</p>
            : liste.length === 0 ? <p className="sb-vide">Aucun {T.nom} du catalogue ne correspond : « ＋ Nouveau {T.nom} » le crée.</p>
            : (
              <ul className="sb-liste">
                {liste.map((s) => (
                  <li key={s.id}>
                    <button type="button" onClick={() => choisir({ id: s.id, nom: s.nom })}>
                      <span className="sb-l-nom">{s.nom}</span>
                      {s.ville ? <span className="sb-l-ville">{s.ville}</span> : null}
                      {s.homonymes > 1 ? <span className="sb-l-tag double" title="Plusieurs fiches portent ce nom : choisis celle qui porte déjà nos biens">{s.homonymes} fiches à ce nom</span> : null}
                      <span className="sb-l-detail">{distinguerSyndic(s)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          <div className="sb-choix-pied">
            <button type="button" className="sb-btn sb-choisir" onClick={nouveau}>＋ Nouveau {T.nom}</button>
            <button type="button" className="sb-btn" onClick={() => { setOuvert(false); setRecherche('') }}>Fermer</button>
          </div>
        </div>
      ) : null}
    </section>
  )
}
