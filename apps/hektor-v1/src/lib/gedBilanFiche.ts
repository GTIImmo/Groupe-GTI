// GED lot 3 (18/11/2026) -- LA FICHE DU BIEN FACE À SES DOCUMENTS : « Ce que dit le DPE », « Ce que dit l'état des
// risques », la fiche synthétique et l'appel de fonds de la copropriété, le métré (Carrez). Même fenêtre que le compromis
// (BilanCompromis.tsx), même modèle de ligne ; fonction pure, essais hors ligne dans test_ged_bilan.cjs.
// Lot A (18/11) : les six rapports de diagnostic et le dossier de diagnostics (DDT) -- §12.41 de la note du chantier.
// Frédéric (17/11) : « à trancher doit proposer de corriger le registre avec la donnée du doc » -- une case REMPLIE qui
// diffère se propose à corriger ; une case VIDE se propose à ajouter (les cartes « Remplir » P1 et P2 sont retirées : un
// seul chemin par case). L'écriture passe par le geste EXISTANT de la fiche (editAnnonceOptimistic -> le worker, ~10 min,
// contrôle au retour), sans modale : l'écran relit la case et n'écrit que si elle porte encore `temoin`.
// ⛔ Le MANDAT (numéro, prix, honoraires, charge, prix d'un avenant) n'a pas de bilan : décision ⑦-7, « je ne souhaite pas
//   pouvoir modifier un mandat » -- ses écarts restent dans « À regarder » (L12, L14, L4, L1). La charge du registre, vide,
//   reste une carte « Remplir » (P3). Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.30 et §12.31.
import { annualiser, comparerNombre, dateLue, lireDateIso, lireNombre, nombreLu, texteLu, TOLERANCES } from './gedComparer'
import type { BilanCompromis, EtatBilan, GenreFiche, LigneBilan } from './gedBilanCompromis'
import type { FaitsRemplir } from './gedRemplir'
import type { DocumentLu } from './gedReglesLues'

const jjmmaaaa = (iso: string) => { const [a, m, j] = iso.slice(0, 10).split('-'); return `${j}/${m}/${a}` }
const nombreClair = (x: number) => String(Math.round(x * 100) / 100).replace('.', ',')
const nombreTexte = (x: number) => String(Math.round(x * 100) / 100)

function plusRecent(docs: DocumentLu[], types: string[], cleDate: string): DocumentLu | null {
  const deType = docs.filter((d) => types.includes(d.lecture.typeCode) && d.lecture.etat === 'lu')
  if (!deType.length) return null
  return deType.reduce((a, b) => {
    const da = lireDateIso(dateLue(a.lecture.valeurs, cleDate))
    const db = lireDateIso(dateLue(b.lecture.valeurs, cleDate))
    return db && (!da || db > da) ? b : a
  })
}

type Ligne = Pick<LigneBilan, 'cle' | 'libelle' | 'etat' | 'lu' | 'valeur' | 'transaction' | 'page' | 'champFiche' | 'temoin'> & Partial<Pick<LigneBilan, 'note' | 'regle'>>
const ligne = (l: Ligne): LigneBilan => ({
  destination: 'hektor', champModale: null, condition: null, attente: null, fige: null, note: null, regle: null, ...l,
})
const bilan = (genre: GenreFiche, d: DocumentLu, lignes: LigneBilan[]): BilanCompromis | null => (lignes.length ? {
  genre, lectureId: d.lecture.id ?? null, nom: d.nom, luLe: d.lecture.luLe, affaireId: 0, dateTransaction: null, conditionsLues: true, conditionsGenerales: [], lignes,
} : null)
const pageDe = (d: DocumentLu, cle: string) => d.lecture.valeurs.find((x) => x.cle === cle && x.rang === 0)?.page ?? null
// une date de la fiche : vide, ou « AAAA-MM-JJ » (Hektor met 0000-00-00 pour rien ; lireDateIso les écarte)
const dateFiche = (v: string | null | undefined) => { const d = lireDateIso(v); return d ? d.toISOString().slice(0, 10) : null }

