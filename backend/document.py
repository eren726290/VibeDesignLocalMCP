"""
Document Store - Manages paper documents as HTML files
"""
import json
import uuid
import base64
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class Element(BaseModel):
    id: str
    name: str
    tag: str = "div"
    type: str = "rectangle"
    style: dict
    children: list = []
    text: Optional[str] = None


class Page(BaseModel):
    id: str
    name: str
    width: int = 375
    height: int = 812
    elements: list[dict] = []


class Document(BaseModel):
    id: str
    title: str
    pages: list[Page]
    current_page: int = 0
    file_path: Optional[str] = None


class DocumentStore:
    def __init__(self):
        self.documents: dict[str, Document] = {}
        self._screenshot_data: dict[str, str] = {}

    def new_document(self, doc_id: str = None) -> dict:
        """Create a new blank document"""
        if doc_id is None:
            doc_id = "default"
        # If doc already exists, return it
        existing = self.documents.get(doc_id)
        if existing:
            return self._doc_to_response(existing)
        page = Page(id="page-1", name="Page 1")
        doc = Document(
            id=doc_id,
            title="Untitled",
            pages=[page],
            current_page=0,
        )
        self.documents[doc_id] = doc
        return self._doc_to_response(doc)

    def get_document(self, doc_id: str) -> dict:
        """Get document by ID"""
        doc = self.documents.get(doc_id)
        if not doc:
            # Auto-create if not found
            return self.new_document()
        return self._doc_to_response(doc)

    def save_document(self, doc_id: str, file_path: str = None) -> dict:
        """Save document to HTML file"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        if file_path:
            doc.file_path = file_path

        html = self._generate_html(doc)

        if doc.file_path:
            Path(doc.file_path).write_text(html, encoding="utf-8")

        return {"success": True, "file_path": doc.file_path, "html": html}

    def open_document(self, doc_id: str, file_path: str) -> dict:
        """Open document from HTML file"""
        path = Path(file_path)
        if not path.exists():
            return {"error": "File not found"}

        content = path.read_text(encoding="utf-8")
        doc = self._parse_html(content, file_path)

        if not doc_id:
            doc_id = str(uuid.uuid4())[:8]

        doc.id = doc_id
        self.documents[doc_id] = doc
        return self._doc_to_response(doc)

    def create_element(self, doc_id: str, element: dict) -> dict:
        """Create a new element"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        page = doc.pages[doc.current_page]

        # Generate ID if not provided
        if "id" not in element:
            element["id"] = f"n-{str(uuid.uuid4())[:8]}"

        page.elements.append(element)
        return {"success": True, "element": element}

    def create_page(self, doc_id: str, page: dict) -> dict:
        """Create a new page"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        if "id" not in page:
            page["id"] = f"page-{str(uuid.uuid4())[:8]}"
        if "name" not in page:
            page["name"] = f"Page {len(doc.pages) + 1}"
        if "width" not in page:
            page["width"] = 375
        if "height" not in page:
            page["height"] = 812
        if "elements" not in page:
            page["elements"] = []

        new_page = Page(
            id=page["id"],
            name=page["name"],
            width=page.get("width", 375),
            height=page.get("height", 812),
            elements=[],
        )
        doc.pages.append(new_page)
        return {"success": True, "page": new_page.model_dump()}

    def update_element(self, doc_id: str, element_id: str, updates: dict) -> dict:
        """Update an element"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        page = doc.pages[doc.current_page]

        for i, el in enumerate(page.elements):
            if el.get("id") == element_id:
                page.elements[i] = {**el, **updates}
                return {"success": True, "element": page.elements[i]}

        return {"error": "Element not found"}

    def delete_element(self, doc_id: str, element_id: str) -> dict:
        """Delete an element"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        page = doc.pages[doc.current_page]
        page.elements = [el for el in page.elements if el.get("id") != element_id]
        return {"success": True}

    def duplicate_element(self, doc_id: str, element_id: str) -> dict:
        """Duplicate an element"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        page = doc.pages[doc.current_page]

        for el in page.elements:
            if el.get("id") == element_id:
                new_el = {**el, "id": f"n-{str(uuid.uuid4())[:8]}"}
                # Offset position slightly
                if "style" in new_el:
                    style = dict(new_el["style"])
                    if "left" in style:
                        style["left"] = f"{float(style['left'].replace('px','')) + 20}px"
                    if "top" in style:
                        style["top"] = f"{float(style['top'].replace('px','')) + 20}px"
                    new_el["style"] = style
                page.elements.append(new_el)
                return {"success": True, "element": new_el}

        return {"error": "Element not found"}

    def export_html(self, doc_id: str, pretty: bool = True) -> dict:
        """Export document as HTML"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        html = self._generate_html(doc, pretty=pretty)
        return {"success": True, "html": html}

    def set_screenshot_data(self, doc_id: str, data: str):
        """Store screenshot data from frontend"""
        self._screenshot_data[doc_id] = data

    def get_screenshot_data(self, doc_id: str) -> dict:
        """Get screenshot data for MCP"""
        data = self._screenshot_data.get(doc_id, "")
        return {"data": data}

    def _doc_to_response(self, doc: Document) -> dict:
        """Convert document to API response"""
        return {
            "id": doc.id,
            "title": doc.title,
            "pages": [
                {
                    "id": p.id,
                    "name": p.name,
                    "width": p.width,
                    "height": p.height,
                    "elements": p.elements,
                }
                for p in doc.pages
            ],
            "current_page": doc.current_page,
            "file_path": doc.file_path,
        }

    def _generate_html(self, doc: Document, pretty: bool = False) -> str:
        """Generate HTML file from document"""
        indent = "  " if pretty else ""
        nl = "\n" if pretty else ""

        def render_element(el: dict, el_indent: str) -> str:
            """Recursively render element and its children as nested HTML"""
            style_str = "; ".join(f"{k}: {v}" for k, v in el.get("style", {}).items())
            content = el.get("text", "") or ""
            tag = el.get("tag", "div")
            el_id = el.get("id", "")
            children_ids = el.get("children", [])

            # Render children first
            children_map = {e["id"]: e for e in doc.pages[doc.current_page].elements}
            children_html = ""
            for cid in children_ids:
                child = children_map.get(cid)
                if child:
                    children_html += render_element(child, el_indent + indent)

            inner = content + children_html
            return f'{el_indent}<{tag} data-paper-node="{el_id}" style="{style_str}">{inner}</{tag}>{nl}'

        pages_html = ""
        for i, page in enumerate(doc.pages):
            # Find root elements (no parentId)
            roots = [el for el in page.elements if not el.get("parentId")]
            elements_html = "".join(render_element(el, indent) for el in roots)

            pages_html += f'{indent}<div data-paper-page="{i}" data-paper-name="{page.name}"{nl}'
            pages_html += f'{indent}     style="width: {page.width}px; height: {page.height}px; position: absolute; left: {100 + i * (page.width + 100)}px; top: 100px; background: white;">{nl}'
            pages_html += elements_html
            pages_html += f'{indent}</div>{nl}'

        return f"""<!DOCTYPE html>
