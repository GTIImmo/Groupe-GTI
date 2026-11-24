"""SON ④ DU 24/11 (« MOT_DU_24_11_MES_QUATRE_REPONSES ») -- QUE PORTE `commission_agence`, ET POURQUOI ELLE NE TOMBE PAS
SUR LA COLONNE « Commission TTC » DANS 453 CAS ? -- LECTURE SEULE. ⛔ Ce sujet nourrit la paie : aucune ecriture, aucune
correction, aucun recalcul. On NOMME.

SA METHODE : ① jamais conclure sur quelques cas -- la distribution COMPLETE ; ② tout temoin positif avec son temoin
INVERSE, mesure sur le groupe sain ; ③ ⛔ les EPOQUES : une colonne n'explique rien si elle n'est pas remplie de la meme
facon a toutes les annees ; ④ la SOURCE avant la statistique ; ⑤ rendre ce qui reste INEXPLIQUE, ligne par ligne.
SA SEULE DONNEE : « IL N'Y A EU AUCUN CHANGEMENT SUR LES HONORAIRES » -- une explication « la regle de paie a change » ne
tient pas.

LES SOURCES LUES (toutes en lecture) :
  data/hektor.sqlite, hektor_vente.raw_json   -- la vente TELLE QUE L'API DE HEKTOR LA REND : honoraires (TTC),
                                                 honorairesEntree / honorairesSortie, commissionAgence
  phase2/phase2.sqlite, app_affaire_console   -- le formulaire de la vente LU DANS LA CONSOLE de Hektor : ses
                                                 intervenants (entree / sortie, personne, montant HT de sa part)
  phase2/phase2.sqlite, app_affaire_repartition -- notre repartition (origine classeur_reconstitue = le Sheet, 13/11)
  l'image du 23/11 08:02 et le passage P du socle -- le Sheet (Commission TTC, Negociateurs, Pourcentages, Charge,
                                                 Agence) et la vente que le protocole donne a chaque ligne tranchee

USAGE : python -u -X utf8 phase2/checks/protocole_commission_agence_ce_qu_elle_porte_2026-11-24.py --passage P [--csv]
"""
import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402
import rapatrier_repartition_classeur as RR  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--passage", type=int, required=True)
ap.add_argument("--csv", action="store_true")
arg = ap.parse_args()


def dire(s=""):
    print(s, flush=True)


def f(x):
    try:
        return float(str(x).replace(",", ".").replace(" ", ""))
    except (TypeError, ValueError):
        return None


PARTS = ((1.0, "TOUT"), (0.75, "3/4"), (0.5, "MOITIE"), (1 / 3, "1/3"), (0.25, "QUART"), (2 / 3, "2/3"),
         (0.125, "1/8"), (0.375, "3/8"), (0.625, "5/8"))


def part(ca, hon):
    """La part du HT que commissionAgence represente : ca x 1,2 / honoraires TTC, rangee sur les fractions simples."""
    if not ca or not hon:
        return "VIDE" if not ca else "HON VIDE"
    s = ca * 1.2 / hon
    for v, nom in PARTS:
        if abs(s - v) <= 0.004:
            return nom
    return "AUTRE (%.3f)" % s


def epoque(an):
    if not an or an < "2015":
        return "1 avant 2015"
    if an < "2017":
        return "2 2015-2016"
    if an < "2025":
        return "3 2017-2024"
    return "4 " + an


def tableau(titre, c, cles=None):
    dire(titre)
    for k in sorted(cles or {x[0] for x in c}):
        lig = {x[1]: n for x, n in c.items() if x[0] == k}
        n = sum(lig.values())
        dire("      %-34s n=%5d  %s" % (k, n, " . ".join("%s %d (%.0f %%)" % (p_, v, 100 * v / n) for p_, v in
                                                     sorted(lig.items(), key=lambda kv: -kv[1]))))


h = sqlite3.connect("file:C:/Hektor/Projet/data/hektor.sqlite?mode=ro", uri=True)
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
HV = {str(v): json.loads(rj) for v, rj in h.execute("select hektor_vente_id, raw_json from hektor_vente")}
dire("QUE PORTE commission_agence ? -- passage %d, %d ventes dans le miroir de Hektor" % (arg.passage, len(HV)))

# ── ④ LA SOURCE ───────────────────────────────────────────────────────────────────────────────────────────────────────
dire()
dire("④ LA SOURCE : commissionAgence de l'API de Hektor (la vente), recopiee TELLE QUELLE par normalize_source.upsert_ventes"
     " -> hektor_vente.commission_agence -> app_affaire_ledger.commission_agence (affaire_ledger.py, « commission_agence "
     "AS commission »). Classe C : Hektor la calcule, personne ne l'ecrit chez nous.")
