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
    allow_origin_regex=r".*",  # allow all origins (including localhost:5173)
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
    elif name == "delete_artboard":
        return _delete_artboard(doc_id, arguments)
    elif name == "delete_nodes":
        return await _delete_nodes(doc_id, arguments)
    elif name == "update_artboard":
        return await _update_artboard(doc_id, arguments)
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
            "x": p.x,
            "y": p.y,
            "width": p.width,
            "height": p.height,
            "backgroundColor": p.backgroundColor,
            "childCount": len(p.elements),
        })

    return {
        "fileName": (doc.title or "Untitled") + ".html",
        "pageName": doc.pages[doc.current_page].name if doc.pages else "No artboard",
        "pageId": doc.pages[doc.current_page].id if doc.pages else "",
        "rootNodeId": doc.pages[doc.current_page].id if doc.pages else "",
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
    page_id = args.get("pageId", "") or None
    elements = _parse_html_elements(html)
    if not doc_id:
        doc_id = "default"
    created = []
    for el in elements:
        result = doc_store.create_element(doc_id, el, page_id=page_id)
        if result.get("success"):
            created.append(result["element"])
        elif result.get("error"):
            return {"success": False, "error": result["error"]}
    # Return full document so frontend can sync its Zustand store
    doc_response = doc_store.get_document(doc_id)
    return {
        "success": True,
        "created": created,
        "count": len(created),
        "document": doc_response,
    }


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

    # Separate artboard-level props (x/y/backgroundColor/width/height) from CSS styles
    artboard_keys = {"x", "y", "backgroundColor", "width", "height", "name"}
    artboard_updates = {k: v for k, v in styles.items() if k in artboard_keys}
    css_styles = {k: v for k, v in styles.items() if k not in artboard_keys}

    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    if not doc:
        return {"error": "Document not found"}

    updated = []
    for node_id in node_ids:
        # Check if this is an artboard (page) ID
        is_artboard = any(p.id == node_id for p in doc.pages)
        if is_artboard and artboard_updates:
            result = doc_store.update_page(doc_id, node_id, artboard_updates)
            if result.get("success"):
                updated.append({"id": node_id, "type": "artboard", "updates": artboard_updates})

        # Also apply CSS styles to elements (elements inside the artboard)
        if css_styles:
            result = doc_store.update_element(doc_id, node_id, {"style": css_styles})
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
    x = args.get("x", 0)
    y = args.get("y", 0)
    if not doc_id:
        doc_id = "default"
    doc = doc_store.documents.get(doc_id)
    if doc:
        page = Page(id=f"page-{len(doc.pages) + 1}", name=name, width=width, height=height, x=x, y=y)
        doc.pages.append(page)
        doc.current_page = len(doc.pages) - 1  # auto-switch to new page
        doc_store._save(doc_id)
        return {"success": True, "page": {"id": page.id, "name": page.name, "x": page.x, "y": page.y, "width": page.width, "height": page.height, "current_page": doc.current_page}}
    return {"error": "Document not found"}


def _delete_artboard(doc_id: str, args: dict) -> dict:
    page_id = args.get("pageId", "")
    if not doc_id:
        doc_id = "default"
    return doc_store.delete_page(doc_id, page_id)


async def _delete_nodes(doc_id: str, args: dict) -> dict:
    """Delete elements by their IDs"""
    node_ids = args.get("nodeIds", [])
    if not doc_id:
        doc_id = "default"
    deleted = []
    for node_id in node_ids:
        result = doc_store.delete_element(doc_id, node_id)
        if result.get("success"):
            deleted.append(node_id)
    return {"success": True, "deleted": deleted}


async def _update_artboard(doc_id: str, args: dict) -> dict:
    """Update artboard/page properties (x, y, width, height, name, backgroundColor)"""
    page_id = args.get("pageId", "")
    if not page_id:
        return {"error": "pageId is required"}
    if not doc_id:
        doc_id = "default"
    updates = {}
    for key in ("x", "y", "width", "height", "name", "backgroundColor"):
        if key in args:
            updates[key] = args[key]
    if not updates:
        return {"error": "No valid update fields provided"}
    return doc_store.update_page(doc_id, page_id, updates)


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
            k = k.strip()
            v = v.strip()
            # Convert kebab-case to camelCase
            parts = k.split("-")
            camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
            style[camel] = v
    return style


def _infer_type(tag: str, style: dict, text: str) -> str:
    """Infer element type from tag and style"""
    if text:
        return "text"
    if style.get("fontSize"):
        return "text"
    bg = style.get("backgroundColor") or style.get("background") or ""
    if bg not in ("transparent", "none", ""):
        return "rectangle"
    w = float(style.get("width", "0").rstrip("px") or 0)
    h = float(style.get("height", "0").rstrip("px") or 0)
    if "frame" in tag.lower() or (w > 200 and h > 100):
        return "frame"
    return "rectangle"


def _parse_html_elements(html: str) -> list[dict]:
    """Parse HTML string and extract elements (including nested)"""
    from bs4 import BeautifulSoup
    import uuid

    soup = BeautifulSoup(html, "html.parser")
    elements = []

    def walk(soup_element, parent_id=None):
        # Use .contents instead of .children — contents is always a fresh list
        # (children returns a list_iterator that can be consumed by get_text or other ops)
        for tag in soup_element.contents:
            if not hasattr(tag, 'name') or tag.name is None:
                continue
            tag_name = tag.name
            if tag_name in ("script", "style", "meta", "link", "head", "body", "html", "svg", "path", "rect", "circle", "line", "polyline", "polygon"):
                continue

            attrs = dict(tag.attrs)
            style = _parse_style(attrs.get("style", ""))

            # Collect Tag children (non-DirectString) once
            tag_children = [c for c in tag.contents if hasattr(c, 'name') and c.name is not None and c.name not in ("script", "style")]

            # text = only if NO Tag children (leaf node)
            # Avoid get_text() — it traverses all descendants and can corrupt the tree
            text = ""
            if not tag_children:
                text = "".join(t for t in tag.contents if isinstance(t, str)) or ""
                text = text.strip()

            el_id = f"n-{str(uuid.uuid4())[:8]}"
            if "id" in attrs and attrs["id"]:
                el_id = attrs["id"]

            el_type = _infer_type(tag_name, style, text)

            el = {
                "id": el_id,
                "name": f"{tag_name.capitalize()} Element",
                "tag": tag_name,
                "type": el_type,
                "style": style,
                "text": text if text else None,
                "children": [],
            }
            if parent_id:
                el["parentId"] = parent_id

            elements.append(el)

            for child in tag_children:
                walk(child, parent_id=el_id)

    walk(soup)
    return elements


# =============================================================================
# MCP Protocol Endpoints - unified handler supporting both formats
# - JSON-RPC 2.0: {jsonrpc, method, params} (for stdio bridge)
# - HTTP type: {name, arguments} (for Claude Code "type: http" config)
# =============================================================================

TOOLS_LIST = [
    {"name": "get_basic_info", "description": "Get basic document info", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_selection", "description": "Get selected nodes", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_tree_summary", "description": "Get tree summary", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string"}}}},
    {"name": "get_children", "description": "Get children of a node", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string"}}}},
    {"name": "get_node_info", "description": "Get node info", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string"}}}},
    {"name": "get_screenshot", "description": "Capture screenshot", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string"}}}},
    {"name": "write_html", "description": "Write HTML to create elements on a specific page", "inputSchema": {"type": "object", "properties": {"html": {"type": "string", "description": "HTML string with inline styles. Each root element becomes a separate canvas element. Use position:absolute and specify left/top/width/height."}, "pageId": {"type": "string", "description": "Target page ID. If omitted, creates on the current page. Use create_artboard first to get a pageId."}}, "required": ["html"]}},
    {"name": "duplicate_nodes", "description": "Duplicate nodes", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}}, "required": ["nodeIds"]}},
    {"name": "update_styles", "description": "Update styles", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}, "styles": {"type": "object"}}, "required": ["nodeIds", "styles"]}},
    {"name": "set_text_content", "description": "Set text content", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}, "text": {"type": "string"}}, "required": ["nodeIds", "text"]}},
    {"name": "rename_nodes", "description": "Rename nodes", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}, "names": {"type": "object"}}, "required": ["nodeIds", "names"]}},
    {"name": "finish_working_on_nodes", "description": "Mark work finished", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_computed_styles", "description": "Get computed styles", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}}}},
    {"name": "get_jsx", "description": "Export as JSX", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}}}},
    {"name": "get_font_family_info", "description": "Get font info", "inputSchema": {"type": "object", "properties": {"fontFamily": {"type": "string"}}}},
    {"name": "save_document", "description": "Save document", "inputSchema": {"type": "object", "properties": {"filePath": {"type": "string"}}}},
    {"name": "open_document", "description": "Open document", "inputSchema": {"type": "object", "properties": {"filePath": {"type": "string"}}, "required": ["filePath"]}},
    {"name": "export_html", "description": "Export as HTML", "inputSchema": {"type": "object", "properties": {"pretty": {"type": "boolean"}}}},
    {"name": "create_artboard", "description": "Create a new artboard/page", "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "description": "Artboard name (e.g. 'Header', 'Hero Section', 'Mobile Home')"}, "width": {"type": "number", "description": "Width in pixels (e.g. 1440 for desktop, 375 for mobile)"}, "height": {"type": "number", "description": "Height in pixels (e.g. 900 for desktop hero, 812 for mobile)"}, "x": {"type": "number", "description": "X position on canvas (px)"}, "y": {"type": "number", "description": "Y position on canvas (px)"}}}},
    {"name": "delete_artboard", "description": "Delete an artboard/page", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Page ID to delete"}}, "required": ["pageId"]}},
    {"name": "delete_nodes", "description": "Delete elements by their IDs", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}, "description": "Array of element IDs to delete"}}, "required": ["nodeIds"]}},
    {"name": "update_artboard", "description": "Update artboard/page properties (position, size, name, background color)", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Page ID to update"}, "x": {"type": "number", "description": "X position on canvas (px)"}, "y": {"type": "number", "description": "Y position on canvas (px)"}, "width": {"type": "number", "description": "Width in pixels"}, "height": {"type": "number", "description": "Height in pixels"}, "name": {"type": "string", "description": "Artboard name"}, "backgroundColor": {"type": "string", "description": "Background color (hex, e.g. #ffffff)"}}, "required": ["pageId"]}},
]


@app.get("/mcp")
async def mcp_get():
    """HTTP MCP: tool discovery"""
    return {"tools": TOOLS_LIST}


@app.post("/mcp")
async def mcp_post(request: Request):
    """Handle MCP - detects format from request body"""
    try:
        data = await request.json()
    except:
        return JSONResponse({"error": "invalid_request"}, status_code=400)

    doc_id = request.headers.get("x-paper-doc-id", "default")

    # HTTP type: {name, arguments}
    if "name" in data and "jsonrpc" not in data:
        tool_name = data.get("name", "")
        tool_args = data.get("arguments", {})
        try:
            result = await handle_mcp_tool(tool_name, tool_args, doc_id)
            return result
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=200)

    # JSON-RPC 2.0: {jsonrpc, method, params}
    method = data.get("method", "")
    params = data.get("params", {})
    msg_id = data.get("id")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": """Paper Clone - A local-first design tool that exports real HTML/CSS.

