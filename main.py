import requests
from bs4 import BeautifulSoup
import re
from dateutil import parser
import json
import pandas as pd
import argparse
import hashlib


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--out_dir", required=True)
    return parser.parse_args()


def fetch_webpage(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def extract_with_regex(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    if match.lastindex:
        return match.group(1).strip()

    return match.group(0).strip()


def extract_feids(text: str, url: str) -> dict:
    soup = BeautifulSoup(text, "html.parser")
    full_text = soup.get_text(separator="\n", strip=True)
    print(full_text)

    title = extract_with_regex(r"Opportunity Listing - (.*?)\n", full_text)

    # (Grand.gov) the regex are used based on the example i have taken so it does cover only the possible str i have identified
    agency = extract_with_regex(r"Agency:\s*(.*?)\s{2,}", full_text)

    open_date_raw = extract_with_regex(
        r"Posted date\s*\n\s*:\s*\n\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", full_text
    )
    close_date_raw = extract_with_regex(
        r"Archive date\s*\n\s*:\s*\n\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", full_text
    )

    if open_date_raw and ":" in open_date_raw:
        open_date_raw = open_date_raw.split(":")[1].strip()
    if close_date_raw and ":" in close_date_raw:
        close_date_raw = close_date_raw.split(":")[1].strip()

    open_date = parser.parse(open_date_raw).isoformat() if open_date_raw else None
    close_date = parser.parse(close_date_raw).isoformat() if close_date_raw else None

    eligibility_text = None
    eligibility_section = extract_with_regex(
        r"Eligibility\s*(.*?)\n\s*Grantor contact information", full_text
    )
    if eligibility_section:
        eligibility_text = eligibility_section.strip()

    program_description = None
    description_section = extract_with_regex(r"Description(.*?)Eligibility", full_text)
    if description_section:
        program_description = description_section.strip()

    award_min = extract_with_regex(r"\$([0-9,]+)\s*\n\s*Award Minimum", full_text)
    award_max = extract_with_regex(r"\$([0-9,]+)\s*\n\s*Award Maximum", full_text)
    if award_min and award_max:
        award_range = f"${award_min}-${award_max}"
    else:
        award_range = None

    return {
        "foa_id": hashlib.md5(url.encode()).hexdigest(),
        "title": title,
        "agency": agency,
        "open_date": open_date,
        "close_date": close_date,
        "eligibility_text": eligibility_text,
        "program_description": program_description,
        "award_range": award_range,
        "source_url": url,
    }


# sample list
TAG_RULES = {
    "artificial-intelligence": ["artificial intelligence", "ai systems"],
    "machine-learning": ["machine learning", "statistical learning"],
    "deep-learning": ["deep learning"],
    "generative-models": ["generative models"],
    "foundation-models": ["foundation models"],
    "federated-learning": ["federated learning"],
    "mathematical-foundations": [
        "mathematical understanding",
        "theoretical foundations",
        "mathematically grounded",
        "mathematical and theoretical",
    ],
    "explainable-ai": ["explainable", "interpretable"],
    "trustworthy-ai": ["trustworthy", "socially responsible"],
    "interdisciplinary-research": ["interdisciplinary", "collaboration"],
}


def tags(data: dict) -> dict:
    text = (
        (data.get("title") or "") + " " + (data.get("program_description") or "")
    ).lower()

    tags = set()

    for tag, kw in TAG_RULES.items():
        for keyword in kw:
            if keyword in text:
                tags.add(tag)
                break

    data["tags"] = sorted(list(tags))
    return data


def main():
    args = parse_args()
    web_content = fetch_webpage(args.url)
    feids = extract_feids(web_content, args.url)
    feids_with_tags = tags(feids)

    df = pd.DataFrame([feids_with_tags])
    df.to_csv(f"{args.out_dir}/foa_data.csv", index=False)
    json.dump(feids_with_tags, open(f"{args.out_dir}/foa_data.json", "w"), indent=4)


if __name__ == "__main__":
    main()
