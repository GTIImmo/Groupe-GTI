// GED morceau 9, lot 9b (13/11/2026) : essais hors ligne des règles des pièces d'identité lues.
//   node test_ged_regles_personnes.cjs
// ① la pièce lue et sa validité ; ② P4 le nom, P5 la validité au jour de la signature, P6 une pièce par personne :
// chaque règle sonne sur son cas ET son témoin se tait ; ③ le branchement (Reçu / Manque, rien n'écrit, la ligne des
// anciens documents reste).
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const charger = (f) => {
  const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, f)], bundle: true, write: false, format: 'cjs', platform: 'node', external: ['./supabase'] }).outputFiles[0].text
  const m = { exports: {} }
  new Function('module', 'exports', 'require', code)(m, m.exports, (n) => (n === './supabase' ? { hasSupabaseEnv: false, supabase: null } : require(n)))
  return m.exports
}
const { reglesPersonnes, piecesLuesDe, finEffective } = charger('src/lib/gedReglesPersonnes.ts')
const v = (cle, x, etat = 'lu', rang = 0) => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page: 1, etat, ...x })
const piece = (rang, x) => [
  v('pieces.nom', { valeur: x.nom }, 'lu', rang), v('pieces.prenoms', { valeur: x.prenoms }, 'lu', rang),
  ...(x.usage ? [v('pieces.nom_usage', { valeur: x.usage }, 'lu', rang)] : []),
  v('pieces.nature', { valeur: x.nature ?? 'cni_nouveau_modele' }, 'lu', rang),
  ...(x.naissance ? [v('pieces.date_naissance', { valeur_date: x.naissance }, 'lu', rang)] : []),
  ...(x.fin ? [v('pieces.date_fin_validite', { valeur_date: x.fin }, x.finEtat ?? 'lu', rang)] : []),
]
const doc = (nom, typeCode, valeurs, etat = 'lu') => ({ nom, lecture: { typeCode, etat, luLe: null, valeurs } })
const cni = (nom, ...pieces) => doc(nom, 'justif.identite', pieces.flatMap((p, i) => piece(i, p)))
const AUJ = new Date(Date.UTC(2026, 10, 13))
const FICHE = { statut: 'Actif', numeroMandat: '18836', typeBien: '1', copropriete: false, anneeConstruction: 1960, assainissement: null, dpeConso: 210, dpeGes: 45, dpeNonConcerne: false, diffusable: true, dpeDate: '2025-01-15', nbLots: null, charges: null, prixAncien: null, prixNouveau: null, prixChangeLe: null, mandatDebut: '2026-03-02', mandatFin: null }
const BIEN = [{ nom: 'FICTIF', prenom: 'Marc' }, { nom: 'FICTIF', prenom: 'Jeanne' }]
const MARC = { nom: 'FICTIF', prenoms: 'Marc, André', naissance: '1960-05-12', fin: '2033-03-03' }
const JEANNE = { nom: 'ESSAI', usage: 'FICTIF', prenoms: 'Jeanne', naissance: '1962-03-03', fin: '2031-01-01' }
const R = (docs, opts = {}) => reglesPersonnes({ ...FICHE, ...(opts.fiche || {}) }, docs, opts.bien ?? BIEN, opts.affaires ?? [], AUJ)
const codes = (al) => al.map((a) => `${a.code}/${a.niveau}`).sort()

console.log('① la pièce lue et sa validité')
const lu = piecesLuesDe('CNI.pdf', cni('CNI.pdf', MARC, JEANNE).lecture)
voir(lu.length === 2 && lu[1].nomUsage === 'FICTIF' && lu[0].fin === '2033-03-03' && lu[0].naissance === '1960-05-12', 'deux pièces dans un fichier : nom, nom d\'usage, naissance, fin de validité')
voir(piecesLuesDe('x', { valeurs: [v('pieces.nom', { valeur: 'X' }, 'incertain')] }).length === 0, 'TÉMOIN : un nom lu avec doute ne fait pas une pièce')
const f1 = finEffective({ nature: 'cni_ancien_modele', naissance: '1960-05-12', fin: '2022-06-13' })
voir(f1.prolongee && f1.date.toISOString().slice(0, 10) === '2027-06-13', 'carte délivrée en 2012 à un majeur : 15 ans (2022 -> 2027)')
const f2 = finEffective({ nature: 'cni_nouveau_modele', naissance: null, fin: '2022-06-13' })
voir(f2.prolongee, 'le « modèle » lu ne décide pas : une fin imprimée de 2014-2023 suffit (naissance inconnue : on prolonge)')
voir(!finEffective({ nature: 'cni_ancien_modele', naissance: '2000-01-01', fin: '2022-06-13' }).prolongee, 'TÉMOIN : délivrée à un mineur (né en 2000, carte de 2012) : pas de prolongation')
voir(!finEffective({ nature: 'passeport', naissance: '1960-05-12', fin: '2022-06-13' }).prolongee, 'TÉMOIN : un passeport garde sa date imprimée')
voir(!finEffective({ nature: 'cni_nouveau_modele', naissance: '1960-05-12', fin: '2033-03-03' }).prolongee && !finEffective({ nature: 'cni_ancien_modele', naissance: '1960-05-12', fin: '2013-12-30' }).prolongee,
  'TÉMOIN : hors de la fenêtre 2014-2023, pas de prolongation (2033, 2013)')
