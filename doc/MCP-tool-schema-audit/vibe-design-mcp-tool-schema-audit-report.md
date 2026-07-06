# VibeDesign MCP Tool Schema Audit Report

Task 44 — Documentation/audit only. No behavior changes.

Comparison of agent-facing MCP schemas (from `TOOLS_LIST` in `backend/main.py`) against actual handler implementation for the 11 priority tools.

---

## write_html

**Status: Response undocumented**

### Agent-facing schema

- **description:** "Write HTML into a document. Supports targeted append/replace-children/replace modes. Use targetNodeId to target an existing element or page. Without targetNodeId, uses pageId or the current page."
- **required:** `["html"]`
- **properties:**
  - `html` (string) — HTML string with inline styles.
  - `targetNodeId` (string) — Target page or element ID.
  - `pageId` (string) — Target page ID; used only if targetNodeId is not provided.
  - `mode` (string) — One of: 'append' (default), 'replace-children', 'replace'.

### Actual behavior

- **accepted inputs:** Same as schema.
- **defaults:** `mode="append"`, `targetNodeId=None`, `pageId=None`.
- **validation:** `html` must be non-empty string. If empty, returns `{"success": false, "error": "html is required"}`. Empty parsed HTML (no elements extracted) returns `{"success": true, "created": [], "count": 0, ...}` — not an error but silently no-ops.
- **side effects:** Parses HTML via `parse_html_elements()`, appends/replaces/replaces-children into the resolved target page/element. Calls `_save()` on the document.
- **response shape:** Returns `{"success": bool, "created": [list of created element dicts], "count": int, "document": {...full doc...}, "mode": str, "targetNodeId": str|None, "deleted": [list of deleted node IDs if mode=replace]}` — includes the full document snapshot.

### Gaps

1. **Response not documented in schema:** The agent gets back `created` (new element dicts), `count`, `document` (full doc snapshot), and `deleted` (only for `replace` mode). None of this is in the schema description.
2. **No mention of empty-HTML no-op:** Agent has no way to know that `html=""` or HTML that produces zero parsed elements is a silent success, not an error.
3. **`mode` values not enumerated in schema:** Schema says `"One of: 'append' (default)... "` but doesn't list the exact three allowed values as an enum.

### Recommended schema fix

- Add response shape to description.
- Mention empty parse result is a success with `count: 0`, not an error.
- Optional: enumerate `mode` values as an enum in the schema.

---

## update_styles

**Status: Schema incomplete**

### Agent-facing schema

- **description:** `"Update styles"` (very short).
- **required:** `["nodeIds", "styles"]`
- **properties:**
  - `nodeIds` (array of string) — no description.
  - `styles` (object) — no description.
  - `removeStyleKeys` (array of string, optional) — documented with example `['left', 'top']`.

### Actual behavior

- **accepted inputs:** `nodeIds`, `styles`, `removeStyleKeys` (optional).
- **defaults:** `removeStyleKeys` omitted = no removal.
- **validation:**
  - `removeStyleKeys` strictly validated: if present, must be array of non-empty strings.
  - Artboard IDs detected and routed to `update_page()` with allowlisted keys (`x, y, backgroundColor, width, height, name`).
  - Element IDs routed to `update_element()` with deep-merge style + optional removal.
- **side effects:** Calls `_save()` after each mutation. Multi-node: all nodes processed, partial success possible.
- **response shape:** `{"success": true, "updated": [list of updated element dicts or {id, type, updates} for artboards]}`

### Gaps

1. **Description is too short:** `"Update styles"` does not convey the artboard routing, the style deep-merge behavior, or the `removeStyleKeys` design.
2. **`nodeIds` missing description:** No hint that these can be both element IDs and artboard IDs with different behavior.
3. **`styles` missing description:** No hint that styles are deep-merged, not replaced.
4. **Artboard vs element routing not documented:** Schema doesn't explain that artboard IDs route to `update_page()` but element IDs route to `update_element()`.
5. **Response not documented:** Agent doesn't know it gets back `updated` array with the mutation results.

