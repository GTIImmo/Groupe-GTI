#!/usr/bin/env python3
"""LA LISTE ENTIERE DES CONTACTS, LA NUIT -- PASSAGE A BLANC (03/11/2026).

Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §40 a §45.

LE DEFAUT. La nuit ne voit un contact modifie dans Hektor que s'il remonte en tete
de `ListContacts` triee par « date de dernier traitement ». Un rattachement de
couple (EA32621, 02/11) change la `datemaj` du contact mais PAS cette date : la
fiche n'est jamais relue. Hektor n'offre ni tri ni filtre par `datemaj` (essai du
03/11) : la seule facon de connaitre la date de chaque fiche est de lire TOUTE la
liste (tri par numero, ~8 500 pages actives, ~9 000 archivees).

CE QUE FAIT CE SCRIPT, A BLANC (le mode par defaut, eprouve en reel le 03/11, §47) :
  1. lit la liste par l'API seule (`/Api/Contact/ListContacts/`, sort=id ASC), page
     apres page, a la vitesse donnee (--intervalle-ms, pour CE processus seulement),
     avec une pause reguliere, une heure limite, et un arret net au premier refus ;
  2. garde SON carnet (`liste_nuit_contact`) et SON tour (`liste_nuit_tour`), et
     range ses pages sous un nom a part (`nuit_liste_contacts_<scope>`) ;
  3. dresse le RAPPORT : fiches a relire (date Hektor plus recente que notre
     derniere relecture), annonces liees, et ecarts avec notre miroir
     (negociateur, lien de couple, etat archive, fiches absentes).

EN MODE REEL (--reel, decision de Frederic du 03/11 : « c'est le but de les reparer
ces pages »), trois choses de plus -- et rien d'autre :
  a. les pages vont AU VRAI ENDROIT : `list_contacts_<scope>`, meme type d'objet,
     memes parametres que la relecture complete du 23/06
     (refetch_contacts_listing_parallel.py). `normalize_source` les relira a 04:00.
     Les pages au-dela de la fin du tour (2 256 pages de mars cote actifs) ne sont
     PAS effacees ici : c'est --purger-pages-perimees, un geste a part, apres lecture
     du rapport, et refuse tant qu'un tour REEL complet n'a pas reecrit 1..N ;
  b. les fiches a relire sont relues (`ContactById`, AU FREIN ACTUEL du projet :
     seule la liste va plus vite), jusqu'a --heure-limite-fiches, les plus
     recemment modifiees d'abord ; meme ecriture que sync_contact_details
     (`contact_detail` + `last_detail_sync_at`) ;
  c. chaque fiche relue entre au PANIER du run (`liste_nuit_contact.relu_le`, et
     `remis_au_run_le` vide) : le run de 04:00 relira leurs annonces si son
     interrupteur APP_RELIRE_ANNONCES_CONTACTS_NUIT=1 est pose (sync_raw.py).

⛔ CE QU'IL NE TOUCHE JAMAIS, meme en reel :
  · `sync_contact_state.date_maj`, `listing_variant`, `last_seen_at` et le curseur
    `contact_cursor_*` : c'est le carnet du run de 04:00, son signal pour relire les
    annonces des contacts qu'IL voit changer (sync_raw.py, find_annonce_ids_by_contact_ids).
    Seul `last_detail_sync_at` bouge pour une fiche relue -- c'est son sens exact ;
  · les pages `list_contacts_*_update` (celles du run) ;
  · rien ne part chez Supabase : la nuit de 04:00 normalise et pousse, comme toujours.

LA REPRISE se fait par NUMERO, pas par page : la page N n'est pas stable (44 445
contacts sortis des actifs entre mars et mai, la page 8430 de mars est devenue la
~6207). Au redemarrage on relit la derniere page lue ; si elle commence APRES le
dernier numero lu, des contacts ont recule d'une page : on recule jusqu'a la
retrouver. Une creation arrive en fin de liste et ne decale rien.

Usage :
    python phase2/sync/liste_contacts_nuit.py --scope active --intervalle-ms 400 --heure-limite 01:55
    python phase2/sync/liste_contacts_nuit.py --scope active --rapport-seul      (aucun appel Hektor)
    python phase2/sync/liste_contacts_nuit.py --scope auto --reel --attendre-file-vide \\
        --intervalle-ms 400 --heure-limite 01:55 --heure-limite-fiches 01:58      (la tache de nuit)
    python phase2/sync/liste_contacts_nuit.py --scope active --purger-pages-perimees [--confirmer]
Sortie : 0 = tour termine ou heure limite atteinte proprement · 2 = mauvais usage ou
         purge refusee · 3 = refus de Hektor sur la LISTE, la connexion, ou un frein (429) :
         blocage du compte · 4 = Hektor ne repond pas (apres patience) · 5 = Hektor refuse
         UNE fiche (403 isole) : elle est mise de cote, les fiches s'arretent pour la nuit.
         Le lanceur de nuit ne retient les recherches que sur 3 (decision du 03/11, §50).
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import (  # noqa: E402
    HEKTOR_MIN_REQUEST_INTERVAL_S,
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
# Fiches : pause en plus du frein du client (1 s) -> ~1,6 s par fiche, le rythme
# mesure des relectures de la tache des recherches (§44).
PAUSE_ENTRE_FICHES_S = 0.5
# Une fiche que Hektor dit introuvable (404) est mise de cote et on continue ; une
# serie de 404 n'est plus un cas isole : on s'arrete.
MAX_404_CONSECUTIFS = 10
# Une reponse illisible pour UNE fiche est mise de cote ; au-dela, on s'arrete.
MAX_REPONSES_ILLISIBLES = 3


class FicheRefusee(HektorNonRetryableError):
    """Hektor refuse UNE fiche (403 sur ContactById) : un cas isole connu (5 fiches
    mises de cote depuis mai, `sync_contact_detail_skip`), pas un blocage du compte.
    On s'arrete quand meme pour la nuit -- mais sans retenir les recherches."""


