#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UNE COLONNE DE CLASSE A DOIT ETRE DANS LES DEUX LISTES.           17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\test_colonnes_classe_a_dans_les_deux_listes.py

⛔ LECTURE SEULE. Lit le code source et, si elle est joignable, la base. N'ecrit rien.
   Sortie 0 = tout est juste . 1 = un rouge . 2 = pas pu mesurer.

⭐⭐⭐ POURQUOI CET ESSAI EXISTE -- il nait d'un defaut, pas d'une precaution.

  B1 (16/11) a pose trois colonnes de CLASSE A chez Supabase -- `vente_reglee_app`,
  `numero_facture_app`, `numero_mandat_app` -- et les a oubliees dans LES DEUX listes
  de `phase2/sync/affaire_ledger.py`. Trouve le 17/11, PAR HASARD, en mesurant
  pourquoi le registre local ne portait pas les 3 729 reglements.

  ⛔⛔ ET RIEN N'AVAIT CASSE, MAIS PAR ACCIDENT : le push n'envoie que ce que le
    LOCAL possede, et le local ne possedait pas ces colonnes. Les deux moities
    manquantes s'annulaient. Le jour ou l'une des deux aurait ete reparee SEULE :

        1. refresh_ledger (l. ~3396) cree la colonne en local  -> VIDE
        2. ledger_rows_for_push (l. ~3413) l'envoie            -> DU VIDE
           ⛔ et EFFACE chez Supabase les 7 400 valeurs posees par C8
        3. redescendre_ce_que_l_app_possede (l. ~3481) arrive APRES : elle ramene
           le vide qu'on vient d'ecrire

    « LA CAUSE N'EST PAS LE PUSH, C'EST L'ORDRE » -- lecon du 07/09, ecrite juste
    au-dessus de `ledger_rows_for_push`.

⚠⚠ ET LA LECON DE METHODE, CELLE QUI A RENDU CET ESSAI NECESSAIRE : j'ai d'abord
  voulu controler la SYMETRIE des deux listes (« toute protegee doit etre creee »).
  **Elle n'aurait rien attrape** : les trois colonnes de B1 manquaient dans les DEUX
  listes, donc SYMETRIQUEMENT. Un controle interne au code ne peut pas voir ce que le
  code ignore. ➡ **Il faut comparer a la BASE**, qui est la seule a savoir quelles
  colonnes de classe A existent vraiment.

CE QUE L'ESSAI VERIFIE :
  1  hors ligne -- la SYMETRIE : toute colonne protegee du push est creee en local.
  2  hors ligne -- aucune colonne n'est ecrite DEUX FOIS dans la meme liste.
  3  avec la base -- TOUTE colonne `%_app` du registre est dans les deux listes,
     SAUF celles declarees ci-dessous comme volontairement absentes.

⭐ LES ABSENCES VOLONTAIRES SE DECLARENT, elles ne se subissent pas -- regle du
  projet (« exclure : le DECLARER »). Sans cette liste, l'essai rougirait pour une
  decision prise, et on apprendrait a ignorer son rouge.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SOURCE = RACINE / "phase2" / "sync" / "affaire_ledger.py"

#: ⬜ LES COLONNES DE CLASSE A VOLONTAIREMENT ABSENTES DES DEUX LISTES.
#:   Chacune porte SA raison et SA date : une absence sans motif est un oubli.
ABSENCES_DECLAREES = {
    "numero_mandat_app":
        "Frederic, 17/11/2026 : ne pas rapatrier la colonne C du classeur "
        "(33 numeros RECYCLES a charges divergentes). La colonne reste vide, "
        "donc elle n'a rien a proteger ni a ramener.",
}

rouges: list[str] = []
verts: list[str] = []


def dit(ok: bool, quoi: str) -> None:
    (verts if ok else rouges).append(quoi)
    print("   %s %s" % ("✅" if ok else "⛔", quoi))


