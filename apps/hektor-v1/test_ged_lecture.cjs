// GED morceau 6, lots 1 à 4 (12-13/11/2026) : essais hors ligne de la lecture côté écran.  node test_ged_lecture.cjs
// ① le résumé d'une lecture ; ② la date lue fait foi dans la règle des 6 mois ; ③ le branchement : file une à une,
// seuls les types qui ont une fiche, garde RIB avant toute image, l'écran n'écrit jamais une lecture.
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
const { resumeLecture, valeurLue, dateEtatLue, FICHES_LUES } = charger('src/lib/gedLecture.ts')
const { reglesSansIa } = charger('src/lib/gedRegles.ts')
const v = (cle, x, etat = 'lu', rang = 0) => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page: 1, etat, ...x })

console.log('① le résumé')
const dpe = { typeCode: 'diag.dpe', etat: 'lu', valeurs: [v('classe_energie', { valeur: 'D' }), v('classe_ges', { valeur: 'C' }), v('conso_ep', { valeur_num: 214.5 }), v('date_etablissement', { valeur_date: '2025-01-15' }), v('date_validite', { valeur_date: '2035-01-14' }, 'incertain'), v('commune', {}, 'non_vu')] }
const r = resumeLecture(dpe)
voir(r.includes('énergie D, climat C') && r.includes('214,5 kWh') && r.includes('établi le 15/01/2025'), 'DPE : classes, consommation, date')
voir(r.includes("valable jusqu'au 14/01/2035 (?)"), 'une valeur « incertaine » porte un point d\'interrogation')
voir(valeurLue(dpe.valeurs, 'commune') === null, 'une valeur « non vue » ne s\'affiche pas')
voir(resumeLecture({ typeCode: 'diag.erp', etat: 'lu', valeurs: [v('date_etablissement', { valeur_date: '2026-09-02' }), v('commune', { valeur: 'Saint-Étienne' })] }) === 'Lu : établi le 02/09/2026 · Saint-Étienne.', 'état des risques : date et commune')
const ddt = { typeCode: 'diag.dossier', etat: 'lu', valeurs: [v('diagnostics.diagnostic', { valeur: 'amiante' }, 'lu', 0), v('diagnostics.diagnostic', { valeur: 'plomb' }, 'lu', 1), v('dpe_classe_energie', { valeur: 'E' })] }
voir(resumeLecture(ddt) === 'Lu : 2 diagnostics (amiante, plomb) · DPE E.', 'dossier de diagnostics : la liste et la classe')
voir(resumeLecture({ typeCode: 'diag.erp', etat: 'pas_ce_type', valeurs: [] }).includes('pas ce type'), 'l\'IA dit « pas ce type » : on le dit')
voir(resumeLecture({ typeCode: 'diag.erp', etat: 'incomplet', valeurs: [] }).includes('rien pu relever'), 'rien de lu : on le dit, sans inventer')

