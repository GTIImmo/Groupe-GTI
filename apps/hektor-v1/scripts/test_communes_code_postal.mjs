// 8a C-3 -- essai des communes du code postal, sur LE CODE REEL.            22/10/2026
// Les fonctions sont DECOUPEES dans src/lib/api.ts et src/App.tsx, traduites par le compilateur
// TypeScript du projet, puis executees : le service geo.api.gouv.fr est REELLEMENT interroge
// (lecture seule). Aucune connexion, aucune ecriture.
//     node scripts/test_communes_code_postal.mjs
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'

const ici = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(import.meta.url)
const ts = require('typescript')
const api = fs.readFileSync(path.join(ici, '..', 'src', 'lib', 'api.ts'), 'utf8')
const app = fs.readFileSync(path.join(ici, '..', 'src', 'App.tsx'), 'utf8')

function tranche(src, debut, fin = '\n}') {
  const i = src.indexOf(debut)
  if (i < 0) return null
  const f = src.indexOf(fin, i)
  return f < 0 ? null : src.slice(i, f + fin.length)
}
const morceaux = {
  cache: (() => { const i = api.indexOf('const communesParCodePostal'); return i < 0 ? null : api.slice(i, api.indexOf('\n', i) + 1) })(),
  fetch: tranche(api, 'export function fetchCommunesForPostalCode('),
  safe: tranche(app, 'function safeText('),
  norm: tranche(app, 'function normalizeContactText('),
  alerte: tranche(app, 'function avertissementLocaliteContact('),
}
const echecs = []
const controle = (nom, ok, detail) => { console.log(`${ok ? '  OK  ' : 'ECHEC '} ${nom}${ok ? '' : ' -- ' + (detail || '')}`); if (!ok) echecs.push(nom) }
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k])
controle('(1) LA PREUVE D\'ABORD : les fonctions sont dans les sources', !manquants.length, manquants.join(', '))
if (manquants.length) process.exit(2)

const js = ts.transpileModule(
  [morceaux.cache, morceaux.fetch.replace('export function', 'function'), morceaux.safe, morceaux.norm, morceaux.alerte,
   'globalThis.__c3 = { fetchCommunesForPostalCode, avertissementLocaliteContact }'].join('\n'),
  { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText
new Function(js)()
const { fetchCommunesForPostalCode: communes, avertissementLocaliteContact: alerte } = globalThis.__c3

try {
  const c42000 = await communes('42000')
  const c42700 = await communes('42700')
  const c63340 = await communes('63340')
  controle('(2) 42000 -> Saint-Étienne (le vrai service)', c42000.includes('Saint-Étienne'), JSON.stringify(c42000))
  controle('(3) 42700 -> Firminy', c42700.includes('Firminy'), JSON.stringify(c42700))
  controle('(4) un code postal partage par plusieurs communes en rend plusieurs (63340)', c63340.length > 1, JSON.stringify(c63340))
  controle('(5) un code postal mal forme ne fait aucun appel et rend une liste vide', (await communes('4200')).length === 0)

  controle('(6) Firminy + 42000 : AVERTI, avec les communes du 42000',
    /n'est pas une commune du 42000/.test(alerte('42000', 'Firminy', c42000) || '') && /Saint-Étienne/.test(alerte('42000', 'Firminy', c42000) || ''),
    alerte('42000', 'Firminy', c42000))
  controle('(7) Saint-Étienne + 42000 : rien', alerte('42000', 'Saint-Étienne', c42000) === null, alerte('42000', 'Saint-Étienne', c42000))
  controle('(8) casse, accents et tirets ne comptent pas : SAINT ETIENNE + 42000 -> rien', alerte('42000', 'SAINT ETIENNE', c42000) === null, alerte('42000', 'SAINT ETIENNE', c42000))
  controle('(9) une ville SANS code postal : AVERTI', /Sans code postal/.test(alerte('', 'Saint-Étienne', []) || ''), alerte('', 'Saint-Étienne', []))
  controle('(10) un code postal a 4 chiffres : AVERTI', /5 chiffres/.test(alerte('4200', 'Saint-Étienne', []) || ''))
  controle('(11) rien de saisi : rien', alerte('', '', []) === null)
  controle('(12) service en panne (liste vide) : on ne crie PAS au faux ecart', alerte('42000', 'Firminy', []) === null)
  const c69600 = await communes('69600')
  const aOullins = alerte('69600', 'Oullins', c69600)
  console.log(`        69600 -> ${JSON.stringify(c69600)} ; Oullins -> ${JSON.stringify(aOullins)}`)
  controle('(13) une commune ancienne (Oullins, fusionnee) : un AVERTISSEMENT (du texte), jamais un blocage',
    typeof aOullins === 'string' && /Hektor risque de ne pas garder/.test(aOullins), JSON.stringify(aOullins))
} catch (e) {
  console.log(`\n⛔ L'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`)
  process.exit(2)
}
console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : '\n✅ Tous les controles sont verts.')
process.exit(echecs.length ? 1 : 0)
