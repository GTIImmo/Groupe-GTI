#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""TEMPS 1 DU CHANTIER CLASSEUR -- NOS GESTES DE MASSE SUR LES TRANSACTIONS.   19/11/2026

    .venv\Scripts\python.exe -X utf8 phase2\checks\temps1_inventaire_gestes_de_masse_2026-11-19.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Des GET chez Supabase, et un CSV dans notice/.

LA QUESTION (Frederic, 19/11) : quelles ecritures de masse ont touche le registre des
transactions, d'apres LE JOURNAL DES TRAVAUX (app_console_job) et non d'apres les notes ?

CE QU'IL PRODUIT -- une ligne par geste, l'entree du temps 3 (le rejeu du chainage) :
    notice/TEMPS1_GESTES_DE_MASSE_2026-11-19.csv
    campagne . script d'origine . quand . le genre . les numeros . etat_avant (lu dans la
    charge, ou RECONSTITUE et dit tel) . etat_apres . l'etat AUJOURD'HUI . et si HEKTOR
    porte le geste dans son propre journal de l'offre (propositions_json).

⭐ LE JUGE QUI NE VIENT PAS DE NOUS. Le script de refus a lui-meme pose `state` dans le
  registre (PATCH, etape 7 de enqueue_refus_offres_mortes_lot.js) : l'etat du registre ne
  prouve donc rien seul. Le journal de l'offre, lui, n'est ecrit que par HEKTOR et relu
  la nuit -- une entree « refus » ou « accepte » datee du 10/11 ou apres est la preuve que
  Hektor a fait le geste.

LES DEUX TEMOINS (un zero ne se croit pas sans temoin positif) :
    POSITIF   les 19 offres reacceptees le 12/11 DOIVENT sortir « etat change » sur leur
              geste du 11/11 : la mesure sait voir un etat qui n'a pas tenu.
    INVERSE   les offres refusees QUE NOUS N'AVONS PAS TOUCHEES doivent, en tres grande
              majorite, porter un refus ANCIEN : la mesure sait dire « ce n'est pas nous ».

Sortie : 0 tout est mesure et coherent . 1 une anomalie nommee . 2 pas pu mesurer.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
import check_gti_health as cgh                                      # noqa: E402

SORTIE = RACINE / "notice" / "TEMPS1_GESTES_DE_MASSE_2026-11-19.csv"
DEPUIS = "2026-11-10"
TYPES = ("change_hektor_offre_status", "cancel_hektor_compromis")
LOT_API = 60

#: La campagne -> le script qui l'a posee. Lu dans le code le 19/11, pas dans les notes.
SCRIPTS = {
    "enqueue_refus_offres_mortes_lot":
        "Console/enqueue_refus_offres_mortes_lot.js --source table",
    "rattrapage_cascade_annulation":
        "Console/enqueue_refus_offres_mortes_lot.js --source cascade",
    "enqueue_fermeture_dossiers_impossibles":
        "Console/enqueue_fermeture_dossiers_impossibles.js",
    "Frederic -- alerte du 12/11/2026 sur le dossier 3676":
        "Console/enqueue_reaccepter_offres_refusees_a_tort.js",
    "cascade_annulation_compromis":
        "RPC app_geste_affaire_optimistic (supabase/patch_cascade_annulation_2026-11-11.sql)"
        " -- consequence AUTOMATIQUE d'un geste HUMAIN",
}


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- rien n'est mesure.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=60)


def tous(cl, table, params):
    """Toutes les lignes, par pages de 1 000 -- jamais un `limit` muet."""
    out, debut = [], 0
    while True:
        p = dict(params)
        p.update({"limit": "1000", "offset": str(debut)})
        page = cl.get(table, p) or []
        out.extend(page)
        if len(page) < 1000:
            return out
        debut += 1000


def par_lots(cl, table, select, colonne, valeurs):
    out = []
    valeurs = sorted(set(valeurs))
    for i in range(0, len(valeurs), LOT_API):
        lot = valeurs[i:i + LOT_API]
        out.extend(cl.get(table, {"select": select,
                                  colonne: "in.(%s)" % ",".join(str(v) for v in lot)}) or [])
    return out


def journal(propositions) -> list[dict]:
    if isinstance(propositions, str):
        try:
            propositions = json.loads(propositions)
        except ValueError:
            return []
    return propositions if isinstance(propositions, list) else []


