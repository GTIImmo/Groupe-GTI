#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C3 -- LES 896 DATES D'ANNULATION DU CLASSEUR : OU SE POSENT-ELLES ?   16/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c3_mesurer_les_dates_annulation_2026-11-16.py

⛔ CE SCRIPT N'ECRIT RIEN. Il lit le Sheet, il lit Supabase, il MESURE et il
  ecrit UN FICHIER dans notice/. Aucune ecriture en base, aucune chez Hektor.

SON ENONCE, AU PLAN (C3) : « Z : 896 dates d'annulation dans date_annulation_app,
DEJA PRETE. En face : des affaires cancelled/refused qui ne disent pas QUAND. »

⭐⭐⭐ POURQUOI C3 N'EST PAS C5, ET C'EST TOUTE LA DIFFERENCE :
  C5 CREAIT des transactions -- d'ou la regle « historique, jamais le present », les
  sept gardes et l'arret sur les affaires en cours. C3 ne cree RIEN : il complete une
  colonne de CLASSE A, sur une transaction QUI EXISTE DEJA et QUI EST DEJA ANNULEE.
  Et `date_annulation_app` n'a AUCUN equivalent chez Hektor (commentaire de la
  colonne 46 : « A NOUS »), donc aucun conflit n'est possible avec lui, jamais.
  ➡ le perimetre n'a donc pas a s'arreter a l'historique. Ce qui reste a garder,
    c'est la JUSTESSE de la date, pas la propriete de la ligne.

LE BALAYAGE DE SES LECTEURS EST FAIT (16/11), et il est propre :
  en base      0 vue . 0 fonction . 0 declencheur ne lit date_annulation_app
  dans le code assistant_objets.py:276 et assistant.ts:164 -- l'ASSISTANT, autre
               chantier ; plus les DEUX protections du push (la colonne figure dans
               COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS depuis le 10/11, AVANT tout
               remplissage, « lecon du 07/09 »)

⚠ CE QUE A1 A MESURE SUR Z, ET QUI COMMANDE LA LECTURE :
      Z ; Annulee ; 896 remplies ; 180 DISTINCTES ; date=896 ; 0 texte
  Z est donc PROPRE -- pas de « 5 decembre23 » comme dans Y. On passe quand meme par
  le parseur TOLERANT : il est additif, il ne coute rien, et un classeur qui gagne
  deux lignes par jour peut gagner un format demain.
  ⚠ 896 valeurs pour 180 dates distinctes = 5 lignes par date en moyenne. Ce script
    le MESURE au lieu de le supposer : des annulations groupees sont plausibles, un
    copier-coller massif aussi, et les deux ne se traitent pas pareil.
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
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
sys.path.insert(0, str(RACINE / "monitoring"))

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402
from rapport_gel_tous_les_champs import date_du_classeur_tolerante  # noqa: E402

AUJOURD_HUI = date(2026, 11, 16)
LOT_API = 60
SORTIE = RACINE / "notice" / "C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv"

#: ⭐⭐⭐ LA REGLE, TRANCHEE PAR FREDERIC LE 16/11/2026 :
#:
#:     « La date d'annulation dans le Sheet represente la date d'annulation
#:       du COMPROMIS. »
#:
#: ⛔⛔ ELLE REFAIT TOUT LE TRI, PAS SEULEMENT LES CAS AMBIGUS. Ma premiere
#:   version acceptait pour cible « toute transaction morte » -- compromis
#:   annule OU offre refusee. Avec sa regle, une ligne dont la seule cible est
#:   une OFFRE n'a pas de cible du tout : poser sur elle une date d'annulation
#:   de compromis serait ecrire une chose fausse. Les 446 « ambigues » cessent
#:   d'etre ambigues (elles portaient compromis+offre : c'est le compromis), et
#:   une partie des 252 « nettes » cesse d'etre posable.
CIBLE = ("compromis", "cancelled")


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


