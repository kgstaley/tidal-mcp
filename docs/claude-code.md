# Working with Claude Code

This project uses [Claude Code](https://claude.ai/claude-code) as a development tool. This document covers how to maintain continuity across sessions and machines.

## Project Configuration

### CLAUDE.md

`CLAUDE.md` in the repo root is automatically loaded by Claude Code at the start of every session. It contains:

- Project architecture and conventions
- Commands for running tests, linting, formatting
- Code standards and error handling patterns
- Git workflow and PR conventions
- tidalapi library reference (verified method signatures, known gotchas)

This is the single source of truth for project context. Update it as new patterns or learnings emerge.

### Plan Files

Long-running plans live in `.claude/plans/`:

```
.claude/plans/
├── session-state.md          # Current progress, what's done, what's next
├── clever-twirling-newell.md # Auto-generated plan (full feature expansion)
└── in-progress/              # Plans actively being worked on
```

## Continuing a Session on Another Machine

### 1. Pull the latest code

```bash
git pull origin <branch-name>
```

### 2. Start Claude Code and point it to the session state

Tell Claude Code to read the session state and continue:

```
Read .claude/plans/session-state.md and continue from where we left off.
```

Claude Code will automatically load `CLAUDE.md` for project conventions. The session state file gives it the specific context: which phase is in progress, what's been completed, what's next, and any key learnings from prior sessions.

### 3. After working, save state before ending

Ask Claude Code to update the session state:

```
Update .claude/plans/session-state.md with current progress, then commit and push.
```

This keeps the state file current for the next session, on any machine.

## Transferring Context Between Accounts

Claude Code stores per-user memory at `~/.claude/projects/<project-hash>/memory/MEMORY.md`. This file is local and does **not** transfer between accounts or machines.

To share context across accounts:

1. **Use `CLAUDE.md` in the repo** — it's version-controlled and loaded automatically for any user
2. **Merge any useful auto-memory content into `CLAUDE.md`** — this is the portable option
3. **Commit session state files** — `.claude/plans/session-state.md` captures progress and decisions

The auto-memory (`~/.claude/`) is best treated as a local cache. The repo-committed `CLAUDE.md` and plan files are the durable, portable source of truth.

## Updating CLAUDE.md

When you discover something important during development (a tidalapi gotcha, a pattern that works well, a convention decision), add it to `CLAUDE.md` and commit it. This way every future session — on any machine, any account — starts with that knowledge.

Examples of things worth adding:
- Library method signatures that differ from docs
- Error handling patterns that solved real bugs
- Testing patterns (what to mock, how to structure fixtures)
- Architecture decisions and their rationale
