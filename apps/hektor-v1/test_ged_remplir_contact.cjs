// GED morceau 9, lot 9c (14/11/2026) : essais hors ligne du remplissage de la fiche d'un mandant.  node test_ged_remplir_contact.cjs
// ① les propositions (gedRemplirContact.ts) : chacune avec son témoin qui se tait ; ② les gardes de l'écriture (App.tsx,
// RecuManque.tsx, ged.ts) : relire juste avant, jamais par-dessus, le nom joint, l'e-mail RGPD coupé.
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
const { propositionsContact, SITUATION_HEKTOR } = charger('src/lib/gedRemplirContact.ts')
const AUJ = new Date(Date.UTC(2026, 10, 14))
const v = (cle, x, rang = 0, etat = 'lu') => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page: 1, etat, ...x })
const doc = (nom, typeCode, valeurs, id = 'L-' + nom) => ({ nom, lecture: { id, typeCode, etat: 'lu', luLe: null, valeurs } })
const cni = (nom, prenoms, naissance, lieu, extra = [], rang = 0, docNom = 'CNI.pdf') => doc(docNom, 'justif.identite', [
  v('pieces.nom', { valeur: nom }, rang), v('pieces.prenoms', { valeur: prenoms }, rang),
  ...(naissance ? [v('pieces.date_naissance', { valeur_date: naissance }, rang)] : []),
  ...(lieu ? [v('pieces.lieu_naissance', { valeur: lieu }, rang)] : []), ...extra])
const fiche = (nom, prenoms, naissance, lieu, situation, extra = [], docNom = 'Renseignements.pdf') => doc(docNom, 'transaction.renseignements', [
  v('personnes.nom', { valeur: nom }), v('personnes.prenoms', { valeur: prenoms }),
  ...(naissance ? [v('personnes.date_naissance', { valeur_date: naissance })] : []),
  ...(lieu ? [v('personnes.lieu_naissance', { valeur: lieu })] : []),
  ...(situation ? [v('personnes.situation_famille', { valeur: situation })] : []), ...extra])
const C = (x = {}) => ({ contactId: '20000009', nom: 'ESSAI 8A C1', prenom: 'Mandant', personneSeule: true, naissance: null, lieu: null, situation: null, ...x })
const DUBIEN = [{ nom: 'ESSAI 8A C1', prenom: 'Mandant' }]
const P = (docs, opts = {}) => propositionsContact(opts.contacts ?? [C(opts.c)], opts.personnes ?? DUBIEN, docs, opts.decisions ?? new Set(), AUJ)
const cles = (ps) => ps.map((p) => p.cle).sort().join()

console.log('① les propositions, chacune avec son témoin')
const p1 = P([cni('ESSAI 8A C1', 'Mandant Jean', '1958-04-02', 'SAINT-ETIENNE (42)')])
voir(cles(p1) === 'C1.birth_date.20000009,C2.birth_place.20000009', 'C1 + C2 : la pièce d\'identité donne la date et le lieu (pas la situation)')
voir(p1.every((p) => p.geste === 'contact' && p.contactId === '20000009' && p.lectureId === 'L-CNI.pdf' && p.source === 'CNI.pdf, page 1'), 'le geste, le contact visé, la lecture et la page d\'origine')
voir(p1.find((p) => p.champ === 'birth_date').valeur === '1958-04-02' && p1.find((p) => p.champ === 'birth_place').valeur === 'SAINT-ETIENNE (42)', 'les valeurs telles que lues (date AAAA-MM-JJ, que le worker met en JJ-MM-AAAA)')
voir(p1[0].texte === 'Mandant ESSAI 8A C1 : date de naissance 02/04/1958', 'le texte de l\'écran')
voir(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', 'Firminy')], { c: { naissance: '1958-04-02', lieu: 'Firminy' } }).length === 0, 'TÉMOIN : les deux cases déjà remplies -> rien (jamais par-dessus)')
voir(cles(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null)], { c: { naissance: '0000-00-00' } })) === 'C1.birth_date.20000009', 'une date « 0000-00-00 » est une case vide')
voir(P([cni('ESSAI 8A C1', 'Mandant', null, 'Firminy')], { c: { lieu: 'trop chère. Recontacter]]>' } }).length === 0, 'TÉMOIN : un lieu déjà rempli, même pollué -> rien (on ne nettoie pas)')

