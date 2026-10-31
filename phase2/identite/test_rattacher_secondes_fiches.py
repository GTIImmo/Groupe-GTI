"""Essai hors ligne de rattacher_secondes_fiches.py (couples · piece C, 31/10/2026).

Un FAUX miroir (sqlite en memoire), un FAUX Supabase, un FAUX registre local :
  (1) cas nominal : une fiche designe la personne 1, nom concordant -> rattachee
  (2) a blanc : dit, n'ecrit rien
  (3) deux fiches designent la personne 1 -> doute, rien n'est ecrit, sortie 1
  (4) nom different -> doute
  (5) numero deja porte dans Supabase -> doute
  (6) numero deja connu du registre local -> doute
  (7) la fiche n'est pas encore dans le miroir -> attendre, sortie 0 (pas d'alarme)
  (8) la personne 1 n'a pas encore sa cible -> attendre
  (9) la case a ete pourvue entre-temps (0 ligne) -> dit, sortie 1
 (10) rien a faire -> sortie 0, aucune lecture du miroir
 (11) la personne 1 elle-meme n'est jamais prise pour sa seconde fiche
 (12) noms : accents, tirets, casse

    python phase2/identite/test_rattacher_secondes_fiches.py
    sortie 0 = tout vert · 1 = un controle en echec
"""
from __future__ import annotations

import io
import sqlite3
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rattacher_secondes_fiches as m  # noqa: E402

echecs = []


def controle(nom, ok, detail=""):
    print(f"{'  OK  ' if ok else 'ECHEC '} {nom}{'' if ok else ' -- ' + str(detail)}")
    if not ok:
        echecs.append(nom)


def miroir(fiches):
    """fiches : [(numero, refCouple, nom)]"""
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE hektor_contact (hektor_contact_id TEXT PRIMARY KEY, hektor_couple_contact_id TEXT, nom TEXT)")
    c.executemany("INSERT INTO hektor_contact VALUES (?,?,?)", fiches)
    return c


def registre(lignes=()):
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE app_contact (app_contact_id INTEGER, hektor_contact_id TEXT, hektor_target_id TEXT)")
    c.executemany("INSERT INTO app_contact VALUES (?,?,?)", lignes)
    return c


class FauxSupabase:
    def __init__(self, personnes2, cibles, porteurs=None, lignes_patch=1):
        self._p2 = personnes2
        self._cibles = cibles
        self._porteurs = porteurs or {}
        self._lignes_patch = lignes_patch
        self.ecrit = []

    def personnes2_sans_cible(self):
        return self._p2

    def cibles_des_premieres(self, identites):
        return {i: self._cibles.get(i, "") for i in identites}

    def porteurs(self, numero):
        return self._porteurs.get(numero, [])

    def poser_cible(self, identite, numero):
        self.ecrit.append((identite, numero))
        return self._lignes_patch


def jouer(sb, mir, reg, a_blanc=False):
    tampon = io.StringIO()
    with redirect_stdout(tampon):
        code = m.executer(sb, mir, reg, a_blanc)
    return code, tampon.getvalue()


P2 = {"hektor_contact_id": "20000032", "nom": "Essai Paire", "hektor_couple_contact_id": "20000031"}
CIBLES = {"20000031": "606071"}
MIR_OK = [("606071", "606071", "ESSAI PAIRE"), ("606072", "606071", "ESSAI PAIRE"), ("606073", "606073", "AUTRE")]

# (1)
sb = FauxSupabase([P2], CIBLES)
code, sortie = jouer(sb, miroir(MIR_OK), registre())
controle("1 rattachee", code == 0 and sb.ecrit == [("20000032", "606072")], (code, sb.ecrit, sortie))

# (2)
sb = FauxSupabase([P2], CIBLES)
code, sortie = jouer(sb, miroir(MIR_OK), registre(), a_blanc=True)
controle("2 a blanc : rien n'est ecrit", code == 0 and sb.ecrit == [] and "A BLANC" in sortie, (code, sb.ecrit, sortie))

