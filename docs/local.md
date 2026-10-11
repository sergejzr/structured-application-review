# Local CPU mode

Local mode is intended for development, small test sets, and text-based or
moderately sized scanned PDFs.

Install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[local]'
```

Install the system tools used by the simple backend:

```bash
# Debian/Ubuntu
sudo apt install poppler-utils tesseract-ocr
```

Run with automatic backend selection:

```bash
bewerbungsanalyse --input input --output output --ocr-backend auto
```

`auto` selects MinerU only when a working NVIDIA GPU is visible. Otherwise it
uses `pdftotext` and falls back to Tesseract for scanned pages. Use
`--ocr-backend simple` to force CPU processing.
