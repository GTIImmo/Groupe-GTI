#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- PASSE 1 : L'INVENTAIRE DES SIGNAUX.          13/11/2026

Demande de Frederic (12/11 au soir) : *« est tu capable de reprendre ligne par
ligne le classeur sheet et chercher toi meme les transactions correspondantes
SANS utiliser la regle du gel, avec ta propre methode, pour comparer ensuite au
mien ? »*

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LES TROIS REGLES D'INDEPENDANCE -- elles sont le coeur du dispositif
═══════════════════════════════════════════════════════════════════════════════
  1. ON NE LIT JAMAIS `app_classeur_lien` (le gel). Pas une fois, nulle part.
  2. ON NE LIT JAMAIS le CSV d'appariement de la v1 : il porte DEJA la reponse
     (« chaine trouvee », « confiance », « par quelle cle »). Le lire, meme pour
     « se reperer », detruirait l'independance en silence.
  3. ON N'IMPORTE AUCUNE LOGIQUE de `apparier_classeur.py`. ⚠ On importe
     `lire_classeur` et `load_env_file` -- et SEULEMENT elles : lire un fichier
     n'est pas apparier. C'est l'acces aux donnees, pas le raisonnement. Si un
     jour on y importait autre chose, l'independance tomberait.

⭐ L'INDEPENDANCE DOIT ETRE GARANTIE PAR CONSTRUCTION, PAS PAR BONNE VOLONTE :
  ce fichier ne contient pas le nom des tables et fichiers interdits ailleurs que
  dans ce commentaire, et la passe 3 (la comparaison) sera un fichier SEPARE.

═══════════════════════════════════════════════════════════════════════════════
CE QUE FAIT CETTE PASSE, ET RIEN D'AUTRE
═══════════════════════════════════════════════════════════════════════════════
Elle MESURE. Elle n'apparie pas encore une seule ligne. Avant de concevoir un
score, il faut savoir ce qu'on a vraiment dans les mains :
  . les colonnes du Sheet, et le taux de remplissage de chacune ;
  . pour chaque signal, sa PUISSANCE DISCRIMINANTE mesuree -- combien de
    transactions un signal donne designe-t-il en moyenne ?
  ⭐ C'est la lecon de Frederic du 29/10 : « une preuve vaut par sa RARETE, pas
    par sa nature ». On ne choisit pas les signaux au jugement, on les PESE.

LECTURE SEULE DE BOUT EN BOUT : Sheet en lecture, phase2.sqlite en mode `ro`.
Rien n'est ecrit en base, ni chez Hektor, ni dans le classeur.

⚠ LA BASE LOCALE PORTE L'ETAT DE LA DESCENTE DE 07:45 HIER. Les 5 dates decidees
  du 12/11 au soir n'y sont donc PAS (ces 5 offres y ont encore `0000-00-00`), et
  les chaines sont celles du dernier run. ⭐ Sans consequence ici : on apparie vers
  des TRANSACTIONS, dont le numero ne bouge jamais.
"""
from __future__ import annotations

import collections
import csv
import io
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

SORTIE = RACINE / "notice" / "APPARIEUR_V2_INVENTAIRE_2026-11-13.csv"


# ─────────────────────────────────────────────────────────────────────────────
# LES NORMALISATEURS -- ecrits ici, pas importes
# ⚠ Le classeur est saisi A LA MAIN : accents, casse, espaces, tirets varient.
#   Une comparaison brute perd des lignes pour rien (faute payee le 12/11 :
#   « Allegre » ne trouvait pas « Allègre »).
# ─────────────────────────────────────────────────────────────────────────────
def sans_accent(t) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(t or ""))
                   if unicodedata.category(c) != "Mn")


def pur(t) -> str:
    """Texte comparable : sans accent, minuscule, espaces normalises."""
    return re.sub(r"\s+", " ", sans_accent(t).strip().lower())


def chiffres(t) -> str:
    return "".join(c for c in str(t or "") if c.isdigit())


def somme(t):
    """Un montant comparable, en euros entiers. Rend None si illisible."""
    s = str(t or "").strip()
    if not s:
        return None
    s = sans_accent(s).replace("EUR", "").replace("€", "")
    s = s.replace(" ", "").replace("\u00a0", "").replace("'", "")
    # 1.234,56 (fr) et 1,234.56 (en) coexistent dans un classeur a la main
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") \
            else s.replace(",", "")
    else:
        s = s.replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        v = float(s)
    except ValueError:
        return None
    return int(round(v)) if v else None


def jour(t) -> str:
    """Une date comparable, en AAAA-MM-JJ. Rend '' si rien d'utilisable."""
    s = str(t or "").strip()
    if not s or s.startswith("0000"):
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", s)
    if m:
        j, mo, a = m.groups()
        a = ("20" + a) if len(a) == 2 else a
        return "%s-%02d-%02d" % (a, int(mo), int(j))
    return ""


