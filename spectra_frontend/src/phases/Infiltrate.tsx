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
  const cols = c === "simplified" ? 3 : c === "standard" ? 4 : 5;
  const count = c === "simplified" ? 6 : c === "standard" ? 12 : 20;

  return (
    <>
      <div className="phase-header">
        <span className="phase-title">Infiltrate</span>
        <span className="phase-instruction">
          {c === "simplified"
            ? "Pick the weakest entry point. ORACLE will guide you."
            : c === "standard"
            ? "Choose an entry point based on signal patterns."
            : "Analyze the network grid. Use all panels. Pick the optimal vector."}
        </span>
      </div>

      {/* Node grid */}
      <div
        className="node-grid card"
        style={{ padding: 12, gridTemplateColumns: `repeat(${cols}, 1fr)` }}
      >
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="node-cell">
            <div className="node-dot" />
            {`N-${String.fromCharCode(65 + (i % 26))}${Math.floor(i / 26) || ""}`}
          </div>
        ))}
      </div>

      <OptionGrid options={state.ui.options} onPick={onPick} />
    </>
  );
}
