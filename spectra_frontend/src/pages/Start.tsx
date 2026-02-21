import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:8000";

export function Start() {
  const nav = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startMission() {
    setLoading(true);
    setError(null);
    try {
      // 1. Create session
      const createRes = await fetch(`${API_BASE}/api/session/create`, { method: "POST" });
      if (!createRes.ok) throw new Error(`Create failed: ${createRes.status}`);
      const { session_id } = await createRes.json();

      // 2. Start timer
      const startRes = await fetch(`${API_BASE}/api/session/${session_id}/start`, { method: "POST" });
      if (!startRes.ok) throw new Error(`Start failed: ${startRes.status}`);

      // 3. Navigate to mission
      nav(`/mission/${session_id}`);
    } catch (e: any) {
      setError(e.message ?? "Failed to connect to backend");
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ margin: 0, fontSize: 32 }}>SPECTRA</h1>
      <p style={{ color: "var(--muted)", maxWidth: 520 }}>
        Your face controls the screen. Begin a mission and watch the UI adapt.
      </p>

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <button
          onClick={startMission}
          disabled={loading}
          style={{
            padding: "10px 20px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--accent)",
            color: "#000",
            cursor: loading ? "wait" : "pointer",
            fontWeight: 800,
            fontSize: 14,
          }}
        >
          {loading ? "Starting..." : "Begin Mission"}
        </button>

        <Link
          to="/mission/demo?demo=1"
          style={{
            padding: "10px 20px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--panel)",
            color: "var(--text)",
            textDecoration: "none",
            fontWeight: 800,
            fontSize: 14,
          }}
        >
          Demo Mode
        </Link>
      </div>

      {error && (
        <div style={{ marginTop: 12, color: "var(--danger)", fontSize: 13 }}>
          {error}
        </div>
      )}
    </div>
  );
}