console.log('①bis le lot 2 : jamais un nom dans le résumé')
const P = (rang, nom, qualite) => [v('personnes.nom', { valeur: nom }, 'lu', rang), v('personnes.prenoms', { valeur: 'Claire' }, 'lu', rang), v('personnes.qualite', { valeur: qualite }, 'lu', rang)]
const taxe = { typeCode: 'justif.taxe', etat: 'lu', valeurs: [v('annee_imposition', { valeur_num: 2026 }), v('montant_total', { valeur_num: 1234 }), v('commune', { valeur: 'Firminy' }), ...P(0, 'MARTIN', 'redevable'), ...P(1, 'DURAND', 'redevable'), ...P(2, 'PETIT', 'usufruitier')] }
const rt = resumeLecture(taxe)
voir(rt === 'Lu : taxe 2026 · 1 234 € · Firminy · 2 redevables, 1 usufruitier.', 'taxe foncière : année, montant, commune, personnes COMPTÉES')
voir(!/MARTIN|DURAND|PETIT|Claire/.test(rt), 'aucun nom ni prénom dans le résumé de la taxe')
const titre = { typeCode: 'justif.titre', etat: 'lu', valeurs: [v('nature_acte', { valeur: 'attestation_succession' }), v('date_acte', { valeur_date: '2019-03-04' }), ...P(0, 'MARTIN', 'heritier'), ...P(1, 'MARTIN', 'heritier'), v('commune', { valeur: 'Firminy' }), v('lots.numero', { valeur: '12' }, 'lu', 0), v('lots.numero', { valeur: '31' }, 'lu', 1)] }
const rti = resumeLecture(titre)
voir(rti === 'Lu : attestation après décès · du 04/03/2019 · 2 héritiers · Firminy · lots 12, 31.', 'titre : nature, date, héritiers comptés, commune, lots')
voir(!/MARTIN|Claire/.test(rti), 'aucun nom dans le résumé du titre')
voir(resumeLecture({ typeCode: 'copro.carnet', etat: 'lu', valeurs: [v('nb_lots_total', { valeur_num: 48 }), v('nb_lots_principaux', { valeur_num: 20 }), v('syndic_nom', { valeur: 'Foncia Loire' }), v('procedure', { valeur: 'administration_provisoire' })] }) === 'Lu : 48 lots dont 20 principaux · syndic Foncia Loire · ⚠ procédure : administration provisoire.', 'fiche synthétique : lots, syndic, la procédure en avant')
voir(resumeLecture({ typeCode: 'copro.appel_fonds', etat: 'lu', valeurs: [v('provision_budget', { valeur_num: 420 }), v('periode', { valeur: 'trimestre' }), v('lots.numero', { valeur: '12' }, 'lu', 0)] }) === 'Lu : provision 420 € (trimestre) · lot 12.', 'appel de fonds : la provision et sa période, le lot')
const cpv = { typeCode: 'transaction.avant_contrat', etat: 'lu', valeurs: [v('date_signature', { valeur_date: '2026-10-15' }), v('prix', { valeur_num: 185000 }), v('honoraires', { valeur_num: 9000 }), v('charge_honoraires', { valeur: 'vendeur' }), v('date_limite_pret', { valeur_date: '2026-12-01' }), v('date_reiteration', { valeur_date: '2027-01-15' }), ...P(0, 'MARTIN', 'vendeur'), ...P(1, 'DURAND', 'acquereur'), ...P(2, 'DURAND', 'acquereur')] }
const rc = resumeLecture(cpv)
voir(rc === 'Lu : signé le 15/10/2026 · 185 000 € · honoraires 9 000 € (vendeur) · prêt avant le 01/12/2026 · acte au plus tard le 15/01/2027 · 1 vendeur, 2 acquéreurs.', 'compromis : date, prix, honoraires et qui paie, prêt, réitération, parties COMPTÉES')
voir(!/MARTIN|DURAND|Claire/.test(rc), 'aucun nom dans le résumé du compromis')
const off = resumeLecture({ typeCode: 'transaction.offre', etat: 'lu', valeurs: [v('montant_offert', { valeur_num: 180000 }), v('base_prix', { valeur: 'fai' }), v('date_offre', { valeur_date: '2026-09-20' }), v('acceptation_vendeur', { valeur: 'acceptee' }), v('date_acceptation', { valeur_date: '2026-09-22' }), v('condition_pret', { valeur: 'oui' }), ...P(0, 'DURAND', 'acquereur')] })
voir(off === 'Lu : offre 180 000 € FAI · du 20/09/2026 · acceptée le 22/09/2026 · sous condition de prêt · 1 acquéreur.' && !/DURAND/.test(off), 'offre : montant et base, date, réponse du vendeur, prêt, acquéreur compté')
voir(resumeLecture({ typeCode: 'copro.pv_ag', etat: 'lu', valeurs: [v('date_ag', { valeur_date: '2026-05-12' }), v('budget_vote', { valeur_num: 85000 }), v('travaux.objet', { valeur: 'ravalement' }, 'lu', 0), v('travaux.objet', { valeur: 'toiture' }, 'lu', 1)] }) === 'Lu : AG du 12/05/2026 · budget 85 000 € · travaux votés : ravalement, toiture.', 'PV d\'AG : date, budget, travaux votés')

