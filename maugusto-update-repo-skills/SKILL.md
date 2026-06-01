---
name: maugusto-update-repo-skills
author: maugustosemperfi
description: >
  Sync locally-signed skills from ~/.agents/skills/ into the ~/dev/skills/ repo.
  Use this skill ONLY when the user explicitly types "maugusto-update-repo-skills" or asks to
  push/update their signed skills to the skills repo. This is a manual, on-demand skill — do not
  trigger it for general git operations, repo updates, or skill-related conversations.
---

# Update Repo Skills

Sync skills authored by `maugustosemperfi` from `~/.agents/skills/` into the local skills repo at `~/dev/skills/`, then commit and push.

## Workflow

### 1. Discover signed local skills

Scan `~/.agents/skills/*/SKILL.md` frontmatter for `author: maugustosemperfi`. Collect the directory name and skill name for each match.

### 2. Compare with repo

For each signed skill found locally:

- **New skill** (not in `~/dev/skills/`): Copy the entire skill directory into `~/dev/skills/`.
- **Existing skill** (already in `~/dev/skills/`): Diff the local version against the repo version.
  - If identical: skip, report as "up to date".
  - If different: this is a **conflict**. Present the user with options:
    1. **Overwrite repo** — replace the repo version with the local one
    2. **Keep repo** — leave the repo version untouched
    3. **Show diff** — display the differences so the user can decide

### 3. Commit and push

After all skills are processed:

- Stage all changes in `~/dev/skills/`
- If there are changes to commit, create a commit with a descriptive message listing what was added/updated
- Push to `origin main`
- Report the final state: what was synced, what was skipped, any conflicts resolved

## Important details

- Only sync skills with `author: maugustosemperfi` in the SKILL.md frontmatter — never sync unsigned skills
- Use `diff -rq` for quick comparison, then `diff -ru` for detailed conflict display
- The repo path is `~/dev/skills/` — do not look elsewhere
- If `~/dev/skills/` doesn't exist or isn't a git repo, tell the user and stop
- If there are no signed skills to sync, say so and stop
- Never force-push
