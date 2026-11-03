#!/usr/bin/env python3
"""LA LISTE ENTIERE DES CONTACTS, LA NUIT -- PASSAGE A BLANC (03/11/2026).

Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §40 a §45.

LE DEFAUT. La nuit ne voit un contact modifie dans Hektor que s'il remonte en tete
de `ListContacts` triee par « date de dernier traitement ». Un rattachement de
couple (EA32621, 02/11) change la `datemaj` du contact mais PAS cette date : la
fiche n'est jamais relue. Hektor n'offre ni tri ni filtre par `datemaj` (essai du
03/11) : la seule facon de connaitre la date de chaque fiche est de lire TOUTE la
liste (tri par numero, ~8 500 pages actives, ~9 000 archivees).

CE QUE FAIT CE SCRIPT, A BLANC (le seul mode ecrit) :
  1. lit la liste par l'API seule (`/Api/Contact/ListContacts/`, sort=id ASC), page
     apres page, a la vitesse donnee (--intervalle-ms, pour CE processus seulement),
     avec une pause reguliere, une heure limite, et un arret net au premier refus ;
  2. garde SON carnet (`liste_nuit_contact`) et SON tour (`liste_nuit_tour`), et
     range ses pages sous un nom a part (`nuit_liste_contacts_<scope>`) ;
  3. dresse le RAPPORT : fiches a relire (date Hektor plus recente que notre
     derniere relecture), annonces liees, et ecarts avec notre miroir
     (negociateur, lien de couple, etat archive, fiches absentes).

⛔ CE QU'IL NE TOUCHE PAS -- c'est tout l'objet du passage a blanc :
  · `sync_contact_state` et le curseur `contact_cursor_*` : c'est le carnet du run
    de 04:00, son signal pour relire les annonces des contacts changes
    (sync_raw.py l. 1755-1759) ; l'ecrire ici viderait ce signal ;
  · les pages `list_contacts_*` : `normalize_source` les relit chaque nuit
    (CONTACT_ENDPOINTS) ; y ecrire changerait le miroir. Le faire est le BUT
    (reparer les pages de mars), mais seulement apres lecture du rapport ;
  · aucune fiche n'est relue, rien ne part chez Supabase.

LA REPRISE se fait par NUMERO, pas par page : la page N n'est pas stable (44 445
contacts sortis des actifs entre mars et mai, la page 8430 de mars est devenue la
~6207). Au redemarrage on relit la derniere page lue ; si elle commence APRES le
dernier numero lu, des contacts ont recule d'une page : on recule jusqu'a la
retrouver. Une creation arrive en fin de liste et ne decale rien.

Usage :
    python phase2/sync/liste_contacts_nuit.py --scope active --intervalle-ms 400 --heure-limite 01:55
    python phase2/sync/liste_contacts_nuit.py --scope active --rapport-seul      (aucun appel Hektor)
Sortie : 0 = tour termine ou heure limite atteinte proprement · 2 = mauvais usage ·
         3 = refus de Hektor (4xx) · 4 = Hektor ne repond pas (apres patience).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import (  # noqa: E402
    HektorClient,
    HektorNonRetryableError,
    Settings,
    connect_db,
    now_utc_iso,
    upsert_raw_response,
)

LISTE_PATH = "/Api/Contact/ListContacts/"
ARCHIVE_PAR_SCOPE = {"active": 0, "archived": 1}
RAPPORTS = ROOT / "logs" / "liste_contacts_nuit"
# Recul maximal pour retrouver le dernier numero lu (une page par pas). Au-dela,
# c'est un depart massif : on repart d'un tour neuf plutot que de marteler Hektor.
RECUL_MAX_PAGES = 60


def endpoint_nuit(scope: str) -> str:
    # ⚠ PAS « list_contacts_… » : normalize_source relit tout ce qui porte ce nom.
    return f"nuit_liste_contacts_{scope}"


def creer_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS liste_nuit_contact (
            hektor_contact_id TEXT PRIMARY KEY,
            scope TEXT NOT NULL,
            datemaj TEXT,
            ref_couple TEXT,
            id_negociateur TEXT,
            archive TEXT,
            vu_le TEXT NOT NULL,
            tour TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS liste_nuit_tour (
            scope TEXT PRIMARY KEY,
            tour TEXT NOT NULL,
            derniere_page INTEGER NOT NULL DEFAULT 0,
            dernier_id INTEGER NOT NULL DEFAULT 0,
            total INTEGER,
            pages_lues INTEGER NOT NULL DEFAULT 0,
            contacts_vus INTEGER NOT NULL DEFAULT 0,
            termine_le TEXT,
            maj TEXT NOT NULL
        );
        """
    )
    conn.commit()


