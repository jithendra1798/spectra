import type { SpectraState, UiCommands, Phase, OracleResponse, EmotionContract1 } from "./types";
import { deriveUiFromEmotion } from "./emotionEngine";
import { addEntry } from "./timelineStore";

type WsMsg =
  | { type: "ui_update"; data: UiCommands }
  | { type: "timer_tick"; time_remaining: number }
  | { type: "phase_change"; phase: Phase }
  | { type: "oracle_said"; text: string; voice_style: OracleResponse["voice_style"] }
  | { type: "connected" }
  | { type: "emotion_update"; data: EmotionContract1 }
  | { type: "disconnected" }
  | { type: "game_end"; final_score: number }
  | { type: "game_state_update"; current_score: number; decisions_made: number; phase: Phase; time_remaining: number };

export const defaultUi: UiCommands = {
  complexity: "standard",
  color_mood: "neutral",
  panels_visible: ["main", "stats"],
  options: [
    { id: "A", label: "Option A" },
    { id: "B", label: "Option B" },
    { id: "C", label: "Option C" },
  ],
  guidance_level: "low",
};

export function initState(sessionId: string): SpectraState {
  return {
    sessionId,
    connected: false,
    phase: "infiltrate",
    timeRemaining: 300,
    currentScore: 0,
    decisionsMade: 0,
    ui: defaultUi,
    comms: [],
  };
}

export function reduce(state: SpectraState, msg: WsMsg): SpectraState {
  console.log(`[reducer] ← ${msg.type}`, msg);
  switch (msg.type) {
    case "connected":
      return { ...state, connected: true };
    case "disconnected":
      return { ...state, connected: false };
    case "timer_tick":
      return { ...state, timeRemaining: msg.time_remaining };
    case "phase_change": {
        // IMPORTANT: when phase changes, refresh options so screens show different options
        const phase = msg.phase;
        const options =
            phase === "infiltrate"
            ? [
                { id: "A", label: "Node A" },
                { id: "B", label: "Node B" },
                { id: "C", label: "Node C" },
                ]
            : phase === "vault"
            ? [
                { id: "FAST", label: "Fast decrypt (risky)" },
                { id: "SAFE", label: "Safe decrypt (slow)" },
                { id: "ABORT", label: "Abort and reroute" },
                ]
            : [
                { id: "CORRIDOR", label: "Main corridor" },
                { id: "TUNNEL", label: "Service tunnel" },
                { id: "ROOF", label: "Rooftop" },
                ];

        return {
            ...state,
            phase,
            comms: [],
            ui: { ...state.ui, options },
        };
        }

        case "game_end": {
        return {
            ...state,
            gameOver: true,
            finalScore: msg.final_score,
            oracle: { text: `Mission ended. Score: ${msg.final_score}`, voice_style: "neutral" as const },
        };
        }
    case "ui_update":
      console.log("[reducer] ui_update — overwriting ui:", {
        prev: { complexity: state.ui.complexity, color_mood: state.ui.color_mood, guidance: state.ui.guidance_level },
        next: { complexity: msg.data.complexity, color_mood: msg.data.color_mood, guidance: msg.data.guidance_level },
        options: msg.data.options,
      });
      return { ...state, ui: msg.data };
    case "emotion_update": {
    const prev = state.ui;
    const nextUi = deriveUiFromEmotion(msg.data, state.ui);
    console.log("[reducer] emotion_update — deriving ui:", {
      stress: msg.data.emotions.stress.toFixed(2),
      focus: msg.data.emotions.focus.toFixed(2),
      confusion: msg.data.emotions.confusion.toFixed(2),
      confidence: msg.data.emotions.confidence.toFixed(2),
      prev_complexity: state.ui.complexity,
      next_complexity: nextUi.complexity,
      prev_mood: state.ui.color_mood,
      next_mood: nextUi.color_mood,
    });

    // detect adaptation event
    let adaptation: string | null = null;
    if (prev.complexity !== nextUi.complexity) {
        adaptation = nextUi.complexity === "simplified" ? "ui_simplified" : "options_expanded";
    } else if (prev.color_mood !== nextUi.color_mood) {
        adaptation = nextUi.color_mood === "calm" ? "voice_calmed" : "full_dashboard";
    }

    addEntry(state.sessionId, {
            t: msg.data.timestamp,
            phase: state.phase,
            stress: msg.data.emotions.stress,
            focus: msg.data.emotions.focus,
            adaptation,
    });

    return { ...state, ui: nextUi };
    }
    case "oracle_said": {
      const oracle = { text: msg.text, voice_style: msg.voice_style };
      return {
        ...state,
        oracle,
        comms: [...state.comms, { role: "oracle", text: msg.text }],
      };
    }
    case "game_state_update":
      return {
        ...state,
        currentScore: msg.current_score,
        decisionsMade: msg.decisions_made,
      };
    default:
      return state;
  }
}