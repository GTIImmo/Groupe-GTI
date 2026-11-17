#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C4 (3e patch) -- LOT 1 : les textes de F . LOT 2 : les conditions de credit.
                                                                     17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c4_generer_lots_1_et_2_2026-11-17.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il GENERE :
     supabase/patch_c4_lots_1_et_2_2026-11-17.sql             le patch
     supabase/patch_c4_lots_1_et_2_2026-11-17_INVERSE.sql     le retour arriere
     supabase/patch_c4_lots_1_et_2_2026-11-17_REPETITION.sql  les controles

⭐⭐⭐ SA CORRECTION DU 17/11, ET ELLE A RENVERSE MON VERDICT :
  j'avais bloque les 86 lignes « en cours » au nom de sa regle du chantier. Il a
  repondu : « MA REGLE SUR LES DONNEES DES TRANSACTIONS EN COURS NE PORTAIT PAS SUR
  LES NOTES ». Sa regle protege contre LE CONFLIT ; la bonne question n'est donc pas
  « l'affaire est-elle en cours ? » mais « HEKTOR PORTE-T-IL CETTE DONNEE ? ».

  ⭐⭐⭐ ET LA MESURE REPOND NON, DEUX FOIS :
    . une NOTE : Hektor n'en a aucune, nulle part.
    . une CONDITION SUSPENSIVE : `app_affaire_console.conditions_suspensives` est
      REMPLIE 0 FOIS SUR 18 591. Hektor ne rend qu'un CATALOGUE de 2 choix
      (`conditions_catalogue`) -- la liste deroulante, jamais une condition posee.
  ➡ Aucun ecrasement possible. Sa regle n'a rien a proteger ici.

⛔⛔ ET J'AI ANNONCE « 47 TEXTES PERDUS » ALORS QU'ILS SONT 80. DEUX FAUTES :
  ① `entetes.index("G")` -- « G » est la LETTRE d'une colonne (la 7e, entete
     « COMMENTAIRES »), pas un nom d'entete. La recherche echouait -> « 0 ligne
     sauvee par sa colonne G » : UN ZERO PAR CONSTRUCTION.
  ② Et meme corrige, « a-t-elle un G ? » ne repond pas a la question : une ligne
     avec un G a bien une note, mais cette note porte LE COMMENTAIRE DE G, PAS LE
     TEXTE DE F. Ce sont deux textes differents.
  ➡ LE SEUL CRITERE HONNETE, celui applique ici : le texte de F est-il, mot pour
    mot, DANS la note de sa transaction ? Mesure :
       le texte de F EST dans la note        1
       il N'Y EST PAS                       80   <- le lot 1
       aucune transaction reliee             5
    et le TEMOIN de la methode : sur 60 lignes ANNULEES dont F EST posee, la
    comparaison en retrouve 28 -- elle sait donc dire OUI.

⛔ LA CLE PRIMAIRE COMMANDE LA FORME DU GESTE (la faute d'hier, pas refaite) :
     app_affaire_note       app_affaire_id SEUL   -> UNE note par transaction
     app_affaire_condition  app_affaire_id + rang -> PLUSIEURS permises
  ➡ 81 des transactions visees PORTENT DEJA une note. Le lot 1 est donc un
    COMPLEMENT (on ajoute un paragraphe a la note existante), pas une creation.
    ⭐ On ne REMPLACE jamais : on AJOUTE, et la sauvegarde datee garde le texte
      d'avant pour que l'inverse le restaure a l'octet.

⭐⭐ LES TROIS PROTECTIONS, puisque l'etat d'une condition BOUGE :
  1 l'ORIGINE de la condition porte sa source ('classeur:F-credit'), jamais
    'saisie' -- donc l'inverse ne touche QUE nos lignes.
    ⛔ Pour les notes COMPLETEES, l'origine ne bouge PAS (sinon les controles des
      4 325 notes du 2e patch deviendraient faux) : la marque est LE PREFIXE du
      paragraphe ajoute, et il est unique.
  2 l'ETAT est TOUJOURS 'attente', JAMAIS 'levee'.
  3 l'ECRAN RESTE MAITRE : une saisie humaine ecrasera la notre.
