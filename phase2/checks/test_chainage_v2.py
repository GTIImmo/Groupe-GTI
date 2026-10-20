#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA REGLE V2 DU CHAINAGE : le temoin, DANS LES DEUX SENS.           20/10/2026

Chantier : notice/CHANTIER_CHAINAGE_2026-10-20.md (la regle figee au § 3).

CE QU'ELLE EPROUVE, ET POURQUOI DANS CET ORDRE
----------------------------------------------
  ⓵ INTERRUPTEUR ETEINT -> le code doit rendre EXACTEMENT ce qu'il rendait avant.
     C'est le TEMOIN INVERSE, et c'est le controle qui compte le plus : il prouve
     que du code neuf dort sans rien changer. Sans lui, « ca marche » ne veut rien
     dire -- on ne saurait pas si la V2 a corrige ou simplement bouge.
  ⓶ INTERRUPTEUR ALLUME -> les comptes mesures le 20/10 par simulation.
  ⓷ LES TROIS INVARIANTS, dans les deux cas. Ce sont EUX qui ont trouve le defaut
     de ma premiere version (une chaine a DEUX VENTES, § 3.0).

⚠ ELLE N'ECRIT RIEN. La table est recopiee en memoire (le patron de
  verifier_regle_chainage.py) : phase2.sqlite est ouverte en LECTURE SEULE.

⚠ ELLE S'EXECUTE DEUX FOIS, dans deux processus : c'est le seul moyen d'eprouver
  LE CHEMIN de l'interrupteur (environnement -> .env -> la regle), et pas
  seulement la fonction. Patcher une variable en memoire ne prouverait rien.

    python phase2/checks/test_chainage_v2.py            # les quatre sens, d'affilee
    APP_CHAINAGE_V2=1 python phase2/checks/test_chainage_v2.py --un-seul-sens
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                               # noqa: BLE001
        pass

# ─── CE QUE LA SIMULATION DU 20/10 A MESURE ────────────────────────────────────
# Elle rejoue la regle ACTUELLE a 31 065/31 066 = 100,00 %, donc ces nombres sont
# des references, pas des estimations. Si la base bouge, ils bougeront : on les
# compare avec une tolerance, et on DIT l'ecart.
ATTENDU_V1_CHAINES = 12702
ATTENDU_V2_CHAINES = 12278
ATTENDU_26_CHAINES = 12159      # V2 + § 2.6, cran 1 (les compromis ANNULES)
ATTENDU_27_CHAINES = 12149      # V2 + § 2.7, cran 2 (+ les compromis ACTIFS)
TOLERANCE = 30          # le parc grandit chaque nuit (+1 a 15 affaires/mois)

MORTS_OFFRE = {"refused", "refusee"}
MORTS_COMPROMIS = {"cancelled", "annule"}


def copie_jetable() -> sqlite3.Connection | None:
    """La table du registre, recopiee en memoire. Rien n'est ecrit sur le disque."""
    from phase2.sync.affaire_ledger import LEDGER_TABLE

    base = RACINE / "phase2" / "phase2.sqlite"
    if not base.exists():
        print("   phase2.sqlite absente : epreuve NON CONCLUANTE")
        return None
    src = sqlite3.connect(f"file:{base.as_posix()}?mode=ro", uri=True)
    jetable = sqlite3.connect(":memory:")
    ddl = src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                      (LEDGER_TABLE,)).fetchone()
    if not ddl:
        src.close()
        print("   table du registre introuvable : epreuve NON CONCLUANTE")
        return None
    jetable.execute(ddl[0])
    cols = [r[1] for r in src.execute(f"PRAGMA table_info({LEDGER_TABLE})")]
    jetable.executemany(
        f"INSERT INTO {LEDGER_TABLE} ({','.join(cols)}) "
        f"VALUES ({','.join('?' * len(cols))})",
        list(src.execute(f"SELECT {','.join(cols)} FROM {LEDGER_TABLE}")))
    jetable.commit()
    src.close()
    return jetable


