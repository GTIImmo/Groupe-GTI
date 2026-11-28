#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LA MISE A JOUR QUOTIDIENNE DEPUIS LE SHEET -- L'OUTIL (28/11/2026, son mot du 27/11 a la nuit).

    python -X utf8 -u phase2\checks\maj_quotidienne_du_classeur.py differences [--de IMAGE] [--a IMAGE]
    python -X utf8 -u phase2\checks\maj_quotidienne_du_classeur.py essai --passage N
    python -X utf8 -u phase2\checks\maj_quotidienne_du_classeur.py a_blanc --lot LOT
    python -X utf8 -u phase2\checks\maj_quotidienne_du_classeur.py ecrire --lot LOT --empreinte E      (apres SON « vas-y »)
    python -X utf8 -u phase2\checks\maj_quotidienne_du_classeur.py repetition --lot LOT
    python -X utf8 -u phase2\checks\maj_quotidienne_du_classeur.py routeur [--poser]

SON MOT (27/11, la nuit) : « tu construis l'outil de mise a jour cette nuit, et ce matin il ecrit TOUTES mes cases chez
nous, d'un seul coup. Il n'y a que les gestes chez Hektor qui restent dehors. » -- « ton essai a blanc de cet outil EST
le rattrapage de mon stock. Il sort la liste de tout ce qu'il ecrirait, c'est-a-dire exactement les cases qui me restent.
Alors arrete de fabriquer des patchs a la main. »

LES HUIT PIECES DU PLAN (§ 6, etapes 5 et 6 FUSIONNEES par son mot : « pas de phase d'observation, elle ecrit des le premier
matin, avec sauvegarde datee, journal, temoin chiffre et arret automatique ») -- et ce qui est NEUF ici :
  1. la photo du jour        : l'image du protocole (protocole_classeur.py image) -- existe ;
  2. ⭐ NEUF -- le journal des differences : deux photos, case par case (ID Unique x colonne) -> neuve / modifiee / disparue ;
     table app_classeur_difference (ecrite avec le lot, dans la meme transaction) ;
  3. le juge                 : le passage du protocole sur la photo du jour (protocole_classeur.py passage) -- existe ;
  4. le routeur              : UNE table, app_champ_destination (D9 : une seule table, pour les deux sens ; pas de sixieme
                               liste) -- sa graine est ROUTEUR ci-dessous, son contenu est le § 3 du plan ;
  5. la decision par case    : les regles DEJA JOUEES (lots A, B, C, etape 3, C8, charge du 24/11, D6 a six controles),
                               reprises telles quelles, colonne par colonne -- jamais une regle nouvelle en silence ;
  6. le temoin chiffre       : chaque colonne boucle (le Sheet porte = la somme de ses etats), sinon ARRET ;
  7. ⭐ NEUF -- la porte d'ecriture appelable sans ecran : le lot entier en UNE transaction -- gardes, empreinte d'avant
     exigee, sauvegardes datees, journal (app_classeur_realignement_journal, la valeur d'avant de chaque case), ecritures,
     controles ; son A_BLANC, son INVERSE, sa REPETITION ;
  8. ⭐ NEUF -- le rapport du matin : 1re rubrique, les dates que la nuit reecrit (Compromis, Vente Fixee, Offre Achat) --
     montrees, JAMAIS ecrites (son mot : « la nuit les reecrit comme Hektor les donne ») ; puis ce qui s'ecrit, colonne par
     colonne ; puis SA LISTE, une phrase par cas mis de cote.

⛔ CE QUI NE S'ECRIT JAMAIS : rien chez Hektor ; jamais l'etat d'une piece ; jamais une part supprimee (elle remonte a lui,
   sa regle 6) ; jamais une note ecrasee (une note neuve datee) ; jamais une des 9 notes saisies ; jamais une piece qu'il a
   fixee lui-meme (SES_DECISIONS du juge) sans qu'il le dise ; jamais la date du compromis ni celle de la vente fixee.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import coupe_preuve_interne as K  # noqa: E402
import rapatrier_repartition_classeur as RR  # noqa: E402

SORTIE = P.DOSSIER / "maj_quotidienne"          # le cache (les lots, leurs decisions, leurs SQL)
RAPPORTS = P.NOTICE                            # le rapport du matin, qu'il lit
NOTES_SAISIES = (1001384, 1001388, 1001389, 1001390, 1001391, 1001392, 1001393, 1001394, 1001395)
RANG = {"vente": 3, "compromis": 2, "offre": 1}
# D6 : les six conflits annonces le 27/11 au soir (carnet § 20.101) -- son mot du 28/11 : « le Sheet gagne sur les six,
#   y compris 650e65c8 a 2 800 ». Si l'outil en mesure d'autres, c'est un arret (une regle qui ne donne pas ce qu'on a dit).
CONFLITS_ANNONCES = {"78bb247a", "650e65c8", "b7aabaf3", "ad8681cd", "EAQJ9D0T", "KO6QPUV7"}

# ═══════════════════════════════════════ LE ROUTEUR (D9) : SA GRAINE ═════════════════════════════════════════════════
# Une ligne par colonne du Sheet. famille = la regle de decision ; destination = la place chez nous ; hektor = ce qui
# part chez Hektor (« jamais » partout : l'etape 9 est en dernier, et peut-etre jamais -- D11) ; ecrit = l'interrupteur.
ROUTEUR = [
    # colonne, famille, destination, regle, hektor, ecrit, raison
    ("COMMENTAIRES", "note_g", "app_affaire_note (origine classeur:G)", "note neuve datee ; jamais un ecrasement",
     "jamais", True, "plan § 3 ; lot A du 27/11"),
    ("En attente de", "note_f", "app_affaire_note (origine classeur:F)",
     "note neuve datee ; « V » seul, pictogramme seul, « V » + prenom : dehors (17/11)", "jamais", True,
     "plan § 3 ; lot B du 27/11"),
    ("Avis à envoyer (oui / non)", "avis", "app_classeur_avis.avis_a_envoyer", "vide -> Sheet ; differe -> Sheet gagne",
     "jamais", True, "lot A du 27/11"),
    ("Commentaire Avis", "avis", "app_classeur_avis.commentaire_avis", "vide -> Sheet ; differe -> Sheet gagne", "jamais",
     True, "lot A du 27/11"),
    ("Avis envoyé", "avis", "app_classeur_avis.avis_envoye", "vide -> Sheet ; differe -> Sheet gagne", "jamais", True,
     "lot A du 27/11"),
    ("Négociateur 1", "parts", "app_affaire_repartition (classeur_reconstitue)",
     "regle du 13/11 ; posee sur une chaine sans part ; une part qui differe lui remonte (regle 6)", "jamais", True,
     "lot C du 27/11"),
    ("Pourcentage 1", "parts", "app_affaire_repartition", "avec son nom", "jamais", True, "lot C du 27/11"),
    ("Négociateur 2", "parts", "app_affaire_repartition", "avec son nom", "jamais", True, "lot C du 27/11"),
    ("Pourcentage 2", "parts", "app_affaire_repartition", "avec son nom", "jamais", True, "lot C du 27/11"),
    ("Négociateur 3", "parts", "app_affaire_repartition", "avec son nom", "jamais", True, "lot C du 27/11"),
    ("Pourcentage 3", "parts", "app_affaire_repartition", "avec son nom", "jamais", True, "lot C du 27/11"),
    ("Annulée", "annulation", "app_affaire_ledger.date_annulation_app",
     "sur le compromis (16/11) ; sans compromis et une seule offre refusee : sur l'offre (27/11) ; ses 6 : la date, "
     "jamais l'etat ; dehors : les 109 anterieures (D3), avant la 1re proposition, une jumelle R27", "jamais", True,
     "plan § 3 et etape 3"),
    ("Commission TTC", "commission", "app_affaire_ledger.honoraires_entree_app",
     "D6 a six controles ; au stade de l'offre et les compromis nes du classeur (D2) : poser ; conflit sur une vente "
     "aux six controles : le Sheet gagne (son mot du 28/11, les six compris) ; le reste : signale", "jamais", True,
     "plan § 5 et D6"),
    ("Charge Commission", "charge", "app_mandat_champ_app (charge_commission, origine classeur) + le reflet",
     "vide -> Sheet ; differe -> Sheet gagne ; deux lignes sur un mandat qui disent deux choses : lui remonte", "jamais",
     True, "patron du 24/11"),
    ("Vente Réglée", "valeur_vente", "app_affaire_ledger.vente_reglee_app", "sur la vente ; la case telle quelle",
     "jamais", True, "C8 du 16/11"),
    ("Numéro de facture", "valeur_vente", "app_affaire_ledger.numero_facture_app",
     "sur la vente ; la case ENTIERE telle quelle, relances comprises (son mot du 28/11 : ne decoupe rien)", "jamais", True,
     "C8 du 16/11"),
    ("Compromis", "rapport_date", "(rien : la nuit la reecrit)", "montree au rapport, jamais ecrite (son mot du 28/11)",
     "jamais", False, "son mot du 28/11, point 4"),
    ("Vente Fixée", "rapport_date", "(rien : la nuit la reecrit)", "montree au rapport, jamais ecrite (son mot du 28/11)",
     "jamais", False, "son mot du 28/11, point 4"),
    ("Offre Achat", "rapport_date", "(rien : la colonne date de l'offre est relue chaque nuit)",
     "montree au rapport, jamais ecrite -- comparee a la 1re proposition (R29)", "jamais", False,
     "plan § 3 ; meme raison que son point 4"),
    ("Etat Actuel", "rapport_etat", "(rien : jamais l'etat d'une piece)", "montree au rapport quand elle contredit nos pieces",
     "jamais", False, "son interdit : on ne touche jamais l'etat"),
] + [(c, "dehors", "(rien)", "lue par le juge, ou laissee dehors par D8", "jamais", False, "D8 et regle du 25/11")
     for c in ("affair_uuid", "product_ref", "Mandat", "Nature", "Lien CRM", "Agence", "Notaire", "Signé", "Vente Prévue",
               "Signée", "Acquéreur", "Adresse Acquéreur", "Vendeur", "Adresse Vendeur", "Prix", "Ville", "Divers",
               "ID Unique")]


def q(s) -> str:
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"


def dire(s: str = "") -> None:
    print(s, flush=True)


