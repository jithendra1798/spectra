/**
 * AdaptationBanner — shown in the main mission UI when Claude explains a UI adaptation.
 *
 * Rendered by the useCopilotAction("explainUIAdaptation") handler in Mission.tsx.
 * The content (reason + type) is entirely AI-generated — this is the generative UI piece.
 */
export function AdaptationBanner({
  reason,
  adaptationType,
  onDismiss,
}: {
  reason: string;
  adaptationType: string;
  onDismiss: () => void;
}) {
  const icon =
    adaptationType === "simplified" ? "▼"
    : adaptationType === "expanded"  ? "▲"
    : adaptationType === "calmed"    ? "◎"
    :                                  "◈";

  return (
    <div className="adaptation-banner">
      <span style={{ fontSize: 14, opacity: 0.7, flexShrink: 0 }}>{icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="tac-label" style={{ marginBottom: 3 }}>ORACLE ADAPTED</div>
        <div style={{ fontSize: 12.5, color: "var(--text)", lineHeight: 1.45 }}>{reason}</div>
      </div>
      <button
        onClick={onDismiss}
        style={{
          background: "none",
          border: "none",
          color: "var(--muted)",
          cursor: "pointer",
          fontSize: 18,
          lineHeight: 1,
          padding: "0 2px",
          flexShrink: 0,
        }}
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
}
