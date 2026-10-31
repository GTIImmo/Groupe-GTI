#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COUPLES · PIECE C — LE FILET DE LA NUIT POUR LA SECONDE FICHE D'UN COUPLE.
                                                                  31/10/2026

Note : notice/COUPLES_ERGONOMIE_ET_ECRITURE_PROPOSITION_2026-10-30.md §15-§17.

LE TROU. Creer un couple dans l'app ecrit les DEUX personnes chez nous (piece A,
interrupteur `couple_nait_complet`), et le worker range le numero Hektor de la
seconde fiche dans la case cible de la personne 2 (piece B). Si le worker l'a
rate (Hektor lent, refus, fiche plus loin que 3), la personne 2 reste sans cible.
La meme nuit, la seconde fiche arrive de Hektor ; le registre (registre_contacts.py)
ne la reconnait pas -- il n'adopte que par la case cible -- et lui donne un numero
de la serie 10 M : la personne 2 existerait DEUX fois.

LE FILET. Juste AVANT la descente de la correspondance, on cherche dans le MIROIR
la fiche de Hektor qui designe la personne 1 (`refCouple`), et on pose la case
cible de la personne 2 -- la meme ecriture que le worker. La descente ramene alors
la paire, le build range la seconde fiche sous NOTRE numero, le registre l'adopte.

AUCUNE REQUETE CHEZ HEKTOR : le miroir et Supabase seulement.

ON N'ECRIT QUE SI ON EST SUR, et sinon on le DIT :
  · une seule fiche du miroir designe la personne 1 (hors elle-meme) ;
  · personne d'autre ne porte deja ce numero (Supabase ET registre local) ;
  · le nom de famille concorde (un temoin en plus du lien de Hektor) ;
  · la case de la personne 2 est encore vide (ecriture conditionnelle).
Si on ne tranche pas, la nuit fait exactement ce qu'elle faisait avant : ce
script n'aggrave rien, il repare quand il est sur.

SORTIE : 0 = rien a faire, ou tout est rattache · 1 = au moins un cas NON tranche
(dit, ligne par ligne) · 2 = lecture impossible (on ne sait pas -- ce n'est pas un
vert). L'etape du run est NON BLOQUANTE.

    python phase2/identite/rattacher_secondes_fiches.py --a-blanc   # dit, n'ecrit rien

IDEMPOTENT : une personne 2 rattachee a sa cible et sort de la liste.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
MIROIR = RACINE / "data" / "hektor.sqlite"
BASE = RACINE / "phase2" / "phase2.sqlite"
PLAGE_NES_DANS_L_APP = 20_000_000
PLAGE_APP = 10_000_000

sys.path.insert(0, str(RACINE / "phase2" / "sync"))


def nom_compare(valeur: object) -> str:
    """Majuscules, sans accents, espaces et tirets reduits : « Le Gall » = « LE-GALL »."""
    texte = unicodedata.normalize("NFD", str(valeur or ""))
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn").upper()
    for signe in "-'’.":
        texte = texte.replace(signe, " ")
    return " ".join(texte.split())


class Supabase:
    """Les 3 gestes dont on a besoin, par l'API REST et la cle de service."""

    def __init__(self) -> None:
        from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: E402
        for fichier in DEFAULT_ENV_FILES:
            load_env_file(fichier)
        url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
        self.cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not self.cle:
            raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        self.base = f"{url.rstrip('/')}/rest/v1/app_contact_current"

    def _appel(self, requete: str, methode: str = "GET", corps: dict | None = None) -> list:
        entetes = {"apikey": self.cle, "Authorization": f"Bearer {self.cle}", "Accept": "application/json"}
        donnees = None
        if corps is not None:
            entetes["Content-Type"] = "application/json"
            entetes["Prefer"] = "return=representation"
            donnees = json.dumps(corps).encode("utf-8")
        demande = urllib.request.Request(f"{self.base}?{requete}", data=donnees, headers=entetes, method=methode)
        with urllib.request.urlopen(demande, timeout=60) as reponse:
            texte = reponse.read().decode("utf-8")
        resultat = json.loads(texte) if texte else []
        return resultat if isinstance(resultat, list) else []

    def personnes2_sans_cible(self) -> list[dict]:
        # Nes dans l'app, sans cible, rattaches a un menage. Quelques lignes au plus :
        # une seule page suffit, et on le VERIFIE (plafond) plutot que de l'esperer.
        lignes = self._appel(
            f"select=hektor_contact_id,nom,hektor_couple_contact_id"
            f"&app_contact_id=gte.{PLAGE_NES_DANS_L_APP}&hektor_target_id=is.null"
            f"&hektor_couple_contact_id=not.is.null&order=hektor_contact_id.asc&limit=1000")
        if len(lignes) >= 1000:
            raise RuntimeError("1 000 personnes 2 sans cible ou plus : au-dela du concevable, on s'arrete.")
        return [l for l in lignes if str(l.get("hektor_couple_contact_id") or "") != str(l.get("hektor_contact_id") or "")]

    def cibles_des_premieres(self, identites: list[str]) -> dict[str, str]:
        if not identites:
            return {}
        liste = ",".join(identites)
        lignes = self._appel(f"select=hektor_contact_id,hektor_target_id&hektor_contact_id=in.({liste})")
        return {str(l["hektor_contact_id"]): str(l.get("hektor_target_id") or "") for l in lignes}

    def porteurs(self, numero_hektor: str) -> list[str]:
        lignes = self._appel(f"select=hektor_contact_id&hektor_target_id=eq.{urllib.parse.quote(numero_hektor)}")
        return [str(l.get("hektor_contact_id") or "") for l in lignes]

    def poser_cible(self, identite: str, numero_hektor: str) -> int:
        lignes = self._appel(
            f"hektor_contact_id=eq.{urllib.parse.quote(identite)}&hektor_target_id=is.null",
            methode="PATCH", corps={"hektor_target_id": numero_hektor})
        return len(lignes)


