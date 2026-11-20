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
const actionsApres = entre(app, '  const docRowActions = (document: ConsoleDocument) => {', '  // ---- Skin « v21 »')
voir(actionsAvant && actionsAvant === actionsApres, 'docRowActions : identique au caractère (Ouvrir, Préparer, Preuves, Relancer, Annuler, Signature, Signé à la main, Supprimer)')
const carteAvant = entre(avant, '          {shown.map((e) => (\n', '\n          ))}\n        </div>')
const carteApres = entre(app, '    const carteDocument = (e: (typeof enriched)[number]) => (\n', '\n    )\n')
voir(carteAvant && carteApres && carteAvant.replace('          {shown.map((e) => (\n', '').trimEnd() === carteApres.replace('    const carteDocument = (e: (typeof enriched)[number]) => (\n', '').trimEnd(),
  'la carte d\'un document (nom, type, visibilité, état de signature, Remplacé, mention de dépôt, suivi des signataires, gestes) : identique au caractère')
voir((app.match(/carteDocument\(e\)/g) || []).length === 2, 'la carte est montée par la liste à plat ET par la ligne dépliée (et nulle part ailleurs)')
voir((app.match(/<SuiviSignatairesYoutrust (preuvesActives=\{preuvesActives\} )?document=/g) || []).length === 3, 'le suivi des signataires reste monté aux trois mêmes endroits')
const fenetres = ['<PiecesSignatureFenetre document={piecesDoc}', '<ChoixSignatureFenetre', '<SignaturePromptModal', '<EnvoiSignatureYoutrust']
voir(fenetres.every((f) => (app.match(new RegExp(f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length === (avant.match(new RegExp(f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length),
  'les fenêtres de signature : autant qu\'avant, aux mêmes endroits')

console.log('② les deux conditions de la session signature (20/11)')
voir(/const ouvrirPuisSuivi = \(d: ConsoleDocument\) => \{[\s\S]{0,400}setLigneDocOuverte\(d\.id\)[\s\S]{0,80}window\.setTimeout\(\(\) => allerAuSuivi\(d\), 120\)/.test(app)
  && /onVoirSuivi=\{\(\) => \{ const d = choixDoc; setChoixDoc\(null\); ouvrirPuisSuivi\(d\) \}\}/.test(app),
  '« Voir le suivi » déplie le groupe et la ligne, PUIS défile jusqu\'au suivi')
voir((app.match(/allerAuSuivi\(d\) \}\}/g) || []).length === 2, 'TÉMOIN : le classic et le suivi du mandat gardent leur « Voir le suivi » d\'avant')
voir(/const etatSignature = e\.sigLabel && !\/\^À envoyer\/\.test\(e\.sigLabel\) \? e\.sigLabel : null/.test(app) && /\{etatSignature \? <small className=\{`gd3-sig/.test(app)
  && /<span className="gd3-etat">\s*\{e\.remplace \? <span className="ens-pill-remplace">Remplacé<\/span> : <span className=\{`fa-ck-docbadge/.test(app),
  'ligne REPLIÉE : la pastille d\'état (Signé, En signature, Expirée…) ET « signée le / expirée le … à renvoyer / en attente » restent visibles')

console.log('③ le classic et les autres filtres ne bougent pas')
voir(/rangeEnListe = false, onDossier,/.test(rm) && /rangeEnListe=\{skin === 'v21'\}/.test(app) && /onDossier=\{skin === 'v21' \? setDossierGed : undefined\}/.test(app), 'le réglage n\'est allumé qu\'au cockpit (absent = l\'écran d\'avant)')
voir(/\{!rangeEnListe \? <div className="gm2-feuilles"/.test(rm) && /\{lus\.length && !rangeEnListe \? \(/.test(rm), 'sans le réglage, la grille de pièces et « Lu par l\'IA » s\'affichent comme avant')
voir(/const vueDossier = docFilter === 'tous' && dossierGed !== null/.test(app) && /\{\(vueDossier && dossierGed \? \[\] : shown\)\.map\(\(e\) => carteDocument\(e\)\)\}/.test(app),
  '« À préparer », « Signés », « Cloud » : la liste à plat d\'aujourd\'hui')

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
