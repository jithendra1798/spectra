export function StatsPanel({ connected }: { connected: boolean }) {
  return (
    <div className="card" style={{ padding: 12 }}>
      <div style={{ fontWeight: 800 }}>Stats</div>
      <div style={{ color: "var(--muted)", marginTop: 6 }}>
        WS: {connected ? "connected" : "offline"}
      </div>
    </div>
  );
}