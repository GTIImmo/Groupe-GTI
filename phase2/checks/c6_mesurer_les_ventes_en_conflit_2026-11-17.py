#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C6 -- LES VENTES DU CLASSEUR QUI ENTRENT EN CONFLIT AVEC NOUS.  17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c6_mesurer_les_ventes_en_conflit_2026-11-17.py

⛔ LECTURE SEULE. Aucune ecriture, aucun patch genere.

⭐⭐⭐ POURQUOI ON REFAIT LA MESURE DEPUIS ZERO. Le plan dit lui-meme, pour les
  « 26 » : « ⏰ LA REGLE EXACTE DES 26 RESTE A RETROUVER : je ne sais pas la
  reconstituer sur le rapport du jour, et je ne la devine pas. »
  ➡ On ne cherche donc PAS a retomber sur 26. On pose une definition CLAIRE, on
    mesure, et on DIT le chiffre obtenu. Un chiffre qu'on ne sait pas reproduire
    n'est pas une mesure, c'est un souvenir.

LA DEFINITION, en trois conditions :
   ① le classeur dit qu'une VENTE a eu lieu (colonne « Vente Réglée » datee)
   ② chez nous, la chaine de cette ligne N'A PAS de transaction `vente`
   ③ MAIS son compromis porte DEJA une `date_acte`
  -> alors poser la vente du classeur entrerait en CONFLIT avec une date que
     NOUS avons deja. C'est ca que Frederic doit trancher.

⚠ ET ON SEPARE LE VRAI CONFLIT DU FAUX : si notre `date_acte` est EGALE a la date
  du classeur, il n'y a aucun conflit -- juste une vente a creer. On compte donc
  les deux a part, et on donne l'ECART en jours.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter
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

RAPPORT = RACINE / "notice" / "C6_LES_VENTES_EN_CONFLIT_2026-11-17.csv"
LOT_API = 60
MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
        "decembre": 12}


