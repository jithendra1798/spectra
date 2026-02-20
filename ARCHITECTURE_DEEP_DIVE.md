# SPECTRA

**Emotion-adaptive AI interface — your face controls the screen.**

You and an AI partner (ORACLE) collaborate through voice on a timed mission. Your webcam reads your emotions in real time, and the entire interface — layout, colors, complexity, voice tone — reshapes around your emotional state. ORACLE has a face — a Tavus-powered video avatar that sees you, hears you, and talks back.

Built for the AI Interfaces Hackathon with Claude · Feb 21, 2026 · Betaworks NYC

---

## How It Works — The Two Loops

### Overview: How the 4 Components Connect

```
                          ┌─────────────────────────────────────────────────┐
                          │                    USER                         │
                          │          face (webcam) + voice (mic)            │
                          └──────────────────────┬──────────────────────────┘
                                                 │
                                                 ▼
                ┌────────────────────────────────────────────────────────────┐
                │                    COMPONENT A                             │
                │              Tavus CVI Session                             │
                │   emotion detection · STT (voice→text) · TTS (text→voice)  │
                │                  ORACLE's face + ears + mouth              │
                └────────┬──────────────────────────────────┬────────────────┘
                         │                                  ▲
              emotion JSON (Contract 1)          ORACLE's response text
              + player speech text                (from Contract 3)
                         │                                  │
                         ▼                                  │
                ┌───────────────────────────────────────────────────────────┐
                │                    COMPONENT D                            │
                │                 Backend (FastAPI)                         │
                │    orchestration · game state · timer · Redis storage     │
                └────────┬──────────────────────────────────┬───────────────┘
                         │                                  │
              Context JSON (Contract 2)          UI commands (from Contract 3)
                         │                                  │
                         ▼                                  ▼
                ┌─────────────────────┐     ┌───────────────────────────────┐
                │     COMPONENT B     │     │         COMPONENT C           │
                │   Claude (ORACLE)   │     │   React + CopilotKit          │
                │   reasoning engine  │     │   adaptive UI rendering       │
                │                     │     │   + debrief visualization     │
                └─────────────────────┘     └───────────────────────────────┘
                         │                                  ▲
                         │        Contract 3                │
                         └──── (response + UI commands) ────┘
                                  via Component D

                ┌───────────┐
                │   Redis   │ ◄── Component D stores emotion timeline (Contract 4)
                │           │ ──► Component C reads timeline for debrief screen
                └───────────┘
```

SPECTRA runs two parallel loops simultaneously:

### Loop 1: Emotion Loop (continuous, every ~1 second)
Runs silently in the background the entire time.

```
                                ┌──────────────┐                     ┌─────────────┐                     ┌───────────┐
┌─────────┐                     │ COMPONENT A  │    emotion JSON     │ COMPONENT D │    store every 1s   │   Redis   │
│  USER's │   webcam + mic ───► │ Tavus CVI    │ ──────────────────► │ Backend     │ ──────────────────► │ (timeline │
│  FACE   │   (video stream)    │ (session)    │   (Contract 1)      │ (FastAPI)   │   (Contract 4)      │  storage) │
└─────────┘                     └──────────────┘                     └─────────────┘                     └───────────┘
```

**What happens:** Component A (Tavus CVI) has an open session with the user's webcam. It continuously analyzes the user's face and extracts emotion scores (stress, focus, confusion, etc.). Component A sends these scores to Component D (backend) every ~1 second via WebSocket. Component D stores each reading in Redis as a timestamped entry (Contract 4) — this builds the emotion timeline that powers the debrief screen at the end.

---

### Loop 2: Interaction Loop (per turn, when user speaks)
Runs every time the user says something or a decision point is reached.

