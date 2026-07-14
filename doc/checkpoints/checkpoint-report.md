# VibeDesignLocalMCP 50% Checkpoint Report

Date: 2026-06-02

## Status

VibeDesignLocalMCP is now at the planned agent-first backend workflow checkpoint, roughly 50% complete.

The priority was not full Paper UI parity. The priority was to make the MCP/document/export loop reliable enough for an agent to build, inspect, patch, and export multi-page report designs without depending only on visual guessing.

## New Features

- `write_html` now supports targeted document mutations:
  - `append`
  - `replace-children`
  - `replace`
  - `pageId`
  - `targetNodeId`
- `get_html` returns clean exported HTML for current page, a page, or an element subtree.
- `get_page_html` returns clean exported HTML for one artboard/page.
- `get_layout_diagnostics` reports likely layout issues:
  - missing dimensions
  - zero-size nodes
  - off-artboard nodes
  - suspicious positions
  - parent overflow
  - text overflow
  - sibling overlap
- `get_overflow_report` reports focused parent/artboard overflow with per-side amounts.
- `get_svg_summary` summarizes inline SVG/chart content:
  - primitive counts
  - rect/circle/line/path/polyline/text details
  - labels
  - chart-like hints
- `get_screenshot` now returns honest stored screenshot metadata and clear missing-screenshot errors.
- `duplicate_nodes` now duplicates full subtrees and returns `descendantIdMap`.
- `move_nodes` supports same-page reorder and reparent operations while preserving subtrees.
- `rename_nodes` now renames both element nodes and page/artboard nodes with page-aware targeting.
- Element names now round-trip through `export_html`, `save_document`, `open_document`, `get_html`, and `get_page_html`.
- `get_jsx` now returns nested JSX with valid React style object syntax and page/node targeting.
- `update_styles` now supports explicit `removeStyleKeys` for safe removal of stale style keys such as `left` and `top`.

## Fine-Tuned Features

- `get_tree_summary` now returns a useful hierarchy with IDs, tags, geometry, text snippets, parent/child data, and depth control.
- `get_node_info` now returns detailed page/element data including parent IDs, child IDs, child counts, style, text, and geometry.
- `get_children` now returns real direct children for pages, elements, and SVG nodes.
- `export_html` now preserves nested content, SVG children, text, escaped HTML, and page isolation.
- `save_document` / `open_document` now round-trip exported VibeDesign HTML with page metadata, nested elements, styles, text, and SVG.
- Element `type` inference is now stable between `write_html` and `open_document`, including links, headings, containers, and SVG primitives.
- `update_styles` now patches style dictionaries instead of replacing them wholesale.
- `desktop/main.py` now points to frontend port `5175`.
- Main docs were translated to English for easier testing and maintenance.

## Refined / Fixed Behavior

- Parser tree consistency was fixed:
  - `parentId` points to the parent.
  - parent `children` contains the child ID.
- Export now walks each page's own element tree instead of leaking content from the current page.
- Style export now converts camelCase keys such as `fontSize` to CSS keys such as `font-size`.
- Save/open skips `data-paper-ui` editor-only content.
- `write_html replace` no longer duplicates nested descendants in the parent child list.
- `pageId + nodeId` targeting was repeatedly tightened:
  - validate `pageId` first
  - constrain node lookup to that page
  - return clear page/node mismatch errors
- Screenshot readback no longer pretends to capture pixels when none were posted by the frontend.
- Page-root duplicated nodes omit `parentId`, matching the existing root-node convention.
- `move_nodes` rejects cross-page moves and cycle moves without mutation.
- `delete_nodes` now removes whole subtrees and cleans remaining references.
- Element names now serialize as `data-paper-name` and parse back from saved HTML.
- SVG primitives now get stable SVG-specific types such as `svg-rect`, `svg-path`, and `svg-text`.
- Style repair can now merge new style values and explicitly remove old keys without losing unrelated visual styles.

