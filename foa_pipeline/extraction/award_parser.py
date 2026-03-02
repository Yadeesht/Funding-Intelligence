"""
Award Parser — Extracts and normalizes monetary award amounts.

Handles formats like:
  - "$1,000,000"
  - "1000000"
  - "$500K"
  - "$2.5M"
  - "$500,000 - $1,000,000" (range)
"""

import re
import logging
from typing import Optional, Tuple


logger = logging.getLogger(__name__)


def parse_award_amount(amount_str: Optional[str]) -> Optional[float]:
    """Parse a single monetary amount string into a float.

    Args:
        amount_str: Raw amount string (e.g., "$1,000,000", "500K").

    Returns:
        Numeric value as float, or None on failure.
    """
    if not amount_str:
        return None

    amount_str = amount_str.strip()

    # Remove dollar sign and whitespace
    amount_str = amount_str.replace("$", "").replace(" ", "").strip()

    if not amount_str:
        return None

    # Handle K/M/B suffixes
    multiplier = 1.0
    suffix_match = re.match(r"^([\d,.]+)\s*([KkMmBb])$", amount_str)
    if suffix_match:
        amount_str = suffix_match.group(1)
        suffix = suffix_match.group(2).upper()
        multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suffix]

    # Remove commas
    amount_str = amount_str.replace(",", "")

    try:
        return float(amount_str) * multiplier
    except ValueError:
        logger.debug("Could not parse award amount: '%s'", amount_str)
        return None


def parse_award_range(
    range_str: Optional[str],
) -> Tuple[Optional[float], Optional[float]]:
    """Parse an award range string into (min, max) tuple.

    Handles formats like:
      - "$500,000 - $1,000,000"
      - "$500K to $1M"
      - "Up to $2,000,000"

    Returns:
        Tuple of (award_min, award_max).
    """
    if not range_str:
        return None, None

    # "Up to X" pattern
    up_to = re.search(r"[Uu]p\s+to\s+\$?([\d,KkMmBb.]+)", range_str)
    if up_to:
        return None, parse_award_amount(up_to.group(1))

    # Range pattern: "$X - $Y" or "$X to $Y"
    amounts = re.findall(r"\$?([\d,]+(?:\.\d+)?[KkMmBb]?)", range_str)
    if len(amounts) >= 2:
        return parse_award_amount(amounts[0]), parse_award_amount(amounts[1])
    elif len(amounts) == 1:
        return None, parse_award_amount(amounts[0])

    return None, None
