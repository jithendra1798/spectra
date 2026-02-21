Perfect. I’ll generate a **clean, hackathon-ready README** for your current frontend state — honest about what’s implemented, clear about integration contracts, and future-ready for CopilotKit + backend.

You can paste this directly into `README.md`.

---

# SPECTRA Frontend

**Emotion-adaptive AI interface — your face controls the screen.**

This is the frontend for **SPECTRA**, built for the AI Interfaces Hackathon (Claude · Tavus · CopilotKit · Redis).

The frontend renders a multi-phase mission interface that dynamically adapts based on:

* Emotion signals (stress, focus, confusion, etc.)
* Claude-generated UI commands
* Game state updates from backend
* Timer updates
* Phase transitions

---

## 🚀 Current Status

### ✅ Implemented

* 3 mission phases:

  * `Infiltrate`
  * `Vault`
  * `Escape`
* Adaptive UI:

  * `complexity`: simplified / standard / full
  * `color_mood`: calm / neutral / intense
  * dynamic panel visibility
  * dynamic options rendering
* Timer display
* Phase switching
* WebSocket integration layer
* Demo mode with emotion simulation
* Debrief route (timeline-ready)
* Reconnect-safe WebSocket hook

### 🚧 Not Yet Integrated (Backend-dependent)

* Tavus CVI (webcam + mic)
* Real emotion streaming
* Claude backend orchestration
* Redis timeline API
* CopilotKit runtime endpoint

---

## 🧠 Architecture (Frontend Role)

Frontend is **Component C** in the system:

```
Backend (FastAPI + Claude)
        ↓
WebSocket
        ↓
useSpectraSocket
        ↓
Reducer (uiReducer)
        ↓
React Adaptive UI
```

Frontend does **not reason**.
Frontend executes UI commands deterministically.

---

## 🛠 Tech Stack

* React 18
* Vite
* TypeScript
* CSS variables (theme-based adaptive styling)
* WebSocket (real-time updates)
* CopilotKit (integration-ready scaffold)

---

## 📂 Project Structure

```
src/
  adaptive/
    emotionEngine.ts
    timelineStore.ts
    types.ts
    uiReducer.ts
    useSpectraSocket.ts
  components/
    DemoControls.tsx
    OptionGrid.tsx
    Timer.tsx
  pages/
    Start.tsx
    Mission.tsx
    Debrief.tsx
  phases/
    Infiltrate.tsx
    Vault.tsx
    Escape.tsx
    PhaseFrame.tsx
    panels/
      StatsPanel.tsx
      RadarPanel.tsx
      CommsPanel.tsx
```

---

## 🧪 Demo Mode

Run:

```
npm install
npm run dev
```

Open:

```
http://localhost:5173/?demo=1
```

Demo Mode Features:

* Manual stress slider
* Phase switching
* UI complexity simulation
* Timer simulation
* No backend required

---

## 🔌 Backend Integration Contract

Frontend connects to:

```
ws://<backend>/ws/{sessionId}
```

Default:

```
ws://localhost:8000/ws/{sessionId}
```

Override via `.env`:

```
VITE_WS_BASE_URL=ws://localhost:8000
```

---

## 📡 WebSocket Inbound Messages (Backend → Frontend)

Backend must send JSON messages in one of the following formats:

### UI Update

```
{
  "type": "ui_update",
  "data": {
    "complexity": "simplified",
    "color_mood": "calm",
    "panels_visible": ["main"],
    "options": [
      { "id": "A", "label": "Node A", "highlighted": true }
    ],
    "guidance_level": "high"
  }
}
```

---

### Timer Tick

```
{
  "type": "timer_tick",
  "time_remaining": 182
}
```

---

### Phase Change

```
{
  "type": "phase_change",
  "phase": "vault"
}
```

---

### Oracle Speech

```
{
  "type": "oracle_said",
  "text": "Good instinct. Node A is weaker.",
  "voice_style": "calm_reassuring"
}
```

---

### Game End

```
{
  "type": "game_end",
  "final_score": 87
}
```

---

### Optional: Timeline Point (for Debrief)

```
{
  "type": "timeline_point",
  "data": {
    "t": 1740153600000,
    "phase": "vault",
    "stress": 0.72,
    "focus": 0.15,
    "adaptation": "ui_simplified"
  }
}
```

---

## 📤 WebSocket Outbound Messages (Frontend → Backend)

### Player Speech

```
{
  "type": "player_speech",
  "text": "I choose Node A"
}
```

---

### Emotion Data (If streaming from browser)

```
{
  "type": "emotion_data",
  "data": { ...Contract1 }
}
```

---

## 🎯 Reducer-Driven Adaptation

All UI changes are applied through:

```
uiReducer.ts
```

WebSocket messages are dispatched directly into reducer.

Reducer is the **single source of truth**.

---

## 🤖 CopilotKit (Integration Ready)

Frontend is prepared to expose CopilotKit actions:

Planned actions:

* `apply_ui_commands`
* `set_phase`
* `oracle_said`
* `apply_game_update`

CopilotKit will act as the structured bridge between Claude tool calls and reducer state mutations.

Frontend remains deterministic — CopilotKit executes UI mutations via reducer dispatch.

---

## 🧩 Debrief Screen

Debrief page expects either:

* `GET /api/timeline/{sessionId}`
  or
* WebSocket `timeline_point` stream

It renders:

* Stress curve
* Phase boundaries
* Adaptation markers
* Summary stats

If backend not available, demo fallback is used.

---

## ⚙️ Environment Variables

Create `.env`:

```
VITE_WS_BASE_URL=ws://localhost:8000
```

---

## 🏁 Hackathon Integration Strategy

Frontend supports two backend modes:

### Mode A (Recommended)

Backend sends Contract 3 over WebSocket.

### Mode B (CopilotKit Runtime)

Claude calls CopilotKit actions directly.

Frontend supports both.

---

## 📌 Summary

Frontend is:

* Adaptive
* Phase-driven
* Emotion-reactive
* Integration-ready
* Reducer-based
* WebSocket-safe
* CopilotKit-compatible

Backend + Tavus can plug in without requiring frontend refactor.

---

## 👤 Author

Manoj Sadanala
Frontend + Adaptive UI
AI Interfaces Hackathon 2026

---

If you want, I can also generate:

* a shorter Devpost-ready README
* or a judge-facing README
* or a technical architecture appendix version

Just tell me which tone you want.