```
                                 ┌──────────────┐
                                 │ COMPONENT A  │
                                 │ Tavus CVI    │
┌──────────┐   user speaks ─────►│              │                   ┌─────────────┐
│          │                     │  STT ────────│── player text ──► │ COMPONENT D │
│   USER   │                     │  (built-in)  │                   │ Backend     │
│          │                     │              │                   │ (FastAPI)   │
│          │◄─ ORACLE speaks ─── │  TTS + Avatar│◄─ response text ──│             │
│          │   (video + voice)   │  (built-in)  │                   │             │
└──────────┘                     └──────────────┘                   └─────┬───────┘
                                                                          │
                                                          builds Context JSON (Contract 2)
                                                          (game state + emotion + player input)
                                                                          │
                                                                          ▼
                                                                   ┌─────────────┐
                                                                   │ COMPONENT B │
                                                                   │ Claude      │
                                                                   │ (ORACLE's   │
                                                                   │  brain)     │
                                                                   └──────┬──────┘
                                                                          │
                                                                returns Contract 3
                                                          (ORACLE response + UI commands)
                                                                          │
                                                                          ▼
                                                                   ┌─────────────┐
┌─────────┐   screen adapts     ┌──────────────┐  UI commands via  │ COMPONENT D │
│  USER   │ ◄────────────────── │ COMPONENT C  │◄── WebSocket ─────│ Backend     │
│  (sees) │                     │ React +      │                   │ (FastAPI)   │
└─────────┘                     │ CopilotKit   │                   └─────────────┘
                                └──────────────┘
```

**What happens:**

1. **User speaks** → Component A (Tavus CVI) captures audio and converts speech to text (STT built into CVI)
2. **Component A → Component D** → player text forwarded to backend
3. **Component D builds Contract 2** → packages player text + current game state + latest emotion snapshot into Context JSON
4. **Component D → Component B** → sends Contract 2 to Claude
5. **Component B (Claude) reasons** → decides what ORACLE should say + how UI should adapt → returns Contract 3
6. **Contract 3 splits two ways:**
   - **Component D → Component A** → sends `oracle_response.text` → Tavus CVI avatar speaks it (user hears ORACLE)
   - **Component D → Component C** → sends `ui_commands` via WebSocket → React + CopilotKit adapts the screen (user sees changes)

Steps 6a and 6b happen simultaneously — the user hears ORACLE and sees the screen change at the same time.

---

## Role of Each Sponsor Technology

| Sponsor Tech | What It Does in SPECTRA | Why It's Essential |
|------------|-------------|----------------|
| **Tavus CVI** | ORACLE's face, ears, and mouth. Reads the user's emotions through webcam. Hears user speak (STT). Speaks back as a video avatar (TTS). All in one real-time session. | Without Tavus, there's no emotion signal, no voice conversation, and no ORACLE avatar. It's the entire human-facing layer. |
| **Claude (Anthropic)** | ORACLE's brain. Receives emotion data + game state + player input. Reasons about what to say and how the UI should adapt. Returns structured JSON with voice response + UI commands. | Without Claude, ORACLE can't think. No reasoning about emotions, no adaptive decisions, no scenario generation. |
| **CopilotKit** | The adaptive UI engine. Takes Claude's UI commands and dynamically renders different React components at runtime. Stressed → simplified layout. Focused → full dashboard. | Without CopilotKit, the UI is static. Claude can decide what should change but nothing actually changes on screen. |
| **Redis** | Real-time memory. Stores emotion readings every second as a timestamped sorted set. Caches game state for instant lookups. Powers the debrief screen. | Without Redis, there's no emotion timeline, the debrief screen is empty, and state lookups are too slow for real-time gameplay. |

> **Remove any single sponsor and the product breaks.** That's intentional — judges notice when sponsor tech is essential vs. decorative.

---

## The Four Components

### Component A: Tavus CVI + Emotion Extraction
**Tech: Tavus CVI API**

Responsible for setting up the Tavus conversation session and extracting emotion data from it.

