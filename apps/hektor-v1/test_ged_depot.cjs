// GED morceau 2 (12/11/2026) : essais hors ligne de la fenêtre de dépôt.  node test_ged_depot.cjs
// ① la règle des NOMS (réponse de la session signature : au réessai, le worker adopte le document « du même nom »,
//   égal ou contenu) ; ② le type proposé par le nom ; ③ le branchement dans le panneau : éteint = le formulaire
//   d'aujourd'hui, et rien d'autre du panneau ne bouge.
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const charger = (fichier) => {
  const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, fichier)], bundle: true, write: false, format: 'cjs', platform: 'node', external: ['react', './supabase'] }).outputFiles[0].text
  const m = { exports: {} }
  new Function('module', 'exports', 'require', code)(m, m.exports, (n) => (n === './supabase' ? { hasSupabaseEnv: false, supabase: null } : require(n)))
  return m.exports
}

console.log('① les noms')
const { nomEnConflit } = charger('src/lib/ged.ts')
voir(nomEnConflit('Mandat signé.pdf', ['Mandat.pdf']) === 'Mandat.pdf', '« Mandat signé » touche « Mandat » (contient)')
voir(nomEnConflit('mandat.pdf', ['Mandat de vente 18836.pdf']) === 'Mandat de vente 18836.pdf', '« mandat » touche « Mandat de vente » (contenu, sans majuscules)')
voir(nomEnConflit('DPE 12-11-2026.pdf', ['DPE 12-11-2026.jpg']) !== null, 'même nom, autre extension : conflit')
voir(nomEnConflit('Mandat de vente.pdf', ['Mandat signe 18836.pdf']) === null, 'TÉMOIN : deux noms qui ne se contiennent pas passent')
voir(nomEnConflit('Taxe foncière 2025.pdf', []) === null, 'TÉMOIN : un dossier vide ne refuse rien')

console.log('② le type proposé par le nom')
const { typeParNom } = charger('src/lib/gedTypeParNom.ts')
voir(typeParNom('Offre de prêt CA.pdf').code === 'transaction.financement', '« offre de prêt » est un financement, pas une offre')
voir(typeParNom('Avenant au mandat 18836.pdf').code === 'mandat.avenant', '« avenant au mandat » est un avenant, pas un mandat')
voir(typeParNom('DPE amiante plomb.pdf').code === 'diag.dossier', 'deux diagnostics ou plus = dossier de diagnostics')
voir(typeParNom('IMG_20261104_0912.jpg').force === 'muet', 'une photo nommée par l\'appareil est muette')
voir(typeParNom('RIB.pdf').code === 'justif.rib', 'le RIB est reconnu par son nom (jamais envoyé à l\'IA)')

console.log('③ le branchement dans le panneau')
const app = fs.readFileSync(path.join(__dirname, 'src/App.tsx'), 'utf8')
voir((app.match(/\{formulaireAjout\}/g) || []).length === 2, 'les deux habillages montrent formulaireAjout')
voir(/const formulaireAjout = gedDepot \? \([\s\S]{0,600}\) : uploadForm/.test(app), 'éteint = uploadForm, le formulaire d\'aujourd\'hui')
voir(/formulaireClassique=\{uploadForm\}/.test(app), 'le formulaire d\'aujourd\'hui reste le secours de la fenêtre')
voir((app.match(/[^=]\{uploadForm\}/g) || []).length === 0, 'plus aucun montage direct de uploadForm (tout passe par formulaireAjout)')
const depot = fs.readFileSync(path.join(__dirname, 'src/DepotDocuments.tsx'), 'utf8')
voir(/createUploadDocumentToHektorJob\(\{/.test(depot), 'l\'envoi passe par le chemin d\'aujourd\'hui')
voir(!/metadata_json|signed_document|storage_path/.test(depot), 'la fenêtre ne touche à aucun marqueur de la signature')
voir(/for \(const ligne of aPartir\)[\s\S]{0,200}await createUploadDocumentToHektorJob/.test(depot), 'un fichier après l\'autre (jamais en parallèle)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