def socle_module():
    spec = importlib.util.spec_from_file_location("socle", str(ICI / "socle_du_protocole_en_base_2026-11-27.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════ PIECE 2 : LE JOURNAL DES DIFFERENCES ════════════════════════════════════════
def lire_photo(nom: str) -> dict:
    d = P.image_choisie(nom)
    P.verifier_image(d)
    return {"nom": d.name, **json.loads((d / "sheet.json").read_text(encoding="utf-8"))}


def differences(a: dict, b: dict) -> list[dict]:
    """Deux photos, case par case : ID Unique x colonne. La 1re ligne d'un ID fait foi (les doublons sont un motif du juge)."""
    ea, eb = a["entete"], b["entete"]
    if ea != eb:
        raise SystemExit("⛔ l'entete du Sheet a change entre %s et %s : %s" % (a["nom"], b["nom"],
                                                                              sorted(set(ea) ^ set(eb))))
    out = []
    ra = {i: v[0] for i, v in a["par_id"].items()}
    rb = {i: v[0] for i, v in b["par_id"].items()}
    for i in sorted(set(ra) | set(rb)):
        x, y = ra.get(i), rb.get(i)
        if x is None:
            out.append({"id_unique": i, "num": y["num"], "colonne": "(la ligne)", "avant": "", "apres": "",
                        "nature": "ligne neuve"})
        elif y is None:
            out.append({"id_unique": i, "num": x["num"], "colonne": "(la ligne)", "avant": "", "apres": "",
                        "nature": "ligne disparue"})
        for k, c in enumerate(eb):
            va = (x["row"][k] if x and k < len(x["row"]) else "") or ""
            vb = (y["row"][k] if y and k < len(y["row"]) else "") or ""
            if va == vb:
                continue
            nat = "neuve" if not va.strip() else ("disparue" if not vb.strip() else "modifiee")
            if not va.strip() and not vb.strip():
                nat = "blancs"
            out.append({"id_unique": i, "num": (y or x)["num"], "colonne": c, "avant": va, "apres": vb, "nature": nat})
    return out


def resume_differences(diff: list[dict]) -> dict:
    par_col = Counter(d["colonne"] for d in diff if d["colonne"] != "(la ligne)")
    return {"cases": sum(par_col.values()), "hors_colonne_A": sum(n for c, n in par_col.items() if c != "affair_uuid"),
            "lignes_neuves": sum(1 for d in diff if d["nature"] == "ligne neuve"),
            "lignes_disparues": sum(1 for d in diff if d["nature"] == "ligne disparue"),
            "par_colonne": dict(par_col.most_common()), "par_nature": dict(Counter(d["nature"] for d in diff))}


def etape_differences(de: str | None, a: str | None) -> int:
    imgs = sorted(p.name for p in P.IMAGES.iterdir() if (p / "manifeste.json").exists())
    pa, pb = lire_photo(de or imgs[-2]), lire_photo(a or imgs[-1])
    diff = differences(pa, pb)
    r = resume_differences(diff)
    dire("LE JOURNAL DES DIFFERENCES : %s -> %s (fichiers en cache, aucune base)" % (pa["nom"], pb["nom"]))
    dire("   %d cases changees (%d hors colonne A) ; %d ligne(s) neuve(s), %d disparue(s)" % (
        r["cases"], r["hors_colonne_A"], r["lignes_neuves"], r["lignes_disparues"]))
    dire("   par nature : %s" % r["par_nature"])
    for c, n in r["par_colonne"].items():
        dire("      %-30s %5d" % (c, n))
    # LE TEMOIN DE LA COMPARAISON : rejouer les differences sur la photo d'avant doit rendre la photo d'apres, a l'octet
    eb = pb["entete"]
    rec = {i: list(v[0]["row"]) + [""] * (len(eb) - len(v[0]["row"])) for i, v in pa["par_id"].items()}
    for d in diff:
        if d["nature"] == "ligne neuve":
            rec[d["id_unique"]] = [""] * len(eb)
        elif d["nature"] == "ligne disparue":
            rec.pop(d["id_unique"], None)
    for d in diff:
        if d["colonne"] != "(la ligne)" and d["id_unique"] in rec:
            rec[d["id_unique"]][eb.index(d["colonne"])] = d["apres"]
    cible = {i: list(v[0]["row"]) + [""] * (len(eb) - len(v[0]["row"])) for i, v in pb["par_id"].items()}
    ok = rec == cible
    dire("   ⇒ TEMOIN : la photo d'avant + le journal = la photo d'apres : %s" % ("OUI, a l'octet" if ok else "⛔ NON"))
    SORTIE.mkdir(parents=True, exist_ok=True)
    f = SORTIE / ("differences_%s_%s.json" % (pa["nom"], pb["nom"]))
    f.write_text(json.dumps({"de": pa["nom"], "a": pb["nom"], "resume": r, "cases": diff}, ensure_ascii=False, indent=0),
                 encoding="utf-8")
    dire("   -> %s" % f)
    return 0 if ok else 1


# ═══════════════════════════════════════ LES DONNEES D'UN ESSAI ══════════════════════════════════════════════════════
class Donnees:
    def __init__(self, passage: int):
        so = sqlite3.connect("file:%s?mode=ro" % P.SOCLE.as_posix(), uri=True)
        row = so.execute("select image, boucle from passage where id=?", (passage,)).fetchone()
        if row is None:
            raise SystemExit("⛔ le passage %d n'est pas au socle" % passage)
        self.image, boucle = row
        if not boucle:
            raise SystemExit("⛔ le passage %d ne boucle pas -- l'outil s'arrete" % passage)
        self.V = {}
        self.R30 = defaultdict(set)
        for i, num, v, e, ps, m, pr in so.execute("select id_unique, num, verdict, etiquette, pieces, motif, preuves "
                                                  "from verdict where passage=?", (passage,)):
            self.V[i] = {"num": num, "verdict": v, "etiquette": e, "motif": m,
                         "pieces": [int(a) for a in json.loads(ps)] if ps else []}
            for x in (json.loads(pr) if pr else []):
                if isinstance(x, str) and x.startswith("REGLE R30") and "rattachee" in x:
                    self.R30[i] |= {int(y) for y in re.findall(r"\d+", x.split("rattachee", 1)[1])}
        so.close()
        self.passage = passage
        self.photo = lire_photo(self.image)
        self.COL = {c: k for k, c in enumerate(self.photo["entete"])}
        self.ROW = {i: e[0]["row"] for i, e in self.photo["par_id"].items()}
        self.T = sorted(i for i, x in self.V.items() if x["verdict"] == "TRANCHEE" and i in self.ROW)
        self.ATT = sorted(i for i, x in self.V.items() if x["verdict"] != "TRANCHEE")
        # LA BASE, EN DIRECT, LECTURE SEULE
        cn, cu = P.pooler()
        cu.execute("select app_affaire_id, kind, state, date::text, date_acte::text, montant, prix_net_vendeur, "
                   "honoraires_entree, honoraires_sortie, commission_agence, honoraires_entree_app, charge_commission_app, "
                   "date_annulation_app, vente_reglee_app, numero_facture_app, app_chaine_id, app_dossier_id, "
                   "app_dossier_numero, app_dossier_uuid::text, hektor_annonce_id, numero_mandat, present_in_hektor, "
                   "coalesce(transaction_origine, 'hektor'), propositions_json, hektor_affaire_id "
                   "from public.app_affaire_ledger")
        cols = ["id", "kind", "state", "date", "date_acte", "montant", "net", "he", "hs", "ca", "he_app", "charge_app",
                "da", "vr", "fa", "chaine", "dossier", "dossier_numero", "dossier_uuid", "annonce", "mandat", "pres",
                "orig", "pj", "ha"]
        self.L = {int(r[0]): dict(zip(cols, r)) for r in cu.fetchall()}
        cu.execute("select app_affaire_id, origine, texte from public.app_affaire_note")
        self.N = {int(a): (o or "", t or "") for a, o, t in cu.fetchall()}
        cu.execute("select id_unique, coalesce(avis_a_envoyer,''), coalesce(commentaire_avis,''), coalesce(avis_envoye,'') "
                   "from public.app_classeur_avis")
        self.AV = {i: {"avis_a_envoyer": a, "commentaire_avis": c, "avis_envoye": e} for i, a, c, e in cu.fetchall()}
        cu.execute("select app_chaine_id, cote, rang, hektor_user_id, pourcentage, origine from public.app_affaire_repartition")
        self.REP = defaultdict(list)
        for ch, co, rg, u, pc, o in cu.fetchall():
            self.REP[int(ch)].append({"cote": co, "rang": rg, "u": str(u), "pc": float(pc or 0), "origine": o or ""})
        cu.execute("select hektor_annonce_id, numero_mandat, valeur_app, origine, ecrit_par from public.app_mandat_champ_app "
                   "where champ = 'charge_commission'")
        self.CHARGE = {(str(a), str(n)): (v or "", o or "", e or "") for a, n, v, o, e in cu.fetchall()}
        cu.execute("select hektor_annonce_id::text, numero_mandat::text from public.app_mandat_register_current")
        self.REGISTRE = {(a, n) for a, n in cu.fetchall()}
        self.MANDATS_DU_BIEN = defaultdict(set)
        for a, n in self.REGISTRE:
            self.MANDATS_DU_BIEN[a].add(n)
        cu.execute("select hektor_annonce_id::text from public.app_dossier_current where hektor_annonce_id is not null")
        self.PARC = {r[0] for r in cu.fetchall()}
        cn.rollback()
        cn.close()
        # l'annuaire des negociateurs (la regle du 13/11), comme le lot C et l'audit des 18
        RR.RAP.ALIAS_NEGOCIATEUR = dict(RR.RAP.ALIAS_REPLI)
        loc = sqlite3.connect("file:%s?mode=ro" % P.BASE.as_posix(), uri=True)
        loc.row_factory = sqlite3.Row
        gens = defaultdict(list)
        for r in loc.execute("select hektor_user_id, nom, prenom, is_active from app_hektor_negotiator_agency_directory"):
            nom_ = " ".join(sorted(RR.mots_du_nom(r["nom"])))
            pre_ = " ".join(sorted(RR.mots_du_nom(r["prenom"])))
            if nom_:
                gens[(nom_, pre_)].append(dict(r))
        loc.close()
        self.PAR_NOM = defaultdict(list)
        for (nom_, pre_), fiches in gens.items():
            act = [f_ for f_ in fiches if f_.get("is_active") in (1, "1", True, "true", "True")]
            choix = sorted(act or fiches, key=lambda f_: int(str(f_["hektor_user_id"])))[0]
            self.PAR_NOM[nom_].append({"nom": nom_, "prenom": pre_, "hektor_user_id": str(choix["hektor_user_id"]),
                                       "fiches": len(fiches), "nom_vrai": (str(choix.get("prenom") or "") + " " +
                                                                           str(choix.get("nom") or "")).strip().upper()})

    def brut(self, i, c) -> str:
        r = self.ROW.get(i) or []
        k = self.COL[c]
        return (str(r[k]) if k < len(r) and r[k] is not None else "")

    def case(self, i, c) -> str:
        return self.brut(i, c).strip()

    def pieces(self, i, genre=None) -> list[int]:
        return sorted(a for a in self.V[i]["pieces"] if a in self.L and (genre is None or self.L[a]["kind"] == genre))


def blanc(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def sans_accent(s):
    s = re.sub(r"[^0-9a-zà-ÿ]", "", (s or "").lower())
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def sans_picto(s):
    return "".join(ch for ch in s if not (unicodedata.category(ch) in ("So", "Sk", "Cs", "Co") or 0xFE00 <= ord(ch) <= 0xFE0F
                                          or ord(ch) == 0x200D or 0x1F000 <= ord(ch)))


PRENOMS_APRES_V = {"Sarah", "Anne", "Tatiana", "Vivien", "Claire", "Dylan", "Frederique", "Joël", "Hugo", "Mélanie", "Clem",
                   "Simon", "Pauline", "Ramazan"}


def f_exclue(g):
    """SA DECISION DU 17/11 (C4), reprise du lot B : « V » seul, pictogramme seul, « V » + prenom nomme : dehors."""
    if not g:
        return ""
    t = blanc(sans_picto(g))
    if t == "":
        return "pictogramme seul"
    if t in ("V", "v"):
        return "« V » seul"
    m = re.fullmatch(r"[Vv] (\S+)", t)
    if m and m.group(1) in PRENOMS_APRES_V:
        return "« V » + prenom"
    return ""


def premiere_proposition(p):
    pj = p["pj"]
    j = pj if isinstance(pj, list) else (json.loads(pj) if pj else [])
    for e in j or []:
        if isinstance(e, dict) and e.get("type") == "proposition" and e.get("date"):
            return K.d_reg(str(e["date"]))
    return K.d_reg(str(p["date"] or ""))


def eur(s):
    try:
        return K.nombre(s)
    except Exception:  # noqa: BLE001
        return None


# ═══════════════════════════════════════ PIECE 5 : LA DECISION PAR CASE ══════════════════════════════════════════════
class Essai:
    """Chaque colonne : un compteur d'etats qui BOUCLE sur les cases du Sheet, des ecritures, des signaux, sa liste."""

    def __init__(self, D: Donnees, date_photo: str):
        self.D = D
        self.date_photo = date_photo                    # « 28/11/2026 » : la date des paragraphes dates
        self.etats = defaultdict(Counter)              # colonne -> etat -> n
        self.ecritures = []                           # dicts
        self.rapport_dates = []                       # la 1re rubrique du rapport
        self.signaux = []                             # rubrique, colonne, id, phrase
        self.liste = []                               # SA liste : (colonne, id, phrase) -- ce que je ne sais pas trancher
        self._neuves = set()                          # les pieces qui recoivent une note neuve dans ce lot
        self._dernier = None

    def etat(self, col, e, n=1):
        self.etats[col][e] += n
        self._dernier = (col, e)

    def ecrire(self, **kw):
        kw["_etat"] = self._dernier
        self.ecritures.append(kw)

    def arbitrer(self):
        """Deux lignes sur la MEME case du registre (meme piece, meme champ) : meme valeur -> ecrite une fois ; deux
        valeurs -> rien, et la case lui remonte. Jamais un choix en silence."""
        par = defaultdict(list)
        for w in self.ecritures:
            if w["famille"] == "ledger":
                par[(w["piece"], w["champ"])].append(w)
        retires = set()
        for _k, ws in par.items():
            if len(ws) == 1:
                continue
            vals = {blanc(w["valeur"]) for w in ws}
            for w in (ws[1:] if len(vals) == 1 else ws):
                retires.add(id(w))
                c, e = w["_etat"]
                self.etats[c][e] -= 1
                if len(vals) == 1:
                    self.etats[c]["1 meme case qu'une autre ligne, meme valeur (ecrite une fois)"] += 1
                else:
                    self.etats[c]["4 deux lignes sur la meme case disent deux choses"] += 1
                    self.mettre_de_cote(c, w["id_unique"], "la piece %d (%s) : les lignes %s disent %s" % (
                        w["piece"], w["champ"], "+".join(x["id_unique"] for x in ws), " / ".join(sorted(vals))))
        self.ecritures = [w for w in self.ecritures if id(w) not in retires]
        for c in list(self.etats):
            self.etats[c] = Counter({e: n for e, n in self.etats[c].items() if n})

    def mettre_de_cote(self, col, i, phrase, motif=None):
        self.liste.append((col, i, phrase, motif or phrase))

    def num(self, i):
        return self.D.V[i]["num"] if i in self.D.V else ""

    # ── les notes G et F (lots A et B) ──
    def notes(self):
        D = self.D
        for col, lettre in (("COMMENTAIRES", "G"), ("En attente de", "F")):
            origines = ("classeur:G", "classeur:F+G") if lettre == "G" else ("classeur:F", "classeur:F+G")
            prefixe = "[classeur %s, suivi en cours au %s] " % (lettre, self.date_photo)
            neuve = ("G : le commentaire -- " if lettre == "G" else prefixe)
            for i in D.ATT:
                if D.case(i, col):
                    self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
            for i in D.T:
                g = D.case(i, col)
                if not g:
                    continue
                if lettre == "F":
                    gx = f_exclue(g)
                    if gx:
                        self.etat(col, "1 dehors par sa decision du 17/11 : " + gx)
                        continue
                ps_ = D.pieces(i)
                if any(g in D.N[a][1] for a in ps_ if a in D.N):
                    self.etat(col, "1 deja chez nous (le texte est dans une note de la ligne)")
                    continue
                if lettre == "F" and any(blanc(sans_picto(g)) in blanc(D.N[a][1]) for a in ps_ if a in D.N):
                    self.etat(col, "1 deja chez nous sans ses pictogrammes (17/11 : on n'y touche pas)")
                    continue
                notes_l = [a for a in ps_ if a in D.N and D.N[a][0] in origines]
                cible = notes_l[0] if notes_l else (max(ps_, key=lambda a: (RANG.get(D.L[a]["kind"], 0), a)) if ps_ else None)
                if cible is None:
                    self.etat(col, "4 la ligne n'a aucune piece")
                    self.mettre_de_cote(col, i, "le texte n'a aucune piece ou aller (la ligne est tranchee sans piece)")
                elif cible in D.N and D.N[cible][0] == "saisie":
                    self.etat(col, "4 la piece porte une note SAISIE par un humain : rien n'est pose")
                    self.mettre_de_cote(col, i, "la piece %d porte une note saisie a la main : je n'y ajoute rien" % cible)
                elif cible in D.N:
                    self.etat(col, "2 ECRIT : paragraphe date ajoute a la note de la piece")
                    self.ecrire(famille="note", colonne=col, id_unique=i, num=self.num(i), piece=cible,
                                geste="paragraphe", valeur=prefixe + g, avant=D.N[cible][1], origine=D.N[cible][0])
                elif cible in self._neuves:
                    self.etat(col, "2 ECRIT : sous la note neuve que ce lot pose deja sur la piece")
                    self.ecrire(famille="note", colonne=col, id_unique=i, num=self.num(i), piece=cible,
                                geste="sous la note neuve", valeur=prefixe + g, avant=None, origine="classeur:" + lettre)
                else:
                    self._neuves.add(cible)
                    self.etat(col, "2 ECRIT : note neuve sur la piece")
                    self.ecrire(famille="note", colonne=col, id_unique=i, num=self.num(i), piece=cible, geste="note neuve",
                                valeur=neuve + g, avant=None, origine="classeur:" + lettre)

    # ── les avis (lot A) ──
    def avis(self):
        D = self.D
        champ = {"Avis à envoyer (oui / non)": "avis_a_envoyer", "Commentaire Avis": "commentaire_avis",
                 "Avis envoyé": "avis_envoye"}
        for col, ch in champ.items():
            for i in D.ATT:
                if D.case(i, col):
                    self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
            for i in D.T:
                val = D.case(i, col)
                if not val:
                    continue
                nous = D.AV.get(i, {}).get(ch, "")
                if nous == val:
                    self.etat(col, "1 deja chez nous")
                    continue
                self.etat(col, "2 ECRIT : %s" % ("ligne neuve" if i not in D.AV else ("le Sheet gagne (valeur d'avant au "
                                                                                     "journal)" if nous else "case vide")))
                self.ecrire(famille="avis", colonne=col, id_unique=i, num=self.num(i), champ=ch, valeur=val,
                            avant=nous if i in D.AV else None, ligne_neuve=i not in D.AV,
                            etiquette=D.V[i]["etiquette"])

    # ── la repartition (lot C, la regle du 13/11) ──
    def parts(self):
        D = self.D
        col = "REPARTITION (les 6 colonnes)"
        rangc = {"vente": 0, "compromis": 1, "offre": 2}
        chaines_vues = {}
        for i in D.ATT:
            if any(D.case(i, "Négociateur %d" % k) for k in (1, 2, 3)):
                self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
        for i in D.T:
            noms = [D.case(i, "Négociateur %d" % k) for k in (1, 2, 3)]
            if not any(noms):
                continue
            ps_ = sorted((a for a in D.pieces(i)), key=lambda a: (rangc.get(D.L[a]["kind"], 3), a))
            if not ps_:
                self.etat(col, "4 sans piece chez nous")
                self.mettre_de_cote(col, i, "la repartition n'a aucune piece ou aller")
                continue
            pcts = [K.nombre(D.case(i, "Pourcentage %d" % k)) for k in (1, 2, 3)]
            parts, pq = RR.nettoyer(noms, pcts)
            qui, refus = {}, ("nettoyage : " + pq) if pq else ""
            rows = next((D.REP[int(D.L[a]["chaine"])] for a in ps_ if D.L[a]["chaine"] is not None
                         and int(D.L[a]["chaine"]) in D.REP), [])
            if not refus:
                for nom, _p in parts:
                    qq, motif = RR.resoudre(nom, D.PAR_NOM, None, {r["u"] for r in rows})
                    if motif:
                        refus = "resolution : %s -> %s" % (nom, motif)
                        break
                    qui[nom] = qq
            cotes = []
            if not refus:
                cotes, pq = RR.decomposer(parts)
                if pq:
                    refus = "decomposition : " + pq
            if refus:
                self.etat(col, "5 dehors : la regle du 13/11 ne sait pas lire la ligne (plan § 6, etape 3 bis)")
                continue
            if rows:
                sig = {(c_, qui[n_]["hektor_user_id"], round(pc_, 2)) for c_, _r, n_, pc_ in cotes}
                if sig == {(r["cote"], r["u"], round(r["pc"], 2)) for r in rows}:
                    self.etat(col, "1 deja chez nous")
                else:
                    org = ",".join(sorted({r["origine"] for r in rows}))
                    self.etat(col, "3 une part differe : elle lui remonte (sa regle 6, on ne supprime pas une part)")
                    st = " | ".join("%s %s" % (n, D.case(i, "Pourcentage %d" % k)) for k, n in zip((1, 2, 3), noms) if n)
                    nous = " + ".join("%s %s %g%%" % (r["cote"], r["u"], r["pc"]) for r in
                                      sorted(rows, key=lambda r: (r["cote"], r["rang"])))
                    self.mettre_de_cote(col, i, "le Sheet dit « %s », chez nous « %s » (origine %s) : la part qui differe "
                                                "ne se supprime pas, a toi de dire" % (st, nous, org))
                continue
            cible = ps_[0]
            chaine = D.L[cible]["chaine"]
            if chaine is None:
                self.etat(col, "4 la piece la plus avancee n'a pas de chaine")
                self.mettre_de_cote(col, i, "la piece %d n'a pas de chaine : la part n'a pas de place" % cible)
                continue
            if int(chaine) in chaines_vues:
                self.etat(col, "4 deux lignes sur la meme chaine : rien n'est pose")
                self.mettre_de_cote(col, i, "deux lignes (%s et %s) sur la chaine %s : je ne choisis pas" % (
                    chaines_vues[int(chaine)], i, chaine))
                continue
            chaines_vues[int(chaine)] = i
            self.etat(col, "2 ECRIT : posee sur la chaine de sa piece la plus avancee")
            for c_, r_, n_, pc_ in cotes:
                self.ecrire(famille="part", colonne=col, id_unique=i, num=self.num(i), piece=cible, chaine=int(chaine),
                            dossier=D.L[cible]["dossier"], cote=c_, rang=int(r_), u=qui[n_]["hektor_user_id"],
                            nom=qui[n_].get("nom_vrai") or n_.upper(), pc=round(float(pc_), 3))

    # ── la date d'annulation (16/11 + etape 3) ──
    def annulation(self):
        D = self.D
        col = "Annulée"
        cle = {j: (D.case(j, "Mandat"), frozenset(P.noms_texte(D.case(j, "Acquéreur"))),
                   P.nombre_case(D.case(j, "Commission TTC"))) for j in D.ROW}
        par_cle = defaultdict(list)
        for j, k in cle.items():
            if k[0] and k[1] and k[2] is not None:
                par_cle[k].append(j)
        for i in D.ATT:
            if D.case(i, col):
                self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
        for i in D.T:
            b = D.case(i, col)
            if not b:
                continue
            comp, offres = D.pieces(i, "compromis"), D.pieces(i, "offre")
            if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", b):
                self.etat(col, "4 date illisible au Sheet")
                self.mettre_de_cote(col, i, "la case « %s » n'est pas une date" % b)
                continue
            val = "%s-%s-%s" % (b[6:10], b[3:5], b[0:2])
            d = K.d_reg(val)
            tous = comp + offres
            if any(K.d_reg(str(D.L[a]["da"] or "")) == d for a in tous if D.L[a]["da"]):
                self.etat(col, "1 deja chez nous")
                continue
            pleines = {a: D.L[a]["da"] for a in tous if (D.L[a]["da"] or "").strip()}
            dcs = [K.d_reg(str(D.L[a]["date"] or "")) for a in comp]
            if comp and all(x and d < x for x in dcs):
                self.etat(col, "1 dehors (D3) : annulation anterieure a son compromis -- le rendez-vous de signature")
                continue
            if comp:
                cible_s = [a for a in comp if D.L[a]["state"] == "cancelled"] or [a for a in comp if D.L[a]["state"] == "active"]
                if len(comp) > 1 and len(cible_s) != 1:
                    self.etat(col, "4 plusieurs compromis : on ne choisit pas")
                    self.mettre_de_cote(col, i, "%d compromis sur la ligne (%s) : je ne choisis pas" % (
                        len(comp), "+".join("%d %s" % (a, D.L[a]["state"]) for a in comp)))
                    continue
                a = cible_s[0] if cible_s else comp[0]
                if pleines.get(a):
                    self.etat(col, "4 la piece porte deja une autre date")
                    self.mettre_de_cote(col, i, "le compromis %d porte deja %s, le Sheet dit %s" % (a, pleines[a], val))
                    continue
                borne = K.d_reg(str(D.L[a]["date"] or ""))
                if borne and d < borne:
                    self.etat(col, "1 dehors (D3) : annulation anterieure a son compromis -- le rendez-vous de signature")
                    continue
                st = D.L[a]["state"]
                pourquoi = ("sa regle du 16/11 : la date va sur le compromis" if st == "cancelled" else
                            "ses 6 : le Sheet dit annule, la piece est vivante -> la date, JAMAIS l'etat")
            else:
                ref = [a for a in offres if D.L[a]["state"] == "refused"]
                acc = [a for a in offres if D.L[a]["state"] == "accepted"]
                if not offres:
                    self.etat(col, "4 ni compromis ni offre")
                    self.mettre_de_cote(col, i, "annulee au Sheet, sans compromis ni offre chez nous : la date n'a pas de place")
                    continue
                if len(ref) == 1 and not acc:
                    a, pourquoi = ref[0], "sa regle du 27/11 : aucun compromis, une seule offre refusee -> sur l'offre"
                elif len(acc) == 1 and not ref:
                    a, pourquoi = acc[0], "ses 6 : le Sheet dit annule, la piece est vivante -> la date, JAMAIS l'etat"
                else:
                    self.etat(col, "4 plusieurs offres : on ne choisit pas")
                    self.mettre_de_cote(col, i, "%d offres (%s) et aucun compromis : je ne choisis pas" % (
                        len(offres), "+".join("%d %s" % (a_, D.L[a_]["state"]) for a_ in offres)))
                    continue
                if pleines.get(a):
                    self.etat(col, "4 la piece porte deja une autre date")
                    self.mettre_de_cote(col, i, "l'offre %d porte deja %s, le Sheet dit %s" % (a, pleines[a], val))
                    continue
                borne = premiere_proposition(D.L[a])
                if borne and d < borne:
                    self.etat(col, "4 annulation AVANT la 1re proposition de l'offre")
                    self.mettre_de_cote(col, i, "annulee le %s, avant la 1re proposition de l'offre %d (%s)%s" % (
                        b, a, borne.strftime("%d/%m/%Y"), " -- un 1er du mois : le Sheet note sans doute le mois"
                        if b.startswith("01/") else ""), motif="la date d'annulation tombe AVANT la 1re proposition de "
                                                               "l'offre (le garde-fou du 16/11, sur l'offre) : non posee")
                    continue
            if [j for j in par_cle.get(cle[i], []) if j != i]:
                self.etat(col, "4 une jumelle R27 (meme Mandat, Acquereur, Commission)")
                self.mettre_de_cote(col, i, "une jumelle R27 porte les memes Mandat, Acquereur et Commission : vide par decision")
                continue
            self.etat(col, "2 ECRIT : %s" % pourquoi.split(" :")[0])
            self.ecrire(famille="ledger", colonne=col, id_unique=i, num=self.num(i), piece=a, champ="date_annulation_app",
                        valeur=val, avant=D.L[a]["da"], pourquoi=pourquoi + " ; Sheet « %s »" % b)

    # ── la Commission TTC (D6, six controles) ──
    def commission(self):
        D = self.D
        col = "Commission TTC"
        rapports = sorted({round(k / 20, 4) for k in range(1, 20)} | {round(1 / 3, 4), round(2 / 3, 4)})
        tva = (1.2, round(1 / 1.2, 4), 1.196, 1.1)
        for i in D.ATT:
            if D.case(i, col):
                self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
        for i in D.T:
            s = D.case(i, col)
            if not s:
                continue
            sh = eur(s)
            if sh is None:
                self.etat(col, "4 je ne sais pas lire la case")
                self.mettre_de_cote(col, i, "la Commission « %s » ne se lit pas comme un montant" % s)
                continue
            px = eur(D.case(i, "Prix"))
            ventes = [a for a in D.pieces(i, "vente") if D.L[a]["pres"]]
            if ventes:
                if len(ventes) > 1:
                    self.etat(col, "4 deux ventes ou plus sur la ligne")
                    self.mettre_de_cote(col, i, "%d ventes vivantes sur la ligne : je ne choisis pas" % len(ventes))
                    continue
                a = ventes[0]
                v = D.L[a]
                he, hs = eur(v["he"]) or 0, eur(v["hs"]) or 0
                ttc = he + hs
                deja = eur(v["he_app"])
                if abs(ttc - sh) < 1 or (deja is not None and abs(deja - sh) < 1):
                    self.etat(col, "1 deja chez nous (la vente, champ TTC)")
                    continue
                prix_v = eur(v["montant"])
                if px is None or prix_v is None or abs(px - prix_v) >= 1:
                    self.etat(col, "3 signal ③ : un ecart de PRIX, pas de commission")
                    self.signaux.append(("commission", col, i, "ecart de prix : Sheet %s, vente %s (%d) ; commission Sheet %g, "
                                                               "Hektor %g" % (D.case(i, "Prix") or "vide", prix_v, a, sh, ttc)))
                    continue
                if ttc and hs and abs(sh - he) < 1:
                    self.etat(col, "1 controle ⑤ : le Sheet porte l'entree seule, la sortie n'est pas nulle -- on ne touche a rien")
                    continue
                r = sh / ttc if ttc else None
                if r is not None and any(abs(r - x) < 0.0005 for x in rapports):
                    self.etat(col, "3 signal ④ : une part ronde d'un partage entre agences")
                    self.signaux.append(("commission", col, i, "le Sheet porte %g, soit %.0f %% des %g de Hektor : un partage, "
                                                               "on ne corrige pas" % (sh, r * 100, ttc)))
                    continue
                if r is not None and any(abs(r - x) < 0.0005 for x in tva):
                    self.etat(col, "3 signal ⑥ : un coefficient de TVA")
                    self.signaux.append(("commission", col, i, "le Sheet porte %g contre %g chez Hektor : rapport %.4f, un "
                                                               "coefficient de TVA" % (sh, ttc, r)))
                    continue
                self.etat(col, "2 ECRIT : conflit aux six controles, le Sheet gagne (sur la vente)")
                self.ecrire(famille="ledger", colonne=col, id_unique=i, num=self.num(i), piece=a, champ="honoraires_entree_app",
                            valeur=s, avant=v["he_app"], pourquoi="D6, conflit aux six controles : le Sheet gagne (son mot "
                                                                    "du 28/11) ; Hektor %g" % ttc)
                continue
            if D.pieces(i, "vente"):
                self.etat(col, "4 la vente de la ligne n'est plus chez Hektor")
                self.mettre_de_cote(col, i, "la vente %s n'est plus chez Hektor : je ne pose la commission nulle part" %
                                    "+".join(map(str, D.pieces(i, "vente"))))
                continue
            comps = D.pieces(i, "compromis")
            comps_h = [a for a in comps if D.L[a]["orig"] != "classeur"]
            comps_c = [a for a in comps if D.L[a]["orig"] == "classeur"]
            if comps_h:
                hons = [(eur(D.L[a]["he"]) or 0) + (eur(D.L[a]["hs"]) or 0) for a in comps_h]
                if any(abs(h - sh) < 1 for h in hons) or any(eur(D.L[a]["he_app"]) is not None
                                                             and abs(eur(D.L[a]["he_app"]) - sh) < 1 for a in comps_h):
                    self.etat(col, "1 deja chez nous (le compromis)")
                else:
                    self.etat(col, "3 controle ② : sans vente, le compromis est provisoire -- en attente")
                continue
            if comps_c:
                if len(comps_c) > 1:
                    self.etat(col, "4 plusieurs compromis du classeur")
                    self.mettre_de_cote(col, i, "%d compromis nes du classeur : je ne choisis pas" % len(comps_c))
                    continue
                a = comps_c[0]
                quoi = "D2 : un compromis ne du classeur (Hektor ne le connait pas)"
            else:
                offres = D.pieces(i, "offre")
                if not offres:
                    self.etat(col, "4 aucune piece ou la poser")
                    self.mettre_de_cote(col, i, "Commission %s sans offre, compromis ni vente chez nous" % s)
                    continue
                ordre = {"accepted": 0, "proposed": 1, "pending": 1, "refused": 2}
                offres = sorted(offres, key=lambda a: (ordre.get(D.L[a]["state"], 3), -a))
                a = offres[0]
                quoi = "au stade de l'offre (sa decision du 27/11) : l'offre %s" % D.L[a]["state"]
            deja = eur(D.L[a]["he_app"])
            if deja is not None and abs(deja - sh) < 1:
                self.etat(col, "1 deja chez nous (honoraires de l'app)")
                continue
            # ⛔ SON MOT DU 27/11 : « tout ce qui parait aberrant se signale, sans jamais s'ecrire en silence » -- le garde-fou
            #   des aberrations de D6 : un montant nul, ou hors de 0,5 % a 20 % du prix quand le Prix est un vrai prix (la
            #   colonne porte un departement, 42 / 43 / 63, sur 990 lignes : sous 10 000, le rapport ne se calcule pas)
            if sh == 0 or (px is not None and px >= 10000 and not (0.005 * px <= sh <= 0.2 * px)):
                self.etat(col, "3 signal : un montant aberrant (nul, ou hors de 0,5 % a 20 % du prix)")
                self.signaux.append(("commission", col, i, "Commission %s pour un Prix de %s : aberrante, non posee (%s)" % (
                    s, D.case(i, "Prix") or "vide", quoi)))
                continue
            self.etat(col, "2 ECRIT : %s" % quoi.split(" :")[0].split(" (")[0])
            self.ecrire(famille="ledger", colonne=col, id_unique=i, num=self.num(i), piece=a, champ="honoraires_entree_app",
                        valeur=s, avant=D.L[a]["he_app"], pourquoi=quoi)

    # ── la charge (patron du 24/11 : le carnet du mandat, puis le reflet) ──
    def charge(self):
        D = self.D
        col = "Charge Commission"
        veut = defaultdict(list)
        for i in D.ATT:
            if D.case(i, col):
                self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
        for i in D.T:
            s = D.case(i, col)
            if not s:
                continue
            ks = sorted({(str(D.L[a]["annonce"]), str(D.L[a]["mandat"])) for a in D.pieces(i)
                         if D.L[a]["mandat"] not in (None, "")})
            if not ks:
                biens = {str(D.L[a]["annonce"]) for a in D.pieces(i) if D.L[a]["annonce"]}
                regs = {(b_, n_) for b_ in biens for n_ in D.MANDATS_DU_BIEN.get(b_, ())}
                self.etat(col, "4 sans mandat sur ses pieces")
                self.mettre_de_cote(col, i, "la charge « %s » : ses pieces n'ont pas de numero de mandat%s" % (
                    s, (" ; le registre ne connait qu'un mandat pour le bien (%s/%s)" % sorted(regs)[0]) if len(regs) == 1
                    else (" ; le registre en connait %d pour le bien" % len(regs) if regs else " ; le bien n'est pas au "
                                                                                                "registre des mandats")),
                    motif="la charge : ses pieces ne portent pas de numero de mandat")
                continue
            if len(ks) > 1:
                self.etat(col, "4 plusieurs mandats sur la ligne")
                self.mettre_de_cote(col, i, "%d mandats sur la ligne (%s) : je ne choisis pas" % (len(ks), ks))
                continue
            veut[ks[0]].append((i, s))
        sa = sans_accent
        for k, ls in sorted(veut.items()):
            valeurs = {sa(s) for _i, s in ls}
            reglees = [(i_, s_) for i_, s_ in ls if D.case(i_, "Etat Actuel") == "Vente réglée"]
            if len(valeurs) > 1 and len({sa(s_) for _i, s_ in reglees}) == 1:
                for i_, s_ in ls:
                    if (i_, s_) not in reglees and sa(s_) != sa(reglees[0][1]):
                        self.etat(col, "1 dehors : sur le meme mandat, la vente reglee fait foi (sa decision du 24/11)")
                ls = [(i_, s_) for i_, s_ in ls if sa(s_) == sa(reglees[0][1])]
                valeurs = {sa(reglees[0][1])}
            if len(valeurs) > 1:
                for i, s in ls:
                    self.etat(col, "4 deux lignes sur le meme mandat disent deux choses")
                    self.mettre_de_cote(col, i, "le mandat %s/%s : les lignes %s disent %s" % (
                        k[0], k[1], "+".join(x[0] for x in ls), " / ".join(sorted({x[1] for x in ls}))),
                        motif="la charge : deux lignes du meme mandat disent deux choses")
                continue
            i, s = ls[0]
            nous = D.CHARGE.get(k)
            if nous and nous[1] == "mandat_app" and sa(nous[0]) != sa(s):
                for i_, _s in ls:
                    self.etat(col, "4 la charge a ete saisie dans l'app : elle ne bouge pas")
                    self.mettre_de_cote(col, i_, "le mandat %s/%s porte « %s » saisi dans l'app, le Sheet dit « %s » : une "
                                                 "saisie ne bouge pas sans ton mot" % (k[0], k[1], nous[0], s))
                continue
            if nous and sa(nous[0]) == sa(s):
                for _ in ls:
                    self.etat(col, "1 deja chez nous")
                continue
            if k not in D.REGISTRE:
                for i_, _s in ls:
                    self.etat(col, "4 le mandat n'est pas au registre (le reflet n'a pas de ligne)")
                    self.mettre_de_cote(col, i_, "le mandat %s/%s n'est pas au registre des mandats" % k)
                continue
            for i_, _s in ls[1:]:
                self.etat(col, "1 meme mandat qu'une autre ligne, meme valeur (ecrite une fois)")
            self.etat(col, "2 ECRIT : %s" % ("le Sheet gagne (valeur d'avant au journal)" if nous else "case vide"))
            self.ecrire(famille="charge", colonne=col, id_unique=i, num=self.num(i), annonce=k[0], mandat=k[1], valeur=s,
                        avant=(nous[0] if nous else None), avant_origine=(nous[1] if nous else None),
                        avant_par=(nous[2] if nous else None))

    # ── Vente Reglee et Numero de facture (C8 du 16/11) : sur la vente, la case telle quelle ──
    def valeurs_vente(self):
        D = self.D
        for col, ch in (("Vente Réglée", "vr"), ("Numéro de facture", "fa")):
            champ = "vente_reglee_app" if ch == "vr" else "numero_facture_app"
            for i in D.ATT:
                if D.case(i, col):
                    self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
            for i in D.T:
                s = D.case(i, col)
                if not s:
                    continue
                brut = D.brut(i, col)
                ventes = D.pieces(i, "vente")
                if not ventes:
                    autres = "+".join("%s %s%s" % (D.L[a]["kind"], D.L[a]["state"], "" if D.L[a]["orig"] != "classeur"
                                                    else " (ne du classeur)") for a in D.pieces(i)) or "aucune piece"
                    vivante = any(D.L[a]["state"] in ("active", "accepted") for a in D.pieces(i)
                                  if D.L[a]["kind"] in ("compromis", "offre"))
                    if vivante:
                        self.etat(col, "3 attend sa vente : l'affaire est vivante, la boucle posera la case le jour ou la "
                                       "vente descendra de Hektor")
                        continue
                    self.etat(col, "4 sans vente chez nous, et l'affaire n'est pas vivante")
                    self.mettre_de_cote(col, i, "« %s » : %s" % (s[:70], autres),
                                        motif="%s sans vente chez nous, sur une affaire morte (sa place est la vente)" % col)
                    continue
                vals = {a: str(D.L[a][ch] or "") for a in ventes}
                if any(blanc(v) == blanc(s) or (ch == "vr" and K.d_sheet(s) and K.d_reg(v) == K.d_sheet(s))
                       for v in vals.values()):
                    self.etat(col, "1 deja chez nous")
                    continue
                if len(ventes) > 1:
                    self.etat(col, "4 plusieurs ventes : on ne choisit pas")
                    self.mettre_de_cote(col, i, "%d ventes sur la ligne : je ne choisis pas" % len(ventes))
                    continue
                a = ventes[0]
                self.etat(col, "2 ECRIT : %s" % ("le Sheet gagne (valeur d'avant au journal)" if vals[a].strip()
                                                 else "sa vente existe, la case etait vide"))
                self.ecrire(famille="ledger", colonne=col, id_unique=i, num=self.num(i), piece=a, champ=champ, valeur=brut,
                            avant=D.L[a][ch], pourquoi="C8 du 16/11 : sur la vente, la case telle quelle")

    # ── la 1re rubrique du rapport : les dates que la nuit reecrit (montrees, jamais ecrites) ──
    def dates_du_rapport(self):
        D = self.D
        aujourd = datetime.now().date()
        for col, g in (("Compromis", "compromis"), ("Vente Fixée", "vente"), ("Offre Achat", "offre")):
            for i in D.ATT:
                if D.case(i, col):
                    self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
            for i in D.T:
                s = D.case(i, col)
                if not s:
                    continue
                d = K.d_sheet(s)
                if d is None:
                    self.etat(col, "5 je ne sais pas lire la case")
                    continue
                ps_ = D.pieces(i, g)
                if g == "compromis" and any(K.d_reg(str(D.L[a]["date"] or "")) == d for a in ps_):
                    self.etat(col, "1 egale chez Hektor")
                    continue
                if g == "compromis" and D.case(i, "Annulée"):
                    da = K.d_sheet(D.case(i, "Annulée"))
                    if da and da < d:
                        self.etat(col, "1 dehors (D3) : le Sheet porte le rendez-vous, l'annulation est avant")
                        continue
                if not ps_:
                    if d > aujourd:
                        self.etat(col, "1 un rendez-vous a venir (la piece se cree a la signature)")
                    else:
                        self.etat(col, "4 sans %s chez nous" % g)
                        if g == "offre":
                            continue        # les 170 de D10 : la ligne garde sa case, rien ne se cree (ni ici ni chez Hektor)
                        self.rapport_dates.append((col, i, self.num(i), s, "", "pas de %s chez nous" % g))
                    continue
                if g == "offre":
                    ds = {a: premiere_proposition(D.L[a]) for a in ps_}
                else:
                    ds = {a: K.d_reg(str(D.L[a]["date"] or "")) for a in ps_}
                    if g == "vente":
                        ds.update({-a: K.d_reg(str(D.L[a]["date_acte"] or "")) for a in ps_})
                if any(x == d for x in ds.values()):
                    self.etat(col, "1 egale chez Hektor")
                    continue
                vals = [(a, x) for a, x in ds.items() if x]
                if not vals:
                    self.etat(col, "3 au rapport : sa piece n'a pas de date chez nous")
                    self.rapport_dates.append((col, i, self.num(i), s, "", "la piece n'a pas de date"))
                    continue
                a, x = min(vals, key=lambda t: abs((t[1] - d).days))
                if g == "offre" and all(abs(a_) in D.R30.get(i, set()) for a_, _x in vals):
                    self.etat(col, "3 au rapport : sa seule offre est celle que R30a a rattachee (peut-etre pas la sienne)")
                    self.rapport_dates.append((col, i, self.num(i), s, x.strftime("%d/%m/%Y"),
                                               "offre %d rattachee par R30a, %s, ecart %+d j -- PEUT-ETRE PAS L'OFFRE DE LA "
                                               "LIGNE : ne rien corriger sans la regarder" % (abs(a), D.L[abs(a)]["state"],
                                                                                              (x - d).days)))
                    continue
                self.etat(col, "3 au rapport : la date differe (a corriger dans Hektor si tu le veux)")
                self.rapport_dates.append((col, i, self.num(i), s, x.strftime("%d/%m/%Y"),
                                           "%s %d, %s, ecart %+d j%s" % (g, abs(a), D.L[abs(a)]["state"], (x - d).days,
                                                                         "" if str(D.L[abs(a)]["annonce"]) in D.PARC
                                                                         else ", bien hors du parc")))

    # ── l'Etat Actuel : montre quand il contredit nos pieces, jamais ecrit ──
    def etat_actuel(self):
        D = self.D
        col = "Etat Actuel"
        for i in D.ATT:
            if D.case(i, col):
                self.etat(col, "0 sur une ligne en attente : pas de piece sure (le juge)")
        for i in D.T:
            s = D.case(i, col)
            if not s:
                continue
            ps_ = D.pieces(i)
            genres = {D.L[a]["kind"] for a in ps_}
            vivantes = [a for a in ps_ if D.L[a]["state"] in ("accepted", "proposed", "active")]
            pb = ""
            if s == "Vente réglée" and "vente" not in genres:
                pb = "le Sheet dit « Vente reglee », la ligne n'a pas de vente chez nous"
            elif s == "Annulée" and vivantes and "vente" not in genres:
                pb = "le Sheet dit « Annulee », chez nous %s est vivante (on n'y touche pas : jamais l'etat)" % "+".join(
                    "%s %d %s" % (D.L[a]["kind"], a, D.L[a]["state"]) for a in vivantes)
            elif s.startswith("Compromis") and "compromis" not in genres:
                pb = "le Sheet dit « %s », la ligne n'a pas de compromis chez nous" % s
            if pb:
                self.etat(col, "3 au rapport : il contredit nos pieces")
                self.signaux.append(("etat", col, i, pb))
            else:
                self.etat(col, "1 coherent avec nos pieces (ou rien a en dire)")


# ═══════════════════════════════════════ PIECE 6 : LE TEMOIN CHIFFRE ═════════════════════════════════════════════════
COLONNES_COMPTEES = ["COMMENTAIRES", "En attente de", "Avis à envoyer (oui / non)", "Commentaire Avis", "Avis envoyé",
                     "REPARTITION (les 6 colonnes)", "Annulée", "Commission TTC", "Charge Commission", "Vente Réglée",
                     "Numéro de facture", "Compromis", "Vente Fixée", "Offre Achat", "Etat Actuel"]


def le_sheet_porte(D: Donnees, col: str) -> int:
    if col == "REPARTITION (les 6 colonnes)":
        return sum(1 for i in D.V if i in D.ROW and any(D.case(i, "Négociateur %d" % k) for k in (1, 2, 3)))
    return sum(1 for i in D.V if i in D.ROW and D.case(i, col))


# ═══════════════════════════════════════ PIECE 7 : LA PORTE D'ECRITURE ═══════════════════════════════════════════════
def fabriquer_sql(E: Essai, lot: str, diff: list[dict], photo_avant: str) -> dict:
    """Le lot ENTIER en une transaction : gardes, empreinte d'avant, sauvegardes datees, journal, ecritures, controles."""
    D = E.D
    stamp = lot.split("_")[-1]
    S = {"ledger": "app_affaire_ledger_avant_maj_%s" % stamp, "note": "app_affaire_note_avant_maj_%s" % stamp,
         "avis": "app_classeur_avis_avant_maj_%s" % stamp, "charge": "app_mandat_champ_app_avant_maj_%s" % stamp,
         "reflet": "app_mandat_register_current_avant_maj_%s" % stamp}
    marque = "classeur:maj:%s" % stamp
    W = E.ecritures
    led = [w for w in W if w["famille"] == "ledger"]
    notes = [w for w in W if w["famille"] == "note"]
    avis = [w for w in W if w["famille"] == "avis"]
    parts = [w for w in W if w["famille"] == "part"]
    charges = [w for w in W if w["famille"] == "charge"]
    ids_led = sorted({w["piece"] for w in led})
    ids_note = sorted({w["piece"] for w in notes if w["geste"] == "paragraphe"})
    ids_note_neuve = sorted({w["piece"] for w in notes if w["geste"] == "note neuve"})
    assert len(ids_note_neuve) == sum(1 for w in notes if w["geste"] == "note neuve"), "deux notes neuves sur une piece"
    assert {w["piece"] for w in notes if w["geste"] == "sous la note neuve"} <= set(ids_note_neuve)
    assert not (set(ids_note) & set(ids_note_neuve)), "une piece recevrait une note neuve ET un paragraphe"
    assert not ((set(ids_note) | set(ids_note_neuve)) & set(NOTES_SAISIES)), "⛔ une des 9 notes saisies serait touchee"
    cles_led = Counter((w["piece"], w["champ"]) for w in led)
    assert all(n == 1 for n in cles_led.values()), "deux ecritures sur la meme case : %s" % [k for k, n in cles_led.items() if n > 1]
    ids_avis = sorted({w["id_unique"] for w in avis})
    chaines = sorted({w["chaine"] for w in parts})
    cles_ch = sorted({(w["annonce"], w["mandat"]) for w in charges})
    annonces_ch = sorted({w["annonce"] for w in charges})

    def lst(xs, f=str):
        return ", ".join(f(x) for x in xs) or "NULL"

    # l'empreinte d'avant : TOUT ce que le lot va toucher, tel que l'essai l'a lu (les gardes l'exigent a l'identique)
    emp_sql = ("select md5(concat_ws('#',\n"
               "  (select coalesce(string_agg(concat_ws('|', app_affaire_id, coalesce(date_annulation_app,'-'), "
               "coalesce(honoraires_entree_app,'-'), coalesce(vente_reglee_app,'-'), coalesce(numero_facture_app,'-')), ';' "
               "order by app_affaire_id), '') from public.app_affaire_ledger where app_affaire_id in (%s)),\n"
               "  (select coalesce(string_agg(app_affaire_id || ':' || md5(coalesce(texte,'')), ';' order by app_affaire_id), '') "
               "from public.app_affaire_note where app_affaire_id in (%s)),\n"
               "  (select coalesce(string_agg(concat_ws('|', id_unique, coalesce(avis_a_envoyer,'-'), coalesce(commentaire_avis,'-'), "
               "coalesce(avis_envoye,'-')), ';' order by id_unique), '') from public.app_classeur_avis where id_unique in (%s)),\n"
               "  (select count(*) from public.app_affaire_repartition where app_chaine_id in (%s)),\n"
               "  (select coalesce(string_agg(concat_ws('|', hektor_annonce_id, numero_mandat, coalesce(valeur_app,'-'), "
               "coalesce(origine,'-')), ';' order by hektor_annonce_id, numero_mandat), '') from public.app_mandat_champ_app "
               "where champ = 'charge_commission' and (hektor_annonce_id, numero_mandat) in (%s))))" % (
                   lst(ids_led), lst(ids_note + ids_note_neuve), lst(ids_avis, q), lst(chaines),
                   ", ".join("(%s, %s)" % (q(a), q(m)) for a, m in cles_ch) or "(NULL, NULL)"))
    corps = []
    corps.append("-- ═══ ① LES GARDES ═══")
    corps.append("do $$ declare n int; e text; begin\n"
                 "  if exists (select 1 from public.app_classeur_realignement_journal where lot = %s) then\n"
                 "    raise exception '⛔ garde : le lot %s est deja (en partie) au journal -- il ne se rejoue pas'; end if;\n"
                 "  if %s then raise exception '⛔ garde : une sauvegarde du lot existe deja'; end if;\n"
                 "  if (select string_agg(app_affaire_id::text, ',' order by app_affaire_id) from public.app_affaire_note "
                 "where origine = 'saisie') <> %s then\n"
                 "    raise exception '⛔ garde : les notes saisies ne sont plus les 9 nommees'; end if;\n"
                 "  e := (%s);\n"
                 "  if e <> '%%(EMPREINTE)s' then raise exception '⛔ garde : l''empreinte d''avant est %%, l''essai a lu %%(EMPREINTE)s "
                 "-- quelqu''un est passe, rien n''est ecrit', e; end if;\n"
                 "  raise notice '✅ gardes : empreinte d''avant %%', e;\nend $$;" % (
                     q(lot), lot, " or ".join("to_regclass('public.%s') is not null" % t for t in S.values()),
                     q(",".join(map(str, NOTES_SAISIES))), emp_sql))
    corps.append("create temp table _saisies_avant on commit drop as select app_affaire_id, md5(texte) m from "
                 "public.app_affaire_note where origine = 'saisie';")
    corps.append("-- ═══ ② LES SAUVEGARDES DATEES (RLS allumee, aucun droit ouvert) ═══")
    corps.append("create table public.%s as select * from public.app_affaire_ledger where app_affaire_id in (%s);"
                 % (S["ledger"], lst(ids_led)))
    corps.append("create table public.%s as select * from public.app_affaire_note where app_affaire_id in (%s);"
                 % (S["note"], lst(ids_note)))
    corps.append("create table public.%s as select * from public.app_classeur_avis where id_unique in (%s);"
                 % (S["avis"], lst(ids_avis, q)))
    corps.append("create table public.%s as select * from public.app_mandat_champ_app where champ = 'charge_commission' and "
                 "(hektor_annonce_id, numero_mandat) in (%s);" % (S["charge"], ", ".join("(%s, %s)" % (q(a), q(m)) for a, m
                                                                                          in cles_ch) or "(NULL, NULL)"))
    corps.append("create table public.%s as select * from public.app_mandat_register_current where hektor_annonce_id::text "
                 "in (%s);" % (S["reflet"], lst(annonces_ch, q)))
    for t in S.values():
        corps.append("alter table public.%s enable row level security; revoke all on public.%s from public, anon, authenticated;"
                     % (t, t))
    # ③ LE JOURNAL : une ligne par case, AVANT l'ecriture, avec sa valeur d'avant et sa ligne d'origine
    corps.append("-- ═══ ③ LE JOURNAL : une ligne par ecriture, sa valeur d'avant, sa ligne d'origine ═══")
    vals = []
    for n, w in enumerate(W, 1):
        fam = w["famille"]
        piece = w.get("piece")
        p = D.L.get(piece) if piece else None
        colonne = {"ledger": "app_affaire_ledger.%s" % w.get("champ"), "note": "app_affaire_note.texte",
                   "avis": "app_classeur_avis.%s" % w.get("champ"), "part": "app_affaire_repartition",
                   "charge": "app_mandat_champ_app.valeur_app (charge_commission)"}[fam]
        geste = w.get("geste") or ("poser" if w.get("avant") in (None, "") else "le Sheet gagne")
        if fam == "part":
            valeur = "%s rang %d : %s (%s) %g %%" % (w["cote"], w["rang"], w["u"], w["nom"], w["pc"])
        else:
            valeur = w["valeur"]
        vals.append("(%s, %d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % (
            q(lot), n, q(fam + " / " + w["colonne"]), q(colonne), q(geste), piece if piece else "NULL",
            q(p["kind"]) if p else "NULL", (w.get("chaine") or (p["chaine"] if p else None)) or "NULL",
            q(p["dossier_numero"]) if p and p["dossier_numero"] else "NULL",
            (q(p["dossier_uuid"]) + "::uuid") if p and p["dossier_uuid"] else "NULL", q(valeur),
            q(w.get("avant")) if w.get("avant") is not None else "NULL", q(w["id_unique"]),
            w["num"] if str(w["num"]).isdigit() else "NULL", q("Sheet, photo %s (passage %d)" % (D.image, D.passage)),
            q(w.get("pourquoi") or ""), q(marque), q(w.get("annonce")) if w.get("annonce") else "NULL",
            q(w.get("mandat")) if w.get("mandat") else "NULL"))
    if vals:
        corps.append("insert into public.app_classeur_realignement_journal (lot, n, famille, colonne, geste, de_app_affaire_id, "
                     "de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid, valeur, ancienne_valeur, ligne_origine, "
                     "ligne_origine_num, lot_origine, pourquoi, ecrit_par, mandat_annonce, mandat_numero)\nvalues\n  "
                     + ",\n  ".join(vals) + ";")
    # le journal des differences (la piece 2), dans la meme transaction
    if diff:
        corps.append("-- le journal des differences : %s -> %s (%d cases)" % (photo_avant, D.image, len(diff)))
        dv = ["(%s, %s, %s, %s, %s, %s, %s, %s, %s)" % (q(photo_avant), q(D.image), q(d["id_unique"]),
                                                       d["num"] if str(d["num"]).isdigit() else "NULL", q(d["colonne"]),
                                                       q(d["avant"]), q(d["apres"]), q(d["nature"]), q(lot)) for d in diff]
        for k in range(0, len(dv), 2000):
            corps.append("insert into public.app_classeur_difference (photo_avant, photo_apres, id_unique, num, colonne, "
                         "avant, apres, nature, lot) values\n  " + ",\n  ".join(dv[k:k + 2000]) + ";")
    corps.append("-- ═══ ④ LES ECRITURES ═══")
    for w in led:
        corps.append("update public.app_affaire_ledger set %s = %s where app_affaire_id = %d;  -- %s %s"
                     % (w["champ"], q(w["valeur"]), w["piece"], w["id_unique"], w["colonne"]))
    par_piece = defaultdict(list)
    for w in notes:
        if w["geste"] == "paragraphe":
            par_piece[w["piece"]].append(w["valeur"])
    for a, ts in sorted(par_piece.items()):
        corps.append("update public.app_affaire_note set texte = texte || E'\\n' || %s where app_affaire_id = %d;"
                     % (q("\n".join(ts)), a))
    neuves = [w for w in notes if w["geste"] == "note neuve"]
    sous = defaultdict(list)
    for w in notes:
        if w["geste"] == "sous la note neuve":
            sous[w["piece"]].append(w)

    def texte_neuf(w):
        return "\n".join([w["valeur"]] + [x["valeur"] for x in sous[w["piece"]]])

    def origine_neuve(w):
        lettres = {w["origine"]} | {x["origine"] for x in sous[w["piece"]]}
        return "classeur:F+G" if lettres == {"classeur:G", "classeur:F"} else w["origine"]
    if neuves:
        corps.append("insert into public.app_affaire_note (app_affaire_id, app_dossier_id, app_chaine_id, origine, texte, "
                     "ecrit_par) values\n  " + ",\n  ".join(
                         "(%d, %s, %s, %s, %s, %s)" % (w["piece"], D.L[w["piece"]]["dossier"] or "NULL",
                                                      D.L[w["piece"]]["chaine"] or "NULL", q(origine_neuve(w)),
                                                      q(texte_neuf(w)), q(marque)) for w in neuves) + ";")
    avis_neufs = sorted({w["id_unique"] for w in avis if w["ligne_neuve"]})
    for i in avis_neufs:
        e = next(w["etiquette"] for w in avis if w["id_unique"] == i)
        corps.append("insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values "
                     "(%s, 'classeur', %s, %s);" % (q(i), q(marque), (q(e) + "::uuid") if e else "NULL"))
    for w in avis:
        corps.append("update public.app_classeur_avis set %s = %s, ecrit_par = %s, ecrit_le = now() where id_unique = %s;"
                     % (w["champ"], q(w["valeur"]), q(marque), q(w["id_unique"])))
    if parts:
        corps.append("insert into public.app_affaire_repartition (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, "
                     "nom_au_moment, pourcentage, origine, ecrit_par) values\n  " + ",\n  ".join(
                         "(%d, %s, %s, %d, %s, %s, %s, 'classeur_reconstitue', %s)" % (
                             w["chaine"], w["dossier"] or "NULL", q(w["cote"]), w["rang"], q(w["u"]), q(w["nom"]), w["pc"],
                             q(marque)) for w in parts) + ";")
    for w in charges:
        corps.append("insert into public.app_mandat_champ_app (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, "
                     "ecrit_par, ecrit_le) values (%s, %s, 'charge_commission', %s, 'classeur', %s, now())\n"
                     "  on conflict (hektor_annonce_id, numero_mandat, champ) do update set valeur_app = excluded.valeur_app, "
                     "origine = 'classeur', ecrit_par = excluded.ecrit_par, ecrit_le = now();"
                     % (q(w["annonce"]), q(w["mandat"]), q(w["valeur"]), q(marque)))
    for a in annonces_ch:
        corps.append("select public.app_reposer_charge_mandat_app(%s, 10000);" % q(a))
    # ⑤ LES CONTROLES : chaque case porte sa valeur ; rien d'autre n'a bouge ; les 9 notes saisies intactes
    corps.append("-- ═══ ⑤ LES CONTROLES ═══")
    ctl = ["do $$ declare n int; begin"]
    if led:
        ctl.append("  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l\n"
                   "    on l.app_affaire_id = j.de_app_affaire_id where j.lot = %s and j.famille like 'ledger / %%' and\n"
                   "    j.valeur = case split_part(j.colonne, '.', 2) when 'date_annulation_app' then l.date_annulation_app\n"
                   "      when 'honoraires_entree_app' then l.honoraires_entree_app when 'vente_reglee_app' then l.vente_reglee_app\n"
                   "      when 'numero_facture_app' then l.numero_facture_app end;\n"
                   "  if n <> %d then raise exception '⛔ controle : %% cases du registre portent leur valeur (attendu %d)', n; end if;"
                   % (q(lot), len(led), len(led)))
        ctl.append("  select count(*) into n from public.app_affaire_ledger l join public.%s s using (app_affaire_id)\n"
                   "   where (l.date_annulation_app, l.honoraires_entree_app, l.vente_reglee_app, l.numero_facture_app) is distinct from\n"
                   "         (s.date_annulation_app, s.honoraires_entree_app, s.vente_reglee_app, s.numero_facture_app);\n"
                   "  if n <> %d then raise exception '⛔ controle : %% pieces du registre ont bouge (attendu %d)', n; end if;"
                   % (S["ledger"], len(ids_led), len(ids_led)))
    if notes:
        ctl.append("  select count(*) into n from public.app_affaire_note where ecrit_par = %s;\n"
                   "  if n <> %d then raise exception '⛔ controle : %% notes neuves (attendu %d)', n; end if;" % (
                       q(marque), len(neuves), len(neuves)))
        ctl.append("  select count(*) into n from public.app_affaire_note a join public.%s s using (app_affaire_id)\n"
                   "   where left(a.texte, length(s.texte)) <> s.texte or a.texte = s.texte;\n"
                   "  if n <> 0 then raise exception '⛔ controle : %% note(s) dont le texte d''avant n''est plus intact au-dessus', n; end if;"
                   % S["note"])
    ctl.append("  select count(*) into n from _saisies_avant s join public.app_affaire_note a using (app_affaire_id) where md5(a.texte) = s.m;\n"
               "  if n <> 9 then raise exception '⛔ controle : % des 9 notes saisies seulement sont intactes', n; end if;")
    if avis:
        ctl.append("  select count(*) into n from public.app_classeur_avis where ecrit_par = %s;\n"
                   "  if n <> %d then raise exception '⛔ controle : %% lignes d''avis marquees (attendu %d)', n; end if;" % (
                       q(marque), len(ids_avis), len(ids_avis)))
    if parts:
        ctl.append("  select count(*) into n from public.app_affaire_repartition where ecrit_par = %s;\n"
                   "  if n <> %d then raise exception '⛔ controle : %% parts (attendu %d)', n; end if;\n"
                   "  select count(*) into n from (select app_chaine_id from public.app_affaire_repartition where app_chaine_id in (%s)\n"
                   "   group by 1 having sum(pourcentage) > 100.001) x;\n"
                   "  if n <> 0 then raise exception '⛔ controle : %% chaine(s) au-dela de 100 %%%%', n; end if;" % (
                       q(marque), len(parts), len(parts), lst(chaines)))
    if charges:
        ctl.append("  select count(*) into n from public.app_mandat_champ_app where champ = 'charge_commission' and ecrit_par = %s;\n"
                   "  if n <> %d then raise exception '⛔ controle : %% charges au carnet (attendu %d)', n; end if;\n"
                   "  select count(*) into n from public.app_mandat_register_current r join public.app_mandat_champ_app k\n"
                   "    on k.hektor_annonce_id = r.hektor_annonce_id::text and k.numero_mandat = r.numero_mandat::text\n"
                   "   where k.champ = 'charge_commission' and k.ecrit_par = %s and r.mandat_charge_honoraires_app is distinct from nullif(btrim(k.valeur_app), '');\n"
                   "  if n <> 0 then raise exception '⛔ controle : %% reflet(s) ne portent pas la charge', n; end if;" % (
                       q(marque), len(charges), len(charges), q(marque)))
    ctl.append("  select count(*) into n from public.app_classeur_realignement_journal where lot = %s;\n"
               "  if n <> %d then raise exception '⛔ controle : %% lignes au journal (attendu %d)', n; end if;" % (
                   q(lot), len(W), len(W)))
    ctl.append("  raise notice '✅ lot %s : %d ecritures (registre %d, notes %d, avis %d, parts %d, charges %d), journal complet';\n"
               "end $$;" % (lot, len(W), len(led), len(notes), len(avis), len(parts), len(charges)))
    corps.append("\n".join(ctl))
    corps.append("-- l'empreinte d'apres (l'inverse et la repetition la relisent)")
    corps.append("do $$ begin raise notice 'EMPREINTE APRES %%', (%s); end $$;" % emp_sql)
    tete = ("-- %s -- LA MISE A JOUR QUOTIDIENNE DEPUIS LE SHEET, chez nous seulement, JAMAIS chez Hektor\n"
            "-- Fabrique par phase2/checks/maj_quotidienne_du_classeur.py -- passage %d, photo %s\n"
            "-- %d ecritures : registre %d, notes %d, avis %d, parts %d, charges %d. Retour : ..._INVERSE.sql\n")
    corps_txt = "\n".join(corps) + "\n"
    inverse = (
        "-- INVERSE du lot %s : rend chaque case a sa valeur d'avant (les sauvegardes datees), retire ce que le lot a pose.\n"
        "-- Il ne juge que SA part (lecon 31). Les sauvegardes restent.\n\nbegin;\n"
        "update public.app_affaire_ledger l set date_annulation_app = s.date_annulation_app, honoraires_entree_app = "
        "s.honoraires_entree_app,\n  vente_reglee_app = s.vente_reglee_app, numero_facture_app = s.numero_facture_app\n"
        "  from public.%s s where s.app_affaire_id = l.app_affaire_id;\n"
        "delete from public.app_affaire_note where ecrit_par = %s;\n"
        "update public.app_affaire_note a set texte = s.texte from public.%s s where s.app_affaire_id = a.app_affaire_id;\n"
        "delete from public.app_classeur_avis where ecrit_par = %s and id_unique not in (select id_unique from public.%s);\n"
        "update public.app_classeur_avis a set avis_a_envoyer = s.avis_a_envoyer, commentaire_avis = s.commentaire_avis,\n"
        "  avis_envoye = s.avis_envoye, ecrit_par = s.ecrit_par, ecrit_le = s.ecrit_le from public.%s s where s.id_unique = a.id_unique;\n"
        "delete from public.app_affaire_repartition where ecrit_par = %s;\n"
        "delete from public.app_mandat_champ_app where champ = 'charge_commission' and ecrit_par = %s\n"
        "  and (hektor_annonce_id, numero_mandat) not in (select hektor_annonce_id, numero_mandat from public.%s);\n"
        "update public.app_mandat_champ_app k set valeur_app = s.valeur_app, origine = s.origine, ecrit_par = s.ecrit_par, "
        "ecrit_le = s.ecrit_le\n  from public.%s s where s.champ = k.champ and s.hektor_annonce_id = k.hektor_annonce_id "
        "and s.numero_mandat = k.numero_mandat;\n%s\n"
        "delete from public.app_classeur_difference where lot = %s;\n"
        "delete from public.app_classeur_realignement_journal where lot = %s;\n"
        "do $$ declare n int; begin\n"
        "  select count(*) into n from public.app_affaire_ledger l join public.%s s using (app_affaire_id)\n"
        "   where (l.date_annulation_app, l.honoraires_entree_app, l.vente_reglee_app, l.numero_facture_app) is distinct from\n"
        "         (s.date_annulation_app, s.honoraires_entree_app, s.vente_reglee_app, s.numero_facture_app);\n"
        "  if n <> 0 then raise exception '⛔ inverse : %% piece(s) du registre ne sont pas revenues', n; end if;\n"
        "  select count(*) into n from public.app_affaire_note where ecrit_par = %s;\n"
        "  if n <> 0 then raise exception '⛔ inverse : %% note(s) du lot restent', n; end if;\n"
        "  select count(*) into n from public.app_affaire_note a join public.%s s using (app_affaire_id) where a.texte <> s.texte;\n"
        "  if n <> 0 then raise exception '⛔ inverse : %% note(s) ne sont pas revenues a l''octet', n; end if;\n"
        "  select count(*) into n from public.app_affaire_repartition where ecrit_par = %s;\n"
        "  if n <> 0 then raise exception '⛔ inverse : %% part(s) du lot restent', n; end if;\n"
        "  select count(*) into n from public.app_mandat_champ_app where ecrit_par = %s;\n"
        "  if n <> 0 then raise exception '⛔ inverse : %% charge(s) du lot restent', n; end if;\n"
        "  raise notice '✅ inverse : le lot %s est retire, les sauvegardes restent';\nend $$;\ncommit;\n" % (
            lot, S["ledger"], q(marque), S["note"], q(marque), S["avis"], S["avis"], q(marque), q(marque), S["charge"],
            S["charge"], "\n".join("select public.app_reposer_charge_mandat_app(%s, 10000);" % q(a) for a in annonces_ch),
            q(lot), q(lot), S["ledger"], q(marque), S["note"], q(marque), q(marque), lot))
    repetition = (
        "-- REPETITION du lot %s (lecture seule) -- attendu : journal %d, registre %d cases a leur valeur, notes neuves %d, "
        "avis %d, parts %d, charges %d, 9 notes saisies\n"
        "select (select count(*) from public.app_classeur_realignement_journal where lot = %s) journal,\n"
        "  (select count(*) from public.app_classeur_realignement_journal j join public.app_affaire_ledger l on l.app_affaire_id = j.de_app_affaire_id\n"
        "    where j.lot = %s and j.famille like 'ledger / %%' and j.valeur = case split_part(j.colonne, '.', 2)\n"
        "      when 'date_annulation_app' then l.date_annulation_app when 'honoraires_entree_app' then l.honoraires_entree_app\n"
        "      when 'vente_reglee_app' then l.vente_reglee_app when 'numero_facture_app' then l.numero_facture_app end) registre,\n"
        "  (select count(*) from public.app_affaire_note where ecrit_par = %s) notes_neuves,\n"
        "  (select count(*) from public.app_affaire_note a join public.%s s using (app_affaire_id)\n"
        "    where left(a.texte, length(s.texte)) <> s.texte) textes_d_avant_abimes,\n"
        "  (select count(*) from public.app_classeur_avis where ecrit_par = %s) avis,\n"
        "  (select count(*) from public.app_affaire_repartition where ecrit_par = %s) parts,\n"
        "  (select count(*) from public.app_mandat_champ_app where ecrit_par = %s) charges,\n"
        "  (select count(*) from public.app_affaire_note where origine = 'saisie') notes_saisies,\n"
        "  (select count(*) from public.app_classeur_difference where lot = %s) differences;\n" % (
            lot, len(W), len(led), len(neuves), len(ids_avis), len(parts), len(charges), q(lot), q(lot), q(marque),
            S["note"], q(marque), q(marque), q(marque), q(lot)))
    return {"tete": tete % (lot, D.passage, D.image, len(W), len(led), len(notes), len(avis), len(parts), len(charges)),
            "corps": corps_txt, "inverse": inverse, "repetition": repetition, "empreinte_sql": emp_sql,
            "attendus": {"journal": len(W), "registre": len(led), "notes_neuves": len(neuves), "paragraphes": len(par_piece),
                         "avis": len(ids_avis), "parts": len(parts), "charges": len(charges), "differences": len(diff)}}


# ═══════════════════════════════════════ PIECE 8 : LE RAPPORT DU MATIN ═══════════════════════════════════════════════
def rapport_du_matin(E: Essai, lot: str, boucle: dict, diff_r: dict | None, photo_avant: str, attendus: dict) -> Path:
    D = E.D
    L = []
    a = L.append
    a("# Le rapport du matin — %s" % datetime.now().strftime("%d/%m/%Y %H:%M"))
    a("")
    a("> Lot `%s` · photo du Sheet `%s` · passage du juge %d · %d lignes, %d tranchées, %d en attente." % (
        lot, D.image, D.passage, len(D.V), len(D.T), len(D.ATT)))
    a("> **Rien n'a été écrit** : c'est l'essai à blanc. Ce qui s'écrirait attend ton « vas-y ».")
    a("")
    a("## 1. Les dates que la nuit réécrit — à corriger dans Hektor si tu le veux")
    a("")
    a("La date du compromis, celle de la vente fixée et celle de l'offre ne s'écrivent jamais chez nous : la nuit les "
      "réécrit comme Hektor les donne. Les voici, quand elles diffèrent.")
    a("")
    for col in ("Compromis", "Vente Fixée", "Offre Achat"):
        rs = [x for x in E.rapport_dates if x[0] == col]
        a("**%s : %d.**" % (col, len(rs)))
        a("")
        for _c, i, num, s, h, quoi in sorted(rs, key=lambda x: (x[2] or 0)):
            a("- ligne %s (`%s`) : le Sheet dit %s%s — %s" % (num, i, s, (", Hektor dit %s" % h) if h else "", quoi))
        a("")
    a("## 2. Ce qui s'écrirait chez nous, colonne par colonne")
    a("")
    a("Chaque colonne boucle : le Sheet porte N cases = la somme de leurs états.")
    a("")
    for col in COLONNES_COMPTEES:
        et = E.etats.get(col, Counter())
        a("**%s** — le Sheet porte %d cases, la somme fait %d : %s." % (col, boucle[col][0], boucle[col][1],
                                                                       "boucle" if boucle[col][0] == boucle[col][1]
                                                                       else "⛔ NE BOUCLE PAS"))
        a("")
        for k, n in sorted(et.items()):
            a("- %s : %d" % (k, n))
        a("")
    a("**Le total de ce qui s'écrirait** : %d écritures — %s." % (attendus["journal"], ", ".join(
        "%s %d" % (k, v) for k, v in attendus.items() if k != "journal")))
    a("")
    a("## 3. Ce que je signale sans l'écrire")
    a("")
    for rub, titre in (("commission", "La Commission (les contrôles ③ ④ ⑥ de D6)"), ("etat", "L'État Actuel qui contredit nos pièces")):
        rs = [x for x in E.signaux if x[0] == rub]
        a("**%s : %d.**" % (titre, len(rs)))
        a("")
        for _r, _c, i, ph in rs:
            a("- ligne %s (`%s`) : %s" % (E.num(i), i, ph))
        a("")
    if diff_r:
        a("## 4. Ce qui a bougé dans le Sheet depuis la photo %s" % photo_avant)
        a("")
        a("%d cases changées (%d hors colonne A), %d lignes neuves, %d disparues." % (
            diff_r["cases"], diff_r["hors_colonne_A"], diff_r["lignes_neuves"], diff_r["lignes_disparues"]))
        a("")
        for c, n in diff_r["par_colonne"].items():
            a("- %s : %d" % (c, n))
        a("")
    a("## 5. Ta liste — ce que je ne sais pas trancher, mis de côté (%d cas, %d motifs)" % (
        len(E.liste), len({(x[0], x[3]) for x in E.liste})))
    a("")
    groupes = defaultdict(list)
    for col, i, ph, motif in E.liste:
        groupes[(col, motif)].append((i, ph))
    for k, ((col, motif), cas) in enumerate(sorted(groupes.items(), key=lambda kv: (-len(kv[1]), kv[0])), 1):
        if len(cas) == 1:
            i, ph = cas[0]
            a("%d. **%s**, ligne %s (`%s`) : %s." % (k, col, E.num(i), i, ph))
            continue
        a("%d. **%s — %d cas** : %s." % (k, col, len(cas), motif))
        for i, ph in sorted(cas, key=lambda c: E.num(c[0]) or 0):
            a("   - ligne %s (`%s`) : %s" % (E.num(i), i, ph))
    a("")
    f = RAPPORTS / ("RAPPORT_DU_MATIN_CLASSEUR_%s.md" % lot.split("_")[-1])
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    return f


# ═══════════════════════════════════════ LES ETAPES ══════════════════════════════════════════════════════════════════
def lire_routeur() -> tuple[dict, str]:
    """L'INTERRUPTEUR de chaque colonne : la table app_champ_destination (D9) ; vide ou absente -> la graine du code, et
    l'outil le DIT. Une colonne eteinte est comptee, montree, jamais ecrite."""
    cn, cu = P.pooler()
    cu.execute("select to_regclass('public.app_champ_destination') is not null")
    lignes = []
    if cu.fetchone()[0]:
        cu.execute("select colonne_sheet, famille, ecrit from public.app_champ_destination")
        lignes = cu.fetchall()
    cn.close()
    if lignes:
        return {c: bool(e) for c, _f, e in lignes}, "la table app_champ_destination (%d colonnes)" % len(lignes)
    return {c: bool(e) for c, _f, _d, _r, _h, e, _ra in ROUTEUR}, "la GRAINE du code (la table est vide)"


def deja_rendu_qui_bouge(avant: int, apres: int) -> list:
    """LE TEMOIN DU JUGE (plan § 6, piece 6) : une ligne TRANCHEE au passage d'avant qui change d'etiquette (ou retombe en
    attente) au passage du jour. Une ligne neuve, ou une ligne en attente qui se tranche, n'est pas un ecart."""
    so = sqlite3.connect("file:%s?mode=ro" % P.SOCLE.as_posix(), uri=True)
    a = {i: (v, e) for i, v, e in so.execute("select id_unique, verdict, etiquette from verdict where passage=?", (avant,))}
    b = {i: (v, e) for i, v, e in so.execute("select id_unique, verdict, etiquette from verdict where passage=?", (apres,))}
    so.close()
    if not a or not b:
        raise SystemExit("⛔ passage %d ou %d absent du socle" % (avant, apres))
    return sorted((i, a[i], b.get(i)) for i in a if a[i][0] == "TRANCHEE" and b.get(i) != a[i])


def etape_essai(passage: int, photo_avant: str | None, passage_avant: int | None = None) -> int:
    t0 = datetime.now()
    lot = "maj_classeur_%s" % t0.strftime("%Y%m%d%H%M%S")
    dire("L'ESSAI A BLANC DE L'OUTIL, SUR TOUT LE STOCK -- lot %s (rien n'est ecrit)" % lot)
    D = Donnees(passage)
    lu = datetime.fromisoformat(D.photo["lu_le"])
    E = Essai(D, lu.strftime("%d/%m/%Y"))
    dire("   passage %d, photo %s (lue le %s) : %d lignes, %d tranchees, %d en attente ; base : %d pieces, %d notes, %d avis"
         % (passage, D.image, D.photo["lu_le"], len(D.V), len(D.T), len(D.ATT), len(D.L), len(D.N), len(D.AV)))
    E.notes()
    E.avis()
    E.parts()
    E.annulation()
    E.commission()
    E.charge()
    E.valeurs_vente()
    E.dates_du_rapport()
    E.etat_actuel()
    E.arbitrer()
    allume, source = lire_routeur()
    eteintes = Counter()
    gardees = []
    for w in E.ecritures:
        cle = "Négociateur 1" if w["colonne"].startswith("REPARTITION") else w["colonne"]
        if allume.get(cle):
            gardees.append(w)
        else:
            eteintes[w["colonne"]] += 1
    E.ecritures = gardees
    dire("   LE ROUTEUR : %s ; ecritures retenues par un interrupteur eteint : %s" % (source, dict(eteintes) or "aucune"))
    # PIECE 6 : LE TEMOIN CHIFFRE -- chaque colonne boucle, sinon ARRET
    boucle, crie = {}, []
    for col in COLONNES_COMPTEES:
        porte = le_sheet_porte(D, col)
        somme = sum(E.etats[col].values())
        boucle[col] = (porte, somme)
        dire("   %-30s le Sheet porte %5d ; somme des etats %5d : %s" % (col, porte, somme, "boucle" if porte == somme
                                                                          else "⛔ NE BOUCLE PAS"))
        for k, n in sorted(E.etats[col].items()):
            dire("        %-92s %5d" % (k, n))
        if porte != somme:
            crie.append(col)
    conflits = {w["id_unique"] for w in E.ecritures if w["famille"] == "ledger" and w["colonne"] == "Commission TTC"
                and w["pourquoi"].startswith("D6, conflit")}
    dire("   LES CONFLITS DE COMMISSION ECRITS : %s -- annonces : %s : %s" % (
        sorted(conflits), sorted(CONFLITS_ANNONCES), "LES MEMES" if conflits == CONFLITS_ANNONCES else
        "⛔ PAS CEUX ANNONCES (en trop %s, manquent %s)" % (sorted(conflits - CONFLITS_ANNONCES),
                                                          sorted(CONFLITS_ANNONCES - conflits))))
    if conflits != CONFLITS_ANNONCES:
        crie.append("Commission TTC (les six conflits)")
    diff, diff_r = [], None
    if passage_avant:
        bouge = deja_rendu_qui_bouge(passage_avant, passage)
        dire("   LE TEMOIN DU JUGE : passage %d -> %d, lignes deja rendues qui changent : %d%s" % (
            passage_avant, passage, len(bouge), (" -- " + " . ".join("%s %s -> %s" % x for x in bouge[:20])) if bouge else ""))
        if bouge:
            crie.append("le juge : %d ligne(s) deja rendue(s) changent d'etiquette" % len(bouge))
    if photo_avant:
        diff = differences(lire_photo(photo_avant), D.photo)
        diff_r = resume_differences(diff)
    sql = fabriquer_sql(E, lot, diff, photo_avant or "")
    SORTIE.mkdir(parents=True, exist_ok=True)
    d = SORTIE / lot
    d.mkdir()
    (d / "decisions.json").write_text(json.dumps({"lot": lot, "passage": passage, "image": D.image, "photo_avant": photo_avant,
                                                  "groupes_de_la_liste": Counter("%s | %s" % (x[0], x[3]) for x in E.liste),
                                                  "ecritures": E.ecritures, "signaux": E.signaux, "liste": E.liste,
                                                  "rapport_dates": E.rapport_dates,
                                                  "etats": {c: dict(v) for c, v in E.etats.items()},
                                                  "attendus": sql["attendus"], "empreinte_sql": sql["empreinte_sql"]}, ensure_ascii=False, indent=0, default=str),
                                      encoding="utf-8")
    (d / "patch_A_BLANC.sql").write_text(sql["tete"] + "-- ⛔ A BLANC : il finit par une erreur VOULUE, tout est annule.\n"
                                         "\nbegin;\n" + sql["corps"] + "do $$ begin raise exception 'A BLANC MAJ CLASSEUR VERT "
                                         "-- RIEN N''EST ECRIT'; end $$;\n", encoding="utf-8")
    (d / "patch_modele.sql").write_text(sql["tete"] + "\nbegin;\n" + sql["corps"] + "commit;\n", encoding="utf-8")
    (d / "patch_INVERSE.sql").write_text(sql["inverse"], encoding="utf-8")
    (d / "patch_REPETITION.sql").write_text(sql["repetition"], encoding="utf-8")
    with (d / "ecritures.csv").open("w", encoding="utf-8-sig", newline="") as h:
        w = csv.writer(h, delimiter=";")
        w.writerow(["famille", "colonne", "id_unique", "ligne", "piece", "champ_ou_geste", "avant", "apres", "pourquoi"])
        for x in E.ecritures:
            w.writerow([x["famille"], x["colonne"], x["id_unique"], x["num"], x.get("piece") or x.get("chaine") or
                        "%s/%s" % (x.get("annonce"), x.get("mandat")), x.get("champ") or x.get("geste") or x.get("cote"),
                        (x.get("avant") or "")[:200], (x.get("valeur") if "valeur" in x else "%s %s %g" % (
                            x["u"], x["nom"], x["pc"]))[:300], x.get("pourquoi", "")])
    f = rapport_du_matin(E, lot, boucle, diff_r, photo_avant or "", sql["attendus"])
    dire("   ⇒ %d ecritures : %s" % (sql["attendus"]["journal"], sql["attendus"]))
    dire("   ⇒ signaux : %d ; dates au rapport : %d ; SA LISTE : %d cas" % (len(E.signaux), len(E.rapport_dates), len(E.liste)))
    dire("   -> %s" % d)
    dire("   -> rapport du matin : %s" % f)
    if crie:
        dire("⛔ ARRET : %s" % crie)
        return 1
    dire("   (%.0f s) -- prochain pas : a_blanc --lot %s" % ((datetime.now() - t0).total_seconds(), lot))
    return 0


def lire_empreinte(cu, lot: str) -> str:
    cu.execute(json.loads((SORTIE / lot / "decisions.json").read_text(encoding="utf-8"))["empreinte_sql"])
    return cu.fetchone()[0]


def jouer(lot: str, mode: str, empreinte: str | None = None) -> int:
    d = SORTIE / lot
    if not d.exists():
        raise SystemExit("⛔ lot inconnu : %s" % lot)
    so = socle_module()
    cn = so.connexion_ecriture()
    cn.autocommit = True
    cu = cn.cursor()
    cu.execute("begin read only")
    e_avant = lire_empreinte(cu, lot)
    cu.execute("rollback")
    dire("   empreinte d'avant, relue maintenant : %s" % e_avant)
    if mode == "a_blanc":
        txt = (d / "patch_A_BLANC.sql").read_text(encoding="utf-8").replace("%(EMPREINTE)s", e_avant)
    else:
        if empreinte != e_avant:
            dire("⛔ l'empreinte donnee (%s) n'est pas celle de la base (%s) : rien n'est ecrit" % (empreinte, e_avant))
            cn.close()
            return 1
        txt = (d / "patch_modele.sql").read_text(encoding="utf-8").replace("%(EMPREINTE)s", e_avant)
        (d / "patch_JOUE.sql").write_text(txt, encoding="utf-8")
    code = 0
    try:
        cu.execute(txt)
        if mode == "a_blanc":
            dire("⛔ l'a blanc n'a PAS leve son erreur voulue")
            code = 2
        else:
            dire("✅ joue sans erreur")
    except Exception as e:  # noqa: BLE001
        msg = str(e).splitlines()[0]
        dire("erreur levee : %s" % msg[:300])
        code = 0 if (mode == "a_blanc" and "A BLANC" in msg and "VERT" in msg) else 1
        try:
            cu.execute("rollback")
        except Exception:  # noqa: BLE001
            pass
    for n in cn.notices:
        dire("notice : %s" % n.strip()[:300])
    cn.close()
    if mode == "a_blanc" and code == 0:
        dire("✅ A BLANC VERT -- rien n'est ecrit. L'empreinte a donner a l'ecriture : %s" % e_avant)
    return code


def etape_repetition(lot: str) -> int:
    d = SORTIE / lot
    att = json.loads((d / "decisions.json").read_text(encoding="utf-8"))["attendus"]
    cn, cu = P.pooler()
    cu.execute((d / "patch_REPETITION.sql").read_text(encoding="utf-8"))
    cols = [x[0] for x in cu.description]
    r = dict(zip(cols, cu.fetchone()))
    cn.close()
    dire("REPETITION du lot %s : %s" % (lot, r))
    ok = (r["journal"] == att["journal"] and r["registre"] == att["registre"] and r["notes_neuves"] == att["notes_neuves"]
          and r["textes_d_avant_abimes"] == 0 and r["avis"] == att["avis"] and r["parts"] == att["parts"]
          and r["charges"] == att["charges"] and r["notes_saisies"] == 9 and r["differences"] == att["differences"])
    dire("⇒ %s" % ("VERT : chaque case porte sa valeur, rien d'abime" if ok else "⛔ ROUGE : %s attendu" % att))
    return 0 if ok else 1


def etape_routeur(poser: bool) -> int:
    cn, cu = P.pooler()
    cu.execute("select to_regclass('public.app_champ_destination') is not null")
    existe = cu.fetchone()[0]
    n = 0
    if existe:
        cu.execute("select count(*) from public.app_champ_destination")
        n = cu.fetchone()[0]
    cn.close()
    dire("LE ROUTEUR : table %s, %d ligne(s) ; graine du code : %d colonnes" % ("presente" if existe else "ABSENTE", n,
                                                                              len(ROUTEUR)))
    for c, fam, dest, regle, hk, ecrit, raison in ROUTEUR:
        dire("   %-28s %-13s %-5s %s" % (c, fam, "ECRIT" if ecrit else "-", dest))
    if poser:
        if not existe or n:
            dire("⛔ la table n'existe pas ou n'est pas vide : rien n'est pose")
            return 1
        so = socle_module()
        w = so.connexion_ecriture()
        c = w.cursor()
        for k, (col, fam, dest, regle, hk, ecrit, raison) in enumerate(ROUTEUR, 1):
            c.execute("insert into public.app_champ_destination (colonne_sheet, ordre, famille, destination, regle, hektor, "
                      "ecrit, raison, sens) values (%s, %s, %s, %s, %s, %s, %s, %s, 'sheet_vers_app')",
                      (col, k, fam, dest, regle, hk, ecrit, raison))
        w.commit()
        w.close()
        dire("✅ %d lignes posees" % len(ROUTEUR))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="etape", required=True)
    d = sp.add_parser("differences")
    d.add_argument("--de")
    d.add_argument("--a")
    e = sp.add_parser("essai")
    e.add_argument("--passage", type=int, required=True)
    e.add_argument("--photo-avant", default=None, help="la photo de la veille, pour le journal des differences")
    e.add_argument("--passage-avant", type=int, default=None, help="le passage de la veille, pour le temoin du juge")
    b = sp.add_parser("a_blanc")
    b.add_argument("--lot", required=True)
    w = sp.add_parser("ecrire")
    w.add_argument("--lot", required=True)
    w.add_argument("--empreinte", required=True)
    r = sp.add_parser("repetition")
    r.add_argument("--lot", required=True)
    ro = sp.add_parser("routeur")
    ro.add_argument("--poser", action="store_true")
    a = ap.parse_args()
    heure = datetime.now().strftime("%H:%M")
    if a.etape != "differences" and "04:00" <= heure < "07:30":
        dire("⛔ %s : la nuit et la descente tournent -- rien sur la base entre 04:00 et 07:30" % heure)
        return 2
    if a.etape == "differences":
        return etape_differences(a.de, a.a)
    if a.etape == "essai":
        return etape_essai(a.passage, a.photo_avant, a.passage_avant)
    if a.etape == "a_blanc":
        return jouer(a.lot, "a_blanc")
    if a.etape == "ecrire":
        return jouer(a.lot, "vrai", a.empreinte)
    if a.etape == "repetition":
        return etape_repetition(a.lot)
    return etape_routeur(a.poser)


if __name__ == "__main__":
    sys.exit(main())