MOTS_VIDES = {
    "mr", "mme", "mlle", "m", "monsieur", "madame", "mademoiselle", "me",
    "sci", "sarl", "sas", "sasu", "eurl", "sa", "scp", "snc", "indivision",
    "et", "ou", "de", "du", "des", "la", "le", "les", "l", "d", "ep", "epoux",
    "veuve", "vve", "ne", "nee", "consorts", "succession", "hoirie",
}


def noms(t) -> set[str]:
    """Les mots de NOM d'un texte, normalises, hors civilites et formes sociales.
    ⭐ On rend un ENSEMBLE : un couple porte deux noms pour un seul acheteur, et
      comparer des ensembles gere ca tout seul (faute payee 4 fois le 12/11 :
      le dossier 2588 paraissait faux, c'etait un COUPLE)."""
    mots = re.split(r"[^A-Za-z\u00c0-\u024f]+", sans_accent(t or ""))
    return {m.lower() for m in mots if len(m) >= 3 and m.lower() not in MOTS_VIDES}


# ─────────────────────────────────────────────────────────────────────────────
def lire_le_sheet():
    from apparier_classeur import lire_classeur, load_env_file  # noqa: E402
    load_env_file(RACINE / ".env")
    entetes, brutes = lire_classeur()
    lignes = [(n, l) for n, l in brutes]
    return entetes, lignes


def lire_le_registre(con):
    """Les transactions, en lecture seule. ⭐ On prend TOUT ce qui peut servir de
    signal, et on ne decide pas encore lesquels comptent."""
    c = con.cursor()
    c.execute("""
        select app_affaire_id, kind, state, date, date_acte, montant,
               numero_mandat, hektor_annonce_id, app_chaine_id,
               acquereur_json, acquereurs_json, mandants_json, propositions_json,
               hektor_acquereur_id, present_in_hektor
          from app_affaire_ledger
    """)
    cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in c.fetchall()]


