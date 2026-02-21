import type { UiOption } from "../adaptive/types";

export function OptionGrid({
  options,
  onPick,
}: {
  options: UiOption[];
  onPick: (id: string) => void;
}) {
  return (
    <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}>
      {options.map((o) => (
        <button
          key={o.id}
          className={`card ${o.highlighted ? "pulse" : ""}`}
          onClick={() => onPick(o.id)}
          style={{
            padding: 14,
            textAlign: "left",
            cursor: "pointer",
            color: "var(--text)",
            background: "var(--panel)",
          }}
        >
          <div style={{ fontSize: 12, color: "var(--muted)" }}>OPTION</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{o.label}</div>
          {o.highlighted ? (
            <div style={{ marginTop: 8, fontSize: 12, color: "var(--accent)", fontWeight: 700 }}>
              Recommended
            </div>
          ) : null}
        </button>
      ))}
    </div>
  );
}