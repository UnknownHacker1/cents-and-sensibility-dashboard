import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PacePoint } from "../lib/api";
import { money, moneyWhole } from "../lib/format";

function Swatch({ dashed, color }: { dashed?: boolean; color: string }) {
  return (
    <svg width="22" height="8" aria-hidden="true">
      <line x1="1" y1="4" x2="21" y2="4" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeDasharray={dashed ? "4 4" : undefined} />
    </svg>
  );
}

type TipProps = { active?: boolean; payload?: { payload: PacePoint }[]; thisLabel: string; lastLabel: string };

function PaceTooltip({ active, payload, thisLabel, lastLabel }: TipProps) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-xl border border-line bg-raised px-3 py-2 text-sm shadow-panel">
      <div className="mb-1 font-medium">Day {p.day}</div>
      {p.this_month !== null && (
        <div className="num flex items-center gap-2">
          <Swatch color="var(--series-this)" /> {thisLabel}: {money(p.this_month)}
        </div>
      )}
      {p.last_month !== null && (
        <div className="num flex items-center gap-2 text-muted">
          <Swatch dashed color="var(--series-last)" /> {lastLabel}: {money(p.last_month)}
        </div>
      )}
    </div>
  );
}

/** Three evenly spaced round ticks above zero, e.g. 0 / 1k / 2k / 3k. */
function niceTicks(max: number) {
  const raw = Math.max(max, 1) / 3;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw) ?? raw;
  return [0, step, step * 2, step * 3];
}

const tickLabel = (v: number) => (v >= 1000 ? `$${+(v / 1000).toFixed(1)}k` : `$${v}`);

/** Running total of spending through the month, against the same day last month. */
export function PaceChart({ data, thisLabel, lastLabel, height = 260 }: { data: PacePoint[]; thisLabel: string; lastLabel: string; height?: number }) {
  const [asTable, setAsTable] = useState(false);
  const latest = [...data].reverse().find((p) => p.this_month !== null);
  const sameDayLast = latest ? data[latest.day - 1]?.last_month : null;
  const ticks = niceTicks(Math.max(...data.map((p) => Math.max(p.this_month ?? 0, p.last_month ?? 0))));

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 text-sm">
        <div className="flex flex-wrap items-center gap-4">
          <span className="flex items-center gap-2">
            <Swatch color="var(--series-this)" /> {thisLabel}
            {latest && <strong className="num">{moneyWhole(latest.this_month ?? 0)}</strong>}
          </span>
          <span className="flex items-center gap-2 text-muted">
            <Swatch dashed color="var(--series-last)" /> {lastLabel}
            {sameDayLast != null && <span className="num">{moneyWhole(sameDayLast)} by day {latest?.day}</span>}
          </span>
        </div>
        <button className="text-muted underline-offset-4 hover:text-ink hover:underline" onClick={() => setAsTable((t) => !t)}>
          {asTable ? "Show chart" : "Show as table"}
        </button>
      </div>

      {asTable ? (
        <div className="max-h-[260px] overflow-auto rounded-xl border border-line">
          <table className="num w-full text-sm">
            <thead className="sticky top-0 bg-sunken text-left text-muted">
              <tr>
                <th className="px-3 py-2 font-medium">Day</th>
                <th className="px-3 py-2 text-right font-medium">{thisLabel}</th>
                <th className="px-3 py-2 text-right font-medium">{lastLabel}</th>
              </tr>
            </thead>
            <tbody>
              {data.map((p) => (
                <tr key={p.day} className="border-t border-line">
                  <td className="px-3 py-1.5">{p.day}</td>
                  <td className="px-3 py-1.5 text-right">{p.this_month === null ? "" : money(p.this_month)}</td>
                  <td className="px-3 py-1.5 text-right text-muted">{p.last_month === null ? "" : money(p.last_month)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ height }} role="img" aria-label={`Spending so far: ${thisLabel} ${latest ? money(latest.this_month ?? 0) : ""}, compared with ${lastLabel}.`}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--line)" strokeDasharray="0" />
              <XAxis dataKey="day" tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={24} />
              <YAxis tickLine={false} axisLine={false} width={52} domain={[0, ticks[3]]} ticks={ticks} tickFormatter={tickLabel} />
              <Tooltip cursor={{ stroke: "var(--muted)", strokeWidth: 1, strokeDasharray: "3 3" }} content={<PaceTooltip thisLabel={thisLabel} lastLabel={lastLabel} />} />
              <Line type="monotone" dataKey="last_month" stroke="var(--series-last)" strokeWidth={2} strokeDasharray="5 5" dot={false} activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--raised)" }} connectNulls={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="this_month" stroke="var(--series-this)" strokeWidth={2.5} dot={false} activeDot={{ r: 5, strokeWidth: 2, stroke: "var(--raised)" }} connectNulls={false} animationDuration={900} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

/** Spending by category: one hue, thin bars with rounded ends, value on the right. */
export function CategoryBars({ rows }: { rows: { category: string; amount: number }[] }) {
  const max = Math.max(...rows.map((r) => r.amount), 1);
  const total = rows.reduce((sum, r) => sum + r.amount, 0);
  if (!rows.length) return <p className="text-muted">No spending this month yet.</p>;
  return (
    <ul className="space-y-3">
      {rows.map((r) => (
        <li key={r.category} className="group grid grid-cols-[7.5rem_1fr_auto] items-center gap-3 text-sm" title={`${r.category}: ${money(r.amount)}, ${Math.round((r.amount / total) * 100)}% of the month`}>
          <span className="truncate">{r.category}</span>
          <span className="h-2.5 rounded-full bg-sunken">
            <span
              className="block h-full rounded-full bg-series-this transition-[filter] group-hover:brightness-110"
              style={{ width: `${Math.max((r.amount / max) * 100, 2)}%` }}
            />
          </span>
          <span className="num w-24 text-right font-medium">
            {money(r.amount)}
            <span className="ml-1.5 hidden text-xs text-muted sm:inline">{Math.round((r.amount / total) * 100)}%</span>
          </span>
        </li>
      ))}
    </ul>
  );
}
