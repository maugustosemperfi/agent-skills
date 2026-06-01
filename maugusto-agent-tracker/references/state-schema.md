# State Schema Reference

This document defines the complete JSON schema for `progress.json`.

## Root Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | Unique identifier for this session (e.g., UUID or timestamp-based) |
| `session_name` | string | Yes | Human-readable name (e.g., "Implement user authentication") |
| `started_at` | string (ISO 8601) | Yes | When the session started |
| `current_phase` | string | Yes | Name of the currently active phase |
| `objectives` | array of Objective | No | Top-level goals this session aims to achieve |
| `phases` | array of Phase | Yes | Ordered list of phases |
| `tasks` | array of Task | Yes | List of all tasks |
| `files_changed` | array of FileChange | No | Files created or modified |
| `errors` | array of Error | No | Errors or blockers encountered |
| `metrics` | Metrics | Yes | Resource usage and timing |

## Objective Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | What this objective aims to achieve |
| `status` | enum | Yes | One of: `pending`, `in_progress`, `done`, `blocked` |
| `priority` | enum | No | One of: `high`, `medium`, `low` (default: `medium`) |
| `notes` | string | No | Additional context or progress notes |

## Phase Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Phase identifier (e.g., "research", "implementation") |
| `status` | enum | Yes | One of: `pending`, `in_progress`, `done`, `skipped` |
| `progress_percent` | number (0-100) | Yes | How much of this phase is complete |
| `started_at` | string (ISO 8601) | No | When this phase started (if status is not `pending`) |
| `completed_at` | string (ISO 8601) | No | When this phase completed (if status is `done`) |

**Standard phase names:**
- `research` — Understanding requirements, exploring codebase
- `planning` — Designing approach, breaking down tasks
- `implementation` — Writing code, creating files
- `testing` — Running tests, verifying correctness
- `review` — Self-review, addressing issues
- `deployment` — Deploying, publishing, or delivering

Use custom phase names when the work doesn't fit these categories.

## Task Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique task identifier (e.g., "task-1", "auth-impl") |
| `description` | string | Yes | What this task involves |
| `status` | enum | Yes | One of: `pending`, `in_progress`, `done`, `failed`, `blocked` |
| `phase` | string | Yes | Which phase this task belongs to |
| `started_at` | string (ISO 8601) | No | When work on this task started |
| `completed_at` | string (ISO 8601) | No | When this task completed or failed |
| `notes` | string | No | Additional context or observations |
| `summary` | string | No | Brief explanation of what was done and why (shown in expanded task view) |
| `files` | array of strings | No | File paths this task created or modified |
| `tags` | array of strings | No | Categorization labels (e.g., "API", "Security") |
| `history` | array of HistoryEntry | No | Chronological log of actions taken during this task |

**Status transitions:**
- `pending` → `in_progress` (when work begins)
- `in_progress` → `done` (when successfully completed)
- `in_progress` → `failed` (when unable to complete)
- `in_progress` → `blocked` (when waiting on external input)
- `blocked` → `in_progress` (when unblocked)

## HistoryEntry Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO 8601) | Yes | When this action occurred |
| `action` | string | Yes | What happened (e.g., "Read file src/auth.js", "Ran npm test") |
| `tool` | string | No | Which tool was used (e.g., "Read", "Bash", "Edit", "Write") |

## FileChange Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | File path relative to working directory |
| `action` | enum | Yes | One of: `created`, `modified`, `deleted`, `renamed` |
| `description` | string | Yes | What changed and why |
| `timestamp` | string (ISO 8601) | No | When this change occurred |
| `task_id` | string | No | ID of the task that caused this change (links to Task object) |

## Error Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO 8601) | Yes | When the error occurred |
| `description` | string | Yes | What went wrong |
| `resolution` | string | No | How it was resolved (if resolved) |
| `severity` | enum | No | One of: `low`, `medium`, `high`, `critical` (default: `medium`) |

## Metrics Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elapsed_seconds` | number | Yes | Total time elapsed since session start |
| `tokens_used` | number | Yes | Approximate token consumption |
| `tool_calls` | number | Yes | Number of tool invocations |
| `files_created` | number | No | Count of files created |
| `files_modified` | number | No | Count of files modified |

## Example: Complete State

