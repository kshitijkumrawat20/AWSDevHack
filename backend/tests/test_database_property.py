"""Property-based tests for DatabaseManager (Property 8: Idempotent Seed)."""

import os
import tempfile
try:
    from prop_compat import given, st
except ImportError:
    from tests.prop_compat import given, st
from database import DatabaseManager


@given(st.integers(min_value=1, max_value=8))
def test_property_8_idempotent_seed(iterations):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(path)

    try:
        for _ in range(iterations):
            db.init_db()

        products = db.get_all_products()
        assert len(products) == 6, f"Expected 6 products after {iterations} inits, got {len(products)}"
        memory = db.get_memory("default")
        assert "Parents visiting" in memory["context"]
    finally:
        db.close()
        if os.path.exists(path):
            os.remove(path)
