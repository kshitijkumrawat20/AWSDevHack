# Implementation Plan: omnipulse-mvp (Alexa+ OmniPulse)

## Overview

The implementation follows a six-task pipeline that builds the backend persistence layer first, then the MCP server, the six domain tools, the agent orchestrator and FastAPI entry point, the frontend Echo Show simulator, and finally the deployment/verification artifacts. Each task produces compilable, testable code that integrates with prior tasks — no orphaned code.

The backend is Python 3.11+ / FastAPI; the frontend is Vite + React + TypeScript + Tailwind CSS + Lucide Icons. The system runs with zero external dependencies by default: SQLite provides persistence and a deterministic smart-fallback agent provides orchestration without any LLM API key. Optional Gemini, OpenAI, or AWS Bedrock keys enable richer LLM-driven orchestration via environment variables.

**Implementation languages**: Python 3.11+ (backend), TypeScript (frontend).

---

## Tasks

- [x] 1. Database initialization and project dependencies
  - [x] 1.1 Create `backend/requirements.txt` with pinned dependency versions
    - Pin `fastapi>=0.110`, `uvicorn[standard]>=0.29`, `pydantic>=2.6`, `httpx>=0.27`, `sse-starlette>=2.1`, `pytest>=8.0`, `hypothesis>=6.100`; optionally pin `langgraph>=0.2`, `langchain-core>=0.2`, `langchain-google-genai>=1.0`, `langchain-openai>=0.1`, `boto3>=1.34` for the LLM path
    - _Design: §Dependencies (Backend Dependencies table)_

  - [x] 1.2 Implement `backend/database.py` — DatabaseManager with schema creation and seed data
    - Create `DatabaseManager` class with `__init__(db_path="omnipulse.db")` using `check_same_thread=False` for concurrent FastAPI access
    - Implement `init_db()`: create tables `household_memory`, `products`, `device_states`, `ring_events`, `orders` with parameterized SQL (`?` placeholders, no string interpolation)
    - Seed 6 products into `products` table (wellness, grocery, ayurvedic categories with tags like "low-sodium", "ayurvedic", "knee-care")
    - Seed default household memory into `household_memory` (context mentioning parents visiting, father knee pain, low-sodium preference, warm lighting preference, budget)
    - Seed initial device states into `device_states` (living_room_light, thermostat)
    - Implement query methods: `get_memory(session_id)`, `save_memory(session_id, context)`, `search_products(query, tags)`, `get_all_products()`, `get_product(product_id)`, `get_device_states()`, `update_device_state(device, state)`, `create_order(product_ids)`, `log_ring_event(event)`, `get_ring_event(event_id)`, `update_ring_event(event_id, fields)`
    - Make `init_db()` idempotent — calling again does not duplicate seed data (use `INSERT OR IGNORE` or check-before-insert)
    - Enable WAL mode (`PRAGMA journal_mode=WAL`) for better read concurrency
    - _Design: §Component 4 (DatabaseManager), §Algorithm 5 (init_db), §Data Models 1–5_
    - _Design: Function 5 (init_db postconditions)_

  - [~]* 1.3 Write unit tests for DatabaseManager in `backend/tests/test_database.py`
    - Test `init_db()` creates all 5 tables
    - Test `products` table has exactly 6 seeded products
    - Test `household_memory` has default seeded context
    - Test `device_states` has initial device states
    - Test `search_products` returns correct matches by tag and name overlap
    - Test `get_product` returns None for non-existent id
    - Test `create_order` persists order with correct total
    - Create `backend/tests/__init__.py` and `backend/tools/__init__.py` package files
    - _Design: §Testing Strategy (Unit Testing — test_database.py), Design: Function 5_

  - [~]* 1.4 Write property-based test for idempotent seeding in `backend/tests/test_database_property.py`
    - **Property 8: Idempotent Seed** — Calling `init_db()` multiple times does not duplicate seed data
    - **Validates: Design: Property 8** (`∀ n > 1 : count(products after n init calls) == 6`)
    - Use `hypothesis` with `@given(st.integers(min_value=1, max_value=10))` to call `init_db()` N times and assert product count stays 6

---

