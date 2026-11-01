"""COUPLES · PHASE 1 (01/11/2026) — LE CLASSEUR DE L'ANCIEN LOGICIEL, CHARGE UNE FOIS.

Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §3 (T2) et §4 (étape 2).

POURQUOI. La migration vers Hektor (~01/03/2026) a perdu la civilite « Madame » :
51 672 fiches sur 51 810 sont arrivees VIDES (AUDIT_COUPLES_ANCIENS… §9). Le seul
endroit qui la connait encore est le classeur exporte de l'ancien logiciel
(`contacts_extraits.xlsx`, 27/02/2026). Il n'a AUCUNE cle commune avec Hektor : on
apparie par le nom + la date de creation (recopiee au jour pres), puis l'e-mail,
le telephone, le nom + prenom -- la methode de l'audit (194 170 sur 202 218).

CE QUE FAIT CE SCRIPT : il remplit la table locale `ancien_logiciel_contact` de
phase2.sqlite, et rien d'autre :
    ancien_contact_id, gender, hektor_contact_id (numero HEKTOR, ou NULL), methode
⛔ AUCUN NOM, AUCUNE COORDONNEE n'y est recopie : le classeur contient des donnees
   personnelles, il ne va ni dans git, ni chez Supabase, ni dans cette table au-dela
   de la civilite et de l'appariement. Le classeur reste a la racine, ignore par git.

Il ne tourne PAS la nuit : le classeur ne bouge plus (il date d'avant la migration).
L'etape de nuit `nature_des_fiches.py` lit cette table ; absente, elle ne rend
simplement pas « Madame ».

Usage :
    python phase2/contacts/charger_ancien_logiciel.py            (remplace la table)
    python phase2/contacts/charger_ancien_logiciel.py --a-blanc  (compte, n'ecrit rien)
Sortie : 0 = fait · 1 = echec.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
DEFAULT_HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
DEFAULT_CLASSEUR = ROOT / "contacts_extraits.xlsx"
TABLE = "ancien_logiciel_contact"


def normaliser(valeur: Any) -> str:
    texte = unicodedata.normalize("NFKD", str(valeur or "").strip().lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", texte)


def telephone(valeur: Any) -> str:
    chiffres = re.sub(r"\D", "", str(valeur or ""))
    return chiffres[-9:] if len(chiffres) >= 9 else ""


def indexer_hektor(fiches: Iterable[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict]]:
    """Les fiches Hektor normalisees, et les quatre index de l'appariement."""
    H: dict[str, dict[str, Any]] = {}
    for f in fiches:
        hid = str(f["hektor_contact_id"])
        lien = f.get("hektor_couple_contact_id")
        H[hid] = {
            "id": hid, "nom": normaliser(f.get("nom")), "pre": normaliser(f.get("prenom")),
            "lien": str(lien) if lien else None, "d": str(f.get("date_enregistrement") or "")[:10],
            "em": normaliser(f.get("email")), "tel": telephone(f.get("portable")) or telephone(f.get("fixe")),
        }
    idx: dict[str, dict] = {k: defaultdict(list) for k in ("nd", "em", "tel", "np")}
    for h in H.values():
        if h["nom"] and h["d"]:
            idx["nd"][(h["nom"], h["d"])].append(h["id"])
        if h["em"]:
            idx["em"][h["em"]].append(h["id"])
        if h["tel"]:
            idx["tel"][h["tel"]].append(h["id"])
        if h["nom"]:
            idx["np"][(h["nom"], h["pre"])].append(h["id"])
    return H, idx


