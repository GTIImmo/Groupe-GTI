"""Chantier classeur, ⑮ -- LES TEMOINS DE G2 ET DE L'OUTIL DE COUPE, sur une COPIE en memoire du registre local.

Lecture seule : la base phase2.sqlite est copiee en memoire (mode=ro) ; rien n'est ecrit nulle part ailleurs que dans
le cache du chantier (C:\\Hektor\\chantier_classeur_q6_cache) et, pour « fichier », dans
phase2/sync/detachements_manuels.csv (le fichier de Frederic, lu SEULEMENT si APP_CHAINAGE_DETACHEMENTS=1).
UN rejeu (ou deux) par appel, ecrit au fil de l'eau (lecon : jamais plus de 10 minutes d'un bloc).

  temoin   le module d'AVANT (git HEAD) et le module d'aujourd'hui, interrupteurs G2 et outil ETEINTS, rejouent la
           nuit de ce soir (les reglages de .env : E allumee, les rattachements du fichier) -> 0 transaction differente
  g2       le module d'aujourd'hui, G2 ALLUMEE contre ETEINTE : les transactions qui changent de dossier ; comparees a
           la mesure du 19/11 au soir (chaines_s3 -> chaines_g2 du cache)
  fichier  ecrit phase2/sync/detachements_manuels.csv depuis les 132 coupes datees VALIDEES (une ligne par morceau)
  outil    G2 ALLUMEE + l'outil ALLUME avec ce fichier : chaque morceau finit EXACTEMENT comme ecrit ; aucun dossier
           ne bouge hors des groupes nommes ; temoins inverses (un bien faux, une transaction inconnue -> refuses)

Usage : python -u phase2/checks/temps10_g2_et_l_outil_rejeu_2026-11-20.py temoin|g2|fichier|outil
"""
from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache")
BASE = RACINE / "phase2" / "phase2.sqlite"
MODULE = RACINE / "phase2" / "sync" / "affaire_ledger.py"
DECISION_132 = RACINE / "notice" / "TEMPS8_DECISION_DU_20_11_LES_132_COUPES_DATEES_VALIDEES_2026-11-20.csv"
FICHIER_DET = RACINE / "phase2" / "sync" / "detachements_manuels.csv"
JOURNAL = CACHE / "temps10_journal.txt"


