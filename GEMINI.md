# SentinelShare Agent Context (GEMINI.md)

This document provides context, guidelines, and "gotchas" for AI agents (and humans) working on SentinelShare.

## 🏗 Project Structure

- **Backend**: Python 3.12+ / FastAPI / SQLModel.
  - Located in `backend/`.
  - **Virtual Environment**: strictly use `venv` (not `.venv`).
  - **Activation**: `source venv/bin/activate`.
  - **Testing**: `pytest` (configuration in root `pytest.ini` or `backend/pytest.ini`).
- **Frontend**: Node.js v22+ / Svelte 5 / Vite / TailwindCSS v4.
  - Located in `frontend/`.
  - **Package Manager**: `npm`.
  - **Testing**: `vitest`.

## 🔄 CI/CD Workflows (`.github/workflows`)

### Critical Workflows

- **`ci.yml`**: Runs on Pull Requests and pushes to `main`/`develop`.
  - **Checks**: Frontend (Lint, Typecheck, Build), Backend (Ruff, Mypy, Pytest).
  - **Note**: Ensure `pytest` failures are not swallowed by `|| true`.
- **`daily-health-check.yml`**: Runs daily to verify system health.
  - **Note**: Uses `github-script` to generate reports. **Step outcomes must be passed via `env` vars**, not accessed via `context.steps`.

### Utility Workflows

- **`auto-approve-copilot-workflows.yml`**: Auto-approves CI for Copilot PRs.
- **`auto-format-pr-title.yml`**: Enforces/fixes conventional commit titles.
- **`issue-labeler.yml`** & **`pr-labeler.yml`**: Auto-triage and labeling.
- **`release-please.yml`**: Automates versioning and changelogs.

## ⚠️ Known Gotchas & Patterns

1.  **GitHub Script Context**:
    - In `actions/github-script`, the `steps` context is **NOT** available in `context.steps` or `steps` global object.
    - **Fix**: Map step outputs/outcomes to environment variables and access via `process.env`.

    ```yaml
    - uses: actions/github-script@v7
      env:
        OUTCOME: ${{ steps.step_id.outcome }}
      with:
        script: console.log(process.env.OUTCOME)
    ```

2.  **Environment Consistency**:
    - CI runs on Ubuntu (Python 3.11/Node 22 usually).
    - Local dev is often Mac (Python 3.12/Node 25).
    - Be aware of version-specific issues (e.g., `mypy` differences).

3.  **Database**:
    - Backend tests often require a DB. `conftest.py` should handle setup.
    - `alembic` is used for migrations.

## 📝 Development Commands

### Backend

```bash
cd backend
source ../venv/bin/activate
pip install -r ../requirements.txt
pytest
ruff check .
mypy .
```

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run check
npm run test
```

## 🤖 Workflows

For a detailed inventory of CI/CD workflows and future recommendations, see [WORKFLOWS.md](./WORKFLOWS.md).
