# VibeDesign MCP Tool Schema Audit Roadmap

Purpose: make VibeDesign MCP tools easier and safer for agents to use by aligning the exposed MCP schemas with real backend behavior and observable frontend/export behavior.

This roadmap is documentation-first. Do not change tool behavior during the audit phase.

## Core Question

Does each MCP tool schema accurately tell the agent what the tool can do?

Correct schema means:

- accepted inputs are documented
- defaults are documented
- page/node targeting is clear
- validation behavior is clear
- side effects are clear
- response shape is useful for follow-up actions
- frontend/export pipeline confirms the advertised behavior

## Evaluation Pipeline

Audit each tool against the real pipeline:

```text
Agent-facing MCP schema
  -> MCP route in backend/main.py
  -> handler argument parsing and validation
  -> document model read/mutation
  -> frontend polling/render behavior when relevant
  -> HTML/JSX/save/open/export behavior when relevant
  -> response returned to the agent
```

Do not evaluate schema only against memory or context-window impressions.

## Primary Source Files

- `backend/main.py`
  - `TOOLS_LIST`
  - MCP routing
  - handler implementations
- `backend/document.py`
  - document model behavior
  - save/open/export behavior
- `backend/parse_html.py`
  - HTML/SVG parsing behavior
- frontend canvas/panel files
  - only when schema claims require render, selection, or UI confirmation
- `tests/`
  - regression tests for behavior that should stay stable

## Priority Tool List

Audit these first because they control precision editing or agent repair decisions:

1. `write_html`
2. `update_styles`
3. `set_text_content`
4. `update_svg_attributes`
5. `get_node_info`
6. `get_html`
7. `get_overflow_report`
8. `move_nodes`
9. `duplicate_nodes`
10. `delete_nodes`
11. `rename_nodes`

## Tool-Specific Audit Targets

### write_html

Check:

- `html` parsing behavior
- `targetNodeId` behavior for page IDs vs element IDs
- `pageId` fallback behavior
- `mode` values: `append`, `replace-children`, `replace`
- behavior when target is missing
- behavior when HTML has multiple root nodes
- whether generated IDs are returned
- whether response gives enough node IDs for follow-up edits

### update_styles

Check:

- `nodeIds` validation
- multi-node behavior
- missing-node behavior
- `styles` merge behavior
- `removeStyleKeys` behavior
- CSS-only vs SVG/XML attribute boundary
- response shape

### set_text_content

Check:

- whether `nodeIds` is required and must be non-empty
- whether multiple nodes are supported
- whether it works on any element or only text-like elements
- whether it replaces all text or only direct text
- whether children are preserved
- missing-node behavior
- cross-page lookup behavior
- response shape, especially updated IDs and failures

Schema improvement goal:

- make precise multi-node text editing obvious to the agent
- clarify safe use for selected node IDs
- document response enough for the agent to confirm edits

### update_svg_attributes

Check:

- accepted node types: SVG root and/or SVG descendants
- supported attribute names
- attribute casing behavior
- native `id` behavior
- page scoping behavior
- missing-node behavior
- validation behavior
- response shape
- save/open/export preservation

### get_node_info

Check:

- page ID vs element ID behavior
- omitted `nodeId` behavior
- response fields
- parent/children metadata
- SVG attribute visibility
- whether response has enough data for precise follow-up edits

### get_html

Check:

- current page fallback
- `pageId` behavior
- `nodeId` behavior for page IDs and element IDs
- pretty-print default
- subtree export behavior
- SVG export preservation
- response shape

### get_overflow_report

Check:

- omitted `pageId` behavior
- `nodeId` behavior for page IDs and element IDs
- subtree vs single-node scope
- `includeArtboard` default and meaning
- `includeParent` default and meaning
- `minOverflow` default and units
- overflow side values
- whether returned node IDs can be directly used with repair tools
- whether response gives enough context for the agent to fix layout without guessing

### move_nodes

Check:

- same-page restriction
- `targetParentId` behavior for page IDs vs element IDs
- omitted `targetParentId` behavior
- `pageId` scoping
- `index` behavior
- ancestor/descendant invalid move protection
- response shape

### duplicate_nodes

Check:

- full subtree duplication
- ID remapping behavior
- offset behavior
- parent/children preservation
- SVG/native ID behavior
- response shape and descendant ID maps

### delete_nodes

Check:

- subtree deletion
- parent/children cleanup
- `pageId` scoping
- missing-node behavior
- current selection impact if any
- response shape

### rename_nodes

Check:

- element rename behavior
- page/artboard rename behavior
- `names` map validation
- `pageId` scoping
- missing-node behavior
- response shape

## Audit Output Format

For each tool, record:

```md
## tool_name

Status: OK | Schema incomplete | Schema misleading | Response undocumented | Implementation mismatch

Agent-facing schema:
- description:
- required:
- properties:

Actual behavior:
- accepted inputs:
- defaults:
- validation:
- side effects:
- response shape:

Pipeline verification:
- frontend:
- export/readback:
- tests/manual:

Gaps:
- ...

Recommended schema fix:
- ...
```

## Suggested Task Sequence

### Task 44: MCP Tool Schema Audit Report

No behavior changes.

Deliverable:

- update `doc/vibe-design-mcp-tool-agent-context.md` with audit results
- or create a separate `doc/vibe-design-mcp-tool-schema-audit-report.md`

Scope:

- audit the 11 priority tools only
- mark exact mismatches and unclear schema text
- recommend schema-only fixes

### Task 45: High-Impact Editing Schema Fixes

Schema text only.

Tools:

- `write_html`
- `update_styles`
- `set_text_content`
- `update_svg_attributes`

Verification:

- MCP tool list still loads
- no handler behavior changes
- whitespace check

### Task 46: Inspection And Repair Schema Fixes

Schema text only.

Tools:

- `get_node_info`
- `get_html`
- `get_overflow_report`

Verification:

- tool list still loads
- schema descriptions match audited behavior

### Task 47: Structural Tool Schema Fixes

Schema text only.

Tools:

- `move_nodes`
- `duplicate_nodes`
- `delete_nodes`
- `rename_nodes`

Verification:

- tool list still loads
- schema descriptions match audited behavior

### Task 48: Schema Regression Test

Add tests that verify:

- every routed tool exists in `TOOLS_LIST`
- every `TOOLS_LIST` tool has a route
- priority tools have non-empty meaningful descriptions
- priority mutation tools document required fields
- no stale/dead schema entries exist

### Task 49: Agent Workflow PC Test

Manual workflow:

- create page with nested HTML/SVG
- inspect target nodes
- edit text with `set_text_content`
- replace section with `write_html`
- adjust styles with `update_styles`
- edit SVG with `update_svg_attributes`
- diagnose layout with `get_overflow_report`
- export/read back with `get_html`

Pass condition:

- agent chooses the right tools without guessing
- returned node IDs support precise follow-up edits
- frontend reflects changes
- export/readback matches expected result

## Guardrails

- Do not build Design Mode.
- Do not add new MCP tools during schema cleanup.
- Do not change backend behavior unless the audit finds a real bug and a separate task is assigned.
- Do not use archive repo files as implementation inspiration.
- Keep each task small and reviewable.

