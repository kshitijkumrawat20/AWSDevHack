"""Make two small live Qloo requests to verify the event key and API host.

Usage: python scripts/smoke_qloo.py [city]
The API key is read only from QLOO_API_KEY and is never printed.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.qloo_client import QlooAPIError, QlooClient


async def main() -> int:
    client = QlooClient()
    if not client.configured:
        print("Missing QLOO_API_KEY. Set the event key in your shell or local .env.")
        return 2

    target = sys.argv[1] if len(sys.argv) > 1 else "movie"
    try:
        matches = await client.search_entities("Spirited Away", "movie", take=5)
        if not matches:
            print("Search request succeeded but no movie entity matched. Try another title.")
            return 1

        seed = matches[0]
        recommendations = await client.recommend(target, [seed["entity_id"]], take=5)
        print(json.dumps({
            "search_status": "ok",
            "resolved_entity": {"name": seed["name"], "type": seed.get("type")},
            "recommendation_status": "ok" if recommendations else "empty",
            "target_category": target,
            "recommendation_count": len(recommendations),
            "recommendation_names": [item["name"] for item in recommendations],
            "credential_printed": False,
        }, indent=2))
        return 0 if recommendations else 1
    except QlooAPIError as exc:
        print(f"Qloo smoke test failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
