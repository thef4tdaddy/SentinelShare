# Deployment Guide (Heroku)

This project is configured for deployment on Heroku using Python (Backend) and Node.js (Frontend Build).

## Prerequisites
- Heroku CLI installed and logged in (`heroku login`).
- Git repository initialized.

## Step 1: Create App & Add-ons
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
```

## Step 2: Configure Buildpacks
Order matters! Python must run, and we use Node to build the frontend.
```bash
heroku buildpacks:add heroku/nodejs
heroku buildpacks:add heroku/python
```

## Step 3: Set Environment Variables
Set the following variables using `heroku config:set KEY=VALUE`:

### Email Settings
- `GMAIL_EMAIL`: Your full Gmail address.
- `GMAIL_PASSWORD`: Your Gmail App Password (NOT your regular password).
- `WIFE_EMAIL`: The recipient email address.
- `SENDER_EMAIL`: Email to send FROM (usually same as GMAIL_EMAIL).
- `SENDER_PASSWORD`: Password for SENDER_EMAIL (usually same as GMAIL_PASSWORD).

### App Settings
- `POLL_INTERVAL`: Minutes between checks (e.g. `60`).
- `SECRET_KEY`: A random string for security (optional but recommended).

## Step 4: Deploy
```bash
git add .
git commit -m "Ready for deploy"
git push heroku main
```

## Step 5: Verify
- Open the app: `heroku open`
- Check logs: `heroku logs --tail`
