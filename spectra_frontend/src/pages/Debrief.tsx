import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Dot } from "recharts";
import { getTimeline, type TimelineEntry } from "../adaptive/timelineStore";

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:8000";

function fmtTime(ms: number) {
  const d = new Date(ms);
  return d.toLocaleTimeString([], { minute: "2-digit", second: "2-digit" });
}

export function Debrief() {
  const { sessionId = "demo" } = useParams();
  const [raw, setRaw] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch timeline from backend API, fall back to sessionStorage
  useEffect(() => {
    let cancelled = false;

    async function fetchTimeline() {
      try {
        const res = await fetch(`${API_BASE}/api/timeline/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          if (!cancelled && Array.isArray(data) && data.length > 0) {
            setRaw(data);
            setLoading(false);
            return;
          }
        }
      } catch {
        // backend unavailable, fall through to sessionStorage
      }

      // Fallback: sessionStorage (demo mode or backend down)
      if (!cancelled) {
        setRaw(getTimeline(sessionId));
        setLoading(false);
      }
    }

    fetchTimeline();
    return () => { cancelled = true; };
  }, [sessionId]);

  const data = useMemo(() => {
    if (raw.length === 0) return [];
    const t0 = raw[0].t;
    return raw.map((e) => ({ ...e, sec: Math.round((e.t - t0) / 1000) }));
  }, [raw]);

  const summary = useMemo(() => {
    if (raw.length === 0) {
      return { peakStress: null as TimelineEntry | null, mostFocus: null as TimelineEntry | null, adaptations: 0 };
    }
    let peakStress = raw[0];
    let mostFocus = raw[0];
    let adaptations = 0;
    for (const e of raw) {
      if (e.stress > peakStress.stress) peakStress = e;
      if (e.focus > mostFocus.focus) mostFocus = e;
      if (e.adaptation) adaptations += 1;
    }
    return { peakStress, mostFocus, adaptations };
  }, [raw]);

  const phaseLines = useMemo(() => {
    if (data.length === 0) return [];
    const seen = new Set<string>();
    const lines: Array<{ phase: string; sec: number }> = [];
    for (const e of data) {
      if (!seen.has(e.phase)) {
        seen.add(e.phase);
        lines.push({ phase: e.phase, sec: e.sec });
      }
    }
    return lines;
  }, [data]);

  if (loading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background: "var(--bg)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            fontFamily: "var(--mono)",
            fontSize: 12,
            color: "var(--muted)",
            letterSpacing: "0.2em",
          }}
        >
          LOADING TIMELINE...
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg)",
        padding: "32px 28px",
        color: "var(--text)",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div className="tac-label" style={{ marginBottom: 8 }}>Mission Debrief</div>
        <div
          style={{
            fontFamily: "var(--mono)",
            fontSize: 28,
            fontWeight: 900,
            letterSpacing: "0.06em",
            color: "var(--accent)",
            transition: "color var(--ui-ease)",
          }}
        >
          Emotional Journey
        </div>
        <div style={{ height: 2, width: 48, background: "var(--accent)", marginTop: 10, borderRadius: 1 }} />
        <div style={{ marginTop: 8, fontSize: 11, color: "var(--label)", fontFamily: "var(--mono)" }}>
          SESSION {sessionId.toUpperCase()}
        </div>
      </div>

      {raw.length === 0 ? (
        <div
          className="card"
          style={{ padding: 36, textAlign: "center", maxWidth: 480 }}
        >
          <div style={{ fontSize: 28, opacity: 0.25, marginBottom: 12 }}>◈</div>
          <div className="tac-label" style={{ marginBottom: 6 }}>No Data</div>
          <div style={{ fontSize: 13, color: "var(--muted)" }}>
            No timeline data recorded for this session.
          </div>
        </div>
      ) : (
        <>
          {/* Timeline chart */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <div className="tac-label" style={{ marginBottom: 12 }}>Stress Timeline</div>
            <div style={{ height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <XAxis
                    dataKey="sec"
                    tick={{ fill: "rgba(148,210,255,0.5)", fontSize: 11, fontFamily: "var(--mono)" }}
                    tickLine={false}
                    axisLine={{ stroke: "rgba(56,189,248,0.12)" }}
                  />
                  <YAxis
                    domain={[0, 1]}
                    tick={{ fill: "rgba(148,210,255,0.5)", fontSize: 11, fontFamily: "var(--mono)" }}
                    tickLine={false}
                    axisLine={false}
                    width={30}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(7,11,18,0.95)",
                      border: "1px solid rgba(56,189,248,0.22)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    labelFormatter={(sec) => `t+${sec}s`}
                    formatter={(value: any, name: any) => [
                      typeof value === "number" ? value.toFixed(2) : value,
                      name,
                    ]}
                  />

                  {phaseLines.map((p) => (
                    <ReferenceLine
                      key={p.phase}
                      x={p.sec}
                      stroke="rgba(255,255,255,0.12)"
                      strokeDasharray="4 4"
                      label={{
                        value: p.phase.toUpperCase(),
                        position: "insideTopLeft",
                        fill: "rgba(148,210,255,0.5)",
                        fontSize: 9,
                        fontFamily: "monospace",
                      }}
                    />
                  ))}

                  <Line
                    type="monotone"
                    dataKey="stress"
                    stroke="var(--accent)"
                    strokeWidth={2}
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      if (!payload?.adaptation) return <Dot {...props} r={1} />;
                      return <Dot cx={cx} cy={cy} r={4} fill="var(--warn)" stroke="none" />;
                    }}
                    isAnimationActive
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div
              style={{
                marginTop: 8,
                fontSize: 11,
                color: "var(--label)",
                fontFamily: "var(--mono)",
              }}
            >
              Highlighted dots = UI adaptation events
            </div>
          </div>

          {/* Summary cards */}
          <div
            style={{
              display: "grid",
              gap: 12,
              gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            }}
          >
            <div className="card" style={{ padding: 16 }}>
              <div className="tac-label" style={{ marginBottom: 8 }}>Peak Stress</div>
              {summary.peakStress ? (
                <>
                  <div
                    style={{
                      fontSize: 28,
                      fontWeight: 900,
                      fontFamily: "var(--mono)",
                      color: "var(--danger)",
                    }}
                  >
                    {summary.peakStress.stress.toFixed(2)}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>
                    {summary.peakStress.phase} &middot; {fmtTime(summary.peakStress.t)}
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 12, color: "var(--muted)" }}>No data</div>
              )}
            </div>

            <div className="card" style={{ padding: 16 }}>
              <div className="tac-label" style={{ marginBottom: 8 }}>Peak Focus</div>
              {summary.mostFocus ? (
                <>
                  <div
                    style={{
                      fontSize: 28,
                      fontWeight: 900,
                      fontFamily: "var(--mono)",
                      color: "var(--ok)",
                    }}
                  >
                    {summary.mostFocus.focus.toFixed(2)}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>
                    {summary.mostFocus.phase} &middot; {fmtTime(summary.mostFocus.t)}
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 12, color: "var(--muted)" }}>No data</div>
              )}
            </div>

            <div className="card" style={{ padding: 16 }}>
              <div className="tac-label" style={{ marginBottom: 8 }}>UI Adaptations</div>
              <div
                style={{
                  fontSize: 28,
                  fontWeight: 900,
                  fontFamily: "var(--mono)",
                  color: "var(--accent)",
                }}
              >
                {summary.adaptations}
              </div>
              <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>
                markers recorded
              </div>
            </div>
          </div>
        </>
      )}

      {/* Footer note */}
      <div
        style={{
          marginTop: 36,
          fontSize: 12,
          color: "var(--label)",
          fontStyle: "italic",
          maxWidth: 600,
        }}
      >
        "This same emotion-adaptive pattern applies to surgical guidance, crisis response,
        education, and adaptive content platforms."
      </div>
    </div>
  );
}
