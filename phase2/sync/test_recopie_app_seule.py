# -*- coding: utf-8 -*-
"""L'EPREUVE HORS LIGNE DE 26bis-TRANSACTIONS (piece 4 de C.19-d, 15/11/2026).

    python -X utf8 phase2/sync/test_recopie_app_seule.py

AUCUN RESEAU, AUCUNE BASE REELLE : chaque controle monte sa propre base SQLite
en memoire, avec le VRAI DDL du registre (`DDL_SQLITE`) et une doublure batie sur
la meme structure -- c'est ainsi que `pull_from_supabase` la recree chaque nuit.

⭐ CE QUE CETTE EPREUVE DOIT PROUVER, ET SURTOUT CE QU'ELLE DOIT REFUSER. Une
  recopie qui prend trop large est pire que pas de recopie : elle ferait entrer
  dans le registre local -- donc dans la sauvegarde, et au prochain push chez
  Supabase -- des lignes que personne n'a decidees. Les temoins inverses (3, 4, 5)
  valent donc autant que le temoin direct (2).
"""
import os
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

import affaire_ledger as al                                          # noqa: E402

VERTS = 0
ROUGES = []


def juger(nom, attendu, obtenu):
    global VERTS
    if attendu == obtenu:
        VERTS += 1
        print("  OK   %s" % nom)
    else:
        ROUGES.append(nom)
        print("  ROUGE %s\n        attendu %r\n        obtenu %r" % (nom, attendu, obtenu))


