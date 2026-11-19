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
const { bilanCompromis, bilanOffre, bilansDuDossier, conditionsApres, verdictDesChoix } = m.exports

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
voir(/if \(!d \|\| !isManagerOrAdmin\) return/.test(ecoute) && /openStatusChangeModal\(cible\)/.test(ecoute) && /setStatusChangeStatus\(d\.genre === 'offre' \? 'offer' : 'compromise'\)/.test(ecoute) && /setStatusChangeAffaireChoisie\(d\.appAffaireId\)/.test(ecoute),
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
voir(/const peutBilan = remplir && Boolean\(onBilan\)/.test(rm) && /Date\.now\(\) - new Date\(b\.luLe\)\.getTime\(\) < 30 \* 60 \* 1000/.test(rm) && /Revoir ce qu'il dit/.test(rm),
  'derrière `ged_remplir` ; s\'ouvre seule sur une lecture NEUVE (30 min) ; se rouvre par « Revoir ce qu\'il dit »')
voir(/@media \(prefers-reduced-motion: reduce\)/.test(fs.readFileSync(path.join(__dirname, 'src/BilanCompromis.css'), 'utf8')), 'les animations se coupent si l\'ordinateur demande moins de mouvement')

console.log('⑤ la modale en arrière-plan (décision du 17/11) et « à trancher » proposé')
const apiSrc = fs.readFileSync(path.join(__dirname, 'src/lib/api.ts'), 'utf8')
voir(!/envoyerAffaireChampsDirect|gesteHektorEnCours/.test(apiSrc + app),
  '⛔ essai réel du 17/11 (« Montant requis ») : l\'envoi par une charge allégée est RETIRÉ -- un seul chemin vers Hektor, la modale')
voir(/const enArrierePlan = versHektor\.length > 0 && versHektor\.every\(\(c\) => estEnvoiDirect\(c\.ligne\)\)/.test(ap) && /arrierePlan: enArrierePlan/.test(ap)
  && /ENVOI_DIRECT: ReadonlySet<string> = new Set\(\['transaction_date', 'signature_date', 'sequestration'\]\)/.test(fen),
  'date de signature, date de l\'acte, séquestre -> la modale CACHÉE ; un prix, un net ou des honoraires -> la modale VISIBLE, pour tout')
const charge = app.slice(app.indexOf('function chargeDeLaModale(reprendre: boolean)'), app.indexOf('async function handleChangeHektorAnnonceStatus('))
const ap2 = app.slice(app.indexOf('async function envoyerEnArrierePlan()'), app.indexOf('// ─── « CORRIGER SANS ENVOYER A HEKTOR »'))
voir(/buyerContactId: statusChangeBuyerContactId/.test(charge) && /modifierAffaireId: reprendre \?/.test(charge)
  && /createChangeHektorAnnonceStatusJob\(chargeDeLaModale\(reprendre\)\)/.test(envoi) && /createChangeHektorAnnonceStatusJob\(chargeDeLaModale\(true\)\)/.test(ap2),
  'la MÊME charge que le bouton « Mettre à jour » : une seule construction (chargeDeLaModale), pour la modale visible et cachée')
voir(!/saveRepartition|ecrireAffaireCommission|ecrireAffaireConditions|ecrireAffaireNote/.test(ap2),
  '⛔ cachée, elle n\'écrit RIEN d\'autre que le travail (pas de répartition par défaut enregistrée en silence, ni commission, conditions, note)')
voir(avantDans(ap2, 'if (!hasHektorNegotiator(cible))', 'await createChangeHektorAnnonceStatusJob(') && avantDans(ap2, 'activeAdminAnnonceJobIds.has(', 'await createChangeHektorAnnonceStatusJob(')
  && avantDans(ap2, "if (!statusChangeAmount.trim() || (statusChangeNeedsSalePrice(statusChangeStatus) && !statusChangeSalePrice.trim()))", 'await createChangeHektorAnnonceStatusJob(')
  && avantDans(ap2, 'await createChangeHektorAnnonceStatusJob(', 'noterDepuisDocument('),
  'les gardes du bouton passent AVANT le travail (négociateur, geste en cours, montant) ; la décision est notée APRÈS')
const pret = app.slice(app.indexOf('// prête ? (déclaré APRÈS'), app.indexOf('// pas prête en 20 secondes'))
voir(/carnetChargePour !== ids\) return/.test(pret) && /Number\(affaire\.app_affaire_id\) !== depuisDocument\.appAffaireId/.test(pret) && /if \(!arrierePlanArme \|\| arrierePlanParti/.test(pret)
  && app.indexOf('// prête ? (déclaré APRÈS') > app.indexOf("if (l.champModale === 'sequestration') { setStatusChangeSequestration(l.valeur)"),
  'elle n\'envoie qu\'une fois PRÊTE (LA transaction désignée, son carnet lu), au rendu suivant la pose des valeurs, une seule fois')
voir(/}, 20000\)/.test(app) && /statusChangeTarget && !depuisDocument\?\.arrierePlan \? \(/.test(app) && /\) : null\) : depuisDocument\?\.arrierePlan \? null : \(<>/.test(app),
  'rien n\'est dessiné en arrière-plan ; pas prête en 20 s -> rien ne part, et c\'est dit dans la fenêtre')