## Agent-First Workflow Now Supported

```text
create_artboard
-> write_html
-> get_tree_summary / get_node_info / get_children
-> get_html / get_page_html
-> get_layout_diagnostics / get_overflow_report / get_svg_summary
-> duplicate_nodes / move_nodes / update_styles / targeted write_html patch
-> get_jsx / export_html
```

This is the core loop to test on PC.

## Known Limitations

- `export_pdf` is intentionally postponed. It needs browser/PDF dependencies and cross-platform testing.
- Image export / PNG export is not implemented yet.
- Visibility/lock behavior is not fully implemented.
- Undo/redo for MCP mutations is not implemented.
- Duplicate MCP backend paths still exist and need consolidation later:
  - `backend/main.py`
  - `backend/mcp_server.py`
  - `backend/handlers/mcp_handler.py`
- There is no full automated regression test suite yet.

## PC Test Checklist

1. Start backend and frontend.
2. Open the desktop/web UI at frontend port `5175`.
3. Create one or more artboards.
4. Use `write_html` to add nested HTML and inline SVG.
5. Use `get_tree_summary`, `get_node_info`, and `get_children` to inspect structure.
6. Use `get_html` and `get_page_html` to read back clean HTML.
7. Use `get_layout_diagnostics`, `get_overflow_report`, and `get_svg_summary` on report-like content.
8. Duplicate a card/section/chart with `duplicate_nodes` and edit cloned descendants using `descendantIdMap`.
9. Move/reparent nodes with `move_nodes`.
10. Export with `export_html` and inspect the saved output.
11. Rename elements/pages, then save and reopen to confirm names survive round-trip.
12. Misplace an element, then repair it with `update_styles` plus `removeStyleKeys` and `move_nodes`.
13. Use `get_jsx` to verify nested JSX, style syntax, and SVG child output.

## Recommended Next Tasks After PC Testing

- Fix any PC/cross-platform issues found during testing.
- Add a small regression test suite for parser/document/export/MCP flows.
- Add image export.
- Add PDF export near the end, after browser dependency strategy is clear.

---

# VibeDesignLocalMCP Checkpoint - Tasks 19-32

Date: 2026-06-23

## Status

The last serious PC test was around Task 19. Since then, Tasks 20-32 changed enough frontend and backend behavior that a new PC checkpoint test is recommended before continuing deeper into Design Mode or additional SVG/frontend work.

This checkpoint does not mean the frontend is complete. It means the project has moved from backend editing repair into frontend safety, selection identity, inspector safety, and Design Mode/SVG planning. A real PC test should verify that the app still feels usable after the safety changes.

## What Changed Since Task 19

- REST routes now return clearer HTTP errors for failed backend mutations instead of silently returning `200 OK`.
- `update_styles` routing was corrected so page/artboard updates and element CSS updates do not steal keys from each other.
- Broken manual creation tools were disabled from normal UI access:
  - text
  - frame
  - rectangle
- Cursor/select mode was made selection-only.
- Manual selected-element resize handles and resize mutation paths were removed.
- Startup viewport behavior now focuses the current page once, with fit-all fallback for invalid current pages.
- Canvas, layer panel, and store selection behavior were tightened around one selection contract:
  - element selection clears artboard selection
  - artboard selection clears element selection
  - empty canvas click clears both
- Layer selection and canvas selection now use the same `selectElement()` path.
- Layer ancestor expansion now keeps selected nested nodes visible.
- Selection outline behavior was fixed for flow/static elements by adding render-only positioning context when needed.
- The right inspector now resolves selected elements across all pages, not only the current page.
- The right inspector shows read-only identity metadata for selected elements/artboards.
- Unsafe element layout inputs in the inspector were disabled.
- Missing/stale selected node IDs now show an explicit missing-selection state.
- Dead draw/drag/mutation paths were removed from `Canvas.tsx`.
- Artboard interaction was diagnosed as acceptable for V1:
  - content click selects artboard
  - header drag moves artboard
  - handles resize artboard
  - normal content clicks do not move or resize
