import type { Phase } from "./types"

export function nextPhase(current: Phase): Phase {
  if (current === "infiltrate") return "vault"
  if (current === "vault") return "escape"
  return "escape"
}