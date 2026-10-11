from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Applicant:
    applicant_id: str
    text: str
    sources: list[str] = field(default_factory=list)


@dataclass
class RawProfile:
    applicant_id: str
    attributes: list[dict[str, Any]]
    surprises: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SchemaAttribute:
    name: str
    description: str = ""
    source: str = "applicant|job|desired"
    priority: str = "informational"


@dataclass
class FinalProfile:
    applicant_id: str
    summary: str
    attributes: dict[str, Any]
    additional_attributes: list[dict[str, Any]] = field(default_factory=list)
    inconsistencies: list[dict[str, Any]] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
