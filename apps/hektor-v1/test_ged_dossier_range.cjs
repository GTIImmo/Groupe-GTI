// 20/11/2026 -- GED, visuel V3, morceau 3 : « LE DOSSIER ». La liste des documents du cockpit se range par moment ; chaque
// ligne se déplie sur la carte d'AUJOURD'HUI. Cet essai prouve qu'on n'a RIEN cassé : la carte et les gestes de la signature
// sont identiques au caractère près à ceux d'avant (lus dans git), le classic est intact, et le rangement est juste.
//   node test_ged_dossier_range.cjs        (--temoin : la carte « abîmée » d'un caractère -> l'essai doit sonner)
const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const lf = (s) => s.replace(/\r\n/g, '\n')
const temoin = process.argv.includes('--temoin')
let app = lf(fs.readFileSync(path.join(__dirname, 'src/App.tsx'), 'utf8'))
if (temoin) app = app.replace('{docRowActions(e.doc)}', '{docRowActions(e.doc) }')
// --temoin7 : la carte classique « abîmée » d'un caractère et la ligne Déposer touchée -> ⑤ doit sonner deux fois
if (process.argv.includes('--temoin7')) app = app.replace('  const carteClassique = (document: ConsoleDocument) => {\n    const preparing', '  const carteClassique = (document: ConsoleDocument) => {\n    const preparing ').replace('>Déposer</button>', '>Déposer </button>')
const rm = lf(fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8'))
// La référence : App.tsx AVANT le morceau 3 -- le parent du commit qui a introduit `const carteDocument` (trouvé par git, sans
// numéro écrit en dur : le commit peut être rejoué sur origin/main et changer de numéro).
const racine = path.join(__dirname, '../..')
const git = (c) => execSync(c, { cwd: racine, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
const introduit = git('git log -S "const carteDocument" --format=%H -- apps/hektor-v1/src/App.tsx').trim().split(/\s+/).pop()
const avant = lf(git(`git show ${introduit}~1:apps/hektor-v1/src/App.tsx`))

console.log('① rien de la signature n\'a bougé')
const entre = (s, a, b) => { const i = s.indexOf(a); const j = s.indexOf(b, i + a.length); return i < 0 || j < 0 ? null : s.slice(i, j) }
const actionsAvant = entre(avant, '  const docRowActions = (document: ConsoleDocument) => {', '  // ---- Skin « v21 »')
// (26/11, morceau 7 B : le code sorti de la branche cockpit se pose juste après docRowActions -- la fin se lit donc à son repère)
const actionsApres = entre(app, '  const docRowActions = (document: ConsoleDocument) => {', app.includes('  // GED V3, morceau 7 B (26/11/2026)') ? '  // GED V3, morceau 7 B (26/11/2026)' : '  // ---- Skin « v21 »')
voir(actionsAvant && actionsAvant === actionsApres, 'docRowActions : identique au caractère (Ouvrir, Préparer, Preuves, Relancer, Annuler, Signature, Signé à la main, Supprimer)')
const carteAvant = entre(avant, '          {shown.map((e) => (\n', '\n          ))}\n        </div>')
const carteApres = entre(app, '    const carteDocument = (e: (typeof enriched)[number]) => (\n', '\n    )\n')
voir(carteAvant && carteApres && carteAvant.replace('          {shown.map((e) => (\n', '').trimEnd() === carteApres.replace('    const carteDocument = (e: (typeof enriched)[number]) => (\n', '').trimEnd(),
  'la carte d\'un document (nom, type, visibilité, état de signature, Remplacé, mention de dépôt, suivi des signataires, gestes) : identique au caractère')
voir((app.match(/carteDocument\(e\)/g) || []).length === 1 && (app.match(/rendreLeDossier\(carteDocument\)/g) || []).length === 1 && (app.match(/\{carte\(e\)\}/g) || []).length === 1,
  'la carte est montée par la liste à plat ET par la ligne dépliée (qui reçoit la carte à monter : morceau 7 B), et nulle part ailleurs')
voir((app.match(/<SuiviSignatairesYoutrust (preuvesActives=\{preuvesActives\} )?document=/g) || []).length === 3, 'le suivi des signataires reste monté aux trois mêmes endroits')
const fenetres = ['<PiecesSignatureFenetre document={piecesDoc}', '<ChoixSignatureFenetre', '<SignaturePromptModal', '<EnvoiSignatureYoutrust']
voir(fenetres.every((f) => (app.match(new RegExp(f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length === (avant.match(new RegExp(f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length),
  'les fenêtres de signature : autant qu\'avant, aux mêmes endroits')

console.log('② les deux conditions de la session signature (20/11)')
voir(/const ouvrirPuisSuivi = \(d: ConsoleDocument\) => \{[\s\S]{0,400}setLigneDocOuverte\(d\.id\)[\s\S]{0,80}window\.setTimeout\(\(\) => allerAuSuivi\(d\), 120\)/.test(app)
  && (app.match(/onVoirSuivi=\{\(\) => \{ const d = choixDoc; setChoixDoc\(null\); ouvrirPuisSuivi\(d\) \}\}/g) || []).length === 2,
  '« Voir le suivi » (cockpit ET panneau classique, morceau 7 B) déplie le groupe et la ligne, PUIS défile jusqu\'au suivi')
voir(/const ouvrirPuisSuivi = \(d: ConsoleDocument\) => \{\s*if \(!vueDossier \|\| !dossierGed\) \{ allerAuSuivi\(d\); return \}/.test(app),
  'TÉMOIN : sans « Le dossier » (fiche classique de l\'ordinateur, filtres du cockpit), « Voir le suivi » défile comme avant')
voir((app.match(/allerAuSuivi\(d\) \}\}/g) || []).length === 1, 'TÉMOIN : le suivi du mandat garde son « Voir le suivi » d\'avant')
voir(/const etatSignature = e\.sigLabel && !\/\^À envoyer\/\.test\(e\.sigLabel\) \? e\.sigLabel : null/.test(app) && /\{etatSignature \? <small className=\{`gd3-sig/.test(app)
  && /<span className="gd3-etat">\s*\{e\.remplace \? <span className="ens-pill-remplace">Remplacé<\/span> : <span className=\{`fa-ck-docbadge/.test(app),
  'ligne REPLIÉE : la pastille d\'état (Signé, En signature, Expirée…) ET « signée le / expirée le … à renvoyer / en attente » restent visibles')

console.log('③ le classic et les autres filtres ne bougent pas')
voir(/rangeEnListe = false, onDossier,/.test(rm) && /rangeEnListe=\{skin === 'v21' \|\| compact\}/.test(app) && /onDossier=\{skin === 'v21' \|\| compact \? setDossierGed : undefined\}/.test(app),
  'le réglage n\'est allumé qu\'au cockpit et au téléphone (absent = l\'écran d\'avant)')
const appelants = app.match(/<ConsoleDocumentsPanel [^\n]*/g) || []
voir(appelants.length === 3 && appelants.filter((l) => / compact /.test(l)).length === 1 && /<div className="mobile-console-documents">\s*<ConsoleDocumentsPanel [^\n]* compact /.test(app),
  'TÉMOIN : `compact` n\'a qu\'un appelant, la fiche du TÉLÉPHONE (la fiche classique de l\'ordinateur reste à plat)')
voir(/\{!rangeEnListe \? <div className="gm2-feuilles"/.test(rm) && /\{lus\.length && !rangeEnListe \? \(/.test(rm), 'sans le réglage, la grille de pièces et « Lu par l\'IA » s\'affichent comme avant')
voir(/const vueDossier = docFilter === 'tous' && dossierGed !== null/.test(app) && /\{\(vueDossier && dossierGed \? \[\] : shown\)\.map\(\(e\) => carteDocument\(e\)\)\}/.test(app),
  '« À préparer », « Signés », « Cloud » : la liste à plat d\'aujourd\'hui')

voir(/const noms = new Set\(l\.documents\)\s*const docs = enriched\.filter\(\(e\) => noms\.has\(e\.doc\.document_name\)\)/.test(app), 'un fichier ne revient pas autant de fois que son nom est porté par d’autres (vu en ligne le 20/11 sur 18849)')

console.log('⑤ morceau 7 B (26/11) : le téléphone range sa liste -- le code DÉPLACÉ est identique au caractère')
// La référence : App.tsx avant le morceau 7 B (parent du commit qui a introduit `const carteClassique`, ou HEAD s'il n'est pas commité)
const intro7 = git('git log -S "const carteClassique" --format=%H -- apps/hektor-v1/src/App.tsx').trim().split(/\s+/).filter(Boolean).pop()
const avant7 = lf(git(`git show ${intro7 ? intro7 + '~1' : 'HEAD'}:apps/hektor-v1/src/App.tsx`))
const retrait = (t, k) => t.split('\n').map((l) => (l.startsWith(' '.repeat(k)) ? l.slice(k) : l)).join('\n')
const corpsAvant = entre(avant7, '            {documents.map((document) => {\n', '\n            })}\n')
const corpsApres = entre(app, '  const carteClassique = (document: ConsoleDocument) => {\n', '\n  }\n')
voir(corpsAvant && corpsApres && retrait(corpsAvant.replace('            {documents.map((document) => {\n', ''), 10) === corpsApres.replace('  const carteClassique = (document: ConsoleDocument) => {\n', ''),
  'la carte classique (nom, Remplacé, Supprimé chez Hektor, envoi à Hektor, SignatureBadge, suivi des signataires, gestes) : identique au caractère')
voir(/\{documents\.length > 0 && !vueDossierTel \? \(\s*<div className="console-documents-list">\s*\{documents\.map\(\(document\) => carteClassique\(document\)\)\}/.test(app)
  && /const vueDossierTel = compact && vueDossier && dossierGed !== null/.test(app),
  'TÉMOIN : hors téléphone, la liste classique à plat d\'aujourd\'hui')
voir(/\{documents\.length > 0 && vueDossierTel \? rendreLeDossier\(\(e\) => carteClassique\(e\.doc\)\) : null\}/.test(app), 'au téléphone : « Le dossier », chaque ligne dépliée montre la carte classique')
const enrAvant = entre(avant7, '    const docTypeOf = (name: string): [string, string] => {', '    const cntAll = enriched.length')
const enrApres = entre(app, '  const docTypeOf = (name: string): [string, string] => {', '  const ligneDocument')
voir(enrAvant && enrApres && retrait(enrAvant, 2).trimEnd() === enrApres.slice(0, enrApres.indexOf('  // « Le dossier » : seulement')).trimEnd(),
  'le type, l\'état de signature et la pastille de chaque document (enriched) : sortis de la branche cockpit, identiques au caractère')
const ligAvant = entre(avant7, '    const ligneDocument = ', '\n    const ouvrirPuisSuivi')
const ligApres = entre(app, '  const ligneDocument = ', '\n  const ouvrirPuisSuivi')
const normalise = (t) => t.replace(', carte: (e: (typeof enriched)[number]) => ReactNode)', ')').replace('{carte(e)}', '{carteDocument(e)}').replace(/\n\s*\/\/ « Voir le suivi »[^\n]*\n[^\n]*$/, '')
voir(ligAvant && ligApres && normalise(retrait(ligAvant, 2)) === normalise(ligApres), 'la ligne repliée/dépliée : identique au caractère, sauf la carte qu\'elle reçoit')
const blocAvant = entre(avant7, '        {vueDossier && dossierGed ? (\n          <div className="gd3-dossier">', '\n        ) : null}\n')
const blocApres = entre(app, '  const rendreLeDossier = (carte: (e: (typeof enriched)[number]) => ReactNode) => (dossierGed ? (\n        <div className="gd3-dossier">', '\n  ) : null)\n')
const sansEntete = (t) => t.slice(t.indexOf('<div className="gd3-dossier">')).replace(/, carte\)/g, ')')
voir(blocAvant && blocApres && sansEntete(retrait(blocAvant, 2)) === sansEntete(blocApres), 'les groupes, les pièces manquantes, « Déposer », « Autres documents » : identiques au caractère (seule la carte passe en argument)')

console.log('④ le rangement par moment (lib/gedPieces.ts, fonction neuve)')
const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, 'src/lib/gedPieces.ts')], bundle: true, write: false, format: 'cjs', platform: 'node' }).outputFiles[0].text
const m = { exports: {} }; new Function('module', 'exports', 'require', code)(m, m.exports, require)
const { dossierParMoment, recuManque } = m.exports
const faits = { statut: 'Sous compromis', numeroMandat: '18836', copropriete: false }
const docs = [
  { nom: 'Promesse de vente signée.pdf', typeCode: 'transaction.compromis' },
  { nom: 'DPE 2024.pdf', typeCode: 'diag.dpe' },
  { nom: 'Mandat de vente signé.pdf', typeCode: 'mandat.vente' },
  { nom: 'Photo façade.jpg', typeCode: null },
]
const r = dossierParMoment(faits, docs)
voir(r.groupes[0].moment === r.moment && r.groupes[0].courant, `le moment en cours vient d'abord (${r.moment})`)
const cles = r.groupes.flatMap((g) => g.lignes.map((l) => l.cle))
voir(cles.length === new Set(cles).size, 'une pièce n\'apparaît qu\'une fois, dans le premier moment qui l\'attend')
voir(r.autres.includes('Photo façade.jpg') && !r.autres.includes('Mandat de vente signé.pdf'), 'un document sans pièce attendue va dans « Autres documents »')
const range = new Set(r.groupes.flatMap((g) => g.lignes.flatMap((l) => l.documents)))
voir(docs.every((d) => range.has(d.nom) || r.autres.includes(d.nom)), 'aucun document ne se perd (rangé, ou dans « Autres »)')
const avantRm = recuManque(faits, docs)
voir(JSON.stringify(avantRm) === JSON.stringify(recuManque(faits, docs)) && r.groupes[0].recues === avantRm.recues && r.groupes[0].attendues === avantRm.attendues,
  'le moment en cours compte comme « Le dossier » d\'aujourd\'hui (recuManque inchangé)')

console.log(ko ? `\n${ko} ROUGE, ${ok} VERT` : `\nTOUT EST VERT (${ok})`)
process.exit(ko ? 1 : 0)
