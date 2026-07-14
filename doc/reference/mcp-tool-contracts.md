# MCP Tool Contracts

This file summarizes the current behavior agents should rely on when using VibeDesign MCP tools.

For exact JSON schema wording, inspect `backend/main.py` and the schema audit docs under `doc/MCP-tool-schema-audit/`.

## General Rules

- Target backend node IDs, not native DOM IDs.
- Prefer readback after mutation.
- Treat missing nodes as possible partial-success cases unless the tool reports a hard error.
- Use page IDs to constrain operations when the target page matters.
- Do not infer success only from visual output; use tool responses and readback tools.

## Creation And Replacement

`write_html` writes HTML into a document with targeted modes:

- `append`
- `replace`
- `replace-children`

It can target a page or a specific node. It returns created elements, counts, deleted IDs for replacement modes, and document state.

## Inspection

Use inspection tools before editing:

- `get_basic_info`
- `get_tree_summary`
- `get_node_info`
- `get_children`
- `get_computed_styles`
- `get_html`
- `get_page_html`
- `get_jsx`
- `get_selection`

`get_html` returns clean exported HTML for a page or element target. The ignored `pretty` option was removed from schema.

## Style And Text Mutation

`update_styles` deep-merges CSS style keys into elements and supports explicit removal through `removeStyleKeys`.

`set_text_content` replaces text content on one or more element nodes while preserving identity, style, and children.

## SVG Mutation And Diagnostics

`update_svg_attributes` updates SVG/XML attributes on SVG elements by backend node ID.

Read-only SVG helpers:

- `get_svg_summary`
- `validate_svg`

SVG native IDs are represented as `style["id"]`.

## Structural Mutation

`move_nodes` reorders or reparents element nodes within the same page. It preserves subtrees and rejects cross-page or cycle moves.

`duplicate_nodes` duplicates full subtrees and returns descendant ID maps for follow-up edits.

`delete_nodes` deletes element subtrees and cleans parent/children references. Pages are not deleted through this tool.

`rename_nodes` renames elements and pages/artboards.

## Diagnostics

Layout and overflow tools are read-only:

- `get_layout_diagnostics`
- `get_overflow_report`

Use them after writes and structural edits to decide whether a repair pass is needed.

## Export And Persistence

Export and persistence tools should preserve nested HTML/SVG and stable identity:

- `save_document`
- `open_document`
- `export_html`

Note: `get_page_html` accepts an optional `pretty` parameter in its schema, but the active handler does not forward it — output is always non-pretty. Do not rely on pretty formatting from `get_page_html`.

After important edits, verify with `get_html`, `get_page_html`, save/open regression tests, or export readback.
