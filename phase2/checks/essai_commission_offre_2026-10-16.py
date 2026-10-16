# -*- coding: utf-8 -*-
"""LE TEMOIN DE L'ESSAI DE COMMISSION — a relancer DEMAIN MATIN.  16/10/2026

═══════════════════════════════════════════════════════════════════════════════
POURQUOI CE FICHIER EXISTE
═══════════════════════════════════════════════════════════════════════════════
Le lot 1 pose trois colonnes de CLASSE A sur `app_affaire_ledger` : l'app seule
les ecrit, dans Supabase, et le run de nuit ne doit JAMAIS les ecraser. Pour que
ca tienne, il faut les trois conditions a la fois :

    ① les colonnes existent chez Supabase
    ② elles sont dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (le push ne les envoie
       pas, sinon la valeur LOCALE -- vide -- ecraserait celle de Supabase)
    ③ elles sont hors du ON CONFLICT DO UPDATE SET local

⚠⚠ ET CE MECANISME N'AVAIT JAMAIS PORTE UNE VALEUR. Mesure du 16/10 : les deux
  colonnes de classe A qui existaient (`taux_honoraires`, `notaire_id`) sont
  VIDES PARTOUT -- 0 en production, 0 en local. J'avais d'abord ecrit « eprouve
  depuis le 03/09 » : c'etait faux. On ne pouvait rien en conclure.

J'ai donc fait deux choses le 16/10 :
  · eprouve la SEMANTIQUE de l'upsert : une ligne renvoyee SANS une colonne la
    laisse intacte (essai reel sur une table a moi, valeur survivante) ;
  · pose une valeur d'essai sur une OFFRE D'ESSAI, pour que le run de nuit
    tranche en vrai. C'est ce que ce fichier verifie.

⭐ LA SEULE PREUVE QUI COMPTE EST LE LENDEMAIN. Tout le reste est un indice.

═══════════════════════════════════════════════════════════════════════════════
L'ESSAI POSE LE 16/10 — note AVANT, pour que le controle soit un controle
═══════════════════════════════════════════════════════════════════════════════
    annonce          24933   le bien d'essai de la console
    affaire          1001339 offre « proposed », seule sur sa chaine (1001339)
    honoraires_entree_app    1234
    honoraires_sortie_app    500
    charge_commission_app    acquereur
    les 6 AUTRES offres de 24933 : laissees VIDES, et elles doivent le rester

⚠ L'essai a ete pose par la CLE DE SERVICE, pas par la RPC : celle-ci exige
  `is_app_manager_or_admin()`, et la cle de service n'a pas d'utilisateur
  (auth.uid() nul) -- elle est donc REFUSEE, ce qui est le bon comportement.
  Le chemin RPC + ecran demande un clic d'un manager connecte : il reste a
  eprouver separement.

LANCEMENT :
    .venv\\Scripts\\python.exe phase2\\checks\\essai_commission_offre_2026-10-16.py
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "phase2" / "sync"))

for _flux in (sys.stdout, sys.stderr):
    try:
        _flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ANNONCE = "24933"
AFFAIRE = 1001339
ATTENDU = {"honoraires_entree_app": "1234",
           "honoraires_sortie_app": "500",
           "charge_commission_app": "acquereur"}
COLONNES = tuple(ATTENDU)
SELECT = "app_affaire_id,kind,state," + ",".join(COLONNES)


def _nombres_egaux(a, b) -> bool:
    """« 1234 » et « 1234.00 » sont la meme valeur. Postgres rend le type de la
    colonne, qui est du texte, mais le run pourrait la reecrire autrement."""
    try:
        return round(float(str(a).replace(",", ".")), 2) == round(
            float(str(b).replace(",", ".")), 2)
    except Exception:
        return str(a).strip() == str(b).strip()


def main() -> int:
    from push_upgrade_to_supabase import (  # noqa: E402
        DEFAULT_ENV_FILES, SupabaseRestClient, load_env_files)

    load_env_files(DEFAULT_ENV_FILES)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        print("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis", file=sys.stderr)
        return 2
    client = SupabaseRestClient(base_url=url, service_role_key=cle)

    rouge = []

    # ── ① la valeur a-t-elle survecu CHEZ SUPABASE ?
    lignes = client._request(method="GET", path="app_affaire_ledger",
                             query={"select": SELECT,
                                    "hektor_annonce_id": f"eq.{ANNONCE}",
                                    "order": "app_affaire_id"})
    cible = next((x for x in lignes if int(x["app_affaire_id"]) == AFFAIRE), None)
    print("① CHEZ SUPABASE")
    if cible is None:
        print(f"   ⛔ l'affaire {AFFAIRE} a DISPARU du registre")
        rouge.append("affaire absente de Supabase")
    else:
        for col, attendu in ATTENDU.items():
            vu = cible.get(col)
            ok = _nombres_egaux(vu, attendu) if col != "charge_commission_app" \
                else str(vu or "").strip() == attendu
            print(f"   {col:24s} attendu {attendu:<10} vu {str(vu):<12} "
                  + ("OK" if ok else "⛔ PERDU"))
            if not ok:
                rouge.append(f"{col} : attendu {attendu}, vu {vu}")

    # ── ② les 6 autres offres doivent etre restees VIDES
    autres = [x for x in lignes if int(x["app_affaire_id"]) != AFFAIRE]
    sales = [x for x in autres if any(x.get(c) for c in COLONNES)]
    print()
    print("② LES AUTRES OFFRES DU BIEN D'ESSAI")
    print(f"   {len(autres)} autre(s) offre(s), dont {len(sales)} portant une valeur"
          f"   (attendu 0)")
    if sales:
        for x in sales:
            print(f"   ⛔ {x['app_affaire_id']} porte "
                  + "/".join(str(x.get(c)) for c in COLONNES))
        rouge.append(f"{len(sales)} autre(s) ligne(s) touchee(s) : le WHERE a debordé")

    # ── ③ la redescente a-t-elle ramene la valeur EN LOCAL ?
    print()
    print("③ EN LOCAL, APRES LA REDESCENTE")
    chemin = ROOT / "phase2" / "phase2.sqlite"
    con = sqlite3.connect(f"file:{chemin.as_posix()}?mode=ro", uri=True)
    try:
        r = con.execute(
            f"SELECT {','.join(COLONNES)} FROM app_affaire_ledger"
            " WHERE app_affaire_id = ?", (AFFAIRE,)).fetchone()
    except sqlite3.OperationalError as erreur:
        print(f"   ⛔ colonnes absentes en local : {erreur}")
        rouge.append("colonnes locales absentes")
        r = None
    con.close()
    if r is not None:
        for col, vu in zip(COLONNES, r):
            attendu = ATTENDU[col]
            ok = (_nombres_egaux(vu, attendu) if col != "charge_commission_app"
                  else str(vu or "").strip() == attendu)
            etat = "OK" if ok else ("pas encore redescendue"
                                    if vu in (None, "") else "⛔ VALEUR DIFFERENTE")
            print(f"   {col:24s} attendu {attendu:<10} vu {str(vu):<12} {etat}")
            # ⚠ Une colonne locale VIDE n'est pas un echec avant la premiere
            #   redescente : le local ne les ECRIT jamais, il les RECOIT.
            if vu not in (None, "") and not ok:
                rouge.append(f"local {col} : attendu {attendu}, vu {vu}")

    print()
    print("═" * 70)
    if rouge:
        print("ESSAI EN ECHEC :")
        for m in rouge:
            print("   ⛔", m)
        return 1
    print("ESSAI TENU : la valeur est intacte chez Supabase, aucune autre ligne")
    print("n'a bouge, et le local ne la contredit pas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