voir(/window\.dispatchEvent\(new CustomEvent<ResultatEnvoi>\(EVENEMENT_RESULTAT_ENVOI/.test(app) && /window\.addEventListener\(EVENEMENT_RESULTAT_ENVOI, ecoute\)/.test(fen),
  'le résultat (envoyé ou refusé) s\'affiche dans la fenêtre « Ce que dit le compromis »')
const rmA = rm.slice(rm.indexOf('const chezHektor = '), rm.indexOf('const date = chezHektor'))
voir(/if \(l\.origine === 'saisie_app'\) \{ enAttente\[champ\] = 'jamais_envoye'; return null \}/.test(rmA) && /\['arrivee', 'sans_objet'\]\.includes\(l\.etat\)/.test(rmA)
  && /if \(dernierEnvoi === 'error'\) \{ enAttente\[champ\] = 'echec'; return null \}/.test(rmA),
  '⛔ la valeur de la transaction est celle de HEKTOR : carnet seul ou dernier envoi RATÉ -> vide ; en route -> la valeur envoyée')
const rate = bilanCompromis([doc(lu18849)], [reg({ sequestre: null, enAttente: { sequestre: 'echec' } })], CATALOGUE)
voir(L(rate, 'B.sequestre').etat === 'ajouter' && /a échoué/.test(L(rate, 'B.sequestre').note), 'essai du 17/11 : un envoi raté se DIT et la valeur se propose de nouveau')
voir(/rouvertes\.has\(l\.cle\) \|\| l\.attente === 'echec' \|\| l\.attente === 'jamais_envoye' \? undefined/.test(fen),
  'essai réel du 17/11 : une décision « envoyé » dont l\'envoi a ÉCHOUÉ ne range pas la ligne dans « Déjà tranché »')
voir(/l\.etat === 'trancher' && !l\.fige && !decisions\?\.has\(`\$\{l\.cle\}\|\$\{l\.valeur\}`\)\)\.map\(\(l\) => \[l\.cle, 'prendre' as ChoixBilan\]\)/.test(fen) && /'corriger le registre'/.test(fen),
  'Frédéric : « à trancher » arrive PROPOSÉ -- la valeur du document choisie (« corriger le registre ») ; lecture seule : rien de choisi')

console.log('⑥ « Ce que dit l\'offre » (lot 2, « étends »)')
const vo = (cle, x, page = 1) => ({ cle, rang: 0, valeur: null, valeur_num: null, valeur_date: null, page, etat: 'lu', ...x })
const luOffre = [vo('montant_offert', { valeur_num: 150000 }), vo('base_prix', { valeur: 'fai' }), vo('date_offre', { valeur_date: '2026-08-29' }), vo('validite_jusquau', { valeur_date: '2026-09-08' }, 2)]
const docO = (valeurs, x = {}) => ({ nom: 'Offre achat.pdf', lecture: { id: 'L-O', typeCode: 'transaction.offre', etat: 'lu', luLe: '2026-11-17T20:00:00Z', valeurs, ...x } })
// la colonne `date` d'une offre porte son DERNIER mouvement (ici le refus du 01/09) ; la proposition est dateProposee
const regO = (x = {}) => ({ kind: 'offre', state: 'proposed', id: 1000001, date: '2026-09-01', dateProposee: '2026-08-29', montant: 150000, joursValidite: 10, acquereurs: [], ...x })
const o = bilanOffre([docO(luOffre)], [regO()])
voir(o && o.genre === 'offre' && o.affaireId === 1000001 && ['O.montant', 'O.date', 'O.validite'].every((c) => L(o, c).etat === 'accord'),
  'l\'offre lue trouve SON offre ; montant, date de PROPOSITION (pas la date du dernier mouvement) et validité : d\'accord')
voir(L(o, 'O.validite').lu === '10 jours', 'la validité se déduit de « valable jusqu\'au » (29/08 -> 08/09 = 10 jours)')
const o2 = bilanOffre([docO(luOffre)], [regO({ montant: 140000, joursValidite: 7, dateProposee: '2026-08-20' })])
voir(L(o2, 'O.montant').etat === 'trancher' && L(o2, 'O.date').etat === 'trancher' && L(o2, 'O.validite').etat === 'trancher' && o2.lignes.every((l) => l.destination === 'hektor' && !l.fige),
  'TÉMOIN : offre PROPOSÉE, trois écarts -> à trancher, « envoyé à Hektor »')
voir(L(o2, 'O.montant').champModale === 'amount' && L(o2, 'O.date').champModale === 'transaction_date' && L(o2, 'O.validite').champModale === 'validity_days', 'chaque ligne nomme SA case de la modale de l\'offre')
const acc = bilanOffre([docO(luOffre)], [regO({ state: 'accepted', montant: 140000 })])
voir(L(acc, 'O.montant').fige && /figée chez Hektor/.test(L(acc, 'O.montant').fige) && !L(acc, 'O.date').fige,
  '⛔ offre ACCEPTÉE : l\'écart se MONTRE, figé (« figée chez Hektor ») -- rien ne se propose ; une ligne d\'accord reste d\'accord')
const ref = bilanOffre([docO(luOffre)], [regO({ state: 'refused', montant: 140000 })])
voir(/date du refus/.test(L(ref, 'O.montant').fige), '⛔ offre REFUSÉE : figée aussi (le registre y porte la date du refus, la modifier la réécrirait)')
voir(!L(bilanOffre([docO(luOffre.map((x) => (x.cle === 'base_prix' ? { ...x, valeur: 'net_vendeur' } : x)))], [regO({ montant: 140000 })]), 'O.montant'),
  'TÉMOIN : un montant NET VENDEUR ne se compare pas au registre (comme la règle L7)')
voir(bilanOffre([docO(luOffre)], [regO(), regO({ id: 1000002 })]) === null && bilanOffre([docO(luOffre)], []) === null, 'TÉMOIN : deux offres que rien ne départage, ou pas d\'offre -> pas de fenêtre')
voir(L(bilanOffre([docO(luOffre)], [regO({ montant: null, enAttente: { montant: 'echec' } })]), 'O.montant').etat === 'ajouter' && /a échoué/.test(L(bilanOffre([docO(luOffre)], [regO({ montant: null, enAttente: { montant: 'echec' } })]), 'O.montant').note),
  'un envoi raté se dit aussi pour l\'offre')
const deux = bilansDuDossier([docO(luOffre), doc(lu18849)], [regO(), reg()], CATALOGUE)
voir(deux.map((x) => x.genre).join() === 'offre,compromis' && bilanCompromis([doc(lu18849)], [reg()], CATALOGUE).genre === 'compromis', 'un dossier : l\'offre puis le compromis, chacun sa fenêtre')
voir(/l\.cle\.startsWith\('B\.'\) && l\.champModale != null && ENVOI_DIRECT\.has/.test(fen),
  '⛔ l\'offre ne part JAMAIS cachée : son chemin renvoie montant, date et validité préremplis (corps neuf, sans cases touchées ni témoin)')
voir(/if \(offreAccepteeFigeeChezHektor\(affaireCourantePourStatut\(\)\)\) \{ finir\(/.test(ap2) && /cleNumero = d\.genre === 'offre' \? 'offre_id' : 'compromis_id'/.test(ecoute),
  'la modale s\'ouvre sur l\'onglet Offre et LE numéro de l\'offre ; une offre acceptée ne part jamais')
voir(/l\.champModale === 'amount' && depuisDocument\.genre === 'offre'\) \{ setStatusChangeAmount\(l\.valeur\); touchees\.push\('amount'\) \}/.test(app) && /setStatusChangeValidityDays\(l\.valeur\); touchees\.push\('validity_days'\)/.test(app),
  'offre : seul le montant est touché (jamais son prix de vente, relu chez Hektor par le worker) ; la validité a sa case')
voir(/!l\.fige && !journal\.has/.test(rm) && /groupe\('Figé chez Hektor'/.test(fen), 'une ligne figée ne compte pas « à trancher » sur la carte ; la fenêtre la range à part')

console.log('⑦ la fiche du bien face à ses documents (lot 3, 18/11)')
const F = (() => {
  const c = esbuild.buildSync({ entryPoints: [path.join(__dirname, 'src/lib/gedBilanFiche.ts')], bundle: true, write: false, format: 'cjs', platform: 'node' }).outputFiles[0].text
  const mm = { exports: {} }
  new Function('module', 'exports', 'require', c)(mm, mm.exports, require)
  return mm.exports
})()
const vf = (cle, x, page = 2) => ({ cle, rang: 0, valeur: null, valeur_num: null, valeur_date: null, page, etat: 'lu', ...x })
const docF = (nom, typeCode, valeurs, x = {}) => ({ nom, lecture: { id: 'L-' + nom, typeCode, etat: 'lu', luLe: '2026-11-18T08:00:00Z', valeurs, ...x } })
const FICHE = { copropriete: true, dpeConso: null, dpeGes: null, dpeDate: null, nbLots: null, charges: null, quotePart: null, erpDate: null, carrez: null }
const dpeF = docF('DPE.pdf', 'diag.dpe', [vf('conso_ep', { valeur_num: 210.4 }), vf('emissions', { valeur_num: 45 }), vf('date_etablissement', { valeur_date: '2026-02-03' })])
const bF = (faits, docs) => F.bilansFiche({ ...FICHE, ...faits }, docs)
const vide = bF({}, [dpeF])[0]
voir(vide.genre === 'dpe' && ['F.dpe_cons', 'F.dpe_ges', 'F.dpe_date'].every((c) => L(vide, c).etat === 'ajouter') && L(vide, 'F.dpe_cons').valeur === '210' && L(vide, 'F.dpe_cons').champFiche === 'dpe_cons' && L(vide, 'F.dpe_cons').temoin === null,
  'DPE sur une fiche VIDE : trois cases à ajouter (ce que faisait la carte P1), valeur arrondie, sa case Hektor, témoin « vide »')
const diff = bF({ dpeConso: 180, dpeGes: 45, dpeDate: '2025-01-01' }, [dpeF])[0]
voir(L(diff, 'F.dpe_cons').etat === 'trancher' && L(diff, 'F.dpe_cons').temoin === '180' && L(diff, 'F.dpe_cons').regle === 'L6' && L(diff, 'F.dpe_ges').etat === 'accord' && L(diff, 'F.dpe_date').etat === 'trancher' && L(diff, 'F.dpe_date').temoin === '2025-01-01',
  '⭐ Frédéric : une case REMPLIE qui diffère -> à trancher, la valeur du DPE proposée (liée à L6) ; égale -> d\'accord')
voir(L(bF({ dpeConso: 211, dpeGes: 45, dpeDate: '2026-02-03' }, [dpeF])[0], 'F.dpe_cons').etat === 'accord', 'TÉMOIN : 211 sur la fiche, 210 lu -> d\'accord (± 1, comme L6)')
voir(L(bF({ dpeDate: '0000-00-00' }, [dpeF])[0], 'F.dpe_date').etat === 'ajouter', 'une date « 0000-00-00 » de Hektor est une case vide')
voir(bF({}, [dpeF]).every((b) => b.lignes.every((l) => l.destination === 'hektor' && l.champModale === null)), 'chaque case de la fiche : « envoyé à Hektor », sans modale')
const erpF = docF('ERP.pdf', 'diag.erp', [vf('date_etablissement', { valeur_date: '2026-09-02' })])
voir(L(bF({}, [erpF])[0], 'F.erp_date').champFiche === 'diag_risques_nat_tech_date' && L(bF({ erpDate: '2026-01-01' }, [erpF])[0], 'F.erp_date').etat === 'trancher', 'état des risques : sa date, vide à ajouter, autre à trancher')
const carnetF = docF('Fiche synthetique.pdf', 'copro.carnet', [vf('sous_type', { valeur: 'fiche_synthetique' }), vf('nb_lots_total', { valeur_num: 48 }), vf('nb_lots_principaux', { valeur_num: 20 })])
const appelF = docF('Appel.pdf', 'copro.appel_fonds', [vf('provision_budget', { valeur_num: 300 }), vf('periode', { valeur: 'trimestre' })])
const co = bF({}, [carnetF, appelF])
voir(co.map((b) => b.genre).join() === 'copro_lots,copro_charges' && L(co[1], 'F.copropriete_quote_part').valeur === '1200', 'copropriété : nombre de lots et quote-part annuelle (300 € par trimestre = 1 200 €), chacun sa fenêtre')
voir(L(bF({ nbLots: 20 }, [carnetF])[0], 'F.copropriete_nb_lot').etat === 'accord' && L(bF({ nbLots: 30 }, [carnetF])[0], 'F.copropriete_nb_lot').etat === 'trancher', 'TÉMOIN : la fiche qui porte les lots PRINCIPAUX est d\'accord (comme L16) ; 30 -> à trancher')
voir(bF({ copropriete: false }, [carnetF, appelF]).length === 0, '⛔ un bien NON marqué copropriété : rien (jamais rien qui ferait passer la case à OUI)')
voir(L(bF({ quotePart: 1150 }, [appelF])[0], 'F.copropriete_quote_part').etat === 'accord' && L(bF({ quotePart: 2000 }, [appelF])[0], 'F.copropriete_quote_part').etat === 'trancher', 'TÉMOIN : charges ± 10 % -> d\'accord ; 2 000 -> à trancher')
const surf = docF('Metre.pdf', 'diag.surface', [vf('surface_carrez', { valeur_num: 61.5 }), vf('date_mesurage', { valeur_date: '2026-03-01' })])
voir(L(bF({ carrez: '70' }, [surf])[0], 'F.surface_carrez').etat === 'trancher' && L(bF({ carrez: '62' }, [surf])[0], 'F.surface_carrez').etat === 'accord' && L(bF({ carrez: '55' }, [surf])[0], 'F.surface_carrez').etat === 'accord',
  'Carrez SENS UNIQUE (comme L15) : plus petite de plus de 5 % -> à trancher ; un peu plus petite, ou plus grande -> d\'accord')
voir(L(bF({}, [surf])[0], 'F.surface_carrez').champFiche === 'SURF_CARREZ' && L(bF({}, [surf])[0], 'F.surface_carrez').valeur === '61.5', 'Carrez vide : à ajouter, dans SA case Hektor, à la décimale')
voir(bF({}, [docF('Mandat.pdf', 'mandat.vente', [vf('prix', { valeur_num: 200000 })])]).length === 0, '⛔ le MANDAT n\'a pas de fenêtre (décision ⑦-7) : ses écarts restent dans « À regarder »')
voir(F.caseInchangee('180', '180') && F.caseInchangee('180.00', '180') && F.caseInchangee('', null) && F.caseInchangee('0000-00-00', null) && F.caseInchangee('2025-01-01 00:00:00', '2025-01-01')
  && !F.caseInchangee('190', '180') && !F.caseInchangee('180', null) && !F.caseInchangee('', '180'), 'la case porte-t-elle encore ce que la fenêtre a montré ? (vide = vide, nombres en nombres, dates au jour)')
const apF = app.slice(app.indexOf('const appliquerBilanFiche = async'), app.indexOf('const appliquerBilan = async'))
voir(avantDans(apF, 'await loadDossierDetail(', 'await editAnnonceOptimistic(') && /caseInchangee\(rawWizardDetailField\(fiche, l\.champFiche as string\), l\.temoin\)/.test(apF) && /startsWith\('copropriete_'\) && !coproOui/.test(apF),
  '⛔ l\'écriture RELIT la fiche : une case qui a changé depuis la fenêtre, ou une copropriété démarquée, n\'est pas écrite (et c\'est dit)')
voir((apF.match(/await editAnnonceOptimistic\(/g) || []).length === 1 && !/createChangeHektorAnnonceStatusJob|EVENEMENT_MODIFIER_TRANSACTION/.test(apF) && /if \(estGenreFiche\(b\.genre\)\) return appliquerBilanFiche\(b, choix\)/.test(app),
  'la fiche part par SON geste habituel, en UN envoi, sans modale ni travail de transaction')
voir(/estGenreFiche\(b\.genre\) \? peutRemplir : peutModifierTransaction/.test(rm) && /bilansFiche\(faits, docsLus\)/.test(rm), 'qui tranche la fiche : celui qui peut la remplir ; les bilans de la fiche ne dépendent pas des transactions')
const remplirSrc = fs.readFileSync(path.join(__dirname, 'src/lib/gedRemplir.ts'), 'utf8')
voir(!/'P1\.|'P2\./.test(remplirSrc) && /'P3\.charge_honoraires'/.test(remplirSrc), 'un seul chemin par case : les cartes P1 et P2 sont retirées ; P3 (la charge vide au registre) reste')
const depot = fs.readFileSync(path.join(__dirname, 'src/DepotDocuments.tsx'), 'utf8')
voir(/resumeLecture\([^)]*\) \} \}\)\s*\n\s*\/\/[^\n]*\n\s*window\.dispatchEvent\(new CustomEvent\('ged:lecture-faite'\)\)/.test(depot) && /addEventListener\('ged:lecture-faite', relu\)/.test(rm) && /\[hektorAnnonceId, nbDocuments, lecturesFaites\]/.test(rm),
  'essai réel du 18/11 : une lecture qui finit fait relire les lectures -- les cartes « Ce que dit… » apparaissent sans recharger')
