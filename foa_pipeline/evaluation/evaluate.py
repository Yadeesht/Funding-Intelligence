"""
Evaluation Module — Measures tagging consistency and accuracy.

Computes precision, recall, F1, and inter-approach agreement
against the gold-standard evaluation dataset.

Usage:
    python -m foa_pipeline.evaluation.evaluate
    python -m foa_pipeline.evaluation.evaluate --tagger embedding --threshold 0.3
"""

import json
import logging
import os
from typing import Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from foa_pipeline.schema.foa_schema import FOARecord, SemanticTags
from foa_pipeline.tagging.rule_based import RuleBasedTagger


logger = logging.getLogger(__name__)

GOLD_DATASET_PATH = os.path.join(os.path.dirname(__file__), "gold_dataset.json")


@dataclass
class CategoryMetrics:
    """Precision / Recall / F1 for one tag category."""

    category: str
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int


@dataclass
class EvaluationReport:
    """Full evaluation report across all categories."""

    category_metrics: List[CategoryMetrics]
    macro_precision: float
    macro_recall: float
    macro_f1: float
    total_records: int

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "FOA Tagging Evaluation Report",
            "=" * 60,
            f"Total evaluation records: {self.total_records}",
            "",
        ]
        for cm in self.category_metrics:
            lines.append(
                f"  {cm.category:25s}  P={cm.precision:.3f}  R={cm.recall:.3f}  "
                f"F1={cm.f1:.3f}  (TP={cm.true_positives}, FP={cm.false_positives}, FN={cm.false_negatives})"
            )
        lines.extend(
            [
                "",
                f"  {'MACRO AVERAGE':25s}  P={self.macro_precision:.3f}  R={self.macro_recall:.3f}  F1={self.macro_f1:.3f}",
                "=" * 60,
            ]
        )
        return "\n".join(lines)


def load_gold_dataset(path: str = GOLD_DATASET_PATH) -> List[dict]:
    """Load the gold-standard evaluation dataset."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_metrics(
    predicted: List[str], expected: List[str]
) -> Tuple[float, float, float, int, int, int]:
    """Compute precision, recall, F1 for a single tag set.

    Returns:
        (precision, recall, f1, true_positives, false_positives, false_negatives)
    """
    pred_set = set(predicted)
    exp_set = set(expected)

    tp = len(pred_set & exp_set)
    fp = len(pred_set - exp_set)
    fn = len(exp_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if len(exp_set) == 0 else 0.0)
    recall = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if len(pred_set) == 0 else 0.0)
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return precision, recall, f1, tp, fp, fn


def evaluate_tagging(
    tagger_type: str = "rule_based",
    embedding_threshold: float = 0.35,
    gold_path: str = GOLD_DATASET_PATH,
) -> EvaluationReport:
    """Run full evaluation of a tagger against the gold dataset.

    Args:
        tagger_type: "rule_based" or "embedding".
        embedding_threshold: Similarity threshold (only for embedding tagger).
        gold_path: Path to gold dataset JSON.

    Returns:
        EvaluationReport with per-category and macro metrics.
    """
    gold_data = load_gold_dataset(gold_path)

    # Initialize tagger
    if tagger_type == "rule_based":
        tagger = RuleBasedTagger()
    elif tagger_type == "embedding":
        from foa_pipeline.tagging.embedding_tagger import EmbeddingTagger

        tagger = EmbeddingTagger(threshold=embedding_threshold)
    else:
        raise ValueError(f"Unknown tagger type: {tagger_type}")

    # Build FOARecords from gold data
    records = []
    for item in gold_data:
        record = FOARecord(
            foa_id=item["foa_id"],
            title=item["title"],
            description=item["description"],
            source="evaluation",
        )
        records.append(record)

    # Tag records
    if hasattr(tagger, "tag_batch"):
        tagged_records = tagger.tag_batch(records)
    else:
        tagged_records = [tagger.tag(r) for r in records]

    # Evaluate per category
    categories = ["research_domains", "methods", "populations", "sponsor_themes"]
    category_metrics = []

    for category in categories:
        total_p, total_r, total_f1 = 0.0, 0.0, 0.0
        total_tp, total_fp, total_fn = 0, 0, 0

        for tagged_record, gold_item in zip(tagged_records, gold_data):
            predicted = getattr(tagged_record.tags, category, [])
            expected = gold_item["expected_tags"].get(category, [])

            p, r, f1, tp, fp, fn = compute_metrics(predicted, expected)
            total_p += p
            total_r += r
            total_f1 += f1
            total_tp += tp
            total_fp += fp
            total_fn += fn

        n = len(gold_data)
        category_metrics.append(
            CategoryMetrics(
                category=category,
                precision=total_p / n,
                recall=total_r / n,
                f1=total_f1 / n,
                true_positives=total_tp,
                false_positives=total_fp,
                false_negatives=total_fn,
            )
        )

    # Macro averages
    macro_p = sum(cm.precision for cm in category_metrics) / len(category_metrics)
    macro_r = sum(cm.recall for cm in category_metrics) / len(category_metrics)
    macro_f1 = sum(cm.f1 for cm in category_metrics) / len(category_metrics)

    return EvaluationReport(
        category_metrics=category_metrics,
        macro_precision=macro_p,
        macro_recall=macro_r,
        macro_f1=macro_f1,
        total_records=len(gold_data),
    )


def main():
    """Run evaluation from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate FOA tagging accuracy")
    parser.add_argument(
        "--tagger",
        choices=["rule_based", "embedding"],
        default="rule_based",
        help="Which tagger to evaluate (default: rule_based)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.35,
        help="Embedding similarity threshold (default: 0.35)",
    )
    parser.add_argument(
        "--gold-path",
        default=GOLD_DATASET_PATH,
        help="Path to gold dataset JSON",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    report = evaluate_tagging(
        tagger_type=args.tagger,
        embedding_threshold=args.threshold,
        gold_path=args.gold_path,
    )
    print(report.summary())


if __name__ == "__main__":
    main()