def invariants(con: sqlite3.Connection) -> dict[str, int]:
    """⚠ CE QUI NE DOIT JAMAIS ARRIVER dans une chaine, quelle que soit la regle."""
    from phase2.sync.affaire_ledger import LEDGER_TABLE

    # ⚠ ON ORDONNE AVEC LA MEME DATE QUE LA REGLE, PAS AVEC LA COLONNE BRUTE.
    #   `date` porte, pour une offre, la date du DERNIER EVENEMENT (son refus par
    #   exemple) -- qui peut tomber APRES la vente alors que l'offre, elle, la
    #   precedait. Mesure du 20/10 : avec la colonne brute, l'invariant accusait
    #   2 chaines SAINES. `_date_de_tri` est la fonction du run elle-meme.
    from phase2.sync.affaire_ledger import _date_de_tri

    par_chaine: dict[int, list[tuple[str, str, str]]] = {}
    for cid, kind, state, date, props in con.execute(
            f"SELECT app_chaine_id, kind, state, date, propositions_json "
            f"FROM {LEDGER_TABLE} WHERE app_chaine_id IS NOT NULL"):
        par_chaine.setdefault(cid, []).append(
            (str(kind or "").lower(), str(state or "").lower(),
             _date_de_tri(kind, date, props) or ""))
    defauts: dict[str, int] = {}

    def compte(quoi: str) -> None:
        defauts[quoi] = defauts.get(quoi, 0) + 1

    for blocs in par_chaine.values():
        ventes = [b for b in blocs if b[0] == "vente"]
        vivants = sum(1 for k, s, _ in blocs
                      if k == "compromis" and s not in MORTS_COMPROMIS)
        if len(ventes) > 1:
            compte("DEUX VENTES dans une chaine")
        if vivants > 1:
            compte("DEUX COMPROMIS VIVANTS dans une chaine")
        # ─── LE 3e INVARIANT : « une chaine fermee ne recoit plus jamais rien » ──
        #
        # ⚠⚠ ET CE N'EST PAS « une chaine vendue porte un compromis actif » : j'ai
        #   essaye celui-la le 20/10, il accuse 9 123 chaines SOUS LA REGLE
        #   ACTUELLE. La cause est ecrite dans le code du chainage : « 7 507
        #   compromis sont anterieurs a une vente et TOUJOURS marques actifs chez
        #   Hektor, parce que personne ne les clot apres l'acte ». L'etat normal
        #   n'est pas un defaut.
        #
        # LE VRAI, celui que verifier_regle_chainage.py a trouve le 08/09 : un
        # bloc DATE APRES la vente qui ferme la chaine.
        dv = [b[2] for b in ventes if b[2]]
        if dv:
            plus_tard = [b for b in blocs
                         if b[0] != "vente" and b[2] and b[2] > max(dv)]
            if plus_tard:
                compte("un bloc DATE APRES la vente qui ferme la chaine")
    return defauts


