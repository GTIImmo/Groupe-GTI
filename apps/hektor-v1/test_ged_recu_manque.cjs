// GED morceau 3 (12/11/2026) : essais hors ligne de « Reçu / Manque ».  node test_ged_recu_manque.cjs
// ① le moment en cours ; ② les pièces « selon le cas » (copropriété, année, maison E/F/G, terrain, DPE non concerné) ;
// ③ la reconnaissance (type décidé > nom ; dossier de diagnostics) ; ④ les moments précédents ; ⑤ le branchement.
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, 'src/lib/gedPieces.ts')], bundle: true, write: false, format: 'cjs', platform: 'node' }).outputFiles[0].text
const m = { exports: {} }
new Function('module', 'exports', 'require', code)(m, m.exports, require)
const { recuManque, momentDuDossier, classeDpe } = m.exports

const fiche = (x) => ({ statut: 'Actif', numeroMandat: '1234', typeBien: '2', copropriete: false, anneeConstruction: 1980, assainissement: "TOUT A L'EGOUT", dpeConso: 150, dpeGes: 20, dpeNonConcerne: false, ...x })
const doc = (nom, typeCode = null) => ({ nom, typeCode })
const piece = (r, cle) => r.pieces.find((p) => p.cle === cle)

console.log('① le moment en cours')
voir(momentDuDossier({ statut: 'Actif', numeroMandat: '' }) === 'mandat', 'actif sans numéro de mandat = prise de mandat')
voir(momentDuDossier({ statut: 'Actif', numeroMandat: '1234' }) === 'mise_en_vente', 'actif avec mandat = mise en vente')
voir(momentDuDossier({ statut: 'Sous offre', numeroMandat: '1234' }) === 'offre', 'sous offre = offre')
voir(momentDuDossier({ statut: 'Sous compromis', numeroMandat: '1234' }) === 'compromis', 'sous compromis = compromis')

console.log('② les pièces selon le cas')
const cpCopro = recuManque(fiche({ statut: 'Sous compromis', copropriete: true, anneeConstruction: 1960 }), [])
voir(piece(cpCopro, 'amiante')?.etat === 'non_trouve', 'construit en 1960 : amiante attendu')
voir(!piece(cpCopro, 'plomb'), 'construit en 1960 : plomb PAS attendu (après 1949)')
voir(piece(cpCopro, 'carrez')?.etat === 'non_trouve' && piece(cpCopro, 'pre_etat_date'), 'copropriété : Carrez et pré-état daté attendus')
const cpInconnu = recuManque(fiche({ statut: 'Sous compromis', copropriete: null, anneeConstruction: null }), [])
voir(piece(cpInconnu, 'amiante')?.etat === 'selon_le_cas' && piece(cpInconnu, 'carrez')?.etat === 'selon_le_cas', 'année et copropriété inconnues : « selon le cas », jamais « non trouvé »')
voir(cpInconnu.attendues === cpInconnu.pieces.filter((p) => p.etat !== 'selon_le_cas').length, 'les « selon le cas » ne comptent pas dans les attendues')
const terrain = recuManque(fiche({ typeBien: '5' }), [])
voir(!piece(terrain, 'dpe') && piece(terrain, 'erp'), 'terrain : pas de DPE, mais l\'état des risques')
voir(!piece(recuManque(fiche({ dpeNonConcerne: true }), []), 'dpe'), 'case « DPE non concerné » : pas de DPE attendu')
voir(classeDpe(380, 20) === 'F' && classeDpe(150, 60) === 'E' && classeDpe(null, 3) === null, 'classe DPE : la pire des deux étiquettes')
voir(piece(recuManque(fiche({ typeBien: '1', dpeConso: 380, dpeGes: 20 }), []), 'audit')?.etat === 'non_trouve', 'maison classée F : audit attendu')
voir(!piece(recuManque(fiche({ typeBien: '1', dpeConso: 150, dpeGes: 20 }), []), 'audit'), 'TÉMOIN : maison classée C : pas d\'audit')
voir(!piece(recuManque(fiche({ typeBien: '2', dpeConso: 380, dpeGes: 20 }), []), 'audit'), 'TÉMOIN : appartement classé F : pas d\'audit (maison seulement)')
voir(!piece(recuManque(fiche({ statut: 'Sous compromis', assainissement: "TOUT A L'EGOUT" }), []), 'assainissement'), 'tout-à-l\'égout : pas de contrôle SPANC')
voir(piece(recuManque(fiche({ statut: 'Sous compromis', assainissement: 'FOSSE SEPTIQUE' }), []), 'assainissement')?.etat === 'non_trouve', 'fosse septique : contrôle SPANC attendu')

console.log('③ la reconnaissance')
const mev = recuManque(fiche({}), [doc('DPE 2024.pdf'), doc('IMG_20261104.jpg', 'diag.erp')])
voir(piece(mev, 'dpe')?.etat === 'recu', 'un DPE reconnu par son nom')
voir(piece(mev, 'erp')?.etat === 'recu', 'un nom muet compte par le type que l\'humain lui a donné')
const ddt = recuManque(fiche({}), [doc('DDT complet 2025.pdf')])
voir(piece(ddt, 'dpe')?.etat === 'recu' && piece(ddt, 'dpe')?.dansUnDossier, 'un dossier de diagnostics compte pour le DPE, « dans un dossier »')
voir(piece(recuManque(fiche({}), [doc('IMG_1234.jpg')]), 'dpe')?.etat === 'non_trouve', 'TÉMOIN : un nom muet non classé ne compte pour rien')
voir(piece(recuManque(fiche({}), [doc('Offre de prêt CA.pdf')]), 'bon_visite')?.etat === 'non_trouve', 'TÉMOIN : une offre de prêt n\'est pas un bon de visite')

console.log('④ les moments précédents')
const cp = recuManque(fiche({ statut: 'Sous compromis' }), [doc('Compromis signé.pdf')])
voir(cp.precedents.some((p) => p.moment === 'mandat' && p.manquantes.some((l) => l.cle === 'mandat')), 'compromis sans mandat au dossier : le mandat remonte des moments précédents')
voir(!cp.precedents.some((p) => p.manquantes.some((l) => l.cle === 'dpe')), 'une pièce déjà demandée au compromis (DPE) n\'est pas répétée')
voir(recuManque(fiche({ statut: 'Actif', numeroMandat: '' }), []).precedents.length === 0, 'prise de mandat : pas de moment précédent')

console.log('⑤ le branchement')
const app = fs.readFileSync(path.join(__dirname, 'src/App.tsx'), 'utf8')
voir((app.match(/\{blocRecuManque\}/g) || []).length === 2, 'le bloc est monté dans les deux habillages')
voir(/const blocRecuManque = gedRecuManque \? \(/.test(app), 'derrière l\'interrupteur ged_recu_manque')
voir(/onDeposer=\{gedDepot \?/.test(app), 'déposer depuis une pièce seulement si la fenêtre de dépôt est allumée')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
voir(!/absent/i.test(rm.replace(/^\/\/.*$/gm, '')), 'l\'écran ne dit jamais « absent »')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