**Builds:**
- Tavus CVI session creation (persona setup for ORACLE — name, voice, appearance)
- Embed CVI widget in the frontend (the video window where ORACLE's face appears)
- Extract emotion scores from the CVI session in real time
- Parse into Contract 1 JSON format and send to backend via WebSocket every ~1s
- Handle STT callback — when user speaks, CVI converts to text, forward to backend
- Handle TTS — when backend sends ORACLE's response text, feed it to CVI so avatar speaks
- Handle edge cases: no face detected, mic permission denied, CVI session timeout

**Outputs:** Contract 1 (Emotion Signal) → to Component D every ~1s
**Receives:** ORACLE response text from Component D → feeds to CVI for avatar to speak
**Receives:** Player speech text from CVI STT → forwards to Component D

> **Fallback:** If CVI setup is too complex, fall back to Raven-1 (emotion only) + browser Web Speech API for voice. Same JSON contracts, same system — just no avatar face.

---

### Component B: AI Brain (ORACLE)
**Tech: Claude API · Structured Output**

Responsible for ORACLE's intelligence — receives the full picture, decides how to respond and adapt.

**Builds:**
- System prompt defining ORACLE's personality + emotion-to-UI mapping rules
- Structured emotion profiling (take raw scores → reason about what user needs)
- Response generation (what ORACLE says + how the UI should change)
- Claude must output exact Contract 3 JSON format every time
- Scenario scripts for each of the 3 phases (2-3 decision points each)

**Receives:** Contract 2 (Context JSON) from Component D
**Outputs:** Contract 3 (ORACLE Response + UI Commands) → to Component D

> **The system prompt is the most important deliverable.** ORACLE's quality = prompt quality.

---

### Component C: Adaptive Frontend
**Tech: React · CopilotKit · CSS**

Responsible for everything the user sees on screen (except the Tavus avatar window) — and making it adapt.

**Builds:**
- 3 phase screens: Infiltrate (node grid), Vault (code puzzle), Escape (route map)
- Each screen has 3 variants: `simplified`, `standard`, `full` — driven by Contract 3
- Color mood system (CSS variables shift based on `color_mood`)
- Panel show/hide based on `panels_visible`
- Dynamic option buttons from `options` array
- Timer countdown display
- CopilotKit integration for generative UI (Claude dynamically picks which components render)
- Layout includes embedded Tavus CVI window (ORACLE's face) alongside the mission UI
- Debrief screen: fetches Contract 4 entries from backend API → renders emotion curve + adaptation markers

**Receives:** Contract 3 (UI commands) from Component D via WebSocket
**Reads:** Contract 4 entries from Redis (via backend API) for debrief

> **Priority:** Get one phase with adaptive rendering working first → duplicate for others → debrief screen last (it's the demo closer).

---

### Component D: Backend + Integration
**Tech: FastAPI · WebSocket · Redis**

The central hub that connects all components, manages game state, and stores the timeline.

**Builds:**
- **FastAPI server** with WebSocket endpoints for real-time communication with frontend and Component A
- **Orchestration loop:**
  1. Receive emotion JSON (Contract 1) from Component A → update current emotion state
  2. Receive player speech text from Component A (forwarded from CVI STT)
  3. Build Context JSON (Contract 2) = current game state + latest emotion snapshot + player text + conversation history
  4. Send Contract 2 to Claude → receive Contract 3 back
  5. Forward `oracle_response.text` to Component A → CVI avatar speaks it
  6. Forward `ui_commands` to Component C via WebSocket → frontend adapts
- **Redis writes:** Store Contract 4 (emotion timeline entry) every ~1 second
- **Redis reads:** Expose GET `/api/timeline/{session_id}` endpoint for debrief screen
- **Game state manager:** Track current phase, 5-minute timer countdown, score, conversation history
- **Timer broadcast:** Send `time_remaining` to frontend every second via WebSocket
- **Phase transitions:** When Contract 3 has `advance_phase: true`, update phase, reset conversation history, notify frontend

**Receives:** Contract 1 from Component A, Contract 3 from Component B, player text from Component A
**Sends:** Contract 2 to Component B, Contract 3 to Component C, response text to Component A
**Stores/Reads:** Contract 4 to/from Redis

> **Integration is the biggest risk.** Get WebSocket routing working first with dummy data. Once data flows end-to-end, everything else is refinement.

---

## Data Contracts

### Contract 1: Emotion Signal
**Route:** A → D *(via WebSocket, every ~1 second)*

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

| Key | Type | Description |
|-----|------|-------------|
| `timestamp` | `int` | Unix time in ms when this reading was captured |
| `emotions.stress` | `float 0-1` | Stressed/anxious (furrowed brow, tense jaw, rapid blinking) |
| `emotions.focus` | `float 0-1` | Focused/engaged (steady gaze, relaxed brow) |
| `emotions.confusion` | `float 0-1` | Confused (squinting, head tilt, lip tension) |
| `emotions.confidence` | `float 0-1` | Confident (relaxed face, slight smile) |
| `emotions.neutral` | `float 0-1` | No strong emotion (resting face) |
| `dominant` | `string` | Highest scoring: `"stress"` \| `"focus"` \| `"confusion"` \| `"confidence"` \| `"neutral"` |
| `face_detected` | `boolean` | `false` if user looks away or camera fails. System holds last known state. |

---

### Contract 2: ORACLE Prompt Context
**Route:** D → B *(per interaction turn)*

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
    { "role": "oracle", "text": "Which entry point looks weakest?" },
    { "role": "player", "text": "I think node A looks weakest" }
  ]
}
```

| Key | Type | Description |
|-----|------|-------------|
| `game_state.phase` | `string` | `"infiltrate"` (pick entry) \| `"vault"` (crack code) \| `"escape"` (choose route) |
| `game_state.time_remaining` | `int` | Seconds left on 5-minute clock |
| `game_state.decisions_made` | `int` | Total player decisions so far |
| `game_state.current_score` | `int` | Running score 0-100 |
| `emotion_snapshot.current` | `object` | Latest Contract 1 JSON |
| `emotion_snapshot.trend` | `string` | `"rising_stress"` \| `"falling_stress"` \| `"rising_focus"` \| `"falling_focus"` \| `"stable"` |
| `emotion_snapshot.avg_stress_30s` | `float 0-1` | Rolling 30s stress average. Smooths spikes. |
| `player_input` | `string or null` | Speech-to-text from CVI. `null` if system-triggered. |
| `conversation_history` | `array` | All messages this phase. `role`: `"oracle"` or `"player"`. Resets on phase advance. |

---

### Contract 3: ORACLE Response + UI Commands
**Route:** B → D → split to A (voice) and C (UI) *(per interaction turn)*

```json
{
  "oracle_response": {
    "text": "Good instinct. Node A has the weakest encryption layer.",
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

| Key | Type | Description |
|-----|------|-------------|
| `oracle_response.text` | `string` | What ORACLE says. Sent to Tavus CVI → avatar speaks it. |
| `oracle_response.voice_style` | `string` | `"calm_reassuring"` (slow, soft) · `"direct_fast"` (quick, confident) · `"urgent"` (timer <60s) · `"neutral"` (default) |
| `ui_commands.complexity` | `string` | `"simplified"` (fewer options, hidden panels) · `"standard"` (default) · `"full"` (all panels, extra options) |
| `ui_commands.color_mood` | `string` | `"calm"` (blues/greens) · `"neutral"` (default) · `"intense"` (reds/oranges) |
| `ui_commands.panels_visible` | `array` | `"main"` (interaction area) · `"stats"` (score/timer) · `"radar"` (progress) · `"comms"` (conversation log) |
| `ui_commands.options[].id` | `string` | Unique option ID |
| `ui_commands.options[].label` | `string` | Display text |
| `ui_commands.options[].highlighted` | `boolean` | `true` = ORACLE's recommendation, visually emphasized |
| `ui_commands.guidance_level` | `string` | `"none"` · `"low"` · `"medium"` · `"high"` (actively recommends) |
| `game_update.score_delta` | `int` | Points earned/lost this turn |
| `game_update.advance_phase` | `boolean` | `true` = move to next phase |
| `game_update.next_prompt` | `string or null` | ORACLE's opening line for next phase. `null` = wait for player. |

---

### Contract 4: Emotion Timeline Entry
**Route:** D → Redis *(every ~1 second, read by debrief)*

```json
{
  "t": 1740153600000,
  "phase": "vault",
  "stress": 0.72,
  "focus": 0.15,
  "adaptation": "ui_simplified"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `t` | `int` | Unix ms timestamp. Redis sorted set score. |
| `phase` | `string` | Active phase. Draws boundaries on debrief graph. |
| `stress` | `float 0-1` | Primary Y-axis for debrief curve. |
| `focus` | `float 0-1` | Secondary debrief data. |
| `adaptation` | `string or null` | `null` = no change. `"ui_simplified"` · `"voice_calmed"` · `"options_expanded"` · `"full_dashboard"` — become marker dots on debrief. |

**Redis key:** `session:{session_id}:timeline` (sorted set). Debrief fetches with `ZRANGEBYSCORE`.

---

## Repo Structure

```
spectra/
├── tavus-pipeline/          # Component A
│   ├── cvi_client.py          # Tavus CVI session setup + management
│   ├── emotion_extractor.py   # Extract emotion scores from CVI
│   └── README.md
├── oracle-brain/            # Component B
│   ├── system_prompt.txt
│   ├── scenarios.py
│   ├── claude_client.py
│   └── README.md
├── frontend/                # Component C
│   ├── src/
│   │   ├── phases/            # Infiltrate, Vault, Escape screens
│   │   ├── debrief/           # Timeline visualization
│   │   ├── adaptive/          # Emotion-driven CSS + CopilotKit logic
│   │   ├── TavusEmbed.jsx     # CVI avatar window component
│   │   └── App.jsx
│   └── README.md
├── backend/                 # Component D
│   ├── server.py              # FastAPI + WebSocket
│   ├── game_state.py          # Phase, timer, score, history
│   ├── redis_client.py        # Timeline storage + retrieval
│   └── README.md
├── mock-data/
│   ├── emotion_signal.json
│   ├── oracle_response.json
│   ├── context_payload.json
│   └── timeline_entries.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Tonight's Checklist

**Tavus CVI + Emotion (Component A)**
- [ ] CVI session created with ORACLE persona
- [ ] Emotion scores extracting from CVI in real time
- [ ] Outputting correct Contract 1 JSON to backend
- [ ] STT working (user speech → text → backend)
- [ ] TTS working (response text → avatar speaks)

**AI Brain (Component B)**
- [ ] System prompt written and tested
- [ ] Claude returning valid Contract 3 from mock Contract 2
- [ ] Infiltrate phase scenario working

**Adaptive Frontend (Component C)**
- [ ] One phase screen with simplified / standard / full variants
- [ ] Color mood switching on mock Contract 3
- [ ] Tavus CVI widget embedded in layout
- [ ] Debrief screen rendering mock Contract 4 timeline

**Backend + Integration (Component D)**
- [ ] FastAPI + WebSocket running
- [ ] Redis storing/retrieving Contract 4 entries
- [ ] Orchestration loop working with mock data end-to-end
- [ ] Timer countdown broadcasting

---

## Setup

```bash
cp .env.example .env
# Fill in API keys: ANTHROPIC_API_KEY, TAVUS_API_KEY, REDIS_URL
```

See each component's README for specific instructions.

---

**Let's build.** 🚀
