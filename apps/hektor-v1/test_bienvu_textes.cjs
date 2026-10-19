// Épreuve du vocabulaire bienvu (lot 6) : exécute le VRAI fichier src/lib/bienvuTexte.ts, compilé deux fois
// (interrupteur éteint, puis allumé) par esbuild.
// Usage : node test_bienvu_textes.cjs   (depuis apps/hektor-v1)
//         node test_bienvu_textes.cjs --temoin   (rejoue les contrôles « éteint » sur le build ALLUMÉ : ils doivent virer au rouge)
const { execFileSync } = require('child_process')
const path = require('path')
const fs = require('fs')
const APP = __dirname
const TEMOIN = process.argv.includes('--temoin')

function compiler(allume) {
  const out = path.join(process.env.TEMP || '.', `bvtextes_${allume ? 'on' : 'off'}.cjs`)
  execFileSync('node', [path.join(APP, 'node_modules/esbuild/bin/esbuild'), path.join(APP, 'src/lib/bienvuTexte.ts'), '--bundle', '--format=cjs',
    `--define:import.meta.env.VITE_APP_BIENVU_ENABLED="${allume ? 'true' : 'false'}"`, '--outfile=' + out, '--log-level=error'])
  delete require.cache[require.resolve(out)]
  return require(out)
}
let ok = 0, ko = 0
function check(nom, cond) { if (cond) { ok++; console.log('  vert  ' + nom) } else { ko++; console.log('  ROUGE ' + nom) } }

const off = compiler(TEMOIN)   // en mode témoin, le « éteint » est en réalité allumé
const on = compiler(true)
const cles = Object.keys(on.TEXTES_BIENVU)
const simples = cles.filter((k) => !k.includes('{}'))
const gabarits = cles.filter((k) => k.includes('{}'))

console.log('1. éteint : chaque texte ressort à l\'identique')
check(`${simples.length} textes simples rendus tels quels`, simples.every((k) => off.bvs(k) === k))
check(`${gabarits.length} gabarits rendus tels quels, valeurs à leur place`, gabarits.every((k) => {
  const morceaux = k.split('{}'); morceaux.raw = morceaux
  const valeurs = morceaux.slice(1).map((_, i) => `<v${i}>`)
  const attendu = morceaux.reduce((a, m, i) => a + m + (i < valeurs.length ? valeurs[i] : ''), '')
  return off.bvt(morceaux, ...valeurs) === attendu
}))

console.log('2. allumé : chaque texte est remplacé, par autre chose que lui-même')
check('textes simples remplacés', simples.every((k) => on.bvs(k) === on.TEXTES_BIENVU[k] && on.bvs(k) !== k))
check('gabarits remplacés, valeurs à leur place', gabarits.every((k) => {
  const morceaux = k.split('{}'); morceaux.raw = morceaux
  const valeurs = morceaux.slice(1).map((_, i) => `<v${i}>`)
  const r = on.bvt(morceaux, ...valeurs)
  return r !== morceaux.reduce((a, m, i) => a + m + (i < valeurs.length ? valeurs[i] : ''), '') && valeurs.every((v) => r.includes(v)) && !/\{\d+\}/.test(r)
}))

console.log('3. allumé : un texte inconnu passe tel quel')
check('texte simple inconnu', on.bvs('Un texte absent de la table') === 'Un texte absent de la table')
check('gabarit inconnu', (() => { const m = ['Inconnu ', ' ici']; m.raw = m; return on.bvt(m, 42) === 'Inconnu 42 ici' })())

