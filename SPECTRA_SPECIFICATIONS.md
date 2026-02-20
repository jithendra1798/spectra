# SPECTRA — Project Specification

> **Emotion-adaptive AI interface where your face controls the screen.**

This document is the complete reference for building SPECTRA. It covers what we're building, how it works, what each component does, the game design, emotion-to-UI mapping rules, the debrief screen, demo plan, and tech stack. Read this before you start coding.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [User Experience Walkthrough](#2-user-experience-walkthrough)
3. [Architecture](#3-architecture)
4. [The Three Phases — Game Design](#4-the-three-phases--game-design)
5. [Emotion-to-UI Mapping Rules](#5-emotion-to-ui-mapping-rules)
6. [Debrief Screen Specification](#6-debrief-screen-specification)
7. [Component Specifications](#7-component-specifications)
8. [Data Contracts](#8-data-contracts)
9. [Tech Stack & Resources](#9-tech-stack--resources)
10. [Demo Script](#10-demo-script)
11. [Build Plan](#11-build-plan)

---

## 1. Project Overview

SPECTRA is a **real-time emotion-adaptive interactive experience** built for the AI Interfaces Hackathon with Claude (Feb 21, 2026).

A user sits at a laptop and collaborates with an AI partner called **ORACLE** through voice to complete a timed 5-minute mission. ORACLE appears on screen as a **Tavus-powered video avatar** — it sees the user's face, hears them speak, and talks back.

The core innovation: **the user's emotional state is a control input**. The webcam continuously reads the user's facial expressions, and the entire interface — layout, colors, complexity, number of options, ORACLE's voice tone — reshapes in real time based on whether the user is stressed, focused, confused, or confident.

After the mission, a **debrief screen** visualizes the user's emotional journey as a timeline, showing every moment the AI adapted to them.

### What Makes This Different

- The **interface itself** is the product — not a chatbot with a nicer UI
- The user's **face is an input device** alongside their voice
- Every pixel on screen responds to **emotional state**, not just text commands
- The **debrief** makes the experience personal and memorable — users see their own emotional data
- All 4 sponsor technologies (Tavus, Claude, CopilotKit, Redis) are structurally essential

### Hackathon Context

- **Event:** AI Interfaces Hackathon with Claude · AI Tinkerers NYC
- **Sponsors:** Anthropic (Claude), Tavus, Redis, CopilotKit
- **Venue:** Betaworks, 29 Little West 12th St, NYC
- **Date:** Saturday, February 21, 2026 · 9 AM – 9 PM
- **Judging Criteria:**
  1. Working Prototype & Execution (stability, responsiveness)
  2. Interface Novelty & Playfulness (new UI patterns, not standard chat)
  3. Theme Alignment: Generative Interfaces (interaction is the innovation)
  4. Leveraging Claude's Capabilities (beyond basic LLM usage)

---

## 2. User Experience Walkthrough

This is exactly what the user sees, hears, and does from start to finish.

### 2.1 Start Screen
- User sees a dark, mission-themed landing screen
- ORACLE's avatar face appears in a video window (Tavus CVI)
- A "Begin Mission" button
- Webcam permission prompt (required)
- Brief text: *"ORACLE will see your face and adapt to how you feel. Ready?"*

### 2.2 Mission Briefing (10 seconds)
- ORACLE's avatar speaks: *"We have 5 minutes to extract classified data from a secure vault. I can hack systems, but I need your judgment to make the right calls. Neither of us can do this alone. Ready?"*
- Timer appears: **5:00**
- User says "Ready" (or any affirmative) → mission begins

### 2.3 Phase 1: Infiltrate (~90 seconds)
- Screen shows a grid of security entry points (nodes)
- ORACLE speaks: *"I've identified three possible entry points. Which pattern looks weakest to you?"*
- User speaks their choice
- ORACLE responds based on choice quality + user's emotion state
- 1-2 decision points in this phase
- Phase ends when ORACLE says *"We're in. Moving to the vault."*

### 2.4 Phase 2: Crack the Vault (~120 seconds)
- Screen shifts to a code-breaking interface
- ORACLE runs computations, presents decision forks
- User makes judgment calls under time pressure
- This is where stress peaks — the timer is visible and ticking
- 2-3 decision points in this phase
- Phase ends when ORACLE says *"Vault cracked. Now we need to get out."*

### 2.5 Phase 3: Escape (~90 seconds)
- Screen shows route options with risk/reward data
- ORACLE presents paths, user chooses under time pressure
- Fast-paced, fewer options, higher stakes
- 1-2 decision points
- Phase ends when timer hits 0 or user escapes

### 2.6 Mission End
- If timer runs out: ORACLE says *"Time's up. Let's see how we did."*
- If user escapes in time: ORACLE says *"We made it. Let's debrief."*
- Transition to debrief screen

### 2.7 Debrief Screen
- Full emotion timeline visualization (see Section 6)
- ORACLE's avatar gives a brief summary: *"Here's your emotional journey through the mission."*
- User sees their stress curve, adaptation moments, and collaboration score

### During the Entire Experience
While all of the above is happening, these things run continuously:
- **Webcam reads emotions** every ~1 second via Tavus
- **UI adapts** based on emotional state (see Section 5 for exact rules)
- **ORACLE's voice tone** changes based on user's stress level
- **Every emotion reading** is stored with a timestamp for the debrief

---

## 3. Architecture

### 3.1 Overview: How the 4 Components Connect

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
                │   emotion detection · STT (voice→text) · TTS (text→voice) │
                │                  ORACLE's face + ears + mouth              │
                └────────┬──────────────────────────────────┬───────────────┘
                         │                                  ▲
              emotion JSON (Contract 1)          ORACLE's response text
              + player speech text                (from Contract 3)
                         │                                  │
                         ▼                                  │
                ┌────────────────────────────────────────────────────────────┐
                │                    COMPONENT D                             │
                │                 Backend (FastAPI)                          │
                │    orchestration · game state · timer · Redis storage      │
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

### 3.2 The Two Parallel Loops

**Loop 1 — Emotion (continuous, every ~1 second):**
```
User's face → Component A (Tavus CVI reads emotions) → Contract 1 JSON → Component D (backend) → stores Contract 4 in Redis
```
This runs silently in the background the entire time, building the emotion timeline.

**Loop 2 — Interaction (per turn, when user speaks):**
```
User speaks → Component A (CVI STT) → text → Component D (builds Contract 2) → Component B (Claude reasons) → Contract 3 → Component D splits:
  → Component A: ORACLE's response text → CVI avatar speaks it
  → Component C: UI commands via WebSocket → screen adapts
```

### 3.3 Role of Each Technology

| Technology | Role | Why Essential |
|------------|------|---------------|
| **Tavus CVI** | ORACLE's face, ears, and mouth. Emotion detection + STT + TTS + video avatar. | Without it: no emotion signal, no voice, no avatar. The entire human-facing layer. |
| **Claude** | ORACLE's brain. Receives emotion + game state + player input. Decides responses and UI adaptations. | Without it: ORACLE can't think. No reasoning, no adaptive decisions. |
| **CopilotKit** | Adaptive UI engine. Claude's commands dynamically render different React components at runtime. | Without it: UI is static. Claude can decide what to change but nothing changes on screen. |
| **Redis** | Real-time memory. Stores emotion timeline + game state. Sub-50ms lookups. | Without it: no debrief timeline, state lookups too slow for real-time gameplay. |
| **WebSocket** | Real-time bidirectional connection between browser and backend. | Emotion data streams every ~1s. UI commands must arrive instantly. HTTP too slow. |
| **FastAPI** | Python backend orchestrating all components. | Central hub connecting everything. |

---

## 4. The Three Phases — Game Design

Each phase is **one screen with 1-3 decision points**. There is no game engine — Claude generates all scenarios, presents options via voice, and evaluates player responses. The mission theme exists solely to create genuine emotions (stress from the timer, relief from progress, focus from engagement).

### Phase 1: Infiltrate

**Setting:** A security grid showing entry points to a building.

**Visual:** Dark screen with glowing nodes representing security entry points. Lines connecting them suggest a network topology.

**ORACLE's opening:** *"I've identified three possible entry points. Node A has low encryption but active monitoring. Node B is heavily encrypted but unmonitored. Node C is a maintenance port — unknown security. Which pattern looks weakest to you?"*

**Decision points:**
1. **Choose entry point** — player speaks their choice. Each has different risk/reward.
2. **React to complication** — ORACLE reports a problem with the chosen path, player must decide: push through or reroute?

**Success criteria (for Claude to evaluate):**
- Choosing based on reasoning (not random) = higher score
- Adapting to complications smoothly = higher score
- Speed of decision = minor score factor

**Phase transition:** ORACLE says *"We're through. Firewall bypassed. Moving to the vault."*

---

### Phase 2: Crack the Vault

**Setting:** A code-breaking interface with multiple data streams.

**Visual:** Central code display with scrolling data. Side panels show computation progress, threat level, and time remaining. This is the most visually complex phase.

**ORACLE's opening:** *"The vault uses a rotating cipher. I can brute-force sections, but I need you to spot the pattern in the sequence. Look at these three code fragments..."*

**Decision points:**
1. **Pattern recognition** — ORACLE presents code fragments, player identifies the pattern
2. **Risk assessment** — ORACLE offers fast (risky) vs. slow (safe) decryption paths
3. **Abort decision** — if threat level rises, player decides: keep going or pull back?

**Success criteria:**
- Pattern identification = high score
- Appropriate risk calibration = high score
- Speed balanced with accuracy = bonus

**Phase transition:** ORACLE says *"Vault cracked. Data extracted. Now we need to get out — security is aware."*

---

### Phase 3: Escape

**Setting:** A building floor plan with multiple exit routes.

**Visual:** Map view showing 2-3 escape paths with risk/reward indicators. Timer is prominent and urgent.

**ORACLE's opening:** *"Security is converging. I see three routes: the main corridor — fast but exposed. The service tunnel — slower but hidden. The rooftop — risky but they won't expect it. We have [X] seconds. Your call."*

**Decision points:**
1. **Choose route** — each has different time cost and risk
2. **React to obstacle** — something blocks the chosen path, split-second reroute decision

**Success criteria:**
- Escaping before timer = high score
- Route choice appropriate to time remaining = bonus
- Calm decision-making under pressure = bonus (detected via emotions)

**Mission end:** Timer hits 0 (fail) or player reaches exit (success). Either way → debrief.

---

### Scenario Scripting Guidelines

Claude generates these scenarios dynamically, but the system prompt should include:
- The 3-phase structure above as a framework
- 2-3 decision templates per phase that Claude can adapt
- Rules for how decision quality maps to score
- Rules for phase transitions (when to advance)
- A personality guide for ORACLE (calm, competent, trusts the player, adapts tone to emotion)

The scenarios should feel **procedurally fresh** each playthrough — Claude can vary the specific options, complications, and dialogue while following the structural template.

---

## 5. Emotion-to-UI Mapping Rules

This is the core of the product. These rules define exactly how the interface changes based on emotional state. Claude uses these rules in its system prompt to generate the right `ui_commands`.

### 5.1 Complexity Mapping

| Emotion State | `complexity` | What Changes |
|--------------|-------------|-------------|
| High stress (>0.6) OR high confusion (>0.5) | `"simplified"` | Options reduce (3→2), non-essential panels hidden, larger text, clearer labels, more whitespace |
| Moderate / mixed signals | `"standard"` | Default balanced layout, all core elements visible |
| High focus (>0.6) AND low stress (<0.3) | `"full"` | All panels visible, bonus options appear, detailed data overlays, smaller dense text |

### 5.2 Color Mood Mapping

| Emotion State | `color_mood` | Visual Effect |
|--------------|-------------|--------------|
| High stress OR rising stress trend | `"calm"` | Blues and greens dominate, lower contrast, softer edges, reduced visual noise |
| Neutral / balanced | `"neutral"` | Default color scheme — dark theme with moderate contrast |
| High focus OR timer < 60s | `"intense"` | Reds and oranges accent, higher contrast, sharper edges, energizing |

### 5.3 ORACLE Voice Mapping

| Emotion State | `voice_style` | How ORACLE Sounds |
|--------------|--------------|-------------------|
| High stress (>0.6) | `"calm_reassuring"` | Slower pace, softer tone, more pauses, reassuring language |
| High focus (>0.6) | `"direct_fast"` | Quicker pace, confident and concise, less hand-holding |
| Timer < 60 seconds | `"urgent"` | Heightened energy, shorter sentences, time-aware language |
| Default / mixed | `"neutral"` | Balanced pace and tone |

### 5.4 Guidance Level Mapping

| Emotion State | `guidance_level` | ORACLE's Behavior |
|--------------|-----------------|-------------------|
| High confidence (>0.5) + high focus (>0.5) | `"none"` | ORACLE presents raw data, player decides alone |
| Moderate confidence, low stress | `"low"` | Subtle hints embedded in ORACLE's dialogue |
| Rising stress, moderate confusion | `"medium"` | ORACLE suggests a preference: "I'd lean toward..." |
| High stress (>0.6) OR high confusion (>0.5) | `"high"` | ORACLE actively recommends, UI highlights the suggestion |

### 5.5 Panel Visibility Mapping

| Complexity Level | Panels Shown | Panels Hidden |
|-----------------|-------------|--------------|
| `"simplified"` | `main` only | `stats`, `radar`, `comms` all hidden |
| `"standard"` | `main`, `stats` | `radar`, `comms` hidden |
| `"full"` | `main`, `stats`, `radar`, `comms` | Nothing hidden |

### 5.6 Option Highlighting

When `guidance_level` is `"high"`, ORACLE marks its recommended option with `highlighted: true`. The frontend should visually emphasize this option (glow effect, slightly larger, subtle pulse animation) to guide stressed users toward a good decision without removing their agency.

### 5.7 Transition Smoothness

UI changes should **never be jarring**. All transitions between states should use:
- **CSS transitions** (300-500ms) for color changes
- **Fade in/out** (200ms) for panel visibility
- **Smooth resize** for layout complexity changes
- The emotion data is already smoothed via `avg_stress_30s` (30-second rolling average) to prevent flickering from momentary expression changes

---

## 6. Debrief Screen Specification

The debrief screen is the **demo closer** — the most important screen for judge impressions. It shows the user their own emotional journey through the mission.

### 6.1 Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Mission Debrief — Your Emotional Journey    Score: 87/100   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  STRESS ─┐                                                   │
│           │     ╱╲        ╱╲                                 │
│           │    ╱  ╲  ●   ╱  ╲                                │
│           │   ╱    ╲╱ ╲ ╱    ╲                               │
│           │  ╱    ●     ●     ╲     ╱╲                       │
│           │ ╱                  ╲   ╱  ╲                      │
│  CALM  ───┘╱                    ╲_╱    ╲____                 │
│           │                                                   │
│           └───────────┬──────────┬──────────┬───             │
│                  INFILTRATE    VAULT     ESCAPE               │
│                                                              │
│  ● = UI adapted    (hover/tap for details)                   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Peak Stress   │ │ Most Focused │ │ Total UI Adaptations │ │
│  │ Vault phase   │ │ Escape phase │ │ 7 changes triggered  │ │
│  │ 2:41 left     │ │ route select │ │                      │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ What worked: You stayed calm during infiltration.      │  │
│  │ What stressed you: Vault phase time pressure.          │  │
│  │ Best moment: Decisive route selection under pressure.  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  "Same pattern applies to surgical guidance, crisis          │
│   response, education, and adaptive content platforms."      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Data Source

The debrief reads **Contract 4 entries** from Redis — a sorted set of emotion readings taken every ~1 second during the mission. Each entry contains:
- Timestamp
- Phase
- Stress score (Y-axis)
- Focus score (secondary)
- Adaptation event (if any)

### 6.3 Visual Elements

**Emotion curve:** Primary line chart showing stress over time. X-axis = mission duration. Y-axis = stress level (0 = calm, 1 = stressed). Color gradient from green (calm) to red (stressed).

**Phase boundaries:** Vertical dashed lines separating infiltrate/vault/escape, labeled.

**Adaptation markers:** Colored dots on the curve at moments where the UI adapted. On hover/tap, show what changed: "UI simplified", "Voice calmed", "Options expanded", "Full dashboard". These are the `adaptation` field from Contract 4.

**Summary cards:** 3 cards below the graph:
- Peak Stress (when and what phase)
- Most Focused (when and what phase)
- Total UI Adaptations (count of non-null adaptation entries)

**ORACLE summary:** A brief text analysis of the user's emotional journey. This can be generated by Claude from the timeline data — e.g., "You stayed calm during infiltration but stress peaked during the vault. Your decisive escape route selection showed strong focus under pressure."

**Vision statement:** A closing line about broader applications: *"This same emotion-adaptive pattern applies to surgical guidance, crisis response, education, and adaptive content platforms."*

### 6.4 Implementation Notes

- Use **Recharts** or **D3** for the emotion curve
- Smooth the curve slightly (rolling average over 3 data points) for visual polish
- Animate the curve drawing left-to-right on page load (1-2 seconds)
- Adaptation markers should have a subtle pulse animation
- The summary text can be a second Claude call with the timeline data, or pre-generated from the last Contract 3

---

## 7. Component Specifications

### Component A: Tavus CVI + Emotion Extraction
**Tech: Tavus CVI API**

| Responsibility | Details |
|---------------|---------|
| CVI session setup | Create a Tavus CVI conversation with ORACLE persona (name, voice, appearance) |
| Avatar embedding | Embed CVI video widget in the frontend — ORACLE's face appears here |
| Emotion extraction | Pull emotion scores from CVI session in real time → parse into Contract 1 |
| STT handling | When CVI detects user speech → extract text → forward to Component D |
| TTS handling | When Component D sends ORACLE's response text → feed to CVI → avatar speaks |
| Error handling | No face detected, mic denied, CVI timeout → graceful fallback |

**Output:** Contract 1 (every ~1s) → Component D
**Receives:** ORACLE response text ← Component D
**Forwards:** Player speech text → Component D

**Fallback:** If CVI is too complex → Raven-1 (emotion only) + Web Speech API (browser STT) + browser TTS. Same contract formats.

---

### Component B: AI Brain (ORACLE)
**Tech: Claude API · Structured Output**

| Responsibility | Details |
|---------------|---------|
| System prompt | Define ORACLE's personality, mission context, all emotion-to-UI mapping rules from Section 5 |
| Emotion profiling | Receive raw emotion scores + trend → reason about user's cognitive state → decide adaptation |
| Response generation | Generate ORACLE's dialogue + UI commands + game state updates |
| Structured output | Must return exact Contract 3 JSON format every single time — no exceptions |
| Scenario scripts | 3 phases × 2-3 decision points each. Claude adapts within the structural template. |

**Receives:** Contract 2 ← Component D
**Output:** Contract 3 → Component D

**System prompt must include:**
- ORACLE's personality (calm, competent, trusts the player, never condescending)
- The complete emotion-to-UI mapping rules (Section 5)
- Phase structure and scenario templates (Section 4)
- Strict Contract 3 JSON output format with examples
- Instruction to use chain-of-thought reasoning about the user's emotional state before deciding adaptations
- Rule: never act without the player's call. Present options, recommend if needed, but player decides.

---

### Component C: Adaptive Frontend
**Tech: React · CopilotKit · CSS**

| Responsibility | Details |
|---------------|---------|
| Phase screens | 3 screens (infiltrate, vault, escape) — each with simplified/standard/full variants |
| Adaptive rendering | Switch variants based on `ui_commands.complexity` from Contract 3 |
| Color system | CSS variables that shift based on `ui_commands.color_mood` |
| Panel management | Show/hide panels based on `ui_commands.panels_visible` |
| Option rendering | Dynamic buttons/cards from `ui_commands.options` array |
| Timer | Countdown display, color shifts as time drops, pulsing when <60s |
| CopilotKit | Integrate generative UI — Claude dynamically decides which components render |
| Tavus embed | Include CVI avatar window in the layout (Component A provides the widget) |
| Debrief | Fetch Contract 4 from Redis API → render emotion curve + markers (Section 6) |
| Transitions | All UI changes smooth — 300-500ms CSS transitions, fade in/out for panels |

**Receives:** Contract 3 UI commands ← Component D (via WebSocket)
**Reads:** Contract 4 timeline ← Redis (via Component D's API)

**Screen layout concept:**
```
┌────────────────────────────────────────────┐
│  ┌──────────┐    ┌─────────────────────┐   │
│  │ ORACLE   │    │   MISSION SCREEN    │   │
│  │ avatar   │    │   (phase content)   │   │
│  │ (Tavus)  │    │                     │   │
│  │          │    │   [options/grid/     │   │
│  │          │    │    map content]      │   │
│  └──────────┘    │                     │   │
│                  └─────────────────────┘   │
│  ┌────────┐ ┌────────┐ ┌────────┐         │
│  │ stats  │ │ radar  │ │ comms  │  ⏱ 3:22  │
│  │ panel  │ │ panel  │ │ panel  │         │
│  └────────┘ └────────┘ └────────┘         │
│  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░ emotion indicator    │
└────────────────────────────────────────────┘
```

In `"simplified"` mode, only the mission screen + ORACLE avatar remain. Everything else fades out.

---

### Component D: Backend + Integration
**Tech: FastAPI · WebSocket · Redis**

| Responsibility | Details |
|---------------|---------|
| FastAPI server | WebSocket endpoints for Component A (emotion + voice) and Component C (UI commands) |
| Orchestration | Receive emotion + voice → build Contract 2 → call Claude → route Contract 3 to A (voice) and C (UI) |
| Game state | Track phase, timer, score, conversation history. Advance phases when Contract 3 says so. |
| Timer | Server-side 5-minute countdown. Broadcast `time_remaining` to frontend every second. |
| Redis writes | Store Contract 4 entries every ~1 second |
| Redis reads | Expose `GET /api/timeline/{session_id}` for debrief screen |
| Emotion processing | Compute `trend` (from last 5 readings) and `avg_stress_30s` (rolling 30s average) before sending to Claude |
| Phase transitions | When `advance_phase: true` → update phase, reset conversation history, notify frontend |
| Session management | Create unique session ID per game. Clean up on game end. |

**Receives:** Contract 1 + player text ← Component A · Contract 3 ← Component B
**Sends:** Contract 2 → Component B · Contract 3 → Component C · response text → Component A
**Stores:** Contract 4 → Redis

**WebSocket message types (to keep channels clean):**

```json
// Frontend → Backend
{ "type": "player_speech", "text": "I choose node A" }
{ "type": "emotion_data", "data": { /* Contract 1 */ } }

// Backend → Frontend
{ "type": "ui_update", "data": { /* Contract 3 ui_commands */ } }
{ "type": "timer_tick", "time_remaining": 182 }
{ "type": "phase_change", "phase": "vault" }
{ "type": "game_end", "final_score": 87 }
```

---

## 8. Data Contracts

*(See README.md for the full JSON schemas with field-level definitions. Summary below.)*

| Contract | Route | Frequency | Purpose |
|----------|-------|-----------|---------|
| **Contract 1** | A → D | Every ~1s | Emotion scores from Tavus (stress, focus, confusion, confidence, neutral) |
| **Contract 2** | D → B | Per turn | Full context for Claude: game state + emotion snapshot + player input + history |
| **Contract 3** | B → D → A,C | Per turn | ORACLE's response text + voice style + UI commands + game updates |
| **Contract 4** | D → Redis | Every ~1s | Timestamped emotion entry for the debrief timeline |

---

## 9. Tech Stack & Resources

### Core Technologies

| Tech | Version/Docs | Used For |
|------|-------------|----------|
| **Tavus CVI** | [tavus.io/developer](https://www.tavus.io) · [CVI Docs](https://docs.tavus.io) | Avatar, emotion detection, STT, TTS |
| **Claude API** | [docs.anthropic.com](https://docs.anthropic.com) · Model: `claude-sonnet-4-20250514` | ORACLE reasoning, structured output |
| **CopilotKit** | [copilotkit.ai/docs](https://www.copilotkit.ai/docs) | Generative UI, dynamic component rendering |
| **Redis** | [redis.io/docs](https://redis.io/docs) | Sorted sets for timeline, state caching |
| **FastAPI** | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) | Backend server, WebSocket support |
| **React** | 18+ | Frontend framework |
| **WebSocket** | FastAPI native | Real-time communication |

### Frontend Libraries (suggestions)

| Library | Purpose |
|---------|---------|
| Recharts or D3 | Debrief emotion curve visualization |
| Framer Motion or CSS transitions | Smooth UI state transitions |
| Tailwind CSS | Rapid styling with CSS variable theming |

### Environment Variables

```
ANTHROPIC_API_KEY=     # Claude API key (provided at hackathon)
TAVUS_API_KEY=         # Tavus API key (provided at hackathon)
REDIS_URL=             # redis://localhost:6379 or hosted
```

---

## 10. Demo Script

The demo is **2 minutes**. The judge IS the user — they don't watch a presentation, they experience it.

### 10.1 Hook (0:00 – 0:20)
- Judge sits at the laptop
- Webcam activates, ORACLE's face appears
- Team member says: *"What if AI could see how you feel and reshape the entire screen around your emotional state? Try it yourself."*
- Judge clicks "Begin Mission"

### 10.2 Live Play (0:20 – 1:30)
- Compressed 90-second mission (shortened timer for demo)
- Judge speaks to ORACLE, makes decisions
- **Key moment to point out:** "Notice how the screen just simplified when you looked stressed" or "See how ORACLE's tone changed when you were focused"
- Let the judge experience at least 2 visible UI adaptations

### 10.3 Debrief + Vision (1:30 – 2:00)
- Debrief screen loads with THEIR emotional journey
- Point out: "These dots are moments the AI adapted to your specific emotional state"
- Closing: *"This same emotion-adaptive pattern applies to surgical guidance, crisis response, education, and content platforms. The interface reads you and reshapes itself."*

### 10.4 Demo Preparation Checklist
- [ ] Compressed timer mode (90 seconds instead of 5 minutes)
- [ ] Pre-tested with webcam in the venue lighting
- [ ] Fallback: if Tavus CVI fails, emotion slider + browser TTS ready
- [ ] One team member assigned to narrate, one to handle tech issues
- [ ] Practice the demo at least 3 times before judging

---

## 11. Build Plan

### Friday Evening (Pre-Build)

| Time | Activity |
|------|----------|
| 5:00 – 6:00 PM | Team sync: walk through architecture, pick components, agree on contracts |
| 6:00 – 10:00 PM | Everyone builds their component independently using mock data |

### Saturday (Hackathon Day)

| Time | Activity |
|------|----------|
| 9:00 – 10:00 AM | Setup: repo, API keys, environment, quick check-in |
| 10:00 AM – 2:00 PM | Integration: connect components, real API calls, end-to-end data flow |
| 2:00 – 5:00 PM | Fine-tuning: emotion thresholds, UI transitions, ORACLE prompt quality, edge cases |
| 5:00 – 7:00 PM | Demo preparation: compressed timer mode, rehearsal, fallback testing, pitch script |
| 7:30 PM | Demo time 🚀 |

### Key Milestones

| Milestone | Target Time | What It Means |
|-----------|-------------|---------------|
| Components talk to each other | Sat 12:00 PM | Mock data flows end-to-end through WebSocket |
| Emotion → UI change visible | Sat 1:00 PM | Changing emotion input produces a visible screen change |
| Full loop working | Sat 3:00 PM | Voice in → Claude → voice out + UI change, with real Tavus |
| Debrief renders real data | Sat 4:00 PM | Timeline shows actual emotion readings from a test run |
| Demo rehearsed 3x | Sat 6:30 PM | Confident 2-minute walkthrough with no crashes |

---

## Appendix: Quick Reference Card

**One-sentence summary:** Your face controls the screen — an AI partner adapts its voice, the layout, and the complexity of the interface based on your emotional state in real time.

**The innovation:** Emotional state as a UI input device.

**The demo killer:** Judge plays a 90-second mission, then sees their OWN emotional journey visualized on the debrief screen.

**The broader story:** The same pattern applies to surgical guidance, crisis response, adaptive education, and content platforms.

---

*SPECTRA — AI Interfaces Hackathon with Claude · Feb 21, 2026 · Betaworks NYC*
