"""
Date Parser — Robust date parsing for FOA date fields.

Handles various date formats encountered across funding sources:
  - "January 15, 2025"
  - "01/15/2025"
  - "2025-01-15"
  - "Jan 15 2025"
  - etc.

All outputs are ISO 8601 formatted (YYYY-MM-DDTHH:MM:SS).
"""

import re
import logging
from typing import Optional
from dateutil import parser as dateparser
from datetime import datetime


logger = logging.getLogger(__name__)


def parse_date_safe(date_str: Optional[str]) -> Optional[str]:
    """Parse a date string into ISO 8601 format.

    Tolerant of various formats. Returns None on failure.

    Args:
        date_str: Raw date string from any source.

    Returns:
        ISO 8601 formatted date string, or None.
    """
    if not date_str:
        return None

    # Clean the input
    date_str = date_str.strip()

    # Remove common prefixes
    date_str = re.sub(
        r"^(Posted|Published|Due|Close|Open|Start|End)\s*(Date)?[:\s]*",
        "",
        date_str,
        flags=re.IGNORECASE,
    ).strip()

    if not date_str:
        return None

    # Try dateutil parser (handles most formats)
    try:
        parsed = dateparser.parse(date_str, fuzzy=True)
        if parsed:
            return parsed.isoformat()
    except (ValueError, OverflowError):
        pass

    # Try common specific patterns as fallback
    patterns = [
        (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
        (r"(\d{1,2})/(\d{1,2})/(\d{4})", "%m/%d/%Y"),
        (r"(\d{1,2})-(\d{1,2})-(\d{4})", "%m-%d-%Y"),
    ]

    for pattern, fmt in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                parsed = datetime.strptime(match.group(0), fmt)
                return parsed.isoformat()
            except ValueError:
                continue

    logger.debug("Could not parse date: '%s'", date_str)
    return None


def format_date_display(iso_date: Optional[str]) -> str:
    """Convert ISO date to human-readable format for display.

    Args:
        iso_date: ISO 8601 date string.

    Returns:
        "Month Day, Year" format, or empty string.
    """
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return iso_date