def endpoint_nuit(scope: str) -> str:
    # ⚠ PAS « list_contacts_… » : normalize_source relit tout ce qui porte ce nom.
    return f"nuit_liste_contacts_{scope}"


def endpoint_reel(scope: str) -> str:
    # Le VRAI endroit, celui que normalize_source relit (CONTACT_ENDPOINTS) et que
    # la relecture complete du 23/06 a ecrit. Meme type d'objet que sync_raw
    # (CONTACT_VARIANTS) : la cle de raw_api_response est (endpoint, type, objet, page).
    return f"list_contacts_{scope}"


def type_objet_reel(scope: str) -> str:
    return f"contact_{scope}"


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
    # Le panier du run (mode reel) : deux colonnes ajoutees a une table deja nee au
    # passage a blanc. `garder_page` ne les nomme pas : un nouveau tour les garde.
    colonnes = {r[1] for r in conn.execute("PRAGMA table_info(liste_nuit_contact)")}
    for colonne in ("relu_le", "remis_au_run_le"):
        if colonne not in colonnes:
            conn.execute(f"ALTER TABLE liste_nuit_contact ADD COLUMN {colonne} TEXT")
    reel = {r[1] for r in conn.execute("PRAGMA table_info(liste_nuit_tour)")}
    if "reel" not in reel:
        # 1 = toutes les pages de ce tour sont allees au vrai endroit (condition de la purge).
        conn.execute("ALTER TABLE liste_nuit_tour ADD COLUMN reel INTEGER NOT NULL DEFAULT 0")
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


def heure_des_declencheurs() -> datetime:
    """L'heure a l'horloge des taches planifiees : leurs declencheurs sont ecrits en
    +01:00 (« 02:00:00+01:00 »), donc l'ete toute la nuit glisse d'une heure locale
    (recherches a 03:00, run a 05:00). Une limite « 01:55 » suit la meme horloge ;
    en heure locale elle tomberait l'ete AVANT le depart de 00:20+01:00 (01:20)."""
    return datetime.now(timezone(timedelta(hours=1))).replace(tzinfo=None)


def heure_depassee(limite: Optional[str], maintenant: Optional[datetime] = None) -> bool:
    """`limite` = « HH:MM » a l'horloge des declencheurs (+01:00). Une limite avant
    midi vise la nuit qui suit un depart du soir (00:20 -> 01:55) : on ne la compare
    qu'apres minuit."""
    if not limite:
        return False
    h, m = (int(x) for x in limite.split(":"))
    now = maintenant or heure_des_declencheurs()
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
                payload: dict[str, Any], reel: bool = False) -> list[int]:
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
        conn, run_id=None,
        endpoint_name=endpoint_reel(scope) if reel else endpoint_nuit(scope),
        object_type=type_objet_reel(scope) if reel else "contact_liste_nuit",
        object_id=None, page=numero_page, params=params, payload=payload, http_status=200,
    )
    return ids


