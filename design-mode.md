# Design Mode

## Purpose

Design Mode is the browser-to-agent side of VibeDesignLocalMCP.

The existing agent workflow already works in one direction:

```text
agent -> VibeDesign MCP tools -> backend document -> frontend canvas
```

The missing direction is:

```text
browser user intent -> live terminal agent -> VibeDesign MCP tools
```

Design Mode should let the user select an exact canvas node, write a short edit request in the browser, and have that request delivered to the already-running agent session. The agent then edits through existing MCP tools and the frontend observes the backend document update.

## User Workflow

```text
User enables Design Mode
        |
        v
User clicks an element on the live canvas
        |
        v
VibeDesign captures selected nodeId/pageId/docId
        |
        v
Right panel prompt becomes active
        |
        v
User writes: "make this button blue"
        |
        v
Send injects a formatted message into the live agent terminal session
        |
        v
Agent uses VibeDesign MCP tools to patch exact node(s)
        |
        v
Frontend poll/sync sees document revision change and clears loading
```

Design Mode is not a replacement for Select. It builds on accurate selection.

```text
layer/tree/node mapping
        |
        v
safe Select tool
        |
        v
Design Mode prompt
        |
        v
agent MCP edit
```

## V1 Architecture

V1 should use a minimal tmux-based trigger bridge instead of a full daemon or task queue.

```text
Browser Design Mode prompt
        |
        | POST /api/design-mode/send
        v
VibeDesign backend endpoint
        |
        | tmux load-buffer + paste-buffer + Enter
        v
tmux session: design-agent
        |
        v
running agent CLI: opencode/codex/gemini/claude/etc.
        |
        v
VibeDesign MCP tools mutate document
        |
        v
frontend polling/render sync
```

The agent must be started inside the tmux session before Design Mode sends prompts.

Example startup shape:

```bash
tmux new-session -d -s design-agent -c /root/my-project/VibeDesignLocalMCP 'opencode'
```

The exact agent binary is configurable outside Design Mode. The trigger mechanism stays the same because tmux types into the pane regardless of which agent is running.

## Building Blocks

- Existing backend document model and MCP edit tools.
- Existing frontend selection state: `docId`, `pageId`, selected `nodeId` or selected node IDs.
- Existing frontend poll/sync loop.
- New backend endpoint: `POST /api/design-mode/send`.
- Persistent tmux session, default name `design-agent`.
- Safe tmux injection using argument lists, not shell strings.
- Document revision/version counter for cheap completion detection.
- Frontend loading state with timeout fallback.

## Why tmux

Normal terminal, cmd, PowerShell, or Termux sessions are not easy to safely control after they already exist. They are private terminal sessions. tmux is a shared terminal session:

```text
normal terminal can attach
browser wrapper can observe later if needed
backend can inject text with tmux send-keys/paste-buffer
agent keeps running in one persistent session
```

For V1, there is no need to show a browser terminal. ttyd, WeTTY, and GoTTY were explored as browser terminal renderers, but they are not the trigger itself. They are useful only if we later want a visible terminal panel.

## Prompt Injection

Do not pass user text through a shell string.

Preferred shape:

```python
subprocess.run(["tmux", "load-buffer", "-"], input=message, text=True, check=True)
subprocess.run(["tmux", "paste-buffer", "-t", "design-agent"], check=True)
subprocess.run(["tmux", "send-keys", "-t", "design-agent", "Enter"], check=True)
```

This avoids shell injection and handles quotes, `$`, backticks, and multiline prompts more safely than `tmux send-keys "<raw message>" Enter`.

The formatted message should include:

- design request marker
- document ID
- page/artboard ID
- selected node ID(s)
- layer path or node name if available
- user prompt
- instruction to use VibeDesign MCP tools
- instruction to verify with readback/diagnostics
- instruction not to edit unrelated files or nodes

Example message:

```text
VibeDesign Design Mode request

docId: default
pageId: page-1
selectedNodeIds:
- button-primary

User request:
Make this button blue and slightly bolder.

Use VibeDesign MCP tools to edit the selected node(s). Verify with readback before final response. Do not edit unrelated nodes or files.
```

