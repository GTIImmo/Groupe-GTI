// GED morceau 8 (13/11/2026) : essais hors ligne des propositions « remplir ».  node test_ged_remplir.cjs
// ① les propositions (gedRemplir.ts) : une case VIDE et une valeur lue nettement, chacune avec son témoin qui se tait ;
// ② les gardes de l'écriture (App.tsx, ged.ts, RecuManque.tsx) : relire juste avant, jamais par-dessus, jamais une
//   charge vide, la liste des conditions comptée strictement ; ③ le patch : interrupteur posé ÉTEINT.
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
const { propositionsRemplir, caseVide } = charger('src/lib/gedRemplir.ts')
const v = (cle, x, etat = 'lu', rang = 0) => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page: 2, etat, ...x })
const doc = (nom, typeCode, valeurs, id = 'L-' + nom) => ({ nom, lecture: { id, typeCode, etat: 'lu', luLe: null, valeurs } })
const FICHE = { statut: 'Actif', numeroMandat: '18836', typeBien: '2', copropriete: true, anneeConstruction: 1960, assainissement: null, dpeConso: null, dpeGes: null, dpeNonConcerne: false, diffusable: true, dpeDate: null, nbLots: null, charges: null, prixAncien: null, prixNouveau: null, prixChangeLe: null, mandatDebut: null, mandatFin: null, quotePart: null, erpDate: null, chargeRegistre: undefined }
const P = (docs, opts = {}) => propositionsRemplir({ ...FICHE, ...(opts.fiche || {}) }, docs, opts.affaires ?? [], opts.decisions ?? new Set(), opts.conditions ?? new Map())
const cles = (ps) => ps.map((p) => p.cle).sort().join()

