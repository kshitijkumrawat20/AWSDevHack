"""MCP Streamable HTTP server for Alexa+ OmniPulse.

Implements the Model Context Protocol (MCP) specification ``2025-11-25`` over
Streamable HTTP, handling JSON-RPC 2.0 ``initialize``, ``tools/list``, and
``tools/call`` methods with optional SSE (``text/event-stream``) responses.

Design references:
    - design.md §Component 1 (MCPServer): interface and responsibilities
    - design.md §Algorithm 1 (MCP JSON-RPC Router): full pseudocode for route()
    - design.md §Function 1 (route): preconditions and postconditions
    - design.md §Error Handling (Scenarios 1-3): JSON-RPC error codes
    - design.md §Property 1: Protocol Version (every initialize -> "2025-11-25")
    - design.md §Property 3: Tool Count (tools/list -> exactly 6 tools)

The module is dependency-free at import time: the optional
:class:`DatabaseManager` is only referenced under ``TYPE_CHECKING`` so the
server can be instantiated and tested without a database. The six domain
tools are implemented in later tasks (Task 3) and registered into the
:class:`ToolRegistry`; until then, schema-only stubs are pre-registered so
``tools/list`` always reports exactly six tools (Property 3) and the module
imports and runs without errors.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

__all__ = [
    "MCPTool",
    "ToolRegistry",
    "MCPServer",
    "JSONRPCError",
    "DEFAULT_TOOL_DEFINITIONS",
]

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from database import DatabaseManager


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 error codes
# ---------------------------------------------------------------------------

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class JSONRPCError(Exception):
    """Raised inside tool dispatch to produce a JSON-RPC error response.

    Carries the standard JSON-RPC ``code`` and ``message`` so :meth:`route`
    can translate it into an ``{"error": {...}}`` envelope without losing the
    request ``id``.
    """

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# Canonical 6-tool definitions (used for tools/list and as default stubs)
# ---------------------------------------------------------------------------

DEFAULT_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_household_memory",
        "description": (
            "Retrieve persistent cross-session household context including "
            "health notes, dietary restrictions, and preferences. Per the "
            "OmniPulse skill, this tool is always invoked first, before any "
            "other tool, so every orchestration is grounded in remembered "
            "context."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "save_household_memory",
        "description": (
            "Persist or update household context (health notes, dietary "
            "restrictions, preferences) for cross-session memory so future "
            "sessions remember household needs such as knee pain or a "
            "low-sodium diet."
        ),
        "inputSchema": {
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
        },
    },
    {
        "name": "update_smarthome_state",
        "description": (
            "Update a smart home device state such as a light (brightness, "
            "color), an HVAC thermostat (temperature, mode), or a routine. "
            "Returns a smart home status card for the simulator canvas."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "device": {"type": "string"},
                "state": {
                    "type": "object",
                    "properties": {
                        "on": {"type": "boolean"},
                        "brightness": {"type": "number"},
                        "color": {"type": "string"},
                        "temperature": {"type": "number"},
                        "mode": {"type": "string"},
                    },
                },
            },
            "required": ["device", "state"],
        },
    },
    {
        "name": "search_and_build_carousel",
        "description": (
            "Search the product catalog by free-text query and optional tags, "
            "matching on name, description, category, or tag overlap, then "
            "return only in-stock products as a shoppable carousel card."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["query"],
        },
    },
    {
        "name": "execute_instant_checkout",
        "description": (
            "Execute a 1-click instant checkout for a list of product ids, "
            "creating a confirmed order and returning the order id, item "
            "list, and total as a checkout confirmation card."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_ids": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["product_ids"],
        },
    },
    {
        "name": "handle_ring_event",
        "description": (
            "Handle a simulated Ring camera or doorbell event (package "
            "delivery or guest arrival), logging the event and verifying a "
            "guest arrival against household memory of expected visitors."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "enum": ["package_delivery", "guest_arrival"],
                },
                "description": {"type": "string"},
            },
            "required": ["event_type", "description"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool contract + registry
# ---------------------------------------------------------------------------


class MCPTool(ABC):
    """Base contract for all OmniPulse MCP domain tools.

    Concrete tools (implemented in Task 3) set ``name``, ``description``, and
    ``input_schema`` and implement :meth:`execute`. The unified tool contract
    is documented in design.md §Component 3: every tool returns
    ``{"content": [...], "ui": {...}}``.
    """

    name: str
    description: str
    input_schema: dict[str, Any]

    @abstractmethod
    def execute(self, arguments: dict[str, Any], db: "DatabaseManager") -> dict[str, Any]:
        """Run the tool against ``db`` and return ``{"content": [...], "ui": {...}}``."""

    def to_definition(self) -> dict[str, Any]:
        """Return the MCP tool definition (``name``, ``description``, ``inputSchema``)."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class _SchemaTool(MCPTool):
    """Schema-only tool stub pre-registered so ``tools/list`` reports all 6 tools.

    Real tool implementations (Task 3) replace these stubs in the registry by
    name. A stub's :meth:`execute` raises :class:`NotImplementedError`, which
    :meth:`MCPServer.route` translates into a JSON-RPC internal error.
    """

    def __init__(self, name: str, description: str, input_schema: dict[str, Any]) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def execute(self, arguments: dict[str, Any], db: "DatabaseManager") -> dict[str, Any]:
        raise NotImplementedError(f"Tool '{self.name}' has not been implemented yet.")


