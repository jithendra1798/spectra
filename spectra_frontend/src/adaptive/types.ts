export type Phase = "infiltrate" | "vault" | "escape" | "debrief";

export type ColorMood = "calm" | "neutral" | "intense";
export type Complexity = "simplified" | "standard" | "full";
export type GuidanceLevel = "none" | "low" | "medium" | "high";

export type UiOption = {
  id: string;
  label: string;
  highlighted?: boolean;
};

export type UiCommands = {
  complexity: Complexity;
  color_mood: ColorMood;
  panels_visible: Array<"main" | "stats" | "radar" | "comms">;
  options: UiOption[];
  guidance_level: GuidanceLevel;
};

export type OracleResponse = {
  text: string;
  voice_style: "calm_reassuring" | "direct_fast" | "urgent" | "neutral";
};

export type EmotionContract1 = {
  timestamp: number;
  emotions: {
    stress: number;
    focus: number;
    confusion: number;
    confidence: number;
    neutral: number;
  };
  dominant: "stress" | "focus" | "confusion" | "confidence" | "neutral";
  face_detected: boolean;
};

export type SpectraState = {
  sessionId: string;
  connected: boolean;
  phase: Phase;
  timeRemaining: number;
  ui: UiCommands;
  oracle?: OracleResponse;
  comms: Array<{ role: "oracle" | "player"; text: string }>;
  gameOver?: boolean;
  finalScore?: number;
};