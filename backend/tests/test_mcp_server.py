"""Unit tests for MCPServer in backend/mcp_server.py."""

from mcp_server import MCPServer, ToolRegistry, MCPTool


class MockEchoTool(MCPTool):
    name = "mock_echo"
    description = "Mock echo tool for test"
    input_schema = {"type": "object", "properties": {"val": {"type": "string"}}}

    def execute(self, arguments, db):
        return {
            "content": [{"type": "text", "text": arguments.get("val", "")}],
            "ui": {"type": "mock_card", "val": arguments.get("val", "")},
        }


def test_initialize_returns_protocol_version():
    server = MCPServer()
    req = {"jsonrpc": "2.0", "id": 101, "method": "initialize"}
    resp = server.route(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 101
    assert resp["result"]["protocolVersion"] == "2025-11-25"
    assert "capabilities" in resp["result"]
    assert "serverInfo" in resp["result"]


def test_tools_list_returns_6_tools():
    server = MCPServer()
    req = {"jsonrpc": "2.0", "id": 102, "method": "tools/list"}
    resp = server.route(req)
    assert resp["id"] == 102
    tools = resp["result"]["tools"]
    assert len(tools) == 6
    names = {t["name"] for t in tools}
    assert "get_household_memory" in names
    assert "search_and_build_carousel" in names
    assert "execute_instant_checkout" in names
    assert "update_smarthome_state" in names
    assert "handle_ring_event" in names
    assert "save_household_memory" in names


def test_tools_call_execution():
    registry = ToolRegistry()
    registry.register(MockEchoTool())
    server = MCPServer(tool_registry=registry)
    req = {
        "jsonrpc": "2.0",
        "id": 103,
        "method": "tools/call",
        "params": {"name": "mock_echo", "arguments": {"val": "hello"}},
    }
    resp = server.route(req)
    assert resp["id"] == 103
    assert resp["result"]["content"][0]["text"] == "hello"
    assert resp["result"]["ui"]["type"] == "mock_card"


def test_error_handling():
    server = MCPServer()
    # Null request
    assert server.route(None)["error"]["code"] == -32700

    # Bad JSON-RPC version
    assert server.route({"jsonrpc": "1.0", "id": 1, "method": "initialize"})["error"]["code"] == -32600

    # Unknown method
    assert server.route({"jsonrpc": "2.0", "id": 2, "method": "unknown/method"})["error"]["code"] == -32601

    # Unknown tool
    assert (
        server.route({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "non_existent"}})[
            "error"
        ]["code"]
        == -32602
    )
