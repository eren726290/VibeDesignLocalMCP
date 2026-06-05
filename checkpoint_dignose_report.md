# VibeDesignLocalMCP Editing Diagnosis Prompt Pack

Date: 2026-06-05

## Purpose

Use this file on PC to test the editing-tool work added after the first checkpoint.

Start from the element repair/editing problem:

```text
Can an agent find misplaced elements by node ID, patch only the wrong style keys, reparent/reorder them, and verify the result without rebuilding the page?
```

The expected standard is not visual guessing. The agent should use MCP readback tools and deterministic edits.

## What We Built For This Diagnosis

Task 16: `update_styles` became non-destructive.

- Style updates now merge into the existing style dict.
- Updating `position`, `left`, or `top` should not wipe `backgroundColor`, `padding`, `borderRadius`, fonts, SVG attributes, or other style keys.

Task 17: element `type` inference became stable.

- `a` remains `link`.
- headings remain `heading`.
- containers such as `header`, `nav`, `section`, and `footer` remain `div`.
- SVG primitives get types such as `svg-rect`, `svg-path`, and `svg-text`.

Task 18: `get_jsx` became a useful nested readback/export tool.

- It preserves nesting.
- It emits valid React style object syntax.
- It supports `pageId`, `nodeId`, and `nodeIds`.
- It includes `data-paper-node` and `data-paper-name`.

Task 19: `update_styles` gained explicit style-key removal.

- Use `removeStyleKeys` to delete stale keys like `left`, `top`, `right`, `bottom`, or `position`.
- Removal is explicit only. Do not treat `"auto"`, `"unset"`, empty string, or `None` as delete commands.

## Standard Repair Workflow

When a page is visually wrong or elements are misplaced, the agent should follow this workflow:

```text
get_tree_summary / get_children
-> identify suspicious node IDs and intended parent/order
-> get_node_info / get_computed_styles
-> update_styles with merge-safe styles and removeStyleKeys
-> move_nodes to restore parent/index
-> get_tree_summary / get_node_info / get_html / get_jsx
-> export_html or save/open round-trip if needed
```

The agent should not delete and rebuild the whole page unless the document is structurally unrecoverable.

## Prompt 1 - Diagnose Misplaced Elements

```text
I intentionally misplaced some elements on this VibeDesign page.

Do not rebuild the page.
Use MCP tools to diagnose the structure and styles.
Find suspicious nodes by ID using get_tree_summary, get_children, get_node_info, and get_computed_styles.

Tell me:
1. Which nodes are misplaced or suspicious.
2. Which parent each node currently has.
3. Which parent/index each node should probably have.
4. Which style keys look wrong, especially position/left/top/right/bottom.
5. What exact update_styles and move_nodes calls you would use to repair them.

Do not make changes yet. Report the diagnosis first.
```

Expected result:

- The agent identifies node IDs instead of guessing from screenshots only.
- The agent distinguishes style problems from parent/order problems.
- The agent proposes `update_styles` plus `removeStyleKeys` for stale absolute positioning.
- The agent proposes `move_nodes` for parent/index repair.

## Prompt 2 - Repair By Node ID

```text
Now repair the misplaced elements.

Rules:
- Do not delete the page.
- Do not rebuild the page from scratch.
- Use update_styles to patch only the necessary style values.
- Use removeStyleKeys to remove stale absolute-position keys such as left/top when needed.
- Use move_nodes to restore parent/index structure.
- Preserve visual styles like backgroundColor, padding, gap, borderRadius, typography, borders, and SVG attributes.
- After repair, verify with get_tree_summary, get_node_info, get_computed_styles, and get_html or get_jsx.

Report the exact node IDs changed and the before/after parent/style differences.
```

Expected result:

- `backgroundColor`, `padding`, `borderRadius`, typography, and SVG attributes survive.
- Removed keys are actually absent, not stored as `"auto"` unless the agent intentionally set them.
- `move_nodes` updates parent/children structure.
- The agent does not fall back to full rebuild.

## Prompt 3 - Verify Non-Destructive Style Merge