def premier_id(payload: dict[str, Any]) -> Optional[int]:
    ids = [int(texte(x.get("id"))) for x in lignes(payload)]
    return min(ids) if ids else None


def lire_la_liste(conn: sqlite3.Connection, lecteur: Lecteur, *, scope: str, nouveau_tour: bool,
                  heure_limite: Optional[str], max_pages: int, pause_toutes: int,
                  pause_secondes: float, dormir=time.sleep, reel: bool = False) -> dict[str, Any]:
    """Le coeur. Ne leve que HektorNonRetryableError (refus) et RuntimeError (pas de
    reponse) ; dans les deux cas le tour garde sa derniere page sure."""
    tour_row = lire_tour(conn, scope)
    # Un tour ne melange jamais les deux modes : la purge exige que TOUTES ses pages
    # soient allees au vrai endroit. Changer de mode = repartir de la page 1.
    autre_mode = tour_row is not None and int(tour_row["reel"] or 0) != int(reel)
    if nouveau_tour or tour_row is None or tour_row["termine_le"] or autre_mode:
        tour = now_utc_iso()
        ecrire_tour(conn, scope, tour=tour, derniere_page=0, dernier_id=0, total=None,
                    pages_lues=0, contacts_vus=0, termine_le=None, reel=int(reel))
        page, dernier_id = 1, 0
        print(f"[liste-nuit] {scope} : nouveau tour {tour}" + (" (REEL)" if reel else " (a blanc)"))
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
        ids = garder_page(conn, scope, tour, page, payload, reel=reel)
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


def table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nom,)).fetchone() is not None


def lignes_du_carnet(conn: sqlite3.Connection, scope: str) -> list[sqlite3.Row]:
    # La table des fiches mises de cote (404, reponse illisible) n'existe qu'une fois
    # qu'une fiche y est entree (sync_contact_details.ensure_contact_detail_skip).
    ecart = ("LEFT JOIN sync_contact_detail_skip k ON k.hektor_contact_id = l.hektor_contact_id"
             if table_existe(conn, "sync_contact_detail_skip") else "")
    ecart_col = "k.last_seen_at" if ecart else "NULL"
    return conn.execute(
        f"""
        SELECT l.hektor_contact_id AS id, l.datemaj, l.ref_couple, l.id_negociateur, l.archive,
               s.last_detail_sync_at AS relu_le, l.relu_le AS relu_la_nuit, {ecart_col} AS ecarte_le,
               h.hektor_contact_id AS au_miroir, h.hektor_negociateur_id AS nego_miroir,
               h.hektor_couple_contact_id AS couple_miroir, h.archive AS archive_miroir
        FROM liste_nuit_contact l
        LEFT JOIN sync_contact_state s ON s.hektor_contact_id = l.hektor_contact_id
        LEFT JOIN hektor_contact h ON h.hektor_contact_id = l.hektor_contact_id
        {ecart}
        WHERE l.scope = ?
        """,
        (scope,),
    ).fetchall()


def jugement(r: sqlite3.Row) -> str:
    """« inconnue » (date 0000 ou vide), « jamais » (jamais relue), « relire »,
    « ecartee » (mise de cote APRES sa derniere modification), ou « a_jour ».

    Derniere relecture = la plus recente de `last_detail_sync_at` (toutes les portes
    du projet) et de notre propre relecture de nuit (une fiche absente du carnet du
    run n'a pas de ligne a mettre a jour : sans ce second marqueur, elle serait
    relue chaque nuit). Meme regle que sync_contact_details (l. 441-449) : datemaj
    (heure de Paris) contre relecture (UTC) -> au pire une relecture en trop,
    jamais un oubli."""
    dm = texte(r["datemaj"])
    if not dm or dm.startswith("0000"):
        return "inconnue"
    relu = max(date_utc_de_relecture(r["relu_le"]), date_utc_de_relecture(r["relu_la_nuit"]))
    if relu and dm[:19] <= relu:
        return "a_jour"
    if r["ecarte_le"] and date_utc_de_relecture(r["ecarte_le"]) >= dm[:19]:
        return "ecartee"
    return "relire" if relu else "jamais"


