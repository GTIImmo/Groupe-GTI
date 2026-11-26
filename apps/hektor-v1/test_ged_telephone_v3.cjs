// 26/11/2026 -- GED, visuel V3, morceau 7 (A) : le téléphone. CSS seulement, deux défauts mesurés à 390 px sur 18849 :
// les boutons d'un document débordaient (40 sur 59), « Non trouvée : déposer » était coupé (10 cases sur 10).
//   node test_ged_telephone_v3.cjs   (--temoin : le bloc retiré -> rouge)
const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')
let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
let css = fs.readFileSync(path.join(__dirname, 'src/RecuManque.css'), 'utf8').replace(/\r\n/g, '\n')
if (process.argv.includes('--temoin')) css = css.slice(0, css.indexOf('/* Visuel V3, morceau 7'))
const i = css.indexOf('Visuel V3, morceau 7')
const fin = i >= 0 ? css.slice(i) : ''
const bloc = (fin.match(/@media \(max-width: 760px\) \{([\s\S]*?)\n\}/) || [])[1] || ''

voir(/\.mobile-console-documents \.console-document-row \.console-document-actions \.ghost-button \{ flex: 1 1 auto; min-width: max-content; \}/.test(bloc),
  'au téléphone, un bouton de document prend sa largeur (plus de texte qui sort du bouton)')
voir(/\.gm2-f \.gm2-ic:not\(\.is-recu\) ~ \.gm2-fd \{ white-space: normal;/.test(bloc), '« Non trouvée : déposer » passe à la ligne au lieu d\'être coupé')
voir(!/\.gm2-f \.gm2-fd \{/.test(bloc), 'TÉMOIN : la case d\'une pièce REÇUE garde sa ligne unique (un nom de fichier sans espace ne sort pas de la case)')
voir(bloc !== '' && !/^[^{]*\{[^}]*\}/m.test(fin.slice(0, fin.indexOf('@media'))), 'tout le morceau est sous @media (max-width: 760px) : l\'ordinateur ne change pas')
voir(i > css.indexOf('Visuel V3, morceau 4'), 'les règles sont AJOUTÉES après les anciennes (rien de réécrit)')
// aucun geste ne change : ni App.tsx ni RecuManque.tsx ne sont touchés par ce morceau
let inchange = true
try { inchange = execSync('git diff --name-only HEAD -- apps/hektor-v1/src/App.tsx apps/hektor-v1/src/RecuManque.tsx', { cwd: path.join(__dirname, '../..'), encoding: 'utf8' }).trim() === '' } catch { inchange = true }
voir(inchange, 'App.tsx et RecuManque.tsx non modifiés par ce morceau (aucun geste, aucune signature ne change)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