cles = Counter()
for d in HV.values():
    for k_ in ("commissionAgence", "honoraires", "honorairesEntree", "honorairesSortie", "honorairesHT", "partAdmin"):
        if f(d.get(k_)):
            cles[k_] += 1
dire("   champs remplis (> 0) : " + " . ".join("%s %d" % kv for kv in cles.most_common()))
eg = sum(1 for d in HV.values() if f(d.get("honoraires")) is not None and abs((f(d.get("honoraires")) or 0) - (
    (f(d.get("honorairesEntree")) or 0) + (f(d.get("honorairesSortie")) or 0))) <= 1)
dire("   honoraires = honorairesEntree + honorairesSortie : %d / %d" % (eg, len(HV)))

# ── ① LA DISTRIBUTION COMPLETE, PAR EPOQUE (toutes les ventes du miroir) ──────────────────────────────────────────────
c1 = Counter()
for d in HV.values():
    c1[(epoque((d.get("date") or "")[:4]), part(f(d.get("commissionAgence")), f(d.get("honoraires"))))] += 1
dire()
tableau("① LA PART DU HT QUE PORTE commissionAgence (ca x 1,2 / honoraires), TOUTES LES VENTES, PAR EPOQUE :", c1)
c1b = Counter()
for d in HV.values():
    an = (d.get("date") or "")[:4]
    if an >= "2024":
        c1b[(an + "-" + (d.get("date") or "")[5:7], part(f(d.get("commissionAgence")), f(d.get("honoraires"))))] += 1
tableau("   ... et MOIS PAR MOIS depuis 2024 (ou la bascule commence-t-elle ?) :", c1b)

# ── LE FORMULAIRE DE HEKTOR LUI-MEME (la console) : ses intervenants contre son propre commissionAgence ──────────────
vid_of = {a: str(v) for a, v in loc.execute("select app_affaire_id, hektor_affaire_id from app_affaire_ledger "
                                            "where kind='vente'")}
FORM = {}
for a, ij in loc.execute("select app_affaire_id, intervenants_json from app_affaire_console where kind='vente' "
                         "and intervenants_json not in ('','[]')"):
    FORM[vid_of.get(a)] = json.loads(ij)
c2 = Counter()
for vid, g in FORM.items():
    d = HV.get(vid)
    if not d or not f(d.get("commissionAgence")):
        continue
    ca = f(d.get("commissionAgence"))
    pers, side = defaultdict(float), defaultdict(float)
    for x in g:
        pers[x.get("id")] += f(x.get("montant")) or 0
        side[x.get("sens")] += f(x.get("montant")) or 0
    tot = sum(pers.values())
    if abs(tot - ca) <= 1.5:
        k_ = "= la SOMME des parts du formulaire"
    elif any(abs(v - ca) <= 1.5 for v in side.values()):
        k_ = "= UN COTE du formulaire (entree OU sortie)"
    elif any(abs(v - ca) <= 1.5 for v in pers.values()):
        k_ = "= la part d'UNE personne"
    elif abs(tot / 4 - ca) <= 1.5:
        k_ = "= le QUART de la somme"
    else:
        k_ = "autre"
    c2[(epoque((d.get("date") or "")[:4]) + (" (%d pers.)" % len(pers)), k_)] += 1
dire()
dire("   LE FORMULAIRE DE HEKTOR (console) : %d ventes lues ; personnes distinctes par vente : %s" % (
    len(FORM), dict(Counter(len({x.get("id") for x in g}) for g in FORM.values()))))
tableau("   commissionAgence CONTRE LES PARTS DE SON PROPRE FORMULAIRE, par epoque :", c2)

# ── LE SHEET : les lignes tranchees qui tiennent UNE vente ────────────────────────────────────────────────────────────
con = P.socle()
image, = con.execute("select image from passage where id=?", (arg.passage,)).fetchone()
VV = {i: json.loads(ps) for i, v, ps in con.execute("select id_unique, verdict, pieces from verdict where passage=?",
                                                     (arg.passage,)) if v == "TRANCHEE" and ps}
con.close()
I = P.Image(P.IMAGES / image)
D, PI = I.D, I.pieces
REP = defaultdict(list)
for c_, cote, u, pct, o in loc.execute("select app_chaine_id, cote, hektor_user_id, pourcentage, origine "
                                       "from app_affaire_repartition"):
    REP[int(c_)].append((cote, str(u), pct, o))


# ⛔ SA REGLE (06/11) : l'identite d'un ADMIN n'est jamais ecrite sur un document -- reperee par son NUMERO (lue a
#   l'execution dans l'annuaire, jamais ecrite ici), son nom est masque partout ou il sortirait
COMPTES_ADMIN = {"46"}
_MOTS_ADMIN = set()
for nom_, in loc.execute("select nom from app_hektor_negotiator_agency_directory where cast(hektor_user_id as text) in "
                         "(%s)" % ",".join("'%s'" % x for x in COMPTES_ADMIN)):
    _MOTS_ADMIN |= set(RR.mots_du_nom(nom_ or ""))


