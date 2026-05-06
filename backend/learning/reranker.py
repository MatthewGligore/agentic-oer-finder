"""Runtime scorer for local logistic-reranker artifacts."""
from __future__ import annotations

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

_DEFAULT_FEATURE_ORDER = [
    'final_rank_score',
    'syllabus_relevance_score',
    'rubric_score',
    'rank_position_inv',
    'is_primary_source',
    'criteria_mean',
    'criteria_min',
    'term_policy_score',
    'query_variant_positive_rate',
]


class Reranker:
    """Load and score with latest reranker model artifact."""

    def __init__(self, model_dir: str = 'backend/learning/model_artifacts'):
        self.model_dir = Path(model_dir)
        self.model = None
        self.feature_names: List[str] = []
        self.metadata: Dict = {}
        self._load_latest()

    def _load_latest(self) -> None:
        if not self.model_dir.exists():
            return
        metadata_files = sorted(self.model_dir.glob('*.metadata.json'))
        if not metadata_files:
            return
        latest = metadata_files[-1]
        try:
            self.metadata = json.loads(latest.read_text())
            model_path = self.model_dir / self.metadata.get('model_file', '')
            if not model_path.exists():
                return
            with open(model_path, 'rb') as fh:
                payload = pickle.load(fh)
            self.model = payload.get('model')
            self.feature_names = payload.get('feature_names', [])
        except Exception as exc:
            logger.warning("Failed to load reranker artifact %s: %s", latest, exc)

    def is_ready(self) -> bool:
        return self.model is not None

    def score(self, feature_payload: Dict) -> float:
        """Return probability-like score for positive feedback."""
        if not self.model:
            return 0.0
        names = self.feature_names or _DEFAULT_FEATURE_ORDER
        row = []
        for name in names:
            if name == 'is_primary_source':
                row.append(float(feature_payload.get('is_primary_source') or 0))
                continue
            row.append(float(feature_payload.get(name, 0) or 0))
        try:
            proba = self.model.predict_proba([row])[0][1]
            return float(proba)
        except Exception as exc:
            logger.warning("Reranker score failed: %s", exc)
            return 0.0
