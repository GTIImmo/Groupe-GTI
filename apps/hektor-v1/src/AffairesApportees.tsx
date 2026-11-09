// CHANTIER PARTENAIRES · LOT 7 (09/11/2026) — « AFFAIRES APPORTÉES » sur la fiche d'un apporteur ou d'un parrain.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.17 ; règles pures : lib/affairesApportees.ts.
// Remplace, derrière le cran `partenaires_apporteur`, le bloc « en construction » de la fiche (même habillage) par ce qui
// EXISTE : les clients apportés (liens `objet client`, rôle apporteur) et l'étape que notre registre leur donne.
// « Noter une affaire apportée » : chercher le client (même recherche que « Ajouter un partenaire »), le choisir →
// `app_partenaire_du_client` (écrit chez nous seulement, rien chez Hektor). « Retirer » garde la trace (qui, quand).
// La commission reste « en construction ».
import { useEffect, useState, type CSSProperties } from 'react'
import { EnConstruction } from './FicheNotaire'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import { motifsDeRecherche } from './lib/ajouterPartenaire'
import { compterEtapes, etapeDuClient, trierApports, type ClientApporte } from './lib/affairesApportees'
import './affaires-apportees.css'

const nomDe = (c: Record<string, unknown>) =>
  String(c.display_name ?? '').trim() || [c.prenom, c.nom].filter(Boolean).join(' ').trim() || `Contact ${c.hektor_contact_id}`

