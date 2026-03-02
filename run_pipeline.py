"""
run_pipeline.py — Main CLI entry point for the FOA Pipeline.

Usage:
    # Ingest batch from Grants.gov
    python run_pipeline.py --source grants_gov --limit 20 --out_dir ./output

    # Ingest batch from NSF
    python run_pipeline.py --source nsf --limit 10 --out_dir ./output

    # Ingest from all sources
    python run_pipeline.py --source all --limit 50 --out_dir ./output

    # Fetch a single opportunity by URL
    python run_pipeline.py --url "https://simpler.grants.gov/opportunity/..." --out_dir ./output

    # Use embedding tagger instead of rule-based
    python run_pipeline.py --source grants_gov --tagger embedding --out_dir ./output

    # Merge new results into existing export
    python run_pipeline.py --source grants_gov --limit 20 --out_dir ./output --merge

"""

import argparse
import json
import logging
import os
import sys
from typing import List

from dotenv import load_dotenv

load_dotenv()

from foa_pipeline.schema.foa_schema import FOARecord
from foa_pipeline.ingestion.grants_gov import GrantsGovIngestor
from foa_pipeline.ingestion.nsf import NSFIngestor
from foa_pipeline.tagging.rule_based import RuleBasedTagger
from foa_pipeline.storage.json_export import export_json
from foa_pipeline.storage.csv_export import export_csv


def setup_logging(verbose: bool = False):
    """Configure logging for the pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="FOA Pipeline — Ingest, tag, and export funding opportunities.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--source",
        choices=["grants_gov", "nsf", "all"],
        default=None,
        help="Source to ingest from (default: grants_gov).",
    )
    source_group.add_argument(
        "--url",
        type=str,
        default=None,
        help="Fetch a single opportunity by URL.",
    )

    # Search / limit
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Search query for targeted ingestion.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum number of FOAs to ingest (default: 25).",
    )

    # Tagger selection
    parser.add_argument(
        "--tagger",
        choices=["rule_based", "embedding", "hybrid"],
        default="rule_based",
        help="Tagging approach (default: rule_based).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.35,
        help="Embedding similarity threshold (default: 0.35).",
    )

    # Output
    parser.add_argument(
        "--out_dir",
        type=str,
        default="./output",
        help="Output directory for JSON/CSV exports (default: ./output).",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge new records into existing exports (dedup by foa_id).",
    )

    # Misc
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser.parse_args()


def get_tagger(tagger_type: str, threshold: float = 0.35):
    """Instantiate the selected tagger."""
    if tagger_type == "rule_based":
        return RuleBasedTagger()
    elif tagger_type == "embedding":
        from foa_pipeline.tagging.embedding_tagger import EmbeddingTagger

        return EmbeddingTagger(threshold=threshold)
    elif tagger_type == "hybrid":
        # Hybrid: apply rule-based first, then embedding, merge results
        return None  # handled separately
    else:
        raise ValueError(f"Unknown tagger: {tagger_type}")


def apply_hybrid_tagging(records: List[FOARecord], threshold: float) -> List[FOARecord]:
    """Apply hybrid tagging: rule-based + embedding, merge results."""
    from foa_pipeline.tagging.embedding_tagger import EmbeddingTagger

    rule_tagger = RuleBasedTagger()
    emb_tagger = EmbeddingTagger(threshold=threshold)

    # Apply rule-based tagging
    rule_tagged = rule_tagger.tag_batch(
        [FOARecord.from_dict(r.to_dict()) for r in records]
    )

    # Apply embedding tagging
    emb_tagged = emb_tagger.tag_batch(records)

    # Merge: union of tags from both approaches
    for rule_rec, emb_rec in zip(rule_tagged, emb_tagged):
        emb_rec.tags.research_domains = sorted(
            set(rule_rec.tags.research_domains) | set(emb_rec.tags.research_domains)
        )
        emb_rec.tags.methods = sorted(
            set(rule_rec.tags.methods) | set(emb_rec.tags.methods)
        )
        emb_rec.tags.populations = sorted(
            set(rule_rec.tags.populations) | set(emb_rec.tags.populations)
        )
        emb_rec.tags.sponsor_themes = sorted(
            set(rule_rec.tags.sponsor_themes) | set(emb_rec.tags.sponsor_themes)
        )

    return emb_tagged


def ingest_records(args) -> List[FOARecord]:
    """Ingest FOA records based on CLI arguments."""
    records: List[FOARecord] = []

    if args.url:
        # Single URL fetch
        # Auto-detect source
        if "nsf.gov" in args.url:
            ingestor = NSFIngestor()
        else:
            ingestor = GrantsGovIngestor()
        record = ingestor.fetch_single(args.url)
        if record:
            records.append(record)
        return records

    sources = []
    source = args.source or "grants_gov"
    if source == "all":
        sources = ["grants_gov", "nsf"]
    else:
        sources = [source]

    for src in sources:
        if src == "grants_gov":
            ingestor = GrantsGovIngestor()
        elif src == "nsf":
            ingestor = NSFIngestor()
        else:
            logging.warning("Unknown source: %s", src)
            continue

        if args.query:
            batch = ingestor.search(args.query, limit=args.limit)
        else:
            batch = ingestor.ingest_batch(limit=args.limit)

        records.extend(batch)

    return records


def main():
    args = parse_args()

    logger = logging.getLogger("pipeline")

    setup_logging(args.verbose)

    # Ingestion
    logger.info("Starting FOA pipeline")
    logger.info("args: %s", args)
    records = ingest_records(args)

    if not records:
        logger.warning("No records ingested. Exiting.")
        sys.exit(1)

    logger.info("Ingested %d total records", len(records))

    # Tagging
    logger.info("Applying %s tagging...", args.tagger)
    if args.tagger == "hybrid":
        records = apply_hybrid_tagging(records, args.threshold)
    else:
        tagger = get_tagger(args.tagger, args.threshold)
        records = tagger.tag_batch(records)

    # Count tags
    total_tags = sum(
        len(r.tags.research_domains)
        + len(r.tags.methods)
        + len(r.tags.populations)
        + len(r.tags.sponsor_themes)
        for r in records
    )
    logger.info("Assigned %d total tags across %d records", total_tags, len(records))

    # Export
    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "foa_dataset.json")
    csv_path = os.path.join(args.out_dir, "foa_dataset.csv")

    export_json(records, json_path, merge=args.merge)
    export_csv(records, csv_path)

    logger.info("Pipeline complete!")
    logger.info("  JSON: %s", json_path)
    logger.info("  CSV:  %s", csv_path)

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"FOA Pipeline Complete")
    print(f"{'=' * 50}")
    print(f"  Records ingested: {len(records)}")
    print(f"  Tags assigned:    {total_tags}")
    print(f"  JSON export:      {json_path}")
    print(f"  CSV export:       {csv_path}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
