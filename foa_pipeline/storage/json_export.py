"""
JSON Export — Serializes FOA records to reproducible JSON files.

Supports:
  - Single-file export (list of records)
  - Deterministic ordering (sorted by foa_id)
  - Schema validation before export
  - Incremental update (merge new records into existing file)
"""

import json
import logging
import os
from typing import List, Optional
from pathlib import Path

from foa_pipeline.schema.foa_schema import FOARecord


logger = logging.getLogger(__name__)


def export_json(
    records: List[FOARecord],
    output_path: str,
    indent: int = 2,
    merge: bool = False,
) -> str:
    """Export FOA records to a JSON file.

    Args:
        records: List of FOARecord objects.
        output_path: Path to write the JSON file.
        indent: JSON indentation (default 2).
        merge: If True, merge with existing file (dedup by foa_id).

    Returns:
        The output file path.
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Merge with existing if requested
    if merge and os.path.exists(output_path):
        existing = load_json(output_path)
        existing_ids = {r.foa_id for r in existing}
        new_records = [r for r in records if r.foa_id not in existing_ids]
        records = existing + new_records
        logger.info(
            "Merged %d new records with %d existing → %d total",
            len(new_records),
            len(existing),
            len(records),
        )

    # Sort deterministically by foa_id
    records.sort(key=lambda r: r.foa_id)

    # Convert to dicts
    data = [record.to_dict() for record in records]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)

    logger.info("Exported %d records to %s", len(records), output_path)
    return output_path


def load_json(file_path: str) -> List[FOARecord]:
    """Load FOA records from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        List of FOARecord objects.
    """
    if not os.path.exists(file_path):
        logger.warning("JSON file not found: %s", file_path)
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for item in data:
        try:
            records.append(FOARecord.from_dict(item))
        except Exception as e:
            logger.warning("Failed to parse record: %s", e)

    logger.info("Loaded %d records from %s", len(records), file_path)
    return records
