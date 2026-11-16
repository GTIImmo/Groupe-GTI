// GED morceau 9, lot 9d (16/11/2026) : essais hors ligne des règles du FINANCEMENT lu.
//   node test_ged_regles_financement.cjs
// ① la pièce lue ; ② P7 le prêt à la date limite (et la pièce manquante à 7 jours, FIN-1), P8 l'emprunteur est
// l'acquéreur : chaque règle sonne sur son cas ET son témoin se tait ; ③ le branchement (À regarder, la 1re page seule).
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
const { reglesFinancement, financementsLusDe } = charger('src/lib/gedReglesFinancement.ts')
const v = (cle, x, etat = 'lu', rang = 0) => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page: 1, etat, ...x })
const doc = (nom, typeCode, valeurs, etat = 'lu') => ({ nom, lecture: { typeCode, etat, luLe: null, valeurs } })
const AUJ = new Date(Date.UTC(2026, 10, 16))
// le compromis lu : condition de prêt, date limite, acquéreur DUPONT Paul
const cpv = (limite, x = {}) => doc(x.nom ?? 'Compromis.pdf', 'transaction.avant_contrat', [
  v('condition_pret', { valeur: x.condition ?? 'oui' }), v('date_signature', { valeur_date: x.signature ?? '2026-09-15' }),
  ...(limite ? [v('date_limite_pret', { valeur_date: limite })] : []), v('prix', { valeur_num: 200000 }),
  v('personnes.nom', { valeur: 'DUPONT' }), v('personnes.prenoms', { valeur: 'Paul' }), v('personnes.qualite', { valeur: 'acquereur' }),
])
// une pièce de financement lue : nature, date, emprunteurs
const fin = (nom, nature, date, emprunteurs = [['DUPONT', 'Paul']], etatNature = 'lu') => doc(nom, 'transaction.financement', [
  ...(nature ? [v('nature', { valeur: nature }, etatNature)] : []), ...(date ? [v('date_document', { valeur_date: date })] : []),
  ...emprunteurs.flatMap(([n, p], r) => [v('personnes.nom', { valeur: n }, 'lu', r), v('personnes.prenoms', { valeur: p }, 'lu', r), v('personnes.qualite', { valeur: 'emprunteur' }, 'lu', r)]),
])
const COMPROMIS = { kind: 'compromis', state: 'accepted', date: '2026-09-15', dateActe: null, id: 1, montant: 200000, acquereurs: [{ nom: 'DUPONT', prenom: 'Paul' }] }
// les documents du dossier pour la PRÉSENCE (type décidé, ou nom)
const pres = (lus, anciens = []) => [...lus.map((d) => ({ nom: d.nom, typeCode: d.lecture.typeCode, date: null, signature: null })), ...anciens.map((nom) => ({ nom, typeCode: null, date: null, signature: null }))]
const R = (lus, opts = {}) => reglesFinancement(pres(lus, opts.anciens), lus, opts.affaires ?? [COMPROMIS], opts.auj ?? AUJ)
const codes = (al) => al.map((a) => `${a.code}/${a.niveau}`).sort().join(',')
const textes = (al) => al.map((a) => a.texte).join(' | ')

console.log('① la pièce lue')
const f = financementsLusDe([fin('Offre.pdf', 'offre_de_pret', '2026-10-02', [['DUPONT', 'Paul'], ['DURAND', 'Léa']])])[0]
voir(f.nature === 'offre_de_pret' && f.date.toISOString().slice(0, 10) === '2026-10-02' && f.emprunteurs.length === 2, 'la nature, la date, les deux emprunteurs')
voir(financementsLusDe([fin('x.pdf', 'refus', null, [], 'incertain')])[0].nature === null, 'TÉMOIN : une nature lue avec doute est inconnue')
voir(financementsLusDe([{ ...fin('x.pdf', 'refus', null), lecture: { ...fin('x.pdf', 'refus', null).lecture, etat: 'incomplet' } }]).length === 0, 'TÉMOIN : une lecture incomplète ne compte pas')

