"""
Regression tests for MCP tool schema inventory and routing.
Ensures TOOLS_LIST stays consistent after Tasks 45-47 schema fixes.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from main import TOOLS_LIST


def test_tool_inventory():
    tools = {t["name"]: t for t in TOOLS_LIST}

    assert len(TOOLS_LIST) == 30, f"Expected 30 tools, got {len(TOOLS_LIST)}"
    assert len(tools) == len(TOOLS_LIST), "Duplicate tool names found"

    for t in TOOLS_LIST:
        assert "name" in t, f"Tool missing name: {t}"
        assert "description" in t, f"Tool '{t['name']}' missing description"
        assert "inputSchema" in t, f"Tool '{t['name']}' missing inputSchema"
        schema = t["inputSchema"]
        assert schema.get("type") == "object", (
            f"Tool '{t['name']}' inputSchema.type != 'object'"
        )
        assert "properties" in schema, (
            f"Tool '{t['name']}' inputSchema missing properties"
        )


def test_route_coverage():
    main_path = Path(__file__).parent.parent / "backend" / "main.py"
    source = main_path.read_text()
    lines = source.splitlines()

    # Locate handle_mcp_tool function body only
    start = None
    for i, line in enumerate(lines):
        if line.startswith("async def handle_mcp_tool"):
            start = i
            break
    assert start is not None, "handle_mcp_tool function not found in main.py"

    body_lines = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped.startswith("async def ") or stripped.startswith("def "):
            break
        if stripped.startswith("# ==="):
            break
        body_lines.append(line)

    body = "\n".join(body_lines)
    route_names = set(re.findall(r'(?:if|elif) name == "([^"]+)"', body))

    tool_names = {t["name"] for t in TOOLS_LIST}

    missing_routes = tool_names - route_names
    assert not missing_routes, (
        f"TOOLS_LIST entries without routes: {missing_routes}"
    )

    extra_routes = route_names - tool_names
    assert not extra_routes, (
        f"Route branches without TOOLS_LIST entries: {extra_routes}"
    )


def _combined_text(tool):
    texts = [tool.get("description", "")]
    props = tool.get("inputSchema", {}).get("properties", {}).values()
    for p in props:
        if isinstance(p, dict) and "description" in p:
            texts.append(p["description"])
    return " ".join(texts)


def test_priority_schema_terms():
    tools = {t["name"]: t for t in TOOLS_LIST}

    # write_html
    text = _combined_text(tools["write_html"])
    assert "created" in text
    assert "count" in text
    assert "deleted" in text
    assert "replace" in text
    assert "multi-artboard" in text
    assert "pageId or targetNodeId" in text

    # update_styles
    text = _combined_text(tools["update_styles"])
    assert "deep-merge" in text or "Deep-merges" in text
    assert "removeStyleKeys" in text
    assert "updated" in text

    # set_text_content
    text = _combined_text(tools["set_text_content"])
    assert "Missing" in text
    assert "updated" in text
    assert "empty string" in text

    # update_svg_attributes
    text = _combined_text(tools["update_svg_attributes"])
    assert "SVG" in text
    assert "non-empty" in text
    assert 'style["id"]' in text

    # get_node_info
    text = _combined_text(tools["get_node_info"])
    assert "current page" in text
    assert "For pages" in text
    assert "For elements" in text

    # get_html
    text = _combined_text(tools["get_html"])
    assert "kind" in text
    assert "pageId" in text
    assert "nodeId" in text
    assert "pretty" not in tools["get_html"]["inputSchema"]["properties"]

    # get_overflow_report
    text = _combined_text(tools["get_overflow_report"])
    assert "includeArtboard" in text
    assert "minOverflow" in text
    assert "overflowCount" in text

    # move_nodes
    text = _combined_text(tools["move_nodes"])
    assert "Cycle protection" in text
    assert "movedCount" in text
    assert "oldParentId" in text

    # duplicate_nodes
    text = _combined_text(tools["duplicate_nodes"])
    assert "descendantIdMap" in text
    assert "duplicatedCount" in text
    assert "positional style only" in text

    # delete_nodes
    text = _combined_text(tools["delete_nodes"])
    assert "deletedByRoot" in text
    assert "Pages are never deleted" in text
    assert "errors" in text

    # rename_nodes
    text = _combined_text(tools["rename_nodes"])
    assert "oldName" in text
    assert "newName" in text
    assert "pageId" in text


def test_required_fields():
    tools = {t["name"]: t for t in TOOLS_LIST}

    assert tools["write_html"]["inputSchema"].get("required") == ["html"]
    assert tools["update_styles"]["inputSchema"].get("required") == [
        "nodeIds", "styles"
    ]
    assert tools["set_text_content"]["inputSchema"].get("required") == [
        "nodeIds", "text"
    ]
    assert tools["update_svg_attributes"]["inputSchema"].get("required") == [
        "nodeId", "attrs"
    ]
    assert tools["move_nodes"]["inputSchema"].get("required") == ["nodeIds"]
    assert tools["duplicate_nodes"]["inputSchema"].get("required") == ["nodeIds"]
    assert tools["delete_nodes"]["inputSchema"].get("required") == ["nodeIds"]
    assert tools["rename_nodes"]["inputSchema"].get("required") == [
        "nodeIds", "names"
    ]


if __name__ == "__main__":
    test_tool_inventory()
    test_route_coverage()
    test_priority_schema_terms()
    test_required_fields()
    print("All MCP tool schema regression checks passed.")
