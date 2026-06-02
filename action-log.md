# Action Log

Planner-owned log for VibeDesignLocalMCP work.

OpenCode does not write this file. Codex reviews completed work and records the decision, changed files, verification, and next action.

## 2026-06-01

### Repository Fork And Initial Read

- Actor: Codex
- Summary: Forked/cloned `eisneim/VibeDesignLocalMCP` under `/root/my-project/VibeDesignLocalMCP`.
- Files changed: none
- Notes:
  - `origin` points to the user fork.
  - `upstream` points to `https://github.com/eisneim/VibeDesignLocalMCP.git`.
  - Root files and project structure were read before planning.

### Full Repo Read

- Actor: Codex
- Summary: Read the repo text files to understand backend, frontend, desktop wrapper, docs, and current MCP implementation.
- Files changed: none
- Key findings:
  - Backend is FastAPI/MCP on port `3004`.
  - Frontend is React/Vite on port `5175`.
  - `backend/main.py` appears to be the active MCP path.
  - `backend/mcp_server.py` and `backend/handlers/mcp_handler.py` appear older or parallel.
  - `parse_html.py` sets `parentId`, but parent `children` arrays were identified as the likely broken document-tree link.
  - `write_html` renders but lacks reliable modes/readback/export behavior.

### Desktop URL Fix

- Actor: Codex
- Summary: Fixed pywebview desktop wrapper URL to match the Vite frontend port.
- Files changed:
  - `desktop/main.py`
- Change:
  - `url="http://localhost:5173"` -> `url="http://localhost:5175"`
- Verification:
  - Read `desktop/main.py` after edit and confirmed the URL points to `5175`.

### Translate Chinese Docs To English

- Actor: Codex
- Summary: Translated Chinese text/references in the main repo docs to English.
- Files changed:
  - `README.md`
  - `plan.md`
  - `prompts.md`
- Verification:
  - Re-read edited files.
  - Searched edited files for remaining Chinese characters.
  - Found and fixed one missed phrase in `plan.md`: `macOS .app 打包` -> `macOS .app packaging`.
  - `git diff --check` passed.
- Notes:
  - No application logic was changed by the translation.
  - The only code change in the same working tree is the desktop URL fix above.

### Architecture Direction Finalized

- Actor: Codex
- Summary: Finalized product direction as agent-first, not a strict 1:1 Paper human-collaboration clone.
- Files changed:
  - `architecture.md`
  - `to-do.md`
  - `action-log.md`
- Decision:
  - Prioritize MCP write/read loop, document-tree correctness, clean export HTML/PDF, and structured diagnostics.
  - Human UI remains important for review and manual correction, but it is secondary to reliable agent workflows.

### Task 01 Review - Parser Tree Consistency

- Actor: Codex
- Summary: Reviewed OpenCode Task 01 implementation.
- Files reviewed:
  - `backend/parse_html.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by OpenCode:
  - `backend/parse_html.py`
- Review result: accepted with follow-up note.
- Verification:
  - `python3 -m py_compile backend/parse_html.py backend/document.py backend/main.py` passed.
  - Manual parser check passed for:
    - `root.children == ["section"]`
    - `section.parentId == "root"`
    - `section.children == ["body"]`
    - `body.parentId == "section"`
    - document order preserved as `root`, `section`, `body`
- Notes:
  - Implementation is scoped and fixes the required invariant for normal valid HTML.
  - OpenCode reported installing `beautifulsoup4` with `--break-system-packages` to run verification, despite the task saying not to install packages. This is a process issue, not a code issue.
  - `beautifulsoup4` is imported by `backend/parse_html.py` but is not listed in `backend/requirements.txt`; add it in a future dependency/docs cleanup task.
  - Duplicate explicit HTML IDs remain ambiguous because the existing document model uses string IDs. Treat duplicate IDs as invalid input for now.

### Task 02 Review - Clean Nested export_html

- Actor: Codex
- Summary: Reviewed OpenCode Task 02 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/document.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by OpenCode:
  - `backend/document.py`
- Files changed by Codex during review:
  - `backend/document.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Added stdlib HTML escaping.
  - Reworked export rendering to use each page's own `elements`.
  - Rendered nested children by walking the `children` array.
  - Added cycle protection and skipped missing child IDs gracefully.
  - Updated `_generate_single_page_html()` and `_generate_html()` to share recursive rendering behavior.
