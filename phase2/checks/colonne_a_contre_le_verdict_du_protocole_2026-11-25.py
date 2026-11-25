#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""L'ECRIVAIN DE LA COLONNE A CONTRE LE VERDICT DU PROTOCOLE (son mot du 25/11) -- LECTURE SEULE.

    python -X utf8 -u phase2\checks\colonne_a_contre_le_verdict_du_protocole_2026-11-25.py

SON MOT : « POURQUOI TON ECRIVAIN N'ACCEPTE-T-IL PAS LE VERDICT DU PROTOCOLE ? [...] qu'est-ce qu'il verifie que le
protocole ne verifie pas [...] Soit il applique un critere PERIME [...] MESURE-LE ET REPONDS-MOI, CAS PAR CAS. »

Les deux juges, lus tels qu'ils sont :
  · LE PROTOCOLE : le socle (chantier_classeur_q6_cache/protocole/socle.sqlite), table verdict, passage 81 (image du
    25/11 07:26, celle de la vague) -- TRANCHEE avec SES pieces, SES preuves et l'etiquette a l'arrivee, ou ATTENTE ;
  · L'ECRIVAIN : le classement neuf (CLASSEMENT_COLONNE_A_APRES_LA_VAGUE_2026-11-25.csv) et ce que son juge relit a
    l'ecriture : LE GEL (app_classeur_lien) et le registre d'aujourd'hui (Supabase).

⛔ N'ECRIT RIEN, ni dans le Sheet ni en base : il lit, et ecrit un CSV dans notice/.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402

NOTICE = RACINE / "notice"
SOCLE = P.DOSSIER / "socle.sqlite"
PASSAGE = 81
CLASSEMENT = NOTICE / "CLASSEMENT_COLONNE_A_APRES_LA_VAGUE_2026-11-25.csv"
VAGUE1A = NOTICE / "CLASSEUR_VAGUE_vague1a_2026-11-25.csv"
VERDICTS_AUDIT = NOTICE / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv"
OPERATIONS_V2 = NOTICE / "AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv"
PATCH_V2 = RACINE / "supabase" / "patch_correction_gel_audit_v2_2026-11-19.sql"
SORTIE = NOTICE / "COLONNE_A_LES_ECARTEES_CONTRE_LE_VERDICT_DU_PROTOCOLE_2026-11-25.csv"


def nombres(t: str) -> set[int]:
    return {int(x) for x in re.findall(r"\b(\d{3,7})\b", t or "")}


