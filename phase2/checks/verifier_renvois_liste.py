#!/usr/bin/env python3
"""Les renvois « l. N » de la page de tete tombent-ils encore juste ?   26/09/2026

POURQUOI CE FICHIER EXISTE. La page de tete de la liste navigue par NUMERO DE LIGNE,
et toute insertion ailleurs dans le document les decale en silence. Le 26/09, quatre
renvois etaient faux -- dont TROIS l'etaient deja : ils ne tombaient pas a cote, ils
tombaient ailleurs (C.9-couple pointait la section C.4). Et en les corrigeant j'ai
fait trois fois la meme erreur : decaler a la main apres avoir change la taille du
document.

LA REGLE : UN RENVOI NE SE CALCULE PAS, IL SE TROUVE. On cherche l'ancre par son
motif, on ecrit le numero trouve, on verifie que la ligne contient bien ce qu'on
annonce.

    python phase2/checks/verifier_renvois_liste.py              # controle seul
    python phase2/checks/verifier_renvois_liste.py --reparer    # corrige les numeros

Sort en 1 si un renvoi est faux (utilisable dans le run). Ne touche a RIEN d'autre
que les numeros de la page de tete.
"""

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
LISTE = RACINE / "notice" / "LISTE_TACHES_A_COCHER_2026-08-29.md"

# La page de tete s'arrete a ce titre : au-dela, c'est l'archive.
FIN_PAGE_DE_TETE = r"^## ✅ `L4-c` EST TERMIN"

# Chaque renvoi de la page de tete, avec le MOTIF de l'ancre qu'il designe.
# forme : (motif du renvoi dans la page de tete, motif de l'ancre dans le document)
RENVOIS = [
    (r"(E\.0-bis \(l\. )(\d+)(\))",        r"^\[ \] E\.0-bis "),
    (r"(D\.0 \(l\. )(\d+)(\))",            r"^\[~\] D\.0 "),
    (r"(C\.9-couple \(l\. )(\d+)(\))",     r"^\[ \] C\.9-couple "),
    (r"(C\.9-e \(l\. )(\d+)(\))",          r"^\s+\[x\] C\.9-e la « tache 22 »"),
    (r"(L4/C\.9 l\. )(\d+)( )",            r"^## 6\. C\.9 "),
    (r"(\(L4-c l\. )(\d+)(\))",            FIN_PAGE_DE_TETE),
    (r"(D\.0 l\. )(\d+)( )",               r"^\[~\] D\.0 "),
    (r"(l\. )(\d+)(\s+Rattrapage)",        r"^\[~\] G\.1 "),
    (r"(l\. )(\d+)(\s+gti-photo)",         r"^## 10bis\. FICHIERS"),
]

# CLAUDE.md navigue dans la MEME liste : ses renvois se decalent pareil.
PORTE = RACINE / "CLAUDE.md"
RENVOIS_PORTE = [
    (r"(`D\.0`, l\. )(\d+)( )", r"^\[~\] D\.0 "),
    (r"(section \*\*10bis\*\*, l\. )(\d+)(\))", r"^## 10bis\. FICHIERS"),
]

REPARER = "--reparer" in sys.argv


def main() -> int:
    brut = LISTE.read_text(encoding="utf-8", newline="")
    saut = "\r\n" if "\r\n" in brut else "\n"
    lignes = brut.split(saut)

    fin = next((i for i, l in enumerate(lignes, 1) if re.search(FIN_PAGE_DE_TETE, l)), None)
    if fin is None:
        print("⛔ fin de la page de tete introuvable -- controle non concluant")
        return 1

    tete = saut.join(lignes[: fin - 1])
    faux, repares = 0, 0
    print(f"{'renvoi':<16} {'ecrit':>6} {'trouve':>7}   ancre")
    print("-" * 74)

    for motif_renvoi, motif_ancre in RENVOIS:
        m = re.search(motif_renvoi, tete, re.M)
        if not m:
            print(f"{motif_ancre[:16]:<16} {'--':>6} {'--':>7}   ⚠ renvoi absent de la page de tete")
            continue
        ecrit = int(m.group(2))
        reel = next((i for i, l in enumerate(lignes, 1) if re.search(motif_ancre, l)), None)
        if reel is None:
            print(f"{m.group(1)[:16]:<16} {ecrit:>6} {'??':>7}   ⛔ ANCRE INTROUVABLE dans le document")
            faux += 1
            continue
        if reel == ecrit:
            print(f"{m.group(1)[:16]:<16} {ecrit:>6} {reel:>7}   OK")
            continue
        faux += 1
        etat = "-> corrige" if REPARER else "⛔ FAUX"
        print(f"{m.group(1)[:16]:<16} {ecrit:>6} {reel:>7}   {etat}")
        if REPARER:
            tete = re.sub(motif_renvoi, lambda g: g.group(1) + str(reel) + g.group(3), tete, count=1, flags=re.M)
            repares += 1

    # ⚠ ON ECRIT, MAIS ON NE SORT PAS : CLAUDE.md navigue dans la meme liste et doit
    # etre repare dans la MEME passe. Sortir ici obligeait a lancer --reparer deux fois,
    # et laissait la porte d'entree avec des numeros perimes entre les deux.
    if REPARER and repares:
        LISTE.write_text(tete + saut + saut.join(lignes[fin - 1:]), encoding="utf-8", newline="")

    # ── les renvois de CLAUDE.md, qui visent la MEME liste ────────────────────
    # ⚠ ON RELIT LA LISTE D'ABORD. Si on vient de la reparer, ses lignes ont bouge :
    # verifier CLAUDE.md contre la version d'AVANT lui donnerait des numeros perimes.
    # C'est le defaut que ce script est cense empecher -- il l'avait lui-meme.
    if REPARER and repares:
        lignes = LISTE.read_text(encoding="utf-8", newline="").split(saut)
    print("\nCLAUDE.md (il navigue dans la meme liste) :")
    tp = PORTE.read_text(encoding="utf-8", newline="")
    for motif_renvoi, motif_ancre in RENVOIS_PORTE:
        m = re.search(motif_renvoi, tp, re.M)
        if not m:
            print(f"  ⚠ renvoi absent : {motif_ancre}")
            continue
        ecrit = int(m.group(2))
        reel = next((i for i, l in enumerate(lignes, 1) if re.search(motif_ancre, l)), None)
        if reel == ecrit:
            print(f"  l. {ecrit:<6} OK")
        elif REPARER and reel:
            tp = re.sub(motif_renvoi, lambda g: g.group(1) + str(reel) + g.group(3),
                        tp, count=1, flags=re.M)
            PORTE.write_text(tp, encoding="utf-8", newline="")
            print(f"  l. {ecrit:<6} -> corrige en {reel}")
            faux += 1
        else:
            print(f"  l. {ecrit:<6} ⛔ FAUX (l'ancre est en {reel})")
            faux += 1

    if faux:
        print(f"\n⛔ {faux} renvoi(s) faux ou corrige(s). Relancer sans --reparer pour confirmer.")
        return 1
    print("\n✅ tous les renvois (liste + CLAUDE.md) tombent juste.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
