// GED lot 10c (17/11/2026) : essais hors ligne de « Ce que dit le compromis ».  node test_ged_bilan.cjs
// ① le bilan (gedBilanCompromis.ts), sur le cas RÉEL de 18849 et ses témoins ; ② la liste des conditions après les choix ;
// ③ la note Vrai / Faux déduite des choix ; ④ le branchement : chaque champ par SON chemin (Hektor par la modale
// « Modifier le compromis », les conditions chez nous), rien d'écrit avant « Enregistrer ».
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, 'src/lib/gedBilanCompromis.ts')], bundle: true, write: false, format: 'cjs', platform: 'node' }).outputFiles[0].text
const m = { exports: {} }
new Function('module', 'exports', 'require', code)(m, m.exports, require)
const { bilanCompromis, conditionsApres, verdictDesChoix } = m.exports

const v = (cle, x, rang = 0, page = 9) => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page, etat: 'lu', ...x })
const cv = (n, d, r) => [v('conditions.nature', { valeur: n }, r, 12), ...(d ? [v('conditions.date_limite', { valeur_date: d }, r, 12)] : [])]
// le compromis de 18849 tel que lu le 17/11 (lecture d41c01f9)
const lu18849 = [v('date_signature', { valeur_date: '2026-10-23' }, 0, 38), v('date_reiteration', { valeur_date: '2027-02-01' }, 0, 10), v('prix', { valeur_num: 124000 }, 0, 4),
  v('prix_net_vendeur', { valeur_num: 115000 }, 0, 4), v('honoraires', { valeur_num: 9000 }, 0, 5), v('sequestre', { valeur_num: 12400 }), v('condition_pret', { valeur: 'oui' }),
  ...cv('preemption', null, 0), ...cv('pret', '2026-12-31', 1), ...cv('hypotheque', null, 2), ...cv('servitudes', null, 3)]
const doc = (valeurs, x = {}) => ({ nom: 'Copie AAE PROMESSE.pdf', lecture: { id: 'L-1', typeCode: 'transaction.avant_contrat', etat: 'lu', luLe: '2026-11-17T14:45:00Z', valeurs, ...x } })
const reg = (x = {}) => ({ kind: 'compromis', state: 'active', id: 30770, date: '2026-10-23', dateActe: '2027-01-23', montant: 124000, prixNetVendeur: 115000, honorairesEntree: 9000, honorairesSortie: null,
  acquereurs: [], sequestre: null, carnetLu: true, conditions: [{ libelle: 'Obtention Crédit', date: '2026-12-31' }], ...x })
const CATALOGUE = ['Préemption mairie', 'Obtention Crédit', 'Permis de construire', 'Delai de retractation SRU', 'Depot du permis de construire', 'Obtention du permis de construire'].map((libelle, i) => ({ id: `c${i}`, libelle }))
const L = (b, cle) => b.lignes.find((l) => l.cle === cle)
const luV = [...lu18849, ...cv('permis_construire', '2027-01-10', 4), ...cv('vente_bien', null, 5)]

console.log('① le bilan')
const b = bilanCompromis([doc(lu18849)], [reg()], CATALOGUE)
voir(b && b.affaireId === 30770 && b.lectureId === 'L-1' && b.conditionsLues, '18849 : le compromis lu trouve SA transaction (30770)')
voir(L(b, 'B.prix').etat === 'accord' && L(b, 'B.date').etat === 'accord' && L(b, 'B.net_vendeur').etat === 'accord' && L(b, 'B.honoraires').etat === 'accord', '18849 : prix, signature, net vendeur, honoraires : d\'accord')
voir(L(b, 'B.date_acte').etat === 'trancher' && L(b, 'B.date_acte').lu === 'le 01/02/2027' && L(b, 'B.date_acte').transaction === 'le 23/01/2027' && L(b, 'B.date_acte').regle === 'L7',
  '⛔ 18849 : date butoir 01/02/2027 au compromis, acte prévu le 23/01/2027 -> CONFLIT (Frédéric : ce sont la même date, elles doivent être identiques)')
