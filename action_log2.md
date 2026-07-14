# Action Log 2

Planner-owned continuation log for VibeDesignLocalMCP work.

`action-log.md` is now archived as the previous long-form log. From this point forward, Codex records new task assignments, reviews, corrections, verification results, and decisions in this file.

OpenCode does not write this file. Codex reviews completed work and records the decision, changed files, verification, and next action.

## 2026-06-23

### Log Split

- Actor: Codex
- Summary: Created `action_log2.md` as the continuation action log.
- Decision:
  - Leave previous `action-log.md` as-is because it has become too long.
  - Record all future planner/reviewer entries in `action_log2.md`.
- Notes:
  - Task 32 and Task 33 were already reconstructed and appended to the previous `action-log.md`.

### Tasks 32-41 Checkpoint Report

- Actor: Codex
- Summary: Added a new checkpoint section to `checkpoint-report.md` covering Tasks 32-41.
- Files changed:
  - `checkpoint-report.md`
  - `action_log2.md`
- Decision:
  - Recommend a PC checkpoint test now because the project has moved from Task 19 to Task 41 with major frontend safety, SVG export, SVG mutation, SVG validation, and parser identity changes.
- PC test focus:
  - generated backend node IDs versus native HTML/SVG IDs
  - SVG render and layer/inspector identity
  - `get_tree_summary`, `get_children`, `get_svg_summary`, and `validate_svg`
  - `update_svg_attributes` by generated backend node ID
  - clean `get_page_html`, `get_jsx`, save/open preservation
  - no direct implementation of manual UI fixes without the four-step diagnostic protocol

## 2026-07-03

### Task 42 Review - Preserve SVG Attributes On Paper HTML Open

- Actor: Codex
- Summary: Fixed the Paper HTML open/save round-trip gap for SVG attributes.
- Files changed:
  - `backend/document.py`
  - `action-log.md` moved into `archive/action-log.md`
  - `action_log2.md`
- Decision:
  - Keep `write_html` unchanged because it already uses the SVG-aware parser.
  - Fix `DocumentStore._parse_element_tree()` so `open_document` preserves SVG/XML attrs when reopening saved Paper HTML.
- Verification:
  - `python3 -m py_compile backend/parse_html.py backend/document.py backend/main.py` passed.
  - Focused save/open round-trip passed for `svg`, `linearGradient`, `clipPath`, `rect`, `path`, and `textPath`.
  - Non-SVG native `id` behavior stayed intact: backend node IDs still come from `data-paper-node`, while native DOM IDs remain in `style["id"]`.

### Builder Process Reset - New OpenCode Session With Ponytail

- Actor: User + Codex
- Summary: Decided to restart builder execution from the accepted Task 42 baseline instead of continuing the old OpenCode session.
- Decision:
  - Start a fresh OpenCode builder session for future tasks.
  - Do not continue the old builder session because it contains abandoned Tasks 43-66 context.
  - Use Ponytail as a builder discipline layer: plan more, write less, reuse existing code/libraries first, and avoid speculative systems.
  - Ponytail does not override `task.md`, Codex scope, verification requirements, or safety checks.
  - Prefer Ponytail lite/full behavior; do not use aggressive cleanup modes unless Codex explicitly asks.
- Project guardrails:
  - Active repo is `VibeDesignLocalMCP-2`.
  - `VibeDesignLocalMCP-archive` is dead history and must not be used for inspiration or implementation.
  - No Design Mode work.
  - Continue with narrow foundation/fine-tuning tasks and PC-testable increments.

### Task 43 Review - SVG Paper HTML Save/Open Regression Tests

- Actor: Codex
- Summary: Reviewed OpenCode Task 43 implementation. No code fix was needed.
- Files reviewed:
  - `tests/test_svg_save_open_roundtrip.py`
  - `task.md`
- Files changed by OpenCode:
  - `tests/test_svg_save_open_roundtrip.py`
  - `task.md`
