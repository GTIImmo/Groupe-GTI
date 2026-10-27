"""⑧ TYPES, ÉTAPE 2 (27/10/2026) — le type de chaque contact de l'app, depuis NOS registres.

Étape de nuit « phase2 type des contacts depuis nos registres », en fin du bloc des contacts
(après l'envoi des contacts et la propagation des numéros). Elle appelle la fonction de la base
`app_recalculer_tous_les_types()` : un geste fait DANS HEKTOR, que la nuit vient d'écrire dans nos
registres, arrive ainsi dans le type ; et un contact neuf, envoyé sans type, reçoit le sien.
Le geste de l'app, lui, pose le type au clic (les 6 portes de la base).
Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §43 à §46.

Interrupteur : APP_TYPE_PAR_NOS_REGISTRES=1 dans .env. Éteint, l'étape le dit et sort en 0 sans rien faire.
Sortie : 0 = fait (ou éteint) · 1 = l'appel a échoué (étape facultative : le run continue, le battement le dit).

    python phase2/sync/recalculer_types_contacts.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phase2" / "sync"))
from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES, SupabaseRestClient, load_env_file, type_par_nos_registres,
)


def main() -> int:
    import os
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)
    if not type_par_nos_registres():
        print("[type des contacts] interrupteur APP_TYPE_PAR_NOS_REGISTRES eteint : rien a faire (la nuit ecrit encore le type).")
        return 0
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("[type des contacts] SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY absent : appel impossible.")
        return 1
    client = SupabaseRestClient(base_url=url, service_role_key=cle)
    debut = time.time()
    try:
        change = client.request(method="POST", path="rpc/app_recalculer_tous_les_types", payload={})
    except Exception as souci:                                       # noqa: BLE001
        print(f"[type des contacts] ECHEC de l'appel : {souci!r}")
        return 1
    print(f"[type des contacts] {change} contact(s) remis d'apres nos registres, en {round(time.time() - debut, 1)} s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
