// GED morceau 4 (12/11/2026) : essais hors ligne du classement par l'IA.  node test_ged_classement_ia.cjs
// ① la garde RIB du navigateur (MÊMES exemples que backend/tests/test_ged_classer.py) ; ② les pages montrées ;
// ③ quand le type de l'IA est pré-choisi ; ④ le branchement : interrupteur, file une à une, rien d'écrit sans clic.
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const code = esbuild.buildSync({
  entryPoints: [path.join(__dirname, 'src/lib/gedClassementIa.ts')], bundle: true, write: false, format: 'cjs', platform: 'node',
  external: ['react', './supabase', './ged', 'pdfjs-dist', 'pdfjs-dist/*', 'pdf-lib'], define: { 'import.meta.env': '{}' },
}).outputFiles[0].text
const m = { exports: {} }
new Function('module', 'exports', 'require', code)(m, m.exports, (n) => (n === './supabase' ? { hasSupabaseEnv: false, supabase: null } : n === './ged' ? { loadInterrupteurTroisCrans: async () => false } : require(n)))
const { ibanValide, texteDitRib, nomDitRib, pagesAEnvoyer, preChoisirTypeIa } = m.exports

console.log('① la garde RIB')
voir(ibanValide('FR7630006000011234567890189'), 'un IBAN français valide est reconnu')
voir(texteDitRib('Titulaire : X\nIBAN : FR76 3000 6000 0112 3456 7890 189\nBIC : AGRIFRPP'), 'un IBAN en blocs, suivi du BIC')
voir(texteDitRib('compte FR7630006000011234567890189 ouvert'), 'un IBAN collé')
voir(texteDitRib('RELEVÉ D’IDENTITÉ BANCAIRE'), 'la phrase « relevé d\'identité bancaire », accents et apostrophe courbe')
voir(!texteDitRib('FR76 3000 6000 0112 3456 7890 188'), 'TÉMOIN : une clé de contrôle fausse n\'est pas un IBAN')
voir(!texteDitRib('Diagnostic de performance énergétique, réf. DP12345678901234, classe D'), 'TÉMOIN : un DPE n\'est pas un RIB')
voir(!texteDitRib(null) && !texteDitRib(''), 'TÉMOIN : pas de texte, pas de RIB')
voir(nomDitRib('RIB vendeur.pdf') && nomDitRib('rib_dupont.jpg') && nomDitRib('IBAN.png'), 'un nom qui dit RIB ou IBAN')
voir(nomDitRib('Relevé d\'identité bancaire.pdf'), 'un nom qui dit « identité bancaire »')
voir(!nomDitRib('Attribution.pdf') && !nomDitRib('Ribeiro compromis.pdf') && !nomDitRib('DPE.pdf'), 'TÉMOIN : « Attribution », « Ribeiro », « DPE » ne disent pas RIB')

console.log('② les pages montrées')
voir(JSON.stringify(pagesAEnvoyer(3)) === '[1,2,3]', '3 pages : toutes')
voir(pagesAEnvoyer(12).length === 12, '12 pages : toutes')
voir(pagesAEnvoyer(40).length === 40 && pagesAEnvoyer(25).length === 25, "proposition A (17/11) : jusqu'à 40 pages, toutes (un lot de pièces se voit en entier)")
voir(JSON.stringify(pagesAEnvoyer(42)) === JSON.stringify([...Array.from({ length: 36 }, (_, i) => i + 1), 39, 40, 41, 42]), '42 pages : les 36 premières et les 4 dernières')

console.log('③ quand le type de l\'IA est pré-choisi')
const r = (x) => ({ typeCode: 'diag.dpe', confiance: 'haute', nomPropose: null, pieces: [], sensible: false, lisible: true, remarque: null, ...x })
const l = (x) => ({ forceNom: 'muet', typeTouche: false, typeAttendu: false, ...x })
voir(preChoisirTypeIa(l({}), r({})), 'nom muet, rien choisi : pré-choisi')
voir(preChoisirTypeIa(l({ forceNom: 'probable' }), r({ confiance: 'moyenne' })), 'nom seulement probable : pré-choisi')
voir(!preChoisirTypeIa(l({ forceNom: 'sur' }), r({})), 'TÉMOIN : nom sûr : montré, pas pré-choisi')
voir(!preChoisirTypeIa(l({ typeTouche: true }), r({})), 'TÉMOIN : type choisi à la main : jamais changé')
voir(!preChoisirTypeIa(l({ typeAttendu: true }), r({})), 'TÉMOIN : type venu de « Reçu / Manque » : jamais changé')
voir(!preChoisirTypeIa(l({}), r({ confiance: 'basse' })) && !preChoisirTypeIa(l({}), r({ lisible: false })), 'TÉMOIN : l\'IA devine ou ne lit pas : montré seulement')

