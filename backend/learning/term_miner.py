"""Mine OER search query terms from global feedback + impressions."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


_STOPWORDS = frozenset({
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
    'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their', 'there',
    'not', 'no', 'yes', 'so', 'if', 'than', 'then', 'also', 'into', 'about', 'over',
    'http', 'https', 'www', 'com', 'org', 'edu', 'html',
})


def _tokenize_words(text: str) -> List[str]:
    if not text:
        return []
    words = re.findall(r'[a-zA-Z0-9]+', text.lower())
    return [w for w in words if len(w) >= 2 and w not in _STOPWORDS]


def _ngrams_from_words(words: List[str], max_n: int = 3) -> List[str]:
    """Return space-joined n-grams (1..max_n)."""
    out: List[str] = []
    for n in range(1, min(max_n, len(words)) + 1):
        for i in range(0, len(words) - n + 1):
            phrase = ' '.join(words[i : i + n])
            if len(phrase) >= 3:
                out.append(phrase)
    return out


def _extract_terms(*texts: str) -> List[str]:
    bag: List[str] = []
    for text in texts:
        if not text:
            continue
        words = _tokenize_words(text)
        bag.extend(_ngrams_from_words(words))
    # Dedupe preserving order
    seen = set()
    uniq = []
    for t in bag:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _subject_from_course_code(course_code: Optional[str]) -> str:
    if not course_code:
        return 'UNKNOWN'
    parts = str(course_code).strip().upper().split()
    return parts[0] if parts else 'UNKNOWN'


def _feedback_delta(event_type: str) -> Optional[int]:
    positive = {'save', 'thumbs_up', 'manual_override'}
    negative = {'dispute', 'thumbs_down'}
    neutral = {'click', 'open_detail'}
    if event_type in positive:
        return 1
    if event_type in negative:
        return -1
    if event_type in neutral:
        return None
    return None


def mine_term_stats_from_training_rows(joined_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate term counts per course subject from joined feedback + impressions.
    Returns rows suitable for query_term_stats upsert.
    """
    counts: Dict[Tuple[str, str], List[int]] = defaultdict(lambda: [0, 0])

    for row in joined_rows:
        feedback = row.get('feedback') or {}
        impression = row.get('impression') or {}
        event_type = str(feedback.get('event_type') or '')
        delta = _feedback_delta(event_type)
        if delta is None:
            continue

        course_code = feedback.get('course_code') or ''
        subject = _subject_from_course_code(course_code)

        eval_payload = impression.get('evaluation_payload') or {}
        resource = eval_payload.get('resource') or {}
        title = resource.get('title') or ''
        feature_payload = impression.get('feature_payload') or {}
        query_variant = str(feature_payload.get('query_variant') or '')
        reason = str(feedback.get('reason') or '')

        terms = _extract_terms(query_variant, title, reason)
        if not terms:
            continue

        for term in terms:
            key = (subject, term)
            if delta > 0:
                counts[key][0] += 1
            elif delta < 0:
                counts[key][1] += 1

    now = datetime.now(timezone.utc).isoformat()
    out: List[Dict[str, Any]] = []
    for (subject, term), (pos, neg) in counts.items():
        if pos == 0 and neg == 0:
            continue
        weight = float(pos - neg)
        out.append({
            'subject': subject,
            'term': term,
            'positive_count': pos,
            'negative_count': neg,
            'weight': weight,
            'updated_at': now,
        })
    return out


def collect_subjects_from_rows(joined_rows: List[Dict[str, Any]]) -> List[str]:
    subjects = {
        _subject_from_course_code((row.get('feedback') or {}).get('course_code'))
        for row in joined_rows
    }
    return sorted(s for s in subjects if s and s != 'UNKNOWN')


class TermPolicy:
    """Runtime helper: score queries using mined term weights."""

    def __init__(
        self,
        rows: Iterable[Dict[str, Any]],
        suppress_threshold: float = -2.0,
    ):
        self.term_weights: Dict[str, float] = {}
        self.suppress_threshold = suppress_threshold
        for r in rows:
            t = (r.get('term') or '').lower().strip()
            if not t:
                continue
            self.term_weights[t] = float(r.get('weight') or 0)
        self._max_abs_weight = max((abs(w) for w in self.term_weights.values()), default=1.0)

    @classmethod
    def empty(cls, suppress_threshold: float = -2.0) -> 'TermPolicy':
        return cls([], suppress_threshold=suppress_threshold)

    def score(self, query: str) -> float:
        if not query or not self.term_weights:
            return 0.0
        q = query.lower()
        total = 0.0
        for term, w in self.term_weights.items():
            if term and term in q:
                total += w
        return total

    def normalized_score(self, query: str) -> float:
        if self._max_abs_weight <= 0:
            return 0.0
        return self.score(query) / self._max_abs_weight

    def should_drop(self, query: str) -> bool:
        q = query.lower()
        for term, w in self.term_weights.items():
            if w <= self.suppress_threshold and term and term in q:
                return True
        return False

    def boost_terms_top_k(self, k: int) -> List[str]:
        sorted_terms = sorted(self.term_weights.items(), key=lambda x: -x[1])
        return [t for t, w in sorted_terms if w > 0][: max(0, k)]