console.log('① les propositions, chacune avec son témoin')
voir(['', '0', '0.00', '0000-00-00', '1970-01-01', null].every(caseVide) && !caseVide('210') && !caseVide('2026-09-10'), 'case vide : rien, « 0 », « 0000-00-00 », la date zéro ; pas une vraie valeur')
const dpe = doc('DPE.pdf', 'diag.dpe', [v('conso_ep', { valeur_num: 210.4 }), v('emissions', { valeur_num: 45 }), v('date_etablissement', { valeur_date: '2026-02-03' })])
const p1 = P([dpe])
voir(cles(p1) === 'P1.dpe_cons,P1.dpe_date,P1.dpe_ges' && p1.find((p) => p.cle === 'P1.dpe_cons').valeur === '210' && p1[0].source === 'DPE.pdf, page 2' && p1[0].lectureId === 'L-DPE.pdf', 'P1 : trois cases vides du DPE, valeur arrondie, la page et la lecture d\'origine')
voir(P([dpe], { fiche: { dpeConso: 180, dpeGes: 30, dpeDate: '2025-01-01' } }).length === 0, 'TÉMOIN P1 : la fiche porte déjà le DPE -> rien (jamais par-dessus)')
voir(cles(P([dpe], { fiche: { dpeConso: 180, dpeGes: 30, dpeDate: '0000-00-00' } })) === 'P1.dpe_date', 'P1 : une date « 0000-00-00 » de Hektor est une case vide')
voir(P([doc('DPE.pdf', 'diag.dpe', [v('conso_ep', { valeur_num: 210 }, 'incertain')])]).length === 0, 'TÉMOIN P1 : une valeur lue « incertaine » ne se propose pas')
const erp = doc('ERP.pdf', 'diag.erp', [v('date_etablissement', { valeur_date: '2026-09-02' })])
voir(cles(P([erp])) === 'P1.diag_risques_nat_tech_date' && P([erp], { fiche: { erpDate: '2026-01-01' } }).length === 0, 'P1 : la date de l\'état des risques ; témoin : déjà remplie -> rien')
const carnet = doc('Fiche synthetique.pdf', 'copro.carnet', [v('sous_type', { valeur: 'fiche_synthetique' }), v('nb_lots_total', { valeur_num: 48 })])
const appel = doc('Appel.pdf', 'copro.appel_fonds', [v('provision_budget', { valeur_num: 300 }), v('periode', { valeur: 'trimestre' })])
const p2 = P([carnet, appel])
voir(cles(p2) === 'P2.copropriete_nb_lot,P2.copropriete_quote_part' && p2.find((p) => p.cle === 'P2.copropriete_quote_part').valeur === '1200', 'P2 : nombre de lots et quote-part annuelle (300 € par trimestre = 1 200 €)')
voir(P([carnet, appel], { fiche: { copropriete: null } }).length === 0 && P([carnet, appel], { fiche: { copropriete: false } }).length === 0, 'TÉMOIN P2 : un bien NON marqué copropriété -> rien (jamais faire passer la case à OUI)')
voir(P([doc('Appel.pdf', 'copro.appel_fonds', [v('provision_budget', { valeur_num: 300 }), v('periode', { valeur: 'autre' })])]).length === 0, 'TÉMOIN P2 : période inconnue -> rien')
const mandat = (charge, numero = '18836') => doc('Mandat.pdf', 'mandat.vente', [v('numero_mandat', { valeur: numero }), v('charge_honoraires', { valeur: charge })])
voir(cles(P([mandat('acquereur')], { fiche: { chargeRegistre: null } })) === 'P3.charge_honoraires', 'P3 : la charge lue, registre lu et vide')
voir(P([mandat('acquereur')], { fiche: { chargeRegistre: undefined } }).length === 0 && P([mandat('acquereur')], { fiche: { chargeRegistre: 'vendeur' } }).length === 0, 'TÉMOIN P3 : registre pas lu (undefined) ou déjà rempli -> rien')
voir(P([mandat('les_deux')], { fiche: { chargeRegistre: null } }).length === 0 && P([mandat('acquereur', '17000')], { fiche: { chargeRegistre: null } }).length === 0, 'TÉMOIN P3 : « les deux » ou un autre mandat -> rien')
const cpv = doc('Compromis.pdf', 'transaction.avant_contrat', [v('condition_pret', { valeur: 'oui' }), v('date_limite_pret', { valeur_date: '2026-12-01' }), v('date_signature', { valeur_date: '2026-10-15' }), v('prix', { valeur_num: 185000 })])
const reg = [{ kind: 'compromis', state: 'active', date: '2026-10-15', dateActe: null, id: 77, montant: 185000, acquereurs: [] }]
const p4 = P([cpv], { affaires: reg, conditions: new Map([[77, 0]]) })
voir(cles(p4) === 'P4.condition_credit' && p4[0].affaireId === 77 && p4[0].valeur === '2026-12-01', 'P4 : la condition « Obtention Crédit » sur LA transaction, liste vide')
voir(P([cpv], { affaires: reg, conditions: new Map([[77, 2]]) }).length === 0 && P([cpv], { affaires: reg, conditions: new Map() }).length === 0, 'TÉMOIN P4 : la liste a déjà 2 conditions, ou son compte est inconnu -> rien')
voir(P([cpv], { affaires: [...reg, { ...reg[0], id: 78 }], conditions: new Map([[77, 0], [78, 0]]) }).length === 0, 'TÉMOIN P4 : deux compromis que rien ne départage -> rien (jamais la mauvaise transaction)')
// lot 10a (17/11) : la date d'acte prévue (la réitération lue) et le séquestre, CHEZ NOUS, sur LA transaction du compromis
const cpv10 = doc('Compromis.pdf', 'transaction.avant_contrat', [v('date_signature', { valeur_date: '2026-10-15' }), v('prix', { valeur_num: 185000 }), v('date_reiteration', { valeur_date: '2027-01-15' }), v('sequestre', { valeur_num: 9250 })])
const reg10 = (x = {}) => [{ kind: 'compromis', state: 'active', date: '2026-10-15', dateActe: null, id: 77, montant: 185000, acquereurs: [], sequestre: null, carnetLu: true, ...x }]
const p10 = P([cpv10], { affaires: reg10() })
voir(cles(p10) === 'P4.date_acte,P4.sequestre' && p10.every((p) => p.geste === 'affaire' && p.affaireId === 77) && p10.find((p) => p.cle === 'P4.date_acte').valeur === '2027-01-15' && p10.find((p) => p.cle === 'P4.sequestre').valeur === '9250',
  '10a : date d\'acte et séquestre vides -> deux propositions « transaction », sur LA transaction, valeurs telles que lues')
voir(P([cpv10], { affaires: reg10({ dateActe: '2027-02-01', sequestre: 9250 }) }).length === 0 && cles(P([cpv10], { affaires: reg10({ dateActe: '0000-00-00' }) })) === 'P4.date_acte,P4.sequestre',
  'TÉMOIN 10a : déjà remplies -> rien (jamais par-dessus) ; « 0000-00-00 » est vide')
