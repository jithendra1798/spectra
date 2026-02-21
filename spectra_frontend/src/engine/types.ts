export type Phase = "infiltrate" | "vault" | "escape"

export type Complexity = "simplified" | "standard" | "full"

export type ColorMood = "calm" | "neutral" | "intense"

export interface UIOption {
  id: string
  label: string
  highlighted?: boolean
}

export interface UICommands {
  complexity: Complexity
  color_mood: ColorMood
  panels_visible: string[]
  options: UIOption[]
  guidance_level: "none" | "low" | "medium" | "high"
}

export interface GameState {
  phase: Phase
  timeRemaining: number
  ui: UICommands
}