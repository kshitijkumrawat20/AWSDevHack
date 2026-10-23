"""Ring camera/doorbell event handler tool for Alexa+ OmniPulse.

Implements :class:`HandleRingEventTool`, one of the six MCP domain tools.
A simulated Ring event (``package_delivery`` or ``guest_arrival``) is
persisted to the ``ring_events`` table and, for guest arrivals, cross-checked
against persistent household memory to decide whether the visitor was
expected. The tool returns a conversational ``content`` block plus a
``ring_alert_card`` UI payload for the Echo Show simulator canvas.

Design references:
    - design.md §Component 3 (MCP Tools): ``{"content": [...], "ui": {...}}``
    - design.md §Data Model 4 (RingEvent): id, event_type, timestamp,
      description, verified, action_taken
    - design.md §Algorithm 4 (Ring Event Handler): full pseudocode
    - design.md §Property 6 (Ring Verification): a guest_arrival event is
      ``verified == true`` iff household memory mentions expected guests
    - design.md §Error Handling (Scenarios 3, 6)

The expected-guest keyword set is exposed as :data:`EXPECTED_GUEST_KEYWORDS`
so the ring verification property test (Task 3.6) can import it and stay in
lock-step with the tool's cross-check logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp_server import INVALID_PARAMS, JSONRPCError, MCPTool

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from database import DatabaseManager

__all__ = ["HandleRingEventTool", "EXPECTED_GUEST_KEYWORDS", "VALID_EVENT_TYPES"]

# The two event types the simulated Ring device can emit.
VALID_EVENT_TYPES = frozenset({"package_delivery", "guest_arrival"})

# Keywords that, when present in household memory ``context``, indicate an
# expected/known visitor. ``parent`` is included (in addition to the
# ``parents visiting`` phrase from design.md §Algorithm 4) so contexts such as
# "my parents are coming" still verify. Kept as a module-level constant so
# the Property 6 property-based test can reference the exact same set.
EXPECTED_GUEST_KEYWORDS: tuple[str, ...] = ("parents visiting", "guest", "parent")

# Default session id used to read household context, matching the rest of
# the system (memory is seeded/written under the ``"default"`` session).
DEFAULT_SESSION_ID = "default"


def _context_mentions_expected_guest(context: Any) -> bool:
    """Return ``True`` if ``context`` mentions any expected-guest keyword.

    The comparison is case-insensitive substring matching, mirroring
    design.md §Algorithm 4 ("contains(lowercase(memory.context), ...)").
    A non-string (e.g. ``None``) context never matches.
    """
    if not isinstance(context, str):
        return False
    lowered = context.lower()
    return any(keyword in lowered for keyword in EXPECTED_GUEST_KEYWORDS)


def _build_ring_speech(event_type: str, verified: bool, action: str) -> str:
    """Compose the spoken Alexa+ response for a Ring event.

    The wording mirrors the speech lines specified in Task 3.4 and the
    design's ring webhook example (design.md §Example 5).
    """
    if event_type == "guest_arrival":
        if verified:
            return (
                "Ring detected a guest arrival. I verified this matches your "
                "expected visitors — your parents. I've unlocked the front "
                "door and notified you."
            )
        return (
            "Ring detected someone at the door. I couldn't verify this guest "
            "against your expected visitors. Please check your Ring camera."
        )
    # event_type == "package_delivery"
    return (
        "Ring detected a package delivery. I've confirmed the delivery and "
        "logged it for your records."
    )


class HandleRingEventTool(MCPTool):
    """MCP tool that handles a simulated Ring camera/doorbell event.

    Implements design.md §Algorithm 4:

    1. validate ``event_type``
    2. persist the event via ``db.log_ring_event``
    3. retrieve household memory via ``db.get_memory("default")``
    4. cross-check a ``guest_arrival`` against remembered expected guests
    5. update the persisted event with ``verified`` and ``action_taken``
    6. return a ``ring_alert_card`` UI payload plus a spoken response
    """

    name = "handle_ring_event"
    description = (
        "Handle a simulated Ring camera or doorbell event (package delivery "
        "or guest arrival), logging the event and verifying guest arrivals "
        "against household memory."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "event_type": {
                "type": "string",
                "enum": ["package_delivery", "guest_arrival"],
            },
            "description": {"type": "string"},
        },
        "required": ["event_type", "description"],
    }

    def execute(self, arguments: dict[str, Any], db: "DatabaseManager") -> dict[str, Any]:
        """Run the Ring event handler and return ``{"content": [...], "ui": {...}}``.

        Raises :class:`JSONRPCError` with ``INVALID_PARAMS`` when
        ``event_type`` is not one of the allowed values, which the MCP router
        translates into a JSON-RPC error response (design.md §Error Handling).
        """
        # Step 1: Validate event_type before touching the database so an
        # invalid request never persists a bogus event.
        event_type = arguments.get("event_type")
        if event_type not in VALID_EVENT_TYPES:
            raise JSONRPCError(
                INVALID_PARAMS,
                "Invalid params: event_type must be 'package_delivery' or "
                "'guest_arrival'",
            )
        description = arguments.get("description", "") or ""

        # Step 2: Persist the raw event (verified defaults to false/0).
        event_id = db.log_ring_event(
            {"event_type": event_type, "description": description}
        )

        # Step 3: Retrieve household memory for cross-verification.
        memory = db.get_memory(DEFAULT_SESSION_ID)

        # Step 4: Cross-check against expected guests.
        verified = False
        action = "notified_homeowner"

        if event_type == "guest_arrival":
            if _context_mentions_expected_guest(memory.get("context", "")):
                verified = True
                action = "verified_expected_guest_and_unlocked_front_door"
            else:
                # verified stays False
                action = "unknown_guest_notified_homeowner"
        elif event_type == "package_delivery":
            verified = True
            action = "package_delivery_confirmed"

        # Step 5: Update the persisted event record with the outcome.
        db.update_ring_event(
            event_id, {"verified": verified, "action_taken": action}
        )

        # Step 6: Build the alert card + spoken response.
        ui = {
            "type": "ring_alert_card",
            "title": "Ring " + event_type,
            "eventType": event_type,
            "verified": verified,
            "description": description,
        }
        speech = _build_ring_speech(event_type, verified, action)

        return {
            "content": [{"type": "text", "text": speech}],
            "ui": ui,
        }
