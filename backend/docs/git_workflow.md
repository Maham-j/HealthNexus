# Git Workflow

This project used an issue → branch → PR workflow during active development.
Now that development is complete, changes (docs, polish) go straight to
`main`.

## During Active Development

1. **Create an issue** describing the task (e.g. "Implement fetchSimilarQueries
   tool", "Migrate to LangChain agent"). Each issue represents one meaningful
   unit of work.
2. **Create a branch** from that issue, named after the feature/fix.
3. **Do the work on that branch**, committing in logical chunks as features
   are completed — not one giant commit at the end.
4. **Open a PR** back into `main` once the feature is working and tested.
5. **Address review feedback** on the PR (see commit history for examples —
   e.g. model selection from OpenWebUI, chain-of-thought markdown
   formatting — both were fixed in response to PR review comments).
6. **Merge** once approved.

## Commit Message Convention

Following [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — a new feature or capability
- `fix:` — a bug fix
- `docs:` — documentation-only changes (README, migration docs, etc.)
- `chore:` — maintenance tasks (removing dead code, adding `.gitignore`
  entries, folder restructuring)

Examples from this project:
```
feat: implement FAISS-based RAG tool for similar query retrieval
feat: migrate chat pipeline to LangChain agent
feat: allow OpenWebUI model selection to control which Groq model runs
feat: format tool calls in chain-of-thought as markdown per review
docs: add project README with architecture, features, and setup guide
docs: add executed PrimeKG EDA notebook with query outputs
chore: remove unused stub files from initial project scaffold
chore: ignore Jupyter checkpoint files
```

## Post-Development (Current State)

The project is now feature-complete. For any further changes (documentation
updates, small polish, README edits), commit directly to `main` — the
issue → branch → PR ceremony is reserved for active collaborative
development with review cycles, not needed for a finished project.

## What Belongs in `.gitignore`

- `venv/`, `.venv/` — Python virtual environments
- `.env` — secrets (Neo4j credentials, Groq API key) — never commit this
- `.ipynb_checkpoints/` — Jupyter's auto-generated backup folder
- `__pycache__/`, `*.pyc` — Python bytecode
