import { OptionGrid } from "../components/OptionGrid";
import type { SpectraState } from "../adaptive/types";

const ROUTES = [
  { name: "Main Corridor",  time: 18, risk: "high"   as const },
  { name: "Service Tunnel", time: 28, risk: "medium" as const },
  { name: "Rooftop",        time: 22, risk: "medium" as const },
];

export function Escape({
  state,
  onPick,
}: {
  state: SpectraState;
  onPick: (id: string) => void;
}) {
  const c = state.ui.complexity;
  const urgent = state.timeRemaining <= 60;
  const visibleRoutes = c === "simplified" ? ROUTES.slice(0, 2) : ROUTES;

  return (
    <>
      <div className="phase-header">
        <span className="phase-title" style={urgent ? { color: "var(--danger)" } : {}}>
          {urgent ? "!!! ESCAPE" : "Escape"}
        </span>
        <span
          className="phase-instruction"
          style={urgent ? { color: "var(--danger)", fontWeight: 700 } : {}}
        >
          {urgent
            ? "CRITICAL — Under 60 seconds. Choose fastest viable route now."
            : "Escape mode: choose a route under pressure."}
        </span>
      </div>

      <div className="card" style={{ padding: 12 }}>
        <div className="tac-label" style={{ marginBottom: 8 }}>Exit Routes</div>
        <div
          style={{
            display: "grid",
            gap: 8,
            gridTemplateColumns: c === "simplified" ? "1fr" : "repeat(3, 1fr)",
          }}
        >
          {visibleRoutes.map((r) => (
            <div key={r.name} className={`route-card risk-${r.risk}`}>
              <div className="route-name">{r.name}</div>
              <div className="route-meta">
                <span>
                  ETA <b style={{ color: "var(--text)" }}>{r.time}s</b>
                </span>
                <span style={{ color: r.risk === "high" ? "var(--danger)" : "var(--warn)" }}>
                  {r.risk.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <OptionGrid options={state.ui.options} onPick={onPick} />
    </>
  );
}
