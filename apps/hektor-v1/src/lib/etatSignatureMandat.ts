// A.2 P8-1 (06/11/2026) -- QUEL DOCUMENT DIT OU EN EST LA SIGNATURE DU MANDAT (cockpit + rubrique Mandat V3).
//
// AVANT : le PREMIER document dont le nom contient « mandat », dans l'ordre de la liste (type puis nom, ordre
// alphabetique : les documents de Hektor, type « document », passent avant ceux de l'app, type « Mandat »), et son
// etat n'etait retenu que s'il portait une procedure ImmoSign ou s'il etait signe. Mesure du 06/11 sur le parc :
// 40 biens lus « rien » alors qu'un etat fiable existait, 21 biens ou le gagnant (attente / signe) dependait de
// l'alphabet, et un mandat Youtrust EN COURS jamais vu (pas de procedure ImmoSign, regle R2).
//
// MAINTENANT : on regarde TOUS les documents du mandat (meme filtre de nom, sans les PDF remplaces) et le PLUS RECENT
// etat fiable l'emporte. Fiable =
//   - un document Youtrust, dans tous ses etats (annule / expire = le PDF est edite, a renvoyer) ;
//   - un document ImmoSign qui porte une procedure (la lecture ImmoSign n'est PAS touchee : on lit ce qu'elle ecrit) ;
//   - un document signe, quel que soit le fournisseur (a la main compris) ;
//   - un PDF fait par l'editeur (photo des signataires), pas encore parti : « edite, a envoyer ».
// Aucun etat fiable -> null, exactement ce que rendait l'ancienne regle dans ce cas (elle ne rendait un etat QUE s'il
// etait fiable) : le repli est donc la regle d'aujourd'hui.

export type DocumentSignable = {
  id?: string | null
  document_name?: string | null
  document_type?: string | null
  created_at?: string | null
  metadata_json?: unknown
}

type Signature = {
  provider?: string | null
  status?: string | null
  procedure_id?: number | string | null
  signed_at?: string | null
  signed_at_iso?: string | null
  sent_at?: string | null
  cancelled_at_iso?: string | null
  expired_at_iso?: string | null
  source?: string | null
}

export type EtatSignature = { status: string; date: number; documentId: string | null; fournisseur: 'youtrust' | 'immosign' | 'manuscrite' | 'editeur'; procedure?: number }

// « 06/11/2026 à 07:09 » (forme ImmoSign, heure de Paris) ou « 2026-11-06 » ou ISO -> millisecondes (NaN si illisible).
export function dateDeSignature(texte: string | null | undefined): number {
  const t = String(texte ?? '').trim()
  if (!t) return NaN
  const fr = t.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s*(?:à|a)\s*(\d{1,2})[:h](\d{2}))?/)
  if (fr) return Date.UTC(Number(fr[3]), Number(fr[2]) - 1, Number(fr[1]), Number(fr[4] ?? 0), Number(fr[5] ?? 0))
  const iso = Date.parse(t)
  return Number.isFinite(iso) ? iso : NaN
}

const premiereDate = (...valeurs: Array<string | null | undefined>): number => {
  for (const v of valeurs) {
    const d = dateDeSignature(v)
    if (Number.isFinite(d)) return d
  }
  return 0
}

// L'etat fiable d'UN document, ou null (etat par defaut d'un modele Hektor, « a envoyer » sans procedure, etc.).
export function etatFiableDuDocument(d: DocumentSignable): EtatSignature | null {
  const md = (d.metadata_json ?? {}) as { signature?: Signature | null; signataires_du_pdf?: unknown }
  const sig = md.signature ?? null
  const id = d.id ?? null
  if (sig && sig.provider === 'youtrust') {
    const brut = String(sig.status ?? '')
    // Une demande annulee ou expiree laisse un PDF edite : le cycle repart a « a envoyer ».
    const status = brut === 'cancelled' || brut === 'expired' ? 'to_send' : brut
    if (!status) return null
    return { status, fournisseur: 'youtrust', documentId: id, date: premiereDate(sig.signed_at_iso, sig.signed_at, sig.cancelled_at_iso, sig.expired_at_iso, sig.sent_at, d.created_at) }
  }
  const procedure = sig?.procedure_id != null && String(sig.procedure_id).trim() !== ''
  if (sig && sig.status && (procedure || sig.status === 'signed')) {
    const numero = procedure ? Number(sig.procedure_id) : NaN
    return { status: String(sig.status), fournisseur: sig.source === 'manuscrite' ? 'manuscrite' : 'immosign', documentId: id, date: premiereDate(sig.signed_at_iso, sig.signed_at, sig.sent_at, d.created_at),
      ...(Number.isFinite(numero) ? { procedure: numero } : {}) }
  }
  // Un PDF de l'editeur (P1) pas encore parti : il est EDITE, meme si la synchro y a pose l'etat par defaut de Hektor.
  if (md.signataires_du_pdf) return { status: 'to_send', fournisseur: 'editeur', documentId: id, date: premiereDate(d.created_at) }
  return null
}

// Le plus recent etat fiable parmi les documents qui passent le filtre de nom (et ne sont pas remplaces).
export function etatSignatureDuMandat(
  documents: DocumentSignable[],
  match: RegExp,
  exclude: RegExp | undefined,
  estRemplace: (d: DocumentSignable) => boolean,
): EtatSignature | null {
  const etats: EtatSignature[] = []
  for (const d of documents) {
    const name = `${d.document_name ?? ''} ${d.document_type ?? ''}`
    if (exclude && exclude.test(name)) continue
    if (estRemplace(d)) continue
    if (!match.test(name)) continue
    const e = etatFiableDuDocument(d)
    if (e) etats.push(e)
  }
  if (!etats.length) return null
  // ⚠ LE PIEGE MESURE LE 06/11 (rejeu sur 630 biens) : pour ImmoSign, `sent_at` n'est PAS la date d'envoi -- c'est le
  //   jour ou l'app a VU l'attente la premiere fois (18/08, 15/10 : jours de grande relecture). Sur 62806, 59502, 63066,
  //   une procedure « en attente » plus ANCIENNE que la procedure signee (numero 809 < 843, 372 < 386, 851 < 853 :
  //   une procedure abandonnee) aurait ecrase le signe. Entre procedures ImmoSign, c'est donc le NUMERO qui dit la plus
  //   recente : une attente dont le numero est inferieur a celui d'une procedure signee est perimee, on l'ecarte.
  const dernierSigneImmoSign = Math.max(-Infinity, ...etats.filter((e) => e.fournisseur === 'immosign' && e.status === 'signed' && e.procedure != null).map((e) => e.procedure as number))
  const dateDuDernierSigne = Math.max(0, ...etats.filter((e) => e.fournisseur === 'immosign' && e.status === 'signed' && e.procedure === dernierSigneImmoSign).map((e) => e.date))
  const vivants = etats
    .filter((e) => !(e.fournisseur === 'immosign' && e.status !== 'signed' && e.procedure != null && e.procedure < dernierSigneImmoSign))
    // Et une procedure de numero SUPERIEUR est bien plus recente que ce signe, quelle que soit sa date « vue le ».
    .map((e) => (e.fournisseur === 'immosign' && e.status !== 'signed' && e.procedure != null && e.procedure > dernierSigneImmoSign && e.date <= dateDuDernierSigne
      ? { ...e, date: dateDuDernierSigne + 1 } : e))
  // A date egale (dates manquantes), l'ordre de la liste departage, comme avant.
  return vivants.reduce((meilleur, e) => (e.date > meilleur.date ? e : meilleur), vivants[0])
}
