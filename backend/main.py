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

# HTML parsing
from parse_html import parse_html_elements

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
    elif name == "move_nodes":
        return await _move_nodes(doc_id, arguments)
    elif name == "update_artboard":
        return await _update_artboard(doc_id, arguments)
    elif name == "save_document":
        return await _save_document(doc_id, arguments)
    elif name == "open_document":
        return await _open_document(doc_id, arguments)
    elif name == "export_html":
        return await _export_html(doc_id, arguments)
    elif name == "get_page_html":
        return await _get_page_html(doc_id, arguments)
    elif name == "get_html":
        return await _get_html(doc_id, arguments)
    elif name == "get_layout_diagnostics":
        return await _get_layout_diagnostics(doc_id, arguments)
    elif name == "get_overflow_report":
        return await _get_overflow_report(doc_id, arguments)
    elif name == "get_svg_summary":
        return await _get_svg_summary(doc_id, arguments)
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


# =============================================================================
# Inspection helpers
# =============================================================================

def _resolve_doc(doc_id):
    """Get document or default."""
    doc = doc_store.documents.get(doc_id) or doc_store.documents.get("default")
    return doc


def _resolve_node(doc, node_id):
    """Find a node (page or element) across all pages. Returns (page, element_or_None)."""
    if not node_id:
        return None, None
    for p in doc.pages:
        if p.id == node_id:
            return p, None
        for el in p.elements:
            if el.get("id") == node_id:
                return p, el
    return None, None


def _px_val(style, key):
    """Parse a px value from style dict. Returns float or None."""
    v = style.get(key) if style else None
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s.endswith("px"):
        s = s[:-2]
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _text_snippet(text, max_len=80):
    """First line of text, stripped and truncated."""
    if not text:
        return ""
    s = str(text).split("\n")[0].strip()
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def _geo_fields(el):
    """Extract geometry fields {x, y, width, height} from element style."""
    style = el.get("style") or {}
    x = _px_val(style, "left") or _px_val(style, "x")
    y = _px_val(style, "top") or _px_val(style, "y")
    w = _px_val(style, "width")
    h = _px_val(style, "height")
    return {"x": x, "y": y, "width": w, "height": h}


def _valid_child_ids(page, el):
    """Get children IDs of an element that actually exist on the page."""
    existing = {e["id"] for e in page.elements}
    return [cid for cid in el.get("children", []) if cid in existing]


def _root_element_ids(page):
    """Get IDs of root elements (no parentId) on a page."""
    return [el["id"] for el in page.elements if not el.get("parentId")]


# =============================================================================
# Layout diagnostics helpers
# =============================================================================


