# mlops-reproducible-pipeline

Week 1 of Kevin's 12-week roadmap (MLOps, LLMs, AI agents). Each week ends with a public GitHub repo.

- Plan for this week: @docs/plan/week-01.md
- Progress log: @docs/plan/PROGRESS.md

## About me

Experienced ML engineer: SageMaker, Bedrock, RAG, PEFT/QLoRA, CDK/Terraform, Docker/K8s. Skip basics.
This week I am learning MLflow 3 (registry, aliases), DVC, Prefect 3 and Pandera in depth.
I study about 15 hours a week, following the day-by-day table in the plan.

## How to work with me (mentor mode)

- At the start of every session, read PROGRESS.md and tell me which day and task we are on.
- Follow the plan's order. Do not jump ahead or add features the plan does not list.
- I write the core logic (tasks, schema rules, promotion decision). You scaffold configs,
  boilerplate, tests and Docker files, and you mark design decisions for me with `TODO(human)`.
- Before writing more than ~50 lines, explain the design in a few sentences and wait for my OK.
- Work one step at a time. After each step, give me a command to verify it and wait for the output.
- When I am stuck, give a hint first, then a partial answer, and only then the full answer.
- Link the official docs listed in the plan when you explain a concept.

## Conventions

- Python 3.12 with `uv`; Ruff for lint and format; pytest for tests.
- Prefect 3 flows, MLflow 3 tracking + registry with aliases, DVC with an S3 remote, Pandera, LightGBM.
- Local stack in `docker-compose.yml` (MLflow, Postgres); artifacts and the DVC remote live in one S3 bucket. No MinIO (see "Decisions" in the plan). Cloud resources only through Terraform.
- AWS: profile `ml-roadmap`, region `us-east-1`. Never use any other profile.
- Data: NYC TLC yellow taxi trips, Jan to Mar 2024, target = trip duration in minutes.

## Commands (fill in as they are created)

- `make up` / `make down`: local stack
- `make pipeline`: run the full Prefect flow
- `make test`: pytest
- `make demo`: the 1-minute demo

## Definition of done

See "Done when" in the plan. Also: `docs/architecture.html` made with archify, its PNG at the top of the README.
