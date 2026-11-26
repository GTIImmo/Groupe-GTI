// 26/11/2026 -- GED, visuel V3, morceau 5 : la fenêtre « Ce que dit… » à l'habit de la V3. Rien de ce qu'elle écrit ne
// change : seuls l'ouverture de la page, l'en-tête, la plaque du document et la coche de réussite.
//   node test_ged_bilan_v3.cjs   (--temoin : la page ne s'ouvre plus d'office -> l'essai doit sonner)
const fs = require('fs')
const path = require('path')
let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
let fen = fs.readFileSync(path.join(__dirname, 'src/BilanCompromis.tsx'), 'utf8').replace(/\r\n/g, '\n')
if (process.argv.includes('--temoin')) fen = fen.replace('return premiere?.page ?? null', 'return null')
const css = fs.readFileSync(path.join(__dirname, 'src/BilanCompromis.css'), 'utf8').replace(/\r\n/g, '\n')

voir(/useState<number \| null>\(\(\) => \{\s*if \(!document\) return null[\s\S]{0,200}matchMedia\?\.\('\(max-width: 760px\)'\)\.matches\) return null[\s\S]{0,200}bilan\.lignes\.find\(\(l\) => l\.page && l\.etat !== 'accord' && !l\.fige\)[\s\S]{0,120}return premiere\?\.page \?\? null/.test(fen),
  'la page s\'ouvre d\'office à la PREMIÈRE ligne à trancher qui a une page (sinon la première qui en a une)')
voir(/max-width: 760px\)'\)\.matches\) return null/.test(fen), 'TÉMOIN : au téléphone, rien ne s\'ouvre d\'office (la page y remplace la liste)')
voir(/if \(!document\) return null/.test(fen), 'sans document retrouvé, pas de page')
const enr = fen.slice(fen.indexOf('async function enregistrer()'), fen.indexOf('const ligneVue'))
voir((fen.match(/onEnregistrer\(/g) || []).length === 1 && enr.includes('onEnregistrer(') && !/setPageVue/.test(enr), 'l\'écriture n\'a pas changé : un seul appel, dans enregistrer, qui ne touche pas à la page')
voir(/\{!message\.erreur \? <svg className="bc-msg-coche"/.test(fen), 'une écriture RÉUSSIE se signe d\'une coche tracée ; une erreur, non')
const fin = css.slice(css.indexOf('Visuel V3, morceau 5'))
voir(/\.bc-plaque\.is-document \{/.test(fin) && /className=\{`bc-plaque is-\$\{cote\}/.test(fen), 'la plaque du document (classe `is-document` posée par le code) a enfin son style')
voir(/\.bc-hd \{ background: var\(--bv-surface, #ffffff\)/.test(fin), 'l\'en-tête est clair (V3)')
voir(/prefers-reduced-motion: reduce\) \{ \.bc-msg-coche path/.test(fin), 'la coche se fige si l\'ordinateur demande moins de mouvement')
voir(css.indexOf('Visuel V3, morceau 5') > css.indexOf('.bc-hd {'), 'les règles V3 sont AJOUTÉES après les anciennes (rien de réécrit)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
