---
name: Proactive review and learning
description: User expects Claude to proactively create meta-skills for review, docs, logging, and learning — not wait to be told
type: feedback
---

When building systems (trading engine, optimization, etc.), proactively create a `/review` or similar meta-skill that covers the full loop: check logs, verify docs are current, audit memory, and plan next steps.

**Why:** The user had to manually ask for a system review and then point out that this should have been a skill from the start. Quote: "you should have a skill that do all this things, docs, logs, learns, code again. learn"

**How to apply:** After any major feature is shipped (new tables, new worker jobs, new slash commands), check whether existing skills cover the new surface area. If not, update them. Also consider whether a new meta-skill is needed to tie things together. Don't wait for the user to notice gaps — anticipate them.