def connu_du_registre(base: sqlite3.Connection | None, numero_hektor: str) -> str | None:
    """L'identite que le registre local donne deja a ce numero Hektor, s'il en donne une."""
    if base is None:
        return None
    ligne = base.execute(
        "SELECT hektor_contact_id FROM app_contact WHERE hektor_target_id = ? OR hektor_contact_id = ? LIMIT 1",
        (numero_hektor, numero_hektor)).fetchone()
    return str(ligne[0]) if ligne else None


def decider(personne2: dict, cible_premiere: str, miroir: sqlite3.Connection,
            supabase, base: sqlite3.Connection | None) -> tuple[str, str | None, str]:
    """(verdict, numero Hektor de la seconde fiche, explication).
    verdict : « rattacher », « attendre » (rien de decidable cette nuit, sans alarme)
    ou « doute » (on n'ecrit pas, et on le dit)."""
    identite = str(personne2["hektor_contact_id"])
    if not (cible_premiere.isdigit() and int(cible_premiere) < PLAGE_APP):
        return "attendre", None, "la personne 1 n'a pas encore son numero Hektor"
    candidates = miroir.execute(
        "SELECT hektor_contact_id, nom FROM hektor_contact "
        "WHERE hektor_couple_contact_id = ? AND hektor_contact_id <> ?",
        (cible_premiere, cible_premiere)).fetchall()
    if not candidates:
        return "attendre", None, f"aucune fiche du miroir ne designe {cible_premiere} (pas encore descendue ?)"
    if len(candidates) > 1:
        return "doute", None, (f"{len(candidates)} fiches designent {cible_premiere} : "
                               + ", ".join(str(c[0]) for c in candidates))
    numero, nom_miroir = str(candidates[0][0]), candidates[0][1]
    if nom_compare(nom_miroir) != nom_compare(personne2.get("nom")):
        return "doute", numero, f"le nom de famille ne concorde pas avec la fiche {numero}"
    autres = [p for p in supabase.porteurs(numero) if p and p != identite]
    if autres:
        return "doute", numero, f"le numero {numero} est deja porte par {', '.join(autres)}"
    deja = connu_du_registre(base, numero)
    if deja and deja != identite:
        return "doute", numero, f"le registre local donne deja l'identite {deja} au numero {numero}"
    return "rattacher", numero, f"la fiche {numero} designe {cible_premiere}, nom concordant"


def executer(supabase, miroir: sqlite3.Connection, base: sqlite3.Connection | None, a_blanc: bool) -> int:
    personnes2 = supabase.personnes2_sans_cible()
    if not personnes2:
        print("[secondes fiches] aucune personne 2 nee dans l'app n'attend sa case cible : rien a faire.")
        return 0
    cibles = supabase.cibles_des_premieres(sorted({str(p["hektor_couple_contact_id"]) for p in personnes2}))
    doutes = 0
    for p in personnes2:
        identite = str(p["hektor_contact_id"])
        premiere = str(p["hektor_couple_contact_id"])
        verdict, numero, pourquoi = decider(p, cibles.get(premiere, ""), miroir, supabase, base)
        if verdict == "rattacher":
            if a_blanc:
                print(f"[secondes fiches] A BLANC : {identite} recevrait la cible {numero} ({pourquoi})")
                continue
            ecrites = supabase.poser_cible(identite, numero)
            if ecrites == 1:
                print(f"[secondes fiches] {identite} rattachee a la fiche Hektor {numero} ({pourquoi})")
            else:
                doutes += 1
                print(f"[secondes fiches] NON ECRIT : {identite} -> {numero}, {ecrites} ligne(s) modifiee(s) "
                      "(case deja pourvue entre-temps ?)")
        elif verdict == "attendre":
            print(f"[secondes fiches] {identite} attend : {pourquoi}")
        else:
            doutes += 1
            print(f"[secondes fiches] DOUTE, rien n'est ecrit pour {identite} : {pourquoi}")
    return 1 if doutes else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Rattache la seconde fiche d'un couple ne dans l'app a sa personne 2.")
    ap.add_argument("--a-blanc", action="store_true", help="dire ce qui serait fait, sans rien ecrire")
    args = ap.parse_args()
    try:
        supabase = Supabase()
        miroir = sqlite3.connect(f"file:{MIROIR.as_posix()}?mode=ro", uri=True, timeout=60)
        base = sqlite3.connect(f"file:{BASE.as_posix()}?mode=ro", uri=True, timeout=60) if BASE.exists() else None
    except Exception as erreur:
        print(f"[secondes fiches] LECTURE IMPOSSIBLE : {type(erreur).__name__}: {erreur}")
        return 2
    try:
        return executer(supabase, miroir, base, args.a_blanc)
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, sqlite3.Error) as erreur:
        print(f"[secondes fiches] LECTURE IMPOSSIBLE : {type(erreur).__name__}: {erreur}")
        return 2
    finally:
        miroir.close()
        if base is not None:
            base.close()


if __name__ == "__main__":
    raise SystemExit(main())
