"""
Base Ingestor — Abstract base class for all FOA source adapters.

Every new source (Grants.gov, NSF, NIH, etc.) extends this class
and implements the three core methods: search, fetch_single, ingest_batch.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from foa_pipeline.schema.foa_schema import FOARecord


logger = logging.getLogger(__name__)


class BaseIngestor(ABC):
    """Abstract base class for FOA source adapters.

    Subclasses must set SOURCE_NAME and implement all abstract methods.
    """

    SOURCE_NAME: str = ""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def search(self, query: str, limit: int = 25) -> List[FOARecord]:
        """Search for FOAs matching a query string.

        Args:
            query: Search keywords.
            limit: Maximum number of results to return.

        Returns:
            List of FOARecord objects (may have partial fields).
        """
        pass

    @abstractmethod
    def fetch_single(self, url_or_id: str) -> Optional[FOARecord]:
        """Fetch a single FOA by URL or source-specific identifier.

        Args:
            url_or_id: A URL or opportunity ID.

        Returns:
            A fully populated FOARecord, or None on failure.
        """
        pass

    @abstractmethod
    def ingest_batch(self, limit: int = 50) -> List[FOARecord]:
        """Ingest a batch of recent FOAs from this source.

        Args:
            limit: Maximum number of FOAs to retrieve.

        Returns:
            List of normalized FOARecord objects.
        """
        pass

    def validate_records(self, records: List[FOARecord]) -> List[FOARecord]:
        """Validate records and log any issues found.

        All records are kept (not discarded), but issues are logged
        as warnings for review.

        Args:
            records: List of FOARecord objects to validate.

        Returns:
            The same list — all records are returned.
        """
        for record in records:
            issues = record.validate()
            if issues:
                self.logger.warning(
                    "Validation issues for %s: %s", record.foa_id, issues
                )
        return records