class ToolRegistry:
    """Registry of MCP tools keyed by name (insertion-ordered).

    Registering a tool whose name already exists replaces the prior entry,
    so the real Task 3 tools swap in for the default schema stubs without
    growing the count beyond six.
    """

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        """Register ``tool``, replacing any existing tool with the same name."""
        if not isinstance(tool, MCPTool):
            raise TypeError("tool must be an MCPTool instance")
        self._tools[tool.name] = tool

    def get(self, name: str) -> MCPTool | None:
        """Return the tool with ``name``, or ``None`` if not registered."""
        return self._tools.get(name)

    def list_all(self) -> list[dict[str, Any]]:
        """Return the MCP tool definitions in registration order."""
        return [tool.to_definition() for tool in self._tools.values()]

    @property
    def names(self) -> list[str]:
        """Return the registered tool names in registration order."""
        return list(self._tools.keys())


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------


class MCPServer:
    """JSON-RPC 2.0 router implementing MCP spec ``2025-11-25``.

    Dispatches ``initialize``, ``tools/list``, and ``tools/call`` methods,
    validates the JSON-RPC 2.0 envelope, and can format responses as either
    plain JSON or SSE (``text/event-stream``).
    """

    PROTOCOL_VERSION: str = "2025-11-25"

    def __init__(
        self,
        db: "DatabaseManager | None" = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.db = db
        if tool_registry is None:
            self.tool_registry = ToolRegistry()
            self._register_default_tools()
        else:
            self.tool_registry = tool_registry

    def _register_default_tools(self) -> None:
        """Pre-register the 6 canonical schema stubs (Property 3 invariant)."""
        for definition in DEFAULT_TOOL_DEFINITIONS:
            self.tool_registry.register(
                _SchemaTool(
                    name=definition["name"],
                    description=definition["description"],
                    input_schema=definition["inputSchema"],
                )
            )

    # ------------------------------------------------------------------
    # JSON-RPC error helper
    # ------------------------------------------------------------------

    @staticmethod
    def _error_response(req_id: Any, code: int, message: str) -> dict[str, Any]:
        """Build a JSON-RPC error response that echoes ``req_id``."""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }

    # ------------------------------------------------------------------
    # Method handlers (return the inner ``result`` dict)
    # ------------------------------------------------------------------

    def handle_initialize(self, request: dict[str, Any]) -> dict[str, Any]:
        """Return protocol version, server capabilities, and server info.

        Implements design.md §Property 1: every initialize response reports
        ``protocolVersion == "2025-11-25"``.
        """
        return {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "omnipulse-mcp", "version": "1.0.0"},
        }

    def handle_tools_list(self, request: dict[str, Any]) -> dict[str, Any]:
        """Return the registered tool definitions.

        Implements design.md §Property 3: the response contains exactly 6
        tools (the default schema stubs, later replaced by real tools).
        """
        return {"tools": self.tool_registry.list_all()}

    def handle_tools_call(self, request: dict[str, Any]) -> dict[str, Any]:
        """Route ``params.name`` to its tool and return ``{"content", "ui"}``.

        Raises :class:`JSONRPCError` for missing/unknown tool names; the caller
        (:meth:`route`) translates it into a JSON-RPC error envelope.
        """
        params = request.get("params") or {}
        name = params.get("name")
        if not name:
            raise JSONRPCError(INVALID_PARAMS, "Invalid params: missing tool name")

        tool = self.tool_registry.get(name)
        if tool is None:
            raise JSONRPCError(
                INVALID_PARAMS, f"Invalid params: unknown tool '{name}'"
            )

        arguments = params.get("arguments", {}) or {}
        result = tool.execute(arguments, self.db)
        # Normalize to the documented tools/call result shape.
        return {
            "content": result.get("content", []) if isinstance(result, dict) else [],
            "ui": result.get("ui", {}) if isinstance(result, dict) else {},
        }

    # ------------------------------------------------------------------
    # Top-level router
    # ------------------------------------------------------------------

    def route(self, json_rpc_request: dict[str, Any] | None) -> dict[str, Any]:
        """Top-level JSON-RPC 2.0 dispatch.

        Validates the envelope, dispatches to the correct method handler, and
        always echoes the request ``id``. Follows design.md §Algorithm 1.
        """
        # Validate JSON-RPC 2.0 envelope
        if json_rpc_request is None:
            return self._error_response(None, PARSE_ERROR, "Parse error")
        if not isinstance(json_rpc_request, dict):
            return self._error_response(None, PARSE_ERROR, "Parse error")
        if json_rpc_request.get("jsonrpc") != "2.0":
            return self._error_response(
                json_rpc_request.get("id"), INVALID_REQUEST, "Invalid Request"
            )

        req_id = json_rpc_request.get("id")
        method = json_rpc_request.get("method")

        # Dispatch by method
        if method == "initialize":
            result = self.handle_initialize(json_rpc_request)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        if method == "tools/list":
            result = self.handle_tools_list(json_rpc_request)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        if method == "tools/call":
            try:
                result = self.handle_tools_call(json_rpc_request)
                return {"jsonrpc": "2.0", "id": req_id, "result": result}
            except JSONRPCError as exc:
                return self._error_response(req_id, exc.code, exc.message)
            except Exception as exc:  # noqa: BLE001 - surface as JSON-RPC error
                # Tool execution failure (design.md §Error Scenario 3).
                return self._error_response(req_id, INTERNAL_ERROR, "Internal error")

        # Unknown method
        return self._error_response(req_id, METHOD_NOT_FOUND, "Method not found")

    # ------------------------------------------------------------------
    # Response formatting (JSON vs SSE)
    # ------------------------------------------------------------------

    def format_response(
        self,
        response_dict: dict[str, Any],
        accept_header: str = "",
    ) -> str:
        """Format ``response_dict`` as plain JSON or an SSE event stream.

        When ``accept_header`` requests ``text/event-stream``, the response is
        returned as a Server-Sent Events ``message`` event; otherwise it is a
        plain JSON string. Used by the FastAPI ``/mcp`` endpoint (Task 4.2).
        """
        payload = json.dumps(response_dict)
        if accept_header and "text/event-stream" in accept_header:
            return f"event: message\ndata: {payload}\n\n"
        return payload
