#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE PLAFOND DE SUPPRESSION DES CONTACTS, RELATIONS ET RECHERCHES.   13/11/2026

Audit : notice/AUDIT_SUPPRESSION_HEKTOR_TOUTES_FAMILLES_2026-11-13.md

CE QU'IL EPROUVE
----------------
  (1) LE TEMOIN INVERSE, ET IL PASSE EN PREMIER : une nuit NORMALE ne doit rien dire.
     Les chiffres sont ceux VRAIMENT mesures dans logs/scheduled/quotidien_*.log
     sur 34 nuits (14/10 -> 13/11) -- 18 relations le 13/11, 58 le 28/10 (le pic
     de la panne Hektor), 28 recherches le 14/10 (l'incident). * Si l'un d'eux
     faisait echouer le push, le garde-fou crierait tous les jours : il ne serait
     plus un garde-fou.
  (2) LE REFUS : au-dela du plafond, chaque table leve, et le message NOMME la table
     et les deux nombres.
  (3) L'ORDRE, et c'est le vrai controle : la verification est appelee AVANT la
     premiere suppression, dans LES DEUX branches (nuit complete et envoi cible).
     Un garde-fou pose apres le premier DELETE laisserait un arret a moitie.
  (4) L'INTERRUPTEUR --allow-stale-deletes laisse passer.
  (5) LES PLAFONDS SONT AU-DESSUS DES MAXIMA MESURES -- le lien entre le code et
     la mesure, pour qu'un futur reglage ne puisse pas descendre sous le reel.

! IL N'ECRIT RIEN, N'OUVRE AUCUNE BASE ET NE FAIT AUCUN APPEL RESEAU.

    python -I phase2/checks/test_plafond_suppression_contacts.py
    sortie 0 = vert . 1 = un controle en echec . 2 = n'a pas pu mesurer
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
SOURCE = RACINE / "phase2" / "sync" / "push_contacts_to_supabase.py"
if str(RACINE / "phase2" / "sync") not in sys.path:
    sys.path.insert(0, str(RACINE / "phase2" / "sync"))

ECHECS: list[str] = []


def controle(libelle: str, condition: bool, detail: str = "") -> None:
    print(("  OK   " if condition else "  ECHEC ") + libelle + (("  -- " + detail) if detail and not condition else ""))
    if not condition:
        ECHECS.append(libelle)


class FauxArgs:
    def __init__(self, allow: bool = False) -> None:
        self.allow_stale_deletes = allow


def main() -> int:
    try:
        import push_contacts_to_supabase as push
    except Exception as exc:                                        # noqa: BLE001
        print("N'A PAS PU MESURER : import impossible (%s)" % type(exc).__name__)
        return 2

    verifier = getattr(push, "verifier_plafonds_de_suppression", None)
    plafonds = getattr(push, "PLAFONDS_SUPPRESSION", None)
    if verifier is None or plafonds is None:
        print("N'A PAS PU MESURER : le garde-fou n'existe pas dans le module.")
        return 2

    def leve(charge: dict, allow: bool = False) -> str | None:
        """Rend le message si ca leve, None sinon."""
        try:
            verifier(charge, FauxArgs(allow))
        except RuntimeError as exc:
            return str(exc)
        return None

    def cles(n: int) -> list[str]:
        return [str(i) for i in range(n)]

    print()
    print("(1) LE TEMOIN INVERSE -- les nuits REELLEMENT mesurees doivent PASSER")
    controle("13/11 : 18 relations (la nuit d'hier) passe",
             leve({"app_contact_relation_current": cles(18)}) is None)
    controle("28/10 : 58 relations (le pic de la panne Hektor) passe",
             leve({"app_contact_relation_current": cles(58)}) is None)
    controle("14/10 : 28 recherches (l'incident documente) passe",
             leve({"app_contact_search_current": cles(28)}) is None)
    controle("le maximum contacts jamais vu (1) passe",
             leve({"app_contact_current": cles(1)}) is None)
    controle("une nuit vide passe", leve({}) is None)
    controle("les trois tables ENSEMBLE a leur maximum reel passent",
             leve({"app_contact_current": cles(1),
                   "app_contact_search_current": cles(28),
                   "app_contact_relation_current": cles(58)}) is None)

    print()
    print("(2) LE REFUS -- au-dela du plafond, chaque table leve et se NOMME")
    for table, plafond in sorted(plafonds.items()):
        msg = leve({table: cles(plafond + 1)})
        controle("%s : %d leve" % (table, plafond + 1), msg is not None)
        if msg:
            controle("   le message nomme la table", table in msg, msg[:120])
            controle("   le message donne les deux nombres",
                     str(plafond + 1) in msg and str(plafond) in msg, msg[:120])
            controle("   le message dit que RIEN n'a ete supprime",
                     "AUCUNE" in msg, msg[:120])
        # le plafond EXACT ne leve pas : la regle est « au-dela », pas « a partir de »
        controle("%s : %d (le plafond exact) NE leve PAS" % (table, plafond),
                 leve({table: cles(plafond)}) is None)

    print()
    print("(3) L'ORDRE -- la verification precede la premiere suppression, DANS LES DEUX BRANCHES")
    try:
        texte = io.open(SOURCE, encoding="utf-8", errors="replace").read()
    except Exception as exc:                                        # noqa: BLE001
        print("N'A PAS PU MESURER : source illisible (%s)" % type(exc).__name__)
        return 2

    # La branche NUIT COMPLETE commence a `if not contact_ids:` ; la branche CIBLEE
    # a `cible_a_supprimer`. On regarde dans CHACUNE que l'appel au garde-fou arrive
    # avant le premier appel qui detruit.
    i_nuit = texte.find("if not contact_ids:")
    i_cible = texte.find("cible_a_supprimer: dict")
    controle("les deux branches sont trouvees dans le source", i_nuit > 0 and i_cible > i_nuit,
             "nuit=%d cible=%d" % (i_nuit, i_cible))
    if i_nuit > 0 and i_cible > i_nuit:
        bloc_nuit = texte[i_nuit:i_cible]
        bloc_cible = texte[i_cible:]
        for nom, bloc in (("nuit complete", bloc_nuit), ("envoi cible", bloc_cible)):
            garde = bloc.find("verifier_plafonds_de_suppression(")
            # le premier geste qui DETRUIT, quel qu'il soit
            gestes = [bloc.find("client.delete_rows_by_key("), bloc.find("delete_contacts_except_dirty(\n")]
            gestes = [g for g in gestes if g >= 0]
            # delete_contacts_except_dirty apparait aussi en commentaire : on prend
            # le premier APPEL reel, repere par la parenthese ouvrante suivie d'un saut.
            premier = min(gestes) if gestes else -1
            controle("%s : le garde-fou est present" % nom, garde >= 0)
            controle("%s : une suppression existe bien (temoin)" % nom, premier >= 0)
            if garde >= 0 and premier >= 0:
                controle("%s : le garde-fou est AVANT la premiere suppression" % nom,
                         garde < premier, "garde=%d premiere_suppression=%d" % (garde, premier))

    print()
    print("(4) L'INTERRUPTEUR")
    controle("--allow-stale-deletes laisse passer 100 000 suppressions",
             leve({"app_contact_current": cles(100000)}, allow=True) is None)
    controle("sans l'interrupteur, les memes 100 000 levent",
             leve({"app_contact_current": cles(100000)}) is not None)

    print()
    print("(5) LES PLAFONDS RESTENT AU-DESSUS DU REEL MESURE (34 nuits)")
    maxima = {"app_contact_current": 1, "app_contact_search_current": 28,
              "app_contact_relation_current": 58}
    for table, maxi in sorted(maxima.items()):
        p = plafonds.get(table)
        controle("%s : plafond %s > maximum mesure %d" % (table, p, maxi),
                 p is not None and p > maxi)
    controle("aucune table protegee n'a ete oubliee",
             set(plafonds) == set(maxima), str(sorted(set(plafonds) ^ set(maxima))))

    print()
    if ECHECS:
        print("ECHEC : %d controle(s) en echec" % len(ECHECS))
        for e in ECHECS:
            print("   . " + e)
        return 1
    print("VERT : tous les controles passent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