- [x] 2. MCP Server (Streamable HTTP, spec 2025-11-25)
  - [x] 2.1 Implement `backend/mcp_server.py` — JSON-RPC 2.0 router with 6-tool registry
    - Create `MCPServer` class with `PROTOCOL_VERSION = "2025-11-25"` class attribute
    - Implement `handle_initialize(request)`: return `{"protocolVersion": "2025-11-25", "capabilities": {"tools": {"listChanged": false}}, "serverInfo": {"name": "omnipulse-mcp", "version": "1.0.0"}}`
    - Implement `handle_tools_list(request)`: return the 6 tool definitions with full JSON-Schema input schemas from a `ToolRegistry`
    - Implement `handle_tools_call(request)`: route `params.name` to the correct tool via registry, call `tool.execute(params.arguments, db)`, return `{"content": result.content, "ui": result.ui}`
    - Implement `route(json_rpc_request)`: top-level dispatch for `initialize`, `tools/list`, `tools/call`; validate JSON-RPC 2.0 envelope (`jsonrpc == "2.0"`, `id`, `method`)
    - Return JSON-RPC error `-32700` (parse error) for null request, `-32600` (invalid request) for wrong `jsonrpc` version, `-32601` (method not found) for unknown method, `-32602` (invalid params) for unknown tool name
    - Create `ToolRegistry` class with `register(tool)`, `list_all()`, `get(name)`, `names` property
    - Create `MCPTool` base class/protocol with `name`, `description`, `input_schema`, `execute(arguments, db)` returning `{"content": [...], "ui": {...}}`
    - Support both plain JSON and `text/event-stream` (SSE) response formats (check `Accept` header)
    - _Design: §Component 1 (MCPServer), §Algorithm 1 (MCP JSON-RPC Router), §Function 1 (route)_
    - _Design: Property 1 (Protocol Version), Property 3 (Tool Count)_

  - [~]* 2.2 Write unit tests for MCP server in `backend/tests/test_mcp_server.py`
    - Test `route()` with `initialize` returns `protocolVersion: "2025-11-25"`
    - Test `route()` with `tools/list` returns exactly 6 tools
    - Test `route()` with `tools/call` routes to correct tool and returns `content` + `ui`
    - Test error responses: unknown method returns `-32601`, null request returns `-32700`, wrong jsonrpc version returns `-32600`, unknown tool returns `-32602`
    - Test response echoes the request `id` in all cases
    - _Design: §Error Handling (Scenarios 1–2), §Function 1 (postconditions)_

  - [~]* 2.3 Write property-based tests for protocol version and tool count in `backend/tests/test_mcp_server_property.py`
    - **Property 1: Protocol Version** — For all `initialize` requests, `response.result.protocolVersion == "2025-11-25"`
    - **Validates: Design: Property 1** (`∀ req : method == "initialize" ⟹ response.result.protocolVersion == "2025-11-25"`)
    - **Property 3: Tool Count** — `tools/list` always returns exactly 6 tools
    - **Validates: Design: Property 3** (`length(tools_list_response.result.tools) == 6`)
    - Use `hypothesis` to generate valid initialize requests with arbitrary `id` values (string, int) and verify protocolVersion is constant

---

