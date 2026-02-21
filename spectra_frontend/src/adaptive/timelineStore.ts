import type { Phase } from "./types";

export type TimelineEntry = {
  t: number;
  phase: Phase;
  stress: number;
  focus: number;
  adaptation: string | null;
};

const key = (sessionId: string) => `spectra:timeline:${sessionId}`;

export function getTimeline(sessionId: string): TimelineEntry[] {
  const raw = sessionStorage.getItem(key(sessionId));
  if (!raw) return [];
  try {
    return JSON.parse(raw) as TimelineEntry[];
  } catch {
    return [];
  }
}

export function addEntry(sessionId: string, entry: TimelineEntry) {
  const prev = getTimeline(sessionId);
  const next = [...prev, entry];
  sessionStorage.setItem(key(sessionId), JSON.stringify(next));
}

export function resetTimeline(sessionId: string) {
  sessionStorage.removeItem(key(sessionId));
}