def masque(n_):
    return "[compte admin]" if _MOTS_ADMIN and set(RR.mots_du_nom(n_ or "")) & _MOTS_ADMIN else n_


def gens_du_sheet(i):
    """Les PERSONNES du Sheet et leur part (le NOM dit le partage : deux fois le meme nom = une seule personne)."""
    out = defaultdict(float)
    for k_ in (1, 2, 3):
        n_ = D.case(i, "Négociateur %d" % k_).strip()
        if n_:
            out[masque(" ".join(sorted(RR.mots_du_nom(n_))))] += K.nombre(D.case(i, "Pourcentage %d" % k_)) or 0
    return dict(out)


LIG = []
for i, ps in VV.items():
    ventes = [a for a in ps if a in PI and PI[a]["kind"] == "vente" and I.nature.get(a) == PC.VRAIE]
    com = K.nombre(D.case(i, "Commission TTC"))
    if len(ventes) != 1 or not com:
        continue
    a = ventes[0]
    d = HV.get(str(PI[a]["hektor_affaire_id"]))
    if not d:
        continue
    ca, hon = f(d.get("commissionAgence")), f(d.get("honoraires"))
    g = gens_du_sheet(i)
    rows = REP.get(int(PI[a]["app_chaine_id"]), [])
    LIG.append({"i": i, "a": a, "vente": str(PI[a]["hektor_affaire_id"]), "an": (d.get("date") or "")[:4],
                "mois": (d.get("date") or "")[:7], "com": com, "ca": ca, "hon": hon, "part": part(ca, com),
                "part_hon": part(ca, hon), "gens": g, "n_gens": len(g),
                "charge": D.case(i, "Charge Commission").strip(), "agence": D.case(i, "Agence").strip(),
                "etat": D.case(i, "Etat Actuel").strip(), "n1": masque(D.case(i, "Négociateur 1").strip()),
                "agence_hektor": str((d.get("annonce") or {}).get("agence")),
                "mandat_type": str((d.get("mandat") or {}).get("type") or "-"),
                "hs": f(d.get("honorairesSortie")) or 0,
                "form_pers": len({x.get("id") for x in FORM.get(str(PI[a]["hektor_affaire_id"]), [])}),
                "ca_montant": any(f(x.get("ca_montant")) for x in FORM.get(str(PI[a]["hektor_affaire_id"]), [])),
                "rep_pers": len({u for _c, u, _p, _o in rows}),
                "rep_origine": ",".join(sorted({o for *_x, o in rows})) or "aucune"})
dire()
dire("LE SHEET : %d lignes tranchees (passage %d) tiennent UNE vente et une Commission TTC" % (len(LIG), arg.passage))
c3 = Counter((epoque(x["an"]), x["part"]) for x in LIG)
tableau("   LA PART : commissionAgence x 1,2 / « Commission TTC », PAR EPOQUE (mes 453 = la MOITIE) :", c3)
dire("      temoin : « Commission TTC » = honoraires de Hektor (TTC) sur %d / %d" % (
    sum(1 for x in LIG if x["hon"] and abs(x["hon"] - x["com"]) <= 1), len(LIG)))

# ── ② ③ LE NOMBRE DE PERSONNES DU SHEET (par le NOM) : positif ET inverse, par epoque ───────────────────────────────
c4 = Counter((epoque(x["an"]) + " / %d personne(s) au Sheet" % x["n_gens"], x["part"]) for x in LIG)
tableau("② LA PART SELON LE NOMBRE DE PERSONNES DU SHEET (le nom dit le partage) :", c4)
# l'epoque de la colonne elle-meme (sa regle ③) : le partage au Sheet est-il ecrit de la meme facon a toutes les annees ?
c4b = Counter((epoque(x["an"]), "%d pers." % x["n_gens"]) for x in LIG)
tableau("   ③ LA COLONNE ELLE-MEME, PAR EPOQUE (le Sheet ecrit-il le partage de la meme facon chaque annee ?) :", c4b)

# LA PART D'UNE PERSONNE : ca x 1,2 / TTC = la part (au Sheet) d'une de ses personnes ?
c5 = Counter()
for x in LIG:
    s = x["ca"] * 1.2 / x["com"] if x["ca"] else None
    if s is None:
        k_ = "commissionAgence vide"
    elif abs(s - 1) <= 0.004:
        k_ = "= TOUT"
    else:
        parts_ = {n_: p_ / 100 for n_, p_ in x["gens"].items()}
        premier = masque(" ".join(sorted(RR.mots_du_nom(x["n1"]))))
        if premier in parts_ and abs(parts_[premier] - s) <= 0.004:
            k_ = "= la part du NEGOCIATEUR 1"
        elif any(abs(v - s) <= 0.004 for v in parts_.values()):
            k_ = "= la part d'un AUTRE negociateur du Sheet"
        else:
            k_ = "⛔ INEXPLIQUE par le Sheet"
    x["explique"] = k_
    c5[(epoque(x["an"]) + " / %d pers." % x["n_gens"], k_)] += 1
