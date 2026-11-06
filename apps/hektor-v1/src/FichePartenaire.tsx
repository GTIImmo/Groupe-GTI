// CHANTIER PARTENAIRES · LOT 3, PIÈCE 3.3b (05/11/2026) — LA PARTIE DROITE DE LA FICHE PARTENAIRE.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §26 ; maquette maquettes/fiche-partenaire-v1.html.
// Quatre chiffres, la section du métier (ses étapes), « À venir » et les deux blocs « avec nous ». Les données n'existent pas
// encore : chaque bloc est MONTRÉ et marqué « en construction » avec son lot (décision du 27/10, comme la fiche notaire).
// Aucune lecture, aucune écriture. Les classes sont celles de la fiche notaire (fiche-notaire-v2.css).
import { useEffect, useState, type CSSProperties } from 'react'
import { EnConstruction, NotaireInterlocuteurs, type Interlocuteur } from './FicheNotaire'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import type { BlocsPartenaire, FamillePartenaire } from './lib/metierPartenaire'

const COULEURS_CHIFFRES = ['var(--ty)', '#c2512a', '#1f5b96', '#2f8a5b']

export function PartenaireChiffres(props: { blocs: BlocsPartenaire }) {
  return (
    <div className="fa-cx-kpis">
      {props.blocs.chiffres.map(([titre, sous], i) => (
        <div className="fa-cx-kpi" key={titre} style={{ ['--sc']: COULEURS_CHIFFRES[i % 4] } as CSSProperties}>
          <div className="fa-cx-kpi-k">{titre}</div>
          <div className="fa-cx-kpi-v" aria-label="pas encore de données">—</div>
          <div className="fa-cx-kpi-s">{sous}</div>
        </div>
      ))}
    </div>
  )
}

export function PartenaireSectionMetier(props: { blocs: BlocsPartenaire }) {
  const s = props.blocs.section
  return (
    <>
      <div className="fa-cx-sec" style={{ ['--sc']: 'var(--ty)' } as CSSProperties}>
        <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="7" width="18" height="13" rx="2.5" /><path d="M8.5 7V5.5A1.5 1.5 0 0 1 10 4h4a1.5 1.5 0 0 1 1.5 1.5V7" /><path d="M3 12.5h18" /></svg></span>
        {s.titre}
        <EnConstruction titre={props.blocs.lot} />
        <span className="fa-cx-sec-ln" />
      </div>
      <section className="fa-cx-mod full" style={{ marginBottom: 24 }}>
        <div className="fa-cx-stages">
          {s.etapes.map((etape) => (
            <div key={etape} className="fa-cx-stage wip"><b>—</b><span>{etape}</span></div>
          ))}
        </div>
        <div className="fa-cx-ech-empty">{s.texte}</div>
      </section>
    </>
  )
}

export function PartenaireAVenir(props: { blocs: BlocsPartenaire }) {
  return (
    <>
      <div className="fa-cx-sec" style={{ ['--sc']: '#c2512a' } as CSSProperties}>
        <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}><circle cx="12" cy="13" r="8" /><path d="M12 9v4l2.5 1.5M9 2h6" /></svg></span>
        À venir
        <EnConstruction />
        <span className="fa-cx-sec-ln" />
      </div>
      <section className="fa-cx-mod full" style={{ marginBottom: 24 }}>
        <div className="fa-cx-ech-empty">{props.blocs.aVenir}</div>
      </section>
    </>
  )
}

export function PartenaireAvecNous(props: { blocs: BlocsPartenaire }) {
  return (
    <div className="fa-cx-duo">
      {props.blocs.avecNous.map(([titre, texte], i) => (
        <div key={titre}>
          <div className="fa-cx-sec" style={{ ['--sc']: i === 0 ? 'var(--ty)' : '#a8814a' } as CSSProperties}>
            <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M4 19V9M10 19V5M16 19v-7M22 19H2" /></svg></span>
            {titre}
            <EnConstruction />
            <span className="fa-cx-sec-ln" />
          </div>
          <section className="fa-cx-mod full"><div className="fa-cx-ech-empty">{texte}</div></section>
        </div>
      ))}
    </div>
  )
}

// PIÈCE 3.4 (06/11/2026) — LES INTERLOCUTEURS D'UN PARTENAIRE (maquette fiche-partenaire-v1, volet gauche). Le même carnet que
// le notaire, sur la même table, renommée app_partenaire_interlocuteur (décision « A et on change le nom », patch du 06/11).
// Lecture : la table (comptes actifs, RLS) ; écriture : le carnet du notaire (relais). Une lecture ratée est DITE.
const EXEMPLES: Record<Exclude<FamillePartenaire, 'autre'>, { vide: string; role: string }> = {
  syndic: { vide: 'Aucun interlocuteur enregistré : gestionnaires de copropriété, comptables, assistants.', role: 'Rôle : gestionnaire, comptable…' },
  diag: { vide: 'Aucun interlocuteur enregistré : techniciens certifiés, planning, secrétariat.', role: 'Rôle : technicien, planning…' },
  courtier: { vide: 'Aucun interlocuteur enregistré : courtiers, conseillers bancaires, assistants.', role: 'Rôle : courtier, conseiller, assistant…' },
  apporteur: { vide: 'Aucun interlocuteur enregistré : les personnes de son réseau à contacter.', role: 'Rôle : associé, assistant…' },
}

export function PartenaireInterlocuteurs(props: { contactId: string; famille: Exclude<FamillePartenaire, 'autre'> }) {
  const [etat, setEtat] = useState<{ lignes: Interlocuteur[] | null; erreur: string | null }>({ lignes: null, erreur: null })
  const [version, setVersion] = useState(0)
  useEffect(() => {
    if (!hasSupabaseEnv || !supabase || !props.contactId.trim()) return
    let annule = false
    void supabase.from('app_partenaire_interlocuteur').select('id,nom,role,telephone,email')
      .eq('contact_id', props.contactId.trim()).is('retire_le', null).order('nom').order('id')
      .then(({ data, error }) => {
        if (annule) return
        setEtat(error ? { lignes: null, erreur: error.message } : { lignes: (data ?? []) as Interlocuteur[], erreur: null })
      })
    return () => { annule = true }
  }, [props.contactId, version])
  if (etat.erreur) {
    return (
      <div className="fa-cx-team">
        <div className="fa-cx-team-head">Interlocuteurs</div>
        <div className="fa-cx-ech-empty fa-cx-err">Interlocuteurs illisibles pour le moment ({etat.erreur}).</div>
      </div>
    )
  }
  const ex = EXEMPLES[props.famille]
  return <NotaireInterlocuteurs notaireId={props.contactId} interlocuteurs={etat.lignes} onChange={() => setVersion((v) => v + 1)}
    titre="Interlocuteurs" vide={ex.vide} exempleRole={ex.role} />
}
