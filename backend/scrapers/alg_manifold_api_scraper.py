"""
Best-effort OpenALG Manifold API scraper.
Falls back to other scrapers if the public API is unavailable.
"""
from typing import Dict, List
import logging
import requests

logger = logging.getLogger(__name__)


class ALGManifoldAPIScraper:
    """Fetch OpenALG resources from Manifold API endpoints when available."""

    def __init__(self, base_url: str = "https://alg.manifoldapp.org"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 8

    def search_resources(self, query: str, course_code: str = "") -> List[Dict]:
        query = (query or "").strip()
        if not query:
            return []

        for endpoint in ("/api/v1/projects", "/api/public/projects"):
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    params={"filter[search]": query, "per_page": 20},
                    timeout=self.timeout,
                )
                if not response.ok:
                    continue
                payload = response.json()
                records = payload.get("data") if isinstance(payload, dict) else payload
                if not isinstance(records, list):
                    continue

                resources: List[Dict] = []
                for item in records:
                    attributes = item.get("attributes", {}) if isinstance(item, dict) else {}
                    title = attributes.get("title") or item.get("title")
                    slug = attributes.get("slug") or item.get("slug")
                    if not title or not slug:
                        continue
                    resources.append(
                        {
                            "title": title,
                            "description": attributes.get("subtitle") or attributes.get("description") or "",
                            "url": f"{self.base_url}/projects/{slug}",
                            "source": "Open ALG Library",
                            "source_platform": "Open ALG Library",
                            "query": query,
                        }
                    )
                if resources:
                    return resources
            except Exception as exc:
                logger.debug("OpenALG Manifold API endpoint %s failed: %s", endpoint, exc)
        return []
