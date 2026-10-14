# Capstone B — Codex development instructions

## Goal
Build and verify a working B component for the capstone: a React + TypeScript HMI frontend and a FastAPI backend that mediates communication with A (data preprocessing / AI predictions and recommendations) and C (Unity digital twin).

## Ground rules
- Work in the currently opened VS Code workspace. Inspect existing files before creating or changing anything. Preserve working code and the project's existing conventions.
- Make actual file changes, not just snippets or descriptions. Use the terminal to install dependencies, run checks, build, and test when permitted.
- Never claim a build, integration, or test passed unless it was actually executed and its result inspected. Report commands and failures accurately.
- Do not assume that A/C API contracts, real datasets, model outputs, or Unity connectivity have been finalized. Record unresolved details in `docs/open-questions.md`; use clearly labeled mock fixtures and adapter interfaces in the meantime.
- Ask before destructive operations, overwriting substantial existing work, changing the architecture in a major way, or requiring secrets/paid services. Do not embed API keys, credentials, or personal data in source code.
- Prefer the smallest functioning vertical slice, then expand iteratively. Avoid adding infrastructure, databases, Docker, authentication, or libraries without a demonstrated need.

## Scope and architecture
- B frontend: React + TypeScript HMI, with readable components, typed API clients, loading/error/empty states, and clear distinction between mock and live data.
- B backend: FastAPI, Pydantic schemas, input validation, documented REST endpoints, CORS configured appropriately for local development, structured error responses, and health check.
- B is the integration hub: A <-> B <-> C. Do not implement A's ML/XAI logic or C's Unity simulation in B; instead define replaceable integration adapters and mock responses.
- Before fixing endpoint names, payload fields, units, directions, or polling/update frequency as contractual facts, confirm them with the user/team. Draft provisional contracts in `docs/api-contract-draft.md` with explicit `DRAFT` labels.
- Keep frontend/backend configurations in environment examples; never commit real secrets.

## Workflow for every task
1. Inspect repository, git status, dependencies, scripts, and existing documentation. Summarize what exists and what is missing.
2. Propose a short, concrete implementation plan and identify any blocking team decisions. For nonblocking unknowns, proceed with documented mock assumptions.
3. Implement one testable increment at a time; keep changes scoped and explain the affected files.
4. Run the appropriate checks (e.g. frontend typecheck/build, backend tests, API smoke test) and fix failures attributable to the change.
5. Report: files changed, features implemented, exact commands executed, verified results, unresolved issues, and the next recommended step.
6. Update `README.md` with Windows-friendly setup/run commands and `docs/progress.md` with completed/pending work.

## Suggested first milestone
Deliver a minimal end-to-end runnable slice:
- FastAPI `/health` endpoint and one explicitly provisional mock-data endpoint.
- React HMI screen that fetches and displays that endpoint, including loading/error states.
- Configured local frontend/backend development startup and README instructions.
- At least one backend test and a successful frontend typecheck/build where the environment permits.
- Draft data contract and a concise list of questions for A/C about data fields, units, ownership, and update timing.

## Communication style
- Explain new concepts (React, TypeScript, FastAPI, REST, JSON, CORS) briefly when first used.
- Distinguish what Codex actually verified from what the user must test manually (especially Unity/A integration).
- Avoid dumping huge code listings in chat when files were already written; link to paths and summarize the important parts.
- Use Korean for explanations, comments when useful, and documentation intended for the student; keep standard programming identifiers in English.
