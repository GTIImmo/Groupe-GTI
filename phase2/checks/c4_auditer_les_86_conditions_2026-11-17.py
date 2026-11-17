#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C4 (3e patch) -- AUDIT DES 86 CONDITIONS EN ATTENTE.             17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c4_auditer_les_86_conditions_2026-11-17.py

⛔ CE SCRIPT N'ECRIT RIEN, NI EN BASE NI DE PATCH. Il AUDITE, parce que ce 3e patch
   se heurte a SA REGLE DU CHANTIER, et qu'il faut la mesurer avant de proposer :

     « on ne reprend que ce que Hektor ne rendra plus : le bien est SORTI du parc
       vivant, OU la date a plus d'un an. Et JAMAIS une date dans le futur. »

⛔⛔ LES DEUX OBSTACLES QUE CET AUDIT DOIT CHIFFRER, ET QUI PEUVENT TOUT ARRETER :

  ① UNE AFFAIRE « EN COURS » EST, PAR DEFINITION, CE QUE HEKTOR REND ENCORE.
     Donc sa regle l'EXCLUT -- sauf si le classeur est PERIME et que l'affaire est
     retombee ou s'est reglee depuis. C'est la premiere mesure : ou en sont ces
     86 affaires CHEZ NOUS, aujourd'hui ?

  ② LES DATES DE F N'ONT PAS D'ANNEE. « ODP15/12 », « DB30/1 » -- 15 decembre de
     QUELLE annee ? Un repli sur l'annee courante FABRIQUERAIT une date (la lecon
     « un repli sur l'heure de lecture fabrique une date qui glisse »). La seule
     ancre honnete est la date du compromis CHEZ NOUS : l'echeance vient APRES la
     signature, donc on choisit l'annee qui met la date apres elle, et on DIT
     combien de lignes restent indatables.
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
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

DETAIL = RACINE / "notice" / "C4_LES_CLAUSES_DE_LA_COLONNE_F_2026-11-16.csv"
RAPPORT = RACINE / "notice" / "C4_LES_86_CONDITIONS_AUDIT_2026-11-17.csv"
LOT_API = 60

#: ⭐ LES ABREVIATIONS QUI PORTENT UNE DATE, et ce qu'elles deviennent.
#:   ⛔ ADP et ODP ne sont PAS deux clauses : DEPART et ECHEANCE de « Obtention
#:     Credit » (catalogue id 2) -- mesure du 17/11, 24 fois sur 24.
#:   ⛔ DB va en NOTE par sa decision du 17/11 (elle vaut « Vente Prevue » 60 fois
#:     sur 65 : nous l'avons deja).
#:   ⬜ DPC et OPC : le sens n'est PAS confirme par lui -> AUCUNE condition posee,
#:     elles sont COMPTEES et NOMMEES pour qu'il tranche.
DATEES = ("ADP", "ODP", "DPC", "OPC", "DB")
MOIS_MAX = 12


def cle(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9/ ]+", " ", t)).strip()


def client():
    #: ⭐ LES TROIS .env, comme le generateur du 1er patch -- la cle de service
    #:   n'est pas dans celui de la racine.
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle_api = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle_api):
        raise SystemExit("⛔ pas d'identifiants Supabase -- rien n'est mesure.")
    return cgh.SupabaseClient(url, cle_api, timeout_seconds=30)


def tout_lire(cl, table, select, ordre):
    out, pas, dep = [], 1000, 0
    while True:
        lot = cl.get(table, {"select": select, "order": ordre,
                             "limit": pas, "offset": dep}) or []
        out.extend(lot)
        if len(lot) < pas:
            return out
        dep += pas


def lire_abrevs(texte: str) -> list[tuple[str, str]]:
    """Rend [(abrev, jj/mm), ...] -- les abreviations SUIVIES d'une date."""
    out = []
    for ab in DATEES:
        for m in re.finditer(ab + r"\s*(\d{1,2})\s*/\s*(\d{1,2})", texte, re.I):
            j, mo = int(m.group(1)), int(m.group(2))
            if 1 <= j <= 31 and 1 <= mo <= MOIS_MAX:
                out.append((ab, "%02d/%02d" % (j, mo)))
    return out


