#!/usr/bin/env bash
# ============================================================
# Smart RAG - Automated Local Setup Script
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================================"
echo "🚀 Setting up Smart RAG Search Environment"
echo "============================================================"

# 1. Environment files
if [ ! -f "$ROOT_DIR/.env" ]; then
    echo "Creating root .env from .env.example..."
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

if [ ! -f "$ROOT_DIR/backend/.env" ]; then
    echo "Creating backend/.env from backend/.env.example..."
    cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
fi

if [ ! -f "$ROOT_DIR/frontend/.env.local" ]; then
    echo "Creating frontend/.env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > "$ROOT_DIR/frontend/.env.local"
fi

# 2. Python Virtual Environment
PYTHON_BIN=""
if command -v /opt/homebrew/bin/python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="/opt/homebrew/bin/python3.12"
elif command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3.12)"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
fi

echo "Using Python: $PYTHON_BIN"
if [ ! -d "$ROOT_DIR/backend/.venv" ]; then
    echo "Creating virtualenv in backend/.venv..."
    "$PYTHON_BIN" -m venv "$ROOT_DIR/backend/.venv"
fi

echo "Installing backend dependencies..."
"$ROOT_DIR/backend/.venv/bin/pip" install --upgrade pip -q
"$ROOT_DIR/backend/.venv/bin/pip" install -r "$ROOT_DIR/backend/requirements.txt" -q
"$ROOT_DIR/backend/.venv/bin/pip" install pytest pytest-asyncio -q

# 3. Frontend Dependencies
echo "Checking frontend dependencies..."
cd "$ROOT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "Installing frontend npm packages..."
    npm install
fi

echo "============================================================"
echo "✅ Setup Complete!"
echo ""
echo "Next Steps:"
echo "1. Set GOOGLE_API_KEY in $ROOT_DIR/backend/.env"
echo "2. Start Docker databases: docker compose up -d"
echo "3. Run migrations: cd backend && source .venv/bin/activate && alembic upgrade head"
echo "4. Run backend: ./scripts/start_backend.sh"
echo "5. Run frontend: ./scripts/start_frontend.sh"
echo "============================================================"