// Un nombre lu face à la case de la fiche : vide -> ajouter ; différent au-delà de la tolérance -> trancher.
function nombre(d: DocumentLu, cle: string, cleLue: string, libelle: string, champ: string, lu: number | null, fiche: number | null,
  tol: { absolue: number; relative: number }, clair: (x: number) => string, regle: string, arrondi = true): LigneBilan | null {
  if (lu == null || lu <= 0) return null
  const valeur = arrondi ? Math.round(lu) : lu
  const etat: EtatBilan = fiche == null ? 'ajouter' : comparerNombre(valeur, fiche, tol) === 'different' ? 'trancher' : 'accord'
  return ligne({ cle, libelle, etat, lu: clair(valeur), valeur: arrondi ? String(valeur) : nombreTexte(valeur), transaction: fiche == null ? null : clair(fiche), page: pageDe(d, cleLue), champFiche: champ, temoin: fiche == null ? null : String(fiche), regle: etat === 'trancher' ? regle : null })
}
function uneDate(d: DocumentLu, cle: string, cleLue: string, libelle: string, champ: string, fiche: string | null | undefined): LigneBilan | null {
  const lue = dateLue(d.lecture.valeurs, cleLue)
  if (!lue) return null
  const base = dateFiche(fiche)
  const etat: EtatBilan = !base ? 'ajouter' : base !== lue.slice(0, 10) ? 'trancher' : 'accord'
  return ligne({ cle, libelle, etat, lu: jjmmaaaa(lue), valeur: lue.slice(0, 10), transaction: base ? jjmmaaaa(base) : null, page: pageDe(d, cleLue), champFiche: champ, temoin: base })
}

// Lot A (18/11, « chaque document a son Ce que dit… ») -- les six rapports de diagnostic : « diagnostic fait » (la case
// Hektor OUI / NON / vide : mesuré le 18/11 sur 4 000 fiches, OUI vient avec sa date, NON presque jamais) et sa date.
// Le dossier de diagnostics (DDT) dit les mêmes choses dans sa liste « diagnostics » : pour chaque case, le document le
// plus RÉCENT parle (un document daté passe devant un non daté ; à date égale, le rapport seul) -- un seul chemin par case.
const DIAGS = [
  { genre: 'diag_electricite', type: 'diag.electricite', nom: 'electricite', champ: 'diag_electrique', libelle: 'Diagnostic électricité', libelleDate: 'Date du diagnostic électricité', cleDate: 'date_etablissement', cleResultat: 'resultat' },
  { genre: 'diag_gaz', type: 'diag.gaz', nom: 'gaz', champ: 'diag_gaz', libelle: 'Diagnostic gaz', libelleDate: 'Date du diagnostic gaz', cleDate: 'date_etablissement', cleResultat: 'resultat' },
  { genre: 'diag_plomb', type: 'diag.plomb', nom: 'plomb', champ: 'diag_plomb', libelle: 'Constat plomb', libelleDate: 'Date du constat plomb', cleDate: 'date_etablissement', cleResultat: 'resultat' },
  { genre: 'diag_termites', type: 'diag.termites', nom: 'termites', champ: 'diag_termites', libelle: 'État termites', libelleDate: 'Date de l\'état termites', cleDate: 'date_etablissement', cleResultat: 'resultat' },
  { genre: 'diag_amiante', type: 'diag.amiante', nom: 'amiante', champ: 'diag_amiante', libelle: 'Repérage amiante', libelleDate: 'Date du repérage amiante', cleDate: 'date_etablissement', cleResultat: 'resultat' },
  { genre: 'diag_assainissement', type: 'diag.assainissement', nom: 'assainissement', champ: 'diag_assainissement', libelle: 'Contrôle d\'assainissement', libelleDate: 'Date du contrôle d\'assainissement', cleDate: 'date_controle', cleResultat: 'conformite' },
] as const
const RESULTATS: Record<string, string> = {
  sans_anomalie: 'sans anomalie', anomalies: 'anomalies', danger_grave: 'danger grave et immédiat', absence: 'absence', presence: 'présence',
  sous_le_seuil: 'sous le seuil', au_dessus_du_seuil: 'au-dessus du seuil', conforme: 'conforme', non_conforme: 'non conforme',
  travaux_obligatoires: 'travaux obligatoires', absence_installation: 'pas d\'installation', raccorde: 'raccordé au réseau',
}
// Lot B (18/11) -- la procédure du syndicat et le plan de sauvegarde (L17), lus dans la fiche synthétique ou le PV d'AG.
// Codes Hektor (formulaire « copropriete », boutons radio, relevés le 18/11 sur l'export de 62649) : ALERTE « soumis à une
// procédure d'alerte » (le mandataire ad hoc), REDRESSEMENT « procédure de redressement » (l'administration provisoire),
// PROCESS « procédure en cours », NOTPROCESS « pas de procédure en cours » ; plan de sauvegarde OUI / NON.
// ⚠ L'écran de saisie propose PAS_DE_PROCEDURE / PROCEDURE_EN_COURS, qui ne sont PAS des valeurs Hektor : lus comme leurs
// équivalents. Un PV ne prouve pas l'absence (consigne de lecture) : il ne parle que d'une procédure qu'il nomme.
const STATUT_LU: Record<string, string> = { aucune: 'NOTPROCESS', mandataire_ad_hoc: 'ALERTE', administration_provisoire: 'REDRESSEMENT', autre: 'PROCESS' }
const STATUT_CLAIR: Record<string, string> = { NOTPROCESS: 'Pas de procédure', ALERTE: 'Procédure d\'alerte', REDRESSEMENT: 'Procédure de redressement', PROCESS: 'Procédure en cours' }
const STATUT_ANCIEN: Record<string, string> = { PAS_DE_PROCEDURE: 'NOTPROCESS', PROCEDURE_EN_COURS: 'PROCESS' }
type Dit = { d: DocumentLu; date: string | null; page: number | null; code: string }
const leDernier = (a: Dit | null, b: Dit | null): Dit | null => (!a || !b ? a ?? b : b.date && (!a.date || b.date.slice(0, 10) > a.date.slice(0, 10)) ? b : a)
function ligneCode(s: Dit, cle: string, libelle: string, champ: string, fiche: string | null | undefined, clair: (c: string) => string, procedure: boolean): LigneBilan {
  const brut = String(fiche ?? '').trim().toUpperCase()
  const base = STATUT_ANCIEN[brut] ?? brut
  const etat: EtatBilan = !base ? 'ajouter' : base === s.code ? 'accord' : 'trancher'
  return ligne({ cle, libelle, etat, lu: clair(s.code), valeur: s.code, transaction: base ? clair(base) : null, page: s.page, champFiche: champ, temoin: String(fiche ?? '').trim() || null, regle: procedure && etat !== 'accord' ? 'L17' : null })
}