<html data-paper-file="true" data-paper-version="1.0">
<head>
  <meta charset="UTF-8">
  <meta name="paper:title" content="{doc.title}">
  <meta name="paper:pages" content="{len(doc.pages)}">
  <meta name="paper:current-page" content="{doc.current_page}">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #f0f0f0; min-height: 100vh; }}
  </style>
</head>
<body>
{pages_html}
</body>
</html>"""

    def _element_to_html(self, el: dict, indent: str, nl: str) -> str:
        """Convert element to HTML string"""
        style_str = "; ".join(f"{k}: {v}" for k, v in el.get("style", {}).items())
        content = el.get("text", "") or ""
        tag = el.get("tag", "div")
        el_id = el.get("id", "")

        inner = content
        if tag != "div" and content:
            inner = content

        return f'{indent}  <{tag} data-paper-node="{el_id}" style="{style_str}">{inner}</{tag}>{nl}'

    def _parse_html(self, content: str, file_path: str) -> Document:
        """Parse HTML file into document"""
        doc_id = str(uuid.uuid4())[:8]
        title = "Untitled"

        # Extract pages from HTML
        import re
        page_pattern = r'<div data-paper-page="(\d+)"[^>]*data-paper-name="([^"]*)"[^>]*style="([^"]*)"'
        pages = []

        # Simple page extraction
        page_divs = re.findall(r'<div data-paper-page="(\d+)"[^>]*>', content)

        for i, page_match in enumerate(re.finditer(r'<div data-paper-page="(\d+)"[^>]*>', content)):
            page_idx = int(page_match.group(1))

            # Find matching closing tag
            start = page_match.end()
            depth = 1
            pos = start
            while depth > 0 and pos < len(content):
                if content[pos:pos+4] == "<div":
                    depth += 1
                elif content[pos:pos+6] == "</div>":
                    depth -= 1
                pos += 1

            page_html = content[start:pos]

            # Extract elements
            elements = []
            element_pattern = r'<(\w+)\s+data-paper-node="([^"]*)"[^>]*>([^<]*)</\w+>'
            for el_match in re.finditer(element_pattern, page_html):
                tag = el_match.group(1)
                el_id = el_match.group(2)
                text = el_match.group(3).strip()

                # Find style
                style_pattern = rf'<{tag}\s+[^>]*style="([^"]*)"'
                style_match = re.search(style_pattern, page_html[el_match.start():el_match.start()+200])
                style = {}
                if style_match:
                    for item in style_match.group(1).split(";"):
                        if ":" in item:
                            k, v = item.split(":", 1)
                            k = k.strip()
                            v = v.strip()
                            # Convert kebab-case to camelCase (and handle special props)
                            _spec = {"background": "backgroundColor", "background-color": "backgroundColor", "font-size": "fontSize", "border-radius": "borderRadius", "line-height": "lineHeight"}
                            if k in _spec:
                                k = _spec[k]
                            elif "-" in k:
                                parts = k.split("-")
                                k = parts[0] + "".join(p.capitalize() for p in parts[1:])
                            style[k] = v

                # Infer type from style
                el_type = "rectangle"
                if text:
                    el_type = "text"
                elif "fontSize" in style:
                    el_type = "text"
                elif (style.get("backgroundColor") or style.get("background", "")) not in ("", "transparent", "none"):
                    el_type = "rectangle"
                elif float(style.get("width", "0")) > 200 and float(style.get("height", "0")) > 100:
                    el_type = "frame"

                elements.append({
                    "id": el_id,
                    "tag": tag,
                    "type": el_type,
                    "style": style,
                    "text": text or None,
                    "children": [],
                })

            pages.append(Page(
                id=f"page-{page_idx}",
                name=f"Page {page_idx + 1}",
                elements=elements,
            ))

        if not pages:
            pages.append(Page(id="page-1", name="Page 1"))

        return Document(
            id=doc_id,
            title=title,
            pages=pages,
            current_page=0,
            file_path=file_path,
        )
