// A.2 P8-3 (06/11/2026) -- LE SUIVI PAR SIGNATAIRE D'UNE DEMANDE YOUTRUST, et ses deux gestes (Relancer, Annuler).
// On LIT notre table app_signature_request (le worker la tient a jour a chaque avis Youtrust, youtrust_sync_signature).
// Les regles des gestes sont celles de Youtrust, pour ne poser AUCUN travail qu'il refuserait (un refus = un travail en
// erreur = une alerte du monitoring) :
//   - Relancer : « seulement si la demande est `ongoing` ET le signataire `notified` » (doc. send_reminder) ;
//   - Annuler  : une demande `ongoing` ou `approval` (au-dela, elle est finie : rien a annuler).
// ImmoSign n'est pas concerne : ses documents gardent leurs boutons (procedure_id), a l'identique.

export type SignataireDemande = {
  index?: number | null
  role?: string | null
  nom?: string | null
  prenom?: string | null
  email?: string | null
  status?: string | null
  signed_at?: string | null
  provider_signer_id?: string | null
}

export type DemandeSignature = {
  id: string
  status?: string | null
  signers?: SignataireDemande[] | null
  expiration_at?: string | null
  done_at?: string | null
  canceled_at?: string | null
  expired_at?: string | null
  last_synced_at?: string | null
}

export type Ton = 'signe' | 'attente' | 'pas_son_tour' | 'refus' | 'neutre'

export type LigneSuivi = {
  cle: string
  nom: string
  role: string
  email: string | null
  libelle: string
  ton: Ton
  relancable: boolean
  providerSignerId: string | null
}

export type Suivi = {
  lignes: LigneSuivi[]
  signes: number
  total: number
  enCours: boolean
  annulable: boolean
  resume: string
}

// « 2026-11-06T07:09:12Z » -> « 06/11/2026 à 08:09 » (heure de Paris). Illisible -> null.
export function dateHeureFr(iso: string | null | undefined): string | null {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  const p = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).formatToParts(d)
  const v = (t: string) => p.find((x) => x.type === t)?.value ?? ''
  return `${v('day')}/${v('month')}/${v('year')} à ${v('hour')}:${v('minute')}`
}

const ROLES: Record<string, string> = { mandant: 'Mandant', mandataire: 'Mandataire (négociateur)' }
const DEMANDE_EN_COURS = new Set(['ongoing', 'approval'])

function etapeDuSignataire(s: SignataireDemande, statutDemande: string): { libelle: string; ton: Ton } {
  const st = String(s.status ?? '')
  if (st === 'signed') {
    const quand = dateHeureFr(s.signed_at)
    return { libelle: quand ? `A signé le ${quand}` : 'A signé', ton: 'signe' }
  }
  if (st === 'declined') return { libelle: 'A refusé de signer', ton: 'refus' }
  if (st === 'aborted' || st === 'error') return { libelle: st === 'error' ? 'Erreur chez Youtrust' : 'Arrêté', ton: 'refus' }
  // La demande est finie (annulée, expirée…) : un signataire non signé ne signera plus.
  if (!DEMANDE_EN_COURS.has(statutDemande)) return { libelle: 'N’a pas signé', ton: 'neutre' }
  if (st === 'initiated' || !st) return { libelle: 'Pas encore son tour', ton: 'pas_son_tour' }
  if (st === 'notified') return { libelle: 'Invité par e-mail — n’a pas encore signé', ton: 'attente' }
  // verified / consent_given / processing : il a ouvert le lien et avance.
  return { libelle: 'En train de signer', ton: 'attente' }
}

export function suiviDeLaDemande(demande: DemandeSignature | null | undefined): Suivi {
  const statut = String(demande?.status ?? '')
  const enCours = DEMANDE_EN_COURS.has(statut)
  const signers = Array.isArray(demande?.signers) ? [...demande!.signers!] : []
  signers.sort((a, b) => (Number(a.index ?? 0) - Number(b.index ?? 0)))
  const lignes: LigneSuivi[] = signers.map((s, i) => {
    const e = etapeDuSignataire(s, statut)
    const nom = [s.prenom, s.nom].map((x) => String(x ?? '').trim()).filter(Boolean).join(' ') || `Signataire ${i + 1}`
    const providerSignerId = s.provider_signer_id ? String(s.provider_signer_id) : null
    return {
      cle: providerSignerId ?? `rang-${i}`,
      nom,
      role: ROLES[String(s.role ?? '')] ?? 'Signataire',
      email: s.email ? String(s.email) : null,
      libelle: e.libelle,
      ton: e.ton,
      relancable: statut === 'ongoing' && s.status === 'notified' && Boolean(providerSignerId),
      providerSignerId,
    }
  })
  const signes = lignes.filter((l) => l.ton === 'signe').length
  const total = lignes.length
  let resume: string
  if (statut === 'done') resume = `Signé par tous${demande?.done_at && dateHeureFr(demande.done_at) ? ` — le ${dateHeureFr(demande.done_at)}` : ''}`
  else if (statut === 'canceled') resume = `Signature annulée${dateHeureFr(demande?.canceled_at) ? ` le ${dateHeureFr(demande?.canceled_at)}` : ''}`
  else if (statut === 'expired') resume = `Signature expirée${dateHeureFr(demande?.expired_at) ? ` le ${dateHeureFr(demande?.expired_at)}` : ''} — à renvoyer`
  else if (statut === 'declined') resume = 'Un signataire a refusé : la signature est arrêtée'
  else if (enCours) {
    const fin = dateHeureFr(demande?.expiration_at)
    resume = `${signes} signature${signes > 1 ? 's' : ''} sur ${total}${fin ? ` — le lien expire le ${fin}` : ''}`
  } else resume = 'État de la signature inconnu'
  return { lignes, signes, total, enCours, annulable: enCours, resume }
}
