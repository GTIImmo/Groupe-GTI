# Banc d essai HORS PRODUCTION de phase2/sync/refresh_contact_inproc.py (chantier 8 / 8a).
# Base locale = une petite base FABRIQUEE dans un dossier temporaire.
# Supabase = SIMULE (aucun appel reseau) : rejouable a tout moment, sans rien ecrire.
# Usage : .venv\Scripts\python.exe -I phase2\checks\test_relecture_apprend_la_paire_8a.py
import importlib.util, os, sqlite3, sys, tempfile, pathlib

ICI = pathlib.Path(__file__).resolve().parent
VRAI_ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("rci", VRAI_ROOT / "phase2" / "sync" / "refresh_contact_inproc.py")
rci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rci)

tmp = pathlib.Path(tempfile.mkdtemp(prefix="essai8a_"))
(tmp / "phase2").mkdir()
base = tmp / "phase2" / "phase2.sqlite"
c = sqlite3.connect(base)
c.executescript("""
CREATE TABLE app_contact_current (hektor_contact_id TEXT PRIMARY KEY, hektor_target_id TEXT, nom TEXT);
CREATE TABLE app_contact (app_contact_id INTEGER, hektor_contact_id TEXT, hektor_target_id TEXT);
INSERT INTO app_contact_current VALUES ('10650744','414000','ANCIEN');          -- contact ancien
INSERT INTO app_contact VALUES (10650744,'10650744','414000');
""")
c.commit(); c.close()

# Supabase SIMULE : la paire du contact d'essai du 21/10 (20000006 / 605922, supprime depuis).
# Le 21/10, ce banc a aussi tourne contre la VRAIE vue, en lecture seule : 13 sur 13.
PAIRES = {"20000006": ("20000006", "605922"), "605922": ("20000006", "605922")}
rci.demander_la_paire_a_supabase = lambda numero: PAIRES.get(numero)
rci.ROOT = tmp

def lignes_corresp():
    k = sqlite3.connect(base)
    try:
        return k.execute("SELECT hektor_contact_id, app_identite FROM app_contact_identite_app ORDER BY 1").fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        k.close()

def etapes(numero):
    s = rci._steps(numero)
    return {lab: argv[argv.index("--contact-id") + 1] for lab, _, argv in s}

resultats = []
def verifie(nom, obtenu, attendu):
    ok = obtenu == attendu
    resultats.append(ok)
    print(("OK   " if ok else "ECHEC"), nom, "| obtenu", obtenu, "| attendu", attendu)

# 1. contact ANCIEN par son identite -> chemin d'avant, Hektor vise par 414000
n, a = rci.resoudre_le_numero("10650744")
verifie("1 ancien, identite : resolution", (n, a), ("10650744", None))
verifie("1 ancien, identite : etapes", etapes(n), {"detail": "414000", "normalize": "414000", "build": "10650744", "push": "10650744"})
# 2. contact ANCIEN par son numero Hektor -> connu du registre, chemin d'avant
n, a = rci.resoudre_le_numero("414000")
verifie("2 ancien, numero Hektor : resolution", (n, a), ("414000", None))
verifie("2 : aucune paire ecrite pour les anciens", lignes_corresp(), [])
# 3. contact NE AUJOURD'HUI, par NOTRE numero (vraie paire lue dans Supabase)
n, a = rci.resoudre_le_numero("20000006")
verifie("3 neuf, identite : resolution", (n, a), ("20000006", None))
verifie("3 : la paire est apprise", lignes_corresp(), [("605922", "20000006")])
verifie("3 : Hektor vise par SON numero, la fiche par la NOTRE", etapes(n),
        {"detail": "605922", "normalize": "605922", "build": "20000006", "push": "20000006"})
# 4. LE CAS DU DOUBLON : le meme contact recu avec le numero HEKTOR
k = sqlite3.connect(base); k.execute("DELETE FROM app_contact_identite_app"); k.commit(); k.close()
n, a = rci.resoudre_le_numero("605922")
verifie("4 neuf, numero Hektor : on rend NOTRE numero", (n, a), ("20000006", None))
verifie("4 : etapes (plus de doublon possible)", etapes(n),
        {"detail": "605922", "normalize": "605922", "build": "20000006", "push": "20000006"})
# 5. identite a nous SANS numero Hektor -> ARRET
n, a = rci.resoudre_le_numero("29999999")
verifie("5 identite sans numero Hektor : arret", a is not None and "pas encore de numero Hektor" in a, True)
# 6. numero Hektor inconnu partout -> chemin d'avant (contact cree dans Hektor)
n, a = rci.resoudre_le_numero("9999998")
verifie("6 numero Hektor inconnu : chemin d'avant", (n, a), ("9999998", None))
# 7. Supabase MUET -> ARRET, jamais a l'aveugle
sauve_url = os.environ.get("SUPABASE_URL")
def demande_muette(numero):
    raise OSError("connexion refusee (essai)")
rci.demander_la_paire_a_supabase = demande_muette
n, a = rci.resoudre_le_numero("20000007")
verifie("7 Supabase muet : arret", a is not None and "aveugle" in a, True)
# 8. la derniere barriere de _steps
try:
    rci._steps("29999999"); verifie("8 derniere barriere", "pas d'arret", "arret")
except RuntimeError:
    verifie("8 derniere barriere", "arret", "arret")

print(f"\n{sum(resultats)} sur {len(resultats)} controles verts")
sys.exit(0 if all(resultats) else 1)