def _parse_len(value):
    """Parse a length value to float or None. Never loses 0."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s.endswith("px"):
        s = s[:-2]
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _get_precise_geo(el):
    """Extract geometry from element style without losing zero values.
    Returns {x, y, width, height} with float or None values."""
    style = el.get("style") or {}
    x = _parse_len(style.get("left"))
    if x is None:
        x = _parse_len(style.get("x"))
    y = _parse_len(style.get("top"))
    if y is None:
        y = _parse_len(style.get("y"))
    w = _parse_len(style.get("width"))
    h = _parse_len(style.get("height"))
    return {"x": x, "y": y, "width": w, "height": h}


def _collect_subtree_ids(page, root_id):
    """Collect root_id and all descendant IDs via children arrays. BFS with cycle protection."""
    el_by_id = {el["id"]: el for el in page.elements}
    ids = set()
    queue = [root_id]
    while queue:
        eid = queue.pop(0)
        if eid in ids:
            continue
        ids.add(eid)
        el = el_by_id.get(eid)
        if el:
            for cid in el.get("children", []):
                if cid not in ids:
                    queue.append(cid)
    return ids


def _rects_overlap(a, b):
    """AABB overlap check. Both are {x, y, width, height} with float values."""
    ax1 = a["x"]
    ay1 = a["y"]
    ax2 = a["x"] + a["width"]
    ay2 = a["y"] + a["height"]
    bx1 = b["x"]
    by1 = b["y"]
    bx2 = b["x"] + b["width"]
    by2 = b["y"] + b["height"]
    return ax1 < bx2 and bx1 < ax2 and ay1 < by2 and by1 < ay2


def _estimate_text_lines(el, geo):
    """Heuristic: estimate text height vs element height.
    Returns (estimated_height, should_report) or None if not applicable."""
    text = el.get("text") or ""
    if not text:
        return None
    w = geo.get("width")
    h = geo.get("height")
    if w is None or h is None or w <= 0:
        return None
    style = el.get("style") or {}
    fs_val = _parse_len(style.get("fontSize"))
    char_width = fs_val * 0.6 if fs_val else 8.0
    estimate_chars_per_line = max(1, w / char_width)
    lines = max(1, -(-len(text) // int(estimate_chars_per_line)))
    lh_val = _parse_len(style.get("lineHeight"))
    if lh_val is None:
        lh_val = fs_val * 1.2 if fs_val else 19.0
    estimated_height = lines * lh_val
    return estimated_height, estimated_height > h


# =============================================================================
# Overflow report helpers
# =============================================================================


def _resolve_diagnostic_target(doc, page_id, node_id):
    """Resolve (page, element) for diagnostic tools with page-constrained lookup.

    Returns (page, el, error_dict_or_None).
    - omitted both → current page
    - pageId only → that page
    - nodeId only → that page/element across all pages
    - both → pageId validated first, node lookup constrained to that page
    """
    target_page = None
    target_el = None
    requested_page = None

    if page_id:
        requested_page = next((p for p in doc.pages if p.id == page_id), None)
        if not requested_page:
            return None, None, {"success": False, "error": f"Page '{page_id}' not found"}

    if node_id:
        pages = [requested_page] if requested_page else doc.pages
        for page in pages:
            if page.id == node_id:
                target_page = page
                break
            for el in page.elements:
                if el.get("id") == node_id:
                    target_page = page
                    target_el = el
                    break
            if target_page:
                break
        if not target_page:
            if requested_page:
                return None, None, {"success": False, "error": f"Node '{node_id}' not found on page '{page_id}'"}
            return None, None, {"success": False, "error": f"Node '{node_id}' not found"}
    elif page_id:
        target_page = requested_page
    else:
        if not doc.pages:
            return None, None, {"success": False, "error": "No pages"}
        target_page = doc.pages[doc.current_page]

    return target_page, target_el, None


def _compute_overflow_amounts(x, y, w, h, bw, bh):
    """Compute per-side overflow amounts.

    Element box: (x, y, w, h). Boundary box: origin (0, 0), size (bw, bh).
    Returns {left, top, right, bottom} with non-negative pixel amounts.
    """
    return {
        "left": max(0.0, -x),
        "top": max(0.0, -y),
        "right": max(0.0, (x + w) - bw),
        "bottom": max(0.0, (y + h) - bh),
    }


def _format_overflow_message(overflow_type, amounts):
    """Format a human-readable message for an overflow item."""
    parts = []
    for side in ("left", "right", "top", "bottom"):
        a = amounts.get(side, 0)
        if a >= 1:
            parts.append(f"{a:.0f}px {side}")
    if not parts:
        return f"Node overflows {overflow_type.replace('-', ' ')}"
    return f"Node overflows {overflow_type.replace('-', ' ')} by " + ", ".join(parts)


# =============================================================================
# SVG summary helpers
# =============================================================================


_SVG_PRIMITIVE_TAGS = ("rect", "circle", "path", "line", "polyline", "polygon", "text")


def _collect_svg_descendants(page, svg_id):
    """BFS walk of children arrays from SVG root. Returns descendants (not the SVG itself)."""
    el_by_id = {el["id"]: el for el in page.elements}
    out = []
    seen = set()
    queue = [svg_id]
    while queue:
        eid = queue.pop(0)
        if eid in seen:
            continue
        seen.add(eid)
        if eid == svg_id:
            el = el_by_id.get(eid)
            if el:
                for cid in el.get("children", []):
                    if cid not in seen:
                        queue.append(cid)
            continue
        el = el_by_id.get(eid)
        if el:
            out.append(el)
            for cid in el.get("children", []):
                if cid not in seen:
                    queue.append(cid)
    return out


def _count_svg_primitives(descendants):
    """Count primitive tags in a list of descendants."""
    counts = {tag: 0 for tag in _SVG_PRIMITIVE_TAGS}
    for el in descendants:
        tag = el.get("tag", "")
        if tag in counts:
            counts[tag] += 1
    return counts


def _count_path_commands(d):
    """Count SVG path command letters in d attribute."""
    if not d:
        return 0
    return sum(1 for c in str(d) if c in "MmLlHhVvCcSsQqTtAaZz")


def _count_points(points_str):
    """Count coordinate pairs in points attribute. Best effort."""
    if not points_str:
        return 0
    import re
    nums = re.findall(r"-?\d+(?:\.\d+)?", str(points_str))
    return len(nums) // 2


def _build_svg_item(el):
    """Build a compact item dict for an SVG primitive by tag."""
    style = el.get("style", {}) or {}
    tag = el.get("tag", "")
    item = {"id": el.get("id", ""), "tag": tag}

    if tag == "rect":
        for k in ("x", "y", "width", "height"):
            v = style.get(k)
            if v is not None:
                item[k] = v
        for k in ("fill", "stroke"):
            v = style.get(k)
            if v is not None:
                item[k] = v
    elif tag == "circle":
        for k in ("cx", "cy", "r"):
            v = style.get(k)
            if v is not None:
                item[k] = v
        for k in ("fill", "stroke"):
            v = style.get(k)
            if v is not None:
                item[k] = v
    elif tag == "line":
        for k in ("x1", "y1", "x2", "y2"):
            v = style.get(k)
            if v is not None:
                item[k] = v
        v = style.get("stroke")
        if v is not None:
            item["stroke"] = v
    elif tag == "path":
        d = style.get("d")
        if d is not None:
            item["d"] = d
        for k in ("stroke", "fill"):
            v = style.get(k)
            if v is not None:
                item[k] = v
        pl = style.get("pathLength")
        if pl is not None:
            item["pathLength"] = pl
        d_str = style.get("d")
        if d_str is not None:
            item["commandCount"] = _count_path_commands(d_str)
    elif tag in ("polyline", "polygon"):
        pts = style.get("points")
        if pts is not None:
            item["points"] = pts
            item["pointCount"] = _count_points(pts)
        for k in ("stroke", "fill"):
            v = style.get(k)
            if v is not None:
                item[k] = v
    elif tag == "text":
        for k in ("x", "y"):
            v = style.get(k)
            if v is not None:
                item[k] = v
        v = style.get("fill")
        if v is not None:
            item["fill"] = v
        item["text"] = el.get("text", "") or ""
    else:
        for k in ("fill", "stroke", "d", "points", "viewBox", "cx", "cy", "r",
                  "x", "y", "x1", "y1", "x2", "y2", "width", "height"):
            v = style.get(k)
            if v is not None:
                item[k] = v
    return item


def _build_svg_hints(counts):
    """Apply chart-hint rules to a primitive-counts dict."""
    hints = []
    if counts.get("rect", 0) >= 3 and counts.get("text", 0) >= 1:
        hints.append("Likely bar chart: multiple rect elements with text labels")
    if counts.get("circle", 0) >= 2:
        hints.append("Contains multiple circles; possible scatter/bubble chart or node diagram")
    if counts.get("path", 0) >= 2 and counts.get("rect", 0) == 0:
        hints.append("Path-heavy SVG; possible line chart, area chart, icon, or custom diagram")
    if counts.get("line", 0) >= 2 and counts.get("text", 0) >= 1:
        hints.append("Contains lines and labels; possible axis, grid, or diagram")
    return hints


def _format_el_line(el):
    """One-line summary string for an element."""
    tag = el.get("tag", "div")
    name = el.get("name", "Element")
    el_id = el.get("id", "?")
    el_type = el.get("type", "")
    geo = _geo_fields(el)
    child_count = len(el.get("children", []))
    snippet = _text_snippet(el.get("text", ""))
    parts = [f"[{tag}] {name} ({el_id})"]
    if el_type:
        parts.append(f"type={el_type}")
    if geo["x"] is not None:
        parts.append(f"x={geo['x']:.0f}")
    if geo["y"] is not None:
        parts.append(f"y={geo['y']:.0f}")
    if geo["width"] is not None:
        parts.append(f"w={geo['width']:.0f}")
    if geo["height"] is not None:
        parts.append(f"h={geo['height']:.0f}")
    if child_count:
        parts.append(f"children={child_count}")
    if snippet:
        parts.append(f'text="{snippet}"')
    return " ".join(parts)


def _build_tree_lines(page, el_ids, max_depth, indent, seen):
    """Recursively build indented tree lines. max_depth controls child levels."""
    lines = []
    el_by_id = {el["id"]: el for el in page.elements}
    for el_id in el_ids:
        el = el_by_id.get(el_id)
        if not el:
            continue
        if el_id in seen:
            lines.append(f"{indent}[cycle] ... ({el_id})")
            continue
        seen.add(el_id)
        lines.append(f"{indent}{_format_el_line(el)}")
        if max_depth > 0:
            child_ids = _valid_child_ids(page, el)
            lines.extend(_build_tree_lines(page, child_ids, max_depth - 1, indent + "  ", seen))
    return lines


def _child_info(page, el, page_id):
    """Build a child info dict for responses."""
    geo = _geo_fields(el)
    child_count = len(el.get("children", []))
    snippet = _text_snippet(el.get("text", ""))
    return {
        "id": el.get("id", ""),
        "name": el.get("name", "Element"),
        "tag": el.get("tag", "div"),
        "type": el.get("type", ""),
        "parentId": el.get("parentId"),
        "pageId": page_id,
        "childCount": child_count,
        "textSnippet": snippet,
        "x": geo["x"],
        "y": geo["y"],
        "width": geo["width"],
        "height": geo["height"],
    }


async def _get_tree_summary(doc_id: str, args: dict) -> dict:
    doc = _resolve_doc(doc_id)
    if not doc:
        return {"summary": "Empty document"}
    node_id = args.get("nodeId", "")
    max_depth = args.get("depth", 5)

    if node_id:
        page, el = _resolve_node(doc, node_id)
        if not page:
            return {"summary": f"Node '{node_id}' not found"}
        if el is None:
            roots = _root_element_ids(page)
            page_line = f'Page "{page.name}" ({page.id}) {page.width}x{page.height} at x={page.x} y={page.y} bg={page.backgroundColor or "#ffffff"} children={len(roots)}'
            lines = [page_line]
            if max_depth > 0:
                lines.extend(_build_tree_lines(page, roots, max_depth - 1, "  ", set()))
        else:
            el_line = _format_el_line(el)
            lines = [el_line]
            if max_depth > 0:
                child_ids = _valid_child_ids(page, el)
                lines.extend(_build_tree_lines(page, child_ids, max_depth - 1, "  ", set()))
    else:
        if not doc.pages:
            return {"summary": "No artboards"}
        page = doc.pages[doc.current_page]
        roots = _root_element_ids(page)
        page_line = f'Page "{page.name}" ({page.id}) {page.width}x{page.height} at x={page.x} y={page.y} bg={page.backgroundColor or "#ffffff"} children={len(roots)}'
        lines = [page_line]
        if max_depth > 0:
            lines.extend(_build_tree_lines(page, roots, max_depth - 1, "  ", set()))

    return {"summary": "\n".join(lines)}


async def _get_children(doc_id: str, args: dict) -> dict:
    doc = _resolve_doc(doc_id)
    if not doc:
        return {"children": []}
    node_id = args.get("nodeId", "")
    if not node_id:
        if not doc.pages:
            return {"children": [], "error": "No artboards"}
        page = doc.pages[doc.current_page]
        el = None
    else:
        page, el = _resolve_node(doc, node_id)
        if not page:
            return {"children": [], "error": f"Node '{node_id}' not found"}
    if el is None:
        child_ids = _root_element_ids(page)
    else:
        child_ids = _valid_child_ids(page, el)
    children = []
    el_by_id = {e["id"]: e for e in page.elements}
    for cid in child_ids:
        child = el_by_id.get(cid)
        if child:
            children.append(_child_info(page, child, page.id))
    return {"children": children}


async def _get_node_info(doc_id: str, args: dict) -> dict:
    doc = _resolve_doc(doc_id)
    if not doc:
        return {"error": "Document not found"}
    node_id = args.get("nodeId", "")
    if not node_id:
        if not doc.pages:
            return {"error": "No artboards"}
        page = doc.pages[doc.current_page]
        el = None
    else:
        page, el = _resolve_node(doc, node_id)
        if not page:
            return {"error": f"Node '{node_id}' not found"}
    if el is None:
        roots = _root_element_ids(page)
        return {
            "id": page.id,
            "kind": "page",
            "name": page.name,
            "x": page.x,
            "y": page.y,
            "width": page.width,
            "height": page.height,
            "backgroundColor": page.backgroundColor or "#ffffff",
            "childIds": roots,
            "childCount": len(roots),
            "elementCount": len(page.elements),
        }
    else:
        geo = _geo_fields(el)
        child_ids = _valid_child_ids(page, el)
        el_by_id = {e["id"]: e for e in page.elements}
        children = []
        for cid in child_ids:
            child = el_by_id.get(cid)
            if child:
                children.append(_child_info(page, child, page.id))
        return {
            "id": el.get("id", ""),
            "kind": "element",
            "name": el.get("name", "Element"),
            "tag": el.get("tag", "div"),
            "type": el.get("type", ""),
            "parentId": el.get("parentId"),
            "pageId": page.id,
            "style": el.get("style", {}),
            "text": el.get("text", ""),
            "textSnippet": _text_snippet(el.get("text", "")),
            "children": children,
            "childIds": child_ids,
            "childCount": len(child_ids),
            "x": geo["x"],
            "y": geo["y"],
            "width": geo["width"],
            "height": geo["height"],
        }


async def _get_screenshot(doc_id: str, args: dict) -> dict:
    stored = doc_store.get_screenshot_data(doc_id)
    if not stored:
        return {"success": False, "error": "No screenshot available for document"}

    page_id = args.get("pageId") or None
    node_id = args.get("nodeId") or None
    requested_scale = args.get("scale", 1)
    requested_transparent = args.get("transparent", False)
    include_data = True if args.get("includeData") is None else bool(args["includeData"])
    resolved_page_id = page_id or stored.get("pageId")
    resolved_node_id = node_id or (None if page_id else stored.get("nodeId"))

    if page_id or node_id:
        doc = _resolve_doc(doc_id)
        if not doc:
            return {"success": False, "error": "Document not found"}
        target_page, target_el, err = _resolve_diagnostic_target(doc, page_id, node_id)
        if err:
            return err
        if target_page:
            resolved_page_id = target_page.id
        if node_id:
            resolved_node_id = target_el.get("id") if target_el else target_page.id

    response = {
        "success": True,
        "pageId": resolved_page_id,
        "nodeId": resolved_node_id,
        "mimeType": stored.get("mimeType", ""),
        "byteLength": stored.get("byteLength", 0),
        "capturedAt": stored.get("capturedAt"),
        "storedPageId": stored.get("pageId"),
        "storedNodeId": stored.get("nodeId"),
        "storedScale": stored.get("scale", 1),
        "storedTransparent": stored.get("transparent", False),
        "requestedScale": requested_scale,
        "requestedTransparent": requested_transparent,
        "summary": f"Latest screenshot available: {stored.get('mimeType', '')}, {stored.get('byteLength', 0)} bytes",
    }
    if include_data:
        response["data"] = stored.get("data", "")
    return response


async def _write_html(doc_id: str, args: dict) -> dict:
    html = args.get("html", "")
    mode = args.get("mode", "append")
    target_node_id = args.get("targetNodeId", "") or None
    page_id = args.get("pageId", "") or None
    if not doc_id:
        doc_id = "default"
    if not html:
        return {"success": False, "error": "html is required"}
    return doc_store.write_html(doc_id, html, mode=mode, target_node_id=target_node_id, page_id=page_id)


async def _duplicate_nodes(doc_id: str, args: dict) -> dict:
    if not doc_id:
        doc_id = "default"
    node_ids = args.get("nodeIds", [])
    if not isinstance(node_ids, list) or not node_ids:
        return {"success": False, "duplicated": [], "duplicatedCount": 0,
                "errors": [{"error": "nodeIds must be a non-empty list"}]}
    try:
        offset_x = float(args.get("offsetX", 20))
        offset_y = float(args.get("offsetY", 20))
    except (TypeError, ValueError):
        return {"success": False, "duplicated": [], "duplicatedCount": 0,
                "errors": [{"error": "offsetX/offsetY must be numeric"}]}
    return doc_store.duplicate_subtree_batch(doc_id, node_ids, offset_x, offset_y)


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
    """Rename element nodes and page/artboard nodes.

    - Renames element nodes (updates ``el["name"]``) and page/artboard nodes
      (updates ``Page.name``). Other fields (id, children, style, text, tag,
      type, size, position, current page, etc.) are preserved.
    - Optional ``pageId`` constrains the lookup to one page: when provided,
      a nodeId equal to ``pageId`` renames the page itself; any other nodeId
      is searched only within that page's elements.
    - When ``pageId`` is omitted, page IDs win over element IDs (a nodeId that
      matches any page is treated as a page rename; otherwise the first
      matching element across all pages is renamed).
    - Missing or invalid names for a requested node produce an error entry
      and do not rename that node; other valid renames still proceed.
    - Save is called once at the end if any rename succeeded.

    Input:
        ``nodeIds`` (list[str], required, non-empty)
        ``names`` (dict[nodeId -> str], required, non-empty; each value must
            be a non-blank string — checked via ``str.strip()``)
        ``pageId`` (str, optional)

    Response:
        ``success``: True if at least one rename succeeded, else False
        ``renamed``: list of {nodeId, pageId, kind, oldName, newName, node}
        ``renamedCount``: int
        ``errors``: list of {nodeId, error}
    """
    if not doc_id:
        doc_id = "default"

    # 1. validate nodeIds
    node_ids = args.get("nodeIds")
    if not isinstance(node_ids, list) or not node_ids:
        return {"success": False, "renamed": [], "renamedCount": 0,
                "errors": [{"error": "nodeIds must be a non-empty list"}]}

    # 2. validate names
    names = args.get("names")
    if not isinstance(names, dict) or not names:
        return {"success": False, "renamed": [], "renamedCount": 0,
                "errors": [{"error": "names must be a non-empty object"}]}

    # 3. resolve document
    doc = doc_store.documents.get(doc_id)
    if not doc:
        return {"success": False, "renamed": [], "renamedCount": 0,
                "errors": [{"error": "Document not found"}]}

    # 4. validate pageId first if provided
    page_id = args.get("pageId") or None
    if page_id is not None:
        page_by_id = {p.id: p for p in doc.pages}
        if page_id not in page_by_id:
            return {"success": False, "renamed": [], "renamedCount": 0,
                    "errors": [{"error": f"Page '{page_id}' not found"}]}

    # 5. process each deduped node ID
    renamed = []
    errors = []
    seen = set()
    for nid in node_ids:
        if not isinstance(nid, str) or not nid:
            errors.append({"nodeId": nid, "error": "nodeId must be a non-empty string"})
            continue
        if nid in seen:
            continue  # silent dedup
        seen.add(nid)

        # name presence + validity
        if nid not in names:
            errors.append({"nodeId": nid, "error": f"Missing name for node '{nid}'"})
            continue
        new_name = names[nid]
        if not (isinstance(new_name, str) and new_name.strip() != ""):
            errors.append({"nodeId": nid,
                           "error": f"Invalid name for node '{nid}': must be a non-empty string"})
            continue

        # Lookup per spec priority
        page_obj = None  # the page object, when found
        el_obj = None    # the element dict, when found
        kind = None

        if page_id is not None:
            target_page = page_by_id[page_id]
            if nid == page_id:
                page_obj = target_page
                kind = "page"
            else:
                for e in target_page.elements:
                    if e.get("id") == nid:
                        el_obj = e
                        page_obj = target_page
                        kind = "element"
                        break
                if el_obj is None:
                    errors.append({"nodeId": nid,
                                   "error": f"Node '{nid}' not found on page '{page_id}'"})
                    continue
        else:
            # page ID match first
            matched_page = None
            for p in doc.pages:
                if p.id == nid:
                    matched_page = p
                    break
            if matched_page is not None:
                page_obj = matched_page
                kind = "page"
            else:
                # first element match across all pages
                for p in doc.pages:
                    for e in p.elements:
                        if e.get("id") == nid:
                            el_obj = e
                            page_obj = p
                            kind = "element"
                            break
                    if el_obj is not None:
                        break
                if el_obj is None:
                    errors.append({"nodeId": nid, "error": f"Node '{nid}' not found"})
                    continue

        # Mutate + record
        if kind == "page":
            old_name = page_obj.name
            page_obj.name = new_name
            renamed.append({
                "nodeId": page_obj.id,
                "pageId": page_obj.id,
                "kind": "page",
                "oldName": old_name,
                "newName": new_name,
                "node": {
                    "id": page_obj.id,
                    "name": page_obj.name,
                    "x": page_obj.x,
                    "y": page_obj.y,
                    "width": page_obj.width,
                    "height": page_obj.height,
                    "backgroundColor": page_obj.backgroundColor,
                    "elements": page_obj.elements,
                },
            })
        else:
            old_name = el_obj.get("name", "")
            el_obj["name"] = new_name
            renamed.append({
                "nodeId": el_obj.get("id"),
                "pageId": page_obj.id,
                "kind": "element",
                "oldName": old_name,
                "newName": new_name,
                "node": el_obj,
            })

    if renamed:
        doc_store._save(doc_id)

    return {
        "success": len(renamed) > 0,
        "renamed": renamed,
        "renamedCount": len(renamed),
        "errors": errors,
    }


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
    x = args.get("x")
    y = args.get("y")
    page_id = args.get("pageId")  # optionally specified by caller
    if not doc_id:
        doc_id = "default"
    doc = doc_store.documents.get(doc_id)
    if doc:
        # Auto-layout: if caller didn't specify x/y, place new artboard to the right
        # of the rightmost existing artboard (horizontal tiling).
        if x is None or y is None:
            if doc.pages:
                rightmost_x = max(p.x + p.width for p in doc.pages)
                x = x if x is not None else rightmost_x + 24
                y = y if y is not None else 0
            else:
                x = x or 0
                y = y or 0

        # Generate unique ID — either caller-specified or a fresh uuid
        if not page_id:
            import uuid
            page_id = f"page-{str(uuid.uuid4())[:8]}"
        # Avoid collision (shouldn't happen with uuid, but safety-check)
        while any(p.id == page_id for p in doc.pages):
            import uuid
            page_id = f"page-{str(uuid.uuid4())[:8]}"
        page = Page(id=page_id, name=name, width=width, height=height, x=x, y=y)
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
    """Delete element subtrees; cleans parent/children references defensively."""
    if not doc_id:
        doc_id = "default"
    node_ids = args.get("nodeIds", [])
    page_id = args.get("pageId") or None
    return doc_store.delete_subtrees(doc_id, node_ids, page_id)


async def _move_nodes(doc_id: str, args: dict) -> dict:
    if not doc_id:
        doc_id = "default"
    node_ids = args.get("nodeIds", [])
    target_parent_id = args.get("targetParentId") or None
    page_id = args.get("pageId") or None
    index = args.get("index")
    return doc_store.move_nodes(doc_id, node_ids, target_parent_id, page_id, index)


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


async def _get_page_html(doc_id: str, args: dict) -> dict:
    page_id = args.get("pageId", "") or None
    return doc_store.get_page_html(doc_id, page_id=page_id)


async def _get_html(doc_id: str, args: dict) -> dict:
    node_id = args.get("nodeId", "") or None
    page_id = args.get("pageId", "") or None
    return doc_store.get_node_html(doc_id, node_id=node_id, page_id=page_id)


async def _get_layout_diagnostics(doc_id: str, args: dict) -> dict:
    """Report likely layout issues: overlap, clipping, text overflow, off-artboard, zero-size, missing dimensions."""
    doc = _resolve_doc(doc_id)
    if not doc:
        return {"success": False, "error": "Document not found"}

    page_id = args.get("pageId") or None
    node_id = args.get("nodeId") or None
    include_overlaps = True if args.get("includeOverlaps") is None else args["includeOverlaps"]
    include_text = True if args.get("includeText") is None else args["includeText"]

    target_page = None
    target_el = None
    requested_page = None

    if page_id:
        requested_page = next((p for p in doc.pages if p.id == page_id), None)
        if not requested_page:
            return {"success": False, "error": f"Page '{page_id}' not found"}

    if node_id:
        pages = [requested_page] if requested_page else doc.pages
        for page in pages:
            if page.id == node_id:
                target_page = page
                break
            for el in page.elements:
                if el.get("id") == node_id:
                    target_page = page
                    target_el = el
                    break
            if target_page:
                break
        if not target_page:
            if requested_page:
                return {"success": False, "error": f"Node '{node_id}' not found on page '{page_id}'"}
            return {"success": False, "error": f"Node '{node_id}' not found"}
    elif page_id:
        target_page = requested_page
    else:
        if not doc.pages:
            return {"success": False, "error": "No pages"}
        target_page = doc.pages[doc.current_page]

    el_by_id = {el["id"]: el for el in target_page.elements}

    if target_el is None:
        check_elements = target_page.elements
    else:
        subtree_ids = _collect_subtree_ids(target_page, target_el["id"])
        check_elements = [el for el in target_page.elements if el.get("id") in subtree_ids]

    el_parent_map = {}
    for el in check_elements:
        pid = el.get("parentId")
        el_parent_map[el["id"]] = el_by_id.get(pid) if pid else None

    issues = []
    overlap_reported = set()

    for el in check_elements:
        geo = _get_precise_geo(el)
        el_id = el.get("id", "")
        tag = el.get("tag", "div")

        geo_for_issue = {
            "x": geo["x"], "y": geo["y"],
            "width": geo["width"], "height": geo["height"],
        }

        # missing-dimensions
        if tag not in ("span", "strong", "em", "br"):
            if geo["width"] is None or geo["height"] is None:
                issues.append({
                    "type": "missing-dimensions", "severity": "info",
                    "nodeId": el_id, "pageId": target_page.id,
                    "message": "Element is missing width or height",
                    "geometry": geo_for_issue,
                })

        # zero-size
        w, h = geo["width"], geo["height"]
        if (w is not None and w == 0) or (h is not None and h == 0):
            issues.append({
                "type": "zero-size", "severity": "warning",
                "nodeId": el_id, "pageId": target_page.id,
                "message": f"Element has zero size (w={w}, h={h})",
                "geometry": geo_for_issue,
            })

        # off-artboard
        x_val, y_val = geo["x"], geo["y"]
        if w is not None and h is not None and x_val is not None and y_val is not None:
            page_w, page_h = target_page.width, target_page.height
            off_right = (x_val + w) - page_w
            off_bottom = (y_val + h) - page_h
            if x_val < 0 or y_val < 0 or off_right > 0 or off_bottom > 0:
                parts = []
                if x_val < 0:
                    parts.append(f"extends {int(abs(x_val))}px beyond the left edge")
                if y_val < 0:
                    parts.append(f"extends {int(abs(y_val))}px beyond the top edge")
                if off_right > 0:
                    parts.append(f"extends {int(off_right)}px beyond the right edge")
                if off_bottom > 0:
                    parts.append(f"extends {int(off_bottom)}px beyond the bottom edge")
                issues.append({
                    "type": "off-artboard", "severity": "warning",
                    "nodeId": el_id, "pageId": target_page.id,
                    "message": "Node " + "; ".join(parts),
                    "geometry": geo_for_issue,
                })

        # suspicious-position
        if x_val is not None and abs(x_val) > target_page.width * 2:
            issues.append({
                "type": "suspicious-position", "severity": "warning",
                "nodeId": el_id, "pageId": target_page.id,
                "message": f"Node has an unusually large x position ({x_val:.0f}px, page width is {target_page.width}px)",
                "geometry": geo_for_issue,
            })
        if y_val is not None and abs(y_val) > target_page.height * 2:
            issues.append({
                "type": "suspicious-position", "severity": "warning",
                "nodeId": el_id, "pageId": target_page.id,
                "message": f"Node has an unusually large y position ({y_val:.0f}px, page height is {target_page.height}px)",
                "geometry": geo_for_issue,
            })

        # overflow (child extends outside parent)
        parent = el_parent_map.get(el_id)
        if parent:
            pg = _get_precise_geo(parent)
            pw, ph = pg["width"], pg["height"]
            if (pw is not None and ph is not None and
                x_val is not None and y_val is not None and
                w is not None and h is not None):
                if x_val + w > pw:
                    ox = (x_val + w) - pw
                    issues.append({
                        "type": "overflow", "severity": "warning",
                        "nodeId": el_id, "pageId": target_page.id,
                        "message": f"Child extends {ox:.0f}px beyond the right edge of its parent",
                        "geometry": geo_for_issue,
                    })
                if y_val + h > ph:
                    oy = (y_val + h) - ph
                    issues.append({
                        "type": "overflow", "severity": "warning",
                        "nodeId": el_id, "pageId": target_page.id,
                        "message": f"Child extends {oy:.0f}px beyond the bottom edge of its parent",
                        "geometry": geo_for_issue,
                    })

        # text-overflow heuristic
        if include_text:
            est = _estimate_text_lines(el, geo)
            if est:
                est_height, overflows = est
                if overflows:
                    issues.append({
                        "type": "text-overflow", "severity": "warning",
                        "nodeId": el_id, "pageId": target_page.id,
                        "message": f"Estimated text may overflow (estimated height: {est_height:.0f}px > element height: {h:.0f}px)",
                        "geometry": geo_for_issue,
                    })

    # Sibling overlap (separate pass, only when requested)
    if include_overlaps:
        groups = {}
        for el in check_elements:
            parent_key = el.get("parentId") or "__page_root__"
            geo = _get_precise_geo(el)
            w, h = geo["width"], geo["height"]
            if (w is not None and h is not None and w > 0 and h > 0 and
                geo["x"] is not None and geo["y"] is not None):
                groups.setdefault(parent_key, []).append((el, geo))

        for sibling_list in groups.values():
            for i in range(len(sibling_list)):
                for j in range(i + 1, len(sibling_list)):
                    el_a, ga = sibling_list[i]
                    el_b, gb = sibling_list[j]
                    pair = tuple(sorted([el_a.get("id", ""), el_b.get("id", "")]))
                    if pair in overlap_reported:
                        continue
                    if _rects_overlap(ga, gb):
                        overlap_reported.add(pair)
                        issues.append({
                            "type": "overlap", "severity": "warning",
                            "nodeId": el_a.get("id", ""),
                            "otherNodeId": el_b.get("id", ""),
                            "pageId": target_page.id,
                            "message": f"Node overlaps sibling {el_b.get('id', '')}",
                            "geometry": {
                                "x": ga["x"], "y": ga["y"],
                                "width": ga["width"], "height": ga["height"],
                            },
                        })

    target_node_id = target_el.get("id") if target_el else None

    return {
        "success": True,
        "pageId": target_page.id,
        "targetNodeId": target_node_id,
        "checkedNodeCount": len(check_elements),
        "issueCount": len(issues),
        "issues": issues,
        "summary": f"{len(issues)} issues across {len(check_elements)} checked nodes",
    }


async def _get_overflow_report(doc_id: str, args: dict) -> dict:
    """Report nodes that overflow their parent or artboard, including per-side amounts."""
    doc = _resolve_doc(doc_id)
    if not doc:
        return {"success": False, "error": "Document not found"}

    page_id = args.get("pageId") or None
    node_id = args.get("nodeId") or None

    include_artboard = True if args.get("includeArtboard") is None else args["includeArtboard"]
    include_parent = True if args.get("includeParent") is None else args["includeParent"]

    try:
        min_overflow = float(args.get("minOverflow", 1))
    except (TypeError, ValueError):
        min_overflow = 1.0
    if min_overflow < 0:
        min_overflow = 1.0

    target_page, target_el, err = _resolve_diagnostic_target(doc, page_id, node_id)
    if err:
        return err

    el_by_id = {el["id"]: el for el in target_page.elements}

    if target_el is None:
        check_elements = target_page.elements
    else:
        subtree_ids = _collect_subtree_ids(target_page, target_el["id"])
        check_elements = [el for el in target_page.elements if el.get("id") in subtree_ids]

    overflows = []

    for el in check_elements:
        geo = _get_precise_geo(el)
        x_val, y_val, w, h = geo["x"], geo["y"], geo["width"], geo["height"]
        if x_val is None or y_val is None or w is None or h is None:
            continue

        el_id = el.get("id", "")
        geo_for_issue = {"x": x_val, "y": y_val, "width": w, "height": h}

        # Artboard overflow
        if include_artboard:
            amounts = _compute_overflow_amounts(x_val, y_val, w, h, target_page.width, target_page.height)
            if any(amounts[s] >= min_overflow for s in ("left", "top", "right", "bottom")):
                severity = "error" if max(amounts.values()) >= 100 else "warning"
                overflows.append({
                    "type": "artboard-overflow",
                    "nodeId": el_id,
                    "pageId": target_page.id,
                    "severity": severity,
                    "amount": amounts,
                    "geometry": geo_for_issue,
                    "boundary": {
                        "kind": "page",
                        "id": target_page.id,
                        "width": target_page.width,
                        "height": target_page.height,
                    },
                    "message": _format_overflow_message("artboard", amounts),
                })

        # Parent overflow (skip root elements)
        if include_parent and el.get("parentId"):
            parent = el_by_id.get(el["parentId"])
            if parent:
                pg = _get_precise_geo(parent)
                pw, ph = pg["width"], pg["height"]
                if pw is not None and ph is not None:
                    amounts = _compute_overflow_amounts(x_val, y_val, w, h, pw, ph)
                    if any(amounts[s] >= min_overflow for s in ("left", "top", "right", "bottom")):
                        severity = "error" if max(amounts.values()) >= 100 else "warning"
                        overflows.append({
                            "type": "parent-overflow",
                            "nodeId": el_id,
                            "pageId": target_page.id,
                            "severity": severity,
                            "amount": amounts,
                            "geometry": geo_for_issue,
                            "boundary": {
                                "kind": "parent",
                                "id": parent.get("id", ""),
                                "width": pw,
                                "height": ph,
                            },
                            "message": _format_overflow_message("parent", amounts),
                        })

    target_node_id = target_el.get("id") if target_el else None

    return {
        "success": True,
        "pageId": target_page.id,
        "targetNodeId": target_node_id,
        "checkedNodeCount": len(check_elements),
        "overflowCount": len(overflows),
        "overflows": overflows,
        "summary": f"{len(overflows)} overflowing nodes across {len(check_elements)} checked nodes",
    }


async def _get_svg_summary(doc_id: str, args: dict) -> dict:
    """Summarize SVG elements and their primitives for text-only inspection."""
    doc = _resolve_doc(doc_id)
    if not doc:
        return {"success": False, "error": "Document not found"}

    page_id = args.get("pageId") or None
    node_id = args.get("nodeId") or None

    try:
        max_items = int(args.get("maxItems", 50))
    except (TypeError, ValueError):
        max_items = 50
    if max_items < 1:
        max_items = 50

    target_page, target_el, err = _resolve_diagnostic_target(doc, page_id, node_id)
    if err:
        return err

    el_by_id = {el["id"]: el for el in target_page.elements}

    # Decide which SVGs to summarize
    svg_roots = []
    if target_el is None:
        # All SVGs on the page
        svg_roots = [el for el in target_page.elements if el.get("tag") == "svg"]
    elif target_el.get("tag") == "svg":
        svg_roots = [target_el]
    else:
        # Non-SVG parent: find SVG descendants in subtree
        subtree_ids = _collect_subtree_ids(target_page, target_el["id"])
        svg_roots = [
            el_by_id[sid] for sid in subtree_ids
            if sid in el_by_id and el_by_id[sid].get("tag") == "svg"
        ]

    svgs_out = []
    for svg in svg_roots:
        style = svg.get("style", {}) or {}
        geo = _get_precise_geo(svg)

        descendants = _collect_svg_descendants(target_page, svg["id"])
        counts = _count_svg_primitives(descendants)

        items = []
        labels = []
        item_slots_used = 0
        for d in descendants:
            tag = d.get("tag", "")
            if tag == "text":
                if item_slots_used < max_items:
                    items.append(_build_svg_item(d))
                    item_slots_used += 1
                if len(labels) < max_items:
                    text_content = d.get("text", "") or ""
                    label_entry = {
                        "id": d.get("id", ""),
                        "text": text_content,
                    }
                    d_style = d.get("style", {}) or {}
                    lx = d_style.get("x")
                    ly = d_style.get("y")
                    if lx is not None:
                        label_entry["x"] = lx
                    if ly is not None:
                        label_entry["y"] = ly
                    labels.append(label_entry)
            else:
                if item_slots_used < max_items:
                    items.append(_build_svg_item(d))
                    item_slots_used += 1

        hints = _build_svg_hints(counts)

        geometry = {}
        for k, key_out in (("x", "x"), ("y", "y"), ("width", "width"), ("height", "height")):
            v = geo.get(k)
            if v is not None:
                geometry[key_out] = v

        summary_parts = []
        for tag in _SVG_PRIMITIVE_TAGS:
            n = counts.get(tag, 0)
            if n:
                summary_parts.append(f"{n} {tag}")
        summary_str = f"SVG {svg.get('id', '?')}: " + ", ".join(summary_parts) if summary_parts else f"SVG {svg.get('id', '?')}: (empty)"

        svg_summary = {
            "id": svg.get("id", ""),
            "pageId": target_page.id,
            "name": svg.get("name", "SVG"),
            "geometry": geometry,
            "viewBox": style.get("viewBox"),
            "primitiveCounts": counts,
            "items": items,
            "labels": labels,
            "hints": hints,
            "summary": summary_str,
        }
        svgs_out.append(svg_summary)

    target_node_id = target_el.get("id") if target_el else None

    return {
        "success": True,
        "pageId": target_page.id,
        "targetNodeId": target_node_id,
        "svgCount": len(svgs_out),
        "svgs": svgs_out,
        "summary": f"{len(svgs_out)} SVG(s) found on page {target_page.id}",
    }


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




# =============================================================================
# MCP Protocol Endpoints - unified handler supporting both formats
# - JSON-RPC 2.0: {jsonrpc, method, params} (for stdio bridge)
# - HTTP type: {name, arguments} (for Claude Code "type: http" config)
# =============================================================================

TOOLS_LIST = [
    {"name": "get_basic_info", "description": "Get basic document info", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_selection", "description": "Get selected nodes", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_tree_summary", "description": "Get hierarchical tree summary of the document", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string", "description": "Optional. Page or element ID. Omit to use current page."}, "depth": {"type": "number", "description": "How many levels to show. 0 = target only. Default 5."}}}},
    {"name": "get_children", "description": "Get direct children of a node", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string", "description": "Optional. Page or element ID. Omit to use current page."}}}},
    {"name": "get_node_info", "description": "Get detailed info about a page or element", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string", "description": "Optional. Page or element ID. Omit to use current page."}}}},
    {"name": "get_screenshot", "description": "Get the latest stored screenshot and metadata for the document.", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Optional page ID."}, "nodeId": {"type": "string", "description": "Optional page or element ID."}, "scale": {"type": "number", "description": "Requested scale preference. Default 1."}, "transparent": {"type": "boolean", "description": "Requested transparency preference. Default false."}, "includeData": {"type": "boolean", "description": "Whether to include the screenshot data in the response. Default true."}}}},
    {"name": "write_html", "description": "Write HTML into a document. Supports targeted append/replace-children/replace modes. Use targetNodeId to target an existing element or page. Without targetNodeId, uses pageId or the current page.", "inputSchema": {"type": "object", "properties": {"html": {"type": "string", "description": "HTML string with inline styles. The outermost element fills the artboard automatically; no need to set position/width/height."}, "targetNodeId": {"type": "string", "description": "Target page or element ID. If targeting an element, the mode operates on that element. If targeting a page, the mode operates on the page root."}, "pageId": {"type": "string", "description": "Target page ID (used only if targetNodeId is not provided). If omitted, uses the current page."}, "mode": {"type": "string", "description": "One of: 'append' (default) — add as children of target, 'replace-children' — remove target's children then append, 'replace' — replace target element itself with new content"}}, "required": ["html"]}},
    {"name": "duplicate_nodes", "description": "Duplicate full element subtrees and return per-root descendant ID maps.", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}, "description": "Element node IDs to duplicate. Required, non-empty."}, "offsetX": {"type": "number", "description": "Horizontal offset applied to cloned root's positional style. Default 20."}, "offsetY": {"type": "number", "description": "Vertical offset applied to cloned root's positional style. Default 20."}}, "required": ["nodeIds"]}},
    {"name": "update_styles", "description": "Update styles", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}, "styles": {"type": "object"}}, "required": ["nodeIds", "styles"]}},
    {"name": "set_text_content", "description": "Set text content", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}, "text": {"type": "string"}}, "required": ["nodeIds", "text"]}},
    {"name": "rename_nodes", "description": "Rename element nodes and page/artboard nodes. Returns per-node results with oldName/newName/kind/pageId/node. Supports an optional pageId constraint to scope the lookup to a single page (or rename that page itself when a nodeId equals pageId).", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}, "description": "Node IDs to rename (elements and/or page IDs). Required, non-empty."}, "names": {"type": "object", "description": "Map of nodeId -> new name. Every requested ID must have a non-empty string entry (whitespace-only is invalid)."}, "pageId": {"type": "string", "description": "Optional page ID. If provided, validates first and scopes the lookup to that page; if a nodeId equals pageId, that page is renamed."}}, "required": ["nodeIds", "names"]}},
    {"name": "finish_working_on_nodes", "description": "Mark work finished", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_computed_styles", "description": "Get computed styles", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}}}},
    {"name": "get_jsx", "description": "Export as JSX", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}}}}},
    {"name": "get_font_family_info", "description": "Get font info", "inputSchema": {"type": "object", "properties": {"fontFamily": {"type": "string"}}}},
    {"name": "save_document", "description": "Save document", "inputSchema": {"type": "object", "properties": {"filePath": {"type": "string"}}}},
    {"name": "open_document", "description": "Open document", "inputSchema": {"type": "object", "properties": {"filePath": {"type": "string"}}, "required": ["filePath"]}},
    {"name": "export_html", "description": "Export as HTML", "inputSchema": {"type": "object", "properties": {"pretty": {"type": "boolean"}}}},
    {"name": "get_page_html", "description": "Get clean exported HTML for one page/artboard", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Optional. Page ID. Omit to use current page."}, "pretty": {"type": "boolean", "description": "Pretty-print the HTML. Default true."}}}},
    {"name": "get_html", "description": "Get clean exported HTML for the current page, a page, or an element subtree.", "inputSchema": {"type": "object", "properties": {"nodeId": {"type": "string", "description": "Optional. Page or element ID. Omit to use current page."}, "pageId": {"type": "string", "description": "Optional. Target page ID."}, "pretty": {"type": "boolean", "description": "Pretty-print the HTML. Default true."}}}},
    {"name": "create_artboard", "description": "Create a new artboard/page", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Optional page ID (e.g. 'hero-section'). Auto-generated if omitted."}, "name": {"type": "string", "description": "Artboard name (e.g. 'Header', 'Hero Section', 'Mobile Home')"}, "width": {"type": "number", "description": "Width in pixels (e.g. 1440 for desktop, 375 for mobile)"}, "height": {"type": "number", "description": "Height in pixels (e.g. 900 for desktop hero, 812 for mobile)"}, "x": {"type": "number", "description": "X position on canvas. If omitted, auto-places to the right of existing artboards."}, "y": {"type": "number", "description": "Y position on canvas. If omitted, auto-places to the right of existing artboards."}}}},
    {"name": "delete_artboard", "description": "Delete an artboard/page", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Page ID to delete"}}, "required": ["pageId"]}},
    {"name": "delete_nodes", "description": "Delete element subtrees. Removes each requested node plus all of its descendants, cleans up parent/children references, and supports optional pageId constraint.", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}, "description": "Element node IDs to delete. Required, non-empty."}, "pageId": {"type": "string", "description": "Optional page ID. If provided, validates first and constrains deletion to that page."}}, "required": ["nodeIds"]}},
    {"name": "move_nodes", "description": "Move element nodes within the same page (reorder or reparent). Preserves whole subtrees. Same-page only — cross-page moves are rejected.", "inputSchema": {"type": "object", "properties": {"nodeIds": {"type": "array", "items": {"type": "string"}, "description": "Element node IDs to move. Required, non-empty."}, "targetParentId": {"type": "string", "description": "Target page ID or element ID. If omitted, pageId is used as the page-root target."}, "pageId": {"type": "string", "description": "Optional page ID. If provided, constrains targetParentId lookup to that page; otherwise targetParentId can be any page or element."}, "index": {"type": "number", "description": "Insertion index inside the target's children array (or page-root order). Omitted or invalid → append at end."}}, "required": ["nodeIds"]}},
    {"name": "update_artboard", "description": "Update artboard/page properties (position, size, name, background color)", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Page ID to update"}, "x": {"type": "number", "description": "X position on canvas (px)"}, "y": {"type": "number", "description": "Y position on canvas (px)"}, "width": {"type": "number", "description": "Width in pixels"}, "height": {"type": "number", "description": "Height in pixels"}, "name": {"type": "string", "description": "Artboard name"}, "backgroundColor": {"type": "string", "description": "Background color (hex, e.g. #ffffff)"}}, "required": ["pageId"]}},
    {"name": "get_layout_diagnostics", "description": "Report likely layout issues such as overlap, clipping, text overflow, off-artboard nodes, zero-size nodes, and missing dimensions.", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Optional page ID."}, "nodeId": {"type": "string", "description": "Optional page or element ID."}, "includeOverlaps": {"type": "boolean", "description": "Include sibling overlap checks. Default true."}, "includeText": {"type": "boolean", "description": "Include text overflow heuristic. Default true."}}}},
    {"name": "get_overflow_report", "description": "Report nodes that overflow their parent or artboard, including overflow amounts per side.", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Optional page ID."}, "nodeId": {"type": "string", "description": "Optional page or element ID."}, "includeArtboard": {"type": "boolean", "description": "Include artboard boundary overflow checks. Default true."}, "includeParent": {"type": "boolean", "description": "Include parent boundary overflow checks. Default true."}, "minOverflow": {"type": "number", "description": "Minimum pixel overflow to report. Default 1."}}}},
    {"name": "get_svg_summary", "description": "Summarize SVG elements and primitives for text-only inspection of charts, diagrams, and icons.", "inputSchema": {"type": "object", "properties": {"pageId": {"type": "string", "description": "Optional page ID."}, "nodeId": {"type": "string", "description": "Optional page or element ID."}, "maxItems": {"type": "number", "description": "Maximum number of detailed items per SVG. Default 50."}}}},
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
  // Horizontal layout: each artboard placed to the right of the previous
  create_artboard({pageId: "hero", name:"Hero Section", width:1440, height:600, x:0, y:0})
  write_html({pageId: "hero", html: "<div>Hero content</div>"})
  create_artboard({pageId: "features", name:"Features", width:1440, height:400, x:0, y:620})
  write_html({pageId: "features", html: "<div>Features content</div>"})

  // Grid layout: specify x/y explicitly for each artboard
  create_artboard({pageId: "mobile-home", name:"Mobile Home", width:375, height:812, x:0, y:0})
  create_artboard({pageId: "mobile-settings", name:"Mobile Settings", width:375, height:812, x:395, y:0})
  create_artboard({pageId: "mobile-profile", name:"Mobile Profile", width:375, height:812, x:790, y:0})

  delete_artboard({pageId: "mobile-settings"}) → removes unwanted artboards

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


@app.post("/api/documents/{doc_id}/export-artboards")
async def api_export_artboards(doc_id: str, body: dict):
    directory = body.get("directory", "")
    if not directory:
        return JSONResponse({"error": "directory is required"}, status_code=400)
    return doc_store.export_artboards(doc_id, directory)


@app.post("/api/documents/{doc_id}/screenshot")
async def api_set_screenshot(doc_id: str, data: dict):
    doc_store.set_screenshot_data(doc_id, data if isinstance(data, dict) else {"data": data})
    return {"success": True}


@app.get("/health")
async def health():
    return {"status": "ok", "server": SERVER_NAME, "version": SERVER_VERSION}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3004)
