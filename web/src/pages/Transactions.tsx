import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ErrorNote, Skeleton } from "../components/ui";
import { api, type Transaction } from "../lib/api";
import { useRefresh } from "../lib/context";
import { money, shortDate } from "../lib/format";
import { useLoad } from "../lib/hooks";

function useDebounced<T>(value: T, ms = 250) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

export function Transactions() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [account, setAccount] = useState("");
  const query = useDebounced(q);
  const { version } = useRefresh();
  const all = useLoad(() => api.transactions({}), [version]);
  const { data, error, reload } = useLoad(() => api.transactions({ q: query, category, account }), [query, category, account, version]);

  const options = useMemo(() => {
    const rows: Transaction[] = all.data ?? [];
    return {
      categories: [...new Set(rows.map((t) => t.category))].sort(),
      accounts: [...new Map(rows.map((t) => [t.account_id, t.account])).entries()],
    };
  }, [all.data]);

  const totals = useMemo(() => {
    const rows = data ?? [];
    return {
      out: rows.filter((t) => t.amount > 0).reduce((s, t) => s + t.amount, 0),
      in: rows.filter((t) => t.amount < 0).reduce((s, t) => s - t.amount, 0),
    };
  }, [data]);

  const select = "rounded-[10px] border border-line bg-raised px-3 py-2 text-sm outline-none focus:border-mint";

  return (
    <div className="space-y-6">
      <header>
        <h1 className="display text-3xl font-semibold">Transactions</h1>
        <p className="mt-1 text-muted">The last 90 days, newest first.</p>
      </header>

      <div className="flex flex-col gap-3 sm:flex-row">
        <label className="relative flex-1">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value.slice(0, 100))}
            placeholder="Search merchants"
            aria-label="Search merchants"
            className="w-full rounded-[10px] border border-line bg-raised py-2 pl-9 pr-3 text-sm outline-none focus:border-mint"
          />
        </label>
        <select value={category} onChange={(e) => setCategory(e.target.value)} className={select} aria-label="Category">
          <option value="">All categories</option>
          {options.categories.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <select value={account} onChange={(e) => setAccount(e.target.value)} className={select} aria-label="Account">
          <option value="">All accounts</option>
          {options.accounts.map(([id, name]) => (
            <option key={id} value={id}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {error && <ErrorNote message={error} onRetry={reload} />}

      {data && (
        <p className="num text-sm text-muted">
          {data.length} {data.length === 1 ? "transaction" : "transactions"}. Out <span className="font-medium text-ink">{money(totals.out)}</span>, in{" "}
          <span className="font-medium text-good">{money(totals.in)}</span>.
        </p>
      )}

      <div className="overflow-hidden rounded-2xl border border-line bg-raised shadow-panel">
        {!data ? (
          <div className="space-y-3 p-5">
            {Array.from({ length: 8 }, (_, i) => (
              <Skeleton key={i} className="h-8" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <p className="p-8 text-center text-muted">No transactions match. Try a different search.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b border-line bg-sunken text-left text-muted">
              <tr>
                <th className="px-4 py-2.5 font-medium sm:px-5">Date</th>
                <th className="px-4 py-2.5 font-medium">Merchant</th>
                <th className="hidden px-4 py-2.5 font-medium md:table-cell">Category</th>
                <th className="hidden px-4 py-2.5 font-medium lg:table-cell">Account</th>
                <th className="px-4 py-2.5 text-right font-medium sm:px-5">Amount</th>
              </tr>
            </thead>
            <tbody>
              {data.map((t, i) => (
                <tr key={`${t.date}-${t.merchant}-${i}`} className="border-b border-line last:border-b-0 hover:bg-sunken/60">
                  <td className="num whitespace-nowrap px-4 py-2.5 text-muted sm:px-5">{shortDate(t.date)}</td>
                  <td className="px-4 py-2.5">
                    <span className="font-medium">{t.merchant}</span>
                    <span className="block text-xs text-muted md:hidden">{t.category}</span>
                  </td>
                  <td className="hidden px-4 py-2.5 md:table-cell">
                    <span className="rounded-full bg-sunken px-2 py-0.5 text-xs">{t.category}</span>
                  </td>
                  <td className="hidden px-4 py-2.5 text-muted lg:table-cell">{t.account}</td>
                  <td className={`num whitespace-nowrap px-4 py-2.5 text-right font-medium sm:px-5 ${t.amount < 0 ? "text-good" : ""}`}>
                    {t.amount < 0 ? `+${money(-t.amount)}` : money(t.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
