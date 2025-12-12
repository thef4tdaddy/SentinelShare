# Product Roadmap

## 🏁 Pre-1.0: Stability & Polish

_Goal: Ensure the system is robust, upgradeable, and professional before the first major public release._

- [x] **Database Migrations (Alembic)**
  - _Why:_ Currently, the database is created on startup. If we change the schema in v1.1, existing users will break. Alembic allows safe schema upgrades.
- [x] **UI Version Display**
  - _Why:_ Users need to know which version they are running for debugging. Add `v1.0.0` to the footer/sidebar.
- [x] **GitHub Templates**
  - _Why:_ Standardize bug reports and PRs with `.github/PULL_REQUEST_TEMPLATE.md` and `ISSUE_TEMPLATE`.

## 🚀 Post-1.0: Intelligence & Integrations

_Goal: Move from "Smart Regex" to "True AI" and expand ecosystem._

- [ ] **LLM-Powered Parsing (Local AI)**
  - _Why:_ Regex is brittle. Integrate Ollama/OpenAI to extract `Date`, `Total`, and `Vendor` with near-100% accuracy, even for unknown formats.
- [ ] **Budgeting Integrations**
  - _Why:_ Push extracted data directly to **YNAB**, **Google Sheets**, or **Actual Budget**.
- [x] **Single-User Authentication**
  - _Why:_ Protect the dashboard. Create a default admin user on install (env vars) so the instance is secure by default.
- [ ] **Multi-User Support**
  - _Why:_ Allow multiple family members to have separate "accounts" or forwarding rules within a single instance.
- [ ] **Sendee Preferences Dashboard**
  - _Why:_ A dedicated view to see all preferences (Allow/Block) set by the recipient via email buttons. Gives visibility into what rules are active.
- [ ] **Telegram/Pushover Notifications**
  - _Why:_ Some users prefer instant chat notifications over forwarded emails.
