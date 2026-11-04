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
    # 04/11/2026 (synthese couples §74) : l'API coupe a 8 s, et l'appel unique en prenait 7,2 sur 94 741
    # contacts (il a echoue le 04/11 a 13:57). On appelle la MEME regle par tranches de numeros.
    # Si la fonction par tranches manque (patch non pose ou retire), on revient a l'appel unique.
    bornes = bornes_des_tranches()
    total, tranches = 0, 0
    try:
        for de, a in zip(bornes, bornes[1:]):
            total += int(client.request(method="POST", path="rpc/app_recalculer_types_tranche",
                                        payload={"p_de": de, "p_a": a}) or 0)
            tranches += 1
    except Exception as souci:                                       # noqa: BLE001
        if tranches == 0 and "app_recalculer_types_tranche" in str(souci) and ("404" in str(souci) or "PGRST202" in str(souci)):
            print("[type des contacts] fonction par tranches absente : appel unique (chemin d'avant)")
            try:
                total = client.request(method="POST", path="rpc/app_recalculer_tous_les_types", payload={})
            except Exception as autre:                               # noqa: BLE001
                print(f"[type des contacts] ECHEC de l'appel : {autre!r}")
                return 1
        else:
            print(f"[type des contacts] ECHEC a la tranche {tranches + 1} sur {len(bornes) - 1} "
                  f"({total} contact(s) deja remis) : {souci!r}")
            return 1
    print(f"[type des contacts] {total} contact(s) remis d'apres nos registres, "
          f"{tranches} tranche(s), en {round(time.time() - debut, 1)} s.")
    return 0


TAILLE_TRANCHE = 15000   # ~31 500 contacts se calculent en 1,4 s : 15 000 laissent une large marge sous 8 s


def bornes_des_tranches() -> list[str]:
    """Bornes [de, a[ en TEXTE (les identites ont 8 chiffres). La premiere et la derniere couvrent tout le reste :
    un contact absent de l'etat local reste donc dans une tranche."""
    import sqlite3
    ids: list[str] = []
    try:
        conn = sqlite3.connect(f"file:{ROOT / 'phase2' / 'phase2.sqlite'}?mode=ro", uri=True, timeout=30)
        try:
            ids = [r[0] for r in conn.execute(
                "SELECT row_key FROM app_contact_supabase_push_state WHERE table_name = 'app_contact_current' ORDER BY row_key")]
        finally:
            conn.close()
    except sqlite3.Error:
        ids = []
    milieu = ids[TAILLE_TRANCHE::TAILLE_TRANCHE] if ids else [f"{n}" for n in range(10100000, 10800000, 100000)]
    return [""] + milieu + ["99999999"]


if __name__ == "__main__":
    raise SystemExit(main())
