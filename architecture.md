# VibeDesignLocalMCP Architecture

## Direction

VibeDesignLocalMCP should become an agent-first Paper-like design workspace.

Paper is roughly half AI-agent workflow and half human collaboration. VibeDesignLocalMCP should invert that priority: the AI agent is the primary user, and the human UI is the visual workspace, inspection surface, and manual correction layer.

The product goal is not to clone every Paper desktop feature first. The goal is to make the MCP/document/export loop reliable enough that an agent can build multi-page reports, inspect structure, patch exact nodes, and export clean HTML/PDF without manual workarounds.

## Core Workflow

```text
AI agent writes HTML/SVG
        |
        v
MCP write_html parses into document nodes
        |
        v
Backend stores a correct node tree
        |
        v
Frontend renders the workspace for human review
        |
        v
Agent inspects tree/node/html/diagnostics
        |
        v
Agent patches exact nodes with write_html modes
        |
        v
Clean export_html and export_pdf
```

## System Shape

The existing author vision is the right base:

- `backend/`: FastAPI, MCP server, document model, HTML parser, persistence, export logic
- `frontend/`: React/Vite canvas UI, artboard rendering, layer panel, property panel, manual edits
- `desktop/`: thin pywebview wrapper only

The backend must be the source of truth. The frontend should render and edit backend state, but it should not become a separate source of truth. MCP tools should mutate the same document model used by save/open/export and the frontend.

## Agent-First Principles

1. MCP tools are the primary API.
2. Every write tool needs a reliable read-back path.
3. Tree summaries must be useful without image vision.
4. Screenshots are useful, but they are not enough.
5. Export must use clean page HTML, not the editor canvas UI.
6. Mutations must be deterministic and targetable.
7. The document tree must round-trip through parse, render, save, open, export, and PDF.

## Pipeline-First Rule

New capabilities should be built from the backend pipeline upward:

```text
backend document pipeline
        |
        v
MCP read/write/diagnostic tools
        |
        v
frontend layer/canvas/inspector shell
        |
        v
Select and Design Mode workflows
        |
        v
layout/domain skills
```

Do not build frontend features or MCP tools on top of missing backend behavior. If the backend cannot store, read back, verify, and export a feature reliably, the frontend should not pretend that feature is supported. Missing backend pipelines create fragile MCP tools and confusing UI state.

## Backend Responsibilities

The backend owns:

- document IDs and active document state
- artboards/pages
- node IDs, parent IDs, and child arrays
- parsed HTML/SVG nodes
- styles and text content
- MCP tool schemas and handlers
- clean HTML export
- clean PDF export
- save/open behavior
- structural diagnostics

The most important backend invariant:

```text
If node.parentId points to a parent, that parent.children must contain the node ID.
```

This invariant is currently the likely root cause behind broken export/save/readback behavior. Fixing it comes before PDF export or advanced UI polish.

## Frontend Responsibilities

The frontend owns:

- visual canvas rendering
- selection and inspection
- layer panel display
- property panel display and edits
- human review
- pan/zoom canvas navigation
- optional screenshot capture if needed

The frontend should not be required for clean export. Export should be generated from the document model and clean HTML, not from toolbar/canvas/editor DOM.

## Frontend Direction After Diagnosis

The existing frontend interaction model is not reliable enough to keep expanding as the primary editor. Manual UI testing showed repeated document identity drift, broken toolbar mutations, weak layer-panel sync, and move behavior that either snaps back or writes stale `left`/`top` into flex/layout nodes.

The next frontend direction is a small agent-first shell, preferably still using the existing Vite + React stack:

- render pages/artboards from backend document state
- focus the current page or fit all artboards on startup
- provide clean pan/zoom navigation
- make the cursor tool a Select tool
- select pages and elements without mutating layout
- sync canvas selection with the layer tree
- show an inspector with node ID, tag/type, text, and style summary
- avoid manual creation tools until the backend/frontend state model is stable

This frontend is a visual cockpit for the backend and MCP tools. It is not a Paper clone and should not try to rebuild full manual design-tool behavior before selection, inspection, and document identity are stable.

## Layer Tree And Selection Contract

The left panel should behave like a Framer/Paper-style layer tree, backed by VibeDesign node IDs:

```text
layer row <-> nodeId <-> rendered canvas element <-> right inspector <-> MCP target
```

A layer row is a human-facing UI representation. The node ID is the real identity. Child layers are nodes whose `parentId` points to another node, and the tree is the parent/child map. `get_tree_summary` is the agent-readable version of the same tree that the left panel shows to the human.

Accurate selection depends on this invariant:

```text
click layer row -> selects exact nodeId -> highlights exact rendered canvas node
click canvas node -> selects exact nodeId -> highlights exact layer row
```

If this mapping is wrong, Select, Design Mode, and targeted MCP edits are unsafe.

## Design Mode Direction

Design Mode should build on Select. It is not a replacement for the selection model. The detailed Design Mode architecture and V1 plan now live in `design-mode.md`.

