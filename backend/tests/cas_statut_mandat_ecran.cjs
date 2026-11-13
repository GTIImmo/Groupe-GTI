// Assistant IA, étape 2 (12/11/2026) -- LE STATUT D'UN MANDAT, CALCULÉ PAR LE VRAI CODE DE L'ÉCRAN.
//
// Décision de Frédéric du 12/11 (« B ») : le calcul est posé UNE fois dans la base
// (supabase/patch_assistant_ia_etape2_statut_mandat_2026-11-12.sql). Ce script prouve que la base
// dit la même chose que l'écran : il extrait les fonctions de apps/hektor-v1/src/lib/api.ts (pas
// une recopie), les fait tourner sur tous les cas croisés, et écrit les attendus que la répétition
// SQL compare à la fonction de la base.
//
// Lancer depuis la racine du dépôt :  node backend/tests/cas_statut_mandat_ecran.cjs
// La sortie (5 affectations PL/pgSQL) se colle dans le bloc « LES CAS » de la répétition.
// Les dates sont des JETONS (HIER, AUJOURDHUI, DEMAIN…) : la répétition les remplace par la date du
// jour à Paris, ce script par la date du jour de la machine. L'attendu ne dépend donc pas du jour.
const fs = require('fs')
const path = require('path')

const racine = path.resolve(__dirname, '..', '..')
const esbuild = require(path.join(racine, 'apps', 'hektor-v1', 'node_modules', 'esbuild'))
const source = fs.readFileSync(path.join(racine, 'apps', 'hektor-v1', 'src', 'lib', 'api.ts'), 'utf8').replace(/\r\n/g, '\n')

function extraire(debut) {
  const i = source.indexOf(debut)
  if (i < 0) throw new Error('fonction introuvable dans api.ts : ' + debut)
  const fin = source.indexOf('\n}\n', i)
  return source.slice(i, fin + 2)
}

const morceaux = [
  'function normalizeMandateStatusValue(',
  'function isMandateEndDateStillValid(',
  'function mandateLifecycleState(',
  'export function mandatStatutForRegisterRow(',
].map(extraire).map((t) => t.replace(/^export /, ''))
const js = esbuild.transformSync('type MandatRecord = any\n' + morceaux.join('\n'), { loader: 'ts' }).code
const ecran = new Function(js + '\nreturn { mandateLifecycleState, mandatStatutForRegisterRow }')()

function jour(decalage) {
  const d = new Date()
  d.setDate(d.getDate() + decalage)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
// ⚠ L'écran ne rejette pas une date qui déborde : new Date('2026-02-30') = le 2 mars (mesuré le 12/11) ;
//   un mois 13, un jour 32 ou 00 sont « invalides » donc le mandat reste valide. 2 dates de fin de ce genre
//   existent dans le registre. Les formats autres que AAAA-MM-JJ (0 dans la base) ne sont PAS reproduits.
const DATES = { NULL: null, VIDE: '', HIER: jour(-1), AUJOURDHUI: jour(0), DEMAIN: jour(1), ANCIENNE: '2019-03-01', LOINTAINE: '2031-12-31',
  FEV30: '2026-02-30', FEV31: '2031-02-31', AVR31: '2031-04-31', MOIS13: '2026-13-01', MOIS00: '2026-00-10', JOUR32: '2026-01-32',
  JOUR00: '2026-01-00', AN0000: '0000-01-01', TEXTE: 'abc' }
const STATUTS = [null, '', 'Actif', ' Actif ', 'ACTIF', 'Vendu', 'Clos', 'Clôturé', 'Estimation', 'Sous compromis', 'Sous offre',
  'Recherche active', 'Sans recherche', 'Contact inconnu', 'Recherche archivée', 'En vente', 'Archivé']
const CLOTURES = [null, '', ' ', '2026-01-01', '2026-01-01 10:00:00']
const VENTES = [null, '', '12345']

const sql = (v) => (v === null ? 'null' : `'${String(v).replace(/'/g, "''")}'`)
const tableau = (liste) => `array[${liste.map(sql).join(', ')}]::text[]`
// Sortie COMPACTE : les quatre listes, et 2 lettres par cas dans l'ordre statut > date > clôture > vente
// (statut : A Actif, V Vendu, C Clos, E Échu ; état : O En cours, N Annulé). La répétition SQL refait
// le même produit croisé et compare lettre à lettre.
const CODE_STATUT = { Actif: 'A', Vendu: 'V', Clos: 'C', 'Échu': 'E' }
const CODE_ETAT = { 'En cours': 'O', 'Annulé': 'N' }
let codes = ''
for (const statut of STATUTS) for (const fin of Object.values(DATES)) for (const cloture of CLOTURES) for (const vente of VENTES) {
  const item = { statut_annonce: statut, mandat_date_fin: fin, mandat_date_cloture: cloture, vente_id: vente }
  const s = CODE_STATUT[ecran.mandatStatutForRegisterRow(item)], e = CODE_ETAT[ecran.mandateLifecycleState(item)]
  if (!s || !e) throw new Error("valeur inattendue de l'écran")
  codes += s + e
}
const dates = Object.entries(DATES).map(([jeton, v]) => (['HIER', 'AUJOURDHUI', 'DEMAIN'].includes(jeton) ? jeton : v))
process.stdout.write([
  `-- ${codes.length / 2} cas, attendus calculés par le code de l'écran (api.ts) le ${jour(0)}`,
  `statuts  := ${tableau(STATUTS)};`,
  `dates    := ${tableau(dates)};  -- HIER / AUJOURDHUI / DEMAIN = jetons remplacés par la date de Paris`,
  `clotures := ${tableau(CLOTURES)};`,
  `ventes   := ${tableau(VENTES)};`,
  `attendus := '${codes}';`,
].join('\n') + '\n')