def ancrer(jm: str, apres):
    """jj/mm -> une date REELLE, ancree sur `apres` (la signature du compromis).

    ⭐ LA REGLE : une echeance vient APRES la signature. On essaie l'annee de la
      signature, puis la suivante, et on garde la PREMIERE qui tombe apres elle.
    ⛔ SANS ANCRE, ON NE DEVINE PAS : on rend None et on le COMPTE.
    """
    if apres is None:
        return None, "pas d ancre (aucune date de compromis chez nous)"
    j, mo = (int(x) for x in jm.split("/"))
    for an in (apres.year, apres.year + 1):
        try:
            d = date(an, mo, j)
        except ValueError:
            return None, "date impossible (%s)" % jm
        if d >= apres:
            return d, "ancree sur %s" % apres.isoformat()
    return None, "aucune annee ne tombe apres %s" % apres.isoformat()


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== C4 (3e patch) -- AUDIT DES CONDITIONS EN ATTENTE (lecture seule) ===")
    print()

    with DETAIL.open(encoding="utf-8-sig", newline="") as f:
        toutes = list(csv.DictReader(f, delimiter=";"))
    if len(toutes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes au CSV. ON NE CONCLUT RIEN." % len(toutes))
        return 2
    print("le CSV du 16/11 : %d lignes" % len(toutes))

    etats = Counter(x["etat_actuel"] or "(vide)" for x in toutes)
    print("   les etats du classeur, toutes familles :")
    for e, n in etats.most_common(8):
        print("      %-28s %5d" % (e[:28], n))
    print()

    cours = [x for x in toutes
             if x["famille"] == "CLAUSE ou MOTIF"
             and (x["etat_actuel"] or "").strip() not in ("Annulée", "Vente réglée")]
    print("=== ① LES LIGNES « EN COURS » : %d ===" % len(cours))
    print("   (famille CLAUSE ou MOTIF, et l'etat du classeur n'est ni Annulée")
    print("    ni Vente réglée -- le meme critere que la mesure du 16/11)")
    if not (70 <= len(cours) <= 110):
        print("⛔ LE COMPTE A BOUGE (on attendait ~86). On s'arrete.")
        return 2
    print()
    print("   leur etat au classeur :")
    for e, n in Counter(x["etat_actuel"] or "(vide)" for x in cours).most_common():
        print("      %-28s %5d" % (e[:28], n))
    print()

    print("=== ② LE DECODAGE DES ABREVIATIONS DATEES ===")
    trouvees = Counter()
    sans_abrev = []
    for x in cours:
        ab = lire_abrevs(x["texte_seul"])
        x["_abrevs"] = ab
        if not ab:
            sans_abrev.append(x)
        for a, _ in ab:
            trouvees[a.upper()] += 1
    print("   lignes qui portent AU MOINS une abreviation datee : %d sur %d"
          % (len(cours) - len(sans_abrev), len(cours)))
    for a, n in trouvees.most_common():
        print("      %-6s %4d" % (a, n))
    print()
    print("   ⚠ les %d lignes SANS aucune abreviation datee (echantillon) :"
          % len(sans_abrev))
    for x in sans_abrev[:14]:
        print("      %-10s %s" % (x["id_unique"], x["texte_seul"][:66]))
    print()

    # --- OU EN SONT CES AFFAIRES CHEZ NOUS ? ---------------------------------
    cl = client()
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id",
                      "ligne_classeur")
    par_id: dict[str, list[int]] = {}
    for r in liens:
        par_id.setdefault(str(r["id_unique"]).strip(), []).append(r["app_affaire_id"])

    besoin = sorted({a for x in cours for a in par_id.get(x["id_unique"], [])})
    rows = []
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        rows.extend(cl.get("app_affaire_ledger",
                           {"select": "app_affaire_id,kind,state,date,"
                                      "hektor_annonce_id,app_dossier_id,app_chaine_id",
                            "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or [])
    ledger = {str(r["app_affaire_id"]): r for r in rows}
    print("=== ③ LE RACCORDEMENT ===")
    print("   lignes reliees au gel        : %d sur %d"
          % (sum(1 for x in cours if par_id.get(x["id_unique"])), len(cours)))
    print("   transactions lues            : %d" % len(ledger))
    print()

    # ⭐⭐⭐ LA MESURE QUI DECIDE DE TOUT : SA REGLE DU CHANTIER
    print("=== ④ ⭐⭐⭐ SA REGLE : CES AFFAIRES SONT-ELLES ENCORE VIVANTES ? ===")
    print("   « on ne reprend que ce que Hektor ne rendra plus »")
    print()
    etat_ici = Counter()
    pourquoi_pas_net = Counter()
    detail = []
    for x in cours:
        trs = [ledger[str(a)] for a in par_id.get(x["id_unique"], []) if str(a) in ledger]
        comp = [t for t in trs if t.get("kind") == "compromis"]
        cible = comp[0] if len(comp) == 1 else None
        if cible is None:
            #: ⛔ « aucun compromis net » cache DEUX causes tres differentes : la
            #:   chaine n'a pas de compromis du tout (c'est une OFFRE), ou elle en
            #:   a plusieurs. Un compte qui les melange ne sert a rien.
            off = [t for t in trs if t.get("kind") == "offre"]
            if not trs:
                pourquoi_pas_net["aucune transaction reliee"] += 1
            elif not comp:
                pourquoi_pas_net["AUCUN compromis -- %s offre(s) seulement"
                                 % (len(off) or "0")] += 1
            else:
                pourquoi_pas_net["PLUSIEURS compromis (%d)" % len(comp)] += 1
        st = (cible or {}).get("state") or "(aucun compromis net)"
        etat_ici[st] += 1
        # la date du compromis chez nous = l'ancre des echeances
        dref = None
        if cible and cible.get("date"):
            try:
                dref = date.fromisoformat(str(cible["date"])[:10])
            except ValueError:
                dref = None
        for ab, jm in x["_abrevs"]:
            d, pourquoi = ancrer(jm, dref)
            detail.append({"id_unique": x["id_unique"],
                           "etat_classeur": x["etat_actuel"],
                           "F_brut": x["texte_seul"][:90],
                           "abrev": ab.upper(), "date_brute": jm,
                           "app_affaire_id": (cible or {}).get("app_affaire_id") or "",
                           "etat_chez_nous": st,
                           "date_compromis": dref.isoformat() if dref else "",
                           "echeance_ancree": d.isoformat() if d else "",
                           "comment": pourquoi,
                           "dans_le_futur": "OUI" if d and d > date.today() else "non"})
    for s, n in etat_ici.most_common():
        print("      %-28s %4d" % (s[:28], n))
    print()
    print("   ⛔ ET « aucun compromis net » CACHE DEUX CAUSES :")
    for c, n in pourquoi_pas_net.most_common():
        print("      %-44s %4d" % (c[:44], n))
    print()
    #: ⛔⛔ MA PREMIERE VERSION COMPTAIT `signed`/`pending` ET RENDAIT 0 -- un zero
    #:   rassurant et FAUX. L'etat vivant d'un compromis chez nous s'appelle
    #:   `active`. Lecon : « un zero ne se croit pas sans temoin positif ».
    vivants = ("active", "signed", "pending")
    encore = sum(etat_ici.get(s, 0) for s in vivants)
    print("   ⛔ ENCORE VIVANTES CHEZ NOUS (%s) : %d" % ("/".join(vivants), encore))
    print("   ✅ TOMBEES OU REGLEES DEPUIS                     : %d"
          % (etat_ici.get("cancelled", 0) + etat_ici.get("completed", 0)))
    print()

    print("=== ⑤ LES ECHEANCES, UNE FOIS ANCREES ===")
    print("   abreviations datees au total : %d" % len(detail))
    print("   ancrees sur un compromis     : %d"
          % sum(1 for d in detail if d["echeance_ancree"]))
    print("   INDATABLES (pas d ancre)     : %d"
          % sum(1 for d in detail if not d["echeance_ancree"]))
    print("   ⛔ DANS LE FUTUR (sa regle les interdit) : %d"
          % sum(1 for d in detail if d["dans_le_futur"] == "OUI"))
    print()

    # ⭐⭐⭐ LE VERDICT : COMBIEN PASSENT SA REGLE, LES TROIS CONDITIONS REUNIES ?
    print("=== ⑦ ⭐⭐⭐ LE VERDICT DE SA REGLE, ABREVIATION PAR ABREVIATION ===")
    print("   les trois conditions, TOUTES exigees :")
    print("      a  l'echeance est ANCREE (sinon on ne connait pas l'annee)")
    print("      b  elle n'est PAS dans le futur")
    print("      c  l'affaire est SORTIE du vivant, OU sa date a plus d'un an")
    print()
    refus = Counter()
    posables = []
    for d in detail:
        if not d["echeance_ancree"]:
            refus["a -- echeance indatable"] += 1
            continue
        if d["dans_le_futur"] == "OUI":
            refus["b -- echeance DANS LE FUTUR"] += 1
            continue
        vivant = d["etat_chez_nous"] in vivants
        vieux = (d["date_compromis"]
                 and (date.today() - date.fromisoformat(d["date_compromis"])).days > 365)
        if vivant and not vieux:
            refus["c -- affaire ENCORE VIVANTE et recente"] += 1
            continue
        #: ⛔ DB va en NOTE par sa decision du 17/11, elle n'est pas une condition
        if d["abrev"] == "DB":
            refus["DB -- sa decision du 17/11 : elle va en NOTE"] += 1
            continue
        if d["abrev"] in ("DPC", "OPC"):
            refus["DPC/OPC -- sens NON confirme par lui"] += 1
            continue
        posables.append(d)
    for r, n in refus.most_common():
        print("      ECARTEE  %-44s %4d" % (r[:44], n))
    print()
    print("   ✅ POSABLES (ADP/ODP qui passent les trois) : %d" % len(posables))
    for d in posables[:20]:
        print("      %-10s %-4s %s  (compromis %s, %s)"
              % (d["id_unique"], d["abrev"], d["echeance_ancree"],
                 d["date_compromis"], d["etat_chez_nous"]))
    print()
    #: ⛔⛔ LE COMPTE DOIT BOUCLER : un ecarte non compte ferait un faux zero.
    if sum(refus.values()) + len(posables) != len(detail):
        print("⛔ LE COMPTE NE BOUCLE PAS : %d ecartees + %d posables != %d."
              % (sum(refus.values()), len(posables), len(detail)))
        return 2
    print("   ✅ le compte boucle : %d ecartees + %d posables = %d"
          % (sum(refus.values()), len(posables), len(detail)))
    print()

    # ⛔⛔ LE TEMOIN POSITIF -- un ZERO ne se croit pas sans lui.
    #   « 0 posable » peut vouloir dire « le filtre refuse tout par un defaut ».
    #   On relache UNE SEULE condition a la fois et on regarde si le code sait
    #   dire OUI. S'il rend 0 partout, c'est mon code qui est casse, pas la regle.
    print("=== ⑧ ⛔⛔ LE TEMOIN POSITIF : LE FILTRE SAIT-IL DIRE OUI ? ===")
    for quoi, garder in (
        ("sans (b) : on accepte les echeances dans le futur",
         lambda d: d["echeance_ancree"] and d["abrev"] in ("ADP", "ODP")),
        ("sans (c) : on accepte les affaires encore vivantes",
         lambda d: d["echeance_ancree"] and d["dans_le_futur"] != "OUI"),
        ("sans la reserve DB/DPC/OPC",
         lambda d: d["echeance_ancree"] and d["dans_le_futur"] != "OUI"
         and not (d["etat_chez_nous"] in vivants
                  and d["date_compromis"]
                  and (date.today()
                       - date.fromisoformat(d["date_compromis"])).days <= 365)),
    ):
        n = sum(1 for d in detail if garder(d))
        print("   %-52s %4d" % (quoi, n))
    print()
    if detail:
        with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, delimiter=";", fieldnames=list(detail[0]))
            w.writeheader()
            w.writerows(detail)
        print("ecrit : %s" % RAPPORT)
    print()
    # ⛔⛔ LE TROU TROUVE EN AUDITANT : le generateur de notes du 2e patch ne prend
    #   F que pour les etats MORTS (« Annulée ») et REGLES (« Vente réglée »), plus
    #   la date butoir. UNE LIGNE « EN COURS » SANS DB N'EST DONC PARTIE NULLE PART.
    print("=== ⑨ ⛔⛔ CES 86 TEXTES SONT-ILS AU MOINS GARDES QUELQUE PART ? ===")
    avec_db = {x["id_unique"] for x in cours
               if any(a.upper() == "DB" for a, _ in x["_abrevs"])}
    #: la colonne G du meme Sheet : si elle est remplie, la ligne a une note
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE DU SHEET RATEE : %d lignes. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    i_g = entetes.index("G") if "G" in entetes else None
    i_id = entetes.index("ID Unique")
    avec_g = set()
    for _rang, l in lignes:
        ident = str(l[i_id] if i_id < len(l) else "").strip()
        g = str(l[i_g] if (i_g is not None and i_g < len(l)) else "").strip()
        if ident and g:
            avec_g.add(ident)
    print("   les 86 lignes en cours :")
    print("      parties en note par leur DB            %4d" % len(avec_db))
    print("      parties en note par leur colonne G     %4d"
          % sum(1 for x in cours if x["id_unique"] in avec_g))
    orphelines = [x for x in cours
                  if x["id_unique"] not in avec_db and x["id_unique"] not in avec_g]
    print("      ⛔ NULLE PART (ni DB, ni G)             %4d" % len(orphelines))
    print()
    print("   les textes PERDUS, en entier :")
    for x in orphelines:
        print("      %-10s [%s] %s"
              % (x["id_unique"], (x["etat_actuel"] or "")[:20], x["texte_seul"][:70]))
    print()

    print("=== ⑥ CE QUI EXISTE DEJA DANS app_affaire_condition ===")
    deja = cl.get("app_affaire_condition",
                  {"select": "app_affaire_id,libelle,etat,origine,date_echeance"}) or []
    print("   %d lignes . origines : %s" % (len(deja),
          " . ".join("%s=%d" % kv for kv in
                     Counter(str(r.get("origine")) for r in deja).most_common())))
    print("   avec une date_echeance : %d"
          % sum(1 for r in deja if r.get("date_echeance")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