def main() -> int:
    if not SOURCE.exists():
        print("⛔ source introuvable : %s" % SOURCE)
        return 2
    src = SOURCE.read_text(encoding="utf-8")

    # ─── les deux listes, EXTRAITES DU CODE et non recopiees ─────────────────
    m = re.search(r"for neuve in \((.*?)\):\s*\n\s+if neuve not in colonnes", src, re.S)
    m2 = re.search(r"COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS = \((.*?)\n\)", src, re.S)
    if not (m and m2):
        print("⛔ LES DEUX LISTES N'ONT PAS ETE RETROUVEES dans le source.")
        print("   Le code a ete remanie : cet essai doit etre relu AVANT de")
        print("   conclure quoi que ce soit. On ne rend PAS un vert.")
        return 2
    creees = re.findall(r'"([a-z_]+)"', m.group(1))
    protegees = re.findall(r'"([a-z_]+)"', m2.group(1))
    print("=== LES DEUX LISTES, LUES DANS LE CODE ===")
    print("   creees en local (la boucle de refresh_ledger) : %d" % len(creees))
    print("   protegees du push ET redescendues             : %d" % len(protegees))
    print()

    # ─── 1. LA SYMETRIE ──────────────────────────────────────────────────────
    print("=== 1. LA SYMETRIE : toute protegee doit etre creee en local ===")
    manquantes = [c for c in protegees if c not in creees]
    dit(not manquantes,
        "aucune colonne protegee n'est absente de la boucle de creation"
        if not manquantes
        else "%d protegee(s) jamais creee(s) en local : %s -- LE FILET D'ORDRE LES "
             "ECARTERAIT A CHAQUE RUN, le mecanisme serait installe A MOITIE"
             % (len(manquantes), ", ".join(manquantes)))

    # ─── 2. AUCUN DOUBLON ────────────────────────────────────────────────────
    print()
    print("=== 2. AUCUNE COLONNE ECRITE DEUX FOIS DANS LA MEME LISTE ===")
    for nom, liste in (("la boucle de creation", creees),
                       ("COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS", protegees)):
        doubles = sorted({c for c in liste if liste.count(c) > 1})
        dit(not doubles,
            "%s : aucun doublon" % nom if not doubles
            else "%s : %s en double" % (nom, ", ".join(doubles)))

    # ─── 3. CONTRE LA BASE -- LE SEUL CONTROLE QUI AURAIT ATTRAPE B1 ────────
    print()
    print("=== 3. TOUTE COLONNE « _app » DU REGISTRE EST-ELLE DANS LES DEUX LISTES ? ===")
    print("   ⭐ c'est LE controle qui compte : une colonne oubliee des DEUX listes")
    print("     est SYMETRIQUE, donc invisible aux controles 1 et 2.")
    sys.path.insert(0, str(RACINE / "monitoring"))
    try:
        import check_gti_health as cgh                              # noqa: PLC0415
        for f in (RACINE / ".env", RACINE / "backend" / ".env",
                  RACINE / "apps" / "hektor-v1" / ".env"):
            if f.exists():
                cgh.load_env_file(f)
        url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
        cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not (url and cle):
            raise RuntimeError("pas d'identifiants")
        cl = cgh.SupabaseClient(url, cle, timeout_seconds=30)
        ligne = cl.get("app_affaire_ledger", {"select": "*", "limit": "1"})
    except Exception as souci:                                      # noqa: BLE001
        print()
        print("   ⚠ LA BASE N'EST PAS JOIGNABLE (%s)." % str(souci)[:70])
        print("   ⛔ ON NE REND PAS UN VERT : ce controle est le seul qui aurait")
        print("     attrape le defaut de B1. Sortie 2 -- « pas pu mesurer ».")
        print()
        print("   (les controles 1 et 2, eux, sont passes : %d vert(s), %d rouge(s))"
              % (len(verts), len(rouges)))
        return 2 if not rouges else 1

    if not (isinstance(ligne, list) and ligne and isinstance(ligne[0], dict)):
        print("   ⚠ le registre n'a rendu aucune ligne : l'echantillon n'apprend rien.")
        print("   ⛔ sortie 2 -- un zero ne se croit pas sans temoin positif.")
        return 2
    la_haut = sorted(c for c in ligne[0] if c.endswith("_app"))
    print("   colonnes « _app » chez Supabase : %d" % len(la_haut))
    print()
    oubliees, declarees = [], []
    for c in la_haut:
        dans_les_deux = c in creees and c in protegees
        if dans_les_deux:
            continue
        if c in ABSENCES_DECLAREES:
            declarees.append(c)
        else:
            oubliees.append(c)
    dit(not oubliees,
        "toute colonne « _app » du registre est dans les DEUX listes"
        if not oubliees
        else "%d colonne(s) de classe A OUBLIEE(S) : %s -- c'est le defaut de B1, "
             "et il est DORMANT : rien ne casse tant que les deux moities manquent, "
             "mais reparer UNE SEULE effacerait les valeurs au premier run"
             % (len(oubliees), ", ".join(oubliees)))
    if declarees:
        print()
        print("   ⬜ ABSENCES DECLAREES, et c'est voulu :")
        for c in declarees:
            print("      %s" % c)
            print("         %s" % ABSENCES_DECLAREES[c])

    print()
    print("=== LE VERDICT ===")
    print("   %d vert(s) . %d rouge(s)" % (len(verts), len(rouges)))
    if rouges:
        print()
        for r in rouges:
            print("   ⛔ %s" % r)
        return 1
    print("   ✅ une colonne de classe A ne peut plus etre posee A MOITIE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
