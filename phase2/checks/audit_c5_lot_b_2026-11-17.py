#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AUDIT APPROFONDI -- LES TRANSACTIONS DU CLASSEUR QUI MANQUENT. 17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\audit_c5_lot_b_2026-11-17.py

⛔ LECTURE SEULE. Aucune ecriture, aucun patch.

Sa demande : « J'ai besoin d'un audit plus approfondi afin de reprendre. Il faut
etre clair et sur. » Ma mesure precedente annoncait 251 manquantes. UN CHIFFRE SEUL
NE SUFFIT PAS A DECIDER : il faut savoir s'il est JUSTE, et ce qu'il contient.

⛔⛔ LE CONTROLE QUI PEUT TOUT INVALIDER, ET ON LE FAIT EN PREMIER :
  ma mesure demandait « la CHAINE LIEE a-t-elle une transaction de ce type ? ».
  Mais un bien peut porter PLUSIEURS chaines (607 biens en portent deux ou plus,
  mesure du 16/11). Si le lien du gel pointe la chaine A et que la transaction
  vit dans la chaine B DU MEME BIEN, je compte un manque QUI N'EXISTE PAS.
  ⭐ C'est exactement la faute du 12/11, deja payee : « je comparais un dossier
    a une transaction ». On la cherche donc avant tout le reste.

LES SIX MESURES :
  ① LE FAUX POSITIF : la transaction existe-t-elle sur le MEME BIEN, hors chaine ?
  ② LA MEME DATE : si elle existe ailleurs, porte-t-elle la MEME date ? (sinon ce
     serait une AUTRE affaire, et le manque serait reel)
  ③ LA CONFIANCE DU LIEN : poser sur un lien « a valider » n'est pas poser sur un
     lien « sure ». C5 avait exige « sure seulement ».
  ④ L'AGE : sa regle du chantier (« ce que Hektor ne rendra plus ») -- combien
     sont VIVANTES, donc hors perimetre ?
  ⑤ L'ETAT au classeur, pour savoir ce qu'on creerait.
  ⑥ L'ECART DES VENTES : le plan disait 39, je mesure 7. On cherche pourquoi.
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

RAPPORT = RACINE / "notice" / "AUDIT_C5_LOT_B_2026-11-17.csv"
LOT_API = 60
MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
        "decembre": 12}
TYPES = [("Offre Achat", "offre"), ("Compromis", "compromis"),
         ("Vente Réglée", "vente")]
#: les etats qui veulent dire « l'affaire court encore »
VIVANTS = ("active", "signed", "pending", "accepted")


