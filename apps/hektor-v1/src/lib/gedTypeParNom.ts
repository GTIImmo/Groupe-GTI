// GED (12/11/2026, morceau 2) : le TYPE d'un document proposé d'après son NOM.
// ⛔ FICHIER FABRIQUÉ à partir des règles de phase2/checks/ged1_mesure_nomenclature.py (une seule source de
//   vérité) : ne pas éditer les règles ici, les corriger là-bas puis refabriquer. Même ordre (« la première qui
//   gagne » : « offre de prêt » n'est pas une offre, « avenant au mandat » n'est pas un mandat), même
//   normalisation, mêmes noms muets. Sert au dépôt (type proposé) et à « Reçu / Manque » (pièce « trouvée »).

export type ForceTypeParNom = 'sur' | 'probable' | 'muet' | 'reste'
export type TypeParNom = { code: string | null; force: ForceTypeParNom }

const REGLES: Array<[string, string, 'sur' | 'probable']> = [
  ["transaction.financement", "offres? de (pret|credit)|offre pret|\\bodp\\b|offpret", "sur"],
  ["bien.entretien", "facture.*(electri|\\bgaz\\b|\\bedf\\b|\\beau\\b|fioul|propane)", "probable"],
  ["mandat.fin", "resiliation|denonciation|annulation ?(du |de |d )?(mandat|mdt)|courrier d annulation|fin de mandat|lettre d annulation", "sur"],
  ["mandat.avenant", "avenant|\\bavt\\b|baisse (de )?prix", "sur"],
  ["mandat.honoraires", "accord (d )?honoraire|accord .*hono|accord franck|baisse d honoraires|honoraires? (mdt|mandat|avt|avenant)|delegation", "sur"],
  ["transaction.offre", "offre (d )?achat|offre (acceptee|signee|contre ?signee|refusee)|annulation (d )?offre|transmission de l offre|proposition d achat|\\boffres?\\b", "sur"],
  ["transaction.renseignements", "renseignements?|\\brens (acq|vend)|fiche acquereurs?|questionnaire vendeur", "probable"],
  ["visite.bon", "bons? (de )?visite|\\bbv\\b|\\bbdv\\b|\\bbvisite", "sur"],
  ["transaction.financement", "accord (de |du )?(principe|pret|bancaire|financement)|\\badp\\b|accord (ca|ce|cic|lcl|bp|cm|bnp|sg|cmb)\\b|attestation (de )?financement|plan de financement|etude de financement|demande de (pret|financement)|(depot|depose) (de |du )?(dossier )?(de )?pret|depot (ce|ca|cic)\\b|preuve de depot|refus (de )?(pret|banque|ca|ce)\\b|contrat de (pret|cre ?a?dit)|cre ?a?dit immo|simul|courtier|\\bpret\\b|financement", "sur"],
  ["mandat.recherche", "mandat (de )?recherche|\\bmdr\\b", "sur"],
  ["mandat.vente", "mandat|\\bmdt\\b|\\bmdv\\b|\\bmv\\b|gti vente (simple|exclu|pref|semi)", "sur"],
  ["transaction.acte", "acte (de )?vente|copie vente|acte authentique|copie aae (vente|attestation de vente)|attestation (de |d )?(vente|acquisition)|attestation (avec|sans) prix|attestation notari|attestation apres vente", "sur"],
  ["transaction.annulation", "annulation (de la |de )?vente|desistement", "sur"],
  ["transaction.avant_contrat", "compromis|promesse|\\bcpmis\\b|avant contrat|copie aae", "sur"],
  ["transaction.sru", "\\bsru\\b|notification|retractation|\\bar24\\b", "sur"],
  ["transaction.sequestre", "sequestre|depot de garantie", "sur"],
  ["transaction.notaire", "notaire|notarial", "probable"],
  ["transaction.mobilier", "\\bmobilier\\b|imprimemobilier|liste (de |du |des )?(meubles|mobilier)", "probable"],
  ["copro.etat_date", "pre ?etat ?date|etat date|questionnaire syndic", "sur"],
  ["copro.pv_ag", "\\bpv\\b.*\\bag\\b|\\bpvag\\b|proces verbal.*\\b(ag|assemblee)|compte rendu a ?g\\b|assemblee|\\bago?\\b|convocation|pouvoir ag", "sur"],
  ["copro.reglement", "reglement (de )?(la )?copro|rglt copro|regl copro|etat descriptif|\\bedd\\b|\\brcp\\b|modificatif", "sur"],
  ["copro.arrete_charges", "arrete (de |des )?(charges?|comptes?)|decompte|\\bd[ae] ?compte (de |des )?charges|releve (de |des )?charges|regul|r gularis|repartition (de |des )?charges|bilan (des )?charges|charges annuelles", "sur"],
  ["copro.appel_fonds", "appels? (de |des )?(fonds?|charges|provisions?)|apell|avis appel|provisions? (sur |de )?charges|budget previsionnel|fonds (de )?travaux", "sur"],
  ["copro.arrete_charges", "(?<!prise en )(?<!cahier des )\\bcharges?\\b|releve (de )?(compte )?copro", "probable"],
  ["copro.carnet", "carnet (d )?entretien|fiche synth", "sur"],
  ["copro.dtg", "\\bdtg\\b|diagnostic technique global|plan pluri|\\bp?ppt\\b", "sur"],
  ["urba.bornage", "bornage|geometre|division|arpentage|servitude", "sur"],
  ["diag.erp", "\\berps?\\b|etat (des |de )?risques|errial|\\bedr\\b|\\besris\\b|\\bernm?t\\b|\\bial\\b|\\bicpe\\b|georisque|risques|argile|radon", "sur"],
  ["diag.audit", "audit energ", "sur"],
  ["diag.dpe", "\\bdpe\\d*\\b|performance energ|\\bd7\\b", "sur"],
  ["diag.amiante", "amiante|\\bdta\\b|\\bd2\\b", "sur"],
  ["diag.plomb", "plomb|\\bcrep\\b|\\bd1\\b", "sur"],
  ["diag.electricite", "electri|\\belec\\b|\\bd5\\b", "sur"],
  ["diag.gaz", "\\bgaz\\b|\\bd4\\b", "sur"],
  ["diag.termites", "termite|parasit|merule|\\bd3\\b", "sur"],
  ["diag.surface", "carrez|boutin|surface|superficie|mesurage", "probable"],
  ["diag.assainissement", "spanc|assainis|fosse|tout a l egout|raccordement", "sur"],
  ["diag.dossier", "\\bddt\\b|\\bdti\\b|diag|coef|resume details|a0 resume|attestation sur l honneur|\\bd[0-9]\\b|rapport de mission|certificat de competence", "sur"],
  ["urba.cadastre", "cadastr|parcelle|matrice|geoportail|\\bsection\\b|visualisation cartographique", "sur"],
  ["urba.certificat", "certificat (d )?urbanisme|\\bcub?\\d*\\b|\\bplu\\b|zonage|zone au|urbanisme|cahier des charges|\\bnru\\b|lotissement", "sur"],
  ["urba.permis", "permis (de construire|d amenager|de demolir)|\\bpc\\b|declaration prealable|\\bdp\\b|conformite|\\bdaact\\b|achevement|ouverture de chantier|autorisation de travaux|\\bpermis\\d*\\b", "sur"],
  ["urba.etude_sol", "\\bg1\\b|\\bg2\\b|geotechni|etude de sol\\b", "sur"],
  ["bien.plans", "\\bplans?\\d*\\b|croquis|vue aerienne", "probable"],
  ["justif.titre", "titre (de )?propri|titre propri|\\btp\\d*\\b|attestation (de |d )?propri|attest prop|acte (de |d )?propri|attestation immobiliere|releve de propriete|donation|success|devolu|acte d achat|acte achat|attestation (d )?achat|achat terrain|notoriete", "sur"],
  ["justif.titre", "\\btitres?\\d*\\b|propri|partage|\\bacte\\b|copie authentique", "probable"],
  ["justif.taxe", "foncier|\\btf\\d*\\b|avis de taxe|\\btaxes?\\b|impots? locaux", "sur"],
  ["justif.identite", "\\bcni\\b|carte (d )?identit|carte id\\b|\\bci\\b|\\bpi\\b|passeport|pieces? d identite|titre de sejour|identite|permis de conduire|\\bid (recto|verso)\\b", "sur"],
  ["justif.etat_civil", "livret (de )?famille|etat civil|habilitation familiale|acte de (naissance|deces|mariage)|contrat de mariage|divorce|\\bpacs\\b|jugement|ordonnance|tutelle|curatelle|deces", "sur"],
  ["justif.pouvoir", "pouvoirs?|procuration", "sur"],
  ["justif.societe", "kbis|statuts?\\b|extrait k", "sur"],
  ["diag.dossier", "^(dossier )?sci .*dossier|^dossier sci", "probable"],
  ["justif.societe", "\\bsci\\b|infos? (societe|sas|sarl)", "probable"],
  ["justif.rib", "\\brib\\b|identite bancaire", "sur"],
  ["facture.honoraires", "^20\\d\\d \\d\\d? \\d\\d? facture|\\bggti\\d*|facture gti|facture.*estimation|\\bgti\\d{6,}|\\bfct\\b|\\best\\s?\\d+\\b|note d honoraires|\\bavoir\\b|\\bavr\\b", "sur"],
  ["estimation.avis", "avis (de )?valeur|estimation|\\bestim\\b|evaluation|^rapport \\d+ \\d+|\\bacm\\b|etude de marche|comparatif", "sur"],
  ["facture.autre", "factures?|\\bfac\\d*\\b", "probable"],
  ["facture.devis", "devis|travaux", "probable"],
  ["visite.compte_rendu", "compte rendu (de )?visite", "sur"],
  ["location.bail", "\\bbail\\b|\\bbaux\\b|location|compte rendu (de )?gestion|\\bedl\\b|etat des lieux|quittance|loyer|locataire|\\bgarant\\b|preavis|\\bconge\\b", "sur"],
  ["entreprise.comptes", "\\bbilans?\\b|liasse|compte de resultat|previsionnel|chiffre d affaires|fonds de commerce", "probable"],
  ["bien.entretien", "entretien|chaudiere|ramonage|\\bedf\\b|echeancier|\\bengie\\b|energie|releve compteur", "probable"],
  ["bien.descriptif", "descripti|fiche (du )?bien|fiche commerciale|plaquette|annonce|presentation", "probable"],
  ["bien.cles", "\\bcles?\\b|\\bclefs?\\b", "probable"],
  ["copro.pv_ag", "\\bpv\\d*\\b|proces verbal", "probable"],
  ["copro.appel_fonds", "appel de", "probable"],
  ["copro.autre", "copro|syndic|syndicat", "probable"],
  ["transaction.annulation", "\\bannul|desistement", "probable"],
  ["courrier", "courrier|lettre|\\blp\\b|\\bar\\b|\\blrar\\b|accuse|recommande|\\bmail\\b|e ?mail|\\bsms\\b", "probable"],
  ["interne.notes", "\\bnotes?\\b|brouillon|en attente|suivi|\\bliste\\b|fiche interne|recap|covid", "probable"],
]
const RX = REGLES.map(([code, motif, force]) => ({ code, rx: new RegExp(motif), force }))
const CODES_DIAG = new Set<string>(["diag.dpe", "diag.amiante", "diag.plomb", "diag.electricite", "diag.gaz", "diag.termites", "diag.erp", "diag.surface"])
const DIAGS = RX.filter((r) => CODES_DIAG.has(r.code))
const MUET_DEBUT = new RegExp("^(sans titre|scanner|adobe scan|resized|s\\d standard|page|img|image|photo|wp|dsc[fn]?|pxl|scan|numeris\\w*|capture|screenshot|document|doc|fichier|cam|whatsapp|unnamed|thumbnail|file|untitled|sans nom|nouveau|new|p)\\d*\\b")
const MUET_TOUT = new RegExp("^[\\d a-f]*$")

