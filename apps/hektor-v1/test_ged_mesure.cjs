// GED morceau 10 (16/11/2026) : essais hors ligne de la MESURE -- juger les lignes « À regarder ».
//   node test_ged_mesure.cjs
// ① la clé d'une ligne ; ② la lecture des jugements contre une fausse base (le plus récent fait foi, une panne -> null) ;
// ③ le patch SQL (verdicts, droits, porte, interrupteur, répétition SANS commit) ; ④ le branchement à l'écran.
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

let ok = 0, ko = 0
const voir = (vrai, libelle) => { if (vrai) { ok++; console.log('  VERT  ' + libelle) } else { ko++; console.log('  ROUGE ' + libelle) } }
const construire = (f, supa) => {
  const code = esbuild.buildSync({ entryPoints: [path.join(__dirname, f)], bundle: true, write: false, format: 'cjs', platform: 'node', external: ['./supabase', 'react'] }).outputFiles[0].text
  const m = { exports: {} }
  new Function('module', 'exports', 'require', code)(m, m.exports, (n) => (n === './supabase' ? supa : n === 'react' ? { useEffect() {}, useState: (x) => [x, () => {}] } : require(n)))
  return m.exports
}
const { cleJugement, VERDICTS, LIBELLE_VERDICT } = construire('src/lib/gedMesure.ts', { hasSupabaseEnv: false, supabase: null })

console.log('① la clé d\'une ligne')
const P9 = { code: 'P9', texte: 'Mandant ESSAI CONTACT est marié(e) depuis le 20/06/1987 avec Claire SPECIMEN' }
voir(cleJugement(P9) === cleJugement({ code: 'P9', texte: 'MANDANT essai contact est marie(e) depuis le 20/06/1987 avec claire specimen' }), 'la même ligne, à la casse et aux accents près -> la même clé')
voir(cleJugement(P9) !== cleJugement({ ...P9, texte: P9.texte.replace('1987', '1988') }), 'TÉMOIN : un texte qui change (une date) -> une AUTRE ligne, à rejuger')
voir(cleJugement(P9) !== cleJugement({ ...P9, code: 'P10' }), 'TÉMOIN : la même phrase sous une autre règle -> une autre clé')
voir(cleJugement(P9).startsWith('P9|'), 'la clé commence par la règle (le compte rendu groupe par règle)')
voir(VERDICTS.map((v) => v.code).join(',') === 'vrai,faux,deja_su' && LIBELLE_VERDICT.deja_su === 'déjà su', 'trois verdicts : vrai, faux, déjà su')

