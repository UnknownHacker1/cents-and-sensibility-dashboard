import { animate } from "motion";
import { useEffect, useRef, useState } from "react";
import type { StoryToken } from "../lib/api";
import { usePrefersReducedMotion } from "../lib/hooks";

// Highlighter-pen tint behind each kind of number
const marker: Record<string, string> = {
  spent: "var(--mint-soft)",
  change_down: "var(--mint-soft)",
  change_up: "var(--coral-soft)",
  alert: "var(--coral-soft)",
  category: "var(--sunken)",
};

function CountUp({ value }: { value: string }) {
  const target = Number(value.replace(/[^0-9.]/g, ""));
  const reduced = usePrefersReducedMotion();
  const [shown, setShown] = useState(reduced ? value : value.replace(/[0-9]/g, "0"));
  const ran = useRef(false);
  useEffect(() => {
    if (reduced || ran.current || !value.startsWith("$")) {
      setShown(value);
      return;
    }
    ran.current = true;
    const controls = animate(0, target, {
      duration: 1.1,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (n) => setShown(`$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`),
      onComplete: () => setShown(value),
    });
    return () => controls.stop();
  }, [value, target, reduced]);
  return (
    <>
      <span aria-hidden="true">{shown}</span>
      <span className="sr-only">{value}</span>
    </>
  );
}

/** The month in one sentence. Numbers get a highlighter mark; money counts up once on load. */
export function Story({ tokens, size = "xl", onAlertClick }: { tokens: StoryToken[]; size?: "xl" | "lg"; onAlertClick?: () => void }) {
  const sizing = size === "xl" ? "text-[clamp(1.75rem,4.2vw,3.25rem)] leading-[1.12]" : "text-[clamp(1.4rem,3vw,2.1rem)] leading-[1.18]";
  return (
    <p className={`display max-w-[30ch] font-medium text-ink ${sizing}`}>
      {tokens.map((token, i) => {
        if ("text" in token) return <span key={i}>{token.text}</span>;
        const style = {
          backgroundImage: `linear-gradient(transparent 58%, ${marker[token.kind]} 58%, ${marker[token.kind]} 92%, transparent 92%)`,
        };
        const inner = token.kind === "spent" ? <CountUp value={token.value} /> : token.value;
        if (token.kind === "alert" && onAlertClick) {
          return (
            <button key={i} onClick={onAlertClick} style={style} className="num cursor-pointer px-0.5 font-bold text-coral-text underline decoration-coral decoration-2 underline-offset-[0.18em]">
              {inner}
            </button>
          );
        }
        const color = token.kind === "change_up" ? "text-coral-text" : token.kind === "change_down" ? "text-good" : "";
        return (
          <span key={i} style={style} className={`num px-0.5 font-bold ${color}`}>
            {inner}
          </span>
        );
      })}
    </p>
  );
}