console.log('①ter le lot 4 : jamais un nom dans le résumé')
const man = resumeLecture({ typeCode: 'mandat.vente', etat: 'lu', valeurs: [v('numero_mandat', { valeur: '18836' }), v('nature', { valeur: 'exclusif' }), v('date_signature', { valeur_date: '2026-03-02' }), v('prix', { valeur_num: 189000 }), v('honoraires', { valeur_num: 9000 }), v('charge_honoraires', { valeur: 'acquereur' }), ...P(0, 'MARTIN', 'mandant'), ...P(1, 'MARTIN', 'mandant')] })
voir(man === 'Lu : mandat 18836 · exclusif · signé le 02/03/2026 · 189 000 € · honoraires 9 000 € (acquéreur) · 2 mandants.' && !/MARTIN|Claire/.test(man), 'mandat : numéro, nature, date, prix, honoraires et qui paie, mandants COMPTÉS')
const ave = resumeLecture({ typeCode: 'mandat.avenant', etat: 'lu', valeurs: [v('date_avenant', { valeur_date: '2026-10-01' }), v('numero_mandat', { valeur: '18836' }), v('objet', { valeur: 'baisse_prix' }), v('nouveau_prix', { valeur_num: 175000 }), ...P(0, 'MARTIN', 'mandant')] })
voir(ave === 'Lu : avenant du 01/10/2026 · au mandat 18836 · baisse de prix · nouveau prix 175 000 € · 1 mandant.' && !/MARTIN/.test(ave), 'avenant : date, mandat, objet, nouveau prix, mandant compté')
voir(resumeLecture({ typeCode: 'mandat.fin', etat: 'lu', valeurs: [v('numero_mandat', { valeur: '18836' }), v('a_l_initiative_de', { valeur: 'mandant' }), v('date_effet', { valeur_date: '2026-11-30' }), v('motif', { valeur: 'vendu_ailleurs' })] }) === "Lu : fin du mandat 18836 · à l'initiative du mandant · le 30/11/2026 · vendu par ailleurs.", 'fin de mandat : qui, quand, pourquoi (liste fermée)')
const act = resumeLecture({ typeCode: 'transaction.acte', etat: 'lu', valeurs: [v('nature', { valeur: 'attestation' }), v('date_vente', { valeur_date: '2027-01-12' }), v('prix', { valeur_num: 185000 }), v('etude_notariale', { valeur: 'Étude Notairefictif' }), ...P(0, 'MARTIN', 'vendeur'), ...P(1, 'DURAND', 'acquereur')] })
voir(act === 'Lu : attestation de vente · vente du 12/01/2027 · 185 000 € · Étude Notairefictif · 1 vendeur, 1 acquéreur.' && !/MARTIN|DURAND/.test(act), 'acte : nature, date de la VENTE, prix, notaire, parties comptées')
voir(resumeLecture({ typeCode: 'transaction.annulation', etat: 'lu', valeurs: [v('nature', { valeur: 'refus_pret' }), v('date_document', { valeur_date: '2026-11-20' }), v('a_l_initiative_de', { valeur: 'acquereur' }), v('sequestre_restitue', { valeur: 'oui' })] }) === "Lu : refus de prêt · du 20/11/2026 · à l'initiative de l'acquéreur · séquestre restitué.", 'annulation : nature, date, qui, séquestre')
voir(resumeLecture({ typeCode: 'facture.honoraires', etat: 'lu', valeurs: [v('numero_facture', { valeur: 'F-2026-118' }), v('date_facture', { valeur_date: '2027-01-12' }), v('montant_ttc', { valeur_num: 9000 }), v('payeur', { valeur: 'vendeur' })] }) === 'Lu : facture F-2026-118 · du 12/01/2027 · 9 000 € TTC · payée par le vendeur.', 'facture : numéro, date, montant, qui paie (une qualité)')
voir(resumeLecture({ typeCode: 'diag.electricite', etat: 'lu', valeurs: [v('resultat', { valeur: 'anomalies' }), v('date_etablissement', { valeur_date: '2026-02-03' })] }) === 'Lu : anomalies · établi le 03/02/2026.' && resumeLecture({ typeCode: 'diag.amiante', etat: 'lu', valeurs: [v('resultat', { valeur: 'presence' })] }) === 'Lu : ⚠ présence.', 'petits diagnostics : le résultat d\'abord, puis la date')
voir(resumeLecture({ typeCode: 'diag.assainissement', etat: 'lu', valeurs: [v('type', { valeur: 'non_collectif' }), v('conformite', { valeur: 'travaux_obligatoires' }), v('delai_travaux_mois', { valeur_num: 12 }), v('date_controle', { valeur_date: '2024-06-14' })] }) === 'Lu : assainissement individuel · ⚠ travaux obligatoires · travaux sous 12 mois · contrôle du 14/06/2024.', 'assainissement : type, conformité, délai, date')
voir(resumeLecture({ typeCode: 'diag.surface', etat: 'lu', valeurs: [v('surface_carrez', { valeur_num: 64.35 }), v('lots.numero', { valeur: '12' }, 'lu', 0), v('date_mesurage', { valeur_date: '2026-02-03' })] }) === 'Lu : Carrez 64,35 m² · lot 12 · mesuré le 03/02/2026.', 'surfaces : Carrez, lot, date')
voir(resumeLecture({ typeCode: 'copro.reglement', etat: 'lu', valeurs: [v('sous_type', { valeur: 'reglement_et_edd' }), v('date_acte', { valeur_date: '1975-04-18' }), v('nb_lots', { valeur_num: 48 }), v('destination', { valeur: 'mixte' }), v('modificatifs_mentionnes', { valeur: 'oui' })] }) === 'Lu : règlement et état descriptif · du 18/04/1975 · 48 lots · destination : habitation et activités · modificatifs cités.', 'règlement : nature, date, lots, destination, modificatifs')
const elecDate = { typeCode: 'diag.electricite', etat: 'lu', valeurs: [v('date_etablissement', { valeur_date: '2026-02-03' })] }
voir(dateEtatLue(elecDate) === null, 'TÉMOIN : la date d\'un diagnostic électricité ne passe jamais pour celle d\'un état des risques (règle des 6 mois inchangée)')
const taxeAvecDate ={ ...taxe, valeurs: [...taxe.valeurs, v('date_etablissement', { valeur_date: '2026-08-31' })] }
voir(dateEtatLue(taxeAvecDate) === null, 'TÉMOIN : la date d\'une taxe ne passe jamais pour la date d\'un état des risques')

