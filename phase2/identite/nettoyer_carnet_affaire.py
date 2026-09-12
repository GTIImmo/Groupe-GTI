#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE CARNET DES SAISIES, NETTOYE DE CE QU'IL N'A PLUS A PROTEGER.  12/09/2026

LA REGLE VIENT DU PLAN, et elle y est ecrite en toutes lettres :

    « ON NE PROTEGE PAS LA DONNEE, ON PROTEGE L'ECRITURE. Ce que l'app a saisi
      n'est pas une valeur qu'elle possede : c'est une ECRITURE EN ATTENTE (...).
      Une valeur possedee ecrase Hektor pour toujours ; une saisie en attente
      cherche a le rejoindre, et DISPARAIT UNE FOIS ARRIVEE. »

Le worker applique desormais cette regle A CHAUD : quand il a prouve que Hektor
porte la valeur envoyee, il retire la saisie du carnet (prouverTransactionModifiee,
11/09). Ce script traite LE STOCK -- les saisies posees avant ce correctif, qui
ne repasseront jamais par une modification.

⚠ IL N'ECRIT RIEN CHEZ HEKTOR et ne lit que Supabase et le miroir local.

CE QU'IL RETIRE, ET RIEN D'AUTRE -- trois motifs, chacun demontrable :

  1. AFFAIRE MORTE. L'affaire est annulee/refusee, ou elle n'a jamais recu de
     numero Hektor. Une saisie qui attend de rejoindre une transaction qui
     n'existe pas n'attend plus rien.
  2. TRACE D'ESSAI. `origine` dit que la ligne vient d'un essai, pas d'un geste
     d'utilisateur. Le cas est deja au dossier : « retirer la trace d'essai --
     affaire 9 : 123 456 au lieu de 79 000 ».
  3. ARRIVEE. La valeur de l'app est CELLE QUE LE MIROIR PORTE. Elle a donc
     rejoint Hektor : elle n'a plus a etre protegee.

CE QU'IL NE TOUCHE PAS, et c'est le plus important : une saisie qui DIVERGE de
Hektor reste. C'est une correction qui n'est pas encore partie, et la retirer
serait perdre la saisie de quelqu'un.

⚠ ON COMPARE AU MIROIR, PAS AU REGISTRE. Le registre porte deja, pour les cinq
  colonnes reposees, ce que l'app detient : s'y comparer reviendrait a se
  regarder dans une glace et a tout declarer arrive.

IDEMPOTENT : rejouer n'ote rien de plus.
RETOUR ARRIERE : aucun automatique -- ce qui est retire l'est. Le script affiche
donc TOUT ce qu'il va faire, et --dry-run est le mode par defaut du doute.

    python phase2/identite/nettoyer_carnet_affaire.py --dry-run
    python phase2/identite/nettoyer_carnet_affaire.py --appliquer
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)

MIROIR = RACINE / "data" / "hektor.sqlite"
CARNET = "app_affaire_champ_app"
LEDGER = "app_affaire_ledger"
ETATS_MORTS = {"cancelled", "refused"}

# La colonne du miroir qui porte, pour chaque genre, ce que HEKTOR dit du champ.
# Ce qui n'y figure pas ne peut pas etre juge : on garde, par prudence.
MIROIR_PAR_CHAMP = {
    "compromis": {
        "montant": ("hektor_compromis", "prix_publique"),
        "prix_publique": ("hektor_compromis", "prix_publique"),
        "prix_net_vendeur": ("hektor_compromis", "prix_net_vendeur"),
        "sequestre": ("hektor_compromis", "sequestre"),
        "date": ("hektor_compromis", "date_start"),
        "date_acte": ("hektor_compromis", "date_signature_acte"),
    },
    "offre": {
        "montant": ("hektor_offre", "raw_montant"),
        "date": ("hektor_offre", "offre_event_date"),
    },
    "vente": {
        "montant": ("hektor_vente", "prix"),
        "prix_publique": ("hektor_vente", "prix"),
        "date": ("hektor_vente", "date_vente"),
    },
}


def client() -> SupabaseRestClient | None:
    for f in DEFAULT_ENV_FILES:
        load_env_file(f)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return None
    return SupabaseRestClient(base_url=url, service_role_key=cle)


def pareil(a, b) -> bool:
    """Deux valeurs disent-elles la meme chose ? « 177000 » et « 177000.00 » : oui."""
    x = str(a if a is not None else "").strip().replace(",", ".")
    y = str(b if b is not None else "").strip().replace(",", ".")
    if not x or not y:
        return False
    if x == y:
        return True
    try:
        return float(x) == float(y)
    except ValueError:
        return False


