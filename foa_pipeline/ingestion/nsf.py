"""
NSF Ingestor — Retrieves funding opportunities from the National Science Foundation.

Supports:
  - Scraping the NSF funding opportunities listing page
  - Fetching individual solicitation pages (HTML)
  - Batch ingestion of recent NSF opportunities

Data sources:
  - Listing: https://new.nsf.gov/funding/opportunities
  - Individual: https://www.nsf.gov/pubs/{year}/nsf{id}/nsf{id}.htm
  - Awards API (supplementary): https://api.nsf.gov/services/v1/awards.json
"""

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

# NSF endpoints
NSF_OPPORTUNITIES_URL = "https://new.nsf.gov/funding/opportunities"
NSF_AWARDS_API = "https://api.nsf.gov/services/v1/awards.json"


class NSFIngestor(BaseIngestor):
    """Source adapter for National Science Foundation funding opportunities."""

    SOURCE_NAME = "nsf"

    def __init__(self, timeout: int = 30, delay: float = 1.0):
        super().__init__(timeout=timeout)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "FOA-Pipeline/0.1 (research-tool)",
                "Accept": "text/html,application/json",
            }
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 25) -> List[FOARecord]:
        """Search NSF awards API for opportunities matching a query.

        Note: The NSF Awards API returns awarded grants. For active
        solicitations, use ingest_batch() which scrapes the listing page.
        """
        self.logger.info("Searching NSF awards for: %s (limit=%d)", query, limit)

        params = {
            "keyword": query,
            "printFields": "id,title,agency,startDate,expDate,abstractText,fundsObligatedAmt,piFirstName,piLastName",
            "offset": 1,
            "rpp": min(limit, 25),
        }

        try:
            resp = self.session.get(NSF_AWARDS_API, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            self.logger.error("NSF Awards API error: %s", e)
            return []

        records = []
        awards = data.get("response", {}).get("award", [])
        for award in awards[:limit]:
            record = self._award_to_record(award)
            if record:
                records.append(record)

        self.logger.info("NSF search returned %d records", len(records))
        return self.validate_records(records)

    def fetch_single(self, url_or_id: str) -> Optional[FOARecord]:
        """Fetch a single NSF solicitation page by URL.

        Args:
            url_or_id: Full URL to an NSF solicitation page.
        """
        url = url_or_id
        self.logger.info("Fetching NSF solicitation: %s", url)

        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.error("Failed to fetch NSF page %s: %s", url, e)
            return None

        return self._parse_solicitation_page(resp.text, url)

    def ingest_batch(self, limit: int = 50) -> List[FOARecord]:
        """Ingest recent NSF funding opportunities by scraping the listing page."""
        self.logger.info("Ingesting batch of %d NSF opportunities", limit)

        try:
            resp = self.session.get(NSF_OPPORTUNITIES_URL, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.error("Failed to fetch NSF opportunities listing: %s", e)
            return []

        records = self._parse_listing_page(resp.text, limit)
        self.logger.info("NSF batch ingestion retrieved %d records", len(records))
        return self.validate_records(records)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _award_to_record(self, award: dict) -> Optional[FOARecord]:
        """Convert an NSF Awards API result to FOARecord."""
        try:
            award_id = award.get("id", "")
            title = award.get("title", "")
            agency_name = award.get("agency", "NSF")
            start_date = parse_date_safe(award.get("startDate"))
            exp_date = parse_date_safe(award.get("expDate"))
            abstract_text = award.get("abstractText", "")
            funds = award.get("fundsObligatedAmt")

            source_url = f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={award_id}"

            return FOARecord(
                foa_id=f"nsf-{award_id}" if award_id else "",
                title=clean_text(title),
                agency=clean_text(agency_name),
                source=self.SOURCE_NAME,
                open_date=start_date,
                close_date=exp_date,
                description=clean_text(abstract_text),
                award_min=float(funds) if funds else None,
                award_max=float(funds) if funds else None,
                source_url=source_url,
            )
        except Exception as e:
            self.logger.warning("Failed to parse NSF award: %s", e)
            return None

    def _parse_listing_page(self, html: str, limit: int) -> List[FOARecord]:
        """Parse the NSF funding opportunities listing page.

        Extracts links to individual solicitations, then fetches each.
        """
        soup = BeautifulSoup(html, "html.parser")
        records: List[FOARecord] = []

        # NSF listing page has opportunity cards/links
        # Look for links that point to funding opportunity detail pages
        links = soup.find_all("a", href=True)
        opportunity_urls = []

        for link in links:
            href = link["href"]
            # Match solicitation links (e.g., /funding/opportunities/... or /pubs/...)
            if re.search(r"/funding/opportunities/\w+", href):
                full_url = (
                    href if href.startswith("http") else f"https://new.nsf.gov{href}"
                )
                if full_url not in opportunity_urls:
                    opportunity_urls.append(full_url)
            elif re.search(r"/pubs/\d{4}/nsf\d+", href):
                full_url = (
                    href if href.startswith("http") else f"https://www.nsf.gov{href}"
                )
                if full_url not in opportunity_urls:
                    opportunity_urls.append(full_url)

        self.logger.info(
            "Found %d opportunity links on NSF listing", len(opportunity_urls)
        )

        for url in opportunity_urls[:limit]:
            record = self.fetch_single(url)
            if record:
                records.append(record)
            time.sleep(self.delay)

        return records

    def _parse_solicitation_page(self, html: str, url: str) -> Optional[FOARecord]:
        """Parse an individual NSF solicitation page into an FOARecord."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            full_text = soup.get_text(separator="\n", strip=True)

            # Try to extract title from page title or h1
            title = ""
            title_tag = soup.find("h1")
            if title_tag:
                title = title_tag.get_text(strip=True)
            elif soup.title:
                title = soup.title.get_text(strip=True)

            # Extract description — look for common NSF section headers
            description = ""
            desc_section = extract_with_regex(
                r"(?:Synopsis|Program Description|Summary)(.*?)(?:Program Requirements|Eligibility|Award Information|$)",
                full_text,
            )
            if desc_section:
                description = desc_section[:5000]  # cap length

            # Eligibility
            eligibility = (
                extract_with_regex(
                    r"Eligibility[:\s]*(.*?)(?:Award Information|Proposal Preparation|Application|$)",
                    full_text,
                )
                or ""
            )

            # Dates
            open_date_raw = extract_with_regex(
                r"(?:Posted|Published|Release Date)[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
                full_text,
            )
            close_date_raw = extract_with_regex(
                r"(?:Deadline|Due Date|Close Date)[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
                full_text,
            )

            # Award amounts
            award_text = extract_with_regex(
                r"(?:Estimated Number of Awards|Anticipated Funding Amount|Award Range).*?(\$[\d,]+(?:\s*[-–to]+\s*\$[\d,]+)?)",
                full_text,
            )
            award_min = None
            award_max = None
            if award_text:
                amounts = re.findall(r"\$([\d,]+)", award_text)
                if len(amounts) >= 2:
                    award_min = parse_award_amount(amounts[0])
                    award_max = parse_award_amount(amounts[1])
                elif len(amounts) == 1:
                    award_max = parse_award_amount(amounts[0])

            return FOARecord(
                foa_id=FOARecord.generate_id(url),
                title=clean_text(title),
                agency="National Science Foundation",
                source=self.SOURCE_NAME,
                open_date=parse_date_safe(open_date_raw),
                close_date=parse_date_safe(close_date_raw),
                eligibility=clean_text(eligibility)[:3000],
                description=clean_text(description),
                award_min=award_min,
                award_max=award_max,
                source_url=url,
                raw_text=full_text[:50000],
            )
        except Exception as e:
            self.logger.error("Failed to parse NSF solicitation %s: %s", url, e)
            return None
