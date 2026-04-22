from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from typing import Any, Dict, Iterable

from hektor_pipeline.common import Settings, connect_db, fetch_latest_raw_payloads, init_db, json_dumps, now_utc_iso
from phase2.sync.manual_mandat_corrections import get_manual_mandat_correction, inject_manual_mandat_if_missing


ANNONCE_ENDPOINTS = (
    "list_annonces_active",
)
CONTACT_ENDPOINTS = (
    "list_contacts",
    "list_contacts_active",
    "list_contacts_archived",
    "list_contacts_active_update",
    "list_contacts_archived_update",
)
MANDAT_ENDPOINTS = ("list_mandats", "list_mandats_update")
OFFRE_ENDPOINTS = ("list_offres", "list_offres_update")
COMPROMIS_ENDPOINTS = ("list_compromis", "list_compromis_update")
VENTE_ENDPOINTS = ("list_ventes", "list_ventes_update")
NEGO_ENDPOINTS = ("list_negos", "nego_by_id")


def iter_listing_items(rows: Iterable[sqlite3.Row]) -> Iterable[Dict[str, Any]]:
    for row in rows:
        payload = json.loads(row["payload_json"])
        data = payload.get("data") or []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item


def latest_detail_map(rows: Iterable[sqlite3.Row]) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        payload = json.loads(row["payload_json"])
        data = payload.get("data")
        object_id = str(row["object_id"] or "").strip()
        if object_id and isinstance(data, dict):
            output[object_id] = data
    return output


def iter_listing_items_for_endpoints(conn: sqlite3.Connection, endpoint_names: Iterable[str]) -> Iterable[Dict[str, Any]]:
    for endpoint_name in endpoint_names:
        yield from iter_listing_items(fetch_latest_raw_payloads(conn, endpoint_name))


def active_annonce_ids_from_raw(conn: sqlite3.Connection) -> set[str]:
    output: set[str] = set()
    for item in iter_listing_items_for_endpoints(conn, ANNONCE_ENDPOINTS):
        annonce_id = normalized_id(item.get("id"))
        if annonce_id:
            output.add(annonce_id)
    return output


def get_detail_payload(data: Dict[str, Any], nested_key: str | None = None) -> Dict[str, Any]:
    if nested_key and isinstance(data.get(nested_key), dict):
        return data[nested_key]
    return data


