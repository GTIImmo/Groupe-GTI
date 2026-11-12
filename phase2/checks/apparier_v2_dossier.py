#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- L'INSTRUCTEUR : il PREPARE, il ne DECIDE pas. 13/11/2026

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ CE QUE CE FICHIER N'EST PAS, ET POURQUOI
═══════════════════════════════════════════════════════════════════════════════
Frederic, 13/11 : *« ton exemple est bon : si tu as DUPONT d'un cote et DUPOND de
l'autre, meme date meme annonce, je pense que tu peux y arriver. **JE DEMANDE DE
L'INTELLIGENCE LIGNE PAR LIGNE, PAS DU CODE.** »*

⭐ Il a raison sur les deux points :
  . mon exemple « DUPONT / DUPOND » servait a dire « aucune intelligence ne peut
    inventer l'information ». C'ETAIT FAUX : quand la date ET l'annonce
    concordent, une lettre d'ecart n'est pas une information manquante, c'est une
    VARIANTE DE SAISIE. Et trancher cela demande du jugement, pas de la magie.
  . et j'avais derive : on me demandait mon jugement, j'ai construit un apparieur
    automatique de plus -- c'est-a-dire ce que la v1 fait deja.

➡ CE FICHIER NE REND AUCUN VERDICT. Il INSTRUIT le dossier d'une ligne : il
  montre tout ce qu'on sait, met les candidats cote a cote, et signale les
  PROXIMITES (noms presque identiques, dates presque identiques, montants
  proches) pour que le jugement se fasse sur des faits, pas sur des souvenirs.
  ⭐ Le verdict est ecrit ensuite A LA MAIN, dans un fichier de decisions, avec
    son motif. C'est la seule facon d'etre « sur a 100 % » : une decision tracee.

═══════════════════════════════════════════════════════════════════════════════
LES REGLES D'INDEPENDANCE TIENNENT TOUJOURS
═══════════════════════════════════════════════════════════════════════════════
  ni `app_classeur_lien` (le gel), ni le CSV de la v1, ni sa logique.

USAGE
    python phase2/checks/apparier_v2_dossier.py --lignes 12,345,678
    python phase2/checks/apparier_v2_dossier.py --verdict "A TRANCHER" --max 10
    python phase2/checks/apparier_v2_dossier.py --id 8Q3LHGZ4
"""
from __future__ import annotations

import argparse
import collections
import csv
import difflib
import io
import json
import sqlite3
import sys
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

from apparier_v2_socle import (chiffres, jour, lire_le_registre,     # noqa: E402
                               lire_le_sheet, noms, noms_du_blob,
                               personnes_du_blob, pur, somme)

ACCORD = RACINE / "notice" / "APPARIEUR_V2_ACCORD_2026-11-13.csv"
CHAMPS_PERSONNES = ("acquereur_json", "acquereurs_json", "mandants_json")


def proche(a: str, b: str) -> float:
    """La ressemblance de deux mots, de 0 a 1. ⭐ C'est elle qui fait voir
    « DUPONT » et « DUPOND » : 0,83. Le code MESURE la ressemblance ;
    il ne decide PAS que c'est la meme personne."""
    return difflib.SequenceMatcher(None, a, b).ratio()


