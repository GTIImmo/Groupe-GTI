"""Lire ce que Google autorise VRAIMENT a notre cle de service.

Pourquoi cet outil (13/10/2026) : `/google-workspace/status` du backend affiche la
variable GOOGLE_WORKSPACE_SCOPES, c'est-a-dire ce que NOUS avons ecrit dans le .env.
Il ne dit RIEN de ce que Google accepte. La seule source de verite est Google :
on lui DEMANDE un jeton, scope par scope, et on regarde s'il le donne.

Trois murs independants, trois messages differents -- ne pas les confondre :
  1. DELEGATION   console d'admin Workspace -> Commandes des API -> delegation
                  au niveau du domaine. Echec = `unauthorized_client` des la
                  demande de jeton (aucun appel d'API n'a encore eu lieu).
  2. API ACTIVEE  console Google Cloud, projet hektor-492708. Echec = HTTP 403
                  avec `SERVICE_DISABLED` / "has not been used in project".
  3. PARTAGE      le fichier lui-meme, partage avec le compte emprunte. Echec =
                  HTTP 404 (fichier invisible) ou 403 PERMISSION_DENIED.

LECTURE SEULE : ce script n'ecrit nulle part, ni chez Google ni chez nous.

    .venv\\Scripts\\python.exe monitoring\\check_google_scopes.py
    .venv\\Scripts\\python.exe monitoring\\check_google_scopes.py --sheet IDENTIFIANT

/!\\ Le python du venv, pas celui du systeme : google-auth n'est que dans le venv.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# (!!) LA CONSOLE WINDOWS EST EN CP1252 : un simple print d un en-tete
#   accentue (" Negociateur ", " Signe ") faisait TOMBER l outil APRES avoir
#   fait tout son travail -- la sonde disait vrai puis mourait a l affichage.
#   Corrige le 16/10/2026. errors=replace : on prefere un caractere de
#   remplacement a une pile d appels.
for _flux in (sys.stdout, sys.stderr):
    try:
        _flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE = Path(__file__).resolve().parents[1]

# Les scopes qu'on interroge par defaut : ceux qu'on utilise deja, et ceux
# qu'on envisage. Un scope absent d'ici s'ajoute avec --scope.
SCOPES_SONDES = (
    ("gmail.send", "https://www.googleapis.com/auth/gmail.send"),
    ("gmail.readonly", "https://www.googleapis.com/auth/gmail.readonly"),
    ("calendar.freebusy", "https://www.googleapis.com/auth/calendar.freebusy"),
    ("calendar.events", "https://www.googleapis.com/auth/calendar.events"),
    ("spreadsheets", "https://www.googleapis.com/auth/spreadsheets"),
    ("spreadsheets.readonly", "https://www.googleapis.com/auth/spreadsheets.readonly"),
    ("drive", "https://www.googleapis.com/auth/drive"),
    ("drive.file", "https://www.googleapis.com/auth/drive.file"),
    ("drive.readonly", "https://www.googleapis.com/auth/drive.readonly"),
)


def load_env_file(path: Path) -> None:
    """Meme chargeur que check_gti_health.py : l'environnement reel gagne."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


def jeton(service_account_file: str, subject: str, scope: str) -> tuple[bool, str]:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    try:
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=[scope]
        ).with_subject(subject)
        creds.refresh(Request())
    except Exception as exc:  # noqa: BLE001 -- on veut le message brut de Google
        texte = str(exc)
        if "unauthorized_client" in texte:
            return False, "MUR 1 : scope absent de la delegation"
        if "invalid_grant" in texte:
            return False, "compte emprunte inconnu ou suspendu (invalid_grant)"
        return False, texte[:160]
    return True, creds.token or ""