# (3)
sb = FauxSupabase([P2], CIBLES)
code, sortie = jouer(sb, miroir(MIR_OK + [("606080", "606071", "ESSAI PAIRE")]), registre())
controle("3 deux candidates : doute", code == 1 and sb.ecrit == [] and "DOUTE" in sortie, (code, sb.ecrit, sortie))

# (4)
sb = FauxSupabase([P2], CIBLES)
code, sortie = jouer(sb, miroir([("606071", "606071", "ESSAI PAIRE"), ("606072", "606071", "DURAND")]), registre())
controle("4 nom different : doute", code == 1 and sb.ecrit == [] and "nom" in sortie, (code, sb.ecrit, sortie))

# (5)
sb = FauxSupabase([P2], CIBLES, porteurs={"606072": ["10650999"]})
code, sortie = jouer(sb, miroir(MIR_OK), registre())
controle("5 deja porte dans Supabase : doute", code == 1 and sb.ecrit == [] and "10650999" in sortie, (code, sb.ecrit, sortie))

# (5 bis) porte par la personne 2 elle-meme : pas un conflit
sb = FauxSupabase([P2], CIBLES, porteurs={"606072": ["20000032"]})
code, sortie = jouer(sb, miroir(MIR_OK), registre())
controle("5bis porte par elle-meme : pas un doute", code == 0 and sb.ecrit == [("20000032", "606072")], (code, sb.ecrit, sortie))

# (6)
sb = FauxSupabase([P2], CIBLES)
code, sortie = jouer(sb, miroir(MIR_OK), registre([(10650999, "10650999", "606072")]))
controle("6 deja connu du registre : doute", code == 1 and sb.ecrit == [] and "registre" in sortie, (code, sb.ecrit, sortie))

# (7)
sb = FauxSupabase([P2], CIBLES)
code, sortie = jouer(sb, miroir([("606071", "606071", "ESSAI PAIRE")]), registre())
controle("7 pas encore au miroir : attendre, sans alarme", code == 0 and sb.ecrit == [] and "attend" in sortie, (code, sb.ecrit, sortie))

# (8)
sb = FauxSupabase([P2], {"20000031": ""})
code, sortie = jouer(sb, miroir(MIR_OK), registre())
controle("8 personne 1 sans cible : attendre", code == 0 and sb.ecrit == [] and "attend" in sortie, (code, sb.ecrit, sortie))

# (9)
sb = FauxSupabase([P2], CIBLES, lignes_patch=0)
code, sortie = jouer(sb, miroir(MIR_OK), registre())
controle("9 case pourvue entre-temps : dit, sortie 1", code == 1 and "NON ECRIT" in sortie, (code, sortie))

# (10)
class MiroirInterdit:
    def execute(self, *a, **k):
        raise AssertionError("le miroir ne doit pas etre lu")

sb = FauxSupabase([], {})
code, sortie = jouer(sb, MiroirInterdit(), None)
controle("10 rien a faire : sortie 0, miroir non lu", code == 0 and "rien a faire" in sortie, (code, sortie))

# (11) la seule fiche qui designe la personne 1 est elle-meme -> attendre
sb = FauxSupabase([P2], CIBLES)
code, sortie = jouer(sb, miroir([("606071", "606071", "ESSAI PAIRE")]), registre())
controle("11 la premiere n'est jamais sa seconde", sb.ecrit == [], sb.ecrit)

# (12)
controle("12 noms normalises", m.nom_compare("Le Gall-Hérvé") == m.nom_compare("LE GALL HERVE")
         and m.nom_compare("DURAND") != m.nom_compare("DURANT"))

print("TOUT VERT" if not echecs else f"{len(echecs)} ECHEC(S)")
sys.exit(1 if echecs else 0)
