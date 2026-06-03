# Vartovii Agent Instructions

These instructions are the canonical project rules for coding agents working in
this repository.

## Communication

- Communicate with the user in Ukrainian unless they explicitly ask otherwise.
- Keep code, comments, documentation, and commit messages in English.
- Be concise in user-facing updates and include concrete verification results.

## Safety

- Never expose, print, commit, copy, or propagate secrets from `.env`, shell
  environment variables, Secret Manager, cloud tools, or local config.
- Never include raw credentials, API keys, MongoDB connection strings, tokens, or
  service account material in logs, documentation, screenshots, or examples.
- Treat `.env.example` as the only environment file that may be committed.

## Engineering Workflow

- Prefer small, reversible changes with local verification before proposing the
  next step.
- Read the local code before editing. Follow existing module boundaries and
  naming patterns.
- Use `rg` or `rg --files` for repository search.
- Use `apply_patch` for manual file edits.
- Do not revert user changes unless the user explicitly asks for that exact
  action.
- Keep production-facing changes deployable through `scripts/deploy.sh`.

## Verification

Run the narrowest reliable checks after meaningful changes:

- `./.venv/bin/python -m pytest tests -q`
- `bash -n scripts/deploy.sh`
- `git diff --check`

For production deploy changes, also verify:

- `/api/health`
- `/api/readiness`
- one `/api/chat` smoke request
- live UI smoke for data source, key counts, and horizontal overflow

## Project Priorities

Vartovii is a hackathon product, but the codebase should read as a production
system:

- Clear multi-agent ownership.
- Auditable evidence and source freshness.
- Safe model routing with fallbacks.
- MongoDB Atlas and MCP integration that is explicit and testable.
- A demo surface that communicates trust, not generic chatbot behavior.
