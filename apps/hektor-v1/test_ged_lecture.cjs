// GED morceau 6, lot 1 (12/11/2026) : essais hors ligne de la lecture côté écran.  node test_ged_lecture.cjs
// ① le résumé d'une lecture ; ② la date lue fait foi dans la règle des 6 mois ; ③ le branchement : file une à une,
// seuls les types qui ont une fiche, garde RIB avant toute image, l'écran n'écrit jamais une lecture.
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
const { resumeLecture, valeurLue, dateEtatLue, FICHES_LUES } = charger('src/lib/gedLecture.ts')
const { reglesSansIa } = charger('src/lib/gedRegles.ts')
const v = (cle, x, etat = 'lu', rang = 0) => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page: 1, etat, ...x })

console.log('① le résumé')
const dpe = { typeCode: 'diag.dpe', etat: 'lu', valeurs: [v('classe_energie', { valeur: 'D' }), v('classe_ges', { valeur: 'C' }), v('conso_ep', { valeur_num: 214.5 }), v('date_etablissement', { valeur_date: '2025-01-15' }), v('date_validite', { valeur_date: '2035-01-14' }, 'incertain'), v('commune', {}, 'non_vu')] }
const r = resumeLecture(dpe)
voir(r.includes('énergie D, climat C') && r.includes('214,5 kWh') && r.includes('établi le 15/01/2025'), 'DPE : classes, consommation, date')
voir(r.includes("valable jusqu'au 14/01/2035 (?)"), 'une valeur « incertaine » porte un point d\'interrogation')
voir(valeurLue(dpe.valeurs, 'commune') === null, 'une valeur « non vue » ne s\'affiche pas')
voir(resumeLecture({ typeCode: 'diag.erp', etat: 'lu', valeurs: [v('date_etablissement', { valeur_date: '2026-09-02' }), v('commune', { valeur: 'Saint-Étienne' })] }) === 'Lu : établi le 02/09/2026 · Saint-Étienne.', 'état des risques : date et commune')
const ddt = { typeCode: 'diag.dossier', etat: 'lu', valeurs: [v('diagnostics.diagnostic', { valeur: 'amiante' }, 'lu', 0), v('diagnostics.diagnostic', { valeur: 'plomb' }, 'lu', 1), v('dpe_classe_energie', { valeur: 'E' })] }
voir(resumeLecture(ddt) === 'Lu : 2 diagnostics (amiante, plomb) · DPE E.', 'dossier de diagnostics : la liste et la classe')
voir(resumeLecture({ typeCode: 'diag.erp', etat: 'pas_ce_type', valeurs: [] }).includes('pas ce type'), 'l\'IA dit « pas ce type » : on le dit')
voir(resumeLecture({ typeCode: 'diag.erp', etat: 'incomplet', valeurs: [] }).includes('rien pu relever'), 'rien de lu : on le dit, sans inventer')

console.log('② la date lue fait foi')
const erpVieux = { typeCode: 'diag.erp', etat: 'lu', valeurs: [v('date_etablissement', { valeur_date: '2025-12-01' })] }
voir(dateEtatLue(erpVieux) === '2025-12-01' && dateEtatLue({ ...erpVieux, etat: 'pas_ce_type' }) === null, 'la date de l\'état ; rien si ce n\'est pas ce type')
const AUJ = new Date(Date.UTC(2026, 10, 12))
const fiche = { statut: 'Sous offre', numeroMandat: '1', typeBien: '2', copropriete: null, anneeConstruction: null, assainissement: null, dpeConso: 150, dpeGes: 20, dpeNonConcerne: false, diffusable: false, dpeDate: null, nbLots: null, charges: null, prixAncien: null, prixNouveau: null, prixChangeLe: null, mandatDebut: null, mandatFin: null }
const mandat = { nom: 'Mandat.pdf', typeCode: null, date: null, signature: 'signed' }
const al = reglesSansIa(fiche, [mandat, { nom: 'ERP.pdf', typeCode: null, date: '2026-11-10', signature: null, dateEtat: '2025-12-01' }], [], AUJ).filter((a) => a.code === 'N4')
voir(al.length === 1 && al[0].texte.includes('établi le 01/12/2025'), 'déposé hier mais ÉTABLI il y a 11 mois : la règle sonne, sur la date lue')
voir(!reglesSansIa(fiche, [mandat, { nom: 'ERP.pdf', typeCode: null, date: '2026-01-10', signature: null, dateEtat: '2026-10-01' }], [], AUJ).some((a) => a.code === 'N4'), 'TÉMOIN : déposé il y a 10 mois mais établi en octobre : se tait')

console.log('③ le branchement')
const depot = fs.readFileSync(path.join(__dirname, 'src/DepotDocuments.tsx'), 'utf8')
const ia = fs.readFileSync(path.join(__dirname, 'src/lib/gedClassementIa.ts'), 'utf8')
const lect = fs.readFileSync(path.join(__dirname, 'src/lib/gedLecture.ts'), 'utf8')
voir(JSON.stringify([...FICHES_LUES].sort()) === '["diag.dossier","diag.dpe","diag.erp"]', 'lot 1 : trois types lus')
voir(/lectureIa && FICHES_LUES\.has\(ligne\.type\) \? \{ etat: 'attente' \} : null/.test(depot), 'une lecture n\'est demandée que si l\'interrupteur est allumé et que le type a une fiche')
voir(/l\.lecture\?\.etat === 'lecture'\)\) return/.test(depot), 'une lecture à la fois')
const prep = ia.slice(ia.indexOf('export async function preparerLecture'), ia.indexOf('export type ResultatLecture'))
voir(prep.indexOf('nomDitRib(file.name)') < prep.indexOf('imageHd(') && prep.indexOf('texteDitRib(') < prep.indexOf('page.render('), 'la garde RIB passe avant toute image')
voir(!/\.insert\(|\.upsert\(|\.update\(|\.rpc\(/.test(lect) && !/app_ged_lecture[^\n]*insert/.test(depot), 'l\'écran n\'écrit jamais une lecture (le serveur seul)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