voir(/if \(!cleOuverture \|\| bilanOuvert \|\| depotOuvert\) return/.test(rm) && /for \(const c of cles\) window\.localStorage\.setItem\(c, '1'\)/.test(rm),
  'essai réel du 18/11 : la fenêtre ne bascule JAMAIS seule pendant qu\'une autre est ouverte (son résultat restait caché) ; une ouverture par lot de lectures neuves')
const fenDepot = fs.readFileSync(path.join(__dirname, 'src/lib/gedFenetreDepot.ts'), 'utf8')
voir(/const depotOuvert = useFenetreDepotOuverte\(\)/.test(rm) && /\}, \[cleOuverture, depotOuvert\]\)/.test(rm)
  && rm.indexOf('|| depotOuvert) return') < rm.indexOf("window.localStorage.setItem(c, '1')"),
  'essai réel du 19/11 : « Ce que dit… » ATTEND la fermeture de la fenêtre de dépôt (rien marqué vu avant), et s\'ouvre à sa fermeture')
voir(/const enFenetre = Boolean\(onFermer\)/.test(depot) && /if \(!enFenetre\) return\s*\n\s*signalerFenetreDepot\(true\)\s*\n\s*return \(\) => signalerFenetreDepot\(false\)/.test(depot),
  'la fenêtre de dépôt (au-dessus du bien) se signale ouverte puis fermée ; posée dans le panneau, elle ne se signale pas')
