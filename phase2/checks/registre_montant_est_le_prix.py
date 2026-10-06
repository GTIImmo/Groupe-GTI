"""CONTROLE -- le registre dit-il le PRIX la ou il ecrivait un montant ?  06/10/2026

Le montant que Hektor rend dans `mandats[]` est resolu sur l'identifiant NU du
mandat, ambigu entre les familles HEKTOR et PROTEXA : 88 lignes portaient le
montant d'un AUTRE bien. Le 05/10 on l'avait MASQUE -- une rustine, qui couvrait
`mandat_montant` et laissait passer deux autres chemins. Depuis le 06/10 on met
LA VRAIE VALEUR : le prix de l'annonce, le meme que la colonne `prix`.

CE CONTROLE N'IMITE RIEN : il appelle `build_mandat_register_rows`, la fonction
du run, et lit ce qu'elle produit.
    ➡ memoire `eprouver-c-est-executer-le-code`

Il n'ecrit RIEN : connexion en lecture seule.

    python phase2/checks/registre_montant_est_le_prix.py
    python phase2/checks/registre_montant_est_le_prix.py --lignes 3000   # plus vite

CE QUI DOIT ETRE VRAI
    ① les TROIS chemins disent le meme chiffre que la colonne `prix` :
         mandat_montant · register_history_json[version courante].montant
         · register_detail_payload_json.mandat_montant
    ② plus AUCUNE ligne a corps emprunte n'a un montant masque (None) alors que
      son annonce a un prix -- le masque est bien retire
    ③ une version PASSEE garde son montant d'epoque : on ne reecrit que la
      version courante
    ④ aucun des 88 montants empruntes ne subsiste
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
RACINE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RACINE))

from phase2.sync.export_app_payload import (  # noqa: E402  -- IMPORTEES, JAMAIS RECOPIEES
    PHASE2_DB,
    attach_hektor_read,
    build_mandat_register_rows,
    charger_corps_suspects,
    normalize_text,
    safe_json_loads,
    sqlite_read_connection,
)


def main() -> int:
    limite = None
    if "--lignes" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--lignes") + 1])

    con = sqlite_read_connection(PHASE2_DB)
    attach_hektor_read(con)
    suspects = charger_corps_suspects(con)

    print("CONTROLE -- le montant du registre est-il le prix de l'annonce ?")
    print("   (lecture seule, aucune ecriture)")
    print()
    lignes = build_mandat_register_rows(con, limit=limite, dossier_ids=None)
    print("   lignes de registre construites : %d" % len(lignes))

    total = sans_prix = 0
    ecart_montant = ecart_histo = ecart_payload = 0
    masques_restants = 0
    versions_passees_gardees = 0
    suspects_vus = suspects_au_prix = suspects_en_defaut = 0
    exemples: list[str] = []

    for ligne in lignes:
        total += 1
        prix = normalize_text(ligne.get("prix")) or ""
        cle = (normalize_text(ligne.get("hektor_annonce_id")) or "",
               normalize_text(ligne.get("numero_mandat")) or "")
        est_suspect = cle in suspects
        if est_suspect:
            suspects_vus += 1
        if not prix:
            sans_prix += 1
            if est_suspect and ligne.get("mandat_montant") is None:
                pass            # pas de prix a mettre : rien a reprocher
            continue

        montant = normalize_text(ligne.get("mandat_montant")) or ""
        if montant != prix:
            ecart_montant += 1
            if len(exemples) < 5:
                exemples.append("      annonce %s n %s : mandat_montant=%r prix=%r"
                                % (cle[0], cle[1], montant, prix))
        if est_suspect:
            if montant == prix:
                suspects_au_prix += 1
            else:
                suspects_en_defaut += 1
            if ligne.get("mandat_montant") is None:
                masques_restants += 1

        histo = safe_json_loads(ligne.get("register_history_json"), [])
        if isinstance(histo, list):
            for version in histo:
                if not isinstance(version, dict):
                    continue
                if version.get("is_current"):
                    if (normalize_text(version.get("montant")) or "") != prix:
                        ecart_histo += 1
                elif normalize_text(version.get("montant")):
                    versions_passees_gardees += 1

        paquet = safe_json_loads(ligne.get("register_detail_payload_json"), {})
        if isinstance(paquet, dict):
            if (normalize_text(paquet.get("mandat_montant")) or "") != prix:
                ecart_payload += 1

    print()
    print("LES TROIS CHEMINS, compares a la colonne `prix`")
    print("   lignes avec un prix                       : %d" % (total - sans_prix))
    print("   lignes sans prix (rien a comparer)        : %d" % sans_prix)
    print("   ecart sur mandat_montant                  : %d" % ecart_montant)
    print("   ecart sur l'historique (version courante) : %d" % ecart_histo)
    print("   ecart sur le payload embarque             : %d" % ecart_payload)
    for ligne_ex in exemples:
        print(ligne_ex)
    print()
    print("LES VERSIONS PASSEES -- elles gardent leur montant d'epoque")
    print("   montants de versions passees conserves    : %d" % versions_passees_gardees)
    print()
    print("LES LIGNES A CORPS EMPRUNTE")
    print("   rencontrees                               : %d" % suspects_vus)
    print("   au prix de l'annonce                      : %d" % suspects_au_prix)
    print("   encore en defaut                          : %d" % suspects_en_defaut)
    print("   encore MASQUEES (montant None)            : %d" % masques_restants)

    echecs = ecart_montant + ecart_histo + ecart_payload + masques_restants + suspects_en_defaut
    print()
    print(("ECHEC -- %d probleme(s)" % echecs) if echecs else "OK -- AUCUN ECHEC")
    return 1 if echecs else 0


if __name__ == "__main__":
    raise SystemExit(main())