- Codex reviewer fix:
  - Updated style export to convert React-style camelCase keys such as `fontSize` into CSS style keys such as `font-size`.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py` passed.
  - `git diff --check` passed.
  - Manual export check passed for nested `root -> child` HTML.
  - Manual export check confirmed escaped text: `Hello <world>` -> `Hello &lt;world&gt;`.
  - Manual export check confirmed two-page export does not leak page 1 content into page 2 or page 2 content into page 1.
  - Manual export check confirmed `fontSize` no longer appears in exported style attributes and `font-size` does.
- Notes:
  - Added a `Dependencies Installed` section to `/root/my-project/VibeDesignLocalMCP_task.md` so future OpenCode task reports explicitly list any installed dependencies.
  - Dependency installs are ignored as requested, but still recorded for future debugging.
  - `_element_to_html()` appears dead after this task and should be handled in a later cleanup task, not as part of Task 02.

### Task 03 Review - save_document / open_document Round-Trip

- Actor: Codex
- Summary: Reviewed OpenCode Task 03 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/document.py`
  - `backend/requirements.txt`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by OpenCode:
  - `backend/document.py`
  - `backend/requirements.txt`
- Files changed by Codex during review:
  - `backend/document.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Replaced lossy regex `_parse_html()` with BeautifulSoup-based parsing.
  - Preserved document title and current page metadata.
  - Parsed page name, size, position, and background from exported page containers.
  - Rebuilt nested `parentId` and `children` relationships from `data-paper-node` DOM structure.
  - Parsed style strings back into camelCase in-memory style keys.
  - Added missing `beautifulsoup4` dependency to `backend/requirements.txt`.
- Codex reviewer fix:
  - Updated `_parse_element_tree()` to skip `data-paper-ui` subtrees explicitly.
  - Removed a stale pre-execution note from `/root/my-project/VibeDesignLocalMCP_task.md` that incorrectly described the Task 02 reviewer fix as an unresolved export issue.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Manual round-trip test passed for a two-page document.
  - Manual test confirmed page names, sizes, positions, backgrounds, document title, and current page round-trip.
  - Manual test confirmed nested `header -> nav -> link` relationships preserve `parentId` and `children`.
  - Manual test confirmed escaped text round-trips from `Contact <us>`.
  - Manual test confirmed page 2 content stays isolated from page 1.
  - Manual test confirmed `data-paper-ui` content is ignored during open/parse.
- Notes:
  - Parser is intentionally scoped to VibeDesign's own exported HTML format, with best-effort fallback to one blank page for malformed/non-VibeDesign HTML.

### Task 04 Review - write_html Modes And Targeted Replacement

- Actor: Codex
- Time: 2026-06-01T13:33:29Z
- Summary: Reviewed OpenCode Task 04 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/document.py`
  - `backend/main.py`
  - `backend/parse_html.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by OpenCode:
  - `backend/document.py`
  - `backend/main.py`
- Files changed by Codex during review:
  - `backend/document.py`
  - `action-log.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Added `DocumentStore.write_html()` as the backend entry point for mode-aware writes.
  - Added `append`, `replace-children`, and `replace` behavior.
  - Added target resolution for page IDs and element IDs.
  - Updated `backend/main.py` `_write_html()` to delegate to `DocumentStore.write_html()`.
  - Updated the MCP `write_html` schema to document `targetNodeId`, `pageId`, and `mode`.
