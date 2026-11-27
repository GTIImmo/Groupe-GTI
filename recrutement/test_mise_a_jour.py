# -*- coding: utf-8 -*-
"""Essai HORS LIGNE de la mise a jour (R2) -- une base jetable, des collectes fabriquees.

    python -X utf8 recrutement/test_mise_a_jour.py

Aucun reseau, aucune donnee reelle : la base est creee dans un dossier temporaire (variable
RECRUTEMENT_DONNEES posee AVANT l'import du collecteur), puis effacee. Chaque attendu est ecrit
AVANT de lancer, et chaque controle dit ce qu'il mesure. Sortie 0 = tout vert, 1 = un rouge.
"""
import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

DOSSIER_ESSAI = Path(tempfile.mkdtemp(prefix="recrutement_essai_"))
os.environ["RECRUTEMENT_DONNEES"] = str(DOSSIER_ESSAI)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collecte_annuaires as ca  # noqa: E402

ARGS = argparse.Namespace(limite=0, relire=False, sans_reseau=True)
rouges = []


def verifier(quoi, obtenu, attendu):
    ok = obtenu == attendu
    print(("  OK    " if ok else "  ROUGE ") + f"{quoi} : {obtenu!r}" + ("" if ok else f"   (attendu {attendu!r})"))
    if not ok:
        rouges.append(quoi)


def voir(con, reseau, ident):
    r = con.execute("select etat_suivi, absences, motif_depart from fiche where reseau=? and identifiant=?", (reseau, ident)).fetchone()
    return tuple(r) if r else None


def passer(con, vus: dict):
    """Une collecte : ouvrir, « lire » les fiches donnees (reseau -> liste de (id, champs)), puis maj."""
    ca._CACHE.clear()
    assert ca.cmd_collecte_ouvrir(con, None, ARGS) == ca.CODE_FINI
    for reseau, fiches in vus.items():
        for ident, champs in fiches:
            ca.enregistrer_fiche(con, reseau, ident, **champs)
    return ca.cmd_maj(con, None, ARGS)


def fiche(i, **plus):
    return (i, {"prenom": "P" + i, "nom": "N" + i.upper(), "departement": "42", "code_postal": "42000",
                "commune": "Saint-Etienne", **plus})


