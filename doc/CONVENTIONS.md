# Documentation Conventions

These rules keep VibeDesignLocalMCP-2 documentation useful for both humans and agents.

## Current Truth First

Docs should describe the current accepted system, not abandoned plans or speculative ideas.

Use `archive/` only for historical recovery. Do not copy roadmap or architecture direction from archived material unless a task explicitly asks for it.

## Scope

Each doc should have one clear purpose.

- Architecture docs explain how the current system works.
- Roadmap docs explain what should happen next.
- Reference docs define stable behavior and contracts.
- Checkpoint docs record test plans and accepted test results.
- Task history belongs in `task.md` and `action_log2.md`, not in reference docs.

## Style

- Start with the practical answer.
- Keep sections short.
- Prefer concrete file paths and tool names over broad descriptions.
- Mark non-goals explicitly when they prevent scope drift.
- Avoid marketing language.
- Avoid future-tense promises unless the file is a roadmap.

## Source Of Truth

The active repo is `VibeDesignLocalMCP-2`.

Active planning files:

- `task.md`
- `action_log2.md`
- `doc/roadmap.md`
- `doc/architecture.md`

Historical source:

- `archive/action-log.md`

Dead reference:

- `VibeDesignLocalMCP-archive`

Do not use `VibeDesignLocalMCP-archive` for new implementation direction.

## Guardrails

- No Design Mode work unless explicitly re-approved later.
- No broad frontend rebuild.
- No speculative feature systems.
- No package-manager-specific app code.
- No manual Text/Frame/Rectangle toolbar restoration.
- No generic manual element drag/resize until a deliberate layout mutation model exists.
