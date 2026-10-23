# Repository Structure & Submission Rules

```text
alexa-plus-omnipulse/
├── .kiro/
│   └── steering/                 # Product, tech, and structure specs
├── skills/
│   └── omnipulse-orchestrator/
│       └── SKILL.md              # Agent Skill definition (Required for Alexa+ Track)
├── backend/
│   ├── main.py                   # FastAPI entry point + Streamable HTTP /mcp endpoint
│   ├── mcp_server.py             # MCP Spec 2025-11-25 JSON-RPC & SSE handler
│   ├── agent.py                  # LangGraph / Bedrock multi-step agent orchestrator
│   ├── tools/
│   │   ├── memory_tools.py       # Cross-session persistent household context
│   │   ├── commerce_tools.py     # Catalog search, carousel builder, 1-click checkout
│   │   ├── smarthome_tools.py    # Lighting, HVAC, and routine state control
│   │   └── ring_tools.py         # Simulated Ring camera/doorbell event handler
│   ├── database.py               # SQLite state initialization & seed data
│   └── requirements.txt
├── frontend/                     # React + Tailwind Alexa+ Echo Show Simulator
├── docker-compose.yml            # 1-command startup for judges
├── LICENSE                       # MIT License (Required for Public GitHub Repo)
└── README.md                     # Architecture, setup guide, and MCP verification steps