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
const P = (docs, opts = {}) => propositionsRemplir({ ...FICHE, ...(opts.fiche || {}) }, docs, opts.decisions ?? new Set())
const cles = (ps) => ps.map((p) => p.cle).sort().join()

console.log('① les propositions, chacune avec son témoin')
voir(['', '0', '0.00', '0000-00-00', '1970-01-01', null].every(caseVide) && !caseVide('210') && !caseVide('2026-09-10'), 'case vide : rien, « 0 », « 0000-00-00 », la date zéro ; pas une vraie valeur')
const dpe = doc('DPE.pdf', 'diag.dpe', [v('conso_ep', { valeur_num: 210.4 }), v('emissions', { valeur_num: 45 }), v('date_etablissement', { valeur_date: '2026-02-03' })])
const p1 = P([dpe])
voir(p1.length === 0, '⛔ lot 3 (18/11) : P1 RETIRÉ -- le DPE passe par la fenêtre « Ce que dit le DPE » (test_ged_bilan ⑦), un seul chemin par case')
voir(P([dpe], { fiche: { dpeConso: 180, dpeGes: 30, dpeDate: '2025-01-01' } }).length === 0, 'TÉMOIN P1 : la fiche porte déjà le DPE -> rien (jamais par-dessus)')
voir(P([dpe], { fiche: { dpeConso: 180, dpeGes: 30, dpeDate: '0000-00-00' } }).length === 0, 'lot 3 : même une date « 0000-00-00 » ne fait plus de carte « Remplir » (la fenêtre la propose à ajouter)')
voir(P([doc('DPE.pdf', 'diag.dpe', [v('conso_ep', { valeur_num: 210 }, 'incertain')])]).length === 0, 'TÉMOIN P1 : une valeur lue « incertaine » ne se propose pas')
const erp = doc('ERP.pdf', 'diag.erp', [v('date_etablissement', { valeur_date: '2026-09-02' })])
voir(P([erp]).length === 0, '⛔ lot 3 : la date de l\'état des risques passe par sa fenêtre, plus par une carte')
const carnet = doc('Fiche synthetique.pdf', 'copro.carnet', [v('sous_type', { valeur: 'fiche_synthetique' }), v('nb_lots_total', { valeur_num: 48 })])
const appel = doc('Appel.pdf', 'copro.appel_fonds', [v('provision_budget', { valeur_num: 300 }), v('periode', { valeur: 'trimestre' })])
const p2 = P([carnet, appel])
voir(p2.length === 0, '⛔ lot 3 : P2 RETIRÉ -- nombre de lots et quote-part passent par la fenêtre de la copropriété')
voir(P([carnet, appel], { fiche: { copropriete: null } }).length === 0 && P([carnet, appel], { fiche: { copropriete: false } }).length === 0, 'TÉMOIN P2 : un bien NON marqué copropriété -> rien (jamais faire passer la case à OUI)')
voir(P([doc('Appel.pdf', 'copro.appel_fonds', [v('provision_budget', { valeur_num: 300 }), v('periode', { valeur: 'autre' })])]).length === 0, 'TÉMOIN P2 : période inconnue -> rien')
const mandat = (charge, numero = '18836') => doc('Mandat.pdf', 'mandat.vente', [v('numero_mandat', { valeur: numero }), v('charge_honoraires', { valeur: charge })])
voir(cles(P([mandat('acquereur')], { fiche: { chargeRegistre: null } })) === 'P3.charge_honoraires', 'P3 : la charge lue, registre lu et vide')
voir(P([mandat('acquereur')], { fiche: { chargeRegistre: undefined } }).length === 0 && P([mandat('acquereur')], { fiche: { chargeRegistre: 'vendeur' } }).length === 0, 'TÉMOIN P3 : registre pas lu (undefined) ou déjà rempli -> rien')
voir(P([mandat('les_deux')], { fiche: { chargeRegistre: null } }).length === 0 && P([mandat('acquereur', '17000')], { fiche: { chargeRegistre: null } }).length === 0, 'TÉMOIN P3 : « les deux » ou un autre mandat -> rien')
const cpv = doc('Compromis.pdf', 'transaction.avant_contrat', [v('condition_pret', { valeur: 'oui' }), v('date_limite_pret', { valeur_date: '2026-12-01' }), v('date_signature', { valeur_date: '2026-10-15' }), v('prix', { valeur_num: 185000 })])
// lots 10a et 10b : les cartes P4 (conditions, date d'acte, séquestre) sont RETIRÉES le 17/11 (lot 10c) -- le compromis lu
// passe par « Ce que dit le compromis » (test_ged_bilan.cjs). Témoin : un compromis complet ne propose plus AUCUNE carte.
const cv = (n, d, r) => [v('conditions.nature', { valeur: n }, 'lu', r), ...(d ? [v('conditions.date_limite', { valeur_date: d }, 'lu', r)] : [])]
const cpvTout = doc('Compromis.pdf', 'transaction.avant_contrat', [v('date_signature', { valeur_date: '2026-10-15' }), v('prix', { valeur_num: 185000 }), v('date_reiteration', { valeur_date: '2027-01-15' }), v('sequestre', { valeur_num: 9250 }), v('condition_pret', { valeur: 'oui' }), ...cv('pret', '2026-12-01', 0), ...cv('preemption', null, 1)])
voir(P([cpv, cpvTout]).length === 0, 'TÉMOIN 10c : le compromis ne propose plus de carte (un seul chemin : « Ce que dit le compromis »)')
// 17/11 : le catalogue de l'agence passe à six clauses -- les libellés écrits doivent y correspondre MOT POUR MOT
const { LIBELLE_CONDITION, natureDuLibelle } = charger('src/lib/gedComparer.ts')
const CATALOGUE_17_11 = ['Préemption mairie', 'Obtention Crédit', 'Permis de construire', 'Delai de retractation SRU', 'Depot du permis de construire', 'Obtention du permis de construire']
voir(['pret', 'preemption', 'permis_construire'].every((n) => CATALOGUE_17_11.includes(LIBELLE_CONDITION[n])), '10b : prêt, préemption et permis s\'écrivent sous le libellé EXACT du catalogue (catalogue à six du 17/11)')
voir(natureDuLibelle('Depot du permis de construire') === 'permis_construire' && natureDuLibelle('Permis de construire') === 'permis_construire' && natureDuLibelle('Delai de retractation SRU') === 'autre',
  '10b : les clauses du catalogue se reconnaissent (dépôt et obtention du permis = permis ; le délai SRU n\'est pas une condition lue)')
