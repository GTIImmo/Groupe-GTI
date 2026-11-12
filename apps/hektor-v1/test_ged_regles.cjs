// GED morceau 5 (12/11/2026) : essais hors ligne des règles sans IA.  node test_ged_regles.cjs
// Chaque règle a son cas qui sonne ET son témoin qui se tait. ⑨ le branchement : interrupteur, rien d'écrit.
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, 'src/lib/gedRegles.ts')], bundle: true, write: false, format: 'cjs', platform: 'node' }).outputFiles[0].text
const m = { exports: {} }
new Function('module', 'exports', 'require', code)(m, m.exports, require)
const { reglesSansIa, finValiditeDpe, lireDate } = m.exports

const AUJ = new Date(Date.UTC(2026, 10, 12))
const fiche = (x) => ({
  statut: 'Actif', numeroMandat: '1234', typeBien: '2', copropriete: false, anneeConstruction: 1980, assainissement: null,
  dpeConso: 150, dpeGes: 20, dpeNonConcerne: false, diffusable: true, dpeDate: '2024-03-01', nbLots: null, charges: null,
  prixAncien: null, prixNouveau: null, prixChangeLe: null, mandatDebut: '2026-01-10', mandatFin: '2026-12-31', ...x,
})
const doc = (nom, x = {}) => ({ nom, typeCode: null, date: '2026-10-01', signature: null, ...x })
const sonne = (alertes, codeRegle) => alertes.filter((a) => a.code === codeRegle)
const mandatSigne = doc('Mandat de vente.pdf', { signature: 'signed' })

console.log('⓪ les dates')
voir(lireDate('0000-00-00') === null && lireDate('1970-01-01') === null && lireDate('') === null, 'date vide de Hektor et date zéro : pas des dates')
voir(lireDate('15/06/2026')?.getUTCMonth() === 5, 'JJ/MM/AAAA lu')
voir(finValiditeDpe(lireDate('2016-05-01')).getUTCFullYear() === 2022 && finValiditeDpe(lireDate('2019-05-01')).getUTCFullYear() === 2024 && finValiditeDpe(lireDate('2022-05-01')).getUTCFullYear() === 2032, 'validité du DPE : 2022, 2024, puis 10 ans')

console.log('① N1 le mandat signé')
voir(sonne(reglesSansIa(fiche({}), [doc('Mandat de vente.pdf', { signature: 'pending' })], [], AUJ), 'N1b').length === 1, 'diffusé, signature en attente : sonne')
voir(!sonne(reglesSansIa(fiche({}), [doc('Mandat de vente.pdf', { signature: 'pending' }), doc('Mandat scan.pdf')], [], AUJ), 'N1b').length, 'TÉMOIN : un PDF papier sans état fait taire la règle')
voir(!sonne(reglesSansIa(fiche({ diffusable: false }), [doc('Mandat de vente.pdf', { signature: 'pending' })], [], AUJ), 'N1b').length, 'TÉMOIN : non diffusé : se tait')
voir(sonne(reglesSansIa(fiche({ statut: 'Sous offre' }), [], [], AUJ), 'N1c').length === 1, 'sous offre sans mandat : sonne')
voir(!sonne(reglesSansIa(fiche({ statut: 'Sous offre' }), [mandatSigne], [], AUJ), 'N1c').length, 'TÉMOIN : sous offre avec mandat signé : se tait')

console.log('② N2 la baisse de prix')
const baisse = { prixAncien: 200000, prixNouveau: 190000, prixChangeLe: '2026-09-01' }
voir(sonne(reglesSansIa(fiche(baisse), [mandatSigne], [], AUJ), 'N2')[0]?.texte.includes('5 %'), 'baisse de 5 % sans avenant : sonne, avec le pourcentage')
voir(!sonne(reglesSansIa(fiche(baisse), [mandatSigne, doc('Avenant au mandat baisse.pdf')], [], AUJ), 'N2').length, 'TÉMOIN : avenant déposé : se tait')
voir(!sonne(reglesSansIa(fiche({ ...baisse, prixNouveau: 196000 }), [mandatSigne], [], AUJ), 'N2').length, 'TÉMOIN : baisse de 2 % : se tait')
voir(!sonne(reglesSansIa(fiche({ ...baisse, prixChangeLe: '2025-12-01' }), [mandatSigne], [], AUJ), 'N2').length, 'TÉMOIN : baisse d\'avant le mandat : se tait')

