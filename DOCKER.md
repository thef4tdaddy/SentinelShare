# Docker Setup Guide for SentinelShare

This guide will help you run SentinelShare using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)

## Quick Start

1. **Clone the repository** (if you haven't already):
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

| Variable | Description | Required |
|----------|-------------|----------|
| `DASHBOARD_PASSWORD` | Password for web UI access | Yes |
| `SECRET_KEY` | Secret key for session management | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL database password | Yes |
| `GMAIL_EMAIL` | Your Gmail address for IMAP | Yes |
| `GMAIL_PASSWORD` | Gmail app password | Yes |
| `WIFE_EMAIL` | Recipient email address | Yes |
| `SENDER_EMAIL` | Sender email for forwarding | Yes |
| `SENDER_PASSWORD` | Sender email password | Yes |
| `POLL_INTERVAL` | Email check interval in seconds (default: 60) | No |

### Data Persistence

Docker Compose creates two persistent volumes:

- `postgres_data`: PostgreSQL database files
- `./data`: Application data (receipts, logs)

Your data will persist across container restarts.

## Common Commands

### View logs
```bash
docker-compose logs -f app
```

### Stop the application
```bash
docker-compose down
```

### Stop and remove all data
```bash
docker-compose down -v
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Access the database
```bash
docker-compose exec db psql -U sentinelshare -d sentinelshare
```

### Run migrations manually
```bash
docker-compose exec app alembic upgrade head
```

## Troubleshooting

### Application won't start
1. Check logs: `docker-compose logs app`
2. Verify `.env` file has all required variables
3. Ensure port 8000 is not already in use

### Database connection issues
1. Check database health: `docker-compose ps`
2. Wait for database to be ready (can take 10-30 seconds on first start)
3. Check logs: `docker-compose logs db`

### Permission issues
If you encounter permission issues with the `data/` directory:
```bash
sudo chown -R $USER:$USER ./data
```

## Using SQLite Instead of PostgreSQL

If you prefer to use SQLite instead of PostgreSQL:

1. Remove the `DATABASE_URL` from your `.env` file (or comment it out)
2. Modify `docker-compose.yml` to remove the `db` service dependency
3. The application will automatically use SQLite with the database file at `/app/local_dev.db`

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
