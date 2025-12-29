# SentinelShare

# SentinelShare

**SentinelShare** is an automated financial guardian for your household. It quietly monitors your email inboxes, intelligently detects receipts (from Amazon, recurring subscriptions, etc.), and forwards them to your partner or accountant.

## 💡 The Problem

Keeping family finances in sync is hard. One person buys something on Amazon, but the receipt gets buried in their personal inbox. The other person (or the accountant) has to chase them down for "that $49.99 charge".

## ✅ The Solution

SentinelShare solves this by:

1.  **Watching**: Connecting securely to your Gmail/iCloud.
2.  **Filtering**: Ignoring spam, shipping updates, and promos.
3.  **Forwarding**: Sending _only_ the actual receipts to a designated email.
4.  **Managing**: Providing a unified dashboard to track what's been shared.

It turns a manual chore into a "set it and forget it" background process.

## 🚀 Features

- **🌙 Dark Mode Support**: Sleek, modern interface with automatic system preference detection and manual override (theme persistence).
- **📧 In-App Email Management**: Add and manage multiple IMAP accounts directly from the dashboard with encrypted credential storage.
- **Intelligent Forwarding**: Forwards detected receipts to a target email address with a rich, summary header.
- **Smart Actions**:
  - **Block**: Stop forwarding specific senders or categories with one click.
  - **Always Forward**: Whitelist senders to ensure they are never missed.
  - **Settings**: Manage preferences directly from the forwarded email or the dashboard.
- **Modern Web Dashboard**:
  - **Activity Feed**: Real-time log of processed emails.
  - **History**: Searchable history of all actions.
  - **Stats**: Visual breakdown of forwarded vs. blocked emails and spending over time.
  - **Settings**: Configure manual rules, manage blocking lists, and edit email templates.
- **Rich Email Templates**: Customizable, beautiful HTML templates for forwarded emails.

## 🛠️ Technology Stack

- **Backend**: Python (FastAPI), SQLModel (SQLite), APScheduler, imaplib.
- **Frontend**: Svelte 5, Tailwind CSS, Vite, Lucide Icons.
- **Deployment**: Ready for Heroku, Docker, or Docker Compose environments (PostgreSQL and SQLite supported).
- **Quality Ensured**: 275+ tests (Pytest, Vitest, Playwright) and robust CI/CD stabilization.

## 📦 Installation & Setup

### 🐳 Docker Quickstart

You can run SentinelShare with a single command using our official Docker image.

```bash
# Pull and run the latest version (GHCR)
# Note: Mount a local data directory to persist receipts and logs
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --name sentinelshare \
  ghcr.io/thef4tdaddy/sentinelshare:latest
```

Or using `docker-compose.yml` (included in repo):

```bash
docker-compose up -d
```

### Quick Start with Docker (Recommended)

The easiest way to get started is with Docker. Choose between SQLite (simpler) or PostgreSQL (production-ready):

**SQLite (Single Container, No Database Setup):**

```bash
git clone https://github.com/f4tdaddy/SentinelShare.git
cd SentinelShare
cp .env.example .env
# Edit .env with your configuration
docker compose -f docker-compose.sqlite.yml up -d
```

**PostgreSQL (Production-Ready):**

```bash
git clone https://github.com/f4tdaddy/SentinelShare.git
cd SentinelShare
cp .env.example .env
# Edit .env with your configuration (including POSTGRES_PASSWORD)
docker compose up -d
```

Visit `http://localhost:8000` and log in with your `DASHBOARD_PASSWORD`.

**👉 See [DOCKER.md](DOCKER.md) for detailed Docker setup instructions.**

### Manual Setup

#### Prerequisites

- Python 3.12+
- Node.js 18+
- IMAP-enabled email accounts (Gmail App Passwords recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/f4tdaddy/SentinelShare.git
cd SentinelShare
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials (see Configuration below)
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Configuration (.env)

Create a `.env` file in the root directory with the following variables:

```ini
# App
SECRET_KEY=your_secret_key_here
APP_URL=http://localhost:5173  # Or your production URL

# Primary Email (Source)
GMAIL_EMAIL=your_email@gmail.com
GMAIL_PASSWORD=your_app_password

# Target Email (Recipient)
WIFE_EMAIL=recipient@example.com
SENDER_EMAIL=your_email@gmail.com  # Account to send FROM
SENDER_PASSWORD=your_app_password

# Optional: Additional Accounts (JSON string)
EMAIL_ACCOUNTS='[{"email": "other@icloud.com", "password": "...", "imap_server": "imap.mail.me.com"}]'
```

### 5. Running the Application

**Backend:**

```bash
# From root directory
python3 run.py
# Or: uvicorn backend.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` (or your configured port) to access the dashboard.

## 📚 Developer Documentation

- **[Project Context & Rules](GEMINI.md)**: Essential guide for AI Agents and Developers, covering architecture, "gotchas", and best practices.
- **[Workflows](WORKFLOWS.md)**: Inventory of CI/CD pipelines and future automation recommendations.
- **[Copilot Agent](.github/agents/SentinelShareCopilotAgent.md)**: Configuration and system prompt for the `SentinelShareCopilotAgent`.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**.

- ✅ **Free for Personal Use**: You can self-host, modify, and use this for your personal needs (e.g., managing your own receipts).
- ❌ **No Commercial Use**: You cannot sell this software, offer it as a service (SaaS), or use it for any commercial benefit without a separate license.

See the [LICENSE](LICENSE) file for details.

---

Copyright (c) 2025 f4tdaddy
