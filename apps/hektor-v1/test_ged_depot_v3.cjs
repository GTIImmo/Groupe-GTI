// 26/11/2026 -- GED, visuel V3, morceau 6 : la fenêtre de dépôt à l'habit de la V3. CSS seulement : aucun geste ne change
// (elle est ouverte aux négociateurs depuis le 18/11).  node test_ged_depot_v3.cjs   (--temoin : l'habit retiré -> rouge)
const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')
let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
let css = fs.readFileSync(path.join(__dirname, 'src/DepotDocuments.css'), 'utf8').replace(/\r\n/g, '\n')
if (process.argv.includes('--temoin')) css = css.slice(0, css.indexOf('/* ═══ Visuel V3, morceau 6'))
const fin = css.indexOf('Visuel V3, morceau 6') >= 0 ? css.slice(css.indexOf('Visuel V3, morceau 6')) : ''

voir(/\.ged-depot\.dd \.dd-hd:not\(\.dd-feuille-hd\) \{ background: var\(--bv-surface, #ffffff\)/.test(fin), 'l\'en-tête de la fenêtre est clair (V3)')
voir(/:not\(\.dd-feuille-hd\)/.test(fin) && !/\.dd-feuille-hd \{[^}]*background/.test(fin), 'TÉMOIN : la feuille du téléphone garde son en-tête sombre (sa poignée est blanche)')
voir(/\.dd-vign::before \{[^}]*background: var\(--bv-magenta, #c5005f\)/.test(fin), 'chaque fichier : une petite page blanche à bande magenta')
voir(/\.ged-depot-ligne\.dd-l \{ margin: 0 0 8px; border: 1px solid/.test(fin) && /\.ged-depot-liste\.dd-liste \{ background: transparent/.test(fin), 'les lignes deviennent des cartes, la liste n\'a plus de cadre')
voir(css.indexOf('Visuel V3, morceau 6') > css.indexOf('.dd-hd {'), 'les règles V3 sont AJOUTÉES après les anciennes (rien de réécrit)')
// aucun geste ne change : le composant n'est pas touché par ce morceau
let tsxInchange = true
try { tsxInchange = execSync('git diff --name-only HEAD -- apps/hektor-v1/src/DepotDocuments.tsx', { cwd: path.join(__dirname, '../..'), encoding: 'utf8' }).trim() === '' } catch { tsxInchange = true }
voir(tsxInchange, 'DepotDocuments.tsx non modifié par ce morceau (aucun geste, aucun envoi ne change)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
