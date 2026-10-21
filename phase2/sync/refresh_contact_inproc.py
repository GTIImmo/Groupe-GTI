#!/usr/bin/env python3
"""Read-through contact en UN SEUL process (optimisation n°8).

Enchaîne les 4 étapes du rafraîchissement d'un contact —
  1) sync_contact_details (ContactById Hektor)
  2) normalize_source
  3) build_contacts_layer
  4) push_contacts_to_supabase
— dans un SEUL démarrage Python, au lieu de 4 process séparés (~3 s de démarrage
chacun). Reproduit À L'IDENTIQUE les commandes lancées par le worker
(`runContactRefreshPipeline`), via runpy → même sémantique que `python xxx.py`
(mêmes flags, même cwd, mêmes chemins). Les 4 scripts d'origine ne sont PAS modifiés.

Arrêt à la 1re étape en échec (comme l'enchaînement séquentiel actuel du worker).
Code de sortie : 0 = OK, sinon le code de l'étape fautive.

Usage : python phase2/sync/refresh_contact_inproc.py --contact-id <id>
"""
from __future__ import annotations

import argparse
import os
import runpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def cible_hektor(identite: str) -> str:
    """Le numero que HEKTOR comprend, pour ce contact.

    ⚠ C-6, 23/09/2026 -- QUATRE ETAPES, DEUX LANGUES. Le worker appelle ce point
      d'entree avec le numero que le front connait : l'IDENTITE. Or les etapes 1
      et 2 ne parlent pas cette langue -- l'une interroge Hektor, l'autre ecrit
      dans le MIROIR, qui est une copie de Hektor. Tant que les deux numeros sont
      egaux, un seul argument suffit ; a la bascule, ouvrir une fiche contact
      aurait envoye notre numero chez Hektor (404, puis liste noire) et fait
      ecrire une fiche vide dans le miroir sous notre numero.

    En cas de doute -- base illisible, contact inconnu -- on rend l'identite,
    c'est-a-dire le comportement d'avant.
    """
    texte = str(identite or "").strip()
    if not texte.isdigit():
        return texte
    try:
        import sqlite3
        conn = sqlite3.connect(str(ROOT / "phase2" / "phase2.sqlite"), timeout=30)
        try:
            ligne = conn.execute(
                "SELECT hektor_target_id FROM app_contact_current "
                "WHERE hektor_contact_id = ? LIMIT 1", (texte,)).fetchone()
        finally:
            conn.close()
    except Exception:
        return texte
    cible = str(ligne[0] or "").strip() if ligne else ""
    return cible or texte


# ═══════════════════════════════════════════════════════════════════════════
# CHANTIER 8 / 8a, 21/10/2026 -- LA RELECTURE APPREND LA PAIRE TOUT DE SUITE
# ═══════════════════════════════════════════════════════════════════════════
# LE DEFAUT, mesure en reel le 21/10 sur le contact d'essai 20000006 / 605922.
# Le serveur n'apprend la paire « identite <-> numero Hektor » d'un contact ne
# dans l'app que LA NUIT (descendre_correspondance_contacts.py, run l. 670). Une
# relecture lancee le jour meme ne la trouve donc nulle part en local :
#   - recue avec NOTRE numero, cible_hektor() le rend tel quel -> Hektor est
#     interroge avec 20000006 (404, liste noire, fiche vide dans le miroir) ;
#   - recue avec le numero HEKTOR (c'est ce que fait le worker apres une
#     creation, console_job_worker.js:18225), le build ne sait pas le traduire
#     -> une SECONDE fiche sous 605922. C'est arrive le 21/10 a 16:04.
# Le script de nuit est ne le 21/09 contre exactement ce doublon : il ne
# protegeait que la nuit.
#
# LE REMEDE : avant les 4 etapes, si la paire est inconnue en local, on la
# demande a Supabase (la MEME vue que la descente de nuit) et on l'ecrit dans
# app_contact_identite_app -- une ligne, INSERT OR REPLACE. Le build et le
# registre des liens la lisent deja ; la descente de nuit la reecrira a
# l'identique. Rien d'autre ne change : un contact dont la paire est connue en
# local (les 356 000 autres) suit exactement le chemin d'avant.
#
# ⛔ LA REGLE QUI NE SE DISCUTE PAS : une identite a nous ne part JAMAIS chez
#    Hektor. Si sa paire est introuvable (pas encore creee chez Hektor, ou
#    Supabase muet), la relecture S'ARRETE en erreur au lieu de viser a l'aveugle.
PLAGE_NUMEROS_APP = 10_000_000
TABLE_CORRESPONDANCE = "app_contact_identite_app"
VUE_CORRESPONDANCE = "app_v_correspondance_identite_cible"


