// A.2 lot 2 -- essai des repères Youtrust du mandat et de l'avenant, sur LE CODE RÉEL.   26/10/2026
// Les fonctions sont DÉCOUPÉES dans src/App.tsx (version du travail ET version du dernier commit,
// lue par git), traduites par le compilateur TypeScript du projet, puis exécutées avec LES MÊMES
// données d'essai et les mêmes doublures pour leurs dépendances lourdes. Aucune connexion.
//     node scripts/test_reperes_signature.mjs
//     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
// Ce qui est prouvé :
//   (A) interrupteur ÉTEINT : le HTML du mandat et de l'avenant est IDENTIQUE, au caractère près,
//       à celui du dernier commit (le PDF, lui, ne se compare pas : Chromium ne rend jamais deux
//       fois le même -- mesuré au lot 1) ;
//   (B) ALLUMÉ : un repère de signature par signataire (mandants 1..N, mandataire N+1), une
//       mention par mandant, tous invisibles, posés APRÈS le remplacement des {{...}} ;
//   (C) un gabarit sans zone de signatures fait REFUSER la génération (jamais un PDF muet).
import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'

const ici = path.dirname(fileURLToPath(import.meta.url))
const racine = path.join(ici, '..')
const require = createRequire(import.meta.url)
const ts = require('typescript')

const echecs = []
const controle = (nom, ok, detail) => { console.log(`${ok ? '  OK  ' : 'ECHEC '} ${nom}${ok ? '' : ' -- ' + (detail || '')}`); if (!ok) echecs.push(nom) }

