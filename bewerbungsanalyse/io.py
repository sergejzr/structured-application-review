from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Applicant, FinalProfile


def load_applicants(root: Path) -> list[Applicant]:
    applicants: list[Applicant] = []
    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        cleaned = sorted(directory.rglob("*.cleaned.md"))
        cleaned_stems = {path.name.removesuffix(".cleaned.md") for path in cleaned}
        files = cleaned + sorted(
            path for path in directory.rglob("*.md")
            if not path.name.endswith(".cleaned.md") and path.stem not in cleaned_stems
        )
        if not files:
            continue
        applicants.append(
            Applicant(
                applicant_id=directory.name,
                text="\n\n--- SOURCE: ---\n\n".join(path.read_text(encoding="utf-8") for path in files),
                sources=[str(path.relative_to(root)) for path in files],
            )
        )
    return applicants


def write_outputs(output: Path, schema: list[dict], profiles: list[FinalProfile]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "schema.json").write_text(json.dumps({"attributes": schema}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "profiles.json").write_text(json.dumps([p.__dict__ for p in profiles], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    names = [item["name"] for item in schema]
    columns = ["Candidate", "Summary", *names, "Zusätzliche/Überraschungsattribute", "Unstimmigkeiten/Auffälligkeiten"]
    rows = []
    for profile in profiles:
        row = {"Candidate": profile.applicant_id, "Summary": profile.summary}
        for name in names:
            item = profile.attributes.get(name, {})
            row[name] = item.get("value", "") if isinstance(item, dict) else str(item)
        row["Zusätzliche/Überraschungsattribute"] = "; ".join(
            f"{item.get('name', '')}: {item.get('value', '')}" for item in profile.additional_attributes
        )
        row["Unstimmigkeiten/Auffälligkeiten"] = "; ".join(
            f"{item.get('name', '')}: {item.get('description', '')}"
            for item in profile.inconsistencies
        )
        rows.append(row)
    with (output / "comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    escape = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
    markdown = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    markdown.extend("| " + " | ".join(escape(row[column]) for column in columns) + " |" for row in rows)
    (output / "comparison.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
