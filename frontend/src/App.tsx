import { useEffect, useRef, useState } from "react";
import { createRun, getOptions, getRun } from "./api";
import type { Options, OpportunityBrief, RunState, Thesis } from "./api";
import BriefCard from "./components/BriefCard";
import ConfidenceChart from "./components/ConfidenceChart";
import ThesisForm from "./components/ThesisForm";

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h2>
      {children}
    </div>
  );
}

function StatusBanner() {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-sky-50 p-4 text-sm text-sky-800 ring-1 ring-sky-200">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
      Running the pipeline — research → (verify ∥ contacts) → briefs. This can take a minute.
    </div>
  );
}

export default function App() {
  const [options, setOptions] = useState<Options | null>(null);
  const [status, setStatus] = useState<RunState | "idle">("idle");
  const [briefs, setBriefs] = useState<OpportunityBrief[]>([]);
  const [error, setError] = useState<string | null>(null);
  const poll = useRef<number | null>(null);

  useEffect(() => {
    getOptions()
      .then(setOptions)
      .catch(() => setOptions(null));
    return () => {
      if (poll.current) window.clearInterval(poll.current);
    };
  }, []);

  const run = async (thesis: Thesis, maxCandidates: number) => {
    setError(null);
    setBriefs([]);
    setStatus("pending");
    try {
      const { run_id } = await createRun(thesis, maxCandidates);
      setStatus("running");
      poll.current = window.setInterval(async () => {
        try {
          const s = await getRun(run_id);
          if (s.status === "done") {
            window.clearInterval(poll.current!);
            setBriefs(s.briefs);
            setStatus("done");
          } else if (s.status === "error") {
            window.clearInterval(poll.current!);
            setError(s.error ?? "Pipeline failed.");
            setStatus("error");
          }
        } catch (e) {
          window.clearInterval(poll.current!);
          setError(e instanceof Error ? e.message : String(e));
          setStatus("error");
        }
      }, 2500);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStatus("error");
    }
  };

  const busy = status === "pending" || status === "running";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-6 py-5">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">🧭 Sourcr</h1>
          <p className="text-sm text-slate-500">
            Multi-agent M&amp;A target sourcing — a thesis in, verified opportunity briefs out.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
        <ThesisForm options={options} disabled={busy} onRun={run} />

        {busy && <StatusBanner />}

        {error && (
          <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-200">
            {error}
          </div>
        )}

        {status === "done" && briefs.length > 0 && (
          <>
            <Card title="Pipeline confidence">
              <ConfidenceChart briefs={briefs} />
            </Card>
            <div className="grid gap-4">
              {briefs.map((b, i) => (
                <BriefCard key={i} brief={b} />
              ))}
            </div>
          </>
        )}

        {status === "done" && briefs.length === 0 && (
          <div className="rounded-lg bg-slate-100 p-4 text-sm text-slate-600">
            No briefs produced — try widening the thesis or raising the candidate count.
          </div>
        )}
      </main>
    </div>
  );
}
