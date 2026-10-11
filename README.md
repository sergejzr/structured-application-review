# Bewerbungsanalyse

Dieses Paket erzeugt aus Bewerbungsunterlagen eine einheitliche Vergleichstabelle.

## Ablauf

1. Alle Bewerbungen werden zunächst ohne Schema analysiert und als Rohprofile gespeichert.
2. Das verbindliche Vergleichsschema wird ausschließlich aus Stellenausschreibung und Wunschattributen erzeugt.
3. Alle Bewerbungen werden mit diesem festen Schema erneut extrahiert.
4. Alles, was in keine Schema-Spalte passt, wird je Bewerbung in einer einzigen Liste bzw. Tabellenspalte für zusätzliche/überraschende Attribute gesammelt.
5. Widersprüche, fehlende Nachweise, unklare Angaben oder mögliche zeitliche Probleme werden separat als neutrale Unstimmigkeiten/Auffälligkeiten mit Evidenz und Schweregrad ausgegeben.

## Eingaben

```text
applications/
  bewerber-001/*.md
  bewerber-002/*.md
job.md
desired_attributes.txt
```

Die Aufbereitung wird automatisch ausgeführt. Unter `output/markdown/` bleiben sowohl das rohe OCR-Markdown als auch die bereinigte Datei `*.cleaned.md` als nachvollziehbare Zwischenergebnisse erhalten.

Das Paket unterstützt zwei Betriebsarten: lokal auf CPU mit `pdftotext` und Tesseract sowie auf einem HPC-GPU-Knoten mit MinerU. `--ocr-backend auto` wählt MinerU nur bei sichtbarer NVIDIA-GPU, sonst die einfache lokale OCR. Details stehen in [docs/local.md](docs/local.md) und [docs/hpc.md](docs/hpc.md).

## Ausführung

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

export OPENWEBUI_API_BASE='https://.../api'
export OPENWEBUI_API_KEY='...'
export OPENWEBUI_MODEL='...'

bewerbungsanalyse --input input --output output
```

Standardstruktur:

```text
input/
├── applications_pdf/<bewerber>/*.pdf
├── stellenbeschreibungen/stellenbeschreibung.md
└── extra_attributes.txt
```

Die drei Pfade können bei Bedarf weiterhin mit `--applications`,
`--job-description` und `--desired-attributes` einzeln überschrieben werden.

Ausgabe: `raw_profiles.json`, `schema.json`, `profiles.json`, `comparison.csv` und `comparison.md` sowie die OCR-/Bereinigungsergebnisse unter `output/markdown/`.