- Codex reviewer fix:
  - Fixed nested `replace` behavior so the old parent `children` array receives only the new fragment root IDs, not every parsed descendant ID. Without this, replacing a node with nested HTML could duplicate descendants in the parent tree and exported HTML.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Manual backend mutation test passed for:
    - append to page
    - second append to same page
    - `replace-children` on page
    - nested append target behavior
    - `replace-children` on nested element
    - `replace` on nested element while preserving sibling order
    - `replace` on page behaving like `replace-children`
    - exported HTML contains nested replacement content exactly once
    - tree integrity invariant after every operation
- Notes:
  - Task 04 gives agents targeted edit capability and removes the full-artboard-rebuild requirement for many corrections.

### Task 05 Review - Strengthen Tree And Node Inspection

- Actor: Codex
- Time: 2026-06-01T13:57:18Z
- Summary: Reviewed OpenCode Task 05 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/main.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by OpenCode:
  - `backend/main.py`
- Files changed by Codex during review:
  - `backend/main.py`
  - `action-log.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Added recursive tree rendering for `get_tree_summary`.
  - Added cross-page node resolution for inspection tools.
  - Added page and element detail responses for `get_node_info`.
  - Added real direct-child responses for `get_children`.
  - Added parent, child, page, text snippet, and geometry fields to inspection responses.
  - Updated MCP schemas for the strengthened inspection tools.
- Codex reviewer fix:
  - Fixed omitted `nodeId` behavior for `get_children` and `get_node_info` so both default to the current page/artboard, matching the shared targeting rule.
  - Updated those two MCP schema descriptions to mark `nodeId` as optional.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Focused manual inspection test passed 8/8 checks for:
    - omitted `nodeId` resolving to current page in `get_node_info`
    - omitted `nodeId` resolving to current page root children in `get_children`
    - SVG direct child order preservation
    - element parent/page/geometry fields
    - hierarchical tree summary output
    - `depth=1` excluding grandchildren
    - cross-page element resolution
    - clear missing-node responses
- Notes:
  - `get_tree_summary` preserves the `{ "summary": "..." }` response shape for missing nodes by returning a clear not-found summary string rather than adding a separate `error` field.

### Task 06 Review - HTML Read-Back Tools

- Actor: Codex
- Time: 2026-06-02T03:10:36Z
- Summary: Reviewed OpenCode Task 06 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/document.py`
  - `backend/main.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by OpenCode:
  - `backend/document.py`
  - `backend/main.py`
- Files changed by Codex during review:
  - `backend/document.py`
  - `action-log.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Added `DocumentStore.get_page_html()` for clean single-page read-back.
  - Added `DocumentStore.get_node_html()` for page or element-subtree read-back.
  - Reused `_generate_single_page_html()` for page HTML and `_render_element()` for element subtree HTML.
  - Added MCP handlers `_get_page_html()` and `_get_html()`.
  - Added `get_page_html` and `get_html` routing and tool schemas.
- Codex reviewer fix:
  - Made `get_node_html()` validate a non-empty `pageId` even when `nodeId` is also provided.
  - When both `pageId` and `nodeId` are provided, node lookup is now constrained to that page and returns a clear page-scoped not-found error if the node lives elsewhere.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Focused manual read-back test passed 15/15 checks for:
    - default current-page `get_page_html`
    - explicit page 2 `get_page_html`
    - default current-page `get_html`
    - page ID targeting through `nodeId`
    - page targeting through `pageId`
    - root element subtree read-back with nested h1/svg/rect/text
    - SVG subtree-only read-back
    - missing page and node errors
    - `data-paper-node` IDs in output
    - safe text/page-title escaping
    - `export_html` regression
    - no-pages errors
    - `pageId` + `nodeId` page-constrained lookup
    - invalid `pageId` validation when `nodeId` is also present
- Notes:
  - OpenCode's pasted completion report was not present at the end of `/root/my-project/VibeDesignLocalMCP_task.md` during Codex review, but the implementation was reviewed directly from the repository diff and behavior.

### Task 07 Review - Layout Diagnostics

