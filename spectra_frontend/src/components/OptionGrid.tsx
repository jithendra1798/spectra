import type { UiOption } from "../adaptive/types";

export function OptionGrid({
  options,
  onPick,
}: {
  options: UiOption[];
  onPick: (id: string) => void;
}) {
  return (
    <div className="option-list">
      {options.map((o, i) => (
        <button
          key={o.id}
          className={`option-btn${o.highlighted ? " highlighted pulse" : ""}`}
          onClick={() => onPick(o.id)}
        >
          <span className="option-num">{String(i + 1).padStart(2, "0")}</span>
          <span className="option-label">{o.label}</span>
          {o.highlighted && <span className="option-rec">ORACLE REC</span>}
        </button>
      ))}
    </div>
  );
}
