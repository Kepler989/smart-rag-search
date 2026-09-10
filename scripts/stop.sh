#!/usr/bin/env bash
# ============================================================
# Smart RAG - Graceful Shutdown Script
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🛑 Stopping Smart RAG Search System..."

# 1. Stop backend processes if running
echo "1. Stopping any running backend (uvicorn) processes..."
pkill -f "uvicorn app.main:app" || true

# 2. Stop frontend processes if running
echo "2. Stopping any running frontend (next dev) processes..."
pkill -f "next dev" || true

# 3. Stop Docker containers
echo "3. Stopping Docker services..."
cd "$ROOT_DIR"
docker compose down

echo "============================================================"
echo "✅ All Smart RAG services have been stopped safely."
echo "Your data in PostgreSQL and Redis volumes is preserved."
echo "To restart later: docker compose up -d && ./scripts/start_backend.sh"
echo "============================================================"
