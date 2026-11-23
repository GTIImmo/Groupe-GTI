#!/usr/bin/env python
"""LE RESTE A VIDER, PREMIER MOTIF : « BIEN SANS PIECE » (23) + « SANS BIEN » (11).     23/11/2026

    python -u -X utf8 phase2/checks/protocole_les_34_sans_piece_ou_sans_bien_2026-11-23.py [--passage 23]

SON MOT DU 23/11 (12), § 1 : « ⛔ LA MESURE A FAIRE EN PREMIER, elle peut solder les 34 d'un coup : pour chacun des 34,
le bien est-il dans l'un de ces DEUX index au lieu de app_dossier_current ? » -- 44 259 biens n'y sont pas : les vendus
/ clos (app_historical_annonce_index_current, cle app_historical_id) et les archives (app_archive_annonce_index_current,
cle app_archive_id) ; leurs cles SONT notre app_dossier_id renomme (export_app_payload.py:363).

CE QU'IL FAIT -- LECTURE SEULE (le socle et l'image du protocole ; Supabase en REPEATABLE READ READ ONLY) :
  1. les 34 lignes du passage, leurs cases Mandat / product_ref / Lien CRM / Etat Actuel (l'image) ;
  2. « BIEN SANS PIECE » : le bien nomme est-il dans app_dossier_current, dans l'index des vendus / clos, dans celui des
     archives -- ou dans AUCUN ; et combien de pieces il a dans le registre de PRODUCTION (pas seulement l'image) ;
  3. « SANS BIEN » : le protocole ne cherche le Mandat que dans le registre des transactions et dans
     app_mandat_register_current. Ici, le Mandat et le product_ref sont AUSSI cherches dans les deux index (leurs
     numero_mandat / numero_dossier) -- le bien qu'ils nommeraient, s'il est unique ;
  4. LE TEMOIN POSITIF de la recherche : sur les lignes TRANCHEES du meme passage, le bien que les trois index donnent par
     le Mandat doit etre celui du protocole -- sinon la recherche ne vaut rien ;
  5. LA REPARTITION DU REGISTRE : les biens qui ont des pieces, par index -- pour dire si « pas dans current » explique
     « pas de piece », ou non.
ECRIT : notice/PROTOCOLE_LES_34_SANS_PIECE_OU_SANS_BIEN_PASSAGE_<P>_2026-11-23.csv. Rien d'autre.
CODES : 0 mesure faite . 2 pas pu lire.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
import protocole_classeur as P  # noqa: E402

RACINE = ICI.parents[1]
COLS = ("Mandat", "product_ref", "Lien CRM", "Etat Actuel")
DATES_LIGNE = ("Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée", "Vente Réglée")
INDEX = (("current", "app_dossier_current", "app_dossier_id"),
         ("vendu_clos", "app_historical_annonce_index_current", "app_historical_id"),
         ("archive", "app_archive_annonce_index_current", "app_archive_id"))


def dire(s: str = "") -> None:
    print(s, flush=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage", type=int)
    a = ap.parse_args()
    con = P.socle()
    pid = a.passage or con.execute("select max(id) from passage where image is not null").fetchone()[0]
    image = con.execute("select image from passage where id=?", (pid,)).fetchone()[0]
    V = {i: (num, json.loads(b), v, m, mt) for i, num, b, v, m, mt in con.execute(
        "select id_unique, num, biens, verdict, motif, motif_texte from verdict where passage=?", (pid,))}
    con.close()
    cibles = {i: x for i, x in V.items() if x[3] in ("BIEN_SANS_PIECE", "SANS_BIEN")}
    sh = json.loads((P.IMAGES / image / "sheet.json").read_text(encoding="utf-8"))
    k = {c: sh["entete"].index(c) for c in COLS + DATES_LIGNE if c in sh["entete"]}

    def case(i, c):
        row = sh["par_id"][i][0]["row"]
        return str(row[k[c]]).strip() if c in k and k[c] < len(row) and row[k[c]] is not None else ""

    import sauvegarde_datee_classeur as S
    try:
        cn, cu = S.connexion()
    except Exception as e:  # noqa: BLE001
        dire("⛔ pas pu se connecter (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    try:
        # les trois index, entiers (hektor_annonce_id, numero_mandat, numero_dossier, statut, archive, cle)
        idx = {}
        par_bien = defaultdict(list)
        par_mandat = defaultdict(set)
        par_ref = defaultdict(set)
        for nom, table, cle in INDEX:
            cu.execute("select %s::text, hektor_annonce_id::text, coalesce(numero_mandat::text, ''), "
                       "coalesce(numero_dossier::text, ''), coalesce(statut_annonce::text, ''), coalesce(archive::text, '') "
                       "from public.%s" % (cle, table))
            rows = cu.fetchall()
            idx[nom] = len(rows)
            for c, b, nm, nd, st, ar in rows:
                if b:
                    par_bien[b].append((nom, c, nm, nd, st, ar))
                if nm.strip():
                    par_mandat[nm.strip()].add(b)
                if nd.strip() and not nd.strip().isdigit():
                    par_ref[nd.strip().upper()].add(b)
        dates_mandat = {}
        for _nom, table, _cle in INDEX:
            cu.execute("select hektor_annonce_id::text, coalesce(mandat_date_debut::text, ''), "
                       "coalesce(mandat_date_fin::text, '') from public.%s" % table)
            for b, d1, d2 in cu.fetchall():
                dates_mandat[b] = (d1[:10], d2[:10])
        cu.execute("select hektor_annonce_id::text, count(*), string_agg(distinct kind, ',') "
                   "from public.app_affaire_ledger group by 1")
        pieces_prod = {b: (n, k_) for b, n, k_ in cu.fetchall()}
        cu.execute("select coalesce(numero_mandat::text, ''), hektor_annonce_id::text from public.app_mandat_register_current")
        registre_mandats = defaultdict(set)
        for nm, b in cu.fetchall():
            if nm.strip():
                registre_mandats[nm.strip()].add(b)
        cn.rollback()
    finally:
        cn.close()

    dire("LES 34 -- passage %d, image %s : %d lignes (%s)" % (pid, image, len(cibles),
                                                             dict(Counter(x[3] for x in cibles.values()))))
    dire("   les index lus (lecture seule) : %s" % idx)

    # 5. la repartition du registre par index
    rep = Counter()
    for b in pieces_prod:
        noms = sorted({x[0] for x in par_bien.get(b, [])})
        rep["+".join(noms) or "AUCUN"] += 1
    dire("   LE REGISTRE DE PRODUCTION : %d biens ont des pieces ; par index : %s" % (len(pieces_prod), dict(rep)))

    import coupe_preuve_interne as K
    from datetime import date as _date

    def premiere_date(i):
        ds = [K.d_sheet(case(i, c)) for c in DATES_LIGNE]
        ds = [d for d in ds if d]
        return min(ds) if ds else None

    def dans_la_periode(b, d0):
        d1, d2 = dates_mandat.get(b, ("", ""))
        if not d0 or not d1:
            return False
        try:
            debut = _date.fromisoformat(d1)
            fin = _date.fromisoformat(d2) if d2 else _date.max
        except ValueError:
            return False
        return debut <= d0 <= fin

    # 4 bis. LA PISTE DU MANDAT RECYCLE, ET SON TEMOIN : sur les lignes TRANCHEES dont le Mandat nomme PLUSIEURS biens
    #   dans les index, la periode qui contient la 1re date de la ligne garde-t-elle le bien du protocole -- et lui seul ?
    t_ok, t_plus, t_autre, t_aucun = 0, 0, [], 0
    for i, (num, biens, v, m, mt) in V.items():
        if v != "TRANCHEE" or len(biens) != 1:
            continue
        mnd = case(i, "Mandat")
        cand = {b for b in par_mandat.get(mnd, set()) if b} if mnd else set()
        if len(cand) < 2:
            continue
        garde = {b for b in cand if dans_la_periode(b, premiere_date(i))}
        if garde == {biens[0]}:
            t_ok += 1
        elif biens[0] in garde:
            t_plus += 1
        elif garde:
            t_autre.append((i, mnd, sorted(garde), biens[0]))
        else:
            t_aucun += 1
    dire("   TEMOIN DE LA PISTE « MANDAT RECYCLE » (lignes TRANCHEES dont le Mandat nomme plusieurs biens) : la periode "
         "garde le bien du protocole SEUL %d . avec d'autres %d . garde un AUTRE bien %d . aucun %d%s" % (
             t_ok, t_plus, len(t_autre), t_aucun, (" -- ex. %s" % t_autre[:4]) if t_autre else ""))

    # 4. le temoin positif de la recherche par le Mandat (dans les trois index)
    ok, ko, sans = 0, [], 0
    for i, (num, biens, v, m, mt) in V.items():
        if v != "TRANCHEE" or len(biens) != 1:
            continue
        mnd = case(i, "Mandat")
        cand = {b for b in par_mandat.get(mnd, set()) if b} if mnd else set()
        if len(cand) != 1:
            sans += 1
            continue
        if next(iter(cand)) == biens[0]:
            ok += 1
        else:
            ko.append((i, mnd, sorted(cand), biens[0]))
    dire("   TEMOIN POSITIF (lignes TRANCHEES, leur Mandat cherche dans les trois index) : %d donnent le bien du protocole, "
         "%d un AUTRE, %d sans reponse unique -- %s" % (ok, len(ko), sans, "la recherche vaut" if ok and not ko else
                                                       "⚠ a lire : %s" % ko[:5]))

    lignes, verdicts = [], Counter()
    for i, (num, biens, v, m, mt) in sorted(cibles.items(), key=lambda kv: kv[1][0] or 0):
        extra = []
        mnd, ref, lien, etat = (case(i, c) for c in COLS)
        if m == "BIEN_SANS_PIECE":
            b = biens[0]
            ou = par_bien.get(b, [])
            noms = sorted({x[0] for x in ou})
            pp = pieces_prod.get(b)
            verdict = "BIEN DANS %s" % ("+".join(noms).upper() if noms else "AUCUN INDEX")
            verdict += " ; %s" % ("%d piece(s) en production (%s)" % pp if pp else "0 piece en production")
        else:
            b = ""
            c_m = {x for x in par_mandat.get(mnd, set()) if x} if mnd else set()
            c_r = {x for x in par_ref.get(ref.upper(), set()) if x} if ref and not ref.isdigit() else set()
            c_reg = registre_mandats.get(mnd, set()) if mnd else set()
            cand = c_m | c_r
            if len(cand) == 1:
                b = next(iter(cand))
                ou = par_bien.get(b, [])
                noms = sorted({x[0] for x in ou})
                pp = pieces_prod.get(b)
                verdict = "LES INDEX NOMMENT LE BIEN %s (par %s) -- dans %s ; %s" % (
                    b, "+".join(x for x, s in (("mandat", c_m), ("product_ref", c_r)) if s), "+".join(noms).upper(),
                    "%d piece(s) en production (%s)" % pp if pp else "0 piece en production")
            elif len(cand) > 1:
                verdict = "PLUSIEURS BIENS dans les index : %s" % sorted(cand, key=lambda x: int(x) if x.isdigit() else 0)
                ou = []
                d0 = premiere_date(i)
                garde = sorted(cb for cb in cand if dans_la_periode(cb, d0))
                for cb in sorted(cand, key=lambda x: int(x) if x.isdigit() else 0):
                    pp = pieces_prod.get(cb)
                    for x in par_bien.get(cb, []):
                        extra.append("   candidat %-6s index %-10s mandat %s du %s au %s . statut %s . %s%s" % (
                            cb, x[0], x[2], dates_mandat.get(cb, ("?", "?"))[0], dates_mandat.get(cb, ("?", "?"))[1],
                            x[4], "%d piece(s) (%s)" % pp if pp else "0 piece",
                            "   <- SA PERIODE CONTIENT %s" % d0 if cb in garde else ""))
                verdict += " ; la periode du mandat contenant la 1re date de la ligne (%s) en garde %d : %s" % (
                    d0, len(garde), garde)
            else:
                verdict = "AUCUN BIEN, meme dans les index (Mandat %r, product_ref %r ; registre des mandats : %s)" % (
                    mnd, ref, sorted(c_reg) or "rien")
                ou = []
        verdicts[(m, verdict.split(" ;")[0].split(" (")[0] if m == "BIEN_SANS_PIECE" else verdict.split(" :")[0][:40])] += 1
        dire("\n%s (ligne %s) %s : %s" % (i, num, m, verdict))
        for x_ in extra:
            dire(x_)
        dire("   Mandat %r . product_ref %r . Lien CRM %r . Etat Actuel %r" % (mnd, ref, lien[:60], etat))
        for x in ou:
            dire("   index %-10s cle %s . mandat %s . dossier %s . statut %s . archive %s" % x)
        lignes.append({"id_unique": i, "ligne": num, "motif": m, "bien": b or (biens[0] if biens else ""),
                       "mandat": mnd, "product_ref": ref, "lien_crm": lien, "etat_actuel": etat, "verdict": verdict,
                       "index": " | ".join("%s %s statut %s archive %s" % (x[0], x[1], x[4], x[5]) for x in ou)})
    out = RACINE / "notice" / ("PROTOCOLE_LES_34_SANS_PIECE_OU_SANS_BIEN_PASSAGE_%d_2026-11-23.csv" % pid)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    dire("\nVERDICTS : %s" % dict(verdicts))
    dire("-> %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