WORKFLOW:
1. First call get_basic_info to see existing artboards
2. Create artboards for each section you need with appropriate sizes
3. Use write_html with pageId to add elements to each artboard

Example artboard sizes:
  - Desktop web: width=1440, height=900 (or your target width)
  - Mobile: width=375, height=812
  - Tablet: width=768, height=1024
  - Header: width=1440, height=80
  - Hero: width=1440, height=600

Tool order:
  create_artboard({name:"Hero Section", width:1440, height:600}) → returns pageId
  write_html({pageId: pageId, html: "..."})
  create_artboard({name:"Features", width:1440, height:400})
  write_html({pageId: newPageId, html: "..."})
  delete_artboard({pageId: "page-1"}) → removes unwanted artboards

Each artboard is independent. Design web pages by creating one artboard per section.""",
            }
        elif method == "tools/list":
            result = {"tools": TOOLS_LIST}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = await handle_mcp_tool(tool_name, tool_args, doc_id)
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]}
            })
        else:
            return JSONResponse(content={"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}})

        return JSONResponse(content={"jsonrpc": "2.0", "id": msg_id, "result": result})
    except Exception as e:
        return JSONResponse(content={"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}}, status_code=200)


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


@app.delete("/api/documents/{doc_id}/pages/{page_id}")
async def api_delete_page(doc_id: str, page_id: str):
    return doc_store.delete_page(doc_id, page_id)


@app.put("/api/documents/{doc_id}/pages/{page_id}")
async def api_update_page(doc_id: str, page_id: str, updates: dict):
    try:
        result = doc_store.update_page(doc_id, page_id, updates)
        print(f"[update_page] doc={doc_id} page={page_id} updates={updates} → {result}")
        return result
    except Exception as e:
        print(f"[update_page] ERROR doc={doc_id} page={page_id}: {e}")
        return {"error": str(e)}


@app.post("/api/documents/{doc_id}/elements")
async def api_create_element(doc_id: str, element: dict):
    try:
        result = doc_store.create_element(doc_id, element)
        print(f"[create_element] doc={doc_id} element_id={element.get('id')} → {result}")
        return result
    except Exception as e:
        print(f"[create_element] ERROR doc={doc_id}: {e}")
        return {"error": str(e)}


@app.put("/api/documents/{doc_id}/elements/{element_id}")
async def api_update_element(doc_id: str, element_id: str, updates: dict):
    try:
        result = doc_store.update_element(doc_id, element_id, updates)
        print(f"[update_element] doc={doc_id} element={element_id} updates={updates} → {result}")
        return result
    except Exception as e:
        print(f"[update_element] ERROR doc={doc_id} element={element_id}: {e}")
        return {"error": str(e)}


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
