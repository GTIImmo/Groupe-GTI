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
voir(/loadContactsEtatCivil\(\[id\], 'app'\)/.test(geste) && geste.indexOf('loadContactsEtatCivil') < geste.indexOf('editContactOptimistic'), 'il RELIT le contact avant d\'écrire, par NOTRE numéro')
voir(/case_deja_remplie/.test(geste) && /caseVide\(actuelle\)/.test(geste), 'jamais par-dessus : la case relue doit être vide')
voir(/nature_fiche !== 'personne_seule'/.test(geste) && /couple_role/.test(geste) && /archive === true/.test(geste), 'personne seule active, relue')
voir(/lastName: nom/.test(geste) && /contact_sans_nom/.test(geste), 'le nom ACTUEL est joint (le worker l\'exige)')
voir(/sendRgpdEmail: false/.test(geste), 'l\'e-mail RGPD est coupé expressément (D-4)')
const appel = (geste.match(/await editContactOptimistic\(\{.*/) || [''])[0]
voir(appel.length > 0 && !/\b(address|postalCode|city|email|phone|phoneSecondary|firstName|civility|comments)\b/.test(appel), 'TÉMOIN : rien d\'autre n\'est envoyé (ni coordonnées, ni prénom, ni civilité)')
voir(/garder\('remplie'/.test(geste) && geste.indexOf('editContactOptimistic') < geste.indexOf("garder('remplie'"), 'la décision est gardée APRÈS l\'écriture')
const recu = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
voir(/etatCivil \? contactsDuBien/.test(recu) && !/propositionsContact\(/.test(recu) && /bilansPersonnes\(contactsEtatCivil, personnesDuBien, docsLus, new Date\(\)\)/.test(recu),
  'lot F : les cartes C1-C3 sont RETIRÉES au profit des fenêtres « Ce que dit… » ; une lecture ratée (null) -> aucune fenêtre contact')
const ged = fs.readFileSync(path.join(__dirname, 'src/lib/ged.ts'), 'utf8')
voir(/from\('app_contacts_current'\)/.test(ged) && /if \(error\) return null/.test(ged.slice(ged.indexOf('loadContactsEtatCivil'))), 'la relecture passe par la vue des contacts (même périmètre), et une erreur rend null')
voir(/loadContactsEtatCivil\(idsContacts \? idsContacts\.split\(','\) : \[\], 'hektor'\)/.test(recu), 'l\'écran lit par le numéro HEKTOR des contacts du bien (le pont)')
voir(/contactId: String\(r\.hektor_contact_id\)/.test(recu) && !/contactId: c\.id/.test(recu), 'TÉMOIN : la proposition porte NOTRE numéro, jamais celui de l\'écran')

console.log('⑥ lot F (18/11) : « Ce que dit la pièce d\'identité / la fiche de renseignements »')
const { bilansPersonnes, contactDeLaLigne } = charger('src/lib/gedRemplirContact.ts')
const LB = (b, cle) => b && b.lignes.find((l) => l.cle === cle)
const f0 = bilansPersonnes([C()], DUBIEN, [cni('ESSAI 8A C1', 'Mandant Jean', '1970-05-04', 'Lyon')], AUJ)
voir(f0.length === 1 && f0[0].genre === 'identite' && LB(f0[0], 'P.birth_date.20000009').etat === 'ajouter' && LB(f0[0], 'P.birth_date.20000009').valeur === '1970-05-04'
  && LB(f0[0], 'P.birth_date.20000009').champFiche === 'birth_date' && LB(f0[0], 'P.birth_place.20000009').valeur === 'Lyon' && LB(f0[0], 'P.birth_date.20000009').temoin === null,
  'une CNI sur une fiche VIDE : sa fenêtre, date et lieu à ajouter, dans les cases du contact, témoin « vide »')
const f1 = bilansPersonnes([C({ naissance: '1971-05-04', lieu: 'LYON' })], DUBIEN, [cni('ESSAI 8A C1', 'Mandant', '1970-05-04', 'Lyon')], AUJ)[0]
voir(LB(f1, 'P.birth_date.20000009').etat === 'trancher' && LB(f1, 'P.birth_date.20000009').temoin === '1971-05-04' && LB(f1, 'P.birth_date.20000009').transaction === '04/05/1971' && LB(f1, 'P.birth_place.20000009').etat === 'accord',
  '⭐ une date REMPLIE qui diffère -> à trancher (on n\'écrit par-dessus que sur le choix) ; le lieu « LYON » = « Lyon » -> d\'accord')
const f2 = bilansPersonnes([C()], DUBIEN, [fiche('ESSAI 8A C1', 'Mandant', '1970-05-04', 'Lyon', 'marie')], AUJ)[0]
voir(f2.genre === 'renseignements' && LB(f2, 'P.marital_status.20000009').valeur === 'married' && LB(f2, 'P.marital_status.20000009').lu === 'marié(e)' && LB(f2, 'P.birth_date.20000009'),
  'la fiche de renseignements : la situation de famille (code Hektor) et, sans pièce d\'identité, la naissance')
const f3 = bilansPersonnes([C()], DUBIEN, [cni('ESSAI 8A C1', 'Mandant', '1970-05-04', 'Lyon'), fiche('ESSAI 8A C1', 'Mandant', '1970-05-04', 'Lyon', 'marie')], AUJ)
voir(f3.length === 2 && !LB(f3[1], 'P.birth_date.20000009') && !LB(f3[1], 'P.birth_place.20000009') && LB(f3[1], 'P.marital_status.20000009') && LB(f3[0], 'P.birth_date.20000009'),
  '⛔ un seul chemin par case : avec une CNI lue, la fiche de renseignements ne parle plus de la naissance (la situation, seulement)')
const deuxCni = [doc('CNI 2.pdf', 'justif.identite', [v('pieces.nom', { valeur: 'ESSAI 8A C1' }), v('pieces.prenoms', { valeur: 'Mandant' }), v('pieces.date_naissance', { valeur_date: '1970-05-04' })], 'L-2'),
  cni('ESSAI 8A C1', 'Mandant', '1970-05-04', 'Lyon')]
deuxCni[0].lecture.luLe = '2026-11-18T10:00:00Z'; deuxCni[1].lecture.luLe = '2026-11-18T09:00:00Z'
const f4 = bilansPersonnes([C()], DUBIEN, deuxCni, AUJ)
voir(f4.length === 1 && f4[0].nom === 'CNI 2.pdf', 'deux pièces d\'identité de la même personne : la plus récemment lue parle, une seule fenêtre')
deuxCni[1] = cni('ESSAI 8A C1', 'Mandant', '1969-01-01', 'Lyon'); deuxCni[1].lecture.luLe = '2026-11-18T09:00:00Z'
voir(bilansPersonnes([C()], DUBIEN, deuxCni, AUJ).length === 0, '⛔ TÉMOIN : deux pièces qui se CONTREDISENT sur la date -> aucune ne parle')
voir(bilansPersonnes([C()], [...DUBIEN, { nom: 'ESSAI 8A C1', prenom: 'Mandant' }], [cni('ESSAI 8A C1', 'Mandant', '1970-05-04', 'Lyon')], AUJ).length === 0, '⛔ deux personnes du bien portent ce nom et ce prénom -> rien')
voir(bilansPersonnes([C({ prenom: 'Autre' })], DUBIEN, [cni('ESSAI 8A C1', 'Mandant', '1970-05-04', 'Lyon')], AUJ).length === 0, 'TÉMOIN : un autre prénom -> rien')
const P1 = (x = {}) => C({ contactId: '20000031', nom: 'COUPLE', prenom: 'Un', personneSeule: false, premiereDuCouple: true, ...x })
const DUCOUPLE = [{ nom: 'COUPLE', prenom: 'Un' }, { nom: 'COUPLE', prenom: 'Deux' }]
const f5 = bilansPersonnes([P1()], DUCOUPLE, [cni('COUPLE', 'Un', '1980-02-02', 'Paris')], AUJ)
voir(f5.length === 1 && LB(f5[0], 'P.birth_date.20000031').etat === 'ajouter', '⭐ la PREMIÈRE personne d\'un couple : sa pièce d\'identité se propose (le worker relit le formulaire de couple)')
voir(bilansPersonnes([P1({ prenom: 'Un et Deux' })], DUCOUPLE, [cni('COUPLE', 'Un', '1980-02-02', 'Paris')], AUJ).length === 0
  && bilansPersonnes([P1({ nom: 'COUPLE/ AUTRE' })], DUCOUPLE, [cni('COUPLE', 'Un', '1980-02-02', 'Paris')], AUJ).length === 0,
  '⛔ une première de couple au prénom ou au nom FUSIONNÉ (« Un et Deux », « COUPLE/ AUTRE ») : rien -- on ne sait pas qui elle est')
voir(bilansPersonnes([C({ personneSeule: false })], DUBIEN, [cni('ESSAI 8A C1', 'Mandant', '1970-05-04', 'Lyon')], AUJ).length === 0, '⛔ TÉMOIN : ni personne seule ni première d\'un couple (le conjoint : lot G) -> rien')
voir(contactDeLaLigne('P.birth_place.20000031') === '20000031' && contactDeLaLigne('F.dpe_cons') === null, 'la ligne dit son contact (NOTRE numéro) ; une ligne de la fiche du bien n\'en a pas')
const debutF = app.indexOf('const appliquerBilanPersonne')
const ecr = debutF >= 0 ? app.slice(debutF, app.indexOf('const appliquerBilan = ', debutF)) : ''
voir(/loadContactsEtatCivil\(\[id\], 'app'\)/.test(ecr) && ecr.indexOf('loadContactsEtatCivil') < ecr.indexOf('editContactOptimistic') && /\['personne_seule', 'couple'\]/.test(ecr) && /!relu\.couple_role/.test(ecr),
  'l\'écriture RELIT chaque contact : actif, personne seule ou première d\'un couple (jamais un conjoint)')
voir(/case_changee/.test(ecr) && /l\.temoin == null/.test(ecr) && /lastName: nom/.test(ecr) && /sendRgpdEmail: false/.test(ecr) && (ecr.match(/await editContactOptimistic\(/g) || []).length === 2
  && /if \(principaleId && ecrites\.length\) \{[\s\S]*?await editContactOptimistic\([\s\S]*?continue\n\s*\}\n\s*if \(ecrites\.length\) \{/.test(ecr),
  'témoin : une case changée depuis l\'ouverture n\'est pas écrite ; le nom actuel joint ; RGPD coupé ; UN geste par contact')
const appelF = (ecr.match(/await editContactOptimistic\(\{.*/) || [''])[0]
voir(appelF.length > 0 && !/\b(address|postalCode|city|email|phone|firstName|civility|comments)\b/.test(appelF), 'TÉMOIN : rien d\'autre n\'est envoyé (ni coordonnées, ni prénom, ni civilité)')
voir(/if \(estGenrePersonne\(b\.genre\)\) return appliquerBilanPersonne\(b, choix\)\s*\n\s*if \(estGenreFiche\(b\.genre\)\)/.test(app), 'l\'aiguillage : les pièces des personnes AVANT la fiche du bien (estGenreFiche les compte aussi)')
voir(/c\.members\.map\(\(m\) => \(\{ id: String\(m\.sourceId/.test(app), 'chaque membre d\'un couple fusionné à l\'écran donne SA fiche')
voir(/const cleBilan = \(b: Bilan\) => `\$\{b\.genre\}\|\$\{b\.lectureId \?\? ''\}`/.test(recu) && !/setBilanOuvert\(b\.genre\)/.test(recu), 'deux pièces d\'identité = deux fenêtres : la fenêtre ouverte se repère par son genre ET sa lecture')

console.log('⑦ lot G (18/11) : la naissance du CONJOINT, par la fiche principale')
const CJ = (x = {}) => C({ contactId: '20000032', nom: 'COUPLE', prenom: 'Deux', personneSeule: false, conjointDe: '20000031', ...x })
const g0 = bilansPersonnes([P1(), CJ()], DUCOUPLE, [cni('COUPLE', 'Deux', '1982-07-14', 'Saint-Étienne', [], 0, 'CNI Deux.pdf')], AUJ)
voir(g0.length === 1 && LB(g0[0], 'P.birth_date.20000032').etat === 'ajouter' && LB(g0[0], 'P.birth_place.20000032').valeur === 'Saint-Étienne' && !LB(g0[0], 'P.birth_date.20000031'),
  '⭐ la pièce du CONJOINT se rattache à SA fiche (pas à la principale) : date et lieu à ajouter')
const g1 = bilansPersonnes([P1(), CJ()], DUCOUPLE, [fiche('COUPLE', 'Deux', '1982-07-14', null, 'marie')], AUJ)
voir(g1.length === 1 && LB(g1[0], 'P.birth_date.20000032') && !LB(g1[0], 'P.marital_status.20000032'), '⛔ jamais la situation de famille d\'un conjoint (une seule par couple, portée par la principale)')
voir(bilansPersonnes([CJ({ conjointDe: '20000032' })], DUCOUPLE, [cni('COUPLE', 'Deux', '1982-07-14', 'Lyon')], AUJ).length === 0 && bilansPersonnes([CJ({ conjointDe: null })], DUCOUPLE, [cni('COUPLE', 'Deux', '1982-07-14', 'Lyon')], AUJ).length === 0,
  'TÉMOIN : un conjoint sans principale (ou qui se pointe lui-même) -> rien')
const debutG = app.indexOf('const appliquerBilanPersonne')
const ecrG = debutG >= 0 ? app.slice(debutG, app.indexOf('const appliquerBilan = ', debutG)) : ''
voir(/relu\.nature_fiche === 'conjoint' && relu\.couple_role === 'conjoint'/.test(ecrG) && /principale\.nature_fiche === 'couple' && !principale\.couple_role/.test(ecrG),
  'l\'écriture relit le conjoint ET sa principale (active, première d\'un couple)')
voir(ecrG.indexOf('await editConjointOptimistic(') > 0 && ecrG.indexOf('await editConjointOptimistic(') < ecrG.indexOf('lastName: nom, personType: \'personne_seule\', sendRgpdEmail: false, ...spouse')
  && /if \(!r\?\.ok\)/.test(ecrG) && /conjoint_refuse/.test(ecrG), 'chez NOUS d\'abord (la fonction du conjoint) ; si elle refuse, RIEN ne part chez Hektor')
const appelG = (ecrG.match(/await editContactOptimistic\(\{ contactId: principaleId.*/) || [''])[0]
voir(appelG.length > 0 && !/\b(address|postalCode|city|email|phone|firstName|civility|comments|spouseFirstName|spouseLastName)\b/.test(appelG), 'TÉMOIN : chez Hektor, la principale n\'envoie QUE la naissance du conjoint (son nom actuel joint)')
const apiSrc = fs.readFileSync(path.join(__dirname, 'src/lib/api.ts'), 'utf8')
voir(/spouse_birth_date: cleanOptionalText\(contact\.spouseBirthDate\)/.test(apiSrc) && /champs\.spouse_birth_date = input\.conjoint\.birthDate/.test(apiSrc), 'le geste porte spouse_birth_date / spouse_birth_place (worker, fonction du conjoint)')
voir(/hektor_couple_contact_id'\)/.test(fs.readFileSync(path.join(__dirname, 'src/lib/ged.ts'), 'utf8')) && /conjointDe: r\.nature_fiche === 'conjoint' && r\.couple_role === 'conjoint'/.test(recu), 'l\'état civil relu porte le lien de couple ; seul un conjoint « nature ET rôle » se propose')

// ⑤ (16/11) LES DEUX NUMÉROS, trouvés par l'épreuve réelle : l'écran donne le numéro HEKTOR (605947), notre clé est le
// nôtre (20000009) ; 0 égaux sur 94 956. La lecture est rejouée contre une fausse base qui garde les deux colonnes.
console.log('⑤ les deux numéros : la lecture de l\'état civil contre une fausse base')
const BASE = [
  { hektor_contact_id: '20000009', hektor_target_id: '605947', nom: 'ESSAI CONTACT', prenom: 'Mandant', birth_date: null, birth_place: null, marital_status: null, nature_fiche: 'personne_seule', couple_role: null, archive: false },
  { hektor_contact_id: '10000101', hektor_target_id: '700001', nom: 'DOUBLE', prenom: 'Un', birth_date: null, birth_place: null, marital_status: null, nature_fiche: 'personne_seule', couple_role: null, archive: false },
  { hektor_contact_id: '10000102', hektor_target_id: '700001', nom: 'DOUBLE', prenom: 'Deux', birth_date: null, birth_place: null, marital_status: null, nature_fiche: 'personne_seule', couple_role: null, archive: false },
]
const colonnesLues = []
let enPanne = false
const fausseBase = { from: (table) => ({ select: () => ({ in: async (col, vals) => {
  colonnesLues.push(`${table}.${col}`)
  return enPanne ? { data: null, error: { message: 'panne' } } : { data: BASE.filter((r) => vals.includes(String(r[col]))), error: null }
} }) }) }
const chargerAvecBase = (f) => {
  const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, f)], bundle: true, write: false, format: 'cjs', platform: 'node', external: ['./supabase', 'react'] }).outputFiles[0].text
  const m = { exports: {} }
  new Function('module', 'exports', 'require', code)(m, m.exports, (n) => (n === './supabase' ? { hasSupabaseEnv: true, supabase: fausseBase } : n === 'react' ? { useEffect() {}, useState: (x) => [x, () => {}] } : require(n)))
  return m.exports
}
const { loadContactsEtatCivil } = chargerAvecBase('src/lib/ged.ts')
;(async () => {
  const parHektor = await loadContactsEtatCivil(['605947'], 'hektor')
  voir(parHektor?.get('605947')?.hektor_contact_id === '20000009' && colonnesLues.at(-1) === 'app_contacts_current.hektor_target_id', 'le numéro HEKTOR de l\'écran retrouve NOTRE fiche (par hektor_target_id)')
  voir((await loadContactsEtatCivil(['605947'], 'app'))?.size === 0, 'TÉMOIN (le défaut du 14/11) : le numéro Hektor cherché comme le nôtre ne trouve RIEN')
  const parApp = await loadContactsEtatCivil(['20000009'], 'app')
  voir(parApp?.get('20000009')?.nom === 'ESSAI CONTACT' && colonnesLues.at(-1) === 'app_contacts_current.hektor_contact_id', 'la relecture au clic, par NOTRE numéro, retrouve la fiche')
  voir((await loadContactsEtatCivil(['20000009'], 'hektor'))?.size === 0, 'TÉMOIN : notre numéro n\'est jamais pris pour un numéro Hektor')
  voir((await loadContactsEtatCivil(['700001', '605947'], 'hektor'))?.has('700001') === false, 'TÉMOIN : un numéro Hektor porté par deux fiches est ambigu -> absent')
  enPanne = true
  voir((await loadContactsEtatCivil(['605947'], 'hektor')) === null, 'TÉMOIN : une lecture en panne rend null (donc aucune proposition)')
  enPanne = false
  console.log(`\n${ok} verts, ${ko} rouges`)
  process.exit(ko ? 1 : 0)
})()