console.log('② P7 -- le prêt à la date limite')
voir(codes(R([cpv('2026-11-20')])) === 'P7/piece' && /dans 4 jours/.test(textes(R([cpv('2026-11-20')]))), 'FIN-1 : limite dans 4 jours, aucune pièce de financement -> « pièce » à déposer')
voir(R([cpv('2026-11-20')])[0].typeADeposer === 'transaction.financement', 'elle propose de déposer un financement')
voir(codes(R([cpv('2026-11-30')])) === '', 'TÉMOIN : limite dans 14 jours -> rien encore')
voir(codes(R([cpv('2026-11-10')])) === 'P7/alerte' && /est passée : aucune pièce/.test(textes(R([cpv('2026-11-10')]))), 'limite PASSÉE sans aucune pièce -> alerte')
voir(codes(R([cpv('2026-11-20')], { anciens: ['offre de pret DUPONT.pdf'] })) === '', 'TÉMOIN : un ancien document reconnu à son NOM fait taire FIN-1')
voir(codes(R([cpv('2026-11-20', { condition: 'non' })])) === '', 'TÉMOIN : compromis sans condition de prêt -> rien')
voir(codes(R([cpv('2026-11-20')], { affaires: [{ ...COMPROMIS, state: 'cancelled' }] })) === '', 'TÉMOIN : compromis annulé -> rien')
voir(codes(R([cpv('2026-11-20')], { affaires: [COMPROMIS, { ...COMPROMIS, id: 2 }] })) === '', 'TÉMOIN : deux compromis vivants indiscernables -> on ne sait pas lequel -> rien')
const refus = R([cpv('2026-12-20'), fin('Refus.pdf', 'refus', '2026-11-05')])
voir(codes(refus) === 'P7/alerte' && /Refus de prêt lu \(du 05\/11\/2026\)/.test(textes(refus)), 'un REFUS lu -> alerte (condition suspensive)')
voir(codes(R([fin('Refus.pdf', 'refus', null)])) === 'P7/alerte', 'le refus parle même sans compromis lu (compromis vivant au registre)')
voir(codes(R([cpv('2026-11-10'), fin('Accord.pdf', 'accord_de_principe', '2026-11-01')])) === '', 'TÉMOIN : limite passée MAIS accord lu daté AVANT -> rien')
const apres = R([cpv('2026-11-10'), fin('Offre.pdf', 'offre_de_pret', '2026-11-12')])
voir(codes(apres) === 'P7/info' && /après la date limite/.test(textes(apres)), 'accord daté APRÈS la limite -> information (prorogation ?)')
voir(codes(R([cpv('2026-11-10'), fin('Offre.pdf', 'offre_de_pret', null)])) === '', 'TÉMOIN : un accord sans date lue -> on ne sait pas -> rien')
const simuPassee = R([cpv('2026-11-10'), fin('Simu.pdf', 'simulation', '2026-09-01')])
voir(codes(simuPassee) === 'P7/alerte' && /aucune offre ni accord de prêt lu$/.test(textes(simuPassee)), 'limite passée, seule une simulation lue -> alerte « aucune offre ni accord »')
const nonLue = R([cpv('2026-11-10'), fin('Simu.pdf', 'simulation', '2026-09-01')], { anciens: ['accord de principe CIC.pdf'] })
voir(codes(nonLue) === 'P7/info' && /1 pièce de financement non lue/.test(textes(nonLue)), 'TÉMOIN : une pièce NON lue au dossier (peut-être l\'offre) -> information, pas alerte')
const simu = R([cpv('2026-12-20'), fin('Simu.pdf', 'simulation', '2026-09-01')])
voir(codes(simu) === 'P7/info' && /simulation/.test(textes(simu)), 'limite à venir, seule une simulation -> information')
voir(codes(R([cpv('2026-12-20'), fin('Simu.pdf', 'simulation', '2026-09-01'), fin('Offre.pdf', 'offre_de_pret', '2026-10-01')])) === '', 'TÉMOIN : une simulation ET une offre -> rien')

console.log('③ P8 -- l\'emprunteur est l\'acquéreur')
const autre = R([cpv('2026-12-20'), fin('Offre.pdf', 'offre_de_pret', '2026-10-01', [['MARTIN', 'Luc']])])
voir(codes(autre) === 'P8/alerte' && /Luc MARTIN n'est au nom d'aucun acquéreur/.test(textes(autre)), 'emprunteur inconnu des acquéreurs -> alerte')
voir(codes(R([cpv('2026-12-20'), fin('Offre.pdf', 'offre_de_pret', '2026-10-01', [['DUPONT', 'Paul'], ['MARTIN', 'Luc']])])) === '', 'TÉMOIN : un des emprunteurs est acquéreur (co-emprunteur) -> rien')
voir(codes(R([fin('Offre.pdf', 'offre_de_pret', '2026-10-01', [['DUPONT', 'Paul']])])) === '', 'TÉMOIN : l\'acquéreur du REGISTRE suffit (sans compromis lu)')
const deux = R([fin('Offre.pdf', 'offre_de_pret', '2026-10-01', [['MARTIN', 'Luc']]), fin('Offre bis.pdf', 'offre_de_pret', '2026-10-01', [['MARTIN', 'Luc']])])
voir(codes(deux) === 'P8/alerte' && /\(2 pièces\)/.test(textes(deux)), 'la même pièce déposée deux fois -> UNE ligne, « (2 pièces) »')
voir(codes(R([fin('Offre.pdf', 'offre_de_pret', '2026-10-01', [['MARTIN', 'Luc']])], { affaires: [{ ...COMPROMIS, acquereurs: [] }] })) === '', 'TÉMOIN : aucun acquéreur connu -> on ne juge pas')
voir(codes(R([fin('Offre.pdf', 'offre_de_pret', '2026-10-01', [['MARTIN', 'Luc']])], { affaires: [] })) === '', 'TÉMOIN : aucun compromis vivant -> rien du tout')
voir(codes(R([fin('Refus.pdf', 'refus', '2026-11-05')], { affaires: [{ ...COMPROMIS, state: 'cancelled' }] })) === '', 'TÉMOIN : un refus de prêt sur un compromis ANNULÉ -> rien (la vente est déjà tombée)')

