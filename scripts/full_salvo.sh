#!/bin/bash
# SentinelShare Full Salvo Verification Script
# This script runs formatting, linting, type-checking, and tests for both backend and frontend.
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}        SentinelShare Full Salvo Verification       ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: ./venv directory not found. Please create it first.${NC}"
    exit 1
fi

# --- Environment Setup ---
export DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD:-testpass}
# Generate a temporary SECRET_KEY if not set (for E2E tests)
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(./venv/bin/python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
fi
# Ensure PYTHONPATH includes project root for backend imports
export PYTHONPATH=$PYTHONPATH:$(pwd)

# --- Backend ---
echo -e "\n${YELLOW}[1/8] Backend: Formatting with Black...${NC}"
./venv/bin/python3 -m black backend

echo -e "\n${YELLOW}[2/8] Backend: Linting with Ruff...${NC}"
./venv/bin/python3 -m ruff check backend --fix

echo -e "\n${YELLOW}[3/8] Backend: Type Checking with Mypy...${NC}"
./venv/bin/python3 -m mypy backend --ignore-missing-imports

echo -e "\n${YELLOW}[4/8] Backend: Running Tests with Pytest...${NC}"
./venv/bin/pytest

# --- Frontend ---
echo -e "\n${YELLOW}[5/8] Frontend: Formatting with Prettier...${NC}"
cd frontend
# Try to run format script, fallback to npx if not defined
npm run format 2>/dev/null || npx prettier --write "src/**/*.{ts,js,svelte,css}"

echo -e "\n${YELLOW}[6/8] Frontend: Linting with ESLint...${NC}"
npm run lint

echo -e "\n${YELLOW}[7/8] Frontend: Svelte Check (TypeScript & Components)...${NC}"
npm run check

echo -e "\n${YELLOW}[8/8] Frontend: Running Vitest...${NC}"
npm run test:run

echo -e "\n${YELLOW}[9/9] Frontend: Running Playwright E2E...${NC}"

# Start Backend Server for E2E
cd .. # Go back to root

echo -e "${BLUE}Cleaning up old Backend processes...${NC}"
pkill -f uvicorn || true

echo -e "${BLUE}Starting Backend Server for E2E...${NC}"
# Use a unique port or default 8000? Frontend config expects 8000 usually.
# Use nohup
nohup ./venv/bin/python3 -u -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > salvo_backend.log 2>&1 &
BACKEND_PID=$!

# Ensure we kill the backend on exit
cleanup() {
    echo -e "\n${BLUE}Stopping Backend Server (PID $BACKEND_PID)...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
}
trap cleanup EXIT

# Wait for server to start (Max 30s)
echo -e "${BLUE}Waiting for Backend to maximize readiness (polling /api/health)...${NC}"
SERVER_READY=0
for i in {1..30}; do
    if curl -s http://0.0.0.0:8000/api/health > /dev/null; then
        echo -e "${GREEN}Backend is ready!${NC}"
        SERVER_READY=1
        break
    fi
    echo -n "."
    sleep 1
done

if [ $SERVER_READY -eq 0 ]; then
    echo -e "\n${RED}Backend failed to start after 30s. Log output:${NC}"
    cat salvo_backend.log
    kill $BACKEND_PID
    exit 1
fi

cd frontend
npx playwright test

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}      PASSED: Full Salvo Verification Complete      ${NC}"
echo -e "${GREEN}====================================================${NC}"
