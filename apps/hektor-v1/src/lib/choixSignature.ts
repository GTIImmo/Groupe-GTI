// A.2 P8-2 (06/11/2026, D42) -- UN SEUL BOUTON « SIGNATURE », TROIS CHOIX.
//
// Frederic (06/11) : « avant la coupure, un seul bouton signature avec ensuite un choix : signature electronique
// (Youtrust), signature Hektor, signature manuscrite ». Et pour la manuscrite : « uniquement si une procedure est
// lancee, laisser le bouton mais faire un message qui explique a l'utilisateur d'annuler la procedure pour pouvoir
// signer a la main le doc ». La meme regle tient pour les deux autres : un document ne part jamais dans deux
// procedures a la fois.
//
// Ce module dit, pour UN document, quels choix sont possibles et, sinon, POURQUOI (le texte affiche). Il ne fait rien.

export type DocumentPourSignature = {
  document_name?: string | null
  document_type?: string | null
  source?: string | null
  hektor_document_id?: string | null
  envoi_hektor_statut?: string | null
  metadata_json?: unknown
}

export type Choix = { possible: boolean; raison: string | null }
export type ChoixDeSignature = {
  procedureEnCours: 'youtrust' | 'immosign' | null
  signe: boolean
  youtrust: Choix
  hektor: Choix
  manuscrite: Choix
}

type Sig = { provider?: string | null; status?: string | null; procedure_id?: number | string | null }

export const TEXTE_ANNULER_D_ABORD = {
  youtrust: 'Une signature électronique (Youtrust) est en cours sur ce document : annulez-la d’abord (« Annuler la signature », sous la liste des signataires).',
  immosign: 'Une signature Hektor (ImmoSign) est en cours sur ce document : annulez-la d’abord.',
}
export const TEXTE_MANUSCRITE_ANNULER = {
  youtrust: 'Une signature électronique (Youtrust) est en cours : annulez-la d’abord pour pouvoir marquer ce document signé à la main (« Annuler la signature », sous la liste des signataires).',
  immosign: 'Une signature Hektor (ImmoSign) est en cours : annulez-la d’abord (bouton « Annuler ») pour pouvoir marquer ce document signé à la main.',
}

// Le seul cas ou la fenetre propose « Regenerer le mandat » (point 3 de la refonte du 06/11).
export const TEXTE_REGENERER = 'Ce document n’a pas été fait par l’éditeur du mandat : régénérez le mandat pour le signer électroniquement.'

export function choixDeSignature(d: DocumentPourSignature, opts: { youtrustActif: boolean; manuscriteActive: boolean }): ChoixDeSignature {
  const md = (d.metadata_json ?? {}) as { signature?: Sig | null; signataires_du_pdf?: unknown; remplace?: unknown }
  const sig = md.signature ?? null
  const signe = sig?.status === 'signed'
  const procedureImmoSign = sig?.procedure_id != null && String(sig.procedure_id).trim() !== ''
  const procedureEnCours: ChoixDeSignature['procedureEnCours'] = sig?.provider === 'youtrust' && sig.status === 'pending' ? 'youtrust'
    : procedureImmoSign && sig?.status === 'pending' ? 'immosign'
    : null
  const remplace = Boolean(md.remplace)
  const nom = `${d.document_name ?? ''} ${d.document_type ?? ''}`
  const mandatOuAvenant = /mandat|avenant/i.test(nom)

  const ferme = (raison: string): Choix => ({ possible: false, raison })
  const ouvert: Choix = { possible: true, raison: null }

  // Rien ne se signe deux fois, ni un PDF remplace par une regeneration.
  if (signe) {
    const r = 'Ce document est déjà signé.'
    return { procedureEnCours, signe, youtrust: ferme(r), hektor: ferme(r), manuscrite: ferme(r) }
  }
  if (remplace) {
    const r = 'Ce PDF a été remplacé par une version régénérée : signez le nouveau.'
    return { procedureEnCours, signe, youtrust: ferme(r), hektor: ferme(r), manuscrite: ferme(r) }
  }

  // 1. Youtrust : l'interrupteur, un PDF de l'editeur (photo des signataires), aucune procedure en cours.
  const youtrust = procedureEnCours ? ferme(TEXTE_ANNULER_D_ABORD[procedureEnCours])
    : !opts.youtrustActif ? ferme('La signature électronique n’est pas encore activée.')
    : !md.signataires_du_pdf ? ferme(TEXTE_REGENERER)
    : ouvert

  // 2. Hektor : le document doit ETRE chez Hektor (ImmoSign ne signe que ce que Hektor a). Un document ne chez nous n'y
  //    est qu'une fois son depot CONFIRME (`envoye`).
  const neChezNous = d.source === 'app'
  const chezHektor = neChezNous ? d.envoi_hektor_statut === 'envoye' && Boolean(d.hektor_document_id) : true
  const hektor = procedureEnCours ? ferme(TEXTE_ANNULER_D_ABORD[procedureEnCours])
    : chezHektor ? ouvert
    : d.envoi_hektor_statut === 'a_envoyer' ? ferme('Dépôt chez Hektor en cours : la signature Hektor sera possible dès qu’il sera confirmé.')
    : d.envoi_hektor_statut === 'echec' ? ferme('Le dépôt chez Hektor a échoué ; il sera repris à 12:30, la signature Hektor sera possible ensuite.')
    : ferme('Ce document n’est pas chez Hektor : la signature Hektor n’est pas possible.')

  // 3. Manuscrite : mandat ou avenant. Procedure en cours -> le choix RESTE, mais il explique d'annuler d'abord.
  const manuscrite = !opts.manuscriteActive || !mandatOuAvenant ? ferme('La signature manuscrite ne se marque que sur un mandat ou un avenant.')
    : procedureEnCours ? ferme(TEXTE_MANUSCRITE_ANNULER[procedureEnCours])
    : ouvert

  return { procedureEnCours, signe, youtrust, hektor, manuscrite }
}

