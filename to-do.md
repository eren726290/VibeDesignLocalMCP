# VibeDesignLocalMCP To-Do

## Priority Order

Historical backend priority order:

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

Current diagnosis priority:

1. Audit runtime/document identity and persistent workspace storage.
2. Fix backend API status honesty for failed mutations.
3. Fix `update_styles` target-aware routing for dual-use keys such as `backgroundColor`, `width`, and `height`.
4. Disable broken manual Text, Frame, and Rectangle toolbar tools.
5. Redefine the cursor/move tool as Select only.
6. Fix initial frontend viewport so the current page or artboards are visible on load.
7. Fix layer/tree/node identity mapping so left panel rows point to exact rendered canvas nodes.
8. Disable remaining unsafe manual resize/mutation paths.
9. Start a minimal Vite + React agent-first frontend shell if patching the current UI remains more expensive than replacing it.
10. Design an agent-first Design Mode on top of accurate Select.
11. Design an agent-first shape/SVG creation and repair pipeline.
12. Defer layout/domain skills until after V1 core behavior is stable.

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

## Current Diagnosis Tasks

These tasks come from the 7-prompt human-vs-agent diagnosis and the Paper/VibeDesign comparison tests.

### D1. Audit runtime identity and persisted workspace state

Find the exact source of truth for documents across backend, MCP, frontend, browser storage, and saved files.

Acceptance criteria:

- identify where old pages persist after repo deletion/reinstall
- identify why frontend sometimes uses `doc-mpxojyrd` and sometimes `default`
- identify which document ID MCP uses
- identify which file/path `get_basic_info` reports
- provide a clean-runtime checklist for Windows/PC testing

### D2. Fix backend API status honesty

If a backend mutation result is an error, the HTTP response must not still be `200 OK`.

Acceptance criteria:

- missing document returns `404`
- missing page/node returns `404`
- invalid payload returns `400`
- successful mutation returns `200`
- frontend callers can distinguish failure from success

### D3. Fix `update_styles` target-aware routing

`backgroundColor`, `width`, and `height` are valid page/artboard fields and valid element CSS style keys. Routing must depend on the resolved target type.

Acceptance criteria:

- updating an element `backgroundColor` applies to element style
- updating an element `width`/`height` applies to element style
- updating a page/artboard `backgroundColor`, `width`, or `height` applies to page/artboard metadata
- unsupported keys are reported clearly instead of silently dropped

### D4. Disable broken manual creation tools

Remove or disable primary toolbar access for Text, Frame, and Rectangle.

Acceptance criteria:

- Text tool no longer attempts broken create requests
- Frame tool no longer attempts broken create requests
- Rectangle tool no longer attempts broken create requests
- backend/MCP text, page, HTML, and shape capabilities remain available
- UI communicates that agent edits are the primary creation/editing path, if any messaging is needed

### D5. Redefine cursor/move as Select

The cursor icon should be a selection tool, not a mixed page-drag, element-drag, and accidental mutation tool.

Acceptance criteria:

- clicking an artboard selects the artboard
- clicking an element selects the element
- selection updates the layer tree and inspector
- clicking inside a page does not drag the page
- element dragging does not write `left`/`top`
- pan remains a separate tool

### D6. Fix page/artboard drag model

Follow Paper's safer pattern: page movement should happen through a page title/name strip or explicit handle, not by dragging anywhere inside the page.

Acceptance criteria:

- dragging inside page content does not move the artboard
- dragging the page title/name strip can move the artboard when page movement is enabled
- page movement persists through backend state
- page movement does not interfere with element selection

### D7. Fix layer/tree/node identity mapping

The left layer panel must behave like Framer/Paper: selecting a layer or child layer should select the exact corresponding rendered canvas element, and selecting a canvas element should highlight the exact layer row.

Acceptance criteria:

- every layer row maps to a stable backend `nodeId`
- every rendered canvas node exposes the same `data-paper-node`
- layer click sets selection to the exact `nodeId`
- canvas click sets selection to the exact `nodeId`
- right panel shows the same selected node
- nested child layers map correctly
- SVG child nodes map as far as the renderer supports them
- no random or wrong element is highlighted
- `get_tree_summary` describes the same node tree that the layer panel displays

### D8. Disable unsafe manual element resize mutations

Selected elements should show selection outline only until there is a deliberate move/resize model.

Acceptance criteria:

- selected elements no longer show resize handles
- element resize handlers no longer call `updateElement`
- selection outline remains visible
- element selection still syncs with the layer tree
- artboard/page resize behavior remains unchanged
- backend/MCP editing paths remain available

