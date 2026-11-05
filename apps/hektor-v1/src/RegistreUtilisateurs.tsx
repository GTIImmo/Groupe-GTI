// REGISTRE DES UTILISATEURS ET DES AGENCES -- étape 3, lot A (05/11/2026). Préfixe ru-.
// La maquette validée par Frédéric (§38) : https://claude.ai/artifact/XMLpyh5kDkfpXPwGTB5738 -- orientée APP, la synchro
// avec Hektor en bas, en gris. Décision du 05/11 : le bouton « Utilisateurs » existant ouvre cet écran, ADMINISTRATEURS
// SEULS, et « Ajouter » / « Modifier son accès » / « lien de mot de passe » rappellent les gestes qui marchaient déjà
// (App.tsx : handleCreateAppUser, handleUpdateAppUser, handleSendPasswordReset).
// ⭐ LOT C (05/11, §43) : la SAISIE AU CARNET -- « Modifier » sur une personne, une agence, la société ; le statut
//   actif / ancien ; trancher un écart ; « c'est vu ». Fonctions en base, administrateurs seuls, rien ne part chez Hektor.
//   L'ajout d'une personne sans compte de l'app reste le lot B.
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { cleAgence, nomAgence } from './lib/pilotage'
import {
  loadHistoriquePersonne, loadRegistreUtilisateurs, marquerPersonneVue, rendreRegistre, saisirRegistre, trancherEcart,
  type RuAgence, type RuDonnees, type RuEvenement, type RuFiche, type RuObjet, type RuPersonne,
} from './lib/registreUtilisateurs'
import { USER_PERIMETRES, type UserProfile } from './types'
import './registre-utilisateurs.css'

export type RuPreRemplissage = { prenom: string; nom: string; email: string; personneId: number }

type Props = {
  comptes: UserProfile[]
  comptesCharges: boolean
  /** change à chaque création / modification de compte : l'écran se relit */
  relecture: number
  message: string | null
  /** un formulaire de compte est ouvert par-dessus : Échap est pour lui */
  enPause?: boolean
  onFermer: () => void
  onAjouter: (pre?: RuPreRemplissage) => void
  onModifierAcces: (compte: UserProfile) => void
  onLienMotDePasse: (email: string) => void
}

type Onglet = 'utilisateurs' | 'agences' | 'societe'
type Segment = 'tous' | 'avec' | 'sans'

const ROLES: Record<string, string> = { admin: 'Administrateur', manager: 'Manager', commercial: 'Négociateur', lecture: 'Lecture' }
const perimetre = (p?: string | null) => USER_PERIMETRES.find((x) => x.valeur === (p ?? 'reseau'))?.libelle ?? 'Tout le réseau'

function date(iso: string | null | undefined, long = false) {
  if (!iso) return ''
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('fr-FR', long ? { day: '2-digit', month: '2-digit', year: 'numeric' } : { day: '2-digit', month: '2-digit' })
}

function telephone(v: string | null | undefined) {
  const brut = String(v ?? '').replace(/[^\d+]/g, '')
  if (/^0\d{9}$/.test(brut)) return brut.replace(/(\d{2})(?=\d)/g, '$1 ').trim()
  return v ?? ''
}

function initiales(nom: string) {
  const mots = nom.replace(/^(m_mme|mr\.?\/mme\.?|mme\.?|mlle\.?|mr\.?|m\.)\s+/i, '').split(/\s+/).filter(Boolean)
  return ((mots[0]?.[0] ?? '') + (mots[mots.length - 1]?.[0] ?? '')).toUpperCase() || '?'
}

const agenceLisible = (nom: string | null | undefined) => (nom ? nomAgence(cleAgence(nom)) : '')

/** Ce que l'écran montre d'une personne, calculé une fois. Une valeur « deduite » vient de Hektor, pas d'une saisie à nous. */
type Vue = {
  p: RuPersonne
  compte: UserProfile | null
  fonction: string
  fonctionDeduite: boolean
  agence: string
  agenceDeduite: boolean
  portable: string
  email: string
  ficheActive: RuFiche | null
  ids: string
  sync: 'a_jour' | 'ecart' | 'eteint'
  ecarts: number
}

function decrireFiche(f: RuFiche) {
  if (f.sorte === 'compte_utilisateur') {
    const type = { ADMIN: 'admin', SECRETAIRE: 'secrétaire', AGENCE: 'agence', NEGO: 'négociateur' }[String(f.typeCompte ?? '').toUpperCase()] ?? (f.typeCompte ?? '').toLowerCase()
    return `compte ${f.userId ?? '?'}${type ? ` (${type})` : ''} ${f.actif ? 'actif' : 'éteint'}`
  }
  return `négo ${f.negoId ?? '?'} ${f.actif ? 'active' : 'éteinte'}`
}

function construireVue(p: RuPersonne, comptes: Map<string, UserProfile>, agences: Map<number, RuAgence>, ecarts: number): Vue {
  const compte = p.appUserId ? comptes.get(p.appUserId) ?? null : null
  const actives = p.fiches.filter((f) => f.actif)
  const ficheActive = actives.find((f) => f.sorte === 'fiche_negociateur') ?? null

  // la fonction : la nôtre, sinon ce que disent ses comptes ACTIFS chez Hektor (une seule réponse), sinon « à choisir »
  let fonction = p.fonction ?? ''
  let fonctionDeduite = false
  if (!fonction) {
    const vues = new Set<string>()
    for (const f of actives) {
      if (f.sorte === 'fiche_negociateur') vues.add('Négociateur')
      else if (String(f.typeCompte).toUpperCase() === 'SECRETAIRE') vues.add('Secrétaire')
      else if (String(f.typeCompte).toUpperCase() === 'ADMIN') vues.add('Administrateur')
    }
    if (vues.size === 1) { fonction = [...vues][0]; fonctionDeduite = true }
    else if (vues.size === 0 && !p.actif && p.type === 'negociateur') { fonction = 'Négociateur'; fonctionDeduite = true }
  }

  // l'agence : la nôtre, sinon celle de sa fiche négo active, sinon la seule de ses fiches (un ancien : la dernière vue)
  let agence = p.appAgenceId ? agences.get(p.appAgenceId)?.nom ?? '' : ''
  let agenceDeduite = false
  if (!agence) {
    const avecAgence = p.fiches.filter((f) => f.agence)
    const distinctes = [...new Set(avecAgence.map((f) => cleAgence(f.agence)))]
    const choisie = ficheActive?.agence ?? (distinctes.length === 1 || !p.actif ? avecAgence[0]?.agence ?? null : null)
    if (choisie) { agence = agenceLisible(choisie); agenceDeduite = true }
  } else agence = agenceLisible(agence)

  const portable = p.portable ?? ficheActive?.portable ?? p.fiches.find((f) => f.portable)?.portable ?? ''
  const actifsHektor = actives.length > 0
  return {
    p, compte, fonction, fonctionDeduite, agence, agenceDeduite, portable: telephone(portable),
    email: p.emailPro ?? (compte?.email && /@gti-immobilier\.fr$/i.test(compte.email) ? compte.email : null) ?? p.email ?? compte?.email ?? '', ficheActive,
    ids: p.fiches.map(decrireFiche).join(' · ') || 'aucune fiche chez Hektor',
    sync: ecarts > 0 ? 'ecart' : actifsHektor ? 'a_jour' : 'eteint', ecarts,
  }
}