voir(/ouvertes = Math\.max\(0, ouvertes \+ \(ouverte \? 1 : -1\)\)/.test(fenDepot) && /window\.addEventListener\(EVENEMENT, maj\)/.test(fenDepot) && /removeEventListener\(EVENEMENT, maj\)/.test(fenDepot),
  'le signal compte les fenêtres ouvertes (jamais sous zéro) et se désabonne')

console.log('⑧ lot A (18/11) : les six rapports de diagnostic et le dossier de diagnostics')
const vr = (cle, x, rang, page = 3) => ({ cle, rang, valeur: null, valeur_num: null, valeur_date: null, page, etat: 'lu', ...x })
const elec = docF('Electricite.pdf', 'diag.electricite', [vf('date_etablissement', { valeur_date: '2026-04-10' }), vf('resultat', { valeur: 'anomalies' })])
const bE = (faits, docs) => bF({ diagnostics: faits }, docs)
const e0 = bE({}, [elec])
voir(e0.length === 1 && e0[0].genre === 'diag_electricite' && L(e0[0], 'F.diag_electrique').etat === 'ajouter' && L(e0[0], 'F.diag_electrique').valeur === 'OUI'
  && L(e0[0], 'F.diag_electrique').champFiche === 'diag_electrique' && L(e0[0], 'F.diag_electrique').temoin === null && L(e0[0], 'F.diag_electrique_date').valeur === '2026-04-10'
  && L(e0[0], 'F.diag_electrique_date').champFiche === 'diag_electrique_date', 'électricité sur une fiche VIDE : « réalisé = OUI » et sa date, à ajouter, chacun dans SA case Hektor')
