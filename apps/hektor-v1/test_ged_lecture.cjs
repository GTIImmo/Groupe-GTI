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

console.log('①bis le lot 2 : jamais un nom dans le résumé')
const P = (rang, nom, qualite) => [v('personnes.nom', { valeur: nom }, 'lu', rang), v('personnes.prenoms', { valeur: 'Claire' }, 'lu', rang), v('personnes.qualite', { valeur: qualite }, 'lu', rang)]
const taxe = { typeCode: 'justif.taxe', etat: 'lu', valeurs: [v('annee_imposition', { valeur_num: 2026 }), v('montant_total', { valeur_num: 1234 }), v('commune', { valeur: 'Firminy' }), ...P(0, 'MARTIN', 'redevable'), ...P(1, 'DURAND', 'redevable'), ...P(2, 'PETIT', 'usufruitier')] }
const rt = resumeLecture(taxe)
voir(rt === 'Lu : taxe 2026 · 1 234 € · Firminy · 2 redevables, 1 usufruitier.', 'taxe foncière : année, montant, commune, personnes COMPTÉES')
voir(!/MARTIN|DURAND|PETIT|Claire/.test(rt), 'aucun nom ni prénom dans le résumé de la taxe')
const titre = { typeCode: 'justif.titre', etat: 'lu', valeurs: [v('nature_acte', { valeur: 'attestation_succession' }), v('date_acte', { valeur_date: '2019-03-04' }), ...P(0, 'MARTIN', 'heritier'), ...P(1, 'MARTIN', 'heritier'), v('commune', { valeur: 'Firminy' }), v('lots.numero', { valeur: '12' }, 'lu', 0), v('lots.numero', { valeur: '31' }, 'lu', 1)] }
const rti = resumeLecture(titre)
voir(rti === 'Lu : attestation après décès · du 04/03/2019 · 2 héritiers · Firminy · lots 12, 31.', 'titre : nature, date, héritiers comptés, commune, lots')
voir(!/MARTIN|Claire/.test(rti), 'aucun nom dans le résumé du titre')
voir(resumeLecture({ typeCode: 'copro.carnet', etat: 'lu', valeurs: [v('nb_lots_total', { valeur_num: 48 }), v('nb_lots_principaux', { valeur_num: 20 }), v('syndic_nom', { valeur: 'Foncia Loire' }), v('procedure', { valeur: 'administration_provisoire' })] }) === 'Lu : 48 lots dont 20 principaux · syndic Foncia Loire · ⚠ procédure : administration provisoire.', 'fiche synthétique : lots, syndic, la procédure en avant')
voir(resumeLecture({ typeCode: 'copro.appel_fonds', etat: 'lu', valeurs: [v('provision_budget', { valeur_num: 420 }), v('periode', { valeur: 'trimestre' }), v('lots.numero', { valeur: '12' }, 'lu', 0)] }) === 'Lu : provision 420 € (trimestre) · lot 12.', 'appel de fonds : la provision et sa période, le lot')
const taxeAvecDate = { ...taxe, valeurs: [...taxe.valeurs, v('date_etablissement', { valeur_date: '2026-08-31' })] }
voir(dateEtatLue(taxeAvecDate) === null, 'TÉMOIN : la date d\'une taxe ne passe jamais pour la date d\'un état des risques')

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
voir(JSON.stringify([...FICHES_LUES].sort()) === '["copro.appel_fonds","copro.arrete_charges","copro.carnet","diag.dossier","diag.dpe","diag.erp","justif.taxe","justif.titre"]', 'lots 1 et 2 : huit types lus')
const srv = fs.readFileSync(path.join(__dirname, '../../backend/app/services/openai_ged_lecture_service.py'), 'utf8')
voir([...FICHES_LUES].every((c) => srv.includes(`"${c}"`)), 'chaque type lu à l\'écran a sa fiche au serveur')
voir(/PAGES_HD_PAR_TYPE: Record<string, number> = \{ 'justif\.titre': 6 \}/.test(ia) && /preparerLecture\(ligne\.file, ligne\.type\)/.test(depot), 'le titre : 6 pages en image, le type est passé à la préparation')
voir(/\.slice\(0, texteMax\)/.test(ia) && /Math\.min\(nbPages, pagesHd\)/.test(ia), 'le texte et les pages suivent le réglage du type (les autres gardent 20 000 et 4)')
voir(/lectureIa && FICHES_LUES\.has\(ligne\.type\) \? \{ etat: 'attente' \} : null/.test(depot), 'une lecture n\'est demandée que si l\'interrupteur est allumé et que le type a une fiche')
voir(/l\.lecture\?\.etat === 'lecture'\)\) return/.test(depot), 'une lecture à la fois')
const prep = ia.slice(ia.indexOf('export async function preparerLecture'), ia.indexOf('export type ResultatLecture'))
voir(prep.indexOf('nomDitRib(file.name)') < prep.indexOf('imageHd(') && prep.indexOf('texteDitRib(') < prep.indexOf('page.render('), 'la garde RIB passe avant toute image')
voir(!/\.insert\(|\.upsert\(|\.update\(|\.rpc\(/.test(lect) && !/app_ged_lecture[^\n]*insert/.test(depot), 'l\'écran n\'écrit jamais une lecture (le serveur seul)')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
voir(/Lu par l'IA : \$\{lus\.length\}/.test(rm) && /\.filter\(\(d\) => d\.present_in_hektor !== false && lectures\.has\(d\.id\)\)/.test(rm), 'après rechargement : TOUT ce qui a été lu se retrouve (« Lu par l\'IA »), quel que soit le moment de la pièce')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