def paire_connue_en_local(numero: str) -> bool:
    """La base du serveur sait-elle deja traduire ce numero ?

    Un numero de Hektor (< 10 M) est connu si le registre ou la table descendue
    le relie a une identite, ou s'il est lui-meme une identite de la couche. Une
    identite a nous (>= 10 M) est connue si on sait quel numero Hektor elle vise.
    """
    import sqlite3
    conn = sqlite3.connect(str(ROOT / "phase2" / "phase2.sqlite"), timeout=30)
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        requetes = []
        if int(numero) >= PLAGE_NUMEROS_APP:
            requetes += [
                ("app_contact_current", "SELECT 1 FROM app_contact_current WHERE hektor_contact_id = ? "
                 "AND COALESCE(TRIM(hektor_target_id), '') <> '' LIMIT 1"),
                ("app_contact", "SELECT 1 FROM app_contact WHERE hektor_contact_id = ? "
                 "AND COALESCE(TRIM(hektor_target_id), '') <> '' LIMIT 1"),
                (TABLE_CORRESPONDANCE, f"SELECT 1 FROM {TABLE_CORRESPONDANCE} WHERE app_identite = ? LIMIT 1"),
            ]
        else:
            requetes += [
                ("app_contact", "SELECT 1 FROM app_contact WHERE hektor_target_id = ? LIMIT 1"),
                (TABLE_CORRESPONDANCE, f"SELECT 1 FROM {TABLE_CORRESPONDANCE} WHERE hektor_contact_id = ? LIMIT 1"),
                ("app_contact_current", "SELECT 1 FROM app_contact_current WHERE hektor_contact_id = ? LIMIT 1"),
            ]
        for table, sql in requetes:
            if table in tables and conn.execute(sql, (numero,)).fetchone():
                return True
        return False
    finally:
        conn.close()


def demander_la_paire_a_supabase(numero: str) -> tuple[str, str] | None:
    """(identite, numero Hektor) pour un contact ne dans l'app, lu dans la vue de
    la descente de nuit. None si la vue ne le connait pas. Leve si Supabase ne
    repond pas (l'appelant decide : il ne vise jamais a l'aveugle)."""
    import json
    import urllib.parse
    import urllib.request
    sys.path.insert(0, str(ROOT / "phase2" / "sync"))
    from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: E402
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
    filtre = urllib.parse.quote(f"(app_identite.eq.{numero},hektor_contact_id.eq.{numero})", safe="(),.")
    adresse = (f"{url.rstrip('/')}/rest/v1/{VUE_CORRESPONDANCE}"
               f"?select=app_identite,hektor_contact_id&or={filtre}&limit=2")
    requete = urllib.request.Request(adresse, headers={
        "apikey": cle, "Authorization": f"Bearer {cle}", "Accept": "application/json"})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        lignes = json.loads(reponse.read().decode("utf-8"))
    if not isinstance(lignes, list) or not lignes:
        return None
    if len(lignes) > 1:
        raise RuntimeError(f"{len(lignes)} paires pour le numero {numero} : la correspondance est incoherente.")
    identite = str(lignes[0].get("app_identite") or "").strip()
    cible = str(lignes[0].get("hektor_contact_id") or "").strip()
    # La FORME, comme verifier_la_correspondance() de la descente de nuit.
    if not (identite.isdigit() and cible.isdigit()
            and int(identite) >= PLAGE_NUMEROS_APP and int(cible) < PLAGE_NUMEROS_APP):
        raise RuntimeError(f"paire de forme fausse pour {numero} : identite={identite!r} cible={cible!r}")
    return identite, cible


