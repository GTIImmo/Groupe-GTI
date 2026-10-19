// Épreuve des signaux de démarrage bienvu : exécute le VRAI fichier src/lib/bienvuBoot.ts
// (compilé tel quel par esbuild, déjà présent avec Vite), pas une imitation.
// Usage : node test_bienvu_boot.cjs   (depuis apps/hektor-v1)
const { execFileSync } = require('child_process')
const path = require('path')
const fs = require('fs')
const APP = __dirname
const out = path.join(process.env.TEMP || '.', 'bvboot_test.cjs')
execFileSync('node', [path.join(APP, 'node_modules/esbuild/bin/esbuild'), path.join(APP, 'src/lib/bienvuBoot.ts'), '--bundle', '--format=cjs', '--outfile=' + out, '--log-level=error'], { stdio: 'inherit' })

let ok = 0, ko = 0
function check(nom, cond) { if (cond) { ok++; console.log('  vert  ' + nom) } else { ko++; console.log('  ROUGE ' + nom) } }

function scenario(nom, fn) {
  console.log(nom)
  delete require.cache[require.resolve(out)]
  const log = []
  global.window = { __bvSplash: { show: () => log.push('show'), hide: () => log.push('hide') } }
  const { bvBoot } = require(out)
  fn(bvBoot, log)
}

scenario('1. au démarrage, pas de session : l\'écran part tout de suite (c\'est la connexion)', (b, log) => {
  b.session(false)
  check('hide appelé', log.join() === 'hide')
})
scenario('2. au démarrage, session : il reste jusqu\'aux premières données', (b, log) => {
  b.session(true)
  check('rien avant les données', log.length === 0)
  b.data()
  check('hide après les données', log.join() === 'hide')
})
scenario('3. les données arrivent AVANT que la session soit connue : il part dès qu\'elle l\'est', (b, log) => {
  b.data()
  check('rien tant que la session est inconnue', log.length === 0)
  b.session(true)
  check('hide', log.join() === 'hide')
})
scenario('4. connexion SANS rechargement (mot de passe) : il revient puis repart', (b, log) => {
  b.session(false)            // écran de connexion
  b.session(true)             // le négociateur se connecte
  check('show au retour de la session', log.join() === 'hide,show')
  b.data()
  check('hide aux premières données', log.join() === 'hide,show,hide')
})
scenario('5. le renouvellement du jeton (même session) ne le réveille pas', (b, log) => {
  b.session(true); b.data()
  const showsAvant = log.filter((x) => x === 'show').length
  b.session(true); b.session(true)
  check('aucun show en plus (hide répété = sans effet : le vrai hide() ignore un écran déjà parti)', log.filter((x) => x === 'show').length === showsAvant)
})
scenario('6. déconnexion puis reconnexion', (b, log) => {
  b.session(true); b.data()
  b.session(false)
  b.session(true)
  check('show à la reconnexion', log.slice(-1)[0] === 'show')
  b.data()
  check('hide ensuite', log.slice(-1)[0] === 'hide')
})
scenario('7. mode factice (sans Supabase) : session présumée, parti aux premières données', (b, log) => {
  b.session(true); b.data()
  check('hide', log.join() === 'hide')
})
scenario('8. interrupteur ÉTEINT : window.__bvSplash absent, rien ne plante', (b) => {
  global.window = {}
  let plante = false
  try { b.session(true); b.data(); b.session(false); b.session(true); b.data() } catch (e) { plante = true }
  check('aucune exception', !plante)
})
console.log(`\n${ok} verts, ${ko} rouges`)
process.exit(ko ? 1 : 0)
