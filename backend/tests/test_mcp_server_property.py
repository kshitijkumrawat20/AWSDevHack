"""Property-based tests for MCPServer (Property 1: Protocol Version, Property 3: Tool Count)."""

try:
    from prop_compat import given, st
except ImportError:
    from tests.prop_compat import given, st
from mcp_server import MCPServer


@given(st.one_of(st.integers(), st.text(min_size=1, max_size=50)))
def test_property_1_protocol_version(req_id):
    server = MCPServer()
    req = {"jsonrpc": "2.0", "id": req_id, "method": "initialize"}
    resp = server.route(req)
    assert resp["result"]["protocolVersion"] == "2025-11-25"
    assert resp["id"] == req_id


@given(st.one_of(st.integers(), st.text(min_size=1, max_size=50)))
def test_property_3_tool_count(req_id):
    server = MCPServer()
    req = {"jsonrpc": "2.0", "id": req_id, "method": "tools/list"}
    resp = server.route(req)
    assert len(resp["result"]["tools"]) == 6
