# -*- coding: utf-8 -*-
"""A.3 — CE QUE NOUS SAVONS QUAND HEKTOR SE TAIT.              15/10/2026

Remplit `nature_app` / `type_app` / `source_app` de `app_mandat` a partir des
SOURCES LEGALES fournies par Frederic. N'ecrit JAMAIS `nature` ni `type`.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI CE SCRIPT EXISTE
═══════════════════════════════════════════════════════════════════════════════
Mesure du 15/10 : **2 902 mandats (10 % du registre) n'ont AUCUN type chez
Hektor**. Tous sont anciens (2009-2024), **tous echus**, et Hektor ne les
remplira jamais -- le robinet s'est ferme en 2025, quand il est passe au libelle
complet. Sans type, `_nature()` ne peut rien affirmer : elle dit INCONNUE, et
c'est la bonne reponse (regle du 29/09 : « on ne devine pas »).

    521 lignes INCONNUE  ·  503 numeros distincts  ·  521/521 ECHUES

Mais l'information existe ailleurs -- dans les sources que Frederic a sorties :

    les deux exports Modelo   un CODE `mandate_type` (1 vente · 2 loc/gestion · 3 recherche)
                              et `exclusivity` (1 EXCLUSIF · 3 ACCORD · 5 SIMPLE)
    le registre LEGAL certifie   la colonne « Objet du mandat », en toutes lettres

⭐ ET NOTRE PROPRE BASE CONFIRME, PAR UN SECOND CHEMIN : 509 des 521 lignes
  portent sur une annonce dont `offre_type` vaut « vente ». Deux sources qui ne
  se connaissent pas disent la meme chose. C'est ce croisement qui autorise
  l'ecriture -- pas la confiance dans un fichier.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI PAS UN SIMPLE UPDATE DE `nature`
═══════════════════════════════════════════════════════════════════════════════
Le run REECRIT `nature` et `type` chaque nuit :

    ON CONFLICT(hektor_annonce_id, numero_mandat) DO UPDATE SET
        nature = excluded.nature, type = excluded.type, ...

Un UPDATE ne tiendrait pas une nuit. Les trois colonnes ecrites ici sont HORS
de l'INSERT du run : il ne les touche jamais. Meme patron que `date_cloture` et
`first_seen_at`, deja protegees ainsi dans cette meme table.

⭐ L'ORDRE DE LECTURE RESTE « HEKTOR D'ABORD » : COALESCE(nature, nature_app).
  Si Hektor parle un jour, c'est lui qui gagne. On ne remplit que son silence.

═══════════════════════════════════════════════════════════════════════════════
LES GARDE-FOUS — chacun repond a une erreur reelle
═══════════════════════════════════════════════════════════════════════════════
① ON N'ECRIT QUE LA OU HEKTOR SE TAIT. Une ligne qui a deja un `type` n'est
   jamais touchee, meme si la source dit autre chose. Ce n'est pas a nous de
   contredire Hektor quand il parle.
② LES DEUX SOURCES DOIVENT S'ACCORDER pour la nature VENTE : le code du
   tableur ET l'`offre_type` de l'annonce. 8 lignes sont en desaccord
   (le tableur dit location/gestion, l'annonce dit vente) : ELLES SONT LAISSEES
   TELLES QUELLES, et comptees a part.
③ LE NUMERO NE SUFFIT PAS A DESIGNER UNE LIGNE : 8 116 numeros sont portes par
   plusieurs annonces (Hektor les recycle). On ecrit donc par le COUPLE
   (annonce, numero), jamais par le numero seul.
④ ⚠ LE PIEGE « 8 682 » : le fichier protexa ecrit 8 682 la ou le registre legal
   dit 18 682. Or 8682 existe chez nous -- une VENTE DE 2014. Toute source dont
   la date est incompatible avec la ligne visee est REFUSEE et comptee.
⑤ RIEN N'EST ECRIT SANS `--ecrire`. Par defaut le script compte et montre.

    python phase2/sync/reparer_nature_depuis_sources_legales.py            (a blanc)
    python phase2/sync/reparer_nature_depuis_sources_legales.py --ecrire
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PHASE2 = ROOT / "phase2" / "phase2.sqlite"
# ⚠ LES DEUX TABLEURS N'ONT PAS LA MEME ORIGINE, et l'etiquette doit le dire
#   (question de Frederic, 15/10 : « pourquoi source_app modelo ? »).
#     mandats_extraits.xlsx     -> l'ANCIEN LOGICIEL, que Frederic appelle Modelo
#     liste mandat du 02_02...  -> un export HEKTOR de fevrier 2026
#   Mesure du 15/10 : les 80 numeros de l'export fevrier sont TOUS deja dans
#   mandats_extraits -- c'est un sous-ensemble, il n'apporte aucun numero neuf.
#   L'etiquette reste donc juste aujourd'hui ; on la rend juste POUR TOUJOURS.
EXPORTS = (("mandats_extraits.xlsx", "modelo"),
           ("liste mandat du 02_02_2026 au 28_02_2026.xlsx", "hektor_fevrier"))

# Codes deduits le 15/10, confirmes par EXCLUSIVITY_LABELS de
# phase2/sync/manual_mandat_corrections.py (ecrit le 05/10, independamment).
NATURE_PAR_CODE = {"1": "VENTE", "3": "RECHERCHE"}      # ⚠ le 2 est AMBIGU : location OU gestion
TYPE_PAR_EXCLUSIVITE = {"1": "EXCLUSIF", "3": "ACCORD", "5": "SIMPLE"}
# offre_type d'une annonce qui est en VENTE (TYPES_ADMIS_AU_REGISTRE du projet)
OFFRE_VENTE = ("0", "10", "6")


def charger_exports() -> dict[str, dict]:
    """Rend {numero: ligne}, chaque ligne marquee de SON fichier d'origine."""
    from openpyxl import load_workbook
    lignes: dict[str, dict] = {}
    for nom, etiquette in EXPORTS:
        chemin = ROOT / nom
        if not chemin.exists():
            print(f"   ⚠ absent, ignore : {nom}", file=sys.stderr)
            continue
        wb = load_workbook(chemin, read_only=True, data_only=True)
        feuille = wb.worksheets[0]
        it = feuille.iter_rows(values_only=True)
        entete = [str(c).strip() if c is not None else "" for c in next(it)]
        for brute in it:
            ligne = dict(zip(entete, brute))
            numero = str(ligne.get("mandate_number") or "").strip()
            if numero:
                ligne["_source"] = etiquette
                lignes.setdefault(numero, ligne)
        wb.close()
    return lignes


