#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA PATIENCE DU CLIENT HEKTOR — N'APPELLE JAMAIS HEKTOR.      22/09/2026

CE QU'IL EPROUVE, et c'est la question posee par le run mort du 22/09 :
quand le serveur tousse une fois, est-ce qu'on lui laisse le temps de se
remettre, ou est-ce qu'on declare forfait ?

Il monte un FAUX serveur en memoire :
    ① un qui renvoie 500 deux fois puis 200  -> le client doit FINIR PAR REUSSIR
    ② un qui renvoie 500 toujours            -> il doit abandonner, en 40 s
    ③ un qui renvoie 403                     -> il doit lever TOUT DE SUITE,
                                                sans une seule nouvelle tentative

⚠ LE TROISIEME EST LE PLUS IMPORTANT. Le 403 est le signal de bannissement du
  projet (« 403 = refus, on s'arrete »). La patience ne doit JAMAIS s'appliquer
  a lui : insister sur un bannissement, c'est l'aggraver. Cet essai est la pour
  qu'on ne puisse pas le casser par inadvertance en retouchant les tentatives.

Les attentes sont VERIFIEES sans les subir : time.sleep est remplace par un
mouchard qui note la duree demandee. L'essai dure moins d'une seconde.

    python phase2/checks/test_patience_hektor.py
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

import requests  # noqa: E402

from hektor_pipeline import common  # noqa: E402


class FausseReponse:
    def __init__(self, code: int) -> None:
        self.status_code = code
        self.headers = {}
        self.text = "erreur simulee"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} simule", response=self)


class FausseSession:
    """Rend la suite de codes qu'on lui donne, puis 200 pour toujours."""

    def __init__(self, codes: list[int]) -> None:
        self.codes = list(codes)
        self.appels = 0

    def request(self, *_args, **_kwargs):
        self.appels += 1
        code = self.codes.pop(0) if self.codes else 200
        return FausseReponse(code)


def client_avec(codes: list[int]):
    client = object.__new__(common.HektorClient)
    client.session = FausseSession(codes)
    client.jwt = "jeton-de-test"
    client.max_retries = 4
    client.settings = type("S", (), {"base_url": "http://test", "timeout": 5})()
    client._respecter_le_plancher = lambda: None
    return client


def main() -> int:
    attentes: list[float] = []
    vrai_sleep = common.time.sleep
    common.time.sleep = lambda s: attentes.append(s)

    echecs: list[str] = []
    try:
        # ── ① il tousse deux fois, puis repond ────────────────────────────
        attentes.clear()
        c = client_avec([500, 500])
        try:
            rep = c.request("GET", "/Api/Annonce/ListAnnonces/")
            ok1 = rep.status_code == 200
        except Exception as err:
            ok1 = False
            print(f"  (detail : {type(err).__name__})")
        print(f"{'  OK  ' if ok1 else 'ECHEC '} un hoquet de deux essais est absorbe "
              f"-- {c.session.appels} appels, attentes {attentes}")
        if not ok1:
            echecs.append("le client abandonne alors que le serveur s'etait remis")
        if attentes[:2] != [2.0, 8.0]:
            echecs.append(f"les attentes devraient etre 2 s puis 8 s, pas {attentes[:2]}")

        # ── ② il tousse toujours ──────────────────────────────────────────
        attentes.clear()
        c = client_avec([500] * 10)
        try:
            c.request("GET", "/Api/Annonce/ListAnnonces/")
            ok2 = False
        except RuntimeError:
            ok2 = True
        total = sum(attentes)
        print(f"{'  OK  ' if ok2 else 'ECHEC '} un serveur durablement casse fait abandonner "
              f"-- {c.session.appels} appels, {total:.0f} s de patience")
        if not ok2:
            echecs.append("le client n'abandonne jamais")
        if total < 35:
            echecs.append(f"la patience totale est de {total:.0f} s, on en attend ~40")

        # ── ③ LE 403 : PAS DE PATIENCE, PAS UNE SEULE NOUVELLE TENTATIVE ──
        attentes.clear()
        c = client_avec([403])
        try:
            c.request("GET", "/Api/Annonce/ListAnnonces/")
            ok3 = False
        except common.HektorNonRetryableError:
            ok3 = True
        except Exception:
            ok3 = False
        print(f"{'  OK  ' if ok3 else 'ECHEC '} un 403 leve IMMEDIATEMENT "
              f"-- {c.session.appels} appel, {len(attentes)} attente(s)")
        if not ok3:
            echecs.append("un 403 n'est plus traite comme un refus immediat")
        if c.session.appels != 1 or attentes:
            echecs.append("on insiste apres un 403 -- c'est exactement ce qui fait bannir")
    finally:
        common.time.sleep = vrai_sleep

    print("")
    if echecs:
        for e in echecs:
            print(f"  - {e}")
        return 1
    print("3 controles passes : patient avec un hoquet, ferme avec un refus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
