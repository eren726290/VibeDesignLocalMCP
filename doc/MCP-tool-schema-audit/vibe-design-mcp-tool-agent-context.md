# VibeDesign MCP Tool Agent Context Snapshot

Purpose: capture the agent-facing MCP tool inventory and input schemas exposed by the active VibeDesign MCP server.

Source of truth for this snapshot:

- `backend/main.py`
- `TOOLS_LIST`

Important: this file records what the agent is told through MCP tool discovery. It does not yet prove that each tool implementation behaves exactly as described. Implementation behavior, response shape, missing parameters, unclear semantics, and stale descriptions should be verified in a later audit pass.

## Audit Fields

Each tool should eventually be checked against these fields:

- Agent-facing description: text exposed in MCP discovery.
- JSON schema exposed to MCP: input properties and required fields.
- Actual implementation behavior: what the handler really does.
- Missing parameters: behavior supported by code but absent from schema.
- Unclear semantics: parameters whose meaning is ambiguous for an agent.
- Outdated description: schema text that no longer matches implementation.
- Response clarity: whether the response gives enough information for follow-up actions.

## Tool Inventory

Total tools: 30

### get_basic_info

Description: Get basic document info

Required: none

Properties: none

Implementation behavior: not verified in this file.

### get_selection

Description: Get selected nodes

Required: none

Properties: none

Implementation behavior: not verified in this file.

### get_tree_summary

Description: Get hierarchical tree summary of the document

Required: none

Properties:

- `nodeId` string: Optional. Page or element ID. Omit to use current page.
- `depth` number: How many levels to show. 0 = target only. Default 5.

Implementation behavior: not verified in this file.

### get_children

Description: Get direct children of a node

Required: none

Properties:

- `nodeId` string: Optional. Page or element ID. Omit to use current page.

Implementation behavior: not verified in this file.

### get_node_info

Description: Get detailed info about a page or element

Required: none

Properties:

- `nodeId` string: Optional. Page or element ID. Omit to use current page.

Implementation behavior: not verified in this file.

### get_screenshot

Description: Get the latest stored screenshot and metadata for the document.

Required: none

Properties:

- `pageId` string: Optional page ID.
- `nodeId` string: Optional page or element ID.
- `scale` number: Requested scale preference. Default 1.
- `transparent` boolean: Requested transparency preference. Default false.
- `includeData` boolean: Whether to include the screenshot data in the response. Default true.

Implementation behavior: not verified in this file.

### write_html

Description: Write HTML into a document. Supports targeted append/replace-children/replace modes. Use targetNodeId to target an existing element or page. Without targetNodeId, uses pageId or the current page.

Required:

- `html`

Properties:

- `html` string: HTML string with inline styles. The outermost element fills the artboard automatically; no need to set position/width/height.
- `targetNodeId` string: Target page or element ID. If targeting an element, the mode operates on that element. If targeting a page, the mode operates on the page root.
- `pageId` string: Target page ID, used only if targetNodeId is not provided. If omitted, uses the current page.
- `mode` string: One of `append` default, `replace-children`, `replace`.

Implementation behavior: not verified in this file.

Initial audit concern: this is likely one of the highest-priority tools to compare against implementation because it is broad and agent-critical.

### duplicate_nodes

Description: Duplicate full element subtrees and return per-root descendant ID maps.

Required:

- `nodeIds`

Properties:

- `nodeIds` array of string: Element node IDs to duplicate. Required, non-empty.
- `offsetX` number: Horizontal offset applied to cloned root's positional style. Default 20.
- `offsetY` number: Vertical offset applied to cloned root's positional style. Default 20.

Implementation behavior: not verified in this file.

### update_styles

Description: Update styles

Required:

- `nodeIds`
- `styles`

Properties:

- `nodeIds` array of string
- `styles` object
- `removeStyleKeys` array of string: Optional style keys to remove from element styles after applying styles. Must be an array of non-empty strings when provided. Applies to elements only; never reaches artboard/page updates. Example: `["left", "top"]`.

