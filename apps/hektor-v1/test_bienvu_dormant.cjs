// Épreuve « éteint = aucun pixel » pour bienvu.
// Usage : node test_bienvu_dormant.cjs   (depuis apps/hektor-v1)
//
// Trois choses, toutes lues dans le VRAI code :
//  1. chaque règle de bienvu.css est sous `.bv` (posée sur <html> seulement si l'interrupteur est
//     allumé) et chaque règle de bienvu-login.css porte une classe `.bvl` (qui n'existe dans le DOM
//     que si la nouvelle page de connexion est rendue) ;
//  2. les @font-face sont déclarées mais personne ne les utilise hors `.bv` / `.bvl` : les polices
//     ne se téléchargent donc jamais interrupteur éteint ;
//  3. App.tsx et MobileLayout.tsx gardent l'ANCIEN rendu quand l'interrupteur est éteint.
const fs = require('fs')
const path = require('path')
const SRC = path.join(__dirname, 'src')
const read = (f) => fs.readFileSync(path.join(SRC, f), 'utf8')

let ok = 0, ko = 0
function check(nom, cond, detail) { if (cond) { ok++; console.log('  vert  ' + nom) } else { ko++; console.log('  ROUGE ' + nom + (detail ? '\n        ' + detail : '')) } }

/** Les sélecteurs de chaque règle « de style » (hors @font-face / @keyframes, @media parcouru). */
function selecteurs(css) {
  const sans = css.replace(/\/\*[\s\S]*?\*\//g, '')
  const out = []
  function parcourir(texte) {
    let i = 0
    while (i < texte.length) {
      const o = texte.indexOf('{', i)
      if (o < 0) break
      const entete = texte.slice(i, o).trim()
      let profondeur = 1, j = o + 1
      while (j < texte.length && profondeur > 0) { if (texte[j] === '{') profondeur++; else if (texte[j] === '}') profondeur--; j++ }
      const corps = texte.slice(o + 1, j - 1)
      if (entete.startsWith('@media') || entete.startsWith('@supports')) parcourir(corps)
      else if (!entete.startsWith('@')) out.push(entete)
      i = j
    }
  }
  parcourir(sans)
  // on coupe sur les virgules du NIVEAU 0 seulement : `:is(a, b)` ne fait qu'un sélecteur
  const separer = (s) => { const r = []; let p = 0, d = ''; for (const c of s) { if (c === '(') p++; if (c === ')') p--; if (c === ',' && p === 0) { r.push(d); d = '' } else d += c } r.push(d); return r }
  return out.flatMap((s) => separer(s).map((x) => x.trim())).filter(Boolean)
}

console.log('1. bienvu.css : tout est sous .bv')
const bv = read('bienvu.css')
const selBv = selecteurs(bv)
const horsBv = selBv.filter((s) => !/^(:root)?\.bv(\s|$|[.:#\[])/.test(s))
check(`${selBv.length} sélecteurs lus, aucun hors .bv`, selBv.length >= 5 && horsBv.length === 0, horsBv.slice(0, 3).join(' | '))

console.log('2. bienvu-login.css : tout porte .bvl')
const lg = read('bienvu-login.css')
const selLg = selecteurs(lg)
const horsLg = selLg.filter((s) => !/\.bvl/.test(s))
check(`${selLg.length} sélecteurs lus, aucun sans .bvl`, selLg.length > 30 && horsLg.length === 0, horsLg.slice(0, 3).join(' | '))

console.log('3. les polices ne sont utilisées que sous .bv / .bvl')
const sansDecl = (css) => css.replace(/\/\*[\s\S]*?\*\//g, '').replace(/@font-face\s*\{[^}]*\}/g, '')
const toutesAutres = ['styles.css', 'layout-overrides.css', 'mobile.css', 'annonces-v2.css', 'fa-cockpit-v2.css', 'design-system.css'].map(read).join('\n')
check('aucune feuille existante ne cite « Plus Jakarta Sans »', !/Plus Jakarta Sans/.test(toutesAutres))
check('bienvu.css ne s\'en sert que par la variable --bv-font-display (sous .bv)', (sansDecl(bv).match(/Plus Jakarta Sans/g) || []).length === 1)

console.log('4. interrupteur ÉTEINT : l\'ancien rendu est gardé')
const app = read('App.tsx')
check('App.tsx garde l\'image gti-mark.png hors bienvu', /APP_BIENVU_ENABLED\s*\n?\s*\? \(sidebarCollapsed \? <BienvuSymbol \/> : <BienvuLogo \/>\)\s*\n?\s*: <img src="\/gti-mark\.png" alt="Groupe GTI" \/>/.test(app))
check('App.tsx garde « Groupe GTI » + titre d\'écran hors bienvu', /APP_BIENVU_ENABLED \? null : \(\s*<div className="rail-brand">\s*<strong>Groupe GTI<\/strong>/.test(app))
check('App.tsx garde l\'ancien écran de connexion (login-shell) après le test bienvu', /if \(bienvuLoginProps\) return <BienvuLogin mode="connexion"[\s\S]{0,80}\n\s*return \(\s*\n\s*<div className="login-shell">/.test(app))
const mob = read('layouts/MobileLayout.tsx')
check('MobileLayout garde la forme CSS et « GTI Immobilier » hors bienvu', /: <div className="mobile-brand-mark" aria-hidden="true" \/>/.test(mob) && /APP_BIENVU_ENABLED \? 'bienvu' : 'GTI Immobilier'/.test(mob))

check("le choix « Nouvelle annonce » garde ses emojis quand l'interrupteur est éteint", ['✨', '✍️', '📸', '🤖', '📷', '📄', '⚠️'].every((e) => app.includes(": '" + e + "'}")))

console.log('5. l\'interrupteur est lu de la même façon partout')
const flag = read('lib/bienvuFlag.ts')
const main = read('main.tsx')
const idx = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8')
check('lib/bienvuFlag.ts et main.tsx lisent VITE_APP_BIENVU_ENABLED avec les mêmes valeurs', /\['true', '1', 'on', 'yes'\]/.test(flag) && /\['true', '1', 'on', 'yes'\]/.test(main))
check('index.html lit le même drapeau avec les mêmes valeurs', /true\|1\|on\|yes/.test(idx) && idx.includes('%VITE_APP_BIENVU_ENABLED%'))

console.log(`\n${ok} verts, ${ko} rouges`)
process.exit(ko ? 1 : 0)
