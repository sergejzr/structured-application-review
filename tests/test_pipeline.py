from pathlib import Path

from bewerbungsanalyse.io import write_outputs
from bewerbungsanalyse.models import Applicant, SchemaAttribute
from bewerbungsanalyse.pipeline import ApplicationPipeline


class FakeClient:
    def complete_json(self, system, user, max_tokens=12000):
        if '"attributes"' in system and "Stellenausschreibung" in system:
            assert "raw_applicant_attributes" not in user
            return {"attributes": [{"name": "Forschungsdatenmanagement", "source": "job", "priority": "must"}]}
        return {
            "summary": "Testprofil",
            "attributes": {"Forschungsdatenmanagement": {"value": "ja", "status": "documented", "evidence": "CV"}},
            "additional_attributes": [{"name": "Unerwartete Erfahrung", "value": "...", "evidence": "CV"}],
            "inconsistencies": [{"name": "Titel ohne Nachweis", "description": "Prüfen", "evidence": "CV", "severity": "low"}],
            "questions": [],
        }


def test_schema_uses_job_and_desired_only():
    pipeline = ApplicationPipeline(FakeClient())
    schema = pipeline.build_schema("JOB", ["Wunsch"])
    assert [item.name for item in schema] == ["Forschungsdatenmanagement"]


def test_outputs_have_separate_additional_and_inconsistency_columns(tmp_path: Path):
    profile = ApplicationPipeline(FakeClient()).final_pass(
        Applicant("A", "Text", ["a.md"]),
        [SchemaAttribute("Forschungsdatenmanagement")],
    )
    write_outputs(tmp_path, [{"name": "Forschungsdatenmanagement"}], [profile])
    header = (tmp_path / "comparison.md").read_text(encoding="utf-8").splitlines()[0]
    assert "Zusätzliche/Überraschungsattribute" in header
    assert "Unstimmigkeiten/Auffälligkeiten" in header