voir(/anomalies/.test(L(e0[0], 'F.diag_electrique').note), 'le résultat lu est DIT (note), jamais écrit : la case Hektor ne dit que « fait »')
const e1 = bE({ diag_electrique: { fait: 'NON', date: null } }, [elec])[0]
voir(L(e1, 'F.diag_electrique').etat === 'trancher' && L(e1, 'F.diag_electrique').temoin === 'NON' && L(e1, 'F.diag_electrique').transaction === 'Non', 'la fiche dit NON, un rapport existe -> à trancher, témoin « NON »')
const e2 = bE({ diag_electrique: { fait: 'OUI', date: '2026-04-10' } }, [elec])[0]
voir(e2.lignes.every((l) => l.etat === 'accord'), 'TÉMOIN : OUI et la même date -> tout d\'accord (pas de carte, « Revoir ce qu\'il dit » seulement)')
voir(L(bE({ diag_electrique: { fait: 'OUI', date: '2025-01-01' } }, [elec])[0], 'F.diag_electrique_date').etat === 'trancher', 'une autre date -> à trancher')
const quatre = bE({}, ['diag.gaz', 'diag.plomb', 'diag.termites', 'diag.amiante'].map((t) => docF(t + '.pdf', t, [vf('date_etablissement', { valeur_date: '2026-05-01' })])))
voir(quatre.map((b) => b.genre).join() === 'diag_gaz,diag_plomb,diag_termites,diag_amiante' && quatre.map((b) => b.lignes[0].champFiche).join() === 'diag_gaz,diag_plomb,diag_termites,diag_amiante',
  'gaz, plomb, termites, amiante : chacun SA fenêtre, chacun SA case Hektor')
const assai = bE({}, [docF('SPANC.pdf', 'diag.assainissement', [vf('date_controle', { valeur_date: '2025-06-20' }), vf('conformite', { valeur: 'travaux_obligatoires' })])])[0]
voir(assai.genre === 'diag_assainissement' && L(assai, 'F.diag_assainissement_date').valeur === '2025-06-20' && /travaux obligatoires/.test(L(assai, 'F.diag_assainissement').note), 'assainissement : la date du CONTRÔLE, et la conformité dite')
const ddtF = docF('DDT.pdf', 'diag.dossier', [vf('dpe_conso_ep', { valeur_num: 250 }), vf('dpe_emissions', { valeur_num: 50 }), vf('dpe_date', { valeur_date: '2026-06-01' }),
  vr('diagnostics.diagnostic', { valeur: 'electricite' }, 0, 7), vr('diagnostics.date_rapport', { valeur_date: '2026-06-01' }, 0, 7), vr('diagnostics.conclusion', { valeur: 'sans anomalie' }, 0, 7),
  vr('diagnostics.diagnostic', { valeur: 'amiante' }, 1, 12), vr('diagnostics.date_rapport', { valeur_date: '2026-06-01' }, 1, 12)])
const d0 = bE({}, [ddtF])
voir(d0.length === 1 && d0[0].genre === 'ddt' && ['F.dpe_cons', 'F.dpe_ges', 'F.dpe_date', 'F.diag_electrique', 'F.diag_electrique_date', 'F.diag_amiante', 'F.diag_amiante_date'].every((c) => L(d0[0], c)),
  '⭐ UN document, UNE fenêtre : le DDT dit le DPE ET chaque diagnostic de sa liste')
voir(L(d0[0], 'F.dpe_cons').valeur === '250' && L(d0[0], 'F.diag_amiante').page === 12 && L(d0[0], 'F.diag_electrique').note === 'résultat lu : sans anomalie', 'le DDT : ses valeurs dpe_*, la page de chaque rapport, sa conclusion')
const mix = bE({}, [ddtF, dpeF, elec])
voir(mix.map((b) => b.genre).join() === 'ddt' && L(mix[0], 'F.dpe_cons').valeur === '250' && L(mix[0], 'F.diag_electrique_date').valeur === '2026-06-01',
  '⛔ un seul chemin par case : le DDT du 01/06 est plus RÉCENT que le DPE (03/02) et le rapport électricité (10/04) -> lui seul parle, pas de deuxième fenêtre')
const vieuxDdt = docF('DDT 2019.pdf', 'diag.dossier', [vf('dpe_conso_ep', { valeur_num: 300 }), vf('dpe_date', { valeur_date: '2019-01-01' }),
  vr('diagnostics.diagnostic', { valeur: 'electricite' }, 0), vr('diagnostics.date_rapport', { valeur_date: '2019-01-01' }, 0), vr('diagnostics.diagnostic', { valeur: 'gaz' }, 1), vr('diagnostics.date_rapport', { valeur_date: '2019-01-01' }, 1)])
