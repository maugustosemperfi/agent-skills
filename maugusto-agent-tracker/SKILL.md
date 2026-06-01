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

# Agent Progress Tracker

You are a meticulous progress tracker. Your job is to maintain a real-time, structured record of what an agent is doing, then generate an interactive HTML dashboard that makes it easy to scan progress across multiple concurrent sessions.

## Why this matters

When running multiple agent chats in parallel, it's easy to lose track of which agent is where. This skill creates a comprehensive, visual progress report for each session so you can quickly understand:
- **What the agent is trying to achieve** (objectives and goals)
- **What's blocking progress** (unresolved errors and blocked tasks)
- **What happened so far** (chronological timeline of all actions)
- **What phase the agent is in** (researching, coding, testing, etc.)
- **Which tasks are done, in progress, or blocked** with detailed summaries
- **What files were created or modified** and which task produced them
- **How much time and resources have been consumed**

The dashboard serves as both a real-time status report and a historical record that can be used to:
- Hand off context to another agent or human
- Debug why an agent got stuck
- Review what was done in a session
- Resume work in a new session with full context

## How it works

You'll maintain a JSON state file (`progress.json`) that captures the current state of work, then use a bundled script to generate an interactive HTML dashboard from that state.

### Step 1: Initialize the state file

At the start of any tracked session, create a `progress.json` file in the working directory with this structure:

```json
{
  "session_id": "unique-identifier",
  "session_name": "Human-readable name",
  "started_at": "2026-06-01T10:00:00Z",
  "current_phase": "research",
  "objectives": [
    {
      "description": "Implement secure user authentication",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "description": "Add rate limiting to prevent brute force",
      "status": "pending",
      "priority": "medium"
    }
  ],
  "phases": [
    {
      "name": "research",
      "status": "in_progress",
      "progress_percent": 30,
      "started_at": "2026-06-01T10:00:00Z"
    },
    {
      "name": "implementation",
      "status": "pending",
      "progress_percent": 0
    },
    {
      "name": "testing",
      "status": "pending",
      "progress_percent": 0
    }
  ],
  "tasks": [
    {
      "id": "task-1",
      "description": "Read requirements document",
      "status": "done",
      "phase": "research",
      "completed_at": "2026-06-01T10:05:00Z",
      "summary": "Extracted 4 key requirements: JWT tokens, email auth, OAuth2, rate limiting.",
      "history": [
        {
          "timestamp": "2026-06-01T10:00:00Z",
          "action": "Read requirements document",
          "tool": "Read"
        }
      ]
    },
    {
      "id": "task-2",
      "description": "Explore codebase structure",
      "status": "in_progress",
      "phase": "research",
      "summary": "Found Express.js with passport.js. No JWT implementation yet.",
      "files": ["src/auth.js"],
      "tags": ["Research"]
    }
  ],
  "files_changed": [
    {
      "path": "src/auth.js",
      "action": "modified",
      "description": "Added password validation function with bcrypt",
      "task_id": "task-2"
    }
  ],
  "errors": [
    {
      "timestamp": "2026-06-01T10:15:00Z",
      "description": "Module not found: bcrypt",
      "resolution": "Installed bcrypt via npm"
    }
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

After each significant action (completing a task, changing phase, encountering an error, modifying a file), update the `progress.json` file. Keep updates atomic and consistent.

**When to update:**
- Task status changes (pending → in_progress → done/failed)
- Phase transitions (research → implementation → testing)
- File creations or modifications
- Errors or blockers encountered
- Periodic metric updates (every ~10 tool calls or every 5 minutes)

**How to update:**
Read the current `progress.json`, modify the relevant fields, and write it back. Don't rewrite the entire file from scratch — preserve existing data.

### Step 3: Generate the HTML dashboard

After updating the state file, run the generation script to produce the HTML dashboard:

```bash
python3 <skill-path>/scripts/generate_dashboard.py progress.json
```

This creates `dashboard.html` in the same directory. The HTML is interactive and includes:
- Objectives & goals with priority and status tracking
- Blockers panel showing unresolved errors and blocked tasks
- Global timeline of everything that happened (merged from task histories, file changes, and errors)
- Phase progress bars with percentages
- Expandable task cards with summaries, file lists, and activity logs
- File changes log with code editor styling
- Metrics summary (time, tokens, tool calls)
- Auto-refresh capability (if opened in a browser, it reloads when the JSON changes)

### Step 4: Keep it current

Continue updating `progress.json` and regenerating `dashboard.html` throughout the session. The dashboard will always reflect the latest state.

## Dashboard structure

The generated HTML follows a consistent layout designed to give complete visibility into what the agent is doing:

1. **Header**: Session name, current phase, and auto-sync indicator
2. **Metrics bento**: Time elapsed, tokens used, tool calls, task completion progress, and blocker count
3. **Objectives & Goals**: Top-level goals with status (done/in_progress/pending/blocked), priority badges, and notes
4. **Blockers panel**: Prominent display of unresolved errors and blocked tasks (only shown when blockers exist)
5. **Phase progress**: Visual timeline of phases with progress bars and status indicators
6. **What Happened (Timeline)**: Chronological merge of all task histories, file changes, and errors - shows the complete story of what the agent did
7. **Task ledger**: Expandable cards for each task showing:
   - Summary of what was done and why
   - Files changed by this task with descriptions
   - Activity log with tool usage
   - Notes and timestamps
8. **Files changed**: Code editor-style view of all modified files with action badges and timestamps

This structure doesn't change from session to session, making it easy to scan multiple dashboards quickly.

## Best practices

- **Update frequently**: The dashboard is only useful if it's current. Update after every major action.
- **Be specific in task descriptions**: "Implement user authentication" is better than "Write code"
- **Write meaningful summaries**: Each task's `summary` field should explain what was done and why, not just restate the description
- **Track errors honestly**: Don't hide failures — they're valuable context for understanding progress
- **Use consistent phase names**: Stick to a standard set (research, planning, implementation, testing, review) unless the work requires custom phases
- **Include file descriptions**: Don't just list "modified src/auth.js" — explain what changed and why
- **Log history entries**: Add `history` entries to tasks to create a detailed timeline of actions taken
- **Define objectives upfront**: Add `objectives` at session start to show what you're trying to achieve
- **Link files to tasks**: Use `task_id` in `files_changed` entries to show which task produced which files
- **Mark blockers clearly**: When a task is blocked, set status to `blocked` and add a `notes` field explaining why

## When to use this skill

Use this skill when:
- You're running multiple agent sessions and need to track them
- The user asks for progress updates or status reports
- You want to create a visual record of work done
- You need to hand off context to another agent or human
- You're debugging why an agent got stuck (the error log helps)

Don't use this skill for:
- Simple one-off tasks that complete in a single step
- Sessions where the user explicitly says they don't want tracking
- Quick questions or conversational interactions

## Integration with other workflows

This skill pairs well with:
- **code-review**: Track the review process itself, then generate a dashboard showing what was reviewed
- **prd-to-plan**: Use the plan's phases as your tracking phases
- **skill-creator**: Track the iteration loop (draft → test → review → improve)

The generated `dashboard.html` can be opened in any browser, shared via file transfer, or later integrated into a web application for real-time monitoring.
