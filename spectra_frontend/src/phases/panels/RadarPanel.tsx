export function RadarPanel() {
  return (
    <div className="card" style={{ padding: 12 }}>
      <div className="tac-label" style={{ marginBottom: 8 }}>Threat / Progress</div>
      <div style={{ display: "grid", gap: 10 }}>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "var(--muted)" }}>Threat</span>
            <span style={{ fontSize: 11, color: "var(--danger)", fontFamily: "var(--mono)", fontWeight: 700 }}>34%</span>
          </div>
          <div className="tac-bar">
            <div className="tac-bar-fill" style={{ width: "34%", background: "var(--danger)" }} />
          </div>
        </div>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "var(--muted)" }}>Progress</span>
            <span style={{ fontSize: 11, color: "var(--ok)", fontFamily: "var(--mono)", fontWeight: 700 }}>61%</span>
          </div>
          <div className="tac-bar">
            <div className="tac-bar-fill" style={{ width: "61%", background: "var(--ok)" }} />
          </div>
        </div>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "var(--muted)" }}>Detection</span>
            <span style={{ fontSize: 11, color: "var(--warn)", fontFamily: "var(--mono)", fontWeight: 700 }}>LOW</span>
          </div>
          <div className="tac-bar">
            <div className="tac-bar-fill" style={{ width: "12%", background: "var(--warn)" }} />
          </div>
        </div>
      </div>
    </div>
  );
}
