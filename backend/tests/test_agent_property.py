"""Property-based tests for AgentOrchestrator (Properties 2, 7, 10)."""

import os
import tempfile
try:
    from prop_compat import given, st
except ImportError:
    from tests.prop_compat import given, st

from agent import AgentOrchestrator
from database import DatabaseManager
from mcp_server import MCPServer
from tools.commerce_tools import ExecuteInstantCheckoutTool, SearchAndBuildCarouselTool
from tools.memory_tools import GetHouseholdMemoryTool, SaveHouseholdMemoryTool
from tools.ring_tools import HandleRingEventTool
from tools.smarthome_tools import UpdateSmarthomeStateTool

VALID_CARD_TYPES = {"carousel", "smarthome_card", "ring_alert_card", "checkout_card", "memory_card"}


def make_agent():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(path)
    db.init_db()

    server = MCPServer(db)
    server.tool_registry.register(GetHouseholdMemoryTool())
    server.tool_registry.register(SaveHouseholdMemoryTool())
    server.tool_registry.register(SearchAndBuildCarouselTool())
    server.tool_registry.register(ExecuteInstantCheckoutTool())
    server.tool_registry.register(UpdateSmarthomeStateTool())
    server.tool_registry.register(HandleRingEventTool())

    agent = AgentOrchestrator(db, server)
    return agent, db, path


@given(st.text(min_size=1, max_size=100))
def test_property_2_memory_first_invocation(message):
    agent, db, path = make_agent()
    try:
        res = agent.orchestrate(message)
        assert len(res.tool_calls) > 0
        assert res.tool_calls[0].name == "get_household_memory"
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)


@given(st.text(min_size=1, max_size=100))
def test_property_7_fallback_independence(message):
    agent, db, path = make_agent()
    try:
        res = agent.smart_fallback(message)
        assert len(res.speech) > 0
        assert isinstance(res.cards, list)
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)


@given(st.text(min_size=1, max_size=100))
def test_property_10_ui_card_types(message):
    agent, db, path = make_agent()
    try:
        res = agent.orchestrate(message)
        for card in res.cards:
            assert card.get("type") in VALID_CARD_TYPES
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)