console.log('③ N4 l\'état des risques de plus de 6 mois')
const offre = fiche({ statut: 'Sous offre' })
voir(sonne(reglesSansIa(offre, [mandatSigne, doc('ERP.pdf', { date: '2026-03-01' })], [], AUJ), 'N4')[0]?.niveau === 'alerte', 'sous offre, ERP déposé en mars : alerte')
voir(sonne(reglesSansIa(fiche({ statut: 'Sous compromis' }), [mandatSigne, doc('ERP.pdf', { date: '2026-03-01' })], [], AUJ), 'N4')[0]?.niveau === 'info', 'sous compromis : simple information (question n° 5 ouverte)')
voir(!sonne(reglesSansIa(offre, [mandatSigne, doc('ERP.pdf', { date: '2026-10-01' })], [], AUJ), 'N4').length, 'TÉMOIN : ERP récent : se tait')
voir(!sonne(reglesSansIa(fiche({}), [mandatSigne, doc('ERP.pdf', { date: '2026-03-01' })], [], AUJ), 'N4').length, 'TÉMOIN : bien seulement actif : se tait')

console.log('④ N5 le DPE')
voir(sonne(reglesSansIa(fiche({ dpeDate: '2019-04-01' }), [mandatSigne], [], AUJ), 'N5').length === 1, 'DPE de 2019 : plus valable depuis le 31/12/2024')
voir(!sonne(reglesSansIa(fiche({ dpeDate: '0000-00-00' }), [mandatSigne], [], AUJ), 'N5').length, 'TÉMOIN : date vide : on ne conclut rien')
voir(sonne(reglesSansIa(fiche({ dpeConso: null, dpeGes: null }), [mandatSigne], [], AUJ), 'N5').some((a) => a.texte.includes('sans DPE')), 'bâti diffusé sans DPE : sonne')
voir(!sonne(reglesSansIa(fiche({ dpeConso: null, dpeGes: null, typeBien: '5' }), [mandatSigne], [], AUJ), 'N5').length, 'TÉMOIN : un terrain : se tait')
voir(!sonne(reglesSansIa(fiche({ dpeConso: null, dpeGes: null, dpeNonConcerne: true }), [mandatSigne], [], AUJ), 'N5').length, 'TÉMOIN : case « DPE non concerné » : se tait')

console.log('⑤ N8 et N9 la copropriété')
voir(sonne(reglesSansIa(fiche({ copropriete: false }), [mandatSigne, doc('PV AG 2025.pdf')], [], AUJ), 'N8').length === 1, 'case à NON avec un PV d\'AG : alerte')
voir(!sonne(reglesSansIa(fiche({ copropriete: false }), [mandatSigne], [], AUJ), 'N8').length, 'TÉMOIN : case à NON sans pièce de copro : se tait')
voir(sonne(reglesSansIa(fiche({ copropriete: true }), [mandatSigne], [], AUJ), 'N9').length === 2, 'copro sans lots ni charges : deux pièces')
voir(!sonne(reglesSansIa(fiche({ copropriete: true, nbLots: 12, charges: 90 }), [mandatSigne], [], AUJ), 'N9').length, 'TÉMOIN : lots et charges remplis : se tait')
voir(!sonne(reglesSansIa(fiche({ copropriete: null }), [mandatSigne], [], AUJ), 'N9').length, 'TÉMOIN : copropriété inconnue : se tait')

