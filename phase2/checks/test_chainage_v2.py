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
import re
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

# ─── LES REFERENCES DE COMPTE ──────────────────────────────────────────────────
#
# ⛔⛔ REETALONNEES LE 12/11/2026, ET VOILA POURQUOI. Les references d'origine
#   venaient de la simulation du 20/10 (12 702 / 12 278 / 12 159 / 12 149) avec une
#   tolerance de 30, pensee pour la croissance du parc (+1 a 15 affaires/mois).
#   Depuis, QUATRE REGLES ONT ETE ALLUMEES -- A (compromis annule seul), B (offre
#   acceptee 0-31 j), C (vente seule) et D (meme acheteur, 12/11) -- et elles ont
#   REUNI 727 dossiers. L'ecart etait donc de ~700, pas de 30 : l'essai criait
#   ROUGE a chaque passage depuis, et son rouge ne disait rien du code.
#
# ⚠⚠ CES NOMBRES DEPENDENT DES REGLES ALLUMEES, PAS SEULEMENT DU PARC. Si l'une
#   des quatre est eteinte, ils remontent. C'est pour ca qu'ils portent desormais
#   LA LISTE des regles sous lesquelles ils ont ete mesures.
#
#   Mesures le 12/11/2026 avec, dans `.env` : V2=1, SANS_DATE=2, OFFRE_PROPOSEE=1,
#   OFFRE_SANS_DATE=1, VENTE_SEULE=1, OFFRE_ACCEPTEE_SEULE=1,
#   COMPROMIS_ANNULE_SEUL=1, MEME_ACHETEUR=1, RATTACHEMENT_MANUEL=1 (6 lignes).
ATTENDU_V1_CHAINES = 11485      # V2 eteinte, les autres regles telles qu'au .env
ATTENDU_V2_CHAINES = 11438      # V2 allumee, cran 0
ATTENDU_26_CHAINES = 11438      # V2 + § 2.6, cran 1 (les compromis ANNULES)
ATTENDU_27_CHAINES = 11428      # V2 + § 2.7, cran 2 (+ les compromis ACTIFS)
TOLERANCE = 30          # le parc grandit chaque nuit (+1 a 15 affaires/mois)

# ⭐⭐ ET CE QUI NE PERIMERA JAMAIS, LUI : LES RELATIONS ENTRE LES COMPTES.
#   Un nombre absolu se demode des qu'une regle change ou que le parc grossit.
#   Une RELATION, elle, reste vraie : une regle qui REUNIT ne peut pas AUGMENTER
#   le nombre de dossiers. C'est ca qu'un essai doit juger.
#   ⚠ On garde les nombres absolus quand meme -- ils disent l'ampleur, et un ecart
#     de 700 merite d'etre vu -- mais ils ne sont plus les SEULS juges.
RELATIONS = (
    ("V2 allumee ne peut pas creer de dossiers",
     lambda v1, v2, c1, c2: v2 <= v1),
    ("le cran 1 des sans-date ne peut pas creer de dossiers",
     lambda v1, v2, c1, c2: c1 <= v2),
    ("le cran 2 ne peut pas creer de dossiers par rapport au cran 1",
     lambda v1, v2, c1, c2: c2 <= c1),
)

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


# ═══════════════════════════════════════════════════════════════════════════════
# LE SOCLE CONNU DE CET INVARIANT -- mesure et explique le 12/11/2026
# ═══════════════════════════════════════════════════════════════════════════════
# L'invariant « un bloc DATE APRES la vente » annonce 11 chaines, ETEINT COMME
# ALLUME. Il se presentait comme « ce qui ne doit JAMAIS arriver » : il criait donc
# ROUGE a chaque passage, depuis des semaines -- et cet essai avec lui.
#
# CE QUE LA MESURE DU 12/11 A ETABLI, et ce ne sont pas des defauts du chainage :
#     dossiers portant une vente                             9 280
#     dont une transaction est datee APRES la vente              11
#   En les regardant un par un : dans la moitie des cas l'ordre
#   compromis -> vente est CORRECT, et c'est l'OFFRE qui est datee apres, parce
#   qu'elle a ete SAISIE APRES COUP pour completer le dossier. Exemples releves :
#   bien 48031 (compromis 19/01/2022, vente 12/04, offre 17/12) et bien 18988
#   (compromis 02/02/2024, vente 18/03, offre 02/05).
#
# UN ESSAI QUI CRIE TOUS LES JOURS N'EST PLUS UN ESSAI. Le jour ou ce nombre MONTE,
# il faut le voir -- et on ne le verra pas si le rouge est permanent. On tolere donc
# le socle MESURE, et on crie DES QU'IL BOUGE, dans les deux sens :
#     plus haut -> une saisie tardive de plus, ou un vrai defaut : on regarde
#     plus bas  -> tant mieux, et on le dit pour que le socle soit abaisse ici
#
# CE N'EST PAS FERMER LES YEUX : le nombre reste AFFICHE a chaque passage, et
# l'ecart au socle est le seul juge. Meme patron que le seuil des fusions de B4.
SOCLE_BLOC_APRES_LA_VENTE = 11
LIBELLE_BLOC_APRES = "un bloc DATE APRES la vente qui ferme la chaine"


