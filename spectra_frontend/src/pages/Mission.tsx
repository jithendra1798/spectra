import { useMemo, useReducer, useEffect, useRef, useState, useCallback } from "react";
import { useParams, useSearchParams, useNavigate, useLocation } from "react-router-dom";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";

import "../adaptive/theme.css";
import { initState, reduce } from "../adaptive/uiReducer";
import { useSpectraSocket } from "../adaptive/useSpectraSocket";
import { PhaseFrame } from "../phases/PhaseFrame";
import { Infiltrate } from "../phases/Infiltrate";
import { Vault } from "../phases/Vault";
import { Escape } from "../phases/Escape";
import { DemoControls } from "../components/DemoControls";
import { AdaptationBanner } from "../components/AdaptationBanner";
import { resetTimeline } from "../adaptive/timelineStore";

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:8000";

export function Mission() {
  const { sessionId = "demo" } = useParams();
  const [search] = useSearchParams();
  const demoMode = search.get("demo") === "1";
  const nav = useNavigate();
  const location = useLocation();
  const tavusUrl = (location.state as any)?.tavusUrl as string | undefined;

  const [state, dispatch] = useReducer(reduce as any, sessionId, initState);
  const { sendPlayerSpeech, sendEmotion } = useSpectraSocket({ sessionId, dispatch, demoMode });

  // ── Session start: triggered when Tavus iframe loads (real mode) ─────────────
  const sessionStarted = useRef(false);

  const startSession = useCallback(async () => {
    if (demoMode || sessionStarted.current) return;
    sessionStarted.current = true;
    try {
      const res = await fetch(`${API_BASE}/api/session/${sessionId}/start`, { method: "POST" });
      if (!res.ok) console.error("[Mission] session start failed:", res.status);
      else console.log("[Mission] session started after Tavus loaded");
    } catch (e) {
      console.error("[Mission] session start error:", e);
    }
  }, [sessionId, demoMode]);

  // If there's no Tavus URL (offline / no API key), start immediately on mount
  useEffect(() => {
    if (demoMode) return;
    if (!tavusUrl) {
      // No Tavus — start timer directly
      startSession();
    }
  }, [demoMode, tavusUrl, startSession]);

  // ── Demo timer ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!demoMode) return;
    const id = window.setInterval(() => {
      dispatch({ type: "timer_tick", time_remaining: Math.max(0, state.timeRemaining - 1) });
    }, 1000);
    return () => window.clearInterval(id);
  }, [demoMode, state.timeRemaining]);

  useEffect(() => {
    if (demoMode) resetTimeline(sessionId);
  }, [demoMode, sessionId]);

  useEffect(() => {
    if (demoMode && state.timeRemaining === 0) {
      dispatch({ type: "game_end", final_score: 87 });
    }
  }, [demoMode, state.timeRemaining]);

  // ── Navigate to debrief when game ends ──────────────────────────────────────
  useEffect(() => {
    if (!state.gameOver) return;
    const t = setTimeout(() => nav(`/debrief/${sessionId}`), 1500);
    return () => clearTimeout(t);
  }, [state.gameOver, sessionId, nav]);

  // ── Player pick handler ──────────────────────────────────────────────────────
  const onPick = (id: string) => {
    dispatch({ type: "oracle_said", text: `You chose option ${id}`, voice_style: "neutral" });
    sendPlayerSpeech(`I choose option ${id}`);
  };

  // ── Phase content ────────────────────────────────────────────────────────────
  const phaseView = useMemo(() => {
    if (state.phase === "vault") return <Vault state={state} onPick={onPick} />;
    if (state.phase === "escape") return <Escape state={state} onPick={onPick} />;
    return <Infiltrate state={state} onPick={onPick} />;
  }, [state.phase, state.ui, state.timeRemaining]);

  // ── CopilotKit: readable state ───────────────────────────────────────────────
  useCopilotReadable({
    description: "Current SPECTRA mission state — phase, timer, and UI complexity driven by player emotions",
    value: {
      phase: state.phase,
      timeRemaining: state.timeRemaining,
      uiComplexity: state.ui.complexity,
      colorMood: state.ui.color_mood,
      guidanceLevel: state.ui.guidance_level,
      connected: state.connected,
    },
  });

  // ── CopilotKit: generative UI action ─────────────────────────────────────────
  const [adaptation, setAdaptation] = useState<{ reason: string; adaptationType: string } | null>(null);

  useCopilotAction({
    name: "explainUIAdaptation",
    description:
      "Called when the mission interface adapts in real-time based on the player's emotional state. " +
      "Generates a one-sentence ORACLE explanation of why the UI changed.",
    parameters: [
      {
        name: "reason",
        type: "string",
        description:
          "One sentence in ORACLE's voice explaining why the UI adapted " +
          "(e.g. 'You looked stressed, so I cleared the noise.').",
        required: true,
      },
      {
        name: "adaptationType",
        type: "string",
        description:
          "Type of adaptation: 'simplified' (stress high), 'expanded' (focus high), " +
          "'calmed' (color mood calmed), or 'intensified' (focus peak / timer low).",
        required: true,
      },
    ],
    handler: async ({ reason, adaptationType }) => {
      setAdaptation({ reason, adaptationType });
      setTimeout(() => setAdaptation(null), 5000);
      return "adaptation explained";
    },
    render: ({ status, args }: any) => (
      <div
        style={{
          padding: "8px 12px",
          borderRadius: 8,
          background: "rgba(125, 211, 252, 0.08)",
          border: "1px solid rgba(125, 211, 252, 0.2)",
          fontSize: 13,
        }}
      >
        {status === "inProgress" ? (
          <span style={{ opacity: 0.6 }}>Adapting interface...</span>
        ) : (
          <>
            <span style={{ fontWeight: 700, marginRight: 6 }}>ORACLE:</span>
            {args?.reason}
          </>
        )}
      </div>
    ),
  });

  // ── Emotion simulator (real mode only) ───────────────────────────────────────
  const phaseRef = useRef(state.phase);
  phaseRef.current = state.phase;
  const timeRef = useRef(state.timeRemaining);
  timeRef.current = state.timeRemaining;
  const sendEmotionRef = useRef(sendEmotion);
  sendEmotionRef.current = sendEmotion;

  useEffect(() => {
    if (demoMode) return;
    const id = window.setInterval(() => {
      const t = timeRef.current;
      const phase = phaseRef.current;
      const base = phase === "vault" ? 0.52 : phase === "escape" ? 0.62 : 0.32;
      const urgency = t < 60 ? 0.25 : t < 120 ? 0.12 : 0;
      const noise = (Math.random() - 0.5) * 0.18;
      const stress = Math.max(0, Math.min(1, base + urgency + noise));
      const focus = Math.max(0, Math.min(1, 0.85 - stress + (Math.random() - 0.5) * 0.1));
      const confusion = Math.max(0, stress * 0.45 + Math.random() * 0.1);
      const confidence = Math.max(0, focus - 0.1);
      sendEmotionRef.current({
        timestamp: Date.now(),
        emotions: { stress, focus, confusion, confidence, neutral: 0.1 },
        dominant: stress > 0.6 ? "stress" : focus > 0.5 ? "focus" : "neutral",
        face_detected: true,
      });
    }, 2000);
    return () => window.clearInterval(id);
  }, [demoMode]);

  // ── Auto-show adaptation banner on complexity change (no CopilotKit dependency) ─
  const prevComplexity = useRef(state.ui.complexity);
  const isFirstRender = useRef(true);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      prevComplexity.current = state.ui.complexity;
      return;
    }
    if (state.ui.complexity === prevComplexity.current) return;
    const prev = prevComplexity.current;
    prevComplexity.current = state.ui.complexity;

    // Show adaptation banner directly (reliable, no Claude round-trip needed)
    const complexity = state.ui.complexity;
    let reason = "Interface recalibrated.";
    let adaptationType = complexity;
    if (complexity === "simplified" && prev !== "simplified") {
      reason = "You looked stressed — I cleared the noise to focus on what matters.";
      adaptationType = "simplified";
    } else if (complexity === "full") {
      reason = "You're in the zone — showing the full mission data.";
      adaptationType = "expanded";
    } else if (complexity === "standard") {
      reason = "Recalibrating to standard operational mode.";
      adaptationType = "standard";
    }
    setAdaptation({ reason, adaptationType });
    setTimeout(() => setAdaptation(null), 5000);
  }, [state.ui.complexity]);

  // ── Render ────────────────────────────────────────────────────────────────────
  const mood = state.ui.color_mood;

  return (
    <div data-mood={mood}>
      {/* Floating adaptation banner */}
      {adaptation && (
        <AdaptationBanner
          reason={adaptation.reason}
          adaptationType={adaptation.adaptationType}
          onDismiss={() => setAdaptation(null)}
        />
      )}

      {/* Demo-only controls */}
      {demoMode && (
        <>
          <button
            onClick={() => nav(`/debrief/${sessionId}`)}
            style={{
              position: "fixed",
              right: 16,
              bottom: 72,
              zIndex: 9999,
              padding: "10px 12px",
              borderRadius: 12,
              border: "1px solid var(--border)",
              background: "var(--panel)",
              color: "var(--text)",
              cursor: "pointer",
              fontWeight: 800,
            }}
          >
            Go Debrief
          </button>
          <DemoControls
            dispatchEmotion={(e) => dispatch({ type: "emotion_update", data: e })}
            setPhase={(p) => dispatch({ type: "phase_change", phase: p })}
          />
        </>
      )}

      {/* Mission screen — onTavusLoad starts the session timer */}
      <PhaseFrame state={state} tavusUrl={tavusUrl} onTavusLoad={startSession}>
        {phaseView}
      </PhaseFrame>

      {/* CopilotKit popup — ORACLE chat */}
      <CopilotPopup
        labels={{
          title: "ORACLE",
          initial: "Ask me anything about the mission.",
        }}
      />
    </div>
  );
}
