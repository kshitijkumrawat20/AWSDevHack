"""Unit tests for AgentOrchestrator in backend/agent.py."""

import os
import tempfile
import pytest

from agent import AgentOrchestrator
from database import DatabaseManager
from mcp_server import MCPServer
from tools.commerce_tools import ExecuteInstantCheckoutTool, SearchAndBuildCarouselTool
from tools.memory_tools import GetHouseholdMemoryTool, SaveHouseholdMemoryTool
from tools.ring_tools import HandleRingEventTool
from tools.smarthome_tools import UpdateSmarthomeStateTool


@pytest.fixture
def agent_fixture():
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
    yield agent, db
    db.close()
    if os.path.exists(path):
        os.remove(path)


def test_memory_first_invocation(agent_fixture):
    agent, _ = agent_fixture
    res = agent.orchestrate("prep the home")
    assert len(res.tool_calls) > 0
    assert res.tool_calls[0].name == "get_household_memory"


def test_smarthome_only_command(agent_fixture):
    agent, _ = agent_fixture
    res = agent.orchestrate("turn on the living room lights")
    assert any(c["type"] == "smarthome_card" for c in res.cards)
    assert "lighting" in res.speech.lower() or "adjusted" in res.speech.lower()


def test_commerce_only_command(agent_fixture):
    agent, _ = agent_fixture
    res = agent.orchestrate("search for low-sodium ayurvedic items")
    assert any(c["type"] == "carousel" for c in res.cards)
    assert "wellness" in res.speech.lower() or "found" in res.speech.lower()


def test_checkout_command(agent_fixture):
    agent, _ = agent_fixture
    res = agent.orchestrate("checkout product 1 and product 2")
    assert any(c["type"] == "checkout_card" for c in res.cards)
    assert "order" in res.speech.lower() or "confirmed" in res.speech.lower()


def test_multi_domain_command(agent_fixture):
    agent, _ = agent_fixture
    res = agent.orchestrate("prep the home for parents and find low-sodium wellness items")
    card_types = [c["type"] for c in res.cards]
    assert "smarthome_card" in card_types
    assert "carousel" in card_types


def test_empty_or_unknown_intent(agent_fixture):
    agent, _ = agent_fixture
    res = agent.orchestrate("hello there")
    assert len(res.speech) > 0
    assert "help" in res.speech.lower()
