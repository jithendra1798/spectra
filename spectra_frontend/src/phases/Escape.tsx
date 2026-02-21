import { OptionGrid } from "../components/OptionGrid";
import type { SpectraState } from "../adaptive/types";

export function Escape({
  state,
  onPick,
}: {
  state: SpectraState;
  onPick: (id: string) => void;
}) {
  const c = state.ui.complexity;
  const urgent = state.timeRemaining <= 60;

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ color: urgent ? "var(--danger)" : "var(--muted)", fontWeight: urgent ? 900 : 600 }}>
        {urgent ? "URGENT: Under 60 seconds. Choose fastest viable route." : "Escape mode: choose a route under pressure."}
      </div>

      <div
        className="card"
        style={{
          padding: 12,
          display: "grid",
          gap: 10,
        }}
      >
        <div style={{ fontWeight: 900 }}>Exit Routes</div>

        <div
          style={{
            display: "grid",
            gap: 10,
            gridTemplateColumns: c === "simplified" ? "1fr" : "repeat(3, 1fr)",
          }}
        >
          {["Main Corridor", "Service Tunnel", "Rooftop"].slice(0, c === "simplified" ? 2 : 3).map((name, i) => (
            <div
              key={name}
              style={{
                padding: 12,
                borderRadius: 14,
                border: "1px solid var(--border)",
                background: "rgba(0,0,0,0.18)",
              }}
            >
              <div style={{ fontWeight: 900 }}>{name}</div>
              <div style={{ color: "var(--muted)", marginTop: 6, fontSize: 13 }}>
                Time: <b style={{ color: "var(--text)" }}>{[18, 28, 22][i]}s</b> · Risk:{" "}
                <b style={{ color: i === 0 ? "var(--danger)" : "var(--accent)" }}>{i === 0 ? "High" : "Medium"}</b>
              </div>
            </div>
          ))}
        </div>
      </div>

      <OptionGrid options={state.ui.options} onPick={onPick} />
    </div>
  );
}