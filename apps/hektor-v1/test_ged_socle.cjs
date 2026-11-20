// 20/11/2026 -- GED, visuel V3, morceau 2 : LE SOCLE. Les trois feuilles de la GED prennent les couleurs et les polices de
// la charte bienvu (jetons --bv-* de src/bienvu.css, posés sous :root.bv). Chaque jeton garde l'ancienne valeur en repli :
// interrupteur bienvu éteint = mêmes pixels qu'avant.  node test_ged_socle.cjs   (--temoin : sur l'ancien fichier, rouge attendu)
const fs = require('fs')
const path = require('path')


let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const FEUILLES = ['RecuManque.css', 'DepotDocuments.css', 'BilanCompromis.css']
// Les couleurs qui ONT un rôle dans la charte : elles ne doivent plus être écrites en dur.
const CHARTE = ['#c5005f', '#8c0044', '#a3004e', '#a3004f', '#a9004f', '#f6b6d5', '#fdf0f6', '#fcedf4', '#fbeef4', '#fde8f1',
  '#1f2121', '#5c6163', '#747a7a', '#e2e5e6', '#cfd3d4', '#cdd2d4', '#f6f7f8', '#f7f8f8', '#2e8a5c', '#e6f3ec', '#fff1dc', '#fbeceb']
const temoin = process.argv.includes('--temoin')
// Témoin inverse : la même feuille, jetons retirés (chaque `var(--bv-…, X)` redevient X) -- l'essai doit alors sonner.
const sansCharte = (css) => css.replace(/var\(--bv-[a-z-]+, (#[0-9a-fA-F]{6})\)/g, '$1').replace(/var\(--bv-font-(?:display|ui), ([^;}]+?)\)(?=\s*[;}])/g, '$1')
const lire = (f) => {
  const css = fs.readFileSync(path.join(__dirname, 'src', f), 'utf8').replace(/\r\n/g, '\n')
  return temoin ? sansCharte(css) : css
}

const bienvu = fs.readFileSync(path.join(__dirname, 'src/bienvu.css'), 'utf8')
const jetons = new Set([...bienvu.matchAll(/(--bv-[a-z-]+)\s*:/g)].map((m) => m[1]))

for (const f of FEUILLES) {
  console.log('== ' + f)
  const css = lire(f)
  const sansRepli = css.replace(/var\(--bv-[a-z-]+, #[0-9a-fA-F]{6}\)/g, '')
  const enDur = CHARTE.filter((h) => sansRepli.toLowerCase().includes(h))
  voir(enDur.length === 0, `aucune couleur de la charte écrite en dur${enDur.length ? ' (reste : ' + enDur.join(', ') + ')' : ''}`)
  const utilises = [...css.matchAll(/var\((--bv-[a-z-]+)/g)].map((m) => m[1])
  voir(utilises.length > 0 && utilises.every((j) => jetons.has(j)), `chaque jeton utilisé existe dans bienvu.css (${utilises.length})`)
  voir(!/var\(--bv-[a-z-]+\)/.test(css), 'chaque jeton garde l’ancienne valeur en repli (éteint = mêmes pixels)')
  const familles = [...css.matchAll(/font-family:\s*([^;}]+)/g)].map((m) => m[1].trim())
  voir(familles.length > 0 && familles.every((v) => /^var\(--bv-font-(display|ui), /.test(v)), `chaque police passe par la charte (${familles.length})`)
  const titres = familles.filter((v) => v.startsWith('var(--bv-font-display')).length
  const texte = familles.filter((v) => v.startsWith('var(--bv-font-ui')).length
  voir(titres > 0 && texte > 0, `deux polices, comme la charte : titres ${titres}, texte ${texte}`)
}
voir(jetons.has('--bv-font-ui') && /--bv-font-ui:\s*'Hanken Grotesk'/.test(bienvu), 'la charte met Hanken Grotesk au texte (décision du 20/11 : « La charte »)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
