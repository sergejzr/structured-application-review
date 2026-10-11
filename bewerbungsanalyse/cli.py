from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io import load_applicants, write_outputs
from .llm import LLMClient
from .ocr import prepare_markdown
from .pipeline import ApplicationPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Zweistufige Bewerbungsanalyse")
    parser.add_argument("--input", type=Path, default=Path("input"), help="Gemeinsamer Input-Ordner")
    parser.add_argument("--applications", type=Path, help="Überschreibt input/applications_pdf")
    parser.add_argument("--job-description", type=Path, help="Überschreibt input/stellenbeschreibungen/stellenbeschreibung.md")
    parser.add_argument("--desired-attributes", type=Path, help="Überschreibt input/extra_attributes.txt")
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--no-cleanup", action="store_true", help="OCR-Markdown nicht per LLM bereinigen")
    parser.add_argument("--overwrite", action="store_true", help="Vorhandene Zwischen- und Ergebnisdateien überschreiben")
    parser.add_argument("--mineru-backend", default="hybrid-auto-engine")
    parser.add_argument("--mineru-method", choices=["auto", "txt", "ocr"], default="auto")
    parser.add_argument("--ocr-backend", choices=["auto", "simple", "mineru"], default="auto",
                        help="auto: MinerU auf GPU, sonst pdftotext/Tesseract; simple: CPU; mineru: GPU")
    args = parser.parse_args()

    applications = args.applications or args.input / "applications_pdf"
    job_description = args.job_description or args.input / "stellenbeschreibungen" / "stellenbeschreibung.md"
    desired_attributes = args.desired_attributes or args.input / "extra_attributes.txt"
    for path, label in ((applications, "Bewerbungsordner"), (job_description, "Stellenbeschreibung"), (desired_attributes, "Wunschattribute")):
        if not path.exists():
            raise SystemExit(f"{label} nicht gefunden: {path}")

    client = LLMClient()
    markdown_root = args.output / "markdown"
    prepare_markdown(
        applications,
        markdown_root,
        client,
        mineru_backend=args.mineru_backend,
        mineru_method=args.mineru_method,
        ocr_backend=args.ocr_backend,
        no_cleanup=args.no_cleanup,
        overwrite=args.overwrite,
    )
    applicants = load_applicants(markdown_root)
    if not applicants:
        raise SystemExit("Keine Markdown-Dokumente gefunden. OCR-Aufbereitung muss vorher erfolgen.")
    job = job_description.read_text(encoding="utf-8")
    desired = [line.strip() for line in desired_attributes.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]

    pipeline = ApplicationPipeline(client)
    raw_profiles = []
    for applicant in applicants:
        print(f"Erste Extraktion: {applicant.applicant_id}", flush=True)
        raw_profiles.append(pipeline.first_pass(applicant))
    (args.output / "raw_profiles.json").parent.mkdir(parents=True, exist_ok=True)
    (args.output / "raw_profiles.json").write_text(json.dumps([p.__dict__ for p in raw_profiles], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Gemeinsames Schema erzeugen", flush=True)
    schema = pipeline.build_schema(job, desired)
    print("Zweite Extraktion", flush=True)
    profiles = [pipeline.final_pass(applicant, schema) for applicant in applicants]
    write_outputs(args.output, [item.__dict__ for item in schema], profiles)
    print(f"Fertig: {len(profiles)} Bewerbungen, {len(schema)} Attribute in {args.output}")


if __name__ == "__main__":
    main()