def fiches_a_relire(conn: sqlite3.Connection, scope: str) -> list[str]:
    """Les plus recemment modifiees d'abord : si l'heure limite coupe, ce sont les
    gestes du jour qui passent."""
    lignes_ = [r for r in lignes_du_carnet(conn, scope) if jugement(r) in ("relire", "jamais")]
    lignes_.sort(key=lambda r: (texte(r["datemaj"]), int(r["id"])), reverse=True)
    return [r["id"] for r in lignes_]


def rapport(conn: sqlite3.Connection, scope: str) -> dict[str, Any]:
    """Ce que la lecture a appris, SANS rien changer. Uniquement des numeros."""
    tour = lire_tour(conn, scope)
    vus = lignes_du_carnet(conn, scope)
    a_relire: list[str] = []
    jamais_lus = date_inconnue = ecartees = 0
    nego_change: Counter = Counter()
    couple_diff = archive_diff = absents = 0
    for r in vus:
        avis = jugement(r)
        if avis == "inconnue":
            date_inconnue += 1
        elif avis == "ecartee":
            ecartees += 1
        elif avis in ("relire", "jamais"):
            a_relire.append(r["id"])
            jamais_lus += avis == "jamais"
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
        "fiches_ecartees_404_ou_illisibles": ecartees,
        "panier_du_run_en_attente": (conn.execute(
            "SELECT COUNT(*) FROM liste_nuit_contact WHERE relu_le IS NOT NULL AND remis_au_run_le IS NULL"
        ).fetchone()[0]),
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


