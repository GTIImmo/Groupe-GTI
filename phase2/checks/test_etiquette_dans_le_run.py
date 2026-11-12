#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B4 — L'EPREUVE DE LA POSE DES ETIQUETTES DANS LE RUN.          12/11/2026

HORS LIGNE DE BOUT EN BOUT. Aucun reseau, aucune base, aucun Hektor : le client
est un FAUX qui note ce qu'on lui demande. On eprouve la vraie fonction du run,
`poser_les_etiquettes_de_dossier`, pas une copie.

CE QU'ON EPROUVE, ET CHAQUE POINT A SON TEMOIN INVERSE :
    1. ETEINT   -> elle ne touche a RIEN (0 appel) et le dit
    2. ALLUME   -> elle appelle la BONNE route, et lit les quatre gestes
    3. ECHEC    -> le client leve : elle NE LEVE PAS, elle dit l'echec
    4. ILLISIBLE-> compte rendu d'une forme inconnue : dit, jamais devine
    5. FUSIONS  -> au-dela du seuil, la ligne est criee
    6. L'ORDRE  -> dans le run, la pose est APRES les chaines et AVANT la redescente

    .venv\\Scripts\\python.exe phase2\\checks\\test_etiquette_dans_le_run.py
"""
from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync import affaire_ledger as AL  # noqa: E402


class FauxClient:
    """Il note ce qu'on lui demande et rend ce qu'on lui a dit de rendre."""

    def __init__(self, reponse=None, leve=False):
        self.appels: list[tuple[str, str]] = []
        self.reponse = reponse
        self.leve = leve

    def _request(self, method=None, path=None, **_):
        self.appels.append((method, path))
        if self.leve:
            raise RuntimeError("Supabase a refuse (essai)")
        return self.reponse


LES_QUATRE_GESTES = [
    {"geste": "pose", "dossiers": 3, "lignes": 7},
    {"geste": "propagation", "dossiers": 2, "lignes": 2},
    {"geste": "fusion", "dossiers": 1, "lignes": 2},
    {"geste": "scission", "dossiers": 0, "lignes": 0},
]


def joue(client, allume: bool) -> tuple[dict, str]:
    """Joue la vraie fonction, interrupteur pose a la main, et rend (resultat, journal)."""
    avant = os.environ.get("APP_ETIQUETTE_DOSSIER")
    os.environ["APP_ETIQUETTE_DOSSIER"] = "1" if allume else "0"
    sortie = io.StringIO()
    try:
        with redirect_stdout(sortie):
            res = AL.poser_les_etiquettes_de_dossier(client)
    finally:
        if avant is None:
            os.environ.pop("APP_ETIQUETTE_DOSSIER", None)
        else:
            os.environ["APP_ETIQUETTE_DOSSIER"] = avant
    return res, sortie.getvalue()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                               # noqa: BLE001
        pass

    rates: list[str] = []

    def exige(nom: str, condition: bool, vu: str = "") -> None:
        print(f"  {'OK  ' if condition else 'RATE'}  {nom}{(' -- ' + vu) if vu else ''}")
        if not condition:
            rates.append(nom)

    print("1. ETEINT -- elle ne doit RIEN faire")
    c = FauxClient(reponse=LES_QUATRE_GESTES)
    res, journal = joue(c, allume=False)
    exige("aucun appel au serveur", len(c.appels) == 0, f"{len(c.appels)} appel(s)")
    exige("elle le DIT dans son resultat", res == {"actif": False}, repr(res))
    exige("elle n'ecrit rien au journal", journal.strip() == "", repr(journal[:60]))

    print("2. ALLUME -- la bonne route, et les quatre gestes lus")
    c = FauxClient(reponse=LES_QUATRE_GESTES)
    res, journal = joue(c, allume=True)
    exige("UN seul appel", len(c.appels) == 1, f"{len(c.appels)}")
    exige("methode POST", c.appels and c.appels[0][0] == "POST", str(c.appels[:1]))
    exige("route rpc/app_poser_etiquettes_dossier",
          c.appels and c.appels[0][1] == "rpc/app_poser_etiquettes_dossier", str(c.appels[:1]))
    exige("pose 3", res.get("pose") == 3, str(res.get("pose")))
    exige("propagation 2", res.get("propagation") == 2, str(res.get("propagation")))
    exige("fusion 1", res.get("fusion") == 1, str(res.get("fusion")))
    exige("scission 0", res.get("scission") == 0, str(res.get("scission")))
    exige("les lignes aussi", res.get("pose_lignes") == 7, str(res.get("pose_lignes")))
    exige("elle DIT ses chiffres", "etiquettes :" in journal, repr(journal[:90]))
    exige("1 fusion NE crie PAS (sous le seuil)",
          "ATTENTION" not in journal, repr(journal[:90]))

    print("3. TEMOIN INVERSE -- le serveur refuse : elle NE LEVE PAS")
    c = FauxClient(leve=True)
    try:
        res, journal = joue(c, allume=True)
        a_leve = False
    except Exception as souci:                                      # noqa: BLE001
        res, journal, a_leve = {}, "", True
        print(f"      (elle a leve : {souci!r})")
    exige("elle ne leve pas", not a_leve)
    exige("elle dit l'echec", bool(res.get("echec")), str(res.get("echec"))[:60])
    exige("et elle le CRIE au journal", "a echoue" in journal, repr(journal[:90]))
    exige("le run CONTINUE est annonce", "CONTINUE" in journal, repr(journal[:90]))

    print("4. TEMOIN INVERSE -- compte rendu d'une forme inconnue")
    for forme in (None, 0, "bonjour", [], [{"pas_geste": 1}], {"geste": "pose"}):
        c = FauxClient(reponse=forme)
        res, journal = joue(c, allume=True)
        exige(f"forme {forme!r:24} -> dite, pas devinee",
              res.get("compte_rendu_illisible") is True and "illisible" in journal,
              repr(res)[:70])

    print("5. LE SEUIL DES FUSIONS -- au-dela, ca crie")
    c = FauxClient(reponse=[{"geste": "fusion", "dossiers": AL.SEUIL_FUSIONS_QUI_INQUIETE,
                             "lignes": 40}])
    res, journal = joue(c, allume=True)
    exige(f"{AL.SEUIL_FUSIONS_QUI_INQUIETE} fusions -> CRIE", "ATTENTION" in journal,
          repr(journal[:70]))
    c = FauxClient(reponse=[{"geste": "fusion",
                             "dossiers": AL.SEUIL_FUSIONS_QUI_INQUIETE - 1, "lignes": 2}])
    res, journal = joue(c, allume=True)
    exige(f"{AL.SEUIL_FUSIONS_QUI_INQUIETE - 1} fusions -> ne crie PAS",
          "ATTENTION" not in journal, repr(journal[:70]))

    print("6. L'ORDRE DANS LE RUN -- lu dans le fichier, pas suppose")
    texte = (ROOT / "phase2" / "sync" / "affaire_ledger.py").read_text(encoding="utf-8")
    i_chaines = texte.index('path="rpc/app_attribuer_chaines_affaire"')
    i_pose = texte.index("etiquettes = poser_les_etiquettes_de_dossier(client)")
    i_redescente = texte.index("colonnes = list(COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS)")
    exige("la pose est APRES les chaines (condition C2 du 29/10)", i_chaines < i_pose)
    exige("la pose est AVANT la redescente", i_pose < i_redescente)
    exige("un seul appel dans tout le fichier",
          texte.count("etiquettes = poser_les_etiquettes_de_dossier(client)") == 1)
    exige("les deux colonnes sont protegees du push (condition C1)",
          '"app_dossier_uuid", "app_dossier_numero",' in texte)

    print("-" * 70)
    if rates:
        print(f"{len(rates)} POINT(S) RATE(S) : " + " . ".join(rates))
        return 1
    print("TOUT EST VERT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
