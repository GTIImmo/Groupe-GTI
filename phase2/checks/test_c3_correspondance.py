#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C-3 — REPETITION : la correspondance arrive ENTIERE, ou pas du tout.
                                                                  23/09/2026

CE QU'ON EPROUVE, et pourquoi chaque controle existe :

  ① LA PAGINATION. La version du 21/09 demandait `limit=10000` en une fois.
     PostgREST plafonne ses reponses : il rend une page et se tait. Avec 0 ou 1
     ligne cela ne se voyait pas. A la bascule la vue en rend 61 984 -- la
     correspondance serait arrivee TRONQUEE, et chaque contact manquant aurait
     ete range sous son numero Hektor, c'est-a-dire une SECONDE FICHE.
     On sert ici 2 pages et demie a un faux serveur et on verifie que tout
     arrive.

  ② LE GARDE-FOU DE FORME. L'ancien refusait au-dela de 5 000 lignes. A la
     bascule, 61 984 lignes sont NORMALES -- et on ne repare pas ce garde-fou en
     l'augmentant : si un parc entier devient normal, un derapage aussi. On
     verifie donc que le nouveau controle laisse passer un parc entier sain et
     ARRETE les quatre formes de derapage.

  ③ L'INVARIANT DU BUILD. L'etape qui remplit la table est NON BLOQUANTE. Apres
     la bascule, construire sans correspondance rangerait tout un parc sous les
     numeros de Hektor en recalculant les empreintes. On verifie que le build
     s'arrete dans ce cas -- et SURTOUT qu'il ne s'arrete PAS aujourd'hui.

  ④ LE CHEMIN INVERSE. Il a ete transforme en table ; on verifie qu'il rend
     toujours la meme chose.

