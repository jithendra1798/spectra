# SPECTRA

**Emotion-adaptive AI interface — your face controls the screen.**

You and an AI partner (ORACLE) collaborate through voice on a timed mission. Your webcam reads your emotions in real time, and the entire interface — layout, colors, complexity, voice tone — reshapes around your emotional state.

Built for the AI Interfaces Hackathon with Claude · Feb 21, 2026 · Betaworks NYC

---

## Data Flow

```
┌──────────────────┐    emotion JSON     ┌──────────────────┐   adaptation cmds   ┌──────────────────┐
│   Component A    │ ──────────────────► │   Component B    │ ──────────────────► │   Component C    │
│ Emotion Pipeline │     (every ~1s)     │ AI Brain (ORACLE)│    (per turn)       │ Adaptive Frontend│
│ Tavus Raven-1    │                     │ Claude API       │                     │ React + CopilotKit│
└──────────────────┘                     └──────────────────┘                     └──────────────────┘
                                                │
                          ┌─────────────────────┼─────────────────────┐
                          │            Component D                     │
                          │       Voice + Backend (FastAPI)            │
                          │    connects all pieces via WebSocket       │
                          │                    │                       │
                          │              ┌─────┴─────┐                │
                          │              │   Redis    │                │
                          │              │ state +    │                │
                          │              │ timeline   │                │
                          │              └───────────┘                │
                          └────────────────────────────────────────────┘
```

> **Every component communicates through the JSON formats below. Build and test with mock data tonight — real integration tomorrow.**

---

## Data Contracts

These are the exact JSON shapes passed between components. If everyone respects these formats, integration will be smooth.

### A → D: Emotion Signal
*Emotion Pipeline → Backend (via WebSocket, every ~1 second)*

```json
{
  "timestamp": 1740153600000,
  "emotions": {
    "stress": 0.72,
    "focus": 0.15,
    "confusion": 0.58,
    "confidence": 0.10,
    "neutral": 0.05
  },
  "dominant": "stress",
  "face_detected": true
}
```
- All emotion values are `0-1` floats
- `dominant` = highest scoring emotion
- `face_detected` = `false` if no face in frame

---

### D → B: ORACLE Prompt Context
*Backend → AI Brain (per interaction turn)*

```json
{
  "game_state": {
    "phase": "vault",
    "time_remaining": 182,
    "decisions_made": 3,
    "current_score": 45
  },
  "emotion_snapshot": {
    "current": { },
    "trend": "rising_stress",
    "avg_stress_30s": 0.65
  },
  "player_input": "I think node A looks weakest",
  "conversation_history": [
    { "role": "oracle", "text": "Which entry point?" },
    { "role": "player", "text": "Node A looks weakest" }
  ]
}
```
- `phase`: `"infiltrate"` | `"vault"` | `"escape"`
- `trend`: computed from last 5 emotion readings
- `current`: latest full Emotion Signal JSON

---

### B → D → C: ORACLE Response + UI Commands
*AI Brain → Backend → Frontend (per interaction turn)*

```json
{
  "oracle_response": {
    "text": "Good instinct. Node A has the weakest encryption layer...",
    "voice_style": "calm_reassuring"
  },
  "ui_commands": {
    "complexity": "simplified",
    "color_mood": "calm",
    "panels_visible": ["main"],
    "options": [
      { "id": "A", "label": "Node A", "highlighted": true },
      { "id": "C", "label": "Node C", "highlighted": true }
    ],
    "guidance_level": "high"
  },
  "game_update": {
    "score_delta": 10,
    "advance_phase": false,
    "next_prompt": null
  }
}
```
- `voice_style`: `"calm_reassuring"` | `"direct_fast"` | `"urgent"` | `"neutral"`
- `complexity`: `"simplified"` | `"standard"` | `"full"`
- `color_mood`: `"calm"` | `"neutral"` | `"intense"`
- `guidance_level`: `"none"` | `"low"` | `"medium"` | `"high"`
- `next_prompt`: `null` if staying in current phase

---

### D → Redis: Emotion Timeline Entry
*Backend → Redis (stored every ~1 second, read by debrief screen)*

```json
{
  "t": 1740153600000,
  "phase": "vault",
  "stress": 0.72,
  "focus": 0.15,
  "adaptation": "ui_simplified"
}
```
- `adaptation`: `null` if no adaptation this tick, otherwise `"ui_simplified"` | `"voice_calmed"` | `"options_expanded"` | `"full_dashboard"`
- Stored as Redis sorted set, scored by timestamp
- Debrief screen reads the full set and renders the emotion curve + markers

---

## Component Instructions

Each component can be built and tested independently using `mock-data/`.

### Component A: Emotion Pipeline
**Tech:** Tavus Raven-1 · Webcam · WebSocket

**Goal:** Read the user's face via webcam, output Emotion Signal JSON every ~1 second.

**Build:**
- Webcam capture — request camera permission, get video stream
- Tavus Raven-1 API — send frames, receive emotion scores
- Parse into Emotion Signal JSON format
- Send to backend via WebSocket every ~1s
- Handle: no face detected, camera denied, API timeout

