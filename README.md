# SPECTRA

**Emotion-adaptive AI interface** — your face controls the screen.

Built for the AI Interfaces Hackathon with Claude · Feb 21, 2026 · Betaworks NYC

## What is this?

You and an AI partner (ORACLE) collaborate through voice on a timed mission. Your webcam reads your emotions in real time, and the entire interface — layout, colors, complexity, voice tone — reshapes around your emotional state.

## Architecture

```
Webcam → [Tavus Raven-1] → emotion JSON → [Backend/WebSocket] → [Claude] → UI commands → [CopilotKit/React] → Screen
                                                    ↕
                                                 [Redis]
                                              (state + timeline)
```

## Components

| Component | Folder | Tech |
|-----------|--------|------|
| Emotion Pipeline | `emotion-pipeline/` | Tavus Raven-1, Webcam |
| AI Brain (ORACLE) | `oracle-brain/` | Claude API |
| Adaptive Frontend | `frontend/` | React, CopilotKit |
| Voice + Backend | `backend/` | FastAPI, WebSocket, Redis |

## Mock Data

The `mock-data/` folder contains sample JSONs for every data contract between components. Use these to build and test your component independently.

## Setup

```bash
cp .env.example .env
# Fill in API keys
```

See each component's README for specific setup instructions.
