// CHANTIER PARTENAIRES · LOT 3, PIÈCE 3.1 (05/11/2026) — LE BLOC « MÉTIER » DU VOLET GAUCHE DE LA FICHE CONTACT.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §24 ; maquette maquettes/fiche-partenaire-v1.html.
// LECTURE SEULE du registre `app_partenaire_metier` (lisible par tout compte actif), les lignes actives du contact, par
// NOTRE numéro. Rien n'est écrit (« Changer le métier » = pièce 3.2).
// Interrupteur : app_setting « partenaires_ecran » (admin = les admins seuls, on = tout le monde, absent = rien), lu dans
// App.tsx avec le même crochet que les couples. Éteint : ni lecture ni bloc.
import { useEffect, useState } from 'react'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import { resumerMetiers, type LigneMetier } from './lib/metierPartenaire'

export type EtatMetiers = { etat: 'eteint' | 'chargement' | 'pret' | 'erreur'; lignes: LigneMetier[] }

export function useMetiersPartenaire(contactId: string, actif: boolean): EtatMetiers {
  const [resultat, setResultat] = useState<EtatMetiers>({ etat: actif ? 'chargement' : 'eteint', lignes: [] })
  useEffect(() => {
    if (!actif || !contactId.trim()) { setResultat({ etat: 'eteint', lignes: [] }); return }
    if (!hasSupabaseEnv || !supabase) { setResultat({ etat: 'erreur', lignes: [] }); return }
    let annule = false
    setResultat({ etat: 'chargement', lignes: [] })
    void supabase.from('app_partenaire_metier')
      .select('metier,source,ecrit_le,confirme_le')
      .eq('contact_id', contactId.trim())
      .is('retire_le', null)
      .then(({ data, error }) => {
        if (annule) return
        setResultat(error ? { etat: 'erreur', lignes: [] } : { etat: 'pret', lignes: (data ?? []) as LigneMetier[] })
      })
    return () => { annule = true }
  }, [contactId, actif])
  return resultat
}

// Chargement ou aucun métier : rien (la fiche ne bouge pas pour les contacts qui ne sont pas des partenaires).
// Erreur : dite, jamais tue (une lecture ratée n'est pas « aucun métier »).
export function BlocMetierPartenaire(props: { metiers: EtatMetiers }) {
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
    </div>
  )
}
