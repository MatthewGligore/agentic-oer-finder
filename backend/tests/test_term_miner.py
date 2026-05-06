"""Tests for query term mining and term policy."""
from backend.learning.term_miner import TermPolicy, mine_term_stats_from_training_rows


def test_mine_term_stats_aggregates_by_subject():
    joined = [
        {
            'feedback': {
                'event_type': 'save',
                'course_code': 'ENGL 1101',
                'reason': '',
            },
            'impression': {
                'feature_payload': {'query_variant': 'rhetoric composition OER'},
                'evaluation_payload': {'resource': {'title': 'Rhetoric Reader'}},
            },
        },
        {
            'feedback': {
                'event_type': 'dispute',
                'course_code': 'ENGL 1101',
                'reason': 'too much focus on grammar worksheets',
            },
            'impression': {
                'feature_payload': {'query_variant': 'grammar worksheets'},
                'evaluation_payload': {'resource': {'title': 'Grammar Drills'}},
            },
        },
    ]
    rows = mine_term_stats_from_training_rows(joined)
    assert rows
    by_term = {(r['subject'], r['term']): r for r in rows}
    assert ('ENGL', 'rhetoric') in by_term or any('rhetoric' in r['term'] for r in rows)
    engl_rows = [r for r in rows if r['subject'] == 'ENGL']
    assert engl_rows


def test_term_policy_score_and_suppress():
    policy = TermPolicy(
        [
            {'term': 'rhetoric', 'weight': 3.0},
            {'term': 'bad term', 'weight': -3.0},
        ],
        suppress_threshold=-2.0,
    )
    assert policy.score('rhetoric open resources') == 3.0
    assert policy.should_drop('use bad term here') is True
    assert policy.should_drop('rhetoric only') is False
    assert policy.normalized_score('rhetoric') == 1.0