- Design Mode V1 architecture was documented:
  - fixed right-panel prompt
  - backend endpoint
  - tmux bridge into a persistent agent session
  - existing MCP tools perform edits
  - frontend polling/revision detects completion
- Skills were explicitly deferred until after V1 core.
- SVG pipeline direction was clarified as agent-first, with SVG-specific tools planned after diagnosis.

## Files Touched In This Checkpoint Range

- `backend/main.py`
- `frontend/src/App.tsx`
- `frontend/src/bridge/api.ts`
- `frontend/src/canvas/Canvas.tsx`
- `frontend/src/canvas/Element.tsx`
- `frontend/src/canvas/viewport.ts`
- `frontend/src/panels/LayerPanel.tsx`
- `frontend/src/panels/PropertyPanel.tsx`
- `frontend/src/store/editorStore.ts`
- `frontend/src/toolbar/Toolbar.tsx`
- `doc/architecture.md`
- `to-do.md`
- `action-log.md`
- `design-mode.md`

## PC Test Recommendation

Yes, test on PC now.

The reason is not only the number of tasks. The reason is the type of changes: selection, layer sync, inspector resolution, viewport focus, disabled manual tools, and canvas cleanup all affect the human UI experience. These are exactly the kinds of changes that can pass builds but still feel wrong in a real browser.

## PC Test Checklist - Tasks 19-32

1. Start backend and frontend.
2. Open the frontend in a normal desktop browser.
3. Confirm the initial viewport focuses a valid current artboard.
4. Confirm the Fit button still fits all artboards.
5. Click an artboard content area and confirm the artboard selects without moving.
6. Click empty canvas outside artboards and confirm selection clears.
7. Click nested elements on canvas and confirm the correct layer row/inspector identity appears.
8. Click nested layer rows and confirm the correct canvas element is selected.
9. Confirm selected layer ancestors expand so the selected child is visible.
10. Confirm selected flow/static elements show a visible outline.
11. Confirm SVG child selection identity is stable, while noting SVG-native visual outline is still a known limitation.
12. Confirm Text, Frame, and Rectangle tools are not available from the normal toolbar.
13. Confirm `R`, `T`, and `F` shortcuts no longer activate disabled creation tools.
14. Confirm the Select tool does not drag or mutate elements.
15. Confirm selected element resize handles are gone.
16. Confirm artboard header drag still moves the artboard.
17. Confirm artboard resize handles still resize the artboard.
18. Confirm the right inspector shows the selected node ID, name, type/tag, parent ID, children count, and owning artboard where applicable.
19. Confirm element layout fields such as `left`, `top`, `width`, and `height` are read-only/disabled in the inspector.
20. Confirm text editing and safe visual controls still work where they are intentionally enabled.
21. Select elements across multiple artboards and confirm the inspector resolves the correct owning artboard.
22. Trigger or simulate a stale/missing selection and confirm the inspector shows an explicit missing-selection warning instead of silently showing the wrong artboard.
23. Export/read back selected content and confirm export target artboard matches the selected element's owning page.
24. Do a short real-world agent workflow:
    - agent creates a page with nested HTML/SVG
    - user selects nodes in the UI
    - agent edits by node ID using MCP
    - frontend polling reflects the changes

## Known Limitations At This Checkpoint

- Frontend is not product-complete.
- Design Mode UI and backend tmux bridge are not implemented yet.
- SVG-native selection outline/highlight is not implemented yet.
- Manual shape/text/frame creation tools are intentionally disabled.
- Export/PDF polish is still future work.
- Full automated regression coverage is still missing.
- Accumulated uncommitted changes span many tasks, so `git diff` must be interpreted by task scope, not as one single task diff.

## Recommended Next Step