tableau("   LA PART EST-ELLE CELLE D'UNE PERSONNE DU SHEET ? (la part de chaque nom, ses pourcentages additionnes) :", c5)

# ── ⑤ LES AFFAIRES ENTIERES (UNE personne au Sheet) : la MOITIE contre le TOUT, signe par signe, par epoque ─────────
dire()
dire("⑤ LES AFFAIRES ENTIERES AU SHEET (une seule personne, 100 %%) : ce qui distingue la MOITIE du TOUT -- chaque signe "
     "mesure DES DEUX COTES (positif = la moitie, inverse = le tout), epoque par epoque")
SIGNES = (("Charge Commission remplie", lambda x: bool(x["charge"])),
          ("Charge = Acquereur", lambda x: x["charge"].lower().startswith("acq")),
          ("honorairesSortie > 0 (Hektor)", lambda x: x["hs"] > 0),
          ("mandat SIMPLE (Hektor)", lambda x: x["mandat_type"].upper() == "SIMPLE"),
          ("formulaire : 2 personnes", lambda x: x["form_pers"] > 1),
          ("formulaire : ca_montant rempli", lambda x: x["ca_montant"]),
          ("repartition : 2 personnes", lambda x: x["rep_pers"] > 1),
          ("Etat = Vente reglee", lambda x: x["etat"] == "Vente réglée"))
for ep in sorted({epoque(x["an"]) for x in LIG}):
    G = [x for x in LIG if epoque(x["an"]) == ep and x["n_gens"] == 1 and x["part"] in ("TOUT", "MOITIE")]
    M = [x for x in G if x["part"] == "MOITIE"]
    T = [x for x in G if x["part"] == "TOUT"]
    if not M or not T:
        dire("   %s : moitie %d, tout %d -- pas de comparaison possible" % (ep, len(M), len(T)))
        continue
    dire("   %s : MOITIE %d . TOUT %d" % (ep, len(M), len(T)))
    for nom, fn in SIGNES:
        a_, b_ = sum(1 for x in M if fn(x)), sum(1 for x in T if fn(x))
        dire("      %-32s moitie %4d / %-4d (%5.1f %%)   tout %4d / %-4d (%5.1f %%)" % (
            nom, a_, len(M), 100 * a_ / len(M), b_, len(T), 100 * b_ / len(T)))
    for nom, cle in (("agence du Sheet", "agence"), ("negociateur 1", "n1"), ("agence Hektor", "agence_hektor")):
        cm, ct = Counter(x[cle] for x in M), Counter(x[cle] for x in T)
        dire("      par %s (les 6 premieres de la moitie, et leur taux de moitie dans l'epoque) : %s" % (
            nom, " . ".join("%s %d/%d" % (k_, v, v + ct.get(k_, 0)) for k_, v in cm.most_common(6))))

# ── LA LISTE DE CE QUI RESTE INEXPLIQUE ───────────────────────────────────────────────────────────────────────────────
inexp = [x for x in LIG if x["explique"] == "⛔ INEXPLIQUE par le Sheet"]
dire()
dire("CE QUI RESTE INEXPLIQUE PAR LE SHEET : %d lignes (par epoque : %s)" % (
    len(inexp), dict(sorted(Counter(epoque(x["an"]) for x in inexp).items()))))
if arg.csv:
    out = P.NOTICE / ("PROTOCOLE_COMMISSION_AGENCE_CE_QU_ELLE_PORTE_PASSAGE_%d_2026-11-24.csv" % arg.passage)
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_unique", "piece_vente", "vente_hektor", "date_vente", "commission_ttc_sheet",
                    "commission_agence_hektor", "honoraires_hektor_ttc", "part_du_ht", "personnes_au_sheet",
                    "parts_au_sheet", "explication", "charge", "agence", "etat", "personnes_au_formulaire_hektor",
                    "repartition_origine"])
        for x in sorted(LIG, key=lambda x: (x["explique"] != "⛔ INEXPLIQUE par le Sheet", x["an"], x["i"])):
            w.writerow([x["i"], x["a"], x["vente"], x["mois"], x["com"], x["ca"], x["hon"], x["part"], x["n_gens"],
                        " | ".join("%s %g" % kv for kv in x["gens"].items()), x["explique"], x["charge"], x["agence"],
                        x["etat"], x["form_pers"], x["rep_origine"]])
    dire("-> %s" % out)