def annee(valeur) -> str | None:
    texte = str(valeur or "")
    trouve = re.search(r"(19|20)\d{2}", texte)
    return trouve.group(0) if trouve else None


# ═══════════════════════════════════════════════════════════════════════════════
# LES LIGNES QUE LES SOURCES LEGALES CONTREDISENT -- VERIFIEES UNE PAR UNE
# ═══════════════════════════════════════════════════════════════════════════════
# ⚠⚠ POURQUOI UNE LISTE EN DUR, ET PAS UNE REGLE.
#   Croiser nos natures avec les sources rend 1 344 « ecarts ». LA PLUPART SONT
#   FAUX, et la cause est la COLLISION DE NUMEROS : 8 116 numeros sont portes par
#   plusieurs annonces, Hektor les recycle. Mesure du 15/10 :
#
#       LOCATION -> VENTE   1 212   ⛔ FAUX. Exemple : le n 30 est chez nous
#                                   « APPARTEMENT 3 CHAMBRES » (offre_type = 2,
#                                   location), et l'export decrit « Maison Lieu
#                                   Chambeyrac 43270 Ceaux-d'Allegre ». Deux biens
#                                   differents sous le meme numero.
#       GESTION  -> VENTE      55   ⛔ meme cause
#       RECHERCHE-> VENTE      63   deja traite par le correctif de _nature()
#       INCONNUE -> VENTE       9   refuses par la garde des dates
#       VENTE    -> RECHERCHE   4   ⭐ VRAIS, verifies un par un
#       INCONNUE -> RECHERCHE   1   ⭐ VRAI, du registre LEGAL
#
#   ➡ Une regle automatique aurait ecrit 1 267 faussetes. Les 5 ci-dessous ont
#     ete confrontes A LA MAIN : meme date (a un jour pres) ET meme nom.
#
# ⚠ ET CES 5 NE COMBLENT PAS UN SILENCE, ILS CONTREDISENT. Pour 4 d'entre eux
#   notre registre dit VENTE -- deduit du `type` (« EXCLUSIF », « SIMPLE »), qui
#   est la CATEGORIE JURIDIQUE, pas l'objet. La source legale, elle, nomme
#   l'OBJET. C'est pourquoi elle l'emporte ici.
#   ⛔ QUI GAGNE A LA LECTURE RESTE A TRANCHER (voir la note du chantier) :
#     pour les 502, `nature_app` ne remplit qu'un vide ; pour ces 5, il contredit.
#     Rien ne lit `nature` aujourd'hui, donc rien ne casse en attendant.
CONTREDITS = {
    # numero : (nature vraie, source, ce qui l'etablit)
    "17704": ("RECHERCHE", "modelo",
              "export code 3 · debut 2025-04-10 des deux cotes · CHAPUIS Jean Michel"),
    "17807": ("RECHERCHE", "modelo",
              "export code 3 · debut 2025-05-21 des deux cotes · OUAHID Bruno"),
    "18057": ("RECHERCHE", "modelo",
              "export code 3 · debut 2025-09-18 des deux cotes"),
    "18297": ("RECHERCHE", "modelo",
              "export code 3 · 2026-01-13 contre 2026-01-12 · GIBBE Elodie"),
    "18502": ("RECHERCHE", "registre_legal",
              "registre LEGAL : « Mandat de recherche non exclusif sans demarchage » "
              "· 02/04/2026 · VAUX ANDREE"),
}