def defauts_hors_socle(defauts: dict[str, int]) -> dict[str, int]:
    """Les defauts a CRIER : tout, sauf le socle connu tant qu'il ne bouge pas."""
    reste = dict(defauts or {})
    vu = reste.pop(LIBELLE_BLOC_APRES, 0)
    if vu != SOCLE_BLOC_APRES_LA_VENTE:
        reste["%s (socle %d, vu %d -- IL A BOUGE)"
              % (LIBELLE_BLOC_APRES, SOCLE_BLOC_APRES_LA_VENTE, vu)] = vu
    return reste


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
    #   ⭐ 12/11 : on AFFICHE tout, et on ne CRIE que ce qui sort du socle connu.
    print(f"   invariants mesures       : {defauts or 'aucun defaut'}")
    hors_socle = defauts_hors_socle(defauts)
    if hors_socle:
        for k, v in hors_socle.items():
            rouges.append(f"INVARIANT : {k} ({v})")
    else:
        print(f"   ✅ invariants : rien hors du socle connu "
              f"({LIBELLE_BLOC_APRES} = {SOCLE_BLOC_APRES_LA_VENTE}, explique le 12/11)")

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
    comptes: list[int] = []
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
        # ⭐ 12/11 : on releve le compte de chaque sens pour juger LES RELATIONS.
        #   Les quatre sens tournent dans des processus separes (l'environnement se
        #   pose AVANT le lancement) : le parent ne peut les comparer qu'ici.
        trouve = re.search(r"chaines\s+:\s+(\d+)", r.stdout)
        comptes.append(int(trouve.group(1)) if trouve else -1)

    # ═══════════════════════════════════════════════════════════════════════════
    # ⭐⭐ LES RELATIONS -- le seul juge qui ne se demode pas
    # ═══════════════════════════════════════════════════════════════════════════
    # Un compte ABSOLU se demode des qu'une regle change ou que le parc grossit :
    # c'est ce qui a fait crier cet essai pendant des semaines (references du 20/10
    # contre une base ou 4 regles avaient depuis reuni 727 dossiers).
    # Une RELATION, elle, reste vraie : une regle qui REUNIT ne peut pas AUGMENTER
    # le nombre de dossiers. On les juge donc apres les quatre sens.
    print("")
    print("=" * 72)
    print("  LES RELATIONS ENTRE LES QUATRE SENS")
    print("=" * 72)
    if len(comptes) == 4 and all(n >= 0 for n in comptes):
        v1, v2, c1, c2 = comptes
        print(f"   V2 eteinte {v1} . V2 {v2} . cran 1 {c1} . cran 2 {c2}")
        for libelle, juge in RELATIONS:
            bon = juge(v1, v2, c1, c2)
            print(("   OK   " if bon else "   ⛔   ") + libelle)
            if not bon:
                total = max(total, 1)
    else:
        # ⛔ UNE LECTURE RATEE N'EST PAS UN VERT : si on n'a pas pu relever les
        #   quatre comptes, on le DIT et on sort en rouge.
        print(f"   ⛔ comptes releves : {comptes} -- impossible de juger les "
              f"relations. On ne conclut pas.")
        total = max(total, 1)
    print(f"\n{'=' * 72}")
    print("  LES QUATRE SENS : " + ("✅ VERTS" if total == 0 else "⛔ UN ROUGE"))
    print("=" * 72)
    return total


if __name__ == "__main__":
    raise SystemExit(main())
