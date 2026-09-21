#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 — LA PROTECTION PASSE DU BIEN AU CHAMP, a la fin du run.  21/09/2026

Le run vient de reecrire les annonces depuis le miroir de Hektor. Les champs que
l'app a saisis et que Hektor n'a pas encore confirmes viennent donc d'etre
ecrases. On les repose par-dessus -- et EUX SEULS.

L'EXEMPLE DE FREDERIC, qui n'avait pas de bonne reponse jusqu'ici :
    14 h  le prix est corrige dans l'app, l'envoi vers Hektor echoue
    15 h  la surface est changee dans Hektor
    -> avant : geler le bien (la surface n'arrive jamais) OU le rafraichir
       (le prix disparait). Les deux sont faux.
    -> maintenant : le prix reste celui de l'app, la surface arrive de Hektor.

ICI, ET PAS DANS LE PUSH : le push porte la logique de delta par empreinte, on
n'y touche pas (meme raisonnement que C.7, ecrit le 25/08). La reapplication est
un geste d'apres, court et sans effet de bord.

RIEN N'EST ENVOYE A HEKTOR, aucun travail n'est cree, la ligne d'attente n'est
pas touchee. Une saisie SOLDEE (ligne disparue) n'est plus reappliquee -- c'est
voulu : elle a ete tranchee.

AUJOURD'HUI : ZERO ligne en attente, donc l'etape ne fait rien. Elle servira au
premier envoi qui echoue.

RETOUR ARRIERE : retirer l'etape du run.
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
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return 2
    client = SupabaseRestClient(base_url=url, service_role_key=cle)
    reponse = client.request(method="POST", path="rpc/app_annonce_reappliquer_saisies",
                             payload={"target_dossier_id": None})
    if isinstance(reponse, dict):
        print(f"[saisies-app] {reponse.get('biens', 0)} bien(s), {reponse.get('champs', 0)} champ(s) reposes")
    else:
        print(f"[saisies-app] reponse inattendue : {json.dumps(reponse, ensure_ascii=False)[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