def main() -> int:
    print("=" * 78)
    print("APPARIEUR V2 -- PASSE 1 : L'INVENTAIRE DES SIGNAUX")
    print("  INDEPENDANCE : ni le gel, ni le CSV de la v1, ni sa logique.")
    print("=" * 78)

    entetes, lignes = lire_le_sheet()
    print("\nLE SHEET : %d lignes, %d colonnes" % (len(lignes), len(entetes)))

    idx = {n: i for i, n in enumerate(entetes)}

    def case(l, nom):
        i = idx.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    # ── ① LE TAUX DE REMPLISSAGE DE CHAQUE COLONNE ──────────────────────────
    print("\n" + "-" * 78)
    print("① LE TAUX DE REMPLISSAGE -- une colonne vide n'est pas un signal")
    print("-" * 78)
    rempli = []
    for nom in entetes:
        n = sum(1 for _, l in lignes if case(l, nom))
        rempli.append((nom, n, 100.0 * n / max(1, len(lignes))))
    for nom, n, pc in rempli:
        barre = "#" * int(pc / 4)
        print("   %-28s %5d  %5.1f %%  %s" % (nom[:28], n, pc, barre))

    # ── ② LE REGISTRE ───────────────────────────────────────────────────────
    con = sqlite3.connect("file:%s?mode=ro"
                          % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    tx = lire_le_registre(con)
    print("\n" + "-" * 78)
    print("② LE REGISTRE : %d transactions" % len(tx))
    print("-" * 78)
    par_genre = collections.Counter(t["kind"] for t in tx)
    for k, v in par_genre.most_common():
        print("   %-12s %6d" % (k, v))

    # ── ③ LA PUISSANCE DISCRIMINANTE DE CHAQUE SIGNAL ───────────────────────
    #   ⭐ LA MESURE QUI DECIDE DE TOUT : combien de transactions un signal
    #     donne designe-t-il ? Un signal qui en designe 1 est un IDENTIFIANT ;
    #     un signal qui en designe 400 est au mieux un DEPARTAGEUR.
    print("\n" + "-" * 78)
    print("③ LA PUISSANCE DISCRIMINANTE -- « une preuve vaut par sa RARETE »")
    print("-" * 78)

    def pese(nom, clef_tx):
        """Combien de transactions par valeur de ce signal ?"""
        d = collections.defaultdict(set)
        for t in tx:
            for v in clef_tx(t):
                if v:
                    d[v].add(t["app_affaire_id"])
        if not d:
            print("   %-26s AUCUNE valeur -- signal inexploitable" % nom)
            return
        tailles = sorted(len(s) for s in d.values())
        n = len(tailles)
        seules = sum(1 for x in tailles if x == 1)
        print("   %-26s %6d valeurs . %5.1f %% n'en designent QU'UNE . "
              "mediane %d . max %d"
              % (nom, n, 100.0 * seules / n, tailles[n // 2], tailles[-1]))

    def noms_tx(t):
        out = set()
        for champ in ("acquereur_json", "acquereurs_json", "mandants_json"):
            out |= noms(t.get(champ))
        return out

    pese("numero de mandat", lambda t: [chiffres(t.get("numero_mandat"))])
    pese("numero d'annonce", lambda t: [str(t.get("hektor_annonce_id") or "")])
    pese("montant", lambda t: [str(somme(t.get("montant")) or "")])
    pese("date (jour)", lambda t: [jour(t.get("date"))])
    pese("1 mot de nom", lambda t: noms_tx(t))
    pese("mandat + montant", lambda t: ["%s|%s" % (chiffres(t.get("numero_mandat")),
                                                   somme(t.get("montant")) or "")])
    pese("annonce + montant", lambda t: ["%s|%s" % (t.get("hektor_annonce_id") or "",
                                                    somme(t.get("montant")) or "")])

    # ── ④ CE QUE CHAQUE LIGNE DU SHEET PORTE REELLEMENT ─────────────────────
    print("\n" + "-" * 78)
    print("④ CE QUE CHAQUE LIGNE DU SHEET PORTE -- combien de signaux utilisables")
    print("-" * 78)
    col = {k: next((n for n in entetes if pur(n) == pur(k)), None) for k in (
        "ID Unique", "Mandat", "Prix", "Acquéreur", "Vendeur", "Ville",
        "Etat Actuel", "Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée",
    )}
    print("   colonnes reperees : %s"
          % ", ".join("%s=%r" % (k, v) for k, v in col.items() if v))
    manquantes = [k for k, v in col.items() if not v]
    if manquantes:
        print("   ⚠ NON TROUVEES, a verifier a la main : %s" % ", ".join(manquantes))

    compte = collections.Counter()
    detail = []
    for n, l in lignes:
        s = []
        if col["Mandat"] and chiffres(case(l, col["Mandat"])):
            s.append("mandat")
        if col["Prix"] and somme(case(l, col["Prix"])):
            s.append("prix")
        if col["Acquéreur"] and noms(case(l, col["Acquéreur"])):
            s.append("acq")
        if col["Vendeur"] and noms(case(l, col["Vendeur"])):
            s.append("vend")
        if col["Ville"] and pur(case(l, col["Ville"])):
            s.append("ville")
        dates = [c for c in ("Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée")
                 if col[c] and jour(case(l, col[c]))]
        if dates:
            s.append("date(%d)" % len(dates))
        compte[len(s)] += 1
        detail.append((n, case(l, col["ID Unique"]) if col["ID Unique"] else "",
                       len(s), "+".join(s)))
    print("\n   combien de signaux par ligne :")
    for k in sorted(compte):
        print("      %d signal(aux) : %5d lignes  (%4.1f %%)"
              % (k, compte[k], 100.0 * compte[k] / len(lignes)))

    with io.open(SORTIE, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ligne du classeur", "ID Unique", "nb signaux", "lesquels"])
        w.writerows(detail)
    print("\n   ecrit : %s" % SORTIE)

    print("\n" + "=" * 78)
    print("PASSE 1 TERMINEE -- rien n'a ete apparie, rien n'a ete ecrit en base.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
