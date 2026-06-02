# Paper Clone - Development Plan

## Overview

Recreate the Paper design tool as a local-first, offline-capable application. Use MCP so AI agents such as Claude Code can read and modify designs.

- **Positioning**: an open-source local clone of Paper
- **Core features**: real HTML/CSS canvas rendering plus a standard MCP server
- **Packaging**: bundle as a macOS app with pywebview

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Claude Code / AI Agent                                │
│  (connects via MCP: 127.0.0.1:3004/mcp)               │
└────────────┬────────────────────────────────────────────┘
             │  Streamable HTTP (MCP Protocol)
             ▼
┌─────────────────────────────────────────────────────────┐
│  Python FastAPI Backend (port 3004)                    │
│  ├── MCP Server (POST /mcp)                           │
│  └── Document Store (HTML files)                        │
└────────────┬────────────────────────────────────────────┘
             │  HTTP API + polling sync
             ▼
┌─────────────────────────────────────────────────────────┐
│  React Frontend (Vite dev server)                      │
│  ├── Canvas (position: absolute + inline styles)        │
│  ├── Toolbar (Move/Pan/Frame/Rectangle/Text)          │
│  ├── Layer Panel                                       │
│  ├── Property Panel                                   │
│  └── Page Tabs                                        │
└─────────────────────────────────────────────────────────┘
```

### Key design decisions

- **Rendering**: real HTML/CSS DOM, `position: absolute` + inline styles (same as Paper)
- **Document format**: `.html` files as the source format, with metadata stored in `data-paper-*` attributes and `<meta>` tags
- **MCP protocol**: standard Streamable HTTP transport, directly connectable from Claude Code
- **Frontend sync**: the frontend polls the backend every second to sync document state
- **Communication flow**: MCP tool call -> Python handler -> frontend polling sync

---

## Feature List

### Phase 1 (MCP + core rendering) ✅ Mostly complete

- [x] Project scaffold setup (FastAPI + Vite + React + pywebview)
- [x] MCP server implementation (19 tools)
- [x] Canvas rendering engine (position: absolute + inline styles)
- [x] Toolbar (Move/Pan/Frame/Rectangle/Text)
- [x] Frontend polling sync
- [ ] File open/save dialog (pywebview native dialog)
- [ ] Toolbar SVG icons

### Phase 2 (Editor interactions) ✅ Mostly complete

- [x] Element selection
- [x] Drag to move
- [x] Resize handles (ArtboardFrame 8-point resize + Element 4-point resize)
- [x] Canvas zoom (mouse wheel, Cmd+ / Cmd-)
- [x] Canvas pan (Pan tool + space-drag)
- [x] Undo/redo (Zustand history)
- [x] Right properties panel (colors, fonts, sizes, etc.)
- [x] Left layers panel (node hierarchy management)
- [ ] Double-click text editing
- [ ] Keyboard shortcut polish (context menu Copy/Paste/Duplicate, etc.)

### Phase 3 (Full features) 🔄 In progress

- [x] Multi-page/multi-artboard support (canvas shows all artboards at once, supports drag/zoom, and syncs properties with the backend in real time)
- [ ] Copy/paste
- [ ] Alignment guides
- [ ] Export formatted HTML
- [ ] Toolbar SVG icons (reuse original Paper icons)

### Phase 4 (Packaging and release)

- [ ] pywebview desktop packaging configuration
- [ ] macOS .app packaging

---

## MCP Tools List (19 tools, all implemented)

### Document operations
- `get_basic_info` — Get document information
- `create_artboard` — Create a new page
- `get_tree_summary` — Get a node tree summary

### Node queries
- `get_children` — Get child nodes
- `get_node_info` — Get detailed node information
- `get_selection` — Get currently selected nodes
- `get_screenshot` — Screenshot

### Node creation
- `write_html` — Write an HTML fragment to create nodes
- `duplicate_nodes` — Duplicate nodes

### Node modifications
- `update_styles` — Update styles
- `set_text_content` — Set text content
- `rename_nodes` — Rename nodes
- `finish_working_on_nodes` — Mark operation complete

### Style export
- `get_computed_styles` — Get computed styles
- `get_jsx` — Export JSX code
- `get_font_family_info` — Get font information

### File operations
- `save_document` — Save document
- `open_document` — Open document
- `export_html` — Export HTML

---

## File Structure

```
paper_clone/
├── backend/
│   ├── main.py              # FastAPI entry point (port 3004) + MCP Server
│   ├── document.py           # Document storage (HTML files)
│   ├── handlers/             # MCP handlers (merged into main.py)
│   │   └── mcp_handler.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── canvas/
│   │   │   ├── Canvas.tsx
│   │   │   └── Element.tsx
│   │   ├── toolbar/
│   │   │   └── Toolbar.tsx
│   │   ├── panels/
│   │   │   ├── LayerPanel.tsx
│   │   │   └── PropertyPanel.tsx
│   │   ├── store/
│   │   │   └── editorStore.ts  (Zustand)
│   │   ├── bridge/
│   │   │   └── api.ts
│   │   └── types.ts
│   ├── vite.config.ts
│   └── package.json
├── desktop/
│   └── main.py              # pywebview entry point
└── plan.md
```

---

## Current tasks

### Phase 1 status

✅ MCP Server running at 127.0.0.1:3004/mcp
✅ Frontend running at http://localhost:5173
✅ MCP write_html successfully creates elements
✅ Frontend polling syncs elements to the canvas
✅ HTML export works

**Remaining**:
- pywebview packaging (requires native dialog support)
- File open/save support
- SVG toolbar icons
- MCP update_artboard tool (x/y/width/height/name/backgroundColor)

---

## Startup

```bash
# Backend
cd backend && python main.py

# Frontend (development mode)
cd frontend && npm run dev

# Desktop app (after packaging)
cd desktop && python main.py
```

### Claude Code MCP Config

Add the following to the Claude Code MCP config file:

```json
{
  "mcpServers": {
    "paper-clone": {
      "command": "curl",
      "args": ["-X", "POST", "-H", "Content-Type: application/json", "-d", "{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{}}", "http://127.0.0.1:3004/mcp"]
    }
  }
}
```

Or call the MCP endpoint directly over HTTP.
