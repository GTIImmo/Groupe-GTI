"""Matterport porte-t-il NOS DEUX numeros -- sans que son identifiant bouge ?

25/09/2026.

app_matterport_group (4 484 lignes) rattachait ses visites virtuelles aux annonces
par le SEUL numero Hektor, et la table ne figure pas dans REPOINT_TABLES.

⚠ LA GARDE POSEE PAR FREDERIC : « en gelant uniquement le champ id, il faut que
  Matterport ne soit pas fige ». Ce test la verifie des deux cotes :
    - `id` ne bouge pas  -> les 5 047 scans (group_id) gardent leur groupe ;
    - tout le reste bouge -> libelle, etat, visibilite, validation, date de synchro
      sont bien dans la charge utile, donc mis a jour a chaque passage.

Il fait tourner LA VRAIE fonction build_supabase_rows du run.
N'APPELLE NI MATTERPORT NI HEKTOR NI SUPABASE. N'ECRIT RIEN.

    python phase2/checks/test_matterport_numero_app.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SCRIPT = RACINE / "phase2" / "sync" / "sync_matterport_models.py"
sys.path.insert(0, str(SCRIPT.parent))

import sync_matterport_models as mp  # noqa: E402

echecs = 0


def controle(nom: str, ok: bool, detail: str = "") -> None:
    global echecs
    print(f"  {'OK ' if ok else 'KO '} {nom}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        echecs += 1


def main() -> int:
    source = SCRIPT.read_text(encoding="utf-8")

    # ── ① MATTERPORT NE PARLE PAS A HEKTOR ────────────────────────────────────
    # C'est la raison pour laquelle doubler le numero est sans effet sur lui.
    appels = re.findall(r"https?://[a-z0-9.\-]+", source)
    hektor = [u for u in appels if "la-boite-immo" in u or "hektor" in u.lower()]
    controle("(a) le run n'appelle QUE Matterport", not hektor, f"appels Hektor : {hektor}")

    # ── ② LA VRAIE FONCTION D'ENVOI ───────────────────────────────────────────
    # On pre-remplit le cache pour ne pas lire le miroir : 62087 est connue, 99999 non.
    mp._NUMERO_APP = {"62087": 4724}

    groupes = [
        {"id": "uuid-fige-A", "hektor_annonce_id": "62087", "numero_mandat": "V800061890",
         "group_state": "active", "group_visibility": "public"},
        {"id": "uuid-fige-B", "hektor_annonce_id": "99999", "numero_mandat": "V800099999",
         "group_state": "archived", "group_visibility": "private"},
    ]
    lignes, _ = mp.build_supabase_rows([], groupes)
    a = next((r for r in lignes if r["id"] == "uuid-fige-A"), None)
    b = next((r for r in lignes if r["id"] == "uuid-fige-B"), None)

    controle("(b) NOTRE numero part avec le groupe",
             a is not None and a.get("app_dossier_id") == 4724, str(a))
    controle("(c) celui de Hektor part toujours",
             a is not None and a.get("hektor_annonce_id") == 62087, str(a))

    # ⚠ LE CONTROLE CENTRAL : l'identifiant ne bouge pas.
    controle("(d) l'identifiant du groupe est INCHANGE",
             a is not None and a["id"] == "uuid-fige-A", str(a))

    # ⚠ ET L'AUTRE MOITIE DE LA GARDE : Matterport n'est PAS fige.
    bougent = ["group_label", "group_state", "group_visibility", "is_validated",
               "synced_at", "updated_at"]
    manquants = [c for c in bougent if a is None or c not in a]
    controle("(e) tout le reste continue d'etre mis a jour chaque nuit",
             not manquants, f"absents de la charge utile : {manquants}")
    controle("(f) l'etat et la visibilite viennent bien du groupe",
             a is not None and a["group_state"] == "active" and a["group_visibility"] == "public",
             str(a))

    # ── ③ UNE ANNONCE INCONNUE N'EST PAS AVALEE ──────────────────────────────
    controle("(g) une annonce sans numero d'app passe quand meme (pas de blocage)",
             b is not None, "le groupe a disparu de l'envoi")
    controle("(h) et son numero est vide, pas invente",
             b is not None and b.get("app_dossier_id") is None, str(b))
    controle("(i) le cas est SIGNALE, pas avale",
             "WARN matterport" in source, "aucun avertissement dans le code")

    # ── ④ LA RECETTE DE L'IDENTIFIANT EST INTACTE ────────────────────────────
    # Elle sera reprise plus tard (patron du carnet C.9-f), pas maintenant.
    controle("(j) stable_group_id est toujours bati sur le numero Hektor",
             "uuid.uuid5(MATTERPORT_GROUP_NAMESPACE, f\"{hektor_annonce_id}:{numero_mandat}\")" in source,
             "la recette a change -- les 4 484 identifiants bougeraient")
    controle("(k) les scans pendent toujours au groupe par group_id",
             'supabase_delete_by_ids(url, key, MATTERPORT_MODEL_TABLE, "group_id"' in source,
             "le lien scans -> groupe a change")

    # ── ⑤ LE NUMERO EST LU DANS LE MIROIR, PAS REDEMANDE ─────────────────────
    controle("(l) le numero vient de app_view_generale (miroir local)",
             "FROM app_view_generale" in source and "def numero_app_par_annonce" in source,
             "le numero est cherche ailleurs")
    controle("(m) il n'est lu qu'une fois par execution",
             "_NUMERO_APP is not None" in source, "une lecture par groupe")

    print(f"\n{f'{echecs} ECHEC(S)' if echecs else 'TOUT VERT'}")
    return 1 if echecs else 0


if __name__ == "__main__":
    raise SystemExit(main())
