# State Schema Reference

This document defines the complete JSON schema for agent state files stored in `~/.agent-tracker/`.

## File Naming

Each agent writes its state to `~/.agent-tracker/<id>.json` where `<id>` matches the `id` field in the JSON.

## Root Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Short slug used for filenames and URLs (e.g., `auth-service`) |
| `name` | string | Yes | Human-readable name (e.g., "Authentication Microservice") |
| `session_id` | string | Yes | Unique session identifier (e.g., `auth-impl-2026-06-01`) |
| `status` | enum | Yes | One of: `running`, `done`, `blocked`, `pending` |
| `current_phase` | string | Yes | Name of the currently active phase |
| `started_at` | string (ISO 8601) | Yes | When the session started |
| `phases` | array of Phase | Yes | Ordered list of phases |
| `tasks` | Tasks | Yes | Task summary counts and item list |
| `files_changed` | array of FileChange | No | Files created or modified |
| `errors` | array of Error | No | Errors or blockers encountered |
| `timeline` | array of TimelineEvent | No | Chronological activity log |
| `metrics` | Metrics | Yes | Resource usage and timing |

## Phase Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Phase identifier (e.g., "research", "implementation") |
| `status` | enum | Yes | One of: `pending`, `in_progress`, `done`, `skipped` |
| `progress_percent` | number (0-100) | Yes | How much of this phase is complete |

**Standard phase names:** `research`, `planning`, `implementation`, `testing`, `review`, `deployment`. Use custom names when needed.

## Tasks Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total` | number | Yes | Total number of tasks |
| `done` | number | Yes | Count of completed tasks |
| `in_progress` | number | Yes | Count of in-progress tasks |
| `blocked` | number | Yes | Count of blocked tasks |
| `pending` | number | Yes | Count of pending tasks |
| `items` | array of TaskItem | Yes | List of all tasks |

## TaskItem Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique task identifier (e.g., "t1", "auth-impl") |
| `title` | string | Yes | Short description of the task |
| `status` | enum | Yes | One of: `pending`, `in_progress`, `done`, `failed`, `blocked` |
| `phase` | string | Yes | Which phase this task belongs to |
| `description` | string | No | Detailed explanation of what was done and why |
| `duration` | string | No | Human-readable duration (e.g., "18m", "1h 30m") |
| `tool_calls` | number | No | Number of tool invocations for this task |

**Status transitions:**
- `pending` → `in_progress` (when work begins)
- `in_progress` → `done` (when successfully completed)
- `in_progress` → `failed` (when unable to complete)
- `in_progress` → `blocked` (when waiting on external input)
- `blocked` → `in_progress` (when unblocked)

## FileChange Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | File path relative to working directory |
| `action` | enum | Yes | One of: `created`, `modified`, `deleted`, `renamed` |
| `lines` | number | No | Number of lines added/changed |

## Error Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Error category (e.g., `runtime`, `config`, `dependency`, `type-error`, `data`, `validation`) |
| `message` | string | Yes | What went wrong |
| `resolved` | boolean | Yes | Whether the error has been resolved |
| `context` | string | No | Where it occurred (e.g., `src/auth/session-store.ts:14`) |
| `timestamp` | string (ISO 8601) | Yes | When the error occurred |

## TimelineEvent Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `time` | string | Yes | Short time display (e.g., "10:00", "14:30") |
| `text` | string | Yes | What happened |
| `type` | enum | Yes | One of: `accent`, `success`, `danger`, `info` |

## Metrics Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elapsed_seconds` | number | Yes | Total time elapsed since session start |
| `tokens_used` | number | Yes | Approximate token consumption |
| `tool_calls` | number | Yes | Number of tool invocations |

## Example: Complete State

```json
{
  "id": "auth-service",
  "name": "Authentication Microservice",
  "session_id": "auth-impl-2026-06-01",
  "status": "running",
  "current_phase": "implementation",
  "started_at": "2026-06-01T10:00:00Z",
  "phases": [
    { "name": "research", "status": "done", "progress_percent": 100 },
    { "name": "planning", "status": "done", "progress_percent": 100 },
    { "name": "implementation", "status": "in_progress", "progress_percent": 65 },
    { "name": "testing", "status": "pending", "progress_percent": 0 }
  ],
  "tasks": {
    "total": 8,
    "done": 5,
    "in_progress": 1,
    "blocked": 0,
    "pending": 2,
    "items": [
      {
        "id": "t1",
        "title": "Analyze existing auth flow and identify gaps",
        "status": "done",
        "phase": "research",
        "description": "Reviewed current OAuth2 implementation, documented token refresh edge cases.",
        "duration": "18m",
        "tool_calls": 12
      },
      {
        "id": "t2",
        "title": "Implement middleware for route protection",
        "status": "in_progress",
        "phase": "implementation",
        "description": "Express middleware validating JWT, check revocation list, attach user context.",
        "duration": "28m",
        "tool_calls": 16
      },
      {
        "id": "t3",
        "title": "Write integration tests for auth flows",
        "status": "pending",
        "phase": "testing"
      }
    ]
  },
  "files_changed": [
    { "path": "src/auth/routes.ts", "action": "created", "lines": 142 },
    { "path": "src/auth/token-service.ts", "action": "created", "lines": 238 },
    { "path": "src/config/redis.ts", "action": "modified", "lines": 12 }
  ],
  "errors": [
    {
      "type": "runtime",
      "message": "Redis connection timeout after 5000ms on session-store initialization",
      "resolved": true,
      "context": "src/auth/session-store.ts:14",
      "timestamp": "2026-06-01T11:23:00Z"
    }
  ],
  "timeline": [
    { "time": "10:00", "text": "Session started — researching auth flow", "type": "accent" },
    { "time": "10:18", "text": "Completed research phase, 3 documents analyzed", "type": "success" },
    { "time": "11:23", "text": "Redis connection timeout — retried with exponential backoff", "type": "danger" },
    { "time": "12:15", "text": "Login endpoint passing all test scenarios", "type": "success" }
  ],
  "metrics": {
    "elapsed_seconds": 3600,
    "tokens_used": 45000,
    "tool_calls": 127
  }
}
```

## Validation Rules

1. **Timestamps**: ISO 8601 format (e.g., `2026-06-01T10:00:00Z`)
2. **Progress percentages**: Integers between 0 and 100
3. **Phase consistency**: If a phase is `done`, its `progress_percent` must be 100
4. **Task counts**: `total` should equal `done + in_progress + blocked + pending`
5. **Current phase**: Must match one of the phase names in the `phases` array
6. **Unique IDs**: Task IDs must be unique within the session
7. **Agent ID**: Must be filesystem-safe (lowercase, hyphens, no spaces or special characters)

## Updating the State

When updating the state file:

1. **Read the current file** — don't start from scratch
2. **Update only what changed** — preserve existing data
3. **Keep counts in sync** — update `tasks.total`, `tasks.done`, etc. when task statuses change
4. **Append timeline events** — add new events as they happen
5. **Write atomically** — write to a temp file first, then rename to avoid corruption
