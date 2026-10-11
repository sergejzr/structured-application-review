from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .llm import LLMClient
from .models import Applicant, FinalProfile, RawProfile, SchemaAttribute


RAW_SYSTEM = """Du analysierst Bewerbungsunterlagen.
Extrahiere in dieser ersten Runde alle tatsächlich belegten fachlichen, beruflichen,
methodischen und sonstigen relevanten Merkmale, ohne Stellenbeschreibung und ohne
vorgegebenes Schema. Nichts erfinden. Für jedes Merkmal kurze Evidenz angeben.
Gib ausschließlich JSON zurück:
{"attributes":[{"name":"...","value":"...","evidence":"..."}],
 "surprises":[{"name":"...","value":"...","evidence":"..."}]}.
"""

SCHEMA_SYSTEM = """Erzeuge das verbindliche Vergleichsschema ausschließlich aus der
Stellenausschreibung und den zusätzlichen Wunschattributen. Bewerbungsunterlagen dürfen
das Schema nicht erweitern. Führe semantisch gleiche Anforderungen zusammen, sodass jede
Anforderung genau eine vergleichbare Spalte erhält. Behalte Wunschattribute als eigene
Spalten, sofern sie nicht bereits semantisch durch eine Stellenanforderung abgedeckt sind.
Individuelle Merkmale aus Bewerbungen gehören ausdrücklich nicht in dieses Schema; sie
werden später gesammelt als zusätzliche/überraschende Merkmale je Bewerbung ausgegeben.
Keine Kandidaten bewerten und nichts erfinden.
Gib ausschließlich JSON zurück:
{"attributes":[{"name":"...","description":"...","source":"applicant|desired|job",
"priority":"must|nice|informational"}]}.
"""

FINAL_SYSTEM = """Extrahiere eine Bewerbung anhand des vorgegebenen Schemas.
Für jedes Schemaattribut muss ein Objekt mit value, status und evidence geliefert werden.
status ist documented, not_documented oder unclear. Niemals fehlende Angaben ergänzen.
Jedes fachliche oder persönliche Merkmal, das nicht in eine Schema-Spalte passt, muss in
einer einzigen Liste additional_attributes gesammelt werden. Diese Liste darf beliebig
viele Einträge enthalten, erzeugt aber keine neuen Schema-Spalten. Dazu gehören auch
interessante unerwartete Merkmale.
Prüfe zusätzlich auf mögliche Unstimmigkeiten oder Auffälligkeiten, zum Beispiel
Widersprüche zwischen Dokumenten, fehlende erwartbare Nachweise, unklare Titel,
abweichende Zeitangaben, möglicherweise abgelaufene Dokumente oder andere Punkte,
die vor einer Entscheidung geprüft werden sollten. Formuliere diese neutral als
Prüfhinweis und behaupte keinen Befund, der aus den Dokumenten nicht hervorgeht.
Gib ausschließlich JSON zurück:
{"summary":"...","attributes":{"Attribut":{"value":"...","status":"...","evidence":"..."}},
"additional_attributes":[{"name":"...","value":"...","evidence":"..."}],
"inconsistencies":[{"name":"...","description":"...","evidence":"...","severity":"low|medium|high"}],
"questions":["..."]}.
"""


class ApplicationPipeline:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def first_pass(self, applicant: Applicant) -> RawProfile:
        result = self.client.complete_json(RAW_SYSTEM, _document_prompt(applicant))
        return RawProfile(applicant.applicant_id, _list(result.get("attributes")), _list(result.get("surprises")))

    def build_schema(
        self,
        job_description: str,
        desired_attributes: list[str],
    ) -> list[SchemaAttribute]:
        user = json.dumps(
            {"desired_attributes": desired_attributes, "job_description": job_description},
            ensure_ascii=False,
        )
        result = self.client.complete_json(SCHEMA_SYSTEM, user, max_tokens=16000)
        return [SchemaAttribute(**_schema_attribute(item)) for item in _list(result.get("attributes"))]

    def final_pass(self, applicant: Applicant, schema: list[SchemaAttribute]) -> FinalProfile:
        schema_json = [attribute.__dict__ for attribute in schema]
        result = self.client.complete_json(
            FINAL_SYSTEM,
            _document_prompt(applicant) + "\nSCHEMA:\n" + json.dumps(schema_json, ensure_ascii=False),
        )
        return FinalProfile(
            applicant_id=applicant.applicant_id,
            summary=str(result.get("summary", "")),
            attributes=result.get("attributes", {}) if isinstance(result.get("attributes"), dict) else {},
            additional_attributes=_list(result.get("additional_attributes", result.get("surprising_attributes"))),
            inconsistencies=_list(result.get("inconsistencies")),
            questions=[str(q) for q in _list(result.get("questions"))],
        )


def _document_prompt(applicant: Applicant) -> str:
    return f"BEWERBER-ID: {applicant.applicant_id}\nQUELLEN: {json.dumps(applicant.sources, ensure_ascii=False)}\nDOKUMENTE:\n{applicant.text}"


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _schema_attribute(value: Any) -> dict[str, str]:
    if isinstance(value, str):
        return {"name": value}
    return {
        "name": str(value.get("name", "")).strip(),
        "description": str(value.get("description", "")),
        "source": str(value.get("source", "informational")),
        "priority": str(value.get("priority", "informational")),
    }