export default function RegistreUtilisateurs(props: Props) {
  const [donnees, setDonnees] = useState<RuDonnees | null>(null)
  const [chargement, setChargement] = useState(true)
  const [onglet, setOnglet] = useState<Onglet>('utilisateurs')
  const [ficheId, setFicheId] = useState<number | null>(null)
  const [agenceId, setAgenceId] = useState<number | null>(null)
  const [version, setVersion] = useState(0)
  const [notice, setNotice] = useState<string | null>(null)
  const apresGeste = (texte: string) => { setNotice(texte); setVersion((n) => n + 1) }

  useEffect(() => {
    let annule = false
    setChargement(true)
    void loadRegistreUtilisateurs()
      .then((d) => { if (!annule) setDonnees(d) })
      .catch((e) => { console.error('[registre] lecture impossible', e); if (!annule) setDonnees(null) })
      .finally(() => { if (!annule) setChargement(false) })
    return () => { annule = true }
  }, [props.relecture, version])

  // Échap ferme la fiche ouverte, puis l'écran
  useEffect(() => {
    const touche = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || props.enPause) return
      if (ficheId != null) setFicheId(null)
      else if (agenceId != null) setAgenceId(null)
      else props.onFermer()
    }
    window.addEventListener('keydown', touche)
    return () => window.removeEventListener('keydown', touche)
  }, [ficheId, agenceId, props])

  const comptesParId = useMemo(() => new Map(props.comptes.map((c) => [c.id, c])), [props.comptes])
  const agencesParId = useMemo(() => new Map((donnees?.agences ?? []).map((a) => [a.id, a])), [donnees])
  const vues = useMemo(() => (donnees?.personnes ?? [])
    .filter((p) => p.type !== 'agence')
    .map((p) => construireVue(p, comptesParId, agencesParId, donnees?.ecartsParPersonne.get(p.id) ?? 0)), [donnees, comptesParId, agencesParId])

  const ouvrirFiche = (id: number) => { setOnglet('utilisateurs'); setAgenceId(null); setFicheId(id) }
  const changerOnglet = (o: Onglet) => { setOnglet(o); setFicheId(null); setAgenceId(null); setNotice(null) }

  const fiche = ficheId != null ? vues.find((v) => v.p.id === ficheId) ?? null : null
  const agence = agenceId != null ? agencesParId.get(agenceId) ?? null : null

  return (
    <div className="ru-overlay" role="dialog" aria-modal="true" aria-label="Registre des utilisateurs">
      <div className="ru-ecran">
        <div className="ru-barre">
          <nav className="ru-onglets" aria-label="Registres">
            {([['utilisateurs', 'Utilisateurs'], ['agences', 'Agences'], ['societe', 'La société']] as Array<[Onglet, string]>).map(([cle, libelle]) => (
              <button key={cle} type="button" aria-current={onglet === cle ? 'page' : undefined} onClick={() => changerOnglet(cle)}>{libelle}</button>
            ))}
          </nav>
          <button className="ru-fermer" type="button" onClick={props.onFermer}>Fermer</button>
        </div>
        {props.message ? <p className="ru-message" role="status">{props.message}</p> : null}
        {notice ? <p className="ru-message" role="status">{notice}</p> : null}
        {chargement && !donnees ? <p className="ru-mute">Lecture du registre…</p> : null}
        {!chargement && !donnees ? <p className="ru-alerte">Le registre n’a pas pu être lu. Le détail est dans la console.</p> : null}
        {donnees && donnees.erreurs.length ? <p className="ru-alerte">Pas pu être lu : {donnees.erreurs.join(', ')}. Le reste s’affiche.</p> : null}

        {donnees && onglet === 'utilisateurs' && !fiche ? (
          <ListeUtilisateurs vues={vues} donnees={donnees} comptes={props.comptes} comptesCharges={props.comptesCharges}
            onOuvrir={ouvrirFiche} onAjouter={() => props.onAjouter()} onModifierAcces={props.onModifierAcces} />
        ) : null}
        {donnees && onglet === 'utilisateurs' && fiche ? (
          <FichePersonne v={fiche} donnees={donnees} comptes={props.comptes} onRetour={() => setFicheId(null)} version={version} onGeste={apresGeste}
            onModifierAcces={props.onModifierAcces} onLienMotDePasse={props.onLienMotDePasse}
            onDonnerAcces={() => props.onAjouter({
              prenom: fiche.p.prenom ?? '', nom: fiche.p.nomFamille ?? fiche.p.nom, email: fiche.email, personneId: fiche.p.id,
            })} />
        ) : null}
        {donnees && onglet === 'agences' && !agence ? (
          <ListeAgences donnees={donnees} vues={vues} onOuvrir={setAgenceId} />
        ) : null}
        {donnees && onglet === 'agences' && agence ? (
          <FicheAgence agence={agence} donnees={donnees} vues={vues} onRetour={() => setAgenceId(null)} onOuvrirPersonne={ouvrirFiche} onGeste={apresGeste} />
        ) : null}
        {donnees && onglet === 'societe' ? <Societe donnees={donnees} onGeste={apresGeste} /> : null}
      </div>
    </div>
  )
}

// ---- Liste des utilisateurs ---------------------------------------------------------------------------------------

