"""
Rule-Based Tagger — Deterministic keyword-matching semantic tagger.

Layer 1 of the hybrid tagging pipeline. Fast, predictable, and
serves as the baseline for tagging accuracy evaluation.

Uses the controlled ontology keywords to assign tags via exact
substring matching against the FOA title + description.
"""

import logging
from typing import List, Dict, Set

from foa_pipeline.schema.foa_schema import FOARecord, SemanticTags
from foa_pipeline.ontology.vocabularies import (
    RESEARCH_DOMAINS,
    METHODS,
    POPULATIONS,
    SPONSOR_THEMES,
)


logger = logging.getLogger(__name__)


class RuleBasedTagger:
    """Deterministic rule-based semantic tagger.

    Assigns tags by checking if any keyword from the controlled ontology
    appears as a substring in the FOA's combined text (title + description).
    """

    def __init__(self):
        self.vocabularies = {
            "research_domains": RESEARCH_DOMAINS,
            "methods": METHODS,
            "populations": POPULATIONS,
            "sponsor_themes": SPONSOR_THEMES,
        }

    def tag(self, record: FOARecord) -> FOARecord:
        """Apply rule-based tags to a single FOA record.

        Modifies record.tags in place and returns the record.
        """
        text = self._build_searchable_text(record)

        research_domains = self._match_category(text, "research_domains")
        methods = self._match_category(text, "methods")
        populations = self._match_category(text, "populations")
        sponsor_themes = self._match_category(text, "sponsor_themes")

        record.tags = SemanticTags(
            research_domains=sorted(research_domains),
            methods=sorted(methods),
            populations=sorted(populations),
            sponsor_themes=sorted(sponsor_themes),
        )

        logger.debug(
            "Rule-based tags for %s: domains=%d, methods=%d, pops=%d, themes=%d",
            record.foa_id,
            len(research_domains),
            len(methods),
            len(populations),
            len(sponsor_themes),
        )

        return record

    def tag_batch(self, records: List[FOARecord]) -> List[FOARecord]:
        """Apply rule-based tags to a batch of records."""
        tagged = []
        for record in records:
            tagged.append(self.tag(record))
        logger.info("Rule-based tagging applied to %d records", len(tagged))
        return tagged

    def _build_searchable_text(self, record: FOARecord) -> str:
        """Combine relevant fields into a single searchable text block."""
        parts = [
            record.title or "",
            record.description or "",
            record.eligibility or "",
        ]
        return " ".join(parts).lower()

    def _match_category(self, text: str, category: str) -> List[str]:
        """Find all matching tags for a given ontology category.

        Args:
            text: Lowercased searchable text.
            category: Ontology category key.

        Returns:
            List of matched tag labels (human-readable).
        """
        vocab = self.vocabularies.get(category, {})
        matched: List[str] = []

        for slug, entry in vocab.items():
            keywords = entry.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text:
                    matched.append(entry["label"])
                    break  # One keyword match is enough per tag

        return matched