voir(L(bilanCompromis([doc(lu18849)], [reg({ dateActe: '2027-02-01' })], CATALOGUE), 'B.date_acte').etat === 'accord', 'TÉMOIN : la même date des deux côtés -> d\'accord')
voir(L(b, 'B.sequestre').etat === 'ajouter' && L(b, 'B.sequestre').valeur === '12400' && L(b, 'B.sequestre').lu === '12 400 €' && L(b, 'B.sequestre').page === 9, '18849 : séquestre 12 400 € à ajouter (transaction vide), lu page 9')
voir(['B.prix', 'B.date', 'B.date_acte', 'B.sequestre', 'B.net_vendeur', 'B.honoraires'].every((c) => L(b, c).destination === 'hektor'), '⛔ prix, dates, séquestre, net, honoraires : « envoyé à Hektor » (Frédéric : « cela dépend des champs »)')
voir(!L(b, 'B.condition.preemption') && !L(b, 'B.condition.hypotheque') && !L(b, 'B.condition.servitudes') && b.conditionsGenerales.join() === 'Préemption mairie,État hypothécaire,Absence de servitude',
  '⛔ 18849 : la préemption, l\'état hypothécaire et l\'absence de servitude sont des conditions GÉNÉRALES -- ni reprises ni comparées, seulement dites à part')
voir(L(bilanCompromis([doc([...lu18849, ...cv('urbanisme', null, 6)])], [reg()], CATALOGUE), 'B.condition.urbanisme').etat === 'ajouter' && /condition libre/.test(L(bilanCompromis([doc([...lu18849, ...cv('urbanisme', null, 6)])], [reg()], CATALOGUE), 'B.condition.urbanisme').note),
  'une condition SUSPENSIVE hors catalogue (urbanisme) se propose en condition LIBRE (la modale les accepte)')
voir(L(b, 'B.condition.pret').etat === 'accord', '18849 : « Obtention Crédit » jusqu\'au 31/12/2026, déjà suivie à la même date -> d\'accord')
const sansCredit = bilanCompromis([doc(lu18849)], [reg({ conditions: [] })], CATALOGUE)
voir(L(sansCredit, 'B.condition.pret').etat === 'ajouter' && L(sansCredit, 'B.condition.pret').valeur === '2026-12-31' && L(sansCredit, 'B.condition.pret').condition.catalogueId === 'c1',
  'TÉMOIN : les conditions SUSPENSIVES restent reprises -- le prêt non suivi se propose, avec sa date et sa clause du catalogue')
voir(b.lignes.filter((l) => l.condition).every((l) => l.destination === 'nous'), '⛔ les conditions : « gardé chez nous » (décision du 16/09, jamais envoyées à Hektor)')
const bV = bilanCompromis([doc(luV)], [reg()], CATALOGUE)
voir(L(bV, 'B.condition.permis_construire').regle === 'L20' && L(bV, 'B.condition.permis_construire').condition.catalogueId === 'c5' && L(bV, 'B.sequestre').regle === null, 'la ligne « À regarder » liée : L20 pour une condition non trouvée ; aucune pour une case vide')
const tard = bilanCompromis([doc(lu18849)], [reg({ dateActe: '2027-03-15' })], CATALOGUE)
voir(L(tard, 'B.date_acte').etat === 'trancher' && /la même/.test(L(tard, 'B.date_acte').note) && L(tard, 'B.date_acte').champModale === 'signature_date', 'TÉMOIN : une date d\'acte prévue APRÈS la date butoir -> à trancher (case « date de signature de l\'acte » de la modale)')
const cherPrix = bilanCompromis([doc(lu18849)], [reg({ montant: 129000, sequestre: 5000 })], CATALOGUE)
voir(L(cherPrix, 'B.prix').etat === 'trancher' && L(cherPrix, 'B.prix').transaction === '129 000 €' && L(cherPrix, 'B.sequestre').etat === 'trancher', 'TÉMOIN : prix et séquestre différents -> à trancher')
voir(bilanCompromis([doc(lu18849)], [reg(), reg({ id: 30771 })], CATALOGUE) === null, 'TÉMOIN : deux compromis que rien ne départage -> pas de fenêtre (jamais la mauvaise transaction)')
voir(bilanCompromis([doc(lu18849)], [reg({ state: 'cancelled' })], CATALOGUE) === null && bilanCompromis([doc(lu18849, { etat: 'incomplet' })], [reg()], CATALOGUE) === null, 'TÉMOIN : compromis annulé, ou lecture incomplète -> pas de fenêtre')
const sansListe = bilanCompromis([doc(lu18849)], [reg({ conditions: null })], CATALOGUE)
voir(!sansListe.conditionsLues && !sansListe.lignes.some((l) => l.condition), 'TÉMOIN : la liste des conditions pas lue -> aucune ligne de condition (jamais croire une liste vide)')
const renonce = bilanCompromis([doc(lu18849.map((x) => (x.cle === 'condition_pret' ? { ...x, valeur: 'renonciation' } : x)))], [reg()], CATALOGUE)
voir(L(renonce, 'B.condition.pret').condition.retirer === true && L(renonce, 'B.condition.pret').etat === 'trancher', 'renonciation au prêt, la transaction le suit -> « retirer la condition ? » à trancher')
voir(L(bilanCompromis([doc(lu18849)], [reg({ conditions: [{ libelle: 'Obtention Crédit', date: '2026-12-15' }] })], CATALOGUE), 'B.condition.pret').etat === 'trancher', 'TÉMOIN : même condition, autre date -> à trancher')

