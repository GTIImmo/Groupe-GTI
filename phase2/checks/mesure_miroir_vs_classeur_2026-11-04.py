# -*- coding: utf-8 -*-
"""SA QUESTION DU 04/11 : « les charges presentes dans le MIROIR ont-elles ete
integrees a ces colonnes, comme celles du Sheet ? »

REPONSE COURTE : NON. Seules les 837 du classeur sont posees.

CE SCRIPT MESURE CE QUE CA COUTE DE NE PAS L'AVOIR FAIT, et il le fait avec un
echantillon DEUX FOIS PLUS GRAND que le juge du 03/11 :
  . le juge comparait Hektor au classeur sur 380 lignes comparables
  . ici on compare Hektor aux 837 lignes REELLEMENT POSEES, mandat par mandat

⭐ ET IL REPOND A UNE NUANCE QUE J'AVAIS MAL POSEE LE 03/11 :
  le juge a montre que Hektor n'apporte que +1,3 point SUR LES LIGNES QUE LE
  CLASSEUR COUVRE DEJA. Il n'a JAMAIS montre que Hektor etait inutile LA OU LE
  CLASSEUR EST MUET -- et c'est 23 737 mandats sur 24 574.
  Du vide ne vaut pas 95 % : il ne vaut rien.

LECTURE SEULE : base locale en mode=ro, aucun appel Hektor, aucune ecriture.
"""
from __future__ import annotations

import io
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = "file:%s?mode=ro" % (RACINE / "data" / "hektor.sqlite").as_posix()
POSEES = RACINE / "supabase" / "patch_charge_classeur_2026-11-04_DONNEES.sql"
SORTIE = RACINE / "notice" / "MESURE_MIROIR_VS_CLASSEUR_2026-11-04.md"

