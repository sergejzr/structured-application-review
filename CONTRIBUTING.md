# Contributing

Install the development environment with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

Do not add real applications or generated candidate data to commits. Use
synthetic fixtures for tests.