def main() -> int:
    C = {}
    with CLASSEMENT.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            C[r["id_unique"]] = r
    con = sqlite3.connect("file:%s?mode=ro" % SOCLE.as_posix(), uri=True)
    image = con.execute("select image from passage where id=?", (PASSAGE,)).fetchone()[0]
    V = {}
    for i, n, v, e, ps, pr, m, mt in con.execute(
            "select id_unique, num, verdict, etiquette, pieces, preuves, motif, motif_texte from verdict where passage=?",
            (PASSAGE,)):
        V[i] = {"verdict": v, "etiquette": e, "pieces": json.loads(ps) if ps else [],
                "preuves": json.loads(pr) if pr else [], "motif": m, "motif_texte": mt}
    con.close()
    print("protocole, passage %d (image %s) : %s" % (PASSAGE, image, dict(Counter(v["verdict"] for v in V.values()))))

    cn, cu = P.pooler()
    cu.execute("select id_unique, app_affaire_id, confiance from public.app_classeur_lien")
    gel, conf_de = defaultdict(set), {}
    for i, a, c in cu.fetchall():
        gel[i].add(int(a))
        conf_de[(i, int(a))] = c
    cu.execute("select app_affaire_id, app_dossier_uuid::text, app_dossier_numero, kind, state, transaction_origine, "
               "hektor_affaire_id, coalesce(vente_reglee_app, '') from public.app_affaire_ledger")
    reg = {}
    for a, u, n, k, s, o, h, vr in cu.fetchall():
        reg[int(a)] = {"uuid": u, "numero": n, "genre": k, "etat": s, "copie": PC.est_copie(int(a), o, h), "reglee": vr}
    cn.rollback()
    cn.close()
    sheet = json.loads((P.IMAGES / image / "sheet.json").read_text(encoding="utf-8"))
    ent = sheet["entete"]
    kE, kR = ent.index("Etat Actuel"), ent.index("Vente Réglée")
    etat = {i: v[0]["row"][kE].strip() for i, v in sheet["par_id"].items()}
    reglee_sheet = {i: v[0]["row"][kR].strip() for i, v in sheet["par_id"].items()}
    col_a = {}
    with VAGUE1A.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            col_a[r["id_unique"]] = r["etiquette_prevue"]

    def eff(ts):
        connues = [a for a in ts if a in reg]
        hk = [a for a in connues if not reg[a]["copie"]]
        return hk or connues

    def u_de(ts) -> set:
        return {reg[a]["uuid"] for a in eff(ts)}

    # ── L'ETIQUETTE A L'ARRIVEE : une etiquette existante, ou « NEUVE:<piece> » (le protocole ne pouvait pas connaitre
    #    l'uuid que la vague donnerait) -> l'etiquette d'AUJOURD'HUI de cette piece-la
    tr = {i: v for i, v in V.items() if v["verdict"] == "TRANCHEE"}
    for v in tr.values():
        e = v["etiquette"] or ""
        v["neuve"] = e.startswith("NEUVE:")
        v["arrivee"] = (reg.get(int(e.split(":")[1]), {}).get("uuid") if v["neuve"] else e)
    print("etiquettes a l'arrivee : %d existantes, %d NEUVES (resolues par leur piece : %d)" % (
        sum(1 for v in tr.values() if not v["neuve"]), sum(1 for v in tr.values() if v["neuve"]),
        sum(1 for v in tr.values() if v["neuve"] and v["arrivee"])))
    # ── TEMOIN 1 : l'etiquette a l'arrivee du protocole = l'etiquette d'AUJOURD'HUI de SES pieces (la vague l'a realisee)
    tenue = {i for i, v in tr.items() if u_de(v["pieces"]) == {v["arrivee"]}}
    pas_tenue = sorted(set(tr) - tenue)
    print("TEMOIN 1 : etiquette a l'arrivee = etiquette d'aujourd'hui de ses pieces : %d / %d ; autres : %d %s" % (
        len(tenue), len(tr), len(pas_tenue), [(i, tr[i]["etiquette"][:13], sorted(u_de(tr[i]["pieces"]), key=str))
                                             for i in pas_tenue[:5]]))
    # ── TEMOIN 2 : sur les lignes que l'ECRIVAIN ecrit (ou a ecrites), son etiquette = celle du protocole ?
    ecrit = [i for i, r in C.items() if r["case_25_11"] in ("VAGUE_1", "A_DEJA_REMPLIE")]
    w_de = {i: u_de(gel.get(i, set())) for i in ecrit}
    accord = [i for i in ecrit if i in tr and w_de[i] == {tr[i]["arrivee"]}]
    desaccord = [i for i in ecrit if i in tr and w_de[i] != {tr[i]["arrivee"]}]
    non_tr = [i for i in ecrit if i not in tr]
    print("TEMOIN 2 : lignes que l'ecrivain ecrit ou a ecrites : %d ; meme etiquette que le protocole : %d ; "
          "DESACCORD : %d %s ; que le protocole n'a PAS tranchees : %d %s" % (
              len(ecrit), len(accord), len(desaccord), desaccord[:10], len(non_tr),
              [(i, C[i]["case_25_11"], V.get(i, {}).get("motif")) for i in non_tr]))
    v1b = set()
    f1b = NOTICE / "CLASSEUR_VAGUE_vague1b_2026-11-25.csv"
    if f1b.exists():
        with f1b.open(encoding="utf-8-sig") as f:
            v1b = {r["id_unique"] for r in csv.DictReader(f, delimiter=";")}
    for i in desaccord[:12]:
        print("      DESACCORD %s (%s) : l'ecrivain %s (gel %s) / le protocole %s (pieces %s)" % (
            i, C[i]["case_25_11"], sorted(w_de[i], key=str), sorted(gel.get(i, set())), tr[i]["arrivee"],
            tr[i]["pieces"]))
    print("   parmi les 50 ECRITES : desaccord %d %s, non tranchees %d %s ; parmi la vague1b : desaccord %d %s, non "
          "tranchees %d %s" % (sum(1 for i in desaccord if i in col_a), [i for i in desaccord if i in col_a],
                               sum(1 for i in non_tr if i in col_a), [i for i in non_tr if i in col_a],
                               sum(1 for i in desaccord if i in v1b), [i for i in desaccord if i in v1b],
                               sum(1 for i in non_tr if i in v1b), [i for i in non_tr if i in v1b]))
    # ── le gel contre les pieces du protocole
    meme_gel = {i for i, v in tr.items() if set(v["pieces"]) == gel.get(i, set())}
    print("gel d'aujourd'hui = pieces du protocole : %d / %d tranchees ; differents : %d" % (
        len(meme_gel), len(tr), len(tr) - len(meme_gel)))

    # ── les lignes de chaque etiquette, PAR LE PROTOCOLE (ses pieces) -- pour « partagee » lue a sa facon
    lignes_u = defaultdict(set)
    for i, v in tr.items():
        for u in u_de(v["pieces"]):
            lignes_u[u].add(i)
    for i, r in C.items():               # les lignes NON tranchees gardent leur gel
        if i not in tr:
            for u in u_de(gel.get(i, set())):
                lignes_u[u].add(i)
    a_porte = defaultdict(list)
    for i, u in col_a.items():
        a_porte[u].append(i)

    # ── l'audit du 18/11, les operations V2, la file d'attente du 19/11
    audit = {}
    with VERDICTS_AUDIT.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            audit[r["id_unique"]] = r
    ops = defaultdict(list)
    with OPERATIONS_V2.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            ops[r["id_unique"]].append(r)
    texte = PATCH_V2.read_text(encoding="utf-8")
    b3 = texte.split("-- ── ③ RETIRER")[1].split("-- ── ④ AJOUTER")[0]
    b4 = texte.split("-- ── ④ AJOUTER")[1].split("-- ── ⑤ LE CONTROLE")[0]
    touchees_v2 = {i for i, _a in re.findall(r"\('([^']+)',\s*(\d+),\s*'\w+'\)", b3)} | \
        {i for _a, _c, i in re.findall(r"\(\d+,\s*(\d+),\s*'\w+',\s*'([^']+)',.*?'([^']+)'\)", b4)}

    def pourquoi_attente(i):
        r = audit.get(i)
        out = []
        if r and r["question_pour_frederic"].strip():
            # le texte de la question n'est PAS recopie (il peut nommer des personnes) : il est dans le fichier de l'audit
            out.append("une question du 18/11 (son texte : %s, colonne question_pour_frederic)" % VERDICTS_AUDIT.name)
        if r and "INCERTAIN" in (r["verdict"] + r["correction_contre_expert"]).upper():
            out.append("audit INCERTAIN")
        for o in ops.get(i, []):
            if o["decision_v2"] != "GARDEE":
                out.append("V2 %s %s -> %s" % (o["operation"], o["de"] or o["vers"], o["decision_v2"]))
        if i == "SHN6RKDI":
            out.append("SHN6RKDI (ajoutee a la main le 19/11)")
        return " ; ".join(out)

    def attendu_audit(i):
        r = audit.get(i)
        if not r:
            return None
        g = set()
        for morceau in r["liens"].split("|"):
            if "GARDER" in morceau:
                g |= nombres(morceau)
        return g | nombres(r["a_rattacher"])

    # ── LES ECARTEES, une par une
    ec = [i for i, r in C.items() if r["case_25_11"] not in ("VAGUE_1", "A_DEJA_REMPLIE")]
    lignes = []
    for i in sorted(ec, key=lambda x: int(C[x]["ligne_au_25_11"])):
        r, v = C[i], V.get(i, {})
        t = v.get("verdict") == "TRANCHEE"
        pp = v.get("pieces", []) if t else []
        up = u_de(pp) if t else set()
        g = sorted(gel.get(i, set()))
        # LIRE LA LIGNE COMME LE PROTOCOLE : ses pieces, une seule etiquette, la sienne, aucune autre ligne dessus
        if not t:
            lisible = "NON : pas tranchee (%s)" % (v.get("motif") or "absente du passage")
        elif not pp:
            lisible = "NON : tranchee sans piece"
        elif len(up) != 1:
            lisible = "NON : ses pieces sont dans %d dossiers" % len(up)
        elif up != {v["arrivee"]}:
            lisible = "NON : l'etiquette d'aujourd'hui n'est pas celle de l'arrivee"
        elif lignes_u[next(iter(up))] - {i}:
            lisible = "NON : son dossier porte aussi %s" % sorted(lignes_u[next(iter(up))] - {i})
        elif [j for j in a_porte.get(next(iter(up)), []) if j != i]:
            lisible = "NON : son etiquette est deja en A sur %s" % a_porte[next(iter(up))]
        else:
            lisible = "OUI"
        conf = sorted({conf_de[(i, a)] for a in g})
        aa = attendu_audit(i)
        tous = set(pp) | set(g)
        vr = sorted({str(a) for a in tous if a in reg and reg[a]["genre"] == "vente" and reg[a]["reglee"]})
        preuves = " || ".join(v.get("preuves", [])) if t else (v.get("motif_texte") or "")
        regles = sorted(set(re.findall(r"REGLE (R\d+[a-z]?)", preuves)))
        lignes.append({
            "id_unique": i, "ligne": r["ligne_au_25_11"], "case_ecrivain": r["case_25_11"],
            "decision_du_20_11": r["decision_du_20_11"], "verdict_protocole": v.get("verdict", "ABSENTE"),
            "motif_protocole": v.get("motif") or "", "etat_au_sheet": etat.get(i, ""),
            "vente_reglee_sheet": reglee_sheet.get(i, ""), "vente_reglee_registre": " ".join(vr),
            "pieces_protocole": " ".join(map(str, pp)), "gel_aujourdhui": " ".join(map(str, g)),
            "gel_egal_protocole": "OUI" if t and set(pp) == set(g) else ("" if not t else "NON"),
            "confiance_du_gel": " ".join(conf),
            "dossiers_protocole": " ".join(sorted({str(reg[a]["numero"]) for a in eff(pp)})) if t else "",
            "dossiers_gel": " ".join(sorted({str(reg[a]["numero"]) for a in eff(g)})),
            "etiquette_arrivee": v.get("etiquette") or "", "etiquette_arrivee_aujourdhui": v.get("arrivee") or "", "lisible_par_le_protocole": lisible,
            "regles_du_protocole": " ".join(regles), "preuves_du_protocole": preuves[:900],
            "audit_18_11": audit[i]["verdict"] if i in audit else "",
            "audit_attendu": " ".join(map(str, sorted(aa))) if aa is not None else "",
            "gel_egal_audit": ("OUI" if aa is not None and aa == set(g) else "NON") if i in audit else "",
            "protocole_egal_audit": ("OUI" if aa is not None and aa == set(pp) else "NON") if i in audit and t else "",
            "touchee_par_v2": "OUI" if i in touchees_v2 else "",
            "pourquoi_en_attente_19_11": pourquoi_attente(i) if r["case_25_11"] == "EN_ATTENTE" else ""})
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter=";")
        w.writeheader()
        w.writerows(lignes)

    L = {x["id_unique"]: x for x in lignes}
    trc = [x for x in lignes if x["verdict_protocole"] == "TRANCHEE"]
    print("\nLES %d ECARTEES : %d tranchees par le protocole, %d non" % (len(lignes), len(trc), len(lignes) - len(trc)))
    for case in ("GEL_SEUL", "LIEN_A_VALIDER", "AUDIT_NON_JUSTE", "SANS_LIEN", "EN_ATTENTE", "PLUSIEURS_DOSSIERS",
                 "ETIQUETTE_PARTAGEE"):
        xs = [x for x in trc if x["case_ecrivain"] == case]
        lis = Counter(x["lisible_par_le_protocole"].split(" : ")[0] + (" : " + x["lisible_par_le_protocole"].split(" : ")[1].split(" ")[0] if " : " in x["lisible_par_le_protocole"] else "") for x in xs)
        print("\n  %s : %d tranchees" % (case, len(xs)))
        print("     lisible par le protocole (ses pieces, une etiquette, la sienne, seule) : %s" % dict(lis))
        print("     gel = pieces du protocole : %s ; regles du protocole : %s" % (
            dict(Counter(x["gel_egal_protocole"] for x in xs)),
            dict(Counter(r_ for x in xs for r_ in (x["regles_du_protocole"].split() or ["(aucune Rnn nommee)"])))))
        print("     decisions du 20/11 : %s ; ventes reglees (Sheet) : %d ; (registre) : %d" % (
            dict(Counter(x["decision_du_20_11"] for x in xs if x["decision_du_20_11"])),
            sum(1 for x in xs if x["etat_au_sheet"] == "Vente réglée"), sum(1 for x in xs if x["vente_reglee_registre"])))
        if case == "LIEN_A_VALIDER":
            print("     confiances du gel : %s" % dict(Counter(x["confiance_du_gel"] for x in xs)))
        if case == "AUDIT_NON_JUSTE":
            print("     verdict de l'audit du 18/11 : %s" % dict(Counter(x["audit_18_11"] for x in xs)))
            print("     touchees par le patch V2 : %d ; gel d'aujourd'hui = ce que l'audit voulait : %s ; protocole = audit :"
                  " %s" % (sum(1 for x in xs if x["touchee_par_v2"]), dict(Counter(x["gel_egal_audit"] for x in xs)),
                           dict(Counter(x["protocole_egal_audit"] for x in xs))))
        if case == "EN_ATTENTE":
            for x in xs:
                print("     %s (ligne %s) : %s | protocole : %s" % (x["id_unique"], x["ligne"],
                                                                 x["pourquoi_en_attente_19_11"][:150],
                                                                 x["lisible_par_le_protocole"][:60]))
        if case == "SANS_LIEN":
            for x in xs:
                print("     %s (ligne %s, %s) : gel [%s] / protocole [%s] -> %s" % (
                    x["id_unique"], x["ligne"], x["etat_au_sheet"], x["gel_aujourdhui"], x["pieces_protocole"],
                    x["dossiers_protocole"]))
    oui = [x for x in trc if x["lisible_par_le_protocole"] == "OUI"]
    print("\nLISIBLES PAR LE PROTOCOLE, sur les %d tranchees ecartees : %d ; par case : %s ; dont decisions du 20/11 : %d" % (
        len(trc), len(oui), dict(Counter(x["case_ecrivain"] for x in oui)), sum(1 for x in oui if x["decision_du_20_11"])))
    print("CSV : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