console.log('④ le branchement')
const lib = fs.readFileSync(path.join(__dirname, 'src/lib/gedClassementIa.ts'), 'utf8')
const depot = fs.readFileSync(path.join(__dirname, 'src/DepotDocuments.tsx'), 'utf8')
voir(/loadInterrupteurTroisCrans\('ged_lecture_ia'\)/.test(lib), 'derrière l\'interrupteur ged_lecture_ia')
voir(/if \(!lectureIa \|\| !types\) return/.test(depot) && /lignes\.some\(\(l\) => l\.ia\?\.etat === 'lecture'\)\) return/.test(depot), 'éteint : aucune demande ; allumé : une ligne à la fois')
voir(lib.indexOf('if (nomDitRib(file.name))') < lib.indexOf('await vignetteImage(file)') && lib.indexOf('texteDitRib(textes.join') < lib.indexOf('page.render('), 'la garde RIB passe AVANT toute vignette')
voir(/IA_COTE_VIGNETTE = 512/.test(lib), 'vignettes de 512 px')
voir(!/createUploadDocumentToHektorJob|gedClasser\(/.test(depot.slice(depot.indexOf('async function lireParIa'), depot.indexOf('async function ligneNeuve'))), 'l\'IA n\'envoie rien et n\'enregistre rien : elle propose')
voir(/typeProposePar: ligne\.typePropose \? ligne\.typeProposePar : null/.test(depot), 'le classement retient qui avait proposé (le nom ou l\'IA)')

console.log("⑤ proposition A (17/11) : le découpage se propose à l'étape 1, sans clic")
const prepIa = lib.slice(lib.indexOf('export async function preparerPourIa'), lib.indexOf("// ── l'appel au serveur"))
voir(/IA_PAGES_MAX = 40/.test(lib) && /IA_TEXTE_MAX = 16000/.test(lib) && /for \(const n of pagesAEnvoyer\(nbPages\)\)/.test(prepIa), 'toutes les pages (40 au plus) en vignettes, 16 000 caractères de texte au plus')
voir(prepIa.includes('`--- page ${n} ---\\n${t.slice(0, n <= 3 ? IA_TEXTE_PAGE_DEBUT : IA_TEXTE_PAGE_SUITE)}`') && /IA_TEXTE_PAGE_SUITE = 300/.test(lib), "le début de CHAQUE page, repérée (les 3 premières plus longues : le type s'y lit)")
voir(prepIa.indexOf('texteDitRib(textes.join') < prepIa.indexOf('page.render(') && prepIa.indexOf('texteDitRib(textes.join') > 0, 'TÉMOIN : la garde RIB lit tout le texte AVANT toute vignette')
voir(!/preparerDecoupage|decoupage|chercherPieces|lienDecoupage|Chercher les pièces/.test(lib + depot), "TÉMOIN : plus de lien « Chercher les pièces » ni de mode à part (remplacé par l'étape 1)")

console.log('⑥ « Prendre ce nom » (17/11)')
const etatIaSrc = depot.slice(depot.indexOf('function etatIa(l: Ligne)'), depot.indexOf('function avisTexte'))
voir(/const nomIa = r\.lisible && r\.nomPropose && normaliserNom\(r\.nomPropose\) !== normaliserNom\(l\.nom\) \? r\.nomPropose : null/.test(etatIaSrc),
  'le nom de l\'IA se MONTRE quand il diffère du nom de la ligne (casse, accents, espaces près)')
voir(/onClick=\{\(\) => modifier\(l\.id, \{ nom: nomIa, nomTouche: true \}\)\}>Prendre ce nom</.test(etatIaSrc),
  'un clic le prend, et le nom compte alors comme choisi (plus rien ne l\'écrase)')
voir(/if \(code && !l\.nomTouche && \(l\.forceNom === 'muet' \|\| l\.forceNom === 'reste'\)\)/.test(depot) && (etatIaSrc.match(/nom: nomIa/g) || []).length === 1 && !/setLignes[\s\S]{0,200}nomIa/.test(etatIaSrc),
  'TÉMOIN : il ne s\'applique TOUT SEUL que sur un nom muet, jamais sur un nom écrit ou reconnu')
console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
