// Listing Annonces V2 -- lot 1 du plan notice/PLAN_DEV_LISTING_ANNONCES_LISTE_PUBLICITE_2026-11-03.md
// (maquette validee par Frederic le 03/11/2026, planche « Bureau 1280 px »).
//
// Interrupteur : VITE_APP_ANNONCES_LISTE_V2. Eteint (defaut), MandatsScreen garde son rendu
// d'avant A L'IDENTIQUE ; ce fichier n'est alors appele nulle part.
//
// ⚠ Ce composant ne calcule RIEN de metier qui n'existe pas deja : MandatsScreen lui passe les
//   valeurs que l'ecran calculait deja (type de bien, negociateur, statut, validation, compte
//   d'acquereurs) et les noeuds d'action (bouton Action, bouton des lignes legeres). Il ne fait
//   que les disposer comme l'annuaire Contacts. Aucune requete : tout est dans la ligne.
import type { ReactNode } from 'react'
import type { MandatRecord } from './types'
import { PastilleFicheMandat, useFicheMandat } from './FicheMandatManquante'
import './annonces-liste-v2.css'

// 03/11/2026 -- Frederic : « je ne veux pas de variable ». La V2 est donc la liste PAR DEFAUT
// (variable absente = allumee). L'ancien rendu reste dans MandatsScreen comme SECOURS : poser
// VITE_APP_ANNONCES_LISTE_V2=false (puis Redeploy) le fait revenir, sans toucher au code.
export const APP_ANNONCES_LISTE_V2 =
  !['false', '0', 'off', 'no'].includes(String(import.meta.env.VITE_APP_ANNONCES_LISTE_V2 ?? '').trim().toLowerCase())

// ── « Modifier » ouvre la fiche sur la rubrique « Le bien » (decision du 03/11) ──
// La fiche (CockpitDetail) se monte a chaque ouverture et choisit sa rubrique dans son useState
// initial : on depose la demande juste avant d'ouvrir, elle la prend une fois. Pas de nouvelle
// propriete a faire descendre a travers les trois couches de la fiche.
let rubriqueDemandee: string | null = null
export function demanderRubriqueAOuverture(rubrique: string) {
  rubriqueDemandee = rubrique
}
export function prendreRubriqueDemandee(): string | null {
  const rubrique = rubriqueDemandee
  rubriqueDemandee = null
  return rubrique
}

const MOIS_MS = 30.4 * 86400000

function jourLocal(value?: string | null): Date | null {
  const texte = String(value ?? '').trim().slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(texte) || texte.startsWith('0000')) return null
  const [a, m, j] = texte.split('-').map(Number)
  const date = new Date(a, m - 1, j)
  return Number.isFinite(date.getTime()) ? date : null
}