def normalized_id(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text or text in {"0", "null", "None"}:
        return None
    return text


def first_present(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def parse_json_list(value: Any) -> list[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except Exception:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    return []


def parse_numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("\u00a0", "").replace(" ", "")
    if not text:
        return None
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def values_differ(previous: float | None, current: float | None) -> bool:
    return previous is not None and current is not None and abs(previous - current) > 1e-9


def build_price_change_event_key(
    *,
    source_kind: str,
    hektor_annonce_id: str | None,
    hektor_mandat_id: str | None,
    numero_mandat: str | None,
    old_value: float,
    new_value: float,
    source_updated_at: str | None,
) -> str:
    payload = "|".join(
        [
            source_kind,
            hektor_annonce_id or "",
            hektor_mandat_id or "",
            numero_mandat or "",
            f"{old_value:.6f}",
            f"{new_value:.6f}",
            source_updated_at or "",
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def insert_price_change_event(
    conn: sqlite3.Connection,
    *,
    source_kind: str,
    hektor_annonce_id: str | None,
    hektor_mandat_id: str | None,
    numero_mandat: str | None,
    old_value: float,
    new_value: float,
    source_updated_at: str | None,
    raw_context: Dict[str, Any],
) -> None:
    event_key = build_price_change_event_key(
        source_kind=source_kind,
        hektor_annonce_id=hektor_annonce_id,
        hektor_mandat_id=hektor_mandat_id,
        numero_mandat=numero_mandat,
        old_value=old_value,
        new_value=new_value,
        source_updated_at=source_updated_at,
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO hektor_price_change_event(
            event_key,
            hektor_annonce_id,
            hektor_mandat_id,
            numero_mandat,
            source_kind,
            old_value,
            new_value,
            source_updated_at,
            detected_at,
            raw_context_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_key,
            hektor_annonce_id,
            hektor_mandat_id,
            numero_mandat,
            source_kind,
            old_value,
            new_value,
            source_updated_at,
            now_utc_iso(),
            json_dumps(raw_context),
        ),
    )


def derive_offre_state_and_event_date(source: Dict[str, Any], item: Dict[str, Any]) -> tuple[str | None, str | None]:
    propositions = parse_json_list(source.get("propositions") or item.get("propositions"))
    latest_event_date = None
    has_proposition = False
    has_accepted = False
    for proposition in propositions:
        proposition_type = str(proposition.get("type") or "").strip().lower()
        proposition_date = str(proposition.get("date") or "").strip() or None
        if proposition_date and (latest_event_date is None or proposition_date > latest_event_date):
            latest_event_date = proposition_date
        if proposition_type == "accepte":
            has_accepted = True
        elif proposition_type == "proposition":
            has_proposition = True
    if has_accepted:
        return "accepted", latest_event_date
    if has_proposition:
        return "proposed", latest_event_date
    fallback_date = first_present(
        source.get("date"),
        source.get("date_creation"),
        source.get("dateCreation"),
        item.get("date"),
        item.get("date_creation"),
        item.get("dateCreation"),
    )
    return None, str(fallback_date or latest_event_date or "") or None


def derive_compromis_state(status: Any) -> str | None:
    status_text = str(status or "").strip()
    if status_text == "1":
        return "active"
    if status_text == "2":
        return "cancelled"
    return None


def load_annonce_mandat_links(conn: sqlite3.Connection) -> tuple[Dict[str, str], Dict[str, str]]:
    mandat_id_to_annonce: Dict[str, str] = {}
    mandat_numero_to_annonce: Dict[str, str] = {}

    for row in conn.execute("SELECT hektor_annonce_id, no_mandat FROM hektor_annonce"):
        annonce_id = normalized_id(row["hektor_annonce_id"])
        numero = str(row["no_mandat"] or "").strip()
        if annonce_id and numero:
            mandat_numero_to_annonce[numero] = annonce_id

    for row in conn.execute("SELECT hektor_annonce_id, mandats_json FROM hektor_annonce_detail"):
        annonce_id = normalized_id(row["hektor_annonce_id"])
        try:
            mandats = json.loads(row["mandats_json"] or "[]")
        except Exception:
            mandats = []
        if not annonce_id or not isinstance(mandats, list):
            continue
        for mandat in mandats:
            if not isinstance(mandat, dict):
                continue
            mandat_id = normalized_id(mandat.get("id"))
            numero = str(mandat.get("numero") or "").strip()
            if mandat_id:
                mandat_id_to_annonce[mandat_id] = annonce_id
            if numero and numero not in mandat_numero_to_annonce:
                mandat_numero_to_annonce[numero] = annonce_id

    return mandat_id_to_annonce, mandat_numero_to_annonce


def upsert_agences(conn: sqlite3.Connection) -> None:
    for item in iter_listing_items(fetch_latest_raw_payloads(conn, "list_agences")):
        conn.execute(
            """
            INSERT INTO hektor_agence(hektor_agence_id, nom, type, mail, tel, responsable, parent_id, raw_json, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_agence_id) DO UPDATE SET
                nom = excluded.nom,
                type = excluded.type,
                mail = excluded.mail,
                tel = excluded.tel,
                responsable = excluded.responsable,
                parent_id = excluded.parent_id,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                str(item.get("id") or ""),
                item.get("nom"),
                item.get("type"),
                item.get("mail"),
                item.get("tel"),
                item.get("responsable"),
                normalized_id(item.get("parent")),
                json_dumps(item),
                now_utc_iso(),
            ),
        )
    conn.commit()


def upsert_negos(conn: sqlite3.Connection) -> None:
    for row in fetch_latest_raw_payloads(conn, "list_negos"):
        payload = json.loads(row["payload_json"])
        data = payload.get("data") or []
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            conn.execute(
                """
                INSERT INTO hektor_negociateur(
                    hektor_negociateur_id, hektor_user_id, hektor_agence_id, nom, prenom, email, telephone, portable, raw_json, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(hektor_negociateur_id) DO UPDATE SET
                    hektor_user_id = excluded.hektor_user_id,
                    hektor_agence_id = excluded.hektor_agence_id,
                    nom = excluded.nom,
                    prenom = excluded.prenom,
                    email = excluded.email,
                    telephone = excluded.telephone,
                    portable = excluded.portable,
                    raw_json = excluded.raw_json,
                    synced_at = excluded.synced_at
                """,
                (
                    str(item.get("id") or ""),
                    normalized_id(item.get("idUser")),
                    normalized_id(item.get("agence")),
                    item.get("nom"),
                    item.get("prenom"),
                    item.get("email"),
                    item.get("telephone"),
                    item.get("portable"),
                    json_dumps(item),
                    now_utc_iso(),
                ),
            )
    for row in fetch_latest_raw_payloads(conn, "nego_by_id"):
        payload = json.loads(row["payload_json"])
        item = payload.get("negociateur")
        if not isinstance(item, dict):
            continue
        conn.execute(
            """
            INSERT INTO hektor_negociateur(
                hektor_negociateur_id, hektor_user_id, hektor_agence_id, nom, prenom, email, telephone, portable, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_negociateur_id) DO UPDATE SET
                hektor_user_id = excluded.hektor_user_id,
                hektor_agence_id = excluded.hektor_agence_id,
                nom = excluded.nom,
                prenom = excluded.prenom,
                email = excluded.email,
                telephone = excluded.telephone,
                portable = excluded.portable,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                str(item.get("id") or ""),
                normalized_id(item.get("idUser")),
                normalized_id(item.get("agence")),
                item.get("nom"),
                item.get("prenom"),
                item.get("email"),
                item.get("telephone"),
                item.get("portable"),
                json_dumps(item),
                now_utc_iso(),
            ),
        )
    conn.commit()


def upsert_annonces(conn: sqlite3.Connection) -> None:
    for item in iter_listing_items_for_endpoints(conn, ANNONCE_ENDPOINTS):
        localite = item.get("localite") or {}
        publique = localite.get("publique") if isinstance(localite, dict) else {}
        annonce_id = str(item.get("id") or "")
        previous_row = conn.execute(
            "SELECT prix, date_maj, no_mandat FROM hektor_annonce WHERE hektor_annonce_id = ?",
            (annonce_id,),
        ).fetchone()
        previous_price = parse_numeric_value(previous_row["prix"]) if previous_row else None
        next_price = parse_numeric_value(item.get("prix"))
        if values_differ(previous_price, next_price):
            previous_numero_mandat = str(previous_row["no_mandat"]).strip() if previous_row and previous_row["no_mandat"] is not None else ""
            source_updated_at = str(item.get("datemaj") or (previous_row["date_maj"] if previous_row else "") or "").strip() or None
            insert_price_change_event(
                conn,
                source_kind="annonce_prix",
                hektor_annonce_id=annonce_id,
                hektor_mandat_id=None,
                numero_mandat=str(item.get("NO_MANDAT") or previous_numero_mandat or "").strip() or None,
                old_value=previous_price,
                new_value=next_price,
                source_updated_at=source_updated_at,
                raw_context={
                    "hektor_annonce_id": annonce_id,
                    "numero_dossier": item.get("NO_DOSSIER"),
                    "numero_mandat": item.get("NO_MANDAT"),
                    "old_value": previous_price,
                    "new_value": next_price,
                    "date_maj": item.get("datemaj"),
                },
            )
        conn.execute(
            """
            INSERT INTO hektor_annonce(
                hektor_annonce_id, no_dossier, no_mandat, hektor_agence_id, hektor_negociateur_id, date_maj, offre_type, idtype,
                prix, surface, archive, diffusable, valide, partage, titre, ville, code_postal, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_annonce_id) DO UPDATE SET
                no_dossier = excluded.no_dossier,
                no_mandat = excluded.no_mandat,
                hektor_agence_id = excluded.hektor_agence_id,
                hektor_negociateur_id = excluded.hektor_negociateur_id,
                date_maj = excluded.date_maj,
                offre_type = excluded.offre_type,
                idtype = excluded.idtype,
                prix = excluded.prix,
                surface = excluded.surface,
                archive = excluded.archive,
                diffusable = excluded.diffusable,
                valide = excluded.valide,
                partage = excluded.partage,
                titre = excluded.titre,
                ville = excluded.ville,
                code_postal = excluded.code_postal,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                annonce_id,
                item.get("NO_DOSSIER"),
                item.get("NO_MANDAT"),
                normalized_id(item.get("agence")),
                normalized_id(item.get("NEGOCIATEUR")),
                item.get("datemaj"),
                item.get("offredem"),
                item.get("idtype"),
                item.get("prix"),
                item.get("surface"),
                item.get("archive"),
                item.get("diffusable"),
                item.get("valide"),
                item.get("partage"),
                item.get("titre"),
                publique.get("ville") if isinstance(publique, dict) else None,
                publique.get("code") if isinstance(publique, dict) else None,
                json_dumps(item),
                now_utc_iso(),
            ),
        )
    conn.commit()


def prune_annonce_scope(conn: sqlite3.Connection, active_annonce_ids: set[str]) -> None:
    if not active_annonce_ids:
        for table in (
            "hektor_annonce_detail",
            "hektor_annonce",
            "hektor_offre",
            "hektor_compromis",
            "hektor_vente",
            "hektor_price_change_event",
            "hektor_broadcast_listing",
            "hektor_annonce_broadcast_state",
            "sync_annonce_contact_link",
        ):
            conn.execute(f"DELETE FROM {table}")
        conn.execute("DELETE FROM hektor_mandat WHERE hektor_annonce_id IS NOT NULL")
        conn.commit()
        return

    placeholders = ", ".join("?" for _ in active_annonce_ids)
    params = tuple(sorted(active_annonce_ids))
    for table in (
        "hektor_annonce_detail",
        "hektor_annonce",
        "hektor_offre",
        "hektor_compromis",
        "hektor_vente",
        "hektor_broadcast_listing",
        "hektor_annonce_broadcast_state",
        "sync_annonce_contact_link",
    ):
        conn.execute(f"DELETE FROM {table} WHERE hektor_annonce_id NOT IN ({placeholders})", params)
    conn.execute(f"DELETE FROM hektor_price_change_event WHERE hektor_annonce_id NOT IN ({placeholders})", params)
    conn.execute(
        f"DELETE FROM hektor_mandat WHERE hektor_annonce_id IS NOT NULL AND hektor_annonce_id NOT IN ({placeholders})",
        params,
    )
    conn.commit()


def upsert_annonce_details(conn: sqlite3.Connection) -> None:
    details = latest_detail_map(fetch_latest_raw_payloads(conn, "annonce_detail"))
    for annonce_id, data in details.items():
        data = inject_manual_mandat_if_missing(data)
        statut = data.get("statut") or {}
        conn.execute(
            """
            INSERT INTO hektor_annonce_detail(
                hektor_annonce_id, statut_id, statut_name, localite_json, mandats_json, proprietaires_json, honoraires_json,
                notes_json, zones_json, particularites_json, pieces_json, images_json, textes_json, terrain_json,
                copropriete_json, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_annonce_id) DO UPDATE SET
                statut_id = excluded.statut_id,
                statut_name = excluded.statut_name,
                localite_json = excluded.localite_json,
                mandats_json = excluded.mandats_json,
                proprietaires_json = excluded.proprietaires_json,
                honoraires_json = excluded.honoraires_json,
                notes_json = excluded.notes_json,
                zones_json = excluded.zones_json,
                particularites_json = excluded.particularites_json,
                pieces_json = excluded.pieces_json,
                images_json = excluded.images_json,
                textes_json = excluded.textes_json,
                terrain_json = excluded.terrain_json,
                copropriete_json = excluded.copropriete_json,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                annonce_id,
                statut.get("id") if isinstance(statut, dict) else None,
                statut.get("name") if isinstance(statut, dict) else None,
                json_dumps(data.get("localite")),
                json_dumps(data.get("mandats")),
                json_dumps(data.get("proprietaires")),
                json_dumps(data.get("honoraires")),
                json_dumps(data.get("notes")),
                json_dumps(data.get("zones")),
                json_dumps(data.get("particularites")),
                json_dumps(data.get("pieces")),
                json_dumps(data.get("images")),
                json_dumps(data.get("textes")),
                json_dumps(data.get("terrain")),
                json_dumps(data.get("copropriete")),
                json_dumps(data),
                now_utc_iso(),
            ),
        )
    conn.commit()


def upsert_mandats(conn: sqlite3.Connection) -> None:
    annonce_detail_map = latest_detail_map(fetch_latest_raw_payloads(conn, "annonce_detail"))
    detail_map = latest_detail_map(fetch_latest_raw_payloads(conn, "mandat_detail"))
    mandat_id_to_annonce, mandat_numero_to_annonce = load_annonce_mandat_links(conn)

    relation_items: Dict[str, Dict[str, Any]] = {}
    for row in fetch_latest_raw_payloads(conn, "mandats_by_annonce"):
        payload = json.loads(row["payload_json"])
        annonce_id = str(row["object_id"] or "").strip()
        data = payload.get("data") or []
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            mandat_id = str(item.get("id") or "").strip()
            if mandat_id:
                enriched = dict(item)
                enriched["idAnnonce"] = annonce_id
                relation_items[mandat_id] = enriched

    existing_relation_pairs = {
        (
            normalized_id(item.get("idAnnonce")),
            str(first_present(item.get("numero"), "") or "").strip(),
        )
        for item in relation_items.values()
    }
    for annonce_id, detail_data in annonce_detail_map.items():
        patched_detail = inject_manual_mandat_if_missing(detail_data)
        correction = get_manual_mandat_correction(
            mandate_number=((patched_detail.get("keyData") or {}) if isinstance(patched_detail.get("keyData"), dict) else {}).get("NO_MANDAT")
        )
        if not correction:
            continue
        pair = (annonce_id, str(correction.get("numero") or "").strip())
        if pair in existing_relation_pairs:
            continue
        manual_item = dict(correction)
        manual_item["idAnnonce"] = annonce_id
        relation_items[str(manual_item["id"])] = manual_item
        existing_relation_pairs.add(pair)

    seen_ids: set[str] = set()

    for item in iter_listing_items_for_endpoints(conn, MANDAT_ENDPOINTS):
        detail_item = detail_map.get(str(item.get("id") or "").strip(), item)
        mandat_id = str(detail_item.get("id") or item.get("id") or "").strip()
        relation_item = relation_items.get(mandat_id, {})
        source = dict(item)
        source.update(detail_item)
        source.update(relation_item)
        mandat_numero = str(first_present(source.get("numero"), item.get("numero")) or "").strip()
        hektor_annonce_id = (
                normalized_id(source.get("idAnnonce"))
            or mandat_id_to_annonce.get(mandat_id)
            or mandat_numero_to_annonce.get(mandat_numero)
        )
        seen_ids.add(mandat_id)
        previous_row = conn.execute(
            "SELECT montant, hektor_annonce_id, numero, synced_at FROM hektor_mandat WHERE hektor_mandat_id = ?",
            (mandat_id,),
        ).fetchone()
        previous_montant = parse_numeric_value(previous_row["montant"]) if previous_row else None
        next_montant = parse_numeric_value(first_present(source.get("montant"), item.get("montant")))
        if values_differ(previous_montant, next_montant):
            source_updated_at = (
                str(first_present(source.get("dateMaj"), source.get("datemaj"), source.get("dateEnregistrement"), source.get("debut")) or "").strip()
                or now_utc_iso()
            )
            event_annonce_id = hektor_annonce_id or (normalized_id(previous_row["hektor_annonce_id"]) if previous_row else None)
            event_numero = mandat_numero or (str(previous_row["numero"]).strip() if previous_row and previous_row["numero"] is not None else None)
            insert_price_change_event(
                conn,
                source_kind="mandat_montant",
                hektor_annonce_id=event_annonce_id,
                hektor_mandat_id=mandat_id,
                numero_mandat=event_numero,
                old_value=previous_montant,
                new_value=next_montant,
                source_updated_at=source_updated_at,
                raw_context={
                    "hektor_mandat_id": mandat_id,
                    "hektor_annonce_id": hektor_annonce_id,
                    "numero_mandat": mandat_numero,
                    "old_value": previous_montant,
                    "new_value": next_montant,
                    "type": first_present(source.get("type"), item.get("type")),
                },
            )
        conn.execute(
            """
            INSERT INTO hektor_mandat(
                hektor_mandat_id, hektor_annonce_id, numero, type, date_enregistrement, date_debut, date_fin, date_cloture,
                montant, mandants_texte, note, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_mandat_id) DO UPDATE SET
                hektor_annonce_id = excluded.hektor_annonce_id,
                numero = excluded.numero,
                type = excluded.type,
                date_enregistrement = excluded.date_enregistrement,
                date_debut = excluded.date_debut,
                date_fin = excluded.date_fin,
                date_cloture = excluded.date_cloture,
                montant = excluded.montant,
                mandants_texte = excluded.mandants_texte,
                note = excluded.note,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                mandat_id,
                hektor_annonce_id,
                first_present(source.get("numero"), item.get("numero")),
                first_present(source.get("type"), item.get("type")),
                first_present(source.get("dateEnregistrement"), source.get("debut"), item.get("dateEnregistrement"), item.get("debut")),
                first_present(source.get("dateDebut"), source.get("debut"), item.get("dateDebut"), item.get("debut")),
                first_present(source.get("dateFin"), source.get("fin"), item.get("dateFin"), item.get("fin")),
                first_present(source.get("dateCloture"), source.get("cloture"), item.get("dateCloture"), item.get("cloture")),
                first_present(source.get("montant"), item.get("montant")),
                first_present(source.get("mandants"), item.get("mandants")),
                first_present(source.get("note"), item.get("note")),
                json_dumps(source),
                now_utc_iso(),
            ),
        )

    for mandat_id, relation_item in relation_items.items():
        if mandat_id in seen_ids:
            continue
        detail_item = detail_map.get(mandat_id, relation_item)
        source = dict(relation_item)
        source.update(detail_item)
        mandat_numero = str(first_present(source.get("numero"), relation_item.get("numero")) or "").strip()
        hektor_annonce_id = (
                normalized_id(source.get("idAnnonce"))
            or mandat_id_to_annonce.get(mandat_id)
            or mandat_numero_to_annonce.get(mandat_numero)
        )
        previous_row = conn.execute(
            "SELECT montant, hektor_annonce_id, numero, synced_at FROM hektor_mandat WHERE hektor_mandat_id = ?",
            (mandat_id,),
        ).fetchone()
        previous_montant = parse_numeric_value(previous_row["montant"]) if previous_row else None
        next_montant = parse_numeric_value(first_present(source.get("montant"), relation_item.get("montant")))
        if values_differ(previous_montant, next_montant):
            source_updated_at = (
                str(first_present(source.get("dateMaj"), source.get("datemaj"), source.get("dateEnregistrement"), source.get("debut")) or "").strip()
                or now_utc_iso()
            )
            event_annonce_id = hektor_annonce_id or (normalized_id(previous_row["hektor_annonce_id"]) if previous_row else None)
            event_numero = mandat_numero or (str(previous_row["numero"]).strip() if previous_row and previous_row["numero"] is not None else None)
            insert_price_change_event(
                conn,
                source_kind="mandat_montant",
                hektor_annonce_id=event_annonce_id,
                hektor_mandat_id=mandat_id,
                numero_mandat=event_numero,
                old_value=previous_montant,
                new_value=next_montant,
                source_updated_at=source_updated_at,
                raw_context={
                    "hektor_mandat_id": mandat_id,
                    "hektor_annonce_id": hektor_annonce_id,
                    "numero_mandat": mandat_numero,
                    "old_value": previous_montant,
                    "new_value": next_montant,
                    "type": first_present(source.get("type"), relation_item.get("type")),
                },
            )
        conn.execute(
            """
            INSERT INTO hektor_mandat(
                hektor_mandat_id, hektor_annonce_id, numero, type, date_enregistrement, date_debut, date_fin, date_cloture,
                montant, mandants_texte, note, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_mandat_id) DO UPDATE SET
                hektor_annonce_id = excluded.hektor_annonce_id,
                numero = excluded.numero,
                type = excluded.type,
                date_enregistrement = excluded.date_enregistrement,
                date_debut = excluded.date_debut,
                date_fin = excluded.date_fin,
                date_cloture = excluded.date_cloture,
                montant = excluded.montant,
                mandants_texte = excluded.mandants_texte,
                note = excluded.note,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                mandat_id,
                hektor_annonce_id,
                first_present(source.get("numero"), relation_item.get("numero")),
                first_present(source.get("type"), relation_item.get("type")),
                first_present(source.get("dateEnregistrement"), source.get("debut"), relation_item.get("dateEnregistrement"), relation_item.get("debut")),
                first_present(source.get("dateDebut"), source.get("debut"), relation_item.get("dateDebut"), relation_item.get("debut")),
                first_present(source.get("dateFin"), source.get("fin"), relation_item.get("dateFin"), relation_item.get("fin")),
                first_present(source.get("dateCloture"), source.get("cloture"), relation_item.get("dateCloture"), relation_item.get("cloture")),
                first_present(source.get("montant"), relation_item.get("montant")),
                first_present(source.get("mandants"), relation_item.get("mandants")),
                first_present(source.get("note"), relation_item.get("note")),
                json_dumps(source),
                now_utc_iso(),
            ),
        )
    conn.commit()


def upsert_contacts(conn: sqlite3.Connection) -> None:
    detail_map = latest_detail_map(fetch_latest_raw_payloads(conn, "contact_detail"))
    for endpoint_name in CONTACT_ENDPOINTS:
        for item in iter_listing_items(fetch_latest_raw_payloads(conn, endpoint_name)):
            source = get_detail_payload(detail_map.get(str(item.get("id") or "").strip(), item), "contact")
            coords = source.get("coordonnees") or {}
            localite = source.get("localite") or {}
            inner = localite.get("localite") if isinstance(localite, dict) else {}
            conn.execute(
                """
                INSERT INTO hektor_contact(
                    hektor_contact_id, hektor_agence_id, hektor_negociateur_id, civilite, nom, prenom, archive, date_enregistrement,
                    date_maj, email, portable, fixe, ville, code_postal, typologie_json, raw_json, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(hektor_contact_id) DO UPDATE SET
                    hektor_agence_id = excluded.hektor_agence_id,
                    hektor_negociateur_id = excluded.hektor_negociateur_id,
                    civilite = excluded.civilite,
                    nom = excluded.nom,
                    prenom = excluded.prenom,
                    archive = excluded.archive,
                    date_enregistrement = excluded.date_enregistrement,
                    date_maj = excluded.date_maj,
                    email = excluded.email,
                    portable = excluded.portable,
                    fixe = excluded.fixe,
                    ville = excluded.ville,
                    code_postal = excluded.code_postal,
                    typologie_json = excluded.typologie_json,
                    raw_json = excluded.raw_json,
                    synced_at = excluded.synced_at
                """,
                (
                    str(source.get("id") or item.get("id") or ""),
                    normalized_id(source.get("agence") or item.get("agence")),
                    normalized_id(source.get("id_negociateur") or item.get("id_negociateur")),
                    source.get("civilite") or item.get("civilite"),
                    source.get("nom") or item.get("nom"),
                    source.get("prenom") or item.get("prenom"),
                    source.get("archive") or item.get("archive"),
                    source.get("dateenr") or item.get("dateenr"),
                    source.get("datemaj") or item.get("datemaj"),
                    coords.get("email") if isinstance(coords, dict) else None,
                    coords.get("portable") if isinstance(coords, dict) else None,
                    coords.get("fixe") if isinstance(coords, dict) else None,
                    inner.get("ville") if isinstance(inner, dict) else None,
                    inner.get("code") if isinstance(inner, dict) else None,
                    json_dumps(source.get("typologie")),
                    json_dumps(source),
                    now_utc_iso(),
                ),
            )
    conn.commit()


def upsert_offres(conn: sqlite3.Connection) -> None:
    for item in iter_listing_items_for_endpoints(conn, OFFRE_ENDPOINTS):
        source = item
        annonce = source.get("annonce") or {}
        mandat = source.get("mandat") or {}
        offre_state, offre_event_date = derive_offre_state_and_event_date(source, item)
        conn.execute(
            """
            INSERT INTO hektor_offre(
                hektor_offre_id, hektor_annonce_id, hektor_mandat_id, hektor_acquereur_id, nom, prenom, raw_status, raw_date,
                offre_state, offre_event_date,
                raw_montant, acquereur_json, propositions_json, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_offre_id) DO UPDATE SET
                hektor_annonce_id = excluded.hektor_annonce_id,
                hektor_mandat_id = excluded.hektor_mandat_id,
                hektor_acquereur_id = excluded.hektor_acquereur_id,
                nom = excluded.nom,
                prenom = excluded.prenom,
                raw_status = excluded.raw_status,
                raw_date = excluded.raw_date,
                offre_state = excluded.offre_state,
                offre_event_date = excluded.offre_event_date,
                raw_montant = excluded.raw_montant,
                acquereur_json = excluded.acquereur_json,
                propositions_json = excluded.propositions_json,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                str(source.get("id") or item.get("id") or ""),
                normalized_id(source.get("id_annonce") or item.get("id_annonce") or (annonce.get("id") if isinstance(annonce, dict) else None)),
                normalized_id(source.get("id_mandat") or item.get("id_mandat") or (mandat.get("id") if isinstance(mandat, dict) else None)),
                normalized_id(source.get("id_acquereur") or item.get("id_acquereur")),
                source.get("nom") or item.get("nom"),
                source.get("prenom") or item.get("prenom"),
                source.get("status") or source.get("statut") or item.get("status") or item.get("statut"),
                source.get("date") or source.get("date_creation") or source.get("dateCreation") or item.get("date") or item.get("date_creation") or item.get("dateCreation"),
                offre_state,
                offre_event_date,
                source.get("montant") or source.get("prix") or item.get("montant") or item.get("prix"),
                json_dumps(source.get("acquereur")),
                json_dumps(source.get("propositions")),
                json_dumps(source),
                now_utc_iso(),
            ),
        )
    conn.commit()


def upsert_compromis(conn: sqlite3.Connection) -> None:
    for item in iter_listing_items_for_endpoints(conn, COMPROMIS_ENDPOINTS):
        source = item
        annonce = source.get("annonce") or {}
        mandat = source.get("mandat") or {}
        compromis_status = source.get("status") or item.get("status")
        compromis_state = derive_compromis_state(compromis_status)
        conn.execute(
            """
            INSERT INTO hektor_compromis(
                hektor_compromis_id, hektor_annonce_id, hektor_mandat_id, status, compromis_state, date_start, date_end, date_signature_acte,
                part_admin, sequestre, prix_net_vendeur, prix_publique, mandants_json, acquereurs_json, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_compromis_id) DO UPDATE SET
                hektor_annonce_id = excluded.hektor_annonce_id,
                hektor_mandat_id = excluded.hektor_mandat_id,
                status = excluded.status,
                compromis_state = excluded.compromis_state,
                date_start = excluded.date_start,
                date_end = excluded.date_end,
                date_signature_acte = excluded.date_signature_acte,
                part_admin = excluded.part_admin,
                sequestre = excluded.sequestre,
                prix_net_vendeur = excluded.prix_net_vendeur,
                prix_publique = excluded.prix_publique,
                mandants_json = excluded.mandants_json,
                acquereurs_json = excluded.acquereurs_json,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                str(source.get("id") or item.get("id") or ""),
                normalized_id(annonce.get("id")) if isinstance(annonce, dict) else None,
                normalized_id(mandat.get("id")) if isinstance(mandat, dict) else None,
                compromis_status,
                compromis_state,
                source.get("date_start") or source.get("dateStart") or item.get("date_start") or item.get("dateStart"),
                source.get("date_end") or source.get("dateEnd") or item.get("date_end") or item.get("dateEnd"),
                source.get("date_signature_acte") or source.get("dateSignatureActe") or item.get("date_signature_acte") or item.get("dateSignatureActe"),
                source.get("part_admin") or source.get("partAdmin") or item.get("part_admin") or item.get("partAdmin"),
                source.get("sequestre") or item.get("sequestre"),
                source.get("prix_net_vendeur") or source.get("prixNetVendeur") or item.get("prix_net_vendeur") or item.get("prixNetVendeur"),
                source.get("prix_publique") or source.get("prixPublique") or item.get("prix_publique") or item.get("prixPublique"),
                json_dumps(source.get("mandants")),
                json_dumps(source.get("acquereurs")),
                json_dumps(source),
                now_utc_iso(),
            ),
        )
    conn.commit()


def upsert_ventes(conn: sqlite3.Connection) -> None:
    for item in iter_listing_items_for_endpoints(conn, VENTE_ENDPOINTS):
        source = item
        annonce = source.get("annonce") or {}
        mandat = source.get("mandat") or {}
        conn.execute(
            """
            INSERT INTO hektor_vente(
                hektor_vente_id, hektor_annonce_id, hektor_mandat_id, date_vente, prix, honoraires, part_admin,
                commission_agence, mandants_json, acquereurs_json, notaires_json, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_vente_id) DO UPDATE SET
                hektor_annonce_id = excluded.hektor_annonce_id,
                hektor_mandat_id = excluded.hektor_mandat_id,
                date_vente = excluded.date_vente,
                prix = excluded.prix,
                honoraires = excluded.honoraires,
                part_admin = excluded.part_admin,
                commission_agence = excluded.commission_agence,
                mandants_json = excluded.mandants_json,
                acquereurs_json = excluded.acquereurs_json,
                notaires_json = excluded.notaires_json,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                str(source.get("id") or item.get("id") or ""),
                normalized_id(annonce.get("id")) if isinstance(annonce, dict) else None,
                normalized_id(mandat.get("id")) if isinstance(mandat, dict) else None,
                source.get("date") or item.get("date"),
                source.get("prix") or item.get("prix"),
                source.get("honoraires") or item.get("honoraires"),
                source.get("part_admin") or source.get("partAdmin") or item.get("part_admin") or item.get("partAdmin"),
                source.get("commission_agence") or source.get("commissionAgence") or item.get("commission_agence") or item.get("commissionAgence"),
                json_dumps(source.get("mandants")),
                json_dumps(source.get("acquereurs")),
                json_dumps(source.get("notaires")),
                json_dumps(source),
                now_utc_iso(),
            ),
        )
    conn.commit()


def upsert_broadcasts(conn: sqlite3.Connection) -> None:
    for item in iter_listing_items(fetch_latest_raw_payloads(conn, "list_broadcasts")):
        conn.execute(
            """
            INSERT INTO hektor_broadcast(hektor_broadcast_id, nom, count, listings_json, raw_json, synced_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_broadcast_id) DO UPDATE SET
                nom = excluded.nom,
                count = excluded.count,
                listings_json = excluded.listings_json,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                str(item.get("id") or ""),
                item.get("nom"),
                item.get("count"),
                json_dumps(item.get("listings")),
                json_dumps(item),
                now_utc_iso(),
            ),
        )
    conn.commit()


def derive_broadcast_state(export_status: Any) -> tuple[str, int, int]:
    status_text = str(export_status or "").strip()
    if not status_text:
        return "unknown", 0, 0
    if status_text.lower() == "exported":
        return "broadcasted", 1, 0
    return "error", 0, 1


def upsert_broadcast_portals(conn: sqlite3.Connection) -> None:
    for item in iter_listing_items(fetch_latest_raw_payloads(conn, "list_broadcasts")):
        broadcast_id = str(item.get("id") or "").strip()
        if not broadcast_id:
            continue
        conn.execute(
            """
            INSERT INTO hektor_broadcast_portal(
                hektor_broadcast_id, passerelle_key, listing_count, supports_read, supports_write, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_broadcast_id) DO UPDATE SET
                passerelle_key = excluded.passerelle_key,
                listing_count = excluded.listing_count,
                supports_read = excluded.supports_read,
                supports_write = excluded.supports_write,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                broadcast_id,
                str(item.get("nom") or "").strip(),
                item.get("count"),
                1,
                1,
                json_dumps(item),
                now_utc_iso(),
            ),
        )
    conn.commit()


def upsert_broadcast_listings(conn: sqlite3.Connection) -> None:
    for item in iter_listing_items(fetch_latest_raw_payloads(conn, "list_broadcasts")):
        broadcast_id = str(item.get("id") or "").strip()
        passerelle = item.get("nom")
        listings = item.get("listings") or []
        if not broadcast_id or not isinstance(listings, list):
            continue

        for listing in listings:
            if not isinstance(listing, dict):
                continue
            annonce_id = normalized_id(listing.get("annonce_id"))
            commercial = listing.get("commercial") or {}
            commercial_id = normalized_id(commercial.get("id")) if isinstance(commercial, dict) else None
            if not annonce_id:
                continue
            conn.execute(
                """
                INSERT INTO hektor_broadcast_listing(
                    hektor_broadcast_id, hektor_annonce_id, passerelle, commercial_id, commercial_type, commercial_nom,
                    commercial_prenom, export_status, raw_json, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(hektor_broadcast_id, hektor_annonce_id, commercial_id) DO UPDATE SET
                    passerelle = excluded.passerelle,
                    commercial_type = excluded.commercial_type,
                    commercial_nom = excluded.commercial_nom,
                    commercial_prenom = excluded.commercial_prenom,
                    export_status = excluded.export_status,
                    raw_json = excluded.raw_json,
                    synced_at = excluded.synced_at
                """,
                (
                    broadcast_id,
                    annonce_id,
                    passerelle,
                    commercial_id,
                    commercial.get("type") if isinstance(commercial, dict) else None,
                    commercial.get("nom") if isinstance(commercial, dict) else None,
                    commercial.get("prenom") if isinstance(commercial, dict) else None,
                    listing.get("export_status"),
                    json_dumps(listing),
                    now_utc_iso(),
                ),
            )
    conn.commit()


def upsert_broadcast_states(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM hektor_annonce_broadcast_state")
    rows = conn.execute(
        """
        SELECT
            hektor_broadcast_id,
            hektor_annonce_id,
            passerelle,
            commercial_id,
            commercial_type,
            commercial_nom,
            commercial_prenom,
            export_status,
            raw_json,
            synced_at
        FROM hektor_broadcast_listing
        """
    ).fetchall()
    for row in rows:
        commercial_key = str(row["commercial_id"] or "").strip()
        current_state, is_success, is_error = derive_broadcast_state(row["export_status"])
        conn.execute(
            """
            INSERT INTO hektor_annonce_broadcast_state(
                hektor_broadcast_id, hektor_annonce_id, commercial_key, passerelle_key, commercial_id,
                commercial_type, commercial_nom, commercial_prenom, current_state, export_status,
                is_success, is_error, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["hektor_broadcast_id"],
                row["hektor_annonce_id"],
                commercial_key,
                row["passerelle"],
                row["commercial_id"],
                row["commercial_type"],
                row["commercial_nom"],
                row["commercial_prenom"],
                current_state,
                row["export_status"],
                is_success,
                is_error,
                row["raw_json"],
                row["synced_at"],
            ),
        )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize raw Hektor payloads into source tables.")
    _ = parser.parse_args()

    settings = Settings.from_env()
    conn = connect_db(settings.db_path)
    init_db(conn)
    active_annonce_ids = active_annonce_ids_from_raw(conn)
    
    upsert_agences(conn)
    upsert_negos(conn)
    upsert_annonces(conn)
    upsert_annonce_details(conn)
    upsert_mandats(conn)
    upsert_contacts(conn)
    upsert_offres(conn)
    upsert_compromis(conn)
    upsert_ventes(conn)
    upsert_broadcasts(conn)
    upsert_broadcast_portals(conn)
    upsert_broadcast_listings(conn)
    upsert_broadcast_states(conn)
    prune_annonce_scope(conn, active_annonce_ids)

    print(f"Source tables normalized into {settings.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