N'APPELLE NI HEKTOR NI SUPABASE. Tout est en memoire.
"""
from __future__ import annotations

import io
import json
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "identite"))
sys.path.insert(0, str(RACINE / "phase2" / "contacts"))

import descendre_correspondance_contacts as corr  # noqa: E402
import build_contacts_layer as build  # noqa: E402

echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


# ── ① LA PAGINATION ────────────────────────────────────────────────────────
def epreuve_pagination() -> None:
    total = 2 * corr.PAGE + 137  # deux pages pleines et un reste
    parc = [{"hektor_contact_id": str(600000 + i),
             "app_identite": str(10_000_000 + i)} for i in range(total)]
    appels: list[int] = []

    class FausseReponse(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def faux_urlopen(requete, timeout=None):
        adresse = requete.full_url
        depart = int(adresse.split("offset=")[1].split("&")[0])
        taille = int(adresse.split("limit=")[1].split("&")[0])
        appels.append(depart)
        page = parc[depart:depart + taille]
        return FausseReponse(json.dumps(page).encode("utf-8"))

    vrai = corr.urllib.request.urlopen
    import os
    os.environ.setdefault("SUPABASE_URL", "https://exemple.invalid")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "faux")
    corr.urllib.request.urlopen = faux_urlopen
    try:
        lues = corr.lire_supabase()
    finally:
        corr.urllib.request.urlopen = vrai

    controle("(1) la correspondance arrive ENTIERE (pas de troncature)",
             len(lues) == total, f"{len(lues)} au lieu de {total}")
    controle("(1) elle a bien ete lue en plusieurs pages",
             len(appels) >= 3, f"{len(appels)} appel(s)")
    controle("(1) aucune ligne perdue ni doublee",
             len({l["hektor_contact_id"] for l in lues}) == total)
    # L'ANCIENNE FORME, pour memoire : une seule requete plafonnee a PAGE.
    controle("(1) la forme d'AVANT aurait tronque",
             len(parc[:corr.PAGE]) < total)


# ── ② LE GARDE-FOU DE FORME ────────────────────────────────────────────────
def epreuve_garde_fou() -> None:
    sain = [{"hektor_contact_id": str(600000 + i),
             "app_identite": str(10_000_000 + i)} for i in range(61_984)]
    controle("(2) un parc ENTIER et sain passe (61 984 lignes)",
             corr.verifier_la_correspondance(sain) == [])

    controle("(2) une identite hors de notre plage est refusee",
             corr.verifier_la_correspondance(
                 [{"hektor_contact_id": "605450", "app_identite": "999"}]) != [])
    controle("(2) un numero Hektor dans NOTRE plage est refuse",
             corr.verifier_la_correspondance(
                 [{"hektor_contact_id": "10000005", "app_identite": "10000006"}]) != [])
    controle("(2) DEUX identites qui visent le meme numero Hektor sont refusees",
             corr.verifier_la_correspondance([
                 {"hektor_contact_id": "605450", "app_identite": "10000001"},
                 {"hektor_contact_id": "605450", "app_identite": "10000002"}]) != [])
    controle("(2) une identite qui vise DEUX numeros Hektor est refusee",
             corr.verifier_la_correspondance([
                 {"hektor_contact_id": "605450", "app_identite": "10000001"},
                 {"hektor_contact_id": "605451", "app_identite": "10000001"}]) != [])
    controle("(2) une valeur non numerique est refusee",
             corr.verifier_la_correspondance(
                 [{"hektor_contact_id": "abc", "app_identite": "10000001"}]) != [])


# ── ③ L'INVARIANT DU BUILD ─────────────────────────────────────────────────
def base_temoin(identites_app: int, correspondances: int) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT)")
    conn.executemany("INSERT INTO app_contact_current VALUES (?)",
                     [(str(605000 + i),) for i in range(50)])
    conn.executemany("INSERT INTO app_contact_current VALUES (?)",
                     [(str(10_000_000 + i),) for i in range(identites_app)])
    conn.execute("CREATE TABLE app_contact_identite_app"
                 " (hektor_contact_id TEXT, app_identite TEXT, vu_le TEXT)")
    conn.executemany("INSERT INTO app_contact_identite_app VALUES (?,?,'')",
                     [(str(605000 + i), str(10_000_000 + i)) for i in range(correspondances)])
    return conn


def epreuve_invariant() -> None:
    # AUJOURD'HUI : aucune identite dans la plage, correspondance vide.
    try:
        build.charger_identites_app(base_temoin(0, 0))
        controle("(3) AUJOURD'HUI le build ne s'arrete PAS (garde dormante)", True)
    except RuntimeError as err:
        controle("(3) AUJOURD'HUI le build ne s'arrete PAS (garde dormante)", False, str(err))

    # APRES LA BASCULE, correspondance perdue : il DOIT s'arreter.
    try:
        build.charger_identites_app(base_temoin(1000, 0))
        controle("(3) APRES la bascule, sans correspondance, le build S'ARRETE", False,
                 "il a construit quand meme")
    except RuntimeError:
        controle("(3) APRES la bascule, sans correspondance, le build S'ARRETE", True)

    # APRES LA BASCULE, correspondance presente : il continue.
    try:
        n = build.charger_identites_app(base_temoin(1000, 1000))
        controle("(3) APRES la bascule, AVEC la correspondance, il continue", n == 1000, f"{n}")
    except RuntimeError as err:
        controle("(3) APRES la bascule, AVEC la correspondance, il continue", False, str(err))


# ── ④ LE CHEMIN INVERSE ────────────────────────────────────────────────────
def epreuve_chemin_inverse() -> None:
    build.charger_identites_app(base_temoin(10, 10))
    controle("(4) l'identite rend le numero du MIROIR",
             build.numero_hektor_pour_le_miroir("10000003") == "605003",
             build.numero_hektor_pour_le_miroir("10000003"))
    controle("(4) un numero inconnu se rend lui-meme",
             build.numero_hektor_pour_le_miroir("999999") == "999999")
    controle("(4) et l'aller marche toujours",
             build.identite_app("605003") == "10000003")


for epreuve in (epreuve_pagination, epreuve_garde_fou,
                epreuve_invariant, epreuve_chemin_inverse):
    epreuve()

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Tous les controles passent : la correspondance arrive entiere, ou le build s'arrete.")
