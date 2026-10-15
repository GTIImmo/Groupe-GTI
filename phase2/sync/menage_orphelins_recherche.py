#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le menage des orphelins de recherche, APPELE DEPUIS LE RUN -- 14/10/2026.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI CE SCRIPT EXISTE : UNE COURSE DE 48 SECONDES
═══════════════════════════════════════════════════════════════════════════════
`app_sweep_search_orphans()` rattache les lignes de rapprochement, de score, de
notification et de relance dont la recherche a disparu. Elle tourne, et elle
travaille vraiment : 16 rapprochements et 212 lignes d'historique rattaches le
14/10, 27 et 370 le 10/10, 42 et 242 le 07/10.

MAIS ELLE ETAIT EN COURSE AVEC LE RUN, et elle perdait :

    le menage  cron Supabase « 0 5 * * * » en UTC   -> 07:00:00 locale
    le push    etape du run                          -> 07:00:48 le 14/10
                                                        07:04:00 le 13/10

Le menage passait donc 48 SECONDES AVANT le push. Il nettoyait l'etat de la
veille, puis le push remontait les lignes -- et il fallait attendre le
LENDEMAIN pour que le rattrapage ait lieu. Pire : 48 s un jour, 4 min l'autre,
l'ordre pouvait s'inverser n'importe quand. Cela explique sans doute que le
menage rattrape 370 lignes certains jours et ZERO les 11, 12 et 13/10.

⚠ UN CRON ET UNE ETAPE DE RUN NE S'ORDONNENT PAS TOUT SEULS. L'un vit chez
  Supabase, l'autre dans PowerShell, et rien ne garantissait leur enchainement.
  On supprime donc la course en appelant le menage DEPUIS le run, juste apres
  le push des contacts : l'ordre devient certain au lieu d'etre aleatoire.

⚠ LE CRON N'EST PAS ETEINT, ET C'EST VOULU. Il reste le filet de securite si
  le run echoue avant cette etape. La fonction est idempotente : la rejouer ne
  coute qu'un passage a vide.

ETAPE NON BLOQUANTE : si Supabase ne repond pas, le run continue. Un menage
rate se rattrape le lendemain ; un run interrompu, non.

    python phase2/sync/menage_orphelins_recherche.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("!! SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents", file=sys.stderr)
        return 1

    # ⚠ LES ARGUMENTS SONT NOMMES OBLIGATOIREMENT (`def __init__(self, *, base_url, ...)`).
    #   Le 15/10 au matin, l'etape a echoue DEUX FOIS sur
    #   « __init__() takes 1 positional argument but 3 were given » : j'avais recopie
    #   l'import de repartition_commission.py sans lire COMMENT il instancie.
    client = SupabaseRestClient(base_url=url, service_role_key=cle)

    # ⭐ L'ESSAI A VIDE : tout se joue SAUF l'appel. C'est ce qui manquait le 14/10 --
    #   je n'avais pas lance le script (il ECRIT en production, et c'etait le bon
    #   reflexe), mais je pouvais eprouver TOUT CE QUI PRECEDE l'ecriture. Un script
    #   qui ecrit doit offrir un moyen de s'eprouver sans ecrire.
    if "--essai-a-vide" in sys.argv:
        print("essai a vide : env lu, client construit")
        print(f"   base    : {client.base_url}")
        print(f"   cle     : {'oui' if client.service_role_key else 'NON'}")
        print("   appel   : NON JOUE (c'est le but)")
        return 0

    try:
        reponse = client.request(method="POST", path="rpc/app_sweep_search_orphans")
    except Exception as exc:  # non bloquant : on dit, et on rend la main
        print(f"!! menage des orphelins impossible : {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    # La fonction rend un jsonb ; on le montre tel quel pour que le journal du
    # run porte la preuve, et pas seulement « DONE ».
    if isinstance(reponse, (dict, list)):
        print(json.dumps(reponse, ensure_ascii=False, indent=2))
        detail = reponse if isinstance(reponse, dict) else {}
        total = sum(v for v in detail.values() if isinstance(v, int))
        print(f"menage des orphelins de recherche : {total} ligne(s) rattachee(s)")
    else:
        print(f"menage des orphelins de recherche : {reponse!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
