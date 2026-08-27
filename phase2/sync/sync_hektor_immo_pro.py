"""Sync du bloc COMMERCIAL des annonces immobilier professionnel -> miroir local.

POURQUOI CE SCRIPT EXISTE.
--------------------------
L'API REST de Hektor ne rend, pour une annonce d'immobilier professionnel, que huit
valeurs : offredem, idtype, trois champs de DPE, copropriete, nb de lots, NO_DOSSIER.
Mesure du 27/08/2026 sur l'annonce 62588, un ensemble immobilier a 5 125 000 EUR.

Elle ne rend NI le sous-type reel (murs commerciaux, fonds de commerce, entrepot...),
NI le bail, NI le loyer, NI la taxe fonciere, NI le chiffre d'affaires. `idtype` vaut
23 -- "Commerce" -- pour les 251 annonces actives, sans exception : le sous-type choisi
a la creation (champ `typeTransacWizard`) n'est jamais restitue.

Verifie par experience, pas par lecture : une annonce a ete creee le 27/08 avec
typeTransacWizard = 5 (Murs commerciaux). L'API la rend en idtype 23, et les mots
"murs" et "commerciaux" sont ABSENTS de toute sa reponse.

MAIS LA CONSOLE, ELLE, SAIT TOUT -- et par GraphQL, pas par du HTML a gratter.
La page /immo-pro/biens-actuels appelle `commercialProperties` avec un fragment
`commercial` complet : sous-type ET SA FAMILLE, activite, loyer de base, charges,
taxe fonciere, duree et echeance du bail, droit d'entree, CA et EBE sur trois
exercices (l'obligation legale d'affichage), lineaire de vitrine, hauteur sous
plafond, quai de chargement, acces PMR, divisibilite.

CE QU'IL NE FAIT PAS.
---------------------
Aucune ecriture chez Hektor. Aucune ecriture Supabase. Il ecrit UNIQUEMENT dans le
miroir local, dans sa propre table -- comme le chauffage.

POURQUOI DANS LE MIROIR ET PAS DANS app_annonce_champ_app.
-----------------------------------------------------------
Parce que c'est une donnee de HEKTOR. Le magasin `app_annonce_champ_app` porte ce que
l'APP detient et que Hektor ignore ; y mettre du Hektor brouillerait la seule
distinction qui comptera le jour de la coupure.

MODELE : identique a sync_hektor_drafts.py (meme transport, meme session, meme
discipline delta/backstop) et a sync_hektor_chauffages.py (meme table de tracabilite :
status, source_hash, error, elapsed_ms -- pour savoir POURQUOI une annonce manque).

Usage:
  python phase2/sync/sync_hektor_immo_pro.py [--full] [--backstop-days 7]
         [--archived] [--session <storage_state.json>] [--max-pages N] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
DEFAULT_SESSION = ROOT / "Console" / "sessions" / "storage_state_sync_light.json"
HEKTOR_BASE_URL = "https://groupe-gti-immobilier.la-boite-immo.com"
GRAPHQL_URL = f"{HEKTOR_BASE_URL}/ws/GraphQL_Web"

# Releve dans la console le 27/08/2026 (session Chrome, page /immo-pro/biens-actuels).
# On ne demande QUE ce dont on a besoin : l'identite, le watermark, et le bloc commercial.
# Le fragment complet de la console tire aussi tout PropertyListing -- inutile ici, le run
# quotidien a deja ces champs par l'API REST.
COMMERCIAL_LISTING_QUERY = (
    "query CommercialPropertyListing($filters: CommercialPropertySearchInput!){"
    "listing:commercialProperties(filters:$filters){"
    "metadata{total perPage currentPage nextPage} "
    "properties:nodes{id status createdAt datemaj "
    "commercial{id roomCount exteriorParkingCount interiorParkingCount "
    "leaseDuration leaseExpirationDate storefrontWidth ceilingHeight insulation "
    "annualRevenue1 fiscalYear1 annualRevenue2 fiscalYear2 annualRevenue3 fiscalYear3 "
    "ebe1 ebe1Year ebe2 ebe2Year ebe3 ebe3Year "
    "propertyTax condition zoneType legalStatus charges baseLeaseAmount "
    "hasWheelchairAccess storefront hasEntryFees hasDock hasCladdedDock "
    "hasWaterConnection hasDivisibleLand "
    "type{id label familyId} "
    "activities{id isMain activity{id label}}}}}}"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_session(path: Path) -> tuple[str, str | None]:
    """Cookies + jeton depuis un storage_state Playwright. Copie de sync_hektor_drafts."""
    state = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).timestamp()
    cookies = "; ".join(
        f"{c['name']}={c['value']}"
        for c in state.get("cookies", [])
        if not c.get("expires") or c["expires"] < 0 or c["expires"] > now
    )
    token = None
    for origin in state.get("origins", []):
        if origin.get("origin") == HEKTOR_BASE_URL:
            for item in origin.get("localStorage", []):
                if item.get("name") == "token" and item.get("value"):
                    raw = str(item["value"])
                    token = raw if raw.startswith("Bearer ") else f"Bearer {raw}"
    return cookies, token


def graphql_page(
    session: requests.Session,
    cookies: str,
    token: str | None,
    page: int,
    archived: bool,
    limit: int,
    recul_ms: int = 15000,
    essais: int = 3,
) -> tuple[dict, int]:
    """Une page. AVEC LE FREIN DE DEBIT DU PROJET.

    LE RYTHME N'EST PAS UNE PRECAUTION DECORATIVE. Notre IP a ete bannie deux fois --
    le 26/08 (plusieurs centaines de sondes d'audit, dont un echantillon a 0,25 s, soit
    quatre fois le plancher du projet) et Hektor rendait encore des 503 le 27/08 en fin
    d'apres-midi. Le worker porte depuis le 23/08 un frein explicite :

        1 000 ms minimum entre deux appels
        15 000 ms de recul apres un refus
        60 s de pause toutes les 100 requetes

    On applique le meme, adapte : ici UNE requete rapporte 50 annonces (contre une
    requete par annonce pour le chauffage ou console_missing_fields), donc le parc
    entier tient en une vingtaine d'appels. Le recul apres refus reste indispensable :
    c'est lui qui evite de transformer un 503 passager en bannissement.
    """
    headers = {
        "Cookie": cookies,
        "Referer": f"{HEKTOR_BASE_URL}/admin/",
        "Origin": HEKTOR_BASE_URL,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = token
    payload = {
        "operationName": "CommercialPropertyListing",
        "query": COMMERCIAL_LISTING_QUERY,
        "variables": {
            "filters": {
                "limit": limit,
                # COMMERCIAL_SALE = la vente immobilier professionnel (offredem 10).
                # La LOCATION pro (11) est volontairement exclue : decision du 27/08,
                # elle reste au serveur et n'apparait pas dans l'app.
                "offers": ["COMMERCIAL_SALE"],
                "status": "ALL",
                "page": page,
                "order": "LATEST",
                "sources": ["local"],
                "archived": archived,
            }
        },
    }
    derniere_erreur: Exception | None = None
    for tentative in range(1, essais + 1):
        debut = time.monotonic()
        try:
            resp = session.post(GRAPHQL_URL, json=payload, headers=headers, timeout=60)
            elapsed = int((time.monotonic() - debut) * 1000)
            # 403 = refus d'acces : on NE REESSAIE PAS. C'est la signature du
            # bannissement, et insister est exactement ce qui l'a aggrave le 26/08.
            if resp.status_code == 403:
                raise RuntimeError(
                    "403 Hektor -- acces refuse. ARRET IMMEDIAT : ne pas reessayer, "
                    "verifier depuis une autre IP avant de conclure a une panne."
                )
            resp.raise_for_status()
            body = resp.json()
            if body.get("errors"):
                raise RuntimeError(f"GraphQL Hektor: {body['errors']}")
            return body["data"]["listing"], elapsed
        except RuntimeError as err:
            if "403" in str(err):
                raise
            derniere_erreur = err
        except Exception as err:  # 503, coupure reseau, timeout
            derniere_erreur = err
        if tentative < essais:
            attente = recul_ms * tentative / 1000.0
            print(
                f"   page {page} : echec ({str(derniere_erreur)[:70]}) "
                f"-- recul de {attente:.0f} s avant la tentative {tentative + 1}/{essais}",
                file=sys.stderr,
            )
            time.sleep(attente)
    raise RuntimeError(f"page {page} : {essais} tentatives echouees -- {derniere_erreur}")


def ensure_schema(con: sqlite3.Connection) -> None:
    """La table, calquee sur hektor_annonce_chauffage_detail.

    Les colonnes de tracabilite (status, source_hash, error, elapsed_ms) ne sont pas
    du decor : c'est ce qui permet de savoir POURQUOI une annonce manque, au lieu de
    constater un trou. C'est exactement ce qui a manque au moniteur le 27/08.
    """
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS hektor_annonce_commercial (
          hektor_annonce_id        TEXT PRIMARY KEY,

          -- identite du bloc
          sous_type_id             TEXT,
          sous_type_label          TEXT,
          famille_id               TEXT,
          activite_principale_id   TEXT,
          activite_principale_label TEXT,
          activites_json           TEXT,

          -- exploitation
          loyer_base               TEXT,
          charges                  TEXT,
          taxe_fonciere            TEXT,
          droit_entree             INTEGER,
          bail_duree               TEXT,
          bail_echeance            TEXT,
          statut_juridique         TEXT,
          type_zone                TEXT,
          etat                     TEXT,

          -- les comptes (obligation legale d'affichage pour une cession de fonds)
          ca1 TEXT, exercice1 TEXT,
          ca2 TEXT, exercice2 TEXT,
          ca3 TEXT, exercice3 TEXT,
          ebe1 TEXT, annee_ebe1 TEXT,
          ebe2 TEXT, annee_ebe2 TEXT,
          ebe3 TEXT, annee_ebe3 TEXT,

          -- le local
          vitrine                  INTEGER,
          vitrine_lineaire         TEXT,
          hauteur_plafond          TEXT,
          isolation                TEXT,
          quai                     INTEGER,
          quai_couvert             INTEGER,
          pmr                      INTEGER,
          divisible                INTEGER,
          eau                      INTEGER,
          nb_pieces                TEXT,
          parkings_ext             TEXT,
          parkings_int             TEXT,

          -- le brut : on ne perd JAMAIS ce que Hektor a dit
          commercial_json          TEXT,

          -- tracabilite
          status                   TEXT,
          datemaj_hektor           TEXT,
          created_at_hektor        TEXT,
          archived                 INTEGER,
          source                   TEXT,
          source_hash              TEXT,
          elapsed_ms               INTEGER,
          error                    TEXT,
          synced_at                TEXT
        )
        """
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_hektor_annonce_commercial_soustype "
        "ON hektor_annonce_commercial(sous_type_id)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS hektor_commercial_sweep_meta (key TEXT PRIMARY KEY, value TEXT)"
    )