def base(lignes_doublure=(), lignes_locales=(), colonne_en_trop_en_local=False,
         colonne_absente_de_la_doublure=False):
    """Une base neuve. `lignes_*` = des dict ; les cles absentes valent NULL."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(al.DDL_SQLITE)
    # Le run ajoute les colonnes neuves apres le DDL (voir refresh_ledger) : on fait
    # pareil, c'est l'etat reel d'une machine a jour.
    for neuve in ("transaction_origine",):
        try:
            con.execute("ALTER TABLE app_affaire_ledger ADD COLUMN %s TEXT" % neuve)
        except sqlite3.OperationalError:
            pass
    if colonne_en_trop_en_local:
        # Le cas « le patch local est colle, celui de Supabase pas encore ».
        con.execute("ALTER TABLE app_affaire_ledger ADD COLUMN colonne_neuve_locale TEXT")
    con.execute("CREATE TABLE app_affaire_ledger__sb AS "
                "SELECT * FROM app_affaire_ledger WHERE 0")
    if colonne_absente_de_la_doublure:
        con.execute("ALTER TABLE app_affaire_ledger__sb DROP COLUMN transaction_origine")
    for table, lignes in (("app_affaire_ledger__sb", lignes_doublure),
                          ("app_affaire_ledger", lignes_locales)):
        connues = {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}
        for ligne in lignes:
            cols = [c for c in ligne if c in connues]
            con.execute("INSERT INTO %s (%s) VALUES (%s)"
                        % (table, ", ".join(cols), ", ".join("?" for _ in cols)),
                        tuple(ligne[c] for c in cols))
    con.commit()
    return con


def L(app_affaire_id, **reste):
    ligne = {"app_affaire_id": app_affaire_id, "kind": "offre", "state": "refused",
             "hektor_annonce_id": 28351, "hektor_affaire_id": None,
             "present_in_hektor": 0, "first_seen_at": "2026-11-15T10:00:00+00:00"}
    ligne.update(reste)
    return ligne


print("=== 26bis-TRANSACTIONS : la porte d'entree du registre local ===")

# ─── 1. L'INTERRUPTEUR ───
os.environ.pop("APP_RECOPIE_APP_SEULE", None)
al._ENV_DEJA_CHARGE = True            # on ne lit pas le .env de la machine
juger("1  eteint par defaut (variable absente)", False, al.recopie_app_seule_active())
os.environ["APP_RECOPIE_APP_SEULE"] = "0"
juger("1b a 0, il reste eteint", False, al.recopie_app_seule_active())
os.environ["APP_RECOPIE_APP_SEULE"] = "1"
juger("1c a 1, il est allume", True, al.recopie_app_seule_active())

# ─── 2. LE TEMOIN DIRECT : une ligne de la plage app SANS numero Hektor entre ───
con = base(lignes_doublure=[L(1001424)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("2  elle est recopiee", 1, r["recopiees"])
juger("2b son numero est nomme", [1001424], r.get("cles"))
juger("2c le temoin boucle (0 -> 1)",
      (0, 1), (r["plage_sans_numero_avant"], r["plage_sans_numero_apres"]))
juger("2d elle est VRAIMENT dans le registre local", 1, con.execute(
    "SELECT COUNT(*) FROM app_affaire_ledger WHERE app_affaire_id=1001424"
).fetchone()[0])

# ─── 3. TEMOIN INVERSE : la MEME ligne AVEC un numero Hektor n'entre PAS ───
con = base(lignes_doublure=[L(1001424, hektor_affaire_id="50128")])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("3  TEMOIN INVERSE -- avec un numero Hektor, elle reste dehors", 0, r["recopiees"])
juger("3b et elle n'est pas candidate", 0, r["candidates"])

# ─── 4. TEMOIN INVERSE : hors de la plage app, elle n'entre PAS ───
con = base(lignes_doublure=[L(999999)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("4  TEMOIN INVERSE -- hors plage app (999 999), elle reste dehors", 0, r["recopiees"])

# ─── 5. TEMOIN INVERSE : un numero Hektor VIDE compte comme absent ───
con = base(lignes_doublure=[L(1001500, hektor_affaire_id="   ")])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("5  un numero vide ou blanc vaut ABSENT, elle entre", 1, r["recopiees"])

# ─── 6. PAS DE DOUBLON : une ligne deja en local n'est pas recopiee ───
con = base(lignes_doublure=[L(1001424), L(1001425)], lignes_locales=[L(1001424)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("6  seule la manquante entre", 1, r["recopiees"])
juger("6b et le local n'a pas de doublon", 1, con.execute(
    "SELECT COUNT(*) FROM app_affaire_ledger WHERE app_affaire_id=1001424").fetchone()[0])

# ─── 7. LES VALEURS SONT COPIEES, pas inventees ───
con = base(lignes_doublure=[L(1001600, montant="250000", date="2023-12-05",
                              transaction_origine="classeur",
                              first_seen_at="2023-12-05T00:00:00+00:00")])
al.recopier_ce_que_hektor_ne_rendra_jamais(con)
ligne = con.execute("SELECT * FROM app_affaire_ledger WHERE app_affaire_id=1001600"
                    ).fetchone()
juger("7  le montant suit", "250000", ligne["montant"])
juger("7b la date suit", "2023-12-05", ligne["date"])
juger("7c LA MARQUE suit", "classeur", ligne["transaction_origine"])
juger("7d LA DATE DE NAISSANCE suit (un numero ne se perd jamais)",
      "2023-12-05T00:00:00+00:00", ligne["first_seen_at"])

# ─── 8. LE PLAFOND REFUSE, et il le dit ───
con = base(lignes_doublure=[L(1000000 + i) for i in range(al.PLAFOND_RECOPIE_APP_SEULE + 1)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("8  au-dela du plafond, RIEN n'est recopie", 0, r["recopiees"])
juger("8b le refus est nomme", al.PLAFOND_RECOPIE_APP_SEULE + 1, r.get("refus_plafond"))
juger("8c et le registre local est intact", 0, con.execute(
    "SELECT COUNT(*) FROM app_affaire_ledger").fetchone()[0])

# ─── 9. LE VOLUME CONNU (242) PASSE, lui ───
con = base(lignes_doublure=[L(1000000 + i) for i in range(242)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("9  les 242 du travail connu passent", 242, r["recopiees"])

# ─── 10. LE FILET D'ORDRE : une colonne que la doublure n'a pas encore ───
con = base(lignes_doublure=[L(1001424)], colonne_en_trop_en_local=True)
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("10 une colonne locale inconnue de la doublure ne fait pas tomber l'etape",
      1, r["recopiees"])

# ─── 11. LE FILET D'ORDRE, dans l'autre sens ───
con = base(lignes_doublure=[L(1001424)], colonne_absente_de_la_doublure=True)
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("11 la marque absente de la doublure ne fait pas tomber l'etape", 1, r["recopiees"])

# ─── 12. UNE COLONNE OBLIGATOIRE VIDE : ecartee, nommee, et l'etape NE TOMBE PAS ───
#
# ⭐ CES DEUX CONTROLES VIENNENT DU TEMOIN DU TEMOIN, PAS DE L'EPREUVE. Les 30
#   premiers controles etaient verts et l'INSERT levait quand meme
#   (IntegrityError: NOT NULL constraint failed: app_affaire_ledger.present_in_hektor)
#   des que la doublure laissait cette colonne vide -- donc l'etape du run tombait.
#   Chez Supabase les trois colonnes sont NOT NULL (mesure du 15/11), donc le cas ne
#   devrait pas arriver ; mais « une ligne ne doit plus arreter le run entier ».
juger("12 les colonnes obligatoires sont LUES, et ce sont les trois attendues",
      ["app_affaire_id", "kind", "present_in_hektor"],
      sorted(al.recopier_ce_que_hektor_ne_rendra_jamais(
          base(lignes_doublure=[L(1001424)]))["colonnes_obligatoires"]))

con = base(lignes_doublure=[L(1001424, kind=None), L(1001425)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("12b la ligne sans genre est ecartee, l'autre entre", 1, r["recopiees"])
juger("12c et elle est NOMMEE", [1001424],
      r.get("ecartees_colonne_obligatoire_vide"))

con = base(lignes_doublure=[L(1001424, present_in_hektor=None), L(1001425)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("12d present_in_hektor vide : ECARTEE au lieu de faire tomber l'etape",
      1, r["recopiees"])
juger("12e et elle est NOMMEE", [1001424],
      r.get("ecartees_colonne_obligatoire_vide"))
juger("12f ⛔ et le vide N'A PAS ete comble par le defaut du DDL (1 = chez Hektor)",
      0, con.execute("SELECT COUNT(*) FROM app_affaire_ledger "
                     "WHERE app_affaire_id=1001424").fetchone()[0])

# ─── 12bis. SANS NUMERO : ECARTEE, ET SURTOUT AUCUN NUMERO INVENTE ───
#
# ⛔⛔ LE DEFAUT QUE CE CONTROLE GARDE FERME. SQLite ne marque pas « notnull » une
#   colonne INTEGER PRIMARY KEY (c'est un alias de rowid) : sans la garde posee a la
#   main, une ligne sans numero serait ENTREE avec un numero INVENTE par SQLite --
#   une seconde serie de numeros frappee en local, la faute que le projet s'interdit
#   depuis le debut. Le PRAGMA ne suffit donc pas, et c'est l'epreuve qui l'a dit.
con = base(lignes_doublure=[L(None), L(1001425)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("12g sans numero : seule l'autre entre", 1, r["recopiees"])
juger("12h ET AUCUN NUMERO N'A ETE INVENTE", [1001425], [
    row[0] for row in con.execute("SELECT app_affaire_id FROM app_affaire_ledger "
                                  "ORDER BY app_affaire_id")])

# ─── 13. PAS DE DOUBLURE : on ne tombe pas ───
con = base(lignes_doublure=[L(1001424)])
con.execute("DROP TABLE app_affaire_ledger__sb")
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("13 sans doublure, le run CONTINUE et le dit", True, r.get("doublure_absente"))

# ─── 14. RIEN A FAIRE : le cas normal des nuits suivantes ───
con = base(lignes_doublure=[L(1001424)], lignes_locales=[L(1001424)])
r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
juger("14 une fois le travail fait, la nuit suivante ne recopie rien", 0, r["recopiees"])

# ─── 15. LE PUSH NE RENVOIE PAS LA MARQUE ───
juger("15 transaction_origine est dans ce que le push N'ENVOIE PAS",
      True, "transaction_origine" in al.COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS)
con = base(lignes_doublure=[L(1001424, transaction_origine="classeur")])
al.recopier_ce_que_hektor_ne_rendra_jamais(con)
envoyees = al.ledger_rows_for_push(con)
juger("15b la ligne part au push...", 1, len(envoyees))
juger("15c ...mais SANS sa marque", False, "transaction_origine" in (envoyees[0] or {}))

# ─── 16. L'ORDRE DANS LE RUN -- lu dans le fichier, pas suppose ───
#
# Meme patron que test_etiquette_dans_le_run (12/11) : la place de ce geste dans la
# nuit n'est pas un detail, c'est ce qui garantit que le PREMIER passage n'ecrit
# rien chez Supabase (apres le push) et que les lignes neuves recoivent aussitot
# les colonnes de classe A (avant la redescente).
texte = (RACINE / "phase2" / "sync" / "affaire_ledger.py").read_text(encoding="utf-8")
i_push = texte.index("client.upsert_rows(path=LEDGER_TABLE, rows=rows")
i_recopie = texte.index('result["recopie_app_seule"] = (')
i_redescente = texte.index('result["chaines"] = redescendre_ce_que_l_app_possede')
juger("16 la recopie est APRES le push (le 1er passage n'ecrit rien chez Supabase)",
      True, i_push < i_recopie)
juger("16b et AVANT la redescente (un seul chemin pour les colonnes de classe A)",
      True, i_recopie < i_redescente)
juger("16c et elle ne tourne QUE si l'interrupteur est allume",
      True, "if recopie_app_seule_active() else" in texte)

print()
print("%d/%d verts" % (VERTS, VERTS + len(ROUGES)))
if ROUGES:
    print("ROUGES : " + " . ".join(ROUGES))
sys.exit(1 if ROUGES else 0)