console.log('② la lecture des jugements, contre une fausse base')
let lignes = []
let enPanne = false
let derniereRpc = null
const fausseBase = {
  from: (t) => ({ select: () => ({ eq: (col, val) => ({ order: async () => (enPanne ? { data: null, error: { message: 'relation "app_ged_jugement" does not exist' } } : { data: lignes.filter((l) => l[col] === val), error: null }) }) }) }),
  rpc: async (nom, params) => { derniereRpc = { nom, params }; return { error: null } },
}
const ged = construire('src/lib/ged.ts', { hasSupabaseEnv: true, supabase: fausseBase })
;(async () => {
  lignes = [
    { hektor_annonce_id: '63331', cle: 'P9|x', verdict: 'faux', juge_le: '2026-11-17T10:00:00Z' },
    { hektor_annonce_id: '63331', cle: 'P9|x', verdict: 'vrai', juge_le: '2026-11-16T10:00:00Z' },
    { hektor_annonce_id: '63331', cle: 'N2|y', verdict: 'deja_su', juge_le: '2026-11-16T09:00:00Z' },
    { hektor_annonce_id: '99999', cle: 'P9|x', verdict: 'vrai', juge_le: '2026-11-18T10:00:00Z' },
  ]
  const m = await ged.loadGedJugements('63331')
  voir(m.size === 2 && m.get('P9|x').verdict === 'faux', 'une ligne rejugée : le PLUS RÉCENT fait foi (la base rend du plus récent au plus ancien)')
  voir(m.get('N2|y').verdict === 'deja_su', 'chaque ligne garde son verdict')
  enPanne = true
  voir((await ged.loadGedJugements('63331')) === null, 'TÉMOIN : table absente ou lecture ratée -> null (les boutons ne s\'affichent pas)')
  enPanne = false
  await ged.gedJuger({ hektorAnnonceId: 63331, regle: 'P9', cle: 'P9|x', texte: 'x', niveau: 'alerte', verdict: 'vrai' })
  voir(derniereRpc.nom === 'app_ged_juger' && derniereRpc.params.p_hektor_annonce_id === '63331' && derniereRpc.params.p_commentaire === null,
    'l\'écriture passe par la SEULE porte app_ged_juger, numéro en texte, sans commentaire par défaut')
  voir(Object.keys(derniereRpc.params).sort().join(',') === 'p_cle,p_commentaire,p_hektor_annonce_id,p_niveau,p_regle,p_texte,p_verdict', 'les 7 paramètres de la porte, ni plus ni moins (pas d\'auteur : c\'est auth.uid())')

  console.log('③ le patch SQL')
  const sql = (f) => fs.readFileSync(path.join(__dirname, '..', '..', 'supabase', f), 'utf8')
  const patch = sql('patch_ged_m10_jugement_2026-11-16.sql')
  const repet = sql('patch_ged_m10_jugement_2026-11-16_REPETITION.sql')
  const inverse = sql('patch_ged_m10_jugement_2026-11-16_INVERSE.sql')
  voir(/check \(verdict in \('vrai', 'faux', 'deja_su'\)\)/.test(patch), 'la base n\'accepte que les trois verdicts de l\'écran')
  voir(/revoke all on table public\.app_ged_jugement from public, anon, authenticated;\s*grant select on table public\.app_ged_jugement to authenticated;/.test(patch), 'authenticated LIT seulement ; anon rien')
  voir(/security definer/.test(patch) && /key = 'ged_propositions'/.test(patch) && /is_app_admin\(\)/.test(patch) && /app_mes_biens_portefeuille/.test(patch), 'la porte : SECURITY DEFINER, interrupteur ged_propositions pour l\'appelant, périmètre du bien')
  voir(/auth\.uid\(\)\)\s*returning id/.test(patch) && !/p_juge_par/.test(patch), 'l\'auteur est auth.uid(), jamais un paramètre')
  voir(!/insert into public\.app_setting/.test(patch) && !/update public\.app_setting/.test(patch), 'TÉMOIN : le patch ne touche à AUCUN interrupteur')
  voir(!/\bcommit\b\s*;/i.test(repet.replace(/--.*$/gm, '')) && /rollback;\s*$/.test(repet.trim() + '\n'), 'la répétition ne porte AUCUN commit et finit par rollback (leçon du 13/11)')
  voir(!/delete from public\.app_setting/.test(inverse) && /drop table if exists public\.app_ged_jugement/.test(inverse), 'le retour arrière retire la table et la porte, et laisse ged_propositions')

  console.log('④ le branchement à l\'écran')
  const rm = fs.readFileSync(path.join(__dirname, 'src/RecuManque.tsx'), 'utf8')
  voir(/if \(!regles\) return[\s\S]{0,120}loadGedJugements\(hektorAnnonceId\)/.test(rm), 'les jugements ne se lisent que si les lignes « À regarder » sont ouvertes (ged_propositions)')
  // Visuel V3, morceau 4 (20/11, décision de Frédéric) : la période de test est retirée -- plus de « Vrai / Faux / Déjà
  // su » ; « Masquer » (pour tout le monde sur le bien) et « Réafficher », écrits dans le MÊME journal.
  voir(/\{jugements \? \(\s*<button type="button" className="gm2-lien gm2-masquer"/.test(rm) && !/aria-label=\{`Juger : /.test(rm) && !/VERDICTS\.map/.test(rm),
    '« Masquer » n\'existe que si la lecture des jugements a réussi ; plus aucune barre « Vrai / Faux / Déjà su »')
  voir(/onClick=\{\(\) => void juger\(a, 'masque'\)\}/.test(rm) && /verdict: 'reaffiche'/.test(rm) && /estMasquee\(jugements\.get\(cleJugement\(a\)\)\?\.verdict\)/.test(rm),
    'Masquer écrit « masque », Réafficher écrit « reaffiche » ; seule une ligne dont le dernier mot est « masque » est masquée')
  voir(/const alertesVisibles = alertes\.filter\(\(a\) => !lieeAUneCarte\(a\) && !masquees\.includes\(a\)\)/.test(rm), 'une alerte déjà montrée par une fenêtre « Ce que dit… » n\'a plus sa propre carte (le doublon)')
  voir(!/verdictDesChoix/.test(rm), 'enregistrer une fenêtre n\'écrit plus de note de mesure')
  voir(/\{nbATraiter > 0 \? \(\s*<div className="gm2-traiter-h"/.test(rm), 'rien à traiter (tout masqué) : pas d\'en-tête « À traiter 0 » (décision du 26/11)')
  voir(/const cle = cleJugement\(a\)[\s\S]{0,200}gedJuger\(\{ hektorAnnonceId, regle: a\.code, cle, texte: a\.texte, niveau: a\.niveau, verdict \}\)/.test(rm), 'le jugement garde la règle, la clé, le texte et le niveau TELS QU\'AFFICHÉS')
  // habillage H1 (16/11) : la ligne n'est plus un bouton ; « Déposer la pièce » est un bouton de la carte, la barre sa voisine
  const bloc = rm.slice(rm.indexOf('{alertesVisibles.map((a, i) => {'), rm.indexOf('gm2-lus'))
  voir(/>Déposer la pièce<\/button>[\s\S]*className="gm2-lien gm2-masquer"/.test(bloc), '« Masquer » est À CÔTÉ du bouton « Déposer », jamais dedans')
  const gm = fs.readFileSync(path.join(__dirname, 'src/lib/gedMesure.ts'), 'utf8')
  voir(/export const estMasquee = \(verdict: VerdictGed \| null \| undefined\): boolean => verdict === 'masque'/.test(gm), 'TÉMOIN : « vrai », « faux », « déjà su » (8 jugements du 17-19/11) ne masquent rien')
  voir(!/gedJuger|loadGedJugements/.test(fs.readFileSync(path.join(__dirname, 'src/lib/gedRegles.ts'), 'utf8')), 'TÉMOIN : les règles elles-mêmes ne savent rien des jugements (on mesure, on ne change pas les règles)')

  console.log(`\n${ok} verts, ${ko} rouges`)
  process.exit(ko ? 1 : 0)
})()