def par_lots(cl, table, select, colonne, valeurs, citer=False):
    out, valeurs = [], sorted(set(valeurs))
    for i in range(0, len(valeurs), LOT_API):
        lot = valeurs[i:i + LOT_API]
        rendu = ",".join(('"%s"' % v) if citer else str(v) for v in lot)
        out.extend(cl.get(table, {"select": select, colonne: "in.(%s)" % rendu}) or [])
    return out


def index_de(lettre: str) -> int:
    """« F » -> 5, « AA » -> 26. Zero-base, comme la liste rendue par le Sheet."""
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def jour_vrai(t: dict) -> date | None:
    """⭐⭐⭐ LE JOUR REEL D'UNE TRANSACTION -- et surtout PAS sa colonne `date`.

    ⛔⛔ LE DEFAUT QUE CETTE FONCTION REPARE, trouve le 16/11 DANS CE SCRIPT MEME.
      Ma premiere version comparait la date du classeur a `date`. Resultat : 131
      lignes rangees « date anterieure a la transaction », dont des temoins qui
      disaient « transaction 10/11/2026 mais annulee 24/06/2024 ». Absurde -- et
      c'est MOI qui avais tort : **pour une offre refusee, `date` EST la date du
      refus** (regle du 12/11), et le refus en question est NOTRE geste de masse
      du 11/11. Je comparais donc le classeur a notre propre ecriture.

    ⭐ LA REGLE DU PROJET, celle que six fonctions de la base appliquent deja
      (app_registre_dossiers, les deux pilotages, app_notaire_fiche,
      app_controle_date_offre, app_poser_etiquettes_dossier) : pour une OFFRE,
      le jour reel est sa PREMIERE PROPOSITION ; pour les autres, `date`.

    ⚠ ET UN PIEGE DANS CE SCRIPT MEME : `dates_des_propositions` rend du
      **jj/mm/aaaa**, et `sorted()` sur ces chaines ne trie PAS dans le temps
      (« 05/12/2020 » passe avant « 22/03/2019 »). On CONVERTIT d'abord, puis on
      prend le minimum -- jamais l'inverse.
    """
    if str(t.get("kind")) == "offre":
        jours = [ap._date_fr(j) for j in ap.dates_des_propositions(t.get("propositions_json"))]
        jours = [d for d in jours if d is not None]
        if jours:
            return min(jours)
    return notre_date(t.get("date"))


