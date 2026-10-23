"""Integration tests for FastAPI endpoints (Property 9: Frontend HTTP)."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_mcp_initialize(client):
    req = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert data["result"]["protocolVersion"] == "2025-11-25"


def test_mcp_tools_list(client):
    req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["result"]["tools"]) == 6


def test_mcp_tools_call_carousel(client):
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "search_and_build_carousel", "arguments": {"query": "tea"}},
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["ui"]["type"] == "carousel"


def test_mcp_sse_accept_header(client):
    req = {"jsonrpc": "2.0", "id": 4, "method": "initialize"}
    resp = client.post("/mcp", json=req, headers={"Accept": "text/event-stream"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
    assert "2025-11-25" in resp.text


def test_chat_multi_domain(client):
    req = {"message": "prep the home and find low-sodium items", "session_id": "default"}
    resp = client.post("/chat", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["speech"]) > 0
    assert len(data["cards"]) >= 2
    types = [c["type"] for c in data["cards"]]
    assert "smarthome_card" in types
    assert "carousel" in types


def test_chat_checkout(client):
    req = {"message": "checkout product 1 and product 2", "session_id": "default"}
    resp = client.post("/chat", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert any(c["type"] == "checkout_card" for c in data["cards"])


def test_ring_webhook_guest_arrival(client):
    req = {"event_type": "guest_arrival", "description": "Parents arriving at front porch"}
    resp = client.post("/webhook/ring", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ring_alert_card"]["verified"] is True
    assert "unlocked" in data["speech"].lower() or "verified" in data["speech"].lower()


def test_ring_webhook_invalid_event(client):
    req = {"event_type": "alien_invasion", "description": "Unknown"}
    resp = client.post("/webhook/ring", json=req)
    assert resp.status_code == 400