```text
accurate layer/tree/node mapping
        |
        v
accurate Select tool
        |
        v
Design Mode
        |
        v
AI edits selected node IDs through MCP
```

Recommended V1 behavior:

- Select mode is the default inspection mode.
- Pan mode is navigation only.
- Design Mode is an explicit toggle.
- In Design Mode, clicking a node selects it and opens or activates an AI edit prompt.
- The prompt should initially live in a fixed right-panel section, not a floating canvas popup.
- Multi-select can later pass multiple selected node IDs to the same prompt.
- Agent edits should target selected node IDs through MCP tools, then use readback/diagnostics to verify.
- Browser-originated prompts should reach the live agent through a minimal tmux bridge for V1, not a full daemon/task queue.

Design Mode must not be introduced before layer-to-canvas node identity is trustworthy.

## Manual Tool Policy

Manual toolbar tools are secondary to the agent workflow.

- Text tool: remove or disable from the primary UI. Text editing is handled through `set_text_content`, targeted `write_html`, and verification tools.
- Frame tool: remove or disable. Page/artboard creation is handled by agent/MCP tools.
- Rectangle tool: remove or disable for now. Paper's rectangle is a styled `div`, not an SVG primitive, but VibeDesign should not keep a broken manual rectangle tool exposed.
- Move/cursor tool: redefine as Select. It should select pages/elements and drive the layer panel/inspector, not drag arbitrary layout elements.
- Pan tool: keep as the canvas navigation tool.

Manual element dragging should stay disabled until there is a deliberate move model. The current behavior writes `left`/`top` into normal flex/text/card elements and can corrupt layout.

## Shape And SVG Direction

Disabling the Rectangle tool does not remove the need for strong shape support. Shape creation should be agent-first and inspectable, similar to the editing pipeline:

- clear shape/SVG creation APIs or conventions
- preserved SVG tags and attributes
- readback through tree/node/html/SVG summary tools
- targeted mutation of SVG attributes such as `x`, `y`, `width`, `height`, `cx`, `cy`, `r`, `d`, `fill`, and `stroke`
- diagnostics for SVG bounds and viewport issues
- repair flow based on inspection and targeted mutation, not blind rewrite

This is a separate pipeline from the old Rectangle toolbar button.

## Skills Direction

Skills are deferred until after V1 core behavior is stable. Do not write skill system prompts, skill scaffolding, `.skill` folders, or skill-loading code during the current V1 round.

The future direction is still important: VibeDesign can support layout/domain skills as a layer above the core MCP engine. The core codebase should not hardcode every design pattern. Instead:

```text
VibeDesign core = document model, MCP tools, diagnostics, export, frontend shell
VibeDesign skills = layout systems, domain recipes, templates, visual planning rules
```

Skills are for agents, not MCP. MCP tool schemas are preloaded as executable tool contracts; skills should use progressive disclosure where only name/description are visible by default, and the full `SKILL.md` plus references/assets are read only when the user's request triggers that skill.

The `kami_consulting` style of skill is one possible future skill, not the default or only skill. Other users should be able to add different craftsmanship packs such as impeccable-style design rules, brand systems, report systems, dashboard systems, or their own domain recipes.

Expected skill workflow:

```text
user request triggers skill -> agent reads that skill -> agent plans with user -> agent uses VibeDesign MCP as executor -> inspect tree/node/html -> patch exact nodes -> export
```

This avoids AI slop by giving agents optional craftsmanship guidance while keeping VibeDesign core focused on reliable document storage, MCP tools, rendering, diagnostics, and export.

## Desktop Responsibilities

The desktop wrapper should stay thin:

- start or connect to backend/frontend
- open the local UI in a native window
- eventually provide native file dialogs

No document logic should live in `desktop/`.

## V1 Priority

V1 should optimize this loop:

```text
write_html -> get_tree_summary/get_node_info/get_html -> fix -> export_html -> export_pdf
```

Human-facing editor polish is useful, but secondary. Toolbar icons, context menu polish, packaging, and component systems should wait until the document model and export path are reliable.

Skills also wait until after this V1 core loop is reliable. They are a future agent-guidance layer, not a V1 runtime dependency.

Near-term frontend work should optimize this loop:

```text
load backend document -> focus page -> select node -> inspect tree/style/text -> agent patches exact node -> frontend refreshes cleanly
```

Before assigning large new rounds, discuss the round direction and next 4-5 tasks with the user. This applies to frontend rebuild work, SVG/shape pipeline work, remaining editing pipeline work, and export work.

Design Mode implementation should also be discussed before coding begins. The agreed V1 direction is documented in `design-mode.md`: fixed right-panel prompt, backend send endpoint, tmux paste into a persistent `design-agent` session, existing MCP edits, existing frontend poll/sync, and revision-based loading completion.

## Non-Goals For Now

- No custom layout engine.
- No new `.vibe` document format.
- No Termux-specific path abstraction.
- No 1:1 Paper UI parity before agent workflow reliability.
- No chart libraries for reports; agents should be able to write inline SVG directly.
