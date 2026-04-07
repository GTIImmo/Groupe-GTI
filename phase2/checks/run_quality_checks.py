from __future__ import annotations

import json
from pathlib import Path

try:
    from phase2.checks.quality_checks import run_checks
except ModuleNotFoundError:
    import sys

    ROOT_DIR = Path(__file__).resolve().parents[2]
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from phase2.checks.quality_checks import run_checks


def render_markdown(report: dict[str, object]) -> str:
    metrics = report["metrics"]
    details = report["details"]

    lines: list[str] = [
        "# Rapport qualite phase 2",
        "",
        "Controles automatises de coherence sur `phase2.sqlite`.",
        "",
        "## Metriques",
        "",
    ]

    for item in metrics:
        lines.append(
            f"- `{item['key']}` : {item['value']} | attente : {item['expectation']}"
        )

    lines.extend(
        [
            "",
            "## Echantillons",
            "",
        ]
    )

    for key, rows in details.items():
        lines.append(f"### `{key}`")
        if not rows:
            lines.append("")
            lines.append("- aucun resultat")
            lines.append("")
            continue
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(rows, ensure_ascii=True, indent=2))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    report = run_checks()
    output = Path(__file__).resolve().parent.parent / "docs" / "RAPPORT_QUALITE_PHASE2.md"
    output.write_text(render_markdown(report), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
