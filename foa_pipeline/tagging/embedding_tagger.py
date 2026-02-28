"""
Embedding-Based Tagger — Semantic similarity tagging using sentence embeddings.

Layer 2 of the hybrid tagging pipeline. Uses sentence-transformers to
encode FOA text and ontology label descriptions, then assigns tags
based on cosine similarity above a configurable threshold.

This is a mini RAG classification layer — encode the query (FOA text),
encode the labels (ontology descriptions), compute similarity, threshold.

Model: all-MiniLM-L6-v2 (default, fast, ~80MB)
"""

import logging
from typing import List, Dict, Optional, Tuple

import numpy as np

from foa_pipeline.schema.foa_schema import FOARecord, SemanticTags
from foa_pipeline.ontology.vocabularies import (
    ALL_VOCABULARIES,
    get_descriptions_for_category,
)


logger = logging.getLogger(__name__)


class EmbeddingTagger:
    """Semantic similarity-based tagger using sentence embeddings.

    Encodes FOA descriptions and ontology labels into the same embedding
    space, then assigns tags where cosine similarity exceeds the threshold.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        threshold: float = 0.35,
        max_tags_per_category: int = 5,
    ):
        """
        Args:
            model_name: sentence-transformers model name.
            threshold: Minimum cosine similarity to assign a tag.
            max_tags_per_category: Maximum tags per ontology category.
        """
        self.model_name = model_name
        self.threshold = threshold
        self.max_tags_per_category = max_tags_per_category
        self._model = None
        self._label_embeddings: Dict[str, Dict[str, np.ndarray]] = {}

    @property
    def model(self):
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading model: %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
                self._precompute_label_embeddings()
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embedding-based tagging. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def _precompute_label_embeddings(self):
        """Pre-encode all ontology label descriptions."""
        logger.info("Pre-computing label embeddings for all ontology categories")
        for category in ALL_VOCABULARIES:
            descriptions = get_descriptions_for_category(category)
            if descriptions:
                slugs = list(descriptions.keys())
                texts = list(descriptions.values())
                embeddings = self._model.encode(texts, normalize_embeddings=True)
                self._label_embeddings[category] = {
                    slug: emb for slug, emb in zip(slugs, embeddings)
                }
        logger.info(
            "Label embeddings computed for %d categories",
            len(self._label_embeddings),
        )

    def tag(self, record: FOARecord) -> FOARecord:
        """Apply embedding-based tags to a single FOA record.

        Modifies record.tags in place and returns the record.
        """
        text = self._build_query_text(record)
        if not text.strip():
            logger.warning(
                "Empty text for %s — skipping embedding tagging", record.foa_id
            )
            return record

        # Encode the FOA text
        query_embedding = self.model.encode(text, normalize_embeddings=True)

        # Score against each category
        results = {}
        for category, label_embeddings in self._label_embeddings.items():
            category_tags = self._score_category(
                query_embedding, label_embeddings, category
            )
            results[category] = category_tags

        record.tags = SemanticTags(
            research_domains=results.get("research_domains", []),
            methods=results.get("methods", []),
            populations=results.get("populations", []),
            sponsor_themes=results.get("sponsor_themes", []),
        )

        logger.debug(
            "Embedding tags for %s: %s",
            record.foa_id,
            {k: len(v) for k, v in results.items()},
        )

        return record

    def tag_batch(self, records: List[FOARecord]) -> List[FOARecord]:
        """Apply embedding-based tags to a batch of records.

        Encodes all FOA texts in a single batch for efficiency.
        """
        if not records:
            return records

        # Build all query texts
        texts = [self._build_query_text(r) for r in records]

        # Batch encode
        query_embeddings = self.model.encode(texts, normalize_embeddings=True)

        for record, query_emb in zip(records, query_embeddings):
            results = {}
            for category, label_embeddings in self._label_embeddings.items():
                results[category] = self._score_category(
                    query_emb, label_embeddings, category
                )

            record.tags = SemanticTags(
                research_domains=results.get("research_domains", []),
                methods=results.get("methods", []),
                populations=results.get("populations", []),
                sponsor_themes=results.get("sponsor_themes", []),
            )

        logger.info("Embedding tagging applied to %d records", len(records))
        return records

    def _build_query_text(self, record: FOARecord) -> str:
        """Combine relevant fields into a query string for encoding."""
        parts = [
            record.title or "",
            record.description or "",
        ]
        # Truncate to reasonable length for embedding
        combined = " ".join(parts)
        return combined[:2000]

    def _score_category(
        self,
        query_embedding: np.ndarray,
        label_embeddings: Dict[str, np.ndarray],
        category: str,
    ) -> List[str]:
        """Score a query embedding against all labels in a category.

        Returns human-readable labels for tags above threshold.
        """
        vocab = ALL_VOCABULARIES.get(category, {})
        scores: List[Tuple[str, float]] = []

        for slug, label_emb in label_embeddings.items():
            similarity = float(np.dot(query_embedding, label_emb))
            if similarity >= self.threshold:
                label = vocab[slug]["label"]
                scores.append((label, similarity))

        # Sort by similarity descending, take top N
        scores.sort(key=lambda x: x[1], reverse=True)
        top_tags = [label for label, _ in scores[: self.max_tags_per_category]]

        return sorted(top_tags)

    def get_similarity_scores(
        self, record: FOARecord
    ) -> Dict[str, List[Tuple[str, float]]]:
        """Return raw similarity scores for debugging / evaluation.

        Returns:
            Dict mapping category → list of (label, score) tuples, sorted desc.
        """
        text = self._build_query_text(record)
        query_embedding = self.model.encode(text, normalize_embeddings=True)

        all_scores = {}
        for category, label_embeddings in self._label_embeddings.items():
            vocab = ALL_VOCABULARIES.get(category, {})
            scores = []
            for slug, label_emb in label_embeddings.items():
                similarity = float(np.dot(query_embedding, label_emb))
                label = vocab[slug]["label"]
                scores.append((label, round(similarity, 4)))
            scores.sort(key=lambda x: x[1], reverse=True)
            all_scores[category] = scores

        return all_scores
