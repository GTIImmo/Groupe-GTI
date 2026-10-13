#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A.3-tech etape B — UN MANDAT, UN NUMERO : le serveur et Supabase d'accord ?
                                                                  30/09/2026

L'OEIL DU REGISTRE DES MANDATS. Meme role que `annonce_un_numero` (C.9-b) pour
l'annonce, et meme patron -- une seule formule, lue par la sonde de sante ET par
le controle de nuit, parce que deux copies d'une meme regle divergent tot ou tard.

CE QU'ON COMPARE
----------------
    le serveur   app_mandat        la table locale, remplie par le run
    Supabase     app_mandat__sb    sa DOUBLURE, descendue par pull_from_supabase

⚠ LA DOUBLURE NE DEMANDE AUCUN CODE, et c'est verifie le 30/09 : le descendeur
  lit le schema de Supabase et descend TOUT ce qu'il trouve ; quand le nom existe
  deja en local il le range sous `<nom>__sb`. app_mandat -> app_mandat__sb, sans
  rien a declarer. « Pas de liste a tenir, donc aucune table ne passe au travers. »

CE QUI EST GRAVE -- seuil ZERO
-------------------------------
    deux_numeros        un meme couple (annonce, numero) porte DEUX numeros
                        d'app. C'est le defaut que la cle unique doit empecher ;
                        s'il apparait, c'est que les deux distributeurs se sont
                        croises.
    croisements         un meme numero d'app vise DEUX couples differents.
    absents_du_cloud    une ligne du serveur que Supabase n'a pas. Le push n'est
                        pas passe -- et un registre incomplet qui se presente
                        comme a jour est exactement ce qu'on refuse ailleurs.
    plage_envahie       un numero >= 1 000 000 pose par le RUN. C'est le defaut
                        d'aout, celui qui a coute cinq jours de creations
                        impossibles cote affaires.

CE QUI N'EST PAS GRAVE, et se compte a part pour ne pas crier pour rien
-----------------------------------------------------------------------
    en_attente          une ligne que SEUL Supabase porte, avec un numero de la
                        plage de l'app : un mandat NE DANS L'APP que le miroir
                        n'a pas encore ramene. C'est le fonctionnement normal,
                        et cela DOIT retomber a zero apres une descente + un run.

CE QU'ELLE REND
---------------
`None` si une table manque -- une mesure impossible n'est PAS un zero, et la
sonde doit le dire. Tant que la doublure n'a jamais ete descendue, c'est le cas,
et c'est honnete : on ne peut rien affirmer sur un accord qu'on n'a pas lu.

LECTURE SEULE.
    python phase2/checks/mandat_un_numero.py     la mesure, code 1 si grave
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"

# La moitie haute est reservee aux mandats nes dans l'app. Meme valeur que
# l'affaire et le dossier. Le run ne doit JAMAIS y poser un numero.
PLAGE = 1_000_000
GRAVES = ("deux_numeros", "croisements", "absents_du_cloud", "plage_envahie")

# ⚠ LA MESURE SE FAIT EN MEMOIRE, PAS EN SQL, ET C'EST UN CORRECTIF DU 30/09.
# La premiere version comparait les deux tables en SQL, avec un CAST des deux
# cotes de la jointure. Un CAST sur une colonne de jointure ecarte TOUT index :
# la sonde a tourne plus de deux minutes sur 26 826 lignes, et une sonde de sante
# qui met deux minutes ne tourne pas -- elle finit par etre coupee.
# 26 826 lignes tiennent dans un dictionnaire sans peine. On lit une fois chaque
# table, on compare des ensembles, et la mesure prend moins d'une seconde.


def _lire(conn: sqlite3.Connection, table: str) -> dict:
    """{(annonce, numero): numero d'app} -- les deux colonnes ramenees au texte."""
    sortie = {}
    for app_id, annonce, numero in conn.execute(
        f"SELECT app_mandat_id, hektor_annonce_id, numero_mandat FROM {table}"
    ):
        a = str(annonce or "").strip()
        n = str(numero or "").strip()
        if a and n:
            sortie[(a, n)] = int(app_id) if app_id is not None else None
    return sortie


def _table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (nom,)).fetchone() is not None


