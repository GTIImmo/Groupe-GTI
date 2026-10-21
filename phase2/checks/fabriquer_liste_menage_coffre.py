# -*- coding: utf-8 -*-
"""LA LISTE DE CANDIDATS -- v3, AVEC LE REPLIAGE ASCII DU NOM.

POURQUOI v3. La v1 comparait un nom DU DISQUE (avec accents) a des noms DU COFFRE
(sans accents : storageSafeFilename replie en ASCII). Tout fichier accentue etait donc
ecarte a tort : 3 656 candidats au lieu de 4 075. Mesure du 21/10, exemples reels :
    disque  « mandat signe.pdf » (avec accent)   ->   coffre  « mandat signe.pdf »
    disque  « ... 40000 EUR H4000 EUR ... »      ->   coffre  « ... 40000_ H4000_ ... »

⚠ `replier()` est une REIMPLEMENTATION de storageSafeFilename. Le script de menage
  verifie de toute facon CHAQUE chemin contre la base avant de supprimer, et un chemin
  mal replie fait un 404 sans consequence. On ne parie donc rien sur cette fonction.

LECTURE SEULE : une seule table lue, aucune requete au coffre, aucun ecrit ailleurs
que dans le CSV.
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
    """Le repliage de storageSafeFilename : NFD, on jette les diacritiques, tout
    non-ASCII imprimable devient _, puis #%?&{}^`[] aussi."""
    s = unicodedata.normalize("NFD", nom)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(c if 0x20 <= ord(c) <= 0x7E else "_" for c in s)
    return "".join("_" if c in INTERDITS else c for c in s)


def tout(table, select, ordre):
    """⭐ ORDRE STABLE OBLIGATOIRE : sans lui la pagination perd des lignes (21/10)."""
    out, offset = [], 0
    while True:
        req = urllib.request.Request(
            f"{URL}/rest/v1/{table}?select={select}&order={ordre}&limit=1000&offset={offset}",
            headers=ENTETES)
        with urllib.request.urlopen(req, timeout=300) as r:
            lot = json.loads(r.read().decode("utf-8"))
        out += lot
        offset += len(lot)
        if len(lot) < 1000:
            return out


print("lecture des fiches vivantes...")
docs = tout("app_console_document", "id,hektor_annonce_id,storage_path", "id")
vivantes = {d["id"] for d in docs}
noms = {}
for d in docs:
    sp = d.get("storage_path")
    if sp:
        noms.setdefault(str(d["hektor_annonce_id"]), set()).add(sp.rsplit("/", 1)[-1])
print(f"  {len(docs)} fiches lues, {len(vivantes)} identifiants vivants")

candidats = []
exacts = replies = compagnons = hors_lot = 0

for ann in os.scandir(LOCAL):
    if not ann.is_dir():
        continue
    dossier = os.path.join(ann.path, "documents")
    if not os.path.isdir(dossier):
        continue
    jeu = noms.get(ann.name, set())
    for e in os.scandir(dossier):
        if not e.is_dir():
            continue
        if e.name in vivantes:          # garde-fou 1
            compagnons += 1
            continue
        for f in os.listdir(e.path):
            if not os.path.isfile(os.path.join(e.path, f)):
                continue
            if f.startswith(("signed_", "immosign_")):   # garde-fou 2
                continue
            nom_coffre = replier(f)
            if nom_coffre not in jeu:                     # garde-fou 3
                hors_lot += 1
                continue
            if nom_coffre == f:
                exacts += 1
            else:
                replies += 1
            candidats.append(f"annonces/{ann.name}/documents/{e.name}/{nom_coffre}")

cible = RACINE / "notice" / "MENAGE_COFFRE_LOT1_2026-10-21.csv"
with open(cible, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# LISTE DE CANDIDATS -- menage du coffre, lot 1, 2026-10-21 (v3)\n")
    fh.write("# deduite du DISQUE, avec REPLIAGE ASCII du nom (comme storageSafeFilename)\n")
    fh.write("# ⚠ CE N'EST PAS UNE DECISION : le script revérifie CHAQUE ligne avant de supprimer\n")
    fh.write("chemin\n")
    for c in sorted(set(candidats)):
        fh.write(c + "\n")

uniques = len(set(candidats))
print()
print("=" * 72)
print(f"  candidats ecrits                  : {uniques}")
print(f"     dont nom identique au disque   : {exacts}")
print(f"     dont nom REPLIE (accents, EUR) : {replies}")
print(f"  dossiers de fiches vivantes       : {compagnons}  (garde-fou 1, jamais touches)")
print(f"  ecartes, sans jumelle vivante     : {hors_lot}  (le lot 2 et au-dela)")
if len(candidats) != uniques:
    print(f"  ⚠ {len(candidats) - uniques} doublon(s) de chemin retire(s)")
print(f"  fichier : {cible.relative_to(RACINE)}")
print("=" * 72)
print("  ⭐ RECOUPEMENT : la mesure SQL du lot 1 donne 4 103.")
print(f"     ici {uniques} -> ecart de {4103 - uniques}, qui reste NON EXPLIQUE")
print("     (probablement des fichiers du coffre sans copie locale -- et les ecarter")
print("      est PLUS PRUDENT, pas moins).")
