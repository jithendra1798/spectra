import { useEffect, useMemo, useRef } from "react";
import type { UiCommands, Phase, EmotionContract1, OracleResponse } from "./types";

type Dispatch = (msg: any) => void;

// ===== WS message shapes (frontend expects these) =====
export type WsInbound =
  | { type: "ui_update"; data: UiCommands }
  | { type: "timer_tick"; time_remaining: number }
  | { type: "phase_change"; phase: Phase }
  | { type: "oracle_said"; text: string; voice_style: OracleResponse["voice_style"] }
  | { type: "game_end"; final_score: number }
  | { type: "emotion_update"; data: EmotionContract1 }
  | { type: "game_state_update"; current_score: number; decisions_made: number; phase: Phase; time_remaining: number }
  // optional: backend can push timeline points live too
  | { type: "timeline_point"; data: { t: number; phase: Phase; stress: number; focus: number; adaptation?: string | null } };

type WsOutbound =
  | { type: "player_speech"; text: string }
  | { type: "emotion_data"; data: EmotionContract1 }
  | { type: "client_event"; name: string; payload?: any };

// ===== runtime config =====
function getWsBaseUrl() {
  // Vite env: define VITE_WS_BASE_URL in .env (or default localhost)
  // Example: VITE_WS_BASE_URL=ws://localhost:8000
  const env = (import.meta as any).env?.VITE_WS_BASE_URL as string | undefined;
  return env ?? "ws://localhost:8000";
}

// ===== type guards =====
function isObject(v: unknown): v is Record<string, any> {
  return !!v && typeof v === "object";
}

function isWsInbound(msg: any): msg is WsInbound {
  if (!isObject(msg) || typeof msg.type !== "string") return false;

  switch (msg.type) {
    case "ui_update":
      return isObject(msg.data);
    case "timer_tick":
      return typeof msg.time_remaining === "number";
    case "phase_change":
      return msg.phase === "infiltrate" || msg.phase === "vault" || msg.phase === "escape" || msg.phase === "debrief";
    case "oracle_said":
      return typeof msg.text === "string";
    case "game_end":
      return typeof msg.final_score === "number";
    case "emotion_update":
      return isObject(msg.data) && isObject(msg.data.emotions);
    case "game_state_update":
      return typeof msg.current_score === "number";
    case "timeline_point":
      return isObject(msg.data) && typeof msg.data.t === "number";
    default:
      return false;
  }
}

export function useSpectraSocket(opts: {
  sessionId: string;
  dispatch: Dispatch;
  demoMode?: boolean;
}) {
  const { sessionId, dispatch, demoMode } = opts;

  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<number>(0);
  const closedByUsRef = useRef(false);

  const wsUrl = useMemo(() => {
    const base = getWsBaseUrl();
    return `${base.replace(/\/$/, "")}/ws/session/${sessionId}`;
  }, [sessionId]);

  useEffect(() => {
    if (demoMode) {
      dispatch({ type: "connected" });
      return;
    }

    closedByUsRef.current = false;

    const connect = () => {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        retryRef.current = 0;
        console.log("[WS] connected →", wsUrl);
        dispatch({ type: "connected" });
      };

      ws.onclose = () => {
        wsRef.current = null;
        console.log("[WS] disconnected from", wsUrl);
        dispatch({ type: "disconnected" });

        // auto-reconnect unless we intentionally closed
        if (closedByUsRef.current) return;

        const attempt = Math.min(6, retryRef.current++);
        const delay = 300 * Math.pow(2, attempt); // 300ms, 600ms, 1200ms... max-ish
        window.setTimeout(connect, delay);
      };

      ws.onerror = () => {
        // close triggers reconnect logic
        try {
          ws.close();
        } catch {}
      };

      ws.onmessage = (evt) => {
        try {
          const raw = JSON.parse(evt.data);
          console.log("[WS ← backend]", raw);
          if (raw?.type === "oracle_speech") {
            dispatch({ type: "oracle_said", text: raw.text, voice_style: raw.voice_style ?? "neutral" });
          } else if (isWsInbound(raw)) {
            dispatch(raw);
          } else {
            console.warn("[WS ← backend] unknown message type:", raw?.type, raw);
          }
        } catch {
          console.error("[WS ← backend] bad JSON:", evt.data);
        }
      };
    };

    connect();

    return () => {
      closedByUsRef.current = true;
      try {
        wsRef.current?.close();
      } catch {}
      wsRef.current = null;
    };
  }, [wsUrl, demoMode, dispatch]);

  function send(msg: WsOutbound) {
    if (demoMode) return;
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn("[WS → backend] not open, dropping:", msg);
      return;
    }
    console.log("[WS → backend]", msg);
    ws.send(JSON.stringify(msg));
  }

  function sendPlayerSpeech(text: string) {
    if (demoMode) {
      dispatch({ type: "oracle_said", text: `Heard: "${text}"`, voice_style: "neutral" });
      return;
    }
    send({ type: "player_speech", text });
  }

  function sendEmotion(data: EmotionContract1) {
    send({ type: "emotion_data", data });
  }

  function sendClientEvent(name: string, payload?: any) {
    send({ type: "client_event", name, payload });
  }

  return { sendPlayerSpeech, sendEmotion, sendClientEvent };
}
