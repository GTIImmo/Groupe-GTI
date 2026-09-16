# -*- coding: utf-8 -*-
"""L'ALIGNEMENT DU SERVEUR, EPROUVE HORS LIGNE.

On ne touche NI la vraie base NI Supabase : une base jetable en memoire, et un
client factice qui joue le journal. Ce qu'on veut prouver :

    1. la ligne journalisee DISPARAIT du registre local
    2. les VOISINES ne bougent pas
    3. la ligne est cochee `serveur_aligne` -- et seulement APRES le commit
    4. une ligne deja absente ne fait pas echouer l'etape (idempotence)
    5. un journal illisible NE SUPPRIME RIEN et ne fait pas tomber le run
"""
import sqlite3
import sys

sys.path.insert(0, r"C:\Hektor\Projet\phase2\sync")
import affaire_ledger  # noqa: E402


class ClientFactice:
    """Rend le journal qu'on lui donne, et note ce qu'on lui coche."""

    def __init__(self, journal, casse=False):
        self.journal = journal
        self.casse = casse
        self.coches = []

    def request(self, *, method, path, payload=None, prefer=None):
        if method == "GET":
            if self.casse:
                raise RuntimeError("journal injoignable")
            return self.journal
        if method == "PATCH":
            self.coches.append(path.split("eq.")[-1])
            return None
        raise AssertionError(f"methode inattendue : {method}")


def base_jetable():
    con = sqlite3.connect(":memory:")
    con.execute(f"""CREATE TABLE {affaire_ledger.LEDGER_TABLE} (
        app_affaire_id INTEGER PRIMARY KEY, kind TEXT, hektor_affaire_id TEXT)""")
    con.executemany(
        f"INSERT INTO {affaire_ledger.LEDGER_TABLE} VALUES (?,?,?)",
        [(1001347, "compromis", "50078"),
         (1001348, "vente", "8795"),
         (1001349, "offre", "33050")])
    con.commit()
    return con


def restant(con):
    return sorted(r[0] for r in con.execute(
        f"SELECT app_affaire_id FROM {affaire_ledger.LEDGER_TABLE}"))


echecs = []


def verifier(nom, condition, detail=""):
    print(f"   {'OK  ' if condition else 'ECHEC'}  {nom}{(' -- ' + detail) if detail else ''}")
    if not condition:
        echecs.append(nom)


print("--- 1. la ligne journalisee part, les voisines restent ---")
con = base_jetable()
cl = ClientFactice([{"app_affaire_id": 1001348, "kind": "vente", "hektor_affaire_id": "8795"}])
r = affaire_ledger.appliquer_les_suppressions(con, cl)
verifier("la ligne visee a disparu", 1001348 not in restant(con), str(restant(con)))
verifier("les deux voisines sont intactes", restant(con) == [1001347, 1001349])
verifier("le compte rendu dit 1 retiree", r["retirees_en_local"] == 1, str(r))
verifier("la ligne est cochee en ligne", cl.coches == ["1001348"], str(cl.coches))

print("--- 2. rejouer ne casse rien (idempotence) ---")
r2 = affaire_ledger.appliquer_les_suppressions(con, cl)
verifier("aucune suppression de plus", r2["retirees_en_local"] == 0, str(r2))
verifier("comptee comme deja absente", r2["deja_absentes"] == 1, str(r2))
verifier("les voisines n'ont pas bouge", restant(con) == [1001347, 1001349])

print("--- 3. un journal illisible ne supprime RIEN ---")
con3 = base_jetable()
cl3 = ClientFactice([], casse=True)
r3 = affaire_ledger.appliquer_les_suppressions(con3, cl3)
verifier("les trois lignes sont la", restant(con3) == [1001347, 1001348, 1001349])
verifier("rien n'a ete coche", cl3.coches == [])
verifier("l'etape n'a pas leve", r3["au_journal"] == 0, str(r3))

print("--- 4. un journal vide ne fait rien ---")
con4 = base_jetable()
cl4 = ClientFactice([])
r4 = affaire_ledger.appliquer_les_suppressions(con4, cl4)
verifier("les trois lignes sont la", restant(con4) == [1001347, 1001348, 1001349])
verifier("aucun appel de cochage", cl4.coches == [])

print()
print(">>> TOUT PASSE" if not echecs else f">>> {len(echecs)} ECHEC(S) : {echecs}")
sys.exit(1 if echecs else 0)
