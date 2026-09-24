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
        key="registre_couche_desaccord",
        label="Fiches que le registre a numerotees mais que la couche range sous Hektor",
        sql="""
SELECT COUNT(*) AS value
FROM app_contact_current c
JOIN app_contact r ON r.hektor_target_id = c.hektor_contact_id
WHERE CAST(c.hektor_contact_id AS INTEGER) < 10000000
  AND CAST(r.hektor_contact_id AS INTEGER) >= 10000000
  -- L4-c-bis 24/09 : un contact NEUF passe UNE nuit sous son numero Hektor (le
  -- build tourne avant le registre) : c'est normal, et le registre le reconnait
  -- sous ses deux numeros. Ce qui est anormal, c'est d'y RESTER.
  AND r.created_at < datetime('now', '-36 hours');
""",
        expectation=(
            "DOIT RESTER A ZERO. Le matin du 24/09, ce compte valait 294 179 et "
            "personne ne le voyait : le registre avait numerote ces fiches, la couche "
            "les rangeait encore sous leur numero de Hektor, et le run suivant leur a "
            "donne une SECONDE identite -- 650 353 lignes au lieu de 356 166, en une "
            "nuit, sans une erreur. Ce n'etait pas une faute de code mais un DESACCORD "
            "entre deux cotes corrects pris separement. Toute valeur > 0 annonce le "
            "meme degat au prochain run."
        ),
    ),
    QualityCheck(
        key="registre_identite_mal_rangee",
        label="Contacts numerotes dont l'identite n'est pas dans la colonne d'identite",
        sql="""
SELECT COUNT(*) AS value
FROM app_contact
WHERE CAST(hektor_contact_id AS INTEGER) < 10000000
  AND app_contact_id >= 10000000;
""",
        expectation=(
            "DOIT RESTER A ZERO. L4-c-bis, 24/09 : l'INSERT des contacts neufs rangeait "
            "leur numero de Hektor dans hektor_contact_id -- colonne qui porte "
            "l'IDENTITE depuis la bascule -- et l'identite a cote. Le build ne les "
            "traduisait jamais : 23 contacts restes sous leur numero Hektor, et le "
            "controle d'accord ne les voyait pas (il ne cherchait que les doublons). "
            "registre_contacts.py repare ces lignes a chaque nuit ; une valeur > 0 "
            "apres son passage veut dire que la reparation n'a pas pu se faire."
        ),
    ),
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
