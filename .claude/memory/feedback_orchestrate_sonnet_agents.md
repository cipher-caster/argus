---
name: Orchestrate Sonnet agents for mid-to-complex tasks
description: For mid to complex tasks, spawn Sonnet subagents to do the work rather than handling everything inline
type: feedback
originSessionId: 302c4b75-146f-4734-a3d9-d3fd60911c30
---
For mid to complex tasks, orchestrate the work by spawning Sonnet subagents via the Agent tool — don't do it all inline in the main conversation.

**Why:** User explicitly prefers this pattern for anything beyond simple/quick tasks.

**How to apply:** When a task involves multiple steps, multiple files, exploration + implementation, or any meaningful scope — delegate to one or more Agent(subagent_type=..., model="sonnet") calls instead of doing it yourself directly. Always pass model="sonnet" per the existing memory rule.
