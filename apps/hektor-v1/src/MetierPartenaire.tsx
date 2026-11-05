// CHANTIER PARTENAIRES · LOT 3 — LE MÉTIER D'UN PARTENAIRE SUR LA FICHE CONTACT.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §24-25 ; maquettes fiche-partenaire-v1.html, fenetre-metier-v1.html.
//   3.1 (05/11) : le bloc « Métier » du volet gauche — LECTURE du registre `app_partenaire_metier` (lignes actives du
//       contact, par NOTRE numéro). Cran app_setting « partenaires_ecran ».
//   3.2 (05/11) : la fenêtre « Métier du contact » — ajouter / retirer, par `app_partenaire_metier_ecrire` (auteur et date
//       gardés ; retirer = dater, jamais effacer ; un métier retiré ne revient pas avec la nuit). Rien ne part chez Hektor.
//       Cran app_setting « partenaires_metier_modif », ET le droit de gérer les contacts (comme « Modifier la fiche »).
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import { METIERS_ORDONNES, origineDuMetier, planDesChangements, resumerMetiers, type LigneMetier } from './lib/metierPartenaire'
import './metier-partenaire.css'

export type EtatMetiers = { etat: 'eteint' | 'chargement' | 'pret' | 'erreur'; lignes: LigneMetier[]; recharger: () => void }

export function useMetiersPartenaire(contactId: string, actif: boolean): EtatMetiers {
  const [resultat, setResultat] = useState<Omit<EtatMetiers, 'recharger'>>({ etat: actif ? 'chargement' : 'eteint', lignes: [] })
  const [version, setVersion] = useState(0)
  useEffect(() => {
    if (!actif || !contactId.trim()) { setResultat({ etat: 'eteint', lignes: [] }); return }
    if (!hasSupabaseEnv || !supabase) { setResultat({ etat: 'erreur', lignes: [] }); return }
    let annule = false
    setResultat((avant) => ({ etat: avant.etat === 'pret' ? 'pret' : 'chargement', lignes: avant.lignes }))
    void supabase.from('app_partenaire_metier')
      .select('metier,source,ecrit_le,confirme_le')
      .eq('contact_id', contactId.trim())
      .is('retire_le', null)
      .then(({ data, error }) => {
        if (annule) return
        setResultat(error ? { etat: 'erreur', lignes: [] } : { etat: 'pret', lignes: (data ?? []) as LigneMetier[] })
      })
    return () => { annule = true }
  }, [contactId, actif, version])
  return { ...resultat, recharger: () => setVersion((v) => v + 1) }
}

// Chargement ou aucun métier : rien (la fiche ne bouge pas pour les contacts qui ne sont pas des partenaires).
// Erreur : dite, jamais tue (une lecture ratée n'est pas « aucun métier »). `onChanger` absent = pas de bouton.
export function BlocMetierPartenaire(props: { metiers: EtatMetiers; onChanger?: () => void }) {
  if (props.metiers.etat === 'erreur') {
    return (
      <div className="fa-cx-metier erreur" role="status">
        <div><div className="k">Métier</div><div className="s">Lecture du registre impossible pour le moment.</div></div>
      </div>
    )
  }
  if (props.metiers.etat !== 'pret') return null
  const resume = resumerMetiers(props.metiers.lignes)
  if (!resume) return null
  return (
    <div className="fa-cx-metier">
      <div><div className="k">Métier</div><div className="v">{resume.titre}</div><div className="s">{resume.origine}</div></div>
      {props.onChanger ? <button type="button" onClick={props.onChanger}>Changer</button> : null}
    </div>
  )
}