- [x] 3. MCP domain tool modules
  - [x] 3.1 Implement `backend/tools/memory_tools.py` — household memory retrieval and persistence
    - Implement `GetHouseholdMemoryTool(MCPTool)` with `name="get_household_memory"`, JSON-Schema for `{session_id: str}`
    - `execute()` calls `db.get_memory(session_id)`, returns `{"content": [{type: "text", text: summary}], "ui": {type: "memory_card", ...}}`
    - Implement `SaveHouseholdMemoryTool(MCPTool)` with `name="save_household_memory"`, JSON-Schema for `{session_id: str, context: str, health_notes: list, dietary_restrictions: list, preferences: dict}`
    - `execute()` calls `db.save_memory(...)` and returns confirmation
    - _Design: §Component 3 (MCP Tools), §Data Model 1 (HouseholdMemory), §SKILL.md Step 1 (Context Retrieval)_

  - [x] 3.2 Implement `backend/tools/commerce_tools.py` — product search, carousel builder, and instant checkout
    - Implement `SearchAndBuildCarouselTool(MCPTool)` with `name="search_and_build_carousel"`, JSON-Schema for `{query: str, tags: list[str]}`
    - `execute()` follows Algorithm 3: lowercase query, match products by name/tag/category overlap, filter to in-stock only, build `{"content": [...], "ui": {type: "carousel", title, products}}` with each product as `{id, name, price, image_url, description, buyable}`
    - Return empty carousel with explanatory text when no matches found
    - Do not mutate catalog data
    - Implement `ExecuteInstantCheckoutTool(MCPTool)` with `name="execute_instant_checkout"`, JSON-Schema for `{product_ids: list[int]}`
    - `execute()` follows Algorithm 5: validate product_ids non-empty, look up each product, accumulate total, create order via `db.create_order()`, return `{"content": [...], "ui": {type: "checkout_card", title, orderId, items, total}}`
    - Return checkout error card with `total: 0` when a product id is not found
    - _Design: §Component 3, §Algorithm 3 (Product Search), §Algorithm 5 (Instant Checkout), §Data Models 2 & 5_
    - _Design: Function 4 (search_and_build_carousel), Property 4 (Checkout Total), Property 5 (Carousel Stock)_

  - [x] 3.3 Implement `backend/tools/smarthome_tools.py` — lighting, HVAC, and routine state control
    - Implement `UpdateSmarthomeStateTool(MCPTool)` with `name="update_smarthome_state"`, JSON-Schema for `{device: str, state: dict}`
    - Validate `device_type` in `{"light", "hvac", "routine"}`; for lights validate `brightness` in [0,100] and `color` in known palette; for hvac validate `temperature` in [60,90]
    - `execute()` calls `db.update_device_state(device, state)`, returns `{"content": [...], "ui": {type: "smarthome_card", title, devices}}`
    - _Design: §Component 3, §Data Model 3 (DeviceState), §Algorithm 2 (Steps 3 — Smart Home domain)_

  - [x] 3.4 Implement `backend/tools/ring_tools.py` — simulated Ring camera/doorbell event handler
    - Implement `HandleRingEventTool(MCPTool)` with `name="handle_ring_event"`, JSON-Schema for `{event_type: str, description: str}`
    - Validate `event_type` in `{"package_delivery", "guest_arrival"}` (reject others with error)
    - `execute()` follows Algorithm 4: persist event via `db.log_ring_event()`, retrieve household memory, cross-check `guest_arrival` against memory context for expected guests (parents, guest keywords), set `verified` and `action_taken`, update event record, return `{"content": [...], "ui": {type: "ring_alert_card", title, eventType, verified, description}}`
    - _Design: §Component 3, §Data Model 4 (RingEvent), §Algorithm 4 (Ring Event Handler), §SKILL.md Step 4_
    - _Design: Property 6 (Ring Verification)_

  - [x]* 3.5 Write unit tests for all 6 tools in `backend/tests/test_tools.py`
    - Test `get_household_memory` returns seeded context for "default" session
    - Test `save_household_memory` persists and round-trips correctly
    - Test `search_and_build_carousel` matches by name, tag overlap, and category
    - Test `search_and_build_carousel` returns only in-stock products
    - Test `search_and_build_carousel` returns empty carousel for no matches
    - Test `execute_instant_checkout` returns correct total for known product ids
    - Test `execute_instant_checkout` returns error card for unknown product id
    - Test `update_smarthome_state` updates device state and returns smarthome_card
    - Test `update_smarthome_state` rejects invalid brightness/temperature ranges
    - Test `handle_ring_event` with `guest_arrival` and memory mentioning parents → verified true
    - Test `handle_ring_event` with `guest_arrival` and empty memory → verified false
    - Test `handle_ring_event` with `package_delivery` → verified true
    - Test `handle_ring_event` rejects invalid event_type
    - _Design: §Testing Strategy (Unit Testing — test_tools.py), §Error Handling (Scenarios 3, 5, 6)_

  - [x]* 3.6 Write property-based tests for carousel, checkout, and ring in `backend/tests/test_tools_property.py`
    - **Property 4: Checkout Total Consistency** — For any list of valid product ids, `ui.total == sum(prices)`
    - **Validates: Design: Property 4** (`∀ product_ids : ui.total == Σ price(p) for p in products`)
    - **Property 5: Carousel Stock Invariant** — Every returned carousel product has `buyable == true`
    - **Validates: Design: Property 5** (`∀ carousel_result : ∀ p ∈ products : p.buyable == true`)
    - **Property 6: Ring Verification** — A `guest_arrival` event is `verified == true` iff memory context mentions expected guests
    - **Validates: Design: Property 6** (`∀ guest_arrival_event : verified == contains(memory.context, expected_guest_keywords)`)
    - Use `hypothesis` to generate arbitrary subsets of product ids for checkout total test; arbitrary query strings for carousel stock test; memory contexts with/without guest keywords for ring verification test

