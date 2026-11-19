# -*- coding: utf-8 -*-
"""AUDIT V2, FIN DU TEMPS 1 -- MON VERDICT SUR LE GEL. 19/11/2026.

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\audit_v2_gel_contre_moi_2026-11-19.py

⛔ LECTURE SEULE. Il ne lit le gel QU'APRES que mon appariement a ete arrete et commite
  (ce2301e, 19/11 01:07) -- regle d'independance n° 1 : le gel sert a COMPARER, jamais a
  choisir. Le gel est celui de SUPABASE (son maitre), relu le 19/11 par tranches et
  verifie a l'empreinte (.tmp/audit_v2_2026-11-19/gel_supabase_19-11.json).

Pour chaque ligne et chaque role : le gel et moi disons-nous la meme transaction ? Et
quand nous divergeons, LA MEME REGLE (juger_tx de mon apparieur : date au jour pres,
nom d'acquereur, prix) mesure la preuve des DEUX choix -- celui du gel et le mien.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
CK = RACINE / "phase2" / "checks"
_spec = importlib.util.spec_from_file_location("apparieur_v2", CK / "audit_v2_apparier_2026-11-19.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)          # rejoue mon appariement (il reecrit son CSV, a l'identique)

GEL = json.loads((RACINE / ".tmp" / "audit_v2_2026-11-19" / "gel_supabase_19-11.json").read_text(encoding="utf-8"))
MOI = {r["id_unique"]: r for r in csv.DictReader(
    open(RACINE / "notice" / "AUDIT_INDEPENDANT_V2_MON_APPARIEMENT_2026-11-19.csv", encoding="utf-8-sig"), delimiter=";")}
LEDGER = {t["app_affaire_id"]: t for t in A.P["ledger"]}
ROLES = ("offre", "compromis", "vente")

gel_de = defaultdict(lambda: defaultdict(set))       # iu -> role -> {tx}
gel_info = {}
ligne_du_gel = {}
for g in GEL:
    gel_de[g["id_unique"]][g["role"]].add(g["app_affaire_id"])
    gel_info[(g["id_unique"], g["app_affaire_id"])] = g
    ligne_du_gel[g["app_affaire_id"]] = g["id_unique"]
mes_lignes = {}
for iu, r in MOI.items():
    for k in ROLES:
        if r[k]:
            mes_lignes[int(r[k])] = iu


def preuve(iu, tid):
    """La preuve d'une transaction pour une ligne, par MA regle (juger_tx)."""
    if tid is None:
        return None, ""
    if tid in A.C5:
        return None, "creee par C5 (hors candidats)"
    t = A.TX.get(tid)
    L = A.LIGNE_DE.get(iu)
    if not t or not L:
        return None, "inconnue"
    sc, pr = A.juger_tx(L, t)
    return sc, ", ".join(pr)


def annonce_de(tid):
    t = LEDGER.get(tid)
    return str(t["hektor_annonce_id"] or "") if t else ""


def qualifier_gel(iu, tid):
    """⭐ AJOUTE APRES LA PREMIERE LECTURE DES 24 « FAUX » (19/11, ~01:30) -- un desaccord
    n'est pas un verdict. On QUALIFIE la transaction que le gel donne a la ligne :
      croise      je la donne a une AUTRE ligne, dont la preuve SUR ELLE est plus forte
      egalite     je la donne a une autre ligne, a preuve EGALE : mon choix est un tri,
                  pas une preuve (doublons du Sheet) -> question
      contredit   ma regle la REFUSE pour cette ligne : acquereur different sans date,
                  ou date a plus de 400 jours
      non_prouve  ma regle ne la designe pas, sans la contredire (ni date ni nom)
      prouve      ma regle la designe pour cette ligne, mais j'ai choisi autre chose
    ⛔ Le calcul arrete (ce2301e) n'est PAS modifie : seule la lecture du desaccord l'est."""
    if tid in A.C5:
        return "c5"
    sc, pr = preuve(iu, tid)
    autre = mes_lignes.get(tid)
    if autre and autre != iu:
        sc_autre, _ = preuve(autre, tid)
        if sc is not None and sc_autre is not None and sc >= 0 and sc == sc_autre:
            return "egalite(%s)" % autre
        if sc is None or sc < 0 or (sc_autre is not None and sc_autre > sc):
            return "croise(%s)" % autre
        return "egalite(%s)" % autre
    if sc is None:
        return "inconnue"
    if sc < 0:
        if "(veto)" in pr:
            return "contredit_nom"       # un autre acquereur, et aucune date pour le sauver
        if "(!)" in pr:
            return "contredit_date"      # une date a plus de 400 jours
        return "non_prouve"
    # ⭐ la transaction du gel est designee par ma regle : on la COMPARE a mon choix
    L = A.LIGNE_DE.get(iu)
    t = A.TX[tid]
    dl = [x for x in L["d"].values() if x]
    if t["date"] and dl and min(abs((t["date"] - x).days) for x in dl) > 730 \
            and "au jour pres" not in pr and "a " not in pr.split("date")[-1][:6]:
        return "chronologie"             # a plus de deux ans de toutes les dates de la ligne
    if t["k"] == "vente" and L["etat"].lower().startswith("annul"):
        return "vente_sur_annulee"       # le Sheet dit annulee, Hektor porte la vente
    m = MOI[iu][t["k"]]
    if m:
        sm, _ = preuve(iu, int(m))
        if sm is not None and sc == sm:
            return "egal_dans_le_bien"   # deux jumeaux chez Hektor, preuve egale
        if sm is not None and sc > sm:
            return "MIEUX_QUE_MOI"       # ⛔ le gel est mieux prouve : MON erreur
        return "moins_bien"              # le gel est moins bien prouve que mon choix
    return "prouve_sans_rival"


