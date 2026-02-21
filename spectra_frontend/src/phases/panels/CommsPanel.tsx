export function CommsPanel({ comms }: { comms: Array<{ role: string; text: string }> }) {
  return (
    <div className="card" style={{ padding: 12, maxHeight: 200, overflowY: "auto" }}>
      <div className="tac-label" style={{ marginBottom: 8 }}>Comms Log</div>
      {comms.length === 0 ? (
        <div style={{ fontSize: 11, color: "var(--label)", fontFamily: "var(--mono)" }}>
          NO TRANSMISSIONS
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
          {comms.slice(-8).map((m, i) => (
            <div key={i} style={{ fontSize: 12 }}>
              <span
                style={{
                  fontFamily: "var(--mono)",
                  fontSize: 10,
                  color: "var(--accent)",
                  fontWeight: 700,
                  marginRight: 6,
                  letterSpacing: "0.1em",
                }}
              >
                {m.role.toUpperCase()}
              </span>
              <span style={{ color: "var(--muted)" }}>{m.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
