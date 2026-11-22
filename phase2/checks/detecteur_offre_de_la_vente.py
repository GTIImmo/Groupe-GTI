#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE DETECTEUR DE L'OFFRE DE LA VENTE -- quelle offre refusee a tort peut se REACCEPTER, laquelle s'EXAMINE.   23/11/2026

    python -u -X utf8 phase2/checks/detecteur_offre_de_la_vente.py

SON MOT DU 23/11 (2), § 3 : « QUAND L'OFFRE QU'ON A REFUSEE N'A PAS LE MONTANT DE LA VENTE, ET QU'UNE AUTRE OFFRE DU
MEME BIEN LE PORTE EXACTEMENT, C'EST L'AUTRE QUI A MENE A LA VENTE. Reaccepter la notre ecrirait une fausse histoire.
Mets cette regle dans ton detecteur : elle vaut pour les prochains lots. » -- et « LES ONZE SURES -- montant exact de la
vente, acceptation AVANT la vente, delai de 1 a 11 mois ».

⛔ LECTURE SEULE. Il ne repare rien : il classe. La reparation (deux gestes par offre) attend son mot, liste validee.

LE JUGE, `juger(offre, pieces_du_bien)` -- une fonction pure, que le prochain lot appellera telle quelle. Dans l'ordre :
  HORS        le bien ne porte aucune vente, ou notre offre n'a JAMAIS ete acceptee avant notre refus ;
  R_APRES     acceptee APRES la vente                                                   -> A EXAMINER
  R_MONTANT   SA REGLE : le montant accepte n'est pas celui de la vente, ET une autre offre du bien porte exactement
              le montant vendu                                                          -> A EXAMINER
  R_SEULE     le montant n'est pas celui de la vente, et aucune autre offre ne le porte -> A EXAMINER
  R_DELAI     montant exact, avant la vente, mais plus d'UN AN avant                    -> A EXAMINER
  R_AMBIGUE   montant exact, avant, a moins d'un an -- mais une AUTRE offre du bien a ete ACCEPTEE au meme montant
              (son journal porte « accepte »)                                           -> SON ARBITRAGE
  SURE        montant exact, acceptee avant la vente, a moins d'un an, et SEULE offre du bien jamais ACCEPTEE au
              montant vendu (les autres a ce montant, s'il y en a, sont nommees : jamais acceptees)
⚠ DEUX CHOSES MESUREES LE 23/11, qui ont fixe la forme du juge :
  . « l'autre offre au montant » n'est, sur les 17, JAMAIS une offre acceptee : les 12 sont proposees et refusees LE
    MEME JOUR (journal « proposition | refus »). Sa regle prouve donc un DOUTE, pas que l'autre « a mene a la vente » :
    ⛔ le juge ne rend JAMAIS « reaccepter l'autre » ; il rend « a examiner ».
  . 6 de ses onze ont AUSSI une autre offre au montant exact (531, 14112 x2, 17322, 22446, 24159, 23995) : ce qui les
    rend sures, c'est d'etre la SEULE ACCEPTEE a ce montant -- c'est aussi ce qui tranche le bien 28653 (14112).
  . la borne « 1 a 11 mois » est ecrite a UN AN : 14112 (340 jours) depasse 11 mois de 3 jours, et il est dans ses onze.
LE TEMOIN : ses onze doivent sortir SURE, ses six A EXAMINER, 23139 HORS -- sinon code 1. Et deux cas fabriques
(une autre ACCEPTEE au meme montant -> R_AMBIGUE ; notre montant faux et une autre au montant -> R_MONTANT).
EN PLUS (meme famille, lecture seule) : les 19 reacceptees le 12/11 par le critere du NOM, passees au meme juge.
ECRIT : notice/LES_ONZE_SURES_ET_LES_SIX_A_EXAMINER_2026-11-23.csv
CODES : 0 le temoin tient . 1 le juge ne rend pas son classement . 2 pas pu lire
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))

SES_ONZE = [531, 3648, 6556, 7780, 14008, 14112, 17322, 22384, 22446, 23995, 24159]
SES_SIX = [14420, 18600, 5126, 21600, 17025, 16421]
HORS_ATTENDU = [23139]
SORTIE = RACINE / "notice" / "LES_ONZE_SURES_ET_LES_SIX_A_EXAMINER_2026-11-23.csv"
UN_AN = 366


def _jour(s):
    s = str(s or "")
    try:
        return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None


def _nombre(x):
    try:
        return round(float(str(x)))
    except (TypeError, ValueError):
        return None


def _acceptations(journal, avant=None):
    """Les entrees « accepte » du journal (avant `avant`, une date texte, si donnee)."""
    return [p for p in (journal or []) if p.get("type") == "accepte"
            and (avant is None or str(p.get("date", "")) < str(avant))]


def notre_refus(journal):
    """Notre refus : la premiere entree « refus » des 11-12/11/2026."""
    r = [p for p in (journal or []) if p.get("type") == "refus" and str(p.get("date", ""))[:10] in ("2026-11-11", "2026-11-12")]
    return r[0] if r else None


