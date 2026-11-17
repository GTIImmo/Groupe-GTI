#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C4 -- LE TEXTE DE F DES LIGNES « EN COURS » EST-IL VRAIMENT POSE ? 17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c4_le_texte_de_f_est_il_vraiment_pose_2026-11-17.py

⛔ LECTURE SEULE.

⛔⛔ POURQUOI CE SCRIPT EXISTE : J'AI ANNONCE UN TROU DE 47 TEXTES, ET MON CRITERE
   ETAIT FAUX DEUX FOIS.

  ① `entetes.index("G")` -- « G » est la LETTRE d'une colonne (la 7e, entete
     « COMMENTAIRES »), pas un nom d'entete. La recherche echouait, donc
     « 0 ligne sauvee par sa colonne G » : UN ZERO PAR CONSTRUCTION. Corrige par
     index_de("G") = 6, et un TEMOIN exige desormais ~4 132 lignes remplies.

  ② Et meme corrige, le critere « a-t-elle un G ? » NE REPOND PAS A LA QUESTION.
     Une ligne avec un G a bien une note -- mais cette note porte LE COMMENTAIRE
     DE G, pas LE TEXTE DE F. Ce sont deux textes differents.

⭐⭐⭐ LE SEUL CRITERE HONNETE : LE TEXTE DE F DE CETTE LIGNE EST-IL, MOT POUR MOT,
   DANS LA NOTE DE SA TRANSACTION ? On va donc LIRE les notes et CHERCHER le texte
   dedans. C'est ce que j'aurais du faire des le debut.
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import Counter
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

DETAIL = RACINE / "notice" / "C4_LES_CLAUSES_DE_LA_COLONNE_F_2026-11-16.csv"
RAPPORT = RACINE / "notice" / "C4_TEXTE_DE_F_NON_POSE_2026-11-17.csv"
LOT_API = 60


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    import os
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


def normaliser(t: str) -> str:
    """Pour comparer deux textes sans se faire piéger par les accents ni l'espace."""
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", t).strip()


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== LE TEXTE DE F DES LIGNES « EN COURS » EST-IL POSE ? (lecture seule) ===")
    print()

    with DETAIL.open(encoding="utf-8-sig", newline="") as f:
        toutes = list(csv.DictReader(f, delimiter=";"))
    if len(toutes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(toutes))
        return 2
    cours = [x for x in toutes
             if x["famille"] == "CLAUSE ou MOTIF"
             and (x["etat_actuel"] or "").strip() not in ("Annulée", "Vente réglée")]
    print("lignes « en cours » : %d" % len(cours))
    if not (70 <= len(cours) <= 110):
        print("⛔ LE COMPTE A BOUGE.")
        return 2

    cl = client()
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id",
                      "ligne_classeur")
    par_id: dict[str, list[int]] = {}
    for r in liens:
        par_id.setdefault(str(r["id_unique"]).strip(), []).append(r["app_affaire_id"])

    besoin = sorted({a for x in cours for a in par_id.get(x["id_unique"], [])})
    #: ⭐ ON LIT LE TEXTE DES NOTES, pas seulement leur existence
    notes: dict[int, dict] = {}
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        for r in (cl.get("app_affaire_note",
                         {"select": "app_affaire_id,texte,origine",
                          "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or []):
            notes[int(r["app_affaire_id"])] = r
    print("transactions reliees %d . portant une note %d" % (len(besoin), len(notes)))
    #: ⛔ TEMOIN : si on ne lit AUCUN texte, la mesure ne vaut rien
    avec_texte = sum(1 for r in notes.values() if str(r.get("texte") or "").strip())
    print("TEMOIN : notes dont le TEXTE est lu : %d (doit valoir %d)"
          % (avec_texte, len(notes)))
    if notes and avec_texte != len(notes):
        print("⛔ DES NOTES SANS TEXTE : la lecture est suspecte.")
        return 2
    print()

    pose, absent, sans_note, sans_lien = [], [], [], []
    for x in cours:
        ident, t = x["id_unique"], (x["texte_seul"] or "").strip()
        cibles = par_id.get(ident, [])
        if not cibles:
            sans_lien.append(x)
            continue
        textes = [str(notes[a]["texte"]) for a in cibles if a in notes]
        if not textes:
            sans_note.append(x)
            continue
        n = normaliser(t)
        if n and any(n in normaliser(u) for u in textes):
            pose.append(x)
        else:
            absent.append(x)

    print("=== LE VERDICT, TEXTE PAR TEXTE ===")
    print("   ✅ le texte de F EST dans la note        %4d" % len(pose))
    print("   ⛔ le texte de F N'Y EST PAS             %4d" % len(absent))
    print("   ⚠  aucune note sur toute la chaine       %4d" % len(sans_note))
    print("   ⚠  aucune transaction reliee             %4d" % len(sans_lien))
    print("   ---------------------------------------------")
    print("   total                                    %4d" % len(cours))
    assert len(pose) + len(absent) + len(sans_note) + len(sans_lien) == len(cours)
    print()
    #: ⛔⛔ LE TEMOIN POSITIF : la methode sait-elle RECONNAITRE un texte pose ?
    #:   Si « pose » valait 0, c'est la comparaison qui serait cassee. On la
    #:   verifie donc sur une famille dont on SAIT que F est posee : les annulees.
    ann = [x for x in toutes
           if x["famille"] == "CLAUSE ou MOTIF"
           and (x["etat_actuel"] or "").strip() == "Annulée"][:60]
    besoin2 = sorted({a for x in ann for a in par_id.get(x["id_unique"], [])})
    notes2 = {}
    for i in range(0, len(besoin2), LOT_API):
        lot = besoin2[i:i + LOT_API]
        for r in (cl.get("app_affaire_note",
                         {"select": "app_affaire_id,texte",
                          "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or []):
            notes2[int(r["app_affaire_id"])] = r
    vus = 0
    for x in ann:
        n = normaliser(x["texte_seul"])
        textes = [str(notes2[a]["texte"]) for a in par_id.get(x["id_unique"], [])
                  if a in notes2]
        if n and any(n in normaliser(u) for u in textes):
            vus += 1
    print("=== ⛔⛔ LE TEMOIN POSITIF DE LA METHODE ===")
    print("   sur %d lignes ANNULEES (dont F EST posee par le 2e patch) :" % len(ann))
    print("   la comparaison en retrouve %d" % vus)
    if vus == 0:
        print("⛔ LA COMPARAISON NE RECONNAIT RIEN : elle est cassee, pas la base.")
        return 2
    print("   ✅ la methode sait dire OUI -- donc les absences ci-dessus sont VRAIES")
    print()

    if absent:
        with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["id_unique", "etat_classeur", "texte_de_F",
                        "app_affaire_id_candidats", "la_note_actuelle"])
            for x in absent:
                cibles = par_id.get(x["id_unique"], [])
                note = next((str(notes[a]["texte"])[:200] for a in cibles
                             if a in notes), "")
                w.writerow([x["id_unique"], x["etat_actuel"], x["texte_seul"],
                            " ".join(map(str, cibles)), note])
        print("ecrit : %s" % RAPPORT)
        print()
        print("   un echantillon de ce qui MANQUE :")
        for x in absent[:12]:
            print("      %-10s %s" % (x["id_unique"], x["texte_seul"][:66]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