// Même normalisation que norm() en Python : sans accents, minuscules, l'extension retirée, les lettres
// accentuées que Hektor coupe (« foncie_re », « proprie_te ») recollées.
export function normaliserNomDocument(nom: string | null | undefined): string {
  let s = (nom ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^\x00-\x7f]/g, '').toLowerCase()
  s = s.replace(/\.(pdf|jpe?g|png|docx?|xlsx?|odt|ods|pptx?|tiff?|txt|heic|gif|bmp|rtf|msg|eml|zip)\b/g, ' ')
  s = s.replace(/[^a-z0-9]+/g, ' ')
  s = s.replace(/(?<=[a-z]) (?=(re|res|te|tes|e|es|ee|ees|reurs|reur|ne|nes|ment)\b)/g, '')
  s = s.replace(/\be (?=[a-z]{2,})/g, 'e')
  s = s.replace(/\bpi ce/g, 'piece')
  s = s.replace(/\bre sume/g, 'resume')
  return s.replace(/\s+/g, ' ').trim()
}

export function typeParNom(nom: string | null | undefined): TypeParNom {
  const n = normaliserNomDocument(nom)
  if (/^(sans titre|scanner|adobe scan|resized|s\d standard|page \d)/.test(n)) return { code: null, force: 'muet' }
  const diagsVus = new Set(DIAGS.filter((r) => r.rx.test(n)).map((r) => r.code))
  if (diagsVus.size >= 2 && !/avenant|mandat|offre|compromis/.test(n)) return { code: 'diag.dossier', force: 'sur' }
  for (const r of RX) {
    if (r.rx.test(n)) return { code: r.code, force: r.force }
  }
  if (MUET_TOUT.test(n) || MUET_DEBUT.test(n)) return { code: null, force: 'muet' }
  return { code: null, force: 'reste' }
}