### Recommended schema fix

- Improve description to mention deep-merge, artboard routing, and removal.
- Add descriptions to `nodeIds` and `styles`.
- Document response shape in description.

---

## set_text_content

**Status: Schema incomplete**

### Agent-facing schema

- **description:** `"Set text content"` (very short).
- **required:** `["nodeIds", "text"]`
- **properties:**
  - `nodeIds` (array of string) — no description.
  - `text` (string) — no description.

### Actual behavior

- **accepted inputs:** `nodeIds`, `text`.
- **defaults:** `nodeIds` defaults to `[]`, `text` defaults to `""`.
- **validation:** No validation of nodeIds being non-empty or nodes existing. Missing nodes are silently skipped.
- **side effects:** Calls `update_element()` for each node ID with `{"text": content}`. Only elements that can accept `text` field are affected.
- **response shape:** `{"success": true, "updated": [list of updated element dicts]}` — empty list if no nodes matched.

### Gaps

1. **Description too short:** `"Set text content"` doesn't explain multi-node support, behavior on non-text nodes, or silent skip of missing nodes.
2. **`nodeIds` missing description:** No hint about what happens when node doesn't exist or isn't a text-capable element.
3. **`text` missing description:** No hint about empty string behavior (it clears text).
4. **Response not documented:** Agent doesn't know `updated` can be empty list on silent skip.
5. **No error for missing nodes:** Failed lookups are silently dropped — agent has no way to know which nodeIds failed.

### Recommended schema fix

- Add description: "Set text content on one or more elements. Missing nodes are silently skipped."
- Document that `text: ""` clears the text.
- Document response shape with `updated` array.

---

## update_svg_attributes

**Status: Schema incomplete**

### Agent-facing schema

- **description:** "Update SVG/XML attributes on an existing SVG node. Writes attrs into the node style dict so export/render paths emit them as SVG attributes."
- **required:** `["nodeId", "attrs"]`
- **properties:**
  - `nodeId` (string) — no description.
  - `attrs` (object) — no description.

### Actual behavior

- **accepted inputs:** `nodeId`, `attrs`.
- **defaults:** None.
- **validation:**
  - `nodeId` must be non-empty string.
  - `attrs` must be non-empty object.
  - Each attr key must be non-empty string.
  - Each attr value must be string, number, bool, or null.
  - Node must exist and be an SVG element (tag in `_SVG_TAGS`).
  - Page/artboard IDs are rejected with error.
- **side effects:** Deep-merges `attrs` into element's `style` dict via `update_element()`.
- **response shape:** `{"success": true, "nodeId": str, "updated": element_dict, "attrs": {k:v}}`

### Gaps

1. **`nodeId` missing description:** No hint that it must be an SVG element node (not a page, not a non-SVG div).
2. **`attrs` missing description:** No hint about accepted attribute names, casing behavior, accepted value types.
3. **Validation behavior not documented:** Schema doesn't tell agent that non-SVG nodes, missing nodes, or empty attrs will fail.
4. **Response not documented:** Agent gets back the full updated element but doesn't know from the schema.
5. **No hint about native `id`:** SVG native `id` is stored in `style["id"]` — this is not mentioned.

### Recommended schema fix

- Add description to both parameters.
- Document that node must be an SVG element (not page, not non-SVG element).
- Document response shape with `updated` and `attrs` fields.

---

## get_node_info

**Status: OK**

### Agent-facing schema

- **description:** "Get detailed info about a page or element".
- **required:** none.
- **properties:**
  - `nodeId` (string) — "Optional. Page or element ID. Omit to use current page."

### Actual behavior