let appNeuf, appAvant, gabarit, reperesTs
try {
  appNeuf = fs.readFileSync(process.env.TEST_APP_TSX || path.join(racine, 'src', 'App.tsx'), 'utf8')
  appAvant = execFileSync('git', ['show', 'HEAD:apps/hektor-v1/src/App.tsx'], { cwd: racine, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
  gabarit = fs.readFileSync(path.join(racine, 'src', 'mandat-template.html'), 'utf8')
  reperesTs = fs.readFileSync(path.join(racine, 'src', 'lib', 'signatureAnchors.ts'), 'utf8')
} catch (e) {
  console.log('ECHEC  lecture des sources -- ' + e.message)
  process.exit(2)
}

function tranche(src, debut, fin = '\n}') {
  const i = src.indexOf(debut)
  if (i < 0) return null
  const f = src.indexOf(fin, i)
  return f < 0 ? null : src.slice(i, f + fin.length)
}
function ligne(src, debut) {
  const i = src.indexOf(debut)
  return i < 0 ? null : src.slice(i, src.indexOf('\n', i) + 1)
}

const NOMS = ['function escapeHtml(', 'function mandatMandantDisplayName(', 'function checkedEntity(',
  'function splitMandatCoverSection(', 'function normalizeMandatPrintContent(', 'function mandatSignatureBlocksHtml(',
  'function renderMandatTemplate(', 'function mandatPreviewHtml(', 'function avenantPreviewHtml(']
const NOMS_NEUFS = ['const AVENANT_DEBUT_SIGNATURES', 'function avenantSignatureBlocksHtml(', 'function avenantAvecReperes(']

// Doublures : les MÊMES pour les deux versions -- la comparaison porte sur le code découpé.
const doublures = `
function buildMandatDocumentMandants() { return [{ civilite: '', prenom: '', nom: '' }] }
function firstNonEmpty(v) { return v == null ? '' : String(v) }
function textOrPlaceholder(value, placeholder = 'A completer') { const t = firstNonEmpty(value); return escapeHtml(t || placeholder) }
function mandatMandantsHtml(mandants, libelle) { return '<div class="mandants">' + escapeHtml(libelle) + '</div>' }
function mandatTemplateLookup(payload, key) { return key === 'mandat.date_signature' ? '26/10/2026' : 'valeur ' + key }
function formatFreeTextHtml(v, d) { return escapeHtml(v || d) }
function formatDraftDate(v) { return v || '' }
function buildMandatDocumentPayload(draft) {
  return { honoraires: { charge: 'mandant' }, options: { execution_anticipee_demandee: 'non' },
    mandants_libelle: draft.mandants.map((m) => m.nom).join(' et '),
    agence: { nom: 'GTI Saint-Etienne', adresse: '1 rue A', code_postal: '42000', ville: 'Saint-Etienne', telephone: '04', email: 'a@b.fr' },
    negociateur: { nom_complet: 'Nego Essai' } }
}`

function charger(src, avecNeufs, gabaritHtml) {
  const morceaux = NOMS.map((n) => [n, tranche(src, n)])
  if (avecNeufs) {
    morceaux.push([NOMS_NEUFS[0], ligne(src, NOMS_NEUFS[0])])
    for (const n of NOMS_NEUFS.slice(1)) morceaux.push([n, tranche(src, n)])
  }
  const manquants = morceaux.filter(([, m]) => !m).map(([n]) => n)
  if (manquants.length) return { manquants }
  const lib = reperesTs.replace(/^export /gm, '')
  const js = ts.transpileModule(
    [lib, doublures, `const mandatTemplateHtml = ${JSON.stringify(gabaritHtml)}`, ...morceaux.map(([, m]) => m),
      'return { mandatPreviewHtml, avenantPreviewHtml }'].join('\n'),
    { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText
  return { f: new Function(js)() }
}

const neuf = charger(appNeuf, true, gabarit)
const avant = charger(appAvant, false, gabarit)
controle('(1) LA PREUVE D\'ABORD : les fonctions sont dans les deux versions',
  !neuf.manquants && !avant.manquants, [...(neuf.manquants || []), ...(avant.manquants || [])].join(', '))
if (neuf.manquants || avant.manquants) process.exit(2)

const mandant = (i) => ({ civilite: 'M.', prenom: `Prenom${i}`, nom: `NOM${i}`, adresse: `${i} rue de l'Essai`, telephone: '+33600000000', email: `m${i}@exemple.fr` })
const brouillon = (n) => ({ mandants: Array.from({ length: n }, (_, i) => mandant(i + 1)), inclureCouverture: true,
  clauseParticuliere: '', numeroMandat: '18999', bienAdresse: '1 rue du Bien', dateSignature: '26/10/2026',
  prixVente: '200 000', honorairesTtc: '10 000', mandantsLibelle: '' })
const dossier = { titre_bien: 'Maison', commercial_nom: 'Nego' }
const compte = (s, motif) => (s.match(motif) || []).length

// (A) éteint = identique au dernier commit
for (const n of [1, 2, 4]) {
  const ref = avant.f.mandatPreviewHtml(brouillon(n), dossier, [])
  controle(`(A) mandat ${n} mandant(s), éteint, sans option : identique`, neuf.f.mandatPreviewHtml(brouillon(n), dossier, []) === ref)
  controle(`(A) mandat ${n} mandant(s), éteint, { reperes:false } : identique`, neuf.f.mandatPreviewHtml(brouillon(n), dossier, [], { reperes: false }) === ref)
}
for (const n of [1, 2, 3]) {
  const ref = avant.f.avenantPreviewHtml(brouillon(n), dossier)
  controle(`(A) avenant ${n} mandant(s), éteint, sans option : identique`, neuf.f.avenantPreviewHtml(brouillon(n), dossier) === ref)
  controle(`(A) avenant ${n} mandant(s), éteint, { reperes:false } : identique`, neuf.f.avenantPreviewHtml(brouillon(n), dossier, { reperes: false }) === ref)
}

// (B) allumé
for (const n of [1, 2, 4, 12]) {
  const h = neuf.f.mandatPreviewHtml(brouillon(n), dossier, [], { reperes: true })
  const sig = [...h.matchAll(/\{\{s(\d+)\|signature\|150\|45\}\}/g)].map((m) => Number(m[1]))
  const men = [...h.matchAll(/\{\{s(\d+)\|mention\|Bon pour mandat\|mention_s\1\}\}/g)].map((m) => Number(m[1]))
  controle(`(B) mandat ${n} : ${n + 1} repères de signature s1..s${n + 1}`, sig.join() === Array.from({ length: n + 1 }, (_, i) => i + 1).join(), sig.join())
  controle(`(B) mandat ${n} : ${n} mentions « Bon pour mandat » s1..s${n} (pas le mandataire)`, men.join() === Array.from({ length: n }, (_, i) => i + 1).join(), men.join())
  controle(`(B) mandat ${n} : chaque repère est invisible (couleur du fond)`, compte(h, /class="yt-repere"[^>]*color:#fafbfc/g) === 2 * n + 1)
  controle(`(B) mandat ${n} : aucune accolade du gabarit oubliée`, compte(h, /\{\{(?!s\d+\|)/g) === 0)
}
for (const n of [1, 2, 3]) {
  const h = neuf.f.avenantPreviewHtml(brouillon(n), dossier, { reperes: true })
  const sig = [...h.matchAll(/\{\{s(\d+)\|signature\|150\|45\}\}/g)].map((m) => Number(m[1]))
  const men = [...h.matchAll(/\{\{s(\d+)\|mention\|Bon pour accord\|mention_s\1\}\}/g)].map((m) => Number(m[1]))
  controle(`(B) avenant ${n} : ${n + 1} repères de signature`, sig.join() === Array.from({ length: n + 1 }, (_, i) => i + 1).join(), sig.join())
  controle(`(B) avenant ${n} : ${n} mentions « Bon pour accord »`, men.join() === Array.from({ length: n }, (_, i) => i + 1).join(), men.join())
  controle(`(B) avenant ${n} : l'ancienne case unique « Le mandant » a disparu`, !h.includes('Signature pr&eacute;c&eacute;d&eacute;e de la mention'))
  controle(`(B) avenant ${n} : le reste du document est intact (même début, même fin)`,
    h.startsWith(avant.f.avenantPreviewHtml(brouillon(n), dossier).split('<table style="border-collapse:separate; border-spacing:0; width:100%"><tbody><tr>\n<td style="padding:0 8px 0 0;')[0])
    && h.endsWith('<div style="height:10px;">&nbsp;</div>\n</div>\n</body></html>'))
}

// (C) refus si la zone des signatures est introuvable
const sansZone = charger(appNeuf, true, gabarit.replace(/<table cellspacing="0" style="border-collapse:separate;border-spacing:12px 0;margin-top:7px;width:100%">[\s\S]*?<\/table>/, ''))
let refuse = false
try { sansZone.f.mandatPreviewHtml(brouillon(2), dossier, [], { reperes: true }) } catch (e) { refuse = /introuvable/.test(e.message) }
controle('(C) mandat sans zone de signatures + repères demandés : génération REFUSÉE', refuse)
let refuseEteint = true
try { sansZone.f.mandatPreviewHtml(brouillon(2), dossier, []) } catch { refuseEteint = false }
controle('(C) …mais éteint, rien ne change (pas de refus)', refuseEteint)

// Pour l'essai sandbox : écrit le HTML RÉEL (gabarit du projet, données d'essai) avec repères.
if (process.env.TEST_DUMP_DIR) {
  fs.mkdirSync(process.env.TEST_DUMP_DIR, { recursive: true })
  fs.writeFileSync(path.join(process.env.TEST_DUMP_DIR, 'mandat_2_mandants.html'), neuf.f.mandatPreviewHtml(brouillon(2), dossier, [], { reperes: true }))
  fs.writeFileSync(path.join(process.env.TEST_DUMP_DIR, 'avenant_2_mandants.html'), neuf.f.avenantPreviewHtml(brouillon(2), dossier, { reperes: true }))
  console.log(`HTML d'essai écrits dans ${process.env.TEST_DUMP_DIR}`)
}

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : '\nTOUT EST VERT')
process.exit(echecs.length ? 1 : 0)
