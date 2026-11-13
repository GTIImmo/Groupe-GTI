#!/usr/bin/env python3
"""GED-1 (06/11/2026) -- LA NOMENCLATURE DES DOCUMENTS, CHIFFREE PAR LE NOM.

LECTURE SEULE : lit app_console_document par l'API REST (cle de service), n'ecrit RIEN, ni en
base ni chez Hektor. Sert a rejouer les chiffres de la note
notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md (§6) et, plus tard, de point de depart a GED-3.

  python phase2/checks/ged1_mesure_nomenclature.py            -> le tableau par famille / type
  python phase2/checks/ged1_mesure_nomenclature.py --reste    -> + les formes non reconnues

Regles : la PREMIERE qui gagne (l'ordre compte : « offre de pret » n'est pas une offre,
« avenant au mandat » n'est pas un mandat). force « sur » = mot clair, « probable » = abreviation
ou mot ambigu (a faire confirmer par l'humain), « muet » = scan / photo / sans titre.
Les codes (mandat.vente, copro.pv_ag...) sont le contrat ; les libelles se changent.
"""
import collections, json, os, re, sys, unicodedata, urllib.parse, urllib.request
from pathlib import Path
import csv, re, sys, unicodedata, collections, random

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\.(pdf|jpe?g|png|docx?|xlsx?|odt|ods|pptx?|tiff?|txt|heic|gif|bmp|rtf|msg|eml|zip)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    # Hektor coupe les lettres accentuées : « foncie_re », « proprie_te », « e_tat », « pi_ce »
    s = re.sub(r"(?<=[a-z]) (?=(re|res|te|tes|e|es|ee|ees|reurs|reur|ne|nes|ment)\b)", "", s)
    s = re.sub(r"\be (?=[a-z]{2,})", "e", s)
    s = re.sub(r"\bpi ce", "piece", s)
    s = re.sub(r"\bre sume", "resume", s)
    return re.sub(r"\s+", " ", s).strip()