- Review result: accepted.
- OpenCode changes accepted:
  - Added a plain Python regression test for the Task 42 Paper HTML save/open SVG attribute fix.
  - Covered one in-memory document, one page, one SVG root, SVG descendants, and one non-SVG div.
  - Verified backend node IDs survive through `data-paper-node`.
  - Verified native DOM IDs survive separately in `style["id"]`.
  - Verified SVG attrs survive `_generate_html()` then `_parse_html()`, including `viewBox`, `gradientUnits`, `stopColor`, `clipPathUnits`, `fill`, `clipPath`, `strokeWidth`, `d`, `href`, and `startOffset`.
  - Verified SVG parent/child structure and non-SVG `backgroundColor` round-trip.
- Verification:
  - `python3 -m py_compile backend/parse_html.py backend/document.py backend/main.py tests/test_svg_save_open_roundtrip.py` passed.
  - `python3 tests/test_svg_save_open_roundtrip.py` passed.
  - `git diff --check` passed.
- Notes:
  - No backend production files, frontend files, archived files, or dependency files were changed by OpenCode for Task 43.

### Frontend Dev Server Fix - Bind Vite To Localhost

- Actor: Codex
- Summary: Diagnosed and fixed `npm run dev` failing in the current Termux/proot Linux environment.
- Problem:
  - Plain `npm run dev` failed with `uv_interface_addresses returned Unknown system error 13`.
  - Direct Node repro showed `require("os").networkInterfaces()` fails in this environment.
  - Vite triggered that path while resolving server URLs because `frontend/vite.config.ts` used `host: true`.
- Files changed:
  - `frontend/vite.config.ts`
  - `action_log2.md`
- Fix:
  - Changed Vite dev server host from `true` to `"127.0.0.1"`.
  - This keeps the existing frontend port behavior but avoids network-interface enumeration.
- Verification:
  - Plain `npm run dev` no longer crashes with the network-interface error and starts Vite on a localhost URL.
  - `npm run build` from `frontend/` passed.
  - `git diff --check -- frontend/vite.config.ts` passed.
  - Restored generated `frontend/tsconfig.tsbuildinfo` after build.
- Notes:
  - If port `5175` is already occupied by another terminal session, Vite may still fall back to the next port. Stop the existing dev server before expecting `5175`.

## 2026-07-05

### MCP Tool Schema Audit Planning

- Actor: User + Codex
- Summary: Started a documentation-first audit track for VibeDesign MCP tool schemas.
- Files created:
  - `doc/vibe-design-mcp-tool-agent-context.md`
  - `doc/vibe-design-mcp-tool-schema-audit-roadmap.md`
- Decision:
  - First capture the agent-facing MCP tool context from `backend/main.py` / `TOOLS_LIST`.
  - Then audit schema text against actual handler behavior and observable pipeline behavior before changing schemas.
  - Do not blindly edit MCP schemas from memory or context-window impressions.
- Current schema baseline:
  - 30 MCP tools documented.
  - The initial total was corrected from 29 to 30 after recounting source-backed tool names.
- Priority audit tools:
  - `write_html`
  - `update_styles`
  - `set_text_content`
  - `update_svg_attributes`
  - `get_node_info`
  - `get_html`
  - `get_overflow_report`
  - `move_nodes`
  - `duplicate_nodes`
  - `delete_nodes`
  - `rename_nodes`
- Audit rule:
  - Compare each schema against the full pipeline: MCP schema, route, handler validation, document model read/mutation, frontend/render behavior when relevant, export/save/open behavior when relevant, and response shape.
- Guardrails:
  - Documentation/audit first.
  - No Design Mode.
  - No new MCP tools.
  - No backend behavior changes unless a separate bug-fix task is assigned.
  - Do not use `VibeDesignLocalMCP-archive` for implementation inspiration.

### Task 44 Review - MCP Tool Schema Audit Report

- Actor: Codex
- Summary: Reviewed OpenCode Task 44 audit report after one requested revision.
- Files reviewed:
  - `doc/vibe-design-mcp-tool-schema-audit-report.md`
  - `task.md`
