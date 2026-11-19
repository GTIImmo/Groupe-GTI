// GED morceau 9, lot 9d-2 (16/11/2026) : essais hors ligne des règles de l'ÉTAT CIVIL lu.
//   node test_ged_regles_etat_civil.cjs
// ① la pièce lue ; ② P9 le conjoint, P10 le décès d'un mandant et la mesure de protection : chaque règle sonne sur son
// cas ET son témoin se tait ; ③ le branchement (À regarder, rien n'écrit, la 1re page seule).
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const charger = (f) => {
  const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, f)], bundle: true, write: false, format: 'cjs', platform: 'node', external: ['./supabase'] }).outputFiles[0].text
  const m = { exports: {} }
  new Function('module', 'exports', 'require', code)(m, m.exports, (n) => (n === './supabase' ? { hasSupabaseEnv: false, supabase: null } : require(n)))
  return m.exports
}
const { reglesEtatCivil, etatsCivilsLusDe } = charger('src/lib/gedReglesEtatCivil.ts')
const v = (cle, x, etat = 'lu', rang = 0) => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page: 1, etat, ...x })
const doc = (nom, typeCode, valeurs, etat = 'lu') => ({ nom, lecture: { typeCode, etat, luLe: null, valeurs } })
const personnes = (liste) => liste.flatMap(([q, n, p], r) => [v('personnes.qualite', { valeur: q }, 'lu', r), v('personnes.nom', { valeur: n }, 'lu', r), v('personnes.prenoms', { valeur: p }, 'lu', r)])
const ec = (nom, nature, date, liste = []) => doc(nom, 'justif.etat_civil', [v('nature', { valeur: nature }), ...(date ? [v('date_acte', { valeur_date: date })] : []), ...personnes(liste)])
const PAUL = ['epoux', 'DUPONT', 'Paul'], MARIE = ['epoux', 'MARTIN', 'Marie']
const mariage = (nom = 'Acte de mariage.pdf', nature = 'acte_mariage') => ec(nom, nature, '1987-06-20', [PAUL, MARIE])
const mandat = (mandants) => doc('Mandat.pdf', 'mandat.vente', personnes(mandants.map(([n, p]) => ['mandant', n, p])))
const BIEN = [{ nom: 'DUPONT', prenom: 'Paul' }]
const R = (docs, bien = BIEN) => reglesEtatCivil(docs, bien)
const codes = (al) => al.map((a) => `${a.code}/${a.niveau}`).sort().join(',')
const textes = (al) => al.map((a) => a.texte).join(' | ')

console.log('① la pièce lue')
const lu = etatsCivilsLusDe([mariage()])[0]
voir(lu.nature === 'acte_mariage' && lu.date.toISOString().slice(0, 10) === '1987-06-20' && lu.personnes.length === 2, 'la nature, la date, les deux époux')
voir(etatsCivilsLusDe([{ ...mariage(), lecture: { ...mariage().lecture, etat: 'incomplet' } }]).length === 0, 'TÉMOIN : une lecture incomplète ne compte pas')
voir(codes(R([])) === '' && codes(R([doc('x.pdf', 'diag.dpe', [])])) === '', 'TÉMOIN : aucune pièce d\'état civil lue -> rien')

console.log('② P9 -- le conjoint')
const p9 = R([mariage()])
voir(codes(p9) === 'P9/alerte' && /Paul DUPONT est marié\(e\) depuis le 20\/06\/1987 avec Marie MARTIN/.test(textes(p9)), 'mandant marié, conjoint absent de la fiche -> alerte')
voir(codes(R([mariage()], [...BIEN, { nom: 'MARTIN', prenom: 'Marie' }])) === '', 'TÉMOIN : les deux époux sur la fiche -> rien')
voir(codes(R([mariage(), mandat([['DUPONT', 'Paul'], ['MARTIN', 'Marie']])])) === '', 'TÉMOIN : le conjoint a signé le mandat lu -> rien')
voir(codes(R([mariage(), mariage('Livret.pdf', 'livret_famille')])) === 'P9/alerte', 'l\'acte ET le livret -> UNE ligne par couple')
voir(codes(R([mariage(), ec('Divorce.pdf', 'divorce', '2010-01-15', [PAUL, MARIE])])) === '', 'TÉMOIN : un divorce lu -> rien')
voir(codes(R([ec('Pacs.pdf', 'pacs', '2015-05-05', [['partenaire', 'DUPONT', 'Paul'], ['partenaire', 'MARTIN', 'Marie']])])) === '', 'TÉMOIN : un PACS ne crie pas (l\'article 215 vaut pour des époux)')
voir(codes(R([mariage(), ec('Deces.pdf', 'acte_deces', '2020-02-02', [['defunt', 'MARTIN', 'Marie']])])) === '', 'TÉMOIN : le conjoint est décédé -> rien')
voir(codes(R([mariage()], [{ nom: 'DUPONT', prenom: '' }])) === '', 'TÉMOIN : une fiche sans prénom -> on ne sait pas, rien')
voir(codes(R([mariage()], [{ nom: 'ROBERT', prenom: 'Luc' }])) === '', 'TÉMOIN : aucun des époux n\'est au dossier -> rien (ce n\'est pas notre affaire)')
voir(codes(R([ec('Acte.pdf', 'acte_mariage', '1987-06-20', [PAUL, ['epoux', 'DUPONT', 'Marie']])])) === 'P9/alerte', 'l\'épouse lue sous le nom du mari (« Marie DUPONT ») reste une autre personne -> alerte')