function dateCourte(date: Date) {
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

function euros(value: unknown) {
  const n = Number(value)
  return Number.isFinite(n) && value !== null && value !== '' ? `${new Intl.NumberFormat('fr-FR').format(n)} €` : null
}

export function nombrePhotos(item: MandatRecord): number {
  const app = item.images_preview_json_app
  if (Array.isArray(app)) return app.length
  if (typeof app === 'string') {
    try { const v = JSON.parse(app); if (Array.isArray(v)) return v.length } catch { /* forme inconnue : on retombe sur l'ancien champ */ }
  }
  try { const v = JSON.parse(item.images_preview_json ?? '[]'); return Array.isArray(v) ? v.length : 0 } catch { return 0 }
}

function initiales(nom: string) {
  return nom.split(/\s+/).filter(Boolean).map((mot) => mot.charAt(0)).join('').slice(0, 2).toUpperCase()
}

const ICONE = {
  photo: 'M4 8h3l2-3h6l2 3h3v11H4zM12 16.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4z',
  lieu: 'M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21zM12 12a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
  bouclier: 'M12 3l7 3v5c0 4.2-2.7 8-7 10-4.3-2-7-5.8-7-10V6z',
  antenne: 'M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7M5.6 5.6a9 9 0 0 0 0 12.8M18.4 5.6a9 9 0 0 1 0 12.8',
  maison: 'M3 11 12 4l9 7M5 10v10h14V10',
  coeur: 'M12 17.2s-3-1.8-3-3.7a1.6 1.6 0 0 1 3-.8 1.6 1.6 0 0 1 3 .8c0 1.9-3 3.7-3 3.7z',
  crayon: 'M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4',
  fleche: 'm9 6 6 6-6 6',
}

function Svg({ d, ...rest }: { d: string; strokeWidth?: number; fill?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill={rest.fill ?? 'none'} stroke="currentColor" strokeWidth={rest.strokeWidth ?? 1.9} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={d} />
    </svg>
  )
}

export function AnnonceV2Colgroup() {
  return (
    // ⚠ Mesure du 03/11 en 1280 px : le menu lateral LIBELLE de l'app laisse ~910 px a la liste (la
    //   maquette avait un rail d'icones). Le negociateur vit donc DANS la cellule Bien, et les largeurs
    //   comptent le padding des cellules (table-layout: fixed).
    <colgroup>
      <col />{/* bien (photo, titre, etiquettes, lieu, negociateur, numeros) -- flexible */}
      <col style={{ width: '118px' }} />{/* prix : prix, ancien barre, pastille d'ecart (03/11 : 106 debordait) */}
      <col style={{ width: '134px' }} />{/* mandat : bouclier + periode */}
      <col style={{ width: '78px' }} />{/* diffusion : un symbole de 34 px (78 : l'en-tete « DIFFUSION » doit tenir) */}
      <col style={{ width: '268px' }} />{/* actions : sceau 116 + 3 x 34 + 3 x 6 + padding 30 -- meme hauteur 34 px que les boutons Contacts */}
    </colgroup>
  )
}

export function AnnonceV2Head() {
  return (
    <tr>
      <th className="av3-l">Bien</th>
      <th>Prix</th>
      <th>Mandat</th>
      <th className="av3-c">Diffusion</th>
      <th className="av3-r">Actions</th>
    </tr>
  )
}

export function AnnonceV2Reperes() {
  return (
    <div className="av3-reperes">
      <b>Repères</b>
      <span><i style={{ background: '#2f7d59' }} />En ligne (le chiffre = nombre de portails)</span>
      <span><i style={{ background: '#fff8ec', border: '1.5px dashed #e8b05a' }} />Diffusable, sur aucun portail</span>
      <span><i style={{ background: '#f4f5f6', border: '1.5px solid #e2e5e6' }} />Pas diffusable (antenne barrée)</span>
      <span><i style={{ width: 9, height: 9, borderRadius: 9, background: '#b66a16' }} />Portail en erreur</span>
      <span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2f7d59" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={ICONE.bouclier} /></svg>Bouclier : mandat validé ou non</span>
      <span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#b5182f" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={ICONE.bouclier} /></svg>Rouge : numéro sans fiche mandat chez Hektor</span>
    </div>
  )
}

export type AnnonceV2CellsProps = {
  item: MandatRecord
  photoUrl: string | null
  typeLabel: string
  negoName: string | null
  /** pastille de transaction deja calculee par l'ecran (« Sous compromis », « Offre reçue », « Vendu », « En création »…), null si Actif */
  transactionLabel: string | null
  validated: boolean
  isLightweight: boolean
  /** bouton Action (MandatActionMenu variant pill) OU bouton des lignes legeres -- fourni par l'ecran */
  actionSlot: ReactNode
  showRappro: boolean
  rapproEligible: boolean
  rapproBadge: number
  rapproTotal: number
  onRappro: () => void
  canEdit: boolean
  onEdit: () => void
  onOpen: () => void
}

type BienPrixProps = Pick<AnnonceV2CellsProps, 'item' | 'photoUrl' | 'typeLabel' | 'negoName' | 'transactionLabel'>

// Les cellules Bien et Prix : les MEMES dans la vue Liste et la vue Publicite.
function BienPrixCells(p: BienPrixProps) {
  const { item } = p
  // Une vignette affichee compte au moins pour une photo (garde : listes sans `images_preview_json_app`).
  const nbPhotos = Math.max(nombrePhotos(item), p.photoUrl ? 1 : 0)
  const titreVide = !String(item.titre_bien ?? '').trim() || String(item.titre_bien).startsWith('[Sans titre]')
  const prix = euros(item.prix)
  const manques = [
    titreVide ? 'sans titre' : null,
    prix ? null : 'sans prix',
    nbPhotos < 5 ? `${nbPhotos} photo${nbPhotos > 1 ? 's' : ''}` : null,
    p.negoName ? null : 'sans négociateur',
  ].filter(Boolean) as string[]

  const ancien = euros(item.price_change_last_old_value)
  const variation = (() => {
    const a = Number(item.price_change_last_old_value)
    const n = Number(item.prix)
    if (!ancien || !Number.isFinite(a) || !Number.isFinite(n) || a === 0 || a === n) return null
    const pct = ((n - a) / a) * 100
    // 03/11 : « +1333,3 % » debordait sur la colonne Mandat. Une decimale sous 10 %, aucune au-dela,
    // separateur de milliers francais (« +1 333 % »).
    const abs = Math.abs(pct)
    const chiffre = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: abs < 10 ? 1 : 0 }).format(abs)
    return { texte: `${pct > 0 ? '+' : '−'}${chiffre} %`, baisse: pct < 0 }
  })()
  const changeLe = jourLocal(item.price_change_last_detected_at)
  const ilYa = changeLe ? Math.max(0, Math.round((Date.now() - changeLe.getTime()) / 86400000)) : null
  const aUnMandat = Boolean(String(item.numero_mandat ?? '').trim())
  const nego = p.negoName && p.negoName !== '-' ? p.negoName : null
  const agence = String(item.agence_nom ?? '').replace(/^Groupe GTI\s*/i, '').trim() || '—'

  return (
    <>
      <td className="av3-l">
        <div className="av3-bien">
          <div className="av3-photo">
            {p.photoUrl ? <img src={p.photoUrl} alt="" loading="lazy" /> : null}
            <span className="av3-nimg" title={`${nbPhotos} photo${nbPhotos > 1 ? 's' : ''}`}><Svg d={ICONE.photo} strokeWidth={2.4} />{nbPhotos}</span>
          </div>
          <div className="av3-txt">
            <span className="av3-titre" title={`${item.titre_bien ?? ''}${item.hektor_annonce_id ? ` — annonce ${item.hektor_annonce_id}` : ''}`}>{item.titre_bien}</span>
            <span className="av3-tags">
              <span className="av3-ids">{aUnMandat ? `N° ${item.numero_mandat}` : 'Sans mandat'}</span>
              <span className="av3-tag">{p.typeLabel}</span>
              {item.mandat_type ? <span className={`av3-tag${/exclu/i.test(item.mandat_type) ? ' excl' : ''}`}>{item.mandat_type.charAt(0) + item.mandat_type.slice(1).toLowerCase()}</span> : null}
              {p.transactionLabel ? <span className="av3-tag transac">{p.transactionLabel}</span> : null}
              {manques.length ? <span className="av3-tag manque" title={`À compléter : ${manques.join(', ')}`}>À compléter{manques.length === 1 ? ` · ${manques[0]}` : ` · ${manques.length}`}</span> : null}
            </span>
            <span className="av3-ligne">
              {item.ville ? <span className="av3-lieu"><Svg d={ICONE.lieu} strokeWidth={2.2} />{item.ville}{item.code_postal ? <span>{item.code_postal}</span> : null}</span> : null}
              <span className="av3-nego" title={nego ? `${nego} · ${agence}` : 'Non affecté'}>
                <span className={`av3-ini${nego ? '' : ' vide'}`} aria-hidden="true">{nego ? initiales(nego) : '—'}</span>
                <span className={`av3-nego-nom${nego ? '' : ' vide'}`}>{nego ?? 'Non affecté'}</span>
                <span className="av3-nego-ag">· {agence}</span>
              </span>
            </span>
          </div>
        </div>
      </td>
      <td>
        <div className={`av3-prix${prix ? '' : ' vide'}`}>{prix ?? 'Prix à saisir'}</div>
        {ancien && variation ? (
          <>
            <div className="av3-avant" title={`Ancien prix : ${ancien}`}><s>{ancien}</s></div>
            <div className="av3-ecart">
              <b className={variation.baisse ? 'baisse' : 'hausse'} title={variation.baisse ? 'Baisse de prix' : 'Hausse de prix'}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={variation.baisse ? 'M12 5v14M6 13l6 6 6-6' : 'M12 19V5M6 11l6-6 6 6'} /></svg>
                {variation.texte}
              </b>
              {ilYa != null ? <span className="av3-quand">{ilYa} j</span> : null}
            </div>
          </>
        ) : null}
      </td>
    </>
  )
}

