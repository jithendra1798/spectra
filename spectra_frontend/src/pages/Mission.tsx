import { useMemo, useReducer, useEffect, useRef, useState } from "react";
import { useParams, useSearchParams, useNavigate, useLocation } from "react-router-dom";
import { useCopilotReadable, useCopilotAction, useCopilotChat } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";

import "../adaptive/theme.css";
import { initState, reduce } from "../adaptive/uiReducer";
import { useSpectraSocket } from "../adaptive/useSpectraSocket";
import { PhaseFrame } from "../phases/PhaseFrame";
import { Briefing } from "../phases/Briefing";
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
  const { sendPlayerSpeech } = useSpectraSocket({ sessionId, dispatch, demoMode });

  // ── Briefing gate — skipped in demo mode ────────────────────────────────────
  const [briefingDone, setBriefingDone] = useState(demoMode);

  async function handleReady() {
    await fetch(`${API_BASE}/api/session/${sessionId}/start`, { method: "POST" });
    setBriefingDone(true);
  }

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
    dispatch({ type: "oracle_said", text: `You chose: ${id}`, voice_style: "neutral" });
    sendPlayerSpeech(`I choose option ${id}`);
  };

  // ── Phase content ────────────────────────────────────────────────────────────
  const phaseView = useMemo(() => {
    if (state.phase === "vault") return <Vault state={state} onPick={onPick} />;
    if (state.phase === "escape") return <Escape state={state} onPick={onPick} />;
    return <Infiltrate state={state} onPick={onPick} />;
  }, [state.phase, state.ui, state.timeRemaining]);

  // ── CopilotKit: readable state ───────────────────────────────────────────────
  // Exposes current mission + emotion context to Claude via useCopilotReadable
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
  // Claude calls explainUIAdaptation when the interface changes.
  // handler  → shows AdaptationBanner in the main mission UI
  // render   → shows an inline card in the CopilotPopup chat
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
      console.log("[CopilotKit] explainUIAdaptation fired:", { reason, adaptationType });
      setAdaptation({ reason, adaptationType });
      // Auto-dismiss after 5 seconds
      setTimeout(() => setAdaptation(null), 5000);
      return "adaptation explained";
    },
    // render shows inside the CopilotPopup when the action fires
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

  // ── Auto-trigger explanation on complexity change ─────────────────────────────
  // When the backend drives complexity up/down via WS, we send a message via
  // useCopilotChat so Claude generates an explanation and calls explainUIAdaptation.
  const { sendMessage } = useCopilotChat();
  const prevComplexity = useRef(state.ui.complexity);
  const isFirstRender = useRef(true);

  useEffect(() => {
    console.log("[UI state]", {
      complexity: state.ui.complexity,
      color_mood: state.ui.color_mood,
      guidance: state.ui.guidance_level,
      phase: state.phase,
      connected: state.connected,
    });

    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    if (state.ui.complexity === prevComplexity.current) return;
    prevComplexity.current = state.ui.complexity;

    console.log("[CopilotKit] complexity changed →", state.ui.complexity, "— sending to Claude");
    sendMessage(
      `The mission interface just switched to "${state.ui.complexity}" mode. ` +
        `Phase: ${state.phase}, time left: ${state.timeRemaining}s. ` +
        `Please call explainUIAdaptation with a one-sentence reason.`
    );
  }, [state.ui.complexity]);

  // ── Render ────────────────────────────────────────────────────────────────────
  const mood = state.ui.color_mood;

  return (
    <div data-mood={mood}>
      {/* Floating adaptation banner — generative UI from CopilotKit */}
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

      {/* Mission screen — briefing gate */}
      {briefingDone ? (
        <PhaseFrame state={state} tavusUrl={tavusUrl}>{phaseView}</PhaseFrame>
      ) : (
        <Briefing tavusUrl={tavusUrl ?? null} connected={state.connected} onReady={handleReady} />
      )}

      {/* CopilotKit popup — typed ORACLE chat, also shows explainUIAdaptation renders */}
      <CopilotPopup
        labels={{
          title: "ORACLE",
          initial: "Ask me anything about the mission, or I'll explain what I'm doing.",
        }}
      />
    </div>
  );
}