function ListeUtilisateurs(props: {
  vues: Vue[]; donnees: RuDonnees; comptes: UserProfile[]; comptesCharges: boolean
  onOuvrir: (id: number) => void; onAjouter: () => void; onModifierAcces: (c: UserProfile) => void
}) {
  const { vues, donnees } = props
  const [recherche, setRecherche] = useState('')
  const [agence, setAgence] = useState('')
  const [fonction, setFonction] = useState('')
  const [segment, setSegment] = useState<Segment>('tous')
  const [anciens, setAnciens] = useState(false)

  const relies = new Set(vues.map((v) => v.p.appUserId).filter(Boolean) as string[])
  const orphelins = props.comptes.filter((c) => !relies.has(c.id))
  const agences = [...new Set(vues.map((v) => v.agence).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'fr'))
  const fonctions = [...new Set(vues.map((v) => v.fonction).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'fr'))
  const nbAgences = (donnees.personnes ?? []).filter((p) => p.type === 'agence').length

  const actives = vues.filter((v) => v.p.actif)
  const avecAcces = vues.filter((v) => v.compte?.is_active)
  const aValider = vues.filter((v) => v.p.aValider)
  const ecarts = vues.reduce((n, v) => n + v.ecarts, 0)

  const q = recherche.trim().toLowerCase()
  const qChiffres = q.replace(/\D/g, '')
  const lignes = vues.filter((v) => {
    if (!anciens && !v.p.actif) return false
    if (agence && v.agence !== agence) return false
    if (fonction && v.fonction !== fonction) return false
    if (segment === 'avec' && !v.compte) return false
    if (segment === 'sans' && v.compte) return false
    if (!q) return true
    if (`${v.p.nom} ${v.email} ${v.p.fiches.map((f) => f.email ?? '').join(' ')}`.toLowerCase().includes(q)) return true
    return qChiffres.length >= 3 && `${v.p.id} ${v.portable.replace(/\D/g, '')}`.includes(qChiffres)
  })

  return (
    <>
      <div className="ru-tete">
        <div className="ru-tete-texte">
          <span className="ru-surtitre">Administration · réservé aux administrateurs</span>
          <h1>Registre des utilisateurs</h1>
          <span className="ru-mute">Les personnes du réseau GTI sous notre numéro : leur fonction, leur agence, leurs coordonnées et leur accès à l’app. Les anciens sont gardés, jamais supprimés.</span>
        </div>
        <button className="ru-bouton" type="button" onClick={props.onAjouter}>
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><path d="M12 5v14M5 12h14" /></svg>
          Ajouter un utilisateur
        </button>
      </div>

      <div className="ru-chiffres">
        <Chiffre titre="Personnes" valeur={vues.length} detail={`dont ${vues.length - actives.length} anciens`} />
        <Chiffre titre="Actives" valeur={actives.length} detail="travaillent avec nous" ton="ok" />
        <Chiffre titre="Accès à l’app" valeur={avecAcces.length} detail={props.comptesCharges ? `+ ${orphelins.length} compte${orphelins.length > 1 ? 's' : ''} relié${orphelins.length > 1 ? 's' : ''} à personne` : 'comptes en lecture…'} />
        <Chiffre titre="À valider" valeur={aValider.length} detail="un repère à côté du nom" ton="attention" />
        <Chiffre titre="Synchro Hektor" valeur={donnees.derniereNuit ? `nuit du ${date(donnees.derniereNuit)}` : 'pas encore lue'} petit
          detail={ecarts ? `${ecarts} écart${ecarts > 1 ? 's' : ''} à trancher` : 'aucun écart à trancher'} />
      </div>

      <section className="ru-carte">
        <div className="ru-filtres">
          <label className="ru-recherche">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
            <span className="ru-cache">Rechercher</span>
            <input type="search" value={recherche} onChange={(e) => setRecherche(e.target.value)} placeholder="Nom, e-mail, téléphone, notre n°…" />
          </label>
          <label className="ru-choix"><span>Agence</span>
            <select value={agence} onChange={(e) => setAgence(e.target.value)}><option value="">Toutes</option>{agences.map((a) => <option key={a}>{a}</option>)}</select>
          </label>
          <label className="ru-choix"><span>Fonction</span>
            <select value={fonction} onChange={(e) => setFonction(e.target.value)}><option value="">Toutes</option>{fonctions.map((f) => <option key={f}>{f}</option>)}</select>
          </label>
          <div className="ru-segments" role="group" aria-label="Accès à l’app">
            {([['tous', 'Tous'], ['avec', 'Avec accès'], ['sans', 'Sans accès']] as Array<[Segment, string]>).map(([cle, libelle]) => (
              <button key={cle} type="button" aria-pressed={segment === cle} onClick={() => setSegment(cle)}>{libelle}</button>
            ))}
          </div>
          <label className={`ru-anciens${anciens ? ' is-on' : ''}`}>
            <input type="checkbox" checked={anciens} onChange={(e) => setAnciens(e.target.checked)} />
            Afficher les anciens
          </label>
        </div>
        <div className="ru-defile">
          <div className="ru-table ru-table-u">
            <div className="ru-ligne ru-entete">
              <span>Personne</span><span>Fonction</span><span>Agence</span><span>Portable</span><span>Accès à l’app</span><span>Statut</span><span className="ru-gris">Synchro Hektor</span><span />
            </div>
            {lignes.map((v) => (
              <div key={v.p.id} className="ru-ligne" role="button" tabIndex={0} onClick={() => props.onOuvrir(v.p.id)}
                onKeyDown={(e) => { if (e.key === 'Enter') props.onOuvrir(v.p.id) }}>
                <div className="ru-personne">
                  <span className={`ru-avatar${v.p.actif ? '' : ' is-ancien'}`} aria-hidden="true">{initiales(v.p.nom)}</span>
                  <div className="ru-personne-texte">
                    <div className="ru-personne-nom"><b>{v.p.nom}</b>{v.p.aValider ? <span className="ru-marque" title={v.p.aValider}>À valider</span> : null}</div>
                    <span className="ru-mute ru-petit">{v.email ? `${v.email} · ` : ''}n° {v.p.id}</span>
                  </div>
                </div>
                <span className={v.fonction ? (v.fonctionDeduite ? 'ru-deduit' : '') : 'ru-a-saisir'} title={v.fonctionDeduite ? 'd’après ses comptes chez Hektor' : undefined}>{v.fonction || 'à choisir'}</span>
                <span className={v.agence ? (v.agenceDeduite ? 'ru-deduit' : '') : 'ru-a-saisir'} title={v.agenceDeduite ? 'd’après ses fiches chez Hektor' : undefined}>{v.agence || (v.p.actif ? 'à choisir' : '—')}</span>
                <span className="ru-num">{v.portable || <span className="ru-mute">—</span>}</span>
                <Acces v={v} identite={v.p.appUserId ? donnees.identites.get(v.p.appUserId) : undefined} />
                <span className={`ru-statut${v.p.actif ? ' is-actif' : ''}`}>{v.p.actif ? 'Actif' : 'Ancien'}</span>
                <span className={`ru-sync is-${v.sync}`} title={v.ids}>{v.sync === 'ecart' ? `${v.ecarts} écart${v.ecarts > 1 ? 's' : ''}` : v.sync === 'a_jour' ? 'à jour' : 'éteint'}</span>
                <span className="ru-lien">Ouvrir</span>
              </div>
            ))}
            <div className="ru-pied">{lignes.length} personne{lignes.length > 1 ? 's' : ''} affichée{lignes.length > 1 ? 's' : ''}{anciens ? '' : ` · ${vues.length - actives.length} anciens masqués`}</div>
          </div>
        </div>
      </section>

      {props.comptesCharges ? (
        <section className="ru-carte ru-bloc">
          <h2>Comptes de l’app reliés à personne · {orphelins.length}</h2>
          {orphelins.length ? (
            <div className="ru-pile">
              {orphelins.map((c) => {
                const identite = donnees.identites.get(c.id)
                return (
                  <div key={c.id} className="ru-orphelin">
                    <b>{c.email ?? c.display_name ?? c.id}</b>
                    <span className="ru-mute">{(ROLES[c.role] ?? c.role).toLowerCase()} · {c.is_active ? 'actif' : 'désactivé'}{derniereConnexion(c, identite) ? ` · ${derniereConnexion(c, identite)}` : ''}</span>
                    <button className="ru-lien" type="button" onClick={() => props.onModifierAcces(c)}>Relier à une personne</button>
                  </div>
                )
              })}
            </div>
          ) : <span className="ru-mute">Tous les comptes de l’app sont reliés à une personne.</span>}
          <span className="ru-mute ru-petit">Les {nbAgences} comptes d’agence ne sont pas des utilisateurs : ils sont rangés dans le registre des agences.</span>
        </section>
      ) : null}
    </>
  )
}

/** « vu le … », « jamais connecté » (la date est connue et vide), ou « » quand le serveur ne l'a pas rendue */
function derniereConnexion(compte: UserProfile, identite?: { derniereConnexion: string | null }, long = false) {
  const quand = compte.last_sign_in_at ?? identite?.derniereConnexion ?? null
  if (quand) return long ? date(quand, true) : `vu le ${date(quand)}`
  return 'last_sign_in_at' in compte ? (long ? 'jamais' : 'jamais connecté') : ''
}

function Acces({ v, identite }: { v: Vue; identite?: { derniereConnexion: string | null } }) {
  if (!v.compte) return <div className="ru-acces"><span className="ru-mute">Pas d’accès</span></div>
  if (!v.compte.is_active) return <div className="ru-acces"><span className="ru-mute">Accès désactivé</span></div>
  const vu = derniereConnexion(v.compte, identite)
  return (
    <div className="ru-acces">
      <span className="ru-acces-role">{ROLES[v.compte.role] ?? v.compte.role} · {perimetre(v.compte.perimetre).toLowerCase()}</span>
      <span className="ru-mute ru-petit">{vu}</span>
    </div>
  )
}

function Chiffre({ titre, valeur, detail, ton, petit }: { titre: string; valeur: ReactNode; detail: string; ton?: 'ok' | 'attention'; petit?: boolean }) {
  return (
    <div className="ru-chiffre">
      <span className="ru-mute ru-petit">{titre}</span>
      <b className={`${petit ? 'is-petit' : ''}${ton ? ` is-${ton}` : ''}`}>{valeur}</b>
      <span className="ru-mute ru-petit">{detail}</span>
    </div>
  )
}

// ---- Fiche d'une personne -----------------------------------------------------------------------------------------

function Champ({ titre, valeur, aide, ton, siVide = 'à saisir' }: { titre: string; valeur: ReactNode; aide?: string; ton?: 'ok' | 'attention'; siVide?: string }) {
  const vide = valeur == null || valeur === ''
  return (
    <div className="ru-champ">
      <span className="ru-mute ru-petit">{titre}</span>
      <b className={vide ? 'ru-a-saisir' : undefined}>{vide ? siVide : valeur}</b>
      {aide ? <span className={`ru-aide${ton ? ` is-${ton}` : ''}`}>{aide}</span> : null}
    </div>
  )
}

