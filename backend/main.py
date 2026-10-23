"""FastAPI Entry Point for Alexa+ OmniPulse.

Exposes:
    - POST /mcp: MCP Streamable HTTP endpoint handling JSON-RPC 2.0 (spec 2025-11-25)
    - POST /chat: Multi-domain agent orchestration (smart fallback + LLM)
    - POST /webhook/ring: Simulated Ring doorbell/camera webhook
    - GET  /events: Server-Sent Events (SSE) stream for proactive Ring alerts
    - GET  /health: System health and runtime status

Design references:
    - design.md §Component 5 (FastAPI Entry Point)
    - design.md §Architecture (Request-Response Flow, Ring Webhook Flow, MCP Inspector Flow)
    - design.md §Security (CORS, Ring Webhook validation)
    - design.md §Performance (SSE Streaming, In-process tool routing)
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from agent import AgentOrchestrator
from database import DatabaseManager
from mcp_server import MCPServer
from tools.commerce_tools import ExecuteInstantCheckoutTool, SearchAndBuildCarouselTool
from tools.memory_tools import GetHouseholdMemoryTool, SaveHouseholdMemoryTool
from tools.ring_tools import HandleRingEventTool, VALID_EVENT_TYPES
from tools.smarthome_tools import UpdateSmarthomeStateTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnipulse.main")

# Global instances initialized on startup
db_manager: DatabaseManager = None  # type: ignore
mcp_server_instance: MCPServer = None  # type: ignore
agent_orchestrator: AgentOrchestrator = None  # type: ignore

# Active subscriber queues for Server-Sent Events (/events)
event_subscribers: set[asyncio.Queue[dict[str, Any]]] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager initializing persistence, MCP server, and tools."""
    global db_manager, mcp_server_instance, agent_orchestrator

    logger.info("Initializing SQLite database with seed data...")
    db_manager = DatabaseManager("omnipulse.db")
    db_manager.init_db()

    logger.info("Initializing MCP Server and registering 6 domain tools...")
    mcp_server_instance = MCPServer(db_manager)
    # Register all 6 tools, replacing any schema stubs
    mcp_server_instance.tool_registry.register(GetHouseholdMemoryTool())
    mcp_server_instance.tool_registry.register(SaveHouseholdMemoryTool())
    mcp_server_instance.tool_registry.register(SearchAndBuildCarouselTool())
    mcp_server_instance.tool_registry.register(ExecuteInstantCheckoutTool())
    mcp_server_instance.tool_registry.register(UpdateSmarthomeStateTool())
    mcp_server_instance.tool_registry.register(HandleRingEventTool())

    logger.info("Initializing Agent Orchestrator...")
    agent_orchestrator = AgentOrchestrator(db_manager, mcp_server_instance)

    yield

    logger.info("Shutting down Alexa+ OmniPulse...")
    if db_manager is not None:
        db_manager.close()


app = FastAPI(
    title="Alexa+ OmniPulse Backend",
    version="1.0.0",
    description="Multi-Service Context-Aware Ambient Orchestrator with Streamable HTTP MCP (spec 2025-11-25)",
    lifespan=lifespan,
)

# Enable CORS for Vite dev server and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request & Response Models ---

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class RingWebhookRequest(BaseModel):
    event_type: str
    description: str = "Activity detected at front door"


# --- Endpoints ---

@app.get("/")
@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint confirming runtime status and MCP protocol version."""
    return {
        "status": "online",
        "service": "Alexa+ OmniPulse",
        "protocolVersion": MCPServer.PROTOCOL_VERSION,
        "toolsCount": len(mcp_server_instance.tool_registry.names) if mcp_server_instance else 6,
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    """Streamable HTTP endpoint implementing the Model Context Protocol (MCP).

    Supports JSON-RPC 2.0 initialize, tools/list, and tools/call.
    Inspects Accept header: if 'text/event-stream' is requested, streams SSE;
    otherwise returns standard application/json.
    """
    accept_header = request.headers.get("accept", "")

    try:
        body = await request.json()
    except Exception:
        body = None

    response_payload = mcp_server_instance.route(body)

    if "text/event-stream" in accept_header:
        async def event_generator():
            yield {
                "event": "message",
                "data": json.dumps(response_payload),
            }

        return EventSourceResponse(event_generator())

    return JSONResponse(content=response_payload)


@app.post("/chat")
async def chat_endpoint(req: ChatRequest) -> dict[str, Any]:
    """Autonomous agent orchestration endpoint.

    Retrieves persistent memory first, triggers appropriate MCP tool calls,
    and returns conversational speech along with rich UI cards for the Echo Show canvas.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    response = agent_orchestrator.orchestrate(req.message, req.session_id)
    return response.to_dict()


@app.post("/webhook/ring")
async def ring_webhook_endpoint(req: RingWebhookRequest) -> dict[str, Any]:
    """Webhook simulation for proactive Ring doorbell and camera events.

    Validates event_type in {'package_delivery', 'guest_arrival'}.
    Logs event, cross-checks expected guests with household memory, updates state,
    and fans out alert event to all connected /events SSE clients.
    """
    if req.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event_type '{req.event_type}'. Must be one of {sorted(list(VALID_EVENT_TYPES))}",
        )

    response = agent_orchestrator.handle_ring_event(
        {"event_type": req.event_type, "description": req.description}
    )

    alert_card = response.cards[0] if response.cards else None

    # Fan out to all SSE listeners connected to /events
    event_data = {
        "event_type": req.event_type,
        "speech": response.speech,
        "ring_alert_card": alert_card,
    }
    for queue in list(event_subscribers):
        try:
            queue.put_nowait(event_data)
        except Exception as e:
            logger.warning("Failed to dispatch SSE event to subscriber: %s", e)

    return {
        "speech": response.speech,
        "ring_alert_card": alert_card,
    }


@app.get("/events")
async def events_sse_endpoint(request: Request) -> EventSourceResponse:
    """Server-Sent Events (SSE) stream for proactive Ring notifications."""
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    event_subscribers.add(queue)

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        try:
            # Send initial keepalive / connection confirmation
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected", "stream": "ring_alerts"}),
            }
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Wait for next event with a timeout for keepalive
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": "ring_alert",
                        "data": json.dumps(data),
                    }
                except asyncio.TimeoutError:
                    # Keepalive ping
                    yield {
                        "event": "ping",
                        "data": json.dumps({"ping": "keepalive"}),
                    }
        finally:
            event_subscribers.discard(queue)

    return EventSourceResponse(event_generator())