def main():
    con = ca.ouvrir_base()
    alpha = [fiche(f"a{i:02d}", siren=None) for i in range(20)]
    alpha[5] = fiche("a05", siren="111111111")
    beta = [fiche(f"b{i}") for i in range(3)]
    gamma = [fiche(f"g{i:02d}") for i in range(12)]
    delta = [fiche(f"d{i:02d}") for i in range(15)]

    print("\n1. La collecte de reference (n° 1) : personne n'y est « nouveau »")
    for reseau, fs in (("alpha", alpha), ("beta", beta), ("gamma", gamma), ("delta", delta)):
        for ident, champs in fs:
            ca.enregistrer_fiche(con, reseau, ident, **champs)
    verifier("collecte initiale", ca.cmd_collecte_initiale(con, None, ARGS), ca.CODE_FINI)
    verifier("etat de a00 apres la n° 1", voir(con, "alpha", "a00"), ("present", 0, None))
    verifier("une 2e collecte initiale ne fait rien", ca.cmd_collecte_initiale(con, None, ARGS), ca.CODE_FINI)
    verifier("observations de la n° 1", con.execute("select count(*) from observation where collecte=1").fetchone()[0], 50)

    print("\n2. Collecte n° 2 : alpha perd a19 et gagne a20 ; beta perd b2 ; GAMMA CASSE (3 sur 12) ;"
          " DELTA perd ses 3 temoins (14 sur 15)")
    code = passer(con, {
        "alpha": alpha[:19] + [fiche("a20")],
        "beta": beta[:2],
        "gamma": gamma[:3],
        "delta": delta[3:] + [fiche("dx1"), fiche("dx2")],
    })
    verifier("code de sortie (une source malade -> 1)", code, ca.CODE_ERREUR)
    sante = dict(con.execute("select reseau, sante from source_etat where collecte=2").fetchall())
    verifier("sante alpha", sante["alpha"], "saine")
    verifier("sante beta (petite source, 2 sur 3)", sante["beta"], "saine")
    verifier("sante gamma (3 sur 12 < 70 %)", sante["gamma"], "malade")
    verifier("sante delta (14 sur 15 mais 0 temoin revu sur 3)", sante["delta"], "malade")
    verifier("a19 (absent une fois)", voir(con, "alpha", "a19"), ("absent", 1, None))
    verifier("a20 (vu pour la 1re fois)", voir(con, "alpha", "a20"), ("nouveau", 0, None))
    verifier("b2 (absent une fois)", voir(con, "beta", "b2"), ("absent", 1, None))
    verifier("⛔ g05 (source malade : l'etat NE BOUGE PAS)", voir(con, "gamma", "g05"), ("present", 0, None))
    verifier("⛔ gamma : zero depart, zero absence", con.execute(
        "select count(*) from fiche where reseau='gamma' and etat_suivi<>'present'").fetchone()[0], 0)
    verifier("⛔ d00, temoin perdu, source malade : l'etat ne bouge pas", voir(con, "delta", "d00"), ("present", 0, None))

    print("\n3. Collecte n° 3 : a19 absent une 2e fois ; a05 disparait d'alpha et son SIREN apparait chez beta ;"
          " gamma revient en entier ; b2 revient")
    alpha3 = [f for f in alpha[:19] if f[0] != "a05"] + [fiche("a20")]
    code = passer(con, {
        "alpha": alpha3,
        "beta": beta + [fiche("b9", siren="111111111")],
        "gamma": gamma,
        "delta": delta + [fiche("dx1"), fiche("dx2")],
    })
    verifier("code de sortie (aucune source malade)", code, ca.CODE_FINI)
    verifier("a19 (absent 2 collectes de suite -> parti)", voir(con, "alpha", "a19"), ("parti", 2, "absent de 2 collectes de suite"))
    verifier("a05 (a change de reseau)", voir(con, "alpha", "a05")[0::2], ("parti", "a rejoint beta"))
    verifier("b9 (nouveau chez beta)", voir(con, "beta", "b9"), ("nouveau", 0, None))
    verifier("b2 (revu apres une absence -> present)", voir(con, "beta", "b2"), ("present", 0, None))
    verifier("a20 (revu -> present)", voir(con, "alpha", "a20"), ("present", 0, None))
    verifier("gamma saine", con.execute("select sante from source_etat where collecte=3 and reseau='gamma'").fetchone()[0], "saine")

    print("\n4. Collecte n° 4 : a19 revient ; LA LISTE NOIRE (telephone de a03, nom de a07, une personne neuve)")
    for nature, empreinte in (ca.empreintes_personne(telephone="06 11 22 33 03")
                              + [e for e in ca.empreintes_personne(prenom="Pa07", nom="NA07", departement="42") if e[0] == "nom"]
                              + [e for e in ca.empreintes_personne(prenom="Pzz", nom="NZZ", departement="42") if e[0] == "nom"]):
        con.execute("insert into liste_noire values (?,?,?)", (empreinte, nature, ca.maintenant()))
    con.commit()
    alpha4 = [(i, dict(c, telephone="06 11 22 33 03") if i == "a03" else c) for i, c in alpha3] + [fiche("a19"), fiche("zz")]
    passer(con, {"alpha": alpha4, "beta": beta + [fiche("b9", siren="111111111")], "gamma": gamma,
                 "delta": delta + [fiche("dx1"), fiche("dx2")]})
    verifier("a19 (parti, revu -> revenu, le motif du depart est efface)", voir(con, "alpha", "a19"), ("revenu", 0, None))
    verifier("⛔ a03 (son telephone est sur la liste) : retire", voir(con, "alpha", "a03"), None)
    verifier("⛔ a03 : plus aucune observation", con.execute(
        "select count(*) from observation where reseau='alpha' and identifiant='a03'").fetchone()[0], 0)
    verifier("⛔ a07 (son nom + departement sont sur la liste) : retire", voir(con, "alpha", "a07"), None)
    verifier("⛔ zz (personne neuve, sur la liste) : jamais entree", voir(con, "alpha", "zz"), None)
    verifier("TEMOIN INVERSE : a04 (pas sur la liste) toujours la", voir(con, "alpha", "a04"), ("present", 0, None))

    print("\n5. Le carnet des corrections : il gagne a l'export, la relecture ne l'ecrase pas")
    con.execute("insert into correction values ('alpha','a00','telephone','06 99 99 99 99','essai',?)", (ca.maintenant(),))
    con.execute("insert into correction values ('alpha','a00','siren','999999999','essai',?)", (ca.maintenant(),))
    con.commit()
    ca.enregistrer_fiche(con, "alpha", "a00", telephone="06 00 00 00 00", source_contact="annuaire alpha : telephone affiche")
    ligne = next(l for l in ca.lignes_csv(con) if l["prenom"] == "Pa00")
    verifier("telephone exporte = celui du carnet", ligne["telephone"], "06 99 99 99 99")
    verifier("la base garde ce que l'annuaire dit", con.execute(
        "select telephone from fiche where identifiant='a00'").fetchone()[0], "06 00 00 00 00")
    verifier("un champ hors liste (siren) n'est PAS corrigeable", ligne["siren"], "")
    verifier("la ligne dit ce qui a ete corrige", ligne["corrige_dans_l_app"], "telephone")

    print("\n6. Le journal des evenements")
    quoi = dict(con.execute("select quoi, count(*) from evenement_fiche group by quoi").fetchall())
    print("  ", quoi)
    verifier("un evenement « change_de_reseau »", quoi.get("change_de_reseau"), 1)
    con.close()


try:
    main()
finally:
    shutil.rmtree(DOSSIER_ESSAI, ignore_errors=True)
print(f"\n{'TOUT VERT' if not rouges else str(len(rouges)) + ' ROUGE(S) : ' + ', '.join(rouges)}")
sys.exit(1 if rouges else 0)
