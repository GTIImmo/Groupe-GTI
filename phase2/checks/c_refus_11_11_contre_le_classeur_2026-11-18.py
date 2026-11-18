#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LES REFUS DU 11/11 JUGES PAR LE CLASSEUR -- une source INDEPENDANTE. 18/11/2026

    .venv\Scripts\python.exe -X utf8 phase2\checks\c_refus_11_11_contre_le_classeur_2026-11-18.py

⛔ CE SCRIPT N'ECRIT RIEN. Lecture seule : des GET chez Supabase + le CSV du gel.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI, ET POURQUOI LE CRITERE D'HIER NE SUFFIT PAS
═══════════════════════════════════════════════════════════════════════════════
Le 11/11 a 19:01, `rattrapage_cascade_annulation` a refuse 661 offres chez Hektor,
sur le seul critere « le compromis de la chaine est annule ». 19 ont ete reparees
le 12/11 ; 642 sont encore refusees.

⭐ Mon premier controle disait : « aucune des 642 n'a de vente dans sa chaine, donc
  le refus est coherent ». ⛔ IL TOURNE EN ROND : la chaine et l'etat du compromis
  viennent tous deux de HEKTOR. Si Hektor marque un compromis « annule » A TORT,
  le controle approuve le refus avec la meme donnee fausse qui l'a cause.

⭐⭐ LE CAS QUI L'A REVELE -- 43091, trouve par Frederic le 18/11 :
      Hektor   compromis 17016 status 2 = ANNULE   (lu en direct le 18/11)
      le Sheet « Vente réglée », vente reglee le 31/07/2026, facture GGTI00004406,
               ET AUCUNE DATE D'ANNULATION (colonne Z vide : absent des 897 de C3)
      et la vente 23266 existe, 65 000 EUR, meme mandat, meme acquereur.
    Le compromis a donc abouti. C'est sa marque chez Hektor qui est fausse.

⭐⭐⭐ D'OU LE JUGE DE CE SCRIPT : LE CLASSEUR, qui ne vient pas de Hektor. Pour
  chaque offre encore refusee, on lit ce que le Sheet dit de SA chaine.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
import check_gti_health as cgh                                      # noqa: E402

#: ⚠ le rapport le PLUS FRAIS -- le classeur bouge, et un rapport perime
#:   ferait juger sur l'etat d'hier.
RAPPORT = RACINE / "notice" / "A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-11-17.csv"
SORTIE = RACINE / "notice" / "C_REFUS_11_11_JUGES_PAR_LE_CLASSEUR_2026-11-18.csv"
LOT_API = 60

#: Les etats du classeur qui disent « l'affaire a ABOUTI ». Un refus d'offre sur
#: une de ces lignes contredit le Sheet.
ETATS_ABOUTIS = {"Vente réglée", "Vendu", "Acte signé"}


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- rien n'est mesure.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def pages(cl, table, select, filtres=None, cle_tri="app_affaire_id"):
    """Toutes les lignes, par paquets -- jamais un `limit` muet."""
    out, apres = [], 0
    while True:
        p = dict(filtres or {})
        p.update({"select": select, cle_tri: "gt.%d" % apres,
                  "order": cle_tri + ".asc", "limit": "1000"})
        page = cl.get(table, p) or []
        if not page:
            return out
        out.extend(page)
        apres = int(page[-1][cle_tri])


def par_lots(cl, table, select, colonne, valeurs, citer=False):
    out = []
    valeurs = sorted(set(valeurs))
    for i in range(0, len(valeurs), LOT_API):
        lot = valeurs[i:i + LOT_API]
        rendu = ",".join(('"%s"' % v) if citer else str(v) for v in lot)
        out.extend(cl.get(table, {"select": select, colonne: "in.(%s)" % rendu}) or [])
    return out


