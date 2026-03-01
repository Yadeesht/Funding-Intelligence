# FOA Pipeline — AI-Powered Funding Intelligence

An open-source pipeline that automatically ingests Funding Opportunity Announcements (FOAs) from public sources, extracts structured fields, and applies ontology-based semantic tags to support institutional research discovery and grant matching.

## Features

- **Multi-source ingestion** — Grants.gov (API + HTML scraping) and NSF (Awards API + page scraping)
- **Canonical schema** — All FOAs normalized into a strict JSON schema with validation
- **Hybrid semantic tagging** — Rule-based keyword matching + embedding similarity (sentence-transformers)
- **Controlled ontology** — 4 taxonomy dimensions: Research Domains, Methods, Populations, Sponsor Themes
- **Reproducible exports** — JSON + CSV with deterministic ordering
- **Evaluation framework** — 20-record gold dataset with precision/recall/F1 metrics
- **Modular architecture** — Each component is pluggable; new sources/taggers/ontologies plug in easily

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For embedding-based tagging, `sentence-transformers` is included in requirements. On first use it will download the `all-MiniLM-L6-v2` model (~80MB).

### 2. Run the pipeline

**Ingest from Grants.gov (default):**
```bash
python run_pipeline.py --source grants_gov --limit 20 --out_dir ./output
```

**Ingest from NSF:**
```bash
python run_pipeline.py --source nsf --limit 10 --out_dir ./output
```

**Ingest from all sources:**
```bash
python run_pipeline.py --source all --limit 50 --out_dir ./output
```

**Fetch a single opportunity by URL:**
```bash
python run_pipeline.py --url "https://simpler.grants.gov/opportunity/508e8ee7-6925-4593-a548-66578974572f" --out_dir ./output
```

**Search by keyword:**
```bash
python run_pipeline.py --source grants_gov --query "artificial intelligence" --limit 20 --out_dir ./output
```

### 3. Choose a tagger

```bash
# Rule-based (fast, deterministic baseline)
python run_pipeline.py --source grants_gov --tagger rule_based --out_dir ./output

# Embedding-based (semantic similarity with sentence-transformers)
python run_pipeline.py --source grants_gov --tagger embedding --threshold 0.35 --out_dir ./output

# Hybrid (union of rule-based + embedding tags)
python run_pipeline.py --source grants_gov --tagger hybrid --out_dir ./output
```

### 4. Run evaluation

```bash
# Evaluate rule-based tagger
python run_pipeline.py --evaluate

# Evaluate embedding tagger
python run_pipeline.py --evaluate --tagger embedding --threshold 0.3

# Or run directly
python -m foa_pipeline.evaluation.evaluate --tagger rule_based
```

### 5. Incremental updates

```bash
# Merge new records into existing exports (deduplicates by foa_id)
python run_pipeline.py --source grants_gov --limit 20 --out_dir ./output --merge
```

## Canonical FOA Schema

Every FOA is normalized into this structure:

```json
{
    "foa_id": "a1b2c3d4e5f60718",
    "title": "AI-Driven Drug Discovery",
    "agency": "National Science Foundation",
    "source": "grants_gov",
    "open_date": "2025-01-15T00:00:00",
    "close_date": "2025-06-30T00:00:00",
    "eligibility": "Higher education institutions...",
    "description": "This program supports research...",
    "award_min": 100000.0,
    "award_max": 500000.0,
    "source_url": "https://simpler.grants.gov/opportunity/...",
    "raw_text": "",
    "tags": {
        "research_domains": ["Artificial Intelligence", "Biomedical Research"],
        "methods": ["Machine Learning Methods", "Simulation"],
        "populations": [],
        "sponsor_themes": ["Innovation & Commercialization"]
    },
    "ingested_at": "2025-03-01T12:00:00+00:00"
}
```

## Ontology Dimensions

| Dimension | Examples | Count |
|-----------|---------|-------|
| **Research Domains** | AI, Machine Learning, Public Health, Climate Science, Cybersecurity | 18 |
| **Methods** | Clinical Trial, Simulation, Qualitative Research, Mixed Methods | 10 |
| **Populations** | Children & Youth, Older Adults, Veterans, Underserved Communities | 8 |
| **Sponsor Themes** | Responsible AI, Sustainability, Workforce Development, DEI | 10 |

All vocabularies are extensible — add new tags by editing `foa_pipeline/ontology/vocabularies.py`.

## Tagging Approaches

### Layer 1: Rule-Based (Baseline)
- Deterministic keyword/substring matching
- Uses the `keywords` field from each ontology entry
- Fast, predictable, no external model dependencies

### Layer 2: Embedding Similarity
- Encodes FOA text + ontology descriptions using `all-MiniLM-L6-v2`
- Cosine similarity scoring with configurable threshold
- Pre-computes label embeddings for efficiency
- Captures semantic meaning beyond exact keyword matches

### Hybrid Mode
- Applies both taggers, takes the union of assigned tags
- Best coverage at the cost of slightly lower precision

## Evaluation

The evaluation framework uses 20 manually annotated FOAs spanning diverse research domains. Metrics computed per category:

- **Precision**: Of predicted tags, how many are correct?
- **Recall**: Of expected tags, how many were found?
- **F1**: Harmonic mean of precision and recall
- **Macro Average**: Unweighted average across all 4 categories

Run `python run_pipeline.py --evaluate` to see the full report.

## Legacy Prototype

The original single-file prototype is preserved in `main.py`. It supports:
```bash
python main.py --url "https://simpler.grants.gov/opportunity/508e8ee7-6925-4593-a548-66578974572f" --out_dir ./out
```

## Adding a New Source

1. Create `foa_pipeline/ingestion/new_source.py`
2. Extend `BaseIngestor` and implement `search()`, `fetch_single()`, `ingest_batch()`
3. Set `SOURCE_NAME = "new_source"`
4. Register in `foa_pipeline/ingestion/__init__.py`
5. Add to `run_pipeline.py` source choices

## Stretch Goals

- [ ] NIH Reporter integration
- [ ] PDF ingestion (PyPDF / PDFMiner)
- [ ] Vector indexing with FAISS or Chroma for similarity search
- [ ] Lightweight search interface (CLI or web UI)
- [ ] LLM-assisted classification (OpenAI / local models)

## Requirements

- Python 3.9+
- See `requirements.txt` for full dependency list

