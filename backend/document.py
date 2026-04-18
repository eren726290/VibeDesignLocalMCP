"""
Document Store - Manages paper documents as HTML files
"""
import json
import uuid
import base64
from pathlib import Path
from typing import Optional
import os

DATA_DIR = Path.home() / ".paper_clone" / "data"
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
    x: int = 0
    y: int = 0
    width: int = 375
    height: int = 812
    backgroundColor: Optional[str] = "#ffffff"
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
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Load any existing documents from disk
        self._load_all()

    def _doc_file(self, doc_id: str) -> Path:
        return DATA_DIR / f"{doc_id}.json"

    def _load_all(self):
        """Load all documents from disk on startup"""
        for f in DATA_DIR.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                doc = Document.model_validate(data)
                self.documents[doc.id] = doc
            except Exception:
                pass  # Skip corrupted files

    def _save(self, doc_id: str):
        """Persist document to disk after every mutation"""
        doc = self.documents.get(doc_id)
        if not doc:
            return
        try:
            self._doc_file(doc_id).write_text(
                doc.model_dump_json(indent=2), encoding="utf-8"
            )
        except Exception:
            pass  # Non-fatal: continue even if disk write fails

    def new_document(self, doc_id: str = None) -> dict:
        """Create a new blank document"""
        if doc_id is None:
            doc_id = "default"
        # If doc already exists, return it
        existing = self.documents.get(doc_id)
        if existing:
            return self._doc_to_response(existing)
        # Start with no pages — AI must create artboards
        doc = Document(
            id=doc_id,
            title="Untitled",
            pages=[],
            current_page=0,
        )
        self.documents[doc_id] = doc
        self._save(doc_id)
        return self._doc_to_response(doc)

    def get_document(self, doc_id: str) -> dict:
        """Get document by ID — source of truth is in-memory."""
        doc = self.documents.get(doc_id)
        if not doc:
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
        self._save(doc_id)
        return self._doc_to_response(doc)

    def create_element(self, doc_id: str, element: dict, page_id: Optional[str] = None) -> dict:
        """Create a new element on the current page or a specific page."""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        if page_id:
            target_page = next((p for p in doc.pages if p.id == page_id), None)
            if not target_page:
                return {"error": f"Page '{page_id}' not found"}
        else:
            target_page = doc.pages[doc.current_page]

        if "id" not in element:
            element["id"] = f"n-{str(uuid.uuid4())[:8]}"

        target_page.elements.append(element)
        self._save(doc_id)
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
        if "x" not in page:
            page["x"] = 0
        if "y" not in page:
            page["y"] = sum(p.height for p in doc.pages) + len(doc.pages) * 20
        if "width" not in page:
            page["width"] = 375
        if "height" not in page:
            page["height"] = 812
        if "elements" not in page:
            page["elements"] = []

        new_page = Page(
            id=page["id"],
            name=page["name"],
            x=page.get("x", 0),
            y=page.get("y", 0),
            width=page.get("width", 375),
            height=page.get("height", 812),
            elements=[],
        )
        doc.pages.append(new_page)
        self._save(doc_id)
        return {"success": True, "page": new_page.model_dump()}

    def update_page(self, doc_id: str, page_id: str, updates: dict) -> dict:
        """Update artboard/page properties (x, y, width, height, name, backgroundColor)"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}
        for i, p in enumerate(doc.pages):
            if p.id == page_id:
                p_dict = p.model_dump()
                for key in ("x", "y", "width", "height", "name", "backgroundColor"):
                    if key in updates:
                        p_dict[key] = updates[key]
                doc.pages[i] = Page.model_validate(p_dict)
                self._save(doc_id)
                return {"success": True}
        return {"error": f"Page '{page_id}' not found"}

    def delete_page(self, doc_id: str, page_id: str) -> dict:
        """Delete a page/artboard"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        idx = None
        for i, p in enumerate(doc.pages):
            if p.id == page_id:
                idx = i
                break
        if idx is None:
            return {"error": f"Page '{page_id}' not found"}

        if len(doc.pages) == 1:
            return {"error": "Cannot delete the last page"}

        doc.pages.pop(idx)
        # Adjust current_page if needed
        if doc.current_page >= len(doc.pages):
            doc.current_page = len(doc.pages) - 1
        elif doc.current_page > idx:
            doc.current_page -= 1

        self._save(doc_id)
        return {"success": True}

    def update_element(self, doc_id: str, element_id: str, updates: dict) -> dict:
        """Update an element"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        for page in doc.pages:
            for i, el in enumerate(page.elements):
                if el.get("id") == element_id:
                    page.elements[i] = {**el, **updates}
                    self._save(doc_id)
                    return {"success": True, "element": page.elements[i]}

        return {"error": "Element not found"}

    def delete_element(self, doc_id: str, element_id: str) -> dict:
        """Delete an element from any page"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}
        for page in doc.pages:
            found = any(el.get("id") == element_id for el in page.elements)
            if found:
                page.elements = [el for el in page.elements if el.get("id") != element_id]
                self._save(doc_id)
                return {"success": True}
        return {"error": "Element not found"}

    def duplicate_element(self, doc_id: str, element_id: str) -> dict:
        """Duplicate an element"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        for page in doc.pages:
            for el in page.elements:
                if el.get("id") == element_id:
                    new_el = {**el, "id": f"n-{str(uuid.uuid4())[:8]}"}
                    if "style" in new_el:
                        style = dict(new_el["style"])
                        if "left" in style:
                            style["left"] = f"{float(style['left'].replace('px','')) + 20}px"
                        if "top" in style:
                            style["top"] = f"{float(style['top'].replace('px','')) + 20}px"
                        new_el["style"] = style
                    page.elements.append(new_el)
                    self._save(doc_id)
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
                    "x": p.x,
                    "y": p.y,
                    "width": p.width,
                    "height": p.height,
                    "backgroundColor": p.backgroundColor,
                    "elements": p.elements,
                }
                for p in doc.pages
            ],
            "current_page": doc.current_page,
            "file_path": doc.file_path,
        }

    def export_artboards(self, doc_id: str, directory: str) -> dict:
        """Export each artboard as a separate HTML file to the target directory.

        Args:
            doc_id: Document ID
            directory: Target directory path

        Returns:
            dict with success status and list of exported files
        """
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        import re
        import os as _os

        dir_path = Path(directory)
        if not dir_path.exists():
            return {"error": f"Directory does not exist: {directory}"}

        exported = []
        for page in doc.pages:
            # Sanitize filename from artboard name
            safe_name = re.sub(r'[^\w\-]', '_', page.name)
            if not safe_name.strip('_'):
                safe_name = "artboard"
            filename = f"{safe_name}.html"
            filepath = dir_path / filename

            # Generate HTML for this single artboard
            html = self._generate_single_page_html(doc, page)
            filepath.write_text(html, encoding="utf-8")
            exported.append(filename)

        return {"success": True, "exported": exported, "directory": directory}

    def _generate_single_page_html(self, doc: Document, page: Page) -> str:
        """Generate HTML for a single artboard/page."""
        def render_element(el: dict, indent: str) -> str:
            style_str = "; ".join(f"{k}: {v}" for k, v in el.get("style", {}).items())
            content = el.get("text", "") or ""
            tag = el.get("tag", "div")
            el_id = el.get("id", "")
            children_ids = el.get("children", [])

            # Build children map from current page
            children_map = {e["id"]: e for e in page.elements}
            children_html = ""
            for cid in children_ids:
                child = children_map.get(cid)
                if child:
                    children_html += render_element(child, indent + "  ")

            inner = content + children_html
            return f'{indent}<{tag} data-paper-node="{el_id}" style="{style_str}">{inner}</{tag}>\n'

        # Root elements (no parentId)
        roots = [el for el in page.elements if not el.get("parentId")]
        elements_html = "".join(render_element(el, "  ") for el in roots)

        # Background div wrapping all elements
        bg_div = f"""<div style="width: {page.width}px; height: {page.height}px; background: {page.backgroundColor or '#ffffff'}; position: relative; overflow: hidden;">
  {elements_html}</div>"""

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{page.name}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: #f0f0f0;
      min-height: 100vh;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding: 40px;
    }}
  </style>
</head>
<body>
{bg_div}
</body>
</html>"""

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
            pages_html += f'{indent}     style="width: {page.width}px; height: {page.height}px; position: absolute; left: {page.x}px; top: {page.y}px; background: {page.backgroundColor or "#ffffff"};">{nl}'
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
