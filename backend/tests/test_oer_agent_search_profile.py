from backend import oer_agent as oer_agent_module
from backend.llm.supabase_client import SupabaseClient


class DummySupabase:
    def is_available(self):
        return False


def _build_agent(monkeypatch):
    monkeypatch.setattr(oer_agent_module, "get_supabase_client", lambda: DummySupabase())
    return oer_agent_module.OERAgent()


def _engl_1101_syllabus():
    return {
        "course_code": "ENGL 1101",
        "course_title": "ENGL 1101",
        "sections": {
            "objectives": """
            Course Outcomes
            Compose expository writing using methods of organization and structure that are clear and appropriate to the form.
            Evaluate texts for their purpose, credibility, sufficiency, accuracy, and bias.
            Identify rhetorical situations used in expository and persuasive writing.
            Practice writing processes, including brainstorming, prewriting, drafting, revising, and reflecting, in academic writing.
            """
        },
    }


def _itec_1001_syllabus():
    return {
        "course_code": "ITEC 1001",
        "course_title": "ITEC 1001",
        "sections": {
            "objectives": """
            Understand the evolution of information technology and future trends.
            Describe computer hardware, software, and networking fundamentals.
            Explain core concepts in information systems and digital literacy.
            """
        },
    }


def _chem_1211k_syllabus():
    return {
        "course_code": "CHEM 1211K",
        "course_title": "CHEM 1211K",
        "sections": {
            "objectives": """
            This course introduces students to chemical concepts and laboratory skills.
            Students analyze atomic structure, chemical bonding, and stoichiometric relationships.
            Learners apply principles of chemical reactions and solution chemistry in lab settings.
            """
        },
    }


def _hist_2111_syllabus():
    return {
        "course_code": "HIST 2111",
        "course_title": "HIST 2111",
        "sections": {
            "objectives": """
            Analyze major events and ideas in United States history from early settlement through Reconstruction.
            Evaluate primary sources and historical arguments about American political and social change.
            Explain the causes and consequences of the Civil War and Reconstruction in the US.
            """
        },
    }


def test_engl_1101_queries_prioritize_english_composition(monkeypatch):
    agent = _build_agent(monkeypatch)

    syllabus_context = agent._syllabus_context_from_info("ENGL 1101", _engl_1101_syllabus())
    query_variants = agent._build_syllabus_queries("ENGL 1101", syllabus_context)

    assert query_variants
    assert "english composition" in query_variants[0].lower()
    assert any("first year composition" in query.lower() for query in query_variants)


def test_itec_1001_queries_stay_anchored_to_intro_it(monkeypatch):
    agent = _build_agent(monkeypatch)

    syllabus_context = agent._syllabus_context_from_info("ITEC 1001", _itec_1001_syllabus())
    query_variants = agent._build_syllabus_queries("ITEC 1001", syllabus_context)

    assert query_variants
    assert "introduction to computing" in query_variants[0].lower()
    # Strict matching should remove generic objective fragments that drift away from IT anchors.
    assert all(
        any(term in query.lower() for term in ["information technology", "computer", "software", "systems", "digital", "networking"])
        for query in query_variants
    )


def test_engl_1101_profile_rejects_meta_alg_entries(monkeypatch):
    agent = _build_agent(monkeypatch)
    syllabus_context = agent._syllabus_context_from_info("ENGL 1101", _engl_1101_syllabus())

    irrelevant = {
        "title": "Research Grant: Comparison of an Open Educational Practice Assignment",
        "description": "Georgia Southern University grant report for a course redesign.",
        "url": "https://alg.manifoldapp.org/projects/grant-report",
        "source": "Open ALG Library",
    }
    relevant = {
        "title": "The Word on College Reading and Writing",
        "description": "An open textbook for college reading, writing, rhetoric, and composition.",
        "url": "https://alg.manifoldapp.org/projects/college-reading-writing",
        "source": "Open ALG Library",
    }

    assert agent._resource_matches_course_profile(irrelevant, syllabus_context) is False
    assert agent._resource_matches_course_profile(relevant, syllabus_context) is True


def test_engl_1101_profile_rejects_foreign_language_false_positive(monkeypatch):
    agent = _build_agent(monkeypatch)
    syllabus_context = agent._syllabus_context_from_info("ENGL 1101", _engl_1101_syllabus())

    french_false_positive = {
        "title": "FREN 1A Elementary French (First Semester)",
        "description": "ALG library result for expository writing rhetorical situation writing process.",
        "url": "https://alg.manifoldapp.org/projects/fren-1a-elementary-french",
        "source": "Open ALG Library",
    }

    assert agent._resource_matches_course_profile(french_false_positive, syllabus_context) is False