const mix2 = bE({}, [vieuxDdt, dpeF, elec])
voir(mix2.map((b) => b.genre).join() === 'dpe,diag_electricite,ddt' && L(mix2[0], 'F.dpe_cons').valeur === '210' && mix2[2].lignes.map((l) => l.cle).join() === 'F.diag_gaz,F.diag_gaz_date',
  'TÉMOIN : un DDT plus ANCIEN -> le DPE et le rapport électricité parlent ; le DDT ne garde que le gaz, qu\'il est seul à dire')
voir(bE({}, [docF('Egal.pdf', 'diag.electricite', [vf('date_etablissement', { valeur_date: '2026-06-01' })]), ddtF]).find((b) => b.genre === 'diag_electricite'), 'à date ÉGALE, le rapport seul parle')
voir(bE({}, [docF('Elec.pdf', 'diag.electricite', [vf('date_etablissement', { valeur_date: '2026-04-10' })], { etat: 'incomplet' })]).length === 0, 'TÉMOIN : une lecture incomplète -> rien')
voir(F.caseInchangee('NON', 'NON') && !F.caseInchangee('OUI', 'NON') && F.caseInchangee('', null) && !F.caseInchangee('NON', null), 'l\'écriture relit la case : NON gardé = écrit ; changée en OUI entre-temps = rien écrit')
const mots = fs.readFileSync(path.join(__dirname, 'src/BilanCompromis.tsx'), 'utf8')
voir(['ddt', 'diag_electricite', 'diag_gaz', 'diag_plomb', 'diag_termites', 'diag_amiante', 'diag_assainissement'].every((g) => new RegExp(`\\n  ${g}: \\{ le: '[^']`).test(mots)) && /diag_assainissement: false/.test(rm),
  'chaque genre neuf a ses mots dans la fenêtre, et aucune ligne « À regarder » liée (L2 parle de validité, pas de « fait »)')
