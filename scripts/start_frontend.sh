#!/usr/bin/env bash
# ============================================================
# Smart RAG - Start Frontend Dev Server
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "✨ Starting Next.js Frontend at http://localhost:3000..."
cd "$ROOT_DIR/frontend"
exec npm run dev
