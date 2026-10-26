// REPETITION de supabase/patch_catalogue_registre_une_lecture_2026-10-26.sql             26/10/2026
// Compare l'ANCIENNE lecture des menus (25 pages du registre, code de api.ts recopie a l'identique)
// et la NOUVELLE (valeurs brutes de la vue app_filter_catalog_registre, meme uniqSorted).
// Lecture seule : GET sur l'API avec la cle de service (elle voit tout le registre, comme un admin).
//   node phase2/checks/comparer_catalogue_registre.mjs . --vue        (apres la pose : lit la vraie vue)
//   node phase2/checks/comparer_catalogue_registre.mjs . valeurs.json (avant : valeurs sorties d'un essai annule)
// Sortie 0 = les 7 listes identiques (contenu ET ordre) ; 1 = un ecart, affiche.
// Temoin inverse fait le 26/10 : une agence retiree des valeurs nouvelles -> « DIFFERENT », sortie 1.
import fs from 'node:fs'

const [, , racine, vueJson] = process.argv
const env = {}
for (const f of ['.env', 'backend/.env', 'apps/hektor-v1/.env']) {
  const p = `${racine}/${f}`
  if (!fs.existsSync(p)) continue
  for (const l of fs.readFileSync(p, 'utf8').split(/\r?\n/)) {
    if (!l.includes('=') || l.trimStart().startsWith('#')) continue
    const i = l.indexOf('=')
    const k = l.slice(0, i).trim()
    if (!(k in env)) env[k] = l.slice(i + 1).trim().replace(/^['"]|['"]$/g, '')
  }
}
const url = env.SUPABASE_URL || env.VITE_SUPABASE_URL
const key = env.SUPABASE_SERVICE_ROLE_KEY

// ─── recopie EXACTE de api.ts ───
function uniqSorted(values) {
  return Array.from(new Set(values.map((value) => (value ?? '').trim()).filter(Boolean))).sort((a, b) =>
    a.localeCompare(b, 'fr'),
  )
}

async function ancienne() {
  const batchSize = 1000
  let from = 0
  const commercials = [], agencies = [], statuts = [], validationDiffusions = [], passerelles = [], diffusions = []
  let lectures = 0
  const t0 = Date.now()
  while (true) {
    const q = `${url}/rest/v1/app_registre_mandats_current?select=register_row_id,commercial_nom,agence_nom,statut_annonce,validation_diffusion_state,portails_resume,diffusable,numero_mandat`
      + `&numero_mandat=not.is.null&numero_mandat=neq.&order=register_row_id.asc`
    const r = await fetch(q, { headers: { apikey: key, Authorization: `Bearer ${key}`, Range: `${from}-${from + batchSize - 1}` } })
    lectures++
    if (!r.ok) throw new Error(`HTTP ${r.status} ${await r.text()}`)
    const data = await r.json()
    if (data.length === 0) break
    for (const row of data) {
      commercials.push((row.commercial_nom ?? '').trim())
      agencies.push((row.agence_nom ?? '').trim())
      statuts.push(row.statut_annonce ?? '')
      validationDiffusions.push(row.validation_diffusion_state ?? '')
      diffusions.push((row.diffusable ?? '0') === '1' ? 'diffusable' : 'non_diffusable')
      passerelles.push(...(row.portails_resume ?? '').split(',').map((value) => value.trim()))
    }
    if (data.length < batchSize) break
    from += batchSize
  }
  return {
    lectures, ms: Date.now() - t0,
    res: {
      commercials: uniqSorted(commercials), agencies: uniqSorted(agencies), statuts: uniqSorted(statuts),
      validationDiffusions: uniqSorted(validationDiffusions), diffusions: uniqSorted(diffusions),
      passerelles: uniqSorted(passerelles), erreursDiffusion: ['avec_erreur', 'sans_erreur'],
    },
  }
}

// ─── la NOUVELLE lecture : meme code que lireCatalogueDuRegistreEnUneLecture ───
function nouvelle(data) {
  const valeurs = { commercial: [], agence: [], statut: [], validation_diffusion_state: [], diffusable: [], passerelle: [] }
  for (const row of data) {
    if (valeurs[row.filter_type]) valeurs[row.filter_type].push(row.filter_value ?? '')
  }
  return {
    commercials: uniqSorted(valeurs.commercial), agencies: uniqSorted(valeurs.agence), statuts: uniqSorted(valeurs.statut),
    validationDiffusions: uniqSorted(valeurs.validation_diffusion_state), diffusions: uniqSorted(valeurs.diffusable),
    passerelles: uniqSorted(valeurs.passerelle), erreursDiffusion: ['avec_erreur', 'sans_erreur'],
  }
}

async function lireLaVue() {
  const r = await fetch(`${url}/rest/v1/app_filter_catalog_registre?select=filter_type,filter_value`,
    { headers: { apikey: key, Authorization: `Bearer ${key}` } })
  if (!r.ok) throw new Error(`la vue ne se lit pas : HTTP ${r.status} ${await r.text()}`)
  return r.json()
}
const vue = vueJson === '--vue'
  ? await lireLaVue()
  : JSON.parse(fs.readFileSync(vueJson, 'utf8')).map(([filter_type, filter_value]) => ({ filter_type, filter_value }))
const a = await ancienne()
const n = nouvelle(vue)
let ecarts = 0
for (const k of Object.keys(a.res)) {
  const sa = JSON.stringify(a.res[k]), sn = JSON.stringify(n[k])
  const ok = sa === sn
  if (!ok) ecarts++
  console.log(`${ok ? 'IDENTIQUE' : '!! DIFFERENT'}  ${k.padEnd(22)} ancienne ${String(a.res[k].length).padStart(3)} · nouvelle ${String(n[k].length).padStart(3)}`)
  if (!ok) {
    console.log('   seulement ancienne :', a.res[k].filter((x) => !n[k].includes(x)))
    console.log('   seulement nouvelle :', n[k].filter((x) => !a.res[k].includes(x)))
    console.log('   ordre ancienne     :', a.res[k].join(' | '))
    console.log('   ordre nouvelle     :', n[k].join(' | '))
  }
}
console.log(`ancienne : ${a.lectures} lectures, ${a.ms} ms (cle de service, sans la regle) · ecarts : ${ecarts}`)
process.exit(ecarts ? 1 : 0)
