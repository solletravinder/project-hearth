#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "Building React frontend..."
cd static/frontend
npm run build
cd ../..
echo "Starting Hearth server..."
uvicorn app.main:app --reload --port 8765