RE_V = re.compile(r"Honoraires vendeur ou bailleur montant\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.I)
RE_A = re.compile(r"Honoraires acqu\w*reur ou locataire\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.I)

# ⛔ RETIREES APRES COUP (conflit du classeur) : elles ne font pas partie des 837.
RETIREES = {("46338", "17322"), ("47174", "17639")}


def charge_du_miroir() -> dict[str, str]:
    """La charge que HEKTOR nous livre, par annonce, depuis le texte libre.

    ⚠ On itere au CURSEUR : raw_json pese 775 Mo, un fetchall() serait fatal.
    ⚠ On prend la DERNIERE occurrence : le bloc est un HISTORIQUE (jusqu'a 6
      lignes), et la charge y bascule parfois (mesure du 03/11).
    """
    out: dict[str, str] = {}
    con = sqlite3.connect(BASE, uri=True)
    try:
        cur = con.cursor()
        for ann, raw in cur.execute(
                "select hektor_annonce_id, raw_json from hektor_annonce_detail"
                " where raw_json like '%onoraires vendeur ou bailleur montant%'"
                "    or raw_json like '%onoraires acqu%reur ou locataire%'"):
            if not raw:
                continue
            v = [float(x) for x in RE_V.findall(raw)]
            a = [float(x) for x in RE_A.findall(raw)]
            dv = v[-1] if v else 0.0
            da = a[-1] if a else 0.0
            if dv > 0 and da > 0:
                out[str(ann).strip()] = "les_deux"
            elif dv > 0:
                out[str(ann).strip()] = "vendeur"
            elif da > 0:
                out[str(ann).strip()] = "acquereur"
        return out
    finally:
        con.close()


def main() -> int:
    posees: dict[tuple[str, str], str] = {}
    t = io.open(POSEES, encoding="utf-8").read()
    for ann, man, ch in re.findall(
            r"\('([^']+)', '([^']+)', 'charge_commission', '(vendeur|acquereur)'", t):
        if (ann, man) not in RETIREES:
            posees[(ann, man)] = ch
    print("posees (classeur, hors les 2 conflits retires) : %d" % len(posees))

    mir = charge_du_miroir()
    print("annonces dont HEKTOR porte une charge               : %d" % len(mir))
    rep = Counter(mir.values())
    for k in sorted(rep):
        print("    %-10s %d" % (k, rep[k]))

    # ── 1. HEKTOR CONTRE LE CLASSEUR, sur les 837 reellement posees ──────────
    print()
    print("=" * 72)
    print("1. HEKTOR CONTRE LE CLASSEUR -- echantillon 2x celui du juge")
    print("=" * 72)
    comp = {}
    for (ann, man), ch in posees.items():
        h = mir.get(ann)
        if h in ("vendeur", "acquereur"):
            comp[(ann, man)] = (ch, h)
    accord = sum(1 for c, h in comp.values() if c == h)
    muet = len(posees) - len([1 for (a, m) in posees if mir.get(a)])
    deux = len([1 for (a, m) in posees if mir.get(a) == "les_deux"])
    print("  comparables (Hektor tranche)        %d" % len(comp))
    print("  Hektor MUET sur l annonce           %d" % muet)
    print("  Hektor porte LES DEUX cases         %d" % deux)
    if comp:
        print("  ACCORD                              %d  = %.1f %%"
              % (accord, 100.0 * accord / len(comp)))
        tv = sum(1 for c, _ in comp.values() if c == "vendeur")
        print("  « toujours vendeur » aurait juste   %d  = %.1f %%"
              % (tv, 100.0 * tv / len(comp)))
        print("  -> le gain REEL de Hektor           %+.1f point"
              % (100.0 * accord / len(comp) - 100.0 * tv / len(comp)))
        # la classe RARE, celle qui compte
        dit_a = [(k, v) for k, v in comp.items() if v[1] == "acquereur"]
        juste_a = [1 for k, v in dit_a if v[0] == "acquereur"]
        vrais_a = [1 for k, v in comp.items() if v[0] == "acquereur"]
        print()
        print("  LA CLASSE RARE (acquereur) :")
        print("    Hektor dit acquereur                %d" % len(dit_a))
        print("    et il a raison                      %d  (precision %.1f %%)"
              % (len(juste_a), 100.0 * len(juste_a) / max(len(dit_a), 1)))
        print("    acquereurs reels au classeur        %d  (rappel %.1f %%)"
              % (len(vrais_a), 100.0 * len(juste_a) / max(len(vrais_a), 1)))
        desaccords = sorted(k for k, v in comp.items() if v[0] != v[1])
    else:
        desaccords = []

    # ── 2. CE QUE LE MIROIR COUVRIRAIT EN PLUS ──────────────────────────────
    print()
    print("=" * 72)
    print("2. CE QUE LE MIROIR COUVRIRAIT, LA OU LE CLASSEUR EST MUET")
    print("=" * 72)
    annonces_posees = {a for (a, m) in posees}
    en_plus = {a: h for a, h in mir.items()
               if a not in annonces_posees and h in ("vendeur", "acquereur")}
    print("  annonces que Hektor tranche et que le classeur ne couvre PAS : %d"
          % len(en_plus))
    r2 = Counter(en_plus.values())
    for k in sorted(r2):
        print("      %-10s %d" % (k, r2[k]))
    print("  annonces ou Hektor porte LES DEUX cases (indecidable)        : %d"
          % sum(1 for a, h in mir.items() if a not in annonces_posees and h == "les_deux"))

    # ── LE RAPPORT ──────────────────────────────────────────────────────────
    r = []
    r.append("# LE MIROIR A-T-IL ETE INTEGRE ? -- mesure du 04/11/2026")
    r.append("")
    r.append("**Sa question** : *« est-ce que les charges presentes dans le miroir ont ete")
    r.append("integrees a ces colonnes comme celle du sheet ? »*")
    r.append("")
    r.append("**NON.** Seules les **837 lignes du classeur** sont posees. Le miroir (ce que")
    r.append("Hektor nous descend) n'a **rien** donne au registre des mandats.")
    r.append("")
    r.append("## 1. Hektor contre le classeur, sur les 837 reellement posees")
    r.append("")
    r.append("Echantillon **deux fois plus grand** que le juge du 03/11 (380 lignes).")
    r.append("")
    r.append("```")
    r.append("posees depuis le classeur           %d" % len(posees))
    r.append("comparables (Hektor tranche)        %d" % len(comp))
    r.append("Hektor MUET sur l annonce           %d" % muet)
    r.append("Hektor porte LES DEUX cases         %d" % deux)
    if comp:
        r.append("ACCORD                              %d = %.1f %%"
                 % (accord, 100.0 * accord / len(comp)))
        tv = sum(1 for c, _ in comp.values() if c == "vendeur")
        r.append("« toujours vendeur » juste          %d = %.1f %%"
                 % (tv, 100.0 * tv / len(comp)))
        r.append("gain reel de Hektor                 %+.1f point"
                 % (100.0 * accord / len(comp) - 100.0 * tv / len(comp)))
    r.append("```")
    r.append("")
    if desaccords:
        r.append("### Les desaccords, NOMMES")
        r.append("")
        r.append("```")
        for k in desaccords[:80]:
            r.append("%s / %s : classeur %s, Hektor %s"
                     % (k[0], k[1], comp[k][0], comp[k][1]))
        r.append("```")
        r.append("")
    r.append("## 2. Ce que le miroir couvrirait EN PLUS")
    r.append("")
    r.append("⭐ **La nuance que j'avais mal posee le 03/11** : le juge a montre que Hektor")
    r.append("n'apporte que +1,3 point **la ou le classeur parle deja**. Il n'a jamais")
    r.append("montre que Hektor etait inutile **la ou le classeur est MUET**.")
    r.append("Du vide ne vaut pas 95 % : il ne vaut rien.")
    r.append("")
    r.append("```")
    r.append("annonces que Hektor tranche, hors classeur   %d" % len(en_plus))
    for k in sorted(r2):
        r.append("    %-10s %d" % (k, r2[k]))
    r.append("les DEUX cases (indecidable, a ecarter)      %d"
             % sum(1 for a, h in mir.items() if a not in annonces_posees and h == "les_deux"))
    r.append("```")
    r.append("")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    io.open(SORTIE, "w", encoding="utf-8", newline="\n").write("\n".join(r))
    print()
    print("  rapport : %s" % SORTIE)
    print("FIN -- lecture seule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
