// CHANTIER PARTENAIRES §28.13 (09/11/2026) — LA FENÊTRE « AJOUTER UN PARTENAIRE ».
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.13 ; maquette : canevas, planches 5 et 6 ; règles pures :
// lib/ajouterPartenaire.ts. Cran `partenaires_fenetre_ajout` (posé par App) : éteint, les fenêtres d'avant restent.
// Deux temps. CHERCHER d'abord, dans TOUS les contacts : celui qui a déjà ce métier se CHOISIT ; un contact qui ne l'a pas
// reçoit le métier (`app_partenaire_metier_ecrire`, rien chez Hektor). CRÉER seulement ensuite : une fiche courte, envoyée
// par le MÊME travail que la fenêtre client (`createHektorContactJob` → worker → Hektor), puis le métier est écrit chez
// nous et, ouverte depuis un bien, la fiche est reliée à ce bien (la carte s'en charge par `poser`).
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import { createHektorContactJob, fetchCommunesForPostalCode } from './lib/api'
import type { ConsoleJob, HektorNegotiatorOption } from './types'
import {
  METIERS_AJOUT, apparenceMetier, avertissementVille, compteRetenu, comptesHektor, detailContact, entreeCreation, ficheVide,
  grouperResultats, libellesMetier, manquesFiche, motifDeRecherche, type ContactTrouve, type FichePartenaire, type MetierAjout,
} from './lib/ajouterPartenaire'
import './ajouter-partenaire.css'

export type DemandeAjoutPartenaire = {
  metier?: MetierAjout
  // Ouverte depuis la carte d'un bien (syndic / diagnostiqueur) : le métier est fixé, et le contact retenu y est relié.
  metierFige?: boolean
  poser?: (id: string, nom: string) => void
}