// audit du 17/11 : on compare à ce que HEKTOR a ; ce qui n'y est pas encore se dit
const jamais = bilanCompromis([doc(lu18849)], [reg({ sequestre: null, enAttente: { sequestre: 'jamais_envoye' } })], CATALOGUE)
voir(L(jamais, 'B.sequestre').etat === 'ajouter' && L(jamais, 'B.sequestre').attente === 'jamais_envoye' && /jamais partie chez Hektor/.test(L(jamais, 'B.sequestre').note),
  '⛔ 30770 : le séquestre du carnet seul (ancien chemin 10a) n\'est PAS chez Hektor -> « à ajouter », et la fenêtre le dit')
const enRoute = bilanCompromis([doc(lu18849)], [reg({ sequestre: 12400, enAttente: { sequestre: 'en_route' } })], CATALOGUE)
voir(L(enRoute, 'B.sequestre').etat === 'accord' && L(enRoute, 'B.sequestre').attente === 'en_route' && /pas encore confirmée/.test(L(enRoute, 'B.sequestre').note),
  'TÉMOIN : envoyé, pas encore revenu -> comparé à la valeur envoyée (pas renvoyé d\'office), et dit « pas encore confirmée »')
voir(L(b, 'B.sequestre').attente === null && L(b, 'B.prix').note === null, 'TÉMOIN : sans carnet en attente, rien n\'est ajouté')

console.log('② la liste des conditions après les choix')
const avant = [{ rang: 1, libelle: 'Obtention Crédit', date_echeance: '2026-12-15', etat: 'levee', date_levee: '2026-11-30', note: 'banque OK', catalogue_id: 'c1', jours: null }]
const apres = conditionsApres(avant, [L(bV, 'B.condition.permis_construire'), L(bV, 'B.condition.vente_bien'), { ...L(b, 'B.condition.pret'), condition: { ...L(b, 'B.condition.pret').condition, date: '2026-12-31' } }])
voir(apres.length === 3 && apres[0].etat === 'levee' && apres[0].note === 'banque OK' && apres[0].date_levee === '2026-11-30' && apres[0].date_echeance === '2026-12-31',
  'la condition déjà suivie GARDE son état, sa levée et sa note ; seule sa date change')
voir(apres[1].libelle === 'Obtention du permis de construire' && apres[1].catalogue_id === 'c5' && apres[1].date_echeance === '2027-01-10' && apres[1].etat === 'attente' && apres[2].libelle === "Vente d'un bien de l'acquéreur" && apres[2].catalogue_id === null && apres.map((c) => c.rang).join() === '1,2,3',
  'les ajoutées arrivent « en attente », du catalogue ou libres, rangs renumérotés')
voir(conditionsApres(avant, [L(renonce, 'B.condition.pret')]).length === 0 && conditionsApres(avant, []).length === 1, 'retirer enlève la condition de prêt ; aucun choix : la liste reste entière')

