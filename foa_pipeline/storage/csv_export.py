"""
CSV Export — Serializes FOA records to flat CSV files.

Flattens the nested tags structure into pipe-delimited columns
for easy viewing in spreadsheets and data analysis tools.

Columns:
  foa_id, title, agency, source, open_date, close_date,
  eligibility, description, award_min, award_max, source_url,
  tags_research_domains, tags_methods, tags_populations, tags_sponsor_themes,
  ingested_at
"""

import csv
import logging
from typing import List
from pathlib import Path

from foa_pipeline.schema.foa_schema import FOARecord


logger = logging.getLogger(__name__)

# CSV column order
CSV_COLUMNS = [
    "foa_id",
    "title",
    "agency",
    "source",
    "open_date",
    "close_date",
    "eligibility",
    "description",
    "award_min",
    "award_max",
    "source_url",
    "tags_research_domains",
    "tags_methods",
    "tags_populations",
    "tags_sponsor_themes",
    "ingested_at",
]


def _record_to_csv_row(record: FOARecord) -> dict:
    """Flatten an FOARecord into a CSV-compatible dict."""
    tags = record.tags
    return {
        "foa_id": record.foa_id,
        "title": record.title,
        "agency": record.agency,
        "source": record.source,
        "open_date": record.open_date or "",
        "close_date": record.close_date or "",
        "eligibility": record.eligibility[:500] if record.eligibility else "",
        "description": record.description[:1000] if record.description else "",
        "award_min": record.award_min if record.award_min is not None else "",
        "award_max": record.award_max if record.award_max is not None else "",
        "source_url": record.source_url,
        "tags_research_domains": " | ".join(tags.research_domains),
        "tags_methods": " | ".join(tags.methods),
        "tags_populations": " | ".join(tags.populations),
        "tags_sponsor_themes": " | ".join(tags.sponsor_themes),
        "ingested_at": record.ingested_at or "",
    }


def export_csv(records: List[FOARecord], output_path: str) -> str:
    """Export FOA records to a CSV file.

    Args:
        records: List of FOARecord objects.
        output_path: Path to write the CSV file.

    Returns:
        The output file path.
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Sort deterministically by foa_id
    records.sort(key=lambda r: r.foa_id)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(_record_to_csv_row(record))

    logger.info("Exported %d records to %s", len(records), output_path)
    return output_path
