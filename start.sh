#!/usr/bin/env bash
# Spectra — start all services

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Oracle Brain (port 8001)..."
cd "$ROOT/oracle-brain"
MOCK_MODE=false .venv/bin/python run.py &> /tmp/spectra-oracle.log &
echo $! > /tmp/spectra-oracle.pid

echo "Starting Backend (port 8000)..."
cd "$ROOT/backend"
.venv/bin/python run.py &> /tmp/spectra-backend.log &
echo $! > /tmp/spectra-backend.pid

echo "Starting Frontend (port 5173)..."
cd "$ROOT/spectra_frontend"
npm run dev &> /tmp/spectra-frontend.log &
echo $! > /tmp/spectra-frontend.pid

echo ""
echo "All services started."
echo "  Oracle Brain → http://localhost:8001"
echo "  Backend      → http://localhost:8000"
echo "  Frontend     → http://localhost:5173"
echo ""
echo "Logs:"
echo "  tail -f /tmp/spectra-oracle.log"
echo "  tail -f /tmp/spectra-backend.log"
echo "  tail -f /tmp/spectra-frontend.log"