def poser_contredits(con, ecrire: bool) -> int:
    """Les 5 lignes que les sources legales contredisent. Voir CONTREDITS."""
    faits = 0
    print("")
    print("=" * 70)
    print("LES LIGNES QUE LES SOURCES LEGALES CONTREDISENT (verifiees a la main)")
    print("=" * 70)
    for numero, (vraie, source, pourquoi) in sorted(CONTREDITS.items()):
        ligne = con.execute(
            "SELECT hektor_annonce_id, nature, nature_app FROM app_mandat"
            "  WHERE numero_mandat = ? AND hektor_annonce_id <> ''", (numero,)).fetchone()
        if ligne is None:
            print(f"   {numero} : ABSENT du registre -- rien a faire")
            continue
        annonce, nature, deja = ligne
        etat = "deja pose" if (deja or "") == vraie else "a poser"
        print(f"   {numero} · annonce {annonce} · nous disons {nature} -> {vraie}  [{etat}]")
        print(f"            {pourquoi}")
        if ecrire and (deja or "") != vraie:
            con.execute("UPDATE app_mandat SET nature_app = ?, source_app = ?"
                        " WHERE numero_mandat = ? AND hektor_annonce_id = ?",
                        (vraie, source, numero, annonce))
            faits += 1
    return faits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remplit nature_app/type_app depuis les sources legales. "
                    "Ne touche JAMAIS nature ni type.")
    parser.add_argument("--ecrire", action="store_true",
                        help="Ecrit vraiment. Sans lui, le script ne fait que compter.")
    parser.add_argument("--base", default=str(PHASE2))
    args = parser.parse_args()

    exports = charger_exports()
    print(f"sources : {len(exports)} numeros dans les exports Modelo")

    con = sqlite3.connect(args.base, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    colonnes = {r[1] for r in con.execute("PRAGMA table_info(app_mandat)")}
    for besoin in ("nature_app", "type_app", "source_app"):
        if besoin not in colonnes:
            print(f"ARRET : la colonne {besoin} n'existe pas encore. "
                  f"Lancer d'abord `mandat_ledger.py --refresh` (il pose l'ALTER).",
                  file=sys.stderr)
            return 2

    lignes = list(con.execute(
        "SELECT hektor_annonce_id, numero_mandat, type, nature, offre_type,"
        "       date_debut, nature_app"
        "  FROM app_mandat"))
    print(f"registre : {len(lignes)} lignes\n")

    a_ecrire: list[tuple] = []
    refus = Counter()
    exemples_date: list[str] = []
    for annonce, numero, type_hektor, nature, offre, debut, deja in lignes:
        numero = str(numero or "").strip()

        # ⓪ ON NE REMPLIT QUE LE TROU, ET LE TROU C'EST « INCONNUE ».
        #   ⚠ CORRIGE LE 15/10 APRES MESURE : sans cette garde, le script aurait
        #     pose « VENTE » sur 1 212 lignes que NOUS avions deduites LOCATION
        #     (depuis l'offre_type de leur annonce) et 42 GESTION. Contredire
        #     notre propre deduction n'est pas remplir un silence, c'est
        #     introduire un desaccord. Une ligne qui porte deja une nature,
        #     meme deduite, n'est pas un trou.
        if (nature or "") != "INCONNUE":
            refus["une nature est deja etablie (ce n'est pas un trou)"] += 1
            continue

        # ① Hektor parle -> on se tait.
        if (type_hektor or "").strip():
            refus["Hektor donne deja un type"] += 1
            continue
        source = exports.get(numero)
        if source is None:
            refus["aucune source pour ce numero"] += 1
            continue

        # ④ LE PIEGE « 8 682 », ET IL MORD SOUVENT.
        #   8 116 numeros sont portes par PLUSIEURS annonces (Hektor les
        #   recycle). Une source trouvee par le numero seul peut donc parler
        #   d'un AUTRE mandat. Quand les annees ne concordent pas, on refuse.
        an_nous = annee(debut)
        an_source = annee(source.get("date_start") or source.get("date"))
        if an_nous and an_source and abs(int(an_nous) - int(an_source)) > 1:
            refus["date incompatible : la source parle d'un AUTRE mandat"] += 1
            if len(exemples_date) < 6:
                exemples_date.append(f"n {numero} (annonce {annonce}) : "
                                     f"chez nous {an_nous}, la source {an_source}")
            continue

        code = str(source.get("mandate_type") or "").strip()
        proposee = NATURE_PAR_CODE.get(code)
        if proposee is None:
            refus[f"code {code or '(vide)'} : ambigu (2 = location OU gestion)"] += 1
            continue

        # ② pour une VENTE, notre propre base doit etre d'accord.
        if proposee == "VENTE" and str(offre or "") not in OFFRE_VENTE:
            refus["desaccord : la source dit vente, l'annonce non"] += 1
            continue

        type_app = TYPE_PAR_EXCLUSIVITE.get(str(source.get("exclusivity") or "").strip())
        a_ecrire.append((proposee, type_app, source.get("_source", "modelo"),
                         str(annonce), numero))

    inconnues = sum(1 for r in lignes if (r[3] or "") == "INCONNUE")
    print(f"LE TROU A COMBLER : {inconnues} lignes « INCONNUE »\n")
    print("CE QUI SERAIT ECRIT")
    print(f"   lignes             {len(a_ecrire)}   sur {inconnues} INCONNUE")
    print(f"   natures            {dict(Counter(x[0] for x in a_ecrire))}")
    print(f"   dont un TYPE aussi {sum(1 for x in a_ecrire if x[1])}"
          f"   {dict(Counter(x[1] for x in a_ecrire if x[1]))}")
    print("\nCE QUI EST REFUSE, ET POURQUOI")
    for motif, nb in refus.most_common():
        print(f"   {nb:>6}  {motif}")
    if exemples_date:
        print("      exemples de dates incompatibles (numero recycle par Hektor) :")
        for e in exemples_date:
            print(f"         {e}")

    poser_contredits(con, ecrire=False)

    if not args.ecrire:
        print("\nA BLANC — rien n'a ete ecrit. Relancer avec --ecrire.")
        con.close()
        return 0

    con.executemany(
        "UPDATE app_mandat SET nature_app=?, type_app=?, source_app=?"
        " WHERE hektor_annonce_id=? AND numero_mandat=?", a_ecrire)
    contredits = poser_contredits(con, ecrire=True)
    con.commit()
    print(f"   + {contredits} ligne(s) contredite(s) corrigee(s)")
    pose = con.execute("SELECT COUNT(*) FROM app_mandat"
                       " WHERE COALESCE(nature_app,'') <> ''").fetchone()[0]
    print(f"\nECRIT. lignes portant desormais une nature_app : {pose}")
    print("   ⚠ `nature` et `type` n'ont PAS ete touchees -- verifier :")
    for r in con.execute(
            "SELECT nature, COUNT(*) FROM app_mandat GROUP BY 1 ORDER BY 2 DESC"):
        print(f"      {r[0]:<12} {r[1]}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
