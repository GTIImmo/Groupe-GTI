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

CE QU'ELLE NE COMPARE PLUS -- `mandat_montant`, retire le 06/10/2026
---------------------------------------------------------------------
La colonne `montant` de app_mandat n'existe plus (recopie exacte de
versions_json[0].montant, 26 839 lignes sur 26 839, et aucun lecteur), et le
registre n'affiche plus de montant de mandat : il affiche LE PRIX DE L'ANNONCE.
Comparer ce champ entre deux constructions de MANDAT n'a donc plus d'objet.
Il reste 13 colonnes comparees.

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
    attach_hektor_read,
    charger_corps_suspects,
    charger_mandants_du_registre_des_liens,
    texte_des_mandants,
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


def depuis_app_mandat(ligne: sqlite3.Row, prix_annonce=None, corps_suspect: bool = False,
                      nos_mandants: list | None = None) -> dict:
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

    # ⚠ LE PRIX ET LE DRAPEAU SONT INDISPENSABLES DEPUIS LE 06/10 (lot 2) : la
    #   version COURANTE de l'historique porte LE PRIX DE L'ANNONCE, plus le
    #   montant du mandat. Sans les passer, ce comparateur annoncerait un ecart
    #   sur `register_history_json` pour CHAQUE ligne ayant un prix -- soit
    #   ~24 000 fausses alertes, et un controle qui crie au loup ne sert a rien.
    historique = [
        normalize_history_version(item, is_current=(i == 0), index=i,
                                  prix_annonce=prix_annonce,
                                  corps_suspect=corps_suspect)
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
        # ⚠ LA MEME REGLE QUE LE REGISTRE (export_app_payload, lot du 05/10) :
        #   NOTRE liste de mandants d'abord, le texte de Hektor en repli. Sans
        #   cela le comparateur annoncait 23 570 ecarts -- 96 % -- en comparant
        #   deux choses qui ne viennent plus de la meme source.
        "mandants_texte": (texte_des_mandants(nos_mandants or [])
                           or _texte(ligne["mandants_texte"])),
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
        "mandat_date_fin", "mandants_texte", "mandat_note",
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
        " date_fin, date_cloture, mandants_texte, note, versions_json,"
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
    suspects = charger_corps_suspects(con)
    mandants = charger_mandants_du_registre_des_liens(con)
    # ⚠ LE PRIX SE LIT DANS LE MIROIR, PAS DANS LA COLONNE DE LA VUE : la colonne
    #   est stockee en REAL et ressort « 65700.0 », alors que le registre lit
    #   `ann.prix` du miroir et ecrit « 65700 ». La difference etait de FORME,
    #   pas de valeur, et elle produisait a elle seule 23 602 faux ecarts.
    prix_miroir = {str(a): p for a, p in con.execute(
        "SELECT hektor_annonce_id, prix FROM hektor.hektor_annonce")}
    for cle in communs:
        attendu = depuis_app_mandat(
            table[cle],
            prix_annonce=prix_miroir.get(cle[0], vue[cle]["prix"]),
            corps_suspect=cle in suspects,
            nos_mandants=mandants.get(cle[0]),
        )
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
    # ⚠ LE MIROIR DOIT ETRE ATTACHE : `charger_corps_suspects` rend un ensemble
    #   VIDE EN SILENCE sans lui (c'est documente dans la fonction, et ce silence
    #   m'a fait annoncer trois chiffres contradictoires le 05/10). Sans le miroir,
    #   ce comparateur serait aveugle aux corps empruntes.
    attach_hektor_read(con)   # la forme du projet, eprouvee
    try:
        fraicheur = con.execute(
            "SELECT substr(MIN(refreshed_at),1,10), substr(MAX(refreshed_at),1,10),"
            " SUM(CASE WHEN substr(refreshed_at,1,10) < date('now','-2 day')"
            "          THEN 1 ELSE 0 END), COUNT(*)"
            " FROM app_mandat_register_current").fetchone()
        m = mesurer(con)
    finally:
        con.close()
    if m is None:
        print("NON MESURABLE : app_mandat ou le registre manque -- ce n'est pas un zero")
        return 2

    print("LA TABLE SAIT-ELLE REFAIRE LE REGISTRE ?")
    print("")
    # ⚠⚠ CE QUE CE CONTROLE LIT, DIT A VOIX HAUTE -- sans cette ligne il ressemble
    #   a une alarme alors qu'il mesure surtout un RETARD. `app_mandat_register_current`
    #   est une table de TRAVAIL LOCALE : le run ne reecrit que ses lignes du
    #   perimetre ACTIF (735 sur 24 493). Les autres datent du jour ou le registre a
    #   ete pose. Un ecart sur une ligne perimee ne dit RIEN de l'application, qui
    #   lit Supabase -- et Supabase se remet a jour avec
    #   `python phase2/sync/registre_mandats_upsert.py`.
    if fraicheur and fraicheur[3]:
        print("   CE QUE JE COMPARE -- la table de travail LOCALE")
        print("      ecrite entre le %s et le %s" % (fraicheur[0], fraicheur[1]))
        print("      dont %d lignes sur %d ont plus de deux jours  <- leurs ecarts"
              " sont du RETARD, pas une avarie" % (fraicheur[2] or 0, fraicheur[3]))
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
