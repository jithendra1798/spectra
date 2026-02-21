import { useState, useEffect, useRef } from "react";
import type { UiOption } from "../adaptive/types";

export function OptionGrid({
  options,
  onPick,
}: {
  options: UiOption[];
  onPick: (id: string) => void;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const prevOptionIdsRef = useRef<string>("");

  // Reset selection only when the set of option IDs actually changes (not on every re-render)
  useEffect(() => {
    const ids = options.map((o) => o.id).join(",");
    if (ids !== prevOptionIdsRef.current) {
      prevOptionIdsRef.current = ids;
      setSelectedId(null);
    }
  }, [options]);

  return (
    <div className="option-list">
      {options.map((o, i) => {
        const isSelected = selectedId === o.id;
        return (
          <button
            key={o.id}
            className={`option-btn${o.highlighted ? " highlighted pulse" : ""}${isSelected ? " selected" : ""}`}
            onClick={() => {
              setSelectedId(o.id);
              onPick(o.id);
            }}
          >
            <span className="option-num">{String(i + 1).padStart(2, "0")}</span>
            <span className="option-label">{o.label}</span>
            {o.highlighted && !isSelected && <span className="option-rec">ORACLE REC</span>}
            {isSelected && <span className="option-chosen">✓ CHOSEN</span>}
          </button>
        );
      })}
    </div>
  );
}
