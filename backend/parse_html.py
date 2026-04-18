"""
HTML parsing utilities for Paper Clone.
Extracts element trees from HTML strings using BeautifulSoup.
"""
from bs4 import BeautifulSoup, Comment
import uuid


def _parse_style(style_str: str) -> dict:
    """Parse a CSS style string into a camelCase key→value dict (React-compatible)."""
    style = {}
    if not style_str:
        return style
    for item in style_str.split(";"):
        item = item.strip()
        if ":" in item:
            k, v = item.split(":", 1)
            k = k.strip()
            v = v.strip()
            # Convert kebab-case to camelCase for React style props
            parts = k.split("-")
            camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
            # Ensure numeric lengths have px units (React CSSProperties needs them).
            # Only for length/percentage properties that AI sometimes writes without px.
            # Unitless properties (zIndex, opacity, flexGrow, flexShrink, flex, etc.) must stay unitless.
            if camel in ("width", "height", "top", "left", "right", "bottom",
                         "marginTop", "marginRight", "marginBottom", "marginLeft",
                         "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
                         "borderRadius", "borderWidth", "fontSize", "lineHeight",
                         "flexBasis", "gap") \
               and v and v.lstrip("-").isdigit():
                v = f"{v}px"
            style[camel] = v
    return style


def _collect_attrs(attrs: dict) -> dict:
    """
    Merge CSS style + SVG presentation attributes into a single style dict.
    SVG attributes like fill, stroke, r, cx, cy, d, viewBox live in tag.attrs,
    not in the style attribute — we need to capture them too.
    """
    style = _parse_style(attrs.get("style", ""))

    # SVG presentation attributes — treat them as style keys so they reach React/SVG rendering
    svg_attrs = [
        # Shape-specific
        "fill", "fillRule", "fillOpacity", "floodOpacity",
        "stroke", "strokeWidth", "strokeLinecap", "strokeLinejoin",
        "strokeDasharray", "strokeOpacity", "strokeMiterlimit", "strokeDashoffset",
        "opacity", "clipPath", "clipRule",
        # Geometry
        "r", "rx", "ry", "cx", "cy", "x", "y", "x1", "y1", "x2", "y2",
        "width", "height",
        # Path & text
        "d", "points", "pathLength",
        # SVG container
        "viewBox", "preserveAspectRatio", "xmlns",
        # Text
        "textAnchor", "dominantBaseline", "fontFamily", "fontSize", "fontWeight",
        "letterSpacing", "textDecoration", "fontStyle", "fontVariant",
        # Gradient & filter
        "offset", "stopColor", "stopOpacity",
        "gradientUnits", "spreadMethod", "gradientTransform",
        "patternUnits", "patternContentUnits",
        "clipPathUnits", "maskUnits", "maskContentUnits",
        # Transform & links
        "transform", "href", "xlinkHref",
    ]
    def _camel_to_kebab(s: str) -> str:
        """Convert camelCase to kebab-case."""
        import re
        return re.sub(r'([A-Z])', r'-\1', s).lower()

    for attr in svg_attrs:
        # BeautifulSoup html.parser lowercases attribute names and converts
        # camelCase SVG attrs to kebab-case (viewBox→viewbox, stopColor→stop-color)
        # Also preserve original camelCase as-is.
        key_lower = attr.lower()
        key_kebab = _camel_to_kebab(attr)
        if key_lower in attrs:
            style[attr] = attrs[key_lower]
        elif key_kebab in attrs:
            style[attr] = attrs[key_kebab]
        elif attr in attrs:
            style[attr] = attrs[attr]
        # Handle namespaced attrs (xlink:href stored as 'xlink:href' by BeautifulSoup)
        if attr == 'xlinkHref' and 'xlink:href' in attrs:
            style['xlinkHref'] = attrs['xlink:href']

    return style


def _infer_type(tag: str, style: dict, text: str) -> str:
    """Infer element type from tag name, style, and text content."""
    if tag == "img":
        return "image"
    if tag == "video":
        return "video"
    if tag == "audio":
        return "audio"
    if tag == "canvas":
        return "canvas"
    if tag == "input":
        return "input"
    if tag == "textarea":
        return "text"
    if tag == "select":
        return "select"
    if tag == "button":
        return "button"
    if tag == "a":
        return "link"
    if tag == "span":
        return "text"
    if tag == "p":
        return "text"
    if tag == "h1":
        return "heading"
    if tag == "h2":
        return "heading"
    if tag == "h3":
        return "heading"
    if tag == "h4":
        return "heading"
    if tag == "h5":
        return "heading"
    if tag == "h6":
        return "heading"
    if tag == "ul":
        return "list"
    if tag == "ol":
        return "list"
    if tag == "li":
        return "list-item"
    if tag == "table":
        return "table"
    if tag == "svg":
        return "svg"
    if text:
        return "text"
    return "div"


def _collect_tags(tag, out_list):
    """Recursively collect all Tag descendants in document order."""
    out_list.append(tag)
    for child in tag.find_all(recursive=False):
        _collect_tags(child, out_list)


def parse_html_elements(html: str) -> list[dict]:
    """
    Parse an HTML string and return a flat list of element dicts with parentId references.

    Uses find_all() to reliably walk the tree in document order, avoiding the
    inconsistent results that .contents/.children can produce with some BeautifulSoup
    parsers and HTML structures.

    The outermost element's position/box-model styles are stripped so it fills the
    artboard naturally — just like an HTML file filling the browser window.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Collect all tags in document order
    all_tags = []
    for tag in soup.find_all(recursive=False):
        _collect_tags(tag, all_tags)

    elements = []
    # Map from Python id(Tag) → our element id
    bs_to_el_id = {}
    # Track whether this is the outermost element (first in document order)
    is_first = True

    for tag in all_tags:
        attrs = dict(tag.attrs)
        style = _collect_attrs(attrs)

        # The outermost element fills the artboard naturally.
        # Strip any layout props that would override natural flow — the artboard
        # provides the viewport dimensions (375×812 etc.). The frontend sets
        # width:100% for the root, so width/height from AI are redundant.
        # Exception: SVG elements need width/height for their display size,
        # and use viewBox for the internal coordinate system.
        if is_first:
            is_first = False
            strip_keys = ["position", "left", "top", "right", "bottom"]
            if tag.name != "svg":
                strip_keys.extend(["width", "height"])
            for key in strip_keys:
                style.pop(key, None)
            # Ensure it doesn't overflow the artboard
            style["overflow"] = style.get("overflow", "hidden")

        # Text: only from direct string children (not all descendants via get_text()).
        # Filter out Comment objects — they're subclasses of str in bs4.
        direct_strings = [s for s in tag.contents if isinstance(s, str) and not isinstance(s, Comment)]
        text = "".join(direct_strings).strip() or None

        el_id = f"n-{str(uuid.uuid4())[:8]}"
        if "id" in attrs and attrs["id"]:
            el_id = attrs["id"]

        # Resolve parent from BeautifulSoup parent pointer
        parent_id = None
        if tag.parent and hasattr(tag.parent, "name") and tag.parent.name not in (None, "[document]"):
            parent_id = bs_to_el_id.get(id(tag.parent))

        el = {
            "id": el_id,
            "name": f"{tag.name.capitalize()} Element",
            "tag": tag.name,
            "type": _infer_type(tag.name, style, text or ""),
            "style": style,
            "text": text,
            "children": [],
        }
        if parent_id:
            el["parentId"] = parent_id

        elements.append(el)
        bs_to_el_id[id(tag)] = el_id

    return elements