- **accepted inputs:** `nodeId` (optional).
- **defaults:** Omitted `nodeId` → returns current page info.
- **validation:** Missing/invalid nodeId returns `{"error": "Node '...' not found"}`.
- **side effects:** None (read-only).
- **response shape:**
  - Page: `{id, kind: "page", name, x, y, width, height, backgroundColor, childIds, childCount, elementCount}`
  - Element: `{id, kind: "element", name, tag, type, parentId, pageId, style, text, textSnippet, children: [{id, name, tag, type}], childIds, childCount, x, y, width, height}`

### Gaps

1. **Minor: response fields not enumerated in description.** Agent doesn't know what fields come back. However, the description says "detailed info" which is fairly descriptive.
2. **Minor: current page fallback not explicit.** Schema says "Omit to use current page" which is correct.

### Recommended schema fix

- Minor: consider adding a note about the response structure in the description (e.g. "Returns page or element metadata including id, name, position, style, text, parent/children").

---

## get_html

**Status: Schema misleading**

### Agent-facing schema

- **description:** "Get clean exported HTML for the current page, a page, or an element subtree."
- **required:** none.
- **properties:**
  - `nodeId` (string) — "Optional. Page or element ID. Omit to use current page."
  - `pageId` (string) — "Optional. Target page ID."
  - `pretty` (boolean) — "Pretty-print the HTML. Default true."

### Actual behavior

- **accepted inputs:** `nodeId`, `pageId`. `pretty` is accepted but **ignored**.
- **defaults:** Omitted `nodeId`/`pageId` → uses current page.
- **validation:** Invalid `pageId` → `{"error": "Page '...' not found"}`. Invalid `nodeId` → `{"error": "Node '...' not found"}`.
- **side effects:** None (read-only).
- **response shape:** Returns `{"success": true, "html": "<...>", "nodeId": str, "pageId": str}` — or error dict.

### Gaps

1. **`pretty` parameter is misleading:** The schema advertises `pretty` as a feature with `"Pretty-print the HTML. Default true."` but the handler at `backend/main.py:1798-1801` calls `doc_store.get_node_html(doc_id, node_id=node_id, page_id=page_id)` **without passing `pretty`**. `DocumentStore.get_node_html()` accepts a `pretty` parameter but does not use it for alternate formatting. The `pretty` flag is effectively dead — the schema promises something the implementation does not deliver.
2. **Response not documented:** Agent doesn't know it gets back `html`, `nodeId`, `pageId` fields.
3. **`nodeId` + `pageId` interaction not documented:** E.g., when both are provided, `pageId` is validated first and constrains the node lookup. This is implementation behavior.

### Recommended schema fix

- Either remove `pretty` from the schema, or make the handler pass it through and implement actual pretty-printing in `get_node_html()`. Schema-only fix: remove `pretty` or document that it is currently accepted but ignored.

---

## get_overflow_report

**Status: OK**

### Agent-facing schema

- **description:** "Report nodes that overflow their parent or artboard, including overflow amounts per side."
- **required:** none.
- **properties:**
  - `pageId` (string) — "Optional page ID."
  - `nodeId` (string) — "Optional page or element ID."
  - `includeArtboard` (boolean) — "Include artboard boundary overflow checks. Default true."
  - `includeParent` (boolean) — "Include parent boundary overflow checks. Default true."
  - `minOverflow` (number) — "Minimum pixel overflow to report. Default 1."

### Actual behavior

- **accepted inputs:** All as documented.
- **defaults:** `includeArtboard=True`, `includeParent=True`, `minOverflow=1`.
- **validation:** `minOverflow` coerced to float; negative values reset to 1. Invalid page/node returns error.
- **side effects:** None (read-only).
- **response shape:** `{"success": true, "overflows": [...items with type, nodeId, pageId, severity, amount per side, geometry, boundary], "overflowCount": int}`

### Gaps

None significant. Description matches behavior. Defaults match. Minor: response not enumerated but description covers it.

### Recommended schema fix

- Optional: document response shape in description.

---

## move_nodes

**Status: Minor gaps**

### Agent-facing schema