voir(finEffective({ nature: 'cni_nouveau_modele', fin: null }) === null, 'fin non lue : rien à dire')

console.log('② P4 le nom')
voir(codes(R([cni('CNI.pdf', MARC, JEANNE)])).length === 0, 'TÉMOIN : les deux mandants, chacun sa pièce (Jeanne par son nom d\'usage) : silence')
let a = R([cni('CNI X.pdf', { nom: 'DURAND', prenoms: 'Paul', fin: '2033-01-01' }), cni('CNI.pdf', MARC, JEANNE)])
voir(codes(a).join() === 'P4/alerte' && /Paul DURAND n'est ni à un mandant ni à un acquéreur/.test(a[0].texte), 'P4 : la pièce d\'un inconnu sonne (alerte)')
a = R([cni('CNI.pdf', MARC, JEANNE)], { bien: [{ nom: 'FICTIF', prenom: '' }, { nom: 'FICTIF', prenom: 'Jeanne' }] })
voir(codes(a).join() === 'P4/info' && /la fiche « FICTIF »/.test(a[0].texte), 'P4 : une fiche sans prénom -> information « écrit autrement », jamais une alerte')
a = R([cni('CNI acq.pdf', { nom: 'ACHETEUR', prenoms: 'Luc', fin: '2033-01-01' }), cni('CNI.pdf', MARC, JEANNE)], { affaires: [{ kind: 'offre', state: 'accepted', date: '2026-10-01', dateActe: null, acquereurs: [{ nom: 'ACHETEUR', prenom: 'Luc' }] }] })
voir(codes(a).length === 0, 'TÉMOIN : la pièce d\'un acquéreur (offre vivante) n\'est pas une inconnue')
a = R([cni('CNI acq.pdf', { nom: 'ACHETEUR', prenoms: 'Luc', fin: '2033-01-01' }), cni('CNI.pdf', MARC, JEANNE)], { affaires: [{ kind: 'offre', state: 'refused', date: '2026-10-01', dateActe: null, acquereurs: [{ nom: 'ACHETEUR', prenom: 'Luc' }] }] })
voir(codes(a).join() === 'P4/alerte', 'l\'acquéreur d\'une offre REFUSÉE n\'est plus du bien : sa pièce sonne')
voir(R([cni('CNI X.pdf', { nom: 'DURAND', prenoms: 'Paul', fin: '2033-01-01' })], { bien: [] }).length === 0, 'TÉMOIN : fiche sans personne : on se tait (et P6 n\'a personne à attendre)')

console.log('③ P5 la validité au jour de la signature')
const vieux = { ...MARC, nature: 'passeport', fin: '2025-12-31' }
a = R([cni('Passeport.pdf', vieux), cni('CNI J.pdf', JEANNE)])
voir(codes(a).join() === 'P5/alerte' && /^Le passeport de Marc FICTIF était périmé à la signature/.test(a[0].texte),
  'P5 : un passeport fini le 31/12/2025, mandat signé le 02/03/2026 -> alerte')