def lire_classeur(token: str, sheet_id: str, plage: str) -> None:
    import requests

    base = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
    reponse = requests.get(
        base,
        params={"fields": "properties.title,sheets.properties(title,gridProperties)"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if reponse.status_code != 200:
        corps = reponse.text[:400]
        if "SERVICE_DISABLED" in corps or "has not been used in project" in corps:
            mur = "MUR 2 : l'API Sheets n'est pas activee dans le projet Google Cloud"
        elif reponse.status_code in (403, 404):
            mur = "MUR 3 : le classeur n'est pas partage avec le compte emprunte"
        else:
            mur = "reponse inattendue"
        print(f"  classeur    : ECHEC {reponse.status_code} -- {mur}")
        print(f"                {corps}")
        return

    info = reponse.json()
    titre = info.get("properties", {}).get("title")
    print(f'  classeur    : "{titre}"')
    for onglet in info.get("sheets", []):
        proprietes = onglet.get("properties", {})
        grille = proprietes.get("gridProperties", {})
        print(
            f'   - onglet "{proprietes.get("title")}" : '
            f'{grille.get("rowCount")} lignes x {grille.get("columnCount")} colonnes'
        )

    valeurs = requests.get(
        f"{base}/values/{plage}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if valeurs.status_code != 200:
        print(f"  valeurs     : ECHEC {valeurs.status_code} -- {valeurs.text[:300]}")
        return
    lignes = valeurs.json().get("values", [])
    print(f"  valeurs     : {len(lignes)} ligne(s) lue(s) sur {plage}")
    for rang, ligne in enumerate(lignes, start=1):
        print(f"   L{rang} | " + " | ".join(str(cellule) for cellule in ligne))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lire les scopes Google reellement autorises (lecture seule)"
    )
    parser.add_argument("--subject", default=None, help="compte emprunte (defaut : GOOGLE_WORKSPACE_SUBJECT_EMAIL)")
    parser.add_argument("--scope", action="append", default=[], help="scope supplementaire a sonder (repetable)")
    parser.add_argument("--sheet", default=None, help="identifiant d'un classeur a lire si un scope Sheets passe")
    parser.add_argument("--plage", default="A1:AZ3", help="plage lue avec --sheet (defaut A1:AZ3)")
    args = parser.parse_args()

    load_env_file(RACINE / ".env")
    service_account_file = os.getenv("GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE", "").strip()
    subject = (args.subject or os.getenv("GOOGLE_WORKSPACE_SUBJECT_EMAIL", "")).strip()
    declares = [s.strip() for s in os.getenv("GOOGLE_WORKSPACE_SCOPES", "").split(",") if s.strip()]

    if not service_account_file or not Path(service_account_file).exists():
        print(f"ARRET : cle de service introuvable ({service_account_file or 'non configuree'})")
        return 2
    if not subject:
        print("ARRET : aucun compte a emprunter (GOOGLE_WORKSPACE_SUBJECT_EMAIL)")
        return 2

    print(f"cle de service : {service_account_file}")
    print(f"compte emprunte: {subject}")
    print(f"declares (.env): {len(declares)} scope(s)")
    print()

    sondes = list(SCOPES_SONDES) + [(s, s) for s in args.scope]
    autorises: dict[str, str] = {}
    for nom, scope in sondes:
        ok, detail = jeton(service_account_file, subject, scope)
        marque = "OK    " if ok else "REFUSE"
        ecart = ""
        if ok and scope not in declares:
            ecart = "   (autorise par Google mais ABSENT du .env)"
        if not ok and scope in declares:
            ecart = "   (declare dans le .env mais REFUSE par Google)"
        suffixe = "" if ok else "-- " + detail
        print(f"  {marque}  {nom:<24} {suffixe}{ecart}")
        if ok:
            autorises[scope] = detail

    if args.sheet:
        print()
        token = (
            autorises.get("https://www.googleapis.com/auth/spreadsheets")
            or autorises.get("https://www.googleapis.com/auth/spreadsheets.readonly")
        )
        if not token:
            print("  classeur    : non lu -- MUR 1, aucun scope Sheets autorise")
        else:
            lire_classeur(token, args.sheet, args.plage)

    return 0 if autorises else 1


if __name__ == "__main__":
    sys.exit(main())
