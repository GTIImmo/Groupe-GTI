from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"


@dataclass(frozen=True)
class QualityCheck:
    key: str
    label: str
    sql: str
    expectation: str


CHECKS: tuple[QualityCheck, ...] = (
    QualityCheck(
        key="vue_generale_total",
        label="Nombre de lignes vue generale",
        sql="SELECT COUNT(*) AS value FROM app_view_generale;",
        expectation="doit rester stable entre deux runs hors variation source",
    ),
    QualityCheck(
        key="demandes_total",
        label="Nombre de lignes demandes mandat diffusion",
        sql="SELECT COUNT(*) AS value FROM app_view_demandes_mandat_diffusion;",
        expectation="doit rester stable entre deux runs hors variation source",
    ),
    QualityCheck(
        key="missing_titles",
        label="Titres vides dans la vue generale",
        sql="""
SELECT COUNT(*) AS value
FROM app_view_generale
WHERE COALESCE(TRIM(titre_bien), '') = '';
""",
        expectation="0",
    ),
    QualityCheck(
        key="view_generale_without_dossier",
        label="Vue generale sans dossier source",
        sql="""
SELECT COUNT(*) AS value
FROM app_view_generale vg
LEFT JOIN app_dossier d ON d.id = vg.app_dossier_id
WHERE d.id IS NULL;
""",
        expectation="0",
    ),
    QualityCheck(
        key="demandes_without_view_generale",
        label="Demandes absentes de la vue generale",
        sql="""
SELECT COUNT(*) AS value
FROM app_view_demandes_mandat_diffusion dmd
LEFT JOIN app_view_generale vg ON vg.app_dossier_id = dmd.app_dossier_id
WHERE vg.app_dossier_id IS NULL;
""",
        expectation="0",
    ),
    QualityCheck(
        key="mandat_numero_id_collision",
        label="Cas no_mandat = mandat_id mais numero source different (indicateur borne)",
        sql="""
SELECT COUNT(*) AS value
FROM (
    SELECT
        src.hektor_annonce_id
    FROM hektor.case_dossier_source src
    INNER JOIN hektor.hektor_mandat m
        ON src.no_mandat = CAST(m.hektor_mandat_id AS TEXT)
    WHERE src.no_mandat GLOB '[0-9]*'
      AND CAST(m.numero AS TEXT) <> src.no_mandat
    LIMIT 5000
);
""",
        expectation="surveiller, indicateur borne a 5000 pour detecter les cas type 59449/44506",
    ),
)


DETAIL_QUERIES: dict[str, str] = {
    "sample_mandat_numero_id_collision": """
SELECT
    src.hektor_annonce_id,
    src.no_dossier,
    src.no_mandat,
    src.mandat_id,
    m.hektor_mandat_id,
    m.numero,
    m.hektor_annonce_id AS mandat_annonce_id
FROM hektor.case_dossier_source src
INNER JOIN hektor.hektor_mandat m
    ON src.no_mandat = CAST(m.hektor_mandat_id AS TEXT)
WHERE src.no_mandat GLOB '[0-9]*'
  AND CAST(m.numero AS TEXT) <> src.no_mandat
ORDER BY src.hektor_annonce_id
LIMIT 15;
""",
}


def run_checks() -> dict[str, object]:
    con = sqlite3.connect(PHASE2_DB)
    con.row_factory = sqlite3.Row
    try:
        con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        metrics: list[dict[str, object]] = []
        for check in CHECKS:
            value = con.execute(check.sql).fetchone()[0]
            metrics.append(
                {
                    "key": check.key,
                    "label": check.label,
                    "value": value,
                    "expectation": check.expectation,
                }
            )

        details: dict[str, list[dict[str, object]]] = {}
        for key, sql in DETAIL_QUERIES.items():
            rows = con.execute(sql).fetchall()
            details[key] = [dict(row) for row in rows]

        return {"metrics": metrics, "details": details}
    finally:
        con.close()