console.log('④ le branchement')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
const regles = fs.readFileSync(path.join(__dirname, 'src/lib/gedReglesFinancement.ts'), 'utf8')
const ia = fs.readFileSync(path.join(__dirname, 'src/lib/gedClassementIa.ts'), 'utf8')
voir(/reglesFinancement\(docs, docsLus, affaires, new Date\(\)\)/.test(rm), 'branchée avec les autres règles sous « À regarder » (même interrupteur)')
const lecturePiece = regles.slice(regles.indexOf('export function financementsLusDe'), regles.indexOf('const ACCORDS'))
const clesLues = [...lecturePiece.matchAll(/(?:texteLu|dateLue|nombreLu)\([^,]+, '([\w.]+)'\)/g)].map((m) => m[1]).sort().join(',')
voir(clesLues === 'date_document,nature' && /personnesLuesDe\(d\.lecture\)/.test(lecturePiece) && !/nombreLu/.test(lecturePiece),
  'TÉMOIN : de la pièce de financement, on ne lit que la nature, la date et les emprunteurs -- aucun nombre')
voir(!/editAnnonce|editContact|ecrire|gedDecider/.test(regles), 'on SIGNALE, on n\'écrit rien')
voir(/PREMIERE_PAGE_SEULE = new Set\(\['transaction\.financement'\]\)/.test(ia) && /envoyables = uneSeule \? textes\.slice\(0, 1\) : textes/.test(ia), 'l\'écran n\'envoie que la 1re page du financement (texte et image)')
voir(/texteDitRib\(textes\.join\('\\n'\)\)/.test(ia) && ia.indexOf("texteDitRib(textes.join('\\n'))") < ia.indexOf('const envoyables'), 'la garde RIB lit TOUTES les pages AVANT de couper à la 1re')

// ⑤ (16/11, épreuve réelle) : une offre de prêt qui porte un IBAN restait rangée « RIB » par la fenêtre de dépôt.
// Décision de Frédéric : elle reste « Financement » quand son NOM le dit ; un nom muet garde le pré-choix RIB.
console.log('⑤ une offre avec IBAN reste « Financement » (le nom le dit)')
const { typeParNom } = charger('src/lib/gedTypeParNom.ts')
const depot = fs.readFileSync(path.join(__dirname, 'src/DepotDocuments.tsx'), 'utf8')
voir(typeParNom('ESSAI9D Accord de principe SPECIMEN avec IBAN.pdf').code === 'transaction.financement' && typeParNom('Offre de pret CIC.pdf').code === 'transaction.financement',
  'le nom d\'une offre ou d\'un accord de prêt propose « Financement » (le cas de l\'épreuve du 16/11)')
voir(/const financementParNom = l\.type === 'transaction\.financement'/.test(depot) && /prep\.rib && l\.etat === 'pret' && !l\.typeTouche && !l\.typeAttenduPose && !financementParNom && parCode\.has\('justif\.rib'\)/.test(depot),
  'un IBAN trouvé ne remplace PAS « Financement » proposé par le nom')
voir(typeParNom('scan001.pdf').code === null && /\? avecType\(base, 'justif\.rib'\) : base/.test(depot), 'TÉMOIN : un nom muet avec un IBAN garde le pré-choix « RIB »')
voir(/if \(nomDitRib\(file\.name\)\)/.test(ia) && /if \(texteDitRib\(textes\.join\('\\n'\)\)\) return \{ lisible: false/.test(ia), 'et la lecture la refuse toujours (garde RIB inchangée)')

console.log(`\n${ok} verts, ${ko} rouges`)
process.exit(ko ? 1 : 0)
