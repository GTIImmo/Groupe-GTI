#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'ECART D'EMPREINTE DE app_poser_etiquettes_dossier : LE CORPS SEUL, SUR LA COPIE ET EN PRODUCTION.   23/11/2026

    python -u -X utf8 phase2/checks/comparer_corps_fonction_copie_et_production.py --pg C:\\Hektor\\outils\\postgres17\\paquet\\package\\native\\bin

SON MOT DU 23/11 (3), § 2 : le patch est colle (repetition 9/9), mais l'empreinte de pg_get_functiondef en production
(b9fa8dea...) n'est pas celle de la copie (e695bf7e...), a version EGALE (17.6). « compare LE CORPS SEUL, pas l'en-tete.
En production je lis : md5(prosrc) 1431b364def1a5cdaf646f5231628dac, length(prosrc) 10 455. Donne-moi les deux memes
chiffres pris SUR TA COPIE, apres le rejeu du patch. » -- A : identiques -> l'ecart est dans l'en-tete ; B : differents
-> OU, et on decide ensemble (inverse avant 05:00).

CE QU'IL FAIT -- TROIS CORPS, pas deux :
  1. PRODUCTION (lecture seule, REPEATABLE READ READ ONLY) : prosrc, pg_get_functiondef, et chaque attribut de l'en-tete
     (securite, volatilite, search_path, langage, strict, cout, parallele, proprietaire) ;
  2. LA COPIE (le Postgres 17.6 LOCAL, localhost:54329, arrete a la fin) : la copie du 22/11 20:12, avec la fonction
     d'AVANT (relue identique a Supabase, 815e956f), puis LE FICHIER DU PATCH joue tel quel -- exactement le rejeu ;
  3. LE FICHIER DU PATCH lui-meme : le texte entre « AS $function$ » et « $function$; ».
  Puis : md5 et longueur des trois corps ; s'ils different, OU (diff ligne a ligne, retours chariot, espaces de fin) ;
  et l'en-tete compare SANS son corps.
⛔ Rien n'est ecrit en production. L'inverse n'est PAS joue (son mot : « NE JOUE PAS L'INVERSE »).
ECRIT : C:\\Hektor\\chantier_classeur_q6_cache\\rejeu_patch_journal\\corps_<horodatage>\\ (les textes et le diff).
CODES : 0 corps identiques (A) . 1 corps differents (B) . 2 pas pu
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import rejeu_patch_journal_sur_copie as R  # noqa: E402

FONCTION = "public.app_poser_etiquettes_dossier"
LIRE = ("select p.prosrc, md5(p.prosrc), length(p.prosrc), pg_get_functiondef(p.oid), md5(pg_get_functiondef(p.oid)), "
        "p.prosecdef, p.provolatile, p.proconfig, l.lanname, p.proisstrict, p.procost, p.prorows, p.proparallel, "
        "pg_get_userbyid(p.proowner), pg_get_function_arguments(p.oid), pg_get_function_result(p.oid), version() "
        "from pg_proc p join pg_language l on l.oid = p.prolang where p.oid = '%s'::regproc" % FONCTION)
CHAMPS = ("prosrc", "md5_prosrc", "length_prosrc", "functiondef", "md5_functiondef", "security_definer", "volatilite",
          "proconfig", "langage", "strict", "cout", "lignes", "parallele", "proprietaire", "arguments", "resultat",
          "version")


def dire(s: str = "") -> None:
    print(s, flush=True)


def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def corps_du_fichier() -> str:
    t = R.PATCH.read_text(encoding="utf-8")
    a = t.index("AS $function$") + len("AS $function$")
    b = t.index("$function$;", a)
    return t[a:b]


