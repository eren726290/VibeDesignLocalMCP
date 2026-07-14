# VibeDesign Workflow

This document explains the normal VibeDesignLocalMCP-2 workflow from a user request to a rendered canvas result.

Example request:

```text
Build me a simple landing page.
```

## Big Picture

VibeDesignLocalMCP-2 is agent-first. The agent does most creation and repair work through MCP tools. The backend owns the document model. The frontend renders backend state and gives the user a safe review surface.

```text
user request
    |
    v
agent plans the page
    |
    v
MCP tools write/inspect/edit document nodes
    |
    v
backend stores the document tree
    |
    v
frontend polls backend and renders artboards
    |
    v
user reviews canvas, layers, and inspector
    |
    v
agent applies precise follow-up edits
```

## Main Actors

### User

The user asks for a design, reviews the result, and gives corrections.

The user should not need to manually build layout through disabled shape tools. Manual frontend interaction is mainly for review, selection, and safe inspection.

### Agent

The agent translates the request into HTML/SVG and uses MCP tools to create, inspect, patch, diagnose, and export the design.

The agent should target backend node IDs, not native DOM IDs.

### MCP Server

The MCP server exposes tools such as:

- `create_artboard`
- `write_html`
- `get_tree_summary`
- `get_node_info`
- `get_children`
- `get_html`
- `get_page_html`
- `update_styles`
- `set_text_content`
- `update_svg_attributes`
- `get_layout_diagnostics`
- `get_overflow_report`
- `get_svg_summary`
- `validate_svg`
- `duplicate_nodes`
- `move_nodes`
- `delete_nodes`
- `rename_nodes`
- `export_html`
- `save_document`
- `open_document`

### Backend

The backend is the source of truth. It stores documents, pages/artboards, elements, styles, SVG attributes, parent/child links, and stable backend node IDs.

### Frontend

The frontend renders pages/artboards from backend state. It supports safe selection, layer identity, inspector identity, pan/zoom, artboard movement, and review.

The frontend is not currently a full manual design editor.

## Request To Canvas Pipeline

### 1. User Sends Request

The workflow starts with a human request:

```text
Build me a simple landing page for a coffee shop.
```

The agent interprets the request into design intent:

- page/artboard size
- sections
- hierarchy
- copy
- visual style
- HTML/SVG structure
- likely responsive or fixed artboard needs

### 2. Agent Creates Or Selects An Artboard

The agent calls `get_basic_info` to inspect the current document and active pages.

If needed, the agent creates an artboard:

```text
create_artboard(pageId, name, width, height, x, y)
```

The backend adds a page/artboard to the document. The frontend later renders it from backend state.

### 3. Agent Writes Initial HTML/SVG

The agent calls `write_html` with HTML content.

Common mode:

```text
write_html(pageId, html, mode="replace-children")
```

The backend parses the HTML into element nodes:

- backend node IDs are generated or preserved
- native DOM IDs are stored separately as `style["id"]`
- inline CSS becomes element style data
- SVG/XML attributes are preserved in the style dict for export/render compatibility
- parent/child relationships are built

Critical tree rule:

```text
if node.parentId points to a parent, that parent.children contains the node ID
```

### 4. Backend Stores Document State

After `write_html`, the backend document contains:

- document metadata
- pages/artboards
- root elements per page
- nested child elements
- styles
- text
- SVG attributes
- backend node IDs
- native DOM IDs where present

The backend document is the shared state used by MCP tools, frontend polling, save/open, diagnostics, and export.

### 5. Frontend Polls And Renders

The frontend periodically fetches backend document state.

It renders:

- canvas
- pages/artboards
- nested elements
- layer panel
- inspector identity
- selection state

The frontend should reflect backend changes made by MCP tools without the agent directly editing frontend state.

### 6. Agent Reads Back Structure

After the first write, the agent should inspect before editing.

Useful tools:

- `get_tree_summary` for document/page structure
- `get_node_info` for exact node identity and metadata
- `get_children` for direct children
- `get_html` for clean element/page HTML readback
- `get_page_html` for page-level HTML
- `get_computed_styles` for style inspection where needed
- `get_selection` for current UI selection when relevant