def juger(offre: dict, pieces: list[dict]) -> dict:
    """offre / pieces : {app_affaire_id, kind, state, montant, date, propositions_json, transaction_origine,
    app_chaine_id}. `pieces` = toutes les pieces du bien. Rend {verdict, motif, ...} -- ne decide rien."""
    j = offre.get("propositions_json") or []
    refus = notre_refus(j)
    acc = _acceptations(j, refus.get("date") if refus else None)
    hektor = [p for p in pieces if not str(p.get("transaction_origine") or "").strip()]
    ventes = [p for p in hektor if p.get("kind") == "vente"]
    out = {"verdict": "", "motif": "", "acceptee_le": "", "montant_accepte": None, "vente": None, "delai_jours": None,
           "autres_au_montant": []}
    if not ventes:
        out.update(verdict="HORS", motif="le bien ne porte aucune vente")
        return out
    if not acc:
        out.update(verdict="HORS", motif="notre offre n'a jamais ete acceptee avant notre refus")
        return out
    a = acc[-1]
    m = _nombre(a.get("montant"))
    da = _jour(a.get("date"))
    meme = [v for v in ventes if _nombre(v.get("montant")) == m]
    v = (meme or sorted(ventes, key=lambda x: abs(((_jour(x.get("date_acte") or x.get("date")) or da) - da).days)))[0]
    dv = _jour(v.get("date_acte") or v.get("date"))
    mv = _nombre(v.get("montant"))
    out.update(acceptee_le=str(a.get("date", ""))[:10], montant_accepte=m, vente=v,
               delai_jours=(dv - da).days if (dv and da) else None)
    autres = []
    for p in hektor:
        if p.get("kind") != "offre" or p.get("app_affaire_id") == offre.get("app_affaire_id"):
            continue
        jp = p.get("propositions_json") or []
        au_montant = _nombre(p.get("montant")) == mv or any(_nombre(e.get("montant")) == mv for e in jp)
        if au_montant:
            acc_p = [e for e in jp if e.get("type") == "accepte" and _nombre(e.get("montant")) == mv]
            autres.append({"id": p.get("app_affaire_id"), "acceptee": bool(acc_p),
                           "journal": " | ".join("%s %s" % (str(e.get("date", ""))[:10], e.get("type")) for e in jp)})
    out["autres_au_montant"] = autres
    if dv and da and da > dv:
        out.update(verdict="A EXAMINER", motif="R_APRES : acceptee %d jours APRES la vente" % (da - dv).days)
    elif m != mv and autres:
        out.update(verdict="A EXAMINER", motif="R_MONTANT (sa regle) : %s accepte, vente a %s, et une autre offre porte "
                   "exactement le montant vendu (%s)" % (m, mv, ", ".join(str(x["id"]) for x in autres)))
    elif m != mv:
        out.update(verdict="A EXAMINER", motif="R_SEULE : %s accepte, vente a %s, aucune autre offre a ce montant" % (m, mv))
    elif out["delai_jours"] is not None and out["delai_jours"] > UN_AN:
        out.update(verdict="A EXAMINER", motif="R_DELAI : acceptee %d jours avant la vente" % out["delai_jours"])
    elif any(x["acceptee"] for x in autres):
        out.update(verdict="SON ARBITRAGE", motif="R_AMBIGUE : une autre offre ACCEPTEE au meme montant (%s)"
                   % ", ".join(str(x["id"]) for x in autres if x["acceptee"]))
    else:
        out.update(verdict="SURE", motif="montant exact, acceptee %s jours avant la vente, seule offre ACCEPTEE a ce "
                   "montant%s" % (out["delai_jours"], (" (au meme montant mais JAMAIS acceptee : %s)" % ", ".join(
                       str(x["id"]) for x in autres)) if autres else ""))
    return out


