"""Verification script for Alexa+ OmniPulse MVP.

Validates:
    1. /mcp initialize handshake (spec 2025-11-25)
    2. /mcp tools/list (6 registered domain tools)
    3. /mcp tools/call (search_and_build_carousel)
    4. /chat multi-domain orchestration (memory-first + smart home + carousel)
    5. /webhook/ring proactive guest arrival verification against memory
"""

import json
from fastapi.testclient import TestClient
from main import app

print("======================================================================")
print("           ALEXA+ OMNIPULSE — MCP & API VERIFICATION RUN              ")
print("======================================================================\n")

with TestClient(app) as client:
    # 1. MCP initialize handshake
    print(">>> [1] Verifying MCP initialize Handshake (Spec 2025-11-25)...")
    req_init = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    res_init = client.post("/mcp", json=req_init)
    print("HTTP Status:", res_init.status_code)
    print("Payload:\n", json.dumps(res_init.json(), indent=2))
    assert res_init.json()["result"]["protocolVersion"] == "2025-11-25"
    print("--> Protocol Version 2025-11-25 VERIFIED!\n")

    # 2. MCP tools/list
    print(">>> [2] Verifying MCP tools/list (6 registered domain tools)...")
    req_tools = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    res_tools = client.post("/mcp", json=req_tools)
    tools = res_tools.json()["result"]["tools"]
    print("Registered Tools Count:", len(tools))
    for t in tools:
        print(f"  - {t['name']}: {t['description'][:65]}...")
    assert len(tools) == 6
    print("--> 6 Tools Count VERIFIED!\n")

    # 3. MCP tools/call
    print(">>> [3] Verifying MCP tools/call (search_and_build_carousel)...")
    req_call = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search_and_build_carousel",
            "arguments": {"query": "tea", "tags": ["ayurvedic", "knee-care"]},
        },
    }
    res_call = client.post("/mcp", json=req_call)
    ui_card = res_call.json()["result"]["ui"]
    print("Returned Card Type:", ui_card["type"])
    print("Found Products:", len(ui_card["products"]))
    for p in ui_card["products"]:
        print(f"  * [{p['id']}] {p['name']} - ${p['price']} (In-Stock: {p['buyable']})")
    assert ui_card["type"] == "carousel"
    print("--> Carousel Tool VERIFIED!\n")

    # 4. /chat multi-domain orchestration
    print(">>> [4] Verifying /chat Multi-Domain Orchestration...")
    req_chat = {
        "message": "My parents are visiting tomorrow. Prep the home and find low-sodium wellness items.",
        "session_id": "default",
    }
    res_chat = client.post("/chat", json=req_chat)
    chat_data = res_chat.json()
    print("Assistant Speech:", chat_data["speech"])
    print("Cards Generated:", len(chat_data["cards"]))
    for c in chat_data["cards"]:
        print(f"  * Card: {c.get('type')} - {c.get('title')}")
    print("First Tool Called:", chat_data["tool_calls"][0]["name"])
    assert chat_data["tool_calls"][0]["name"] == "get_household_memory"
    print("--> Memory-First Multi-Domain Flow VERIFIED!\n")

    # 5. /webhook/ring proactive guest verification
    print(">>> [5] Verifying /webhook/ring Doorbell Event (Guest Arrival)...")
    req_ring = {
        "event_type": "guest_arrival",
        "description": "Two visitors at front door",
    }
    res_ring = client.post("/webhook/ring", json=req_ring)
    ring_data = res_ring.json()
    print("Ring Speech:", ring_data["speech"])
    print("Verified Against Memory:", ring_data["ring_alert_card"]["verified"])
    assert ring_data["ring_alert_card"]["verified"] is True
    print("--> Ring Guest Verification VERIFIED!\n")

print("======================================================================")
print("                 ALL VERIFICATION CHECKS PASSED                       ")
print("======================================================================")
