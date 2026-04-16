"""
MCP Handler - Bridge between MCP tools and document store
"""
import json
import base64
import uuid
from typing import Any, Optional

# Global doc store reference
_doc_store = None


def set_doc_store(store):
    global _doc_store
    _doc_store = store


def get_doc_store():
    return _doc_store


# =============================================================================
# MCP Tool Handlers
# =============================================================================

async def handle_tool_call(tool_name: str, args: dict, doc_id: str = "default") -> dict:
    """Route tool calls to appropriate handlers"""
    handlers = {
        "get_basic_info": get_basic_info,
        "get_selection": get_selection,
        "get_tree_summary": get_tree_summary,
        "get_children": get_children,
        "get_node_info": get_node_info,
        "get_screenshot": get_screenshot,
        "write_html": write_html,
        "duplicate_nodes": duplicate_nodes,
        "update_styles": update_styles,
        "set_text_content": set_text_content,
        "rename_nodes": rename_nodes,
        "finish_working_on_nodes": finish_working_on_nodes,
        "get_computed_styles": get_computed_styles,
        "get_jsx": get_jsx,
        "get_font_family_info": get_font_family_info,
        "create_artboard": create_artboard,
        "save_document": save_document,
        "open_document": open_document,
        "export_html": export_html,
    }

    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}

    return await handler(args, doc_id)


# =============================================================================
# Tool Implementations
# =============================================================================

async def get_basic_info(args: dict, doc_id: str) -> dict:
    """Get basic document info"""
    store = get_doc_store()
    if not store:
        store.new_document()

    doc = store.documents.get(doc_id)
    if not doc:
        doc = store.documents.get("default")
        if not doc:
            store.new_document()
            doc = store.documents.get("default")

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
        "fileName": doc.title + ".html",
        "pageName": doc.pages[doc.current_page].name if doc.pages else "Page 1",
        "pageId": doc.pages[doc.current_page].id if doc.pages else "page-1",
        "rootNodeId": doc.pages[doc.current_page].id if doc.pages else "page-1",
        "nodeCount": sum(len(p.elements) for p in doc.pages),
        "artboardCount": len(doc.pages),
        "artboards": pages,
        "fontFamilies": ["system-ui", "sans-serif", "serif", "monospace"],
    }


async def get_selection(args: dict, doc_id: str) -> dict:
    """Get currently selected nodes"""
    store = get_doc_store()
    if not store:
        return {"nodes": []}

    doc = store.documents.get(doc_id) or store.documents.get("default")
    if not doc:
        return {"nodes": []}

    # Return first element as selection for now
    page = doc.pages[doc.current_page]
    if page.elements:
        return {
            "nodes": [
                {
                    "id": page.elements[0].get("id", ""),
                    "name": page.elements[0].get("name", "Element"),
                    "type": page.elements[0].get("tag", "div"),
                }
            ]
        }
    return {"nodes": []}


async def get_tree_summary(args: dict, doc_id: str) -> dict:
    """Get tree summary of nodes"""
    store = get_doc_store()
    if not store:
        return {"summary": ""}

    doc = store.documents.get(doc_id) or store.documents.get("default")
    if not doc:
        return {"summary": "Empty document"}

    page = doc.pages[doc.current_page]

    lines = [f"Page: {page.name} ({page.width}x{page.height})"]
    for el in page.elements:
        el_id = el.get("id", "?")
        el_name = el.get("name", "Element")
        el_tag = el.get("tag", "div")
        lines.append(f"  [{el_tag}] {el_name} ({el_id})")

    return {"summary": "\n".join(lines)}


async def get_children(args: dict, doc_id: str) -> dict:
    """Get children of a node"""
    node_id = args.get("nodeId", "")
    store = get_doc_store()

    doc = store.documents.get(doc_id) or store.documents.get("default")
    if not doc:
        return {"children": []}

    # Return page elements as children
    page = doc.pages[doc.current_page]
    if not node_id or node_id == page.id:
        children = []
        for el in page.elements:
            children.append({
                "id": el.get("id", ""),
                "name": el.get("name", "Element"),
                "type": el.get("tag", "div"),
                "childCount": 0,
            })
        return {"children": children}

    return {"children": []}


async def get_node_info(args: dict, doc_id: str) -> dict:
    """Get detailed info about a node"""
    node_id = args.get("nodeId", "")
    store = get_doc_store()

    doc = store.documents.get(doc_id) or store.documents.get("default")
    if not doc:
        return {"error": "Not found"}

    page = doc.pages[doc.current_page]
    for el in page.elements:
        if el.get("id") == node_id:
            return {
                "id": el.get("id", ""),
                "name": el.get("name", "Element"),
                "tag": el.get("tag", "div"),
                "style": el.get("style", {}),
                "text": el.get("text", ""),
            }

    return {"error": "Node not found"}


async def get_screenshot(args: dict, doc_id: str) -> dict:
    """Get screenshot data"""
    node_id = args.get("nodeId", "")
    scale = args.get("scale", 1)
    transparent = args.get("transparent", False)

    store = get_doc_store()
    data = store.get_screenshot_data(doc_id)

    return {
        "data": data.get("data", ""),
        "nodeId": node_id,
        "scale": scale,
        "transparent": transparent,
    }


async def write_html(args: dict, doc_id: str) -> dict:
    """Write HTML to create elements"""
    html = args.get("html", "")
    parent_id = args.get("parentId", "")

    store = get_doc_store()
    if not store:
        return {"error": "Document store not initialized"}

    # Parse HTML and create elements
    elements = _parse_html_elements(html)

    if not doc_id:
        doc_id = "default"

    created = []
    for el in elements:
        result = store.create_element(doc_id, el)
        if result.get("success"):
            created.append(result["element"])

    return {
        "success": True,
        "created": created,
        "count": len(created),
    }


