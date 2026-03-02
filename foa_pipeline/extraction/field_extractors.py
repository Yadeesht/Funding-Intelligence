"""
Field Extractors — Shared text cleaning and regex extraction utilities.

Used across all ingestion modules for normalizing raw HTML/PDF text
into clean structured fields.
"""

import re
import unicodedata
from typing import Optional


def normalize_whitespace(text: str) -> str:
    """Collapse consecutive whitespace into single spaces and strip."""
    if not text:
        return ""
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def clean_text(text: Optional[str]) -> str:
    """Full text cleaning pipeline.

    1. Unicode normalization (NFKD → ASCII-safe)
    2. Strip control characters
    3. Normalize whitespace
    4. Strip leading/trailing whitespace
    """
    if not text:
        return ""
    # Unicode normalize
    text = unicodedata.normalize("NFKD", text)
    # Remove control characters except newline/tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    # Collapse whitespace
    text = normalize_whitespace(text)
    return text


def extract_with_regex(pattern: str, text: str, group: int = 1) -> Optional[str]:
    """Extract a field using a regex pattern.

    Args:
        pattern: Regex pattern with at least one capture group.
        text: Text to search.
        group: Which capture group to return (default=1).

    Returns:
        Matched and stripped text, or None if no match.
    """
    if not text:
        return None
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    try:
        return match.group(group).strip()
    except IndexError:
        return match.group(0).strip()


def extract_all_with_regex(pattern: str, text: str) -> list:
    """Extract all matches of a pattern from text.

    Returns a list of matched strings (group 1 if available, else group 0).
    """
    if not text:
        return []
    matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
    results = []
    for m in matches:
        try:
            results.append(m.group(1).strip())
        except IndexError:
            results.append(m.group(0).strip())
    return results


def truncate_text(text: str, max_length: int = 5000) -> str:
    """Truncate text to a maximum length, adding ellipsis if truncated."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."
