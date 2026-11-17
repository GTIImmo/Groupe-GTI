#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QUE MANQUE-T-IL ENCORE, APRES TOUT CE QU'ON A POSE ?            17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\classeur_ce_qui_manque_encore_2026-11-17.py

⛔ LECTURE SEULE.

Sa question du 17/11 : « alors que je pensais avoir fini le rattrapage ». Elle est
juste, et ma reponse precedente etait trop etroite : je n'avais mesure QUE LES
VENTES (C6). Ici on mesure LES TROIS TYPES, pour dire ce qui manque vraiment.

⭐ LES TROIS DATES DU CLASSEUR ET CE QU'ELLES PROUVENT :
     « Offre Achat »   -> une OFFRE a existe
     « Compromis »     -> un COMPROMIS a ete signe
     « Vente Réglée »  -> une VENTE a eu lieu
   Pour chacune : la date est-elle lisible ? la ligne est-elle reliee ? et avons-nous
   la transaction correspondante ?

⛔ ET ON NE CONFOND PAS DEUX CHOSES, c'est la faute que le plan a deja corrigee le
  16/11 : « 241 » n'etait pas un nombre de CREATIONS. Ici chaque case est nommee.
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402

RAPPORT = RACINE / "notice" / "CLASSEUR_CE_QUI_MANQUE_2026-11-17.csv"
LOT_API = 60
MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
        "decembre": 12}
#: la colonne du Sheet -> le `kind` de notre registre
TYPES = [("Offre Achat", "offre"), ("Compromis", "compromis"),
         ("Vente Réglée", "vente")]


def sans_accent(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def date_du_classeur(v: str):
    """Les DEUX formats -- la lecon du 14/11 (« 5 decembre23 » rendait None)."""
    t = (v or "").strip()
    if not t:
        return None
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", t)
    if m:
        j, mo, a = (int(x) for x in m.groups())
        a = a + 2000 if a < 100 else a
        try:
            return date(a, mo, j)
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{1,2})\s*([a-z]+)\s*(\d{2,4})", sans_accent(t))
    if m:
        mo = MOIS.get(m.group(2))
        a = int(m.group(3))
        a = a + 2000 if a < 100 else a
        if mo:
            try:
                return date(a, mo, int(m.group(1)))
            except ValueError:
                return None
    return None


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def tout_lire(cl, table, select, ordre):
    out, pas, dep = [], 1000, 0
    while True:
        lot = cl.get(table, {"select": select, "order": ordre,
                             "limit": pas, "offset": dep}) or []
        out.extend(lot)
        if len(lot) < pas:
            return out
        dep += pas


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== QUE MANQUE-T-IL ENCORE ? LES TROIS TYPES (lecture seule) ===")
    print()
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(lignes))
        return 2
    i_id = entetes.index("ID Unique")
    i_etat = entetes.index("Etat Actuel")
    idx = {col: entetes.index(col) for col, _k in TYPES}

    def case(l, i):
        return str(l[i] if i < len(l) else "").strip()

    #: ce que le classeur AFFIRME, par type
    affirme = defaultdict(dict)        # kind -> {id_unique: date}
    illisibles = Counter()
    for _r, l in lignes:
        ident = case(l, i_id)
        if not ident:
            continue
        for col, kind in TYPES:
            brut = case(l, idx[col])
            if not brut:
                continue
            d = date_du_classeur(brut)
            if d is None:
                illisibles[kind] += 1
                continue
            affirme[kind][ident] = d
    print("CE QUE LE CLASSEUR AFFIRME :")
    for _col, kind in TYPES:
        print("   %-10s %5d lignes datees  (illisibles ecartees : %d)"
              % (kind, len(affirme[kind]), illisibles[kind]))
    #: ⛔ TEMOIN : une lecture trop maigre veut dire que les formats sont rates
    if len(affirme["vente"]) < 3000 or len(affirme["offre"]) < 3000:
        print("⛔ LECTURE SUSPECTE -- trop peu de dates lues.")
        return 2
    print()

    # ─── CE QUE NOUS AVONS ───────────────────────────────────────────────────
    cl = client()
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id",
                      "ligne_classeur")
    par_id = defaultdict(list)
    for r in liens:
        par_id[str(r["id_unique"]).strip()].append(r["app_affaire_id"])

    tous = sorted({a for ids in affirme.values() for i in ids
                   for a in par_id.get(i, [])})
    rows = []
    for i in range(0, len(tous), LOT_API):
        lot = tous[i:i + LOT_API]
        rows.extend(cl.get("app_affaire_ledger",
                           {"select": "app_affaire_id,kind,state,date,"
                                      "hektor_annonce_id,app_chaine_id",
                            "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or [])
    ledger = {str(r["app_affaire_id"]): r for r in rows}
    print("transactions reliees lues : %d" % len(ledger))
    print()

    manquantes = []
    print("=== LE VERDICT, TYPE PAR TYPE ===")
    for _col, kind in TYPES:
        tri = Counter()
        for ident, d in affirme[kind].items():
            cibles = par_id.get(ident, [])
            trs = [ledger[str(a)] for a in cibles if str(a) in ledger]
            if not trs:
                tri["aucune transaction reliee (le re-gel les verra)"] += 1
                manquantes.append({"type": kind, "id_unique": ident,
                                   "date_classeur": d.isoformat(),
                                   "cause": "aucun lien", "annonce": "",
                                   "chaine": ""})
                continue
            if any(t.get("kind") == kind for t in trs):
                tri["✅ NOUS L AVONS"] += 1
                continue
            tri["⛔ MANQUE chez nous"] += 1
            t = trs[0]
            manquantes.append({"type": kind, "id_unique": ident,
                               "date_classeur": d.isoformat(),
                               "cause": "la chaine existe, la transaction NON",
                               "annonce": t.get("hektor_annonce_id") or "",
                               "chaine": t.get("app_chaine_id") or ""})
        tot = sum(tri.values())
        print("   %s -- %d lignes datees au classeur" % (kind.upper(), tot))
        for k, n in tri.most_common():
            print("      %-50s %5d  %5.1f %%" % (k[:50], n, 100.0 * n / tot))
        print()

    print("=== ⭐ CE QUI MANQUE VRAIMENT, EN UN CHIFFRE ===")
    par_cause = Counter((m["type"], m["cause"]) for m in manquantes)
    for (kind, cause), n in sorted(par_cause.items()):
        print("   %-10s %-44s %4d" % (kind, cause[:44], n))
    print("   %-10s %-44s %4d" % ("", "-- TOTAL", len(manquantes)))
    print()
    vrai = sum(n for (k, c), n in par_cause.items() if c != "aucun lien")
    sans = len(manquantes) - vrai
    print("   ⛔ transactions a CREER (la chaine existe deja)      %4d" % vrai)
    print("   ⚠  lignes sans aucun lien (le re-gel D1 les verra)   %4d" % sans)
    print()
    if manquantes:
        with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, delimiter=";", fieldnames=list(manquantes[0]))
            w.writeheader()
            w.writerows(sorted(manquantes, key=lambda m: (m["type"], m["date_classeur"])))
        print("ecrit : %s" % RAPPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
