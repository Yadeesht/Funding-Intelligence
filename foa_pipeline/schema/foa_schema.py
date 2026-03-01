"""
Canonical FOA Schema — Single source of truth for all FOA data.

Every ingestion source normalizes into this schema before downstream
processing (tagging, export, evaluation).
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class SemanticTags:
    """Semantic tags aligned to the controlled ontology."""

    research_domains: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    populations: List[str] = field(default_factory=list)
    sponsor_themes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def all_tags(self) -> List[str]:
        """Return a flat list of all assigned tags."""
        return (
            self.research_domains
            + self.methods
            + self.populations
            + self.sponsor_themes
        )

    def is_empty(self) -> bool:
        return not any(
            [self.research_domains, self.methods, self.populations, self.sponsor_themes]
        )


@dataclass
class FOARecord:
    """Canonical Funding Opportunity Announcement record.

    All ingestion sources normalize into this format.
    """

    foa_id: str = ""
    title: str = ""
    agency: str = ""
    source: str = ""  # e.g., "grants_gov", "nsf"
    open_date: Optional[str] = None  # ISO 8601
    close_date: Optional[str] = None  # ISO 8601
    eligibility: str = ""
    description: str = ""
    award_min: Optional[float] = None
    award_max: Optional[float] = None
    source_url: str = ""
    raw_text: str = ""
    tags: SemanticTags = field(default_factory=SemanticTags)
    ingested_at: Optional[str] = None  # ISO 8601 timestamp

    def __post_init__(self):
        if not self.ingested_at:
            self.ingested_at = datetime.now(timezone.utc).isoformat()
        if not self.foa_id and self.source_url:
            self.foa_id = self.generate_id(self.source_url)

    @staticmethod
    def generate_id(text: str) -> str:
        """Generate a deterministic FOA ID from any text (typically source URL)."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> "FOARecord":
        """Construct an FOARecord from a dictionary."""
        tags_data = data.pop("tags", {})
        if isinstance(tags_data, dict):
            tags = SemanticTags(**tags_data)
        elif isinstance(tags_data, SemanticTags):
            tags = tags_data
        else:
            tags = SemanticTags()
        return cls(tags=tags, **data)

    def validate(self) -> List[str]:
        """Validate required fields. Returns list of issue descriptions."""
        issues = []
        if not self.foa_id:
            issues.append("Missing foa_id")
        if not self.title:
            issues.append("Missing title")
        if not self.source:
            issues.append("Missing source")
        if not self.source_url:
            issues.append("Missing source_url")
        for date_field, date_val in [
            ("open_date", self.open_date),
            ("close_date", self.close_date),
        ]:
            if date_val:
                try:
                    datetime.fromisoformat(date_val)
                except ValueError:
                    issues.append(f"Invalid {date_field} format: {date_val}")
        if self.award_min is not None and self.award_max is not None:
            if self.award_min > self.award_max:
                issues.append("award_min exceeds award_max")
        return issues


# Template dict for quick reference and JSON schema documentation
SCHEMA_TEMPLATE = {
    "foa_id": "",
    "title": "",
    "agency": "",
    "source": "",
    "open_date": "",
    "close_date": "",
    "eligibility": "",
    "description": "",
    "award_min": None,
    "award_max": None,
    "source_url": "",
    "raw_text": "",
    "tags": {
        "research_domains": [],
        "methods": [],
        "populations": [],
        "sponsor_themes": [],
    },
    "ingested_at": "",
}
