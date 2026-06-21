import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Confidence, OpportunityBrief } from "../api";

const LEVELS: Confidence[] = ["VERIFIED", "LIKELY", "UNVERIFIED", "CONFLICTING"];
const COLORS: Record<Confidence, string> = {
  VERIFIED: "#16a34a",
  LIKELY: "#84cc16",
  UNVERIFIED: "#f59e0b",
  CONFLICTING: "#ef4444",
};

export default function ConfidenceChart({ briefs }: { briefs: OpportunityBrief[] }) {
  const data = briefs.map((b) => {
    const counts: Record<string, number | string> = { name: b.company_name };
    for (const lvl of LEVELS) {
      counts[lvl] = b.key_facts.filter((f) => f.confidence === lvl).length;
    }
    return counts;
  });

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, 56 * data.length + 64)}>
      <BarChart data={data} layout="vertical" margin={{ left: 16, right: 24, top: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" allowDecimals={false} />
        <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        {LEVELS.map((lvl) => (
          <Bar key={lvl} dataKey={lvl} stackId="a" fill={COLORS[lvl]} radius={2} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