def get_meta(con: sqlite3.Connection, key: str) -> str | None:
    row = con.execute("SELECT value FROM hektor_commercial_sweep_meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def set_meta(con: sqlite3.Connection, key: str, value: str | None) -> None:
    con.execute(
        "INSERT INTO hektor_commercial_sweep_meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def _bool(value: object) -> int | None:
    if value is None:
        return None
    return 1 if value is True else 0


#: Les sentinelles de "vide" de Hektor. Le projet a deja sa regle -- "0 vaut vide"
#: (memoire dpe-0-vaut-vide-fiche-hektor) et les dates MySQL nulles '0000-00-00'
#: reconnues par le magasin des champs app. GraphQL en ajoute une troisieme, vue le
#: 27/08 sur bail_echeance : '-0001-11-30T00:00:00', l'an -1. Sans ce filtre, une
#: annonce sans bail afficherait une echeance en l'an -1, et pire : le magasin des
#: doublures la compterait comme une divergence a chaque comparaison.
SENTINELLES_VIDE = {
    "0000-00-00", "0000-00-00 00:00:00", "0000-00-00T00:00:00",
    "-0001-11-30", "-0001-11-30T00:00:00", "-0001-11-30 00:00:00",
}


def _txt(value: object) -> str | None:
    if value is None:
        return None
    texte = str(value).strip()
    if not texte:
        return None
    if texte in SENTINELLES_VIDE or texte.startswith("-0001-11-30"):
        return None
    return texte


def upsert_commercial(
    con: sqlite3.Connection, prop: dict, archived: bool, source: str, elapsed: int
) -> str:
    """Ecrit une annonce. Rend 'ecrit', 'inchange' ou 'sans_bloc'."""
    annonce_id = str(prop.get("id") or "").strip()
    if not annonce_id:
        return "sans_id"
    bloc = prop.get("commercial")
    if not isinstance(bloc, dict):
        # Une annonce immo pro sans bloc commercial : on la trace quand meme, sinon
        # on ne saurait pas la distinguer d'une annonce jamais lue.
        con.execute(
            "INSERT INTO hektor_annonce_commercial(hektor_annonce_id, status, datemaj_hektor, "
            "created_at_hektor, archived, source, elapsed_ms, error, synced_at) "
            "VALUES(?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(hektor_annonce_id) DO UPDATE SET "
            "  status = excluded.status, datemaj_hektor = excluded.datemaj_hektor, "
            "  source = excluded.source, error = excluded.error, synced_at = excluded.synced_at",
            (annonce_id, prop.get("status"), prop.get("datemaj"), prop.get("createdAt"),
             1 if archived else 0, source, elapsed, "bloc commercial absent", now_iso()),
        )
        return "sans_bloc"

    brut = json.dumps(bloc, ensure_ascii=False, sort_keys=True)
    empreinte = str(abs(hash(brut)))

    ancien = con.execute(
        "SELECT source_hash FROM hektor_annonce_commercial WHERE hektor_annonce_id = ?",
        (annonce_id,),
    ).fetchone()
    if ancien and ancien[0] == empreinte:
        con.execute(
            "UPDATE hektor_annonce_commercial SET synced_at = ?, source = ? WHERE hektor_annonce_id = ?",
            (now_iso(), source, annonce_id),
        )
        return "inchange"

    type_bloc = bloc.get("type") or {}
    activites = bloc.get("activities") or []
    principale = next((a for a in activites if a.get("isMain")), activites[0] if activites else {})
    act = (principale or {}).get("activity") or {}

    con.execute(
        """
        INSERT INTO hektor_annonce_commercial(
          hektor_annonce_id,
          sous_type_id, sous_type_label, famille_id,
          activite_principale_id, activite_principale_label, activites_json,
          loyer_base, charges, taxe_fonciere, droit_entree,
          bail_duree, bail_echeance, statut_juridique, type_zone, etat,
          ca1, exercice1, ca2, exercice2, ca3, exercice3,
          ebe1, annee_ebe1, ebe2, annee_ebe2, ebe3, annee_ebe3,
          vitrine, vitrine_lineaire, hauteur_plafond, isolation,
          quai, quai_couvert, pmr, divisible, eau,
          nb_pieces, parkings_ext, parkings_int,
          commercial_json,
          status, datemaj_hektor, created_at_hektor, archived,
          source, source_hash, elapsed_ms, error, synced_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(hektor_annonce_id) DO UPDATE SET
          sous_type_id = excluded.sous_type_id,
          sous_type_label = excluded.sous_type_label,
          famille_id = excluded.famille_id,
          activite_principale_id = excluded.activite_principale_id,
          activite_principale_label = excluded.activite_principale_label,
          activites_json = excluded.activites_json,
          loyer_base = excluded.loyer_base, charges = excluded.charges,
          taxe_fonciere = excluded.taxe_fonciere, droit_entree = excluded.droit_entree,
          bail_duree = excluded.bail_duree, bail_echeance = excluded.bail_echeance,
          statut_juridique = excluded.statut_juridique, type_zone = excluded.type_zone,
          etat = excluded.etat,
          ca1 = excluded.ca1, exercice1 = excluded.exercice1,
          ca2 = excluded.ca2, exercice2 = excluded.exercice2,
          ca3 = excluded.ca3, exercice3 = excluded.exercice3,
          ebe1 = excluded.ebe1, annee_ebe1 = excluded.annee_ebe1,
          ebe2 = excluded.ebe2, annee_ebe2 = excluded.annee_ebe2,
          ebe3 = excluded.ebe3, annee_ebe3 = excluded.annee_ebe3,
          vitrine = excluded.vitrine, vitrine_lineaire = excluded.vitrine_lineaire,
          hauteur_plafond = excluded.hauteur_plafond, isolation = excluded.isolation,
          quai = excluded.quai, quai_couvert = excluded.quai_couvert,
          pmr = excluded.pmr, divisible = excluded.divisible, eau = excluded.eau,
          nb_pieces = excluded.nb_pieces,
          parkings_ext = excluded.parkings_ext, parkings_int = excluded.parkings_int,
          commercial_json = excluded.commercial_json,
          status = excluded.status, datemaj_hektor = excluded.datemaj_hektor,
          created_at_hektor = excluded.created_at_hektor, archived = excluded.archived,
          source = excluded.source, source_hash = excluded.source_hash,
          elapsed_ms = excluded.elapsed_ms, error = NULL, synced_at = excluded.synced_at
        """,
        (
            annonce_id,
            _txt(type_bloc.get("id")), _txt(type_bloc.get("label")), _txt(type_bloc.get("familyId")),
            _txt(act.get("id")), _txt(act.get("label")),
            json.dumps(activites, ensure_ascii=False) if activites else None,
            _txt(bloc.get("baseLeaseAmount")), _txt(bloc.get("charges")),
            _txt(bloc.get("propertyTax")), _bool(bloc.get("hasEntryFees")),
            _txt(bloc.get("leaseDuration")), _txt(bloc.get("leaseExpirationDate")),
            _txt(bloc.get("legalStatus")), _txt(bloc.get("zoneType")), _txt(bloc.get("condition")),
            _txt(bloc.get("annualRevenue1")), _txt(bloc.get("fiscalYear1")),
            _txt(bloc.get("annualRevenue2")), _txt(bloc.get("fiscalYear2")),
            _txt(bloc.get("annualRevenue3")), _txt(bloc.get("fiscalYear3")),
            _txt(bloc.get("ebe1")), _txt(bloc.get("ebe1Year")),
            _txt(bloc.get("ebe2")), _txt(bloc.get("ebe2Year")),
            _txt(bloc.get("ebe3")), _txt(bloc.get("ebe3Year")),
            _bool(bloc.get("storefront")), _txt(bloc.get("storefrontWidth")),
            _txt(bloc.get("ceilingHeight")), _txt(bloc.get("insulation")),
            _bool(bloc.get("hasDock")), _bool(bloc.get("hasCladdedDock")),
            _bool(bloc.get("hasWheelchairAccess")), _bool(bloc.get("hasDivisibleLand")),
            _bool(bloc.get("hasWaterConnection")),
            _txt(bloc.get("roomCount")),
            _txt(bloc.get("exteriorParkingCount")), _txt(bloc.get("interiorParkingCount")),
            brut,
            prop.get("status"), prop.get("datemaj"), prop.get("createdAt"),
            1 if archived else 0,
            source, empreinte, elapsed, None, now_iso(),
        ),
    )
    return "ecrit"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--session", type=Path, default=DEFAULT_SESSION)
    ap.add_argument("--full", action="store_true", help="balayage complet, sans watermark")
    ap.add_argument("--archived", action="store_true", help="lire les ARCHIVEES au lieu des actives")
    ap.add_argument("--backstop-days", type=int, default=7)
    ap.add_argument("--limit", type=int, default=50, help="annonces par page")
    ap.add_argument("--max-pages", type=int, default=0, help="0 = pas de limite")
    # LE RYTHME DU PROJET, pas des valeurs choisies au hasard :
    #   1 s minimum entre deux appels        (CONSOLE_HEKTOR_MIN_REQUEST_INTERVAL_MS)
    #   15 s de recul apres un refus         (CONSOLE_HEKTOR_BACKOFF_AFTER_REJECT_MS)
    #   60 s de pause longue, periodique     (CONSOLE_HEKTOR_LONG_PAUSE_MS)
    # On prend 2 s entre les pages plutot que 1 : Hektor rendait encore des 503 le
    # 27/08 au soir, et une page nous rapporte 50 annonces -- le parc entier tient
    # en une vingtaine d'appels, donc la prudence ne coute presque rien.
    ap.add_argument("--pause-seconds", type=float, default=2.0, help="entre deux pages (plancher projet : 1)")
    ap.add_argument("--backoff-seconds", type=float, default=15.0, help="recul apres un refus")
    ap.add_argument("--pause-every", type=int, default=50, help="pause longue toutes les N pages")
    ap.add_argument("--long-pause-seconds", type=float, default=60.0, help="duree de la pause longue")
    ap.add_argument("--dry-run", action="store_true", help="n'ecrit rien")
    return ap.parse_args()


def should_full(con: sqlite3.Connection, args: argparse.Namespace, cle_full: str) -> bool:
    if args.full:
        return True
    if not con.execute("SELECT 1 FROM hektor_annonce_commercial LIMIT 1").fetchone():
        return True
    dernier = get_meta(con, cle_full)
    if not dernier:
        return True
    try:
        quand = datetime.fromisoformat(dernier.replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(timezone.utc) - quand > timedelta(days=args.backstop_days)


def main() -> int:
    args = parse_args()
    if not args.session.exists():
        print(f"Session introuvable: {args.session}", file=sys.stderr)
        return 2
    cookies, token = load_session(args.session)
    if not cookies:
        print("Session sans cookies valides -- relancer playwright_login.js", file=sys.stderr)
        return 2

    portee = "archivees" if args.archived else "actives"
    cle_wm = f"watermark_datemaj_{portee}"
    cle_full = f"dernier_full_{portee}"

    con = sqlite3.connect(HEKTOR_DB, timeout=60)
    ensure_schema(con)
    complet = should_full(con, args, cle_full)
    watermark = get_meta(con, cle_wm) or ""
    mode = "full" if complet else "delta"
    print(f"Portee: {portee} | mode: {mode} | watermark={watermark or '(aucun)'}")

    session = requests.Session()
    compteurs = {"lues": 0, "ecrites": 0, "inchangees": 0, "sans_bloc": 0}
    nouveau_wm = watermark
    page, pages = 1, 0
    total_annonce = None

    try:
        while True:
            listing, elapsed = graphql_page(
                session, cookies, token, page, args.archived, args.limit,
                recul_ms=int(args.backoff_seconds * 1000),
            )
            meta = listing.get("metadata") or {}
            if total_annonce is None:
                total_annonce = meta.get("total")
                print(f"Hektor annonce {total_annonce} annonce(s) en {portee}")
            props = listing.get("properties") or []
            if not props:
                break
            page_utile = complet
            for prop in props:
                compteurs["lues"] += 1
                datemaj = str(prop.get("datemaj") or "")
                if datemaj > nouveau_wm:
                    nouveau_wm = datemaj
                if not complet and watermark and datemaj <= watermark:
                    continue
                page_utile = True
                if args.dry_run:
                    continue
                verdict = upsert_commercial(con, prop, args.archived, mode, elapsed)
                if verdict == "ecrit":
                    compteurs["ecrites"] += 1
                elif verdict == "inchange":
                    compteurs["inchangees"] += 1
                elif verdict == "sans_bloc":
                    compteurs["sans_bloc"] += 1
            if not args.dry_run:
                con.commit()
            pages += 1
            # En delta, la liste est triee LATEST : une page entierement sous le
            # watermark signifie qu'on a rattrape le connu -> on s'arrete.
            if not complet and not page_utile:
                print(f"Page {page} entierement sous le watermark -- arret.")
                break
            suivante = meta.get("nextPage")
            if suivante in (None, "", 0, "0"):
                break
            if args.max_pages and pages >= args.max_pages:
                print(f"Limite de {args.max_pages} page(s) atteinte.")
                break
            page = int(suivante)
            if args.pause_every and pages % args.pause_every == 0:
                print(f"   pause longue de {args.long_pause_seconds:.0f} s apres {pages} pages")
                time.sleep(args.long_pause_seconds)
            else:
                time.sleep(args.pause_seconds)
    finally:
        if not args.dry_run:
            if nouveau_wm:
                set_meta(con, cle_wm, nouveau_wm)
            if complet:
                set_meta(con, cle_full, now_iso())
            con.commit()
        con.close()

    print(
        f"{portee}: {pages} page(s), {compteurs['lues']} lue(s), "
        f"{compteurs['ecrites']} ecrite(s), {compteurs['inchangees']} inchangee(s), "
        f"{compteurs['sans_bloc']} sans bloc commercial"
    )
    if args.dry_run:
        print("(dry-run : rien n'a ete ecrit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
