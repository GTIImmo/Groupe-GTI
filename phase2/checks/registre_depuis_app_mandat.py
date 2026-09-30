# -*- coding: utf-8 -*-
"""A.3-tech phase 1 (30/09/2026) -- LA TABLE SAIT-ELLE REFAIRE LE REGISTRE ?
LECTURE SEULE. N'ECRIT NULLE PART, N'APPELLE NI HEKTOR NI SUPABASE.

LA QUESTION, ET POURQUOI ELLE SE POSE MAINTENANT
-------------------------------------------------
Le chantier consiste a changer LA SOURCE des colonnes de mandat du registre :
elles viendront de `app_mandat` au lieu du miroir. La vue ne bouge pas, l'ecran
ne bouge pas -- mais si la table rend une AUTRE valeur, l'ecran affichera cette
autre valeur sans rien signaler.

Donc on ne bascule pas d'abord pour regarder ensuite. ON REGARDE D'ABORD.

CE QU'ELLE COMPARE
------------------
Les 14 colonnes du registre qui viennent du mandat, ligne par ligne, sur le
couple (annonce, numero) -- la cle des deux cotes.

CE QU'ELLE NE COMPTE PAS COMME UN ECART, ET C'EST MOTIVE
---------------------------------------------------------
`mandat_date_cloture` : la table la PROTEGE PAR OMISSION -- l'app la possede
(CHAMPS_APP_MANDAT, carnet app_mandat_champ_app), et le run n'a pas a
l'ecraser avec ce que Hektor en pense. La decision est du 28/08 :

    « tant que Hektor vit, son registre dira le mandat ouvert quand le notre
      le dira clos. »

Un ecart sur cette colonne est donc LE COMPORTEMENT VOULU. Il est compte a
part, jamais avec les autres -- sans quoi on lirait comme une avarie ce qui
est une decision.

CE QU'ELLE REND
---------------
Trois populations, jamais un total :
    LES DEUX      le couple est des deux cotes  -> on compare vraiment
    TABLE SEULE   ce que la table ajoute        -> le gain attendu
    VUE SEULE     ce que la table perdrait      -> LE SEUL VRAI DANGER
"""
from __future__ import annotations

import collections
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync.export_app_payload import (  # noqa: E402
    normalize_history_version,
    normalize_register_mandat_type,
    normalize_text,
)

PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"

# Les trois types d'offre que le registre admet (decision du 26/08). La table
# porte TOUT ; sans ce filtre on lirait 2 348 locations comme un « gain ».
TYPES_ADMIS = ("0", "10", "6")

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _texte(valeur) -> str:
    return normalize_text(valeur) or ""


def depuis_app_mandat(ligne: sqlite3.Row) -> dict:
    """Les colonnes de mandat du registre, telles que la table les rendrait.

    ⚠ MEMES FORMULES QUE LE REGISTRE, IMPORTEES. `normalize_register_mandat_type`
      est celle dont l'ordre des tests compte : « non exclusif » doit passer
      AVANT « exclusif », faute de quoi 164 mandats simples sont presentes comme
      exclusifs -- ce qui n'est pas une nuance d'affichage.
    """
    try:
        versions = json.loads(ligne["versions_json"] or "[]")
    except Exception:
        versions = []
    try:
        avenants = json.loads(ligne["avenants_json"] or "[]")
    except Exception:
        avenants = []

    historique = [
        normalize_history_version(item, is_current=(i == 0), index=i)
        for i, item in enumerate(versions)
    ]
    return {
        "numero_mandat": _texte(ligne["numero_mandat"]),
        "mandat_numero_reference": _texte(ligne["numero_mandat"]),
        "mandat_source_id": _texte(ligne["hektor_mandat_id"]),
        "mandat_type": _texte(normalize_register_mandat_type(ligne["type"])),
        "mandat_type_source": _texte(ligne["type"]),
        "mandat_date_debut": _texte(ligne["date_debut"]),
        "mandat_date_fin": _texte(ligne["date_fin"]),
        "mandat_montant": _texte(ligne["montant"]),
        "mandants_texte": _texte(ligne["mandants_texte"]),
        "mandat_note": _texte(ligne["note"]),
        "register_version_count": int(ligne["version_count"] or 0),
        "register_embedded_avenant_count": int(ligne["avenant_count"] or 0),
        "register_avenants_json": json.dumps(avenants, ensure_ascii=True, separators=(",", ":")),
        "register_history_json": json.dumps(historique, ensure_ascii=True, separators=(",", ":")),
    }