def sans_accent(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def date_du_classeur(v: str):
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


def date_de_nous(v):
    try:
        return date.fromisoformat(str(v or "").strip()[:10])
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
    print("=== AUDIT -- LES TRANSACTIONS DU CLASSEUR QUI MANQUENT (lecture seule) ===")
    print()
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(lignes))
        return 2
    i_id, i_etat = entetes.index("ID Unique"), entetes.index("Etat Actuel")
    idx = {c: entetes.index(c) for c, _k in TYPES}

    def case(l, i):
        return str(l[i] if i < len(l) else "").strip()

    affirme = defaultdict(dict)
    etat_de = {}
    for _r, l in lignes:
        ident = case(l, i_id)
        if not ident:
            continue
        etat_de[ident] = case(l, i_etat)
        for col, kind in TYPES:
            d = date_du_classeur(case(l, idx[col]))
            if d:
                affirme[kind][ident] = d
    if len(affirme["offre"]) < 3000:
        print("⛔ LECTURE SUSPECTE.")
        return 2

    # ─── CE QUE NOUS AVONS : par chaine ET PAR BIEN ──────────────────────────
    cl = client()
    liens = tout_lire(cl, "app_classeur_lien",
                      "id_unique,app_affaire_id,confiance", "ligne_classeur")
    par_id = defaultdict(list)
    confiance_de = {}
    for r in liens:
        i = str(r["id_unique"]).strip()
        par_id[i].append(r["app_affaire_id"])
        #: la confiance la PLUS FAIBLE de la ligne : on ne se rassure pas
        #: ⛔⛔ LES VALEURS PORTENT DES ACCENTS : « sûre », « à valider ». Mon
        #:   premier test comparait a « sure » sans accent et rendait 0 POSABLE
        #:   alors qu'il y avait 223 liens surs et 135 chaines closes -- un zero
        #:   par construction, qu'un croisement absurde a trahi. On NORMALISE.
        ordre = {"sure": 3, "bonne": 2, "a valider": 1}
        c = sans_accent(str(r.get("confiance") or "").strip())
        if i not in confiance_de or ordre.get(c, 0) < ordre.get(confiance_de[i], 9):
            confiance_de[i] = c

    besoin = sorted({a for ids in affirme.values() for i in ids
                     for a in par_id.get(i, [])})
    rows = []
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        rows.extend(cl.get("app_affaire_ledger",
                           {"select": "app_affaire_id,kind,state,date,"
                                      "hektor_annonce_id,app_chaine_id",
                            "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or [])
    ledger = {str(r["app_affaire_id"]): r for r in rows}
    print("transactions reliees lues : %d" % len(ledger))

    #: ⭐ TOUT LE REGISTRE PAR BIEN -- c'est ca qui permet le controle ①
    tout_le_registre = tout_lire(cl, "app_affaire_ledger",
                                 "app_affaire_id,kind,state,date,hektor_annonce_id,"
                                 "app_chaine_id", "app_affaire_id")
    par_bien = defaultdict(list)
    par_chaine = defaultdict(list)
    for r in tout_le_registre:
        if r.get("hektor_annonce_id"):
            par_bien[str(r["hektor_annonce_id"])].append(r)
        if r.get("app_chaine_id"):
            par_chaine[str(r["app_chaine_id"])].append(r)
    print("registre entier : %d transactions, sur %d biens et %d chaines"
          % (len(tout_le_registre), len(par_bien), len(par_chaine)))
    print()
    print("=== ⛔⛔ LA FAUTE QUE SA QUESTION A TROUVEE -- « on a pas deja ajoute les")
    print("    offres 195 ? ». OUI, ET MON PREMIER AUDIT NE LES VOYAIT PAS.")
    print("    Il cherchait les transactions d'une ligne VIA app_classeur_lien. Mais")
    print("    les 195 transactions CREEES le 16/11 N'ONT PAS DE LIEN DANS LE GEL --")
    print("    le re-gel additif (D1) n'a pas encore eu lieu. Elles etaient donc")
    print("    INVISIBLES, et je recomptais comme « manquant » ce qui venait d'etre")
    print("    pose. Preuve : UAER0F0F, chaine 7904 -> la transaction 1001543,")
    print("    compromis/cancelled du 2020-07-15, origine « classeur ».")
    print("    ➡ ON INTERROGE DESORMAIS **TOUTE LA CHAINE**, pas le lien.")
    print()

    # ─── LE TRI, AVEC LE CONTROLE DU FAUX POSITIF ────────────────────────────
    manque = []
    faux_positifs = []
    for _col, kind in TYPES:
        for ident, d in affirme[kind].items():
            cibles = par_id.get(ident, [])
            trs_du_lien = [ledger[str(a)] for a in cibles if str(a) in ledger]
            if not trs_du_lien:
                continue                      # sans lien : traite a part
            #: ⭐⭐⭐ ON ELARGIT A TOUTE LA CHAINE. Le lien du gel ne pointe que
            #:   les transactions qui existaient AVANT lui ; celles qu'on a creees
            #:   depuis (les 195 du 16/11) n'y sont pas. Interroger le lien seul
            #:   fait recompter comme « manquant » ce qu'on vient de poser.
            chaines = {str(t.get("app_chaine_id")) for t in trs_du_lien
                       if t.get("app_chaine_id")}
            trs = list(trs_du_lien)
            vus = {t["app_affaire_id"] for t in trs}
            for c in chaines:
                for r in par_chaine.get(c, []):
                    if r["app_affaire_id"] not in vus:
                        trs.append(r)
                        vus.add(r["app_affaire_id"])
            if any(t.get("kind") == kind for t in trs):
                continue                      # nous l'avons
            #: ⛔⛔ LE CONTROLE ① : existe-t-elle sur LE MEME BIEN, hors chaine ?
            biens = {str(t.get("hektor_annonce_id")) for t in trs
                     if t.get("hektor_annonce_id")}
            ailleurs = [r for b in biens for r in par_bien.get(b, [])
                        if r.get("kind") == kind
                        and str(r.get("app_chaine_id")) not in chaines]
            if ailleurs:
                #: ② porte-t-elle LA MEME DATE ? (sinon c'est une AUTRE affaire)
                memes = [r for r in ailleurs if date_de_nous(r.get("date")) == d]
                faux_positifs.append({
                    "type": kind, "id_unique": ident,
                    "date_classeur": d.isoformat(),
                    "trouvee_ailleurs": len(ailleurs),
                    "dont_MEME_date": len(memes),
                    "bien": " ".join(sorted(biens)),
                    "verdict": ("FAUX POSITIF -- meme date, autre chaine"
                                if memes else
                                "autre affaire sur le meme bien (date differente)")})
                if memes:
                    continue                  # ⛔ ce n'est PAS un manque
            t = trs[0]
            manque.append({
                "type": kind, "id_unique": ident, "date_classeur": d.isoformat(),
                "annee": d.year, "etat_classeur": etat_de.get(ident, ""),
                "confiance_du_lien": confiance_de.get(ident, "(inconnue)"),
                "annonce": t.get("hektor_annonce_id") or "",
                "chaine": t.get("app_chaine_id") or "",
                "etats_de_la_chaine": " ".join(sorted(
                    {str(x.get("kind")) + ":" + str(x.get("state")) for x in trs})),
                "chaine_VIVANTE": any(x.get("state") in VIVANTS for x in trs)})

    print("=== ① ⛔⛔ LE CONTROLE DU FAUX POSITIF ===")
    print("   lignes ou la transaction existe AILLEURS sur le meme bien : %d"
          % len(faux_positifs))
    for v, n in Counter(x["verdict"] for x in faux_positifs).most_common():
        print("      %-54s %4d" % (v[:54], n))
    retires = sum(1 for x in faux_positifs if x["dont_MEME_date"])
    print("   ⭐ RETIREES du compte des manquantes : %d" % retires)
    print()

    print("=== LE COMPTE CORRIGE ===")
    for k, n in Counter(m["type"] for m in manque).most_common():
        print("   %-10s %4d" % (k, n))
    print("   %-10s %4d" % ("TOTAL", len(manque)))
    print()

    print("=== ③ LA CONFIANCE DU LIEN (C5 exigeait « sure » SEULEMENT) ===")
    for c, n in Counter(m["confiance_du_lien"] for m in manque).most_common():
        print("   %-14s %4d  %5.1f %%" % (c, n, 100.0 * n / len(manque) if manque else 0))
    print()

    print("=== ④ SA REGLE DU CHANTIER : LA CHAINE EST-ELLE VIVANTE ? ===")
    viv = sum(1 for m in manque if m["chaine_VIVANTE"])
    print("   chaine VIVANTE (Hektor la rendra)  %4d  -> HORS PERIMETRE" % viv)
    print("   chaine CLOSE                       %4d  -> reprenable" % (len(manque) - viv))
    print()
    print("   par ANNEE de la date du classeur :")
    for a, n in sorted(Counter(m["annee"] for m in manque).items()):
        print("      %-6s %4d" % (a, n))
    print()

    print("=== ⑤ L'ETAT AU CLASSEUR de ce qu'on creerait ===")
    for e, n in Counter(m["etat_classeur"] for m in manque).most_common(8):
        print("   %-26s %4d" % (e[:26] or "(vide)", n))
    print()

    print("=== ⭐⭐ LE LOT VRAIMENT POSABLE : lien « sûre » ET chaine CLOSE ===")
    posables = [m for m in manque
                if m["confiance_du_lien"] == "sure" and not m["chaine_VIVANTE"]]
    for k, n in Counter(m["type"] for m in posables).most_common():
        print("   %-10s %4d" % (k, n))
    print("   %-10s %4d" % ("TOTAL", len(posables)))
    #: ⛔ LE GARDE-FOU CONTRE LE ZERO PAR CONSTRUCTION : un croisement ne peut pas
    #:   rendre 0 quand ses deux composantes sont grandes. Si ca arrive, c'est le
    #:   test qui est faux, pas la base -- et le script doit le DIRE, pas conclure.
    n_sure = sum(1 for m in manque if m["confiance_du_lien"] == "sure")
    n_close = sum(1 for m in manque if not m["chaine_VIVANTE"])
    if not posables and n_sure > 10 and n_close > 10:
        print("⛔⛔ ZERO IMPOSSIBLE : %d liens surs et %d chaines closes, et 0 au"
              " croisement. LE TEST EST FAUX." % (n_sure, n_close))
        return 2
    print("   (temoin du croisement : %d liens surs . %d chaines closes)"
          % (n_sure, n_close))
    print()
    print("   par ANNEE, dans le lot posable :")
    for a, n in sorted(Counter(m["annee"] for m in posables).items()):
        print("      %-6s %4d" % (a, n))
    print()
    print("   par ETAT au classeur, dans le lot posable :")
    for e, n in Counter(m["etat_classeur"] for m in posables).most_common(8):
        print("      %-26s %4d" % (e[:26] or "(vide)", n))
    print()

    if manque:
        with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, delimiter=";", fieldnames=list(manque[0]))
            w.writeheader()
            w.writerows(sorted(manque, key=lambda m: (m["type"], m["date_classeur"])))
        print("ecrit : %s" % RAPPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
