import type { GameState, Complexity, ColorMood } from "./types";

export function applyEmotion(state: GameState, emotion: number): GameState {
  // emotion: 0 = calm, 1 = high stress

  let complexity: Complexity = "standard";
  let mood: ColorMood = "neutral";

  if (emotion > 0.7) {
    complexity = "simplified"
    mood = "calm"
  } else if (emotion < 0.3) {
    complexity = "full"
    mood = "intense"
  }

  return {
    ...state,
    ui: {
      ...state.ui,
      complexity,
      color_mood: mood
    }
  }
}