Run this PC checkpoint before assigning another broad frontend feature. If PC testing exposes human UI bugs, diagnose them with the established four-step protocol before implementing fixes:

```text
agent creates fresh page
-> user uses text/manual UI path
-> user moves/selects one element
-> agent performs an edit
-> compare logs and document state across all paths
```

---

# VibeDesignLocalMCP Checkpoint - Tasks 32-41

Date: 2026-06-23

## Status

Yes, test on PC now.

The last PC test was around Task 19. Tasks 20-32 changed the frontend safety/selection shell. Tasks 32-41 then changed the SVG and parser identity pipeline substantially. Together, that is enough surface area that real PC/browser testing is the right next move before assigning more broad implementation work.

This checkpoint still does not mean the app is complete. It means the agent-first SVG pipeline is now strong enough to validate in a real browser/workspace loop.

## What Changed Since Task 32

- Task 33 diagnosed the current SVG representation:
  - parse/store and frontend SVG render were mostly functional
  - backend export was the critical breakage
- SVG HTML export now emits SVG attrs as native XML attributes instead of CSS style entries.
- JSX export now emits SVG attrs as React-compatible JSX attrs instead of CSS style object entries.
- Native SVG `id` attrs now round-trip for refs such as gradients, clip paths, masks, symbols, and text paths.
- Canonical SVG tag names now export correctly:
  - `linearGradient`
  - `radialGradient`
  - `clipPath`
  - `foreignObject`
  - `textPath`
- Added `update_svg_attributes` MCP tool for direct SVG/XML attr mutation.
- Added `foreignObject` and `textPath` tag parity across active SVG export/mutation paths.
- Added missing textPath/text attrs:
  - `startOffset`
  - `textLength`
  - `lengthAdjust`
  - `method`
  - `spacing`
  - `side`
- Added read-only `validate_svg` MCP diagnostic tool:
  - malformed/missing `viewBox`
  - missing refs
  - duplicate native SVG IDs
  - missing primitive attrs
  - simple numeric viewBox bounds warnings
- Parser backend node IDs are now decoupled from native HTML/SVG `id` attrs:
  - backend node ID is generated and unique
  - native `id` is preserved in `style["id"]`
  - `data-paper-node` remains the backend target ID
  - native `id="..."` still exports
- `validate_svg` now avoids false missing-ref reports for hex colors like `fill="#111827"`.

## Files Touched In This Checkpoint Range

- `backend/parse_html.py`
- `backend/document.py`
- `backend/main.py`
- `frontend/src/canvas/Element.tsx` (review context)
- `frontend/src/panels/LayerPanel.tsx` (review context)
- `frontend/src/store/editorStore.ts` (review context)
- `frontend/src/types.ts` (review context)
- `doc/architecture.md`
- `to-do.md`
- `design-mode.md`
- `action-log.md`
- `action_log2.md`

## PC Test Recommendation

Yes. Run a PC checkpoint test before assigning more backend/frontend features.

Priority is not visual polish. Priority is verifying the end-to-end agent loop:

```text
agent writes HTML/SVG
-> backend parses native layers
-> UI renders selectable nodes
-> agent inspects IDs/tree/SVG diagnostics
-> agent edits by generated backend node ID
-> clean HTML/JSX export preserves native IDs and refs
```

## PC Test Checklist - Tasks 32-41

1. Start backend and frontend on PC.
2. Open the frontend in a normal desktop browser.
3. Create a fresh artboard/page through MCP.
4. Use `write_html` to add a mixed HTML/SVG sample:
   - a normal HTML wrapper with native `id="hero"`
   - inline `<svg id="chart" viewBox="0 0 100 100">`
   - `<defs>` with `linearGradient id="grad-a"`
   - `<rect fill="url(#grad-a)">`
   - `<clipPath id="clip-a">`
   - `<textPath href="#path-a" startOffset="50%">`
   - two SVG nodes intentionally sharing the same native id for duplicate-id validation
