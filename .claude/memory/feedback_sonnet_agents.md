---
name: Always use Sonnet model for agents
description: When orchestrating subagents via the Agent tool, always pass model="sonnet" — never default to Opus or Haiku for spawned agents
type: feedback
originSessionId: 1f5b6b5a-ea47-4ba9-87d4-8690f44ca852
---
Always pass `model: "sonnet"` when spawning subagents via the Agent tool.

**Why:** User explicitly instructed this on 2026-04-18 during an orchestration task. They want Sonnet as the standard for delegated work in this project.

**How to apply:** Every Agent tool invocation must include `model: "sonnet"` unless the user specifies otherwise for a particular call. Applies to all subagent_types (Explore, general-purpose, Plan, etc.).
