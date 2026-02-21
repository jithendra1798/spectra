import { useMemo, useReducer, useEffect } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";

// import { CopilotKit } from "@copilotkit/react-core";
// import "@copilotkit/react-ui/styles.css";

import "../adaptive/theme.css";
import { initState, reduce } from "../adaptive/uiReducer";
import { useSpectraSocket } from "../adaptive/useSpectraSocket";
import { PhaseFrame } from "../phases/PhaseFrame";
import { Infiltrate } from "../phases/Infiltrate";
import { DemoControls } from "../components/DemoControls";
import { Vault } from "../phases/Vault";
import { Escape } from "../phases/Escape";
import { resetTimeline } from "../adaptive/timelineStore";

export function Mission() {
  const { sessionId = "demo" } = useParams();
  const [search] = useSearchParams();
  const demoMode = search.get("demo") === "1";

  const [state, dispatch] = useReducer(reduce as any, sessionId, initState);
  const { sendPlayerSpeech } = useSpectraSocket({ sessionId, dispatch, demoMode });

  const mood = state.ui.color_mood;

  useEffect(() => {
  if (!demoMode) return;

  const id = window.setInterval(() => {
    dispatch({
      type: "timer_tick",
      time_remaining: Math.max(0, state.timeRemaining - 1),
    });
  }, 1000);

  return () => window.clearInterval(id);
  // we only want this to depend on demoMode + timeRemaining
}, [demoMode, state.timeRemaining]);

useEffect(() => {
  if (!demoMode) return;
  resetTimeline(sessionId);
}, [demoMode, sessionId]);

useEffect(() => {
  if (!demoMode) return;
  if (state.timeRemaining !== 0) return;

  dispatch({ type: "game_end", final_score: 87 });
}, [demoMode, state.timeRemaining]);

//   const phaseView = useMemo(() => {
//     // Start with infiltrate only; later switch on state.phase
//     return (
//       <Infiltrate
//         state={state}
//         onPick={(id) => {
//           dispatch({ type: "oracle_said", text: `Player picked ${id}`, voice_style: "neutral" });
//           sendPlayerSpeech(`I choose option ${id}`);
//         }}
//       />
//     );
//   }, [state, sendPlayerSpeech, dispatch]);

const nav = useNavigate();

// Navigate to debrief when game ends (backend or demo)
useEffect(() => {
  if (!state.gameOver) return;
  const timer = setTimeout(() => nav(`/debrief/${sessionId}`), 1500);
  return () => clearTimeout(timer);
}, [state.gameOver, sessionId, nav]);

const onPick = (id: string) => {
  dispatch({ type: "oracle_said", text: `Player picked ${id}`, voice_style: "neutral" });
  sendPlayerSpeech(`I choose option ${id}`);
};
  const phaseView = useMemo(() => {
    if (state.phase === "vault") return <Vault state={state} onPick={onPick} />;
    if (state.phase === "escape") return <Escape state={state} onPick={onPick} />;
    return <Infiltrate state={state} onPick={onPick} />;
    }, [state.phase, state.ui, state.timeRemaining]);

  return (
    // <CopilotKit runtimeUrl="/api/copilotkit" /* can be unused for MVP */>
    //   <div data-mood={mood}>
    //     <div style={{ color: "white", padding: 20 }}>MISSION LOADED</div>
    //     <PhaseFrame state={state}>{phaseView}</PhaseFrame>
    //   </div>
    // </CopilotKit>
        <div data-mood={mood}>
            {demoMode ? (
            <>
                <button
                onClick={() => nav(`/debrief/${sessionId}`)}
                style={{
                    position: "fixed",
                    right: 16,
                    bottom: 16,
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
            ) : null}

            <PhaseFrame state={state}>{phaseView}</PhaseFrame>
        </div>
    )
}