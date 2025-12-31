# SentinelShare Workflows

This document maintains an inventory of active GitHub Actions workflows and a wish-list for future automation enhancements.

## 🤖 Active Workflow Inventory

| Workflow                 | Trigger         | Purpose                                                                                                      |
| :----------------------- | :-------------- | :----------------------------------------------------------------------------------------------------------- | --- |
| **CI** (`ci.yml`)        | Push/PR         | Runs Frontend (Lint, Typecheck, Build) and Backend (Ruff, Mypy, Pytest) validation.                          |
| **Daily Health Check**   | Schedule/Manual | Runs full test-suite daily to detect regressions in `develop` not caught by PRs (e.g., date-dependent bugs). |
| **Release Please**       | Main Push       | Automates changelog generation and version tagging based on conventional commits.                            |
| **Issue/PR Labeler**     | Issues/PRs      | Auto-labels based on keywords, file paths, and semantic commit types.                                        |
| **Dependabot Triage**    | PR              | Auto-prioritizes Dependabot PRs based on update severity (Major/Minor/Patch).                                |
| **Auto-Format Title**    | PR              | Ensures PR titles follow Conventional Commits standard to support Release Please.                            |
| **Auto-Approve Copilot** | PR              | Automatically approves low-risk workflow runs triggered by Copilot agents.                                   |
| **Stale Issues**         | Schedule        | Automatically closes issues/PRs that have had no activity for 60+ days.                                      |
| **Dependency Review**    | PR              | Scans PR dependency changes for vulnerabilities before they merge.                                           |
| **CodeQL Analysis**      | Schedule/PR     | Deep semantic code analysis (Managed via GitHub Default Setup).                                              |     |
| **Spell Check**          | PR              | Catches typos in documentation and code comments.                                                            |
| **Bundle Size**          | PR              | Monitors frontend bundle size (Limit: 300kB JS, 100ms load).                                                 |
| **Lighthouse CI**        | PR              | Audits Frontend Performance, Accessibility, and SEO (PWA disabled).                                          |
| **Playwright Tests**     | PR              | Runs End-to-End (E2E) browser tests against the Svelte application.                                          |

## 💡 Recommended Workflows (Future)

Consider adding these to enhance automation:

_(Currently all recommended workflows have been implemented. Add new ideas here as they arise.)_