// ---- La saisie au carnet (lot C) ------------------------------------------------------------------------------------

type ChampSaisie = {
  champ: string
  titre: string
  /** la valeur À NOUS (la colonne), pas la valeur déduite de Hektor */
  valeur: string | null
  /** ce que l'écran affiche aujourd'hui (Hektor, ou l'accès @gti pour l'e-mail), en grisé, quand la nôtre est vide */
  indice?: string
  type?: 'texte' | 'choix' | 'date'
  options?: Array<[string, string]>
  suggestions?: string[]
}

function FormulaireSaisie({ objet, id, champs, carnet, onGeste, onFermer }: {
  objet: RuObjet; id: number; champs: ChampSaisie[]; carnet: Set<string>; onGeste: (texte: string) => void; onFermer: () => void
}) {
  const [valeurs, setValeurs] = useState<Record<string, string>>(() => Object.fromEntries(champs.map((c) => [c.champ, c.valeur ?? ''])))
  const [occupe, setOccupe] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const modifies = champs.filter((c) => (valeurs[c.champ] ?? '').trim() !== (c.valeur ?? '').trim())

  async function enregistrer() {
    if (!modifies.length) { onFermer(); return }
    setOccupe(true)
    setErreur(null)
    try {
      await saisirRegistre(objet, id, Object.fromEntries(modifies.map((c) => [c.champ, (valeurs[c.champ] ?? '').trim() || null])))
      onGeste(`${modifies.length} champ${modifies.length > 1 ? 's' : ''} enregistré${modifies.length > 1 ? 's' : ''} chez nous : ${modifies.map((c) => c.titre.toLowerCase()).join(', ')}. La nuit ne les écrase plus.`)
      onFermer()
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    } finally {
      setOccupe(false)
    }
  }

  async function rendre(c: ChampSaisie) {
    setOccupe(true)
    setErreur(null)
    try {
      await rendreRegistre(objet, id, c.champ)
      onGeste(`${c.titre} rendu à Hektor : la nuit prochaine le reposera.`)
      onFermer()
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    } finally {
      setOccupe(false)
    }
  }

  return (
    <form className="ru-saisie" onSubmit={(e) => { e.preventDefault(); void enregistrer() }}>
      <div className="ru-saisie-grille">
        {champs.map((c) => {
          const auCarnet = carnet.has(`${objet}:${id}:${c.champ}`)
          const liste = c.suggestions?.length ? `ru-sugg-${c.champ}` : undefined
          return (
            <label key={c.champ} className="ru-saisie-champ">
              <span className="ru-mute ru-petit">{c.titre}</span>
              {c.type === 'choix' ? (
                <select value={valeurs[c.champ] ?? ''} onChange={(e) => setValeurs({ ...valeurs, [c.champ]: e.target.value })} disabled={occupe}>
                  {(c.options ?? []).map(([val, lib]) => <option key={val} value={val}>{lib}</option>)}
                </select>
              ) : (
                <input type={c.type === 'date' ? 'date' : 'text'} value={valeurs[c.champ] ?? ''} placeholder={c.indice ? `affiché : ${c.indice}` : ''} list={liste}
                  onChange={(e) => setValeurs({ ...valeurs, [c.champ]: e.target.value })} disabled={occupe} />
              )}
              {liste ? <datalist id={liste}>{c.suggestions?.map((x) => <option key={x} value={x} />)}</datalist> : null}
              <span className="ru-aide">
                {auCarnet ? <>saisi chez nous · <button type="button" className="ru-lien ru-gauche is-mini" disabled={occupe} onClick={() => void rendre(c)}>Rendre à Hektor</button></>
                  : c.valeur ? 'repris de Hektor' : 'vide chez nous · la nuit le remplira'}
              </span>
            </label>
          )
        })}
      </div>
      {erreur ? <p className="ru-alerte">{erreur}</p> : null}
      <div className="ru-actions ru-saisie-pied">
        <span className="ru-mute ru-petit">{modifies.length ? `${modifies.length} champ${modifies.length > 1 ? 's' : ''} modifié${modifies.length > 1 ? 's' : ''}` : 'Rien de modifié'} · un champ vidé reste vide (la nuit ne le remplit plus)</span>
        <button className="ru-fermer" type="button" onClick={onFermer} disabled={occupe}>Annuler</button>
        <button className="ru-bouton" type="submit" disabled={occupe || !modifies.length}>{occupe ? 'Enregistrement…' : 'Enregistrer'}</button>
      </div>
    </form>
  )
}

const FONCTIONS = ['Négociateur', 'Agent commercial', 'Secrétaire', 'Assistante', 'Responsable d’agence', 'Administrateur', 'Gérant']

