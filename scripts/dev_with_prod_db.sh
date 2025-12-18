#!/bin/bash

# WARNING
echo "================================================================"
echo "WARNING: You are about to connect your LOCAL development environment"
echo "to a REMOTE (possibly PRODUCTION) database."
echo "Any changes you make, including migrations or data mutations,"
echo "will affect the REAL database."
echo "================================================================"
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "Error: Heroku CLI is not installed or not in your PATH."
    exit 1
fi

# Try to detect app name from git remote
APP_NAME=$(git remote get-url heroku 2>/dev/null | sed -E 's/.*heroku.com\/(.*)\.git/\1/')

if [ -z "$APP_NAME" ]; then
    echo "Could not auto-detect Heroku app name from git remote."
    echo "Please enter the Heroku app name:"
    read -r APP_NAME
else
    echo "Detected Heroku app: $APP_NAME"
    echo "Press Enter to use this app, or type a different name:"
    read -r USER_APP_NAME
    if [ -n "$USER_APP_NAME" ]; then
        APP_NAME="$USER_APP_NAME"
    fi
fi

if [ -z "$APP_NAME" ]; then
    echo "Error: No App Name provided. Exiting."
    exit 1
fi

echo "Fetching DATABASE_URL from Heroku for app '$APP_NAME'..."
PROD_DB_URL=$(heroku config:get DATABASE_URL -a "$APP_NAME")

if [ -z "$PROD_DB_URL" ]; then
    echo "Error: Could not retrieve DATABASE_URL. Make sure you are logged in (heroku login) and the app exists."
    exit 1
fi

# Load local .env for other secrets (like DASHBOARD_PASSWORD) if it exists
if [ -f .env ]; then
    echo "Loading local .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Export user input as the environment variable (OVERRIDING .env if it was set there)
export DATABASE_URL="$PROD_DB_URL"

echo ""
echo "Starting backend and frontend..."
echo "To stop, press Ctrl+C."
echo ""

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill "$BACKEND_PID" 2>/dev/null
    kill "$FRONTEND_PID" 2>/dev/null
    exit
}

trap cleanup SIGINT

# Start Backend
uvicorn backend.main:app --reload &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID)"

# Start Frontend
(cd frontend && npm run dev) &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID)"

# Wait for both
wait
