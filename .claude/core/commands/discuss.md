---
description: Read-only thinking partner. Explore and reason about the code/topic and discuss options — makes NO changes. Edit/Write removed from the tool pool for the turn.
disable-model-invocation: true
disallowed-tools: Edit, Write, NotebookEdit, Agent
allowed-tools: Read, Grep, Glob, Bash(git log:*), Bash(git diff:*), Bash(git status:*), Bash(git show:*), Bash(git blame:*), WebSearch, WebFetch
---

# /discuss — read-only thinking partner

Discuss the topic / question in `$ARGUMENTS`. This is a **read-only** mode: investigate, reason, and
talk through options — but **make no changes to anything**.

How the read-only posture is enforced (be honest about the mechanism, don't overclaim):
- `disallowed-tools` **removes** `Edit`, `Write`, `NotebookEdit`, and `Agent` from the tool pool
  while this command is active — so you physically cannot modify files or spawn an editing subagent
  on the `/discuss` turn. Per the skills spec this restriction **clears on the user's next message**,
  so it is a per-turn guard: if the conversation continues and you need it read-only again, the user
  re-invokes `/discuss`.
- `allowed-tools` pre-approves read-only tools (Read/Grep/Glob, read-only `git`, web) so they run
  without permission prompts. It does **not** by itself restrict anything — the restriction comes
  from `disallowed-tools` above. `Bash` remains callable but only read-only `git` is pre-approved;
  any other shell command would require the user's explicit approval, which you should not seek here.

Even if a fix seems trivial, do not try to make it in this mode. If the discussion concludes a change
is wanted, say so and tell the user to run `/dev` or `/fix` (or approve it in plan mode).

## How to work

1. **Gather context yourself** with Read / Grep / Glob and read-only `git` (log, diff, status, show,
   blame). Do not spawn subagents — staying single-context keeps the read-only posture airtight.
2. **Reason out loud.** Lay out what you found, the tradeoffs, the options, and the risks. Where
   relevant, ground claims in specific `file:line` references and, for external questions, cite
   sources from WebSearch/WebFetch.
3. **Recommend, don't act.** End with a clear recommendation (or a small set of options with their
   tradeoffs) and the concrete next step the user would take to execute it.

Be direct and substantive. This mode exists for thinking, not doing.
