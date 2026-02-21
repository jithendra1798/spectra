export function CommsPanel({ comms }: { comms: Array<{ role: string; text: string }> }) {
  return (
    <div className="card" style={{ padding: 12, maxHeight: 180, overflow: "auto" }}>
      <div style={{ fontWeight: 800 }}>Comms</div>
      <div style={{ marginTop: 8, display: "grid", gap: 8 }}>
        {comms.slice(-6).map((m, i) => (
          <div key={i} style={{ fontSize: 13, color: "var(--muted)" }}>
            <b style={{ color: "var(--text)" }}>{m.role}:</b> {m.text}
          </div>
        ))}
      </div>
    </div>
  );
}