def dire(s: str) -> None:
    ligne = "%s  %s" % (datetime.now().strftime("%H:%M:%S"), s)
    print(ligne, flush=True)
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def charger(chemin: Path, nom: str):
    """Charge un affaire_ledger.py comme un module a part, ses chemins ramenes au depot."""
    source = chemin.read_text(encoding="utf-8")
    for avant, apres in (("ROOT = Path(__file__).resolve().parents[2]", "ROOT = Path(%r)" % str(RACINE)),
                         ('FICHIER_RATTACHEMENTS = Path(__file__).resolve().parent / "rattachements_manuels.csv"',
                          "FICHIER_RATTACHEMENTS = Path(%r)" % str(RACINE / "phase2" / "sync" / "rattachements_manuels.csv")),
                         ('FICHIER_DETACHEMENTS = Path(__file__).resolve().parent / "detachements_manuels.csv"',
                          "FICHIER_DETACHEMENTS = Path(%r)" % str(FICHIER_DET))):
        if avant in source:
            source = source.replace(avant, apres)
    tmp = CACHE / ("_module_%s.py" % nom)
    tmp.write_text(source, encoding="utf-8")
    sys.path.insert(0, str(RACINE))
    spec = importlib.util.spec_from_file_location("al_" + nom, tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def copie() -> sqlite3.Connection:
    src = sqlite3.connect("file:%s?mode=ro" % BASE.as_posix(), uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def rejouer(mod, env: dict) -> tuple[dict, dict, sqlite3.Connection]:
    gardes = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        con = copie()
        with contextlib.redirect_stdout(io.StringIO()) as sortie:
            res = mod.recalculer_les_chaines(con)
        ch = {int(a): int(c) for a, c in con.execute("SELECT app_affaire_id, app_chaine_id FROM %s" % mod.LEDGER_TABLE)}
        res["_ligne"] = sortie.getvalue().strip().splitlines()[-1] if sortie.getvalue().strip() else ""
        return ch, res, con
    finally:
        for k, v in gardes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


ETEINTS = {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "0"}


def etape_temoin() -> int:
    t0 = time.time()
    dire("TEMOIN : le module d'avant (git HEAD) contre celui d'aujourd'hui, G2 et outil ETEINTS")
    texte = subprocess.run(["git", "-C", str(RACINE), "show", "HEAD:phase2/sync/affaire_ledger.py"],
                           capture_output=True, check=True).stdout.decode("utf-8")
    avant = CACHE / "_affaire_ledger_HEAD.py"
    avant.write_text(texte.replace("\r\n", "\n"), encoding="utf-8")
    m_avant, m_apres = charger(avant, "avant"), charger(MODULE, "apres")
    ch_a, res_a, _ = rejouer(m_avant, {})
    dire("   avant : %d dossiers (%.0f s) -- %s" % (len(set(ch_a.values())), time.time() - t0, res_a["_ligne"][:200]))
    ch_b, res_b, _ = rejouer(m_apres, ETEINTS)
    dire("   apres : %d dossiers (%.0f s) -- %s" % (len(set(ch_b.values())), time.time() - t0, res_b["_ligne"][:200]))
    ecarts = [a for a in set(ch_a) | set(ch_b) if ch_a.get(a) != ch_b.get(a)]
    meme_ligne = res_a["_ligne"] == res_b["_ligne"]
    dire("   ⭐ transactions dans un autre dossier : %d (attendu 0) ; la ligne du compte rendu identique : %s"
         % (len(ecarts), meme_ligne))
    (CACHE / "chaines_ce_soir_sans_g2.json").write_text(json.dumps({str(k): v for k, v in ch_b.items()}), encoding="utf-8")
    ok = not ecarts and meme_ligne
    dire("TEMOIN : %s (%.0f s)" % ("VERT" if ok else "⛔ ROUGE", time.time() - t0))
    return 0 if ok else 1


def etape_g2() -> int:
    t0 = time.time()
    dire("G2 : le module d'aujourd'hui, G2 ALLUMEE contre ETEINTE (la nuit de ce soir : E + les rattachements)")
    mod = charger(MODULE, "apres")
    ch_off, _, _ = rejouer(mod, ETEINTS)
    ch_on, res_on, _ = rejouer(mod, {"APP_CHAINAGE_GARDE_G2": "1", "APP_CHAINAGE_DETACHEMENTS": "0"})
    bouge = sorted(a for a in ch_off if ch_off[a] != ch_on.get(a))
    dire("   dossiers : %d -> %d ; transactions qui changent de dossier : %d ; passages bloques par G2 : %s"
         % (len(set(ch_off.values())), len(set(ch_on.values())), len(bouge),
            res_on.get("[G2] garde : l'offre acceptee datee est a un autre acheteur -- abstention", 0)))
    s3 = {int(a): c for a, c in json.loads((CACHE / "chaines_s3.json").read_text(encoding="utf-8")).items()}
    g2 = {int(a): c for a, c in json.loads((CACHE / "chaines_g2.json").read_text(encoding="utf-8")).items()}
    mesure = sorted(a for a in s3 if s3[a] != g2.get(a))
    commun = set(bouge) & set(mesure)
    dire("   la mesure du 19/11 (s3 -> g2) : %d transactions ; communes : %d ; seulement ce soir : %d %s ; seulement "
         "le 19/11 : %d %s" % (len(mesure), len(commun), len(set(bouge) - set(mesure)),
                                sorted(set(bouge) - set(mesure))[:12], len(set(mesure) - set(bouge)),
                                sorted(set(mesure) - set(bouge))[:12]))
    (CACHE / "chaines_ce_soir_avec_g2.json").write_text(json.dumps({str(k): v for k, v in ch_on.items()}), encoding="utf-8")
    dire("G2 : FIN (%.0f s) -- ⚠ la mesure du 19/11 portait aussi les 8 lignes de 5.6 ; ce soir non : un ecart vient de la"
         % (time.time() - t0))
    return 0


def morceaux_d_une_coupe(texte: str) -> list[tuple[list[int], str]]:
    """« 7778 comp(active)+7780 offr(refuse)+7782 vent -> 2SCBZXMH OLIVEIRA | 7779 ... -> VEP1DVQ4 COLOMBET || ... »"""
    sorties = []
    for part in texte.split("||")[0].split(" | "):
        if "->" not in part:
            continue                                # DISPUTEES / SANS LIGNE / C5 : jamais dans un morceau
        gauche, droite = part.split("->", 1)
        ids = [int(x) for x in re.findall(r"(\d+) (?:comp|offr|vent)", gauche)]
        if ids:
            sorties.append((ids, droite.strip().split()[0]))
    return sorties


def etape_fichier() -> int:
    with DECISION_132.open(encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))
    coupes = {}
    for r in lignes:
        coupes.setdefault(r["numero_de_coupe"], r["la_coupe"])
    dire("FICHIER : %d coupes validees (attendu 132)" % len(coupes))
    if len(coupes) != 132:
        return 1
    con = sqlite3.connect("file:%s?mode=ro" % BASE.as_posix(), uri=True)
    sortie = ["# LES DETACHEMENTS DECIDES A LA MAIN -- lu par affaire_ledger.recalculer_les_chaines SEULEMENT si",
              "# APP_CHAINAGE_DETACHEMENTS=1 (eteint par defaut). Une ligne = UN MORCEAU = une affaire : ses transactions",
              "# deviennent un dossier a elles seules. Genere le %s par phase2/checks/temps10_g2_et_l_outil_rejeu_2026-11-20.py"
              % datetime.now().strftime("%d/%m/%Y %H:%M"),
              "# depuis les 132 coupes datees VALIDEES par Frederic le 20/11 (« LES 132 COUPES DATEES : OUI »).",
              "transactions;bien;geste;pourquoi"]
    refus = []
    n = 0
    for num, texte in sorted(coupes.items(), key=lambda kv: int(kv[0])):
        morceaux = morceaux_d_une_coupe(texte)
        tous = [a for ids, _ in morceaux for a in ids]
        biens = {r[0] for r in con.execute("SELECT DISTINCT hektor_annonce_id FROM app_affaire_ledger WHERE app_affaire_id IN (%s)"
                                            % ",".join(map(str, tous)))}
        if len(biens) != 1 or len(tous) != len(set(tous)):
            refus.append((num, biens, texte[:120]))
            continue
        bien = next(iter(biens))
        for ids, ligne in morceaux:
            sortie.append("%s;%s;coupe_132_n%s;%s -- coupe datee validee le 20/11" % (" ".join(map(str, sorted(ids))), bien, num, ligne))
            n += 1
    FICHIER_DET.write_text("\n".join(sortie) + "\n", encoding="utf-8")
    dire("FICHIER : %s -- %d morceaux ; coupes refusees a la fabrication : %d %s" % (FICHIER_DET.name, n, len(refus), refus[:3]))
    return 0 if not refus else 1


def etape_outil() -> int:
    t0 = time.time()
    dire("OUTIL : G2 + l'outil ALLUMES avec %s, contre G2 seule" % FICHIER_DET.name)
    mod = charger(MODULE, "apres")
    ch_g2, _, _ = rejouer(mod, {"APP_CHAINAGE_GARDE_G2": "1", "APP_CHAINAGE_DETACHEMENTS": "0"})
    ch, res, _ = rejouer(mod, {"APP_CHAINAGE_GARDE_G2": "1", "APP_CHAINAGE_DETACHEMENTS": "1"})
    det = mod.lire_detachements_manuels()
    dire("   morceaux lus : %d ; compte rendu : %s" % (len(det), {k: v for k, v in res.items() if str(k).startswith("[X]")}))
    par_chaine = defaultdict(set)
    for a, c in ch.items():
        par_chaine[c].add(a)
    exacts, faux = 0, []
    for ids, bien, geste, _p in det:
        cs = {ch.get(a) for a in ids}
        if len(cs) == 1 and par_chaine[next(iter(cs))] == set(ids):
            exacts += 1
        else:
            faux.append((geste, sorted(ids), sorted(cs)))
    dire("   ⭐ morceaux qui finissent EXACTEMENT comme ecrits : %d sur %d ; autrement : %d %s"
         % (exacts, len(det), len(faux), faux[:5]))
    nommes = {a for ids, *_ in det for a in ids}
    groupes_g2 = defaultdict(set)
    for a, c in ch_g2.items():
        groupes_g2[c].add(a)
    touches = set()
    for a in nommes:
        touches |= groupes_g2.get(ch_g2.get(a), set())
    hors = sorted(a for a in ch if ch[a] != ch_g2.get(a) and a not in touches)
    bouge = sorted(a for a in ch if ch[a] != ch_g2.get(a))
    dire("   transactions qui changent de dossier par l'outil : %d ; HORS des dossiers nommes : %d (attendu 0) %s"
         % (len(bouge), len(hors), hors[:10]))
    # temoins inverses : un bien faux, une transaction inconnue
    sauve = FICHIER_DET.read_text(encoding="utf-8")
    try:
        # trois lignes semees, chacune pour UN refus : un bien qui n'existe pas ; une transaction inconnue sur un
        # vrai bien ; une transaction deja coupee par une autre ligne (la ligne semee vient APRES)
        nommees = {a for ids, *_ in det for a in ids}
        libre = next(a for a in ch if a not in nommees)
        FICHIER_DET.write_text(sauve + "%d;999999999;temoin_bien_inconnu;-\n9999999;%s;temoin_transaction_inconnue;-\n"
                               "%d %d;%s;temoin_deux_lignes;-\n"
                               % (libre, det[0][1], min(det[0][0]), libre, det[0][1]), encoding="utf-8")
        _, res_t, _ = rejouer(mod, {"APP_CHAINAGE_GARDE_G2": "1", "APP_CHAINAGE_DETACHEMENTS": "1"})
    finally:
        FICHIER_DET.write_text(sauve, encoding="utf-8")
    vus = {k: v for k, v in res_t.items() if str(k).startswith("[X]")}
    attendus = {"[X] detachement : bien inconnu -- la ligne n'est jamais lue": 1,
                "[X] detachement : transaction introuvable -- le morceau est ignore": 1,
                "[X] detachement : une transaction dans deux lignes -- la seconde est ignoree": 1}
    inverse_ok = all(vus.get(k, 0) == v for k, v in attendus.items()) and \
        vus.get("[X] detachement decide a la main", 0) == res.get("[X] detachement decide a la main", 0)
    dire("   TEMOINS INVERSES (3 lignes semees) : %s -> %s" % (vus, "VUS, chacun une fois" if inverse_ok else "⛔ PAS VUS"))
    (CACHE / "chaines_ce_soir_avec_g2_et_outil.json").write_text(json.dumps({str(k): v for k, v in ch.items()}), encoding="utf-8")
    ok = not faux and not hors and inverse_ok
    dire("OUTIL : %s (%.0f s) ; dossiers %d (G2 seule) -> %d (G2 + outil)"
         % ("VERT" if ok else "⛔ ROUGE", time.time() - t0, len(set(ch_g2.values())), len(set(ch.values()))))
    return 0 if ok else 1


if __name__ == "__main__":
    etape = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"temoin": etape_temoin, "g2": etape_g2, "fichier": etape_fichier, "outil": etape_outil}.get(
        etape, lambda: (print(__doc__), 3)[1])())
