# VibeDesignLocalMCP-2 Architecture

## Current Direction

VibeDesignLocalMCP-2 is an agent-first local design workspace. The core product is not a full manual design tool clone. The priority is a reliable document pipeline that lets an agent create, inspect, patch, validate, save/open, and export HTML/SVG designs with stable node identity.

The active baseline is Tasks 1-52. Tasks 43-66 from the abandoned planner session are not part of this roadmap; the current Tasks 43-52 are the rebuilt stability, MCP schema, and documentation track.

## Active Sources

- Active repo: `VibeDesignLocalMCP-2`
- Active task file: `task.md`
- Active planner log: `action_log2.md`
- Historical log: `archive/action-log.md`

`VibeDesignLocalMCP-archive` is dead history. Do not use it for inspiration or implementation. Only inspect it when explicitly recovering history.

## Non-Goals

- No Design Mode work.
- No broad frontend rebuild.
- No speculative new systems.
- No distro-specific package-manager integration.
- No skills runtime, `.skill` folders, skill loaders, or skill prompts.
- No manual Text/Frame/Rectangle tool restoration.
- No generic manual element dragging or resizing until a deliberate layout mutation model exists.

## Operating Rules

- Assign one narrow task at a time in `task.md`.
- Builder implements only the assigned task and appends a completion report to `task.md`.
- Codex reviews and records decisions in `action_log2.md`.
- Use Ponytail as builder discipline: plan more, write less, reuse existing code/libraries first.
- Ponytail does not override task scope, verification, safety, or Codex review.
- Prefer small foundation and fine-tuning tasks that can be PC-tested.
- Discuss any large round before assigning implementation.

## System Shape

- `backend/`: FastAPI app, active MCP handlers, document model, parser, diagnostics, save/open, export.
- `frontend/`: React/Vite canvas review shell, artboard rendering, layer panel, property panel, selection, pan/zoom.
- `desktop/`: thin pywebview wrapper only.

The backend is the source of truth. The frontend renders and inspects backend state. MCP tools mutate the same document model used by frontend polling, save/open, diagnostics, and export.

## Core Pipeline

```text
agent writes HTML/SVG
        |
        v
write_html parses into document nodes
        |
        v
backend stores stable node tree
        |
        v
agent reads tree/node/html/svg diagnostics
        |
        v
agent patches exact nodes
        |
        v
save/open and export preserve structure
```

The critical invariant remains:

```text
if node.parentId points to a parent, that parent.children contains the node ID
```

## Built Foundation

The accepted foundation now includes:

- parser parent/children consistency
- nested HTML export
- save/open round-trip for Paper HTML
- `write_html` modes: `append`, `replace`, `replace-children`
- targeted `pageId` and `targetNodeId` behavior
- stronger tree, child, node, HTML, JSX, layout, overflow, screenshot, and SVG readback tools
- subtree-safe duplicate, move, rename, and delete tools
- non-destructive style updates and explicit style key removal
- runtime document identity cleanup
- REST error status honesty
- target-aware `update_styles`
- disabled unsafe manual creation/drag/resize paths
- safer selection, layer/canvas sync, and right inspector identity
- SVG export/readback fixes through Task 42
- SVG save/open round-trip regression coverage
- MCP tool schema audit, schema text corrections, and regression coverage
- live MCP agent workflow validation
- active documentation moved under `doc/` with source-audited reference docs

## SVG Model

Backend node IDs are generated VibeDesign IDs. Native HTML/SVG DOM IDs are stored separately in `style["id"]`.

SVG attributes currently live in the element `style` dict so the existing renderer and mutation paths can share one storage shape. Export and JSX paths split SVG/XML attributes from CSS style. `open_document` also preserves SVG/XML attrs when reopening saved Paper HTML.

Important SVG capabilities:

- canonical SVG export for tags such as `linearGradient`, `clipPath`, `foreignObject`, and `textPath`
- native SVG IDs and references preserved
- `update_svg_attributes` mutates SVG/XML attrs by backend node ID
- `get_svg_summary` gives text inspection of SVG primitives
- `validate_svg` checks common SVG issues without mutation

Known SVG limits:

- frontend SVG-native visual selection outline is still limited
- `update_svg_attributes` is permissive about unknown attr keys
- SVG test coverage should be formalized beyond focused manual checks

## Frontend Policy

The current frontend should remain a review and inspection surface:

- render backend pages/artboards
- focus current artboard or fit artboards on startup
- pan/zoom
- safe Select behavior
- layer-to-canvas identity
- inspector identity and safe visual/text edits

Manual creation tools and generic layout mutation stay disabled. Artboard move/resize remains explicit artboard behavior only.

## Verification Policy

Every implementation task should run the smallest meaningful checks:

- backend edits: `python3 -m py_compile backend/parse_html.py backend/document.py backend/main.py`
- frontend edits: `npm run build` from `frontend/`
- whitespace: `git diff --check`
- focused behavioral script/check for the touched path

After a cluster of meaningful user-facing changes, do a PC checklist test before continuing.