def depuis_la_vue(ligne: sqlite3.Row) -> dict:
    sortie = {}
    for colonne in (
        "numero_mandat", "mandat_numero_reference", "mandat_source_id",
        "mandat_type", "mandat_type_source", "mandat_date_debut",
        "mandat_date_fin", "mandat_montant", "mandants_texte", "mandat_note",
    ):
        sortie[colonne] = _texte(ligne[colonne])
    sortie["register_version_count"] = int(ligne["register_version_count"] or 0)
    sortie["register_embedded_avenant_count"] = int(ligne["register_embedded_avenant_count"] or 0)
    sortie["register_avenants_json"] = _texte(ligne["register_avenants_json"]) or "[]"
    sortie["register_history_json"] = _texte(ligne["register_history_json"]) or "[]"
    return sortie


def mesurer(con: sqlite3.Connection) -> dict | None:
    con.row_factory = sqlite3.Row
    for nom in ("app_mandat", "app_mandat_register_current"):
        if not con.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?", (nom,)
        ).fetchone():
            return None

    table = {}
    for r in con.execute(
        "SELECT hektor_annonce_id, numero_mandat, hektor_mandat_id, type, date_debut,"
        " date_fin, date_cloture, montant, mandants_texte, note, versions_json,"
        " version_count, avenants_json, avenant_count, offre_type"
        " FROM app_mandat"
    ):
        table[(str(r["hektor_annonce_id"]), str(r["numero_mandat"]))] = r

    vue = {}
    for r in con.execute("SELECT * FROM app_mandat_register_current"):
        vue[(str(r["hektor_annonce_id"]), str(r["numero_mandat"]))] = r

    communs = set(table) & set(vue)
    # Ce que la table AJOUTERAIT : seulement les types que le registre admet.
    table_seule = {c for c in set(table) - set(vue)
                   if str(table[c]["offre_type"] or "") in TYPES_ADMIS}
    vue_seule = set(vue) - set(table)

    ecarts = collections.Counter()
    exemples = collections.defaultdict(list)
    cloture_ecart = 0
    for cle in communs:
        attendu = depuis_app_mandat(table[cle])
        actuel = depuis_la_vue(vue[cle])
        for colonne, valeur in attendu.items():
            if valeur != actuel[colonne]:
                ecarts[colonne] += 1
                if len(exemples[colonne]) < 3:
                    exemples[colonne].append((cle, actuel[colonne], valeur))
        # compte a part -- voir l'en-tete : c'est une decision, pas une avarie
        if _texte(table[cle]["date_cloture"]) != _texte(vue[cle]["mandat_date_cloture"]):
            cloture_ecart += 1

    return {
        "communs": len(communs),
        "table_seule": len(table_seule),
        "vue_seule": len(vue_seule),
        "vue_seule_exemples": sorted(vue_seule)[:10],
        "ecarts": dict(ecarts),
        "exemples": {k: v for k, v in exemples.items()},
        "cloture_ecart": cloture_ecart,
    }


def main() -> int:
    con = sqlite3.connect("file:%s?mode=ro" % PHASE2_DB.as_posix(), uri=True)
    try:
        m = mesurer(con)
    finally:
        con.close()
    if m is None:
        print("NON MESURABLE : app_mandat ou le registre manque -- ce n'est pas un zero")
        return 2

    print("LA TABLE SAIT-ELLE REFAIRE LE REGISTRE ?")
    print("")
    print("   couples des DEUX cotes (compares)   : %s" % m["communs"])
    print("   TABLE SEULE (le gain, types admis)  : %s" % m["table_seule"])
    print("   VUE SEULE  (ce qu'on PERDRAIT)      : %s   <- doit valoir 0" % m["vue_seule"])
    if m["vue_seule"]:
        print("      exemples :", ", ".join("%s/%s" % c for c in m["vue_seule_exemples"]))
    print("")
    if not m["ecarts"]:
        print("   ECARTS SUR LES 14 COLONNES          : AUCUN")
    else:
        print("   ECARTS SUR LES 14 COLONNES :")
        for colonne, n in sorted(m["ecarts"].items(), key=lambda kv: -kv[1]):
            part = 100.0 * n / max(m["communs"], 1)
            print("      %-34s %6s  (%.2f %%)" % (colonne, n, part))
        print("")
        for colonne, liste in m["exemples"].items():
            print("      -- %s --" % colonne)
            for (a, n), vue_v, table_v in liste:
                print("         annonce %-7s n° %-9s" % (a, n))
                print("            la VUE   : %s" % (str(vue_v)[:110] if vue_v != "" else "(vide)"))
                print("            la TABLE : %s" % (str(table_v)[:110] if table_v != "" else "(vide)"))
    print("")
    print("   -- compte a part, c'est une DECISION du 28/08 --")
    print("   mandat_date_cloture different       : %s" % m["cloture_ecart"])
    print("      (l'app possede ce champ ; le run ne l'ecrase pas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
