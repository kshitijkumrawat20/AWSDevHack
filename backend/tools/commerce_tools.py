"""Commerce domain MCP tools for Alexa+ OmniPulse.

Implements the two commerce-facing MCP tools that power the wellness
shopping and 1-click voice/checkout flows:

* :class:`SearchAndBuildCarouselTool` — catalog search that returns an
  in-stock product carousel (Algorithm 3).
* :class:`ExecuteInstantCheckoutTool` — instant checkout that persists an
  order and returns a confirmation card (Algorithm 5).

Design references:
    - design.md §Component 3 (MCP Tools): unified ``{"content", "ui"}`` contract
    - design.md §Algorithm 3 (Product Search & Carousel Builder)
    - design.md §Algorithm 5 (Instant Checkout)
    - design.md §Data Models 2 (Product) and 5 (Order)
    - design.md §Function 4 (search_and_build_carousel postconditions)
    - design.md §Property 4 (Checkout Total Consistency): ``ui.total`` == sum
      of prices
    - design.md §Property 5 (Carousel Stock Invariant): every carousel product
      has ``buyable == true``

Both tools are :class:`~mcp_server.MCPTool` subclasses registered into the
MCP :class:`~mcp_server.ToolRegistry` (Task 4 wires them into ``main.py``).
They never mutate catalog data: carousel products are freshly-built dicts
derived from the database rows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp_server import MCPTool

__all__ = ["SearchAndBuildCarouselTool", "ExecuteInstantCheckoutTool"]

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from database import DatabaseManager


# ---------------------------------------------------------------------------
# Product search & carousel builder (Algorithm 3)
# ---------------------------------------------------------------------------


class SearchAndBuildCarouselTool(MCPTool):
    """Search the catalog and return an in-stock shoppable carousel.

    Matches products by query substring against name, description, or
    category, and by tag overlap. Only in-stock matches are surfaced as a
    ``carousel`` UI card. The catalog is read-only: no rows are modified.
    """

    name: str = "search_and_build_carousel"
    description: str = (
        "Search the product catalog by query and optional tags, returning "
        "in-stock products as a shoppable carousel."
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["query"],
    }

    def execute(
        self,
        arguments: dict[str, Any],
        db: "DatabaseManager",
    ) -> dict[str, Any]:
        """Run the carousel search per design Algorithm 3.

        Steps:
            1. Lowercase the query (the database also lowercases, but this
               keeps the contract explicit and idempotent).
            2. Delegate matching to ``db.search_products`` which returns only
               in-stock matches by name/description/category or tag overlap.
            3. Build a fresh carousel product dict per match (no catalog
               mutation) with ``buyable`` reflecting ``in_stock``.
            4. Return ``{"content": [...], "ui": {type: "carousel", ...}}``.
            5. Empty matches yield an explanatory empty carousel.
        """
        query = (arguments.get("query") or "").lower()
        tags = arguments.get("tags") or []

        # search_products already lowercases and filters to in-stock items;
        # passing the lowercased query keeps the contract explicit.
        matched = db.search_products(query, tags)

        # Property 5 (Carousel Stock Invariant): every surfaced product is
        # in stock, so ``buyable`` is always true here.
        carousel_products = [
            {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "image_url": product["image_url"],
                "description": product["description"],
                "buyable": product["in_stock"],
            }
            for product in matched
        ]

        count = len(carousel_products)
        if count == 0:
            return {
                "content": [
                    {"type": "text", "text": "No products found matching your criteria."}
                ],
                "ui": {
                    "type": "carousel",
                    "title": "Wellness Recommendations",
                    "products": [],
                },
            }

        return {
            "content": [
                {"type": "text", "text": f"Found {count} products matching your search."}
            ],
            "ui": {
                "type": "carousel",
                "title": "Wellness Recommendations",
                "products": carousel_products,
            },
        }


# ---------------------------------------------------------------------------
# Instant checkout (Algorithm 5)
# ---------------------------------------------------------------------------


class ExecuteInstantCheckoutTool(MCPTool):
    """Execute a 1-click instant checkout for a list of product ids.

    Validates each id exists, accumulates the total from product prices,
    persists an order via ``db.create_order``, and returns a
    ``checkout_card`` confirmation with the order id, item names, and total.
    An unknown product id short-circuits to a checkout error card with
    ``total: 0``.
    """

    name: str = "execute_instant_checkout"
    description: str = "Execute a 1-click instant checkout for a list of product ids."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "product_ids": {"type": "array", "items": {"type": "integer"}},
        },
        "required": ["product_ids"],
    }

    def execute(
        self,
        arguments: dict[str, Any],
        db: "DatabaseManager",
    ) -> dict[str, Any]:
        """Run the instant checkout per design Algorithm 5.

        Steps:
            1. Assert ``product_ids`` is non-empty (else a checkout error card).
            2. Look up each product; an unknown id returns an error card with
               ``total: 0`` (no order is created).
            3. Accumulate the running total from product prices.
            4. Persist the order via ``db.create_order``.
            5. Return ``{"content": [...], "ui": {type: "checkout_card", ...}}``
               with ``orderId``, ``items`` (names), and ``total``.

        Property 4 (Checkout Total Consistency): ``ui.total`` equals the sum
        of the individual product prices.
        """
        product_ids = arguments.get("product_ids") or []

        # Step 1: validate non-empty (design ASSERT length(product_ids) > 0).
        if not product_ids:
            return {
                "content": [
                    {"type": "text", "text": "Checkout failed: no product ids provided."}
                ],
                "ui": {
                    "type": "checkout_card",
                    "title": "Checkout Error",
                    "items": [],
                    "total": 0,
                },
            }

        # Step 2-3: look up each product and accumulate the running total.
        products: list[dict[str, Any]] = []
        total = 0.0
        for pid in product_ids:
            product = db.get_product(int(pid))
            if product is None:
                return {
                    "content": [
                        {"type": "text", "text": f"Product {pid} not found."}
                    ],
                    "ui": {
                        "type": "checkout_card",
                        "title": "Checkout Error",
                        "items": [],
                        "total": 0,
                    },
                }
            products.append(product)
            total += product["price"]

        total = round(total, 2)

        # Step 4: persist the order (db.create_order recomputes the total).
        order = db.create_order(product_ids)

        # Step 5: build the confirmation card and speech text.
        item_names = [product["name"] for product in products]
        speech = (
            f"Your order is confirmed. {len(products)} items totaling ${total:.2f}."
        )

        return {
            "content": [{"type": "text", "text": speech}],
            "ui": {
                "type": "checkout_card",
                "title": "Order Confirmed",
                "orderId": f"ORD-{order['id']}",
                "items": item_names,
                "total": total,
            },
        }
