# -*- coding: utf-8 -*-
"""Etape ① du run du recrutement : la DESCENTE, schema « recrutement » -> base locale (R4, 24/11/2026).

    python -X utf8 recrutement/descendre.py            -> rapporte et applique
    python -X utf8 recrutement/descendre.py --essai    -> dit ce qu'elle ferait, n'ecrit rien en local

Interprete : le Python SYSTEME (psycopg2). Connexion : le robot (recrutement/robot.py), qui ne fait que LIRE
ces deux tables.

CE QU'ELLE RAPPORTE, AVANT TOUTE COLLECTE (le lanceur s'arrete si elle echoue : on ne collecte jamais sans
savoir qui ne doit plus revenir) :
  - la liste « ne plus contacter / effacer » (des empreintes) : elle est rangee en local, PUIS APPLIQUEE
    tout de suite -- une personne qui y est sort de la base locale (sa fiche, ses observations, ses
    evenements, l'adresse de sa page, son entreprise si plus personne ne la cite). La collecte suivante ne
    pourra plus la remettre : enregistrer_fiche lit la liste avant tout enregistrement ;
  - le carnet des corrections : il REMPLACE le carnet local (l'app est la seule a l'ecrire).
Les sauvegardes datees (C:\\Hektor\\Backups\\recrutement, un an) gardent l'ancien etat jusqu'a leur rotation
-- c'est ecrit dans la note (§13 R5) et dans la mention d'information.
Le journal ne porte que des COMPTES, jamais un nom. Sortie : 0 = fait (ou essai), 1 = echec.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collecte_annuaires as ca  # noqa: E402


def appliquer(con, liste_noire: list[tuple], corrections: list[tuple], essai: bool) -> dict:
    """La partie LOCALE (eprouvee hors ligne par test_descente.py).
    liste_noire : (empreinte, nature, demande_le) ; corrections : (reseau, identifiant, champ, valeur, par, le)."""
    noire = {e for e, _, _ in liste_noire}
    a_retirer = []
    for f in con.execute("select reseau, identifiant, url, siren, telephone, email, prenom, nom, departement from fiche"):
        if any(e in noire for _, e in ca.empreintes_personne(
                siren=f["siren"], telephone=f["telephone"], email=f["email"],
                prenom=f["prenom"], nom=f["nom"], departement=f["departement"])):
            a_retirer.append((f["reseau"], f["identifiant"], f["url"], f["siren"]))
    compte = {"liste_noire": len(noire), "fiches_retirees": len(a_retirer), "corrections": len(corrections)}
    if essai:
        return compte
    con.executemany("insert or replace into liste_noire (empreinte, nature, le) values (?,?,?)",
                    [(e, n, str(d)) for e, n, d in liste_noire])
    for reseau, ident, url, siren in a_retirer:
        con.execute("delete from fiche where reseau=? and identifiant=?", (reseau, ident))
        con.execute("delete from observation where reseau=? and identifiant=?", (reseau, ident))
        con.execute("delete from evenement_fiche where reseau=? and identifiant=?", (reseau, ident))
        con.execute("delete from correction where reseau=? and identifiant=?", (reseau, ident))
        if url:
            con.execute("delete from page_lue where url=?", (url,))
        if siren and not con.execute("select 1 from fiche where siren=?", (siren,)).fetchone():
            con.execute("delete from entreprise where siren=?", (siren,))
    # le carnet : celui de l'app REMPLACE le carnet local (l'app est la seule a l'ecrire)
    con.execute("delete from correction")
    con.executemany("insert into correction (reseau, identifiant, champ, valeur, par, le) values (?,?,?,?,?,?)",
                    [(r, i, c, v, None if p is None else str(p), str(l)) for r, i, c, v, p, l in corrections])
    con.commit()
    ca._CACHE.pop("noire", None)  # la liste a change : le prochain enregistrement la relit
    return compte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--essai", action="store_true", help="dire ce qui serait fait, sans rien ecrire en local")
    args = p.parse_args()
    import robot
    try:
        rcon = robot.connexion()
    except robot.RobotIndisponible as e:
        print(f"⛔ DESCENTE IMPOSSIBLE : {e}")
        return 1
    try:
        cur = rcon.cursor()
        cur.execute("select empreinte, nature, demande_le from recrutement.liste_noire")
        liste_noire = cur.fetchall()
        cur.execute("select reseau, identifiant, champ, valeur, par, le from recrutement.correction")
        corrections = cur.fetchall()
    except Exception as e:
        print(f"⛔ DESCENTE IMPOSSIBLE (lecture) : {e.__class__.__name__} : {str(e)[:300]}")
        return 1
    finally:
        rcon.close()
    compte = appliquer(ca.ouvrir_base(), liste_noire, corrections, args.essai)
    print(("essai : " if args.essai else "") +
          f"liste « ne plus contacter » : {compte['liste_noire']} empreintes ; fiches retirees en local : "
          f"{compte['fiches_retirees']} ; corrections recopiees : {compte['corrections']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
