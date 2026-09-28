#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""N.1 — LA CAMPAGNE DES CHAMPS D'ANNONCE : Hektor ignore, accepte, ou calcule ?
                                                                  28/09/2026

POURQUOI CE FICHIER EXISTE
--------------------------
Les transactions ont leurs TROIS CLASSES depuis le 03/09, et c'est ce qui rend leur
cohabitation avec Hektor sure -- sans AUCUNE regle d'arbitrage :

    A  Hektor IGNORE le champ     -> colonne protegee, le run ne l'ecrit jamais
    B  Hektor ACCEPTE l'ecriture  -> l'app pousse, RELIT, ecrit ce que Hektor a RETENU
    C  Hektor CALCULE le champ    -> l'app n'edite pas, lecture seule

L'annonce n'a jamais eu cette mesure. Sans elle, on ne sait pas quel champ peut vivre
chez nous ni lequel se ferait ecraser -- et on ne peut donc ni remplir CHAMPS_APP_ANNONCE
(qui le FIGERAIT, c'est le GEL repere par Frederic le 03/09), ni s'en passer en confiance.

LA METHODE EST CELLE DE LA CAMPAGNE 0.1, MOT POUR MOT
-----------------------------------------------------
    « SANS AUCUNE ECRITURE : le cycle complet avait envoye des valeurs connues,
      il suffisait de relire ce que Hektor a RETENU. »

Ici c'est pareil, et la matiere est DEJA la : chaque travail `update_hektor_annonce_fields`
porte la valeur envoyee ET `base_snapshot` -- ce que Hektor affichait juste avant -- aux
NOMS HEKTOR. Le miroir porte les memes noms. Aucune table de correspondance a inventer,
aucun appel reseau, aucune ecriture nulle part.

    envoye    le travail, dans Supabase
    avant     base_snapshot, dans le meme travail
    retenu    le miroir local, aujourd'hui

    retenu == envoye   -> B    il a garde notre valeur
    retenu == avant    -> A    il n'a rien pris  (ou il a refuse)
    ni l'un ni l'autre -> C ?  quelqu'un d'autre a ecrit : lui, ou un humain depuis

⚠ LE BIAIS, ET IL EST DIT PLUTOT QUE MASQUE. Entre un envoi de mai et le miroir
  d'aujourd'hui, une valeur a pu changer LEGITIMEMENT (le negociateur corrige son bien).
  Un verdict n'est donc SUR que si l'envoi est recent et qu'aucune autre ecriture n'a eu
  lieu depuis. Le script affiche l'age de chaque envoi et compte a part les cas anciens.
  Il ne rend JAMAIS un verdict « C » seul : il ecrit « C ou modifie depuis », et c'est a
  la relecture humaine de trancher.

⚠ CE QU'IL NE FAIT PAS. Aucune ecriture, aucun appel a Hektor, aucun travail cree. Il ne
  decide pas non plus ce qu'on fera des classes : c'est N.2 et N.3.

USAGE
-----
    python phase2/checks/campagne_champs_annonce.py
    python phase2/checks/campagne_champs_annonce.py --depuis 2026-08-01
    python phase2/checks/campagne_champs_annonce.py --detail        # ligne par ligne
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# La console Windows de ce poste est en cp1252 : elle ne sait pas ECRIRE les symboles
# affiches ici. Meme correctif que phase2/checks/verifier_renvois_liste.py (27/09) --
# un verificateur qui meurt sur un caractere ne verifie rien.
for _flux in (sys.stdout, sys.stderr):
    try:
        _flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE = Path(__file__).resolve().parents[2]
MIROIR = RACINE / "data" / "hektor.sqlite"
ENV_FILES = (RACINE / ".env", RACINE / "apps" / "hektor-v1" / ".env")

# Les clefs de service du travail, qui ne sont pas des champs d'annonce.
HORS_CHAMPS = {
    "source", "from_pending", "base_snapshot", "app_dossier_id", "hektor_annonce_id",
    "requested_by", "origin", "reason", "job_origin", "pending_key", "repair_reason",
    "hektor_user_id", "hektor_user_label", "hektor_user_email", "hektor_agence_id",
    "hektor_negociator_form_id", "agence_nom", "fields", "fields_json",
}


def charger_env() -> tuple[str, str]:
    for chemin in ENV_FILES:
        try:
            if not chemin.exists():
                continue
            for ligne in chemin.read_text(encoding="utf-8").splitlines():
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "=" not in ligne:
                    continue
                cle, valeur = ligne.split("=", 1)
                cle = cle.strip()
                if cle and cle not in os.environ:
                    os.environ[cle] = valeur.strip().strip('"').strip("'")
        except OSError:
            continue
    base = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").strip().rstrip("/")
    cle = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    return base, cle


def lire_envois(base: str, cle: str, depuis: str | None) -> list[dict]:
    """Les travaux de modification d'annonce, pagines PAR CURSEUR (jamais offset)."""
    out: list[dict] = []
    apres = "1970-01-01"
    if depuis:
        apres = depuis
    while True:
        q = urllib.parse.urlencode({
            "select": "id,created_at,status,payload_json",
            "job_type": "eq.update_hektor_annonce_fields",
            "created_at": f"gt.{apres}",
            "order": "created_at.asc",
            "limit": "500",
        })
        req = urllib.request.Request(
            f"{base}/rest/v1/app_console_job?{q}",
            headers={"apikey": cle, "Authorization": f"Bearer {cle}"})
        with urllib.request.urlopen(req, timeout=60) as rep:
            lot = json.loads(rep.read().decode("utf-8"))
        if not lot:
            break
        out.extend(lot)
        apres = lot[-1]["created_at"]
        if len(lot) < 500:
            break
    return out


def chercher(obj, nom: str):
    """La valeur du champ `nom`, ou qu'il soit dans le blob de Hektor.

    Le raw_json range ses champs par groupes (keyData, diagnostiques.props...), et le
    nom exact est le meme partout. On descend donc partout plutot que de tenir une
    carte des groupes -- une carte se perime, la recherche non.
    """
    if isinstance(obj, dict):
        if nom in obj and not isinstance(obj[nom], (dict, list)):
            return obj[nom]
        # la forme {"value": ...} des props de Hektor
        if nom in obj and isinstance(obj[nom], dict) and "value" in obj[nom]:
            return obj[nom]["value"]
        for v in obj.values():
            trouve = chercher(v, nom)
            if trouve is not None:
                return trouve
    elif isinstance(obj, list):
        for v in obj:
            trouve = chercher(v, nom)
            if trouve is not None:
                return trouve
    return None


def pareil(a, b) -> bool:
    """Comparaison tolerante : Hektor rend « 6 », « 6.0 » et « 6 » pour la meme chose."""
    if a is None or b is None:
        return a is None and b is None
    ta, tb = str(a).strip(), str(b).strip()
    if ta == tb:
        return True
    try:
        return abs(float(ta.replace(",", ".")) - float(tb.replace(",", "."))) < 1e-9
    except (TypeError, ValueError):
        return ta.casefold() == tb.casefold()


def main() -> int:
    ap = argparse.ArgumentParser(description="N.1 -- la campagne des champs d'annonce (lecture seule).")
    ap.add_argument("--depuis", default=None, help="Ne regarder que les envois apres cette date (AAAA-MM-JJ).")
    ap.add_argument("--detail", action="store_true", help="Une ligne par envoi.")
    args = ap.parse_args()

    base, cle = charger_env()
    if not base or not cle:
        print("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents", file=sys.stderr)
        return 2
    if not MIROIR.exists():
        print(f"miroir introuvable : {MIROIR}", file=sys.stderr)
        return 2

    envois = lire_envois(base, cle, args.depuis)
    print("=" * 78)
    print("N.1 -- LA CAMPAGNE DES CHAMPS D'ANNONCE           envoye / avant / retenu")
    print("=" * 78)
    print(f"travaux lus : {len(envois)}")

    m = sqlite3.connect(f"file:{MIROIR}?mode=ro", uri=True)
    cache: dict[str, dict] = {}

    # ⚠ LE MIROIR A PLUSIEURS SOURCES, ET UNE SEULE NE SUFFIT PAS. Ma premiere version ne
    #   lisait que `raw_json` (l'API REST) et declarait « absent » des champs qui reviennent
    #   par un AUTRE chemin -- le chauffage arrive par le scrutage de la console
    #   (`chauffage_console_json`), jamais par l'API : c'est ecrit en memoire du projet
    #   depuis des semaines. Conclure sur une seule source, c'est inventer des absences.
    SOURCES_DETAIL = ("raw_json", "localite_json", "zones_json", "particularites_json",
                      "pieces_json", "terrain_json", "copropriete_json", "honoraires_json",
                      "mandats_json", "proprietaires_json", "textes_json")

    def miroir_de(annonce: str) -> dict:
        if annonce not in cache:
            fond: dict = {}
            colonnes = {r[1] for r in m.execute("pragma table_info(hektor_annonce_detail)")}
            voulues = [c for c in SOURCES_DETAIL if c in colonnes]
            if voulues:
                r = m.execute("select %s from hektor_annonce_detail where hektor_annonce_id=?"
                              % ", ".join(voulues), (annonce,)).fetchone()
                if r:
                    for nom, brut in zip(voulues, r):
                        if not brut:
                            continue
                        try:
                            fond[nom] = json.loads(brut)
                        except (ValueError, TypeError):
                            pass
            # la table plate (prix, titre, statut...) et le chauffage, qui n'arrive QUE par la console
            for table in ("hektor_annonce", "hektor_annonce_chauffage_detail",
                          "hektor_annonce_console_detail"):
                try:
                    cols = [x[1] for x in m.execute("pragma table_info(%s)" % table)]
                except sqlite3.Error:
                    continue
                if not cols:
                    continue
                try:
                    lig = m.execute("select * from %s where hektor_annonce_id=? limit 1" % table,
                                    (annonce,)).fetchone()
                except sqlite3.Error:
                    continue
                if not lig:
                    continue
                for nom, val in zip(cols, lig):
                    if isinstance(val, str) and val.strip().startswith(("{", "[")):
                        try:
                            fond["%s.%s" % (table, nom)] = json.loads(val)
                            continue
                        except ValueError:
                            pass
                    fond.setdefault(nom, val)
            cache[annonce] = fond
        return cache[annonce]

    verdicts: dict[str, dict[str, int]] = {}
    lignes: list[tuple] = []
    sans_miroir = 0

    for j in envois:
        p = j.get("payload_json") or {}
        if isinstance(p, str):
            try:
                p = json.loads(p)
            except ValueError:
                continue
        annonce = str(p.get("hektor_annonce_id") or "").strip()
        if not annonce:
            continue
        avant_tout = p.get("base_snapshot") or {}
        fond = miroir_de(annonce)
        if not fond:
            sans_miroir += 1
            continue
        for champ, envoye in p.items():
            if champ in HORS_CHAMPS or isinstance(envoye, (dict, list)):
                continue
            avant = avant_tout.get(champ) if isinstance(avant_tout, dict) else None
            retenu = chercher(fond, champ)
            if retenu is None:
                verdict = "absent du miroir"
            elif pareil(retenu, envoye):
                verdict = "B accepte"
            elif avant is not None and pareil(retenu, avant):
                verdict = "A ignore"
            else:
                verdict = "C ou modifie depuis"
            verdicts.setdefault(champ, {}).setdefault(verdict, 0)
            verdicts[champ][verdict] += 1
            lignes.append((j["created_at"][:10], annonce, champ, envoye, avant, retenu, verdict))

    if sans_miroir:
        print(f"⚠ {sans_miroir} travail(s) ecarte(s) : annonce absente du miroir local")
    print()

    if args.detail:
        print(f"{'date':<11}{'annonce':<9}{'champ':<24}{'envoye':<14}{'avant':<14}{'retenu':<14}verdict")
        for l in sorted(lignes):
            print("%-11s%-9s%-24s%-14s%-14s%-14s%s" % (
                l[0], l[1], l[2][:23], str(l[3])[:13], str(l[4])[:13], str(l[5])[:13], l[6]))
        print()

    print(f"{'champ':<26}{'B accepte':>10}{'A ignore':>10}{'C/modifie':>11}{'absent':>8}   verdict net")
    print("-" * 78)
    net = {"B": [], "A": [], "C": [], "?": []}
    for champ in sorted(verdicts, key=lambda c: -sum(verdicts[c].values())):
        v = verdicts[champ]
        b, a, c, x = (v.get("B accepte", 0), v.get("A ignore", 0),
                      v.get("C ou modifie depuis", 0), v.get("absent du miroir", 0))
        if b and not a and not c:
            marque, ou = "B", "B"
        elif a and not b and not c:
            marque, ou = "A", "A"
        elif c and not b and not a:
            marque, ou = "C ?", "C"
        else:
            marque, ou = "a relire", "?"
        net[ou].append(champ)
        print("%-26s%10d%10d%11d%8d   %s" % (champ, b, a, c, x, marque))

    print()
    print("=" * 78)
    print(f"  B (Hektor ACCEPTE)  : {len(net['B']):>3} champ(s)")
    print(f"  A (Hektor IGNORE)   : {len(net['A']):>3} champ(s)   <- les seuls a proteger")
    print(f"  C ou modifie depuis : {len(net['C']):>3} champ(s)   <- a relire un par un")
    print(f"  a relire (melange)  : {len(net['?']):>3} champ(s)")
    print("=" * 78)
    if net["A"]:
        print("\nCANDIDATS CLASSE A :", ", ".join(sorted(net["A"])))
    print("\n⚠ Un verdict n'est sur que si l'envoi est RECENT : une valeur a pu changer")
    print("  legitimement depuis. Relancer avec --depuis pour ne garder que le recent,")
    print("  et --detail pour lire les cas un par un avant de conclure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
