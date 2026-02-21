import { OptionGrid } from "../components/OptionGrid";
import type { SpectraState } from "../adaptive/types";

export function Vault({
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
          ? "Vault mode: keep it simple. Pick the safer move."
          : c === "standard"
          ? "Vault mode: identify the pattern and choose a decrypt path."
          : "Vault mode: full dashboard. Watch threat + progress and decide fast."}
      </div>

      <div className="card" style={{ padding: 12, display: "grid", gap: 10 }}>
        <div style={{ fontWeight: 900 }}>Cipher Fragments</div>

        <div
          style={{
            display: "grid",
            gap: 10,
            gridTemplateColumns: c === "full" ? "repeat(3, 1fr)" : "repeat(2, 1fr)",
          }}
        >
          {Array.from({ length: c === "simplified" ? 2 : c === "standard" ? 4 : 6 }).map((_, i) => (
            <div
              key={i}
              style={{
                padding: 12,
                borderRadius: 14,
                border: "1px solid var(--border)",
                background: "rgba(0,0,0,0.18)",
                color: "var(--muted)",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                fontSize: 12,
                lineHeight: 1.4,
              }}
            >
              {`7F A3 1C ${i}B\n9D 2E 44 ${i}A\nC0 FF EE ${i}7`}
            </div>
          ))}
        </div>

        {c === "full" ? (
          <div style={{ display: "flex", gap: 10, marginTop: 6 }}>
            <div className="card" style={{ padding: 10, flex: 1 }}>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>Threat</div>
              <div style={{ fontWeight: 900, color: "var(--danger)" }}>Rising</div>
            </div>
            <div className="card" style={{ padding: 10, flex: 1 }}>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>Decrypt Progress</div>
              <div style={{ fontWeight: 900, color: "var(--accent)" }}>62%</div>
            </div>
          </div>
        ) : null}
      </div>

      <OptionGrid options={state.ui.options} onPick={onPick} />
    </div>
  );
}