def noms_lisibles(blob) -> str:
    """Les personnes d'un blob, en clair -- pour etre LU, pas compare."""
    out = []
    for p in personnes_du_blob(blob):
        bout = " ".join(str(p.get(k) or "").strip()
                        for k in ("civilite", "prenom", "nom") if p.get(k))
        ident = p.get("id") or p.get("app_contact_id") or ""
        out.append("%s [%s]" % (bout.strip() or "(sans nom)", ident))
    return " | ".join(out) if out else "(aucune personne)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lignes", default="")
    ap.add_argument("--id", default="")
    ap.add_argument("--verdict", default="")
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--candidats", type=int, default=5)
    args = ap.parse_args()

    # ── quelles lignes instruire ? ──────────────────────────────────────────
    voulues: list[str] = []
    if args.lignes:
        voulues = [x.strip() for x in args.lignes.split(",") if x.strip()]
    elif args.id or args.verdict:
        with io.open(ACCORD, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh, delimiter=";"):
                if args.id and pur(r["ID Unique"]) == pur(args.id):
                    voulues.append(r["ligne"])
                elif args.verdict and pur(args.verdict) in pur(r["verdict"]):
                    voulues.append(r["ligne"])
        voulues = voulues[:args.max]
    if not voulues:
        print("rien a instruire : passer --lignes, --id ou --verdict")
        return 1

    tx = lire_le_registre()
    par_bien = collections.defaultdict(list)
    for t in tx:
        par_bien[t["hektor_annonce_id"]].append(t)
    i_mandat = collections.defaultdict(set)
    i_nom = collections.defaultdict(set)
    i_date = collections.defaultdict(set)
    noms_bien = collections.defaultdict(set)
    for t in tx:
        b = t["hektor_annonce_id"]
        m = chiffres(t.get("numero_mandat"))
        if m:
            i_mandat[m].add(b)
        mots: set[str] = set()
        for ch in CHAMPS_PERSONNES:
            mots |= noms_du_blob(t.get(ch))
        noms_bien[b] |= mots
        for mot in mots:
            i_nom[mot].add(b)
        for d in (jour(t.get("date")), jour(t.get("date_acte"))):
            if d:
                i_date[d].add(b)

    # le numero de dossier et la ville, pour eclairer
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""select hektor_annonce_id, mandat_numero_reference, ville, type_bien,
                        statut_annonce
                   from app_registre_mandats_current""")
    infos = {}
    for ann, ref, ville, tb, st in c.fetchall():
        infos.setdefault(ann, {"ref": ref, "ville": ville, "type": tb, "statut": st})
    con.close()

    entetes, lignes = lire_le_sheet()
    par_num = {str(n): l for n, l in lignes}
    ic = {k: (entetes.index(k) if k in entetes else None) for k in entetes}

    def case(l, nom):
        i = ic.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    for num in voulues:
        l = par_num.get(str(num))
        if l is None:
            print("\nligne %s : INTROUVABLE dans le Sheet" % num)
            continue
        print("\n" + "=" * 86)
        print("LIGNE %s DU CLASSEUR   -- ID %s" % (num, case(l, "ID Unique")))
        print("=" * 86)
        for ch in ("Mandat", "Etat Actuel", "Acquéreur", "Vendeur", "Prix", "Ville",
                   "Négociateur 1", "Agence", "Offre Achat", "Compromis",
                   "Vente Prévue", "Vente Fixée", "Annulée", "product_ref",
                   "COMMENTAIRES", "En attente de"):
            v = case(l, ch)
            if v:
                print("   %-16s %s" % (ch, v[:150]))

        man = chiffres(case(l, "Mandat"))
        mots = noms(case(l, "Acquéreur")) | noms(case(l, "Vendeur"))
        dates = {k: jour(case(l, k)) for k in
                 ("Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée")}
        dates = {k: v for k, v in dates.items() if v}
        prix = somme(case(l, "Prix"))

        cand: set = set()
        if man:
            cand |= i_mandat.get(man, set())
        for mot in mots:
            cand |= i_nom.get(mot, set())
        for d in dates.values():
            cand |= i_date.get(d, set())
        # ⭐ ET LE CAS « DUPONT / DUPOND » : on cherche aussi les biens dont un
        #   nom RESSEMBLE a un nom du classeur. C'est ce que le code peut faire
        #   pour preparer le jugement -- il MESURE la ressemblance, il ne conclut pas.
        presque: dict = {}
        if mots and len(cand) < 300:
            for mot in mots:
                for autre, biens in i_nom.items():
                    if autre == mot or abs(len(autre) - len(mot)) > 2:
                        continue
                    r = proche(mot, autre)
                    if r >= 0.80:
                        for b in biens:
                            presque.setdefault(b, set()).add("%s~%s(%.2f)"
                                                             % (mot, autre, r))
            cand |= set(presque)

        if not cand:
            print("\n   AUCUN CANDIDAT -- ni par le mandat, ni par un nom, ni par"
                  " une date, ni par une ressemblance de nom.")
            continue

        # on classe les candidats par nombre de signaux, pour les presenter
        notes = []
        for b in cand:
            sig = []
            if man and b in i_mandat.get(man, set()):
                sig.append("MANDAT")
            comm = mots & noms_bien.get(b, set())
            if comm:
                sig.append("noms:" + ",".join(sorted(comm)))
            jb = {jour(t.get("date")) for t in par_bien[b]} | \
                 {jour(t.get("date_acte")) for t in par_bien[b]}
            jb.discard("")
            dj = [k for k, v in dates.items() if v in jb]
            if dj:
                sig.append("dates:" + ",".join(dj))
            if b in presque:
                sig.append("PRESQUE:" + ",".join(sorted(presque[b])[:3]))
            mts = {somme(t.get("montant")) for t in par_bien[b]}
            mts.discard(None)
            if prix is not None and mts:
                e = min(abs(v - prix) for v in mts)
                if e == 0:
                    sig.append("prix=")
                elif e <= 0.12 * prix:
                    sig.append("prix~%+d" % (min(mts, key=lambda v: abs(v - prix)) - prix))
            notes.append((len(sig), b, sig))
        notes.sort(key=lambda x: -x[0])

        print("\n   --- LES CANDIDATS, a juger (%d en tout) ---" % len(notes))
        for _, b, sig in notes[:args.candidats]:
            inf = infos.get(b, {})
            print("\n   BIEN %s   %s %s   mandat ref %s   statut %s"
                  % (b, inf.get("ville") or "?", inf.get("type") or "",
                     inf.get("ref") or "-", inf.get("statut") or "-"))
            print("      signaux : %s" % " | ".join(sig))
            for t in sorted(par_bien[b], key=lambda z: z["app_affaire_id"]):
                print("      %-9s %-10s %-11s %-12s mandat %-7s n° %s"
                      % (t["kind"], t.get("state") or "-",
                         jour(t.get("date")) or (t.get("date") or "-"),
                         somme(t.get("montant")) if somme(t.get("montant")) is not None else "-",
                         t.get("numero_mandat") or "-", t["app_affaire_id"]))
                for ch in ("acquereurs_json", "acquereur_json", "mandants_json"):
                    if t.get(ch):
                        print("         %-16s %s" % (ch.replace("_json", ""),
                                                     noms_lisibles(t[ch])[:140]))
                        break
    print("\n" + "=" * 86)
    print("AUCUN VERDICT N'A ETE REND U ICI. Ce fichier instruit, il ne decide pas.")
    print("=" * 86)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
