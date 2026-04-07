from __future__ import annotations

from pathlib import Path

try:
    from phase2.pipeline.domain_model import build_domain_inventory
    from phase2.rules.status_rules import (
        ALERT_TYPES,
        GLOBAL_STATUSES,
        SUB_STATUSES,
        VALIDATION_DIFFUSION_STATES,
        VISIBILITY_STATES,
        WORKFLOW_MANDAT_DIFFUSION,
    )
except ModuleNotFoundError:
    import sys

    here = Path(__file__).resolve().parents[2]
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    from phase2.pipeline.domain_model import build_domain_inventory
    from phase2.rules.status_rules import (
        ALERT_TYPES,
        GLOBAL_STATUSES,
        SUB_STATUSES,
        VALIDATION_DIFFUSION_STATES,
        VISIBILITY_STATES,
        WORKFLOW_MANDAT_DIFFUSION,
    )


def render_contract_markdown() -> str:
    inventory = build_domain_inventory()

    lines: list[str] = [
        "# Contrat courant de phase 2",
        "",
        "Document technique genere a partir du nouveau socle `pipeline/` et `rules/`.",
        "",
        "## Workflow central",
        "",
        f"- workflow principal courant : `{WORKFLOW_MANDAT_DIFFUSION}`",
        "",
        "## Entites couvertes",
        "",
    ]

    for entity in inventory["entities"]:
        lines.append(
            f"- `{entity['key']}` : {entity['label']} | source `{entity['source_table']}` | {entity['description']}"
        )

    lines.extend(
        [
            "",
            "## Vues de consommation",
            "",
        ]
    )

    for view in inventory["views"]:
        lines.append(
            f"- `{view['sql_name']}` : {view['label']} | {view['grain']} | {view['purpose']}"
        )

    lines.extend(
        [
            "",
            "## Etats metier de reference",
            "",
            f"- validation diffusion : {', '.join(f'`{value}`' for value in VALIDATION_DIFFUSION_STATES)}",
            f"- visibilite : {', '.join(f'`{value}`' for value in VISIBILITY_STATES)}",
            f"- statut global : {', '.join(f'`{value}`' for value in GLOBAL_STATUSES)}",
            f"- sous-statut : {', '.join(f'`{value}`' for value in SUB_STATUSES)}",
            f"- alertes : {', '.join(f'`{value}`' for value in ALERT_TYPES)}",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    phase2_root = Path(__file__).resolve().parents[1]
    output = phase2_root / "docs" / "CONTRAT_COURANT_PHASE2.md"
    output.write_text(render_contract_markdown(), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
