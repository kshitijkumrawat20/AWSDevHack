# Technical Stack & Standards

## Backend & MCP Server
- **Language & Framework:** Python 3.11+, FastAPI
- **MCP Compliance:** Must implement Model Context Protocol (MCP) specification `2025-11-25` over **Streamable HTTP** (`POST /mcp` handling JSON-RPC 2.0 `initialize`, `tools/list`, and `tools/call` with HTTP/SSE streaming support).
- **Agent Orchestration:** LangGraph / LangChain or AWS Bedrock (Claude) with fallback support for Google Gemini / OpenAI API via environment variables so local testing never blocks[cite: 1].
- **Database / State:** SQLite (`omnipulse.db`) for zero-config persistent cross-session user memory, cart state, and smart home state (ensuring judges can run the repo locally without external DB credentials).
- **Voice Integration:** Web Speech API (Browser STT/TTS) with optional ElevenLabs TTS endpoint for ultra-realistic Alexa+ voice output[cite: 1].

## Frontend (Alexa+ Echo Show Web Simulator)
- **Stack:** Next.js (React) or Vite + React + Tailwind CSS + Lucide Icons.
- **UI Design:** Dark-mode Echo Show 15 / Alexa+ glassmorphic dashboard featuring:
  - Animated Alexa+ voice orb & live transcript bar.
  - Dynamic Rich Media Canvas (renders Product Carousels, Checkout Cards, and Smart Home Controls from MCP tool metadata).
  - Live **MCP Protocol Inspector Drawer** (shows real-time `initialize`, `tools/list`, and `tools/call` JSON-RPC payloads over Streamable HTTP to prove runtime technology usage to judges).
  - **"Simulate Ring Event" Button** to trigger proactive webhook workflows.


Critical Code Rules for Judges
The MCP endpoint (/mcp) MUST explicitly report protocolVersion: "2025-11-25" during the initialize handshake.

The frontend simulator MUST make real runtime HTTP requests to the /mcp and /agent endpoints and visually display the MCP JSON-RPC exchange in an inspector panel.