console.log('⑥ N10 la transaction au registre')
voir(sonne(reglesSansIa(fiche({}), [mandatSigne, doc('Offre achat Dupont.pdf')], [], AUJ), 'N10').length === 1, 'une offre au dossier, aucune au registre : information')
voir(!sonne(reglesSansIa(fiche({}), [mandatSigne, doc('Offre achat.pdf')], [{ kind: 'offre', state: 'refused', date: '2026-10-01', dateActe: null }], AUJ), 'N10').length, 'TÉMOIN : l\'offre est au registre : se tait')
voir(sonne(reglesSansIa(fiche({}), [mandatSigne, doc('Acte de vente 2011.pdf')], [], AUJ), 'N10')[0]?.pourquoi.includes('titre'), 'un acte sans vente au registre : « souvent la vente précédente »')

console.log('⑦ N11 hors de la période du mandat')
voir(sonne(reglesSansIa(fiche({ mandatFin: '2026-06-30' }), [mandatSigne], [{ kind: 'offre', state: 'accepted', date: '2026-08-01', dateActe: null }], AUJ), 'N11').length === 1, 'offre acceptée après la fin du mandat : alerte')
voir(!sonne(reglesSansIa(fiche({ mandatFin: '2026-06-30' }), [mandatSigne], [{ kind: 'offre', state: 'refused', date: '2026-08-01', dateActe: null }], AUJ), 'N11').length, 'TÉMOIN : offre refusée : se tait')
voir(!sonne(reglesSansIa(fiche({ mandatFin: null }), [mandatSigne], [{ kind: 'offre', state: 'accepted', date: '2026-08-01', dateActe: null }], AUJ), 'N11').length, 'TÉMOIN : fin de mandat inconnue : se tait')

console.log('⑧ N12 l\'acte prévu')
const cp = fiche({ statut: 'Sous compromis' })
const compromis = [{ kind: 'compromis', state: 'active', date: '2026-07-01', dateActe: '2026-10-15' }]
voir(sonne(reglesSansIa(cp, [mandatSigne], compromis, AUJ), 'N12').length === 1, 'acte prévu le 15/10, pas d\'acte : pièce non trouvée')
voir(!sonne(reglesSansIa(cp, [mandatSigne, doc('Acte authentique.pdf')], compromis, AUJ), 'N12').length, 'TÉMOIN : acte déposé : se tait')
voir(!sonne(reglesSansIa(cp, [mandatSigne], [{ ...compromis[0], dateActe: '2026-12-20' }], AUJ), 'N12').length, 'TÉMOIN : acte prévu plus tard : se tait')

console.log('⑨ le branchement')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
const lib = fs.readFileSync(path.join(__dirname, 'src/lib/gedRegles.ts'), 'utf8')
voir(/loadInterrupteurTroisCrans\('ged_propositions'\)/.test(fs.readFileSync(path.join(__dirname, 'src/lib/ged.ts'), 'utf8')) && /if \(!regles \|\| affaires === null\) return \[\]/.test(rm), 'derrière ged_propositions ; registre illisible : les règles se taisent')
voir(!/supabase|fetch\(|rpc\(/.test(lib), 'les règles ne lisent ni n\'écrivent rien (fonction pure)')
voir(!/absent/i.test(lib.replace(/^\/\/.*$/gm, '')) && !/absent/i.test(rm.replace(/^\/\/.*$/gm, '')), 'l\'écran ne dit jamais « absent »')
const tout = reglesSansIa(fiche({ statut: 'Sous offre', copropriete: true, dpeDate: '2019-01-01' }), [doc('ERP.pdf', { date: '2026-01-01' })], [], AUJ)
voir(tout.findIndex((a) => a.niveau === 'info') === -1 || tout.findIndex((a) => a.niveau === 'alerte') < tout.findIndex((a) => a.niveau !== 'alerte'), 'les alertes d\'abord, les informations à la fin')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