Implementation behavior: not verified in this file.

Initial audit concern: description is very short compared with the parameter behavior.

### set_text_content

Description: Set text content

Required:

- `nodeIds`
- `text`

Properties:

- `nodeIds` array of string
- `text` string

Implementation behavior: not verified in this file.

### rename_nodes

Description: Rename element nodes and page/artboard nodes. Returns per-node results with oldName/newName/kind/pageId/node. Supports an optional pageId constraint to scope the lookup to a single page, or rename that page itself when a nodeId equals pageId.

Required:

- `nodeIds`
- `names`

Properties:

- `nodeIds` array of string: Node IDs to rename, elements and/or page IDs. Required, non-empty.
- `names` object: Map of nodeId to new name. Every requested ID must have a non-empty string entry. Whitespace-only is invalid.
- `pageId` string: Optional page ID. If provided, validates first and scopes the lookup to that page; if a nodeId equals pageId, that page is renamed.

Implementation behavior: not verified in this file.

### finish_working_on_nodes

Description: Mark work finished

Required: none

Properties: none

Implementation behavior: not verified in this file.

### get_computed_styles

Description: Get computed styles

Required: none

Properties:

- `nodeIds` array of string

Implementation behavior: not verified in this file.

### get_jsx

Description: Export as a JSX `function PaperCanvas()` component. Supports pageId, nodeId, and nodeIds. Emits valid React style object syntax, escapes text safely, and includes data-paper-node/data-paper-name expression attributes on every element. Read-only.

Required: none

Properties:

- `pageId` string: Optional page ID. Validated first; constrains nodeId/nodeIds lookup to that page.
- `nodeId` string: Optional single node ID. If it equals pageId, exports that page; otherwise exports that element subtree. Mutually exclusive with nodeIds.
- `nodeIds` array of string: Optional list of element node IDs. Renders each subtree in page/traversal order. Per-page ancestor/descendant dedup: a requested descendant whose ancestor is also requested is dropped. Empty list behaves like no nodeIds. Mutually exclusive with nodeId.

Implementation behavior: not verified in this file.

### get_font_family_info

Description: Get font info

Required: none

Properties:

- `fontFamily` string

Implementation behavior: not verified in this file.

### save_document

Description: Save document

Required: none

Properties:

- `filePath` string

Implementation behavior: not verified in this file.

### open_document

Description: Open document

Required:

- `filePath`

Properties:

- `filePath` string

Implementation behavior: not verified in this file.

### export_html

Description: Export as HTML

Required: none

Properties:

- `pretty` boolean

Implementation behavior: not verified in this file.

### get_page_html

Description: Get clean exported HTML for one page/artboard

Required: none

Properties:

- `pageId` string: Optional. Page ID. Omit to use current page.
- `pretty` boolean: Pretty-print the HTML. Default true.

Implementation behavior: not verified in this file.

### get_html

Description: Get clean exported HTML for the current page, a page, or an element subtree.

Required: none

Properties:

- `nodeId` string: Optional. Page or element ID. Omit to use current page.
- `pageId` string: Optional. Target page ID.
- `pretty` boolean: Pretty-print the HTML. Default true.

Implementation behavior: not verified in this file.

### create_artboard

Description: Create a new artboard/page

Required: none

Properties:

- `pageId` string: Optional page ID, for example `hero-section`. Auto-generated if omitted.
- `name` string: Artboard name, for example `Header`, `Hero Section`, or `Mobile Home`.
- `width` number: Width in pixels.
- `height` number: Height in pixels.
- `x` number: X position on canvas. If omitted, auto-places to the right of existing artboards.
- `y` number: Y position on canvas. If omitted, auto-places to the right of existing artboards.

Implementation behavior: not verified in this file.

### delete_artboard

Description: Delete an artboard/page

Required:

- `pageId`

Properties:

- `pageId` string: Page ID to delete.

Implementation behavior: not verified in this file.

### delete_nodes