This step gives the agent backend node IDs for precise edits.

### 7. User Reviews The Canvas

The user reviews the rendered frontend canvas.

Expected frontend behavior:

- clicking artboard content selects the artboard without moving it
- dragging the artboard header/title strip moves the artboard
- clicking elements selects them
- layer and canvas selection stay aligned
- the right inspector shows stable identity metadata
- unsafe element layout fields stay read-only/disabled

The frontend is a safe review and inspection surface, not the main layout mutation engine.

### 8. User Requests Changes

The user gives feedback:

```text
Make the hero headline shorter and change the button color.
```

The agent maps the request to exact backend nodes using the earlier readback or fresh inspection.

Typical edit tools:

- `set_text_content` for text changes
- `update_styles` for CSS changes
- `update_svg_attributes` for SVG/XML attribute changes
- `write_html` with `replace` or `replace-children` for replacing a section
- `move_nodes` for same-page reorder/reparent operations
- `duplicate_nodes` for copying a section/card and receiving descendant ID maps
- `delete_nodes` for removing element subtrees
- `rename_nodes` for human-readable element/page names

### 9. Backend Applies Mutations

Mutation tools update the backend document model.

Examples:

```text
set_text_content(nodeIds=["n-hero-title"], text="Fresh coffee, fast.")
```

```text
update_styles(nodeIds=["n-primary-button"], styles={"backgroundColor": "#0f766e"})
```

```text
update_svg_attributes(nodeId="n-logo-path", attrs={"fill": "#0f766e"})
```

After mutation, the agent should read back the result instead of assuming the visual output is correct.

### 10. Agent Diagnoses Layout And SVG

The agent runs diagnostics when layout or SVG correctness matters.

Useful tools:

- `get_layout_diagnostics`
- `get_overflow_report`
- `get_svg_summary`
- `validate_svg`

These tools are read-only. They help decide whether another repair pass is needed.

### 11. Frontend Updates Again

The frontend polls backend state again and renders the updated canvas.

The user can inspect:

- visual result
- selected element outline
- layer identity
- inspector metadata
- text/style changes

If the user reports an issue, the loop repeats from inspection/edit/diagnostics.

## Save, Open, And Export

When the design is ready, the agent or app can use:

- `save_document`
- `open_document`
- `export_html`
- `get_html`
- `get_page_html`
- `get_jsx`

Expected preservation:

- pages/artboards
- backend element node IDs
- element names
- nesting
- styles
- native HTML/SVG IDs
- SVG/XML attributes

Note: `get_page_html` currently accepts a `pretty` parameter in schema, but the handler ignores it. Agents should not rely on pretty formatting from `get_page_html`.

## Normal Agent Loop

The practical loop is:

```text
understand request
  -> create/select artboard
  -> write_html
  -> inspect tree/node/html
  -> patch exact nodes
  -> diagnose layout/svg
  -> read back/export
  -> user review
  -> repeat if needed
```

## What Should Not Happen

Current guardrails:

- do not use Design Mode
- do not restore manual Text/Frame/Rectangle tools
- do not rely on generic frontend element drag/resize
- do not mutate layout only by guessing from screenshots
- do not target native DOM IDs when MCP tools require backend node IDs
- do not use archive docs as active implementation guidance

## Example: Simple Landing Page

1. User asks for a landing page.
2. Agent calls `get_basic_info`.
3. Agent creates or selects an artboard.
4. Agent calls `write_html` with hero, feature, pricing, and footer markup.
5. Backend parses the HTML into stable nodes.
6. Frontend polls and renders the artboard.
7. Agent calls `get_tree_summary` and `get_node_info` to collect node IDs.
8. User asks for headline and color changes.
9. Agent calls `set_text_content` and `update_styles`.
10. Agent calls `get_overflow_report` and `get_html`.
11. Frontend renders the updated canvas.
12. User approves or asks for another precise edit.

## Source References

- `doc/architecture.md`
- `doc/reference/document-model.md`
- `doc/reference/mcp-tool-contracts.md`
- `doc/reference/frontend-safety.md`
