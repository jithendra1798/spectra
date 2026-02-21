export interface TimelineEntry {
  timestamp: number
  stress: number
  adaptation?: string
}

export const timeline: TimelineEntry[] = []

export function record(stress: number, adaptation?: string) {
  timeline.push({
    timestamp: Date.now(),
    stress,
    adaptation
  })
}