console.log('4. règles de rédaction des nouveaux textes')
const nouveaux = Object.values(on.TEXTES_BIENVU)
const garde = /(dans Hektor|sur Hektor|par Hektor|à Hektor|comme dans Hektor|Hektor a (refusé|bloqué)|que Hektor)/
check('« Hektor » ne reste que pour un geste réel ou un refus venu de Hektor', nouveaux.filter((t) => /Hektor/.test(t) && !garde.test(t)).length === 0)
check('tutoiement : ni « vous », ni « votre », ni impératif en -ez', nouveaux.filter((t) => /\b(vous|votre|vos|Voulez|Vérifiez|Contrôlez|renvoyez|fermez|Rouvrez|refaites)\b/i.test(t)).length === 0)
check('pas de texte vide', nouveaux.every((t) => t.trim().length > 0))
check('les « {0} » du nouveau texte correspondent aux « {} » de la clé', cles.every((k) => (k.match(/\{\}/g) || []).length === (on.TEXTES_BIENVU[k].match(/\{\d+\}/g) || []).length))

console.log('5. le code : tout appel bvs/bvt vise un texte de la table')
const SRC = path.join(APP, 'src')
const fichiers = ['App.tsx', 'lib/api.ts', 'ContactSearchModal.tsx']
const ts = require(path.join(APP, 'node_modules/typescript'))
let orphelins = [], appels = 0
for (const f of fichiers) {
  const texte = fs.readFileSync(path.join(SRC, f), 'utf8')
  const sf = ts.createSourceFile(f, texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
  const visiter = (n) => {
    if (ts.isCallExpression(n) && ts.isIdentifier(n.expression) && n.expression.text === 'bvs' && n.arguments.length === 1 && (ts.isStringLiteral(n.arguments[0]) || ts.isNoSubstitutionTemplateLiteral(n.arguments[0]))) {
      appels++; if (!(n.arguments[0].text in on.TEXTES_BIENVU)) orphelins.push(`${f}:${sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1} ${n.arguments[0].text.slice(0, 50)}`)
    } else if (ts.isTaggedTemplateExpression(n) && ts.isIdentifier(n.tag) && n.tag.text === 'bvt') {
      appels++
      const t = n.template
      const c = ts.isNoSubstitutionTemplateLiteral(t) ? t.text : [t.head.text, ...t.templateSpans.map((s) => s.literal.text)].join('{}')
      if (!(c in on.TEXTES_BIENVU)) orphelins.push(`${f}:${sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1} ${c.slice(0, 50)}`)
    }
    ts.forEachChild(n, visiter)
  }
  visiter(sf)
}
check(`${appels} appels, aucun hors table`, orphelins.length === 0 && appels > 0)
if (orphelins.length) orphelins.forEach((o) => console.log('     orphelin : ' + o))
check('chaque entrée de la table sert au moins une fois', (() => {
  const utilisees = new Set()
  for (const f of fichiers) {
    const texte = fs.readFileSync(path.join(SRC, f), 'utf8')
    const sf = ts.createSourceFile(f, texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
    const visiter = (n) => {
      if (ts.isCallExpression(n) && ts.isIdentifier(n.expression) && n.expression.text === 'bvs' && n.arguments[0] && (ts.isStringLiteral(n.arguments[0]) || ts.isNoSubstitutionTemplateLiteral(n.arguments[0]))) utilisees.add(n.arguments[0].text)
      else if (ts.isTaggedTemplateExpression(n) && ts.isIdentifier(n.tag) && n.tag.text === 'bvt') { const t = n.template; utilisees.add(ts.isNoSubstitutionTemplateLiteral(t) ? t.text : [t.head.text, ...t.templateSpans.map((s) => s.literal.text)].join('{}')) }
      ts.forEachChild(n, visiter)
    }
    visiter(sf)
  }
  const inutiles = cles.filter((k) => !utilisees.has(k))
  if (inutiles.length) inutiles.forEach((k) => console.log('     inutile : ' + k.slice(0, 60)))
  return inutiles.length === 0
})())

console.log(`\n${ok} verts, ${ko} rouges${TEMOIN ? ' (mode témoin : les contrôles « éteint » DOIVENT être rouges)' : ''}`)
process.exit(TEMOIN ? (ko > 0 ? 0 : 1) : (ko === 0 ? 0 : 1))
