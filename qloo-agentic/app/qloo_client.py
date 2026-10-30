"""Server-side Qloo Insights API client. Never exposes credentials or raw errors."""
from __future__ import annotations
import os
from typing import Any
import httpx
from dotenv import load_dotenv

load_dotenv()

QLOO_TYPES = {
    "movie": "urn:entity:movie", "tv_show": "urn:entity:tv_show",
    "artist": "urn:entity:artist", "book": "urn:entity:book",
    "brand": "urn:entity:brand", "videogame": "urn:entity:videogame",
}
TARGET_TYPES = {
    "place": "urn:entity:place", "movie": "urn:entity:movie",
    "artist": "urn:entity:artist",
}

class QlooAPIError(RuntimeError):
    """Sanitized API error; never contains request headers or API credentials."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

class QlooClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = (api_key if api_key is not None else os.getenv("QLOO_API_KEY", "")).strip()
        self.base_url = (base_url or os.getenv("QLOO_BASE_URL", "https://hackathon.api.qloo.com")).rstrip("/")
        self.timeout = float(os.getenv("QLOO_TIMEOUT_SECONDS", "20"))

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            raise QlooAPIError("Qloo API key is not configured on the server.")
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers={"X-Api-Key": self.api_key, "Accept": "application/json"},
                timeout=self.timeout,
                follow_redirects=False,
            ) as client:
                response = await client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise QlooAPIError("Qloo request timed out. Try again in a moment.") from exc
        except httpx.RequestError as exc:
            raise QlooAPIError("Could not connect to the Qloo API.") from exc
        if response.status_code == 401:
            raise QlooAPIError("Qloo rejected the configured API key. Check the event-issued key.", 401)
        if response.status_code == 403:
            raise QlooAPIError("Qloo denied this request. Check that the event key has access.", 403)
        if response.status_code == 429:
            raise QlooAPIError("Qloo rate limit reached. Wait briefly before trying again.", 429)
        if response.is_error:
            raise QlooAPIError(f"Qloo returned HTTP {response.status_code} for this request.", response.status_code)
        try:
            payload = response.json()
        except ValueError as exc:
            raise QlooAPIError("Qloo returned a response that was not valid JSON.", response.status_code) from exc
        if not isinstance(payload, dict):
            raise QlooAPIError("Qloo returned an unexpected response shape.", response.status_code)
        return payload

    async def search_entities(self, query: str, entity_kind: str, take: int = 8) -> list[dict[str, Any]]:
        if entity_kind not in QLOO_TYPES:
            raise QlooAPIError("Unsupported Qloo entity category.")
        payload = await self._get("/search", {
            "query": query.strip(), "types": QLOO_TYPES[entity_kind],
            "take": max(1, min(take, 12)),
        })
        return normalize_entities(payload)

    async def recommend(self, target_kind: str, seed_entity_ids: list[str],
                        city: str | None = None, take: int = 6) -> list[dict[str, Any]]:
        if target_kind not in TARGET_TYPES:
            raise QlooAPIError("Unsupported recommendation category.")
        if not seed_entity_ids:
            raise QlooAPIError("At least one confirmed taste signal is required.")
        params: dict[str, Any] = {
            "filter.type": TARGET_TYPES[target_kind],
            "signal.interests.entities": ",".join(seed_entity_ids[:3]),
            "filter.exclude.entities": ",".join(seed_entity_ids[:3]),
            "feature.explainability": "true",
            "take": max(1, min(take, 10)),
        }
        if target_kind == "place" and city:
            params["filter.location.query"] = city.strip()
        payload = await self._get("/v2/insights", params)
        return normalize_entities(payload, recommendations=True)

def _candidate_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results", {})
    if isinstance(results, list):
        return [x for x in results if isinstance(x, dict)]
    if isinstance(results, dict):
        for key in ("entities", "results", "items"):
            value = results.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    for key in ("entities", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    return []

def normalize_entities(payload: dict[str, Any], recommendations: bool = False) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in _candidate_list(payload):
        entity_id = item.get("entity_id") or item.get("id") or item.get("qid")
        name = item.get("name") or item.get("title")
        if not entity_id or not name:
            continue
        properties = item.get("properties") if isinstance(item.get("properties"), dict) else {}
        image_value = properties.get("image")
        image_url = image_value.get("url") if isinstance(image_value, dict) else image_value if isinstance(image_value, str) else None
        description = properties.get("description") or item.get("description")
        query_data = item.get("query") if isinstance(item.get("query"), dict) else {}
        affinity = query_data.get("affinity", item.get("affinity"))
        record: dict[str, Any] = {
            "entity_id": str(entity_id), "name": str(name),
            "type": item.get("type") or item.get("subtype"),
            "image_url": image_url,
            "description": str(description)[:280] if description else None,
            "source": "Qloo Taste Graph",
        }
        if recommendations:
            if isinstance(affinity, (int, float)):
                record["affinity"] = float(affinity)
            if query_data.get("explainability") is not None:
                record["explainability"] = query_data["explainability"]
        normalized.append(record)
    return normalized