F = "sur"; P = "probable"
L = {
 "transaction.financement": ("transaction", "Financement (offre / accord de prêt, simulation)"),
 "transaction.offre": ("transaction", "Offre d'achat (et sa réponse)"),
 "transaction.renseignements": ("transaction", "Fiche de renseignements acquéreurs / vendeurs"),
 "transaction.avant_contrat": ("transaction", "Compromis / promesse de vente"),
 "transaction.sru": ("transaction", "Notification SRU / rétractation"),
 "transaction.sequestre": ("transaction", "Séquestre / dépôt de garantie"),
 "transaction.acte": ("transaction", "Acte de vente / attestation de vente"),
 "transaction.notaire": ("transaction", "Dossier / courrier du notaire"),
 "transaction.mobilier": ("transaction", "Liste du mobilier"),
 "transaction.annulation": ("transaction", "Annulation d'une vente / désistement"),
 "mandat.vente": ("mandat", "Mandat de vente"),
 "mandat.recherche": ("mandat", "Mandat de recherche"),
 "mandat.avenant": ("mandat", "Avenant au mandat (baisse de prix…)"),
 "mandat.honoraires": ("mandat", "Accord / baisse d'honoraires"),
 "mandat.fin": ("mandat", "Fin de mandat (résiliation, dénonciation, annulation)"),
 "visite.bon": ("visite", "Bon de visite"),
 "visite.compte_rendu": ("visite", "Compte rendu de visite"),
 "copro.etat_date": ("copropriete", "Pré-état daté / état daté"),
 "copro.pv_ag": ("copropriete", "PV / convocation d'assemblée générale"),
 "copro.reglement": ("copropriete", "Règlement de copropriété / état descriptif de division"),
 "copro.arrete_charges": ("copropriete", "Arrêté / décompte de charges (dépenses réelles)"),
 "copro.appel_fonds": ("copropriete", "Appels de fonds / provisions / budget prévisionnel"),
 "copro.carnet": ("copropriete", "Carnet d'entretien / fiche synthétique"),
 "copro.dtg": ("copropriete", "DTG / plan pluriannuel de travaux"),
 "copro.autre": ("copropriete", "Autre document de copropriété"),
 "diag.dossier": ("diagnostics", "Dossier de diagnostics (DDT) / autre diagnostic"),
 "diag.dpe": ("diagnostics", "DPE"),
 "diag.audit": ("diagnostics", "Audit énergétique"),
 "diag.amiante": ("diagnostics", "Amiante"),
 "diag.plomb": ("diagnostics", "Plomb (CREP)"),
 "diag.electricite": ("diagnostics", "Électricité"),
 "diag.gaz": ("diagnostics", "Gaz"),
 "diag.termites": ("diagnostics", "Termites / parasites / mérule"),
 "diag.erp": ("diagnostics", "État des risques (ERP / ERRIAL / Géorisques)"),
 "diag.surface": ("diagnostics", "Surface (Carrez / Boutin)"),
 "diag.assainissement": ("diagnostics", "Assainissement (SPANC, raccordement)"),
 "urba.cadastre": ("urbanisme", "Cadastre / parcelles"),
 "urba.certificat": ("urbanisme", "Certificat d'urbanisme / PLU / lotissement"),
 "urba.permis": ("urbanisme", "Permis / déclaration de travaux / conformité"),
 "urba.bornage": ("urbanisme", "Bornage / division / servitudes"),
 "urba.etude_sol": ("urbanisme", "Étude de sol / géotechnique (G1, G2)"),
 "justif.titre": ("justificatifs", "Titre de propriété / origine de propriété"),
 "justif.taxe": ("justificatifs", "Taxe foncière / impôts locaux"),
 "justif.identite": ("justificatifs", "Pièce d'identité"),
 "justif.etat_civil": ("justificatifs", "État civil / capacité (livret de famille, mariage, décès, tutelle)"),
 "justif.pouvoir": ("justificatifs", "Pouvoir / procuration"),
 "justif.societe": ("justificatifs", "Société venderesse (Kbis, statuts)"),
 "justif.rib": ("justificatifs", "RIB"),
 "estimation.avis": ("estimation", "Avis de valeur / dossier d'estimation"),
 "facture.honoraires": ("facturation", "Facture / note d'honoraires GTI"),
 "facture.autre": ("facturation", "Autre facture"),
 "facture.devis": ("facturation", "Devis / travaux"),
 "location.bail": ("location", "Bail / état des lieux / quittance / gérance"),
 "entreprise.comptes": ("entreprise", "Bilans / comptes (fonds de commerce)"),
 "bien.plans": ("bien", "Plans / vues du bien"),
 "bien.entretien": ("bien", "Entretien / énergie (chaudière, ramonage, contrats)"),
 "bien.descriptif": ("bien", "Descriptif / fiche commerciale du bien"),
 "bien.cles": ("bien", "Clés (photo / remise)"),
 "courrier": ("courrier", "Courrier / lettre / accusé de réception"),
 "interne.notes": ("interne", "Notes / suivi interne"),
}
# (code, motif, force) — la première qui gagne. force : « sur » = mot clair · « probable » = abréviation ou mot ambigu
R = [
 # ── d'abord les mots pièges : « offre de prêt » n'est pas une offre, « avenant au mandat » n'est pas un mandat
 ("transaction.financement", r"offres? de (pret|credit)|offre pret|\bodp\b|offpret", F),
 ("bien.entretien", r"facture.*(electri|\bgaz\b|\bedf\b|\beau\b|fioul|propane)", P),
 ("mandat.fin", r"resiliation|denonciation|annulation ?(du |de |d )?(mandat|mdt)|courrier d annulation|fin de mandat|lettre d annulation", F),
 ("mandat.avenant", r"avenant|\bavt\b|baisse (de )?prix", F),
 ("mandat.honoraires", r"accord (d )?honoraire|accord .*hono|accord franck|baisse d honoraires|honoraires? (mdt|mandat|avt|avenant)|delegation", F),
 ("transaction.offre", r"offre (d )?achat|offre (acceptee|signee|contre ?signee|refusee)|annulation (d )?offre|transmission de l offre|proposition d achat|\boffres?\b", F),
 ("transaction.renseignements", r"renseignements?|\brens (acq|vend)|fiche acquereurs?|questionnaire vendeur", P),
 ("visite.bon", r"bons? (de )?visite|\bbv\b|\bbdv\b|\bbvisite", F),
 ("transaction.financement", r"accord (de |du )?(principe|pret|bancaire|financement)|\badp\b|accord (ca|ce|cic|lcl|bp|cm|bnp|sg|cmb)\b"
  r"|attestation (de )?financement|plan de financement|etude de financement|demande de (pret|financement)|(depot|depose) (de |du )?(dossier )?(de )?pret"
  r"|depot (ce|ca|cic)\b|preuve de depot|refus (de )?(pret|banque|ca|ce)\b|contrat de (pret|cre ?a?dit)|cre ?a?dit immo|simul|courtier|\bpret\b|financement", F),
 ("mandat.recherche", r"mandat (de )?recherche|\bmdr\b", F),
 ("mandat.vente", r"mandat|\bmdt\b|\bmdv\b|\bmv\b|gti vente (simple|exclu|pref|semi)", F),
 # ── transaction
 ("transaction.acte", r"acte (de )?vente|copie vente|acte authentique|copie aae (vente|attestation de vente)|attestation (de |d )?(vente|acquisition)|attestation (avec|sans) prix|attestation notari|attestation apres vente", F),
 ("transaction.annulation", r"annulation (de la |de )?vente|desistement", F),
 ("transaction.avant_contrat", r"compromis|promesse|\bcpmis\b|avant contrat|copie aae", F),
 ("transaction.sru", r"\bsru\b|notification|retractation|\bar24\b", F),
 ("transaction.sequestre", r"sequestre|depot de garantie", F),
 ("transaction.notaire", r"notaire|notarial", P),
 ("transaction.mobilier", r"\bmobilier\b|imprimemobilier|liste (de |du |des )?(meubles|mobilier)", P),
 # ── copropriété
 ("copro.etat_date", r"pre ?etat ?date|etat date|questionnaire syndic", F),
 ("copro.pv_ag", r"\bpv\b.*\bag\b|\bpvag\b|proces verbal.*\b(ag|assemblee)|compte rendu a ?g\b|assemblee|\bago?\b|convocation|pouvoir ag", F),
 ("copro.reglement", r"reglement (de )?(la )?copro|rglt copro|regl copro|etat descriptif|\bedd\b|\brcp\b|modificatif", F),
 # charges : décision de Frédéric (06/11) — deux types, la dépense réelle d'un côté, l'appel de l'autre
 ("copro.arrete_charges", r"arrete (de |des )?(charges?|comptes?)|decompte|\bd[ae] ?compte (de |des )?charges|releve (de |des )?charges"
  r"|regul|r gularis|repartition (de |des )?charges|bilan (des )?charges|charges annuelles", F),
 ("copro.appel_fonds", r"appels? (de |des )?(fonds?|charges|provisions?)|apell|avis appel|provisions? (sur |de )?charges|budget previsionnel|fonds (de )?travaux", F),
 # « charges » seul : le contenu penche vers la dépense réelle (7 sur 11 lus le 06/11) -> proposé, à confirmer
 ("copro.arrete_charges", r"(?<!prise en )(?<!cahier des )\bcharges?\b|releve (de )?(compte )?copro", P),
 ("copro.carnet", r"carnet (d )?entretien|fiche synth", F),
 ("copro.dtg", r"\bdtg\b|diagnostic technique global|plan pluri|\bp?ppt\b", F),
 # ── terrain
 ("urba.bornage", r"bornage|geometre|division|arpentage|servitude", F),
 # ── diagnostics (un nom qui cite 2 diagnostics ou plus = dossier, voir classer())
 ("diag.erp", r"\berps?\b|etat (des |de )?risques|errial|\bedr\b|\besris\b|\bernm?t\b|\bial\b|\bicpe\b|georisque|risques|argile|radon", F),
 ("diag.audit", r"audit energ", F),
 ("diag.dpe", r"\bdpe\d*\b|performance energ|\bd7\b", F),
 ("diag.amiante", r"amiante|\bdta\b|\bd2\b", F),
 ("diag.plomb", r"plomb|\bcrep\b|\bd1\b", F),
 ("diag.electricite", r"electri|\belec\b|\bd5\b", F),
 ("diag.gaz", r"\bgaz\b|\bd4\b", F),
 ("diag.termites", r"termite|parasit|merule|\bd3\b", F),
 ("diag.surface", r"carrez|boutin|surface|superficie|mesurage", P),
 ("diag.assainissement", r"spanc|assainis|fosse|tout a l egout|raccordement", F),
 ("diag.dossier", r"\bddt\b|\bdti\b|diag|coef|resume details|a0 resume|attestation sur l honneur|\bd[0-9]\b|rapport de mission|certificat de competence", F),
 # ── urbanisme
 ("urba.cadastre", r"cadastr|parcelle|matrice|geoportail|\bsection\b|visualisation cartographique", F),
 ("urba.certificat", r"certificat (d )?urbanisme|\bcub?\d*\b|\bplu\b|zonage|zone au|urbanisme|cahier des charges|\bnru\b|lotissement", F),
 ("urba.permis", r"permis (de construire|d amenager|de demolir)|\bpc\b|declaration prealable|\bdp\b|conformite|\bdaact\b|achevement|ouverture de chantier|autorisation de travaux|\bpermis\d*\b", F),
 ("urba.etude_sol", r"\bg1\b|\bg2\b|geotechni|etude de sol\b", F),
 ("bien.plans", r"\bplans?\d*\b|croquis|vue aerienne", P),
 # ── justificatifs (pièces du propriétaire, demandées au mandat)
 ("justif.titre", r"titre (de )?propri|titre propri|\btp\d*\b|attestation (de |d )?propri|attest prop|acte (de |d )?propri|attestation immobiliere|releve de propriete"
  r"|donation|success|devolu|acte d achat|acte achat|attestation (d )?achat|achat terrain|notoriete", F),
 ("justif.titre", r"\btitres?\d*\b|propri|partage|\bacte\b|copie authentique", P),
 ("justif.taxe", r"foncier|\btf\d*\b|avis de taxe|\btaxes?\b|impots? locaux", F),
 ("justif.identite", r"\bcni\b|carte (d )?identit|carte id\b|\bci\b|\bpi\b|passeport|pieces? d identite|titre de sejour|identite|permis de conduire|\bid (recto|verso)\b", F),
 ("justif.etat_civil", r"livret (de )?famille|etat civil|habilitation familiale|acte de (naissance|deces|mariage)|contrat de mariage|divorce|\bpacs\b|jugement|ordonnance|tutelle|curatelle|deces", F),
 ("justif.pouvoir", r"pouvoirs?|procuration", F),
 ("justif.societe", r"kbis|statuts?\b|extrait k", F),
 ("diag.dossier", r"^(dossier )?sci .*dossier|^dossier sci", P),
 ("justif.societe", r"\bsci\b|infos? (societe|sas|sarl)", P),
 ("justif.rib", r"\brib\b|identite bancaire", F),
 # ── facturation, estimation
 ("facture.honoraires", r"^20\d\d \d\d? \d\d? facture|\bggti\d*|facture gti|facture.*estimation|\bgti\d{6,}|\bfct\b|\best\s?\d+\b|\bnotes? (d )?honoraires?\b|\bavoir\b|\bavr\b", F),
 ("estimation.avis", r"avis (de )?valeur|estimation|\bestim\b|evaluation|^rapport \d+ \d+|\bacm\b|etude de marche|comparatif", F),
 ("facture.autre", r"factures?|\bfac\d*\b", P),
 ("facture.devis", r"devis|travaux", P),
 # ── visite, location, entreprise
 ("visite.compte_rendu", r"compte rendu (de )?visite", F),
 ("location.bail", r"\bbail\b|\bbaux\b|location|compte rendu (de )?gestion|\bedl\b|etat des lieux|quittance|loyer|locataire|\bgarant\b|preavis|\bconge\b", F),
 ("entreprise.comptes", r"\bbilans?\b|liasse|compte de resultat|previsionnel|chiffre d affaires|fonds de commerce", P),
 # ── bien
 ("bien.entretien", r"entretien|chaudiere|ramonage|\bedf\b|echeancier|\bengie\b|energie|releve compteur", P),
 ("bien.descriptif", r"descripti|fiche (du )?bien|fiche commerciale|plaquette|annonce|presentation", P),
 ("bien.cles", r"\bcles?\b|\bclefs?\b", P),
 # ── fin des listes
 ("copro.pv_ag", r"\bpv\d*\b|proces verbal", P),
 ("copro.appel_fonds", r"appel de", P),
 ("copro.autre", r"copro|syndic|syndicat", P),
 ("transaction.annulation", r"\bannul|desistement", P),
 ("courrier", r"courrier|lettre|\blp\b|\bar\b|\blrar\b|accuse|recommande|\bmail\b|e ?mail|\bsms\b", P),
 ("interne.notes", r"\bnotes?\b|brouillon|en attente|suivi|\bliste\b|fiche interne|recap|covid", P),
]
RX = [(c, re.compile(m), force) for c, m, force in R]
assert all(c in L for c, m, force in R)
DIAGS = [(c, rx) for c, rx, force in RX if c in
         ("diag.dpe", "diag.amiante", "diag.plomb", "diag.electricite", "diag.gaz", "diag.termites", "diag.erp", "diag.surface")]