async def duplicate_nodes(args: dict, doc_id: str) -> dict:
    """Duplicate nodes"""
    node_ids = args.get("nodeIds", [])
    store = get_doc_store()

    if not doc_id:
        doc_id = "default"

    results = []
    for node_id in node_ids:
        result = store.duplicate_element(doc_id, node_id)
        if result.get("success"):
            results.append(result["element"])

    return {
        "success": True,
        "duplicated": results,
    }


async def update_styles(args: dict, doc_id: str) -> dict:
    """Update styles of nodes"""
    node_ids = args.get("nodeIds", [])
    styles = args.get("styles", {})
    store = get_doc_store()

    if not doc_id:
        doc_id = "default"

    updated = []
    for node_id in node_ids:
        result = store.update_element(doc_id, node_id, {"style": styles})
        if result.get("success"):
            updated.append(result["element"])

    return {
        "success": True,
        "updated": updated,
    }


async def set_text_content(args: dict, doc_id: str) -> dict:
    """Set text content of nodes"""
    node_ids = args.get("nodeIds", [])
    content = args.get("text", "")
    store = get_doc_store()

    if not doc_id:
        doc_id = "default"

    updated = []
    for node_id in node_ids:
        result = store.update_element(doc_id, node_id, {"text": content})
        if result.get("success"):
            updated.append(result["element"])

    return {
        "success": True,
        "updated": updated,
    }


async def rename_nodes(args: dict, doc_id: str) -> dict:
    """Rename nodes"""
    node_ids = args.get("nodeIds", [])
    names = args.get("names", {})
    store = get_doc_store()

    if not doc_id:
        doc_id = "default"

    updated = []
    for node_id in node_ids:
        name = names.get(node_id, "Element")
        result = store.update_element(doc_id, node_id, {"name": name})
        if result.get("success"):
            updated.append(result["element"])

    return {
        "success": True,
        "updated": updated,
    }


async def finish_working_on_nodes(args: dict, doc_id: str) -> dict:
    """Mark work as finished"""
    return {"success": True, "finished": True}


async def get_computed_styles(args: dict, doc_id: str) -> dict:
    """Get computed styles of nodes"""
    node_ids = args.get("nodeIds", [])
    store = get_doc_store()

    doc = store.documents.get(doc_id) or store.documents.get("default")
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


async def get_jsx(args: dict, doc_id: str) -> dict:
    """Export nodes as JSX"""
    node_ids = args.get("nodeIds", [])
    store = get_doc_store()

    doc = store.documents.get(doc_id) or store.documents.get("default")
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


async def get_font_family_info(args: dict, doc_id: str) -> dict:
    """Get font family info"""
    family = args.get("fontFamily", "")
    return {
        "family": family,
        "available": True,
        "weights": ["normal", "bold"],
    }


async def create_artboard(args: dict, doc_id: str) -> dict:
    """Create a new artboard/page"""
    name = args.get("name", "New Page")
    width = args.get("width", 375)
    height = args.get("height", 812)
    store = get_doc_store()

    if not doc_id:
        doc_id = "default"

    # Add new page to document
    doc = store.documents.get(doc_id)
    if doc:
        from document import Page
        page = Page(
            id=f"page-{len(doc.pages) + 1}",
            name=name,
            width=width,
            height=height,
        )
        doc.pages.append(page)
        return {
            "success": True,
            "page": {
                "id": page.id,
                "name": page.name,
                "width": page.width,
                "height": page.height,
            },
        }

    return {"error": "Document not found"}


async def save_document(args: dict, doc_id: str) -> dict:
    """Save document to file"""
    file_path = args.get("filePath", "")
    store = get_doc_store()

    if not doc_id:
        doc_id = "default"

    return store.save_document(doc_id, file_path if file_path else None)


async def open_document(args: dict, doc_id: str) -> dict:
    """Open document from file"""
    file_path = args.get("filePath", "")
    store = get_doc_store()

    if not file_path:
        return {"error": "filePath is required"}

    new_id = str(uuid.uuid4())[:8]
    return store.open_document(new_id, file_path)


async def export_html(args: dict, doc_id: str) -> dict:
    """Export document as HTML"""
    pretty = args.get("pretty", True)
    store = get_doc_store()

    if not doc_id:
        doc_id = "default"

    return store.export_html(doc_id, pretty)


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_html_elements(html: str) -> list[dict]:
    """Parse HTML string and extract elements"""
    import re
    elements = []

    # Match div, span, etc. with inline styles
    pattern = r'<(\w+)\s+([^>]*)>([^<]*)</\1>'
    for match in re.finditer(pattern, html, re.DOTALL):
        tag = match.group(1)
        attrs_str = match.group(2)
        text = match.group(3).strip()

        # Extract style
        style = {}
        style_match = re.search(r'style="([^"]*)"', attrs_str)
        if style_match:
            for item in style_match.group(1).split(";"):
                if ":" in item:
                    k, v = item.split(":", 1)
                    style[k.strip()] = v.strip()

        # Extract id
        el_id = f"n-{str(uuid.uuid4())[:8]}"
        id_match = re.search(r'id="([^"]*)"', attrs_str)
        if id_match:
            el_id = id_match.group(1)

        elements.append({
            "id": el_id,
            "name": f"{tag.capitalize()} Element",
            "tag": tag,
            "style": style,
            "text": text,
        })

    return elements
