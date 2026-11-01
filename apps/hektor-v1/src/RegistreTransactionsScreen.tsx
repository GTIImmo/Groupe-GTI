import { useEffect, useMemo, useState } from 'react'
import { loadRegistreDossiers, loadRepartitionsDesChaines, type RegistreDossierRow, type RegistreEtape, type RepartitionLigne } from './lib/api'
import './registre-transactions.css'

// Registre des transactions -- étape « écran liste » (01/11/2026), derrière l'interrupteur
// `registre_transactions_ecran`. Une ligne = un DOSSIER (offre -> compromis -> vente).
// Lecture seule : la fiche et ses gestes sont l'étape suivante ; un clic ouvre la fiche du bien.
// Maquette : https://claude.ai/artifact/3FA3yDqWuDWuqLdZAkvS8x · note : notice/AUDIT_GESTES_REGISTRE_TRANSACTIONS_2026-10-30.md § 8.
// ⛔ Aucun mot « Hektor » à l'écran (décision du 30/10) ; une lecture ratée se dit, sans détail technique.

type RegistreTransactionsScreenProps = {
  isAdmin: boolean
  onOpenDossier?: (appDossierId: number) => void
  libelleTypeBien?: (code: string | null | undefined) => string
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

export default function RegistreTransactionsScreen({ isAdmin, onOpenDossier, libelleTypeBien }: RegistreTransactionsScreenProps) {
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

  const ouvrir = (ligne: RegistreDossierRow) => {
    if (onOpenDossier && ligne.app_dossier_id != null) onOpenDossier(ligne.app_dossier_id)
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
                    const ouvrable = Boolean(onOpenDossier && ligne.app_dossier_id != null)
                    const type = typeEnClair(ligne.type_bien)
                    return (
                      <tr key={ligne.app_chaine_id} className={ouvrable ? 'is-ouvrable' : undefined} onClick={ouvrable ? () => ouvrir(ligne) : undefined}>
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
                              {ouvrable ? (
                                <button type="button" className="rt-lien" onClick={(event) => { event.stopPropagation(); ouvrir(ligne) }}>
                                  {ligne.ville || 'Ville inconnue'}
                                </button>
                              ) : (
                                <b>{ligne.ville || 'Ville inconnue'}</b>
                              )}
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
                const ouvrable = Boolean(onOpenDossier && ligne.app_dossier_id != null)
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
                    {ouvrable ? (
                      <button type="button" className="rt-carte-dossier" onClick={() => ouvrir(ligne)}>{contenu}</button>
                    ) : (
                      <div className="rt-carte-dossier">{contenu}</div>
                    )}
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
