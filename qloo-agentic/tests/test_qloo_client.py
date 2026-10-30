from app.qloo_client import normalize_entities
from app.agent import OCCASION_SCENES


def test_normalize_qloo_search_entities():
    payload = {"results": {"entities": [{"entity_id": "ABC-123", "name": "Spirited Away", "type": "urn:entity:movie", "properties": {"description": "An animated fantasy film"}}]}}
    results = normalize_entities(payload)
    assert len(results) == 1
    assert results[0]["entity_id"] == "ABC-123"
    assert results[0]["source"] == "Qloo Taste Graph"


def test_normalize_recommendations_keeps_real_affinity():
    payload = {"results": {"entities": [{"entity_id": "XYZ-789", "name": "Example Place", "query": {"affinity": 0.73}}]}}
    results = normalize_entities(payload, recommendations=True)
    assert results[0]["affinity"] == 0.73


def test_occasion_scene_is_a_suggestion():
    assert OCCASION_SCENES["movie_night"]["brightness"] == 22
    assert OCCASION_SCENES["movie_night"]["temperature"] == "warm"
