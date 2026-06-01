---
name: maugusto-update-local-skills
author: maugustosemperfi
description: >
  Pull skills from a GitHub repo and install/update them into ~/.agents/skills/.
  Use this skill ONLY when the user explicitly types "maugusto-update-local-skills" or asks to
  pull/install skills from a repo into their local setup. This is a manual, on-demand skill — do not
  trigger it for general git operations, skill creation, or skill-related conversations.
---

# Update Local Skills

Pull skills from a GitHub repo and install or update them in `~/.agents/skills/`.

## Workflow

### 1. Identify the source repo

The user should provide a GitHub repo reference. Accept any of these formats:
- Full URL: `https://github.com/maugustosemperfi/agent-skills`
- Short form: `maugustosemperfi/agent-skills`
- Just the repo name if it's already cloned locally under `~/dev/`

If no repo is specified, default to `maugustosemperfi/agent-skills`.

### 2. Clone or pull the repo

- If the repo is already cloned locally (check `~/dev/` for matching directories), pull latest from `origin main`.
- If not cloned, clone it to a temp location (`/tmp/skills-repo-<timestamp>/`).

### 3. Discover repo skills

Scan the repo root for directories containing a `SKILL.md` file. Each such directory is a skill.

### 4. Compare and install

For each skill in the repo:

- **New skill** (not in `~/.agents/skills/`): Copy the entire skill directory into `~/.agents/skills/`.
- **Existing skill** (already in `~/.agents/skills/`): Diff the repo version against the local version.
  - If identical: skip, report as "up to date".
  - If different: this is a **conflict**. Present the user with options:
    1. **Overwrite local** — replace the local version with the repo one
    2. **Keep local** — leave the local version untouched
    3. **Show diff** — display the differences so the user can decide

### 5. Report results

Summarize what happened:
- Skills installed (new)
- Skills updated (overwritten)
- Skills skipped (up to date or kept local)
- Any conflicts and how they were resolved

## Important details

- The target directory is always `~/.agents/skills/`
- Use `diff -rq` for quick comparison, then `diff -ru` for detailed conflict display
- If cloning to temp, clean up the temp directory when done
- Never overwrite local skills without explicit user approval when conflicts exist
- If the repo contains non-skill directories (no SKILL.md), ignore them silently
- If no skills are found in the repo, tell the user and stop