---

> **Checkpoint — Backend core (database + MCP server + tools) is complete:**
> Ensure all tests pass, ask the user if questions arise.

- [x] 4. Agent orchestrator and FastAPI entry point
  - [x] 4.1 Implement `backend/agent.py` — AgentOrchestrator with smart fallback and LLM path
    - Create `AgentOrchestrator` class initialized with `db` and `mcp_server` (or tool registry)
    - Implement `orchestrate(message, session_id)`: always call `get_household_memory` first (SKILL.md mandate), then detect intent, chain MCP tool calls, compose `AgentResponse` with `speech` (str), `cards` (list), `tool_calls` (log)
    - Implement `smart_fallback(message, session_id)`: deterministic rule-based orchestration following Algorithm 2 — keyword matching for smarthome ("light", "warm", "cool", "thermostat"), commerce ("buy", "order", "shop", "search", "wellness"), checkout ("checkout", "purchase", "confirm"), ring ("guest", "ring", "package", "doorbell"); multi-domain keywords trigger parallel tool calls; use memory preferences to customize (warm lighting if memory.preferences.lighting == "warm", comfort hvac if knee pain in health_notes)
    - Implement `llm_orchestrate(message, memory, session_id)`: LLM-driven tool selection using Gemini/OpenAI/Bedrock via env vars (`GEMINI_API_KEY`, `OPENAI_API_KEY`, AWS credentials); return list of tool invocations; gracefully fall back to `smart_fallback` when no key is set
    - Implement `handle_ring_event(event)`: proactive handler for webhook-triggered Ring events following Algorithm 4 flow
    - Build internal tool invocation that calls tools in-process (not network round-trip per design performance section)
    - Compose speech by joining speech_parts; default to help message when no intent detected
    - _Design: §Component 2 (AgentOrchestrator), §Algorithm 2 (Agent Orchestration), §Function 2 (orchestrate), §Function 3 (smart_fallback)_
    - _Design: Property 2 (Memory-First), Property 7 (Fallback Independence), Property 10 (UI Card Type)_
    - _SKILL.md Steps 1–4_

  - [x] 4.2 Implement `backend/main.py` — FastAPI entry point with all endpoints
    - Create FastAPI app with CORS enabled for `localhost:5173` (Vite dev server)
    - Initialize `DatabaseManager` and call `init_db()` on startup
    - Initialize `MCPServer` with `ToolRegistry` registering all 6 tools (wire tools into registry)
    - Initialize `AgentOrchestrator` with db and mcp_server
    - Implement `POST /mcp`: MCP Streamable HTTP endpoint handling JSON-RPC 2.0; check `Accept: text/event-stream` header to return SSE response via `sse-starlette`, otherwise return plain JSON; pass request body to `mcp_server.route()`
    - Implement `POST /chat`: accept `{message, session_id}`, call `agent.orchestrate(message, session_id)`, return `{speech, cards, tool_calls}` JSON
    - Implement `POST /webhook/ring`: accept `{event_type, description}`, validate event_type in allowed set (reject with HTTP 400 otherwise), call `agent.handle_ring_event()`, push alert to SSE event queue, return `{speech, ring_alert_card}`
    - Implement `GET /events`: SSE stream endpoint that pushes proactive Ring event alerts to the frontend using `sse-starlette`; use an asyncio Queue for event fan-out
    - _Design: §Component 5 (FastAPI Entry Point), §Architecture (Request-Response Flow, Ring Webhook Flow)_
    - _Design: §Security (CORS, Ring Webhook validation), §Performance (SSE Streaming)_

  - [x]* 4.3 Write unit tests for AgentOrchestrator in `backend/tests/test_agent.py`
    - Test `smart_fallback()` calls `get_household_memory` first (tool_calls[0].name == "get_household_memory")
    - Test smarthome-only command triggers `update_smarthome_state` with warm lighting from memory preferences
    - Test commerce-only command triggers `search_and_build_carousel` with tags derived from memory
    - Test checkout command triggers `execute_instant_checkout`
    - Test multi-domain command (smarthome + commerce) triggers both tool domains
    - Test response structure: `speech` is non-empty, `cards` are valid UI card types
    - Test fallback when no LLM key is set (no exception, valid response)
    - Test default help speech when no intent detected
    - _Design: §Testing Strategy (Unit Testing — test_agent.py), §Function 2 & 3 (postconditions)_

  - [x]* 4.4 Write property-based tests for agent invariants in `backend/tests/test_agent_property.py`
    - **Property 2: Memory-First Invocation** — `get_household_memory` is always invoked before any other tool
    - **Validates: Design: Property 2** (`∀ orchestrate(m, s) : tool_calls[0].name == "get_household_memory"`)
    - **Property 7: Fallback Independence** — `smart_fallback` produces non-empty speech without any LLM key
    - **Validates: Design: Property 7** (`smart_fallback(m, s).speech ≠ ""`)
    - **Property 10: UI Card Type** — Every card has `type` in `{"carousel", "smarthome_card", "ring_alert_card", "checkout_card"}`
    - **Validates: Design: Property 10** (`∀ card ∈ cards : card.type ∈ {...}`)
    - Use `hypothesis` to generate arbitrary non-empty message strings and session ids; verify memory-first ordering, non-empty speech, and valid card types

  - [x]* 4.5 Write integration tests for API endpoints in `backend/tests/test_api_integration.py`
    - Use FastAPI `TestClient` to test `/mcp`, `/chat`, `/webhook/ring` end-to-end
    - Test `/mcp` initialize handshake returns `protocolVersion: "2025-11-25"`
    - Test `/mcp` tools/list returns 6 tools
    - Test `/mcp` tools/call for `search_and_build_carousel` returns carousel UI
    - Test `/mcp` with `Accept: text/event-stream` returns SSE-formatted response
    - Test `/chat` returns valid `{speech, cards, tool_calls}` JSON for multi-domain command
    - Test `/chat` with purchase intent returns checkout_card
    - Test `/webhook/ring` with `guest_arrival` returns ring_alert_card and logs event
    - Test `/webhook/ring` with invalid event_type returns HTTP 400
    - Test full flow: user message → agent → MCP tools → database → response
    - **Property 9: Frontend HTTP** — Verify endpoints accept and return real JSON-RPC over HTTP (not mock)
    - **Validates: Design: Property 9** (real HTTP requests to `/mcp` and `/chat`)
    - _Design: §Testing Strategy (Integration Testing — test_api_integration.py)_

