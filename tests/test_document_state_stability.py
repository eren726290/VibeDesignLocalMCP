"""Regression coverage for document routing, stable page IDs, and data repair."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import document as document_module
from document import Document, DocumentStore, Page


def _store_in_temp_dir():
    temporary = tempfile.TemporaryDirectory()
    document_module.DATA_DIR = Path(temporary.name)
    return temporary, DocumentStore()


def test_open_keeps_document_and_page_ids_stable():
    original_data_dir = document_module.DATA_DIR
    temporary, store = _store_in_temp_dir()
    try:
        source = Document(
            id="source-doc",
            title="Stable IDs",
            current_page=1,
            pages=[
                Page(id="deck-4x3", name="4:3", width=960, height=720),
                Page(id="deck-9x16", name="9:16", width=720, height=1280),
            ],
        )
        html_path = Path(temporary.name) / "stable.html"
        html_path.write_text(store._generate_html(source), encoding="utf-8")

        opened = store.open_document("active-doc", str(html_path))

        assert opened["id"] == "active-doc"
        assert [page["id"] for page in opened["pages"]] == ["deck-4x3", "deck-9x16"]
        assert opened["current_page"] == 1
    finally:
        document_module.DATA_DIR = original_data_dir
        temporary.cleanup()


def test_multi_artboard_writes_require_an_explicit_target():
    original_data_dir = document_module.DATA_DIR
    temporary, store = _store_in_temp_dir()
    try:
        store.documents["active-doc"] = Document(
            id="active-doc",
            title="Targeting",
            pages=[
                Page(id="deck-4x3", name="4:3", width=960, height=720),
                Page(id="deck-9x16", name="9:16", width=720, height=1280),
            ],
            current_page=1,
        )

        ambiguous = store.write_html("active-doc", "<div>wrong page</div>")
        targeted = store.write_html("active-doc", "<div>right page</div>", page_id="deck-4x3")

        assert not ambiguous["success"]
        assert "pageId or targetNodeId" in ambiguous["error"]
        assert targeted["success"]
        assert targeted["pageId"] == "deck-4x3"
        assert len(store.documents["active-doc"].pages[0].elements) == 1
        assert len(store.documents["active-doc"].pages[1].elements) == 0
    finally:
        document_module.DATA_DIR = original_data_dir
        temporary.cleanup()


def test_single_artboard_write_can_still_use_current_page():
    original_data_dir = document_module.DATA_DIR
    temporary, store = _store_in_temp_dir()
    try:
        store.documents["single-doc"] = Document(
            id="single-doc",
            title="Single artboard",
            pages=[Page(id="only-page", name="Only", width=960, height=720)],
        )

        result = store.write_html("single-doc", "<div>single-page content</div>")

        assert result["success"]
        assert result["pageId"] == "only-page"
        assert len(store.documents["single-doc"].pages[0].elements) == 1
    finally:
        document_module.DATA_DIR = original_data_dir
        temporary.cleanup()


def test_load_repairs_document_integrity_deterministically():
    temporary = tempfile.TemporaryDirectory()
    original_data_dir = document_module.DATA_DIR
    document_module.DATA_DIR = Path(temporary.name)
    try:
        broken = {
            "id": "broken-doc",
            "title": "Broken",
            "current_page": 99,
            "pages": [
                {
                    "id": "duplicate-page",
                    "name": "One",
                    "width": 960,
                    "height": 720,
                    "elements": [
                        {"id": "node-a", "style": None, "children": ["node-b", "missing"]},
                        {"id": "node-b", "style": {}, "children": [], "parentId": "node-a"},
                    ],
                },
                {
                    "id": "duplicate-page",
                    "name": "Two",
                    "width": 0,
                    "height": -1,
                    "elements": [
                        {"id": "node-a", "style": {}, "children": []},
                    ],
                },
            ],
        }
        (document_module.DATA_DIR / "broken-doc.json").parent.mkdir(parents=True, exist_ok=True)
        (document_module.DATA_DIR / "broken-doc.json").write_text(json.dumps(broken), encoding="utf-8")

        repaired = DocumentStore().documents["broken-doc"]
        page_ids = [page.id for page in repaired.pages]
        node_ids = [element["id"] for page in repaired.pages for element in page.elements]

        assert len(page_ids) == len(set(page_ids))
        assert len(node_ids) == len(set(node_ids))
        assert repaired.current_page == 1
        assert repaired.pages[1].width == 375
        assert repaired.pages[1].height == 812
        assert all(isinstance(element["style"], dict) for page in repaired.pages for element in page.elements)
        assert repaired.pages[0].elements[0]["children"] == ["node-b"]
    finally:
        document_module.DATA_DIR = original_data_dir
        temporary.cleanup()


if __name__ == "__main__":
    test_open_keeps_document_and_page_ids_stable()
    test_multi_artboard_writes_require_an_explicit_target()
    test_single_artboard_write_can_still_use_current_page()
    test_load_repairs_document_integrity_deterministically()
    print("Document state stability checks passed.")
