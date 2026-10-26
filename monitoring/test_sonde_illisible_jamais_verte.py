#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPREUVE : une lecture ratee n'est JAMAIS un vert (26/10/2026).

LE DEFAUT. Trois sondes (cron.health, workers.heartbeat, data.contacts_satellites)
transformaient TOUTE erreur en « ok, en attente de migration » -- un repli de juillet,
migrations posees depuis. Mesure sur 362 passages (26/09 -> 26/10) : la sonde pg_cron
a ete coupee a 8 s (57014) 146 fois, et l'ecran a affiche VERT a chaque fois.

ET LE TROU VOISIN. Une tache pg_cron ACTIVE sans aucun passage connu etait ignoree
(`age is not None`). Depuis qu'app_cron_health ne lit plus que les ~50 000 derniers
passages, une tache morte au-dela de la fenetre arriverait ainsi : elle doit sonner.

AUCUN APPEL RESEAU : le client Supabase est imite.
    python monitoring/test_sonde_illisible_jamais_verte.py
"""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_gti_health as cgh  # noqa: E402

# Les CHECK de app_monitor_status (lus en base le 26/10) : une ligne refusee fait
# tomber TOUT le lot (memoire « nouvelle ligne du moniteur : lire les CHECK »).
DOMAINES = {"system", "business", "mixed", "data_quality", "workers", "cron", "surface", "scheduledtasks", "email"}
STATUTS = {"ok", "warning", "critical", "unknown"}
SEVERITES = {"info", "warning", "critical", "unknown"}

COUPURE = RuntimeError(
    'Supabase HTTP 500 on rpc/app_cron_health: {"code":"57014","message":"canceling statement due to statement timeout"}'
)


class FauxSupabase:
    def __init__(self, *, erreur=None, lignes=None):
        self.erreur = erreur
        self.lignes = lignes

    def request(self, path, **_):
        if self.erreur:
            raise self.erreur
        return self.lignes

    def get(self, path, params=None):
        if self.erreur:
            raise self.erreur
        return self.lignes


def _moniteur(supabase) -> cgh.Monitor:
    args = argparse.Namespace(project_root=".", cron_stale_minutes=30, worker_stale_default_minutes=180)
    return cgh.Monitor(args, supabase)


def _il_y_a(minutes: float) -> str:
    return cgh.iso_utc(cgh.utc_now() - timedelta(minutes=minutes))


def _par_cle(m: cgh.Monitor) -> dict:
    return {r.status_key: r for r in m.results}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    echecs: list[str] = []

    def verifier(titre: str, cond: bool, detail: str = "") -> None:
        print(f"  {'OK ' if cond else 'NON'}  {titre}" + (f"  -- {detail}" if detail and not cond else ""))
        if not cond:
            echecs.append(titre)

    def lignes_valides(m: cgh.Monitor) -> bool:
        return all(r.domain in DOMAINES and r.status in STATUTS and r.severity in SEVERITES for r in m.results)

    print("1. pg_cron coupe a 8 s -> « illisible », jamais vert")
    m = _moniteur(FauxSupabase(erreur=COUPURE))
    m.check_cron_health()
    r = _par_cle(m).get("cron.health")
    verifier("statut unknown", r is not None and r.status == "unknown", r and r.status)
    verifier("severite unknown", r is not None and r.severity == "unknown")
    verifier("le message dit illisible et garde le 57014", r is not None and "illisible" in r.message and "57014" in r.message)
    verifier("plus de « en attente de migration »", r is not None and "migration" not in r.message)
    verifier("ligne acceptee par les CHECK", lignes_valides(m))

    print("2. pg_cron lisible, tout va bien -> ok")
    m = _moniteur(FauxSupabase(lignes=[
        {"jobname": "rapprochement-dirty", "active": True, "schedule": "*/1 * * * *", "last_run": _il_y_a(1), "last_status": "succeeded"},
        {"jobname": "app-sweep-search-orphans", "active": True, "schedule": "0 5 * * *", "last_run": _il_y_a(120), "last_status": "succeeded"},
    ]))
    m.check_cron_health()
    r = _par_cle(m)["cron.health"]
    verifier("statut ok, 0 anomalie", r.status == "ok" and r.details.get("problem_count") == 0, r.message)

    print("3. tache ACTIVE sans passage connu (hors fenetre) -> anomalie")
    m = _moniteur(FauxSupabase(lignes=[
        {"jobname": "app-photo-sortie-vitrine", "active": True, "schedule": "30 8 * * *", "last_run": None, "last_status": None},
    ]))
    m.check_cron_health()
    d = _par_cle(m)
    verifier("cron.health en warning", d["cron.health"].status == "warning", d["cron.health"].message)
    verifier("la tache a sa ligne « aucun passage connu »",
             "cron.health:app_photo_sortie_vitrine" in d and "aucun passage" in d["cron.health:app_photo_sortie_vitrine"].message)
    verifier("lignes acceptees par les CHECK", lignes_valides(m))

    print("4. tache INACTIVE sans passage -> toujours ignoree (comme avant)")
    m = _moniteur(FauxSupabase(lignes=[
        {"jobname": "vieille-tache", "active": False, "schedule": "0 1 * * *", "last_run": None, "last_status": None},
    ]))
    m.check_cron_health()
    verifier("ok", _par_cle(m)["cron.health"].status == "ok")

    print("5. echec et retard : inchanges")
    m = _moniteur(FauxSupabase(lignes=[
        {"jobname": "a", "active": True, "schedule": "*/1 * * * *", "last_run": _il_y_a(1), "last_status": "failed"},
        {"jobname": "b", "active": True, "schedule": "*/1 * * * *", "last_run": _il_y_a(300), "last_status": "succeeded"},
    ]))
    m.check_cron_health()
    d = _par_cle(m)
    verifier("echec signale", "dernier run en echec" in d["cron.health:a"].message)
    verifier("retard signale", "pas de run depuis" in d["cron.health:b"].message)

    print("6. heartbeat workers illisible -> « illisible », jamais vert")
    m = _moniteur(FauxSupabase(erreur=RuntimeError("Supabase HTTP 500 on app_worker_registry: 57014")))
    m.check_worker_heartbeat()
    r = _par_cle(m).get("workers.heartbeat")
    verifier("statut unknown", r is not None and r.status == "unknown", r and r.status)
    verifier("ligne acceptee par les CHECK", lignes_valides(m))

    print("7. satellites des contacts illisibles -> « illisible », jamais vert")
    m = _moniteur(FauxSupabase(erreur=RuntimeError("Supabase HTTP 500 on rpc/app_contact_retraduire_satellites: 57014")))
    m.check_contacts_satellites()
    r = _par_cle(m).get("data.contacts_satellites")
    verifier("statut unknown", r is not None and r.status == "unknown", r and r.status)
    verifier("ligne acceptee par les CHECK", lignes_valides(m))

    print()
    if echecs:
        print(f"ECHEC : {len(echecs)} verification(s) rouge(s)")
        return 1
    print("TOUT EST VERT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
