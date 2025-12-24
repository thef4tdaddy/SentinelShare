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

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}      PASSED: Full Salvo Verification Complete      ${NC}"
echo -e "${GREEN}====================================================${NC}"
