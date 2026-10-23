---
name: omnipulse-orchestrator
description: Autonomous Alexa+ household, commerce, and Ring access-control orchestrator with persistent cross-session memory.
version: 1.0.0
mcp_spec_version: "2025-11-25"
transport: streamable-http
---

# Alexa+ OmniPulse Agent Skill

## Instructions
When a user interacts with Alexa+, always execute the following workflow:
1. **Context Retrieval:** Call `get_household_memory` first to check stored health conditions, dietary restrictions, and preferences.
2. **Multi-Service Execution:** If a request spans multiple domains (e.g., preparing the home for guests and ordering supplies), autonomously chain `update_smarthome_state` and `search_and_build_carousel` in a single turn.
3. **Rich UI Rendering:** Always include structured UI payloads (`carousel`, `checkout_card`, `smarthome_card`, or `ring_alert_card`) when invoking commerce or device tools.
4. **Purchasing Confirmation:** When the user says "Buy", "Checkout", or clicks purchase, invoke `execute_instant_checkout` and return an order confirmation card.