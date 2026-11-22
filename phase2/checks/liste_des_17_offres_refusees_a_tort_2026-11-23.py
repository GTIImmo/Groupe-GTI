#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA LISTE DES 17 OFFRES REFUSEES A TORT, CHACUNE AVEC SA PREUVE.             23/11/2026

    python -u -X utf8 phase2/checks/liste_des_17_offres_refusees_a_tort_2026-11-23.py

SA DEMANDE (mot du 23/11, § 4 b) : « LA LISTE DES 14, chacune avec sa preuve lue dans `propositions_json` : la date de
l'acceptation, la date de notre refus, le montant, et le montant de la vente. ⛔ TU NE REPARES RIEN. »

⛔ LECTURE SEULE (REPEATABLE READ READ ONLY). Rien chez Hektor, rien en base.

POUR CHAQUE OFFRE (ses 17 -- les 14 et les 3 « moins graves » --, plus, a part, ce que la mesure a trouve en route) :
  . la PREUVE, lue entree par entree dans `propositions_json` : la derniere acceptation (date, montant) et NOTRE refus
    (l'entree « refus » du 11-12/11/2026), et le travail qui l'a pose (sa source, son heure) ;
  . la VENTE du bien (par `hektor_annonce_id`, jamais par le nom) : numero, montant, date ;
  . les AUTRES offres encore acceptees sur le bien -- ⚠ en disant si c'est une offre DE HEKTOR ou une COPIE DU
    CLASSEUR (transaction_origine) : une copie du classeur n'est pas une offre acceptee chez Hektor.
ECRIT : notice/LISTE_DES_17_OFFRES_REFUSEES_A_TORT_2026-11-23.csv
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))

SES_14 = ["531/1387", "3648/8395", "6556/12728", "7780/15722", "14112/28653", "14420/29285", "17322/36794",
          "22384/44914", "22446/45081", "24159/47815", "5126/10703", "16421/34296", "18600/39032", "21600/43126"]
SES_3 = ["14008/28422", "17025/36165", "23995/47557"]
#: trouvees en route, A PART : les 2 que la cascade refuserait AUJOURD'HUI (rejeu a blanc du 23/11, 00:40), et la 18e
#: du 12/11, posee par enqueue_fermeture_dossiers_impossibles.js SUR SA DECISION dossier par dossier.
EN_ROUTE = {8018: "la cascade la REFUSERAIT AUJOURD'HUI (a blanc du 23/11) -- retenue par la garde du bien",
            13984: "la cascade la REFUSERAIT AUJOURD'HUI (a blanc du 23/11) -- retenue par la garde du bien",
            23139: "18e : refusee le 12/11 par enqueue_fermeture_dossiers_impossibles.js, SUR TA DECISION du 12/11"}
SORTIE = RACINE / "notice" / "LISTE_DES_17_OFFRES_REFUSEES_A_TORT_2026-11-23.csv"


def jour(s) -> str:
    s = str(s or "")
    return "%s/%s/%s" % (s[8:10], s[5:7], s[0:4]) if len(s) >= 10 else "?"


