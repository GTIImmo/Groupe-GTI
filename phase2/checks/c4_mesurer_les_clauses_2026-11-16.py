#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C4 -- LES CLAUSES PARTICULIERES CACHEES DANS LA COLONNE F.         16/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c4_mesurer_les_clauses_2026-11-16.py

⛔ LECTURE SEULE. Lit le Sheet, mesure, ecrit UN fichier dans notice/. Rien en base.

⭐⭐⭐ CE QUE C4 DOIT REMPLIR, ET JE L'AVAIS PRESENTE A L'ENVERS LE 16/11 :
  `app_affaire_condition` n'est pas une table de notes. Ses colonnes le disent --
  `libelle . jours . date_echeance . etat . date_levee . note . catalogue_id` : ce
  sont LES CLAUSES PARTICULIERES, avec leur delai, leur echeance, et si elles ont
  ete LEVEES. Avec leur catalogue de types, `app_condition_catalogue`, qui ne porte
  aujourd'hui que **2 lignes**. Le mecanisme est en place et QUASI VIDE.

  ⛔ Frederic, 16/11 : « Non c4 devait remplir les clause particuliere etc. Relie nos
    notes du chantier. » J'avais mis en avant le dechet (les « V », les pastilles) et
    cache la valeur. A16 dit l'inverse :

      LE VRAI CONTENU UTILE -- LA CAUSE DES ANNULATIONS, chacune a 100 % :
         retractation / SRU 129 . pret refuse 107 . annulation 70
         travaux 11 . succession ou divorce 10 . changement d'avis 8
      ➡ 383 des 896 annulations ont un motif identifiable, 734 textes a regrouper
      LE FINANCEMENT : 167 lignes « 260K 25a », « relais » -> montant et duree du PRET

  Et la phrase qui compte : « nous savons qu'une vente tombe, JAMAIS POURQUOI. »

LES QUATRE TRAITEMENTS QUE LA NOTE EXIGE, et ce script les fait tous les quatre :
```
   ① SEPARER le pictogramme du texte : ils sont dans la MEME case
   ② NORMALISER « refus pret » (31) et « refus de pret » (24) : la MEME chose
   ③ ECARTER ce qui n'est pas un etat : « V Sarah » porte un PRENOM
   ④ LE CLASSEUR CONTIENT DES EMOJI, et un script naif MEURT dessus (05/11)
```

⭐ ET LA CONSIGNE DE FREDERIC EST RESPECTEE (« en bloc, sans interpreter ») : on ne
  TRANSFORME aucun texte. On SEPARE ce qui est colle dans la meme case, on GROUPE ce
  qui est manifestement identique (casse, accents, « de »), et on ECARTE ce qui n'est
  pas une clause. Le texte d'origine est conserve dans le fichier, a cote.

⛔ CE SCRIPT NE DECIDE RIEN : il presente le catalogue qui sort de F, pour que
  Frederic tranche sur une liste REELLE et non sur une idee.
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # ④ les emoji
except Exception:
    pass

import apparier_classeur as ap                                      # noqa: E402

SORTIE = RACINE / "notice" / "C4_LES_CLAUSES_DE_LA_COLONNE_F_2026-11-16.csv"
CATALOGUE = RACINE / "notice" / "C4_CATALOGUE_PROPOSE_2026-11-16.csv"


def index_de(lettre: str) -> int:
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def est_pictogramme(c: str) -> bool:
    """④ Un pictogramme, c'est un caractere hors des alphabets usuels : emoji,
    symbole, forme geometrique. On le reconnait par sa CATEGORIE Unicode, jamais
    par une liste de caracteres -- une liste oublie toujours le suivant."""
    if c in " \t ":
        return False
    cat = unicodedata.category(c)                    # So = Symbol other, Sk, Sm
    return cat.startswith("S") or ord(c) > 0x2000


def sans_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def cle(s: str) -> str:
    """② La clef de regroupement. ⚠ ELLE NE TRANSFORME PAS LE TEXTE GARDE : elle ne
    sert qu'a reconnaitre que deux ecritures disent la meme chose. Le texte
    d'origine est conserve tel quel dans le fichier."""
    t = sans_accent(s).lower().strip()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\b(de|du|des|la|le|les|d|l|pour|en|au|aux)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