def texte(valeur: Any) -> str:
    return str(valeur if valeur is not None else "").strip()


def numero(valeur: Any) -> Optional[str]:
    """Meme regle que normalize_source.normalized_id : vide, 0, null -> rien."""
    t = texte(valeur)
    return None if not t or t in {"0", "null", "None"} else t


class ClientListe(HektorClient):
    """Le client commun, avec UNE seule tentative de connexion.

    Le client commun reessaie sa connexion jusqu'a 4 fois, 403 et 429 compris : une
    rafale de connexions est le motif qui nous a fait bannir le 17/09. Ici une
    connexion refusee arrete tout -- la nuit suivante reprendra.
    """

    def authenticate(self) -> str:
        avant = self.max_retries
        self.max_retries = 1
        try:
            return super().authenticate()
        finally:
            self.max_retries = avant


class Lecteur:
    """Une page = une requete comptee ; le plancher de rythme est celui du client."""

    def __init__(self, client: Any, scope: str, version: str) -> None:
        self.client = client
        self.scope = scope
        self.version = version
        self.requetes = 0

    def page(self, numero_page: int) -> dict[str, Any]:
        params = {
            "archive": ARCHIVE_PAR_SCOPE[self.scope],
            "sort": "id",
            "way": "ASC",
            "page": numero_page,
            "version": self.version,
        }
        self.requetes += 1
        payload = self.client.get_json(LISTE_PATH, params=params)
        if not isinstance(payload, dict):
            raise RuntimeError(f"page {numero_page} : reponse inattendue ({type(payload).__name__})")
        payload["_params"] = params
        return payload


def lignes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") or []
    return [x for x in data if isinstance(x, dict) and texte(x.get("id")).isdigit()]


def heure_depassee(limite: Optional[str], maintenant: Optional[datetime] = None) -> bool:
    """`limite` = « HH:MM » en heure locale. Une limite avant midi vise la nuit qui
    suit un depart du soir (00:20 -> 01:55) : on ne la compare qu'apres minuit."""
    if not limite:
        return False
    h, m = (int(x) for x in limite.split(":"))
    now = maintenant or datetime.now()
    if h < 12 and now.hour >= 12:
        return False
    return (now.hour, now.minute) >= (h, m)


