# Docker Setup Guide for SentinelShare

This guide will help you run SentinelShare using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)

## Quick Start

Choose between SQLite (simpler, single container) or PostgreSQL (production-ready):

### Option 1: SQLite (Recommended for Getting Started)

Perfect for testing and personal use. No database setup required!

1. **Clone the repository**:
   ```bash
   git clone https://github.com/f4tdaddy/SentinelShare.git
   cd SentinelShare
   ```

2. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit the `.env` file** with your configuration:
   - Set `DASHBOARD_PASSWORD` for web UI access
   - Set `SECRET_KEY` to a random secure string
   - Configure your email credentials (GMAIL_EMAIL, GMAIL_PASSWORD, etc.)
   - **Note**: You don't need `POSTGRES_PASSWORD` for SQLite

4. **Start the application**:
   ```bash
   docker compose -f docker-compose.sqlite.yml up -d
   ```

5. **Access the application**:
   - Open your browser to `http://localhost:8000`
   - Log in with the password you set in `DASHBOARD_PASSWORD`

### Option 2: PostgreSQL (Recommended for Production)

More robust for production environments with multiple users or high volume.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/f4tdaddy/SentinelShare.git
   cd SentinelShare
   ```

2. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit the `.env` file** with your configuration:
   - Set `DASHBOARD_PASSWORD` for web UI access
   - Set `SECRET_KEY` to a random secure string
   - Set `POSTGRES_PASSWORD` for database security
   - Configure your email credentials (GMAIL_EMAIL, GMAIL_PASSWORD, etc.)

4. **Start the application**:
   ```bash
   docker compose up -d
   ```

5. **Access the application**:
   - Open your browser to `http://localhost:8000`
   - Log in with the password you set in `DASHBOARD_PASSWORD`

## Configuration

### Environment Variables

All configuration is done through environment variables in the `.env` file:

#### Required for Both SQLite and PostgreSQL

| Variable | Description | Required |
|----------|-------------|----------|
| `DASHBOARD_PASSWORD` | Password for web UI access | Yes |
| `SECRET_KEY` | Secret key for session management | Yes |
| `GMAIL_EMAIL` | Your Gmail address for IMAP | Yes |
| `GMAIL_PASSWORD` | Gmail app password | Yes |
| `WIFE_EMAIL` | Recipient email address | Yes |
| `SENDER_EMAIL` | Sender email for forwarding | Yes |
| `SENDER_PASSWORD` | Sender email password | Yes |
| `POLL_INTERVAL` | Email check interval in seconds (default: 60) | No |

#### Required Only for PostgreSQL

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_PASSWORD` | PostgreSQL database password | Yes (PostgreSQL only) |

### Data Persistence

**SQLite setup:**
- `./data`: Contains SQLite database file (`local_dev.db`) and application data (receipts, logs)

**PostgreSQL setup:**
- `postgres_data`: PostgreSQL database files (Docker volume)
- `./data`: Application data (receipts, logs)

Your data will persist across container restarts.

## Common Commands

### SQLite Commands

#### View logs
```bash
docker compose -f docker-compose.sqlite.yml logs -f app
```

#### Stop the application
```bash
docker compose -f docker-compose.sqlite.yml down
```

#### Rebuild after code changes
```bash
docker compose -f docker-compose.sqlite.yml up -d --build
```

#### Run migrations manually
```bash
docker compose -f docker-compose.sqlite.yml exec app alembic upgrade head
```

### PostgreSQL Commands

#### View logs
```bash
docker compose logs -f app
```

#### Stop the application
```bash
docker compose down
```

#### Stop and remove all data
```bash
docker compose down -v
```

#### Rebuild after code changes
```bash
docker compose up -d --build
```

#### Access the database
```bash
docker compose exec db psql -U sentinelshare -d sentinelshare
```

#### Run migrations manually
```bash
docker compose exec app alembic upgrade head
```

## Troubleshooting

### Application won't start
1. Check logs: `docker compose logs app` (or `docker compose -f docker-compose.sqlite.yml logs app` for SQLite)
2. Verify `.env` file has all required variables
3. Ensure port 8000 is not already in use

### Database connection issues (PostgreSQL only)
1. Check database health: `docker compose ps`
2. Wait for database to be ready (can take 10-30 seconds on first start)
3. Check logs: `docker compose logs db`

### Permission issues
If you encounter permission issues with the `data/` directory:
```bash
sudo chown -R $USER:$USER ./data
```

## Switching Between SQLite and PostgreSQL

### From SQLite to PostgreSQL

1. Stop the SQLite container:
   ```bash
   docker compose -f docker-compose.sqlite.yml down
   ```

2. Add `POSTGRES_PASSWORD` to your `.env` file

3. Start with PostgreSQL:
   ```bash
   docker compose up -d
   ```

Note: Your existing data won't be automatically migrated. You'll start with a fresh database.

### From PostgreSQL to SQLite

1. Stop the PostgreSQL containers:
   ```bash
   docker compose down
   ```

2. Start with SQLite:
   ```bash
   docker compose -f docker-compose.sqlite.yml up -d
   ```

Note: Your existing data won't be automatically migrated. You'll start with a fresh database.

## Production Deployment

For production deployments:

1. Use strong passwords for `DASHBOARD_PASSWORD`, `SECRET_KEY`, and `POSTGRES_PASSWORD`
2. Consider using Docker secrets instead of environment variables
3. Set up a reverse proxy (like Nginx) with SSL/TLS
4. Configure regular backups of the `postgres_data` volume
5. Monitor logs and set up alerts

## Building the Image Separately

If you want to build the Docker image without using Docker Compose:

```bash
docker build -t sentinelshare:latest .
```

Then run it:
```bash
docker run -d \
  --name sentinelshare \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  sentinelshare:latest
```

Note: This method doesn't include PostgreSQL. You'll need to provide your own database or use SQLite.
