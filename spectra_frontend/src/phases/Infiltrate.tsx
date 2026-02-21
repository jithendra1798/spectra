import { OptionGrid } from "../components/OptionGrid";
import type { SpectraState } from "../adaptive/types";

export function Infiltrate({
  state,
  onPick,
}: {
  state: SpectraState;
  onPick: (id: string) => void;
}) {
  const c = state.ui.complexity;

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ color: "var(--muted)" }}>
        {c === "simplified"
          ? "Pick the weakest entry point. ORACLE will guide you."
          : c === "standard"
          ? "Choose an entry point based on signal patterns."
          : "Analyze the grid. Use panels + comms. Pick the optimal entry point."}
      </div>

      {/* Node grid visual */}
      <div
        className="card"
        style={{
          padding: 12,
          display: "grid",
          gap: 10,
          gridTemplateColumns:
            c === "simplified" ? "repeat(2, 1fr)" : c === "standard" ? "repeat(3, 1fr)" : "repeat(4, 1fr)",
        }}
      >
        {Array.from({ length: c === "simplified" ? 6 : c === "standard" ? 9 : 12 }).map((_, i) => (
          <div
            key={i}
            style={{
              padding: 12,
              borderRadius: 14,
              border: "1px solid var(--border)",
              background: "rgba(0,0,0,0.18)",
              color: "var(--muted)",
              fontWeight: 700,
            }}
          >
            Node {String.fromCharCode(65 + i)}
          </div>
        ))}
      </div>

      {/* Real choices are Contract 3 options */}
      <OptionGrid options={state.ui.options} onPick={onPick} />
    </div>
  );
}