function FichePersonne(props: {
  v: Vue; donnees: RuDonnees; comptes: UserProfile[]; onRetour: () => void; version: number; onGeste: (texte: string) => void
  onModifierAcces: (c: UserProfile) => void; onLienMotDePasse: (email: string) => void; onDonnerAcces: () => void
}) {
  const { v, donnees } = props
  const p = v.p
  const [historique, setHistorique] = useState<RuEvenement[] | null | undefined>(undefined)
  const [edition, setEdition] = useState(false)
  const [confirmeStatut, setConfirmeStatut] = useState(false)
  const [occupe, setOccupe] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  useEffect(() => {
    let annule = false
    setHistorique(undefined)
    void loadHistoriquePersonne(p.id).then((h) => { if (!annule) setHistorique(h) })
    return () => { annule = true }
  }, [p.id, props.version])
  useEffect(() => { setEdition(false); setConfirmeStatut(false); setErreur(null) }, [p.id])

  async function geste(action: () => Promise<unknown>, texte: string) {
    setOccupe(true)
    setErreur(null)
    try {
      await action()
      props.onGeste(texte)
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    } finally {
      setOccupe(false)
      setConfirmeStatut(false)
    }
  }
  const statutAuCarnet = donnees.carnet.has(`personne:${p.id}:actif`)

  const identite = p.appUserId ? donnees.identites.get(p.appUserId) : undefined
  const autresComptes = useMemo(() => {
    // les comptes de l'app NON reliés qui portent l'une de ses adresses (le gmail de Franck)
    const relies = new Set((donnees.personnes ?? []).map((x) => x.appUserId).filter(Boolean))
    const adresses = new Set([p.email, p.emailPro, ...p.fiches.map((f) => f.email)].filter(Boolean).map((e) => String(e).toLowerCase()))
    return props.comptes.filter((c) => !relies.has(c.id) && c.email && adresses.has(c.email.toLowerCase()))
  }, [donnees.personnes, p, props.comptes])
  const prenom = p.prenom ?? ''
  const nomFamille = p.nomFamille ?? ''
  const ficheGestes = identite?.hektorNegociateurId ? p.fiches.find((f) => f.negoId === identite.hektorNegociateurId) : null
  const comptesHektor = p.fiches.filter((f) => f.sorte === 'compte_utilisateur' && f.actif)
  const ecartsHisto = (historique ?? []).filter((h) => h.aSignaler)

  return (
    <>
      <button className="ru-retour" type="button" onClick={props.onRetour}>← Registre des utilisateurs</button>
      <div className="ru-carte ru-fiche-tete">
        <div className="ru-fiche-qui">
          <span className={`ru-avatar is-grand${p.actif ? '' : ' is-ancien'}`} aria-hidden="true">{initiales(p.nom)}</span>
          <div className="ru-pile-serree">
            <div className="ru-fiche-nom">
              <h1>{p.nom}</h1>
              <span className={`ru-pastille${p.actif ? ' is-actif' : ''}`}>{p.actif ? 'Actif' : 'Ancien'}</span>
              {p.aValider ? <span className="ru-marque" title={p.aValider}>À valider</span> : null}
            </div>
            <span className="ru-mute">Notre n° {p.id}{v.email ? ` · ${v.email}` : ''}{v.compte ? ` · accès ${(ROLES[v.compte.role] ?? v.compte.role).toLowerCase()} à l’app` : ' · pas d’accès à l’app'}</span>
          </div>
        </div>
        <div className="ru-actions">
          {!edition ? <button className="ru-bouton-ligne" type="button" onClick={() => setEdition(true)}>Modifier</button> : null}
          {v.compte ? <button className="ru-bouton-ligne is-gris" type="button" onClick={() => props.onModifierAcces(v.compte as UserProfile)}>Modifier son accès</button> : null}
          {!v.compte && p.actif ? <button className="ru-bouton-ligne is-gris" type="button" onClick={props.onDonnerAcces}>Lui donner l’accès à l’app</button> : null}
          {confirmeStatut ? (
            <>
              <button className="ru-bouton" type="button" disabled={occupe}
                onClick={() => void geste(() => saisirRegistre('personne', p.id, { actif: !p.actif }), p.actif ? `${p.nom} passe en ancien chez nous. La nuit ne le remet plus actif.` : `${p.nom} redevient actif chez nous.`)}>
                {p.actif ? 'Confirmer : ancien' : 'Confirmer : actif'}
              </button>
              <button className="ru-fermer" type="button" onClick={() => setConfirmeStatut(false)}>Annuler</button>
            </>
          ) : (
            <button className="ru-fermer" type="button" disabled={occupe} onClick={() => setConfirmeStatut(true)}
              title={p.actif ? 'Il sort des listes d’actifs (répartition, filtres). Rien ne change chez Hektor.' : undefined}>
              {p.actif ? 'Le passer en ancien' : 'Le remettre actif'}
            </button>
          )}
        </div>
      </div>
      {erreur ? <p className="ru-alerte">{erreur}</p> : null}
      {statutAuCarnet ? (
        <p className="ru-mute ru-petit ru-ligne-info">Statut {p.actif ? 'actif' : 'ancien'} saisi chez nous : la nuit ne le recalcule plus.{' '}
          <button type="button" className="ru-lien ru-gauche is-mini" disabled={occupe}
            onClick={() => void geste(() => rendreRegistre('personne', p.id, 'actif'), 'Statut rendu à Hektor : la nuit prochaine le recalculera.')}>Rendre le statut à Hektor</button>
        </p>
      ) : null}

      <div className="ru-colonnes">
        <div className="ru-principal">
          <section className="ru-carte">
            <div className="ru-carte-tete"><h2>Qui il est</h2><span className="ru-mute ru-petit">nos données ; ce que vous saisissez ici, la nuit ne l’écrase plus</span></div>
            {edition ? (
              <FormulaireSaisie objet="personne" id={p.id} carnet={donnees.carnet} onGeste={props.onGeste} onFermer={() => setEdition(false)} champs={[
                { champ: 'civilite', titre: 'Civilité', valeur: p.civilite, type: 'choix', options: [['', '—'], ['M.', 'M.'], ['Mme', 'Mme']] },
                { champ: 'prenom', titre: 'Prénom', valeur: p.prenom },
                { champ: 'nom_famille', titre: 'Nom', valeur: p.nomFamille, indice: p.prenom ? undefined : p.nom },
                { champ: 'fonction', titre: 'Fonction', valeur: p.fonction, indice: v.fonctionDeduite ? v.fonction : undefined, suggestions: FONCTIONS },
                { champ: 'app_agence_id', titre: 'Agence', valeur: p.appAgenceId == null ? null : String(p.appAgenceId), type: 'choix',
                  options: [['', (donnees.agences ?? []).length ? (v.agenceDeduite ? `— (Hektor : ${v.agence})` : '—') : '— (les agences arrivent avec la nuit)'],
                    ...(donnees.agences ?? []).map((a): [string, string] => [String(a.id), a.nom])] },
                { champ: 'email_pro', titre: 'E-mail professionnel', valeur: p.emailPro, indice: v.email || undefined },
                { champ: 'portable', titre: 'Portable', valeur: p.portable, indice: v.portable || undefined },
                { champ: 'telephone', titre: 'Téléphone fixe', valeur: p.telephone,
                  indice: ((fixe) => (fixe && fixe !== v.portable ? fixe : undefined))(telephone(v.ficheActive?.telephone)) },
              ]} />
            ) : (
            <div className="ru-grille-qui">
              <div className="ru-photo">
                {p.photo ? <img src={p.photo} alt="" /> : <span className="ru-avatar is-tres-grand" aria-hidden="true">{initiales(p.nom)}</span>}
              </div>
              <Champ titre="Civilité" valeur={p.civilite} />
              <Champ titre="Prénom" valeur={prenom} />
              <Champ titre="Nom" valeur={nomFamille || (prenom ? '' : p.nom)} />
              <Champ titre="Fonction" valeur={v.fonction} siVide="à choisir" aide={v.fonctionDeduite ? 'd’après ses comptes chez Hektor' : v.fonction ? undefined : 'négociateur, secrétaire, administrateur…'} />
              <Champ titre="Agence" valeur={v.agence} siVide={p.actif ? 'à choisir' : '—'} aide={v.agenceDeduite ? 'd’après ses fiches chez Hektor' : undefined}
                ton={/formation/i.test(v.agence) ? 'attention' : undefined} />
              <Champ titre="Statut" valeur={p.actif ? 'Actif' : 'Ancien'} aide={p.actif ? 'travaille avec nous' : 'gardé, jamais supprimé'} />
              <Champ titre="E-mail professionnel" valeur={v.email} aide={v.compte?.email && v.compte.email.toLowerCase() === v.email.toLowerCase() ? 'celle de son accès à l’app' : undefined} ton="ok" />
              <Champ titre="Portable" valeur={v.portable} />
              <Champ titre="Téléphone fixe" valeur={((fixe) => (fixe && fixe !== v.portable ? fixe : ''))(telephone(p.telephone ?? v.ficheActive?.telephone))} />
            </div>
            )}
          </section>

          <section className="ru-carte">
            <div className="ru-carte-tete">
              <h2>Son accès à l’app</h2>
              {v.compte?.email ? <button className="ru-bouton-ligne is-petit" type="button" onClick={() => props.onLienMotDePasse(v.compte?.email ?? '')}>Envoyer un lien de mot de passe</button> : null}
            </div>
            {v.compte ? (
              <div className="ru-grille-4">
                <Champ titre="Identifiant" valeur={v.compte.email} />
                <Champ titre="Rôle" valeur={ROLES[v.compte.role] ?? v.compte.role} aide={v.compte.is_active ? undefined : 'accès désactivé'} ton="attention" />
                <Champ titre="Jusqu’où il voit" valeur={perimetre(v.compte.perimetre)} />
                <Champ titre="Dernière connexion" valeur={derniereConnexion(v.compte, identite, true) || 'inconnue'} />
              </div>
            ) : (
              <p className="ru-corps ru-mute">Pas d’accès à l’app.{p.actif ? ' « Lui donner l’accès à l’app » ouvre la création de compte, déjà reliée à cette personne.' : ''}</p>
            )}
            {autresComptes.length ? (
              <div className="ru-sous-bloc">
                <span className="ru-sous-titre">{autresComptes.length > 1 ? `${autresComptes.length} autres comptes` : 'Un autre compte'} de l’app à son adresse, non relié{autresComptes.length > 1 ? 's' : ''}</span>
                {autresComptes.map((c) => (
                  <div key={c.id} className="ru-orphelin"><b>{c.email}</b><span className="ru-mute">{(ROLES[c.role] ?? c.role).toLowerCase()} · {c.is_active ? 'actif' : 'désactivé'}</span></div>
                ))}
              </div>
            ) : null}
          </section>

          <section className="ru-carte ru-bloc">
            <h2>Historique</h2>
            {historique === undefined ? <span className="ru-mute">Lecture…</span> : null}
            {historique === null ? <span className="ru-alerte">L’historique n’a pas pu être lu.</span> : null}
            <ol className="ru-histo">
              {(historique ?? []).map((h, i) => (
                <li key={i}><span className="ru-mute ru-num">{date(h.quand)}</span><span>{h.texte}{h.aSignaler ? <span className="ru-marque">à trancher</span> : null}</span></li>
              ))}
              {p.creeLe ? <li><span className="ru-mute ru-num">{date(p.creeLe)}</span><span>Entré au registre sous le n° {p.id}{p.origine === 'app' ? ', né dans l’app' : ''}</span></li> : null}
            </ol>
          </section>

          <details className="ru-synchro" open>
            <summary>
              <span className="ru-synchro-titre">Synchro avec Hektor</span>
              <span className="ru-mute ru-petit">{p.fiches.length} fiche{p.fiches.length > 1 ? 's' : ''} chez Hektor{donnees.derniereNuit ? ` · dernière lecture nuit du ${date(donnees.derniereNuit)}` : ''}{v.ecarts ? ` · ${v.ecarts} écart${v.ecarts > 1 ? 's' : ''}` : ''}</span>
            </summary>
            <div className="ru-synchro-corps">
              <div className="ru-encadre">
                <span className="ru-mute">Son accès à l’app agit chez Hektor par</span>
                <b>{!v.compte ? 'pas d’accès à l’app' : ficheGestes ? `la fiche négociateur n° ${ficheGestes.negoId}${ficheGestes.agence ? ` (${agenceLisible(ficheGestes.agence)})` : ''}` : identite?.hektorUserId ? `le compte n° ${identite.hektorUserId}` : 'aucune fiche : rien n’est envoyé en son nom'}</b>
                {comptesHektor.length ? <><span className="ru-mute">Son compte chez Hektor</span><span>{comptesHektor.map((f) => decrireFiche(f)).join(' · ')} — noté, jamais envoyé dans un geste</span></> : null}
                <span className="ru-mute">Pilotage et transactions</span><span>{p.fiches.length > 1 ? `ses ${p.fiches.length} fiches réunies en une personne` : 'une seule personne'}</span>
              </div>
              <div className="ru-defile">
                <div className="ru-table ru-table-f">
                  <div className="ru-ligne ru-entete"><span>Fiche Hektor</span><span>Agence chez Hektor</span><span>Chez Hektor</span><span>Rattachée</span></div>
                  {p.fiches.map((f, i) => (
                    <div key={i} className="ru-ligne is-fixe">
                      <b className={f.actif ? undefined : 'ru-normal'}>{f.sorte === 'compte_utilisateur' ? `compte n° ${f.userId}${f.typeCompte ? ` · ${f.typeCompte.toLowerCase()}` : ''}` : `négociateur n° ${f.negoId}`}</b>
                      <span>{f.agence ? agenceLisible(f.agence) : '—'}</span>
                      <span className={f.actif ? 'ru-ok' : 'ru-gris'}>{f.actif ? (f.sorte === 'compte_utilisateur' ? 'actif' : 'active') : f.absentDepuis ? `absente depuis le ${date(f.absentDepuis)}` : 'éteinte'}</span>
                      <span className="ru-mute">{f.rattachePar ?? '—'}{f.email ? ` · ${f.email}` : ''}</span>
                    </div>
                  ))}
                  {!p.fiches.length ? <div className="ru-pied">Aucune fiche chez Hektor : personne née dans l’app.</div> : null}
                </div>
              </div>
              <span className="ru-mute ru-petit">Ces numéros servent aux échanges avec Hektor tant qu’il vit ; après la coupure, seul notre n° {p.id} compte.</span>
            </div>
          </details>
        </div>

        <aside className="ru-cote">
          {p.aValider || ecartsHisto.length ? (
            <section className="ru-carte ru-bloc ru-a-valider">
              <h2>À valider · {(p.aValider ? 1 : 0) + ecartsHisto.length}</h2>
              {p.aValider ? (
                <div className="ru-pile">
                  <p>{p.aValider}</p>
                  <div className="ru-actions">
                    <button className="ru-bouton is-sombre" type="button" disabled={occupe}
                      onClick={() => void geste(() => marquerPersonneVue(p.id), `« À valider » retiré pour ${p.nom}.`)}>C’est vu</button>
                  </div>
                </div>
              ) : null}
              {ecartsHisto.map((h, i) => {
                const ecart = h.ecart
                return (
                  <div key={i} className="ru-pile">
                    <p>{h.texte}</p>
                    {ecart ? (
                      <div className="ru-actions">
                        <button className="ru-bouton is-sombre" type="button" disabled={occupe}
                          onClick={() => void geste(() => trancherEcart(ecart.source, ecart.id, 'garder'), 'Écart tranché : la nôtre est gardée, il ne revient plus.')}>
                          {ecart.source === 'registre' ? 'Garder la nôtre' : 'Classer'}
                        </button>
                        {ecart.source === 'registre' && ecart.chezHektor ? (
                          <button className="ru-fermer" type="button" disabled={occupe}
                            onClick={() => void geste(() => trancherEcart('registre', ecart.id, 'prendre'), 'Écart tranché : la valeur de Hektor est prise chez nous.')}>
                            Prendre celle de Hektor
                          </button>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                )
              })}
              {ecartsHisto.length ? <span className="ru-mute ru-petit">« Garder la nôtre » ne change rien chez Hektor : l’écart ne revient plus.</span> : null}
            </section>
          ) : null}
          <section className="ru-carte ru-bloc">
            <h2>Où on le retrouve dans l’app</h2>
            <span>Pilotage et transactions : <b>une seule personne</b>.</span>
            <span>Menus de saisie : {v.ficheActive ? 'son nom parmi les négociateurs actifs.' : 'absent (aucune fiche négociateur active chez Hektor).'}</span>
            <span>Rendez-vous et agenda : {v.compte ? 'par son accès à l’app.' : 'pas d’accès à l’app.'}</span>
          </section>
        </aside>
      </div>
    </>
  )
}

// ---- Agences ------------------------------------------------------------------------------------------------------

/** Les négociateurs ACTIFS d'une agence : la personne rangée chez elle, sinon sa fiche négo active dans cette agence. */
function equipe(agence: RuAgence, vues: Vue[]) {
  const cles = new Set([agence.nom, ...agence.ecritures].map((e) => cleAgence(e)))
  return vues.filter((v) => v.p.actif && (v.p.appAgenceId === agence.id || (v.p.appAgenceId == null && v.ficheActive?.agence && cles.has(cleAgence(v.ficheActive.agence)))))
}

function emailsPartages(agences: RuAgence[]) {
  const compte = new Map<string, number>()
  for (const a of agences) if (a.email) compte.set(a.email.toLowerCase(), (compte.get(a.email.toLowerCase()) ?? 0) + 1)
  return compte
}

const pasUneVraieAgence = (a: RuAgence) => /formation|supprim/i.test(a.nom)

function RegistreVide({ quoi }: { quoi: string }) {
  return (
    <section className="ru-carte ru-bloc">
      <h2>{quoi} : pas encore rempli</h2>
      <span>Ce registre est rempli et tenu par la nuit, à partir des listes que la nuit télécharge déjà. Elle n’a pas encore écrit.</span>
      <span className="ru-mute ru-petit">Il se remplit la première nuit où cette tenue écrit.</span>
    </section>
  )
}

function ListeAgences({ donnees, vues, onOuvrir }: { donnees: RuDonnees; vues: Vue[]; onOuvrir: (id: number) => void }) {
  const agences = donnees.agences
  return (
    <>
      <div className="ru-tete">
        <div className="ru-tete-texte">
          <span className="ru-surtitre">Administration · réservé aux administrateurs</span>
          <h1>Registre des agences</h1>
          <span className="ru-mute">Nos agences sous notre numéro : coordonnées, responsable, équipe. Ce que vous corrigez ici est à nous ; Hektor ne le complète que tant qu’il vit.</span>
        </div>
        <div className="ru-pile-serree ru-droite">
          <button className="ru-bouton" type="button" disabled>Ajouter une agence · à venir</button>
          <span className="ru-mute ru-petit">Une agence se crée chez Hektor tant qu’il vit ; ici après la coupure.</span>
        </div>
      </div>
      {agences === null ? <p className="ru-alerte">Le registre des agences n’a pas pu être lu.</p> : null}
      {agences && !agences.length ? <RegistreVide quoi="Le registre des agences" /> : null}
      {agences && agences.length ? (() => {
        const vraies = agences.filter((a) => !pasUneVraieAgence(a))
        const partages = emailsPartages(agences)
        const aVerifier = agences.filter((a) => a.email && (partages.get(a.email.toLowerCase()) ?? 0) > 1)
        const aSaisir = vraies.filter((a) => !a.adresse || !a.responsable)
        const equipeActive = new Set(agences.flatMap((a) => equipe(a, vues).map((v) => v.p.id)))
        return (
          <>
            <div className="ru-chiffres is-4">
              <Chiffre titre="Agences" valeur={vraies.length} detail={agences.length > vraies.length ? `+ ${agences.filter(pasUneVraieAgence).map((a) => `« ${a.nom} »`).join(' et ')}` : 'toutes actives'} />
              <Chiffre titre="Équipe active" valeur={equipeActive.size} detail="personnes rattachées" ton="ok" />
              <Chiffre titre="E-mails à vérifier" valeur={aVerifier.length} detail="la boîte d’une autre agence" ton="attention" />
              <Chiffre titre="À saisir chez nous" valeur={aSaisir.length} detail="adresse ou responsable manquant" />
            </div>
            <section className="ru-carte">
              <div className="ru-defile">
                <div className="ru-table ru-table-a">
                  <div className="ru-ligne ru-entete"><span>Notre n°</span><span>Agence</span><span>E-mail</span><span>Téléphone</span><span>Équipe</span><span>Statut</span><span className="ru-gris">Synchro Hektor</span><span /></div>
                  {agences.map((a) => {
                    const partage = a.email && (partages.get(a.email.toLowerCase()) ?? 0) > 1
                    return (
                      <div key={a.id} className="ru-ligne" role="button" tabIndex={0} onClick={() => onOuvrir(a.id)} onKeyDown={(e) => { if (e.key === 'Enter') onOuvrir(a.id) }}>
                        <span className="ru-num ru-mute">{a.id}</span>
                        <b>{a.nom}</b>
                        <span className={partage ? 'ru-a-saisir' : undefined} title={partage ? 'la même boîte qu’une autre agence : à vérifier' : undefined}>{a.email ?? '—'}{partage ? ' ⚠' : ''}</span>
                        <span className="ru-num">{telephone(a.telephone) || '—'}</span>
                        <span className="ru-num">{equipe(a, vues).length}</span>
                        <span className={`ru-statut${a.statut === 'active' ? ' is-actif' : ''}`}>{{ active: 'Active', formation: 'Formation', supprimee: 'Supprimée', fermee: 'Fermée' }[a.statut ?? ''] ?? a.statut ?? '—'}</span>
                        <span className={`ru-sync is-${a.present ? 'a_jour' : 'eteint'}`} title={`agence Hektor n° ${a.hektorAgenceId ?? '?'} · compte d’agence n° ${a.hektorCompteId ?? '?'}`}>{a.present ? 'à jour' : 'absente'}</span>
                        <span className="ru-lien">Ouvrir</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </section>
          </>
        )
      })() : null}
    </>
  )
}

function FicheAgence({ agence: a, donnees, vues, onRetour, onOuvrirPersonne, onGeste }: {
  agence: RuAgence; donnees: RuDonnees; vues: Vue[]; onRetour: () => void; onOuvrirPersonne: (id: number) => void; onGeste: (texte: string) => void
}) {
  const [edition, setEdition] = useState(false)
  const membres = equipe(a, vues)
  const partageAvec = (donnees.agences ?? []).filter((x) => x.id !== a.id && a.email && x.email?.toLowerCase() === a.email.toLowerCase())
  const carnet = (champ: string) => donnees.carnet.has(`agence:${a.id}:${champ}`)
  const origine = (champ: string, valeur: string | null) => (valeur ? (carnet(champ) ? 'saisi chez nous' : 'repris de Hektor') : 'manquant')
  return (
    <>
      <button className="ru-retour" type="button" onClick={onRetour}>← Registre des agences</button>
      <div className="ru-carte ru-fiche-tete">
        <div className="ru-pile-serree">
          <div className="ru-fiche-nom"><h1>{a.nom}</h1><span className={`ru-pastille${a.statut === 'active' ? ' is-actif' : ''}`}>{{ active: 'Active', formation: 'Formation', supprimee: 'Supprimée', fermee: 'Fermée' }[a.statut ?? ''] ?? a.statut ?? '—'}</span></div>
          <span className="ru-mute">Notre n° {a.id} · {membres.length} personne{membres.length > 1 ? 's' : ''} active{membres.length > 1 ? 's' : ''} · {a.responsable ? `responsable ${a.responsable}` : 'responsable à saisir'}</span>
        </div>
      </div>
      <div className="ru-colonnes">
        <div className="ru-principal">
          <section className="ru-carte">
            <div className="ru-carte-tete"><h2>Coordonnées — à nous</h2>
              {!edition ? <button className="ru-bouton-ligne is-petit" type="button" onClick={() => setEdition(true)}>Modifier l’agence</button> : null}</div>
            {edition ? (
              <FormulaireSaisie objet="agence" id={a.id} carnet={donnees.carnet} onGeste={onGeste} onFermer={() => setEdition(false)} champs={[
                { champ: 'nom', titre: 'Nom affiché', valeur: a.nom },
                { champ: 'telephone', titre: 'Téléphone', valeur: a.telephone },
                { champ: 'email', titre: 'E-mail', valeur: a.email },
                { champ: 'adresse', titre: 'Adresse', valeur: a.adresse },
                { champ: 'code_postal', titre: 'Code postal', valeur: a.codePostal },
                { champ: 'ville', titre: 'Ville', valeur: a.ville },
                { champ: 'responsable', titre: 'Responsable', valeur: a.responsable },
                { champ: 'siret_etablissement', titre: 'SIRET de l’établissement', valeur: a.siret },
                { champ: 'site', titre: 'Site', valeur: a.site },
              ]} />
            ) : (
            <div className="ru-grille-3">
              <Champ titre="Nom affiché" valeur={a.nom} aide={origine('nom', a.nom)} />
              <Champ titre="Téléphone" valeur={telephone(a.telephone)} aide={origine('telephone', a.telephone)} />
              <Champ titre="E-mail" valeur={a.email} aide={partageAvec.length ? `⚠ la boîte de ${partageAvec.map((x) => x.nom).join(', ')} — à vérifier` : origine('email', a.email)} ton={partageAvec.length ? 'attention' : undefined} />
              <Champ titre="Adresse" valeur={[a.adresse, [a.codePostal, a.ville].filter(Boolean).join(' ')].filter(Boolean).join(', ')} aide={origine('adresse', a.adresse)} />
              <Champ titre="Responsable" valeur={a.responsable} />
              <Champ titre="SIRET de l’établissement" valeur={a.siret} aide={a.siret ? undefined : 'la société a le sien'} />
            </div>
            )}
          </section>
          <section className="ru-carte ru-bloc">
            <h2>Les écritures de son nom</h2>
            <span className="ru-mute">Les biens, mandats et contacts écrivent le nom de l’agence de plusieurs façons. Chaque écriture connue est rattachée ici à notre n° {a.id} : c’est elle qui range une ligne dans la bonne agence.</span>
            <div className="ru-etiquettes">{(a.ecritures.length ? a.ecritures : [a.nom]).map((e) => <span key={e} className="ru-etiquette">{e}</span>)}</div>
          </section>
          <details className="ru-synchro">
            <summary><span className="ru-synchro-titre">Synchro avec Hektor</span><span className="ru-mute ru-petit">{a.derniereVue ? `dernière lecture le ${date(a.derniereVue)}` : 'pas encore lue'}</span></summary>
            <div className="ru-synchro-corps">
              <span>agence Hektor n° {a.hektorAgenceId ?? '?'}, compte d’agence n° {a.hektorCompteId ?? '?'} — {a.present ? 'présents chez Hektor' : `absents de la liste${a.absentDepuis ? ` depuis le ${date(a.absentDepuis)}` : ''}, gardés`}</span>
              <span className="ru-mute ru-petit">Après la coupure, seul notre n° {a.id} compte.</span>
            </div>
          </details>
        </div>
        <aside className="ru-cote">
          <section className="ru-carte ru-bloc">
            <h2>Équipe active · {membres.length}</h2>
            {membres.map((m) => <button key={m.p.id} type="button" className="ru-lien ru-gauche" onClick={() => onOuvrirPersonne(m.p.id)}>{m.p.nom} · {m.fonction || 'fonction à choisir'}</button>)}
            {!membres.length ? <span className="ru-mute">Personne d’actif rattaché.</span> : null}
          </section>
          {partageAvec.length ? (
            <section className="ru-carte ru-bloc ru-a-valider">
              <h2>À valider</h2>
              <p>E-mail : Hektor donne {a.email}, la boîte de {partageAvec.map((x) => x.nom).join(', ')}.</p>
            </section>
          ) : null}
        </aside>
      </div>
    </>
  )
}

// ---- La société ---------------------------------------------------------------------------------------------------

const CHAMPS_SOCIETE: Array<[string, string]> = [
  ['raison_sociale', 'Raison sociale'], ['forme', 'Forme'], ['siret', 'SIRET'], ['naf', 'Code NAF'], ['capital', 'Capital'],
  ['rcs', 'RCS (numéro)'], ['rcs_ville', 'RCS (ville)'], ['tva', 'TVA intracommunautaire'], ['siege_adresse', 'Siège : adresse'],
  ['siege_code_postal', 'Siège : code postal'], ['siege_ville', 'Siège : ville'], ['telephone', 'Téléphone'], ['email', 'E-mail'],
  ['assureur_nom', 'Assureur RCP'], ['rcp_numero', 'N° de contrat RCP'], ['assureur_adresse', 'Assureur : adresse'],
  ['assureur_code_postal', 'Assureur : code postal'], ['assureur_ville', 'Assureur : ville'], ['mediateur_nom', 'Médiateur'],
  ['mediateur_adresse', 'Médiateur : adresse'], ['mediateur_code_postal', 'Médiateur : code postal'], ['mediateur_ville', 'Médiateur : ville'],
  ['mediateur_site', 'Médiateur : site'], ['carte_type', 'Carte : type'], ['carte_numero', 'Carte : numéro'],
  ['carte_delivree_par', 'Carte : délivrée par'], ['carte_detenteur', 'Carte : détenteur'], ['carte_maniement_fonds', 'Carte : maniement de fonds'],
  ['carte_validite', 'Carte : valable jusqu’au'], ['carte_garant', 'Carte : garant'], ['carte_montant', 'Carte : montant de la garantie'],
]

function Societe({ donnees, onGeste }: { donnees: RuDonnees; onGeste: (texte: string) => void }) {
  const [edition, setEdition] = useState(false)
  const s = donnees.societe
  const nbAgences = (donnees.agences ?? []).filter((a) => !pasUneVraieAgence(a)).length
  const ligne = (...parts: Array<string | null | undefined>) => parts.filter(Boolean).join(' · ')
  const adresse = (a?: string | null, cp?: string | null, v?: string | null) => [a, [cp, v].filter(Boolean).join(' ')].filter(Boolean).join(', ')
  if (donnees.erreurs.includes('la société')) return <p className="ru-alerte">La société n’a pas pu être lue.</p>
  if (!s) return <RegistreVide quoi="La société" />
  const validite = s.carte_validite
  const rappel = validite ? new Date(`${validite}T12:00:00`) : null
  if (rappel) rappel.setMonth(rappel.getMonth() - 3)
  return (
    <>
      <div className="ru-tete">
        <div className="ru-tete-texte">
          <span className="ru-surtitre">Une seule société{nbAgences ? ` · ses ${nbAgences} agences` : ''}</span>
          <h1>{s.raison_sociale ?? 'La société'}</h1>
          <span className="ru-mute">Nos informations légales, à nous. Reprises de Hektor ; ce que vous saisissez ici, la nuit ne l’écrase plus.</span>
        </div>
        {!edition ? <button className="ru-bouton-ligne" type="button" onClick={() => setEdition(true)}>Modifier</button> : null}
      </div>
      {edition ? (
        <section className="ru-carte">
          <div className="ru-carte-tete"><h2>Modifier la société</h2></div>
          <FormulaireSaisie objet="societe" id={Number(s.app_societe_id ?? 3000001)} carnet={donnees.carnet} onGeste={onGeste} onFermer={() => setEdition(false)}
            champs={CHAMPS_SOCIETE.map(([champ, titre]) => ({ champ, titre, valeur: s[champ] ?? null, type: champ === 'carte_validite' ? 'date' : 'texte' }))} />
        </section>
      ) : null}
      <div className="ru-colonnes">
        <div className="ru-principal">
          <section className="ru-carte">
            <div className="ru-carte-tete"><h2>Informations juridiques</h2></div>
            <div className="ru-grille-3">
              <Champ titre="Forme" valeur={s.forme} />
              <Champ titre="SIRET" valeur={s.siret} />
              <Champ titre="Code NAF" valeur={s.naf} />
              <Champ titre="Capital" valeur={s.capital} />
              <Champ titre="RCS" valeur={ligne(s.rcs_ville, s.rcs)} />
              <Champ titre="TVA intracommunautaire" valeur={s.tva} />
              <Champ titre="Siège social" valeur={adresse(s.siege_adresse, s.siege_code_postal, s.siege_ville)} />
              <Champ titre="Contact" valeur={ligne(telephone(s.telephone), s.email)} />
              <Champ titre="Assurance RCP" valeur={ligne(s.assureur_nom, s.rcp_numero ? `contrat ${s.rcp_numero}` : null, adresse(s.assureur_adresse, s.assureur_code_postal, s.assureur_ville))} />
              <Champ titre="Médiateur" valeur={ligne(s.mediateur_nom, adresse(s.mediateur_adresse, s.mediateur_code_postal, s.mediateur_ville))} />
            </div>
          </section>
        </div>
        <aside className="ru-cote">
          <section className="ru-carte ru-bloc">
            <h2>Carte professionnelle</h2>
            <div className="ru-grille-2">
              <Champ titre="Type" valeur={s.carte_type} />
              <Champ titre="Numéro" valeur={s.carte_numero} />
              <Champ titre="Délivrée par" valeur={s.carte_delivree_par} />
              <Champ titre="Détenteur" valeur={s.carte_detenteur} />
              <Champ titre="Maniement de fonds" valeur={s.carte_maniement_fonds} />
              <Champ titre="Valable jusqu’au" valeur={date(validite, true)} />
            </div>
            {rappel ? <span className="ru-mute ru-petit">À renouveler : trois mois avant la fin, le {rappel.toLocaleDateString('fr-FR')}.</span> : null}
          </section>
          <section className="ru-carte ru-bloc">
            <h2>Documents de la société</h2>
            <span>Barème d’honoraires : {s.bareme_url ? 'chez Hektor — à recopier' : 'aucun'}</span>
            <span>Logo : {s.logo_url ? 'chez Hektor — à recopier' : 'aucun'}</span>
          </section>
        </aside>
      </div>
    </>
  )
}