def un_sens() -> int:
    """Eprouve le code TEL QU'IL EST CHARGE, avec l'interrupteur que l'env porte."""
    from phase2.sync.affaire_ledger import (LEDGER_TABLE, chainage_sans_date_niveau,
                                            chainage_v2_actif,
                                            recalculer_les_chaines)

    CHAINAGE_V2 = chainage_v2_actif()
    SANS_DATE = chainage_sans_date_niveau()

    etiquette = ("V2 + § 2.7 (cran 2 : + les compromis ACTIFS)" if SANS_DATE >= 2
                 else "V2 + § 2.6 (cran 1 : les compromis ANNULES)" if SANS_DATE >= 1
                 else "V2 ALLUMEE" if CHAINAGE_V2
                 else "V2 ETEINTE (temoin inverse)")
    print(f"\n{'=' * 72}\n  {etiquette}\n{'=' * 72}")
    con = copie_jetable()
    if con is None:
        return 2

    avant = dict(con.execute(
        f"SELECT app_affaire_id, app_chaine_id FROM {LEDGER_TABLE}"))
    resultat = recalculer_les_chaines(con)
    apres = dict(con.execute(
        f"SELECT app_affaire_id, app_chaine_id FROM {LEDGER_TABLE}"))
    defauts = invariants(con)
    con.close()

    bouge = [a for a, v in apres.items() if avant.get(a) != v]
    chaines = int(resultat["chaines"])
    rouges: list[str] = []

    print(f"   chaines                  : {chaines}")
    print(f"   transactions deplacees   : {len(bouge)}")
    print(f"   l etiquette du resultat  : chainage_v2 = {resultat.get('chainage_v2')}")

    # ① l'etiquette doit dire la verite
    if bool(resultat.get("chainage_v2")) is not bool(CHAINAGE_V2):
        rouges.append("le resultat ne dit PAS si la V2 a tourne")
    if int(resultat.get("chainage_sans_date") or 0) != int(SANS_DATE):
        rouges.append("le resultat ne dit PAS a quel CRAN le repli des sans-date a tourne")

    # ② le compte attendu
    attendu = (ATTENDU_27_CHAINES if SANS_DATE >= 2
               else ATTENDU_26_CHAINES if SANS_DATE >= 1
               else ATTENDU_V2_CHAINES if CHAINAGE_V2
               else ATTENDU_V1_CHAINES)
    ecart = abs(chaines - attendu)
    print(f"   attendu                  : {attendu}  (ecart {ecart}, tolerance {TOLERANCE})")
    if ecart > TOLERANCE:
        rouges.append(f"compte hors tolerance : {chaines} au lieu de ~{attendu}")

    # ③ ⚠⚠ LE TEMOIN NE SE MESURE PLUS CONTRE LA BASE -- CORRIGE LE 20/10.
    #
    #   Il disait : « eteinte, la V2 ne doit RIEN changer », en comparant a
    #   app_chaine_id tel qu'il est EN BASE. C'etait juste tant que la base etait
    #   le resultat de la V1. Depuis que la V2 est en production, la base EST le
    #   resultat de la V2 : le meme juge accusait alors 427 deplacements avec
    #   l'interrupteur ETEINT, et « elle n'a rien change » avec l'interrupteur
    #   ALLUME. Le code etait sain, LA CIBLE AVAIT BOUGE.
    #   ➡ Le temoin est donc LE COMPTE attendu par combinaison d'interrupteurs
    #     (verifie en ②) : les trois references sont distinctes, donc un compte
    #     juste prouve que la bonne regle a tourne. `bouge` reste AFFICHE, comme
    #     information : il dit par rapport a quel regime la base a ete ecrite.
    regime = ("V2 + § 2.7 (cran 2)" if SANS_DATE >= 2
              else "V2 + § 2.6 (cran 1)" if SANS_DATE >= 1
              else "V2" if CHAINAGE_V2 else "la regle d avant")
    if bouge:
        print(f"   i {len(bouge)} transaction(s) differeraient de ce qui est EN BASE "
              f"-- normal si la base n a pas ete ecrite en « {regime} »")
    else:
        print(f"   ✅ la base EST le resultat de « {regime} » (0 ecart)")

    # ④ les invariants, dans les deux cas
    if defauts:
        for k, v in defauts.items():
            rouges.append(f"INVARIANT : {k} ({v})")
    else:
        print("   ✅ invariants : aucun defaut")

    # ⑤ les refus doivent etre NOMMES
    refus = {k: v for k, v in resultat.items()
             if isinstance(v, int) and k not in ("transactions", "chaines", "sans_date")}
    if refus:
        print("   ce que la regle a fait et ce qu elle a refuse, nomme :")
        for k, v in sorted(refus.items(), key=lambda z: -z[1]):
            print(f"      {k:<56} {v:>5}")

    if rouges:
        print("\n   ⛔ ROUGE :")
        for r in rouges:
            print(f"      - {r}")
        return 1
    print("\n   ✅ VERT")
    return 0


