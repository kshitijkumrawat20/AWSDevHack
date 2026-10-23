"""Household memory retrieval and persistence tools for Alexa+ OmniPulse.

Implements two :class:`MCPTool` subclasses that read and write the
cross-session household context stored by :class:`DatabaseManager`:

* :class:`GetHouseholdMemoryTool` (``get_household_memory``) — retrieves the
  stored household context (health notes, dietary restrictions, preferences)
  and returns it as a natural-language summary plus a ``memory_card`` UI
  payload. Per the OmniPulse skill, this tool is always invoked first, before
  any other tool, so every orchestration is grounded in remembered context.
* :class:`SaveHouseholdMemoryTool` (``save_household_memory``) — persists or
  updates household context for cross-session memory so future sessions
  remember household needs such as knee pain or a low-sodium diet.

Design references:
    - design.md §Component 3 (MCP Tools): unified tool contract
    - design.md §Data Model 1 (HouseholdMemory): context, health_notes,
      dietary_restrictions, preferences, updated_at
    - SKILL.md Step 1 (Context Retrieval): call ``get_household_memory`` first

Every tool follows the unified contract documented in design.md
§Component 3: ``execute`` returns ``{"content": [...], "ui": {...}}``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

# ``mcp_server`` is a sibling top-level module (``backend`` is on sys.path
# when the app or tests run), matching the import convention used by
# ``mcp_server.py`` itself (``from database import DatabaseManager``).
from mcp_server import MCPTool

__all__ = ["GetHouseholdMemoryTool", "SaveHouseholdMemoryTool"]

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from database import DatabaseManager


def _build_memory_summary(memory: dict[str, Any]) -> str:
    """Render a household memory record as a natural-language summary.

    Each field is described in its own sentence so the summary reads clearly
    even when some fields are empty (e.g. a fresh session with no stored
    context). The shape mirrors the example in the task spec:

        "Household context: ... Health notes: ... Dietary restrictions: ...
         Preferences: ..."
    """
    session_id = memory.get("session_id", "")
    context = memory.get("context", "")
    health_notes = memory.get("health_notes") or []
    dietary_restrictions = memory.get("dietary_restrictions") or []
    preferences = memory.get("preferences") or {}

    parts: list[str] = []

    if context:
        parts.append(f"Household context: {context}.")
    else:
        parts.append(f"No stored household context for session '{session_id}'.")

    if health_notes:
        parts.append(f"Health notes: {', '.join(str(n) for n in health_notes)}.")
    else:
        parts.append("Health notes: none recorded.")

    if dietary_restrictions:
        joined = ", ".join(str(r) for r in dietary_restrictions)
        parts.append(f"Dietary restrictions: {joined}.")
    else:
        parts.append("Dietary restrictions: none recorded.")

    if preferences:
        pref_str = ", ".join(f"{k}: {v}" for k, v in preferences.items())
        parts.append(f"Preferences: {pref_str}.")
    else:
        parts.append("Preferences: none recorded.")

    return " ".join(parts)


def _memory_to_ui(memory: dict[str, Any]) -> dict[str, Any]:
    """Build the ``memory_card`` UI payload from a stored memory record.

    Only the user-facing fields are surfaced (``updated_at`` is omitted) so
    the simulator canvas renders a clean, deterministic card.
    """
    return {
        "type": "memory_card",
        "session_id": memory.get("session_id", ""),
        "context": memory.get("context", ""),
        "health_notes": memory.get("health_notes", []),
        "dietary_restrictions": memory.get("dietary_restrictions", []),
        "preferences": memory.get("preferences", {}),
    }


class GetHouseholdMemoryTool(MCPTool):
    """Retrieve persistent cross-session household context.

    Calls :meth:`DatabaseManager.get_memory` for the requested ``session_id``
    and returns a natural-language summary (``content``) alongside a
    ``memory_card`` UI payload (``ui``) for the simulator canvas.

    Per SKILL.md Step 1, this tool is always invoked before any other tool so
    every orchestration is grounded in remembered household context.
    """

    name = "get_household_memory"
    description = (
        "Retrieve persistent cross-session household context including "
        "health notes, dietary restrictions, and preferences."
    )
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
        },
        "required": ["session_id"],
    }

    def execute(self, arguments: dict[str, Any], db: "DatabaseManager") -> dict[str, Any]:
        """Return ``{"content": [text summary], "ui": {memory_card}}``."""
        session_id = arguments.get("session_id", "")
        memory = db.get_memory(session_id)
        summary = _build_memory_summary(memory)
        return {
            "content": [{"type": "text", "text": summary}],
            "ui": _memory_to_ui(memory),
        }


class SaveHouseholdMemoryTool(MCPTool):
    """Persist or update household context for cross-session memory.

    Calls :meth:`DatabaseManager.save_memory` with the provided fields (all
    except ``session_id`` are optional and default to empty values) and
    returns a confirmation message alongside the updated ``memory_card`` UI
    payload so the simulator reflects the new state immediately.
    """

    name = "save_household_memory"
    description = "Persist or update household context for cross-session memory."
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "context": {"type": "string"},
            "health_notes": {"type": "array", "items": {"type": "string"}},
            "dietary_restrictions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "preferences": {"type": "object"},
        },
        "required": ["session_id"],
    }

    def execute(self, arguments: dict[str, Any], db: "DatabaseManager") -> dict[str, Any]:
        """Persist the memory and return ``{"content": [confirmation], "ui": {memory_card}}``.

        Missing optional arguments default to empty values (empty string for
        ``context``, empty lists for ``health_notes``/``dietary_restrictions``,
        empty dict for ``preferences``), matching ``DatabaseManager.save_memory``'s
        own defaults so no ``None`` ever reaches the persistence layer.
        """
        session_id = arguments.get("session_id", "")
        context = arguments.get("context", "")
        health_notes = arguments.get("health_notes")
        dietary_restrictions = arguments.get("dietary_restrictions")
        preferences = arguments.get("preferences")

        memory = db.save_memory(
            session_id,
            context,
            health_notes=health_notes,
            dietary_restrictions=dietary_restrictions,
            preferences=preferences,
        )
        return {
            "content": [{"type": "text", "text": "Household memory updated successfully."}],
            "ui": _memory_to_ui(memory),
        }
