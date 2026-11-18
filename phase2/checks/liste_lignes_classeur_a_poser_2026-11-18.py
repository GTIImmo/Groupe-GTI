#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LA LISTE DES LIGNES DU CLASSEUR QU'IL A TRANCHEES.                18/11/2026

    .venv\Scripts\python.exe -X utf8 phase2\checks\liste_lignes_classeur_a_poser_2026-11-18.py

⛔ LECTURE SEULE. Il croise les 43 lignes de la page d'arbitrage
  (notice/LIGNES_A_TRANCHER_ECRAN_2026-11-18.json) avec SES 41 decisions, et ecrit
  notice/LISTE_LIGNES_CLASSEUR_A_POSER_2026-11-18.md -- une liste par famille, triee
  par numero de ligne du classeur.

⭐⭐ LA RAISON D'ETRE DE CE SCRIPT : la page d'arbitrage enregistrait UN CLIC PAR
  IDENTIFIANT alors qu'elle affichait 43 LIGNES -- NEFHS7JI et 1ESJE28Q en portent
  DEUX chacun. Donc 41 decisions ne couvrent pas 43 lignes, et il faut le DIRE ligne
  par ligne au lieu d'annoncer un total. Voir la memoire
  compte-d-identifiants-n-est-pas-un-compte-de-lignes.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
LIGNES = RACINE / "notice" / "LIGNES_A_TRANCHER_ECRAN_2026-11-18.json"
SORTIE = RACINE / "notice" / "LISTE_LIGNES_CLASSEUR_A_POSER_2026-11-18.md"
#: ses 41 verdicts, releves dans la base de la page d'arbitrage (collection `decisions`)
DECISIONS = Path(
    r"C:\Users\admin\AppData\Local\Temp\claude\C--Hektor"
    r"\4959e387-790b-43cc-8053-a7faae3d6774\scratchpad\ses_decisions.json"
)

#: ce que l'audit du 18/11 a tranche sur les 6 qu'il avait ecartees
VERDICT_AUDIT = {
    "1ESJE28Q": "LIEN FAUX -- le bon bien est l'annonce 9194 (mandants RECAMIER), SANS transaction",
    "8Q3LHGZ4": "LIEN FAUX -- le bon bien est l'annonce 46472 (mandants ROQUES), SANS transaction",
    "53ZS73KW": "BON BIEN, MAUVAISE AFFAIRE -- nous avons CHAPUIS 2026, le Sheet decrit GIBERT 2024",
    "TR42PT5H": "LIEN FAUX -- le bon dossier est la chaine 27195 (MORAND ZIMMER / BELONJE BIEL)",
    "74IL9C8F": "APPARIEMENT CERTAIN -- compromis au JOUR EXACT ; l'offre dit 2002 pour 2022",
    "QH6672TZ": "APPARIEMENT CERTAIN -- vente au JOUR EXACT ; l'offre est a 366 JOURS PILE",
}

ETATS_FR = {
    "active": "active", "accepted": "acceptee", "cancelled": "ANNULEE",
    "refused": "refusee", "None": "sans etat", None: "sans etat",
}


def transactions(ligne: dict) -> str:
    """Les transactions de NOTRE chaine, resumees par genre et par etat.

    ⭐ C'est la question n1 de la pose : sur LAQUELLE poser ? Sa decision du 17/11
      sur C2 ecartait les annulees, et 14 des 78 visees le sont.
    """
    app = ligne.get("app") or []
    if not app:
        return "AUCUNE transaction"
    bouts = []
    for t in app:
        genre = str(t.get("k") or "?")
        etat = ETATS_FR.get(t.get("s"), str(t.get("s")))
        bouts.append("%s %s (%s)" % (genre, t.get("id"), etat))
    return " . ".join(bouts)