voir(/périmé à la signature du mandat du 02\/03\/2026/.test(a[0].texte), 'P5 : le texte dit la date de référence (le mandat de la fiche)')
a = R([cni('Passeport.pdf', { ...MARC, nature: 'passeport', fin: '2026-06-30' }), cni('CNI J.pdf', JEANNE)])
voir(codes(a).join() === 'P5/info' && /est périmé depuis le 30\/06\/2026/.test(a[0].texte), 'P5 : valide au mandat, périmée aujourd\'hui, pas encore de compromis -> information « en demander une à jour »')
a = R([cni('Passeport.pdf', { ...MARC, nature: 'passeport', fin: '2026-06-30' }), cni('CNI J.pdf', JEANNE), doc('Mandat.pdf', 'mandat.vente', [v('date_signature', { valeur_date: '2026-08-01' })])])
voir(codes(a).join() === 'P5/alerte' && /signature du mandat du 01\/08\/2026/.test(a[0].texte), 'P5 : la date LUE au mandat passe avant le début de la fiche')
a = R([cni('Passeport.pdf', { ...MARC, nature: 'passeport', fin: '2026-06-30' }), cni('CNI J.pdf', JEANNE)], { affaires: [{ kind: 'compromis', state: 'signed', date: '2026-05-10', dateActe: null, acquereurs: [] }] })
voir(codes(a).length === 0, 'TÉMOIN : valide au compromis du 10/05/2026 : silence (même périmée aujourd\'hui)')
a = R([cni('Passeport.pdf', { ...MARC, nature: 'passeport', fin: '2026-06-30' }), cni('CNI J.pdf', JEANNE)], { affaires: [{ kind: 'compromis', state: 'signed', date: '2026-09-10', dateActe: null, acquereurs: [] }] })
voir(codes(a).join() === 'P5/alerte' && /au compromis du 10\/09\/2026/.test(a[0].texte), 'P5 : périmée au compromis -> alerte')
a = R([cni('CNI.pdf', { ...MARC, nature: 'cni_ancien_modele', fin: '2022-06-13' }), cni('CNI J.pdf', JEANNE)])
voir(codes(a).length === 0, 'TÉMOIN : carte de 2012 « finie » en 2022 mais prolongée à 2027 : silence')
a = R([cni('CNI.pdf', { ...MARC, nature: 'cni_ancien_modele', fin: '2016-01-01' }), cni('CNI J.pdf', JEANNE)])
voir(codes(a).join() === 'P5/alerte' && /^La carte d'identité de Marc FICTIF était périmée/.test(a[0].texte) && /carte prolongée de 5 ans/.test(a[0].texte), 'P5 : même prolongée (2021), périmée au mandat -> alerte, et le texte dit la prolongation')

console.log('④ P6 une pièce par personne')
a = R([cni('CNI M.pdf', MARC)])
voir(codes(a).join() === 'P6/piece' && /Pièce d'identité de Jeanne FICTIF : non trouvée parmi les pièces lues/.test(a[0].texte) && a[0].typeADeposer === 'justif.identite', 'P6 : Jeanne n\'a pas de pièce lue -> à déposer')
voir(R([]).length === 0 && R([doc('CNI.pdf', 'justif.identite', [], 'incomplet')]).length === 0, 'TÉMOIN : aucune pièce LUE sur le bien : P6 se tait (les anciennes cartes ne sont pas lues)')
a = R([cni('CNI.pdf', MARC, JEANNE)], { affaires: [{ kind: 'compromis', state: 'signed', date: '2026-10-10', dateActe: null, acquereurs: [{ nom: 'ACHETEUR', prenom: 'Luc' }] }] })
voir(codes(a).join() === 'P6/piece' && /Luc ACHETEUR/.test(a[0].texte), 'P6 : au compromis, l\'acquéreur aussi')
a = R([cni('CNI.pdf', MARC, JEANNE)], { affaires: [{ kind: 'offre', state: 'accepted', date: '2026-10-10', dateActe: null, acquereurs: [{ nom: 'ACHETEUR', prenom: 'Luc' }] }] })
voir(codes(a).length === 0, 'TÉMOIN : à l\'offre, la pièce de l\'acquéreur n\'est pas encore attendue')
a = R([cni('CNI M.pdf', MARC)], { bien: [{ nom: 'FICTIF', prenom: 'Marc' }, { nom: 'FICTIF', prenom: 'Marc' }] })
voir(codes(a).length === 0, 'TÉMOIN : la même personne deux fois sur la fiche (couple mal rangé) : comptée une fois')

a = R([cni('CNI M.pdf', MARC)], { bien: [{ nom: 'FICTIF', prenom: '' }] })
voir(codes(a).join() === 'P4/info', 'TÉMOIN : une fiche sans prénom est couverte par la pièce au même nom (P6 se tait ; P4 le signale)')

console.log('⑤ le branchement')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
const lib = fs.readFileSync(path.join(__dirname, 'src/lib/gedReglesPersonnes.ts'), 'utf8')
voir(/\.\.\.reglesPersonnes\(faits, docsLus, personnesDuBien, affaires, new Date\(\)\)\]/.test(rm), 'branché dans « Reçu / Manque », avec les autres règles (même tri, même interrupteur)')
voir(!/supabase|\.rpc\(|\.insert\(|\.update\(|fetch\(/.test(lib), 'la règle n\'écrit rien et ne lit rien elle-même (fonction pure)')
voir(!/pieces\.(numero|date_delivrance|autorite_delivrance)/.test(lib), 'la règle ne connaît pas le registre (numéro, délivrance)')
const pieces = fs.readFileSync(path.join(__dirname, 'src/lib/gedPieces.ts'), 'utf8')
voir(/Pièce d\\'identité de chaque mandant/.test(pieces), 'la ligne « Pièce d\'identité de chaque mandant » (anciens documents, par le nom) RESTE')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
