// A.2 LOT 5, L5-1 -- essai hors ligne de la reception des avis Youtrust, sur LE CODE REEL (logique.ts, joue par Node 24
// qui lit le TypeScript tel quel). Fausse base en memoire ; signatures calculees par node:crypto (un AUTRE code que
// celui de la fonction, qui utilise Web Crypto). N'appelle rien.                                       05/11/2026
//     node supabase/functions/youtrust-webhook/test_logique.mjs   (0 = vert · 1 = un echec · 2 = pas pu mesurer)
import { createHmac } from 'node:crypto'

let L
try { L = await import('./logique.ts') } catch (e) { console.log(`⛔ logique.ts illisible : ${e.message}`); process.exit(2) }
const echecs = []
const controle = (nom, ok, detail) => { console.log(`${ok ? '  OK  ' : 'ECHEC '} ${nom}${ok ? '' : ' -- ' + (detail || '')}`); if (!ok) echecs.push(nom) }

const SECRET = 'a'.repeat(32)
const DEMANDE = { id: 'req-uuid-1', app_dossier_id: 9000005, hektor_annonce_id: '70005' }
const avis = (extra = {}) => ({
  event_id: 'evt-1', event_name: 'signer.done', event_time: '1793880000', subscription_id: 'sub', sandbox: true,
  data: { signature_request: { id: 'yt-sr-1', status: 'ongoing', external_id: 'doc-1', signers: [] }, signer: { id: 'yt-signer-1', status: 'signed' } },
  ...extra,
})
const signer = (octets, secret = SECRET) => `sha256=${createHmac('sha256', secret).update(octets).digest('hex')}`
const octetsDe = (objet) => new TextEncoder().encode(JSON.stringify(objet))

function fausseBase({ demandes = [DEMANDE], enAttente = false, panne = null } = {}) {
  const b = { avis: new Map(), travaux: [], appels: [] }
  b.base = {
    async rangerAvis(l) { b.appels.push('ranger'); if (panne === 'ranger') throw new Error('base indisponible'); if (b.avis.has(l.event_id)) return 'doublon'; b.avis.set(l.event_id, l); return 'nouveau' },
    async trouverDemande(id) { b.appels.push('trouver'); return demandes.find(() => id === 'yt-sr-1') ?? null },
    async travailEnAttente() { b.appels.push('attente'); return enAttente || b.travaux.some((t) => t.status === 'pending') },
    async poserTravail(t) { b.appels.push('poser'); if (panne === 'poser') throw new Error('insertion refusee'); b.travaux.push(t) },
  }
  return b
}
const appeler = (b, objet, { entete, methode = 'POST', brut } = {}) => {
  const corps = brut ?? octetsDe(objet)
  return L.traiterAvis({ methode, corps, entete: entete === undefined ? signer(corps) : entete }, SECRET, b.base)
}

