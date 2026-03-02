"""
Grants.gov Ingestor — Retrieves FOAs from simpler.grants.gov.

Supports:
  - API-based search via POST /v1/opportunities/search
  - Single opportunity fetch via page scraping (simpler.grants.gov)
  - Batch ingestion of recent posted opportunities
"""

import os
import re
import time
import logging
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from foa_pipeline.ingestion.base_ingestor import BaseIngestor
from foa_pipeline.schema.foa_schema import FOARecord
from foa_pipeline.extraction.field_extractors import (
    clean_text,
    extract_with_regex,
)
from foa_pipeline.extraction.date_parser import parse_date_safe
from foa_pipeline.extraction.award_parser import parse_award_amount


logger = logging.getLogger(__name__)

SEARCH_API_URL = "https://api.simpler.grants.gov/v1/opportunities/search"
OPPORTUNITY_PAGE_BASE = "https://simpler.grants.gov/opportunity"

GRANTS_GOV_API_KEY = os.environ.get("GRANTS_GOV_API_KEY", "")


class GrantsGovIngestor(BaseIngestor):
    """Source adapter for Grants.gov (simpler.grants.gov)."""

    SOURCE_NAME = "grants_gov"

    def __init__(self, timeout: int = 30, delay: float = 1.0):
        """
        Args:
            timeout: HTTP request timeout in seconds.
            delay: Polite delay between requests (seconds).
        """
        super().__init__(timeout=timeout)
        self.delay = delay
        self.session = requests.Session()
        headers: dict = {
            "User-Agent": "FOA-Pipeline/0.1 (research-tool)",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        api_key = GRANTS_GOV_API_KEY
        if api_key:
            headers["X-Api-Key"] = api_key
        else:
            self.logger.warning(
                "GRANTS_GOV_API_KEY not set — API calls may return 401. "
                "Register at https://simpler.grants.gov/ to get a key."
            )
        self.session.headers.update(headers)

    # Public interface
    def search(self, query: str, limit: int = 25) -> List[FOARecord]:
        """Search Grants.gov for opportunities matching a query.

        Uses the simpler.grants.gov REST API.
        """
        self.logger.info("Searching Grants.gov for: %s (limit=%d)", query, limit)
        payload = {
            "pagination": {
                "page_offset": 1,
                "page_size": min(limit, 25),
                # sort_order must be a list of sort-descriptor objects
                "sort_order": [
                    {"order_by": "post_date", "sort_direction": "descending"}
                ],
            },
            "query": query,
        }

        try:
            resp = self.session.post(SEARCH_API_URL, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            self.logger.error("Grants.gov search API error: %s", e)
            return []
        except ValueError as e:
            # JSONDecodeError (subclass of ValueError) means the server returned
            # non-JSON — log the raw body to aid diagnosis
            self.logger.error(
                "Grants.gov search: unexpected non-JSON response (%s). Body: %s",
                e,
                resp.text[:500] if resp is not None else "<no response>",
            )
            return []

        records = []
        opportunities = data.get("data", [])
        for opp in opportunities[:limit]:
            record = self._api_result_to_record(opp)
            if record:
                records.append(record)

        self.logger.info("Search returned %d records", len(records))
        return self.validate_records(records)

    def fetch_single(self, url_or_id: str) -> Optional[FOARecord]:
        """Fetch a single FOA from its simpler.grants.gov page URL or opportunity ID."""
        if not url_or_id.startswith("http"):
            url = f"{OPPORTUNITY_PAGE_BASE}/{url_or_id}"
        else:
            url = url_or_id

        self.logger.info("Fetching single opportunity: %s", url)

        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.error("Failed to fetch %s: %s", url, e)
            return None

        return self._parse_opportunity_page(resp.text, url)

    def ingest_batch(self, limit: int = 50) -> List[FOARecord]:
        """Ingest a batch of recently posted FOAs from Grants.gov.

        Performs a broad search sorted by post date descending.
        """
        self.logger.info("Ingesting batch of %d recent Grants.gov FOAs", limit)
        # Base payload — page_offset and page_size are updated per iteration
        payload: dict = {
            "pagination": {
                "page_offset": 1,
                "page_size": min(limit, 25),
                "sort_order": [
                    {"order_by": "post_date", "sort_direction": "descending"}
                ],
            },
        }

        all_records: List[FOARecord] = []
        page = 1
        remaining = limit

        while remaining > 0:
            payload["pagination"]["page_offset"] = page
            payload["pagination"]["page_size"] = min(remaining, 25)

            resp = None
            try:
                resp = self.session.post(
                    SEARCH_API_URL, json=payload, timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                self.logger.error("Batch ingestion API error on page %d: %s", page, e)
                break
            except ValueError as e:
                self.logger.error(
                    "Batch ingestion: non-JSON response on page %d (%s). Body: %s",
                    page,
                    e,
                    resp.text[:500] if resp is not None else "<no response>",
                )
                break

            opportunities = data.get("data", [])
            if not opportunities:
                break

            for opp in opportunities:
                self.logger.debug("Processing batch opportunity: %s", opp)
                record = self._api_result_to_record(opp)
                if record:
                    all_records.append(record)
                    remaining -= 1
                    if remaining <= 0:
                        break

            page += 1
            time.sleep(self.delay)

        self.logger.info("Batch ingestion retrieved %d records", len(all_records))
        return self.validate_records(all_records)

    def _api_result_to_record(self, opp: dict) -> Optional[FOARecord]:
        """Convert an API search result dict into an FOARecord."""
        # self.logger.debug("Parsing API result: %s", opp)
        try:
            opp_id = opp.get("opportunity_id", "")
            title = opp.get("opportunity_title", "") or opp.get("title", "")
            agency = opp.get("agency_name", "") or opp.get("agency", "")

            # All date/award/description fields live inside the nested summary object
            summary = opp.get("summary") or {}
            open_date = parse_date_safe(
                summary.get("post_date") or opp.get("post_date")
            )
            close_date = parse_date_safe(
                summary.get("close_date") or opp.get("close_date")
            )
            description = clean_text(summary.get("summary_description") or "")
            award_min = summary.get("award_floor")
            award_max = summary.get("award_ceiling")

            source_url = f"{OPPORTUNITY_PAGE_BASE}/{opp_id}" if opp_id else ""

            return FOARecord(
                foa_id=str(opp_id) if opp_id else "",
                title=clean_text(title),
                agency=clean_text(agency),
                source=self.SOURCE_NAME,
                open_date=open_date,
                close_date=close_date,
                description=description,
                award_min=award_min,
                award_max=award_max,
                source_url=source_url,
            )
        except Exception as e:
            self.logger.warning("Failed to parse API result: %s", e)
            return None

    def _parse_opportunity_page(self, html: str, url: str) -> Optional[FOARecord]:
        """Parse a simpler.grants.gov opportunity page into an FOARecord.

        This extends the regex-based extraction from the original main.py
        with more robust parsing.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            full_text = soup.get_text(separator="\n", strip=True)

            title = extract_with_regex(r"Opportunity Listing - (.*?)\n", full_text)

            # Agency name appears on the line immediately after "Agency:"
            agency = extract_with_regex(r"Agency:\n(.*?)\n", full_text)

            open_date_raw = extract_with_regex(
                r"Posted date\s*\n\s*:\s*\n\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
                full_text,
            )
            close_date_raw = extract_with_regex(
                r"Archive date\s*\n\s*:\s*\n\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
                full_text,
            )

            # Clean stray colons from date strings
            if open_date_raw and ":" in open_date_raw:
                open_date_raw = open_date_raw.split(":")[1].strip()
            if close_date_raw and ":" in close_date_raw:
                close_date_raw = close_date_raw.split(":")[1].strip()

            open_date = parse_date_safe(open_date_raw)
            close_date = parse_date_safe(close_date_raw)

            eligibility = (
                extract_with_regex(
                    r"Eligibility\s*(.*?)\n\s*Grantor contact information", full_text
                )
                or ""
            )

            description = (
                extract_with_regex(r"Description(.*?)Eligibility", full_text) or ""
            )

            award_min = parse_award_amount(
                extract_with_regex(r"\$([0-9,]+)\s*\n\s*Award Minimum", full_text)
            )
            award_max = parse_award_amount(
                extract_with_regex(r"\$([0-9,]+)\s*\n\s*Award Maximum", full_text)
            )

            return FOARecord(
                foa_id=FOARecord.generate_id(url),
                title=clean_text(title or ""),
                agency=clean_text(agency or ""),
                source=self.SOURCE_NAME,
                open_date=open_date,
                close_date=close_date,
                eligibility=clean_text(eligibility),
                description=clean_text(description),
                award_min=award_min,
                award_max=award_max,
                source_url=url,
                raw_text=full_text[:50000],  # cap raw text size
            )
        except Exception as e:
            self.logger.error("Failed to parse opportunity page %s: %s", url, e)
            return None