Description: Delete element subtrees. Removes each requested node plus all of its descendants, cleans up parent/children references, and supports optional pageId constraint.

Required:

- `nodeIds`

Properties:

- `nodeIds` array of string: Element node IDs to delete. Required, non-empty.
- `pageId` string: Optional page ID. If provided, validates first and constrains deletion to that page.

Implementation behavior: not verified in this file.

### move_nodes

Description: Move element nodes within the same page, reorder or reparent. Preserves whole subtrees. Same-page only; cross-page moves are rejected.

Required:

- `nodeIds`

Properties:

- `nodeIds` array of string: Element node IDs to move. Required, non-empty.
- `targetParentId` string: Target page ID or element ID. If omitted, pageId is used as the page-root target.
- `pageId` string: Optional page ID. If provided, constrains targetParentId lookup to that page; otherwise targetParentId can be any page or element.
- `index` number: Insertion index inside the target's children array or page-root order. Omitted or invalid means append at end.

Implementation behavior: not verified in this file.

### update_artboard

Description: Update artboard/page properties: position, size, name, background color.

Required:

- `pageId`

Properties:

- `pageId` string: Page ID to update.
- `x` number: X position on canvas in px.
- `y` number: Y position on canvas in px.
- `width` number: Width in pixels.
- `height` number: Height in pixels.
- `name` string: Artboard name.
- `backgroundColor` string: Background color, for example `#ffffff`.

Implementation behavior: not verified in this file.

### get_layout_diagnostics

Description: Report likely layout issues such as overlap, clipping, text overflow, off-artboard nodes, zero-size nodes, and missing dimensions.

Required: none

Properties:

- `pageId` string: Optional page ID.
- `nodeId` string: Optional page or element ID.
- `includeOverlaps` boolean: Include sibling overlap checks. Default true.
- `includeText` boolean: Include text overflow heuristic. Default true.

Implementation behavior: not verified in this file.

### get_overflow_report

Description: Report nodes that overflow their parent or artboard, including overflow amounts per side.

Required: none

Properties:

- `pageId` string: Optional page ID.
- `nodeId` string: Optional page or element ID.
- `includeArtboard` boolean: Include artboard boundary overflow checks. Default true.
- `includeParent` boolean: Include parent boundary overflow checks. Default true.
- `minOverflow` number: Minimum pixel overflow to report. Default 1.

Implementation behavior: not verified in this file.

### get_svg_summary

Description: Summarize SVG elements and primitives for text-only inspection of charts, diagrams, and icons.

Required: none

Properties:

- `pageId` string: Optional page ID.
- `nodeId` string: Optional page or element ID.
- `maxItems` number: Maximum number of detailed items per SVG. Default 50.

Implementation behavior: not verified in this file.

### update_svg_attributes

Description: Update SVG/XML attributes on an existing SVG node. Writes attrs into the node style dict so export/render paths emit them as SVG attributes.

Required:

- `nodeId`
- `attrs`

Properties:

- `nodeId` string
- `attrs` object

Implementation behavior: not verified in this file.

Initial audit concern: schema does not describe supported SVG attribute names, attribute casing behavior, validation behavior, page scoping, or response shape.

### validate_svg

Description: Validate SVG trees for missing references, malformed viewBox, missing primitive attrs, duplicate native IDs, and simple viewBox bounds issues.

Required: none

Properties:

- `pageId` string: Optional page/artboard ID. If provided, validates SVGs on that page or constrains node lookup.
- `nodeId` string: Optional SVG root, SVG descendant, or page/artboard ID.

Implementation behavior: not verified in this file.

## Next Audit Pass

Recommended next task for OpenCode:

1. For each tool in this file, read its handler in `backend/main.py`.
2. Compare actual parameters, defaults, validation, side effects, and response shape against the MCP schema.
3. Record mismatches in this doc without changing tool behavior.
4. Prioritize high-impact tools first: `write_html`, `update_styles`, `update_svg_attributes`, `get_html`, `get_node_info`, `move_nodes`, and `duplicate_nodes`.