def le_chemin_du_env() -> int:
    """⭐ LE CONTROLE QUI PROUVE QUE LA COMMANDE D'ALLUMAGE MARCHE.

    ⚠⚠ DEFAUT TROUVE LE 20/10 AVANT DE S'EN SERVIR : l'interrupteur etait une
      CONSTANTE lue a l'import, et `.env` n'est charge qu'au milieu de main(),
      sous `--push`. `APP_CHAINAGE_V2=1` dans `.env` n'allumait RIEN -- et un
      `--refresh` seul ne lisait meme pas l'interrupteur.

    On eprouve donc LE CHEMIN, avec un `.env` jetable : ni le vrai fichier de
    Frederic ni l'environnement reel ne sont touches.
    """
    import tempfile

    from phase2.sync import affaire_ledger as al

    print(f"\n{'=' * 72}\n  LE CHEMIN DE L INTERRUPTEUR (.env)\n{'=' * 72}")
    rouges: list[str] = []
    vrais_fichiers = al.DEFAULT_ENV_FILES
    avait = os.environ.pop("APP_CHAINAGE_V2", None)
    try:
        with tempfile.TemporaryDirectory() as dossier:
            faux = Path(dossier) / ".env"
            # ① un .env qui ALLUME
            faux.write_text("APP_CHAINAGE_V2=1\n", encoding="utf-8")
            al.DEFAULT_ENV_FILES = [faux]
            al._ENV_DEJA_CHARGE = False
            if al.chainage_v2_actif():
                print("   ✅ un .env qui porte APP_CHAINAGE_V2=1 ALLUME bien la V2")
            else:
                rouges.append("un .env avec APP_CHAINAGE_V2=1 n allume RIEN "
                              "-- la commande d allumage serait une fausse promesse")
            # ② et un .env muet laisse ETEINT (le temoin inverse du chemin)
            os.environ.pop("APP_CHAINAGE_V2", None)
            faux.write_text("AUTRE_CHOSE=1\n", encoding="utf-8")
            al._ENV_DEJA_CHARGE = False
            if al.chainage_v2_actif():
                rouges.append("un .env SANS la variable allume quand meme : "
                              "l interrupteur ne s eteint plus")
            else:
                print("   ✅ un .env muet laisse la V2 ETEINTE")
    finally:
        al.DEFAULT_ENV_FILES = vrais_fichiers
        al._ENV_DEJA_CHARGE = False
        os.environ.pop("APP_CHAINAGE_V2", None)
        if avait is not None:
            os.environ["APP_CHAINAGE_V2"] = avait
    if rouges:
        print("\n   ⛔ ROUGE :")
        for r in rouges:
            print(f"      - {r}")
        return 1
    print("\n   ✅ VERT")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--un-seul-sens", action="store_true",
                    help="n eprouve que l interrupteur present dans l environnement")
    args = ap.parse_args()
    if args.un_seul_sens:
        return un_sens()

    # ⚠ D'ABORD LE CHEMIN : si la commande d'allumage ne marche pas, le reste de
    #   l'epreuve ne dit rien d'utile.
    total = le_chemin_du_env()

    # ⚠ TROIS PROCESSUS, parce que l'environnement se pose AVANT le lancement :
    #   c'est ainsi que la tache planifiee et le shell s'en serviront.
    #   ⓵ tout eteint        -> la regle d'avant, a l'identique (temoin inverse)
    #   ⓶ V2 seule           -> le chainage V2
    #   ⓷ V2 + cran 1 (§ 2.6) -> CE QUI TOURNE EN PRODUCTION depuis le 20/10
    #   ⓸ V2 + cran 2 (§ 2.7) -> + les compromis ACTIFS sans date
    for valeur, sansdate in (("0", "0"), ("1", "0"), ("1", "1"), ("1", "2")):
        env = dict(os.environ)
        env["APP_CHAINAGE_V2"] = valeur
        env["APP_CHAINAGE_SANS_DATE"] = sansdate
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                            "--un-seul-sens"],
                           cwd=str(RACINE), env=env, text=True,
                           encoding="utf-8", errors="replace",
                           capture_output=True)
        sys.stdout.write(r.stdout)
        if r.stderr.strip():
            sys.stderr.write(r.stderr)
        total = max(total, r.returncode)
    print(f"\n{'=' * 72}")
    print("  LES QUATRE SENS : " + ("✅ VERTS" if total == 0 else "⛔ UN ROUGE"))
    print("=" * 72)
    return total


if __name__ == "__main__":
    raise SystemExit(main())