5. Confirm the frontend renders the SVG.
6. Select the SVG root and child SVG nodes where the current frontend allows it.
7. Confirm layer panel and inspector show generated backend node IDs, not native HTML/SVG IDs.
8. Run `get_tree_summary` and confirm tree IDs are generated backend IDs.
9. Run `get_node_info` on SVG child nodes and confirm `style["id"]` contains native SVG IDs where applicable.
10. Run `get_children` on the SVG root and confirm children are generated backend IDs.
11. Run `get_svg_summary` and confirm primitives are visible.
12. Run `validate_svg` on the SVG root:
    - duplicate native SVG IDs should report `duplicate_svg_id`
    - valid `url(#grad-a)` refs should not report missing refs
    - intentionally missing refs should report `missing_ref_target`
13. Use `update_svg_attributes` on a generated backend node ID:
    - change `rect` `fill`, `x`, `width`, or `rx`
    - change `path` `d`
    - change `textPath` `startOffset`
14. Confirm frontend visually updates after backend poll/sync.
15. Run `get_page_html` and verify:
    - `data-paper-node` is generated backend ID
    - native `id="..."` is preserved
    - SVG attrs are XML attrs, not CSS style entries
    - non-SVG native `id` does not appear as CSS `id: ...`
16. Run `get_jsx` and verify:
    - SVG attrs are JSX props
    - `strokeWidth`, `viewBox`, `startOffset` use camelCase
    - non-SVG native `id` is a prop, not inside `style={{ }}`
17. Save and reopen the document.
18. After reopen, confirm:
    - backend node IDs are still generated IDs from `data-paper-node`
    - native IDs remain in exported output
    - duplicate backend node IDs are not introduced
    - `validate_svg` still sees duplicate native SVG IDs where intentionally present
19. Do one short real-world agent workflow:
    - ask the agent to create a small chart/card/report section
    - inspect it with tree/SVG tools
    - patch one SVG element by ID
    - validate and export
20. If manual UI bugs appear, stop and use the four-step diagnosis protocol before assigning fixes.

## Known Limitations At This Checkpoint

- Frontend is still not product-complete.
- Design Mode UI and tmux bridge are documented but not implemented.
- SVG-native visual selection/highlight may still be limited.
- Manual shape/text/frame creation tools remain intentionally disabled.
- `export_pdf` remains postponed.
- Full regression tests are still not part of the repo.
- Accumulated uncommitted changes still span many tasks, so `git diff` must be read by task scope.

## Recommended Next Step

Run the PC test now.

If the PC test passes, the project can continue with the next planned layer:

- either Design Mode V1 plumbing,
- or focused frontend selection/highlight polish,
- or a small automated regression test suite for the new SVG/parser/export pipeline.

If the PC test fails, do not jump straight into fixes. Use the required diagnostic sequence:

```text
agent creates fresh page
-> user uses one manual UI action
-> user moves/selects one element
-> agent edits same page
-> compare backend document ID, page ID, node ID, coordinates, and styles
```

---

# VibeDesignLocalMCP Checkpoint - Tasks 33-49

Date: 2026-07-06

## Status

Test on PC now.

The previous completed PC test covered Tasks 19-32 and passed. Tasks 33-49 then changed the SVG/parser/export pipeline, added SVG mutation/validation support, fixed SVG save/open round-trip coverage, corrected the Vite dev-server binding for this Termux/proot environment, audited and improved MCP tool schemas, added schema regression tests, and completed one real MCP agent workflow validation.

This checkpoint is not about new UI features. It is a foundation checkpoint: verify that the agent-first MCP pipeline remains reliable in the actual browser + backend + frontend environment.

## What Changed Since Task 32

