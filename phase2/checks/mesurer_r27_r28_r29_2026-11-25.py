#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""R27 (sans le gel), R28 (le verrou « un mandat, une seule vente »), R29 (la ligne suit la vente de sa commission) --
LECTURE SEULE, ⛔ RIEN N'EST ECRIT (son mot du 25/11, soir : « Rien n'est ecrit tant que je n'ai pas vu ces trois chiffres »).

    python -X utf8 -u phase2\checks\mesurer_r27_r28_r29_2026-11-25.py

Les champs de HEKTOR seulement (jamais nos recopies de son Sheet : vente_reglee_app, numero_facture_app...) :
numero_mandat, honoraires_entree, les acquereurs, le journal des offres (propositions_json).
"""
from __future__ import annotations

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

STOP = {"NAN", "MME", "MR", "MLLE", "ET", "SCI", "SOCIETE", "SOCIÉTÉ", "LES", "DES", "EPOUX", "ÉPOUX", "INDIVISION"}


def noms(t) -> set:
    return {x for x in re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", str(t or "").upper()) if x not in STOP}


def nombre(t):
    t = re.sub(r"[^\d,.]", "", str(t or "")).replace(",", ".")
    try:
        return float(t) if t else None
    except ValueError:
        return None


def main() -> int:
    con = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
    V = {i: {"v": v, "e": e or "", "ps": json.loads(ps) if ps else [], "m": m or ""} for i, v, e, ps, m in con.execute(
        "select id_unique, verdict, etiquette, pieces, motif from verdict where passage=81")}
    con.close()
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, kind, state, date::text, app_chaine_id, app_dossier_uuid::text, app_dossier_numero, "
               "transaction_origine, hektor_affaire_id, numero_mandat, honoraires_entree, acquereurs_json::text, "
               "acquereur_json::text, hektor_annonce_id, propositions_json::text, coalesce(date_annulation_app,'') "
               "from public.app_affaire_ledger")
    R = {}
    for r in cu.fetchall():
        R[int(r[0])] = dict(zip(["a", "genre", "etat", "date", "chaine", "uuid", "numero", "origine", "hk", "mandat", "hon",
                                 "acqs", "acq", "annonce", "props", "annul"], r))
    cn.rollback()
    cn.close()
    img = json.loads((P.IMAGES / "2026-11-25_072625" / "sheet.json").read_text(encoding="utf-8"))
    ent = img["entete"]

    def case(i, c):
        return img["par_id"][i][0]["row"][ent.index(c)].strip()

    def copie(a):
        return PC.est_copie(a, R[a]["origine"], R[a]["hk"])

    def acq_noms(a):
        out = set()
        for t in (R[a]["acqs"], R[a]["acq"]):
            try:
                x = json.loads(t) if t else None
            except ValueError:
                x = None
            for y in (x if isinstance(x, list) else [x] if isinstance(x, dict) else []):
                if isinstance(y, dict):
                    out |= noms(y.get("nom"))
        return out

    def jour_offre(a):
        try:
            pj = json.loads(R[a]["props"]) if R[a]["props"] else []
        except ValueError:
            return None
        for p in pj or []:
            for x in (p if isinstance(p, list) else [p]):
                if isinstance(x, dict) and x.get("type") == "proposition" and x.get("date"):
                    return str(x["date"])[:10]
        return (R[a]["date"] or "")[:10] or None

    tenues = defaultdict(set)              # piece -> lignes qui la tiennent au 81
    for i, v in V.items():
        if v["v"] == "TRANCHEE":
            for a in v["ps"]:
                tenues[a].add(i)
    ventes_hk = [a for a, r in R.items() if r["genre"] == "vente" and not copie(a)]
    par_mandat = defaultdict(list)
    for a in ventes_hk:
        m = str(R[a]["mandat"] or "").strip()
        if m:
            par_mandat[m].append(a)

    # ── ① R27 : le 3e critere SANS le gel ──
    print("① R27 -- un 3e critere sans le gel (pour deux lignes ANNULEES, sans vente au dossier)")
    for x, y in (("3308P0UX", "YRUF0S9H"), ("T2GZOY5O", "O6R10ZQA")):
        ps = sorted(set(V[x]["ps"]) | set(V[y]["ps"]))
        jh = {}
        for a in ps:
            if a in R and not copie(a):
                try:
                    pj = json.loads(R[a]["props"]) if R[a]["props"] else []
                except ValueError:
                    pj = []
                for p in pj or []:
                    for z in (p if isinstance(p, list) else [p]):
                        if isinstance(z, dict) and z.get("type") in ("refus", "annulation"):
                            jh[a] = str(z.get("date"))[:10]
                if R[a]["genre"] == "compromis" and R[a]["annul"]:
                    jh.setdefault(a, "annulation posee %s" % R[a]["annul"])
        dx, dy = P.K.d_sheet(case(x, "Annulée")), P.K.d_sheet(case(y, "Annulée"))
        print("   %s annulee %s | %s annulee %s | le dossier : %s ; Hektor date le refus / l'annulation : %s" % (
            x, dx, y, dy, ps, jh))
        prouvee = [i for i, d in ((x, dx), (y, dy)) if d and str(d) in {str(v)[:10] for v in jh.values()}]
        plus_ancienne = min(((dx, x), (dy, y)), key=lambda t: (t[0] is None, t[0]))[1]
        print("     critere ② (annulation deja posee) : %s ; ③ prouvee par le journal de Hektor : %s ; ④ la plus ancienne "
              "date d'annulation : %s" % ([i for i, d in ((x, dx), (y, dy)) if d and any(
                  str(d) in str(v) for v in jh.values() if str(v).startswith("annulation"))] or "aucune",
                                           prouvee or "aucune", plus_ancienne))

    # ── ② R28 : le verrou « un mandat, une seule vente » ──
    print("\n② R28 -- les mandats et leurs ventes (Hektor, sans les copies)")
    plusieurs = {m: v for m, v in par_mandat.items() if len(v) > 1}
    print("   ventes de Hektor : %d, sur %d mandats ; mandats a PLUSIEURS ventes : %d (%s ventes) ; ventes sans mandat : %d" % (
        len(ventes_hk), len(par_mandat), len(plusieurs), sum(len(v) for v in plusieurs.values()),
        sum(1 for a in ventes_hk if not str(R[a]["mandat"] or "").strip())))
    print("   repartition : %s" % dict(sorted(Counter(len(v) for v in par_mandat.values()).items())))
    print("   exemples de mandats a plusieurs ventes : %s" % [(m, [(a, (R[a]["date"] or "")[:10]) for a in v])
                                                           for m, v in list(plusieurs.items())[:6]])

    def r28(i):
        m = case(i, "Mandat")
        vs = par_mandat.get(m, [])
        if len(vs) != 1:
            return False, "mandat %r : %d vente(s)" % (m, len(vs))
        a = vs[0]
        h, c = nombre(R[a]["hon"]), nombre(case(i, "Commission TTC"))
        okh = h is not None and c is not None and abs(h - c) < 1
        oka = bool(acq_noms(a) & noms(case(i, "Acquéreur")))
        deja = sorted(tenues.get(a, set()) - {i})
        return okh and oka and not deja, "vente %s (%s) : honoraires %s / Commission %s -> %s ; acquereur %s / %s -> %s%s" % (
            a, R[a]["numero"], h, c, okh, sorted(acq_noms(a)), sorted(noms(case(i, "Acquéreur"))), oka,
            " ; ⛔ deja tenue par %s" % deja if deja else "")
    cs = sorted(i for i, v in V.items() if v["m"] == "COPIE_SEULE")
    deb = []
    for i in cs:
        ok, why = r28(i)
        if ok:
            deb.append(i)
        print("   %s (%s, mandat %s) -> %s : %s" % (i, case(i, "Etat Actuel"), case(i, "Mandat"), "DEBLOQUEE" if ok else "non", why))
    print("   => R28 debloque %d ligne(s) sur les %d « copie seule » : %s" % (len(deb), len(cs), deb))
    att = sorted(i for i, v in V.items() if v["v"] != "TRANCHEE")
    jum = [i for i in att if i not in cs and r28(i)[0]]
    print("   (temoin de portee, hors de son motif : parmi les %d autres lignes en attente, le verrou seul en prendrait %d : %s)"
          % (len(att) - len(cs), len(jum), jum))

    # ── ③ R29 : la ligne suit la vente qui porte sa commission, meme si le nom note est celui d'un acquereur REFUSE ──
    print("\n③ R29 -- une ligne suit la vente de sa commission, quand son nom est celui d'un acquereur REFUSE")
    offres_ref = [a for a, r in R.items() if r["genre"] == "offre" and r["etat"] == "refused" and not copie(a)]
    prises = []
    for i in att:
        nm = noms(case(i, "Acquéreur"))
        jo = P.K.d_sheet(case(i, "Offre Achat"))
        if not nm or not jo:
            continue
        cand = [a for a in offres_ref if acq_noms(a) & nm and jour_offre(a) == str(jo)]
        for a in cand:
            ms = {str(R[b]["mandat"] or "").strip() for b, r in R.items() if r["annonce"] == R[a]["annonce"] and
                  str(r["mandat"] or "").strip()}
            vs = sorted({v for m in ms for v in par_mandat.get(m, [])})
            if len(vs) != 1:
                print("   %s : offre refusee %s (%s, %s) -> mandat(s) %s : %d vente(s) -- pas de verrou" % (
                    i, a, sorted(acq_noms(a)), jour_offre(a), sorted(ms), len(vs)))
                continue
            v = vs[0]
            h, c = nombre(R[v]["hon"]), nombre(case(i, "Commission TTC"))
            okh = h is not None and c is not None and abs(h - c) < 1
            autre_acq = not (acq_noms(v) & nm)
            deja = sorted(tenues.get(v, set()) - {i})
            ok = okh and autre_acq and not deja
            print("   %s (ligne %s, %s, mandat du Sheet %s) : son nom %s = l'offre REFUSEE %s du %s (annonce %s, mandat %s) -> "
                  "LA vente %s (%s, acquereur %s, honoraires %s / Commission %s) %s%s" % (
                      i, img["par_id"][i][0]["num"], case(i, "Etat Actuel"), case(i, "Mandat"), sorted(nm), a,
                      jour_offre(a), R[a]["annonce"], sorted(ms), v, R[v]["numero"], sorted(acq_noms(v)), h, c,
                      "-> PRISE" if ok else "-> non", " ; ⛔ deja tenue par %s" % deja if deja else ""))
            if ok:
                prises.append((i, v, R[v]["numero"]))
    print("   => R29 prendrait %d ligne(s) : %s" % (len(prises), prises))
    return 0


if __name__ == "__main__":
    sys.exit(main())