**Test independently:**
- Small test page: webcam + live emotion JSON printout
- Verify JSON matches contract exactly
- Try different expressions — does stress rise when you frown?

> **Fallback:** If Raven-1 gives trouble, build a manual emotion slider that outputs the same JSON. Rest of the system won't know the difference.

---

### Component B: AI Brain (ORACLE)
**Tech:** Claude API · Function Calling · Structured Output

**Goal:** Receive game state + emotion data, output ORACLE's response + UI adaptation commands.

**Build:**
- **System prompt** — ORACLE personality, mission context, emotion-to-UI mapping rules
- **Emotion profiling** — reason about raw scores to determine what user needs
- **Response generation** — given phase + emotion + input, generate text + UI commands
- **Structured output** — Claude must return exact ORACLE Response JSON every time
- **Scenario scripts** — one per phase, 2-3 decision points each

**Test independently:**
- Script that sends mock Context JSON to Claude, prints response
- Vary emotion snapshots — does high stress → `"simplified"` commands?
- Verify JSON is parseable and matches contract

> **The system prompt is the most important deliverable.** ORACLE's quality = prompt quality.

---

### Component C: Adaptive Frontend
**Tech:** React · CopilotKit · CSS Transitions

**Goal:** Render mission UI. Dynamically swap layout, colors, components based on UI commands.

**Build:**
- **3 phase screens** — Infiltrate (node grid), Vault (code puzzle), Escape (route map)
- **Adaptive rendering** — simplified / standard / full variants per `ui_commands.complexity`
- **Color mood system** — CSS variables shift per `ui_commands.color_mood`
- **Panel visibility** — show/hide per `ui_commands.panels_visible`
- **Option rendering** — dynamic from `ui_commands.options` array
- **Timer** — countdown display, color shifts as time drops
- **Debrief screen** — timeline from Redis, stress curve + adaptation markers
- **CopilotKit** — generative UI for dynamic component rendering

**Test independently:**
- Mock panel with buttons: "stressed" / "focused" / "advance phase"
- Feed mock ORACLE Response JSON, verify UI changes visually
- Test debrief with mock timeline array

> **Priority:** One phase working with adaptive rendering first → duplicate → debrief last (it's the demo closer, make it polished).

---

### Component D: Voice I/O + Backend + Integration
**Tech:** FastAPI · WebSocket · Web Speech API · Redis · ElevenLabs (optional)

**Goal:** Route data between components. Voice in/out. Game state. Emotion timeline storage.

**Build:**
- **FastAPI + WebSocket** — receive emotion data from A, route to B
- **Game state manager** — phase, timer, score, conversation history
- **Voice input** — Web Speech API (browser) → text → backend
- **Voice output** — TTS for ORACLE (browser TTS or ElevenLabs)
- **Redis** — store timeline entries + game state, expose API for debrief
- **Orchestration loop** — emotion + voice → context JSON → Claude → response → frontend + speak
- **Timer** — server-side 5-min countdown, broadcast to frontend

**Test independently:**
- FastAPI running, send mock emotion via WebSocket, verify routing
- Voice input → text arrives at server
- Redis write/read timeline entries
- Full mock loop end-to-end

> **Integration is the biggest risk.** Get WebSocket routing working first with dummy data. Once data flows, everything else is refinement.

---

## Repo Structure

```
spectra/
├── emotion-pipeline/        # Component A
│   ├── tavus_client.py
│   ├── webcam.js
│   └── README.md
├── oracle-brain/            # Component B
│   ├── system_prompt.txt
│   ├── scenarios.py
│   ├── claude_client.py
│   └── README.md
├── frontend/                # Component C
│   ├── src/
│   │   ├── phases/
│   │   ├── debrief/
│   │   ├── adaptive/
│   │   └── App.jsx
│   └── README.md
├── backend/                 # Component D
│   ├── server.py
│   ├── game_state.py
│   ├── redis_client.py
│   └── README.md
├── mock-data/               # Shared mock data
│   ├── emotion_signal.json
│   ├── oracle_response.json
│   ├── context_payload.json
│   └── timeline_entries.json
├── docker-compose.yml
├── .env.example
└── README.md
```

> **mock-data/** is key — everyone tests against the same JSONs. If your component produces correct output from mock input, integration will work.

---

## Tonight's Checklist

**Emotion Pipeline**
- [ ] Webcam capture working
- [ ] Tavus API call working (or fallback slider)
- [ ] Outputting correct Emotion Signal JSON

**AI Brain**
- [ ] System prompt written and tested
- [ ] Claude returning valid ORACLE Response JSON
- [ ] Infiltrate phase scenario working

**Adaptive Frontend**
- [ ] One phase with simplified / standard / full variants
- [ ] Color mood switching on mock input
- [ ] Debrief screen rendering mock timeline

**Voice + Backend**
- [ ] FastAPI + WebSocket running
- [ ] Voice → text working
- [ ] Redis storing/retrieving timeline entries
- [ ] Mock data flowing through full loop

---

## Setup

```bash
cp .env.example .env
# Fill in your API keys
```

See each component's README for specific instructions.

---

**Let's build.** 🚀