def main() -> int:
    if not RAPPORT.exists():
        print("⛔ le rapport du gel manque : %s" % RAPPORT)
        return 2
    cl = client()

    # ── ① LES OFFRES VISEES LE 11/11, prises au JOURNAL DES TRAVAUX ───────────
    # ⛔⛔ 18/11 : la premiere version demandait `limit=5000` et croyait tout lire.
    #   PostgREST PLAFONNE A 1 000 LIGNES et ne le dit pas : j'ai obtenu 444 offres
    #   au lieu de 661, et le compte avait l'air plausible. On PAGINE, au curseur
    #   sur `created_at`, et on VERIFIE le total contre un temoin.
    # ⛔ ET LE CURSEUR SUR `created_at` EN RATAIT 6 DE PLUS : les 661 travaux ont
    #   ete poses en 1,4 seconde, plusieurs PARTAGENT la meme microseconde, et un
    #   `gt.` saute les ex-aequo du bord de page. On pagine par DECALAGE, sur un
    #   ordre stable (created_at PUIS id, qui est unique).
    jobs, decalage = [], 0
    while True:
        page = cl.get("app_console_job", {
            "select": "id,created_at,payload_json",
            "job_type": "eq.change_hektor_offre_status",
            "order": "created_at.asc,id.asc",
            "offset": str(decalage), "limit": "1000"}) or []
        if not page:
            break
        jobs.extend(page)
        decalage += len(page)
    visees = set()
    for j in jobs:
        p = j.get("payload_json") or {}
        if str(p.get("origine") or "") == "rattrapage_cascade_annulation":
            o = str(p.get("hektor_offre_id") or "").strip()
            if o:
                visees.add(o)
    print("① travaux change_hektor_offre_status lus  : %d" % len(jobs))
    print("① offres visees par le rattrapage du 11/11 : %d" % len(visees))
    #: ⭐ LE TEMOIN : la mesure SQL du 18/11 en comptait 661. Moins, c'est une
    #:   lecture ratee -- et une lecture ratee n'est JAMAIS un vert.
    if len(visees) < 661:
        print("⛔ %d visees au lieu des 661 mesurees en SQL -- LECTURE INCOMPLETE."
              % len(visees))
        return 2
    if not visees:
        print("⛔ aucune -- lecture ratee, ce n'est PAS un vert.")
        return 2

    # ── ② CELLES QUI SONT ENCORE REFUSEES AUJOURD'HUI ─────────────────────────
    lignes = par_lots(cl, "app_affaire_ledger",
                      "app_affaire_id,hektor_affaire_id,hektor_annonce_id,app_chaine_id,kind,state",
                      "hektor_affaire_id", visees, citer=True)
    refusees = [x for x in lignes
                if x["kind"] == "offre" and str(x.get("state") or "") == "refused"
                and str(x.get("hektor_affaire_id") or "") in visees]
    print("② encore refusees aujourd'hui            : %d" % len(refusees))
    chaines = {x["app_chaine_id"] for x in refusees if x.get("app_chaine_id") is not None}

    # ── ③ TOUTES LES TRANSACTIONS DE CES CHAINES, puis leurs liens au classeur ─
    membres = par_lots(cl, "app_affaire_ledger",
                       "app_affaire_id,app_chaine_id,kind,state",
                       "app_chaine_id", chaines)
    liens = par_lots(cl, "app_classeur_lien", "app_affaire_id,id_unique,role",
                     "app_affaire_id", [m["app_affaire_id"] for m in membres])
    chaine_de = {m["app_affaire_id"]: m["app_chaine_id"] for m in membres}
    ids_par_chaine: dict[int, set[str]] = {}
    for l in liens:
        ch = chaine_de.get(l["app_affaire_id"])
        if ch is not None:
            ids_par_chaine.setdefault(ch, set()).add(str(l["id_unique"]))
    print("③ chaines concernees %d, dont reliees au classeur %d"
          % (len(chaines), len(ids_par_chaine)))

    # ── ④ CE QUE LE SHEET DIT DE CES LIGNES -- LE JUGE INDEPENDANT ────────────
    with RAPPORT.open(encoding="utf-8-sig", newline="") as f:
        classeur = {str(l["ID Unique"]).strip(): l for l in csv.DictReader(f, delimiter=";")}
    print("④ lignes du classeur lues                : %d" % len(classeur))

    verdicts = Counter()
    detail = []
    for o in refusees:
        ch = o.get("app_chaine_id")
        ids = ids_par_chaine.get(ch, set())
        if not ids:
            verdicts["aucune ligne du classeur reliee -- le Sheet ne dit rien"] += 1
            continue
        etats, factures, annul = set(), set(), set()
        for i in ids:
            c = classeur.get(i)
            if not c:
                continue
            etats.add((c.get("c_Etat Actuel") or "").strip())
            if (c.get("c_Numero de facture") or "").strip():
                factures.add((c.get("c_Numero de facture") or "").strip())
            if (c.get("c_Vente Reglee") or "").strip():
                annul.add((c.get("c_Vente Reglee") or "").strip())
        abouti = bool(etats & ETATS_ABOUTIS) or bool(factures)
        if abouti:
            verdicts["⛔ LE CLASSEUR DIT QUE L'AFFAIRE A ABOUTI -- refus a revoir"] += 1
            detail.append({
                "offre_hektor": o.get("hektor_affaire_id"), "annonce": o.get("hektor_annonce_id"),
                "chaine": ch, "id_uniques": "|".join(sorted(ids)),
                "etat_classeur": "|".join(sorted(e for e in etats if e)),
                "numero_facture": "|".join(sorted(factures)),
                "vente_reglee": "|".join(sorted(annul))})
        elif etats:
            verdicts["le classeur ne dit pas abouti (%s)"
                     % " / ".join(sorted(e for e in etats if e)[:2])] += 1
        else:
            verdicts["ligne reliee mais introuvable dans le rapport"] += 1

    print()
    print("=== ⑤ LE VERDICT DU CLASSEUR SUR LES %d REFUS ===" % len(refusees))
    for k, v in verdicts.most_common():
        print("   %-64s %4d" % (k[:64], v))

    if detail:
        champs = list(detail[0].keys())
        with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=champs, delimiter=";")
            w.writeheader()
            w.writerows(detail)
        print()
        print("⛔ %d refus a revoir -- la liste nommee est dans :" % len(detail))
        print("   %s" % SORTIE)

    # ⭐ LE TEMOIN POSITIF : sans lui, un « 0 » ne se croit pas. Si AUCUNE ligne
    #   du classeur n'a ete lue, c'est une lecture ratee, pas un resultat.
    if not ids_par_chaine:
        print("⛔ aucune chaine reliee au classeur : LECTURE RATEE, pas un vert.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