const r = P([fiche('ESSAI 8A C1', 'Mandant', '1958-04-02', 'Firminy', 'marie')])
voir(cles(r) === 'C1.birth_date.20000009,C2.birth_place.20000009,C3.marital_status.20000009' && r.find((p) => p.champ === 'marital_status').valeur === 'married', 'C3 : la fiche de renseignements donne aussi la situation, en code Hektor (marie -> married)')
voir(r.find((p) => p.champ === 'marital_status').texte === 'Mandant ESSAI 8A C1 : situation de famille « marié(e) »', 'le texte de la situation')
voir(Object.entries({ marie: 'married', celibataire: 'single', veuf: 'widower', divorce: 'divorced', pacse: 'civil_union' }).every(([a, b]) => SITUATION_HEKTOR[a] === b), 'les 5 codes de Hektor')
voir(['separe', 'concubinage', 'autre'].every((s) => !cles(P([fiche('ESSAI 8A C1', 'Mandant', null, null, s)])).includes('C3')), 'TÉMOIN : séparé, concubinage, autre -> pas de code Hektor -> rien')
voir(!cles(P([fiche('ESSAI 8A C1', 'Mandant', null, null, 'marie')], { c: { situation: 'single' } })).includes('C3'), 'TÉMOIN : situation déjà remplie -> rien')

console.log('② la personne : exactement elle, et une seule')
voir(P([cni('ESSAI 8A C2', 'Mandant', '1958-04-02', 'Firminy')]).length === 0, 'TÉMOIN : un autre nom -> rien')
voir(P([cni('ESSAI 8A C1', 'Paul', '1958-04-02', 'Firminy')]).length === 0, 'TÉMOIN : même nom, autre premier prénom -> rien')
voir(P([cni('ESSAI 8A', 'Mandant', '1958-04-02', 'Firminy')]).length === 0, 'TÉMOIN : un nom seulement PROCHE (un mot en moins) -> rien')
voir(P([cni('Essai 8a-C1', 'mandant', '1958-04-02', null)]).length === 1, 'même nom écrit autrement (casse, tiret) -> retrouvé')
voir(P([cni('DUPONT', 'Mandant', '1958-04-02', null, [v('pieces.nom_usage', { valeur: 'ESSAI 8A C1' })])]).length === 1, 'retrouvé par le NOM D\'USAGE de la pièce')
voir(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null)], { personnes: [...DUBIEN, { nom: 'ESSAI 8A C1', prenom: 'Mandant' }] }).length === 0, 'TÉMOIN : deux personnes du bien portent ce nom et ce prénom -> rien')
voir(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null)], { c: { personneSeule: false } }).length === 0, 'TÉMOIN : pas une personne seule (couple) -> rien')
voir(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null)], { c: { contactId: 'r-0-abc' } }).length === 0, 'TÉMOIN : pas de numéro de contact -> rien')
voir(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null)], { c: { prenom: '' } }).length === 0, 'TÉMOIN : la fiche n\'a pas de prénom -> rien')