// ── A.2 (06/11/2026) -- REFONTE DE LA FENETRE « FAIRE SIGNER » (maquette validee par Frederic : points 1 a 4, le 5 abandonne)
// Ce que la fenetre MONTRE : l'identite du document (point 1), ses signataires (point 2), et de quoi proposer « Regenerer
// le mandat » (point 3) et « Voir le suivi » (point 4). Lecture seule de ce qui est deja range sur le document.
export type IdentiteDocument = {
  estMandat: boolean
  titre: string
  meta: string
  depot: { texte: string; ton: 'ok' | 'attente' | 'neutre' }
  signataires: string
  cases: number | null
  progression: string | null
}

type Personne = { civilite?: string | null; prenom?: string | null; nom?: string | null }
const nomDe = (p: Personne) => [p.prenom, p.nom].map((x) => String(x ?? '').trim()).filter(Boolean).join(' ') || String(p.nom ?? '').trim() || '?'
const listeFr = (noms: string[]) => (noms.length <= 1 ? noms.join('') : `${noms.slice(0, -1).join(', ')} et ${noms[noms.length - 1]}`)

// « 2026-11-06T11:40:00Z » -> « 06/11 à 12:40 » (heure de Paris). Illisible -> null.
export function dateCourteFr(iso: string | null | undefined): string | null {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  const p = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).formatToParts(d)
  const v = (k: string) => p.find((x) => x.type === k)?.value ?? ''
  return `${v('day')}/${v('month')} à ${v('hour')}:${v('minute')}`
}

export function identiteDuDocument(
  d: DocumentPourSignature & { created_at?: string | null },
  opts: { numeroMandat?: string | null; negociateur?: string | null } = {},
): IdentiteDocument {
  const md = (d.metadata_json ?? {}) as { cree_le?: string | null; signature?: { progress?: string | null } | null; signataires_du_pdf?: { mandants?: Personne[] } | null }
  const nom = `${d.document_name ?? ''} ${d.document_type ?? ''}`
  const estMandat = /mandat|avenant/i.test(nom)
  const avenant = /avenant/i.test(nom)
  const photo = md.signataires_du_pdf && Array.isArray(md.signataires_du_pdf.mandants) ? md.signataires_du_pdf : null
  const mandants = photo ? (photo.mandants ?? []) : []
  const cases = photo ? mandants.length + 1 : null
  const quand = dateCourteFr(md.cree_le ?? d.created_at ?? null)
  const numero = String(opts.numeroMandat ?? '').trim()

  const titre = photo ? `${avenant ? 'Avenant au mandat' : 'Mandat de vente'}${numero ? ` n° ${numero}` : ''}` : String(d.document_name ?? 'Document')
  const meta = photo
    ? `Généré dans l’app${quand ? ` le ${quand}` : ''}, ${cases} cases de signature`
    : estMandat && d.source !== 'app'
      ? 'Modèle Hektor : l’app ne connaît pas ses signataires'
      : quand ? `Ajouté le ${quand}` : ''

  const s = d.source === 'app' ? d.envoi_hektor_statut : null
  const depot: IdentiteDocument['depot'] = d.source !== 'app' ? { texte: 'Chez Hektor', ton: 'neutre' }
    : s === 'envoye' ? { texte: 'Déposé chez Hektor', ton: 'ok' }
    : s === 'a_envoyer' ? { texte: 'Dépôt chez Hektor en cours', ton: 'attente' }
    : s === 'echec' ? { texte: 'Dépôt chez Hektor en échec', ton: 'attente' }
    : { texte: 'Pas chez Hektor', ton: 'neutre' }

  const nego = String(opts.negociateur ?? '').trim() || 'le négociateur'
  const signataires = photo
    ? `Signent : ${listeFr(mandants.map(nomDe))}, ${mandants.length > 1 ? 'les mandants' : 'le mandant'}, puis ${nego} en dernier.`
    : estMandat ? 'Les signataires de ce modèle se choisissent dans Hektor, ou signent sur papier.' : ''

  const prog = String(md.signature?.progress ?? '').match(/^(\d+)\s*\/\s*(\d+)$/)
  const progression = prog ? `${prog[1]} signature${Number(prog[1]) > 1 ? 's' : ''} sur ${prog[2]}` : null
  return { estMandat, titre, meta, depot, signataires, cases, progression }
}