"""
from __future__ import annotations

import csv
import importlib.util
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

#: ⭐ ON REUTILISE L'AUDIT comme module -- meme lecture, meme ancrage, meme tri.
#:   Deux implementations qui divergent, ce sont deux verites. Son nom porte des
#:   tirets, donc il se charge par importlib et non par `import`.
_spec = importlib.util.spec_from_file_location(
    "c4_audit",
    RACINE / "phase2" / "checks" / "c4_auditer_les_86_conditions_2026-11-17.py")
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

DETAIL = RACINE / "notice" / "C4_LES_CLAUSES_DE_LA_COLONNE_F_2026-11-16.csv"
BASE = RACINE / "supabase" / "patch_c4_lots_1_et_2_2026-11-17"
RAPPORT = RACINE / "notice" / "C4_LOTS_1_ET_2_2026-11-17.csv"
LOT_API = 60

#: l'identifiant du catalogue pour « Obtention Credit » -- IL EXISTE DEJA (id 2).
#: ⛔ ADP et ODP n'en sont pas deux clauses mais le DEPART et l'ECHEANCE de
#:   celle-la (24 fois sur 24, ecart median 31 jours).
CATALOGUE_CREDIT = "2"
LIBELLE_CREDIT = "Obtention Crédit"

#: ⭐⭐⭐ SA DECISION DU 17/11, ET ELLE EXPLIQUE SON « 6 » : le catalogue passe de
#:   4 a SIX clauses. « je veux que DPC/OPC c'est bien le depot et l'obtention du
#:   permis devienne deux conditions suspensives en + ».
#:
#: ⭐⭐ ET LE DELAI DE 91 JOURS EST MESURE, PAS INVENTE : sur les 2 lignes du
#:   classeur qui portent DPC *et* OPC, l'ecart est de 90 et 91 jours -- soit
#:   exactement les 3 mois d'instruction d'un permis de construire.
#:   Le DEPOT, lui, est un acte et non un delai : 0.
CLAUSES_NEUVES = [
    ("Depot du permis de construire", 0, "DPC"),
    ("Obtention du permis de construire", 91, "OPC"),
]

#: ⚠ UNE REDONDANCE A DIRE, pas a cacher : « Permis de construire » (id 3) a ete
#:   pose hier pour le MOTIF « refus PC » et pour le signe « PC » (34 fois). Les
#:   deux clauses neuves sont les DEUX ETAPES de ce meme permis. C'est son choix,
#:   et il est utile (un compromis attend le depot, PUIS l'obtention) -- mais le
#:   catalogue portera donc trois libelles autour du permis.
CATALOGUE_PC_GENERIQUE = "3"

ORIGINE_COND = "classeur:F-credit"
ORIGINE_NOTE_NEUVE = "classeur:F-en-cours"
#: ⭐⭐ LA MARQUE DU PARAGRAPHE AJOUTE -- c'est elle qui rend le geste mesurable
#:   ET reversible, puisque l'origine de la note ne bouge pas.
MARQUE = "[classeur F, suivi en cours au 17/11/2026]"


def index_de(lettre: str) -> int:
    """« G » -> 6. La LETTRE d'une colonne du Sheet, pas son entete."""
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def normaliser(t: str) -> str:
    """Pour comparer deux textes sans se faire piéger par les accents ni l'espace."""
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", t).strip()


