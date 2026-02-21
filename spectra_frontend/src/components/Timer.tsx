export function Timer({ seconds }: { seconds: number }) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  const isUrgent = seconds <= 60;
  return (
    <div className={`timer-display${isUrgent ? " urgent" : ""}`}>
      {m}:{String(s).padStart(2, "0")}
    </div>
  );
}
