#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES TABLES SATELLITES SUIVENT LE CONTACT — L'APPEL DE NUIT ET LA SONDE.   24/09/2026

La regle elle-meme (la fonction SQL) a ete prouvee dans Supabase, sur des copies
temporaires annulees (notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md).
Ici on prouve, avec un FAUX Supabase, les deux pieces qui l'appellent :

  L'ETAPE DE NUIT (phase2/identite/propager_numeros_contact.py)
    (1) elle retraduit POUR DE BON, et AVANT la propagation
    (2) --dry-run : retraduction A BLANC, et PAS de propagation
    (3) fonction absente (patch pas applique) : l'etape continue, la propagation passe
    (4) jamais d'exception brute a l'ecran
  LA SONDE (monitoring/check_gti_health.py, Monitor.check_contacts_satellites)
    (5) 0 a retraduire -> ok       (6) des lignes a retraduire -> warning
    (7) un ecart -> critical       (8) fonction absente -> info, pas d'alarme
    (9) elle appelle TOUJOURS a blanc

⚠ LA PREUVE D'ABORD : sur la version epinglee du script, il n'appelle rien --
  le test doit ECHOUER.
      python phase2/checks/test_retraduire_satellites.py --script <fichier>
N'appelle pas Supabase.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import os
import sys
from pathlib import Path
from types import SimpleNamespace

RACINE = Path(__file__).resolve().parents[2]
ECHECS: list[str] = []
TOTAL = 9
RPC = "rpc/app_contact_retraduire_satellites"


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK ' if ok else 'KO '} {nom}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        ECHECS.append(nom)


def charger(nom: str, chemin: Path):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    spec.loader.exec_module(module)
    return module


class FauxClient:
    def __init__(self, fonction_absente: bool = False, reponse: dict | None = None):
        self.appels: list[tuple] = []
        self.fonction_absente = fonction_absente
        self.reponse = reponse or {"mode": "applique", "a_traduire": 69, "traduits": 69,
                                   "sautes": 0, "ecarts": {}, "detail": {"traduits": {"app_rapprochement": 69}}}

    def request(self, *args, method="GET", path=None, payload=None, **kw):
        path = path or (args[0] if args else "")
        self.appels.append((method, path, payload))
        if path == RPC:
            if self.fonction_absente:
                raise RuntimeError("Could not find the function public.app_contact_retraduire_satellites")
            return self.reponse
        if path.startswith("app_contacts_sans_numero"):
            return []
        if path == "rpc/app_contact_id_propager":
            return {"total": 0, "detail": {}}
        return None


class Ecran(io.StringIO):
    """L'ecran du script : il appelle sys.stdout.reconfigure au demarrage."""

    def reconfigure(self, **kw):
        return None


def lancer_etape(S, client: FauxClient, *argv: str) -> tuple[int, str]:
    S.SupabaseRestClient = lambda **kw: client
    S.charge_env = lambda: None
    os.environ["SUPABASE_URL"] = "https://faux.invalid"
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "faux"
    sys.argv = ["propager_numeros_contact.py", *argv]
    sortie = Ecran()
    with contextlib.redirect_stdout(sortie):
        try:
            code = S.main()
        except Exception as exc:  # noqa: BLE001
            code = f"EXCEPTION {type(exc).__name__}"
    return code, sortie.getvalue()


def ordre(client: FauxClient) -> list[str]:
    return [p for _, p, _ in client.appels if p.startswith("rpc/")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default=str(RACINE / "phase2" / "identite" / "propager_numeros_contact.py"))
    args = ap.parse_args()
    sys.path.insert(0, str(RACINE / "phase2" / "sync"))
    S = charger("propager_sous_test", Path(args.script))
    print(f"script teste : {args.script}")

    # ── L'ETAPE DE NUIT
    c = FauxClient()
    code, out = lancer_etape(S, c)
    appel = next((pl for _, p, pl in c.appels if p == RPC), None)
    controle("(1) retraduction POUR DE BON, AVANT la propagation",
             code == 0 and ordre(c) == [RPC, "rpc/app_contact_id_propager"] and appel == {"p_appliquer": True},
             f"code {code} ; ordre {ordre(c)} ; charge {appel}")

    c = FauxClient(reponse={"mode": "a_blanc", "a_traduire": 69, "traduits": 0, "sautes": 0, "ecarts": {}})
    code, out = lancer_etape(S, c, "--dry-run")
    appel = next((pl for _, p, pl in c.appels if p == RPC), None)
    controle("(2) --dry-run : a blanc, et PAS de propagation",
             code == 0 and appel == {"p_appliquer": False} and "rpc/app_contact_id_propager" not in ordre(c),
             f"code {code} ; ordre {ordre(c)} ; charge {appel}")

    c = FauxClient(fonction_absente=True)
    code, out = lancer_etape(S, c)
    controle("(3) fonction absente : l'etape continue, la propagation passe",
             code == 0 and "rpc/app_contact_id_propager" in ordre(c), f"code {code} ; ordre {ordre(c)}")
    controle("(4) jamais d'exception brute a l'ecran",
             "Could not find" not in out and "Traceback" not in out, out[-200:])

    # ── LA SONDE
    sys.path.insert(0, str(RACINE / "monitoring"))
    M = charger("sante_sous_test", RACINE / "monitoring" / "check_gti_health.py")

    def sonde(client) -> list[tuple]:
        vus: list[tuple] = []
        faux = SimpleNamespace(supabase=client,
                               add=lambda *a, **kw: vus.append((a[4], kw.get("severity"), a[5])))
        M.Monitor.check_contacts_satellites(faux)
        return vus

    class FauxSante(FauxClient):
        def request(self, path, *, method="GET", payload=None, **kw):
            return super().request(method=method, path=path, payload=payload)

    ok = sonde(FauxSante(reponse={"a_traduire": 0, "traduisibles": 0, "sautes": 0, "ecarts": {}}))
    controle("(5) 0 a retraduire -> ok", len(ok) == 1 and ok[0][0] == "ok", str(ok))
    w = sonde(FauxSante(reponse={"a_traduire": 30, "traduisibles": 30, "sautes": 0, "ecarts": {}}))
    controle("(6) des lignes a retraduire -> warning", len(w) == 1 and w[0][0] == "warning", str(w))
    cr = sonde(FauxSante(reponse={"a_traduire": 3, "traduisibles": 1, "sautes": 1, "ecarts": {"app_rapprochement": 1}}))
    controle("(7) un ecart -> critical", len(cr) == 1 and cr[0][0] == "critical", str(cr))
    ab = sonde(FauxSante(fonction_absente=True))
    controle("(8) fonction absente -> info, pas d'alarme",
             len(ab) == 1 and ab[0][0] == "ok" and ab[0][1] == "info", str(ab))
    espion = FauxSante(reponse={"a_traduire": 0, "traduisibles": 0, "sautes": 0, "ecarts": {}})
    sonde(espion)
    controle("(9) la sonde appelle TOUJOURS a blanc",
             [pl for _, p, pl in espion.appels if p == RPC] == [{"p_appliquer": False}], str(espion.appels))

    print(f"\n{'TOUT VERT' if not ECHECS else str(len(ECHECS)) + ' ECHEC(S)'} ({TOTAL - len(ECHECS)}/{TOTAL})")
    return 1 if ECHECS else 0


if __name__ == "__main__":
    sys.exit(main())