```json
{
  "session_id": "auth-impl-2026-06-01",
  "session_name": "Implement user authentication",
  "started_at": "2026-06-01T10:00:00Z",
  "current_phase": "implementation",
  "objectives": [
    {
      "description": "Implement secure user registration and login",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "description": "Add JWT-based session management",
      "status": "pending",
      "priority": "high"
    },
    {
      "description": "Integrate with existing user database",
      "status": "done",
      "priority": "medium"
    }
  ],
  "phases": [
    {
      "name": "research",
      "status": "done",
      "progress_percent": 100,
      "started_at": "2026-06-01T10:00:00Z",
      "completed_at": "2026-06-01T10:15:00Z"
    },
    {
      "name": "planning",
      "status": "done",
      "progress_percent": 100,
      "started_at": "2026-06-01T10:15:00Z",
      "completed_at": "2026-06-01T10:25:00Z"
    },
    {
      "name": "implementation",
      "status": "in_progress",
      "progress_percent": 60,
      "started_at": "2026-06-01T10:25:00Z"
    },
    {
      "name": "testing",
      "status": "pending",
      "progress_percent": 0
    }
  ],
  "tasks": [
    {
      "id": "research-1",
      "description": "Read PRD and extract auth requirements",
      "status": "done",
      "phase": "research",
      "started_at": "2026-06-01T10:00:00Z",
      "completed_at": "2026-06-01T10:08:00Z",
      "summary": "Extracted key auth requirements: JWT-based tokens, email/password login, OAuth2 support, rate limiting on auth endpoints.",
      "history": [
        {
          "timestamp": "2026-06-01T10:00:00Z",
          "action": "Read requirements document",
          "tool": "Read"
        },
        {
          "timestamp": "2026-06-01T10:05:00Z",
          "action": "Identified 4 auth requirements",
          "tool": "Task"
        }
      ]
    },
    {
      "id": "research-2",
      "description": "Explore existing auth patterns in codebase",
      "status": "done",
      "phase": "research",
      "started_at": "2026-06-01T10:08:00Z",
      "completed_at": "2026-06-01T10:15:00Z",
      "summary": "Found existing Express setup with passport.js. No JWT implementation yet. Database uses Sequelize ORM."
    },
    {
      "id": "plan-1",
      "description": "Design authentication flow",
      "status": "done",
      "phase": "planning",
      "started_at": "2026-06-01T10:15:00Z",
      "completed_at": "2026-06-01T10:20:00Z",
      "summary": "Designed flow: Register → verify email → login → JWT issued → middleware validates on protected routes."
    },
    {
      "id": "impl-1",
      "description": "Create user model and database schema",
      "status": "done",
      "phase": "implementation",
      "started_at": "2026-06-01T10:25:00Z",
      "completed_at": "2026-06-01T10:35:00Z",
      "summary": "Created User model with email (unique, indexed), password_hash, created_at, updated_at. Added migration for users table.",
      "files": ["src/models/user.js", "migrations/001_create_users.js"],
      "tags": ["Database"],
      "history": [
        {
          "timestamp": "2026-06-01T10:25:00Z",
          "action": "Created user model file",
          "tool": "Write"
        },
        {
          "timestamp": "2026-06-01T10:28:00Z",
          "action": "Created database migration",
          "tool": "Write"
        },
        {
          "timestamp": "2026-06-01T10:32:00Z",
          "action": "Ran migration successfully",
          "tool": "Bash"
        }
      ]
    },
    {
      "id": "impl-2",
      "description": "Implement registration endpoint",
      "status": "done",
      "phase": "implementation",
      "started_at": "2026-06-01T10:35:00Z",
      "completed_at": "2026-06-01T10:50:00Z",
      "summary": "POST /auth/register: validates input, hashes password with bcrypt (12 rounds), creates user, returns JWT.",
      "files": ["src/routes/auth.js", "src/utils/validation.js"],
      "tags": ["API", "Security"]
    },
    {
      "id": "impl-3",
      "description": "Implement login endpoint",
      "status": "in_progress",
      "phase": "implementation",
      "started_at": "2026-06-01T10:50:00Z",
      "summary": "POST /auth/login: validates credentials, compares bcrypt hash, issues JWT with 24h expiry.",
      "files": ["src/routes/auth.js"],
      "tags": ["API", "Security"],
      "history": [
        {
          "timestamp": "2026-06-01T10:50:00Z",
          "action": "Started implementing login route",
          "tool": "Edit"
        },
        {
          "timestamp": "2026-06-01T10:55:00Z",
          "action": "Added credential validation logic",
          "tool": "Edit"
        }
      ]
    },
    {
      "id": "impl-4",
      "description": "Add JWT token generation",
      "status": "pending",
      "phase": "implementation"
    },
    {
      "id": "test-1",
      "description": "Write unit tests for auth functions",
      "status": "pending",
      "phase": "testing"
    }
  ],
  "files_changed": [
    {
      "path": "src/models/user.js",
      "action": "created",
      "description": "User model with email, password hash, and timestamps",
      "timestamp": "2026-06-01T10:28:00Z",
      "task_id": "impl-1"
    },
    {
      "path": "src/routes/auth.js",
      "action": "created",
      "description": "Authentication routes (register, login, logout)",
      "timestamp": "2026-06-01T10:40:00Z",
      "task_id": "impl-2"
    },
    {
      "path": "src/middleware/auth.js",
      "action": "created",
      "description": "JWT verification middleware",
      "timestamp": "2026-06-01T10:45:00Z",
      "task_id": "impl-2"
    }
  ],
  "errors": [
    {
      "timestamp": "2026-06-01T10:30:00Z",
      "description": "bcrypt module not found",
      "resolution": "Installed bcrypt via npm install bcrypt",
      "severity": "medium"
    }
  ],
  "metrics": {
    "elapsed_seconds": 3600,
    "tokens_used": 45000,
    "tool_calls": 127,
    "files_created": 3,
    "files_modified": 0
  }
}
```

## Validation Rules

1. **Timestamps**: All timestamps must be ISO 8601 format (e.g., `2026-06-01T10:00:00Z`)
2. **Progress percentages**: Must be integers between 0 and 100
3. **Phase consistency**: If a phase is `done`, its `progress_percent` must be 100
4. **Task consistency**: Tasks in `pending` phases should typically be `pending` themselves
5. **Current phase**: Must match one of the phase names in the `phases` array
6. **Unique IDs**: Task IDs must be unique within the session

## Updating the State

When updating `progress.json`:

1. **Read the current file** — don't start from scratch
2. **Update only what changed** — preserve existing data
3. **Maintain consistency** — if you mark a task as done, consider updating the phase progress
4. **Add timestamps** — when tasks or phases transition, record when it happened
5. **Write atomically** — write to a temp file first, then rename to avoid corruption

Example update flow:

```bash
# Read current state
cat progress.json > progress.json.backup

# Modify in your code (pseudocode)
# state.tasks.find(t => t.id === "impl-3").status = "done"
# state.tasks.find(t => t.id === "impl-3").completed_at = now()
# state.phases.find(p => p.name === "implementation").progress_percent = 75

# Write back
# write_json("progress.json.tmp", state)
# rename("progress.json.tmp", "progress.json")
```
