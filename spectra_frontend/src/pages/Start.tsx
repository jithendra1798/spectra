import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:8000";

export function Start() {
  const nav = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startMission() {
    setLoading(true);
    setError(null);
    try {
      // 1. Create session (backend also creates a fresh Tavus conversation)
      const createRes = await fetch(`${API_BASE}/api/session/create`, { method: "POST" });
      if (!createRes.ok) throw new Error(`Create failed: ${createRes.status}`);
      const { session_id, tavus_conversation_url, tavus_conversation_id } = await createRes.json();

      // 2. Navigate to mission — timer will start once Tavus video iframe loads
      nav(`/mission/${session_id}`, {
        state: { tavusUrl: tavus_conversation_url, tavusConversationId: tavus_conversation_id },
      });
    } catch (e: any) {
      setError(e.message ?? "Failed to connect to backend");
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 24px",
      }}
    >
      <div style={{ width: "100%", maxWidth: 480 }}>
        {/* Logo block */}
        <div style={{ marginBottom: 48 }}>
          <div
            style={{
              fontFamily: "var(--mono)",
              fontSize: 11,
              letterSpacing: "0.38em",
              color: "var(--muted)",
              marginBottom: 12,
              textTransform: "uppercase",
            }}
          >
            Emotion Adaptive Interface
          </div>
          <div
            style={{
              fontFamily: "var(--mono)",
              fontSize: 56,
              fontWeight: 900,
              letterSpacing: "0.14em",
              color: "var(--accent)",
              lineHeight: 1,
              transition: "color var(--ui-ease)",
            }}
          >
            SPECTRA
          </div>
          <div
            style={{
              height: 2,
              width: 64,
              background: "var(--accent)",
              marginTop: 14,
              borderRadius: 1,
              boxShadow: "0 0 12px var(--accent-glow)",
              transition: "background var(--ui-ease), box-shadow var(--ui-ease)",
            }}
          />
        </div>

        {/* Description */}
        <p
          style={{
            fontSize: 14,
            color: "var(--muted)",
            lineHeight: 1.75,
            margin: "0 0 44px",
          }}
        >
          Your facial expressions adapt the interface in real time. ORACLE reads your stress,
          focus, and confidence — and reshapes every element to match your cognitive state.
        </p>

        {/* Action buttons */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <button
            onClick={startMission}
            disabled={loading}
            style={{
              padding: "14px 20px",
              borderRadius: 10,
              border: "1px solid var(--accent)",
              background: "var(--accent-dim)",
              color: "var(--accent)",
              cursor: loading ? "wait" : "pointer",
              fontFamily: "var(--mono)",
              fontWeight: 700,
              fontSize: 13,
              letterSpacing: "0.16em",
              textTransform: "uppercase",
              transition: "all 200ms",
              boxShadow: "0 0 20px var(--accent-glow)",
            }}
          >
            {loading ? "INITIALIZING..." : "BEGIN MISSION"}
          </button>

          <button
            onClick={() => nav("/mission/demo?demo=1")}
            style={{
              padding: "12px 20px",
              borderRadius: 10,
              border: "1px solid var(--border)",
              background: "transparent",
              color: "var(--muted)",
              cursor: "pointer",
              fontFamily: "var(--mono)",
              fontWeight: 600,
              fontSize: 12,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              transition: "all 200ms",
            }}
          >
            Demo Mode
          </button>
        </div>

        {error && (
          <div
            style={{
              marginTop: 16,
              padding: "10px 14px",
              borderRadius: 8,
              background: "rgba(248,113,113,0.08)",
              border: "1px solid rgba(248,113,113,0.25)",
              color: "var(--danger)",
              fontSize: 13,
            }}
          >
            {error}
          </div>
        )}

        {/* Footer */}
        <div
          style={{
            marginTop: 60,
            fontSize: 11,
            color: "var(--label)",
            fontFamily: "var(--mono)",
            letterSpacing: "0.12em",
          }}
        >
          ORACLE &nbsp;·&nbsp; ADAPTIVE INTELLIGENCE &nbsp;·&nbsp; v2.0
        </div>
      </div>
    </div>
  );
}
