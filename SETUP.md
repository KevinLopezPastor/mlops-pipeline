# Week 1 Claude Code kit: mentor + reviewer

## What is in here

| File | What it does |
| --- | --- |
| `CLAUDE.md` | Project context and mentor rules; imports the plan and progress log |
| `.claude/output-styles/mentor.md` | "Mentor" style: one step at a time, `TODO(human)` for the code you write, hints before answers |
| `.claude/agents/project-reviewer.md` | Read-only senior reviewer on Opus with project memory, so it tracks its own past findings |
| `.claude/skills/today/` | `/today`: start a session at the right day and step |
| `.claude/skills/checkpoint/` | `/checkpoint`: log the session in PROGRESS.md |
| `.claude/skills/review-week/` | `/review-week [focus]`: run the reviewer and get scores and fixes |
| `.claude/settings.json` | Turns on the Mentor style; safe permissions |
| `docs/plan/week-01.md`, `PROGRESS.md` | The plan from the roadmap doc, and the log the agents read and update |

## Setup (10 minutes)

1. Create the repo: `gh repo create mlops-reproducible-pipeline --public --clone` (or from your template repo).
2. Copy everything in this kit into the repo root, keeping the folders.
3. Open the repo in VS Code with File > Open Folder > `mlops-reproducible-pipeline`
   (or run `code mlops-reproducible-pipeline` in a terminal; `code` is VS Code's command to open a folder).
   Claude Code reads `CLAUDE.md` and `.claude/` from the folder it starts in, so it must be this repo root.
4. Start Claude Code in that folder: click the Claude icon in the VS Code sidebar, or open
   Terminal > New Terminal, check `pwd` ends in `mlops-reproducible-pipeline`, and run `claude`.
   If `claude --version` says "command not found", install it with
   `curl -fsSL https://claude.ai/install.sh | bash` and open a new terminal. The first run asks you to
   log in and to trust the folder; say yes so the kit's settings load.
5. Check it loaded: `/output-style` should show **Mentor** as current; typing `@` should offer
   **project-reviewer (agent)** in the list; typing `/` should show `/today`, `/checkpoint`, `/review-week`.
   (`/agents` no longer lists agents in current Claude Code.) If the reviewer or the commands are missing,
   run `/exit` and start `claude` again from the repo root: a running session does not pick up a
   `.claude/agents/` folder that did not exist when it started.
6. Commit the kit: `git add . && git commit -m "Add Claude Code mentor and reviewer setup"`.

## Daily loop

1. `/today` to start. The mentor reads the plan and progress and gives you today's steps.
2. Work through the steps. Write your parts at each `TODO(human)` and say "done" in the chat.
3. `/checkpoint` at the end. It updates PROGRESS.md and suggests a commit message.

## Reviews

- `/review-week` for a full review (best on Fri after the tasks work, and on Sat before publishing).
- `/review-week tests` or `/review-week reproducibility` to focus it.
- The reviewer keeps notes in `.claude/agent-memory/project-reviewer/`; commit them so the next
  review checks whether earlier findings were fixed.
- Apply the fixes yourself with the mentor, then run the review again until no blockers are left.

## Reusing it next week

Copy the kit into the next repo, replace `docs/plan/week-01.md` with the new week's plan,
update the file names in `CLAUDE.md`, `today`, `checkpoint` and `review-week`, and reset PROGRESS.md.