export function AnnonceV2Cells(p: AnnonceV2CellsProps) {
  const { item } = p
  const aUnMandat = Boolean(String(item.numero_mandat ?? '').trim())
  const bouclier = !aUnMandat
    ? { cls: 'sans', label: 'Sans mandat', marque: 'M9 12h6', titre: 'Pas encore de numéro de mandat' }
    : p.validated
      ? { cls: 'ok', label: 'Validé', marque: 'm9 12 2 2 4-4', titre: 'Mandat validé par la Direction' }
      : { cls: 'attente', label: 'Non validé', marque: 'M12 9v3M12 15h.01', titre: 'Mandat pas encore validé par la Direction' }
  // Un numero sans fiche chez Hektor (03/11) : la pastille rouge REMPLACE le bouclier, qui disait « Validé ».
  const ficheMandat = useFicheMandat(item)

  const debut = jourLocal(item.mandat_date_debut)
  const fin = jourLocal(item.mandat_date_fin)
  const periode = (() => {
    if (!debut || !fin || fin <= debut) return null
    const maintenant = Date.now()
    const pct = Math.max(0, Math.min(100, Math.round(((maintenant - debut.getTime()) / (fin.getTime() - debut.getTime())) * 100)))
    const reste = Math.ceil((fin.getTime() - maintenant) / 86400000)
    const etat = reste < 0 ? 'echu' : reste <= 30 ? 'bientot' : ''
    const texte = reste < 0 ? `Échu depuis ${-reste} j` : reste <= 30 ? `Reste ${reste} j` : `Reste ${Math.round((fin.getTime() - maintenant) / MOIS_MS)} mois`
    return { debut: dateCourte(debut), fin: dateCourte(fin), pct, etat, texte }
  })()

  const portails = Number(item.nb_portails_actifs ?? 0) || 0
  const diffusable = String(item.diffusable ?? '').trim() === '1'
  const enErreur = Boolean(item.has_diffusion_error)
  const antenne = !diffusable ? 'non' : portails > 0 ? 'enligne' : 'zero'
  const antenneTitre = `${!diffusable ? 'Pas diffusable' : portails > 0 ? `En ligne sur ${portails} portail${portails > 1 ? 's' : ''}` : 'Diffusable, sur aucun portail'}${enErreur ? ' · un portail en erreur' : ''}`

  return (
    <>
      <BienPrixCells item={item} photoUrl={p.photoUrl} typeLabel={p.typeLabel} negoName={p.negoName} transactionLabel={p.transactionLabel} />
      <td>
        <div className="av3-mandat">
          {ficheMandat ? <PastilleFicheMandat etat={ficheMandat} /> : (
            <span className={`av3-bouclier ${bouclier.cls}`} title={bouclier.titre}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={ICONE.bouclier} /><path d={bouclier.marque} /></svg>
              {bouclier.label}
            </span>
          )}
          {periode ? (
            <>
              <span className="av3-dates"><span>{periode.debut}</span><span>{periode.fin}</span></span>
              <span className={`av3-barre ${periode.etat}`} aria-hidden="true"><i style={{ width: `${periode.pct}%` }} /></span>
              <span className={`av3-reste ${periode.etat}`}>{periode.texte}</span>
            </>
          ) : null}
        </div>
      </td>
      <td>
        <div className="av3-dif">
          <span className={`av3-antenne ${antenne}`} title={antenneTitre} aria-label={antenneTitre} role="img">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" aria-hidden="true">
              <path d={ICONE.antenne} />
              {antenne === 'non' ? <path d="M4 4l16 16" strokeWidth={2.4} /> : null}
            </svg>
            {antenne === 'enligne' ? <span className="nb">{portails}</span> : null}
            {enErreur ? <span className="err" /> : null}
          </span>
        </div>
      </td>
      <td className="av3-r">
        <div className="av3-actions" onClick={(event) => event.stopPropagation()}>
          {/* `row-actions` : la fenetre « Actions disponibles » et le bouton des lignes legeres ne sont
              mis en page QUE sous ce conteneur (styles.css ~3863). `display: contents` : il ne prend
              aucune place dans la grille. */}
          <span className="row-actions av3-slot">{p.actionSlot}</span>
          {p.showRappro && p.rapproEligible ? (
            <button type="button" className="ra rappro" title={`${p.rapproBadge || p.rapproTotal || 0} acquéreur(s) correspondant(s)${p.rapproBadge ? ' · non proposés' : ''}`} aria-label="Rapprochement acquéreurs" onClick={(event) => { event.stopPropagation(); p.onRappro() }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={ICONE.maison} /><path d={ICONE.coeur} fill="currentColor" stroke="none" /></svg>
              {p.rapproBadge > 0 ? <span className="ra-badge">{p.rapproBadge > 99 ? '99+' : p.rapproBadge}</span> : null}
            </button>
          ) : <span className="ra-spacer" aria-hidden="true" />}
          {p.canEdit ? (
            <button type="button" className="ra" title="Modifier l'annonce (rubrique « Le bien »)" aria-label="Modifier l'annonce" onClick={(event) => { event.stopPropagation(); p.onEdit() }}>
              <Svg d={ICONE.crayon} />
            </button>
          ) : <span className="ra-spacer" aria-hidden="true" />}
          <button type="button" className="ra cta" title="Ouvrir la fiche" aria-label="Ouvrir la fiche" onClick={(event) => { event.stopPropagation(); p.onOpen() }}>
            <Svg d={ICONE.fleche} strokeWidth={2.4} />
          </button>
        </div>
      </td>
    </>
  )
}

// ── Vue Publicite (lot 3, 03/11/2026 -- maquette V8 validee) ─────────────────────────────────────
// Au-dessus : 6 cartes « Presence sur les portails » (site GTI + 5 portails), cliquables en filtre
// « diffusables absentes de X ». Dans la liste : une case par portail quand l'annonce est diffusable,
// sinon une bande « Faire la demande ». Une seule action par ligne : la fleche « Ouvrir » (V8).
// L'etat « en ligne » vient de `portails_resume` (deja dans la ligne) ; l'envoi chez Hektor est fait
// par l'ecran (MandatsScreen), ce composant ne fait que dessiner.
export const PORTAILS_PUB = [
  { key: 'leboncoinDirect', court: 'LB', nom: 'Leboncoin', libelle: 'Leboncoin', teinte: '#A5793D' },
  { key: 'bienicidirect', court: 'BI', nom: "Bien'ici", libelle: "Bien'ici", teinte: '#C5005F' },
  { key: 'paper', court: 'PA', nom: 'Paper', libelle: 'Paper', teinte: '#1F7A4A' },
  { key: 'etreproprio', court: 'EP', nom: 'Etreproprio', libelle: 'Etrepro.', teinte: '#3A4A95' },
  { key: 'superimmo', court: 'SI', nom: 'Superimmo', libelle: 'Superimmo', teinte: '#0F6874' },
] as const

// Numeros de passerelle chez Hektor COMMUNS a toutes les agences (mesures le 03/11 dans
// hektor_broadcast). Bien'ici et Leboncoin dependent de l'agence : app_diffusion_agency_target.
export const PORTAIL_ID_COMMUN: Record<string, string> = { etreproprio: '19', paper: '20', superimmo: '21' }

export function portailsDeLaLigne(resume: string | null | undefined): string[] {
  return Array.from(new Set(String(resume ?? '').split(',').map((cle) => cle.trim()).filter(Boolean)))
}

export type EtatCase = 'enligne' | 'absent' | 'erreur' | 'envoi' | 'retrait' | 'echec'

export function AnnonceOnglets(p: { vue: 'liste' | 'pub'; onChange: (vue: 'liste' | 'pub') => void }) {
  return (
    <div className="av3-onglets" role="tablist" aria-label="Vue du listing">
      <button type="button" role="tab" aria-selected={p.vue === 'liste'} className={p.vue === 'liste' ? 'on' : ''} onClick={() => p.onChange('liste')}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" aria-hidden="true"><path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" /></svg>
        Liste
      </button>
      <button type="button" role="tab" aria-selected={p.vue === 'pub'} className={p.vue === 'pub' ? 'on' : ''} onClick={() => p.onChange('pub')}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" aria-hidden="true"><path d={ICONE.antenne} /></svg>
        Publicité
      </button>
    </div>
  )
}

const nombreFr = (n: number) => new Intl.NumberFormat('fr-FR').format(n)

/** Les 6 cartes : `actif` = la carte qui filtre ('gti', une cle de portail, ou null). */
export function AnnoncePresence(p: {
  presence: { diffusables: number; nonDiffusables: number; enLigne: Record<string, number> } | null
  chargement: boolean
  actif: string | null
  onPick: (cle: string | null) => void
}) {
  const base = p.presence?.diffusables ?? 0
  const cartes = [
    { cle: 'gti', court: 'GTI', nom: 'Site GTI', teinte: '#222323', valeur: base, unite: 'diffusables', pct: base ? 100 : 0, pied: 'Suit « Diffusable »', titre: `Absentes du site GTI : ${nombreFr(p.presence?.nonDiffusables ?? 0)} annonces pas encore diffusables` },
    ...PORTAILS_PUB.map((portail) => {
      const on = p.presence?.enLigne[portail.key] ?? 0
      const abs = Math.max(0, base - on)
      return { cle: portail.key, court: portail.court, nom: portail.nom, teinte: portail.teinte, valeur: on, unite: `/ ${nombreFr(base)}`, pct: base ? (on / base) * 100 : 0, pied: `${nombreFr(abs)} absente${abs > 1 ? 's' : ''}`, titre: `Voir les ${nombreFr(abs)} annonces diffusables absentes de ${portail.nom}` }
    }),
  ]
  return (
    <section className={`av3-presence${p.chargement ? ' charge' : ''}`} aria-label="Présence sur les portails">
      {cartes.map((carte) => {
        const actif = p.actif === carte.cle
        return (
          <button key={carte.cle} type="button" className={`av3-carte${actif ? ' on' : ''}`} aria-pressed={actif} title={carte.titre} onClick={() => p.onPick(actif ? null : carte.cle)}>
            <span className="av3-carte-tete"><span className="av3-pastille" style={{ background: carte.teinte }} aria-hidden="true">{carte.court}</span>{carte.nom}</span>
            <span className="av3-carte-val"><b>{p.presence ? nombreFr(carte.valeur) : '…'}</b><span>{carte.unite}</span></span>
            <span className="av3-carte-barre" aria-hidden="true"><i style={{ width: `${carte.pct.toFixed(1)}%`, background: carte.teinte }} /></span>
            <span className="av3-carte-pied">{carte.pied}</span>
          </button>
        )
      })}
    </section>
  )
}

/** La barre noire du filtre de carte, comme la maquette. */
export function AnnonceFiltrePresence(p: { actif: string | null; presence: { diffusables: number; nonDiffusables: number; enLigne: Record<string, number> } | null; onClear: () => void }) {
  if (!p.actif) return null
  const portail = PORTAILS_PUB.find((x) => x.key === p.actif)
  const texte = portail
    ? `Diffusables absentes de ${portail.nom}${p.presence ? ` · ${nombreFr(Math.max(0, p.presence.diffusables - (p.presence.enLigne[portail.key] ?? 0)))}` : ''}`
    : `Absentes du site GTI : pas encore diffusables${p.presence ? ` · ${nombreFr(p.presence.nonDiffusables)}` : ''}`
  return (
    <div className="av3-filtre" role="status">
      <span>{texte}</span>
      <button type="button" onClick={p.onClear}>Retirer le filtre</button>
    </div>
  )
}

export function AnnoncePubColgroup() {
  return (
    <colgroup>
      <col />{/* bien -- flexible */}
      <col style={{ width: '128px' }} />{/* prix + signaux */}
      {PORTAILS_PUB.map((portail) => <col key={portail.key} style={{ width: '64px' }} />)}
      <col style={{ width: '70px' }} />{/* ouvrir */}
    </colgroup>
  )
}

export function AnnoncePubHead() {
  return (
    <tr>
      <th className="av3-l">Bien</th>
      <th>Prix</th>
      {PORTAILS_PUB.map((portail) => (
        <th key={portail.key} className="av3-c av3-th-portail" title={portail.nom}>
          <span className="av3-th-p">
            <span className="av3-pastille" style={{ background: portail.teinte }} aria-hidden="true">{portail.court}</span>
            <span className="av3-th-nom">{portail.libelle}</span>
          </span>
        </th>
      ))}
      <th className="av3-r"><span className="av3-sr">Ouvrir</span></th>
    </tr>
  )
}

export function AnnoncePubReperes() {
  return (
    <div className="av3-reperes">
      <b>Repères</b>
      <span><i style={{ background: '#2f7d59' }} />En ligne : décocher pour retirer</span>
      <span><i style={{ background: '#fff', border: '2px solid #cfd3d4' }} />Absente : cocher pour publier</span>
      <span><i style={{ background: '#fff3df', border: '2px solid #b66a16' }} />Erreur : cocher pour relancer</span>
      <span>La case ne change qu'après la réponse de Hektor</span>
    </div>
  )
}

export type AnnoncePubCellsProps = BienPrixProps & {
  /** null = annonce diffusable (les cases) ; sinon le texte de la bande, et son bouton s'il y en a un */
  bande: null | { texte: string; bouton?: { label: string; onClick: () => void; attente?: boolean } }
  cases: Record<string, { etat: EtatCase; titre: string }>
  onToggle: (portalKey: string) => void
  onOpen: () => void
}

export function AnnoncePubCells(p: AnnoncePubCellsProps) {
  const { item } = p
  const nbPhotos = Math.max(nombrePhotos(item), p.photoUrl ? 1 : 0)
  const prix = euros(item.prix)
  const aUnMandat = Boolean(String(item.numero_mandat ?? '').trim())
  const meta = [p.typeLabel, aUnMandat ? `N° ${item.numero_mandat}` : 'Sans mandat', item.ville].filter(Boolean).join(' · ')
  // Les signaux de la maquette, sous le prix : ce qu'un negociateur doit voir pour sa pub.
  const nEnLigne = Object.values(p.cases).filter((c) => c.etat === 'enligne' || c.etat === 'retrait').length
  const fin = jourLocal(item.mandat_date_fin)
  const signaux: Array<{ t: string; cls: string }> = []
  if (aUnMandat && fin && fin.getTime() < Date.now()) signaux.push({ t: 'Mandat échu', cls: 'echu' })
  if (p.transactionLabel && p.transactionLabel !== 'Brouillon' && nEnLigne > 0) signaux.push({ t: `Encore en ligne · ${p.transactionLabel.toLowerCase()}`, cls: 'transac' })
  if (!p.bande && nEnLigne === 0 && !p.transactionLabel) signaux.push({ t: 'Visible nulle part', cls: 'nulle' })
  return (
    <>
      <td className="av3-l">
        <div className="av3-bien av3-pub-bien">
          <div className="av3-photo">
            {p.photoUrl ? <img src={p.photoUrl} alt="" loading="lazy" /> : null}
            <span className="av3-nimg" title={`${nbPhotos} photo${nbPhotos > 1 ? 's' : ''}`}><Svg d={ICONE.photo} strokeWidth={2.4} />{nbPhotos}</span>
          </div>
          <div className="av3-txt">
            <span className="av3-titre" title={`${item.titre_bien ?? ''}${item.hektor_annonce_id ? ` — annonce ${item.hektor_annonce_id}` : ''}`}>{item.titre_bien}</span>
            <span className="av3-pub-meta">{meta}</span>
            {p.transactionLabel ? <span className="av3-tags"><span className="av3-tag transac">{p.transactionLabel}</span></span> : null}
          </div>
        </div>
      </td>
      <td>
        <div className={`av3-prix${prix ? '' : ' vide'}`}>{prix ?? 'Prix à saisir'}</div>
        {signaux.map((s) => <div key={s.t} className={`av3-signal ${s.cls}`}>{s.t}</div>)}
      </td>
      {p.bande ? (
        <td colSpan={PORTAILS_PUB.length} className="av3-pub-bande-td">
          <div className="av3-pub-bande" onClick={(event) => event.stopPropagation()}>
            <span>{p.bande.texte}</span>
            {p.bande.bouton ? (
              <button type="button" className={`av3-pub-demande${p.bande.bouton.attente ? ' attente' : ''}`} disabled={p.bande.bouton.attente} onClick={(event) => { event.stopPropagation(); if (!p.bande?.bouton?.attente) p.bande?.bouton?.onClick() }}>
                {p.bande.bouton.label}
              </button>
            ) : null}
          </div>
        </td>
      ) : PORTAILS_PUB.map((portail) => {
        const kase = p.cases[portail.key] ?? { etat: 'absent' as EtatCase, titre: portail.nom }
        const occupe = kase.etat === 'envoi' || kase.etat === 'retrait'
        return (
          <td key={portail.key} className="av3-c">
            <button
              type="button"
              role="checkbox"
              aria-checked={kase.etat === 'enligne' || kase.etat === 'retrait'}
              aria-label={kase.titre}
              title={kase.titre}
              className={`av3-case ${kase.etat}`}
              disabled={occupe}
              onClick={(event) => { event.stopPropagation(); if (!occupe) p.onToggle(portail.key) }}
            >
              {kase.etat === 'enligne' ? <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7" /></svg> : null}
              {kase.etat === 'erreur' ? <b aria-hidden="true">!</b> : null}
              {kase.etat === 'echec' ? <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" aria-hidden="true"><path d="M7 7l10 10M17 7 7 17" /></svg> : null}
              {occupe ? <i className="av3-case-roue" aria-hidden="true" /> : null}
            </button>
          </td>
        )
      })}
      <td className="av3-r">
        <div className="av3-actions av3-pub-ouvrir" onClick={(event) => event.stopPropagation()}>
          <button type="button" className="ra cta" title="Ouvrir la fiche" aria-label="Ouvrir la fiche" onClick={(event) => { event.stopPropagation(); p.onOpen() }}>
            <Svg d={ICONE.fleche} strokeWidth={2.4} />
          </button>
        </div>
      </td>
    </>
  )
}