# ─────────────────────────────────────────────────────────────────────────────
# LA FRAICHEUR DE LA COPIE -- ajoute le 13/10/2026
#
# POURQUOI. La sentinelle criait « le push n'est pas passe » TOUS LES MATINS a
# 07:49, et se taisait d'elle-meme a 09:49. Mesure de l'historique : 5 absents le
# 08/10, 1 le 09/10, 3 le 10/10, 4 le 13/10 -- et « 0 ecart » deux heures plus
# tard, chaque fois. Les donnees etaient bonnes a chaque coup.
#
# LA CAUSE n'etait pas le push, c'etait L'ORDRE DES HORLOGES :
#     06:56  le run POUSSE le registre vers Supabase
#     07:45  la descente commence
#     07:48  LA SONDE PASSE -- la copie app_mandat__sb n'est pas encore refaite
#     ~07:58 la descente refait enfin la copie  (c'est la table 97 sur 110)
# La sonde comparait donc le registre a une copie PLUS VIEILLE QUE LUI.
#
# UNE ALARME QUI CRIE TOUS LES JOURS POUR RIEN EST UNE ALARME QU'ON NE LIT PLUS,
# et le jour ou elle aura raison, personne ne la croira.
#
# ⚠ CE QU'ON NE CHANGE PAS : le rouge quand le push n'est VRAIMENT pas passe.
#   Dans ce cas la descente ramene une copie A JOUR qui n'a pas les mandats --
#   la copie est alors plus RECENTE que le registre, on juge, et on crie. Le
#   parti pris ecrit au-dessus (« ROUGE TANT QUE LE PUSH N'A PAS EU LIEU, et
#   c'est voulu ») reste entier.
#
# ⚠ ET LE PIEGE DES FUSEAUX, parce qu'il aurait fausse la mesure de DEUX HEURES :
#     app_mandat.last_seen_at        '2026-10-13T04:56:43+00:00'  -> UTC
#     sb_pull_state.derniere_descente '2026-10-13T07:45:03'       -> heure LOCALE
#   Comparer les deux comme des textes aurait donne un resultat faux -- c'est
#   exactement le genre d'erreur qui fait mentir une sentinelle. On ramene donc
#   les deux a UTC avant de comparer, et on REND les deux dates pour qu'on puisse
#   toujours verifier a la main ce que la mesure a compare.
# ─────────────────────────────────────────────────────────────────────────────

def _en_utc(texte: str | None) -> datetime | None:
    """Rend un instant en UTC, ou None si on ne sait pas lire.

    Deux formes attendues, et une seule porte son fuseau :
        '2026-10-13T04:56:43+00:00'  -> deja situe
        '2026-10-13T07:45:03'        -> heure LOCALE de la machine du run
    Une date qu'on ne sait pas lire rend None, et l'appelant se tait : on ne
    devine pas un fuseau.
    """
    propre = (texte or "").strip().replace(" ", "T")
    if not propre:
        return None
    try:
        instant = datetime.fromisoformat(propre)
    except ValueError:
        return None
    if instant.tzinfo is None:
        # pas de fuseau ecrit = heure locale de la machine qui a descendu
        instant = instant.astimezone()
    return instant.astimezone(timezone.utc)


def _fraicheur_copie(conn: sqlite3.Connection) -> dict:
    """La copie est-elle plus recente que le registre qu'on lui compare ?

    Rend toujours les deux dates, meme quand on ne peut pas trancher : une
    mesure se verifie a la main, donc elle montre ce qu'elle a compare.
    """
    sortie = {
        "copie_descendue_le": None,
        "registre_ecrit_le": None,
        "copie_en_retard": None,   # None = on ne sait pas, et on ne devine pas
        "copie_en_cours": False,
    }
    if _table_existe(conn, "sb_pull_state"):
        ligne = conn.execute(
            "SELECT derniere_descente, dernier_echec FROM sb_pull_state "
            "WHERE table_name = 'app_mandat__sb'"
        ).fetchone()
        if ligne:
            sortie["copie_descendue_le"] = ligne[0]
            # Le descendeur ecrit 'copie en cours' AVANT de copier et l'efface
            # apres la bascule : si on tombe pile dessus, la copie est en train
            # d'etre refaite -- on ne juge pas.
            sortie["copie_en_cours"] = (ligne[1] or "").strip().lower().startswith("copie en cours")

    ligne = conn.execute("SELECT max(last_seen_at) FROM app_mandat").fetchone()
    if ligne:
        sortie["registre_ecrit_le"] = ligne[0]

    descente = _en_utc(sortie["copie_descendue_le"])
    registre = _en_utc(sortie["registre_ecrit_le"])
    if descente is not None and registre is not None:
        sortie["copie_en_retard"] = descente < registre
    return sortie


