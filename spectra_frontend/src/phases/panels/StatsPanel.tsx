export function StatsPanel({ connected }: { connected: boolean }) {
  return (
    <div className="card" style={{ padding: 12 }}>
      <div className="tac-label" style={{ marginBottom: 8 }}>System Status</div>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <div className={`dot ${connected ? "dot-ok" : "dot-danger"}`} />
        <span style={{ fontSize: 12, color: connected ? "var(--ok)" : "var(--danger)" }}>
          {connected ? "LINK ACTIVE" : "LINK DOWN"}
        </span>
      </div>
      <div className="tac-divider" />
      <div style={{ display: "grid", gap: 6 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="tac-label">Signal</span>
          <span style={{ color: "var(--ok)", fontFamily: "var(--mono)", fontWeight: 700, fontSize: 11 }}>STRONG</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="tac-label">Encryption</span>
          <span style={{ color: "var(--accent)", fontFamily: "var(--mono)", fontWeight: 700, fontSize: 11 }}>AES-256</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="tac-label">Protocol</span>
          <span style={{ color: "var(--muted)", fontFamily: "var(--mono)", fontWeight: 700, fontSize: 11 }}>SPECTRA/WS</span>
        </div>
      </div>
    </div>
  );
}
