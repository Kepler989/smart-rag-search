#!/usr/bin/env bash
# ============================================================
# Smart RAG - Start Backend API
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting FastAPI Backend at http://localhost:8000..."
cd "$ROOT_DIR/backend"
source .venv/bin/activate
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
