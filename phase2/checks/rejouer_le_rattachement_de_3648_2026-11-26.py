#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LE RATTACHEMENT 3648 -> 3647, REJOUE PAR LA VRAIE FONCTION DE NUIT SUR UNE COPIE EN MEMOIRE -- ⛔ RIEN N'EST ECRIT.

    python -X utf8 -u phase2\checks\rejouer_le_rattachement_de_3648_2026-11-26.py

SON MOT (26/11) : « Accord pour la ligne de rattachement -- montre-moi son texte exact avant la nuit, je la relis. » ;
« demain matin, ne me donne pas le compte rendu de la nuit : donne-moi le temoin [...] Mesure, pas rapporte. »

CE QU'IL FAIT (le patron de temps4_rattachements_10_menages_2026-11-19.py) : phase2.sqlite en mode=ro, la SEULE table que
le chainage lit et ecrit (app_affaire_ledger) copiee en memoire ; la vraie fonction recalculer_les_chaines jouee deux fois :
    AVANT   le fichier des rattachements tel qu'il est (16 decisions)       -> doit rendre la base, 0 ecart
    APRES   le meme fichier + LA LIGNE PROPOSEE, dans un fichier TEMPORAIRE (le vrai n'est jamais ouvert en ecriture)
LES TEMOINS
    FICHIER   le vrai fichier a 16 decisions, et 3648 n'y est pas
    BASE      AVANT = la base (0 ecart), sinon la comparaison ne prouve rien
    POSITIF   3648 rejoint la chaine de 3647 et 3650, numero 3647 ; « [M] rattachement decide a la main » passe de 16 a 17
    INVERSE   AUCUNE autre transaction ne change de chaine (seule 3648) ; 427UDDSF garde {3646, 3649}
    GARDES    ni deux ventes ni deux compromis vivants de plus dans un dossier
    ETIQUETTE la fusion garde l'etiquette de la plus petite piece : 3647 = 42dd4d66 (D2024-0511) ; D2024-0306 n'a plus de piece
Sortie : 0 vert . 2 un temoin a echoue.
"""
from __future__ import annotations

import contextlib
import io
import os
import sqlite3
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import phase2.sync.affaire_ledger as al  # noqa: E402

BASE = RACINE / "phase2" / "phase2.sqlite"
SOURCE, CIBLE, BIEN = 3648, 3647, 8395
#: ⭐ 26/11, son mot : « Ajoute seulement un marqueur en tete du commentaire, « [refus 11/11] », pour qu'on retrouve d'un seul
#:   coup toutes les reparations nees de cette operation quand on ouvrira ce chantier pour lui-meme. »
MARQUEUR = "[refus 11/11]"
LIGNE_PROPOSEE = ("3648;3647;8395;2026-11-26;[refus 11/11] POTTIER -- l'offre du 23/08/2024 (acceptee, puis refusee le 11/11/2026 par "
                  "notre rattrapage_cascade_annulation) rejoint son compromis 3647 et sa vente 3650 : la ligne 9Q0FHAKK du "
                  "classeur (passage 82) -- D2024-0306 fusionne dans D2024-0511")
DECISIONS_ATTENDUES = 16


def copie() -> sqlite3.Connection:
    src = sqlite3.connect(f"file:{BASE.as_posix()}?mode=ro", uri=True)
    mem = sqlite3.connect(":memory:")
    sql = src.execute("select sql from sqlite_master where type='table' and name=?", (al.LEDGER_TABLE,)).fetchone()[0]
    mem.execute(sql)
    cols = [r[1] for r in src.execute("pragma table_info(%s)" % al.LEDGER_TABLE)]
    mem.executemany("insert into %s (%s) values (%s)" % (al.LEDGER_TABLE, ", ".join(cols), ", ".join("?" * len(cols))),
                    src.execute("select %s from %s" % (", ".join(cols), al.LEDGER_TABLE)))
    for (s,) in src.execute("select sql from sqlite_master where type='index' and tbl_name=? and sql is not null",
                            (al.LEDGER_TABLE,)):
        mem.execute(s)
    mem.commit()
    src.close()
    return mem


def rejouer(fichier: Path) -> tuple[dict, dict]:
    d_origine = al.FICHIER_RATTACHEMENTS
    al.FICHIER_RATTACHEMENTS = fichier
    try:
        con = copie()
        tampon = io.StringIO()
        with contextlib.redirect_stdout(tampon):
            compte = al.recalculer_les_chaines(con)
        chaines = {int(a): int(c) for a, c in con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {al.LEDGER_TABLE}")}
        con.close()
    finally:
        al.FICHIER_RATTACHEMENTS = d_origine
    return chaines, compte


def main() -> int:
    echecs = []
    print("LA LIGNE PROPOSEE (a sa relecture, elle n'est PAS dans le vrai fichier) :\n   %s\n" % LIGNE_PROPOSEE)
    assert ";" not in LIGNE_PROPOSEE.split(";", 4)[4], "un point-virgule dans le pourquoi casserait la lecture"
    assert LIGNE_PROPOSEE.split(";", 4)[4].startswith(MARQUEUR + " "), "le marqueur doit ouvrir le commentaire"
    assert LIGNE_PROPOSEE.isascii(), "aucun accent dans la ligne"
    decisions = al.lire_rattachements_manuels()
    print("FICHIER : %d decisions (attendu %d) ; 3648 deja dedans : %s"
          % (len(decisions), DECISIONS_ATTENDUES, any(s == SOURCE for s, _c, _b, _p in decisions)))
    if len(decisions) != DECISIONS_ATTENDUES or any(s == SOURCE for s, _c, _b, _p in decisions):
        echecs.append("le vrai fichier")
    texte = al.FICHIER_RATTACHEMENTS.read_text(encoding="utf-8-sig")
    with tempfile.TemporaryDirectory() as tmp:
        avec = Path(tmp) / "rattachements_avec_3648.csv"
        avec.write_text(texte.rstrip("\r\n") + "\n" + LIGNE_PROPOSEE + "\n", encoding="utf-8")
        d_o = al.FICHIER_RATTACHEMENTS
        al.FICHIER_RATTACHEMENTS = avec
        try:
            lu = al.lire_rattachements_manuels()
        finally:
            al.FICHIER_RATTACHEMENTS = d_o
        print("   le fichier temporaire se lit : %d decisions, dont %s" % (len(lu), [d[:3] for d in lu if d[0] == SOURCE]))
        if len(lu) != DECISIONS_ATTENDUES + 1 or not any(d[:3] == (SOURCE, CIBLE, BIEN) for d in lu):
            echecs.append("la ligne proposee ne se lit pas")
        pq = [d[3] for d in lu if d[0] == SOURCE]
        print("   son commentaire, tel que le LECTEUR le rend : %r" % (pq[0][:60] + "..." if pq else None))
        if not pq or not pq[0].startswith(MARQUEUR + " "):
            echecs.append("le marqueur n'ouvre pas le commentaire lu")
        apres, compte_apres = rejouer(avec)
    avant, compte_avant = rejouer(al.FICHIER_RATTACHEMENTS)

    src = sqlite3.connect(f"file:{BASE.as_posix()}?mode=ro", uri=True)
    info = {}
    for a, bien, k, s, ch, u, num, pres, dn in src.execute(
            f"SELECT app_affaire_id, hektor_annonce_id, kind, state, app_chaine_id, app_dossier_uuid, hektor_affaire_id, "
            f"present_in_hektor, app_dossier_numero FROM {al.LEDGER_TABLE}"):
        info[int(a)] = {"bien": str(bien), "genre": k, "etat": (s or "").lower(), "base": int(ch) if ch is not None else None,
                        "uuid": u, "numero": dn,
                        "effacee": bool(str(num or "").strip()) and str(pres) in ("0", "false", "False")}
    src.close()
    ecart = [a for a in avant if avant[a] != info[a]["base"]]
    print("\nBASE : AVANT (fichier tel quel) contre la base : %d ecart(s) (attendu 0) %s" % (len(ecart), ecart[:10]))
    if ecart:
        echecs.append("AVANT != base")
    bougent = sorted(a for a in avant if avant[a] != apres[a])
    print("POSITIF : 3648 -> chaine %s (avant %s) ; 3647 -> %s ; 3650 -> %s" % (apres[SOURCE], avant[SOURCE], apres[CIBLE], apres[3650]))
    if not (apres[SOURCE] == apres[CIBLE] == apres[3650] == CIBLE):
        echecs.append("3648 pas reunie a 3647")
    k = "[M] rattachement decide a la main"
    print("   « %s » : %s -> %s (attendu +1)" % (k, compte_avant.get(k), compte_apres.get(k)))
    if (compte_apres.get(k) or 0) != (compte_avant.get(k) or 0) + 1:
        echecs.append("compteur [M]")
    for kk in sorted(set(compte_avant) | set(compte_apres)):
        if kk.startswith("[M]") and kk != k and compte_avant.get(kk) != compte_apres.get(kk):
            print("   ⚠ %s : %s -> %s" % (kk, compte_avant.get(kk), compte_apres.get(kk)))
            echecs.append(kk)
    print("INVERSE : transactions qui changent de chaine : %d %s (attendu 1, la seule 3648)" % (len(bougent), bougent[:10]))
    if bougent != [SOURCE]:
        echecs.append("temoin inverse")
    print("   427UDDSF : 3646 -> %s, 3649 -> %s (attendu 3646 / 3646)" % (apres[3646], apres[3649]))
    if not (apres[3646] == apres[3649] == 3646):
        echecs.append("427UDDSF")

    def gardes(ch):
        par = defaultdict(list)
        for a, c in ch.items():
            if not info[a]["effacee"]:
                par[c].append(info[a])
        return (sum(1 for m in par.values() if sum(1 for x in m if x["genre"] == "vente") >= 2),
                sum(1 for m in par.values() if sum(1 for x in m if x["genre"] == "compromis"
                                                   and x["etat"] not in al.ETATS_COMPROMIS_MORTS) >= 2))
    print("GARDES : deux ventes / deux compromis vivants : avant %s, apres %s" % (gardes(avant), gardes(apres)))
    if gardes(avant) != gardes(apres):
        echecs.append("gardes")
    groupe = sorted(a for a, c in apres.items() if c == apres[SOURCE])
    gagnante = info[min(groupe)]
    print("ETIQUETTE : la chaine %s = %s ; la plus petite piece %d porte %s (%s) -- 3648 portait %s (%s)"
          % (apres[SOURCE], groupe, min(groupe), str(gagnante["uuid"])[:8], gagnante["numero"],
             str(info[SOURCE]["uuid"])[:8], info[SOURCE]["numero"]))
    if not str(gagnante["uuid"]).startswith("42dd4d66"):
        echecs.append("etiquette gardee")
    reste_0306 = [a for a, c in apres.items() if info[a]["numero"] == "D2024-0306" and a != SOURCE]
    print("   D2024-0306 : pieces qui le porteraient encore apres la fusion : %d %s" % (len(reste_0306), reste_0306))
    if reste_0306:
        echecs.append("D2024-0306 garde une piece")
    if echecs:
        print("\n⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs)
        return 2
    print("\n✅ TOUT EST VERT : seule 3648 bouge, elle rejoint 3647 et 3650, l'etiquette gardee est D2024-0511")
    return 0


if __name__ == "__main__":
    sys.exit(main())
