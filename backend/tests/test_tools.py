"""Unit tests for all 6 domain tools in backend/tools/."""

import os
import tempfile
import pytest

from database import DatabaseManager
from tools.commerce_tools import ExecuteInstantCheckoutTool, SearchAndBuildCarouselTool
from tools.memory_tools import GetHouseholdMemoryTool, SaveHouseholdMemoryTool
from tools.ring_tools import HandleRingEventTool
from tools.smarthome_tools import UpdateSmarthomeStateTool


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(path)
    db.init_db()
    yield db
    db.close()
    if os.path.exists(path):
        os.remove(path)


def test_get_and_save_memory_tool(temp_db):
    get_tool = GetHouseholdMemoryTool()
    save_tool = SaveHouseholdMemoryTool()

    # Seeded read
    res = get_tool.execute({"session_id": "default"}, temp_db)
    assert "Parents visiting" in res["content"][0]["text"]
    assert res["ui"]["type"] == "memory_card"

    # Save new
    save_tool.execute(
        {
            "session_id": "user123",
            "context": "Prefers vegan snacks",
            "health_notes": ["allergy to peanuts"],
            "dietary_restrictions": ["vegan"],
            "preferences": {"lighting": "cool"},
        },
        temp_db,
    )
    res2 = get_tool.execute({"session_id": "user123"}, temp_db)
    assert "vegan" in res2["content"][0]["text"].lower()


def test_commerce_tools(temp_db):
    carousel_tool = SearchAndBuildCarouselTool()
    checkout_tool = ExecuteInstantCheckoutTool()

    # Search
    c_res = carousel_tool.execute({"query": "tea", "tags": ["ayurvedic"]}, temp_db)
    assert c_res["ui"]["type"] == "carousel"
    assert len(c_res["ui"]["products"]) >= 1
    assert all(p["buyable"] for p in c_res["ui"]["products"])

    # Empty search
    c_empty = carousel_tool.execute({"query": "non_existent_xyz", "tags": []}, temp_db)
    assert len(c_empty["ui"]["products"]) == 0

    # Checkout valid
    ch_res = checkout_tool.execute({"product_ids": [1, 2]}, temp_db)
    assert ch_res["ui"]["type"] == "checkout_card"
    assert ch_res["ui"]["total"] > 0
    assert len(ch_res["ui"]["items"]) == 2

    # Checkout invalid
    ch_err = checkout_tool.execute({"product_ids": [9999]}, temp_db)
    assert ch_err["ui"]["title"] == "Checkout Error"


def test_smarthome_tools(temp_db):
    tool = UpdateSmarthomeStateTool()

    # Light update
    res = tool.execute(
        {"device": "living_room_light", "state": {"on": True, "brightness": 60, "color": "warm"}},
        temp_db,
    )
    assert res["ui"]["type"] == "smarthome_card"

    # HVAC update
    res2 = tool.execute(
        {"device": "thermostat", "state": {"on": True, "temperature": 72, "mode": "heat"}},
        temp_db,
    )
    assert res2["ui"]["type"] == "smarthome_card"


def test_ring_tool(temp_db):
    tool = HandleRingEventTool()

    # Guest arrival with memory mentioning parents -> verified == True
    res_guest = tool.execute({"event_type": "guest_arrival", "description": "Guests at door"}, temp_db)
    assert res_guest["ui"]["type"] == "ring_alert_card"
    assert res_guest["ui"]["verified"] is True

    # Package delivery -> verified == True
    res_pkg = tool.execute({"event_type": "package_delivery", "description": "Amazon delivery"}, temp_db)
    assert res_pkg["ui"]["verified"] is True