console.log('③ la note Vrai / Faux déduite des choix (morceau 10)')
const alerteL20 = "Conditions suspensives du compromis non trouvées dans la transaction : Obtention du permis de construire, Vente d'un bien de l'acquéreur"
voir(verdictDesChoix(alerteL20, 'L20', bV.lignes, new Map([['B.condition.permis_construire', 'prendre']])) === 'vrai', 'une condition prise -> l\'alerte avait raison (vrai)')
voir(verdictDesChoix(alerteL20, 'L20', bV.lignes, new Map([['B.condition.permis_construire', 'garder'], ['B.condition.vente_bien', 'garder']])) === 'faux', 'toutes laissées -> elle a sonné pour rien (faux)')
voir(verdictDesChoix(alerteL20, 'L20', bV.lignes, new Map([['B.condition.permis_construire', 'garder']])) === null && verdictDesChoix(alerteL20, 'L20', bV.lignes, new Map()) === null, 'TÉMOIN : tranché en partie, ou rien -> pas de note')

console.log('④ le branchement')
const app = fs.readFileSync(path.join(__dirname, 'src/App.tsx'), 'utf8')
const fen = fs.readFileSync(path.join(__dirname, 'src/BilanCompromis.tsx'), 'utf8')
const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
const v2 = fs.readFileSync(path.join(__dirname, 'src/ModaleStatutV2.tsx'), 'utf8')
const ap = app.slice(app.indexOf('const appliquerBilan = async'), app.indexOf('// A.2 lot 6b P5', app.indexOf('const appliquerBilan = async')))
const avantDans = (s, a, z) => s.indexOf(a) >= 0 && s.indexOf(z) > s.indexOf(a)
voir(avantDans(ap, 'await loadAffairesForDossier(', 'await ecrireAffaireConditions(') && /\['refused', 'cancelled'\]\.includes/.test(ap), 'la transaction est RELUE avant tout geste ; close ou illisible -> rien')
voir(avantDans(ap, 'await lireConditionsCompletesStrict(b.affaireId)', 'await ecrireAffaireConditions(b.affaireId, apres)'), 'conditions : la liste COMPLÈTE relue STRICTEMENT juste avant d\'être réécrite')
voir(!/editAffaireOptimistic|createChangeHektorAnnonceStatusJob/.test(ap) && /window\.dispatchEvent\(new CustomEvent\(EVENEMENT_MODIFIER_TRANSACTION/.test(ap),
  '⛔ champs Hektor : AUCUNE écriture directe (ni carnet seul, ni travail) -- la modale « Modifier le compromis » est demandée')
const ecoute = app.slice(app.indexOf('const demande = (e: Event) =>'), app.indexOf('window.addEventListener(EVENEMENT_DROITS_TRANSACTION'))
voir(/if \(!d \|\| !isManagerOrAdmin\) return/.test(ecoute) && /openStatusChangeModal\(cible\)/.test(ecoute) && /setStatusChangeStatus\('compromise'\)/.test(ecoute) && /setStatusChangeAffaireChoisie\(d\.appAffaireId\)/.test(ecoute),
  'la modale EXISTANTE s\'ouvre sur le compromis et LA transaction lue ; seul un responsable ou un admin')
const prerempli = app.indexOf('    // LES CHAMPS QUE SEUL LE CARNET PORTE.')
const pose = app.indexOf("if (l.champModale === 'sequestration') { setStatusChangeSequestration(l.valeur)")
voir(prerempli > 0 && pose > prerempli && /toucherStatusChange\(\.\.\.touchees\)/.test(app), 'les valeurs se posent APRÈS le préremplissage du registre (sinon il les écraserait), marquées touchées')
const envoi = app.slice(app.indexOf('async function handleChangeHektorAnnonceStatus('), app.indexOf('function openDiffusionModal'))
voir(/if \(reprendre && depuisDocument && Number\(affaireCourantePourStatut\(\)\?\.app_affaire_id\) === depuisDocument\.appAffaireId\) \{\s*noterDepuisDocument/.test(envoi) && avantDans(envoi, 'const job = await createChangeHektorAnnonceStatusJob(', 'noterDepuisDocument('),
  'la décision « remplie » n\'est notée qu\'APRÈS l\'envoi réussi de « Mettre à jour le compromis »')
voir(/const notees = d\.lignes\.filter\(\(l\) => !l\.champModale \|\| egal\(dansLaCase\[l\.champModale\] \?\? '', l\.valeur\)\)/.test(app), 'TÉMOIN : une case changée à la main dans la modale n\'est pas notée « prise du compromis »')
voir(/depuisDocument \? \(/.test(v2) && /« Mettre à jour le compromis » : c'est ce bouton qui envoie à Hektor/.test(v2), 'la modale DIT ce qui vient du compromis, et quel bouton envoie')
const enr = fen.slice(fen.indexOf('async function enregistrer()'), fen.indexOf('const ligneVue'))
voir((fen.match(/onEnregistrer\(/g) || []).length === 1 && enr.includes('onEnregistrer('), 'la fenêtre n\'écrit RIEN avant « Enregistrer » (un seul appel, dans enregistrer)')
voir(/envoyé à Hektor/.test(fen) && /gardé chez nous/.test(fen), 'chaque ligne dit OÙ elle va (les mots de la modale de statut)')
voir(/const peutBilan = remplir && Boolean\(onBilan\)/.test(rm) && /Date\.now\(\) - new Date\(bilan\.luLe\)\.getTime\(\) < 30 \* 60 \* 1000/.test(rm) && /Revoir ce qu'il dit/.test(rm),
  'derrière `ged_remplir` ; s\'ouvre seule sur une lecture NEUVE (30 min) ; se rouvre par « Revoir ce qu\'il dit »')
voir(/@media \(prefers-reduced-motion: reduce\)/.test(fs.readFileSync(path.join(__dirname, 'src/BilanCompromis.css'), 'utf8')), 'les animations se coupent si l\'ordinateur demande moins de mouvement')

console.log('⑤ l\'envoi direct (décision du 17/11) et « à trancher » proposé')
const apiSrc = fs.readFileSync(path.join(__dirname, 'src/lib/api.ts'), 'utf8')
const env = apiSrc.slice(apiSrc.indexOf('export async function envoyerAffaireChampsDirect'), apiSrc.indexOf('export async function loadConsoleJobsByIds'))
voir(/supabase\.rpc\('app_modifier_affaire_optimistic'/.test(env) && /reprendre_transaction: true, champs_touches: touches/.test(env) && !/amount|net_seller_price|buyer_fees|seller_fees/.test(env),
  'envoi direct : la MÊME porte que « Mettre à jour » ; la charge ne porte que les cases envoyées, nommées « touchées » (jamais prix, net, honoraires)')
voir(/ENVOI_DIRECT: ReadonlySet<string> = new Set\(\['transaction_date', 'signature_date', 'sequestration'\]\)/.test(fen), 'seules la date de signature, la date de l\'acte et le séquestre partent directement')
voir(avantDans(ap, 'if (!hasHektorNegotiator(dossier)) throw', 'await ecrireAffaireConditions(') && avantDans(ap, 'await gesteHektorEnCours(dossier.hektor_annonce_id)', 'await ecrireAffaireConditions(')
  && avantDans(ap, 'await gesteHektorEnCours(', 'await envoyerAffaireChampsDirect('),
  'les gardes de la modale (négociateur Hektor, aucun geste en cours) passent AVANT toute écriture')
voir(avantDans(ap, 'const job = await envoyerAffaireChampsDirect(', "await noter(c.ligne, 'remplie', { geste: 'envoi_direct_hektor'") && /if \(versHektor\.length && parLaModale\)/.test(ap),
  'la décision « remplie » est notée APRÈS le travail créé ; prix, net ou honoraires -> TOUT passe par la modale (un seul travail)')
const rmA = rm.slice(rm.indexOf('const chezHektor = '), rm.indexOf('const date = chezHektor'))
voir(/if \(l\.origine === 'saisie_app'\) \{ enAttente\[champ\] = 'jamais_envoye'; return null \}/.test(rmA) && /\['arrivee', 'sans_objet'\]\.includes\(l\.etat\)/.test(rmA),
  '⛔ la valeur de la transaction est celle de HEKTOR : le carnet seul compte comme vide ; une valeur en route se compare telle qu\'envoyée')
voir(/l\.etat === 'trancher' && !decisions\?\.has\(`\$\{l\.cle\}\|\$\{l\.valeur\}`\)\)\.map\(\(l\) => \[l\.cle, 'prendre' as ChoixBilan\]\)/.test(fen) && /'corriger le registre'/.test(fen),
  'Frédéric : « à trancher » arrive PROPOSÉ -- la valeur du document choisie (« corriger le registre ») ; lecture seule : rien de choisi')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