voir(P([cpv10], { affaires: reg10({ carnetLu: false }) }).length === 0 && P([cpv10], { affaires: reg10({ carnetLu: undefined }) }).length === 0,
  'TÉMOIN 10a : le carnet de l\'app n\'a pas été lu sans erreur -> rien (une case remplie chez nous paraîtrait vide)')
voir(P([cpv10], { affaires: reg10({ state: 'cancelled' }) }).length === 0 && P([cpv10], { affaires: [...reg10(), ...reg10({ id: 78 })] }).length === 0,
  'TÉMOIN 10a : transaction annulée, ou deux que rien ne départage -> rien')
voir(!cles(P([cpv10], { affaires: reg10({ date: null }) })).includes('date_signature'), 'TÉMOIN 10a : la date de SIGNATURE ne se remplit jamais (un compromis sans date est souvent non signé)')
// lot 10b (17/11) : TOUTES les conditions suspensives lues (fiche v2), d'un clic, si la liste de la transaction est vide
const cv = (n, d, r) => [v('conditions.nature', { valeur: n }, 'lu', r), ...(d ? [v('conditions.date_limite', { valeur_date: d }, 'lu', r)] : [])]
const cpvV2 = (vals) => doc('Compromis.pdf', 'transaction.avant_contrat', [v('date_signature', { valeur_date: '2026-10-15' }), v('prix', { valeur_num: 185000 }), ...vals])
const regC = [{ kind: 'compromis', state: 'active', date: '2026-10-15', dateActe: '2027-01-15', id: 77, montant: 185000, acquereurs: [], sequestre: 9250, carnetLu: true }]
const pC = P([cpvV2([v('condition_pret', { valeur: 'oui' }), ...cv('pret', '2026-12-01', 0), ...cv('preemption', null, 1), ...cv('preemption', '2026-11-30', 2)])], { affaires: regC, conditions: new Map([[77, 0]]) })
voir(cles(pC) === 'P4.conditions' && pC[0].valeur === 'pret@2026-12-01|preemption@2026-11-30' && pC[0].texte.includes('Obtention Crédit jusqu\'au 01/12/2026') && pC[0].texte.includes('Préemption mairie'),
  '10b : prêt + préemption (en double) -> UNE proposition, la liste entière, une nature une fois (avec la date trouvée)')
voir(cles(P([cpvV2([v('condition_pret', { valeur: 'oui' }), ...cv('pret', '2026-12-01', 0)])], { affaires: regC, conditions: new Map([[77, 0]]) })) === 'P4.condition_credit',
  '10b : le prêt SEUL garde la forme d\'avant (P4.condition_credit) -- les décisions déjà prises restent valables')
voir(P([cpvV2([v('condition_pret', { valeur: 'oui' }), ...cv('pret', '2026-12-01', 0), ...cv('preemption', null, 1)])], { affaires: regC, conditions: new Map([[77, 1]]) }).length === 0,
  'TÉMOIN 10b : la transaction a déjà une condition -> rien (le geste remplace toute la liste)')
voir(P([cpvV2([v('condition_pret', { valeur: 'renonciation' }), ...cv('pret', '2026-12-01', 0), ...cv('vente_bien', null, 1)])], { affaires: regC, conditions: new Map([[77, 0]]) })[0]?.valeur === 'vente_bien@',
  '10b : « renonciation » au prêt -> la condition de prêt ne se propose pas')
const { decoderConditions } = charger('src/lib/gedRemplir.ts')
voir(JSON.stringify(decoderConditions('pret@2026-12-01|bidon@|vente_bien@20261|preemption@')) === JSON.stringify([{ nature: 'pret', date: '2026-12-01' }, { nature: 'preemption', date: null }]),
  'TÉMOIN 10b : le décodage rejette une nature inconnue et une date mal formée')
voir(P([dpe], { decisions: new Set(['P1.dpe_cons|210', 'P1.dpe_ges|45', 'P1.dpe_date|2026-02-03']) }).length === 0 && cles(P([dpe], { decisions: new Set(['P1.dpe_cons|199']) })).includes('P1.dpe_cons'), 'une décision prise ne revient pas ; une AUTRE valeur lue, si')

