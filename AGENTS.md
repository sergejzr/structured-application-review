# Agent instructions

## Project purpose

`structured-application-review` analyzes application documents in a reproducible,
evidence-based way. It produces comparable applicant profiles and tables without
turning undocumented information into facts.

## Data flow

1. Read PDFs from `input/applications_pdf/<applicant>/`.
2. Preserve raw OCR Markdown and create `*.cleaned.md` under `output/markdown/`.
3. Extract a schema-free raw profile from each applicant.
4. Build the comparison schema exclusively from the job description and desired attributes.
5. Re-extract every applicant using that fixed schema.
6. Store out-of-schema information in `additional_attributes`.
7. Store contradictions, missing evidence, unclear dates/titles, and other review hints in `inconsistencies`.
8. Render JSON, CSV, and Markdown outputs.

The schema must not be expanded with candidate-specific facts. Candidate-specific
facts belong in evidence or in the additional-attributes collection.

## Input layout and command

The default input layout is:

```text
input/
├── applications_pdf/<applicant>/*.pdf
├── stellenbeschreibungen/stellenbeschreibung.md
└── extra_attributes.txt
```

Run locally with:

```bash
bewerbungsanalyse --input input --output output --ocr-backend auto
```

Use `--ocr-backend simple` for CPU-only local extraction. Use `--ocr-backend mineru`
on a configured GPU/HPC node. `auto` selects MinerU only when an NVIDIA GPU is visible;
otherwise it uses `pdftotext` and Tesseract.

The LLM client uses an OpenAI-compatible OpenWebUI endpoint configured only through:
`OPENWEBUI_API_BASE`, `OPENWEBUI_API_KEY`, and `OPENWEBUI_MODEL`.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Run `python3 -m compileall -q bewerbungsanalyse tests` for a dependency-light syntax check.
Use synthetic fixtures only. Do not add real applications, generated profiles, OCR output,
API keys, tokens, or local model caches to Git.

## Change guidelines

- Keep local and HPC OCR behind the same interface.
- Preserve intermediate Markdown outputs; downstream stages must be restartable.
- Keep evidence and source references with extracted values.
- Treat `not_documented` and `unclear` as distinct from negative evaluation.
- Keep inconsistency findings neutral and evidence-backed; do not infer misconduct or suitability.
- Update README/docs and tests when changing the pipeline or CLI.
- Check `git status` and scan for secrets before committing or pushing.

## Privacy and safety

Application documents are sensitive personal data. Before using a remote LLM, verify that
the endpoint is approved for the documents and understand retention. Never place credentials
in source code, shell scripts, example configs, issues, or documentation.