export default function AffairesApportees(props: { partenaireId: string; peutEcrire: boolean; noterSignal?: number }) {
  const [liste, setListe] = useState<{ etat: 'chargement' | 'pret' | 'erreur'; clients: ClientApporte[]; erreur?: string }>({ etat: 'chargement', clients: [] })
  const [version, setVersion] = useState(0)
  const [noter, setNoter] = useState(false)
  const [saisie, setSaisie] = useState('')
  const [trouves, setTrouves] = useState<{ etat: 'vide' | 'chargement' | 'pret' | 'erreur'; lignes: { id: string; nom: string; detail: string }[]; erreur?: string }>({ etat: 'vide', lignes: [] })
  const [travail, setTravail] = useState<string | null>(null)
  const [aRetirer, setARetirer] = useState<string | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  // Le bouton de l'en-tête de la fiche ouvre le même panneau.
  useEffect(() => { if (props.noterSignal && props.peutEcrire) setNoter(true) }, [props.noterSignal, props.peutEcrire])

  useEffect(() => {
    if (!hasSupabaseEnv || !supabase) { setListe({ etat: 'erreur', clients: [], erreur: 'base indisponible' }); return }
    let vivant = true
    ;(async () => {
      try {
        const l = await supabase!.from('app_partenaire_lien').select('id,client_contact_id,pose_le')
          .eq('partenaire_id', props.partenaireId).eq('role', 'apporteur').eq('objet', 'client').is('retire_le', null)
        if (l.error) throw new Error(l.error.message)
        const liens = (l.data ?? []) as { id: number; client_contact_id: string; pose_le: string | null }[]
        const ids = liens.map((x) => String(x.client_contact_id))
        const fiches = new Map<string, Record<string, unknown>>()
        for (let i = 0; i < ids.length; i += 200) {
          const c = await supabase!.from('app_contact_current').select('hektor_contact_id,display_name,prenom,nom,ville,archive,relation_roles_json')
            .in('hektor_contact_id', ids.slice(i, i + 200))
          if (c.error) throw new Error(c.error.message)
          for (const f of (c.data ?? []) as Record<string, unknown>[]) fiches.set(String(f.hektor_contact_id), f)
        }
        const clients: ClientApporte[] = liens.map((x) => {
          const f = fiches.get(String(x.client_contact_id)) ?? {}
          const e = etapeDuClient(f.relation_roles_json)
          return { lienId: x.id, clientId: String(x.client_contact_id), nom: fiches.has(String(x.client_contact_id)) ? nomDe(f) : `Contact ${x.client_contact_id}`,
            ville: String(f.ville ?? '').trim() || null, archive: f.archive === true, poseLe: x.pose_le, etape: e.etape, libelle: e.libelle }
        })
        if (vivant) setListe({ etat: 'pret', clients: trierApports(clients) })
      } catch (e) {
        if (vivant) setListe({ etat: 'erreur', clients: [], erreur: e instanceof Error ? e.message : String(e) })
      }
    })()
    return () => { vivant = false }
  }, [props.partenaireId, version])

  // La recherche du client : dans tous les contacts, à la frappe (mêmes motifs que « Ajouter un partenaire »).
  useEffect(() => {
    const motifs = motifsDeRecherche(saisie)
    if (!noter || !motifs.length) { setTrouves({ etat: 'vide', lignes: [] }); return }
    if (!hasSupabaseEnv || !supabase) { setTrouves({ etat: 'erreur', lignes: [], erreur: 'base indisponible' }); return }
    let vivant = true
    setTrouves((t) => ({ ...t, etat: 'chargement' }))
    const t = window.setTimeout(async () => {
      try {
        const c = await supabase!.from('app_contact_current')
          .select('hektor_contact_id,display_name,prenom,nom,ville,phone_primary,email,archive')
          .or(motifs.flatMap((m) => ['search_text', 'email', 'phone_secondary'].map((col) => `${col}.ilike."${m}"`)).join(','))
          .or('couple_role.is.null,couple_role.neq.menage_resolu')
          .limit(15)
        if (c.error) throw new Error(c.error.message)
        const deja = new Set(liste.clients.map((x) => x.clientId))
        const lignes = ((c.data ?? []) as Record<string, unknown>[])
          .filter((x) => String(x.hektor_contact_id) !== props.partenaireId && !deja.has(String(x.hektor_contact_id)))
          .map((x) => ({ id: String(x.hektor_contact_id), nom: nomDe(x),
            detail: [String(x.ville ?? '').trim(), `n° ${x.hektor_contact_id}`, String(x.phone_primary ?? x.email ?? '').trim(), x.archive === true ? 'archivé' : '']
              .filter(Boolean).join(' · ') }))
        if (vivant) setTrouves({ etat: 'pret', lignes })
      } catch (e) {
        if (vivant) setTrouves({ etat: 'erreur', lignes: [], erreur: e instanceof Error ? e.message : String(e) })
      }
    }, 300)
    return () => { vivant = false; window.clearTimeout(t) }
  }, [saisie, noter, liste.clients, props.partenaireId])

  async function ecrire(clientId: string, retirer: boolean) {
    if (!supabase) return
    setTravail(clientId); setErreur(null)
    const { error } = await supabase.rpc('app_partenaire_du_client', { p_role: 'apporteur', p_client: clientId, p_partenaire: props.partenaireId, p_retirer: retirer })
    setTravail(null)
    if (error) { setErreur(error.message); return }
    setARetirer(null)
    if (!retirer) { setNoter(false); setSaisie('') }
    setVersion((v) => v + 1)
  }

  const etapes = compterEtapes(liste.clients)
  return (
    <>
      <div className="fa-cx-sec" style={{ ['--sc']: 'var(--ty)' } as CSSProperties}>
        <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round"><path d="M8 12h8M12 8l4 4-4 4" /><circle cx="12" cy="12" r="9" /></svg></span>
        Affaires apportées
        <span className="fa-cx-sec-meta">{liste.etat === 'pret' ? `${liste.clients.length} client${liste.clients.length > 1 ? 's' : ''}` : ''}</span>
        <span className="fa-cx-sec-ln" />
        {props.peutEcrire && !noter ? <button type="button" className="aa-noter" onClick={() => setNoter(true)}>＋ Noter une affaire apportée</button> : null}
      </div>
      <section className="fa-cx-mod full" style={{ marginBottom: 24 }}>
        <div className="fa-cx-stages">
          {Object.entries(etapes).map(([etape, n]) => (
            <div key={etape} className={`fa-cx-stage${n == null ? ' wip' : ''}`}><b>{n == null ? '—' : n}</b><span>{etape}</span></div>
          ))}
        </div>
        {noter ? (
          <div className="aa-panneau">
            <div className="aa-panneau-tete">
              <span>Quel client vous a-t-il apporté ?</span>
              <button type="button" className="aa-lien" onClick={() => { setNoter(false); setSaisie('') }}>Fermer</button>
            </div>
            <input className="aa-cherche" type="search" autoFocus value={saisie} onChange={(e) => setSaisie(e.target.value)}
              placeholder="Nom, téléphone, e-mail ou ville du client…" aria-label="Chercher le client apporté" />
            {trouves.etat === 'vide' ? <p className="aa-vide">Tape au moins 3 caractères.</p>
              : trouves.etat === 'chargement' && !trouves.lignes.length ? <p className="aa-vide">Recherche…</p>
              : trouves.etat === 'erreur' ? <p className="aa-erreur">La recherche a échoué : {trouves.erreur}</p>
              : !trouves.lignes.length ? <p className="aa-vide">Aucun contact ne correspond.</p>
              : (
                <ul className="aa-liste">
                  {trouves.lignes.map((c) => (
                    <li key={c.id}>
                      <span className="aa-id"><b>{c.nom}</b><small>{c.detail}</small></span>
                      <button type="button" className="aa-prim" disabled={travail !== null} onClick={() => void ecrire(c.id, false)}>{travail === c.id ? 'Enregistrement…' : 'Noter'}</button>
                    </li>
                  ))}
                </ul>
              )}
            <p className="aa-note">Le lien s'écrit chez nous seulement ; rien ne part chez Hektor.</p>
          </div>
        ) : null}
        {erreur ? <p className="aa-erreur">{erreur}</p> : null}
        {liste.etat === 'chargement' ? <div className="fa-cx-ech-empty">Lecture des affaires apportées…</div>
          : liste.etat === 'erreur' ? <div className="fa-cx-ech-empty aa-erreur">Les affaires apportées n'ont pas pu être lues : {liste.erreur}</div>
          : !liste.clients.length ? <div className="fa-cx-ech-empty">Aucune affaire apportée notée pour l'instant.{props.peutEcrire ? ' « Noter une affaire apportée » relie un client à cet apporteur.' : ''}</div>
          : (
            <ul className="aa-liste aa-apports">
              {liste.clients.map((c) => (
                <li key={c.lienId}>
                  <span className="aa-id"><b>{c.nom}{c.archive ? <em> · archivé</em> : null}</b>
                    <small>{[c.ville, `n° ${c.clientId}`, c.poseLe ? `noté le ${new Date(c.poseLe).toLocaleDateString('fr-FR')}` : null].filter(Boolean).join(' · ')}</small></span>
                  <span className={`aa-etape e-${c.etape}`}>{c.libelle}</span>
                  {props.peutEcrire ? (aRetirer === c.clientId ? (
                    <span className="aa-confirme">Retirer ?
                      <button type="button" className="aa-lien ret" disabled={travail !== null} onClick={() => void ecrire(c.clientId, true)}>Oui</button>
                      <button type="button" className="aa-lien" onClick={() => setARetirer(null)}>Non</button></span>
                  ) : <button type="button" className="aa-lien ret" onClick={() => setARetirer(c.clientId)}>Retirer</button>) : null}
                </li>
              ))}
            </ul>
          )}
        <div className="aa-commission">Commission convenue, due, réglée <EnConstruction titre="lot 7 · H1" /></div>
      </section>
    </>
  )
}
