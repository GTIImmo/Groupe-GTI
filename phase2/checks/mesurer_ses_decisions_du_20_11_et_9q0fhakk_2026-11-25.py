#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SES DECISIONS DU 20/11 (les 19, la decision B) AU PASSAGE 81, ET LA LIGNE 9Q0FHAKK -- LECTURE SEULE, ⛔ RIEN N'EST ECRIT.

    python -X utf8 -u phase2\checks\mesurer_ses_decisions_du_20_11_et_9q0fhakk_2026-11-25.py

SON MOT (25/11) :
  ① « les 19 lignes de ma decision, une par une -- combien sont TRANCHEES au passage 81 avec un dossier unique ? [...] Et
    verifie l'inverse : est-ce qu'en les remettant dans la vague, UNE SEULE ligne deja ecrite changerait d'etiquette ? »
  ② « au passage 81, APRES la vague, l'etiquette prevue de ces 9 lignes est-elle celle de LEUR VENTE, ou celle de la
    tentative ratee ? »
  ③ 9Q0FHAKK : « SA VENTE EXISTE [...] MESURE-LE ET DIS-MOI SI TU ARRIVES AU MEME ENDROIT [...] Et dis-moi ce qu'est la
    chaine 3648. »
Sources : le socle du protocole (passage 81), le registre (SQL direct), le Sheet relu (colonne A), les fichiers de ses
deux decisions, l'image de 07:26 (les colonnes du Sheet), l'audit du 18/11.
"""
from __future__ import annotations

import csv
import json
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
D19 = NOTICE / "TEMPS7_DECISION_DU_20_11_LES_19_HORS_DE_LA_VAGUE_1_2026-11-20.csv"
DB = NOTICE / "TEMPS6_DECISION_B_LIGNES_REPORTEES_EN_VAGUE_2_PAR_G2_2026-11-20.csv"
AUDIT = NOTICE / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv"


def lire(f):
    with f.open(encoding="utf-8-sig") as h:
        return list(csv.DictReader(h, delimiter=";"))


def main() -> int:
    con = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
    V = {i: {"v": v, "e": e or "", "ps": json.loads(ps) if ps else [], "pr": json.loads(pr) if pr else [], "m": m,
             "mt": mt} for i, v, e, ps, pr, m, mt in con.execute(
        "select id_unique, verdict, etiquette, pieces, preuves, motif, motif_texte from verdict where passage=81")}
    con.close()
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, kind, state, date::text, montant, app_chaine_id, app_dossier_uuid::text, "
               "app_dossier_numero, transaction_origine, hektor_affaire_id, hektor_annonce_id, numero_mandat, "
               "propositions_json, acquereurs_json, coalesce(vente_reglee_app,''), coalesce(numero_facture_app,''), "
               "honoraires_entree, date_acte::text from public.app_affaire_ledger")
    R = {}
    for r in cu.fetchall():
        R[int(r[0])] = dict(zip(["a", "genre", "etat", "date", "montant", "chaine", "uuid", "numero", "origine", "hk",
                                 "annonce", "mandat", "props", "acq", "reglee", "facture", "hon", "acte"], r))
    cu.execute("select id_unique, app_affaire_id from public.app_classeur_lien")
    gel = defaultdict(set)
    for i, a in cu.fetchall():
        gel[i].add(int(a))
    cn.rollback()
    cn.close()
    import apparier_classeur as ac
    ac.load_env_file(RACINE / ".env")
    entete, lignes = ac.lire_classeur()
    A = {}
    for _n, l in lignes:
        l = [("" if x is None else str(x)) for x in list(l)] + [""] * 38
        if l[37].strip():
            A[l[37].strip()] = l[0].strip()
    en_a = Counter(v for v in A.values() if v)

    def copie(a):
        return PC.est_copie(a, R[a]["origine"], R[a]["hk"])

    def dossier(ps):
        k = [a for a in ps if a in R]
        hk = [a for a in k if not copie(a)] or k
        return {R[a]["uuid"] for a in hk}

    def arrivee(i):
        e = V[i]["e"]
        return R.get(int(e.split(":")[1]), {}).get("uuid") if e.startswith("NEUVE:") else e

    lignes_u = defaultdict(set)
    for i, x in V.items():
        if x["v"] == "TRANCHEE":
            for u in dossier(x["ps"]):
                lignes_u[u].add(i)

    # ── ① LES 19 ──
    print("① SA DECISION DU 20/11 SUR LES 19 -- au passage 81")
    d19 = lire(D19)
    ok19 = []
    for r in d19:
        i = r["id_unique"]
        x = V.get(i, {"v": "ABSENTE", "ps": []})
        d = dossier(x["ps"]) if x["v"] == "TRANCHEE" else set()
        u = next(iter(d)) if len(d) == 1 else None
        autres = sorted(lignes_u.get(u, set()) - {i}) if u else []
        deja = A.get(i, "")
        conflit = u and en_a.get(u, 0) > 0
        vr = [a for a in x["ps"] if a in R and R[a]["genre"] == "vente"]
        bon = x["v"] == "TRANCHEE" and len(d) == 1 and u == arrivee(i) and not autres and not conflit and not deja
        if bon:
            ok19.append(i)
        print("   %-9s %-8s pieces %-26s -> %-11s %s%s%s%s | sortie de la piece en cause : %s" % (
            i, x["v"], " ".join(map(str, x["ps"])), R[next(iter(x["ps"]))]["numero"] if x["ps"] else "-",
            "UN dossier" if len(d) == 1 else "%d dossiers" % len(d),
            " ; vente %s reglee %s" % (vr[0], R[vr[0]]["reglee"] or "-") if vr else " ; pas de vente",
            " ; ⛔ son dossier porte aussi %s" % autres if autres else "",
            " ; ⛔ son etiquette est DEJA en A" if conflit else "", r["la_piece_en_cause"][:70]))
    print("   => %d / %d TRANCHEES, un seul dossier, l'etiquette du 81, seules sur leur dossier, etiquette absente de la "
          "colonne A" % (len(ok19), len(d19)))
    print("   => L'INVERSE : remettre une ligne dans la vague n'ecrit QUE sa case vide (l'ecrivain n'ecrase jamais) ; une "
          "etiquette deja en A sur une autre ligne la ferait SAUTER (UUID_DEJA_DANS_LE_SHEET), jamais ecrire par-dessus. "
          "Etiquettes des 19 deja presentes en A : %d" % sum(1 for r in d19 for u in dossier(V.get(r["id_unique"], {"ps": []})["ps"])
                                                            if en_a.get(u)))

    # ── ② LA DECISION B ──
    print("\n② SA DECISION B (9 lignes, « vague 2, apres G2 ») -- l'etiquette prevue au 81 : LEUR VENTE ou la tentative ratee ?")
    okb = []
    for r in lire(DB):
        i = r["id_unique"]
        x = V.get(i, {"v": "ABSENTE", "ps": []})
        u = arrivee(i) if x["v"] == "TRANCHEE" else None
        ventes = [a for a in x["ps"] if a in R and R[a]["genre"] == "vente"]
        u_vente = {R[a]["uuid"] for a in ventes}
        ratee_txt = r["le_dossier_coupe_par_g2"].split("||")[0]
        ratee = [int(t) for t in ratee_txt.replace("(", " ").split() if t.isdigit() and int(t) in R]
        u_ratee = {R[a]["uuid"] for a in ratee}
        avant = r["etiquette_avant_g2"]
        verdict = ("LEUR VENTE" if u and u_vente == {u} and u not in u_ratee else
                   "LA TENTATIVE RATEE" if u in u_ratee or u == avant else "A REGARDER")
        if verdict == "LEUR VENTE" and len(dossier(x["ps"])) == 1 and not A.get(i) and not en_a.get(u):
            okb.append(i)
        print("   %-9s %-8s pieces %-20s -> %-11s etiquette %s | vente %s (%s, reglee %s) | tentative ratee %s : "
              "etiquette %s (= celle d'avant G2 : %s) -> %s" % (
                  i, x["v"], " ".join(map(str, x["ps"])), R[ventes[0]]["numero"] if ventes else "-", (u or "")[:8],
                  ventes, sorted(x[:8] for x in u_vente), R[ventes[0]]["reglee"] if ventes else "-", ratee,
                  sorted(x[:8] for x in u_ratee), avant[:8] in {x[:8] for x in u_ratee}, verdict))
    print("   => %d / 9 : l'etiquette prevue est celle de LEUR VENTE, un seul dossier, case A vide, etiquette absente de A"
          % len(okb))

    # ── ③ 9Q0FHAKK ──
    print("\n③ 9Q0FHAKK")
    sheet = json.loads((P.IMAGES / "2026-11-25_072625" / "sheet.json").read_text(encoding="utf-8"))
    ent = sheet["entete"]
    row = sheet["par_id"]["9Q0FHAKK"][0]["row"]
    cols = ["Mandat", "product_ref", "Etat Actuel", "Offre Achat", "Compromis", "Signé", "Vente Prévue", "Vente Fixée",
            "Signée", "Vente Réglée", "Numéro de facture", "Prix", "Commission TTC", "Ville", "Agence"]
    print("   le Sheet (ligne %s) : %s" % (sheet["par_id"]["9Q0FHAKK"][0]["num"],
                                         " ; ".join("%s=%r" % (c, row[ent.index(c)]) for c in cols if c in ent)))
    x = V["9Q0FHAKK"]
    print("   le protocole (81) : %s %s -- %s" % (x["v"], x["m"], (x["mt"] or "")[:300]))
    print("   le gel : %s" % sorted(gel.get("9Q0FHAKK", set())))
    au = {r["id_unique"]: r for r in lire(AUDIT)}
    for j in ("9Q0FHAKK", "427UDDSF"):
        if j in au:
            print("   l'audit du 18/11 sur %s : %s | liens %s | a rattacher %s | dossier juste %s" % (
                j, au[j]["verdict"], au[j]["liens"][:90], au[j]["a_rattacher"][:60], au[j]["dossier_juste"][:90]))
    pcs = sorted(a for a, r in R.items() if str(r["annonce"]) == "8395")
    print("   l'annonce 8395 (registre) : %d pieces" % len(pcs))
    for a in pcs:
        r = R[a]
        props = ""
        try:
            pj = json.loads(r["props"]) if r["props"] else []
            props = "; ".join("%s %s" % (str(p.get("date") or p.get("date_proposition") or "")[:10],
                                         p.get("prix") or p.get("montant") or "") for p in (pj if isinstance(pj, list) else [])[:3])
        except (ValueError, TypeError, AttributeError):
            props = str(r["props"])[:80]
        lignes_p = sorted(i for i, v in V.items() if v["v"] == "TRANCHEE" and a in v["ps"])
        gel_p = sorted(i for i, s in gel.items() if a in s)
        print("     %-6s %-9s %-9s date %-19s montant %-9s chaine %-5s %-11s mandat %-6s acq %s | reglee %r facture %r "
              "| propositions [%s] | tenue au 81 par %s ; au gel par %s" % (
                  a, r["genre"], r["etat"], (r["date"] or "")[:19], r["montant"], r["chaine"], r["numero"], r["mandat"],
                  str(r["acq"])[:60], r["reglee"], r["facture"], props, lignes_p or "PERSONNE", gel_p or "personne"))
    m = [a for a, r in R.items() if str(r["mandat"]) == "17253"]
    print("   le mandat 17253 (celui de sa ligne) porte au registre : %s" % sorted(
        (a, R[a]["genre"], R[a]["annonce"]) for a in m)[:10])
    return 0


if __name__ == "__main__":
    sys.exit(main())