- **description:** "Move element nodes within the same page (reorder or reparent). Preserves whole subtrees. Same-page only — cross-page moves are rejected."
- **required:** `["nodeIds"]`
- **properties:**
  - `nodeIds` (array of string) — "Element node IDs to move. Required, non-empty."
  - `targetParentId` (string) — "Target page ID or element ID. If omitted, pageId is used as the page-root target."
  - `pageId` (string) — "Optional page ID. If provided, constrains targetParentId lookup to that page; otherwise targetParentId can be any page or element."
  - `index` (number) — "Insertion index inside the target's children array (or page-root order). Omitted or invalid → append at end."

### Actual behavior

- **accepted inputs:** Same as schema.
- **defaults:** `targetParentId=None` (page root), `pageId=None`, `index=None` (append).
- **validation:** Same-page restriction enforced. Cycle detection (no move under own descendant). Missing node returns error. If `pageId` provided, `targetParentId` lookup constrained to that page. Cross-page move returns error.
- **side effects:** Reorders/reparents elements. Calls `_save()`.
- **response shape:** `{"success": bool, "pageId": str, "targetParentId": str|None, "moved": [{nodeId, oldParentId, newParentId, oldIndex, newIndex}], "movedCount": int, "errors": [...]}`

### Gaps

1. **Response not documented.** Agent doesn't know it gets back `moved`, `movedCount`, `errors` with per-node old/new parent/index tracking.
2. **Cycle protection not mentioned.** Agent could try to move a parent under its own child and get an error.

### Recommended schema fix

- Document response shape: returns `moved` array with per-node `oldParentId`/`newParentId`/`oldIndex`/`newIndex`.
- Mention cycle protection in description.

---

## duplicate_nodes

**Status: Minor gaps**

### Agent-facing schema

- **description:** "Duplicate full element subtrees and return per-root descendant ID maps."
- **required:** `["nodeIds"]`
- **properties:**
  - `nodeIds` (array of string) — "Element node IDs to duplicate. Required, non-empty."
  - `offsetX` (number) — "Horizontal offset applied to cloned root's positional style. Default 20."
  - `offsetY` (number) — "Vertical offset applied to cloned root's positional style. Default 20."

### Actual behavior

- **accepted inputs:** Same as schema.
- **defaults:** `offsetX=20`, `offsetY=20`.
- **validation:** `nodeIds` must be non-empty list. `offsetX`/`offsetY` coerced to float; non-numeric returns error. Missing nodes reported in `errors` array, rest of batch continues.
- **side effects:** Clones full subtrees with new generated IDs. The root's positional style gets the offset applied; descendants' styles are not offset. Calls `_save()`.
- **response shape:** `{"success": bool, "duplicated": [{sourceNodeId, newNodeId, pageId, node, created, createdIds, descendantIdMap}], "duplicatedCount": int, "errors": [{nodeId, error}]}`

### Gaps

1. **Response not fully documented.** Schema description mentions "return per-root descendant ID maps" which is good. But the detailed shape (each entry has `sourceNodeId`, `newNodeId`, `pageId`, `node`, `created`, `createdIds`, `descendantIdMap`) is not described.
2. **Offset only applies to root's positional style.** Descendant styles are not offset. Not mentioned.

### Recommended schema fix

- Add detail about response structure: each entry contains `sourceNodeId`, `newNodeId`, `descendantIdMap`, etc.
- Mention that `offsetX`/`offsetY` apply to the cloned root's `left`/`top` style only, not descendants.

---

## delete_nodes

**Status: OK**

### Agent-facing schema

- **description:** "Delete element subtrees. Removes each requested node plus all of its descendants, cleans up parent/children references, and supports optional pageId constraint."
- **required:** `["nodeIds"]`
- **properties:**
  - `nodeIds` (array of string) — "Element node IDs to delete. Required, non-empty."
  - `pageId` (string) — "Optional page ID. If provided, validates first and constrains deletion to that page."

### Actual behavior

