"""
Document Store - Manages paper documents as HTML files
"""
import html
import json
import uuid
import base64
import copy
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
        self._screenshot_data: dict[str, dict] = {}
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

    @staticmethod
    def _collect_descendant_ids(elements_by_id: dict, parent_id: str) -> set:
        """Collect all descendant element IDs of a given parent (recursive)."""
        ids = set()
        parent = elements_by_id.get(parent_id)
        if not parent:
            return ids
        for child_id in parent.get("children", []):
            ids.add(child_id)
            ids |= DocumentStore._collect_descendant_ids(elements_by_id, child_id)
        return ids

    @staticmethod
    def _collect_subtree_ids_ordered(elements_by_id: dict, root_id: str) -> list:
        """Collect descendant IDs in DFS order following original child order.

        The root_id itself is NOT included; only descendants.
        """
        result = []
        root = elements_by_id.get(root_id)
        if not root:
            return result
        for child_id in root.get("children", []):
            result.append(child_id)
            result.extend(DocumentStore._collect_subtree_ids_ordered(elements_by_id, child_id))
        return result

    @staticmethod
    def _offset_root_style(style: dict, offset_x, offset_y) -> dict:
        """Apply (offset_x, offset_y) to root positional style keys only.

        Preserves the original format (int stays int, '12px' stays '12px').
        Leaves unparseable values unchanged. Does not modify descendants.
        """
        new_style = dict(style)
        for key, offset in (("left", offset_x), ("top", offset_y),
                            ("x", offset_x), ("y", offset_y)):
            if key not in new_style:
                continue
            original = new_style[key]
            is_px = isinstance(original, str) and original.strip().endswith("px")
            s = str(original).strip()
            if s.endswith("px"):
                s = s[:-2].strip()
            try:
                parsed = float(s)
            except (ValueError, TypeError):
                continue
            new_value = parsed + offset
            if is_px:
                if float(new_value).is_integer():
                    new_style[key] = f"{int(new_value)}px"
                else:
                    new_style[key] = f"{new_value}px"
            elif isinstance(original, int) and float(new_value).is_integer():
                new_style[key] = int(new_value)
            else:
                new_style[key] = new_value
        return new_style

    def duplicate_subtree_batch(self, doc_id: str, node_ids, offset_x=20, offset_y=20) -> dict:
        """Duplicate full element subtrees and return per-root descendant ID maps.

        Args:
            doc_id: Document identifier.
            node_ids: List of element node IDs to duplicate. Non-empty list of strings.
            offset_x: Horizontal offset applied to cloned root's positional style only.
            offset_y: Vertical offset applied to cloned root's positional style only.

        Returns:
            {
              "success": bool,
              "duplicated": [
                {
                  "sourceNodeId": str,
                  "newNodeId": str,
                  "pageId": str,
                  "node": { ...new root element... },
                  "created": [ ...all new elements including root... ],
                  "createdIds": [ ...new IDs in DFS order... ],
                  "descendantIdMap": { oldId: newId, ... }  # includes root
                }
              ],
              "duplicatedCount": int,
              "errors": [ {"nodeId": str, "error": str} ]
            }

        Behavior:
            - Validates each node exists; missing ones are reported in errors and the
              batch continues with the rest.
            - Cross-page search; original element is never reparented off its page.
            - If a requested node is a descendant of another requested node, it is
              skipped silently (covered by the ancestor's clone).
            - Only element nodes are duplicated; page/artboard nodes are skipped with
              a clear error entry.
            - Cloned root inherits the original root's parent (or page-root status).
            - If the original root had a parent, the cloned root ID is appended to
              that original parent's children array (the only permitted mutation of
              an existing original node).
            - Page elements order: cloned subtree is inserted immediately after the
              original root for visual ordering.
        """
        if not isinstance(node_ids, list) or not node_ids:
            return {"success": False, "duplicated": [], "duplicatedCount": 0,
                    "errors": [{"error": "nodeIds must be a non-empty list"}]}

        doc = self.documents.get(doc_id)
        if not doc:
            return {"success": False, "duplicated": [], "duplicatedCount": 0,
                    "errors": [{"error": "Document not found"}]}

        # Build lookup structures and resolve requested ids
        id_to_page = {}     # node_id -> page
        id_to_el = {}       # node_id -> element dict
        child_to_parent = {}  # child_id -> parent_id, inferred from children arrays
        for page in doc.pages:
            for el in page.elements:
                el_id = el.get("id")
                if el_id:
                    id_to_page[el_id] = page
                    id_to_el[el_id] = el
                for cid in el.get("children", []) or []:
                    child_to_parent[cid] = el_id

        valid_ids = []
        errors = []
        for nid in node_ids:
            if not isinstance(nid, str) or not nid:
                errors.append({"nodeId": nid, "error": "nodeId must be a non-empty string"})
                continue
            if nid in id_to_el:
                # Reject if it's a page (page objects are in doc.pages, not page.elements)
                valid_ids.append(nid)
            else:
                # Check if it's a page ID (not allowed)
                is_page = any(p.id == nid for p in doc.pages)
                if is_page:
                    errors.append({"nodeId": nid, "error": f"Node '{nid}' is a page; only elements can be duplicated"})
                else:
                    errors.append({"nodeId": nid, "error": f"Node '{nid}' not found"})

        # Drop requested ids that are descendants of another requested id (silent skip)
        top_level_ids = []
        for nid in valid_ids:
            is_descendant = False
            for other in valid_ids:
                if other == nid:
                    continue
                descendants = self._collect_descendant_ids(id_to_el, other)
                if nid in descendants:
                    is_descendant = True
                    break
            if not is_descendant:
                top_level_ids.append(nid)

        duplicated_results = []

        for root_id in top_level_ids:
            page = id_to_page[root_id]
            original_root = id_to_el[root_id]
            elements_by_id = {el.get("id"): el for el in page.elements if el.get("id")}

            # DFS-ordered descendant list (root not included)
            descendant_ids = self._collect_subtree_ids_ordered(elements_by_id, root_id)
            subtree_ids = [root_id] + descendant_ids

            # Generate all new IDs upfront
            id_map = {}
            for old_id in subtree_ids:
                id_map[old_id] = f"n-{str(uuid.uuid4())[:8]}"

            # Clone each node
            created_elements = []
            for old_id in subtree_ids:
                original = id_to_el[old_id]
                clone = copy.deepcopy(original)
                clone["id"] = id_map[old_id]

                # Deep-copy style
                if "style" in clone and clone["style"] is not None:
                    clone["style"] = copy.deepcopy(clone["style"])
                    if old_id == root_id:
                        clone["style"] = self._offset_root_style(clone["style"], offset_x, offset_y)

                # Rewrite children references to cloned IDs
                new_children = []
                for cid in clone.get("children", []):
                    new_children.append(id_map.get(cid, cid))
                clone["children"] = new_children

                # Rewrite parentId
                old_parent = original.get("parentId")
                if old_parent is None and old_id != root_id:
                    # Fall back to inferred parent from children arrays
                    old_parent = child_to_parent.get(old_id)
                if old_id == root_id:
                    # Root: keep original parent (could be None for page root, or another element)
                    if old_parent:
                        clone["parentId"] = old_parent
                    else:
                        clone.pop("parentId", None)
                else:
                    # Descendant: parent is the cloned parent
                    clone["parentId"] = id_map.get(old_parent, old_parent)

                created_elements.append(clone)

            # Determine insertion position in page.elements (right after original root)
            original_root_index = None
            for i, el in enumerate(page.elements):
                if el.get("id") == root_id:
                    original_root_index = i
                    break

            if original_root_index is None:
                # Shouldn't happen, but be safe
                page.elements.extend(created_elements)
            else:
                # Insert in DFS order immediately after the original root
                # Find the end of the original subtree so we insert AFTER the whole original subtree
                original_subtree_ids = set(subtree_ids)
                end_index = original_root_index
                for i in range(original_root_index + 1, len(page.elements)):
                    el_id = page.elements[i].get("id")
                    # Walk up the parent chain to see if this element is a descendant of the root
                    cur = el_id
                    chain = set()
                    while cur and cur in elements_by_id and cur not in chain:
                        chain.add(cur)
                        cur = elements_by_id[cur].get("parentId")
                    if any(c in original_subtree_ids for c in chain):
                        end_index = i
                    else:
                        break
                page.elements = (page.elements[:end_index + 1] +
                                 created_elements +
                                 page.elements[end_index + 1:])

            # If root had a parent, append new root id to original parent's children
            old_parent = original_root.get("parentId")
            if old_parent is None:
                # Fall back to inferred parent from children arrays
                old_parent = child_to_parent.get(root_id)
            if old_parent:
                parent_el = id_to_el.get(old_parent)
                if parent_el is not None:
                    children = parent_el.get("children", [])
                    if id_map[root_id] not in children:
                        # Insert after root_id in the parent's children array
                        try:
                            idx = children.index(root_id)
                            parent_el["children"] = children[:idx + 1] + [id_map[root_id]] + children[idx + 1:]
                        except ValueError:
                            parent_el.setdefault("children", []).append(id_map[root_id])

            new_root_id = id_map[root_id]
            duplicated_results.append({
                "sourceNodeId": root_id,
                "newNodeId": new_root_id,
                "pageId": page.id,
                "node": created_elements[0],
                "created": created_elements,
                "createdIds": [e["id"] for e in created_elements],
                "descendantIdMap": id_map,
            })

        if duplicated_results:
            self._save(doc_id)

        return {
            "success": bool(duplicated_results),
            "duplicated": duplicated_results,
            "duplicatedCount": len(duplicated_results),
            "errors": errors,
        }

    def move_nodes(self, doc_id: str, node_ids, target_parent_id=None,
                   page_id=None, index=None) -> dict:
        """Move existing element nodes within a single page (reorder or reparent).

        - Reorder page-root nodes.
        - Reorder children under the same parent.
        - Reparent under another element (same page only).
        - Preserve whole subtrees by reference (no clone, no delete).
        - Prevent cycles: cannot move a node under itself or any descendant.
        - Same-page only; cross-page moves return an error and do not mutate.

        Args:
            doc_id: Document identifier.
            node_ids: List of element node IDs to move. Non-empty list of strings.
            target_parent_id: Optional page ID or element ID for the new parent.
            page_id: Optional page ID; constrains target_parent_id lookup to that page.
            index: Optional insertion index inside the target parent's `children`
                array (or page-root order). Omitted/invalid → append at end.

        Returns:
            {
              "success": bool,
              "pageId": str,
              "targetParentId": str | None,
              "moved": [
                {"nodeId", "oldParentId", "newParentId", "oldIndex", "newIndex"}
              ],
              "movedCount": int,
              "errors": [{"nodeId", "error"}]
            }
        """
        if not isinstance(node_ids, list) or not node_ids:
            return {"success": False, "moved": [], "movedCount": 0,
                    "errors": [{"error": "nodeIds must be a non-empty list"}]}
        if not target_parent_id and not page_id:
            return {"success": False, "moved": [], "movedCount": 0,
                    "errors": [{"error": "Either targetParentId or pageId must be provided"}]}

        doc = self.documents.get(doc_id)
        if not doc:
            return {"success": False, "moved": [], "movedCount": 0,
                    "errors": [{"error": "Document not found"}]}

        # Build lookup tables
        page_by_id = {p.id: p for p in doc.pages}
        id_to_page = {}
        id_to_el = {}
        for page in doc.pages:
            for el in page.elements:
                eid = el.get("id")
                if eid:
                    id_to_page[eid] = page
                    id_to_el[eid] = el

        # Resolve target_page (validate pageId first if given)
        target_page = None
        if page_id:
            if page_id not in page_by_id:
                return {"success": False, "moved": [], "movedCount": 0,
                        "errors": [{"error": f"Page '{page_id}' not found"}]}
            target_page = page_by_id[page_id]

        # Resolve target_parent_el with strict pageId constraint
        target_parent_el = None
        if target_parent_id:
            if target_page is not None:
                if target_parent_id == target_page.id:
                    # page-root target on the requested page
                    target_parent_el = None
                elif target_parent_id in page_by_id:
                    # Different page ID — not allowed when pageId is set
                    return {"success": False, "moved": [], "movedCount": 0,
                            "errors": [{"error": f"Target parent '{target_parent_id}' not found on page '{target_page.id}'"}]}
                else:
                    el = next((e for e in target_page.elements if e.get("id") == target_parent_id), None)
                    if el is None:
                        return {"success": False, "moved": [], "movedCount": 0,
                                "errors": [{"error": f"Target parent '{target_parent_id}' not found on page '{target_page.id}'"}]}
                    target_parent_el = el
            else:
                # No pageId: targetParentId can be any page ID or any element ID
                if target_parent_id in page_by_id:
                    target_page = page_by_id[target_parent_id]
                    target_parent_el = None
                else:
                    for p in doc.pages:
                        el = next((e for e in p.elements if e.get("id") == target_parent_id), None)
                        if el:
                            target_page = p
                            target_parent_el = el
                            break
                    if target_parent_el is None:
                        return {"success": False, "moved": [], "movedCount": 0,
                                "errors": [{"error": f"Target parent '{target_parent_id}' not found"}]}

        if target_page is None:
            return {"success": False, "moved": [], "movedCount": 0,
                    "errors": [{"error": "Target page could not be resolved"}]}

        # Coerce index (exclude bool, which subclasses int in Python)
        insert_index = None
        if isinstance(index, int) and not isinstance(index, bool) and index >= 0:
            insert_index = index

        # Collect valid sources + errors
        valid_sources = []
        errors = []
        seen = set()
        for nid in node_ids:
            if not isinstance(nid, str) or not nid:
                errors.append({"nodeId": nid, "error": "nodeId must be a non-empty string"})
                continue
            if nid in seen:
                continue  # silent dedup of duplicate IDs in input
            seen.add(nid)
            el = id_to_el.get(nid)
            if el is None:
                errors.append({"nodeId": nid, "error": f"Node '{nid}' not found"})
                continue
            if id_to_page[nid] is not target_page:
                return {"success": False, "moved": [], "movedCount": 0,
                        "errors": [{"error": "Cross-page moves are not supported"}]}
            valid_sources.append(el)

        if not valid_sources:
            return {"success": False, "moved": [], "movedCount": 0, "errors": errors}

        # Build target-page element map
        elements_by_id = {el.get("id"): el for el in target_page.elements if el.get("id")}

        # Filter ancestor + descendant (silent)
        top_level = []
        for el in valid_sources:
            eid = el.get("id")
            is_descendant = False
            for other in valid_sources:
                if other is el:
                    continue
                descendants = self._collect_descendant_ids(elements_by_id, other.get("id"))
                if eid in descendants:
                    is_descendant = True
                    break
            if not is_descendant:
                top_level.append(el)

        if not top_level:
            return {"success": False, "moved": [], "movedCount": 0, "errors": errors}

        # Cycle validation
        target_id = target_parent_el.get("id") if target_parent_el else target_page.id
        for el in top_level:
            eid = el.get("id")
            if eid == target_id:
                return {"success": False, "moved": [], "movedCount": 0,
                        "errors": [{"error": f"Cannot move '{eid}' under itself"}]}
            subtree = {eid}
            subtree.update(self._collect_subtree_ids_ordered(elements_by_id, eid))
            if target_id in subtree:
                return {"success": False, "moved": [], "movedCount": 0,
                        "errors": [{"error": f"Cannot move '{eid}' under its own descendant '{target_id}'"}]}

        # Build synthesized target_children list (snapshot of current order)
        if target_parent_el:
            target_children = list(target_parent_el.get("children", []))
        else:
            # Page-root order: elements with no parentId, in current page.elements order
            target_children = [e.get("id") for e in target_page.elements
                               if e.get("id") and elements_by_id[e["id"]].get("parentId") is None]

        # Snapshot old info (for response)
        old_info = []
        for el in top_level:
            eid = el.get("id")
            old_parent_id = el.get("parentId")
            if old_parent_id and old_parent_id in elements_by_id:
                old_parent_el = elements_by_id[old_parent_id]
                old_kids = old_parent_el.get("children", [])
                old_index = old_kids.index(eid) if eid in old_kids else -1
            else:
                old_parent_el = None
                old_index = target_children.index(eid) if eid in target_children else -1
            old_info.append((el, old_parent_id, old_parent_el, old_index))

        # Clamp initial insert index
        running_index = insert_index
        if running_index is not None and running_index > len(target_children):
            running_index = len(target_children)

        # Mutate
        moved_responses = []
        for el, old_parent_id, old_parent_el, old_index in old_info:
            eid = el.get("id")

            # Remove from old location
            if old_parent_el is not None:
                if eid in old_parent_el.get("children", []):
                    old_parent_el["children"] = [c for c in old_parent_el["children"] if c != eid]
            else:
                # Was a page root — remove from synthesized list
                if eid in target_children:
                    target_children.remove(eid)
                    if running_index is not None and old_index >= 0 and old_index < running_index:
                        running_index -= 1

            # Update parentId
            if target_parent_el:
                el["parentId"] = target_parent_el.get("id")
            else:
                if "parentId" in el:
                    del el["parentId"]

            # Defensive: ensure eid not already in target_children
            if eid in target_children:
                target_children.remove(eid)

            # Insert at running_index (or append)
            if running_index is None or running_index > len(target_children):
                target_children.append(eid)
                actual_new_index = len(target_children) - 1
            else:
                target_children.insert(running_index, eid)
                actual_new_index = running_index
                running_index += 1

            # Persist target_children to the actual children array
            if target_parent_el:
                target_parent_el["children"] = target_children

            moved_responses.append({
                "nodeId": eid,
                "oldParentId": old_parent_id,
                "newParentId": target_parent_el.get("id") if target_parent_el else None,
                "oldIndex": old_index,
                "newIndex": actual_new_index,
            })

        # Re-order page.elements: remove moved subtree blocks, re-insert near target
        moved_subtrees = []
        for el, _, _, _ in old_info:
            eid = el.get("id")
            descendants = self._collect_subtree_ids_ordered(elements_by_id, eid)
            subtree_ids = [eid] + descendants
            subtree_elements = [id_to_el[i] for i in subtree_ids]
            moved_subtrees.append((eid, subtree_elements))

        moved_ids_set = set()
        for _, subtree in moved_subtrees:
            moved_ids_set.update(e.get("id") for e in subtree)

        if target_parent_el:
            # Element target: insert each moved subtree right after the target parent
            new_elements = [e for e in target_page.elements if e.get("id") not in moved_ids_set]
            t_id = target_parent_el.get("id")
            target_idx = next((i for i, e in enumerate(new_elements) if e.get("id") == t_id), -1)
            insert_at = target_idx + 1 if target_idx >= 0 else len(new_elements)
            for _, subtree in moved_subtrees:
                new_elements = new_elements[:insert_at] + subtree + new_elements[insert_at:]
                insert_at += len(subtree)
            target_page.elements = new_elements
        else:
            # Page-root target: rebuild page.elements in DFS order from new page-root order.
            # This ensures the page-root portion reflects target_children.
            visited = set()
            rebuilt = []

            def dfs(eid):
                if eid in visited or eid not in id_to_el:
                    return
                visited.add(eid)
                rebuilt.append(id_to_el[eid])
                for cid in id_to_el[eid].get("children", []) or []:
                    dfs(cid)

            for cid in target_children:
                dfs(cid)

            target_page.elements = rebuilt

        self._save(doc_id)

        return {
            "success": True,
            "pageId": target_page.id,
            "targetParentId": target_parent_el.get("id") if target_parent_el else None,
            "moved": moved_responses,
            "movedCount": len(moved_responses),
            "errors": errors,
        }

    def write_html(self, doc_id: str, html: str, mode: str = "append",
                   target_node_id: str = None, page_id: str = None) -> dict:
        """Write HTML into a document with targeted mode support."""
        from parse_html import parse_html_elements

        doc = self.documents.get(doc_id)
        if not doc:
            return {"success": False, "error": "Document not found"}

        parsed = parse_html_elements(html)
        if not parsed:
            return {"success": True, "created": [], "count": 0, "document": self._doc_to_response(doc),
                    "mode": mode, "targetNodeId": target_node_id, "deleted": []}

        # Resolve target
        target_page = None
        target_el = None

        if target_node_id:
            # Check if target_node_id is a page ID
            for p in doc.pages:
                if p.id == target_node_id:
                    target_page = p
                    break
            if not target_page:
                # Check if it's an element ID
                for p in doc.pages:
                    for el in p.elements:
                        if el.get("id") == target_node_id:
                            target_page = p
                            target_el = el
                            break
                    if target_page:
                        break
        elif page_id:
            for p in doc.pages:
                if p.id == page_id:
                    target_page = p
                    break

        if not target_page:
            target_page = doc.pages[doc.current_page]

        # Dispatch by mode
        created_ids = []
        deleted_ids = []

        if mode == "append":
            created_ids = self._mode_append(target_page, target_el, parsed)
        elif mode == "replace-children":
            created_ids, deleted_ids = self._mode_replace_children(target_page, target_el, parsed)
        elif mode == "replace":
            if target_el is None:
                # Target is the page — treat as replace-children
                created_ids, deleted_ids = self._mode_replace_children(target_page, None, parsed)
            else:
                created_ids, deleted_ids = self._mode_replace(target_page, target_el, parsed)

        self._save(doc_id)
        created = [el for el in target_page.elements if el.get("id") in created_ids]
        return {
            "success": True,
            "created": created,
            "count": len(created),
            "document": self._doc_to_response(doc),
            "mode": mode,
            "targetNodeId": target_node_id,
            "deleted": deleted_ids,
        }

    def _mode_append(self, page, target_el: dict, parsed: list) -> list:
        """Append parsed roots as children of target. Returns list of created IDs."""
        created_ids = []
        parsed_ids = {el["id"] for el in parsed}
        if target_el is None:
            for el in parsed:
                # Only strip parentId from true roots (parents outside this parsed set)
                if el.get("parentId") not in parsed_ids:
                    el.pop("parentId", None)
                page.elements.append(el)
                created_ids.append(el["id"])
        else:
            for el in parsed:
                # Only set parentId on true roots; keep internal nesting as-is
                if el.get("parentId") not in parsed_ids:
                    el["parentId"] = target_el["id"]
                    if el["id"] not in target_el["children"]:
                        target_el["children"].append(el["id"])
                page.elements.append(el)
                created_ids.append(el["id"])
        return created_ids

    def _mode_replace_children(self, page, target_el: dict, parsed: list) -> tuple:
        """Replace children of target with parsed roots. Returns (created_ids, deleted_ids)."""
        deleted_ids = []
        if target_el is None:
            # Replace all page elements
            deleted_ids = [el["id"] for el in page.elements]
            page.elements = []
        else:
            elements_by_id = {el["id"]: el for el in page.elements}
            descendant_ids = self._collect_descendant_ids(elements_by_id, target_el["id"])
            deleted_ids = list(descendant_ids)
            self._remove_elements(page, descendant_ids)
            target_el["children"] = []

        created_ids = self._mode_append(page, target_el, parsed)
        return created_ids, deleted_ids

    def _mode_replace(self, page, target_el: dict, parsed: list) -> tuple:
        """Replace target element and all descendants with parsed roots. Returns (created_ids, deleted_ids)."""
        parent_id = target_el.get("parentId")

        elements_by_id = {el["id"]: el for el in page.elements}
        ids_to_remove = self._collect_descendant_ids(elements_by_id, target_el["id"])
        ids_to_remove.add(target_el["id"])
        deleted_ids = list(ids_to_remove)

        target_idx = None
        for i, el in enumerate(page.elements):
            if el["id"] == target_el["id"]:
                target_idx = i
                break

        if target_idx is None:
            return [], deleted_ids

        # Build new element list preserving order
        before = page.elements[:target_idx]
        after = [el for el in page.elements[target_idx + 1:] if el["id"] not in ids_to_remove]

        parsed_ids = {el["id"] for el in parsed}
        for el in parsed:
            if el.get("parentId") in parsed_ids:
                continue
            if parent_id:
                el["parentId"] = parent_id
            else:
                el.pop("parentId", None)

        new_root_ids = [el["id"] for el in parsed if el.get("parentId") not in parsed_ids]
        page.elements = before + parsed + after

        # Update parent's children array
        if parent_id:
            parent = next((el for el in page.elements if el["id"] == parent_id), None)
            if parent:
                children = parent.get("children", [])
                try:
                    old_idx = children.index(target_el["id"])
                    parent["children"] = children[:old_idx] + new_root_ids + children[old_idx + 1:]
                except ValueError:
                    pass

        return [el["id"] for el in parsed], deleted_ids

    @staticmethod
    def _remove_elements(page, ids_to_remove: set):
        """Remove elements from page and clean up references to removed IDs."""
        page.elements = [el for el in page.elements if el.get("id") not in ids_to_remove]
        for el in page.elements:
            el["children"] = [cid for cid in el.get("children", []) if cid not in ids_to_remove]
            if el.get("parentId") in ids_to_remove:
                del el["parentId"]

    def export_html(self, doc_id: str, pretty: bool = True) -> dict:
        """Export document as HTML"""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"error": "Document not found"}

        html = self._generate_html(doc, pretty=pretty)
        return {"success": True, "html": html}

    def get_page_html(self, doc_id: str, page_id: str = None, pretty: bool = True) -> dict:
        """Get clean exported HTML for one page/artboard."""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"success": False, "error": "Document not found"}
        if page_id:
            page = next((p for p in doc.pages if p.id == page_id), None)
            if not page:
                return {"success": False, "error": f"Page '{page_id}' not found"}
        else:
            if not doc.pages:
                return {"success": False, "error": "No pages"}
            page = doc.pages[doc.current_page]
        html = self._generate_single_page_html(doc, page)
        return {"success": True, "kind": "page", "pageId": page.id, "html": html}

    def get_node_html(self, doc_id: str, node_id: str = None, page_id: str = None, pretty: bool = True) -> dict:
        """Get clean exported HTML for a page or a single node subtree."""
        doc = self.documents.get(doc_id)
        if not doc:
            return {"success": False, "error": "Document not found"}

        target_page = None
        target_el = None
        requested_page = None

        if page_id:
            requested_page = next((p for p in doc.pages if p.id == page_id), None)
            if not requested_page:
                return {"success": False, "error": f"Page '{page_id}' not found"}

        if node_id:
            pages = [requested_page] if requested_page else doc.pages
            for p in pages:
                if p.id == node_id:
                    target_page = p
                    break
            if not target_page:
                for p in pages:
                    for el in p.elements:
                        if el.get("id") == node_id:
                            target_page = p
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

        if target_el:
            elements_by_id = {el["id"]: el for el in target_page.elements}
            html = self._render_element(target_el, elements_by_id, "", "  ", "\n").strip()
            return {"success": True, "kind": "element", "pageId": target_page.id, "nodeId": target_el["id"], "html": html}
        else:
            html = self._generate_single_page_html(doc, target_page)
            return {"success": True, "kind": "page", "pageId": target_page.id, "html": html}

    def set_screenshot_data(self, doc_id: str, payload: dict):
        """Store screenshot data and metadata from frontend."""
        from datetime import datetime, timezone

        data_str = (payload.get("data") or "") if isinstance(payload, dict) else ""
        mime_type = ""
        byte_length = 0
        if isinstance(data_str, str) and data_str.startswith("data:"):
            semi = data_str.find(";")
            if semi > 5:
                mime_type = data_str[5:semi]
            comma = data_str.find(",")
            if comma >= 0:
                b64 = data_str[comma + 1:]
                byte_length = (len(b64) * 3) // 4
        elif isinstance(data_str, str):
            byte_length = len(data_str)

        captured_at = None
        if isinstance(payload, dict):
            captured_at = payload.get("capturedAt") or None
        if not captured_at:
            captured_at = datetime.now(timezone.utc).isoformat()

        self._screenshot_data[doc_id] = {
            "data": data_str,
            "pageId": (payload.get("pageId") if isinstance(payload, dict) else None) or None,
            "nodeId": (payload.get("nodeId") if isinstance(payload, dict) else None) or None,
            "scale": payload.get("scale", 1) if isinstance(payload, dict) else 1,
            "transparent": payload.get("transparent", False) if isinstance(payload, dict) else False,
            "capturedAt": captured_at,
            "byteLength": byte_length,
            "mimeType": mime_type,
        }

    def get_screenshot_data(self, doc_id: str) -> dict:
        """Get stored screenshot metadata dict (or empty dict if none)."""
        return self._screenshot_data.get(doc_id, {})

    @staticmethod
    def _style_to_attr(style: dict) -> str:
        """Convert style dict to escaped style attribute string."""
        if not style:
            return ""

        def to_css_property(name: str) -> str:
            if name.startswith("--"):
                return name
            return "".join(f"-{ch.lower()}" if ch.isupper() else ch for ch in name)

        parts = []
        for k, v in style.items():
            if v is not None:
                parts.append(f"{to_css_property(str(k))}: {v}")
        return f' style="{html.escape("; ".join(parts))}"'

    def _render_element(self, el: dict, elements_by_id: dict, indent: str, indent_step: str, nl: str, _seen: set = None) -> str:
        """Recursively render element and children, walking children array with cycle detection."""
        if _seen is None:
            _seen = set()
        el_id = el.get("id", "")
        if not el_id or el_id in _seen:
            return ""
        _seen.add(el_id)

        tag = el.get("tag", "div")
        text = html.escape(el.get("text", "") or "")
        style_attr = self._style_to_attr(el.get("style", {}))
        attrs = f'data-paper-node="{html.escape(el_id)}"'

        children_html = ""
        for child_id in el.get("children", []):
            child = elements_by_id.get(child_id)
            if child:
                children_html += self._render_element(child, elements_by_id, indent + indent_step, indent_step, nl, _seen)

        inner = text + children_html
        return f'{indent}<{tag} {attrs}{style_attr}>{inner}</{tag}>{nl}'

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
        elements_by_id = {el["id"]: el for el in page.elements}
        roots = [el for el in page.elements if not el.get("parentId")]

        elements_html = ""
        for root in roots:
            elements_html += self._render_element(root, elements_by_id, "  ", "  ", "\n")

        bg_color = html.escape(page.backgroundColor or "#ffffff")
        bg_div = f"""<div style="width: {page.width}px; height: {page.height}px; background: {bg_color}; position: relative; overflow: hidden;">
  {elements_html}</div>"""

        page_title = html.escape(page.name)
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{page_title}</title>
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

        pages_html = ""
        for i, page in enumerate(doc.pages):
            elements_by_id = {el["id"]: el for el in page.elements}
            roots = [el for el in page.elements if not el.get("parentId")]

            elements_html = ""
            for root in roots:
                elements_html += self._render_element(root, elements_by_id, indent, indent, nl)

            page_name = html.escape(page.name)
            bg_color = html.escape(page.backgroundColor or "#ffffff")
            pages_html += f'{indent}<div data-paper-page="{i}" data-paper-name="{page_name}"{nl}'
            pages_html += f'{indent}     style="width: {page.width}px; height: {page.height}px; position: absolute; left: {page.x}px; top: {page.y}px; background: {bg_color};">{nl}'
            pages_html += elements_html
            pages_html += f'{indent}</div>{nl}'

        doc_title = html.escape(doc.title)
        return f"""<!DOCTYPE html>
<html data-paper-file="true" data-paper-version="1.0">
<head>
  <meta charset="UTF-8">
  <meta name="paper:title" content="{doc_title}">
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

    @staticmethod
    def _parse_css_style(style_str: str) -> dict:
        """Parse CSS style string to camelCase dict (handles both kebab and camel keys)."""
        result = {}
        if not style_str:
            return result
        for item in style_str.split(";"):
            item = item.strip()
            if ":" in item:
                k, v = item.split(":", 1)
                k = k.strip()
                v = v.strip()
                parts = k.split("-")
                camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
                result[camel] = v
        return result

    @staticmethod
    def _parse_px(value: str) -> int:
        """Parse a pixel value string like '960px' or '960' into int."""
        if not value:
            return 0
        value = value.strip()
        if value.endswith("px"):
            value = value[:-2]
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _infer_type(self, tag: str, style: dict, text: str) -> str:
        """Infer element type from tag, style, and text content."""
        text_tags = {"p", "span", "em", "strong", "label", "figcaption"}
        heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}
        if tag in ("img",):
            return "image"
        if tag in heading_tags:
            return "heading"
        if tag in ("ul", "ol"):
            return "list"
        if tag == "li":
            return "list-item"
        if tag in ("svg",):
            return "svg"
        if tag == "table":
            return "table"
        if tag in text_tags:
            return "text"
        if text:
            return "text"
        if style.get("fontSize"):
            return "text"
        return "rectangle"

    def _parse_element_tree(self, tag, elements: list, parent_id: str = None):
        """Recursively walk BeautifulSoup tag tree, appending element dicts to `elements`.
        Returns the element ID if this tag is a data-paper-node, None otherwise."""
        if tag.get("data-paper-ui") is not None:
            return None

        if not tag.get("data-paper-node"):
            for child in tag.children:
                if isinstance(child, str) or not hasattr(child, "name"):
                    continue
                self._parse_element_tree(child, elements, parent_id)
            return None

        el_id = tag["data-paper-node"]
        tag_name = tag.name
        style = self._parse_css_style(tag.get("style", ""))

        from bs4 import Comment
        direct_strings = [s for s in tag.contents if isinstance(s, str) and not isinstance(s, Comment)]
        text = "".join(direct_strings).strip() or None

        el_type = self._infer_type(tag_name, style, text or "")

        el = {
            "id": el_id,
            "name": f"{tag_name.capitalize()} Element",
            "tag": tag_name,
            "type": el_type,
            "style": style,
            "text": text,
            "children": [],
        }
        if parent_id:
            el["parentId"] = parent_id

        elements.append(el)

        for child in tag.children:
            if isinstance(child, str) or not hasattr(child, "name"):
                continue
            child_id = self._parse_element_tree(child, elements, parent_id=el_id)
            if child_id:
                el["children"].append(child_id)

        return el_id

    def _parse_html(self, content: str, file_path: str) -> Document:
        """Parse HTML file into document using BeautifulSoup."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")

        title = "Untitled"
        title_meta = soup.find("meta", {"name": "paper:title"})
        if title_meta and title_meta.get("content"):
            title = title_meta["content"]

        current_page = 0
        cp_meta = soup.find("meta", {"name": "paper:current-page"})
        if cp_meta and cp_meta.get("content"):
            try:
                current_page = int(cp_meta["content"])
            except (ValueError, TypeError):
                pass

        pages = []
        page_divs = soup.find_all("div", attrs={"data-paper-page": True})

        for page_div in page_divs:
            page_idx_str = page_div.get("data-paper-page", "0")
            try:
                page_idx = int(page_idx_str)
            except (ValueError, TypeError):
                page_idx = 0

            page_name = page_div.get("data-paper-name", f"Page {page_idx + 1}")
            page_style = self._parse_css_style(page_div.get("style", ""))

            width = self._parse_px(page_style.get("width", "375"))
            height = self._parse_px(page_style.get("height", "812"))
            x = self._parse_px(page_style.get("left", "0"))
            y = self._parse_px(page_style.get("top", "0"))
            bg_color = page_style.get("background") or page_style.get("backgroundColor") or "#ffffff"

            elements = []
            for child in page_div.children:
                if isinstance(child, str) or not hasattr(child, "name"):
                    continue
                if child.name == "style":
                    continue
                self._parse_element_tree(child, elements)

            pages.append(Page(
                id=f"page-{page_idx}",
                name=page_name,
                x=x,
                y=y,
                width=width,
                height=height,
                backgroundColor=bg_color,
                elements=elements,
            ))

        if not pages:
            pages.append(Page(id="page-1", name="Page 1"))

        doc_id = str(uuid.uuid4())[:8]
        return Document(
            id=doc_id,
            title=title,
            pages=pages,
            current_page=current_page,
            file_path=file_path,
        )