#: ③ Ce qui N'EST PAS une clause. Mesure, pas devine : A16 nomme les trois familles.
def quoi_est_ce(texte: str) -> str:
    t = cle(texte)
    if not t:
        return "rien (pictogramme seul)"
    # un financement : un montant en K et/ou une duree en annees
    if re.search(r"\b\d{2,4}\s*k\b", t) or re.search(r"\b\d{1,2}\s*a\b", t) \
       or "relais" in t:
        return "FINANCEMENT (montant / duree du pret)"
    # un prenom seul derriere un V : « v sarah », « v anne »
    if re.fullmatch(r"v [a-z]+", t):
        return "PRENOM derriere un V"
    if re.fullmatch(r"v", t):
        return "etat V (= VENDU, deja connu)"
    return "CLAUSE ou MOTIF"


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== C4 -- LES CLAUSES PARTICULIERES CACHEES DANS F (lecture seule) ===")
    print()

    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    i_f, i_g = index_de("F"), index_de("G")
    i_etat = entetes.index("Etat Actuel")
    i_id = entetes.index("ID Unique")
    print("le Sheet : %d lignes . F = %r . G = %r"
          % (len(lignes), entetes[i_f], entetes[i_g]))
    print()

    def case(l, i):
        return str(l[i] if i < len(l) else "").strip()

    detail = []
    familles = Counter()
    pictos = Counter()
    par_cle: dict[str, dict] = defaultdict(lambda: {"n": 0, "ecritures": Counter(),
                                                    "etats": Counter()})
    n_f = n_g = 0
    for _rang, l in lignes:
        brut = case(l, i_f)
        if case(l, i_g):
            n_g += 1
        if not brut:
            continue
        n_f += 1
        # ① SEPARER le pictogramme du texte, dans la meme case
        picto = "".join(c for c in brut if est_pictogramme(c))
        texte = "".join(c for c in brut if not est_pictogramme(c)).strip()
        for c in picto:
            pictos[c] += 1
        famille = quoi_est_ce(texte)
        familles[famille] += 1
        etat = case(l, i_etat)
        if famille == "CLAUSE ou MOTIF":
            k = cle(texte)
            par_cle[k]["n"] += 1
            par_cle[k]["ecritures"][texte] += 1
            par_cle[k]["etats"][etat or "(vide)"] += 1
        detail.append({"id_unique": case(l, i_id), "F_brut": brut,
                       "pictogramme": picto, "texte_seul": texte,
                       "famille": famille, "etat_actuel": etat,
                       "clef_de_regroupement": cle(texte)})

    print("=== ① LA SEPARATION : %d cases de F remplies ===" % n_f)
    print("   (et G en porte %d, du texte libre -> app_affaire_note)" % n_g)
    print()
    print("=== ③ LE TRI PAR FAMILLE ===")
    for fam, n in familles.most_common():
        print("   %-42s %5d" % (fam, n))
    print()
    print("=== ④ LES PICTOGRAMMES, SEPARES DU TEXTE ===")
    for c, n in pictos.most_common(10):
        try:
            nom = unicodedata.name(c)
        except ValueError:
            nom = "?"
        print("   %r  %5d   %s" % (c, n, nom[:56]))
    print()

    # ─── ② LE CATALOGUE QUI SORT DE F ────────────────────────────────────────
    utiles = sorted(par_cle.items(), key=lambda kv: -kv[1]["n"])
    print("=== ② LE CATALOGUE DES CLAUSES QUI SORT DE F ===")
    print("   %d ecritures distinctes se regroupent en %d clauses"
          % (sum(len(v["ecritures"]) for _k, v in utiles), len(utiles)))
    print()
    print("   lignes  clause (la clef)            ses ecritures au classeur")
    for k, v in utiles[:30]:
        ecr = " | ".join("%s (%d)" % (e, n) for e, n in v["ecritures"].most_common(3))
        print("   %5d   %-26s %s" % (v["n"], k[:26], ecr[:62]))
    if len(utiles) > 30:
        print("   ... et %d clauses de moins de %d lignes (tout est dans le CSV)"
              % (len(utiles) - 30, utiles[30][1]["n"]))
    print()

    # ⭐⭐ LE TEMOIN QUI DONNE SA VALEUR A F : le motif pointe-t-il vers « Annulee » ?
    print("=== ⭐ LE TEMOIN : CES CLAUSES POINTENT-ELLES VERS UNE ANNULATION ? ===")
    print("   (A16 annoncait 100 % pour les six plus gros motifs)")
    print()
    print("   lignes  clause                      part « Annulee »")
    for k, v in utiles[:14]:
        tot = sum(v["etats"].values())
        ann = v["etats"].get("Annulée", 0) + v["etats"].get("Annulee", 0)
        print("   %5d   %-26s %3d %%   (%s)"
              % (v["n"], k[:26], round(100 * ann / max(tot, 1)),
                 " . ".join("%s %d" % (e, n) for e, n in v["etats"].most_common(3))[:46]))

    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=list(detail[0]))
        w.writeheader()
        w.writerows(detail)
    with CATALOGUE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "lignes", "clause_proposee", "ecritures_au_classeur",
            "part_annulee_pourcent", "etats_rencontres"])
        w.writeheader()
        for k, v in utiles:
            tot = sum(v["etats"].values())
            ann = v["etats"].get("Annulée", 0) + v["etats"].get("Annulee", 0)
            w.writerow({"lignes": v["n"], "clause_proposee": k,
                        "ecritures_au_classeur": " | ".join(
                            "%s (%d)" % (e, n) for e, n in v["ecritures"].most_common()),
                        "part_annulee_pourcent": round(100 * ann / max(tot, 1)),
                        "etats_rencontres": " . ".join(
                            "%s %d" % (e, n) for e, n in v["etats"].most_common())})
    print()
    print("ecrit : %s" % SORTIE)
    print("ecrit : %s" % CATALOGUE)
    print()
    print("⛔ RIEN N'A ETE ECRIT EN BASE. Ce script PRESENTE le catalogue ;")
    print("   le choix des clauses a retenir appartient a Frederic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
