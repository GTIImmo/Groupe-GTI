// Épreuve de la page de connexion bienvu (lot 2).
// Exécute le VRAI code de BienvuLogin.tsx (compilé tel quel par esbuild, déjà présent avec Vite).
// Usage : node test_bienvu_login.cjs   (depuis apps/hektor-v1)
//
// Ce qu'elle garde : App.tsx n'a qu'UN champ de message pour les erreurs ET les confirmations.
// La page neuve les distingue par le début du texte. Si quelqu'un réécrit une confirmation
// (lot « vocabulaire »), la page afficherait une confirmation en rouge — cette épreuve le crie.
const { execFileSync } = require('child_process')
const path = require('path')
const fs = require('fs')

const APP = __dirname
const out = path.join(process.env.TEMP || process.env.TMPDIR || '.', 'bvlogin_test.cjs')
execFileSync('node', [path.join(APP, 'node_modules/esbuild/bin/esbuild'), path.join(APP, 'src/BienvuLogin.tsx'), '--bundle', '--format=cjs', '--platform=node', '--loader:.css=empty', '--jsx=automatic', '--outfile=' + out, '--log-level=error'], { stdio: 'inherit' })
const { classerMessageAuth } = require(out)

let ok = 0, ko = 0
function check(nom, cond) { if (cond) { ok++; console.log('  vert  ' + nom) } else { ko++; console.log('  ROUGE ' + nom) } }

console.log('1. confirmations (affichées en vert)')
check('lien envoyé (sans accents, tel que dans App.tsx)', classerMessageAuth('Lien de reinitialisation envoye a camille@gti-immobilier.fr') === 'ok')
check('lien envoyé (avec accents, après le lot vocabulaire)', classerMessageAuth('Lien de réinitialisation envoyé à camille@gti-immobilier.fr') === 'ok')
check('mot de passe mis à jour (sans accents)', classerMessageAuth('Mot de passe mis a jour. Vous pouvez maintenant vous connecter.') === 'ok')
check('mot de passe mis à jour (avec accents)', classerMessageAuth('Mot de passe mis à jour. Vous pouvez maintenant vous connecter.') === 'ok')

console.log('2. erreurs (affichées en rouge) — dont celles qui ressemblent à une confirmation')
for (const m of [
  'Connexion refusee : utilise une adresse @gti-immobilier.fr.',
  'Les mots de passe ne correspondent pas',
  'Le mot de passe doit contenir au moins 8 caracteres',
  'Renseigne un email pour recevoir le lien de reinitialisation',   // contient « reinitialisation » mais n'est PAS une confirmation
  'Unable to send password reset email',
  'Erreur d envoi de reinitialisation',
  'Connexion impossible',
]) check('erreur : ' + m.slice(0, 50), classerMessageAuth(m) === 'erreur')

console.log('3. rien à afficher')
check('null', classerMessageAuth(null) === null)
check('chaîne vide', classerMessageAuth('') === null)
check('espaces', classerMessageAuth('   ') === null)

console.log('4. GARDE : App.tsx émet bien des confirmations que la page reconnaît')
const app = fs.readFileSync(path.join(APP, 'src/App.tsx'), 'utf8')
const succes = [...app.matchAll(/setErrorMessage\(\s*[`'"]((?:Lien de r|Mot de passe mis)[^`'"]*)/gi)].map((m) => m[1])
check('au moins 2 messages de confirmation trouvés dans App.tsx (trouvés : ' + succes.length + ')', succes.length >= 2)
check('chacun est classé « ok » par la page', succes.length > 0 && succes.every((m) => classerMessageAuth(m) === 'ok'))

console.log('5. GARDE : la page ne contient aucune logique d\'authentification')
const src = fs.readFileSync(path.join(APP, 'src/BienvuLogin.tsx'), 'utf8')
check('aucun appel à signIn / signOut / supabase', !/signIn|signOut|supabase|updatePassword|sendPasswordReset/.test(src.replace(/\/\/.*$/gm, '')))

console.log(`\n${ok} verts, ${ko} rouges`)
process.exit(ko ? 1 : 0)
