import { useState } from "react";
import type { Options, Thesis } from "../api";

const EXAMPLE: Thesis = {
  industry: "Industrial & Infrastructure Services",
  sub_sector: "commercial HVAC and mechanical services",
  geography: "Midwest US (IL, MO, IN, OH)",
  revenue_min: 5_000_000,
  revenue_max: 20_000_000,
  employee_min: 20,
  employee_max: 150,
  ownership_preference: "founder-led",
  notes: "Prioritize companies with recurring service contracts over project-only revenue.",
};

const labelCls = "block text-xs font-semibold uppercase tracking-wide text-slate-500";
const fieldCls =
  "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500";

function num(v: string): number | null {
  const n = Number(v);
  return v === "" || Number.isNaN(n) ? null : n;
}

export default function ThesisForm({
  options,
  disabled,
  onRun,
}: {
  options: Options | null;
  disabled: boolean;
  onRun: (thesis: Thesis, maxCandidates: number) => void;
}) {
  const [t, setT] = useState<Thesis>(EXAMPLE);
  const [maxCandidates, setMaxCandidates] = useState(3);
  const set = <K extends keyof Thesis>(k: K, v: Thesis[K]) => setT((p) => ({ ...p, [k]: v }));

  const industries = options?.industries ?? [t.industry];
  const ownerships = options?.ownership_types ?? [t.ownership_preference];

  return (
    <form
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(e) => {
        e.preventDefault();
        onRun(t, maxCandidates);
      }}
    >
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className={labelCls}>Industry</label>
          <select
            className={fieldCls}
            value={t.industry}
            onChange={(e) => set("industry", e.target.value)}
          >
            {industries.map((i) => (
              <option key={i} value={i}>
                {i}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelCls}>Ownership preference</label>
          <select
            className={fieldCls}
            value={t.ownership_preference}
            onChange={(e) => set("ownership_preference", e.target.value)}
          >
            {ownerships.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelCls}>Sub-sector</label>
          <input
            className={fieldCls}
            value={t.sub_sector}
            onChange={(e) => set("sub_sector", e.target.value)}
          />
        </div>
        <div>
          <label className={labelCls}>Geography</label>
          <input
            className={fieldCls}
            value={t.geography}
            onChange={(e) => set("geography", e.target.value)}
          />
        </div>
        <div>
          <label className={labelCls}>Revenue min (USD)</label>
          <input
            type="number"
            className={fieldCls}
            value={t.revenue_min ?? ""}
            onChange={(e) => set("revenue_min", num(e.target.value))}
          />
        </div>
        <div>
          <label className={labelCls}>Revenue max (USD)</label>
          <input
            type="number"
            className={fieldCls}
            value={t.revenue_max ?? ""}
            onChange={(e) => set("revenue_max", num(e.target.value))}
          />
        </div>
        <div>
          <label className={labelCls}>Employees min</label>
          <input
            type="number"
            className={fieldCls}
            value={t.employee_min ?? ""}
            onChange={(e) => set("employee_min", num(e.target.value))}
          />
        </div>
        <div>
          <label className={labelCls}>Employees max</label>
          <input
            type="number"
            className={fieldCls}
            value={t.employee_max ?? ""}
            onChange={(e) => set("employee_max", num(e.target.value))}
          />
        </div>
      </div>

      <div className="mt-4">
        <label className={labelCls}>Notes / extra screening criteria</label>
        <textarea
          className={fieldCls}
          rows={2}
          value={t.notes ?? ""}
          onChange={(e) => set("notes", e.target.value)}
        />
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
        <label className="flex items-center gap-3 text-sm text-slate-600">
          Max candidates
          <input
            type="range"
            min={1}
            max={8}
            value={maxCandidates}
            onChange={(e) => setMaxCandidates(Number(e.target.value))}
          />
          <span className="w-5 font-semibold text-slate-800">{maxCandidates}</span>
        </label>
        <button
          type="submit"
          disabled={disabled}
          className="rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {disabled ? "Running…" : "Run pipeline →"}
        </button>
      </div>
    </form>
  );
}
