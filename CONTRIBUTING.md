# Contributing

Thank you for considering a contribution to MultiModal FinRAG Prod.

## Development Principles

- Keep retrieval, routing, and generation behavior explicit and testable.
- Do not change model-routing logic or retrieval algorithms without documenting the reason.
- Avoid committing runtime artifacts, local databases, uploaded documents, vector stores, or secrets.
- Prefer small pull requests with a clear motivation.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill in the required API keys in `.env`, then run:

```bash
uvicorn api.main:app --reload
python -m ui.app
```

## Pull Request Checklist

- The change is scoped and described clearly.
- Documentation has been updated when behavior changes.
- No API keys, credentials, local paths, databases, or vector-store files are committed.
- New examples use placeholders instead of private data.
- Any new dependency is justified in the pull request.