def relire_les_fiches(conn: sqlite3.Connection, client: Any, version: str, ids: list[str], *,
                      heure_limite: Optional[str], dormir: Callable[[float], None] = time.sleep,
                      pause_s: float = PAUSE_ENTRE_FICHES_S,
                      bilan: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Relit les fiches, UNE requete chacune, et les met au panier du run.

    Memes ecritures que sync_contact_details (la porte eprouvee) : la reponse brute
    sous `contact_detail`, puis `last_detail_sync_at`. Plus stricte sur les erreurs :
    tout refus autre qu'un 404 arrete la nuit (« un 403 arrete tout, on ne rejoue
    jamais »). Leve FicheRefusee (403 sur une fiche, mise de cote comme le fait
    sync_contact_details), HektorNonRetryableError (autre refus : 429, 401...) ou
    RuntimeError (pas de reponse) ;
    `bilan`, fourni par l'appelant, garde alors les comptes jusqu'a l'arret.
    """
    # Import ici : sync_contact_details importe sync_raw, qui est lourd et inutile
    # au passage a blanc et au rapport.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from sync_contact_details import (  # noqa: E402
        CONTACT_DETAIL_ENDPOINT_NAME,
        CONTACT_DETAIL_PATH,
        is_contact_detail_403,
        is_contact_detail_404,
        mark_contact_detail_skip,
        validate_contact_detail_payload,
    )
    from sync_raw import mark_contact_detail_synced  # noqa: E402

    bilan = bilan if bilan is not None else {}
    bilan.update({"a_relire": len(ids), "relues": 0, "introuvables_404": 0, "illisibles": 0, "fin": "toutes"})
    suite_404 = 0
    for contact_id in ids:
        if heure_depassee(heure_limite):
            bilan["fin"] = "heure_limite"
            break
        params = {"id": contact_id, "version": version}
        try:
            payload = client.get_json(CONTACT_DETAIL_PATH, params=params)
        except HektorNonRetryableError as exc:
            if is_contact_detail_403(exc):
                mark_contact_detail_skip(conn, contact_id, reason="http_403_forbidden", error_message=str(exc))
                conn.commit()
                bilan["refusees_403"] = bilan.get("refusees_403", 0) + 1
                raise FicheRefusee(f"fiche {contact_id} refusee : {exc}") from exc
            if not is_contact_detail_404(exc):
                raise
            mark_contact_detail_skip(conn, contact_id, reason="http_404_not_found", error_message=str(exc))
            conn.commit()
            bilan["introuvables_404"] += 1
            suite_404 += 1
            if suite_404 >= MAX_404_CONSECUTIFS:
                raise RuntimeError(f"{suite_404} fiches introuvables de suite (dernier {contact_id}) : on s'arrete")
            dormir(pause_s)
            continue
        suite_404 = 0
        try:
            validate_contact_detail_payload(payload, contact_id)
        except RuntimeError as exc:
            mark_contact_detail_skip(conn, contact_id, reason="reponse_illisible", error_message=str(exc))
            conn.commit()
            bilan["illisibles"] += 1
            if bilan["illisibles"] >= MAX_REPONSES_ILLISIBLES:
                raise RuntimeError(f"{bilan['illisibles']} reponses illisibles (derniere {contact_id}) : on s'arrete")
            dormir(pause_s)
            continue
        upsert_raw_response(  # commit dedans
            conn, run_id=None, endpoint_name=CONTACT_DETAIL_ENDPOINT_NAME, object_type="contact_detail",
            object_id=contact_id, page=None, params=params, payload=payload, http_status=200,
        )
        mark_contact_detail_synced(conn, contact_id)  # UPDATE seul : sans ligne au carnet du run, rien
        # Au panier du run : relue maintenant, pas encore remise (une fiche relue une
        # seconde fois avant 04:00 y revient, ce qui est le but).
        conn.execute(
            "UPDATE liste_nuit_contact SET relu_le = ?, remis_au_run_le = NULL WHERE hektor_contact_id = ?",
            (now_utc_iso(), contact_id),
        )
        conn.commit()
        bilan["relues"] += 1
        dormir(pause_s)
    return bilan


# ── LA GARDE « WORKER VIDE » ────────────────────────────────────────────────────
# Le balayage des photos masquees (23:00) fait travailler le worker jusque vers
# 00:20-01:00. Le worker parle a Hektor par la console, avec SON frein : deux
# processus = deux freins qui s'additionnent (bannissement du 17/09). La liste rapide
# attend donc que la file soit vide. ⛔ Une lecture ratee n'est JAMAIS un vert : si
# Supabase ne repond pas, on considere la file occupee.

def lire_fichiers_env() -> None:
    """Meme ordre que monitoring/check_gti_health.configure_supabase, sans ecraser
    une variable deja posee."""
    for chemin in (ROOT / ".env", ROOT / "backend" / ".env", ROOT / "apps" / "hektor-v1" / ".env"):
        if not chemin.exists():
            continue
        for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))


def travaux_en_file() -> Optional[int]:
    """Nombre de travaux pending ou running (au plus 1 : on ne veut que savoir si
    c'est vide). None = pas pu lire."""
    lire_fichiers_env()
    url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not cle:
        return None
    requete = urllib.request.Request(
        url + "/rest/v1/app_console_job?select=id&status=in.(pending,running)&limit=1",
        headers={"apikey": cle, "Authorization": f"Bearer {cle}"},
    )
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            return len(json.loads(reponse.read().decode("utf-8")))
    except Exception as exc:  # noqa: BLE001
        print(f"[liste-nuit] file du worker illisible ({type(exc).__name__}) -- comptee comme occupee")
        return None


def attendre_file_vide(heure_limite: Optional[str], *, lire: Callable[[], Optional[int]] = travaux_en_file,
                       dormir: Callable[[float], None] = time.sleep, pas_s: float = 120.0) -> bool:
    """True quand la file est vide ; False si l'heure limite arrive avant."""
    while True:
        n = lire()
        if n == 0:
            return True
        if heure_depassee(heure_limite):
            return False
        print(f"[liste-nuit] {datetime.now():%H:%M} : le worker travaille encore"
              f" ({'illisible' if n is None else 'file non vide'}) -- on attend {int(pas_s)} s")
        dormir(pas_s)


# ── LA PURGE DES PAGES PERIMEES ─────────────────────────────────────────────────
# Le meme geste que sync_raw.prune_raw_listing_pages (apres un balayage complet des
# annonces), avec deux gardes de plus : le tour doit etre TERMINE et REEL, et chacune
# de ses pages 1..N doit avoir ete reecrite PENDANT ce tour. Au 03/11 cote actifs :
# pages 1..8429 du 23/06, 8430..10759 du 30/03 ; un tour reel en ecrit 1..8503 ->
# 2 256 pages de mars a retirer (celles qui imposent un negociateur perime).

def pages_perimees(conn: sqlite3.Connection, scope: str) -> dict[str, Any]:
    tour = lire_tour(conn, scope)
    endpoint = endpoint_reel(scope)
    if tour is None or not tour["termine_le"] or not int(tour["reel"] or 0):
        return {"refus": "aucun tour REEL termine pour ce perimetre"}
    n = int(tour["derniere_page"])
    vieilles_dans_le_tour = conn.execute(
        "SELECT COUNT(*) FROM raw_api_response WHERE endpoint_name = ? AND page_key BETWEEN 1 AND ?"
        " AND fetched_at < ?", (endpoint, n, tour["tour"]),
    ).fetchone()[0]
    ecrites = conn.execute(
        "SELECT COUNT(*) FROM raw_api_response WHERE endpoint_name = ? AND page_key BETWEEN 1 AND ?"
        " AND fetched_at >= ?", (endpoint, n, tour["tour"]),
    ).fetchone()[0]
    if vieilles_dans_le_tour or ecrites != n:
        return {"refus": f"pages 1..{n} pas toutes reecrites pendant le tour {tour['tour']}"
                         f" ({ecrites} fraiches, {vieilles_dans_le_tour} anciennes)"}
    au_dela = conn.execute(
        "SELECT COUNT(*), MIN(page_key), MAX(page_key), MIN(fetched_at), MAX(fetched_at)"
        " FROM raw_api_response WHERE endpoint_name = ? AND page_key > ?", (endpoint, n),
    ).fetchone()
    return {"endpoint": endpoint, "derniere_page_du_tour": n, "tour": tour["tour"],
            "pages_au_dela": au_dela[0], "de_la_page": au_dela[1], "a_la_page": au_dela[2],
            "lues_entre": [au_dela[3], au_dela[4]]}


def purger_pages_perimees(conn: sqlite3.Connection, scope: str, confirmer: bool) -> int:
    etat = pages_perimees(conn, scope)
    print(json.dumps(etat, ensure_ascii=False, indent=2))
    if "refus" in etat:
        print("[liste-nuit] PURGE REFUSEE.")
        return 2
    if not confirmer:
        print("[liste-nuit] (a blanc : rien n'est efface ; --confirmer pour retirer ces pages)")
        return 0
    conn.execute("DELETE FROM raw_api_response WHERE endpoint_name = ? AND page_key > ?",
                 (etat["endpoint"], etat["derniere_page_du_tour"]))
    conn.commit()
    print(f"[liste-nuit] {etat['pages_au_dela']} page(s) retiree(s) de {etat['endpoint']}.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Liste entiere des contacts Hektor -- a blanc par defaut, --reel la nuit.")
    ap.add_argument("--scope", choices=("active", "archived", "auto"), default="auto",
                    help="auto = archived le dimanche, active les autres jours.")
    ap.add_argument("--intervalle-ms", type=int, default=1000,
                    help="Plancher entre deux requetes de LISTE, pour CE processus (defaut 1000 = le frein actuel)."
                         " Les fiches restent au frein du projet.")
    ap.add_argument("--pause-toutes-pages", type=int, default=500)
    ap.add_argument("--pause-secondes", type=float, default=30.0)
    ap.add_argument("--heure-limite", default="", help="HH:MM, heure locale (ex. 01:55) : fin de la LISTE.")
    ap.add_argument("--max-pages", type=int, default=0, help="0 = sans plafond de pages.")
    ap.add_argument("--nouveau-tour", action="store_true", help="Repartir de la page 1.")
    ap.add_argument("--rapport-seul", action="store_true", help="Aucun appel Hektor : le rapport seul.")
    ap.add_argument("--reel", action="store_true",
                    help="Pages au vrai endroit (list_contacts_<scope>), fiches relues, panier du run.")
    ap.add_argument("--heure-limite-fiches", default="", help="HH:MM : fin de la relecture des fiches (mode reel).")
    ap.add_argument("--sans-fiches", action="store_true", help="Mode reel : la liste seule, aucune fiche relue.")
    ap.add_argument("--attendre-file-vide", action="store_true",
                    help="Attendre que la file du worker soit vide (au plus jusqu'a --heure-limite).")
    ap.add_argument("--purger-pages-perimees", action="store_true",
                    help="Montrer (ou retirer avec --confirmer) les pages au-dela du dernier tour REEL termine.")
    ap.add_argument("--confirmer", action="store_true")
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "hektor.sqlite")
    args = ap.parse_args(argv)

    scope = args.scope
    if scope == "auto":
        scope = "archived" if heure_des_declencheurs().weekday() == 6 else "active"
    if args.intervalle_ms < 300:
        print("[liste-nuit] REFUS : intervalle sous 300 ms (plus de 3 req/s) -- au-dessus de tout ce qui a passe.")
        return 2

    conn = connect_db(args.db)
    creer_tables(conn)
    if args.purger_pages_perimees:
        return purger_pages_perimees(conn, scope, args.confirmer)

    code = 0
    debut = time.time()
    lecteur: Optional[Lecteur] = None
    resultat_fiches: Optional[dict[str, Any]] = None
    bilan: Optional[dict[str, Any]] = None
    if not args.rapport_seul:
        if args.attendre_file_vide and not attendre_file_vide(args.heure_limite or None):
            print(f"[liste-nuit] {datetime.now():%H:%M} : le worker n'a pas fini avant l'heure limite --"
                  " PAS DE LISTE cette nuit (le tour reprendra la nuit prochaine)")
        else:
            settings = Settings.from_env()
            client = ClientListe(settings)
            client.min_request_interval = args.intervalle_ms / 1000.0
            lecteur = Lecteur(client, scope, settings.api_version)
            print(f"[liste-nuit] {scope} : {'REEL' if args.reel else 'A BLANC'}, {args.intervalle_ms} ms entre"
                  f" requetes, pause {int(args.pause_secondes)} s toutes les {args.pause_toutes_pages} pages,"
                  f" heure limite {args.heure_limite or '(aucune)'}")
            try:
                bilan = lire_la_liste(conn, lecteur, scope=scope, nouveau_tour=args.nouveau_tour,
                                      heure_limite=args.heure_limite or None, max_pages=args.max_pages,
                                      pause_toutes=args.pause_toutes_pages, pause_secondes=args.pause_secondes,
                                      reel=args.reel)
                print(f"[liste-nuit] fin : {bilan['fin']} -- {bilan['pages']} pages, {bilan['contacts']} contacts,"
                      f" {bilan['recul']} recul, {bilan['inversions']} page(s) hors ordre")
                if args.reel and not args.sans_fiches:
                    # Les fiches au FREIN DU PROJET : seule la liste va plus vite (Frederic, 03/11).
                    client.min_request_interval = HEKTOR_MIN_REQUEST_INTERVAL_S
                    ids = fiches_a_relire(conn, scope)
                    print(f"[liste-nuit] fiches a relire : {len(ids)} (frein {HEKTOR_MIN_REQUEST_INTERVAL_S:g} s"
                          f" + {PAUSE_ENTRE_FICHES_S:g} s), heure limite {args.heure_limite_fiches or '(aucune)'}")
                    resultat_fiches = {}
                    relire_les_fiches(conn, client, settings.api_version, ids,
                                      heure_limite=args.heure_limite_fiches or None, bilan=resultat_fiches)
                    print(f"[liste-nuit] fiches : {json.dumps(resultat_fiches, ensure_ascii=False)}")
            except FicheRefusee as exc:
                print(f"[liste-nuit] ARRET DES FICHES : Hektor refuse une fiche ({exc}). Elle est mise de cote.")
                code = 5
                if resultat_fiches is not None:
                    resultat_fiches["fin"] = "fiche_refusee"
            except HektorNonRetryableError as exc:
                print(f"[liste-nuit] ARRET : Hektor REFUSE ({exc}). Rien n'est rejoue ; la reprise est gardee.")
                code = 3
                if resultat_fiches is not None:
                    resultat_fiches["fin"] = "refus"
            except RuntimeError as exc:
                print(f"[liste-nuit] ARRET : Hektor ne repond pas, ou trop d'erreurs ({exc}). La reprise est gardee.")
                code = 4
                if resultat_fiches is not None:
                    resultat_fiches["fin"] = "arret"
            f_ = resultat_fiches or {}
            fiches_demandees = (f_.get("relues", 0) + f_.get("introuvables_404", 0) + f_.get("illisibles", 0)
                                + f_.get("refusees_403", 0))
            print(f"[liste-nuit] requetes Hektor : {lecteur.requetes} pages + {fiches_demandees} fiches"
                  f" (+ la connexion) en {round(time.time() - debut)} s")

    resultat = rapport(conn, scope)
    resultat["mode"] = "reel" if args.reel else "a_blanc"
    resultat["liste"] = bilan
    resultat["fiches"] = resultat_fiches
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
