# Agent Skills

Personal Codex and agent skills by Marcos Augusto.

This repository is a small toolkit for making agent work easier to run, observe, review, and keep in sync across machines. Each top-level directory that contains a `SKILL.md` file is a standalone skill.

## Skills

| Skill | Purpose | Use it when |
| --- | --- | --- |
| `maugusto-agent-tracker` | Generates an interactive HTML dashboard fleet from JSON state files in `~/.agent-tracker/`. | You are running one or more agents and want a progress dashboard with phases, tasks, files, errors, and timelines. |
| `maugusto-agent-work-review` | Reviews agent-made code changes against a PRD, ADR, RFC, plan, or spec. | You need a strict second pass that checks whether implementation actually matches the driving document. |
| `maugusto-update-local-skills` | Pulls skills from a GitHub repo into `~/.agents/skills/`. | You want to install or update local skills from this repo or another skills repo. |
| `maugusto-update-repo-skills` | Syncs locally authored skills from `~/.agents/skills/` back into this repo. | You have edited local skills and want to publish the signed versions here. |

## Repository layout

```text
.
├── maugusto-agent-tracker/
│   ├── SKILL.md
│   ├── evals/evals.json
│   ├── references/state-schema.md
│   ├── scripts/generate_dashboard.py
│   └── tests/test_dashboard.py
├── maugusto-agent-work-review/
│   ├── SKILL.md
│   ├── evals/evals.json
│   └── references/review-format.md
├── maugusto-update-local-skills/
│   └── SKILL.md
└── maugusto-update-repo-skills/
    └── SKILL.md
```

## Agent tracker

`maugusto-agent-tracker` turns agent state files into a two-screen dashboard system:

- `fleet.html`: overview of all tracked agents, status counts, filters, and progress cards
- `agent-<id>.html`: detail view for one agent, including phases, task ledger, timeline, files changed, and unresolved errors

Agents write JSON files into `~/.agent-tracker/`. The dashboard generator scans that directory and writes HTML into `~/.agent-tracker/output/`.

```bash
python3 maugusto-agent-tracker/scripts/generate_dashboard.py ~/.agent-tracker/<agent-id>.json
open ~/.agent-tracker/output/fleet.html
```

The state schema is documented in `maugusto-agent-tracker/references/state-schema.md`.

## Work review

`maugusto-agent-work-review` is a skeptical code-review skill for agent output. It compares code changes against a driving document and produces a review with:

- requirements coverage
- critical, important, and minor findings
- file and line references
- re-review notes when fixes are submitted

The output format is documented in `maugusto-agent-work-review/references/review-format.md`.

## Sync workflow

The two update skills keep local and repo copies aligned:

- `maugusto-update-local-skills`: install or update repo skills into `~/.agents/skills/`
- `maugusto-update-repo-skills`: copy locally authored skills back into `~/dev/skills/`, then commit and push

Both skills are deliberately manual. They should only run when explicitly requested because they can overwrite skill directories after user approval.

## Installing manually

To install one skill by hand, copy its directory into `~/.agents/skills/`:

```bash
mkdir -p ~/.agents/skills
cp -R maugusto-agent-tracker ~/.agents/skills/
```

To install all skills:

```bash
mkdir -p ~/.agents/skills
for skill in */SKILL.md; do
  cp -R "$(dirname "$skill")" ~/.agents/skills/
done
```

## Development notes

- Keep each skill self-contained. Put reusable scripts under that skill's `scripts/` directory and long references under `references/`.
- Keep `SKILL.md` focused on runtime behavior: when the skill should trigger, what it should inspect, and what it should produce.
- Use `evals/evals.json` to capture trigger and behavior examples.
- The tracker includes Python tests in `maugusto-agent-tracker/tests/test_dashboard.py`, but they currently expect sample data at `~/Downloads/agent-tracker-update/data`.

## License

No license has been declared yet.
