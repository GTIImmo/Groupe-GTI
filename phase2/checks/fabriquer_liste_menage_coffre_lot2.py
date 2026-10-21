# -*- coding: utf-8 -*-
"""LA LISTE DU LOT 2 -- les documents RETIRES de Hektor dont le coffre garde une copie.

Restreinte aux 63 annonces que la mesure SQL du 21/10 designe (988 fichiers, 1 606 Mo).
Deduite du DISQUE, donc chaque candidat a sa copie serveur PAR CONSTRUCTION -- et c'est
precisement le garde-fou du lot 2 : on ne supprime la copie du coffre que si le serveur
garde la sienne.

⚠ Le nom emis est le nom DU COFFRE (replie en ASCII), pas celui du disque.
LECTURE SEULE : une table lue, aucune requete au coffre.
"""
import io
import json
import os
import sys
import unicodedata
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RACINE = Path("C:/Hektor/Projet")
LOCAL = Path("C:/Hektor/HektorConsoleDocuments/annonces")

LES63 = ["11841", "14383", "14452", "18540", "23417", "24113", "28405", "28548", "32578",
         "32650", "33151", "35884", "40608", "41402", "43437", "46414", "49540", "49624",
         "49854", "54791", "58897", "58903", "59064", "59153", "59198", "59200", "59228",
         "59392", "59449", "59466", "59499", "59624", "59625", "59627", "59651", "61577",
         "61594", "61601", "61654", "61730", "61743", "61756", "61890", "61918", "61935",
         "61943", "61949", "61977", "61986", "62067", "62068", "62167", "62170", "62264",
         "62325", "62352", "62405", "62527", "62764", "62802", "62839", "63086", "63193"]


def charger_env(p):
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        l = raw.strip()
        if not l or l.startswith("#") or "=" not in l:
            continue
        k, v = l.split("=", 1)
        k = k.strip()
        if k and k not in os.environ:
            os.environ[k] = v.strip().strip('"').strip("'")


for f in (RACINE / ".env", RACINE / "Console" / ".env", RACINE / "apps" / "hektor-v1" / ".env"):
    charger_env(f)

URL = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").rstrip("/")
CLE = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
if not URL or not CLE:
    print("ARRET : Supabase introuvable.")
    sys.exit(2)
ENTETES = {"apikey": CLE, "Authorization": f"Bearer {CLE}"}

INTERDITS = set('#%?&{}^`[]')


def replier(nom):
    s = unicodedata.normalize("NFD", nom)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(c if 0x20 <= ord(c) <= 0x7E else "_" for c in s)
    return "".join("_" if c in INTERDITS else c for c in s)


def lire(chemin):
    req = urllib.request.Request(f"{URL}/rest/v1/{chemin}", headers=ENTETES)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode("utf-8"))


# les fiches vivantes de ces 63 annonces (largement sous les 1 000 lignes)
docs = lire("app_console_document?hektor_annonce_id=in.(" + ",".join(LES63) + ")"
            "&select=id,hektor_annonce_id,storage_path&order=id&limit=1000")
vivantes = {d["id"] for d in docs}
noms = {}
for d in docs:
    sp = d.get("storage_path")
    if sp:
        noms.setdefault(str(d["hektor_annonce_id"]), set()).add(sp.rsplit("/", 1)[-1])
print(f"fiches vivantes sur les 63 annonces : {len(docs)}")

candidats = []
exclus_lot1 = compagnons = 0
for a in LES63:
    dossier = LOCAL / a / "documents"
    if not dossier.is_dir():
        continue
    jeu = noms.get(a, set())
    for e in os.scandir(dossier):
        if not e.is_dir():
            continue
        if e.name in vivantes:            # garde-fou 1
            compagnons += 1
            continue
        for f in os.listdir(e.path):
            if not os.path.isfile(os.path.join(e.path, f)):
                continue
            if f.startswith(("signed_", "immosign_")):   # garde-fou 2
                continue
            nom_coffre = replier(f)
            if nom_coffre in jeu:          # une fiche vivante porte ce nom -> LOT 1
                exclus_lot1 += 1
                continue
            candidats.append(f"annonces/{a}/documents/{e.name}/{nom_coffre}")

cible = RACINE / "notice" / "MENAGE_COFFRE_LOT2_2026-10-21.csv"
uniques = sorted(set(candidats))
with open(cible, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# LISTE DU LOT 2 -- documents RETIRES de Hektor, 2026-10-21\n")
    fh.write("# restreinte aux 63 annonces que la mesure SQL designe (988 fichiers au coffre)\n")
    fh.write("# deduite du DISQUE : chaque candidat a sa copie serveur PAR CONSTRUCTION\n")
    fh.write("# ⚠ a lancer avec --lot2 : le garde-fou 3 du lot 1 les refuserait tous\n")
    fh.write("chemin\n")
    for c in uniques:
        fh.write(c + "\n")

print()
print("=" * 72)
print(f"  candidats du LOT 2 ecrits      : {len(uniques)}")
print(f"  ecartes car ils relevent du LOT 1 : {exclus_lot1}")
print(f"  dossiers de fiches vivantes    : {compagnons}  (garde-fou 1)")
print(f"  fichier : {cible.relative_to(RACINE)}")
print("=" * 72)
print("  ⭐ RECOUPEMENT : la mesure SQL du lot 2 donne 988 fichiers au coffre.")
print(f"     ici {len(uniques)} candidats -- un ecart est NORMAL (le disque porte aussi")
print("     des fichiers que le coffre n'a plus ; ceux-la rendront « deja absent »).")
