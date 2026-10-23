"""Smart home domain MCP tools for Alexa+ OmniPulse.

Implements the ``update_smarthome_state`` MCP tool, which updates a smart
home device (light, HVAC thermostat, or routine) and returns a Smart Home
Status Card for the Echo Show simulator's Rich Media Canvas.

Design references:
    - design.md §Component 3 (MCP Tools): unified tool contract
        ``{"content": [...], "ui": {...}}``
    - design.md §Data Model 3 (DeviceState): device_id, device_type, state, room
    - design.md §Data Model 3 validation rules:
        * device_type inferred from device name
        * lights:  state.brightness in [0, 100]; state.color in known palette
        * hvac:    state.temperature in [60, 90] Fahrenheit
        * routine: no domain-specific validation
    - design.md §Algorithm 2 (Steps 3 - Smart Home domain): warm lighting and
      comfort HVAC derived from household memory / message keywords

The module imports :class:`MCPTool` from ``mcp_server`` (the backend package
root is on ``sys.path`` at runtime and during tests) and is dependency-free
at import time: ``DatabaseManager`` is referenced only under
``TYPE_CHECKING`` so the tools can be imported without a live database.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp_server import MCPTool

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from database import DatabaseManager

__all__ = ["UpdateSmarthomeStateTool"]

# Known color palette for light devices (design.md §Data Model 3).
LIGHT_COLOR_PALETTE: frozenset[str] = frozenset(
    {"warm", "cool", "white", "daylight", "amber"}
)

# Valid brightness range for lights, expressed as a percentage.
LIGHT_BRIGHTNESS_MIN = 0
LIGHT_BRIGHTNESS_MAX = 100

# Valid Fahrenheit temperature range for HVAC thermostats.
HVAC_TEMP_MIN = 60
HVAC_TEMP_MAX = 90


class UpdateSmarthomeStateTool(MCPTool):
    """MCP tool: update a smart home device state and return a status card.

    Infers the device type from the device name, validates the requested
    state against the domain rules (brightness / color for lights,
    temperature for HVAC), persists the new state via
    :meth:`DatabaseManager.update_device_state`, and returns a Smart Home
    Status Card for the simulator.

    The returned payload follows the unified tool contract documented in
    design.md §Component 3::

        {"content": [{"type": "text", "text": ...}], "ui": {...}}
    """

    name: str = "update_smarthome_state"
    description: str = (
        "Update a smart home device state (light, HVAC thermostat, or "
        "routine) and return a smart home status card."
    )
    input_schema: dict[str, Any] = {
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
    }

    def execute(
        self,
        arguments: dict[str, Any],
        db: "DatabaseManager",
    ) -> dict[str, Any]:
        """Validate and persist a device state update.

        Preconditions:
            * ``arguments`` carries a non-empty ``device`` (str) and a
              ``state`` (dict) optionally containing ``on``, ``brightness``,
              ``color``, ``temperature``, and/or ``mode``.
            * ``db`` is an initialized :class:`DatabaseManager`.

        Postconditions:
            * On success the new state is persisted via
              ``db.update_device_state`` and the result carries a
              ``smarthome_card`` UI whose ``devices`` list contains the
              updated device dict (``device_id``, ``device_type``,
              ``state``, ``room``).
            * On validation failure no database write occurs; the result
              carries a single text ``content`` entry describing the error
              and an empty ``ui``.
        """
        device = arguments.get("device")
        state = arguments.get("state")

        # --- Argument presence / shape checks ----------------------------
        if not device or not isinstance(device, str):
            return self._error("Missing or invalid 'device' (expected a string).")
        if state is None or not isinstance(state, dict):
            return self._error("Missing or invalid 'state' (expected an object).")

        # --- Domain validation (design.md §Data Model 3) ------------------
        device_type = self._infer_device_type(device)
        validation_error = self._validate_state(device_type, state)
        if validation_error is not None:
            return self._error(validation_error)

        # --- Persist and build the response ------------------------------
        updated_device = db.update_device_state(device, state)
        description = self._describe_state(device_type, state)
        return {
            "content": [
                {"type": "text", "text": f"Updated {device}: {description}."},
            ],
            "ui": {
                "type": "smarthome_card",
                "title": "Smart Home Status",
                "devices": [updated_device],
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_device_type(device: str) -> str:
        """Infer ``device_type`` from the device name.

        Mirrors :meth:`DatabaseManager._infer_device_type` so the validation
        type matches the row that will be stored: anything not recognised as
        HVAC or a routine is treated as a light.
        """
        d = device.lower()
        if "thermostat" in d or "hvac" in d:
            return "hvac"
        if "routine" in d:
            return "routine"
        return "light"

    @staticmethod
    def _validate_state(device_type: str, state: dict[str, Any]) -> str | None:
        """Validate ``state`` for ``device_type``.

        Returns an error message string when validation fails, or ``None``
        when the state is acceptable. Only fields that are actually present
        in ``state`` are validated, per design.md §Data Model 3.
        """
        if device_type == "light":
            if "brightness" in state:
                brightness = state["brightness"]
                if isinstance(brightness, bool) or not isinstance(brightness, (int, float)):
                    return (
                        "Invalid brightness: expected a number in "
                        f"[{LIGHT_BRIGHTNESS_MIN}, {LIGHT_BRIGHTNESS_MAX}], "
                        f"got {brightness!r}."
                    )
                if not (LIGHT_BRIGHTNESS_MIN <= brightness <= LIGHT_BRIGHTNESS_MAX):
                    return (
                        f"Invalid brightness: {brightness} is out of range "
                        f"[{LIGHT_BRIGHTNESS_MIN}, {LIGHT_BRIGHTNESS_MAX}]."
                    )
            if "color" in state:
                color = state["color"]
                if not isinstance(color, str) or color.lower() not in LIGHT_COLOR_PALETTE:
                    return (
                        f"Invalid color: {color!r} is not in the known palette "
                        f"{sorted(LIGHT_COLOR_PALETTE)}."
                    )
        elif device_type == "hvac":
            if "temperature" in state:
                temperature = state["temperature"]
                if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
                    return (
                        "Invalid temperature: expected a number in "
                        f"[{HVAC_TEMP_MIN}, {HVAC_TEMP_MAX}] Fahrenheit, "
                        f"got {temperature!r}."
                    )
                if not (HVAC_TEMP_MIN <= temperature <= HVAC_TEMP_MAX):
                    return (
                        f"Invalid temperature: {temperature} is out of range "
                        f"[{HVAC_TEMP_MIN}, {HVAC_TEMP_MAX}] Fahrenheit."
                    )
        # routine -> no domain-specific validation
        return None

    @staticmethod
    def _describe_state(device_type: str, state: dict[str, Any]) -> str:
        """Build a human-readable summary of ``state`` for the speech text."""
        parts: list[str] = []
        if "on" in state:
            parts.append("on" if state["on"] else "off")
        if device_type == "light":
            if "brightness" in state:
                parts.append(f"brightness {state['brightness']}%")
            if "color" in state:
                parts.append(f"{state['color']} light")
        elif device_type == "hvac":
            if "temperature" in state:
                parts.append(f"{state['temperature']}°F")
            if "mode" in state:
                parts.append(f"{state['mode']} mode")
        # Fallback: surface any remaining state keys generically so the
        # summary is never empty for unusual states (e.g. custom routines).
        if not parts:
            for key, value in state.items():
                parts.append(f"{key} {value}")
        return ", ".join(parts)

    @staticmethod
    def _error(message: str) -> dict[str, Any]:
        """Build a validation-error tool result (no database write occurs)."""
        return {
            "content": [{"type": "text", "text": f"Validation error: {message}"}],
            "ui": {},
        }