- Files changed by OpenCode:
  - `doc/vibe-design-mcp-tool-schema-audit-report.md`
  - `task.md`
- Review result: accepted.
- Initial review finding:
  - The first report missed that `get_html` exposes `pretty` in the MCP schema but active `_get_html()` does not pass it to `doc_store.get_node_html()`.
  - OpenCode revised the report to mark `get_html` as `Schema misleading`.
- Accepted audit outcome:
  - Task 45 candidates: `write_html`, `update_styles`, `set_text_content`, `update_svg_attributes`.
  - `get_html` needs backend/schema alignment because `pretty` is currently a dead schema flag.
  - Task 46 candidates: `get_node_info`, `get_overflow_report`.
  - Task 47 candidates: `move_nodes`, `duplicate_nodes`, `delete_nodes`.
  - `rename_nodes` needs no immediate schema fix.
- Verification:
  - `git diff --check -- doc/vibe-design-mcp-tool-schema-audit-report.md task.md` passed.
- Notes:
  - No backend behavior was changed in Task 44.

### Task 45 Review - High-Impact MCP Editing Schema Text

- Actor: Codex
- Summary: Reviewed OpenCode Task 45 schema text fixes after one requested revision.
- Files reviewed:
  - `backend/main.py`
  - `task.md`
- Files changed by OpenCode:
  - `backend/main.py`
  - `task.md`
- Review result: accepted.
- Accepted changes:
  - Improved `write_html` MCP schema text with target mode support, non-empty HTML requirement, zero-parse behavior, response fields, and `deleted` IDs only for `replace` mode.
  - Improved `update_styles` schema text with deep-merge behavior, artboard/page routing, multi-node support, response shape, and partial-success behavior.
  - Improved `set_text_content` schema text with multi-node support, silent missing-node skips, preserved children/style/identity, and empty-string clearing behavior.
  - Improved `update_svg_attributes` schema text with SVG-node requirement, SVG/XML attribute examples, non-empty attrs requirement, accepted value types, native SVG `id` storage as `style["id"]`, and response shape.
- Verification:
  - `python3 -m py_compile backend/main.py` passed.
  - `PYTHONPATH=backend` schema import/count check passed with 30 tools.
  - `git diff --check -- backend/main.py task.md` passed.
- Notes:
  - No handler behavior was changed.
  - `get_html.pretty` remains deferred for a later backend/schema alignment task.

### Task 46 Review - MCP Inspection And Diagnostic Schema Text

- Actor: Codex
- Summary: Reviewed OpenCode Task 46 schema text fixes for read-only inspection/export/diagnostic tools.
- Files reviewed:
  - `backend/main.py`
  - `task.md`
- Files changed by OpenCode:
  - `backend/main.py`
  - `task.md`
- Review result: accepted.
- Accepted changes:
  - Improved `get_node_info` schema text with current-page fallback, page response fields, element response fields, and invalid-node error behavior.
  - Improved `get_html` schema text with response shape, targeting rules, page-scoped lookup behavior, and error behavior.
  - Removed dead `pretty` property from `get_html` schema because the active handler ignores it.
  - Improved `get_overflow_report` schema text with defaults, target behavior, `minOverflow` coercion, response fields, and overflow item shape.
- Verification:
  - `python3 -m py_compile backend/main.py` passed.
  - `PYTHONPATH=backend` schema import/count check passed with 30 tools.
  - Confirmed `pretty` is absent from `get_html` schema.
  - `git diff --check -- backend/main.py task.md` passed.
- Notes:
  - No handler behavior was changed.
  - Task 47 structural tools remain untouched.

### Task 47 Review - MCP Structural Tool Schema Text

- Actor: Codex
- Summary: Reviewed OpenCode Task 47 schema text fixes for structural mutation tools.
- Files reviewed:
  - `backend/main.py`
  - `task.md`
- Files changed by OpenCode:
  - `backend/main.py`
  - `task.md`