def notre_date(v) -> date | None:
    """NOS dates, en aaaa-mm-jj. ⛔ Le sens INVERSE de date_du_classeur_tolerante :
    les melanger donne un signal MUET qui passe pour un signal VERT (14/11)."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(v or "").strip())
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== C3 -- OU SE POSENT LES 896 DATES D'ANNULATION ? (lecture seule) ===")
    print()

    # ─── 1. LE SHEET ─────────────────────────────────────────────────────────
    # ⛔⛔ `lire_classeur` rend un TUPLE (entetes, lignes), et chaque ligne est un
    #   COUPLE (rang dans le Sheet, cellules) -- pas une grille. Ma premiere version
    #   la traitait comme une grille : elle a lu « 1 ligne de corps », rendu DES ZEROS
    #   PARTOUT, et SORTI EN CODE 0. Un zero ne se croit pas sans temoin positif, et
    #   une lecture ratee n'est jamais un vert : d'ou les deux gardes ci-dessous.
    entetes_bruts, lignes_du_sheet = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    corps = [cellules for _rang, cellules in lignes_du_sheet]

    #: GARDE 1 -- LA LECTURE A-T-ELLE VRAIMENT EU LIEU ? Le classeur porte
    #: 4 789 lignes (mesure du 16/11). Un plancher tres bas suffit a distinguer
    #: « lu » de « rate » sans se perimer a chaque ligne ajoutee.
    PLANCHER = 3000
    if len(corps) < PLANCHER:
        print("⛔ LECTURE RATEE : %d lignes de corps, moins du plancher de %d."
              % (len(corps), PLANCHER))
        print("   Le classeur en portait 4 789 le 16/11. ON NE CONCLUT RIEN.")
        return 2
    try:
        col_id = entetes.index("ID Unique")
    except ValueError:
        print("⛔ la colonne « ID Unique » est introuvable dans l'en-tete du Sheet.")
        print("   en-tetes lus : %s" % entetes[:12])
        return 2
    col_z = index_de("Z")
    print("le classeur : %d lignes de corps . « ID Unique » en colonne %d . Z en %d"
          % (len(corps), col_id, col_z))
    print("   l'en-tete de Z dit : %r" % (entetes[col_z] if col_z < len(entetes) else "?"))

    # ─── 2. LES LIGNES QUI PORTENT UNE DATE EN Z ─────────────────────────────
    du_classeur: dict[str, date] = {}
    illisibles, sans_id = 0, 0
    for l in corps:
        brut = l[col_z] if col_z < len(l) else ""
        if not str(brut or "").strip():
            continue
        d = date_du_classeur_tolerante(brut)
        if d is None:
            illisibles += 1
            continue
        ident = str(l[col_id] if col_id < len(l) else "").strip()
        if not ident:
            sans_id += 1
            continue
        du_classeur[ident] = d

    print()
    print("Z remplie et LISIBLE          : %4d  (A1 annoncait 896)" % (len(du_classeur) + sans_id))
    print("   dont SANS « ID Unique »    : %4d  <- injoignables, on ne devine pas" % sans_id)
    print("   retenues                   : %4d" % len(du_classeur))
    print("Z remplie mais ILLISIBLE      : %4d  <- doit valoir 0 (Z est propre)" % illisibles)

    #: GARDE 2 -- LE TEMOIN POSITIF. A1 a compte 896 dates en Z le 16/11. Si on en
    #: trouve une poignee, ce n'est pas « il n'y a rien a faire » : c'est que la
    #: colonne ou le format a change sous nos pieds.
    TEMOIN_Z = 700
    if len(du_classeur) + sans_id < TEMOIN_Z:
        print()
        print("⛔ TEMOIN POSITIF EN ECHEC : %d dates lues en Z, moins du seuil de %d."
              % (len(du_classeur) + sans_id, TEMOIN_Z))
        print("   A1 en comptait 896 le 16/11. La colonne ou le format a bouge.")
        print("   ON NE CONCLUT RIEN -- un zero ne se croit pas sans temoin positif.")
        return 2
    print()
    distinctes = len(set(du_classeur.values()))
    print("⚠ LE SIGNAL DE A1, MESURE : %d dates pour %d lignes = %.1f lignes par date"
          % (distinctes, len(du_classeur), len(du_classeur) / max(distinctes, 1)))
    gros = Counter(du_classeur.values()).most_common(5)
    for d, n in gros:
        print("      %s  %4d lignes" % (d.strftime("%d/%m/%Y"), n))
    print("   ⭐ a juger : des annulations GROUPEES sont plausibles (une relance, une")
    print("      cloture de periode) ; un copier-coller massif ne le serait pas.")

    # ─── 3. LE GEL : quelle transaction chaque ligne designe-t-elle ? ────────
    cl = client()
    liens = par_lots(cl, "app_classeur_lien", "id_unique,app_affaire_id,role,confiance",
                     "id_unique", list(du_classeur), citer=True)
    par_id: dict[str, list[dict]] = {}
    for r in liens:
        par_id.setdefault(str(r["id_unique"]), []).append(r)
    print()
    print("liens trouves dans le gel     : %4d pour %4d lignes du classeur"
          % (len(liens), len(par_id)))
    print("lignes SANS AUCUN lien        : %4d  <- hors de portee de C3"
          % (len(du_classeur) - len(par_id)))

    rows = par_lots(cl, "app_affaire_ledger",
                    "app_affaire_id,hektor_annonce_id,app_chaine_id,kind,state,date,"
                    "date_annulation_app,transaction_origine,propositions_json",
                    "app_affaire_id", [r["app_affaire_id"] for r in liens])
    ledger = {str(r["app_affaire_id"]): r for r in rows}

    # ─── 4. LE TRI ───────────────────────────────────────────────────────────
    nettes, plusieurs, deja_datee, futures = [], [], [], []
    anterieures, compromis_autre_etat, offre_seule, rien_du_tout = [], [], [], []
    etats_compromis = Counter()
    for ident, d in sorted(du_classeur.items()):
        vues = []
        for lien in par_id.get(ident, []):
            t = ledger.get(str(lien["app_affaire_id"]))
            if t:
                vues.append(t)
        cibles = [t for t in vues
                  if (str(t.get("kind")), str(t.get("state") or "")) == CIBLE]
        autres_compromis = [t for t in vues if str(t.get("kind")) == "compromis"
                            and t not in cibles]
        for t in vues:
            if str(t.get("kind")) == "compromis":
                etats_compromis[str(t.get("state") or "(vide)")] += 1

        if not cibles:
            # ⭐ ON DIT POURQUOI, au lieu d'un seul tas « aucune cible ».
            if autres_compromis:
                compromis_autre_etat.append((ident, d, autres_compromis))
            elif any(str(t.get("kind")) == "offre" for t in vues):
                offre_seule.append((ident, d, vues))
            else:
                rien_du_tout.append((ident, d))
            continue
        a_jour = [t for t in cibles if str(t.get("date_annulation_app") or "").strip()]
        if a_jour:
            deja_datee.append((ident, d, a_jour))
            continue
        if len(cibles) > 1:
            plusieurs.append((ident, d, cibles))
            continue
        t = cibles[0]
        # ⭐ LES DEUX TEMOINS DE JUSTESSE, avant toute pose.
        if d > AUJOURD_HUI:
            futures.append((ident, d, t))
            continue
        dt = jour_vrai(t)
        if dt is not None and d < dt:
            anterieures.append((ident, d, t, dt))
            continue
        nettes.append((ident, d, t))
    # noms repris par l'affichage plus bas
    incoherentes = anterieures
    aucune_morte = [(i, d) for i, d, _c in compromis_autre_etat] \
        + [(i, d) for i, d, _c in offre_seule] + rien_du_tout

    print()
    print("=== LE TRI, LIGNE PAR LIGNE ===")
    print()
    print("LA REGLE APPLIQUEE : la cible est un COMPROMIS `cancelled`, et rien d'autre")
    print("   (Frederic, 16/11 : « la date d'annulation du Sheet represente la date")
    print("    d'annulation du COMPROMIS »)")
    print()
    print("✅ UN SEUL compromis annule, posable : %4d" % len(nettes))
    print("⚠  PLUSIEURS compromis annules       : %4d  <- on ne choisit pas a sa place" % len(plusieurs))
    print("⚠  un compromis, mais PAS annule     : %4d  <- le classeur dit annule, nous non" % len(compromis_autre_etat))
    print("⚠  AUCUN compromis, seulement une offre : %4d  <- hors de sa regle" % len(offre_seule))
    print("·  aucune transaction du tout        : %4d" % len(rien_du_tout))
    print("·  DEJA datee chez nous              : %4d  <- rien a faire (doit valoir 0)" % len(deja_datee))
    print("⛔ DATE ANTERIEURE au jour vrai       : %4d" % len(incoherentes))
    print("⛔ DATE DANS LE FUTUR                : %4d  <- jamais posee" % len(futures))
    print()
    print("   les etats des compromis rencontres : %s" % dict(etats_compromis))
    total = (len(nettes) + len(plusieurs) + len(compromis_autre_etat) + len(offre_seule)
             + len(rien_du_tout) + len(deja_datee) + len(incoherentes) + len(futures))
    print()
    print("partition : %d = %d (doit boucler sur les lignes retenues)"
          % (total, len(du_classeur)))
    if total != len(du_classeur):
        print("⛔ LA PARTITION NE BOUCLE PAS -- un cas m'echappe, ne rien poser.")

    if nettes:
        print()
        print("=== LES CINQ PREMIERES CIBLES NETTES ===")
        print("   annonce  type       date transaction  -> annulee le")
        for ident, d, t in nettes[:5]:
            print("   %-8s %-10s %-16s -> %s   (%s)"
                  % (t.get("hektor_annonce_id"), t.get("kind"),
                     t.get("date") or "(vide)", d.strftime("%d/%m/%Y"), ident))

    if incoherentes:
        print()
        print("=== ⛔ LES INCOHERENTES -- a regarder, jamais a poser ===")
        print("   (comparees au JOUR VRAI, pas a `date` : voir jour_vrai())")
        for ident, d, t, dt in incoherentes[:8]:
            print("   %-8s %-10s jour vrai %s  mais annulee %s   (%s)"
                  % (t.get("hektor_annonce_id"), t.get("kind"),
                     dt.strftime("%d/%m/%Y"), d.strftime("%d/%m/%Y"), ident))

    # ─── DE QUOI SONT FAITES LES « PLUSIEURS CIBLES » ? ──────────────────────
    if plusieurs:
        print()
        print("=== ⚠ LES %d LIGNES A PLUSIEURS CIBLES MORTES -- DE QUOI SONT-ELLES FAITES ? ===" % len(plusieurs))
        formes = Counter()
        une_chaine = 0
        for _ident, _d, cibles in plusieurs:
            formes["+".join(sorted("%s/%s" % (t.get("kind"), t.get("state")) for t in cibles))] += 1
            if len({t.get("app_chaine_id") for t in cibles}) == 1:
                une_chaine += 1
        for forme, n in formes.most_common(8):
            print("   %-60s %4d" % (forme, n))
        print()
        print("   dont TOUTES LES CIBLES DANS UNE SEULE CHAINE : %d sur %d"
              % (une_chaine, len(plusieurs)))
        print("   ⭐ si c'est la quasi-totalite, une regle simple suffit (« la DERNIERE")
        print("      morte de la chaine porte l'annulation ») -- mais c'est une DECISION,")
        print("      pas un calcul : je ne la prends pas seul.")

    # ─── 5. L'ANNEE DES CIBLES NETTES ────────────────────────────────────────
    if nettes:
        print()
        print("=== L'ANNEE DES %d CIBLES NETTES ===" % len(nettes))
        for an, n in sorted(Counter(d.year for _, d, _ in nettes).items()):
            print("   %s  %4d" % (an, n))

    # ─── 6. LE FICHIER ───────────────────────────────────────────────────────
    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "verdict", "id_unique", "date_annulation_classeur", "app_affaire_id",
            "annonce", "chaine", "type", "etat", "date_transaction",
            "date_annulation_deja", "origine"])
        w.writeheader()

        def ecrire(verdict, ident, d, t):
            w.writerow({"verdict": verdict, "id_unique": ident,
                        "date_annulation_classeur": d.strftime("%Y-%m-%d"),
                        "app_affaire_id": (t or {}).get("app_affaire_id", ""),
                        "annonce": (t or {}).get("hektor_annonce_id", ""),
                        "chaine": (t or {}).get("app_chaine_id", ""),
                        "type": (t or {}).get("kind", ""),
                        "etat": (t or {}).get("state", ""),
                        "date_transaction": (t or {}).get("date", ""),
                        "date_annulation_deja": (t or {}).get("date_annulation_app", ""),
                        "origine": (t or {}).get("transaction_origine", "")})

        for ident, d, t in nettes:
            ecrire("nette", ident, d, t)
        for ident, d, cibles in plusieurs:
            for t in cibles:
                ecrire("plusieurs_cibles", ident, d, t)
        for ident, d, cs in compromis_autre_etat:
            for t in cs:
                ecrire("compromis_pas_annule", ident, d, t)
        for ident, d, vs in offre_seule:
            for t in vs:
                ecrire("offre_seule_pas_de_compromis", ident, d, t)
        for ident, d in rien_du_tout:
            ecrire("aucune_transaction", ident, d, None)
        for ident, d, a_jour in deja_datee:
            for t in a_jour:
                ecrire("deja_datee", ident, d, t)
        for ident, d, t, _dt in incoherentes:
            ecrire("date_anterieure", ident, d, t)
        for ident, d, t in futures:
            ecrire("date_future", ident, d, t)

    print()
    print("ecrit : %s" % SORTIE)
    print()
    print("⛔ RIEN N'A ETE ECRIT EN BASE. Le patch, s'il doit exister, sera genere")
    print("   a part, et il attendra un « go ».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