- Actor: Codex
- Time: 2026-06-02T03:36:28Z
- Summary: Reviewed OpenCode Task 07 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/main.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by OpenCode:
  - `backend/main.py`
- Files changed by Codex during review:
  - `backend/main.py`
  - `action-log.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Added `get_layout_diagnostics` MCP handler.
  - Added zero-safe geometry parsing helpers for diagnostics.
  - Added page/current-page/node-subtree targeting.
  - Added diagnostics for missing dimensions, zero size, off-artboard geometry, suspicious positions, parent overflow, text overflow heuristic, and sibling overlap.
  - Added routing in `handle_mcp_tool` and a `TOOLS_LIST` schema entry.
  - Correctly grouped page-root siblings under a stable root group for overlap detection.
  - Honored `includeOverlaps` and `includeText` with default `true` behavior.
- Codex reviewer fix:
  - Updated `get_layout_diagnostics` targeting so a non-empty `pageId` is validated before `nodeId`, and when both are provided node lookup is constrained to that page. This matches Task 07 and the Task 06 read-back targeting rule.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Focused manual diagnostics test passed 20/20 checks for:
    - default current-page diagnostics
    - all seven issue types: missing-dimensions, zero-size, off-artboard, suspicious-position, overflow, text-overflow, overlap
    - page 2 clean/separate targeting
    - page targeting through `nodeId`
    - element-subtree targeting
    - `includeOverlaps: false`
    - `includeText: false`
    - missing page and node errors
    - valid `pageId` + `nodeId`
    - mismatched `pageId` + `nodeId`
    - invalid `pageId` with valid `nodeId`
    - response shape fields and issue count consistency
    - read-only behavior preserving document elements
- Notes:
  - The diagnostics are intentionally heuristic and model-based. They do not attempt browser layout, flex/grid, transforms, or exact text measurement.

## 2026-06-02

### Task 10 Review - Strengthen Screenshot Readback

- Actor: Codex
- Time: 2026-06-02T05:40:57Z
- Summary: Reviewed OpenCode Task 10 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/document.py`
  - `backend/main.py`
  - `backend/requirements.txt`
  - `architecture.md`
  - `to-do.md`
  - `action-log.md`
- Files changed by OpenCode:
  - `backend/document.py`
  - `backend/main.py`
- Files changed by Codex during review:
  - `backend/main.py`
  - `action-log.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Changed screenshot storage from a raw string to a metadata dictionary.
  - Preserved compatibility with the old frontend POST shape `{data: "..."}`.
  - Added metadata normalization for `pageId`, `nodeId`, `scale`, `transparent`, `capturedAt`, `byteLength`, and `mimeType`.
  - Reworked MCP `get_screenshot` to return clear `success` / `error` responses.
  - Added `includeData: false` support to omit large screenshot payloads while returning metadata.
  - Added `pageId` / `nodeId` validation using the existing page-constrained resolver.
  - Updated the `get_screenshot` MCP schema.
- Codex reviewer fix:
  - Fixed targeted screenshot response metadata so a requested `nodeId` on another page returns that resolved page ID, not the stored screenshot page ID.
  - Fixed `pageId`-only requests so the top-level `nodeId` is `None` rather than leaking a stored node ID from another page.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Manual screenshot handler test passed for:
    - missing screenshot error
    - default latest screenshot response
    - `includeData: false`
    - invalid `pageId`
    - invalid `nodeId`
    - `pageId + nodeId` mismatch
    - `nodeId` targeting an element on another page
    - `nodeId` targeting a page ID
    - `pageId`-only targeting
- Notes:
  - No dependencies were installed.
  - Planner-owned files were not edited by OpenCode.
  - This task does not capture fresh pixels; it makes the existing frontend-posted screenshot readback honest and target-aware.

### Task 11 Review - Improve duplicate_nodes With Descendant ID Map

- Actor: Codex
- Time: 2026-06-02T06:23:10Z
- Summary: Reviewed OpenCode Task 11 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/document.py`
  - `backend/main.py`
  - `backend/requirements.txt`
  - `architecture.md`
  - `to-do.md`
  - `action-log.md`
