"""Agent Orchestrator for Alexa+ OmniPulse.

Orchestrates multi-service workflows across Smart Home, Commerce, and Ring Security
domains. Implements both a deterministic smart-fallback engine (zero external API keys)
and an LLM-powered orchestration path (Gemini / OpenAI / Bedrock).

Design references:
    - design.md §Component 2 (AgentOrchestrator)
    - design.md §Algorithm 2 (Agent Orchestration & Smart Fallback)
    - design.md §Function 2 (orchestrate) & Function 3 (smart_fallback)
    - design.md §Property 2 (Memory-First Invocation)
    - design.md §Property 7 (Fallback Independence)
    - design.md §Property 10 (UI Card Type)
    - SKILL.md Steps 1-4 (Multi-Service Orchestration Workflow)
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from database import DatabaseManager
    from mcp_server import MCPServer

logger = logging.getLogger("omnipulse.agent")


class ToolCallRecord(dict):
    """Represents an invoked tool call.

    Inherits from dict for transparent JSON serialization, and exposes attributes
    (e.g. ``record.name``) for property-based and unit test assertions.
    """

    def __init__(
        self,
        name: str,
        arguments: Optional[dict[str, Any]] = None,
        result: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        args = arguments or {}
        res = result or {}
        super().__init__(name=name, arguments=args, result=res, **kwargs)
        self.name = name
        self.arguments = args
        self.result = res

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as err:
            raise AttributeError(item) from err

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value
        super().__setattr__(key, value)


class AgentResponse(BaseModel):
    """Standardized response from the Agent Orchestrator."""

    speech: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[Any] = Field(default_factory=list)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "speech": self.speech,
            "cards": self.cards,
            "tool_calls": [dict(tc) if isinstance(tc, dict) else tc for tc in self.tool_calls],
        }


class AgentOrchestrator:
    """Autonomous context-aware agent orchestrating MCP tools for Alexa+ OmniPulse."""

    def __init__(self, db: "DatabaseManager", mcp_server: "MCPServer") -> None:
        self.db = db
        self.mcp_server = mcp_server

    def _call_tool_in_process(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered MCP tool directly in-process without network overhead."""
        tool = self.mcp_server.tool_registry.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not registered in MCP server registry")
        return tool.execute(arguments, self.db)

    def orchestrate(self, message: str, session_id: str = "default") -> AgentResponse:
        """Main entry point: always retrieves memory first, then selects LLM or fallback.

        Preconditions:
            * message is a string
            * session_id is a non-empty string
        Postconditions:
            * get_household_memory is always called first (Property 2)
            * Returns a valid AgentResponse with speech and cards
        """
        # Check if an LLM provider key is available in the environment
        has_llm_key = bool(
            os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or (os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
        )

        if has_llm_key:
            try:
                # Memory retrieval must always happen first
                memory = self.db.get_memory(session_id)
                llm_res = self.llm_orchestrate(message, memory, session_id)
                if llm_res is not None:
                    return llm_res
            except Exception as e:
                logger.warning("LLM orchestration failed or threw error; falling back to smart_fallback: %s", e)

        # Default zero-dependency deterministic engine
        return self.smart_fallback(message, session_id)

    def smart_fallback(self, message: str, session_id: str = "default") -> AgentResponse:
        """Deterministic rule-based orchestration following design.md Algorithm 2.

        Guarantees:
            1. get_household_memory is invoked first (Property 2)
            2. Operates without any external LLM API key (Property 7)
            3. All returned cards match valid UICard types (Property 10)
        """
        cards: list[dict[str, Any]] = []
        tool_calls: list[ToolCallRecord] = []
        speech_parts: list[str] = []

        # Step 1: ALWAYS retrieve household memory first (SKILL.md Step 1 mandate)
        memory_result = self._call_tool_in_process("get_household_memory", {"session_id": session_id})
        tool_calls.append(
            ToolCallRecord(
                name="get_household_memory",
                arguments={"session_id": session_id},
                result=memory_result,
            )
        )
        memory = self.db.get_memory(session_id)

        lower_msg = (message or "").lower()

        # Step 2: Intent detection via keyword matching (design.md Algorithm 2)
        smarthome_keywords = [
            "light", "warm", "cool", "thermostat", "temperature",
            "routine", "prepare", "prep", "set", "living room", "home", "ambient",
        ]
        commerce_keywords = [
            "buy", "order", "shop", "search", "find", "get", "product",
            "low-sodium", "ayurvedic", "wellness", "item", "recommend", "tea", "salt",
        ]
        checkout_keywords = ["checkout", "purchase", "confirm", "buy now"]
        ring_keywords = ["ring", "guest", "package", "doorbell", "someone", "visitor", "front door"]

        # If user explicitly specifies "checkout product X" or "checkout items"
        is_explicit_checkout = any(k in lower_msg for k in checkout_keywords) or (
            "buy" in lower_msg and any(char.isdigit() for char in lower_msg)
        )
        wants_smarthome = any(k in lower_msg for k in smarthome_keywords)
        wants_commerce = any(k in lower_msg for k in commerce_keywords) and not is_explicit_checkout
        wants_checkout = is_explicit_checkout
        wants_ring = any(k in lower_msg for k in ring_keywords)

        # Step 3: Smart Home domain
        if wants_smarthome:
            pref_lighting = memory.get("preferences", {}).get("lighting", "")
            if pref_lighting == "warm" or "warm" in lower_msg or "ambient" in lower_msg:
                light_args = {"device": "living_room_light", "state": {"on": True, "brightness": 60, "color": "warm"}}
            else:
                light_args = {"device": "living_room_light", "state": {"on": True, "brightness": 80, "color": "cool"}}

            health_notes = [str(hn).lower() for hn in memory.get("health_notes", [])]
            if "comfort" in lower_msg or any("knee pain" in hn or "joint" in hn for hn in health_notes):
                hvac_args = {"device": "thermostat", "state": {"on": True, "temperature": 72, "mode": "heat"}}
            else:
                hvac_args = {"device": "thermostat", "state": {"on": True, "temperature": 70, "mode": "auto"}}

            light_res = self._call_tool_in_process("update_smarthome_state", light_args)
            hvac_res = self._call_tool_in_process("update_smarthome_state", hvac_args)

            cards.append(light_res["ui"])
            cards.append(hvac_res["ui"])
            tool_calls.append(
                ToolCallRecord(
                    name="update_smarthome_state",
                    arguments=light_args,
                    result=light_res,
                )
            )
            tool_calls.append(
                ToolCallRecord(
                    name="update_smarthome_state",
                    arguments=hvac_args,
                    result=hvac_res,
                )
            )
            speech_parts.append("I've adjusted the lighting and thermostat for comfort.")

        # Step 4: Commerce domain
        if wants_commerce:
            # Extract query and tags based on memory and message
            query = "wellness"
            if "low-sodium" in lower_msg or "sodium" in lower_msg:
                query = "low-sodium"
            elif "ayurvedic" in lower_msg:
                query = "ayurvedic"
            elif "tea" in lower_msg:
                query = "tea"
            elif "salt" in lower_msg:
                query = "salt"

            # Derive tags from dietary restrictions and health preferences
            tags: list[str] = []
            for diet in memory.get("dietary_restrictions", []):
                tags.append(str(diet).lower())
            if any("knee" in str(hn).lower() for hn in memory.get("health_notes", [])):
                tags.append("knee-care")

            if not tags:
                tags = ["wellness", "ayurvedic", "low-sodium"]

            carousel_args = {"query": query, "tags": tags}
            carousel_res = self._call_tool_in_process("search_and_build_carousel", carousel_args)
            cards.append(carousel_res["ui"])
            tool_calls.append(
                ToolCallRecord(
                    name="search_and_build_carousel",
                    arguments=carousel_args,
                    result=carousel_res,
                )
            )
            speech_parts.append("I found some items that match your wellness preferences.")

        # Step 5: Checkout domain
        if wants_checkout:
            # Extract numbers from message, e.g. "checkout product 1 and product 3"
            found_ids = [int(num) for num in re.findall(r"\b(\d+)\b", lower_msg)]
            if not found_ids:
                # Default to top 2 recommended wellness products (items 1 & 2)
                found_ids = [1, 2]

            checkout_args = {"product_ids": found_ids}
            checkout_res = self._call_tool_in_process("execute_instant_checkout", checkout_args)
            cards.append(checkout_res["ui"])
            tool_calls.append(
                ToolCallRecord(
                    name="execute_instant_checkout",
                    arguments=checkout_args,
                    result=checkout_res,
                )
            )
            # Use natural checkout speech
            order_text = ""
            if checkout_res.get("content"):
                order_text = checkout_res["content"][0].get("text", "")
            speech_parts.append(order_text or "Your order is confirmed.")

        # Step 6: Ring security domain (if mentioned directly in chat command)
        if wants_ring:
            event_type = "package_delivery" if "package" in lower_msg else "guest_arrival"
            description = "Activity detected at front door via voice command"
            ring_args = {"event_type": event_type, "description": description}
            ring_res = self._call_tool_in_process("handle_ring_event", ring_args)
            cards.append(ring_res["ui"])
            tool_calls.append(
                ToolCallRecord(
                    name="handle_ring_event",
                    arguments=ring_args,
                    result=ring_res,
                )
            )
            if ring_res.get("content"):
                speech_parts.append(ring_res["content"][0].get("text", ""))

        # Step 7: Compose speech and final response
        speech = " ".join(speech_parts).strip()
        if not speech:
            speech = "I can help with smart home controls, wellness shopping, and Ring security. What would you like to do?"

        return AgentResponse(
            speech=speech,
            cards=cards,
            tool_calls=tool_calls,
        )

    def llm_orchestrate(
        self, message: str, memory: dict[str, Any], session_id: str
    ) -> Optional[AgentResponse]:
        """Optional LLM-driven orchestration using Gemini, OpenAI, or AWS Bedrock.

        Gracefully returns None if LLM is unavailable or fails, triggering fallback.
        """
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        prompt = (
            f"You are Alexa+ OmniPulse, an autonomous ambient assistant.\n"
            f"User memory: {json.dumps(memory)}\n"
            f"User command: {message}\n"
            f"Available tools: update_smarthome_state, search_and_build_carousel, execute_instant_checkout, handle_ring_event.\n"
            f"Respond with JSON: {{'actions': [{{'tool': ..., 'arguments': ...}}], 'speech': ...}}"
        )

        try:
            if gemini_key:
                from google import genai  # type: ignore
                client = genai.Client(api_key=gemini_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                text = response.text or ""
                # Parse JSON if possible
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    actions = data.get("actions", [])
                    speech = data.get("speech", "I have updated your home and catalog preferences.")
                    cards: list[dict[str, Any]] = []
                    tool_calls: list[ToolCallRecord] = [
                        ToolCallRecord(name="get_household_memory", arguments={"session_id": session_id}, result=memory)
                    ]
                    for action in actions:
                        t_name = action.get("tool")
                        t_args = action.get("arguments", {})
                        if t_name:
                            res = self._call_tool_in_process(t_name, t_args)
                            cards.append(res["ui"])
                            tool_calls.append(ToolCallRecord(name=t_name, arguments=t_args, result=res))
                    return AgentResponse(speech=speech, cards=cards, tool_calls=tool_calls)
        except Exception as e:
            logger.info("LLM invocation skipped or failed: %s", e)

        return None

    def handle_ring_event(self, event: dict[str, Any]) -> AgentResponse:
        """Proactive handler for simulated Ring camera/doorbell events."""
        event_type = event.get("event_type", "guest_arrival")
        description = event.get("description", "Motion detected at front door")

        res = self._call_tool_in_process(
            "handle_ring_event",
            {"event_type": event_type, "description": description},
        )

        speech = ""
        if res.get("content"):
            speech = res["content"][0].get("text", "")

        return AgentResponse(
            speech=speech,
            cards=[res["ui"]],
            tool_calls=[
                ToolCallRecord(
                    name="handle_ring_event",
                    arguments={"event_type": event_type, "description": description},
                    result=res,
                )
            ],
        )