const Ico = (props: { d: string; size?: number }) => (
  <svg width={props.size ?? 20} height={props.size ?? 20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={props.d} /></svg>
)
const nomDe = (c: Record<string, unknown>) =>
  String(c.display_name ?? '').trim() || [c.prenom, c.nom].filter(Boolean).join(' ').trim() || `Contact ${c.hektor_contact_id}`

export default function AjouterPartenaire(props: {
  demande: DemandeAjoutPartenaire
  negociateurs: HektorNegotiatorOption[]
  profileRole: string | null
  sessionEmail: string | null
  hektorUserId: string | null
  hektorUserEmail: string | null
  numeroDuTravail: (job: ConsoleJob) => string | null
  onTravail?: (job: ConsoleJob) => void
  onOuvrirFiche?: (id: string) => void
  onFermer: () => void
}) {
  const [metier, setMetier] = useState<MetierAjout>(props.demande.metier ?? 'syndic')
  const [temps, setTemps] = useState<'chercher' | 'creer'>('chercher')
  const [saisie, setSaisie] = useState('')
  const [recherche, setRecherche] = useState<{ etat: 'vide' | 'chargement' | 'pret' | 'erreur'; liste: ContactTrouve[]; erreur?: string }>({ etat: 'vide', liste: [] })
  const [comptes, setComptes] = useState<Record<string, number>>({})
  const [fiche, setFiche] = useState<FichePartenaire>(ficheVide)
  const [communes, setCommunes] = useState<string[]>([])
  const [travail, setTravail] = useState<string | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const ctx = { role: props.profileRole, sessionEmail: props.sessionEmail, hektorUserId: props.hektorUserId, hektorUserEmail: props.hektorUserEmail }
  const { dispo, defaut } = useMemo(() => comptesHektor(props.negociateurs, ctx),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [props.negociateurs, props.profileRole, props.sessionEmail, props.hektorUserId, props.hektorUserEmail])
  const [compteId, setCompteId] = useState<string>(defaut?.idUser ?? '')
  useEffect(() => { if (!compteId && defaut) setCompteId(defaut.idUser) }, [defaut, compteId])
  const choisi = dispo.find((n) => n.idUser === compteId) ?? null
  const compte = compteRetenu(choisi, dispo.length === 0, ctx)
  const L = libellesMetier(metier)
  const a = apparenceMetier(metier)
  const champRecherche = useRef<HTMLInputElement>(null)

  // Combien de fiches chaque métier compte déjà (les pastilles).
  useEffect(() => {
    if (!hasSupabaseEnv || !supabase) return
    let vivant = true
    void supabase.from('app_partenaire_metier').select('metier').is('retire_le', null).in('metier', METIERS_AJOUT.map((m) => m.metier))
      .then(({ data }) => {
        if (!vivant || !data) return
        const n: Record<string, number> = {}
        for (const r of data as { metier: string }[]) n[r.metier] = (n[r.metier] ?? 0) + 1
        setComptes(n)
      })
    return () => { vivant = false }
  }, [])

  // La recherche, à la frappe (3 caractères, pause de 300 ms), dans TOUS les contacts, sous la règle d'accès habituelle.
  useEffect(() => {
    const motif = motifDeRecherche(saisie)
    if (!motif) { setRecherche({ etat: 'vide', liste: [] }); return }
    if (!hasSupabaseEnv || !supabase) { setRecherche({ etat: 'erreur', liste: [], erreur: 'base indisponible' }); return }
    let vivant = true
    setRecherche((r) => ({ ...r, etat: 'chargement' }))
    const t = window.setTimeout(async () => {
      try {
        const c = await supabase!.from('app_contact_current')
          .select('hektor_contact_id,display_name,prenom,nom,ville,phone_primary,phone_secondary,email,archive')
          .or(`search_text.ilike.${motif},email.ilike.${motif},phone_secondary.ilike.${motif}`)
          .or('couple_role.is.null,couple_role.neq.menage_resolu')
          .limit(20)
        if (c.error) throw new Error(c.error.message)
        const lignes = (c.data ?? []) as Record<string, unknown>[]
        const ids = lignes.map((x) => String(x.hektor_contact_id))
        const metiers = new Map<string, string[]>()
        const biens = new Map<string, number>()
        if (ids.length) {
          const m = await supabase!.from('app_partenaire_metier').select('contact_id,metier').in('contact_id', ids).is('retire_le', null)
          if (m.error) throw new Error(m.error.message)
          for (const r of (m.data ?? []) as { contact_id: string; metier: string }[]) metiers.set(String(r.contact_id), [...(metiers.get(String(r.contact_id)) ?? []), r.metier])
          if (metier === 'syndic' || metier === 'diagnostiqueur') {
            const l = await supabase!.from('app_partenaire_lien').select('partenaire_id').in('partenaire_id', ids).eq('role', metier).eq('objet', 'bien').is('retire_le', null)
            if (l.error) throw new Error(l.error.message)
            for (const r of (l.data ?? []) as { partenaire_id: string }[]) biens.set(String(r.partenaire_id), (biens.get(String(r.partenaire_id)) ?? 0) + 1)
          }
        }
        const liste: ContactTrouve[] = lignes.map((x) => {
          const id = String(x.hektor_contact_id)
          return { id, nom: nomDe(x), ville: String(x.ville ?? '').trim() || null, telephone: String(x.phone_primary ?? x.phone_secondary ?? '').trim() || null,
            email: String(x.email ?? '').trim() || null, archive: x.archive === true, metiers: metiers.get(id) ?? [], biens: biens.get(id) ?? 0 }
        })
        if (vivant) setRecherche({ etat: 'pret', liste })
      } catch (e) {
        if (vivant) setRecherche({ etat: 'erreur', liste: [], erreur: e instanceof Error ? e.message : String(e) })
      }
    }, 300)
    return () => { vivant = false; window.clearTimeout(t) }
  }, [saisie, metier])

  // La ville suit le code postal (8a C-3).
  useEffect(() => {
    let vivant = true
    fetchCommunesForPostalCode(fiche.codePostal).then((l) => { if (vivant) setCommunes(l) }).catch(() => { if (vivant) setCommunes([]) })
    return () => { vivant = false }
  }, [fiche.codePostal])

  const groupes = grouperResultats(recherche.liste, metier)

  // Retenir un contact : le relier au bien (ouverte depuis un bien), sinon ouvrir sa fiche au catalogue.
  function retenir(id: string, nom: string) {
    props.onFermer()
    if (props.demande.poser) props.demande.poser(id, nom)
    else props.onOuvrirFiche?.(id)
  }
  async function donnerLeMetier(c: ContactTrouve) {
    if (!supabase) return
    setTravail(c.id); setErreur(null)
    const { error } = await supabase.rpc('app_partenaire_metier_ecrire', { p_contact: c.id, p_metier: metier, p_retirer: false })
    setTravail(null)
    if (error) { setErreur(`Le métier n'a pas pu être écrit : ${error.message}`); return }
    retenir(c.id, c.nom)
  }
  async function creer() {
    const manques = manquesFiche(fiche, Boolean(compte.email || compte.idUser))
    if (manques.length) { setErreur(`Il manque ${manques.join(', ')}.`); return }
    setTravail('creation'); setErreur(null)
    try {
      const job = await createHektorContactJob({ contact: entreeCreation(fiche, metier, compte), priority: 18 })
      props.onTravail?.(job)
      const id = props.numeroDuTravail(job)
      const nom = fiche.forme === 'societe' ? fiche.raisonSociale.trim() : [fiche.prenom, fiche.nom].map((s) => s.trim()).filter(Boolean).join(' ')
      if (!id || !supabase) { setTravail(null); setErreur(`La fiche est créée, mais son numéro n'est pas revenu : donne-lui le métier depuis sa fiche.`); return }
      const { error } = await supabase.rpc('app_partenaire_metier_ecrire', { p_contact: id, p_metier: metier, p_retirer: false })
      setTravail(null)
      if (error) { setErreur(`La fiche ${nom} est créée, mais son métier n'a pas pu être écrit : ${error.message}`); return }
      retenir(id, nom)
    } catch (e) {
      setTravail(null)
      setErreur(e instanceof Error ? e.message : String(e))
    }
  }
  const champ = (cle: keyof FichePartenaire) => ({
    value: fiche[cle] as string,
    onChange: (e: { target: { value: string } }) => setFiche((f) => ({ ...f, [cle]: e.target.value })),
  })
  const alerteVille = avertissementVille(fiche.codePostal, fiche.ville, communes)
  const sousTitre = temps === 'chercher'
    ? "Cherche d'abord : il existe peut-être déjà, au catalogue ou dans vos contacts."
    : saisie.trim() ? `« ${saisie.trim()} » n'a rien donné : on crée la fiche.` : 'Une fiche courte, envoyée comme toute création de contact.'

  return (
    <div className="ap-voile" onClick={props.onFermer}>
      <section className="ap-fen" role="dialog" aria-modal="true" aria-label={L.titre} style={{ ['--m']: a.couleur, ['--m-doux']: a.doux } as CSSProperties} onClick={(e) => e.stopPropagation()}>
        <header className="ap-tete">
          <span className="ap-pic"><Ico d={a.icone} size={22} /></span>
          <div className="ap-tete-tx">
            <h2 className="ap-titre">{temps === 'chercher' ? L.titre : L.nouveau}</h2>
            <p className="ap-sous">{sousTitre}</p>
          </div>
          <ol className="ap-etapes" aria-label="Étapes">
            <li className={temps === 'chercher' ? 'on' : 'fait'}><i>{temps === 'chercher' ? '1' : '✓'}</i>Chercher</li>
            <li className={temps === 'creer' ? 'on' : ''}><i>2</i>Créer</li>
          </ol>
          <button type="button" className="ap-fermer" aria-label="Fermer" onClick={props.onFermer}><Ico d="M6 6l12 12M18 6 6 18" size={14} /></button>
        </header>

        {temps === 'chercher' ? (
          <div className="ap-corps">
            {!props.demande.metierFige ? (
              <div className="ap-metiers" role="group" aria-label="Métier">
                {METIERS_AJOUT.map((m) => {
                  const ap = apparenceMetier(m.metier)
                  return (
                    <button key={m.metier} type="button" className={`ap-met${m.metier === metier ? ' on' : ''}`} aria-pressed={m.metier === metier}
                      style={{ ['--c']: ap.couleur } as CSSProperties} onClick={() => setMetier(m.metier)}>
                      <b><Ico d={ap.icone} size={13} /></b>{libellesMetier(m.metier).pastille}{comptes[m.metier] != null ? <small>{comptes[m.metier]}</small> : null}
                    </button>
                  )
                })}
              </div>
            ) : null}
            <label className="ap-cherche">
              <Ico d="M11 4a7 7 0 1 1 0 14 7 7 0 0 1 0-14zM20 20l-3.5-3.5" />
              <input ref={champRecherche} type="search" autoFocus value={saisie} onChange={(e) => setSaisie(e.target.value)}
                placeholder="Nom, téléphone, e-mail ou ville…" aria-label="Chercher dans tous les contacts" />
              <span className="ap-aide">dans tous les contacts</span>
            </label>

            <div className="ap-resultats" aria-live="polite">
              {recherche.etat === 'vide' ? <p className="ap-vide">Tape au moins 3 caractères.</p>
                : recherche.etat === 'chargement' && !recherche.liste.length ? <p className="ap-vide">Recherche…</p>
                : recherche.etat === 'erreur' ? <p className="ap-erreur">La recherche a échoué : {recherche.erreur}</p>
                : !recherche.liste.length ? <p className="ap-vide">Aucun contact ne correspond.</p>
                : (
                  <>
                    {groupes.deja.length ? (
                      <div className="ap-groupe">
                        <div className="ap-gt">{L.deja} <span>{groupes.deja.length}</span></div>
                        {groupes.deja.map((c) => (
                          <div key={c.id} className="ap-ligne">
                            <span className="ap-av">{c.nom.slice(0, 2).toUpperCase()}</span>
                            <span className="ap-id"><span className="ap-nom">{c.nom}{c.archive ? <em> · archivé</em> : null}</span>
                              <span className="ap-det">{detailContact(c)}{c.biens ? <b> · {c.biens} de nos biens</b> : null}</span></span>
                            {props.onOuvrirFiche && props.demande.poser ? <button type="button" className="ap-lien" onClick={() => { props.onFermer(); props.onOuvrirFiche?.(c.id) }}>Ouvrir sa fiche</button> : null}
                            <button type="button" className="ap-prim" disabled={travail !== null} onClick={() => retenir(c.id, c.nom)}>{props.demande.poser ? 'Choisir' : 'Ouvrir sa fiche'}</button>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {groupes.autres.length ? (
                      <div className="ap-groupe">
                        <div className="ap-gt">Dans vos contacts, sans ce métier <span>{groupes.autres.length}</span></div>
                        {groupes.autres.map((c) => (
                          <div key={c.id} className="ap-ligne client">
                            <span className="ap-av">{c.nom.slice(0, 2).toUpperCase()}</span>
                            <span className="ap-id"><span className="ap-nom">{c.nom}{c.archive ? <em> · archivé</em> : null}</span>
                              <span className="ap-det">{detailContact(c)}{c.metiers.length ? <> · {c.metiers.join(', ')}</> : null}</span></span>
                            <button type="button" className="ap-sec" disabled={travail !== null} onClick={() => void donnerLeMetier(c)}>
                              {travail === c.id ? 'Enregistrement…' : L.enFaire}
                            </button>
                          </div>
                        ))}
                        <p className="ap-note">« {L.enFaire} » : aucune nouvelle fiche, rien n'est créé chez Hektor — seul son métier s'ajoute chez nous.</p>
                      </div>
                    ) : null}
                  </>
                )}
              {erreur ? <p className="ap-erreur">{erreur}</p> : null}
            </div>
          </div>
        ) : (
          <div className="ap-corps ap-creer">
            <div className="ap-carte">
              <div className="ap-ligne-haut">
                <div className="ap-bascule" role="group" aria-label="Forme">
                  <button type="button" className={fiche.forme === 'societe' ? 'on' : ''} aria-pressed={fiche.forme === 'societe'} onClick={() => setFiche((f) => ({ ...f, forme: 'societe' }))}>Société</button>
                  <button type="button" className={fiche.forme === 'personne' ? 'on' : ''} aria-pressed={fiche.forme === 'personne'} onClick={() => setFiche((f) => ({ ...f, forme: 'personne' }))}>Personne</button>
                </div>
                {dispo.length > 1 || !choisi ? (
                  <label className="ap-compte">Créé sous
                    <select value={compteId} onChange={(e) => setCompteId(e.target.value)}>
                      <option value="">Choisir le négociateur</option>
                      {dispo.map((n) => <option key={n.idUser} value={n.idUser}>{n.label}{n.agenceNom ? ` · ${n.agenceNom}` : ''}</option>)}
                    </select>
                  </label>
                ) : <span className="ap-compte">Créé sous ton compte · <b>{choisi.label}</b></span>}
              </div>
              {fiche.forme === 'societe' ? (
                <>
                  <label className="ap-champ"><span>Raison sociale <em>*</em></span><input autoFocus {...champ('raisonSociale')} /></label>
                  <div className="ap-st">La personne à qui parler <small>(facultatif)</small></div>
                </>
              ) : null}
              <div className="ap-rang ap-r3">
                <label className="ap-champ"><span>Civilité</span>
                  <select {...champ('civilite')}><option value="">—</option><option value="M.">M.</option><option value="Mme.">Mme.</option></select></label>
                <label className="ap-champ"><span>Prénom</span><input {...champ('prenom')} /></label>
                <label className="ap-champ"><span>Nom{fiche.forme === 'personne' ? <em> *</em> : null}</span><input {...champ('nom')} /></label>
              </div>
              <div className="ap-st">Pour la joindre</div>
              <div className="ap-rang ap-r3b">
                <label className="ap-champ"><span>Téléphone</span><input inputMode="tel" {...champ('telephone')} /></label>
                <label className="ap-champ"><span>Portable</span><input inputMode="tel" {...champ('portable')} /></label>
                <label className="ap-champ"><span>E-mail</span><input type="email" {...champ('email')} /></label>
              </div>
              <div className="ap-rang ap-r3c">
                <label className="ap-champ"><span>Adresse</span><input {...champ('adresse')} /></label>
                <label className="ap-champ"><span>Code postal</span><input inputMode="numeric" {...champ('codePostal')} /></label>
                <label className="ap-champ"><span>Ville</span>
                  <input list="ap-communes" {...champ('ville')} />
                  <datalist id="ap-communes">{communes.map((c) => <option key={c} value={c} />)}</datalist>
                </label>
              </div>
              {alerteVille ? <p className="ap-alerte">{alerteVille}</p> : null}
              <div className="ap-rang ap-r2">
                <label className="ap-champ"><span>Site internet</span><input {...champ('site')} /></label>
                <label className="ap-champ"><span>Note</span><input {...champ('note')} /></label>
              </div>
              {erreur ? <p className="ap-erreur">{erreur}</p> : null}
            </div>
            <aside className="ap-droite">
              <div className="ap-ticket">
                <span className="ap-tpic"><Ico d={a.icone} size={18} /></span>
                <span><span className="ap-tmet">{L.pastille}</span>
                  <span className="ap-tnom">{(fiche.forme === 'societe' ? fiche.raisonSociale : [fiche.prenom, fiche.nom].join(' ')).trim() || '—'}</span>
                  <span className="ap-to">{[fiche.ville, fiche.telephone || fiche.portable || fiche.email].filter((s) => s.trim()).join(' · ') || ' '}</span></span>
              </div>
              <div className="ap-bloc">
                <h3>À l'enregistrement</h3>
                <ol className="ap-suite">
                  <li><i>1</i>La fiche naît chez nous, avec son numéro, tout de suite.</li>
                  <li><i>2</i>Elle part chez Hektor, comme toute création de contact.</li>
                  <li><i>3</i>Son métier « {L.pastille.toLowerCase()} » s'inscrit : elle entre au catalogue.</li>
                  {props.demande.poser ? <li><i>4</i>Elle est reliée au bien.</li> : null}
                </ol>
              </div>
              <div className="ap-bloc">
                <h3>Réglé pour un partenaire</h3>
                <ul className="ap-fixe">
                  <li>Type « partenaire », métier {L.pastille.toLowerCase()}</li>
                  <li>Pas d'e-mail « espace client »</li>
                  <li>Pas d'automatismes clients</li>
                </ul>
              </div>
            </aside>
          </div>
        )}

        <footer className="ap-pied">
          {temps === 'chercher' ? (
            <>
              <span className="ap-pt">Aucun ne correspond ?<small>Une fiche neuve ne se crée qu'après cette recherche.</small></span>
              <button type="button" className="ap-prim ap-gros" disabled={saisie.trim().length < 3} onClick={() => { setErreur(null); setTemps('creer')
                setFiche((f) => (f.raisonSociale || f.nom ? f : { ...f, raisonSociale: /\d/.test(saisie) ? '' : saisie.trim() })) }}>{L.nouveauBouton}</button>
            </>
          ) : (
            <>
              <button type="button" className="ap-lien" onClick={() => { setErreur(null); setTemps('chercher') }}>‹ Revenir à la recherche</button>
              <button type="button" className="ap-sec" onClick={props.onFermer}>Annuler</button>
              <button type="button" className="ap-prim ap-gros" disabled={travail !== null} onClick={() => void creer()}>{travail === 'creation' ? 'Création…' : L.creer}</button>
            </>
          )}
        </footer>
      </section>
    </div>
  )
}