console.log('② la date lue fait foi')
const erpVieux = { typeCode: 'diag.erp', etat: 'lu', valeurs: [v('date_etablissement', { valeur_date: '2025-12-01' })] }
voir(dateEtatLue(erpVieux) === '2025-12-01' && dateEtatLue({ ...erpVieux, etat: 'pas_ce_type' }) === null, 'la date de l\'état ; rien si ce n\'est pas ce type')
const AUJ = new Date(Date.UTC(2026, 10, 12))
const fiche = { statut: 'Sous offre', numeroMandat: '1', typeBien: '2', copropriete: null, anneeConstruction: null, assainissement: null, dpeConso: 150, dpeGes: 20, dpeNonConcerne: false, diffusable: false, dpeDate: null, nbLots: null, charges: null, prixAncien: null, prixNouveau: null, prixChangeLe: null, mandatDebut: null, mandatFin: null }
const mandat = { nom: 'Mandat.pdf', typeCode: null, date: null, signature: 'signed' }
const al = reglesSansIa(fiche, [mandat, { nom: 'ERP.pdf', typeCode: null, date: '2026-11-10', signature: null, dateEtat: '2025-12-01' }], [], AUJ).filter((a) => a.code === 'N4')
voir(al.length === 1 && al[0].texte.includes('établi le 01/12/2025'), 'déposé hier mais ÉTABLI il y a 11 mois : la règle sonne, sur la date lue')
voir(!reglesSansIa(fiche, [mandat, { nom: 'ERP.pdf', typeCode: null, date: '2026-01-10', signature: null, dateEtat: '2026-10-01' }], [], AUJ).some((a) => a.code === 'N4'), 'TÉMOIN : déposé il y a 10 mois mais établi en octobre : se tait')

