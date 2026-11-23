#!/usr/bin/env python
"""R9 : SES HUIT ECARTS, NOMMES UN PAR UN.     23/11/2026

    python -u -X utf8 phase2/checks/protocole_r9_les_huit_ecarts_2026-11-23.py

SON MOT DU 23/11 (16) : « LES HUIT, UNE PAR UNE, avec pour chacune la ligne que R9 donne, la ligne que la preuve donne, et
POURQUOI elles divergent. [...] Regarde si tes 8 ne sont pas justement la ou les honoraires collent par hasard. »
LE TEMOIN DE R9 (le meme que celui annonce) : sur tout le Sheet, une vraie piece que le gel d'UNE SEULE ligne nomme, dont
les honoraires = la Commission TTC de cette ligne -- la preuve stricte la donne-t-elle a CETTE ligne ? Les cas ou elle la
donne a une AUTRE ligne sont les ecarts. Pour chacun : la piece (genre, etat, date, montant, honoraires), la ligne du gel
et la ligne de la preuve (leurs Prix, Commission, dates, etat), LA PREUVE qui a tranche, et ce qui colle a chacune.
LECTURE SEULE (l'image du protocole, la coupe rejouee en memoire). Rien n'est ecrit.
"""
from __future__ import annotations

import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402


def dire(s: str = "") -> None:
    print(s, flush=True)


def nb(s):
    try:
        return round(float(str(s).replace(" ", "").replace(",", ".")))
    except ValueError:
        return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = P.socle()
    image = con.execute("select image from passage where id=(select max(id) from passage)").fetchone()[0]
    con.close()
    I = P.Image(P.IMAGES / image)
    D = I.D
    ecarts, total = [], 0
    for b in sorted(D.lignes_bien):
        lignes_b = set(D.lignes_bien[b])
        if not D.par_bien.get(b):
            continue
        S = {q: I.pieces[q]["app_chaine_id"] for q in D.par_bien.get(b, [])}
        r = K.couper_le_bien(D, b, lignes_b, S, sorted(D.par_bien.get(b, [])), P.A_PART_PAR_DECISION)
        for i in sorted(lignes_b):
            com = nb(D.case(i, "Commission TTC"))
            for g in I.gel_par_ligne.get(i, []):
                a = int(g["piece"])
                if a not in D.REG or D.REG[a]["bien"] != b or I.nature.get(a) != PC.VRAIE:
                    continue
                if [x for x in I.gel_par_piece.get(a, []) if x != i]:
                    continue
                h = D.REG[a]["hon"]
                if h is None or com is None or round(h) != com or a not in r["va"]:
                    continue
                total += 1
                if i not in r["va"][a]:
                    ecarts.append((b, a, i, sorted(r["va"][a]), r["preuve"].get(a, "")))
    dire("LE TEMOIN DE R9 (image %s) : %d pieces tranchees par la preuve ; %d donnees a une AUTRE ligne que celle du gel"
         % (image, total, len(ecarts)))
    for n, (b, a, i, js, quoi) in enumerate(ecarts, 1):
        reg = D.REG[a]
        dire("\n%d. bien %s, piece %d : %s %s du %s, montant %s, honoraires %s (dossier %s)" % (
            n, b, a, reg["genre"], reg["etat"], reg["date"] or "?", reg["montant"], reg["hon"],
            I.pieces[a]["app_dossier_numero"]))
        dire("   LA PREUVE STRICTE la donne a %s -- %s" % ("+".join(js), P.preuve_nommee(I, a, frozenset(js), quoi)[:200]))
        for x, qui in [(i, "LE GEL (R9)")] + [(j, "LA PREUVE") for j in js]:
            cols = {c: D.case(x, c).strip() for c in ("Etat Actuel", "Offre Achat", "Compromis", "Vente Fixée", "Prix",
                                                      "Commission TTC", "Négociateur 1")}
            colle = []
            for c in K.COLS_DATE.get(reg["genre"], []):
                if reg["date"] and K.d_sheet(D.case(x, c)) == reg["date"]:
                    colle.append("date = %s" % c)
            if reg["montant"] is not None and nb(cols["Prix"]) == round(reg["montant"]):
                colle.append("montant = Prix")
            if nb(cols["Commission TTC"]) == round(reg["hon"]):
                colle.append("honoraires = Commission")
            if D.touche_ph(a, x):
                colle.append("PRIX + HONORAIRES (la preuve)")
            dire("   %-12s %s : %s | colle : %s" % (qui, x, " . ".join("%s %s" % (k, v) for k, v in cols.items() if v),
                                                    ", ".join(colle) or "rien"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
