# SPECTRA — Component D Backend

> FastAPI server that orchestrates all SPECTRA components, manages game state, processes emotions, and stores the timeline in Redis.

## Architecture

```
Component A (Tavus CVI)  ──WebSocket──►  Component D (this)  ──HTTP──►  Component B (Claude)
                                              │
                                              ├──WebSocket──►  Component C (React + CopilotKit)
                                              │
                                              └──Redis──►  Emotion Timeline
```

## Quick Start

### 1. Prerequisites

- **Python 3.11+**
- **Redis** (optional — falls back to in-memory storage)

Start Redis via Docker (optional):
```bash
docker run -d -p 6379:6379 redis:alpine
```

### 2. Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy env file (MOCK_MODE=true by default for local dev)
cp .env.example .env
```

### 3. Run

```bash
python run.py
```

Server starts at `http://localhost:8000`.

### 4. Verify

```bash
# Health check
curl http://localhost:8000/health

# Create a session
curl -X POST http://localhost:8000/api/session/create

# Get session state
curl http://localhost:8000/api/session/{session_id}/state

# Start the timer
curl -X POST http://localhost:8000/api/session/{session_id}/start

# Get timeline (for debrief)
curl http://localhost:8000/api/timeline/{session_id}
```

### 5. Test WebSocket

Use `websocat` or any WebSocket client:
```bash
websocat ws://localhost:8000/ws/session/{session_id}
```

Send emotion data:
```json
{"type": "emotion_data", "data": {"timestamp": 1740153600000, "emotions": {"stress": 0.72, "focus": 0.15, "confusion": 0.58, "confidence": 0.10, "neutral": 0.05}, "dominant": "stress", "face_detected": true}}
```

Send player speech:
```json
{"type": "player_speech", "text": "I think node A looks weakest"}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `COMPONENT_B_URL` | `http://localhost:8001` | Component B (ORACLE brain) URL |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated allowed origins |
| `MOCK_MODE` | `false` | When `true`, returns canned Contract 3 responses without calling Component B |
| `DEMO_MODE` | `false` | When `true`, game timer is 90s instead of 300s |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |

## API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/session/create` | Create new game session → `{ session_id }` |
| `GET` | `/api/session/{id}/state` | Get current game state |
| `POST` | `/api/session/{id}/start` | Start the countdown timer |
| `GET` | `/api/timeline/{id}` | Get full emotion timeline for debrief |

### WebSocket

**Endpoint:** `ws://localhost:8000/ws/session/{session_id}`

**Incoming (browser → backend):**
- `emotion_data` — Contract 1 emotion readings (~1/s)
- `player_speech` — STT text from Component A

**Outgoing (backend → browser):**
- `ui_update` — Contract 3 UI commands → Component C
- `oracle_speech` — ORACLE response text → Component A (Tavus TTS)
- `timer_tick` — countdown every second
- `phase_change` — phase transition notification
- `game_end` — game over with final score

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, WS endpoint, lifespan
│   ├── config.py            # Env vars via pydantic-settings
│   ├── models.py            # All Pydantic models (Contracts 1-4, WS messages)
│   ├── redis_client.py      # Redis connection + state/timeline CRUD
│   ├── game_state.py        # Session CRUD, phase logic, timer, scoring
│   ├── emotion_processor.py # Buffer, trend, avg, adaptation detection
│   ├── orchestrator.py      # Main loop: emotion → context → ORACLE → broadcast
│   ├── ws_handler.py        # WS connection manager + broadcast
│   └── routes/
│       ├── __init__.py
│       ├── session.py       # REST: create, start, get state
│       └── timeline.py      # REST: get timeline
├── requirements.txt
├── .env.example
├── .env
├── README.md
└── run.py                   # uvicorn runner with reload
```

## Data Flow

### Emotion Loop (every ~1s)
```
Component A → WS emotion_data → EmotionProcessor.push_to_buffer() → Redis timeline (Contract 4)
```

### Interaction Loop (per player turn)
```
Component A → WS player_speech
  → Build Contract 2 (game state + emotion snapshot + history)
  → POST to Component B → Contract 3
  → Apply game updates (score, phase)
  → Detect adaptation → annotate timeline
  → Broadcast: oracle_speech (→ A) + ui_update (→ C)
```

## Mock Mode

When `MOCK_MODE=true`, Component B is not called. Instead, the orchestrator returns alternating Contract 3 responses:
- **Even turns:** "stressed" response — simplified UI, calm colors, high guidance
- **Odd turns:** "focused" response — full dashboard, intense colors, no guidance

This lets you test the full pipeline without Component B running.
