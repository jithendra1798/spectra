import { useState } from "react";

const PHASES = [
  {
    num: "01",
    name: "INFILTRATE",
    desc: "Breach the target network node and establish a covert foothold inside the system perimeter.",
  },
  {
    num: "02",
    name: "VAULT",
    desc: "Decrypt the cipher fragments before the extraction window closes. Precision under pressure.",
  },
  {
    num: "03",
    name: "ESCAPE",
    desc: "Choose an exit route under time pressure. Every second counts — trust your instincts.",
  },
];

interface BriefingProps {
  tavusUrl: string | null;
  connected: boolean;
  onReady: () => Promise<void>;
}

export function Briefing({ tavusUrl, connected, onReady }: BriefingProps) {
  const [starting, setStarting] = useState(false);

  async function handleReady() {
    setStarting(true);
    try {
      await onReady();
    } catch {
      setStarting(false);
    }
  }

  return (
    <div className="hud-root" data-mood="neutral">
      {/* ── Top bar ── */}
      <div className="hud-topbar">
        <div className="hud-logo">SPECTRA</div>

        <div className="hud-phase-indicator">
          <span className="hud-phase-step">00 / 03</span>
          <div className="phase-sep" />
          <span className="hud-phase-name">MISSION BRIEFING</span>
        </div>

        <div className="hud-topbar-right">
          <div
            className={`dot ${connected ? "dot-ok" : "dot-danger"}`}
            title={connected ? "Connected" : "Offline"}
          />
        </div>
      </div>

      {/* ── Body ── */}
      <div className="hud-body">
        {/* Oracle sidebar — larger video for briefing */}
        <div className="oracle-sidebar card" style={{ padding: 14 }}>
          <div className="oracle-header">
            <div className="dot dot-ok" />
            <div className="oracle-label">Oracle</div>
          </div>

          <div className="oracle-video" style={{ height: 260 }}>
            {tavusUrl ? (
              <iframe
                title="Tavus CVI"
                src={tavusUrl}
                allow="camera; microphone; autoplay; clipboard-write; display-capture"
              />
            ) : (
              <div className="oracle-offline">
                <div className="oracle-offline-icon">◈</div>
                <span>ORACLE OFFLINE</span>
              </div>
            )}
          </div>

          <div
            style={{
              marginTop: 12,
              padding: "8px 10px",
              borderRadius: 6,
              background: "rgba(125, 211, 252, 0.06)",
              border: "1px solid rgba(125, 211, 252, 0.15)",
              fontSize: 12,
              color: "var(--muted)",
              fontFamily: "var(--mono)",
              lineHeight: 1.6,
            }}
          >
            ORACLE will brief you on the mission. Listen carefully before you proceed.
          </div>
        </div>

        {/* Phase overview card */}
        <div className="phase-content card" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <div
              className="tac-label"
              style={{ marginBottom: 4, fontSize: 10, letterSpacing: "0.3em", color: "var(--muted)" }}
            >
              MISSION OVERVIEW
            </div>
            <div
              style={{
                fontFamily: "var(--mono)",
                fontSize: 18,
                fontWeight: 800,
                color: "var(--accent)",
                letterSpacing: "0.1em",
              }}
            >
              OPERATION SPECTRA
            </div>
          </div>

          {/* Phase cards */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
            {PHASES.map((p) => (
              <div
                key={p.num}
                className="card"
                style={{
                  padding: "12px 14px",
                  display: "flex",
                  gap: 14,
                  alignItems: "flex-start",
                  background: "rgba(125, 211, 252, 0.04)",
                  border: "1px solid rgba(125, 211, 252, 0.12)",
                }}
              >
                <div
                  style={{
                    fontFamily: "var(--mono)",
                    fontSize: 22,
                    fontWeight: 900,
                    color: "var(--accent)",
                    opacity: 0.35,
                    lineHeight: 1,
                    minWidth: 32,
                  }}
                >
                  {p.num}
                </div>
                <div>
                  <div
                    className="tac-label"
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      letterSpacing: "0.22em",
                      color: "var(--accent)",
                      marginBottom: 4,
                    }}
                  >
                    {p.name}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>{p.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* CTA */}
          <button
            onClick={handleReady}
            disabled={starting}
            style={{
              marginTop: 8,
              padding: "15px 20px",
              borderRadius: 10,
              border: "1px solid var(--accent)",
              background: starting ? "var(--panel)" : "var(--accent-dim)",
              color: starting ? "var(--muted)" : "var(--accent)",
              cursor: starting ? "wait" : "pointer",
              fontFamily: "var(--mono)",
              fontWeight: 800,
              fontSize: 13,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              transition: "all 200ms",
              boxShadow: starting ? "none" : "0 0 24px var(--accent-glow)",
              animation: starting ? "none" : "pulseGlow 2s ease-in-out infinite",
              width: "100%",
            }}
          >
            {starting ? "INITIATING..." : "I'M READY, ORACLE"}
          </button>
        </div>
      </div>

      {/* ── No panel strip during briefing ── */}
      <div className="hud-panels" />

      <style>{`
        @keyframes pulseGlow {
          0%, 100% { box-shadow: 0 0 18px var(--accent-glow); }
          50%       { box-shadow: 0 0 36px var(--accent-glow); }
        }
      `}</style>
    </div>
  );
}