def apparier(ancienne: dict[str, Any], H: dict[str, dict[str, Any]], idx: dict[str, dict]) -> tuple[str | None, str]:
    """(numero Hektor, methode) d'une fiche de l'ancien logiciel -- (None, 'non_trouvee') sinon.

    Fonction PURE, celle de l'audit du 01/11 : on prend la PREMIERE cle qui designe
    UNE seule fiche ; si elle en designe plusieurs, on garde celle qui a le meme nom
    ET la meme date, si elle est unique (methode suffixee « + »).
    """
    nom, pre = normaliser(ancienne.get("last_name")), normaliser(ancienne.get("first_name"))
    date = str(ancienne.get("time_created") or "")[:10]
    em = normaliser(ancienne.get("email"))
    tl = telephone(ancienne.get("phone_mobile")) or telephone(ancienne.get("phone_fixed"))
    for cle, valeur in (("nd", (nom, date)), ("em", em), ("tel", tl), ("np", (nom, pre))):
        if not (valeur[0] if isinstance(valeur, tuple) else valeur):
            continue
        ids = idx[cle].get(valeur, [])
        if cle == "nd":
            # une fiche principale ou sans foyer plutot qu'une seconde fiche au nom recopie
            ids = [i for i in ids if H[i]["lien"] in (None, i)] or ids
        if len(ids) == 1:
            return ids[0], cle
        if len(ids) > 1:
            fines = [i for i in ids if H[i]["nom"] == nom and H[i]["d"] == date]
            if len(fines) == 1:
                return fines[0], cle + "+"
    return None, "non_trouvee"


def lire_classeur(chemin: Path) -> list[dict[str, Any]]:
    import openpyxl  # noqa: PLC0415 -- seulement pour ce chargement ponctuel

    feuille = openpyxl.load_workbook(chemin, read_only=True).worksheets[0]
    lignes = feuille.iter_rows(values_only=True)
    entete = next(lignes)
    return [dict(zip(entete, ligne)) for ligne in lignes]


def lire_hektor(chemin: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(f"file:{chemin.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(
            "SELECT hektor_contact_id, nom, prenom, hektor_couple_contact_id, date_enregistrement, "
            "email, portable, fixe FROM hektor_contact")]
    finally:
        conn.close()


def ecrire(conn: sqlite3.Connection, lignes: list[tuple[int, int | None, str | None, str]]) -> None:
    """Remplace la table en une seule transaction."""
    charge_le = datetime.now().isoformat(timespec="seconds")
    with conn:
        conn.execute(f"DROP TABLE IF EXISTS {TABLE}")
        conn.execute(f"""
            CREATE TABLE {TABLE} (
                ancien_contact_id INTEGER PRIMARY KEY,
                gender INTEGER,
                hektor_contact_id TEXT,
                methode TEXT NOT NULL,
                charge_le TEXT NOT NULL
            )""")
        conn.executemany(f"INSERT INTO {TABLE} VALUES (?, ?, ?, ?, ?)",
                         [(a, g, h, m, charge_le) for a, g, h, m in lignes])
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_hektor ON {TABLE}(hektor_contact_id)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--classeur", type=Path, default=DEFAULT_CLASSEUR)
    ap.add_argument("--hektor-db", type=Path, default=DEFAULT_HEKTOR_DB)
    ap.add_argument("--phase2-db", type=Path, default=DEFAULT_PHASE2_DB)
    ap.add_argument("--a-blanc", action="store_true")
    args = ap.parse_args()
    if not args.classeur.exists():
        print(f"[ancien logiciel] classeur introuvable : {args.classeur}", file=sys.stderr)
        return 1
    anciennes = lire_classeur(args.classeur)
    H, idx = indexer_hektor(lire_hektor(args.hektor_db))
    lignes = []
    methodes: Counter[str] = Counter()
    for a in anciennes:
        hid, methode = apparier(a, H, idx)
        methodes[methode] += 1
        lignes.append((int(a["contact_id"]), a.get("gender"), hid, methode))
    visees = Counter(h for _, _, h, _ in lignes if h)
    print(f"[ancien logiciel] {len(anciennes)} fiche(s) lue(s), {sum(v for k, v in methodes.items() if k != 'non_trouvee')} "
          f"appariee(s) : " + ", ".join(f"{k} {v}" for k, v in sorted(methodes.items()))
          + f" ; {sum(1 for v in visees.values() if v > 1)} fiche(s) Hektor visee(s) plusieurs fois")
    if args.a_blanc:
        print("[ancien logiciel] A BLANC : rien n'est ecrit")
        return 0
    conn = sqlite3.connect(args.phase2_db, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        ecrire(conn, lignes)
    finally:
        conn.close()
    print(f"[ancien logiciel] table {TABLE} remplie : {len(lignes)} ligne(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
