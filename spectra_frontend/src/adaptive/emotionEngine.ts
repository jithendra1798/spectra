import type { EmotionContract1, UiCommands } from "./types";

export function deriveUiFromEmotion(emotion: EmotionContract1, current: UiCommands): UiCommands {
  const { stress, focus, confusion, confidence } = emotion.emotions;

  // Rule 1: high stress OR high confusion => simplify + calm + high guidance
  if (stress > 0.6 || confusion > 0.5) {
    const baseOptions = current.options ?? [];
    const options = baseOptions.slice(0, 2).map((o, _idx) => ({
      ...o,
      highlighted: true, // when guidance high, we can highlight recommendation(s)
    }));

    return {
      ...current,
      complexity: "simplified",
      color_mood: "calm",
      panels_visible: ["main"],
      guidance_level: "high",
      options: options.length ? options : current.options,
    };
  }

  // Rule 2: high focus AND low stress => full + intense
  if (focus > 0.6 && stress < 0.3 && confidence > 0.5) {
    return {
      ...current,
      complexity: "full",
      color_mood: "intense",
      panels_visible: ["main", "stats", "radar", "comms"],
      guidance_level: "low",
      options: current.options.map((o) => ({ ...o, highlighted: false })),
    };
  }

  // Default: standard + neutral
  return {
    ...current,
    complexity: "standard",
    color_mood: "neutral",
    panels_visible: ["main", "stats"],
    guidance_level: "medium",
    options: current.options.map((o) => ({ ...o, highlighted: false })),
  };
}