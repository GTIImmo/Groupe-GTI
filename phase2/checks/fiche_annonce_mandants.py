"""CONTROLE -- la fiche annonce affiche-t-elle NOS mandants ?        06/10/2026

Le registre des mandats a ete repare le 05/10. La fiche annonce, elle, lisait
toujours `mandats_json`, c'est-a-dire la reponse brute de Hektor -- et sur les
457 couples a corps emprunte, 456 y affichaient le nom d'un client sur le bien
de quelqu'un d'autre.

CE CONTROLE N'IMITE RIEN. Il appelle `build_trimmed_detail_payload`, la fonction
que le run utilise, deux fois sur la MEME ligne : sans la carte des mandants
(l'etat d'avant) puis avec (l'etat d'apres). Ce qu'il imprime est donc ce que la
fiche affichera, pas une reconstitution.
    ➡ memoire `eprouver-c-est-executer-le-code`

Il n'ecrit RIEN, ni en local ni dans le cloud : connexion en lecture seule.

    python phase2/checks/fiche_annonce_mandants.py              # temoins + bilan
    python phase2/checks/fiche_annonce_mandants.py --temoins    # temoins seuls

CE QUI DOIT ETRE VRAI POUR QUE LE LOT SOIT BON
    ① corps emprunte ET aucun nom en commun : le nom est remplace par le notre
    ② corps emprunte MAIS meme personne      : le texte de Hektor RESTE, entier
       (il porte l'adresse, et parfois un co-mandant que notre texte perdrait)
    ③ ni suspect, ni mandant chez nous       : rien ne bouge
    ④ aucune entree ne perd son texte -- le compteur `videes` doit valoir 0
    ⑤ interrupteur a 0 : AUCUNE difference (preuve du retour arriere)
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
RACINE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RACINE))

from phase2.sync.export_app_payload import (  # noqa: E402  -- IMPORTEES, JAMAIS RECOPIEES
    DETAIL_MANDANTS_DEPUIS_NOS_LIENS,
    PHASE2_DB,
    SQL_DOSSIERS_BASE,
    attach_hektor_read,
    build_trimmed_detail_payload,
    charger_corps_suspects,
    charger_mandants_du_registre_des_liens,
    fetch_rows_by_ids,
    jetons_de_nom,
    mandats_json_avec_nos_mandants,
    normalize_text,
    safe_json_loads,
    sqlite_read_connection,
    texte_des_mandants,
)


def entrees(valeur: object) -> list[dict]:
    """`mandats_json` est tantot une LISTE, tantot un OBJET SEUL."""
    items = safe_json_loads(valeur, None)
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def texte(item: dict) -> str:
    return str(item.get("mandants") or "").strip()


def main() -> int:
    temoins_seuls = "--temoins" in sys.argv
    con = sqlite_read_connection(PHASE2_DB)
    attach_hektor_read(con)

    print("CONTROLE -- la fiche annonce et ses mandants        (lecture seule)")
    print("   interrupteur APP_DETAIL_MANDANTS_DEPUIS_NOS_LIENS : %s"
          % ("1 (allume)" if DETAIL_MANDANTS_DEPUIS_NOS_LIENS else "0 (eteint)"))
    print()

    carte = charger_mandants_du_registre_des_liens(con)
    suspects_par_annonce: dict[str, set[str]] = {}
    for annonce_suspecte, numero_suspect in charger_corps_suspects(con):
        suspects_par_annonce.setdefault(annonce_suspecte, set()).add(numero_suspect)
    annonces_suspectes = set(suspects_par_annonce)

    # ── LES TEMOINS ───────────────────────────────────────────────────────────
    # On les choisit DANS LE PERIMETRE DE L'APP, en interrogeant la meme base
    # que le run : un temoin hors perimetre rendrait 0 ligne et ferait croire a
    # une panne (c'est ce qui etait arrive le 05/10 au chemin immediat).
    # LE PERIMETRE EXACT, copie d'ANNONCES_SCOPE_WHERE comme le fait deja
    # chemin_immediat_paquet.py : hors de lui, SQL_DOSSIERS_BASE ne sert AUCUNE
    # ligne et le temoin echouerait pour une raison qui n'est pas le correctif.
    PERIM = (
        " COALESCE(v.archive, '0') = '0'"
        " AND COALESCE(v.detail_statut_name, v.statut_annonce, '')"
        "     IN ('Actif', 'Sous offre', 'Sous compromis', 'Estimation')"
        " AND v.app_dossier_id IS NOT NULL")
    # Les trois familles, et ce qu'on EXIGE de chacune. Une famille qu'on ne
    # trouve pas est DITE, elle n'est pas sautee en silence.
    ATTENDU = {
        "emprunte_vrai": "doit CHANGER",
        "emprunte_meme_personne": "ne doit PAS changer",
        "ordinaire": "ne doit PAS changer",
    }
    choisis: list[tuple[str, int, int]] = []
    for annonce, dossier, blob in con.execute(
        "SELECT v.hektor_annonce_id, v.app_dossier_id, v.mandats_json"
        " FROM app_view_generale v WHERE " + PERIM +
        " ORDER BY v.app_dossier_id DESC LIMIT 6000"
    ):
        cle = normalize_text(annonce) or ""
        if not cle:
            continue
        numeros = suspects_par_annonce.get(cle) or set()
        nos_jetons = jetons_de_nom(texte_des_mandants(carte.get(cle) or []))
        famille = "ordinaire"
        for item in entrees(blob):
            if (normalize_text(item.get("numero")) or "") not in numeros:
                continue
            famille = ("emprunte_meme_personne"
                       if nos_jetons and jetons_de_nom(texte(item)) & nos_jetons
                       else "emprunte_vrai")
            break
        if sum(1 for f, _, _ in choisis if f == famille) < 2:
            choisis.append((famille, int(annonce), int(dossier)))
        if len(choisis) >= 6:
            break
    for famille in ATTENDU:
        if not any(f == famille for f, _, _ in choisis):
            print("   ⚠ famille « %s » introuvable parmi les 6 000 dossiers lus"
                  " -- NON MESUREE" % famille)

    echecs = 0
    for famille, annonce, dossier in choisis:
        lignes = fetch_rows_by_ids(
            con, base_sql=SQL_DOSSIERS_BASE, id_column="app_dossier_id",
            ids=[dossier], limit=None,
        )
        if not lignes:
            print("   %-22s annonce %-8s ECHEC  aucune ligne lue" % (famille, annonce))
            echecs += 1
            continue
        ligne = lignes[0]
        avant = build_trimmed_detail_payload(ligne, None, None)
        apres = build_trimmed_detail_payload(ligne, carte, suspects_par_annonce)
        ea, ep = entrees(avant.get("mandats_json")), entrees(apres.get("mandats_json"))
        print("   %-24s annonce %-8s dossier %-9s %d mandat(s)   [%s]"
              % (famille, annonce, dossier, len(ep), ATTENDU[famille]))
        if len(ea) != len(ep):
            print("        ECHEC  le nombre d'entrees a change : %d -> %d" % (len(ea), len(ep)))
            echecs += 1
        bouge = False
        for a, p in zip(ea, ep):
            if texte(a) == texte(p):
                print("        n %-7s inchange : %s" % (str(a.get("numero") or "?"),
                                                         texte(a) or "(vide)"))
                continue
            bouge = True
            print("        n %-7s avant : %s" % (str(a.get("numero") or "?"),
                                                  texte(a) or "(vide)"))
            print("                 apres : %s" % (texte(p) or "(vide)"))
            if texte(a) and not texte(p):
                print("        ECHEC  un texte a ete VIDE")
                echecs += 1
        if bouge != (famille == "emprunte_vrai"):
            print("        ECHEC  %s, or la fiche %s"
                  % (ATTENDU[famille], "a change" if bouge else "n'a pas change"))
            echecs += 1
        print()

    if temoins_seuls:
        return 1 if echecs else 0

    # ── LE BILAN SUR TOUTES LES FICHES ────────────────────────────────────────
    # Il appelle `mandats_json_avec_nos_mandants`, la fonction du run. Il ne
    # REJOUE pas la regle : une epreuve qui recode ce qu'elle mesure peut etre
    # verte alors que le code est faux (memoire `eprouver-c-est-executer-le-code`).
    print("BILAN sur toutes les fiches d'annonce")
    total = reecrites = videes = 0
    susp_total = susp_reecrites = susp_intactes = susp_sans_recours = 0
    for annonce_id, blob in con.execute(
        "SELECT hektor_annonce_id, mandats_json FROM hektor.hektor_annonce_detail"
        " WHERE COALESCE(mandats_json,'') <> ''"
    ):
        cle = normalize_text(annonce_id) or ""
        avant_items = entrees(blob)
        if not avant_items:
            continue
        total += len(avant_items)
        numeros = suspects_par_annonce.get(cle) or set()
        nos = carte.get(cle) or []
        apres_blob, n = mandats_json_avec_nos_mandants(blob, nos, numeros)
        reecrites += n
        apres_items = entrees(apres_blob)
        if len(apres_items) != len(avant_items):
            print("   ⛔ annonce %s : %d entrees -> %d"
                  % (cle, len(avant_items), len(apres_items)))
        for a, p in zip(avant_items, apres_items):
            if texte(a) and not texte(p):
                videes += 1
            if (normalize_text(a.get("numero")) or "") not in numeros:
                continue
            susp_total += 1
            if texte(a) != texte(p):
                susp_reecrites += 1
            elif not texte_des_mandants(nos):
                susp_sans_recours += 1
            else:
                susp_intactes += 1
    print("   entrees de mandat dans les fiches          : %d" % total)
    print("   REECRITES depuis notre registre            : %d" % reecrites)
    print("   entrees VIDEES par le correctif            : %d   %s"
          % (videes, "OK" if videes == 0 else "INTERDIT"))
    print()
    print("   couples a corps emprunte rencontres        : %d" % susp_total)
    print("      -> corriges (aucun nom en commun)       : %d" % susp_reecrites)
    print("      -> laisses intacts (meme personne)      : %d" % susp_intactes)
    print("      -> sans recours (nos liens muets)       : %d" % susp_sans_recours)
    if videes:
        echecs += 1

    print()
    print(("ECHEC -- %d probleme(s)" % echecs) if echecs else "OK -- AUCUN ECHEC")
    return 1 if echecs else 0


if __name__ == "__main__":
    raise SystemExit(main())