MUET_DEBUT = re.compile(r"^(sans titre|scanner|adobe scan|resized|s\d standard|page|img|image|photo|wp|dsc[fn]?|pxl|scan|numeris\w*|capture|screenshot"
                        r"|document|doc|fichier|cam|whatsapp|unnamed|thumbnail|file|untitled|sans nom|nouveau|new|p)\d*\b")
MUET_TOUT = re.compile(r"^[\d a-f]*$")   # que des chiffres / un hachage

def classer(nom, source=""):
    """Rend (code, famille, libellé, force). force : sur | probable | muet | reste."""
    n = norm(nom)
    if source == "hektor_console_modele" and n.startswith("document"):
        return ("muet.modele", "non_classe", "Modèle Hektor sans nom parlant", "muet")
    if re.match(r"^(sans titre|scanner|adobe scan|resized|s\d standard|page \d)", n):
        return ("muet", "non_classe", "Nom muet (scan, photo, sans titre)", "muet")
    if len({c for c, rx in DIAGS if rx.search(n)}) >= 2 and not re.search(r"avenant|mandat|offre|compromis", n):
        return ("diag.dossier",) + L["diag.dossier"] + (F,)
    for c, rx, force in RX:
        if rx.search(n):
            return (c,) + L[c] + (force,)
    if MUET_TOUT.match(n) or MUET_DEBUT.match(n):
        return ("muet", "non_classe", "Nom muet (scan, photo, sans titre)", "muet")
    return ("reste", "non_classe", "Nom parlant non reconnu", "reste")