### D9. Define Design Mode on top of Select

Design Mode should be an explicit mode/toggle, inspired by Cursor Design Mode, but targeting VibeDesign backend node IDs instead of source files.

Acceptance criteria:

- Select mode remains safe inspection mode
- Design Mode is opt-in
- selecting a node in Design Mode opens or activates a right-panel AI edit prompt
- prompt receives selected node ID(s)
- agent edits selected node(s) through MCP tools
- readback/diagnostics verify results
- no Design Mode work begins until layer/canvas/node identity is trustworthy

Implementation notes:

- Use `design-mode.md` as the source of truth.
- Do not build a full daemon/queue system for V1.
- Do not depend on agent-specific headless CLI flags.
- Do not require a visible browser terminal.
- Use a persistent tmux session as the agent-agnostic trigger bridge.

Minimal V1 subtasks:

1. Add a backend document revision/version counter and expose it to the frontend.
2. Add a fixed right-panel Design Mode prompt tied to selected node ID(s).
3. Add `POST /api/design-mode/send`.
4. Format the request with doc/page/node identity and user prompt.
5. Inject the message into `tmux` with `load-buffer`, `paste-buffer`, and `send-keys Enter`.
6. Disable Send while pending and clear loading when the document version changes.
7. Add a frontend timeout for no-op/error cases.

### D10. Defer layout/domain skills until after V1 core

Do not write skill system prompts, skill scaffolding, `.skill` folders, skill-loading code, or skill-specific backend/frontend behavior during the current V1 core-feature round.

Future direction: use skills for layout intelligence rather than hardcoding design patterns into backend/frontend code. Skills are agent guidance/craftsmanship, not MCP tools. VibeDesign remains the document/runtime executor.

Acceptance criteria:

- no V1 tasks implement skill prompts, skill folders, or skill-loading code
- future skill work uses progressive disclosure: skill name/description first, full `SKILL.md` only when triggered
- no single skill, including Kami Consulting, becomes the default or definitive VibeDesign pattern
- VibeDesign core remains responsible only for document storage, MCP tools, diagnostics, rendering, and export

### D11. Prevent stale layout-coordinate corruption

Manual UI must not write `left`/`top` into flex/text/card elements as a generic move operation.

Acceptance criteria:

- flex children are not moved by adding `left`/`top` without a deliberate positioning model
- existing stale `left`/`top` can be detected and removed with `removeStyleKeys`
- repair agents are guided toward targeted key removal before rebuilds

### D12. Build minimal agent-first frontend shell

If the existing frontend remains too unstable, build a small replacement shell on Vite + React instead of patching the current UI indefinitely.

Initial scope:

- document load from backend
- artboard rendering
- fit/focus viewport
- pan/zoom
- Select tool
- layer tree
- inspector
- no manual Text/Frame/Rectangle tools
- no manual element dragging

### D13. Design agent-first shape/SVG pipeline

Rectangle is disabled as a broken manual tool. Shape/SVG support should be handled as an agent-first creation and repair pipeline.

Acceptance criteria:

- define shape/SVG creation API or conventions
- preserve inspectable SVG tags and attributes
- support targeted SVG attribute mutation
- expose diagnostics/readback for SVG bounds and viewport issues
- keep export HTML faithful to SVG structure

## Advanced / Polish

### A1. Document agent repair heuristics

Tasks 16-19 validated that the backend editing tools can repair misplaced elements by node ID without rebuilding the page. Treat this item as workflow polish, not a blocker.

Document a standard repair strategy for agents that receive a vague request such as "I messed up the elements, fix it":

- Start with `get_computed_styles` across suspicious nodes to find stale `position`, `left`, `top`, `right`, and `bottom` keys.
- Use `get_tree_summary`, `get_children`, and `get_node_info` to compare current parent/child structure with semantic names and sibling patterns.
- Infer likely parent/index from names, tags, and sibling groups, such as `Footer` under the root container or menu cards inside a menu grid.
- Use `update_styles` plus `removeStyleKeys` for style-only misplacements.
- Use `move_nodes` for structural parent/order mistakes.
- Verify with `get_tree_summary`, `get_node_info`, `get_computed_styles`, `get_html`, or `get_jsx`.

This captures the "Issue 2" advice from the PC validation: the tools are now capable, but agent repair behavior should be documented so future agents consistently choose targeted repair over delete-and-rebuild.