## Completion Detection

V1 should avoid a full agent completion protocol.

Minimal approach:

```text
frontend stores versionAtSubmit
        |
        v
agent edits via MCP
        |
        v
backend bumps document revision/version on mutation
        |
        v
frontend poll sees version > versionAtSubmit
        |
        v
loading clears
```

Known V1 gap: if the agent errors, asks a question, or makes no document mutation, the loading state may not naturally clear. Add a frontend-only timeout, such as 30 seconds, to show a non-blocking "no change detected" state.

## Safety Rules

- Design Mode is opt-in.
- Select mode remains the safe default.
- The send button is disabled while a request is pending.
- V1 should serialize requests in the frontend to avoid interleaving prompts in the agent's stdin.
- Backend should only inject formatted design requests, not arbitrary shell commands.
- The tmux target session name should be configured and validated.
- If the tmux session is missing, return a clear error and ask the user to start the agent session.
- The backend endpoint should not expose arbitrary `command` or `args` fields.
- The prompt should target node IDs, not visual guesses.

## Relationship To Prior Research

### Agentation

Agentation is the strongest reference for the annotation/request lifecycle:

```text
browser annotation -> structured request -> agent can list/reply/resolve/dismiss
```

VibeDesign should borrow the lifecycle language later:

- pending
- sent
- editing
- resolved
- failed
- agent reply/summary

For V1, keep this lightweight. Do not build the full annotation conversation system yet.

### React Grab

React Grab is the strongest reference for browser-side element selection and prompt UX:

```text
hover/select element -> prompt/comment mode -> element/source context payload
```

VibeDesign should borrow the idea, not the React source-file mapping. VibeDesign identity is:

```text
docId + pageId + nodeId + layer path + node snapshot
```

### OpenCLI

OpenCLI is useful inspiration for driving desktop/web agent surfaces, but it does not solve the current terminal-agent trigger directly. It can inject prompts into Codex/Cursor desktop UIs, while VibeDesign V1 needs to inject into an agent running in a terminal session.

### Multica

Multica proves a robust managed-agent architecture:

```text
web task -> backend queue -> local daemon -> agent CLI -> streamed result
```

That is too heavy for V1. VibeDesign should keep the same basic insight, "browser request reaches local agent," but use tmux as the minimal bridge instead of building a full runtime platform.

### ttyd / WeTTY / GoTTY

These render a terminal in the browser. They are not the trigger mechanism. They can be added later as an optional terminal panel, attached to the same tmux session. They are not required for V1 Design Mode.

## Minimal V1 Plan

1. Ensure Select identity is accurate.
   - Layer row, canvas node, right panel, and MCP target must agree on `nodeId`.

2. Add document revision/version.
   - Increment on backend document mutations used by MCP/API.
   - Expose it in existing document fetch/read responses.

3. Add Design Mode UI state.
   - Explicit toggle.
   - Fixed right-panel prompt.
   - Selected node ID(s) visible in the identity section.
   - Send button disabled while pending.

4. Add backend send endpoint.
   - `POST /api/design-mode/send`.
   - Validate selected document/page/node data.
   - Format message.
   - Inject through tmux buffer/paste/Enter.
   - Return accepted/error status.

5. Add frontend completion behavior.
   - Store `versionAtSubmit`.
   - Clear loading after poll sees version move.
   - Add 30 second no-change timeout.

6. Manual verification.
   - Start agent inside `tmux`.
   - Select a known node.
   - Submit a simple style request.
   - Confirm the agent receives the request.
   - Confirm agent uses MCP to mutate the selected node.
   - Confirm frontend updates from existing sync.

## Deferred

- Floating canvas prompt.
- Multi-agent routing.
- Full annotation thread/reply/resolve system.
- ttyd terminal panel.
- Backend request queue.
- Agent completion protocol.
- Audio/notification style feedback.
- Skills integration.
- SVG/shape-specific Design Mode workflows.
