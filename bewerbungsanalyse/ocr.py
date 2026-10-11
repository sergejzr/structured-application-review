from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .llm import LLMClient


CLEANUP_SYSTEM = """Bereinige OCR-extrahiertes Markdown aus Bewerbungsunterlagen.
Gib ausschließlich bereinigtes Markdown zurück. Bewahre alle Namen, Daten, Fakten,
Qualifikationen und Dokumentstrukturen. Erfinde nichts und fasse nicht zusammen.
Korrigiere nur OCR-Fehler, kaputte Zeilenumbrüche, offensichtliche Duplikate und Formatierung.
"""


def prepare_markdown(
    input_root: Path,
    output_root: Path,
    client: LLMClient,
    *,
    mineru_backend: str = "hybrid-auto-engine",
    mineru_method: str = "auto",
    ocr_backend: str = "auto",
    no_cleanup: bool = False,
    overwrite: bool = False,
) -> Path:
    """Erzeugt und behält raw sowie cleaned Markdown je Bewerber und Dokument."""
    output_root.mkdir(parents=True, exist_ok=True)
    files = sorted(
        path for path in input_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".md", ".txt"}
    )
    if not files:
        raise SystemExit(f"Keine PDF-, Markdown- oder Textdateien gefunden: {input_root}")

    for source in files:
        relative = source.relative_to(input_root)
        applicant = relative.parts[0] if len(relative.parts) > 1 else source.parent.name
        destination = output_root / applicant
        raw_path = destination / f"{source.stem}.md"
        cleaned_path = destination / f"{source.stem}.cleaned.md"
        destination.mkdir(parents=True, exist_ok=True)

        if source.suffix.lower() == ".pdf":
            if overwrite or not raw_path.exists() or not raw_path.stat().st_size:
                raw_path.write_text(
                    _pdf_markdown(source, mineru_backend, mineru_method, ocr_backend),
                    encoding="utf-8",
                )
        elif overwrite or not raw_path.exists() or not raw_path.stat().st_size:
            shutil.copyfile(source, raw_path)

        if overwrite or not cleaned_path.exists() or not cleaned_path.stat().st_size:
            raw = raw_path.read_text(encoding="utf-8", errors="replace")
            cleaned = raw if no_cleanup else client.complete_text(CLEANUP_SYSTEM, raw, max_tokens=12000)
            cleaned_path.write_text(cleaned + "\n", encoding="utf-8")

    return output_root


def _pdf_markdown(pdf: Path, backend: str, method: str, ocr_backend: str) -> str:
    if ocr_backend not in {"auto", "simple", "mineru"}:
        raise ValueError(f"Unbekanntes OCR-Backend: {ocr_backend}")
    use_mineru = ocr_backend == "mineru" or (ocr_backend == "auto" and _gpu_available() and shutil.which("mineru"))
    if use_mineru:
        return _mineru_markdown(pdf, backend, method)
    return _simple_pdf_markdown(pdf)


def _gpu_available() -> bool:
    return shutil.which("nvidia-smi") is not None and subprocess.run(
        ["nvidia-smi", "-L"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
    ).returncode == 0


def _mineru_markdown(pdf: Path, backend: str, method: str) -> str:
    with tempfile.TemporaryDirectory(prefix="bewerbungsanalyse_mineru_") as temp:
        try:
            subprocess.run(
                ["mineru", "-p", str(pdf), "-o", temp, "-m", method, "-b", backend],
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise RuntimeError(f"MinerU konnte PDF nicht verarbeiten: {pdf}") from exc
        candidates = sorted(Path(temp).rglob("*.md"), key=lambda path: path.stat().st_size, reverse=True)
        if not candidates:
            raise RuntimeError(f"MinerU hat kein Markdown erzeugt: {pdf}")
        return candidates[0].read_text(encoding="utf-8", errors="replace")


def _simple_pdf_markdown(pdf: Path) -> str:
    """CPU-only extraction: pdftotext first, then page-wise Tesseract OCR."""
    if shutil.which("pdftotext"):
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    return _tesseract_markdown(pdf)


def _tesseract_markdown(pdf: Path) -> str:
    """Letzter Fallback für gescannte PDFs in lokalen CPU-Testumgebungen."""
    with tempfile.TemporaryDirectory(prefix="bewerbungsanalyse_tesseract_") as temp:
        prefix = str(Path(temp) / "page")
        rendered = subprocess.run(
            ["pdftoppm", "-r", "200", "-png", str(pdf), prefix],
            check=False,
            capture_output=True,
            text=True,
        )
        if rendered.returncode != 0:
            raise RuntimeError(f"PDF konnte weder mit MinerU noch pdftoppm verarbeitet werden: {pdf}")
        pages = sorted(Path(temp).glob("page-*.png"))
        text_parts = []
        for number, page in enumerate(pages, 1):
            result = subprocess.run(
                ["tesseract", str(page), "stdout", "--psm", "3"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                text_parts.append(f"## Seite {number}\n\n{result.stdout.strip()}")
        if not text_parts:
            raise RuntimeError(f"PDF konnte nicht gelesen werden: {pdf}")
        return "\n\n".join(text_parts) + "\n"