---

- [x] 5. Frontend Echo Show simulator
  - [x] 5.1 Scaffold Vite + React + TypeScript + Tailwind project in `frontend/`
    - Run `npm create vite@latest frontend -- --template react-ts` to scaffold
    - Install dependencies: `react`, `react-dom`, `lucide-react`, `tailwindcss`, `postcss`, `autoprefixer`
    - Configure Tailwind CSS with dark-mode glassmorphic theme (dark background, translucent panels with backdrop-blur)
    - Configure `vite.config.ts` with proxy to `http://localhost:8000` for `/mcp`, `/chat`, `/webhook/ring`, `/events` (or use direct `http://localhost:8000` fetch)
    - Create `src/types.ts` with TypeScript interfaces: `ChatResponse`, `UICard` (union of `CarouselCard`, `SmartHomeCard`, `RingAlertCard`, `CheckoutCard`), `ProductItem`, `DeviceStateItem`, `MCPRequest`, `MCPResponse`
    - Create `src/api.ts` with fetch wrappers: `sendChat(message, sessionId)`, `mcpInitialize()`, `mcpToolsList()`, `mcpToolsCall(name, args)`, `triggerRingEvent(eventType, description)`, `connectEventStream()` (SSE via EventSource)
    - _Design: §Component 6 (Frontend Simulator), §Data Model 7 (MCP UI Card Schemas)_
    - _tech.md: Frontend Stack (Vite + React + Tailwind CSS + Lucide Icons)_

  - [x] 5.2 Build core layout and glassmorphic dashboard shell in `frontend/src/App.tsx`
    - Create dark-mode Echo Show 15-inspired layout with glassmorphic panel styling
    - Render placeholder areas for: voice orb (top center), transcript bar (below orb), Rich Media Canvas (center), MCP Inspector drawer (right side), quick-demo chips (bottom), Simulate Ring Event button (corner)
    - Implement state management: `messages` (transcript history), `cards` (rendered UI cards), `inspectorPayloads` (MCP JSON-RPC log), `isListening` (voice state), `sessionId` (default "default")
    - Wire `sendChat()` to update messages and cards from `ChatResponse`
    - _Design: §Component 6, §Architecture (Frontend layer), tech.md: UI Design_

  - [x] 5.3 Build MCP Protocol Inspector drawer in `frontend/src/components/McpInspector.tsx`
    - Create slide-out drawer component showing real-time JSON-RPC payloads
    - On mount, send real `initialize` request to `http://localhost:8000/mcp` and display the response (proving `protocolVersion: "2025-11-25"`)
    - Send real `tools/list` request and display the 6 tool schemas
    - When a tool is called (from /chat orchestration), display the `tools/call` request and response payloads
    - Use a ring buffer (last 20 messages) to avoid unbounded memory growth
    - Render raw JSON with syntax highlighting (collapsible sections per method)
    - Display each payload with method label: `initialize`, `tools/list`, `tools/call`
    - _Design: §Architecture (MCP Protocol Inspector Flow), tech.md: MCP Protocol Inspector Drawer_
    - _Design: Property 9 (Frontend HTTP — real runtime requests to /mcp)_

  - [x] 5.4 Build Rich Media Canvas in `frontend/src/components/RichMediaCanvas.tsx` with card renderers
    - Create canvas component that dynamically renders cards from `ChatResponse.cards` based on `card.type`
    - Implement `CarouselCard` renderer: horizontal scrollable product cards with image, name, price, description, and "Buy" button; use lazy loading for product images
    - Implement `SmartHomeCard` renderer: device state display (on/off toggle, brightness slider, color indicator, temperature, mode) with glassmorphic styling
    - Implement `CheckoutCard` renderer: order confirmation with orderId, item list, and total; success checkmark animation
    - Implement `RingAlertCard` renderer: alert banner with event type, verified badge (green check if verified, yellow warning if not), and description
    - Wire "Buy" button on carousel products to send a checkout command via `sendChat("checkout product {id}")`
    - _Design: §Component 6, §Data Model 7 (UICard union type), §Example 4 (Checkout via Frontend Button)_
    - _tech.md: Dynamic Rich Media Canvas_

  - [x] 5.5 Build voice I/O with Web Speech API in `frontend/src/hooks/useVoice.ts` and `frontend/src/components/VoiceOrb.tsx`
    - Create `useVoice` hook wrapping `window.SpeechRecognition` (STT) and `window.speechSynthesis` (TTS)
    - Implement start/stop listening with transcript callback; handle browser compatibility (webkit prefix fallback)
    - Implement `speak(text)` function using `SpeechSynthesisUtterance` for TTS; call after each chat response
    - Create animated `VoiceOrb` component: pulsing/breathing animation when listening, calm glow when idle, ripple effect when speaking
    - Create `TranscriptBar` component showing live transcription and assistant responses
    - Wire voice input to `sendChat()` and voice output to `speak(speech)` from response
    - _Design: §Component 6, tech.md: Voice Integration (Web Speech API STT/TTS)_

  - [x] 5.6 Build quick-demo chips and Simulate Ring Event button, wire all components into App
    - Create `DemoChips` component with preset commands: "Prep home for parents and find low-sodium items", "Set warm lighting", "Search wellness products", "Checkout items" — each chip sends the preset to `sendChat()`
    - Create `RingTriggerButton` component that calls `triggerRingEvent("guest_arrival", "Two people at front door")` and connects to `/events` SSE stream via `EventSource` to receive proactive ring alerts
    - Wire SSE ring alert events to display `RingAlertCard` in the canvas and speak the notification via TTS
    - Import and compose all components (`VoiceOrb`, `TranscriptBar`, `RichMediaCanvas`, `McpInspector`, `DemoChips`, `RingTriggerButton`) into `App.tsx`
    - Ensure all real HTTP requests target `http://localhost:8000` (no mock data)
    - _Design: §Architecture (Ring Webhook Flow), §Example 5 (Simulate Ring Event), tech.md: Simulate Ring Event Button_
    - _Design: Property 9 (Frontend HTTP — real runtime requests, not mock)_

