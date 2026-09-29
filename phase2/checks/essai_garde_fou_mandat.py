# -*- coding: utf-8 -*-
"""ESSAI DU GARDE-FOU DU NUMERO DE MANDAT -- releve des temoins, LECTURE SEULE.

CE QU'ON VEUT PROUVER
---------------------
Que le worker REFUSE de generer un numero de mandat sur une annonce sans mandant,
et qu'il le refuse AVANT `protexa-valideStep1` -- donc SANS CONSOMMER DE NUMERO.

C'est la promesse ecrite le 18/05 dans NOTE_HEKTOR_MANDAT_NUMERO_AUTO :
    « Si aucun mandant n'est detecte, le job passe en erreur SANS CONSOMMER
      DE NUMERO. »
Elle n'a jamais ete eprouvee. Ce script permet de l'eprouver sans risque.

POURQUOI L'ESSAI EST SUR, ET A QUELLE CONDITION
-----------------------------------------------
La porte a TROIS sources, et elle ne leve qu'apres les avoir toutes trouvees vides
(console_job_worker.js, L4-b' du 22/09) :
    1. nos numeros de mandants, traduits vers Hektor
    2. la liste « prospects » de la console
    3. l'API des proprietaires -- QUI N'EST PAS FILTREE PAR AGENCE

-- SI L'UNE DES TROIS REPOND, LA PORTE S'OUVRE ET LE NUMERO EST CONSOMME.
   L'essai n'est donc sur QUE sur une annonce vide des trois cotes. C'est
   pourquoi ce script releve les temoins AVANT, et qu'on les relit APRES :
   un numero consomme se verrait immediatement.

CE QUE CE SCRIPT NE FAIT PAS
----------------------------
Il ne cree aucun travail, n'appelle pas Hektor, n'ecrit nulle part. Il REGARDE.
Le travail d'essai, lui, se cree a la main et demande l'accord de Frederic :
c'est une ecriture en base de production et un appel chez Hektor.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
MIROIR = RACINE / "data" / "hektor.sqlite"

# Les deux annonces d'essai de C.9, sans mandant et sans numero (mesure du 29/09).
# Elles sont deja marquees pour suppression dans la memoire projet : les user
# comme cible d'essai ne cree aucune dette.
CIBLES = ("63146", "63147")

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def temoins() -> dict:
    """Les trois temoins qui disent si un numero a ete consomme."""
    cx = sqlite3.connect(f"file:{MIROIR}?mode=ro", uri=True)
    try:
        # 1. Le plus grand numero PROTEXA. C'est LE temoin : il n'augmente que
        #    lorsqu'un numero est reellement consomme.
        plus_grand = cx.execute(
            "SELECT MAX(CAST(numero AS INTEGER)) FROM hektor_mandat "
            "WHERE numero GLOB '[0-9]*' AND CAST(numero AS INTEGER) BETWEEN 10000 AND 99999"
        ).fetchone()[0]

        # 2. Combien de mandats en tout -- un second regard sur le meme fait.
        total = cx.execute("SELECT COUNT(*) FROM hektor_mandat").fetchone()[0]

        # 3. Les cibles portent-elles deja un mandat ? Elles ne doivent pas.
        marque = ",".join("?" for _ in CIBLES)
        sur_cibles = cx.execute(
            f"SELECT hektor_annonce_id, COUNT(*) FROM hektor_mandat "
            f"WHERE CAST(hektor_annonce_id AS TEXT) IN ({marque}) GROUP BY 1",
            CIBLES,
        ).fetchall()
        return {
            "plus_grand_numero": plus_grand,
            "mandats_total": total,
            "mandats_sur_les_cibles": dict(sur_cibles),
        }
    finally:
        cx.close()


def main() -> int:
    if not MIROIR.exists():
        print(f"miroir introuvable : {MIROIR}", file=sys.stderr)
        return 2
    t = temoins()
    print("TEMOINS DU GARDE-FOU DU NUMERO DE MANDAT")
    print("")
    print(f"   plus grand numero PROTEXA : {t['plus_grand_numero']}")
    print(f"   mandats dans le miroir    : {t['mandats_total']}")
    print(f"   mandats sur les cibles    : {t['mandats_sur_les_cibles'] or 'aucun'}  (cibles : {', '.join(CIBLES)})")
    print("")
    print("LECTURE DU RESULTAT, APRES L'ESSAI :")
    print("   le plus grand numero N'A PAS BOUGE  -> le garde-fou a tenu, RIEN consomme")
    print("   il a augmente de 1                  -> un numero a ete brule : le garde-fou")
    print("                                          n'a pas tenu, et il faut comprendre")
    print("                                          laquelle des trois sources a repondu")
    print("")
    print("-- le miroir ne se met a jour QU'AU RUN DE NUIT. Pour lire l'effet tout de")
    print("   suite, il faut relire le mandat chez Hektor, pas ici.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
