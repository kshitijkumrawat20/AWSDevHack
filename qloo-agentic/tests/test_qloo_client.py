import asyncio

from app.qloo_client import QlooClient, QlooAPIError, normalize_entities
from app.agent import OCCASION_SCENES


def test_normalize_qloo_search_entities():
    payload = {"results": {"entities": [{"entity_id": "ABC-123", "name": "Spirited Away", "type": "urn:entity:movie", "properties": {"description": "An animated fantasy film"}}]}}
    results = normalize_entities(payload)
    assert len(results) == 1
    assert results[0]["entity_id"] == "ABC-123"
    assert results[0]["source"] == "Qloo Taste Graph"


def test_normalize_recommendations_keeps_real_affinity():
    payload = {"results": {"entities": [{"entity_id": "XYZ-789", "name": "Example Place", "query": {"affinity": 0.73, "explainability": {"signals": []}}}]}}
    results = normalize_entities(payload, recommendations=True)
    assert results[0]["affinity"] == 0.73
    assert "explainability" in results[0]


def test_normalize_does_not_invent_affinity():
    payload = {"results": {"entities": [{"entity_id": "XYZ-789", "name": "Example"}]}}
    results = normalize_entities(payload, recommendations=True)
    assert "affinity" not in results[0]


def test_search_rejects_unsupported_entity_type_without_network():
    client = QlooClient(api_key="test-key")
    try:
        asyncio.run(client.search_entities("test", "unsupported"))
    except QlooAPIError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Unsupported entity type should raise")


def test_occasion_scene_is_a_suggestion():
    assert OCCASION_SCENES["movie_night"]["brightness"] == 22
    assert OCCASION_SCENES["movie_night"]["temperature"] == "warm"