export function FenetreMetierPartenaire(props: { contactId: string; nom: string; lignes: LigneMetier[]; onClose: () => void; onEnregistre: () => void }) {
  const [retraits, setRetraits] = useState<Set<string>>(new Set())
  const [ajouts, setAjouts] = useState<Set<string>>(new Set())
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const actifs = props.lignes.map((l) => l.metier)
  const plan = planDesChangements(actifs, retraits, ajouts)
  const nbAjouts = plan.filter((c) => !c.retirer).length
  const nbRetraits = plan.length - nbAjouts
  const fermer = () => { if (!envoi) props.onClose() }

  useEffect(() => {
    const touche = (event: KeyboardEvent) => { if (event.key === 'Escape') fermer() }
    window.addEventListener('keydown', touche)
    return () => window.removeEventListener('keydown', touche)
  })

  const basculer = (ensemble: Set<string>, regler: (s: Set<string>) => void, metier: string) => {
    const suivant = new Set(ensemble)
    if (suivant.has(metier)) suivant.delete(metier); else suivant.add(metier)
    regler(suivant)
  }

  const enregistrer = async () => {
    if (!plan.length || envoi) return
    if (!hasSupabaseEnv || !supabase) { setErreur('Connexion à la base indisponible.'); return }
    setEnvoi(true)
    setErreur(null)
    let faits = 0
    try {
      for (const changement of plan) {
        const { error } = await supabase.rpc('app_partenaire_metier_ecrire', {
          p_contact: props.contactId, p_metier: changement.metier, p_retirer: changement.retirer,
        })
        if (error) throw new Error(error.message)
        faits += 1
      }
      props.onEnregistre()
      props.onClose()
    } catch (e) {
      // Ce qui est passé est gardé (chaque changement s'écrit à part) : on relit, et on dit où ça s'est arrêté.
      if (faits > 0) props.onEnregistre()
      setErreur(`${faits ? `${faits} changement(s) enregistré(s), puis ` : ''}échec : ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setEnvoi(false)
    }
  }

  const libelle = (metier: string) => METIERS_ORDONNES.find((m) => m.metier === metier)?.libelle ?? metier
  return createPortal(
    <div className="mtp-voile" onClick={(event) => { event.stopPropagation(); fermer() }}>
      <section className="mtp" role="dialog" aria-modal="true" aria-labelledby="mtp-titre" onClick={(event) => event.stopPropagation()}>
        <header className="mtp-tete">
          <span className="mtp-ic" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="7" width="18" height="13" rx="2.5" /><path d="M8.5 7V5.5A1.5 1.5 0 0 1 10 4h4a1.5 1.5 0 0 1 1.5 1.5V7" /><path d="M3 12.5h18" /></svg></span>
          <div className="mtp-titres">
            <div className="mtp-sur">Partenaire</div>
            <h2 className="mtp-titre" id="mtp-titre">Métier du contact</h2>
            <div className="mtp-qui">{props.nom} · contact {props.contactId}</div>
          </div>
          <button className="mtp-x" type="button" aria-label="Fermer" onClick={fermer}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round"><path d="M6 6l12 12M18 6 6 18" /></svg></button>
        </header>

        <div className="mtp-corps">
          <div>
            <div className="mtp-k">Ses métiers {props.lignes.length ? <span className="n">· {props.lignes.length}</span> : null}</div>
            {props.lignes.length ? (
              <div className="mtp-actuels">
                {props.lignes.map((ligne) => {
                  const retire = retraits.has(ligne.metier)
                  return (
                    <div className={`mtp-actuel${retire ? ' retire' : ''}`} key={ligne.metier}>
                      <span className="pt" aria-hidden="true" />
                      <div className="t">
                        <div className="nm">{libelle(ligne.metier)}</div>
                        <div className="or">{retire ? 'Sera retiré à l’enregistrement' : origineDuMetier(ligne).replace(/^./, (c) => c.toUpperCase())}</div>
                      </div>
                      <button type="button" disabled={envoi} onClick={() => basculer(retraits, setRetraits, ligne.metier)}>{retire ? 'Garder' : 'Retirer'}</button>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="mtp-vide">Aucun métier pour l’instant. Choisissez-en un ci-dessous pour en faire un <b>partenaire</b>.</div>
            )}
          </div>

          <div>
            <div className="mtp-k">Ajouter un métier</div>
            <div className="mtp-choix">
              {METIERS_ORDONNES.filter((m) => !actifs.includes(m.metier)).map((m) => {
                const on = ajouts.has(m.metier)
                return (
                  <button type="button" key={m.metier} className={`mtp-pill${m.premier ? ' prem' : ''}${on ? ' on' : ''}`} aria-pressed={on} disabled={envoi}
                    onClick={() => basculer(ajouts, setAjouts, m.metier)}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m5 12 5 5 9-10" /></svg>{m.libelle}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="mtp-note">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 7.6v.4" /></svg>
            <span>Le métier vit <b>chez nous</b> : rien n’est envoyé à Hektor. Un métier retiré ici ne revient pas avec la mise à jour de la nuit ; on le remet en l’ajoutant.</span>
          </div>
          {erreur ? <div className="mtp-erreur" role="alert">{erreur}</div> : null}
        </div>

        <footer className="mtp-pied">
          <div className="mtp-bilan" aria-live="polite">
            {plan.length === 0 ? 'Aucun changement' : (
              <>
                {nbAjouts ? <b className="aj">{nbAjouts} ajout{nbAjouts > 1 ? 's' : ''}</b> : null}
                {nbAjouts && nbRetraits ? ' · ' : null}
                {nbRetraits ? <b className="re">{nbRetraits} retrait{nbRetraits > 1 ? 's' : ''}</b> : null}
              </>
            )}
          </div>
          <button className="mtp-btn" type="button" onClick={fermer} disabled={envoi}>Annuler</button>
          <button className="mtp-btn go" type="button" onClick={() => void enregistrer()} disabled={envoi || plan.length === 0}>{envoi ? 'Enregistrement…' : 'Enregistrer'}</button>
        </footer>
      </section>
    </div>,
    document.body,
  )
}
