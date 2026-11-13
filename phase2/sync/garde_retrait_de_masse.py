#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE GARDE-FOU DU RETRAIT DE MASSE -- un seul endroit.        13/11/2026

Audit : notice/AUDIT_SUPPRESSION_HEKTOR_TOUTES_FAMILLES_2026-11-13.md

POURQUOI UN MODULE A PART, ET PAS UNE COPIE DANS CHAQUE REGISTRE.
Le projet a paye trois fois la regle inverse : une protection ecrite deux fois
finit par diverger, et une exclusion rangee a cote sans etre appelee partout
recree le defaut (les brouillons, 20/10). Les registres des MANDATS et des
RELATIONS ont exactement le meme besoin : ils ont donc exactement le meme code,
ecrit UNE fois, ici.

CE QUI MANQUAIT. Les deux registres se protegent deja du silence TOTAL :

    if full and vus_ce_run:        # <- rien n'a ete lu -> on ne marque rien

C'est juste, mais c'est du tout-ou-rien : une nuit ou Hektor rend UN mandat sur
26 921 passe cette garde, et les 26 920 autres sont marques absents. Le seuil
ci-dessous attrape ce cas -- celui d'une lecture PARTIELLE.

⭐ LE PATRON EXISTE DEJA DANS LE PROJET, on ne l'invente pas :
    annonces      push_upgrade_to_supabase.py : --max-stale-deletes 500, RuntimeError
    transactions  normalize_source.py         : SEUIL_MIROIR_COMPLET = 0.5
    contacts      push_contacts_to_supabase.py: PLAFONDS_SUPPRESSION (13/11)

⛔⛔ ET LE PIEGE DES MANDATS, MESURE LE 13/11 -- NE PAS COMPTER A L'AVEUGLE.
Sur 568 mandats marques `present_in_hektor = 0`, **UN SEUL** a vraiment disparu
de Hektor. Les 567 autres viennent du REGISTRE LEGAL 2014-2024 et de MODELO :
ils n'ont jamais ete chez Hektor, ils NAISSENT avec le drapeau a false, et c'est
leur etat normal. Ils sont tous entres la meme nuit, le 28/10 a 14:57.
    ➡ Un plafond naif aurait REFUSE cet import legitime.
    ➡ L'appelant ne compte donc que les VRAIES disparitions : celles qui portent
      un identifiant Hektor. Voir `hektor_mandat_id is not null` chez l'appelant.

L'INTERRUPTEUR, meme forme que le reste du projet (.env, lu a chaud) :
    APP_RETRAIT_DE_MASSE_AUTORISE=1   laisse passer, pour un elargissement VOULU
    absent ou 0                       le garde-fou mord (defaut)
"""
from __future__ import annotations

import os

# Plafonds CALIBRES SUR LES JOURNAUX DU RUN (34 nuits, 14/10 -> 13/11), pas au
# doigt mouille. La marge est large EXPRES : le but est d'attraper une nuit a
# 5 000, pas a 20. Un garde-fou qui crie tous les jours n'en est plus un.
#
#   famille      vivants    plus forte nuit observee    plafond
#   relations    132 937            17                    500
#   mandats       26 921             1 (vraie disparition) 200
PLAFONDS = {
    "relations": 500,
    "mandats": 200,
}


class RetraitDeMasseRefuse(RuntimeError):
    """Leve AVANT le moindre marquage. Rien n'a ete ecrit."""


def autorise_par_l_environnement() -> bool:
    return (os.environ.get("APP_RETRAIT_DE_MASSE_AUTORISE") or "0").strip() == "1"


def verifier(famille: str, combien: int, *, total_vivants: int | None = None) -> None:
    """Refuse un retrait de masse. A appeler AVANT d'ecrire quoi que ce soit.

    `combien` ne compte QUE les vraies disparitions (voir le piege des mandats).
    `total_vivants` n'entre pas dans la decision : il ne sert qu'au message, pour
    qu'un humain voie tout de suite l'ampleur sans aller la chercher.
    """
    plafond = PLAFONDS.get(famille)
    if plafond is None or combien <= plafond:
        return
    if autorise_par_l_environnement():
        print(f"[{famille}] retrait de masse de {combien} ligne(s) AUTORISE "
              f"par APP_RETRAIT_DE_MASSE_AUTORISE (plafond {plafond}).")
        return
    part = ""
    if total_vivants:
        part = f", soit {100.0 * combien / total_vivants:.1f} % des {total_vivants} vivantes"
    # ON LE DIT AVANT DE LEVER : le message de l'exception peut etre tronque dans
    # le compte rendu du run ; cette ligne-la ne l'est pas.
    print(f"[{famille}] ARRET DE SECURITE : retrait de masse refuse -- "
          f"{combien} > {plafond}{part}. AUCUNE ligne n'a ete marquee.")
    raise RetraitDeMasseRefuse(
        f"Arret de securite ({famille}) : {combien} lignes allaient etre marquees "
        f"absentes, plafond {plafond}{part}. AUCUNE n'a ete touchee. Si c'est voulu, "
        f"relancer avec APP_RETRAIT_DE_MASSE_AUTORISE=1 apres avoir regarde POURQUOI "
        f"il y en a autant."
    )