- Review result: accepted.
- Accepted changes:
  - Improved `move_nodes` schema text with same-page behavior, cycle protection, target lookup behavior, index behavior, and response shape.
  - Improved `duplicate_nodes` schema text with non-empty node IDs, partial success, root-only offset behavior, and response shape including descendant ID maps.
  - Improved `delete_nodes` schema text with subtree deletion, non-empty node IDs, missing-node partial success, ancestor/descendant dedup, response shape, and page deletion exclusion.
- Verification:
  - `python3 -m py_compile backend/main.py` passed.
  - `PYTHONPATH=backend` schema import/count check passed with 30 tools.
  - `git diff --check -- backend/main.py task.md` passed.
- Notes:
  - No handler behavior was changed.
  - `rename_nodes` was left untouched as intended.

### Task 48 Review - MCP Tool Schema Regression Tests

- Actor: Codex
- Summary: Reviewed OpenCode Task 48 regression test for MCP tool schema inventory and routing consistency.
- Files reviewed:
  - `tests/test_mcp_tool_schema.py`
  - `task.md`
- Files changed by OpenCode:
  - `tests/test_mcp_tool_schema.py`
  - `task.md`
- Review result: accepted.
- Accepted changes:
  - Added a plain Python regression test for `TOOLS_LIST` inventory structure, uniqueness, and expected count of 30 tools.
  - Added bidirectional route coverage checks between `TOOLS_LIST` and `handle_mcp_tool`, scoped to the function body.
  - Added priority schema term checks covering Tasks 45-47 improvements.
  - Added required-field checks for key mutation tools.
  - Added a guard that `get_html.pretty` remains absent from the active schema.
- Verification:
  - `python3 -m py_compile backend/main.py tests/test_mcp_tool_schema.py` passed.
  - `python3 tests/test_mcp_tool_schema.py` passed and printed `All MCP tool schema regression checks passed.`
  - `git diff --check -- tests/test_mcp_tool_schema.py task.md` passed.
- Notes:
  - No runtime behavior or schema text was changed in Task 48.

### Task 49 Review - MCP Schema Agent Workflow PC Test

- Actor: Codex
- Summary: Reviewed OpenCode Task 49 manual MCP workflow validation report.
- Files reviewed:
  - `task.md`
- Files changed by OpenCode:
  - `task.md`
- Review result: accepted.
- Accepted workflow result:
  - Backend and frontend were already running, per user confirmation.
  - OpenCode used the existing services and did not start or restart servers.
  - Workflow exercised `write_html`, `get_node_info`, `get_html`, `set_text_content`, `update_styles`, `update_svg_attributes`, and `get_overflow_report`.
  - Supporting setup used `create_artboard` to isolate the test page.
  - Final readback confirmed text edit, section replacement, style edit, and SVG attribute edit.
  - `get_html` worked without `pretty`.
- Verification:
  - `python3 tests/test_mcp_tool_schema.py` passed.
  - `git diff --check -- task.md` passed.
- Result:
  - PASS. The improved MCP schemas supported a precise agent workflow without schema confusion.
- Notes:
  - OpenCode reported 3 pre-existing artboards with the same ID `test-page-001`; not caused by Task 49, but worth tracking if duplicate page IDs affect future workflows.

### Tasks 33-49 Checkpoint Report

- Actor: Codex
- Summary: Added a new PC checkpoint section to `checkpoint-report.md` covering Tasks 33-49.
- Files changed:
  - `checkpoint-report.md`
  - `action_log2.md`
- Decision:
  - Recommend a PC checkpoint test now because Tasks 33-49 changed the SVG parser/export/mutation pipeline, SVG save/open preservation, MCP schema clarity, route/schema regression coverage, and real agent workflow reliability.
- PC test focus:
  - SVG/native ID preservation versus generated backend node IDs
  - `update_svg_attributes`, `validate_svg`, `get_svg_summary`, and export/readback behavior
  - `get_html` working without the removed `pretty` schema parameter
  - schema regression test and SVG round-trip test passing on PC
  - real agent workflow using write/inspect/edit/diagnose/export tools without schema confusion
- Notes:
  - Duplicate `test-page-001` artboards are not treated as an issue for this checkpoint.
