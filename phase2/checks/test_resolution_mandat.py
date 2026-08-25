# -*- coding: utf-8 -*-
"""Essaie la resolution du mandat par le REGISTRE, comme le worker la fait.

25/08 -- PORTEE CORRIGEE. Ce test a ete ecrit pour C.5, qui resolvait ainsi le mandat des
TRANSACTIONS. C.5 a ete annulee le jour meme : Hektor n'attend pas un numero seul mais un
couple <id>-<FAMILLE>, et le worker recopie desormais a nouveau sa valeur telle quelle.
La requete testee ici reste VIVANTE, mais sur un autre chemin : `resoudreMandatAClore`
(cloture), ou elle sert de second recours quand le libelle de Hektor ne permet pas de
cibler le mandat. Le test garde donc tout son sens -- il ne couvre plus les transactions.

Le worker interroge Supabase avec :
    app_mandat_register_current?select=mandat_source_id
        &hektor_annonce_id=eq.<annonce>&numero_mandat=eq.<numero>&limit=2
et n'accepte QUE si exactement une ligne revient.

On rejoue cette requete sur un echantillon reel et on compare au resultat attendu.
Aucune transaction n'est creee : c'est une lecture.
"""
from __future__ import annotations

import sqlite3
import sys
import urllib.parse
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES, SupabaseRestClient, load_env_file,
)
import os  # noqa: E402

for f in DEFAULT_ENV_FILES:
    load_env_file(f)
url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
cle = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
client = SupabaseRestClient(base_url=url, service_role_key=cle)

p = sqlite3.connect(f"file:{RACINE}/phase2/phase2.sqlite?mode=ro", uri=True)

# Echantillon : 20 annonces a mandat unique + LES 24 a plusieurs mandats.
simples = p.execute("""
    SELECT hektor_annonce_id, numero_mandat, mandat_source_id
      FROM app_mandat_register_current
     WHERE hektor_annonce_id IS NOT NULL AND numero_mandat IS NOT NULL
       AND mandat_source_id IS NOT NULL
       AND app_dossier_id IN (SELECT app_dossier_id FROM (
             SELECT app_dossier_id, count(DISTINCT numero_mandat) n
               FROM app_mandat_register_current GROUP BY 1) WHERE n = 1)
     LIMIT 20""").fetchall()

multiples = p.execute("""
    SELECT hektor_annonce_id, numero_mandat, mandat_source_id
      FROM app_mandat_register_current
     WHERE hektor_annonce_id IS NOT NULL AND numero_mandat IS NOT NULL
       AND mandat_source_id IS NOT NULL
       AND app_dossier_id IN (SELECT app_dossier_id FROM (
             SELECT app_dossier_id, count(DISTINCT numero_mandat) n
               FROM app_mandat_register_current
              WHERE numero_mandat IS NOT NULL GROUP BY 1) WHERE n > 1)""").fetchall()


def essaie(lot, titre):
    ok = rate = ambigu = 0
    for annonce, numero, attendu in lot:
        chemin = (f"app_mandat_register_current?select=mandat_source_id"
                  f"&hektor_annonce_id=eq.{urllib.parse.quote(str(annonce))}"
                  f"&numero_mandat=eq.{urllib.parse.quote(str(numero))}&limit=2")
        rows = client.request(method="GET", path=chemin)
        if not isinstance(rows, list) or len(rows) != 1:
            ambigu += 1
            print(f"   AMBIGU/ABSENT annonce={annonce} numero={numero} -> {rows}")
            continue
        recu = str(rows[0].get("mandat_source_id"))
        if recu == str(attendu):
            ok += 1
        else:
            rate += 1
            print(f"   FAUX  annonce={annonce} numero={numero} "
                  f"attendu={attendu} recu={recu}")
    print(f"{titre}: {ok} resolus juste, {rate} faux, {ambigu} non resolus "
          f"(sur {len(lot)})")
    return rate, ambigu


print("=== ESSAI DE LA RESOLUTION, telle que le worker la fait ===\n")
r1, a1 = essaie(simples, "annonces a UN mandat   ")
r2, a2 = essaie(multiples, "annonces a PLUSIEURS   ")
print()
print("VERDICT :", "aucune resolution fausse" if (r1 + r2) == 0
      else f"{r1+r2} RESOLUTIONS FAUSSES -- a corriger")
print("         ", f"{a1+a2} cas non resolus -> le worker retombe sur le HTML "
                   "et le journalise")