def main() -> int:
    cl = client()

    # ── 1. LE JOURNAL DES TRAVAUX ────────────────────────────────────────────────
    travaux = tous(cl, "app_console_job", {
        "select": "id,job_type,status,created_at,finished_at,requested_by,payload_json,result_json",
        "job_type": "in.(%s)" % ",".join(TYPES),
        "created_at": "gte.%s" % DEPUIS,
        "order": "created_at.asc,id.asc"})
    gestes = []
    for j in travaux:
        p = j.get("payload_json") or {}
        origine = p.get("origine") or p.get("source") or ""
        humain = j.get("requested_by") is not None
        # Les campagnes sont les travaux SANS auteur ; on garde la seule cascade
        # automatique d'un geste humain, parce que le dossier du 19/11 la comptait.
        if humain and origine != "cascade_annulation_compromis":
            continue
        gestes.append({
            "job_id": j["id"], "job_type": j["job_type"], "statut_travail": j.get("status"),
            "cree_le": j.get("created_at"), "fini_le": j.get("finished_at"),
            "campagne": origine or "(sans origine)",
            "script": SCRIPTS.get(origine, "?"),
            "auteur": "humain" if humain else "script",
            "app_affaire_id": int(p["app_affaire_id"]) if p.get("app_affaire_id") is not None else None,
            "hektor_id": p.get("hektor_offre_id") or p.get("hektor_compromis_id") or "",
            "hektor_annonce_id": p.get("hektor_annonce_id") or "",
            "geste": p.get("type") or ("annulation" if j["job_type"] == "cancel_hektor_compromis" else ""),
            "etat_avant_cle": "etat_avant" in p,
            "etat_avant": p.get("etat_avant"),
            "etat_apres": p.get("etat_apres") or "",
            "decide_par": p.get("decide_par") or "",
            "registre_lignes": (j.get("result_json") or {}).get("registre_lignes"),
        })
    if not gestes:
        print("⛔ aucun geste lu -- la lecture a echoue ou le filtre ne mesure rien (code 2).")
        return 2

    # ── 2. LE REGISTRE, pour ces transactions ────────────────────────────────────
    ids = [g["app_affaire_id"] for g in gestes if g["app_affaire_id"] is not None]
    lignes = par_lots(cl, "app_affaire_ledger",
                      "app_affaire_id,kind,state,date,present_in_hektor,hektor_affaire_id,"
                      "hektor_annonce_id,app_chaine_id,app_dossier_uuid,transaction_origine,"
                      "propositions_json", "app_affaire_id", ids)
    registre = {int(l["app_affaire_id"]): l for l in lignes}

    # ── 3. L'ETAT D'AVANT : lu, ou reconstitue -- et DIT ─────────────────────────
    precedent: dict[int, dict] = {}
    for g in gestes:                                  # deja dans l'ordre du temps
        a = g["app_affaire_id"]
        if g["etat_avant_cle"]:
            g["etat_avant_source"] = "charge"
            g["etat_avant_lu"] = g["etat_avant"] if g["etat_avant"] is not None else "(vide)"
        elif a in precedent:
            g["etat_avant_source"] = "reconstitue (geste %s)" % precedent[a]["job_id"]
            g["etat_avant_lu"] = precedent[a]["etat_apres"]
        else:
            g["etat_avant_source"] = "INCONNU"
            g["etat_avant_lu"] = ""
        if a is not None:
            precedent[a] = g

    # ── 4. LE GESTE TIENT-IL ? ET HEKTOR LE PORTE-T-IL ? ─────────────────────────
    dernier_par_aff = {g["app_affaire_id"]: g for g in gestes}
    for g in gestes:
        l = registre.get(g["app_affaire_id"])
        g["au_registre"] = l is not None
        g["genre"] = (l or {}).get("kind") or ""
        g["etat_aujourdhui"] = (l or {}).get("state") or ""
        g["date_aujourdhui"] = (l or {}).get("date") or ""
        g["present_chez_hektor"] = (l or {}).get("present_in_hektor")
        g["numero_coherent"] = l is not None and str(l.get("hektor_affaire_id") or "") == str(g["hektor_id"])
        g["chaine_aujourdhui"] = (l or {}).get("app_chaine_id") or ""
        g["etiquette_aujourdhui"] = (l or {}).get("app_dossier_uuid") or ""
        g["dernier_geste"] = dernier_par_aff.get(g["app_affaire_id"]) is g
        attendu = {"refus": "refus", "accepte": "accepte"}.get(g["geste"])
        entrees = journal((l or {}).get("propositions_json"))
        if attendu:
            g["journal_hektor_porte_le_geste"] = any(
                e.get("type") == attendu and str(e.get("date") or "") >= DEPUIS for e in entrees)
            g["entrees_datees_avant_le_geste"] = sum(
                1 for e in entrees if e.get("date") and str(e["date"]) < DEPUIS)
        else:
            g["journal_hektor_porte_le_geste"] = None   # un compromis n'a pas de journal
            g["entrees_datees_avant_le_geste"] = None
        g["date_deplacee_au_geste"] = str(g["date_aujourdhui"] or "") >= DEPUIS
        if g["etat_aujourdhui"] == g["etat_apres"]:
            g["verdict"] = "tenu"
        elif not g["dernier_geste"]:
            g["verdict"] = "defait par un geste suivant"
        else:
            g["verdict"] = "NON TENU"

    # ── 5. LES TEMOINS ───────────────────────────────────────────────────────────
    defaits = [g for g in gestes if g["verdict"] == "defait par un geste suivant"]
    temoin_positif = len(defaits) == 19
    touchees = set(ids)
    refusees = tous(cl, "app_affaire_ledger", {
        "select": "app_affaire_id,transaction_origine,propositions_json",
        "kind": "eq.offre", "state": "eq.refused", "order": "app_affaire_id.asc"})
    inverse = Counter()
    for r in refusees:
        if int(r["app_affaire_id"]) in touchees:
            continue
        e = journal(r.get("propositions_json"))
        refus = [x for x in e if x.get("type") == "refus"]
        if not refus:
            inverse["sans entree refus" + (" (classeur)" if r.get("transaction_origine") else "")] += 1
        elif any(str(x.get("date") or "") >= DEPUIS for x in refus):
            inverse["refus depuis le 10/11"] += 1
        else:
            inverse["refus ancien seulement"] += 1
    temoin_inverse = inverse["refus ancien seulement"] > 10 * max(1, inverse["refus depuis le 10/11"])

    # ── 6. LE CSV ────────────────────────────────────────────────────────────────
    colonnes = ["campagne", "script", "auteur", "job_type", "job_id", "statut_travail", "cree_le",
                "fini_le", "app_affaire_id", "hektor_id", "hektor_annonce_id", "genre", "geste",
                "etat_avant_lu", "etat_avant_source", "etat_apres", "etat_aujourdhui", "verdict",
                "journal_hektor_porte_le_geste", "entrees_datees_avant_le_geste",
                "date_aujourdhui", "date_deplacee_au_geste", "present_chez_hektor",
                "numero_coherent", "registre_lignes", "decide_par", "chaine_aujourdhui",
                "etiquette_aujourdhui"]
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colonnes, extrasaction="ignore")
        w.writeheader()
        for g in gestes:
            w.writerow(g)

    # ── 7. LE COMPTE RENDU ───────────────────────────────────────────────────────
    par_campagne = defaultdict(list)
    for g in gestes:
        par_campagne[(g["campagne"], g["job_type"])].append(g)
    print("GESTES LUS : %d . transactions distinctes : %d" % (len(gestes), len(set(ids))))
    for (camp, jt), gs in par_campagne.items():
        t = Counter("%s->%s" % (g["etat_avant_lu"] or "?", g["etat_apres"]) for g in gs)
        v = Counter(g["verdict"] for g in gs)
        jh = Counter(str(g["journal_hektor_porte_le_geste"]) for g in gs)
        print("  %-55s %-27s %4d  %s  %s  journal Hektor %s" % (
            camp[:55], jt, len(gs), dict(t), dict(v), dict(jh)))
    anomalies = [g for g in gestes if g["verdict"] == "NON TENU" or not g["au_registre"]
                 or not g["numero_coherent"] or g["statut_travail"] != "done"
                 or g["journal_hektor_porte_le_geste"] is False or g["etat_avant_source"] == "INCONNU"]
    print("TEMOIN POSITIF (19 defaits par la reacceptation) : %d -> %s" % (
        len(defaits), "OK" if temoin_positif else "ECHEC"))
    print("TEMOIN INVERSE (offres refusees non touchees) : %s -> %s" % (
        dict(inverse), "OK" if temoin_inverse else "ECHEC"))
    print("ANOMALIES : %d" % len(anomalies))
    for g in anomalies[:20]:
        print("   ", g["campagne"], g["app_affaire_id"], g["verdict"], g["statut_travail"])
    print("CSV : %s" % SORTIE)
    if not (temoin_positif and temoin_inverse):
        return 2
    return 1 if anomalies else 0


if __name__ == "__main__":
    sys.exit(main())
