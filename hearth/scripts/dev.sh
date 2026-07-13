#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "Starting Hearth in development mode..."
cd static/frontend
npm run dev &
REACT_PID=$!
cd ..
uvicorn app.main:app --reload --port 8765
kill $REACT_PID 2>/dev/null || true
