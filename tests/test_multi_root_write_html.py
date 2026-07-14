"""Regression coverage for write_html with multiple top-level HTML roots."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import document as document_module
from document import Document, DocumentStore, Page
from parse_html import parse_html_elements


def test_single_root_remains_a_full_artboard_wrapper():
    elements = parse_html_elements(
        '<section style="height:100px;background:red;position:absolute">A</section>'
    )

    assert len(elements) == 1
    assert "height" not in elements[0]["style"]
    assert "position" not in elements[0]["style"]
    assert elements[0]["style"]["overflow"] == "hidden"


def test_write_html_keeps_multiple_root_siblings_in_normal_flow():
    original_data_dir = document_module.DATA_DIR
    temporary = tempfile.TemporaryDirectory()
    document_module.DATA_DIR = Path(temporary.name)
    try:
        store = DocumentStore()
        store.documents["multi-root-doc"] = Document(
            id="multi-root-doc",
            title="Multi-root",
            pages=[Page(id="page-1", name="Page", width=375, height=812)],
        )

        result = store.write_html(
            "multi-root-doc",
            '<section style="height:100px;background:red">A</section>'
            '<section style="height:100px;background:blue">B</section>',
        )
        roots = store.documents["multi-root-doc"].pages[0].elements

        assert result["success"]
        assert result["count"] == 2
        assert [root["text"] for root in roots] == ["A", "B"]
        assert [root["style"]["height"] for root in roots] == ["100px", "100px"]
        assert [root["style"]["background"] for root in roots] == ["red", "blue"]
        assert all("overflow" not in root["style"] for root in roots)
    finally:
        document_module.DATA_DIR = original_data_dir
        temporary.cleanup()


if __name__ == "__main__":
    test_single_root_remains_a_full_artboard_wrapper()
    test_write_html_keeps_multiple_root_siblings_in_normal_flow()
    print("Multi-root write_html checks passed.")