def euros(m) -> str:
    try:
        return "{:,}".format(int(float(str(m)))).replace(",", " ") + " EUR"
    except (TypeError, ValueError):
        return "?"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    import sauvegarde_datee_classeur as S
    cn, cu = S.connexion()
    try:
        cibles = [int(x.split("/")[0]) for x in SES_14 + SES_3] + list(EN_ROUTE)
        cu.execute("select app_affaire_id, kind, state, montant, date, hektor_affaire_id, hektor_annonce_id, "
                   "app_chaine_id, transaction_origine, propositions_json from public.app_affaire_ledger "
                   "where app_affaire_id = any(%s)", (cibles,))
        offres = {int(r[0]): r for r in cu.fetchall()}
        biens = sorted({int(r[6]) for r in offres.values() if r[6] is not None})
        cu.execute("select app_affaire_id, kind, state, montant, date, date_acte, hektor_affaire_id, hektor_annonce_id, "
                   "app_chaine_id, transaction_origine, present_in_hektor from public.app_affaire_ledger "
                   "where hektor_annonce_id = any(%s) and kind in ('vente', 'offre')", (biens,))
        du_bien = {}
        for r in cu.fetchall():
            du_bien.setdefault(int(r[7]), []).append(r)
        cu.execute("select payload_json->>'app_affaire_id', payload_json->>'origine', payload_json->>'type', status, "
                   "finished_at from public.app_console_job where job_type = 'change_hektor_offre_status' "
                   "and created_at >= '2026-11-11' and created_at < '2026-11-14'")
        travaux = {}
        for a, o, t, st, fi in cu.fetchall():
            if a:
                travaux.setdefault(int(a), []).append((o, t, st, str(fi)[:19]))
        cn.rollback()
    finally:
        cn.close()

    lignes = []
    rouges = []

    def une(cle: str, groupe: str) -> None:
        a, b = (int(x) for x in cle.split("/")) if "/" in cle else (int(cle), None)
        o = offres.get(a)
        if not o:
            rouges.append("%d introuvable" % a)
            return
        _, kind, state, montant, date, hk, bien, chaine, origine, props = o
        if b is not None and int(bien) != b:
            rouges.append("%d : bien %s au registre, %s dans ta liste" % (a, bien, b))
        props = props or []
        refus = [p for p in props if p.get("type") == "refus" and str(p.get("date", "")).startswith("2026-11-1")]
        notre_refus = refus[0] if refus else {}
        # ⚠ l'acceptation qui compte est celle d'AVANT notre refus (apres, c'est la reacceptation du 12/11)
        acc = [p for p in props if p.get("type") == "accepte" and str(p.get("date", "")) < str(notre_refus.get("date", "9"))]
        derniere_acc = acc[-1] if acc else {}
        apres = [p for p in props if str(p.get("date", "")) > str(notre_refus.get("date", "9"))]
        ventes = [v for v in du_bien.get(int(bien), []) if v[1] == "vente"]
        autres = [v for v in du_bien.get(int(bien), []) if v[1] == "offre" and v[0] != a
                  and str(v[2] or "").lower() in ("accepted", "acceptee")]
        autres_hk = [v for v in autres if not str(v[9] or "").strip()]
        autres_cl = [v for v in autres if str(v[9] or "").strip()]
        trv = travaux.get(a, [])
        def nombre(x):
            try:
                return round(float(str(x)))
            except (TypeError, ValueError):
                return None
        mv = [nombre(v[3]) for v in ventes]
        exact = derniere_acc and nombre(derniere_acc.get("montant")) in mv
        # l'ecart entre l'acceptation et la vente : une offre acceptee APRES la vente se DIT
        from datetime import date as _d
        def jj(x):
            x = str(x or "")
            try:
                return _d(int(x[0:4]), int(x[5:7]), int(x[8:10]))
            except ValueError:
                return None
        ecarts = []
        for v in ventes:
            a_, v_ = jj(derniere_acc.get("date")), jj(v[5] or v[4])
            if a_ and v_:
                ecarts.append("vente %d jours APRES l'acceptation" % (v_ - a_).days if v_ >= a_
                              else "⚠ ACCEPTEE %d JOURS APRES LA VENTE" % (a_ - v_).days)
        lignes.append({
            "groupe": groupe, "offre": a, "offre_hektor": hk, "bien": bien, "etat_aujourd_hui": state,
            "acceptee_le": jour(derniere_acc.get("date")), "montant_accepte": euros(derniere_acc.get("montant")),
            "refusee_par_nous_le": (str(notre_refus.get("date", "?"))[:16]),
            "par_le_travail": " ; ".join("%s %s %s %s" % t for t in trv) or "?",
            "rien_depuis_notre_refus": "OUI" if not apres else "NON : %s" % [p.get("type") for p in apres],
            "vente": " ; ".join("%s (n° %s) %s le %s%s" % (v[0], v[6] or "-", euros(v[3]), jour(v[5] or v[4]),
                                                          "" if v[10] is not False else " SUPPRIMEE chez Hektor")
                                for v in ventes) or "AUCUNE",
            "montant": "EXACT" if exact else "renegocie",
            "acceptation_et_vente": " ; ".join(ecarts) or "?",
            "autres_offres_acceptees_chez_hektor": " ; ".join("%s (n° %s) %s" % (v[0], v[6], euros(v[3]))
                                                              for v in autres_hk) or "AUCUNE",
            "copies_du_classeur_acceptees": " ; ".join("%s (%s)" % (v[0], v[9]) for v in autres_cl) or "-",
            "note": EN_ROUTE.get(a, ""),
        })

    for c in SES_14:
        une(c, "les 14")
    for c in SES_3:
        une(c, "les 3")
    for a in EN_ROUTE:
        une(str(a), "en route")
    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    for l in lignes:
        print("%-8s offre %-6s (n° %-5s) bien %-6s | acceptee le %s a %s | refusee par nous le %s | vente %s | %s"
              " | autres acceptees Hektor : %s | copies : %s | depuis : %s | %s" % (
                  l["groupe"], l["offre"], l["offre_hektor"], l["bien"], l["acceptee_le"], l["montant_accepte"],
                  l["refusee_par_nous_le"], l["vente"], l["montant"] + " | " + l["acceptation_et_vente"],
                  l["autres_offres_acceptees_chez_hektor"],
                  l["copies_du_classeur_acceptees"], l["rien_depuis_notre_refus"], l["par_le_travail"]))
    print("-> %s (%d lignes)" % (SORTIE, len(lignes)))
    if rouges:
        print("⛔ ROUGES : %s" % rouges)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
