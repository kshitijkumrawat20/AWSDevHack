"""Property-based tests for MCP domain tools (Properties 4, 5, 6)."""

import os
import tempfile
import pytest
try:
    from prop_compat import given, st
except ImportError:
    from tests.prop_compat import given, st

from database import DatabaseManager
from tools.commerce_tools import ExecuteInstantCheckoutTool, SearchAndBuildCarouselTool
from tools.ring_tools import HandleRingEventTool


@pytest.fixture(scope="module")
def shared_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(path)
    db.init_db()
    yield db
    db.close()
    if os.path.exists(path):
        os.remove(path)


@given(st.lists(st.sampled_from([1, 2, 3, 4, 5, 6]), min_size=1, max_size=5))
def test_property_4_checkout_total_consistency(product_ids):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(path)
    db.init_db()
    try:
        checkout_tool = ExecuteInstantCheckoutTool()
        expected_total = sum(db.get_product(pid)["price"] for pid in product_ids)
        res = checkout_tool.execute({"product_ids": product_ids}, db)
        assert round(res["ui"]["total"], 2) == round(expected_total, 2)
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)


@given(st.text(min_size=1, max_size=30))
def test_property_5_carousel_stock_invariant(query):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(path)
    db.init_db()
    try:
        carousel_tool = SearchAndBuildCarouselTool()
        res = carousel_tool.execute({"query": query, "tags": []}, db)
        for prod in res["ui"]["products"]:
            assert prod["buyable"] is True
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)


@given(st.text(min_size=1, max_size=100))
def test_property_6_ring_verification(context_text):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(path)
    db.init_db()
    try:
        db.save_memory("default", context=context_text)
        tool = HandleRingEventTool()
        res = tool.execute({"event_type": "guest_arrival", "description": "Doorbell ring"}, db)
        mentions_guest = any(
            kw in context_text.lower() for kw in ["parents visiting", "guest", "parent"]
        )
        assert res["ui"]["verified"] == mentions_guest
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)