def mesurer(conn: sqlite3.Connection) -> dict | None:
    """Rend les comptes, et `graves` leur somme.

    None si une des deux tables manque -- ce n'est PAS un zero.
    """
    if not _table_existe(conn, "app_mandat") or not _table_existe(conn, "app_mandat__sb"):
        return None
    serveur = _lire(conn, "app_mandat")
    cloud = _lire(conn, "app_mandat__sb")

    # ① LE COUPLE PORTE-T-IL LE MEME NUMERO DES DEUX COTES ?
    deux_numeros = sum(1 for cle, ident in cloud.items()
                       if cle in serveur and serveur[cle] != ident)

    # ② UN NUMERO VISE-T-IL DEUX COUPLES ? On retourne les deux tables : si un
    #    meme numero d'app pointe ici et la-bas sur des couples differents,
    #    l'identite du mandat est rompue.
    par_id_serveur = {}
    for cle, ident in serveur.items():
        if ident is not None:
            par_id_serveur[ident] = cle
    croisements = sum(1 for cle, ident in cloud.items()
                      if ident in par_id_serveur and par_id_serveur[ident] != cle)

    # ③ LE PUSH EST-IL PASSE ?
    absents_du_cloud = sum(1 for cle in serveur if cle not in cloud)

    # ④ CE QUE SEUL LE CLOUD PORTE, dans la plage de l'app : un mandat NE DANS
    #    L'APP que le miroir n'a pas encore ramene. Normal, compte a part.
    en_attente = sum(1 for cle, ident in cloud.items()
                     if cle not in serveur and (ident or 0) >= PLAGE)

    comptes = {
        "deux_numeros": deux_numeros,
        "croisements": croisements,
        "absents_du_cloud": absents_du_cloud,
        "en_attente": en_attente,
    }
    # Le run ne distribue que SOUS la plage. Un numero au-dessus, cote serveur,
    # veut dire que l'allocateur a regarde le MAX global -- le defaut d'aout.
    comptes["plage_envahie"] = sum(1 for ident in serveur.values()
                                   if (ident or 0) >= PLAGE)
    comptes["graves"] = sum(comptes[c] for c in GRAVES)
    comptes["serveur"] = len(serveur)
    comptes["supabase"] = len(cloud)

    # ⑤ LA COPIE EST-ELLE PLUS RECENTE QUE CE QU'ON LUI COMPARE ? (13/10/2026)
    #    `graves` n'est PAS touche -- on ajoute des cles, on n'en retire aucune,
    #    pour que le code retour du script en ligne de commande ne change pas de
    #    sens. C'est l'appelant qui decide s'il crie ou s'il se tait.
    comptes.update(_fraicheur_copie(conn))
    # Vrai seulement quand les deux conditions tiennent : il manque des lignes
    # ET la copie est trop vieille pour en juger. C'est le cas « je ne sais pas »,
    # a ne pas confondre avec « tout va bien » ni avec « le push a echoue ».
    comptes["absents_non_concluants"] = bool(
        comptes["absents_du_cloud"]
        and (comptes.get("copie_en_retard") is True or comptes.get("copie_en_cours"))
    )
    return comptes


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    conn = sqlite3.connect(f"file:{BASE.as_posix()}?mode=ro", uri=True)
    try:
        m = mesurer(conn)
    finally:
        conn.close()
    if m is None:
        print("NON MESURABLE : app_mandat ou sa doublure app_mandat__sb manque.")
        print("   (la doublure arrive avec : python phase2/sync/pull_from_supabase.py")
        print("    --table app_mandat -- aucun code a ecrire, le descendeur la prend seul)")
        return 2
    print(f"serveur {m['serveur']} mandats · doublure Supabase {m['supabase']}")
    for cle in GRAVES:
        print(f"  {cle:22} {m[cle]}")
    print(f"  {'en_attente':22} {m['en_attente']}   (normal : ne dans l'app, pas encore chez Hektor)")
    print(f"  copie descendue le   {m['copie_descendue_le']}")
    print(f"  registre ecrit le    {m['registre_ecrit_le']}")
    if m["copie_en_cours"]:
        print("  >>> la copie est EN COURS de descente")
    elif m["copie_en_retard"] is True:
        print("  >>> LA COPIE EST PLUS VIEILLE QUE LE REGISTRE")
    elif m["copie_en_retard"] is None:
        print("  >>> fraicheur de la copie INCONNUE (date illisible) -- on ne devine pas")
    if m["absents_non_concluants"]:
        # On ne peut rien affirmer : les lignes « absentes » le sont peut-etre
        # seulement parce que la copie est anterieure au push. Ce n'est NI un
        # zero, NI une alerte.
        print(f"NON CONCLUANT : {m['absents_du_cloud']} ligne(s) manquent a une copie "
              "plus vieille que le registre -- a revoir apres la prochaine descente.")
        return 2
    if m["graves"]:
        print(f"GRAVE : {m['graves']} ecart(s) -- un mandat doit avoir UN numero.")
        return 1
    print("Un mandat, un numero : le serveur et Supabase sont d'accord.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
