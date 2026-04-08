#!/bin/bash
# Start Timeline locally (without Docker)
# Usage: ./start.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Find Node
if [ -d "$HOME/.nvm" ]; then
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1091
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" --no-use
  # Use latest installed node
  NODE_PATH=$(ls -d "$NVM_DIR/versions/node"/*/bin 2>/dev/null | sort -V | tail -1)
  export PATH="$NODE_PATH:$PATH"
fi

# Find Python
PYTHON=""
for p in python3.13 python3.12 python3.11 python3; do
  if command -v "$p" &>/dev/null; then
    PYTHON="$p"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "Error: Python 3.11+ required"
  exit 1
fi

echo "▶ Starting Timeline"
echo "  Python: $($PYTHON --version)"
echo "  Node:   $(node --version 2>/dev/null || echo 'not found')"
echo ""

# Backend
cd "$SCRIPT_DIR/backend"
if [ ! -d ".venv" ]; then
  echo "Creating Python venv..."
  "$PYTHON" -m venv .venv
  .venv/bin/pip install -q fastapi "uvicorn[standard]" sqlalchemy alembic pydantic "pydantic-settings" \
    python-multipart httpx pillow piexif icalendar numpy aiofiles python-dateutil chardet
fi

echo "▶ Backend  → http://localhost:8000"
PYTHONPATH=src .venv/bin/uvicorn timeline.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Frontend
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install --silent
fi

echo "▶ Frontend → http://localhost:5173"
npm run dev -- --open &
FRONTEND_PID=$!

echo ""
echo "Timeline running!"
echo "  App:    http://localhost:5173"
echo "  API:    http://localhost:8000/api/v1"
echo "  Docs:   http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

# Cleanup on exit
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT TERM

wait