def txt(v) -> str:
    """Un litteral SQL sur UNE SEULE LIGNE, sans retour chariot (lecon 30)."""
    s = str(v if v is not None else "")
    s = s.replace("\r", " ").replace("\n", " ")
    return "'" + s.replace("'", "''") + "'"


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== C4 (3e patch) -- LOTS 1 ET 2 (aucune ecriture en base) ===")
    print()

    with DETAIL.open(encoding="utf-8-sig", newline="") as f:
        toutes = list(csv.DictReader(f, delimiter=";"))
    if len(toutes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes. ON NE GENERE RIEN." % len(toutes))
        return 2

    cours = [x for x in toutes
             if x["famille"] == "CLAUSE ou MOTIF"
             and (x["etat_actuel"] or "").strip() not in ("Annulée", "Vente réglée")]
    if not (70 <= len(cours) <= 110):
        print("⛔ LE COMPTE DES LIGNES EN COURS A BOUGE (%d)." % len(cours))
        return 2
    for x in cours:
        x["_abrevs"] = audit.lire_abrevs(x["texte_seul"])
    print("lignes « en cours » : %d" % len(cours))

    #: ⛔ LE TEMOIN DE LA COLONNE G -- c'est lui qui aurait attrape mon zero par
    #:   construction. « G » est la 7e colonne, remplie sur ~4 132 lignes.
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE DU SHEET RATEE : %d lignes." % len(lignes))
        return 2
    i_g = index_de("G")
    n_g = sum(1 for _r, l in lignes
              if i_g < len(l) and str(l[i_g] or "").strip())
    print("   la colonne G est la %de, entete %r, remplie %d fois"
          % (i_g + 1, entetes[i_g], n_g))
    if n_g < 3000:
        print("⛔ LA COLONNE G EST MAL LUE (%d, on attend ~4 132)." % n_g)
        return 2
    print()

    # --- LA CIBLE DE CHAQUE LIGNE, ET LE TEXTE DE SA NOTE --------------------
    cl = audit.client()
    liens = audit.tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id",
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

    #: ⭐ ON LIT LE TEXTE des notes, pas seulement leur existence
    notes: dict[int, dict] = {}
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        for r in (cl.get("app_affaire_note",
                         {"select": "app_affaire_id,texte,origine",
                          "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or []):
            notes[int(r["app_affaire_id"])] = r
    sans_texte = sum(1 for r in notes.values() if not str(r.get("texte") or "").strip())
    print("transactions reliees %d . portant une note %d . dont sans texte %d"
          % (len(besoin), len(notes), sans_texte))
    if sans_texte:
        print("⛔ DES NOTES SANS TEXTE : la lecture est suspecte.")
        return 2

    rang_pris: dict[int, int] = defaultdict(int)
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        for r in (cl.get("app_affaire_condition",
                         {"select": "app_affaire_id,rang",
                          "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or []):
            a = int(r["app_affaire_id"])
            rang_pris[a] = max(rang_pris[a], int(r["rang"] or 0))
    print("transactions portant deja une condition : %d" % len(rang_pris))
    print()

    def avancee(trs):
        """La transaction la plus avancee : vente > compromis > offre."""
        for k in ("vente", "compromis", "offre"):
            m = [t for t in trs if t.get("kind") == k]
            if m:
                return m[0]
        return trs[0] if trs else None

    # ─── LOT 1 : LES TEXTES DE F QUI NE SONT NULLE PART ──────────────────────
    a_completer, a_creer = [], []
    deja, sans_lien = 0, 0
    for x in cours:
        t_f = (x["texte_seul"] or "").strip()
        cibles = par_id.get(x["id_unique"], [])
        trs = [ledger[str(a)] for a in cibles if str(a) in ledger]
        if not trs:
            sans_lien += 1
            continue
        n = normaliser(t_f)
        textes = [str(notes[a]["texte"]) for a in cibles if a in notes]
        if n and any(n in normaliser(u) for u in textes):
            deja += 1
            continue
        cible = avancee(trs)
        a = int(cible["app_affaire_id"])
        frag = "%s %s" % (MARQUE, t_f)
        if a in notes:
            a_completer.append({"app_affaire_id": a, "fragment": frag,
                                "id_unique": x["id_unique"],
                                "etat_classeur": x["etat_actuel"],
                                "origine_note": notes[a].get("origine")})
        else:
            #: ⚠ une transaction LIBRE de la chaine, pour ne pas heurter la cle
            libres = [u for u in trs if int(u["app_affaire_id"]) not in notes]
            cible2 = avancee(libres) if libres else None
            if cible2 is None:
                a_completer.append({"app_affaire_id": a, "fragment": frag,
                                    "id_unique": x["id_unique"],
                                    "etat_classeur": x["etat_actuel"],
                                    "origine_note": notes[a].get("origine")})
                continue
            b = int(cible2["app_affaire_id"])
            notes[b] = {"app_affaire_id": b, "texte": frag,
                        "origine": ORIGINE_NOTE_NEUVE}
            a_creer.append({"app_affaire_id": b, "texte": frag,
                            "app_dossier_id": cible2.get("app_dossier_id"),
                            "app_chaine_id": cible2.get("app_chaine_id"),
                            "id_unique": x["id_unique"],
                            "etat_classeur": x["etat_actuel"]})
    print("=== LOT 1 -- LES TEXTES DE F ===")
    print("   ✅ a COMPLETER (la note existe)      %4d" % len(a_completer))
    print("   ✅ a CREER (aucune note sur la chaine) %3d" % len(a_creer))
    print("   ·  deja dans la note                 %4d" % deja)
    print("   ⚠  aucune transaction reliee         %4d" % sans_lien)
    print("   ---------------------------------------------")
    print("   total                                %4d" % len(cours))
    if len(a_completer) + len(a_creer) + deja + sans_lien != len(cours):
        print("⛔ LE COMPTE NE BOUCLE PAS.")
        return 2
    #: ⛔ une meme transaction ne doit pas etre completee DEUX fois (la cle)
    dbl = [a for a, n in Counter(x["app_affaire_id"] for x in a_completer).items()
           if n > 1]
    if dbl:
        print("   ⚠ %d transactions recoivent PLUSIEURS fragments -- on les FUSIONNE"
              % len(dbl))
        fusion: dict[int, dict] = {}
        for x in a_completer:
            a = x["app_affaire_id"]
            if a in fusion:
                fusion[a]["fragment"] += " | " + x["fragment"]
                fusion[a]["id_unique"] += " " + x["id_unique"]
            else:
                fusion[a] = dict(x)
        a_completer = list(fusion.values())
        print("   -> %d mises a jour apres fusion" % len(a_completer))
    print()

    # ─── LE CATALOGUE : DEUX CLAUSES NEUVES, SA DECISION DU 17/11 ────────────
    #: ⛔ `id` est TEXT, NOT NULL et SANS DEFAUT : ce n'est pas une sequence mais
    #:   un identifiant choisi a la main. Il faut le FOURNIR -- le maximum
    #:   NUMERIQUE + 1, en ne lisant que les ids numeriques (la faute d'hier).
    cat = cl.get("app_condition_catalogue", {"select": "id,libelle,jours_defaut,rang"}) or []
    print("=== LE CATALOGUE AVANT : %d clauses ===" % len(cat))
    for r in sorted(cat, key=lambda r: int(r["rang"] or 0)):
        print("   %-3s %-36s %3s j" % (r["id"], r["libelle"], r["jours_defaut"]))
    deja_lib = {normaliser(r["libelle"]) for r in cat}
    num = [int(r["id"]) for r in cat if str(r["id"]).isdigit()]
    rang = max([int(r["rang"] or 0) for r in cat] or [0])
    prochain = (max(num) if num else 0) + 1
    clauses, id_de = [], {}
    for libelle, jours, signe in CLAUSES_NEUVES:
        if normaliser(libelle) in deja_lib:
            print("   ⚠ « %s » EXISTE DEJA au catalogue -- on ne la recree pas"
                  % libelle)
            id_de[signe] = next(r["id"] for r in cat
                                if normaliser(r["libelle"]) == normaliser(libelle))
            continue
        rang += 1
        clauses.append({"id": str(prochain), "libelle": libelle,
                        "jours_defaut": jours, "rang": rang})
        id_de[signe] = str(prochain)
        prochain += 1
    print("   ➡ A AJOUTER : %s"
          % (" . ".join("%s=%s (%d j)" % (c["id"], c["libelle"], c["jours_defaut"])
                        for c in clauses) or "(aucune)"))
    print("   ⚠ et « Permis de construire » (id %s) reste au catalogue : les deux"
          % CATALOGUE_PC_GENERIQUE)
    print("     clauses neuves en sont les DEUX ETAPES, pas un remplacement.")
    print()

    # ─── LOT 2 : LES CONDITIONS, TROIS SIGNES ────────────────────────────────
    #: ⭐ ODP -> « Obtention Credit » (id 2, le delai vient de ADP->ODP)
    #:   DPC -> « Depot du permis de construire »      (sa decision du 17/11)
    #:   OPC -> « Obtention du permis de construire »  (sa decision du 17/11)
    PLAN = [("ODP", CATALOGUE_CREDIT, LIBELLE_CREDIT),
            ("DPC", None, "Depot du permis de construire"),
            ("OPC", None, "Obtention du permis de construire")]
    conditions, ecarte = [], Counter()
    for x in cours:
        trs = [ledger[str(a)] for a in par_id.get(x["id_unique"], []) if str(a) in ledger]
        comp = [t for t in trs if t.get("kind") == "compromis"]
        for signe, cat_id, libelle in PLAN:
            vus = [jm for a, jm in x["_abrevs"] if a.upper() == signe]
            if not vus:
                continue
            if len(comp) != 1:
                ecarte["%s -- pas UN SEUL compromis dans la chaine" % signe] += 1
                continue
            t = comp[0]
            dref = None
            if t.get("date"):
                try:
                    dref = date.fromisoformat(str(t["date"])[:10])
                except ValueError:
                    dref = None
            d, _p = audit.ancrer(vus[0], dref)
            if d is None:
                ecarte["%s -- echeance indatable (pas d ancre)" % signe] += 1
                continue
            #: le DELAI : pour le credit, l'ecart ADP->ODP mesure sur CETTE ligne ;
            #: pour le permis, le `jours_defaut` de sa clause (91 j, mesure).
            jours = None
            if signe == "ODP":
                adp = [jm for a, jm in x["_abrevs"] if a.upper() == "ADP"]
                if adp:
                    d_adp, _q = audit.ancrer(adp[0], dref)
                    if d_adp is not None and d >= d_adp:
                        jours = (d - d_adp).days
            else:
                jours = next((j for lib, j, s in CLAUSES_NEUVES if s == signe), None)
            a = int(t["app_affaire_id"])
            rang_pris[a] += 1
            conditions.append({"app_affaire_id": a, "rang": rang_pris[a],
                               "libelle": libelle, "jours": jours,
                               "date_echeance": d.isoformat(),
                               "catalogue_id": cat_id or id_de[signe],
                               "app_dossier_id": t.get("app_dossier_id"),
                               "app_chaine_id": t.get("app_chaine_id"),
                               "note": x["texte_seul"].strip()[:300],
                               "id_unique": x["id_unique"], "signe": signe,
                               "date_compromis": dref.isoformat() if dref else "",
                               "etat_chez_nous": t.get("state")})
    print("=== LOT 2 -- LES CONDITIONS SUSPENSIVES ===")
    print("   ✅ posables                          %4d" % len(conditions))
    for s, n in Counter(c["signe"] for c in conditions).most_common():
        lib = next(libelle for sg, _c, libelle in PLAN if sg == s)
        print("      %-5s %-36s %4d" % (s, lib[:36], n))
    for k, n in ecarte.most_common():
        print("   ⚠  ECARTEE %-42s %4d" % (k[:42], n))
    if conditions:
        js = sorted(c["jours"] for c in conditions
                    if c["jours"] is not None and c["signe"] == "ODP")
        if js:
            print("   le delai ADP->ODP : de %d a %d jours, median %d"
                  % (js[0], js[-1], js[len(js) // 2]))
        print("   les echeances par annee : %s"
              % " . ".join("%s=%d" % kv for kv in sorted(
                  Counter(c["date_echeance"][:4] for c in conditions).items())))
        print("   deja passees %d . a venir %d"
              % (sum(1 for c in conditions
                     if date.fromisoformat(c["date_echeance"]) <= date.today()),
                 sum(1 for c in conditions
                     if date.fromisoformat(c["date_echeance"]) > date.today())))
    print()
    if not (a_completer or a_creer) or not conditions:
        print("⛔ UN LOT EST VIDE -- on ne genere pas un patch a moitie.")
        return 2

    with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["lot", "geste", "app_affaire_id", "id_unique", "valeur"])
        for x in a_completer:
            w.writerow(["1 note", "COMPLETER", x["app_affaire_id"], x["id_unique"],
                        x["fragment"]])
        for x in a_creer:
            w.writerow(["1 note", "CREER", x["app_affaire_id"], x["id_unique"],
                        x["texte"]])
        for c in conditions:
            w.writerow(["2 condition", "CREER", c["app_affaire_id"], c["id_unique"],
                        "%s echeance %s delai %s"
                        % (c["libelle"], c["date_echeance"], c["jours"])])
    print("ecrit : %s" % RAPPORT)

    # ─── LE PATCH ────────────────────────────────────────────────────────────
    nu, nn, nc = len(a_completer), len(a_creer), len(conditions)
    ntot = nu + nn
    v_upd = ",\n    ".join("(%d, %s)" % (x["app_affaire_id"], txt(x["fragment"]))
                           for x in a_completer)
    v_ins = ",\n    ".join(
        "(%d, %s, %s, %s, %s)"
        % (x["app_affaire_id"],
           x["app_dossier_id"] if x["app_dossier_id"] else "null",
           x["app_chaine_id"] if x["app_chaine_id"] else "null",
           txt(x["texte"]), txt(ORIGINE_NOTE_NEUVE)) for x in a_creer) or "(null,null,null,null,null)"
    v_cond = ",\n    ".join(
        "(%d, %d, %s, %s, %s::date, %s, %s, %s, %s, %s)"
        % (c["app_affaire_id"], c["rang"], txt(c["libelle"]),
           c["jours"] if c["jours"] is not None else "null",
           txt(c["date_echeance"]), txt(c["catalogue_id"]),
           c["app_dossier_id"] if c["app_dossier_id"] else "null",
           c["app_chaine_id"] if c["app_chaine_id"] else "null",
           txt(c["note"]), txt(ORIGINE_COND)) for c in conditions)
    aujourd = date.today().isoformat()
    ncl = len(clauses)
    ncat_apres = len(cat) + ncl
    ids_cl = ", ".join(txt(c["id"]) for c in clauses) or "''"
    v_cat = ",\n    ".join("(%s, %s, %d, %d)"
                           % (txt(c["id"]), txt(c["libelle"]),
                              c["jours_defaut"], c["rang"]) for c in clauses)
    bloc_cat = "" if not clauses else f"""
-- ②bis LE CATALOGUE -- LES {ncl} CLAUSES NEUVES (sa decision du 17/11)
--    ⛔ `id` est TEXT, NOT NULL, SANS DEFAUT : on le FOURNIT (max numerique + 1).
--    ⭐ 91 jours est MESURE : sur les 2 lignes du classeur portant DPC *et* OPC,
--      l'ecart est de 90 et 91 jours -- les 3 mois d'instruction d'un permis.
insert into app_condition_catalogue (id, libelle, jours_defaut, rang)
values
    {v_cat}
on conflict (id) do nothing;
"""
    #: ⭐ UN CONTROLE PAR LIBELLE -- un total juste peut cacher deux erreurs qui
    #:   s'annulent. On compte donc chaque clause separement.
    par_lib = Counter(c["libelle"] for c in conditions)
    detail_signes = "\nunion all\n".join(
        "select '   dont « %s » (attendu %d)', count(*)::text,\n"
        "       case when count(*) = %d then '✅' else '⛔' end\n"
        "  from app_affaire_condition\n"
        " where origine = %s and libelle = %s"
        % (lib.replace("'", "''"), n, n, txt(ORIGINE_COND), txt(lib))
        for lib, n in sorted(par_lib.items()))
    bloc_ins = "" if not a_creer else f"""
-- ④ bis LOT 1 -- LES {nn} NOTES A CREER (aucune note sur toute la chaine)
insert into app_affaire_note
    (app_affaire_id, app_dossier_id, app_chaine_id, texte, origine)
values
    {v_ins}
on conflict (app_affaire_id) do nothing;
"""

    patch = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (3e patch) -- LOT 1 : {ntot} TEXTES DE F . LOT 2 : {nc} CONDITIONS DE CREDIT
-- Genere le {aujourd} par phase2/checks/c4_generer_lots_1_et_2_2026-11-17.py
--
-- ⭐⭐⭐ SA CORRECTION DU 17/11 : « MA REGLE SUR LES DONNEES DES TRANSACTIONS EN
--   COURS NE PORTAIT PAS SUR LES NOTES ». Sa regle protege contre LE CONFLIT ; la
--   bonne question est « HEKTOR PORTE-T-IL CETTE DONNEE ? », et la mesure dit NON
--   deux fois : aucune note chez Hektor, et `conditions_suspensives` est remplie
--   0 FOIS SUR 18 591 (il ne rend qu'un catalogue de 2 choix).
--
-- ⛔⛔ J'AVAIS ANNONCE 47 TEXTES PERDUS : ILS SONT {ntot}. Mon critere cherchait le
--   nom d'entete « G » (c'est la LETTRE de la 7e colonne, entete COMMENTAIRES) --
--   un zero par construction -- puis, corrige, il confondait « la ligne a un
--   commentaire G » avec « LE TEXTE DE F est pose ». Ce sont deux textes.
--
-- ⭐⭐ LE LOT 1 EST UN COMPLEMENT, PAS UN REMPLACEMENT : la cle de app_affaire_note
--   est app_affaire_id SEUL, et {nu} transactions portent deja une note. On AJOUTE
--   un paragraphe marque « {MARQUE} », et la sauvegarde datee garde le texte
--   d'avant pour que l'inverse le restaure a l'octet.
--
-- ⛔ L'ORIGINE DES NOTES COMPLETEES NE BOUGE PAS -- sinon les controles des 4 325
--   notes du 2e patch deviendraient faux. La marque est le PREFIXE du paragraphe.
--
-- RETOUR ARRIERE : patch_c4_lots_1_et_2_2026-11-17_INVERSE.sql
-- CONTROLES      : patch_c4_lots_1_et_2_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① LE GARDE-FOU : si le lot est deja pose, on ne rejoue pas
do $$
declare n_note integer; n_cond integer;
begin
  select count(*) into n_note from app_affaire_note
   where position({txt(MARQUE)} in texte) > 0;
  select count(*) into n_cond from app_affaire_condition
   where origine = {txt(ORIGINE_COND)};
  if n_note > 0 or n_cond > 0 then
    raise exception '⛔ DEJA POSE : % notes marquees et % conditions. '
      'Jouer l INVERSE d abord.', n_note, n_cond;
  end if;
end $$;

-- ② LA SAUVEGARDE DATEE : le texte EXACT d'avant, pour les notes qu'on complete
drop table if exists app_c4_note_avant_20261117;
create table app_c4_note_avant_20261117 as
  select app_affaire_id, texte, origine, now() as sauve_le
    from app_affaire_note
   where app_affaire_id in ({", ".join(str(x["app_affaire_id"]) for x in a_completer)});

do $$
declare n integer;
begin
  select count(*) into n from app_c4_note_avant_20261117;
  if n <> {nu} then
    raise exception '⛔ LA SAUVEGARDE PORTE % lignes au lieu de {nu}', n;
  end if;
end $$;
{bloc_cat}
-- ③ LOT 1 -- COMPLETER LES {nu} NOTES EXISTANTES
--    ⭐ on AJOUTE un paragraphe, on ne remplace rien. Et la clause `position`
--      rend le geste IDEMPOTENT : rejoue, il n'ajoute pas deux fois.
update app_affaire_note n
   set texte = n.texte || chr(10) || v.fragment
  from (values
    {v_upd}
  ) as v(app_affaire_id, fragment)
 where n.app_affaire_id = v.app_affaire_id
   and position(v.fragment in n.texte) = 0;
{bloc_ins}
-- ⑤ LOT 2 -- LES {nc} CONDITIONS « Obtention Credit »
--    etat : la valeur par defaut 'attente'. On n'affirme JAMAIS une levee.
insert into app_affaire_condition
    (app_affaire_id, rang, libelle, jours, date_echeance, catalogue_id,
     app_dossier_id, app_chaine_id, note, origine)
values
    {v_cond}
on conflict (app_affaire_id, rang) do nothing;

-- ⑥ LES CONTROLES, DANS LA MEME TRANSACTION -- un seul faux et tout tombe
do $$
declare n integer;
begin
  select count(*) into n from app_affaire_note
   where position({txt(MARQUE)} in texte) > 0;
  if n <> {ntot} then
    raise exception '⛔ LOT 1 : % notes marquees au lieu de {ntot}', n;
  end if;

  select count(*) into n from app_affaire_condition where origine = {txt(ORIGINE_COND)};
  if n <> {nc} then raise exception '⛔ LOT 2 : % conditions au lieu de {nc}', n; end if;

  -- ⭐ LES VOISINS SONT INTACTS
  select count(*) into n from app_affaire_note where origine = 'classeur';
  if n <> 195 then raise exception '⛔ LES 195 NOTES DE C5 ONT BOUGE : %', n; end if;
  select count(*) into n from app_affaire_note
   where origine in ('classeur:F', 'classeur:G', 'classeur:F+G');
  if n <> 4325 then raise exception '⛔ LES 4 325 NOTES DU 2e PATCH ONT BOUGE : %', n; end if;
  select count(*) into n from app_affaire_condition where origine = 'saisie';
  if n <> 5 then raise exception '⛔ LES 5 CONDITIONS SAISIES ONT BOUGE : %', n; end if;

  -- ⭐⭐ LE TEXTE D'AVANT EST TOUJOURS LA : on a COMPLETE, pas remplace
  select count(*) into n
    from app_c4_note_avant_20261117 s
    join app_affaire_note a on a.app_affaire_id = s.app_affaire_id
   where position(s.texte in a.texte) = 0;
  if n <> 0 then
    raise exception '⛔ % notes ont PERDU leur texte d origine -- on remplace !', n;
  end if;

  -- ⭐ aucune condition en levee, aucune note vide, echeance et catalogue partout
  select count(*) into n from app_affaire_condition
   where origine = {txt(ORIGINE_COND)} and etat <> 'attente';
  if n <> 0 then raise exception '⛔ % conditions ne sont pas en attente', n; end if;
  select count(*) into n from app_affaire_note where coalesce(btrim(texte), '') = '';
  if n <> 0 then raise exception '⛔ % notes vides', n; end if;
  select count(*) into n from app_affaire_condition
   where origine = {txt(ORIGINE_COND)} and date_echeance is null;
  if n <> 0 then raise exception '⛔ % conditions sans echeance', n; end if;

  -- ⭐⭐ CHAQUE CONDITION POINTE UNE CLAUSE QUI EXISTE VRAIMENT au catalogue --
  --   une jointure, pas une liste en dur : c'est la base qui repond.
  select count(*) into n from app_affaire_condition c
   where c.origine = {txt(ORIGINE_COND)}
     and not exists (select 1 from app_condition_catalogue k
                      where k.id = c.catalogue_id);
  if n <> 0 then raise exception '⛔ % conditions pointent une clause INEXISTANTE', n; end if;

  -- ⭐ LE CATALOGUE EST A {ncat_apres}, et les {len(cat)} d'avant sont INTACTES
  select count(*) into n from app_condition_catalogue;
  if n <> {ncat_apres} then
    raise exception '⛔ LE CATALOGUE PORTE % clauses au lieu de {ncat_apres}', n;
  end if;
  select count(*) into n from app_condition_catalogue
   where id in ({", ".join(txt(r["id"]) for r in cat)});
  if n <> {len(cat)} then
    raise exception '⛔ LES {len(cat)} CLAUSES D ORIGINE ONT BOUGE : %', n;
  end if;

  raise notice '✅ LOT 1 : % textes de F . LOT 2 : % conditions . catalogue a %',
    {ntot}, {nc}, {ncat_apres};
end $$;

commit;
"""

    inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (3e patch) -- LE RETOUR ARRIERE DES LOTS 1 ET 2
-- Genere le {aujourd}
--
-- ⭐⭐ IL RESTAURE LE TEXTE EXACT D'AVANT depuis la sauvegarde datee, et il ne
--   touche que : les notes PORTANT LA MARQUE, les notes d'origine
--   '{ORIGINE_NOTE_NEUVE}', et les conditions d'origine '{ORIGINE_COND}'.
--   Il ne PEUT PAS toucher les 195 notes de C5, les 4 325 du 2e patch, ni les
--   5 conditions saisies dans l'app.
--
-- ⛔ ET IL JUGE SA PROPRE PART (lecon 31) : il verifie qu'il ne reste AUCUNE
--   trace de la marque, ET que les voisins sont intacts.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① les notes CREEES par le patch : on les retire
delete from app_affaire_note where origine = {txt(ORIGINE_NOTE_NEUVE)};

-- ② les notes COMPLETEES : on restaure le texte EXACT d'avant
update app_affaire_note a
   set texte = s.texte
  from app_c4_note_avant_20261117 s
 where a.app_affaire_id = s.app_affaire_id
   and a.texte <> s.texte;

-- ③ les conditions posees par le patch
delete from app_affaire_condition where origine = {txt(ORIGINE_COND)};

-- ④ les clauses neuves du catalogue -- ⛔ SEULEMENT si plus rien ne les utilise
delete from app_condition_catalogue k
 where k.id in ({ids_cl})
   and not exists (select 1 from app_affaire_condition c where c.catalogue_id = k.id);

do $$
declare n integer;
begin
  select count(*) into n from app_affaire_note
   where position({txt(MARQUE)} in texte) > 0;
  if n <> 0 then raise exception '⛔ il reste % notes marquees', n; end if;
  select count(*) into n from app_affaire_note where origine = {txt(ORIGINE_NOTE_NEUVE)};
  if n <> 0 then raise exception '⛔ il reste % notes creees', n; end if;
  select count(*) into n from app_affaire_condition where origine = {txt(ORIGINE_COND)};
  if n <> 0 then raise exception '⛔ il reste % conditions', n; end if;

  -- ⭐⭐ LE TEXTE EST REVENU A L'IDENTIQUE, pas seulement « sans la marque »
  select count(*) into n
    from app_c4_note_avant_20261117 s
    join app_affaire_note a on a.app_affaire_id = s.app_affaire_id
   where a.texte <> s.texte;
  if n <> 0 then raise exception '⛔ % notes ne sont pas revenues a l identique', n; end if;

  -- ⭐ LES VOISINS, PROUVES INTACTS
  select count(*) into n from app_affaire_note where origine = 'classeur';
  if n <> 195 then raise exception '⛔ LES 195 NOTES DE C5 ONT BOUGE : %', n; end if;
  select count(*) into n from app_affaire_note
   where origine in ('classeur:F', 'classeur:G', 'classeur:F+G');
  if n <> 4325 then raise exception '⛔ LES 4 325 NOTES DU 2e PATCH ONT BOUGE : %', n; end if;
  select count(*) into n from app_affaire_condition where origine = 'saisie';
  if n <> 5 then raise exception '⛔ LES 5 CONDITIONS SAISIES ONT BOUGE : %', n; end if;

  -- ⭐ LE CATALOGUE EST REVENU A {len(cat)}, et ses clauses d'origine sont LA
  select count(*) into n from app_condition_catalogue;
  if n <> {len(cat)} then
    raise exception '⛔ LE CATALOGUE PORTE % clauses au lieu de {len(cat)}', n;
  end if;
  select count(*) into n from app_condition_catalogue
   where id in ({", ".join(txt(r["id"]) for r in cat)});
  if n <> {len(cat)} then
    raise exception '⛔ LES {len(cat)} CLAUSES D ORIGINE ONT BOUGE : %', n;
  end if;

  raise notice '✅ RETOUR ARRIERE COMPLET, texte restaure a l identique';
end $$;

commit;
"""

    repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (3e patch) -- LES CONTROLES, A REJOUER AUTANT DE FOIS QU'ON VEUT
-- Genere le {aujourd}. ⛔ IL N'ECRIT RIEN.
-- ⭐ Chaque ligne porte CE QU'ON ATTEND, pour qu'un ecart saute aux yeux.
-- ═══════════════════════════════════════════════════════════════════════════
select 'LOT 1 -- textes de F marques (attendu {ntot})' as controle,
       count(*)::text as mesure,
       case when count(*) = {ntot} then '✅' else '⛔' end as verdict
  from app_affaire_note where position({txt(MARQUE)} in texte) > 0
union all
select 'LOT 1 -- dont CREEES (attendu {nn})', count(*)::text,
       case when count(*) = {nn} then '✅' else '⛔' end
  from app_affaire_note where origine = {txt(ORIGINE_NOTE_NEUVE)}
union all
select 'LOT 2 -- conditions de credit (attendu {nc})', count(*)::text,
       case when count(*) = {nc} then '✅' else '⛔' end
  from app_affaire_condition where origine = {txt(ORIGINE_COND)}
union all
select 'toutes en etat attente (attendu {nc})', count(*)::text,
       case when count(*) = {nc} then '✅' else '⛔' end
  from app_affaire_condition where origine = {txt(ORIGINE_COND)} and etat = 'attente'
union all
select 'toutes avec une echeance (attendu {nc})', count(*)::text,
       case when count(*) = {nc} then '✅' else '⛔' end
  from app_affaire_condition
 where origine = {txt(ORIGINE_COND)} and date_echeance is not null
union all
select '⭐⭐ chaque condition pointe une clause EXISTANTE (attendu 0 orpheline)',
       count(*)::text, case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_condition c
 where c.origine = {txt(ORIGINE_COND)}
   and not exists (select 1 from app_condition_catalogue k where k.id = c.catalogue_id)
union all
select 'LE CATALOGUE porte {ncat_apres} clauses (sa decision du 17/11)',
       count(*)::text, case when count(*) = {ncat_apres} then '✅' else '⛔' end
  from app_condition_catalogue
union all
select '⭐ VOISIN -- les {len(cat)} clauses d origine (attendu {len(cat)})',
       count(*)::text, case when count(*) = {len(cat)} then '✅' else '⛔' end
  from app_condition_catalogue where id in ({", ".join(txt(r["id"]) for r in cat)})
union all
{detail_signes}
union all
select '⭐⭐ LE TEXTE D AVANT EST INTACT (attendu 0 perdu)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_c4_note_avant_20261117 s
  join app_affaire_note a on a.app_affaire_id = s.app_affaire_id
 where position(s.texte in a.texte) = 0
union all
select '⭐ VOISIN -- les 195 notes de C5 (attendu 195)', count(*)::text,
       case when count(*) = 195 then '✅' else '⛔' end
  from app_affaire_note where origine = 'classeur'
union all
select '⭐ VOISIN -- les notes du 2e patch (attendu 4325)', count(*)::text,
       case when count(*) = 4325 then '✅' else '⛔' end
  from app_affaire_note
 where origine in ('classeur:F', 'classeur:G', 'classeur:F+G')
union all
select '⭐ VOISIN -- les 5 conditions saisies (attendu 5)', count(*)::text,
       case when count(*) = 5 then '✅' else '⛔' end
  from app_affaire_condition where origine = 'saisie'
union all
select 'aucune note vide, TOUTE la table (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_note where coalesce(btrim(texte), '') = ''
union all
select 'une seule note par transaction (attendu 0 doublon)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from (select app_affaire_id from app_affaire_note
         group by app_affaire_id having count(*) > 1) d
union all
select '⛔ TEMOIN INVERSE -- aucune condition en levee (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_condition
 where origine = {txt(ORIGINE_COND)} and (etat = 'levee' or date_levee is not null)
union all
select '⛔ TEMOIN INVERSE -- aucune echeance hors 2024-2027 (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_affaire_condition
 where origine = {txt(ORIGINE_COND)}
   and (date_echeance < '2024-01-01'::date or date_echeance > '2027-12-31'::date)
union all
select '⭐ les conditions tombent sur des COMPROMIS (attendu {nc})', count(*)::text,
       case when count(*) = {nc} then '✅' else '⛔' end
  from app_affaire_condition c
  join app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id
 where c.origine = {txt(ORIGINE_COND)} and l.kind = 'compromis'
union all
select '⭐ les notes marquees tombent sur une CHAINE (attendu {ntot})', count(*)::text,
       case when count(*) = {ntot} then '✅' else '⛔' end
  from app_affaire_note n
  join app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id
 where position({txt(MARQUE)} in n.texte) > 0 and l.app_chaine_id is not null;
"""

    for suffixe, contenu in ((".sql", patch), ("_INVERSE.sql", inverse),
                             ("_REPETITION.sql", repetition)):
        p = Path(str(BASE) + suffixe)
        #: ⛔ EN LF PUR, pas en CRLF -- un patch est COLLE dans l'editeur SQL, et
        #:   la lecon 30 dit qu'un retour chariot egare dans un patch colle fait
        #:   des degats. `write_text` traduit \n en \r\n sur Windows : on l'empeche
        #:   en ecrivant les octets nous-memes.
        p.write_bytes(contenu.encode("utf-8"))
        b = p.read_bytes()
        print("ecrit : %-50s %6d octets . CR %d"
              % (p.name, len(b), b.count(b"\r")))
        if b.count(b"\r"):
            print("⛔ DES RETOURS CHARIOT DANS UN PATCH A COLLER.")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