def index_de(lettre: str) -> int:
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def sans_accent(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def date_du_classeur(v: str):
    """Les DEUX formats du classeur -- la lecon du 14/11 (« 5 decembre23 »).

    ⛔ Une lecture qui ne gere qu'un format perd UNE LIGNE SUR CINQ, en silence.
    """
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
    t2 = sans_accent(t)
    m = re.fullmatch(r"(\d{1,2})\s*([a-z]+)\s*(\d{2,4})", t2)
    if m:
        j, nom, a = int(m.group(1)), m.group(2), int(m.group(3))
        mo = MOIS.get(nom)
        a = a + 2000 if a < 100 else a
        if mo:
            try:
                return date(a, mo, j)
            except ValueError:
                return None
    return None


def date_de_nous(v):
    t = str(v or "").strip()[:10]
    try:
        return date.fromisoformat(t)
    except ValueError:
        return None


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- rien n'est mesure.")
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
    print("=== C6 -- LES VENTES DU CLASSEUR EN CONFLIT AVEC NOUS (lecture seule) ===")
    print()
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    i_id = entetes.index("ID Unique")
    i_vr = entetes.index("Vente Réglée")
    i_etat = entetes.index("Etat Actuel")
    print("le classeur : %d lignes . « Vente Réglée » = colonne %d"
          % (len(lignes), i_vr + 1))

    def case(l, i):
        return str(l[i] if i < len(l) else "").strip()

    #: ① LES LIGNES OU LE CLASSEUR DIT QU'UNE VENTE A EU LIEU
    ventes_sheet = {}
    illisibles = 0
    for _r, l in lignes:
        ident, brut = case(l, i_id), case(l, i_vr)
        if not (ident and brut):
            continue
        d = date_du_classeur(brut)
        if d is None:
            illisibles += 1
            continue
        ventes_sheet[ident] = {"date": d, "brut": brut, "etat": case(l, i_etat)}
    print("   lignes avec une DATE DE VENTE lisible : %d" % len(ventes_sheet))
    print("   ⚠ dates illisibles (ecartees, comptees) : %d" % illisibles)
    #: ⛔ TEMOIN : si on lit trop peu, la lecture des deux formats est cassee
    if len(ventes_sheet) < 3000:
        print("⛔ TROP PEU DE DATES LUES -- la lecture des deux formats est suspecte.")
        return 2
    print()

    # ─── CE QUE NOUS AVONS, PAR CHAINE ───────────────────────────────────────
    cl = client()
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id",
                      "ligne_classeur")
    par_id = {}
    for r in liens:
        par_id.setdefault(str(r["id_unique"]).strip(), []).append(r["app_affaire_id"])

    besoin = sorted({a for i in ventes_sheet for a in par_id.get(i, [])})
    print("transactions a lire : %d" % len(besoin))
    rows = []
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        rows.extend(cl.get("app_affaire_ledger",
                           {"select": "app_affaire_id,kind,state,date,date_acte,"
                                      "hektor_annonce_id,app_chaine_id",
                            "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or [])
    ledger = {str(r["app_affaire_id"]): r for r in rows}
    print("transactions lues : %d" % len(ledger))
    print()

    #: ② et ③ LE TRI
    tri = Counter()
    conflits = []
    for ident, v in ventes_sheet.items():
        cibles = par_id.get(ident, [])
        trs = [ledger[str(a)] for a in cibles if str(a) in ledger]
        if not trs:
            tri["aucune transaction reliee"] += 1
            continue
        if any(t.get("kind") == "vente" for t in trs):
            tri["la vente EXISTE deja chez nous -- rien a faire"] += 1
            continue
        comp = [t for t in trs if t.get("kind") == "compromis"]
        if not comp:
            tri["pas de vente ET pas de compromis -- a CREER, sans conflit"] += 1
            continue
        avec_acte = [t for t in comp if date_de_nous(t.get("date_acte"))]
        if not avec_acte:
            tri["un compromis SANS date d acte -- a CREER, sans conflit"] += 1
            continue
        t = avec_acte[0]
        notre = date_de_nous(t.get("date_acte"))
        ecart = (v["date"] - notre).days
        if ecart == 0:
            tri["notre date d acte est LA MEME -- aucun conflit"] += 1
            continue
        tri["⛔ CONFLIT : notre date d acte DIFFERE"] += 1
        conflits.append({"id_unique": ident, "etat_classeur": v["etat"],
                         "date_du_classeur": v["date"].isoformat(),
                         "brut_du_classeur": v["brut"],
                         "app_affaire_id": t["app_affaire_id"],
                         "annonce": t.get("hektor_annonce_id"),
                         "etat_du_compromis": t.get("state"),
                         "notre_date_acte": notre.isoformat(),
                         "notre_date_compromis": str(t.get("date") or "")[:10],
                         "ecart_jours": ecart})

    print("=== LE TRI ===")
    for k, n in tri.most_common():
        print("   %-58s %5d" % (k[:58], n))
    print("   %-58s %5d" % ("-- total", sum(tri.values())))
    assert sum(tri.values()) == len(ventes_sheet)
    print()

    if not conflits:
        print("⭐ AUCUN CONFLIT -- il n'y a rien a trancher.")
        return 0

    print("=== ⛔ LES %d CONFLITS, EN DETAIL ===" % len(conflits))
    ecarts = sorted(abs(c["ecart_jours"]) for c in conflits)
    print("   l'ecart en jours : de %d a %d, median %d"
          % (ecarts[0], ecarts[-1], ecarts[len(ecarts) // 2]))
    print("   le classeur est APRES nous : %d . AVANT nous : %d"
          % (sum(1 for c in conflits if c["ecart_jours"] > 0),
             sum(1 for c in conflits if c["ecart_jours"] < 0)))
    print()
    print("   par TRANCHE d'ecart :")
    for libelle, test in (("le MEME MOIS (<= 31 j)", lambda e: e <= 31),
                          ("1 a 3 mois", lambda e: 31 < e <= 92),
                          ("3 mois a 1 an", lambda e: 92 < e <= 365),
                          ("PLUS D UN AN", lambda e: e > 365)):
        n = sum(1 for c in conflits if test(abs(c["ecart_jours"])))
        print("      %-28s %4d" % (libelle, n))
    print()
    print("   l'etat de NOTRE compromis :")
    for s, n in Counter(c["etat_du_compromis"] for c in conflits).most_common():
        print("      %-18s %4d" % (str(s), n))
    print()
    print("   les 15 premiers :")
    for c in sorted(conflits, key=lambda c: abs(c["ecart_jours"]), reverse=True)[:15]:
        print("      %-10s annonce %-7s classeur %s . nous %s . ecart %+5d j . %s"
              % (c["id_unique"], str(c["annonce"]), c["date_du_classeur"],
                 c["notre_date_acte"], c["ecart_jours"], c["etat_du_compromis"]))
    with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=list(conflits[0]))
        w.writeheader()
        w.writerows(sorted(conflits, key=lambda c: abs(c["ecart_jours"]), reverse=True))
    print()
    print("ecrit : %s" % RAPPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
