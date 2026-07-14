# Document Model

This file defines the current document identity and tree model used by backend storage, MCP tools, frontend rendering, save/open, and export.

## Shape

The backend document contains pages. Pages contain element roots. Elements can contain child elements.

```text
Document
  Page / artboard
    Element
      Element
      Element
```

The backend is the source of truth. The frontend renders backend state and sends safe edit requests back through backend APIs.

## Identity

VibeDesign node IDs are backend IDs. Agents should use these IDs for MCP mutation tools.

Native HTML/SVG DOM IDs are separate. They are stored as `style["id"]` so export and reopen can preserve real DOM IDs without confusing them with backend node IDs.

Practical rule:

- Use backend node IDs for targeting.
- Use native DOM IDs only as exported HTML/SVG attributes.

## Tree Invariant

The critical invariant is:

```text
if node.parentId points to a parent, that parent.children contains the node ID
```

Page-root elements do not need a `parentId`. Their ownership is the containing page.

## Children

`children` stores child node IDs in render/order position. Structural tools such as duplicate, move, rename, and delete must preserve or update these relationships.

Subtree operations should treat a node and all descendants as one logical structure unless the tool contract says otherwise.

## Styles And SVG Attributes

Element visual styles live in the `style` dict.

Current SVG/XML attributes also live in the `style` dict so existing renderer, mutation, export, and reopen paths share one storage shape. Export paths split SVG/XML attributes from CSS style when writing HTML/JSX.

Known examples:

- SVG root: `viewBox`, `width`, `height`, `id`
- SVG shape: `fill`, `strokeWidth`, `clipPath`, `d`
- Text path: `href`, `startOffset`

## Save/Open

Paper HTML save/open should preserve:

- pages/artboards
- backend node IDs
- element names
- nesting
- style values
- native DOM IDs
- SVG/XML attributes

Any change to parser, export, or document storage should be checked against these round-trip expectations.