// une valeur NETTE d'une liste, à son rang
const auRang = (d: DocumentLu, cle: string, rang: number) => { const v = d.lecture.valeurs.find((x) => x.cle === cle && x.rang === rang); return v && v.etat === 'lu' ? v : null }
// ce qu'un document dit d'une case : sa date (ISO) et la page, ou rien
type Source = { d: DocumentLu; date: string | null; page: number | null; resultat: string | null }
const plusRecente = (a: Source | null, b: Source | null): Source | null => {
  if (!a || !b) return a ?? b
  return b.date && (!a.date || b.date.slice(0, 10) > a.date.slice(0, 10)) ? b : a
}
// le DDT le plus récent (par la date la plus récente qu'il porte : celle du DPE ou d'un rapport de sa liste)
function ddtPlusRecent(lus: DocumentLu[]): DocumentLu | null {
  const dateDe = (d: DocumentLu) => [dateLue(d.lecture.valeurs, 'dpe_date'), ...d.lecture.valeurs.filter((x) => x.cle === 'diagnostics.date_rapport' && x.etat === 'lu').map((x) => x.valeur_date)]
    .filter((x): x is string => !!x).map((x) => x.slice(0, 10)).sort().pop() ?? ''
  const ddts = lus.filter((d) => d.lecture.typeCode === 'diag.dossier')
  return ddts.length ? ddts.reduce((a, b) => (dateDe(b) > dateDe(a) ? b : a)) : null
}
// « diagnostic fait » : la case Hektor vaut OUI quand un rapport existe ; NON -> à trancher ; vide -> à ajouter
function ligneFait(s: Source, champ: string, libelle: string, fiche: string | null | undefined): LigneBilan {
  const brut = String(fiche ?? '').trim()
  const etat: EtatBilan = !brut ? 'ajouter' : brut.toUpperCase() === 'OUI' ? 'accord' : 'trancher'
  return ligne({
    cle: `F.${champ}`, libelle: `${libelle} réalisé`, etat, lu: 'Oui', valeur: 'OUI', transaction: !brut ? null : brut.toUpperCase() === 'OUI' ? 'Oui' : brut.toUpperCase() === 'NON' ? 'Non' : brut,
    page: s.page, champFiche: champ, temoin: brut || null, note: s.resultat ? `résultat lu : ${s.resultat}` : null,
  })
}
function ligneDateSource(s: Source, cle: string, libelle: string, champ: string, fiche: string | null | undefined): LigneBilan | null {
  if (!s.date) return null
  const lue = s.date.slice(0, 10)
  const base = dateFiche(fiche)
  const etat: EtatBilan = !base ? 'ajouter' : base !== lue ? 'trancher' : 'accord'
  return ligne({ cle, libelle, etat, lu: jjmmaaaa(lue), valeur: lue, transaction: base ? jjmmaaaa(base) : null, page: s.page, champFiche: champ, temoin: base })
}

