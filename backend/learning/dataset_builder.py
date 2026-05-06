"""Build reranker training matrices from impression + feedback rows."""
from __future__ import annotations

from typing import Dict, List, Tuple


def build_training_dataset(joined_rows: List[Dict]) -> Tuple[List[List[float]], List[int], List[str]]:
    """Return X, y, feature_names from joined feedback/impression payloads."""
    feature_names = [
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
    x_rows: List[List[float]] = []
    labels: List[int] = []

    for row in joined_rows:
        feedback = row.get('feedback', {}) or {}
        impression = row.get('impression', {}) or {}
        features = impression.get('feature_payload', {}) or {}
        label = _event_label(feedback.get('event_type', ''))
        if label is None:
            continue

        criteria_values = list((features.get('criteria_scores') or {}).values())
        criteria_values = [float(v or 0) for v in criteria_values]
        criteria_mean = sum(criteria_values) / len(criteria_values) if criteria_values else 0.0
        criteria_min = min(criteria_values) if criteria_values else 0.0

        rank_position = float(impression.get('rank_position') or 0)
        x_rows.append([
            float(features.get('final_rank_score') or 0),
            float(features.get('syllabus_relevance_score') or 0),
            float(features.get('rubric_score') or 0),
            1.0 / rank_position if rank_position > 0 else 0.0,
            1.0 if str(features.get('source_tier', '')).lower() == 'primary' else 0.0,
            criteria_mean,
            criteria_min,
            float(features.get('term_policy_score') or 0),
            float(features.get('query_variant_positive_rate') or 0),
        ])
        labels.append(label)

    return x_rows, labels, feature_names


def _event_label(event_type: str) -> int | None:
    positive = {'save', 'thumbs_up', 'manual_override'}
    negative = {'dispute', 'thumbs_down'}
    neutral = {'click', 'open_detail'}
    if event_type in positive:
        return 1
    if event_type in negative:
        return 0
    if event_type in neutral:
        return None
    return None