console.log('② les gardes de l\'écriture')
const app = fs.readFileSync(path.join(__dirname, 'src/App.tsx'), 'utf8')
const fn = app.slice(app.indexOf('const remplirDepuisDocument = async'), app.indexOf('return `Enregistré : ${p.texte}.`\n  }\n', app.indexOf('const remplirDepuisDocument')) + 60)
const avant = (a, b) => fn.indexOf(a) >= 0 && fn.indexOf(b) > fn.indexOf(a)
voir(avant('await loadDossierDetail(dossier.app_dossier_id', 'await editAnnonceOptimistic(') && avant('if (!caseVide(actuelle)) return refus(', 'await editAnnonceOptimistic('), 'fiche : relue FRAÎCHE juste avant ; pleine -> rien écrit, la décision dit « echec »')
voir(/if \(p\.champ\.startsWith\('copropriete_'\) && !\/oui\/i\.test/.test(fn), 'copropriété : seulement si le bien est ENCORE marqué copropriété')
voir(avant('loadRegisterCycleAffaires(', 'await ecrireMandatCharge(') && /if \(!numero \|\| !ligne\) return refus/.test(fn) && /charge: p\.valeur === 'vendeur' \? 'mandant' : 'acquereur'/.test(fn), 'charge : la ligne du registre relue (sans elle, rien) ; jamais une charge vide')
voir(avant('await compterConditionsStrict([id])', 'await ecrireAffaireConditions(') && /if \(compte !== 0\) return refus/.test(fn), 'condition : la liste comptée STRICTEMENT juste avant ; non vide ou inconnue -> rien')
voir(avant('await editAnnonceOptimistic(', "await garder('remplie'"), 'la décision « remplie » est gardée APRÈS le geste réussi')
const fnAff = fn.slice(fn.indexOf("if (p.geste === 'affaire') {"), fn.indexOf('// condition : la liste doit être VIDE'))
const avAff = (a, b) => fnAff.indexOf(a) >= 0 && fnAff.indexOf(b) > fnAff.indexOf(a)
voir(avAff('await loadAffairesForDossier(', 'await editAffaireOptimistic(') && avAff('await lireCarnetAffairesStrict([idAffaire])', 'await editAffaireOptimistic(') && avAff('if (!caseVide(actuelle)) return refus(', 'await editAffaireOptimistic('),
  '10a : la transaction ET son carnet relus (strictement) juste avant ; case pleine -> rien écrit')
voir(/\['refused', 'cancelled'\]\.includes/.test(fnAff) && /if \(!\['date_acte', 'sequestre'\]\.includes\(p\.champ\)\) return refus/.test(fnAff) && /if \(!res\.ok \|\| res\.champs_retenus !== 1\) return refus/.test(fnAff),
  '10a : transaction close, champ inconnu, correction non retenue -> refus écrit')
voir(/const voulues = p\.cle === 'P4\.conditions' \? decoderConditions\(p\.valeur\) : \[\{ nature: 'pret' as const, date: p\.valeur \}\]/.test(fn) && /if \(!voulues\.length\) return refus\('liste_illisible'/.test(fn)
  && avant('await compterConditionsStrict([id])', 'const voulues =') && avant('const lignesConditions =', 'await ecrireAffaireConditions(id, lignesConditions)'),
  '10b : la liste lue est décodée APRÈS le compte strict (vide exigé) ; illisible -> rien écrit ; le prêt seul comme avant')
voir(!/createChangeAnnonceStatus|app_modifier_affaire_optimistic|modifierAffaireId/.test(fnAff) && /chez nous ; Hektor n'est pas prévenu/.test(fnAff),
  'TÉMOIN 10a : CHEZ NOUS seulement (décision du 17/11) -- aucun travail vers Hektor')
const ged = fs.readFileSync(path.join(__dirname, 'src/lib/ged.ts'), 'utf8')
const strict = ged.slice(ged.indexOf('export async function compterConditionsStrict'))
voir(/if \(error\) throw new Error\(error\.message\)/.test(strict.slice(0, 900)) && /if \(error\) return null/.test(ged.slice(ged.indexOf('export async function loadGedDecisions'), ged.indexOf('export async function gedDecider'))), 'lectures : les conditions LÈVENT sur erreur ; les décisions rendent null (rien ne se repropose)')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
voir(/if \(!remplir \|\| !peutRemplir \|\| !decisions \|\| !conditions \|\| affaires === null\) return \[\]/.test(rm) && !/\[remplir, onRemplir/.test(rm), 'écran : une lecture ratée -> aucune proposition ; les lectures ne se relancent pas à chaque rendu')
voir(!/tout remplir/i.test(rm) && (rm.match(/'Remplir la fiche'/g) || []).length === 1, 'un clic par proposition : un seul bouton, pas de « tout remplir »')
voir(!/TAXE_FONCIERE|numero_mandat'|mandat_date|PRIXNETVENDEUR/.test(fs.readFileSync(path.join(__dirname, 'src/lib/gedRemplir.ts'), 'utf8').replace(/numero_mandat'\), faits\.numeroMandat/g, '')), 'jamais la taxe foncière, ni un champ du mandat')