sortie = []
cat = Counter()
detail_cat = Counter()
for L in A.LIGNES:
    iu = L["iu"]
    moi = MOI[iu]
    g = gel_de.get(iu, {})
    roles_out = []
    etats = []
    for k in ROLES:
        gk = g.get(k, set())
        g_c5 = {x for x in gk if x in A.C5}
        g_hk = gk - g_c5
        m = int(moi[k]) if moi[k] else None
        if not gk and m is None:
            continue
        if m is not None and g_hk == {m}:
            e = "identique"
        elif m is None and not g_hk and g_c5:
            e = "C5_seul"                     # le gel tient une creation, Hektor n'a rien
        elif m is not None and not g_hk and g_c5:
            e = "C5_copie"                    # le gel tient une creation, Hektor A la vraie
        elif m is not None and not gk:
            autre = ligne_du_gel.get(m)
            e = "moi_en_plus" + ("(gel->%s)" % autre if autre else "")
        elif m is None and g_hk:
            autres = {mes_lignes.get(x) for x in g_hk} - {None}
            e = "gel_en_plus" + ("(moi->%s)" % ",".join(sorted(autres)) if autres else "")
        else:
            autres = {mes_lignes.get(x) for x in g_hk} - {None}
            e = "divergent" + ("(moi->%s)" % ",".join(sorted(autres)) if autres else "")
        # ⭐ la qualite du desaccord, transaction du gel par transaction du gel
        quals = []
        if e.split("(")[0] in ("gel_en_plus", "divergent"):
            for x in sorted(g_hk):
                q = qualifier_gel(iu, x)
                # l'offre RENEGOCIEE : meme bien, meme acheteur, deux offres -- la question
                # de principe de Frederic (1re offre ou acceptee ?), on ne la tranche pas
                if k == "offre" and m is not None and x in A.TX and m in A.TX and \
                        A.TX[x]["annonce"] == A.TX[m]["annonce"] and \
                        (A.TX[x]["acq"] & A.TX[m]["acq"] or A.TX[x]["acq_ids"] & A.TX[m]["acq_ids"]
                         or A.noms_voisins(A.TX[x]["acq"], A.TX[m]["acq"])):   # MADER / MADERE
                    q = "renegociation"
                quals.append(q)
            e = e + "[" + ",".join(quals) + "]"
        etats.append(e.split("(")[0].split("[")[0])
        for q in quals:
            etats.append("Q:" + q.split("(")[0])
        detail_cat[(k, e.split("(")[0].split("[")[0])] += 1
        pg = [(x, preuve(iu, x)) for x in sorted(gk)]
        pm = preuve(iu, m) if m is not None else (None, "")
        roles_out.append({"role": k, "etat": e, "gel": " ".join(str(x) for x in sorted(gk)),
                          "moi": m or "", "preuve_gel": " ; ".join("%s: %s [%s]" % (x, p[1], p[0]) for x, p in pg),
                          "preuve_moi": "%s [%s]" % (pm[1], pm[0]) if m is not None else ""})
    # ── le verdict de la ligne
    s = set(etats)
    ann_gel = sorted({annonce_de(x) for k in g for x in g[k]} - {""})
    bien = "" if not ann_gel or not moi["annonce"] else ("meme_bien" if moi["annonce"] in ann_gel else "BIEN_DIFFERENT")
    if not g:
        v = "SANS_LIEN_GEL/" + ("A_RATTACHER" if any(moi[k] for k in ROLES)
                                else ("BIEN_SANS_TRANSACTION" if moi["annonce"] else "RIEN"))
    elif not s - {"identique", "C5_seul"}:
        v = "JUSTE"
    elif s <= {"identique", "C5_seul", "moi_en_plus"}:
        v = "INCOMPLET"
    elif bien == "BIEN_DIFFERENT" and ({"Q:MIEUX_QUE_MOI", "Q:prouve_sans_rival"} & s) and \
            any(("au jour pres" in p or "honoraires = commission" in p)
                for r_ in roles_out for p in [r_["preuve_gel"]]):
        # ⭐ (c0a73edd, M2G1Z1K8) un bien DIFFERENT, mais le gel porte une date au jour pres
        #   ou la commission exacte : ce n'est pas une erreur prouvee, c'est une QUESTION
        #   (deux lots, une ligne ; ou le lot voisin). On ne retire rien.
        v = "QUESTION_BIEN"
    elif "Q:MIEUX_QUE_MOI" in s:
        v = "MON_ERREUR"                  # ⛔ le gel est mieux prouve que moi
    elif {"Q:egalite", "Q:renegociation"} & s:
        v = "QUESTION"                    # doublon du Sheet a preuve egale, ou offre renegociee
    elif {"Q:contredit_nom", "Q:contredit_date", "Q:croise", "Q:moins_bien"} & s \
            or (bien == "BIEN_DIFFERENT" and "identique" not in s):
        v = "PARTIEL" if "identique" in s else "FAUX"
    elif s <= {"identique", "C5_seul", "C5_copie", "moi_en_plus"} and "C5_copie" in s:
        v = "C5_COPIE"
    elif s - {"identique", "C5_seul", "C5_copie", "moi_en_plus", "gel_en_plus", "divergent"} \
            <= {"Q:egal_dans_le_bien"} and "Q:egal_dans_le_bien" in s:
        v = "JUSTE_JUMEAU"                # le gel a pris l'autre jumeau : aussi juste que moi
    else:
        v = "NON_PROUVE" if "identique" not in s else "PARTIEL_NON_PROUVE"
    if "C5_copie" in s and v != "C5_COPIE":
        v += "+C5_COPIE"
    cat[v] += 1
    conf = sorted({gel_info[(iu, x)]["confiance"] for k in g for x in g[k]})
    etg = sorted({gel_info[(iu, x)]["etage"] for k in g for x in g[k]})
    sortie.append({"id_unique": iu, "rang": L["rang"], "etat_sheet": L["etat"], "mon_verdict_sur_le_gel": v,
                   "bien": bien, "annonce_gel": " ".join(ann_gel), "annonce_moi": moi["annonce"],
                   "ma_certitude": moi["certitude"], "mes_drapeaux": moi["drapeaux"],
                   "confiance_gel": " ".join(conf), "etage_gel": " / ".join(etg)[:120],
                   "roles": " || ".join("%s=%s gel[%s] moi[%s]" % (r["role"], r["etat"], r["gel"], r["moi"]) for r in roles_out),
                   "preuve_gel": " || ".join("%s: %s" % (r["role"], r["preuve_gel"]) for r in roles_out if r["etat"] != "identique"),
                   "preuve_moi": " || ".join("%s: %s" % (r["role"], r["preuve_moi"]) for r in roles_out if r["etat"] != "identique")})

out = RACINE / "notice" / "AUDIT_INDEPENDANT_V2_GEL_CONTRE_MOI_2026-11-19.csv"
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sortie[0].keys()), delimiter=";")
    w.writeheader()
    w.writerows(sortie)
print("\nMON VERDICT SUR LE GEL (%d lignes) :" % len(sortie))
for k, n in sorted(cat.items(), key=lambda x: -x[1]):
    print("  %-40s %5d" % (k, n))
print("\npar role :")
for (k, e), n in sorted(detail_cat.items()):
    print("  %-10s %-14s %5d" % (k, e, n))
print("\nla qualite des desaccords (transaction du gel par transaction du gel) :")
qq = Counter()
for s_ in sortie:
    for part in s_["roles"].split(" || "):
        if "[" in part.split(" gel[")[0]:
            for q in part.split(" gel[")[0].split("[", 1)[1].rstrip("]").split(","):
                qq[q.split("(")[0]] += 1
for k, n in sorted(qq.items(), key=lambda x: -x[1]):
    print("  %-16s %4d" % (k, n))
print("\nbien different :", sum(1 for s in sortie if s["bien"] == "BIEN_DIFFERENT"))
print("ecrit :", out)
