"""La reprise fait-elle ce qu'elle annonce ? Quatre cas, aucune base de production.

On ne teste pas « la sauvegarde marche » -- on vient de le voir. On teste ce
qu'on ne voit JAMAIS en temps normal : ce qui se passe quand la base est occupee.
"""
import os, sqlite3, sys, time
os.chdir(r"C:\Hektor\Projet")
sys.path.insert(0, "phase2/sync")
import backup_critical as B

B.VERROU_RECUL_S = 0.2          # on ne va pas attendre 3 minutes pour un essai
VERROU = sqlite3.OperationalError("database is locked")

ok = True
def verdict(nom, attendu, obtenu):
    global ok
    bon = attendu == obtenu
    ok = ok and bon
    print("   %-52s %s" % (nom, "OK" if bon else "ECHEC (attendu %r, obtenu %r)" % (attendu, obtenu)))

# ① un verrou passager : on doit reessayer et finir par reussir
essais = []
def occupee_puis_libre():
    essais.append(1)
    if len(essais) < 3:
        raise VERROU
    return "archive"
verdict("verrou passager -> on insiste et on reussit", "archive",
        B.reessayer_si_verrouille("essai", occupee_puis_libre))
verdict("   et on a bien fait trois tentatives", 3, len(essais))

# ② un verrou qui ne lache jamais : on doit LEVER, pas rendre None
try:
    B.reessayer_si_verrouille("essai", lambda: (_ for _ in ()).throw(VERROU))
    verdict("verrou permanent -> on leve", "RuntimeError", "rien leve")
except RuntimeError as e:
    verdict("verrou permanent -> on leve", True, "AUCUNE ARCHIVE" in str(e))

# ③ une VRAIE panne ne doit PAS etre reessayee ni masquee
pannes = []
def vraie_panne():
    pannes.append(1)
    raise sqlite3.DatabaseError("file is not a database")
try:
    B.reessayer_si_verrouille("essai", vraie_panne)
    verdict("panne reelle -> remonte telle quelle", "DatabaseError", "rien leve")
except sqlite3.DatabaseError:
    verdict("panne reelle -> remonte telle quelle", True, True)
verdict("   et elle n'a PAS ete rejouee", 1, len(pannes))

# ④ l'attente est-elle vraiment posee sur la connexion ?
import tempfile, pathlib
tmp = pathlib.Path(tempfile.gettempdir()) / "essai_verrou.sqlite"
sqlite3.connect(tmp).execute("CREATE TABLE IF NOT EXISTS t(x)").connection.commit()
c = B.connect_readonly(tmp, timeout=7.0)
lu = c.execute("PRAGMA busy_timeout").fetchone()[0]
c.close()
verdict("connect_readonly pose le busy_timeout (7 s = 7000 ms)", 7000, lu)
verdict("le defaut du module est bien 60 s", 60.0, B.VERROU_ATTENTE_S)

print("")
print("   >>> " + ("TOUT PASSE" if ok else "IL Y A UN ECHEC"))
sys.exit(0 if ok else 1)