- Files changed by OpenCode:
  - `backend/document.py`
  - `backend/main.py`
- Files changed by Codex during review:
  - `backend/document.py`
  - `action-log.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Kept legacy `DocumentStore.duplicate_element()` backward compatible.
  - Added subtree-aware `duplicate_subtree_batch()` with old-to-new `descendantIdMap`.
  - Added ordered subtree collection, root-only offset handling, deep-copy cloning, and parent inference fallback from `children` arrays.
  - Updated MCP `_duplicate_nodes()` to validate input, parse offsets, and return `duplicated`, `duplicatedCount`, and `errors`.
  - Updated the `duplicate_nodes` schema with `offsetX` and `offsetY`.
  - Preserved cross-page lookup and partial success behavior for missing nodes.
- Codex reviewer fix:
  - Removed explicit `parentId: None` from duplicated page-root clones. Page roots should omit `parentId`, matching the existing root-node convention while still remaining inspectable as roots.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Focused manual duplicate test passed for:
    - full nested subtree clone
    - `descendantIdMap` including root and descendants
    - cloned child `parentId` values pointing to cloned parents
    - nested root preserving original parent relationship
    - original parent `children` insertion after original root
    - page-root clone remaining a page root
    - root-only offset behavior
    - descendants not being offset
    - numeric, zero, px-string, and unparseable position handling
    - ancestor + descendant deduplication
    - missing-node partial failure
    - cross-page duplication
  - Additional page-root behavior check passed after reviewer fix.
- Notes:
  - No dependencies were installed.
  - Planner-owned files were not edited by OpenCode.
  - `duplicate_nodes` now supports immediate agent edits of cloned descendants using returned ID maps.

### Task 12 Review - Add move_nodes For Same-Page Reorder And Reparent

- Actor: Codex
- Time: 2026-06-02T08:49:53Z
- Summary: Reviewed OpenCode Task 12 implementation. No code fix was needed.
- Files reviewed:
  - `backend/document.py`
  - `backend/main.py`
  - `backend/requirements.txt`
  - `architecture.md`
  - `to-do.md`
  - `action-log.md`
- Files changed by OpenCode:
  - `backend/document.py`
  - `backend/main.py`
- Files changed by Codex during review:
  - `action-log.md`
- Review result: accepted.
- OpenCode changes accepted:
  - Added `DocumentStore.move_nodes()` for same-page reorder and reparent operations.
  - Added MCP `_move_nodes()` handler, route entry, and `TOOLS_LIST` schema.
  - Supported page-root reordering, child reparenting, same-parent child reordering, and nested-node-to-root moves.
  - Preserved whole subtrees by reference without cloning or deleting descendants.
  - Rejected cross-page moves, self moves, and moves under descendants without mutation.
  - Added strict `pageId`-first target validation and page-constrained `targetParentId` lookup.
  - Rebuilt page-root `page.elements` order from root order for page-root moves.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Focused independent move tests passed for:
    - page-root reorder
    - child reparent to another parent
    - same-parent reorder
    - nested node moved to page root
    - moved root `parentId` updates
    - descendant `parentId` preservation
    - old parent child removal
    - new parent/root index insertion
    - ancestor + descendant deduplication
    - missing source partial failure
    - self-cycle rejection without mutation
    - descendant-cycle rejection without mutation
    - invalid `pageId` validating before target lookup
    - page-constrained target lookup
    - cross-page rejection without mutation
- Notes:
  - No dependencies were installed.
  - Planner-owned files were not edited by OpenCode.
  - The implementation intentionally rejects cross-page moves for this checkpoint.
  - Task 12 brings the project to the planned 50% checkpoint for agent-first backend workflow testing.

### Task 08 Review - Overflow Report

- Actor: Codex
- Time: 2026-06-02T04:03:27Z
- Summary: Reviewed OpenCode Task 08 implementation and made one small reviewer fix.
- Files reviewed:
  - `backend/main.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by OpenCode:
  - `backend/main.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by Codex during review:
  - `backend/main.py`
  - `action-log.md`
- Review result: accepted after minor fix.
- OpenCode changes accepted:
  - Added `get_overflow_report` MCP handler.
  - Added overflow helpers for target resolution, side amount calculation, and message formatting.
  - Reused Task 07 zero-safe geometry and subtree helpers.
  - Reported `artboard-overflow` and `parent-overflow` with per-side amounts, geometry, boundary metadata, severity, and message.
  - Added `includeArtboard`, `includeParent`, and `minOverflow` options.
  - Added routing in `handle_mcp_tool` and a `TOOLS_LIST` schema entry.
- Codex reviewer fix:
  - Updated `_resolve_diagnostic_target()` so a non-empty `pageId` is validated before `nodeId`, and when both are provided node lookup is constrained to that page.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Focused manual overflow test passed 23/23 checks for:
    - default current-page report
    - artboard right/bottom and left/top amounts
    - parent right/bottom and left/top amounts
    - missing-geometry nodes skipped
    - non-overflowing nodes absent
    - severity escalation for overflow >= 100px
    - page 2 clean/separate targeting
    - page targeting through `nodeId`
    - element-subtree targeting
    - `includeArtboard: false`
    - `includeParent: false`
    - `minOverflow` filtering
    - missing page and node errors
    - valid `pageId` + `nodeId`
    - mismatched `pageId` + `nodeId`
    - invalid `pageId` with valid `nodeId`
    - response shape and item shape
    - read-only behavior preserving document elements
- Notes:
  - Parent overflow uses boundary origin `(0, 0)` and parent width/height, treating child coordinates as parent-relative as specified.

### Task 09 Review - SVG Summary

- Actor: Codex
- Time: 2026-06-02T04:40:10Z
- Summary: Reviewed OpenCode Task 09 implementation. No code fix was needed.
- Files reviewed:
  - `backend/main.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
  - `backend/parse_html.py` for SVG attribute context only
