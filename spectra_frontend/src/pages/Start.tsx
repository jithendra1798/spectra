import { Link } from "react-router-dom";

export function Start() {
  const sessionId = "demo";
  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ margin: 0, fontSize: 32 }}>SPECTRA</h1>
      <p style={{ color: "var(--muted)", maxWidth: 520 }}>
        Your face controls the screen. Begin a mission and watch the UI adapt.
      </p>
      <div style={{ display: "flex", gap: 12 }}>
        <Link to={`/mission/${sessionId}?demo=1`}>Start (Demo Mode)</Link>
        <Link to={`/mission/${sessionId}`}>Start (Backend WS)</Link>
      </div>
    </div>
  );
}