- SVG representation was diagnosed before implementation.
- HTML export now emits SVG attributes as native XML attributes instead of CSS style entries.
- JSX export now emits SVG attributes as React-compatible props.
- Canonical SVG tag output was improved for tags such as `linearGradient`, `clipPath`, `foreignObject`, and `textPath`.
- Native HTML/SVG `id` attrs are preserved separately from generated backend node IDs:
  - backend targeting uses generated `data-paper-node` IDs
  - native DOM/SVG IDs live in `style["id"]`
  - export/readback preserves native IDs
- `update_svg_attributes` was added for direct SVG/XML attribute mutation by generated backend node ID.
- `validate_svg` was added as a read-only SVG diagnostic tool.
- SVG validation was tightened to avoid false missing-ref reports for color hex values.
- `DocumentStore._parse_element_tree()` was fixed so reopening saved Paper HTML preserves SVG/XML attrs.
- A regression test now covers Paper HTML save/open SVG attr round-trip.
- Vite dev server was fixed for the current Termux/proot environment by binding to `127.0.0.1`.
- MCP tool schemas were audited against the full pipeline:
  - schema
  - `handle_mcp_tool` route
  - backend handler
  - document/parser/export behavior
  - response shape
  - real agent follow-up workflow
- MCP schema text was improved for high-impact editing tools:
  - `write_html`
  - `update_styles`
  - `set_text_content`
  - `update_svg_attributes`
- MCP schema text was improved for inspection/export/diagnostic tools:
  - `get_node_info`
  - `get_html`
  - `get_overflow_report`
- The dead `pretty` parameter was removed from the active `get_html` schema because the handler ignored it.
- MCP schema text was improved for structural tools:
  - `move_nodes`
  - `duplicate_nodes`
  - `delete_nodes`
- `tests/test_mcp_tool_schema.py` was added to lock the 30-tool schema inventory, route coverage, priority schema terms, required fields, and `get_html.pretty` removal.
- A real MCP workflow test passed using:
  - `write_html`
  - `get_node_info`
  - `get_html`
  - `set_text_content`
  - `update_styles`
  - `update_svg_attributes`
  - `get_overflow_report`

## Files Touched In This Checkpoint Range

- `backend/main.py`
- `backend/document.py`
- `backend/parse_html.py`
- `frontend/vite.config.ts`
- `tests/test_svg_save_open_roundtrip.py`
- `tests/test_mcp_tool_schema.py`
- `task.md`
- `action_log2.md`
- `checkpoint-report.md`
- `doc/MCP-tool-schema-audit/mcp-tool-audit-final-report.md`
- `doc/MCP-tool-schema-audit/vibe-design-mcp-tool-agent-context.md`
- `doc/MCP-tool-schema-audit/vibe-design-mcp-tool-schema-audit-report.md`
- `doc/MCP-tool-schema-audit/vibe-design-mcp-tool-schema-audit-roadmap.md`

## PC Test Recommendation

Yes. Run a PC checkpoint test for Tasks 33-49 before assigning the next feature layer.

The reason is that Tasks 33-49 changed the reliability layer agents depend on: SVG parsing/export, SVG mutation, save/open preservation, schema clarity, route coverage, and real workflow confirmation. A PC test should confirm the backend, frontend, MCP server, and agent all agree in a real session.

## PC Test Checklist - Tasks 33-49

1. Start backend and frontend on PC.
2. Confirm frontend starts with normal `npm run dev` and binds to a localhost URL without needing `--host 127.0.0.1`.
3. Open the frontend in a normal desktop browser.
4. Run `python3 tests/test_svg_save_open_roundtrip.py` and confirm it passes.
5. Run `python3 tests/test_mcp_tool_schema.py` and confirm it prints `All MCP tool schema regression checks passed.`
6. Create a fresh artboard/page through MCP.
7. Use `write_html` to add mixed HTML/SVG content with:
   - nested HTML structure
   - visible text
   - native HTML `id`
   - inline SVG root with native `id`
   - at least one editable SVG child such as `rect` or `path`
   - at least one SVG ref case such as `linearGradient`, `clipPath`, or `textPath` if practical