def lire_tout(cl: SupabaseRestClient, table: str, champs: str, cle_ordre: str) -> list[dict]:
    """PostgREST plafonne a 1 000 lignes : on pagine, sinon on conclut sur un bout."""
    out: list[dict] = []
    depart = 0
    while True:
        page = cl.request(method="GET", path=(
            f"{table}?select={champs}&order={cle_ordre}.asc&offset={depart}&limit=1000"))
        if not isinstance(page, list) or not page:
            break
        out.extend(page)
        depart += len(page)
        if len(page) < 1000:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--appliquer", action="store_true",
                    help="Retirer pour de bon. Sans lui, on montre et on ne touche a rien.")
    args = ap.parse_args()

    cl = client()
    if cl is None:
        return 1

    carnet = lire_tout(cl, CARNET, "app_affaire_id,champ,valeur_app,origine", "app_affaire_id")
    affaires = {int(a["app_affaire_id"]): a for a in lire_tout(
        cl, LEDGER, "app_affaire_id,kind,hektor_affaire_id,state", "app_affaire_id")
        if a.get("app_affaire_id") is not None}
    print("carnet         %4d lignes sur %d affaires" % (
        len(carnet), len({c["app_affaire_id"] for c in carnet})))

    mir = sqlite3.connect(f"file:{MIROIR.as_posix()}?mode=ro", uri=True)

    def chez_hektor(genre: str, champ: str, tid: str):
        table_col = MIROIR_PAR_CHAMP.get(genre, {}).get(champ)
        if not table_col or not tid:
            return None
        table, col = table_col
        cle = {"compromis": "hektor_compromis_id", "offre": "hektor_offre_id",
               "vente": "hektor_vente_id"}[genre]
        try:
            r = mir.execute(f'SELECT "{col}" FROM {table} WHERE {cle} = ?', (str(tid),)).fetchone()
        except sqlite3.Error:
            return None
        return r[0] if r else None

    a_retirer: list[tuple[int, str, str]] = []
    gardees = 0
    for ligne in carnet:
        aid = int(ligne["app_affaire_id"])
        champ = str(ligne["champ"])
        val = ligne.get("valeur_app")
        aff = affaires.get(aid)
        if aff is None:
            a_retirer.append((aid, champ, "affaire absente du registre"))
            continue
        etat = str(aff.get("state") or "").strip().lower()
        tid = str(aff.get("hektor_affaire_id") or "").strip()
        if etat in ETATS_MORTS or not tid:
            a_retirer.append((aid, champ, "affaire morte ou sans numero Hektor"))
            continue
        if str(ligne.get("origine") or "").startswith("essai"):
            a_retirer.append((aid, champ, "trace d'essai"))
            continue
        ref = chez_hektor(str(aff.get("kind") or ""), champ, tid)
        if ref is not None and pareil(val, ref):
            a_retirer.append((aid, champ, "arrivee : le miroir porte la meme valeur"))
        else:
            gardees += 1

    motifs: dict[str, int] = {}
    for _, _, m in a_retirer:
        motifs[m] = motifs.get(m, 0) + 1
    print()
    print("-- CE QUI PART --")
    for m, n in sorted(motifs.items(), key=lambda x: -x[1]):
        print("   %-42s %4d" % (m, n))
    print("   %-42s %4d" % ("TOTAL", len(a_retirer)))
    print()
    print("-- CE QUI RESTE (saisie qui n'a pas rejoint Hektor) --")
    print("   %-42s %4d" % ("gardees", gardees))
    print()
    for aid, champ, m in a_retirer[:40]:
        print("   affaire %-9s %-20s %s" % (aid, champ, m))
    if len(a_retirer) > 40:
        print("   ... et %d autres" % (len(a_retirer) - 40))

    if not args.appliquer:
        print("\n--dry-run (defaut) : RIEN n'a ete retire. Ajouter --appliquer.")
        return 0

    for aid, champ, _ in a_retirer:
        cl.request(method="DELETE", path=(
            f"{CARNET}?app_affaire_id=eq.{aid}&champ=eq.{champ}"))
    reste = lire_tout(cl, CARNET, "app_affaire_id,champ", "app_affaire_id")
    print("\ncarnet apres   %4d lignes   (-%d)" % (len(reste), len(carnet) - len(reste)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