const { decoderConditions } = charger('src/lib/gedRemplir.ts')
voir(JSON.stringify(decoderConditions('pret@2026-12-01|bidon@|vente_bien@20261|preemption@')) === JSON.stringify([{ nature: 'pret', date: '2026-12-01' }, { nature: 'preemption', date: null }]),
  'TÉMOIN 10b : le décodage rejette une nature inconnue et une date mal formée')
voir(P([dpe], { decisions: new Set(['P1.dpe_cons|199']) }).length === 0, 'lot 3 : plus aucune carte du DPE, avec ou sans décision (la fenêtre garde son propre journal)')

console.log('② les gardes de l\'écriture')
const app = fs.readFileSync(path.join(__dirname, 'src/App.tsx'), 'utf8').replace(/\r\n/g, '\n')
const fn = app.slice(app.indexOf('const remplirDepuisDocument = async'), app.indexOf('return `Enregistré : ${p.texte}.`\n  }\n', app.indexOf('const remplirDepuisDocument')) + 60)
const avant = (a, b) => fn.indexOf(a) >= 0 && fn.indexOf(b) > fn.indexOf(a)
voir(avant('await loadDossierDetail(dossier.app_dossier_id', 'await editAnnonceOptimistic(') && avant('if (!caseVide(actuelle)) return refus(', 'await editAnnonceOptimistic('), 'fiche : relue FRAÎCHE juste avant ; pleine -> rien écrit, la décision dit « echec »')
voir(/if \(p\.champ\.startsWith\('copropriete_'\) && !\/oui\/i\.test/.test(fn), 'copropriété : seulement si le bien est ENCORE marqué copropriété')
voir(avant('loadRegisterCycleAffaires(', 'await ecrireMandatCharge(') && /if \(!numero \|\| !ligne\) return refus/.test(fn) && /charge: p\.valeur === 'vendeur' \? 'mandant' : 'acquereur'/.test(fn), 'charge : la ligne du registre relue (sans elle, rien) ; jamais une charge vide')
voir(avant('await compterConditionsStrict([id])', 'await ecrireAffaireConditions(') && /if \(compte !== 0\) return refus/.test(fn), 'condition : la liste comptée STRICTEMENT juste avant ; non vide ou inconnue -> rien')
voir(avant('await editAnnonceOptimistic(', "await garder('remplie'"), 'la décision « remplie » est gardée APRÈS le geste réussi')
const fnAff = fn.slice(fn.indexOf("if (p.geste === 'affaire')"), fn.indexOf('// condition : la liste doit être VIDE'))
voir(/if \(p\.geste === 'affaire'\) return refus\('passe_par_le_compromis'/.test(fnAff) && !/editAffaireOptimistic\(/.test(fnAff),
  '10c : la porte « chez nous seulement » de la date d\'acte et du séquestre est FERMÉE (champs que Hektor connaît) -- rien écrit')
voir(/const voulues = p\.cle === 'P4\.conditions' \? decoderConditions\(p\.valeur\) : \[\{ nature: 'pret' as const, date: p\.valeur \}\]/.test(fn) && /if \(!voulues\.length\) return refus\('liste_illisible'/.test(fn)
  && avant('await compterConditionsStrict([id])', 'const voulues =') && avant('const lignesConditions =', 'await ecrireAffaireConditions(id, lignesConditions)'),
  '10b : la liste lue est décodée APRÈS le compte strict (vide exigé) ; illisible -> rien écrit ; le prêt seul comme avant')
const ged = fs.readFileSync(path.join(__dirname, 'src/lib/ged.ts'), 'utf8').replace(/\r\n/g, '\n')
const strict = ged.slice(ged.indexOf('export async function compterConditionsStrict'))
voir(/if \(error\) throw new Error\(error\.message\)/.test(strict.slice(0, 900)) && /if \(error\) return null/.test(ged.slice(ged.indexOf('export async function loadGedDecisions'), ged.indexOf('export async function gedDecider'))), 'lectures : les conditions LÈVENT sur erreur ; les décisions rendent null (rien ne se repropose)')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8').replace(/\r\n/g, '\n')
voir(/if \(!remplir \|\| !peutRemplir \|\| !decisions \|\| affaires === null\) return \[\]/.test(rm) && !/\[remplir, onRemplir/.test(rm), 'écran : une lecture ratée -> aucune proposition ; les lectures ne se relancent pas à chaque rendu')
voir(!/tout remplir/i.test(rm) && (rm.match(/'Remplir la fiche'/g) || []).length === 1, 'un clic par proposition : un seul bouton, pas de « tout remplir »')
voir(!/TAXE_FONCIERE|numero_mandat'|mandat_date|PRIXNETVENDEUR/.test(fs.readFileSync(path.join(__dirname, 'src/lib/gedRemplir.ts'), 'utf8').replace(/\r\n/g, '\n').replace(/numero_mandat'\), faits\.numeroMandat/g, '')), 'jamais la taxe foncière, ni un champ du mandat')

console.log('③ le patch')
const patch = fs.readFileSync(path.join(__dirname, '../../supabase/patch_ged_m8_remplir_2026-11-13.sql'), 'utf8').replace(/\r\n/g, '\n')
voir(/\('ged_remplir', 'off'/.test(patch) && /security definer/.test(patch) && /auth\.uid\(\)\)\s*returning id/.test(patch) && /revoke all on table public\.app_ged_decision from public, anon, authenticated/.test(patch), 'interrupteur posé ÉTEINT ; porte SECURITY DEFINER ; l\'auteur est l\'appelant ; table fermée en écriture')
voir(/decision in \('remplie', 'ignoree', 'echec'\)/.test(patch) && !/update public\.app_ged_decision|delete from public\.app_ged_decision/.test(patch), 'trois décisions possibles ; la table est un journal (ni mise à jour ni effacement)')

console.log('④ habillage H3 (16/11) : la carte, la ligne repliée, « La fiche du bien »')
const rmH3 = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8').replace(/\r\n/g, '\n')
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
