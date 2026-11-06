// CHANTIER PARTENAIRES · LOT 4, PIÈCE 4.2 (06/11/2026) — « SYNDIC DE LA COPROPRIÉTÉ » SUR LA FICHE D'UN BIEN.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §27.3-27.4. Règles : lib/syndicDuBien.ts.
// Écriture : `app_partenaire_syndic_du_bien` (droit sur le bien, partenaire = syndic du registre, l'ancien lien retiré daté).
// Lecture : `app_partenaire_syndic_du_bien_lire`. Rien chez Hektor (décision D2) ; ce que Hektor indique est seulement montré.
// « Ouvrir sa fiche » passe par le catalogue des partenaires (règle du 05/11 : une fiche métier s'ouvre depuis le catalogue).
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

// LOT 5 (06/11/2026) : la même carte sert au DIAGNOSTIQUEUR (role='diagnostiqueur') — geste générique
// `app_partenaire_du_bien` / `_lire` ; le syndic garde ses fonctions de la 4.2 (rien ne change pour lui).
export type RoleDuBien = 'syndic' | 'diagnostiqueur'
const TEXTES: Record<RoleDuBien, { titre: string; nom: string; aucun: string; choisir: string; action: string; chercher: string; icone: string }> = {
  syndic: { titre: 'Syndic de la copropriété', nom: 'syndic', aucun: 'Aucun syndic', choisir: '＋ Choisir le syndic', action: 'Demander un document',
    chercher: 'Chercher un syndic (nom, ville, n° ou téléphone)…', icone: 'M3 21h18M5 21V7l7-4 7 4v14M9 9h.01M15 9h.01M9 13h.01M15 13h.01' },
  diagnostiqueur: { titre: 'Diagnostiqueur', nom: 'diagnostiqueur', aucun: 'Aucun diagnostiqueur', choisir: '＋ Choisir le diagnostiqueur', action: 'Commander un diagnostic',
    chercher: 'Chercher un diagnostiqueur (nom, ville, n° ou téléphone)…', icone: 'M9 11l3 3 8-8M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9' },
}

async function lireLeSyndic(annonce: number, role: RoleDuBien = 'syndic'): Promise<Syndic | null> {
  if (!hasSupabaseEnv || !supabase) throw new Error('base indisponible')
  const r = role === 'syndic'
    ? await supabase.rpc('app_partenaire_syndic_du_bien_lire', { p_hektor_annonce_id: annonce })
    : await supabase.rpc('app_partenaire_du_bien_lire', { p_role: role, p_hektor_annonce_id: annonce })
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
}) {
  const role: RoleDuBien = props.role ?? 'syndic'
  const T = TEXTES[role]
  const annonce = props.hektorAnnonceId
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
    if (!annonce) { setLecture({ etat: 'pret', syndic: null }); return }
    setLecture((avant) => (avant.etat === 'pret' ? avant : { etat: 'chargement' }))
    lireLeSyndic(annonce, role)
      .then((syndic) => { if (!annule) setLecture({ etat: 'pret', syndic }) })
      .catch((e: unknown) => { if (!annule) setLecture({ etat: 'erreur', erreur: e instanceof Error ? e.message : String(e) }) })
    return () => { annule = true }
  }, [annonce, version, role])

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
    if (!hasSupabaseEnv || !supabase || !annonce) return
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

  return (
    <section className={`sb-syndic${lectureSeule ? ' tel' : ''}${role === 'diagnostiqueur' ? ' diag' : ''}`} aria-label={T.titre}>
      <div className="sb-tete">
        <span className="sb-ic"><Ico d={T.icone} /></span>
        <span className="sb-titre">{T.titre}</span>
        <span className="sb-k">chez nous · Hektor n'est pas modifié</span>
      </div>

      {!annonce ? <p className="sb-vide">Le bien n'a pas encore de numéro d'annonce : le {T.nom} se choisira quand il l'aura.</p>
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
            <button type="button" className="sb-btn" onClick={() => { setChoix(false); setRecherche('') }}>Fermer</button>
          </div>
        </div>
      ) : null}
    </section>
  )
}