console.log('③ la valeur : nette, plausible, et une seule')
voir(P([doc('CNI.pdf', 'justif.identite', [v('pieces.nom', { valeur: 'ESSAI 8A C1' }), v('pieces.prenoms', { valeur: 'Mandant' }), v('pieces.date_naissance', { valeur_date: '1958-04-02' }, 0, 'incertain')])]).length === 0, 'TÉMOIN : une date lue « incertaine » -> rien')
voir(P([cni('ESSAI 8A C1', 'Mandant', '2027-01-01', null)]).length === 0 && P([cni('ESSAI 8A C1', 'Mandant', '1850-01-01', null)]).length === 0 && P([cni('ESSAI 8A C1', 'Mandant', '1958-02-30', null)]).length === 0, 'TÉMOIN : une date dans le futur, avant 1900 ou impossible -> rien')
voir(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', 'Firminy'), fiche('ESSAI 8A C1', 'Mandant', '1958-04-03', 'FIRMINY', null)]).map((p) => p.champ).join() === 'birth_place', 'TÉMOIN : deux dates qui se contredisent -> pas de date ; le lieu, dit pareil (casse), reste')
voir(P([cni('ESSAI 8A C1', 'Mandant', null, 'Firminy'), fiche('ESSAI 8A C1', 'Mandant', null, 'Saint-Etienne', null)]).length === 0, 'TÉMOIN : deux lieux qui se contredisent -> rien')
voir(P([fiche('ESSAI 8A C1', 'Mandant', null, null, 'marie'), fiche('ESSAI 8A C1', 'Mandant', null, null, 'separe', [], 'Renseignements 2.pdf')]).length === 0, 'TÉMOIN : « marié » et « séparé » -> rien (une situation sans code compte comme une voix)')
voir(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null), cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null, [], 0, 'CNI verso.pdf')]).length === 1, 'deux pièces qui disent la même date -> une seule proposition')
voir(P([cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null)], { decisions: new Set(['C1.birth_date.20000009|1958-04-02']) }).length === 0, 'TÉMOIN : déjà remplie ou ignorée -> ne revient pas')
voir(P([doc('Avis.pdf', 'fiscal.taxe_fonciere', [v('personnes.nom', { valeur: 'ESSAI 8A C1' }), v('personnes.prenoms', { valeur: 'Mandant' }), v('personnes.date_naissance', { valeur_date: '1958-04-02' })])]).length === 0, 'TÉMOIN : un autre type de document (taxe, titre) ne remplit rien')
voir(P([{ nom: 'CNI.pdf', lecture: { ...cni('ESSAI 8A C1', 'Mandant', '1958-04-02', null).lecture, etat: 'incomplet' } }]).length === 0, 'TÉMOIN : une lecture incomplète ne remplit rien')

console.log('④ les gardes de l\'écriture, dans le code')
const app = fs.readFileSync(path.join(__dirname, 'src/App.tsx'), 'utf8')
const debut = app.indexOf("if (p.geste === 'contact') {")
const geste = debut >= 0 ? app.slice(debut, app.indexOf("if (p.geste === 'charge')", debut)) : ''
voir(geste.length > 0, 'le geste « contact » est dans remplirDepuisDocument, avant le registre')
voir(/loadContactsEtatCivil\(\[id\]\)/.test(geste) && geste.indexOf('loadContactsEtatCivil') < geste.indexOf('editContactOptimistic'), 'il RELIT le contact avant d\'écrire')
voir(/case_deja_remplie/.test(geste) && /caseVide\(actuelle\)/.test(geste), 'jamais par-dessus : la case relue doit être vide')
voir(/nature_fiche !== 'personne_seule'/.test(geste) && /couple_role/.test(geste) && /archive === true/.test(geste), 'personne seule active, relue')
voir(/lastName: nom/.test(geste) && /contact_sans_nom/.test(geste), 'le nom ACTUEL est joint (le worker l\'exige)')
voir(/sendRgpdEmail: false/.test(geste), 'l\'e-mail RGPD est coupé expressément (D-4)')
const appel = (geste.match(/await editContactOptimistic\(\{.*/) || [''])[0]
voir(appel.length > 0 && !/\b(address|postalCode|city|email|phone|phoneSecondary|firstName|civility|comments)\b/.test(appel), 'TÉMOIN : rien d\'autre n\'est envoyé (ni coordonnées, ni prénom, ni civilité)')
voir(/garder\('remplie'/.test(geste) && geste.indexOf('editContactOptimistic') < geste.indexOf("garder('remplie'"), 'la décision est gardée APRÈS l\'écriture')
const recu = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
voir(/etatCivil \? contactsDuBien/.test(recu) && /propositionsContact\(contacts, personnesDuBien, docsLus, decisions/.test(recu), 'l\'écran : une lecture ratée (null) -> aucune proposition contact')
const ged = fs.readFileSync(path.join(__dirname, 'src/lib/ged.ts'), 'utf8')
voir(/from\('app_contacts_current'\)/.test(ged) && /if \(error\) return null/.test(ged.slice(ged.indexOf('loadContactsEtatCivil'))), 'la relecture passe par la vue des contacts (même périmètre), et une erreur rend null')

console.log(`\n${ok} verts, ${ko} rouges`)
process.exit(ko ? 1 : 0)
