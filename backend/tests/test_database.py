"""Unit tests for DatabaseManager in backend/database.py."""

import os
import tempfile
import pytest
from database import DatabaseManager


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


def test_init_db_creates_tables(temp_db):
    cur = temp_db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    expected = {"household_memory", "products", "device_states", "ring_events", "orders"}
    assert expected.issubset(tables)


def test_seed_products_count(temp_db):
    products = temp_db.get_all_products()
    assert len(products) == 6
    names = [p["name"] for p in products]
    assert "Ashwagandha Root Extract" in names
    assert "Low-Sodium Turmeric Latte Mix" in names


def test_seed_household_memory(temp_db):
    memory = temp_db.get_memory("default")
    assert "Parents visiting" in memory["context"]
    assert "father has knee pain" in memory["health_notes"]
    assert "low-sodium" in memory["dietary_restrictions"]
    assert memory["preferences"]["lighting"] == "warm"


def test_seed_device_states(temp_db):
    devices = temp_db.get_device_states()
    assert len(devices) >= 2
    dev_ids = [d["device_id"] for d in devices]
    assert "living_room_light" in dev_ids
    assert "thermostat" in dev_ids


def test_search_products(temp_db):
    matches = temp_db.search_products("turmeric")
    assert len(matches) >= 1
    assert any("Turmeric" in m["name"] for m in matches)

    tag_matches = temp_db.search_products("", tags=["ayurvedic"])
    assert len(tag_matches) >= 2


def test_get_product_not_found(temp_db):
    p = temp_db.get_product(9999)
    assert p is None


def test_create_order(temp_db):
    order = temp_db.create_order([1, 2])
    assert order["id"] > 0
    assert len(order["product_ids"]) == 2
    assert order["total"] > 0
    assert order["status"] == "confirmed"
