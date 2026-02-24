AI-Powered FOA Ingestion (Screening Task)

This code implements a minimal Funding Opportunity Announcement (FOA) ingestion pipeline.

Given a Grants.gov  FOA URL, the script: only this URL template is considered when writing the regex pattern

1. Fetches the webpage
2. Extracts structured fields using regex-based parsing
3. Applies deterministic rule-based semantic tags (only considered the tags related to AI and mathematics related content)
4. Exports structured outputs as JSON and CSV


Use this command to run the code:

python main.py --url "FOA_URL" --out_dir ./out

(replace the FOA_URL with the URL you want to test)

sampel URL u can try:

https://simpler.grants.gov/opportunity/508e8ee7-6925-4593-a548-66578974572f

The code better works for the simpler.grants.gov listed webpages, i have reviewed various webpage from that and tested its working perfect for those

Assumptions & Limitations

1. Regex patterns are tailored to Grants.gov HTML structure.
2. PDF ingestion is not available in this code.

