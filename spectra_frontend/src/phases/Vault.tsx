import { OptionGrid } from "../components/OptionGrid";
import type { SpectraState } from "../adaptive/types";

const HEX_LINES = ["7F A3 1C 4B", "9D 2E 44 7A", "C0 FF EE 12"];

export function Vault({
  state,
  onPick,
}: {
  state: SpectraState;
  onPick: (id: string) => void;
}) {
  const c = state.ui.complexity;
  const frags = c === "simplified" ? 2 : c === "standard" ? 4 : 6;
  const cols = c === "full" ? 3 : 2;

  return (
    <>
      <div className="phase-header">
        <span className="phase-title">Vault</span>
        <span className="phase-instruction">
          {c === "simplified"
            ? "Vault mode: keep it simple. Pick the safer move."
            : c === "standard"
            ? "Identify the pattern. Choose a decrypt path."
            : "Full dashboard active. Watch threat + progress. Decide fast."}
        </span>
      </div>

      <div className="card" style={{ padding: 12 }}>
        <div className="tac-label" style={{ marginBottom: 8 }}>Cipher Fragments</div>
        <div className="cipher-grid" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {Array.from({ length: frags }).map((_, i) => (
            <div key={i} className="cipher-block">
              <div className="cipher-id">FRAG-{String(i + 1).padStart(2, "0")}</div>
              <div className="cipher-text">
                {HEX_LINES.map((l, j) => (
                  <div key={j}>{l.slice(0, -1) + String(i)}</div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {c === "full" && (
          <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
            <div
              style={{
                flex: 1,
                padding: "8px 10px",
                background: "var(--bg-dark)",
                borderRadius: 6,
                border: "1px solid var(--border)",
              }}
            >
              <div className="tac-label">Threat Level</div>
              <div style={{ fontWeight: 900, color: "var(--danger)", fontSize: 15, marginTop: 3 }}>
                Rising
              </div>
            </div>
            <div
              style={{
                flex: 1,
                padding: "8px 10px",
                background: "var(--bg-dark)",
                borderRadius: 6,
                border: "1px solid var(--border)",
              }}
            >
              <div className="tac-label">Decrypt</div>
              <div style={{ fontWeight: 900, color: "var(--ok)", fontSize: 15, marginTop: 3 }}>
                62%
              </div>
              <div className="tac-bar" style={{ marginTop: 4 }}>
                <div className="tac-bar-fill" style={{ width: "62%" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      <OptionGrid options={state.ui.options} onPick={onPick} />
    </>
  );
}