def lire_tour(conn: sqlite3.Connection, scope: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM liste_nuit_tour WHERE scope = ?", (scope,)).fetchone()


def ecrire_tour(conn: sqlite3.Connection, scope: str, **champs: Any) -> None:
    champs["maj"] = now_utc_iso()
    if lire_tour(conn, scope) is None:
        cols = ["scope", *champs]
        conn.execute(
            f"INSERT INTO liste_nuit_tour({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            [scope, *champs.values()],
        )
    else:
        conn.execute(
            f"UPDATE liste_nuit_tour SET {', '.join(f'{k} = ?' for k in champs)} WHERE scope = ?",
            [*champs.values(), scope],
        )
    conn.commit()


def garder_page(conn: sqlite3.Connection, scope: str, tour: str, numero_page: int,
                payload: dict[str, Any]) -> list[int]:
    vu_le = now_utc_iso()
    ids: list[int] = []
    for item in lignes(payload):
        ids.append(int(texte(item.get("id"))))
        conn.execute(
            """
            INSERT INTO liste_nuit_contact(hektor_contact_id, scope, datemaj, ref_couple,
                                           id_negociateur, archive, vu_le, tour)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_contact_id) DO UPDATE SET
                scope = excluded.scope, datemaj = excluded.datemaj,
                ref_couple = excluded.ref_couple, id_negociateur = excluded.id_negociateur,
                archive = excluded.archive, vu_le = excluded.vu_le, tour = excluded.tour
            """,
            (texte(item.get("id")), scope, texte(item.get("datemaj")) or None,
             texte(item.get("refCouple")) or None, texte(item.get("id_negociateur")) or None,
             texte(item.get("archive")) or None, vu_le, tour),
        )
    params = payload.pop("_params", None)
    upsert_raw_response(  # commit dedans
        conn, run_id=None, endpoint_name=endpoint_nuit(scope), object_type="contact_liste_nuit",
        object_id=None, page=numero_page, params=params, payload=payload, http_status=200,
    )
    return ids


def premier_id(payload: dict[str, Any]) -> Optional[int]:
    ids = [int(texte(x.get("id"))) for x in lignes(payload)]
    return min(ids) if ids else None


def lire_la_liste(conn: sqlite3.Connection, lecteur: Lecteur, *, scope: str, nouveau_tour: bool,
                  heure_limite: Optional[str], max_pages: int, pause_toutes: int,
                  pause_secondes: float, dormir=time.sleep) -> dict[str, Any]:
    """Le coeur. Ne leve que HektorNonRetryableError (refus) et RuntimeError (pas de
    reponse) ; dans les deux cas le tour garde sa derniere page sure."""
    tour_row = lire_tour(conn, scope)
    if nouveau_tour or tour_row is None or tour_row["termine_le"]:
        tour = now_utc_iso()
        ecrire_tour(conn, scope, tour=tour, derniere_page=0, dernier_id=0, total=None,
                    pages_lues=0, contacts_vus=0, termine_le=None)
        page, dernier_id = 1, 0
        print(f"[liste-nuit] {scope} : nouveau tour {tour}")
    else:
        tour = tour_row["tour"]
        page = max(1, int(tour_row["derniere_page"]))
        dernier_id = int(tour_row["dernier_id"])
        print(f"[liste-nuit] {scope} : reprise du tour {tour} a la page {page} (dernier numero lu {dernier_id})")

    bilan = {"scope": scope, "tour": tour, "pages": 0, "contacts": 0, "recul": 0,
             "fin": "", "inversions": 0}

    # LA REPRISE : retrouver le dernier numero lu (voir l'en-tete).
    payload: Optional[dict[str, Any]] = None
    if dernier_id > 0:
        while True:
            payload = lecteur.page(page)
            debut = premier_id(payload)
            if debut is None or debut <= dernier_id or page == 1:
                break
            if bilan["recul"] >= RECUL_MAX_PAGES:
                print(f"[liste-nuit] recul de {RECUL_MAX_PAGES} pages sans retrouver {dernier_id} :"
                      " depart massif -- le tour repartira de la page 1 la nuit prochaine")
                ecrire_tour(conn, scope, termine_le=now_utc_iso())
                bilan["fin"] = "recul_trop_long"
                return bilan
            page -= 1
            bilan["recul"] += 1
        if bilan["recul"]:
            print(f"[liste-nuit] {bilan['recul']} page(s) de recul pour retrouver le numero {dernier_id}")

    while True:
        if heure_depassee(heure_limite):
            bilan["fin"] = "heure_limite"
            break
        if max_pages and bilan["pages"] >= max_pages:
            bilan["fin"] = "max_pages"
            break
        if payload is None:
            payload = lecteur.page(page)
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        suivante = metadata.get("nextPage")
        total = metadata.get("total")
        ids = garder_page(conn, scope, tour, page, payload)
        payload = None
        if not ids:
            ecrire_tour(conn, scope, termine_le=now_utc_iso())
            bilan["fin"] = "tour_termine"
            break
        if ids != sorted(ids):
            bilan["inversions"] += 1
        bilan["pages"] += 1
        bilan["contacts"] += len(ids)
        tour_row = lire_tour(conn, scope)
        ecrire_tour(conn, scope, derniere_page=page, dernier_id=max(max(ids), dernier_id),
                    total=int(total) if str(total or "").isdigit() else tour_row["total"],
                    pages_lues=int(tour_row["pages_lues"]) + 1,
                    contacts_vus=int(tour_row["contacts_vus"]) + len(ids))
        dernier_id = max(max(ids), dernier_id)
        if suivante in (None, "", 0, "0"):
            ecrire_tour(conn, scope, termine_le=now_utc_iso())
            bilan["fin"] = "tour_termine"
            break
        page = int(suivante)
        if pause_toutes and bilan["pages"] % pause_toutes == 0:
            print(f"[liste-nuit] {bilan['pages']} pages -- pause de {int(pause_secondes)} s")
            dormir(pause_secondes)
    return bilan


def date_utc_de_relecture(valeur: Optional[str]) -> str:
    return texte(valeur)[:19].replace("T", " ")


def rapport(conn: sqlite3.Connection, scope: str) -> dict[str, Any]:
    """Ce que la lecture a appris, SANS rien changer. Uniquement des numeros."""
    tour = lire_tour(conn, scope)
    vus = conn.execute(
        """
        SELECT l.hektor_contact_id AS id, l.datemaj, l.ref_couple, l.id_negociateur, l.archive,
               s.last_detail_sync_at AS relu_le,
               h.hektor_contact_id AS au_miroir, h.hektor_negociateur_id AS nego_miroir,
               h.hektor_couple_contact_id AS couple_miroir, h.archive AS archive_miroir
        FROM liste_nuit_contact l
        LEFT JOIN sync_contact_state s ON s.hektor_contact_id = l.hektor_contact_id
        LEFT JOIN hektor_contact h ON h.hektor_contact_id = l.hektor_contact_id
        WHERE l.scope = ?
        """,
        (scope,),
    ).fetchall()
    a_relire: list[str] = []
    jamais_lus = date_inconnue = 0
    nego_change: Counter = Counter()
    couple_diff = archive_diff = absents = 0
    for r in vus:
        dm = texte(r["datemaj"])
        relu = date_utc_de_relecture(r["relu_le"])
        if not dm or dm.startswith("0000"):
            date_inconnue += 1
        elif not relu:
            jamais_lus += 1
            a_relire.append(r["id"])
        elif dm[:19] > relu:
            # Meme regle que sync_contact_details (l. 441-449) : datemaj (heure de Paris)
            # contre relecture (UTC) -> au pire une relecture en trop, jamais un oubli.
            a_relire.append(r["id"])
        if r["au_miroir"] is None:
            absents += 1
            continue
        nouveau = numero(r["id_negociateur"])
        if nouveau and nouveau != numero(r["nego_miroir"]):
            nego_change[(numero(r["nego_miroir"]) or "(vide)", nouveau)] += 1
        if numero(r["ref_couple"]) != numero(r["couple_miroir"]):
            couple_diff += 1
        if texte(r["archive"]) and texte(r["archive"]) != texte(r["archive_miroir"]):
            archive_diff += 1
    annonces = 0
    for debut in range(0, len(a_relire), 500):
        tranche = a_relire[debut:debut + 500]
        annonces += conn.execute(
            f"SELECT COUNT(DISTINCT hektor_annonce_id) FROM sync_annonce_contact_link "
            f"WHERE hektor_contact_id IN ({','.join('?' for _ in tranche)})",
            tranche,
        ).fetchone()[0]
    return {
        "scope": scope,
        "tour": dict(tour) if tour else None,
        "contacts_vus": len(vus),
        "fiches_a_relire": len(a_relire),
        "dont_jamais_lues": jamais_lus,
        "date_inconnue_0000": date_inconnue,
        "annonces_liees_aux_fiches_a_relire_au_plus": annonces,
        "absents_du_miroir": absents,
        "negociateur_change": sum(nego_change.values()),
        "negociateur_change_principaux": [
            {"miroir": a, "liste": b, "contacts": n} for (a, b), n in nego_change.most_common(10)
        ],
        "lien_de_couple_different": couple_diff,
        "etat_archive_different": archive_diff,
        "exemples_a_relire": a_relire[:20],
    }


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Liste entiere des contacts Hektor -- passage A BLANC.")
    ap.add_argument("--scope", choices=("active", "archived", "auto"), default="auto",
                    help="auto = archived le dimanche, active les autres jours.")
    ap.add_argument("--intervalle-ms", type=int, default=1000,
                    help="Plancher entre deux requetes, pour CE processus (defaut 1000 = le frein actuel).")
    ap.add_argument("--pause-toutes-pages", type=int, default=500)
    ap.add_argument("--pause-secondes", type=float, default=30.0)
    ap.add_argument("--heure-limite", default="", help="HH:MM, heure locale (ex. 01:55).")
    ap.add_argument("--max-pages", type=int, default=0, help="0 = sans plafond de pages.")
    ap.add_argument("--nouveau-tour", action="store_true", help="Repartir de la page 1.")
    ap.add_argument("--rapport-seul", action="store_true", help="Aucun appel Hektor : le rapport seul.")
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "hektor.sqlite")
    args = ap.parse_args(argv)

    scope = args.scope
    if scope == "auto":
        scope = "archived" if datetime.now().weekday() == 6 else "active"
    if args.intervalle_ms < 300:
        print("[liste-nuit] REFUS : intervalle sous 300 ms (plus de 3 req/s) -- au-dessus de tout ce qui a passe.")
        return 2

    conn = connect_db(args.db)
    creer_tables(conn)
    code = 0
    debut = time.time()
    lecteur: Optional[Lecteur] = None
    if not args.rapport_seul:
        settings = Settings.from_env()
        client = ClientListe(settings)
        client.min_request_interval = args.intervalle_ms / 1000.0
        lecteur = Lecteur(client, scope, settings.api_version)
        print(f"[liste-nuit] {scope} : A BLANC, {args.intervalle_ms} ms entre requetes, pause"
              f" {int(args.pause_secondes)} s toutes les {args.pause_toutes_pages} pages,"
              f" heure limite {args.heure_limite or '(aucune)'}")
        try:
            bilan = lire_la_liste(conn, lecteur, scope=scope, nouveau_tour=args.nouveau_tour,
                                  heure_limite=args.heure_limite or None, max_pages=args.max_pages,
                                  pause_toutes=args.pause_toutes_pages, pause_secondes=args.pause_secondes)
            print(f"[liste-nuit] fin : {bilan['fin']} -- {bilan['pages']} pages, {bilan['contacts']} contacts,"
                  f" {bilan['recul']} recul, {bilan['inversions']} page(s) hors ordre")
        except HektorNonRetryableError as exc:
            print(f"[liste-nuit] ARRET : Hektor REFUSE ({exc}). Rien n'est rejoue ; la reprise est gardee.")
            code = 3
        except RuntimeError as exc:
            print(f"[liste-nuit] ARRET : Hektor ne repond pas apres patience ({exc}). La reprise est gardee.")
            code = 4
        print(f"[liste-nuit] requetes Hektor : {lecteur.requetes} pages (+ la connexion)"
              f" en {round(time.time() - debut)} s")

    resultat = rapport(conn, scope)
    resultat["requetes_pages"] = lecteur.requetes if lecteur else 0
    resultat["code"] = code
    RAPPORTS.mkdir(parents=True, exist_ok=True)
    chemin = RAPPORTS / f"rapport_{scope}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    chemin.write_text(json.dumps(resultat, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in resultat.items() if k != "exemples_a_relire"}, ensure_ascii=False, indent=2))
    print(f"[liste-nuit] rapport : {chemin}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
