import { Timer } from "../components/Timer";
import type { SpectraState } from "../adaptive/types";
import { StatsPanel } from "./panels/StatsPanel";
import { RadarPanel } from "./panels/RadarPanel";
import { CommsPanel } from "./panels/CommsPanel";

const PHASE_STEPS: Record<string, string> = {
  infiltrate: "01 / 03",
  vault:      "02 / 03",
  escape:     "03 / 03",
};

export function PhaseFrame({
  state,
  tavusUrl: tavusUrlProp,
  children,
}: {
  state: SpectraState;
  tavusUrl?: string;
  children: React.ReactNode;
}) {
  // Prefer dynamically generated URL from session creation; fall back to env var (demo mode)
  const envUrl = (import.meta as any).env?.VITE_TAVUS_CONVERSATION_URL as string | undefined;
  const tavusUrl = (tavusUrlProp ?? envUrl) || null;

  const panels = new Set(state.ui.panels_visible);
  const panelClass = (name: "stats" | "radar" | "comms") =>
    `fade ${panels.has(name) ? "visiblePanel" : "hiddenPanel"}`;

  return (
    <div className="hud-root" data-mood={state.ui.color_mood ?? "neutral"}>
      {/* ── Top status bar ── */}
      <div className="hud-topbar">
        <div className="hud-logo">SPECTRA</div>

        <div className="hud-phase-indicator">
          <span className="hud-phase-step">{PHASE_STEPS[state.phase] ?? "— / —"}</span>
          <div className="phase-sep" />
          <span className="hud-phase-name">{state.phase}</span>
        </div>

        <div className="hud-topbar-right">
          <Timer seconds={state.timeRemaining} />
          <div
            className={`dot ${state.connected ? "dot-ok" : "dot-danger"}`}
            title={state.connected ? "Connected" : "Offline"}
          />
        </div>
      </div>

      {/* ── Body: oracle sidebar + phase content ── */}
      <div className="hud-body">
        {/* Oracle sidebar */}
        <div className="oracle-sidebar card" style={{ padding: 14 }}>
          <div className="oracle-header">
            <div className="dot dot-ok" />
            <div className="oracle-label">Oracle</div>
          </div>

          <div className="oracle-video">
            {tavusUrl ? (
              <iframe
                title="Tavus CVI"
                src={tavusUrl}
                allow="camera; microphone; autoplay; clipboard-write; display-capture"
              />
            ) : (
              <div className="oracle-offline">
                <div className="oracle-offline-icon">◈</div>
                <span>ORACLE OFFLINE</span>
              </div>
            )}
          </div>

          {state.oracle?.text && (
            <div className="oracle-speech">
              <div className="oracle-speech-label">Last transmission</div>
              {state.oracle.text}
            </div>
          )}
        </div>

        {/* Phase content */}
        <div className="phase-content card" style={{ padding: 16 }}>
          {children}
        </div>
      </div>

      {/* ── Panel strip ── */}
      <div className="hud-panels">
        <div className={panelClass("stats")}>
          <StatsPanel connected={state.connected} />
        </div>
        <div className={panelClass("radar")}>
          <RadarPanel />
        </div>
        <div className={panelClass("comms")}>
          <CommsPanel comms={state.comms} />
        </div>
      </div>
    </div>
  );
}