def decrire(nom: str, s: str) -> str:
    lignes = s.split("\n")
    return ("%s : md5 %s . %d caracteres . %d lignes . %d retour(s) chariot . %d ligne(s) a espace de fin . %d tab(s) . "
            "%d caractere(s) hors ASCII" % (nom, md5(s), len(s), len(lignes), s.count("\r"),
                                            sum(1 for x in lignes if x.rstrip("\r") != x.rstrip("\r").rstrip()),
                                            s.count("\t"), sum(1 for c in s if ord(c) > 127)))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pg", required=True)
    a = ap.parse_args()
    out = R.CACHE / ("corps_%s" % datetime.now().strftime("%Y-%m-%d_%H%M%S"))
    out.mkdir(parents=True, exist_ok=True)
    # 1. PRODUCTION
    import sauvegarde_datee_classeur as S
    try:
        cn, cu = S.connexion()
        cu.execute(LIRE)
        prod = dict(zip(CHAMPS, cu.fetchone()))
        cn.rollback()
        cn.close()
    except Exception as e:  # noqa: BLE001
        dire("⛔ la production n'a pas pu etre lue (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    # 2. LA COPIE, le patch rejoue tel quel
    d = R.CACHE / "2026-11-22_201242"
    man = json.loads((d / "manifeste.json").read_text(encoding="utf-8"))
    L = R.Local(Path(a.pg))
    L.demarrer()
    try:
        rouges = R.charger_modele(L, d, man)
        if rouges:
            dire("⛔ la copie n'est pas celle de Supabase : %s -- code 2" % rouges)
            return 2
        R.base_depuis("modele", "corps_apres")
        R.jouer_fichier("corps_apres", R.PATCH)
        cn = L.cnx("corps_apres")
        cu = cn.cursor()
        cu.execute(LIRE)
        copie = dict(zip(CHAMPS, cu.fetchone()))
        cn.close()
    finally:
        L.arreter()
    fichier = corps_du_fichier()
    for nom, x in (("production", prod), ("copie", copie)):
        (out / ("prosrc_%s.txt" % nom)).write_bytes(x["prosrc"].encode("utf-8"))
        (out / ("functiondef_%s.sql" % nom)).write_bytes(x["functiondef"].encode("utf-8"))
    (out / "prosrc_fichier_du_patch.txt").write_bytes(fichier.encode("utf-8"))

    dire("=== 1. LES DEUX CHIFFRES QU'IL DEMANDE ===")
    dire("   PRODUCTION : md5(prosrc) %s . length(prosrc) %s   (son mot : 1431b364def1a5cdaf646f5231628dac . 10 455)"
         % (prod["md5_prosrc"], prod["length_prosrc"]))
    dire("   COPIE      : md5(prosrc) %s . length(prosrc) %s" % (copie["md5_prosrc"], copie["length_prosrc"]))
    dire("   (pg_get_functiondef : production %s . copie %s)" % (prod["md5_functiondef"], copie["md5_functiondef"]))
    dire("   versions : production %s | copie %s" % (prod["version"].split(" on ")[0], copie["version"].split(" on ")[0]))
    dire("")
    dire("=== 2. LES TROIS CORPS ===")
    for nom, s in (("production     ", prod["prosrc"]), ("copie          ", copie["prosrc"]),
                   ("fichier du patch", fichier)):
        dire("   " + decrire(nom, s))
    corps_egaux = prod["prosrc"] == copie["prosrc"]
    dire("   corps production == corps copie : %s ; copie == fichier : %s ; production == fichier : %s"
         % (corps_egaux, copie["prosrc"] == fichier, prod["prosrc"] == fichier))
    if not corps_egaux:
        sans_cr = prod["prosrc"].replace("\r", "") == copie["prosrc"].replace("\r", "")
        sans_fin = ("\n".join(x.rstrip() for x in prod["prosrc"].replace("\r", "").split("\n"))
                    == "\n".join(x.rstrip() for x in copie["prosrc"].replace("\r", "").split("\n")))
        dire("   ⚠ DIFFERENTS. Egaux si l'on retire les retours chariot : %s ; et les espaces de fin de ligne : %s"
             % (sans_cr, sans_fin))
        diff = list(difflib.unified_diff([repr(x) for x in copie["prosrc"].split("\n")],
                                         [repr(x) for x in prod["prosrc"].split("\n")],
                                         "copie", "production", n=1, lineterm=""))
        (out / "diff_corps_copie_production.txt").write_text("\n".join(diff), encoding="utf-8")
        dire("   diff (repr, %d lignes) -> %s ; les 40 premieres :" % (len(diff), out / "diff_corps_copie_production.txt"))
        for x in diff[:40]:
            dire("      " + x[:200])
    dire("")
    dire("=== 3. L'EN-TETE, SANS SON CORPS ===")
    tp = prod["functiondef"].replace(prod["prosrc"], "<CORPS>")
    tc = copie["functiondef"].replace(copie["prosrc"], "<CORPS>")
    dire("   en-tete production == en-tete copie : %s" % (tp == tc))
    for k in ("security_definer", "volatilite", "proconfig", "langage", "strict", "cout", "lignes", "parallele",
              "proprietaire", "arguments", "resultat"):
        m = "" if prod[k] == copie[k] else "   <- DIFFERE"
        dire("   %-16s production %-40s copie %s%s" % (k, str(prod[k])[:40], str(copie[k])[:60], m))
    if tp != tc:
        for x in difflib.unified_diff(tc.split("\n"), tp.split("\n"), "copie", "production", n=0, lineterm=""):
            dire("      " + repr(x)[:200])
    dire("")
    dire("-> les textes : %s" % out)
    if corps_egaux:
        dire("⭐ HYPOTHESE A : LE CORPS EST IDENTIQUE -- l'ecart de pg_get_functiondef est dans l'en-tete (voir 3).")
        return 0
    dire("⛔ HYPOTHESE B : LE CORPS DIFFERE -- voir le diff.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
