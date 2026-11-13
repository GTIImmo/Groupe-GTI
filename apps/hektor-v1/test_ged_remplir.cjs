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

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
