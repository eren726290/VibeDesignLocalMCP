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
- selection
- drag/resize interactions
- layer panel display
- property panel display and edits
- human review
- optional screenshot capture if needed

The frontend should not be required for clean export. Export should be generated from the document model and clean HTML, not from toolbar/canvas/editor DOM.

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

## Non-Goals For Now

- No custom layout engine.
- No new `.vibe` document format.
- No Termux-specific path abstraction.
- No 1:1 Paper UI parity before agent workflow reliability.
- No chart libraries for reports; agents should be able to write inline SVG directly.

