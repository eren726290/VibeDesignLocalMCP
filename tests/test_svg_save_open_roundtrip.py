"""
SVG Paper HTML save/open round-trip regression test.

Ensures that SVG/XML attributes survive _generate_html() -> _parse_html()
without loss (Task 42 fix regression coverage).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from document import DocumentStore, Document, Page


def test_svg_save_open_roundtrip():
    store = DocumentStore()

    # Build 7 elements in 1 page: SVG root + 5 SVG descendants + 1 non-SVG div.
    elements = [
        # --- SVG root ---
        {
            "id": "n-svg-root",
            "name": "Svg Element",
            "tag": "svg",
            "type": "svg",
            "style": {
                "id": "my-svg",
                "viewBox": "0 0 200 200",
                "width": "200",
                "height": "200",
            },
            "text": None,
            "children": ["n-grad", "n-clip", "n-rect", "n-path", "n-tp"],
        },
        # --- Descendants (lowercase tags, matching BeautifulSoup output) ---
        {
            "id": "n-grad",
            "name": "Lineargradient Element",
            "tag": "lineargradient",
            "type": "svg-gradient",
            "style": {
                "id": "my-grad",
                "gradientUnits": "userSpaceOnUse",
                "stopColor": "#ff0000",
            },
            "text": None,
            "children": [],
            "parentId": "n-svg-root",
        },
        {
            "id": "n-clip",
            "name": "Clippath Element",
            "tag": "clippath",
            "type": "svg-clip-path",
            "style": {
                "id": "my-clip",
                "clipPathUnits": "userSpaceOnUse",
            },
            "text": None,
            "children": [],
            "parentId": "n-svg-root",
        },
        {
            "id": "n-rect",
            "name": "Rect Element",
            "tag": "rect",
            "type": "svg-rect",
            "style": {
                "fill": "url(#my-grad)",
                "clipPath": "url(#my-clip)",
                "strokeWidth": "2",
            },
            "text": None,
            "children": [],
            "parentId": "n-svg-root",
        },
        {
            "id": "n-path",
            "name": "Path Element",
            "tag": "path",
            "type": "svg-path",
            "style": {
                "d": "M10 10 L190 10",
            },
            "text": None,
            "children": [],
            "parentId": "n-svg-root",
        },
        {
            "id": "n-tp",
            "name": "Textpath Element",
            "tag": "textpath",
            "type": "svg-text",
            "style": {
                "href": "#my-path",
                "startOffset": "50%",
            },
            "text": None,
            "children": [],
            "parentId": "n-svg-root",
        },
        # --- Non-SVG (proves native id + CSS survive) ---
        {
            "id": "n-div",
            "name": "Div Element",
            "tag": "div",
            "type": "div",
            "style": {
                "id": "my-div",
                "backgroundColor": "#00ff00",
            },
            "text": None,
            "children": [],
        },
    ]

    page = Page(
        id="page-test",
        name="Test SVG Page",
        width=1440,
        height=900,
        backgroundColor="#ffffff",
        elements=elements,
    )
    doc = Document(id="test-doc", title="SVG Round-trip Test", pages=[page])

    # Round-trip
    html = store._generate_html(doc)
    reopened = store._parse_html(html, "test.html")

    # ---- Assertions ----
    assert len(reopened.pages) == 1, "Expected 1 page after round-trip"
    rp = reopened.pages[0]

    el_by_id = {el["id"]: el for el in rp.elements}

    # ---------- SVG root ----------
    svg = el_by_id.get("n-svg-root")
    assert svg is not None, "SVG root node missing after round-trip"
    assert svg["tag"] == "svg", f"Expected 'svg', got '{svg['tag']}'"
    assert svg["style"].get("id") == "my-svg", \
        f"SVG native id: expected 'my-svg', got '{svg['style'].get('id')}'"
    assert svg["style"].get("viewBox") == "0 0 200 200", \
        f"viewBox: expected '0 0 200 200', got '{svg['style'].get('viewBox')}'"
    assert svg["style"].get("width") == "200", \
        f"SVG width: expected '200', got '{svg['style'].get('width')}'"
    assert svg["style"].get("height") == "200", \
        f"SVG height: expected '200', got '{svg['style'].get('height')}'"
    assert "parentId" not in svg, "SVG root should be page root"

    # ---------- linearGradient (internal tag: lineargradient) ----------
    grad = el_by_id.get("n-grad")
    assert grad is not None, "linearGradient node missing"
    assert grad["tag"] == "lineargradient", f"Expected 'lineargradient', got '{grad['tag']}'"
    assert grad["style"].get("id") == "my-grad", \
        f"gradient id: expected 'my-grad', got '{grad['style'].get('id')}'"
    assert grad["style"].get("gradientUnits") == "userSpaceOnUse", \
        f"gradientUnits: expected 'userSpaceOnUse', got '{grad['style'].get('gradientUnits')}'"
    assert grad["style"].get("stopColor") == "#ff0000", \
        f"stopColor: expected '#ff0000', got '{grad['style'].get('stopColor')}'"
    assert grad.get("parentId") == "n-svg-root", \
        f"gradient parentId: expected 'n-svg-root', got '{grad.get('parentId')}'"

    # ---------- clipPath (internal tag: clippath) ----------
    clip = el_by_id.get("n-clip")
    assert clip is not None, "clipPath node missing"
    assert clip["tag"] == "clippath", f"Expected 'clippath', got '{clip['tag']}'"
    assert clip["style"].get("id") == "my-clip", \
        f"clipPath id: expected 'my-clip', got '{clip['style'].get('id')}'"
    assert clip["style"].get("clipPathUnits") == "userSpaceOnUse", \
        f"clipPathUnits: expected 'userSpaceOnUse', got '{clip['style'].get('clipPathUnits')}'"
    assert clip.get("parentId") == "n-svg-root", \
        f"clipPath parentId: expected 'n-svg-root', got '{clip.get('parentId')}'"

    # ---------- rect ----------
    rect = el_by_id.get("n-rect")
    assert rect is not None, "rect node missing"
    assert rect["tag"] == "rect", f"Expected 'rect', got '{rect['tag']}'"
    assert rect["style"].get("fill") == "url(#my-grad)", \
        f"rect fill: expected 'url(#my-grad)', got '{rect['style'].get('fill')}'"
    assert rect["style"].get("clipPath") == "url(#my-clip)", \
        f"rect clipPath: expected 'url(#my-clip)', got '{rect['style'].get('clipPath')}'"
    assert rect["style"].get("strokeWidth") == "2", \
        f"rect strokeWidth: expected '2', got '{rect['style'].get('strokeWidth')}'"
    assert rect.get("parentId") == "n-svg-root", \
        f"rect parentId: expected 'n-svg-root', got '{rect.get('parentId')}'"

    # ---------- path ----------
    path = el_by_id.get("n-path")
    assert path is not None, "path node missing"
    assert path["tag"] == "path", f"Expected 'path', got '{path['tag']}'"
    assert path["style"].get("d") == "M10 10 L190 10", \
        f"path d: expected 'M10 10 L190 10', got '{path['style'].get('d')}'"
    assert path.get("parentId") == "n-svg-root", \
        f"path parentId: expected 'n-svg-root', got '{path.get('parentId')}'"

    # ---------- textPath (internal tag: textpath) ----------
    tp = el_by_id.get("n-tp")
    assert tp is not None, "textPath node missing"
    assert tp["tag"] == "textpath", f"Expected 'textpath', got '{tp['tag']}'"
    assert tp["style"].get("href") == "#my-path", \
        f"textPath href: expected '#my-path', got '{tp['style'].get('href')}'"
    assert tp["style"].get("startOffset") == "50%", \
        f"textPath startOffset: expected '50%', got '{tp['style'].get('startOffset')}'"
    assert tp.get("parentId") == "n-svg-root", \
        f"textPath parentId: expected 'n-svg-root', got '{tp.get('parentId')}'"

    # ---------- Parent / child structure ----------
    assert svg["children"] == ["n-grad", "n-clip", "n-rect", "n-path", "n-tp"], \
        f"SVG children: expected 5 items, got {svg['children']}"

    # ---------- Non-SVG div ----------
    div = el_by_id.get("n-div")
    assert div is not None, "Non-SVG div node missing"
    assert div["tag"] == "div", f"Expected 'div', got '{div['tag']}'"
    assert div["style"].get("id") == "my-div", \
        f"div native id: expected 'my-div', got '{div['style'].get('id')}'"
    assert div["style"].get("backgroundColor") == "#00ff00", \
        f"div backgroundColor: expected '#00ff00', got '{div['style'].get('backgroundColor')}'"
    assert "parentId" not in div, "Non-SVG root should be page root"

    print("All SVG Paper HTML save/open regression checks passed.")


if __name__ == "__main__":
    test_svg_save_open_roundtrip()