8. Confirm the frontend renders the HTML/SVG content.
9. Select or inspect SVG root and child nodes where the frontend allows it.
10. Confirm layer/inspector identity uses generated backend node IDs, not native DOM/SVG IDs.
11. Run `get_tree_summary` and confirm generated backend IDs appear in the tree.
12. Run `get_node_info` on HTML and SVG nodes and confirm:
    - generated backend ID is the target ID
    - native `id` is preserved in `style["id"]` where applicable
    - children/parent/page fields are useful for follow-up edits
13. Run `get_children` on an SVG root and confirm direct child IDs are generated backend IDs.
14. Run `get_svg_summary` and confirm SVG primitives are visible enough for agent inspection.
15. Run `validate_svg` on the SVG root and confirm valid refs are not falsely reported missing.
16. Use `update_svg_attributes` on a generated backend SVG node ID and confirm the frontend updates after polling/sync.
17. Use `set_text_content` on a selected text-bearing node and confirm only that node changes.
18. Use `write_html` with `replace` or `replace-children` on one selected section and confirm only that section changes.
19. Use `update_styles` on one or more nodes and confirm styles merge without wiping unrelated style keys.
20. Use `get_overflow_report` and confirm the response includes checked node count, overflow count, and usable node/geometry context when overflow exists.
21. Use `get_html` without `pretty` and confirm final readback includes:
    - text edit
    - section replacement
    - style edit
    - SVG attr edit
    - correct page/subtree target
22. Run `get_page_html` and confirm SVG attrs export as XML attrs, not CSS style entries.
23. Run `get_jsx` and confirm SVG attrs export as JSX props such as `viewBox`, `strokeWidth`, and `startOffset` where applicable.
24. Save and reopen the document.
25. After reopen, confirm:
    - generated backend node IDs remain targetable through `data-paper-node`
    - native IDs remain in exported output
    - SVG/XML attrs survive reopen
    - no duplicate backend node IDs are introduced
26. Run a short real agent workflow:
    - agent creates a nested HTML/SVG section
    - agent inspects exact nodes
    - agent edits text by node ID
    - agent edits SVG attrs by node ID
    - agent runs overflow diagnostics
    - agent exports/readbacks the final result
27. Confirm the agent does not need to guess tool parameters after the schema audit.
28. Confirm mutation responses provide enough IDs and response fields for precise follow-up edits.
29. Confirm no frontend regression from Tasks 19-32 appears while testing the Tasks 33-49 workflow.
30. Record pass/fail notes and any issue with exact page ID, node ID, tool call, response, and frontend behavior.

## Known Limitations At This Checkpoint

- Frontend is still not product-complete.
- Design Mode is explicitly not being built right now.
- SVG-native visual selection/highlight may still be limited.
- Manual shape/text/frame creation tools remain intentionally disabled.
- `export_pdf` remains postponed.
- The codebase still has accumulated uncommitted changes across many tasks, so `git diff` must be interpreted by task scope.
- Duplicate native IDs can exist intentionally for SVG validation tests. Do not treat native-ID duplicates as backend node-ID duplicates.
- Duplicate `test-page-001` artboards reported during Task 49 are not treated as an issue for this checkpoint.

## Pass Criteria

The Tasks 33-49 PC checkpoint passes if:

- both regression tests pass
- frontend starts and renders the test page
- generated backend IDs and native DOM/SVG IDs remain separate
- SVG mutation, validation, export, save, and reopen behave as expected
- `get_html` works without `pretty`
- the real agent workflow can complete without schema confusion
- final readback matches the intended edits

## Recommended Next Step

Run this PC checkpoint before starting the next feature.

If it passes, continue with small foundation or polish tasks. If it fails, diagnose the exact failing pipeline hop before assigning a fix:

```text
schema/tool call
-> route
-> handler
-> document model
-> frontend render or export/readback
-> agent follow-up behavior
```
