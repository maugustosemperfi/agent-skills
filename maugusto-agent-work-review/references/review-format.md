# Review Document Format

Use this structure for every review document. The goal is to produce something the implementing agent can work through like a task list — clear, specific, and actionable.

## Template

```markdown
# Code Review: [Short title describing what was reviewed]

**Date**: YYYY-MM-DD
**Driving document**: [path to PRD/ADR/RFC/plan]
**Changes reviewed**: [description of scope — e.g., "uncommitted changes", "commits abc1234..def5678", "last 2 hours of commits"]
**Review iteration**: [N — 1 for first review, 2+ for re-reviews]
**Previous review**: [path to previous review .md, or "N/A"]

## Summary

[2-3 sentences: overall assessment. Is the implementation on track? How close to complete? What's the biggest concern?]

**Status**: [one of]
- ✅ **Complete** — all requirements met, no blocking issues
- 🟡 **Nearly complete** — minor issues remain, almost there
- 🔴 **Incomplete** — significant gaps or issues found
- ⚫ **Not started / wrong direction** — fundamental problems

## Requirements coverage

For each requirement in the driving document, state whether it's been addressed:

| # | Requirement | Status | Notes |
|---|-------------|--------|-------|
| 1 | [requirement text] | ✅ Done / 🟡 Partial / ❌ Missing | [brief note with file:line if applicable] |

## Findings

### Critical (must fix)

Issues that mean the implementation doesn't work, doesn't match the spec in a fundamental way, or introduces serious risk.

#### [C1] [Short title]
- **File**: `path/to/file.ts:42`
- **Requirement**: [which requirement from the driving doc this relates to]
- **Issue**: [what's wrong — be specific, quote the problematic code if helpful]
- **Suggestion**: [what should change, described in words — not code]

### Important (should fix)

Issues that degrade quality, miss edge cases, or partially deviate from the spec but don't completely break things.

#### [I1] [Short title]
- **File**: `path/to/file.ts:87`
- **Requirement**: [which requirement]
- **Issue**: [what's wrong]
- **Suggestion**: [what should change]

### Minor (nice to have)

Style issues, small improvements, nitpicks. Only include these if they're genuinely worth the implementing agent's time.

#### [M1] [Short title]
- **File**: `path/to/file.ts:15`
- **Issue**: [what could be improved]
- **Suggestion**: [how]

## Re-review notes (iteration 2+)

[Only for re-reviews. For each finding from the previous review, state:]

| Previous finding | Status | Notes |
|-----------------|--------|-------|
| [C1] Previous title | ✅ Resolved / 🟡 Partial / ❌ Not resolved | [what changed or didn't] |

### New findings

[Any new issues introduced by the fixes]
```

## Guidelines

- **Severity is about impact on the goal**, not about code style preferences. A missing feature the spec requires is Critical. A suboptimal variable name is Minor (or skip it).
- **One finding per issue.** Don't bundle multiple problems into one finding — it makes tracking resolution harder.
- **Quote the code** when it helps clarify the issue, but keep quotes short (a few lines max).
- **Reference the driving document** by section or requirement number when possible. This helps the implementing agent understand the "why" behind each finding.
- **Be constructive.** The goal is to help the implementing agent succeed, not to punish it. Frame findings as "this needs to change because X" rather than "this is wrong."