# ── la mesure (lecture seule) ─────────────────────────────────────────────────
def _env():
    racine = Path(__file__).resolve().parents[2]
    for f in (racine / ".env", racine / "Console" / ".env", racine / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            for l in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                l = l.strip()
                if l and not l.startswith("#") and "=" in l:
                    k, v = l.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not cle:
        print("ARRET : SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY introuvable."); sys.exit(2)
    return url, cle


def lire_documents():
    url, cle = _env()
    dernier, lignes = "00000000-0000-0000-0000-000000000000", []
    while True:
        q = (f"{url}/rest/v1/app_console_document?select=id,hektor_annonce_id,document_name,source,storage_status"
             f"&id=gt.{dernier}&order=id.asc&limit=1000")
        req = urllib.request.Request(q, headers={"apikey": cle, "Authorization": f"Bearer {cle}"})
        with urllib.request.urlopen(req, timeout=120) as rep:
            lot = json.loads(rep.read().decode("utf-8"))
        if not lot:
            return lignes
        lignes += lot
        dernier = lot[-1]["id"]


if __name__ == "__main__":
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    docs = lire_documents()
    tot, sur, prob, coffre = (collections.Counter() for _ in range(4))
    fam, biens, formes, lib, famof = collections.Counter(), collections.defaultdict(set), collections.defaultdict(collections.Counter), {}, {}
    biens_coffre = set()
    for d in docs:
        c, f, l, force = classer(d["document_name"], d["source"])
        lib[c], famof[c] = l, f
        tot[c] += 1; fam[f] += 1
        sur[c] += force == "sur"; prob[c] += force == "probable"
        formes[c][" ".join(re.sub(r"\d+", "#", norm(d["document_name"])).split()[:4])] += 1
        if d["storage_status"] == "cloud_available":
            coffre[c] += 1; biens[c].add(d["hektor_annonce_id"]); biens_coffre.add(d["hektor_annonce_id"])
    n, nb = len(docs), max(len(biens_coffre), 1)
    print(f"{n} documents · {sum(coffre.values())} ouvrables dans l'app (coffre) sur {len(biens_coffre)} biens")
    for f in sorted(fam, key=lambda f: -fam[f]):
        print(f"\n## {f} -- {fam[f]} ({100 * fam[f] / n:.1f} %)")
        for c in sorted((c for c in tot if famof[c] == f), key=lambda c: -tot[c]):
            print(f"  {c:27} {tot[c]:7}  sur {sur[c]:6}  probable {prob[c]:5}  coffre {coffre[c]:5} "
                  f"({100 * len(biens[c]) / nb:4.1f} % des biens)  {lib[c]}  | {' | '.join(k for k, _ in formes[c].most_common(3))}")
    s, p = sum(sur.values()), sum(prob.values())
    print(f"\nsur {s} ({100 * s / n:.1f} %) · probable {p} ({100 * p / n:.1f} %) · muet {tot['muet'] + tot['muet.modele']} · non reconnu {tot['reste']}")
    if "--reste" in sys.argv:
        print("\nNON RECONNUS, formes les plus frequentes :")
        for k, v in formes["reste"].most_common(60):
            print(f"  {v:5}  {k}")