voir(/diagnostics: Object\.fromEntries\(\['diag_electrique', 'diag_gaz', 'diag_plomb', 'diag_termites', 'diag_amiante', 'diag_assainissement', 'diag_loi_carrez'\]/.test(app) && /\{ fait: lire\(c\) \|\| null, date: lire\(`\$\{c\}_date`\) \|\| null \}/.test(app),
  'la fiche lue : les six cases et leurs dates, brutes')

console.log('⑨ lot B (18/11) : la procédure du syndicat et le plan de sauvegarde (fiche synthétique, PV d\'AG)')
const synth = (proc, plan, date = '2026-03-01') => docF('Synthese.pdf', 'copro.carnet', [vf('sous_type', { valeur: 'fiche_synthetique' }), vf('date_etablissement', { valeur_date: date }),
  ...(proc ? [vf('procedure', { valeur: proc }, 4)] : []), ...(plan ? [vf('plan_sauvegarde', { valeur: plan }, 4)] : [])])
const pvF = (proc, date = '2026-06-15', piece = 'pv') => docF('PV AG.pdf', 'copro.pv_ag', [vf('type_piece', { valeur: piece }), vf('date_ag', { valeur_date: date }), ...(proc ? [vf('procedure', { valeur: proc }, 7)] : [])])
const g0 = bF({}, [synth('aucune', 'non')])
voir(g0.length === 1 && g0[0].genre === 'copro_lots' && L(g0[0], 'F.copropriete_statut_syndicat').valeur === 'NOTPROCESS' && L(g0[0], 'F.copropriete_statut_syndicat').etat === 'ajouter'
  && L(g0[0], 'F.copropriete_plan_sauvegarde').valeur === 'NON' && L(g0[0], 'F.copropriete_statut_syndicat').regle === null,
  'fiche synthétique « aucune » / « non » sur une fiche VIDE : NOTPROCESS et NON à ajouter (les codes réels de Hektor), sans lien à L17')
const g1 = bF({ statutSyndicat: 'NOTPROCESS' }, [synth('mandataire_ad_hoc', 'non')])[0]
voir(L(g1, 'F.copropriete_statut_syndicat').etat === 'trancher' && L(g1, 'F.copropriete_statut_syndicat').valeur === 'ALERTE' && L(g1, 'F.copropriete_statut_syndicat').temoin === 'NOTPROCESS'
  && L(g1, 'F.copropriete_statut_syndicat').regle === 'L17' && L(g1, 'F.copropriete_statut_syndicat').lu === 'Procédure d\'alerte' && L(g1, 'F.copropriete_statut_syndicat').transaction === 'Pas de procédure',
  '⭐ un mandataire ad hoc lu, la fiche dit « pas de procédure » -> à trancher, ALERTE proposé, lié à L17')
voir(L(bF({ statutSyndicat: 'REDRESSEMENT' }, [synth('administration_provisoire')])[0], 'F.copropriete_statut_syndicat').etat === 'accord', 'TÉMOIN : administration provisoire = REDRESSEMENT -> d\'accord')
voir(L(bF({ statutSyndicat: 'PAS_DE_PROCEDURE' }, [synth('aucune')])[0], 'F.copropriete_statut_syndicat').etat === 'accord'
  && L(bF({ statutSyndicat: 'PAS_DE_PROCEDURE' }, [synth('aucune')])[0], 'F.copropriete_statut_syndicat').temoin === 'PAS_DE_PROCEDURE', 'l\'ancien code de l\'écran de saisie (PAS_DE_PROCEDURE) vaut NOTPROCESS ; le témoin garde la case telle quelle')
const g2 = bF({ planSauvegarde: 'NON' }, [synth('aucune', 'non', '2025-01-10'), pvF('plan_sauvegarde')])
voir(g2.map((b) => b.genre).join() === 'copro_lots,copro_ag' && L(g2[1], 'F.copropriete_plan_sauvegarde').valeur === 'OUI' && L(g2[1], 'F.copropriete_plan_sauvegarde').etat === 'trancher'
  && L(g2[1], 'F.copropriete_plan_sauvegarde').page === 7 && !L(g2[0], 'F.copropriete_plan_sauvegarde') && L(g2[0], 'F.copropriete_statut_syndicat'),
  '⛔ un seul chemin par case : le PV du 15/06/2026 (plan de sauvegarde) est plus RÉCENT -> lui parle du plan ; la fiche synthétique garde le statut, qu\'elle est seule à dire')
voir(bF({}, [synth('aucune', 'non', '2026-09-01'), pvF('plan_sauvegarde')]).map((b) => b.genre).join() === 'copro_lots', 'TÉMOIN : une fiche synthétique plus récente que le PV -> elle seule parle, pas de fenêtre du PV')
voir(bF({}, [pvF(null)]).length === 0 && bF({}, [pvF('mandataire_ad_hoc', '2026-06-15', 'convocation')]).length === 0, '⛔ un PV qui ne nomme rien ne prouve pas l\'absence ; une convocation ne parle pas -> rien')
const g3 = bF({}, [pvF('administration_provisoire')])[0]
voir(g3.genre === 'copro_ag' && L(g3, 'F.copropriete_statut_syndicat').valeur === 'REDRESSEMENT' && !L(g3, 'F.copropriete_plan_sauvegarde'), 'un PV d\'administration provisoire -> REDRESSEMENT, et rien sur le plan')
voir(bF({ copropriete: false }, [synth('mandataire_ad_hoc', 'oui'), pvF('plan_sauvegarde')]).length === 0, '⛔ TÉMOIN : un bien NON marqué copropriété -> rien (jamais faire passer la case à OUI)')
voir(verdictDesChoix('Copropriété : mandataire ad hoc (lu dans Synthese.pdf)', 'L17', g1.lignes, new Map([['F.copropriete_statut_syndicat', 'prendre']])) === 'vrai', 'la ligne L17 de « À regarder » reçoit sa note par le choix (comme L16 au lot 3)')
voir(/copro_lots: \(a\.code === 'L16' && a\.texte\.startsWith\('Copropriété'\)\) \|\| a\.code === 'L17'/.test(rm) && /copro_ag: a\.code === 'L17'/.test(rm) && /\n  copro_ag: \{ le: 'le procès-verbal/.test(mots)
  && /planSauvegarde: lire\('copropriete_plan_sauvegarde'\) \|\| null/.test(app), 'le genre neuf a ses mots, L17 est liée aux deux fenêtres, la fiche lue porte le plan de sauvegarde brut')

console.log('⑩ lot C (18/11) : la taxe foncière et les charges au mois')
const avisF = (montant, annee, plusieurs = 'non') => docF(`Taxe ${annee}.pdf`, 'justif.taxe', [vf('annee_imposition', { valeur_num: annee }), vf('montant_total', { valeur_num: montant }, 1), vf('plusieurs_biens', { valeur: plusieurs })])
const t0 = bF({}, [avisF(1234, 2026)])
voir(t0.length === 1 && t0[0].genre === 'taxe' && L(t0[0], 'F.TAXE_FONCIERE').etat === 'ajouter' && L(t0[0], 'F.TAXE_FONCIERE').valeur === '1234' && L(t0[0], 'F.TAXE_FONCIERE').champFiche === 'TAXE_FONCIERE'
  && L(t0[0], 'F.TAXE_FONCIERE').page === 1 && L(t0[0], 'F.TAXE_FONCIERE').regle === 'T1' && L(t0[0], 'F.TAXE_FONCIERE').note === 'avis 2026', 'un avis sur une fiche VIDE : la taxe à ajouter dans TAXE_FONCIERE, liée à T1, l\'année dite')
voir(L(bF({ taxeFonciere: '0' }, [avisF(1234, 2026)])[0], 'F.TAXE_FONCIERE').etat === 'ajouter' && L(bF({ taxeFonciere: '0' }, [avisF(1234, 2026)])[0], 'F.TAXE_FONCIERE').temoin === null, 'une taxe à 0 sur la fiche est une case VIDE')
const t1 = bF({ taxeFonciere: '900' }, [avisF(1234, 2026), avisF(800, 2024)])
voir(t1.length === 1 && L(t1[0], 'F.TAXE_FONCIERE').etat === 'trancher' && L(t1[0], 'F.TAXE_FONCIERE').valeur === '1234' && L(t1[0], 'F.TAXE_FONCIERE').temoin === '900',
  '⭐ deux avis : le plus RÉCENT parle (2026 : 1 234 €), la fiche dit 900 -> à trancher, témoin 900')
voir(L(bF({ taxeFonciere: '1236' }, [avisF(1234, 2026)])[0], 'F.TAXE_FONCIERE').etat === 'accord' && L(bF({ taxeFonciere: '1236' }, [avisF(1234, 2026)])[0], 'F.TAXE_FONCIERE').regle === null, 'TÉMOIN : 1 236 sur la fiche, 1 234 lu -> d\'accord (± 5 €, comme T1)')
voir(bF({}, [avisF(5000, 2026, 'oui')]).length === 0, '⛔ un avis qui porte PLUSIEURS biens ne se propose pas : son montant n\'est pas celui du bien')
const ch = bF({ quotePart: 1800 }, [docF('Appel.pdf', 'copro.appel_fonds', [vf('provision_budget', { valeur_num: 450 }), vf('periode', { valeur: 'trimestre' })])])[0]
voir(ch.genre === 'copro_charges' && L(ch, 'F.copropriete_quote_part').etat === 'accord' && L(ch, 'F.CHARGES').etat === 'ajouter' && L(ch, 'F.CHARGES').valeur === '150' && L(ch, 'F.CHARGES').champFiche === 'CHARGES',
  'l\'appel de fonds (450 € par trimestre) : 1 800 € par an d\'accord, et 150 € PAR MOIS à ajouter dans CHARGES -- même fenêtre')
const chM = (mois) => L(bF({ quotePart: 1800, chargesMois: mois }, [docF('Appel.pdf', 'copro.appel_fonds', [vf('provision_budget', { valeur_num: 450 }), vf('periode', { valeur: 'trimestre' })])])[0], 'F.CHARGES')
voir(chM('0').etat === 'ajouter' && chM('155').etat === 'accord' && chM('120').etat === 'trancher' && chM('120').temoin === '120', 'CHARGES à 0 = vide ; 155 / 150 d\'accord (± 10 € par mois) ; 120 / 150 à trancher')
voir(bF({ copropriete: false, chargesMois: '0' }, [docF('Appel.pdf', 'copro.appel_fonds', [vf('provision_budget', { valeur_num: 450 }), vf('periode', { valeur: 'trimestre' })])]).length === 0, '⛔ TÉMOIN : un bien NON marqué copropriété -> pas de charges proposées')
voir(/\n  taxe: \{ le: 'l\\'avis de taxe foncière'/.test(mots) && /taxe: a\.code === 'T1'/.test(rm) && /chargesMois: lire\('CHARGES'\) \|\| null/.test(app), 'la taxe a ses mots, T1 est liée à sa fenêtre, la fiche lue porte CHARGES brute')

console.log('⑪ lot D (18/11) : le métré complet (surface habitable, mesurage Carrez réalisé et sa date)')
const metre = (x) => docF('Metrage.pdf', 'diag.surface', [vf('date_mesurage', { valeur_date: '2026-03-12' }), ...(x.carrez ? [vf('surface_carrez', { valeur_num: x.carrez }, 2)] : []), ...(x.hab ? [vf('surface_habitable', { valeur_num: x.hab }, 3)] : [])])
const m0 = bF({}, [metre({ carrez: 66.4, hab: 68.25 })])[0]
voir(m0.genre === 'surface' && L(m0, 'F.surface_carrez').etat === 'ajouter' && L(m0, 'F.diag_loi_carrez').valeur === 'OUI' && L(m0, 'F.diag_loi_carrez').etat === 'ajouter'
  && L(m0, 'F.diag_loi_carrez_date').valeur === '2026-03-12' && L(m0, 'F.surfappart').valeur === '68.25' && L(m0, 'F.surfappart').champFiche === 'surfappart' && L(m0, 'F.surfappart').page === 3,
  'un métré sur une fiche VIDE : Carrez, « mesurage Carrez réalisé = OUI », sa date, et la surface habitable 68.25 (décimale « . ») -- une fenêtre')
const m1 = bF({ surfaceHabitable: '75', carrez: '66', diagnostics: { diag_loi_carrez: { fait: 'OUI', date: '2026-03-12' } } }, [metre({ carrez: 66.4, hab: 68.25 })])[0]
voir(L(m1, 'F.surfappart').etat === 'trancher' && L(m1, 'F.surfappart').temoin === '75' && L(m1, 'F.surfappart').regle === null && ['F.surface_carrez', 'F.diag_loi_carrez', 'F.diag_loi_carrez_date'].every((c) => L(m1, c).etat === 'accord'),
  '⭐ la fiche dit 75 m², le métré 68,25 -> à trancher (dans les deux sens, sans règle liée) ; Carrez, fait et date d\'accord')
voir(L(bF({ surfaceHabitable: '69' }, [metre({ hab: 68.25 })])[0], 'F.surfappart').etat === 'accord', 'TÉMOIN : 69 / 68,25 -> d\'accord (± 1 m²)')
const m2s = bF({}, [metre({ hab: 90 })])[0]
voir(m2s.lignes.map((l) => l.cle).join() === 'F.surfappart', 'un métré SANS Carrez (une maison) : la surface habitable seule, pas de « mesurage Carrez réalisé »')
voir(bF({}, [docF('Metrage.pdf', 'diag.surface', [vf('date_mesurage', { valeur_date: '2026-03-12' })])]).length === 0, 'TÉMOIN : un métré sans surface lue -> rien')

console.log('⑫ lot E (18/11) : le titre de propriété -> la surface du terrain')
const titreF = (m2v, x = []) => docF('Titre.pdf', 'justif.titre', [vf('date_acte', { valeur_date: '2004-07-01' }), vf('contenance_totale_m2', { valeur_num: m2v }, 5), ...x])
const e0t = bF({ copropriete: false }, [titreF(812)])
voir(e0t.length === 1 && e0t[0].genre === 'titre' && L(e0t[0], 'F.surfterrain').etat === 'ajouter' && L(e0t[0], 'F.surfterrain').valeur === '812' && L(e0t[0], 'F.surfterrain').champFiche === 'surfterrain' && L(e0t[0], 'F.surfterrain').page === 5,
  'un titre (812 m²) sur une maison hors copropriété, terrain VIDE : surfterrain à ajouter')
voir(L(bF({ copropriete: false, surfaceTerrain: '0' }, [titreF(812)])[0], 'F.surfterrain').etat === 'ajouter' && L(bF({ copropriete: false, surfaceTerrain: '800' }, [titreF(812)])[0], 'F.surfterrain').etat === 'trancher'
  && L(bF({ copropriete: false, surfaceTerrain: '812' }, [titreF(812)])[0], 'F.surfterrain').etat === 'accord', 'terrain à 0 = vide ; 800 / 812 à trancher ; 812 d\'accord')
voir(bF({ copropriete: true }, [titreF(2400)]).length === 0 && bF({ copropriete: null }, [titreF(2400)]).length === 0, '⛔ un bien EN copropriété (ou non dit) : rien -- la contenance de l\'immeuble n\'est pas le terrain d\'un appartement')
voir(bF({ copropriete: false }, [titreF(2400, [vr('lots.numero', { valeur: '12' }, 0)])]).length === 0, '⛔ un titre qui cite des LOTS : rien, même si la fiche dit « hors copropriété »')
const deuxTitres = bF({ copropriete: false }, [titreF(812), docF('Titre 2019.pdf', 'justif.titre', [vf('date_acte', { valeur_date: '2019-05-02' }), vf('contenance_totale_m2', { valeur_num: 1012 })])])
voir(deuxTitres.length === 1 && L(deuxTitres[0], 'F.surfterrain').valeur === '1012', 'deux titres : le plus RÉCENT parle (2019, 1 012 m²)')
voir(/\n  titre: \{ le: 'le titre de propriété'/.test(mots) && /titre: false/.test(rm) && /surfaceHabitable: lire\('surfappart'\) \|\| null/.test(app) && /surfaceTerrain: lire\('surfterrain'\) \|\| null/.test(app),
  'le titre a ses mots, aucune ligne « À regarder » liée, la fiche lue porte surfappart et surfterrain bruts')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
