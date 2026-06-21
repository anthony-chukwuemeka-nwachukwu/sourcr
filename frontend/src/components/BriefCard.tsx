import type { Confidence, OpportunityBrief, Overall } from "../api";

const OVERALL_BADGE: Record<Overall, string> = {
  HIGH: "bg-green-100 text-green-800 ring-green-600/20",
  MEDIUM: "bg-amber-100 text-amber-800 ring-amber-600/20",
  LOW: "bg-orange-100 text-orange-800 ring-orange-600/20",
  NEEDS_REVIEW: "bg-red-100 text-red-800 ring-red-600/20",
};

const CONF_TEXT: Record<Confidence, string> = {
  VERIFIED: "text-green-700",
  LIKELY: "text-lime-700",
  UNVERIFIED: "text-amber-700",
  CONFLICTING: "text-red-700",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h4>
      <div className="mt-1 text-sm text-slate-700">{children}</div>
    </section>
  );
}

export default function BriefCard({ brief }: { brief: OpportunityBrief }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-start justify-between gap-4 border-b border-slate-100 p-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{brief.company_name}</h3>
          {brief.domain && (
            <a
              href={`https://${brief.domain}`}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-sky-600 hover:underline"
            >
              {brief.domain}
            </a>
          )}
        </div>
        <span
          className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset ${OVERALL_BADGE[brief.overall_confidence]}`}
        >
          {brief.overall_confidence}
        </span>
      </div>

      <div className="space-y-4 p-4">
        <Section title="Summary">{brief.summary}</Section>
        <Section title="Fit vs. Thesis">{brief.fit_rationale}</Section>

        <Section title="Key Facts">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="py-1 pr-3 font-medium">Fact</th>
                <th className="py-1 pr-3 font-medium">Confidence</th>
                <th className="py-1 font-medium">Sources</th>
              </tr>
            </thead>
            <tbody>
              {brief.key_facts.map((f, i) => (
                <tr key={i} className="border-t border-slate-100 align-top">
                  <td className="py-1.5 pr-3 text-slate-700">{f.fact}</td>
                  <td className={`py-1.5 pr-3 font-medium ${CONF_TEXT[f.confidence]}`}>
                    {f.confidence}
                  </td>
                  <td className="py-1.5">
                    {f.sources.map((s, j) => (
                      <a
                        key={j}
                        href={s}
                        target="_blank"
                        rel="noreferrer"
                        className="block max-w-xs truncate text-sky-600 hover:underline"
                      >
                        {s}
                      </a>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        {brief.decision_makers.length > 0 && (
          <Section title="Decision-Makers">
            <ul className="space-y-1">
              {brief.decision_makers.map((c, i) => (
                <li key={i} className="flex flex-wrap items-center gap-x-2">
                  <span className="font-medium text-slate-800">{c.name}</span>
                  <span className="text-slate-500">— {c.title}</span>
                  {c.profile_url && (
                    <a
                      href={c.profile_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-sky-600 hover:underline"
                    >
                      profile ↗
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </Section>
        )}
      </div>
    </div>
  );
}
