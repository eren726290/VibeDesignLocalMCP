"""
Paper Clone Backend - FastAPI + MCP Server
Combines document API and MCP protocol in a single FastAPI application.
"""
import uvicorn
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Document Store
from document import DocumentStore, Page, Document

# MCP Server configuration
SERVER_NAME = "paper-clone"
SERVER_VERSION = "0.1.0"

# Global document store
doc_store = DocumentStore()

# FastAPI app
app = FastAPI(title="Paper Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Helper: MCP Tool Handlers
# =============================================================================

async def handle_mcp_tool(name: str, arguments: dict, doc_id: str) -> dict:
    """Route MCP tool calls to appropriate handlers"""

    if name == "get_basic_info":
        return await _get_basic_info(doc_id)
    elif name == "get_selection":
        return await _get_selection(doc_id)
    elif name == "get_tree_summary":
        return await _get_tree_summary(doc_id, arguments)
    elif name == "get_children":
        return await _get_children(doc_id, arguments)
    elif name == "get_node_info":
        return await _get_node_info(doc_id, arguments)
    elif name == "get_screenshot":
        return await _get_screenshot(doc_id, arguments)
    elif name == "write_html":
        return await _write_html(doc_id, arguments)
    elif name == "duplicate_nodes":
        return await _duplicate_nodes(doc_id, arguments)
    elif name == "update_styles":
        return await _update_styles(doc_id, arguments)
    elif name == "set_text_content":
        return await _set_text_content(doc_id, arguments)
    elif name == "rename_nodes":
        return await _rename_nodes(doc_id, arguments)
    elif name == "finish_working_on_nodes":
        return {"success": True, "finished": True}
    elif name == "get_computed_styles":
        return await _get_computed_styles(doc_id, arguments)
    elif name == "get_jsx":
        return await _get_jsx(doc_id, arguments)
    elif name == "get_font_family_info":
        return {"family": arguments.get("fontFamily", ""), "available": True, "weights": ["normal", "bold"]}
    elif name == "create_artboard":
        return await _create_artboard(doc_id, arguments)
    elif name == "save_document":
        return await _save_document(doc_id, arguments)
    elif name == "open_document":
        return await _open_document(doc_id, arguments)
    elif name == "export_html":
        return await _export_html(doc_id, arguments)
    else:
        return {"error": f"Unknown tool: {name}"}


async def _get_basic_info(doc_id: str) -> dict:
    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    if not doc:
        doc_store.new_document()
        doc = doc_store.documents.get("default")

    pages = []
    for p in doc.pages:
        pages.append({
            "id": p.id,
            "name": p.name,
            "width": p.width,
            "height": p.height,
            "childCount": len(p.elements),
        })

    return {
        "fileName": (doc.title or "Untitled") + ".html",
        "pageName": doc.pages[doc.current_page].name if doc.pages else "Page 1",
        "pageId": doc.pages[doc.current_page].id if doc.pages else "page-1",
        "rootNodeId": doc.pages[doc.current_page].id if doc.pages else "page-1",
        "nodeCount": sum(len(p.elements) for p in doc.pages),
        "artboardCount": len(doc.pages),
        "artboards": pages,
        "fontFamilies": ["system-ui", "sans-serif", "serif", "monospace"],
    }


async def _get_selection(doc_id: str) -> dict:
    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    if not doc:
        return {"nodes": []}
    page = doc.pages[doc.current_page]
    if page.elements:
        return {
            "nodes": [{
                "id": page.elements[0].get("id", ""),
                "name": page.elements[0].get("name", "Element"),
                "type": page.elements[0].get("tag", "div"),
            }]
        }
    return {"nodes": []}


async def _get_tree_summary(doc_id: str, args: dict) -> dict:
    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    if not doc:
        return {"summary": "Empty document"}
    page = doc.pages[doc.current_page]
    lines = [f"Page: {page.name} ({page.width}x{page.height})"]
    for el in page.elements:
        lines.append(f"  [{el.get('tag', 'div')}] {el.get('name', 'Element')} ({el.get('id', '?')})")
    return {"summary": "\n".join(lines)}


async def _get_children(doc_id: str, args: dict) -> dict:
    node_id = args.get("nodeId", "")
    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    if not doc:
        return {"children": []}
    page = doc.pages[doc.current_page]
    if not node_id or node_id == page.id:
        return {
            "children": [
                {"id": el.get("id", ""), "name": el.get("name", "Element"), "type": el.get("tag", "div"), "childCount": 0}
                for el in page.elements
            ]
        }
    return {"children": []}


async def _get_node_info(doc_id: str, args: dict) -> dict:
    node_id = args.get("nodeId", "")
    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    if not doc:
        return {"error": "Not found"}
    page = doc.pages[doc.current_page]
    for el in page.elements:
        if el.get("id") == node_id:
            return {"id": el.get("id", ""), "name": el.get("name", "Element"), "tag": el.get("tag", "div"), "style": el.get("style", {}), "text": el.get("text", "")}
    return {"error": "Node not found"}


async def _get_screenshot(doc_id: str, args: dict) -> dict:
    data = doc_store.get_screenshot_data(doc_id)
    return {"data": data.get("data", ""), "nodeId": args.get("nodeId", ""), "scale": args.get("scale", 1), "transparent": args.get("transparent", False)}


async def _write_html(doc_id: str, args: dict) -> dict:
    html = args.get("html", "")
    elements = _parse_html_elements(html)
    if not doc_id:
        doc_id = "default"
    created = []
    for el in elements:
        result = doc_store.create_element(doc_id, el)
        if result.get("success"):
            created.append(result["element"])
    return {"success": True, "created": created, "count": len(created)}


async def _duplicate_nodes(doc_id: str, args: dict) -> dict:
    node_ids = args.get("nodeIds", [])
    if not doc_id:
        doc_id = "default"
    results = []
    for node_id in node_ids:
        result = doc_store.duplicate_element(doc_id, node_id)
        if result.get("success"):
            results.append(result["element"])
    return {"success": True, "duplicated": results}


async def _update_styles(doc_id: str, args: dict) -> dict:
    node_ids = args.get("nodeIds", [])
    styles = args.get("styles", {})
    if not doc_id:
        doc_id = "default"
    updated = []
    for node_id in node_ids:
        result = doc_store.update_element(doc_id, node_id, {"style": styles})
        if result.get("success"):
            updated.append(result["element"])
    return {"success": True, "updated": updated}


async def _set_text_content(doc_id: str, args: dict) -> dict:
    node_ids = args.get("nodeIds", [])
    content = args.get("text", "")
    if not doc_id:
        doc_id = "default"
    updated = []
    for node_id in node_ids:
        result = doc_store.update_element(doc_id, node_id, {"text": content})
        if result.get("success"):
            updated.append(result["element"])
    return {"success": True, "updated": updated}


async def _rename_nodes(doc_id: str, args: dict) -> dict:
    node_ids = args.get("nodeIds", [])
    names = args.get("names", {})
    if not doc_id:
        doc_id = "default"
    updated = []
    for node_id in node_ids:
        name = names.get(node_id, "Element")
        result = doc_store.update_element(doc_id, node_id, {"name": name})
        if result.get("success"):
            updated.append(result["element"])
    return {"success": True, "updated": updated}


async def _get_computed_styles(doc_id: str, args: dict) -> dict:
    node_ids = args.get("nodeIds", [])
    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    if not doc:
        return {"styles": {}}
    page = doc.pages[doc.current_page]
    styles = {}
    for node_id in node_ids:
        for el in page.elements:
            if el.get("id") == node_id:
                styles[node_id] = el.get("style", {})
                break
    return {"styles": styles}


async def _get_jsx(doc_id: str, args: dict) -> dict:
    node_ids = args.get("nodeIds", [])
    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    if not doc:
        return {"jsx": ""}
    page = doc.pages[doc.current_page]
    jsx_lines = ["function PaperCanvas() {", "  return ("]
    for el in page.elements:
        if not node_ids or el.get("id") in node_ids:
            tag = el.get("tag", "div")
            style = el.get("style", {})
            text = el.get("text", "")
            style_str = ", ".join(f'{k}="{v}"' for k, v in style.items())
            if text:
                jsx_lines.append(f'    <{tag} style={{{{ {style_str} }}}}>{text}</{tag}>')
            else:
                jsx_lines.append(f'    <{tag} style={{{{ {style_str} }}}} />')
    jsx_lines.extend(["  );", "}"])
    return {"jsx": "\n".join(jsx_lines)}


async def _create_artboard(doc_id: str, args: dict) -> dict:
    name = args.get("name", "New Page")
    width = args.get("width", 375)
    height = args.get("height", 812)
    if not doc_id:
        doc_id = "default"
    doc = doc_store.documents.get(doc_id)
    if doc:
        page = Page(id=f"page-{len(doc.pages) + 1}", name=name, width=width, height=height)
        doc.pages.append(page)
        return {"success": True, "page": {"id": page.id, "name": page.name, "width": page.width, "height": page.height}}
    return {"error": "Document not found"}


async def _save_document(doc_id: str, args: dict) -> dict:
    file_path = args.get("filePath", "")
    if not doc_id:
        doc_id = "default"
    return doc_store.save_document(doc_id, file_path if file_path else None)


async def _open_document(doc_id: str, args: dict) -> dict:
    file_path = args.get("filePath", "")
    if not file_path:
        return {"error": "filePath is required"}
    import uuid
    new_id = str(uuid.uuid4())[:8]
    return doc_store.open_document(new_id, file_path)


async def _export_html(doc_id: str, args: dict) -> dict:
    pretty = args.get("pretty", True)
    if not doc_id:
        doc_id = "default"
    return doc_store.export_html(doc_id, pretty)


def _kebab_to_camel(kebab: str) -> str:
    """Convert kebab-case CSS property to camelCase JS property name"""
    # Special mappings for CSS shorthand properties
    SPECIAL = {
        "background": "backgroundColor",
        "background-color": "backgroundColor",
        "font-size": "fontSize",
        "line-height": "lineHeight",
        "border-radius": "borderRadius",
        "border-width": "borderWidth",
        "border-color": "borderColor",
        "margin-left": "marginLeft",
        "margin-right": "marginRight",
        "margin-top": "marginTop",
        "margin-bottom": "marginBottom",
        "padding-left": "paddingLeft",
        "padding-right": "paddingRight",
        "padding-top": "paddingTop",
        "padding-bottom": "paddingBottom",
    }
    if kebab in SPECIAL:
        return SPECIAL[kebab]
    parts = kebab.split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _parse_style(raw: str) -> dict:
    """Parse CSS style string into camelCase dict"""
    style = {}
    for item in raw.split(";"):
        if ":" in item:
            k, v = item.split(":", 1)
            style[_kebab_to_camel(k.strip())] = v.strip()
    return style


def _parse_html_elements(html: str) -> list[dict]:
    """Parse HTML string and extract elements"""
    import re
    import uuid
    elements = []
    pattern = r'<(\w+)\s+([^>]*)>([^<]*)</\1>'
    for match in re.finditer(pattern, html, re.DOTALL):
        tag = match.group(1)
        attrs_str = match.group(2)
        text = match.group(3).strip()
        style = {}
        style_match = re.search(r'style="([^"]*)"', attrs_str)
        if style_match:
            style = _parse_style(style_match.group(1))
        el_id = f"n-{str(uuid.uuid4())[:8]}"
        id_match = re.search(r'id="([^"]*)"', attrs_str)
        if id_match:
            el_id = id_match.group(1)
        # Infer element type from style
        el_type = "rectangle"
        if text:
            el_type = "text"
        elif style.get("fontSize"):
            el_type = "text"
        elif style.get("backgroundColor") or style.get("background"):
            bg = style.get("backgroundColor") or style.get("background") or ""
            if bg != "transparent" and bg != "none":
                el_type = "rectangle"
        elif "frame" in tag.lower() or (parseFloat(style.get("width", "0")) > 200 and parseFloat(style.get("height", "0")) > 100):
            el_type = "frame"

        elements.append({"id": el_id, "name": f"{tag.capitalize()} Element", "tag": tag, "type": el_type, "style": style, "text": text or None, "children": []})
    return elements


# =============================================================================
# MCP Protocol Endpoints
# =============================================================================

@app.get("/mcp")
async def mcp_get():
    return JSONResponse(
        content={"error": "not_found", "message": "Use POST for MCP requests"},
        status_code=404,
    )


@app.post("/mcp")
async def mcp_post(request: Request):
    """Handle MCP requests"""
    try:
        data = await request.json()
    except:
        return JSONResponse(content={"error": "invalid_request"}, status_code=400)

    method = data.get("method", "")
    params = data.get("params", {})
    doc_id = request.headers.get("x-paper-doc-id", "default")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": """Paper Clone - A local-first design tool that exports real HTML/CSS.
Use tools to create, edit, and export web designs. Canvas renders real HTML elements with position: absolute and inline styles.""",
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {"name": "get_basic_info", "description": "Get basic document information", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "get_selection", "description": "Get currently selected nodes", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "get_tree_summary", "description": "Get tree summary", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string"}, "depth": {"type": "number"}}}},
                    {"name": "get_children", "description": "Get children of a node", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string"}}}},
                    {"name": "get_node_info", "description": "Get node info", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string"}}}},
                    {"name": "get_screenshot", "description": "Capture screenshot", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string"}, "scale": {"type": "number"}, "transparent": {"type": "boolean"}}}},
                    {"name": "write_html", "description": "Write HTML to create elements", "inputSchema": {"type": "object", "properties": {"html": {"type": "string"}, "parentId": {"type": "string"}}, "required": ["html"]}},
                    {"name": "duplicate_nodes", "description": "Duplicate nodes", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}}, "required": ["nodeIds"]}},
                    {"name": "update_styles", "description": "Update styles", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}, "styles": {"type": "object"}}, "required": ["nodeIds", "styles"]}},
                    {"name": "set_text_content", "description": "Set text content", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}, "text": {"type": "string"}}, "required": ["nodeIds", "text"]}},
                    {"name": "rename_nodes", "description": "Rename nodes", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}, "names": {"type": "object"}}, "required": ["nodeIds", "names"]}},
                    {"name": "finish_working_on_nodes", "description": "Mark work finished", "inputSchema": {"type": "object", "properties": {}}},
                    {"name": "get_computed_styles", "description": "Get computed styles", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}}, "required": ["nodeIds"]}},
                    {"name": "get_jsx", "description": "Export as JSX", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}}}},
                    {"name": "get_font_family_info", "description": "Get font info", "inputSchema": {"type": "object", "properties": {"fontFamily": {"type": "string"}}}},
                    {"name": "create_artboard", "description": "Create artboard", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "width": {"type": "number"}, "height": {"type": "number"}}}},
                    {"name": "save_document", "description": "Save document", "inputSchema": {"type": "object", "properties": {"filePath": {"type": "string"}}}},
                    {"name": "open_document", "description": "Open document", "inputSchema": {"type": "object", "properties": {"filePath": {"type": "string"}}, "required": ["filePath"]}},
                    {"name": "export_html", "description": "Export as HTML", "inputSchema": {"type": "object", "properties": {"pretty": {"type": "boolean"}}}},
                ]
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = await handle_mcp_tool(tool_name, tool_args, doc_id)
            if isinstance(result, dict) and "error" in result:
                return JSONResponse(content={"jsonrpc": "2.0", "id": data.get("id"), "result": {"content": [{"type": "text", "text": json.dumps(result)}], "isError": True}})
            return JSONResponse(content={"jsonrpc": "2.0", "id": data.get("id"), "result": {"content": [{"type": "text", "text": json.dumps(result)}]}})
        else:
            return JSONResponse(content={"jsonrpc": "2.0", "id": data.get("id"), "error": {"code": -32601, "message": f"Unknown method: {method}"}})

        return JSONResponse(content={"jsonrpc": "2.0", "id": data.get("id"), "result": result})
    except Exception as e:
        return JSONResponse(
            content={"jsonrpc": "2.0", "id": data.get("id"), "error": {"code": -32603, "message": str(e)}},
            status_code=200,
        )


# =============================================================================
# Document API (used by frontend)
# =============================================================================

@app.post("/api/documents/new")
async def api_new_document():
    return doc_store.new_document()


@app.get("/api/documents/{doc_id}")
async def api_get_document(doc_id: str):
    return doc_store.get_document(doc_id)


@app.post("/api/documents/{doc_id}/save")
async def api_save_document(doc_id: str):
    return doc_store.save_document(doc_id)


@app.post("/api/documents/{doc_id}/open")
async def api_open_document(doc_id: str, file_path: str):
    return doc_store.open_document(doc_id, file_path)


@app.patch("/api/documents/{doc_id}/current-page")
async def api_set_current_page(doc_id: str, body: dict):
    doc = doc_store.documents.get(doc_id)
    if not doc:
        return JSONResponse({"error": "Document not found"}, status_code=404)
    doc.current_page = body.get("current_page", 0)
    return {"success": True}


@app.post("/api/documents/{doc_id}/pages")
async def api_create_page(doc_id: str, page: dict):
    return doc_store.create_page(doc_id, page)


@app.post("/api/documents/{doc_id}/elements")
async def api_create_element(doc_id: str, element: dict):
    return doc_store.create_element(doc_id, element)


@app.put("/api/documents/{doc_id}/elements/{element_id}")
async def api_update_element(doc_id: str, element_id: str, updates: dict):
    return doc_store.update_element(doc_id, element_id, updates)


@app.delete("/api/documents/{doc_id}/elements/{element_id}")
async def api_delete_element(doc_id: str, element_id: str):
    return doc_store.delete_element(doc_id, element_id)


@app.post("/api/documents/{doc_id}/duplicate")
async def api_duplicate_element(doc_id: str, element_id: str):
    return doc_store.duplicate_element(doc_id, element_id)


@app.post("/api/documents/{doc_id}/export")
async def api_export_html(doc_id: str, pretty: bool = True):
    return doc_store.export_html(doc_id, pretty)


@app.post("/api/documents/{doc_id}/screenshot")
async def api_set_screenshot(doc_id: str, data: dict):
    doc_store.set_screenshot_data(doc_id, data.get("data", ""))
    return {"success": True}


@app.get("/health")
async def health():
    return {"status": "ok", "server": SERVER_NAME, "version": SERVER_VERSION}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3004)
