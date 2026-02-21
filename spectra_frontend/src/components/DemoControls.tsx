import { useMemo, useState } from "react";
import type { UiCommands, Phase, EmotionContract1 } from "../adaptive/types";

function clamp01(x: number) {
  return Math.max(0, Math.min(1, x));
}

function inferUiFromStress(
  stress: number
): Pick<UiCommands, "complexity" | "color_mood" | "panels_visible" | "guidance_level"> {
  if (stress > 0.6) {
    return {
      complexity: "simplified",
      color_mood: "calm",
      panels_visible: ["main"],
      guidance_level: "high",
    };
  }
  if (stress < 0.3) {
    return {
      complexity: "full",
      color_mood: "intense",
      panels_visible: ["main", "stats", "radar", "comms"],
      guidance_level: "low",
    };
  }
  return {
    complexity: "standard",
    color_mood: "neutral",
    panels_visible: ["main", "stats"],
    guidance_level: "medium",
  };
}

export function DemoControls({
  dispatchEmotion,
  setPhase,
}: {
  dispatchEmotion: (e: EmotionContract1) => void;
  setPhase: (p: Phase) => void;
}) {
  const [stress, setStress] = useState(0.45);
  const derived = useMemo(() => inferUiFromStress(stress), [stress]);

  function sendEmotion() {
    const s = stress;

    const focus = clamp01(1 - s);
    const confusion = clamp01(s * 0.6);
    const confidence = clamp01((1 - s) * 0.7);
    const neutral = clamp01(0.1);

    const emotions = { stress: s, focus, confusion, confidence, neutral };

    const dominant =
      s >= focus && s >= confusion && s >= confidence ? "stress"
        : focus >= confusion && focus >= confidence ? "focus"
        : confusion >= confidence ? "confusion"
        : "confidence";

    const payload: EmotionContract1 = {
      timestamp: Date.now(),
      emotions,
      dominant,
      face_detected: true,
    };

    dispatchEmotion(payload);
  }

  return (
    <div
      className="card"
      style={{
        position: "fixed",
        right: 16,
        top: 16,
        width: 300,
        padding: 12,
        zIndex: 9999,
      }}
    >
      <div style={{ fontWeight: 900, marginBottom: 8 }}>Demo Controls</div>

      <div style={{ fontSize: 12, color: "var(--muted)" }}>Stress</div>
      <input
        type="range"
        min={0}
        max={1}
        step={0.01}
        value={stress}
        onChange={(e) => setStress(clamp01(parseFloat(e.target.value)))}
        style={{ width: "100%" }}
      />

      <div style={{ display: "grid", gap: 6, marginTop: 10, fontSize: 12, color: "var(--muted)" }}>
        <div>
          complexity: <b style={{ color: "var(--text)" }}>{derived.complexity}</b>
        </div>
        <div>
          color mood: <b style={{ color: "var(--text)" }}>{derived.color_mood}</b>
        </div>
        <div>
          guidance: <b style={{ color: "var(--text)" }}>{derived.guidance_level}</b>
        </div>
      </div>

      <button
        onClick={sendEmotion}
        style={{
          marginTop: 10,
          width: "100%",
          padding: "10px 12px",
          borderRadius: 12,
          border: "1px solid var(--border)",
          background: "var(--panel)",
          color: "var(--text)",
          cursor: "pointer",
          fontWeight: 800,
        }}
      >
        Send Emotion Update
      </button>

      <div style={{ marginTop: 12, fontSize: 12, color: "var(--muted)" }}>Phase</div>
      <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
        <button
          onClick={() => setPhase("infiltrate")}
          style={{ flex: 1, padding: "8px 10px", borderRadius: 12, border: "1px solid var(--border)", background: "transparent", color: "var(--text)", cursor: "pointer" }}
        >
          Infiltrate
        </button>
        <button
          onClick={() => setPhase("vault")}
          style={{ flex: 1, padding: "8px 10px", borderRadius: 12, border: "1px solid var(--border)", background: "transparent", color: "var(--text)", cursor: "pointer" }}
        >
          Vault
        </button>
        <button
          onClick={() => setPhase("escape")}
          style={{ flex: 1, padding: "8px 10px", borderRadius: 12, border: "1px solid var(--border)", background: "transparent", color: "var(--text)", cursor: "pointer" }}
        >
          Escape
        </button>
      </div>

      <div style={{ marginTop: 8, fontSize: 11, color: "var(--muted)" }}>
        This simulates backend Contract 1 emotion feed + phase_change events.
      </div>
    </div>
  );
}