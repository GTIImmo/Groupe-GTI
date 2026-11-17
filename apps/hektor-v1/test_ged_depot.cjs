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
// 13/11 (essai réel du lot 4) : « Note honoraires GTI », sans « d' », tombait dans les notes internes -- un type jamais
// envoyé à l'IA, qui ne pouvait donc pas rattraper.
voir(['Note honoraires GTI.pdf', "Note d'honoraires.pdf", 'Notes honoraire vente.pdf'].every((n) => typeParNom(n).code === 'facture.honoraires'), 'une note d\'honoraires, avec ou sans « d\' », est une facture d\'honoraires')
voir(typeParNom('Notes visite.pdf').code === 'interne.notes' && typeParNom('Accord honoraires mandat.pdf').code === 'mandat.honoraires' && typeParNom('Baisse d honoraires.pdf').code === 'mandat.honoraires',
  'TÉMOIN : une note sans honoraires reste une note interne ; un accord ou une baisse d\'honoraires reste au mandat')

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

// habillage H2 (16/11) : la fenêtre au-dessus du bien
voir(/onFermer=\{skin === 'v21' \? \(\) => setUploadOpen\(false\) : undefined\}/.test(app), 'H2 : la fenêtre ne se pose au-dessus du bien qu\'en skin cockpit ; le classique la garde dans le panneau')
voir(/function demanderFermer\(\) \{[\s\S]{0,80}if \(envoiEnCours \|\| nonPartis \|\| lecturesEnCours\) setBande\(true\)\s*else onFermer\(\)/.test(depot),
  'H2 : fermer avec un fichier non parti, un envoi ou une lecture en cours DEMANDE d\'abord (une saisie ne se perd jamais)')
voir(/const nonPartis = lignes\.filter\(\(l\) => l\.etat === 'pret' && l\.aEnvoyer\)/.test(depot) && /if \(!lignes\.some\(\(l\) => \(l\.etat === 'pret' && l\.aEnvoyer\) \|\| l\.lecture\?\.etat === 'attente' \|\| l\.lecture\?\.etat === 'lecture'\)\) return/.test(depot),
  'H2 : la bande et l\'avertissement du navigateur comptent les mêmes fichiers')
voir((depot.match(/onClick=\{demanderFermer\}/g) || []).length === 2 && /e\.key === 'Escape'\) \{ e\.stopPropagation\(\); demanderFermer\(\)/.test(depot),
  'H2 : la croix, « Fermer » et Échap passent TOUS par la garde')
voir(!/\.dd-voile[^}]*onMouseDown|className="dd-voile" onClick/.test(depot), 'TÉMOIN : un clic à côté de la fenêtre ne la ferme pas')
const ia = fs.readFileSync(path.join(__dirname, 'src/lib/gedClassementIa.ts'), 'utf8')
const apercu = ia.slice(ia.indexOf('export async function apercuPremierePage'), ia.indexOf('export function useGedLectureIa'))
voir(apercu.length > 200 && !/fetch\(|backendApiBaseUrl|supabase/.test(apercu), 'H2 : l\'aperçu dessine la page 1 DANS le navigateur, rien ne part (ni serveur, ni IA)')
voir(!/apercuPremierePage|apercus\[/.test(depot.slice(depot.indexOf('async function lireParIa'), depot.indexOf('async function ligneNeuve'))), 'TÉMOIN : l\'aperçu n\'entre pas dans ce qui part à l\'IA')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
voir(/onResultat\?\.\(\{ moment: resultat\.moment, nonTrouvees: resultat\.pieces\.filter\(\(l\) => l\.etat === 'non_trouve'\)\.map\(\(l\) => l\.libelle\) \}\)/.test(rm) && /onResultat=\{setContexteDepot\}/.test(app),
  'H2 : les pièces non trouvées de la fenêtre sont celles du « Dossier » (une seule lecture)')
voir(!/\babsente?s?\b|\bmanque\b/i.test(depot.slice(depot.indexOf('// D\'où vient le type'))), 'TÉMOIN : le rendu dit « non trouvée », jamais « absente » ni « manque »')
// habillage H4 (16/11) : au téléphone, les pages photographiées montent dans un panneau du bas
const feuille = depot.slice(depot.indexOf('{pages.length ? createPortal('), depot.indexOf('{types === null ?'))
voir(feuille.length > 300 && /onClick=\{\(\) => void assemblerPages\(\)\}/.test(feuille) && /onClick=\{\(\) => setPages\(\[\]\)\}/.test(feuille) && /photographier\('dd-b2', 'Ajouter une page \(le verso\)'\)/.test(feuille),
  'H4 : le panneau du téléphone garde LES MÊMES gestes (l\'appareil photo du téléphone, « Faire un PDF », « Annuler les photos »)')
voir(!/getUserMedia|mediaDevices|fetch\(|\.rpc\(|createUpload/.test(feuille + depot.slice(depot.indexOf('const vignettesPages'), depot.indexOf('const vignettesPages') + 400)),
  'TÉMOIN : pas de viseur dans l\'app (décision du 16/11 : « A » seul), et les vignettes ne partent nulle part')
voir(/useEffect\(\(\) => \(\) => vignettesPages\.forEach\(\(u\) => URL\.revokeObjectURL\(u\)\), \[vignettesPages\]\)/.test(depot), 'H4 : les adresses locales des vignettes sont rendues (pas de fuite de mémoire)')
// vu en production le 17/11 : « 1 page photographiée : elles formeront… »
voir(!/photographiée\$\{[^}]*\} : elles formeront/.test(depot) && /'1 page photographiée : elle formera un document/.test(depot), 'la bande des photos parle français au singulier')
// vu en production le 16/11 : « 1 document ne est pas parti » (le gabarit ne savait pas élider)
voir(!/\bne \$\{|\bne est\b/.test(depot) && /'1 document n\\'est pas parti\.'/.test(depot) && /' L\\'envoyer avant de fermer \?'/.test(depot),
  'H2 : la bande parle français au singulier (« n\'est pas parti », « L\'envoyer »)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