- Files changed by OpenCode:
  - `backend/main.py`
  - `/root/my-project/VibeDesignLocalMCP_task.md`
- Files changed by Codex during review:
  - `action-log.md`
- Review result: accepted.
- OpenCode changes accepted:
  - Added `get_svg_summary` MCP handler.
  - Added helpers for SVG descendant collection, primitive counting, path command counting, point counting, compact item building, and chart hints.
  - Reused existing zero-safe geometry and page-constrained targeting helpers.
  - Summarized SVG roots with geometry, viewBox, primitiveCounts, items, labels, hints, and summary text.
  - Supported page, SVG node, and non-SVG parent subtree targeting.
  - Added routing in `handle_mcp_tool` and a `TOOLS_LIST` schema entry.
- Verification:
  - `python3 -m py_compile backend/document.py backend/main.py backend/parse_html.py` passed.
  - `git diff --check` passed.
  - Focused manual SVG summary test passed 20/20 checks for:
    - default current-page SVG summary
    - primitive counts for rect, circle, path, line, polyline, and text
    - SVG geometry and viewBox
    - bar-chart, circle/scatter, line/axis, and path-heavy hints
    - path `commandCount`
    - polyline `pointCount`
    - labels with text and positions
    - page 2 separate targeting
    - page targeting through `nodeId`
    - direct SVG-node targeting
    - non-SVG parent subtree targeting
    - missing page and node errors
    - invalid page validation before node lookup
    - page-constrained node lookup
    - primitive counts remaining complete when `maxItems` caps items
    - response shape
    - read-only behavior preserving document elements
- Notes:
  - Planner-owned files `architecture.md`, `to-do.md`, and `action-log.md` remain Codex-owned. OpenCode did not edit `architecture.md` or `to-do.md` for Task 09.