console.log('③ le branchement')
const depot = fs.readFileSync(path.join(__dirname, 'src/DepotDocuments.tsx'), 'utf8')
const ia = fs.readFileSync(path.join(__dirname, 'src/lib/gedClassementIa.ts'), 'utf8')
const lect = fs.readFileSync(path.join(__dirname, 'src/lib/gedLecture.ts'), 'utf8')
voir(FICHES_LUES.size === 25 &&['copro.pv_ag', 'transaction.offre', 'mandat.avenant', 'diag.surface', 'facture.honoraires', 'copro.reglement'].every((c) => FICHES_LUES.has(c)), 'lots 1 à 4 : vingt-cinq types lus')
voir(!FICHES_LUES.has('justif.rib') && !FICHES_LUES.has('justif.identite') && !FICHES_LUES.has('transaction.financement') && !FICHES_LUES.has('bien.entretien'), 'TÉMOIN : ni le RIB, ni les pièces des personnes, ni les factures d\'énergie (entretien)')
const { pagesAImager } = (() => {
  const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, 'src/lib/gedClassementIa.ts')], bundle: true, write: false, format: 'cjs', platform: 'node',
    external: ['react', './supabase', './ged', 'pdfjs-dist', 'pdfjs-dist/*', 'pdf-lib'], define: { 'import.meta.env': '{}' } }).outputFiles[0].text
  const m = { exports: {} }
  new Function('module', 'exports', 'require', code)(m, m.exports, (n) => (n === './supabase' ? { hasSupabaseEnv: false, supabase: null } : n === './ged' ? {} : require(n)))
  return m.exports
})()
voir(JSON.stringify(pagesAImager(40, 6, 2, true)) === '[39,40]' && JSON.stringify(pagesAImager(40, 6, 2, false)) === '[1,2,3,4,39,40]', 'compromis : en texte, les 2 dernières pages en image ; scanné, les 4 premières et les 2 dernières')
voir(JSON.stringify(pagesAImager(1, 4, 1, true)) === '[1]' && JSON.stringify(pagesAImager(3, 6, 2, false)) === '[1,2,3]', 'offre d\'une page : sa page en image même avec du texte ; un petit scan : toutes ses pages')
voir(JSON.stringify(pagesAImager(12, 6, 2, true)) === '[11,12]' && JSON.stringify(pagesAImager(1, 4, 1, false)) === '[1]' && JSON.stringify(pagesAImager(5, 4, 1, false)) === '[1,2,3,5]', 'lot 4 : mandat en texte = ses 2 pages de signatures ; avenant scanné de 5 pages = les 3 premières et la dernière')
voir(JSON.stringify(pagesAImager(12, 4, 0, true)) === '[]' && JSON.stringify(pagesAImager(12, 4, 0, false)) === '[1,2,3,4]' && JSON.stringify(pagesAImager(30, 6, 0, false)) === '[1,2,3,4,5,6]', 'TÉMOIN : lots 1 et 2 inchangés (texte seul ; scan = les premières pages)')
const srv = fs.readFileSync(path.join(__dirname, '../../backend/app/services/openai_ged_lecture_service.py'), 'utf8')
// même réglage qu'au serveur : chaque table lue dans les DEUX sources, comparée clé par clé (lot 4 : 13/11)
const table = (src, debut, motif) => {
  const i = src.indexOf(debut)
  const bloc = i < 0 ? '' : src.slice(i, src.indexOf('}', i))
  return JSON.stringify([...bloc.matchAll(motif)].map((m) => [m[1], m[2] === 'MAX_PAGES_HD' ? 6 : Number(m[2])]).sort())
}
const front = (nom) => table(ia, `${nom}: Record<string, number> = {`, /'([\w.]+)': (\d+)/g)
const serveur = (nom) => table(srv, `\n${nom} = {`, /"([\w.]+)": (\w+)/g)
voir(front('FIN_EN_IMAGE_PAR_TYPE') === serveur('FIN_EN_IMAGE') && front('FIN_EN_IMAGE_PAR_TYPE').includes('mandat.avenant'), 'les pages de FIN en image : même table à l\'écran et au serveur (lot 4 compris)')
voir(front('PAGES_HD_PAR_TYPE') === serveur('PAGES_HD') && front('PAGES_HD_PAR_TYPE').includes('copro.reglement'), 'les pages en haute définition : même table à l\'écran et au serveur')
voir(/'transaction\.avant_contrat': 80000/.test(ia) && /'mandat\.vente': 40000/.test(ia) && /'transaction\.acte': 40000/.test(ia) && /'copro\.reglement': 40000/.test(ia), 'le texte long : compromis 80 000 ; mandat, acte, règlement 40 000 (comme texte_max au serveur)')
voir([...FICHES_LUES].every((c) => srv.includes(`"${c}"`)), 'chaque type lu à l\'écran a sa fiche au serveur')
voir(/'justif\.titre': 6,/.test(ia) && /preparerLecture\(ligne\.file, ligne\.type\)/.test(depot), 'le titre : 6 pages en image, le type est passé à la préparation')
voir(/\.slice\(0, texteMax\)/.test(ia) && /for \(const n of pagesAImager\(nbPages, pagesHd, fin, avecTexte\)\)/.test(ia) && /LECTURE_TEXTE_MAX = 20000/.test(ia) && /LECTURE_PAGES_HD = 4/.test(ia), 'le texte et les pages suivent le réglage du type (les autres gardent 20 000 et 4)')
voir((depot.match(/lectureIa && typeLu\(ligne\.type\) \? \{ etat: 'attente' \} : null/g) ?? []).length === 2 && !/lectureIa && FICHES_LUES\.has\(ligne\.type\)/.test(depot), 'une lecture n\'est demandée que si l\'interrupteur est allumé et que le type a une fiche (les deux endroits)')
voir(/l\.lecture\?\.etat === 'lecture'\)\) return/.test(depot), 'une lecture à la fois')
const prep = ia.slice(ia.indexOf('export async function preparerLecture'), ia.indexOf('export type ResultatLecture'))
voir(prep.indexOf('nomDitRib(file.name)') < prep.indexOf('imageHd(') && prep.indexOf('texteDitRib(') < prep.indexOf('page.render('), 'la garde RIB passe avant toute image')
voir(!/\.insert\(|\.upsert\(|\.update\(|\.rpc\(/.test(lect) && !/app_ged_lecture[^\n]*insert/.test(depot), 'l\'écran n\'écrit jamais une lecture (le serveur seul)')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
voir(/Lu par l'IA : \$\{lus\.length\}/.test(rm) && /\.filter\(\(d\) => d\.present_in_hektor !== false && lectures\.has\(d\.id\)\)/.test(rm), 'après rechargement : TOUT ce qui a été lu se retrouve (« Lu par l\'IA »), quel que soit le moment de la pièce')

console.log('④ morceau 9, lot 9a : les pièces des personnes')
const { FICHES_PERSONNES_LUES } = charger('src/lib/gedLecture.ts')
voir(FICHES_PERSONNES_LUES.size === 2 && FICHES_PERSONNES_LUES.has('justif.identite') && FICHES_PERSONNES_LUES.has('transaction.renseignements') && FICHES_LUES.size === 25,
  'deux types À PART (identité, fiche de renseignements) ; les 25 types lus ne bougent pas')
voir(!FICHES_PERSONNES_LUES.has('justif.rib') && !FICHES_PERSONNES_LUES.has('transaction.financement') && !FICHES_PERSONNES_LUES.has('justif.etat_civil'),
  'TÉMOIN : ni le RIB, ni le financement, ni l\'état civil (9d)')
const fp = srv.slice(srv.indexOf('FICHES_PERSONNES: dict'), srv.indexOf('PRIVES = '))
voir([...FICHES_PERSONNES_LUES].every((c) => fp.includes(`"${c}": {`)), 'chaque pièce lue à l\'écran a sa fiche au serveur, dans FICHES_PERSONNES')
voir(/const typeLu = \(code: string\) => FICHES_LUES\.has\(code\) \|\| \(lecturePersonnes && FICHES_PERSONNES_LUES\.has\(code\)\)/.test(depot) && /useGedLecturePersonnes\(\)/.test(depot),
  'une pièce des personnes n\'est demandée que si SON interrupteur est ouvert')
const ged = fs.readFileSync(path.join(__dirname, 'src/lib/ged.ts'), 'utf8')
voir(/loadInterrupteurTroisCrans\('ged_lecture_personnes'\)/.test(ged), 'l\'interrupteur ged_lecture_personnes, à trois crans')
const Pc = (rang, x) => [v('pieces.nature', { valeur: x.nature }, 'lu', rang), v('pieces.nom', { valeur: 'SPECIMEN' }, 'lu', rang), v('pieces.prenoms', { valeur: 'Jeanne' }, 'lu', rang),
  v('pieces.date_naissance', { valeur_date: '1938-04-02' }, 'lu', rang), v('pieces.date_fin_validite', { valeur_date: x.fin }, x.etat ?? 'lu', rang)]
const cni = resumeLecture({ typeCode: 'justif.identite', etat: 'lu', valeurs: [...Pc(0, { nature: 'cni_nouveau_modele', fin: '2033-03-03' })] })
voir(cni === "Lu : carte d'identité valable jusqu'au 03/03/2033.", 'pièce d\'identité : la nature et la fin de validité')
voir(!/SPECIMEN|Jeanne|1938|02\/04/.test(cni), 'aucun nom, prénom ni date de naissance dans le résumé')
const deux = resumeLecture({ typeCode: 'justif.identite', etat: 'lu', valeurs: [...Pc(0, { nature: 'cni_ancien_modele', fin: '2022-06-13' }), ...Pc(1, { nature: 'passeport', fin: '2030-01-01', etat: 'incertain' })] })
voir(deux === "Lu : 2 pièces · carte d'identité valable jusqu'au 13/06/2022 · passeport valable jusqu'au 01/01/2030 (?).", 'deux pièces dans un fichier : comptées, une par une, l\'incertain marqué')
const rens = resumeLecture({ typeCode: 'transaction.renseignements', etat: 'lu', valeurs: [v('date_document', { valeur_date: '2026-10-01' }), ...P(0, 'MARTIN', 'vendeur'), ...P(1, 'MARTIN', 'vendeur'),
  v('personnes.adresse', { valeur: '3 rue des Essais' }, 'lu', 0), v('personnes.date_naissance', { valeur_date: '1950-01-01' }, 'lu', 0)] })
voir(rens === 'Lu : fiche de renseignements · du 01/10/2026 · 2 vendeurs.' && !/MARTIN|Claire|Essais|1950/.test(rens), 'fiche de renseignements : la date, les personnes COMPTÉES ; ni nom, ni adresse, ni naissance')
voir(![lect, depot, rm, ged].some((t) => /pieces\.(numero|date_delivrance|autorite_delivrance)|ged_prive|app_ged_piece_privee/.test(t)), 'l\'écran ne connaît ni le numéro ni la délivrance de la pièce (registre ged_prive)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