---

> **Checkpoint — Full application (backend + frontend) is wired together:**
> Ensure all tests pass, ask the user if questions arise.

- [x] 6. Deployment artifacts and verification run
  - [x] 6.1 Create `docker-compose.yml` for 1-command startup
    - Define `backend` service: Python 3.11 image, install `requirements.txt`, run `uvicorn main:app --host 0.0.0.0 --port 8000` from `backend/`
    - Define `frontend` service: Node 18 image, install npm deps, run `npm run dev -- --host` from `frontend/`, depends on `backend`
    - Expose ports 8000 (backend) and 5173 (frontend)
    - Ensure judges can run `docker-compose up` to start both services
    - _structure.md: docker-compose.yml (1-command startup for judges)_

  - [x] 6.2 Create `LICENSE` file with MIT License
    - Add standard MIT License text with copyright year and holder
    - _structure.md: LICENSE (MIT License, Required for Public GitHub Repo)_

  - [x] 6.3 Create `README.md` with architecture, setup guide, and MCP verification steps
    - Document architecture overview (three-layer: frontend, backend/MCP, SQLite)
    - Document setup: `pip install -r backend/requirements.txt`, `cd frontend && npm install`
    - Document run commands: backend `uvicorn main:app --reload`, frontend `npm run dev`
    - Document MCP verification steps: open inspector, verify `protocolVersion: "2025-11-25"`, verify 6 tools, verify tools/call returns carousel
    - Document optional LLM env vars: `GEMINI_API_KEY`, `OPENAI_API_KEY`, AWS Bedrock credentials
    - Document the Simulate Ring Event feature and cross-session memory
    - _structure.md: README.md (Architecture, setup guide, and MCP verification steps)_

  - [x] 6.4 Run verification: confirm MCP handshake, tool count, and backend startup
    - Start the backend: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000`
    - Verify `/mcp` initialize returns `protocolVersion: "2025-11-25"` (send a curl/httpx request and check the response)
    - Verify `/mcp` tools/list returns exactly 6 tool definitions
    - Verify `/mcp` tools/call for `search_and_build_carousel` returns a carousel UI payload
    - Verify `/chat` returns `{speech, cards}` for a multi-domain command
    - Verify `/webhook/ring` logs an event and returns a ring_alert_card
    - Verify SQLite `omnipulse.db` is auto-created with seed data
    - Confirm no external API key is required for the default smart-fallback demo
    - _Design: Property 1 (Protocol Version), Property 3 (Tool Count), Property 9 (Frontend HTTP)_
    - _tech.md: Critical Code Rules for Judges (protocolVersion 2025-11-25)_

---

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP, though they are recommended for validating the 10 correctness properties from the design
- Each task references specific design sections (components, algorithms, functions, properties) and steering-file requirements for traceability
- Checkpoints ensure incremental validation after backend core (Task 3) and full application wiring (Task 5)
- Property tests validate universal correctness properties using `hypothesis`; unit tests validate specific examples and edge cases
- The backend uses in-process tool calls (no network round-trip) for the agent's internal MCP invocations, while the frontend inspector sends real HTTP requests to `/mcp` for protocol compliance proof
- All database queries use parameterized SQL (`?` placeholders) to prevent injection
- The smart-fallback agent enables the full demo without any LLM API key; optional keys enable richer orchestration

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "1.4", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.1", "3.2", "3.3", "3.4"] },
    { "id": 3, "tasks": ["3.5", "3.6", "4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3", "4.4"] },
    { "id": 5, "tasks": ["4.5", "5.1"] },
    { "id": 6, "tasks": ["5.2"] },
    { "id": 7, "tasks": ["5.3", "5.4", "5.5"] },
    { "id": 8, "tasks": ["5.6"] },
    { "id": 9, "tasks": ["6.1", "6.2", "6.3"] },
    { "id": 10, "tasks": ["6.4"] }
  ]
}
```
