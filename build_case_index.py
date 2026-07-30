from __future__ import annotations

import argparse

from hektor_pipeline.common import Settings, connect_db, init_db, now_utc_iso


def build_case_dossier_source(conn, hektor_annonce_ids: list[str] | None = None) -> int:
    cleaned_ids = sorted({str(value or "").strip() for value in (hektor_annonce_ids or []) if str(value or "").strip()})
    target_where = ""
    target_params: list[str] = []
    if cleaned_ids:
        placeholders = ",".join("?" for _ in cleaned_ids)
        target_where = f"WHERE ids.hektor_annonce_id IN ({placeholders})"
        target_params = cleaned_ids
    query = """
    INSERT INTO case_dossier_source(
        hektor_annonce_id, no_dossier, no_mandat, hektor_agence_id, hektor_negociateur_id,
        negociateur_nom, negociateur_prenom, negociateur_email, negociateur_telephone, negociateur_portable,
        statut_name, annonce_source_status, archive, diffusable, valide, prix, case_kind,
        mandat_id, mandat_type, mandat_date_debut, mandat_date_fin, mandat_date_cloture,
        offre_id, compromis_id, vente_id, vente_date, updated_at
    )
    WITH annonce_ids AS (
        SELECT hektor_annonce_id FROM hektor_annonce
        UNION
        SELECT hektor_annonce_id FROM hektor_offre WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
        UNION
        SELECT hektor_annonce_id FROM hektor_compromis WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
        UNION
        SELECT hektor_annonce_id FROM hektor_vente WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
    ),
    annonce_candidates AS (
        SELECT
            a.hektor_annonce_id,
            a.no_dossier,
            a.no_mandat,
            a.hektor_agence_id,
            a.hektor_negociateur_id,
            a.archive,
            a.diffusable,
            a.valide,
            a.prix,
            0 AS source_rank,
            a.synced_at AS event_date
        FROM hektor_annonce a
        UNION ALL
        SELECT
            o.hektor_annonce_id,
            json_extract(o.raw_json, '$.annonce.NO_DOSSIER'),
            json_extract(o.raw_json, '$.annonce.NO_MANDAT'),
            json_extract(o.raw_json, '$.annonce.agence'),
            json_extract(o.raw_json, '$.annonce.NEGOCIATEUR'),
            json_extract(o.raw_json, '$.annonce.archive'),
            json_extract(o.raw_json, '$.annonce.diffusable'),
            json_extract(o.raw_json, '$.annonce.valide'),
            COALESCE(json_extract(o.raw_json, '$.annonce.prix'), o.raw_montant),
            3 AS source_rank,
            COALESCE(o.raw_date, o.synced_at) AS event_date
        FROM hektor_offre o
        WHERE NULLIF(TRIM(o.hektor_annonce_id), '') IS NOT NULL
        UNION ALL
        SELECT
            c.hektor_annonce_id,
            json_extract(c.raw_json, '$.annonce.NO_DOSSIER'),
            json_extract(c.raw_json, '$.annonce.NO_MANDAT'),
            json_extract(c.raw_json, '$.annonce.agence'),
            json_extract(c.raw_json, '$.annonce.NEGOCIATEUR'),
            json_extract(c.raw_json, '$.annonce.archive'),
            json_extract(c.raw_json, '$.annonce.diffusable'),
            json_extract(c.raw_json, '$.annonce.valide'),
            COALESCE(json_extract(c.raw_json, '$.annonce.prix'), c.prix_publique),
            2 AS source_rank,
            COALESCE(c.date_start, c.synced_at) AS event_date
        FROM hektor_compromis c
        WHERE NULLIF(TRIM(c.hektor_annonce_id), '') IS NOT NULL
        UNION ALL
        SELECT
            v.hektor_annonce_id,
            json_extract(v.raw_json, '$.annonce.NO_DOSSIER'),
            json_extract(v.raw_json, '$.annonce.NO_MANDAT'),
            json_extract(v.raw_json, '$.annonce.agence'),
            json_extract(v.raw_json, '$.annonce.NEGOCIATEUR'),
            json_extract(v.raw_json, '$.annonce.archive'),
            json_extract(v.raw_json, '$.annonce.diffusable'),
            json_extract(v.raw_json, '$.annonce.valide'),
            COALESCE(json_extract(v.raw_json, '$.annonce.prix'), v.prix),
            1 AS source_rank,
            COALESCE(v.date_vente, v.synced_at) AS event_date
        FROM hektor_vente v
        WHERE NULLIF(TRIM(v.hektor_annonce_id), '') IS NOT NULL
    ),
    annonce_ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY hektor_annonce_id
                   ORDER BY source_rank, COALESCE(event_date, '') DESC
               ) AS rn
        FROM annonce_candidates
    ),
    mandat_ranked AS (
        SELECT *,
               -- hektor_annonce_id vaut '' et non NULL depuis que la colonne fait
               -- partie de la cle primaire (SQLite y accepterait NULL, ce qui
               -- desactiverait toute detection de conflit). Les tests doivent donc
               -- porter sur la chaine vide : sans NULLIF, tous les mandats orphelins
               -- tomberaient dans une meme partition '' et un seul survivrait.
               ROW_NUMBER() OVER (
                   PARTITION BY COALESCE(NULLIF(hektor_annonce_id, ''), numero)
                   ORDER BY
                       CASE WHEN COALESCE(hektor_annonce_id, '') <> '' THEN 0 ELSE 1 END,
                       COALESCE(date_debut, date_enregistrement, synced_at) DESC
               ) AS rn
        FROM hektor_mandat
    ),
    offre_ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY hektor_annonce_id
                   ORDER BY
                       CASE offre_state
                           WHEN 'accepted' THEN 0
                           WHEN 'proposed' THEN 1
                           ELSE 2
                       END,
                       COALESCE(offre_event_date, raw_date, synced_at) DESC
               ) AS rn
        FROM hektor_offre
        WHERE hektor_annonce_id IS NOT NULL
    ),
    compromis_ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY hektor_annonce_id
                   ORDER BY
                       CASE compromis_state
                           WHEN 'active' THEN 0
                           WHEN 'cancelled' THEN 1
                           ELSE 2
                       END,
                       COALESCE(date_start, synced_at) DESC
               ) AS rn
        FROM hektor_compromis
        WHERE hektor_annonce_id IS NOT NULL
    ),
    vente_ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY hektor_annonce_id
                   ORDER BY COALESCE(date_vente, synced_at) DESC
               ) AS rn
        FROM hektor_vente
        WHERE hektor_annonce_id IS NOT NULL
    )
    SELECT
        ids.hektor_annonce_id,
        a.no_dossier,
        -- Cle de cycle du registre : NO_MANDAT de l'annonce Hektor est en retard sur le mandat
        -- le plus recent ; on prefere le numero du cycle courant pour que le registre range la
        -- donnee vivante sous le bon numero (mono-mandat : mf.numero == a.no_mandat => no-op).
        COALESCE(NULLIF(mf.numero, ''), a.no_mandat) AS no_mandat,
        a.hektor_agence_id,
        a.hektor_negociateur_id,
        n.nom,
        n.prenom,
        n.email,
        n.telephone,
        n.portable,
        d.statut_name,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM hektor_annonce ha
                WHERE ha.hektor_annonce_id = ids.hektor_annonce_id
            ) THEN 'present'
            ELSE 'missing'
        END AS annonce_source_status,
        a.archive,
        a.diffusable,
        a.valide,
        a.prix,
        CASE
            WHEN NOT EXISTS (
                SELECT 1
                FROM hektor_annonce ha
                WHERE ha.hektor_annonce_id = ids.hektor_annonce_id
            )
            AND COALESCE(
                json_extract(o.raw_json, '$.annonce.idtype'),
                json_extract(c.raw_json, '$.annonce.idtype'),
                json_extract(v.raw_json, '$.annonce.idtype')
            ) = '23'
            AND COALESCE(
                json_extract(o.raw_json, '$.annonce.offredem'),
                json_extract(c.raw_json, '$.annonce.offredem'),
                json_extract(v.raw_json, '$.annonce.offredem')
            ) = '10'
            THEN 'transaction_commerce'
            ELSE NULL
        END AS case_kind,
        -- Cycle courant : l'identite du mandat suit le CYCLE le plus recent (mf), identifie
        -- par son NUMERO (pas par l'id interne, que Hektor recycle). On ne bascule que sur un
        -- vrai re-mandatement (numero de l'affaire different du numero courant) ; sinon on garde
        -- l'expression baseline a l'identique => mono-mandat et doublons d'id sont inchanges.
        CASE WHEN mf.numero IS NOT NULL AND md.numero IS NOT NULL AND md.numero <> mf.numero
             THEN mf.hektor_mandat_id
             ELSE COALESCE(
            NULLIF(md.hektor_mandat_id, ''),
            NULLIF(md.hektor_mandat_id, '0'),
            mf.hektor_mandat_id,
            NULLIF(c.hektor_mandat_id, ''),
            NULLIF(c.hektor_mandat_id, '0'),
            NULLIF(o.hektor_mandat_id, ''),
            NULLIF(o.hektor_mandat_id, '0'),
            NULLIF(v.hektor_mandat_id, ''),
            NULLIF(v.hektor_mandat_id, '0')
        ) END AS mandat_id,
        CASE WHEN mf.numero IS NOT NULL AND md.numero IS NOT NULL AND md.numero <> mf.numero
             THEN mf.type
             ELSE COALESCE(
            md.type,
            mf.type,
            json_extract(c.raw_json, '$.mandat.type'),
            json_extract(o.raw_json, '$.mandat.type'),
            json_extract(v.raw_json, '$.mandat.type')
        ) END AS mandat_type,
        CASE WHEN mf.numero IS NOT NULL AND md.numero IS NOT NULL AND md.numero <> mf.numero
             THEN mf.date_debut
             ELSE COALESCE(
            md.date_debut,
            mf.date_debut,
            json_extract(c.raw_json, '$.mandat.debut'),
            json_extract(o.raw_json, '$.mandat.debut'),
            json_extract(v.raw_json, '$.mandat.debut')
        ) END AS mandat_date_debut,
        CASE WHEN mf.numero IS NOT NULL AND md.numero IS NOT NULL AND md.numero <> mf.numero
             THEN mf.date_fin
             ELSE COALESCE(
            md.date_fin,
            mf.date_fin,
            json_extract(c.raw_json, '$.mandat.fin'),
            json_extract(o.raw_json, '$.mandat.fin'),
            json_extract(v.raw_json, '$.mandat.fin')
        ) END AS mandat_date_fin,
        CASE WHEN mf.numero IS NOT NULL AND md.numero IS NOT NULL AND md.numero <> mf.numero
             THEN mf.date_cloture
             ELSE COALESCE(
            md.date_cloture,
            mf.date_cloture,
            json_extract(c.raw_json, '$.mandat.cloture'),
            json_extract(o.raw_json, '$.mandat.cloture'),
            json_extract(v.raw_json, '$.mandat.cloture')
        ) END AS mandat_date_cloture,
        -- Affaire scopee au cycle courant : on ne retire l'offre / le compromis / la vente que
        -- si SON mandat (mo/mc/mv) porte un NUMERO different du numero courant (ancien cycle).
        CASE WHEN mf.numero IS NOT NULL AND mo.numero IS NOT NULL AND mo.numero <> mf.numero THEN NULL ELSE o.hektor_offre_id END AS hektor_offre_id,
        CASE WHEN mf.numero IS NOT NULL AND mc.numero IS NOT NULL AND mc.numero <> mf.numero THEN NULL ELSE c.hektor_compromis_id END AS hektor_compromis_id,
        CASE WHEN mf.numero IS NOT NULL AND mv.numero IS NOT NULL AND mv.numero <> mf.numero THEN NULL ELSE v.hektor_vente_id END AS hektor_vente_id,
        CASE WHEN mf.numero IS NOT NULL AND mv.numero IS NOT NULL AND mv.numero <> mf.numero THEN NULL ELSE v.date_vente END AS date_vente,
        ?
    FROM annonce_ids ids
    LEFT JOIN annonce_ranked a ON a.hektor_annonce_id = ids.hektor_annonce_id AND a.rn = 1
    LEFT JOIN hektor_negociateur n ON n.hektor_negociateur_id = a.hektor_negociateur_id
    LEFT JOIN hektor_annonce_detail d ON d.hektor_annonce_id = ids.hektor_annonce_id
    LEFT JOIN offre_ranked o ON o.hektor_annonce_id = ids.hektor_annonce_id AND o.rn = 1
    LEFT JOIN compromis_ranked c ON c.hektor_annonce_id = ids.hektor_annonce_id AND c.rn = 1
    LEFT JOIN vente_ranked v ON v.hektor_annonce_id = ids.hektor_annonce_id AND v.rn = 1
    LEFT JOIN hektor_mandat md
        ON md.hektor_mandat_id = COALESCE(
            NULLIF(c.hektor_mandat_id, ''),
            NULLIF(c.hektor_mandat_id, '0'),
            NULLIF(o.hektor_mandat_id, ''),
            NULLIF(o.hektor_mandat_id, '0'),
            NULLIF(v.hektor_mandat_id, ''),
            NULLIF(v.hektor_mandat_id, '0')
        )
        -- Un identifiant de mandat n'est unique qu'au sein d'une annonce : sans cette
        -- condition, la jointure pourrait ramener le mandat d'une autre annonce.
        AND CAST(md.hektor_annonce_id AS TEXT) = CAST(ids.hektor_annonce_id AS TEXT)
    -- Mandat propre a chaque affaire (offre/compromis/vente) pour lire SON numero de cycle.
    -- Qualifie par l'annonce (meme regle de cle que md), car l'id de mandat n'est unique
    -- qu'au sein d'une annonce.
    LEFT JOIN hektor_mandat mo
        ON mo.hektor_mandat_id = COALESCE(NULLIF(o.hektor_mandat_id, ''), NULLIF(o.hektor_mandat_id, '0'))
        AND CAST(mo.hektor_annonce_id AS TEXT) = CAST(ids.hektor_annonce_id AS TEXT)
    LEFT JOIN hektor_mandat mc
        ON mc.hektor_mandat_id = COALESCE(NULLIF(c.hektor_mandat_id, ''), NULLIF(c.hektor_mandat_id, '0'))
        AND CAST(mc.hektor_annonce_id AS TEXT) = CAST(ids.hektor_annonce_id AS TEXT)
    LEFT JOIN hektor_mandat mv
        ON mv.hektor_mandat_id = COALESCE(NULLIF(v.hektor_mandat_id, ''), NULLIF(v.hektor_mandat_id, '0'))
        AND CAST(mv.hektor_annonce_id AS TEXT) = CAST(ids.hektor_annonce_id AS TEXT)
    LEFT JOIN mandat_ranked mf
        ON (
            mf.hektor_annonce_id = ids.hektor_annonce_id
            OR (
                -- Repli : rattacher par numero un mandat dont l'annonce n'a pas ete
                -- resolue. Le test etait 'IS NULL', devenu toujours faux depuis que
                -- la colonne est NOT NULL DEFAULT ''.
                COALESCE(mf.hektor_annonce_id, '') = ''
                AND mf.numero = a.no_mandat
            )
        )
       AND mf.rn = 1
    __TARGET_WHERE__
    """.replace("__TARGET_WHERE__", target_where)

    if cleaned_ids:
        placeholders = ",".join("?" for _ in cleaned_ids)
        conn.execute(f"DELETE FROM case_dossier_source WHERE hektor_annonce_id IN ({placeholders})", cleaned_ids)
    else:
        conn.execute("DELETE FROM case_dossier_source")
    conn.execute(query, (now_utc_iso(), *target_params))
    conn.commit()

    if cleaned_ids:
        placeholders = ",".join("?" for _ in cleaned_ids)
        count = conn.execute(
            f"SELECT COUNT(*) FROM case_dossier_source WHERE hektor_annonce_id IN ({placeholders})",
            cleaned_ids,
        ).fetchone()[0]
    else:
        count = conn.execute("SELECT COUNT(*) FROM case_dossier_source").fetchone()[0]
    return int(count)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the first consolidated dossier index.")
    parser.add_argument("--id-annonce", action="append", default=[], help="Limit rebuild to one Hektor annonce id. Can be repeated.")
    args = parser.parse_args()

    settings = Settings.from_env()
    conn = connect_db(settings.db_path)
    init_db(conn)
    count = build_case_dossier_source(conn, args.id_annonce)
    print(f"Built case_dossier_source with {count} rows in {settings.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
