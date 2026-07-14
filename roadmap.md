# VibeDesignLocalMCP-2 Roadmap

## Baseline

Current accepted baseline: Tasks 1-42.

This project restarted from the stable Task 41 state, then Task 42 fixed SVG attributes being dropped when reopening saved Paper HTML. Tasks 43-66 from the abandoned session are intentionally excluded.

## Built

Backend/document foundation:

- HTML parser builds stable `parentId` and `children` relationships.
- Nested export preserves tree structure.
- Paper HTML save/open preserves pages, node IDs, names, nesting, styles, native IDs, and SVG attrs.
- `write_html` supports `append`, `replace`, and `replace-children`.
- `write_html` targets pages and elements.
- `get_tree_summary`, `get_node_info`, `get_children`, `get_html`, and `get_page_html` provide readback.
- `get_jsx` exports nested JSX.
- layout, overflow, screenshot, and SVG diagnostics exist.
- duplicate, move, rename, and delete tools are subtree-aware enough for current use.
- style updates are non-destructive and support explicit key removal.
- REST error responses are more honest.
- runtime document identity cleanup is in place.

Frontend safety foundation:

- broken manual Text, Frame, and Rectangle tools are disabled.
- cursor/move behavior is selection-oriented.
- unsafe manual element drag and resize paths are removed.
- canvas/layer selection identity is stronger.
- right inspector shows stable identity and disables unsafe element layout fields.
- artboard interaction is already safe enough for V1; Task 32.2 strip polish is intentionally skipped.

SVG foundation:

- SVG attrs export as XML/JSX attrs instead of CSS where appropriate.
- native SVG IDs and references are preserved.
- canonical SVG tag names export correctly.
- `foreignObject` and `textPath` parity is handled.
- `update_svg_attributes` exists for SVG/XML attr edits.
- `validate_svg` is read-only and catches common SVG issues.
- backend node IDs are decoupled from native HTML/SVG IDs.
- Paper HTML open now preserves SVG attrs.

## Current Guardrails

- No Design Mode.
- No archive-driven implementation.
- No broad frontend rebuild.
- No speculative feature systems.
- No skills work.
- No manual shape/rectangle toolbar restoration.
- No package-manager-specific app code such as DNF integration.
- Use `task.md` for one active assignment.
- Use `action_log2.md` for planner/reviewer decisions.
- Use Ponytail as a discipline layer, not as permission to skip verification.

## Next Priorities

### 1. Stabilize Tests Around Existing Foundation

Add focused tests for what already exists before adding features.

Candidate tasks:

- Add backend tests for Paper HTML save/open SVG attr round-trip.
- Add tests for native DOM ID versus backend node ID separation.
- Add tests for `update_svg_attributes` export/readback.
- Add tests for `validate_svg` no-mutation behavior.
- Add tests for `write_html` target modes on nested structures.

### 2. Tighten SVG Mutation Contracts

Make current SVG tools sharper without broadening scope.

Candidate tasks:

- Make `update_svg_attributes` report unknown/non-exported attr keys.
- Consider allowlisting SVG attrs only after testing current valid use cases.
- Add readback in `update_svg_attributes` response that separates SVG attrs from CSS style keys.

### 3. Improve Export Confidence

Strengthen current export paths instead of adding new export formats first.

Candidate tasks:

- Audit `export_html`, `get_page_html`, `get_html`, `save_document`, and `get_jsx` parity for nested HTML/SVG.
- Add a small backend smoke script/test: `write_html -> tree -> node html -> page html -> save/open -> compare`.
- Verify non-SVG style export still works after SVG fixes.

### 4. Frontend Fine-Tuning Only

Keep frontend tasks small and PC-testable.

Candidate tasks:

- Audit current artboard/header behavior without rebuilding Task 32.2.
- Improve selection visibility only if it is a real PC-test issue.
- Improve inspector clarity only where it helps exact node targeting.
- Avoid broad UI redesign.

### 5. Documentation Cleanup

Make docs reflect the reset.

Candidate tasks:

- Update README with current run commands and Linux/Fedora-neutral notes.
- Add a short clean-runtime note for `~/.paper_clone/data`.
- Keep old long-form docs archived.

## Deferred

- Design Mode.
- Skills.
- Frontend replacement shell.
- Manual shape toolbar.
- Undo/redo.
- Image export.
- Full PDF/export expansion beyond current stable paths.
- Packaging and desktop polish.

## Suggested Next Task

Task 43 should be a test/stability task, not a feature task.

Recommended Task 43:

```text
Add focused backend regression tests for SVG Paper HTML save/open round-trip.
```

Why:

- Task 42 fixed a real bug.
- The fix is important enough to preserve with tests.
- It is narrow, backend-only, and PC-testable.
- It reinforces the foundation before any new feature work.