try {
  // 1. Le chemin nominal
  {
    const b = fausseBase()
    const r = await appeler(b, avis())
    const l = b.avis.get('evt-1')
    controle('1. avis signé juste : 200, rangé, UN travail youtrust_sync_signature posé pour la demande',
      r.statut === 200 && r.corps.travail === 'pose' && b.travaux.length === 1 && b.travaux[0].job_type === 'youtrust_sync_signature'
        && b.travaux[0].payload_json.signature_request_id === 'req-uuid-1' && b.travaux[0].app_dossier_id === 9000005 && b.travaux[0].status === 'pending', JSON.stringify(r))
    controle('1. la ligne rangée : numéros Youtrust, sandbox, date de l\'époque Unix, avis entier',
      l && l.provider === 'youtrust' && l.provider_request_id === 'yt-sr-1' && l.provider_signer_id === 'yt-signer-1' && l.sandbox === true
        && l.event_time === new Date(1793880000 * 1000).toISOString() && l.payload.data.signer.status === 'signed', JSON.stringify(l))
  }
  // 2. Les refus
  {
    const b = fausseBase()
    const faux = await appeler(b, avis(), { entete: signer(octetsDe(avis()), 'b'.repeat(32)) })
    const sans = await appeler(b, avis(), { entete: null })
    const corpsModifie = octetsDe(avis({ event_name: 'signature_request.done' }))
    const altere = await appeler(b, null, { brut: corpsModifie, entete: signer(octetsDe(avis())) })
    controle('2. mauvaise clé, en-tête absent, corps modifié après signature : 401, RIEN rangé, rien posé',
      faux.statut === 401 && sans.statut === 401 && altere.statut === 401 && b.appels.length === 0, JSON.stringify([faux.statut, sans.statut, altere.statut, b.appels]))
    const get = await appeler(fausseBase(), avis(), { methode: 'GET' })
    controle('2. autre méthode que POST : 405', get.statut === 405)
    const sansSecret = await L.traiterAvis({ methode: 'POST', corps: octetsDe(avis()), entete: signer(octetsDe(avis())) }, '', fausseBase().base)
    controle('2. secret non posé : 500 (Youtrust renverra), jamais un 200 aveugle', sansSecret.statut === 500)
    const illisible = new TextEncoder().encode('{pas du json')
    const r400 = await appeler(fausseBase(), null, { brut: illisible })
    const sansId = await appeler(fausseBase(), avis({ event_id: '' }))
    controle('2. corps illisible ou sans event_id (mais bien signé) : 400', r400.statut === 400 && sansId.statut === 400)
  }
  // 3. Doublons, désordre, demande inconnue
  {
    const b = fausseBase()
    await appeler(b, avis())
    const r2 = await appeler(b, avis())
    controle('3. le MÊME avis reçu deux fois : une seule ligne, un seul travail en attente', b.avis.size === 1 && b.travaux.length === 1 && r2.corps.rangement === 'doublon' && r2.corps.travail === 'deja_en_attente', JSON.stringify(r2))
    const r3 = await appeler(b, avis({ event_id: 'evt-2', event_name: 'signer.notified' }))
    controle('3. un autre avis de la même demande pendant qu\'un travail attend : rangé, pas de second travail', b.avis.size === 2 && b.travaux.length === 1 && r3.corps.travail === 'deja_en_attente')
  }
  {
    const b = fausseBase({ demandes: [] })
    const r = await appeler(b, avis())
    controle('3. demande inconnue (créée hors de l\'app) : avis gardé, 200, AUCUN travail', r.statut === 200 && b.avis.size === 1 && b.travaux.length === 0 && r.corps.travail === 'demande_inconnue')
    const sansDemande = await appeler(fausseBase(), avis({ event_id: 'evt-9', data: {} }))
    controle('3. avis sans demande (contact.created…) : gardé, 200, aucun travail', sansDemande.statut === 200 && sansDemande.corps.travail === 'sans_demande')
  }
  // 4. Les pannes de base : 500, et le renvoi de Youtrust répare
  {
    const b = fausseBase({ panne: 'ranger' })
    const r = await appeler(b, avis())
    controle('4. la base refuse de ranger : 500 (Youtrust renverra), aucun travail', r.statut === 500 && b.travaux.length === 0)
  }
  {
    const b = fausseBase({ panne: 'poser' })
    const r1 = await appeler(b, avis())
    b.base.poserTravail = async (t) => { b.travaux.push(t) }
    const r2 = await appeler(b, avis())
    controle('4. ⭐ avis rangé mais travail raté (500) : au RENVOI, le doublon est ignoré MAIS le travail est posé',
      r1.statut === 500 && r2.statut === 200 && r2.corps.rangement === 'doublon' && r2.corps.travail === 'pose' && b.travaux.length === 1, JSON.stringify([r1, r2]))
  }
  // 5. TÉMOIN : le contrôle de signature sait dire non (sinon les 401 ne prouveraient rien)
  {
    const corps = octetsDe(avis())
    const juste = await L.signatureValide(corps, signer(corps), SECRET)
    const majuscules = await L.signatureValide(corps, signer(corps).toUpperCase().replace('SHA256=', 'sha256='), SECRET)
    const tronque = await L.signatureValide(corps, signer(corps).slice(0, -1), SECRET)
    controle('5. TÉMOIN : la signature de node:crypto est acceptée (même calcul que Youtrust), hex en majuscules aussi ; tronquée : refusée',
      juste === true && majuscules === true && tronque === false)
  }
  // 6. Le branchement : sans jeton, la bonne en-tête, la bonne table
  {
    const { readFileSync } = await import('node:fs')
    const index = readFileSync(new URL('./index.ts', import.meta.url), 'utf8')
    controle('6. index.ts : en-tête x-yousign-signature-256, corps BRUT (arrayBuffer), tables app_signature_event / app_signature_request / app_console_job, déploiement --no-verify-jwt documenté',
      /headers\.get\('x-yousign-signature-256'\)/.test(index) && /request\.arrayBuffer\(\)/.test(index) && /from\('app_signature_event'\)[\s\S]*onConflict: 'event_id', ignoreDuplicates: true/.test(index)
        && /from\('app_signature_request'\)/.test(index) && /eq\('status', 'pending'\)/.test(index) && /--no-verify-jwt/.test(index))
  }
} catch (e) {
  console.log(`⛔ L'essai n'a pas pu tourner : ${e && e.stack ? e.stack : e}`)
  process.exit(2)
}
console.log(echecs.length ? `\n⛔ ${echecs.length} contrôle(s) en échec.` : '\n✅ Tous les contrôles sont verts.')
process.exit(echecs.length ? 1 : 0)
