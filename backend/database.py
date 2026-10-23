"""SQLite persistence layer for Alexa+ OmniPulse.

Implements :class:`DatabaseManager`, a zero-config SQLite-backed store for
cross-session household memory, the product catalog, smart home device
state, Ring event logs, and checkout orders.

Design references:
    - design.md §Component 4 (DatabaseManager)
    - design.md §Algorithm 5 / §Function 5 (init_db postconditions)
    - design.md §Data Models 1-5 (HouseholdMemory, Product, DeviceState,
      RingEvent, Order)

The module uses only the Python standard library so the backend runs with
no external database credentials. All data queries use parameterized SQL
(`?` placeholders); identifiers in DDL are static strings (no user input).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Iterable

__all__ = ["DatabaseManager"]


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

# A fixed timestamp for seeded rows keeps tests deterministic. Calling
# ``init_db()`` again never overwrites these rows (``INSERT OR IGNORE``).
_SEED_UPDATED_AT = "2025-01-01T00:00:00+00:00"

SEED_PRODUCTS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Ashwagandha Root Extract",
        "category": "ayurvedic",
        "price": 24.99,
        "image_url": "https://placehold.co/600x400/2d5a3d/ffffff?text=Ashwagandha",
        "description": (
            "Pure ashwagandha root extract to support stress relief, joint "
            "comfort, and restful sleep. An Ayurvedic adaptogen ideal for "
            "elderly wellness routines and knee-care recovery."
        ),
        "tags": ["ayurvedic", "wellness", "knee-care", "low-sodium"],
        "in_stock": 1,
    },
    {
        "id": 2,
        "name": "Low-Sodium Turmeric Latte Mix",
        "category": "wellness",
        "price": 18.50,
        "image_url": "https://placehold.co/600x400/c9962a/ffffff?text=Turmeric+Latte",
        "description": (
            "Golden turmeric latte mix with a low-sodium Ayurvedic spice "
            "blend. Anti-inflammatory and comforting for evening wellness."
        ),
        "tags": ["low-sodium", "ayurvedic", "wellness"],
        "in_stock": 1,
    },
    {
        "id": 3,
        "name": "Organic Moringa Capsules",
        "category": "wellness",
        "price": 22.00,
        "image_url": "https://placehold.co/600x400/3a7d44/ffffff?text=Moringa",
        "description": (
            "Organic moringa leaf capsules packed with vitamins and "
            "minerals. Low-sodium, plant-based daily wellness supplement."
        ),
        "tags": ["wellness", "low-sodium", "ayurvedic"],
        "in_stock": 1,
    },
    {
        "id": 4,
        "name": "Himalayan Pink Salt (Low Sodium Blend)",
        "category": "grocery",
        "price": 9.99,
        "image_url": "https://placehold.co/600x400/b5482f/ffffff?text=Himalayan+Salt",
        "description": (
            "Mineral-rich Himalayan pink salt blended for a lower-sodium "
            "seasoning. A grocery staple for heart-friendly cooking."
        ),
        "tags": ["low-sodium", "grocery"],
        "in_stock": 1,
    },
    {
        "id": 5,
        "name": "Joint Support Herbal Tea",
        "category": "ayurvedic",
        "price": 15.75,
        "image_url": "https://placehold.co/600x400/7a4fa0/ffffff?text=Herbal+Tea",
        "description": (
            "Ayurvedic herbal tea blend formulated for joint support and "
            "knee comfort. Low-sodium, caffeine-free, and soothing."
        ),
        "tags": ["ayurvedic", "knee-care", "wellness", "low-sodium"],
        "in_stock": 1,
    },
    {
        "id": 6,
        "name": "Cold-Pressed Coconut Oil",
        "category": "grocery",
        "price": 12.50,
        "image_url": "https://placehold.co/600x400/1f8a70/ffffff?text=Coconut+Oil",
        "description": (
            "Cold-pressed virgin coconut oil for cooking and Ayurvedic skin "
            "care. A versatile grocery and wellness staple."
        ),
        "tags": ["grocery", "wellness", "ayurvedic", "low-sodium"],
        "in_stock": 1,
    },
]

SEED_MEMORY: dict[str, Any] = {
    "session_id": "default",
    "context": (
        "Parents visiting tomorrow; father has knee pain and prefers "
        "low-sodium Ayurvedic wellness items; warm ambient lighting preferred"
    ),
    "health_notes": ["father has knee pain"],
    "dietary_restrictions": ["low-sodium", "ayurvedic"],
    "preferences": {"lighting": "warm", "budget": 200},
}

SEED_DEVICES: list[dict[str, Any]] = [
    {
        "device_id": "living_room_light",
        "device_type": "light",
        "state": {"on": False, "brightness": 0, "color": "warm"},
        "room": "living_room",
    },
    {
        "device_id": "thermostat",
        "device_type": "hvac",
        "state": {"on": False, "temperature": 70, "mode": "auto"},
        "room": "living_room",
    },
]


class DatabaseManager:
    """Zero-config SQLite store with schema creation and seed data.

    A single shared connection is opened with ``check_same_thread=False`` so
    FastAPI request handlers running in different threads can share it. A
    re-entrant lock serializes connection access, and WAL journal mode keeps
    readers from blocking writers (and vice versa) for better concurrency.

    Attributes:
        db_path: Path to the SQLite database file.
        conn: The shared ``sqlite3.Connection`` (``row_factory = Row``).
    """

    def __init__(self, db_path: str = "omnipulse.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # Re-entrant so a method may call another locked method safely.
        self._lock = threading.RLock()
        with self._lock:
            # WAL mode persists in the database header; better read
            # concurrency (readers do not block writers).
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA foreign_keys=ON")

    # ------------------------------------------------------------------
    # Schema + seed
    # ------------------------------------------------------------------

    def init_db(self) -> None:
        """Create all tables and seed default data if not already present.

        Idempotent: repeated calls never duplicate seed rows because every
        seed insert uses ``INSERT OR IGNORE`` against a primary key.
        """
        with self._lock:
            cur = self.conn.cursor()

            # --- DDL (static identifiers; no user input interpolated) ---
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS household_memory (
                    session_id TEXT PRIMARY KEY,
                    context TEXT NOT NULL,
                    health_notes TEXT,
                    dietary_restrictions TEXT,
                    preferences TEXT,
                    updated_at TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    image_url TEXT NOT NULL,
                    description TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    in_stock INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS device_states (
                    device_id TEXT PRIMARY KEY,
                    device_type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    room TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ring_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT,
                    verified INTEGER DEFAULT 0,
                    action_taken TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_ids TEXT NOT NULL,
                    total REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'confirmed',
                    created_at TEXT NOT NULL
                )
                """
            )

            # --- Seed data (all values via ? placeholders) ---
            cur.execute(
                """
                INSERT OR IGNORE INTO household_memory
                    (session_id, context, health_notes, dietary_restrictions,
                     preferences, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    SEED_MEMORY["session_id"],
                    SEED_MEMORY["context"],
                    json.dumps(SEED_MEMORY["health_notes"]),
                    json.dumps(SEED_MEMORY["dietary_restrictions"]),
                    json.dumps(SEED_MEMORY["preferences"]),
                    _SEED_UPDATED_AT,
                ),
            )

            for product in SEED_PRODUCTS:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO products
                        (id, name, category, price, image_url, description,
                         tags, in_stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product["id"],
                        product["name"],
                        product["category"],
                        product["price"],
                        product["image_url"],
                        product["description"],
                        json.dumps(product["tags"]),
                        product["in_stock"],
                    ),
                )

            for device in SEED_DEVICES:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO device_states
                        (device_id, device_type, state, room)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        device["device_id"],
                        device["device_type"],
                        json.dumps(device["state"]),
                        device["room"],
                    ),
                )

            self.conn.commit()

    # ------------------------------------------------------------------
    # Row -> dict converters
    # ------------------------------------------------------------------

    @staticmethod
    def _product_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": row["price"],
            "image_url": row["image_url"],
            "description": row["description"],
            "tags": json.loads(row["tags"] or "[]"),
            "in_stock": bool(row["in_stock"]),
        }

    @staticmethod
    def _memory_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "session_id": row["session_id"],
            "context": row["context"],
            "health_notes": json.loads(row["health_notes"] or "[]"),
            "dietary_restrictions": json.loads(row["dietary_restrictions"] or "[]"),
            "preferences": json.loads(row["preferences"] or "{}"),
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _device_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "device_id": row["device_id"],
            "device_type": row["device_type"],
            "state": json.loads(row["state"] or "{}"),
            "room": row["room"],
        }

    @staticmethod
    def _ring_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "event_type": row["event_type"],
            "timestamp": row["timestamp"],
            "description": row["description"],
            "verified": bool(row["verified"]),
            "action_taken": row["action_taken"],
        }

    # ------------------------------------------------------------------
    # Household memory
    # ------------------------------------------------------------------

    def get_memory(self, session_id: str) -> dict[str, Any]:
        """Return stored household context for ``session_id``.

        If no row exists, a default empty memory structure is returned so
        downstream tools can always access ``context``/``health_notes``/
        ``preferences`` without ``None`` checks.
        """
        with self._lock:
            cur = self.conn.execute(
                "SELECT * FROM household_memory WHERE session_id = ?",
                (session_id,),
            )
            row = cur.fetchone()
        if row is None:
            return {
                "session_id": session_id,
                "context": "",
                "health_notes": [],
                "dietary_restrictions": [],
                "preferences": {},
                "updated_at": "",
            }
        return self._memory_from_row(row)

    def save_memory(
        self,
        session_id: str,
        context: Any,
        health_notes: list[str] | None = None,
        dietary_restrictions: list[str] | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist new or updated household context, returning the stored row.

        Supports two call conventions for compatibility with the design
        interface and the MCP tool schema:

        * ``save_memory(session_id, context_str, health_notes, ...)``
        * ``save_memory(session_id, {"context": ..., "health_notes": ...})``
        """
        if isinstance(context, dict):
            data = context
            context = data.get("context", "")
            health_notes = data.get("health_notes", health_notes)
            dietary_restrictions = data.get("dietary_restrictions", dietary_restrictions)
            preferences = data.get("preferences", preferences)

        health_notes = health_notes if health_notes is not None else []
        dietary_restrictions = (
            dietary_restrictions if dietary_restrictions is not None else []
        )
        preferences = preferences if preferences is not None else {}
        updated_at = _now_iso()

        with self._lock:
            cur = self.conn.execute(
                "SELECT 1 FROM household_memory WHERE session_id = ?",
                (session_id,),
            )
            exists = cur.fetchone() is not None
            if exists:
                self.conn.execute(
                    """
                    UPDATE household_memory
                       SET context = ?, health_notes = ?,
                           dietary_restrictions = ?, preferences = ?,
                           updated_at = ?
                     WHERE session_id = ?
                    """,
                    (
                        str(context),
                        json.dumps(health_notes),
                        json.dumps(dietary_restrictions),
                        json.dumps(preferences),
                        updated_at,
                        session_id,
                    ),
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO household_memory
                        (session_id, context, health_notes,
                         dietary_restrictions, preferences, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        str(context),
                        json.dumps(health_notes),
                        json.dumps(dietary_restrictions),
                        json.dumps(preferences),
                        updated_at,
                    ),
                )
            self.conn.commit()

        return self.get_memory(session_id)

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    def get_all_products(self) -> list[dict[str, Any]]:
        """Return every product in the catalog, ordered by id."""
        with self._lock:
            cur = self.conn.execute("SELECT * FROM products ORDER BY id")
            return [self._product_from_row(row) for row in cur.fetchall()]

    def get_product(self, product_id: int) -> dict[str, Any] | None:
        """Return a single product by id, or ``None`` if not found."""
        with self._lock:
            cur = self.conn.execute(
                "SELECT * FROM products WHERE id = ?",
                (product_id,),
            )
            row = cur.fetchone()
        return self._product_from_row(row) if row else None

    def search_products(
        self,
        query: str,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the catalog by name/description/category overlap and tags.

        A product matches if the lowercased ``query`` is a substring of its
        name, description, or category, OR if it shares any tag with ``tags``.
        Only in-stock matches are returned. An empty query with no tags
        matches nothing.
        """
        query_lower = (query or "").lower().strip()
        tags_lower = [str(t).lower() for t in (tags or [])]

        matched: list[dict[str, Any]] = []
        for product in self.get_all_products():
            is_match = False
            if query_lower:
                haystacks = (
                    product["name"].lower(),
                    product["description"].lower(),
                    product["category"].lower(),
                )
                if any(query_lower in field for field in haystacks):
                    is_match = True
            if not is_match and tags_lower:
                product_tags = [t.lower() for t in product["tags"]]
                if any(t in product_tags for t in tags_lower):
                    is_match = True
            if is_match and product["in_stock"]:
                matched.append(product)
        return matched

    # ------------------------------------------------------------------
    # Smart home devices
    # ------------------------------------------------------------------

    def get_device_states(self) -> list[dict[str, Any]]:
        """Return all device states, ordered by device_id."""
        with self._lock:
            cur = self.conn.execute("SELECT * FROM device_states ORDER BY device_id")
            return [self._device_from_row(row) for row in cur.fetchall()]

    def update_device_state(
        self,
        device: str,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Set the state JSON for ``device`` (UPSERT), returning the row.

        Existing devices are updated in place. Unknown devices are inserted
        with an inferred ``device_type`` and ``room`` so the smart home
        domain can introduce new devices dynamically.
        """
        state_json = json.dumps(state)
        with self._lock:
            cur = self.conn.execute(
                "SELECT * FROM device_states WHERE device_id = ?",
                (device,),
            )
            row = cur.fetchone()
            if row is None:
                device_type = self._infer_device_type(device)
                room = self._infer_room(device)
                self.conn.execute(
                    """
                    INSERT INTO device_states (device_id, device_type, state, room)
                    VALUES (?, ?, ?, ?)
                    """,
                    (device, device_type, state_json, room),
                )
            else:
                self.conn.execute(
                    "UPDATE device_states SET state = ? WHERE device_id = ?",
                    (state_json, device),
                )
            self.conn.commit()
            cur = self.conn.execute(
                "SELECT * FROM device_states WHERE device_id = ?",
                (device,),
            )
            return self._device_from_row(cur.fetchone())

    @staticmethod
    def _infer_device_type(device_id: str) -> str:
        d = device_id.lower()
        if "thermostat" in d or "hvac" in d:
            return "hvac"
        if "routine" in d:
            return "routine"
        return "light"

    @staticmethod
    def _infer_room(device_id: str) -> str:
        d = device_id.lower()
        for room in (
            "living_room",
            "bedroom",
            "kitchen",
            "bathroom",
            "office",
            "garage",
        ):
            if d.startswith(room) or room in d:
                return room
        return "living_room"

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def create_order(self, product_ids: Iterable[int]) -> dict[str, Any]:
        """Persist an order for ``product_ids`` and return the order record.

        The order total is computed by summing the price of each existing
        product. Unknown product ids contribute 0 to the total (they are
        reported as errors by the calling tool, not the database).
        """
        ids = [int(pid) for pid in product_ids]
        total = 0.0
        for pid in ids:
            product = self.get_product(pid)
            if product:
                total += product["price"]
        total = round(total, 2)
        created_at = _now_iso()

        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO orders (product_ids, total, status, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (json.dumps(ids), total, "confirmed", created_at),
            )
            self.conn.commit()
            order_id = cur.lastrowid

        return {
            "id": order_id,
            "product_ids": ids,
            "total": total,
            "status": "confirmed",
            "created_at": created_at,
        }

    # ------------------------------------------------------------------
    # Ring events
    # ------------------------------------------------------------------

    def log_ring_event(self, event: dict[str, Any]) -> int:
        """Insert a Ring event and return its new id."""
        event_type = event.get("event_type", "guest_arrival")
        description = event.get("description", "")
        timestamp = event.get("timestamp") or _now_iso()
        action_taken = event.get("action_taken", "")
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO ring_events
                    (event_type, timestamp, description, verified, action_taken)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_type, timestamp, description, 0, action_taken),
            )
            self.conn.commit()
            return cur.lastrowid

    def get_ring_event(self, event_id: int) -> dict[str, Any] | None:
        """Return a Ring event by id, or ``None`` if not found."""
        with self._lock:
            cur = self.conn.execute(
                "SELECT * FROM ring_events WHERE id = ?",
                (event_id,),
            )
            row = cur.fetchone()
        return self._ring_from_row(row) if row else None

    def update_ring_event(
        self,
        event_id: int,
        fields: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update one or more Ring event fields, returning the updated row.

        Only a whitelist of column names is accepted; values are bound as
        parameters so no user input is ever interpolated into the SQL.
        """
        if not fields:
            return self.get_ring_event(event_id)

        allowed = {
            "verified",
            "action_taken",
            "event_type",
            "description",
            "timestamp",
        }
        set_clauses: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "verified":
                value = 1 if value else 0
            set_clauses.append(f"{key} = ?")
            values.append(value)

        if not set_clauses:
            return self.get_ring_event(event_id)

        values.append(event_id)
        with self._lock:
            self.conn.execute(
                f"UPDATE ring_events SET {', '.join(set_clauses)} WHERE id = ?",
                values,
            )
            self.conn.commit()
        return self.get_ring_event(event_id)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            self.conn.close()

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