def ecrire_la_paire(identite: str, cible: str) -> None:
    """Une ligne dans la table que la descente de nuit remplit -- meme forme."""
    import sqlite3
    from datetime import datetime, timezone
    conn = sqlite3.connect(str(ROOT / "phase2" / "phase2.sqlite"), timeout=60)
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE_CORRESPONDANCE} (
                    hektor_contact_id TEXT PRIMARY KEY,
                    app_identite      TEXT NOT NULL,
                    vu_le             TEXT NOT NULL
                )""")
        conn.execute(
            f"INSERT OR REPLACE INTO {TABLE_CORRESPONDANCE} (hektor_contact_id, app_identite, vu_le) VALUES (?,?,?)",
            (cible, identite, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        conn.commit()
    finally:
        conn.close()


def resoudre_le_numero(numero: str) -> tuple[str, str | None]:
    """Rend (le numero a donner aux 4 etapes, message d'arret ou None).

    Paire connue en local -> le numero tel quel : le chemin d'avant, inchange.
    Sinon -> on apprend la paire et on rend l'IDENTITE (le build et le push la
    parlent ; cible_hektor() la traduira pour Hektor grace a la ligne apprise).
    """
    if paire_connue_en_local(numero):
        return numero, None
    try:
        paire = demander_la_paire_a_supabase(numero)
    except Exception as erreur:  # Supabase muet, ou reponse incoherente
        return numero, (f"paire de numeros introuvable pour {numero} ({type(erreur).__name__}: {erreur}). "
                        "On ne vise pas Hektor a l'aveugle.")
    if paire is None:
        if int(numero) >= PLAGE_NUMEROS_APP:
            return numero, (f"le contact {numero} est ne dans l'app et n'a pas encore de numero Hektor. "
                            "On n'envoie pas un numero de l'app a Hektor.")
        # Un numero de Hektor qu'aucun contact ne dans l'app ne vise : un contact
        # cree dans Hektor et pas encore connu du serveur. Le chemin d'avant.
        return numero, None
    identite, cible = paire
    ecrire_la_paire(identite, cible)
    print(f"[refresh-inproc] paire apprise : identite {identite} <-> numero Hektor {cible}", flush=True)
    return identite, None


def _cible_apprise(identite: str) -> str:
    """cible_hektor(), plus la table de correspondance (ou la paire vient d'etre ecrite)."""
    cible = cible_hektor(identite)
    if cible != identite or int(identite) < PLAGE_NUMEROS_APP:
        return cible
    import sqlite3
    conn = sqlite3.connect(str(ROOT / "phase2" / "phase2.sqlite"), timeout=30)
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        for sql in (f"SELECT hektor_contact_id FROM {TABLE_CORRESPONDANCE} WHERE app_identite = ? LIMIT 1",
                    "SELECT hektor_target_id FROM app_contact WHERE hektor_contact_id = ? LIMIT 1"):
            try:
                ligne = conn.execute(sql, (identite,)).fetchone()
            except sqlite3.OperationalError:
                continue
            if ligne and str(ligne[0] or "").strip():
                return str(ligne[0]).strip()
    finally:
        conn.close()
    return identite


def _steps(contact_id: str):
    """(libellé, chemin relatif depuis ROOT, argv) — flags IDENTIQUES au worker."""
    identite = str(contact_id or "").strip()
    pour_hektor = _cible_apprise(identite)
    # ⛔ Derniere barriere : jamais un numero de l'app chez Hektor.
    if pour_hektor.isdigit() and int(pour_hektor) >= PLAGE_NUMEROS_APP:
        raise RuntimeError(f"le contact {identite} n'a pas de numero Hektor connu : on ne l'interroge pas.")
    return [
        # ETAPES 1 et 2 : la langue de HEKTOR et de son miroir.
        ("detail", "phase2/sync/sync_contact_details.py", [
            "--skip-listing-refresh", "--contact-id", pour_hektor,
            "--batch-size", "1", "--limit", "0",
            "--request-delay-seconds", "0", "--batch-pause-seconds", "0",
            "--max-hard-errors", "1", "--max-consecutive-hard-errors", "1",
            "--no-normalize",
        ]),
        ("normalize", "normalize_source.py", ["--contact-id", pour_hektor]),
        # ETAPES 3 et 4 : NOTRE langue. (Le build accepte les deux, il traduit
        # dans les deux sens ; on lui donne l'identite, qui est la sienne.)
        ("build", "phase2/contacts/build_contacts_layer.py", [
            "--contact-id", identite, "--no-reports",
        ]),
        # --include-archived-searches (21/08/2026) : meme raison que dans le run de 03:00.
        # Sans elle, ouvrir une fiche contact suffirait a resupprimer ses recherches
        # archivees de Supabase, et a reorpheliner ce qui pointait dessus.
        ("push", "phase2/sync/push_contacts_to_supabase.py", [
            "--contact-id", identite,
            "--push-mode", "full", "--contacts-scope", "active_or_eligible",
            "--skip-stats", "--include-archived-searches",
        ]),
    ]


def _run_step(rel_path: str, argv: list[str]) -> int:
    """Exécute un script comme le ferait `python <rel_path> <argv>`, en process."""
    abs_path = str(ROOT / rel_path)
    script_dir = os.path.dirname(abs_path)
    old_argv, old_path = sys.argv, list(sys.path)
    sys.argv = [abs_path] + argv
    # Reproduit le contexte d'import de `python xxx.py` : dossier du script + ROOT.
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, script_dir)
    try:
        runpy.run_path(abs_path, run_name="__main__")
        return 0
    except SystemExit as exc:                # `raise SystemExit(main())` côté script
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 1
    finally:
        sys.argv, sys.path = old_argv, old_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-through contact en 1 process (n°8).")
    ap.add_argument("--contact-id", required=True)
    args = ap.parse_args()
    cid = str(args.contact_id).strip()
    if not cid.isdigit():
        print(f"[refresh-inproc] contact-id invalide: {cid!r}", file=sys.stderr)
        return 2

    # Chantier 8 / 8a (21/10/2026) : la paire d'un contact ne aujourd'hui.
    numero, arret = resoudre_le_numero(cid)
    if arret:
        print(f"[refresh-inproc] ARRET : {arret}", file=sys.stderr)
        return 3
    try:
        etapes = _steps(numero)
    except RuntimeError as erreur:
        print(f"[refresh-inproc] ARRET : {erreur}", file=sys.stderr)
        return 3

    t0 = time.time()
    for label, rel, argv in etapes:
        print(f"=== [refresh-inproc] ETAPE {label} ===", flush=True)
        st = time.time()
        rc = _run_step(rel, argv)
        print(f"=== [refresh-inproc] {label} fini en {round(time.time() - st, 1)}s (code {rc}) ===", flush=True)
        if rc != 0:
            print(f"[refresh-inproc] ARRET : etape {label} en echec (code {rc})", file=sys.stderr)
            return rc or 1
    print(f"[refresh-inproc] OK contact {cid} en {round(time.time() - t0, 1)}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
