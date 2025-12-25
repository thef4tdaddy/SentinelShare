# SentinelShare Workflows

This document maintains an inventory of active GitHub Actions workflows and a wish-list for future automation enhancements.

## 🤖 Active Workflow Inventory

| Workflow                 | Trigger         | Purpose                                                                                                      |
| :----------------------- | :-------------- | :----------------------------------------------------------------------------------------------------------- |
| **CI** (`ci.yml`)        | Push/PR         | Runs Frontend (Lint, Typecheck, Build) and Backend (Ruff, Mypy, Pytest) validation.                          |
| **Daily Health Check**   | Schedule/Manual | Runs full test-suite daily to detect regressions in `develop` not caught by PRs (e.g., date-dependent bugs). |
| **Release Please**       | Main Push       | Automates changelog generation and version tagging based on conventional commits.                            |
| **Issue/PR Labeler**     | Issues/PRs      | Auto-labels based on keywords, file paths, and semantic commit types.                                        |
| **Dependabot Triage**    | PR              | Auto-prioritizes Dependabot PRs based on update severity (Major/Minor/Patch).                                |
| **Auto-Format Title**    | PR              | Ensures PR titles follow Conventional Commits standard to support Release Please.                            |
| **Auto-Approve Copilot** | PR              | Automatically approves low-risk workflow runs triggered by Copilot agents.                                   |

## 💡 Recommended Workflows (Future)

Consider adding these to enhance automation:

### Maintenance & Security

1.  **Stale Issues (`stale.yml`)**:
    - Automatically close issues/PRs that have had no activity for 60+ days to keep the backlog clean.
    - _Action_: `actions/stale`.

2.  **Dependency Review (`dependency-review.yml`)**:
    - Scans PR dependency changes for vulnerabilities before they merge.
    - _Action_: `actions/dependency-review-action`.

3.  **CodeQL Analysis (`codeql.yml`)**:
    - Deep semantic code analysis to find security vulnerabilities (SQL injection, XSS) that linters miss.
    - _Action_: `github/codeql-action`.

### Quality Assurance

4.  **Spell Check (`spell-check.yml`)**:
    - Catches typos in documentation and code comments to maintain professional quality.
    - _Action_: `check-spelling/check-spelling`.

5.  **Bundle Size (`size-limit.yml`)**:
    - Monitors frontend bundle size to prevent performance regressions.
    - _Action_: `andresz1/size-limit-action`.

6.  **Lighthouse CI (`lighthouse.yml`)**:
    - Automatically check Svelte app's Performance, Accessibility, and SEO on every PR.
    - _Action_: `treosh/lighthouse-ci-action`.

7.  **End-to-End Testing (`playwright.yml`)**:
    - Run real browser tests against the Svelte application to verify critical flows (Login, Dashboard).
    - _Action_: `playwright-community/playwright-github-action`.