console.log('③ P10 -- le décès d\'un mandant, la protection')
const deces = R([ec('Deces.pdf', 'acte_deces', '2026-10-30', [['defunt', 'DUPONT', 'Paul']])])
voir(codes(deces) === 'P10/alerte' && /Paul DUPONT, au dossier, est décédé\(e\) le 30\/10\/2026 : un mandat prend fin/.test(textes(deces)), 'un mandant décédé -> alerte (article 2003)')
voir(codes(R([ec('Deces.pdf', 'acte_deces', '2026-10-30', [['defunt', 'ROBERT', 'Luc']])])) === '', 'TÉMOIN : le défunt n\'est pas au dossier -> rien')
voir(codes(R([ec('Deces.pdf', 'acte_deces', '2026-10-30', [['defunt', 'ROBERT', 'Luc']]), mandat([['ROBERT', 'Luc']])], [])) === 'P10/alerte', 'le défunt est mandant au MANDAT LU (pas sur la fiche) -> alerte')
voir(codes(R([ec('Deces 1.pdf', 'acte_deces', '2026-10-30', [['defunt', 'DUPONT', 'Paul']]), ec('Deces 2.pdf', 'acte_deces', '2026-10-30', [['defunt', 'DUPONT', 'Paul']])])) === 'P10/alerte', 'le même acte déposé deux fois -> UNE ligne')
const prot = R([ec('Jugement.pdf', 'protection', null)])
voir(codes(prot) === 'P10/alerte' && /Une mesure de protection juridique est au dossier$/.test(textes(prot)), 'une mesure de protection -> alerte, SANS nom ni détail')
voir(/\(2 pièces\)/.test(textes(R([ec('J1.pdf', 'protection', null), ec('J2.pdf', 'protection', null)]))), 'deux pièces de protection -> une ligne « (2 pièces) »')

voir(!/vérifier/.test(p9[0].pourquoi) && !/vérifier/.test(prot[0].pourquoi), 'l\'explication ne redit pas « vérifier » (l\'écran met déjà « à vérifier : » devant une alerte)')

// ⑤ (16/11, épreuve réelle) : « Acte de mariage », « Acte de décès » étaient pris pour un TITRE par leur nom
// (\bacte\b « probable »). Corrigé dans la SOURCE (phase2/checks/ged1_mesure_nomenclature.py), fichier refabriqué.
console.log('⑤ le type par le nom : un acte d\'état civil n\'est pas un titre')
const { typeParNom } = charger('src/lib/gedTypeParNom.ts')
const tp = (n) => `${typeParNom(n).code}/${typeParNom(n).force}`
voir(['Acte de mariage.pdf', 'acte de deces 13.pdf', 'Acte deces papa 001.jpg', 'acte mariage.pdf', 'Extrait acte de naissance Stéphanie.pdf', 'Certificat de décès.pdf'].every((n) => tp(n) === 'justif.etat_civil/sur'),
  'acte de mariage, de décès (avec ou sans « de »), extrait de naissance, certificat de décès -> état civil, sûr')
voir(tp('Titre de propriete et acte de deces.pdf') === 'justif.titre/sur', 'TÉMOIN : un nom qui dit AUSSI le titre reste un titre (règle sûre du titre d\'abord)')
voir(tp('Acte de vente Dupont.pdf') === 'transaction.acte/sur' && tp('Acte notarie.pdf') === 'justif.titre/probable' && tp('Acte de notoriete.pdf') === 'justif.titre/sur',
  'TÉMOIN : acte de vente, acte notarié, notoriété ne bougent pas')
voir(tp('Livret de famille.pdf') === 'justif.etat_civil/sur', 'TÉMOIN : le livret de famille reste état civil')

console.log('④ le branchement')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
const regles = fs.readFileSync(path.join(__dirname, 'src/lib/gedReglesEtatCivil.ts'), 'utf8')
const ia = fs.readFileSync(path.join(__dirname, 'src/lib/gedClassementIa.ts'), 'utf8')
voir(/reglesEtatCivil\(docsLus, personnesCompletes\)/.test(rm), 'branchée avec les autres règles sous « À regarder » (même interrupteur)')
voir(!/editAnnonce|editContact|ecrire|gedDecider/.test(regles), 'on SIGNALE, on n\'écrit rien')
const lecture = regles.slice(regles.indexOf('export function etatsCivilsLusDe'), regles.indexOf('const MARIAGES'))
const cles = [...lecture.matchAll(/(?:texteLu|dateLue|nombreLu)\([^,]+, '([\w.]+)'\)/g)].map((m) => m[1]).sort().join(',')
voir(cles === 'date_acte,nature' && /personnesLuesDe\(d\.lecture\)/.test(lecture), 'TÉMOIN : de la pièce on ne lit que la nature, la date et les personnes')
voir(/PREMIERE_PAGE_SEULE = new Set\(\['transaction\.financement', 'justif\.etat_civil'\]\)/.test(ia), 'l\'écran n\'envoie que la 1re page de l\'état civil')

console.log(`\n${ok} verts, ${ko} rouges`)
process.exit(ko ? 1 : 0)