- **accepted inputs:** Same as schema.
- **defaults:** `pageId=None`.
- **validation:** `nodeIds` validated as non-empty list. Invalid `pageId` returns error. Missing nodes reported in errors array, rest of batch continues.
- **side effects:** Deletes full subtrees. Cleans parent/children references. Ancestor/descendant dedup: if both parent and child are requested, only the parent subtree is deleted. Pages are never deleted. Calls `_save()`.
- **response shape:** `{"success": bool, "deleted": [all deleted IDs], "deletedCount": int, "deletedRoots": [input order, deduped], "deletedByRoot": {root: [ids]}, "errors": [{nodeId, error}]}`

### Gaps

None significant. Description matches behavior. All key behaviors documented.

### Recommended schema fix

- Optional: document response shape (deleted, deletedCount, deletedRoots, deletedByRoot, errors).

---

## rename_nodes

**Status: OK (thorough docstring)**

### Agent-facing schema

- **description:** "Rename element nodes and page/artboard nodes. Returns per-node results with oldName/newName/kind/pageId/node. Supports an optional pageId constraint to scope the lookup to a single page (or rename that page itself when a nodeId equals pageId)."
- **required:** `["nodeIds", "names"]`
- **properties:**
  - `nodeIds` (array of string) — "Node IDs to rename (elements and/or page IDs). Required, non-empty."
  - `names` (object) — "Map of nodeId -> new name. Every requested ID must have a non-empty string entry (whitespace-only is invalid)."
  - `pageId` (string) — "Optional page ID. If provided, validates first and scopes the lookup to that page; if a nodeId equals pageId, that page is renamed."

### Actual behavior

- **accepted inputs:** Same as schema. Behavior matches the comprehensive docstring in the implementation.
- **defaults:** `pageId=None`.
- **validation:** `nodeIds` non-empty list. `names` non-empty object. Each name validated as non-empty string. Page ID cross-validated if provided. Missing nodes reported in errors; valid renames proceed.
- **side effects:** Renames element `name` field or page `name` field. Calls `_save()`.
- **response shape:** `{"success": bool, "renamed": [{nodeId, pageId, kind, oldName, newName, node}], "renamedCount": int, "errors": [{nodeId, error}]}`

### Gaps

None significant. Description is thorough. Docstring in code is even more detailed but the schema description covers the important points.

### Recommended schema fix

- None needed.

---

## Summary

| Tool | Status | Key gap |
|---|---|---|
| write_html | Response undocumented | No mention of `created`, `count`, `document`, `deleted` in response; empty parse is silent no-op |
| update_styles | Schema incomplete | Description too short; artboard vs element routing undocumented; no descriptions on `nodeIds`/`styles` |
| set_text_content | Schema incomplete | Description too short; silent skip of missing nodes undocumented |
| update_svg_attributes | Schema incomplete | `nodeId`/`attrs` have no descriptions; validation not documented |
| get_node_info | OK | Minor: no response field list |
| get_html | Schema misleading | `pretty` parameter accepted but ignored by handler — dead flag |
| get_overflow_report | OK | Minor: response not enumerated but covered by description |
| move_nodes | Minor gaps | Response shape undocumented; cycle protection not mentioned |
| duplicate_nodes | Minor gaps | Response shape partially documented; offset applies to root only |
| delete_nodes | OK | Minor: response shape not enumerated |
| rename_nodes | OK | Thorough description matches behavior |

**3 tools need schema fixes (Task 45):** `write_html`, `update_styles`, `set_text_content`.
**1 tool needs schema fix (Task 45):** `update_svg_attributes`.
**1 tool needs backend alignment + schema fix (Task 45/46):** `get_html` — `pretty` parameter accepted but ignored by handler.
**2 tools need minor fixes (Task 46):** `get_node_info`, `get_overflow_report`.
**3 tools need minor fixes (Task 47):** `move_nodes`, `duplicate_nodes`, `delete_nodes`.
**1 tool needs no fix:** `rename_nodes`.
