#!/usr/bin/env bash
# Spectra — stop all services

kill_port() {
  local pids
  pids=$(lsof -ti :"$1" 2>/dev/null)
  if [ -n "$pids" ]; then
    kill $pids 2>/dev/null && echo "Stopped port $1" || echo "Failed to stop port $1"
  else
    echo "Nothing on port $1"
  fi
}

kill_port 8001
kill_port 8000
kill_port 5173

# Clean up pid files
rm -f /tmp/spectra-oracle.pid /tmp/spectra-backend.pid /tmp/spectra-frontend.pid

echo "Done."