export function bilansFiche(faits: FaitsRemplir, docs: DocumentLu[]): BilanCompromis[] {
  const lus = docs.filter((d) => d.lecture.etat === 'lu')
  const sortie: Array<BilanCompromis | null> = []
  const kwh = (x: number) => `${x} kWh/m²/an`
  const co2 = (x: number) => `${x} kg CO₂/m²/an`
  const ddt = ddtPlusRecent(lus)
  const lignesDdt: Array<LigneBilan | null> = []

  // le DPE le plus récent : consommation et émissions (± 1, comme L6), date d'établissement -- lu seul, ou dans le DDT
  // (ses champs dpe_*) : le plus récent des deux parle, à date égale le DPE seul
  const dpeSeul = plusRecent(lus, ['diag.dpe'], 'date_etablissement')
  const ddtDpe = ddt && ['dpe_conso_ep', 'dpe_emissions', 'dpe_date'].some((c) => texteLu(ddt.lecture.valeurs, c) != null || nombreLu(ddt.lecture.valeurs, c) != null || dateLue(ddt.lecture.valeurs, c) != null) ? ddt : null
  const dpeSource = plusRecente(dpeSeul ? { d: dpeSeul, date: dateLue(dpeSeul.lecture.valeurs, 'date_etablissement'), page: null, resultat: null } : null,
    ddtDpe ? { d: ddtDpe, date: dateLue(ddtDpe.lecture.valeurs, 'dpe_date'), page: null, resultat: null } : null)
  if (dpeSource) {
    const dpe = dpeSource.d
    const v = dpe.lecture.valeurs
    const k = dpe.lecture.typeCode === 'diag.dossier' ? { cons: 'dpe_conso_ep', ges: 'dpe_emissions', date: 'dpe_date' } : { cons: 'conso_ep', ges: 'emissions', date: 'date_etablissement' }
    const lignes = [
      nombre(dpe, 'F.dpe_cons', k.cons, 'Consommation d\'énergie', 'dpe_cons', nombreLu(v, k.cons), faits.dpeConso ?? null, TOLERANCES.dpe, kwh, 'L6'),
      nombre(dpe, 'F.dpe_ges', k.ges, 'Émissions de gaz à effet de serre', 'dpe_ges', nombreLu(v, k.ges), faits.dpeGes ?? null, TOLERANCES.dpe, co2, 'L6'),
      uneDate(dpe, 'F.dpe_date', k.date, 'Date du DPE', 'dpe_date', faits.dpeDate),
    ]
    if (dpe === ddt) lignesDdt.push(...lignes)
    else sortie.push(bilan('dpe', dpe, lignes.filter((l): l is LigneBilan => l !== null)))
  }
  // l'état des risques le plus récent : sa date d'établissement
  const erp = plusRecent(lus, ['diag.erp'], 'date_etablissement')
  if (erp) {
    sortie.push(bilan('erp', erp, [uneDate(erp, 'F.erp_date', 'date_etablissement', 'Date de l\'état des risques', 'diag_risques_nat_tech_date', faits.erpDate)].filter((l): l is LigneBilan => l !== null)))
  }
  // les six rapports : chacun sa fenêtre ; ce que le DDT en dit rejoint la fenêtre du DDT
  for (const g of DIAGS) {
    const rapport = plusRecent(lus, [g.type], g.cleDate)
    const deRapport: Source | null = rapport ? {
      d: rapport, date: dateLue(rapport.lecture.valeurs, g.cleDate), page: pageDe(rapport, g.cleDate),
      resultat: ((r) => (r ? RESULTATS[r] ?? r : null))(texteLu(rapport.lecture.valeurs, g.cleResultat)),
    } : null
    const rangDdt = ddt ? ddt.lecture.valeurs.find((x) => x.cle === 'diagnostics.diagnostic' && x.etat === 'lu' && x.valeur === g.nom)?.rang : undefined
    const deDdt: Source | null = ddt && rangDdt != null ? {
      d: ddt, date: auRang(ddt, 'diagnostics.date_rapport', rangDdt)?.valeur_date ?? null,
      page: auRang(ddt, 'diagnostics.diagnostic', rangDdt)?.page ?? null, resultat: auRang(ddt, 'diagnostics.conclusion', rangDdt)?.valeur ?? null,
    } : null
    // à date égale, le rapport seul parle (plusRecente garde le premier)
    const s = plusRecente(deRapport, deDdt)
    if (!s) continue
    const fiche = faits.diagnostics?.[g.champ]
    const lignes = [ligneFait(s, g.champ, g.libelle, fiche?.fait), ligneDateSource(s, `F.${g.champ}_date`, g.libelleDate, `${g.champ}_date`, fiche?.date)]
    if (s.d === ddt) lignesDdt.push(...lignes)
    else sortie.push(bilan(g.genre, s.d, lignes.filter((l): l is LigneBilan => l !== null)))
  }
  if (ddt) sortie.push(bilan('ddt', ddt, lignesDdt.filter((l): l is LigneBilan => l !== null)))
  // ⛔ la copropriété : seulement sur un bien MARQUÉ copropriété -- jamais rien qui ferait passer la case à OUI
  if (faits.copropriete === true) {
    const carnet = lus.find((x) => x.lecture.typeCode === 'copro.carnet' && texteLu(x.lecture.valeurs, 'sous_type') === 'fiche_synthetique')
    const lignesCarnet: Array<LigneBilan | null> = []
    if (carnet) {
      const total = nombreLu(carnet.lecture.valeurs, 'nb_lots_total')
      const principaux = nombreLu(carnet.lecture.valeurs, 'nb_lots_principaux')
      const l = nombre(carnet, 'F.copropriete_nb_lot', 'nb_lots_total', 'Nombre de lots de la copropriété', 'copropriete_nb_lot', total, faits.nbLots ?? null, { absolue: 0, relative: 0 }, (x) => `${x} lots`, 'L16')
      // comme L16 : la fiche qui porte le nombre de lots PRINCIPAUX est d'accord
      if (l && l.etat === 'trancher' && principaux != null && principaux === faits.nbLots) { l.etat = 'accord'; l.regle = null }
      if (l && principaux != null && l.etat !== 'accord') l.note = `dont ${principaux} lots principaux`
      lignesCarnet.push(l)
    }
    // lot B : le statut du syndicat et le plan de sauvegarde -- la fiche synthétique (qui peut dire « aucune » / « non ») et
    // le PV d'AG le plus récent qui NOMME une procédure (jamais une convocation) ; par case, le plus récent des deux parle
    const pv = lus.filter((x) => x.lecture.typeCode === 'copro.pv_ag' && texteLu(x.lecture.valeurs, 'type_piece') !== 'convocation'
      && ['mandataire_ad_hoc', 'administration_provisoire', 'plan_sauvegarde'].includes(texteLu(x.lecture.valeurs, 'procedure') ?? ''))
      .reduce<DocumentLu | null>((a, b) => (!a || (dateLue(b.lecture.valeurs, 'date_ag') ?? '') > (dateLue(a.lecture.valeurs, 'date_ag') ?? '') ? b : a), null)
    const procCarnet = carnet ? texteLu(carnet.lecture.valeurs, 'procedure') : null
    const planCarnet = carnet ? texteLu(carnet.lecture.valeurs, 'plan_sauvegarde') : null
    const procPv = pv ? texteLu(pv.lecture.valeurs, 'procedure') : null
    const dit = (d: DocumentLu | null, cleDate: string, cle: string, code: string | null | undefined): Dit | null => (d && code ? { d, date: dateLue(d.lecture.valeurs, cleDate), page: pageDe(d, cle), code } : null)
    const statut = leDernier(dit(carnet ?? null, 'date_etablissement', 'procedure', procCarnet ? STATUT_LU[procCarnet] : null),
      dit(pv, 'date_ag', 'procedure', procPv && procPv !== 'plan_sauvegarde' ? STATUT_LU[procPv] : null))
    const plan = leDernier(dit(carnet ?? null, 'date_etablissement', 'plan_sauvegarde', planCarnet === 'oui' ? 'OUI' : planCarnet === 'non' ? 'NON' : null),
      dit(pv, 'date_ag', 'procedure', procPv === 'plan_sauvegarde' ? 'OUI' : null))
    const lignesPv: LigneBilan[] = []
    for (const [s, l] of [
      [statut, statut && ligneCode(statut, 'F.copropriete_statut_syndicat', 'Procédure de la copropriété', 'copropriete_statut_syndicat', faits.statutSyndicat, (c) => STATUT_CLAIR[c] ?? c, statut.code !== 'NOTPROCESS')],
      [plan, plan && ligneCode(plan, 'F.copropriete_plan_sauvegarde', 'Plan de sauvegarde', 'copropriete_plan_sauvegarde', faits.planSauvegarde, (c) => (c === 'OUI' ? 'Oui' : c === 'NON' ? 'Non' : c), plan.code === 'OUI')],
    ] as Array<[Dit | null, LigneBilan | null]>) {
      if (!s || !l) continue
      if (s.d === pv) lignesPv.push(l)
      else lignesCarnet.push(l)
    }
    if (carnet) sortie.push(bilan('copro_lots', carnet, lignesCarnet.filter((l): l is LigneBilan => l !== null)))
    if (pv) sortie.push(bilan('copro_ag', pv, lignesPv))
    // la quote-part annuelle du lot : le budget annuel, sinon les charges courantes, sinon la provision annualisée.
    // ⚠ comparée à la case que l'on écrit (copropriete_quote_part), jamais à CHARGES (L16 compare à « quote-part ou CHARGES »)
    const appel = plusRecent(lus, ['copro.appel_fonds', 'copro.arrete_charges'], 'date_document')
    if (appel) {
      const v = appel.lecture.valeurs
      const cle = nombreLu(v, 'budget_annuel_lot') != null ? 'budget_annuel_lot' : nombreLu(v, 'charges_courantes_lot') != null ? 'charges_courantes_lot' : 'provision_budget'
      const annuel = nombreLu(v, 'budget_annuel_lot') ?? nombreLu(v, 'charges_courantes_lot') ?? annualiser(nombreLu(v, 'provision_budget'), texteLu(v, 'periode'))
      const l = nombre(appel, 'F.copropriete_quote_part', cle, 'Charges annuelles du lot', 'copropriete_quote_part', annuel, faits.quotePart ?? null, TOLERANCES.chargesAnnuelles, (x) => `${nombreClair(x)} € par an`, 'L16', false)
      sortie.push(bilan('copro_charges', appel, l ? [l] : []))
    }
  }
  // la Carrez mesurée : SENS UNIQUE (comme L15) -- à trancher seulement plus PETITE de plus de 5 % ; plus grande, d'accord
  const surface = plusRecent(lus, ['diag.surface'], 'date_mesurage')
  const carrez = surface ? nombreLu(surface.lecture.valeurs, 'surface_carrez') : null
  if (surface && carrez != null && carrez > 0) {
    const fiche = lireNombre(faits.carrez)
    const etat: EtatBilan = fiche == null || fiche <= 0 ? 'ajouter' : carrez < fiche * (1 - TOLERANCES.carrezSensUnique) ? 'trancher' : 'accord'
    const m2 = (x: number) => `${nombreClair(x)} m²`
    sortie.push(bilan('surface', surface, [ligne({
      cle: 'F.surface_carrez', libelle: 'Surface Carrez', etat, lu: m2(carrez), valeur: nombreTexte(carrez), transaction: fiche == null || fiche <= 0 ? null : m2(fiche),
      page: pageDe(surface, 'surface_carrez'), champFiche: 'SURF_CARREZ', temoin: fiche == null || fiche <= 0 ? null : String(fiche),
      note: etat === 'trancher' ? 'plus de 5 % en moins : l\'acquéreur peut demander une baisse du prix (loi Carrez)' : null, regle: etat === 'trancher' ? 'L15' : null,
    })]))
  }
  return sortie.filter((b): b is BilanCompromis => b !== null)
}

// La case de la fiche porte-t-elle encore ce que le bilan a vu ? (vide = vide ; nombres comparés en nombres, dates au jour)
export function caseInchangee(actuelle: string | null | undefined, temoin: string | null): boolean {
  const s = String(actuelle ?? '').trim()
  const vide = !s || /^0+([.,]0+)?$/.test(s) || /^(0000-00-00|1970-01-01)/.test(s)
  if (temoin == null) return vide
  if (vide) return false
  if (/^\d{4}-\d{2}-\d{2}/.test(temoin)) return s.slice(0, 10) === temoin.slice(0, 10)
  const a = Number(s.replace(',', '.'))
  const b = Number(temoin.replace(',', '.'))
  return Number.isFinite(a) && Number.isFinite(b) ? Math.abs(a - b) < 0.005 : s === temoin.trim()
}