console.log('③ le patch')
const patch = fs.readFileSync(path.join(__dirname, '../../supabase/patch_ged_m8_remplir_2026-11-13.sql'), 'utf8')
voir(/\('ged_remplir', 'off'/.test(patch) && /security definer/.test(patch) && /auth\.uid\(\)\)\s*returning id/.test(patch) && /revoke all on table public\.app_ged_decision from public, anon, authenticated/.test(patch), 'interrupteur posé ÉTEINT ; porte SECURITY DEFINER ; l\'auteur est l\'appelant ; table fermée en écriture')
voir(/decision in \('remplie', 'ignoree', 'echec'\)/.test(patch) && !/update public\.app_ged_decision|delete from public\.app_ged_decision/.test(patch), 'trois décisions possibles ; la table est un journal (ni mise à jour ni effacement)')

console.log('④ habillage H3 (16/11) : la carte, la ligne repliée, « La fiche du bien »')
const rmH3 = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
const agirH3 = rmH3.slice(rmH3.indexOf('const agir = async'), rmH3.indexOf('function envoler'))
voir(/const message = await onRemplir\(p\)/.test(agirH3) && /await gedDecider\(\{ hektorAnnonceId, lectureId: p\.lectureId, cle: p\.cle, champ: p\.champ, valeur: p\.valeur, decision: 'ignoree' \}\)/.test(agirH3),
  'H3 : le geste et la décision « ignorée » passent par les MÊMES portes qu\'avant (rien de neuf n\'écrit)')
voir(/const ecrit = \/\^\(Envoyé\|Enregistré\)\/\.test\(message\)/.test(agirH3) && /if \(ecrit && p\.geste === 'fiche'\) \{ setApercu\(null\); [^\n]*envoler\(p, depart\)/.test(agirH3) && (agirH3.match(/envoler\(/g) || []).length === 1
  && /return `Envoyé : \$\{p\.texte\}/.test(app) && /return `Enregistré : \$\{p\.texte\}/.test(app) && /return `Rien écrit : \$\{texte\}`/.test(app),
  'H3 : une case ne s\'allume que si le geste a ÉCRIT (« Envoyé » / « Enregistré ») ; un « Rien écrit » se replie sans rien allumer')
const casesH3 = rmH3.slice(rmH3.indexOf('const CASES_FICHE'), rmH3.indexOf('// Un montant du registre'))
voir(casesH3.length > 200 && !/load|supabase|rpc|fetch/i.test(casesH3) && !/load|supabase|rpc|fetch/i.test(rmH3.slice(rmH3.indexOf('const casesFiche'), rmH3.indexOf('const ficheVisible'))),
  'H3 : « La fiche du bien » ne lit RIEN de neuf : les faits de la fiche, et ce qu\'on vient d\'y écrire')
voir(/window\.matchMedia\?\.\('\(prefers-reduced-motion: reduce\)'\)\.matches\) return/.test(rmH3), 'H3 : moins de mouvement demandé -> pas de vol, la case s\'allume seulement')
voir(!/tout remplir/i.test(rmH3) && !/absent/i.test(rmH3.replace(/^\/\/.*$/gm, '')), 'TÉMOIN : toujours un clic par proposition, et jamais « absent »')
const voirH3 = rmH3.slice(rmH3.indexOf('async function voirDocument'), rmH3.indexOf('// H3 : les cases de « La fiche du bien »'))
voir(/await createConsoleDocumentSignedUrl\(d\)/.test(voirH3) && /apercuPremierePage\(fichier, 720, page \?\? 1\)/.test(voirH3),
  'H3 : « Voir le document » passe par l\'ouverture d\'AUJOURD\'HUI (décision du 16/11 : « comme Ouvrir ») et dessine la page lue')
voir(!/lireParIa|classerParIa|preparerLecture|backendApiBaseUrl|\.rpc\(|\.insert\(|\.update\(/.test(voirH3),
  'TÉMOIN : l\'aperçu n\'envoie le document ni à l\'IA ni au serveur de lecture, et n\'écrit rien d\'autre que ce qu\'« Ouvrir » écrit')
voir(/lectures\.get\(d\.id\)\?\.id === p\.lectureId/.test(rmH3) && /\{documentDe\(p\) \? \(/.test(rmH3), 'H3 : le bouton n\'existe que si le document de la lecture est retrouvé')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
