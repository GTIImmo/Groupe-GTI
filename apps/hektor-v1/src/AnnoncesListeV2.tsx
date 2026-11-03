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
import './annonces-liste-v2.css'

export const APP_ANNONCES_LISTE_V2 =
  ['true', '1', 'on', 'yes'].includes(String(import.meta.env.VITE_APP_ANNONCES_LISTE_V2 ?? '').trim().toLowerCase())

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
      <col style={{ width: '106px' }} />{/* prix */}
      <col style={{ width: '146px' }} />{/* mandat : bouclier + periode */}
      <col style={{ width: '78px' }} />{/* diffusion : un symbole (78 : l'en-tete « DIFFUSION » doit tenir) */}
      <col style={{ width: '288px' }} />{/* actions : pilule 136 + 3 x 34 + 3 x 6 + padding 30 (Inter est plus large que la police de la maquette) */}
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

export function AnnonceV2Cells(p: AnnonceV2CellsProps) {
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
    return { texte: `${pct > 0 ? '+' : '−'}${Math.abs(pct).toFixed(1).replace('.', ',')} %`, baisse: pct < 0 }
  })()
  const changeLe = jourLocal(item.price_change_last_detected_at)
  const ilYa = changeLe ? Math.max(0, Math.round((Date.now() - changeLe.getTime()) / 86400000)) : null

  const aUnMandat = Boolean(String(item.numero_mandat ?? '').trim())
  const bouclier = !aUnMandat
    ? { cls: 'sans', label: 'Sans mandat', marque: 'M9 12h6', titre: 'Pas encore de numéro de mandat' }
    : p.validated
      ? { cls: 'ok', label: 'Validé', marque: 'm9 12 2 2 4-4', titre: 'Mandat validé par la Direction' }
      : { cls: 'attente', label: 'Non validé', marque: 'M12 9v3M12 15h.01', titre: 'Mandat pas encore validé par la Direction' }

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
            <div className="av3-avant"><s>{ancien}</s> <b className={variation.baisse ? 'baisse' : ''}>{variation.texte}</b></div>
            {ilYa != null ? <div className="av3-quand">il y a {ilYa} j</div> : null}
          </>
        ) : null}
      </td>
      <td>
        <div className="av3-mandat">
          <span className={`av3-bouclier ${bouclier.cls}`} title={bouclier.titre}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={ICONE.bouclier} /><path d={bouclier.marque} /></svg>
            {bouclier.label}
          </span>
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
