# Frontend Safety

The current frontend is a review and inspection surface for the backend document model.

It is not a full manual design editor. Frontend behavior should stay conservative until the backend mutation model explicitly supports broader layout editing.

## Allowed Responsibilities

The frontend should:

- render backend pages/artboards
- focus the current artboard or fit artboards on startup
- support pan and zoom
- support safe Select behavior
- keep canvas, layer panel, and inspector selection identity aligned
- show stable identity metadata in the inspector
- allow safe text and visual edits where already supported
- poll backend state after MCP/REST changes

## Disabled Or Deferred

These behaviors are intentionally disabled or deferred:

- manual Text tool
- manual Frame tool
- manual Rectangle tool
- keyboard shortcuts that activate disabled creation tools
- generic selected-element dragging
- generic selected-element resize handles
- broad Design Mode UI
- frontend-only document mutation systems

## Artboard Interaction

Artboards remain explicit objects.

Current expected behavior:

- clicking artboard content selects the artboard without moving it
- dragging the artboard header/title strip moves the artboard
- artboard resize handles resize the artboard
- empty canvas click clears selection

Task 32.2 header-strip polish is intentionally not rebuilt in the current reset unless a later PC test identifies it as necessary.

## Inspector Safety

The right inspector should resolve selected nodes across all pages, not only the current page.

Unsafe element layout fields such as `left`, `top`, `width`, and `height` should stay read-only/disabled in Select-only mode. Layout mutation should happen through backend/MCP tools with readback.

## Selection Identity

Selection identity should remain stable across:

- canvas element clicks
- layer row clicks
- nested elements
- cross-artboard selections
- stale or missing node IDs

If a selected node cannot be found, the UI should show an explicit missing-selection state instead of silently displaying the wrong page or element.