def bloc(ligne: dict, verdict: str, commentaire: str) -> list[str]:
    out = [
        "   ligne %-5s  %-9s  mandat %-7s  %s"
        % (ligne["ligne"], ligne["id"], ligne.get("mandat") or "-",
           (ligne.get("ville") or "").strip(" -")[:52]),
        "      le classeur %-12s  nous %-12s  ecart %s"
        % (ligne.get("classeur") or "-", ligne.get("nous") or "-", ligne.get("ecart") or "-"),
        "      %s" % transactions(ligne),
    ]
    if commentaire.strip():
        out.append("      \u2b50 SON MOT : \u00ab %s \u00bb" % commentaire.strip())
    for p in (ligne.get("pourquoi") or [])[:1]:
        out.append("      %s" % str(p)[:96])
    if ligne["id"] in VERDICT_AUDIT:
        out.append("      \u26d4 L'AUDIT DU 18/11 : %s" % VERDICT_AUDIT[ligne["id"]])
    return out


def main() -> int:
    lignes = json.loads(LIGNES.read_text("utf-8"))
    dec = json.loads(DECISIONS.read_text("utf-8"))

    ids = [str(x["id"]) for x in lignes]
    doubles = sorted(k for k, v in Counter(ids).items() if v > 1)

    poser, ecartees, sans = [], [], []
    for x in lignes:
        d = dec.get(str(x["id"]))
        if d is None:
            sans.append((x, "", ""))
            continue
        verdict = d[0] if isinstance(d, list) else str(d)
        mot = (d[1] if isinstance(d, list) and len(d) > 1 else "") or ""
        (poser if verdict == "classeur" else ecartees).append((x, verdict, mot))

    par_famille: dict[str, list] = {}
    for x, v, m in poser:
        par_famille.setdefault(x.get("famille") or "?", []).append((x, v, m))

    L: list[str] = []
    L.append("# LES LIGNES DU CLASSEUR QU'IL A TRANCHEES -- 18/11/2026")
    L.append("")
    L.append("> \u26d4\u26d4 **RIEN N'EST POSE EN BASE.** Cette liste est l'etat de son arbitrage de")
    L.append("> la nuit du 17 au 18/11, ligne par ligne. La pose est une ECRITURE EN")
    L.append("> PRODUCTION : elle attend son \u00ab vas-y \u00bb.")
    L.append(">")
    L.append("> Source : `notice/LIGNES_A_TRANCHER_ECRAN_2026-11-18.json` (les 43 lignes")
    L.append("> affichees) croise avec ses 41 decisions (collection `decisions` de la page).")
    L.append("> Regenerer : `phase2/checks/liste_lignes_classeur_a_poser_2026-11-18.py`.")
    L.append("")
    L.append("```")
    L.append("   LE COMPTE, ET IL NE TOMBE PAS ROND :")
    L.append("     %d lignes affichees  pour  %d identifiants" % (len(lignes), len(set(ids))))
    L.append("     %d verdicts \u00ab le classeur a raison \u00bb  ->  %d LIGNES" % (
        len({x['id'] for x, _, _ in poser}), len(poser)))
    L.append("     %d ecartees (\u00ab rien \u00bb)             ->  %d LIGNES" % (
        len({x['id'] for x, _, _ in ecartees}), len(ecartees)))
    L.append("   \u26d4 LA CAUSE : %s portent DEUX lignes chacun"
             % " et ".join(doubles))
    L.append("     (une commission ET une date d'offre) et la page n'enregistrait")
    L.append("     QU'UN CLIC PAR IDENTIFIANT.")
    L.append("```")
    L.append("")

    for fam in sorted(par_famille, key=lambda f: -len(par_famille[f])):
        items = sorted(par_famille[fam], key=lambda t: t[0]["ligne"])
        L.append("## \u2705 \u00ab LE CLASSEUR A RAISON \u00bb -- %s (%d lignes)" % (fam.upper(), len(items)))
        L.append("")
        L.append("```")
        for x, v, m in items:
            L.extend(bloc(x, v, m))
            L.append("")
        L.append("```")
        L.append("")

    #: \u2b50\u2b50 LA SECTION QUI SERT LE PLUS : ou son verdict contredit la recommandation.
    #:   Ce n'est pas un reproche -- c'est LE SHEET QUI FAIT FOI (sa regle) -- mais une
    #:   divergence appuyee sur un bareme doit etre VUE avant la pose.
    contre = []
    for x in lignes:
        r, d = str(x.get("reco") or ""), dec.get(str(x["id"]))
        if not d:
            continue
        verdict = d[0] if isinstance(d, list) else str(d)
        if verdict == "classeur" and r.startswith("NOUS avons raison"):
            contre.append((x, "il a suivi LE CLASSEUR quand la reco disait NOUS"))
        elif verdict == "rien" and r.startswith("le CLASSEUR a raison"):
            contre.append((x, "il a ECARTE quand la reco disait LE CLASSEUR"))

    L.append("## \u26a0\u26a0 LES %d LIGNES OU SON VERDICT CONTREDIT LA RECOMMANDATION" % len(contre))
    L.append("")
    L.append("```")
    for x, pourquoi in sorted(contre, key=lambda t: t[0]["ligne"]):
        L.append("   ligne %-5s  %-9s  %-14s  %s"
                 % (x["ligne"], x["id"], x.get("famille"), pourquoi))
        L.append("      le classeur %-12s  nous %-12s  ecart %s"
                 % (x.get("classeur") or "-", x.get("nous") or "-", x.get("ecart") or "-"))
        for p in (x.get("pourquoi") or []):
            L.append("      %s" % str(p)[:96])
        if x["id"] in VERDICT_AUDIT:
            L.append("      \u26d4 L'AUDIT DU 18/11 : %s" % VERDICT_AUDIT[x["id"]])
        L.append("")
    L.append("```")
    L.append("")
    L.append("```")
    L.append("   ET CE QUE SES 35 \u00ab classeur \u00bb RECOUVRENT, PAR RECOMMANDATION :")
    rep = Counter(str(x.get("reco") or "")[:52] for x in lignes
                  if (dec.get(str(x["id"])) or [""])[0] == "classeur")
    for k, n in rep.most_common():
        L.append("     %-54s %d" % (k, n))
    L.append("   \u2b50 Il a donc tranche POUR LE CLASSEUR sur %d lignes ou la page ne"
             % sum(n for k, n in rep.items()
                   if k.startswith("LES DEUX") or k.startswith("a regarder")))
    L.append("     recommandait RIEN (\u00ab les deux sont plausibles \u00bb, \u00ab a regarder \u00bb).")
    L.append("```")
    L.append("")

    L.append("## \u26d4\u26d4 LA LIGNE QUI N'EST PAS TRANCHEE")
    L.append("")
    L.append("```")
    for ident in doubles:
        verdict = dec.get(ident)
        v = verdict[0] if isinstance(verdict, list) else str(verdict)
        fams = [x.get("famille") for x in lignes if x["id"] == ident]
        L.append("   %-9s un seul clic \u00ab %s \u00bb pour %d lignes : %s"
                 % (ident, v, len(fams), " + ".join(map(str, fams))))
        for x in lignes:
            if x["id"] != ident:
                continue
            L.append("      %-14s classeur %-12s nous %-12s ecart %s"
                     % (x.get("famille"), x.get("classeur") or "-",
                        x.get("nous") or "-", x.get("ecart") or "-"))
        if v == "classeur":
            L.append("      \u26d4 ON NE SAIT PAS s'il visait l'une, l'autre, ou les deux.")
        else:
            L.append("      \u2b50 \u00ab rien \u00bb couvre les deux lignes sans ambiguite.")
        L.append("")
    L.append("```")
    L.append("")

    L.append("## \u2b1c LES LIGNES ECARTEES, ET CE QUE L'AUDIT EN DIT (%d)" % len(ecartees))
    L.append("")
    L.append("```")
    for x, v, m in sorted(ecartees, key=lambda t: t[0]["ligne"]):
        L.extend(bloc(x, v, m))
        L.append("")
    L.append("```")

    if sans:
        L.append("")
        L.append("## \u26d4 LIGNES SANS AUCUNE DECISION (%d)" % len(sans))
        L.append("")
        L.append("```")
        for x, _, _ in sans:
            L.append("   ligne %-5s %-9s %s" % (x["ligne"], x["id"], x.get("famille")))
        L.append("```")

    #: \u26a0 les documents du projet sont en CRLF -- voir la memoire
    #:   fins-de-ligne-docs-mesurer-en-python
    SORTIE.write_bytes("\r\n".join(L).encode("utf-8") + b"\r\n")
    print("ecrit : %s" % SORTIE)
    print("  %d octets, %d lignes" % (SORTIE.stat().st_size, len(L)))
    print("  %d lignes a poser . %d ecartees . %d sans decision"
          % (len(poser), len(ecartees), len(sans)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
