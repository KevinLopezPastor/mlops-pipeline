---
name: review-week
description: Run the project-reviewer agent on the repo and return its assessment
disable-model-invocation: true
context: fork
agent: project-reviewer
background: false
---

Review this repository against docs/plan/week-01.md and docs/plan/PROGRESS.md.
Check your memory for earlier reviews first and report which earlier findings are fixed.

Focus requested by Kevin (may be empty, meaning a full review): $ARGUMENTS
