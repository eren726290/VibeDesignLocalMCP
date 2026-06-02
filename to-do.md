# VibeDesignLocalMCP To-Do

## Priority Order

1. Fix document tree consistency.
2. Fix clean nested `export_html`.
3. Fix `save_document` / `open_document` enough to preserve the normal workflow.
4. Add `write_html` modes.
5. Add reliable `targetNodeId` behavior.
6. Improve `get_tree_summary`, `get_node_info`, and `get_children`.
7. Add `get_html` / `get_page_html`.
8. Add layout and text diagnostics.
9. Add clean `export_pdf` from exported page HTML.
10. Improve SVG inspectability.
11. Improve secondary exports and editing tools.

## Full Task List

### 1. Fix document tree consistency

`parse_html.py` must populate both `parentId` and parent `children`. This is the first task because export/save/readback depend on it.

### 2. Fix `export_html` for nested content

Exported HTML must preserve nested divs, SVG children, text, styles, and artboard structure.

### 3. Fix `save_document` / `open_document`

Save/load should round-trip the full document without destroying artboard names, sizes, positions, parent/child hierarchy, SVG, or styles.

### 4. Add `write_html` modes

Support Paper-like modes:

- `append`
- `replace`
- `replace-children`

This removes the delete-artboard/rebuild workaround.

### 5. Add proper `targetNodeId` support

`write_html` should target an artboard or any node, not only the current page/global behavior.

### 6. Improve `get_tree_summary`

Add:

- node ID
- type/tag
- position
- size
- text snippet
- child count
- parent ID
- visible/locked state if available
- basic overflow/clipping flags

This is critical because the product is agent-first.

### 7. Improve `get_node_info`

Return detailed node information:

- `id`
- `parentId`
- `children`
- `childIds`
- `childCount`
- artboard ID
- x/y/width/height
- text
- tag/type
- visibility
- lock state
- style

### 8. Fix `get_children`

Return real direct children for any node, including SVG children.

### 9. Fix SVG metadata

SVG nodes such as `svg`, `rect`, `circle`, `path`, `line`, and `text` should preserve correct tag/type and be inspectable through tree/query tools.

### 10. Add `get_html` / `get_page_html`

Agents need read-back. This should return current clean HTML for an artboard or node.

### 11. Add `get_layout_diagnostics`

Report:

- overlap
- clipping
- text overflow
- off-artboard elements
- zero-size nodes
- missing dimensions
- suspicious absolute positions

### 12. Add `get_overflow_report`

Focused report-building diagnostic: list nodes that overflow parent/artboard and by how many pixels.

### 13. Add `get_svg_summary`

Text summary of SVG primitives:

- SVG dimensions and viewBox
- rect positions
- circle positions/radii
- path counts
- text labels
- chart-like structure hints

### 14. Re-evaluate `get_screenshot`

Screenshots are useful, but not the primary blocker because the current agent workflow can use external visual tools. Keep this lower priority than tree/readback/export correctness.

### 15. Add clean `export_pdf`

PDF export must be generated from clean exported HTML, not the editor UI. For multi-page reports, each artboard should become one PDF page.

### 16. Add image export parity

Expose `export_png` or `export_image` for artboards/nodes.

### 17. Fix `get_jsx`

JSX export should preserve nesting and generate valid React style objects.

### 18. Add `move_nodes`

Support node reordering and reparenting for layer order and targeted edits.

### 19. Improve `duplicate_nodes`

Return a `descendantIdMap` so agents can edit cloned children immediately.

### 20. Fix `rename_nodes` response

Return actual updated nodes instead of misleading empty results.

### 21. Add visibility/lock behavior

Types already mention visible/locked state. Make behavior consistent across render, tree, node info, and export.

### 22. Add undo/redo for MCP mutations

Frontend has history, but MCP edits also need rollback support or snapshot-based undo.

### 23. Consolidate duplicate MCP backend paths

`main.py`, `mcp_server.py`, and `handlers/mcp_handler.py` overlap. Pick one active implementation and demote or remove stale paths later.

### 24. Tighten API schemas

Tool schemas should match real behavior:

- `pageId`
- `targetNodeId`
- `mode`
- export params
- PDF params

### 25. Add parser/document/export tests

Add focused Python tests for:

- nested HTML
- inline SVG
- save/open round-trip
- export HTML
- write modes

### 26. Add MCP smoke tests

Scripted flow:

```text
create artboard -> write nested HTML -> tree summary -> export HTML -> save/open -> compare structure
```

### 27. Fix desktop wrapper URL

Desktop should point to the actual frontend port, `5175`. This is already fixed locally in `desktop/main.py`.

### 28. Improve startup/dev docs

Replace author-local paths and unclear setup notes with portable commands for Windows, macOS, and Linux.

### 29. Keep normal Windows/macOS/Linux compatibility

Do not over-engineer path handling. Just avoid obvious hardcoded author-machine assumptions.

### 30. Keep the natural VibeDesign document workflow

Do not introduce a new `.vibe` format now. Keep using the existing HTML/document workflow unless a concrete need appears later.

