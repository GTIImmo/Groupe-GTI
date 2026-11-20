// 19/11/2026 : « Nouveau contact » -- le bouton du bas change de rôle sous le curseur (« Étape suivante » -> « Créer le
// contact », « Créer » -> « Continuer malgré doublon ») ; il reste inactif une seconde après chaque changement.
//   node test_contact_double_clic.cjs
const fs = require('fs')
const path = require('path')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const app = fs.readFileSync(path.join(__dirname, 'src/App.tsx'), 'utf8').replace(/\r\n/g, '\n')

const essai = (src) => {
  const debut = src.indexOf("const [duplicatesAccepted, setDuplicatesAccepted] = useState(false)")
  const bloc = src.slice(debut, debut + 1200)
  const bouton = /<button className="btn-brand" type="submit" disabled=\{pending \|\| boutonVientDeChanger\}>\s*<span>\{cnewSubmitLabel\}<\/span>/.test(src)
  return {
    effet: /useEffect\(\(\) => \{\s*if \(premierRenduBouton\.current\) \{ premierRenduBouton\.current = false; return \}\s*setBoutonVientDeChanger\(true\)\s*const t = window\.setTimeout\(\(\) => setBoutonVientDeChanger\(false\), 1000\)\s*return \(\) => window\.clearTimeout\(t\)\s*\}, \[contactStep, duplicatesAccepted\]\)/.test(bloc),
    bouton,
  }
}

const r = essai(app)
voir(r.effet, 'une seconde d\'arrêt après chaque changement d\'étape OU l\'apparition des doublons (pas au premier affichage)')
voir(r.bouton, 'le bouton « Étape suivante / Créer le contact / Continuer malgré doublon » suit cet arrêt')
voir((app.match(/boutonVientDeChanger/g) || []).length === 2, 'boutonVientDeChanger : déclaré, et lu par le seul bouton du bas')
const sans = essai(app.replace('disabled={pending || boutonVientDeChanger}>', 'disabled={pending}>').replace('}, [contactStep, duplicatesAccepted])', '}, [contactStep])'))
voir(!sans.bouton && !sans.effet, 'TÉMOIN INVERSE : sans la garde (ou sans les doublons dans l\'effet), l\'essai sonne')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