```text
Test whether update_styles is non-destructive.

Pick one styled element with many style keys such as backgroundColor, padding, borderRadius, fontFamily, fontSize, and border styles.
Use update_styles to change only position to static.
Then inspect the same node with get_node_info and get_computed_styles.

Confirm whether all unrelated style keys survived.
Do not change anything else.
```

Expected result:

- Only `position` changes.
- Unrelated style keys remain unchanged.
- This confirms Task 16.

## Prompt 4 - Verify Explicit Style Key Removal

```text
Test explicit style-key removal.

Pick one element that has position/left/top in its style.
Use update_styles with:
- styles: {"position": "static"}
- removeStyleKeys: ["left", "top"]

Then verify with get_node_info, get_computed_styles, get_html, and get_jsx.

Confirm that:
1. position is now static.
2. left and top are absent from the element style.
3. unrelated style keys are preserved.
4. export/readback output does not include left/top on that element.
```

Expected result:

- `left` and `top` are removed from the element style dict.
- `get_html` and `get_jsx` omit those keys for the target element.
- Page/artboard wrapper styles may still contain `left`/`top`; that is normal and should not be counted as failure.

## Prompt 5 - Verify Type Stability

```text
Test type stability.

Create or inspect content containing:
- header, nav, section, footer
- a links
- h1/h2 headings
- svg with rect, circle, path, line, polygon/polyline, and text if possible

Use get_tree_summary and get_node_info before save.
Then save_document and open_document.
Use get_tree_summary and get_node_info again.

Confirm that:
- a remains type=link.
- headings remain type=heading.
- containers remain type=div.
- SVG primitives get stable svg-* types.
- IDs, tags, text, style, parentId, and children survive.
```

Expected result:

- No drift like `a -> text`.
- No drift like `header/nav/section -> rectangle`.
- SVG primitive tags remain inspectable and type metadata is useful.

## Prompt 6 - Verify Nested JSX Readback

```text
Test get_jsx.

Use get_jsx with:
1. no args
2. pageId
3. nodeId for a page
4. nodeId for an element subtree
5. nodeIds for multiple subtrees

Check that JSX:
- preserves nesting
- includes data-paper-node and data-paper-name
- uses valid style object syntax with colons
- quotes non-identifier style keys
- escapes text safely
- preserves SVG child tags such as rect/path/text
- does not duplicate a descendant when both ancestor and descendant are requested
```

Expected result:

- JSX output is a readable `function PaperCanvas()` component.
- Style syntax looks like `backgroundColor: "#fff"`, not `backgroundColor="#fff"`.
- Nested children appear inside their parent tags.

## Prompt 7 - Save/Open After Repair

```text
Now verify persistence after repair.

Save the document.
Open it again.
Compare the repaired nodes before and after open_document.

Confirm:
- parentId and children arrays are still correct.
- removed style keys are still absent.
- unrelated styles are still present.
- element names and page names survive.
- get_tree_summary, get_node_info, get_html, and get_jsx all reflect the repaired state.
```

Expected result:

- The repair survives round-trip.
- No element-name loss.
- No style-key resurrection.

## Pass / Fail Standard

Pass:

- The agent repairs misplaced elements by targeted MCP edits.
- The page is not deleted/rebuilt.
- Node IDs are used throughout the workflow.
- Style patches are non-destructive.
- Stale keys can be removed explicitly.
- `move_nodes` repairs parent/index structure.
- Readback tools agree after repair.

Fail:

- The agent deletes/rebuilds the whole page for a repairable issue.
- `update_styles` wipes unrelated visual style.
- `left`/`top` remain on the target element after explicit removal.
- `move_nodes` leaves broken parent/children references.
- Save/open loses the repair.
- `get_jsx` or `get_html` contradicts `get_node_info`.

## Notes For The Tester

- Whole-page HTML wrappers legitimately use `left` and `top` for artboard placement. When checking style-key removal, inspect the target element, not the page wrapper.
- `get_svg_summary` uses `tag` as the source of truth, but Task 17 should also make SVG `type` metadata useful.
- This diagnosis pack starts at Task 16 intentionally. Earlier parser/export/tree tests belong to the original checkpoint test, not this editing-tool diagnosis.
