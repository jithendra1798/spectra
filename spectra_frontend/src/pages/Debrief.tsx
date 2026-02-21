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
    return raw.map((e) => ({
      ...e,
      sec: Math.round((e.t - t0) / 1000),
    }));
  }, [raw]);

  const summary = useMemo(() => {
    if (raw.length === 0) {
      return { peakStress: null as any, mostFocus: null as any, adaptations: 0 };
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
      <div style={{ padding: 24, color: "var(--text)" }}>
        <div style={{ fontSize: 14, color: "var(--muted)" }}>Loading timeline...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24, color: "var(--text)" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--muted)" }}>Mission Debrief</div>
          <div style={{ fontSize: 28, fontWeight: 900 }}>Your Emotional Journey</div>
        </div>
        <div style={{ fontSize: 12, color: "var(--muted)" }}>Session: {sessionId}</div>
      </div>

      {raw.length === 0 ? (
        <div className="card" style={{ padding: 24, marginTop: 16, textAlign: "center" }}>
          <div style={{ fontSize: 14, color: "var(--muted)" }}>No timeline data recorded for this session.</div>
        </div>
      ) : (
        <>
          <div className="card" style={{ padding: 16, marginTop: 16 }}>
            <div style={{ fontWeight: 900, marginBottom: 10 }}>Stress Timeline</div>

            <div style={{ height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <XAxis dataKey="sec" tick={{ fill: "var(--muted)" }} />
                  <YAxis domain={[0, 1]} tick={{ fill: "var(--muted)" }} />
                  <Tooltip
                    contentStyle={{ background: "rgba(0,0,0,0.85)", border: "1px solid rgba(255,255,255,0.1)" }}
                    labelFormatter={(sec) => `t+${sec}s`}
                    formatter={(value: any, name: any, _props: any) => [value, name]}
                  />

                  {phaseLines.map((p) => (
                    <ReferenceLine
                      key={p.phase}
                      x={p.sec}
                      stroke="rgba(255,255,255,0.15)"
                      strokeDasharray="4 4"
                      label={{
                        value: p.phase.toUpperCase(),
                        position: "insideTopLeft",
                        fill: "var(--muted)",
                        fontSize: 10,
                      }}
                    />
                  ))}

                  <Line
                    type="monotone"
                    dataKey="stress"
                    strokeWidth={2}
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      if (!payload?.adaptation) return <Dot {...props} r={1} />;
                      return <Dot cx={cx} cy={cy} r={4} />;
                    }}
                    isAnimationActive={true}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div style={{ marginTop: 10, fontSize: 12, color: "var(--muted)" }}>
              Dots indicate moments the UI adapted (adaptation marker present).
            </div>
          </div>

          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(3, minmax(0, 1fr))", marginTop: 16 }}>
            <div className="card" style={{ padding: 14 }}>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>Peak Stress</div>
              {summary.peakStress ? (
                <>
                  <div style={{ fontSize: 22, fontWeight: 900 }}>{summary.peakStress.stress.toFixed(2)}</div>
                  <div style={{ fontSize: 12, color: "var(--muted)" }}>
                    {summary.peakStress.phase} &middot; {fmtTime(summary.peakStress.t)}
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 12, color: "var(--muted)" }}>No data</div>
              )}
            </div>

            <div className="card" style={{ padding: 14 }}>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>Most Focused</div>
              {summary.mostFocus ? (
                <>
                  <div style={{ fontSize: 22, fontWeight: 900 }}>{summary.mostFocus.focus.toFixed(2)}</div>
                  <div style={{ fontSize: 12, color: "var(--muted)" }}>
                    {summary.mostFocus.phase} &middot; {fmtTime(summary.mostFocus.t)}
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 12, color: "var(--muted)" }}>No data</div>
              )}
            </div>

            <div className="card" style={{ padding: 14 }}>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>Total UI Adaptations</div>
              <div style={{ fontSize: 22, fontWeight: 900 }}>{summary.adaptations}</div>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>markers recorded</div>
            </div>
          </div>
        </>
      )}

      <div style={{ marginTop: 18, fontSize: 13, color: "var(--muted)", fontStyle: "italic" }}>
        "This same emotion-adaptive pattern applies to surgical guidance, crisis response, education, and adaptive content platforms."
      </div>
    </div>
  );
}
