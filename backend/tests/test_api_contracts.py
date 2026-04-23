import pytest

from backend import app as app_module


@pytest.fixture()
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


class DummySupabase:
    def __init__(self):
        self.saved = []
        self.syllabuses = []

    def is_available(self):
        return True

    def fetch_syllabus_by_url(self, _url):
        return None

    def insert_syllabus(self, payload):
        return {"id": "syll-1", **payload}

    def insert_sections_batch(self, payload):
        return len(payload)

    def fetch_syllabuses_by_course_code(self, _course_code, _term=None):
        return self.syllabuses

    def list_saved_resources(self, course_code=None):
        if not course_code:
            return list(self.saved)
        return [row for row in self.saved if row["course_code"] == course_code]

    def upsert_saved_resource(self, row):
        existing = next((item for item in self.saved if item["course_code"] == row["course_code"] and item["resource_url"] == row["resource_url"]), None)
        if existing:
            existing.update(row)
            return existing
        new_row = {"id": f"saved-{len(self.saved)+1}", **row}
        self.saved.append(new_row)
        return new_row

    def delete_saved_resource(self, resource_id):
        original = len(self.saved)
        self.saved = [item for item in self.saved if item["id"] != resource_id]
        return len(self.saved) != original


class DummyAgent:
    def __init__(self, response):
        self.response = response

    def find_oer_for_course(self, _course_code, _term=None):
        return self.response


def test_search_rejects_malformed_course(client):
    response = client.post("/api/search", json={"course_code": "bad"})
    assert response.status_code == 400


def test_search_requires_scrape_when_missing_syllabus(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_agent", lambda: DummyAgent({"scrape_required": True, "error": "missing"}))
    response = client.post("/api/search", json={"course_code": "ENGL 1101"})
    assert response.status_code == 409
    assert response.get_json()["scrape_ui_path"] == "/scrape"


def test_search_returns_ranked_top_10(client, monkeypatch):
    raw_resources = []
    for idx in range(12):
        raw_resources.append(
            {
                "resource": {"title": f"R{idx}", "description": "d", "url": f"https://x/{idx}", "source": "Open ALG Library"},
                "final_rank_score": 4.5,
                "license_check": {"license_type": "CC BY"},
                "syllabus_relevance": {"rationale": "good fit"},
                "rubric_evaluation": {"criteria_evaluations": {"Content Quality": {"score": 4, "explanation": "ok"}}},
            }
        )
    monkeypatch.setattr(app_module, "get_agent", lambda: DummyAgent({"course_code": "ENGL 1101", "evaluated_resources": raw_resources, "resources_found": 12}))
    response = client.post("/api/search", json={"course_code": "ENGL 1101"})
    assert response.status_code == 200
    assert len(response.get_json()["results"]) == 10


def test_ollama_unavailable_returns_503(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_agent", lambda: DummyAgent({"error": "OLLAMA_UNAVAILABLE"}))
    response = client.post("/api/search", json={"course_code": "ENGL 1101"})
    assert response.status_code == 503


def test_saved_resources_crud(client, monkeypatch):
    sb = DummySupabase()
    monkeypatch.setattr(app_module, "get_supabase_client", lambda: sb)

    created = client.post(
        "/api/saved-resources",
        json={
            "course_code": "ENGL 1101",
            "resource_url": "https://example.com/book",
            "title": "Book",
            "description": "Desc",
            "source": "Open ALG Library",
        },
    )
    assert created.status_code == 200
    created_id = created.get_json()["id"]

    listed = client.get("/api/saved-resources")
    assert listed.status_code == 200
    assert len(listed.get_json()["saved_resources"]) == 1

    deleted = client.delete(f"/api/saved-resources/{created_id}")
    assert deleted.status_code == 200


def test_scrape_contracts(client, monkeypatch):
    sb = DummySupabase()
    monkeypatch.setattr(app_module, "get_supabase_client", lambda: sb)

    malformed = client.post("/api/scrape-syllabi", json={"course_code": "bad"})
    assert malformed.status_code == 400

    monkeypatch.setattr(app_module, "fetch_library_index_for_course", lambda _code: [])
    monkeypatch.setattr(app_module, "fetch_library_index", lambda: [{"course_code": "ENGL 1102", "term": "Fall", "syllabus_url": "https://x"}])
    not_found = client.post("/api/scrape-syllabi", json={"course_code": "ENGL 1101"})
    assert not_found.status_code == 404
    assert isinstance(not_found.get_json().get("suggested_course_codes"), list)


def test_scrape_syllabi_applies_demo_cap(client, monkeypatch):
    sb = DummySupabase()
    monkeypatch.setattr(app_module, "get_supabase_client", lambda: sb)
    monkeypatch.setattr(app_module, "fetch_and_parse_syllabus", lambda _url: {})
    monkeypatch.setattr(app_module, "prepare_section_records", lambda _id, _sections: [])

    discovered = [
        {
            "course_code": "ENGL 1101",
            "term": "Fall 2025",
            "syllabus_url": f"https://example.com/syllabi/{idx}",
            "course_id": f"CID-{idx}",
            "section_number": str(idx),
            "instructor_name": "Instructor",
        }
        for idx in range(12)
    ]
    monkeypatch.setattr(app_module, "fetch_library_index_for_course", lambda _code: discovered)

    response = client.post("/api/scrape-syllabi", json={"course_code": "ENGL 1101"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["matched_count"] == 10
    assert payload["inserted_syllabuses"] == 10