def _essais() -> list[str]:
    """Deux cas fabriques : la branche d'arbitrage et sa regle doivent MORDRE."""
    rouges = []
    J = lambda *e: [{"date": d, "type": t, "montant": mt} for d, t, mt in e]  # noqa: E731
    vente = {"app_affaire_id": 9, "kind": "vente", "montant": "100000", "date": "2021-06-01"}
    notre = {"app_affaire_id": 1, "kind": "offre", "montant": "100000",
             "propositions_json": J(("2021-02-01", "accepte", "100000"), ("2026-11-11 19:00", "refus", "100000"))}
    autre_acc = {"app_affaire_id": 2, "kind": "offre", "montant": "100000",
                 "propositions_json": J(("2021-01-01", "accepte", "100000"), ("2021-01-20", "refus", "100000"))}
    if juger(notre, [notre, autre_acc, vente])["verdict"] != "SON ARBITRAGE":
        rouges.append("essai 1 : une autre ACCEPTEE au meme montant devait rendre SON ARBITRAGE")
    faux = dict(notre, montant="95000",
                propositions_json=J(("2021-02-01", "accepte", "95000"), ("2026-11-11 19:00", "refus", "95000")))
    autre = {"app_affaire_id": 3, "kind": "offre", "montant": "100000",
             "propositions_json": J(("2021-01-01", "proposition", "100000"), ("2021-01-01", "refus", "100000"))}
    if not juger(faux, [faux, autre, vente])["motif"].startswith("R_MONTANT"):
        rouges.append("essai 2 : sa regle (montant faux + une autre au montant) devait mordre")
    if juger(notre, [notre, autre, vente])["verdict"] != "SURE":
        rouges.append("essai 3 : une autre au montant JAMAIS acceptee ne doit pas empecher SURE")
    return rouges


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rouges = _essais()
    print("essais fabriques : %s" % ("3/3 verts" if not rouges else rouges))
    import sauvegarde_datee_classeur as S
    try:
        cn, cu = S.connexion()
    except Exception as e:  # noqa: BLE001
        print("⛔ Supabase n'a pas pu etre lu (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    cols = ("app_affaire_id", "kind", "state", "montant", "date", "date_acte", "hektor_affaire_id", "hektor_annonce_id",
            "app_chaine_id", "transaction_origine", "propositions_json")
    try:
        # les 19 reacceptees du 12/11 : par leurs travaux
        cu.execute("select distinct (payload_json->>'app_affaire_id')::bigint from public.app_console_job "
                   "where job_type = 'change_hektor_offre_status' and payload_json->>'type' = 'accepte' "
                   "and created_at >= '2026-11-12' and created_at < '2026-11-13'")
        dix_neuf = sorted(int(r[0]) for r in cu.fetchall())
        cibles = SES_ONZE + SES_SIX + HORS_ATTENDU + dix_neuf
        cu.execute("select %s from public.app_affaire_ledger where hektor_annonce_id in (select hektor_annonce_id from "
                   "public.app_affaire_ledger where app_affaire_id = any(%%s))" % ", ".join(cols), (cibles,))
        pieces = [dict(zip(cols, r)) for r in cu.fetchall()]
        cn.rollback()
    finally:
        cn.close()
    par_bien, par_id = {}, {}
    for p in pieces:
        par_bien.setdefault(p["hektor_annonce_id"], []).append(p)
        par_id[p["app_affaire_id"]] = p
    lignes, verdicts = [], {}
    for groupe, ids in (("ses onze", SES_ONZE), ("ses six", SES_SIX), ("hors", HORS_ATTENDU),
                        ("les 19 du 12/11", dix_neuf)):
        for i in ids:
            o = par_id.get(i)
            if not o:
                rouges.append("%d introuvable" % i)
                continue
            r = juger(o, par_bien[o["hektor_annonce_id"]])
            verdicts[(groupe, i)] = r["verdict"]
            v = r["vente"] or {}
            lignes.append({"groupe": groupe, "offre": i, "bien": o["hektor_annonce_id"], "etat": o["state"],
                           "verdict": r["verdict"], "motif": r["motif"], "acceptee_le": r["acceptee_le"],
                           "montant_accepte": r["montant_accepte"], "vente": v.get("app_affaire_id"),
                           "vente_montant": _nombre(v.get("montant")), "vente_le": str(v.get("date_acte") or v.get("date") or "")[:10],
                           "delai_jours": r["delai_jours"],
                           "autres_au_montant_vendu": " ; ".join("%s (%s : %s)" % (x["id"], "ACCEPTEE" if x["acceptee"]
                                                                  else "jamais acceptee", x["journal"])
                                                                  for x in r["autres_au_montant"]) or "-"})
            print("%-16s %-6s bien %-6s %-14s %s" % (groupe, i, o["hektor_annonce_id"], r["verdict"], r["motif"]))
    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    # LE TEMOIN : le juge rend SON classement
    for i in SES_ONZE:
        if verdicts.get(("ses onze", i)) != "SURE":
            rouges.append("%d : %s au lieu de SURE" % (i, verdicts.get(("ses onze", i))))
    for i in SES_SIX:
        if verdicts.get(("ses six", i)) != "A EXAMINER":
            rouges.append("%d : %s au lieu de A EXAMINER" % (i, verdicts.get(("ses six", i))))
    for i in HORS_ATTENDU:
        if verdicts.get(("hors", i)) != "HORS":
            rouges.append("%d : %s au lieu de HORS" % (i, verdicts.get(("hors", i))))
    from collections import Counter
    c19 = Counter(verdicts[("les 19 du 12/11", i)] for i in dix_neuf if ("les 19 du 12/11", i) in verdicts)
    print("-> %s (%d lignes)" % (SORTIE, len(lignes)))
    print("TEMOIN : ses onze SURE %d/11 . ses six A EXAMINER %d/6 . 23139 HORS %s . les 19 du 12/11 : %s" % (
        sum(verdicts.get(("ses onze", i)) == "SURE" for i in SES_ONZE),
        sum(verdicts.get(("ses six", i)) == "A EXAMINER" for i in SES_SIX),
        verdicts.get(("hors", 23139)), dict(c19)))
    if rouges:
        print("⛔ ROUGES : %s" % rouges)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