def test_itec_1001_profile_rejects_non_it_resources(monkeypatch):
    agent = _build_agent(monkeypatch)
    syllabus_context = agent._syllabus_context_from_info("ITEC 1001", _itec_1001_syllabus())

    irrelevant = {
        "title": "General Chemistry for Scientists and Engineers II",
        "description": "Open chemistry ancillary materials and lab case studies.",
        "url": "https://alg.manifoldapp.org/projects/general-chemistry-case-studies",
        "source": "Open ALG Library",
    }
    relevant = {
        "title": "Introduction to Information Systems Open Textbook",
        "description": "An introduction to information technology and computer systems for college students.",
        "url": "https://alg.manifoldapp.org/projects/introduction-to-information-systems",
        "source": "Open ALG Library",
    }

    assert agent._resource_matches_course_profile(irrelevant, syllabus_context) is False
    assert agent._resource_matches_course_profile(relevant, syllabus_context) is True


def test_chem_1211k_queries_stay_anchored_to_chemistry(monkeypatch):
    agent = _build_agent(monkeypatch)

    syllabus_context = agent._syllabus_context_from_info("CHEM 1211K", _chem_1211k_syllabus())
    query_variants = agent._build_syllabus_queries("CHEM 1211K", syllabus_context)

    assert query_variants
    assert query_variants[0].lower() == "chemistry"
    assert all(
        any(
            term in query.lower()
            for term in ["chemistry", "chemical", "reaction", "stoichiometry", "atomic", "lab"]
        )
        for query in query_variants
    )


def test_hist_2111_queries_prioritize_us_history(monkeypatch):
    agent = _build_agent(monkeypatch)

    syllabus_context = agent._syllabus_context_from_info("HIST 2111", _hist_2111_syllabus())
    query_variants = agent._build_syllabus_queries("HIST 2111", syllabus_context)

    assert query_variants
    assert "us history" in query_variants[0].lower()
    assert all(
        any(term in query.lower() for term in ["history", "us", "united states", "american"])
        for query in query_variants
    )


def test_chem_1211k_profile_rejects_grant_report_artifacts(monkeypatch):
    agent = _build_agent(monkeypatch)
    syllabus_context = agent._syllabus_context_from_info("CHEM 1211K", _chem_1211k_syllabus())

    irrelevant = {
        "title": "2020 Transformation Grant Final Report Summary",
        "description": "Grant final report summary for a program transformation initiative.",
        "url": "https://alg.manifoldapp.org/projects/transformation-grant-summary",
        "source": "Open ALG Library",
    }
    relevant = {
        "title": "General Chemistry Laboratory Manual",
        "description": "Open chemistry laboratory manual covering atomic structure, bonding, and reactions.",
        "url": "https://alg.manifoldapp.org/projects/general-chemistry-lab-manual",
        "source": "Open ALG Library",
    }

    assert agent._resource_matches_course_profile(irrelevant, syllabus_context) is False
    assert agent._resource_matches_course_profile(relevant, syllabus_context) is True


def test_strict_profile_uses_query_metadata_for_sparse_resource_cards(monkeypatch):
    agent = _build_agent(monkeypatch)
    syllabus_context = agent._syllabus_context_from_info("ENGL 1101", _engl_1101_syllabus())

    sparse_but_relevant = {
        "title": "Project Page",
        "description": "Open ALG Library project page.",
        "url": "https://alg.manifoldapp.org/projects/college-writing-reader",
        "source": "Open ALG Library",
        "query": "english composition expository writing rhetoric",
        "source_search_url": "https://alg.manifoldapp.org/search?q=english+composition+expository+writing+rhetoric",
    }

    assert agent._resource_matches_course_profile(sparse_but_relevant, syllabus_context) is True


def test_balances_openalg_and_merlot_when_both_available(monkeypatch):
    agent = _build_agent(monkeypatch)
    ranked = [
        {"title": f"Merlot {idx}", "url": f"https://www.merlot.org/merlot/viewMaterial.htm?materialid={idx}", "source": "MERLOT"}
        for idx in range(1, 7)
    ] + [
        {"title": f"ALG {idx}", "url": f"https://alg.manifoldapp.org/projects/alg-{idx}", "source": "Open ALG Library"}
        for idx in range(1, 5)
    ]

    balanced = agent._balance_primary_source_mix(ranked, limit=6)
    alg_count = sum(1 for item in balanced if item.get("source") == "Open ALG Library")
    merlot_count = sum(1 for item in balanced if item.get("source") == "MERLOT")

    assert len(balanced) == 6
    assert alg_count == 3
    assert merlot_count == 3


def test_missing_saved_resources_table_is_cached_as_optional():
    class MissingTableQuery:
        def select(self, *_args, **_kwargs):
            return self

        def order(self, *_args, **_kwargs):
            return self

        def eq(self, *_args, **_kwargs):
            return self

        def execute(self):
            raise Exception(
                "{'message': \"Could not find the table 'public.saved_resources' in the schema cache\", 'code': 'PGRST205'}"
            )

    client = SupabaseClient.__new__(SupabaseClient)
    client.client = type("FakeClient", (), {"table": lambda self, _name: MissingTableQuery()})()
    client._saved_resources_available = True

    first = client.list_saved_resources("ENGL 1101")
    second = client.list_saved_resources("ENGL 1101")

    assert first == []
    assert second == []
    assert client._saved_resources_available is False
