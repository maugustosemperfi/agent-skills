---
name: maugusto-agent-tracker
author: maugustosemperfi
description: >
  Generate interactive HTML dashboards to track agent progress in real-time.
  Use this skill whenever you need to track what an agent is doing across multiple concurrent chats,
  monitor task completion, visualize progress through phases, or create a progress report.
  Also trigger when the user mentions tracking progress, monitoring agent work, creating dashboards,
  visualizing task status, or wants to see what an agent has done so far.
  Even if the user just says "track this" or "show me progress", use this skill.
---

# Agent Fleet Tracker

You are a meticulous progress tracker. Your job is to maintain a real-time, structured record of what an agent is doing, then generate an interactive HTML dashboard fleet that shows all agents at a glance and lets you drill into each one.

## Why this matters

When running multiple agent chats in parallel, it's easy to lose track of which agent is where. This skill creates a **two-screen dashboard system**:

- **Fleet Overview** (`fleet.html`) — bird's-eye view of all agents with metrics, status cards, and filters
- **Agent Detail** (`agent-<id>.html`) — deep-dive into a single agent with phases, tasks, timeline, files, and errors

The dashboards help you:
- See which agents are running, blocked, or done
- Understand what each agent is trying to achieve
- Identify unresolved errors and blockers
- Review chronological timelines of all actions
- Track file changes and resource consumption
- Hand off context between agents or to humans

## How it works

All agents write their state to a shared directory (`~/.agent-tracker/`), and a bundled script generates the full dashboard fleet from all JSON files found there.

### Step 1: Initialize the state file

At the start of any tracked session, create `~/.agent-tracker/<your-id>.json` with this structure:

```json
{
  "id": "auth-service",
  "name": "Authentication Microservice",
  "session_id": "auth-impl-2026-06-01",
  "status": "running",
  "current_phase": "research",
  "started_at": "2026-06-01T10:00:00Z",
  "phases": [
    { "name": "research", "status": "in_progress", "progress_percent": 30 },
    { "name": "implementation", "status": "pending", "progress_percent": 0 },
    { "name": "testing", "status": "pending", "progress_percent": 0 }
  ],
  "tasks": {
    "total": 2,
    "done": 1,
    "in_progress": 1,
    "blocked": 0,
    "pending": 0,
    "items": [
      {
        "id": "t1",
        "title": "Read requirements document",
        "status": "done",
        "phase": "research",
        "description": "Extracted 4 key requirements: JWT tokens, email auth, OAuth2, rate limiting.",
        "duration": "5m",
        "tool_calls": 8
      },
      {
        "id": "t2",
        "title": "Explore codebase structure",
        "status": "in_progress",
        "phase": "research",
        "description": "Found Express.js with passport.js. No JWT implementation yet.",
        "duration": "12m",
        "tool_calls": 15
      }
    ]
  },
  "files_changed": [
    { "path": "src/auth.js", "action": "modified", "lines": 34 }
  ],
  "errors": [
    {
      "type": "runtime",
      "message": "Module not found: bcrypt",
      "resolved": true,
      "context": "src/auth.js:3",
      "timestamp": "2026-06-01T10:15:00Z"
    }
  ],
  "timeline": [
    { "time": "10:00", "text": "Session started — reading requirements", "type": "accent" },
    { "time": "10:05", "text": "Requirements extracted: 4 key items", "type": "success" },
    { "time": "10:15", "text": "bcrypt not found — installed via npm", "type": "danger" }
  ],
  "metrics": {
    "elapsed_seconds": 900,
    "tokens_used": 15000,
    "tool_calls": 42
  }
}
```

See `references/state-schema.md` for the complete schema definition.

### Step 2: Update the state as you work

After each significant action, read your JSON file, update the relevant fields, and write it back. Keep the task counts (`total`, `done`, `in_progress`, `blocked`, `pending`) in sync with the items array.

**When to update:**
- Task status changes (pending → in_progress → done/failed/blocked)
- Phase transitions (research → implementation → testing)
- File creations or modifications
- Errors or blockers encountered
- Timeline events (append new entries as they happen)
- Periodic metric updates (every ~10 tool calls or every 5 minutes)

### Step 3: Generate the dashboard fleet

After updating your state file, run:

```bash
python3 <skill-path>/scripts/generate_dashboard.py ~/.agent-tracker/<your-id>.json
```

This scans all `*.json` files in `~/.agent-tracker/`, then generates:
- `~/.agent-tracker/output/fleet.html` — fleet overview
- `~/.agent-tracker/output/agent-<id>.html` — one detail page per agent

Open `fleet.html` in a browser to see all agents. Click any card to drill into that agent's detail page.

### Step 4: Keep it current

Continue updating your JSON and regenerating throughout the session. The fleet dashboard always reflects the latest state of all agents.

## Dashboard structure

### Fleet Overview (fleet.html)

1. **Metrics grid** — Total Agents, Running, Blocked (alert if >0), Completed, Total Tokens
2. **Filter bar** — All / Running / Completed / Blocked / Pending
3. **Agent card grid** — Each card shows name, session_id, status pill, current phase, progress bar, task/file/error stats, elapsed time, and a link to the detail page

### Agent Detail (agent-<id>.html)

1. **Header** — Name, session_id, status pill, header metrics (Progress %, Phase, Tasks, Elapsed, Tokens, Tool Calls, Blockers)
2. **Tabbed interface** with 5 tabs:
   - **Phases** — Progress bars for each phase, color-coded by status
   - **Task Ledger** — Expandable cards with title, status, phase tag, description, duration, tool calls
   - **Timeline** — Vertical timeline with colored dots (accent, success, danger, info)
   - **Files Changed** — Table with monospace paths, action badges, line counts
   - **Errors & Blockers** — Error cards with type, message, context, resolved/unresolved status

## Best practices

- **Update frequently** — dashboards are only useful if current
- **Be specific in task titles** — "Implement user authentication" not "Write code"
- **Write meaningful descriptions** — explain what was done and why
- **Track errors honestly** — they're valuable context for understanding progress
- **Append timeline events** — they tell the story of what happened
- **Keep counts in sync** — update `tasks.done`, `tasks.in_progress`, etc. when statuses change
- **Use consistent phase names** — research, planning, implementation, testing, review, deployment
- **Set `resolved: true`** on errors when they're fixed
- **Use descriptive `context`** on errors (file:line or description of blocker)

## When to use this skill

Use when:
- Running multiple agent sessions and need to track them
- The user asks for progress updates or status reports
- You want a visual record of work done
- Handing off context to another agent or human
- Debugging why an agent got stuck

Don't use for:
- Simple one-off tasks that complete in a single step
- Sessions where the user explicitly says they don't want tracking
- Quick questions or conversational interactions
