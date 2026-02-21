import { Timer } from "../components/Timer";
import type { SpectraState } from "../adaptive/types";
import { StatsPanel } from "./panels/StatsPanel";
import { RadarPanel } from "./panels/RadarPanel";
import { CommsPanel } from "./panels/CommsPanel";

export function PhaseFrame({
  state,
  children,
}: {
  state: SpectraState;
  children: React.ReactNode;
}) {
  const panels = new Set(state.ui.panels_visible);

  const panelClass = (name: "stats" | "radar" | "comms") =>
    `fade ${panels.has(name) ? "visiblePanel" : "hiddenPanel"}`;

  return (
    <div style={{ padding: 18, display: "grid", gap: 14, minHeight: "100vh" }}>
      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 14 }}>
        {/* ORACLE tile (Tavus embed later) */}
        <div className="card" style={{ padding: 14, minHeight: 180 }}>
          <div style={{ fontWeight: 800 }}>ORACLE</div>
          <div style={{ color: "var(--muted)", marginTop: 8 }}>
            Tavus embed goes here
          </div>
        </div>

        <div className="card" style={{ padding: 14, display: "grid", gap: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>PHASE</div>
              <div style={{ fontSize: 20, fontWeight: 900, textTransform: "capitalize" }}>{state.phase}</div>
            </div>
            <Timer seconds={state.timeRemaining} />
          </div>
          {children}
        </div>
      </div>

      {/* Panels row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
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